"""P2.3-C cross-surface window handoff / docking / conflict semantics.

Contract-only cross-surface workspace-window semantics over the P2.3-A
workspace foundation and P2.3-B focus/stack projection. This module defines
deterministic handoff, docking, conflict, compatibility, and projection read
models; it does not create UI, browser/Tauri apps, route runtime, drag/drop,
docking UI, layout engines, conflict resolvers, permission enforcement,
storage, memory/trace writes, product behavior, or runtime mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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
    FloatingWindowIdentityContract,
    FloatingWindowKind,
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
from .workspace_window_semantics import (
    P2_3_B_PACK_ID,
    P2_3_B_REPORT_FILENAME,
    P2_3_B_REPORT_PATH,
    P23BWorkspaceWindowSemanticsResult,
    WorkspaceFocusStackProjectionResult,
    build_p2_3_b_workspace_window_semantics_result,
)

P2_3_C_PACK_ID = "P2.3-C"
P2_3_C_PACK_NAME = "Cross-Surface Window Handoff / Conflict / Docking Semantics"
P2_3_C_SECTION_ID = P2_3_SECTION_ID
P2_3_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.3.11",
    "P2.3.12",
    "P2.3.13",
    "P2.3.14",
    "P2.3.15",
)
P2_3_C_DEPENDENCY_PACKS: tuple[str, ...] = (
    AUDIT_REPAIR_001_PACK_ID,
    P2_3_A_PACK_ID,
    P2_3_B_PACK_ID,
)
P2_3_C_NEXT_PACK = "P2.3-D"
P2_3_C_REPORT_FILENAME = "P2_3_C_WORKSPACE_WINDOW_CROSS_SURFACE.md"
P2_3_C_REPORT_PATH = f"agent/reports/{P2_3_C_REPORT_FILENAME}"
P2_3_C_RESULT_VERSION = "p2_3_c_window_cross_surface_semantics_result.v1"
P2_3_HANDOFF_VERSION = "p2_3_c_cross_surface_window_handoff_contract.v1"
P2_3_DOCKING_VERSION = "p2_3_c_window_docking_intent_contract.v1"
P2_3_CONFLICT_VERSION = "p2_3_c_window_conflict_contract.v1"
P2_3_COMPATIBILITY_VERSION = "p2_3_c_window_surface_compatibility_contract.v1"
P2_3_CROSS_SURFACE_PROJECTION_VERSION = "p2_3_c_cross_surface_window_projection.v1"

_HANDOFF_NON_GOALS: tuple[str, ...] = (
    "no_route_execution",
    "no_real_surface_switch",
    "no_frontend_window_movement",
    "no_cross_surface_runtime",
)
_DOCKING_NON_GOALS: tuple[str, ...] = (
    "no_docking_ui",
    "no_drag_drop",
    "no_real_layout_change",
    "no_runtime_docking_behavior",
)
_CONFLICT_NON_GOALS: tuple[str, ...] = (
    "no_conflict_resolver_runtime",
    "no_real_collision_detection",
    "no_layout_engine",
    "no_automatic_resolution",
)
_COMPATIBILITY_NON_GOALS: tuple[str, ...] = (
    "no_permission_enforcement",
    "no_permission_grant",
    "no_permission_denial",
    "no_runtime_block",
    "no_custos_integration",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_frontend_state_store",
    "no_product_behavior",
    "no_p2_3_d_implementation",
    "no_p2_10_implementation",
    "no_p2_13_implementation",
)


class CrossSurfaceWindowHandoffIntent(str, Enum):
    HANDOFF_REQUESTED = "HANDOFF_REQUESTED"
    HANDOFF_REPRESENTED = "HANDOFF_REPRESENTED"
    HANDOFF_DEFERRED = "HANDOFF_DEFERRED"
    HANDOFF_UNAVAILABLE = "HANDOFF_UNAVAILABLE"


class CrossSurfaceWindowHandoffReason(str, Enum):
    SURFACE_CONTEXT_TRANSFER = "SURFACE_CONTEXT_TRANSFER"
    OPERATOR_INTENT_TRANSFER = "OPERATOR_INTENT_TRANSFER"
    RESTORE_TARGET_TRANSFER = "RESTORE_TARGET_TRANSFER"
    GROUP_CONTEXT_TRANSFER = "GROUP_CONTEXT_TRANSFER"
    UNAVAILABLE_HANDOFF = "UNAVAILABLE_HANDOFF"


class CrossSurfaceWindowHandoffTruthBoundary(str, Enum):
    CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT = "CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT"
    DECLARATIVE_HANDOFF_ONLY = "DECLARATIVE_HANDOFF_ONLY"
    NOT_ROUTE_RUNTIME = "NOT_ROUTE_RUNTIME"
    NOT_SURFACE_SWITCH_RUNTIME = "NOT_SURFACE_SWITCH_RUNTIME"


class WindowDockingMode(str, Enum):
    DOCK_REQUESTED = "DOCK_REQUESTED"
    UNDOCK_REQUESTED = "UNDOCK_REQUESTED"
    DOCK_REPRESENTED = "DOCK_REPRESENTED"
    UNDOCK_REPRESENTED = "UNDOCK_REPRESENTED"
    DOCK_UNAVAILABLE = "DOCK_UNAVAILABLE"
    DOCK_DEFERRED = "DOCK_DEFERRED"


class WindowDockingRegion(str, Enum):
    SURFACE_LEFT = "SURFACE_LEFT"
    SURFACE_RIGHT = "SURFACE_RIGHT"
    SURFACE_TOP = "SURFACE_TOP"
    SURFACE_BOTTOM = "SURFACE_BOTTOM"
    FLOATING_REGION = "FLOATING_REGION"
    UNDOCKED_REGION = "UNDOCKED_REGION"


class WindowDockingTruthBoundary(str, Enum):
    WINDOW_DOCKING_INTENT_CONTRACT = "WINDOW_DOCKING_INTENT_CONTRACT"
    DECLARATIVE_DOCKING_ONLY = "DECLARATIVE_DOCKING_ONLY"
    NOT_DOCKING_UI = "NOT_DOCKING_UI"
    NOT_DRAG_DROP = "NOT_DRAG_DROP"


class WindowConflictKind(str, Enum):
    PLACEMENT_CONFLICT = "PLACEMENT_CONFLICT"
    SURFACE_INCOMPATIBILITY = "SURFACE_INCOMPATIBILITY"
    WINDOW_GROUP_CONFLICT = "WINDOW_GROUP_CONFLICT"
    FOCUS_CONFLICT = "FOCUS_CONFLICT"
    STACK_ORDER_CONFLICT = "STACK_ORDER_CONFLICT"
    DOCKING_CONFLICT = "DOCKING_CONFLICT"
    RESTORE_CONFLICT = "RESTORE_CONFLICT"


class WindowConflictSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKED_CONTRACT = "BLOCKED_CONTRACT"
    DEFERRED_REVIEW = "DEFERRED_REVIEW"
    UNAVAILABLE = "UNAVAILABLE"


class WindowConflictTruthBoundary(str, Enum):
    WINDOW_CONFLICT_CONTRACT = "WINDOW_CONFLICT_CONTRACT"
    DECLARATIVE_CONFLICT_STATE_ONLY = "DECLARATIVE_CONFLICT_STATE_ONLY"
    NOT_CONFLICT_RESOLVER_RUNTIME = "NOT_CONFLICT_RESOLVER_RUNTIME"
    NOT_LAYOUT_ENGINE = "NOT_LAYOUT_ENGINE"


class WindowCompatibilityKind(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    REQUIRES_OPERATOR_REVIEW = "REQUIRES_OPERATOR_REVIEW"
    REQUIRES_FUTURE_PERMISSION_CHECK = "REQUIRES_FUTURE_PERMISSION_CHECK"
    UNAVAILABLE = "UNAVAILABLE"
    DEFERRED = "DEFERRED"


class WindowCompatibilityTruthBoundary(str, Enum):
    WINDOW_SURFACE_COMPATIBILITY_CONTRACT = "WINDOW_SURFACE_COMPATIBILITY_CONTRACT"
    CONTRACT_COMPATIBILITY_ONLY = "CONTRACT_COMPATIBILITY_ONLY"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_CUSTOS_INTEGRATION = "NOT_CUSTOS_INTEGRATION"


class CrossSurfaceWindowProjectionTruthBoundary(str, Enum):
    CROSS_SURFACE_WINDOW_PROJECTION_RESULT = "CROSS_SURFACE_WINDOW_PROJECTION_RESULT"
    DEV_FIXTURE = "DEV_FIXTURE"
    READ_MODEL_RESULT_ONLY = "READ_MODEL_RESULT_ONLY"
    NOT_FRONTEND_STATE_STORE = "NOT_FRONTEND_STATE_STORE"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"


@dataclass(frozen=True)
class P23CSideEffectProof(_CanonicalMixin):
    frontend_ui_created: bool = False
    browser_app_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    frontend_window_moved: bool = False
    surface_runtime_switched: bool = False
    route_runtime_created: bool = False
    routes_executed: bool = False
    drag_drop_created: bool = False
    docking_ui_created: bool = False
    undocking_ui_created: bool = False
    layout_engine_created: bool = False
    css_created: bool = False
    real_layout_changed: bool = False
    conflict_resolver_created: bool = False
    real_collision_detected: bool = False
    automatic_conflict_resolution_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    custos_integration_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    local_storage_written: bool = False
    browser_storage_written: bool = False
    memory_written: bool = False
    trace_written: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_3_d_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class CrossSurfaceWindowHandoffContract(_CanonicalMixin):
    handoff_id: str
    schema_version: str
    window_id: str
    source_surface_id: str
    target_surface_id: str
    workspace_state_id: str
    handoff_intent: CrossSurfaceWindowHandoffIntent
    handoff_reason: CrossSurfaceWindowHandoffReason
    handoff_payload_refs: tuple[str, ...]
    handoff_available: bool
    unavailable_reason: str
    executes_route: bool
    switches_surface_runtime: bool
    moves_frontend_window: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class WindowDockingIntentContract(_CanonicalMixin):
    docking_id: str
    schema_version: str
    window_id: str
    workspace_state_id: str
    dock_target_surface_id: str
    dock_region: WindowDockingRegion
    docking_mode: WindowDockingMode
    docking_reason: str
    dock_available: bool
    unavailable_reason: str
    creates_docking_ui: bool
    executes_drag_drop: bool
    changes_real_layout: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class WindowConflictContract(_CanonicalMixin):
    conflict_id: str
    schema_version: str
    workspace_state_id: str
    window_ids: tuple[str, ...]
    conflict_kind: WindowConflictKind
    conflict_reason: str
    severity: WindowConflictSeverity
    suggested_resolution_intent: str
    conflict_available: bool
    unavailable_reason: str
    detects_real_collision: bool
    resolves_conflict_runtime: bool
    changes_layout: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class WindowSurfaceCompatibilityContract(_CanonicalMixin):
    compatibility_id: str
    schema_version: str
    window_kind: FloatingWindowKind
    source_surface_id: str
    target_surface_id: str
    allowed_as_contract: bool
    compatibility_kind: WindowCompatibilityKind
    compatibility_reason: str
    requires_operator_review: bool
    requires_permission_check_later: bool
    enforces_permission: bool
    grants_permission: bool
    denies_permission: bool
    blocks_runtime: bool
    mutates_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class CrossSurfaceWindowProjectionResult(_CanonicalMixin):
    projection_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    foundation_ref: str
    semantics_ref: str
    handoff_contracts: tuple[CrossSurfaceWindowHandoffContract, ...]
    docking_intent_contracts: tuple[WindowDockingIntentContract, ...]
    conflict_contracts: tuple[WindowConflictContract, ...]
    compatibility_contracts: tuple[WindowSurfaceCompatibilityContract, ...]
    side_effect_proof: P23CSideEffectProof
    next_pack: str
    truth_label: str
    is_frontend_state_store: bool
    is_product_behavior: bool
    starts_p2_3_d: bool
    starts_p2_10: bool
    starts_p2_13: bool
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P23CWindowCrossSurfaceSemanticsResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    audit_repair_ref: str
    p2_3_a_ref: str
    p2_3_b_ref: str
    foundation_ref: str
    semantics_ref: str
    checkpoint_reads: tuple[P23CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    handoff_contracts: tuple[CrossSurfaceWindowHandoffContract, ...]
    docking_intent_contracts: tuple[WindowDockingIntentContract, ...]
    conflict_contracts: tuple[WindowConflictContract, ...]
    compatibility_contracts: tuple[WindowSurfaceCompatibilityContract, ...]
    cross_surface_window_projection_result: CrossSurfaceWindowProjectionResult
    side_effect_proof: P23CSideEffectProof
    next_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def _foundation_ref(foundation: P23AWorkspaceStateFoundationResult) -> str:
    seed = foundation.projection_seed
    return f"{seed.projection_seed_id}:{seed.projection_hash}"


def _semantics_ref(semantics: P23BWorkspaceWindowSemanticsResult) -> str:
    projection = semantics.workspace_focus_stack_projection_result
    return f"{projection.projection_id}:{projection.projection_hash}"


def _window_ids(foundation: P23AWorkspaceStateFoundationResult) -> tuple[str, ...]:
    return tuple(contract.window_id for contract in foundation.identity_contracts)


def _workspace_state_id(foundation: P23AWorkspaceStateFoundationResult) -> str:
    return foundation.workspace_state.workspace_state_id


def _identity_by_window_id(
    foundation: P23AWorkspaceStateFoundationResult,
    window_id: str,
) -> FloatingWindowIdentityContract:
    for contract in foundation.identity_contracts:
        if contract.window_id == window_id:
            return contract
    _reject(
        "window id must come from P2.3-A identity contracts",
        field="window_id",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable after validation rejection")


def _validate_surface_id(surface_id: str, *, field: str) -> None:
    if surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            "surface id must use canonical P2 surface registry",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def build_p2_3_c_side_effect_proof() -> P23CSideEffectProof:
    return P23CSideEffectProof()


def build_cross_surface_window_handoff_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    window_id: str | None = None,
    source_surface_id: str | None = None,
    target_surface_id: str | None = None,
    handoff_intent: CrossSurfaceWindowHandoffIntent = (
        CrossSurfaceWindowHandoffIntent.HANDOFF_REPRESENTED
    ),
    handoff_reason: CrossSurfaceWindowHandoffReason = (
        CrossSurfaceWindowHandoffReason.SURFACE_CONTEXT_TRANSFER
    ),
    handoff_payload_refs: tuple[str, ...] | None = None,
    handoff_available: bool = True,
    unavailable_reason: str = "",
) -> CrossSurfaceWindowHandoffContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    assert_p2_3_a_foundation_exists(foundation)
    if window_id is None:
        window_id = _window_ids(foundation)[0]
    identity = _identity_by_window_id(foundation, window_id)
    if source_surface_id is None:
        source_surface_id = identity.source_surface_id
    if target_surface_id is None:
        target_surface_id = identity.target_surface_id
    _validate_surface_id(source_surface_id, field="source_surface_id")
    _validate_surface_id(target_surface_id, field="target_surface_id")
    if handoff_payload_refs is None:
        handoff_payload_refs = (identity.content_ref, identity.context_ref)
    if not handoff_available and not unavailable_reason:
        unavailable_reason = "UNAVAILABLE_HANDOFF: handoff unavailable by contract"
    payload = {
        "handoff_id": f"p2_3_c_handoff_{window_id}_{target_surface_id}",
        "schema_version": P2_3_HANDOFF_VERSION,
        "window_id": window_id,
        "source_surface_id": source_surface_id,
        "target_surface_id": target_surface_id,
        "workspace_state_id": _workspace_state_id(foundation),
        "handoff_intent": handoff_intent,
        "handoff_reason": handoff_reason,
        "handoff_payload_refs": handoff_payload_refs,
        "handoff_available": handoff_available,
        "unavailable_reason": unavailable_reason,
        "executes_route": False,
        "switches_surface_runtime": False,
        "moves_frontend_window": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": (
            CrossSurfaceWindowHandoffTruthBoundary.CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT.value
        ),
        "non_goals": _HANDOFF_NON_GOALS,
    }
    contract = CrossSurfaceWindowHandoffContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_window_handoff_is_not_route_runtime(contract)
    assert_window_handoff_does_not_switch_surface_runtime(contract)
    assert_window_handoff_does_not_move_frontend_window(contract)
    return contract


def build_cross_surface_window_handoff_contracts(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
) -> tuple[CrossSurfaceWindowHandoffContract, ...]:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    return tuple(
        build_cross_surface_window_handoff_contract(
            foundation=foundation,
            window_id=contract.window_id,
        )
        for contract in foundation.identity_contracts
    )


def build_window_docking_intent_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    window_id: str | None = None,
    dock_target_surface_id: str | None = None,
    dock_region: WindowDockingRegion = WindowDockingRegion.SURFACE_RIGHT,
    docking_mode: WindowDockingMode = WindowDockingMode.DOCK_REPRESENTED,
    docking_reason: str = "P2.3-C declarative docking grammar over P2.3-A window",
    dock_available: bool = True,
    unavailable_reason: str = "",
) -> WindowDockingIntentContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    if window_id is None:
        window_id = _window_ids(foundation)[0]
    identity = _identity_by_window_id(foundation, window_id)
    if dock_target_surface_id is None:
        dock_target_surface_id = identity.owner_surface_id
    _validate_surface_id(dock_target_surface_id, field="dock_target_surface_id")
    if not dock_available and not unavailable_reason:
        unavailable_reason = "UNAVAILABLE_DOCKING: docking unavailable by contract"
    payload = {
        "docking_id": f"p2_3_c_docking_{window_id}_{dock_target_surface_id}",
        "schema_version": P2_3_DOCKING_VERSION,
        "window_id": window_id,
        "workspace_state_id": _workspace_state_id(foundation),
        "dock_target_surface_id": dock_target_surface_id,
        "dock_region": dock_region,
        "docking_mode": docking_mode,
        "docking_reason": docking_reason,
        "dock_available": dock_available,
        "unavailable_reason": unavailable_reason,
        "creates_docking_ui": False,
        "executes_drag_drop": False,
        "changes_real_layout": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": WindowDockingTruthBoundary.WINDOW_DOCKING_INTENT_CONTRACT.value,
        "non_goals": _DOCKING_NON_GOALS,
    }
    contract = WindowDockingIntentContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_docking_intent_is_not_docking_ui(contract)
    assert_undocking_intent_is_not_drag_drop(contract)
    return contract


def build_window_conflict_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    window_ids: tuple[str, ...] | None = None,
    conflict_kind: WindowConflictKind = WindowConflictKind.PLACEMENT_CONFLICT,
    conflict_reason: str = "P2.3-C declarative conflict state over window refs",
    severity: WindowConflictSeverity = WindowConflictSeverity.WARNING,
    suggested_resolution_intent: str = "operator_review_or_future_p2_3_d_tail",
    conflict_available: bool = True,
    unavailable_reason: str = "",
) -> WindowConflictContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    known_window_ids = _window_ids(foundation)
    if window_ids is None:
        window_ids = known_window_ids[:2]
    if not window_ids:
        _reject(
            "window conflict requires at least one window id",
            field="window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if any(window_id not in known_window_ids for window_id in window_ids):
        _reject(
            "window conflict ids must come from P2.3-A identity contracts",
            field="window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not conflict_available and not unavailable_reason:
        unavailable_reason = "UNAVAILABLE_CONFLICT: conflict unavailable by contract"
    payload = {
        "conflict_id": f"p2_3_c_conflict_{conflict_kind.value.lower()}",
        "schema_version": P2_3_CONFLICT_VERSION,
        "workspace_state_id": _workspace_state_id(foundation),
        "window_ids": window_ids,
        "conflict_kind": conflict_kind,
        "conflict_reason": conflict_reason,
        "severity": severity,
        "suggested_resolution_intent": suggested_resolution_intent,
        "conflict_available": conflict_available,
        "unavailable_reason": unavailable_reason,
        "detects_real_collision": False,
        "resolves_conflict_runtime": False,
        "changes_layout": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": WindowConflictTruthBoundary.WINDOW_CONFLICT_CONTRACT.value,
        "non_goals": _CONFLICT_NON_GOALS,
    }
    contract = WindowConflictContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_conflict_state_is_not_conflict_resolver_runtime(contract)
    assert_collision_contract_is_not_layout_engine(contract)
    return contract


def build_window_surface_compatibility_contract(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    window_id: str | None = None,
    window_kind: FloatingWindowKind | None = None,
    source_surface_id: str | None = None,
    target_surface_id: str | None = None,
    allowed_as_contract: bool = True,
    compatibility_kind: WindowCompatibilityKind = WindowCompatibilityKind.COMPATIBLE,
    compatibility_reason: str = (
        "P2.3-C contract-level compatibility only; no permission decision"
    ),
    requires_operator_review: bool = False,
    requires_permission_check_later: bool = False,
) -> WindowSurfaceCompatibilityContract:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    if window_id is None:
        window_id = _window_ids(foundation)[0]
    identity = _identity_by_window_id(foundation, window_id)
    if window_kind is None:
        window_kind = identity.window_kind
    if source_surface_id is None:
        source_surface_id = identity.source_surface_id
    if target_surface_id is None:
        target_surface_id = identity.target_surface_id
    _validate_surface_id(source_surface_id, field="source_surface_id")
    _validate_surface_id(target_surface_id, field="target_surface_id")
    payload = {
        "compatibility_id": (
            f"p2_3_c_compatibility_{window_kind.value.lower()}_{target_surface_id}"
        ),
        "schema_version": P2_3_COMPATIBILITY_VERSION,
        "window_kind": window_kind,
        "source_surface_id": source_surface_id,
        "target_surface_id": target_surface_id,
        "allowed_as_contract": allowed_as_contract,
        "compatibility_kind": compatibility_kind,
        "compatibility_reason": compatibility_reason,
        "requires_operator_review": requires_operator_review,
        "requires_permission_check_later": requires_permission_check_later,
        "enforces_permission": False,
        "grants_permission": False,
        "denies_permission": False,
        "blocks_runtime": False,
        "mutates_runtime": False,
        "truth_label": (
            WindowCompatibilityTruthBoundary.WINDOW_SURFACE_COMPATIBILITY_CONTRACT.value
        ),
        "non_goals": _COMPATIBILITY_NON_GOALS,
    }
    contract = WindowSurfaceCompatibilityContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_compatibility_is_not_permission_enforcement(contract)
    assert_compatibility_does_not_grant_permission(contract)
    assert_compatibility_does_not_deny_permission(contract)
    return contract


def build_cross_surface_window_projection_result(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    semantics: P23BWorkspaceWindowSemanticsResult | None = None,
    handoff_contracts: tuple[CrossSurfaceWindowHandoffContract, ...] | None = None,
    docking_intent_contracts: tuple[WindowDockingIntentContract, ...] | None = None,
    conflict_contracts: tuple[WindowConflictContract, ...] | None = None,
    compatibility_contracts: tuple[WindowSurfaceCompatibilityContract, ...] | None = None,
    side_effect_proof: P23CSideEffectProof | None = None,
) -> CrossSurfaceWindowProjectionResult:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    if semantics is None:
        semantics = build_p2_3_b_workspace_window_semantics_result()
    assert_p2_3_a_foundation_exists(foundation)
    assert_p2_3_b_projection_result_exists(semantics)
    if handoff_contracts is None:
        handoff_contracts = build_cross_surface_window_handoff_contracts(
            foundation=foundation
        )
    if docking_intent_contracts is None:
        docking_intent_contracts = (
            build_window_docking_intent_contract(foundation=foundation),
        )
    if conflict_contracts is None:
        conflict_contracts = (build_window_conflict_contract(foundation=foundation),)
    if compatibility_contracts is None:
        compatibility_contracts = (
            build_window_surface_compatibility_contract(foundation=foundation),
        )
    if side_effect_proof is None:
        side_effect_proof = build_p2_3_c_side_effect_proof()
    payload = {
        "projection_id": "p2_3_c_cross_surface_window_projection",
        "schema_version": P2_3_CROSS_SURFACE_PROJECTION_VERSION,
        "section_id": P2_3_C_SECTION_ID,
        "created_for_pack": P2_3_C_PACK_ID,
        "foundation_ref": _foundation_ref(foundation),
        "semantics_ref": _semantics_ref(semantics),
        "handoff_contracts": handoff_contracts,
        "docking_intent_contracts": docking_intent_contracts,
        "conflict_contracts": conflict_contracts,
        "compatibility_contracts": compatibility_contracts,
        "side_effect_proof": side_effect_proof,
        "next_pack": P2_3_C_NEXT_PACK,
        "truth_label": (
            CrossSurfaceWindowProjectionTruthBoundary.CROSS_SURFACE_WINDOW_PROJECTION_RESULT.value
        ),
        "is_frontend_state_store": False,
        "is_product_behavior": False,
        "starts_p2_3_d": False,
        "starts_p2_10": False,
        "starts_p2_13": False,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = CrossSurfaceWindowProjectionResult(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_result_is_not_frontend_state_store(projection)
    assert_projection_result_is_not_product_behavior(projection)
    assert_p2_3_c_does_not_start_p2_3_d(projection)
    assert_p2_3_c_does_not_start_p2_10(projection)
    assert_p2_3_c_does_not_start_p2_13(projection)
    assert_p2_3_c_side_effects_all_false(projection.side_effect_proof)
    return projection


def _checkpoint_reads() -> tuple[P23CheckpointRead, ...]:
    rows = {
        "P2.3.11": (
            "Cross-Surface Window Handoff Contract",
            "CrossSurfaceWindowHandoffContract",
            "test_p2_3_11_*",
            "CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT / NOT_ROUTE_RUNTIME",
            "route/surface-switch runtime unavailable by contract",
            "Declarative handoff only; no route execution or frontend movement",
        ),
        "P2.3.12": (
            "Window Docking / Undocking Intent Contract",
            "WindowDockingIntentContract",
            "test_p2_3_12_*",
            "WINDOW_DOCKING_INTENT_CONTRACT / NOT_DOCKING_UI",
            "docking UI and drag/drop unavailable by contract",
            "Intent grammar only; no docking UI, drag/drop, or layout change",
        ),
        "P2.3.13": (
            "Window Conflict / Collision Contract",
            "WindowConflictContract",
            "test_p2_3_13_*",
            "WINDOW_CONFLICT_CONTRACT / NOT_CONFLICT_RESOLVER_RUNTIME",
            "conflict resolver and real collision detection unavailable by contract",
            "Declarative conflict evidence only; no resolver or layout engine",
        ),
        "P2.3.14": (
            "Window Constraint / Compatibility Contract",
            "WindowSurfaceCompatibilityContract",
            "test_p2_3_14_*",
            "WINDOW_SURFACE_COMPATIBILITY_CONTRACT / NOT_PERMISSION_ENFORCEMENT",
            "permission enforcement and Custos integration unavailable by contract",
            "Compatibility only; no permission grant, denial, or runtime block",
        ),
        "P2.3.15": (
            "Cross-Surface Window Projection Result",
            "CrossSurfaceWindowProjectionResult",
            "test_p2_3_15_*",
            "CROSS_SURFACE_WINDOW_PROJECTION_RESULT / NOT_PRODUCT_BEHAVIOR",
            "frontend/product behavior unavailable by contract",
            "Bundles P2.3-C semantics over P2.3-A/B projections only",
        ),
    }
    reads: list[P23CheckpointRead] = []
    for checkpoint_id in P2_3_C_PACK_CHECKPOINT_IDS:
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


def build_p2_3_c_window_cross_surface_semantics_result() -> (
    P23CWindowCrossSurfaceSemanticsResult
):
    foundation = build_p2_3_a_workspace_state_foundation_result()
    semantics = build_p2_3_b_workspace_window_semantics_result()
    assert_p2_3_a_foundation_exists(foundation)
    assert_p2_3_b_projection_result_exists(semantics)
    handoffs = build_cross_surface_window_handoff_contracts(foundation=foundation)
    dockings = (build_window_docking_intent_contract(foundation=foundation),)
    conflicts = (build_window_conflict_contract(foundation=foundation),)
    compatibilities = (
        build_window_surface_compatibility_contract(foundation=foundation),
    )
    side_effects = build_p2_3_c_side_effect_proof()
    projection = build_cross_surface_window_projection_result(
        foundation=foundation,
        semantics=semantics,
        handoff_contracts=handoffs,
        docking_intent_contracts=dockings,
        conflict_contracts=conflicts,
        compatibility_contracts=compatibilities,
        side_effect_proof=side_effects,
    )
    drift, drift_details = detect_surface_taxonomy_drift()
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    payload = {
        "schema_version": P2_3_C_RESULT_VERSION,
        "pack_id": P2_3_C_PACK_ID,
        "section_id": P2_3_C_SECTION_ID,
        "section_name": P2_3_SECTION_NAME,
        "covered_checkpoints": P2_3_C_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_3_C_DEPENDENCY_PACKS,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "audit_repair_ref": (
            f"agent/reports/{AUDIT_REPAIR_001_REPORT_FILENAME}:"
            f"{AUDIT_REPAIR_001_PACK_ID}"
        ),
        "p2_3_a_ref": f"{P2_3_A_REPORT_PATH}:{P2_3_A_PACK_ID}",
        "p2_3_b_ref": f"{P2_3_B_REPORT_PATH}:{P2_3_B_PACK_ID}",
        "foundation_ref": _foundation_ref(foundation),
        "semantics_ref": _semantics_ref(semantics),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": (
            CrossSurfaceWindowHandoffTruthBoundary.CROSS_SURFACE_WINDOW_HANDOFF_CONTRACT.value,
            WindowDockingTruthBoundary.WINDOW_DOCKING_INTENT_CONTRACT.value,
            WindowConflictTruthBoundary.WINDOW_CONFLICT_CONTRACT.value,
            WindowCompatibilityTruthBoundary.WINDOW_SURFACE_COMPATIBILITY_CONTRACT.value,
            CrossSurfaceWindowProjectionTruthBoundary.CROSS_SURFACE_WINDOW_PROJECTION_RESULT.value,
            CrossSurfaceWindowProjectionTruthBoundary.READ_MODEL_RESULT_ONLY.value,
            CrossSurfaceWindowProjectionTruthBoundary.NOT_PRODUCT_BEHAVIOR.value,
        ),
        "unavailable_reasons": (
            "UNAVAILABLE_ROUTE_RUNTIME: handoff is not route execution",
            "UNAVAILABLE_DOCKING_UI: docking intent is not drag/drop or UI",
            "UNAVAILABLE_CONFLICT_RESOLVER: conflict is not resolver runtime",
            "UNAVAILABLE_PERMISSION_ENFORCEMENT: compatibility grants no authority",
            "UNAVAILABLE_PRODUCT_BEHAVIOR: projection is not frontend state store",
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "handoff_contracts": handoffs,
        "docking_intent_contracts": dockings,
        "conflict_contracts": conflicts,
        "compatibility_contracts": compatibilities,
        "cross_surface_window_projection_result": projection,
        "side_effect_proof": side_effects,
        "next_pack": P2_3_C_NEXT_PACK,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    result = P23CWindowCrossSurfaceSemanticsResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_3_c_depends_on_p2_3_b(result)
    assert_p2_3_c_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_3_c_result(
    result: P23CWindowCrossSurfaceSemanticsResult | None = None,
) -> str:
    if result is None:
        result = build_p2_3_c_window_cross_surface_semantics_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_3_c_depends_on_p2_3_b(
    result: P23CWindowCrossSurfaceSemanticsResult,
) -> None:
    if AUDIT_REPAIR_001_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-C must depend on AUDIT-REPAIR-001",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_3_A_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-C must depend on P2.3-A",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_3_B_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-C must depend on P2.3-B",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_3_B_REPORT_FILENAME not in result.p2_3_b_ref:
        _reject(
            "P2.3-C must cite P2.3-B report",
            field="p2_3_b_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not result.semantics_ref.startswith("p2_3_b_workspace_focus_stack_projection:"):
        _reject(
            "P2.3-C semantics ref must point to P2.3-B projection result",
            field="semantics_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_a_foundation_exists(
    foundation: P23AWorkspaceStateFoundationResult,
) -> None:
    seed = foundation.projection_seed
    if not seed.projection_seed_id or not seed.projection_hash:
        _reject(
            "P2.3-A projection seed is required for P2.3-C",
            field="projection_seed",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_b_projection_result_exists(
    semantics: P23BWorkspaceWindowSemanticsResult,
) -> None:
    projection: WorkspaceFocusStackProjectionResult = (
        semantics.workspace_focus_stack_projection_result
    )
    if not projection.projection_id or not projection.projection_hash:
        _reject(
            "P2.3-B projection result is required for P2.3-C",
            field="workspace_focus_stack_projection_result",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if projection.next_pack != P2_3_C_PACK_ID:
        _reject(
            "P2.3-B projection must hand off to P2.3-C",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_window_handoff_is_not_route_runtime(
    contract: CrossSurfaceWindowHandoffContract,
) -> None:
    if (
        contract.executes_route
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "handoff contract must not execute routes or mutate runtime",
            field="executes_route",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.handoff_available and not contract.unavailable_reason:
        _reject(
            "unavailable handoff requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_window_handoff_does_not_switch_surface_runtime(
    contract: CrossSurfaceWindowHandoffContract,
) -> None:
    if contract.switches_surface_runtime:
        _reject(
            "handoff contract must not switch surfaces at runtime",
            field="switches_surface_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_window_handoff_does_not_move_frontend_window(
    contract: CrossSurfaceWindowHandoffContract,
) -> None:
    if contract.moves_frontend_window:
        _reject(
            "handoff contract must not move frontend windows",
            field="moves_frontend_window",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_docking_intent_is_not_docking_ui(
    contract: WindowDockingIntentContract,
) -> None:
    if (
        contract.creates_docking_ui
        or contract.changes_real_layout
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "docking intent must not create UI, layout, or runtime side effects",
            field="creates_docking_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.dock_available and not contract.unavailable_reason:
        _reject(
            "unavailable docking intent requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_undocking_intent_is_not_drag_drop(
    contract: WindowDockingIntentContract,
) -> None:
    if contract.executes_drag_drop:
        _reject(
            "docking/undocking intent must not execute drag/drop",
            field="executes_drag_drop",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_conflict_state_is_not_conflict_resolver_runtime(
    contract: WindowConflictContract,
) -> None:
    if (
        contract.resolves_conflict_runtime
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "conflict state must not create resolver runtime or side effects",
            field="resolves_conflict_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.conflict_available and not contract.unavailable_reason:
        _reject(
            "unavailable conflict requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not contract.window_ids:
        _reject(
            "conflict contract requires window ids",
            field="window_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_collision_contract_is_not_layout_engine(
    contract: WindowConflictContract,
) -> None:
    if contract.detects_real_collision or contract.changes_layout:
        _reject(
            "collision contract must not detect real collision or change layout",
            field="detects_real_collision",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_compatibility_is_not_permission_enforcement(
    contract: WindowSurfaceCompatibilityContract,
) -> None:
    if contract.enforces_permission or contract.blocks_runtime or contract.mutates_runtime:
        _reject(
            "compatibility contract must not enforce permission or block runtime",
            field="enforces_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_compatibility_does_not_grant_permission(
    contract: WindowSurfaceCompatibilityContract,
) -> None:
    if contract.grants_permission:
        _reject(
            "compatibility contract must not grant permission",
            field="grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_compatibility_does_not_deny_permission(
    contract: WindowSurfaceCompatibilityContract,
) -> None:
    if contract.denies_permission:
        _reject(
            "compatibility contract must not deny permission",
            field="denies_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_result_is_not_frontend_state_store(
    projection: CrossSurfaceWindowProjectionResult,
) -> None:
    if projection.is_frontend_state_store:
        _reject(
            "cross-surface projection must not be frontend state store",
            field="is_frontend_state_store",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_result_is_not_product_behavior(
    projection: CrossSurfaceWindowProjectionResult,
) -> None:
    if projection.is_product_behavior:
        _reject(
            "cross-surface projection must not be product behavior",
            field="is_product_behavior",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_c_does_not_start_p2_3_d(
    projection: CrossSurfaceWindowProjectionResult,
) -> None:
    if projection.starts_p2_3_d:
        _reject(
            "P2.3-C projection must not start P2.3-D",
            field="starts_p2_3_d",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_c_does_not_start_p2_10(
    projection: CrossSurfaceWindowProjectionResult,
) -> None:
    if projection.starts_p2_10:
        _reject(
            "P2.3-C projection must not start P2.10",
            field="starts_p2_10",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_c_does_not_start_p2_13(
    projection: CrossSurfaceWindowProjectionResult,
) -> None:
    if projection.starts_p2_13:
        _reject(
            "P2.3-C projection must not start P2.13",
            field="starts_p2_13",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_c_side_effects_all_false(proof: P23CSideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                "P2.3-C side-effect proof fields must all be false",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
