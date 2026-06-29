"""Tests for P2.2-D local navigation integration tail / section seal."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell import (
    AUDIT_REPAIR_001_PACK_ID,
    AUDIT_REPAIR_001_REPORT_FILENAME,
    P2_2_A_REPORT_FILENAME,
    P2_2_B_REPORT_FILENAME,
    P2_2_C_PACK_ID,
    P2_2_C_REPORT_FILENAME,
    P2_2_D_DEPENDENCY_PACKS,
    P2_2_D_PACK_CHECKPOINT_IDS,
    P2_2_D_PACK_ID,
    P22LocalNavigationSealDecision,
    P22P23ReadinessDecision,
    assert_p2_2_a_b_c_outputs_reused,
    assert_p2_2_cli_inspect_is_read_only,
    assert_p2_2_d_depends_on_audit_repair_001,
    assert_p2_2_d_depends_on_p2_2_c,
    assert_p2_2_d_does_not_start_p2_3,
    assert_p2_2_d_does_not_start_p2_4,
    assert_p2_2_docs_sync_does_not_rewrite_roadmap_canon,
    assert_p2_2_event_contract_does_not_emit_runtime_events,
    assert_p2_2_event_contract_is_not_event_bus,
    assert_p2_2_exit_seal_is_contract_scope_only,
    assert_p2_2_exit_seal_is_not_release_scope,
    assert_p2_2_integration_snapshot_is_not_source_of_truth,
    assert_p2_2_integration_snapshot_is_not_ui,
    assert_p2_2_projection_contract_is_not_api_server,
    assert_p2_2_tui_binding_unavailable_has_reason,
    assert_p2_3_readiness_does_not_start_p2_3,
    build_local_nav_context_projection_result,
    build_local_nav_hierarchy_projection_result,
    build_local_nav_projection_seed,
    build_p2_2_c_local_navigation_context_result,
    build_p2_2_d_local_navigation_integration_tail_result,
    build_p2_2_d_side_effect_proof,
    build_p2_2_local_navigation_api_contract_shape,
    build_p2_2_local_navigation_cli_inspect_contract,
    build_p2_2_local_navigation_docs_state_sync,
    build_p2_2_local_navigation_event_contract_shape,
    build_p2_2_local_navigation_exit_seal,
    build_p2_2_local_navigation_integration_snapshot,
    build_p2_2_local_navigation_projection_contract,
    build_p2_2_local_navigation_shell_binding_contract,
    build_p2_2_local_navigation_tui_binding_status,
    build_p2_3_readiness_result,
    serialize_p2_2_d_result,
)
from agentic_runtime.aurel_shell.surface_registry import CANONICAL_SURFACE_ORDER


def test_aurel_shell_module_imports_p2_2_d() -> None:
    import agentic_runtime.aurel_shell.local_navigation_integration_tail  # noqa: F401


def test_p2_2_d_dependency_constants() -> None:
    assert P2_2_D_PACK_ID == "P2.2-D"
    assert AUDIT_REPAIR_001_PACK_ID in P2_2_D_DEPENDENCY_PACKS
    assert P2_2_C_PACK_ID in P2_2_D_DEPENDENCY_PACKS
    assert P2_2_D_PACK_CHECKPOINT_IDS == (
        "P2.2.16",
        "P2.2.17",
        "P2.2.18",
        "P2.2.19",
        "P2.2.20",
    )


def test_p2_2_d_audit_repair_and_p2_2_c_dependencies() -> None:
    p2_2_c = build_p2_2_c_local_navigation_context_result()
    result = build_p2_2_d_local_navigation_integration_tail_result()
    assert AUDIT_REPAIR_001_REPORT_FILENAME in result.audit_repair_ref
    assert P2_2_C_REPORT_FILENAME in result.integration_snapshot.context_ref
    assert P2_2_A_REPORT_FILENAME in result.integration_snapshot.foundation_ref
    assert P2_2_B_REPORT_FILENAME in result.integration_snapshot.hierarchy_ref
    assert_p2_2_d_depends_on_audit_repair_001(result)
    assert_p2_2_d_depends_on_p2_2_c(result, p2_2_c)


def test_p2_2_d_does_not_start_p2_3_or_p2_4() -> None:
    readiness = build_p2_3_readiness_result()
    assert readiness.starts_p2_3 is False
    assert readiness.ready_for_implementation is False
    assert_p2_3_readiness_does_not_start_p2_3(readiness)
    assert_p2_2_d_does_not_start_p2_3(readiness)
    assert_p2_2_d_does_not_start_p2_4(readiness)


def test_p2_2_16_integration_snapshot_builds_serializes_and_reuses_a_b_c() -> None:
    foundation = build_local_nav_projection_seed()
    hierarchy = build_local_nav_hierarchy_projection_result(foundation=foundation)
    context = build_local_nav_context_projection_result(
        foundation=foundation,
        hierarchy_projection=hierarchy,
    )
    snapshot = build_p2_2_local_navigation_integration_snapshot(
        foundation=foundation,
        hierarchy=hierarchy,
        context=context,
    )
    assert snapshot.section_id == "P2.2"
    assert snapshot.created_for_pack == "P2.2-D"
    assert snapshot.foundation_ref
    assert snapshot.hierarchy_ref
    assert snapshot.context_ref
    assert snapshot.ownership_summary
    assert snapshot.registry_summary
    assert snapshot.item_summary
    assert snapshot.visibility_availability_summary
    assert snapshot.hierarchy_summary
    assert snapshot.ordering_summary
    assert snapshot.selection_summary
    assert snapshot.interaction_summary
    assert snapshot.context_summary
    assert snapshot.profile_summary
    assert snapshot.restoration_summary
    assert snapshot.degraded_profile_summary
    assert snapshot.truth_boundary_summary
    assert snapshot.side_effect_summary
    assert json.loads(json.dumps(snapshot.to_canonical_dict()))
    assert_p2_2_a_b_c_outputs_reused(snapshot, foundation, hierarchy, context)


def test_p2_2_16_snapshot_is_read_model_only() -> None:
    snapshot = build_p2_2_local_navigation_integration_snapshot()
    assert snapshot.is_source_of_truth is False
    assert snapshot.is_ui is False
    assert snapshot.creates_sidebar is False
    assert snapshot.creates_global_left_nav is False
    assert snapshot.mutates_runtime is False
    assert snapshot.writes_memory is False
    assert snapshot.writes_trace is False
    assert_p2_2_integration_snapshot_is_not_source_of_truth(snapshot)
    assert_p2_2_integration_snapshot_is_not_ui(snapshot)


def test_p2_2_17_projection_contract_builds_serializes_and_refs_snapshot() -> None:
    snapshot = build_p2_2_local_navigation_integration_snapshot()
    contract = build_p2_2_local_navigation_projection_contract(snapshot=snapshot)
    assert contract.projection_version == "v1"
    assert contract.foundation_contract_ref == snapshot.foundation_ref
    assert contract.hierarchy_contract_ref == snapshot.hierarchy_ref
    assert contract.context_contract_ref == snapshot.context_ref
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_2_17_api_contract_is_shape_only() -> None:
    api_contract = build_p2_2_local_navigation_api_contract_shape()
    assert api_contract.unavailable_reason
    assert api_contract.is_server is False
    assert api_contract.creates_http_routes is False
    assert api_contract.handles_http_requests is False
    assert_p2_2_projection_contract_is_not_api_server(api_contract)


def test_p2_2_17_event_contract_is_shape_only() -> None:
    event_contract = build_p2_2_local_navigation_event_contract_shape()
    assert event_contract.unavailable_reason
    assert event_contract.is_event_bus is False
    assert event_contract.emits_runtime_events is False
    assert event_contract.publishes_events is False
    assert event_contract.subscribes_events is False
    assert_p2_2_event_contract_is_not_event_bus(event_contract)
    assert_p2_2_event_contract_does_not_emit_runtime_events(event_contract)


def test_p2_2_17_projection_contract_has_no_runtime_side_effects() -> None:
    contract = build_p2_2_local_navigation_projection_contract()
    assert contract.creates_ui is False
    assert contract.creates_api_server is False
    assert contract.creates_http_routes is False
    assert contract.creates_event_bus is False
    assert contract.emits_runtime_events is False
    assert contract.mutates_runtime is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False


def test_p2_2_18_shell_binding_contract_builds_serializes() -> None:
    binding = build_p2_2_local_navigation_shell_binding_contract()
    assert binding.section_id == "P2.2"
    assert binding.executes_routes is False
    assert binding.mutates_runtime is False
    assert binding.writes_memory is False
    assert binding.writes_trace is False
    assert binding.creates_interactive_tui is False
    assert binding.creates_product_ui is False
    assert json.loads(json.dumps(binding.to_canonical_dict()))


def test_p2_2_18_cli_inspect_is_read_only_if_available() -> None:
    cli = build_p2_2_local_navigation_cli_inspect_contract()
    if cli.cli_inspect_available:
        assert cli.cli_inspect_read_only is True
        assert cli.cli_inspect_command
    assert_p2_2_cli_inspect_is_read_only(cli)


def test_p2_2_18_tui_binding_unavailable_with_reason() -> None:
    tui = build_p2_2_local_navigation_tui_binding_status()
    assert tui.tui_binding_available is False
    assert tui.tui_unavailable_reason
    assert_p2_2_tui_binding_unavailable_has_reason(tui)


def test_p2_2_19_docs_state_sync_builds_serializes() -> None:
    sync = build_p2_2_local_navigation_docs_state_sync()
    assert sync.section_id == "P2.2"
    assert sync.report_path
    assert sync.report_index_updated is True
    assert sync.roadmap_canon_rewritten is False
    assert_p2_2_docs_sync_does_not_rewrite_roadmap_canon(sync)
    assert json.loads(json.dumps(sync.to_canonical_dict()))


def test_p2_2_20_exit_seal_builds_serializes() -> None:
    seal = build_p2_2_local_navigation_exit_seal()
    assert seal.section_id == "P2.2"
    assert seal.seal_value == P22LocalNavigationSealDecision.SEALED_FOR_P2_2_CONTRACT_SCOPE
    assert seal.sealed_for_contract_scope is True
    assert seal.contract_scope_only is True
    assert seal.production_live_claimed is False
    assert seal.trace_verified_claimed is False
    assert seal.release_scope_claimed is False
    assert seal.ui_claimed is False
    assert seal.route_runtime_claimed is False
    assert seal.api_server_claimed is False
    assert seal.event_bus_claimed is False
    assert seal.memory_write_claimed is False
    assert seal.trace_write_claimed is False
    assert seal.runtime_mutation_claimed is False
    assert_p2_2_exit_seal_is_contract_scope_only(seal)
    assert_p2_2_exit_seal_is_not_release_scope(seal)
    assert json.loads(json.dumps(seal.to_canonical_dict()))


def test_p2_2_20_p2_3_readiness_builds_serializes() -> None:
    readiness = build_p2_3_readiness_result()
    assert readiness.from_section_id == "P2.2"
    assert readiness.to_section_id == "P2.3"
    assert readiness.readiness_value == P22P23ReadinessDecision.READY_FOR_P2_3_PLAN
    assert readiness.ready_for_plan is True
    assert readiness.ready_for_implementation is False
    assert readiness.starts_p2_3 is False
    assert readiness.implements_floating_windows is False
    assert readiness.implements_workspace_state is False
    assert readiness.implements_command_palette is False
    assert readiness.authorizes_release is False
    assert json.loads(json.dumps(readiness.to_canonical_dict()))


def test_p2_2_d_side_effect_proof_all_false() -> None:
    proof = build_p2_2_d_side_effect_proof()
    for field, value in proof.to_canonical_dict().items():
        assert value is False, field


def test_p2_2_d_pack_result_serializes_and_preserves_surfaces() -> None:
    result = build_p2_2_d_local_navigation_integration_tail_result()
    assert result.pack_id == "P2.2-D"
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert result.next_pack == "P2.3-A"
    assert len(result.checkpoint_reads) == 5
    assert all(
        result.checkpoint_statuses[checkpoint_id] == "DONE"
        for checkpoint_id in P2_2_D_PACK_CHECKPOINT_IDS
    )
    assert json.loads(serialize_p2_2_d_result(result))
