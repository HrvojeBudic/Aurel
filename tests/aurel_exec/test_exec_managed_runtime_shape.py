"""P4-EXEC-C managed runtime shape tests — wraps the B bridge, adds no path."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecQueueState,
    ExecRuntimeBridge,
    ExecutionMessageKind,
    QueueClaimStatus,
    WorkerSlotStatus,
    build_managed_runtime_projection,
    claim_queue_entry,
    create_local_worker_slot,
    create_queue_entry,
    run_claimed_queue_entry_once,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def _claimed_shape(*, expires_at_tick=100):
    _, decision, job, lease, session, attempt = build_bound_slice(
        expires_at_tick=expires_at_tick
    )
    entry = create_queue_entry(job, lease, current_tick=4)
    slot = create_local_worker_slot()
    claim, entry, slot = claim_queue_entry(entry, slot, lease, current_tick=5)
    return decision, job, lease, session, attempt, entry, slot, claim


def _run(bridge, fake, card, shape, *, tick=6):
    decision, job, lease, session, attempt, entry, slot, claim = shape
    request = build_bridge_request(job, lease, session, attempt)
    return run_claimed_queue_entry_once(
        bridge, request, queue_entry=entry, claim=claim, worker_slot=slot,
        job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=tick,
    )


def test_managed_runtime_shape_wraps_existing_runtime_bridge():
    shape = _claimed_shape()
    bridge, fake, card = bridge_with_fake()
    assert isinstance(bridge, ExecRuntimeBridge)  # the P4-EXEC-B bridge, reused
    managed = _run(bridge, fake, card, shape)
    # exactly one governed submit through the existing bridge path
    assert len(fake.submit_calls) == 1
    assert managed.bridge_execution.result.runtime_submit_called is True
    assert managed.result.completed is True
    assert managed.result.success is True
    assert managed.result.outcome_id == managed.bridge_execution.outcome.outcome_id
    # shape landed honestly: entry COMPLETED, slot released, claim RELEASED
    assert managed.queue_entry.queue_state is ExecQueueState.COMPLETED
    assert managed.worker_slot.status is WorkerSlotStatus.AVAILABLE
    assert managed.claim.claim_status is QueueClaimStatus.RELEASED
    # causality recorded locally in order
    kinds = [m.message_kind for m in managed.log.messages]
    assert kinds == [
        ExecutionMessageKind.ATTEMPT_READY,
        ExecutionMessageKind.CHECKPOINT_BOUND,
        ExecutionMessageKind.ATTEMPT_SUBMITTED,
        ExecutionMessageKind.OUTCOME_RECORDED,
        ExecutionMessageKind.CHECKPOINT_BOUND,
        ExecutionMessageKind.ROLLBACK_REF_CREATED,
        ExecutionMessageKind.WORKER_RELEASED,
    ]
    assert managed.result.message_ids == tuple(m.message_id for m in managed.log.messages)
    # checkpoint boundaries + not-executed rollback ref
    assert managed.pre_attempt_checkpoint.checkpoint_available is True
    assert managed.post_attempt_checkpoint.checkpoint_available is True
    assert managed.rollback_ref.rollback_executed is False


def test_managed_runtime_shape_does_not_create_new_submit_path():
    # the helper cannot run without the B bridge and a coherent claimed shape;
    # a blocked shape performs zero kernel calls
    shape = _claimed_shape()
    decision, job, lease, session, attempt, entry, slot, claim = shape
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    released_claim = dataclasses.replace(claim, claim_status=QueueClaimStatus.RELEASED)
    with pytest.raises(AurelExecValidationError) as excinfo:
        run_claimed_queue_entry_once(
            bridge, request, queue_entry=entry, claim=released_claim, worker_slot=slot,
            job=job, lease=lease, session=session, attempt=attempt,
            card=card, current_tick=6,
        )
    assert excinfo.value.code is AurelExecErrorCode.CLAIM_STATE_INVALID
    assert fake.submit_calls == []
    # source-level: the C modules never import the runtime kernel — the only
    # sanctioned kernel reference remains exec_runtime_bridge.py (B pack)
    from pathlib import Path

    import agentic_runtime.aurel_exec as aurel_exec

    for module_name in ("exec_queue.py", "exec_worker.py", "exec_messages.py",
                        "exec_checkpoint.py"):
        source = (Path(aurel_exec.__file__).parent / module_name).read_text(
            encoding="utf-8"
        )
        assert "from ..runtime import" not in source
        assert "from agentic_runtime.runtime import" not in source
        assert ".dispatch(" not in source
        assert "import subprocess" not in source
        assert "import socket" not in source
        assert "import asyncio" not in source
        assert "import threading" not in source


def test_managed_run_preserves_runtime_failure_honestly():
    shape = _claimed_shape()
    bridge, fake, card = bridge_with_fake(succeed=False)
    managed = _run(bridge, fake, card, shape)
    assert managed.result.completed is True
    assert managed.result.success is False
    assert "FileNotFoundError" in (managed.result.error_message or "")
    assert managed.queue_entry.queue_state is ExecQueueState.FAILED
    kinds = [m.message_kind for m in managed.log.messages]
    assert ExecutionMessageKind.ERROR_RECORDED in kinds
    # worker still released after a failed run; failure is visible, not hidden
    assert managed.worker_slot.status is WorkerSlotStatus.AVAILABLE


def test_managed_run_requires_coherent_claim():
    shape = _claimed_shape()
    decision, job, lease, session, attempt, entry, slot, claim = shape
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    foreign_claim = dataclasses.replace(claim, exec_job_id="exec-job-other")
    with pytest.raises(AurelExecValidationError) as excinfo:
        run_claimed_queue_entry_once(
            bridge, request, queue_entry=entry, claim=foreign_claim, worker_slot=slot,
            job=job, lease=lease, session=session, attempt=attempt,
            card=card, current_tick=6,
        )
    assert excinfo.value.code is AurelExecErrorCode.CLAIM_MISMATCH
    assert fake.submit_calls == []


def test_projection_shows_queue_worker_message_checkpoint_state():
    shape = _claimed_shape()
    bridge, fake, card = bridge_with_fake()
    managed = _run(bridge, fake, card, shape)
    projection = build_managed_runtime_projection(
        queue_entry=managed.queue_entry,
        worker_slot=managed.worker_slot,
        claim=managed.claim,
        log=managed.log,
        checkpoint_refs=(managed.pre_attempt_checkpoint, managed.post_attempt_checkpoint),
        rollback_refs=(managed.rollback_ref,),
    )
    assert projection.queue_state is ExecQueueState.COMPLETED
    assert projection.worker_slot_state == "AVAILABLE"
    assert projection.claim_state == "RELEASED"
    assert len(projection.local_execution_messages) == 7
    assert len(projection.checkpoint_refs) == 2
    assert len(projection.rollback_refs) == 1
    assert projection.checkpoint_ref_available is True
    assert projection.read_only is True


def test_recovery_p5_p9_remain_unavailable():
    shape = _claimed_shape()
    bridge, fake, card = bridge_with_fake()
    managed = _run(bridge, fake, card, shape)
    projection = build_managed_runtime_projection(
        queue_entry=managed.queue_entry, worker_slot=managed.worker_slot,
        claim=managed.claim, log=managed.log,
    )
    for boundary_field in (
        "queue_is_scheduler",
        "worker_pool_available",
        "remote_worker_available",
        "distributed_worker_available",
        "transport_bus_available",
        "network_publish_available",
        "pubsub_available",
        "checkpoint_persistence_engine_available",
        "rollback_available",
        "rollback_executed",
        "recovery_engine_available",
        "retry_engine_available",
        "concurrency_engine_available",
        "p5_trace_verification_available",
        "p9_full_enforcement_available",
        "shell_ui_available",
        "react_frontend_available",
        "api_server_available",
    ):
        assert getattr(projection, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, single_local_worker_slot_only=False)
    # claiming checkpoint availability without refs is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, checkpoint_ref_available=True)
