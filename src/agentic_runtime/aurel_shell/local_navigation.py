"""AurelShell per-surface local navigation foundation (P2.2-A / P2.2.0–P2.2.5).

Contract-only local navigation ownership, per-surface nav registries, nav item
contracts, visibility/availability states, and projection seed over the sealed
P2.1 topbar/surface registry foundation.

Architectural law:
  - Local navigation is surface-owned, not global topbar.
  - Nav registry is read model, not source of truth.
  - Nav item is semantic handle, not route execution or click handler.
  - Visibility is epistemic state, not permission.
  - Availability is contract scope, not LIVE.
  - Projection seed is not UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    SURFACE_KIND_DISPLAY_NAMES,
    AurelSurfaceKind,
    SURFACE_KIND_IDS,
)
from .topbar import (
    P2_1_SECTION_ID,
    SETTINGS_SURFACE_ID,
    SYSTEM_SURFACE_ID,
)
from .topbar_integration_tail import (
    P2_1_D_REPORT_FILENAME,
    P21P22ReadinessDecision,
    P21TopbarSealDecision,
    build_p2_1_topbar_exit_seal,
    build_p2_2_readiness_result,
)

P2_2_A_PACK_ID = "P2.2-A"
P2_2_SECTION_ID = "P2.2"
P2_2_SECTION_NAME = "Per-Surface Local Navigation"
P2_2_A_PACK_NAME = "Per-Surface Local Navigation Foundation"
P2_2_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.2.0",
    "P2.2.1",
    "P2.2.2",
    "P2.2.3",
    "P2.2.4",
    "P2.2.5",
)
P2_2_A_DEPENDENCY_PACKS: tuple[str, ...] = ("P2.1-D",)
P2_2_A_NEXT_PACK = "P2.2-B"
P2_2_A_REPORT_FILENAME = "P2_2_A_LOCAL_NAVIGATION_FOUNDATION.md"
P2_2_A_REPORT_PATH = f"agent/reports/{P2_2_A_REPORT_FILENAME}"
P2_2_A_RESULT_VERSION = "p2_2_a_local_navigation_foundation_result.v1"
P2_2_SECTION_INTAKE_VERSION = "p2_2_section_intake.v1"
P2_2_HANDOFF_GATE_VERSION = "p2_2_p2_1_handoff_gate.v1"
LOCAL_NAV_OWNERSHIP_VERSION = "local_navigation_ownership_contract.v1"
LOCAL_NAV_REGISTRY_VERSION = "per_surface_local_nav_registry.v1"
LOCAL_NAV_GROUP_VERSION = "local_nav_group_contract.v1"
LOCAL_NAV_ITEM_VERSION = "local_nav_item_contract.v1"
LOCAL_NAV_VISIBILITY_VERSION = "local_nav_visibility_availability_state.v1"
LOCAL_NAV_PROJECTION_VERSION = "local_nav_projection_seed.v1"

P2_1_CONTRACT_SCOPE_SEAL = P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE.value
P2_2_PLAN_READINESS = P21P22ReadinessDecision.READY_FOR_P2_2_PLAN.value

_EnumT = TypeVar("_EnumT", bound=Enum)

_INTAKE_NON_GOALS: tuple[str, ...] = (
    "no_ui",
    "no_nav_rendering",
    "no_route_runtime",
    "no_p2_3",
)
_OWNERSHIP_NON_GOALS: tuple[str, ...] = (
    "no_global_nav_sidebar",
    "no_topbar_route_execution",
    "no_ui_layout",
    "no_route_runtime",
)
_REGISTRY_NON_GOALS: tuple[str, ...] = (
    "no_frontend_nav_tree",
    "no_real_route_handlers",
    "no_local_state_persistence",
    "no_global_left_nav",
)
_ITEM_NON_GOALS: tuple[str, ...] = (
    "no_click_handler",
    "no_frontend_route",
    "no_command_palette_action",
    "no_tool_execution",
    "no_permission_grant",
)
_VISIBILITY_NON_GOALS: tuple[str, ...] = (
    "no_runtime_health_check",
    "no_auth_check",
    "no_live_nav_evaluation",
    "no_permission_grant",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_visual_nav",
    "no_local_nav_runtime",
    "no_route_execution",
    "no_p2_2_b_implementation",
    "no_p2_3_implementation",
)

_SURFACE_PRIMARY_LABELS: dict[str, str] = {
    "aurel_cro": "Overview",
    "hq": "Command Center",
    "corp": "Operations",
    "hub": "Tool Hub",
    "ide": "Workspace",
    "system": "System Console",
    "settings": "Configuration",
}


class P22TruthLabel(str, Enum):
    SECTION_INTAKE = "SECTION_INTAKE"
    HANDOFF_GATE = "HANDOFF_GATE"
    CONTRACT_SCOPE = "CONTRACT_SCOPE"
    NOT_UI = "NOT_UI"
    NOT_P2_3 = "NOT_P2_3"
    SURFACE_OWNED_LOCAL_NAV = "SURFACE_OWNED_LOCAL_NAV"
    NOT_GLOBAL_TOPBAR = "NOT_GLOBAL_TOPBAR"
    NOT_COMMAND_PALETTE = "NOT_COMMAND_PALETTE"
    NOT_FLOATING_WINDOW = "NOT_FLOATING_WINDOW"
    NOT_ROUTE_RUNTIME = "NOT_ROUTE_RUNTIME"
    LOCAL_NAV_REGISTRY_CONTRACT = "LOCAL_NAV_REGISTRY_CONTRACT"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NAV_ITEM_CONTRACT = "NAV_ITEM_CONTRACT"
    NOT_ACTION_EXECUTION = "NOT_ACTION_EXECUTION"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_PERMISSION = "NOT_PERMISSION"
    NOT_CLICK_HANDLER = "NOT_CLICK_HANDLER"
    VISIBILITY_CONTRACT = "VISIBILITY_CONTRACT"
    AVAILABILITY_CONTRACT = "AVAILABILITY_CONTRACT"
    NOT_LIVE = "NOT_LIVE"
    NOT_AUTH_CHECK = "NOT_AUTH_CHECK"
    PROJECTION_SEED = "PROJECTION_SEED"
    NOT_P2_2_B = "NOT_P2_2_B"


class LocalNavigationOwner(str, Enum):
    SURFACE = "SURFACE"


class LocalNavGroupKind(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TOOLS = "TOOLS"
    STATUS = "STATUS"
    SETTINGS = "SETTINGS"
    SOURCES = "SOURCES"
    PLACEHOLDER = "PLACEHOLDER"


class LocalNavItemKind(str, Enum):
    SECTION = "SECTION"
    PANEL = "PANEL"
    INSPECT = "INSPECT"
    SETTINGS_VIEW = "SETTINGS_VIEW"
    SOURCE_VIEW = "SOURCE_VIEW"
    STATUS_VIEW = "STATUS_VIEW"
    PLACEHOLDER = "PLACEHOLDER"


class LocalNavVisibilityState(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


class LocalNavAvailabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PROTECTED = "PROTECTED"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class P22SectionIntakeTruthBoundary(_CanonicalMixin):
    is_contract_scope: bool
    is_ui: bool
    starts_p2_2: bool
    starts_p2_2_b: bool
    starts_p2_3: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22SectionIntake(_CanonicalMixin):
    section_id: str
    section_name: str
    depends_on_section: str
    required_previous_seal: str
    required_previous_readiness: str
    previous_section_report_ref: str
    previous_section_seal_found: bool
    previous_section_readiness_found: bool
    starts_p2_2: bool
    starts_p2_2_b: bool
    starts_p2_3: bool
    truth_label: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    non_goals: tuple[str, ...]
    intake_hash: str


@dataclass(frozen=True)
class P22P21HandoffGate(_CanonicalMixin):
    schema_version: str
    pack_id: str
    depends_on_section: str
    required_previous_seal: str
    required_previous_readiness: str
    previous_section_report_ref: str
    previous_section_seal_found: bool
    previous_section_readiness_found: bool
    starts_p2_2: bool
    starts_p2_2_b: bool
    starts_p2_3: bool
    truth_label: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    non_goals: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class LocalNavigationOwnershipTruthBoundary(_CanonicalMixin):
    owned_by_surface: bool
    owned_by_global_topbar: bool
    owned_by_command_palette: bool
    owned_by_floating_window: bool
    owned_by_runtime_router: bool
    creates_global_left_nav: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavigationOwnershipContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    surface_display_name: str
    local_nav_owner: LocalNavigationOwner
    owned_by_surface: bool
    owned_by_global_topbar: bool
    owned_by_command_palette: bool
    owned_by_floating_window: bool
    owned_by_runtime_router: bool
    creates_global_left_nav: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class PerSurfaceLocalNavRegistryTruthBoundary(_CanonicalMixin):
    is_source_of_truth: bool
    creates_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavGroupContract(_CanonicalMixin):
    schema_version: str
    group_id: str
    surface_id: str
    label: str
    description: str
    group_kind: LocalNavGroupKind
    default_group: bool
    protected: bool
    unavailable: bool
    deferred: bool
    deferred_to_section: str
    deferred_to_pack: str
    unavailable_reason: str
    truth_label: str
    non_goals: tuple[str, ...]
    group_hash: str


@dataclass(frozen=True)
class PerSurfaceLocalNavRegistry(_CanonicalMixin):
    schema_version: str
    surface_id: str
    surface_display_name: str
    nav_registry_id: str
    nav_groups: tuple[LocalNavGroupContract, ...]
    default_local_nav_group: str
    protected_nav_groups: tuple[str, ...]
    unavailable_nav_groups: tuple[str, ...]
    deferred_nav_groups: tuple[str, ...]
    truth_label: str
    is_source_of_truth: bool
    creates_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    non_goals: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class LocalNavItemTruthBoundary(_CanonicalMixin):
    executes_action: bool
    executes_route: bool
    creates_click_handler: bool
    creates_keyboard_shortcut: bool
    grants_permission: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavItemContract(_CanonicalMixin):
    schema_version: str
    nav_item_id: str
    surface_id: str
    group_id: str
    label: str
    description: str
    nav_kind: LocalNavItemKind
    visibility: LocalNavVisibilityState
    availability: LocalNavAvailabilityState
    route_hint: str
    requires_operator: bool
    protected: bool
    deferred: bool
    deferred_to_section: str
    deferred_to_pack: str
    unavailable_reason: str
    executes_action: bool
    executes_route: bool
    creates_click_handler: bool
    creates_keyboard_shortcut: bool
    grants_permission: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    item_hash: str


@dataclass(frozen=True)
class LocalNavVisibilityAvailabilityTruthBoundary(_CanonicalMixin):
    visible_does_not_grant_permission: bool
    available_does_not_mean_live: bool
    is_live: bool
    permission_granted: bool
    runtime_checked: bool
    auth_checked: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavVisibilityAvailabilityState(_CanonicalMixin):
    schema_version: str
    nav_item_id: str
    surface_id: str
    visible: bool
    hidden: bool
    available: bool
    unavailable: bool
    protected: bool
    deferred: bool
    deferred_to_section: str
    deferred_to_pack: str
    reason: str
    truth_label: str
    is_live: bool
    permission_granted: bool
    runtime_checked: bool
    auth_checked: bool
    non_goals: tuple[str, ...]
    state_hash: str


@dataclass(frozen=True)
class LocalNavProjectionTruthBoundary(_CanonicalMixin):
    is_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    creates_route_runtime: bool
    executes_routes: bool
    creates_command_palette: bool
    creates_floating_windows: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    starts_p2_2_b: bool
    starts_p2_3: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22ASideEffectProof(_CanonicalMixin):
    """P2.2-A side-effect / no-authority proof. Every field is false."""

    ui_created: bool = False
    frontend_component_created: bool = False
    frontend_sidebar_created: bool = False
    global_left_nav_created: bool = False
    frontend_route_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    cli_live_product_created: bool = False
    tui_product_created: bool = False
    route_runtime_created: bool = False
    route_handler_created: bool = False
    click_handler_created: bool = False
    keyboard_shortcut_created: bool = False
    command_palette_created: bool = False
    floating_window_created: bool = False
    browser_tests_created: bool = False
    live_shell_created: bool = False
    api_server_created: bool = False
    http_route_created: bool = False
    event_bus_created: bool = False
    runtime_event_emitted: bool = False
    source_of_truth_created: bool = False
    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    roadmap_rewritten: bool = False
    registry_truth_mutated: bool = False
    surface_promoted: bool = False
    production_live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_2_b_started: bool = False
    p2_3_started: bool = False


@dataclass(frozen=True)
class LocalNavProjectionSeed(_CanonicalMixin):
    projection_id: str
    created_for_pack: str
    section_intake: P22SectionIntake
    handoff_gate: P22P21HandoffGate
    ownership_contracts: tuple[LocalNavigationOwnershipContract, ...]
    per_surface_nav_registries: tuple[PerSurfaceLocalNavRegistry, ...]
    nav_group_contracts: tuple[LocalNavGroupContract, ...]
    nav_item_contracts: tuple[LocalNavItemContract, ...]
    visibility_availability_states: tuple[LocalNavVisibilityAvailabilityState, ...]
    truth_boundary: LocalNavProjectionTruthBoundary
    side_effect_proof: P22ASideEffectProof
    next_pack: str
    is_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    creates_route_runtime: bool
    executes_routes: bool
    creates_command_palette: bool
    creates_floating_windows: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    starts_p2_2_b: bool
    starts_p2_3: bool
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P22ALocalNavigationFoundationResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    section_intake: P22SectionIntake
    handoff_gate: P22P21HandoffGate
    projection_seed: LocalNavProjectionSeed
    side_effect_proof: P22ASideEffectProof
    taxonomy_drift_detected: bool
    truth_labels: tuple[str, ...]
    next_pack: str
    result_hash: str


def _coerce_enum(enum_cls: type[_EnumT], value: _EnumT | str, field: str) -> _EnumT:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            try:
                return enum_cls[value]
            except KeyError:
                pass
    _reject(
        f"invalid {field}: {value!r}",
        field=field,
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def _require_reason(reason: str, *, field: str) -> None:
    if not reason:
        _reject(
            "unavailable or deferred state requires reason or target",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _require_deferred_target(section: str, pack: str, *, field: str) -> None:
    if not section or not pack:
        _reject(
            "deferred state requires deferred_to_section and deferred_to_pack",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _surface_kind_for_id(surface_id: str) -> AurelSurfaceKind:
    for kind, sid in SURFACE_KIND_IDS.items():
        if sid == surface_id:
            return kind
    _reject(
        f"unknown surface_id: {surface_id!r}",
        field="surface_id",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def _surface_display_name(surface_id: str) -> str:
    kind = _surface_kind_for_id(surface_id)
    return SURFACE_KIND_DISPLAY_NAMES[kind]


def _p2_1_d_handoff_evidence() -> tuple[bool, bool]:
    exit_seal = build_p2_1_topbar_exit_seal()
    readiness = build_p2_2_readiness_result()
    seal_found = (
        exit_seal.seal_decision == P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE
    )
    readiness_found = (
        readiness.p2_2_readiness_decision == P21P22ReadinessDecision.READY_FOR_P2_2_PLAN
    )
    return seal_found, readiness_found


def build_p2_2_section_intake(
    *,
    previous_section_seal_found: bool | None = None,
    previous_section_readiness_found: bool | None = None,
) -> P22SectionIntake:
    if previous_section_seal_found is None or previous_section_readiness_found is None:
        seal_found, readiness_found = _p2_1_d_handoff_evidence()
        if previous_section_seal_found is None:
            previous_section_seal_found = seal_found
        if previous_section_readiness_found is None:
            previous_section_readiness_found = readiness_found
    payload = {
        "section_id": P2_2_SECTION_ID,
        "section_name": P2_2_SECTION_NAME,
        "depends_on_section": P2_1_SECTION_ID,
        "required_previous_seal": P2_1_CONTRACT_SCOPE_SEAL,
        "required_previous_readiness": P2_2_PLAN_READINESS,
        "previous_section_report_ref": P2_1_D_REPORT_FILENAME,
        "previous_section_seal_found": previous_section_seal_found,
        "previous_section_readiness_found": previous_section_readiness_found,
        "starts_p2_2": True,
        "starts_p2_2_b": False,
        "starts_p2_3": False,
        "truth_label": P22TruthLabel.SECTION_INTAKE.value,
        "blockers": (),
        "warnings": (
            "P2.2-A starts contract work only; no UI or route runtime is created",
        ),
        "non_goals": _INTAKE_NON_GOALS,
    }
    intake = P22SectionIntake(**payload, intake_hash=_hash_payload(payload))
    assert_p2_1_contract_scope_sealed(intake)
    assert_p2_2_section_intake_readiness_is_plan_only(intake)
    return intake


def build_p2_1_handoff_gate(
    *,
    previous_section_seal_found: bool | None = None,
    previous_section_readiness_found: bool | None = None,
) -> P22P21HandoffGate:
    if previous_section_seal_found is None or previous_section_readiness_found is None:
        seal_found, readiness_found = _p2_1_d_handoff_evidence()
        if previous_section_seal_found is None:
            previous_section_seal_found = seal_found
        if previous_section_readiness_found is None:
            previous_section_readiness_found = readiness_found
    payload = {
        "schema_version": P2_2_HANDOFF_GATE_VERSION,
        "pack_id": P2_2_A_PACK_ID,
        "depends_on_section": P2_1_SECTION_ID,
        "required_previous_seal": P2_1_CONTRACT_SCOPE_SEAL,
        "required_previous_readiness": P2_2_PLAN_READINESS,
        "previous_section_report_ref": P2_1_D_REPORT_FILENAME,
        "previous_section_seal_found": previous_section_seal_found,
        "previous_section_readiness_found": previous_section_readiness_found,
        "starts_p2_2": True,
        "starts_p2_2_b": False,
        "starts_p2_3": False,
        "truth_label": P22TruthLabel.HANDOFF_GATE.value,
        "blockers": (),
        "warnings": (
            "READY_FOR_P2_2_PLAN was permission to plan P2.2, not proof local nav exists",
        ),
        "non_goals": _INTAKE_NON_GOALS,
    }
    gate = P22P21HandoffGate(**payload, gate_hash=_hash_payload(payload))
    assert_p2_2_a_depends_on_p2_1_d(gate)
    return gate


def build_local_navigation_ownership_contract(
    surface_id: str,
) -> LocalNavigationOwnershipContract:
    display_name = _surface_display_name(surface_id)
    payload = {
        "schema_version": LOCAL_NAV_OWNERSHIP_VERSION,
        "surface_id": surface_id,
        "surface_display_name": display_name,
        "local_nav_owner": LocalNavigationOwner.SURFACE,
        "owned_by_surface": True,
        "owned_by_global_topbar": False,
        "owned_by_command_palette": False,
        "owned_by_floating_window": False,
        "owned_by_runtime_router": False,
        "creates_global_left_nav": False,
        "truth_label": P22TruthLabel.SURFACE_OWNED_LOCAL_NAV.value,
        "non_goals": _OWNERSHIP_NON_GOALS,
    }
    contract = LocalNavigationOwnershipContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_local_nav_is_surface_owned(contract)
    assert_no_global_left_nav_created(contract)
    return contract


def build_local_navigation_ownership_contracts() -> tuple[LocalNavigationOwnershipContract, ...]:
    return tuple(
        build_local_navigation_ownership_contract(surface_id)
        for surface_id in CANONICAL_SURFACE_ORDER
    )


def build_local_nav_group_contract(
    *,
    surface_id: str,
    group_id: str,
    label: str,
    description: str,
    group_kind: LocalNavGroupKind | str,
    default_group: bool = False,
    protected: bool = False,
    unavailable: bool = False,
    deferred: bool = False,
    deferred_to_section: str = "",
    deferred_to_pack: str = "",
    unavailable_reason: str = "",
) -> LocalNavGroupContract:
    kind = _coerce_enum(LocalNavGroupKind, group_kind, "group_kind")
    if unavailable:
        _require_reason(unavailable_reason, field="unavailable_reason")
    if deferred:
        _require_deferred_target(
            deferred_to_section,
            deferred_to_pack,
            field="deferred_to_section",
        )
    payload = {
        "schema_version": LOCAL_NAV_GROUP_VERSION,
        "group_id": group_id,
        "surface_id": surface_id,
        "label": label,
        "description": description,
        "group_kind": kind,
        "default_group": default_group,
        "protected": protected,
        "unavailable": unavailable,
        "deferred": deferred,
        "deferred_to_section": deferred_to_section,
        "deferred_to_pack": deferred_to_pack,
        "unavailable_reason": unavailable_reason,
        "truth_label": P22TruthLabel.LOCAL_NAV_REGISTRY_CONTRACT.value,
        "non_goals": _REGISTRY_NON_GOALS,
    }
    return LocalNavGroupContract(**payload, group_hash=_hash_payload(payload))


def _default_groups_for_surface(surface_id: str) -> tuple[LocalNavGroupContract, ...]:
    primary_id = f"{surface_id}_primary"
    groups: list[LocalNavGroupContract] = [
        build_local_nav_group_contract(
            surface_id=surface_id,
            group_id=primary_id,
            label=_SURFACE_PRIMARY_LABELS.get(surface_id, "Primary"),
            description=f"Primary local navigation group for {surface_id}",
            group_kind=LocalNavGroupKind.PRIMARY,
            default_group=True,
        ),
    ]
    if surface_id == SYSTEM_SURFACE_ID:
        groups.append(
            build_local_nav_group_contract(
                surface_id=surface_id,
                group_id=f"{surface_id}_protected",
                label="Protected",
                description="Protected operator-only local nav group",
                group_kind=LocalNavGroupKind.STATUS,
                protected=True,
            )
        )
    if surface_id == SETTINGS_SURFACE_ID:
        groups.append(
            build_local_nav_group_contract(
                surface_id=surface_id,
                group_id=f"{surface_id}_settings",
                label="Settings Views",
                description="Non-root configuration views",
                group_kind=LocalNavGroupKind.SETTINGS,
            )
        )
    groups.append(
        build_local_nav_group_contract(
            surface_id=surface_id,
            group_id=f"{surface_id}_deferred_tools",
            label="Advanced Tools",
            description="Deferred local nav tools",
            group_kind=LocalNavGroupKind.TOOLS,
            deferred=True,
            deferred_to_section="P2.2",
            deferred_to_pack="P2.2-B",
        )
    )
    groups.append(
        build_local_nav_group_contract(
            surface_id=surface_id,
            group_id=f"{surface_id}_unavailable_placeholder",
            label="Unavailable Placeholder",
            description="Contract-only unavailable group",
            group_kind=LocalNavGroupKind.PLACEHOLDER,
            unavailable=True,
            unavailable_reason=(
                f"UNAVAILABLE_LOCAL_NAV: advanced {surface_id} local nav not implemented in P2.2-A"
            ),
        )
    )
    return tuple(groups)


def build_local_nav_group_contracts() -> tuple[LocalNavGroupContract, ...]:
    groups: list[LocalNavGroupContract] = []
    for surface_id in CANONICAL_SURFACE_ORDER:
        groups.extend(_default_groups_for_surface(surface_id))
    return tuple(groups)


def build_per_surface_local_nav_registry(
    surface_id: str,
    *,
    nav_groups: tuple[LocalNavGroupContract, ...] | None = None,
) -> PerSurfaceLocalNavRegistry:
    if nav_groups is None:
        nav_groups = _default_groups_for_surface(surface_id)
    default_group = next(
        (group.group_id for group in nav_groups if group.default_group),
        nav_groups[0].group_id if nav_groups else "",
    )
    protected = tuple(group.group_id for group in nav_groups if group.protected)
    unavailable = tuple(group.group_id for group in nav_groups if group.unavailable)
    deferred = tuple(group.group_id for group in nav_groups if group.deferred)
    display_name = _surface_display_name(surface_id)
    payload = {
        "schema_version": LOCAL_NAV_REGISTRY_VERSION,
        "surface_id": surface_id,
        "surface_display_name": display_name,
        "nav_registry_id": f"local_nav_registry_{surface_id}",
        "nav_groups": nav_groups,
        "default_local_nav_group": default_group,
        "protected_nav_groups": protected,
        "unavailable_nav_groups": unavailable,
        "deferred_nav_groups": deferred,
        "truth_label": P22TruthLabel.LOCAL_NAV_REGISTRY_CONTRACT.value,
        "is_source_of_truth": False,
        "creates_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "executes_routes": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "non_goals": _REGISTRY_NON_GOALS,
    }
    registry = PerSurfaceLocalNavRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_local_nav_registry_is_not_source_of_truth(registry)
    return registry


def build_per_surface_local_nav_registries() -> tuple[PerSurfaceLocalNavRegistry, ...]:
    return tuple(
        build_per_surface_local_nav_registry(surface_id)
        for surface_id in CANONICAL_SURFACE_ORDER
    )


def build_local_nav_item_contract(
    *,
    surface_id: str,
    group_id: str,
    nav_item_id: str,
    label: str,
    description: str,
    nav_kind: LocalNavItemKind | str,
    visibility: LocalNavVisibilityState | str = LocalNavVisibilityState.VISIBLE,
    availability: LocalNavAvailabilityState | str = LocalNavAvailabilityState.AVAILABLE,
    route_hint: str = "",
    requires_operator: bool = False,
    protected: bool = False,
    deferred: bool = False,
    deferred_to_section: str = "",
    deferred_to_pack: str = "",
    unavailable_reason: str = "",
) -> LocalNavItemContract:
    kind = _coerce_enum(LocalNavItemKind, nav_kind, "nav_kind")
    vis = _coerce_enum(LocalNavVisibilityState, visibility, "visibility")
    avail = _coerce_enum(LocalNavAvailabilityState, availability, "availability")
    if availability == LocalNavAvailabilityState.UNAVAILABLE or (
        isinstance(availability, str) and availability == "UNAVAILABLE"
    ):
        _require_reason(unavailable_reason, field="unavailable_reason")
    if deferred:
        _require_deferred_target(
            deferred_to_section,
            deferred_to_pack,
            field="deferred_to_section",
        )
    if not route_hint:
        route_hint = f"/{surface_id}/{nav_item_id.replace(f'{surface_id}_', '')}"
    payload = {
        "schema_version": LOCAL_NAV_ITEM_VERSION,
        "nav_item_id": nav_item_id,
        "surface_id": surface_id,
        "group_id": group_id,
        "label": label,
        "description": description,
        "nav_kind": kind,
        "visibility": vis,
        "availability": avail,
        "route_hint": route_hint,
        "requires_operator": requires_operator,
        "protected": protected,
        "deferred": deferred,
        "deferred_to_section": deferred_to_section,
        "deferred_to_pack": deferred_to_pack,
        "unavailable_reason": unavailable_reason,
        "executes_action": False,
        "executes_route": False,
        "creates_click_handler": False,
        "creates_keyboard_shortcut": False,
        "grants_permission": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": P22TruthLabel.NAV_ITEM_CONTRACT.value,
        "non_goals": _ITEM_NON_GOALS,
    }
    item = LocalNavItemContract(**payload, item_hash=_hash_payload(payload))
    assert_nav_item_is_not_execution(item)
    assert_nav_item_does_not_create_click_handler(item)
    return item


def _default_items_for_surface(
    surface_id: str,
    groups: tuple[LocalNavGroupContract, ...],
) -> tuple[LocalNavItemContract, ...]:
    group_by_id = {group.group_id: group for group in groups}
    primary_id = next(
        group.group_id for group in groups if group.default_group
    )
    items: list[LocalNavItemContract] = [
        build_local_nav_item_contract(
            surface_id=surface_id,
            group_id=primary_id,
            nav_item_id=f"{surface_id}_overview",
            label=_SURFACE_PRIMARY_LABELS.get(surface_id, "Overview"),
            description=f"Primary local nav item for {surface_id}",
            nav_kind=LocalNavItemKind.SECTION,
        ),
    ]
    if surface_id == SYSTEM_SURFACE_ID:
        protected_group = f"{surface_id}_protected"
        if protected_group in group_by_id:
            items.append(
                build_local_nav_item_contract(
                    surface_id=surface_id,
                    group_id=protected_group,
                    nav_item_id=f"{surface_id}_operator_console",
                    label="Operator Console",
                    description="Protected operator-only local nav item",
                    nav_kind=LocalNavItemKind.STATUS_VIEW,
                    requires_operator=True,
                    protected=True,
                    availability=LocalNavAvailabilityState.PROTECTED,
                )
            )
    if surface_id == SETTINGS_SURFACE_ID:
        settings_group = f"{surface_id}_settings"
        if settings_group in group_by_id:
            items.append(
                build_local_nav_item_contract(
                    surface_id=surface_id,
                    group_id=settings_group,
                    nav_item_id=f"{surface_id}_preferences",
                    label="Preferences",
                    description="Non-root configuration view",
                    nav_kind=LocalNavItemKind.SETTINGS_VIEW,
                )
            )
    deferred_group = f"{surface_id}_deferred_tools"
    if deferred_group in group_by_id:
        items.append(
            build_local_nav_item_contract(
                surface_id=surface_id,
                group_id=deferred_group,
                nav_item_id=f"{surface_id}_advanced_tools",
                label="Advanced Tools",
                description="Deferred local nav item",
                nav_kind=LocalNavItemKind.PLACEHOLDER,
                deferred=True,
                deferred_to_section="P2.2",
                deferred_to_pack="P2.2-B",
                availability=LocalNavAvailabilityState.DEFERRED,
            )
        )
    unavailable_group = f"{surface_id}_unavailable_placeholder"
    if unavailable_group in group_by_id:
        items.append(
            build_local_nav_item_contract(
                surface_id=surface_id,
                group_id=unavailable_group,
                nav_item_id=f"{surface_id}_unavailable_item",
                label="Unavailable Item",
                description="Contract-only unavailable nav item",
                nav_kind=LocalNavItemKind.PLACEHOLDER,
                availability=LocalNavAvailabilityState.UNAVAILABLE,
                unavailable_reason=(
                    f"UNAVAILABLE_LOCAL_NAV: {surface_id} advanced item not implemented in P2.2-A"
                ),
            )
        )
    return tuple(items)


def build_local_nav_item_contracts() -> tuple[LocalNavItemContract, ...]:
    items: list[LocalNavItemContract] = []
    for surface_id in CANONICAL_SURFACE_ORDER:
        groups = _default_groups_for_surface(surface_id)
        items.extend(_default_items_for_surface(surface_id, groups))
    return tuple(items)


def build_local_nav_visibility_availability_state(
    item: LocalNavItemContract,
) -> LocalNavVisibilityAvailabilityState:
    visible = item.visibility == LocalNavVisibilityState.VISIBLE
    hidden = item.visibility == LocalNavVisibilityState.HIDDEN
    available = item.availability == LocalNavAvailabilityState.AVAILABLE
    unavailable = item.availability == LocalNavAvailabilityState.UNAVAILABLE
    protected = item.availability == LocalNavAvailabilityState.PROTECTED or item.protected
    deferred = item.availability == LocalNavAvailabilityState.DEFERRED or item.deferred
    reason = item.unavailable_reason
    if unavailable and not reason:
        _require_reason(reason, field="reason")
    if deferred:
        _require_deferred_target(
            item.deferred_to_section,
            item.deferred_to_pack,
            field="deferred_to_section",
        )
    payload = {
        "schema_version": LOCAL_NAV_VISIBILITY_VERSION,
        "nav_item_id": item.nav_item_id,
        "surface_id": item.surface_id,
        "visible": visible,
        "hidden": hidden,
        "available": available,
        "unavailable": unavailable,
        "protected": protected,
        "deferred": deferred,
        "deferred_to_section": item.deferred_to_section,
        "deferred_to_pack": item.deferred_to_pack,
        "reason": reason,
        "truth_label": P22TruthLabel.VISIBILITY_CONTRACT.value,
        "is_live": False,
        "permission_granted": False,
        "runtime_checked": False,
        "auth_checked": False,
        "non_goals": _VISIBILITY_NON_GOALS,
    }
    state = LocalNavVisibilityAvailabilityState(
        **payload,
        state_hash=_hash_payload(payload),
    )
    assert_visibility_is_not_permission(state)
    assert_availability_is_not_live(state)
    return state


def build_local_nav_visibility_availability_states(
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> tuple[LocalNavVisibilityAvailabilityState, ...]:
    if items is None:
        items = build_local_nav_item_contracts()
    return tuple(build_local_nav_visibility_availability_state(item) for item in items)


def build_p2_2_a_side_effect_proof() -> P22ASideEffectProof:
    return P22ASideEffectProof()


def build_local_nav_projection_seed(
    *,
    section_intake: P22SectionIntake | None = None,
    handoff_gate: P22P21HandoffGate | None = None,
    ownership_contracts: tuple[LocalNavigationOwnershipContract, ...] | None = None,
    per_surface_nav_registries: tuple[PerSurfaceLocalNavRegistry, ...] | None = None,
    nav_group_contracts: tuple[LocalNavGroupContract, ...] | None = None,
    nav_item_contracts: tuple[LocalNavItemContract, ...] | None = None,
    visibility_availability_states: tuple[LocalNavVisibilityAvailabilityState, ...] | None = None,
) -> LocalNavProjectionSeed:
    if section_intake is None:
        section_intake = build_p2_2_section_intake()
    if handoff_gate is None:
        handoff_gate = build_p2_1_handoff_gate()
    if ownership_contracts is None:
        ownership_contracts = build_local_navigation_ownership_contracts()
    if per_surface_nav_registries is None:
        per_surface_nav_registries = build_per_surface_local_nav_registries()
    if nav_group_contracts is None:
        nav_group_contracts = build_local_nav_group_contracts()
    if nav_item_contracts is None:
        nav_item_contracts = build_local_nav_item_contracts()
    if visibility_availability_states is None:
        visibility_availability_states = build_local_nav_visibility_availability_states(
            nav_item_contracts
        )
    side_effects = build_p2_2_a_side_effect_proof()
    truth_boundary_payload = {
        "is_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "creates_route_runtime": False,
        "executes_routes": False,
        "creates_command_palette": False,
        "creates_floating_windows": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "starts_p2_2_b": False,
        "starts_p2_3": False,
        "truth_labels": (
            P22TruthLabel.PROJECTION_SEED.value,
            P22TruthLabel.READ_MODEL_ONLY.value,
            P22TruthLabel.NOT_UI.value,
            P22TruthLabel.NOT_ROUTE_RUNTIME.value,
            P22TruthLabel.NOT_P2_2_B.value,
            P22TruthLabel.NOT_P2_3.value,
        ),
    }
    truth_boundary = LocalNavProjectionTruthBoundary(
        **truth_boundary_payload,
        boundary_hash=_hash_payload(truth_boundary_payload),
    )
    payload = {
        "projection_id": "local_nav_projection_seed_p2_2_a",
        "created_for_pack": P2_2_A_PACK_ID,
        "section_intake": section_intake,
        "handoff_gate": handoff_gate,
        "ownership_contracts": ownership_contracts,
        "per_surface_nav_registries": per_surface_nav_registries,
        "nav_group_contracts": nav_group_contracts,
        "nav_item_contracts": nav_item_contracts,
        "visibility_availability_states": visibility_availability_states,
        "truth_boundary": truth_boundary,
        "side_effect_proof": side_effects,
        "next_pack": P2_2_A_NEXT_PACK,
        "is_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "creates_route_runtime": False,
        "executes_routes": False,
        "creates_command_palette": False,
        "creates_floating_windows": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "starts_p2_2_b": False,
        "starts_p2_3": False,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    seed = LocalNavProjectionSeed(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_seed_is_not_ui(seed)
    assert_projection_seed_does_not_execute_routes(seed)
    assert_p2_2_a_does_not_start_p2_2_b(seed)
    assert_p2_2_a_does_not_start_p2_3(seed)
    return seed


def build_p2_2_a_local_navigation_foundation_result() -> P22ALocalNavigationFoundationResult:
    section_intake = build_p2_2_section_intake()
    handoff_gate = build_p2_1_handoff_gate()
    projection_seed = build_local_nav_projection_seed(
        section_intake=section_intake,
        handoff_gate=handoff_gate,
    )
    side_effects = build_p2_2_a_side_effect_proof()
    drift_detected, _drift_details = detect_surface_taxonomy_drift()
    payload = {
        "schema_version": P2_2_A_RESULT_VERSION,
        "pack_id": P2_2_A_PACK_ID,
        "section_id": P2_2_SECTION_ID,
        "section_name": P2_2_SECTION_NAME,
        "covered_checkpoints": P2_2_A_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_2_A_DEPENDENCY_PACKS,
        "section_intake": section_intake,
        "handoff_gate": handoff_gate,
        "projection_seed": projection_seed,
        "side_effect_proof": side_effects,
        "taxonomy_drift_detected": drift_detected,
        "truth_labels": (
            P22TruthLabel.CONTRACT_SCOPE.value,
            P22TruthLabel.READ_MODEL_ONLY.value,
            P22TruthLabel.NOT_UI.value,
            P22TruthLabel.NOT_LIVE.value,
            P22TruthLabel.NOT_P2_2_B.value,
            P22TruthLabel.NOT_P2_3.value,
        ),
        "next_pack": P2_2_A_NEXT_PACK,
    }
    return P22ALocalNavigationFoundationResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_p2_2_a_result(
    result: P22ALocalNavigationFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_2_a_local_navigation_foundation_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_2_a_depends_on_p2_1_d(gate: P22P21HandoffGate) -> None:
    if gate.required_previous_seal != P2_1_CONTRACT_SCOPE_SEAL:
        _reject(
            "P2.2-A requires P2.1 contract-scope seal",
            field="required_previous_seal",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if gate.required_previous_readiness != P2_2_PLAN_READINESS:
        _reject(
            "P2.2-A requires READY_FOR_P2_2_PLAN",
            field="required_previous_readiness",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not gate.previous_section_seal_found or not gate.previous_section_readiness_found:
        _reject(
            "P2.1-D seal/readiness evidence must be found",
            field="previous_section_seal_found",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_1_contract_scope_sealed(intake: P22SectionIntake) -> None:
    if intake.required_previous_seal != P2_1_CONTRACT_SCOPE_SEAL:
        _reject(
            "section intake must require SEALED_FOR_P2_1_CONTRACT_SCOPE",
            field="required_previous_seal",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not intake.previous_section_seal_found:
        _reject(
            "P2.1 contract-scope seal must be found",
            field="previous_section_seal_found",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_section_intake_readiness_is_plan_only(intake: P22SectionIntake) -> None:
    if intake.required_previous_readiness != P2_2_PLAN_READINESS:
        _reject(
            "section intake must require READY_FOR_P2_2_PLAN",
            field="required_previous_readiness",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_local_nav_is_surface_owned(contract: LocalNavigationOwnershipContract) -> None:
    if not contract.owned_by_surface:
        _reject(
            "local navigation must be owned by surface",
            field="owned_by_surface",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        contract.owned_by_global_topbar
        or contract.owned_by_command_palette
        or contract.owned_by_floating_window
        or contract.owned_by_runtime_router
    ):
        _reject(
            "local navigation must not be owned by topbar/command palette/floating window/router",
            field="owned_by_global_topbar",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_global_left_nav_created(contract: LocalNavigationOwnershipContract) -> None:
    if contract.creates_global_left_nav:
        _reject(
            "local navigation ownership must not create global left nav",
            field="creates_global_left_nav",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_local_nav_registry_is_not_source_of_truth(
    registry: PerSurfaceLocalNavRegistry,
) -> None:
    if registry.is_source_of_truth:
        _reject(
            "local nav registry must not be source of truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if (
        registry.creates_ui
        or registry.creates_sidebar
        or registry.creates_global_left_nav
        or registry.executes_routes
        or registry.mutates_runtime
    ):
        _reject(
            "local nav registry must not create UI/routes or mutate runtime",
            field="creates_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_nav_item_is_not_execution(item: LocalNavItemContract) -> None:
    if (
        item.executes_action
        or item.executes_route
        or item.grants_permission
        or item.mutates_runtime
    ):
        _reject(
            "nav item must not execute action/route or grant permission",
            field="executes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_nav_item_does_not_create_click_handler(item: LocalNavItemContract) -> None:
    if item.creates_click_handler or item.creates_keyboard_shortcut:
        _reject(
            "nav item must not create click handler or keyboard shortcut",
            field="creates_click_handler",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_visibility_is_not_permission(state: LocalNavVisibilityAvailabilityState) -> None:
    if state.permission_granted or state.auth_checked:
        _reject(
            "visibility must not grant permission or perform auth check",
            field="permission_granted",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_availability_is_not_live(state: LocalNavVisibilityAvailabilityState) -> None:
    if state.is_live or state.runtime_checked:
        _reject(
            "availability must not mean LIVE or runtime health check",
            field="is_live",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_unavailable_state_has_reason(state: LocalNavVisibilityAvailabilityState) -> None:
    if state.unavailable and not state.reason:
        _reject(
            "unavailable state requires reason",
            field="reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_deferred_state_has_target(state: LocalNavVisibilityAvailabilityState) -> None:
    if state.deferred and (not state.deferred_to_section or not state.deferred_to_pack):
        _reject(
            "deferred state requires target section/pack",
            field="deferred_to_section",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_projection_seed_is_not_ui(seed: LocalNavProjectionSeed) -> None:
    if seed.is_ui or seed.creates_sidebar or seed.creates_global_left_nav:
        _reject(
            "projection seed must not be UI or create sidebar/global left nav",
            field="is_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_seed_does_not_execute_routes(seed: LocalNavProjectionSeed) -> None:
    if seed.creates_route_runtime or seed.executes_routes:
        _reject(
            "projection seed must not create route runtime or execute routes",
            field="creates_route_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_a_does_not_start_p2_2_b(seed: LocalNavProjectionSeed) -> None:
    if seed.starts_p2_2_b:
        _reject(
            "P2.2-A must not start P2.2-B",
            field="starts_p2_2_b",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_a_does_not_start_p2_3(seed: LocalNavProjectionSeed) -> None:
    if seed.starts_p2_3 or seed.creates_floating_windows or seed.creates_command_palette:
        _reject(
            "P2.2-A must not start P2.3 or create command palette/floating windows",
            field="starts_p2_3",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def validate_local_nav_item_kind(kind: LocalNavItemKind | str) -> LocalNavItemKind:
    return _coerce_enum(LocalNavItemKind, kind, "nav_kind")


def validate_local_nav_group_kind(kind: LocalNavGroupKind | str) -> LocalNavGroupKind:
    return _coerce_enum(LocalNavGroupKind, kind, "group_kind")
