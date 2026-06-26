"""Source trust resolver v0 shadow recommendations (P1.7.11).

Source Trust Resolver v0 is shadow-only. WOULD_* trust recommendations are
not trust mutation, source blocking, quarantine action, approval activation,
trace writes, Ledger writes, memory canonization, or runtime action.
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
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .path_resolver import (
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
)
from .risk_classification import (
    PathSourceRiskClassification,
    PathSourceRiskLevel,
    PathSourceRiskSignalKind,
)
from .serialization import stable_hash
from .source_identity import SourceIdentity
from .source_provenance import EvidenceConfidence, ProvenanceBinding
from .source_trust_taxonomy import SourceTrustTaxonomy
from .untrusted_content_boundary import (
    ContentInfluenceSurface,
    UntrustedBoundaryPosture,
    UntrustedContentBoundary,
)
from .validation import validate_known_fields

SOURCE_TRUST_RESOLVER_TASK_ID = "P1.7.11"
SOURCE_TRUST_RESOLVER_VERSION = "source_trust_resolver.v0.shadow"

SOURCE_TRUST_RESOLVER_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "input_id",
    "source_identity",
    "source_trust_label",
    "source_trust_taxonomy",
    "untrusted_boundary",
    "provenance_binding",
    "risk_classification",
    "path_resolver_result",
    "source_label",
    "input_hash",
    "metadata",
})

SOURCE_TRUST_RESOLVER_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "result_id",
    "input_id",
    "shadow_decision",
    "decision_reasons",
    "recommended_trust_label",
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

_COMMAND_SURFACES: frozenset[ContentInfluenceSurface] = frozenset({
    ContentInfluenceSurface.PROMPT_INSTRUCTION,
    ContentInfluenceSurface.TOOL_ARGUMENT,
    ContentInfluenceSurface.MEMORY_WRITE,
    ContentInfluenceSurface.POLICY_DEFINITION,
    ContentInfluenceSurface.AUTHORITY_EXPANSION,
    ContentInfluenceSurface.EXECUTION_REQUEST,
    ContentInfluenceSurface.SOURCE_CANONIZATION,
})


class SourceTrustShadowDecision(str, Enum):
    """Shadow trust recommendation vocabulary; not source mutation."""

    WOULD_TRUST = "WOULD_TRUST"
    WOULD_REVIEW = "WOULD_REVIEW"
    WOULD_DISTRUST = "WOULD_DISTRUST"
    WOULD_QUARANTINE = "WOULD_QUARANTINE"
    WOULD_REQUIRE_OPERATOR_REVIEW = "WOULD_REQUIRE_OPERATOR_REVIEW"
    WOULD_REQUIRE_POLICY_REVIEW = "WOULD_REQUIRE_POLICY_REVIEW"
    UNKNOWN = "UNKNOWN"


class SourceTrustDecisionReason(str, Enum):
    """Deterministic explanation vocabulary for shadow trust recommendations."""

    SOURCE_IDENTITY_PRESENT = "SOURCE_IDENTITY_PRESENT"
    SOURCE_IDENTITY_MISSING = "SOURCE_IDENTITY_MISSING"
    SOURCE_LABEL_TRUSTED = "SOURCE_LABEL_TRUSTED"
    SOURCE_LABEL_UNTRUSTED = "SOURCE_LABEL_UNTRUSTED"
    SOURCE_LABEL_EXTERNAL = "SOURCE_LABEL_EXTERNAL"
    SOURCE_LABEL_UNKNOWN = "SOURCE_LABEL_UNKNOWN"
    SOURCE_LABEL_QUARANTINED = "SOURCE_LABEL_QUARANTINED"
    BOUNDARY_INFORM_ONLY = "BOUNDARY_INFORM_ONLY"
    BOUNDARY_RESTRICTS_COMMAND = "BOUNDARY_RESTRICTS_COMMAND"
    PROVENANCE_PRESENT = "PROVENANCE_PRESENT"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    EVIDENCE_UNVERIFIED = "EVIDENCE_UNVERIFIED"
    EVIDENCE_CONFLICTED = "EVIDENCE_CONFLICTED"
    RISK_CLASSIFICATION_LOW = "RISK_CLASSIFICATION_LOW"
    RISK_CLASSIFICATION_MEDIUM = "RISK_CLASSIFICATION_MEDIUM"
    RISK_CLASSIFICATION_HIGH = "RISK_CLASSIFICATION_HIGH"
    RISK_CLASSIFICATION_CRITICAL = "RISK_CLASSIFICATION_CRITICAL"
    PATH_RESOLVER_WOULD_ALLOW = "PATH_RESOLVER_WOULD_ALLOW"
    PATH_RESOLVER_WOULD_REVIEW = "PATH_RESOLVER_WOULD_REVIEW"
    PATH_RESOLVER_WOULD_RESTRICT = "PATH_RESOLVER_WOULD_RESTRICT"
    PATH_RESOLVER_WOULD_DENY = "PATH_RESOLVER_WOULD_DENY"
    POLICY_BRIDGE_UNAVAILABLE = "POLICY_BRIDGE_UNAVAILABLE"
    SHADOW_MODE_ONLY = "SHADOW_MODE_ONLY"
    UNKNOWN = "UNKNOWN"


_REASON_ORDER: dict[SourceTrustDecisionReason, int] = {
    reason: index for index, reason in enumerate(SourceTrustDecisionReason)
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


def _parse_trust_label(value: SourceTrustLabel | str) -> SourceTrustLabel:
    if isinstance(value, SourceTrustLabel):
        return value
    if isinstance(value, str):
        try:
            return SourceTrustLabel(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_trust_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
                field="source_trust_label",
            ) from exc
    raise PathGovernanceError(
        "source_trust_label must be a string or SourceTrustLabel",
        code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
        field="source_trust_label",
    )


def _parse_optional_trust_label(
    value: SourceTrustLabel | str | None,
) -> SourceTrustLabel | None:
    if value is None:
        return None
    return _parse_trust_label(value)


def _parse_shadow_decision(
    value: SourceTrustShadowDecision | str,
) -> SourceTrustShadowDecision:
    if isinstance(value, SourceTrustShadowDecision):
        return value
    if isinstance(value, str):
        try:
            return SourceTrustShadowDecision(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid shadow_decision: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="shadow_decision",
            ) from exc
    raise PathGovernanceError(
        "shadow_decision must be a string or SourceTrustShadowDecision",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="shadow_decision",
    )


def _parse_decision_reason(
    value: SourceTrustDecisionReason | str,
) -> SourceTrustDecisionReason:
    if isinstance(value, SourceTrustDecisionReason):
        return value
    if isinstance(value, str):
        try:
            return SourceTrustDecisionReason(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid decision reason: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="decision_reasons",
            ) from exc
    raise PathGovernanceError(
        "decision_reasons entries must be strings or SourceTrustDecisionReason",
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
    decision_reasons: Sequence[SourceTrustDecisionReason | str] | None,
) -> tuple[SourceTrustDecisionReason, ...]:
    raw = () if decision_reasons is None else decision_reasons
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "decision_reasons must be a sequence",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="decision_reasons",
        )
    parsed = {_parse_decision_reason(item) for item in raw}
    return tuple(sorted(parsed, key=lambda item: _REASON_ORDER[item]))


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


def _build_source_trust_taxonomy(
    value: SourceTrustTaxonomy | Mapping[str, Any] | None,
) -> SourceTrustTaxonomy | None:
    if value is None:
        return None
    if isinstance(value, SourceTrustTaxonomy):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "source_trust_taxonomy must be a SourceTrustTaxonomy object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="source_trust_taxonomy",
        )
    return SourceTrustTaxonomy.from_dict(value)


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


def _build_path_resolver_result(
    value: PathGovernanceResolverResult | Mapping[str, Any] | None,
) -> PathGovernanceResolverResult | None:
    if value is None:
        return None
    if isinstance(value, PathGovernanceResolverResult):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_resolver_result must be a PathGovernanceResolverResult object "
            "or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="path_resolver_result",
        )
    return PathGovernanceResolverResult.from_dict(value)


def _input_payload(
    *,
    source_identity: SourceIdentity | None,
    source_trust_label: SourceTrustLabel | None,
    source_trust_taxonomy: SourceTrustTaxonomy | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    risk_classification: PathSourceRiskClassification | None,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
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
        "source_identity": (
            None if source_identity is None else source_identity.to_canonical_dict()
        ),
        "source_label": source_label.value,
        "source_trust_label": (
            None if source_trust_label is None else source_trust_label.value
        ),
        "source_trust_taxonomy": (
            None
            if source_trust_taxonomy is None
            else source_trust_taxonomy.to_canonical_dict()
        ),
        "untrusted_boundary": (
            None
            if untrusted_boundary is None
            else untrusted_boundary.to_canonical_dict()
        ),
    }


def compute_source_trust_resolver_input_hash(
    *,
    source_identity: SourceIdentity | None,
    source_trust_label: SourceTrustLabel | None,
    source_trust_taxonomy: SourceTrustTaxonomy | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    risk_classification: PathSourceRiskClassification | None,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic source trust shadow resolver input hash."""
    return stable_hash(_input_payload(
        source_identity=source_identity,
        source_trust_label=source_trust_label,
        source_trust_taxonomy=source_trust_taxonomy,
        untrusted_boundary=untrusted_boundary,
        provenance_binding=provenance_binding,
        risk_classification=risk_classification,
        path_resolver_result=path_resolver_result,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class SourceTrustResolverInput:
    """Hash-ready shadow trust resolver input; not trust authority."""

    source_identity: SourceIdentity | None = None
    source_trust_label: SourceTrustLabel | None = None
    source_trust_taxonomy: SourceTrustTaxonomy | None = None
    untrusted_boundary: UntrustedContentBoundary | None = None
    provenance_binding: ProvenanceBinding | None = None
    risk_classification: PathSourceRiskClassification | None = None
    path_resolver_result: PathGovernanceResolverResult | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    input_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_identity = _build_source_identity(self.source_identity)
        source_trust_label = _parse_optional_trust_label(self.source_trust_label)
        source_trust_taxonomy = _build_source_trust_taxonomy(
            self.source_trust_taxonomy,
        )
        untrusted_boundary = _build_untrusted_boundary(self.untrusted_boundary)
        provenance_binding = _build_provenance_binding(self.provenance_binding)
        risk_classification = _build_risk_classification(self.risk_classification)
        path_resolver_result = _build_path_resolver_result(self.path_resolver_result)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        input_hash = compute_source_trust_resolver_input_hash(
            source_identity=source_identity,
            source_trust_label=source_trust_label,
            source_trust_taxonomy=source_trust_taxonomy,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            path_resolver_result=path_resolver_result,
            source_label=source_label,
            metadata=metadata,
        )
        input_id = input_hash
        if self.input_id not in ("", input_id):
            raise PathGovernanceValidationError(
                "input_id does not match source trust resolver input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match source trust resolver input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "source_trust_label", source_trust_label)
        object.__setattr__(self, "source_trust_taxonomy", source_trust_taxonomy)
        object.__setattr__(self, "untrusted_boundary", untrusted_boundary)
        object.__setattr__(self, "provenance_binding", provenance_binding)
        object.__setattr__(self, "risk_classification", risk_classification)
        object.__setattr__(self, "path_resolver_result", path_resolver_result)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "input_hash", input_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _input_payload(
            source_identity=self.source_identity,
            source_trust_label=self.source_trust_label,
            source_trust_taxonomy=self.source_trust_taxonomy,
            untrusted_boundary=self.untrusted_boundary,
            provenance_binding=self.provenance_binding,
            risk_classification=self.risk_classification,
            path_resolver_result=self.path_resolver_result,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["input_hash"] = self.input_hash
        payload["input_id"] = self.input_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceTrustResolverInput:
        validate_known_fields(
            data,
            SOURCE_TRUST_RESOLVER_INPUT_KNOWN_FIELDS,
            label="source_trust_resolver_input",
        )
        return cls(
            source_identity=data.get("source_identity"),
            source_trust_label=data.get("source_trust_label"),
            source_trust_taxonomy=data.get("source_trust_taxonomy"),
            untrusted_boundary=data.get("untrusted_boundary"),
            provenance_binding=data.get("provenance_binding"),
            risk_classification=data.get("risk_classification"),
            path_resolver_result=data.get("path_resolver_result"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            input_id=data.get("input_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


def compute_source_trust_resolver_result_id(
    *,
    input_id: str,
    shadow_decision: SourceTrustShadowDecision,
    decision_reasons: tuple[SourceTrustDecisionReason, ...],
    recommended_trust_label: SourceTrustLabel | None,
    risk_level: PathSourceRiskLevel | None,
    resolver_version: str,
) -> str:
    """Compute deterministic source trust shadow resolver result identifier."""
    return stable_hash({
        "decision_reasons": [item.value for item in decision_reasons],
        "input_id": input_id,
        "recommended_trust_label": (
            None if recommended_trust_label is None else recommended_trust_label.value
        ),
        "resolver_version": resolver_version,
        "risk_level": None if risk_level is None else risk_level.value,
        "shadow_decision": shadow_decision.value,
    })


def _result_payload(
    *,
    result_id: str,
    input_id: str,
    shadow_decision: SourceTrustShadowDecision,
    decision_reasons: tuple[SourceTrustDecisionReason, ...],
    recommended_trust_label: SourceTrustLabel | None,
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
        "recommended_trust_label": (
            None if recommended_trust_label is None else recommended_trust_label.value
        ),
        "resolver_version": resolver_version,
        "result_id": result_id,
        "risk_level": None if risk_level is None else risk_level.value,
        "shadow_decision": shadow_decision.value,
        "shadow_only": shadow_only,
        "source_label": source_label.value,
        "would_require_approval": would_require_approval,
        "would_write_trace_later": would_write_trace_later,
    }


def compute_source_trust_resolver_result_hash(
    *,
    result_id: str,
    input_id: str,
    shadow_decision: SourceTrustShadowDecision,
    decision_reasons: tuple[SourceTrustDecisionReason, ...],
    recommended_trust_label: SourceTrustLabel | None,
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
    """Compute deterministic source trust shadow resolver result hash."""
    return stable_hash(_result_payload(
        result_id=result_id,
        input_id=input_id,
        shadow_decision=shadow_decision,
        decision_reasons=decision_reasons,
        recommended_trust_label=recommended_trust_label,
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
class SourceTrustResolverResult:
    """Shadow-only trust result; recommendation is not trust mutation."""

    input_id: str
    shadow_decision: SourceTrustShadowDecision
    decision_reasons: tuple[SourceTrustDecisionReason, ...]
    recommended_trust_label: SourceTrustLabel | None = None
    risk_level: PathSourceRiskLevel | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    shadow_only: bool = True
    enforced: bool = False
    would_require_approval: bool = False
    would_write_trace_later: bool = False
    result_id: str = ""
    result_hash: str = ""
    created_by_task: str = SOURCE_TRUST_RESOLVER_TASK_ID
    resolver_version: str = SOURCE_TRUST_RESOLVER_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.created_by_task != SOURCE_TRUST_RESOLVER_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.11",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        if self.resolver_version != SOURCE_TRUST_RESOLVER_VERSION:
            raise PathGovernanceValidationError(
                "resolver_version must be source_trust_resolver.v0.shadow",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="resolver_version",
            )
        if self.shadow_only is not True:
            raise PathGovernanceValidationError(
                "shadow_only must remain True for P1.7.11 resolver v0",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="shadow_only",
            )
        if self.enforced is not False:
            raise PathGovernanceValidationError(
                "enforced must remain False for P1.7.11 resolver v0",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="enforced",
            )
        input_id = _required_string(self.input_id, field_name="input_id")
        shadow_decision = _parse_shadow_decision(self.shadow_decision)
        decision_reasons = _freeze_decision_reasons(self.decision_reasons)
        recommended_trust_label = _parse_optional_trust_label(
            self.recommended_trust_label,
        )
        risk_level = _parse_risk_level(self.risk_level)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        result_id = compute_source_trust_resolver_result_id(
            input_id=input_id,
            shadow_decision=shadow_decision,
            decision_reasons=decision_reasons,
            recommended_trust_label=recommended_trust_label,
            risk_level=risk_level,
            resolver_version=self.resolver_version,
        )
        if self.result_id not in ("", result_id):
            raise PathGovernanceValidationError(
                "result_id does not match source trust resolver result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_id",
            )
        result_hash = compute_source_trust_resolver_result_hash(
            result_id=result_id,
            input_id=input_id,
            shadow_decision=shadow_decision,
            decision_reasons=decision_reasons,
            recommended_trust_label=recommended_trust_label,
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
                "result_hash does not match source trust resolver result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_hash",
            )
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "shadow_decision", shadow_decision)
        object.__setattr__(self, "decision_reasons", decision_reasons)
        object.__setattr__(
            self,
            "recommended_trust_label",
            recommended_trust_label,
        )
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
            recommended_trust_label=self.recommended_trust_label,
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
    def from_dict(cls, data: Mapping[str, Any]) -> SourceTrustResolverResult:
        validate_known_fields(
            data,
            SOURCE_TRUST_RESOLVER_RESULT_KNOWN_FIELDS,
            label="source_trust_resolver_result",
        )
        return cls(
            input_id=data["input_id"],
            shadow_decision=data["shadow_decision"],
            decision_reasons=tuple(data.get("decision_reasons", ())),
            recommended_trust_label=data.get("recommended_trust_label"),
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
                SOURCE_TRUST_RESOLVER_TASK_ID,
            ),
            resolver_version=data.get(
                "resolver_version",
                SOURCE_TRUST_RESOLVER_VERSION,
            ),
            metadata=data.get("metadata", {}),
        )


def _reason_tuple(
    reasons: set[SourceTrustDecisionReason],
) -> tuple[SourceTrustDecisionReason, ...]:
    return tuple(sorted(reasons, key=lambda item: _REASON_ORDER[item]))


def _risk_signal_kinds(
    risk_classification: PathSourceRiskClassification | None,
) -> set[PathSourceRiskSignalKind]:
    if risk_classification is None:
        return set()
    return {signal.signal_kind for signal in risk_classification.signals}


def _effective_trust_label(
    resolver_input: SourceTrustResolverInput,
) -> SourceTrustLabel | None:
    if resolver_input.source_trust_label is not None:
        return resolver_input.source_trust_label
    if resolver_input.source_identity is not None:
        return resolver_input.source_identity.source_ref.trust_label
    if resolver_input.untrusted_boundary is not None:
        return resolver_input.untrusted_boundary.trust_label
    if (
        resolver_input.risk_classification is not None
        and resolver_input.risk_classification.trust_label is not None
    ):
        return resolver_input.risk_classification.trust_label
    return None


def _has_unverified_evidence(binding: ProvenanceBinding | None) -> bool:
    if binding is None:
        return False
    for evidence in binding.evidence_refs:
        if evidence.confidence in {
            EvidenceConfidence.UNVERIFIED,
            EvidenceConfidence.LOW,
        }:
            return True
    for claim in binding.claim_refs:
        if claim.confidence in {
            EvidenceConfidence.UNVERIFIED,
            EvidenceConfidence.LOW,
        }:
            return True
    return False


def _has_conflicted_evidence(binding: ProvenanceBinding | None) -> bool:
    if binding is None:
        return False
    for evidence in binding.evidence_refs:
        if evidence.confidence is EvidenceConfidence.CONFLICTED:
            return True
    for claim in binding.claim_refs:
        if claim.confidence is EvidenceConfidence.CONFLICTED:
            return True
    return False


def _derive_reasons(
    resolver_input: SourceTrustResolverInput,
) -> set[SourceTrustDecisionReason]:
    reasons = {SourceTrustDecisionReason.SHADOW_MODE_ONLY}
    risk_signals = _risk_signal_kinds(resolver_input.risk_classification)
    trust_label = _effective_trust_label(resolver_input)

    if resolver_input.source_identity is None:
        reasons.add(SourceTrustDecisionReason.SOURCE_IDENTITY_MISSING)
    else:
        reasons.add(SourceTrustDecisionReason.SOURCE_IDENTITY_PRESENT)

    if trust_label is SourceTrustLabel.TRUSTED:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_TRUSTED)
    elif trust_label is SourceTrustLabel.EXTERNAL:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_EXTERNAL)
    elif trust_label is SourceTrustLabel.UNTRUSTED:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_UNTRUSTED)
    elif trust_label is SourceTrustLabel.QUARANTINED:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_QUARANTINED)
    elif trust_label is None or trust_label is SourceTrustLabel.UNKNOWN:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_UNKNOWN)

    if PathSourceRiskSignalKind.EXTERNAL_SOURCE in risk_signals:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_EXTERNAL)
    if PathSourceRiskSignalKind.UNTRUSTED_SOURCE in risk_signals:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_UNTRUSTED)
    if PathSourceRiskSignalKind.QUARANTINED_SOURCE in risk_signals:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_QUARANTINED)
    if PathSourceRiskSignalKind.UNKNOWN_SOURCE in risk_signals:
        reasons.add(SourceTrustDecisionReason.SOURCE_LABEL_UNKNOWN)

    boundary = resolver_input.untrusted_boundary
    if boundary is not None:
        if boundary.posture in {
            UntrustedBoundaryPosture.INFORM_ONLY,
            UntrustedBoundaryPosture.QUOTABLE,
            UntrustedBoundaryPosture.SUMMARIZABLE,
        }:
            reasons.add(SourceTrustDecisionReason.BOUNDARY_INFORM_ONLY)
        if (
            bool(set(boundary.influence_surfaces) & _COMMAND_SURFACES)
            or boundary.posture
            in {
                UntrustedBoundaryPosture.REVIEW_REQUIRED,
                UntrustedBoundaryPosture.QUARANTINED,
            }
        ):
            reasons.add(SourceTrustDecisionReason.BOUNDARY_RESTRICTS_COMMAND)

    if resolver_input.provenance_binding is None:
        reasons.add(SourceTrustDecisionReason.PROVENANCE_MISSING)
    else:
        reasons.add(SourceTrustDecisionReason.PROVENANCE_PRESENT)

    if (
        PathSourceRiskSignalKind.MISSING_PROVENANCE in risk_signals
        or (
            resolver_input.risk_classification is not None
            and resolver_input.risk_classification.provenance_binding_id is not None
            and resolver_input.provenance_binding is None
        )
    ):
        reasons.add(SourceTrustDecisionReason.PROVENANCE_MISSING)
        reasons.discard(SourceTrustDecisionReason.PROVENANCE_PRESENT)

    if {
        PathSourceRiskSignalKind.UNVERIFIED_CLAIM,
        PathSourceRiskSignalKind.LOW_CONFIDENCE_EVIDENCE,
    } & risk_signals or _has_unverified_evidence(resolver_input.provenance_binding):
        reasons.add(SourceTrustDecisionReason.EVIDENCE_UNVERIFIED)
    if (
        PathSourceRiskSignalKind.CONFLICTED_EVIDENCE in risk_signals
        or _has_conflicted_evidence(resolver_input.provenance_binding)
    ):
        reasons.add(SourceTrustDecisionReason.EVIDENCE_CONFLICTED)
        reasons.add(SourceTrustDecisionReason.POLICY_BRIDGE_UNAVAILABLE)

    if resolver_input.risk_classification is not None:
        risk_level = resolver_input.risk_classification.risk_level
        if risk_level in {PathSourceRiskLevel.NONE, PathSourceRiskLevel.LOW}:
            reasons.add(SourceTrustDecisionReason.RISK_CLASSIFICATION_LOW)
        elif risk_level is PathSourceRiskLevel.MEDIUM:
            reasons.add(SourceTrustDecisionReason.RISK_CLASSIFICATION_MEDIUM)
        elif risk_level is PathSourceRiskLevel.HIGH:
            reasons.add(SourceTrustDecisionReason.RISK_CLASSIFICATION_HIGH)
        elif risk_level is PathSourceRiskLevel.CRITICAL:
            reasons.add(SourceTrustDecisionReason.RISK_CLASSIFICATION_CRITICAL)

    path_result = resolver_input.path_resolver_result
    if path_result is not None:
        if path_result.shadow_decision is PathGovernanceShadowDecision.WOULD_ALLOW:
            reasons.add(SourceTrustDecisionReason.PATH_RESOLVER_WOULD_ALLOW)
        elif path_result.shadow_decision is PathGovernanceShadowDecision.WOULD_REVIEW:
            reasons.add(SourceTrustDecisionReason.PATH_RESOLVER_WOULD_REVIEW)
        elif path_result.shadow_decision in {
            PathGovernanceShadowDecision.WOULD_RESTRICT,
            PathGovernanceShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW,
        }:
            reasons.add(SourceTrustDecisionReason.PATH_RESOLVER_WOULD_RESTRICT)
        elif path_result.shadow_decision in {
            PathGovernanceShadowDecision.WOULD_DENY,
            PathGovernanceShadowDecision.WOULD_QUARANTINE,
        }:
            reasons.add(SourceTrustDecisionReason.PATH_RESOLVER_WOULD_DENY)

    if (
        resolver_input.source_identity is None
        and trust_label is None
        and resolver_input.untrusted_boundary is None
        and resolver_input.provenance_binding is None
        and resolver_input.risk_classification is None
        and resolver_input.path_resolver_result is None
    ):
        reasons.add(SourceTrustDecisionReason.UNKNOWN)

    return reasons


def _derive_shadow_decision(
    *,
    risk_level: PathSourceRiskLevel | None,
    reasons: set[SourceTrustDecisionReason],
) -> SourceTrustShadowDecision:
    if SourceTrustDecisionReason.SOURCE_LABEL_QUARANTINED in reasons:
        return SourceTrustShadowDecision.WOULD_QUARANTINE
    if SourceTrustDecisionReason.EVIDENCE_CONFLICTED in reasons:
        return SourceTrustShadowDecision.WOULD_REQUIRE_POLICY_REVIEW
    if risk_level is PathSourceRiskLevel.CRITICAL:
        return SourceTrustShadowDecision.WOULD_DISTRUST
    if SourceTrustDecisionReason.PATH_RESOLVER_WOULD_DENY in reasons:
        return SourceTrustShadowDecision.WOULD_DISTRUST
    if (
        risk_level is PathSourceRiskLevel.HIGH
        or SourceTrustDecisionReason.PATH_RESOLVER_WOULD_RESTRICT in reasons
    ):
        return SourceTrustShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW
    if (
        SourceTrustDecisionReason.SOURCE_LABEL_UNTRUSTED in reasons
        and SourceTrustDecisionReason.BOUNDARY_RESTRICTS_COMMAND in reasons
    ):
        return SourceTrustShadowDecision.WOULD_DISTRUST
    if risk_level is PathSourceRiskLevel.MEDIUM:
        return SourceTrustShadowDecision.WOULD_REVIEW
    if (
        SourceTrustDecisionReason.SOURCE_LABEL_EXTERNAL in reasons
        or SourceTrustDecisionReason.SOURCE_LABEL_UNTRUSTED in reasons
        or SourceTrustDecisionReason.PROVENANCE_MISSING in reasons
        or SourceTrustDecisionReason.EVIDENCE_UNVERIFIED in reasons
        or SourceTrustDecisionReason.PATH_RESOLVER_WOULD_REVIEW in reasons
    ):
        return SourceTrustShadowDecision.WOULD_REVIEW
    if (
        SourceTrustDecisionReason.SOURCE_LABEL_TRUSTED in reasons
        and SourceTrustDecisionReason.PROVENANCE_PRESENT in reasons
        and (
            SourceTrustDecisionReason.RISK_CLASSIFICATION_LOW in reasons
            or risk_level is None
        )
    ):
        return SourceTrustShadowDecision.WOULD_TRUST
    if SourceTrustDecisionReason.UNKNOWN in reasons:
        return SourceTrustShadowDecision.UNKNOWN
    return SourceTrustShadowDecision.WOULD_REVIEW


def _recommended_trust_label(
    *,
    decision: SourceTrustShadowDecision,
    effective_trust_label: SourceTrustLabel | None,
) -> SourceTrustLabel:
    if decision is SourceTrustShadowDecision.WOULD_TRUST:
        return SourceTrustLabel.TRUSTED
    if decision is SourceTrustShadowDecision.WOULD_DISTRUST:
        return SourceTrustLabel.UNTRUSTED
    if decision is SourceTrustShadowDecision.WOULD_QUARANTINE:
        return SourceTrustLabel.QUARANTINED
    if effective_trust_label is not None:
        return effective_trust_label
    return SourceTrustLabel.UNKNOWN


def _would_require_approval(decision: SourceTrustShadowDecision) -> bool:
    return decision in {
        SourceTrustShadowDecision.WOULD_DISTRUST,
        SourceTrustShadowDecision.WOULD_QUARANTINE,
        SourceTrustShadowDecision.WOULD_REQUIRE_OPERATOR_REVIEW,
        SourceTrustShadowDecision.WOULD_REQUIRE_POLICY_REVIEW,
    }


def _explicit_context_supplied(values: Sequence[Any]) -> bool:
    return any(item is not None for item in values)


def resolve_source_trust_shadow(
    resolver_input: SourceTrustResolverInput | Mapping[str, Any] | None = None,
    *,
    source_identity: SourceIdentity | Mapping[str, Any] | None = None,
    source_trust_label: SourceTrustLabel | str | None = None,
    source_trust_taxonomy: SourceTrustTaxonomy | Mapping[str, Any] | None = None,
    untrusted_boundary: UntrustedContentBoundary | Mapping[str, Any] | None = None,
    provenance_binding: ProvenanceBinding | Mapping[str, Any] | None = None,
    risk_classification: PathSourceRiskClassification | Mapping[str, Any] | None = None,
    path_resolver_result: PathGovernanceResolverResult | Mapping[str, Any] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> SourceTrustResolverResult:
    """Resolve a non-mutating source trust shadow recommendation."""
    if resolver_input is not None:
        if _explicit_context_supplied((
            source_identity,
            source_trust_label,
            source_trust_taxonomy,
            untrusted_boundary,
            provenance_binding,
            risk_classification,
            path_resolver_result,
            metadata,
        )):
            raise PathGovernanceValidationError(
                "resolver_input cannot be combined with explicit context pieces",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="resolver_input",
            )
        resolved_input = (
            resolver_input
            if isinstance(resolver_input, SourceTrustResolverInput)
            else SourceTrustResolverInput.from_dict(resolver_input)
        )
    else:
        resolved_input = SourceTrustResolverInput(
            source_identity=source_identity,
            source_trust_label=source_trust_label,
            source_trust_taxonomy=source_trust_taxonomy,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            risk_classification=risk_classification,
            path_resolver_result=path_resolver_result,
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
    )
    recommended_label = _recommended_trust_label(
        decision=decision,
        effective_trust_label=_effective_trust_label(resolved_input),
    )
    return SourceTrustResolverResult(
        input_id=resolved_input.input_id,
        shadow_decision=decision,
        decision_reasons=_reason_tuple(reasons),
        recommended_trust_label=recommended_label,
        risk_level=risk_level,
        source_label=resolved_input.source_label,
        shadow_only=True,
        enforced=False,
        would_require_approval=_would_require_approval(decision),
        would_write_trace_later=True,
        metadata={
            "recommended_trust_label_advisory_only": True,
            "resolver_boundary": "shadow_only_not_mutating",
            "source_input_hash": resolved_input.input_hash,
        },
    )
