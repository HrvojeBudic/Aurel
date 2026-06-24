"""tools.py — Tool Bus v1.

The Tool Bus is the controlled execution surface exposed to ``AgenticRuntime``.
It is *not* an authority system: it registers tools, validates contracts when a
contract registry is bound, executes handlers inside the sandbox, and returns
structured results. Policy, HITL, budget, verifier, trace, and memory governance
remain Runtime responsibilities.
"""
from __future__ import annotations

import fnmatch
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from .core_types import CommandEnvelope, ObservationEnvelope, now
from .model_providers.http_utils import fetch_url_bytes
from .sandbox import SandboxBackend
from .sandbox_policy import SandboxExecutionContext, SandboxPolicy
from .tool_contracts import (ContractValidationResult, ToolContractRegistry,
                             ToolInputValidator)


class ToolSideEffectType(str, Enum):
    NONE = "none"
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    SHELL_EXECUTION = "shell_execution"


class ToolRiskLevel(str, Enum):
    TRIVIAL = "trivial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolSandboxRequirement(str, Enum):
    WORKSPACE = "workspace"
    HARD_ISOLATION_RECOMMENDED = "hard_isolation_recommended"
    HARD_ISOLATION_REQUIRED = "hard_isolation_required"


class ToolVerifierRequirement(str, Enum):
    NONE = "none"
    EXIT_STATUS = "exit_status"
    STATE_VERIFIER = "state_verifier"


@dataclass
class ToolError:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolMetadata:
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    required_capabilities: list[str] = field(default_factory=list)
    side_effect_type: ToolSideEffectType = ToolSideEffectType.NONE
    sandbox_requirement: ToolSandboxRequirement = ToolSandboxRequirement.WORKSPACE
    verifier_requirement: ToolVerifierRequirement = ToolVerifierRequirement.NONE


@dataclass
class ToolExecutionContext:
    sandbox: SandboxBackend
    command_id: str = ""
    timeout_seconds: float = 10.0
    sandbox_policy: Optional[SandboxPolicy] = None
    sandbox_context: Optional[SandboxExecutionContext] = None


@dataclass
class ToolExecutionResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    error: Optional[ToolError] = None

    def to_observation(self, command_id: str) -> ObservationEnvelope:
        artifacts = dict(self.artifacts)
        artifacts["tool_status"] = "ok" if self.success else "error"
        artifacts["duration_ms"] = int(self.duration_ms)
        if self.error is not None:
            artifacts["error_code"] = self.error.code
            artifacts["error_reason"] = self.error.message
        return ObservationEnvelope.make(
            command_id,
            success=self.success,
            stdout=self.stdout,
            stderr=self.stderr,
            exit_code=self.exit_code,
            artifacts=artifacts,
            duration_s=self.duration_ms / 1000.0,
        )


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    handler: Callable[[SandboxBackend, dict], ObservationEnvelope | ToolExecutionResult]
    output_schema: dict = field(default_factory=dict)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    required_capabilities: list[str] = field(default_factory=list)
    side_effect_type: ToolSideEffectType = ToolSideEffectType.NONE
    sandbox_requirement: ToolSandboxRequirement = ToolSandboxRequirement.WORKSPACE
    verifier_requirement: ToolVerifierRequirement = ToolVerifierRequirement.NONE

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            risk_level=self.risk_level,
            required_capabilities=list(self.required_capabilities),
            side_effect_type=self.side_effect_type,
            sandbox_requirement=self.sandbox_requirement,
            verifier_requirement=self.verifier_requirement,
        )


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    @property
    def registered(self) -> set[str]:
        return set(self._tools)

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"tool '{spec.name}' already registered")
        self._tools[spec.name] = spec

    def list_tools(self) -> list[ToolSpec]:
        return [self._tools[n] for n in sorted(self._tools)]

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)


class ToolBus(ToolRegistry):
    def __init__(
        self,
        sandbox: SandboxBackend,
        contracts: Optional[ToolContractRegistry] = None,
        sandbox_policy: Optional[SandboxPolicy] = None,
    ) -> None:
        super().__init__()
        self.sandbox = sandbox
        self.contracts = contracts
        self.sandbox_policy = sandbox_policy
        self.input_validator = ToolInputValidator()

    def bind_sandbox_policy(self, policy: SandboxPolicy) -> None:
        self.sandbox_policy = policy

    def bind_contracts(self, contracts: ToolContractRegistry) -> None:
        self.contracts = contracts

    def execute(self, tool_name: str, args: dict, *,
                command_id: str = "") -> ToolExecutionResult:
        spec = self.get(tool_name)
        if spec is None:
            return _tool_error("unknown_tool", f"no such tool: {tool_name}")

        if self.sandbox_policy is not None:
            sb_decision = self.sandbox_policy.check_tool(tool_name, spec, args)
            if not sb_decision.allowed:
                violation = sb_decision.violation
                return _tool_error(
                    "sandbox_violation",
                    sb_decision.reason,
                    details={
                        "violation_id": violation.violation_id if violation else "",
                        "profile_name": violation.profile_name if violation else "",
                        "attempted_action": violation.attempted_action if violation else "",
                        "attempted_path": violation.attempted_path if violation else "",
                        "severity": violation.severity if violation else "deny",
                    },
                )

        if self.contracts is not None:
            contract, gate = self.contracts.resolve_for_execution(
                tool_name, self.registered)
            if not gate.ok:
                return _contract_error(gate)
            check = self.input_validator.validate(contract, args)
            if not check.ok:
                return _contract_error(check)

        t0 = now()
        try:
            result = spec.handler(self.sandbox, args)
            if isinstance(result, ObservationEnvelope):
                out = ToolExecutionResult(
                    success=result.success,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.exit_code,
                    artifacts=dict(result.artifacts),
                    duration_ms=result.duration_s * 1000.0,
                )
            else:
                out = result
        except Exception as e:  # tools must never crash the runtime
            out = _tool_error("tool_exception", f"{type(e).__name__}: {e}")
        if out.duration_ms <= 0:
            out.duration_ms = (now() - t0) * 1000.0
        return out


class ToolRuntime(ToolBus):
    def __init__(self, sandbox: SandboxBackend,
                 sandbox_policy: Optional[SandboxPolicy] = None) -> None:
        super().__init__(sandbox, sandbox_policy=sandbox_policy)
        self._register_builtins()

    def dispatch(self, cmd: CommandEnvelope) -> ObservationEnvelope:
        result = self.execute(cmd.tool, cmd.args, command_id=cmd.id)
        obs = result.to_observation(cmd.id)
        obs.duration_s = result.duration_ms / 1000.0
        return obs

    # ---- builtins ----------------------------------------------------- #
    def _register_builtins(self) -> None:
        def read_file(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            content = sb.read_file(args["path"])
            max_bytes = args.get("max_bytes")
            truncated = False
            out = content
            if isinstance(max_bytes, int) and max_bytes >= 0:
                raw = content.encode("utf-8", "replace")
                if len(raw) > max_bytes:
                    out = raw[:max_bytes].decode("utf-8", "replace")
                    truncated = True
            return ObservationEnvelope.make("", success=True, stdout=out,
                artifacts={"path": args["path"], "content": out,
                           "bytes": len(content.encode("utf-8", "replace")),
                           "truncated": truncated})

        def write_file(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            old = None
            try:
                old = sb.read_file(args["path"])
            except OSError:
                pass
            sb.write_file(args["path"], args["content"])
            encoded = args["content"].encode("utf-8", "replace")
            return ObservationEnvelope.make("", success=True,
                artifacts={"path": args["path"], "wrote": True,
                           "bytes_written": len(encoded),
                           "changed": old != args["content"]})

        def edit_file(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            # find/replace edit; verifier later confirms the replacement landed
            content = sb.read_file(args["path"])
            old, new = args["find"], args["replace"]
            if old not in content:
                return ObservationEnvelope.make("", success=False,
                    stderr=f"find string not present in {args['path']}")
            updated = content.replace(old, new, 1)
            sb.write_file(args["path"], updated)
            return ObservationEnvelope.make("", success=True,
                artifacts={"path": args["path"], "replaced": True,
                           "find": old, "replace": new})

        def list_dir(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            root = args.get("path", ".")
            recursive = bool(args.get("recursive", False))
            entries = _list_dir(sb, root, recursive=recursive)
            return ObservationEnvelope.make("", success=True,
                stdout="\n".join(entries), artifacts={"entries": entries,
                                                       "root": root})

        def search_text(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            matches = _search_text(
                sb, args.get("root", "."), args["query"],
                glob=args.get("glob"), max_results=args.get("max_results", 100))
            return ObservationEnvelope.make("", success=True,
                stdout="\n".join(m["snippet"] for m in matches),
                artifacts={"matches": matches})

        def git_status(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            repo = args.get("repo_path", ".")
            try:
                sb.list_dir(repo)
            except OSError as e:
                return _obs_error("path_error", str(e))
            res = sb.run_shell(["git", "-C", repo, "status", "--short"],
                               timeout=5)
            clean = res.success and not res.stdout.strip()
            return ObservationEnvelope.make("", success=res.success,
                stdout=res.stdout, stderr=res.stderr, exit_code=res.exit_code,
                artifacts={"status_text": res.stdout, "clean": clean,
                           "timed_out": res.timed_out,
                           "error_kind": res.error_kind})

        def git_diff(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            repo = args.get("repo_path", ".")
            try:
                sb.list_dir(repo)
            except OSError as e:
                return _obs_error("path_error", str(e))
            cmd = ["git", "-C", repo, "diff"]
            if args.get("staged"):
                cmd.append("--staged")
            res = sb.run_shell(cmd, timeout=10)
            truncated = bool(res.truncated)
            return ObservationEnvelope.make("", success=res.success,
                stdout=res.stdout, stderr=res.stderr, exit_code=res.exit_code,
                artifacts={"diff_text": res.stdout, "truncated": truncated,
                           "timed_out": res.timed_out,
                           "error_kind": res.error_kind})

        def run_tests(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            from .file_patch import resolve_run_tests_command

            command = resolve_run_tests_command(args)
            timeout = args.get("timeout_seconds", args.get("timeout", 15))
            t0 = time.perf_counter()
            res = sb.run_shell(command, timeout=timeout)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            ok = res.success
            return ObservationEnvelope.make("", success=ok,
                stdout=res.stdout, stderr=res.stderr, exit_code=res.exit_code,
                artifacts={
                    "exit_code": res.exit_code,
                    "duration_ms": duration_ms,
                    "fs_diff": res.fs_diff,
                    "timed_out": res.timed_out,
                    "truncated": res.truncated,
                    "sandbox_mode": res.sandbox_mode,
                    "error_kind": res.error_kind,
                })

        def run_python(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            timeout = args.get("timeout_seconds", 10)
            t0 = time.perf_counter()
            res = sb.run_shell(["python3", *args["args"]], timeout=timeout)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            return ObservationEnvelope.make("", success=res.success,
                stdout=res.stdout, stderr=res.stderr, exit_code=res.exit_code,
                artifacts={"exit_code": res.exit_code, "duration_ms": duration_ms,
                           "fs_diff": res.fs_diff, "timed_out": res.timed_out,
                           "truncated": res.truncated,
                           "sandbox_mode": res.sandbox_mode,
                           "error_kind": res.error_kind})

        def run_shell(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            command = args.get("command", args.get("cmd"))
            if isinstance(command, str):
                command = ["sh", "-c", command]
            if not isinstance(command, list):
                return _obs_error("missing_command", "run_shell requires command or cmd")
            timeout = args.get("timeout_seconds", args.get("timeout", 10))
            t0 = time.perf_counter()
            res = sb.run_shell(command, timeout=timeout)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            return ObservationEnvelope.make("", success=res.success,
                stdout=res.stdout, stderr=res.stderr, exit_code=res.exit_code,
                artifacts={
                    "exit_code": res.exit_code,
                    "duration_ms": duration_ms,
                    "fs_diff": res.fs_diff,
                    "timed_out": res.timed_out,
                    "truncated": res.truncated,
                    "sandbox_mode": res.sandbox_mode,
                    "error_kind": res.error_kind,
                })

        def delete_file(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            path = args["path"]
            existed = True
            try:
                sb.read_file(path)
            except OSError:
                existed = False
            if not existed:
                return _obs_error("path_missing", f"cannot delete missing file: {path}")
            sb.delete_file(path)
            return ObservationEnvelope.make("", success=True,
                artifacts={"path": path, "deleted": True})

        def network_fetch(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            import urllib.error

            from .core_types import sha

            url = args["url"]
            timeout = args.get("timeout_seconds", args.get("timeout", 10))
            max_bytes = int(args.get("max_bytes", 65536))
            t0 = time.perf_counter()
            try:
                status, data, truncated = fetch_url_bytes(
                    url,
                    headers={"User-Agent": "agentic-runtime/0.2"},
                    timeout=timeout,
                    max_bytes=max_bytes,
                )
                body = data.decode("utf-8", errors="replace")
                duration_ms = int((time.perf_counter() - t0) * 1000)
                return ObservationEnvelope.make("", success=True,
                    stdout=body,
                    artifacts={
                        "url": url,
                        "status": status,
                        "bytes": len(data),
                        "truncated": truncated,
                        "content_hash": sha(body),
                        "duration_ms": duration_ms,
                    })
            except (urllib.error.URLError, TimeoutError, ValueError) as e:
                return _obs_error("network_error", str(e))

        def patch_file(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            diff = args.get("patch") or args.get("unified_diff")
            if not diff:
                return _obs_error("missing_patch", "patch_file requires patch or unified_diff")
            try:
                original = sb.read_file(args["path"])
                from .file_patch import apply_simple_unified_diff

                updated, summary = apply_simple_unified_diff(original, diff)
            except ValueError as e:
                return ObservationEnvelope.make("", success=False,
                    stderr=str(e), artifacts={"path": args["path"],
                                             "applied": False,
                                             "summary": str(e)})
            sb.write_file(args["path"], updated)
            return ObservationEnvelope.make("", success=True,
                artifacts={"path": args["path"], "applied": True,
                           "summary": summary})

        def mutate_protected(sb: SandboxBackend, args: dict) -> ObservationEnvelope:
            sb.write_file(args["path"], args["content"])
            return ObservationEnvelope.make("", success=True,
                artifacts={"path": args["path"], "protected_mutation": True})

        self.register(ToolSpec("read_file", "Read a file in the workspace",
            {"path": "str", "max_bytes": "int?"}, read_file,
            risk_level=ToolRiskLevel.TRIVIAL,
            required_capabilities=["filesystem_read"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_READ,
            verifier_requirement=ToolVerifierRequirement.NONE))
        self.register(ToolSpec("write_file", "Write/overwrite a file",
            {"path": "str", "content": "str", "create_dirs": "bool?"},
            write_file,
            risk_level=ToolRiskLevel.MEDIUM,
            required_capabilities=["filesystem_write"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_WRITE,
            verifier_requirement=ToolVerifierRequirement.STATE_VERIFIER))
        self.register(ToolSpec("edit_file", "Find/replace a single occurrence",
            {"path": "str", "find": "str", "replace": "str"}, edit_file,
            risk_level=ToolRiskLevel.MEDIUM,
            required_capabilities=["filesystem_write"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_WRITE,
            verifier_requirement=ToolVerifierRequirement.STATE_VERIFIER))
        self.register(ToolSpec("list_dir", "List a directory",
            {"path": "str?", "recursive": "bool?"}, list_dir,
            risk_level=ToolRiskLevel.TRIVIAL,
            required_capabilities=["filesystem_read"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_READ))
        self.register(ToolSpec("search_text", "Search text under a workspace root",
            {"root": "str", "query": "str", "glob": "str?",
             "max_results": "int?"}, search_text,
            risk_level=ToolRiskLevel.TRIVIAL,
            required_capabilities=["filesystem_read"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_READ))
        self.register(ToolSpec("git_status", "Read git status",
            {"repo_path": "str?"}, git_status,
            risk_level=ToolRiskLevel.TRIVIAL,
            required_capabilities=["filesystem_read"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_READ))
        self.register(ToolSpec("git_diff", "Read git diff",
            {"repo_path": "str?", "staged": "bool?"}, git_diff,
            risk_level=ToolRiskLevel.TRIVIAL,
            required_capabilities=["filesystem_read"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_READ))
        self.register(ToolSpec("run_tests", "Run a python test file",
            {"test_file": "str?", "command": "list[str]?",
             "timeout": "float?", "timeout_seconds": "int?"}, run_tests,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["shell_execution"],
            side_effect_type=ToolSideEffectType.SHELL_EXECUTION,
            sandbox_requirement=ToolSandboxRequirement.HARD_ISOLATION_RECOMMENDED,
            verifier_requirement=ToolVerifierRequirement.STATE_VERIFIER))
        self.register(ToolSpec("run_python", "Run python inside the sandbox",
            {"args": "list[str]", "timeout_seconds": "int?"}, run_python,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["shell_execution"],
            side_effect_type=ToolSideEffectType.SHELL_EXECUTION,
            sandbox_requirement=ToolSandboxRequirement.HARD_ISOLATION_RECOMMENDED,
            verifier_requirement=ToolVerifierRequirement.EXIT_STATUS))
        self.register(ToolSpec("run_shell", "Run an arbitrary command (HIGH risk)",
            {"cmd": "list[str]?", "command": "str?", "timeout": "float?",
             "timeout_seconds": "int?"}, run_shell,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["shell_execution"],
            side_effect_type=ToolSideEffectType.SHELL_EXECUTION,
            sandbox_requirement=ToolSandboxRequirement.HARD_ISOLATION_RECOMMENDED,
            verifier_requirement=ToolVerifierRequirement.EXIT_STATUS))
        self.register(ToolSpec("patch_file", "Apply a small unified diff to a file",
            {"path": "str", "patch": "str?", "unified_diff": "str?"},
            patch_file,
            risk_level=ToolRiskLevel.MEDIUM,
            required_capabilities=["filesystem_write"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_WRITE,
            verifier_requirement=ToolVerifierRequirement.EXIT_STATUS))
        self.register(ToolSpec("delete_file", "Delete a file in the workspace",
            {"path": "str"}, delete_file,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["filesystem_write"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_WRITE,
            verifier_requirement=ToolVerifierRequirement.STATE_VERIFIER))
        self.register(ToolSpec("network_fetch", "Fetch a URL over HTTP(S)",
            {"url": "str", "timeout": "number?", "timeout_seconds": "int?",
             "max_bytes": "int?"},
            network_fetch,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["network_access"],
            side_effect_type=ToolSideEffectType.NONE,
            sandbox_requirement=ToolSandboxRequirement.HARD_ISOLATION_RECOMMENDED,
            verifier_requirement=ToolVerifierRequirement.STATE_VERIFIER))
        self.register(ToolSpec(
            "mutate_protected_verification",
            "Approved mutation of a protected verification file (HIGH risk)",
            {"path": "str", "content": "str", "approved": "bool"},
            mutate_protected,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["filesystem_write"],
            side_effect_type=ToolSideEffectType.FILESYSTEM_WRITE,
            verifier_requirement=ToolVerifierRequirement.STATE_VERIFIER))


def _tool_error(code: str, message: str,
                details: Optional[dict[str, Any]] = None) -> ToolExecutionResult:
    return ToolExecutionResult(
        success=False,
        stderr=f"{code}: {message}",
        artifacts={"error_code": code, "error_reason": message},
        error=ToolError(code, message, details or {}),
    )


def _contract_error(check: ContractValidationResult) -> ToolExecutionResult:
    return _tool_error(
        check.code,
        check.message,
        {"arg": check.arg, **check.details},
    )


def _obs_error(code: str, message: str) -> ObservationEnvelope:
    return ObservationEnvelope.make(
        "", success=False, stderr=f"{code}: {message}",
        artifacts={"error_code": code, "error_reason": message})


def _list_dir(sb: SandboxBackend, root: str, *, recursive: bool) -> list[str]:
    if not recursive:
        return sb.list_dir(root)
    # Validate root through the sandbox first, then walk the resolved workspace path.
    sb.list_dir(root)
    base = os.path.normpath(os.path.join(sb.root, root))
    entries: list[str] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for name in sorted([*dirnames, *filenames]):
            path = os.path.relpath(os.path.join(dirpath, name), base)
            entries.append(path)
    return entries


def _search_text(
    sb: SandboxBackend,
    root: str,
    query: str,
    *,
    glob: Optional[str],
    max_results: int,
) -> list[dict[str, Any]]:
    sb.list_dir(root)
    base = os.path.normpath(os.path.join(sb.root, root))
    matches: list[dict[str, Any]] = []
    max_results = max(1, min(int(max_results or 100), 1000))
    for dirpath, _, filenames in os.walk(base):
        for filename in sorted(filenames):
            rel_to_root = os.path.relpath(os.path.join(dirpath, filename), base)
            rel = rel_to_root if root in ("", ".") else f"{root.rstrip('/')}/{rel_to_root}"
            if glob and not fnmatch.fnmatch(rel, glob):
                continue
            try:
                text = sb.read_file(rel)
            except (OSError, UnicodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if query in line:
                    matches.append({
                        "file": rel,
                        "path": rel,
                        "line": lineno,
                        "snippet": line[:240],
                    })
                    if len(matches) >= max_results:
                        return matches
    return matches
