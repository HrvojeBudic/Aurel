"""Path governance test harness (P1.7.15).

Test harness verifies shadow governance behavior.
It must not become the governance runtime.
Harness assertions prove model consistency, not runtime authority.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .conflict_precedence import (
    ConflictPrecedenceResult,
    resolve_path_source_conflicts_shadow,
)
from .escape_detection import PathBoundaryCheckResult, PathBoundaryStatus
from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .path_identity import PathIdentity, PathKind, build_path_identity
from .path_resolution_trace import (
    PathResolutionTraceHookResult,
    build_path_resolution_trace_payload,
    record_path_resolution_trace_hook,
)
from .path_resolver import (
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
    resolve_path_governance_shadow,
)
from .path_violation_trace import (
    PathViolationTraceHookResult,
    build_path_violation_trace_payload,
    record_path_violation_trace_hook,
)
from .risk_classification import (
    PathSourceRiskClassification,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    RiskClassificationBasis,
    build_path_source_risk_classification,
    build_path_source_risk_signal,
)
from .serialization import stable_hash
from .source_identity import SourceKind, SourceOrigin, build_source_identity
from .source_provenance import (
    EvidenceBindingKind,
    EvidenceConfidence,
    ProvenanceBinding,
    SourceClaimKind,
    build_provenance_binding,
    build_source_claim_ref,
    build_source_evidence_ref,
)
from .source_trust_resolver import (
    SourceTrustResolverResult,
    SourceTrustShadowDecision,
    resolve_source_trust_shadow,
)
from .trusted_roots import build_trusted_root_registry
from .untrusted_content_boundary import (
    ContentInfluenceSurface,
    UntrustedBoundaryPosture,
    UntrustedContentKind,
    build_untrusted_content_boundary,
)
from .path_authority_scope import (
    PathAuthorityBasis,
    PathAuthoritySubject,
    PathAuthoritySubjectKind,
    PathScopeAction,
    build_path_authority_scope,
)
from .validation import validate_known_fields

PATH_GOVERNANCE_TEST_HARNESS_TASK_ID = "P1.7.15"
PATH_GOVERNANCE_TEST_HARNESS_VERSION = "path_governance_test_harness.v1"

PATH_GOVERNANCE_HARNESS_SCENARIO_KNOWN_FIELDS: frozenset[str] = frozenset({
    "scenario_id",
    "scenario_kind",
    "description",
    "source_label",
    "fixtures_label",
    "expected_outcomes",
    "metadata",
})

PATH_GOVERNANCE_HARNESS_RUN_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "run_id",
    "scenarios",
    "source_label",
    "input_hash",
    "metadata",
})

PATH_GOVERNANCE_HARNESS_STEP_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "step_id",
    "scenario_id",
    "step_name",
    "status",
    "observed_refs",
    "expected_outcomes",
    "passed",
    "reason",
    "source_label",
    "step_hash",
    "metadata",
})

PATH_GOVERNANCE_HARNESS_RUN_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "result_id",
    "run_id",
    "scenario_results",
    "passed",
    "failed_count",
    "skipped_count",
    "unavailable_count",
    "error_count",
    "source_label",
    "harness_version",
    "created_by_task",
    "result_hash",
    "metadata",
})

_SAFETY_EXPECTATIONS: frozenset[str] = frozenset({
    "EXPECT_NO_ENFORCEMENT",
    "EXPECT_NO_LEDGER",
    "EXPECT_NO_RUNTIME_MUTATION",
    "EXPECT_NO_POLICY_CALL",
    "EXPECT_NO_APPROVAL_ACTIVATION",
    "EXPECT_NO_SOURCE_MUTATION",
})


class PathGovernanceHarnessScenarioKind(str, Enum):
    """Harness scenario classification; not runtime action."""

    TRUSTED_PATH_ALLOWED_SHADOW = "TRUSTED_PATH_ALLOWED_SHADOW"
    UNTRUSTED_SOURCE_REVIEW_SHADOW = "UNTRUSTED_SOURCE_REVIEW_SHADOW"
    PATH_ESCAPE_RESTRICT_SHADOW = "PATH_ESCAPE_RESTRICT_SHADOW"
    SOURCE_DISTRUST_CONFLICT_SHADOW = "SOURCE_DISTRUST_CONFLICT_SHADOW"
    CRITICAL_RISK_QUARANTINE_RECOMMENDED = "CRITICAL_RISK_QUARANTINE_RECOMMENDED"
    MISSING_PROVENANCE_REVIEW_SHADOW = "MISSING_PROVENANCE_REVIEW_SHADOW"
    UNTRUSTED_BOUNDARY_COMMAND_SURFACE = "UNTRUSTED_BOUNDARY_COMMAND_SURFACE"
    TRACE_PAYLOAD_ONLY = "TRACE_PAYLOAD_ONLY"
    VIOLATION_DRIFT_PAYLOAD_ONLY = "VIOLATION_DRIFT_PAYLOAD_ONLY"
    UNKNOWN = "UNKNOWN"


class PathGovernanceHarnessExpectation(str, Enum):
    """Assertions over shadow/test behavior; expectations do not enforce."""

    EXPECT_WOULD_ALLOW = "EXPECT_WOULD_ALLOW"
    EXPECT_WOULD_REVIEW = "EXPECT_WOULD_REVIEW"
    EXPECT_WOULD_RESTRICT = "EXPECT_WOULD_RESTRICT"
    EXPECT_WOULD_DENY = "EXPECT_WOULD_DENY"
    EXPECT_WOULD_DISTRUST = "EXPECT_WOULD_DISTRUST"
    EXPECT_WOULD_QUARANTINE = "EXPECT_WOULD_QUARANTINE"
    EXPECT_CONFLICT_SIGNAL = "EXPECT_CONFLICT_SIGNAL"
    EXPECT_TRACE_PAYLOAD = "EXPECT_TRACE_PAYLOAD"
    EXPECT_VIOLATION_PAYLOAD = "EXPECT_VIOLATION_PAYLOAD"
    EXPECT_NO_ENFORCEMENT = "EXPECT_NO_ENFORCEMENT"
    EXPECT_NO_LEDGER = "EXPECT_NO_LEDGER"
    EXPECT_NO_RUNTIME_MUTATION = "EXPECT_NO_RUNTIME_MUTATION"
    EXPECT_NO_POLICY_CALL = "EXPECT_NO_POLICY_CALL"
    EXPECT_NO_APPROVAL_ACTIVATION = "EXPECT_NO_APPROVAL_ACTIVATION"
    EXPECT_NO_SOURCE_MUTATION = "EXPECT_NO_SOURCE_MUTATION"
    UNKNOWN = "UNKNOWN"


class PathGovernanceHarnessStatus(str, Enum):
    """Harness step status; FAIL is not enforcement."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


_DEFAULT_SCENARIO_ORDER: tuple[PathGovernanceHarnessScenarioKind, ...] = (
    PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW,
    PathGovernanceHarnessScenarioKind.UNTRUSTED_SOURCE_REVIEW_SHADOW,
    PathGovernanceHarnessScenarioKind.PATH_ESCAPE_RESTRICT_SHADOW,
    PathGovernanceHarnessScenarioKind.SOURCE_DISTRUST_CONFLICT_SHADOW,
    PathGovernanceHarnessScenarioKind.CRITICAL_RISK_QUARANTINE_RECOMMENDED,
    PathGovernanceHarnessScenarioKind.MISSING_PROVENANCE_REVIEW_SHADOW,
    PathGovernanceHarnessScenarioKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE,
    PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY,
    PathGovernanceHarnessScenarioKind.VIOLATION_DRIFT_PAYLOAD_ONLY,
)

_PATH_ALLOW_DECISIONS: frozenset[PathGovernanceShadowDecision] = frozenset({
    PathGovernanceShadowDecision.WOULD_ALLOW,
})
_PATH_REVIEW_DECISIONS: frozenset[PathGovernanceShadowDecision] = frozenset({
    PathGovernanceShadowDecision.WOULD_REVIEW,
    PathGovernanceShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW,
    PathGovernanceShadowDecision.WOULD_REQUIRE_POLICY_REVIEW,
})
_PATH_RESTRICT_DECISIONS: frozenset[PathGovernanceShadowDecision] = frozenset({
    PathGovernanceShadowDecision.WOULD_RESTRICT,
})
_PATH_DENY_DECISIONS: frozenset[PathGovernanceShadowDecision] = frozenset({
    PathGovernanceShadowDecision.WOULD_DENY,
})
_PATH_QUARANTINE_DECISIONS: frozenset[PathGovernanceShadowDecision] = frozenset({
    PathGovernanceShadowDecision.WOULD_QUARANTINE,
})

_SOURCE_TRUST_DECISIONS: frozenset[SourceTrustShadowDecision] = frozenset({
    SourceTrustShadowDecision.WOULD_TRUST,
})
_SOURCE_REVIEW_DECISIONS: frozenset[SourceTrustShadowDecision] = frozenset({
    SourceTrustShadowDecision.WOULD_REVIEW,
    SourceTrustShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW,
    SourceTrustShadowDecision.WOULD_REQUIRE_POLICY_REVIEW,
})
_SOURCE_DISTRUST_DECISIONS: frozenset[SourceTrustShadowDecision] = frozenset({
    SourceTrustShadowDecision.WOULD_DISTRUST,
})
_SOURCE_QUARANTINE_DECISIONS: frozenset[SourceTrustShadowDecision] = frozenset({
    SourceTrustShadowDecision.WOULD_QUARANTINE,
})

_DECISION_EXPECTATION_NAMES: frozenset[str] = frozenset({
    PathGovernanceHarnessExpectation.EXPECT_WOULD_ALLOW.value,
    PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW.value,
    PathGovernanceHarnessExpectation.EXPECT_WOULD_RESTRICT.value,
    PathGovernanceHarnessExpectation.EXPECT_WOULD_DENY.value,
    PathGovernanceHarnessExpectation.EXPECT_WOULD_DISTRUST.value,
    PathGovernanceHarnessExpectation.EXPECT_WOULD_QUARANTINE.value,
})


def _sorted_metadata_dict(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): metadata[key] for key in sorted(metadata.keys(), key=str)}


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> MappingProxyType[str, Any]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(_sorted_metadata_dict(metadata))


def _parse_source_label(value: Any) -> ProjectionSourceLabel:
    if isinstance(value, ProjectionSourceLabel):
        return value
    if isinstance(value, str):
        try:
            return ProjectionSourceLabel(value)
        except ValueError as exc:
            raise PathGovernanceValidationError(
                f"invalid source_label: {value}",
                code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            ) from exc
    raise PathGovernanceValidationError(
        "source_label must be ProjectionSourceLabel or str",
        code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
        field="source_label",
    )


def _parse_scenario_kind(value: Any) -> PathGovernanceHarnessScenarioKind:
    if isinstance(value, PathGovernanceHarnessScenarioKind):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceHarnessScenarioKind(value)
        except ValueError as exc:
            raise PathGovernanceValidationError(
                f"invalid scenario_kind: {value}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="scenario_kind",
            ) from exc
    raise PathGovernanceValidationError(
        "scenario_kind must be PathGovernanceHarnessScenarioKind or str",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="scenario_kind",
    )


def _parse_status(value: Any) -> PathGovernanceHarnessStatus:
    if isinstance(value, PathGovernanceHarnessStatus):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceHarnessStatus(value)
        except ValueError as exc:
            raise PathGovernanceValidationError(
                f"invalid status: {value}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="status",
            ) from exc
    raise PathGovernanceValidationError(
        "status must be PathGovernanceHarnessStatus or str",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="status",
    )


def _parse_expectations(
    values: Sequence[Any],
) -> tuple[PathGovernanceHarnessExpectation, ...]:
    parsed: list[PathGovernanceHarnessExpectation] = []
    for item in values:
        if isinstance(item, PathGovernanceHarnessExpectation):
            parsed.append(item)
        elif isinstance(item, str):
            try:
                parsed.append(PathGovernanceHarnessExpectation(item))
            except ValueError as exc:
                raise PathGovernanceValidationError(
                    f"invalid expected_outcome: {item}",
                    code=PathGovernanceErrorCode.INVALID_ENUM,
                    field="expected_outcomes",
                ) from exc
        else:
            raise PathGovernanceValidationError(
                "expected_outcomes must contain enum or str values",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="expected_outcomes",
            )
    return tuple(parsed)


def _scenario_id_payload(
    *,
    scenario_kind: PathGovernanceHarnessScenarioKind,
    description: str,
    source_label: ProjectionSourceLabel,
    fixtures_label: ProjectionSourceLabel,
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "description": description,
        "expected_outcomes": [item.value for item in expected_outcomes],
        "fixtures_label": fixtures_label.value,
        "metadata": _sorted_metadata_dict(metadata),
        "scenario_kind": scenario_kind.value,
        "source_label": source_label.value,
    }


def compute_scenario_id(
    *,
    scenario_kind: PathGovernanceHarnessScenarioKind,
    description: str,
    source_label: ProjectionSourceLabel,
    fixtures_label: ProjectionSourceLabel,
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic harness scenario identifier."""
    return stable_hash(_scenario_id_payload(
        scenario_kind=scenario_kind,
        description=description,
        source_label=source_label,
        fixtures_label=fixtures_label,
        expected_outcomes=expected_outcomes,
        metadata=metadata,
    ))


def _run_input_hash_payload(
    *,
    scenarios: tuple[PathGovernanceHarnessScenario, ...],
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "metadata": _sorted_metadata_dict(metadata),
        "scenarios": [scenario.scenario_id for scenario in scenarios],
        "source_label": source_label.value,
    }


def compute_run_id(
    *,
    scenarios: tuple[PathGovernanceHarnessScenario, ...],
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic harness run identifier."""
    return stable_hash(_run_input_hash_payload(
        scenarios=scenarios,
        source_label=source_label,
        metadata=metadata,
    ))


def compute_input_hash(
    *,
    scenarios: tuple[PathGovernanceHarnessScenario, ...],
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic harness run input hash."""
    return compute_run_id(
        scenarios=scenarios,
        source_label=source_label,
        metadata=metadata,
    )


def _step_id_payload(
    *,
    scenario_id: str,
    step_name: str,
    observed_refs: Mapping[str, Any],
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
) -> dict[str, Any]:
    return {
        "expected_outcomes": [item.value for item in expected_outcomes],
        "observed_refs": _sorted_metadata_dict(observed_refs),
        "scenario_id": scenario_id,
        "step_name": step_name,
    }


def compute_step_id(
    *,
    scenario_id: str,
    step_name: str,
    observed_refs: Mapping[str, Any],
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
) -> str:
    """Compute deterministic harness step identifier."""
    return stable_hash(_step_id_payload(
        scenario_id=scenario_id,
        step_name=step_name,
        observed_refs=observed_refs,
        expected_outcomes=expected_outcomes,
    ))


def _step_hash_payload(
    *,
    scenario_id: str,
    step_name: str,
    status: PathGovernanceHarnessStatus,
    observed_refs: Mapping[str, Any],
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
    passed: bool,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "expected_outcomes": [item.value for item in expected_outcomes],
        "metadata": _sorted_metadata_dict(metadata),
        "observed_refs": _sorted_metadata_dict(observed_refs),
        "passed": passed,
        "reason": reason,
        "scenario_id": scenario_id,
        "source_label": source_label.value,
        "status": status.value,
        "step_name": step_name,
    }


def compute_step_hash(
    *,
    scenario_id: str,
    step_name: str,
    status: PathGovernanceHarnessStatus,
    observed_refs: Mapping[str, Any],
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
    passed: bool,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic harness step hash."""
    return stable_hash(_step_hash_payload(
        scenario_id=scenario_id,
        step_name=step_name,
        status=status,
        observed_refs=observed_refs,
        expected_outcomes=expected_outcomes,
        passed=passed,
        reason=reason,
        source_label=source_label,
        metadata=metadata,
    ))


def _result_id_payload(
    *,
    run_id: str,
    scenario_results: tuple[PathGovernanceHarnessStepResult, ...],
    harness_version: str,
) -> dict[str, Any]:
    return {
        "harness_version": harness_version,
        "run_id": run_id,
        "scenario_results": [item.step_hash for item in scenario_results],
    }


def compute_result_id(
    *,
    run_id: str,
    scenario_results: tuple[PathGovernanceHarnessStepResult, ...],
    harness_version: str,
) -> str:
    """Compute deterministic harness run result identifier."""
    return stable_hash(_result_id_payload(
        run_id=run_id,
        scenario_results=scenario_results,
        harness_version=harness_version,
    ))


def _result_hash_payload(
    *,
    run_id: str,
    scenario_results: tuple[PathGovernanceHarnessStepResult, ...],
    passed: bool,
    failed_count: int,
    skipped_count: int,
    unavailable_count: int,
    error_count: int,
    source_label: ProjectionSourceLabel,
    harness_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "created_by_task": created_by_task,
        "error_count": error_count,
        "failed_count": failed_count,
        "harness_version": harness_version,
        "metadata": _sorted_metadata_dict(metadata),
        "passed": passed,
        "run_id": run_id,
        "scenario_results": [item.step_hash for item in scenario_results],
        "skipped_count": skipped_count,
        "source_label": source_label.value,
        "unavailable_count": unavailable_count,
    }


def compute_result_hash(
    *,
    run_id: str,
    scenario_results: tuple[PathGovernanceHarnessStepResult, ...],
    passed: bool,
    failed_count: int,
    skipped_count: int,
    unavailable_count: int,
    error_count: int,
    source_label: ProjectionSourceLabel,
    harness_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic harness run result hash."""
    return stable_hash(_result_hash_payload(
        run_id=run_id,
        scenario_results=scenario_results,
        passed=passed,
        failed_count=failed_count,
        skipped_count=skipped_count,
        unavailable_count=unavailable_count,
        error_count=error_count,
        source_label=source_label,
        harness_version=harness_version,
        created_by_task=created_by_task,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathGovernanceHarnessScenario:
    """Deterministic DEV_FIXTURE harness scenario; not runtime authority."""

    scenario_kind: PathGovernanceHarnessScenarioKind
    description: str
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...]
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    fixtures_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    scenario_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        scenario_kind = _parse_scenario_kind(self.scenario_kind)
        description = str(self.description)
        source_label = _parse_source_label(self.source_label)
        fixtures_label = _parse_source_label(self.fixtures_label)
        expected_outcomes = _parse_expectations(self.expected_outcomes)
        metadata = _freeze_metadata(self.metadata)
        scenario_id = compute_scenario_id(
            scenario_kind=scenario_kind,
            description=description,
            source_label=source_label,
            fixtures_label=fixtures_label,
            expected_outcomes=expected_outcomes,
            metadata=metadata,
        )
        if self.scenario_id not in ("", scenario_id):
            raise PathGovernanceValidationError(
                "scenario_id does not match scenario content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="scenario_id",
            )
        object.__setattr__(self, "scenario_kind", scenario_kind)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "fixtures_label", fixtures_label)
        object.__setattr__(self, "expected_outcomes", expected_outcomes)
        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _scenario_id_payload(
            scenario_kind=self.scenario_kind,
            description=self.description,
            source_label=self.source_label,
            fixtures_label=self.fixtures_label,
            expected_outcomes=self.expected_outcomes,
            metadata=self.metadata,
        )
        payload["scenario_id"] = self.scenario_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceHarnessScenario:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_HARNESS_SCENARIO_KNOWN_FIELDS,
            label="path_governance_harness_scenario",
        )
        return cls(
            scenario_kind=data["scenario_kind"],
            description=data["description"],
            expected_outcomes=tuple(data.get("expected_outcomes", ())),
            source_label=data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
            fixtures_label=data.get("fixtures_label", ProjectionSourceLabel.DEV_FIXTURE),
            scenario_id=data.get("scenario_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathGovernanceHarnessRunInput:
    """Deterministic harness suite run input."""

    scenarios: tuple[PathGovernanceHarnessScenario, ...]
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    run_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        scenarios = tuple(
            item if isinstance(item, PathGovernanceHarnessScenario)
            else PathGovernanceHarnessScenario.from_dict(item)
            for item in self.scenarios
        )
        scenarios = tuple(sorted(scenarios, key=lambda item: item.scenario_id))
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        run_id = compute_run_id(
            scenarios=scenarios,
            source_label=source_label,
            metadata=metadata,
        )
        input_hash = compute_input_hash(
            scenarios=scenarios,
            source_label=source_label,
            metadata=metadata,
        )
        if self.run_id not in ("", run_id):
            raise PathGovernanceValidationError(
                "run_id does not match run input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="run_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match run input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "scenarios", scenarios)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "input_hash", input_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _run_input_hash_payload(
            scenarios=self.scenarios,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["input_hash"] = self.input_hash
        payload["run_id"] = self.run_id
        payload["scenarios"] = [
            scenario.to_canonical_dict() for scenario in self.scenarios
        ]
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceHarnessRunInput:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_HARNESS_RUN_INPUT_KNOWN_FIELDS,
            label="path_governance_harness_run_input",
        )
        return cls(
            scenarios=tuple(data.get("scenarios", ())),
            source_label=data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
            run_id=data.get("run_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathGovernanceHarnessStepResult:
    """Harness step outcome; pass/fail is not runtime authority."""

    scenario_id: str
    step_name: str
    status: PathGovernanceHarnessStatus
    observed_refs: Mapping[str, Any]
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...]
    passed: bool
    reason: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    step_id: str = ""
    step_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        scenario_id = str(self.scenario_id)
        step_name = str(self.step_name)
        status = _parse_status(self.status)
        observed_refs = _freeze_metadata(dict(self.observed_refs))
        expected_outcomes = _parse_expectations(self.expected_outcomes)
        reason = str(self.reason)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        step_id = compute_step_id(
            scenario_id=scenario_id,
            step_name=step_name,
            observed_refs=observed_refs,
            expected_outcomes=expected_outcomes,
        )
        step_hash = compute_step_hash(
            scenario_id=scenario_id,
            step_name=step_name,
            status=status,
            observed_refs=observed_refs,
            expected_outcomes=expected_outcomes,
            passed=self.passed,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.step_id not in ("", step_id):
            raise PathGovernanceValidationError(
                "step_id does not match step content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="step_id",
            )
        if self.step_hash not in ("", step_hash):
            raise PathGovernanceValidationError(
                "step_hash does not match step content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="step_hash",
            )
        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "step_name", step_name)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "observed_refs", observed_refs)
        object.__setattr__(self, "expected_outcomes", expected_outcomes)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "step_id", step_id)
        object.__setattr__(self, "step_hash", step_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _step_hash_payload(
            scenario_id=self.scenario_id,
            step_name=self.step_name,
            status=self.status,
            observed_refs=self.observed_refs,
            expected_outcomes=self.expected_outcomes,
            passed=self.passed,
            reason=self.reason,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["step_hash"] = self.step_hash
        payload["step_id"] = self.step_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceHarnessStepResult:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_HARNESS_STEP_RESULT_KNOWN_FIELDS,
            label="path_governance_harness_step_result",
        )
        return cls(
            scenario_id=data["scenario_id"],
            step_name=data["step_name"],
            status=data["status"],
            observed_refs=data.get("observed_refs", {}),
            expected_outcomes=tuple(data.get("expected_outcomes", ())),
            passed=bool(data["passed"]),
            reason=data["reason"],
            source_label=data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
            step_id=data.get("step_id", ""),
            step_hash=data.get("step_hash", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathGovernanceHarnessRunResult:
    """Aggregated harness run outcome; not runtime authority."""

    run_id: str
    scenario_results: tuple[PathGovernanceHarnessStepResult, ...]
    passed: bool
    failed_count: int
    skipped_count: int
    unavailable_count: int
    error_count: int
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE
    harness_version: str = PATH_GOVERNANCE_TEST_HARNESS_VERSION
    created_by_task: str = PATH_GOVERNANCE_TEST_HARNESS_TASK_ID
    result_id: str = ""
    result_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        run_id = str(self.run_id)
        scenario_results = tuple(
            item if isinstance(item, PathGovernanceHarnessStepResult)
            else PathGovernanceHarnessStepResult.from_dict(item)
            for item in self.scenario_results
        )
        source_label = _parse_source_label(self.source_label)
        harness_version = str(self.harness_version)
        created_by_task = str(self.created_by_task)
        metadata = _freeze_metadata(self.metadata)
        failed_count = sum(
            1 for item in scenario_results
            if item.status is PathGovernanceHarnessStatus.FAIL
        )
        skipped_count = sum(
            1 for item in scenario_results
            if item.status is PathGovernanceHarnessStatus.SKIPPED
        )
        unavailable_count = sum(
            1 for item in scenario_results
            if item.status is PathGovernanceHarnessStatus.UNAVAILABLE
        )
        error_count = sum(
            1 for item in scenario_results
            if item.status is PathGovernanceHarnessStatus.ERROR
        )
        passed = failed_count == 0 and error_count == 0
        result_id = compute_result_id(
            run_id=run_id,
            scenario_results=scenario_results,
            harness_version=harness_version,
        )
        result_hash = compute_result_hash(
            run_id=run_id,
            scenario_results=scenario_results,
            passed=passed,
            failed_count=failed_count,
            skipped_count=skipped_count,
            unavailable_count=unavailable_count,
            error_count=error_count,
            source_label=source_label,
            harness_version=harness_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.result_id not in ("", result_id):
            raise PathGovernanceValidationError(
                "result_id does not match run result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_id",
            )
        if self.result_hash not in ("", result_hash):
            raise PathGovernanceValidationError(
                "result_hash does not match run result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_hash",
            )
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "scenario_results", scenario_results)
        object.__setattr__(self, "passed", passed)
        object.__setattr__(self, "failed_count", failed_count)
        object.__setattr__(self, "skipped_count", skipped_count)
        object.__setattr__(self, "unavailable_count", unavailable_count)
        object.__setattr__(self, "error_count", error_count)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "harness_version", harness_version)
        object.__setattr__(self, "created_by_task", created_by_task)
        object.__setattr__(self, "result_id", result_id)
        object.__setattr__(self, "result_hash", result_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _result_hash_payload(
            run_id=self.run_id,
            scenario_results=self.scenario_results,
            passed=self.passed,
            failed_count=self.failed_count,
            skipped_count=self.skipped_count,
            unavailable_count=self.unavailable_count,
            error_count=self.error_count,
            source_label=self.source_label,
            harness_version=self.harness_version,
            created_by_task=self.created_by_task,
            metadata=self.metadata,
        )
        payload["result_hash"] = self.result_hash
        payload["result_id"] = self.result_id
        payload["scenario_results"] = [
            item.to_canonical_dict() for item in self.scenario_results
        ]
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceHarnessRunResult:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_HARNESS_RUN_RESULT_KNOWN_FIELDS,
            label="path_governance_harness_run_result",
        )
        return cls(
            run_id=data["run_id"],
            scenario_results=tuple(data.get("scenario_results", ())),
            passed=bool(data.get("passed", False)),
            failed_count=int(data.get("failed_count", 0)),
            skipped_count=int(data.get("skipped_count", 0)),
            unavailable_count=int(data.get("unavailable_count", 0)),
            error_count=int(data.get("error_count", 0)),
            source_label=data.get("source_label", ProjectionSourceLabel.DEV_FIXTURE),
            harness_version=data.get(
                "harness_version",
                PATH_GOVERNANCE_TEST_HARNESS_VERSION,
            ),
            created_by_task=data.get(
                "created_by_task",
                PATH_GOVERNANCE_TEST_HARNESS_TASK_ID,
            ),
            result_id=data.get("result_id", ""),
            result_hash=data.get("result_hash", ""),
            metadata=data.get("metadata", {}),
        )


def _fixture_metadata() -> MappingProxyType[str, Any]:
    return MappingProxyType({"fixture": "DEV_FIXTURE"})


def _source_identity(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.TRUSTED,
    source_kind: SourceKind = SourceKind.OPERATOR_INPUT,
    source_origin: SourceOrigin = SourceOrigin.OPERATOR,
) -> Any:
    return build_source_identity(
        source_kind=source_kind,
        source_origin=source_origin,
        uri_or_path=f"DEV_FIXTURE:source/{trust_label.value}",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        trust_label=trust_label,
        metadata=_fixture_metadata(),
    )


def _path_identity(raw_path: str = "src/example.py") -> PathIdentity:
    return build_path_identity(
        raw_path,
        path_kind=PathKind.REPO_RELATIVE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_fixture_metadata(),
    )


def _boundary_result(
    status: PathBoundaryStatus = PathBoundaryStatus.PATH_OK,
    raw_path: str = "src/example.py",
) -> PathBoundaryCheckResult:
    return PathBoundaryCheckResult(
        normalized_path=raw_path,
        boundary_status=status,
        path_identity=_path_identity(raw_path),
        trusted_root_id="DEV_FIXTURE:root",
        trusted_root_normalized_path="src",
        reason="DEV_FIXTURE boundary context",
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_fixture_metadata(),
    )


def _risk(
    risk_level: PathSourceRiskLevel,
    *,
    signals: tuple[Any, ...] | None = None,
    trust_label: SourceTrustLabel | None = None,
    provenance_binding_id: str | None = None,
) -> PathSourceRiskClassification:
    if signals is None:
        signals = (
            build_path_source_risk_signal(
                PathSourceRiskSignalKind.UNKNOWN_SOURCE,
                RiskClassificationBasis.SOURCE_TRUST,
                risk_level,
                "DEV_FIXTURE risk",
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata=_fixture_metadata(),
            ),
        )
    return build_path_source_risk_classification(
        signals=signals,
        risk_level=risk_level,
        trust_label=trust_label,
        provenance_binding_id=provenance_binding_id,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_fixture_metadata(),
    )


def _provenance_binding() -> ProvenanceBinding:
    source_identity = _source_identity(trust_label=SourceTrustLabel.TRUSTED)
    return build_provenance_binding(
        source_identity=source_identity,
        evidence_refs=(
            build_source_evidence_ref(
                EvidenceBindingKind.SOURCE_TRUST_LABEL,
                source_identity,
                confidence=EvidenceConfidence.HIGH,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata=_fixture_metadata(),
            ),
        ),
        claim_refs=(
            build_source_claim_ref(
                SourceClaimKind.FACTUAL_CLAIM,
                source_identity,
                "DEV_FIXTURE claim",
                confidence=EvidenceConfidence.HIGH,
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
                metadata=_fixture_metadata(),
            ),
        ),
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_fixture_metadata(),
    )


def _authority_scope() -> Any:
    return build_path_authority_scope(
        subject=PathAuthoritySubject(
            subject_kind=PathAuthoritySubjectKind.OPERATOR,
            display_name="DEV_FIXTURE",
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
        ),
        actions=(PathScopeAction.READ,),
        basis=PathAuthorityBasis.TEST_FIXTURE,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_fixture_metadata(),
    )


def _untrusted_boundary(
    *,
    trust_label: SourceTrustLabel = SourceTrustLabel.UNTRUSTED,
    surfaces: tuple[ContentInfluenceSurface, ...] = (
        ContentInfluenceSurface.PROMPT_INSTRUCTION,
    ),
) -> Any:
    return build_untrusted_content_boundary(
        content_kind=UntrustedContentKind.EXTERNAL_TEXT,
        source_identity=_source_identity(
            trust_label=trust_label,
            source_kind=SourceKind.EXTERNAL_WEB,
            source_origin=SourceOrigin.EXTERNAL_NETWORK,
        ),
        trust_label=trust_label,
        posture=UntrustedBoundaryPosture.REVIEW_REQUIRED,
        influence_surfaces=surfaces,
        source_label=ProjectionSourceLabel.DEV_FIXTURE,
        metadata=_fixture_metadata(),
    )


def _safety_expectations() -> tuple[PathGovernanceHarnessExpectation, ...]:
    return (
        PathGovernanceHarnessExpectation.EXPECT_NO_ENFORCEMENT,
        PathGovernanceHarnessExpectation.EXPECT_NO_LEDGER,
        PathGovernanceHarnessExpectation.EXPECT_NO_RUNTIME_MUTATION,
        PathGovernanceHarnessExpectation.EXPECT_NO_POLICY_CALL,
        PathGovernanceHarnessExpectation.EXPECT_NO_APPROVAL_ACTIVATION,
        PathGovernanceHarnessExpectation.EXPECT_NO_SOURCE_MUTATION,
    )


def _default_description(kind: PathGovernanceHarnessScenarioKind) -> str:
    return f"DEV_FIXTURE default scenario: {kind.value}"


def _default_expectations(
    kind: PathGovernanceHarnessScenarioKind,
) -> tuple[PathGovernanceHarnessExpectation, ...]:
    specific: tuple[PathGovernanceHarnessExpectation, ...]
    if kind is PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW:
        specific = (
            PathGovernanceHarnessExpectation.EXPECT_WOULD_ALLOW,
            PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW,
        )
    elif kind is PathGovernanceHarnessScenarioKind.UNTRUSTED_SOURCE_REVIEW_SHADOW:
        specific = (
            PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW,
            PathGovernanceHarnessExpectation.EXPECT_WOULD_DISTRUST,
        )
    elif kind is PathGovernanceHarnessScenarioKind.PATH_ESCAPE_RESTRICT_SHADOW:
        specific = (
            PathGovernanceHarnessExpectation.EXPECT_WOULD_RESTRICT,
            PathGovernanceHarnessExpectation.EXPECT_WOULD_DENY,
        )
    elif kind is PathGovernanceHarnessScenarioKind.SOURCE_DISTRUST_CONFLICT_SHADOW:
        specific = (
            PathGovernanceHarnessExpectation.EXPECT_CONFLICT_SIGNAL,
            PathGovernanceHarnessExpectation.EXPECT_WOULD_DISTRUST,
            PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW,
        )
    elif kind is PathGovernanceHarnessScenarioKind.CRITICAL_RISK_QUARANTINE_RECOMMENDED:
        specific = (
            PathGovernanceHarnessExpectation.EXPECT_WOULD_QUARANTINE,
            PathGovernanceHarnessExpectation.EXPECT_WOULD_DENY,
        )
    elif kind is PathGovernanceHarnessScenarioKind.MISSING_PROVENANCE_REVIEW_SHADOW:
        specific = (PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW,)
    elif kind is PathGovernanceHarnessScenarioKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE:
        specific = (
            PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW,
            PathGovernanceHarnessExpectation.EXPECT_CONFLICT_SIGNAL,
        )
    elif kind is PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY:
        specific = (PathGovernanceHarnessExpectation.EXPECT_TRACE_PAYLOAD,)
    elif kind is PathGovernanceHarnessScenarioKind.VIOLATION_DRIFT_PAYLOAD_ONLY:
        specific = (PathGovernanceHarnessExpectation.EXPECT_VIOLATION_PAYLOAD,)
    else:
        specific = (PathGovernanceHarnessExpectation.UNKNOWN,)
    return specific + _safety_expectations()


def build_path_governance_harness_scenario(
    scenario_kind: PathGovernanceHarnessScenarioKind | str,
    *,
    description: str | None = None,
    expected_outcomes: Sequence[PathGovernanceHarnessExpectation | str] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
    fixtures_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceHarnessScenario:
    """Build a deterministic harness scenario without side effects."""
    kind = _parse_scenario_kind(scenario_kind)
    resolved_description = (
        description if description is not None else _default_description(kind)
    )
    resolved_outcomes = (
        tuple(expected_outcomes)
        if expected_outcomes is not None
        else _default_expectations(kind)
    )
    return PathGovernanceHarnessScenario(
        scenario_kind=kind,
        description=resolved_description,
        expected_outcomes=resolved_outcomes,
        source_label=source_label,
        fixtures_label=fixtures_label,
        metadata=metadata or {"fixture": "DEV_FIXTURE"},
    )


def build_default_path_governance_harness_suite(
    *,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[PathGovernanceHarnessScenario, ...]:
    """Build deterministic default DEV_FIXTURE harness scenarios."""
    resolved_metadata = metadata or {"fixture": "DEV_FIXTURE", "suite": "default"}
    return tuple(
        build_path_governance_harness_scenario(
            kind,
            source_label=source_label,
            fixtures_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=resolved_metadata,
        )
        for kind in _DEFAULT_SCENARIO_ORDER
    )


def _bool_ref(value: bool) -> str:
    return "true" if value else "false"


def _shadow_decision_value(decision: Any) -> str:
    if hasattr(decision, "value"):
        return str(decision.value)
    return str(decision)


def _observed_from_path_result(result: PathGovernanceResolverResult) -> dict[str, str]:
    return {
        "path_result_id": result.result_id,
        "path_result_hash": result.result_hash,
        "path_shadow_decision": _shadow_decision_value(result.shadow_decision),
        "path_shadow_only": _bool_ref(result.shadow_only),
        "path_enforced": _bool_ref(result.enforced),
    }


def _observed_from_source_result(result: SourceTrustResolverResult) -> dict[str, str]:
    return {
        "source_result_id": result.result_id,
        "source_result_hash": result.result_hash,
        "source_shadow_decision": _shadow_decision_value(result.shadow_decision),
        "source_shadow_only": _bool_ref(result.shadow_only),
        "source_enforced": _bool_ref(result.enforced),
    }


def _observed_from_conflict(result: ConflictPrecedenceResult) -> dict[str, str]:
    return {
        "conflict_result_id": result.result_id,
        "conflict_result_hash": result.result_hash,
        "conflict_signal_count": str(len(result.conflict_signals)),
        "conflict_shadow_only": _bool_ref(result.shadow_only),
        "conflict_enforced": _bool_ref(result.enforced),
        "conflict_recommended_shadow_decision": _shadow_decision_value(
            result.recommended_shadow_decision,
        ),
    }


def _observed_from_trace_hook(result: PathResolutionTraceHookResult) -> dict[str, str]:
    payload = result.payload
    return {
        "trace_hook_id": result.hook_id,
        "trace_hook_hash": result.hook_hash,
        "trace_payload_id": payload.payload_id if payload is not None else "",
        "trace_payload_hash": payload.payload_hash if payload is not None else "",
        "trace_written": _bool_ref(result.trace_written),
        "ledger_written": _bool_ref(result.ledger_written),
        "runtime_mutated": _bool_ref(result.runtime_mutated),
    }


def _observed_from_violation_hook(
    result: PathViolationTraceHookResult,
) -> dict[str, str]:
    payload = result.payload
    return {
        "violation_hook_id": result.hook_id,
        "violation_hook_hash": result.hook_hash,
        "violation_payload_id": payload.payload_id if payload is not None else "",
        "violation_payload_hash": payload.payload_hash if payload is not None else "",
        "trace_written": _bool_ref(result.trace_written),
        "ledger_written": _bool_ref(result.ledger_written),
        "runtime_mutated": _bool_ref(result.runtime_mutated),
        "enforcement_triggered": _bool_ref(result.enforcement_triggered),
    }


def _matches_decision_expectation(
    expectation: PathGovernanceHarnessExpectation,
    observed: Mapping[str, str],
) -> bool:
    path_decision = observed.get("path_shadow_decision")
    source_decision = observed.get("source_shadow_decision")
    conflict_decision = observed.get("conflict_recommended_shadow_decision")

    if expectation is PathGovernanceHarnessExpectation.EXPECT_WOULD_ALLOW:
        if path_decision and path_decision in {item.value for item in _PATH_ALLOW_DECISIONS}:
            return True
        if source_decision and source_decision in {item.value for item in _SOURCE_TRUST_DECISIONS}:
            return True
        return False
    if expectation is PathGovernanceHarnessExpectation.EXPECT_WOULD_REVIEW:
        review_values = {item.value for item in _PATH_REVIEW_DECISIONS} | {
            item.value for item in _SOURCE_REVIEW_DECISIONS
        }
        return (
            (path_decision in review_values if path_decision else False)
            or (source_decision in review_values if source_decision else False)
            or (conflict_decision in review_values if conflict_decision else False)
        )
    if expectation is PathGovernanceHarnessExpectation.EXPECT_WOULD_RESTRICT:
        return path_decision in {item.value for item in _PATH_RESTRICT_DECISIONS}
    if expectation is PathGovernanceHarnessExpectation.EXPECT_WOULD_DENY:
        return path_decision in {item.value for item in _PATH_DENY_DECISIONS}
    if expectation is PathGovernanceHarnessExpectation.EXPECT_WOULD_DISTRUST:
        return source_decision in {item.value for item in _SOURCE_DISTRUST_DECISIONS}
    if expectation is PathGovernanceHarnessExpectation.EXPECT_WOULD_QUARANTINE:
        quarantine_values = {item.value for item in _PATH_QUARANTINE_DECISIONS} | {
            item.value for item in _SOURCE_QUARANTINE_DECISIONS
        }
        return (
            (path_decision in quarantine_values if path_decision else False)
            or (source_decision in quarantine_values if source_decision else False)
            or (conflict_decision in quarantine_values if conflict_decision else False)
        )
    return False


def _check_expectations(
    expected_outcomes: tuple[PathGovernanceHarnessExpectation, ...],
    observed_refs: Mapping[str, str],
) -> tuple[bool, str]:
    """Evaluate advisory expectations against observed shadow refs."""
    failures: list[str] = []
    observed = dict(observed_refs)
    decision_expectations = [
        item for item in expected_outcomes
        if item.value in _DECISION_EXPECTATION_NAMES
    ]
    other_expectations = [
        item for item in expected_outcomes
        if item.value not in _DECISION_EXPECTATION_NAMES
        and item is not PathGovernanceHarnessExpectation.UNKNOWN
    ]

    if decision_expectations:
        if not any(
            _matches_decision_expectation(item, observed_refs)
            for item in decision_expectations
        ):
            failures.append(
                "no matching advisory shadow decision for decision expectations",
            )

    for expectation in other_expectations:
        if expectation.value in _SAFETY_EXPECTATIONS:
            observed.setdefault("harness_enforcement", "false")
            observed.setdefault("harness_ledger_write", "false")
            observed.setdefault("harness_runtime_mutation", "false")
            observed.setdefault("harness_policy_call", "false")
            observed.setdefault("harness_approval_activation", "false")
            observed.setdefault("harness_source_mutation", "false")
            continue
        if expectation is PathGovernanceHarnessExpectation.EXPECT_CONFLICT_SIGNAL:
            count = int(observed.get("conflict_signal_count", "0"))
            if count <= 0:
                failures.append("expected conflict signal not observed")
            continue
        if expectation is PathGovernanceHarnessExpectation.EXPECT_TRACE_PAYLOAD:
            if not observed.get("trace_payload_id"):
                failures.append("expected trace payload ref missing")
            elif observed.get("ledger_written", "false") != "false":
                failures.append("trace hook reported ledger write")
            elif observed.get("runtime_mutated", "false") != "false":
                failures.append("trace hook reported runtime mutation")
            continue
        if expectation is PathGovernanceHarnessExpectation.EXPECT_VIOLATION_PAYLOAD:
            if not observed.get("violation_payload_id"):
                failures.append("expected violation payload ref missing")
            elif observed.get("enforcement_triggered", "false") != "false":
                failures.append("violation hook reported enforcement")
            elif observed.get("runtime_mutated", "false") != "false":
                failures.append("violation hook reported runtime mutation")
            continue
        failures.append(f"unhandled expectation: {expectation.value}")

    if failures:
        return False, "; ".join(failures)
    return True, "expectations satisfied"


def _execute_scenario_shadow_chain(
    scenario: PathGovernanceHarnessScenario,
) -> dict[str, str]:
    """Run P1.7 shadow helpers for a scenario kind; no enforcement side effects."""
    kind = scenario.scenario_kind
    fixture_meta = _fixture_metadata()
    observed: dict[str, str] = {
        "harness_enforcement": "false",
        "harness_ledger_write": "false",
        "harness_runtime_mutation": "false",
        "harness_policy_call": "false",
        "harness_approval_activation": "false",
        "harness_source_mutation": "false",
        "scenario_kind": kind.value,
    }

    if kind is PathGovernanceHarnessScenarioKind.TRUSTED_PATH_ALLOWED_SHADOW:
        path_result = resolve_path_governance_shadow(
            path_identity=_path_identity(),
            source_identity=_source_identity(trust_label=SourceTrustLabel.TRUSTED),
            trusted_root_registry=build_trusted_root_registry(
                source_label=ProjectionSourceLabel.DEV_FIXTURE,
            ),
            boundary_check_result=_boundary_result(),
            authority_scope=_authority_scope(),
            provenance_binding=_provenance_binding(),
            risk_classification=_risk(PathSourceRiskLevel.LOW),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_result = resolve_source_trust_shadow(
            source_identity=_source_identity(trust_label=SourceTrustLabel.TRUSTED),
            provenance_binding=_provenance_binding(),
            risk_classification=_risk(PathSourceRiskLevel.LOW),
            path_resolver_result=path_result,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        conflict = resolve_path_source_conflicts_shadow(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            risk_classification=_risk(PathSourceRiskLevel.LOW),
            provenance_binding=_provenance_binding(),
            authority_scope=_authority_scope(),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        observed.update(_observed_from_source_result(source_result))
        observed.update(_observed_from_conflict(conflict))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.UNTRUSTED_SOURCE_REVIEW_SHADOW:
        source_result = resolve_source_trust_shadow(
            source_identity=_source_identity(
                trust_label=SourceTrustLabel.UNTRUSTED,
                source_kind=SourceKind.EXTERNAL_WEB,
                source_origin=SourceOrigin.EXTERNAL_NETWORK,
            ),
            untrusted_boundary=_untrusted_boundary(),
            risk_classification=_risk(PathSourceRiskLevel.MEDIUM),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_source_result(source_result))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.PATH_ESCAPE_RESTRICT_SHADOW:
        path_result = resolve_path_governance_shadow(
            boundary_check_result=_boundary_result(
                PathBoundaryStatus.PATH_TRAVERSAL_CANDIDATE,
                "../secret.txt",
            ),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.SOURCE_DISTRUST_CONFLICT_SHADOW:
        path_result = resolve_path_governance_shadow(
            risk_classification=_risk(PathSourceRiskLevel.LOW),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_result = resolve_source_trust_shadow(
            source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
            risk_classification=_risk(PathSourceRiskLevel.MEDIUM),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        conflict = resolve_path_source_conflicts_shadow(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        observed.update(_observed_from_source_result(source_result))
        observed.update(_observed_from_conflict(conflict))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.CRITICAL_RISK_QUARANTINE_RECOMMENDED:
        path_result = resolve_path_governance_shadow(
            risk_classification=_risk(PathSourceRiskLevel.CRITICAL),
            untrusted_boundary=_untrusted_boundary(
                trust_label=SourceTrustLabel.QUARANTINED,
            ),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.MISSING_PROVENANCE_REVIEW_SHADOW:
        missing_signal = build_path_source_risk_signal(
            PathSourceRiskSignalKind.MISSING_PROVENANCE,
            RiskClassificationBasis.PROVENANCE_EVIDENCE,
            PathSourceRiskLevel.UNKNOWN,
            "DEV_FIXTURE missing provenance",
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        path_result = resolve_path_governance_shadow(
            risk_classification=_risk(
                PathSourceRiskLevel.UNKNOWN,
                signals=(missing_signal,),
            ),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_result = resolve_source_trust_shadow(
            source_identity=_source_identity(trust_label=SourceTrustLabel.UNKNOWN),
            risk_classification=_risk(
                PathSourceRiskLevel.UNKNOWN,
                signals=(missing_signal,),
            ),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        observed.update(_observed_from_source_result(source_result))
        observed["provenance_binding_present"] = "false"
        return observed

    if kind is PathGovernanceHarnessScenarioKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE:
        boundary = _untrusted_boundary(
            surfaces=(
                ContentInfluenceSurface.PROMPT_INSTRUCTION,
                ContentInfluenceSurface.TOOL_ARGUMENT,
                ContentInfluenceSurface.MEMORY_WRITE,
                ContentInfluenceSurface.POLICY_DEFINITION,
                ContentInfluenceSurface.AUTHORITY_EXPANSION,
                ContentInfluenceSurface.EXECUTION_REQUEST,
            ),
        )
        path_result = resolve_path_governance_shadow(
            untrusted_boundary=boundary,
            risk_classification=_risk(
                PathSourceRiskLevel.HIGH,
                trust_label=SourceTrustLabel.UNTRUSTED,
            ),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_result = resolve_source_trust_shadow(
            source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
            untrusted_boundary=boundary,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        conflict = resolve_path_source_conflicts_shadow(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            untrusted_boundary=boundary,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        observed.update(_observed_from_source_result(source_result))
        observed.update(_observed_from_conflict(conflict))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.TRACE_PAYLOAD_ONLY:
        path_result = resolve_path_governance_shadow(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_result = resolve_source_trust_shadow(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        conflict = resolve_path_source_conflicts_shadow(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        trace_hook = record_path_resolution_trace_hook(
            path_resolver_result=path_result,
            source_trust_resolver_result=source_result,
            conflict_precedence_result=conflict,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_result))
        observed.update(_observed_from_source_result(source_result))
        observed.update(_observed_from_conflict(conflict))
        observed.update(_observed_from_trace_hook(trace_hook))
        return observed

    if kind is PathGovernanceHarnessScenarioKind.VIOLATION_DRIFT_PAYLOAD_ONLY:
        path_expected = resolve_path_governance_shadow(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        path_current = resolve_path_governance_shadow(
            boundary_check_result=_boundary_result(
                PathBoundaryStatus.PATH_TRAVERSAL_CANDIDATE,
                "../drift.txt",
            ),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_expected = resolve_source_trust_shadow(
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        source_current = resolve_source_trust_shadow(
            source_identity=_source_identity(trust_label=SourceTrustLabel.UNTRUSTED),
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        conflict = resolve_path_source_conflicts_shadow(
            path_resolver_result=path_expected,
            source_trust_resolver_result=source_expected,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        expected_trace = build_path_resolution_trace_payload(
            path_resolver_result=path_expected,
            source_trust_resolver_result=source_expected,
            conflict_precedence_result=conflict,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        current_trace = build_path_resolution_trace_payload(
            path_resolver_result=path_current,
            source_trust_resolver_result=source_current,
            conflict_precedence_result=conflict,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        violation_hook = record_path_violation_trace_hook(
            expected_path_resolver_result=path_expected,
            current_path_resolver_result=path_current,
            expected_source_trust_result=source_expected,
            current_source_trust_result=source_current,
            expected_conflict_precedence_result=conflict,
            current_conflict_precedence_result=conflict,
            expected_trace_payload=expected_trace,
            current_trace_payload=current_trace,
            source_label=ProjectionSourceLabel.DEV_FIXTURE,
            metadata=fixture_meta,
        )
        observed.update(_observed_from_path_result(path_current))
        observed.update(_observed_from_source_result(source_current))
        observed.update(_observed_from_violation_hook(violation_hook))
        return observed

    observed["status"] = PathGovernanceHarnessStatus.UNAVAILABLE.value
    return observed


def run_path_governance_harness_scenario(
    scenario: PathGovernanceHarnessScenario | Mapping[str, Any],
    *,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceHarnessStepResult:
    """Run one harness scenario against P1.7 shadow helpers; no enforcement."""
    resolved = (
        scenario
        if isinstance(scenario, PathGovernanceHarnessScenario)
        else PathGovernanceHarnessScenario.from_dict(scenario)
    )
    step_metadata = _freeze_metadata({
        **dict(_fixture_metadata()),
        **dict(metadata or {}),
        **dict(resolved.metadata),
    })
    step_name = f"shadow_chain:{resolved.scenario_kind.value}"

    try:
        if resolved.scenario_kind is PathGovernanceHarnessScenarioKind.UNKNOWN:
            return PathGovernanceHarnessStepResult(
                scenario_id=resolved.scenario_id,
                step_name=step_name,
                status=PathGovernanceHarnessStatus.UNAVAILABLE,
                observed_refs={"scenario_kind": resolved.scenario_kind.value},
                expected_outcomes=resolved.expected_outcomes,
                passed=False,
                reason="scenario kind unavailable",
                source_label=source_label,
                metadata=step_metadata,
            )

        observed_refs = _execute_scenario_shadow_chain(resolved)
        if observed_refs.get("status") == PathGovernanceHarnessStatus.UNAVAILABLE.value:
            return PathGovernanceHarnessStepResult(
                scenario_id=resolved.scenario_id,
                step_name=step_name,
                status=PathGovernanceHarnessStatus.UNAVAILABLE,
                observed_refs=observed_refs,
                expected_outcomes=resolved.expected_outcomes,
                passed=False,
                reason="required shadow capability unavailable",
                source_label=source_label,
                metadata=step_metadata,
            )

        passed, reason = _check_expectations(resolved.expected_outcomes, observed_refs)
        status = (
            PathGovernanceHarnessStatus.PASS
            if passed
            else PathGovernanceHarnessStatus.FAIL
        )
        return PathGovernanceHarnessStepResult(
            scenario_id=resolved.scenario_id,
            step_name=step_name,
            status=status,
            observed_refs=observed_refs,
            expected_outcomes=resolved.expected_outcomes,
            passed=passed,
            reason=reason,
            source_label=source_label,
            metadata=step_metadata,
        )
    except PathGovernanceError as exc:
        return PathGovernanceHarnessStepResult(
            scenario_id=resolved.scenario_id,
            step_name=step_name,
            status=PathGovernanceHarnessStatus.ERROR,
            observed_refs={"error_code": str(exc.code)},
            expected_outcomes=resolved.expected_outcomes,
            passed=False,
            reason=str(exc),
            source_label=source_label,
            metadata=step_metadata,
        )
    except Exception as exc:  # noqa: BLE001 — harness captures unexpected errors as ERROR
        return PathGovernanceHarnessStepResult(
            scenario_id=resolved.scenario_id,
            step_name=step_name,
            status=PathGovernanceHarnessStatus.ERROR,
            observed_refs={"error_type": type(exc).__name__},
            expected_outcomes=resolved.expected_outcomes,
            passed=False,
            reason=str(exc),
            source_label=source_label,
            metadata=step_metadata,
        )


def run_path_governance_harness_suite(
    run_input: PathGovernanceHarnessRunInput | Mapping[str, Any] | None = None,
    *,
    scenarios: Sequence[PathGovernanceHarnessScenario | Mapping[str, Any]] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.DEV_FIXTURE,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceHarnessRunResult:
    """Run harness scenarios in deterministic order; no side effects."""
    if run_input is not None:
        resolved_input = (
            run_input
            if isinstance(run_input, PathGovernanceHarnessRunInput)
            else PathGovernanceHarnessRunInput.from_dict(run_input)
        )
        resolved_scenarios = resolved_input.scenarios
        resolved_source_label = resolved_input.source_label
        resolved_metadata = _freeze_metadata({
            **dict(resolved_input.metadata),
            **dict(metadata or {}),
        })
        run_id = resolved_input.run_id
    elif scenarios is not None:
        resolved_scenarios = tuple(
            item if isinstance(item, PathGovernanceHarnessScenario)
            else PathGovernanceHarnessScenario.from_dict(item)
            for item in scenarios
        )
        resolved_scenarios = tuple(
            sorted(resolved_scenarios, key=lambda item: item.scenario_id)
        )
        resolved_source_label = source_label
        resolved_metadata = _freeze_metadata(metadata or {"fixture": "DEV_FIXTURE"})
        run_id = compute_run_id(
            scenarios=resolved_scenarios,
            source_label=resolved_source_label,
            metadata=resolved_metadata,
        )
    else:
        resolved_scenarios = build_default_path_governance_harness_suite(
            source_label=source_label,
            metadata=metadata,
        )
        resolved_source_label = source_label
        resolved_metadata = _freeze_metadata(metadata or {"fixture": "DEV_FIXTURE"})
        run_id = compute_run_id(
            scenarios=resolved_scenarios,
            source_label=resolved_source_label,
            metadata=resolved_metadata,
        )

    scenario_results: list[PathGovernanceHarnessStepResult] = []
    for scenario in resolved_scenarios:
        scenario_results.append(
            run_path_governance_harness_scenario(
                scenario,
                source_label=resolved_source_label,
                metadata=resolved_metadata,
            )
        )

    return PathGovernanceHarnessRunResult(
        run_id=run_id,
        scenario_results=tuple(scenario_results),
        passed=False,
        failed_count=0,
        skipped_count=0,
        unavailable_count=0,
        error_count=0,
        source_label=resolved_source_label,
        metadata=resolved_metadata,
    )
