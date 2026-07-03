"""P4-EXEC-B ExecutionSession — minimal execution continuity.

A session gives even a single governed attempt identity continuity so that
future runtime management (P4-EXEC-C worker/queue/bus/checkpoint shape) has
something real to manage. A session is not a workflow, not a queue, not a
worker, and not a checkpoint system — those claims are structurally
unconstructible. A session is required before runtime submit: the bridge
refuses to submit without an active session.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_job import ExecJob, transition_exec_job
from .exec_types import (
    ExecLifecycleState,
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXECUTION_SESSION_VERSION = "execution_session.v1"


class ExecutionSessionStatus(str, Enum):
    OPEN = "OPEN"
    RUNNING = "RUNNING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    ERROR = "ERROR"


SESSION_STATUS_TRANSITIONS: dict[ExecutionSessionStatus, tuple[ExecutionSessionStatus, ...]] = {
    ExecutionSessionStatus.OPEN: (
        ExecutionSessionStatus.RUNNING,
        ExecutionSessionStatus.CLOSED,
        ExecutionSessionStatus.FAILED,
        ExecutionSessionStatus.ERROR,
    ),
    ExecutionSessionStatus.RUNNING: (
        ExecutionSessionStatus.CLOSED,
        ExecutionSessionStatus.FAILED,
        ExecutionSessionStatus.ERROR,
    ),
    ExecutionSessionStatus.CLOSED: (),
    ExecutionSessionStatus.FAILED: (),
    ExecutionSessionStatus.ERROR: (),
}

ACTIVE_SESSION_STATUSES: tuple[ExecutionSessionStatus, ...] = (
    ExecutionSessionStatus.OPEN,
    ExecutionSessionStatus.RUNNING,
)

_TERMINAL_SESSION_STATUSES = (
    ExecutionSessionStatus.CLOSED,
    ExecutionSessionStatus.FAILED,
)


@dataclass(frozen=True)
class ExecutionSession(_ExecCanonicalMixin):
    """Minimal execution continuity for one job. Required for submit."""

    session_id: str
    exec_job_id: str
    status: ExecutionSessionStatus
    opened_at_tick: int
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_SESSION_VERSION
    closed_at_tick: int | None = None
    source_flow_run_id: str | None = None
    operator_context_ref: str | None = None
    runtime_context_ref: str | None = None
    sandbox_scope_ref: str | None = None
    trace_run_ref: str | None = None
    is_workflow: bool = False
    is_queue: bool = False
    is_worker: bool = False
    is_checkpoint: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "session_id", code=AurelExecErrorCode.EMPTY_SESSION_ID)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_allowed_truth_label(self)
        forbid_true(self, "is_workflow", "is_queue", "is_worker", "is_checkpoint")
        if self.status in _TERMINAL_SESSION_STATUSES:
            if self.closed_at_tick is None or self.closed_at_tick < self.opened_at_tick:
                raise AurelExecValidationError(
                    f"{self.status.value} session requires closed_at_tick >= opened_at_tick",
                    code=AurelExecErrorCode.INVALID_SESSION_WINDOW,
                    field="closed_at_tick",
                )
        elif self.closed_at_tick is not None:
            raise AurelExecValidationError(
                f"{self.status.value} session may not carry closed_at_tick",
                code=AurelExecErrorCode.INVALID_SESSION_WINDOW,
                field="closed_at_tick",
            )

    @property
    def session_hash(self) -> str:
        return stable_hash(self)

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_SESSION_STATUSES


def _transition_session(
    session: ExecutionSession,
    new_status: ExecutionSessionStatus,
    *,
    closed_at_tick: int | None = None,
) -> ExecutionSession:
    if new_status not in SESSION_STATUS_TRANSITIONS[session.status]:
        raise AurelExecValidationError(
            f"invalid session transition {session.status.value} -> {new_status.value}",
            code=AurelExecErrorCode.SESSION_INVALID,
            field="status",
        )
    return dataclasses.replace(session, status=new_status, closed_at_tick=closed_at_tick)


def open_execution_session(
    job: ExecJob,
    *,
    opened_at_tick: int,
    source_flow_run_id: str | None = None,
    operator_context_ref: str | None = None,
    runtime_context_ref: str | None = None,
    sandbox_scope_ref: str | None = None,
    trace_run_ref: str | None = None,
) -> ExecutionSession:
    """Open a session for a LEASED job. Opening a session executes nothing."""
    if job.lifecycle_state is not ExecLifecycleState.LEASED:
        raise AurelExecValidationError(
            f"session requires a LEASED job, not {job.lifecycle_state.value}",
            code=AurelExecErrorCode.SESSION_INVALID,
            field="lifecycle_state",
        )
    if not job.lease_id:
        raise AurelExecValidationError(
            "session requires the job to carry its lease_id",
            code=AurelExecErrorCode.EMPTY_LEASE_ID,
            field="lease_id",
        )
    session_id = "exec-session-" + stable_hash((job.exec_job_id, opened_at_tick))[:16]
    return ExecutionSession(
        session_id=session_id,
        exec_job_id=job.exec_job_id,
        status=ExecutionSessionStatus.OPEN,
        opened_at_tick=opened_at_tick,
        truth_label=job.truth_label,
        source_flow_run_id=source_flow_run_id,
        operator_context_ref=operator_context_ref,
        runtime_context_ref=runtime_context_ref,
        sandbox_scope_ref=sandbox_scope_ref,
        trace_run_ref=trace_run_ref,
    )


def mark_session_running(session: ExecutionSession) -> ExecutionSession:
    return _transition_session(session, ExecutionSessionStatus.RUNNING)


def close_execution_session(
    session: ExecutionSession, *, closed_at_tick: int
) -> ExecutionSession:
    return _transition_session(
        session, ExecutionSessionStatus.CLOSED, closed_at_tick=closed_at_tick
    )


def mark_session_failed(
    session: ExecutionSession, *, closed_at_tick: int
) -> ExecutionSession:
    return _transition_session(
        session, ExecutionSessionStatus.FAILED, closed_at_tick=closed_at_tick
    )


def bind_session_to_job(job: ExecJob, session: ExecutionSession) -> ExecJob:
    """Bind an active session to its job (LEASED -> SESSION_BOUND)."""
    if session.exec_job_id != job.exec_job_id:
        raise AurelExecValidationError(
            "session was opened for a different job",
            code=AurelExecErrorCode.SESSION_JOB_MISMATCH,
            field="exec_job_id",
        )
    if not session.active:
        raise AurelExecValidationError(
            f"cannot bind a {session.status.value} session",
            code=AurelExecErrorCode.SESSION_INVALID,
            field="status",
        )
    return transition_exec_job(
        job, ExecLifecycleState.SESSION_BOUND, session_id=session.session_id
    )
