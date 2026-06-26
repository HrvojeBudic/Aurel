"""Path governance resolver v0 shadow recommendations (P1.7.10).

Resolver v0 is shadow-only. WOULD_* recommendations are not enforcement,
authorization, approval activation, trace writes, Ledger writes, or runtime action.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .escape_detection import PathBoundaryCheckResult, PathBoundaryStatus
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .path_authority_scope import PathAuthorityScope
from .path_identity import PathIdentity
from .risk_classification import (
    PathSourceRiskClassification,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
    RiskClassificationBasis,
)
from .serialization import stable_hash
from .source_identity import SourceIdentity
from .source_provenance import EvidenceConfidence, ProvenanceBinding
from .trusted_roots import TrustedRootRegistry
from .untrusted_content_boundary import (
    ContentInfluenceSurface,
    UntrustedBoundaryPosture,
    UntrustedContentBoundary,
)
from .validation import validate_known_fields

PATH_GOVERNANCE_RESOLVER_TASK_ID = "P1.7.10"
PATH_GOVERNANCE_RESOLVER_VERSION = "path_governance_resolver.v0.shadow"

PATH_GOVERNANCE_RESOLVER_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "input_id",
    "path_identity",
    "source_identity",
    "trusted_root_registry",
    "boundary_check_result",
    "authority_scope",
    "untrusted_boundary",
    "provenance_binding",
    "risk_classification",
    "source_label",
    "input_hash",
    "metadata",
})

PATH_GOVERNANCE_RESOLVER_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "result_id",
    "input_id",
    "shadow_decision",
    "decision_reasons",
    "risk_level",
    "source_label",
    "shadow_only",
    "enforced",
    "would_require_approval",
    "would_write_trace_later",
    "result_hash",
    "created_by_task",
    "resolver_version",
    "metadata",
})

_ACCEPTABLE_TRUST_LABELS: frozenset[SourceTrustLabel] = frozenset({
    SourceTrustLabel.TRUSTED,
    SourceTrustLabel.OPERATOR_PROVIDED,
    SourceTrustLabel.INTERNAL_REPO,
    SourceTrustLabel.LOCAL_PRIVATE,
    SourceTrustLabel.TOOL_GENERATED,
})

_UNTRUSTED_TRUST_LABELS: frozenset[SourceTrustLabel] = frozenset({
    SourceTrustLabel.UNTRUSTED,
    SourceTrustLabel.QUARANTINED,
})

_COMMAND_SURFACES: frozenset[ContentInfluenceSurface] = frozenset({
    ContentInfluenceSurface.PROMPT_INSTRUCTION,
    ContentInfluenceSurface.TOOL_ARGUMENT,
    ContentInfluenceSurface.MEMORY_WRITE,
    ContentInfluenceSurface.POLICY_DEFINITION,
    ContentInfluenceSurface.AUTHORITY_EXPANSION,
    ContentInfluenceSurface.EXECUTION_REQUEST,
    ContentInfluenceSurface.SOURCE_CANONIZATION,
})

_AUTHORITY_SIGNAL_KINDS: frozenset[PathSourceRiskSignalKind] = frozenset({
    PathSourceRiskSignalKind.AUTHORITY_EXPANSION_SURFACE,
    PathSourceRiskSignalKind.POLICY_DEFINITION_SURFACE,
    PathSourceRiskSignalKind.EXECUTION_REQUEST_SURFACE,
})


class PathGovernanceShadowDecision(str, Enum):
    """Shadow recommendation vocabulary; not runtime action or enforcement."""

    WOULD_ALLOW = "WOULD_ALLOW"
    WOULD_REVIEW = "WOULD_REVIEW"
    WOULD_RESTRICT = "WOULD_RESTRICT"
    WOULD_DENY = "WOULD_DENY"
    WOULD_QUARANTINE = "WOULD_QUARANTINE"
    WOULD_REQUIRE_OPERATOR_REVIEW = "WOULD_REQUIRE_OPERATOR_REVIEW"
    WOULD_REQUIRE_POLICY_REVIEW = "WOULD_REQUIRE_POLICY_REVIEW"
    UNKNOWN = "UNKNOWN"


class PathGovernanceDecisionReason(str, Enum):
    """Deterministic explanation vocabulary for shadow recommendations."""

    SOURCE_TRUST_ACCEPTABLE = "SOURCE_TRUST_ACCEPTABLE"
    SOURCE_TRUST_UNTRUSTED = "SOURCE_TRUST_UNTRUSTED"
    SOURCE_TRUST_UNKNOWN = "SOURCE_TRUST_UNKNOWN"
    PATH_WITHIN_DECLARED_ROOT = "PATH_WITHIN_DECLARED_ROOT"
    PATH_OUTSIDE_DECLARED_ROOT = "PATH_OUTSIDE_DECLARED_ROOT"
    PATH_TRAVERSAL_CANDIDATE = "PATH_TRAVERSAL_CANDIDATE"
    AUTHORITY_SCOPE_DECLARED = "AUTHORITY_SCOPE_DECLARED"
    AUTHORITY_SCOPE_MISSING = "AUTHORITY_SCOPE_MISSING"
    UNTRUSTED_CONTENT_BOUNDARY = "UNTRUSTED_CONTENT_BOUNDARY"
    RISK_CLASSIFICATION_HIGH = "RISK_CLASSIFICATION_HIGH"
    RISK_CLASSIFICATION_CRITICAL = "RISK_CLASSIFICATION_CRITICAL"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    EVIDENCE_UNVERIFIED = "EVIDENCE_UNVERIFIED"
    POLICY_BRIDGE_UNAVAILABLE = "POLICY_BRIDGE_UNAVAILABLE"
    SHADOW_MODE_ONLY = "SHADOW_MODE_ONLY"
    UNKNOWN = "UNKNOWN"


_REASON_ORDER: dict[PathGovernanceDecisionReason, int] = {
    reason: index for index, reason in enumerate(PathGovernanceDecisionReason)
}


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


def _parse_shadow_decision(
    value: PathGovernanceShadowDecision | str,
) -> PathGovernanceShadowDecision:
    if isinstance(value, PathGovernanceShadowDecision):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceShadowDecision(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid shadow_decision: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="shadow_decision",
            ) from exc
    raise PathGovernanceError(
        "shadow_decision must be a string or PathGovernanceShadowDecision",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="shadow_decision",
    )


def _parse_decision_reason(
    value: PathGovernanceDecisionReason | str,
) -> PathGovernanceDecisionReason:
    if isinstance(value, PathGovernanceDecisionReason):
        return value
    if isinstance(value, str):
        try:
            return PathGovernanceDecisionReason(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid decision reason: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="decision_reasons",
            ) from exc
    raise PathGovernanceError(
        "decision_reasons entries must be strings or PathGovernanceDecisionReason",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="decision_reasons",
    )


def _parse_risk_level(
    value: PathSourceRiskLevel | str | None,
) -> PathSourceRiskLevel | None:
    if value is None:
        return None
    if isinstance(value, PathSourceRiskLevel):
        return value
    if isinstance(value, str):
        try:
            return PathSourceRiskLevel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid risk_level: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="risk_level",
            ) from exc
    raise PathGovernanceError(
        "risk_level must be a string, PathSourceRiskLevel, or None",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="risk_level",
    )


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


def _freeze_decision_reasons(
    decision_reasons: Sequence[PathGovernanceDecisionReason | str] | None,
) -> tuple[PathGovernanceDecisionReason, ...]:
    raw = () if decision_reasons is None else decision_reasons
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "decision_reasons must be a sequence",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="decision_reasons",
        )
    parsed = {_parse_decision_reason(item) for item in raw}
    return tuple(sorted(parsed, key=lambda item: _REASON_ORDER[item]))


def _build_path_identity(
    value: PathIdentity | Mapping[str, Any] | None,
) -> PathIdentity | None:
    if value is None:
        return None
    if isinstance(value, PathIdentity):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_identity must be a PathIdentity object or mapping",
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
            "source_identity must be a SourceIdentity object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="source_identity",
        )
    return SourceIdentity.from_dict(value)


def _build_trusted_root_registry(
    value: TrustedRootRegistry | Mapping[str, Any] | None,
) -> TrustedRootRegistry | None:
    if value is None:
        return None
    if isinstance(value, TrustedRootRegistry):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "trusted_root_registry must be a TrustedRootRegistry object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="trusted_root_registry",
        )
    return TrustedRootRegistry.from_dict(value)


def _build_boundary_check_result(
    value: PathBoundaryCheckResult | Mapping[str, Any] | None,
) -> PathBoundaryCheckResult | None:
    if value is None:
        return None
    if isinstance(value, PathBoundaryCheckResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "boundary_check_result must be a PathBoundaryCheckResult object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="boundary_check_result",
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
            "authority_scope must be a PathAuthorityScope object or mapping",
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
            "untrusted_boundary must be an UntrustedContentBoundary object or mapping",
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
            "provenance_binding must be a ProvenanceBinding object or mapping",
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
            "risk_classification must be a PathSourceRiskClassification object "
            "or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="risk_classification",
        )
    return PathSourceRiskClassification.from_dict(value)


def _input_payload(
    *,
    path_identity: PathIdentity | None,
    source_identity: SourceIdentity | None,
    trusted_root_registry: TrustedRootRegistry | None,
    boundary_check_result: PathBoundaryCheckResult | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    risk_classification: PathSourceRiskClassification | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authority_scope": (
            None if authority_scope is None else authority_scope.to_canonical_dict()
        ),
        "boundary_check_result": (
            None
            if boundary_check_result is None
            else boundary_check_result.to_canonical_dict()
        ),
        "metadata": _sorted_metadata_dict(metadata),
        "path_identity": (
            None if path_identity is None else path_identity.to_canonical_dict()
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
    }


def compute_path_governance_resolver_input_hash(
    *,
    path_identity: PathIdentity | None,
    source_identity: SourceIdentity | None,
    trusted_root_registry: TrustedRootRegistry | None,
    boundary_check_result: PathBoundaryCheckResult | None,
    authority_scope: PathAuthorityScope | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    risk_classification: PathSourceRiskClassification | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic shadow resolver input hash."""
    return stable_hash(_input_payload(
        path_identity=path_identity,
        source_identity=source_identity,
        trusted_root_registry=trusted_root_registry,
        boundary_check_result=boundary_check_result,
        authority_scope=authority_scope,
        untrusted_boundary=untrusted_boundary,
        provenance_binding=provenance_binding,
        risk_classification=risk_classification,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathGovernanceResolverInput:
    """Hash-ready shadow resolver input context; not authority or enforcement."""

    path_identity: PathIdentity | None = None
    source_identity: SourceIdentity | None = None
    trusted_root_registry: TrustedRootRegistry | None = None
    boundary_check_result: PathBoundaryCheckResult | None = None
    authority_scope: PathAuthorityScope | None = None
    untrusted_boundary: UntrustedContentBoundary | None = None
    provenance_binding: ProvenanceBinding | None = None
    risk_classification: PathSourceRiskClassification | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    input_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path_identity = _build_path_identity(self.path_identity)
        source_identity = _build_source_identity(self.source_identity)
        trusted_root_registry = _build_trusted_root_registry(
            self.trusted_root_registry,
        )
        boundary_check_result = _build_boundary_check_result(
            self.boundary_check_result,
        )
        authority_scope = _build_authority_scope(self.authority_scope)
        untrusted_boundary = _build_untrusted_boundary(self.untrusted_boundary)
        provenance_binding = _build_provenance_binding(self.provenance_binding)
        risk_classification = _build_risk_classification(self.risk_classification)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        input_hash = compute_path_governance_resolver_input_hash(
            path_identity=path_identity,
            source_identity=source_identity,
            trusted_root_registry=trusted_root_registry,
            boundary_check_result=boundary_check_result,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            source_label=source_label,
            metadata=metadata,
        )
        input_id = input_hash
        if self.input_id not in ("", input_id):
            raise PathGovernanceValidationError(
                "input_id does not match resolver input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match resolver input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "path_identity", path_identity)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "trusted_root_registry", trusted_root_registry)
        object.__setattr__(self, "boundary_check_result", boundary_check_result)
        object.__setattr__(self, "authority_scope", authority_scope)
        object.__setattr__(self, "untrusted_boundary", untrusted_boundary)
        object.__setattr__(self, "provenance_binding", provenance_binding)
        object.__setattr__(self, "risk_classification", risk_classification)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "input_hash", input_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _input_payload(
            path_identity=self.path_identity,
            source_identity=self.source_identity,
            trusted_root_registry=self.trusted_root_registry,
            boundary_check_result=self.boundary_check_result,
            authority_scope=self.authority_scope,
            untrusted_boundary=self.untrusted_boundary,
            provenance_binding=self.provenance_binding,
            risk_classification=self.risk_classification,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["input_hash"] = self.input_hash
        payload["input_id"] = self.input_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceResolverInput:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_RESOLVER_INPUT_KNOWN_FIELDS,
            label="path_governance_resolver_input",
        )
        return cls(
            path_identity=data.get("path_identity"),
            source_identity=data.get("source_identity"),
            trusted_root_registry=data.get("trusted_root_registry"),
            boundary_check_result=data.get("boundary_check_result"),
            authority_scope=data.get("authority_scope"),
            untrusted_boundary=data.get("untrusted_boundary"),
            provenance_binding=data.get("provenance_binding"),
            risk_classification=data.get("risk_classification"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            input_id=data.get("input_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


def compute_path_governance_resolver_result_id(
    *,
    input_id: str,
    shadow_decision: PathGovernanceShadowDecision,
    decision_reasons: tuple[PathGovernanceDecisionReason, ...],
    risk_level: PathSourceRiskLevel | None,
    resolver_version: str,
) -> str:
    """Compute deterministic shadow resolver result identifier."""
    return stable_hash({
        "decision_reasons": [item.value for item in decision_reasons],
        "input_id": input_id,
        "resolver_version": resolver_version,
        "risk_level": None if risk_level is None else risk_level.value,
        "shadow_decision": shadow_decision.value,
    })


def _result_payload(
    *,
    result_id: str,
    input_id: str,
    shadow_decision: PathGovernanceShadowDecision,
    decision_reasons: tuple[PathGovernanceDecisionReason, ...],
    risk_level: PathSourceRiskLevel | None,
    source_label: ProjectionSourceLabel,
    shadow_only: bool,
    enforced: bool,
    would_require_approval: bool,
    would_write_trace_later: bool,
    created_by_task: str,
    resolver_version: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "created_by_task": created_by_task,
        "decision_reasons": [item.value for item in decision_reasons],
        "enforced": enforced,
        "input_id": input_id,
        "metadata": _sorted_metadata_dict(metadata),
        "resolver_version": resolver_version,
        "result_id": result_id,
        "risk_level": None if risk_level is None else risk_level.value,
        "shadow_decision": shadow_decision.value,
        "shadow_only": shadow_only,
        "source_label": source_label.value,
        "would_require_approval": would_require_approval,
        "would_write_trace_later": would_write_trace_later,
    }


def compute_path_governance_resolver_result_hash(
    *,
    result_id: str,
    input_id: str,
    shadow_decision: PathGovernanceShadowDecision,
    decision_reasons: tuple[PathGovernanceDecisionReason, ...],
    risk_level: PathSourceRiskLevel | None,
    source_label: ProjectionSourceLabel,
    shadow_only: bool,
    enforced: bool,
    would_require_approval: bool,
    would_write_trace_later: bool,
    created_by_task: str,
    resolver_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic shadow resolver result hash."""
    return stable_hash(_result_payload(
        result_id=result_id,
        input_id=input_id,
        shadow_decision=shadow_decision,
        decision_reasons=decision_reasons,
        risk_level=risk_level,
        source_label=source_label,
        shadow_only=shadow_only,
        enforced=enforced,
        would_require_approval=would_require_approval,
        would_write_trace_later=would_write_trace_later,
        created_by_task=created_by_task,
        resolver_version=resolver_version,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathGovernanceResolverResult:
    """Shadow-only resolver result; recommended action is not runtime action."""

    input_id: str
    shadow_decision: PathGovernanceShadowDecision
    decision_reasons: tuple[PathGovernanceDecisionReason, ...]
    risk_level: PathSourceRiskLevel | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    shadow_only: bool = True
    enforced: bool = False
    would_require_approval: bool = False
    would_write_trace_later: bool = False
    result_id: str = ""
    result_hash: str = ""
    created_by_task: str = PATH_GOVERNANCE_RESOLVER_TASK_ID
    resolver_version: str = PATH_GOVERNANCE_RESOLVER_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.created_by_task != PATH_GOVERNANCE_RESOLVER_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.10",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        if self.resolver_version != PATH_GOVERNANCE_RESOLVER_VERSION:
            raise PathGovernanceValidationError(
                "resolver_version must be path_governance_resolver.v0.shadow",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="resolver_version",
            )
        if self.shadow_only is not True:
            raise PathGovernanceValidationError(
                "shadow_only must remain True for P1.7.10 resolver v0",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="shadow_only",
            )
        if self.enforced is not False:
            raise PathGovernanceValidationError(
                "enforced must remain False for P1.7.10 resolver v0",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="enforced",
            )
        input_id = _required_string(self.input_id, field_name="input_id")
        shadow_decision = _parse_shadow_decision(self.shadow_decision)
        decision_reasons = _freeze_decision_reasons(self.decision_reasons)
        risk_level = _parse_risk_level(self.risk_level)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        result_id = compute_path_governance_resolver_result_id(
            input_id=input_id,
            shadow_decision=shadow_decision,
            decision_reasons=decision_reasons,
            risk_level=risk_level,
            resolver_version=self.resolver_version,
        )
        if self.result_id not in ("", result_id):
            raise PathGovernanceValidationError(
                "result_id does not match resolver result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_id",
            )
        result_hash = compute_path_governance_resolver_result_hash(
            result_id=result_id,
            input_id=input_id,
            shadow_decision=shadow_decision,
            decision_reasons=decision_reasons,
            risk_level=risk_level,
            source_label=source_label,
            shadow_only=True,
            enforced=False,
            would_require_approval=self.would_require_approval,
            would_write_trace_later=self.would_write_trace_later,
            created_by_task=self.created_by_task,
            resolver_version=self.resolver_version,
            metadata=metadata,
        )
        if self.result_hash not in ("", result_hash):
            raise PathGovernanceValidationError(
                "result_hash does not match resolver result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_hash",
            )
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "shadow_decision", shadow_decision)
        object.__setattr__(self, "decision_reasons", decision_reasons)
        object.__setattr__(self, "risk_level", risk_level)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "shadow_only", True)
        object.__setattr__(self, "enforced", False)
        object.__setattr__(self, "result_id", result_id)
        object.__setattr__(self, "result_hash", result_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _result_payload(
            result_id=self.result_id,
            input_id=self.input_id,
            shadow_decision=self.shadow_decision,
            decision_reasons=self.decision_reasons,
            risk_level=self.risk_level,
            source_label=self.source_label,
            shadow_only=self.shadow_only,
            enforced=self.enforced,
            would_require_approval=self.would_require_approval,
            would_write_trace_later=self.would_write_trace_later,
            created_by_task=self.created_by_task,
            resolver_version=self.resolver_version,
            metadata=self.metadata,
        )
        payload["result_hash"] = self.result_hash
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathGovernanceResolverResult:
        validate_known_fields(
            data,
            PATH_GOVERNANCE_RESOLVER_RESULT_KNOWN_FIELDS,
            label="path_governance_resolver_result",
        )
        return cls(
            input_id=data["input_id"],
            shadow_decision=data["shadow_decision"],
            decision_reasons=tuple(data.get("decision_reasons", ())),
            risk_level=data.get("risk_level"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            shadow_only=data.get("shadow_only", True),
            enforced=data.get("enforced", False),
            would_require_approval=data.get("would_require_approval", False),
            would_write_trace_later=data.get("would_write_trace_later", False),
            result_id=data.get("result_id", ""),
            result_hash=data.get("result_hash", ""),
            created_by_task=data.get(
                "created_by_task",
                PATH_GOVERNANCE_RESOLVER_TASK_ID,
            ),
            resolver_version=data.get(
                "resolver_version",
                PATH_GOVERNANCE_RESOLVER_VERSION,
            ),
            metadata=data.get("metadata", {}),
        )


def _reason_tuple(
    reasons: set[PathGovernanceDecisionReason],
) -> tuple[PathGovernanceDecisionReason, ...]:
    return tuple(sorted(reasons, key=lambda item: _REASON_ORDER[item]))


def _risk_signal_kinds(
    risk_classification: PathSourceRiskClassification | None,
) -> set[PathSourceRiskSignalKind]:
    if risk_classification is None:
        return set()
    return {signal.signal_kind for signal in risk_classification.signals}


def _risk_bases(
    risk_classification: PathSourceRiskClassification | None,
) -> set[RiskClassificationBasis]:
    if risk_classification is None:
        return set()
    return {signal.basis for signal in risk_classification.signals}


def _trust_labels(
    resolver_input: PathGovernanceResolverInput,
) -> set[SourceTrustLabel]:
    labels: set[SourceTrustLabel] = set()
    if resolver_input.source_identity is not None:
        labels.add(resolver_input.source_identity.source_ref.trust_label)
    if resolver_input.untrusted_boundary is not None:
        labels.add(resolver_input.untrusted_boundary.trust_label)
    if (
        resolver_input.risk_classification is not None
        and resolver_input.risk_classification.trust_label is not None
    ):
        labels.add(resolver_input.risk_classification.trust_label)
    return labels


def _has_unverified_evidence(binding: ProvenanceBinding | None) -> bool:
    if binding is None:
        return False
    for evidence in binding.evidence_refs:
        if evidence.confidence in {
            EvidenceConfidence.UNVERIFIED,
            EvidenceConfidence.CONFLICTED,
            EvidenceConfidence.LOW,
        }:
            return True
    for claim in binding.claim_refs:
        if claim.confidence in {
            EvidenceConfidence.UNVERIFIED,
            EvidenceConfidence.CONFLICTED,
            EvidenceConfidence.LOW,
        }:
            return True
    return False


def _derive_reasons(
    resolver_input: PathGovernanceResolverInput,
) -> set[PathGovernanceDecisionReason]:
    reasons = {PathGovernanceDecisionReason.SHADOW_MODE_ONLY}
    trust_labels = _trust_labels(resolver_input)
    risk_signals = _risk_signal_kinds(resolver_input.risk_classification)
    risk_bases = _risk_bases(resolver_input.risk_classification)

    if trust_labels & _UNTRUSTED_TRUST_LABELS or {
        PathSourceRiskSignalKind.UNTRUSTED_SOURCE,
        PathSourceRiskSignalKind.QUARANTINED_SOURCE,
    } & risk_signals:
        reasons.add(PathGovernanceDecisionReason.SOURCE_TRUST_UNTRUSTED)
    elif trust_labels and trust_labels <= _ACCEPTABLE_TRUST_LABELS:
        reasons.add(PathGovernanceDecisionReason.SOURCE_TRUST_ACCEPTABLE)
    else:
        reasons.add(PathGovernanceDecisionReason.SOURCE_TRUST_UNKNOWN)

    boundary = resolver_input.boundary_check_result
    if boundary is not None:
        if boundary.boundary_status is PathBoundaryStatus.PATH_OK:
            reasons.add(PathGovernanceDecisionReason.PATH_WITHIN_DECLARED_ROOT)
        if boundary.boundary_status is PathBoundaryStatus.PATH_OUTSIDE_TRUSTED_ROOT:
            reasons.add(PathGovernanceDecisionReason.PATH_OUTSIDE_DECLARED_ROOT)
        if boundary.boundary_status is PathBoundaryStatus.PATH_TRAVERSAL_CANDIDATE:
            reasons.add(PathGovernanceDecisionReason.PATH_TRAVERSAL_CANDIDATE)
    if PathSourceRiskSignalKind.PATH_TRAVERSAL_SIGNAL in risk_signals:
        reasons.add(PathGovernanceDecisionReason.PATH_TRAVERSAL_CANDIDATE)
    if PathSourceRiskSignalKind.OUTSIDE_TRUSTED_ROOT_SIGNAL in risk_signals:
        reasons.add(PathGovernanceDecisionReason.PATH_OUTSIDE_DECLARED_ROOT)

    if (
        resolver_input.authority_scope is not None
        or (
            resolver_input.risk_classification is not None
            and resolver_input.risk_classification.authority_scope_id is not None
        )
    ):
        reasons.add(PathGovernanceDecisionReason.AUTHORITY_SCOPE_DECLARED)
    elif (
        RiskClassificationBasis.AUTHORITY_SCOPE in risk_bases
        or bool(risk_signals & _AUTHORITY_SIGNAL_KINDS)
    ):
        reasons.add(PathGovernanceDecisionReason.AUTHORITY_SCOPE_MISSING)
        reasons.add(PathGovernanceDecisionReason.POLICY_BRIDGE_UNAVAILABLE)

    if resolver_input.untrusted_boundary is not None:
        boundary_surfaces = set(resolver_input.untrusted_boundary.influence_surfaces)
        if (
            resolver_input.untrusted_boundary.trust_label in _UNTRUSTED_TRUST_LABELS
            or resolver_input.untrusted_boundary.posture
            is UntrustedBoundaryPosture.QUARANTINED
            or bool(boundary_surfaces & _COMMAND_SURFACES)
        ):
            reasons.add(PathGovernanceDecisionReason.UNTRUSTED_CONTENT_BOUNDARY)

    if resolver_input.risk_classification is not None:
        if resolver_input.risk_classification.risk_level is PathSourceRiskLevel.HIGH:
            reasons.add(PathGovernanceDecisionReason.RISK_CLASSIFICATION_HIGH)
        if resolver_input.risk_classification.risk_level is PathSourceRiskLevel.CRITICAL:
            reasons.add(PathGovernanceDecisionReason.RISK_CLASSIFICATION_CRITICAL)

    if (
        PathSourceRiskSignalKind.MISSING_PROVENANCE in risk_signals
        or (
            resolver_input.risk_classification is not None
            and resolver_input.risk_classification.provenance_binding_id is not None
            and resolver_input.provenance_binding is None
        )
    ):
        reasons.add(PathGovernanceDecisionReason.PROVENANCE_MISSING)
    if {
        PathSourceRiskSignalKind.UNVERIFIED_CLAIM,
        PathSourceRiskSignalKind.LOW_CONFIDENCE_EVIDENCE,
        PathSourceRiskSignalKind.CONFLICTED_EVIDENCE,
    } & risk_signals or _has_unverified_evidence(resolver_input.provenance_binding):
        reasons.add(PathGovernanceDecisionReason.EVIDENCE_UNVERIFIED)

    if (
        resolver_input.risk_classification is None
        and boundary is None
        and resolver_input.untrusted_boundary is None
        and not trust_labels
    ):
        reasons.add(PathGovernanceDecisionReason.UNKNOWN)

    return reasons


def _derive_shadow_decision(
    *,
    risk_level: PathSourceRiskLevel | None,
    reasons: set[PathGovernanceDecisionReason],
    resolver_input: PathGovernanceResolverInput,
) -> PathGovernanceShadowDecision:
    if PathGovernanceDecisionReason.AUTHORITY_SCOPE_MISSING in reasons:
        return PathGovernanceShadowDecision.WOULD_REQUIRE_POLICY_REVIEW
    if risk_level is PathSourceRiskLevel.CRITICAL:
        if (
            PathGovernanceDecisionReason.UNTRUSTED_CONTENT_BOUNDARY in reasons
            and resolver_input.untrusted_boundary is not None
            and (
                resolver_input.untrusted_boundary.posture
                is UntrustedBoundaryPosture.QUARANTINED
                or resolver_input.untrusted_boundary.trust_label
                is SourceTrustLabel.QUARANTINED
            )
        ):
            return PathGovernanceShadowDecision.WOULD_QUARANTINE
        return PathGovernanceShadowDecision.WOULD_DENY
    if PathGovernanceDecisionReason.PATH_TRAVERSAL_CANDIDATE in reasons:
        return PathGovernanceShadowDecision.WOULD_RESTRICT
    if PathGovernanceDecisionReason.PATH_OUTSIDE_DECLARED_ROOT in reasons:
        return PathGovernanceShadowDecision.WOULD_RESTRICT
    if risk_level is PathSourceRiskLevel.HIGH:
        return PathGovernanceShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW
    if risk_level is PathSourceRiskLevel.MEDIUM:
        return PathGovernanceShadowDecision.WOULD_REVIEW
    if PathGovernanceDecisionReason.PROVENANCE_MISSING in reasons:
        return PathGovernanceShadowDecision.WOULD_REVIEW
    if PathGovernanceDecisionReason.EVIDENCE_UNVERIFIED in reasons:
        return PathGovernanceShadowDecision.WOULD_REVIEW
    if PathGovernanceDecisionReason.UNTRUSTED_CONTENT_BOUNDARY in reasons:
        return PathGovernanceShadowDecision.WOULD_REVIEW
    if risk_level in {PathSourceRiskLevel.NONE, PathSourceRiskLevel.LOW}:
        if {
            PathGovernanceDecisionReason.AUTHORITY_SCOPE_DECLARED,
            PathGovernanceDecisionReason.PATH_WITHIN_DECLARED_ROOT,
            PathGovernanceDecisionReason.SOURCE_TRUST_ACCEPTABLE,
        } & reasons or risk_level is PathSourceRiskLevel.NONE:
            return PathGovernanceShadowDecision.WOULD_ALLOW
        return PathGovernanceShadowDecision.WOULD_REVIEW
    if risk_level is PathSourceRiskLevel.UNKNOWN:
        return PathGovernanceShadowDecision.WOULD_REVIEW
    return PathGovernanceShadowDecision.UNKNOWN


def _would_require_approval(decision: PathGovernanceShadowDecision) -> bool:
    return decision in {
        PathGovernanceShadowDecision.WOULD_RESTRICT,
        PathGovernanceShadowDecision.WOULD_DENY,
        PathGovernanceShadowDecision.WOULD_QUARANTINE,
        PathGovernanceShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW,
        PathGovernanceShadowDecision.WOULD_REQUIRE_POLICY_REVIEW,
    }


def _explicit_context_supplied(values: Sequence[Any]) -> bool:
    return any(item is not None for item in values)


def resolve_path_governance_shadow(
    resolver_input: PathGovernanceResolverInput | Mapping[str, Any] | None = None,
    *,
    path_identity: PathIdentity | Mapping[str, Any] | None = None,
    source_identity: SourceIdentity | Mapping[str, Any] | None = None,
    trusted_root_registry: TrustedRootRegistry | Mapping[str, Any] | None = None,
    boundary_check_result: PathBoundaryCheckResult | Mapping[str, Any] | None = None,
    authority_scope: PathAuthorityScope | Mapping[str, Any] | None = None,
    untrusted_boundary: UntrustedContentBoundary | Mapping[str, Any] | None = None,
    provenance_binding: ProvenanceBinding | Mapping[str, Any] | None = None,
    risk_classification: PathSourceRiskClassification | Mapping[str, Any] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathGovernanceResolverResult:
    """Resolve a non-enforcing path governance shadow recommendation."""
    if resolver_input is not None:
        if _explicit_context_supplied((
            path_identity,
            source_identity,
            trusted_root_registry,
            boundary_check_result,
            authority_scope,
            untrusted_boundary,
            provenance_binding,
            risk_classification,
            metadata,
        )):
            raise PathGovernanceValidationError(
                "resolver_input cannot be combined with explicit context pieces",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="resolver_input",
            )
        resolved_input = (
            resolver_input
            if isinstance(resolver_input, PathGovernanceResolverInput)
            else PathGovernanceResolverInput.from_dict(resolver_input)
        )
    else:
        resolved_input = PathGovernanceResolverInput(
            path_identity=path_identity,
            source_identity=source_identity,
            trusted_root_registry=trusted_root_registry,
            boundary_check_result=boundary_check_result,
            authority_scope=authority_scope,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            source_label=source_label,
            metadata=metadata,
        )

    risk_level = (
        None
        if resolved_input.risk_classification is None
        else resolved_input.risk_classification.risk_level
    )
    reasons = _derive_reasons(resolved_input)
    decision = _derive_shadow_decision(
        risk_level=risk_level,
        reasons=reasons,
        resolver_input=resolved_input,
    )
    return PathGovernanceResolverResult(
        input_id=resolved_input.input_id,
        shadow_decision=decision,
        decision_reasons=_reason_tuple(reasons),
        risk_level=risk_level,
        source_label=resolved_input.source_label,
        shadow_only=True,
        enforced=False,
        would_require_approval=_would_require_approval(decision),
        would_write_trace_later=True,
        metadata={
            "resolver_boundary": "shadow_only_not_enforced",
            "source_input_hash": resolved_input.input_hash,
        },
    )
