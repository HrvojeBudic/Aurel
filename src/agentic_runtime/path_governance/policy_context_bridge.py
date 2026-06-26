"""Policy context bridge (P1.7.16).

Policy Context Bridge prepares governance context.
It does not decide policy.
Context readiness is not authority.
Policy bridge is input shaping, not enforcement.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .conflict_precedence import ConflictPrecedenceResult
from .escape_detection import PathBoundaryCheckResult
from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .path_authority_scope import PathAuthorityScope
from .path_identity import PathIdentity
from .path_resolution_trace import PathResolutionTracePayload
from .path_resolver import PathGovernanceResolverResult
from .path_violation_trace import PathViolationTracePayload
from .risk_classification import (
    PathSourceRiskClassification,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
)
from .serialization import stable_hash
from .source_identity import SourceIdentity
from .source_provenance import ProvenanceBinding
from .source_trust_resolver import (
    SourceTrustResolverResult,
    SourceTrustShadowDecision,
)
from .test_harness import PathGovernanceHarnessRunResult
from .trusted_roots import TrustedRootRegistry
from .untrusted_content_boundary import UntrustedContentBoundary
from .validation import validate_known_fields

PATH_POLICY_CONTEXT_BRIDGE_TASK_ID = "P1.7.16"
PATH_POLICY_CONTEXT_PACKET_SCHEMA = "path_policy_context_packet.v1"
PATH_POLICY_CONTEXT_BRIDGE_VERSION = "path_policy_context_bridge.v1"

PATH_POLICY_CONTEXT_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "input_id",
    "path_identity",
    "source_identity",
    "source_trust_label",
    "trusted_root_registry",
    "path_boundary_result",
    "authority_scope",
    "untrusted_boundary",
    "provenance_binding",
    "risk_classification",
    "path_resolver_result",
    "source_trust_result",
    "conflict_precedence_result",
    "path_resolution_trace_payload",
    "violation_drift_trace_payload",
    "harness_result",
    "decision_surfaces",
    "source_label",
    "input_hash",
    "metadata",
})

PATH_POLICY_CONTEXT_SUBJECT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "subject_ref_id",
    "subject_kind",
    "ref_id",
    "ref_hash",
    "summary",
    "source_label",
    "metadata",
})

PATH_POLICY_CONTEXT_PACKET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "packet_id",
    "subjects",
    "decision_surfaces",
    "requirements",
    "advisory_summary",
    "source_label",
    "packet_hash",
    "schema_version",
    "created_by_task",
    "metadata",
})

PATH_POLICY_CONTEXT_BRIDGE_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "bridge_id",
    "input_id",
    "context_packet",
    "bridge_mode",
    "disposition",
    "policy_called",
    "policy_decision_made",
    "approval_created",
    "ledger_written",
    "runtime_mutated",
    "enforcement_triggered",
    "source_label",
    "bridge_hash",
    "created_by_task",
    "bridge_version",
    "metadata",
})

_FORBIDDEN_DECISION_TOKENS: frozenset[str] = frozenset({
    "ALLOW",
    "DENY",
    "BLOCK",
    "APPROVE",
    "ENFORCE",
    "AUTHORIZED",
    "QUARANTINED",
})

_REQUIREMENT_ORDER: dict[str, int] = {}


class PathPolicyContextSubjectKind(str, Enum):
    """Policy context subject classification; not policy decision."""

    PATH_IDENTITY = "PATH_IDENTITY"
    SOURCE_IDENTITY = "SOURCE_IDENTITY"
    SOURCE_TRUST_LABEL = "SOURCE_TRUST_LABEL"
    TRUSTED_ROOT_SCOPE = "TRUSTED_ROOT_SCOPE"
    PATH_BOUNDARY_RESULT = "PATH_BOUNDARY_RESULT"
    AUTHORITY_SCOPE = "AUTHORITY_SCOPE"
    UNTRUSTED_CONTENT_BOUNDARY = "UNTRUSTED_CONTENT_BOUNDARY"
    PROVENANCE_BINDING = "PROVENANCE_BINDING"
    RISK_CLASSIFICATION = "RISK_CLASSIFICATION"
    PATH_RESOLVER_RESULT = "PATH_RESOLVER_RESULT"
    SOURCE_TRUST_RESULT = "SOURCE_TRUST_RESULT"
    CONFLICT_PRECEDENCE_RESULT = "CONFLICT_PRECEDENCE_RESULT"
    PATH_RESOLUTION_TRACE_PAYLOAD = "PATH_RESOLUTION_TRACE_PAYLOAD"
    VIOLATION_DRIFT_TRACE_PAYLOAD = "VIOLATION_DRIFT_TRACE_PAYLOAD"
    HARNESS_RESULT = "HARNESS_RESULT"
    UNKNOWN = "UNKNOWN"


class PathPolicyDecisionSurface(str, Enum):
    """Future policy decision surface; descriptive only, not execution."""

    MEMORY_WRITE = "MEMORY_WRITE"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    PROMPT_ASSEMBLY = "PROMPT_ASSEMBLY"
    FILE_ACCESS = "FILE_ACCESS"
    COMMAND_EXECUTION = "COMMAND_EXECUTION"
    MODEL_ROUTING = "MODEL_ROUTING"
    OUTPUT_PROVENANCE = "OUTPUT_PROVENANCE"
    AGENT_DELEGATION = "AGENT_DELEGATION"
    WORKFLOW_EXECUTION = "WORKFLOW_EXECUTION"
    SOURCE_TRUST_UPDATE = "SOURCE_TRUST_UPDATE"
    UNKNOWN = "UNKNOWN"


class PathPolicyRequirementKind(str, Enum):
    """Advisory policy requirement; not approval creation or enforcement."""

    REQUIRES_POLICY_REVIEW = "REQUIRES_POLICY_REVIEW"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_SOURCE_TRUST_REVIEW = "REQUIRES_SOURCE_TRUST_REVIEW"
    REQUIRES_PROVENANCE_REVIEW = "REQUIRES_PROVENANCE_REVIEW"
    REQUIRES_AUTHORITY_REVIEW = "REQUIRES_AUTHORITY_REVIEW"
    REQUIRES_TRACE_BINDING = "REQUIRES_TRACE_BINDING"
    REQUIRES_CONFLICT_REVIEW = "REQUIRES_CONFLICT_REVIEW"
    REQUIRES_RISK_REVIEW = "REQUIRES_RISK_REVIEW"
    WOULD_REQUIRE_RUNTIME_POLICY_LATER = "WOULD_REQUIRE_RUNTIME_POLICY_LATER"
    UNKNOWN = "UNKNOWN"


class PathPolicyBridgeMode(str, Enum):
    """Policy context bridge mode; does not invoke policy runtime."""

    CONTEXT_ONLY = "CONTEXT_ONLY"
    SIMULATION_CONTEXT = "SIMULATION_CONTEXT"
    POLICY_RUNTIME_UNAVAILABLE = "POLICY_RUNTIME_UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class PathPolicyBridgeDisposition(str, Enum):
    """Bridge outcome disposition; not policy decision."""

    CONTEXT_CREATED = "CONTEXT_CREATED"
    WOULD_SUBMIT_TO_POLICY_LATER = "WOULD_SUBMIT_TO_POLICY_LATER"
    POLICY_RUNTIME_UNAVAILABLE = "POLICY_RUNTIME_UNAVAILABLE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


_REQUIREMENT_ORDER.update({
    requirement.value: index
    for index, requirement in enumerate(PathPolicyRequirementKind)
})


def _requirement_sort_key(
    requirement: PathPolicyRequirementKind,
) -> int:
    return _REQUIREMENT_ORDER[requirement.value]


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


def _parse_subject_kind(
    value: PathPolicyContextSubjectKind | str,
) -> PathPolicyContextSubjectKind:
    if isinstance(value, PathPolicyContextSubjectKind):
        return value
    if isinstance(value, str):
        try:
            return PathPolicyContextSubjectKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid subject_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="subject_kind",
            ) from exc
    raise PathGovernanceError(
        "subject_kind must be a string or PathPolicyContextSubjectKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="subject_kind",
    )


def _parse_decision_surfaces(
    values: Sequence[PathPolicyDecisionSurface | str] | None,
) -> tuple[PathPolicyDecisionSurface, ...]:
    if values is None:
        return ()
    parsed: list[PathPolicyDecisionSurface] = []
    for value in values:
        if isinstance(value, PathPolicyDecisionSurface):
            parsed.append(value)
        elif isinstance(value, str):
            try:
                parsed.append(PathPolicyDecisionSurface(value))
            except ValueError as exc:
                raise PathGovernanceError(
                    f"invalid decision_surface: {value!r}",
                    code=PathGovernanceErrorCode.INVALID_ENUM,
                    field="decision_surfaces",
                ) from exc
        else:
            raise PathGovernanceError(
                "decision_surfaces must contain PathPolicyDecisionSurface or str",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="decision_surfaces",
            )
    return tuple(sorted(set(parsed), key=lambda item: item.value))


def _parse_requirements(
    values: Sequence[PathPolicyRequirementKind | str] | None,
) -> tuple[PathPolicyRequirementKind, ...]:
    if values is None:
        return ()
    parsed: list[PathPolicyRequirementKind] = []
    for value in values:
        if isinstance(value, PathPolicyRequirementKind):
            parsed.append(value)
        elif isinstance(value, str):
            try:
                parsed.append(PathPolicyRequirementKind(value))
            except ValueError as exc:
                raise PathGovernanceError(
                    f"invalid requirement: {value!r}",
                    code=PathGovernanceErrorCode.INVALID_ENUM,
                    field="requirements",
                ) from exc
        else:
            raise PathGovernanceError(
                "requirements must contain PathPolicyRequirementKind or str",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="requirements",
            )
    return tuple(sorted(set(parsed), key=_requirement_sort_key))


def _parse_bridge_mode(value: PathPolicyBridgeMode | str) -> PathPolicyBridgeMode:
    if isinstance(value, PathPolicyBridgeMode):
        return value
    if isinstance(value, str):
        try:
            return PathPolicyBridgeMode(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid bridge_mode: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="bridge_mode",
            ) from exc
    raise PathGovernanceError(
        "bridge_mode must be a string or PathPolicyBridgeMode",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="bridge_mode",
    )


def _parse_disposition(
    value: PathPolicyBridgeDisposition | str,
) -> PathPolicyBridgeDisposition:
    if isinstance(value, PathPolicyBridgeDisposition):
        return value
    if isinstance(value, str):
        try:
            return PathPolicyBridgeDisposition(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid disposition: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="disposition",
            ) from exc
    raise PathGovernanceError(
        "disposition must be a string or PathPolicyBridgeDisposition",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="disposition",
    )


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


def _validate_advisory_summary(value: str) -> str:
    if not isinstance(value, str):
        raise PathGovernanceValidationError(
            "advisory_summary must be a string",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="advisory_summary",
        )
    upper = value.upper()
    for token in _FORBIDDEN_DECISION_TOKENS:
        if token in upper.split() or f" {token} " in f" {upper} ":
            raise PathGovernanceValidationError(
                "advisory_summary must remain advisory only",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="advisory_summary",
            )
    return value


def _build_path_identity(
    value: PathIdentity | Mapping[str, Any] | None,
) -> PathIdentity | None:
    if value is None:
        return None
    if isinstance(value, PathIdentity):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_identity must be a PathIdentity or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="path_identity",
        )
    return PathIdentity.from_dict(value)


def _build_source_identity(
    value: SourceIdentity | Mapping[str, Any] | None,
) -> SourceIdentity | None:
    if value is None:
        return None
    if isinstance(value, SourceIdentity):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "source_identity must be a SourceIdentity or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="source_identity",
        )
    return SourceIdentity.from_dict(value)


def _parse_source_trust_label(
    value: SourceTrustLabel | str | None,
) -> SourceTrustLabel | None:
    if value is None:
        return None
    if isinstance(value, SourceTrustLabel):
        return value
    if isinstance(value, str):
        try:
            return SourceTrustLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_trust_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="source_trust_label",
            ) from exc
    raise PathGovernanceError(
        "source_trust_label must be a string or SourceTrustLabel",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="source_trust_label",
    )


def _build_trusted_root_registry(
    value: TrustedRootRegistry | Mapping[str, Any] | None,
) -> TrustedRootRegistry | None:
    if value is None:
        return None
    if isinstance(value, TrustedRootRegistry):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "trusted_root_registry must be a TrustedRootRegistry or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="trusted_root_registry",
        )
    return TrustedRootRegistry.from_dict(value)


def _build_path_boundary_result(
    value: PathBoundaryCheckResult | Mapping[str, Any] | None,
) -> PathBoundaryCheckResult | None:
    if value is None:
        return None
    if isinstance(value, PathBoundaryCheckResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_boundary_result must be a PathBoundaryCheckResult or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="path_boundary_result",
        )
    return PathBoundaryCheckResult.from_dict(value)


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


def _build_source_trust_result(
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


def _build_path_resolution_trace_payload(
    value: PathResolutionTracePayload | Mapping[str, Any] | None,
) -> PathResolutionTracePayload | None:
    if value is None:
        return None
    if isinstance(value, PathResolutionTracePayload):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_resolution_trace_payload must be a PathResolutionTracePayload "
            "or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="path_resolution_trace_payload",
        )
    return PathResolutionTracePayload.from_dict(value)


def _build_violation_drift_trace_payload(
    value: PathViolationTracePayload | Mapping[str, Any] | None,
) -> PathViolationTracePayload | None:
    if value is None:
        return None
    if isinstance(value, PathViolationTracePayload):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "violation_drift_trace_payload must be a PathViolationTracePayload "
            "or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="violation_drift_trace_payload",
        )
    return PathViolationTracePayload.from_dict(value)


def _build_harness_result(
    value: PathGovernanceHarnessRunResult | Mapping[str, Any] | None,
) -> PathGovernanceHarnessRunResult | None:
    if value is None:
        return None
    if isinstance(value, PathGovernanceHarnessRunResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "harness_result must be a PathGovernanceHarnessRunResult or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="harness_result",
        )
    return PathGovernanceHarnessRunResult.from_dict(value)


def _extract_ref_from_subject(
    subject_kind: PathPolicyContextSubjectKind,
    subject: Any,
) -> tuple[str, str, str]:
    """Extract ref_id, ref_hash, and advisory summary from upstream subject."""
    if subject_kind is PathPolicyContextSubjectKind.PATH_IDENTITY:
        assert isinstance(subject, PathIdentity)
        return (
            subject.identity_hash[:16],
            subject.identity_hash,
            "advisory path identity context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.SOURCE_IDENTITY:
        assert isinstance(subject, SourceIdentity)
        return (
            subject.source_ref.source_id,
            subject.identity_hash,
            "advisory source identity context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.SOURCE_TRUST_LABEL:
        label = subject if isinstance(subject, SourceTrustLabel) else SourceTrustLabel(subject)
        label_hash = stable_hash({"source_trust_label": label.value})
        return (label.value, label_hash, f"advisory source trust label {label.value}")
    if subject_kind is PathPolicyContextSubjectKind.TRUSTED_ROOT_SCOPE:
        assert isinstance(subject, TrustedRootRegistry)
        return (
            subject.registry_hash[:16],
            subject.registry_hash,
            "advisory trusted root scope context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.PATH_BOUNDARY_RESULT:
        assert isinstance(subject, PathBoundaryCheckResult)
        ref_hash = subject.result_hash
        ref_id = ref_hash[:16] if ref_hash else subject.normalized_path
        return (ref_id, ref_hash, "advisory path boundary check context reference")
    if subject_kind is PathPolicyContextSubjectKind.AUTHORITY_SCOPE:
        assert isinstance(subject, PathAuthorityScope)
        return (
            subject.scope_id,
            subject.scope_hash,
            "advisory authority scope context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.UNTRUSTED_CONTENT_BOUNDARY:
        assert isinstance(subject, UntrustedContentBoundary)
        return (
            subject.boundary_id,
            subject.boundary_hash,
            "advisory untrusted content boundary context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.PROVENANCE_BINDING:
        assert isinstance(subject, ProvenanceBinding)
        return (
            subject.binding_id,
            subject.binding_hash,
            "advisory provenance binding context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.RISK_CLASSIFICATION:
        assert isinstance(subject, PathSourceRiskClassification)
        return (
            subject.classification_id,
            subject.classification_hash,
            f"advisory risk classification {subject.risk_level.value}",
        )
    if subject_kind is PathPolicyContextSubjectKind.PATH_RESOLVER_RESULT:
        assert isinstance(subject, PathGovernanceResolverResult)
        return (
            subject.result_id,
            subject.result_hash,
            f"advisory path resolver shadow {subject.shadow_decision.value}",
        )
    if subject_kind is PathPolicyContextSubjectKind.SOURCE_TRUST_RESULT:
        assert isinstance(subject, SourceTrustResolverResult)
        return (
            subject.result_id,
            subject.result_hash,
            f"advisory source trust shadow {subject.shadow_decision.value}",
        )
    if subject_kind is PathPolicyContextSubjectKind.CONFLICT_PRECEDENCE_RESULT:
        assert isinstance(subject, ConflictPrecedenceResult)
        return (
            subject.result_id,
            subject.result_hash,
            "advisory conflict precedence context reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.PATH_RESOLUTION_TRACE_PAYLOAD:
        assert isinstance(subject, PathResolutionTracePayload)
        return (
            subject.payload_id,
            subject.payload_hash,
            "advisory path resolution trace payload reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.VIOLATION_DRIFT_TRACE_PAYLOAD:
        assert isinstance(subject, PathViolationTracePayload)
        return (
            subject.payload_id,
            subject.payload_hash,
            "advisory violation drift trace payload reference",
        )
    if subject_kind is PathPolicyContextSubjectKind.HARNESS_RESULT:
        assert isinstance(subject, PathGovernanceHarnessRunResult)
        return (
            subject.result_id,
            subject.result_hash,
            "advisory harness result context reference",
        )
    return ("", "", "advisory unknown subject context reference")


def compute_path_policy_context_subject_ref_id(
    *,
    subject_kind: PathPolicyContextSubjectKind,
    ref_id: str,
    ref_hash: str,
    summary: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    return stable_hash({
        "metadata": _sorted_metadata_dict(metadata),
        "ref_hash": ref_hash,
        "ref_id": ref_id,
        "source_label": source_label.value,
        "subject_kind": subject_kind.value,
        "summary": summary,
    })


def build_path_policy_context_subject_ref(
    subject_kind: PathPolicyContextSubjectKind | str,
    *,
    subject: Any = None,
    ref_id: str | None = None,
    ref_hash: str | None = None,
    summary: str | None = None,
    source_label: ProjectionSourceLabel | str,
    metadata: Mapping[str, Any] | None = None,
) -> PathPolicyContextSubjectRef:
    """Build a lightweight policy context subject reference; not a policy decision."""
    parsed_kind = _parse_subject_kind(subject_kind)
    parsed_label = _parse_source_label(source_label)
    frozen_metadata = _freeze_metadata(metadata)

    extracted_id = ref_id or ""
    extracted_hash = ref_hash or ""
    extracted_summary = summary or ""
    if subject is not None:
        auto_id, auto_hash, auto_summary = _extract_ref_from_subject(parsed_kind, subject)
        if not extracted_id:
            extracted_id = auto_id
        if not extracted_hash:
            extracted_hash = auto_hash
        if not extracted_summary:
            extracted_summary = auto_summary

    if not extracted_summary:
        extracted_summary = f"advisory {parsed_kind.value.lower()} context reference"

    subject_ref_id = compute_path_policy_context_subject_ref_id(
        subject_kind=parsed_kind,
        ref_id=extracted_id,
        ref_hash=extracted_hash,
        summary=extracted_summary,
        source_label=parsed_label,
        metadata=frozen_metadata,
    )

    return PathPolicyContextSubjectRef(
        subject_ref_id=subject_ref_id,
        subject_kind=parsed_kind,
        ref_id=extracted_id,
        ref_hash=extracted_hash,
        summary=extracted_summary,
        source_label=parsed_label,
        metadata=frozen_metadata,
    )


def _provenance_is_missing(provenance_binding: ProvenanceBinding | None) -> bool:
    if provenance_binding is None:
        return True
    if not provenance_binding.evidence_refs and not provenance_binding.claim_refs:
        return True
    return False


def _risk_has_missing_provenance(
    risk_classification: PathSourceRiskClassification | None,
) -> bool:
    if risk_classification is None:
        return False
    return any(
        signal.signal_kind is PathSourceRiskSignalKind.MISSING_PROVENANCE
        for signal in risk_classification.signals
    )


def derive_path_policy_requirements(
    *,
    context_input: PathPolicyContextInput | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    source_trust_result: SourceTrustResolverResult | None = None,
    conflict_precedence_result: ConflictPrecedenceResult | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    authority_scope: PathAuthorityScope | None = None,
    path_resolution_trace_payload: PathResolutionTracePayload | None = None,
    violation_drift_trace_payload: PathViolationTracePayload | None = None,
    source_label: ProjectionSourceLabel | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[PathPolicyRequirementKind, ...]:
    """Derive advisory policy requirements; does not create approvals or enforce."""
    _ = _parse_source_label(source_label) if source_label is not None else None
    _ = _freeze_metadata(metadata)

    if context_input is not None:
        risk_classification = context_input.risk_classification
        source_trust_result = context_input.source_trust_result
        conflict_precedence_result = context_input.conflict_precedence_result
        provenance_binding = context_input.provenance_binding
        authority_scope = context_input.authority_scope
        path_resolution_trace_payload = context_input.path_resolution_trace_payload
        violation_drift_trace_payload = context_input.violation_drift_trace_payload

    requirements: set[PathPolicyRequirementKind] = set()

    if risk_classification is not None:
        if risk_classification.risk_level in {
            PathSourceRiskLevel.HIGH,
            PathSourceRiskLevel.CRITICAL,
        }:
            requirements.update({
                PathPolicyRequirementKind.REQUIRES_RISK_REVIEW,
                PathPolicyRequirementKind.REQUIRES_OPERATOR_REVIEW,
                PathPolicyRequirementKind.WOULD_REQUIRE_RUNTIME_POLICY_LATER,
            })

    if _provenance_is_missing(provenance_binding) or _risk_has_missing_provenance(
        risk_classification,
    ):
        requirements.add(PathPolicyRequirementKind.REQUIRES_PROVENANCE_REVIEW)

    if source_trust_result is not None:
        if source_trust_result.shadow_decision in {
            SourceTrustShadowDecision.WOULD_DISTRUST,
            SourceTrustShadowDecision.WOULD_QUARANTINE,
        }:
            requirements.update({
                PathPolicyRequirementKind.REQUIRES_SOURCE_TRUST_REVIEW,
                PathPolicyRequirementKind.REQUIRES_POLICY_REVIEW,
            })

    if conflict_precedence_result is not None and conflict_precedence_result.conflict_signals:
        requirements.add(PathPolicyRequirementKind.REQUIRES_CONFLICT_REVIEW)

    if authority_scope is None:
        requirements.add(PathPolicyRequirementKind.REQUIRES_AUTHORITY_REVIEW)

    if path_resolution_trace_payload is not None or violation_drift_trace_payload is not None:
        requirements.add(PathPolicyRequirementKind.REQUIRES_TRACE_BINDING)

    return tuple(sorted(requirements, key=_requirement_sort_key))


def _build_advisory_summary(
    requirements: tuple[PathPolicyRequirementKind, ...],
) -> str:
    parts = ["context-only policy context packet; policy runtime unavailable"]
    for requirement in requirements:
        if requirement is PathPolicyRequirementKind.REQUIRES_RISK_REVIEW:
            parts.append("risk review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_OPERATOR_REVIEW:
            parts.append("operator review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_PROVENANCE_REVIEW:
            parts.append("provenance review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_SOURCE_TRUST_REVIEW:
            parts.append("source trust review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_POLICY_REVIEW:
            parts.append("future policy review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_CONFLICT_REVIEW:
            parts.append("conflict review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_AUTHORITY_REVIEW:
            parts.append("authority review required later")
        elif requirement is PathPolicyRequirementKind.REQUIRES_TRACE_BINDING:
            parts.append("trace binding recommended later")
        elif requirement is PathPolicyRequirementKind.WOULD_REQUIRE_RUNTIME_POLICY_LATER:
            parts.append("WOULD_REQUIRE_RUNTIME_POLICY_LATER")
    return _validate_advisory_summary("; ".join(parts))


def _input_payload(
    *,
    path_identity: PathIdentity | None,
    source_identity: SourceIdentity | None,
    source_trust_label: SourceTrustLabel | None,
    trusted_root_registry: TrustedRootRegistry | None,
    path_boundary_result: PathBoundaryCheckResult | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    risk_classification: PathSourceRiskClassification | None,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_result: SourceTrustResolverResult | None,
    conflict_precedence_result: ConflictPrecedenceResult | None,
    path_resolution_trace_payload: PathResolutionTracePayload | None,
    violation_drift_trace_payload: PathViolationTracePayload | None,
    harness_result: PathGovernanceHarnessRunResult | None,
    decision_surfaces: tuple[PathPolicyDecisionSurface, ...],
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
        "decision_surfaces": [item.value for item in decision_surfaces],
        "harness_result": (
            None if harness_result is None else harness_result.to_canonical_dict()
        ),
        "metadata": _sorted_metadata_dict(metadata),
        "path_boundary_result": (
            None
            if path_boundary_result is None
            else path_boundary_result.to_canonical_dict()
        ),
        "path_identity": (
            None if path_identity is None else path_identity.to_canonical_dict()
        ),
        "path_resolution_trace_payload": (
            None
            if path_resolution_trace_payload is None
            else path_resolution_trace_payload.to_canonical_dict()
        ),
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
        "source_identity": (
            None if source_identity is None else source_identity.to_canonical_dict()
        ),
        "source_label": source_label.value,
        "source_trust_label": (
            None if source_trust_label is None else source_trust_label.value
        ),
        "source_trust_result": (
            None
            if source_trust_result is None
            else source_trust_result.to_canonical_dict()
        ),
        "trusted_root_registry": (
            None
            if trusted_root_registry is None
            else trusted_root_registry.to_canonical_dict()
        ),
        "untrusted_boundary": (
            None
            if untrusted_boundary is None
            else untrusted_boundary.to_canonical_dict()
        ),
        "violation_drift_trace_payload": (
            None
            if violation_drift_trace_payload is None
            else violation_drift_trace_payload.to_canonical_dict()
        ),
    }


def compute_path_policy_context_input_hash(
    *,
    path_identity: PathIdentity | None = None,
    source_identity: SourceIdentity | None = None,
    source_trust_label: SourceTrustLabel | None = None,
    trusted_root_registry: TrustedRootRegistry | None = None,
    path_boundary_result: PathBoundaryCheckResult | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    path_resolver_result: PathGovernanceResolverResult | None = None,
    source_trust_result: SourceTrustResolverResult | None = None,
    conflict_precedence_result: ConflictPrecedenceResult | None = None,
    path_resolution_trace_payload: PathResolutionTracePayload | None = None,
    violation_drift_trace_payload: PathViolationTracePayload | None = None,
    harness_result: PathGovernanceHarnessRunResult | None = None,
    decision_surfaces: tuple[PathPolicyDecisionSurface, ...] = (),
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    return stable_hash(_input_payload(
        path_identity=path_identity,
        source_identity=source_identity,
        source_trust_label=source_trust_label,
        trusted_root_registry=trusted_root_registry,
        path_boundary_result=path_boundary_result,
        authority_scope=authority_scope,
        untrusted_boundary=untrusted_boundary,
        provenance_binding=provenance_binding,
        risk_classification=risk_classification,
        path_resolver_result=path_resolver_result,
        source_trust_result=source_trust_result,
        conflict_precedence_result=conflict_precedence_result,
        path_resolution_trace_payload=path_resolution_trace_payload,
        violation_drift_trace_payload=violation_drift_trace_payload,
        harness_result=harness_result,
        decision_surfaces=decision_surfaces,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathPolicyContextSubjectRef:
    """Lightweight policy context subject reference; not full payload embedding."""

    subject_ref_id: str
    subject_kind: PathPolicyContextSubjectKind
    ref_id: str = ""
    ref_hash: str = ""
    summary: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.UNAVAILABLE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        subject_kind = _parse_subject_kind(self.subject_kind)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        ref_id = str(self.ref_id)
        ref_hash = str(self.ref_hash)
        summary = _validate_advisory_summary(str(self.summary))
        subject_ref_id = compute_path_policy_context_subject_ref_id(
            subject_kind=subject_kind,
            ref_id=ref_id,
            ref_hash=ref_hash,
            summary=summary,
            source_label=source_label,
            metadata=metadata,
        )
        if self.subject_ref_id not in ("", subject_ref_id):
            raise PathGovernanceValidationError(
                "subject_ref_id does not match subject ref content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="subject_ref_id",
            )
        object.__setattr__(self, "subject_kind", subject_kind)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "ref_id", ref_id)
        object.__setattr__(self, "ref_hash", ref_hash)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "subject_ref_id", subject_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "metadata": _sorted_metadata_dict(self.metadata),
            "ref_hash": self.ref_hash,
            "ref_id": self.ref_id,
            "source_label": self.source_label.value,
            "subject_kind": self.subject_kind.value,
            "subject_ref_id": self.subject_ref_id,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathPolicyContextSubjectRef:
        validate_known_fields(
            data,
            PATH_POLICY_CONTEXT_SUBJECT_REF_KNOWN_FIELDS,
            label="path_policy_context_subject_ref",
        )
        return cls(
            subject_ref_id=data.get("subject_ref_id", ""),
            subject_kind=data["subject_kind"],
            ref_id=data.get("ref_id", ""),
            ref_hash=data.get("ref_hash", ""),
            summary=data.get("summary", ""),
            source_label=data.get("source_label", ProjectionSourceLabel.UNAVAILABLE),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathPolicyContextInput:
    """Hash-ready policy context input; not policy authority."""

    path_identity: PathIdentity | None = None
    source_identity: SourceIdentity | None = None
    source_trust_label: SourceTrustLabel | None = None
    trusted_root_registry: TrustedRootRegistry | None = None
    path_boundary_result: PathBoundaryCheckResult | None = None
    authority_scope: PathAuthorityScope | None = None
    untrusted_boundary: UntrustedContentBoundary | None = None
    provenance_binding: ProvenanceBinding | None = None
    risk_classification: PathSourceRiskClassification | None = None
    path_resolver_result: PathGovernanceResolverResult | None = None
    source_trust_result: SourceTrustResolverResult | None = None
    conflict_precedence_result: ConflictPrecedenceResult | None = None
    path_resolution_trace_payload: PathResolutionTracePayload | None = None
    violation_drift_trace_payload: PathViolationTracePayload | None = None
    harness_result: PathGovernanceHarnessRunResult | None = None
    decision_surfaces: tuple[PathPolicyDecisionSurface, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.UNAVAILABLE
    input_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path_identity = _build_path_identity(self.path_identity)
        source_identity = _build_source_identity(self.source_identity)
        source_trust_label = _parse_source_trust_label(self.source_trust_label)
        trusted_root_registry = _build_trusted_root_registry(self.trusted_root_registry)
        path_boundary_result = _build_path_boundary_result(self.path_boundary_result)
        authority_scope = _build_authority_scope(self.authority_scope)
        untrusted_boundary = _build_untrusted_boundary(self.untrusted_boundary)
        provenance_binding = _build_provenance_binding(self.provenance_binding)
        risk_classification = _build_risk_classification(self.risk_classification)
        path_resolver_result = _build_path_resolver_result(self.path_resolver_result)
        source_trust_result = _build_source_trust_result(self.source_trust_result)
        conflict_precedence_result = _build_conflict_precedence_result(
            self.conflict_precedence_result,
        )
        path_resolution_trace_payload = _build_path_resolution_trace_payload(
            self.path_resolution_trace_payload,
        )
        violation_drift_trace_payload = _build_violation_drift_trace_payload(
            self.violation_drift_trace_payload,
        )
        harness_result = _build_harness_result(self.harness_result)
        decision_surfaces = _parse_decision_surfaces(self.decision_surfaces)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        input_hash = compute_path_policy_context_input_hash(
            path_identity=path_identity,
            source_identity=source_identity,
            source_trust_label=source_trust_label,
            trusted_root_registry=trusted_root_registry,
            path_boundary_result=path_boundary_result,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            path_resolver_result=path_resolver_result,
            source_trust_result=source_trust_result,
            conflict_precedence_result=conflict_precedence_result,
            path_resolution_trace_payload=path_resolution_trace_payload,
            violation_drift_trace_payload=violation_drift_trace_payload,
            harness_result=harness_result,
            decision_surfaces=decision_surfaces,
            source_label=source_label,
            metadata=metadata,
        )
        input_id = input_hash
        if self.input_id not in ("", input_id):
            raise PathGovernanceValidationError(
                "input_id does not match policy context input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match policy context input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "path_identity", path_identity)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "source_trust_label", source_trust_label)
        object.__setattr__(self, "trusted_root_registry", trusted_root_registry)
        object.__setattr__(self, "path_boundary_result", path_boundary_result)
        object.__setattr__(self, "authority_scope", authority_scope)
        object.__setattr__(self, "untrusted_boundary", untrusted_boundary)
        object.__setattr__(self, "provenance_binding", provenance_binding)
        object.__setattr__(self, "risk_classification", risk_classification)
        object.__setattr__(self, "path_resolver_result", path_resolver_result)
        object.__setattr__(self, "source_trust_result", source_trust_result)
        object.__setattr__(self, "conflict_precedence_result", conflict_precedence_result)
        object.__setattr__(self, "path_resolution_trace_payload", path_resolution_trace_payload)
        object.__setattr__(self, "violation_drift_trace_payload", violation_drift_trace_payload)
        object.__setattr__(self, "harness_result", harness_result)
        object.__setattr__(self, "decision_surfaces", decision_surfaces)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "input_hash", input_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _input_payload(
            path_identity=self.path_identity,
            source_identity=self.source_identity,
            source_trust_label=self.source_trust_label,
            trusted_root_registry=self.trusted_root_registry,
            path_boundary_result=self.path_boundary_result,
            authority_scope=self.authority_scope,
            untrusted_boundary=self.untrusted_boundary,
            provenance_binding=self.provenance_binding,
            risk_classification=self.risk_classification,
            path_resolver_result=self.path_resolver_result,
            source_trust_result=self.source_trust_result,
            conflict_precedence_result=self.conflict_precedence_result,
            path_resolution_trace_payload=self.path_resolution_trace_payload,
            violation_drift_trace_payload=self.violation_drift_trace_payload,
            harness_result=self.harness_result,
            decision_surfaces=self.decision_surfaces,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["input_hash"] = self.input_hash
        payload["input_id"] = self.input_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathPolicyContextInput:
        validate_known_fields(
            data,
            PATH_POLICY_CONTEXT_INPUT_KNOWN_FIELDS,
            label="path_policy_context_input",
        )
        return cls(
            path_identity=data.get("path_identity"),
            source_identity=data.get("source_identity"),
            source_trust_label=data.get("source_trust_label"),
            trusted_root_registry=data.get("trusted_root_registry"),
            path_boundary_result=data.get("path_boundary_result"),
            authority_scope=data.get("authority_scope"),
            untrusted_boundary=data.get("untrusted_boundary"),
            provenance_binding=data.get("provenance_binding"),
            risk_classification=data.get("risk_classification"),
            path_resolver_result=data.get("path_resolver_result"),
            source_trust_result=data.get("source_trust_result"),
            conflict_precedence_result=data.get("conflict_precedence_result"),
            path_resolution_trace_payload=data.get("path_resolution_trace_payload"),
            violation_drift_trace_payload=data.get("violation_drift_trace_payload"),
            harness_result=data.get("harness_result"),
            decision_surfaces=data.get("decision_surfaces", ()),
            source_label=data.get("source_label", ProjectionSourceLabel.UNAVAILABLE),
            input_id=data.get("input_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


def compute_path_policy_context_packet_id(
    *,
    subjects: tuple[PathPolicyContextSubjectRef, ...],
    decision_surfaces: tuple[PathPolicyDecisionSurface, ...],
    requirements: tuple[PathPolicyRequirementKind, ...],
    schema_version: str,
) -> str:
    return stable_hash({
        "decision_surfaces": [item.value for item in decision_surfaces],
        "requirements": [item.value for item in requirements],
        "schema_version": schema_version,
        "subjects": [item.subject_ref_id for item in subjects],
    })


@dataclass(frozen=True)
class PathPolicyContextPacket:
    """Policy-ready context packet; descriptive only, not policy decision."""

    subjects: tuple[PathPolicyContextSubjectRef, ...]
    decision_surfaces: tuple[PathPolicyDecisionSurface, ...] = field(default_factory=tuple)
    requirements: tuple[PathPolicyRequirementKind, ...] = field(default_factory=tuple)
    advisory_summary: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.UNAVAILABLE
    packet_id: str = ""
    packet_hash: str = ""
    schema_version: str = PATH_POLICY_CONTEXT_PACKET_SCHEMA
    created_by_task: str = PATH_POLICY_CONTEXT_BRIDGE_TASK_ID
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        subjects = tuple(
            item if isinstance(item, PathPolicyContextSubjectRef)
            else PathPolicyContextSubjectRef.from_dict(item)
            for item in self.subjects
        )
        subjects = tuple(sorted(subjects, key=lambda item: item.subject_ref_id))
        decision_surfaces = _parse_decision_surfaces(self.decision_surfaces)
        requirements = _parse_requirements(self.requirements)
        advisory_summary = _validate_advisory_summary(str(self.advisory_summary))
        source_label = _parse_source_label(self.source_label)
        schema_version = str(self.schema_version)
        created_by_task = str(self.created_by_task)
        metadata = _freeze_metadata(self.metadata)
        if schema_version != PATH_POLICY_CONTEXT_PACKET_SCHEMA:
            raise PathGovernanceValidationError(
                "schema_version must be path_policy_context_packet.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="schema_version",
            )
        if created_by_task != PATH_POLICY_CONTEXT_BRIDGE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.16",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        packet_id = compute_path_policy_context_packet_id(
            subjects=subjects,
            decision_surfaces=decision_surfaces,
            requirements=requirements,
            schema_version=schema_version,
        )
        packet_hash = stable_hash({
            "advisory_summary": advisory_summary,
            "created_by_task": created_by_task,
            "decision_surfaces": [item.value for item in decision_surfaces],
            "metadata": _sorted_metadata_dict(metadata),
            "packet_id": packet_id,
            "requirements": [item.value for item in requirements],
            "schema_version": schema_version,
            "source_label": source_label.value,
            "subjects": [item.to_canonical_dict() for item in subjects],
        })
        if self.packet_id not in ("", packet_id):
            raise PathGovernanceValidationError(
                "packet_id does not match policy context packet content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="packet_id",
            )
        if self.packet_hash not in ("", packet_hash):
            raise PathGovernanceValidationError(
                "packet_hash does not match policy context packet content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="packet_hash",
            )
        object.__setattr__(self, "subjects", subjects)
        object.__setattr__(self, "decision_surfaces", decision_surfaces)
        object.__setattr__(self, "requirements", requirements)
        object.__setattr__(self, "advisory_summary", advisory_summary)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "packet_id", packet_id)
        object.__setattr__(self, "packet_hash", packet_hash)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "created_by_task", created_by_task)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "advisory_summary": self.advisory_summary,
            "created_by_task": self.created_by_task,
            "decision_surfaces": [item.value for item in self.decision_surfaces],
            "metadata": _sorted_metadata_dict(self.metadata),
            "packet_hash": self.packet_hash,
            "packet_id": self.packet_id,
            "requirements": [item.value for item in self.requirements],
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "subjects": [item.to_canonical_dict() for item in self.subjects],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathPolicyContextPacket:
        validate_known_fields(
            data,
            PATH_POLICY_CONTEXT_PACKET_KNOWN_FIELDS,
            label="path_policy_context_packet",
        )
        return cls(
            subjects=tuple(data.get("subjects", ())),
            decision_surfaces=data.get("decision_surfaces", ()),
            requirements=data.get("requirements", ()),
            advisory_summary=data.get("advisory_summary", ""),
            source_label=data.get("source_label", ProjectionSourceLabel.UNAVAILABLE),
            packet_id=data.get("packet_id", ""),
            packet_hash=data.get("packet_hash", ""),
            schema_version=data.get("schema_version", PATH_POLICY_CONTEXT_PACKET_SCHEMA),
            created_by_task=data.get("created_by_task", PATH_POLICY_CONTEXT_BRIDGE_TASK_ID),
            metadata=data.get("metadata", {}),
        )


def _build_subject_refs_from_input(
    context_input: PathPolicyContextInput,
) -> tuple[PathPolicyContextSubjectRef, ...]:
    refs: list[PathPolicyContextSubjectRef] = []
    mapping: list[tuple[Any, PathPolicyContextSubjectKind]] = [
        (context_input.path_identity, PathPolicyContextSubjectKind.PATH_IDENTITY),
        (context_input.source_identity, PathPolicyContextSubjectKind.SOURCE_IDENTITY),
        (context_input.source_trust_label, PathPolicyContextSubjectKind.SOURCE_TRUST_LABEL),
        (context_input.trusted_root_registry, PathPolicyContextSubjectKind.TRUSTED_ROOT_SCOPE),
        (context_input.path_boundary_result, PathPolicyContextSubjectKind.PATH_BOUNDARY_RESULT),
        (context_input.authority_scope, PathPolicyContextSubjectKind.AUTHORITY_SCOPE),
        (context_input.untrusted_boundary, PathPolicyContextSubjectKind.UNTRUSTED_CONTENT_BOUNDARY),
        (context_input.provenance_binding, PathPolicyContextSubjectKind.PROVENANCE_BINDING),
        (context_input.risk_classification, PathPolicyContextSubjectKind.RISK_CLASSIFICATION),
        (context_input.path_resolver_result, PathPolicyContextSubjectKind.PATH_RESOLVER_RESULT),
        (context_input.source_trust_result, PathPolicyContextSubjectKind.SOURCE_TRUST_RESULT),
        (context_input.conflict_precedence_result, PathPolicyContextSubjectKind.CONFLICT_PRECEDENCE_RESULT),
        (context_input.path_resolution_trace_payload, PathPolicyContextSubjectKind.PATH_RESOLUTION_TRACE_PAYLOAD),
        (context_input.violation_drift_trace_payload, PathPolicyContextSubjectKind.VIOLATION_DRIFT_TRACE_PAYLOAD),
        (context_input.harness_result, PathPolicyContextSubjectKind.HARNESS_RESULT),
    ]
    for subject, kind in mapping:
        if subject is not None:
            refs.append(build_path_policy_context_subject_ref(
                kind,
                subject=subject,
                source_label=context_input.source_label,
                metadata=context_input.metadata,
            ))
    return tuple(sorted(refs, key=lambda item: item.subject_ref_id))


def build_path_policy_context_packet(
    *,
    context_input: PathPolicyContextInput | None = None,
    path_identity: PathIdentity | None = None,
    source_identity: SourceIdentity | None = None,
    source_trust_label: SourceTrustLabel | str | None = None,
    trusted_root_registry: TrustedRootRegistry | None = None,
    path_boundary_result: PathBoundaryCheckResult | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    path_resolver_result: PathGovernanceResolverResult | None = None,
    source_trust_result: SourceTrustResolverResult | None = None,
    conflict_precedence_result: ConflictPrecedenceResult | None = None,
    path_resolution_trace_payload: PathResolutionTracePayload | None = None,
    violation_drift_trace_payload: PathViolationTracePayload | None = None,
    harness_result: PathGovernanceHarnessRunResult | None = None,
    decision_surfaces: Sequence[PathPolicyDecisionSurface | str] | None = None,
    source_label: ProjectionSourceLabel | str,
    metadata: Mapping[str, Any] | None = None,
) -> PathPolicyContextPacket:
    """Build advisory policy context packet; does not call policy engine."""
    parsed_label = _parse_source_label(source_label)
    frozen_metadata = _freeze_metadata(metadata)

    if context_input is None:
        context_input = PathPolicyContextInput(
            path_identity=path_identity,
            source_identity=source_identity,
            source_trust_label=source_trust_label,
            trusted_root_registry=trusted_root_registry,
            path_boundary_result=path_boundary_result,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            path_resolver_result=path_resolver_result,
            source_trust_result=source_trust_result,
            conflict_precedence_result=conflict_precedence_result,
            path_resolution_trace_payload=path_resolution_trace_payload,
            violation_drift_trace_payload=violation_drift_trace_payload,
            harness_result=harness_result,
            decision_surfaces=decision_surfaces or (),
            source_label=parsed_label,
            metadata=frozen_metadata,
        )

    subjects = _build_subject_refs_from_input(context_input)
    requirements = derive_path_policy_requirements(context_input=context_input)
    advisory_summary = _build_advisory_summary(requirements)
    surfaces = context_input.decision_surfaces
    if decision_surfaces is not None:
        surfaces = _parse_decision_surfaces(decision_surfaces)

    return PathPolicyContextPacket(
        subjects=subjects,
        decision_surfaces=surfaces,
        requirements=requirements,
        advisory_summary=advisory_summary,
        source_label=context_input.source_label,
        metadata=frozen_metadata,
    )


def compute_path_policy_context_bridge_id(
    *,
    input_id: str,
    packet_hash: str,
    bridge_mode: PathPolicyBridgeMode,
    disposition: PathPolicyBridgeDisposition,
    bridge_version: str,
) -> str:
    return stable_hash({
        "bridge_mode": bridge_mode.value,
        "bridge_version": bridge_version,
        "disposition": disposition.value,
        "input_id": input_id,
        "packet_hash": packet_hash,
    })


@dataclass(frozen=True)
class PathPolicyContextBridgeResult:
    """Policy context bridge outcome; not policy decision or enforcement."""

    input_id: str
    context_packet: PathPolicyContextPacket
    bridge_mode: PathPolicyBridgeMode = PathPolicyBridgeMode.CONTEXT_ONLY
    disposition: PathPolicyBridgeDisposition = PathPolicyBridgeDisposition.CONTEXT_CREATED
    policy_called: bool = False
    policy_decision_made: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    runtime_mutated: bool = False
    enforcement_triggered: bool = False
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.UNAVAILABLE
    bridge_id: str = ""
    bridge_hash: str = ""
    created_by_task: str = PATH_POLICY_CONTEXT_BRIDGE_TASK_ID
    bridge_version: str = PATH_POLICY_CONTEXT_BRIDGE_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        input_id = str(self.input_id)
        context_packet = (
            self.context_packet
            if isinstance(self.context_packet, PathPolicyContextPacket)
            else PathPolicyContextPacket.from_dict(self.context_packet)
        )
        bridge_mode = _parse_bridge_mode(self.bridge_mode)
        disposition = _parse_disposition(self.disposition)
        source_label = _parse_source_label(self.source_label)
        created_by_task = str(self.created_by_task)
        bridge_version = str(self.bridge_version)
        metadata = _freeze_metadata(self.metadata)

        for field_name, value in (
            ("policy_called", self.policy_called),
            ("policy_decision_made", self.policy_decision_made),
            ("approval_created", self.approval_created),
            ("ledger_written", self.ledger_written),
            ("runtime_mutated", self.runtime_mutated),
            ("enforcement_triggered", self.enforcement_triggered),
        ):
            if value is not False:
                raise PathGovernanceValidationError(
                    f"{field_name} must be false in P1.7.16",
                    code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                    field=field_name,
                )

        if created_by_task != PATH_POLICY_CONTEXT_BRIDGE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.16",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        if bridge_version != PATH_POLICY_CONTEXT_BRIDGE_VERSION:
            raise PathGovernanceValidationError(
                "bridge_version must be path_policy_context_bridge.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="bridge_version",
            )

        bridge_id = compute_path_policy_context_bridge_id(
            input_id=input_id,
            packet_hash=context_packet.packet_hash,
            bridge_mode=bridge_mode,
            disposition=disposition,
            bridge_version=bridge_version,
        )
        bridge_hash = stable_hash({
            "approval_created": False,
            "bridge_id": bridge_id,
            "bridge_mode": bridge_mode.value,
            "bridge_version": bridge_version,
            "context_packet": context_packet.to_canonical_dict(),
            "created_by_task": created_by_task,
            "disposition": disposition.value,
            "enforcement_triggered": False,
            "input_id": input_id,
            "ledger_written": False,
            "metadata": _sorted_metadata_dict(metadata),
            "policy_called": False,
            "policy_decision_made": False,
            "runtime_mutated": False,
            "source_label": source_label.value,
        })

        if self.bridge_id not in ("", bridge_id):
            raise PathGovernanceValidationError(
                "bridge_id does not match bridge result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="bridge_id",
            )
        if self.bridge_hash not in ("", bridge_hash):
            raise PathGovernanceValidationError(
                "bridge_hash does not match bridge result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="bridge_hash",
            )

        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "context_packet", context_packet)
        object.__setattr__(self, "bridge_mode", bridge_mode)
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "created_by_task", created_by_task)
        object.__setattr__(self, "bridge_version", bridge_version)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "bridge_id", bridge_id)
        object.__setattr__(self, "bridge_hash", bridge_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "approval_created": self.approval_created,
            "bridge_hash": self.bridge_hash,
            "bridge_id": self.bridge_id,
            "bridge_mode": self.bridge_mode.value,
            "bridge_version": self.bridge_version,
            "context_packet": self.context_packet.to_canonical_dict(),
            "created_by_task": self.created_by_task,
            "disposition": self.disposition.value,
            "enforcement_triggered": self.enforcement_triggered,
            "input_id": self.input_id,
            "ledger_written": self.ledger_written,
            "metadata": _sorted_metadata_dict(self.metadata),
            "policy_called": self.policy_called,
            "policy_decision_made": self.policy_decision_made,
            "runtime_mutated": self.runtime_mutated,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathPolicyContextBridgeResult:
        validate_known_fields(
            data,
            PATH_POLICY_CONTEXT_BRIDGE_RESULT_KNOWN_FIELDS,
            label="path_policy_context_bridge_result",
        )
        return cls(
            input_id=data["input_id"],
            context_packet=data["context_packet"],
            bridge_mode=data.get("bridge_mode", PathPolicyBridgeMode.CONTEXT_ONLY),
            disposition=data.get("disposition", PathPolicyBridgeDisposition.CONTEXT_CREATED),
            policy_called=bool(data.get("policy_called", False)),
            policy_decision_made=bool(data.get("policy_decision_made", False)),
            approval_created=bool(data.get("approval_created", False)),
            ledger_written=bool(data.get("ledger_written", False)),
            runtime_mutated=bool(data.get("runtime_mutated", False)),
            enforcement_triggered=bool(data.get("enforcement_triggered", False)),
            source_label=data.get("source_label", ProjectionSourceLabel.UNAVAILABLE),
            bridge_id=data.get("bridge_id", ""),
            bridge_hash=data.get("bridge_hash", ""),
            created_by_task=data.get("created_by_task", PATH_POLICY_CONTEXT_BRIDGE_TASK_ID),
            bridge_version=data.get("bridge_version", PATH_POLICY_CONTEXT_BRIDGE_VERSION),
            metadata=data.get("metadata", {}),
        )


def bridge_path_governance_to_policy_context(
    *,
    context_input: PathPolicyContextInput | None = None,
    context_packet: PathPolicyContextPacket | None = None,
    path_identity: PathIdentity | None = None,
    source_identity: SourceIdentity | None = None,
    source_trust_label: SourceTrustLabel | str | None = None,
    trusted_root_registry: TrustedRootRegistry | None = None,
    path_boundary_result: PathBoundaryCheckResult | None = None,
    authority_scope: PathAuthorityScope | None = None,
    untrusted_boundary: UntrustedContentBoundary | None = None,
    provenance_binding: ProvenanceBinding | None = None,
    risk_classification: PathSourceRiskClassification | None = None,
    path_resolver_result: PathGovernanceResolverResult | None = None,
    source_trust_result: SourceTrustResolverResult | None = None,
    conflict_precedence_result: ConflictPrecedenceResult | None = None,
    path_resolution_trace_payload: PathResolutionTracePayload | None = None,
    violation_drift_trace_payload: PathViolationTracePayload | None = None,
    harness_result: PathGovernanceHarnessRunResult | None = None,
    decision_surfaces: Sequence[PathPolicyDecisionSurface | str] | None = None,
    bridge_mode: PathPolicyBridgeMode | str = PathPolicyBridgeMode.CONTEXT_ONLY,
    source_label: ProjectionSourceLabel | str,
    metadata: Mapping[str, Any] | None = None,
) -> PathPolicyContextBridgeResult:
    """Bridge path governance context to policy-ready packet; does not call policy."""
    parsed_mode = _parse_bridge_mode(bridge_mode)
    parsed_label = _parse_source_label(source_label)
    frozen_metadata = _freeze_metadata(metadata)

    if context_input is None and context_packet is None:
        context_input = PathPolicyContextInput(
            path_identity=path_identity,
            source_identity=source_identity,
            source_trust_label=source_trust_label,
            trusted_root_registry=trusted_root_registry,
            path_boundary_result=path_boundary_result,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            path_resolver_result=path_resolver_result,
            source_trust_result=source_trust_result,
            conflict_precedence_result=conflict_precedence_result,
            path_resolution_trace_payload=path_resolution_trace_payload,
            violation_drift_trace_payload=violation_drift_trace_payload,
            harness_result=harness_result,
            decision_surfaces=decision_surfaces or (),
            source_label=parsed_label,
            metadata=frozen_metadata,
        )
    elif context_input is None:
        input_id = stable_hash({"packet_hash": context_packet.packet_hash})
    else:
        input_id = context_input.input_id

    if context_packet is None:
        context_packet = build_path_policy_context_packet(
            context_input=context_input,
            decision_surfaces=decision_surfaces,
            source_label=parsed_label,
            metadata=frozen_metadata,
        )
        input_id = context_input.input_id if context_input is not None else input_id

    if parsed_mode is PathPolicyBridgeMode.POLICY_RUNTIME_UNAVAILABLE:
        disposition = PathPolicyBridgeDisposition.POLICY_RUNTIME_UNAVAILABLE
    elif parsed_mode is PathPolicyBridgeMode.ERROR:
        disposition = PathPolicyBridgeDisposition.ERROR
    elif parsed_mode is PathPolicyBridgeMode.SIMULATION_CONTEXT:
        disposition = PathPolicyBridgeDisposition.WOULD_SUBMIT_TO_POLICY_LATER
    else:
        disposition = PathPolicyBridgeDisposition.CONTEXT_CREATED

    return PathPolicyContextBridgeResult(
        input_id=input_id,
        context_packet=context_packet,
        bridge_mode=parsed_mode,
        disposition=disposition,
        source_label=parsed_label,
        metadata=frozen_metadata,
    )
