"""Tests for P2.2-C local navigation context / surface-specific profiles."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    AUDIT_REPAIR_001_PACK_ID,
    AUDIT_REPAIR_001_REPORT_FILENAME,
    P2_2_A_REPORT_FILENAME,
    P2_2_B_PACK_ID,
    P2_2_B_REPORT_FILENAME,
    P2_2_C_DEPENDENCY_PACKS,
    P2_2_C_NEXT_PACK,
    P2_2_C_PACK_CHECKPOINT_IDS,
    P2_2_C_PACK_ID,
    LocalNavRestoreSource,
    SurfaceLocalNavProfileKind,
    assert_context_projection_does_not_start_p2_2_d,
    assert_context_projection_does_not_start_p2_3,
    assert_context_projection_is_not_ui,
    assert_local_nav_hierarchy_projection_reused,
    assert_p2_2_c_no_duplicate_local_nav_hierarchy,
    assert_p2_2_c_no_duplicate_local_nav_registry,
    assert_p2_2_c_depends_on_audit_repair_001,
    assert_p2_2_c_depends_on_p2_2_b,
    build_local_nav_context_carryover_contract,
    build_local_nav_context_carryover_contracts,
    build_local_nav_context_projection_result,
    build_local_nav_degraded_profile_contract,
    build_local_nav_degraded_profile_contracts,
    build_local_nav_hierarchy_projection_result,
    build_local_nav_projection_seed,
    build_local_nav_state_restoration_contract,
    build_local_nav_state_restoration_contracts,
    build_p2_2_c_local_navigation_context_result,
    build_p2_2_c_side_effect_proof,
    build_surface_local_nav_profile_contract,
    build_surface_local_nav_profile_contracts,
    serialize_p2_2_c_result,
    validate_local_nav_restore_source,
    validate_surface_local_nav_profile_kind,
)
from agentic_runtime.aurel_shell.contracts import AurelShellValidationError
from agentic_runtime.aurel_shell.local_navigation_hierarchy import (
    build_local_nav_selection_state,
    build_per_surface_local_nav_registries,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER
from agentic_runtime.aurel_shell.topbar import SYSTEM_SURFACE_ID


def test_aurel_shell_module_imports_p2_2_c() -> None:
    import agentic_runtime.aurel_shell.local_navigation_context  # noqa: F401


def test_p2_2_c_dependency_constants() -> None:
    assert P2_2_C_PACK_ID == "P2.2-C"
    assert AUDIT_REPAIR_001_PACK_ID in P2_2_C_DEPENDENCY_PACKS
    assert P2_2_B_PACK_ID in P2_2_C_DEPENDENCY_PACKS
    assert P2_2_C_PACK_CHECKPOINT_IDS == (
        "P2.2.11",
        "P2.2.12",
        "P2.2.13",
        "P2.2.14",
        "P2.2.15",
    )
    assert P2_2_C_NEXT_PACK == "P2.2-D"


def test_p2_2_c_audit_repair_and_p2_2_b_dependencies() -> None:
    foundation = build_local_nav_projection_seed()
    hierarchy = build_local_nav_hierarchy_projection_result(foundation=foundation)
    result = build_p2_2_c_local_navigation_context_result()
    assert AUDIT_REPAIR_001_REPORT_FILENAME in result.audit_repair_ref
    assert P2_2_B_REPORT_FILENAME in result.hierarchy_ref
    assert P2_2_A_REPORT_FILENAME in result.foundation_ref
    assert_p2_2_c_depends_on_audit_repair_001(result)
    assert_p2_2_c_depends_on_p2_2_b(result, hierarchy)


def test_p2_2_c_hierarchy_projection_reused() -> None:
    foundation = build_local_nav_projection_seed()
    hierarchy = build_local_nav_hierarchy_projection_result(foundation=foundation)
    projection = build_local_nav_context_projection_result(
        foundation=foundation,
        hierarchy_projection=hierarchy,
    )
    assert_local_nav_hierarchy_projection_reused(projection, hierarchy)
    assert_p2_2_c_no_duplicate_local_nav_registry(projection, foundation)
    assert_p2_2_c_no_duplicate_local_nav_hierarchy(projection, hierarchy)


def test_p2_2_c_does_not_start_p2_2_d_or_p2_3() -> None:
    projection = build_local_nav_context_projection_result()
    result = build_p2_2_c_local_navigation_context_result()
    assert projection.next_pack == P2_2_C_NEXT_PACK
    assert projection.starts_p2_2_d is False
    assert projection.starts_p2_3 is False
    assert result.next_pack == P2_2_C_NEXT_PACK
    assert_context_projection_does_not_start_p2_2_d(projection)
    assert_context_projection_does_not_start_p2_3(projection)


def test_p2_2_11_context_carryover_builds_and_serializes() -> None:
    contracts = build_local_nav_context_carryover_contracts()
    assert len(contracts) == len(CANONICAL_SURFACE_ORDER)
    for contract in contracts:
        assert contract.previous_projection_ref
        assert contract.current_projection_ref
        assert contract.selected_group_ref
        assert contract.writes_memory is False
        assert contract.writes_trace is False
        assert contract.mutates_runtime is False
        assert contract.uses_local_storage is False
        assert contract.uses_browser_storage is False
        assert contract.executes_route is False
        json.dumps(contract.to_canonical_dict())


def test_p2_2_11_unavailable_carryover_requires_reason() -> None:
    with pytest.raises(AurelShellValidationError):
        build_local_nav_context_carryover_contract(
            surface_id="hq",
            previous_projection_ref="prev",
            current_projection_ref="curr",
            selected_nav_item_ref="",
            selected_group_ref="",
            carryover_available=False,
            carryover_unavailable_reason="",
        )


def test_p2_2_12_surface_profile_builds_and_serializes() -> None:
    profiles = build_surface_local_nav_profile_contracts()
    assert len(profiles) == len(CANONICAL_SURFACE_ORDER)
    for profile in profiles:
        assert profile.surface_id in CANONICAL_SURFACE_ORDER
        assert profile.default_group_id
        assert profile.primary_nav_items
        assert profile.creates_surface_taxonomy is False
        assert profile.activates_future_surface is False
        assert profile.creates_ui is False
        assert profile.creates_sidebar is False
        assert profile.executes_routes is False
        assert profile.mutates_runtime is False
        json.dumps(profile.to_canonical_dict())


def test_p2_2_12_profile_kinds_valid_and_invalid() -> None:
    validate_surface_local_nav_profile_kind(SurfaceLocalNavProfileKind.CRO_SURFACE)
    validate_surface_local_nav_profile_kind("HUB_SURFACE")
    with pytest.raises(AurelShellValidationError):
        validate_surface_local_nav_profile_kind("FORUM_SURFACE")


def test_p2_2_12_official_surfaces_only() -> None:
    registries = build_per_surface_local_nav_registries()
    for registry in registries:
        profile = build_surface_local_nav_profile_contract(registry)
        assert profile.surface_id in CANONICAL_SURFACE_ORDER
        assert "Forum" not in profile.surface_display_name
        assert "Archivium" not in profile.surface_display_name


def test_p2_2_13_restoration_builds_and_serializes() -> None:
    contracts = build_local_nav_state_restoration_contracts()
    assert len(contracts) == len(CANONICAL_SURFACE_ORDER)
    for contract in contracts:
        assert contract.restored_group_id
        assert contract.restored_nav_item_id
        assert contract.route_executed is False
        assert contract.action_executed is False
        assert contract.url_mutated is False
        assert contract.runtime_mutated is False
        assert contract.memory_written is False
        assert contract.trace_written is False
        assert contract.local_storage_written is False
        assert contract.browser_storage_written is False
        json.dumps(contract.to_canonical_dict())


def test_p2_2_13_restore_sources_valid_and_invalid() -> None:
    validate_local_nav_restore_source(LocalNavRestoreSource.DEFAULT_PROFILE)
    validate_local_nav_restore_source("PROTECTED_FALLBACK")
    with pytest.raises(AurelShellValidationError):
        validate_local_nav_restore_source("ROUTE_EXECUTED")


def test_p2_2_13_invalid_restoration_requires_reason() -> None:
    registries = build_per_surface_local_nav_registries()
    selection = build_local_nav_selection_state(registries[0])
    with pytest.raises(AurelShellValidationError):
        build_local_nav_state_restoration_contract(
            selection,
            restoration_valid=False,
            invalid_reason="",
        )


def test_p2_2_14_degraded_profile_builds_and_serializes() -> None:
    profiles = build_surface_local_nav_profile_contracts()
    degraded = build_local_nav_degraded_profile_contracts(profiles=profiles)
    assert len(degraded) == len(CANONICAL_SURFACE_ORDER)
    system_profile = next(p for p in profiles if p.surface_id == SYSTEM_SURFACE_ID)
    system_degraded = build_local_nav_degraded_profile_contract(system_profile)
    assert system_degraded.degraded is True
    assert system_degraded.degradation_reason
    assert system_degraded.is_runtime_failure is False
    assert system_degraded.runtime_failure_proven is False
    assert system_degraded.starts_repair_automation is False
    assert system_degraded.emits_notification is False
    assert system_degraded.mutates_runtime is False
    hub_degraded = next(d for d in degraded if d.surface_id == "hub")
    assert hub_degraded.unavailable is True
    assert hub_degraded.unavailable_reason
    for contract in degraded:
        json.dumps(contract.to_canonical_dict())


def test_p2_2_14_degraded_and_unavailable_require_reasons() -> None:
    profiles = build_surface_local_nav_profile_contracts()
    profile = profiles[0]
    with pytest.raises(AurelShellValidationError):
        build_local_nav_degraded_profile_contract(
            profile,
            degraded=True,
            degradation_reason="",
        )
    with pytest.raises(AurelShellValidationError):
        build_local_nav_degraded_profile_contract(
            profile,
            unavailable=True,
            unavailable_reason="",
        )


def test_p2_2_15_context_projection_builds_and_serializes() -> None:
    projection = build_local_nav_context_projection_result()
    assert projection.context_carryover_contracts
    assert projection.surface_profile_contracts
    assert projection.state_restoration_contracts
    assert projection.degraded_profile_contracts
    assert P2_2_B_REPORT_FILENAME in projection.hierarchy_ref
    assert projection.is_ui is False
    assert projection.creates_sidebar is False
    assert projection.creates_global_left_nav is False
    assert projection.creates_route_runtime is False
    assert projection.executes_routes is False
    assert projection.creates_click_handlers is False
    assert projection.creates_command_palette is False
    assert projection.creates_floating_windows is False
    assert projection.writes_memory is False
    assert projection.writes_trace is False
    assert projection.mutates_runtime is False
    assert projection.creates_surface_taxonomy is False
    assert_context_projection_is_not_ui(projection)
    json.dumps(projection.to_canonical_dict())


def test_p2_2_15_pack_result_serializes() -> None:
    result = build_p2_2_c_local_navigation_context_result()
    payload = json.loads(serialize_p2_2_c_result(result))
    assert payload["pack_id"] == P2_2_C_PACK_ID
    assert payload["context_projection"]["hierarchy_ref"]


def test_p2_2_c_side_effect_proof_all_false() -> None:
    proof = build_p2_2_c_side_effect_proof()
    for field_name, value in proof.to_canonical_dict().items():
        assert value is False, field_name


def test_p2_2_c_side_effect_proof_critical_fields() -> None:
    proof = build_p2_2_c_side_effect_proof()
    assert proof.ui_created is False
    assert proof.frontend_sidebar_created is False
    assert proof.global_left_nav_created is False
    assert proof.route_runtime_created is False
    assert proof.click_handler_created is False
    assert proof.command_palette_created is False
    assert proof.floating_window_created is False
    assert proof.memory_written is False
    assert proof.trace_written is False
    assert proof.local_storage_written is False
    assert proof.browser_storage_written is False
    assert proof.surface_taxonomy_created is False
    assert proof.future_surface_activated is False
    assert proof.p2_2_d_started is False
    assert proof.p2_3_started is False
