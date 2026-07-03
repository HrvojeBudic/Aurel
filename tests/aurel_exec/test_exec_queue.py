"""P4-EXEC-C ExecQueueEntry tests — a queue entry is not a scheduler."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecQueueState,
    block_queue_entry,
    create_exec_job,
    create_queue_entry,
    decide_admission,
    build_dev_fixture_admission_request,
    mark_queue_entry_claimed,
    mark_queue_entry_completed,
    mark_queue_entry_failed,
    mark_queue_entry_running,
    revoke_execution_lease,
)
from tests.aurel_exec._bridge_helpers import build_bound_slice


def test_queue_entry_requires_admitted_leased_job():
    _, decision, job, lease, _, _ = build_bound_slice()
    entry = create_queue_entry(job, lease, current_tick=4)
    assert entry.queue_state is ExecQueueState.PENDING
    assert entry.exec_job_id == job.exec_job_id
    assert entry.lease_id == lease.lease_id
    # an ADMITTED job without a bound lease cannot enter the queue
    request = build_dev_fixture_admission_request(request_id="exec-req-queue-x")
    unleased_job = create_exec_job(
        decide_admission(request), source_p3_candidate_ref=request.source_p3_candidate_ref
    )
    with pytest.raises(AurelExecValidationError) as excinfo:
        create_queue_entry(unleased_job, lease, current_tick=4)
    assert excinfo.value.code is AurelExecErrorCode.QUEUE_ENTRY_INVALID


def test_queue_entry_blocked_by_expired_or_revoked_lease():
    _, _, job, lease, _, _ = build_bound_slice(expires_at_tick=10)
    with pytest.raises(AurelExecValidationError) as expired:
        create_queue_entry(job, lease, current_tick=10)
    assert expired.value.code is AurelExecErrorCode.LEASE_EXPIRED
    _, _, job2, lease2, _, _ = build_bound_slice()
    revoked = revoke_execution_lease(lease2)
    with pytest.raises(AurelExecValidationError) as blocked:
        create_queue_entry(
            dataclasses.replace(job2), revoked, current_tick=4
        )
    assert blocked.value.code is AurelExecErrorCode.LEASE_REVOKED


def test_queue_entry_does_not_schedule_workflow():
    _, _, job, lease, _, _ = build_bound_slice()
    entry = create_queue_entry(job, lease, current_tick=4)
    assert entry.schedules_workflows is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(entry, schedules_workflows=True)
    for verb in ("schedule", "dispatch", "plan", "route"):
        assert not hasattr(entry, verb)


def test_queue_entry_does_not_execute():
    _, _, job, lease, _, _ = build_bound_slice()
    entry = create_queue_entry(job, lease, current_tick=4)
    assert entry.executes is False
    assert entry.dispatches_remotely is False
    for boundary_field in ("executes", "dispatches_remotely"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(entry, **{boundary_field: True})
    for verb in ("execute", "run", "submit"):
        assert not hasattr(entry, verb)


def test_queue_lifecycle_is_deterministic_and_fail_closed():
    _, _, job, lease, _, _ = build_bound_slice()
    entry = create_queue_entry(job, lease, current_tick=4)
    claimed = mark_queue_entry_claimed(entry, worker_slot_id="exec-worker-x", claimed_at_tick=5)
    assert claimed.queue_state is ExecQueueState.CLAIMED
    running = mark_queue_entry_running(claimed)
    completed = mark_queue_entry_completed(running, completed_at_tick=6)
    assert completed.queue_state is ExecQueueState.COMPLETED
    # invalid transitions fail closed
    with pytest.raises(AurelExecValidationError):
        mark_queue_entry_running(entry)  # PENDING -> RUNNING skips CLAIMED
    with pytest.raises(AurelExecValidationError):
        mark_queue_entry_completed(claimed, completed_at_tick=6)
    with pytest.raises(AurelExecValidationError):
        block_queue_entry(completed)  # terminal
    failed = mark_queue_entry_failed(
        mark_queue_entry_running(
            mark_queue_entry_claimed(entry, worker_slot_id="exec-worker-x", claimed_at_tick=5)
        ),
        completed_at_tick=7,
    )
    assert failed.queue_state is ExecQueueState.FAILED


def test_claimed_queue_entry_must_reference_its_worker_slot():
    _, _, job, lease, _, _ = build_bound_slice()
    entry = create_queue_entry(job, lease, current_tick=4)
    with pytest.raises(AurelExecValidationError) as excinfo:
        dataclasses.replace(entry, queue_state=ExecQueueState.CLAIMED)
    assert excinfo.value.code is AurelExecErrorCode.QUEUE_STATE_INVALID
