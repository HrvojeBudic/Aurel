"""Source identity schema and deterministic hashes (P1.7.2)."""
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
from .serialization import stable_hash
from .validation import validate_known_fields

SOURCE_IDENTITY_TASK_ID = "P1.7.2"
SOURCE_IDENTITY_SCHEMA_VERSION = "source_identity.v1"

SOURCE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "source_id",
    "source_kind",
    "source_origin",
    "source_label",
    "trust_label",
    "display_name",
    "uri_or_path",
    "content_hash",
    "metadata",
})

SOURCE_LINEAGE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "parent_source_id",
    "relationship",
    "lineage_hash",
    "notes",
    "metadata",
})

SOURCE_IDENTITY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "source_ref",
    "lineage_refs",
    "identity_hash",
    "created_by_task",
    "schema_version",
})


class SourceKind(str, Enum):
    """Source representation kind; not trust, authority, or permission."""

    OPERATOR_INPUT = "OPERATOR_INPUT"
    REPO_FILE = "REPO_FILE"
    LOCAL_FILE = "LOCAL_FILE"
    UPLOADED_FILE = "UPLOADED_FILE"
    EXTERNAL_WEB = "EXTERNAL_WEB"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    AGENT_OUTPUT = "AGENT_OUTPUT"
    MEMORY_ENTRY = "MEMORY_ENTRY"
    PATH_REF = "PATH_REF"
    UNKNOWN = "UNKNOWN"


class SourceOrigin(str, Enum):
    """Source origin hint; it does not grant authority."""

    OPERATOR = "OPERATOR"
    INTERNAL_REPO = "INTERNAL_REPO"
    LOCAL_MACHINE = "LOCAL_MACHINE"
    UPLOAD = "UPLOAD"
    EXTERNAL_NETWORK = "EXTERNAL_NETWORK"
    GOVERNED_TOOL = "GOVERNED_TOOL"
    MODEL = "MODEL"
    AGENT = "AGENT"
    MEMORY = "MEMORY"
    UNKNOWN = "UNKNOWN"


class SourceLineageRelationship(str, Enum):
    """Minimal lineage seed relationship; not a provenance graph."""

    DERIVED_FROM = "DERIVED_FROM"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    SUMMARIZED_FROM = "SUMMARIZED_FROM"
    UPLOADED_AS = "UPLOADED_AS"
    GENERATED_BY = "GENERATED_BY"
    QUOTED_FROM = "QUOTED_FROM"
    REFERENCES = "REFERENCES"
    UNKNOWN = "UNKNOWN"


def _parse_source_kind(value: SourceKind | str) -> SourceKind:
    if isinstance(value, SourceKind):
        return value
    if isinstance(value, str):
        try:
            return SourceKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="source_kind",
            ) from exc
    raise PathGovernanceError(
        "source_kind must be a string or SourceKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="source_kind",
    )


def _parse_source_origin(value: SourceOrigin | str) -> SourceOrigin:
    if isinstance(value, SourceOrigin):
        return value
    if isinstance(value, str):
        try:
            return SourceOrigin(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid source_origin: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="source_origin",
            ) from exc
    raise PathGovernanceError(
        "source_origin must be a string or SourceOrigin",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="source_origin",
    )


def _parse_lineage_relationship(
    value: SourceLineageRelationship | str,
) -> SourceLineageRelationship:
    if isinstance(value, SourceLineageRelationship):
        return value
    if isinstance(value, str):
        try:
            return SourceLineageRelationship(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid relationship: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="relationship",
            ) from exc
    raise PathGovernanceError(
        "relationship must be a string or SourceLineageRelationship",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="relationship",
    )


def _parse_projection_source_label(
    value: ProjectionSourceLabel | str,
) -> ProjectionSourceLabel:
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


def _optional_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PathGovernanceValidationError(
            f"{field_name} must be a string or None",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return value


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


def _freeze_notes(notes: Sequence[str] | None) -> tuple[str, ...]:
    raw = () if notes is None else notes
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "notes must be a sequence of strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="notes",
        )
    return tuple(str(item) for item in raw)


def compute_source_id(
    *,
    source_kind: SourceKind,
    source_origin: SourceOrigin,
    display_name: str | None,
    uri_or_path: str | None,
    content_hash: str | None,
    trust_label: SourceTrustLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute a deterministic source identifier without reading source content."""
    return stable_hash({
        "content_hash": content_hash,
        "display_name": display_name,
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "source_kind": source_kind.value,
        "source_origin": source_origin.value,
        "trust_label": trust_label.value,
        "uri_or_path": uri_or_path,
    })


def compute_lineage_hash(
    *,
    parent_source_id: str,
    relationship: SourceLineageRelationship,
    notes: tuple[str, ...],
    metadata: Mapping[str, Any],
) -> str:
    """Compute a deterministic lineage seed hash without parent lookup."""
    return stable_hash({
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "notes": list(notes),
        "parent_source_id": parent_source_id,
        "relationship": relationship.value,
    })


@dataclass(frozen=True)
class SourceRef:
    """Stable source reference; it grants no trust or command authority."""

    source_id: str
    source_kind: SourceKind = SourceKind.UNKNOWN
    source_origin: SourceOrigin = SourceOrigin.UNKNOWN
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    trust_label: SourceTrustLabel = SourceTrustLabel.UNKNOWN
    display_name: str | None = None
    uri_or_path: str | None = None
    content_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _required_string(
            self.source_id,
            field_name="source_id",
        ))
        object.__setattr__(self, "source_kind", _parse_source_kind(self.source_kind))
        object.__setattr__(self, "source_origin", _parse_source_origin(self.source_origin))
        object.__setattr__(
            self,
            "source_label",
            _parse_projection_source_label(self.source_label),
        )
        object.__setattr__(self, "trust_label", _parse_trust_label(self.trust_label))
        object.__setattr__(
            self,
            "display_name",
            _optional_string(self.display_name, field_name="display_name"),
        )
        object.__setattr__(
            self,
            "uri_or_path",
            _optional_string(self.uri_or_path, field_name="uri_or_path"),
        )
        object.__setattr__(
            self,
            "content_hash",
            _optional_string(self.content_hash, field_name="content_hash"),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "content_hash": self.content_hash,
            "display_name": self.display_name,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "source_id": self.source_id,
            "source_kind": self.source_kind.value,
            "source_label": self.source_label.value,
            "source_origin": self.source_origin.value,
            "trust_label": self.trust_label.value,
            "uri_or_path": self.uri_or_path,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceRef:
        validate_known_fields(data, SOURCE_REF_KNOWN_FIELDS, label="source_ref")
        return cls(
            source_id=data["source_id"],
            source_kind=data.get("source_kind", SourceKind.UNKNOWN),
            source_origin=data.get("source_origin", SourceOrigin.UNKNOWN),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            trust_label=data.get("trust_label", SourceTrustLabel.UNKNOWN),
            display_name=data.get("display_name"),
            uri_or_path=data.get("uri_or_path"),
            content_hash=data.get("content_hash"),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class SourceLineageRef:
    """Flat lineage seed reference; not evidence binding or graph traversal."""

    parent_source_id: str
    relationship: SourceLineageRelationship
    lineage_hash: str
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parent_source_id", _required_string(
            self.parent_source_id,
            field_name="parent_source_id",
        ))
        object.__setattr__(
            self,
            "relationship",
            _parse_lineage_relationship(self.relationship),
        )
        object.__setattr__(self, "lineage_hash", _required_string(
            self.lineage_hash,
            field_name="lineage_hash",
        ))
        object.__setattr__(self, "notes", _freeze_notes(self.notes))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "lineage_hash": self.lineage_hash,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "notes": list(self.notes),
            "parent_source_id": self.parent_source_id,
            "relationship": self.relationship.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceLineageRef:
        validate_known_fields(
            data,
            SOURCE_LINEAGE_REF_KNOWN_FIELDS,
            label="source_lineage_ref",
        )
        return cls(
            parent_source_id=data["parent_source_id"],
            relationship=data.get("relationship", SourceLineageRelationship.UNKNOWN),
            lineage_hash=data["lineage_hash"],
            notes=_freeze_notes(data.get("notes", ())),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class SourceIdentity:
    """Stable source identity object; representation only, no authority."""

    source_ref: SourceRef
    lineage_refs: tuple[SourceLineageRef, ...]
    identity_hash: str
    created_by_task: str = SOURCE_IDENTITY_TASK_ID
    schema_version: str = SOURCE_IDENTITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, SourceRef):
            raise PathGovernanceValidationError(
                "source_ref must be a SourceRef",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="source_ref",
            )
        if isinstance(self.lineage_refs, list):
            lineage_refs = tuple(self.lineage_refs)
        else:
            lineage_refs = self.lineage_refs
        if not isinstance(lineage_refs, tuple) or not all(
            isinstance(item, SourceLineageRef) for item in lineage_refs
        ):
            raise PathGovernanceValidationError(
                "lineage_refs must be a tuple of SourceLineageRef objects",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="lineage_refs",
            )
        object.__setattr__(self, "lineage_refs", lineage_refs)
        if self.created_by_task != SOURCE_IDENTITY_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.2",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        if self.schema_version != SOURCE_IDENTITY_SCHEMA_VERSION:
            raise PathGovernanceValidationError(
                "schema_version must be source_identity.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="schema_version",
            )
        object.__setattr__(self, "identity_hash", _required_string(
            self.identity_hash,
            field_name="identity_hash",
        ))

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "created_by_task": self.created_by_task,
            "identity_hash": self.identity_hash,
            "lineage_refs": [item.to_canonical_dict() for item in self.lineage_refs],
            "schema_version": self.schema_version,
            "source_ref": self.source_ref.to_canonical_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceIdentity:
        validate_known_fields(data, SOURCE_IDENTITY_KNOWN_FIELDS, label="source_identity")
        lineage_refs_raw = data.get("lineage_refs", ())
        if isinstance(lineage_refs_raw, str) or not isinstance(lineage_refs_raw, Sequence):
            raise PathGovernanceValidationError(
                "lineage_refs must be a sequence",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="lineage_refs",
            )
        return cls(
            source_ref=SourceRef.from_dict(data["source_ref"]),
            lineage_refs=tuple(SourceLineageRef.from_dict(item) for item in lineage_refs_raw),
            identity_hash=data["identity_hash"],
            created_by_task=data.get("created_by_task", SOURCE_IDENTITY_TASK_ID),
            schema_version=data.get("schema_version", SOURCE_IDENTITY_SCHEMA_VERSION),
        )


def _build_source_lineage_ref(
    value: SourceLineageRef | Mapping[str, Any],
) -> SourceLineageRef:
    if isinstance(value, SourceLineageRef):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "lineage_refs entries must be SourceLineageRef objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="lineage_refs",
        )
    validate_known_fields(
        value,
        SOURCE_LINEAGE_REF_KNOWN_FIELDS,
        label="source_lineage_ref",
    )
    parent_source_id = _required_string(
        value["parent_source_id"],
        field_name="parent_source_id",
    )
    relationship = _parse_lineage_relationship(
        value.get("relationship", SourceLineageRelationship.UNKNOWN),
    )
    notes = _freeze_notes(value.get("notes", ()))
    metadata = _freeze_metadata(value.get("metadata", {}))
    lineage_hash = value.get("lineage_hash")
    if lineage_hash is None:
        lineage_hash = compute_lineage_hash(
            parent_source_id=parent_source_id,
            relationship=relationship,
            notes=notes,
            metadata=metadata,
        )
    return SourceLineageRef(
        parent_source_id=parent_source_id,
        relationship=relationship,
        lineage_hash=lineage_hash,
        notes=notes,
        metadata=metadata,
    )


def build_source_identity(
    source_kind: SourceKind = SourceKind.UNKNOWN,
    source_origin: SourceOrigin = SourceOrigin.UNKNOWN,
    display_name: str | None = None,
    uri_or_path: str | None = None,
    content_hash: str | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    trust_label: SourceTrustLabel = SourceTrustLabel.UNKNOWN,
    metadata: Mapping[str, Any] | None = None,
    lineage_refs: Sequence[SourceLineageRef | Mapping[str, Any]] | None = None,
) -> SourceIdentity:
    """Build deterministic source identity without fetching, reading, or trusting it."""
    parsed_kind = _parse_source_kind(source_kind)
    parsed_origin = _parse_source_origin(source_origin)
    parsed_source_label = _parse_projection_source_label(source_label)
    parsed_trust_label = _parse_trust_label(trust_label)
    parsed_display_name = _optional_string(display_name, field_name="display_name")
    parsed_uri_or_path = _optional_string(uri_or_path, field_name="uri_or_path")
    parsed_content_hash = _optional_string(content_hash, field_name="content_hash")
    frozen_metadata = _freeze_metadata(metadata)
    source_id = compute_source_id(
        source_kind=parsed_kind,
        source_origin=parsed_origin,
        display_name=parsed_display_name,
        uri_or_path=parsed_uri_or_path,
        content_hash=parsed_content_hash,
        trust_label=parsed_trust_label,
        metadata=frozen_metadata,
    )
    source_ref = SourceRef(
        source_id=source_id,
        source_kind=parsed_kind,
        source_origin=parsed_origin,
        source_label=parsed_source_label,
        trust_label=parsed_trust_label,
        display_name=parsed_display_name,
        uri_or_path=parsed_uri_or_path,
        content_hash=parsed_content_hash,
        metadata=frozen_metadata,
    )
    lineage_tuple = tuple(
        _build_source_lineage_ref(item) for item in (() if lineage_refs is None else lineage_refs)
    )
    identity_hash = stable_hash({
        "lineage_refs": [item.to_canonical_dict() for item in lineage_tuple],
        "schema_version": SOURCE_IDENTITY_SCHEMA_VERSION,
        "source_ref": source_ref.to_canonical_dict(),
    })
    return SourceIdentity(
        source_ref=source_ref,
        lineage_refs=lineage_tuple,
        identity_hash=identity_hash,
    )
