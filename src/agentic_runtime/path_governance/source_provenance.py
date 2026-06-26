"""Source provenance and evidence binding seed (P1.7.8)."""
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
from .source_identity import SourceIdentity
from .serialization import stable_hash
from .validation import validate_known_fields

SOURCE_PROVENANCE_TASK_ID = "P1.7.8"
SOURCE_PROVENANCE_BINDING_VERSION = "source_provenance_binding.v1"
SOURCE_PROVENANCE_BINDING_REGISTRY_VERSION = (
    "source_provenance_binding_registry.v1"
)
CLAIM_SUMMARY_MAX_LENGTH = 512

SOURCE_EVIDENCE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "evidence_id",
    "evidence_kind",
    "source_identity",
    "source_label",
    "confidence",
    "evidence_hash",
    "metadata",
})

SOURCE_CLAIM_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "claim_id",
    "claim_kind",
    "source_identity",
    "claim_summary",
    "source_label",
    "confidence",
    "claim_hash",
    "metadata",
})

SOURCE_PROVENANCE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "provenance_id",
    "provenance_kind",
    "source_identity",
    "parent_source_id",
    "derived_from",
    "source_label",
    "provenance_hash",
    "metadata",
})

PROVENANCE_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "binding_id",
    "source_identity",
    "provenance_refs",
    "evidence_refs",
    "claim_refs",
    "boundary_ref_id",
    "authority_scope_id",
    "path_identity_hash",
    "source_label",
    "binding_hash",
    "created_by_task",
    "binding_version",
    "metadata",
})

PROVENANCE_BINDING_REGISTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "registry_version",
    "bindings",
    "registry_hash",
    "source_label",
    "created_by_task",
    "notes",
    "metadata",
})


class SourceProvenanceKind(str, Enum):
    """Declared provenance kind; provenance kind does not assert truth or authority."""

    DIRECT_SOURCE = "DIRECT_SOURCE"
    DERIVED_SOURCE = "DERIVED_SOURCE"
    TRANSFORMED_SOURCE = "TRANSFORMED_SOURCE"
    TOOL_PRODUCED = "TOOL_PRODUCED"
    MODEL_PRODUCED = "MODEL_PRODUCED"
    AGENT_PRODUCED = "AGENT_PRODUCED"
    MEMORY_RECALLED = "MEMORY_RECALLED"
    OPERATOR_PROVIDED = "OPERATOR_PROVIDED"
    UNKNOWN = "UNKNOWN"


class EvidenceBindingKind(str, Enum):
    """Declared evidence binding kind; does not resolve truth or write trace."""

    SOURCE_IDENTITY = "SOURCE_IDENTITY"
    SOURCE_TRUST_LABEL = "SOURCE_TRUST_LABEL"
    PATH_IDENTITY = "PATH_IDENTITY"
    TRUSTED_ROOT_DECLARATION = "TRUSTED_ROOT_DECLARATION"
    ESCAPE_DETECTION_RESULT = "ESCAPE_DETECTION_RESULT"
    AUTHORITY_SCOPE_DECLARATION = "AUTHORITY_SCOPE_DECLARATION"
    UNTRUSTED_BOUNDARY_DECLARATION = "UNTRUSTED_BOUNDARY_DECLARATION"
    CLAIM_REFERENCE = "CLAIM_REFERENCE"
    OUTPUT_REFERENCE = "OUTPUT_REFERENCE"
    UNKNOWN = "UNKNOWN"


class EvidenceConfidence(str, Enum):
    """Confidence marker; not a truth guarantee or resolver output."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"
    UNVERIFIED = "UNVERIFIED"


class SourceClaimKind(str, Enum):
    """Claim classification only; does not accept, reject, execute, or enforce."""

    FACTUAL_CLAIM = "FACTUAL_CLAIM"
    INSTRUCTION_CLAIM = "INSTRUCTION_CLAIM"
    POLICY_CLAIM = "POLICY_CLAIM"
    AUTHORITY_CLAIM = "AUTHORITY_CLAIM"
    MEMORY_CLAIM = "MEMORY_CLAIM"
    TOOL_RESULT_CLAIM = "TOOL_RESULT_CLAIM"
    MODEL_OUTPUT_CLAIM = "MODEL_OUTPUT_CLAIM"
    UNKNOWN = "UNKNOWN"


def _parse_provenance_kind(
    value: SourceProvenanceKind | str,
) -> SourceProvenanceKind:
    if isinstance(value, SourceProvenanceKind):
        return value
    if isinstance(value, str):
        try:
            return SourceProvenanceKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid provenance_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="provenance_kind",
            ) from exc
    raise PathGovernanceError(
        "provenance_kind must be a string or SourceProvenanceKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="provenance_kind",
    )


def _parse_evidence_kind(value: EvidenceBindingKind | str) -> EvidenceBindingKind:
    if isinstance(value, EvidenceBindingKind):
        return value
    if isinstance(value, str):
        try:
            return EvidenceBindingKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid evidence_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="evidence_kind",
            ) from exc
    raise PathGovernanceError(
        "evidence_kind must be a string or EvidenceBindingKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="evidence_kind",
    )


def _parse_confidence(value: EvidenceConfidence | str) -> EvidenceConfidence:
    if isinstance(value, EvidenceConfidence):
        return value
    if isinstance(value, str):
        try:
            return EvidenceConfidence(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid confidence: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="confidence",
            ) from exc
    raise PathGovernanceError(
        "confidence must be a string or EvidenceConfidence",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="confidence",
    )


def _parse_claim_kind(value: SourceClaimKind | str) -> SourceClaimKind:
    if isinstance(value, SourceClaimKind):
        return value
    if isinstance(value, str):
        try:
            return SourceClaimKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid claim_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="claim_kind",
            ) from exc
    raise PathGovernanceError(
        "claim_kind must be a string or SourceClaimKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="claim_kind",
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


def _required_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise PathGovernanceValidationError(
            f"{field_name} must be a non-empty string",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return value


def _claim_summary(value: Any) -> str:
    summary = _required_string(value, field_name="claim_summary")
    if len(summary) > CLAIM_SUMMARY_MAX_LENGTH:
        raise PathGovernanceValidationError(
            f"claim_summary must be at most {CLAIM_SUMMARY_MAX_LENGTH} characters",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="claim_summary",
        )
    return summary


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


def _build_source_identity(value: SourceIdentity | Mapping[str, Any]) -> SourceIdentity:
    if isinstance(value, SourceIdentity):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "source_identity must be a SourceIdentity object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="source_identity",
        )
    return SourceIdentity.from_dict(value)


def _freeze_derived_from(
    derived_from: Sequence[str] | None,
) -> tuple[str, ...]:
    raw = () if derived_from is None else derived_from
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "derived_from must be a sequence of source id strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="derived_from",
        )
    parsed = tuple(_required_string(item, field_name="derived_from") for item in raw)
    return tuple(sorted(parsed))


def compute_evidence_id(
    *,
    evidence_kind: EvidenceBindingKind,
    source_identity: SourceIdentity,
    source_label: ProjectionSourceLabel,
    confidence: EvidenceConfidence,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic evidence identifier without verifying truth."""
    return stable_hash({
        "confidence": confidence.value,
        "evidence_kind": evidence_kind.value,
        "metadata": _sorted_metadata_dict(metadata),
        "source_identity": source_identity.to_canonical_dict(),
        "source_identity_hash": source_identity.identity_hash,
        "source_label": source_label.value,
    })


def _evidence_canonical_payload(evidence: SourceEvidenceRef) -> dict[str, Any]:
    return {
        "confidence": evidence.confidence.value,
        "evidence_hash": evidence.evidence_hash,
        "evidence_id": evidence.evidence_id,
        "evidence_kind": evidence.evidence_kind.value,
        "metadata": _sorted_metadata_dict(evidence.metadata),
        "source_identity": evidence.source_identity.to_canonical_dict(),
        "source_label": evidence.source_label.value,
    }


def compute_evidence_hash(
    *,
    evidence_id: str,
    evidence_kind: EvidenceBindingKind,
    source_identity: SourceIdentity,
    source_label: ProjectionSourceLabel,
    confidence: EvidenceConfidence,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic evidence hash over canonical evidence payload."""
    return stable_hash({
        "confidence": confidence.value,
        "evidence_id": evidence_id,
        "evidence_kind": evidence_kind.value,
        "metadata": _sorted_metadata_dict(metadata),
        "source_identity": source_identity.to_canonical_dict(),
        "source_label": source_label.value,
    })


def compute_claim_id(
    *,
    claim_kind: SourceClaimKind,
    source_identity: SourceIdentity,
    claim_summary: str,
    source_label: ProjectionSourceLabel,
    confidence: EvidenceConfidence,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic claim identifier without accepting or rejecting claim."""
    return stable_hash({
        "claim_kind": claim_kind.value,
        "claim_summary": claim_summary,
        "confidence": confidence.value,
        "metadata": _sorted_metadata_dict(metadata),
        "source_identity": source_identity.to_canonical_dict(),
        "source_identity_hash": source_identity.identity_hash,
        "source_label": source_label.value,
    })


def _claim_canonical_payload(claim: SourceClaimRef) -> dict[str, Any]:
    return {
        "claim_hash": claim.claim_hash,
        "claim_id": claim.claim_id,
        "claim_kind": claim.claim_kind.value,
        "claim_summary": claim.claim_summary,
        "confidence": claim.confidence.value,
        "metadata": _sorted_metadata_dict(claim.metadata),
        "source_identity": claim.source_identity.to_canonical_dict(),
        "source_label": claim.source_label.value,
    }


def compute_claim_hash(
    *,
    claim_id: str,
    claim_kind: SourceClaimKind,
    source_identity: SourceIdentity,
    claim_summary: str,
    source_label: ProjectionSourceLabel,
    confidence: EvidenceConfidence,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic claim hash over canonical claim payload."""
    return stable_hash({
        "claim_id": claim_id,
        "claim_kind": claim_kind.value,
        "claim_summary": claim_summary,
        "confidence": confidence.value,
        "metadata": _sorted_metadata_dict(metadata),
        "source_identity": source_identity.to_canonical_dict(),
        "source_label": source_label.value,
    })


def compute_provenance_id(
    *,
    provenance_kind: SourceProvenanceKind,
    source_identity: SourceIdentity,
    parent_source_id: str | None,
    derived_from: tuple[str, ...],
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic provenance identifier without graph traversal."""
    payload: dict[str, Any] = {
        "derived_from": list(derived_from),
        "metadata": _sorted_metadata_dict(metadata),
        "provenance_kind": provenance_kind.value,
        "source_identity": source_identity.to_canonical_dict(),
        "source_identity_hash": source_identity.identity_hash,
        "source_label": source_label.value,
    }
    if parent_source_id is not None:
        payload["parent_source_id"] = parent_source_id
    return stable_hash(payload)


def _provenance_canonical_payload(
    provenance: SourceProvenanceRef,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "derived_from": list(provenance.derived_from),
        "metadata": _sorted_metadata_dict(provenance.metadata),
        "provenance_hash": provenance.provenance_hash,
        "provenance_id": provenance.provenance_id,
        "provenance_kind": provenance.provenance_kind.value,
        "source_identity": provenance.source_identity.to_canonical_dict(),
        "source_label": provenance.source_label.value,
    }
    if provenance.parent_source_id is not None:
        payload["parent_source_id"] = provenance.parent_source_id
    return payload


def compute_provenance_hash(
    *,
    provenance_id: str,
    provenance_kind: SourceProvenanceKind,
    source_identity: SourceIdentity,
    parent_source_id: str | None,
    derived_from: tuple[str, ...],
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic provenance hash over canonical provenance payload."""
    payload: dict[str, Any] = {
        "derived_from": list(derived_from),
        "metadata": _sorted_metadata_dict(metadata),
        "provenance_id": provenance_id,
        "provenance_kind": provenance_kind.value,
        "source_identity": source_identity.to_canonical_dict(),
        "source_label": source_label.value,
    }
    if parent_source_id is not None:
        payload["parent_source_id"] = parent_source_id
    return stable_hash(payload)


def compute_binding_id(
    *,
    source_identity: SourceIdentity,
    provenance_refs: tuple[SourceProvenanceRef, ...],
    evidence_refs: tuple[SourceEvidenceRef, ...],
    claim_refs: tuple[SourceClaimRef, ...],
    boundary_ref_id: str | None,
    authority_scope_id: str | None,
    path_identity_hash: str | None,
    binding_version: str = SOURCE_PROVENANCE_BINDING_VERSION,
) -> str:
    """Compute deterministic binding identifier without resolver behavior."""
    payload: dict[str, Any] = {
        "binding_version": binding_version,
        "claim_refs": [
            _claim_canonical_payload(item)
            for item in sorted(claim_refs, key=lambda ref: ref.claim_id)
        ],
        "evidence_refs": [
            _evidence_canonical_payload(item)
            for item in sorted(evidence_refs, key=lambda ref: ref.evidence_id)
        ],
        "provenance_refs": [
            _provenance_canonical_payload(item)
            for item in sorted(provenance_refs, key=lambda ref: ref.provenance_id)
        ],
        "source_identity": source_identity.to_canonical_dict(),
        "source_identity_hash": source_identity.identity_hash,
    }
    if boundary_ref_id is not None:
        payload["boundary_ref_id"] = boundary_ref_id
    if authority_scope_id is not None:
        payload["authority_scope_id"] = authority_scope_id
    if path_identity_hash is not None:
        payload["path_identity_hash"] = path_identity_hash
    return stable_hash(payload)


def _binding_canonical_payload(binding: ProvenanceBinding) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "binding_hash": binding.binding_hash,
        "binding_id": binding.binding_id,
        "binding_version": binding.binding_version,
        "claim_refs": [item.to_canonical_dict() for item in binding.claim_refs],
        "created_by_task": binding.created_by_task,
        "evidence_refs": [item.to_canonical_dict() for item in binding.evidence_refs],
        "metadata": _sorted_metadata_dict(binding.metadata),
        "provenance_refs": [
            item.to_canonical_dict() for item in binding.provenance_refs
        ],
        "source_identity": binding.source_identity.to_canonical_dict(),
        "source_label": binding.source_label.value,
    }
    if binding.boundary_ref_id is not None:
        payload["boundary_ref_id"] = binding.boundary_ref_id
    if binding.authority_scope_id is not None:
        payload["authority_scope_id"] = binding.authority_scope_id
    if binding.path_identity_hash is not None:
        payload["path_identity_hash"] = binding.path_identity_hash
    return payload


def compute_binding_hash(
    *,
    binding_id: str,
    source_identity: SourceIdentity,
    provenance_refs: tuple[SourceProvenanceRef, ...],
    evidence_refs: tuple[SourceEvidenceRef, ...],
    claim_refs: tuple[SourceClaimRef, ...],
    boundary_ref_id: str | None,
    authority_scope_id: str | None,
    path_identity_hash: str | None,
    source_label: ProjectionSourceLabel,
    created_by_task: str,
    binding_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic binding hash; not a Ledger write or trace event."""
    payload: dict[str, Any] = {
        "binding_id": binding_id,
        "binding_version": binding_version,
        "claim_refs": [
            _claim_canonical_payload(item)
            for item in sorted(claim_refs, key=lambda ref: ref.claim_id)
        ],
        "created_by_task": created_by_task,
        "evidence_refs": [
            _evidence_canonical_payload(item)
            for item in sorted(evidence_refs, key=lambda ref: ref.evidence_id)
        ],
        "metadata": _sorted_metadata_dict(metadata),
        "provenance_refs": [
            _provenance_canonical_payload(item)
            for item in sorted(provenance_refs, key=lambda ref: ref.provenance_id)
        ],
        "source_identity": source_identity.to_canonical_dict(),
        "source_label": source_label.value,
    }
    if boundary_ref_id is not None:
        payload["boundary_ref_id"] = boundary_ref_id
    if authority_scope_id is not None:
        payload["authority_scope_id"] = authority_scope_id
    if path_identity_hash is not None:
        payload["path_identity_hash"] = path_identity_hash
    return stable_hash(payload)


def compute_provenance_binding_registry_hash(
    *,
    registry_version: str,
    bindings: Sequence[ProvenanceBinding],
    created_by_task: str,
) -> str:
    """Compute deterministic order-insensitive provenance binding registry hash."""
    return stable_hash({
        "bindings": [
            item.to_canonical_dict()
            for item in sorted(bindings, key=lambda binding: binding.binding_id)
        ],
        "created_by_task": created_by_task,
        "registry_version": registry_version,
    })


@dataclass(frozen=True)
class SourceEvidenceRef:
    """Evidence reference; does not verify truth, emit trace, or write Ledger."""

    evidence_kind: EvidenceBindingKind
    source_identity: SourceIdentity
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    confidence: EvidenceConfidence = EvidenceConfidence.UNVERIFIED
    evidence_id: str = ""
    evidence_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        evidence_kind = _parse_evidence_kind(self.evidence_kind)
        source_identity = _build_source_identity(self.source_identity)
        source_label = _parse_source_label(self.source_label)
        confidence = _parse_confidence(self.confidence)
        metadata = _freeze_metadata(self.metadata)
        evidence_id = compute_evidence_id(
            evidence_kind=evidence_kind,
            source_identity=source_identity,
            source_label=source_label,
            confidence=confidence,
            metadata=metadata,
        )
        if self.evidence_id not in ("", evidence_id):
            raise PathGovernanceValidationError(
                "evidence_id does not match evidence content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="evidence_id",
            )
        evidence_hash = compute_evidence_hash(
            evidence_id=evidence_id,
            evidence_kind=evidence_kind,
            source_identity=source_identity,
            source_label=source_label,
            confidence=confidence,
            metadata=metadata,
        )
        if self.evidence_hash not in ("", evidence_hash):
            raise PathGovernanceValidationError(
                "evidence_hash does not match evidence content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="evidence_hash",
            )
        object.__setattr__(self, "evidence_kind", evidence_kind)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "evidence_id", evidence_id)
        object.__setattr__(self, "evidence_hash", evidence_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _evidence_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceEvidenceRef:
        validate_known_fields(
            data,
            SOURCE_EVIDENCE_REF_KNOWN_FIELDS,
            label="source_evidence_ref",
        )
        source_identity = data["source_identity"]
        return cls(
            evidence_kind=data["evidence_kind"],
            source_identity=(
                source_identity
                if isinstance(source_identity, SourceIdentity)
                else SourceIdentity.from_dict(source_identity)
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            confidence=data.get("confidence", EvidenceConfidence.UNVERIFIED),
            evidence_id=data.get("evidence_id", ""),
            evidence_hash=data.get("evidence_hash", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class SourceClaimRef:
    """Claim reference; classification only, not acceptance or execution."""

    claim_kind: SourceClaimKind
    source_identity: SourceIdentity
    claim_summary: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    confidence: EvidenceConfidence = EvidenceConfidence.UNVERIFIED
    claim_id: str = ""
    claim_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        claim_kind = _parse_claim_kind(self.claim_kind)
        source_identity = _build_source_identity(self.source_identity)
        claim_summary = _claim_summary(self.claim_summary)
        source_label = _parse_source_label(self.source_label)
        confidence = _parse_confidence(self.confidence)
        metadata = _freeze_metadata(self.metadata)
        claim_id = compute_claim_id(
            claim_kind=claim_kind,
            source_identity=source_identity,
            claim_summary=claim_summary,
            source_label=source_label,
            confidence=confidence,
            metadata=metadata,
        )
        if self.claim_id not in ("", claim_id):
            raise PathGovernanceValidationError(
                "claim_id does not match claim content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="claim_id",
            )
        claim_hash = compute_claim_hash(
            claim_id=claim_id,
            claim_kind=claim_kind,
            source_identity=source_identity,
            claim_summary=claim_summary,
            source_label=source_label,
            confidence=confidence,
            metadata=metadata,
        )
        if self.claim_hash not in ("", claim_hash):
            raise PathGovernanceValidationError(
                "claim_hash does not match claim content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="claim_hash",
            )
        object.__setattr__(self, "claim_kind", claim_kind)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "claim_summary", claim_summary)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "claim_id", claim_id)
        object.__setattr__(self, "claim_hash", claim_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _claim_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceClaimRef:
        validate_known_fields(
            data,
            SOURCE_CLAIM_REF_KNOWN_FIELDS,
            label="source_claim_ref",
        )
        source_identity = data["source_identity"]
        return cls(
            claim_kind=data["claim_kind"],
            source_identity=(
                source_identity
                if isinstance(source_identity, SourceIdentity)
                else SourceIdentity.from_dict(source_identity)
            ),
            claim_summary=data["claim_summary"],
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            confidence=data.get("confidence", EvidenceConfidence.UNVERIFIED),
            claim_id=data.get("claim_id", ""),
            claim_hash=data.get("claim_hash", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class SourceProvenanceRef:
    """Provenance lineage seed; not a graph engine or trace event."""

    provenance_kind: SourceProvenanceKind
    source_identity: SourceIdentity
    parent_source_id: str | None = None
    derived_from: tuple[str, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    provenance_id: str = ""
    provenance_hash: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        provenance_kind = _parse_provenance_kind(self.provenance_kind)
        source_identity = _build_source_identity(self.source_identity)
        parent_source_id = _optional_string(
            self.parent_source_id,
            field_name="parent_source_id",
        )
        derived_from = _freeze_derived_from(self.derived_from)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        provenance_id = compute_provenance_id(
            provenance_kind=provenance_kind,
            source_identity=source_identity,
            parent_source_id=parent_source_id,
            derived_from=derived_from,
            source_label=source_label,
            metadata=metadata,
        )
        if self.provenance_id not in ("", provenance_id):
            raise PathGovernanceValidationError(
                "provenance_id does not match provenance content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="provenance_id",
            )
        provenance_hash = compute_provenance_hash(
            provenance_id=provenance_id,
            provenance_kind=provenance_kind,
            source_identity=source_identity,
            parent_source_id=parent_source_id,
            derived_from=derived_from,
            source_label=source_label,
            metadata=metadata,
        )
        if self.provenance_hash not in ("", provenance_hash):
            raise PathGovernanceValidationError(
                "provenance_hash does not match provenance content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="provenance_hash",
            )
        object.__setattr__(self, "provenance_kind", provenance_kind)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "parent_source_id", parent_source_id)
        object.__setattr__(self, "derived_from", derived_from)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "provenance_id", provenance_id)
        object.__setattr__(self, "provenance_hash", provenance_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _provenance_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceProvenanceRef:
        validate_known_fields(
            data,
            SOURCE_PROVENANCE_REF_KNOWN_FIELDS,
            label="source_provenance_ref",
        )
        source_identity = data["source_identity"]
        return cls(
            provenance_kind=data["provenance_kind"],
            source_identity=(
                source_identity
                if isinstance(source_identity, SourceIdentity)
                else SourceIdentity.from_dict(source_identity)
            ),
            parent_source_id=data.get("parent_source_id"),
            derived_from=data.get("derived_from", ()),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            provenance_id=data.get("provenance_id", ""),
            provenance_hash=data.get("provenance_hash", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class ProvenanceBinding:
    """Reference binding object; not truth verification, trace, or Ledger write."""

    source_identity: SourceIdentity
    provenance_refs: tuple[SourceProvenanceRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[SourceEvidenceRef, ...] = field(default_factory=tuple)
    claim_refs: tuple[SourceClaimRef, ...] = field(default_factory=tuple)
    boundary_ref_id: str | None = None
    authority_scope_id: str | None = None
    path_identity_hash: str | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    binding_id: str = ""
    binding_hash: str = ""
    created_by_task: str = SOURCE_PROVENANCE_TASK_ID
    binding_version: str = SOURCE_PROVENANCE_BINDING_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.binding_version != SOURCE_PROVENANCE_BINDING_VERSION:
            raise PathGovernanceValidationError(
                "binding_version must be source_provenance_binding.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="binding_version",
            )
        if self.created_by_task != SOURCE_PROVENANCE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.8",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        source_identity = _build_source_identity(self.source_identity)
        provenance_refs = _freeze_provenance_refs(self.provenance_refs)
        evidence_refs = _freeze_evidence_refs(self.evidence_refs)
        claim_refs = _freeze_claim_refs(self.claim_refs)
        boundary_ref_id = _optional_string(
            self.boundary_ref_id,
            field_name="boundary_ref_id",
        )
        authority_scope_id = _optional_string(
            self.authority_scope_id,
            field_name="authority_scope_id",
        )
        path_identity_hash = _optional_string(
            self.path_identity_hash,
            field_name="path_identity_hash",
        )
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        binding_id = compute_binding_id(
            source_identity=source_identity,
            provenance_refs=provenance_refs,
            evidence_refs=evidence_refs,
            claim_refs=claim_refs,
            boundary_ref_id=boundary_ref_id,
            authority_scope_id=authority_scope_id,
            path_identity_hash=path_identity_hash,
            binding_version=self.binding_version,
        )
        if self.binding_id not in ("", binding_id):
            raise PathGovernanceValidationError(
                "binding_id does not match binding content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="binding_id",
            )
        binding_hash = compute_binding_hash(
            binding_id=binding_id,
            source_identity=source_identity,
            provenance_refs=provenance_refs,
            evidence_refs=evidence_refs,
            claim_refs=claim_refs,
            boundary_ref_id=boundary_ref_id,
            authority_scope_id=authority_scope_id,
            path_identity_hash=path_identity_hash,
            source_label=source_label,
            created_by_task=self.created_by_task,
            binding_version=self.binding_version,
            metadata=metadata,
        )
        if self.binding_hash not in ("", binding_hash):
            raise PathGovernanceValidationError(
                "binding_hash does not match binding content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="binding_hash",
            )
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "provenance_refs", provenance_refs)
        object.__setattr__(self, "evidence_refs", evidence_refs)
        object.__setattr__(self, "claim_refs", claim_refs)
        object.__setattr__(self, "boundary_ref_id", boundary_ref_id)
        object.__setattr__(self, "authority_scope_id", authority_scope_id)
        object.__setattr__(self, "path_identity_hash", path_identity_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "binding_id", binding_id)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _binding_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProvenanceBinding:
        validate_known_fields(
            data,
            PROVENANCE_BINDING_KNOWN_FIELDS,
            label="provenance_binding",
        )
        source_identity = data["source_identity"]
        return cls(
            source_identity=(
                source_identity
                if isinstance(source_identity, SourceIdentity)
                else SourceIdentity.from_dict(source_identity)
            ),
            provenance_refs=tuple(
                item if isinstance(item, SourceProvenanceRef)
                else SourceProvenanceRef.from_dict(item)
                for item in data.get("provenance_refs", ())
            ),
            evidence_refs=tuple(
                item if isinstance(item, SourceEvidenceRef)
                else SourceEvidenceRef.from_dict(item)
                for item in data.get("evidence_refs", ())
            ),
            claim_refs=tuple(
                item if isinstance(item, SourceClaimRef)
                else SourceClaimRef.from_dict(item)
                for item in data.get("claim_refs", ())
            ),
            boundary_ref_id=data.get("boundary_ref_id"),
            authority_scope_id=data.get("authority_scope_id"),
            path_identity_hash=data.get("path_identity_hash"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
            created_by_task=data.get("created_by_task", SOURCE_PROVENANCE_TASK_ID),
            binding_version=data.get(
                "binding_version",
                SOURCE_PROVENANCE_BINDING_VERSION,
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class ProvenanceBindingRegistry:
    """Stable provenance binding registry; not an audit ledger or resolver."""

    bindings: tuple[ProvenanceBinding, ...] = field(default_factory=tuple)
    registry_hash: str = ""
    registry_version: str = SOURCE_PROVENANCE_BINDING_REGISTRY_VERSION
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    created_by_task: str = SOURCE_PROVENANCE_TASK_ID
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.registry_version != SOURCE_PROVENANCE_BINDING_REGISTRY_VERSION:
            raise PathGovernanceValidationError(
                "registry_version must be source_provenance_binding_registry.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="registry_version",
            )
        if self.created_by_task != SOURCE_PROVENANCE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.8",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        bindings = tuple(
            item if isinstance(item, ProvenanceBinding)
            else ProvenanceBinding.from_dict(item)
            for item in self.bindings
        )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_notes(self.notes)
        metadata = _freeze_metadata(self.metadata)
        registry_hash = compute_provenance_binding_registry_hash(
            registry_version=self.registry_version,
            bindings=bindings,
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
            "bindings",
            tuple(sorted(bindings, key=lambda item: item.binding_id)),
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "registry_hash", registry_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "bindings": [item.to_canonical_dict() for item in self.bindings],
            "created_by_task": self.created_by_task,
            "metadata": _sorted_metadata_dict(self.metadata),
            "notes": list(self.notes),
            "registry_hash": self.registry_hash,
            "registry_version": self.registry_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProvenanceBindingRegistry:
        validate_known_fields(
            data,
            PROVENANCE_BINDING_REGISTRY_KNOWN_FIELDS,
            label="provenance_binding_registry",
        )
        return cls(
            bindings=tuple(
                item if isinstance(item, ProvenanceBinding)
                else ProvenanceBinding.from_dict(item)
                for item in data.get("bindings", ())
            ),
            registry_hash=data.get("registry_hash", ""),
            registry_version=data.get(
                "registry_version",
                SOURCE_PROVENANCE_BINDING_REGISTRY_VERSION,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            created_by_task=data.get("created_by_task", SOURCE_PROVENANCE_TASK_ID),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def _build_evidence_ref(
    value: SourceEvidenceRef | Mapping[str, Any],
) -> SourceEvidenceRef:
    if isinstance(value, SourceEvidenceRef):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "evidence_refs entries must be SourceEvidenceRef objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="evidence_refs",
        )
    return SourceEvidenceRef.from_dict(value)


def _build_claim_ref(value: SourceClaimRef | Mapping[str, Any]) -> SourceClaimRef:
    if isinstance(value, SourceClaimRef):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "claim_refs entries must be SourceClaimRef objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="claim_refs",
        )
    return SourceClaimRef.from_dict(value)


def _build_provenance_ref(
    value: SourceProvenanceRef | Mapping[str, Any],
) -> SourceProvenanceRef:
    if isinstance(value, SourceProvenanceRef):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "provenance_refs entries must be SourceProvenanceRef objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="provenance_refs",
        )
    return SourceProvenanceRef.from_dict(value)


def _build_binding(value: ProvenanceBinding | Mapping[str, Any]) -> ProvenanceBinding:
    if isinstance(value, ProvenanceBinding):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "bindings entries must be ProvenanceBinding objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="bindings",
        )
    return ProvenanceBinding.from_dict(value)


def _freeze_evidence_refs(
    evidence_refs: Sequence[SourceEvidenceRef | Mapping[str, Any]] | None,
) -> tuple[SourceEvidenceRef, ...]:
    raw = () if evidence_refs is None else evidence_refs
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "evidence_refs must be a sequence of SourceEvidenceRef values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="evidence_refs",
        )
    parsed = tuple(_build_evidence_ref(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.evidence_id))


def _freeze_claim_refs(
    claim_refs: Sequence[SourceClaimRef | Mapping[str, Any]] | None,
) -> tuple[SourceClaimRef, ...]:
    raw = () if claim_refs is None else claim_refs
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "claim_refs must be a sequence of SourceClaimRef values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="claim_refs",
        )
    parsed = tuple(_build_claim_ref(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.claim_id))


def _freeze_provenance_refs(
    provenance_refs: Sequence[SourceProvenanceRef | Mapping[str, Any]] | None,
) -> tuple[SourceProvenanceRef, ...]:
    raw = () if provenance_refs is None else provenance_refs
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "provenance_refs must be a sequence of SourceProvenanceRef values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="provenance_refs",
        )
    parsed = tuple(_build_provenance_ref(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.provenance_id))


def build_source_evidence_ref(
    evidence_kind: EvidenceBindingKind | str,
    source_identity: SourceIdentity | Mapping[str, Any],
    confidence: EvidenceConfidence | str = EvidenceConfidence.UNVERIFIED,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> SourceEvidenceRef:
    """Build deterministic evidence reference without verifying truth."""
    return SourceEvidenceRef(
        evidence_kind=evidence_kind,
        source_identity=_build_source_identity(source_identity),
        confidence=confidence,
        source_label=source_label,
        metadata=metadata,
    )


def build_source_claim_ref(
    claim_kind: SourceClaimKind | str,
    source_identity: SourceIdentity | Mapping[str, Any],
    claim_summary: str,
    confidence: EvidenceConfidence | str = EvidenceConfidence.UNVERIFIED,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> SourceClaimRef:
    """Build deterministic claim reference without accepting or rejecting claim."""
    return SourceClaimRef(
        claim_kind=claim_kind,
        source_identity=_build_source_identity(source_identity),
        claim_summary=claim_summary,
        confidence=confidence,
        source_label=source_label,
        metadata=metadata,
    )


def build_source_provenance_ref(
    provenance_kind: SourceProvenanceKind | str,
    source_identity: SourceIdentity | Mapping[str, Any],
    parent_source_id: str | None = None,
    derived_from: Sequence[str] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> SourceProvenanceRef:
    """Build deterministic provenance reference without graph engine."""
    return SourceProvenanceRef(
        provenance_kind=provenance_kind,
        source_identity=_build_source_identity(source_identity),
        parent_source_id=parent_source_id,
        derived_from=_freeze_derived_from(derived_from),
        source_label=source_label,
        metadata=metadata,
    )


def build_provenance_binding(
    source_identity: SourceIdentity | Mapping[str, Any],
    provenance_refs: Sequence[SourceProvenanceRef | Mapping[str, Any]] | None = None,
    evidence_refs: Sequence[SourceEvidenceRef | Mapping[str, Any]] | None = None,
    claim_refs: Sequence[SourceClaimRef | Mapping[str, Any]] | None = None,
    boundary_ref_id: str | None = None,
    authority_scope_id: str | None = None,
    path_identity_hash: str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> ProvenanceBinding:
    """Build deterministic provenance binding without resolver or Ledger write."""
    return ProvenanceBinding(
        source_identity=_build_source_identity(source_identity),
        provenance_refs=_freeze_provenance_refs(provenance_refs),
        evidence_refs=_freeze_evidence_refs(evidence_refs),
        claim_refs=_freeze_claim_refs(claim_refs),
        boundary_ref_id=boundary_ref_id,
        authority_scope_id=authority_scope_id,
        path_identity_hash=path_identity_hash,
        source_label=source_label,
        metadata=metadata,
    )


def build_provenance_binding_registry(
    bindings: Sequence[ProvenanceBinding | Mapping[str, Any]] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> ProvenanceBindingRegistry:
    """Build deterministic binding registry without audit or enforcement."""
    binding_tuple = tuple(
        _build_binding(item) for item in (() if bindings is None else bindings)
    )
    return ProvenanceBindingRegistry(
        bindings=binding_tuple,
        source_label=source_label,
        notes=(
            "P1.7.8 registry declares source provenance and evidence binding state only.",
            "Provenance binding is not truth verification; evidence reference is not "
            "Ledger write; claim binding is not claim acceptance.",
        ),
        metadata=metadata,
    )
