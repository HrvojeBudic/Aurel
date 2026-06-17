"""
sandbox_policy.py — Sandbox profiles, policy enforcement, and diagnostics (P0.17).

Tool access is not machine access. Tools execute inside a declared sandbox profile
and within runtime authority. Profiles declare capabilities; policy enforces them
before handlers run and at the filesystem boundary.
"""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from .canonical_path import CanonicalPathResolver, PathResolutionError
from .core_types import new_id, now
from .sandbox import (
    BubblewrapSandbox,
    DEFAULT_MAX_OUTPUT_BYTES,
    DEFAULT_TIMEOUT_S,
    DockerSandbox,
    SandboxBackend,
    SandboxMode,
    SandboxUnavailableError,
    UnsafeLocalSandbox,
)

if TYPE_CHECKING:
    from .tools import ToolSpec


class SandboxProfileName(str, Enum):
    NO_EXEC_READONLY = "no_exec_readonly"
    RESTRICTED_LOCAL = "restricted_local"
    UNSAFE_LOCAL_DEMO = "unsafe_local_demo"
    DOCKER = "docker"
    BUBBLEWRAP = "bubblewrap"


SECRET_BASENAMES = {
    ".env", ".envrc", "credentials.json", "secrets.json",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
}
SECRET_PREFIXES = (".env.",)


class SandboxViolationError(PermissionError):
    """Raised when a sandbox policy check fails at the filesystem boundary."""

    def __init__(self, violation: "SandboxViolation") -> None:
        self.violation = violation
        super().__init__(violation.reason)


@dataclass
class SandboxProfile:
    profile_name: str
    mode: SandboxMode
    workspace_root: str
    allow_read: bool = True
    allow_write: bool = False
    allow_exec: bool = False
    allow_network: bool = False
    allow_env: bool = False
    allow_secrets: bool = False
    allowed_paths: list[str] = field(default_factory=lambda: ["*"])
    disallowed_paths: list[str] = field(default_factory=list)
    max_timeout_seconds: float = DEFAULT_TIMEOUT_S
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES
    backend_name: str = "UnsafeLocalSandbox"
    unsafe: bool = False
    limitations: list[str] = field(default_factory=list)

    @property
    def execution_limits(self) -> "SandboxExecutionLimits":
        return SandboxExecutionLimits(
            timeout_seconds=self.max_timeout_seconds,
            max_output_bytes=self.max_output_bytes,
            network_allowed=self.allow_network,
            secrets_allowed=self.allow_secrets,
        )


@dataclass
class SandboxExecutionLimits:
    timeout_seconds: float = DEFAULT_TIMEOUT_S
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES
    max_files_changed: int = 0
    max_processes: int = 0
    network_allowed: bool = False
    secrets_allowed: bool = False


@dataclass
class SandboxCapabilityMap:
    read_tools: set[str] = field(default_factory=set)
    write_tools: set[str] = field(default_factory=set)
    exec_tools: set[str] = field(default_factory=set)
    network_tools: set[str] = field(default_factory=set)


DEFAULT_CAPABILITY_MAP = SandboxCapabilityMap(
    read_tools={
        "read_file", "list_dir", "search_text", "git_status", "git_diff",
    },
    write_tools={
        "write_file", "edit_file", "patch_file", "delete_file",
        "mutate_protected_verification",
    },
    exec_tools={"run_shell", "run_python", "run_tests"},
    network_tools=set(),
)


@dataclass
class SandboxViolation:
    violation_id: str
    reason: str
    profile_name: str
    attempted_action: str
    attempted_path: str = ""
    tool_name: str = ""
    severity: str = "deny"
    created_at: float = field(default_factory=now)

    @staticmethod
    def make(
        profile_name: str,
        attempted_action: str,
        reason: str,
        *,
        attempted_path: str = "",
        tool_name: str = "",
        severity: str = "deny",
    ) -> "SandboxViolation":
        return SandboxViolation(
            violation_id=new_id("sandbox_violation"),
            reason=reason,
            profile_name=profile_name,
            attempted_action=attempted_action,
            attempted_path=attempted_path,
            tool_name=tool_name,
            severity=severity,
        )


@dataclass
class SandboxDecision:
    allowed: bool
    reason: str = ""
    violation: Optional[SandboxViolation] = None


@dataclass
class SandboxDiagnostics:
    active_profile: str
    backend_name: str
    workspace_root: str
    network_allowed: bool
    secrets_allowed: bool
    write_allowed: bool
    exec_allowed: bool
    read_allowed: bool
    unsafe: bool
    limitations: list[str] = field(default_factory=list)
    backend_available: bool = True
    hard_isolated: bool = False
    security_boundary: bool = False


@dataclass
class SandboxExecutionContext:
    sandbox: SandboxBackend
    profile: SandboxProfile
    limits: SandboxExecutionLimits
    command_id: str = ""
    timeout_seconds: float = DEFAULT_TIMEOUT_S


def is_secret_like_path(path: str) -> bool:
    name = os.path.basename(path.replace("\\", "/"))
    if name in SECRET_BASENAMES:
        return True
    for prefix in SECRET_PREFIXES:
        if name.startswith(prefix):
            return True
    low = name.lower()
    return "secret" in low or "credential" in low or name.endswith(".pem")


def resolve_workspace_path(root: str, path: str) -> str:
    resolver = CanonicalPathResolver(root)
    return resolver.resolve(path).relative


def is_path_allowed(
    profile: SandboxProfile,
    path: str,
    *,
    action: str = "read",
) -> bool:
    try:
        rel = resolve_workspace_path(profile.workspace_root, path)
    except PathResolutionError:
        return False
    if not profile.allow_secrets and is_secret_like_path(rel):
        return False
    for pattern in profile.disallowed_paths:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path, pattern):
            return False
    if "*" in profile.allowed_paths:
        return True
    for pattern in profile.allowed_paths:
        p = pattern.rstrip("/")
        if rel == p or rel.startswith(p + "/"):
            return True
    return False


def enforce_path_policy(
    profile: SandboxProfile,
    path: str,
    action: str,
) -> SandboxDecision:
    if action == "read" and not profile.allow_read:
        return SandboxDecision(
            allowed=False,
            reason="read denied by profile",
            violation=SandboxViolation.make(
                profile.profile_name, action, "read denied by profile",
                attempted_path=path,
            ),
        )
    if action == "write" and not profile.allow_write:
        return SandboxDecision(
            allowed=False,
            reason="write denied by profile",
            violation=SandboxViolation.make(
                profile.profile_name, action, "write denied by profile",
                attempted_path=path,
            ),
        )
    try:
        rel = resolve_workspace_path(profile.workspace_root, path)
    except PathResolutionError as e:
        return SandboxDecision(
            allowed=False,
            reason=str(e),
            violation=SandboxViolation.make(
                profile.profile_name, action, str(e), attempted_path=path,
            ),
        )
    if not profile.allow_secrets and is_secret_like_path(rel):
        return SandboxDecision(
            allowed=False,
            reason="secret-like path protected by default",
            violation=SandboxViolation.make(
                profile.profile_name, action,
                "secret-like path protected by default",
                attempted_path=rel,
            ),
        )
    if not is_path_allowed(profile, path, action=action):
        return SandboxDecision(
            allowed=False,
            reason="path outside allowed prefixes",
            violation=SandboxViolation.make(
                profile.profile_name, action,
                "path outside allowed prefixes", attempted_path=rel,
            ),
        )
    return SandboxDecision(allowed=True, reason="ok")


def _profile_templates() -> dict[str, dict[str, Any]]:
    return {
        SandboxProfileName.NO_EXEC_READONLY.value: dict(
            allow_read=True, allow_write=False, allow_exec=False,
            allow_network=False, allow_env=False, allow_secrets=False,
            unsafe=False, backend_name="UnsafeLocalSandbox",
            limitations=["no writes", "no execution", "network denied by policy"],
        ),
        SandboxProfileName.RESTRICTED_LOCAL.value: dict(
            allow_read=True, allow_write=True, allow_exec=True,
            allow_network=False, allow_env=False, allow_secrets=False,
            max_timeout_seconds=30.0, unsafe=False,
            backend_name="UnsafeLocalSandbox",
            limitations=[
                "network denied by policy (unsafe local backend cannot enforce network isolation)",
                "secrets denied by default",
            ],
        ),
        SandboxProfileName.UNSAFE_LOCAL_DEMO.value: dict(
            allow_read=True, allow_write=True, allow_exec=True,
            allow_network=True, allow_env=True, allow_secrets=False,
            max_timeout_seconds=60.0, unsafe=True,
            backend_name="UnsafeLocalSandbox",
            limitations=[
                "NOT a security boundary — demo/trusted workloads only",
                "network and host visibility NOT blocked",
            ],
        ),
        SandboxProfileName.DOCKER.value: dict(
            allow_read=True, allow_write=True, allow_exec=True,
            allow_network=False, allow_env=False, allow_secrets=False,
            max_timeout_seconds=60.0, unsafe=False,
            backend_name="DockerSandbox",
            limitations=["requires docker daemon", "partial — container isolation when available"],
        ),
        SandboxProfileName.BUBBLEWRAP.value: dict(
            allow_read=True, allow_write=True, allow_exec=True,
            allow_network=False, allow_env=False, allow_secrets=False,
            max_timeout_seconds=60.0, unsafe=False,
            backend_name="BubblewrapSandbox",
            limitations=["requires bwrap", "Linux only"],
        ),
    }


def get_sandbox_profile(
    name: str,
    workspace_root: str,
    *,
    allowed_paths: Optional[list[str]] = None,
    disallowed_paths: Optional[list[str]] = None,
) -> SandboxProfile:
    key = name.strip().lower()
    templates = _profile_templates()
    if key not in templates:
        raise ValueError(f"unknown sandbox profile: {name}")
    tpl = dict(templates[key])
    mode = {
        SandboxProfileName.DOCKER.value: SandboxMode.DOCKER,
        SandboxProfileName.BUBBLEWRAP.value: SandboxMode.BUBBLEWRAP,
        SandboxProfileName.UNSAFE_LOCAL_DEMO.value: SandboxMode.UNSAFE_LOCAL,
    }.get(key, SandboxMode.UNSAFE_LOCAL)
    return SandboxProfile(
        profile_name=key,
        mode=mode,
        workspace_root=os.path.abspath(workspace_root),
        allowed_paths=list(allowed_paths or ["*"]),
        disallowed_paths=list(disallowed_paths or []),
        **tpl,
    )


def materialize_sandbox_backend(profile: SandboxProfile) -> SandboxBackend:
    root = profile.workspace_root
    os.makedirs(root, exist_ok=True)
    if profile.profile_name == SandboxProfileName.DOCKER.value:
        return DockerSandbox.create(root=root, max_output_bytes=profile.max_output_bytes)
    if profile.profile_name == SandboxProfileName.BUBBLEWRAP.value:
        return BubblewrapSandbox.create(root=root, max_output_bytes=profile.max_output_bytes)
    return UnsafeLocalSandbox(
        root=root,
        max_output_bytes=profile.max_output_bytes,
    )


def create_profiled_sandbox(
    profile_name: str,
    workspace_root: str,
    *,
    allowed_paths: Optional[list[str]] = None,
    disallowed_paths: Optional[list[str]] = None,
) -> tuple["ProfiledSandbox", SandboxPolicy]:
    profile = get_sandbox_profile(
        profile_name, workspace_root,
        allowed_paths=allowed_paths,
        disallowed_paths=disallowed_paths,
    )
    try:
        backend = materialize_sandbox_backend(profile)
    except SandboxUnavailableError as e:
        raise SandboxUnavailableError(e.mode, e.reason) from e
    policy = SandboxPolicy(profile)
    return ProfiledSandbox(backend, policy), policy


def backend_availability(profile_name: str) -> tuple[bool, str]:
    key = profile_name.strip().lower()
    if key == SandboxProfileName.DOCKER.value:
        ok = DockerSandbox.is_available()
        return ok, "docker available" if ok else "docker not available"
    if key == SandboxProfileName.BUBBLEWRAP.value:
        ok = BubblewrapSandbox.is_available()
        return ok, "bubblewrap available" if ok else "bwrap not available"
    return True, "available"


def resolve_apply_sandbox_profile(
    explicit: Optional[str] = None,
) -> tuple[str, list[str]]:
    """Pick sandbox for ``--apply``: explicit profile, else hard isolation when available.

    Preference order when *explicit* is None: bubblewrap → docker → restricted_local.
    """
    limitations: list[str] = []
    if explicit:
        return explicit.strip().lower(), limitations
    if BubblewrapSandbox.is_available():
        return SandboxProfileName.BUBBLEWRAP.value, limitations
    if DockerSandbox.is_available():
        return SandboxProfileName.DOCKER.value, limitations
    limitations.append(
        "hard sandbox (bubblewrap/docker) unavailable; using restricted_local — "
        "install bwrap or docker for production apply workflows"
    )
    return SandboxProfileName.RESTRICTED_LOCAL.value, limitations


class SandboxPolicy:
    """Evaluate tool and path requests against a sandbox profile."""

    def __init__(
        self,
        profile: SandboxProfile,
        capabilities: SandboxCapabilityMap | None = None,
    ) -> None:
        self.profile = profile
        self.capabilities = capabilities or DEFAULT_CAPABILITY_MAP

    def diagnostics(self, backend: SandboxBackend) -> SandboxDiagnostics:
        avail, _ = backend_availability(self.profile.profile_name)
        limits = list(self.profile.limitations)
        if self.profile.unsafe:
            limits = [UnsafeLocalSandbox.UNSAFE_WARNING, *limits]
        if not self.profile.allow_network and backend.mode is SandboxMode.UNSAFE_LOCAL:
            limits.append("network not blocked by unsafe local backend")
        return SandboxDiagnostics(
            active_profile=self.profile.profile_name,
            backend_name=type(backend).__name__,
            workspace_root=self.profile.workspace_root,
            network_allowed=self.profile.allow_network,
            secrets_allowed=self.profile.allow_secrets,
            write_allowed=self.profile.allow_write,
            exec_allowed=self.profile.allow_exec,
            read_allowed=self.profile.allow_read,
            unsafe=self.profile.unsafe,
            limitations=limits,
            backend_available=avail,
            hard_isolated=bool(getattr(backend, "is_hard_isolated", False)),
            security_boundary=bool(getattr(backend, "is_security_boundary", False)),
        )

    def check_path(self, path: str, action: str) -> SandboxDecision:
        return enforce_path_policy(self.profile, path, action)

    def check_tool(
        self,
        tool_name: str,
        tool_spec: Optional["ToolSpec"],
        args: dict[str, Any],
    ) -> SandboxDecision:
        if tool_name in self.capabilities.network_tools:
            return self._deny_tool(
                tool_name, "network tools are not implemented",
                attempted_action="network",
            )
        if tool_name in self.capabilities.exec_tools and not self.profile.allow_exec:
            return self._deny_tool(tool_name, "execution denied by sandbox profile", "exec")
        if tool_name in self.capabilities.write_tools and not self.profile.allow_write:
            return self._deny_tool(tool_name, "write denied by sandbox profile", "write")
        if tool_name in self.capabilities.read_tools and not self.profile.allow_read:
            return self._deny_tool(tool_name, "read denied by sandbox profile", "read")

        if tool_spec is not None:
            cap = tool_spec.metadata.side_effect_type.value
            if cap == "filesystem_write" and not self.profile.allow_write:
                return self._deny_tool(tool_name, "write side effect denied", "write")
            if cap == "shell_execution" and not self.profile.allow_exec:
                return self._deny_tool(tool_name, "shell execution denied", "exec")
            if cap == "filesystem_read" and not self.profile.allow_read:
                return self._deny_tool(tool_name, "read side effect denied", "read")

        for key in ("path", "repo_path", "root"):
            if key in args and isinstance(args[key], str):
                action = "write" if tool_name in self.capabilities.write_tools else "read"
                if tool_name in self.capabilities.exec_tools:
                    action = "read"
                decision = self.check_path(args[key], action)
                if not decision.allowed:
                    if decision.violation:
                        decision.violation.tool_name = tool_name
                    return decision
        return SandboxDecision(allowed=True, reason="ok")

    def execution_context(self, backend: SandboxBackend, command_id: str = "") -> SandboxExecutionContext:
        limits = self.profile.execution_limits
        return SandboxExecutionContext(
            sandbox=backend,
            profile=self.profile,
            limits=limits,
            command_id=command_id,
            timeout_seconds=limits.timeout_seconds,
        )

    def _deny_tool(self, tool_name: str, reason: str, attempted_action: str) -> SandboxDecision:
        return SandboxDecision(
            allowed=False,
            reason=reason,
            violation=SandboxViolation.make(
                self.profile.profile_name,
                attempted_action,
                reason,
                tool_name=tool_name,
            ),
        )


class ProfiledSandbox:
    """Sandbox backend wrapper that enforces profile policy at the FS/exec boundary."""

    def __init__(self, backend: SandboxBackend, policy: SandboxPolicy) -> None:
        self._backend = backend
        self.policy = policy
        self.profile = policy.profile

    @property
    def mode(self) -> SandboxMode:
        return self._backend.mode

    @property
    def root(self) -> str:
        return self._backend.root

    @property
    def is_hard_isolated(self) -> bool:
        return self._backend.is_hard_isolated

    @property
    def is_security_boundary(self) -> bool:
        return self._backend.is_security_boundary

    def _guard(self, path: str, action: str) -> None:
        decision = self.policy.check_path(path, action)
        if not decision.allowed:
            raise SandboxViolationError(decision.violation or SandboxViolation.make(
                self.profile.profile_name, action, decision.reason, attempted_path=path,
            ))

    def read_file(self, rel: str) -> str:
        self._guard(rel, "read")
        return self._backend.read_file(rel)

    def write_file(self, rel: str, content: str) -> None:
        self._guard(rel, "write")
        return self._backend.write_file(rel, content)

    def list_dir(self, rel: str = ".") -> list[str]:
        self._guard(rel, "read")
        return self._backend.list_dir(rel)

    def run_shell(self, cmd: list[str], timeout: float = DEFAULT_TIMEOUT_S) -> Any:
        if not self.profile.allow_exec:
            raise SandboxViolationError(SandboxViolation.make(
                self.profile.profile_name, "exec", "execution denied by sandbox profile",
            ))
        cap = min(timeout, self.profile.max_timeout_seconds)
        return self._backend.run_shell(cmd, timeout=cap)

    def state_hash(self) -> str:
        return self._backend.state_hash()

    def snapshot(self) -> str:
        return self._backend.snapshot()

    def rollback(self, snapshot_id: str) -> None:
        return self._backend.rollback(snapshot_id)
