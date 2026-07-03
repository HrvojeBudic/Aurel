"""P4-EXEC-C WorkerSlot / QueueClaim / managed runtime helper.

Exactly one local in-process worker capacity slot exists in this pack. A
worker slot is not a worker pool; remote and distributed worker kinds are
representable only as structurally UNAVAILABLE. A queue claim binds one
queue entry to one local worker slot under a currently valid lease — double
claim is blocked and a claim is not execution by itself.

``run_claimed_queue_entry_once`` is the managed runtime helper: it wraps
the existing P4-EXEC-B ``ExecRuntimeBridge`` path (queue entry → claim →
local messages → pre-attempt checkpoint ref → bridge → outcome →
post-attempt checkpoint ref → not-executed rollback ref → worker release).
It reuses the bridge as-is and creates no new submit path, no retry, no
recovery, no rollback execution, and no async dispatch.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_checkpoint import (
    ExecutionCheckpointRef,
    ExecutionRollbackRef,
    create_post_attempt_checkpoint_ref,
    create_pre_attempt_checkpoint_ref,
    create_rollback_ref,
)
from .exec_job import ExecJob, ExecutionAttempt
from .exec_lease import ExecutionLease, validate_execution_lease
from .exec_messages import (
    ExecutionMessage,
    ExecutionMessageKind,
    LocalExecutionMessageLog,
    append_execution_message,
    build_execution_message,
)
from .exec_queue import (
    ExecQueueEntry,
    ExecQueueState,
    mark_queue_entry_claimed,
    mark_queue_entry_completed,
    mark_queue_entry_failed,
    mark_queue_entry_running,
)
from .exec_runtime_bridge import (
    ExecRuntimeBridge,
    RuntimeBridgeExecution,
    RuntimeBridgeSubmitRequest,
)
from .exec_session import ExecutionSession
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

WORKER_SLOT_VERSION = "worker_slot.v1"
QUEUE_CLAIM_VERSION = "queue_claim.v1"
MANAGED_RUNTIME_RESULT_VERSION = "managed_runtime_result.v1"
NO_WORKER_POOL_PROOF_VERSION = "no_worker_pool_proof.v1"
NO_REMOTE_WORKER_PROOF_VERSION = "no_remote_worker_proof.v1"

WORKER_POOL_UNAVAILABLE_REASON = (
    "P4-EXEC-C supports exactly one local in-process worker slot; a worker "
    "pool, async dispatcher, or concurrency platform does not exist — one "
    "worker before a worker pool"
)
REMOTE_WORKER_UNAVAILABLE_REASON = (
    "remote and distributed workers are structurally unavailable; there is "
    "no network transport, no distributed queue, and no remote runtime — "
    "distributed shape belongs to a later operator-approved pack"
)


class WorkerKind(str, Enum):
    IN_PROCESS_LOCAL = "IN_PROCESS_LOCAL"
    REMOTE_UNAVAILABLE = "REMOTE_UNAVAILABLE"
    DISTRIBUTED_UNAVAILABLE = "DISTRIBUTED_UNAVAILABLE"
    ERROR = "ERROR"


class WorkerSlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    RELEASING = "RELEASING"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class QueueClaimStatus(str, Enum):
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    RELEASED = "RELEASED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class WorkerSlot(_ExecCanonicalMixin):
    """One local in-process worker capacity slot. Not a worker pool."""

    worker_slot_id: str
    worker_kind: WorkerKind
    status: WorkerSlotStatus
    truth_label: ExecTruthLabel
    contract_version: str = WORKER_SLOT_VERSION
    current_queue_entry_id: str | None = None
    current_exec_job_id: str | None = None
    claimed_at_tick: int | None = None
    released_at_tick: int | None = None
    is_worker_pool: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "worker_slot_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_allowed_truth_label(self)
        forbid_true(self, "is_worker_pool")
        if self.worker_kind is not WorkerKind.IN_PROCESS_LOCAL and (
            self.status is not WorkerSlotStatus.UNAVAILABLE
        ):
            raise AurelExecValidationError(
                f"worker kind {self.worker_kind.value} is structurally "
                "UNAVAILABLE; only IN_PROCESS_LOCAL can hold other statuses",
                code=AurelExecErrorCode.WORKER_KIND_UNAVAILABLE,
                field="worker_kind",
            )


@dataclass(frozen=True)
class QueueClaim(_ExecCanonicalMixin):
    """Binding of one queue entry to one local worker slot. Not execution."""

    claim_id: str
    queue_entry_id: str
    worker_slot_id: str
    exec_job_id: str
    lease_id: str
    claim_status: QueueClaimStatus
    truth_label: ExecTruthLabel
    contract_version: str = QUEUE_CLAIM_VERSION
    claimed_at_tick: int | None = None
    released_at_tick: int | None = None
    release_reason: str | None = None
    is_execution: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "claim_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "queue_entry_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "worker_slot_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "lease_id", code=AurelExecErrorCode.EMPTY_LEASE_ID)
        require_allowed_truth_label(self)
        forbid_true(self, "is_execution")

    @property
    def claim_hash(self) -> str:
        return stable_hash(self)


def create_local_worker_slot(
    *, truth_label: ExecTruthLabel = ExecTruthLabel.DEV_FIXTURE, slot_ref: str = "slot-0"
) -> WorkerSlot:
    """Create the single local in-process worker slot. Spawns nothing."""
    worker_slot_id = "exec-worker-" + stable_hash(("IN_PROCESS_LOCAL", slot_ref))[:16]
    return WorkerSlot(
        worker_slot_id=worker_slot_id,
        worker_kind=WorkerKind.IN_PROCESS_LOCAL,
        status=WorkerSlotStatus.AVAILABLE,
        truth_label=truth_label,
    )


def claim_queue_entry(
    entry: ExecQueueEntry,
    slot: WorkerSlot,
    lease: ExecutionLease,
    *,
    current_tick: int,
) -> tuple[QueueClaim, ExecQueueEntry, WorkerSlot]:
    """Bind one PENDING queue entry to one AVAILABLE local worker slot.

    Deterministic and fail-closed: double claim, non-local worker kinds,
    and expired/revoked leases block the claim. Claiming executes nothing.
    """
    if slot.worker_kind is not WorkerKind.IN_PROCESS_LOCAL:
        raise AurelExecValidationError(
            f"cannot claim with {slot.worker_kind.value}: only the local "
            "in-process worker slot exists",
            code=AurelExecErrorCode.WORKER_KIND_UNAVAILABLE,
            field="worker_kind",
        )
    if slot.status is not WorkerSlotStatus.AVAILABLE:
        raise AurelExecValidationError(
            f"double claim blocked: worker slot is {slot.status.value}",
            code=AurelExecErrorCode.DOUBLE_CLAIM_BLOCKED,
            field="status",
        )
    if entry.queue_state is not ExecQueueState.PENDING:
        raise AurelExecValidationError(
            f"double claim blocked: queue entry is {entry.queue_state.value}",
            code=AurelExecErrorCode.DOUBLE_CLAIM_BLOCKED,
            field="queue_state",
        )
    if lease.lease_id != entry.lease_id or lease.exec_job_id != entry.exec_job_id:
        raise AurelExecValidationError(
            "claim requires the queue entry's own lease",
            code=AurelExecErrorCode.CLAIM_MISMATCH,
            field="lease_id",
        )
    validation = validate_execution_lease(lease, current_tick=current_tick)
    if not validation.valid:
        code = (
            AurelExecErrorCode.LEASE_REVOKED
            if validation.revoked
            else AurelExecErrorCode.LEASE_EXPIRED
        )
        raise AurelExecValidationError(
            f"claim blocked: {validation.reason}", code=code, field="lease_id"
        )
    claim_id = "exec-claim-" + stable_hash(
        (entry.queue_entry_id, slot.worker_slot_id, current_tick)
    )[:16]
    claim = QueueClaim(
        claim_id=claim_id,
        queue_entry_id=entry.queue_entry_id,
        worker_slot_id=slot.worker_slot_id,
        exec_job_id=entry.exec_job_id,
        lease_id=lease.lease_id,
        claim_status=QueueClaimStatus.CLAIMED,
        truth_label=entry.truth_label,
        claimed_at_tick=current_tick,
    )
    claimed_entry = mark_queue_entry_claimed(
        entry, worker_slot_id=slot.worker_slot_id, claimed_at_tick=current_tick
    )
    claimed_slot = dataclasses.replace(
        slot,
        status=WorkerSlotStatus.CLAIMED,
        current_queue_entry_id=entry.queue_entry_id,
        current_exec_job_id=entry.exec_job_id,
        claimed_at_tick=current_tick,
    )
    return claim, claimed_entry, claimed_slot


def release_worker_slot(
    slot: WorkerSlot, claim: QueueClaim, *, released_at_tick: int, release_reason: str
) -> tuple[WorkerSlot, QueueClaim]:
    """Release the slot back to AVAILABLE and close the claim. Not execution."""
    if slot.status not in (WorkerSlotStatus.CLAIMED, WorkerSlotStatus.RUNNING):
        raise AurelExecValidationError(
            f"cannot release a {slot.status.value} worker slot",
            code=AurelExecErrorCode.CLAIM_STATE_INVALID,
            field="status",
        )
    if claim.worker_slot_id != slot.worker_slot_id:
        raise AurelExecValidationError(
            "claim does not belong to this worker slot",
            code=AurelExecErrorCode.CLAIM_MISMATCH,
            field="worker_slot_id",
        )
    released_slot = dataclasses.replace(
        slot,
        status=WorkerSlotStatus.AVAILABLE,
        current_queue_entry_id=None,
        current_exec_job_id=None,
        released_at_tick=released_at_tick,
    )
    released_claim = dataclasses.replace(
        claim,
        claim_status=QueueClaimStatus.RELEASED,
        released_at_tick=released_at_tick,
        release_reason=release_reason,
    )
    return released_slot, released_claim


def fail_worker_slot(
    slot: WorkerSlot, claim: QueueClaim, *, released_at_tick: int, release_reason: str
) -> tuple[WorkerSlot, QueueClaim]:
    """Mark slot and claim FAILED. Records state; repairs nothing."""
    failed_slot = dataclasses.replace(
        slot, status=WorkerSlotStatus.FAILED, released_at_tick=released_at_tick
    )
    failed_claim = dataclasses.replace(
        claim,
        claim_status=QueueClaimStatus.FAILED,
        released_at_tick=released_at_tick,
        release_reason=release_reason,
    )
    return failed_slot, failed_claim


@dataclass(frozen=True)
class ManagedRuntimeResult(_ExecCanonicalMixin):
    """Local orchestration result of one managed pass. Not P5 proof."""

    managed_runtime_result_id: str
    queue_entry_id: str
    worker_slot_id: str
    claim_id: str
    exec_job_id: str
    completed: bool
    success: bool
    truth_label: ExecTruthLabel
    contract_version: str = MANAGED_RUNTIME_RESULT_VERSION
    session_id: str | None = None
    attempt_id: str | None = None
    outcome_id: str | None = None
    pre_attempt_checkpoint_ref_id: str | None = None
    post_attempt_checkpoint_ref_id: str | None = None
    rollback_ref_id: str | None = None
    message_ids: tuple[str, ...] = ()
    error_message: str | None = None
    is_p5_proof: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "managed_runtime_result_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_allowed_truth_label(self)
        forbid_true(self, "is_p5_proof")


@dataclass(frozen=True)
class ManagedRuntimeExecution(_ExecCanonicalMixin):
    """One completed managed pass: result + updated shape objects."""

    result: ManagedRuntimeResult
    queue_entry: ExecQueueEntry
    worker_slot: WorkerSlot
    claim: QueueClaim
    log: LocalExecutionMessageLog
    bridge_execution: RuntimeBridgeExecution
    pre_attempt_checkpoint: ExecutionCheckpointRef
    post_attempt_checkpoint: ExecutionCheckpointRef
    rollback_ref: ExecutionRollbackRef


def run_claimed_queue_entry_once(
    bridge: ExecRuntimeBridge,
    request: RuntimeBridgeSubmitRequest,
    *,
    queue_entry: ExecQueueEntry,
    claim: QueueClaim,
    worker_slot: WorkerSlot,
    job: ExecJob,
    lease: ExecutionLease,
    session: ExecutionSession,
    attempt: ExecutionAttempt,
    card: object,
    current_tick: int,
    log: LocalExecutionMessageLog | None = None,
) -> ManagedRuntimeExecution:
    """Run one claimed queue entry once through the existing bridge.

    queue entry → claim → local messages → pre-attempt checkpoint ref →
    ExecRuntimeBridge.submit_once (the P4-EXEC-B path, reused as-is) →
    outcome → post-attempt checkpoint ref → not-executed rollback ref →
    worker release. No new submit path, no retry, no recovery, no rollback
    execution, no async dispatch.
    """
    if claim.queue_entry_id != queue_entry.queue_entry_id or (
        claim.worker_slot_id != worker_slot.worker_slot_id
        or claim.exec_job_id != job.exec_job_id
        or claim.lease_id != lease.lease_id
    ):
        raise AurelExecValidationError(
            "managed run requires a coherent claim over queue entry, worker "
            "slot, job, and lease",
            code=AurelExecErrorCode.CLAIM_MISMATCH,
            field="claim_id",
        )
    if claim.claim_status is not QueueClaimStatus.CLAIMED:
        raise AurelExecValidationError(
            f"managed run requires a CLAIMED claim, not {claim.claim_status.value}",
            code=AurelExecErrorCode.CLAIM_STATE_INVALID,
            field="claim_status",
        )
    if queue_entry.queue_state is not ExecQueueState.CLAIMED:
        raise AurelExecValidationError(
            f"managed run requires a CLAIMED queue entry, not "
            f"{queue_entry.queue_state.value}",
            code=AurelExecErrorCode.QUEUE_STATE_INVALID,
            field="queue_state",
        )
    if worker_slot.status is not WorkerSlotStatus.CLAIMED:
        raise AurelExecValidationError(
            f"managed run requires a CLAIMED worker slot, not {worker_slot.status.value}",
            code=AurelExecErrorCode.WORKER_UNAVAILABLE,
            field="status",
        )

    log = log if log is not None else LocalExecutionMessageLog()
    label = queue_entry.truth_label
    sequence = len(log.messages)
    message_ids: list[str] = []

    def _record(kind: ExecutionMessageKind, summary: str, **refs: object) -> None:
        nonlocal log, sequence
        message = build_execution_message(
            kind,
            payload_summary=summary,
            truth_label=label,
            exec_job_id=job.exec_job_id,
            session_id=session.session_id,
            queue_entry_id=queue_entry.queue_entry_id,
            worker_slot_id=worker_slot.worker_slot_id,
            created_at_tick=current_tick,
            sequence=sequence,
            **refs,
        )
        log = append_execution_message(log, message)
        message_ids.append(message.message_id)
        sequence += 1

    _record(
        ExecutionMessageKind.ATTEMPT_READY,
        "attempt ready under valid claim",
        attempt_id=attempt.attempt_id,
    )
    pre_checkpoint = create_pre_attempt_checkpoint_ref(
        exec_job_id=job.exec_job_id,
        session_id=session.session_id,
        attempt_id=attempt.attempt_id,
        snapshot_source=(job, lease.lease_id, session.session_id, attempt.attempt_id),
        truth_label=label,
        created_at_tick=current_tick,
    )
    _record(
        ExecutionMessageKind.CHECKPOINT_BOUND,
        f"pre-attempt checkpoint ref {pre_checkpoint.checkpoint_ref_id}",
        attempt_id=attempt.attempt_id,
        causality_ref=pre_checkpoint.checkpoint_ref_id,
    )

    queue_entry = mark_queue_entry_running(queue_entry)
    claim = dataclasses.replace(claim, claim_status=QueueClaimStatus.RUNNING)
    worker_slot = dataclasses.replace(worker_slot, status=WorkerSlotStatus.RUNNING)

    # ---- the reused P4-EXEC-B governed submit path, unchanged ---- #
    bridge_execution = bridge.submit_once(
        request,
        job=job,
        lease=lease,
        session=session,
        attempt=attempt,
        card=card,
        current_tick=current_tick,
    )
    outcome = bridge_execution.outcome
    _record(
        ExecutionMessageKind.ATTEMPT_SUBMITTED,
        "attempt submitted through existing ExecRuntimeBridge",
        attempt_id=bridge_execution.attempt.attempt_id,
        causality_ref=bridge_execution.result.command_id,
    )
    _record(
        ExecutionMessageKind.OUTCOME_RECORDED,
        f"outcome {outcome.runtime_status.value}: {outcome.result_summary[:80]}",
        attempt_id=bridge_execution.attempt.attempt_id,
        causality_ref=outcome.outcome_id,
    )
    if not outcome.success:
        _record(
            ExecutionMessageKind.ERROR_RECORDED,
            f"runtime failure preserved: {(outcome.error_message or '')[:80]}",
            attempt_id=bridge_execution.attempt.attempt_id,
            causality_ref=outcome.outcome_id,
        )

    post_checkpoint = create_post_attempt_checkpoint_ref(
        exec_job_id=job.exec_job_id,
        session_id=session.session_id,
        attempt_id=bridge_execution.attempt.attempt_id,
        snapshot_source=outcome,
        truth_label=label,
        created_at_tick=current_tick,
    )
    _record(
        ExecutionMessageKind.CHECKPOINT_BOUND,
        f"post-attempt checkpoint ref {post_checkpoint.checkpoint_ref_id}",
        attempt_id=bridge_execution.attempt.attempt_id,
        causality_ref=post_checkpoint.checkpoint_ref_id,
    )
    rollback_ref = create_rollback_ref(pre_checkpoint, truth_label=label)
    _record(
        ExecutionMessageKind.ROLLBACK_REF_CREATED,
        f"rollback ref {rollback_ref.rollback_ref_id} (not executed; unavailable)",
        attempt_id=bridge_execution.attempt.attempt_id,
        causality_ref=rollback_ref.rollback_ref_id,
    )

    if outcome.success:
        queue_entry = mark_queue_entry_completed(
            queue_entry, completed_at_tick=current_tick
        )
        release_reason = "managed run completed"
    else:
        queue_entry = mark_queue_entry_failed(queue_entry, completed_at_tick=current_tick)
        release_reason = "managed run failed (runtime failure preserved)"
    worker_slot, claim = release_worker_slot(
        worker_slot, claim, released_at_tick=current_tick, release_reason=release_reason
    )
    _record(
        ExecutionMessageKind.WORKER_RELEASED,
        f"worker slot released: {release_reason}",
        attempt_id=bridge_execution.attempt.attempt_id,
    )

    result = ManagedRuntimeResult(
        managed_runtime_result_id="exec-managed-"
        + stable_hash((claim.claim_id, bridge_execution.result.bridge_result_id))[:16],
        queue_entry_id=queue_entry.queue_entry_id,
        worker_slot_id=worker_slot.worker_slot_id,
        claim_id=claim.claim_id,
        exec_job_id=job.exec_job_id,
        completed=True,
        success=outcome.success,
        truth_label=label,
        session_id=session.session_id,
        attempt_id=bridge_execution.attempt.attempt_id,
        outcome_id=outcome.outcome_id,
        pre_attempt_checkpoint_ref_id=pre_checkpoint.checkpoint_ref_id,
        post_attempt_checkpoint_ref_id=post_checkpoint.checkpoint_ref_id,
        rollback_ref_id=rollback_ref.rollback_ref_id,
        message_ids=tuple(message_ids),
        error_message=outcome.error_message,
    )
    return ManagedRuntimeExecution(
        result=result,
        queue_entry=queue_entry,
        worker_slot=worker_slot,
        claim=claim,
        log=log,
        bridge_execution=bridge_execution,
        pre_attempt_checkpoint=pre_checkpoint,
        post_attempt_checkpoint=post_checkpoint,
        rollback_ref=rollback_ref,
    )


@dataclass(frozen=True)
class NoWorkerPoolProof(_ExecCanonicalMixin):
    """Evidence that exactly one local worker slot exists — no pool."""

    reason: str
    contract_version: str = NO_WORKER_POOL_PROOF_VERSION
    single_local_worker_slot_only: bool = True
    worker_pool_available: bool = False
    concurrency_engine_available: bool = False

    def __post_init__(self) -> None:
        forbid_false(self, "single_local_worker_slot_only")
        forbid_true(self, "worker_pool_available", "concurrency_engine_available")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_worker_pool_proof() -> NoWorkerPoolProof:
    return NoWorkerPoolProof(reason=WORKER_POOL_UNAVAILABLE_REASON)


@dataclass(frozen=True)
class NoRemoteWorkerProof(_ExecCanonicalMixin):
    """Evidence that remote/distributed workers are unavailable."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_REMOTE_WORKER_PROOF_VERSION
    remote_worker_available: bool = False
    distributed_worker_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "remote_worker_available", "distributed_worker_available")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_remote_worker_proof() -> NoRemoteWorkerProof:
    return NoRemoteWorkerProof(
        reason=REMOTE_WORKER_UNAVAILABLE_REASON,
        future_pack_owner="post-P4 distributed runtime (operator-decided)",
    )
