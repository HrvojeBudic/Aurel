"""Path authority scope declarations and deterministic hashes (P1.7.6)."""
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
from .path_identity import PathIdentity
from .serialization import stable_hash
from .trusted_roots import PathScopeAction
from .validation import validate_known_fields

PATH_AUTHORITY_SCOPE_TASK_ID = "P1.7.6"
PATH_AUTHORITY_SCOPE_VERSION = "path_authority_scope.v1"
PATH_AUTHORITY_SCOPE_REGISTRY_VERSION = "path_authority_scope_registry.v1"

PATH_AUTHORITY_SUBJECT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "subject_kind",
    "subject_id",
    "display_name",
    "source_label",
    "metadata",
})

PATH_AUTHORITY_CONSTRAINT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "constraint_id",
    "constraint_kind",
    "reason",
    "source_label",
    "metadata",
})

PATH_AUTHORITY_SCOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "scope_id",
    "subject",
    "root_id",
    "path_identity",
    "actions",
    "basis",
    "constraints",
    "source_label",
    "scope_hash",
    "created_by_task",
    "scope_version",
    "metadata",
})

PATH_AUTHORITY_SCOPE_REGISTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "registry_version",
    "scopes",
    "registry_hash",
    "source_label",
    "created_by_task",
    "notes",
    "metadata",
})


class PathAuthoritySubjectKind(str, Enum):
    """Declared authority subject kind; subject kind does not grant authority."""

    OPERATOR = "OPERATOR"
    AGENT = "AGENT"
    TOOL = "TOOL"
    WORKFLOW = "WORKFLOW"
    MODEL = "MODEL"
    RUNTIME = "RUNTIME"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"


class PathAuthorityBasis(str, Enum):
    """Declared reason a scope exists; basis does not grant permission."""

    OPERATOR_DECLARATION = "OPERATOR_DECLARATION"
    POLICY_DECLARATION = "POLICY_DECLARATION"
    TRUSTED_ROOT_REGISTRY = "TRUSTED_ROOT_REGISTRY"
    SYSTEM_DEFAULT = "SYSTEM_DEFAULT"
    TASK_CONTEXT = "TASK_CONTEXT"
    TEST_FIXTURE = "TEST_FIXTURE"
    UNKNOWN = "UNKNOWN"


class PathAuthorityConstraintKind(str, Enum):
    """Declared future-governance constraint; constraint kind does not enforce."""

    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_POLICY_REVIEW = "REQUIRES_POLICY_REVIEW"
    REQUIRES_TRACE = "REQUIRES_TRACE"
    REQUIRES_LOCAL_ONLY = "REQUIRES_LOCAL_ONLY"
    REQUIRES_SANDBOX_LATER = "REQUIRES_SANDBOX_LATER"
    REQUIRES_NO_NETWORK_LATER = "REQUIRES_NO_NETWORK_LATER"
    RESTRICTS_EXECUTE = "RESTRICTS_EXECUTE"
    RESTRICTS_WRITE = "RESTRICTS_WRITE"
    RESTRICTS_MEMORY_USE = "RESTRICTS_MEMORY_USE"
    RESTRICTS_PROMPT_CONTEXT_USE = "RESTRICTS_PROMPT_CONTEXT_USE"
    UNKNOWN = "UNKNOWN"


def _parse_subject_kind(value: PathAuthoritySubjectKind | str) -> PathAuthoritySubjectKind:
    if isinstance(value, PathAuthoritySubjectKind):
        return value
    if isinstance(value, str):
        try:
            return PathAuthoritySubjectKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid subject_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="subject_kind",
            ) from exc
    raise PathGovernanceError(
        "subject_kind must be a string or PathAuthoritySubjectKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="subject_kind",
    )


def _parse_basis(value: PathAuthorityBasis | str) -> PathAuthorityBasis:
    if isinstance(value, PathAuthorityBasis):
        return value
    if isinstance(value, str):
        try:
            return PathAuthorityBasis(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid basis: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="basis",
            ) from exc
    raise PathGovernanceError(
        "basis must be a string or PathAuthorityBasis",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="basis",
    )


def _parse_constraint_kind(
    value: PathAuthorityConstraintKind | str,
) -> PathAuthorityConstraintKind:
    if isinstance(value, PathAuthorityConstraintKind):
        return value
    if isinstance(value, str):
        try:
            return PathAuthorityConstraintKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid constraint_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="constraint_kind",
            ) from exc
    raise PathGovernanceError(
        "constraint_kind must be a string or PathAuthorityConstraintKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="constraint_kind",
    )


def _parse_scope_action(value: PathScopeAction | str) -> PathScopeAction:
    if isinstance(value, PathScopeAction):
        return value
    if isinstance(value, str):
        try:
            return PathScopeAction(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid scope action: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="actions",
            ) from exc
    raise PathGovernanceError(
        "scope action must be a string or PathScopeAction",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="actions",
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


def _freeze_actions(
    actions: Sequence[PathScopeAction | str],
    *,
    field_name: str,
) -> tuple[PathScopeAction, ...]:
    if isinstance(actions, str) or not isinstance(actions, Sequence):
        raise PathGovernanceValidationError(
            f"{field_name} must be a sequence of PathScopeAction values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    parsed = tuple(_parse_scope_action(item) for item in actions)
    parsed = tuple(sorted(parsed, key=lambda item: item.value))
    if not parsed:
        raise PathGovernanceValidationError(
            f"{field_name} must be non-empty",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    return parsed


def _freeze_notes(notes: Sequence[str] | None) -> tuple[str, ...]:
    raw = () if notes is None else notes
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "notes must be a sequence of strings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="notes",
        )
    return tuple(str(item) for item in raw)


def _build_path_identity(value: PathIdentity | Mapping[str, Any]) -> PathIdentity:
    if isinstance(value, PathIdentity):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "path_identity must be a PathIdentity object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="path_identity",
        )
    return PathIdentity.from_dict(value)


def _sorted_metadata_dict(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return dict(sorted(metadata.items(), key=lambda item: item[0]))


def compute_subject_id(
    *,
    subject_kind: PathAuthoritySubjectKind,
    display_name: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic subject identifier without granting authority."""
    return stable_hash({
        "display_name": display_name,
        "metadata": _sorted_metadata_dict(metadata),
        "subject_kind": subject_kind.value,
    })


def compute_constraint_id(
    *,
    constraint_kind: PathAuthorityConstraintKind,
    reason: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic constraint identifier without enforcing policy."""
    return stable_hash({
        "constraint_kind": constraint_kind.value,
        "metadata": _sorted_metadata_dict(metadata),
        "reason": reason,
    })


def _constraint_canonical_payload(
    constraint: PathAuthorityConstraint,
) -> dict[str, Any]:
    return {
        "constraint_id": constraint.constraint_id,
        "constraint_kind": constraint.constraint_kind.value,
        "metadata": _sorted_metadata_dict(constraint.metadata),
        "reason": constraint.reason,
        "source_label": constraint.source_label.value,
    }


def compute_scope_id(
    *,
    subject: PathAuthoritySubject,
    root_id: str | None,
    path_identity: PathIdentity | None,
    actions: tuple[PathScopeAction, ...],
    basis: PathAuthorityBasis,
    constraints: tuple[PathAuthorityConstraint, ...],
    scope_version: str = PATH_AUTHORITY_SCOPE_VERSION,
) -> str:
    """Compute deterministic scope identifier without resolving authority."""
    payload: dict[str, Any] = {
        "actions": [item.value for item in actions],
        "basis": basis.value,
        "constraints": [
            _constraint_canonical_payload(item)
            for item in sorted(constraints, key=lambda item: item.constraint_id)
        ],
        "scope_version": scope_version,
        "subject": subject.to_canonical_dict(),
    }
    if root_id is not None:
        payload["root_id"] = root_id
    if path_identity is not None:
        payload["path_identity"] = path_identity.to_canonical_dict()
        payload["path_identity_hash"] = path_identity.identity_hash
    return stable_hash(payload)


def compute_scope_hash(
    *,
    scope_id: str,
    subject: PathAuthoritySubject,
    root_id: str | None,
    path_identity: PathIdentity | None,
    actions: tuple[PathScopeAction, ...],
    basis: PathAuthorityBasis,
    constraints: tuple[PathAuthorityConstraint, ...],
    source_label: ProjectionSourceLabel,
    created_by_task: str,
    scope_version: str,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic scope hash over canonical scope payload."""
    payload: dict[str, Any] = {
        "actions": [item.value for item in actions],
        "basis": basis.value,
        "constraints": [
            _constraint_canonical_payload(item)
            for item in sorted(constraints, key=lambda item: item.constraint_id)
        ],
        "created_by_task": created_by_task,
        "metadata": _sorted_metadata_dict(metadata),
        "scope_id": scope_id,
        "scope_version": scope_version,
        "source_label": source_label.value,
        "subject": subject.to_canonical_dict(),
    }
    if root_id is not None:
        payload["root_id"] = root_id
    if path_identity is not None:
        payload["path_identity"] = path_identity.to_canonical_dict()
    return stable_hash(payload)


def compute_authority_scope_registry_hash(
    *,
    registry_version: str,
    scopes: Sequence[PathAuthorityScope],
    created_by_task: str,
) -> str:
    """Compute deterministic order-insensitive authority scope registry hash."""
    return stable_hash({
        "created_by_task": created_by_task,
        "registry_version": registry_version,
        "scopes": [
            item.to_canonical_dict()
            for item in sorted(scopes, key=lambda scope: scope.scope_id)
        ],
    })


@dataclass(frozen=True)
class PathAuthoritySubject:
    """Declared authority subject; it grants no permission or runtime authority."""

    subject_kind: PathAuthoritySubjectKind
    display_name: str
    subject_id: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        subject_kind = _parse_subject_kind(self.subject_kind)
        display_name = _required_string(self.display_name, field_name="display_name")
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        subject_id = compute_subject_id(
            subject_kind=subject_kind,
            display_name=display_name,
            metadata=metadata,
        )
        if self.subject_id not in ("", subject_id):
            raise PathGovernanceValidationError(
                "subject_id does not match subject content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="subject_id",
            )
        object.__setattr__(self, "subject_kind", subject_kind)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "subject_id", subject_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "metadata": _sorted_metadata_dict(self.metadata),
            "source_label": self.source_label.value,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathAuthoritySubject:
        validate_known_fields(
            data,
            PATH_AUTHORITY_SUBJECT_KNOWN_FIELDS,
            label="path_authority_subject",
        )
        return cls(
            subject_kind=data["subject_kind"],
            display_name=data["display_name"],
            subject_id=data.get("subject_id", ""),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathAuthorityConstraint:
    """Declared future-governance constraint; it does not enforce policy."""

    constraint_kind: PathAuthorityConstraintKind
    reason: str
    constraint_id: str = ""
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        constraint_kind = _parse_constraint_kind(self.constraint_kind)
        reason = _required_string(self.reason, field_name="reason")
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        constraint_id = compute_constraint_id(
            constraint_kind=constraint_kind,
            reason=reason,
            metadata=metadata,
        )
        if self.constraint_id not in ("", constraint_id):
            raise PathGovernanceValidationError(
                "constraint_id does not match constraint content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="constraint_id",
            )
        object.__setattr__(self, "constraint_kind", constraint_kind)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "constraint_id", constraint_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return _constraint_canonical_payload(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathAuthorityConstraint:
        validate_known_fields(
            data,
            PATH_AUTHORITY_CONSTRAINT_KNOWN_FIELDS,
            label="path_authority_constraint",
        )
        return cls(
            constraint_kind=data["constraint_kind"],
            reason=data["reason"],
            constraint_id=data.get("constraint_id", ""),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathAuthorityScope:
    """Declared path authority scope; it is not permission, resolver output, or enforcement."""

    subject: PathAuthoritySubject
    actions: tuple[PathScopeAction, ...]
    basis: PathAuthorityBasis
    root_id: str | None = None
    path_identity: PathIdentity | None = None
    constraints: tuple[PathAuthorityConstraint, ...] = field(default_factory=tuple)
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    scope_id: str = ""
    scope_hash: str = ""
    created_by_task: str = PATH_AUTHORITY_SCOPE_TASK_ID
    scope_version: str = PATH_AUTHORITY_SCOPE_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scope_version != PATH_AUTHORITY_SCOPE_VERSION:
            raise PathGovernanceValidationError(
                "scope_version must be path_authority_scope.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="scope_version",
            )
        if self.created_by_task != PATH_AUTHORITY_SCOPE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.6",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        subject = _build_subject(self.subject)
        basis = _parse_basis(self.basis)
        actions = _freeze_actions(self.actions, field_name="actions")
        root_id = _optional_string(self.root_id, field_name="root_id")
        path_identity = (
            None
            if self.path_identity is None
            else _build_path_identity(self.path_identity)
        )
        constraints = _freeze_constraints(self.constraints)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        scope_id = compute_scope_id(
            subject=subject,
            root_id=root_id,
            path_identity=path_identity,
            actions=actions,
            basis=basis,
            constraints=constraints,
            scope_version=self.scope_version,
        )
        if self.scope_id not in ("", scope_id):
            raise PathGovernanceValidationError(
                "scope_id does not match scope content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="scope_id",
            )
        scope_hash = compute_scope_hash(
            scope_id=scope_id,
            subject=subject,
            root_id=root_id,
            path_identity=path_identity,
            actions=actions,
            basis=basis,
            constraints=constraints,
            source_label=source_label,
            created_by_task=self.created_by_task,
            scope_version=self.scope_version,
            metadata=metadata,
        )
        if self.scope_hash not in ("", scope_hash):
            raise PathGovernanceValidationError(
                "scope_hash does not match scope content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="scope_hash",
            )
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "basis", basis)
        object.__setattr__(self, "root_id", root_id)
        object.__setattr__(self, "path_identity", path_identity)
        object.__setattr__(self, "constraints", constraints)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_id", scope_id)
        object.__setattr__(self, "scope_hash", scope_hash)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "actions": [item.value for item in self.actions],
            "basis": self.basis.value,
            "constraints": [item.to_canonical_dict() for item in self.constraints],
            "created_by_task": self.created_by_task,
            "metadata": _sorted_metadata_dict(self.metadata),
            "scope_hash": self.scope_hash,
            "scope_id": self.scope_id,
            "scope_version": self.scope_version,
            "source_label": self.source_label.value,
            "subject": self.subject.to_canonical_dict(),
        }
        if self.root_id is not None:
            payload["root_id"] = self.root_id
        if self.path_identity is not None:
            payload["path_identity"] = self.path_identity.to_canonical_dict()
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathAuthorityScope:
        validate_known_fields(
            data,
            PATH_AUTHORITY_SCOPE_KNOWN_FIELDS,
            label="path_authority_scope",
        )
        return cls(
            subject=(
                data["subject"]
                if isinstance(data["subject"], PathAuthoritySubject)
                else PathAuthoritySubject.from_dict(data["subject"])
            ),
            actions=data["actions"],
            basis=data["basis"],
            root_id=data.get("root_id"),
            path_identity=data.get("path_identity"),
            constraints=tuple(
                item if isinstance(item, PathAuthorityConstraint)
                else PathAuthorityConstraint.from_dict(item)
                for item in data.get("constraints", ())
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            scope_id=data.get("scope_id", ""),
            scope_hash=data.get("scope_hash", ""),
            created_by_task=data.get("created_by_task", PATH_AUTHORITY_SCOPE_TASK_ID),
            scope_version=data.get("scope_version", PATH_AUTHORITY_SCOPE_VERSION),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathAuthorityScopeRegistry:
    """Stable authority scope declaration registry; not a resolver or sandbox."""

    scopes: tuple[PathAuthorityScope, ...] = field(default_factory=tuple)
    registry_hash: str = ""
    registry_version: str = PATH_AUTHORITY_SCOPE_REGISTRY_VERSION
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    created_by_task: str = PATH_AUTHORITY_SCOPE_TASK_ID
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.registry_version != PATH_AUTHORITY_SCOPE_REGISTRY_VERSION:
            raise PathGovernanceValidationError(
                "registry_version must be path_authority_scope_registry.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="registry_version",
            )
        if self.created_by_task != PATH_AUTHORITY_SCOPE_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.6",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        scopes = tuple(
            item if isinstance(item, PathAuthorityScope) else PathAuthorityScope.from_dict(item)
            for item in self.scopes
        )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_notes(self.notes)
        metadata = _freeze_metadata(self.metadata)
        registry_hash = compute_authority_scope_registry_hash(
            registry_version=self.registry_version,
            scopes=scopes,
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
            "scopes",
            tuple(sorted(scopes, key=lambda item: item.scope_id)),
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "registry_hash", registry_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "created_by_task": self.created_by_task,
            "metadata": _sorted_metadata_dict(self.metadata),
            "notes": list(self.notes),
            "registry_hash": self.registry_hash,
            "registry_version": self.registry_version,
            "scopes": [item.to_canonical_dict() for item in self.scopes],
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathAuthorityScopeRegistry:
        validate_known_fields(
            data,
            PATH_AUTHORITY_SCOPE_REGISTRY_KNOWN_FIELDS,
            label="path_authority_scope_registry",
        )
        return cls(
            scopes=tuple(
                item if isinstance(item, PathAuthorityScope)
                else PathAuthorityScope.from_dict(item)
                for item in data.get("scopes", ())
            ),
            registry_hash=data.get("registry_hash", ""),
            registry_version=data.get(
                "registry_version",
                PATH_AUTHORITY_SCOPE_REGISTRY_VERSION,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            created_by_task=data.get("created_by_task", PATH_AUTHORITY_SCOPE_TASK_ID),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def _freeze_constraints(
    constraints: Sequence[PathAuthorityConstraint | Mapping[str, Any]] | None,
) -> tuple[PathAuthorityConstraint, ...]:
    raw = () if constraints is None else constraints
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            "constraints must be a sequence of PathAuthorityConstraint values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="constraints",
        )
    parsed = tuple(_build_constraint(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.constraint_id))


def _build_subject(
    value: PathAuthoritySubject | Mapping[str, Any],
) -> PathAuthoritySubject:
    if isinstance(value, PathAuthoritySubject):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "subject must be a PathAuthoritySubject object or mapping",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="subject",
        )
    return PathAuthoritySubject.from_dict(value)


def _build_constraint(
    value: PathAuthorityConstraint | Mapping[str, Any],
) -> PathAuthorityConstraint:
    if isinstance(value, PathAuthorityConstraint):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "constraints entries must be PathAuthorityConstraint objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="constraints",
        )
    return PathAuthorityConstraint.from_dict(value)


def _build_scope(value: PathAuthorityScope | Mapping[str, Any]) -> PathAuthorityScope:
    if isinstance(value, PathAuthorityScope):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "scopes entries must be PathAuthorityScope objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="scopes",
        )
    return PathAuthorityScope.from_dict(value)


def build_path_authority_scope(
    subject: PathAuthoritySubject | Mapping[str, Any],
    actions: Sequence[PathScopeAction | str],
    basis: PathAuthorityBasis | str,
    *,
    root_id: str | None = None,
    path_identity: PathIdentity | Mapping[str, Any] | None = None,
    constraints: Sequence[PathAuthorityConstraint | Mapping[str, Any]] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathAuthorityScope:
    """Build deterministic path authority scope without resolving authority."""
    return PathAuthorityScope(
        subject=_build_subject(subject),
        actions=actions,
        basis=basis,
        root_id=root_id,
        path_identity=path_identity,
        constraints=_freeze_constraints(constraints),
        source_label=source_label,
        metadata=metadata,
    )


def build_path_authority_scope_registry(
    scopes: Sequence[PathAuthorityScope | Mapping[str, Any]] | None = None,
    *,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PathAuthorityScopeRegistry:
    """Build deterministic authority scope registry without resolving authority."""
    scope_tuple = tuple(
        _build_scope(item) for item in (() if scopes is None else scopes)
    )
    return PathAuthorityScopeRegistry(
        scopes=scope_tuple,
        source_label=source_label,
        notes=(
            "P1.7.6 registry declares path authority scope state only.",
            "Authority scopes are not permissions, runtime authority, "
            "sandbox policy, resolver output, or enforcement.",
        ),
        metadata=metadata,
    )
