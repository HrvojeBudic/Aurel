"""Path/source conflict and precedence shadow rules (P1.7.12).

Conflict detection is not conflict enforcement. Precedence rules are not runtime
authority. Strictest-wins recommendations are shadow-only.
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
from .labels import ProjectionSourceLabel
from .path_authority_scope import PathAuthorityScope
from .path_resolver import (
    PathGovernanceResolverResult,
    PathGovernanceShadowDecision,
)
from .risk_classification import (
    PathSourceRiskClassification,
    PathSourceRiskLevel,
)
from .serialization import stable_hash
from .source_provenance import EvidenceConfidence, ProvenanceBinding
from .source_trust_resolver import (
    SourceTrustResolverResult,
    SourceTrustShadowDecision,
)
from .untrusted_content_boundary import (
    ContentInfluenceSurface,
    UntrustedBoundaryPosture,
    UntrustedContentBoundary,
)
from .validation import validate_known_fields

CONFLICT_PRECEDENCE_TASK_ID = "P1.7.12"
CONFLICT_PRECEDENCE_VERSION = "path_source_conflict_precedence.v0.shadow"

PATH_SOURCE_CONFLICT_SIGNAL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "signal_id",
    "conflict_kind",
    "severity",
    "reason",
    "source_label",
    "metadata",
})

PRECEDENCE_RULE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "rule_id",
    "rule_kind",
    "applies_to",
    "severity",
    "recommended_posture",
    "reason",
    "source_label",
    "metadata",
})

CONFLICT_PRECEDENCE_INPUT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "input_id",
    "path_resolver_result",
    "source_trust_resolver_result",
    "risk_classification",
    "untrusted_boundary",
    "provenance_binding",
    "authority_scope",
    "source_label",
    "input_hash",
    "metadata",
})

CONFLICT_PRECEDENCE_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "result_id",
    "input_id",
    "conflict_signals",
    "precedence_rules",
    "final_shadow_posture",
    "recommended_shadow_decision",
    "source_label",
    "shadow_only",
    "enforced",
    "would_require_operator_review",
    "would_require_policy_review",
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

_SHADOW_STRICTNESS: dict[str, int] = {
    "WOULD_QUARANTINE": 1,
    "WOULD_DENY": 2,
    "WOULD_DISTRUST": 3,
    "WOULD_RESTRICT": 4,
    "WOULD_REQUIRE_OPERATOR_REVIEW": 5,
    "WOULD_REQUIRE_POLICY_REVIEW": 6,
    "WOULD_REVIEW": 7,
    "WOULD_TRUST": 8,
    "WOULD_ALLOW": 8,
    "UNKNOWN": 9,
}

class PathSourceConflictKind(str, Enum):
    """Conflict classification; does not resolve or enforce."""

    PATH_SOURCE_DECISION_MISMATCH = "PATH_SOURCE_DECISION_MISMATCH"
    PATH_WOULD_ALLOW_SOURCE_WOULD_DISTRUST = "PATH_WOULD_ALLOW_SOURCE_WOULD_DISTRUST"
    PATH_WOULD_ALLOW_SOURCE_WOULD_QUARANTINE = (
        "PATH_WOULD_ALLOW_SOURCE_WOULD_QUARANTINE"
    )
    PATH_WOULD_ALLOW_RISK_HIGH = "PATH_WOULD_ALLOW_RISK_HIGH"
    PATH_WOULD_ALLOW_RISK_CRITICAL = "PATH_WOULD_ALLOW_RISK_CRITICAL"
    SOURCE_WOULD_TRUST_PATH_WOULD_DENY = "SOURCE_WOULD_TRUST_PATH_WOULD_DENY"
    SOURCE_WOULD_TRUST_PATH_WOULD_RESTRICT = "SOURCE_WOULD_TRUST_PATH_WOULD_RESTRICT"
    AUTHORITY_SCOPE_MISSING = "AUTHORITY_SCOPE_MISSING"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    EVIDENCE_CONFLICTED = "EVIDENCE_CONFLICTED"
    UNTRUSTED_BOUNDARY_COMMAND_SURFACE = "UNTRUSTED_BOUNDARY_COMMAND_SURFACE"
    UNKNOWN = "UNKNOWN"


class PrecedenceRuleKind(str, Enum):
    """Precedence recommendation vocabulary; does not apply runtime action."""

    STRICTEST_WINS_SHADOW = "STRICTEST_WINS_SHADOW"
    REVIEW_ON_CONFLICT = "REVIEW_ON_CONFLICT"
    POLICY_REVIEW_ON_UNKNOWN = "POLICY_REVIEW_ON_UNKNOWN"
    OPERATOR_REVIEW_ON_HIGH_RISK = "OPERATOR_REVIEW_ON_HIGH_RISK"
    QUARANTINE_RECOMMENDED_ON_CRITICAL = "QUARANTINE_RECOMMENDED_ON_CRITICAL"
    SOURCE_DISTRUST_OVERRIDES_PATH_ALLOW = "SOURCE_DISTRUST_OVERRIDES_PATH_ALLOW"
    PATH_DENY_OVERRIDES_SOURCE_TRUST = "PATH_DENY_OVERRIDES_SOURCE_TRUST"
    MISSING_PROVENANCE_REQUIRES_REVIEW = "MISSING_PROVENANCE_REQUIRES_REVIEW"
    CONFLICTED_EVIDENCE_REQUIRES_POLICY_REVIEW = (
        "CONFLICTED_EVIDENCE_REQUIRES_POLICY_REVIEW"
    )
    UNKNOWN = "UNKNOWN"


class ConflictSeverity(str, Enum):
    """Conflict severity marker; does not block or enforce."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ConflictPrecedencePosture(str, Enum):
    """Conflict posture recommendation; not runtime action."""

    NO_CONFLICT = "NO_CONFLICT"
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    OPERATOR_REVIEW_RECOMMENDED = "OPERATOR_REVIEW_RECOMMENDED"
    POLICY_REVIEW_RECOMMENDED = "POLICY_REVIEW_RECOMMENDED"
    RESTRICT_RECOMMENDED = "RESTRICT_RECOMMENDED"
    QUARANTINE_RECOMMENDED = "QUARANTINE_RECOMMENDED"
    UNKNOWN = "UNKNOWN"


_POSTURE_STRICTNESS: dict[ConflictPrecedencePosture, int] = {
    ConflictPrecedencePosture.QUARANTINE_RECOMMENDED: 1,
    ConflictPrecedencePosture.RESTRICT_RECOMMENDED: 2,
    ConflictPrecedencePosture.POLICY_REVIEW_RECOMMENDED: 3,
    ConflictPrecedencePosture.OPERATOR_REVIEW_RECOMMENDED: 4,
    ConflictPrecedencePosture.REVIEW_RECOMMENDED: 5,
    ConflictPrecedencePosture.INFORMATIONAL: 6,
    ConflictPrecedencePosture.NO_CONFLICT: 7,
    ConflictPrecedencePosture.UNKNOWN: 8,
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


def _parse_conflict_kind(
    value: PathSourceConflictKind | str,
) -> PathSourceConflictKind:
    if isinstance(value, PathSourceConflictKind):
        return value
    if isinstance(value, str):
        try:
            return PathSourceConflictKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid conflict_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="conflict_kind",
            ) from exc
    raise PathGovernanceError(
        "conflict_kind must be a string or PathSourceConflictKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="conflict_kind",
    )


def _parse_rule_kind(value: PrecedenceRuleKind | str) -> PrecedenceRuleKind:
    if isinstance(value, PrecedenceRuleKind):
        return value
    if isinstance(value, str):
        try:
            return PrecedenceRuleKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid rule_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="rule_kind",
            ) from exc
    raise PathGovernanceError(
        "rule_kind must be a string or PrecedenceRuleKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="rule_kind",
    )


def _parse_severity(value: ConflictSeverity | str) -> ConflictSeverity:
    if isinstance(value, ConflictSeverity):
        return value
    if isinstance(value, str):
        try:
            return ConflictSeverity(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid severity: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="severity",
            ) from exc
    raise PathGovernanceError(
        "severity must be a string or ConflictSeverity",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="severity",
    )


def _parse_posture(value: ConflictPrecedencePosture | str) -> ConflictPrecedencePosture:
    if isinstance(value, ConflictPrecedencePosture):
        return value
    if isinstance(value, str):
        try:
            return ConflictPrecedencePosture(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid recommended_posture: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="recommended_posture",
            ) from exc
    raise PathGovernanceError(
        "recommended_posture must be a string or ConflictPrecedencePosture",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="recommended_posture",
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


def _validate_shadow_decision(value: str) -> str:
    decision = _required_string(value, field_name="recommended_shadow_decision")
    forbidden_bare = {
        "ALLOW",
        "DENY",
        "BLOCK",
        "TRUST",
        "DISTRUST",
        "ENFORCE",
        "APPROVED",
        "QUARANTINE_NOW",
    }
    if decision in forbidden_bare:
        raise PathGovernanceValidationError(
            "recommended_shadow_decision must use WOULD_* advisory vocabulary",
            code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
            field="recommended_shadow_decision",
        )
    if decision == "UNKNOWN" or decision.startswith("WOULD_"):
        return decision
    raise PathGovernanceValidationError(
        "recommended_shadow_decision must be WOULD_* or UNKNOWN",
        code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
        field="recommended_shadow_decision",
    )


def _normalize_applies_to(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(str(item) for item in value)
    raise PathGovernanceValidationError(
        "applies_to must be a string or sequence of strings",
        code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
        field="applies_to",
    )


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


def _signal_id_payload(
    *,
    conflict_kind: PathSourceConflictKind,
    severity: ConflictSeverity,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "conflict_kind": conflict_kind.value,
        "metadata": _sorted_metadata_dict(metadata),
        "reason": reason,
        "severity": severity.value,
        "source_label": source_label.value,
    }


def compute_conflict_signal_id(
    *,
    conflict_kind: PathSourceConflictKind,
    severity: ConflictSeverity,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic conflict signal identifier."""
    return stable_hash(_signal_id_payload(
        conflict_kind=conflict_kind,
        severity=severity,
        reason=reason,
        source_label=source_label,
        metadata=metadata,
    ))


def _rule_id_payload(
    *,
    rule_kind: PrecedenceRuleKind,
    applies_to: tuple[str, ...],
    severity: ConflictSeverity,
    recommended_posture: ConflictPrecedencePosture,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "applies_to": list(applies_to),
        "metadata": _sorted_metadata_dict(metadata),
        "reason": reason,
        "recommended_posture": recommended_posture.value,
        "rule_kind": rule_kind.value,
        "severity": severity.value,
        "source_label": source_label.value,
    }


def compute_precedence_rule_id(
    *,
    rule_kind: PrecedenceRuleKind,
    applies_to: tuple[str, ...],
    severity: ConflictSeverity,
    recommended_posture: ConflictPrecedencePosture,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic precedence rule identifier."""
    return stable_hash(_rule_id_payload(
        rule_kind=rule_kind,
        applies_to=applies_to,
        severity=severity,
        recommended_posture=recommended_posture,
        reason=reason,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class PathSourceConflictSignal:
    """Shadow conflict signal; classification only, not enforcement."""

    conflict_kind: PathSourceConflictKind
    severity: ConflictSeverity
    reason: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    signal_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        conflict_kind = _parse_conflict_kind(self.conflict_kind)
        severity = _parse_severity(self.severity)
        reason = _required_string(self.reason, field_name="reason")
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        signal_id = compute_conflict_signal_id(
            conflict_kind=conflict_kind,
            severity=severity,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.signal_id not in ("", signal_id):
            raise PathGovernanceValidationError(
                "signal_id does not match conflict signal content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="signal_id",
            )
        object.__setattr__(self, "conflict_kind", conflict_kind)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "signal_id", signal_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _signal_id_payload(
            conflict_kind=self.conflict_kind,
            severity=self.severity,
            reason=self.reason,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["signal_id"] = self.signal_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathSourceConflictSignal:
        validate_known_fields(
            data,
            PATH_SOURCE_CONFLICT_SIGNAL_KNOWN_FIELDS,
            label="path_source_conflict_signal",
        )
        return cls(
            conflict_kind=data["conflict_kind"],
            severity=data["severity"],
            reason=data["reason"],
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            signal_id=data.get("signal_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PrecedenceRule:
    """Shadow precedence rule; recommends future handling only."""

    rule_kind: PrecedenceRuleKind
    applies_to: tuple[str, ...]
    severity: ConflictSeverity
    recommended_posture: ConflictPrecedencePosture
    reason: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    rule_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        rule_kind = _parse_rule_kind(self.rule_kind)
        applies_to = _normalize_applies_to(self.applies_to)
        severity = _parse_severity(self.severity)
        recommended_posture = _parse_posture(self.recommended_posture)
        reason = _required_string(self.reason, field_name="reason")
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        rule_id = compute_precedence_rule_id(
            rule_kind=rule_kind,
            applies_to=applies_to,
            severity=severity,
            recommended_posture=recommended_posture,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.rule_id not in ("", rule_id):
            raise PathGovernanceValidationError(
                "rule_id does not match precedence rule content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="rule_id",
            )
        object.__setattr__(self, "rule_kind", rule_kind)
        object.__setattr__(self, "applies_to", applies_to)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "recommended_posture", recommended_posture)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _rule_id_payload(
            rule_kind=self.rule_kind,
            applies_to=self.applies_to,
            severity=self.severity,
            recommended_posture=self.recommended_posture,
            reason=self.reason,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["rule_id"] = self.rule_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PrecedenceRule:
        validate_known_fields(
            data,
            PRECEDENCE_RULE_KNOWN_FIELDS,
            label="precedence_rule",
        )
        return cls(
            rule_kind=data["rule_kind"],
            applies_to=tuple(data.get("applies_to", ())),
            severity=data["severity"],
            recommended_posture=data["recommended_posture"],
            reason=data["reason"],
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            rule_id=data.get("rule_id", ""),
            metadata=data.get("metadata", {}),
        )


def _input_payload(
    *,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_resolver_result: SourceTrustResolverResult | None,
    risk_classification: PathSourceRiskClassification | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    authority_scope: PathAuthorityScope | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authority_scope": (
            None if authority_scope is None else authority_scope.to_canonical_dict()
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


def compute_conflict_precedence_input_hash(
    *,
    path_resolver_result: PathGovernanceResolverResult | None,
    source_trust_resolver_result: SourceTrustResolverResult | None,
    risk_classification: PathSourceRiskClassification | None,
    untrusted_boundary: UntrustedContentBoundary | None,
    provenance_binding: ProvenanceBinding | None,
    authority_scope: PathAuthorityScope | None,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic conflict precedence input hash."""
    return stable_hash(_input_payload(
        path_resolver_result=path_resolver_result,
        source_trust_resolver_result=source_trust_resolver_result,
        risk_classification=risk_classification,
        untrusted_boundary=untrusted_boundary,
        provenance_binding=provenance_binding,
        authority_scope=authority_scope,
        source_label=source_label,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class ConflictPrecedenceInput:
    """Hash-ready conflict precedence input; not enforcement authority."""

    path_resolver_result: PathGovernanceResolverResult | None = None
    source_trust_resolver_result: SourceTrustResolverResult | None = None
    risk_classification: PathSourceRiskClassification | None = None
    untrusted_boundary: UntrustedContentBoundary | None = None
    provenance_binding: ProvenanceBinding | None = None
    authority_scope: PathAuthorityScope | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    input_id: str = ""
    input_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path_resolver_result = _build_path_resolver_result(self.path_resolver_result)
        source_trust_resolver_result = _build_source_trust_resolver_result(
            self.source_trust_resolver_result,
        )
        risk_classification = _build_risk_classification(self.risk_classification)
        untrusted_boundary = _build_untrusted_boundary(self.untrusted_boundary)
        provenance_binding = _build_provenance_binding(self.provenance_binding)
        authority_scope = _build_authority_scope(self.authority_scope)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        input_hash = compute_conflict_precedence_input_hash(
            path_resolver_result=path_resolver_result,
            source_trust_resolver_result=source_trust_resolver_result,
            risk_classification=risk_classification,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            source_label=source_label,
            metadata=metadata,
        )
        input_id = input_hash
        if self.input_id not in ("", input_id):
            raise PathGovernanceValidationError(
                "input_id does not match conflict precedence input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_id",
            )
        if self.input_hash not in ("", input_hash):
            raise PathGovernanceValidationError(
                "input_hash does not match conflict precedence input content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="input_hash",
            )
        object.__setattr__(self, "path_resolver_result", path_resolver_result)
        object.__setattr__(self, "source_trust_resolver_result", source_trust_resolver_result)
        object.__setattr__(self, "risk_classification", risk_classification)
        object.__setattr__(self, "untrusted_boundary", untrusted_boundary)
        object.__setattr__(self, "provenance_binding", provenance_binding)
        object.__setattr__(self, "authority_scope", authority_scope)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "input_hash", input_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = _input_payload(
            path_resolver_result=self.path_resolver_result,
            source_trust_resolver_result=self.source_trust_resolver_result,
            risk_classification=self.risk_classification,
            untrusted_boundary=self.untrusted_boundary,
            provenance_binding=self.provenance_binding,
            authority_scope=self.authority_scope,
            source_label=self.source_label,
            metadata=self.metadata,
        )
        payload["input_hash"] = self.input_hash
        payload["input_id"] = self.input_id
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConflictPrecedenceInput:
        validate_known_fields(
            data,
            CONFLICT_PRECEDENCE_INPUT_KNOWN_FIELDS,
            label="conflict_precedence_input",
        )
        return cls(
            path_resolver_result=data.get("path_resolver_result"),
            source_trust_resolver_result=data.get("source_trust_resolver_result"),
            risk_classification=data.get("risk_classification"),
            untrusted_boundary=data.get("untrusted_boundary"),
            provenance_binding=data.get("provenance_binding"),
            authority_scope=data.get("authority_scope"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            input_id=data.get("input_id", ""),
            input_hash=data.get("input_hash", ""),
            metadata=data.get("metadata", {}),
        )


def compute_conflict_precedence_result_id(
    *,
    input_id: str,
    conflict_signals: tuple[PathSourceConflictSignal, ...],
    precedence_rules: tuple[PrecedenceRule, ...],
    final_shadow_posture: ConflictPrecedencePosture,
    recommended_shadow_decision: str,
    resolver_version: str,
) -> str:
    """Compute deterministic conflict precedence result identifier."""
    return stable_hash({
        "conflict_signal_ids": [item.signal_id for item in conflict_signals],
        "final_shadow_posture": final_shadow_posture.value,
        "input_id": input_id,
        "precedence_rule_ids": [item.rule_id for item in precedence_rules],
        "recommended_shadow_decision": recommended_shadow_decision,
        "resolver_version": resolver_version,
    })


def _result_payload(
    *,
    result_id: str,
    input_id: str,
    conflict_signals: tuple[PathSourceConflictSignal, ...],
    precedence_rules: tuple[PrecedenceRule, ...],
    final_shadow_posture: ConflictPrecedencePosture,
    recommended_shadow_decision: str,
    source_label: ProjectionSourceLabel,
    shadow_only: bool,
    enforced: bool,
    would_require_operator_review: bool,
    would_require_policy_review: bool,
    would_write_trace_later: bool,
    created_by_task: str,
    resolver_version: str,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "conflict_signals": [
            item.to_canonical_dict() for item in conflict_signals
        ],
        "created_by_task": created_by_task,
        "enforced": enforced,
        "final_shadow_posture": final_shadow_posture.value,
        "input_id": input_id,
        "metadata": _sorted_metadata_dict(metadata),
        "precedence_rules": [item.to_canonical_dict() for item in precedence_rules],
        "recommended_shadow_decision": recommended_shadow_decision,
        "resolver_version": resolver_version,
        "result_id": result_id,
        "shadow_only": shadow_only,
        "source_label": source_label.value,
        "would_require_operator_review": would_require_operator_review,
        "would_require_policy_review": would_require_policy_review,
        "would_write_trace_later": would_write_trace_later,
    }


def compute_conflict_precedence_result_hash(
    *,
    result_id: str,
    input_id: str,
    conflict_signals: tuple[PathSourceConflictSignal, ...],
    precedence_rules: tuple[PrecedenceRule, ...],
    final_shadow_posture: ConflictPrecedencePosture,
    recommended_shadow_decision: str,
    source_label: ProjectionSourceLabel,
    shadow_only: bool,
    enforced: bool,
    would_require_operator_review: bool,
    would_require_policy_review: bool,
    would_write_trace_later: bool,
    created_by_task: str,
    resolver_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic conflict precedence result hash."""
    return stable_hash(_result_payload(
        result_id=result_id,
        input_id=input_id,
        conflict_signals=conflict_signals,
        precedence_rules=precedence_rules,
        final_shadow_posture=final_shadow_posture,
        recommended_shadow_decision=recommended_shadow_decision,
        source_label=source_label,
        shadow_only=shadow_only,
        enforced=enforced,
        would_require_operator_review=would_require_operator_review,
        would_require_policy_review=would_require_policy_review,
        would_write_trace_later=would_write_trace_later,
        created_by_task=created_by_task,
        resolver_version=resolver_version,
        metadata=metadata,
    ))


@dataclass(frozen=True)
class ConflictPrecedenceResult:
    """Shadow-only conflict/precedence result; not runtime enforcement."""

    input_id: str
    conflict_signals: tuple[PathSourceConflictSignal, ...]
    precedence_rules: tuple[PrecedenceRule, ...]
    final_shadow_posture: ConflictPrecedencePosture
    recommended_shadow_decision: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    shadow_only: bool = True
    enforced: bool = False
    would_require_operator_review: bool = False
    would_require_policy_review: bool = False
    would_write_trace_later: bool = False
    result_id: str = ""
    result_hash: str = ""
    created_by_task: str = CONFLICT_PRECEDENCE_TASK_ID
    resolver_version: str = CONFLICT_PRECEDENCE_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.created_by_task != CONFLICT_PRECEDENCE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.12",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        if self.resolver_version != CONFLICT_PRECEDENCE_VERSION:
            raise PathGovernanceValidationError(
                "resolver_version must be path_source_conflict_precedence.v0.shadow",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="resolver_version",
            )
        if self.shadow_only is not True:
            raise PathGovernanceValidationError(
                "shadow_only must remain True for P1.7.12 conflict precedence v0",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="shadow_only",
            )
        if self.enforced is not False:
            raise PathGovernanceValidationError(
                "enforced must remain False for P1.7.12 conflict precedence v0",
                code=PathGovernanceErrorCode.ENFORCEMENT_NOT_AVAILABLE,
                field="enforced",
            )
        input_id = _required_string(self.input_id, field_name="input_id")
        conflict_signals = _freeze_signals(self.conflict_signals)
        precedence_rules = _freeze_rules(self.precedence_rules)
        final_shadow_posture = _parse_posture(self.final_shadow_posture)
        recommended_shadow_decision = _validate_shadow_decision(
            self.recommended_shadow_decision,
        )
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        result_id = compute_conflict_precedence_result_id(
            input_id=input_id,
            conflict_signals=conflict_signals,
            precedence_rules=precedence_rules,
            final_shadow_posture=final_shadow_posture,
            recommended_shadow_decision=recommended_shadow_decision,
            resolver_version=self.resolver_version,
        )
        if self.result_id not in ("", result_id):
            raise PathGovernanceValidationError(
                "result_id does not match conflict precedence result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_id",
            )
        result_hash = compute_conflict_precedence_result_hash(
            result_id=result_id,
            input_id=input_id,
            conflict_signals=conflict_signals,
            precedence_rules=precedence_rules,
            final_shadow_posture=final_shadow_posture,
            recommended_shadow_decision=recommended_shadow_decision,
            source_label=source_label,
            shadow_only=True,
            enforced=False,
            would_require_operator_review=self.would_require_operator_review,
            would_require_policy_review=self.would_require_policy_review,
            would_write_trace_later=self.would_write_trace_later,
            created_by_task=self.created_by_task,
            resolver_version=self.resolver_version,
            metadata=metadata,
        )
        if self.result_hash not in ("", result_hash):
            raise PathGovernanceValidationError(
                "result_hash does not match conflict precedence result content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="result_hash",
            )
        object.__setattr__(self, "input_id", input_id)
        object.__setattr__(self, "conflict_signals", conflict_signals)
        object.__setattr__(self, "precedence_rules", precedence_rules)
        object.__setattr__(self, "final_shadow_posture", final_shadow_posture)
        object.__setattr__(
            self,
            "recommended_shadow_decision",
            recommended_shadow_decision,
        )
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
            conflict_signals=self.conflict_signals,
            precedence_rules=self.precedence_rules,
            final_shadow_posture=self.final_shadow_posture,
            recommended_shadow_decision=self.recommended_shadow_decision,
            source_label=self.source_label,
            shadow_only=self.shadow_only,
            enforced=self.enforced,
            would_require_operator_review=self.would_require_operator_review,
            would_require_policy_review=self.would_require_policy_review,
            would_write_trace_later=self.would_write_trace_later,
            created_by_task=self.created_by_task,
            resolver_version=self.resolver_version,
            metadata=self.metadata,
        )
        payload["result_hash"] = self.result_hash
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConflictPrecedenceResult:
        validate_known_fields(
            data,
            CONFLICT_PRECEDENCE_RESULT_KNOWN_FIELDS,
            label="conflict_precedence_result",
        )
        raw_signals = data.get("conflict_signals", ())
        raw_rules = data.get("precedence_rules", ())
        return cls(
            input_id=data["input_id"],
            conflict_signals=tuple(
                PathSourceConflictSignal.from_dict(item)
                if isinstance(item, MappingABC)
                else item
                for item in raw_signals
            ),
            precedence_rules=tuple(
                PrecedenceRule.from_dict(item)
                if isinstance(item, MappingABC)
                else item
                for item in raw_rules
            ),
            final_shadow_posture=data["final_shadow_posture"],
            recommended_shadow_decision=data["recommended_shadow_decision"],
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            shadow_only=data.get("shadow_only", True),
            enforced=data.get("enforced", False),
            would_require_operator_review=data.get(
                "would_require_operator_review",
                False,
            ),
            would_require_policy_review=data.get("would_require_policy_review", False),
            would_write_trace_later=data.get("would_write_trace_later", False),
            result_id=data.get("result_id", ""),
            result_hash=data.get("result_hash", ""),
            created_by_task=data.get("created_by_task", CONFLICT_PRECEDENCE_TASK_ID),
            resolver_version=data.get("resolver_version", CONFLICT_PRECEDENCE_VERSION),
            metadata=data.get("metadata", {}),
        )


def _freeze_signals(
    signals: Sequence[PathSourceConflictSignal | Mapping[str, Any]],
) -> tuple[PathSourceConflictSignal, ...]:
    parsed = [
        item if isinstance(item, PathSourceConflictSignal)
        else PathSourceConflictSignal.from_dict(item)
        for item in signals
    ]
    return tuple(sorted(parsed, key=lambda item: item.signal_id))


def _freeze_rules(
    rules: Sequence[PrecedenceRule | Mapping[str, Any]],
) -> tuple[PrecedenceRule, ...]:
    parsed = [
        item if isinstance(item, PrecedenceRule)
        else PrecedenceRule.from_dict(item)
        for item in rules
    ]
    return tuple(sorted(parsed, key=lambda item: item.rule_id))


def _decision_value(
    path_result: PathGovernanceResolverResult | None,
    source_result: SourceTrustResolverResult | None,
) -> tuple[str | None, str | None]:
    path_value = (
        None
        if path_result is None
        else path_result.shadow_decision.value
    )
    source_value = (
        None
        if source_result is None
        else source_result.shadow_decision.value
    )
    return path_value, source_value


def _strictest_decision(*decisions: str | None) -> str:
    candidates = [item for item in decisions if item is not None]
    if not candidates:
        return "UNKNOWN"
    return min(
        candidates,
        key=lambda item: _SHADOW_STRICTNESS.get(item, 9),
    )


def _strictest_posture(
    postures: set[ConflictPrecedencePosture],
) -> ConflictPrecedencePosture:
    if not postures:
        return ConflictPrecedencePosture.NO_CONFLICT
    return min(postures, key=lambda item: _POSTURE_STRICTNESS[item])


def _is_permissive_path(decision: PathGovernanceShadowDecision | None) -> bool:
    if decision is None:
        return False
    return decision is PathGovernanceShadowDecision.WOULD_ALLOW


def _is_permissive_source(decision: SourceTrustShadowDecision | None) -> bool:
    if decision is None:
        return False
    return decision is SourceTrustShadowDecision.WOULD_TRUST


def _both_permissive(
    path_result: PathGovernanceResolverResult | None,
    source_result: SourceTrustResolverResult | None,
) -> bool:
    path_decision = None if path_result is None else path_result.shadow_decision
    source_decision = None if source_result is None else source_result.shadow_decision
    if path_decision is not None and source_decision is not None:
        return _is_permissive_path(path_decision) and _is_permissive_source(
            source_decision,
        )
    if path_decision is not None:
        return _is_permissive_path(path_decision)
    if source_decision is not None:
        return _is_permissive_source(source_decision)
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


def _boundary_restricts_command_surface(
    boundary: UntrustedContentBoundary | None,
) -> bool:
    if boundary is None:
        return False
    surfaces = set(boundary.influence_surfaces)
    if bool(surfaces & _COMMAND_SURFACES):
        return True
    return boundary.posture in {
        UntrustedBoundaryPosture.REVIEW_REQUIRED,
        UntrustedBoundaryPosture.QUARANTINED,
    }


def _make_signal(
    *,
    conflict_kind: PathSourceConflictKind,
    severity: ConflictSeverity,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any] | None = None,
) -> PathSourceConflictSignal:
    return PathSourceConflictSignal(
        conflict_kind=conflict_kind,
        severity=severity,
        reason=reason,
        source_label=source_label,
        metadata=metadata or {},
    )


def _make_rule(
    *,
    rule_kind: PrecedenceRuleKind,
    applies_to: tuple[str, ...],
    severity: ConflictSeverity,
    recommended_posture: ConflictPrecedencePosture,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any] | None = None,
) -> PrecedenceRule:
    return PrecedenceRule(
        rule_kind=rule_kind,
        applies_to=applies_to,
        severity=severity,
        recommended_posture=recommended_posture,
        reason=reason,
        source_label=source_label,
        metadata=metadata or {},
    )


def _derive_conflict_and_rules(
    conflict_input: ConflictPrecedenceInput,
) -> tuple[
    list[PathSourceConflictSignal],
    list[PrecedenceRule],
    set[ConflictPrecedencePosture],
    bool,
    bool,
]:
    signals: list[PathSourceConflictSignal] = []
    rules: list[PrecedenceRule] = []
    postures: set[ConflictPrecedencePosture] = set()
    would_require_operator_review = False
    would_require_policy_review = False
    source_label = conflict_input.source_label

    path_result = conflict_input.path_resolver_result
    source_result = conflict_input.source_trust_resolver_result
    path_decision = None if path_result is None else path_result.shadow_decision
    source_decision = None if source_result is None else source_result.shadow_decision
    path_value, source_value = _decision_value(path_result, source_result)

    if path_result is not None and source_result is not None:
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.STRICTEST_WINS_SHADOW,
            applies_to=(
                PathSourceConflictKind.PATH_SOURCE_DECISION_MISMATCH.value,
            ),
            severity=ConflictSeverity.MEDIUM,
            recommended_posture=ConflictPrecedencePosture.REVIEW_RECOMMENDED,
            reason="Strictest shadow recommendation wins in shadow precedence model",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.REVIEW_RECOMMENDED)
        if path_value != source_value:
            signals.append(_make_signal(
                conflict_kind=PathSourceConflictKind.PATH_SOURCE_DECISION_MISMATCH,
                severity=ConflictSeverity.MEDIUM,
                reason="Path and source shadow recommendations differ materially",
                source_label=source_label,
            ))
            postures.add(ConflictPrecedencePosture.REVIEW_RECOMMENDED)

    if (
        path_decision is PathGovernanceShadowDecision.WOULD_ALLOW
        and source_decision is SourceTrustShadowDecision.WOULD_DISTRUST
    ):
        kind = PathSourceConflictKind.PATH_WOULD_ALLOW_SOURCE_WOULD_DISTRUST
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.HIGH,
            reason="Path resolver would allow while source trust resolver would distrust",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.SOURCE_DISTRUST_OVERRIDES_PATH_ALLOW,
            applies_to=(kind.value,),
            severity=ConflictSeverity.HIGH,
            recommended_posture=ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
            reason="Source distrust shadow result overrides path would-allow",
            source_label=source_label,
        ))
        postures.update({
            ConflictPrecedencePosture.REVIEW_RECOMMENDED,
            ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
        })

    if (
        path_decision is PathGovernanceShadowDecision.WOULD_ALLOW
        and source_decision is SourceTrustShadowDecision.WOULD_QUARANTINE
    ):
        kind = PathSourceConflictKind.PATH_WOULD_ALLOW_SOURCE_WOULD_QUARANTINE
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.CRITICAL,
            reason="Path resolver would allow while source trust resolver would quarantine",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.QUARANTINE_RECOMMENDED_ON_CRITICAL,
            applies_to=(kind.value,),
            severity=ConflictSeverity.CRITICAL,
            recommended_posture=ConflictPrecedencePosture.QUARANTINE_RECOMMENDED,
            reason="Source quarantine shadow result overrides path would-allow",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.QUARANTINE_RECOMMENDED)

    if (
        source_decision is SourceTrustShadowDecision.WOULD_TRUST
        and path_decision is PathGovernanceShadowDecision.WOULD_DENY
    ):
        kind = PathSourceConflictKind.SOURCE_WOULD_TRUST_PATH_WOULD_DENY
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.HIGH,
            reason="Source trust resolver would trust while path resolver would deny",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.PATH_DENY_OVERRIDES_SOURCE_TRUST,
            applies_to=(kind.value,),
            severity=ConflictSeverity.HIGH,
            recommended_posture=ConflictPrecedencePosture.POLICY_REVIEW_RECOMMENDED,
            reason="Path would-deny shadow result overrides source would-trust",
            source_label=source_label,
        ))
        postures.update({
            ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
            ConflictPrecedencePosture.POLICY_REVIEW_RECOMMENDED,
        })
        would_require_policy_review = True

    if (
        source_decision is SourceTrustShadowDecision.WOULD_TRUST
        and path_decision is PathGovernanceShadowDecision.WOULD_RESTRICT
    ):
        kind = PathSourceConflictKind.SOURCE_WOULD_TRUST_PATH_WOULD_RESTRICT
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.MEDIUM,
            reason="Source trust resolver would trust while path resolver would restrict",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.PATH_DENY_OVERRIDES_SOURCE_TRUST,
            applies_to=(kind.value,),
            severity=ConflictSeverity.MEDIUM,
            recommended_posture=ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
            reason="Path would-restrict shadow result overrides source would-trust",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.RESTRICT_RECOMMENDED)

    risk_level = (
        None
        if conflict_input.risk_classification is None
        else conflict_input.risk_classification.risk_level
    )
    if _both_permissive(path_result, source_result) and risk_level is PathSourceRiskLevel.HIGH:
        kind = PathSourceConflictKind.PATH_WOULD_ALLOW_RISK_HIGH
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.HIGH,
            reason="Permissive path/source shadow recommendations with high risk",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.OPERATOR_REVIEW_ON_HIGH_RISK,
            applies_to=(kind.value,),
            severity=ConflictSeverity.HIGH,
            recommended_posture=ConflictPrecedencePosture.OPERATOR_REVIEW_RECOMMENDED,
            reason="High risk recommends future operator review",
            source_label=source_label,
        ))
        postures.update({
            ConflictPrecedencePosture.OPERATOR_REVIEW_RECOMMENDED,
            ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
        })
        would_require_operator_review = True

    if (
        _both_permissive(path_result, source_result)
        and risk_level is PathSourceRiskLevel.CRITICAL
    ):
        kind = PathSourceConflictKind.PATH_WOULD_ALLOW_RISK_CRITICAL
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.CRITICAL,
            reason="Permissive path/source shadow recommendations with critical risk",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.QUARANTINE_RECOMMENDED_ON_CRITICAL,
            applies_to=(kind.value,),
            severity=ConflictSeverity.CRITICAL,
            recommended_posture=ConflictPrecedencePosture.QUARANTINE_RECOMMENDED,
            reason="Critical risk recommends future quarantine consideration",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.QUARANTINE_RECOMMENDED)
        would_require_operator_review = True
        would_require_policy_review = True

    if conflict_input.provenance_binding is None and (
        path_result is not None or source_result is not None
    ):
        kind = PathSourceConflictKind.PROVENANCE_MISSING
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.MEDIUM,
            reason="Provenance/evidence binding is missing or unresolved",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.MISSING_PROVENANCE_REQUIRES_REVIEW,
            applies_to=(kind.value,),
            severity=ConflictSeverity.MEDIUM,
            recommended_posture=ConflictPrecedencePosture.REVIEW_RECOMMENDED,
            reason="Missing provenance recommends future review",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.REVIEW_RECOMMENDED)

    if _has_conflicted_evidence(conflict_input.provenance_binding):
        kind = PathSourceConflictKind.EVIDENCE_CONFLICTED
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.HIGH,
            reason="Evidence/provenance context is conflicted",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.CONFLICTED_EVIDENCE_REQUIRES_POLICY_REVIEW,
            applies_to=(kind.value,),
            severity=ConflictSeverity.HIGH,
            recommended_posture=ConflictPrecedencePosture.POLICY_REVIEW_RECOMMENDED,
            reason="Conflicted evidence recommends future policy review",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.POLICY_REVIEW_RECOMMENDED)
        would_require_policy_review = True

    if _boundary_restricts_command_surface(conflict_input.untrusted_boundary):
        kind = PathSourceConflictKind.UNTRUSTED_BOUNDARY_COMMAND_SURFACE
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.MEDIUM,
            reason="Untrusted content boundary indicates command/instruction surface",
            source_label=source_label,
        ))
        rules.append(_make_rule(
            rule_kind=PrecedenceRuleKind.REVIEW_ON_CONFLICT,
            applies_to=(kind.value,),
            severity=ConflictSeverity.MEDIUM,
            recommended_posture=ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
            reason="Untrusted boundary command surface recommends future review",
            source_label=source_label,
        ))
        postures.update({
            ConflictPrecedencePosture.REVIEW_RECOMMENDED,
            ConflictPrecedencePosture.RESTRICT_RECOMMENDED,
        })

    if (
        conflict_input.authority_scope is None
        and (path_result is not None or source_result is not None)
    ):
        kind = PathSourceConflictKind.AUTHORITY_SCOPE_MISSING
        signals.append(_make_signal(
            conflict_kind=kind,
            severity=ConflictSeverity.LOW,
            reason="Authority scope context is missing or unresolved",
            source_label=source_label,
        ))
        postures.add(ConflictPrecedencePosture.INFORMATIONAL)

    return signals, rules, postures, would_require_operator_review, would_require_policy_review


def _explicit_context_supplied(values: Sequence[Any]) -> bool:
    return any(item is not None for item in values)


def resolve_path_source_conflicts_shadow(
    conflict_input: ConflictPrecedenceInput | Mapping[str, Any] | None = None,
    *,
    path_resolver_result: PathGovernanceResolverResult | Mapping[str, Any] | None = None,
    source_trust_resolver_result: (
        SourceTrustResolverResult | Mapping[str, Any] | None
    ) = None,
    risk_classification: PathSourceRiskClassification | Mapping[str, Any] | None = None,
    untrusted_boundary: UntrustedContentBoundary | Mapping[str, Any] | None = None,
    provenance_binding: ProvenanceBinding | Mapping[str, Any] | None = None,
    authority_scope: PathAuthorityScope | Mapping[str, Any] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> ConflictPrecedenceResult:
    """Resolve non-enforcing path/source conflict and precedence shadow output."""
    if conflict_input is not None:
        if _explicit_context_supplied((
            path_resolver_result,
            source_trust_resolver_result,
            risk_classification,
            untrusted_boundary,
            provenance_binding,
            authority_scope,
            metadata,
        )):
            raise PathGovernanceValidationError(
                "conflict_input cannot be combined with explicit context pieces",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="conflict_input",
            )
        resolved_input = (
            conflict_input
            if isinstance(conflict_input, ConflictPrecedenceInput)
            else ConflictPrecedenceInput.from_dict(conflict_input)
        )
    else:
        resolved_input = ConflictPrecedenceInput(
            path_resolver_result=path_resolver_result,
            source_trust_resolver_result=source_trust_resolver_result,
            risk_classification=risk_classification,
            untrusted_boundary=untrusted_boundary,
            provenance_binding=provenance_binding,
            authority_scope=authority_scope,
            source_label=source_label,
            metadata=metadata,
        )

    signals, rules, postures, op_review, pol_review = _derive_conflict_and_rules(
        resolved_input,
    )
    frozen_signals = _freeze_signals(signals)
    frozen_rules = _freeze_rules(rules)

    path_value, source_value = _decision_value(
        resolved_input.path_resolver_result,
        resolved_input.source_trust_resolver_result,
    )
    recommended = _strictest_decision(path_value, source_value)

    if not postures:
        final_posture = ConflictPrecedencePosture.NO_CONFLICT
    else:
        final_posture = _strictest_posture(postures)

    if recommended == "UNKNOWN" and final_posture is not ConflictPrecedencePosture.NO_CONFLICT:
        recommended = "WOULD_REVIEW"

    return ConflictPrecedenceResult(
        input_id=resolved_input.input_id,
        conflict_signals=frozen_signals,
        precedence_rules=frozen_rules,
        final_shadow_posture=final_posture,
        recommended_shadow_decision=recommended,
        source_label=resolved_input.source_label,
        shadow_only=True,
        enforced=False,
        would_require_operator_review=op_review,
        would_require_policy_review=pol_review,
        would_write_trace_later=True,
        metadata={
            "conflict_precedence_boundary": "shadow_only_not_enforcing",
            "source_input_hash": resolved_input.input_hash,
        },
    )
