from __future__ import annotations

import json

from agentic_runtime.aurel_flow import (
    RUNTIME_BEHAVIOR_READ_MODEL_VERSION,
    build_runtime_behavior_read_model,
    serialize_runtime_behavior_read_model,
)
from agentic_runtime.aurel_flow.demo import run_runtime_behavior_demo


def test_read_model_exposes_events_and_relations() -> None:
    read_model = run_runtime_behavior_demo()

    assert read_model.read_model_version == RUNTIME_BEHAVIOR_READ_MODEL_VERSION
    assert read_model.pack_id == "P3-FLOW-B"
    assert read_model.events_count == 3
    assert read_model.event_stream_snapshot.event_count == 3
    assert len(read_model.event_relations) == 3
    child_relation = read_model.event_relations[1]
    assert child_relation.parent_event_id == read_model.event_relations[0].event_id
    assert child_relation.correlation_id == "behavior-demo"
    assert child_relation.affected_node_ids == ("fetch", "gate")


def test_read_model_exposes_commitments_and_pause_state() -> None:
    read_model = run_runtime_behavior_demo()

    assert len(read_model.mediated_actor_outputs) == 1
    assert len(read_model.state_commitments) == 1
    assert read_model.state_commitments[0].commit_status.value == "COMMITTED_INTERNAL"
    assert len(read_model.pause_states) == 1
    assert read_model.pause_states[0].pause_reason.value == "WAITING_APPROVAL"
    assert len(read_model.operator_decision_signals) == 1
    assert read_model.operator_decision_signals[0].decision_kind.value == "RESUME"


def test_read_model_exposes_responsibility_and_recovery_candidates() -> None:
    read_model = run_runtime_behavior_demo()

    assert len(read_model.responsibility_transfer_frames) == 1
    assert read_model.responsibility_transfer_frames[0].authority_transferred is False
    assert len(read_model.retry_eligibilities) == 1
    assert len(read_model.recovery_proposals) == 1
    assert len(read_model.rollback_candidates) == 1
    assert read_model.failure_classifications == ("VALIDATION_FAILURE",)
    assert read_model.failure_propagation_risks == ("WORKFLOW_BLOCKING",)


def test_read_model_exposes_truth_labels_and_unavailable_reasons() -> None:
    read_model = run_runtime_behavior_demo()

    assert read_model.truth_labels["events"] == "LOCAL_RUNTIME_BEHAVIOR"
    assert read_model.truth_labels["execution"] == "UNAVAILABLE"
    assert read_model.truth_labels["trace_verification"] == "UNAVAILABLE"
    assert read_model.truth_labels["ledger"] == "UNAVAILABLE"
    assert read_model.truth_labels["authority"] == "UNAVAILABLE"
    assert read_model.truth_labels["cli_binding"] == "UNAVAILABLE"
    assert "P3.7" in read_model.cli_binding_unavailable_reason

    capabilities = {entry.capability: entry.reason for entry in read_model.unavailable_capabilities}
    assert "P4 AurelExec" in capabilities["UNAVAILABLE_EXECUTION"]
    assert "P5 AurelTrace" in capabilities["UNAVAILABLE_TRACE_VERIFICATION"]


def test_read_model_serializes_deterministically() -> None:
    encoded_once = serialize_runtime_behavior_read_model(run_runtime_behavior_demo())
    encoded_twice = serialize_runtime_behavior_read_model(run_runtime_behavior_demo())
    payload = json.loads(encoded_once)

    assert encoded_once == encoded_twice
    assert payload["read_model_version"] == RUNTIME_BEHAVIOR_READ_MODEL_VERSION
    assert payload["execution_available"] is False
    assert payload["trace_verified"] is False
    assert payload["ledger_written"] is False
    assert payload["global_trace_written"] is False


def test_empty_read_model_is_valid_and_honest() -> None:
    read_model = build_runtime_behavior_read_model("wfrun-empty")

    assert read_model.event_stream_snapshot is None
    assert read_model.events_count == 0
    assert read_model.event_relations == ()
    assert read_model.predictability_labels == ()
    assert read_model.execution_available is False
    assert read_model.trace_verified is False
    assert read_model.read_model_hash


def test_predictability_labels_are_advisory_metadata_only() -> None:
    read_model = run_runtime_behavior_demo()

    # Advisory labels are exposed but grant nothing and schedule nothing.
    assert read_model.predictability_labels == ("UNSPECIFIED",)
