"""P4-EXEC-A read-only projection, boundary proofs, and P4-EXEC-B handoff.

``ExecProjection`` exposes admission / lease / job / attempt-guard state and
honestly marks runtime.submit, trace verification, and policy/Custos
enforcement unavailable. A projection is not execution and mutates nothing.

The four boundary proof objects are report evidence only: they prove the
declared posture of this pack's contracts, not runtime behavior beyond this
pack's no-side-effect checks. The ``P4ExecAHandoffFrame`` names exactly what
P4-EXEC-B may consume later; a handoff frame is not a runtime bridge.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exec_admission import (
    STANDARD_UNAVAILABLE_REASONS,
    ExecAdmissionDecision,
    ExecUnavailableReason,
)
from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_job import ExecJob, ExecutionAttempt
from .exec_lease import ExecutionLease, LeaseValidationResult
from .exec_types import (
    CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
    RAW_EXECUTION_UNAVAILABLE_REASON,
    RUNTIME_SUBMIT_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    ExecAdmissionState,
    ExecLifecycleState,
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
)

EXEC_PROJECTION_VERSION = "exec_projection.v1"
P4_EXEC_A_HANDOFF_FRAME_VERSION = "p4_exec_a_handoff_frame.v1"
NO_RUNTIME_SUBMIT_PROOF_VERSION = "no_runtime_submit_proof.v1"
NO_RAW_EXECUTION_PROOF_VERSION = "no_raw_execution_proof.v1"
NO_TRACE_VERIFIED_PROOF_VERSION = "no_trace_verified_proof.v1"
NO_CUSTOS_ENFORCEMENT_PROOF_VERSION = "no_custos_enforcement_proof.v1"

FUTURE_RUNTIME_BRIDGE_STEPS: tuple[str, ...] = (
    "ExecJob",
    "ExecutionLease",
    "ExecutionAttempt",
    "CommandEnvelope",
    "AgenticRuntime.submit()",
    "ExecutionOutcome",
)
"""The minimal future runtime bridge P4-EXEC-B builds. Naming the chain is
not building it: no step here is wired or callable in P4-EXEC-A."""


class ExecLeaseProjectionState(str, Enum):
    NO_LEASE = "NO_LEASE"
    LEASE_VALID = "LEASE_VALID"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    LEASE_REVOKED = "LEASE_REVOKED"


class ExecAttemptGuardState(str, Enum):
    NO_ATTEMPT = "NO_ATTEMPT"
    ATTEMPT_PENDING_WITH_VALID_LEASE = "ATTEMPT_PENDING_WITH_VALID_LEASE"
    BLOCKED_NO_VALID_LEASE = "BLOCKED_NO_VALID_LEASE"


@dataclass(frozen=True)
class ExecProjection(_ExecCanonicalMixin):
    """Read-only admission/lease/job/attempt-guard view. Not execution."""

    admission_state: ExecAdmissionState
    lease_state: ExecLeaseProjectionState
    job_state: ExecLifecycleState | None
    attempt_guard_state: ExecAttemptGuardState
    truth_labels: tuple[ExecTruthLabel, ...]
    unavailable_reasons: tuple[ExecUnavailableReason, ...]
    contract_version: str = EXEC_PROJECTION_VERSION
    runtime_submit_available: bool = False
    runtime_submit_unavailable_reason: str = RUNTIME_SUBMIT_UNAVAILABLE_REASON
    trace_verified_available: bool = False
    trace_verified_unavailable_reason: str = TRACE_VERIFICATION_UNAVAILABLE_REASON
    policy_enforcement_available: bool = False
    policy_enforcement_unavailable_reason: str = CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON
    read_only: bool = True

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "runtime_submit_available",
            "trace_verified_available",
            "policy_enforcement_available",
        )
        forbid_false(self, "read_only")
        require_nonempty(
            self, "runtime_submit_unavailable_reason", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(
            self, "trace_verified_unavailable_reason", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(
            self,
            "policy_enforcement_unavailable_reason",
            code=AurelExecErrorCode.EMPTY_FIELD,
        )


def build_exec_projection(
    decision: ExecAdmissionDecision,
    *,
    lease: ExecutionLease | None = None,
    lease_validation: LeaseValidationResult | None = None,
    job: ExecJob | None = None,
    attempt: ExecutionAttempt | None = None,
) -> ExecProjection:
    """Project admission/lease/job/attempt state read-only. Mutates nothing."""
    if lease is None:
        lease_state = ExecLeaseProjectionState.NO_LEASE
    elif lease_validation is not None and lease_validation.revoked:
        lease_state = ExecLeaseProjectionState.LEASE_REVOKED
    elif lease_validation is not None and lease_validation.expired:
        lease_state = ExecLeaseProjectionState.LEASE_EXPIRED
    elif lease_validation is not None and lease_validation.valid:
        lease_state = ExecLeaseProjectionState.LEASE_VALID
    elif lease.revoked:
        lease_state = ExecLeaseProjectionState.LEASE_REVOKED
    else:
        lease_state = ExecLeaseProjectionState.NO_LEASE

    if attempt is not None:
        attempt_guard_state = ExecAttemptGuardState.ATTEMPT_PENDING_WITH_VALID_LEASE
    elif lease_state is ExecLeaseProjectionState.LEASE_VALID:
        attempt_guard_state = ExecAttemptGuardState.NO_ATTEMPT
    else:
        attempt_guard_state = ExecAttemptGuardState.BLOCKED_NO_VALID_LEASE

    labels: list[ExecTruthLabel] = [decision.truth_label]
    for obj in (lease, job, attempt):
        if obj is not None and obj.truth_label not in labels:
            labels.append(obj.truth_label)

    return ExecProjection(
        admission_state=decision.state,
        lease_state=lease_state,
        job_state=job.lifecycle_state if job is not None else None,
        attempt_guard_state=attempt_guard_state,
        truth_labels=tuple(labels),
        unavailable_reasons=decision.unavailable_reasons,
    )


@dataclass(frozen=True)
class NoRuntimeSubmitProof(_ExecCanonicalMixin):
    """Evidence that runtime.submit stays unavailable, unwired, and uncalled."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_RUNTIME_SUBMIT_PROOF_VERSION
    runtime_submit_available: bool = False
    runtime_submit_called: bool = False
    runtime_submit_wired: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "runtime_submit_available",
            "runtime_submit_called",
            "runtime_submit_wired",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class NoRawExecutionProof(_ExecCanonicalMixin):
    """Evidence that no raw execution of any kind happened in this pack."""

    reason: str
    contract_version: str = NO_RAW_EXECUTION_PROOF_VERSION
    execution_performed: bool = False
    tool_dispatched: bool = False
    model_invoked: bool = False
    verifier_executed: bool = False
    sandbox_executed: bool = False
    environment_executed: bool = False
    subprocess_called: bool = False
    network_called: bool = False
    filesystem_mutated: bool = False
    memory_written: bool = False
    identity_mutated: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "execution_performed",
            "tool_dispatched",
            "model_invoked",
            "verifier_executed",
            "sandbox_executed",
            "environment_executed",
            "subprocess_called",
            "network_called",
            "filesystem_mutated",
            "memory_written",
            "identity_mutated",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class NoTraceVerifiedProof(_ExecCanonicalMixin):
    """Evidence that nothing is trace-verified and no Trace/Ledger is written."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_TRACE_VERIFIED_PROOF_VERSION
    trace_verified: bool = False
    trace_written: bool = False
    ledger_written: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "trace_verified", "trace_written", "ledger_written")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class NoCustosEnforcementProof(_ExecCanonicalMixin):
    """Evidence that no Custos/policy enforcement happened; shadow-only."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_CUSTOS_ENFORCEMENT_PROOF_VERSION
    custos_enforced: bool = False
    policy_enforced: bool = False
    policy_shadow_only: bool = True

    def __post_init__(self) -> None:
        forbid_true(self, "custos_enforced", "policy_enforced")
        forbid_false(self, "policy_shadow_only")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_runtime_submit_proof() -> NoRuntimeSubmitProof:
    return NoRuntimeSubmitProof(
        reason=RUNTIME_SUBMIT_UNAVAILABLE_REASON,
        future_pack_owner="P4-EXEC-B",
    )


def build_no_raw_execution_proof() -> NoRawExecutionProof:
    return NoRawExecutionProof(reason=RAW_EXECUTION_UNAVAILABLE_REASON)


def build_no_trace_verified_proof() -> NoTraceVerifiedProof:
    return NoTraceVerifiedProof(
        reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
        future_pack_owner="P5 AurelTrace",
    )


def build_no_custos_enforcement_proof() -> NoCustosEnforcementProof:
    return NoCustosEnforcementProof(
        reason=CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
        future_pack_owner="P9 Custos",
    )


@dataclass(frozen=True)
class RuntimeSubmitUnavailableReason(_ExecCanonicalMixin):
    """Why runtime.submit is unavailable here and who owns it later."""

    reason: str = RUNTIME_SUBMIT_UNAVAILABLE_REASON
    future_pack_owner: str = "P4-EXEC-B"
    future_p4_exec_b_required: bool = True

    def __post_init__(self) -> None:
        forbid_false(self, "future_p4_exec_b_required")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class FutureRuntimeBridgeRequirement(_ExecCanonicalMixin):
    """One thing P4-EXEC-B (or P5/P9) must build. Naming is not building."""

    requirement: str
    future_owner: str
    is_implemented: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "is_implemented")
        require_nonempty(self, "requirement", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_owner", code=AurelExecErrorCode.EMPTY_FIELD)


STANDARD_BRIDGE_REQUIREMENTS: tuple[FutureRuntimeBridgeRequirement, ...] = (
    FutureRuntimeBridgeRequirement(
        requirement="governed runtime.submit bridge consuming lease scope",
        future_owner="P4-EXEC-B",
    ),
    FutureRuntimeBridgeRequirement(
        requirement="ExecJob lifecycle / managed execution sessions",
        future_owner="P4-EXEC-B+",
    ),
    FutureRuntimeBridgeRequirement(
        requirement="trace binding and trace verification of execution evidence",
        future_owner="P5 AurelTrace",
    ),
    FutureRuntimeBridgeRequirement(
        requirement="execution authorization and policy enforcement",
        future_owner="P9 Custos",
    ),
    FutureRuntimeBridgeRequirement(
        requirement="operator-facing execution state projection",
        future_owner="P2 AurelShell",
    ),
)


@dataclass(frozen=True)
class P4ExecAHandoffFrame(_ExecCanonicalMixin):
    """What P4-EXEC-B may consume later. A handoff frame is not a bridge:
    it wires nothing, submits nothing, and executes nothing."""

    admission_decision_id: str
    execution_lease_id: str | None
    exec_job_id: str | None
    attempt_id: str | None
    allowed_execution_mode: str | None
    allowed_tool_name: str | None
    allowed_args_hash: str | None
    sandbox_profile: str | None
    budget_scope_ref: str | None
    authority_scope_ref: str | None
    runtime_submit_unavailable: RuntimeSubmitUnavailableReason
    bridge_requirements: tuple[FutureRuntimeBridgeRequirement, ...]
    unavailable_reasons: tuple[ExecUnavailableReason, ...]
    contract_version: str = P4_EXEC_A_HANDOFF_FRAME_VERSION
    future_bridge_steps: tuple[str, ...] = FUTURE_RUNTIME_BRIDGE_STEPS
    is_p4_exec_b: bool = False
    runtime_submit_wired: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "is_p4_exec_b", "runtime_submit_wired", "execution_performed")
        require_nonempty(
            self, "admission_decision_id", code=AurelExecErrorCode.EMPTY_DECISION_ID
        )
        if self.future_bridge_steps != FUTURE_RUNTIME_BRIDGE_STEPS:
            raise AurelExecValidationError(
                "future_bridge_steps must name the full minimal bridge chain",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="future_bridge_steps",
            )


def build_p4_exec_a_handoff_frame(
    decision: ExecAdmissionDecision,
    *,
    lease: ExecutionLease | None = None,
    job: ExecJob | None = None,
    attempt: ExecutionAttempt | None = None,
) -> P4ExecAHandoffFrame:
    """Build the P4-EXEC-B handoff frame from real pack objects."""
    scope = lease.scope if lease is not None else None
    return P4ExecAHandoffFrame(
        admission_decision_id=decision.decision_id,
        execution_lease_id=lease.lease_id if lease is not None else None,
        exec_job_id=job.exec_job_id if job is not None else None,
        attempt_id=attempt.attempt_id if attempt is not None else None,
        allowed_execution_mode=(
            scope.allowed_execution_mode.value if scope is not None else None
        ),
        allowed_tool_name=scope.allowed_tool_name if scope is not None else None,
        allowed_args_hash=scope.allowed_args_hash if scope is not None else None,
        sandbox_profile=scope.sandbox_profile if scope is not None else None,
        budget_scope_ref=scope.budget_scope_ref if scope is not None else None,
        authority_scope_ref=scope.authority_scope_ref if scope is not None else None,
        runtime_submit_unavailable=RuntimeSubmitUnavailableReason(),
        bridge_requirements=STANDARD_BRIDGE_REQUIREMENTS,
        unavailable_reasons=STANDARD_UNAVAILABLE_REASONS,
    )
