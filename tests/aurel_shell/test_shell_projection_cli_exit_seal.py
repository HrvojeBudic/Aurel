"""Tests for P2.0-F projection / API / event / CLI / docs / exit seal."""

from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_shell import (
    CANONICAL_SURFACE_ORDER,
    P2_0_F_DEPENDENCY_PACKS,
    P2_0_F_NEXT_STEP,
    P2_0_F_PACK_CHECKPOINT_IDS,
    P2_0_F_PACK_ID,
    P20ExitSealDecision,
    P20ExitSealScope,
    P20LiveDemoStatus,
    P20ReadinessForP21Decision,
    P20ScopeSealStatus,
    ShellAPIRuntimeStatus,
    ShellBindingStatus,
    ShellEventRuntimeStatus,
    ShellProjectionStatus,
    assert_api_contract_is_not_server,
    assert_cli_does_not_execute,
    assert_cli_inspect_is_read_only,
    assert_docs_do_not_fake_proof,
    assert_docs_do_not_override_roadmap_canon,
    assert_event_contract_is_not_emitted_runtime_event,
    assert_no_event_bus_created,
    assert_no_http_routes_created,
    assert_p2_1_not_started,
    assert_p2_1_readiness_is_review_only,
    assert_p2_contract_scope_seals_separately,
    assert_production_live_scope_requires_live_path,
    assert_projection_does_not_mutate_runtime,
    assert_projection_is_not_source_of_truth,
    assert_projection_is_read_model_only,
    assert_release_scope_not_allowed_on_fixtures_only,
    assert_seal_honest,
    assert_trace_verified_scope_requires_actual_verification,
    assert_tui_status_explicit,
    build_default_surface_registry,
    build_p2_0_docs_state_report_update,
    build_p2_0_exit_seal,
    build_p2_0_exit_seal_checklist,
    build_p2_0_f_projection_cli_exit_seal_result,
    build_p2_0_live_integration_demo_result,
    build_p2_0_readiness_for_p2_1_review,
    build_shell_api_contract,
    build_shell_api_endpoint_contract,
    build_shell_cli_binding_contract,
    build_shell_event_contract,
    build_shell_event_payload_contract,
    build_shell_inspect_command_contract,
    build_shell_projection_contract,
    build_shell_projection_payload,
    build_shell_projection_read_model,
    build_shell_tui_binding_contract,
    derive_p2_0_exit_seal_decision,
    handle_shell_cli_inspect,
    serialize_p2_0_f_result,
    serialize_shell_api_contract,
    serialize_shell_cli_binding_contract,
    serialize_shell_event_contract,
    serialize_shell_projection_payload,
)
from agentic_runtime.aurel_shell.projection import (
    FORBIDDEN_P2_0_F_TRUTH_LABELS,
    P20FSideEffectProof,
)


# ---------------------------------------------------------------------------
# Dispatch / dependency
# ---------------------------------------------------------------------------


def test_aurel_shell_module_imports_p2_0_f() -> None:
    import agentic_runtime.aurel_shell.api_contract  # noqa: F401
    import agentic_runtime.aurel_shell.cli_binding  # noqa: F401
    import agentic_runtime.aurel_shell.event_contract  # noqa: F401
    import agentic_runtime.aurel_shell.exit_seal  # noqa: F401
    import agentic_runtime.aurel_shell.projection  # noqa: F401


def test_p2_0_f_dependency_constants() -> None:
    assert P2_0_F_PACK_ID == "P2.0-F"
    assert P2_0_F_DEPENDENCY_PACKS == (
        "P2.0-A",
        "P2.0-B",
        "P2.0-C",
        "P2.0-D",
        "P2.0-E",
    )
    assert P2_0_F_PACK_CHECKPOINT_IDS == (
        "P2.0.27",
        "P2.0.28",
        "P2.0.29",
        "P2.0.30",
    )


def test_p2_0_f_uses_p2_0_a_registry_not_duplicate_list() -> None:
    registry = build_default_surface_registry()
    read_model = build_shell_projection_read_model()
    assert read_model.canonical_surface_ids == registry.canonical_surface_ids
    assert read_model.canonical_surface_ids == tuple(CANONICAL_SURFACE_ORDER)
    assert registry.surface_count == 7


def test_p2_0_f_projection_reflects_a_through_e_summaries() -> None:
    read_model = build_shell_projection_read_model()
    # Every dependency-pack summary surfaces through the projection read model.
    assert read_model.surface_registry_summary["surface_count"] == "7"
    assert read_model.navigation_boundary_summary["logo_routes_to"] == "aurel_cro"
    assert read_model.continuity_summary
    assert read_model.truth_label_summary
    assert read_model.permission_matrix_summary
    assert read_model.unavailable_state_summary
    assert read_model.fixture_disclosure_summary
    assert read_model.operator_demo_summary
    assert read_model.client_consistency_summary
    assert read_model.regression_harness_summary
    assert read_model.readiness_summary


# ---------------------------------------------------------------------------
# P2.0.27 projection / API / event
# ---------------------------------------------------------------------------


def test_p2_0_27_projection_contract_builds_and_serializes() -> None:
    contract = build_shell_projection_contract()
    assert contract.projection_status is ShellProjectionStatus.PROJECTION_ONLY
    payload = serialize_shell_projection_payload(contract)
    assert json.loads(payload)
    rt = serialize_shell_projection_payload(contract.projection_payload)
    assert json.loads(rt)


def test_p2_0_27_projection_is_read_model_only_not_source_of_truth() -> None:
    payload = build_shell_projection_payload()
    assert payload.is_read_model is True
    assert payload.is_source_of_truth is False
    assert payload.read_model.is_read_model is True
    assert payload.read_model.is_source_of_truth is False
    assert_projection_is_read_model_only(payload)
    assert_projection_is_not_source_of_truth(payload)


def test_p2_0_27_projection_does_not_mutate_runtime_memory_trace() -> None:
    payload = build_shell_projection_payload()
    assert payload.mutates_runtime is False
    assert payload.writes_memory is False
    assert payload.writes_trace is False
    assert_projection_does_not_mutate_runtime(payload)


def test_p2_0_27_api_contract_is_not_server_no_http_route() -> None:
    contract = build_shell_api_contract()
    assert contract.runtime_status is ShellAPIRuntimeStatus.UNAVAILABLE_API_RUNTIME
    assert contract.is_api_server is False
    assert contract.creates_http_route is False
    assert contract.handles_network_request is False
    assert contract.mutates_runtime is False
    assert contract.authorizes_action is False
    assert_api_contract_is_not_server(contract)
    assert_no_http_routes_created(contract)
    assert json.loads(serialize_shell_api_contract(contract))


def test_p2_0_27_api_endpoint_contract_serializes() -> None:
    endpoint = build_shell_api_endpoint_contract(projection_ref="abc")
    assert endpoint.is_api_server is False
    assert endpoint.creates_http_route is False
    assert endpoint.response_contract.projection_ref == "abc"
    assert json.loads(json.dumps(endpoint.to_canonical_dict()))


def test_p2_0_27_event_contract_is_not_emitted_no_event_bus() -> None:
    contract = build_shell_event_contract()
    assert contract.runtime_status is ShellEventRuntimeStatus.UNAVAILABLE_EVENT_RUNTIME
    assert contract.is_runtime_event is False
    assert contract.event_emitted is False
    assert contract.event_bus_created is False
    assert contract.mutates_runtime is False
    assert contract.writes_trace is False
    assert_event_contract_is_not_emitted_runtime_event(contract)
    assert_no_event_bus_created(contract)
    assert json.loads(serialize_shell_event_contract(contract))


def test_p2_0_27_event_payload_contract_serializes() -> None:
    payload = build_shell_event_payload_contract(projection_ref="xyz")
    assert payload.event_emitted is False
    assert payload.is_runtime_event is False
    assert payload.projection_ref == "xyz"
    assert json.loads(json.dumps(payload.to_canonical_dict()))


# ---------------------------------------------------------------------------
# P2.0.28 CLI / TUI binding
# ---------------------------------------------------------------------------


def test_p2_0_28_cli_binding_is_read_only() -> None:
    contract = build_shell_cli_binding_contract()
    assert contract.binding_status is ShellBindingStatus.READ_ONLY_CONTRACT
    assert contract.is_read_only is True
    assert contract.executes_action is False
    assert contract.mutates_runtime is False
    assert contract.grants_permission is False
    assert contract.starts_workflow is False
    assert contract.writes_memory is False
    assert contract.writes_trace is False
    assert_cli_inspect_is_read_only(contract)
    assert_cli_does_not_execute(contract)
    assert json.loads(serialize_shell_cli_binding_contract(contract))


def test_p2_0_28_inspect_command_contract_serializes_read_only() -> None:
    command = build_shell_inspect_command_contract(projection_ref="ref")
    assert command.is_read_only is True
    assert command.executes_action is False
    assert command.mutates_runtime is False
    assert json.loads(json.dumps(command.to_canonical_dict()))


def test_p2_0_28_cli_inspect_handler_is_read_only_no_authority() -> None:
    result = handle_shell_cli_inspect()
    assert result["read_only"] is True
    assert result["authority_granted"] is False
    assert result["executed"] is False
    assert result["mutated_runtime"] is False
    assert result["started_workflow"] is False


def test_p2_0_28_tui_binding_is_unavailable_with_reason() -> None:
    contract = build_shell_tui_binding_contract()
    assert contract.binding_status is ShellBindingStatus.UNAVAILABLE
    assert contract.unavailable_reason
    assert contract.next_action
    assert contract.truth_label == "TUI_UNAVAILABLE"
    assert_tui_status_explicit(contract)
    assert json.loads(serialize_shell_cli_binding_contract(contract))


def test_p2_0_28_tui_does_not_create_live_product() -> None:
    contract = build_shell_tui_binding_contract()
    assert contract.side_effects.live_tui_product_created is False
    assert contract.side_effects.ui_created is False


# ---------------------------------------------------------------------------
# P2.0.29 docs / state / report sync
# ---------------------------------------------------------------------------


def test_p2_0_29_docs_update_builds_and_serializes() -> None:
    update = build_p2_0_docs_state_report_update()
    assert update.report_path.endswith("P2_0_F_PROJECTION_CLI_EXIT_SEAL.md")
    assert json.loads(json.dumps(update.to_canonical_dict()))


def test_p2_0_29_docs_update_does_not_override_roadmap_canon() -> None:
    update = build_p2_0_docs_state_report_update()
    assert update.roadmap_canon_overridden is False
    assert update.state_sync_summary.roadmap_canon_overridden is False
    assert_docs_do_not_override_roadmap_canon(update)


def test_p2_0_29_docs_update_does_not_fake_proof_or_live() -> None:
    update = build_p2_0_docs_state_report_update()
    assert update.truth_label not in FORBIDDEN_P2_0_F_TRUTH_LABELS
    assert update.validation_recorded is True
    assert_docs_do_not_fake_proof(update)


def test_p2_0_29_report_present_and_indexed() -> None:
    update = build_p2_0_docs_state_report_update()
    assert update.report_index_updated is True
    assert all(entry.present_on_disk for entry in update.report_entries)
    assert all(entry.indexed for entry in update.report_entries)


# ---------------------------------------------------------------------------
# P2.0.30 exit seal + live demo + P2.1 readiness
# ---------------------------------------------------------------------------


def test_p2_0_30_exit_seal_builds_and_seals_contract_scope() -> None:
    seal = build_p2_0_exit_seal()
    assert seal.exit_seal_decision is P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE
    assert seal.truth_label == "SEALED_FOR_P2_CONTRACT_SCOPE"
    assert seal.contract_scope_decision is P20ScopeSealStatus.SEALED
    assert_seal_honest(seal)


def test_p2_0_30_seal_scopes_are_explicit() -> None:
    seal = build_p2_0_exit_seal()
    assert set(seal.seal_scopes) == {
        "P2_CONTRACT_SCOPE",
        "PRODUCTION_LIVE_SCOPE",
        "TRACE_VERIFIED_SCOPE",
        "RELEASE_SCOPE",
    }


def test_p2_0_30_checklist_serializes_and_has_unavailable_boundaries() -> None:
    checklist = build_p2_0_exit_seal_checklist()
    assert checklist.failed_count == 0
    # production-live, trace-verification, and TUI are explicitly UNAVAILABLE.
    assert checklist.unavailable_count >= 2
    assert json.loads(json.dumps(checklist.to_canonical_dict()))


def test_p2_0_30_production_live_scope_cannot_seal_without_live_path() -> None:
    seal = build_p2_0_exit_seal(seal_scope=P20ExitSealScope.PRODUCTION_LIVE_SCOPE)
    assert seal.exit_seal_decision is P20ExitSealDecision.PARTIAL
    assert seal.production_live_available is False
    assert seal.production_live_scope_decision is not P20ScopeSealStatus.SEALED
    assert_production_live_scope_requires_live_path(seal)


def test_p2_0_30_trace_verified_scope_cannot_seal_without_verification() -> None:
    seal = build_p2_0_exit_seal(seal_scope=P20ExitSealScope.TRACE_VERIFIED_SCOPE)
    assert seal.exit_seal_decision is P20ExitSealDecision.PARTIAL
    assert seal.trace_verification_available is False
    assert seal.trace_verified_scope_decision is not P20ScopeSealStatus.SEALED
    assert_trace_verified_scope_requires_actual_verification(seal)


def test_p2_0_30_release_scope_cannot_seal_on_fixtures_only() -> None:
    seal = build_p2_0_exit_seal(seal_scope=P20ExitSealScope.RELEASE_SCOPE)
    assert seal.exit_seal_decision is P20ExitSealDecision.PARTIAL
    assert seal.release_scope_decision is not P20ScopeSealStatus.SEALED
    assert_release_scope_not_allowed_on_fixtures_only(seal)


def test_p2_0_30_contract_scope_seals_separately_from_production() -> None:
    seal = build_p2_0_exit_seal()
    assert seal.contract_scope_decision is P20ScopeSealStatus.SEALED
    assert seal.production_live_scope_decision is not P20ScopeSealStatus.SEALED
    assert_p2_contract_scope_seals_separately(seal)


def test_p2_0_30_seal_cannot_claim_fake_live() -> None:
    decision, _ = derive_p2_0_exit_seal_decision(
        checklist_passed=False,
        unavailable_count=3,
        live_demo=build_p2_0_live_integration_demo_result(),
        fake_truth_claim_detected=True,
    )
    assert decision is P20ExitSealDecision.NOT_SEALED
    seal = build_p2_0_exit_seal(truth_labels=("LIVE",))
    assert seal.checklist.fake_live_detected is True
    assert seal.exit_seal_decision is P20ExitSealDecision.NOT_SEALED


def test_p2_0_30_seal_cannot_claim_fake_trace_verified() -> None:
    seal = build_p2_0_exit_seal(truth_labels=("TRACE_VERIFIED",))
    assert seal.checklist.fake_trace_verified_detected is True
    assert seal.exit_seal_decision is P20ExitSealDecision.NOT_SEALED


def test_p2_0_30_blocked_when_dependency_reports_missing(tmp_path) -> None:
    # An empty repo root has no dependency reports -> BLOCKED.
    seal = build_p2_0_exit_seal(repo_root=tmp_path)
    assert seal.exit_seal_decision is P20ExitSealDecision.BLOCKED
    assert seal.contract_scope_decision is P20ScopeSealStatus.BLOCKED


def test_p2_0_30_live_demo_truth_boundary_explicit() -> None:
    demo = build_p2_0_live_integration_demo_result()
    assert demo.demo_status is P20LiveDemoStatus.DEV_FIXTURE_TESTED
    assert demo.truth_label == "NOT_LIVE"
    assert demo.live_path_evidence is False
    assert "UNAVAILABLE_LIVE_PATH" in demo.unavailable_reason
    assert demo.demo_passed is True


def test_p2_0_30_live_demo_rejects_fake_live_status() -> None:
    with pytest.raises(ValueError):
        build_p2_0_live_integration_demo_result(demo_status="LIVE_TESTED")
    with pytest.raises(ValueError):
        build_p2_0_live_integration_demo_result(
            demo_status=P20LiveDemoStatus.PRODUCTION_LIVE_TESTED
        )


def test_p2_0_30_live_demo_unavailable_status_has_reason() -> None:
    demo = build_p2_0_live_integration_demo_result(
        demo_status=P20LiveDemoStatus.UNAVAILABLE_LIVE_PATH
    )
    assert demo.demo_passed is False
    assert demo.unavailable_reason
    assert demo.live_path_evidence is False


def test_p2_0_30_p2_1_readiness_review_only_when_sealed() -> None:
    readiness = build_p2_0_readiness_for_p2_1_review(
        P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE
    )
    assert readiness.readiness_decision is P20ReadinessForP21Decision.READY_FOR_P2_1_REVIEW
    assert readiness.is_review_only is True
    assert readiness.starts_p2_1 is False
    assert readiness.authorizes_p2_1_coding is False
    assert_p2_1_readiness_is_review_only(readiness)
    assert_p2_1_not_started(readiness)


def test_p2_0_30_p2_1_readiness_not_ready_when_not_sealed() -> None:
    readiness = build_p2_0_readiness_for_p2_1_review(P20ExitSealDecision.PARTIAL)
    assert readiness.readiness_decision is P20ReadinessForP21Decision.NOT_READY_FOR_P2_1
    assert readiness.authorizes_p2_1_coding is False


def test_p2_0_30_seal_does_not_start_or_authorize_p2_1() -> None:
    seal = build_p2_0_exit_seal()
    assert seal.p2_1_readiness.starts_p2_1 is False
    assert seal.p2_1_readiness.authorizes_p2_1_coding is False
    assert seal.side_effects.p2_1_started is False


# ---------------------------------------------------------------------------
# Pack result + side-effect proof
# ---------------------------------------------------------------------------


def test_pack_result_covers_checkpoints_and_dependencies() -> None:
    result = build_p2_0_f_projection_cli_exit_seal_result()
    assert result.pack_id == "P2.0-F"
    assert result.covered_checkpoints == P2_0_F_PACK_CHECKPOINT_IDS
    assert result.dependency_packs == P2_0_F_DEPENDENCY_PACKS
    assert set(result.checkpoint_statuses.values()) == {"DONE"}


def test_pack_result_next_step_is_omni_review() -> None:
    result = build_p2_0_f_projection_cli_exit_seal_result()
    assert result.next_recommended_step == P2_0_F_NEXT_STEP
    assert "OMNI review" in result.next_recommended_step


def test_pack_result_serializes() -> None:
    result = build_p2_0_f_projection_cli_exit_seal_result()
    assert json.loads(serialize_p2_0_f_result(result))


def test_pack_result_records_operator_waiver() -> None:
    result = build_p2_0_f_projection_cli_exit_seal_result()
    assert any("P2.0-E OMNI" in waiver for waiver in result.dependency_waivers)


def test_side_effect_proof_all_false() -> None:
    proof = P20FSideEffectProof()
    for field_value in vars(proof).values():
        assert field_value is False
    result = build_p2_0_f_projection_cli_exit_seal_result()
    for field_value in vars(result.side_effect_proof).values():
        assert field_value is False


def test_pack_result_does_not_create_server_bus_or_ui() -> None:
    result = build_p2_0_f_projection_cli_exit_seal_result()
    proof = result.side_effect_proof
    assert proof.api_server_created is False
    assert proof.http_routes_created is False
    assert proof.event_bus_created is False
    assert proof.runtime_events_emitted is False
    assert proof.ui_created is False
    assert proof.live_cli_product_created is False
    assert proof.live_tui_product_created is False


def test_pack_result_no_forbidden_truth_labels() -> None:
    result = build_p2_0_f_projection_cli_exit_seal_result()
    for label in result.truth_labels:
        assert label not in FORBIDDEN_P2_0_F_TRUTH_LABELS
