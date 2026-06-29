"""Tests for P2.2-B local navigation hierarchy / interaction constraints."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    P2_2_A_PACK_ID,
    P2_2_A_REPORT_FILENAME,
    P2_2_B_DEPENDENCY_PACKS,
    P2_2_B_NEXT_PACK,
    P2_2_B_PACK_CHECKPOINT_IDS,
    P2_2_B_PACK_ID,
    LocalNavAvailabilityState,
    LocalNavHierarchyNodeKind,
    LocalNavInteractionDisposition,
    LocalNavInteractionKind,
    LocalNavSelectionSource,
    assert_deferred_nav_has_target,
    assert_hierarchy_has_no_cycles,
    assert_hierarchy_is_not_ui,
    assert_interaction_does_not_create_click_handler,
    assert_interaction_does_not_execute_route,
    assert_interaction_is_intent_only,
    assert_local_nav_foundation_reused,
    assert_no_duplicate_local_nav_item_contract,
    assert_no_duplicate_local_nav_registry,
    assert_ordering_is_deterministic,
    assert_ordering_is_not_layout_engine,
    assert_p2_2_b_depends_on_p2_2_a,
    assert_p2_2_b_does_not_start_p2_2_c,
    assert_p2_2_b_does_not_start_p2_3,
    assert_projection_is_not_sidebar,
    assert_protected_nav_is_not_permission_enforcement,
    assert_selection_does_not_mutate_runtime,
    assert_selection_is_not_route_execution,
    build_local_nav_hierarchy_contract,
    build_local_nav_hierarchy_contracts,
    build_local_nav_hierarchy_edge,
    build_local_nav_hierarchy_projection_result,
    build_local_nav_interaction_constraint,
    build_local_nav_interaction_constraints,
    build_local_nav_ordering_contract,
    build_local_nav_ordering_contracts,
    build_local_nav_ordering_rule,
    build_local_nav_projection_seed,
    build_local_nav_selection_state,
    build_local_nav_selection_states,
    build_p2_2_b_local_navigation_hierarchy_result,
    build_p2_2_b_side_effect_proof,
    build_per_surface_local_nav_registries,
    serialize_p2_2_b_result,
    validate_local_nav_interaction_kind,
    validate_local_nav_selection_source,
)
from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_aurel_shell_module_imports_p2_2_b() -> None:
    import agentic_runtime.aurel_shell.local_navigation_hierarchy  # noqa: F401


def test_p2_2_b_dependency_constants() -> None:
    assert P2_2_B_PACK_ID == "P2.2-B"
    assert P2_2_B_DEPENDENCY_PACKS == (P2_2_A_PACK_ID,)
    assert P2_2_B_PACK_CHECKPOINT_IDS == (
        "P2.2.6",
        "P2.2.7",
        "P2.2.8",
        "P2.2.9",
        "P2.2.10",
    )
    assert P2_2_B_NEXT_PACK == "P2.2-C"


def test_p2_2_b_foundation_dependency() -> None:
    foundation = build_local_nav_projection_seed()
    projection = build_local_nav_hierarchy_projection_result(foundation=foundation)
    result = build_p2_2_b_local_navigation_hierarchy_result()
    assert P2_2_A_REPORT_FILENAME in projection.foundation_ref
    assert P2_2_A_REPORT_FILENAME in result.foundation_ref
    assert foundation.created_for_pack == P2_2_A_PACK_ID
    assert_local_nav_foundation_reused(projection, foundation)
    assert_no_duplicate_local_nav_registry(projection, foundation)
    assert_no_duplicate_local_nav_item_contract(projection, foundation)
    assert_p2_2_b_depends_on_p2_2_a(result, foundation)


def test_p2_2_b_does_not_start_p2_2_c_or_p2_3() -> None:
    projection = build_local_nav_hierarchy_projection_result()
    result = build_p2_2_b_local_navigation_hierarchy_result()
    assert projection.next_pack == P2_2_B_NEXT_PACK
    assert projection.starts_p2_2_c is False
    assert projection.starts_p2_3 is False
    assert result.next_pack == P2_2_B_NEXT_PACK
    assert_p2_2_b_does_not_start_p2_2_c(projection)
    assert_p2_2_b_does_not_start_p2_3(projection)


def test_p2_2_6_hierarchy_contract_builds_and_serializes() -> None:
    registries = build_per_surface_local_nav_registries()
    contracts = build_local_nav_hierarchy_contracts(registries=registries)
    assert len(contracts) == len(CANONICAL_SURFACE_ORDER)
    for contract in contracts:
        assert contract.cycle_detected is False
        assert contract.allows_nested_groups is True
        assert contract.max_depth >= 2
        assert contract.groups
        assert contract.items
        assert contract.parent_child_edges
        assert contract.creates_ui is False
        assert contract.creates_sidebar is False
        assert contract.creates_global_left_nav is False
        assert contract.executes_routes is False
        assert contract.mutates_runtime is False
        assert_hierarchy_has_no_cycles(contract)
        assert_hierarchy_is_not_ui(contract)
        assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_2_6_hierarchy_edge_builds() -> None:
    edge = build_local_nav_hierarchy_edge(
        surface_id="hq",
        parent_id="hq_primary",
        child_id="hq_overview",
        parent_kind=LocalNavHierarchyNodeKind.GROUP,
        child_kind=LocalNavHierarchyNodeKind.ITEM,
        depth=2,
    )
    assert edge.creates_ui_edge is False
    assert edge.executes_route is False
    assert edge.mutates_runtime is False
    assert json.loads(json.dumps(edge.to_canonical_dict()))


def test_p2_2_6_hierarchy_references_foundation_registries() -> None:
    registries = build_per_surface_local_nav_registries()
    registry = registries[0]
    contract = build_local_nav_hierarchy_contract(registry)
    assert contract.nav_registry_id == registry.nav_registry_id
    assert contract.root_group_id == registry.default_local_nav_group
    assert set(contract.groups).issubset({group.group_id for group in registry.nav_groups})


def test_p2_2_7_ordering_contract_builds_and_serializes() -> None:
    contracts = build_local_nav_ordering_contracts()
    assert len(contracts) == len(CANONICAL_SURFACE_ORDER)
    for contract in contracts:
        assert contract.stable_order is True
        assert contract.drag_drop_enabled is False
        assert contract.ui_persistence_created is False
        assert contract.layout_position_changed is False
        assert contract.mutates_runtime is False
        assert contract.ordered_group_ids
        assert contract.ordered_item_ids
        assert contract.priority_rules
        assert_ordering_is_deterministic(contract)
        assert_ordering_is_not_layout_engine(contract)
        assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_2_7_ordering_rule_builds_and_serializes() -> None:
    rule = build_local_nav_ordering_rule(
        surface_id="hq",
        target_kind=LocalNavHierarchyNodeKind.GROUP,
        target_id="hq_primary",
        priority=0,
        sort_key="group:000:hq_primary",
    )
    assert rule.stable is True
    assert rule.creates_ui_position is False
    assert json.loads(json.dumps(rule.to_canonical_dict()))


def test_p2_2_8_selection_state_builds_and_serializes() -> None:
    states = build_local_nav_selection_states()
    assert len(states) == len(CANONICAL_SURFACE_ORDER)
    for state in states:
        assert state.selected_nav_item_id
        assert state.selected_group_id
        assert state.selection_valid is True
        assert state.route_executed is False
        assert state.action_executed is False
        assert state.url_mutated is False
        assert state.runtime_mutated is False
        assert state.memory_written is False
        assert state.trace_written is False
        assert_selection_is_not_route_execution(state)
        assert_selection_does_not_mutate_runtime(state)
        assert json.loads(json.dumps(state.to_canonical_dict()))


def test_p2_2_8_selection_source_closed_world() -> None:
    for source in LocalNavSelectionSource:
        assert validate_local_nav_selection_source(source) == source
        assert validate_local_nav_selection_source(source.value) == source
    with pytest.raises(AurelShellValidationError):
        validate_local_nav_selection_source("INVALID_SOURCE")


def test_p2_2_8_invalid_selection_has_reason() -> None:
    registries = build_per_surface_local_nav_registries()
    with pytest.raises(AurelShellValidationError):
        build_local_nav_selection_state(
            registries[0],
            selection_valid=False,
            invalid_reason="",
        )


def test_p2_2_9_interaction_constraints_build_and_serialize() -> None:
    constraints = build_local_nav_interaction_constraints()
    assert constraints
    kinds_seen = {constraint.interaction_kind for constraint in constraints}
    assert LocalNavInteractionKind.SELECT_ITEM_INTENT in kinds_seen
    assert LocalNavInteractionKind.EXPAND_GROUP_INTENT in kinds_seen
    assert LocalNavInteractionKind.COLLAPSE_GROUP_INTENT in kinds_seen
    assert LocalNavInteractionKind.SHOW_ITEM_INFO in kinds_seen
    for constraint in constraints:
        assert constraint.executes_action is False
        assert constraint.executes_route is False
        assert constraint.creates_click_handler is False
        assert constraint.creates_keyboard_shortcut is False
        assert constraint.grants_permission is False
        assert constraint.enforces_permission is False
        assert constraint.mutates_runtime is False
        assert constraint.writes_memory is False
        assert constraint.writes_trace is False
        assert_interaction_is_intent_only(constraint)
        assert_interaction_does_not_create_click_handler(constraint)
        assert_interaction_does_not_execute_route(constraint)
        assert_protected_nav_is_not_permission_enforcement(constraint)
        assert json.loads(json.dumps(constraint.to_canonical_dict()))


def test_p2_2_9_interaction_kind_closed_world() -> None:
    for kind in LocalNavInteractionKind:
        assert validate_local_nav_interaction_kind(kind) == kind
        assert validate_local_nav_interaction_kind(kind.value) == kind
    with pytest.raises(AurelShellValidationError):
        validate_local_nav_interaction_kind("INVALID_KIND")


def test_p2_2_9_blocked_interaction_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_interaction_constraint(
            interaction_id="blocked_no_reason",
            interaction_kind=LocalNavInteractionKind.SHOW_UNAVAILABLE_REASON,
            surface_id="hq",
            nav_item_id="hq_overview",
            group_id="hq_primary",
            disposition=LocalNavInteractionDisposition.UNAVAILABLE_WITH_REASON,
            allowed_as_intent=False,
            blocked_reason="",
        )


def test_p2_2_9_deferred_interaction_requires_target() -> None:
    constraint = build_local_nav_interaction_constraint(
        interaction_id="deferred_with_target",
        interaction_kind=LocalNavInteractionKind.SHOW_DEFERRED_REASON,
        surface_id="hq",
        nav_item_id="hq_advanced_tools",
        group_id="hq_deferred_tools",
        disposition=LocalNavInteractionDisposition.DEFERRED_WITH_TARGET,
        blocked_reason="Deferred local nav item",
        deferred_to_section="P2.2",
        deferred_to_pack="P2.2-B",
    )
    assert constraint.deferred is True
    assert_deferred_nav_has_target(constraint)


def test_p2_2_9_protected_interaction_does_not_enforce_permission() -> None:
    constraints = build_local_nav_interaction_constraints()
    protected = [
        c
        for c in constraints
        if c.interaction_kind == LocalNavInteractionKind.SHOW_PROTECTED_REASON
    ]
    assert protected
    for constraint in protected:
        assert constraint.requires_operator is True
        assert constraint.enforces_permission is False
        assert constraint.grants_permission is False


def test_p2_2_10_hierarchy_projection_builds_and_serializes() -> None:
    projection = build_local_nav_hierarchy_projection_result()
    assert projection.hierarchy_contracts
    assert projection.ordering_contracts
    assert projection.selection_states
    assert projection.interaction_constraints
    assert projection.next_pack == P2_2_B_NEXT_PACK
    assert projection.is_sidebar_ui is False
    assert projection.creates_ui is False
    assert projection.creates_sidebar is False
    assert projection.creates_global_left_nav is False
    assert projection.creates_route_runtime is False
    assert projection.executes_routes is False
    assert projection.creates_click_handlers is False
    assert projection.creates_keyboard_shortcuts is False
    assert projection.creates_command_palette is False
    assert projection.creates_floating_windows is False
    assert projection.starts_p2_2_c is False
    assert projection.starts_p2_3 is False
    assert_projection_is_not_sidebar(projection)
    assert json.loads(json.dumps(projection.to_canonical_dict()))


def test_p2_2_10_pack_result_builds_and_serializes() -> None:
    result = build_p2_2_b_local_navigation_hierarchy_result()
    assert result.pack_id == P2_2_B_PACK_ID
    assert result.covered_checkpoints == P2_2_B_PACK_CHECKPOINT_IDS
    assert result.hierarchy_projection is not None
    serialized = serialize_p2_2_b_result(result)
    assert serialized
    assert json.loads(serialized)


def test_p2_2_b_side_effect_proof_all_false() -> None:
    proof = build_p2_2_b_side_effect_proof()
    critical_fields = (
        "ui_created",
        "frontend_sidebar_created",
        "global_left_nav_created",
        "route_runtime_created",
        "click_handler_created",
        "keyboard_shortcut_created",
        "command_palette_created",
        "floating_window_created",
        "api_server_created",
        "event_bus_created",
        "memory_written",
        "trace_written",
        "p2_2_c_started",
        "p2_3_started",
    )
    for field in critical_fields:
        assert getattr(proof, field) is False
