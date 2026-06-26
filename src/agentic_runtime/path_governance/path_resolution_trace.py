"""Path resolution trace hook (P1.7.13).

Trace hook is observability, not authority. Trace payload is not Ledger finality.
Trace hook result is not runtime enforcement.
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
from .path_resolver import PathGovernanceResolverResult
from .risk_classification import PathSourceRiskClassification
from .serialization import stable_hash
from .source_provenance import ProvenanceBinding
from .source_trust_resolver import SourceTrustResolverResult
from .untrusted_content_boundary import UntrustedContentBoundary
from .validation import validate_known_fields

PATH_RESOLUTION_TRACE_TASK_ID = "P1.7.13"
PATH_RESOLUTION_TRACE_PAYLOAD_SCHEMA = "path_resolution_trace_payload.v1"
PATH_RESOLUTION_TRACE_HOOK_VERSION = "path_resolution_trace_hook.v1"

PATH_RESOLUTION_TRACE_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "input_id",
    "path_resolver_result",
    "source_trust_resolver_result",
    "conflict_precedence_result",
    "risk_classification",
    "provenance_binding",
    "authority_scope",
    "untrusted_boundary",
    "source_label",
    "input_hash",
    "metadata",
})

PATH_RESOLUTION_TRACE_PAYLOAD_KNOWN_FIELDS: frozenset[str] = frozenset({
    "payload_id",
    "event_kind",
    "trace_subject_ref",
    "path_result_ref",
    "source_trust_result_ref",
    "conflict_result_ref",
    "risk_classification_ref",
    "provenance_binding_ref",
    "authority_scope_ref",
    "boundary_ref",
    "decision_summary",
    "trace_reasons",
    "source_label",
    "payload_hash",
    "schema_version",
    "created_by_task",
    "metadata",
})

PATH_RESOLUTION_TRACE_HOOK_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "hook_id",
    "input_id",
    "payload",
    "hook_mode",
    "disposition",
    "sink_name",
    "trace_written",
    "ledger_written",
    "runtime_mutated",
    "source_label",
    "hook_hash",
    "created_by_task",
    "hook_version",
    "metadata",
})

_FORBIDDEN_DECISION_TOKENS: frozenset[str] = frozenset({
    "ALLOW",
    "DENY",
    "BLOCK",
    "TRUST",
    "DISTRUST",
    "ENFORCE",
    "ENFORCED",
    "APPROVED",
    "QUARANTINE_NOW",
})


class PathResolutionTraceEventKind(str, Enum):
    """Trace event classification; not Ledger finality."""

    PATH_RESOLUTION_SHADOW_RESULT = "PATH_RESOLUTION_SHADOW_RESULT"
    SOURCE_TRUST_SHADOW_RESULT = "SOURCE_TRUST_SHADOW_RESULT"
    CONFLICT_PRECEDENCE_SHADOW_RESULT = "CONFLICT_PRECEDENCE_SHADOW_RESULT"
    PATH_SOURCE_TRACE_SUMMARY = "PATH_SOURCE_TRACE_SUMMARY"
    TRACE_HOOK_ATTEMPTED = "TRACE_HOOK_ATTEMPTED"
    TRACE_HOOK_PAYLOAD_CREATED = "TRACE_HOOK_PAYLOAD_CREATED"
    TRACE_SINK_UNAVAILABLE = "TRACE_SINK_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class PathResolutionTraceHookMode(str, Enum):
    """Trace hook delivery mode; does not imply enforcement."""

    PAYLOAD_ONLY = "PAYLOAD_ONLY"
    INJECTED_SINK = "INJECTED_SINK"
    TRACE_SPINE_UNAVAILABLE = "TRACE_SPINE_UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PathResolutionTraceDisposition(str, Enum):
    """Trace hook outcome disposition; not runtime action."""

    WOULD_RECORD = "WOULD_RECORD"
    PAYLOAD_CREATED = "PAYLOAD_CREATED"
    RECORDED_TO_INJECTED_SINK = "RECORDED_TO_INJECTED_SINK"
    TRACE_SPINE_UNAVAILABLE = "TRACE_SPINE_UNAVAILABLE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PathResolutionTraceReason(str, Enum):
    """Trace payload construction reason; does not enforce."""

    PATH_RESOLVER_RESULT_PRESENT = "PATH_RESOLVER_RESULT_PRESENT"
    SOURCE_TRUST_RESULT_PRESENT = "SOURCE_TRUST_RESULT_PRESENT"
    CONFLICT_PRECEDENCE_PRESENT = "CONFLICT_PRECEDENCE_PRESENT"
    RISK_CLASSIFICATION_PRESENT = "RISK_CLASSIFICATION_PRESENT"
    PROVENANCE_PRESENT = "PROVENANCE_PRESENT"
    AUTHORITY_SCOPE_PRESENT = "AUTHORITY_SCOPE_PRESENT"
    BOUNDARY_CONTEXT_PRESENT = "BOUNDARY_CONTEXT_PRESENT"
    SHADOW_ONLY_CONTEXT = "SHADOW_ONLY_CONTEXT"
    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    LEDGER_UNAVAILABLE = "LEDGER_UNAVAILABLE"
    TRACE_SPINE_UNAVAILABLE = "TRACE_SPINE_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


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
    value: PathResolutionTraceEventKind | str,
) -> PathResolutionTraceEventKind:
    if isinstance(value, PathResolutionTraceEventKind):
        return value
    if isinstance(value, str):
        try:
            return PathResolutionTraceEventKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid event_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="event_kind",
            ) from exc
    raise PathGovernanceError(
        "event_kind must be a string or PathResolutionTraceEventKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="event_kind",
    )


def _parse_hook_mode(
    value: PathResolutionTraceHookMode | str,
) -> PathResolutionTraceHookMode:
    if isinstance(value, PathResolutionTraceHookMode):
        return value
    if isinstance(value, str):
        try:
            return PathResolutionTraceHookMode(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid hook_mode: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="hook_mode",
            ) from exc
    raise PathGovernanceError(
        "hook_mode must be a string or PathResolutionTraceHookMode",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="hook_mode",
    )


def _parse_disposition(
    value: PathResolutionTraceDisposition | str,
) -> PathResolutionTraceDisposition:
    if isinstance(value, PathResolutionTraceDisposition):
        return value
    if isinstance(value, str):
        try:
            return PathResolutionTraceDisposition(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid disposition: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="disposition",
            ) from exc
    raise PathGovernanceError(
        "disposition must be a string or PathResolutionTraceDisposition",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="disposition",
    )


def _parse_trace_reasons(
    value: Sequence[PathResolutionTraceReason | str] | None,
) -> tuple[PathResolutionTraceReason, ...]:
    if value is None:
        return ()
    reasons: list[PathResolutionTraceReason] = []
    for item in value:
        if isinstance(item, PathResolutionTraceReason):
            reasons.append(item)
        elif isinstance(item, str):
            try:
                reasons.append(PathResolutionTraceReason(item))
            except ValueError as exc:
                raise PathGovernanceError(
                    f"invalid trace_reason: {item!r}",
                    code=PathGovernanceErrorCode.INVALID_ENUM,
                    field="trace_reasons",
                ) from exc
        else:
            raise PathGovernanceError(
                "trace_reasons must contain PathResolutionTraceReason or str values",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="trace_reasons",
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
            "source_trust_resolver_result must be a SourceTrustResolverResult "
            "or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="source_trust_resolver_result",
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


def _validate_decision_summary(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "decision_summary must be a mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="decision_summary",
        )

    def _check_item(item: Any) -> None:
        if isinstance(item, str):
            upper = item.upper()
            if upper in _FORBIDDEN_DECISION_TOKENS:
                raise PathGovernanceValidationError(
                    "decision_summary must use WOULD_* advisory vocabulary only",
                    code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                    field="decision_summary",
                )
            if upper == "ALLOWED" or upper == "BLOCKED" or upper == "DENIED":
                raise PathGovernanceValidationError(
                    "decision_summary must use WOULD_* advisory vocabulary only",
                    code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                    field="decision_summary",
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


def _collect_trace_reasons(
    *,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_resolver_result: SourceTrustResolverResult | None,
    conflict_precedence_result: ConflictPrecedenceResult | None,
    risk_classification: PathSourceRiskClassification | None,
    provenance_binding: ProvenanceBinding | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
) -> tuple[PathResolutionTraceReason, ...]:
    reasons: set[PathResolutionTraceReason] = {
        PathResolutionTraceReason.SHADOW_ONLY_CONTEXT,
        PathResolutionTraceReason.ENFORCEMENT_UNAVAILABLE,
        PathResolutionTraceReason.LEDGER_UNAVAILABLE,
        PathResolutionTraceReason.TRACE_SPINE_UNAVAILABLE,
    }
    if path_resolver_result is not None:
        reasons.add(PathResolutionTraceReason.PATH_RESOLVER_RESULT_PRESENT)
    if source_trust_resolver_result is not None:
        reasons.add(PathResolutionTraceReason.SOURCE_TRUST_RESULT_PRESENT)
    if conflict_precedence_result is not None:
        reasons.add(PathResolutionTraceReason.CONFLICT_PRECEDENCE_PRESENT)
    if risk_classification is not None:
        reasons.add(PathResolutionTraceReason.RISK_CLASSIFICATION_PRESENT)
    if provenance_binding is not None:
        reasons.add(PathResolutionTraceReason.PROVENANCE_PRESENT)
    if authority_scope is not None:
        reasons.add(PathResolutionTraceReason.AUTHORITY_SCOPE_PRESENT)
    if untrusted_boundary is not None:
        reasons.add(PathResolutionTraceReason.BOUNDARY_CONTEXT_PRESENT)
    return tuple(sorted(reasons, key=lambda reason: reason.value))


def _build_decision_summary(
    *,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_resolver_result: SourceTrustResolverResult | None,
    conflict_precedence_result: ConflictPrecedenceResult | None,
) -> Mapping[str, Any]:
    summary: dict[str, Any] = {
        "enforced": False,
        "shadow_only": True,
        "summary_text": (
            "Shadow path/source/conflict context summarized for observability only"
        ),
    }
    if path_resolver_result is not None:
        summary["path_shadow_decision"] = path_resolver_result.shadow_decision.value
        summary["path_shadow_only"] = path_resolver_result.shadow_only
        summary["path_enforced"] = path_resolver_result.enforced
    if source_trust_resolver_result is not None:
        summary["source_shadow_decision"] = (
            source_trust_resolver_result.shadow_decision.value
        )
        summary["source_shadow_only"] = source_trust_resolver_result.shadow_only
        summary["source_enforced"] = source_trust_resolver_result.enforced
    if conflict_precedence_result is not None:
        summary["conflict_recommended_shadow_decision"] = (
            conflict_precedence_result.recommended_shadow_decision
        )
        summary["conflict_final_shadow_posture"] = (
            conflict_precedence_result.final_shadow_posture.value
        )
        summary["conflict_shadow_only"] = conflict_precedence_result.shadow_only
        summary["conflict_enforced"] = conflict_precedence_result.enforced
    return _validate_decision_summary(summary)


def _input_payload(
    *,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_resolver_result: SourceTrustResolverResult | None,
    conflict_precedence_result: ConflictPrecedenceResult | None,
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
        "conflict_precedence_result": (
            None
            if conflict_precedence_result is None
            else conflict_precedence_result.to_canonical_dict()
        ),
        "metadata": _sorted_metadata_dict(metadata),
        "path_resolver_result": (
            None
            if path_resolver_result is None
            else path_resolver_result.to_canonical_dict()
        ),
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
        "source_trust_resolver_result": (
            None
            if source_trust_resolver_result is None
            else source_trust_resolver_result.to_canonical_dict()
        ),
        "untrusted_boundary": (
            None
            if untrusted_boundary is None
            else untrusted_boundary.to_canonical_dict()
        ),
    }


def compute_path_resolution_trace_input_hash(
    *,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_resolver_result: SourceTrustResolverResult | None,
    conflict_precedence_result: ConflictPrecedenceResult | None,
    risk_classification: PathSourceRiskClassification | None,
    provenance_binding: ProvenanceBinding | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path resolution trace input hash."""
    return stable_hash(_input_payload(
        path_resolver_result=path_resolver_result,
        source_trust_resolver_result=source_trust_resolver_result,
        conflict_precedence_result=conflict_precedence_result,
        risk_classification=risk_classification,
        provenance_binding=provenance_binding,
        authority_scope=authority_scope,
        untrusted_boundary=untrusted_boundary,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathResolutionTraceInput:
    """Hash-ready path resolution trace input; not enforcement authority."""

    path_resolver_result: PathGovernanceResolverResult | None = None
    source_trust_resolver_result: SourceTrustResolverResult | None = None
    conflict_precedence_result: ConflictPrecedenceResult | None = None
    risk_classification: PathSourceRiskClassification | None = None
    provenance_binding: ProvenanceBinding | None = None
    authority_scope: PathAuthorityScope | None = None
    untrusted_boundary: UntrustedContentBoundary | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    input_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path_resolver_result = _build_path_resolver_result(self.path_resolver_result)
        source_trust_resolver_result = _build_source_trust_resolver_result(
            self.source_trust_resolver_result,
        )
        conflict_precedence_result = _build_conflict_precedence_result(
            self.conflict_precedence_result,
        )
        risk_classification = _build_risk_classification(self.risk_classification)
        provenance_binding = _build_provenance_binding(self.provenance_binding)
        authority_scope = _build_authority_scope(self.authority_scope)
        untrusted_boundary = _build_untrusted_boundary(self.untrusted_boundary)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        input_hash = compute_path_resolution_trace_input_hash(
            path_resolver_result=path_resolver_result,
            source_trust_resolver_result=source_trust_resolver_result,
            conflict_precedence_result=conflict_precedence_result,
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
                "input_id does not match path resolution trace input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match path resolution trace input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "path_resolver_result", path_resolver_result)
        object.__setattr__(self, "source_trust_resolver_result", source_trust_resolver_result)
        object.__setattr__(self, "conflict_precedence_result", conflict_precedence_result)
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
            path_resolver_result=self.path_resolver_result,
            source_trust_resolver_result=self.source_trust_resolver_result,
            conflict_precedence_result=self.conflict_precedence_result,
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
    def from_dict(cls, data: Mapping[str, Any]) -> PathResolutionTraceInput:
        validate_known_fields(
            data,
            PATH_RESOLUTION_TRACE_INPUT_KNOWN_FIELDS,
            label="path_resolution_trace_input",
        )
        return cls(
            path_resolver_result=data.get("path_resolver_result"),
            source_trust_resolver_result=data.get("source_trust_resolver_result"),
            conflict_precedence_result=data.get("conflict_precedence_result"),
            risk_classification=data.get("risk_classification"),
            provenance_binding=data.get("provenance_binding"),
            authority_scope=data.get("authority_scope"),
            untrusted_boundary=data.get("untrusted_boundary"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            input_id=data.get("input_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


def _payload_hash_payload(
    *,
    event_kind: PathResolutionTraceEventKind,
    trace_subject_ref: str,
    path_result_ref: str,
    source_trust_result_ref: str,
    conflict_result_ref: str,
    risk_classification_ref: str,
    provenance_binding_ref: str,
    authority_scope_ref: str,
    boundary_ref: str,
    decision_summary: Mapping[str, Any],
    trace_reasons: tuple[PathResolutionTraceReason, ...],
    source_label: ProjectionSourceLabel,
    schema_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authority_scope_ref": authority_scope_ref,
        "boundary_ref": boundary_ref,
        "conflict_result_ref": conflict_result_ref,
        "created_by_task": created_by_task,
        "decision_summary": dict(decision_summary),
        "event_kind": event_kind.value,
        "metadata": _sorted_metadata_dict(metadata),
        "path_result_ref": path_result_ref,
        "provenance_binding_ref": provenance_binding_ref,
        "risk_classification_ref": risk_classification_ref,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "source_trust_result_ref": source_trust_result_ref,
        "trace_reasons": [reason.value for reason in trace_reasons],
        "trace_subject_ref": trace_subject_ref,
    }


def compute_path_resolution_trace_payload_id(
    *,
    event_kind: PathResolutionTraceEventKind,
    trace_subject_ref: str,
    path_result_ref: str,
    source_trust_result_ref: str,
    conflict_result_ref: str,
    risk_classification_ref: str,
    provenance_binding_ref: str,
    authority_scope_ref: str,
    boundary_ref: str,
    decision_summary: Mapping[str, Any],
    trace_reasons: tuple[PathResolutionTraceReason, ...],
    source_label: ProjectionSourceLabel,
    schema_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path resolution trace payload identifier."""
    return stable_hash(_payload_hash_payload(
        event_kind=event_kind,
        trace_subject_ref=trace_subject_ref,
        path_result_ref=path_result_ref,
        source_trust_result_ref=source_trust_result_ref,
        conflict_result_ref=conflict_result_ref,
        risk_classification_ref=risk_classification_ref,
        provenance_binding_ref=provenance_binding_ref,
        authority_scope_ref=authority_scope_ref,
        boundary_ref=boundary_ref,
        decision_summary=decision_summary,
        trace_reasons=trace_reasons,
        source_label=source_label,
        schema_version=schema_version,
        created_by_task=created_by_task,
        metadata=metadata,
    ))


def compute_path_resolution_trace_payload_hash(
    *,
    payload_id: str,
    event_kind: PathResolutionTraceEventKind,
    trace_subject_ref: str,
    path_result_ref: str,
    source_trust_result_ref: str,
    conflict_result_ref: str,
    risk_classification_ref: str,
    provenance_binding_ref: str,
    authority_scope_ref: str,
    boundary_ref: str,
    decision_summary: Mapping[str, Any],
    trace_reasons: tuple[PathResolutionTraceReason, ...],
    source_label: ProjectionSourceLabel,
    schema_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path resolution trace payload hash."""
    payload = _payload_hash_payload(
        event_kind=event_kind,
        trace_subject_ref=trace_subject_ref,
        path_result_ref=path_result_ref,
        source_trust_result_ref=source_trust_result_ref,
        conflict_result_ref=conflict_result_ref,
        risk_classification_ref=risk_classification_ref,
        provenance_binding_ref=provenance_binding_ref,
        authority_scope_ref=authority_scope_ref,
        boundary_ref=boundary_ref,
        decision_summary=decision_summary,
        trace_reasons=trace_reasons,
        source_label=source_label,
        schema_version=schema_version,
        created_by_task=created_by_task,
        metadata=metadata,
    )
    payload["payload_id"] = payload_id
    return stable_hash(payload)


@dataclass(frozen=True)
class PathResolutionTracePayload:
    """Deterministic path resolution trace payload; observability only."""

    event_kind: PathResolutionTraceEventKind = (
        PathResolutionTraceEventKind.PATH_SOURCE_TRACE_SUMMARY
    )
    trace_subject_ref: str = ""
    path_result_ref: str = ""
    source_trust_result_ref: str = ""
    conflict_result_ref: str = ""
    risk_classification_ref: str = ""
    provenance_binding_ref: str = ""
    authority_scope_ref: str = ""
    boundary_ref: str = ""
    decision_summary: Mapping[str, Any] = field(default_factory=dict)
    trace_reasons: tuple[PathResolutionTraceReason, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    payload_id: str = ""
    payload_hash: str = ""
    schema_version: str = PATH_RESOLUTION_TRACE_PAYLOAD_SCHEMA
    created_by_task: str = PATH_RESOLUTION_TRACE_TASK_ID
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        event_kind = _parse_event_kind(self.event_kind)
        trace_subject_ref = str(self.trace_subject_ref)
        path_result_ref = str(self.path_result_ref)
        source_trust_result_ref = str(self.source_trust_result_ref)
        conflict_result_ref = str(self.conflict_result_ref)
        risk_classification_ref = str(self.risk_classification_ref)
        provenance_binding_ref = str(self.provenance_binding_ref)
        authority_scope_ref = str(self.authority_scope_ref)
        boundary_ref = str(self.boundary_ref)
        decision_summary = _validate_decision_summary(self.decision_summary)
        trace_reasons = _parse_trace_reasons(self.trace_reasons)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        created_by_task = _required_string(self.created_by_task, field_name="created_by_task")
        payload_id = compute_path_resolution_trace_payload_id(
            event_kind=event_kind,
            trace_subject_ref=trace_subject_ref,
            path_result_ref=path_result_ref,
            source_trust_result_ref=source_trust_result_ref,
            conflict_result_ref=conflict_result_ref,
            risk_classification_ref=risk_classification_ref,
            provenance_binding_ref=provenance_binding_ref,
            authority_scope_ref=authority_scope_ref,
            boundary_ref=boundary_ref,
            decision_summary=decision_summary,
            trace_reasons=trace_reasons,
            source_label=source_label,
            schema_version=schema_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.payload_id not in ("", payload_id):
            raise PathGovernanceValidationError(
                "payload_id does not match path resolution trace payload content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload_id",
            )
        payload_hash = compute_path_resolution_trace_payload_hash(
            payload_id=payload_id,
            event_kind=event_kind,
            trace_subject_ref=trace_subject_ref,
            path_result_ref=path_result_ref,
            source_trust_result_ref=source_trust_result_ref,
            conflict_result_ref=conflict_result_ref,
            risk_classification_ref=risk_classification_ref,
            provenance_binding_ref=provenance_binding_ref,
            authority_scope_ref=authority_scope_ref,
            boundary_ref=boundary_ref,
            decision_summary=decision_summary,
            trace_reasons=trace_reasons,
            source_label=source_label,
            schema_version=schema_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.payload_hash not in ("", payload_hash):
            raise PathGovernanceValidationError(
                "payload_hash does not match path resolution trace payload content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload_hash",
            )
        object.__setattr__(self, "event_kind", event_kind)
        object.__setattr__(self, "trace_subject_ref", trace_subject_ref)
        object.__setattr__(self, "path_result_ref", path_result_ref)
        object.__setattr__(self, "source_trust_result_ref", source_trust_result_ref)
        object.__setattr__(self, "conflict_result_ref", conflict_result_ref)
        object.__setattr__(self, "risk_classification_ref", risk_classification_ref)
        object.__setattr__(self, "provenance_binding_ref", provenance_binding_ref)
        object.__setattr__(self, "authority_scope_ref", authority_scope_ref)
        object.__setattr__(self, "boundary_ref", boundary_ref)
        object.__setattr__(self, "decision_summary", decision_summary)
        object.__setattr__(self, "trace_reasons", trace_reasons)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "payload_id", payload_id)
        object.__setattr__(self, "payload_hash", payload_hash)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "created_by_task", created_by_task)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _payload_hash_payload(
            event_kind=self.event_kind,
            trace_subject_ref=self.trace_subject_ref,
            path_result_ref=self.path_result_ref,
            source_trust_result_ref=self.source_trust_result_ref,
            conflict_result_ref=self.conflict_result_ref,
            risk_classification_ref=self.risk_classification_ref,
            provenance_binding_ref=self.provenance_binding_ref,
            authority_scope_ref=self.authority_scope_ref,
            boundary_ref=self.boundary_ref,
            decision_summary=self.decision_summary,
            trace_reasons=self.trace_reasons,
            source_label=self.source_label,
            schema_version=self.schema_version,
            created_by_task=self.created_by_task,
            metadata=self.metadata,
        )
        payload["payload_id"] = self.payload_id
        payload["payload_hash"] = self.payload_hash
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathResolutionTracePayload:
        validate_known_fields(
            data,
            PATH_RESOLUTION_TRACE_PAYLOAD_KNOWN_FIELDS,
            label="path_resolution_trace_payload",
        )
        return cls(
            event_kind=data.get(
                "event_kind",
                PathResolutionTraceEventKind.PATH_SOURCE_TRACE_SUMMARY,
            ),
            trace_subject_ref=data.get("trace_subject_ref", ""),
            path_result_ref=data.get("path_result_ref", ""),
            source_trust_result_ref=data.get("source_trust_result_ref", ""),
            conflict_result_ref=data.get("conflict_result_ref", ""),
            risk_classification_ref=data.get("risk_classification_ref", ""),
            provenance_binding_ref=data.get("provenance_binding_ref", ""),
            authority_scope_ref=data.get("authority_scope_ref", ""),
            boundary_ref=data.get("boundary_ref", ""),
            decision_summary=data.get("decision_summary", {}),
            trace_reasons=tuple(data.get("trace_reasons", ())),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            payload_id=data.get("payload_id", ""),
            payload_hash=data.get("payload_hash", ""),
            schema_version=data.get("schema_version", PATH_RESOLUTION_TRACE_PAYLOAD_SCHEMA),
            created_by_task=data.get("created_by_task", PATH_RESOLUTION_TRACE_TASK_ID),
            metadata=data.get("metadata", {}),
        )


def _hook_hash_payload(
    *,
    input_id: str,
    payload_hash: str,
    hook_mode: PathResolutionTraceHookMode,
    disposition: PathResolutionTraceDisposition,
    sink_name: str | None,
    trace_written: bool,
    ledger_written: bool,
    runtime_mutated: bool,
    source_label: ProjectionSourceLabel,
    hook_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "created_by_task": created_by_task,
        "disposition": disposition.value,
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


def compute_path_resolution_trace_hook_id(
    *,
    input_id: str,
    payload_hash: str,
    hook_mode: PathResolutionTraceHookMode,
    disposition: PathResolutionTraceDisposition,
    sink_name: str | None,
    hook_version: str,
) -> str:
    """Compute deterministic path resolution trace hook identifier."""
    return stable_hash({
        "disposition": disposition.value,
        "hook_mode": hook_mode.value,
        "hook_version": hook_version,
        "input_id": input_id,
        "payload_hash": payload_hash,
        "sink_name": sink_name or "",
    })


def compute_path_resolution_trace_hook_hash(
    *,
    hook_id: str,
    input_id: str,
    payload_hash: str,
    hook_mode: PathResolutionTraceHookMode,
    disposition: PathResolutionTraceDisposition,
    sink_name: str | None,
    trace_written: bool,
    ledger_written: bool,
    runtime_mutated: bool,
    source_label: ProjectionSourceLabel,
    hook_version: str,
    created_by_task: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic path resolution trace hook hash."""
    payload = _hook_hash_payload(
        input_id=input_id,
        payload_hash=payload_hash,
        hook_mode=hook_mode,
        disposition=disposition,
        sink_name=sink_name,
        trace_written=trace_written,
        ledger_written=ledger_written,
        runtime_mutated=runtime_mutated,
        source_label=source_label,
        hook_version=hook_version,
        created_by_task=created_by_task,
        metadata=metadata,
    )
    payload["hook_id"] = hook_id
    return stable_hash(payload)


@dataclass(frozen=True)
class PathResolutionTraceHookResult:
    """Path resolution trace hook result; observability only, not enforcement."""

    input_id: str
    payload: PathResolutionTracePayload
    hook_mode: PathResolutionTraceHookMode = PathResolutionTraceHookMode.PAYLOAD_ONLY
    disposition: PathResolutionTraceDisposition = (
        PathResolutionTraceDisposition.PAYLOAD_CREATED
    )
    sink_name: str | None = None
    trace_written: bool = False
    ledger_written: bool = False
    runtime_mutated: bool = False
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    hook_id: str = ""
    hook_hash: str = ""
    created_by_task: str = PATH_RESOLUTION_TRACE_TASK_ID
    hook_version: str = PATH_RESOLUTION_TRACE_HOOK_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ledger_written is not False:
            raise PathGovernanceValidationError(
                "ledger_written must be False in P1.7.13",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="ledger_written",
            )
        if self.runtime_mutated is not False:
            raise PathGovernanceValidationError(
                "runtime_mutated must be False in P1.7.13",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="runtime_mutated",
            )
        input_id = _required_string(self.input_id, field_name="input_id")
        if not isinstance(self.payload, PathResolutionTracePayload):
            raise PathGovernanceValidationError(
                "payload must be a PathResolutionTracePayload",
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
        hook_id = compute_path_resolution_trace_hook_id(
            input_id=input_id,
            payload_hash=self.payload.payload_hash,
            hook_mode=hook_mode,
            disposition=disposition,
            sink_name=sink_name,
            hook_version=hook_version,
        )
        if self.hook_id not in ("", hook_id):
            raise PathGovernanceValidationError(
                "hook_id does not match path resolution trace hook content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="hook_id",
            )
        hook_hash = compute_path_resolution_trace_hook_hash(
            hook_id=hook_id,
            input_id=input_id,
            payload_hash=self.payload.payload_hash,
            hook_mode=hook_mode,
            disposition=disposition,
            sink_name=sink_name,
            trace_written=trace_written,
            ledger_written=False,
            runtime_mutated=False,
            source_label=source_label,
            hook_version=hook_version,
            created_by_task=created_by_task,
            metadata=metadata,
        )
        if self.hook_hash not in ("", hook_hash):
            raise PathGovernanceValidationError(
                "hook_hash does not match path resolution trace hook content",
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
    def from_dict(cls, data: Mapping[str, Any]) -> PathResolutionTraceHookResult:
        validate_known_fields(
            data,
            PATH_RESOLUTION_TRACE_HOOK_RESULT_KNOWN_FIELDS,
            label="path_resolution_trace_hook_result",
        )
        payload_raw = data["payload"]
        if isinstance(payload_raw, PathResolutionTracePayload):
            payload = payload_raw
        elif isinstance(payload_raw, MappingABC):
            payload = PathResolutionTracePayload.from_dict(payload_raw)
        else:
            raise PathGovernanceValidationError(
                "payload must be a PathResolutionTracePayload or mapping",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="payload",
            )
        return cls(
            input_id=data["input_id"],
            payload=payload,
            hook_mode=data.get("hook_mode", PathResolutionTraceHookMode.PAYLOAD_ONLY),
            disposition=data.get(
                "disposition",
                PathResolutionTraceDisposition.PAYLOAD_CREATED,
            ),
            sink_name=data.get("sink_name"),
            trace_written=data.get("trace_written", False),
            ledger_written=data.get("ledger_written", False),
            runtime_mutated=data.get("runtime_mutated", False),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            hook_id=data.get("hook_id", ""),
            hook_hash=data.get("hook_hash", ""),
            created_by_task=data.get("created_by_task", PATH_RESOLUTION_TRACE_TASK_ID),
            hook_version=data.get("hook_version", PATH_RESOLUTION_TRACE_HOOK_VERSION),
            metadata=data.get("metadata", {}),
        )


def build_path_resolution_trace_payload(
    *,
    trace_input: PathResolutionTraceInput | None = None,
    path_resolver_result: PathGovernanceResolverResult | None = None,
    source_trust_resolver_result: SourceTrustResolverResult | None = None,
    conflict_precedence_result: ConflictPrecedenceResult | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    trace_subject_ref: str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathResolutionTracePayload:
    """Build deterministic path resolution trace payload without writing trace."""
    if trace_input is None:
        trace_input = PathResolutionTraceInput(
            path_resolver_result=path_resolver_result,
            source_trust_resolver_result=source_trust_resolver_result,
            conflict_precedence_result=conflict_precedence_result,
            risk_classification=risk_classification,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            source_label=source_label,
            metadata=metadata or {},
        )
    subject_ref = trace_subject_ref or trace_input.input_id
    decision_summary = _build_decision_summary(
        path_resolver_result=trace_input.path_resolver_result,
        source_trust_resolver_result=trace_input.source_trust_resolver_result,
        conflict_precedence_result=trace_input.conflict_precedence_result,
    )
    trace_reasons = _collect_trace_reasons(
        path_resolver_result=trace_input.path_resolver_result,
        source_trust_resolver_result=trace_input.source_trust_resolver_result,
        conflict_precedence_result=trace_input.conflict_precedence_result,
        risk_classification=trace_input.risk_classification,
        provenance_binding=trace_input.provenance_binding,
        authority_scope=trace_input.authority_scope,
        untrusted_boundary=trace_input.untrusted_boundary,
    )
    return PathResolutionTracePayload(
        event_kind=PathResolutionTraceEventKind.PATH_SOURCE_TRACE_SUMMARY,
        trace_subject_ref=subject_ref,
        path_result_ref=_object_ref(
            "" if trace_input.path_resolver_result is None
            else trace_input.path_resolver_result.result_id,
            "" if trace_input.path_resolver_result is None
            else trace_input.path_resolver_result.result_hash,
        ),
        source_trust_result_ref=_object_ref(
            "" if trace_input.source_trust_resolver_result is None
            else trace_input.source_trust_resolver_result.result_id,
            "" if trace_input.source_trust_resolver_result is None
            else trace_input.source_trust_resolver_result.result_hash,
        ),
        conflict_result_ref=_object_ref(
            "" if trace_input.conflict_precedence_result is None
            else trace_input.conflict_precedence_result.result_id,
            "" if trace_input.conflict_precedence_result is None
            else trace_input.conflict_precedence_result.result_hash,
        ),
        risk_classification_ref=_object_ref(
            "" if trace_input.risk_classification is None
            else trace_input.risk_classification.classification_id,
            "" if trace_input.risk_classification is None
            else trace_input.risk_classification.classification_hash,
        ),
        provenance_binding_ref=_object_ref(
            "" if trace_input.provenance_binding is None
            else trace_input.provenance_binding.binding_id,
            "" if trace_input.provenance_binding is None
            else trace_input.provenance_binding.binding_hash,
        ),
        authority_scope_ref=_object_ref(
            "" if trace_input.authority_scope is None
            else trace_input.authority_scope.scope_id,
            "" if trace_input.authority_scope is None
            else trace_input.authority_scope.scope_hash,
        ),
        boundary_ref=_object_ref(
            "" if trace_input.untrusted_boundary is None
            else trace_input.untrusted_boundary.boundary_id,
            "" if trace_input.untrusted_boundary is None
            else trace_input.untrusted_boundary.boundary_hash,
        ),
        decision_summary=decision_summary,
        trace_reasons=trace_reasons,
        source_label=trace_input.source_label,
        metadata=trace_input.metadata,
    )


def record_path_resolution_trace_hook(
    *,
    trace_input: PathResolutionTraceInput | None = None,
    payload: PathResolutionTracePayload | None = None,
    path_resolver_result: PathGovernanceResolverResult | None = None,
    source_trust_resolver_result: SourceTrustResolverResult | None = None,
    conflict_precedence_result: ConflictPrecedenceResult | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    trace_subject_ref: str | None = None,
    sink: Callable[[PathResolutionTracePayload], Any] | None = None,
    sink_name: str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathResolutionTraceHookResult:
    """Record path resolution trace hook result without Ledger or runtime mutation."""
    if trace_input is None and payload is None:
        trace_input = PathResolutionTraceInput(
            path_resolver_result=path_resolver_result,
            source_trust_resolver_result=source_trust_resolver_result,
            conflict_precedence_result=conflict_precedence_result,
            risk_classification=risk_classification,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            source_label=source_label,
            metadata=metadata or {},
        )
    if payload is None:
        payload = build_path_resolution_trace_payload(
            trace_input=trace_input,
            trace_subject_ref=trace_subject_ref,
            source_label=source_label,
            metadata=metadata,
        )
    input_id = trace_input.input_id if trace_input is not None else payload.trace_subject_ref
    if sink is None:
        return PathResolutionTraceHookResult(
            input_id=input_id,
            payload=payload,
            hook_mode=PathResolutionTraceHookMode.PAYLOAD_ONLY,
            disposition=PathResolutionTraceDisposition.PAYLOAD_CREATED,
            sink_name=None,
            trace_written=False,
            ledger_written=False,
            runtime_mutated=False,
            source_label=payload.source_label,
            metadata=metadata or {},
        )
    try:
        sink(payload)
    except Exception:
        return PathResolutionTraceHookResult(
            input_id=input_id,
            payload=payload,
            hook_mode=PathResolutionTraceHookMode.ERROR,
            disposition=PathResolutionTraceDisposition.ERROR,
            sink_name=sink_name,
            trace_written=False,
            ledger_written=False,
            runtime_mutated=False,
            source_label=payload.source_label,
            metadata=metadata or {},
        )
    return PathResolutionTraceHookResult(
        input_id=input_id,
        payload=payload,
        hook_mode=PathResolutionTraceHookMode.INJECTED_SINK,
        disposition=PathResolutionTraceDisposition.RECORDED_TO_INJECTED_SINK,
        sink_name=sink_name,
        trace_written=True,
        ledger_written=False,
        runtime_mutated=False,
        source_label=payload.source_label,
        metadata=metadata or {},
    )
