"""Untrusted content boundary declarations and deterministic hashes (P1.7.7)."""
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

UNTRUSTED_CONTENT_BOUNDARY_TASK_ID = "P1.7.7"
UNTRUSTED_CONTENT_BOUNDARY_VERSION = "untrusted_content_boundary.v1"
UNTRUSTED_CONTENT_BOUNDARY_REGISTRY_VERSION = "untrusted_content_boundary_registry.v1"

BOUNDARY_RESTRICTION_KNOWN_FIELDS: frozenset[str] = frozenset({
    "restriction_id",
    "restriction_kind",
    "surface",
    "reason",
    "source_label",
    "metadata",
})

UNTRUSTED_CONTENT_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "boundary_id",
    "content_kind",
    "source_identity",
    "trust_label",
    "posture",
    "influence_surfaces",
    "restrictions",
    "source_label",
    "boundary_hash",
    "created_by_task",
    "boundary_version",
    "metadata",
})

UNTRUSTED_CONTENT_BOUNDARY_REGISTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "registry_version",
    "boundaries",
    "registry_hash",
    "source_label",
    "created_by_task",
    "notes",
    "metadata",
})


class UntrustedContentKind(str, Enum):
    """Declared content kind; content kind does not decide trust or authority."""

    EXTERNAL_TEXT = "EXTERNAL_TEXT"
    UPLOADED_FILE_CONTENT = "UPLOADED_FILE_CONTENT"
    WEB_CONTENT = "WEB_CONTENT"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    AGENT_OUTPUT = "AGENT_OUTPUT"
    MEMORY_RECALL = "MEMORY_RECALL"
    PATH_REFERENCED_CONTENT = "PATH_REFERENCED_CONTENT"
    UNKNOWN = "UNKNOWN"


class ContentInfluenceSurface(str, Enum):
    """Declared influence surface; influence surface does not grant permission."""

    INFORMATIONAL_CONTEXT = "INFORMATIONAL_CONTEXT"
    CITATION = "CITATION"
    SUMMARY = "SUMMARY"
    PROMPT_INSTRUCTION = "PROMPT_INSTRUCTION"
    TOOL_ARGUMENT = "TOOL_ARGUMENT"
    MEMORY_WRITE = "MEMORY_WRITE"
    POLICY_DEFINITION = "POLICY_DEFINITION"
    AUTHORITY_EXPANSION = "AUTHORITY_EXPANSION"
    EXECUTION_REQUEST = "EXECUTION_REQUEST"
    SOURCE_CANONIZATION = "SOURCE_CANONIZATION"
    UNKNOWN = "UNKNOWN"


class BoundaryRestrictionKind(str, Enum):
    """Declared future-governance restriction; restriction kind does not enforce."""

    REQUIRES_SOURCE_LABEL = "REQUIRES_SOURCE_LABEL"
    REQUIRES_TRUST_REVIEW = "REQUIRES_TRUST_REVIEW"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_POLICY_REVIEW = "REQUIRES_POLICY_REVIEW"
    REQUIRES_QUARANTINE_LATER = "REQUIRES_QUARANTINE_LATER"
    RESTRICTS_PROMPT_INSTRUCTION = "RESTRICTS_PROMPT_INSTRUCTION"
    RESTRICTS_TOOL_ARGUMENT = "RESTRICTS_TOOL_ARGUMENT"
    RESTRICTS_MEMORY_WRITE = "RESTRICTS_MEMORY_WRITE"
    RESTRICTS_POLICY_DEFINITION = "RESTRICTS_POLICY_DEFINITION"
    RESTRICTS_AUTHORITY_EXPANSION = "RESTRICTS_AUTHORITY_EXPANSION"
    RESTRICTS_EXECUTION_REQUEST = "RESTRICTS_EXECUTION_REQUEST"
    UNKNOWN = "UNKNOWN"


class UntrustedBoundaryPosture(str, Enum):
    """Declared boundary posture; posture does not execute, block, or authorize."""

    INFORM_ONLY = "INFORM_ONLY"
    QUOTABLE = "QUOTABLE"
    SUMMARIZABLE = "SUMMARIZABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    QUARANTINED = "QUARANTINED"
    UNKNOWN = "UNKNOWN"


_SURFACE_TO_RESTRICTION_KIND: dict[ContentInfluenceSurface, BoundaryRestrictionKind] = {
    ContentInfluenceSurface.PROMPT_INSTRUCTION: (
        BoundaryRestrictionKind.RESTRICTS_PROMPT_INSTRUCTION
    ),
    ContentInfluenceSurface.TOOL_ARGUMENT: BoundaryRestrictionKind.RESTRICTS_TOOL_ARGUMENT,
    ContentInfluenceSurface.MEMORY_WRITE: BoundaryRestrictionKind.RESTRICTS_MEMORY_WRITE,
    ContentInfluenceSurface.POLICY_DEFINITION: (
        BoundaryRestrictionKind.RESTRICTS_POLICY_DEFINITION
    ),
    ContentInfluenceSurface.AUTHORITY_EXPANSION: (
        BoundaryRestrictionKind.RESTRICTS_AUTHORITY_EXPANSION
    ),
    ContentInfluenceSurface.EXECUTION_REQUEST: (
        BoundaryRestrictionKind.RESTRICTS_EXECUTION_REQUEST
    ),
    ContentInfluenceSurface.SOURCE_CANONIZATION: (
        BoundaryRestrictionKind.RESTRICTS_AUTHORITY_EXPANSION
    ),
}

_COMMAND_SURFACES: tuple[ContentInfluenceSurface, ...] = (
    ContentInfluenceSurface.PROMPT_INSTRUCTION,
    ContentInfluenceSurface.TOOL_ARGUMENT,
    ContentInfluenceSurface.MEMORY_WRITE,
    ContentInfluenceSurface.POLICY_DEFINITION,
    ContentInfluenceSurface.AUTHORITY_EXPANSION,
    ContentInfluenceSurface.EXECUTION_REQUEST,
    ContentInfluenceSurface.SOURCE_CANONIZATION,
)


def _parse_content_kind(value: UntrustedContentKind | str) -> UntrustedContentKind:
    if isinstance(value, UntrustedContentKind):
        return value
    if isinstance(value, str):
        try:
            return UntrustedContentKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid content_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="content_kind",
            ) from exc
    raise PathGovernanceError(
        "content_kind must be a string or UntrustedContentKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="content_kind",
    )


def _parse_influence_surface(
    value: ContentInfluenceSurface | str,
) -> ContentInfluenceSurface:
    if isinstance(value, ContentInfluenceSurface):
        return value
    if isinstance(value, str):
        try:
            return ContentInfluenceSurface(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid influence surface: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="influence_surfaces",
            ) from exc
    raise PathGovernanceError(
        "influence surface must be a string or ContentInfluenceSurface",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="influence_surfaces",
    )


def _parse_restriction_kind(
    value: BoundaryRestrictionKind | str,
) -> BoundaryRestrictionKind:
    if isinstance(value, BoundaryRestrictionKind):
        return value
    if isinstance(value, str):
        try:
            return BoundaryRestrictionKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid restriction_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="restriction_kind",
            ) from exc
    raise PathGovernanceError(
        "restriction_kind must be a string or BoundaryRestrictionKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="restriction_kind",
    )


def _parse_posture(value: UntrustedBoundaryPosture | str) -> UntrustedBoundaryPosture:
    if isinstance(value, UntrustedBoundaryPosture):
        return value
    if isinstance(value, str):
        try:
            return UntrustedBoundaryPosture(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid posture: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="posture",
            ) from exc
    raise PathGovernanceError(
        "posture must be a string or UntrustedBoundaryPosture",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="posture",
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


def _freeze_surfaces(
    surfaces: Sequence[ContentInfluenceSurface | str] | None,
    *,
    field_name: str,
) -> tuple[ContentInfluenceSurface, ...]:
    raw = () if surfaces is None else surfaces
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            f"{field_name} must be a sequence of ContentInfluenceSurface values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    parsed = tuple(_parse_influence_surface(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.value))


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


def _restriction_kind_for_surface(
    surface: ContentInfluenceSurface,
) -> BoundaryRestrictionKind:
    return _SURFACE_TO_RESTRICTION_KIND.get(
        surface,
        BoundaryRestrictionKind.UNKNOWN,
    )


def _make_default_restriction(
    surface: ContentInfluenceSurface,
    *,
    trust_label: SourceTrustLabel,
    source_label: ProjectionSourceLabel,
) -> BoundaryRestriction:
    return BoundaryRestriction(
        restriction_kind=_restriction_kind_for_surface(surface),
        surface=surface,
        reason=f"trust_label default declaration for {trust_label.value}",
        source_label=source_label,
    )


def default_posture_for_trust_label(
    trust_label: SourceTrustLabel | str,
) -> UntrustedBoundaryPosture:
    """Return declarative default posture for a trust label; not a resolver decision."""
    parsed = _parse_trust_label(trust_label)
    mapping: dict[SourceTrustLabel, UntrustedBoundaryPosture] = {
        SourceTrustLabel.TRUSTED: UntrustedBoundaryPosture.SUMMARIZABLE,
        SourceTrustLabel.OPERATOR_PROVIDED: UntrustedBoundaryPosture.REVIEW_REQUIRED,
        SourceTrustLabel.INTERNAL_REPO: UntrustedBoundaryPosture.SUMMARIZABLE,
        SourceTrustLabel.LOCAL_PRIVATE: UntrustedBoundaryPosture.REVIEW_REQUIRED,
        SourceTrustLabel.TOOL_GENERATED: UntrustedBoundaryPosture.SUMMARIZABLE,
        SourceTrustLabel.EXTERNAL: UntrustedBoundaryPosture.INFORM_ONLY,
        SourceTrustLabel.UNTRUSTED: UntrustedBoundaryPosture.INFORM_ONLY,
        SourceTrustLabel.UNKNOWN: UntrustedBoundaryPosture.REVIEW_REQUIRED,
        SourceTrustLabel.QUARANTINED: UntrustedBoundaryPosture.QUARANTINED,
    }
    return mapping.get(parsed, UntrustedBoundaryPosture.UNKNOWN)


def default_influence_surfaces_for_trust_label(
    trust_label: SourceTrustLabel | str,
) -> tuple[ContentInfluenceSurface, ...]:
    """Return declarative default influence surfaces; not permission or enforcement."""
    parsed = _parse_trust_label(trust_label)
    mapping: dict[SourceTrustLabel, tuple[ContentInfluenceSurface, ...]] = {
        SourceTrustLabel.TRUSTED: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.CITATION,
            ContentInfluenceSurface.SUMMARY,
        ),
        SourceTrustLabel.OPERATOR_PROVIDED: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
        ),
        SourceTrustLabel.INTERNAL_REPO: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.SUMMARY,
        ),
        SourceTrustLabel.LOCAL_PRIVATE: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
        ),
        SourceTrustLabel.TOOL_GENERATED: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.SUMMARY,
        ),
        SourceTrustLabel.EXTERNAL: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.CITATION,
        ),
        SourceTrustLabel.UNTRUSTED: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
            ContentInfluenceSurface.CITATION,
        ),
        SourceTrustLabel.UNKNOWN: (
            ContentInfluenceSurface.INFORMATIONAL_CONTEXT,
        ),
        SourceTrustLabel.QUARANTINED: (),
    }
    return mapping.get(parsed, (ContentInfluenceSurface.UNKNOWN,))


def _restricted_surfaces_for_trust_label(
    trust_label: SourceTrustLabel,
) -> tuple[ContentInfluenceSurface, ...]:
    mapping: dict[SourceTrustLabel, tuple[ContentInfluenceSurface, ...]] = {
        SourceTrustLabel.TRUSTED: (
            ContentInfluenceSurface.AUTHORITY_EXPANSION,
            ContentInfluenceSurface.POLICY_DEFINITION,
            ContentInfluenceSurface.EXECUTION_REQUEST,
        ),
        SourceTrustLabel.OPERATOR_PROVIDED: (
            ContentInfluenceSurface.AUTHORITY_EXPANSION,
            ContentInfluenceSurface.POLICY_DEFINITION,
            ContentInfluenceSurface.MEMORY_WRITE,
        ),
        SourceTrustLabel.INTERNAL_REPO: (
            ContentInfluenceSurface.EXECUTION_REQUEST,
            ContentInfluenceSurface.TOOL_ARGUMENT,
            ContentInfluenceSurface.POLICY_DEFINITION,
        ),
        SourceTrustLabel.LOCAL_PRIVATE: (
            ContentInfluenceSurface.MEMORY_WRITE,
            ContentInfluenceSurface.PROMPT_INSTRUCTION,
            ContentInfluenceSurface.TOOL_ARGUMENT,
            ContentInfluenceSurface.AUTHORITY_EXPANSION,
        ),
        SourceTrustLabel.TOOL_GENERATED: (
            ContentInfluenceSurface.POLICY_DEFINITION,
            ContentInfluenceSurface.AUTHORITY_EXPANSION,
            ContentInfluenceSurface.MEMORY_WRITE,
            ContentInfluenceSurface.TOOL_ARGUMENT,
        ),
        SourceTrustLabel.EXTERNAL: _COMMAND_SURFACES,
        SourceTrustLabel.UNTRUSTED: _COMMAND_SURFACES,
        SourceTrustLabel.UNKNOWN: _COMMAND_SURFACES,
        SourceTrustLabel.QUARANTINED: _COMMAND_SURFACES,
    }
    return mapping.get(trust_label, _COMMAND_SURFACES)


def default_restrictions_for_trust_label(
    trust_label: SourceTrustLabel | str,
    *,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
) -> tuple[BoundaryRestriction, ...]:
    """Return declarative default restrictions for a trust label; not enforcement."""
    parsed = _parse_trust_label(trust_label)
    parsed_source_label = _parse_source_label(source_label)
    restricted = _restricted_surfaces_for_trust_label(parsed)
    return tuple(
        _make_default_restriction(
            surface,
            trust_label=parsed,
            source_label=parsed_source_label,
        )
        for surface in restricted
    )


def compute_restriction_id(
    *,
    restriction_kind: BoundaryRestrictionKind,
    surface: ContentInfluenceSurface,
    reason: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic restriction identifier without enforcing policy."""
    return stable_hash({
        "metadata": _sorted_metadata_dict(metadata),
        "reason": reason,
        "restriction_kind": restriction_kind.value,
        "surface": surface.value,
    })


def _restriction_canonical_payload(
    restriction: BoundaryRestriction,
) -> dict[str, Any]:
    return {
        "metadata": _sorted_metadata_dict(restriction.metadata),
        "reason": restriction.reason,
        "restriction_id": restriction.restriction_id,
        "restriction_kind": restriction.restriction_kind.value,
        "source_label": restriction.source_label.value,
        "surface": restriction.surface.value,
    }


def compute_boundary_id(
    *,
    content_kind: UntrustedContentKind,
    source_identity: SourceIdentity,
    trust_label: SourceTrustLabel,
    posture: UntrustedBoundaryPosture,
    influence_surfaces: tuple[ContentInfluenceSurface, ...],
    restrictions: tuple[BoundaryRestriction, ...],
    boundary_version: str = UNTRUSTED_CONTENT_BOUNDARY_VERSION,
) -> str:
    """Compute deterministic boundary identifier without resolving trust."""
    return stable_hash({
        "boundary_version": boundary_version,
        "content_kind": content_kind.value,
        "influence_surfaces": [item.value for item in influence_surfaces],
        "posture": posture.value,
        "restrictions": [
            _restriction_canonical_payload(item)
            for item in sorted(restrictions, key=lambda item: item.restriction_id)
        ],
        "source_identity": source_identity.to_canonical_dict(),
        "source_identity_hash": source_identity.identity_hash,
        "trust_label": trust_label.value,
    })


def compute_boundary_hash(
    *,
    boundary_id: str,
    content_kind: UntrustedContentKind,
    source_identity: SourceIdentity,
    trust_label: SourceTrustLabel,
    posture: UntrustedBoundaryPosture,
    influence_surfaces: tuple[ContentInfluenceSurface, ...],
    restrictions: tuple[BoundaryRestriction, ...],
    source_label: ProjectionSourceLabel,
    created_by_task: str,
    boundary_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic boundary hash over canonical boundary payload."""
    return stable_hash({
        "boundary_id": boundary_id,
        "boundary_version": boundary_version,
        "content_kind": content_kind.value,
        "created_by_task": created_by_task,
        "influence_surfaces": [item.value for item in influence_surfaces],
        "metadata": _sorted_metadata_dict(metadata),
        "posture": posture.value,
        "restrictions": [
            _restriction_canonical_payload(item)
            for item in sorted(restrictions, key=lambda item: item.restriction_id)
        ],
        "source_identity": source_identity.to_canonical_dict(),
        "source_label": source_label.value,
        "trust_label": trust_label.value,
    })


def compute_untrusted_boundary_registry_hash(
    *,
    registry_version: str,
    boundaries: Sequence[UntrustedContentBoundary],
    created_by_task: str,
) -> str:
    """Compute deterministic order-insensitive untrusted boundary registry hash."""
    return stable_hash({
        "boundaries": [
            item.to_canonical_dict()
            for item in sorted(boundaries, key=lambda boundary: boundary.boundary_id)
        ],
        "created_by_task": created_by_task,
        "registry_version": registry_version,
    })


@dataclass(frozen=True)
class BoundaryRestriction:
    """Declared future-governance restriction; it does not filter or enforce."""

    restriction_kind: BoundaryRestrictionKind
    surface: ContentInfluenceSurface
    reason: str
    restriction_id: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        restriction_kind = _parse_restriction_kind(self.restriction_kind)
        surface = _parse_influence_surface(self.surface)
        reason = _required_string(self.reason, field_name="reason")
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        restriction_id = compute_restriction_id(
            restriction_kind=restriction_kind,
            surface=surface,
            reason=reason,
            metadata=metadata,
        )
        if self.restriction_id not in ("", restriction_id):
            raise PathGovernanceValidationError(
                "restriction_id does not match restriction content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="restriction_id",
            )
        object.__setattr__(self, "restriction_kind", restriction_kind)
        object.__setattr__(self, "surface", surface)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "restriction_id", restriction_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _restriction_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BoundaryRestriction:
        validate_known_fields(
            data,
            BOUNDARY_RESTRICTION_KNOWN_FIELDS,
            label="boundary_restriction",
        )
        return cls(
            restriction_kind=data["restriction_kind"],
            surface=data["surface"],
            reason=data["reason"],
            restriction_id=data.get("restriction_id", ""),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class UntrustedContentBoundary:
    """Declared untrusted content boundary; not a firewall, filter, or enforcement."""

    content_kind: UntrustedContentKind
    source_identity: SourceIdentity
    trust_label: SourceTrustLabel
    posture: UntrustedBoundaryPosture = UntrustedBoundaryPosture.UNKNOWN
    influence_surfaces: tuple[ContentInfluenceSurface, ...] = field(default_factory=tuple)
    restrictions: tuple[BoundaryRestriction, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    boundary_id: str = ""
    boundary_hash: str = ""
    created_by_task: str = UNTRUSTED_CONTENT_BOUNDARY_TASK_ID
    boundary_version: str = UNTRUSTED_CONTENT_BOUNDARY_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.boundary_version != UNTRUSTED_CONTENT_BOUNDARY_VERSION:
            raise PathGovernanceValidationError(
                "boundary_version must be untrusted_content_boundary.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="boundary_version",
            )
        if self.created_by_task != UNTRUSTED_CONTENT_BOUNDARY_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.7",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        content_kind = _parse_content_kind(self.content_kind)
        source_identity = _build_source_identity(self.source_identity)
        trust_label = _parse_trust_label(self.trust_label)
        posture = _parse_posture(self.posture)
        influence_surfaces = _freeze_surfaces(
            self.influence_surfaces,
            field_name="influence_surfaces",
        )
        restrictions = _freeze_restrictions(self.restrictions)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        boundary_id = compute_boundary_id(
            content_kind=content_kind,
            source_identity=source_identity,
            trust_label=trust_label,
            posture=posture,
            influence_surfaces=influence_surfaces,
            restrictions=restrictions,
            boundary_version=self.boundary_version,
        )
        if self.boundary_id not in ("", boundary_id):
            raise PathGovernanceValidationError(
                "boundary_id does not match boundary content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="boundary_id",
            )
        boundary_hash = compute_boundary_hash(
            boundary_id=boundary_id,
            content_kind=content_kind,
            source_identity=source_identity,
            trust_label=trust_label,
            posture=posture,
            influence_surfaces=influence_surfaces,
            restrictions=restrictions,
            source_label=source_label,
            created_by_task=self.created_by_task,
            boundary_version=self.boundary_version,
            metadata=metadata,
        )
        if self.boundary_hash not in ("", boundary_hash):
            raise PathGovernanceValidationError(
                "boundary_hash does not match boundary content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="boundary_hash",
            )
        object.__setattr__(self, "content_kind", content_kind)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "trust_label", trust_label)
        object.__setattr__(self, "posture", posture)
        object.__setattr__(self, "influence_surfaces", influence_surfaces)
        object.__setattr__(self, "restrictions", restrictions)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "boundary_hash", boundary_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundary_hash": self.boundary_hash,
            "boundary_id": self.boundary_id,
            "boundary_version": self.boundary_version,
            "content_kind": self.content_kind.value,
            "created_by_task": self.created_by_task,
            "influence_surfaces": [item.value for item in self.influence_surfaces],
            "metadata": _sorted_metadata_dict(self.metadata),
            "posture": self.posture.value,
            "restrictions": [item.to_canonical_dict() for item in self.restrictions],
            "source_identity": self.source_identity.to_canonical_dict(),
            "source_label": self.source_label.value,
            "trust_label": self.trust_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UntrustedContentBoundary:
        validate_known_fields(
            data,
            UNTRUSTED_CONTENT_BOUNDARY_KNOWN_FIELDS,
            label="untrusted_content_boundary",
        )
        source_identity = data["source_identity"]
        return cls(
            content_kind=data["content_kind"],
            source_identity=(
                source_identity
                if isinstance(source_identity, SourceIdentity)
                else SourceIdentity.from_dict(source_identity)
            ),
            trust_label=data["trust_label"],
            posture=data.get("posture", UntrustedBoundaryPosture.UNKNOWN),
            influence_surfaces=data.get("influence_surfaces", ()),
            restrictions=tuple(
                item if isinstance(item, BoundaryRestriction)
                else BoundaryRestriction.from_dict(item)
                for item in data.get("restrictions", ())
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            boundary_id=data.get("boundary_id", ""),
            boundary_hash=data.get("boundary_hash", ""),
            created_by_task=data.get(
                "created_by_task",
                UNTRUSTED_CONTENT_BOUNDARY_TASK_ID,
            ),
            boundary_version=data.get(
                "boundary_version",
                UNTRUSTED_CONTENT_BOUNDARY_VERSION,
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class UntrustedContentBoundaryRegistry:
    """Stable untrusted content boundary registry; not a firewall or resolver."""

    boundaries: tuple[UntrustedContentBoundary, ...] = field(default_factory=tuple)
    registry_hash: str = ""
    registry_version: str = UNTRUSTED_CONTENT_BOUNDARY_REGISTRY_VERSION
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    created_by_task: str = UNTRUSTED_CONTENT_BOUNDARY_TASK_ID
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.registry_version != UNTRUSTED_CONTENT_BOUNDARY_REGISTRY_VERSION:
            raise PathGovernanceValidationError(
                "registry_version must be untrusted_content_boundary_registry.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="registry_version",
            )
        if self.created_by_task != UNTRUSTED_CONTENT_BOUNDARY_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.7",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        boundaries = tuple(
            item if isinstance(item, UntrustedContentBoundary)
            else UntrustedContentBoundary.from_dict(item)
            for item in self.boundaries
        )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_notes(self.notes)
        metadata = _freeze_metadata(self.metadata)
        registry_hash = compute_untrusted_boundary_registry_hash(
            registry_version=self.registry_version,
            boundaries=boundaries,
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
            "boundaries",
            tuple(sorted(boundaries, key=lambda item: item.boundary_id)),
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "registry_hash", registry_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundaries": [item.to_canonical_dict() for item in self.boundaries],
            "created_by_task": self.created_by_task,
            "metadata": _sorted_metadata_dict(self.metadata),
            "notes": list(self.notes),
            "registry_hash": self.registry_hash,
            "registry_version": self.registry_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UntrustedContentBoundaryRegistry:
        validate_known_fields(
            data,
            UNTRUSTED_CONTENT_BOUNDARY_REGISTRY_KNOWN_FIELDS,
            label="untrusted_content_boundary_registry",
        )
        return cls(
            boundaries=tuple(
                item if isinstance(item, UntrustedContentBoundary)
                else UntrustedContentBoundary.from_dict(item)
                for item in data.get("boundaries", ())
            ),
            registry_hash=data.get("registry_hash", ""),
            registry_version=data.get(
                "registry_version",
                UNTRUSTED_CONTENT_BOUNDARY_REGISTRY_VERSION,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            created_by_task=data.get(
                "created_by_task",
                UNTRUSTED_CONTENT_BOUNDARY_TASK_ID,
            ),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def _freeze_restrictions(
    restrictions: Sequence[BoundaryRestriction | Mapping[str, Any]] | None,
) -> tuple[BoundaryRestriction, ...]:
    raw = () if restrictions is None else restrictions
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "restrictions must be a sequence of BoundaryRestriction values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="restrictions",
        )
    parsed = tuple(_build_restriction(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.restriction_id))


def _build_restriction(
    value: BoundaryRestriction | Mapping[str, Any],
) -> BoundaryRestriction:
    if isinstance(value, BoundaryRestriction):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "restrictions entries must be BoundaryRestriction objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="restrictions",
        )
    return BoundaryRestriction.from_dict(value)


def _build_boundary(
    value: UntrustedContentBoundary | Mapping[str, Any],
) -> UntrustedContentBoundary:
    if isinstance(value, UntrustedContentBoundary):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "boundaries entries must be UntrustedContentBoundary objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="boundaries",
        )
    return UntrustedContentBoundary.from_dict(value)


def build_untrusted_content_boundary(
    content_kind: UntrustedContentKind | str,
    source_identity: SourceIdentity | Mapping[str, Any],
    trust_label: SourceTrustLabel | str,
    *,
    influence_surfaces: Sequence[ContentInfluenceSurface | str] | None = None,
    restrictions: Sequence[BoundaryRestriction | Mapping[str, Any]] | None = None,
    posture: UntrustedBoundaryPosture | str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> UntrustedContentBoundary:
    """Build deterministic untrusted content boundary without filtering or enforcing."""
    parsed_trust_label = _parse_trust_label(trust_label)
    resolved_posture = (
        default_posture_for_trust_label(parsed_trust_label)
        if posture is None
        else _parse_posture(posture)
    )
    resolved_surfaces = (
        default_influence_surfaces_for_trust_label(parsed_trust_label)
        if influence_surfaces is None
        else _freeze_surfaces(influence_surfaces, field_name="influence_surfaces")
    )
    resolved_restrictions = (
        default_restrictions_for_trust_label(
            parsed_trust_label,
            source_label=source_label,
        )
        if restrictions is None
        else _freeze_restrictions(restrictions)
    )
    return UntrustedContentBoundary(
        content_kind=content_kind,
        source_identity=_build_source_identity(source_identity),
        trust_label=parsed_trust_label,
        posture=resolved_posture,
        influence_surfaces=resolved_surfaces,
        restrictions=resolved_restrictions,
        source_label=source_label,
        metadata=metadata,
    )


def build_untrusted_content_boundary_registry(
    boundaries: Sequence[UntrustedContentBoundary | Mapping[str, Any]] | None = None,
    *,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> UntrustedContentBoundaryRegistry:
    """Build deterministic boundary registry without filtering or enforcing."""
    boundary_tuple = tuple(
        _build_boundary(item) for item in (() if boundaries is None else boundaries)
    )
    return UntrustedContentBoundaryRegistry(
        boundaries=boundary_tuple,
        source_label=source_label,
        notes=(
            "P1.7.7 registry declares untrusted content boundary state only.",
            "Content boundaries are not firewalls, prompt filters, memory gates, "
            "tool blockers, resolver output, or enforcement.",
        ),
        metadata=metadata,
    )
