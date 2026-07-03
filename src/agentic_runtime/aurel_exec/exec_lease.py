"""P4-EXEC-A execution lease kernel.

An ``ExecutionLease`` is a scoped, expiring, revocable capability token
issued only from an ADMIT decision. It binds allowed mode / tool / sandbox /
args hash / budget / authority / policy refs so P4-EXEC-B can later check a
runtime attempt against exactly this scope.

A lease is not execution: issuing, validating, or revoking a lease submits
nothing, dispatches nothing, and authorizes nothing outside P9. Time is a
deterministic logical tick supplied by the caller — no wall clock is read.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum

from .exec_admission import (
    ExecAdmissionDecision,
    ExecAdmissionRequest,
    ExecMissingRequirement,
)
from .exec_errors import AurelExecError, AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecAdmissionState,
    ExecMissingRequirementKind,
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

LEASE_SCOPE_VERSION = "lease_scope.v1"
EXECUTION_LEASE_VERSION = "execution_lease.v1"
LEASE_VALIDATION_RESULT_VERSION = "lease_validation_result.v1"


class LeaseDenialReason(str, Enum):
    DECISION_NOT_ADMIT = "DECISION_NOT_ADMIT"
    DECISION_REQUEST_MISMATCH = "DECISION_REQUEST_MISMATCH"


class LeaseRevocationState(str, Enum):
    NOT_REVOKED = "NOT_REVOKED"
    REVOKED = "REVOKED"


class ExecLeaseDenied(AurelExecError):
    """Raised when a lease cannot be issued. Denial is data, not execution."""

    def __init__(self, message: str, *, denial_reason: LeaseDenialReason) -> None:
        super().__init__(message)
        self.denial_reason = denial_reason


@dataclass(frozen=True)
class LeaseScope(_ExecCanonicalMixin):
    """The execution scope a lease binds. A scope names limits; it grants
    no P9 authority and executes nothing."""

    allowed_execution_mode: ExecutionMode
    allowed_tool_name: str | None
    allowed_args_hash: str | None
    sandbox_profile: str | None
    budget_scope_ref: str | None
    authority_scope_ref: str | None
    policy_snapshot_ref: str | None
    contract_version: str = LEASE_SCOPE_VERSION


@dataclass(frozen=True)
class ExecutionLease(_ExecCanonicalMixin):
    """Scoped, expiring, revocable execution capability token.

    No attempt may exist without a valid lease; an expired or revoked lease
    is invalid; and holding a lease is not execution and not authorization.
    """

    lease_id: str
    exec_job_id: str
    admission_decision_id: str
    scope: LeaseScope
    issued_at_tick: int
    max_attempts: int
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_LEASE_VERSION
    issuer_ref: str | None = None
    expires_at_tick: int | None = None
    revoked: bool = False
    revocation_state: LeaseRevocationState = LeaseRevocationState.NOT_REVOKED

    def __post_init__(self) -> None:
        require_nonempty(self, "lease_id", code=AurelExecErrorCode.EMPTY_LEASE_ID)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(
            self, "admission_decision_id", code=AurelExecErrorCode.EMPTY_DECISION_ID
        )
        require_allowed_truth_label(self)
        if self.max_attempts < 1:
            raise AurelExecValidationError(
                "max_attempts must be at least 1",
                code=AurelExecErrorCode.INVALID_MAX_ATTEMPTS,
                field="max_attempts",
            )
        if self.expires_at_tick is not None and self.expires_at_tick <= self.issued_at_tick:
            raise AurelExecValidationError(
                "expires_at_tick must be after issued_at_tick",
                code=AurelExecErrorCode.INVALID_LEASE_WINDOW,
                field="expires_at_tick",
            )
        if self.revoked != (self.revocation_state is LeaseRevocationState.REVOKED):
            raise AurelExecValidationError(
                "revoked flag and revocation_state must agree",
                code=AurelExecErrorCode.REVOCATION_STATE_MISMATCH,
                field="revocation_state",
            )

    @property
    def lease_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class LeaseValidationResult(_ExecCanonicalMixin):
    """Deterministic, side-effect-free lease validity verdict."""

    valid: bool
    reason: str
    lease_id: str
    expired: bool
    revoked: bool
    truth_label: ExecTruthLabel
    missing_requirements: tuple[ExecMissingRequirement, ...] = ()
    contract_version: str = LEASE_VALIDATION_RESULT_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_allowed_truth_label(self)
        if self.valid and (self.expired or self.revoked):
            raise AurelExecValidationError(
                "an expired or revoked lease can never be valid",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="valid",
            )


def issue_execution_lease(
    decision: ExecAdmissionDecision,
    request: ExecAdmissionRequest,
    *,
    exec_job_id: str,
    issued_at_tick: int,
    expires_at_tick: int | None = None,
    max_attempts: int = 1,
    issuer_ref: str | None = None,
) -> ExecutionLease:
    """Issue a scoped lease from an ADMIT decision. Issuing executes nothing.

    Non-ADMIT decisions (HOLD/REJECT/REQUIRE_*/ERROR) are denied with
    ``ExecLeaseDenied``; a decision/request mismatch is denied likewise.
    """
    if decision.request_id != request.request_id:
        raise ExecLeaseDenied(
            "decision does not belong to this request",
            denial_reason=LeaseDenialReason.DECISION_REQUEST_MISMATCH,
        )
    if decision.state is not ExecAdmissionState.ADMIT:
        raise ExecLeaseDenied(
            f"lease denied: admission state is {decision.state.value}, not ADMIT",
            denial_reason=LeaseDenialReason.DECISION_NOT_ADMIT,
        )
    scope = LeaseScope(
        allowed_execution_mode=request.requested_execution_mode,
        allowed_tool_name=request.requested_tool_name,
        allowed_args_hash=request.requested_args_hash,
        sandbox_profile=request.requested_sandbox_profile,
        budget_scope_ref=request.requested_budget_ref,
        authority_scope_ref=request.requested_authority_ref,
        policy_snapshot_ref=request.requested_policy_context_ref,
    )
    lease_id = "exec-lease-" + stable_hash(
        (decision.decision_id, exec_job_id, issued_at_tick)
    )[:16]
    return ExecutionLease(
        lease_id=lease_id,
        exec_job_id=exec_job_id,
        admission_decision_id=decision.decision_id,
        scope=scope,
        issued_at_tick=issued_at_tick,
        max_attempts=max_attempts,
        truth_label=decision.truth_label,
        issuer_ref=issuer_ref,
        expires_at_tick=expires_at_tick,
    )


def validate_execution_lease(
    lease: ExecutionLease, *, current_tick: int
) -> LeaseValidationResult:
    """Deterministic lease validity check at a logical tick. No side effects."""
    expired = lease.expires_at_tick is not None and current_tick >= lease.expires_at_tick
    revoked = lease.revoked
    if revoked:
        reason = "lease is revoked; a revoked lease is invalid"
    elif expired:
        reason = "lease is expired; an expired lease is invalid"
    else:
        reason = (
            "lease is valid at this tick; a valid lease is still not execution "
            "and not P9 authorization"
        )
    missing: tuple[ExecMissingRequirement, ...] = ()
    if revoked or expired:
        missing = (
            ExecMissingRequirement(
                kind=ExecMissingRequirementKind.VALID_LEASE,
                explanation=reason,
            ),
        )
    return LeaseValidationResult(
        valid=not revoked and not expired,
        reason=reason,
        lease_id=lease.lease_id,
        expired=expired,
        revoked=revoked,
        truth_label=lease.truth_label,
        missing_requirements=missing,
    )


def revoke_execution_lease(lease: ExecutionLease) -> ExecutionLease:
    """Return a revoked copy of the lease. Revocation is data, not execution."""
    return dataclasses.replace(
        lease,
        revoked=True,
        revocation_state=LeaseRevocationState.REVOKED,
    )
