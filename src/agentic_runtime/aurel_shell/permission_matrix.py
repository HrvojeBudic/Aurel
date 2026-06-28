"""AurelShell permission meaning matrix contracts (P2.0-D / P2.0.19).

The matrix is a semantic affordance map. It describes what a surface action
means for an operator and agent, but it does not authorize, execute, grant
permission, or replace Custos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)
from .surface_registry import (
    AurelSurfaceKind,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)

AUREL_PERMISSION_MATRIX_CONTRACT_VERSION = "aurel_permission_matrix_contract.v1"
AUREL_PERMISSION_ENTRY_VERSION = "aurel_permission_entry.v1"
AUREL_PERMISSION_MATRIX_SNAPSHOT_VERSION = "aurel_permission_matrix_snapshot.v1"


class SurfacePermissionMeaning(str, Enum):
    VIEW_ALLOWED = "VIEW_ALLOWED"
    INSPECT_ALLOWED = "INSPECT_ALLOWED"
    PROPOSE_ALLOWED = "PROPOSE_ALLOWED"
    REQUEST_APPROVAL_ALLOWED = "REQUEST_APPROVAL_ALLOWED"
    OPERATOR_ONLY = "OPERATOR_ONLY"
    SYSTEM_ONLY = "SYSTEM_ONLY"
    AGENT_FORBIDDEN = "AGENT_FORBIDDEN"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class SurfacePermissionBoundary(str, Enum):
    CONTRACT_ONLY = "contract_only"
    DOES_NOT_AUTHORIZE = "does_not_authorize"
    DOES_NOT_EXECUTE = "does_not_execute"
    DOES_NOT_REPLACE_CUSTOS = "does_not_replace_custos"
    DOES_NOT_GRANT_PERMISSION = "does_not_grant_permission"


_PERMISSION_NON_GOALS: tuple[str, ...] = (
    "no_custos_enforcement",
    "no_runtime_permission_checks",
    "no_auth_middleware",
    "no_execution_grants",
    "no_root_grants",
)


@dataclass(frozen=True)
class SurfacePermissionMatrixContract(_CanonicalMixin):
    """P2.0.19 contract: permission meanings without enforcement."""

    schema_version: str
    permission_matrix_exists: bool
    permission_matrix_is_contract_only: bool
    permission_matrix_does_not_authorize: bool
    permission_matrix_does_not_execute: bool
    permission_matrix_does_not_replace_custos: bool
    permission_matrix_does_not_grant_permission: bool
    truth_label: str
    boundaries: tuple[SurfacePermissionBoundary, ...]
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfacePermissionEntry(_CanonicalMixin):
    """Single surface/action permission meaning entry."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    action_class: str
    permission_meaning: SurfacePermissionMeaning
    operator_visible_label: str
    agent_allowed: bool
    operator_required: bool
    system_only: bool
    requires_approval: bool
    is_contract_only: bool
    authorizes_action: bool
    executes_action: bool
    replaces_custos: bool
    grants_permission: bool
    non_goals: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class SurfacePermissionMatrixSnapshot(_CanonicalMixin):
    """Snapshot of permission meanings for canonical registry surfaces."""

    schema_version: str
    contract: SurfacePermissionMatrixContract
    entries: tuple[SurfacePermissionEntry, ...]
    entry_count: int
    canonical_surface_ids: tuple[str, ...]
    registry_hash: str
    truth_label: str
    snapshot_hash: str


def build_surface_permission_matrix_contract() -> SurfacePermissionMatrixContract:
    payload = {
        "schema_version": AUREL_PERMISSION_MATRIX_CONTRACT_VERSION,
        "permission_matrix_exists": True,
        "permission_matrix_is_contract_only": True,
        "permission_matrix_does_not_authorize": True,
        "permission_matrix_does_not_execute": True,
        "permission_matrix_does_not_replace_custos": True,
        "permission_matrix_does_not_grant_permission": True,
        "truth_label": "PERMISSION_MATRIX_CONTRACT_ONLY",
        "boundaries": tuple(SurfacePermissionBoundary),
        "non_goals": _PERMISSION_NON_GOALS,
    }
    return SurfacePermissionMatrixContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def build_surface_permission_entry(
    *,
    surface_id: str,
    surface_kind: AurelSurfaceKind | str,
    action_class: str,
    permission_meaning: SurfacePermissionMeaning | str,
    operator_visible_label: str,
    agent_allowed: bool,
    operator_required: bool,
    system_only: bool,
    requires_approval: bool,
    non_goals: tuple[str, ...] = _PERMISSION_NON_GOALS,
) -> SurfacePermissionEntry:
    if isinstance(surface_kind, str):
        surface_kind = AurelSurfaceKind(surface_kind)
    if isinstance(permission_meaning, str):
        permission_meaning = SurfacePermissionMeaning(permission_meaning)
    payload = {
        "schema_version": AUREL_PERMISSION_ENTRY_VERSION,
        "surface_id": surface_id,
        "surface_kind": surface_kind,
        "action_class": action_class,
        "permission_meaning": permission_meaning,
        "operator_visible_label": operator_visible_label,
        "agent_allowed": agent_allowed,
        "operator_required": operator_required,
        "system_only": system_only,
        "requires_approval": requires_approval,
        "is_contract_only": True,
        "authorizes_action": False,
        "executes_action": False,
        "replaces_custos": False,
        "grants_permission": False,
        "non_goals": non_goals,
    }
    entry = SurfacePermissionEntry(**payload, entry_hash=_hash_payload(payload))
    assert_permission_entry_is_contract_only(entry)
    assert_permission_matrix_does_not_authorize(entry)
    assert_permission_matrix_does_not_execute(entry)
    assert_permission_matrix_does_not_replace_custos(entry)
    assert_permission_matrix_does_not_grant_permission(entry)
    return entry


def _entry_for_surface(
    surface_id: str,
    surface_kind: AurelSurfaceKind,
) -> SurfacePermissionEntry:
    if surface_kind is AurelSurfaceKind.SYSTEM:
        return build_surface_permission_entry(
            surface_id=surface_id,
            surface_kind=surface_kind,
            action_class="operator_root_control_contract",
            permission_meaning=SurfacePermissionMeaning.AGENT_FORBIDDEN,
            operator_visible_label="OPERATOR_ONLY / AGENT_FORBIDDEN",
            agent_allowed=False,
            operator_required=True,
            system_only=True,
            requires_approval=True,
            non_goals=_PERMISSION_NON_GOALS
            + ("no_system_agent_access", "no_root_authority_grant"),
        )
    if surface_kind is AurelSurfaceKind.SETTINGS:
        return build_surface_permission_entry(
            surface_id=surface_id,
            surface_kind=surface_kind,
            action_class="non_root_config_inspect",
            permission_meaning=SurfacePermissionMeaning.INSPECT_ALLOWED,
            operator_visible_label="Settings non-root config only",
            agent_allowed=True,
            operator_required=False,
            system_only=False,
            requires_approval=False,
            non_goals=_PERMISSION_NON_GOALS
            + ("no_root_config", "no_system_mutation"),
        )
    if surface_kind is AurelSurfaceKind.HUB:
        return build_surface_permission_entry(
            surface_id=surface_id,
            surface_kind=surface_kind,
            action_class="tool_entry_inspect",
            permission_meaning=SurfacePermissionMeaning.INSPECT_ALLOWED,
            operator_visible_label="HUB tool entry only",
            agent_allowed=True,
            operator_required=False,
            system_only=False,
            requires_approval=False,
            non_goals=_PERMISSION_NON_GOALS
            + ("no_tool_execution", "no_tool_permission_grant"),
        )
    if surface_kind is AurelSurfaceKind.IDE:
        return build_surface_permission_entry(
            surface_id=surface_id,
            surface_kind=surface_kind,
            action_class="codeops_inspect_or_propose",
            permission_meaning=SurfacePermissionMeaning.PROPOSE_ALLOWED,
            operator_visible_label="IDE proposal/read contract only",
            agent_allowed=True,
            operator_required=False,
            system_only=False,
            requires_approval=True,
            non_goals=_PERMISSION_NON_GOALS
            + ("no_runtime_authority", "no_validation_bypass"),
        )
    return build_surface_permission_entry(
        surface_id=surface_id,
        surface_kind=surface_kind,
        action_class="surface_view_or_inspect",
        permission_meaning=SurfacePermissionMeaning.VIEW_ALLOWED,
        operator_visible_label="View/inspect contract only",
        agent_allowed=True,
        operator_required=False,
        system_only=False,
        requires_approval=False,
    )


def build_default_surface_permission_matrix(
    registry: AurelSurfaceRegistry | None = None,
) -> SurfacePermissionMatrixSnapshot:
    if registry is None:
        registry = build_default_surface_registry()
    contract = build_surface_permission_matrix_contract()
    entries = tuple(
        _entry_for_surface(surface.surface_id, surface.surface_kind)
        for surface in registry.surfaces
    )
    payload = {
        "schema_version": AUREL_PERMISSION_MATRIX_SNAPSHOT_VERSION,
        "contract": contract,
        "entries": entries,
        "entry_count": len(entries),
        "canonical_surface_ids": registry.canonical_surface_ids,
        "registry_hash": registry.registry_hash,
        "truth_label": "PERMISSION_MATRIX_CONTRACT_ONLY",
    }
    snapshot = SurfacePermissionMatrixSnapshot(
        **payload,
        snapshot_hash=_hash_payload(payload),
    )
    assert_permission_matrix_references_canonical_surfaces(snapshot, registry)
    assert_system_is_operator_only_agent_forbidden(snapshot)
    assert_settings_is_non_root_config(snapshot)
    assert_hub_is_tool_entry_only(snapshot)
    assert_ide_is_not_runtime_authority(snapshot)
    return snapshot


def assert_permission_entry_is_contract_only(entry: SurfacePermissionEntry) -> None:
    if not entry.is_contract_only:
        _reject(
            "permission matrix entry must be contract-only",
            field="is_contract_only",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_permission_matrix_does_not_authorize(
    entry: SurfacePermissionEntry,
) -> None:
    if entry.authorizes_action:
        _reject(
            "permission matrix must not authorize actions",
            field="authorizes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_permission_matrix_does_not_execute(entry: SurfacePermissionEntry) -> None:
    if entry.executes_action:
        _reject(
            "permission matrix must not execute actions",
            field="executes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_permission_matrix_does_not_replace_custos(
    entry: SurfacePermissionEntry,
) -> None:
    if entry.replaces_custos:
        _reject(
            "permission matrix must not replace Custos",
            field="replaces_custos",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_permission_matrix_does_not_grant_permission(
    entry: SurfacePermissionEntry,
) -> None:
    if entry.grants_permission:
        _reject(
            "permission matrix must not grant permission",
            field="grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_permission_matrix_references_canonical_surfaces(
    snapshot: SurfacePermissionMatrixSnapshot,
    registry: AurelSurfaceRegistry,
) -> None:
    entry_ids = tuple(entry.surface_id for entry in snapshot.entries)
    if entry_ids != registry.canonical_surface_ids:
        _reject(
            "permission matrix must reference canonical registry surfaces",
            field="entries",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _entry_by_kind(
    snapshot: SurfacePermissionMatrixSnapshot,
    kind: AurelSurfaceKind,
) -> SurfacePermissionEntry:
    for entry in snapshot.entries:
        if entry.surface_kind is kind:
            return entry
    _reject(
        f"permission matrix missing {kind.value}",
        field="entries",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def assert_system_is_operator_only_agent_forbidden(
    snapshot: SurfacePermissionMatrixSnapshot,
) -> None:
    entry = _entry_by_kind(snapshot, AurelSurfaceKind.SYSTEM)
    if entry.agent_allowed or not entry.operator_required or not entry.system_only:
        _reject(
            "SYSTEM permission entry must be operator-only and agent-forbidden",
            field="system_entry",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if entry.permission_meaning not in {
        SurfacePermissionMeaning.OPERATOR_ONLY,
        SurfacePermissionMeaning.AGENT_FORBIDDEN,
    }:
        _reject(
            "SYSTEM permission meaning must be OPERATOR_ONLY or AGENT_FORBIDDEN",
            field="permission_meaning",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_settings_is_non_root_config(
    snapshot: SurfacePermissionMatrixSnapshot,
) -> None:
    entry = _entry_by_kind(snapshot, AurelSurfaceKind.SETTINGS)
    if "non_root_config" not in entry.action_class:
        _reject(
            "Settings permission entry must be non-root config only",
            field="action_class",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if entry.system_only or entry.grants_permission:
        _reject(
            "Settings permission entry must not grant root/system permission",
            field="settings_entry",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_hub_is_tool_entry_only(snapshot: SurfacePermissionMatrixSnapshot) -> None:
    entry = _entry_by_kind(snapshot, AurelSurfaceKind.HUB)
    if "tool_entry" not in entry.action_class or entry.executes_action:
        _reject(
            "HUB permission entry must be tool-entry-only",
            field="hub_entry",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_ide_is_not_runtime_authority(
    snapshot: SurfacePermissionMatrixSnapshot,
) -> None:
    entry = _entry_by_kind(snapshot, AurelSurfaceKind.IDE)
    if not any("runtime_authority" in non_goal for non_goal in entry.non_goals):
        _reject(
            "IDE permission entry must declare no runtime authority",
            field="non_goals",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
