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
from .exec_checkpoint import ExecutionCheckpointRef, ExecutionRollbackRef
from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_job import ExecJob, ExecutionAttempt
from .exec_lease import ExecutionLease, LeaseValidationResult
from .exec_messages import (
    TRANSPORT_BUS_UNAVAILABLE_REASON,
    ExecutionMessage,
    LocalExecutionMessageLog,
)
from .exec_outcome import ExecutionOutcome, ExecutionOutcomeStatus
from .exec_queue import ExecQueueEntry, ExecQueueState
from .exec_runtime_bridge import build_unsupported_execution_mode_proofs
from .exec_session import ExecutionSession, ExecutionSessionStatus
from .exec_trace_binding import ExecTraceBinding
from .exec_types import (
    CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
    RAW_EXECUTION_UNAVAILABLE_REASON,
    RUNTIME_SUBMIT_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    ExecAdmissionState,
    ExecCustosStatus,
    ExecLifecycleState,
    ExecTruthLabel,
    ExecutionMode,
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
    """Read-only admission/lease/session/job/attempt/outcome view.

    P4-EXEC-B expansion: ``runtime_submit_available=True`` is constructible
    only with ``runtime_submit_called=True`` — availability may only be
    claimed on actual submit evidence, never declared. Worker/queue/bus/
    checkpoint/recovery availability is structurally False.
    """

    admission_state: ExecAdmissionState
    lease_state: ExecLeaseProjectionState
    job_state: ExecLifecycleState | None
    attempt_guard_state: ExecAttemptGuardState
    truth_labels: tuple[ExecTruthLabel, ...]
    unavailable_reasons: tuple[ExecUnavailableReason, ...]
    contract_version: str = EXEC_PROJECTION_VERSION
    session_state: ExecutionSessionStatus | None = None
    attempt_state: ExecLifecycleState | None = None
    runtime_submit_available: bool = False
    runtime_submit_called: bool = False
    runtime_submit_ref: str | None = None
    outcome_status: ExecutionOutcomeStatus | None = None
    outcome_summary: str | None = None
    trace_bound: bool = False
    policy_p9_status: ExecCustosStatus = ExecCustosStatus.ENFORCEMENT_UNAVAILABLE
    unsupported_modes_unavailable: tuple[str, ...] = ()
    runtime_submit_unavailable_reason: str = RUNTIME_SUBMIT_UNAVAILABLE_REASON
    trace_verified_available: bool = False
    trace_verified_unavailable_reason: str = TRACE_VERIFICATION_UNAVAILABLE_REASON
    policy_enforcement_available: bool = False
    policy_enforcement_unavailable_reason: str = CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON
    worker_queue_available: bool = False
    execution_bus_available: bool = False
    checkpoint_available: bool = False
    recovery_available: bool = False
    read_only: bool = True

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "trace_verified_available",
            "policy_enforcement_available",
            "worker_queue_available",
            "execution_bus_available",
            "checkpoint_available",
            "recovery_available",
        )
        forbid_false(self, "read_only")
        if self.runtime_submit_available and not self.runtime_submit_called:
            raise AurelExecValidationError(
                "runtime_submit_available may only be claimed with actual "
                "submit evidence (runtime_submit_called=True)",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_submit_available",
            )
        if self.trace_bound and not self.runtime_submit_called:
            raise AurelExecValidationError(
                "trace_bound requires an actual runtime submit",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="trace_bound",
            )
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
    session: ExecutionSession | None = None,
    outcome: ExecutionOutcome | None = None,
    trace_binding: ExecTraceBinding | None = None,
) -> ExecProjection:
    """Project admission/lease/session/job/attempt/outcome state read-only.
    Mutates nothing and executes nothing."""
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
    for obj in (lease, job, attempt, session, outcome, trace_binding):
        if obj is not None and obj.truth_label not in labels:
            labels.append(obj.truth_label)

    runtime_submit_called = bool(attempt is not None and attempt.runtime_submit_called)
    unsupported_modes = tuple(
        proof.mode.value for proof in build_unsupported_execution_mode_proofs()
    )
    return ExecProjection(
        admission_state=decision.state,
        lease_state=lease_state,
        job_state=job.lifecycle_state if job is not None else None,
        attempt_guard_state=attempt_guard_state,
        truth_labels=tuple(labels),
        unavailable_reasons=decision.unavailable_reasons,
        session_state=session.status if session is not None else None,
        attempt_state=attempt.lifecycle_state if attempt is not None else None,
        runtime_submit_available=runtime_submit_called,
        runtime_submit_called=runtime_submit_called,
        runtime_submit_ref=(
            attempt.runtime_submit_ref if attempt is not None else None
        ),
        outcome_status=outcome.runtime_status if outcome is not None else None,
        outcome_summary=outcome.result_summary if outcome is not None else None,
        trace_bound=bool(trace_binding is not None and trace_binding.trace_bound),
        policy_p9_status=decision.custos_status,
        unsupported_modes_unavailable=unsupported_modes,
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


MANAGED_RUNTIME_PROJECTION_VERSION = "managed_runtime_projection.v1"


@dataclass(frozen=True)
class ManagedRuntimeProjection(_ExecCanonicalMixin):
    """Read-only P4-EXEC-C managed runtime shape view.

    The local queue and the single in-process worker slot are real
    (``local_queue_available``/``local_worker_slot_available`` may be True);
    everything platform-shaped stays structurally False: worker pool,
    remote/distributed workers, transport bus, checkpoint persistence
    engine, rollback execution, recovery engine. A projection is not
    runtime control.
    """

    queue_state: ExecQueueState | None
    queue_entry_id: str | None
    worker_slot_state: str | None
    worker_slot_id: str | None
    claim_state: str | None
    claim_id: str | None
    local_execution_messages: tuple[ExecutionMessage, ...]
    checkpoint_refs: tuple[ExecutionCheckpointRef, ...]
    rollback_refs: tuple[ExecutionRollbackRef, ...]
    truth_labels: tuple[ExecTruthLabel, ...]
    unavailable_reasons: tuple[ExecUnavailableReason, ...]
    contract_version: str = MANAGED_RUNTIME_PROJECTION_VERSION
    local_queue_available: bool = True
    local_worker_slot_available: bool = True
    single_local_worker_slot_only: bool = True
    queue_is_scheduler: bool = False
    worker_pool_available: bool = False
    remote_worker_available: bool = False
    distributed_worker_available: bool = False
    transport_bus_available: bool = False
    network_publish_available: bool = False
    pubsub_available: bool = False
    checkpoint_ref_available: bool = False
    checkpoint_persistence_engine_available: bool = False
    rollback_available: bool = False
    rollback_executed: bool = False
    recovery_engine_available: bool = False
    retry_engine_available: bool = False
    concurrency_engine_available: bool = False
    p5_trace_verification_available: bool = False
    p9_full_enforcement_available: bool = False
    shell_ui_available: bool = False
    react_frontend_available: bool = False
    api_server_available: bool = False
    transport_bus_unavailable_reason: str = TRANSPORT_BUS_UNAVAILABLE_REASON
    read_only: bool = True

    def __post_init__(self) -> None:
        forbid_true(
            self,
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
        )
        forbid_false(self, "single_local_worker_slot_only", "read_only")
        if self.checkpoint_ref_available and not self.checkpoint_refs:
            raise AurelExecValidationError(
                "checkpoint_ref_available requires actual checkpoint refs",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="checkpoint_ref_available",
            )


def build_managed_runtime_projection(
    *,
    queue_entry: ExecQueueEntry | None = None,
    worker_slot: object | None = None,
    claim: object | None = None,
    log: LocalExecutionMessageLog | None = None,
    checkpoint_refs: tuple[ExecutionCheckpointRef, ...] = (),
    rollback_refs: tuple[ExecutionRollbackRef, ...] = (),
) -> ManagedRuntimeProjection:
    """Project managed runtime shape read-only. Mutates and controls nothing."""
    messages = log.messages if log is not None else ()
    labels: list[ExecTruthLabel] = []
    for obj in (queue_entry, worker_slot, claim, *checkpoint_refs, *rollback_refs):
        obj_label = getattr(obj, "truth_label", None)
        if obj_label is not None and obj_label not in labels:
            labels.append(obj_label)
    return ManagedRuntimeProjection(
        queue_state=queue_entry.queue_state if queue_entry is not None else None,
        queue_entry_id=queue_entry.queue_entry_id if queue_entry is not None else None,
        worker_slot_state=(
            getattr(worker_slot, "status").value if worker_slot is not None else None
        ),
        worker_slot_id=(
            getattr(worker_slot, "worker_slot_id") if worker_slot is not None else None
        ),
        claim_state=(
            getattr(claim, "claim_status").value if claim is not None else None
        ),
        claim_id=getattr(claim, "claim_id") if claim is not None else None,
        local_execution_messages=messages,
        checkpoint_refs=checkpoint_refs,
        rollback_refs=rollback_refs,
        truth_labels=tuple(labels),
        unavailable_reasons=STANDARD_UNAVAILABLE_REASONS,
        checkpoint_ref_available=bool(checkpoint_refs),
    )


MODE_PROJECTION_VERSION = "mode_projection.v1"


@dataclass(frozen=True)
class ModeProjection(_ExecCanonicalMixin):
    """Read-only P4-EXEC-D execution mode view.

    Shows which modes are available (only TOOL, only through the existing
    bridge), profile-only, unavailable, or blocked — with reasons. Risky
    execution claims (model call, terminal/shell, eval/script, new sandbox,
    P5/P9/Shell/API) are structurally False. A projection is not runtime
    control and a mode status is not permission.
    """

    mode_registry_id: str
    supported_modes: tuple[str, ...]
    profile_only_modes: tuple[str, ...]
    unavailable_modes: tuple[str, ...]
    blocked_modes: tuple[str, ...]
    tool_profile_status: str
    model_profile_status: str
    terminal_profile_status: str
    code_profile_status: str
    truth_labels: tuple[ExecTruthLabel, ...]
    contract_version: str = MODE_PROJECTION_VERSION
    requested_execution_mode: str | None = None
    mode_profile_id: str | None = None
    mode_available: bool = False
    mode_blocked_reason: str | None = None
    mode_missing_requirements: tuple[str, ...] = ()
    silent_fallback_allowed: bool = False
    direct_dispatch_allowed: bool = False
    model_call_allowed: bool = False
    terminal_execution_available: bool = False
    shell_allowed: bool = False
    subprocess_allowed: bool = False
    code_execution_available: bool = False
    eval_allowed: bool = False
    script_execution_allowed: bool = False
    new_sandbox_execution_available: bool = False
    network_execution_available: bool = False
    p5_trace_verification_available: bool = False
    p9_full_enforcement_available: bool = False
    shell_ui_available: bool = False
    react_frontend_available: bool = False
    api_server_available: bool = False
    read_only: bool = True

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "silent_fallback_allowed",
            "direct_dispatch_allowed",
            "model_call_allowed",
            "terminal_execution_available",
            "shell_allowed",
            "subprocess_allowed",
            "code_execution_available",
            "eval_allowed",
            "script_execution_allowed",
            "new_sandbox_execution_available",
            "network_execution_available",
            "p5_trace_verification_available",
            "p9_full_enforcement_available",
            "shell_ui_available",
            "react_frontend_available",
            "api_server_available",
        )
        forbid_false(self, "read_only")
        require_nonempty(self, "mode_registry_id", code=AurelExecErrorCode.EMPTY_FIELD)
        if self.mode_available and self.requested_execution_mode not in self.supported_modes:
            raise AurelExecValidationError(
                "mode_available requires the requested mode to be a "
                "registry-supported mode",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="mode_available",
            )
        if not self.mode_available and self.requested_execution_mode is not None:
            if not (self.mode_blocked_reason or self.mode_missing_requirements):
                raise AurelExecValidationError(
                    "a non-available requested mode must carry a blocked reason",
                    code=AurelExecErrorCode.EMPTY_FIELD,
                    field="mode_blocked_reason",
                )


def build_mode_projection(registry, *, decision=None) -> ModeProjection:
    """Project registry + optional compatibility decision read-only."""
    tool_status = registry.profile_for(ExecutionMode.TOOL).availability_status.value
    model_status = registry.profile_for(ExecutionMode.MODEL).availability_status.value
    terminal_status = registry.profile_for(ExecutionMode.TERMINAL).availability_status.value
    code_status = registry.profile_for(ExecutionMode.CODE).availability_status.value
    labels: list[ExecTruthLabel] = [registry.truth_label]
    if decision is not None and decision.truth_label not in labels:
        labels.append(decision.truth_label)
    return ModeProjection(
        mode_registry_id=registry.registry_id,
        supported_modes=registry.supported_modes,
        profile_only_modes=registry.profile_only_modes,
        unavailable_modes=registry.unavailable_modes,
        blocked_modes=registry.blocked_modes,
        tool_profile_status=tool_status,
        model_profile_status=model_status,
        terminal_profile_status=terminal_status,
        code_profile_status=code_status,
        truth_labels=tuple(labels),
        requested_execution_mode=(
            decision.requested_execution_mode if decision is not None else None
        ),
        mode_profile_id=decision.profile_id if decision is not None else None,
        mode_available=bool(decision is not None and decision.allowed),
        mode_blocked_reason=(
            decision.reason if decision is not None and decision.blocked else None
        ),
        mode_missing_requirements=(
            decision.missing_requirements if decision is not None else ()
        ),
    )
