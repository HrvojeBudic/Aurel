"""AurelShell topbar route visibility contracts (P2.1-C / P2.1.11-P2.1.15).

Contract-only route visibility, interaction constraints, registry metadata
consistency, and blocked/deferred state projection over the P2.1-A/B topbar
registry/status foundation.

Architectural law:
  - Route visibility is not route execution.
  - Interaction constraint is not permission.
  - Blocked/deferred state is not runtime failure.
  - Registry refinement validates metadata; it does not rewrite source truth.
  - Projection is not live UI.
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
from .topbar import (
    LOGO_ROUTE_SURFACE_ID,
    P2_1_A_PACK_ID,
    P2_1_SECTION_ID,
    P2_1_SECTION_NAME,
    SETTINGS_SURFACE_ID,
    SYSTEM_SURFACE_ID,
    P21CheckpointRead,
    P21CheckpointStatus,
    SurfaceRegistry,
    TopbarReadModel,
    build_default_topbar_surface_registry,
    build_global_topbar_read_model,
)
from .topbar_status import (
    P2_1_B_NEXT_PACK,
    P2_1_B_PACK_ID,
    P21BSideEffectProof,
    TopbarStatusProjection,
    TopbarSurfaceAvailabilityStatus,
    build_topbar_status_projection,
)

P2_1_C_PACK_ID = "P2.1-C"
P2_1_C_PACK_NAME = (
    "Topbar Route Visibility / Interaction Constraints / Registry Refinement"
)
P2_1_C_NEXT_PACK = "P2.1-D"
P2_1_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.1.11",
    "P2.1.12",
    "P2.1.13",
    "P2.1.14",
    "P2.1.15",
)
P2_1_C_DEPENDENCY_PACKS: tuple[str, ...] = (
    "P2.0-A",
    "P2.0-B",
    "P2.0-C",
    "P2.0-D",
    "P2.0-E",
    "P2.0-F",
    "P2.1-A",
    "P2.1-B",
)
P2_1_A_REPORT_FILENAME = "P2_1_A_GLOBAL_TOPBAR_SURFACE_REGISTRY.md"
P2_1_B_REPORT_FILENAME = "P2_1_B_TOPBAR_STATUS_SLOTS.md"
TOPBAR_ROUTE_VISIBILITY_PROJECTION_VERSION = "topbar_route_visibility_projection.v1"
P2_1_C_PACK_RESULT_VERSION = "p2_1_c_topbar_route_visibility_result.v1"

_EnumT = TypeVar("_EnumT", bound=Enum)

_ROUTE_NON_GOALS: tuple[str, ...] = (
    "no_browser_route",
    "no_frontend_router",
    "no_cli_route_execution",
    "no_navigation_engine",
    "no_route_handler",
)
_INTERACTION_NON_GOALS: tuple[str, ...] = (
    "no_click_handlers",
    "no_keyboard_shortcuts",
    "no_command_palette",
    "no_local_nav",
    "no_route_execution",
    "no_permission_grants",
)
_REFINEMENT_NON_GOALS: tuple[str, ...] = (
    "no_surface_promotion",
    "no_forum_archivium_activation",
    "no_roadmap_rewrite",
    "no_source_of_truth_store",
    "no_registry_mutation",
)
_STATE_NON_GOALS: tuple[str, ...] = (
    "no_error_monitoring",
    "no_notification_engine",
    "no_route_runtime",
    "no_local_nav",
    "no_workflow_start",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_visual_topbar",
    "no_route_runtime",
    "no_local_nav",
    "no_command_palette",
    "no_p2_1_d_implementation",
    "no_p2_2_implementation",
)


class TopbarRouteVisibilityState(str, Enum):
    VISIBLE_ROUTE = "VISIBLE_ROUTE"
    PROTECTED_VISIBLE_ROUTE = "PROTECTED_VISIBLE_ROUTE"
    UNAVAILABLE_VISIBLE_ROUTE = "UNAVAILABLE_VISIBLE_ROUTE"


class TopbarRouteVisibilityTruthBoundary(str, Enum):
    ROUTE_VISIBILITY_ONLY = "ROUTE_VISIBILITY_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    NOT_ROUTE_RUNTIME = "NOT_ROUTE_RUNTIME"
    NOT_EXECUTION = "NOT_EXECUTION"
    NOT_FRONTEND_ROUTE = "NOT_FRONTEND_ROUTE"


class TopbarInteractionKind(str, Enum):
    SURFACE_SWITCH_INTENT = "SURFACE_SWITCH_INTENT"
    OPEN_SURFACE_INFO = "OPEN_SURFACE_INFO"
    OPEN_PROTECTED_INFO = "OPEN_PROTECTED_INFO"
    SHOW_UNAVAILABLE_REASON = "SHOW_UNAVAILABLE_REASON"
    SHOW_STATUS_DETAILS = "SHOW_STATUS_DETAILS"
    SHOW_ROUTE_VISIBILITY = "SHOW_ROUTE_VISIBILITY"
    SHOW_BLOCKED_REASON = "SHOW_BLOCKED_REASON"


class TopbarInteractionDisposition(str, Enum):
    ALLOWED_AS_INTENT = "ALLOWED_AS_INTENT"
    PROTECTED_INTENT = "PROTECTED_INTENT"
    BLOCKED_WITH_REASON = "BLOCKED_WITH_REASON"
    DEFERRED_WITH_TARGET = "DEFERRED_WITH_TARGET"
    UNAVAILABLE_WITH_REASON = "UNAVAILABLE_WITH_REASON"


class TopbarInteractionTruthBoundary(str, Enum):
    INTERACTION_CONSTRAINT_ONLY = "INTERACTION_CONSTRAINT_ONLY"
    INTENT_ONLY = "INTENT_ONLY"
    NOT_PERMISSION = "NOT_PERMISSION"
    NOT_AUTHORITY = "NOT_AUTHORITY"
    NOT_EXECUTION = "NOT_EXECUTION"
    NOT_UI_HANDLER = "NOT_UI_HANDLER"


class TopbarRegistryRefinementTruthBoundary(str, Enum):
    METADATA_CONSISTENCY_ONLY = "METADATA_CONSISTENCY_ONLY"
    NOT_ROADMAP_REWRITE = "NOT_ROADMAP_REWRITE"
    NOT_SOURCE_TRUTH_MUTATION = "NOT_SOURCE_TRUTH_MUTATION"
    NOT_SURFACE_PROMOTION = "NOT_SURFACE_PROMOTION"


class TopbarBlockedDeferredStateKind(str, Enum):
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    PROTECTED = "PROTECTED"
    DEFERRED_TO_P2_2 = "DEFERRED_TO_P2_2"
    DEFERRED_TO_P2_3 = "DEFERRED_TO_P2_3"
    DEFERRED_TO_P2_4 = "DEFERRED_TO_P2_4"
    ERROR_CONTRACT_ONLY = "ERROR_CONTRACT_ONLY"


class TopbarBlockedDeferredTruthBoundary(str, Enum):
    BLOCKED_STATE_CONTRACT_ONLY = "BLOCKED_STATE_CONTRACT_ONLY"
    DEFERRED_WITH_REASON = "DEFERRED_WITH_REASON"
    NOT_RUNTIME_FAILURE = "NOT_RUNTIME_FAILURE"
    NOT_NOTIFICATION = "NOT_NOTIFICATION"


class TopbarRouteVisibilityProjectionTruthBoundary(str, Enum):
    PROJECTION_ONLY = "PROJECTION_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_LIVE_UI = "NOT_LIVE_UI"
    NOT_ROUTE_RUNTIME = "NOT_ROUTE_RUNTIME"
    NOT_LOCAL_NAV = "NOT_LOCAL_NAV"
    NOT_COMMAND_PALETTE = "NOT_COMMAND_PALETTE"


@dataclass(frozen=True)
class TopbarRouteVisibilityContract(_CanonicalMixin):
    surface_id: str
    display_name: str
    route_hint: str
    route_label: str
    visible_in_topbar: bool
    is_default_logo_route: bool
    is_protected_route: bool
    is_unavailable_route: bool
    is_route_runtime: bool
    route_executed: bool
    creates_route_handler: bool
    creates_frontend_route: bool
    creates_cli_route: bool
    truth_label: str
    availability_status: str
    unavailable_reason: str
    source: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class TopbarInteractionConstraint(_CanonicalMixin):
    interaction_id: str
    interaction_kind: TopbarInteractionKind
    surface_id: str
    allowed_as_intent: bool
    requires_operator: bool
    blocked: bool
    blocked_reason: str
    deferred_to_section: str
    deferred_to_pack: str
    executes_action: bool
    grants_authority: bool
    permission_granted: bool
    route_executed: bool
    mutates_runtime: bool
    creates_ui_handler: bool
    creates_keyboard_shortcut: bool
    truth_label: str
    source: str
    non_goals: tuple[str, ...]
    constraint_hash: str


@dataclass(frozen=True)
class TopbarRegistryMetadataConsistencyCheck(_CanonicalMixin):
    check_id: str
    passed: bool
    reason: str
    truth_label: str
    check_hash: str


@dataclass(frozen=True)
class TopbarRegistryRefinementResult(_CanonicalMixin):
    refinement_id: str
    created_for_pack: str
    all_visible_routes_map_to_registry_surfaces: bool
    all_status_slots_map_to_registry_surfaces: bool
    all_protected_surfaces_have_boundary_metadata: bool
    all_unavailable_surfaces_have_reasons: bool
    all_deferred_states_have_targets: bool
    logo_route_remains_aurel_cro: bool
    settings_remains_non_root: bool
    system_remains_protected: bool
    no_duplicate_active_surfaces: bool
    future_refs_remain_inactive: bool
    roadmap_rewritten: bool
    registry_truth_mutated: bool
    surface_promoted: bool
    source_of_truth_created: bool
    truth_label: str
    warnings: tuple[str, ...]
    non_goals: tuple[str, ...]
    refinement_hash: str


@dataclass(frozen=True)
class TopbarBlockedDeferredState(_CanonicalMixin):
    state_id: str
    state_kind: TopbarBlockedDeferredStateKind
    surface_id: str
    interaction_kind: TopbarInteractionKind
    reason: str
    operator_message: str
    deferred_to: str
    deferred_to_section: str
    deferred_to_pack: str
    is_error: bool
    is_blocked: bool
    is_unavailable: bool
    is_protected: bool
    is_deferred: bool
    is_runtime_failure: bool
    runtime_failure_proven: bool
    truth_label: str
    source: str
    non_goals: tuple[str, ...]
    notification_created: bool
    workflow_started: bool
    state_hash: str


@dataclass(frozen=True)
class TopbarRouteVisibilityUnavailableBinding(_CanonicalMixin):
    binding_id: str
    binding_kind: str
    surface_id: str
    status: str
    unavailable_reason: str
    truth_label: str


@dataclass(frozen=True)
class P21CSideEffectProof(_CanonicalMixin):
    ui_created: bool = False
    frontend_component_created: bool = False
    frontend_route_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    cli_live_binding_created: bool = False
    tui_live_binding_created: bool = False
    route_runtime_created: bool = False
    route_handler_created: bool = False
    local_navigation_created: bool = False
    command_palette_created: bool = False
    floating_window_created: bool = False
    browser_tests_created: bool = False
    live_shell_created: bool = False
    notification_engine_created: bool = False
    approval_queue_created: bool = False
    runtime_event_stream_created: bool = False
    runtime_error_monitor_created: bool = False
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
    event_bus_created: bool = False
    api_server_created: bool = False
    http_route_created: bool = False
    roadmap_rewritten: bool = False
    registry_truth_mutated: bool = False
    surface_promoted: bool = False
    p2_1_d_started: bool = False
    p2_2_started: bool = False


@dataclass(frozen=True)
class TopbarRouteVisibilityProjection(_CanonicalMixin):
    projection_id: str
    created_for_pack: str
    topbar_read_model_ref: str
    topbar_status_projection_ref: str
    registry_ref: str
    route_visibility_contracts: tuple[TopbarRouteVisibilityContract, ...]
    interaction_constraints: tuple[TopbarInteractionConstraint, ...]
    registry_refinement_result: TopbarRegistryRefinementResult
    blocked_deferred_states: tuple[TopbarBlockedDeferredState, ...]
    truth_boundary: tuple[TopbarRouteVisibilityProjectionTruthBoundary, ...]
    unavailable_bindings: tuple[TopbarRouteVisibilityUnavailableBinding, ...]
    side_effect_proof: P21CSideEffectProof
    is_live_ui: bool
    creates_ui: bool
    creates_route_runtime: bool
    creates_frontend_route: bool
    creates_local_navigation: bool
    creates_command_palette: bool
    executes_routes: bool
    grants_authority: bool
    permission_granted: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    starts_p2_1_d: bool
    starts_p2_2: bool
    next_pack: str
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P21CTopbarRouteVisibilityPackResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    depends_on_pack: str
    depends_on_reports: tuple[str, ...]
    topbar_read_model_ref: str
    topbar_status_projection_ref: str
    registry_ref: str
    checkpoint_reads: tuple[P21CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    projection: TopbarRouteVisibilityProjection
    side_effect_proof: P21CSideEffectProof
    truth_labels: tuple[str, ...]
    next_pack: str
    is_live: bool
    is_trace_verified: bool
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


def _require_reason(reason: str, *, field: str = "reason") -> None:
    if not reason:
        _reject(
            "blocked, unavailable, protected, or error contract state requires reason",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _require_deferred_target(
    deferred_to_section: str,
    deferred_to_pack: str,
    *,
    field: str = "deferred_to_pack",
) -> None:
    if not deferred_to_section or not deferred_to_pack:
        _reject(
            "deferred interaction/state requires target section and pack",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def build_topbar_route_visibility_contract(
    surface_id: str,
    *,
    registry: SurfaceRegistry | None = None,
    availability_status: str = TopbarSurfaceAvailabilityStatus.AVAILABLE_CONTRACT.value,
    is_unavailable_route: bool = False,
    unavailable_reason: str = "",
    source: str = "P2.1-A SurfaceRegistry + P2.1-B availability projection",
) -> TopbarRouteVisibilityContract:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    entry = next((item for item in registry.entries if item.surface_id == surface_id), None)
    if entry is None:
        _reject(
            f"unknown surface id: {surface_id!r}",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    assert entry is not None
    if is_unavailable_route:
        _require_reason(unavailable_reason, field="unavailable_reason")
    is_protected = surface_id in registry.protected_surface_ids
    truth_label = (
        TopbarRouteVisibilityTruthBoundary.NOT_ROUTE_RUNTIME.value
        if not is_unavailable_route
        else TopbarRouteVisibilityTruthBoundary.CONTRACT_ONLY.value
    )
    payload = {
        "surface_id": entry.surface_id,
        "display_name": entry.display_name,
        "route_hint": entry.route,
        "route_label": f"{entry.display_name} route visibility",
        "visible_in_topbar": entry.global_topbar_visible,
        "is_default_logo_route": entry.surface_id == LOGO_ROUTE_SURFACE_ID,
        "is_protected_route": is_protected,
        "is_unavailable_route": is_unavailable_route,
        "is_route_runtime": False,
        "route_executed": False,
        "creates_route_handler": False,
        "creates_frontend_route": False,
        "creates_cli_route": False,
        "truth_label": truth_label,
        "availability_status": availability_status,
        "unavailable_reason": unavailable_reason,
        "source": source,
        "non_goals": _ROUTE_NON_GOALS,
    }
    contract = TopbarRouteVisibilityContract(**payload, contract_hash=_hash_payload(payload))
    assert_route_visibility_is_not_route_runtime(contract)
    assert_route_visibility_does_not_execute(contract)
    if contract.is_unavailable_route:
        assert_unavailable_state_has_reason(contract)
    return contract


def build_topbar_route_visibility_contracts(
    *,
    registry: SurfaceRegistry | None = None,
    status_projection: TopbarStatusProjection | None = None,
) -> tuple[TopbarRouteVisibilityContract, ...]:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if status_projection is None:
        status_projection = build_topbar_status_projection(registry=registry)
    availability_by_surface = {
        slot.surface_id: slot for slot in status_projection.surface_availability_slots
    }
    contracts: list[TopbarRouteVisibilityContract] = []
    for surface_id in registry.topbar_visible_surface_ids:
        slot = availability_by_surface.get(surface_id)
        contracts.append(
            build_topbar_route_visibility_contract(
                surface_id,
                registry=registry,
                availability_status=(
                    slot.availability_status.value
                    if slot is not None
                    else TopbarSurfaceAvailabilityStatus.AVAILABLE_CONTRACT.value
                ),
                is_unavailable_route=bool(slot and slot.is_unavailable),
                unavailable_reason=slot.unavailable_reason if slot else "",
            )
        )
    assert_visible_routes_map_to_registry(tuple(contracts), registry)
    assert_logo_route_remains_cro(tuple(contracts), registry)
    assert_system_remains_protected(tuple(contracts), registry)
    return tuple(contracts)


def build_topbar_interaction_constraint(
    interaction_id: str,
    interaction_kind: TopbarInteractionKind | str,
    surface_id: str,
    *,
    registry: SurfaceRegistry | None = None,
    disposition: TopbarInteractionDisposition | str = (
        TopbarInteractionDisposition.ALLOWED_AS_INTENT
    ),
    allowed_as_intent: bool = True,
    requires_operator: bool = False,
    blocked_reason: str = "",
    deferred_to_section: str = "",
    deferred_to_pack: str = "",
    source: str = "P2.1-C interaction safety grammar",
) -> TopbarInteractionConstraint:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if surface_id not in registry.official_surface_ids:
        _reject(
            f"unknown surface id: {surface_id!r}",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    kind = _coerce_enum(TopbarInteractionKind, interaction_kind, "interaction_kind")
    disposition_value = _coerce_enum(
        TopbarInteractionDisposition,
        disposition,
        "disposition",
    )
    blocked = disposition_value in {
        TopbarInteractionDisposition.BLOCKED_WITH_REASON,
        TopbarInteractionDisposition.DEFERRED_WITH_TARGET,
        TopbarInteractionDisposition.UNAVAILABLE_WITH_REASON,
    }
    if disposition_value == TopbarInteractionDisposition.PROTECTED_INTENT:
        requires_operator = True
    if blocked:
        _require_reason(blocked_reason, field="blocked_reason")
    if disposition_value == TopbarInteractionDisposition.DEFERRED_WITH_TARGET:
        _require_deferred_target(deferred_to_section, deferred_to_pack)
    payload = {
        "interaction_id": interaction_id,
        "interaction_kind": kind,
        "surface_id": surface_id,
        "allowed_as_intent": allowed_as_intent,
        "requires_operator": requires_operator,
        "blocked": blocked,
        "blocked_reason": blocked_reason,
        "deferred_to_section": deferred_to_section,
        "deferred_to_pack": deferred_to_pack,
        "executes_action": False,
        "grants_authority": False,
        "permission_granted": False,
        "route_executed": False,
        "mutates_runtime": False,
        "creates_ui_handler": False,
        "creates_keyboard_shortcut": False,
        "truth_label": (
            TopbarInteractionTruthBoundary.INTENT_ONLY.value
            if allowed_as_intent
            else TopbarInteractionTruthBoundary.INTERACTION_CONSTRAINT_ONLY.value
        ),
        "source": source,
        "non_goals": _INTERACTION_NON_GOALS,
    }
    constraint = TopbarInteractionConstraint(
        **payload,
        constraint_hash=_hash_payload(payload),
    )
    assert_interaction_constraint_is_not_permission(constraint)
    assert_interaction_constraint_does_not_execute(constraint)
    return constraint


def build_topbar_interaction_constraints(
    *,
    registry: SurfaceRegistry | None = None,
) -> tuple[TopbarInteractionConstraint, ...]:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    return (
        build_topbar_interaction_constraint(
            "surface_switch_intent_aurel_cro",
            TopbarInteractionKind.SURFACE_SWITCH_INTENT,
            LOGO_ROUTE_SURFACE_ID,
            registry=registry,
        ),
        build_topbar_interaction_constraint(
            "open_surface_info_hq",
            TopbarInteractionKind.OPEN_SURFACE_INFO,
            "hq",
            registry=registry,
        ),
        build_topbar_interaction_constraint(
            "open_protected_info_system",
            TopbarInteractionKind.OPEN_PROTECTED_INFO,
            SYSTEM_SURFACE_ID,
            registry=registry,
            disposition=TopbarInteractionDisposition.PROTECTED_INTENT,
            blocked_reason="SYSTEM is operator-only; topbar may show boundary info only",
        ),
        build_topbar_interaction_constraint(
            "show_unavailable_reason_aurel_cro",
            TopbarInteractionKind.SHOW_UNAVAILABLE_REASON,
            LOGO_ROUTE_SURFACE_ID,
            registry=registry,
        ),
        build_topbar_interaction_constraint(
            "show_status_details_hq",
            TopbarInteractionKind.SHOW_STATUS_DETAILS,
            "hq",
            registry=registry,
        ),
        build_topbar_interaction_constraint(
            "show_route_visibility_aurel_cro",
            TopbarInteractionKind.SHOW_ROUTE_VISIBILITY,
            LOGO_ROUTE_SURFACE_ID,
            registry=registry,
        ),
        build_topbar_interaction_constraint(
            "show_blocked_reason_system",
            TopbarInteractionKind.SHOW_BLOCKED_REASON,
            SYSTEM_SURFACE_ID,
            registry=registry,
            disposition=TopbarInteractionDisposition.BLOCKED_WITH_REASON,
            allowed_as_intent=False,
            requires_operator=True,
            blocked_reason="SYSTEM route visibility is protected and not executable",
        ),
        build_topbar_interaction_constraint(
            "defer_local_navigation_p2_2",
            TopbarInteractionKind.SHOW_ROUTE_VISIBILITY,
            "hq",
            registry=registry,
            disposition=TopbarInteractionDisposition.DEFERRED_WITH_TARGET,
            allowed_as_intent=False,
            blocked_reason="Per-surface local navigation belongs to P2.2",
            deferred_to_section="P2.2",
            deferred_to_pack="P2.2",
        ),
        build_topbar_interaction_constraint(
            "defer_floating_workspace_p2_3",
            TopbarInteractionKind.SHOW_STATUS_DETAILS,
            "hub",
            registry=registry,
            disposition=TopbarInteractionDisposition.DEFERRED_WITH_TARGET,
            allowed_as_intent=False,
            blocked_reason="Floating workspace state belongs to P2.3",
            deferred_to_section="P2.3",
            deferred_to_pack="P2.3",
        ),
        build_topbar_interaction_constraint(
            "defer_command_palette_p2_4",
            TopbarInteractionKind.SHOW_ROUTE_VISIBILITY,
            "ide",
            registry=registry,
            disposition=TopbarInteractionDisposition.DEFERRED_WITH_TARGET,
            allowed_as_intent=False,
            blocked_reason="Global command palette belongs to P2.4",
            deferred_to_section="P2.4",
            deferred_to_pack="P2.4",
        ),
    )


def build_topbar_blocked_deferred_state(
    state_id: str,
    state_kind: TopbarBlockedDeferredStateKind | str,
    surface_id: str,
    interaction_kind: TopbarInteractionKind | str,
    *,
    registry: SurfaceRegistry | None = None,
    reason: str,
    operator_message: str = "",
    deferred_to_section: str = "",
    deferred_to_pack: str = "",
    source: str = "P2.1-C blocked/deferred state contract",
) -> TopbarBlockedDeferredState:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if surface_id not in registry.official_surface_ids:
        _reject(
            f"unknown surface id: {surface_id!r}",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    kind = _coerce_enum(TopbarBlockedDeferredStateKind, state_kind, "state_kind")
    interaction = _coerce_enum(
        TopbarInteractionKind,
        interaction_kind,
        "interaction_kind",
    )
    _require_reason(reason)
    is_deferred = kind in {
        TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_2,
        TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_3,
        TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_4,
    }
    if is_deferred:
        _require_deferred_target(deferred_to_section, deferred_to_pack)
    is_error = kind == TopbarBlockedDeferredStateKind.ERROR_CONTRACT_ONLY
    payload = {
        "state_id": state_id,
        "state_kind": kind,
        "surface_id": surface_id,
        "interaction_kind": interaction,
        "reason": reason,
        "operator_message": operator_message or reason,
        "deferred_to": deferred_to_pack,
        "deferred_to_section": deferred_to_section,
        "deferred_to_pack": deferred_to_pack,
        "is_error": is_error,
        "is_blocked": kind == TopbarBlockedDeferredStateKind.BLOCKED,
        "is_unavailable": kind == TopbarBlockedDeferredStateKind.UNAVAILABLE,
        "is_protected": kind == TopbarBlockedDeferredStateKind.PROTECTED,
        "is_deferred": is_deferred,
        "is_runtime_failure": False,
        "runtime_failure_proven": False,
        "truth_label": (
            TopbarBlockedDeferredTruthBoundary.DEFERRED_WITH_REASON.value
            if is_deferred
            else TopbarBlockedDeferredTruthBoundary.BLOCKED_STATE_CONTRACT_ONLY.value
        ),
        "source": source,
        "non_goals": _STATE_NON_GOALS,
        "notification_created": False,
        "workflow_started": False,
    }
    state = TopbarBlockedDeferredState(**payload, state_hash=_hash_payload(payload))
    if state.is_blocked:
        assert_blocked_state_has_reason(state)
    if state.is_unavailable:
        assert_unavailable_state_has_reason(state)
    if state.is_deferred:
        assert_deferred_state_has_target_pack_or_section(state)
    return state


def build_topbar_blocked_deferred_states(
    *,
    registry: SurfaceRegistry | None = None,
) -> tuple[TopbarBlockedDeferredState, ...]:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    return (
        build_topbar_blocked_deferred_state(
            "system_switch_blocked_contract",
            TopbarBlockedDeferredStateKind.BLOCKED,
            SYSTEM_SURFACE_ID,
            TopbarInteractionKind.SHOW_BLOCKED_REASON,
            registry=registry,
            reason="SYSTEM route execution is blocked; SYSTEM remains operator-only",
        ),
        build_topbar_blocked_deferred_state(
            "system_protected_boundary_contract",
            TopbarBlockedDeferredStateKind.PROTECTED,
            SYSTEM_SURFACE_ID,
            TopbarInteractionKind.OPEN_PROTECTED_INFO,
            registry=registry,
            reason="SYSTEM protected boundary is displayed only, not enforced here",
            source="P2.1-B TopbarProtectedBoundarySlot",
        ),
        build_topbar_blocked_deferred_state(
            "route_runtime_unavailable_contract",
            TopbarBlockedDeferredStateKind.UNAVAILABLE,
            LOGO_ROUTE_SURFACE_ID,
            TopbarInteractionKind.SHOW_UNAVAILABLE_REASON,
            registry=registry,
            reason="UNAVAILABLE_ROUTE_RUNTIME: P2.1-C exposes route visibility only",
        ),
        build_topbar_blocked_deferred_state(
            "local_navigation_deferred_p2_2",
            TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_2,
            "hq",
            TopbarInteractionKind.SHOW_ROUTE_VISIBILITY,
            registry=registry,
            reason="Per-surface local navigation belongs to P2.2",
            deferred_to_section="P2.2",
            deferred_to_pack="P2.2",
        ),
        build_topbar_blocked_deferred_state(
            "floating_workspace_deferred_p2_3",
            TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_3,
            "hub",
            TopbarInteractionKind.SHOW_STATUS_DETAILS,
            registry=registry,
            reason="Floating/window workspace state belongs to P2.3",
            deferred_to_section="P2.3",
            deferred_to_pack="P2.3",
        ),
        build_topbar_blocked_deferred_state(
            "command_palette_deferred_p2_4",
            TopbarBlockedDeferredStateKind.DEFERRED_TO_P2_4,
            "ide",
            TopbarInteractionKind.SHOW_ROUTE_VISIBILITY,
            registry=registry,
            reason="Global command palette belongs to P2.4",
            deferred_to_section="P2.4",
            deferred_to_pack="P2.4",
        ),
        build_topbar_blocked_deferred_state(
            "error_contract_only_not_runtime_failure",
            TopbarBlockedDeferredStateKind.ERROR_CONTRACT_ONLY,
            LOGO_ROUTE_SURFACE_ID,
            TopbarInteractionKind.SHOW_UNAVAILABLE_REASON,
            registry=registry,
            reason="ERROR_CONTRACT_ONLY: explanatory state, no runtime failure proven",
        ),
    )


def build_topbar_registry_metadata_consistency_check(
    check_id: str,
    passed: bool,
    reason: str,
    *,
    truth_label: str = (
        TopbarRegistryRefinementTruthBoundary.METADATA_CONSISTENCY_ONLY.value
    ),
) -> TopbarRegistryMetadataConsistencyCheck:
    payload = {
        "check_id": check_id,
        "passed": passed,
        "reason": reason,
        "truth_label": truth_label,
    }
    return TopbarRegistryMetadataConsistencyCheck(
        **payload,
        check_hash=_hash_payload(payload),
    )


def build_topbar_registry_refinement_result(
    *,
    registry: SurfaceRegistry | None = None,
    topbar_read_model: TopbarReadModel | None = None,
    status_projection: TopbarStatusProjection | None = None,
    route_visibility_contracts: tuple[TopbarRouteVisibilityContract, ...] | None = None,
    blocked_deferred_states: tuple[TopbarBlockedDeferredState, ...] | None = None,
) -> TopbarRegistryRefinementResult:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if topbar_read_model is None:
        topbar_read_model = build_global_topbar_read_model(registry=registry)
    if status_projection is None:
        status_projection = build_topbar_status_projection(
            registry=registry,
            topbar_read_model=topbar_read_model,
        )
    if route_visibility_contracts is None:
        route_visibility_contracts = build_topbar_route_visibility_contracts(
            registry=registry,
            status_projection=status_projection,
        )
    if blocked_deferred_states is None:
        blocked_deferred_states = build_topbar_blocked_deferred_states(registry=registry)

    registry_ids = {entry.surface_id for entry in registry.entries}
    route_ids = {contract.surface_id for contract in route_visibility_contracts}
    status_ids = {slot.surface_id for slot in status_projection.surface_availability_slots}
    protected_slot_ids = {
        slot.surface_id for slot in status_projection.protected_boundary_slots
    }
    duplicate_free = len(registry_ids) == len(registry.entries)
    future_refs_inactive = True
    for ref in registry.future_surface_refs:
        normalized = ref.lower().replace("-", "_").replace(" ", "_")
        if normalized in registry_ids or ref in registry_ids:
            future_refs_inactive = False
            break
    warnings = tuple(
        "SURFACE_TAXONOMY_DRIFT"
        for signal in registry.taxonomy_drift_signals
        if signal.detected
    )
    payload = {
        "refinement_id": "topbar_registry_refinement_p2_1_c",
        "created_for_pack": P2_1_C_PACK_ID,
        "all_visible_routes_map_to_registry_surfaces": route_ids <= registry_ids,
        "all_status_slots_map_to_registry_surfaces": status_ids <= registry_ids,
        "all_protected_surfaces_have_boundary_metadata": set(
            registry.protected_surface_ids
        )
        <= protected_slot_ids,
        "all_unavailable_surfaces_have_reasons": all(
            (not contract.is_unavailable_route) or bool(contract.unavailable_reason)
            for contract in route_visibility_contracts
        )
        and all(
            (not slot.is_unavailable) or bool(slot.unavailable_reason)
            for slot in status_projection.surface_availability_slots
        ),
        "all_deferred_states_have_targets": all(
            (not state.is_deferred)
            or bool(state.deferred_to_section and state.deferred_to_pack)
            for state in blocked_deferred_states
        ),
        "logo_route_remains_aurel_cro": registry.logo_route_surface_id
        == LOGO_ROUTE_SURFACE_ID,
        "settings_remains_non_root": topbar_read_model.settings_entry.surface_id
        == SETTINGS_SURFACE_ID
        and topbar_read_model.settings_entry.settings_scope
        and not topbar_read_model.settings_entry.root_protected,
        "system_remains_protected": SYSTEM_SURFACE_ID in registry.protected_surface_ids,
        "no_duplicate_active_surfaces": duplicate_free,
        "future_refs_remain_inactive": future_refs_inactive,
        "roadmap_rewritten": False,
        "registry_truth_mutated": False,
        "surface_promoted": False,
        "source_of_truth_created": False,
        "truth_label": TopbarRegistryRefinementTruthBoundary.METADATA_CONSISTENCY_ONLY.value,
        "warnings": warnings,
        "non_goals": _REFINEMENT_NON_GOALS,
    }
    result = TopbarRegistryRefinementResult(
        **payload,
        refinement_hash=_hash_payload(payload),
    )
    assert_registry_refinement_does_not_rewrite_roadmap(result)
    assert_registry_refinement_does_not_mutate_registry_truth(result)
    if not result.all_unavailable_surfaces_have_reasons:
        _reject(
            "unavailable route/status metadata requires reasons",
            field="all_unavailable_surfaces_have_reasons",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not result.all_deferred_states_have_targets:
        _reject(
            "deferred states require target section/pack",
            field="all_deferred_states_have_targets",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return result


def build_p2_1_c_side_effect_proof() -> P21CSideEffectProof:
    return P21CSideEffectProof()


def _unavailable_bindings(
    contracts: tuple[TopbarRouteVisibilityContract, ...],
    states: tuple[TopbarBlockedDeferredState, ...],
) -> tuple[TopbarRouteVisibilityUnavailableBinding, ...]:
    bindings: list[TopbarRouteVisibilityUnavailableBinding] = []
    for contract in contracts:
        if contract.is_unavailable_route:
            bindings.append(
                TopbarRouteVisibilityUnavailableBinding(
                    binding_id=f"{contract.surface_id}_route_unavailable",
                    binding_kind="route_visibility",
                    surface_id=contract.surface_id,
                    status=TopbarRouteVisibilityState.UNAVAILABLE_VISIBLE_ROUTE.value,
                    unavailable_reason=contract.unavailable_reason,
                    truth_label=contract.truth_label,
                )
            )
    for state in states:
        if state.is_unavailable or state.is_deferred or state.is_error:
            bindings.append(
                TopbarRouteVisibilityUnavailableBinding(
                    binding_id=f"{state.state_id}_binding",
                    binding_kind="blocked_deferred_state",
                    surface_id=state.surface_id,
                    status=state.state_kind.value,
                    unavailable_reason=state.reason,
                    truth_label=state.truth_label,
                )
            )
    return tuple(bindings)


def build_topbar_route_visibility_projection(
    *,
    registry: SurfaceRegistry | None = None,
    topbar_read_model: TopbarReadModel | None = None,
    status_projection: TopbarStatusProjection | None = None,
    route_visibility_contracts: tuple[TopbarRouteVisibilityContract, ...] | None = None,
    interaction_constraints: tuple[TopbarInteractionConstraint, ...] | None = None,
    blocked_deferred_states: tuple[TopbarBlockedDeferredState, ...] | None = None,
) -> TopbarRouteVisibilityProjection:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if topbar_read_model is None:
        topbar_read_model = build_global_topbar_read_model(registry=registry)
    if status_projection is None:
        status_projection = build_topbar_status_projection(
            registry=registry,
            topbar_read_model=topbar_read_model,
        )
    if route_visibility_contracts is None:
        route_visibility_contracts = build_topbar_route_visibility_contracts(
            registry=registry,
            status_projection=status_projection,
        )
    if interaction_constraints is None:
        interaction_constraints = build_topbar_interaction_constraints(registry=registry)
    if blocked_deferred_states is None:
        blocked_deferred_states = build_topbar_blocked_deferred_states(registry=registry)

    assert_route_visibility_extends_p2_1_a_b_read_models(
        topbar_read_model,
        status_projection,
        registry,
    )
    refinement = build_topbar_registry_refinement_result(
        registry=registry,
        topbar_read_model=topbar_read_model,
        status_projection=status_projection,
        route_visibility_contracts=route_visibility_contracts,
        blocked_deferred_states=blocked_deferred_states,
    )
    side_effects = build_p2_1_c_side_effect_proof()
    unavailable_bindings = _unavailable_bindings(
        route_visibility_contracts,
        blocked_deferred_states,
    )
    payload = {
        "projection_id": "topbar_route_visibility_projection_p2_1_c",
        "created_for_pack": P2_1_C_PACK_ID,
        "topbar_read_model_ref": topbar_read_model.read_model_id,
        "topbar_status_projection_ref": status_projection.projection_id,
        "registry_ref": registry.registry_id,
        "route_visibility_contracts": route_visibility_contracts,
        "interaction_constraints": interaction_constraints,
        "registry_refinement_result": refinement,
        "blocked_deferred_states": blocked_deferred_states,
        "truth_boundary": (
            TopbarRouteVisibilityProjectionTruthBoundary.PROJECTION_ONLY,
            TopbarRouteVisibilityProjectionTruthBoundary.READ_MODEL_ONLY,
            TopbarRouteVisibilityProjectionTruthBoundary.NOT_LIVE_UI,
            TopbarRouteVisibilityProjectionTruthBoundary.NOT_ROUTE_RUNTIME,
            TopbarRouteVisibilityProjectionTruthBoundary.NOT_LOCAL_NAV,
            TopbarRouteVisibilityProjectionTruthBoundary.NOT_COMMAND_PALETTE,
        ),
        "unavailable_bindings": unavailable_bindings,
        "side_effect_proof": side_effects,
        "is_live_ui": False,
        "creates_ui": False,
        "creates_route_runtime": False,
        "creates_frontend_route": False,
        "creates_local_navigation": False,
        "creates_command_palette": False,
        "executes_routes": False,
        "grants_authority": False,
        "permission_granted": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "starts_p2_1_d": False,
        "starts_p2_2": False,
        "next_pack": P2_1_C_NEXT_PACK,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = TopbarRouteVisibilityProjection(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_is_not_live_ui(projection)
    assert_projection_creates_no_local_nav(projection)
    assert_projection_creates_no_command_palette(projection)
    assert_projection_does_not_start_p2_1_d(projection)
    assert_projection_does_not_start_p2_2(projection)
    return projection


def _checkpoint_reads() -> tuple[P21CheckpointRead, ...]:
    rows = {
        "P2.1.11": (
            "Topbar Route Visibility Contract",
            "TopbarRouteVisibilityContract, build_topbar_route_visibility_contracts()",
            "test_route_visibility_*",
            "ROUTE_VISIBILITY_ONLY / NOT_ROUTE_RUNTIME / NOT_EXECUTION",
        ),
        "P2.1.12": (
            "Topbar Interaction Constraint Contract",
            "TopbarInteractionConstraint, build_topbar_interaction_constraints()",
            "test_interaction_*",
            "INTERACTION_CONSTRAINT_ONLY / INTENT_ONLY / NOT_PERMISSION",
        ),
        "P2.1.13": (
            "Registry Refinement / Metadata Consistency Contract",
            "TopbarRegistryRefinementResult",
            "test_registry_refinement_*",
            "METADATA_CONSISTENCY_ONLY / NOT_ROADMAP_REWRITE",
        ),
        "P2.1.14": (
            "Topbar Error / Blocked / Deferred State Contract",
            "TopbarBlockedDeferredState",
            "test_blocked_deferred_*",
            "BLOCKED_STATE_CONTRACT_ONLY / NOT_RUNTIME_FAILURE",
        ),
        "P2.1.15": (
            "Topbar Route Visibility Projection / Readiness Result",
            "TopbarRouteVisibilityProjection, P21CTopbarRouteVisibilityPackResult",
            "test_route_visibility_projection_*",
            "PROJECTION_ONLY / READ_MODEL_ONLY / NOT_LIVE_UI",
        ),
    }
    return tuple(
        P21CheckpointRead(
            checkpoint_id=checkpoint_id,
            canonical_name=rows[checkpoint_id][0],
            status=P21CheckpointStatus.DONE,
            evidence=rows[checkpoint_id][1],
            tests=rows[checkpoint_id][2],
            truth_label=rows[checkpoint_id][3],
            unavailable_reason="n/a - contract/read-model route visibility only",
            limitations="No UI, route runtime, local nav, command palette, P2.1-D, or P2.2",
        )
        for checkpoint_id in P2_1_C_PACK_CHECKPOINT_IDS
    )


def build_p2_1_c_topbar_route_visibility_result() -> (
    P21CTopbarRouteVisibilityPackResult
):
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    status_projection = build_topbar_status_projection(
        registry=registry,
        topbar_read_model=read_model,
    )
    projection = build_topbar_route_visibility_projection(
        registry=registry,
        topbar_read_model=read_model,
        status_projection=status_projection,
    )
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        checkpoint.checkpoint_id: checkpoint.status.value
        for checkpoint in checkpoint_reads
    }
    side_effects = build_p2_1_c_side_effect_proof()
    payload: dict[str, Any] = {
        "schema_version": P2_1_C_PACK_RESULT_VERSION,
        "pack_id": P2_1_C_PACK_ID,
        "section_id": P2_1_SECTION_ID,
        "section_name": P2_1_SECTION_NAME,
        "covered_checkpoints": P2_1_C_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_1_C_DEPENDENCY_PACKS,
        "depends_on_pack": P2_1_B_PACK_ID,
        "depends_on_reports": (P2_1_A_REPORT_FILENAME, P2_1_B_REPORT_FILENAME),
        "topbar_read_model_ref": read_model.read_model_id,
        "topbar_status_projection_ref": status_projection.projection_id,
        "registry_ref": registry.registry_id,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "projection": projection,
        "side_effect_proof": side_effects,
        "truth_labels": (
            TopbarRouteVisibilityTruthBoundary.ROUTE_VISIBILITY_ONLY.value,
            TopbarInteractionTruthBoundary.INTERACTION_CONSTRAINT_ONLY.value,
            TopbarRegistryRefinementTruthBoundary.METADATA_CONSISTENCY_ONLY.value,
            TopbarBlockedDeferredTruthBoundary.NOT_RUNTIME_FAILURE.value,
            TopbarRouteVisibilityProjectionTruthBoundary.PROJECTION_ONLY.value,
            "NOT_LIVE",
            "NOT_TRACE_VERIFIED",
        ),
        "next_pack": P2_1_C_NEXT_PACK,
        "is_live": False,
        "is_trace_verified": False,
    }
    return P21CTopbarRouteVisibilityPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_p2_1_c_result(result: P21CTopbarRouteVisibilityPackResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_1_c_depends_on_p2_1_b(
    result: P21CTopbarRouteVisibilityPackResult,
) -> None:
    if result.depends_on_pack != P2_1_B_PACK_ID:
        _reject(
            "P2.1-C must depend on P2.1-B",
            field="depends_on_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_route_visibility_extends_p2_1_a_b_read_models(
    read_model: TopbarReadModel,
    status_projection: TopbarStatusProjection,
    registry: SurfaceRegistry,
) -> None:
    if read_model.created_for_pack != P2_1_A_PACK_ID:
        _reject(
            "route visibility must extend P2.1-A read model",
            field="topbar_read_model_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if status_projection.created_for_pack != P2_1_B_PACK_ID:
        _reject(
            "route visibility must extend P2.1-B status projection",
            field="topbar_status_projection_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if status_projection.registry_ref != registry.registry_id:
        _reject(
            "status projection must reference the same registry",
            field="registry_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_visible_routes_map_to_registry(
    contracts: tuple[TopbarRouteVisibilityContract, ...],
    registry: SurfaceRegistry,
) -> None:
    registry_ids = set(registry.official_surface_ids)
    for contract in contracts:
        if contract.visible_in_topbar and contract.surface_id not in registry_ids:
            _reject(
                f"visible route not in registry: {contract.surface_id!r}",
                field="surface_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_route_visibility_is_not_route_runtime(
    contract: TopbarRouteVisibilityContract,
) -> None:
    if (
        contract.is_route_runtime
        or contract.creates_route_handler
        or contract.creates_frontend_route
        or contract.creates_cli_route
    ):
        _reject(
            "route visibility must not create route runtime or handlers",
            field="is_route_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_route_visibility_does_not_execute(
    contract: TopbarRouteVisibilityContract,
) -> None:
    if contract.route_executed:
        _reject(
            "route visibility must not execute routes",
            field="route_executed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_interaction_constraint_is_not_permission(
    constraint: TopbarInteractionConstraint,
) -> None:
    if constraint.grants_authority or constraint.permission_granted:
        _reject(
            "interaction constraint must not grant authority or permission",
            field="permission_granted",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_interaction_constraint_does_not_execute(
    constraint: TopbarInteractionConstraint,
) -> None:
    if (
        constraint.executes_action
        or constraint.route_executed
        or constraint.mutates_runtime
        or constraint.creates_ui_handler
        or constraint.creates_keyboard_shortcut
    ):
        _reject(
            "interaction constraint must not execute or create handlers",
            field="executes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_deferred_state_has_target_pack_or_section(
    state: TopbarBlockedDeferredState,
) -> None:
    if state.is_deferred and not (state.deferred_to_section and state.deferred_to_pack):
        _reject(
            "deferred state requires target section/pack",
            field="deferred_to_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_blocked_state_has_reason(state: TopbarBlockedDeferredState) -> None:
    if state.is_blocked and not state.reason:
        _reject(
            "blocked state requires reason",
            field="reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_unavailable_state_has_reason(
    state: TopbarBlockedDeferredState | TopbarRouteVisibilityContract,
) -> None:
    if isinstance(state, TopbarBlockedDeferredState):
        missing = state.is_unavailable and not state.reason
    else:
        missing = state.is_unavailable_route and not state.unavailable_reason
    if missing:
        _reject(
            "unavailable state requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_registry_refinement_does_not_rewrite_roadmap(
    result: TopbarRegistryRefinementResult,
) -> None:
    if result.roadmap_rewritten or result.surface_promoted:
        _reject(
            "registry refinement must not rewrite roadmap or promote surfaces",
            field="roadmap_rewritten",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_registry_refinement_does_not_mutate_registry_truth(
    result: TopbarRegistryRefinementResult,
) -> None:
    if result.registry_truth_mutated or result.source_of_truth_created:
        _reject(
            "registry refinement must not mutate registry truth",
            field="registry_truth_mutated",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_logo_route_remains_cro(
    contracts: tuple[TopbarRouteVisibilityContract, ...],
    registry: SurfaceRegistry,
) -> None:
    logo_contracts = [contract for contract in contracts if contract.is_default_logo_route]
    if len(logo_contracts) != 1 or logo_contracts[0].surface_id != LOGO_ROUTE_SURFACE_ID:
        _reject(
            "logo route must remain Aurel CRO",
            field="is_default_logo_route",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if registry.logo_route_surface_id != LOGO_ROUTE_SURFACE_ID:
        _reject(
            "registry logo route must remain Aurel CRO",
            field="logo_route_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_system_remains_protected(
    contracts: tuple[TopbarRouteVisibilityContract, ...],
    registry: SurfaceRegistry,
) -> None:
    system = next(
        (contract for contract in contracts if contract.surface_id == SYSTEM_SURFACE_ID),
        None,
    )
    if system is None or not system.is_protected_route:
        _reject(
            "SYSTEM route must remain protected",
            field="is_protected_route",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if SYSTEM_SURFACE_ID not in registry.protected_surface_ids:
        _reject(
            "SYSTEM must remain in protected registry surfaces",
            field="protected_surface_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_settings_remains_non_root(
    result: TopbarRegistryRefinementResult,
) -> None:
    if not result.settings_remains_non_root:
        _reject(
            "Settings must remain non-root",
            field="settings_remains_non_root",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_future_refs_remain_inactive(
    result: TopbarRegistryRefinementResult,
) -> None:
    if not result.future_refs_remain_inactive:
        _reject(
            "future refs must remain inactive",
            field="future_refs_remain_inactive",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_projection_is_not_live_ui(
    projection: TopbarRouteVisibilityProjection,
) -> None:
    if projection.is_live_ui or projection.creates_ui:
        _reject(
            "route visibility projection must not claim live UI",
            field="is_live_ui",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if projection.creates_route_runtime or projection.executes_routes:
        _reject(
            "route visibility projection must not create or execute routes",
            field="creates_route_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_creates_no_local_nav(
    projection: TopbarRouteVisibilityProjection,
) -> None:
    if projection.creates_local_navigation:
        _reject(
            "route visibility projection must not create local navigation",
            field="creates_local_navigation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_creates_no_command_palette(
    projection: TopbarRouteVisibilityProjection,
) -> None:
    if projection.creates_command_palette:
        _reject(
            "route visibility projection must not create command palette",
            field="creates_command_palette",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_does_not_start_p2_1_d(
    projection: TopbarRouteVisibilityProjection,
) -> None:
    if projection.starts_p2_1_d:
        _reject(
            "P2.1-C must not start P2.1-D",
            field="starts_p2_1_d",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_projection_does_not_start_p2_2(
    projection: TopbarRouteVisibilityProjection,
) -> None:
    if projection.starts_p2_2:
        _reject(
            "P2.1-C must not start P2.2",
            field="starts_p2_2",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
