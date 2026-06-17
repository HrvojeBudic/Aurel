"""
test_integrity.py — Protected verification file integrity (P0.4).

Detects reward hacking where agents weaken tests, golden fixtures, or eval
harnesses to make broken code appear correct.
"""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from typing import Optional

from .canonical_path import CanonicalPathResolver
from .core_types import AgentCard, CommandEnvelope, ObservationEnvelope, VerifierResult, sha
from .sandbox import SandboxBackend

# Verifier result codes
INTEGRITY_OK = ""
PROTECTED_FILE_MUTATION = "PROTECTED_FILE_MUTATION"
PROTECTED_MUTATION_UNAUTHORIZED = "PROTECTED_MUTATION_UNAUTHORIZED"

# Dedicated high-risk tool for approved protected-file mutation
MUTATE_PROTECTED_TOOL = "mutate_protected_verification"

_WRITE_TOOLS_AFFECTING_INTEGRITY = frozenset({
    "edit_file", "write_file", "patch_file", "delete_file",
    "run_tests", "run_python", "run_shell",
    MUTATE_PROTECTED_TOOL,
})


@dataclass(frozen=True)
class ProtectedPathPolicy:
    """Glob patterns for verification assets that must not change silently."""

    patterns: tuple[str, ...] = (
        "tests/**",
        "**/test_*.py",
        "**/*_test.py",
        "fixtures/golden/**",
        "verifiers/**",
        "evals/**",
    )

    def is_protected(self, relpath: str) -> bool:
        norm = relpath.replace("\\", "/").lstrip("./")
        return any(_match_pattern(norm, pat) for pat in self.patterns)

    def classify_path(self, relpath: str) -> str:
        return "protected" if self.is_protected(relpath) else "source"


def _match_pattern(path: str, pattern: str) -> bool:
    pat = pattern.replace("\\", "/")
    if pat.endswith("/**"):
        root = pat[:-3]
        return path == root or path.startswith(root + "/")
    if pat.startswith("**/"):
        suffix = pat[3:]
        parts = path.split("/")
        for i in range(len(parts)):
            segment = "/".join(parts[i:])
            if fnmatch.fnmatch(segment, suffix):
                return True
            if fnmatch.fnmatch(parts[i], suffix):
                return True
        return fnmatch.fnmatch(path, suffix)
    return fnmatch.fnmatch(path, pat)


@dataclass
class FileIntegritySnapshot:
    """Content hashes of all protected files visible in the workspace."""

    file_hashes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def capture(cls, sandbox: SandboxBackend,
                policy: ProtectedPathPolicy) -> FileIntegritySnapshot:
        hashes: dict[str, str] = {}
        for rel in _iter_workspace_files(sandbox.root):
            if policy.is_protected(rel):
                hashes[rel] = _hash_file(sandbox, rel)
        return cls(file_hashes=hashes)

    def diff(self, other: FileIntegritySnapshot) -> dict[str, list[str]]:
        before, after = self.file_hashes, other.file_hashes
        added = sorted(set(after) - set(before))
        deleted = sorted(set(before) - set(after))
        changed = sorted(
            p for p in set(before) & set(after) if before[p] != after[p])
        return {"added_files": added, "deleted_files": deleted, "changed_files": changed}

    @property
    def paths(self) -> set[str]:
        return set(self.file_hashes)


def _iter_workspace_files(root: str) -> list[str]:
    paths: list[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            paths.append(rel.replace("\\", "/"))
    return sorted(paths)


def _hash_file(sandbox: SandboxBackend, rel: str) -> str:
    try:
        return sha(sandbox.read_file(rel))
    except OSError:
        return "<missing>"


def command_targets_protected(cmd: CommandEnvelope,
                              policy: ProtectedPathPolicy,
                              resolver: CanonicalPathResolver) -> bool:
    """True if this command directly targets a protected path."""
    path = cmd.args.get("path") or cmd.args.get("file")
    if not path:
        return False
    try:
        rel = resolver.resolve(path).relative
    except Exception:
        return False
    return policy.is_protected(rel)


def is_approved_protected_mutation(cmd: CommandEnvelope, card: AgentCard) -> bool:
    """Dedicated pathway: tool + card authority + explicit approval flag."""
    if cmd.tool != MUTATE_PROTECTED_TOOL:
        return False
    return bool(
        card.authority.allow_protected_mutation
        and cmd.args.get("approved") is True
    )


@dataclass
class IntegrityCheckResult:
    passed: bool
    code: str
    reason: str
    added_files: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)

    def to_verifier_result(self) -> VerifierResult:
        return VerifierResult(
            passed=self.passed,
            verifier="test_integrity_verifier",
            code=self.code,
            reason=self.reason,
            evidence={
                "added_files": self.added_files,
                "deleted_files": self.deleted_files,
                "changed_files": self.changed_files,
            },
        )


class TestIntegrityVerifier:
    """Compare before/after protected-file snapshots around command execution."""

    def __init__(self, sandbox: SandboxBackend,
                 policy: Optional[ProtectedPathPolicy] = None,
                 resolver: Optional[CanonicalPathResolver] = None) -> None:
        self.sandbox = sandbox
        self.policy = policy or ProtectedPathPolicy()
        self.resolver = resolver or CanonicalPathResolver(sandbox.root)
        self._baseline = FileIntegritySnapshot.capture(sandbox, self.policy)

    def capture(self) -> FileIntegritySnapshot:
        return FileIntegritySnapshot.capture(self.sandbox, self.policy)

    def snapshot(self) -> None:
        """Reset the rolling baseline (e.g. after seeding a repo)."""
        self._baseline = self.capture()

    def is_protected(self, relpath: str) -> bool:
        return self.policy.is_protected(relpath)

    def verify(
        self,
        cmd: CommandEnvelope,
        obs: ObservationEnvelope,
        card: Optional[AgentCard] = None,
        before: Optional[FileIntegritySnapshot] = None,
    ) -> VerifierResult:
        before_snap = before or self._baseline
        after_snap = self.capture()
        result = self._compare(before_snap, after_snap, cmd, card)
        if result.passed:
            self._baseline = after_snap
        return result.to_verifier_result()

    def _compare(
        self,
        before: FileIntegritySnapshot,
        after: FileIntegritySnapshot,
        cmd: CommandEnvelope,
        card: Optional[AgentCard],
    ) -> IntegrityCheckResult:
        delta = before.diff(after)
        added = delta["added_files"]
        deleted = delta["deleted_files"]
        changed = delta["changed_files"]

        if is_approved_protected_mutation(cmd, card or _null_card()):
            target = cmd.args.get("path", "")
            try:
                rel = self.resolver.resolve(target).relative
            except Exception:
                rel = target
            allowed = {rel} if rel else set()
            bad_added = [p for p in added if p not in allowed]
            bad_deleted = [p for p in deleted if p not in allowed]
            bad_changed = [p for p in changed if p not in allowed]
            if bad_added or bad_deleted or bad_changed:
                return IntegrityCheckResult(
                    False, PROTECTED_FILE_MUTATION,
                    "approved mutation touched files outside declared target",
                    bad_added, bad_deleted, bad_changed,
                )
            return IntegrityCheckResult(
                True, INTEGRITY_OK,
                "protected mutation via dedicated approved pathway",
            )

        if added or deleted or changed:
            return IntegrityCheckResult(
                False, PROTECTED_FILE_MUTATION,
                "protected verification file mutation detected",
                added, deleted, changed,
            )

        return IntegrityCheckResult(
            True, INTEGRITY_OK, "protected verification files unchanged",
        )


def _null_card() -> AgentCard:
    from .core_types import AgentClass, AuthorityScope
    return AgentCard.make("null", AgentClass.EXECUTION, "",
                          AuthorityScope())
