"""P4-EXEC-B ExecJob / ExecutionAttempt lifecycle expansion tests."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecLifecycleState,
    ExecutionAttempt,
    ExecTruthLabel,
    bind_lease_to_job,
    transition_exec_job,
    transition_execution_attempt,
)
from tests.aurel_exec._bridge_helpers import build_bound_slice


def test_exec_job_lifecycle_transitions_are_deterministic():
    _, _, job, _, _, _ = build_bound_slice()
    assert job.lifecycle_state is ExecLifecycleState.SESSION_BOUND
    step1 = transition_exec_job(job, ExecLifecycleState.ATTEMPT_PENDING)
    step2 = transition_exec_job(job, ExecLifecycleState.ATTEMPT_PENDING)
    assert step1 == step2
    running = transition_exec_job(step1, ExecLifecycleState.RUNNING, updated_at_tick=9)
    assert running.lifecycle_state is ExecLifecycleState.RUNNING
    assert running.updated_at_tick == 9
    done = transition_exec_job(running, ExecLifecycleState.SUCCEEDED)
    assert done.lifecycle_state is ExecLifecycleState.SUCCEEDED


def test_invalid_job_lifecycle_transitions_are_rejected():
    _, _, job, _, _, _ = build_bound_slice()  # SESSION_BOUND
    for bad_target in (
        ExecLifecycleState.SUCCEEDED,
        ExecLifecycleState.RUNNING,
        ExecLifecycleState.LEASED,
        ExecLifecycleState.CANDIDATE,
    ):
        with pytest.raises(AurelExecValidationError) as excinfo:
            transition_exec_job(job, bad_target)
        assert excinfo.value.code is AurelExecErrorCode.INVALID_LIFECYCLE_TRANSITION


def test_job_cannot_take_attempt_only_states():
    _, _, job, _, _, _ = build_bound_slice()
    for attempt_only in (
        ExecLifecycleState.READY_TO_SUBMIT,
        ExecLifecycleState.SUBMITTED,
    ):
        with pytest.raises(AurelExecValidationError):
            transition_exec_job(job, attempt_only)


def test_bind_lease_to_job_requires_matching_lease():
    _, decision, job, lease, _, _ = build_bound_slice()
    # job is already LEASED+SESSION_BOUND; re-binding from a bound state fails
    with pytest.raises(AurelExecValidationError):
        bind_lease_to_job(job, lease)


def test_attempt_lifecycle_transitions_are_deterministic_and_guarded():
    _, _, job, lease, session, attempt = build_bound_slice()
    assert attempt.lifecycle_state is ExecLifecycleState.ATTEMPT_PENDING
    ready = transition_execution_attempt(attempt, ExecLifecycleState.READY_TO_SUBMIT)
    running = transition_execution_attempt(ready, ExecLifecycleState.RUNNING)
    assert running.runtime_submit_called is False
    # RUNNING -> SUBMITTED requires the submit-truth fields
    with pytest.raises(AurelExecValidationError):
        transition_execution_attempt(running, ExecLifecycleState.SUBMITTED)
    submitted = transition_execution_attempt(
        running,
        ExecLifecycleState.SUBMITTED,
        runtime_submit_called=True,
        command_id="cmd_test",
    )
    assert submitted.runtime_submit_called is True
    done = transition_execution_attempt(submitted, ExecLifecycleState.SUCCEEDED)
    assert done.lifecycle_state is ExecLifecycleState.SUCCEEDED


def test_invalid_attempt_transitions_are_rejected():
    _, _, _, _, _, attempt = build_bound_slice()
    for bad_target in (
        ExecLifecycleState.SUBMITTED,
        ExecLifecycleState.SUCCEEDED,
        ExecLifecycleState.RUNNING,
        ExecLifecycleState.ADMITTED,
    ):
        with pytest.raises(AurelExecValidationError):
            transition_execution_attempt(attempt, bad_target)


def test_attempt_submit_truth_is_structural():
    # runtime_submit_called=True requires submit-aware state + command + session
    with pytest.raises(AurelExecValidationError):
        ExecutionAttempt(
            attempt_id="exec-attempt-x",
            exec_job_id="exec-job-x",
            lease_id="exec-lease-x",
            lifecycle_state=ExecLifecycleState.SUBMITTED,
            truth_label=ExecTruthLabel.DEV_FIXTURE,
            runtime_submit_called=True,
            command_id="cmd_x",
            session_id=None,
        )
    # SUBMITTED/SUCCEEDED without runtime_submit_called is unconstructible
    for state in (ExecLifecycleState.SUBMITTED, ExecLifecycleState.SUCCEEDED):
        with pytest.raises(AurelExecValidationError):
            ExecutionAttempt(
                attempt_id="exec-attempt-x",
                exec_job_id="exec-job-x",
                lease_id="exec-lease-x",
                lifecycle_state=state,
                truth_label=ExecTruthLabel.DEV_FIXTURE,
                runtime_submit_called=False,
                session_id="exec-session-x",
            )


def test_attempt_requires_valid_lease_and_session():
    from agentic_runtime.aurel_exec import create_execution_attempt, revoke_execution_lease
    from tests.aurel_exec._bridge_helpers import bridge_with_fake, build_bridge_request

    _, _, job, lease, session, attempt = build_bound_slice()
    # revoked lease denies attempt creation (lease-before-attempt, A law)
    with pytest.raises(AurelExecValidationError) as excinfo:
        create_execution_attempt(
            job, revoke_execution_lease(lease), current_tick=3,
            session_id=session.session_id,
        )
    assert excinfo.value.code is AurelExecErrorCode.LEASE_REVOKED
    # sessionless attempt cannot submit (session-before-submit, B law)
    import dataclasses

    bridge, fake, card = bridge_with_fake()
    sessionless = dataclasses.replace(attempt, session_id=None)
    request = build_bridge_request(job, lease, session, sessionless)
    with pytest.raises(AurelExecValidationError) as excinfo2:
        bridge.submit_once(
            request, job=job, lease=lease, session=session, attempt=sessionless,
            card=card, current_tick=5,
        )
    assert excinfo2.value.code is AurelExecErrorCode.SESSION_REQUIRED
    assert fake.submit_calls == []


def test_job_and_attempt_are_not_worker_or_queue_objects():
    _, _, job, _, _, attempt = build_bound_slice()
    for obj in (job, attempt):
        for forbidden in ("worker_id", "queue_position", "queue_id", "checkpoint_id"):
            assert not hasattr(obj, forbidden)
