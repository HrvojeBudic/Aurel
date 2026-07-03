"""P4-EXEC-A minimal ExecJob / ExecutionAttempt skeleton.

An ``ExecJob`` is a future executable unit created only from an ADMIT
decision — it is not execution and implies no runtime.submit. The
``ExecutionAttempt`` skeleton exists only to prove lease-before-attempt:
no attempt can be constructed without a currently valid lease for the same
job, and ``runtime_submit_called`` is structurally False — constructing an
attempt that claims a runtime submit is impossible in this pack.
"""

from __future__ import annotations

from dataclasses import dataclass

from .exec_admission import ExecAdmissionDecision
from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_lease import ExecutionLease, LeaseValidationResult, validate_execution_lease
from .exec_types import (
    ExecAdmissionState,
    ExecLifecycleState,
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXEC_JOB_VERSION = "exec_job.v1"
EXECUTION_ATTEMPT_VERSION = "execution_attempt.v1"


@dataclass(frozen=True)
class ExecJob(_ExecCanonicalMixin):
    """A future executable unit. A job is not execution and does not dispatch."""

    exec_job_id: str
    admission_decision_id: str
    source_p3_candidate_ref: str
    lifecycle_state: ExecLifecycleState
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_JOB_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(
            self, "admission_decision_id", code=AurelExecErrorCode.EMPTY_DECISION_ID
        )
        require_allowed_truth_label(self)

    @property
    def job_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class ExecutionAttempt(_ExecCanonicalMixin):
    """Attempt skeleton proving lease-before-attempt.

    ``runtime_submit_called`` must remain False: an attempt claiming a
    runtime submit is unconstructible in P4-EXEC-A. This skeleton is not a
    runtime attempt — conversion belongs to P4-EXEC-B.
    """

    attempt_id: str
    exec_job_id: str
    lease_id: str
    lifecycle_state: ExecLifecycleState
    truth_label: ExecTruthLabel
    runtime_submit_called: bool = False
    contract_version: str = EXECUTION_ATTEMPT_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "attempt_id", code=AurelExecErrorCode.EMPTY_ATTEMPT_ID)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "lease_id", code=AurelExecErrorCode.EMPTY_LEASE_ID)
        require_allowed_truth_label(self)
        forbid_true(self, "runtime_submit_called")


def create_exec_job(decision: ExecAdmissionDecision, *, source_p3_candidate_ref: str) -> ExecJob:
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
    )


def create_execution_attempt(
    job: ExecJob,
    lease: ExecutionLease,
    *,
    current_tick: int,
) -> tuple[ExecutionAttempt, LeaseValidationResult]:
    """Create an attempt skeleton only under a currently valid lease.

    Lease-before-attempt law: an expired, revoked, or job-mismatched lease
    denies the attempt fail-closed. The created attempt performs nothing —
    runtime.submit stays unavailable until P4-EXEC-B.
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
    )
    return attempt, validation
