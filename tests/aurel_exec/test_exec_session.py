"""P4-EXEC-B ExecutionSession tests."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecLifecycleState,
    ExecutionSession,
    ExecutionSessionStatus,
    ExecTruthLabel,
    bind_session_to_job,
    close_execution_session,
    mark_session_failed,
    mark_session_running,
    open_execution_session,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def test_session_opens_runs_closes_and_fails_deterministically():
    _, _, job, _, session, _ = build_bound_slice()
    assert session.status is ExecutionSessionStatus.OPEN
    running = mark_session_running(session)
    assert running.status is ExecutionSessionStatus.RUNNING
    closed = close_execution_session(running, closed_at_tick=9)
    assert closed.status is ExecutionSessionStatus.CLOSED
    assert closed.closed_at_tick == 9
    failed = mark_session_failed(mark_session_running(session), closed_at_tick=9)
    assert failed.status is ExecutionSessionStatus.FAILED
    # terminal states cannot transition
    with pytest.raises(AurelExecValidationError):
        mark_session_running(closed)
    with pytest.raises(AurelExecValidationError):
        close_execution_session(failed, closed_at_tick=10)


def test_session_requires_leased_job():
    _, decision, job, _, _, _ = build_bound_slice()
    # job is SESSION_BOUND now; opening another session requires LEASED
    with pytest.raises(AurelExecValidationError) as excinfo:
        open_execution_session(job, opened_at_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.SESSION_INVALID


def test_session_window_consistency_is_fail_closed():
    _, _, _, _, session, _ = build_bound_slice()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(session, closed_at_tick=9)  # OPEN with closed tick
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(
            session, status=ExecutionSessionStatus.CLOSED, closed_at_tick=None
        )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(
            session, status=ExecutionSessionStatus.CLOSED, closed_at_tick=1
        )  # closes before it opened


def test_session_is_not_workflow_queue_worker_or_checkpoint():
    _, _, _, _, session, _ = build_bound_slice()
    assert session.is_workflow is False
    assert session.is_queue is False
    assert session.is_worker is False
    assert session.is_checkpoint is False
    for boundary_field in ("is_workflow", "is_queue", "is_worker", "is_checkpoint"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(session, **{boundary_field: True})


def test_session_cannot_claim_live_truth_label():
    _, _, _, _, session, _ = build_bound_slice()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(session, truth_label=ExecTruthLabel.LIVE)


def test_bind_session_to_job_rejects_foreign_or_closed_sessions():
    _, _, job, lease, session, _ = build_bound_slice()
    foreign = dataclasses.replace(session, exec_job_id="exec-job-other")
    with pytest.raises(AurelExecValidationError) as excinfo:
        bind_session_to_job(job, foreign)
    assert excinfo.value.code is AurelExecErrorCode.SESSION_JOB_MISMATCH


def test_execution_session_required_for_submit():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    # attempt without a bound session cannot submit
    unbound_attempt = dataclasses.replace(attempt, session_id=None)
    request = build_bridge_request(job, lease, session, unbound_attempt)
    with pytest.raises(AurelExecValidationError) as excinfo:
        bridge.submit_once(
            request,
            job=job,
            lease=lease,
            session=session,
            attempt=unbound_attempt,
            card=card,
            current_tick=5,
        )
    assert excinfo.value.code is AurelExecErrorCode.SESSION_REQUIRED
    assert fake.submit_calls == []
    # a closed session cannot host a submit either
    closed = close_execution_session(session, closed_at_tick=9)
    request2 = build_bridge_request(job, lease, closed, attempt)
    with pytest.raises(AurelExecValidationError) as excinfo2:
        bridge.submit_once(
            request2,
            job=job,
            lease=lease,
            session=closed,
            attempt=attempt,
            card=card,
            current_tick=10,
        )
    assert excinfo2.value.code is AurelExecErrorCode.SESSION_INVALID
    assert fake.submit_calls == []
