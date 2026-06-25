"""Trusted root registry seed and deterministic hashes (P1.7.4)."""
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
from .path_identity import PathIdentity
from .serialization import stable_hash
from .validation import validate_known_fields

TRUSTED_ROOT_REGISTRY_TASK_ID = "P1.7.4"
TRUSTED_ROOT_REGISTRY_VERSION = "trusted_root_registry.v1"

TRUSTED_ROOT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "root_id",
    "root_kind",
    "path_identity",
    "display_name",
    "source_label",
    "trust_label",
    "allowed_actions",
    "denied_actions",
    "reason",
    "registry_version",
    "metadata",
})

PATH_SCOPE_GRANT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "grant_id",
    "root_id",
    "actions",
    "reason",
    "source_label",
    "metadata",
})

PATH_SCOPE_DENY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "deny_id",
    "root_id",
    "actions",
    "reason",
    "source_label",
    "metadata",
})

TRUSTED_ROOT_REGISTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "registry_version",
    "trusted_roots",
    "scope_grants",
    "scope_denies",
    "registry_hash",
    "source_label",
    "created_by_task",
    "notes",
    "metadata",
})


class TrustedRootKind(str, Enum):
    """Declared root boundary kind; not permission, authority, or safety."""

    REPO_ROOT = "REPO_ROOT"
    WORKSPACE_ROOT = "WORKSPACE_ROOT"
    OPERATOR_APPROVED = "OPERATOR_APPROVED"
    AGENT_REPORTS = "AGENT_REPORTS"
    ARTIFACTS = "ARTIFACTS"
    UPLOADS = "UPLOADS"
    DENIED_ROOT = "DENIED_ROOT"
    UNKNOWN = "UNKNOWN"


class PathScopeAction(str, Enum):
    """Declared scope action vocabulary; not runtime permission."""

    READ = "READ"
    WRITE = "WRITE"
    CREATE = "CREATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    IMPORT = "IMPORT"
    LIST = "LIST"
    MEMORY_USE = "MEMORY_USE"
    PROMPT_CONTEXT_USE = "PROMPT_CONTEXT_USE"
    TOOL_INPUT_USE = "TOOL_INPUT_USE"
    UNKNOWN = "UNKNOWN"


class PathScopeReason(str, Enum):
    """Explanation metadata for a scope declaration; not enforcement."""

    REPO_CONTEXT = "REPO_CONTEXT"
    WORKSPACE_CONTEXT = "WORKSPACE_CONTEXT"
    OPERATOR_APPROVAL = "OPERATOR_APPROVAL"
    REPORT_OUTPUT = "REPORT_OUTPUT"
    ARTIFACT_OUTPUT = "ARTIFACT_OUTPUT"
    UPLOAD_BOUNDARY = "UPLOAD_BOUNDARY"
    DENIED_BY_DEFAULT = "DENIED_BY_DEFAULT"
    UNKNOWN = "UNKNOWN"


def _parse_root_kind(value: TrustedRootKind | str) -> TrustedRootKind:
    if isinstance(value, TrustedRootKind):
        return value
    if isinstance(value, str):
        try:
            return TrustedRootKind(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid root_kind: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="root_kind",
            ) from exc
    raise PathGovernanceError(
        "root_kind must be a string or TrustedRootKind",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="root_kind",
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


def _parse_scope_reason(value: PathScopeReason | str) -> PathScopeReason:
    if isinstance(value, PathScopeReason):
        return value
    if isinstance(value, str):
        try:
            return PathScopeReason(value)
        except ValueError as exc:
            raise PathGovernanceError(
                f"invalid reason: {value!r}",
                code=PathGovernanceErrorCode.INVALID_ENUM,
                field="reason",
            ) from exc
    raise PathGovernanceError(
        "reason must be a string or PathScopeReason",
        code=PathGovernanceErrorCode.INVALID_ENUM,
        field="reason",
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


def _freeze_actions(
    actions: Sequence[PathScopeAction | str] | None,
    *,
    field_name: str,
) -> tuple[PathScopeAction, ...]:
    raw = () if actions is None else actions
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise PathGovernanceValidationError(
            f"{field_name} must be a sequence of PathScopeAction values",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field=field_name,
        )
    parsed = tuple(_parse_scope_action(item) for item in raw)
    return tuple(sorted(parsed, key=lambda item: item.value))


def _freeze_non_empty_actions(
    actions: Sequence[PathScopeAction | str],
    *,
    field_name: str,
) -> tuple[PathScopeAction, ...]:
    parsed = _freeze_actions(actions, field_name=field_name)
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


def compute_root_id(
    *,
    root_kind: TrustedRootKind,
    path_identity: PathIdentity,
    allowed_actions: tuple[PathScopeAction, ...],
    denied_actions: tuple[PathScopeAction, ...],
    reason: PathScopeReason,
    registry_version: str = TRUSTED_ROOT_REGISTRY_VERSION,
) -> str:
    """Compute deterministic trusted root identifier without filesystem access."""
    return stable_hash({
        "allowed_actions": [item.value for item in allowed_actions],
        "denied_actions": [item.value for item in denied_actions],
        "path_identity": path_identity.to_canonical_dict(),
        "path_identity_hash": path_identity.identity_hash,
        "reason": reason.value,
        "registry_version": registry_version,
        "root_kind": root_kind.value,
    })


def compute_grant_id(
    *,
    root_id: str,
    actions: tuple[PathScopeAction, ...],
    reason: PathScopeReason,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic scope grant identifier without granting authority."""
    return stable_hash({
        "actions": [item.value for item in actions],
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "reason": reason.value,
        "root_id": root_id,
        "source_label": source_label.value,
    })


def compute_deny_id(
    *,
    root_id: str,
    actions: tuple[PathScopeAction, ...],
    reason: PathScopeReason,
    source_label: ProjectionSourceLabel,
    metadata: Mapping[str, Any],
) -> str:
    """Compute deterministic scope deny identifier without blocking runtime."""
    return stable_hash({
        "actions": [item.value for item in actions],
        "metadata": dict(sorted(metadata.items(), key=lambda item: item[0])),
        "reason": reason.value,
        "root_id": root_id,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class TrustedRoot:
    """Declared trusted root boundary; it grants no permission or safety."""

    path_identity: PathIdentity
    root_kind: TrustedRootKind = TrustedRootKind.UNKNOWN
    display_name: str | None = None
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    trust_label: SourceTrustLabel = SourceTrustLabel.UNKNOWN
    allowed_actions: tuple[PathScopeAction, ...] = field(default_factory=tuple)
    denied_actions: tuple[PathScopeAction, ...] = field(default_factory=tuple)
    reason: PathScopeReason = PathScopeReason.UNKNOWN
    root_id: str = ""
    registry_version: str = TRUSTED_ROOT_REGISTRY_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path_identity = _build_path_identity(self.path_identity)
        root_kind = _parse_root_kind(self.root_kind)
        display_name = _optional_string(self.display_name, field_name="display_name")
        source_label = _parse_source_label(self.source_label)
        trust_label = _parse_trust_label(self.trust_label)
        allowed_actions = _freeze_actions(
            self.allowed_actions,
            field_name="allowed_actions",
        )
        denied_actions = _freeze_actions(
            self.denied_actions,
            field_name="denied_actions",
        )
        reason = _parse_scope_reason(self.reason)
        if self.registry_version != TRUSTED_ROOT_REGISTRY_VERSION:
            raise PathGovernanceValidationError(
                "registry_version must be trusted_root_registry.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="registry_version",
            )
        metadata = _freeze_metadata(self.metadata)
        root_id = compute_root_id(
            root_kind=root_kind,
            path_identity=path_identity,
            allowed_actions=allowed_actions,
            denied_actions=denied_actions,
            reason=reason,
            registry_version=self.registry_version,
        )
        if self.root_id not in ("", root_id):
            raise PathGovernanceValidationError(
                "root_id does not match trusted root content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="root_id",
            )
        object.__setattr__(self, "path_identity", path_identity)
        object.__setattr__(self, "root_kind", root_kind)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "trust_label", trust_label)
        object.__setattr__(self, "allowed_actions", allowed_actions)
        object.__setattr__(self, "denied_actions", denied_actions)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "root_id", root_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "allowed_actions": [item.value for item in self.allowed_actions],
            "denied_actions": [item.value for item in self.denied_actions],
            "display_name": self.display_name,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "path_identity": self.path_identity.to_canonical_dict(),
            "reason": self.reason.value,
            "registry_version": self.registry_version,
            "root_id": self.root_id,
            "root_kind": self.root_kind.value,
            "source_label": self.source_label.value,
            "trust_label": self.trust_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TrustedRoot:
        validate_known_fields(data, TRUSTED_ROOT_KNOWN_FIELDS, label="trusted_root")
        return cls(
            path_identity=data["path_identity"],
            root_kind=data.get("root_kind", TrustedRootKind.UNKNOWN),
            display_name=data.get("display_name"),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            trust_label=data.get("trust_label", SourceTrustLabel.UNKNOWN),
            allowed_actions=data.get("allowed_actions", ()),
            denied_actions=data.get("denied_actions", ()),
            reason=data.get("reason", PathScopeReason.UNKNOWN),
            root_id=data.get("root_id", ""),
            registry_version=data.get("registry_version", TRUSTED_ROOT_REGISTRY_VERSION),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathScopeGrant:
    """Declared grantable scope; it does not grant runtime authority."""

    root_id: str
    actions: tuple[PathScopeAction, ...]
    reason: PathScopeReason = PathScopeReason.UNKNOWN
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    grant_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        root_id = _required_string(self.root_id, field_name="root_id")
        actions = _freeze_non_empty_actions(self.actions, field_name="actions")
        reason = _parse_scope_reason(self.reason)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        grant_id = compute_grant_id(
            root_id=root_id,
            actions=actions,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.grant_id not in ("", grant_id):
            raise PathGovernanceValidationError(
                "grant_id does not match grant content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="grant_id",
            )
        object.__setattr__(self, "root_id", root_id)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "grant_id", grant_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "actions": [item.value for item in self.actions],
            "grant_id": self.grant_id,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "reason": self.reason.value,
            "root_id": self.root_id,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathScopeGrant:
        validate_known_fields(data, PATH_SCOPE_GRANT_KNOWN_FIELDS, label="path_scope_grant")
        return cls(
            root_id=data["root_id"],
            actions=data["actions"],
            reason=data.get("reason", PathScopeReason.UNKNOWN),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            grant_id=data.get("grant_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class PathScopeDeny:
    """Declared denied scope; it does not enforce runtime blocking."""

    root_id: str
    actions: tuple[PathScopeAction, ...]
    reason: PathScopeReason = PathScopeReason.UNKNOWN
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    deny_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        root_id = _required_string(self.root_id, field_name="root_id")
        actions = _freeze_non_empty_actions(self.actions, field_name="actions")
        reason = _parse_scope_reason(self.reason)
        source_label = _parse_source_label(self.source_label)
        metadata = _freeze_metadata(self.metadata)
        deny_id = compute_deny_id(
            root_id=root_id,
            actions=actions,
            reason=reason,
            source_label=source_label,
            metadata=metadata,
        )
        if self.deny_id not in ("", deny_id):
            raise PathGovernanceValidationError(
                "deny_id does not match deny content",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="deny_id",
            )
        object.__setattr__(self, "root_id", root_id)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "deny_id", deny_id)
        object.__setattr__(self, "metadata", metadata)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "actions": [item.value for item in self.actions],
            "deny_id": self.deny_id,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "reason": self.reason.value,
            "root_id": self.root_id,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PathScopeDeny:
        validate_known_fields(data, PATH_SCOPE_DENY_KNOWN_FIELDS, label="path_scope_deny")
        return cls(
            root_id=data["root_id"],
            actions=data["actions"],
            reason=data.get("reason", PathScopeReason.UNKNOWN),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            deny_id=data.get("deny_id", ""),
            metadata=data.get("metadata", {}),
        )


def compute_registry_hash(
    *,
    registry_version: str,
    trusted_roots: Sequence[TrustedRoot],
    scope_grants: Sequence[PathScopeGrant],
    scope_denies: Sequence[PathScopeDeny],
    created_by_task: str,
) -> str:
    """Compute deterministic order-insensitive registry hash."""
    return stable_hash({
        "created_by_task": created_by_task,
        "registry_version": registry_version,
        "scope_denies": [
            item.to_canonical_dict()
            for item in sorted(scope_denies, key=lambda deny: deny.deny_id)
        ],
        "scope_grants": [
            item.to_canonical_dict()
            for item in sorted(scope_grants, key=lambda grant: grant.grant_id)
        ],
        "trusted_roots": [
            item.to_canonical_dict()
            for item in sorted(trusted_roots, key=lambda root: root.root_id)
        ],
    })


@dataclass(frozen=True)
class TrustedRootRegistry:
    """Stable trusted root declaration registry; not a resolver or sandbox."""

    trusted_roots: tuple[TrustedRoot, ...] = field(default_factory=tuple)
    scope_grants: tuple[PathScopeGrant, ...] = field(default_factory=tuple)
    scope_denies: tuple[PathScopeDeny, ...] = field(default_factory=tuple)
    registry_hash: str = ""
    registry_version: str = TRUSTED_ROOT_REGISTRY_VERSION
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE
    created_by_task: str = TRUSTED_ROOT_REGISTRY_TASK_ID
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.registry_version != TRUSTED_ROOT_REGISTRY_VERSION:
            raise PathGovernanceValidationError(
                "registry_version must be trusted_root_registry.v1",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="registry_version",
            )
        if self.created_by_task != TRUSTED_ROOT_REGISTRY_TASK_ID:
            raise PathGovernanceValidationError(
                "created_by_task must be P1.7.4",
                code=PathGovernanceErrorCode.INVALID_VERSION,
                field="created_by_task",
            )
        trusted_roots = tuple(self.trusted_roots)
        if not all(isinstance(item, TrustedRoot) for item in trusted_roots):
            raise PathGovernanceValidationError(
                "trusted_roots must be TrustedRoot objects",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="trusted_roots",
            )
        scope_grants = tuple(self.scope_grants)
        if not all(isinstance(item, PathScopeGrant) for item in scope_grants):
            raise PathGovernanceValidationError(
                "scope_grants must be PathScopeGrant objects",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="scope_grants",
            )
        scope_denies = tuple(self.scope_denies)
        if not all(isinstance(item, PathScopeDeny) for item in scope_denies):
            raise PathGovernanceValidationError(
                "scope_denies must be PathScopeDeny objects",
                code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                field="scope_denies",
            )
        root_ids = {item.root_id for item in trusted_roots}
        for grant in scope_grants:
            if grant.root_id not in root_ids:
                raise PathGovernanceValidationError(
                    "scope_grants must reference a trusted root in this registry",
                    code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                    field="scope_grants",
                )
        for deny in scope_denies:
            if deny.root_id not in root_ids:
                raise PathGovernanceValidationError(
                    "scope_denies must reference a trusted root in this registry",
                    code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
                    field="scope_denies",
                )
        source_label = _parse_source_label(self.source_label)
        notes = _freeze_notes(self.notes)
        metadata = _freeze_metadata(self.metadata)
        registry_hash = compute_registry_hash(
            registry_version=self.registry_version,
            trusted_roots=trusted_roots,
            scope_grants=scope_grants,
            scope_denies=scope_denies,
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
            "trusted_roots",
            tuple(sorted(trusted_roots, key=lambda item: item.root_id)),
        )
        object.__setattr__(
            self,
            "scope_grants",
            tuple(sorted(scope_grants, key=lambda item: item.grant_id)),
        )
        object.__setattr__(
            self,
            "scope_denies",
            tuple(sorted(scope_denies, key=lambda item: item.deny_id)),
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "registry_hash", registry_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "created_by_task": self.created_by_task,
            "metadata": dict(sorted(self.metadata.items(), key=lambda item: item[0])),
            "notes": list(self.notes),
            "registry_hash": self.registry_hash,
            "registry_version": self.registry_version,
            "scope_denies": [item.to_canonical_dict() for item in self.scope_denies],
            "scope_grants": [item.to_canonical_dict() for item in self.scope_grants],
            "source_label": self.source_label.value,
            "trusted_roots": [item.to_canonical_dict() for item in self.trusted_roots],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TrustedRootRegistry:
        validate_known_fields(
            data,
            TRUSTED_ROOT_REGISTRY_KNOWN_FIELDS,
            label="trusted_root_registry",
        )
        return cls(
            trusted_roots=tuple(
                item if isinstance(item, TrustedRoot) else TrustedRoot.from_dict(item)
                for item in data.get("trusted_roots", ())
            ),
            scope_grants=tuple(
                item if isinstance(item, PathScopeGrant)
                else PathScopeGrant.from_dict(item)
                for item in data.get("scope_grants", ())
            ),
            scope_denies=tuple(
                item if isinstance(item, PathScopeDeny) else PathScopeDeny.from_dict(item)
                for item in data.get("scope_denies", ())
            ),
            registry_hash=data.get("registry_hash", ""),
            registry_version=data.get(
                "registry_version",
                TRUSTED_ROOT_REGISTRY_VERSION,
            ),
            source_label=data.get("source_label", ProjectionSourceLabel.LIVE),
            created_by_task=data.get(
                "created_by_task",
                TRUSTED_ROOT_REGISTRY_TASK_ID,
            ),
            notes=data.get("notes", ()),
            metadata=data.get("metadata", {}),
        )


def _build_trusted_root(value: TrustedRoot | Mapping[str, Any]) -> TrustedRoot:
    if isinstance(value, TrustedRoot):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "trusted_roots entries must be TrustedRoot objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="trusted_roots",
        )
    return TrustedRoot.from_dict(value)


def _build_scope_grant(value: PathScopeGrant | Mapping[str, Any]) -> PathScopeGrant:
    if isinstance(value, PathScopeGrant):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "scope_grants entries must be PathScopeGrant objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="scope_grants",
        )
    return PathScopeGrant.from_dict(value)


def _build_scope_deny(value: PathScopeDeny | Mapping[str, Any]) -> PathScopeDeny:
    if isinstance(value, PathScopeDeny):
        return value
    if not isinstance(value, MappingABC):
        raise PathGovernanceValidationError(
            "scope_denies entries must be PathScopeDeny objects or mappings",
            code=PathGovernanceErrorCode.SERIALIZATION_ERROR,
            field="scope_denies",
        )
    return PathScopeDeny.from_dict(value)


def build_trusted_root_registry(
    trusted_roots: Sequence[TrustedRoot | Mapping[str, Any]] | None = None,
    scope_grants: Sequence[PathScopeGrant | Mapping[str, Any]] | None = None,
    scope_denies: Sequence[PathScopeDeny | Mapping[str, Any]] | None = None,
    source_label: ProjectionSourceLabel = ProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> TrustedRootRegistry:
    """Build deterministic trusted root registry without resolving authority."""
    root_tuple = tuple(
        _build_trusted_root(item) for item in (() if trusted_roots is None else trusted_roots)
    )
    grant_tuple = tuple(
        _build_scope_grant(item) for item in (() if scope_grants is None else scope_grants)
    )
    deny_tuple = tuple(
        _build_scope_deny(item) for item in (() if scope_denies is None else scope_denies)
    )
    return TrustedRootRegistry(
        trusted_roots=root_tuple,
        scope_grants=grant_tuple,
        scope_denies=deny_tuple,
        source_label=source_label,
        notes=(
            "P1.7.4 registry declares trusted root and scope state only.",
            "Trusted roots and scope declarations are not permissions, "
            "runtime authority, sandbox policy, escape detection, or enforcement.",
        ),
        metadata=metadata,
    )
