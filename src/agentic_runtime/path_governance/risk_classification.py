"""Path/source risk classification model (P1.7.9)."""
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
from .source_identity import SourceIdentity
from .serialization import stable_hash
from .validation import validate_known_fields

PATH_SOURCE_RISK_TASK_ID = "P1.7.9"
PATH_SOURCE_RISK_CLASSIFICATION_VERSION = "path_source_risk_classification.v1"
PATH_SOURCE_RISK_REGISTRY_VERSION = "path_source_risk_registry.v1"
REASON_MAX_LENGTH = 512

PATH_SOURCE_RISK_SIGNAL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "signal_id",
    "signal_kind",
    "basis",
    "risk_level",
    "reason",
    "source_label",
    "metadata",
})

PATH_SOURCE_RISK_CLASSIFICATION_KNOWN_FIELDS: frozenset[str] = frozenset({
    "classification_id",
    "subject_ref",
    "path_identity_hash",
    "source_identity",
    "trust_label",
    "boundary_ref_id",
    "authority_scope_id",
    "provenance_binding_id",
    "signals",
    "risk_level",
    "posture",
    "source_label",
    "classification_hash",
    "created_by_task",
    "classification_version",
    "metadata",
})

PATH_SOURCE_RISK_REGISTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "registry_version",
    "classifications",
    "registry_hash",
    "source_label",
    "created_by_task",
    "notes",
    "metadata",
})

_RISK_LEVEL_RANK: dict[PathSourceRiskLevel, int] = {}


class PathSourceRiskLevel(str, Enum):
    """Declared risk level; classification only, not deny or enforcement."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PathSourceRiskSignalKind(str, Enum):
    """Declared risk signal kind; signal is not decision, block, or allow/deny."""

    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"
    UNTRUSTED_SOURCE = "UNTRUSTED_SOURCE"
    QUARANTINED_SOURCE = "QUARANTINED_SOURCE"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"
    TOOL_GENERATED_SOURCE = "TOOL_GENERATED_SOURCE"
    MODEL_GENERATED_SOURCE = "MODEL_GENERATED_SOURCE"
    PATH_TRAVERSAL_SIGNAL = "PATH_TRAVERSAL_SIGNAL"
    OUTSIDE_TRUSTED_ROOT_SIGNAL = "OUTSIDE_TRUSTED_ROOT_SIGNAL"
    ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT = "ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT"
    AUTHORITY_EXPANSION_SURFACE = "AUTHORITY_EXPANSION_SURFACE"
    PROMPT_INSTRUCTION_SURFACE = "PROMPT_INSTRUCTION_SURFACE"
    TOOL_ARGUMENT_SURFACE = "TOOL_ARGUMENT_SURFACE"
    MEMORY_WRITE_SURFACE = "MEMORY_WRITE_SURFACE"
    POLICY_DEFINITION_SURFACE = "POLICY_DEFINITION_SURFACE"
    EXECUTION_REQUEST_SURFACE = "EXECUTION_REQUEST_SURFACE"
    LOW_CONFIDENCE_EVIDENCE = "LOW_CONFIDENCE_EVIDENCE"
    CONFLICTED_EVIDENCE = "CONFLICTED_EVIDENCE"
    UNVERIFIED_CLAIM = "UNVERIFIED_CLAIM"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    UNKNOWN = "UNKNOWN"


class RiskClassificationBasis(str, Enum):
    """Declared classification basis; basis does not grant or deny anything."""

    SOURCE_TRUST = "SOURCE_TRUST"
    PATH_BOUNDARY = "PATH_BOUNDARY"
    TRUSTED_ROOT = "TRUSTED_ROOT"
    AUTHORITY_SCOPE = "AUTHORITY_SCOPE"
    UNTRUSTED_CONTENT_BOUNDARY = "UNTRUSTED_CONTENT_BOUNDARY"
    PROVENANCE_EVIDENCE = "PROVENANCE_EVIDENCE"
    CLAIM_REFERENCE = "CLAIM_REFERENCE"
    SYSTEM_DEFAULT = "SYSTEM_DEFAULT"
    TEST_FIXTURE = "TEST_FIXTURE"
    UNKNOWN = "UNKNOWN"


class RiskClassificationPosture(str, Enum):
    """Declared future-handling posture; posture does not enforce."""

    INFORMATIONAL = "INFORMATIONAL"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    REVIEW_REQUIRED_LATER = "REVIEW_REQUIRED_LATER"
    RESTRICTED_LATER = "RESTRICTED_LATER"
    QUARANTINE_RECOMMENDED = "QUARANTINE_RECOMMENDED"
    UNKNOWN = "UNKNOWN"


_RISK_LEVEL_RANK.update({
    PathSourceRiskLevel.UNKNOWN: -1,
    PathSourceRiskLevel.NONE: 0,
    PathSourceRiskLevel.LOW: 1,
    PathSourceRiskLevel.MEDIUM: 2,
    PathSourceRiskLevel.HIGH: 3,
    PathSourceRiskLevel.CRITICAL: 4,
})

_SIGNAL_KIND_DEFAULT_LEVEL: dict[PathSourceRiskSignalKind, PathSourceRiskLevel] = {
    PathSourceRiskSignalKind.AUTHORITY_EXPANSION_SURFACE: PathSourceRiskLevel.CRITICAL,
    PathSourceRiskSignalKind.POLICY_DEFINITION_SURFACE: PathSourceRiskLevel.CRITICAL,
    PathSourceRiskSignalKind.EXECUTION_REQUEST_SURFACE: PathSourceRiskLevel.CRITICAL,
    PathSourceRiskSignalKind.PATH_TRAVERSAL_SIGNAL: PathSourceRiskLevel.HIGH,
    PathSourceRiskSignalKind.OUTSIDE_TRUSTED_ROOT_SIGNAL: PathSourceRiskLevel.HIGH,
    PathSourceRiskSignalKind.QUARANTINED_SOURCE: PathSourceRiskLevel.HIGH,
    PathSourceRiskSignalKind.MEMORY_WRITE_SURFACE: PathSourceRiskLevel.HIGH,
    PathSourceRiskSignalKind.EXTERNAL_SOURCE: PathSourceRiskLevel.MEDIUM,
    PathSourceRiskSignalKind.UNTRUSTED_SOURCE: PathSourceRiskLevel.MEDIUM,
    PathSourceRiskSignalKind.TOOL_ARGUMENT_SURFACE: PathSourceRiskLevel.MEDIUM,
    PathSourceRiskSignalKind.PROMPT_INSTRUCTION_SURFACE: PathSourceRiskLevel.MEDIUM,
    PathSourceRiskSignalKind.CONFLICTED_EVIDENCE: PathSourceRiskLevel.MEDIUM,
    PathSourceRiskSignalKind.TOOL_GENERATED_SOURCE: PathSourceRiskLevel.LOW,
    PathSourceRiskSignalKind.MODEL_GENERATED_SOURCE: PathSourceRiskLevel.LOW,
    PathSourceRiskSignalKind.LOW_CONFIDENCE_EVIDENCE: PathSourceRiskLevel.LOW,
    PathSourceRiskSignalKind.UNVERIFIED_CLAIM: PathSourceRiskLevel.LOW,
    PathSourceRiskSignalKind.UNKNOWN_SOURCE: PathSourceRiskLevel.UNKNOWN,
    PathSourceRiskSignalKind.MISSING_PROVENANCE: PathSourceRiskLevel.UNKNOWN,
    PathSourceRiskSignalKind.ABSOLUTE_PATH_WITHOUT_ROOT_CONTEXT: PathSourceRiskLevel.UNKNOWN,
    PathSourceRiskSignalKind.UNKNOWN: PathSourceRiskLevel.UNKNOWN,
}

_RISK_LEVEL_DEFAULT_POSTURE: dict[PathSourceRiskLevel, RiskClassificationPosture] = {
    PathSourceRiskLevel.NONE: RiskClassificationPosture.INFORMATIONAL,
    PathSourceRiskLevel.LOW: RiskClassificationPosture.REVIEW_RECOMMENDED,
    PathSourceRiskLevel.MEDIUM: RiskClassificationPosture.REVIEW_RECOMMENDED,
    PathSourceRiskLevel.HIGH: RiskClassificationPosture.REVIEW_REQUIRED_LATER,
    PathSourceRiskLevel.CRITICAL: RiskClassificationPosture.QUARANTINE_RECOMMENDED,
    PathSourceRiskLevel.UNKNOWN: RiskClassificationPosture.UNKNOWN,
}


def _parse_risk_level(value: PathSourceRiskLevel | str) -> PathSourceRiskLevel:
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
        "risk_level must be a string or PathSourceRiskLevel",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="risk_level",
    )


def _parse_signal_kind(
    value: PathSourceRiskSignalKind | str,
) -> PathSourceRiskSignalKind:
    if isinstance(value, PathSourceRiskSignalKind):
        return value
    if isinstance(value, str):
        try:
            return PathSourceRiskSignalKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid signal_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="signal_kind",
            ) from exc
    raise PathGovernanceError(
        "signal_kind must be a string or PathSourceRiskSignalKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="signal_kind",
    )


def _parse_basis(value: RiskClassificationBasis | str) -> RiskClassificationBasis:
    if isinstance(value, RiskClassificationBasis):
        return value
    if isinstance(value, str):
        try:
            return RiskClassificationBasis(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid basis: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="basis",
            ) from exc
    raise PathGovernanceError(
        "basis must be a string or RiskClassificationBasis",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="basis",
    )


def _parse_posture(value: RiskClassificationPosture | str) -> RiskClassificationPosture:
    if isinstance(value, RiskClassificationPosture):
        return value
    if isinstance(value, str):
        try:
            return RiskClassificationPosture(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid posture: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="posture",
            ) from exc
    raise PathGovernanceError(
        "posture must be a string or RiskClassificationPosture",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="posture",
    )


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
                f"invalid trust_label: {value!r}",
                code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
                field="trust_label",
            ) from exc
    raise PathGovernanceError(
        "trust_label must be a string or SourceTrustLabel",
        code=PathGovernanceErrorCode.INVALID_TRUST_LABEL,
        field="trust_label",
    )


def _required_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise PathGovernanceValidationError(
            f"{field_name} must be a non-empty string",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return value


def _reason(value: Any) -> str:
    text = _required_string(value, field_name="reason")
    if len(text) > REASON_MAX_LENGTH:
        raise PathGovernanceValidationError(
            f"reason must be at most {REASON_MAX_LENGTH} characters",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="reason",
        )
    return text


def _optional_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _required_string(value, field_name=field_name)


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


def _freeze_notes(notes: Sequence[str] | None) -> tuple[str, ...]:
    raw = () if notes is None else notes
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "notes must be a sequence of strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="notes",
        )
    return tuple(str(item) for item in raw)


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


def _default_risk_level_for_signal_kind(
    signal_kind: PathSourceRiskSignalKind,
) -> PathSourceRiskLevel:
    return _SIGNAL_KIND_DEFAULT_LEVEL.get(signal_kind, PathSourceRiskLevel.UNKNOWN)


def _effective_signal_risk_level(signal: PathSourceRiskSignal) -> PathSourceRiskLevel:
    declared = signal.risk_level
    default = _default_risk_level_for_signal_kind(signal.signal_kind)
    if _RISK_LEVEL_RANK[declared] >= _RISK_LEVEL_RANK[default]:
        return declared
    return default


def _max_risk_level(levels: Sequence[PathSourceRiskLevel]) -> PathSourceRiskLevel:
    if not levels:
        return PathSourceRiskLevel.NONE
    return max(levels, key=lambda item: _RISK_LEVEL_RANK[item])


def _derive_risk_level_from_signals(
    signals: Sequence[PathSourceRiskSignal],
) -> PathSourceRiskLevel:
    if not signals:
        return PathSourceRiskLevel.NONE
    return _max_risk_level(
        [_effective_signal_risk_level(item) for item in signals],
    )


def _derive_posture_from_risk_level(
    risk_level: PathSourceRiskLevel,
) -> RiskClassificationPosture:
    return _RISK_LEVEL_DEFAULT_POSTURE.get(
        risk_level,
        RiskClassificationPosture.UNKNOWN,
    )


def compute_signal_id(
    *,
    signal_kind: PathSourceRiskSignalKind,
    basis: RiskClassificationBasis,
    risk_level: PathSourceRiskLevel,
    reason: str,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic signal identifier without decisioning."""
    return stable_hash({
        "basis": basis.value,
        "metadata": _sorted_metadata_dict(metadata),
        "reason": reason,
        "risk_level": risk_level.value,
        "signal_kind": signal_kind.value,
        "source_label": source_label.value,
    })


def _signal_canonical_payload(signal: PathSourceRiskSignal) -> dict[str, Any]:
    return {
        "basis": signal.basis.value,
        "metadata": _sorted_metadata_dict(signal.metadata),
        "reason": signal.reason,
        "risk_level": signal.risk_level.value,
        "signal_id": signal.signal_id,
        "signal_kind": signal.signal_kind.value,
        "source_label": signal.source_label.value,
    }


def compute_classification_id(
    *,
    subject_ref: str | None,
    path_identity_hash: str | None,
    source_identity: SourceIdentity | None,
    trust_label: SourceTrustLabel | None,
    boundary_ref_id: str | None,
    authority_scope_id: str | None,
    provenance_binding_id: str | None,
    signals: tuple[PathSourceRiskSignal, ...],
    classification_version: str = PATH_SOURCE_RISK_CLASSIFICATION_VERSION,
) -> str:
    """Compute deterministic classification identifier without resolver behavior."""
    payload: dict[str, Any] = {
        "classification_version": classification_version,
        "signals": [
            _signal_canonical_payload(item)
            for item in sorted(signals, key=lambda signal: signal.signal_id)
        ],
    }
    if subject_ref is not None:
        payload["subject_ref"] = subject_ref
    if path_identity_hash is not None:
        payload["path_identity_hash"] = path_identity_hash
    if source_identity is not None:
        payload["source_identity"] = source_identity.to_canonical_dict()
        payload["source_identity_hash"] = source_identity.identity_hash
    if trust_label is not None:
        payload["trust_label"] = trust_label.value
    if boundary_ref_id is not None:
        payload["boundary_ref_id"] = boundary_ref_id
    if authority_scope_id is not None:
        payload["authority_scope_id"] = authority_scope_id
    if provenance_binding_id is not None:
        payload["provenance_binding_id"] = provenance_binding_id
    return stable_hash(payload)


def _classification_canonical_payload(
    classification: PathSourceRiskClassification,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "classification_hash": classification.classification_hash,
        "classification_id": classification.classification_id,
        "classification_version": classification.classification_version,
        "created_by_task": classification.created_by_task,
        "metadata": _sorted_metadata_dict(classification.metadata),
        "posture": classification.posture.value,
        "risk_level": classification.risk_level.value,
        "signals": [item.to_canonical_dict() for item in classification.signals],
        "source_label": classification.source_label.value,
    }
    if classification.subject_ref is not None:
        payload["subject_ref"] = classification.subject_ref
    if classification.path_identity_hash is not None:
        payload["path_identity_hash"] = classification.path_identity_hash
    if classification.source_identity is not None:
        payload["source_identity"] = classification.source_identity.to_canonical_dict()
    if classification.trust_label is not None:
        payload["trust_label"] = classification.trust_label.value
    if classification.boundary_ref_id is not None:
        payload["boundary_ref_id"] = classification.boundary_ref_id
    if classification.authority_scope_id is not None:
        payload["authority_scope_id"] = classification.authority_scope_id
    if classification.provenance_binding_id is not None:
        payload["provenance_binding_id"] = classification.provenance_binding_id
    return payload


def compute_classification_hash(
    *,
    classification_id: str,
    subject_ref: str | None,
    path_identity_hash: str | None,
    source_identity: SourceIdentity | None,
    trust_label: SourceTrustLabel | None,
    boundary_ref_id: str | None,
    authority_scope_id: str | None,
    provenance_binding_id: str | None,
    signals: tuple[PathSourceRiskSignal, ...],
    risk_level: PathSourceRiskLevel,
    posture: RiskClassificationPosture,
    source_label: ProjectionSourceLabel,
    created_by_task: str,
    classification_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic classification hash; not enforcement or policy decision."""
    payload: dict[str, Any] = {
        "classification_id": classification_id,
        "classification_version": classification_version,
        "created_by_task": created_by_task,
        "metadata": _sorted_metadata_dict(metadata),
        "posture": posture.value,
        "risk_level": risk_level.value,
        "signals": [
            _signal_canonical_payload(item)
            for item in sorted(signals, key=lambda signal: signal.signal_id)
        ],
        "source_label": source_label.value,
    }
    if subject_ref is not None:
        payload["subject_ref"] = subject_ref
    if path_identity_hash is not None:
        payload["path_identity_hash"] = path_identity_hash
    if source_identity is not None:
        payload["source_identity"] = source_identity.to_canonical_dict()
    if trust_label is not None:
        payload["trust_label"] = trust_label.value
    if boundary_ref_id is not None:
        payload["boundary_ref_id"] = boundary_ref_id
    if authority_scope_id is not None:
        payload["authority_scope_id"] = authority_scope_id
    if provenance_binding_id is not None:
        payload["provenance_binding_id"] = provenance_binding_id
    return stable_hash(payload)


def compute_path_source_risk_registry_hash(
    *,
    registry_version: str,
    classifications: Sequence[PathSourceRiskClassification],
    created_by_task: str,
) -> str:
    """Compute deterministic order-insensitive path/source risk registry hash."""
    return stable_hash({
        "classifications": [
            item.to_canonical_dict()
            for item in sorted(
                classifications,
                key=lambda classification: classification.classification_id,
            )
        ],
        "created_by_task": created_by_task,
        "registry_version": registry_version,
    })


@dataclass(frozen=True)
class PathSourceRiskSignal:
    """Declared risk signal; not decision, block, allow/deny, or enforcement."""

    signal_kind: PathSourceRiskSignalKind
    basis: RiskClassificationBasis
    risk_level: PathSourceRiskLevel
    reason: str
    signal_id: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        signal_kind = _parse_signal_kind(self.signal_kind)
        basis = _parse_basis(self.basis)
        risk_level = _parse_risk_level(self.risk_level)
        reason = _reason(self.reason)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        signal_id = compute_signal_id(
            signal_kind=signal_kind,
            basis=basis,
            risk_level=risk_level,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.signal_id not in ("", signal_id):
            raise PathGovernanceValidationError(
                "signal_id does not match signal content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="signal_id",
            )
        object.__setattr__(self, "signal_kind", signal_kind)
        object.__setattr__(self, "basis", basis)
        object.__setattr__(self, "risk_level", risk_level)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "signal_id", signal_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _signal_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathSourceRiskSignal:
        validate_known_fields(
            data,
            PATH_SOURCE_RISK_SIGNAL_KNOWN_FIELDS,
            label="path_source_risk_signal",
        )
        return cls(
            signal_kind=data["signal_kind"],
            basis=data["basis"],
            risk_level=data["risk_level"],
            reason=data["reason"],
            signal_id=data.get("signal_id", ""),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathSourceRiskClassification:
    """Risk classification summary; not resolver, policy decision, or enforcement."""

    signals: tuple[PathSourceRiskSignal, ...] = field(default_factory=tuple)
    risk_level: PathSourceRiskLevel = PathSourceRiskLevel.UNKNOWN
    posture: RiskClassificationPosture = RiskClassificationPosture.UNKNOWN
    subject_ref: str | None = None
    path_identity_hash: str | None = None
    source_identity: SourceIdentity | None = None
    trust_label: SourceTrustLabel | None = None
    boundary_ref_id: str | None = None
    authority_scope_id: str | None = None
    provenance_binding_id: str | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    classification_id: str = ""
    classification_hash: str = ""
    created_by_task: str = PATH_SOURCE_RISK_TASK_ID
    classification_version: str = PATH_SOURCE_RISK_CLASSIFICATION_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.classification_version != PATH_SOURCE_RISK_CLASSIFICATION_VERSION:
            raise PathGovernanceValidationError(
                "classification_version must be path_source_risk_classification.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="classification_version",
            )
        if self.created_by_task != PATH_SOURCE_RISK_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.9",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        signals = _freeze_signals(self.signals)
        subject_ref = _optional_string(self.subject_ref, field_name="subject_ref")
        path_identity_hash = _optional_string(
            self.path_identity_hash,
            field_name="path_identity_hash",
        )
        source_identity = _build_source_identity(self.source_identity)
        trust_label = (
            None
            if self.trust_label is None
            else _parse_trust_label(self.trust_label)
        )
        boundary_ref_id = _optional_string(
            self.boundary_ref_id,
            field_name="boundary_ref_id",
        )
        authority_scope_id = _optional_string(
            self.authority_scope_id,
            field_name="authority_scope_id",
        )
        provenance_binding_id = _optional_string(
            self.provenance_binding_id,
            field_name="provenance_binding_id",
        )
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        risk_level = _parse_risk_level(self.risk_level)
        posture = _parse_posture(self.posture)
        classification_id = compute_classification_id(
            subject_ref=subject_ref,
            path_identity_hash=path_identity_hash,
            source_identity=source_identity,
            trust_label=trust_label,
            boundary_ref_id=boundary_ref_id,
            authority_scope_id=authority_scope_id,
            provenance_binding_id=provenance_binding_id,
            signals=signals,
            classification_version=self.classification_version,
        )
        if self.classification_id not in ("", classification_id):
            raise PathGovernanceValidationError(
                "classification_id does not match classification content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="classification_id",
            )
        classification_hash = compute_classification_hash(
            classification_id=classification_id,
            subject_ref=subject_ref,
            path_identity_hash=path_identity_hash,
            source_identity=source_identity,
            trust_label=trust_label,
            boundary_ref_id=boundary_ref_id,
            authority_scope_id=authority_scope_id,
            provenance_binding_id=provenance_binding_id,
            signals=signals,
            risk_level=risk_level,
            posture=posture,
            source_label=source_label,
            created_by_task=self.created_by_task,
            classification_version=self.classification_version,
            metadata=metadata,
        )
        if self.classification_hash not in ("", classification_hash):
            raise PathGovernanceValidationError(
                "classification_hash does not match classification content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="classification_hash",
            )
        object.__setattr__(self, "signals", signals)
        object.__setattr__(self, "risk_level", risk_level)
        object.__setattr__(self, "posture", posture)
        object.__setattr__(self, "subject_ref", subject_ref)
        object.__setattr__(self, "path_identity_hash", path_identity_hash)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "trust_label", trust_label)
        object.__setattr__(self, "boundary_ref_id", boundary_ref_id)
        object.__setattr__(self, "authority_scope_id", authority_scope_id)
        object.__setattr__(self, "provenance_binding_id", provenance_binding_id)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "classification_id", classification_id)
        object.__setattr__(self, "classification_hash", classification_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _classification_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathSourceRiskClassification:
        validate_known_fields(
            data,
            PATH_SOURCE_RISK_CLASSIFICATION_KNOWN_FIELDS,
            label="path_source_risk_classification",
        )
        source_identity = data.get("source_identity")
        return cls(
            signals=tuple(
                item if isinstance(item, PathSourceRiskSignal)
                else PathSourceRiskSignal.from_dict(item)
                for item in data.get("signals", ())
            ),
            risk_level=data.get("risk_level", PathSourceRiskLevel.UNKNOWN),
            posture=data.get("posture", RiskClassificationPosture.UNKNOWN),
            subject_ref=data.get("subject_ref"),
            path_identity_hash=data.get("path_identity_hash"),
            source_identity=(
                None
                if source_identity is None
                else (
                    source_identity
                    if isinstance(source_identity, SourceIdentity)
                    else SourceIdentity.from_dict(source_identity)
                )
            ),
            trust_label=data.get("trust_label"),
            boundary_ref_id=data.get("boundary_ref_id"),
            authority_scope_id=data.get("authority_scope_id"),
            provenance_binding_id=data.get("provenance_binding_id"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            classification_id=data.get("classification_id", ""),
            classification_hash=data.get("classification_hash", ""),
            created_by_task=data.get("created_by_task", PATH_SOURCE_RISK_TASK_ID),
            classification_version=data.get(
                "classification_version",
                PATH_SOURCE_RISK_CLASSIFICATION_VERSION,
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathSourceRiskRegistry:
    """Stable path/source risk registry; not resolver or enforcement."""

    classifications: tuple[PathSourceRiskClassification, ...] = field(
        default_factory=tuple,
    )
    registry_hash: str = ""
    registry_version: str = PATH_SOURCE_RISK_REGISTRY_VERSION
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    created_by_task: str = PATH_SOURCE_RISK_TASK_ID
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.registry_version != PATH_SOURCE_RISK_REGISTRY_VERSION:
            raise PathGovernanceValidationError(
                "registry_version must be path_source_risk_registry.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="registry_version",
            )
        if self.created_by_task != PATH_SOURCE_RISK_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.9",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        classifications = tuple(
            item if isinstance(item, PathSourceRiskClassification)
            else PathSourceRiskClassification.from_dict(item)
            for item in self.classifications
        )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_notes(self.notes)
        metadata = _freeze_metadata(self.metadata)
        registry_hash = compute_path_source_risk_registry_hash(
            registry_version=self.registry_version,
            classifications=classifications,
            created_by_task=self.created_by_task,
        )
        if self.registry_hash not in ("", registry_hash):
            raise PathGovernanceValidationError(
                "registry_hash does not match registry content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="registry_hash",
            )
        object.__setattr__(
            self,
            "classifications",
            tuple(
                sorted(classifications, key=lambda item: item.classification_id),
            ),
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "registry_hash", registry_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "classifications": [
                item.to_canonical_dict() for item in self.classifications
            ],
            "created_by_task": self.created_by_task,
            "metadata": _sorted_metadata_dict(self.metadata),
            "notes": list(self.notes),
            "registry_hash": self.registry_hash,
            "registry_version": self.registry_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathSourceRiskRegistry:
        validate_known_fields(
            data,
            PATH_SOURCE_RISK_REGISTRY_KNOWN_FIELDS,
            label="path_source_risk_registry",
        )
        return cls(
            classifications=tuple(
                item if isinstance(item, PathSourceRiskClassification)
                else PathSourceRiskClassification.from_dict(item)
                for item in data.get("classifications", ())
            ),
            registry_hash=data.get("registry_hash", ""),
            registry_version=data.get(
                "registry_version",
                PATH_SOURCE_RISK_REGISTRY_VERSION,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            created_by_task=data.get("created_by_task", PATH_SOURCE_RISK_TASK_ID),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def _build_signal(
    value: PathSourceRiskSignal | Mapping[str, Any],
) -> PathSourceRiskSignal:
    if isinstance(value, PathSourceRiskSignal):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "signals entries must be PathSourceRiskSignal objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="signals",
        )
    return PathSourceRiskSignal.from_dict(value)


def _build_classification(
    value: PathSourceRiskClassification | Mapping[str, Any],
) -> PathSourceRiskClassification:
    if isinstance(value, PathSourceRiskClassification):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "classifications entries must be PathSourceRiskClassification "
            "objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="classifications",
        )
    return PathSourceRiskClassification.from_dict(value)


def _freeze_signals(
    signals: Sequence[PathSourceRiskSignal | Mapping[str, Any]] | None,
) -> tuple[PathSourceRiskSignal, ...]:
    raw = () if signals is None else signals
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "signals must be a sequence of PathSourceRiskSignal values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="signals",
        )
    parsed = tuple(_build_signal(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.signal_id))


def build_path_source_risk_signal(
    signal_kind: PathSourceRiskSignalKind | str,
    basis: RiskClassificationBasis | str,
    risk_level: PathSourceRiskLevel | str,
    reason: str,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathSourceRiskSignal:
    """Build deterministic risk signal without decisioning or enforcement."""
    return PathSourceRiskSignal(
        signal_kind=signal_kind,
        basis=basis,
        risk_level=risk_level,
        reason=reason,
        source_label=source_label,
        metadata=metadata,
    )


def build_path_source_risk_classification(
    signals: Sequence[PathSourceRiskSignal | Mapping[str, Any]] | None = None,
    source_identity: SourceIdentity | Mapping[str, Any] | None = None,
    trust_label: SourceTrustLabel | str | None = None,
    path_identity_hash: str | None = None,
    boundary_ref_id: str | None = None,
    authority_scope_id: str | None = None,
    provenance_binding_id: str | None = None,
    subject_ref: str | None = None,
    risk_level: PathSourceRiskLevel | str | None = None,
    posture: RiskClassificationPosture | str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathSourceRiskClassification:
    """Build deterministic risk classification without resolver or enforcement."""
    frozen_signals = _freeze_signals(signals)
    resolved_risk_level = (
        _derive_risk_level_from_signals(frozen_signals)
        if risk_level is None
        else _parse_risk_level(risk_level)
    )
    resolved_posture = (
        _derive_posture_from_risk_level(resolved_risk_level)
        if posture is None
        else _parse_posture(posture)
    )
    return PathSourceRiskClassification(
        signals=frozen_signals,
        risk_level=resolved_risk_level,
        posture=resolved_posture,
        subject_ref=subject_ref,
        path_identity_hash=path_identity_hash,
        source_identity=_build_source_identity(source_identity),
        trust_label=trust_label,
        boundary_ref_id=boundary_ref_id,
        authority_scope_id=authority_scope_id,
        provenance_binding_id=provenance_binding_id,
        source_label=source_label,
        metadata=metadata,
    )


def derive_path_source_risk_classification(
    signals: Sequence[PathSourceRiskSignal | Mapping[str, Any]],
    *,
    source_identity: SourceIdentity | Mapping[str, Any] | None = None,
    trust_label: SourceTrustLabel | str | None = None,
    path_identity_hash: str | None = None,
    boundary_ref_id: str | None = None,
    authority_scope_id: str | None = None,
    provenance_binding_id: str | None = None,
    subject_ref: str | None = None,
    risk_level: PathSourceRiskLevel | str | None = None,
    posture: RiskClassificationPosture | str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathSourceRiskClassification:
    """Derive declarative risk classification from signals without decisioning."""
    return build_path_source_risk_classification(
        signals=signals,
        source_identity=source_identity,
        trust_label=trust_label,
        path_identity_hash=path_identity_hash,
        boundary_ref_id=boundary_ref_id,
        authority_scope_id=authority_scope_id,
        provenance_binding_id=provenance_binding_id,
        subject_ref=subject_ref,
        risk_level=risk_level,
        posture=posture,
        source_label=source_label,
        metadata=metadata,
    )


def build_path_source_risk_registry(
    classifications: Sequence[
        PathSourceRiskClassification | Mapping[str, Any]
    ] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathSourceRiskRegistry:
    """Build deterministic risk registry without resolver or enforcement."""
    classification_tuple = tuple(
        _build_classification(item)
        for item in (() if classifications is None else classifications)
    )
    return PathSourceRiskRegistry(
        classifications=classification_tuple,
        source_label=source_label,
        notes=(
            "P1.7.9 registry declares path/source risk classification state only.",
            "Risk classification is not resolver; risk level is not deny; "
            "risk posture is not policy decision.",
        ),
        metadata=metadata,
    )
