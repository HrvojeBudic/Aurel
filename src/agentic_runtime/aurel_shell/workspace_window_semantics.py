"""P2.3-B floating window focus / stack / grouping / restore semantics.

Contract-only workspace-window semantics over the P2.3-A workspace state
foundation. This module defines deterministic focus, stack, group, restore,
and projection read models; it does not create UI, browser/Tauri apps,
frontend focus, z-index/layout runtime, storage, memory/trace writes, route
runtime, product behavior, or runtime mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .local_navigation_context import (
    AUDIT_REPAIR_001_PACK_ID,
    AUDIT_REPAIR_001_REPORT_FILENAME,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER
from .workspace_state import (
    P2_3_A_PACK_ID,
    P2_3_A_REPORT_FILENAME,
    P2_3_A_REPORT_PATH,
    P2_3_SECTION_ID,
    P2_3_SECTION_NAME,
    P23CheckpointRead,
    P23CheckpointStatus,
    P23AWorkspaceStateFoundationResult,
    build_p2_3_a_workspace_state_foundation_result,
)

P2_3_B_PACK_ID = "P2.3-B"
P2_3_B_PACK_NAME = "Floating Window Focus / Stack / Grouping / Restore Semantics"
P2_3_B_SECTION_ID = P2_3_SECTION_ID
P2_3_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.3.6",
    "P2.3.7",
    "P2.3.8",
    "P2.3.9",
    "P2.3.10",
)
P2_3_B_DEPENDENCY_PACKS: tuple[str, ...] = (
    AUDIT_REPAIR_001_PACK_ID,
    P2_3_A_PACK_ID,
)
P2_3_B_NEXT_PACK = "P2.3-C"
P2_3_B_REPORT_FILENAME = "P2_3_B_WORKSPACE_WINDOW_SEMANTICS.md"
P2_3_B_REPORT_PATH = f"agent/reports/{P2_3_B_REPORT_FILENAME}"
P2_3_B_RESULT_VERSION = "p2_3_b_workspace_window_semantics_result.v1"
P2_3_FOCUS_INTENT_VERSION = "p2_3_b_floating_window_focus_intent_contract.v1"
P2_3_STACK_ORDER_VERSION = "p2_3_b_floating_window_stack_order_contract.v1"
P2_3_GROUP_VERSION = "p2_3_b_floating_window_group_contract.v1"
P2_3_RESTORE_VERSION = "p2_3_b_floating_window_restore_contract.v1"
P2_3_FOCUS_STACK_PROJECTION_VERSION = "p2_3_b_workspace_focus_stack_projection.v1"

_FOCUS_NON_GOALS: tuple[str, ...] = (
    "no_real_browser_focus",
    "no_visual_active_state",
    "no_focus_manager_runtime",
    "no_frontend_component_activation",
)
_STACK_NON_GOALS: tuple[str, ...] = (
    "no_z_index_runtime",
    "no_css",
    "no_layout_engine",
    "no_real_window_stacking_behavior",
)
_GROUP_NON_GOALS: tuple[str, ...] = (
    "no_desktop_workspace_ui",
    "no_frontend_group_ui",
    "no_tabs_ui",
    "no_runtime_grouping_behavior",
)
_RESTORE_NON_GOALS: tuple[str, ...] = (
    "no_persistence",
    "no_local_storage",
    "no_browser_storage",
    "no_memory_write",
    "no_trace_write",
    "no_route_execution",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_frontend_state_store",
    "no_product_behavior",
    "no_p2_3_c_implementation",
    "no_p2_10_implementation",
    "no_p2_13_implementation",
)


class FloatingWindowFocusSource(str, Enum):
    OPERATOR_INTENT = "OPERATOR_INTENT"
    WORKSPACE_READ_MODEL = "WORKSPACE_READ_MODEL"
    SURFACE_CONTEXT = "SURFACE_CONTEXT"
    RESTORE_CONTRACT = "RESTORE_CONTRACT"
    UNAVAILABLE_FALLBACK = "UNAVAILABLE_FALLBACK"


class FloatingWindowFocusReason(str, Enum):
    DEFAULT_ACTIVE_WINDOW = "DEFAULT_ACTIVE_WINDOW"
    OPERATOR_SELECTED_WINDOW = "OPERATOR_SELECTED_WINDOW"
    RESTORE_ACTIVE_WINDOW = "RESTORE_ACTIVE_WINDOW"
    GROUP_PRIMARY_WINDOW = "GROUP_PRIMARY_WINDOW"
    UNAVAILABLE_FOCUS = "UNAVAILABLE_FOCUS"


class FloatingWindowFocusTruthBoundary(str, Enum):
    FLOATING_WINDOW_FOCUS_INTENT_CONTRACT = "FLOATING_WINDOW_FOCUS_INTENT_CONTRACT"
    DECLARATIVE_INTENT_ONLY = "DECLARATIVE_INTENT_ONLY"
    NOT_FOCUS_MANAGER = "NOT_FOCUS_MANAGER"
    NOT_BROWSER_FOCUS = "NOT_BROWSER_FOCUS"


class FloatingWindowStackRole(str, Enum):
    ACTIVE = "ACTIVE"
    PREVIOUS_ACTIVE = "PREVIOUS_ACTIVE"
    BACKGROUND = "BACKGROUND"
    INSPECTOR = "INSPECTOR"
    STATUS = "STATUS"


class FloatingWindowLayerOrderHint(str, Enum):
    SURFACE_BASE = "SURFACE_BASE"
    FLOATING_PANEL = "FLOATING_PANEL"
    INSPECTION_LAYER = "INSPECTION_LAYER"
    STATUS_LAYER = "STATUS_LAYER"
    OVERLAY_HINT = "OVERLAY_HINT"


class FloatingWindowStackTruthBoundary(str, Enum):
    FLOATING_WINDOW_STACK_ORDER_CONTRACT = "FLOATING_WINDOW_STACK_ORDER_CONTRACT"
    READ_MODEL_ORDER_ONLY = "READ_MODEL_ORDER_ONLY"
    NOT_Z_INDEX_RUNTIME = "NOT_Z_INDEX_RUNTIME"
    NOT_LAYOUT_ENGINE = "NOT_LAYOUT_ENGINE"


class FloatingWindowGroupKind(str, Enum):
    REVIEW_GROUP = "REVIEW_GROUP"
    APPROVAL_GROUP = "APPROVAL_GROUP"
    TRACE_GROUP = "TRACE_GROUP"
    AGENT_WORK_GROUP = "AGENT_WORK_GROUP"
    DOCUMENT_GROUP = "DOCUMENT_GROUP"
    SYSTEM_INSPECT_GROUP = "SYSTEM_INSPECT_GROUP"
    SURFACE_CONTEXT_GROUP = "SURFACE_CONTEXT_GROUP"


class FloatingWindowGroupScope(str, Enum):
    SINGLE_SURFACE = "SINGLE_SURFACE"
    CROSS_SURFACE_READ_MODEL = "CROSS_SURFACE_READ_MODEL"
    WORKSPACE_READ_MODEL = "WORKSPACE_READ_MODEL"
    PROTECTED_SURFACE_SCOPE = "PROTECTED_SURFACE_SCOPE"


class FloatingWindowGroupTruthBoundary(str, Enum):
    FLOATING_WINDOW_GROUP_CONTRACT = "FLOATING_WINDOW_GROUP_CONTRACT"
    LOGICAL_COLLECTION_ONLY = "LOGICAL_COLLECTION_ONLY"
    NOT_DESKTOP_WORKSPACE_UI = "NOT_DESKTOP_WORKSPACE_UI"
    NOT_FRONTEND_TABS = "NOT_FRONTEND_TABS"


class FloatingWindowRestoreSource(str, Enum):
    DEFAULT_WORKSPACE_STATE = "DEFAULT_WORKSPACE_STATE"
    PREVIOUS_READ_MODEL = "PREVIOUS_READ_MODEL"
    OPERATOR_INTENT_CONTRACT = "OPERATOR_INTENT_CONTRACT"
    UNAVAILABLE_FALLBACK = "UNAVAILABLE_FALLBACK"
    ERROR_FALLBACK = "ERROR_FALLBACK"


class FloatingWindowRestoreMode(str, Enum):
    DEFAULT_RECONSTRUCTION = "DEFAULT_RECONSTRUCTION"
    READ_MODEL_RECONSTRUCTION = "READ_MODEL_RECONSTRUCTION"
    OPERATOR_INTENT_RESUME = "OPERATOR_INTENT_RESUME"
    UNAVAILABLE_RECONSTRUCTION = "UNAVAILABLE_RECONSTRUCTION"
    ERROR_BOUNDARY_RECONSTRUCTION = "ERROR_BOUNDARY_RECONSTRUCTION"


class FloatingWindowRestoreTruthBoundary(str, Enum):
    FLOATING_WINDOW_RESTORE_CONTRACT = "FLOATING_WINDOW_RESTORE_CONTRACT"
    STATE_RECONSTRUCTION_CONTRACT_ONLY = "STATE_RECONSTRUCTION_CONTRACT_ONLY"
    NOT_PERSISTENCE = "NOT_PERSISTENCE"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"


class WorkspaceFocusStackProjectionTruthBoundary(str, Enum):
    WORKSPACE_FOCUS_STACK_PROJECTION_RESULT = "WORKSPACE_FOCUS_STACK_PROJECTION_RESULT"
    DEV_FIXTURE = "DEV_FIXTURE"
    READ_MODEL_RESULT_ONLY = "READ_MODEL_RESULT_ONLY"
    NOT_FRONTEND_STATE_STORE = "NOT_FRONTEND_STATE_STORE"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"


@dataclass(frozen=True)
class P23BSideEffectProof(_CanonicalMixin):
    frontend_ui_created: bool = False
    browser_app_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    browser_focus_set: bool = False
    frontend_component_activated: bool = False
    focus_manager_created: bool = False
    draggable_window_created: bool = False
    resizable_window_created: bool = False
    window_manager_created: bool = False
    z_index_runtime_created: bool = False
    layout_engine_created: bool = False
    css_created: bool = False
    frontend_group_ui_created: bool = False
    tab_ui_created: bool = False
    desktop_workspace_ui_created: bool = False
    keyboard_shortcut_created: bool = False
    command_palette_created: bool = False
    route_runtime_created: bool = False
    routes_executed: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    local_storage_written: bool = False
    browser_storage_written: bool = False
    memory_written: bool = False
    trace_written: bool = False
    runtime_mutated: bool = False
    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_3_c_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class FloatingWindowFocusIntentContract(_CanonicalMixin):
    focus_id: str
    schema_version: str
    window_id: str
    workspace_state_id: str
    focus_source: FloatingWindowFocusSource
    focus_reason: FloatingWindowFocusReason
    active_window_candidate: str
    previous_active_window_id: str
    focus_available: bool
    unavailable_reason: str
    sets_browser_focus: bool
    activates_frontend_component: bool
    creates_focus_manager_runtime: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class FloatingWindowStackOrderContract(_CanonicalMixin):
    stack_id: str
    schema_version: str
    workspace_state_id: str
    ordered_window_ids: tuple[str, ...]
    active_window_id: str
    stack_role_map: dict[str, str]
    layer_order_hint: FloatingWindowLayerOrderHint
    z_order_hint: str
    ordering_reason: str
    creates_z_index_runtime: bool
    creates_layout_engine: bool
    creates_css: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class FloatingWindowGroupContract(_CanonicalMixin):
    group_id: str
    schema_version: str
    workspace_state_id: str
    group_kind: FloatingWindowGroupKind
    group_scope: FloatingWindowGroupScope
    window_ids: tuple[str, ...]
    primary_window_id: str
    surface_scope: tuple[str, ...]
    group_reason: str
    group_available: bool
    unavailable_reason: str
    creates_desktop_workspace: bool
    creates_frontend_group_ui: bool
    creates_tab_ui: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class FloatingWindowRestoreContract(_CanonicalMixin):
    restore_id: str
    schema_version: str
    workspace_state_id: str
    restore_source: FloatingWindowRestoreSource
    restore_mode: FloatingWindowRestoreMode
    restored_window_ids: tuple[str, ...]
    restored_active_window_id: str
    restored_group_ids: tuple[str, ...]
    restore_available: bool
    unavailable_reason: str
    resume_reason: str
    uses_local_storage: bool
    uses_browser_storage: bool
    writes_memory: bool
    writes_trace: bool
    mutates_runtime: bool
    executes_routes: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class WorkspaceFocusStackProjectionResult(_CanonicalMixin):
    projection_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    foundation_ref: str
    focus_intent_contracts: tuple[FloatingWindowFocusIntentContract, ...]
    stack_order_contracts: tuple[FloatingWindowStackOrderContract, ...]
    window_group_contracts: tuple[FloatingWindowGroupContract, ...]
    restore_contracts: tuple[FloatingWindowRestoreContract, ...]
    side_effect_proof: P23BSideEffectProof
    next_pack: str
    truth_label: str
    is_frontend_state_store: bool
    is_product_behavior: bool
    starts_p2_3_c: bool
    starts_p2_10: bool
    starts_p2_13: bool
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P23BWorkspaceWindowSemanticsResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    audit_repair_ref: str
    p2_3_a_ref: str
    foundation_ref: str
    checkpoint_reads: tuple[P23CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    focus_intent_contracts: tuple[FloatingWindowFocusIntentContract, ...]
    stack_order_contracts: tuple[FloatingWindowStackOrderContract, ...]
    window_group_contracts: tuple[FloatingWindowGroupContract, ...]
    restore_contracts: tuple[FloatingWindowRestoreContract, ...]
    workspace_focus_stack_projection_result: WorkspaceFocusStackProjectionResult
    side_effect_proof: P23BSideEffectProof
    next_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def _foundation_ref(foundation: P23AWorkspaceStateFoundationResult) -> str:
    seed = foundation.projection_seed
    return f"{seed.projection_seed_id}:{seed.projection_hash}"


def _window_ids(
    foundation: P23AWorkspaceStateFoundationResult,
) -> tuple[str, ...]:
    return tuple(contract.window_id for contract in foundation.identity_contracts)


def _workspace_state_id(foundation: P23AWorkspaceStateFoundationResult) -> str:
    return foundation.workspace_state.workspace_state_id


def build_p2_3_b_side_effect_proof() -> P23BSideEffectProof:
    return P23BSideEffectProof()


def build_floating_window_focus_intent_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    window_id: str | None = None,
    focus_source: FloatingWindowFocusSource = FloatingWindowFocusSource.WORKSPACE_READ_MODEL,
    focus_reason: FloatingWindowFocusReason = FloatingWindowFocusReason.DEFAULT_ACTIVE_WINDOW,
    previous_active_window_id: str = "",
    focus_available: bool = True,
    unavailable_reason: str = "",
) -> FloatingWindowFocusIntentContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    assert_p2_3_a_projection_seed_exists(foundation)
    known_window_ids = _window_ids(foundation)
    if window_id is None:
        window_id = known_window_ids[0]
    if window_id not in known_window_ids:
        _reject(
            "focus intent window must come from P2.3-A identity contracts",
            field="window_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not focus_available and not unavailable_reason:
        unavailable_reason = "UNAVAILABLE_FOCUS_INTENT: focus unavailable by contract"
    payload = {
        "focus_id": f"p2_3_b_focus_{window_id}",
        "schema_version": P2_3_FOCUS_INTENT_VERSION,
        "window_id": window_id,
        "workspace_state_id": _workspace_state_id(foundation),
        "focus_source": focus_source,
        "focus_reason": focus_reason,
        "active_window_candidate": window_id,
        "previous_active_window_id": previous_active_window_id,
        "focus_available": focus_available,
        "unavailable_reason": unavailable_reason,
        "sets_browser_focus": False,
        "activates_frontend_component": False,
        "creates_focus_manager_runtime": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": (
            FloatingWindowFocusTruthBoundary.FLOATING_WINDOW_FOCUS_INTENT_CONTRACT.value
        ),
        "non_goals": _FOCUS_NON_GOALS,
    }
    contract = FloatingWindowFocusIntentContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_focus_intent_is_not_focus_manager(contract)
    assert_active_window_is_not_browser_focus(contract)
    return contract


def build_floating_window_focus_intent_contracts(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
) -> tuple[FloatingWindowFocusIntentContract, ...]:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    window_ids = _window_ids(foundation)
    previous = ""
    contracts: list[FloatingWindowFocusIntentContract] = []
    for index, window_id in enumerate(window_ids):
        reason = (
            FloatingWindowFocusReason.DEFAULT_ACTIVE_WINDOW
            if index == 0
            else FloatingWindowFocusReason.OPERATOR_SELECTED_WINDOW
        )
        contracts.append(
            build_floating_window_focus_intent_contract(
                foundation=foundation,
                window_id=window_id,
                focus_reason=reason,
                previous_active_window_id=previous,
            )
        )
        previous = window_id
    return tuple(contracts)


def build_floating_window_stack_order_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    ordered_window_ids: tuple[str, ...] | None = None,
    active_window_id: str | None = None,
    layer_order_hint: FloatingWindowLayerOrderHint = (
        FloatingWindowLayerOrderHint.FLOATING_PANEL
    ),
) -> FloatingWindowStackOrderContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    known_window_ids = _window_ids(foundation)
    if ordered_window_ids is None:
        ordered_window_ids = known_window_ids
    if not ordered_window_ids:
        _reject(
            "stack order requires at least one window id",
            field="ordered_window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    unknown = tuple(window_id for window_id in ordered_window_ids if window_id not in known_window_ids)
    if unknown:
        _reject(
            "stack order window ids must come from P2.3-A identity contracts",
            field="ordered_window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if active_window_id is None:
        active_window_id = ordered_window_ids[0]
    if active_window_id not in ordered_window_ids:
        _reject(
            "active window must be represented in ordered window ids",
            field="active_window_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    stack_role_map: dict[str, str] = {}
    for index, candidate in enumerate(ordered_window_ids):
        if candidate == active_window_id:
            role = FloatingWindowStackRole.ACTIVE
        elif index == 1:
            role = FloatingWindowStackRole.PREVIOUS_ACTIVE
        elif "inspector" in candidate:
            role = FloatingWindowStackRole.INSPECTOR
        elif "system_status" in candidate:
            role = FloatingWindowStackRole.STATUS
        else:
            role = FloatingWindowStackRole.BACKGROUND
        stack_role_map[candidate] = role.value
    payload = {
        "stack_id": "p2_3_b_workspace_stack_order",
        "schema_version": P2_3_STACK_ORDER_VERSION,
        "workspace_state_id": _workspace_state_id(foundation),
        "ordered_window_ids": ordered_window_ids,
        "active_window_id": active_window_id,
        "stack_role_map": stack_role_map,
        "layer_order_hint": layer_order_hint,
        "z_order_hint": "read-model ordering hint only; no z-index runtime",
        "ordering_reason": "P2.3-B deterministic read-model stack order over P2.3-A windows",
        "creates_z_index_runtime": False,
        "creates_layout_engine": False,
        "creates_css": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": (
            FloatingWindowStackTruthBoundary.FLOATING_WINDOW_STACK_ORDER_CONTRACT.value
        ),
        "non_goals": _STACK_NON_GOALS,
    }
    contract = FloatingWindowStackOrderContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_stack_order_is_not_z_index_runtime(contract)
    assert_layer_order_is_not_layout_engine(contract)
    return contract


def build_floating_window_group_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    group_kind: FloatingWindowGroupKind = FloatingWindowGroupKind.SURFACE_CONTEXT_GROUP,
    group_scope: FloatingWindowGroupScope = FloatingWindowGroupScope.WORKSPACE_READ_MODEL,
    window_ids: tuple[str, ...] | None = None,
    primary_window_id: str | None = None,
    surface_scope: tuple[str, ...] | None = None,
    group_available: bool = True,
    unavailable_reason: str = "",
) -> FloatingWindowGroupContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    known_window_ids = _window_ids(foundation)
    if window_ids is None:
        window_ids = known_window_ids[:2]
    if not window_ids:
        _reject(
            "window group requires at least one window id",
            field="window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if any(window_id not in known_window_ids for window_id in window_ids):
        _reject(
            "window group ids must come from P2.3-A identity contracts",
            field="window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if primary_window_id is None:
        primary_window_id = window_ids[0]
    if primary_window_id not in window_ids:
        _reject(
            "primary window must be part of the group",
            field="primary_window_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if surface_scope is None:
        surface_scope = tuple(
            contract.owner_surface_id
            for contract in foundation.identity_contracts
            if contract.window_id in window_ids
        )
    if any(surface_id not in CANONICAL_SURFACE_ORDER for surface_id in surface_scope):
        _reject(
            "window group surface scope must use canonical P2 surfaces",
            field="surface_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not group_available and not unavailable_reason:
        unavailable_reason = "UNAVAILABLE_GROUP: group unavailable by contract"
    payload = {
        "group_id": f"p2_3_b_group_{group_kind.value.lower()}",
        "schema_version": P2_3_GROUP_VERSION,
        "workspace_state_id": _workspace_state_id(foundation),
        "group_kind": group_kind,
        "group_scope": group_scope,
        "window_ids": window_ids,
        "primary_window_id": primary_window_id,
        "surface_scope": surface_scope,
        "group_reason": "logical collection over P2.3-A window contracts",
        "group_available": group_available,
        "unavailable_reason": unavailable_reason,
        "creates_desktop_workspace": False,
        "creates_frontend_group_ui": False,
        "creates_tab_ui": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": FloatingWindowGroupTruthBoundary.FLOATING_WINDOW_GROUP_CONTRACT.value,
        "non_goals": _GROUP_NON_GOALS,
    }
    contract = FloatingWindowGroupContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_group_is_not_desktop_workspace_ui(contract)
    assert_group_is_not_frontend_tabs(contract)
    return contract


def build_floating_window_restore_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    groups: tuple[FloatingWindowGroupContract, ...] | None = None,
    restore_source: FloatingWindowRestoreSource = (
        FloatingWindowRestoreSource.PREVIOUS_READ_MODEL
    ),
    restore_mode: FloatingWindowRestoreMode = (
        FloatingWindowRestoreMode.READ_MODEL_RECONSTRUCTION
    ),
    restore_available: bool = True,
    unavailable_reason: str = "",
) -> FloatingWindowRestoreContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    if groups is None:
        groups = (build_floating_window_group_contract(foundation=foundation),)
    restored_window_ids = _window_ids(foundation)
    restored_active_window_id = restored_window_ids[0]
    restored_group_ids = tuple(group.group_id for group in groups)
    if not restore_available and not unavailable_reason:
        unavailable_reason = "UNAVAILABLE_RESTORE: restore unavailable by contract"
    payload = {
        "restore_id": "p2_3_b_workspace_restore_resume",
        "schema_version": P2_3_RESTORE_VERSION,
        "workspace_state_id": _workspace_state_id(foundation),
        "restore_source": restore_source,
        "restore_mode": restore_mode,
        "restored_window_ids": restored_window_ids,
        "restored_active_window_id": restored_active_window_id,
        "restored_group_ids": restored_group_ids,
        "restore_available": restore_available,
        "unavailable_reason": unavailable_reason,
        "resume_reason": "read-model reconstruction from P2.3-A projection seed and P2.3-B contracts",
        "uses_local_storage": False,
        "uses_browser_storage": False,
        "writes_memory": False,
        "writes_trace": False,
        "mutates_runtime": False,
        "executes_routes": False,
        "truth_label": (
            FloatingWindowRestoreTruthBoundary.FLOATING_WINDOW_RESTORE_CONTRACT.value
        ),
        "non_goals": _RESTORE_NON_GOALS,
    }
    contract = FloatingWindowRestoreContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_restore_is_not_persistence(contract)
    assert_resume_state_is_not_memory_write(contract)
    assert_restore_does_not_use_local_storage(contract)
    assert_restore_does_not_use_browser_storage(contract)
    return contract


def build_workspace_focus_stack_projection_result(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    focus_intent_contracts: tuple[FloatingWindowFocusIntentContract, ...] | None = None,
    stack_order_contracts: tuple[FloatingWindowStackOrderContract, ...] | None = None,
    window_group_contracts: tuple[FloatingWindowGroupContract, ...] | None = None,
    restore_contracts: tuple[FloatingWindowRestoreContract, ...] | None = None,
    side_effect_proof: P23BSideEffectProof | None = None,
) -> WorkspaceFocusStackProjectionResult:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    if focus_intent_contracts is None:
        focus_intent_contracts = build_floating_window_focus_intent_contracts(
            foundation=foundation
        )
    if stack_order_contracts is None:
        stack_order_contracts = (
            build_floating_window_stack_order_contract(foundation=foundation),
        )
    if window_group_contracts is None:
        window_group_contracts = (
            build_floating_window_group_contract(foundation=foundation),
        )
    if restore_contracts is None:
        restore_contracts = (
            build_floating_window_restore_contract(
                foundation=foundation,
                groups=window_group_contracts,
            ),
        )
    if side_effect_proof is None:
        side_effect_proof = build_p2_3_b_side_effect_proof()
    payload = {
        "projection_id": "p2_3_b_workspace_focus_stack_projection",
        "schema_version": P2_3_FOCUS_STACK_PROJECTION_VERSION,
        "section_id": P2_3_B_SECTION_ID,
        "created_for_pack": P2_3_B_PACK_ID,
        "foundation_ref": _foundation_ref(foundation),
        "focus_intent_contracts": focus_intent_contracts,
        "stack_order_contracts": stack_order_contracts,
        "window_group_contracts": window_group_contracts,
        "restore_contracts": restore_contracts,
        "side_effect_proof": side_effect_proof,
        "next_pack": P2_3_B_NEXT_PACK,
        "truth_label": (
            WorkspaceFocusStackProjectionTruthBoundary.WORKSPACE_FOCUS_STACK_PROJECTION_RESULT.value
        ),
        "is_frontend_state_store": False,
        "is_product_behavior": False,
        "starts_p2_3_c": False,
        "starts_p2_10": False,
        "starts_p2_13": False,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = WorkspaceFocusStackProjectionResult(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_result_is_not_frontend_state_store(projection)
    assert_projection_result_is_not_product_behavior(projection)
    assert_p2_3_b_does_not_start_p2_3_c(projection)
    assert_p2_3_b_does_not_start_p2_10(projection)
    assert_p2_3_b_does_not_start_p2_13(projection)
    assert_p2_3_b_side_effects_all_false(projection.side_effect_proof)
    return projection


def _checkpoint_reads() -> tuple[P23CheckpointRead, ...]:
    rows = {
        "P2.3.6": (
            "Floating Window Focus Intent Contract",
            "FloatingWindowFocusIntentContract",
            "test_p2_3_6_*",
            "FLOATING_WINDOW_FOCUS_INTENT_CONTRACT / NOT_FOCUS_MANAGER",
            "focus manager runtime unavailable by contract",
            "Declarative active-window candidate only; no browser focus",
        ),
        "P2.3.7": (
            "Floating Window Stack / Layer Order Contract",
            "FloatingWindowStackOrderContract",
            "test_p2_3_7_*",
            "FLOATING_WINDOW_STACK_ORDER_CONTRACT / NOT_Z_INDEX_RUNTIME",
            "z-index/layout runtime unavailable by contract",
            "Read-model ordering only; no CSS, z-index, or layout engine",
        ),
        "P2.3.8": (
            "Floating Window Group / Collection Contract",
            "FloatingWindowGroupContract",
            "test_p2_3_8_*",
            "FLOATING_WINDOW_GROUP_CONTRACT / NOT_FRONTEND_TABS",
            "desktop workspace UI unavailable by contract",
            "Logical collection only; no group UI or tabs UI",
        ),
        "P2.3.9": (
            "Floating Window Restore / Resume Contract",
            "FloatingWindowRestoreContract",
            "test_p2_3_9_*",
            "FLOATING_WINDOW_RESTORE_CONTRACT / NOT_PERSISTENCE",
            "storage/persistence unavailable by contract",
            "Read-model reconstruction only; no storage, memory, trace, or routes",
        ),
        "P2.3.10": (
            "Workspace Focus/Stack Projection Result",
            "WorkspaceFocusStackProjectionResult",
            "test_p2_3_10_*",
            "WORKSPACE_FOCUS_STACK_PROJECTION_RESULT / NOT_PRODUCT_BEHAVIOR",
            "frontend/product behavior unavailable by contract",
            "Bundles P2.3-B semantics over P2.3-A projection seed only",
        ),
    }
    reads: list[P23CheckpointRead] = []
    for checkpoint_id in P2_3_B_PACK_CHECKPOINT_IDS:
        row = rows[checkpoint_id]
        payload = {
            "checkpoint_id": checkpoint_id,
            "canonical_name": row[0],
            "status": P23CheckpointStatus.DONE,
            "evidence": row[1],
            "tests": row[2],
            "truth_label": row[3],
            "unavailable_reason": row[4],
            "limitations": row[5],
        }
        reads.append(P23CheckpointRead(**payload, read_hash=_hash_payload(payload)))
    return tuple(reads)


def build_p2_3_b_workspace_window_semantics_result() -> (
    P23BWorkspaceWindowSemanticsResult
):
    foundation = build_p2_3_a_workspace_state_foundation_result()
    assert_p2_3_a_projection_seed_exists(foundation)
    focus_contracts = build_floating_window_focus_intent_contracts(
        foundation=foundation
    )
    stack_contracts = (
        build_floating_window_stack_order_contract(foundation=foundation),
    )
    group_contracts = (
        build_floating_window_group_contract(foundation=foundation),
    )
    restore_contracts = (
        build_floating_window_restore_contract(
            foundation=foundation,
            groups=group_contracts,
        ),
    )
    side_effects = build_p2_3_b_side_effect_proof()
    projection = build_workspace_focus_stack_projection_result(
        foundation=foundation,
        focus_intent_contracts=focus_contracts,
        stack_order_contracts=stack_contracts,
        window_group_contracts=group_contracts,
        restore_contracts=restore_contracts,
        side_effect_proof=side_effects,
    )
    drift, drift_details = detect_surface_taxonomy_drift()
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    payload = {
        "schema_version": P2_3_B_RESULT_VERSION,
        "pack_id": P2_3_B_PACK_ID,
        "section_id": P2_3_B_SECTION_ID,
        "section_name": P2_3_SECTION_NAME,
        "covered_checkpoints": P2_3_B_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_3_B_DEPENDENCY_PACKS,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "audit_repair_ref": (
            f"agent/reports/{AUDIT_REPAIR_001_REPORT_FILENAME}:"
            f"{AUDIT_REPAIR_001_PACK_ID}"
        ),
        "p2_3_a_ref": f"{P2_3_A_REPORT_PATH}:{P2_3_A_PACK_ID}",
        "foundation_ref": _foundation_ref(foundation),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": (
            FloatingWindowFocusTruthBoundary.FLOATING_WINDOW_FOCUS_INTENT_CONTRACT.value,
            FloatingWindowStackTruthBoundary.FLOATING_WINDOW_STACK_ORDER_CONTRACT.value,
            FloatingWindowGroupTruthBoundary.FLOATING_WINDOW_GROUP_CONTRACT.value,
            FloatingWindowRestoreTruthBoundary.FLOATING_WINDOW_RESTORE_CONTRACT.value,
            WorkspaceFocusStackProjectionTruthBoundary.WORKSPACE_FOCUS_STACK_PROJECTION_RESULT.value,
            WorkspaceFocusStackProjectionTruthBoundary.READ_MODEL_RESULT_ONLY.value,
            WorkspaceFocusStackProjectionTruthBoundary.NOT_PRODUCT_BEHAVIOR.value,
        ),
        "unavailable_reasons": (
            "UNAVAILABLE_FOCUS_MANAGER: focus intent is not browser/frontend focus",
            "UNAVAILABLE_Z_INDEX_LAYOUT: stack order is not z-index/CSS/layout runtime",
            "UNAVAILABLE_GROUP_UI: group contract is not desktop workspace or tabs UI",
            "UNAVAILABLE_PERSISTENCE: restore/resume uses no storage, memory, or trace",
            "UNAVAILABLE_PRODUCT_BEHAVIOR: projection is not frontend state store",
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "focus_intent_contracts": focus_contracts,
        "stack_order_contracts": stack_contracts,
        "window_group_contracts": group_contracts,
        "restore_contracts": restore_contracts,
        "workspace_focus_stack_projection_result": projection,
        "side_effect_proof": side_effects,
        "next_pack": P2_3_B_NEXT_PACK,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    result = P23BWorkspaceWindowSemanticsResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_3_b_depends_on_p2_3_a(result)
    assert_p2_3_b_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_3_b_result(
    result: P23BWorkspaceWindowSemanticsResult | None = None,
) -> str:
    if result is None:
        result = build_p2_3_b_workspace_window_semantics_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_3_b_depends_on_p2_3_a(
    result: P23BWorkspaceWindowSemanticsResult,
) -> None:
    if AUDIT_REPAIR_001_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-B must depend on AUDIT-REPAIR-001",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_3_A_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-B must depend on P2.3-A",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_3_A_REPORT_FILENAME not in result.p2_3_a_ref:
        _reject(
            "P2.3-B must cite P2.3-A report",
            field="p2_3_a_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not result.foundation_ref.startswith("p2_3_workspace_state_projection_seed:"):
        _reject(
            "P2.3-B foundation ref must point to P2.3-A projection seed",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_a_projection_seed_exists(
    foundation: P23AWorkspaceStateFoundationResult,
) -> None:
    seed = foundation.projection_seed
    if not seed.projection_seed_id or not seed.projection_hash:
        _reject(
            "P2.3-A projection seed is required for P2.3-B",
            field="projection_seed",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if seed.next_pack != P2_3_B_PACK_ID:
        _reject(
            "P2.3-A projection seed must hand off to P2.3-B",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_focus_intent_is_not_focus_manager(
    contract: FloatingWindowFocusIntentContract,
) -> None:
    if (
        contract.creates_focus_manager_runtime
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "focus intent must not create focus manager or runtime side effects",
            field="creates_focus_manager_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.focus_available and not contract.unavailable_reason:
        _reject(
            "unavailable focus intent requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_active_window_is_not_browser_focus(
    contract: FloatingWindowFocusIntentContract,
) -> None:
    if contract.sets_browser_focus or contract.activates_frontend_component:
        _reject(
            "active window candidate must not set browser focus or activate frontend",
            field="sets_browser_focus",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_stack_order_is_not_z_index_runtime(
    contract: FloatingWindowStackOrderContract,
) -> None:
    if (
        contract.creates_z_index_runtime
        or contract.creates_css
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "stack order must not create z-index/CSS/runtime side effects",
            field="creates_z_index_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if contract.active_window_id not in contract.ordered_window_ids:
        _reject(
            "active window must be present in ordered stack",
            field="active_window_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_layer_order_is_not_layout_engine(
    contract: FloatingWindowStackOrderContract,
) -> None:
    if contract.creates_layout_engine:
        _reject(
            "layer order hint must not create layout engine",
            field="creates_layout_engine",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_group_is_not_desktop_workspace_ui(
    contract: FloatingWindowGroupContract,
) -> None:
    if (
        contract.creates_desktop_workspace
        or contract.creates_frontend_group_ui
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "window group must not create desktop/frontend group UI or side effects",
            field="creates_desktop_workspace",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.group_available and not contract.unavailable_reason:
        _reject(
            "unavailable group requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_group_is_not_frontend_tabs(contract: FloatingWindowGroupContract) -> None:
    if contract.creates_tab_ui:
        _reject(
            "window group must not create tabs UI",
            field="creates_tab_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if contract.primary_window_id not in contract.window_ids:
        _reject(
            "primary window must be present in group",
            field="primary_window_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_restore_is_not_persistence(contract: FloatingWindowRestoreContract) -> None:
    if (
        contract.uses_local_storage
        or contract.uses_browser_storage
        or contract.mutates_runtime
        or contract.executes_routes
    ):
        _reject(
            "restore contract must not use persistence, storage, runtime, or routes",
            field="uses_local_storage",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.restore_available and not contract.unavailable_reason:
        _reject(
            "unavailable restore requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_resume_state_is_not_memory_write(
    contract: FloatingWindowRestoreContract,
) -> None:
    if contract.writes_memory or contract.writes_trace:
        _reject(
            "resume state must not write memory or trace",
            field="writes_memory",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_restore_does_not_use_local_storage(
    contract: FloatingWindowRestoreContract,
) -> None:
    if contract.uses_local_storage:
        _reject(
            "restore contract must not use local storage",
            field="uses_local_storage",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_restore_does_not_use_browser_storage(
    contract: FloatingWindowRestoreContract,
) -> None:
    if contract.uses_browser_storage:
        _reject(
            "restore contract must not use browser storage",
            field="uses_browser_storage",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_result_is_not_frontend_state_store(
    projection: WorkspaceFocusStackProjectionResult,
) -> None:
    if projection.is_frontend_state_store:
        _reject(
            "workspace focus/stack projection must not be frontend state store",
            field="is_frontend_state_store",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_result_is_not_product_behavior(
    projection: WorkspaceFocusStackProjectionResult,
) -> None:
    if projection.is_product_behavior:
        _reject(
            "workspace focus/stack projection must not be product behavior",
            field="is_product_behavior",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_b_does_not_start_p2_3_c(
    projection: WorkspaceFocusStackProjectionResult,
) -> None:
    if projection.starts_p2_3_c:
        _reject(
            "P2.3-B projection must not start P2.3-C",
            field="starts_p2_3_c",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_b_does_not_start_p2_10(
    projection: WorkspaceFocusStackProjectionResult,
) -> None:
    if projection.starts_p2_10:
        _reject(
            "P2.3-B projection must not start P2.10",
            field="starts_p2_10",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_b_does_not_start_p2_13(
    projection: WorkspaceFocusStackProjectionResult,
) -> None:
    if projection.starts_p2_13:
        _reject(
            "P2.3-B projection must not start P2.13",
            field="starts_p2_13",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_b_side_effects_all_false(proof: P23BSideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                "P2.3-B side-effect proof fields must all be false",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )

