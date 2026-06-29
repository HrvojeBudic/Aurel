"""Tests for P2.2-A per-surface local navigation foundation."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    P2_1_CONTRACT_SCOPE_SEAL,
    P2_2_A_DEPENDENCY_PACKS,
    P2_2_A_NEXT_PACK,
    P2_2_A_PACK_CHECKPOINT_IDS,
    P2_2_A_PACK_ID,
    P2_2_PLAN_READINESS,
    P2_2_SECTION_ID,
    P2_2_SECTION_NAME,
    LocalNavAvailabilityState,
    LocalNavItemKind,
    LocalNavVisibilityState,
    assert_availability_is_not_live,
    assert_deferred_state_has_target,
    assert_local_nav_is_surface_owned,
    assert_local_nav_registry_is_not_source_of_truth,
    assert_nav_item_does_not_create_click_handler,
    assert_nav_item_is_not_execution,
    assert_no_global_left_nav_created,
    assert_p2_1_contract_scope_sealed,
    assert_p2_2_a_depends_on_p2_1_d,
    assert_p2_2_a_does_not_start_p2_2_b,
    assert_p2_2_a_does_not_start_p2_3,
    assert_p2_2_section_intake_readiness_is_plan_only,
    assert_projection_seed_does_not_execute_routes,
    assert_projection_seed_is_not_ui,
    assert_unavailable_state_has_reason,
    assert_visibility_is_not_permission,
    build_local_nav_group_contract,
    build_local_nav_item_contract,
    build_local_nav_item_contracts,
    build_local_nav_projection_seed,
    build_local_nav_visibility_availability_state,
    build_local_nav_visibility_availability_states,
    build_local_navigation_ownership_contract,
    build_local_navigation_ownership_contracts,
    build_p2_1_handoff_gate,
    build_p2_2_a_local_navigation_foundation_result,
    build_p2_2_a_side_effect_proof,
    build_p2_2_section_intake,
    build_per_surface_local_nav_registries,
    build_per_surface_local_nav_registry,
    serialize_p2_2_a_result,
    validate_local_nav_item_kind,
)
from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_aurel_shell_module_imports_p2_2_a() -> None:
    import agentic_runtime.aurel_shell.local_navigation  # noqa: F401


def test_p2_2_a_dependency_constants() -> None:
    assert P2_2_A_PACK_ID == "P2.2-A"
    assert P2_2_A_DEPENDENCY_PACKS == ("P2.1-D",)
    assert P2_2_A_PACK_CHECKPOINT_IDS == (
        "P2.2.0",
        "P2.2.1",
        "P2.2.2",
        "P2.2.3",
        "P2.2.4",
        "P2.2.5",
    )


def test_p2_1_d_seal_and_readiness_dependencies() -> None:
    intake = build_p2_2_section_intake()
    gate = build_p2_1_handoff_gate()
    assert intake.required_previous_seal == P2_1_CONTRACT_SCOPE_SEAL
    assert intake.required_previous_readiness == P2_2_PLAN_READINESS
    assert intake.previous_section_seal_found is True
    assert intake.previous_section_readiness_found is True
    assert gate.required_previous_seal == P2_1_CONTRACT_SCOPE_SEAL
    assert gate.required_previous_readiness == P2_2_PLAN_READINESS
    assert_p2_1_contract_scope_sealed(intake)
    assert_p2_2_section_intake_readiness_is_plan_only(intake)
    assert_p2_2_a_depends_on_p2_1_d(gate)


def test_p2_2_a_does_not_start_p2_2_b_or_p2_3() -> None:
    intake = build_p2_2_section_intake()
    gate = build_p2_1_handoff_gate()
    seed = build_local_nav_projection_seed()
    assert intake.starts_p2_2 is True
    assert intake.starts_p2_2_b is False
    assert intake.starts_p2_3 is False
    assert gate.starts_p2_2_b is False
    assert gate.starts_p2_3 is False
    assert seed.starts_p2_2_b is False
    assert seed.starts_p2_3 is False
    assert_p2_2_a_does_not_start_p2_2_b(seed)
    assert_p2_2_a_does_not_start_p2_3(seed)


def test_p2_2_0_section_intake_builds_and_serializes() -> None:
    intake = build_p2_2_section_intake()
    assert intake.section_id == P2_2_SECTION_ID
    assert intake.section_name == P2_2_SECTION_NAME
    assert intake.depends_on_section == "P2.1"
    assert intake.starts_p2_2 is True
    assert intake.starts_p2_2_b is False
    assert intake.starts_p2_3 is False
    assert json.loads(json.dumps(intake.to_canonical_dict()))


def test_p2_2_0_handoff_gate_builds_and_serializes() -> None:
    gate = build_p2_1_handoff_gate()
    assert gate.depends_on_section == "P2.1"
    assert gate.required_previous_seal == P2_1_CONTRACT_SCOPE_SEAL
    assert gate.required_previous_readiness == P2_2_PLAN_READINESS
    assert gate.starts_p2_2 is True
    assert gate.starts_p2_2_b is False
    assert gate.starts_p2_3 is False
    assert json.loads(json.dumps(gate.to_canonical_dict()))


def test_p2_2_1_ownership_contracts_build_and_serialize() -> None:
    contracts = build_local_navigation_ownership_contracts()
    assert len(contracts) == len(CANONICAL_SURFACE_ORDER)
    for contract in contracts:
        assert contract.owned_by_surface is True
        assert contract.owned_by_global_topbar is False
        assert contract.owned_by_command_palette is False
        assert contract.owned_by_floating_window is False
        assert contract.owned_by_runtime_router is False
        assert contract.creates_global_left_nav is False
        assert_local_nav_is_surface_owned(contract)
        assert_no_global_left_nav_created(contract)
        assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_2_1_single_ownership_contract() -> None:
    contract = build_local_navigation_ownership_contract("hq")
    assert contract.surface_id == "hq"
    assert contract.surface_display_name == "HQ"


def test_p2_2_2_per_surface_nav_registries_build_and_serialize() -> None:
    registries = build_per_surface_local_nav_registries()
    assert len(registries) == len(CANONICAL_SURFACE_ORDER)
    registry_ids = {registry.surface_id for registry in registries}
    assert registry_ids == set(CANONICAL_SURFACE_ORDER)
    for registry in registries:
        assert registry.default_local_nav_group
        assert registry.is_source_of_truth is False
        assert registry.creates_ui is False
        assert registry.creates_sidebar is False
        assert registry.creates_global_left_nav is False
        assert registry.executes_routes is False
        assert registry.mutates_runtime is False
        assert_local_nav_registry_is_not_source_of_truth(registry)
        assert json.loads(json.dumps(registry.to_canonical_dict()))


def test_p2_2_2_registry_has_protected_unavailable_deferred_groups() -> None:
    registry = build_per_surface_local_nav_registry("system")
    assert registry.protected_nav_groups
    assert registry.unavailable_nav_groups
    assert registry.deferred_nav_groups
    for group_id in registry.unavailable_nav_groups:
        group = next(g for g in registry.nav_groups if g.group_id == group_id)
        assert group.unavailable_reason
    for group_id in registry.deferred_nav_groups:
        group = next(g for g in registry.nav_groups if g.group_id == group_id)
        assert group.deferred_to_section
        assert group.deferred_to_pack


def test_p2_2_2_unavailable_group_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_group_contract(
            surface_id="hq",
            group_id="hq_bad",
            label="Bad",
            description="Bad",
            group_kind="PRIMARY",
            unavailable=True,
            unavailable_reason="",
        )


def test_p2_2_2_deferred_group_requires_target() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_group_contract(
            surface_id="hq",
            group_id="hq_bad",
            label="Bad",
            description="Bad",
            group_kind="PRIMARY",
            deferred=True,
        )


def test_p2_2_3_nav_item_contracts_build_and_serialize() -> None:
    items = build_local_nav_item_contracts()
    assert items
    for item in items:
        assert item.executes_action is False
        assert item.executes_route is False
        assert item.creates_click_handler is False
        assert item.creates_keyboard_shortcut is False
        assert item.grants_permission is False
        assert item.mutates_runtime is False
        assert_nav_item_is_not_execution(item)
        assert_nav_item_does_not_create_click_handler(item)
        assert json.loads(json.dumps(item.to_canonical_dict()))


def test_p2_2_3_allowed_nav_kinds_accepted() -> None:
    for kind in LocalNavItemKind:
        assert validate_local_nav_item_kind(kind) == kind
        assert validate_local_nav_item_kind(kind.value) == kind


def test_p2_2_3_invalid_nav_kind_rejected() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_item_contract(
            surface_id="hq",
            group_id="hq_primary",
            nav_item_id="hq_bad",
            label="Bad",
            description="Bad",
            nav_kind="INVALID_KIND",
        )


def test_p2_2_3_protected_nav_item_represented() -> None:
    item = build_local_nav_item_contract(
        surface_id="system",
        group_id="system_protected",
        nav_item_id="system_console",
        label="Console",
        description="Protected",
        nav_kind=LocalNavItemKind.STATUS_VIEW,
        protected=True,
        requires_operator=True,
        availability=LocalNavAvailabilityState.PROTECTED,
    )
    assert item.protected is True
    assert item.requires_operator is True


def test_p2_2_3_unavailable_nav_item_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_item_contract(
            surface_id="hq",
            group_id="hq_primary",
            nav_item_id="hq_bad",
            label="Bad",
            description="Bad",
            nav_kind=LocalNavItemKind.PLACEHOLDER,
            availability=LocalNavAvailabilityState.UNAVAILABLE,
            unavailable_reason="",
        )


def test_p2_2_3_deferred_nav_item_requires_target() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_item_contract(
            surface_id="hq",
            group_id="hq_primary",
            nav_item_id="hq_bad",
            label="Bad",
            description="Bad",
            nav_kind=LocalNavItemKind.PLACEHOLDER,
            deferred=True,
        )


def test_p2_2_4_visibility_availability_states_build_and_serialize() -> None:
    items = build_local_nav_item_contracts()
    states = build_local_nav_visibility_availability_states(items)
    assert len(states) == len(items)
    for state in states:
        assert state.is_live is False
        assert state.permission_granted is False
        assert state.runtime_checked is False
        assert state.auth_checked is False
        assert_visibility_is_not_permission(state)
        assert_availability_is_not_live(state)
        if state.unavailable:
            assert_unavailable_state_has_reason(state)
        if state.deferred:
            assert_deferred_state_has_target(state)
        assert json.loads(json.dumps(state.to_canonical_dict()))


def test_p2_2_4_visible_does_not_grant_permission() -> None:
    item = build_local_nav_item_contract(
        surface_id="hq",
        group_id="hq_primary",
        nav_item_id="hq_visible",
        label="Visible",
        description="Visible item",
        nav_kind=LocalNavItemKind.SECTION,
        visibility=LocalNavVisibilityState.VISIBLE,
        availability=LocalNavAvailabilityState.AVAILABLE,
    )
    state = build_local_nav_visibility_availability_state(item)
    assert state.visible is True
    assert state.permission_granted is False


def test_p2_2_4_available_does_not_mean_live() -> None:
    item = build_local_nav_item_contract(
        surface_id="hq",
        group_id="hq_primary",
        nav_item_id="hq_available",
        label="Available",
        description="Available item",
        nav_kind=LocalNavItemKind.SECTION,
    )
    state = build_local_nav_visibility_availability_state(item)
    assert state.available is True
    assert state.is_live is False


def test_p2_2_5_projection_seed_builds_and_serializes() -> None:
    seed = build_local_nav_projection_seed()
    assert seed.section_intake
    assert seed.handoff_gate
    assert seed.ownership_contracts
    assert seed.per_surface_nav_registries
    assert seed.nav_group_contracts
    assert seed.nav_item_contracts
    assert seed.visibility_availability_states
    assert seed.side_effect_proof
    assert seed.handoff_gate.required_previous_seal == P2_1_CONTRACT_SCOPE_SEAL
    assert seed.handoff_gate.required_previous_readiness == P2_2_PLAN_READINESS
    assert seed.next_pack == P2_2_A_NEXT_PACK
    assert seed.is_ui is False
    assert seed.creates_global_left_nav is False
    assert seed.creates_sidebar is False
    assert seed.creates_route_runtime is False
    assert seed.executes_routes is False
    assert seed.creates_command_palette is False
    assert seed.creates_floating_windows is False
    assert seed.starts_p2_2_b is False
    assert seed.starts_p2_3 is False
    assert_projection_seed_is_not_ui(seed)
    assert_projection_seed_does_not_execute_routes(seed)
    assert json.loads(json.dumps(seed.to_canonical_dict()))


def test_p2_2_5_pack_result_builds_and_serializes() -> None:
    result = build_p2_2_a_local_navigation_foundation_result()
    assert result.pack_id == P2_2_A_PACK_ID
    assert result.section_id == P2_2_SECTION_ID
    assert result.projection_seed
    assert result.next_pack == P2_2_A_NEXT_PACK
    assert json.loads(serialize_p2_2_a_result(result))


def test_side_effect_proof_all_false() -> None:
    proof = build_p2_2_a_side_effect_proof()
    critical_fields = (
        "ui_created",
        "frontend_sidebar_created",
        "global_left_nav_created",
        "route_runtime_created",
        "route_handler_created",
        "click_handler_created",
        "keyboard_shortcut_created",
        "command_palette_created",
        "floating_window_created",
        "api_server_created",
        "event_bus_created",
        "memory_written",
        "trace_written",
        "p2_2_b_started",
        "p2_3_started",
    )
    for field in critical_fields:
        assert getattr(proof, field) is False
