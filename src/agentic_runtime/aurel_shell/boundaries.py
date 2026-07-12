"""AurelShell authority boundary contracts (P2.0-B / P2.0.11–P2.0.14).

Source-of-truth, SYSTEM no-agent-access, Settings vs SYSTEM, and HUB tool
entry boundaries. Contract-only — no runtime enforcement or tool execution.

Architectural law:
  - Surface access is not source-of-truth access.
  - SYSTEM is operator-only root; agents cannot access SYSTEM.
  - Settings is non-root configuration; Settings is not SYSTEM.
  - HUB tool entry is not tool execution.
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

AUREL_BOUNDARY_CONTRACT_VERSION = "aurel_boundary_contract.v1"


class BoundaryTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    BOUNDARY_CONTRACT_ONLY = "BOUNDARY_CONTRACT_ONLY"
    SOURCE_OF_TRUTH_BOUNDARY_ONLY = "SOURCE_OF_TRUTH_BOUNDARY_ONLY"
    OPERATOR_ONLY_CONTRACT = "OPERATOR_ONLY_CONTRACT"
    NON_ROOT_CONFIG_CONTRACT = "NON_ROOT_CONFIG_CONTRACT"
    TOOL_ENTRY_CONTRACT_ONLY = "TOOL_ENTRY_CONTRACT_ONLY"
    NOT_LIVE = "NOT_LIVE"
    UNAVAILABLE = "UNAVAILABLE"


class SurfaceTruthOwnerKind(str, Enum):
    """Backend/control-plane truth owner relation kinds."""

    AUREL_CORE_OPERATOR_CONTROL_PLANE = "aurel_core_operator_control_plane"
    AUREL_CORE_FLOW_TRACE_PROJECTIONS = "aurel_core_flow_trace_projections"
    BUSINESS_ENVIRONMENT_STATE = "business_environment_state"
    TOOL_CAPABILITY_REGISTRY_PROJECTION = "tool_capability_registry_projection"
    CODEOPS_REPO_VALIDATION = "codeops_repo_validation"
    OPERATOR_SYSTEM_ROOT_CONTROL_PLANE = "operator_system_root_control_plane"
    NON_ROOT_CONFIGURATION_STORE = "non_root_configuration_store"


_TRUTH_OWNER_MAP: dict[AurelSurfaceKind, SurfaceTruthOwnerKind] = {
    AurelSurfaceKind.AUREL_CRO: SurfaceTruthOwnerKind.AUREL_CORE_OPERATOR_CONTROL_PLANE,
    AurelSurfaceKind.HQ: SurfaceTruthOwnerKind.AUREL_CORE_FLOW_TRACE_PROJECTIONS,
    AurelSurfaceKind.CORP: SurfaceTruthOwnerKind.BUSINESS_ENVIRONMENT_STATE,
    AurelSurfaceKind.HUB: SurfaceTruthOwnerKind.TOOL_CAPABILITY_REGISTRY_PROJECTION,
    AurelSurfaceKind.IDE: SurfaceTruthOwnerKind.CODEOPS_REPO_VALIDATION,
    AurelSurfaceKind.SYSTEM: SurfaceTruthOwnerKind.OPERATOR_SYSTEM_ROOT_CONTROL_PLANE,
    AurelSurfaceKind.SETTINGS: SurfaceTruthOwnerKind.NON_ROOT_CONFIGURATION_STORE,
}

_PROJECTION_RELATIONS: dict[AurelSurfaceKind, str] = {
    AurelSurfaceKind.AUREL_CRO: "operator_state_projection",
    AurelSurfaceKind.HQ: "sovereign_operations_projection",
    AurelSurfaceKind.CORP: "business_environment_projection",
    AurelSurfaceKind.HUB: "tool_constellation_projection",
    AurelSurfaceKind.IDE: "codeops_engineering_projection",
    AurelSurfaceKind.SYSTEM: "operator_root_control_projection",
    AurelSurfaceKind.SETTINGS: "non_root_config_projection",
}

_READ_MODEL_RELATIONS: dict[AurelSurfaceKind, str] = {
    AurelSurfaceKind.AUREL_CRO: "cro_read_model",
    AurelSurfaceKind.HQ: "hq_read_model",
    AurelSurfaceKind.CORP: "corp_read_model",
    AurelSurfaceKind.HUB: "hub_read_model",
    AurelSurfaceKind.IDE: "ide_read_model",
    AurelSurfaceKind.SYSTEM: "system_read_model",
    AurelSurfaceKind.SETTINGS: "settings_read_model",
}


@dataclass(frozen=True)
class SurfaceSourceOfTruthBoundary(_CanonicalMixin):
    """P2.0.11 — surface does not own truth; truth owner is explicit."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    surface_owns_truth: bool
    truth_owner_kind: SurfaceTruthOwnerKind
    truth_owner_relation: str
    projection_relation: str
    read_model_relation: str
    truth_label: BoundaryTruthLabel
    unavailable_reason: str
    non_goals: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SystemAccessRule(_CanonicalMixin):
    """Access rule for SYSTEM surface."""

    agent_access_allowed: bool
    operator_only: bool
    root_boundary: bool
    default_route_target_allowed: bool


@dataclass(frozen=True)
class SystemNoAgentAccessBoundary(_CanonicalMixin):
    """P2.0.12 — SYSTEM is operator-only; agents forbidden."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    access_rule: SystemAccessRule
    runtime_enforcement_created: bool
    truth_label: BoundaryTruthLabel
    secondary_truth_labels: tuple[BoundaryTruthLabel, ...]
    unavailable_reason: str
    non_goals: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SettingsConfigScope(_CanonicalMixin):
    """Settings configuration scope — non-root only."""

    is_system: bool
    can_grant_root: bool
    can_modify_system_root: bool
    can_perform_system_actions: bool


@dataclass(frozen=True)
class SystemConfigScope(_CanonicalMixin):
    """SYSTEM configuration scope — operator-only root."""

    is_operator_only: bool
    is_root_boundary: bool


@dataclass(frozen=True)
class SettingsSystemConfigBoundary(_CanonicalMixin):
    """P2.0.13 — Settings is distinct from SYSTEM; non-root config only."""

    schema_version: str
    settings_scope: SettingsConfigScope
    system_scope: SystemConfigScope
    settings_is_system: bool
    settings_can_grant_root: bool
    settings_can_modify_system_root: bool
    settings_can_perform_system_actions: bool
    system_is_operator_only: bool
    system_root_boundary_preserved: bool
    truth_label: BoundaryTruthLabel
    secondary_truth_labels: tuple[BoundaryTruthLabel, ...]
    unavailable_reason: str
    non_goals: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class HubToolEntryContract(_CanonicalMixin):
    """HUB tool entry contract fields."""

    hub_can_list_tool_entries: bool
    hub_can_execute_tools: bool
    hub_can_grant_tool_permission: bool
    hub_entry_is_tool_call: bool
    tool_entry_truth_label: BoundaryTruthLabel


@dataclass(frozen=True)
class HubInternalToolEntryBoundary(_CanonicalMixin):
    """P2.0.14 — HUB may list tool entries; cannot execute or grant permission."""

    schema_version: str
    surface_id: str
    surface_kind: AurelSurfaceKind
    tool_entry: HubToolEntryContract
    truth_label: BoundaryTruthLabel
    secondary_truth_labels: tuple[BoundaryTruthLabel, ...]
    unavailable_reason: str
    non_goals: tuple[str, ...]
    boundary_hash: str


_SOT_NON_GOALS: tuple[str, ...] = (
    "no_source_of_truth_store_implementation",
    "no_runtime_state_ownership",
    "no_backend_state_mutation",
)

_SYSTEM_NON_GOALS: tuple[str, ...] = (
    "no_system_ui",
    "no_runtime_enforcement_engine",
    "no_permission_matrix",
    "no_root_action_execution",
)

_SETTINGS_NON_GOALS: tuple[str, ...] = (
    "no_settings_ui",
    "no_config_runtime",
    "no_root_action_execution",
    "no_system_mutation",
)

_HUB_NON_GOALS: tuple[str, ...] = (
    "no_tool_execution",
    "no_tool_permission_grants",
    "no_tool_gateway",
    "no_workflow_execution",
)


def _build_surface_source_of_truth_boundary(
    kind: AurelSurfaceKind,
    *,
    surface_id: str,
) -> SurfaceSourceOfTruthBoundary:
    owner_kind = _TRUTH_OWNER_MAP[kind]
    payload = {
        "schema_version": AUREL_BOUNDARY_CONTRACT_VERSION,
        "surface_id": surface_id,
        "surface_kind": kind,
        "surface_owns_truth": False,
        "truth_owner_kind": owner_kind,
        "truth_owner_relation": owner_kind.value,
        "projection_relation": _PROJECTION_RELATIONS[kind],
        "read_model_relation": _READ_MODEL_RELATIONS[kind],
        "truth_label": BoundaryTruthLabel.SOURCE_OF_TRUTH_BOUNDARY_ONLY,
        "unavailable_reason": "source_of_truth_boundary_contract_only",
        "non_goals": _SOT_NON_GOALS,
    }
    return SurfaceSourceOfTruthBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_surface_source_of_truth_boundaries(
    registry: AurelSurfaceRegistry | None = None,
) -> tuple[SurfaceSourceOfTruthBoundary, ...]:
    if registry is None:
        registry = build_default_surface_registry()
    return tuple(
        _build_surface_source_of_truth_boundary(
            surface.surface_kind,
            surface_id=surface.surface_id,
        )
        for surface in registry.surfaces
    )


def build_system_no_agent_access_boundary() -> SystemNoAgentAccessBoundary:
    access_rule = SystemAccessRule(
        agent_access_allowed=False,
        operator_only=True,
        root_boundary=True,
        default_route_target_allowed=False,
    )
    payload = {
        "schema_version": AUREL_BOUNDARY_CONTRACT_VERSION,
        "surface_id": "system",
        "surface_kind": AurelSurfaceKind.SYSTEM,
        "access_rule": access_rule,
        "runtime_enforcement_created": False,
        "truth_label": BoundaryTruthLabel.OPERATOR_ONLY_CONTRACT,
        "secondary_truth_labels": (BoundaryTruthLabel.BOUNDARY_CONTRACT_ONLY,),
        "unavailable_reason": "system_boundary_contract_only_no_runtime_enforcement",
        "non_goals": _SYSTEM_NON_GOALS,
    }
    return SystemNoAgentAccessBoundary(**payload, boundary_hash=_hash_payload(payload))


@dataclass(frozen=True)
class SystemReadModelProjection(_CanonicalMixin):
    """F8.2 — one operator-only System read projection (zero-write)."""

    projection_id: str
    read_path: str
    truth_owner_relation: str
    operator_only: bool
    zero_write: bool
    truth_label: BoundaryTruthLabel


def build_system_read_model_projections() -> tuple[SystemReadModelProjection, ...]:
    """SYSTEM surface read-model projections (governance state, operator-only)."""
    specs = (
        ("system_audit", "/read/system/audit"),
        ("system_usage", "/read/system/usage"),
    )
    out: list[SystemReadModelProjection] = []
    for projection_id, read_path in specs:
        out.append(SystemReadModelProjection(
            projection_id=projection_id,
            read_path=read_path,
            truth_owner_relation=_READ_MODEL_RELATIONS[AurelSurfaceKind.SYSTEM],
            operator_only=True,
            zero_write=True,
            truth_label=BoundaryTruthLabel.SOURCE_OF_TRUTH_BOUNDARY_ONLY,
        ))
    return tuple(out)


def build_settings_system_config_boundary() -> SettingsSystemConfigBoundary:
    settings_scope = SettingsConfigScope(
        is_system=False,
        can_grant_root=False,
        can_modify_system_root=False,
        can_perform_system_actions=False,
    )
    system_scope = SystemConfigScope(
        is_operator_only=True,
        is_root_boundary=True,
    )
    payload = {
        "schema_version": AUREL_BOUNDARY_CONTRACT_VERSION,
        "settings_scope": settings_scope,
        "system_scope": system_scope,
        "settings_is_system": False,
        "settings_can_grant_root": False,
        "settings_can_modify_system_root": False,
        "settings_can_perform_system_actions": False,
        "system_is_operator_only": True,
        "system_root_boundary_preserved": True,
        "truth_label": BoundaryTruthLabel.NON_ROOT_CONFIG_CONTRACT,
        "secondary_truth_labels": (BoundaryTruthLabel.BOUNDARY_CONTRACT_ONLY,),
        "unavailable_reason": "settings_system_boundary_contract_only",
        "non_goals": _SETTINGS_NON_GOALS,
    }
    return SettingsSystemConfigBoundary(**payload, boundary_hash=_hash_payload(payload))


def build_hub_internal_tool_entry_boundary() -> HubInternalToolEntryBoundary:
    tool_entry = HubToolEntryContract(
        hub_can_list_tool_entries=True,
        hub_can_execute_tools=False,
        hub_can_grant_tool_permission=False,
        hub_entry_is_tool_call=False,
        tool_entry_truth_label=BoundaryTruthLabel.TOOL_ENTRY_CONTRACT_ONLY,
    )
    payload = {
        "schema_version": AUREL_BOUNDARY_CONTRACT_VERSION,
        "surface_id": "hub",
        "surface_kind": AurelSurfaceKind.HUB,
        "tool_entry": tool_entry,
        "truth_label": BoundaryTruthLabel.TOOL_ENTRY_CONTRACT_ONLY,
        "secondary_truth_labels": (BoundaryTruthLabel.BOUNDARY_CONTRACT_ONLY,),
        "unavailable_reason": "hub_tool_entry_boundary_contract_only",
        "non_goals": _HUB_NON_GOALS,
    }
    return HubInternalToolEntryBoundary(**payload, boundary_hash=_hash_payload(payload))


def assert_surface_does_not_own_truth(
    boundary: SurfaceSourceOfTruthBoundary,
) -> None:
    if boundary.surface_owns_truth:
        _reject(
            f"surface {boundary.surface_id} must not own truth",
            field="surface_owns_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_system_has_no_agent_access(
    boundary: SystemNoAgentAccessBoundary,
) -> None:
    rule = boundary.access_rule
    if rule.agent_access_allowed:
        _reject(
            "SYSTEM must forbid agent access",
            field="access_rule.agent_access_allowed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not rule.operator_only:
        _reject(
            "SYSTEM must be operator-only",
            field="access_rule.operator_only",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_settings_is_not_system(
    boundary: SettingsSystemConfigBoundary,
) -> None:
    if boundary.settings_is_system:
        _reject(
            "Settings must not be SYSTEM",
            field="settings_is_system",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_settings_cannot_grant_root(
    boundary: SettingsSystemConfigBoundary,
) -> None:
    if boundary.settings_can_grant_root:
        _reject(
            "Settings must not grant root authority",
            field="settings_can_grant_root",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_hub_entry_is_not_tool_execution(
    boundary: HubInternalToolEntryBoundary,
) -> None:
    entry = boundary.tool_entry
    if entry.hub_can_execute_tools:
        _reject(
            "HUB must not execute tools",
            field="tool_entry.hub_can_execute_tools",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if entry.hub_entry_is_tool_call:
        _reject(
            "HUB entry must not be tool call",
            field="tool_entry.hub_entry_is_tool_call",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_hub_cannot_grant_tool_permission(
    boundary: HubInternalToolEntryBoundary,
) -> None:
    if boundary.tool_entry.hub_can_grant_tool_permission:
        _reject(
            "HUB must not grant tool permission",
            field="tool_entry.hub_can_grant_tool_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
