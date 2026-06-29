"""Tests for P2.1-D topbar integration tail / section seal."""

from __future__ import annotations

import json

from agentic_runtime.aurel_shell import (
    P2_1_D_DEPENDENCY_PACKS,
    P2_1_D_NEXT_RECOMMENDED_PACK,
    P2_1_D_NEXT_SECTION,
    P2_1_D_PACK_CHECKPOINT_IDS,
    P2_1_D_PACK_ID,
    P21P22ReadinessDecision,
    P21TopbarSealDecision,
    assert_cli_binding_does_not_execute_routes,
    assert_cli_binding_does_not_switch_surfaces,
    assert_cli_binding_is_read_only_or_unavailable,
    assert_docs_sync_does_not_promote_old_taxonomy,
    assert_docs_sync_does_not_rewrite_roadmap,
    assert_event_contract_does_not_emit_runtime_event,
    assert_event_contract_is_not_event_bus,
    assert_exit_seal_does_not_claim_live,
    assert_exit_seal_does_not_claim_release_scope,
    assert_exit_seal_does_not_claim_trace_verified,
    assert_exit_seal_is_contract_scope_only,
    assert_integration_snapshot_is_not_source_of_truth,
    assert_integration_snapshot_reuses_p2_1_a_b_c,
    assert_p2_1_d_depends_on_p2_1_c,
    assert_p2_1_d_does_not_start_p2_2,
    assert_p2_2_readiness_is_plan_only,
    assert_projection_contract_is_not_api_server,
    assert_tui_binding_available_or_unavailable_with_reason,
    assert_unavailable_bindings_have_reasons,
    build_p2_1_c_topbar_route_visibility_result,
    build_p2_1_d_side_effect_proof,
    build_p2_1_d_topbar_integration_tail_result,
    build_p2_1_docs_state_report_sync,
    build_p2_1_topbar_api_contract_shape,
    build_p2_1_topbar_capability_map,
    build_p2_1_topbar_cli_inspect_contract,
    build_p2_1_topbar_event_contract_shape,
    build_p2_1_topbar_exit_seal,
    build_p2_1_topbar_integration_snapshot,
    build_p2_1_topbar_projection_contract,
    build_p2_1_topbar_shell_binding_contract,
    build_p2_1_topbar_tui_binding_status,
    build_p2_2_readiness_result,
    serialize_p2_1_d_result,
)


def test_aurel_shell_module_imports_p2_1_d() -> None:
    import agentic_runtime.aurel_shell.topbar_integration_tail  # noqa: F401


def test_p2_1_d_dependency_constants() -> None:
    assert P2_1_D_PACK_ID == "P2.1-D"
    assert P2_1_D_DEPENDENCY_PACKS == ("P2.1-A", "P2.1-B", "P2.1-C")
    assert P2_1_D_PACK_CHECKPOINT_IDS == (
        "P2.1.16",
        "P2.1.17",
        "P2.1.18",
        "P2.1.19",
        "P2.1.20",
    )


def test_p2_1_d_depends_on_p2_1_c_result() -> None:
    p2_1_c = build_p2_1_c_topbar_route_visibility_result()
    assert p2_1_c.next_pack == "P2.1-D"
    assert_p2_1_d_depends_on_p2_1_c(p2_1_c)


def test_p2_1_16_integration_snapshot_builds_serializes_and_reuses_a_b_c() -> None:
    snapshot = build_p2_1_topbar_integration_snapshot()
    assert snapshot.section_id == "P2.1"
    assert snapshot.section_name == "Global Topbar / Surface Registry"
    assert snapshot.covered_packs == ("P2.1-A", "P2.1-B", "P2.1-C", "P2.1-D")
    assert snapshot.registry_ref
    assert snapshot.topbar_read_model_ref
    assert snapshot.status_projection_ref
    assert snapshot.route_visibility_projection_ref
    assert snapshot.p2_1_a_result_ref
    assert snapshot.p2_1_b_result_ref
    assert snapshot.p2_1_c_result_ref
    assert json.loads(json.dumps(snapshot.to_canonical_dict()))
    assert_integration_snapshot_reuses_p2_1_a_b_c(snapshot)


def test_p2_1_16_snapshot_has_taxonomy_truth_side_effect_and_unavailable_reasons() -> None:
    snapshot = build_p2_1_topbar_integration_snapshot()
    assert snapshot.taxonomy_drift_summary["surface_taxonomy_drift"] == "true"
    assert snapshot.taxonomy_drift_summary["old_taxonomy_promoted"] == "false"
    assert snapshot.truth_boundary_summary["is_source_of_truth"] == "false"
    assert snapshot.side_effect_summary["ui_created"] == "false"
    assert snapshot.unavailable_bindings
    assert_unavailable_bindings_have_reasons(snapshot.unavailable_bindings)


def test_p2_1_16_snapshot_is_read_model_only() -> None:
    snapshot = build_p2_1_topbar_integration_snapshot()
    assert snapshot.is_source_of_truth is False
    assert snapshot.is_live_ui is False
    assert snapshot.creates_ui is False
    assert snapshot.mutates_runtime is False
    assert snapshot.writes_memory is False
    assert snapshot.writes_trace is False
    assert_integration_snapshot_is_not_source_of_truth(snapshot)


def test_p2_1_16_capability_map_covers_p2_1_0_to_p2_1_20() -> None:
    capability_map = build_p2_1_topbar_capability_map()
    assert capability_map.checkpoint_coverage[0] == "P2.1.0"
    assert capability_map.checkpoint_coverage[-1] == "P2.1.20"
    assert len(capability_map.checkpoint_coverage) == 21
    assert not capability_map.missing_capabilities
    assert not capability_map.partial_capabilities
    assert capability_map.unavailable_bindings
    assert json.loads(json.dumps(capability_map.to_canonical_dict()))
    assert_unavailable_bindings_have_reasons(capability_map.unavailable_bindings)


def test_p2_1_17_projection_contract_builds_serializes_and_refs_snapshot() -> None:
    snapshot = build_p2_1_topbar_integration_snapshot()
    contract = build_p2_1_topbar_projection_contract(snapshot=snapshot)
    assert contract.projection_version == "v1"
    assert contract.integration_snapshot_ref == snapshot.snapshot_hash
    assert contract.registry_contract_ref == snapshot.registry_ref
    assert contract.status_contract_ref == snapshot.status_projection_ref
    assert contract.route_visibility_contract_ref == snapshot.route_visibility_projection_ref
    assert json.loads(json.dumps(contract.to_canonical_dict()))


def test_p2_1_17_api_contract_is_shape_only() -> None:
    api_contract = build_p2_1_topbar_api_contract_shape(projection_ref="snapshot")
    assert api_contract.unavailable_reason
    assert api_contract.api_server_created is False
    assert api_contract.http_route_created is False
    assert api_contract.mutates_runtime is False
    assert_projection_contract_is_not_api_server(api_contract)


def test_p2_1_17_event_contract_is_shape_only() -> None:
    event_contract = build_p2_1_topbar_event_contract_shape(projection_ref="snapshot")
    assert event_contract.unavailable_reason
    assert event_contract.event_bus_created is False
    assert event_contract.runtime_event_emitted is False
    assert event_contract.mutates_runtime is False
    assert event_contract.writes_trace is False
    assert_event_contract_is_not_event_bus(event_contract)
    assert_event_contract_does_not_emit_runtime_event(event_contract)


def test_p2_1_17_projection_does_not_create_server_bus_or_truth() -> None:
    contract = build_p2_1_topbar_projection_contract()
    assert contract.api_server_created is False
    assert contract.http_route_created is False
    assert contract.event_bus_created is False
    assert contract.runtime_event_emitted is False
    assert contract.is_source_of_truth is False
    assert_unavailable_bindings_have_reasons(contract.unavailable_bindings)


def test_p2_1_18_cli_inspect_contract_is_read_only() -> None:
    cli = build_p2_1_topbar_cli_inspect_contract(projection_ref="projection")
    assert cli.cli_inspect_available is True
    assert cli.cli_commands
    assert cli.is_read_only is True
    assert cli.executes_routes is False
    assert cli.switches_surfaces is False
    assert cli.mutates_runtime is False
    assert cli.writes_memory is False
    assert cli.writes_trace is False
    assert cli.creates_live_cli_product is False
    assert_cli_binding_is_read_only_or_unavailable(cli)
    assert_cli_binding_does_not_execute_routes(cli)
    assert_cli_binding_does_not_switch_surfaces(cli)


def test_p2_1_18_tui_binding_is_unavailable_with_reason() -> None:
    tui = build_p2_1_topbar_tui_binding_status(projection_ref="projection")
    assert tui.tui_binding_available is False
    assert tui.tui_unavailable_reason
    assert tui.is_read_only is True
    assert tui.executes_routes is False
    assert tui.switches_surfaces is False
    assert tui.mutates_runtime is False
    assert tui.writes_memory is False
    assert tui.writes_trace is False
    assert tui.creates_tui_product is False
    assert_tui_binding_available_or_unavailable_with_reason(tui)


def test_p2_1_18_shell_binding_contract_builds_and_serializes() -> None:
    binding = build_p2_1_topbar_shell_binding_contract()
    assert binding.shell_binding_available is True
    assert binding.cli_inspect_available is True
    assert binding.tui_binding_available is False
    assert binding.tui_unavailable_reason
    assert binding.is_read_only is True
    assert binding.executes_routes is False
    assert binding.switches_surfaces is False
    assert binding.mutates_runtime is False
    assert binding.writes_memory is False
    assert binding.writes_trace is False
    assert binding.creates_live_cli_product is False
    assert binding.creates_tui_product is False
    assert json.loads(json.dumps(binding.to_canonical_dict()))


def test_p2_1_19_docs_state_report_sync_builds_and_does_not_rewrite() -> None:
    sync = build_p2_1_docs_state_report_sync()
    result = sync.docs_sync_result
    assert result.report_created is True
    assert result.report_path == "agent/reports/P2_1_D_TOPBAR_INTEGRATION_TAIL.md"
    assert result.report_indexed is True
    assert result.active_task_updated is True
    assert result.roadmap_progress_updated is True
    assert result.state_updated is True
    assert result.decisions_updated is True
    assert result.tests_updated is True
    assert result.architecture_updated is True
    assert result.roadmap_rewritten is False
    assert result.old_taxonomy_promoted is False
    assert sync.next_task_points_to_p2_2_planning is True
    assert sync.p2_2_implementation_started is False
    assert json.loads(json.dumps(sync.to_canonical_dict()))
    assert_docs_sync_does_not_rewrite_roadmap(result)
    assert_docs_sync_does_not_promote_old_taxonomy(result)


def test_p2_1_20_exit_seal_builds_contract_scope_only() -> None:
    seal = build_p2_1_topbar_exit_seal()
    assert seal.seal_decision is P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE
    assert seal.sealed_scope == "CONTRACT_SCOPE"
    assert seal.ready_for_next_section is True
    assert seal.next_section == "P2.2"
    assert seal.p2_2_readiness_decision is P21P22ReadinessDecision.READY_FOR_P2_2_PLAN
    assert seal.p2_1_a_evidence_checked is True
    assert seal.p2_1_b_evidence_checked is True
    assert seal.p2_1_c_evidence_checked is True
    assert seal.p2_1_d_evidence_checked is True
    assert json.loads(json.dumps(seal.to_canonical_dict()))
    assert_exit_seal_is_contract_scope_only(seal)


def test_p2_1_20_exit_seal_does_not_claim_live_trace_release_or_runtime() -> None:
    seal = build_p2_1_topbar_exit_seal()
    assert seal.production_live_claimed is False
    assert seal.trace_verified_claimed is False
    assert seal.release_scope_claimed is False
    assert seal.visual_topbar_implemented is False
    assert seal.local_navigation_implemented is False
    assert seal.route_runtime_implemented is False
    assert seal.api_server_created is False
    assert seal.event_bus_created is False
    assert seal.p2_2_started is False
    assert_exit_seal_does_not_claim_live(seal)
    assert_exit_seal_does_not_claim_trace_verified(seal)
    assert_exit_seal_does_not_claim_release_scope(seal)


def test_p2_1_20_p2_2_readiness_is_plan_only() -> None:
    readiness = build_p2_2_readiness_result()
    assert readiness.next_section == "P2.2"
    assert readiness.next_pack_recommendation == "P2.2-A"
    assert readiness.p2_2_readiness_decision is P21P22ReadinessDecision.READY_FOR_P2_2_PLAN
    assert readiness.readiness_is_plan_only is True
    assert readiness.p2_2_started is False
    assert readiness.p2_2_implemented is False
    assert readiness.local_navigation_implemented is False
    assert json.loads(json.dumps(readiness.to_canonical_dict()))
    assert_p2_2_readiness_is_plan_only(readiness)
    assert_p2_1_d_does_not_start_p2_2(readiness)


def test_pack_result_covers_tail_and_next_section_without_starting_p2_2() -> None:
    result = build_p2_1_d_topbar_integration_tail_result()
    assert result.pack_id == "P2.1-D"
    assert result.section_id == "P2.1"
    assert result.covered_checkpoints == P2_1_D_PACK_CHECKPOINT_IDS
    assert result.dependency_packs == ("P2.1-A", "P2.1-B", "P2.1-C")
    assert result.next_section == P2_1_D_NEXT_SECTION
    assert result.next_recommended_pack == P2_1_D_NEXT_RECOMMENDED_PACK
    assert result.exit_seal.seal_decision is P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE
    assert result.p2_2_readiness.p2_2_started is False
    assert json.loads(serialize_p2_1_d_result(result))


def test_pack_result_checkpoint_statuses_are_done() -> None:
    result = build_p2_1_d_topbar_integration_tail_result()
    assert result.checkpoint_statuses == {
        "P2.1.16": "DONE",
        "P2.1.17": "DONE",
        "P2.1.18": "DONE",
        "P2.1.19": "DONE",
        "P2.1.20": "DONE",
    }
    for read in result.checkpoint_reads:
        assert read.evidence
        assert read.tests
        assert read.truth_label
        assert read.unavailable_reason
        assert read.limitations


def test_side_effect_proof_false_for_forbidden_work() -> None:
    proof = build_p2_1_d_side_effect_proof()
    payload = proof.to_canonical_dict()
    assert payload
    assert all(value is False for value in payload.values())
    assert proof.ui_created is False
    assert proof.frontend_component_created is False
    assert proof.frontend_route_created is False
    assert proof.web_client_created is False
    assert proof.desktop_client_created is False
    assert proof.mobile_client_created is False
    assert proof.cli_live_product_created is False
    assert proof.tui_product_created is False
    assert proof.route_runtime_created is False
    assert proof.route_handler_created is False
    assert proof.local_navigation_created is False
    assert proof.command_palette_created is False
    assert proof.api_server_created is False
    assert proof.http_route_created is False
    assert proof.event_bus_created is False
    assert proof.runtime_event_emitted is False
    assert proof.permission_enforcement_created is False
    assert proof.custos_integration_created is False
    assert proof.memory_written is False
    assert proof.trace_written is False
    assert proof.runtime_mutated is False
    assert proof.roadmap_rewritten is False
    assert proof.registry_truth_mutated is False
    assert proof.surface_promoted is False
    assert proof.production_live_claimed is False
    assert proof.trace_verified_claimed is False
    assert proof.release_scope_claimed is False
    assert proof.p2_2_started is False
