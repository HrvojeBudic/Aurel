"""AurelShell local navigation hierarchy / interaction constraints (P2.2-B / P2.2.6–P2.2.10).

Contract-only hierarchy, ordering, selection state, interaction constraints, and
hierarchy projection over the P2.2-A local navigation foundation.

Architectural law:
  - Hierarchy is structural metadata, not UI layout.
  - Ordering is deterministic contract order, not drag/drop layout.
  - Selection is read-model state, not route execution.
  - Interaction constraint is intent constraint, not click handler.
  - Protected nav is not permission enforcement.
  - Deferred nav requires target section/pack and does not mean implementation.
  - Hierarchy projection is not sidebar UI.
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
    LocalNavGroupContract,
    LocalNavItemContract,
    LocalNavProjectionSeed,
    PerSurfaceLocalNavRegistry,
    build_local_nav_item_contracts,
    build_local_nav_projection_seed,
    build_per_surface_local_nav_registries,
)
from .surface_registry import CANONICAL_SURFACE_ORDER
from .topbar import SETTINGS_SURFACE_ID, SYSTEM_SURFACE_ID

P2_2_B_PACK_ID = "P2.2-B"
P2_2_B_PACK_NAME = "Local Navigation Hierarchy / Interaction Constraints"
P2_2_B_SECTION_ID = "P2.2"
P2_2_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.2.6",
    "P2.2.7",
    "P2.2.8",
    "P2.2.9",
    "P2.2.10",
)
P2_2_B_DEPENDENCY_PACKS: tuple[str, ...] = (P2_2_A_PACK_ID,)
P2_2_B_NEXT_PACK = "P2.2-C"
P2_2_B_REPORT_FILENAME = "P2_2_B_LOCAL_NAVIGATION_HIERARCHY.md"
P2_2_B_REPORT_PATH = f"agent/reports/{P2_2_B_REPORT_FILENAME}"
P2_2_B_RESULT_VERSION = "p2_2_b_local_navigation_hierarchy_result.v1"
LOCAL_NAV_HIERARCHY_VERSION = "local_nav_hierarchy_contract.v1"
LOCAL_NAV_HIERARCHY_EDGE_VERSION = "local_nav_hierarchy_edge.v1"
LOCAL_NAV_ORDERING_VERSION = "local_nav_ordering_contract.v1"
LOCAL_NAV_ORDERING_RULE_VERSION = "local_nav_ordering_rule.v1"
LOCAL_NAV_SELECTION_VERSION = "local_nav_selection_state.v1"
LOCAL_NAV_INTERACTION_VERSION = "local_nav_interaction_constraint.v1"
LOCAL_NAV_HIERARCHY_PROJECTION_VERSION = "local_nav_hierarchy_projection.v1"

_HIERARCHY_NON_GOALS: tuple[str, ...] = (
    "no_visual_tree",
    "no_sidebar_rendering",
    "no_global_left_nav",
    "no_route_runtime",
)
_ORDERING_NON_GOALS: tuple[str, ...] = (
    "no_drag_drop",
    "no_layout_engine",
    "no_ui_persistence",
    "no_runtime_mutation",
)
_SELECTION_NON_GOALS: tuple[str, ...] = (
    "no_actual_active_route",
    "no_url_mutation",
    "no_runtime_state_mutation",
    "no_click_handler",
)
_INTERACTION_NON_GOALS: tuple[str, ...] = (
    "no_click_handler",
    "no_keyboard_shortcut",
    "no_command_palette_action",
    "no_permission_grant",
    "no_permission_enforcement",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_visual_nav",
    "no_route_execution",
    "no_click_handlers",
    "no_p2_2_c_implementation",
    "no_p2_3_implementation",
)

_EnumT = TypeVar("_EnumT", bound=Enum)


class P22BTruthLabel(str, Enum):
    LOCAL_NAV_HIERARCHY_CONTRACT = "LOCAL_NAV_HIERARCHY_CONTRACT"
    STRUCTURAL_METADATA_ONLY = "STRUCTURAL_METADATA_ONLY"
    NOT_UI = "NOT_UI"
    NOT_ROUTE_RUNTIME = "NOT_ROUTE_RUNTIME"
    ORDERING_CONTRACT = "ORDERING_CONTRACT"
    STABLE_ORDER_ONLY = "STABLE_ORDER_ONLY"
    NOT_LAYOUT_ENGINE = "NOT_LAYOUT_ENGINE"
    NOT_UI_PERSISTENCE = "NOT_UI_PERSISTENCE"
    SELECTION_STATE_CONTRACT = "SELECTION_STATE_CONTRACT"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    INTERACTION_CONSTRAINT_ONLY = "INTERACTION_CONSTRAINT_ONLY"
    INTENT_ONLY = "INTENT_ONLY"
    NOT_CLICK_HANDLER = "NOT_CLICK_HANDLER"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    HIERARCHY_PROJECTION = "HIERARCHY_PROJECTION"
    NOT_P2_2_C = "NOT_P2_2_C"
    NOT_P2_3 = "NOT_P2_3"


class LocalNavHierarchyNodeKind(str, Enum):
    ROOT = "ROOT"
    GROUP = "GROUP"
    ITEM = "ITEM"


class LocalNavSelectionSource(str, Enum):
    DEFAULT = "DEFAULT"
    RESTORED_READ_MODEL = "RESTORED_READ_MODEL"
    OPERATOR_INTENT_CONTRACT = "OPERATOR_INTENT_CONTRACT"
    UNAVAILABLE_FALLBACK = "UNAVAILABLE_FALLBACK"
    PROTECTED_FALLBACK = "PROTECTED_FALLBACK"


class LocalNavInteractionKind(str, Enum):
    SELECT_ITEM_INTENT = "SELECT_ITEM_INTENT"
    EXPAND_GROUP_INTENT = "EXPAND_GROUP_INTENT"
    COLLAPSE_GROUP_INTENT = "COLLAPSE_GROUP_INTENT"
    SHOW_ITEM_INFO = "SHOW_ITEM_INFO"
    SHOW_UNAVAILABLE_REASON = "SHOW_UNAVAILABLE_REASON"
    SHOW_PROTECTED_REASON = "SHOW_PROTECTED_REASON"
    SHOW_DEFERRED_REASON = "SHOW_DEFERRED_REASON"


class LocalNavInteractionDisposition(str, Enum):
    ALLOWED_AS_INTENT = "ALLOWED_AS_INTENT"
    BLOCKED_WITH_REASON = "BLOCKED_WITH_REASON"
    PROTECTED_INTENT = "PROTECTED_INTENT"
    DEFERRED_WITH_TARGET = "DEFERRED_WITH_TARGET"
    UNAVAILABLE_WITH_REASON = "UNAVAILABLE_WITH_REASON"


@dataclass(frozen=True)
class LocalNavHierarchyTruthBoundary(_CanonicalMixin):
    is_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavHierarchyEdge(_CanonicalMixin):
    schema_version: str
    edge_id: str
    surface_id: str
    parent_id: str
    child_id: str
    parent_kind: LocalNavHierarchyNodeKind
    child_kind: LocalNavHierarchyNodeKind
    depth: int
    creates_ui_edge: bool
    executes_route: bool
    mutates_runtime: bool
    truth_label: str
    edge_hash: str


@dataclass(frozen=True)
class LocalNavHierarchyContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    nav_registry_id: str
    root_group_id: str
    groups: tuple[str, ...]
    items: tuple[str, ...]
    parent_child_edges: tuple[LocalNavHierarchyEdge, ...]
    max_depth: int
    allows_nested_groups: bool
    cycle_detected: bool
    creates_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class LocalNavOrderingTruthBoundary(_CanonicalMixin):
    is_layout_engine: bool
    drag_drop_enabled: bool
    ui_persistence_created: bool
    mutates_runtime: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavOrderingRule(_CanonicalMixin):
    schema_version: str
    rule_id: str
    surface_id: str
    target_kind: LocalNavHierarchyNodeKind
    target_id: str
    priority: int
    sort_key: str
    stable: bool
    operator_pinned: bool
    creates_ui_position: bool
    truth_label: str
    rule_hash: str


@dataclass(frozen=True)
class LocalNavOrderingContract(_CanonicalMixin):
    schema_version: str
    surface_id: str
    ordered_group_ids: tuple[str, ...]
    ordered_item_ids: tuple[str, ...]
    priority_rules: tuple[LocalNavOrderingRule, ...]
    sort_key: str
    stable_order: bool
    operator_pinned: bool
    layout_position_changed: bool
    drag_drop_enabled: bool
    ui_persistence_created: bool
    mutates_runtime: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class LocalNavSelectionTruthBoundary(_CanonicalMixin):
    route_executed: bool
    action_executed: bool
    url_mutated: bool
    runtime_mutated: bool
    memory_written: bool
    trace_written: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavSelectionState(_CanonicalMixin):
    schema_version: str
    surface_id: str
    selected_nav_item_id: str
    selected_group_id: str
    selection_source: LocalNavSelectionSource
    selection_valid: bool
    invalid_reason: str
    route_executed: bool
    action_executed: bool
    url_mutated: bool
    runtime_mutated: bool
    memory_written: bool
    trace_written: bool
    truth_label: str
    non_goals: tuple[str, ...]
    state_hash: str


@dataclass(frozen=True)
class LocalNavInteractionTruthBoundary(_CanonicalMixin):
    executes_action: bool
    executes_route: bool
    creates_click_handler: bool
    creates_keyboard_shortcut: bool
    grants_permission: bool
    enforces_permission: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class LocalNavInteractionConstraint(_CanonicalMixin):
    schema_version: str
    interaction_id: str
    interaction_kind: LocalNavInteractionKind
    surface_id: str
    nav_item_id: str
    group_id: str
    allowed_as_intent: bool
    blocked: bool
    blocked_reason: str
    protected: bool
    requires_operator: bool
    deferred: bool
    deferred_to_section: str
    deferred_to_pack: str
    executes_action: bool
    executes_route: bool
    creates_click_handler: bool
    creates_keyboard_shortcut: bool
    grants_permission: bool
    enforces_permission: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    constraint_hash: str


@dataclass(frozen=True)
class LocalNavHierarchyProjectionTruthBoundary(_CanonicalMixin):
    is_sidebar_ui: bool
    creates_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    creates_route_runtime: bool
    executes_routes: bool
    creates_click_handlers: bool
    creates_keyboard_shortcuts: bool
    creates_command_palette: bool
    creates_floating_windows: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    starts_p2_2_c: bool
    starts_p2_3: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22BSideEffectProof(_CanonicalMixin):
    """P2.2-B side-effect / no-authority proof. Every field is false."""

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
    p2_2_c_started: bool = False
    p2_3_started: bool = False


@dataclass(frozen=True)
class LocalNavHierarchyProjectionResult(_CanonicalMixin):
    projection_id: str
    created_for_pack: str
    foundation_ref: str
    hierarchy_contracts: tuple[LocalNavHierarchyContract, ...]
    ordering_contracts: tuple[LocalNavOrderingContract, ...]
    selection_states: tuple[LocalNavSelectionState, ...]
    interaction_constraints: tuple[LocalNavInteractionConstraint, ...]
    truth_boundary: LocalNavHierarchyProjectionTruthBoundary
    side_effect_proof: P22BSideEffectProof
    next_pack: str
    is_sidebar_ui: bool
    creates_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    creates_route_runtime: bool
    executes_routes: bool
    creates_click_handlers: bool
    creates_keyboard_shortcuts: bool
    creates_command_palette: bool
    creates_floating_windows: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    starts_p2_2_c: bool
    starts_p2_3: bool
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P22BLocalNavigationHierarchyResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    pack_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    foundation_ref: str
    hierarchy_projection: LocalNavHierarchyProjectionResult
    side_effect_proof: P22BSideEffectProof
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
            "blocked or unavailable interaction requires reason",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _require_deferred_target(section: str, pack: str, *, field: str) -> None:
    if not section or not pack:
        _reject(
            "deferred interaction requires deferred_to_section and deferred_to_pack",
            field=field,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def _items_for_surface(
    surface_id: str,
    items: tuple[LocalNavItemContract, ...],
) -> tuple[LocalNavItemContract, ...]:
    return tuple(item for item in items if item.surface_id == surface_id)


def _detect_cycle(edges: tuple[LocalNavHierarchyEdge, ...]) -> bool:
    adjacency: dict[str, list[str]] = {}
    nodes: set[str] = set()
    for edge in edges:
        adjacency.setdefault(edge.parent_id, []).append(edge.child_id)
        nodes.add(edge.parent_id)
        nodes.add(edge.child_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for child in adjacency.get(node, []):
            if dfs(child):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(node) for node in nodes)


def _max_edge_depth(edges: tuple[LocalNavHierarchyEdge, ...]) -> int:
    if not edges:
        return 0
    return max(edge.depth for edge in edges)


def build_local_nav_hierarchy_edge(
    *,
    surface_id: str,
    parent_id: str,
    child_id: str,
    parent_kind: LocalNavHierarchyNodeKind | str,
    child_kind: LocalNavHierarchyNodeKind | str,
    depth: int,
) -> LocalNavHierarchyEdge:
    parent = _coerce_enum(LocalNavHierarchyNodeKind, parent_kind, "parent_kind")
    child = _coerce_enum(LocalNavHierarchyNodeKind, child_kind, "child_kind")
    edge_id = f"{surface_id}_edge_{parent_id}_to_{child_id}"
    payload = {
        "schema_version": LOCAL_NAV_HIERARCHY_EDGE_VERSION,
        "edge_id": edge_id,
        "surface_id": surface_id,
        "parent_id": parent_id,
        "child_id": child_id,
        "parent_kind": parent,
        "child_kind": child,
        "depth": depth,
        "creates_ui_edge": False,
        "executes_route": False,
        "mutates_runtime": False,
        "truth_label": P22BTruthLabel.STRUCTURAL_METADATA_ONLY.value,
    }
    return LocalNavHierarchyEdge(**payload, edge_hash=_hash_payload(payload))


def _build_hierarchy_edges_for_registry(
    registry: PerSurfaceLocalNavRegistry,
    items: tuple[LocalNavItemContract, ...],
) -> tuple[LocalNavHierarchyEdge, ...]:
    surface_id = registry.surface_id
    root_group_id = registry.default_local_nav_group
    edges: list[LocalNavHierarchyEdge] = []
    surface_items = _items_for_surface(surface_id, items)
    items_by_group: dict[str, list[LocalNavItemContract]] = {}
    for item in surface_items:
        items_by_group.setdefault(item.group_id, []).append(item)

    for group in registry.nav_groups:
        if group.group_id == root_group_id:
            continue
        edges.append(
            build_local_nav_hierarchy_edge(
                surface_id=surface_id,
                parent_id=root_group_id,
                child_id=group.group_id,
                parent_kind=LocalNavHierarchyNodeKind.GROUP,
                child_kind=LocalNavHierarchyNodeKind.GROUP,
                depth=2,
            )
        )

    for group_id, group_items in items_by_group.items():
        parent_kind = LocalNavHierarchyNodeKind.GROUP
        depth = 2 if group_id == root_group_id else 3
        for item in group_items:
            edges.append(
                build_local_nav_hierarchy_edge(
                    surface_id=surface_id,
                    parent_id=group_id,
                    child_id=item.nav_item_id,
                    parent_kind=parent_kind,
                    child_kind=LocalNavHierarchyNodeKind.ITEM,
                    depth=depth,
                )
            )
    return tuple(edges)


def build_local_nav_hierarchy_contract(
    registry: PerSurfaceLocalNavRegistry,
    *,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> LocalNavHierarchyContract:
    if items is None:
        items = build_local_nav_item_contracts()
    surface_id = registry.surface_id
    surface_items = _items_for_surface(surface_id, items)
    groups = tuple(group.group_id for group in registry.nav_groups)
    item_ids = tuple(item.nav_item_id for item in surface_items)
    edges = _build_hierarchy_edges_for_registry(registry, items)
    cycle_detected = _detect_cycle(edges)
    if cycle_detected:
        _reject(
            "local nav hierarchy must not contain cycles",
            field="parent_child_edges",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    max_depth = _max_edge_depth(edges)
    payload = {
        "schema_version": LOCAL_NAV_HIERARCHY_VERSION,
        "surface_id": surface_id,
        "nav_registry_id": registry.nav_registry_id,
        "root_group_id": registry.default_local_nav_group,
        "groups": groups,
        "items": item_ids,
        "parent_child_edges": edges,
        "max_depth": max_depth,
        "allows_nested_groups": True,
        "cycle_detected": False,
        "creates_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "executes_routes": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": P22BTruthLabel.LOCAL_NAV_HIERARCHY_CONTRACT.value,
        "non_goals": _HIERARCHY_NON_GOALS,
    }
    contract = LocalNavHierarchyContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_hierarchy_is_not_ui(contract)
    assert_hierarchy_has_no_cycles(contract)
    return contract


def build_local_nav_hierarchy_contracts(
    *,
    registries: tuple[PerSurfaceLocalNavRegistry, ...] | None = None,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> tuple[LocalNavHierarchyContract, ...]:
    if registries is None:
        registries = build_per_surface_local_nav_registries()
    if items is None:
        items = build_local_nav_item_contracts()
    return tuple(
        build_local_nav_hierarchy_contract(registry, items=items)
        for registry in registries
    )


def build_local_nav_ordering_rule(
    *,
    surface_id: str,
    target_kind: LocalNavHierarchyNodeKind | str,
    target_id: str,
    priority: int,
    sort_key: str,
    operator_pinned: bool = False,
) -> LocalNavOrderingRule:
    kind = _coerce_enum(LocalNavHierarchyNodeKind, target_kind, "target_kind")
    rule_id = f"{surface_id}_order_{kind.value.lower()}_{target_id}"
    payload = {
        "schema_version": LOCAL_NAV_ORDERING_RULE_VERSION,
        "rule_id": rule_id,
        "surface_id": surface_id,
        "target_kind": kind,
        "target_id": target_id,
        "priority": priority,
        "sort_key": sort_key,
        "stable": True,
        "operator_pinned": operator_pinned,
        "creates_ui_position": False,
        "truth_label": P22BTruthLabel.STABLE_ORDER_ONLY.value,
    }
    return LocalNavOrderingRule(**payload, rule_hash=_hash_payload(payload))


def build_local_nav_ordering_contract(
    registry: PerSurfaceLocalNavRegistry,
    *,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> LocalNavOrderingContract:
    if items is None:
        items = build_local_nav_item_contracts()
    surface_id = registry.surface_id
    surface_items = _items_for_surface(surface_id, items)
    ordered_group_ids = tuple(group.group_id for group in registry.nav_groups)
    ordered_item_ids = tuple(item.nav_item_id for item in surface_items)
    rules: list[LocalNavOrderingRule] = []
    for index, group_id in enumerate(ordered_group_ids):
        rules.append(
            build_local_nav_ordering_rule(
                surface_id=surface_id,
                target_kind=LocalNavHierarchyNodeKind.GROUP,
                target_id=group_id,
                priority=index,
                sort_key=f"group:{index:03d}:{group_id}",
                operator_pinned=group_id == registry.default_local_nav_group,
            )
        )
    base = len(rules)
    for index, item_id in enumerate(ordered_item_ids):
        rules.append(
            build_local_nav_ordering_rule(
                surface_id=surface_id,
                target_kind=LocalNavHierarchyNodeKind.ITEM,
                target_id=item_id,
                priority=base + index,
                sort_key=f"item:{index:03d}:{item_id}",
            )
        )
    sort_key = f"{surface_id}:stable_order"
    payload = {
        "schema_version": LOCAL_NAV_ORDERING_VERSION,
        "surface_id": surface_id,
        "ordered_group_ids": ordered_group_ids,
        "ordered_item_ids": ordered_item_ids,
        "priority_rules": tuple(rules),
        "sort_key": sort_key,
        "stable_order": True,
        "operator_pinned": True,
        "layout_position_changed": False,
        "drag_drop_enabled": False,
        "ui_persistence_created": False,
        "mutates_runtime": False,
        "truth_label": P22BTruthLabel.ORDERING_CONTRACT.value,
        "non_goals": _ORDERING_NON_GOALS,
    }
    contract = LocalNavOrderingContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_ordering_is_deterministic(contract)
    assert_ordering_is_not_layout_engine(contract)
    return contract


def build_local_nav_ordering_contracts(
    *,
    registries: tuple[PerSurfaceLocalNavRegistry, ...] | None = None,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> tuple[LocalNavOrderingContract, ...]:
    if registries is None:
        registries = build_per_surface_local_nav_registries()
    if items is None:
        items = build_local_nav_item_contracts()
    return tuple(
        build_local_nav_ordering_contract(registry, items=items)
        for registry in registries
    )


def build_local_nav_selection_state(
    registry: PerSurfaceLocalNavRegistry,
    *,
    items: tuple[LocalNavItemContract, ...] | None = None,
    selection_source: LocalNavSelectionSource | str = LocalNavSelectionSource.DEFAULT,
    selected_nav_item_id: str | None = None,
    selected_group_id: str | None = None,
    selection_valid: bool = True,
    invalid_reason: str = "",
) -> LocalNavSelectionState:
    if items is None:
        items = build_local_nav_item_contracts()
    source = _coerce_enum(LocalNavSelectionSource, selection_source, "selection_source")
    surface_id = registry.surface_id
    surface_items = _items_for_surface(surface_id, items)
    default_group = selected_group_id or registry.default_local_nav_group
    if selected_nav_item_id is None:
        default_items = [
            item
            for item in surface_items
            if item.group_id == default_group
            and item.availability == LocalNavAvailabilityState.AVAILABLE
        ]
        selected_item = default_items[0].nav_item_id if default_items else ""
        if not default_items and surface_items:
            fallback = surface_items[0]
            selected_item = fallback.nav_item_id
            default_group = fallback.group_id
            if fallback.availability == LocalNavAvailabilityState.UNAVAILABLE:
                source = LocalNavSelectionSource.UNAVAILABLE_FALLBACK
            elif fallback.protected or fallback.availability == LocalNavAvailabilityState.PROTECTED:
                source = LocalNavSelectionSource.PROTECTED_FALLBACK
    else:
        selected_item = selected_nav_item_id
    if not selection_valid and not invalid_reason:
        _require_reason(invalid_reason, field="invalid_reason")
    payload = {
        "schema_version": LOCAL_NAV_SELECTION_VERSION,
        "surface_id": surface_id,
        "selected_nav_item_id": selected_item,
        "selected_group_id": default_group,
        "selection_source": source,
        "selection_valid": selection_valid,
        "invalid_reason": invalid_reason,
        "route_executed": False,
        "action_executed": False,
        "url_mutated": False,
        "runtime_mutated": False,
        "memory_written": False,
        "trace_written": False,
        "truth_label": P22BTruthLabel.SELECTION_STATE_CONTRACT.value,
        "non_goals": _SELECTION_NON_GOALS,
    }
    state = LocalNavSelectionState(**payload, state_hash=_hash_payload(payload))
    assert_selection_is_not_route_execution(state)
    assert_selection_does_not_mutate_runtime(state)
    return state


def build_local_nav_selection_states(
    *,
    registries: tuple[PerSurfaceLocalNavRegistry, ...] | None = None,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> tuple[LocalNavSelectionState, ...]:
    if registries is None:
        registries = build_per_surface_local_nav_registries()
    if items is None:
        items = build_local_nav_item_contracts()
    return tuple(
        build_local_nav_selection_state(registry, items=items)
        for registry in registries
    )


def build_local_nav_interaction_constraint(
    *,
    interaction_id: str,
    interaction_kind: LocalNavInteractionKind | str,
    surface_id: str,
    nav_item_id: str,
    group_id: str,
    disposition: LocalNavInteractionDisposition | str = (
        LocalNavInteractionDisposition.ALLOWED_AS_INTENT
    ),
    allowed_as_intent: bool = True,
    blocked_reason: str = "",
    deferred_to_section: str = "",
    deferred_to_pack: str = "",
) -> LocalNavInteractionConstraint:
    kind = _coerce_enum(LocalNavInteractionKind, interaction_kind, "interaction_kind")
    disposition_value = _coerce_enum(
        LocalNavInteractionDisposition,
        disposition,
        "disposition",
    )
    blocked = disposition_value in {
        LocalNavInteractionDisposition.BLOCKED_WITH_REASON,
        LocalNavInteractionDisposition.DEFERRED_WITH_TARGET,
        LocalNavInteractionDisposition.UNAVAILABLE_WITH_REASON,
    }
    protected = disposition_value == LocalNavInteractionDisposition.PROTECTED_INTENT
    deferred = disposition_value == LocalNavInteractionDisposition.DEFERRED_WITH_TARGET
    requires_operator = protected
    if blocked:
        _require_reason(blocked_reason, field="blocked_reason")
    if deferred:
        _require_deferred_target(
            deferred_to_section,
            deferred_to_pack,
            field="deferred_to_section",
        )
    payload = {
        "schema_version": LOCAL_NAV_INTERACTION_VERSION,
        "interaction_id": interaction_id,
        "interaction_kind": kind,
        "surface_id": surface_id,
        "nav_item_id": nav_item_id,
        "group_id": group_id,
        "allowed_as_intent": allowed_as_intent,
        "blocked": blocked,
        "blocked_reason": blocked_reason,
        "requires_operator": requires_operator,
        "protected": protected,
        "deferred": deferred,
        "deferred_to_section": deferred_to_section,
        "deferred_to_pack": deferred_to_pack,
        "executes_action": False,
        "executes_route": False,
        "creates_click_handler": False,
        "creates_keyboard_shortcut": False,
        "grants_permission": False,
        "enforces_permission": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": P22BTruthLabel.INTERACTION_CONSTRAINT_ONLY.value,
        "non_goals": _INTERACTION_NON_GOALS,
    }
    constraint = LocalNavInteractionConstraint(
        **payload,
        constraint_hash=_hash_payload(payload),
    )
    assert_interaction_is_intent_only(constraint)
    assert_interaction_does_not_create_click_handler(constraint)
    assert_interaction_does_not_execute_route(constraint)
    assert_protected_nav_is_not_permission_enforcement(constraint)
    if deferred:
        assert_deferred_nav_has_target(constraint)
    return constraint


def _interaction_constraints_for_item(
    item: LocalNavItemContract,
) -> tuple[LocalNavInteractionConstraint, ...]:
    base_id = f"{item.surface_id}_{item.nav_item_id}"
    constraints: list[LocalNavInteractionConstraint] = [
        build_local_nav_interaction_constraint(
            interaction_id=f"{base_id}_select",
            interaction_kind=LocalNavInteractionKind.SELECT_ITEM_INTENT,
            surface_id=item.surface_id,
            nav_item_id=item.nav_item_id,
            group_id=item.group_id,
        ),
        build_local_nav_interaction_constraint(
            interaction_id=f"{base_id}_expand_group",
            interaction_kind=LocalNavInteractionKind.EXPAND_GROUP_INTENT,
            surface_id=item.surface_id,
            nav_item_id=item.nav_item_id,
            group_id=item.group_id,
        ),
        build_local_nav_interaction_constraint(
            interaction_id=f"{base_id}_collapse_group",
            interaction_kind=LocalNavInteractionKind.COLLAPSE_GROUP_INTENT,
            surface_id=item.surface_id,
            nav_item_id=item.nav_item_id,
            group_id=item.group_id,
        ),
        build_local_nav_interaction_constraint(
            interaction_id=f"{base_id}_show_info",
            interaction_kind=LocalNavInteractionKind.SHOW_ITEM_INFO,
            surface_id=item.surface_id,
            nav_item_id=item.nav_item_id,
            group_id=item.group_id,
        ),
    ]
    if item.availability == LocalNavAvailabilityState.UNAVAILABLE:
        constraints.append(
            build_local_nav_interaction_constraint(
                interaction_id=f"{base_id}_show_unavailable",
                interaction_kind=LocalNavInteractionKind.SHOW_UNAVAILABLE_REASON,
                surface_id=item.surface_id,
                nav_item_id=item.nav_item_id,
                group_id=item.group_id,
                disposition=LocalNavInteractionDisposition.UNAVAILABLE_WITH_REASON,
                allowed_as_intent=False,
                blocked_reason=item.unavailable_reason,
            )
        )
    if item.protected or item.availability == LocalNavAvailabilityState.PROTECTED:
        constraints.append(
            build_local_nav_interaction_constraint(
                interaction_id=f"{base_id}_show_protected",
                interaction_kind=LocalNavInteractionKind.SHOW_PROTECTED_REASON,
                surface_id=item.surface_id,
                nav_item_id=item.nav_item_id,
                group_id=item.group_id,
                disposition=LocalNavInteractionDisposition.PROTECTED_INTENT,
                blocked_reason="Protected local nav requires operator context only",
            )
        )
    if item.deferred or item.availability == LocalNavAvailabilityState.DEFERRED:
        constraints.append(
            build_local_nav_interaction_constraint(
                interaction_id=f"{base_id}_show_deferred",
                interaction_kind=LocalNavInteractionKind.SHOW_DEFERRED_REASON,
                surface_id=item.surface_id,
                nav_item_id=item.nav_item_id,
                group_id=item.group_id,
                disposition=LocalNavInteractionDisposition.DEFERRED_WITH_TARGET,
                blocked_reason="Deferred local nav item",
                deferred_to_section=item.deferred_to_section,
                deferred_to_pack=item.deferred_to_pack,
            )
        )
    return tuple(constraints)


def build_local_nav_interaction_constraints(
    *,
    items: tuple[LocalNavItemContract, ...] | None = None,
) -> tuple[LocalNavInteractionConstraint, ...]:
    if items is None:
        items = build_local_nav_item_contracts()
    constraints: list[LocalNavInteractionConstraint] = []
    for item in items:
        constraints.extend(_interaction_constraints_for_item(item))
    return tuple(constraints)


def build_p2_2_b_side_effect_proof() -> P22BSideEffectProof:
    return P22BSideEffectProof()


def build_local_nav_hierarchy_projection_result(
    *,
    foundation: LocalNavProjectionSeed | None = None,
    hierarchy_contracts: tuple[LocalNavHierarchyContract, ...] | None = None,
    ordering_contracts: tuple[LocalNavOrderingContract, ...] | None = None,
    selection_states: tuple[LocalNavSelectionState, ...] | None = None,
    interaction_constraints: tuple[LocalNavInteractionConstraint, ...] | None = None,
) -> LocalNavHierarchyProjectionResult:
    if foundation is None:
        foundation = build_local_nav_projection_seed()
    if hierarchy_contracts is None:
        hierarchy_contracts = build_local_nav_hierarchy_contracts()
    if ordering_contracts is None:
        ordering_contracts = build_local_nav_ordering_contracts()
    if selection_states is None:
        selection_states = build_local_nav_selection_states()
    if interaction_constraints is None:
        interaction_constraints = build_local_nav_interaction_constraints()
    side_effects = build_p2_2_b_side_effect_proof()
    foundation_ref = f"{P2_2_A_REPORT_FILENAME}:{foundation.projection_id}"
    truth_boundary_payload = {
        "is_sidebar_ui": False,
        "creates_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "creates_route_runtime": False,
        "executes_routes": False,
        "creates_click_handlers": False,
        "creates_keyboard_shortcuts": False,
        "creates_command_palette": False,
        "creates_floating_windows": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "starts_p2_2_c": False,
        "starts_p2_3": False,
        "truth_labels": (
            P22BTruthLabel.HIERARCHY_PROJECTION.value,
            P22BTruthLabel.READ_MODEL_ONLY.value,
            P22BTruthLabel.NOT_UI.value,
            P22BTruthLabel.NOT_ROUTE_RUNTIME.value,
            P22BTruthLabel.NOT_P2_2_C.value,
            P22BTruthLabel.NOT_P2_3.value,
        ),
    }
    truth_boundary = LocalNavHierarchyProjectionTruthBoundary(
        **truth_boundary_payload,
        boundary_hash=_hash_payload(truth_boundary_payload),
    )
    payload = {
        "projection_id": "local_nav_hierarchy_projection_p2_2_b",
        "created_for_pack": P2_2_B_PACK_ID,
        "foundation_ref": foundation_ref,
        "hierarchy_contracts": hierarchy_contracts,
        "ordering_contracts": ordering_contracts,
        "selection_states": selection_states,
        "interaction_constraints": interaction_constraints,
        "truth_boundary": truth_boundary,
        "side_effect_proof": side_effects,
        "next_pack": P2_2_B_NEXT_PACK,
        "is_sidebar_ui": False,
        "creates_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "creates_route_runtime": False,
        "executes_routes": False,
        "creates_click_handlers": False,
        "creates_keyboard_shortcuts": False,
        "creates_command_palette": False,
        "creates_floating_windows": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "starts_p2_2_c": False,
        "starts_p2_3": False,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = LocalNavHierarchyProjectionResult(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_is_not_sidebar(projection)
    assert_p2_2_b_does_not_start_p2_2_c(projection)
    assert_p2_2_b_does_not_start_p2_3(projection)
    assert_local_nav_foundation_reused(projection, foundation)
    return projection


def build_p2_2_b_local_navigation_hierarchy_result() -> P22BLocalNavigationHierarchyResult:
    foundation = build_local_nav_projection_seed()
    projection = build_local_nav_hierarchy_projection_result(foundation=foundation)
    side_effects = build_p2_2_b_side_effect_proof()
    foundation_ref = projection.foundation_ref
    payload = {
        "schema_version": P2_2_B_RESULT_VERSION,
        "pack_id": P2_2_B_PACK_ID,
        "section_id": P2_2_B_SECTION_ID,
        "pack_name": P2_2_B_PACK_NAME,
        "covered_checkpoints": P2_2_B_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_2_B_DEPENDENCY_PACKS,
        "foundation_ref": foundation_ref,
        "hierarchy_projection": projection,
        "side_effect_proof": side_effects,
        "truth_labels": (
            P22BTruthLabel.HIERARCHY_PROJECTION.value,
            P22BTruthLabel.READ_MODEL_ONLY.value,
            P22BTruthLabel.NOT_UI.value,
            P22BTruthLabel.NOT_ROUTE_RUNTIME.value,
            P22BTruthLabel.NOT_P2_2_C.value,
            P22BTruthLabel.NOT_P2_3.value,
        ),
        "next_pack": P2_2_B_NEXT_PACK,
    }
    result = P22BLocalNavigationHierarchyResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_2_b_depends_on_p2_2_a(result, foundation)
    return result


def serialize_p2_2_b_result(
    result: P22BLocalNavigationHierarchyResult | None = None,
) -> str:
    if result is None:
        result = build_p2_2_b_local_navigation_hierarchy_result()
    return to_canonical_json(result.to_canonical_dict())


def validate_local_nav_selection_source(
    source: LocalNavSelectionSource | str,
) -> LocalNavSelectionSource:
    return _coerce_enum(LocalNavSelectionSource, source, "selection_source")


def validate_local_nav_interaction_kind(
    kind: LocalNavInteractionKind | str,
) -> LocalNavInteractionKind:
    return _coerce_enum(LocalNavInteractionKind, kind, "interaction_kind")


def assert_p2_2_b_depends_on_p2_2_a(
    result: P22BLocalNavigationHierarchyResult,
    foundation: LocalNavProjectionSeed,
) -> None:
    if P2_2_A_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.2-B must depend on P2.2-A",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if foundation.created_for_pack != P2_2_A_PACK_ID:
        _reject(
            "P2.2-B must reuse P2.2-A projection seed",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_A_REPORT_FILENAME not in result.foundation_ref:
        _reject(
            "P2.2-B foundation ref must reference P2.2-A report",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_local_nav_foundation_reused(
    projection: LocalNavHierarchyProjectionResult,
    foundation: LocalNavProjectionSeed,
) -> None:
    if foundation.created_for_pack != P2_2_A_PACK_ID:
        _reject(
            "hierarchy projection must reference P2.2-A foundation",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_A_REPORT_FILENAME not in projection.foundation_ref:
        _reject(
            "hierarchy projection foundation ref must include P2.2-A report",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if len(projection.hierarchy_contracts) != len(foundation.per_surface_nav_registries):
        _reject(
            "hierarchy contracts must cover all P2.2-A registries",
            field="hierarchy_contracts",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_duplicate_local_nav_registry(
    projection: LocalNavHierarchyProjectionResult,
    foundation: LocalNavProjectionSeed,
) -> None:
    foundation_ids = {
        registry.nav_registry_id for registry in foundation.per_surface_nav_registries
    }
    hierarchy_ids = {
        contract.nav_registry_id for contract in projection.hierarchy_contracts
    }
    if foundation_ids != hierarchy_ids:
        _reject(
            "hierarchy must reuse P2.2-A nav registry ids without duplication",
            field="nav_registry_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_duplicate_local_nav_item_contract(
    projection: LocalNavHierarchyProjectionResult,
    foundation: LocalNavProjectionSeed,
) -> None:
    foundation_item_ids = {item.nav_item_id for item in foundation.nav_item_contracts}
    hierarchy_item_ids = {
        item_id
        for contract in projection.hierarchy_contracts
        for item_id in contract.items
    }
    if not hierarchy_item_ids.issubset(foundation_item_ids):
        _reject(
            "hierarchy items must reference P2.2-A nav item contracts",
            field="items",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_hierarchy_has_no_cycles(contract: LocalNavHierarchyContract) -> None:
    if contract.cycle_detected or _detect_cycle(contract.parent_child_edges):
        _reject(
            "hierarchy must not contain cycles",
            field="cycle_detected",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_hierarchy_is_not_ui(contract: LocalNavHierarchyContract) -> None:
    if (
        contract.creates_ui
        or contract.creates_sidebar
        or contract.creates_global_left_nav
        or contract.executes_routes
        or contract.mutates_runtime
    ):
        _reject(
            "hierarchy must not create UI or execute routes",
            field="creates_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_ordering_is_deterministic(contract: LocalNavOrderingContract) -> None:
    if not contract.stable_order:
        _reject(
            "ordering must be stable and deterministic",
            field="stable_order",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    priorities = [rule.priority for rule in contract.priority_rules]
    if len(priorities) != len(set(priorities)):
        _reject(
            "ordering priority rules must be deterministic",
            field="priority_rules",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_ordering_is_not_layout_engine(contract: LocalNavOrderingContract) -> None:
    if (
        contract.drag_drop_enabled
        or contract.ui_persistence_created
        or contract.layout_position_changed
        or contract.mutates_runtime
    ):
        _reject(
            "ordering must not be layout engine or UI persistence",
            field="drag_drop_enabled",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selection_is_not_route_execution(state: LocalNavSelectionState) -> None:
    if state.route_executed or state.action_executed or state.url_mutated:
        _reject(
            "selection must not execute route or action",
            field="route_executed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_selection_does_not_mutate_runtime(state: LocalNavSelectionState) -> None:
    if state.runtime_mutated or state.memory_written or state.trace_written:
        _reject(
            "selection must not mutate runtime or write memory/trace",
            field="runtime_mutated",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_interaction_is_intent_only(constraint: LocalNavInteractionConstraint) -> None:
    if constraint.executes_action or constraint.executes_route:
        _reject(
            "interaction constraint must be intent only",
            field="executes_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_interaction_does_not_create_click_handler(
    constraint: LocalNavInteractionConstraint,
) -> None:
    if constraint.creates_click_handler or constraint.creates_keyboard_shortcut:
        _reject(
            "interaction constraint must not create click handler or keyboard shortcut",
            field="creates_click_handler",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_interaction_does_not_execute_route(
    constraint: LocalNavInteractionConstraint,
) -> None:
    if constraint.executes_route:
        _reject(
            "interaction constraint must not execute route",
            field="executes_route",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_protected_nav_is_not_permission_enforcement(
    constraint: LocalNavInteractionConstraint,
) -> None:
    if constraint.grants_permission or constraint.enforces_permission:
        _reject(
            "protected nav interaction must not grant or enforce permission",
            field="grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_deferred_nav_has_target(constraint: LocalNavInteractionConstraint) -> None:
    if constraint.deferred and (
        not constraint.deferred_to_section or not constraint.deferred_to_pack
    ):
        _reject(
            "deferred interaction requires target section/pack",
            field="deferred_to_section",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_projection_is_not_sidebar(
    projection: LocalNavHierarchyProjectionResult,
) -> None:
    if (
        projection.is_sidebar_ui
        or projection.creates_ui
        or projection.creates_sidebar
        or projection.creates_global_left_nav
    ):
        _reject(
            "hierarchy projection must not be sidebar UI",
            field="is_sidebar_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_b_does_not_start_p2_2_c(
    projection: LocalNavHierarchyProjectionResult,
) -> None:
    if projection.starts_p2_2_c:
        _reject(
            "P2.2-B must not start P2.2-C",
            field="starts_p2_2_c",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_b_does_not_start_p2_3(
    projection: LocalNavHierarchyProjectionResult,
) -> None:
    if projection.starts_p2_3 or projection.creates_floating_windows or projection.creates_command_palette:
        _reject(
            "P2.2-B must not start P2.3 or create command palette/floating windows",
            field="starts_p2_3",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
