"""
verifier.py — The State Verifier (Hrvoje §6.5, the anti-reward-hacking core).

Evaluation must be STATE-BASED, not claim-based. Test integrity checks are
delegated to ``test_integrity.TestIntegrityVerifier``.
"""
from __future__ import annotations

from typing import Callable, Optional

from .core_types import CommandEnvelope, ObservationEnvelope, VerifierResult
from .file_patch import apply_simple_unified_diff, resolve_run_tests_command
from .sandbox import SandboxBackend
from .test_integrity import (
    FileIntegritySnapshot,
    TestIntegrityVerifier,
    _WRITE_TOOLS_AFFECTING_INTEGRITY,
)

VerifierFn = Callable[
    [SandboxBackend, CommandEnvelope, ObservationEnvelope, Optional[str]],
    VerifierResult,
]


class StateVerifier:
    def __init__(self, sandbox: SandboxBackend,
                 test_integrity: Optional[TestIntegrityVerifier] = None) -> None:
        self.sandbox = sandbox
        self.test_integrity = test_integrity or TestIntegrityVerifier(sandbox)
        self._verifiers: dict[str, VerifierFn] = {}
        self._register_builtins()

    def register(self, tool: str, fn: VerifierFn) -> None:
        self._verifiers[tool] = fn

    def should_check_integrity(self, cmd: CommandEnvelope) -> bool:
        return cmd.tool in _WRITE_TOOLS_AFFECTING_INTEGRITY

    def capture_integrity(self) -> FileIntegritySnapshot:
        return self.test_integrity.capture()

    def verify(
        self,
        cmd: CommandEnvelope,
        obs: ObservationEnvelope,
        card=None,
        integrity_before: Optional[FileIntegritySnapshot] = None,
        write_snapshot_id: Optional[str] = None,
    ) -> VerifierResult:
        fn = self._verifiers.get(cmd.tool)
        if fn is None:
            result = VerifierResult(
                passed=obs.success, verifier="none",
                reason="no state verifier for tool; trusting exit status only",
                evidence={"caveat": "unverified"})
        else:
            try:
                result = fn(self.sandbox, cmd, obs, write_snapshot_id)
            except Exception as e:
                return VerifierResult(False, f"{cmd.tool}_verifier",
                                      reason=f"verifier error: {e}")

        if not result.passed:
            return result

        if self.should_check_integrity(cmd):
            ti = self.test_integrity.verify(cmd, obs, card, before=integrity_before)
            if not ti.passed:
                return ti

        return result

    def _register_builtins(self) -> None:
        def verify_edit(sb: SandboxBackend, cmd, obs, snap_id=None) -> VerifierResult:
            path = cmd.args["path"]
            old, new = cmd.args["find"], cmd.args["replace"]
            try:
                actual = sb.read_file(path)
            except OSError as e:
                return VerifierResult(False, "edit_file_verifier",
                                      reason=f"cannot read {path}: {e}")
            if not snap_id:
                return VerifierResult(
                    False, "edit_file_verifier",
                    reason="edit_file verifier missing pre-write snapshot")
            try:
                original = sb.read_snapshot_file(snap_id, path)
            except (KeyError, OSError) as e:
                return VerifierResult(False, "edit_file_verifier",
                                      reason=f"cannot read pre-edit state for {path}: {e}")
            if old not in original:
                ok = False
                reason = "find string was not present in pre-edit file state"
            elif original.count(old) > 1:
                ok = False
                reason = "find string appeared multiple times; single replacement is ambiguous"
            else:
                expected = original.replace(old, new, 1)
                ok = actual == expected
                reason = (
                    "edit matches single find/replace on pre-edit state"
                    if ok else "edit diverges from expected find/replace result"
                )
            return VerifierResult(
                passed=ok, verifier="edit_file_verifier",
                evidence={"path": path, "exact_match": ok},
                reason=reason)

        def verify_write(sb: SandboxBackend, cmd, obs, _snap_id=None) -> VerifierResult:
            path = cmd.args["path"]
            try:
                content = sb.read_file(path)
            except OSError as e:
                return VerifierResult(False, "write_file_verifier",
                                      reason=f"file absent after write: {e}")
            ok = content == cmd.args["content"]
            return VerifierResult(ok, "write_file_verifier",
                evidence={"path": path, "exact_match": ok},
                reason="file content matches written bytes" if ok
                       else "file content diverges from claim")

        def verify_patch(sb: SandboxBackend, cmd, obs, snap_id=None) -> VerifierResult:
            path = cmd.args["path"]
            diff = cmd.args.get("patch") or cmd.args.get("unified_diff")
            if not diff:
                return VerifierResult(False, "patch_file_verifier",
                                      reason="patch_file missing patch/unified_diff")
            if not obs.artifacts.get("applied"):
                return VerifierResult(
                    False, "patch_file_verifier",
                    evidence={"path": path, "applied": False,
                              "summary": obs.artifacts.get("summary", "")},
                    reason="patch_file did not report an applied patch")
            if not snap_id:
                return VerifierResult(
                    False, "patch_file_verifier",
                    reason="patch_file verifier missing pre-write snapshot")
            try:
                original = sb.read_snapshot_file(snap_id, path)
                expected, summary = apply_simple_unified_diff(original, diff)
                actual = sb.read_file(path)
            except (OSError, KeyError, ValueError) as e:
                return VerifierResult(False, "patch_file_verifier",
                                      reason=f"cannot verify patched file {path}: {e}")
            ok = actual == expected
            return VerifierResult(
                ok, "patch_file_verifier",
                evidence={"path": path, "exact_match": ok, "summary": summary},
                reason="patched file matches independently recomputed state" if ok
                       else "patched file diverges from expected post-patch state")

        def verify_mutate_protected(sb: SandboxBackend, cmd, obs, _snap_id=None) -> VerifierResult:
            path = cmd.args["path"]
            try:
                content = sb.read_file(path)
            except OSError as e:
                return VerifierResult(False, "mutate_protected_verifier",
                                      reason=f"cannot read {path}: {e}")
            ok = content == cmd.args["content"]
            return VerifierResult(ok, "mutate_protected_verifier",
                evidence={"path": path, "exact_match": ok},
                reason="protected file updated via approved pathway" if ok
                       else "protected file content diverges from claim")

        def verify_delete(sb: SandboxBackend, cmd, obs, _snap_id=None) -> VerifierResult:
            path = cmd.args["path"]
            try:
                sb.read_file(path)
            except OSError:
                return VerifierResult(
                    True, "delete_file_verifier",
                    evidence={"path": path, "absent": True},
                    reason="file absent in real file state after delete")
            return VerifierResult(
                False, "delete_file_verifier",
                evidence={"path": path, "absent": False},
                reason="file still present after claimed delete")

        def verify_network_fetch(sb: SandboxBackend, cmd, obs, _snap_id=None) -> VerifierResult:
            import urllib.error
            import urllib.request

            from .core_types import sha

            url = cmd.args["url"]
            timeout = cmd.args.get("timeout_seconds", cmd.args.get("timeout", 10))
            max_bytes = int(cmd.args.get("max_bytes", 65536))
            req = urllib.request.Request(
                url, headers={"User-Agent": "agentic-runtime/0.2"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read(max_bytes + 1)
                    if len(data) > max_bytes:
                        data = data[:max_bytes]
                    body = data.decode("utf-8", errors="replace")
            except (urllib.error.URLError, TimeoutError, ValueError) as e:
                return VerifierResult(
                    False, "network_fetch_verifier",
                    reason=f"independent fetch failed: {e}")
            ok = sha(body) == sha(obs.stdout)
            return VerifierResult(
                ok, "network_fetch_verifier",
                evidence={"url": url, "content_hash_match": ok,
                          "reexec_status": resp.status},
                reason="independent fetch content matches observation" if ok
                       else "fetched content diverges from tool observation")

        def verify_tests(sb: SandboxBackend, cmd, obs, _snap_id=None) -> VerifierResult:
            command = resolve_run_tests_command(cmd.args)
            timeout = cmd.args.get("timeout_seconds", cmd.args.get("timeout", 15))
            res = sb.run_shell(command, timeout=timeout)
            ok = res.success
            combined = dict(obs.artifacts.get("fs_diff", {}))
            combined.update(res.fs_diff)
            unexpected = _unexpected_fs_changes(combined, cmd)
            if unexpected:
                return VerifierResult(
                    False, "run_tests_verifier",
                    evidence={"unexpected_fs_changes": unexpected,
                              "reexec_exit": res.exit_code,
                              "reexec_command": command},
                    reason=f"run_tests modified unexpected files: {unexpected}")
            return VerifierResult(ok, "run_tests_verifier",
                evidence={"reexec_exit": res.exit_code,
                          "agent_claimed_exit": obs.exit_code,
                          "reexec_command": command},
                reason="independent test re-run passed" if ok
                       else "independent test re-run failed")

        self.register("edit_file", verify_edit)
        self.register("write_file", verify_write)
        self.register("patch_file", verify_patch)
        self.register("delete_file", verify_delete)
        self.register("network_fetch", verify_network_fetch)
        self.register("mutate_protected_verification", verify_mutate_protected)
        self.register("run_tests", verify_tests)


def _unexpected_fs_changes(fs_diff: dict[str, str], cmd: CommandEnvelope) -> list[str]:
    allowed = {cmd.args.get("test_file", "test.py")}
    app_paths = cmd.args.get("allowed_app_paths", [])
    unexpected: list[str] = []
    for path, kind in fs_diff.items():
        norm = path.replace("\\", "/")
        if norm in allowed:
            continue
        if norm.startswith("__pycache__/") or norm.endswith(".pyc"):
            continue
        if any(norm == p or norm.startswith(p.rstrip("/") + "/") for p in app_paths):
            continue
        if kind in ("added", "modified", "deleted"):
            unexpected.append(norm)
    return unexpected
