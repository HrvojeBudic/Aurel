"""P4-EXEC-C ExecQueueEntry — local execution queue entry.

A queue entry represents an admitted + leased job waiting for a local
execution claim. A queue entry is not a scheduler: P3 AurelFlow schedules
and proposes; this queue only holds jobs that already passed admission and
hold a lease. A queue entry does not execute, does not dispatch remotely,
and does not replace P3 scheduling — those claims are structurally
unconstructible.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_job import ExecJob
from .exec_lease import ExecutionLease, validate_execution_lease
from .exec_types import (
    ExecLifecycleState,
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXEC_QUEUE_ENTRY_VERSION = "exec_queue_entry.v1"

QUEUE_IS_NOT_SCHEDULER_REASON = (
    "the local execution queue holds admitted + leased jobs only; P3 "
    "AurelFlow schedules and proposes — a queue entry schedules nothing"
)


class ExecQueueState(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


QUEUE_STATE_TRANSITIONS: dict[ExecQueueState, tuple[ExecQueueState, ...]] = {
    ExecQueueState.PENDING: (
        ExecQueueState.CLAIMED,
        ExecQueueState.CANCELLED,
        ExecQueueState.BLOCKED,
        ExecQueueState.ERROR,
    ),
    ExecQueueState.CLAIMED: (
        ExecQueueState.RUNNING,
        ExecQueueState.CANCELLED,
        ExecQueueState.BLOCKED,
        ExecQueueState.ERROR,
    ),
    ExecQueueState.RUNNING: (
        ExecQueueState.COMPLETED,
        ExecQueueState.FAILED,
        ExecQueueState.ERROR,
    ),
    ExecQueueState.COMPLETED: (),
    ExecQueueState.FAILED: (),
    ExecQueueState.CANCELLED: (),
    ExecQueueState.BLOCKED: (),
    ExecQueueState.ERROR: (),
}

_QUEUE_ENTRY_ELIGIBLE_JOB_STATES = (
    ExecLifecycleState.LEASED,
    ExecLifecycleState.SESSION_BOUND,
)


@dataclass(frozen=True)
class ExecQueueEntry(_ExecCanonicalMixin):
    """One admitted + leased job waiting for a local execution claim.
    Not a scheduler, not execution, not remote dispatch."""

    queue_entry_id: str
    exec_job_id: str
    lease_id: str
    queue_state: ExecQueueState
    priority: int
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_QUEUE_ENTRY_VERSION
    session_id: str | None = None
    created_at_tick: int | None = None
    claimed_at_tick: int | None = None
    completed_at_tick: int | None = None
    worker_slot_id: str | None = None
    schedules_workflows: bool = False
    executes: bool = False
    dispatches_remotely: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "queue_entry_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "lease_id", code=AurelExecErrorCode.EMPTY_LEASE_ID)
        require_allowed_truth_label(self)
        forbid_true(self, "schedules_workflows", "executes", "dispatches_remotely")
        if self.queue_state is ExecQueueState.CLAIMED and not self.worker_slot_id:
            raise AurelExecValidationError(
                "a CLAIMED queue entry must reference its worker slot",
                code=AurelExecErrorCode.QUEUE_STATE_INVALID,
                field="worker_slot_id",
            )

    @property
    def queue_entry_hash(self) -> str:
        return stable_hash(self)


def _transition_queue_entry(
    entry: ExecQueueEntry, new_state: ExecQueueState, **updates: object
) -> ExecQueueEntry:
    if new_state not in QUEUE_STATE_TRANSITIONS[entry.queue_state]:
        raise AurelExecValidationError(
            f"invalid queue transition {entry.queue_state.value} -> {new_state.value}",
            code=AurelExecErrorCode.QUEUE_STATE_INVALID,
            field="queue_state",
        )
    return dataclasses.replace(entry, queue_state=new_state, **updates)


def create_queue_entry(
    job: ExecJob,
    lease: ExecutionLease,
    *,
    current_tick: int,
    priority: int = 0,
) -> ExecQueueEntry:
    """Enqueue an admitted + leased job locally. Enqueueing executes nothing
    and schedules nothing — P3 already proposed and P4-A already admitted."""
    if job.lifecycle_state not in _QUEUE_ENTRY_ELIGIBLE_JOB_STATES:
        raise AurelExecValidationError(
            f"queue requires an admitted + leased job; job is "
            f"{job.lifecycle_state.value}",
            code=AurelExecErrorCode.QUEUE_ENTRY_INVALID,
            field="lifecycle_state",
        )
    if lease.exec_job_id != job.exec_job_id or job.lease_id != lease.lease_id:
        raise AurelExecValidationError(
            "queue entry requires the job's own bound lease",
            code=AurelExecErrorCode.LEASE_JOB_MISMATCH,
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
            f"queue entry blocked: {validation.reason}", code=code, field="lease_id"
        )
    queue_entry_id = "exec-queue-" + stable_hash((job.exec_job_id, current_tick))[:16]
    return ExecQueueEntry(
        queue_entry_id=queue_entry_id,
        exec_job_id=job.exec_job_id,
        lease_id=lease.lease_id,
        queue_state=ExecQueueState.PENDING,
        priority=priority,
        truth_label=job.truth_label,
        session_id=job.session_id,
        created_at_tick=current_tick,
    )


def mark_queue_entry_claimed(
    entry: ExecQueueEntry, *, worker_slot_id: str, claimed_at_tick: int
) -> ExecQueueEntry:
    return _transition_queue_entry(
        entry,
        ExecQueueState.CLAIMED,
        worker_slot_id=worker_slot_id,
        claimed_at_tick=claimed_at_tick,
    )


def mark_queue_entry_running(entry: ExecQueueEntry) -> ExecQueueEntry:
    return _transition_queue_entry(entry, ExecQueueState.RUNNING)


def mark_queue_entry_completed(
    entry: ExecQueueEntry, *, completed_at_tick: int
) -> ExecQueueEntry:
    return _transition_queue_entry(
        entry, ExecQueueState.COMPLETED, completed_at_tick=completed_at_tick
    )


def mark_queue_entry_failed(
    entry: ExecQueueEntry, *, completed_at_tick: int
) -> ExecQueueEntry:
    return _transition_queue_entry(
        entry, ExecQueueState.FAILED, completed_at_tick=completed_at_tick
    )


def block_queue_entry(entry: ExecQueueEntry) -> ExecQueueEntry:
    return _transition_queue_entry(entry, ExecQueueState.BLOCKED)
