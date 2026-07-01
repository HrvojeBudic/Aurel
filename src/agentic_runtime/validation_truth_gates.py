"""P1.ENF-F-A validation truth and determinism drift gates."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class DeterminismGateStatus(str, Enum):
    PASS = "pass"
    FAIL_DIRTY_WORKTREE = "fail_dirty_worktree"
    FAIL_FIXTURE_MUTATION = "fail_fixture_mutation"
    BLOCKED_UNRELATED_DIRTY_FILES = "blocked_unrelated_dirty_files"
    WARN_GATE_INPUT_UNAVAILABLE = "warn_gate_input_unavailable"
    UNAVAILABLE = "unavailable"


class ToolingTruthGateStatus(str, Enum):
    PASS = "pass"
    FAIL_CORE_STRICT_PROBE_MISSING = "fail_core_strict_probe_missing"
    FAIL_CORE_STRICT_PROBE_FAILED = "fail_core_strict_probe_failed"
    WARN_BASELINE_ONLY = "warn_baseline_only"
    BLOCKED_TOOLING_OVERCLAIM = "blocked_tooling_overclaim"
    UNAVAILABLE = "unavailable"


class ValidationClaimStrength(str, Enum):
    BASELINE_ONLY = "baseline_only"
    CORE_STRICT_PROBE = "core_strict_probe"
    FULL_SUITE = "full_suite"
    COVERAGE = "coverage"
    UNAVAILABLE = "unavailable"


CORE_STRICT_PROBE_ERROR_CODES: frozenset[str] = frozenset(
    {"arg-type", "call-arg", "union-attr"}
)


@dataclass(frozen=True)
class TrackedFixtureMutationFinding:
    fixture_path: str
    expected_hash: str
    actual_hash: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "actual_hash": self.actual_hash,
            "expected_hash": self.expected_hash,
            "fixture_path": self.fixture_path,
        }


@dataclass(frozen=True)
class ValidationSideEffectFinding:
    affected_path: str
    reason_code: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "affected_path": self.affected_path,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class DeterminismGateInput:
    """Structured input for fixture/worktree determinism checks."""

    tracked_fixture_hashes: Mapping[str, str] = field(default_factory=dict)
    observed_fixture_hashes: Mapping[str, str] = field(default_factory=dict)
    dirty_tracked_paths: tuple[str, ...] = ()
    unrelated_dirty_paths: tuple[str, ...] = ()
    consent_determinism_tests_present: bool = False
    gate_input_available: bool = True


@dataclass(frozen=True)
class DeterminismGateResult:
    status: DeterminismGateStatus
    truth_label: str = "VALIDATION_TRUTH_GATE"
    fixture_mutations: tuple[TrackedFixtureMutationFinding, ...] = ()
    side_effects: tuple[ValidationSideEffectFinding, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "fixture_mutations": [
                item.to_canonical_dict() for item in self.fixture_mutations
            ],
            "reason_codes": sorted(self.reason_codes),
            "side_effects": [item.to_canonical_dict() for item in self.side_effects],
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class DirtyWorktreeGateInput:
    dirty_paths: tuple[str, ...] = ()
    unrelated_dirty_paths: tuple[str, ...] = ()
    tracked_fixture_paths: tuple[str, ...] = ()
    tracked_fixture_hashes_before: Mapping[str, str] = field(default_factory=dict)
    tracked_fixture_hashes_after: Mapping[str, str] = field(default_factory=dict)
    gate_input_available: bool = True


@dataclass(frozen=True)
class DirtyWorktreeGateResult:
    status: DeterminismGateStatus
    determinism: DeterminismGateResult
    truth_label: str = "VALIDATION_TRUTH_GATE"

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "determinism": self.determinism.to_canonical_dict(),
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class ValidationOverclaimFinding:
    claim: str
    cited_strength: ValidationClaimStrength
    required_strength: ValidationClaimStrength
    reason_code: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "cited_strength": self.cited_strength.value,
            "claim": self.claim,
            "reason_code": self.reason_code,
            "required_strength": self.required_strength.value,
        }


@dataclass(frozen=True)
class ToolingTruthGateInput:
    baseline_mypy_documented: bool = False
    core_strict_probe_documented: bool = False
    ruff_documented: bool = False
    cited_strength: ValidationClaimStrength = ValidationClaimStrength.BASELINE_ONLY
    core_strict_probe_present: bool = False
    core_strict_probe_passed: bool = False
    core_strict_probe_error_codes: tuple[str, ...] = ()
    claim_core_strict_as_full_type_safety: bool = False


@dataclass(frozen=True)
class ToolingTruthGateResult:
    status: ToolingTruthGateStatus
    truth_label: str = "VALIDATION_TRUTH_GATE"
    overclaims: tuple[ValidationOverclaimFinding, ...] = ()
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "overclaims": [item.to_canonical_dict() for item in self.overclaims],
            "reason_codes": sorted(self.reason_codes),
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class CoreStrictProbeGateInput:
    probe_command_present: bool = False
    probe_passed: bool = False
    enabled_error_codes: tuple[str, ...] = ()
    probe_targets_core_files: bool = False


@dataclass(frozen=True)
class CoreStrictProbeGateResult:
    status: ToolingTruthGateStatus
    missing_error_codes: tuple[str, ...] = ()
    truth_label: str = "VALIDATION_TRUTH_GATE"
    reason_codes: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "missing_error_codes": sorted(self.missing_error_codes),
            "reason_codes": sorted(self.reason_codes),
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


class DeterminismGate:
    def evaluate(self, gate_input: DeterminismGateInput) -> DeterminismGateResult:
        return evaluate_determinism_gate(gate_input)


class DirtyWorktreeGate:
    def evaluate(self, gate_input: DirtyWorktreeGateInput) -> DirtyWorktreeGateResult:
        return evaluate_dirty_worktree_gate(gate_input)


class ToolingTruthGate:
    def evaluate(self, gate_input: ToolingTruthGateInput) -> ToolingTruthGateResult:
        return evaluate_tooling_truth_gate(gate_input)


class CoreStrictProbeGate:
    def evaluate(
        self, gate_input: CoreStrictProbeGateInput
    ) -> CoreStrictProbeGateResult:
        return evaluate_core_strict_probe_gate(gate_input)


def evaluate_determinism_gate(gate_input: DeterminismGateInput) -> DeterminismGateResult:
    if not gate_input.gate_input_available:
        return DeterminismGateResult(
            status=DeterminismGateStatus.WARN_GATE_INPUT_UNAVAILABLE,
            reason_codes=("GATE_INPUT_UNAVAILABLE",),
        )

    if gate_input.unrelated_dirty_paths:
        return DeterminismGateResult(
            status=DeterminismGateStatus.BLOCKED_UNRELATED_DIRTY_FILES,
            reason_codes=("UNRELATED_DIRTY_FILES_BLOCK_DONE",),
        )

    mutations: list[TrackedFixtureMutationFinding] = []
    for path, expected in gate_input.tracked_fixture_hashes.items():
        observed = gate_input.observed_fixture_hashes.get(path)
        if observed is None:
            continue
        if observed != expected:
            mutations.append(
                TrackedFixtureMutationFinding(
                    fixture_path=path,
                    expected_hash=expected,
                    actual_hash=observed,
                )
            )

    if mutations:
        return DeterminismGateResult(
            status=DeterminismGateStatus.FAIL_FIXTURE_MUTATION,
            fixture_mutations=tuple(mutations),
            reason_codes=("TRACKED_FIXTURE_HASH_DRIFT",),
        )

    if gate_input.dirty_tracked_paths:
        side_effects = tuple(
            ValidationSideEffectFinding(
                affected_path=path,
                reason_code="TRACKED_PATH_DIRTY",
            )
            for path in gate_input.dirty_tracked_paths
        )
        return DeterminismGateResult(
            status=DeterminismGateStatus.FAIL_DIRTY_WORKTREE,
            side_effects=side_effects,
            reason_codes=("DIRTY_TRACKED_PATHS",),
        )

    return DeterminismGateResult(
        status=DeterminismGateStatus.PASS,
        reason_codes=("TRACKED_FIXTURE_HASHES_STABLE",),
    )


def evaluate_dirty_worktree_gate(
    gate_input: DirtyWorktreeGateInput,
) -> DirtyWorktreeGateResult:
    determinism_input = DeterminismGateInput(
        tracked_fixture_hashes=gate_input.tracked_fixture_hashes_before,
        observed_fixture_hashes=gate_input.tracked_fixture_hashes_after,
        dirty_tracked_paths=tuple(
            path
            for path in gate_input.dirty_paths
            if path in gate_input.tracked_fixture_paths
        ),
        unrelated_dirty_paths=gate_input.unrelated_dirty_paths,
        gate_input_available=gate_input.gate_input_available,
    )
    determinism = evaluate_determinism_gate(determinism_input)
    return DirtyWorktreeGateResult(status=determinism.status, determinism=determinism)


def evaluate_core_strict_probe_gate(
    gate_input: CoreStrictProbeGateInput,
) -> CoreStrictProbeGateResult:
    if not gate_input.probe_command_present:
        return CoreStrictProbeGateResult(
            status=ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_MISSING,
            reason_codes=("CORE_STRICT_PROBE_COMMAND_MISSING",),
        )

    enabled = set(gate_input.enabled_error_codes)
    missing = tuple(
        sorted(code for code in CORE_STRICT_PROBE_ERROR_CODES if code not in enabled)
    )
    if missing:
        return CoreStrictProbeGateResult(
            status=ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_MISSING,
            missing_error_codes=missing,
            reason_codes=("CORE_STRICT_PROBE_MISSING_REQUIRED_ERROR_CODES",),
        )

    if not gate_input.probe_targets_core_files:
        return CoreStrictProbeGateResult(
            status=ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_MISSING,
            reason_codes=("CORE_STRICT_PROBE_TARGETS_NOT_CORE_FILES",),
        )

    if not gate_input.probe_passed:
        return CoreStrictProbeGateResult(
            status=ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_FAILED,
            reason_codes=("CORE_STRICT_PROBE_FAILED",),
        )

    return CoreStrictProbeGateResult(
        status=ToolingTruthGateStatus.PASS,
        reason_codes=("CORE_STRICT_PROBE_PASSED",),
    )


def evaluate_tooling_truth_gate(
    gate_input: ToolingTruthGateInput,
) -> ToolingTruthGateResult:
    probe_result = evaluate_core_strict_probe_gate(
        CoreStrictProbeGateInput(
            probe_command_present=gate_input.core_strict_probe_present,
            probe_passed=gate_input.core_strict_probe_passed,
            enabled_error_codes=gate_input.core_strict_probe_error_codes,
            probe_targets_core_files=gate_input.core_strict_probe_present,
        )
    )

    overclaims: list[ValidationOverclaimFinding] = []
    if gate_input.claim_core_strict_as_full_type_safety:
        overclaims.append(
            ValidationOverclaimFinding(
                claim="full_type_safety",
                cited_strength=gate_input.cited_strength,
                required_strength=ValidationClaimStrength.UNAVAILABLE,
                reason_code="FULL_TYPE_SAFETY_NOT_CLAIMABLE",
            )
        )

    if (
        gate_input.cited_strength is ValidationClaimStrength.CORE_STRICT_PROBE
        and probe_result.status
        is not ToolingTruthGateStatus.PASS
    ):
        overclaims.append(
            ValidationOverclaimFinding(
                claim="core_strict_probe",
                cited_strength=gate_input.cited_strength,
                required_strength=ValidationClaimStrength.CORE_STRICT_PROBE,
                reason_code="CORE_STRICT_PROBE_EVIDENCE_MISSING_OR_FAILED",
            )
        )

    if overclaims:
        return ToolingTruthGateResult(
            status=ToolingTruthGateStatus.BLOCKED_TOOLING_OVERCLAIM,
            overclaims=tuple(overclaims),
            reason_codes=("TOOLING_OVERCLAIM",),
        )

    if probe_result.status is ToolingTruthGateStatus.PASS:
        return ToolingTruthGateResult(
            status=ToolingTruthGateStatus.PASS,
            reason_codes=("CORE_STRICT_PROBE_ACCEPTED",),
        )

    if (
        gate_input.cited_strength is ValidationClaimStrength.BASELINE_ONLY
        and gate_input.baseline_mypy_documented
    ):
        return ToolingTruthGateResult(
            status=ToolingTruthGateStatus.WARN_BASELINE_ONLY,
            reason_codes=("BASELINE_MYPY_ONLY_WEAK_EVIDENCE",),
        )

    if probe_result.status is ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_FAILED:
        return ToolingTruthGateResult(
            status=ToolingTruthGateStatus.FAIL_CORE_STRICT_PROBE_FAILED,
            reason_codes=probe_result.reason_codes,
        )

    return ToolingTruthGateResult(
        status=probe_result.status,
        reason_codes=probe_result.reason_codes,
    )
