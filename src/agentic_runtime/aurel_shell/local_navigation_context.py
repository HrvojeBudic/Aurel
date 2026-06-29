"""AurelShell local navigation context / surface profiles (P2.2-C / P2.2.11–P2.2.15).

Contract-only context carryover, surface-specific profiles, state restoration,
degraded/unavailable profiles, and context projection over P2.2-A/P2.2-B foundation.

Architectural law:
  - Context carryover is read-model continuity, not memory persistence.
  - Surface profile is local nav shape, not new surface taxonomy.
  - State restoration is read-model restoration, not route execution.
  - Degraded profile is honest contract state, not runtime failure claim.
  - Context projection is not UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .local_navigation import (
    P2_2_A_PACK_ID,
    P2_2_A_REPORT_FILENAME,
    LocalNavAvailabilityState,
    LocalNavItemContract,
    LocalNavProjectionSeed,
    PerSurfaceLocalNavRegistry,
    build_local_nav_item_contracts,
    build_local_nav_projection_seed,
    build_per_surface_local_nav_registries,
)
from .local_navigation_hierarchy import (
    P2_2_B_PACK_ID,
    P2_2_B_REPORT_FILENAME,
    LocalNavHierarchyProjectionResult,
    LocalNavSelectionSource,
    LocalNavSelectionState,
    build_local_nav_hierarchy_projection_result,
    build_local_nav_selection_states,
)
from .surface_registry import CANONICAL_SURFACE_ORDER
from .topbar import SYSTEM_SURFACE_ID

AUDIT_REPAIR_001_PACK_ID = "AUDIT-REPAIR-001"
AUDIT_REPAIR_001_REPORT_FILENAME = (
    "AUDIT_REPAIR_001_TEST_PORTABILITY_P2_2_B_CANON_SYNC.md"
)

P2_2_C_PACK_ID = "P2.2-C"
P2_2_C_PACK_NAME = "Local Navigation Context / Surface-Specific Profiles"
P2_2_C_SECTION_ID = "P2.2"
P2_2_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.2.11",
    "P2.2.12",
    "P2.2.13",
    "P2.2.14",
    "P2.2.15",
)
P2_2_C_DEPENDENCY_PACKS: tuple[str, ...] = (
    AUDIT_REPAIR_001_PACK_ID,
    P2_2_B_PACK_ID,
    P2_2_A_PACK_ID,
)
P2_2_C_NEXT_PACK = "P2.2-D"
P2_2_C_REPORT_FILENAME = "P2_2_C_LOCAL_NAVIGATION_CONTEXT.md"
P2_2_C_REPORT_PATH = f"agent/reports/{P2_2_C_REPORT_FILENAME}"
P2_2_C_RESULT_VERSION = "p2_2_c_local_navigation_context_result.v1"
LOCAL_NAV_CONTEXT_CARRYOVER_VERSION = "local_nav_context_carryover_contract.v1"
LOCAL_NAV_SURFACE_PROFILE_VERSION = "surface_local_nav_profile_contract.v1"
LOCAL_NAV_RESTORATION_VERSION = "local_nav_state_restoration_contract.v1"
LOCAL_NAV_DEGRADED_PROFILE_VERSION = "local_nav_degraded_profile_contract.v1"
LOCAL_NAV_CONTEXT_PROJECTION_VERSION = "local_nav_context_projection.v1"
LOCAL_NAV_CONTEXT_PROJECTION_ID = "local_nav_context_projection_p2_2_c"

_CARRYOVER_NON_GOALS: tuple[str, ...] = (
    "no_persistent_memory",
    "no_runtime_state_mutation",
    "no_route_execution",
    "no_local_storage",
    "no_browser_storage",
)
_PROFILE_NON_GOALS: tuple[str, ...] = (
    "no_new_surfaces",
    "no_forum_archivium_activation",
    "no_ui_layout",
    "no_runtime_router",
)
_RESTORATION_NON_GOALS: tuple[str, ...] = (
    "no_url_mutation",
    "no_browser_state",
    "no_runtime_state",
    "no_persistence",
)
_DEGRADED_NON_GOALS: tuple[str, ...] = (
    "no_runtime_monitoring",
    "no_notification_engine",
    "no_repair_automation",
    "no_failure_diagnosis_engine",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_visual_nav",
    "no_local_storage",
    "no_route_execution",
    "no_p2_2_d_implementation",
    "no_p2_3_implementation",
)

_EnumT = TypeVar("_EnumT", bound=Enum)

_SURFACE_PROFILE_KINDS: dict[str, str] = {
    "aurel_cro": "CRO_SURFACE",
    "hq": "COMMAND_SURFACE",
    "corp": "BUSINESS_SURFACE",
    "hub": "HUB_SURFACE",
    "ide": "ENGINEERING_SURFACE",
    "system": "SYSTEM_SURFACE",
    "settings": "CONFIG_SURFACE",
}


class P22CTruthLabel(str, Enum):
    CONTEXT_CARRYOVER_CONTRACT = "CONTEXT_CARRYOVER_CONTRACT"
    READ_MODEL_CONTINUITY_ONLY = "READ_MODEL_CONTINUITY_ONLY"
    NOT_MEMORY_PERSISTENCE = "NOT_MEMORY_PERSISTENCE"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    SURFACE_LOCAL_NAV_PROFILE_CONTRACT = "SURFACE_LOCAL_NAV_PROFILE_CONTRACT"
    OFFICIAL_SURFACES_ONLY = "OFFICIAL_SURFACES_ONLY"
    NOT_SURFACE_TAXONOMY = "NOT_SURFACE_TAXONOMY"
    NOT_UI = "NOT_UI"
    STATE_RESTORATION_CONTRACT = "STATE_RESTORATION_CONTRACT"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    DEGRADED_PROFILE_CONTRACT = "DEGRADED_PROFILE_CONTRACT"
    UNAVAILABLE_PROFILE_CONTRACT = "UNAVAILABLE_PROFILE_CONTRACT"
    NOT_RUNTIME_FAILURE_CLAIM = "NOT_RUNTIME_FAILURE_CLAIM"
    NOT_REPAIR_AUTOMATION = "NOT_REPAIR_AUTOMATION"
    CONTEXT_PROJECTION = "CONTEXT_PROJECTION"
    NOT_PERSISTENCE = "NOT_PERSISTENCE"
    NOT_P2_2_D = "NOT_P2_2_D"
    NOT_P2_3 = "NOT_P2_3"


class SurfaceLocalNavProfileKind(str, Enum):
    COMMAND_SURFACE = "COMMAND_SURFACE"
    BUSINESS_SURFACE = "BUSINESS_SURFACE"
    HUB_SURFACE = "HUB_SURFACE"
    ENGINEERING_SURFACE = "ENGINEERING_SURFACE"
    SYSTEM_SURFACE = "SYSTEM_SURFACE"
    CONFIG_SURFACE = "CONFIG_SURFACE"
    CRO_SURFACE = "CRO_SURFACE"


class LocalNavRestoreSource(str, Enum):
    DEFAULT_PROFILE = "DEFAULT_PROFILE"
    PREVIOUS_READ_MODEL = "PREVIOUS_READ_MODEL"
    OPERATOR_INTENT_CONTRACT = "OPERATOR_INTENT_CONTRACT"
    UNAVAILABLE_FALLBACK = "UNAVAILABLE_FALLBACK"
    PROTECTED_FALLBACK = "PROTECTED_FALLBACK"


@dataclass(frozen=True)
class LocalNavContextCarryoverTruthBoundary(_CanonicalMixin):
    writes_memory: bool
    writes_trace: bool
    mutates_runtime: bool
    uses_local_storage: bool
    uses_browser_storage: bool
    executes_route: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavContextCarryoverContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    previous_projection_ref: str
    current_projection_ref: str
    selected_nav_item_ref: str
    selected_group_ref: str
    carryover_reason: str
    carryover_available: bool
    carryover_unavailable_reason: str
    writes_memory: bool
    writes_trace: bool
    mutates_runtime: bool
    uses_local_storage: bool
    uses_browser_storage: bool
    executes_route: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceLocalNavProfileTruthBoundary(_CanonicalMixin):
    creates_surface_taxonomy: bool
    activates_future_surface: bool
    creates_ui: bool
    creates_sidebar: bool
    executes_routes: bool
    mutates_runtime: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SurfaceLocalNavProfileContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    surface_display_name: str
    profile_id: str
    profile_kind: SurfaceLocalNavProfileKind
    default_group_id: str
    primary_nav_items: tuple[str, ...]
    protected_nav_items: tuple[str, ...]
    unavailable_nav_items: tuple[str, ...]
    deferred_nav_items: tuple[str, ...]
    profile_truth_label: str
    creates_surface_taxonomy: bool
    activates_future_surface: bool
    creates_ui: bool
    creates_sidebar: bool
    executes_routes: bool
    mutates_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class LocalNavStateRestorationTruthBoundary(_CanonicalMixin):
    route_executed: bool
    action_executed: bool
    url_mutated: bool
    runtime_mutated: bool
    memory_written: bool
    trace_written: bool
    local_storage_written: bool
    browser_storage_written: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavStateRestorationContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    restore_source: LocalNavRestoreSource
    restored_group_id: str
    restored_nav_item_id: str
    restoration_valid: bool
    invalid_reason: str
    route_executed: bool
    action_executed: bool
    url_mutated: bool
    runtime_mutated: bool
    memory_written: bool
    trace_written: bool
    local_storage_written: bool
    browser_storage_written: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class LocalNavDegradedProfileTruthBoundary(_CanonicalMixin):
    is_runtime_failure: bool
    runtime_failure_proven: bool
    starts_repair_automation: bool
    emits_notification: bool
    mutates_runtime: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavDegradedProfileContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    profile_id: str
    degraded: bool
    unavailable: bool
    degradation_reason: str
    unavailable_reason: str
    operator_message: str
    fallback_profile_id: str
    requires_repair: bool
    is_runtime_failure: bool
    runtime_failure_proven: bool
    starts_repair_automation: bool
    emits_notification: bool
    mutates_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class LocalNavContextProjectionTruthBoundary(_CanonicalMixin):
    is_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    creates_route_runtime: bool
    executes_routes: bool
    creates_click_handlers: bool
    creates_keyboard_shortcuts: bool
    creates_command_palette: bool
    creates_floating_windows: bool
    writes_memory: bool
    writes_trace: bool
    mutates_runtime: bool
    uses_local_storage: bool
    uses_browser_storage: bool
    creates_surface_taxonomy: bool
    starts_p2_2_d: bool
    starts_p2_3: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22CSideEffectProof(_CanonicalMixin):
    """P2.2-C side-effect / no-authority proof. Every field is false."""

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
    local_storage_written: bool = False
    browser_storage_written: bool = False
    surface_taxonomy_created: bool = False
    future_surface_activated: bool = False
    roadmap_rewritten: bool = False
    registry_truth_mutated: bool = False
    surface_promoted: bool = False
    production_live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_2_d_started: bool = False
    p2_3_started: bool = False


@dataclass(frozen=True)
class LocalNavContextProjectionResult(_CanonicalMixin):
    projection_id: str
    created_for_pack: str
    foundation_ref: str
    hierarchy_ref: str
    context_carryover_contracts: tuple[LocalNavContextCarryoverContract, ...]
    surface_profile_contracts: tuple[SurfaceLocalNavProfileContract, ...]
    state_restoration_contracts: tuple[LocalNavStateRestorationContract, ...]
    degraded_profile_contracts: tuple[LocalNavDegradedProfileContract, ...]
    truth_boundary: LocalNavContextProjectionTruthBoundary
    side_effect_proof: P22CSideEffectProof
    next_pack: str
    is_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    creates_route_runtime: bool
    executes_routes: bool
    creates_click_handlers: bool
    creates_keyboard_shortcuts: bool
    creates_command_palette: bool
    creates_floating_windows: bool
    writes_memory: bool
    writes_trace: bool
    mutates_runtime: bool
    uses_local_storage: bool
    uses_browser_storage: bool
    creates_surface_taxonomy: bool
    starts_p2_2_d: bool
    starts_p2_3: bool
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P22CLocalNavigationContextResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    pack_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    audit_repair_ref: str
    foundation_ref: str
    hierarchy_ref: str
    context_projection: LocalNavContextProjectionResult
    side_effect_proof: P22CSideEffectProof
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
            f"{field} is required",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _items_for_surface(
    surface_id: str,
    items: tuple[LocalNavItemContract, ...],
) -> tuple[LocalNavItemContract, ...]:
    return tuple(item for item in items if item.surface_id == surface_id)


def _selection_source_to_restore_source(
    source: LocalNavSelectionSource,
) -> LocalNavRestoreSource:
    mapping = {
        LocalNavSelectionSource.DEFAULT: LocalNavRestoreSource.DEFAULT_PROFILE,
        LocalNavSelectionSource.RESTORED_READ_MODEL: (
            LocalNavRestoreSource.PREVIOUS_READ_MODEL
        ),
        LocalNavSelectionSource.OPERATOR_INTENT_CONTRACT: (
            LocalNavRestoreSource.OPERATOR_INTENT_CONTRACT
        ),
        LocalNavSelectionSource.UNAVAILABLE_FALLBACK: (
            LocalNavRestoreSource.UNAVAILABLE_FALLBACK
        ),
        LocalNavSelectionSource.PROTECTED_FALLBACK: (
            LocalNavRestoreSource.PROTECTED_FALLBACK
        ),
    }
    return mapping[source]


def _profile_items_by_kind(
    surface_id: str,
    items: tuple[LocalNavItemContract, ...],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    surface_items = _items_for_surface(surface_id, items)
    primary: list[str] = []
    protected: list[str] = []
    unavailable: list[str] = []
    deferred: list[str] = []
    for item in surface_items:
        if item.availability == LocalNavAvailabilityState.UNAVAILABLE:
            unavailable.append(item.nav_item_id)
        elif item.deferred or item.availability == LocalNavAvailabilityState.DEFERRED:
            deferred.append(item.nav_item_id)
        elif item.protected or item.availability == LocalNavAvailabilityState.PROTECTED:
            protected.append(item.nav_item_id)
        else:
            primary.append(item.nav_item_id)
    return tuple(primary), tuple(protected), tuple(unavailable), tuple(deferred)


def build_local_nav_context_carryover_contract(
    *,
    surface_id: str,
    previous_projection_ref: str,
    current_projection_ref: str,
    selected_nav_item_ref: str,
    selected_group_ref: str,
    carryover_reason: str = "READ_MODEL_CONTINUITY_FROM_HIERARCHY_PROJECTION",
    carryover_available: bool = True,
    carryover_unavailable_reason: str = "",
) -> LocalNavContextCarryoverContract:
    if not carryover_available:
        _require_reason(carryover_unavailable_reason, field="carryover_unavailable_reason")
    payload = {
        "schema_version": LOCAL_NAV_CONTEXT_CARRYOVER_VERSION,
        "surface_id": surface_id,
        "previous_projection_ref": previous_projection_ref,
        "current_projection_ref": current_projection_ref,
        "selected_nav_item_ref": selected_nav_item_ref,
        "selected_group_ref": selected_group_ref,
        "carryover_reason": carryover_reason,
        "carryover_available": carryover_available,
        "carryover_unavailable_reason": carryover_unavailable_reason,
        "writes_memory": False,
        "writes_trace": False,
        "mutates_runtime": False,
        "uses_local_storage": False,
        "uses_browser_storage": False,
        "executes_route": False,
        "truth_label": P22CTruthLabel.CONTEXT_CARRYOVER_CONTRACT.value,
        "non_goals": _CARRYOVER_NON_GOALS,
    }
    contract = LocalNavContextCarryoverContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_context_carryover_is_not_memory_persistence(contract)
    assert_context_carryover_does_not_write_trace(contract)
    return contract


def build_local_nav_context_carryover_contracts(
    *,
    hierarchy_projection: LocalNavHierarchyProjectionResult | None = None,
    selection_states: tuple[LocalNavSelectionState, ...] | None = None,
    current_projection_ref: str | None = None,
) -> tuple[LocalNavContextCarryoverContract, ...]:
    if hierarchy_projection is None:
        hierarchy_projection = build_local_nav_hierarchy_projection_result()
    if selection_states is None:
        selection_states = build_local_nav_selection_states()
    previous_ref = (
        f"{P2_2_B_REPORT_FILENAME}:{hierarchy_projection.projection_id}"
    )
    current_ref = current_projection_ref or (
        f"{P2_2_C_REPORT_FILENAME}:{LOCAL_NAV_CONTEXT_PROJECTION_ID}"
    )
    selection_by_surface = {state.surface_id: state for state in selection_states}
    contracts: list[LocalNavContextCarryoverContract] = []
    for surface_id in CANONICAL_SURFACE_ORDER:
        state = selection_by_surface[surface_id]
        available = bool(state.selected_nav_item_id) and state.selection_valid
        unavailable_reason = ""
        if not available:
            unavailable_reason = state.invalid_reason or (
                "CARRYOVER_UNAVAILABLE: no valid selection to carry over"
            )
        contracts.append(
            build_local_nav_context_carryover_contract(
                surface_id=surface_id,
                previous_projection_ref=previous_ref,
                current_projection_ref=current_ref,
                selected_nav_item_ref=state.selected_nav_item_id,
                selected_group_ref=state.selected_group_id,
                carryover_available=available,
                carryover_unavailable_reason=unavailable_reason,
            )
        )
    return tuple(contracts)


def build_surface_local_nav_profile_contract(
    registry: PerSurfaceLocalNavRegistry,
    *,
    items: tuple[LocalNavItemContract, ...] | None = None,
    profile_kind: SurfaceLocalNavProfileKind | str | None = None,
) -> SurfaceLocalNavProfileContract:
    if items is None:
        items = build_local_nav_item_contracts()
    surface_id = registry.surface_id
    if profile_kind is None:
        kind_str = _SURFACE_PROFILE_KINDS.get(surface_id, "COMMAND_SURFACE")
        profile_kind = _coerce_enum(
            SurfaceLocalNavProfileKind, kind_str, "profile_kind"
        )
    else:
        profile_kind = _coerce_enum(
            SurfaceLocalNavProfileKind, profile_kind, "profile_kind"
        )
    primary, protected, unavailable, deferred = _profile_items_by_kind(surface_id, items)
    for item in _items_for_surface(surface_id, items):
        if item.availability == LocalNavAvailabilityState.UNAVAILABLE and not item.unavailable_reason:
            _require_reason(item.unavailable_reason, field="unavailable_reason")
        if item.deferred and (not item.deferred_to_section or not item.deferred_to_pack):
            _reject(
                "deferred item requires deferred_to_section and deferred_to_pack",
                field="deferred_to_section",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    payload = {
        "schema_version": LOCAL_NAV_SURFACE_PROFILE_VERSION,
        "surface_id": surface_id,
        "surface_display_name": registry.surface_display_name,
        "profile_id": f"local_nav_profile_{surface_id}",
        "profile_kind": profile_kind,
        "default_group_id": registry.default_local_nav_group,
        "primary_nav_items": primary,
        "protected_nav_items": protected,
        "unavailable_nav_items": unavailable,
        "deferred_nav_items": deferred,
        "profile_truth_label": P22CTruthLabel.SURFACE_LOCAL_NAV_PROFILE_CONTRACT.value,
        "creates_surface_taxonomy": False,
        "activates_future_surface": False,
        "creates_ui": False,
        "creates_sidebar": False,
        "executes_routes": False,
        "mutates_runtime": False,
        "truth_label": P22CTruthLabel.SURFACE_LOCAL_NAV_PROFILE_CONTRACT.value,
        "non_goals": _PROFILE_NON_GOALS,
    }
    contract = SurfaceLocalNavProfileContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_surface_profile_uses_official_surface(contract)
    assert_surface_profile_does_not_create_surface_taxonomy(contract)
    return contract


def build_surface_local_nav_profile_contracts(
    *,
    registries: tuple[PerSurfaceLocalNavRegistry, ...] | None = None,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> tuple[SurfaceLocalNavProfileContract, ...]:
    if registries is None:
        registries = build_per_surface_local_nav_registries()
    if items is None:
        items = build_local_nav_item_contracts()
    return tuple(
        build_surface_local_nav_profile_contract(registry, items=items)
        for registry in registries
    )


def build_local_nav_state_restoration_contract(
    selection: LocalNavSelectionState,
    *,
    restore_source: LocalNavRestoreSource | str | None = None,
    restoration_valid: bool | None = None,
    invalid_reason: str = "",
) -> LocalNavStateRestorationContract:
    source = restore_source
    if source is None:
        source = _selection_source_to_restore_source(selection.selection_source)
    else:
        source = _coerce_enum(LocalNavRestoreSource, source, "restore_source")
    valid = selection.selection_valid if restoration_valid is None else restoration_valid
    reason = invalid_reason or (selection.invalid_reason if not valid else "")
    if not valid:
        _require_reason(reason, field="invalid_reason")
    payload = {
        "schema_version": LOCAL_NAV_RESTORATION_VERSION,
        "surface_id": selection.surface_id,
        "restore_source": source,
        "restored_group_id": selection.selected_group_id,
        "restored_nav_item_id": selection.selected_nav_item_id,
        "restoration_valid": valid,
        "invalid_reason": reason if not valid else "",
        "route_executed": False,
        "action_executed": False,
        "url_mutated": False,
        "runtime_mutated": False,
        "memory_written": False,
        "trace_written": False,
        "local_storage_written": False,
        "browser_storage_written": False,
        "truth_label": P22CTruthLabel.STATE_RESTORATION_CONTRACT.value,
        "non_goals": _RESTORATION_NON_GOALS,
    }
    contract = LocalNavStateRestorationContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_state_restoration_is_not_route_execution(contract)
    assert_state_restoration_does_not_mutate_url(contract)
    assert_state_restoration_does_not_mutate_runtime(contract)
    return contract


def build_local_nav_state_restoration_contracts(
    *,
    selection_states: tuple[LocalNavSelectionState, ...] | None = None,
) -> tuple[LocalNavStateRestorationContract, ...]:
    if selection_states is None:
        selection_states = build_local_nav_selection_states()
    return tuple(
        build_local_nav_state_restoration_contract(state)
        for state in selection_states
    )


def _default_degraded_profile_for_surface(
    surface_id: str,
    profile_id: str,
) -> tuple[bool, bool, str, str, str, str]:
    """Return degraded, unavailable, degradation_reason, unavailable_reason, operator_message, fallback."""
    if surface_id == SYSTEM_SURFACE_ID:
        return (
            True,
            False,
            "PROTECTED_BOUNDARY: operator-only local nav profile with protected items",
            "",
            "SYSTEM local nav profile is contract-only; operator context required for protected items",
            f"local_nav_profile_{surface_id}_default",
        )
    if surface_id == "hub":
        return (
            False,
            True,
            "",
            "UNAVAILABLE_LOCAL_NAV: hub advanced local nav placeholder not contract-bound in P2.2-C",
            "Hub local nav profile unavailable for advanced placeholder items only",
            f"local_nav_profile_{surface_id}_default",
        )
    return False, False, "", "", "", f"local_nav_profile_{surface_id}"


def build_local_nav_degraded_profile_contract(
    profile: SurfaceLocalNavProfileContract,
    *,
    degraded: bool | None = None,
    unavailable: bool | None = None,
    degradation_reason: str = "",
    unavailable_reason: str = "",
    operator_message: str = "",
    fallback_profile_id: str = "",
) -> LocalNavDegradedProfileContract:
    defaults = _default_degraded_profile_for_surface(
        profile.surface_id, profile.profile_id
    )
    deg, unav, deg_reason, unav_reason, op_msg, fallback = defaults
    if degraded is not None:
        deg = degraded
    if unavailable is not None:
        unav = unavailable
    if degradation_reason:
        deg_reason = degradation_reason
    if unavailable_reason:
        unav_reason = unavailable_reason
    if operator_message:
        op_msg = operator_message
    if fallback_profile_id:
        fallback = fallback_profile_id
    if deg:
        _require_reason(deg_reason, field="degradation_reason")
    if unav:
        _require_reason(unav_reason, field="unavailable_reason")
    truth = (
        P22CTruthLabel.UNAVAILABLE_PROFILE_CONTRACT.value
        if unav
        else P22CTruthLabel.DEGRADED_PROFILE_CONTRACT.value
    )
    payload = {
        "schema_version": LOCAL_NAV_DEGRADED_PROFILE_VERSION,
        "surface_id": profile.surface_id,
        "profile_id": profile.profile_id,
        "degraded": deg,
        "unavailable": unav,
        "degradation_reason": deg_reason,
        "unavailable_reason": unav_reason,
        "operator_message": op_msg,
        "fallback_profile_id": fallback,
        "requires_repair": False,
        "is_runtime_failure": False,
        "runtime_failure_proven": False,
        "starts_repair_automation": False,
        "emits_notification": False,
        "mutates_runtime": False,
        "truth_label": truth,
        "non_goals": _DEGRADED_NON_GOALS,
    }
    contract = LocalNavDegradedProfileContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_degraded_profile_requires_reason(contract)
    assert_degraded_profile_is_not_runtime_failure_claim(contract)
    return contract


def build_local_nav_degraded_profile_contracts(
    *,
    profiles: tuple[SurfaceLocalNavProfileContract, ...] | None = None,
) -> tuple[LocalNavDegradedProfileContract, ...]:
    if profiles is None:
        profiles = build_surface_local_nav_profile_contracts()
    return tuple(
        build_local_nav_degraded_profile_contract(profile) for profile in profiles
    )


def build_p2_2_c_side_effect_proof() -> P22CSideEffectProof:
    return P22CSideEffectProof()


def build_local_nav_context_projection_result(
    *,
    foundation: LocalNavProjectionSeed | None = None,
    hierarchy_projection: LocalNavHierarchyProjectionResult | None = None,
    context_carryover_contracts: tuple[LocalNavContextCarryoverContract, ...] | None = None,
    surface_profile_contracts: tuple[SurfaceLocalNavProfileContract, ...] | None = None,
    state_restoration_contracts: tuple[LocalNavStateRestorationContract, ...] | None = None,
    degraded_profile_contracts: tuple[LocalNavDegradedProfileContract, ...] | None = None,
) -> LocalNavContextProjectionResult:
    if foundation is None:
        foundation = build_local_nav_projection_seed()
    if hierarchy_projection is None:
        hierarchy_projection = build_local_nav_hierarchy_projection_result(
            foundation=foundation
        )
    current_ref = f"{P2_2_C_REPORT_FILENAME}:{LOCAL_NAV_CONTEXT_PROJECTION_ID}"
    if context_carryover_contracts is None:
        context_carryover_contracts = build_local_nav_context_carryover_contracts(
            hierarchy_projection=hierarchy_projection,
            current_projection_ref=current_ref,
        )
    if surface_profile_contracts is None:
        surface_profile_contracts = build_surface_local_nav_profile_contracts()
    if state_restoration_contracts is None:
        state_restoration_contracts = build_local_nav_state_restoration_contracts()
    if degraded_profile_contracts is None:
        degraded_profile_contracts = build_local_nav_degraded_profile_contracts(
            profiles=surface_profile_contracts
        )
    side_effects = build_p2_2_c_side_effect_proof()
    foundation_ref = f"{P2_2_A_REPORT_FILENAME}:{foundation.projection_id}"
    hierarchy_ref = (
        f"{P2_2_B_REPORT_FILENAME}:{hierarchy_projection.projection_id}"
    )
    truth_boundary_payload = {
        "is_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "creates_route_runtime": False,
        "executes_routes": False,
        "creates_click_handlers": False,
        "creates_keyboard_shortcuts": False,
        "creates_command_palette": False,
        "creates_floating_windows": False,
        "writes_memory": False,
        "writes_trace": False,
        "mutates_runtime": False,
        "uses_local_storage": False,
        "uses_browser_storage": False,
        "creates_surface_taxonomy": False,
        "starts_p2_2_d": False,
        "starts_p2_3": False,
        "truth_labels": (
            P22CTruthLabel.CONTEXT_PROJECTION.value,
            P22CTruthLabel.READ_MODEL_ONLY.value,
            P22CTruthLabel.NOT_UI.value,
            P22CTruthLabel.NOT_PERSISTENCE.value,
            P22CTruthLabel.NOT_P2_2_D.value,
            P22CTruthLabel.NOT_P2_3.value,
        ),
    }
    truth_boundary = LocalNavContextProjectionTruthBoundary(
        **truth_boundary_payload,
        boundary_hash=_hash_payload(truth_boundary_payload),
    )
    payload = {
        "projection_id": LOCAL_NAV_CONTEXT_PROJECTION_ID,
        "created_for_pack": P2_2_C_PACK_ID,
        "foundation_ref": foundation_ref,
        "hierarchy_ref": hierarchy_ref,
        "context_carryover_contracts": context_carryover_contracts,
        "surface_profile_contracts": surface_profile_contracts,
        "state_restoration_contracts": state_restoration_contracts,
        "degraded_profile_contracts": degraded_profile_contracts,
        "truth_boundary": truth_boundary,
        "side_effect_proof": side_effects,
        "next_pack": P2_2_C_NEXT_PACK,
        "is_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "creates_route_runtime": False,
        "executes_routes": False,
        "creates_click_handlers": False,
        "creates_keyboard_shortcuts": False,
        "creates_command_palette": False,
        "creates_floating_windows": False,
        "writes_memory": False,
        "writes_trace": False,
        "mutates_runtime": False,
        "uses_local_storage": False,
        "uses_browser_storage": False,
        "creates_surface_taxonomy": False,
        "starts_p2_2_d": False,
        "starts_p2_3": False,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = LocalNavContextProjectionResult(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_context_projection_is_not_ui(projection)
    assert_context_projection_does_not_start_p2_2_d(projection)
    assert_context_projection_does_not_start_p2_3(projection)
    assert_local_nav_hierarchy_projection_reused(projection, hierarchy_projection)
    return projection


def build_p2_2_c_local_navigation_context_result() -> P22CLocalNavigationContextResult:
    foundation = build_local_nav_projection_seed()
    hierarchy_projection = build_local_nav_hierarchy_projection_result(
        foundation=foundation
    )
    projection = build_local_nav_context_projection_result(
        foundation=foundation,
        hierarchy_projection=hierarchy_projection,
    )
    side_effects = build_p2_2_c_side_effect_proof()
    audit_repair_ref = (
        f"{AUDIT_REPAIR_001_REPORT_FILENAME}:AUDIT-REPAIR-001"
    )
    payload = {
        "schema_version": P2_2_C_RESULT_VERSION,
        "pack_id": P2_2_C_PACK_ID,
        "section_id": P2_2_C_SECTION_ID,
        "pack_name": P2_2_C_PACK_NAME,
        "covered_checkpoints": P2_2_C_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_2_C_DEPENDENCY_PACKS,
        "audit_repair_ref": audit_repair_ref,
        "foundation_ref": projection.foundation_ref,
        "hierarchy_ref": projection.hierarchy_ref,
        "context_projection": projection,
        "side_effect_proof": side_effects,
        "truth_labels": (
            P22CTruthLabel.CONTEXT_PROJECTION.value,
            P22CTruthLabel.READ_MODEL_ONLY.value,
            P22CTruthLabel.NOT_UI.value,
            P22CTruthLabel.NOT_PERSISTENCE.value,
            P22CTruthLabel.NOT_P2_2_D.value,
            P22CTruthLabel.NOT_P2_3.value,
        ),
        "next_pack": P2_2_C_NEXT_PACK,
    }
    result = P22CLocalNavigationContextResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_2_c_depends_on_audit_repair_001(result)
    assert_p2_2_c_depends_on_p2_2_b(result, hierarchy_projection)
    return result


def serialize_p2_2_c_result(
    result: P22CLocalNavigationContextResult | None = None,
) -> str:
    if result is None:
        result = build_p2_2_c_local_navigation_context_result()
    return to_canonical_json(result.to_canonical_dict())


def validate_surface_local_nav_profile_kind(
    kind: SurfaceLocalNavProfileKind | str,
) -> SurfaceLocalNavProfileKind:
    return _coerce_enum(SurfaceLocalNavProfileKind, kind, "profile_kind")


def validate_local_nav_restore_source(
    source: LocalNavRestoreSource | str,
) -> LocalNavRestoreSource:
    return _coerce_enum(LocalNavRestoreSource, source, "restore_source")


def assert_p2_2_c_depends_on_audit_repair_001(
    result: P22CLocalNavigationContextResult,
) -> None:
    if AUDIT_REPAIR_001_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.2-C must depend on AUDIT-REPAIR-001",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if AUDIT_REPAIR_001_REPORT_FILENAME not in result.audit_repair_ref:
        _reject(
            "P2.2-C audit repair ref must reference AUDIT-REPAIR-001 report",
            field="audit_repair_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_c_depends_on_p2_2_b(
    result: P22CLocalNavigationContextResult,
    hierarchy_projection: LocalNavHierarchyProjectionResult,
) -> None:
    if P2_2_B_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.2-C must depend on P2.2-B",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_B_REPORT_FILENAME not in result.hierarchy_ref:
        _reject(
            "P2.2-C hierarchy ref must reference P2.2-B report",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if hierarchy_projection.created_for_pack != P2_2_B_PACK_ID:
        _reject(
            "P2.2-C must reuse P2.2-B hierarchy projection",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_local_nav_hierarchy_projection_reused(
    projection: LocalNavContextProjectionResult,
    hierarchy_projection: LocalNavHierarchyProjectionResult,
) -> None:
    expected = f"{P2_2_B_REPORT_FILENAME}:{hierarchy_projection.projection_id}"
    if projection.hierarchy_ref != expected:
        _reject(
            "context projection must reference P2.2-B hierarchy projection",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    for carryover in projection.context_carryover_contracts:
        if hierarchy_projection.projection_id not in carryover.previous_projection_ref:
            _reject(
                "carryover must reference previous hierarchy projection",
                field="previous_projection_ref",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_p2_2_c_no_duplicate_local_nav_registry(
    projection: LocalNavContextProjectionResult,
    foundation: LocalNavProjectionSeed,
) -> None:
    foundation_ids = {
        registry.nav_registry_id for registry in foundation.per_surface_nav_registries
    }
    profile_ids = {profile.profile_id for profile in projection.surface_profile_contracts}
    if len(profile_ids) != len(CANONICAL_SURFACE_ORDER):
        _reject(
            "surface profiles must cover official surfaces without duplication",
            field="profile_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if len(foundation_ids) != len(CANONICAL_SURFACE_ORDER):
        _reject(
            "foundation registries must match official surface count",
            field="nav_registry_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_c_no_duplicate_local_nav_hierarchy(
    projection: LocalNavContextProjectionResult,
    hierarchy_projection: LocalNavHierarchyProjectionResult,
) -> None:
    if P2_2_B_REPORT_FILENAME not in projection.hierarchy_ref:
        _reject(
            "context projection must not duplicate hierarchy; must reference P2.2-B",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if hierarchy_projection.projection_id not in projection.hierarchy_ref:
        _reject(
            "hierarchy projection id must be reused not duplicated",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_context_carryover_is_not_memory_persistence(
    contract: LocalNavContextCarryoverContract,
) -> None:
    if (
        contract.writes_memory
        or contract.uses_local_storage
        or contract.uses_browser_storage
    ):
        _reject(
            "context carryover must not persist to memory or storage",
            field="writes_memory",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_carryover_does_not_write_trace(
    contract: LocalNavContextCarryoverContract,
) -> None:
    if contract.writes_trace or contract.mutates_runtime or contract.executes_route:
        _reject(
            "context carryover must not write trace, mutate runtime, or execute route",
            field="writes_trace",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_surface_profile_uses_official_surface(
    contract: SurfaceLocalNavProfileContract,
) -> None:
    if contract.surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            "surface profile must use official surface only",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_surface_profile_does_not_create_surface_taxonomy(
    contract: SurfaceLocalNavProfileContract,
) -> None:
    if (
        contract.creates_surface_taxonomy
        or contract.activates_future_surface
        or contract.creates_ui
        or contract.creates_sidebar
        or contract.executes_routes
        or contract.mutates_runtime
    ):
        _reject(
            "surface profile must not create taxonomy, UI, or execute routes",
            field="creates_surface_taxonomy",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_state_restoration_is_not_route_execution(
    contract: LocalNavStateRestorationContract,
) -> None:
    if contract.route_executed or contract.action_executed:
        _reject(
            "state restoration must not execute route or action",
            field="route_executed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_state_restoration_does_not_mutate_url(
    contract: LocalNavStateRestorationContract,
) -> None:
    if contract.url_mutated:
        _reject(
            "state restoration must not mutate URL",
            field="url_mutated",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_state_restoration_does_not_mutate_runtime(
    contract: LocalNavStateRestorationContract,
) -> None:
    if (
        contract.runtime_mutated
        or contract.memory_written
        or contract.trace_written
        or contract.local_storage_written
        or contract.browser_storage_written
    ):
        _reject(
            "state restoration must not mutate runtime or write persistence",
            field="runtime_mutated",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_degraded_profile_requires_reason(
    contract: LocalNavDegradedProfileContract,
) -> None:
    if contract.degraded and not contract.degradation_reason:
        _reject(
            "degraded profile requires degradation_reason",
            field="degradation_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if contract.unavailable and not contract.unavailable_reason:
        _reject(
            "unavailable profile requires unavailable_reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_degraded_profile_is_not_runtime_failure_claim(
    contract: LocalNavDegradedProfileContract,
) -> None:
    if contract.is_runtime_failure and not contract.runtime_failure_proven:
        _reject(
            "runtime failure must not be claimed without proof",
            field="is_runtime_failure",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if contract.starts_repair_automation or contract.emits_notification or contract.mutates_runtime:
        _reject(
            "degraded profile must not start repair, emit notification, or mutate runtime",
            field="starts_repair_automation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_projection_is_not_ui(
    projection: LocalNavContextProjectionResult,
) -> None:
    if (
        projection.is_ui
        or projection.creates_sidebar
        or projection.creates_global_left_nav
        or projection.creates_route_runtime
        or projection.executes_routes
        or projection.creates_click_handlers
        or projection.creates_command_palette
        or projection.creates_floating_windows
    ):
        _reject(
            "context projection must not be UI or route runtime",
            field="is_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_projection_does_not_start_p2_2_d(
    projection: LocalNavContextProjectionResult,
) -> None:
    if projection.starts_p2_2_d:
        _reject(
            "P2.2-C must not start P2.2-D",
            field="starts_p2_2_d",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_projection_does_not_start_p2_3(
    projection: LocalNavContextProjectionResult,
) -> None:
    if projection.starts_p2_3:
        _reject(
            "P2.2-C must not start P2.3",
            field="starts_p2_3",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
