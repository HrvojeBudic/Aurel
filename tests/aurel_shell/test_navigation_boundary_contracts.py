"""Tests for P2.0-B navigation and boundary contracts."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    CANONICAL_SURFACE_ORDER,
    AurelSurfaceKind,
    build_default_surface_registry,
)
from agentic_runtime.aurel_shell.boundaries import (
    BoundaryTruthLabel,
    SurfaceTruthOwnerKind,
    assert_hub_cannot_grant_tool_permission,
    assert_hub_entry_is_not_tool_execution,
    assert_settings_cannot_grant_root,
    assert_settings_is_not_system,
    assert_surface_does_not_own_truth,
    assert_system_has_no_agent_access,
    build_hub_internal_tool_entry_boundary,
    build_settings_system_config_boundary,
    build_surface_source_of_truth_boundaries,
    build_system_no_agent_access_boundary,
)
from agentic_runtime.aurel_shell.navigation_boundary import (
    NavigationBoundaryTruthLabel,
    RouteBindingTruthLabel,
    assert_each_surface_has_local_nav_boundary,
    assert_logo_does_not_grant_root,
    assert_logo_does_not_route_to_system,
    assert_logo_routes_to_cro_only,
    assert_navigation_does_not_grant_permission,
    assert_no_navigation_runtime_created,
    assert_no_universal_left_nav,
    assert_surface_nav_does_not_own_truth,
    build_aurel_logo_route_binding,
    build_no_universal_left_nav_contract,
    build_per_surface_navigation_boundaries,
)
from agentic_runtime.aurel_shell.navigation_read_model import (
    P2_0_B_DEPENDENCY_PACK,
    P2_0_B_NEXT_PACK,
    P2_0_B_PACK_CHECKPOINT_IDS,
    P2_0_B_PACK_ID,
    build_p2_0_b_navigation_boundary_pack_result,
    serialize_navigation_boundary_pack_result,
)


def test_module_imports() -> None:
    import agentic_runtime.aurel_shell.navigation_boundary  # noqa: F401
    import agentic_runtime.aurel_shell.boundaries  # noqa: F401
    import agentic_runtime.aurel_shell.navigation_read_model  # noqa: F401


def test_p2_0_b_uses_p2_0_a_registry() -> None:
    registry = build_default_surface_registry()
    nav_pack = build_per_surface_navigation_boundaries(registry)
    assert nav_pack.surface_count == registry.surface_count == 7
    sot = build_surface_source_of_truth_boundaries(registry)
    assert len(sot) == 7


def test_p2_0_b_no_duplicate_surface_list_in_production() -> None:
    """Production code derives boundaries from registry, not hardcoded lists."""
    registry = build_default_surface_registry()
    nav_pack = build_per_surface_navigation_boundaries(registry)
    nav_ids = {b.surface_id for b in nav_pack.surface_boundaries}
    registry_ids = {s.surface_id for s in registry.surfaces}
    assert nav_ids == registry_ids == set(CANONICAL_SURFACE_ORDER)


# --- P2.0.9 No Universal Left Nav ---


def test_p2_0_9_no_universal_left_nav() -> None:
    contract = build_no_universal_left_nav_contract()
    assert contract.global_left_nav_allowed is False
    assert contract.per_surface_nav_required is True
    assert contract.surface_nav_is_local is True
    assert contract.truth_label == NavigationBoundaryTruthLabel.BOUNDARY_CONTRACT_ONLY
    assert_no_universal_left_nav(contract)
    assert_no_navigation_runtime_created(contract)


def test_p2_0_9_each_surface_local_nav() -> None:
    pack = build_per_surface_navigation_boundaries()
    assert_each_surface_has_local_nav_boundary(pack)
    for boundary in pack.surface_boundaries:
        assert boundary.local_nav_required is True
        assert boundary.global_left_nav_allowed is False
        assert_navigation_does_not_grant_permission(boundary)
        assert_surface_nav_does_not_own_truth(boundary)


def test_p2_0_9_no_nav_ui_or_runtime() -> None:
    contract = build_no_universal_left_nav_contract()
    assert contract.route_runtime_created is False
    pack = build_per_surface_navigation_boundaries()
    for boundary in pack.surface_boundaries:
        assert boundary.route_runtime_created is False


# --- P2.0.10 Logo Route Binding ---


def test_p2_0_10_logo_routes_to_cro() -> None:
    binding = build_aurel_logo_route_binding()
    assert binding.target.surface_kind == AurelSurfaceKind.AUREL_CRO
    assert binding.target.surface_id == "aurel_cro"
    assert_logo_routes_to_cro_only(binding)


def test_p2_0_10_logo_not_system() -> None:
    binding = build_aurel_logo_route_binding()
    assert binding.target.surface_kind != AurelSurfaceKind.SYSTEM
    assert binding.target_is_system is False
    assert_logo_does_not_route_to_system(binding)


def test_p2_0_10_logo_not_settings() -> None:
    binding = build_aurel_logo_route_binding()
    assert binding.target.surface_kind != AurelSurfaceKind.SETTINGS
    assert binding.target_is_settings is False


def test_p2_0_10_logo_no_root_access() -> None:
    binding = build_aurel_logo_route_binding()
    assert binding.grants_root_access is False
    assert_logo_does_not_grant_root(binding)


def test_p2_0_10_logo_contract_only() -> None:
    binding = build_aurel_logo_route_binding()
    assert binding.route_runtime_created is False
    assert binding.truth_label == RouteBindingTruthLabel.ROUTE_CONTRACT_ONLY
    assert RouteBindingTruthLabel.ROUTE_HINT_ONLY in binding.secondary_truth_labels


# --- P2.0.11 Source-of-Truth Boundaries ---


def test_p2_0_11_every_surface_source_of_truth() -> None:
    boundaries = build_surface_source_of_truth_boundaries()
    assert len(boundaries) == 7
    kinds = {b.surface_kind for b in boundaries}
    assert kinds == set(AurelSurfaceKind)


def test_p2_0_11_no_surface_owns_truth() -> None:
    boundaries = build_surface_source_of_truth_boundaries()
    for boundary in boundaries:
        assert boundary.surface_owns_truth is False
        assert_surface_does_not_own_truth(boundary)


def test_p2_0_11_truth_owner_explicit() -> None:
    boundaries = build_surface_source_of_truth_boundaries()
    by_kind = {b.surface_kind: b for b in boundaries}
    assert (
        by_kind[AurelSurfaceKind.AUREL_CRO].truth_owner_kind
        == SurfaceTruthOwnerKind.AUREL_CORE_OPERATOR_CONTROL_PLANE
    )
    assert (
        by_kind[AurelSurfaceKind.HQ].truth_owner_kind
        == SurfaceTruthOwnerKind.AUREL_CORE_FLOW_TRACE_PROJECTIONS
    )
    assert (
        by_kind[AurelSurfaceKind.CORP].truth_owner_kind
        == SurfaceTruthOwnerKind.BUSINESS_ENVIRONMENT_STATE
    )
    assert (
        by_kind[AurelSurfaceKind.HUB].truth_owner_kind
        == SurfaceTruthOwnerKind.TOOL_CAPABILITY_REGISTRY_PROJECTION
    )
    assert (
        by_kind[AurelSurfaceKind.IDE].truth_owner_kind
        == SurfaceTruthOwnerKind.CODEOPS_REPO_VALIDATION
    )
    for boundary in boundaries:
        assert boundary.projection_relation
        assert boundary.read_model_relation
        assert boundary.truth_owner_relation


def test_p2_0_11_source_of_truth_serializes() -> None:
    boundaries = build_surface_source_of_truth_boundaries()
    payload = json.dumps(
        [b.to_canonical_dict() for b in boundaries],
        sort_keys=True,
    )
    parsed = json.loads(payload)
    assert len(parsed) == 7
    assert all(b["surface_owns_truth"] is False for b in parsed)


# --- P2.0.12 SYSTEM No-Agent-Access ---


def test_p2_0_12_system_forbids_agent_access() -> None:
    boundary = build_system_no_agent_access_boundary()
    assert boundary.access_rule.agent_access_allowed is False
    assert_system_has_no_agent_access(boundary)


def test_p2_0_12_system_operator_only() -> None:
    boundary = build_system_no_agent_access_boundary()
    assert boundary.access_rule.operator_only is True
    assert boundary.access_rule.root_boundary is True
    assert boundary.truth_label == BoundaryTruthLabel.OPERATOR_ONLY_CONTRACT


def test_p2_0_12_system_not_default_route() -> None:
    boundary = build_system_no_agent_access_boundary()
    assert boundary.access_rule.default_route_target_allowed is False
    logo = build_aurel_logo_route_binding()
    assert logo.target.surface_kind != AurelSurfaceKind.SYSTEM


def test_p2_0_12_no_runtime_enforcement() -> None:
    boundary = build_system_no_agent_access_boundary()
    assert boundary.runtime_enforcement_created is False


# --- P2.0.13 Settings vs SYSTEM ---


def test_p2_0_13_settings_not_system() -> None:
    boundary = build_settings_system_config_boundary()
    assert boundary.settings_is_system is False
    assert_settings_is_not_system(boundary)


def test_p2_0_13_settings_non_root() -> None:
    boundary = build_settings_system_config_boundary()
    assert boundary.settings_scope.is_system is False
    assert boundary.truth_label == BoundaryTruthLabel.NON_ROOT_CONFIG_CONTRACT


def test_p2_0_13_settings_cannot_grant_root() -> None:
    boundary = build_settings_system_config_boundary()
    assert boundary.settings_can_grant_root is False
    assert_settings_cannot_grant_root(boundary)


def test_p2_0_13_settings_cannot_modify_system_root() -> None:
    boundary = build_settings_system_config_boundary()
    assert boundary.settings_can_modify_system_root is False


def test_p2_0_13_settings_cannot_perform_system_actions() -> None:
    boundary = build_settings_system_config_boundary()
    assert boundary.settings_can_perform_system_actions is False


def test_p2_0_13_system_remains_operator_only() -> None:
    boundary = build_settings_system_config_boundary()
    assert boundary.system_is_operator_only is True
    assert boundary.system_root_boundary_preserved is True


# --- P2.0.14 HUB Tool Entry ---


def test_p2_0_14_hub_tool_entry_contract_only() -> None:
    boundary = build_hub_internal_tool_entry_boundary()
    assert (
        boundary.tool_entry.tool_entry_truth_label
        == BoundaryTruthLabel.TOOL_ENTRY_CONTRACT_ONLY
    )
    assert boundary.truth_label == BoundaryTruthLabel.TOOL_ENTRY_CONTRACT_ONLY


def test_p2_0_14_hub_can_list_tool_entries() -> None:
    boundary = build_hub_internal_tool_entry_boundary()
    assert boundary.tool_entry.hub_can_list_tool_entries is True


def test_p2_0_14_hub_cannot_execute_tools() -> None:
    boundary = build_hub_internal_tool_entry_boundary()
    assert boundary.tool_entry.hub_can_execute_tools is False
    assert_hub_entry_is_not_tool_execution(boundary)


def test_p2_0_14_hub_cannot_grant_tool_permission() -> None:
    boundary = build_hub_internal_tool_entry_boundary()
    assert boundary.tool_entry.hub_can_grant_tool_permission is False
    assert_hub_cannot_grant_tool_permission(boundary)


def test_p2_0_14_hub_entry_not_tool_call() -> None:
    boundary = build_hub_internal_tool_entry_boundary()
    assert boundary.tool_entry.hub_entry_is_tool_call is False


# --- Pack Result ---


def test_pack_result_covers_p2_0_9_through_p2_0_14() -> None:
    result = build_p2_0_b_navigation_boundary_pack_result()
    assert result.pack_id == P2_0_B_PACK_ID
    assert result.covered_checkpoints == P2_0_B_PACK_CHECKPOINT_IDS
    assert len(result.checkpoint_reads) == 6
    assert all(
        read.status.value == "DONE" for read in result.checkpoint_reads
    )


def test_pack_result_depends_on_p2_0_a() -> None:
    result = build_p2_0_b_navigation_boundary_pack_result()
    assert result.dependency_pack == P2_0_B_DEPENDENCY_PACK
    assert result.registry.surface_count == 7


def test_pack_result_next_pack_is_p2_0_c() -> None:
    result = build_p2_0_b_navigation_boundary_pack_result()
    assert result.next_pack == P2_0_B_NEXT_PACK


def test_pack_result_side_effects_all_false() -> None:
    result = build_p2_0_b_navigation_boundary_pack_result()
    proof = result.side_effect_proof
    for field_name, value in proof.to_canonical_dict().items():
        assert value is False, f"side effect {field_name} must be false"


def test_pack_result_serializes() -> None:
    result = build_p2_0_b_navigation_boundary_pack_result()
    payload = serialize_navigation_boundary_pack_result(result)
    parsed = json.loads(payload)
    assert parsed["pack_id"] == "P2.0-B"
    assert parsed["result_hash"] == result.result_hash


@pytest.mark.parametrize("checkpoint_id", P2_0_B_PACK_CHECKPOINT_IDS)
def test_checkpoint_status_done(checkpoint_id: str) -> None:
    result = build_p2_0_b_navigation_boundary_pack_result()
    assert result.checkpoint_statuses[checkpoint_id] == "DONE"
