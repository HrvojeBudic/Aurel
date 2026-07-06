"""
sandbox.py — Sandbox backends for governed command execution.

Security model
--------------
- ``UnsafeLocalSandbox`` — **NOT a security boundary**. Demo/trusted workloads only.
  Subprocesses inherit host visibility; ``cwd`` confinement is not isolation.

- ``BubblewrapSandbox`` / ``DockerSandbox`` — hard isolation backends implementing
  ``SandboxBackend``. No silent fallback to unsafe mode.

Runtime and tools depend only on the ``SandboxBackend`` protocol.
"""
from __future__ import annotations

import enum
import os
import platform
import resource
import shutil
import subprocess  # nosec B404 - subprocess is the explicit execution backend for sandbox implementations
import tempfile
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol, runtime_checkable

from .canonical_path import CanonicalPathResolver, PathResolutionError
from .core_types import new_id, sha

if TYPE_CHECKING:
    from .state_store import StateStore

# Retained write snapshots per workspace backend. Oldest entries are evicted under pressure.
DEFAULT_MAX_SNAPSHOTS = 64
SANDBOX_TMPDIR = os.path.join(os.sep, "tmp")


def max_snapshots_limit() -> int:
    """Resolve snapshot retention cap (override via AGENTIC_MAX_SNAPSHOTS)."""
    raw = os.environ.get("AGENTIC_MAX_SNAPSHOTS", "").strip()
    if raw.isdigit():
        return max(1, int(raw))
    return DEFAULT_MAX_SNAPSHOTS


MAX_SNAPSHOTS = DEFAULT_MAX_SNAPSHOTS

DEFAULT_MAX_OUTPUT_BYTES = 256 * 1024
DEFAULT_TIMEOUT_S = 10.0

# Functional availability probes execute a trivial command through the same
# invocation the backend uses for real workloads, so "available" can never be
# claimed on a host where actual isolation fails (e.g. userns restrictions,
# snap-docker seccomp). Results are cached per process with a short TTL.
_PROBE_TTL_S = 60.0
_PROBE_CACHE: dict[str, tuple[float, bool, str]] = {}


def _cached_probe(key: str, prober: "Callable[[], tuple[bool, str]]") -> tuple[bool, str]:
    hit = _PROBE_CACHE.get(key)
    now_m = time.monotonic()
    if hit is not None and now_m - hit[0] < _PROBE_TTL_S:
        return hit[1], hit[2]
    ok, reason = prober()
    _PROBE_CACHE[key] = (now_m, ok, reason)
    return ok, reason


def clear_probe_cache() -> None:
    """Drop cached probe results (tests / doctor --no-cache)."""
    _PROBE_CACHE.clear()


class SandboxMode(str, enum.Enum):
    UNSAFE_LOCAL = "unsafe_local"
    BUBBLEWRAP = "bubblewrap"
    DOCKER = "docker"


class SandboxUnavailableError(RuntimeError):
    """Raised when a hard sandbox backend is requested but cannot be provisioned."""

    def __init__(self, mode: SandboxMode, reason: str) -> None:
        self.mode = mode
        self.reason = reason
        super().__init__(f"sandbox mode {mode.value} unavailable: {reason}")


@dataclass
class ExecResult:
    """Structured result from ``SandboxBackend.run_shell``."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    truncated: bool = False
    fs_diff: dict[str, str] = field(default_factory=dict)
    sandbox_mode: str = ""
    error_kind: str = ""  # "", "timeout", "unavailable", "sandbox_error"

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.error_kind


@runtime_checkable
class SandboxBackend(Protocol):
    """Interface consumed by ToolRuntime, PolicyEngine, and StateVerifier."""

    mode: SandboxMode
    root: str

    @property
    def is_hard_isolated(self) -> bool: ...

    @property
    def is_security_boundary(self) -> bool: ...

    def read_file(self, rel: str) -> str: ...
    def write_file(self, rel: str, content: str) -> None: ...
    def delete_file(self, rel: str) -> None: ...
    def list_dir(self, rel: str = ".") -> list[str]: ...
    def run_shell(self, cmd: list[str], timeout: float = DEFAULT_TIMEOUT_S) -> ExecResult: ...
    def state_hash(self) -> str: ...
    def snapshot(self) -> str: ...
    def rollback(self, snapshot_id: str) -> None: ...
    def read_snapshot_file(self, snapshot_id: str, rel: str) -> str: ...
    def release_snapshot(self, snapshot_id: str) -> None: ...
    def active_snapshot_count(self) -> int: ...


# Backward-compatible alias used across the codebase.
Sandbox = SandboxBackend
SafeSandbox = SandboxBackend


# --------------------------------------------------------------------------- #
#  Shared helpers
# --------------------------------------------------------------------------- #
def _tree_hash(root: str) -> str:
    parts: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            try:
                with open(fp, "rb") as f:
                    parts.append(rel + ":" + sha(f.read().decode("utf-8", "replace")))
            except OSError:
                parts.append(rel + ":<unreadable>")
    return sha("|".join(parts))


def _tree_map(root: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            try:
                with open(fp, "rb") as f:
                    out[rel] = sha(f.read().decode("utf-8", "replace"))
            except OSError:
                out[rel] = "<unreadable>"
    return out


def _diff_trees(before: dict[str, str], after: dict[str, str]) -> dict[str, str]:
    diff: dict[str, str] = {}
    for p in after.keys() - before.keys():
        diff[p] = "added"
    for p in before.keys() - after.keys():
        diff[p] = "deleted"
    for p in before.keys() & after.keys():
        if before[p] != after[p]:
            diff[p] = "modified"
    return diff


def _cap_stream(text: str, limit: int = DEFAULT_MAX_OUTPUT_BYTES) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    omitted = len(text) - limit
    return text[:limit] + f"\n<output truncated: {omitted} bytes omitted>", True


def _decode_stream(data: str | bytes | None) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def _resolve_executable_path(name: str) -> tuple[str | None, str]:
    resolved = shutil.which(name)
    if resolved is None:
        return None, f"{name} executable not found"
    return os.path.abspath(resolved), "ok"


def _validated_subprocess_cmd(cmd: list[str]) -> list[str]:
    """Fail closed on malformed argv before invoking a subprocess.

    This validates argv structure only. Callers remain responsible for policy,
    approval, and sandbox selection before execution reaches this boundary.
    """
    if not isinstance(cmd, list):
        raise TypeError("cmd must be a list[str]")
    if not cmd:
        raise ValueError("cmd must not be empty")

    validated: list[str] = []
    for index, part in enumerate(cmd):
        if not isinstance(part, str):
            raise TypeError(f"cmd[{index}] must be str")
        if not part:
            raise ValueError(f"cmd[{index}] must not be empty")
        if "\x00" in part:
            raise ValueError(f"cmd[{index}] must not contain NUL bytes")
        validated.append(part)
    return validated


def _run_subprocess(
    cmd: list[str],
    *,
    cwd: str,
    env: dict[str, str],
    timeout: float,
    sandbox_mode: SandboxMode,
    max_output: int = DEFAULT_MAX_OUTPUT_BYTES,
    preexec_fn: Optional[Callable[[], None]] = None,
    fs_root: Optional[str] = None,
) -> ExecResult:
    cmd = _validated_subprocess_cmd(cmd)
    before = _tree_map(fs_root) if fs_root else {}
    timed_out = False
    truncated = False
    error_kind = ""
    try:
        proc = subprocess.run(  # nosec B603 - argv is validated here; policy and approval occur before sandbox execution
            cmd, cwd=cwd, env=env, preexec_fn=preexec_fn,
            capture_output=True, timeout=timeout)
        code = proc.returncode
        out = _decode_stream(proc.stdout)
        err = _decode_stream(proc.stderr)
    except subprocess.TimeoutExpired as e:
        timed_out = True
        error_kind = "timeout"
        code = 124
        out = _decode_stream(e.stdout)
        err = _decode_stream(e.stderr) + "\n<timeout>"
    except FileNotFoundError as e:
        code = 127
        out, err = "", f"sandbox executable not found: {e}"
        error_kind = "unavailable"
    except OSError as e:
        code = 127
        out, err = "", f"sandbox error: {e}"
        error_kind = "sandbox_error"

    out, t_out = _cap_stream(out, max_output)
    err, t_err = _cap_stream(err, max_output)
    truncated = t_out or t_err

    after = _tree_map(fs_root) if fs_root else {}
    return ExecResult(
        exit_code=code, stdout=out, stderr=err,
        timed_out=timed_out, truncated=truncated,
        fs_diff=_diff_trees(before, after) if fs_root else {},
        sandbox_mode=sandbox_mode.value, error_kind=error_kind,
    )


def _scrubbed_env(root: str) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": root,
        "TMPDIR": root,
        "LANG": "C.UTF-8",
    }


class _WorkspaceBackend:
    """Shared host-side filesystem operations with canonical path resolution."""

    mode: SandboxMode
    is_hard_isolated: bool
    is_security_boundary: bool

    def __init__(self, root: str, mode: SandboxMode,
                 hard: bool, security_boundary: bool) -> None:
        self.root = root
        self.mode = mode
        self.is_hard_isolated = hard
        self.is_security_boundary = security_boundary
        self._snapshots: dict[str, str] = {}
        self._paths = CanonicalPathResolver(self.root)

    def _abs(self, rel: str) -> str:
        try:
            return self._paths.resolve(rel).absolute
        except PathResolutionError as e:
            raise PermissionError(str(e)) from e

    def read_file(self, rel: str) -> str:
        with open(self._abs(rel), "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def write_file(self, rel: str, content: str) -> None:
        p = self._abs(rel)
        parent = os.path.dirname(p)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def delete_file(self, rel: str) -> None:
        os.remove(self._abs(rel))

    def list_dir(self, rel: str = ".") -> list[str]:
        return sorted(os.listdir(self._abs(rel)))

    def state_hash(self) -> str:
        return _tree_hash(self.root)

    # ----------------------------------------------------------------------- #
    #  Content-addressed state store (M0) — additive, retained, parallel to the
    #  ephemeral snapshot/rollback path below. These never mutate ``_snapshots``.
    # ----------------------------------------------------------------------- #
    def commit_state(self, store: "StateStore") -> str:
        """Persist the current workspace into the content-addressed store.

        Returns the content hash (== ``state_hash()``). Unlike ``snapshot()``,
        the committed state is keyed by content and retained for later
        ``checkout`` / fork; it does not participate in ``rollback``.
        """
        return store.put(self.root)

    def checkout(
        self, store: "StateStore", state_hash: str, *, root: Optional[str] = None
    ) -> "_WorkspaceBackend":
        """Materialize a stored state into a fresh backend of the same kind.

        Reconstructs ``state_hash`` into a new (empty) root and returns a new
        backend rooted there. The receiver is left untouched.
        """
        new_root = root or tempfile.mkdtemp(prefix="ar_checkout_")
        os.makedirs(new_root, exist_ok=True)
        store.materialize(state_hash, new_root)
        return type(self)(root=new_root)

    def snapshot(self) -> str:
        snap_dir = tempfile.mkdtemp(prefix="ar_snap_")
        dst = os.path.join(snap_dir, "tree")
        shutil.copytree(self.root, dst)
        sid = new_id("snap")
        self._snapshots[sid] = dst
        self._evict_snapshots_if_needed()
        return sid

    def rollback(self, snapshot_id: str) -> None:
        src = self._snapshots.get(snapshot_id)
        if not src:
            raise KeyError(f"unknown snapshot {snapshot_id}")
        shutil.rmtree(self.root)
        shutil.copytree(src, self.root)
        self._paths = CanonicalPathResolver(self.root)
        self._release_snapshot(snapshot_id)

    def read_snapshot_file(self, snapshot_id: str, rel: str) -> str:
        src = self._snapshots.get(snapshot_id)
        if not src:
            raise KeyError(f"unknown snapshot {snapshot_id}")
        try:
            resolved = CanonicalPathResolver(src).resolve(rel)
            path = resolved.absolute
        except PathResolutionError as e:
            raise PermissionError(
                f"snapshot path rejected: {e}"
            ) from e
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def release_snapshot(self, snapshot_id: str) -> None:
        self._release_snapshot(snapshot_id)

    def active_snapshot_count(self) -> int:
        return len(self._snapshots)

    def _evict_snapshots_if_needed(self) -> None:
        limit = max_snapshots_limit()
        while len(self._snapshots) > limit:
            old_id, _ = next(iter(self._snapshots.items()))
            self._release_snapshot(old_id)

    def _release_snapshot(self, snapshot_id: str) -> None:
        path = self._snapshots.pop(snapshot_id, None)
        if path:
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)


# --------------------------------------------------------------------------- #
#  Unsafe local — NOT a security boundary
# --------------------------------------------------------------------------- #
class UnsafeLocalSandbox(_WorkspaceBackend):
    """Demo/trusted-only backend. **Not a security boundary.**

    Runs subprocesses with ``cwd`` set to the workspace root and rlimits applied,
    but processes retain host filesystem, network, and privilege visibility.
    Use only when the caller explicitly opts into ``SandboxMode.UNSAFE_LOCAL``.
    """

    UNSAFE_WARNING = (
        "UnsafeLocalSandbox is NOT a security boundary — demo/trusted workloads only"
    )

    def __init__(self, root: Optional[str] = None,
                 cpu_seconds: int = 10, mem_mb: int = 512,
                 max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES) -> None:
        root = root or tempfile.mkdtemp(prefix="ar_unsafe_")
        os.makedirs(root, exist_ok=True)
        super().__init__(root, SandboxMode.UNSAFE_LOCAL, hard=False, security_boundary=False)
        self.cpu_seconds = cpu_seconds
        self.mem_mb = mem_mb
        self.max_output_bytes = max_output_bytes

    def run_shell(self, cmd: list[str], timeout: float = DEFAULT_TIMEOUT_S) -> ExecResult:
        def _limit() -> None:
            resource.setrlimit(resource.RLIMIT_CPU,
                               (self.cpu_seconds, self.cpu_seconds))
            soft = self.mem_mb * 1024 * 1024
            try:
                resource.setrlimit(resource.RLIMIT_AS, (soft, soft))
            except (ValueError, OSError):
                pass
            os.setsid()

        return _run_subprocess(
            cmd, cwd=self.root, env=_scrubbed_env(self.root), timeout=timeout,
            sandbox_mode=self.mode, max_output=self.max_output_bytes,
            preexec_fn=_limit, fs_root=self.root,
        )


LocalSubprocessSandbox = UnsafeLocalSandbox  # deprecated alias


# --------------------------------------------------------------------------- #
#  Bubblewrap — Linux hard isolation
# --------------------------------------------------------------------------- #
def _bubblewrap_available() -> tuple[bool, str]:
    """Functional probe: run ``/bin/true`` through the production bwrap invocation.

    ``bwrap --version`` succeeds on hosts where namespace creation is blocked
    (e.g. ``kernel.apparmor_restrict_unprivileged_userns=1``), so availability
    is only claimed after a real sandboxed execution exits 0.
    """
    return _cached_probe("bubblewrap", _probe_bubblewrap)


def _probe_bubblewrap() -> tuple[bool, str]:
    executable, reason = _resolve_executable_path("bwrap")
    if executable is None:
        return False, reason
    workspace = tempfile.mkdtemp(prefix="ar_bwrap_probe_")
    try:
        probe_cmd = _bubblewrap_cmd(workspace, ["/bin/true"], executable)
        proc = subprocess.run(  # nosec B603 - fixed functional probe through the production invocation
            probe_cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            return True, f"{executable} (functional probe ok)"
        detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        return False, f"bwrap functional probe failed: {detail}"
    except FileNotFoundError:
        return False, "bwrap executable not found"
    except subprocess.TimeoutExpired:
        return False, "bwrap functional probe timed out"
    except OSError as e:
        return False, str(e)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def _bubblewrap_cmd(workspace: str, cmd: list[str], executable: str) -> list[str]:
    """Build a bubblewrap invocation with network blocked and workspace bind."""
    work = "/work"
    args = [
        executable,
        "--unshare-all",
        "--unshare-net",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--setenv", "PATH", "/usr/bin:/bin",
        "--setenv", "LANG", "C.UTF-8",
        "--setenv", "HOME", work,
        "--setenv", "TMPDIR", SANDBOX_TMPDIR,
        "--dir", SANDBOX_TMPDIR,
        "--dir", work,
        "--bind", workspace, work,
        "--chdir", work,
        "--proc", "/proc",
        "--dev", "/dev",
    ]
    for host_path in ("/usr", "/bin", "/lib", "/lib64"):
        if os.path.isdir(host_path):
            args.extend(["--ro-bind", host_path, host_path])
    args.append("--")
    args.extend(cmd)
    return args


class BubblewrapSandbox(_WorkspaceBackend):
    """Linux bubblewrap backend — real isolation boundary when bwrap is available."""

    def __init__(self, root: Optional[str] = None,
                 max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES) -> None:
        root = root or tempfile.mkdtemp(prefix="ar_bwrap_")
        os.makedirs(root, exist_ok=True)
        super().__init__(root, SandboxMode.BUBBLEWRAP, hard=True, security_boundary=True)
        self.max_output_bytes = max_output_bytes

    @classmethod
    def is_available(cls) -> bool:
        ok, _ = _bubblewrap_available()
        return ok

    @classmethod
    def create(cls, root: Optional[str] = None, **kwargs) -> BubblewrapSandbox:
        ok, reason = _bubblewrap_available()
        if not ok:
            raise SandboxUnavailableError(SandboxMode.BUBBLEWRAP, reason)
        return cls(root=root, **kwargs)

    def run_shell(self, cmd: list[str], timeout: float = DEFAULT_TIMEOUT_S) -> ExecResult:
        executable, reason = _resolve_executable_path("bwrap")
        if executable is None:
            return ExecResult(
                exit_code=127,
                stdout="",
                stderr=reason,
                sandbox_mode=self.mode.value,
                error_kind="unavailable",
            )
        bwrap = _bubblewrap_cmd(self.root, cmd, executable)
        return _run_subprocess(
            bwrap, cwd=self.root, env=os.environ.copy(), timeout=timeout,
            sandbox_mode=self.mode, max_output=self.max_output_bytes,
            fs_root=self.root,
        )


# --------------------------------------------------------------------------- #
#  Docker — container hard isolation
# --------------------------------------------------------------------------- #
DOCKER_DEFAULT_IMAGE = "python:3.12-slim"


def _docker_hardening_flags(mem_mb: int, pids: int) -> list[str]:
    """Isolation flags shared by the functional probe and ``run_shell``.

    Keeping these in one place means the availability probe exercises the exact
    security posture real workloads run under — so a host where a flag such as
    ``--security-opt no-new-privileges`` breaks exec (snap-docker) reports
    UNAVAILABLE instead of a false green.
    """
    return [
        "--rm", "--network", "none",
        "--memory", f"{mem_mb}m", "--pids-limit", str(pids),
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--read-only", "--tmpfs", f"{SANDBOX_TMPDIR}:exec",
    ]


def _docker_available(image: str = DOCKER_DEFAULT_IMAGE) -> tuple[bool, str]:
    """Functional probe: run ``true`` in a fully hardened container.

    ``docker info`` succeeds on daemons where the hardened container cannot
    actually exec (seccomp/apparmor under snap), so availability is claimed
    only after a real hardened run exits 0.
    """
    return _cached_probe(f"docker::{image}", lambda: _probe_docker(image))


def _probe_docker(image: str) -> tuple[bool, str]:
    executable, reason = _resolve_executable_path("docker")
    if executable is None:
        return False, reason
    docker_cmd = [
        executable, "run", *_docker_hardening_flags(64, 64),
        image, "true",
    ]
    try:
        proc = subprocess.run(  # nosec B603 - functional probe through the production hardened invocation
            docker_cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode == 0:
            return True, f"{executable} (hardened probe ok, image {image})"
        detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        return False, f"docker hardened probe failed: {detail}"
    except FileNotFoundError:
        return False, "docker executable not found"
    except subprocess.TimeoutExpired:
        return False, "docker hardened probe timed out"
    except OSError as e:
        return False, str(e)


class DockerSandbox(_WorkspaceBackend):
    """Docker container backend — hard isolation when docker is available."""

    def __init__(self, image: str = DOCKER_DEFAULT_IMAGE, root: Optional[str] = None,
                 mem_mb: int = 512, pids: int = 128,
                 max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES) -> None:
        root = root or tempfile.mkdtemp(prefix="ar_docker_")
        os.makedirs(root, exist_ok=True)
        super().__init__(root, SandboxMode.DOCKER, hard=True, security_boundary=True)
        self.image = image
        self.mem_mb = mem_mb
        self.pids = pids
        self.max_output_bytes = max_output_bytes

    @classmethod
    def is_available(cls) -> bool:
        ok, _ = _docker_available()
        return ok

    @classmethod
    def create(cls, root: Optional[str] = None, **kwargs) -> DockerSandbox:
        ok, reason = _docker_available(kwargs.get("image", DOCKER_DEFAULT_IMAGE))
        if not ok:
            raise SandboxUnavailableError(SandboxMode.DOCKER, reason)
        return cls(root=root, **kwargs)

    def run_shell(self, cmd: list[str], timeout: float = DEFAULT_TIMEOUT_S) -> ExecResult:
        executable, reason = _resolve_executable_path("docker")
        if executable is None:
            return ExecResult(
                exit_code=127,
                stdout="",
                stderr=reason,
                sandbox_mode=self.mode.value,
                error_kind="unavailable",
            )
        docker_cmd = [
            executable, "run", *_docker_hardening_flags(self.mem_mb, self.pids),
            "-v", f"{self.root}:/work:rw", "-w", "/work", self.image, *cmd,
        ]
        return _run_subprocess(
            docker_cmd, cwd=self.root, env=os.environ.copy(), timeout=timeout,
            sandbox_mode=self.mode, max_output=self.max_output_bytes,
            fs_root=self.root,
        )


# --------------------------------------------------------------------------- #
#  Host attestation — proof of what isolation the host can actually provide
# --------------------------------------------------------------------------- #
def _read_userns_sysctl() -> str:
    """Best-effort read of the apparmor userns restriction, for the fingerprint."""
    for path in (
        "/proc/sys/kernel/apparmor_restrict_unprivileged_userns",
        "/proc/sys/kernel/unprivileged_userns_clone",
    ):
        try:
            with open(path, encoding="utf-8") as f:
                return f"{os.path.basename(path)}={f.read().strip()}"
        except OSError:
            continue
    return "userns_sysctl=unknown"


def host_fingerprint() -> dict[str, str]:
    """Stable identity of the host's isolation-relevant configuration."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "userns": _read_userns_sysctl(),
    }


def probe_backend(mode: SandboxMode) -> dict[str, Any]:
    """Run the functional probe for one backend and return an attestation dict.

    This is the single source of truth for "can this host provide backend X",
    consumed by ``build_runtime`` (attestation record), ``doctor``, and
    ``_auto_hard_sandbox``.
    """
    if mode is SandboxMode.BUBBLEWRAP:
        ok, reason = _bubblewrap_available()
        probe = "bwrap /bin/true through production invocation"
    elif mode is SandboxMode.DOCKER:
        ok, reason = _docker_available()
        probe = "docker run --cap-drop ALL --security-opt no-new-privileges --read-only true"
    elif mode is SandboxMode.UNSAFE_LOCAL:
        ok, reason = True, "unsafe local — NOT a security boundary"
        probe = "none"
    else:
        ok, reason = False, f"unknown mode {mode}"
        probe = "none"
    return {
        "backend": mode.value,
        "available": ok,
        "reason": reason,
        "probe": probe,
        "hard_isolated": ok and mode in (SandboxMode.BUBBLEWRAP, SandboxMode.DOCKER),
        "host": host_fingerprint(),
    }


# --------------------------------------------------------------------------- #
#  Factory — no silent downgrade
# --------------------------------------------------------------------------- #
def create_sandbox(
    mode: SandboxMode = SandboxMode.UNSAFE_LOCAL,
    *,
    root: Optional[str] = None,
    allow_unsafe: bool = False,
    **kwargs,
) -> SandboxBackend:
    """Provision a sandbox backend. Hard modes raise if unavailable — never downgrade."""
    if mode is SandboxMode.UNSAFE_LOCAL:
        if not allow_unsafe:
            raise ValueError(
                "SandboxMode.UNSAFE_LOCAL requires allow_unsafe=True — "
                "it is NOT a security boundary")
        return UnsafeLocalSandbox(root=root, **kwargs)
    if mode is SandboxMode.BUBBLEWRAP:
        return BubblewrapSandbox.create(root=root, **kwargs)
    if mode is SandboxMode.DOCKER:
        return DockerSandbox.create(root=root, **kwargs)
    raise ValueError(f"unknown sandbox mode: {mode}")
