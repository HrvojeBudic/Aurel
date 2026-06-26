"""Path violation / drift trace hook (P1.7.14).

Violation/drift trace hook records evidence of mismatch.
It does not correct, enforce, rollback, or punish.
Drift detection is observability before control.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .conflict_precedence import ConflictPrecedenceResult
from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel
from .path_authority_scope import PathAuthorityScope
from .path_resolution_trace import PathResolutionTracePayload
from .path_resolver import (
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
)
from .risk_classification import PathSourceRiskClassification, PathSourceRiskLevel
from .serialization import stable_hash
from .source_provenance import ProvenanceBinding
from .source_trust_resolver import SourceTrustResolverResult
from .untrusted_content_boundary import UntrustedContentBoundary
from .validation import validate_known_fields

PATH_VIOLATION_TRACE_TASK_ID = "P1.7.14"
PATH_VIOLATION_TRACE_PAYLOAD_SCHEMA = "path_violation_trace_payload.v1"
PATH_VIOLATION_TRACE_HOOK_VERSION = "path_violation_trace_hook.v1"

PATH_VIOLATION_TRACE_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "input_id",
    "expected_path_resolver_result",
    "current_path_resolver_result",
    "expected_source_trust_result",
    "current_source_trust_result",
    "expected_conflict_precedence_result",
    "current_conflict_precedence_result",
    "expected_trace_payload",
    "current_trace_payload",
    "risk_classification",
    "provenance_binding",
    "authority_scope",
    "untrusted_boundary",
    "source_label",
    "input_hash",
    "metadata",
})

PATH_VIOLATION_TRACE_PAYLOAD_KNOWN_FIELDS: frozenset[str] = frozenset({
    "payload_id",
    "event_kind",
    "violation_subject_ref",
    "severity",
    "violation_summary",
    "expected_refs",
    "current_refs",
    "drift_reasons",
    "source_label",
    "payload_hash",
    "schema_version",
    "created_by_task",
    "metadata",
})

PATH_VIOLATION_TRACE_HOOK_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "hook_id",
    "input_id",
    "payload",
    "hook_mode",
    "disposition",
    "sink_name",
    "trace_written",
    "ledger_written",
    "runtime_mutated",
    "enforcement_triggered",
    "source_label",
    "hook_hash",
    "created_by_task",
    "hook_version",
    "metadata",
})

PATH_SOURCE_DRIFT_SIGNAL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "drift_signal_id",
    "event_kind",
    "severity",
    "expected_ref",
    "current_ref",
    "reason",
    "source_label",
    "metadata",
})

_SEVERITY_RANK: dict[PathViolationSeverity, int] = {}

_FORBIDDEN_SUMMARY_TOKENS: frozenset[str] = frozenset({
    "ALLOW",
    "ALLOWED",
    "DENY",
    "DENIED",
    "BLOCK",
    "BLOCKED",
    "TRUST",
    "DISTRUST",
    "ENFORCE",
    "ENFORCED",
    "APPROVED",
    "QUARANTINE",
    "QUARANTINED",
    "QUARANTINE_NOW",
    "ROLLED_BACK",
    "CORRECTED",
    "REPAIRED",
})


class PathViolationTraceEventKind(str, Enum):
    """Violation/drift event classification; not deny or correction."""

    PATH_BOUNDARY_VIOLATION_CANDIDATE = "PATH_BOUNDARY_VIOLATION_CANDIDATE"
    PATH_TRAVERSAL_DRIFT = "PATH_TRAVERSAL_DRIFT"
    SOURCE_TRUST_DRIFT = "SOURCE_TRUST_DRIFT"
    RISK_CLASSIFICATION_DRIFT = "RISK_CLASSIFICATION_DRIFT"
    CONFLICT_PRECEDENCE_DRIFT = "CONFLICT_PRECEDENCE_DRIFT"
    PROVENANCE_EXPECTATION_MISSING = "PROVENANCE_EXPECTATION_MISSING"
    AUTHORITY_SCOPE_MISSING_DRIFT = "AUTHORITY_SCOPE_MISSING_DRIFT"
    UNTRUSTED_BOUNDARY_DRIFT = "UNTRUSTED_BOUNDARY_DRIFT"
    TRACE_PAYLOAD_MISMATCH = "TRACE_PAYLOAD_MISMATCH"
    VIOLATION_TRACE_PAYLOAD_CREATED = "VIOLATION_TRACE_PAYLOAD_CREATED"
    VIOLATION_TRACE_SINK_UNAVAILABLE = "VIOLATION_TRACE_SINK_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class PathViolationSeverity(str, Enum):
    """Violation/drift severity candidate; does not block or enforce."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PathViolationTraceHookMode(str, Enum):
    """Violation trace hook delivery mode; does not imply enforcement."""

    PAYLOAD_ONLY = "PAYLOAD_ONLY"
    INJECTED_SINK = "INJECTED_SINK"
    TRACE_SPINE_UNAVAILABLE = "TRACE_SPINE_UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PathViolationTraceDisposition(str, Enum):
    """Violation trace hook outcome disposition; not runtime action."""

    WOULD_RECORD = "WOULD_RECORD"
    PAYLOAD_CREATED = "PAYLOAD_CREATED"
    RECORDED_TO_INJECTED_SINK = "RECORDED_TO_INJECTED_SINK"
    TRACE_SPINE_UNAVAILABLE = "TRACE_SPINE_UNAVAILABLE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PathViolationTraceReason(str, Enum):
    """Violation/drift payload construction reason; does not enforce."""

    PATH_RESOLVER_RESULT_PRESENT = "PATH_RESOLVER_RESULT_PRESENT"
    SOURCE_TRUST_RESULT_PRESENT = "SOURCE_TRUST_RESULT_PRESENT"
    CONFLICT_PRECEDENCE_PRESENT = "CONFLICT_PRECEDENCE_PRESENT"
    RISK_CLASSIFICATION_PRESENT = "RISK_CLASSIFICATION_PRESENT"
    EXPECTED_TRACE_PAYLOAD_PRESENT = "EXPECTED_TRACE_PAYLOAD_PRESENT"
    CURRENT_TRACE_PAYLOAD_PRESENT = "CURRENT_TRACE_PAYLOAD_PRESENT"
    PATH_BOUNDARY_CHANGED = "PATH_BOUNDARY_CHANGED"
    SOURCE_TRUST_CHANGED = "SOURCE_TRUST_CHANGED"
    RISK_CLASSIFICATION_CHANGED = "RISK_CLASSIFICATION_CHANGED"
    CONFLICT_PRECEDENCE_CHANGED = "CONFLICT_PRECEDENCE_CHANGED"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    AUTHORITY_SCOPE_MISSING = "AUTHORITY_SCOPE_MISSING"
    BOUNDARY_CONTEXT_CHANGED = "BOUNDARY_CONTEXT_CHANGED"
    SHADOW_ONLY_CONTEXT = "SHADOW_ONLY_CONTEXT"
    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    LEDGER_UNAVAILABLE = "LEDGER_UNAVAILABLE"
    TRACE_SPINE_UNAVAILABLE = "TRACE_SPINE_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


# Populate severity rank after enum definition
_SEVERITY_RANK.update({
    PathViolationSeverity.NONE: 0,
    PathViolationSeverity.LOW: 1,
    PathViolationSeverity.MEDIUM: 2,
    PathViolationSeverity.HIGH: 3,
    PathViolationSeverity.CRITICAL: 4,
    PathViolationSeverity.UNKNOWN: 5,
})


def _parse_source_label(value: ProjectionSourceLabel | str) -> ProjectionSourceLabel:
    if isinstance(value, ProjectionSourceLabel):
        return value
    if isinstance(value, str):
        try:
            return ProjectionSourceLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            ) from exc
    raise PathGovernanceError(
        "source_label must be a string or ProjectionSourceLabel",
        code=PathGovernanceErrorCode.INVALID_SOURCE_LABEL,
        field="source_label",
    )


def _parse_event_kind(
    value: PathViolationTraceEventKind | str,
) -> PathViolationTraceEventKind:
    if isinstance(value, PathViolationTraceEventKind):
        return value
    if isinstance(value, str):
        try:
            return PathViolationTraceEventKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid event_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="event_kind",
            ) from exc
    raise PathGovernanceError(
        "event_kind must be a string or PathViolationTraceEventKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="event_kind",
    )


def _parse_severity(value: PathViolationSeverity | str) -> PathViolationSeverity:
    if isinstance(value, PathViolationSeverity):
        return value
    if isinstance(value, str):
        try:
            return PathViolationSeverity(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid severity: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="severity",
            ) from exc
    raise PathGovernanceError(
        "severity must be a string or PathViolationSeverity",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="severity",
    )


def _parse_hook_mode(
    value: PathViolationTraceHookMode | str,
) -> PathViolationTraceHookMode:
    if isinstance(value, PathViolationTraceHookMode):
        return value
    if isinstance(value, str):
        try:
            return PathViolationTraceHookMode(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid hook_mode: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="hook_mode",
            ) from exc
    raise PathGovernanceError(
        "hook_mode must be a string or PathViolationTraceHookMode",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="hook_mode",
    )


def _parse_disposition(
    value: PathViolationTraceDisposition | str,
) -> PathViolationTraceDisposition:
    if isinstance(value, PathViolationTraceDisposition):
        return value
    if isinstance(value, str):
        try:
            return PathViolationTraceDisposition(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid disposition: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="disposition",
            ) from exc
    raise PathGovernanceError(
        "disposition must be a string or PathViolationTraceDisposition",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="disposition",
    )


def _parse_drift_reasons(
    value: Sequence[PathViolationTraceReason | str] | None,
) -> tuple[PathViolationTraceReason, ...]:
    if value is None:
        return ()
    reasons: list[PathViolationTraceReason] = []
    for item in value:
        if isinstance(item, PathViolationTraceReason):
            reasons.append(item)
        elif isinstance(item, str):
            try:
                reasons.append(PathViolationTraceReason(item))
            except ValueError as exc:
                raise PathGovernanceError(
                    f"invalid drift_reason: {item!r}",
                    code=PathGovernanceErrorCode.INVALID_ENUM,
                    field="drift_reasons",
                ) from exc
        else:
            raise PathGovernanceError(
                "drift_reasons must contain PathViolationTraceReason or str values",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="drift_reasons",
            )
    return tuple(sorted(set(reasons), key=lambda reason: reason.value))


def _required_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise PathGovernanceValidationError(
            f"{field_name} must be a non-empty string",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return value


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    raw = {} if metadata is None else metadata
    if not isinstance(raw, MappingABC):
        raise PathGovernanceValidationError(
            "metadata must be a mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="metadata",
        )
    frozen = dict(raw)
    stable_hash(frozen)
    return MappingProxyType(frozen)


def _sorted_metadata_dict(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return dict(sorted(metadata.items(), key=lambda item: item[0]))


def _object_ref(object_id: str, object_hash: str) -> str:
    if not object_id and not object_hash:
        return ""
    if object_id and object_hash:
        return f"{object_id}:{object_hash}"
    return object_id or object_hash


def _build_path_resolver_result(
    value: PathGovernanceResolverResult | Mapping[str, Any] | None,
) -> PathGovernanceResolverResult | None:
    if value is None:
        return None
    if isinstance(value, PathGovernanceResolverResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_resolver_result must be a PathGovernanceResolverResult or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="path_resolver_result",
        )
    return PathGovernanceResolverResult.from_dict(value)


def _build_source_trust_resolver_result(
    value: SourceTrustResolverResult | Mapping[str, Any] | None,
) -> SourceTrustResolverResult | None:
    if value is None:
        return None
    if isinstance(value, SourceTrustResolverResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "source_trust_result must be a SourceTrustResolverResult or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="source_trust_result",
        )
    return SourceTrustResolverResult.from_dict(value)


def _build_conflict_precedence_result(
    value: ConflictPrecedenceResult | Mapping[str, Any] | None,
) -> ConflictPrecedenceResult | None:
    if value is None:
        return None
    if isinstance(value, ConflictPrecedenceResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "conflict_precedence_result must be a ConflictPrecedenceResult or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="conflict_precedence_result",
        )
    return ConflictPrecedenceResult.from_dict(value)


def _build_trace_payload(
    value: PathResolutionTracePayload | Mapping[str, Any] | None,
) -> PathResolutionTracePayload | None:
    if value is None:
        return None
    if isinstance(value, PathResolutionTracePayload):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "trace_payload must be a PathResolutionTracePayload or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="trace_payload",
        )
    return PathResolutionTracePayload.from_dict(value)


def _build_risk_classification(
    value: PathSourceRiskClassification | Mapping[str, Any] | None,
) -> PathSourceRiskClassification | None:
    if value is None:
        return None
    if isinstance(value, PathSourceRiskClassification):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "risk_classification must be a PathSourceRiskClassification or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="risk_classification",
        )
    return PathSourceRiskClassification.from_dict(value)


def _build_untrusted_boundary(
    value: UntrustedContentBoundary | Mapping[str, Any] | None,
) -> UntrustedContentBoundary | None:
    if value is None:
        return None
    if isinstance(value, UntrustedContentBoundary):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "untrusted_boundary must be an UntrustedContentBoundary or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="untrusted_boundary",
        )
    return UntrustedContentBoundary.from_dict(value)


def _build_provenance_binding(
    value: ProvenanceBinding | Mapping[str, Any] | None,
) -> ProvenanceBinding | None:
    if value is None:
        return None
    if isinstance(value, ProvenanceBinding):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "provenance_binding must be a ProvenanceBinding or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="provenance_binding",
        )
    return ProvenanceBinding.from_dict(value)


def _build_authority_scope(
    value: PathAuthorityScope | Mapping[str, Any] | None,
) -> PathAuthorityScope | None:
    if value is None:
        return None
    if isinstance(value, PathAuthorityScope):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "authority_scope must be a PathAuthorityScope or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="authority_scope",
        )
    return PathAuthorityScope.from_dict(value)


def _validate_violation_summary(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "violation_summary must be a mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="violation_summary",
        )

    def _check_item(item: Any) -> None:
        if isinstance(item, str):
            upper = item.upper()
            if upper in _FORBIDDEN_SUMMARY_TOKENS:
                raise PathGovernanceValidationError(
                    "violation_summary must remain observational only",
                    code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                    field="violation_summary",
                )
        elif isinstance(item, MappingABC):
            for nested in item.values():
                _check_item(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                _check_item(nested)

    for item in value.values():
        _check_item(item)
    return MappingProxyType(dict(value))


def _risk_level_to_severity(level: PathSourceRiskLevel) -> PathViolationSeverity:
    try:
        return PathViolationSeverity(level.value)
    except ValueError:
        return PathViolationSeverity.UNKNOWN


def _path_result_ref(result: PathGovernanceResolverResult | None) -> str:
    if result is None:
        return ""
    return _object_ref(result.result_id, result.result_hash)


def _source_result_ref(result: SourceTrustResolverResult | None) -> str:
    if result is None:
        return ""
    return _object_ref(result.result_id, result.result_hash)


def _conflict_result_ref(result: ConflictPrecedenceResult | None) -> str:
    if result is None:
        return ""
    return _object_ref(result.result_id, result.result_hash)


def _trace_payload_ref(payload: PathResolutionTracePayload | None) -> str:
    if payload is None:
        return ""
    return _object_ref(payload.payload_id, payload.payload_hash)


def _risk_ref(risk: PathSourceRiskClassification | None) -> str:
    if risk is None:
        return ""
    return _object_ref(risk.classification_id, risk.classification_hash)


def _provenance_ref(binding: ProvenanceBinding | None) -> str:
    if binding is None:
        return ""
    return _object_ref(binding.binding_id, binding.binding_hash)


def _authority_ref(scope: PathAuthorityScope | None) -> str:
    if scope is None:
        return ""
    return _object_ref(scope.scope_id, scope.scope_hash)


def _boundary_ref(boundary: UntrustedContentBoundary | None) -> str:
    if boundary is None:
        return ""
    return _object_ref(boundary.boundary_id, boundary.boundary_hash)


def _input_payload(
    *,
    expected_path_resolver_result: PathGovernanceResolverResult | None,
    current_path_resolver_result: PathGovernanceResolverResult | None,
    expected_source_trust_result: SourceTrustResolverResult | None,
    current_source_trust_result: SourceTrustResolverResult | None,
    expected_conflict_precedence_result: ConflictPrecedenceResult | None,
    current_conflict_precedence_result: ConflictPrecedenceResult | None,
    expected_trace_payload: PathResolutionTracePayload | None,
    current_trace_payload: PathResolutionTracePayload | None,
    risk_classification: PathSourceRiskClassification | None,
    provenance_binding: ProvenanceBinding | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authority_scope": (
            None if authority_scope is None else authority_scope.to_canonical_dict()
        ),
        "current_conflict_precedence_result": (
            None
            if current_conflict_precedence_result is None
            else current_conflict_precedence_result.to_canonical_dict()
        ),
        "current_path_resolver_result": (
            None
            if current_path_resolver_result is None
            else current_path_resolver_result.to_canonical_dict()
        ),
        "current_source_trust_result": (
            None
            if current_source_trust_result is None
            else current_source_trust_result.to_canonical_dict()
        ),
        "current_trace_payload": (
            None
            if current_trace_payload is None
            else current_trace_payload.to_canonical_dict()
        ),
        "expected_conflict_precedence_result": (
            None
            if expected_conflict_precedence_result is None
            else expected_conflict_precedence_result.to_canonical_dict()
        ),
        "expected_path_resolver_result": (
            None
            if expected_path_resolver_result is None
            else expected_path_resolver_result.to_canonical_dict()
        ),
        "expected_source_trust_result": (
            None
            if expected_source_trust_result is None
            else expected_source_trust_result.to_canonical_dict()
        ),
        "expected_trace_payload": (
            None
            if expected_trace_payload is None
            else expected_trace_payload.to_canonical_dict()
        ),
        "metadata": _sorted_metadata_dict(metadata),
        "provenance_binding": (
            None
            if provenance_binding is None
            else provenance_binding.to_canonical_dict()
        ),
        "risk_classification": (
            None
            if risk_classification is None
            else risk_classification.to_canonical_dict()
        ),
        "source_label": source_label.value,
        "untrusted_boundary": (
            None
            if untrusted_boundary is None
            else untrusted_boundary.to_canonical_dict()
        ),
    }


def compute_path_violation_trace_input_hash(
    *,
    expected_path_resolver_result: PathGovernanceResolverResult | None,
    current_path_resolver_result: PathGovernanceResolverResult | None,
    expected_source_trust_result: SourceTrustResolverResult | None,
    current_source_trust_result: SourceTrustResolverResult | None,
    expected_conflict_precedence_result: ConflictPrecedenceResult | None,
    current_conflict_precedence_result: ConflictPrecedenceResult | None,
    expected_trace_payload: PathResolutionTracePayload | None,
    current_trace_payload: PathResolutionTracePayload | None,
    risk_classification: PathSourceRiskClassification | None,
    provenance_binding: ProvenanceBinding | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path violation trace input hash."""
    return stable_hash(_input_payload(
        expected_path_resolver_result=expected_path_resolver_result,
        current_path_resolver_result=current_path_resolver_result,
        expected_source_trust_result=expected_source_trust_result,
        current_source_trust_result=current_source_trust_result,
        expected_conflict_precedence_result=expected_conflict_precedence_result,
        current_conflict_precedence_result=current_conflict_precedence_result,
        expected_trace_payload=expected_trace_payload,
        current_trace_payload=current_trace_payload,
        risk_classification=risk_classification,
        provenance_binding=provenance_binding,
        authority_scope=authority_scope,
        untrusted_boundary=untrusted_boundary,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathViolationTraceInput:
    """Hash-ready path violation trace input; not enforcement authority."""

    expected_path_resolver_result: PathGovernanceResolverResult | None = None
    current_path_resolver_result: PathGovernanceResolverResult | None = None
    expected_source_trust_result: SourceTrustResolverResult | None = None
    current_source_trust_result: SourceTrustResolverResult | None = None
    expected_conflict_precedence_result: ConflictPrecedenceResult | None = None
    current_conflict_precedence_result: ConflictPrecedenceResult | None = None
    expected_trace_payload: PathResolutionTracePayload | None = None
    current_trace_payload: PathResolutionTracePayload | None = None
    risk_classification: PathSourceRiskClassification | None = None
    provenance_binding: ProvenanceBinding | None = None
    authority_scope: PathAuthorityScope | None = None
    untrusted_boundary: UntrustedContentBoundary | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    input_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        expected_path = _build_path_resolver_result(self.expected_path_resolver_result)
        current_path = _build_path_resolver_result(self.current_path_resolver_result)
        expected_source = _build_source_trust_resolver_result(
            self.expected_source_trust_result,
        )
        current_source = _build_source_trust_resolver_result(
            self.current_source_trust_result,
        )
        expected_conflict = _build_conflict_precedence_result(
            self.expected_conflict_precedence_result,
        )
        current_conflict = _build_conflict_precedence_result(
            self.current_conflict_precedence_result,
        )
        expected_trace = _build_trace_payload(self.expected_trace_payload)
        current_trace = _build_trace_payload(self.current_trace_payload)
        risk_classification = _build_risk_classification(self.risk_classification)
        provenance_binding = _build_provenance_binding(self.provenance_binding)
        authority_scope = _build_authority_scope(self.authority_scope)
        untrusted_boundary = _build_untrusted_boundary(self.untrusted_boundary)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        input_hash = compute_path_violation_trace_input_hash(
            expected_path_resolver_result=expected_path,
            current_path_resolver_result=current_path,
            expected_source_trust_result=expected_source,
            current_source_trust_result=current_source,
            expected_conflict_precedence_result=expected_conflict,
            current_conflict_precedence_result=current_conflict,
            expected_trace_payload=expected_trace,
            current_trace_payload=current_trace,
            risk_classification=risk_classification,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            source_label=source_label,
            metadata=metadata,
        )
        input_id = input_hash
        if self.input_id not in ("", input_id):
            raise PathGovernanceValidationError(
                "input_id does not match path violation trace input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match path violation trace input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "expected_path_resolver_result", expected_path)
        object.__setattr__(self, "current_path_resolver_result", current_path)
        object.__setattr__(self, "expected_source_trust_result", expected_source)
        object.__setattr__(self, "current_source_trust_result", current_source)
        object.__setattr__(self, "expected_conflict_precedence_result", expected_conflict)
        object.__setattr__(self, "current_conflict_precedence_result", current_conflict)
        object.__setattr__(self, "expected_trace_payload", expected_trace)
        object.__setattr__(self, "current_trace_payload", current_trace)
        object.__setattr__(self, "risk_classification", risk_classification)
        object.__setattr__(self, "provenance_binding", provenance_binding)
        object.__setattr__(self, "authority_scope", authority_scope)
        object.__setattr__(self, "untrusted_boundary", untrusted_boundary)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "input_hash", input_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _input_payload(
            expected_path_resolver_result=self.expected_path_resolver_result,
            current_path_resolver_result=self.current_path_resolver_result,
            expected_source_trust_result=self.expected_source_trust_result,
            current_source_trust_result=self.current_source_trust_result,
            expected_conflict_precedence_result=self.expected_conflict_precedence_result,
            current_conflict_precedence_result=self.current_conflict_precedence_result,
            expected_trace_payload=self.expected_trace_payload,
            current_trace_payload=self.current_trace_payload,
            risk_classification=self.risk_classification,
            provenance_binding=self.provenance_binding,
            authority_scope=self.authority_scope,
            untrusted_boundary=self.untrusted_boundary,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["input_hash"] = self.input_hash
        payload["input_id"] = self.input_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathViolationTraceInput:
        validate_known_fields(
            data,
            PATH_VIOLATION_TRACE_INPUT_KNOWN_FIELDS,
            label="path_violation_trace_input",
        )
        return cls(
            expected_path_resolver_result=data.get("expected_path_resolver_result"),
            current_path_resolver_result=data.get("current_path_resolver_result"),
            expected_source_trust_result=data.get("expected_source_trust_result"),
            current_source_trust_result=data.get("current_source_trust_result"),
            expected_conflict_precedence_result=data.get(
                "expected_conflict_precedence_result",
            ),
            current_conflict_precedence_result=data.get(
                "current_conflict_precedence_result",
            ),
            expected_trace_payload=data.get("expected_trace_payload"),
            current_trace_payload=data.get("current_trace_payload"),
            risk_classification=data.get("risk_classification"),
            provenance_binding=data.get("provenance_binding"),
            authority_scope=data.get("authority_scope"),
            untrusted_boundary=data.get("untrusted_boundary"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            input_id=data.get("input_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


def _drift_signal_hash_payload(
    *,
    event_kind: PathViolationTraceEventKind,
    severity: PathViolationSeverity,
    expected_ref: str,
    current_ref: str,
    reason: PathViolationTraceReason,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "current_ref": current_ref,
        "event_kind": event_kind.value,
        "expected_ref": expected_ref,
        "metadata": _sorted_metadata_dict(metadata),
        "reason": reason.value,
        "severity": severity.value,
        "source_label": source_label.value,
    }


def compute_path_source_drift_signal_id(
    *,
    event_kind: PathViolationTraceEventKind,
    severity: PathViolationSeverity,
    expected_ref: str,
    current_ref: str,
    reason: PathViolationTraceReason,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path source drift signal identifier."""
    return stable_hash(_drift_signal_hash_payload(
        event_kind=event_kind,
        severity=severity,
        expected_ref=expected_ref,
        current_ref=current_ref,
        reason=reason,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathSourceDriftSignal:
    """Observational drift signal; not correction or enforcement."""

    event_kind: PathViolationTraceEventKind
    severity: PathViolationSeverity
    expected_ref: str
    current_ref: str
    reason: PathViolationTraceReason
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    drift_signal_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        event_kind = _parse_event_kind(self.event_kind)
        severity = _parse_severity(self.severity)
        expected_ref = str(self.expected_ref)
        current_ref = str(self.current_ref)
        if isinstance(self.reason, PathViolationTraceReason):
            reason = self.reason
        elif isinstance(self.reason, str):
            reason = PathViolationTraceReason(self.reason)
        else:
            raise PathGovernanceValidationError(
                "reason must be a PathViolationTraceReason or str",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="reason",
            )
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        drift_signal_id = compute_path_source_drift_signal_id(
            event_kind=event_kind,
            severity=severity,
            expected_ref=expected_ref,
            current_ref=current_ref,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.drift_signal_id not in ("", drift_signal_id):
            raise PathGovernanceValidationError(
                "drift_signal_id does not match drift signal content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="drift_signal_id",
            )
        object.__setattr__(self, "event_kind", event_kind)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "expected_ref", expected_ref)
        object.__setattr__(self, "current_ref", current_ref)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "drift_signal_id", drift_signal_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _drift_signal_hash_payload(
            event_kind=self.event_kind,
            severity=self.severity,
            expected_ref=self.expected_ref,
            current_ref=self.current_ref,
            reason=self.reason,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["drift_signal_id"] = self.drift_signal_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathSourceDriftSignal:
        validate_known_fields(
            data,
            PATH_SOURCE_DRIFT_SIGNAL_KNOWN_FIELDS,
            label="path_source_drift_signal",
        )
        return cls(
            event_kind=data["event_kind"],
            severity=data["severity"],
            expected_ref=data.get("expected_ref", ""),
            current_ref=data.get("current_ref", ""),
            reason=data["reason"],
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            drift_signal_id=data.get("drift_signal_id", ""),
            metadata=data.get("metadata", {}),
        )


def detect_path_source_drift_signals(
    *,
    violation_input: PathViolationTraceInput | None = None,
    expected_path_resolver_result: PathGovernanceResolverResult | None = None,
    current_path_resolver_result: PathGovernanceResolverResult | None = None,
    expected_source_trust_result: SourceTrustResolverResult | None = None,
    current_source_trust_result: SourceTrustResolverResult | None = None,
    expected_conflict_precedence_result: ConflictPrecedenceResult | None = None,
    current_conflict_precedence_result: ConflictPrecedenceResult | None = None,
    expected_trace_payload: PathResolutionTracePayload | None = None,
    current_trace_payload: PathResolutionTracePayload | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[PathSourceDriftSignal, ...]:
    """Detect observational drift signals without correction or enforcement."""
    if violation_input is None:
        violation_input = PathViolationTraceInput(
            expected_path_resolver_result=expected_path_resolver_result,
            current_path_resolver_result=current_path_resolver_result,
            expected_source_trust_result=expected_source_trust_result,
            current_source_trust_result=current_source_trust_result,
            expected_conflict_precedence_result=expected_conflict_precedence_result,
            current_conflict_precedence_result=current_conflict_precedence_result,
            expected_trace_payload=expected_trace_payload,
            current_trace_payload=current_trace_payload,
            risk_classification=risk_classification,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            source_label=source_label,
            metadata=metadata or {},
        )
    label = violation_input.source_label
    meta = dict(violation_input.metadata)
    signals: list[PathSourceDriftSignal] = []

    exp_path = violation_input.expected_path_resolver_result
    cur_path = violation_input.current_path_resolver_result
    if exp_path is not None and cur_path is not None:
        exp_ref = _path_result_ref(exp_path)
        cur_ref = _path_result_ref(cur_path)
        if exp_ref != cur_ref or exp_path.shadow_decision != cur_path.shadow_decision:
            severity = PathViolationSeverity.HIGH
            if cur_path.shadow_decision == PathGovernanceShadowDecision.WOULD_DENY:
                severity = PathViolationSeverity.HIGH
            elif exp_path.shadow_decision != cur_path.shadow_decision:
                severity = PathViolationSeverity.MEDIUM
            else:
                severity = PathViolationSeverity.MEDIUM
            event_kind = PathViolationTraceEventKind.PATH_BOUNDARY_VIOLATION_CANDIDATE
            signals.append(PathSourceDriftSignal(
                event_kind=event_kind,
                severity=severity,
                expected_ref=exp_ref,
                current_ref=cur_ref,
                reason=PathViolationTraceReason.PATH_BOUNDARY_CHANGED,
                source_label=label,
                metadata=meta,
            ))

    exp_source = violation_input.expected_source_trust_result
    cur_source = violation_input.current_source_trust_result
    if exp_source is not None and cur_source is not None:
        exp_ref = _source_result_ref(exp_source)
        cur_ref = _source_result_ref(cur_source)
        if exp_ref != cur_ref or exp_source.shadow_decision != cur_source.shadow_decision:
            signals.append(PathSourceDriftSignal(
                event_kind=PathViolationTraceEventKind.SOURCE_TRUST_DRIFT,
                severity=PathViolationSeverity.MEDIUM,
                expected_ref=exp_ref,
                current_ref=cur_ref,
                reason=PathViolationTraceReason.SOURCE_TRUST_CHANGED,
                source_label=label,
                metadata=meta,
            ))

    exp_conflict = violation_input.expected_conflict_precedence_result
    cur_conflict = violation_input.current_conflict_precedence_result
    if exp_conflict is not None and cur_conflict is not None:
        exp_ref = _conflict_result_ref(exp_conflict)
        cur_ref = _conflict_result_ref(cur_conflict)
        if (
            exp_ref != cur_ref
            or exp_conflict.recommended_shadow_decision
            != cur_conflict.recommended_shadow_decision
        ):
            signals.append(PathSourceDriftSignal(
                event_kind=PathViolationTraceEventKind.CONFLICT_PRECEDENCE_DRIFT,
                severity=PathViolationSeverity.MEDIUM,
                expected_ref=exp_ref,
                current_ref=cur_ref,
                reason=PathViolationTraceReason.CONFLICT_PRECEDENCE_CHANGED,
                source_label=label,
                metadata=meta,
            ))

    exp_trace = violation_input.expected_trace_payload
    cur_trace = violation_input.current_trace_payload
    if exp_trace is not None and cur_trace is not None:
        exp_ref = _trace_payload_ref(exp_trace)
        cur_ref = _trace_payload_ref(cur_trace)
        if exp_ref != cur_ref:
            signals.append(PathSourceDriftSignal(
                event_kind=PathViolationTraceEventKind.TRACE_PAYLOAD_MISMATCH,
                severity=PathViolationSeverity.MEDIUM,
                expected_ref=exp_ref,
                current_ref=cur_ref,
                reason=PathViolationTraceReason.EXPECTED_TRACE_PAYLOAD_PRESENT,
                source_label=label,
                metadata=meta,
            ))

    risk = violation_input.risk_classification
    current_risk_ref = _risk_ref(risk)
    if exp_trace is not None and exp_trace.risk_classification_ref:
        if current_risk_ref != exp_trace.risk_classification_ref:
            severity = PathViolationSeverity.MEDIUM
            if risk is not None:
                severity = _risk_level_to_severity(risk.risk_level)
            signals.append(PathSourceDriftSignal(
                event_kind=PathViolationTraceEventKind.RISK_CLASSIFICATION_DRIFT,
                severity=severity,
                expected_ref=exp_trace.risk_classification_ref,
                current_ref=current_risk_ref,
                reason=PathViolationTraceReason.RISK_CLASSIFICATION_CHANGED,
                source_label=label,
                metadata=meta,
            ))

    if exp_trace is not None and exp_trace.provenance_binding_ref:
        current_prov_ref = _provenance_ref(violation_input.provenance_binding)
        if not current_prov_ref:
            signals.append(PathSourceDriftSignal(
                event_kind=PathViolationTraceEventKind.PROVENANCE_EXPECTATION_MISSING,
                severity=PathViolationSeverity.MEDIUM,
                expected_ref=exp_trace.provenance_binding_ref,
                current_ref=current_prov_ref,
                reason=PathViolationTraceReason.PROVENANCE_MISSING,
                source_label=label,
                metadata=meta,
            ))

    if exp_trace is not None and exp_trace.authority_scope_ref:
        current_auth_ref = _authority_ref(violation_input.authority_scope)
        if not current_auth_ref:
            signals.append(PathSourceDriftSignal(
                event_kind=PathViolationTraceEventKind.AUTHORITY_SCOPE_MISSING_DRIFT,
                severity=PathViolationSeverity.LOW,
                expected_ref=exp_trace.authority_scope_ref,
                current_ref=current_auth_ref,
                reason=PathViolationTraceReason.AUTHORITY_SCOPE_MISSING,
                source_label=label,
                metadata=meta,
            ))

    current_boundary_ref = _boundary_ref(violation_input.untrusted_boundary)
    expected_boundary_ref = (
        exp_trace.boundary_ref if exp_trace is not None else ""
    )
    if expected_boundary_ref and expected_boundary_ref != current_boundary_ref:
        signals.append(PathSourceDriftSignal(
            event_kind=PathViolationTraceEventKind.UNTRUSTED_BOUNDARY_DRIFT,
            severity=PathViolationSeverity.LOW,
            expected_ref=expected_boundary_ref,
            current_ref=current_boundary_ref,
            reason=PathViolationTraceReason.BOUNDARY_CONTEXT_CHANGED,
            source_label=label,
            metadata=meta,
        ))

    signals.sort(key=lambda signal: (signal.event_kind.value, signal.drift_signal_id))
    return tuple(signals)


def _collect_drift_reasons(
    *,
    violation_input: PathViolationTraceInput,
    drift_signals: tuple[PathSourceDriftSignal, ...],
) -> tuple[PathViolationTraceReason, ...]:
    reasons: set[PathViolationTraceReason] = {
        PathViolationTraceReason.SHADOW_ONLY_CONTEXT,
        PathViolationTraceReason.ENFORCEMENT_UNAVAILABLE,
        PathViolationTraceReason.LEDGER_UNAVAILABLE,
        PathViolationTraceReason.TRACE_SPINE_UNAVAILABLE,
    }
    if violation_input.expected_path_resolver_result is not None:
        reasons.add(PathViolationTraceReason.PATH_RESOLVER_RESULT_PRESENT)
    if violation_input.current_path_resolver_result is not None:
        reasons.add(PathViolationTraceReason.PATH_RESOLVER_RESULT_PRESENT)
    if violation_input.expected_source_trust_result is not None:
        reasons.add(PathViolationTraceReason.SOURCE_TRUST_RESULT_PRESENT)
    if violation_input.current_source_trust_result is not None:
        reasons.add(PathViolationTraceReason.SOURCE_TRUST_RESULT_PRESENT)
    if violation_input.expected_conflict_precedence_result is not None:
        reasons.add(PathViolationTraceReason.CONFLICT_PRECEDENCE_PRESENT)
    if violation_input.current_conflict_precedence_result is not None:
        reasons.add(PathViolationTraceReason.CONFLICT_PRECEDENCE_PRESENT)
    if violation_input.risk_classification is not None:
        reasons.add(PathViolationTraceReason.RISK_CLASSIFICATION_PRESENT)
    if violation_input.expected_trace_payload is not None:
        reasons.add(PathViolationTraceReason.EXPECTED_TRACE_PAYLOAD_PRESENT)
    if violation_input.current_trace_payload is not None:
        reasons.add(PathViolationTraceReason.CURRENT_TRACE_PAYLOAD_PRESENT)
    for signal in drift_signals:
        reasons.add(signal.reason)
    return tuple(sorted(reasons, key=lambda reason: reason.value))


def _build_expected_refs(violation_input: PathViolationTraceInput) -> dict[str, str]:
    refs: dict[str, str] = {}
    if violation_input.expected_path_resolver_result is not None:
        refs["path_resolver_result"] = _path_result_ref(
            violation_input.expected_path_resolver_result,
        )
    if violation_input.expected_source_trust_result is not None:
        refs["source_trust_result"] = _source_result_ref(
            violation_input.expected_source_trust_result,
        )
    if violation_input.expected_conflict_precedence_result is not None:
        refs["conflict_precedence_result"] = _conflict_result_ref(
            violation_input.expected_conflict_precedence_result,
        )
    if violation_input.expected_trace_payload is not None:
        refs["trace_payload"] = _trace_payload_ref(violation_input.expected_trace_payload)
    if violation_input.risk_classification is not None:
        refs["risk_classification"] = _risk_ref(violation_input.risk_classification)
    if violation_input.provenance_binding is not None:
        refs["provenance_binding"] = _provenance_ref(violation_input.provenance_binding)
    if violation_input.authority_scope is not None:
        refs["authority_scope"] = _authority_ref(violation_input.authority_scope)
    if violation_input.untrusted_boundary is not None:
        refs["untrusted_boundary"] = _boundary_ref(violation_input.untrusted_boundary)
    return refs


def _build_current_refs(violation_input: PathViolationTraceInput) -> dict[str, str]:
    refs: dict[str, str] = {}
    if violation_input.current_path_resolver_result is not None:
        refs["path_resolver_result"] = _path_result_ref(
            violation_input.current_path_resolver_result,
        )
    if violation_input.current_source_trust_result is not None:
        refs["source_trust_result"] = _source_result_ref(
            violation_input.current_source_trust_result,
        )
    if violation_input.current_conflict_precedence_result is not None:
        refs["conflict_precedence_result"] = _conflict_result_ref(
            violation_input.current_conflict_precedence_result,
        )
    if violation_input.current_trace_payload is not None:
        refs["trace_payload"] = _trace_payload_ref(violation_input.current_trace_payload)
    if violation_input.risk_classification is not None:
        refs["risk_classification"] = _risk_ref(violation_input.risk_classification)
    if violation_input.provenance_binding is not None:
        refs["provenance_binding"] = _provenance_ref(violation_input.provenance_binding)
    if violation_input.authority_scope is not None:
        refs["authority_scope"] = _authority_ref(violation_input.authority_scope)
    if violation_input.untrusted_boundary is not None:
        refs["untrusted_boundary"] = _boundary_ref(violation_input.untrusted_boundary)
    return refs


def _primary_event_and_severity(
    drift_signals: tuple[PathSourceDriftSignal, ...],
) -> tuple[PathViolationTraceEventKind, PathViolationSeverity]:
    if not drift_signals:
        return (
            PathViolationTraceEventKind.VIOLATION_TRACE_PAYLOAD_CREATED,
            PathViolationSeverity.NONE,
        )
    best = max(
        drift_signals,
        key=lambda signal: (
            _SEVERITY_RANK.get(signal.severity, 0),
            signal.event_kind.value,
        ),
    )
    return best.event_kind, best.severity


def _build_violation_summary(
    *,
    drift_signals: tuple[PathSourceDriftSignal, ...],
) -> Mapping[str, Any]:
    summary: dict[str, Any] = {
        "drift_candidate_count": len(drift_signals),
        "enforced": False,
        "shadow_only": True,
        "summary_text": (
            "Expected/current governance context mismatch candidates observed"
            if drift_signals
            else "No drift candidates detected; violation trace payload created"
        ),
    }
    if drift_signals:
        summary["drift_event_kinds"] = sorted(
            {signal.event_kind.value for signal in drift_signals},
        )
    return _validate_violation_summary(summary)


def _payload_hash_payload(
    *,
    event_kind: PathViolationTraceEventKind,
    violation_subject_ref: str,
    severity: PathViolationSeverity,
    violation_summary: Mapping[str, Any],
    expected_refs: Mapping[str, str],
    current_refs: Mapping[str, str],
    drift_reasons: tuple[PathViolationTraceReason, ...],
    source_label: ProjectionSourceLabel,
    schema_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "created_by_task": created_by_task,
        "current_refs": dict(sorted(current_refs.items())),
        "drift_reasons": [reason.value for reason in drift_reasons],
        "event_kind": event_kind.value,
        "expected_refs": dict(sorted(expected_refs.items())),
        "metadata": _sorted_metadata_dict(metadata),
        "schema_version": schema_version,
        "severity": severity.value,
        "source_label": source_label.value,
        "violation_subject_ref": violation_subject_ref,
        "violation_summary": dict(violation_summary),
    }


def compute_path_violation_trace_payload_id(
    *,
    event_kind: PathViolationTraceEventKind,
    violation_subject_ref: str,
    severity: PathViolationSeverity,
    violation_summary: Mapping[str, Any],
    expected_refs: Mapping[str, str],
    current_refs: Mapping[str, str],
    drift_reasons: tuple[PathViolationTraceReason, ...],
    source_label: ProjectionSourceLabel,
    schema_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path violation trace payload identifier."""
    return stable_hash(_payload_hash_payload(
        event_kind=event_kind,
        violation_subject_ref=violation_subject_ref,
        severity=severity,
        violation_summary=violation_summary,
        expected_refs=expected_refs,
        current_refs=current_refs,
        drift_reasons=drift_reasons,
        source_label=source_label,
        schema_version=schema_version,
        created_by_task=created_by_task,
        metadata=metadata,
    ))


def compute_path_violation_trace_payload_hash(
    *,
    payload_id: str,
    event_kind: PathViolationTraceEventKind,
    violation_subject_ref: str,
    severity: PathViolationSeverity,
    violation_summary: Mapping[str, Any],
    expected_refs: Mapping[str, str],
    current_refs: Mapping[str, str],
    drift_reasons: tuple[PathViolationTraceReason, ...],
    source_label: ProjectionSourceLabel,
    schema_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path violation trace payload hash."""
    payload = _payload_hash_payload(
        event_kind=event_kind,
        violation_subject_ref=violation_subject_ref,
        severity=severity,
        violation_summary=violation_summary,
        expected_refs=expected_refs,
        current_refs=current_refs,
        drift_reasons=drift_reasons,
        source_label=source_label,
        schema_version=schema_version,
        created_by_task=created_by_task,
        metadata=metadata,
    )
    payload["payload_id"] = payload_id
    return stable_hash(payload)


@dataclass(frozen=True)
class PathViolationTracePayload:
    """Deterministic path violation trace payload; observability only."""

    event_kind: PathViolationTraceEventKind = (
        PathViolationTraceEventKind.VIOLATION_TRACE_PAYLOAD_CREATED
    )
    violation_subject_ref: str = ""
    severity: PathViolationSeverity = PathViolationSeverity.NONE
    violation_summary: Mapping[str, Any] = field(default_factory=dict)
    expected_refs: Mapping[str, str] = field(default_factory=dict)
    current_refs: Mapping[str, str] = field(default_factory=dict)
    drift_reasons: tuple[PathViolationTraceReason, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    payload_id: str = ""
    payload_hash: str = ""
    schema_version: str = PATH_VIOLATION_TRACE_PAYLOAD_SCHEMA
    created_by_task: str = PATH_VIOLATION_TRACE_TASK_ID
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        event_kind = _parse_event_kind(self.event_kind)
        violation_subject_ref = str(self.violation_subject_ref)
        severity = _parse_severity(self.severity)
        violation_summary = _validate_violation_summary(self.violation_summary)
        if not isinstance(self.expected_refs, MappingABC):
            raise PathGovernanceValidationError(
                "expected_refs must be a mapping",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="expected_refs",
            )
        if not isinstance(self.current_refs, MappingABC):
            raise PathGovernanceValidationError(
                "current_refs must be a mapping",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="current_refs",
            )
        expected_refs = MappingProxyType(dict(sorted(self.expected_refs.items())))
        current_refs = MappingProxyType(dict(sorted(self.current_refs.items())))
        drift_reasons = _parse_drift_reasons(self.drift_reasons)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        created_by_task = _required_string(self.created_by_task, field_name="created_by_task")
        payload_id = compute_path_violation_trace_payload_id(
            event_kind=event_kind,
            violation_subject_ref=violation_subject_ref,
            severity=severity,
            violation_summary=violation_summary,
            expected_refs=expected_refs,
            current_refs=current_refs,
            drift_reasons=drift_reasons,
            source_label=source_label,
            schema_version=schema_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.payload_id not in ("", payload_id):
            raise PathGovernanceValidationError(
                "payload_id does not match path violation trace payload content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload_id",
            )
        payload_hash = compute_path_violation_trace_payload_hash(
            payload_id=payload_id,
            event_kind=event_kind,
            violation_subject_ref=violation_subject_ref,
            severity=severity,
            violation_summary=violation_summary,
            expected_refs=expected_refs,
            current_refs=current_refs,
            drift_reasons=drift_reasons,
            source_label=source_label,
            schema_version=schema_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.payload_hash not in ("", payload_hash):
            raise PathGovernanceValidationError(
                "payload_hash does not match path violation trace payload content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload_hash",
            )
        object.__setattr__(self, "event_kind", event_kind)
        object.__setattr__(self, "violation_subject_ref", violation_subject_ref)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "violation_summary", violation_summary)
        object.__setattr__(self, "expected_refs", expected_refs)
        object.__setattr__(self, "current_refs", current_refs)
        object.__setattr__(self, "drift_reasons", drift_reasons)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "payload_id", payload_id)
        object.__setattr__(self, "payload_hash", payload_hash)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "created_by_task", created_by_task)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _payload_hash_payload(
            event_kind=self.event_kind,
            violation_subject_ref=self.violation_subject_ref,
            severity=self.severity,
            violation_summary=self.violation_summary,
            expected_refs=self.expected_refs,
            current_refs=self.current_refs,
            drift_reasons=self.drift_reasons,
            source_label=self.source_label,
            schema_version=self.schema_version,
            created_by_task=self.created_by_task,
            metadata=self.metadata,
        )
        payload["payload_id"] = self.payload_id
        payload["payload_hash"] = self.payload_hash
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathViolationTracePayload:
        validate_known_fields(
            data,
            PATH_VIOLATION_TRACE_PAYLOAD_KNOWN_FIELDS,
            label="path_violation_trace_payload",
        )
        return cls(
            event_kind=data.get(
                "event_kind",
                PathViolationTraceEventKind.VIOLATION_TRACE_PAYLOAD_CREATED,
            ),
            violation_subject_ref=data.get("violation_subject_ref", ""),
            severity=data.get("severity", PathViolationSeverity.NONE),
            violation_summary=data.get("violation_summary", {}),
            expected_refs=data.get("expected_refs", {}),
            current_refs=data.get("current_refs", {}),
            drift_reasons=tuple(data.get("drift_reasons", ())),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            payload_id=data.get("payload_id", ""),
            payload_hash=data.get("payload_hash", ""),
            schema_version=data.get("schema_version", PATH_VIOLATION_TRACE_PAYLOAD_SCHEMA),
            created_by_task=data.get("created_by_task", PATH_VIOLATION_TRACE_TASK_ID),
            metadata=data.get("metadata", {}),
        )


def _hook_hash_payload(
    *,
    input_id: str,
    payload_hash: str,
    hook_mode: PathViolationTraceHookMode,
    disposition: PathViolationTraceDisposition,
    sink_name: str | None,
    trace_written: bool,
    ledger_written: bool,
    runtime_mutated: bool,
    enforcement_triggered: bool,
    source_label: ProjectionSourceLabel,
    hook_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "created_by_task": created_by_task,
        "disposition": disposition.value,
        "enforcement_triggered": enforcement_triggered,
        "hook_mode": hook_mode.value,
        "hook_version": hook_version,
        "input_id": input_id,
        "ledger_written": ledger_written,
        "metadata": _sorted_metadata_dict(metadata),
        "payload_hash": payload_hash,
        "runtime_mutated": runtime_mutated,
        "sink_name": sink_name or "",
        "source_label": source_label.value,
        "trace_written": trace_written,
    }


def compute_path_violation_trace_hook_id(
    *,
    input_id: str,
    payload_hash: str,
    hook_mode: PathViolationTraceHookMode,
    disposition: PathViolationTraceDisposition,
    sink_name: str | None,
    hook_version: str,
) -> str:
    """Compute deterministic path violation trace hook identifier."""
    return stable_hash({
        "disposition": disposition.value,
        "hook_mode": hook_mode.value,
        "hook_version": hook_version,
        "input_id": input_id,
        "payload_hash": payload_hash,
        "sink_name": sink_name or "",
    })


def compute_path_violation_trace_hook_hash(
    *,
    hook_id: str,
    input_id: str,
    payload_hash: str,
    hook_mode: PathViolationTraceHookMode,
    disposition: PathViolationTraceDisposition,
    sink_name: str | None,
    trace_written: bool,
    ledger_written: bool,
    runtime_mutated: bool,
    enforcement_triggered: bool,
    source_label: ProjectionSourceLabel,
    hook_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path violation trace hook hash."""
    payload = _hook_hash_payload(
        input_id=input_id,
        payload_hash=payload_hash,
        hook_mode=hook_mode,
        disposition=disposition,
        sink_name=sink_name,
        trace_written=trace_written,
        ledger_written=ledger_written,
        runtime_mutated=runtime_mutated,
        enforcement_triggered=enforcement_triggered,
        source_label=source_label,
        hook_version=hook_version,
        created_by_task=created_by_task,
        metadata=metadata,
    )
    payload["hook_id"] = hook_id
    return stable_hash(payload)


@dataclass(frozen=True)
class PathViolationTraceHookResult:
    """Path violation trace hook result; observability only, not enforcement."""

    input_id: str
    payload: PathViolationTracePayload
    hook_mode: PathViolationTraceHookMode = PathViolationTraceHookMode.PAYLOAD_ONLY
    disposition: PathViolationTraceDisposition = (
        PathViolationTraceDisposition.PAYLOAD_CREATED
    )
    sink_name: str | None = None
    trace_written: bool = False
    ledger_written: bool = False
    runtime_mutated: bool = False
    enforcement_triggered: bool = False
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    hook_id: str = ""
    hook_hash: str = ""
    created_by_task: str = PATH_VIOLATION_TRACE_TASK_ID
    hook_version: str = PATH_VIOLATION_TRACE_HOOK_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ledger_written is not False:
            raise PathGovernanceValidationError(
                "ledger_written must be False in P1.7.14",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="ledger_written",
            )
        if self.runtime_mutated is not False:
            raise PathGovernanceValidationError(
                "runtime_mutated must be False in P1.7.14",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="runtime_mutated",
            )
        if self.enforcement_triggered is not False:
            raise PathGovernanceValidationError(
                "enforcement_triggered must be False in P1.7.14",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="enforcement_triggered",
            )
        input_id = _required_string(self.input_id, field_name="input_id")
        if not isinstance(self.payload, PathViolationTracePayload):
            raise PathGovernanceValidationError(
                "payload must be a PathViolationTracePayload",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload",
            )
        hook_mode = _parse_hook_mode(self.hook_mode)
        disposition = _parse_disposition(self.disposition)
        sink_name = None if self.sink_name is None else str(self.sink_name)
        trace_written = bool(self.trace_written)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        hook_version = _required_string(self.hook_version, field_name="hook_version")
        created_by_task = _required_string(self.created_by_task, field_name="created_by_task")
        hook_id = compute_path_violation_trace_hook_id(
            input_id=input_id,
            payload_hash=self.payload.payload_hash,
            hook_mode=hook_mode,
            disposition=disposition,
            sink_name=sink_name,
            hook_version=hook_version,
        )
        if self.hook_id not in ("", hook_id):
            raise PathGovernanceValidationError(
                "hook_id does not match path violation trace hook content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="hook_id",
            )
        hook_hash = compute_path_violation_trace_hook_hash(
            hook_id=hook_id,
            input_id=input_id,
            payload_hash=self.payload.payload_hash,
            hook_mode=hook_mode,
            disposition=disposition,
            sink_name=sink_name,
            trace_written=trace_written,
            ledger_written=False,
            runtime_mutated=False,
            enforcement_triggered=False,
            source_label=source_label,
            hook_version=hook_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.hook_hash not in ("", hook_hash):
            raise PathGovernanceValidationError(
                "hook_hash does not match path violation trace hook content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="hook_hash",
            )
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "hook_mode", hook_mode)
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "sink_name", sink_name)
        object.__setattr__(self, "trace_written", trace_written)
        object.__setattr__(self, "ledger_written", False)
        object.__setattr__(self, "runtime_mutated", False)
        object.__setattr__(self, "enforcement_triggered", False)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "hook_id", hook_id)
        object.__setattr__(self, "hook_hash", hook_hash)
        object.__setattr__(self, "hook_version", hook_version)
        object.__setattr__(self, "created_by_task", created_by_task)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _hook_hash_payload(
            input_id=self.input_id,
            payload_hash=self.payload.payload_hash,
            hook_mode=self.hook_mode,
            disposition=self.disposition,
            sink_name=self.sink_name,
            trace_written=self.trace_written,
            ledger_written=self.ledger_written,
            runtime_mutated=self.runtime_mutated,
            enforcement_triggered=self.enforcement_triggered,
            source_label=self.source_label,
            hook_version=self.hook_version,
            created_by_task=self.created_by_task,
            metadata=self.metadata,
        )
        payload["hook_id"] = self.hook_id
        payload["hook_hash"] = self.hook_hash
        payload["payload"] = self.payload.to_canonical_dict()
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathViolationTraceHookResult:
        validate_known_fields(
            data,
            PATH_VIOLATION_TRACE_HOOK_RESULT_KNOWN_FIELDS,
            label="path_violation_trace_hook_result",
        )
        payload_raw = data["payload"]
        if isinstance(payload_raw, PathViolationTracePayload):
            payload = payload_raw
        elif isinstance(payload_raw, MappingABC):
            payload = PathViolationTracePayload.from_dict(payload_raw)
        else:
            raise PathGovernanceValidationError(
                "payload must be a PathViolationTracePayload or mapping",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload",
            )
        return cls(
            input_id=data["input_id"],
            payload=payload,
            hook_mode=data.get("hook_mode", PathViolationTraceHookMode.PAYLOAD_ONLY),
            disposition=data.get(
                "disposition",
                PathViolationTraceDisposition.PAYLOAD_CREATED,
            ),
            sink_name=data.get("sink_name"),
            trace_written=data.get("trace_written", False),
            ledger_written=data.get("ledger_written", False),
            runtime_mutated=data.get("runtime_mutated", False),
            enforcement_triggered=data.get("enforcement_triggered", False),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            hook_id=data.get("hook_id", ""),
            hook_hash=data.get("hook_hash", ""),
            created_by_task=data.get("created_by_task", PATH_VIOLATION_TRACE_TASK_ID),
            hook_version=data.get("hook_version", PATH_VIOLATION_TRACE_HOOK_VERSION),
            metadata=data.get("metadata", {}),
        )


def build_path_violation_trace_payload(
    *,
    violation_input: PathViolationTraceInput | None = None,
    expected_path_resolver_result: PathGovernanceResolverResult | None = None,
    current_path_resolver_result: PathGovernanceResolverResult | None = None,
    expected_source_trust_result: SourceTrustResolverResult | None = None,
    current_source_trust_result: SourceTrustResolverResult | None = None,
    expected_conflict_precedence_result: ConflictPrecedenceResult | None = None,
    current_conflict_precedence_result: ConflictPrecedenceResult | None = None,
    expected_trace_payload: PathResolutionTracePayload | None = None,
    current_trace_payload: PathResolutionTracePayload | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    violation_subject_ref: str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathViolationTracePayload:
    """Build deterministic path violation trace payload without writing trace."""
    if violation_input is None:
        violation_input = PathViolationTraceInput(
            expected_path_resolver_result=expected_path_resolver_result,
            current_path_resolver_result=current_path_resolver_result,
            expected_source_trust_result=expected_source_trust_result,
            current_source_trust_result=current_source_trust_result,
            expected_conflict_precedence_result=expected_conflict_precedence_result,
            current_conflict_precedence_result=current_conflict_precedence_result,
            expected_trace_payload=expected_trace_payload,
            current_trace_payload=current_trace_payload,
            risk_classification=risk_classification,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            source_label=source_label,
            metadata=metadata or {},
        )
    drift_signals = detect_path_source_drift_signals(violation_input=violation_input)
    event_kind, severity = _primary_event_and_severity(drift_signals)
    subject_ref = violation_subject_ref or violation_input.input_id
    return PathViolationTracePayload(
        event_kind=event_kind,
        violation_subject_ref=subject_ref,
        severity=severity,
        violation_summary=_build_violation_summary(drift_signals=drift_signals),
        expected_refs=_build_expected_refs(violation_input),
        current_refs=_build_current_refs(violation_input),
        drift_reasons=_collect_drift_reasons(
            violation_input=violation_input,
            drift_signals=drift_signals,
        ),
        source_label=violation_input.source_label,
        metadata=violation_input.metadata,
    )


def record_path_violation_trace_hook(
    *,
    violation_input: PathViolationTraceInput | None = None,
    payload: PathViolationTracePayload | None = None,
    expected_path_resolver_result: PathGovernanceResolverResult | None = None,
    current_path_resolver_result: PathGovernanceResolverResult | None = None,
    expected_source_trust_result: SourceTrustResolverResult | None = None,
    current_source_trust_result: SourceTrustResolverResult | None = None,
    expected_conflict_precedence_result: ConflictPrecedenceResult | None = None,
    current_conflict_precedence_result: ConflictPrecedenceResult | None = None,
    expected_trace_payload: PathResolutionTracePayload | None = None,
    current_trace_payload: PathResolutionTracePayload | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    violation_subject_ref: str | None = None,
    sink: Callable[[PathViolationTracePayload], Any] | None = None,
    sink_name: str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathViolationTraceHookResult:
    """Record path violation trace hook result without Ledger or runtime mutation."""
    if violation_input is None and payload is None:
        violation_input = PathViolationTraceInput(
            expected_path_resolver_result=expected_path_resolver_result,
            current_path_resolver_result=current_path_resolver_result,
            expected_source_trust_result=expected_source_trust_result,
            current_source_trust_result=current_source_trust_result,
            expected_conflict_precedence_result=expected_conflict_precedence_result,
            current_conflict_precedence_result=current_conflict_precedence_result,
            expected_trace_payload=expected_trace_payload,
            current_trace_payload=current_trace_payload,
            risk_classification=risk_classification,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            source_label=source_label,
            metadata=metadata or {},
        )
    if payload is None:
        payload = build_path_violation_trace_payload(
            violation_input=violation_input,
            violation_subject_ref=violation_subject_ref,
            source_label=source_label,
            metadata=metadata,
        )
    input_id = (
        violation_input.input_id
        if violation_input is not None
        else payload.violation_subject_ref
    )
    if sink is None:
        return PathViolationTraceHookResult(
            input_id=input_id,
            payload=payload,
            hook_mode=PathViolationTraceHookMode.PAYLOAD_ONLY,
            disposition=PathViolationTraceDisposition.PAYLOAD_CREATED,
            sink_name=None,
            trace_written=False,
            ledger_written=False,
            runtime_mutated=False,
            enforcement_triggered=False,
            source_label=payload.source_label,
            metadata=metadata or {},
        )
    try:
        sink(payload)
    except Exception:
        return PathViolationTraceHookResult(
            input_id=input_id,
            payload=payload,
            hook_mode=PathViolationTraceHookMode.ERROR,
            disposition=PathViolationTraceDisposition.ERROR,
            sink_name=sink_name,
            trace_written=False,
            ledger_written=False,
            runtime_mutated=False,
            enforcement_triggered=False,
            source_label=payload.source_label,
            metadata=metadata or {},
        )
    return PathViolationTraceHookResult(
        input_id=input_id,
        payload=payload,
        hook_mode=PathViolationTraceHookMode.INJECTED_SINK,
        disposition=PathViolationTraceDisposition.RECORDED_TO_INJECTED_SINK,
        sink_name=sink_name,
        trace_written=True,
        ledger_written=False,
        runtime_mutated=False,
        enforcement_triggered=False,
        source_label=payload.source_label,
        metadata=metadata or {},
    )
