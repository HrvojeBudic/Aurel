"""Tests for P2.0-E operator demo, snapshot, route harness, readiness."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_runtime.aurel_shell import (
    CANONICAL_SURFACE_ORDER,
    ClientKind,
    P20ReadinessDecision,
    P2_0_E_DEPENDENCY_PACKS,
    P2_0_E_NEXT_PACK,
    P2_0_E_PACK_CHECKPOINT_IDS,
    P2_0_E_PACK_ID,
    assert_client_consistency_does_not_create_clients,
    assert_clients_share_same_registry_truth_permission_unavailable_fixture_contracts,
    assert_logo_routes_to_cro_contract,
    assert_no_universal_left_nav_contract_holds,
    assert_operator_demo_covers_all_surfaces,
    assert_operator_demo_does_not_execute,
    assert_operator_demo_does_not_mutate_runtime,
    assert_operator_demo_is_not_live,
    assert_readiness_does_not_start_p2_0_f,
    assert_readiness_is_not_exit_seal,
    assert_readiness_is_not_live,
    assert_route_harness_does_not_create_runtime_routes,
    assert_route_hub_entry_is_not_tool_execution,
    assert_route_settings_is_not_system,
    assert_settings_is_not_system,
    assert_shell_snapshot_does_not_mutate_runtime,
    assert_shell_snapshot_is_not_source_of_truth,
    assert_shell_snapshot_is_read_model_only,
    assert_shell_snapshot_serializes,
    assert_system_is_not_logo_default_route,
    build_default_surface_registry,
    build_multi_client_consistency_contract,
    build_operator_testable_surface_demo_state,
    build_p2_0_b_navigation_boundary_pack_result,
    build_p2_0_c_floating_window_handoff_context_result,
    build_p2_0_cognitive_os_lock_readiness,
    build_p2_0_d_truth_permission_fixture_result,
    build_p2_0_e_operator_demo_snapshot_regression_result,
    build_shell_state_snapshot,
    build_shell_state_snapshot_contract,
    build_surface_regression_route_test_harness,
    run_surface_regression_route_contract_harness,
    serialize_p2_0_e_result,
    serialize_shell_state_snapshot,
)
from agentic_runtime.aurel_shell.fixture_discipline import SurfaceFixtureKind
from agentic_runtime.aurel_shell.operator_demo import OperatorDemoAvailabilityState
from agentic_runtime.aurel_shell.truth_labels import SurfaceTruthLabel


def test_aurel_shell_module_imports_p2_0_e() -> None:
    import agentic_runtime.aurel_shell.client_consistency  # noqa: F401
    import agentic_runtime.aurel_shell.operator_demo  # noqa: F401
    import agentic_runtime.aurel_shell.readiness  # noqa: F401
    import agentic_runtime.aurel_shell.regression_harness  # noqa: F401
    import agentic_runtime.aurel_shell.shell_snapshot  # noqa: F401


def test_p2_0_e_dependencies_exist_and_hash() -> None:
    registry = build_default_surface_registry()
    p2_0_b = build_p2_0_b_navigation_boundary_pack_result()
    p2_0_c = build_p2_0_c_floating_window_handoff_context_result()
    p2_0_d = build_p2_0_d_truth_permission_fixture_result()
    assert registry.surface_count == 7
    assert p2_0_b.result_hash
    assert p2_0_c.result_hash
    assert p2_0_d.result_hash


def test_p2_0_e_uses_p2_0_a_registry() -> None:
    registry = build_default_surface_registry()
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    assert result.canonical_surface_ids == registry.canonical_surface_ids
    assert result.operator_demo_state.canonical_surface_ids == registry.canonical_surface_ids
    assert result.shell_state_snapshot.surface_registry_summary["surface_count"] == "7"


def test_p2_0_e_respects_p2_0_b_boundaries() -> None:
    result = run_surface_regression_route_contract_harness()
    assert_logo_routes_to_cro_contract(result)
    assert_system_is_not_logo_default_route(result)
    assert_route_settings_is_not_system(result)
    assert_route_hub_entry_is_not_tool_execution(result)
    assert_no_universal_left_nav_contract_holds(result)


def test_p2_0_e_respects_p2_0_c_continuity_semantics() -> None:
    p2_0_c = build_p2_0_c_floating_window_handoff_context_result()
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    assert p2_0_c.side_effect_proof.memory_written is False
    assert p2_0_c.side_effect_proof.runtime_mutated is False
    assert p2_0_c.side_effect_proof.trace_written is False
    assert result.side_effect_proof.memory_written is False
    assert result.side_effect_proof.runtime_mutated is False


def test_p2_0_e_respects_p2_0_d_truth_fixture_discipline() -> None:
    p2_0_d = build_p2_0_d_truth_permission_fixture_result()
    demo = build_operator_testable_surface_demo_state()
    assert p2_0_d.permission_matrix_summary["authorizes_action"] == "false"
    assert p2_0_d.fixture_discipline_summary["is_live"] == "false"
    assert all(card.truth_label is SurfaceTruthLabel.DEV_FIXTURE for card in demo.cards)


def test_p2_0_e_does_not_duplicate_canonical_surface_list_in_production() -> None:
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    assert result.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    repo_root = Path(__file__).resolve().parents[2]
    p2_0_e_sources = (
        "operator_demo.py",
        "client_consistency.py",
        "shell_snapshot.py",
        "regression_harness.py",
        "readiness.py",
    )
    source_text = "\n".join(
        (repo_root / "src/agentic_runtime/aurel_shell" / name).read_text()
        for name in p2_0_e_sources
    )
    assert '("aurel_cro", "hq", "corp", "hub", "ide", "system", "settings")' not in source_text


def test_p2_0_22_operator_demo_state_builds() -> None:
    demo = build_operator_testable_surface_demo_state()
    assert demo.demo_state_exists is True
    assert demo.demo_state_is_operator_testable is True
    assert demo.demo_state_is_dev_fixture is True
    assert demo.demo_state_is_not_live is True


def test_p2_0_22_operator_demo_surface_cards_serialize() -> None:
    demo = build_operator_testable_surface_demo_state()
    for card in demo.cards:
        payload = json.dumps(card.to_canonical_dict(), sort_keys=True)
        parsed = json.loads(payload)
        assert parsed["surface_id"] == card.surface_id
        assert parsed["truth_label"] == SurfaceTruthLabel.DEV_FIXTURE.value


def test_p2_0_22_operator_demo_covers_all_seven_surfaces() -> None:
    demo = build_operator_testable_surface_demo_state()
    assert demo.surface_count == 7
    assert demo.canonical_surface_ids == CANONICAL_SURFACE_ORDER
    assert_operator_demo_covers_all_surfaces(demo)


def test_p2_0_22_operator_demo_is_dev_fixture_contract_not_live() -> None:
    demo = build_operator_testable_surface_demo_state()
    assert demo.truth_boundary.fixture_kind is SurfaceFixtureKind.DEV_FIXTURE
    for card in demo.cards:
        assert card.fixture_kind is SurfaceFixtureKind.DEV_FIXTURE
        assert card.availability_state is OperatorDemoAvailabilityState.OPERATOR_TESTABLE
        assert card.demo_is_live is False
    assert_operator_demo_is_not_live(demo)


def test_p2_0_22_operator_demo_has_no_execution_or_mutation() -> None:
    demo = build_operator_testable_surface_demo_state()
    assert demo.demo_state_does_not_execute is True
    assert demo.demo_state_does_not_mutate_runtime is True
    assert demo.demo_state_does_not_write_memory is True
    assert demo.demo_state_does_not_write_trace is True
    assert demo.demo_state_does_not_create_ui is True
    assert_operator_demo_does_not_execute(demo)
    assert_operator_demo_does_not_mutate_runtime(demo)


def test_p2_0_23_multi_client_consistency_contract_builds() -> None:
    contract = build_multi_client_consistency_contract()
    assert contract.truth_label == "CLIENT_CONSISTENCY_CONTRACT_ONLY"
    assert len(contract.expectations) == 5
    assert contract.creates_clients is False


def test_p2_0_23_client_kinds_exist() -> None:
    assert {kind.value for kind in ClientKind} == {
        "WEB",
        "DESKTOP",
        "MOBILE",
        "CLI",
        "TUI",
    }


def test_p2_0_23_client_contract_does_not_create_clients() -> None:
    contract = build_multi_client_consistency_contract()
    assert contract.implements_ui is False
    assert contract.implements_cli is False
    assert contract.implements_runtime is False
    assert_client_consistency_does_not_create_clients(contract)


def test_p2_0_23_all_clients_share_projection_expectations() -> None:
    contract = build_multi_client_consistency_contract()
    assert_clients_share_same_registry_truth_permission_unavailable_fixture_contracts(
        contract
    )
    for expectation in contract.expectations:
        assert expectation.same_surface_registry is True
        assert expectation.same_truth_labels is True
        assert expectation.same_permission_meanings is True
        assert expectation.same_unavailable_states is True
        assert expectation.same_fixture_disclosures is True
        assert expectation.same_snapshot_contract is True


def test_p2_0_24_shell_snapshot_contract_builds() -> None:
    contract = build_shell_state_snapshot_contract()
    assert contract.snapshot_serializes is True
    assert contract.snapshot_is_read_model is True
    assert contract.snapshot_is_not_source_of_truth is True


def test_p2_0_24_shell_snapshot_serializes() -> None:
    snapshot = build_shell_state_snapshot()
    payload = serialize_shell_state_snapshot(snapshot)
    parsed = json.loads(payload)
    assert parsed["snapshot_id"] == snapshot.snapshot_id
    assert parsed["truth_label"] == "SHELL_SNAPSHOT_CONTRACT_ONLY"
    assert_shell_snapshot_serializes(snapshot)


def test_p2_0_24_shell_snapshot_includes_a_b_c_d_e_summaries() -> None:
    snapshot = build_shell_state_snapshot()
    assert snapshot.surface_registry_summary["surface_count"] == "7"
    assert snapshot.navigation_boundary_summary["no_universal_left_nav"] == "true"
    assert "floating_window_contract" in snapshot.continuity_summary
    assert snapshot.permission_matrix_summary["authorizes_action"] == "false"
    assert snapshot.operator_demo_summary["operator_testable"] == "true"
    assert snapshot.client_consistency_summary["creates_clients"] == "false"


def test_p2_0_24_shell_snapshot_is_read_model_not_truth_or_mutation() -> None:
    snapshot = build_shell_state_snapshot()
    assert snapshot.is_read_model is True
    assert snapshot.is_source_of_truth is False
    assert snapshot.mutates_runtime is False
    assert snapshot.writes_memory is False
    assert snapshot.writes_trace is False
    assert snapshot.carries_truth_labels is True
    assert_shell_snapshot_is_read_model_only(snapshot)
    assert_shell_snapshot_is_not_source_of_truth(snapshot)
    assert_shell_snapshot_does_not_mutate_runtime(snapshot)


def test_p2_0_25_regression_route_harness_builds() -> None:
    harness = build_surface_regression_route_test_harness()
    assert harness.validates_contract_cases_only is True
    assert harness.case_count >= 10
    assert harness.creates_route_runtime is False


def test_p2_0_25_route_contract_cases_serialize() -> None:
    harness = build_surface_regression_route_test_harness()
    for case in harness.cases:
        payload = json.dumps(case.to_canonical_dict(), sort_keys=True)
        parsed = json.loads(payload)
        assert parsed["case_id"] == case.case_id
        assert parsed["truth_label"] == "REGRESSION_HARNESS_CONTRACT_ONLY"


def test_p2_0_25_harness_validates_required_route_cases() -> None:
    result = run_surface_regression_route_contract_harness()
    expected_cases = {
        "exactly_seven_surfaces",
        "logo_routes_to_cro",
        "system_not_logo_default_route",
        "settings_not_system",
        "hub_entry_not_tool_execution",
        "no_universal_left_nav",
        "demo_states_truth_labeled",
        "unavailable_states_reasoned",
        "fixtures_not_live",
        "snapshot_not_source_of_truth",
    }
    assert {case.case_id for case in result.case_results} == expected_cases
    assert result.passed is True
    assert all(case.passed for case in result.case_results)


def test_p2_0_25_harness_does_not_create_route_runtime_or_browser_tests() -> None:
    result = run_surface_regression_route_contract_harness()
    assert result.creates_route_runtime is False
    assert result.runs_frontend is False
    assert result.runs_browser is False
    assert result.mutates_runtime is False
    assert_route_harness_does_not_create_runtime_routes(result)


def test_p2_0_26_readiness_builds() -> None:
    readiness = build_p2_0_cognitive_os_lock_readiness()
    assert readiness.readiness_id
    assert readiness.criteria
    assert readiness.readiness_decision is P20ReadinessDecision.READY_FOR_P2_0_F_REVIEW


def test_p2_0_26_readiness_checks_a_b_c_d_e_criteria() -> None:
    readiness = build_p2_0_cognitive_os_lock_readiness()
    assert readiness.dependency_packs_checked == (
        "P2.0-A",
        "P2.0-B",
        "P2.0-C",
        "P2.0-D",
        "P2.0-E",
    )
    assert all(criterion.truth_label == "READINESS_REVIEW_ONLY" for criterion in readiness.criteria)


def test_p2_0_26_readiness_can_report_blockers() -> None:
    readiness = build_p2_0_cognitive_os_lock_readiness(
        blockers=("validation_missing",),
        warnings=(),
    )
    assert readiness.readiness_decision is P20ReadinessDecision.BLOCKED
    assert readiness.blockers == ("validation_missing",)
    assert any(not criterion.passed for criterion in readiness.criteria)


def test_p2_0_26_readiness_does_not_claim_exit_seal_live_or_next_pack() -> None:
    readiness = build_p2_0_cognitive_os_lock_readiness()
    assert readiness.is_exit_seal is False
    assert readiness.is_live_claim is False
    assert readiness.starts_next_pack is False
    assert readiness.authorizes_p2_1 is False
    assert_readiness_is_not_exit_seal(readiness)
    assert_readiness_is_not_live(readiness)
    assert_readiness_does_not_start_p2_0_f(readiness)


def test_pack_result_covers_p2_0_22_through_p2_0_26() -> None:
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    assert result.pack_id == P2_0_E_PACK_ID
    assert result.covered_checkpoints == P2_0_E_PACK_CHECKPOINT_IDS
    assert len(result.checkpoint_reads) == 5
    assert all(status == "DONE" for status in result.checkpoint_statuses.values())


def test_pack_result_depends_on_p2_0_a_b_c_d() -> None:
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    assert result.dependency_packs == P2_0_E_DEPENDENCY_PACKS
    assert result.operator_demo_state.surface_count == 7
    assert result.multi_client_consistency_contract.canonical_surface_ids == CANONICAL_SURFACE_ORDER


def test_pack_result_next_pack_and_readiness_boundary() -> None:
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    assert result.next_pack == P2_0_E_NEXT_PACK
    assert result.readiness_decision is P20ReadinessDecision.READY_FOR_P2_0_F_REVIEW
    assert result.readiness.is_exit_seal is False
    assert result.readiness.starts_next_pack is False


def test_pack_result_side_effect_proof_false_for_forbidden_work() -> None:
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    for field_name, value in result.side_effect_proof.to_canonical_dict().items():
        assert value is False, f"side effect {field_name} must be false"


def test_pack_result_serializes() -> None:
    result = build_p2_0_e_operator_demo_snapshot_regression_result()
    payload = serialize_p2_0_e_result(result)
    parsed = json.loads(payload)
    assert parsed["pack_id"] == "P2.0-E"
    assert parsed["result_hash"] == result.result_hash
    assert parsed["side_effect_proof"]["ui_created"] is False
