from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowPackageExportStatus,
    FlowPublicSurfaceStatus,
    FlowTruthLabel,
    build_failure_recovery_projection,
    build_flow_actual_code_inventory,
    build_flow_demo_bundle,
    build_flow_demo_scenario_read_model,
    build_flow_demo_truth_projection,
    build_flow_state_projection,
    build_mediated_actor_output_read_model,
    build_pause_decision_read_model,
    build_responsibility_transfer_read_model,
    build_rollback_candidate_projection,
    build_state_commitment_read_model,
)
from agentic_runtime.aurel_flow.demo import run_runtime_behavior_demo


def test_actual_code_inventory_builds_from_repo_truth() -> None:
    inventory = build_flow_actual_code_inventory()

    assert inventory.package_name == "agentic_runtime.aurel_flow"
    assert inventory.module_count >= 13
    assert inventory.test_count >= 11
    assert "workflow_graph.py" in inventory.known_flow_a_modules
    assert "runtime_events.py" in inventory.known_flow_b_modules
    assert "flow_projection.py" in inventory.known_flow_c_modules
    assert inventory.production_deps == ()


def test_actual_code_inventory_statuses_are_honest() -> None:
    inventory = build_flow_actual_code_inventory()

    assert inventory.top_level_exported is False
    assert inventory.runtime_py_integrated is False
    assert inventory.agentic_entity_integrated is False
    assert inventory.repo_agent_integrated is False
    assert inventory.build_runtime_integrated is False
    assert inventory.trace_integrated is False
    assert inventory.policy_integrated is False
    assert inventory.persistence_available is False
    assert inventory.cli_integrated_read_only is True
    assert inventory.cli_surface_status is FlowPublicSurfaceStatus.CLI_READ_ONLY
    assert (
        inventory.package_export_status
        is FlowPackageExportStatus.PACKAGE_EXPORTED_INTERNAL
    )


def test_actual_code_inventory_rejects_fake_integration() -> None:
    inventory = build_flow_actual_code_inventory()

    for forbidden in ("runtime_py_integrated", "trace_integrated", "policy_integrated"):
        with pytest.raises(AurelFlowValidationError):
            replace(inventory, **{forbidden: True})


def test_actual_code_inventory_deterministic_with_explicit_inputs() -> None:
    modules = ("a.py", "b.py")
    tests = ("test_p3_flow_x.py",)
    first = build_flow_actual_code_inventory(modules, tests)
    second = build_flow_actual_code_inventory(modules, tests)

    assert first.read_model_hash == second.read_model_hash
    assert first.module_count == 2
    assert first.test_count == 1


def test_flow_state_projection_deterministic_and_read_only() -> None:
    bundle = build_flow_demo_bundle()
    step_before = bundle.run.state.step
    states_before = dict(bundle.run.state.node_states)

    first = build_flow_state_projection(bundle.graph, bundle.run)
    second = build_flow_state_projection(bundle.graph, bundle.run)

    assert first.projection_hash == second.projection_hash
    assert bundle.run.state.step == step_before
    assert dict(bundle.run.state.node_states) == states_before
    assert first.lifecycle_status == bundle.run.state.lifecycle_status.value
    assert first.truth.live is False
    assert first.truth.trace_verified is False
    assert first.truth.execution_available is False


def test_flow_state_projection_includes_behavior_summary() -> None:
    bundle = build_flow_demo_bundle()
    behavior = run_runtime_behavior_demo()

    projection = build_flow_state_projection(bundle.graph, bundle.run, behavior)

    assert projection.behavior_summary.events_count == behavior.events_count
    assert projection.behavior_summary.pause_count == 1
    assert projection.behavior_summary.rollback_candidate_count == 1
    assert projection.behavior_summary.failure_count == 1


def test_flow_projection_truth_fails_closed() -> None:
    bundle = build_flow_demo_bundle()
    projection = build_flow_state_projection(bundle.graph, bundle.run)

    for forbidden in ("live", "trace_verified", "execution_available", "ledger_written"):
        with pytest.raises(AurelFlowValidationError):
            replace(projection.truth, **{forbidden: True})


def test_mediated_output_and_commitment_read_models() -> None:
    behavior = run_runtime_behavior_demo()

    outputs = build_mediated_actor_output_read_model(behavior)
    commitments = build_state_commitment_read_model(behavior)

    assert outputs.output_count == 1
    assert outputs.direct_state_mutation_allowed_any is False
    assert commitments.commitment_count == 1
    assert commitments.commit_statuses == ("COMMITTED_INTERNAL",)
    assert commitments.mutation_scopes == ("INTERNAL_AUREL_FLOW",)
    assert commitments.ledger_written_any is False
    assert commitments.external_side_effect_any is False
    with pytest.raises(AurelFlowValidationError):
        replace(commitments, ledger_written_any=True)


def test_responsibility_and_pause_read_models() -> None:
    behavior = run_runtime_behavior_demo()

    responsibility = build_responsibility_transfer_read_model(behavior)
    pause = build_pause_decision_read_model(behavior)

    assert responsibility.frame_count == 1
    assert responsibility.handoffs == ("demo-actor->demo-operator",)
    assert responsibility.authority_transferred_any is False
    assert pause.pause_count == 1
    assert pause.pause_reasons == ("WAITING_APPROVAL",)
    assert pause.signal_kinds == ("RESUME",)
    assert pause.decision_quality.counterargument_present_count == 1
    assert pause.decision_quality.decision_pressure_warning_count == 1
    assert pause.decision_quality.authority_granted_any is False
    with pytest.raises(AurelFlowValidationError):
        replace(responsibility, authority_transferred_any=True)


def test_failure_recovery_and_rollback_projections() -> None:
    behavior = run_runtime_behavior_demo()

    recovery = build_failure_recovery_projection(behavior)
    rollback = build_rollback_candidate_projection(behavior)

    assert recovery.failure_classifications == ("VALIDATION_FAILURE",)
    assert recovery.recovery_step_count == 2
    assert recovery.retry_executed_any is False
    assert recovery.recovery_executed_any is False
    assert rollback.candidate_count == 1
    assert rollback.safe_to_execute_any is False
    assert rollback.rollback_executed_any is False
    with pytest.raises(AurelFlowValidationError):
        replace(rollback, safe_to_execute_any=True)


def test_demo_truth_projection_states_dev_fixture_boundaries() -> None:
    bundle = build_flow_demo_bundle()
    truth = build_flow_demo_truth_projection(bundle)

    assert truth.demo_completed_nodes_are_dev_fixture is True
    assert truth.demo_completion_is_not_execution is True
    assert truth.demo_rollback_edge_is_declarative is True
    assert truth.demo_rollback_edge_does_not_execute is True
    assert truth.demo_trace_verified is False
    assert truth.demo_live is False
    assert truth.truth_label is FlowTruthLabel.DEV_FIXTURE

    with pytest.raises(AurelFlowValidationError):
        replace(truth, demo_live=True)
    with pytest.raises(AurelFlowValidationError):
        replace(truth, demo_completion_is_not_execution=False)


def test_demo_scenario_read_model_is_deterministic() -> None:
    first = build_flow_demo_scenario_read_model(build_flow_demo_bundle())
    second = build_flow_demo_scenario_read_model(build_flow_demo_bundle())

    assert first.read_model_hash == second.read_model_hash
    assert first.completed_node_ids == ("start",)
    assert first.failed_node_ids == ("fetch",)
    assert first.paused_node_ids == ("gate",)
    assert first.rollback_candidate_node_ids == ("fetch",)
