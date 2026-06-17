"""
verifier.py — The State Verifier (Hrvoje §6.5, the anti-reward-hacking core).

Evaluation must be STATE-BASED, not claim-based. Test integrity checks are
delegated to ``test_integrity.TestIntegrityVerifier``.
"""
from __future__ import annotations

from typing import Callable, Optional

from .core_types import CommandEnvelope, ObservationEnvelope, VerifierResult
from .sandbox import SandboxBackend
from .test_integrity import (
    FileIntegritySnapshot,
    TestIntegrityVerifier,
    _WRITE_TOOLS_AFFECTING_INTEGRITY,
)

VerifierFn = Callable[[SandboxBackend, CommandEnvelope, ObservationEnvelope], VerifierResult]


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
    ) -> VerifierResult:
        fn = self._verifiers.get(cmd.tool)
        if fn is None:
            result = VerifierResult(
                passed=obs.success, verifier="none",
                reason="no state verifier for tool; trusting exit status only",
                evidence={"caveat": "unverified"})
        else:
            try:
                result = fn(self.sandbox, cmd, obs)
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
        def verify_edit(sb: SandboxBackend, cmd, obs) -> VerifierResult:
            path = cmd.args["path"]
            try:
                content = sb.read_file(path)
            except OSError as e:
                return VerifierResult(False, "edit_file_verifier",
                                      reason=f"cannot read {path}: {e}")
            new = cmd.args["replace"]
            ok = new in content
            return VerifierResult(
                passed=ok, verifier="edit_file_verifier",
                evidence={"path": path, "replacement_present": ok},
                reason="replacement confirmed in real file state" if ok
                       else "claimed edit NOT present in real file")

        def verify_write(sb: SandboxBackend, cmd, obs) -> VerifierResult:
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

        def verify_patch(sb: SandboxBackend, cmd, obs) -> VerifierResult:
            path = cmd.args["path"]
            try:
                sb.read_file(path)
            except OSError as e:
                return VerifierResult(False, "patch_file_verifier",
                                      reason=f"cannot read patched file {path}: {e}")
            applied = bool(obs.artifacts.get("applied"))
            return VerifierResult(
                applied, "patch_file_verifier",
                evidence={"path": path, "applied": applied,
                          "summary": obs.artifacts.get("summary", "")},
                reason="patch_file reported applied patch" if applied
                       else "patch_file did not report an applied patch")

        def verify_mutate_protected(sb: SandboxBackend, cmd, obs) -> VerifierResult:
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

        def verify_tests(sb: SandboxBackend, cmd, obs) -> VerifierResult:
            res = sb.run_shell(["python3", cmd.args.get("test_file", "test.py")],
                               timeout=cmd.args.get("timeout", 15))
            ok = res.success
            combined = dict(obs.artifacts.get("fs_diff", {}))
            combined.update(res.fs_diff)
            unexpected = _unexpected_fs_changes(combined, cmd)
            if unexpected:
                return VerifierResult(
                    False, "run_tests_verifier",
                    evidence={"unexpected_fs_changes": unexpected,
                              "reexec_exit": res.exit_code},
                    reason=f"run_tests modified unexpected files: {unexpected}")
            return VerifierResult(ok, "run_tests_verifier",
                evidence={"reexec_exit": res.exit_code,
                          "agent_claimed_exit": obs.exit_code},
                reason="independent test re-run passed" if ok
                       else "independent test re-run failed")

        self.register("edit_file", verify_edit)
        self.register("write_file", verify_write)
        self.register("patch_file", verify_patch)
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
