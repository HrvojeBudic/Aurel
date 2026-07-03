"""P4-EXEC-C ExecutionMessage / LocalExecutionMessageLog tests.

A local message is not a network event; the log is not a bus."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTruthLabel,
    ExecutionMessageKind,
    LocalExecutionMessageLog,
    append_execution_message,
    build_execution_message,
    build_no_transport_bus_proof,
    filter_execution_messages_by_attempt,
    filter_execution_messages_by_job,
    filter_execution_messages_by_queue_entry,
    filter_execution_messages_by_session,
    list_execution_messages,
)


def _message(kind=ExecutionMessageKind.JOB_QUEUED, **overrides):
    values = dict(
        payload_summary="test message",
        truth_label=ExecTruthLabel.DEV_FIXTURE,
        exec_job_id="exec-job-a",
        session_id="exec-session-a",
        attempt_id="exec-attempt-a",
        queue_entry_id="exec-queue-a",
        created_at_tick=1,
    )
    values.update(overrides)
    return build_execution_message(kind, **values)


def test_local_execution_message_log_appends_and_filters():
    log = LocalExecutionMessageLog()
    assert list_execution_messages(log) == ()
    m1 = _message(ExecutionMessageKind.JOB_QUEUED)
    m2 = _message(ExecutionMessageKind.QUEUE_CLAIMED, exec_job_id="exec-job-b",
                  session_id="exec-session-b", attempt_id="exec-attempt-b",
                  queue_entry_id="exec-queue-b", sequence=1)
    log = append_execution_message(log, m1)
    log2 = append_execution_message(log, m2)
    # append is immutable: the earlier log is untouched
    assert len(log.messages) == 1
    assert list_execution_messages(log2) == (m1, m2)
    assert filter_execution_messages_by_job(log2, "exec-job-a") == (m1,)
    assert filter_execution_messages_by_session(log2, "exec-session-b") == (m2,)
    assert filter_execution_messages_by_attempt(log2, "exec-attempt-a") == (m1,)
    assert filter_execution_messages_by_queue_entry(log2, "exec-queue-b") == (m2,)


def test_message_ids_are_deterministic():
    assert _message().message_id == _message().message_id
    assert _message(sequence=1).message_id != _message(sequence=2).message_id


def test_execution_message_is_not_network_event():
    message = _message()
    assert message.is_network_event is False
    assert message.routes is False
    assert message.executes is False
    for boundary_field in ("is_network_event", "routes", "executes"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(message, **{boundary_field: True})
    for verb in ("publish", "send", "route", "dispatch", "subscribe"):
        assert not hasattr(message, verb)


def test_execution_message_log_is_not_transport_bus():
    log = LocalExecutionMessageLog()
    assert log.is_transport_bus is False
    assert log.publishes_network_events is False
    assert log.pubsub_available is False
    assert log.has_subscribers is False
    for boundary_field in (
        "is_transport_bus",
        "publishes_network_events",
        "pubsub_available",
        "has_subscribers",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(log, **{boundary_field: True})
    # no bus surface exists on the log at all
    for verb in ("publish", "subscribe", "route", "emit", "broadcast", "dispatch"):
        assert not hasattr(log, verb)
    proof = build_no_transport_bus_proof()
    assert proof.transport_bus_available is False
    assert proof.network_publish_available is False
    assert proof.pubsub_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, transport_bus_available=True)


def test_message_kind_vocabulary_is_exact():
    assert {kind.value for kind in ExecutionMessageKind} == {
        "JOB_QUEUED",
        "QUEUE_CLAIMED",
        "WORKER_CLAIMED",
        "SESSION_OPENED",
        "ATTEMPT_READY",
        "CHECKPOINT_BOUND",
        "ATTEMPT_SUBMITTED",
        "OUTCOME_RECORDED",
        "ROLLBACK_REF_CREATED",
        "WORKER_RELEASED",
        "ERROR_RECORDED",
        "UNAVAILABLE",
        "ERROR",
    }


def test_message_cannot_claim_live_or_empty_payload():
    with pytest.raises(AurelExecValidationError):
        _message(truth_label=ExecTruthLabel.LIVE)
    with pytest.raises(AurelExecValidationError):
        _message(payload_summary="  ")
