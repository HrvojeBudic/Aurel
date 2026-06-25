"""Path identity schema and deterministic hashes (P1.7.1)."""
from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .canonical_path import normalize_path_string, path_normalization_warnings
from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceValidationError,
)
from .labels import ProjectionSourceLabel
from .serialization import stable_hash
from .validation import validate_known_fields

PATH_IDENTITY_TASK_ID = "P1.7.1"
PATH_IDENTITY_SCHEMA_VERSION = "path_identity.v1"

PATH_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "raw_path",
    "path_kind",
    "declared_sensitivity",
    "source_label",
    "metadata",
})

CANONICAL_PATH_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "raw_path",
    "normalized_path",
    "display_path",
    "path_kind",
    "canonicalization_status",
    "path_hash",
    "canonical_hash",
    "source_label",
    "warnings",
    "metadata",
})

PATH_IDENTITY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "path_ref",
    "canonical_ref",
    "identity_hash",
    "created_by_task",
    "schema_version",
})


class PathKind(str, Enum):
    """Declared path interpretation kind; not authority or safety."""

    REPO_RELATIVE = "REPO_RELATIVE"
    LOCAL_ABSOLUTE = "LOCAL_ABSOLUTE"
    LOCAL_RELATIVE = "LOCAL_RELATIVE"
    WORKSPACE_RELATIVE = "WORKSPACE_RELATIVE"
    UPLOAD_REF = "UPLOAD_REF"
    VIRTUAL = "VIRTUAL"
    UNKNOWN = "UNKNOWN"


class PathSensitivity(str, Enum):
    """Declared path sensitivity; no secret scanning is performed."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PRIVATE = "PRIVATE"
    SECRET_CANDIDATE = "SECRET_CANDIDATE"
    UNKNOWN = "UNKNOWN"


class CanonicalizationStatus(str, Enum):
    """String representation status; not trust, permission, or authority."""

    CANONICAL = "CANONICAL"
    NORMALIZED_ONLY = "NORMALIZED_ONLY"
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


def _parse_path_kind(value: PathKind | str) -> PathKind:
    if isinstance(value, PathKind):
        return value
    if isinstance(value, str):
        try:
            return PathKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid path_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="path_kind",
            ) from exc
    raise PathGovernanceError(
        "path_kind must be a string or PathKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="path_kind",
    )


def _parse_path_sensitivity(value: PathSensitivity | str) -> PathSensitivity:
    if isinstance(value, PathSensitivity):
        return value
    if isinstance(value, str):
        try:
            return PathSensitivity(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid declared_sensitivity: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="declared_sensitivity",
            ) from exc
    raise PathGovernanceError(
        "declared_sensitivity must be a string or PathSensitivity",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="declared_sensitivity",
    )


def _parse_canonicalization_status(
    value: CanonicalizationStatus | str,
) -> CanonicalizationStatus:
    if isinstance(value, CanonicalizationStatus):
        return value
    if isinstance(value, str):
        try:
            return CanonicalizationStatus(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid canonicalization_status: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="canonicalization_status",
            ) from exc
    raise PathGovernanceError(
        "canonicalization_status must be a string or CanonicalizationStatus",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="canonicalization_status",
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


def _validate_raw_path(raw_path: Any) -> str:
    if not isinstance(raw_path, str) or raw_path == "":
        raise PathGovernanceValidationError(
            "raw_path must be a non-empty string",
            code=PathGovernanceErrorCode.CANONICALIZATION_NOT_AVAILABLE,
            field="raw_path",
        )
    return raw_path


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


def _freeze_warnings(warnings: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    raw = () if warnings is None else warnings
    if isinstance(raw, str) or not isinstance(raw, (tuple, list)):
        raise PathGovernanceValidationError(
            "warnings must be a list or tuple of strings",
            code=PathGovernanceErrorCode.CANONICALIZATION_NOT_AVAILABLE,
            field="warnings",
        )
    return tuple(str(item) for item in raw)


@dataclass(frozen=True)
class PathRef:
    """Raw path reference; it grants no permission or authority."""

    raw_path: str
    path_kind: PathKind = PathKind.UNKNOWN
    declared_sensitivity: PathSensitivity = PathSensitivity.UNKNOWN
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_path", _validate_raw_path(self.raw_path))
        object.__setattr__(self, "path_kind", _parse_path_kind(self.path_kind))
        object.__setattr__(
            self,
            "declared_sensitivity",
            _parse_path_sensitivity(self.declared_sensitivity),
        )
        object.__setattr__(self, "source_label", _parse_source_label(self.source_label))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "declared_sensitivity": self.declared_sensitivity.value,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "path_kind": self.path_kind.value,
            "raw_path": self.raw_path,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathRef:
        validate_known_fields(data, PATH_REF_KNOWN_FIELDS, label="path_ref")
        return cls(
            raw_path=data["raw_path"],
            path_kind=data.get("path_kind", PathKind.UNKNOWN),
            declared_sensitivity=data.get(
                "declared_sensitivity",
                PathSensitivity.UNKNOWN,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class CanonicalPathRef:
    """Normalized path representation; it is not a trusted-root decision."""

    raw_path: str
    normalized_path: str
    display_path: str
    path_kind: PathKind
    canonicalization_status: CanonicalizationStatus
    path_hash: str
    canonical_hash: str
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_path", _validate_raw_path(self.raw_path))
        if not isinstance(self.normalized_path, str):
            raise PathGovernanceValidationError(
                "normalized_path must be a string",
                code=PathGovernanceErrorCode.CANONICALIZATION_NOT_AVAILABLE,
                field="normalized_path",
            )
        if not isinstance(self.display_path, str):
            raise PathGovernanceValidationError(
                "display_path must be a string",
                code=PathGovernanceErrorCode.CANONICALIZATION_NOT_AVAILABLE,
                field="display_path",
            )
        object.__setattr__(self, "path_kind", _parse_path_kind(self.path_kind))
        object.__setattr__(
            self,
            "canonicalization_status",
            _parse_canonicalization_status(self.canonicalization_status),
        )
        object.__setattr__(self, "source_label", _parse_source_label(self.source_label))
        object.__setattr__(self, "warnings", _freeze_warnings(self.warnings))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
        for field_name in ("path_hash", "canonical_hash"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or len(value) != 64:
                raise PathGovernanceValidationError(
                    f"{field_name} must be a SHA-256 hex digest",
                    code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                    field=field_name,
                )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "canonical_hash": self.canonical_hash,
            "canonicalization_status": self.canonicalization_status.value,
            "display_path": self.display_path,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "normalized_path": self.normalized_path,
            "path_hash": self.path_hash,
            "path_kind": self.path_kind.value,
            "raw_path": self.raw_path,
            "source_label": self.source_label.value,
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalPathRef:
        validate_known_fields(
            data,
            CANONICAL_PATH_REF_KNOWN_FIELDS,
            label="canonical_path_ref",
        )
        return cls(
            raw_path=data["raw_path"],
            normalized_path=data["normalized_path"],
            display_path=data["display_path"],
            path_kind=data["path_kind"],
            canonicalization_status=data["canonicalization_status"],
            path_hash=data["path_hash"],
            canonical_hash=data["canonical_hash"],
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            warnings=_freeze_warnings(data.get("warnings", ())),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathIdentity:
    """Stable path identity object; representation only, no runtime authority."""

    path_ref: PathRef
    canonical_ref: CanonicalPathRef
    identity_hash: str
    created_by_task: str = PATH_IDENTITY_TASK_ID
    schema_version: str = PATH_IDENTITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.path_ref, PathRef):
            raise PathGovernanceValidationError(
                "path_ref must be a PathRef",
                code=PathGovernanceErrorCode.CANONICALIZATION_NOT_AVAILABLE,
                field="path_ref",
            )
        if not isinstance(self.canonical_ref, CanonicalPathRef):
            raise PathGovernanceValidationError(
                "canonical_ref must be a CanonicalPathRef",
                code=PathGovernanceErrorCode.CANONICALIZATION_NOT_AVAILABLE,
                field="canonical_ref",
            )
        if self.created_by_task != PATH_IDENTITY_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        if self.schema_version != PATH_IDENTITY_SCHEMA_VERSION:
            raise PathGovernanceValidationError(
                "schema_version must be path_identity.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="schema_version",
            )
        if not isinstance(self.identity_hash, str) or len(self.identity_hash) != 64:
            raise PathGovernanceValidationError(
                "identity_hash must be a SHA-256 hex digest",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="identity_hash",
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "canonical_ref": self.canonical_ref.to_canonical_dict(),
            "created_by_task": self.created_by_task,
            "identity_hash": self.identity_hash,
            "path_ref": self.path_ref.to_canonical_dict(),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathIdentity:
        validate_known_fields(data, PATH_IDENTITY_KNOWN_FIELDS, label="path_identity")
        return cls(
            path_ref=PathRef.from_dict(data["path_ref"]),
            canonical_ref=CanonicalPathRef.from_dict(data["canonical_ref"]),
            identity_hash=data["identity_hash"],
            created_by_task=data.get("created_by_task", PATH_IDENTITY_TASK_ID),
            schema_version=data.get("schema_version", PATH_IDENTITY_SCHEMA_VERSION),
        )


def build_path_identity(
    raw_path: str,
    path_kind: PathKind = PathKind.UNKNOWN,
    declared_sensitivity: PathSensitivity = PathSensitivity.UNKNOWN,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathIdentity:
    """Build a deterministic path identity without resolving or enforcing it."""
    path_ref = PathRef(
        raw_path=raw_path,
        path_kind=path_kind,
        declared_sensitivity=declared_sensitivity,
        source_label=source_label,
        metadata={} if metadata is None else metadata,
    )
    normalized_path = normalize_path_string(path_ref.raw_path)
    warnings = path_normalization_warnings(normalized_path)
    path_hash = stable_hash({
        "declared_sensitivity": path_ref.declared_sensitivity.value,
        "path_kind": path_ref.path_kind.value,
        "raw_path": path_ref.raw_path,
    })
    canonical_hash = stable_hash({
        "canonicalization_status": CanonicalizationStatus.NORMALIZED_ONLY.value,
        "display_path": normalized_path,
        "normalized_path": normalized_path,
        "path_kind": path_ref.path_kind.value,
        "raw_path": path_ref.raw_path,
        "warnings": list(warnings),
    })
    canonical_ref = CanonicalPathRef(
        raw_path=path_ref.raw_path,
        normalized_path=normalized_path,
        display_path=normalized_path,
        path_kind=path_ref.path_kind,
        canonicalization_status=CanonicalizationStatus.NORMALIZED_ONLY,
        path_hash=path_hash,
        canonical_hash=canonical_hash,
        source_label=path_ref.source_label,
        warnings=warnings,
        metadata=path_ref.metadata,
    )
    identity_hash = stable_hash({
        "canonical_ref": canonical_ref.to_canonical_dict(),
        "path_ref": path_ref.to_canonical_dict(),
        "schema_version": PATH_IDENTITY_SCHEMA_VERSION,
    })
    return PathIdentity(
        path_ref=path_ref,
        canonical_ref=canonical_ref,
        identity_hash=identity_hash,
    )
