from __future__ import annotations

import json

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowErrorCode,
    AurelFlowValidationError,
    FLOW_RUNTIME_READ_MODEL_VERSION,
    WorkflowLifecycleStatus,
    build_flow_runtime_read_model,
    create_workflow_run,
    lifecycle_transition,
    make_scheduler_decision,
    serialize_flow_runtime_read_model,
    transition_workflow_run,
)
from agentic_runtime.aurel_flow.demo import (
    DEMO_GRAPH_ID,
    build_demo_workflow_graph,
    run_flow_foundation_demo,
)


def test_read_model_exposes_graph_summary() -> None:
    read_model = run_flow_foundation_demo()

    assert read_model.read_model_version == FLOW_RUNTIME_READ_MODEL_VERSION
    assert read_model.pack_id == "P3-FLOW-A"
    assert read_model.graph.graph_id == DEMO_GRAPH_ID
    assert read_model.graph.node_count == 5
    assert read_model.graph.edge_count == 5
    assert read_model.graph.valid is True


def test_read_model_exposes_run_lifecycle_and_node_states() -> None:
    read_model = run_flow_foundation_demo()
    snapshot = read_model.run_snapshot

    assert snapshot.lifecycle_status is WorkflowLifecycleStatus.RUNNING
    assert set(snapshot.node_states) == {"start", "fetch", "gate", "apply", "end"}
    # 2 lifecycle transitions + 3 node marks each for "start" and "fetch".
    assert snapshot.step == 8
    assert snapshot.transition_count == 8
    assert snapshot.snapshot_hash


def test_read_model_exposes_ready_waiting_blocked_truth() -> None:
    read_model = run_flow_foundation_demo()

    # Mid-flight demo: the approval gate holds everything downstream.
    assert read_model.ready_node_ids == ()
    assert read_model.waiting_approval_node_ids == ("gate",)
    assert read_model.waiting_dependency_node_ids == ("apply", "end")
    assert read_model.blocked_node_ids == ()
    assert read_model.next_ready_node_id == ""


def test_fresh_run_read_model_shows_entry_ready() -> None:
    graph = build_demo_workflow_graph()
    run = create_workflow_run(graph)
    read_model = build_flow_runtime_read_model(graph, run)

    assert read_model.ready_node_ids == ("start",)
    assert read_model.next_ready_node_id == "start"


def test_read_model_exposes_truth_labels_and_unavailable_reasons() -> None:
    read_model = run_flow_foundation_demo()

    assert read_model.truth_labels["graph"] == "DEV_FIXTURE"
    assert read_model.truth_labels["run"] == "DEV_FIXTURE"
    assert read_model.truth_labels["scheduler"] == "LOCAL_RUNTIME_SUBSTRATE"
    assert read_model.truth_labels["execution"] == "UNAVAILABLE"
    assert read_model.truth_labels["trace_verification"] == "UNAVAILABLE"
    assert read_model.truth_labels["cli_binding"] == "UNAVAILABLE"

    capabilities = {entry.capability: entry.reason for entry in read_model.unavailable_capabilities}
    assert "P4 AurelExec" in capabilities["UNAVAILABLE_EXECUTION"]
    assert "P5 AurelTrace" in capabilities["UNAVAILABLE_TRACE_VERIFICATION"]
    assert "P3.7" in capabilities["UNAVAILABLE_CLI_BINDING"]
    assert "P3.3" in capabilities["UNAVAILABLE_EVENT_STREAM"]
    assert "P3.4" in capabilities["UNAVAILABLE_APPROVAL_RUNTIME"]
    assert "in-memory only" in capabilities["UNAVAILABLE_PERSISTENCE"]


def test_read_model_serializes_deterministically() -> None:
    encoded_once = serialize_flow_runtime_read_model(run_flow_foundation_demo())
    encoded_twice = serialize_flow_runtime_read_model(run_flow_foundation_demo())
    payload = json.loads(encoded_once)

    assert encoded_once == encoded_twice
    assert payload["read_model_version"] == FLOW_RUNTIME_READ_MODEL_VERSION
    assert payload["live"] is False
    assert payload["trace_verified"] is False
    assert payload["run_snapshot"]["lifecycle_status"] == "RUNNING"


def test_read_model_rejects_stale_scheduler_decision() -> None:
    graph = build_demo_workflow_graph()
    run = create_workflow_run(graph)
    stale_decision = make_scheduler_decision(graph, run)
    moved = transition_workflow_run(
        run,
        lifecycle_transition(WorkflowLifecycleStatus.CREATED, WorkflowLifecycleStatus.READY),
    )

    with pytest.raises(AurelFlowValidationError) as excinfo:
        build_flow_runtime_read_model(graph, moved, stale_decision)

    assert excinfo.value.code is AurelFlowErrorCode.GRAPH_RUN_MISMATCH


def test_demo_is_an_operator_testable_path() -> None:
    first = run_flow_foundation_demo()
    second = run_flow_foundation_demo()

    assert first.read_model_hash == second.read_model_hash
    assert first.scheduler_decision.decision_hash == second.scheduler_decision.decision_hash
    assert first.run_snapshot.run_id == second.run_snapshot.run_id
