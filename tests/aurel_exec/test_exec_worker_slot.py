"""P4-EXEC-C WorkerSlot / QueueClaim tests — one slot, no pool."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecQueueState,
    QueueClaimStatus,
    WorkerKind,
    WorkerSlot,
    WorkerSlotStatus,
    build_no_remote_worker_proof,
    build_no_worker_pool_proof,
    claim_queue_entry,
    create_local_worker_slot,
    create_queue_entry,
    fail_worker_slot,
    release_worker_slot,
    revoke_execution_lease,
)
from agentic_runtime.aurel_exec import ExecTruthLabel
from tests.aurel_exec._bridge_helpers import build_bound_slice


def _pending_entry(expires_at_tick=100):
    _, _, job, lease, _, _ = build_bound_slice(expires_at_tick=expires_at_tick)
    return create_queue_entry(job, lease, current_tick=4), lease


def test_local_worker_slot_claims_queue_entry():
    entry, lease = _pending_entry()
    slot = create_local_worker_slot()
    assert slot.worker_kind is WorkerKind.IN_PROCESS_LOCAL
    assert slot.status is WorkerSlotStatus.AVAILABLE
    claim, claimed_entry, claimed_slot = claim_queue_entry(entry, slot, lease, current_tick=5)
    assert claim.claim_status is QueueClaimStatus.CLAIMED
    assert claimed_entry.queue_state is ExecQueueState.CLAIMED
    assert claimed_entry.worker_slot_id == slot.worker_slot_id
    assert claimed_slot.status is WorkerSlotStatus.CLAIMED
    assert claimed_slot.current_queue_entry_id == entry.queue_entry_id
    assert claim.is_execution is False


def test_double_claim_is_blocked():
    entry, lease = _pending_entry()
    slot = create_local_worker_slot()
    claim, claimed_entry, claimed_slot = claim_queue_entry(entry, slot, lease, current_tick=5)
    # busy slot cannot claim again
    with pytest.raises(AurelExecValidationError) as slot_busy:
        claim_queue_entry(entry, claimed_slot, lease, current_tick=6)
    assert slot_busy.value.code is AurelExecErrorCode.DOUBLE_CLAIM_BLOCKED
    # already-claimed entry cannot be claimed by a fresh slot
    with pytest.raises(AurelExecValidationError) as entry_busy:
        claim_queue_entry(claimed_entry, create_local_worker_slot(slot_ref="slot-b"),
                          lease, current_tick=6)
    assert entry_busy.value.code is AurelExecErrorCode.DOUBLE_CLAIM_BLOCKED


def test_expired_and_revoked_lease_block_claim():
    entry, lease = _pending_entry(expires_at_tick=10)
    slot = create_local_worker_slot()
    with pytest.raises(AurelExecValidationError) as expired:
        claim_queue_entry(entry, slot, lease, current_tick=10)
    assert expired.value.code is AurelExecErrorCode.LEASE_EXPIRED
    entry2, lease2 = _pending_entry()
    with pytest.raises(AurelExecValidationError) as revoked:
        claim_queue_entry(entry2, slot, revoke_execution_lease(lease2), current_tick=5)
    assert revoked.value.code is AurelExecErrorCode.LEASE_REVOKED


def test_remote_and_distributed_workers_are_unavailable():
    # non-local kinds are constructible only as structurally UNAVAILABLE
    for kind in (WorkerKind.REMOTE_UNAVAILABLE, WorkerKind.DISTRIBUTED_UNAVAILABLE):
        unavailable = WorkerSlot(
            worker_slot_id="exec-worker-x",
            worker_kind=kind,
            status=WorkerSlotStatus.UNAVAILABLE,
            truth_label=ExecTruthLabel.UNAVAILABLE,
        )
        assert unavailable.status is WorkerSlotStatus.UNAVAILABLE
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(unavailable, status=WorkerSlotStatus.AVAILABLE)
        # and they can never claim
        entry, lease = _pending_entry()
        with pytest.raises(AurelExecValidationError) as excinfo:
            claim_queue_entry(entry, unavailable, lease, current_tick=5)
        assert excinfo.value.code is AurelExecErrorCode.WORKER_KIND_UNAVAILABLE
    proof = build_no_remote_worker_proof()
    assert proof.remote_worker_available is False
    assert proof.distributed_worker_available is False
    for boundary_field in ("remote_worker_available", "distributed_worker_available"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_worker_slot_is_not_worker_pool():
    slot = create_local_worker_slot()
    assert slot.is_worker_pool is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(slot, is_worker_pool=True)
    for forbidden in ("pool_size", "workers", "slots", "spawn", "scale"):
        assert not hasattr(slot, forbidden)
    proof = build_no_worker_pool_proof()
    assert proof.single_local_worker_slot_only is True
    assert proof.worker_pool_available is False
    assert proof.concurrency_engine_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, single_local_worker_slot_only=False)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(proof, worker_pool_available=True)


def test_release_and_fail_are_deterministic_state_arithmetic():
    entry, lease = _pending_entry()
    slot = create_local_worker_slot()
    claim, _, claimed_slot = claim_queue_entry(entry, slot, lease, current_tick=5)
    released_slot, released_claim = release_worker_slot(
        claimed_slot, claim, released_at_tick=6, release_reason="test release"
    )
    assert released_slot.status is WorkerSlotStatus.AVAILABLE
    assert released_slot.current_queue_entry_id is None
    assert released_claim.claim_status is QueueClaimStatus.RELEASED
    assert released_claim.release_reason == "test release"
    # releasing an AVAILABLE slot fails closed
    with pytest.raises(AurelExecValidationError):
        release_worker_slot(released_slot, released_claim, released_at_tick=7,
                            release_reason="again")
    failed_slot, failed_claim = fail_worker_slot(
        claimed_slot, claim, released_at_tick=6, release_reason="test failure"
    )
    assert failed_slot.status is WorkerSlotStatus.FAILED
    assert failed_claim.claim_status is QueueClaimStatus.FAILED
