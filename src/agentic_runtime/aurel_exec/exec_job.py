"""P4 ExecJob / ExecutionAttempt with submit-aware lifecycle (P4-EXEC-A/B).

P4-EXEC-A shipped the skeletons proving lease-before-attempt. P4-EXEC-B
expands both into lifecycle-capable objects for the first governed runtime
submit bridge. The laws are unchanged: a job is not execution by itself, a
job cannot run without a valid lease, a job cannot submit without a valid
session, and no attempt can claim a runtime submit that did not happen —
``runtime_submit_called=True`` is constructible only in submit-aware states
with a command id and session bound.

Nothing in this module executes: transitions are pure frozen-replace state
arithmetic. The only path to an actual submit is the ExecRuntimeBridge.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .exec_admission import ExecAdmissionDecision
from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_lease import ExecutionLease, LeaseValidationResult, validate_execution_lease
from .exec_types import (
    ATTEMPT_LIFECYCLE_TRANSITIONS,
    JOB_LIFECYCLE_TRANSITIONS,
    SUBMIT_AWARE_ATTEMPT_STATES,
    ExecAdmissionState,
    ExecLifecycleState,
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXEC_JOB_VERSION = "exec_job.v2"
EXECUTION_ATTEMPT_VERSION = "execution_attempt.v2"


def _require_transition(
    kind: str,
    transitions: dict[ExecLifecycleState, tuple[ExecLifecycleState, ...]],
    current: ExecLifecycleState,
    new: ExecLifecycleState,
) -> None:
    if new not in transitions[current]:
        raise AurelExecValidationError(
            f"invalid {kind} lifecycle transition {current.value} -> {new.value}",
            code=AurelExecErrorCode.INVALID_LIFECYCLE_TRANSITION,
            field="lifecycle_state",
        )


@dataclass(frozen=True)
class ExecJob(_ExecCanonicalMixin):
    """A lifecycle-capable future executable unit. A job is not execution
    by itself and cannot reach RUNNING except through the runtime bridge."""

    exec_job_id: str
    admission_decision_id: str
    source_p3_candidate_ref: str
    lifecycle_state: ExecLifecycleState
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_JOB_VERSION
    lease_id: str | None = None
    session_id: str | None = None
    source_flow_run_id: str | None = None
    source_atomic_unit_id: str | None = None
    requested_execution_mode: ExecutionMode | None = None
    requested_tool_name: str | None = None
    updated_at_tick: int | None = None

    def __post_init__(self) -> None:
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(
            self, "admission_decision_id", code=AurelExecErrorCode.EMPTY_DECISION_ID
        )
        require_allowed_truth_label(self)
        if self.lifecycle_state in (
            ExecLifecycleState.READY_TO_SUBMIT,
            ExecLifecycleState.SUBMITTED,
        ):
            raise AurelExecValidationError(
                f"{self.lifecycle_state.value} is an attempt-only state",
                code=AurelExecErrorCode.INVALID_LIFECYCLE_TRANSITION,
                field="lifecycle_state",
            )

    @property
    def job_hash(self) -> str:
        return stable_hash(self)


def transition_exec_job(
    job: ExecJob,
    new_state: ExecLifecycleState,
    *,
    lease_id: str | None = None,
    session_id: str | None = None,
    updated_at_tick: int | None = None,
) -> ExecJob:
    """Deterministically transition a job. Invalid transitions fail closed.
    Transitioning is state arithmetic, never execution."""
    _require_transition("job", JOB_LIFECYCLE_TRANSITIONS, job.lifecycle_state, new_state)
    return dataclasses.replace(
        job,
        lifecycle_state=new_state,
        lease_id=lease_id if lease_id is not None else job.lease_id,
        session_id=session_id if session_id is not None else job.session_id,
        updated_at_tick=updated_at_tick if updated_at_tick is not None else job.updated_at_tick,
    )


def bind_lease_to_job(job: ExecJob, lease: ExecutionLease) -> ExecJob:
    """Bind an issued lease to its job (ADMITTED -> LEASED). Not execution."""
    if lease.exec_job_id != job.exec_job_id:
        raise AurelExecValidationError(
            "lease was issued for a different job",
            code=AurelExecErrorCode.LEASE_JOB_MISMATCH,
            field="exec_job_id",
        )
    return transition_exec_job(job, ExecLifecycleState.LEASED, lease_id=lease.lease_id)


@dataclass(frozen=True)
class ExecutionAttempt(_ExecCanonicalMixin):
    """Submit-aware execution attempt.

    Lease-before-attempt and submit-truth laws hold structurally:
    ``runtime_submit_called=True`` requires a submit-aware lifecycle state,
    a bound session, and a command id — an attempt claiming a submit that
    never went through the bridge is unconstructible. SUBMITTED/SUCCEEDED
    without ``runtime_submit_called=True`` is likewise unconstructible.
    """

    attempt_id: str
    exec_job_id: str
    lease_id: str
    lifecycle_state: ExecLifecycleState
    truth_label: ExecTruthLabel
    runtime_submit_called: bool = False
    contract_version: str = EXECUTION_ATTEMPT_VERSION
    session_id: str | None = None
    runtime_submit_ref: str | None = None
    command_id: str | None = None
    command_envelope_hash: str | None = None
    outcome_id: str | None = None
    trace_binding_id: str | None = None
    error_message: str | None = None
    started_at_tick: int | None = None
    ended_at_tick: int | None = None

    def __post_init__(self) -> None:
        require_nonempty(self, "attempt_id", code=AurelExecErrorCode.EMPTY_ATTEMPT_ID)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "lease_id", code=AurelExecErrorCode.EMPTY_LEASE_ID)
        require_allowed_truth_label(self)
        if self.session_id is not None and not self.session_id.strip():
            raise AurelExecValidationError(
                "session_id may not be blank when set",
                code=AurelExecErrorCode.EMPTY_SESSION_ID,
                field="session_id",
            )
        if self.runtime_submit_called:
            if self.lifecycle_state not in SUBMIT_AWARE_ATTEMPT_STATES:
                raise AurelExecValidationError(
                    "runtime_submit_called=True requires a submit-aware "
                    f"lifecycle state, not {self.lifecycle_state.value}",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="runtime_submit_called",
                )
            if not self.command_id:
                raise AurelExecValidationError(
                    "runtime_submit_called=True requires a command_id",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="command_id",
                )
            if not self.session_id:
                raise AurelExecValidationError(
                    "runtime_submit_called=True requires a bound session",
                    code=AurelExecErrorCode.SESSION_REQUIRED,
                    field="session_id",
                )
        elif self.lifecycle_state in (
            ExecLifecycleState.SUBMITTED,
            ExecLifecycleState.SUCCEEDED,
        ):
            raise AurelExecValidationError(
                f"{self.lifecycle_state.value} requires runtime_submit_called=True",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_submit_called",
            )

    @property
    def attempt_hash(self) -> str:
        return stable_hash(self)


def transition_execution_attempt(
    attempt: ExecutionAttempt,
    new_state: ExecLifecycleState,
    **updates: object,
) -> ExecutionAttempt:
    """Deterministically transition an attempt. Invalid transitions fail
    closed; the submit-truth guards re-run on the new instance."""
    _require_transition(
        "attempt", ATTEMPT_LIFECYCLE_TRANSITIONS, attempt.lifecycle_state, new_state
    )
    return dataclasses.replace(attempt, lifecycle_state=new_state, **updates)


def create_exec_job(
    decision: ExecAdmissionDecision,
    *,
    source_p3_candidate_ref: str,
    requested_execution_mode: ExecutionMode | None = None,
    requested_tool_name: str | None = None,
) -> ExecJob:
    """Create a job from an ADMIT decision only. Creating a job executes nothing."""
    if decision.state is not ExecAdmissionState.ADMIT:
        raise AurelExecValidationError(
            f"job denied: admission state is {decision.state.value}, not ADMIT",
            code=AurelExecErrorCode.JOB_DENIED,
            field="state",
        )
    exec_job_id = "exec-job-" + stable_hash(decision.decision_id)[:16]
    return ExecJob(
        exec_job_id=exec_job_id,
        admission_decision_id=decision.decision_id,
        source_p3_candidate_ref=source_p3_candidate_ref,
        lifecycle_state=ExecLifecycleState.ADMITTED,
        truth_label=decision.truth_label,
        requested_execution_mode=requested_execution_mode,
        requested_tool_name=requested_tool_name,
    )


def create_execution_attempt(
    job: ExecJob,
    lease: ExecutionLease,
    *,
    current_tick: int,
    session_id: str | None = None,
) -> tuple[ExecutionAttempt, LeaseValidationResult]:
    """Create an attempt skeleton only under a currently valid lease.

    Lease-before-attempt law: an expired, revoked, or job-mismatched lease
    denies the attempt fail-closed. The created attempt performs nothing —
    submitting requires the ExecRuntimeBridge with a valid session.
    """
    if lease.exec_job_id != job.exec_job_id:
        raise AurelExecValidationError(
            "attempt denied: lease was issued for a different job",
            code=AurelExecErrorCode.LEASE_JOB_MISMATCH,
            field="exec_job_id",
        )
    validation = validate_execution_lease(lease, current_tick=current_tick)
    if not validation.valid:
        code = AurelExecErrorCode.LEASE_INVALID
        if validation.revoked:
            code = AurelExecErrorCode.LEASE_REVOKED
        elif validation.expired:
            code = AurelExecErrorCode.LEASE_EXPIRED
        raise AurelExecValidationError(
            f"attempt denied: {validation.reason}",
            code=code,
            field="lease_id",
        )
    attempt_id = "exec-attempt-" + stable_hash(
        (job.exec_job_id, lease.lease_id, current_tick)
    )[:16]
    attempt = ExecutionAttempt(
        attempt_id=attempt_id,
        exec_job_id=job.exec_job_id,
        lease_id=lease.lease_id,
        lifecycle_state=ExecLifecycleState.ATTEMPT_PENDING,
        truth_label=job.truth_label,
        session_id=session_id,
        started_at_tick=current_tick,
    )
    return attempt, validation
