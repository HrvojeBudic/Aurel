"""P4-EXEC-B ExecRuntimeBridge — the first governed runtime submit bridge.

This is the single place where AurelExec crosses from execution eligibility
into actual governed execution, and it crosses only through the existing
``AgenticRuntime.submit()`` kernel (the execution syscall for this pack).
The bridge validates job + lease + session + attempt coherence, builds a
repo-standard ``CommandEnvelope``, calls ``submit()`` exactly once, and
normalizes the captured result. It is a supervisor of the existing kernel,
never a second executor: no direct tool dispatch, no subprocess, no network,
no raw filesystem access, no sandbox/model/verifier invocation, no manual
trace/ledger write, and no manual policy/Custos enforcement exist here.

Supported first path: ``ExecutionMode.TOOL`` with the ``read_file`` tool —
the least dangerous read-only execution. Every other mode/tool is
structurally refused and reported UNAVAILABLE with a future owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from ..core_types import CommandEnvelope, RiskLevel
from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_job import ExecJob, ExecutionAttempt, transition_exec_job, transition_execution_attempt
from .exec_lease import ExecutionLease, validate_execution_lease
from .exec_outcome import ExecutionOutcome, normalize_runtime_result
from .exec_session import (
    ACTIVE_SESSION_STATUSES,
    ExecutionSession,
    ExecutionSessionStatus,
    mark_session_running,
)
from .exec_trace_binding import ExecTraceBinding, build_exec_trace_binding
from .exec_types import (
    ExecLifecycleState,
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

if TYPE_CHECKING:  # inspection-only import; the kernel is injected at runtime
    from ..core_types import AgentCard
    from ..runtime import AgenticRuntime

RUNTIME_BRIDGE_SUBMIT_REQUEST_VERSION = "runtime_bridge_submit_request.v1"
RUNTIME_BRIDGE_SUBMIT_RESULT_VERSION = "runtime_bridge_submit_result.v1"
RUNTIME_SUBMIT_PROOF_VERSION = "runtime_submit_proof.v1"
NO_DIRECT_DISPATCH_PROOF_VERSION = "no_direct_dispatch_proof.v1"
UNSUPPORTED_EXECUTION_MODE_PROOF_VERSION = "unsupported_execution_mode_proof.v1"

SUPPORTED_BRIDGE_EXECUTION_MODES: tuple[ExecutionMode, ...] = (ExecutionMode.TOOL,)
SUPPORTED_BRIDGE_TOOLS: tuple[str, ...] = ("read_file",)

DIRECT_DISPATCH_FORBIDDEN_REASON = (
    "AurelExec supervises the existing AgenticRuntime.submit() kernel and "
    "never dispatches tools, subprocesses, network, filesystem, sandbox, "
    "models, or verifiers directly — a second executor is forbidden"
)

UNSUPPORTED_MODE_FUTURE_OWNERS: dict[ExecutionMode, str] = {
    ExecutionMode.MODEL: "P4-EXEC-D execution mode profiles",
    ExecutionMode.TERMINAL: "P4-EXEC-D execution mode profiles",
    ExecutionMode.CODE: "P4-EXEC-D execution mode profiles",
    ExecutionMode.CONVERSATION: "P4-EXEC-D execution mode profiles",
    ExecutionMode.COMPOSITE: "P4-EXEC-D execution mode profiles",
    ExecutionMode.UNAVAILABLE: "no owner; UNAVAILABLE is never executable",
    ExecutionMode.ERROR: "no owner; ERROR is never executable",
}


class RuntimeSubmitStatus(str, Enum):
    """Closed-world bridge submit status. There is no VERIFIED member."""

    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class RuntimeBridgeUnavailableReason(_ExecCanonicalMixin):
    """Why a mode/tool cannot go through the bridge, and who owns it later."""

    requested_execution_mode: ExecutionMode
    requested_tool_name: str | None
    reason: str
    future_pack_owner: str

    def __post_init__(self) -> None:
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class RuntimeBridgeSubmitRequest(_ExecCanonicalMixin):
    """A lease/session/job-bound request to submit once. Not execution."""

    bridge_request_id: str
    exec_job_id: str
    session_id: str
    attempt_id: str
    lease_id: str
    issuer_card_id: str
    requested_tool_name: str
    requested_execution_mode: ExecutionMode
    command_args: tuple[tuple[str, Any], ...]
    contract_version: str = RUNTIME_BRIDGE_SUBMIT_REQUEST_VERSION
    rationale: str = "AurelExec P4-EXEC-B governed read-only submit"
    expected_effect: str = "read-only inspection through the governed runtime; no state change"
    truth_label: ExecTruthLabel = ExecTruthLabel.DEV_FIXTURE

    def __post_init__(self) -> None:
        require_nonempty(self, "bridge_request_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "exec_job_id", code=AurelExecErrorCode.EMPTY_JOB_ID)
        require_nonempty(self, "session_id", code=AurelExecErrorCode.EMPTY_SESSION_ID)
        require_nonempty(self, "attempt_id", code=AurelExecErrorCode.EMPTY_ATTEMPT_ID)
        require_nonempty(self, "lease_id", code=AurelExecErrorCode.EMPTY_LEASE_ID)
        require_nonempty(self, "issuer_card_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "requested_tool_name", code=AurelExecErrorCode.EMPTY_FIELD)
        require_allowed_truth_label(self)

    @property
    def request_hash(self) -> str:
        return stable_hash(self)

    def args_dict(self) -> dict[str, Any]:
        return dict(self.command_args)


@dataclass(frozen=True)
class RuntimeBridgeSubmitResult(_ExecCanonicalMixin):
    """What the bridge actually did. Reflects the real kernel call only."""

    bridge_result_id: str
    bridge_request_id: str
    runtime_submit_called: bool
    submit_status: RuntimeSubmitStatus
    success: bool
    raw_result_summary: str
    truth_label: ExecTruthLabel
    contract_version: str = RUNTIME_BRIDGE_SUBMIT_RESULT_VERSION
    runtime_submit_ref: str | None = None
    command_id: str | None = None
    error_message: str | None = None
    outcome_id: str | None = None
    trace_binding_id: str | None = None
    direct_tool_dispatch_called: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "bridge_result_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "bridge_request_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "raw_result_summary", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "direct_tool_dispatch_called", "trace_verified")
        if self.success and not self.runtime_submit_called:
            raise AurelExecValidationError(
                "a bridge result cannot claim success without a runtime submit",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="success",
            )
        if self.runtime_submit_called != (
            self.submit_status is RuntimeSubmitStatus.SUBMITTED
        ):
            raise AurelExecValidationError(
                "runtime_submit_called and submit_status must agree",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="submit_status",
            )


@dataclass(frozen=True)
class RuntimeBridgeExecution(_ExecCanonicalMixin):
    """One completed bridge pass: result + outcome + updated state objects."""

    request: RuntimeBridgeSubmitRequest
    result: RuntimeBridgeSubmitResult
    outcome: ExecutionOutcome
    trace_binding: ExecTraceBinding
    job: ExecJob
    session: ExecutionSession
    attempt: ExecutionAttempt


class ExecRuntimeBridge:
    """Supervisor of the existing runtime kernel. Never a second executor.

    The injected kernel must expose the repo-standard
    ``submit(cmd: CommandEnvelope, card: AgentCard) -> CommandResult``
    surface; the bridge uses that method and nothing else on the kernel.
    """

    def __init__(self, runtime: "AgenticRuntime") -> None:
        submit = getattr(runtime, "submit", None)
        if not callable(submit):
            raise AurelExecValidationError(
                "runtime kernel must expose a callable submit(cmd, card)",
                code=AurelExecErrorCode.RUNTIME_KERNEL_INVALID,
                field="runtime",
            )
        self._runtime = runtime

    def _validate_support(self, request: RuntimeBridgeSubmitRequest) -> None:
        mode = request.requested_execution_mode
        if mode not in SUPPORTED_BRIDGE_EXECUTION_MODES:
            reason = describe_unavailable_mode(mode, request.requested_tool_name)
            raise AurelExecValidationError(
                f"unsupported execution mode {mode.value}: {reason.reason}",
                code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
                field="requested_execution_mode",
            )
        if request.requested_tool_name not in SUPPORTED_BRIDGE_TOOLS:
            raise AurelExecValidationError(
                f"unsupported tool {request.requested_tool_name!r}: only the "
                f"safe read-only tools {SUPPORTED_BRIDGE_TOOLS} may cross the "
                "bridge in P4-EXEC-B",
                code=AurelExecErrorCode.UNSUPPORTED_TOOL,
                field="requested_tool_name",
            )

    def _validate_coherence(
        self,
        request: RuntimeBridgeSubmitRequest,
        *,
        job: ExecJob,
        lease: ExecutionLease,
        session: ExecutionSession,
        attempt: ExecutionAttempt,
        card: "AgentCard",
    ) -> None:
        bindings = (
            ("exec_job_id", request.exec_job_id, job.exec_job_id),
            ("exec_job_id", request.exec_job_id, lease.exec_job_id),
            ("exec_job_id", request.exec_job_id, session.exec_job_id),
            ("exec_job_id", request.exec_job_id, attempt.exec_job_id),
            ("session_id", request.session_id, session.session_id),
            ("attempt_id", request.attempt_id, attempt.attempt_id),
            ("lease_id", request.lease_id, lease.lease_id),
            ("lease_id", request.lease_id, attempt.lease_id),
            ("issuer_card_id", request.issuer_card_id, card.id),
        )
        for field_name, expected, actual in bindings:
            if expected != actual:
                raise AurelExecValidationError(
                    f"bridge request {field_name} does not match the bound objects",
                    code=AurelExecErrorCode.BRIDGE_REQUEST_MISMATCH,
                    field=field_name,
                )

    def _validate_lease_scope(
        self,
        request: RuntimeBridgeSubmitRequest,
        lease: ExecutionLease,
        *,
        current_tick: int,
    ) -> None:
        validation = validate_execution_lease(lease, current_tick=current_tick)
        if not validation.valid:
            code = AurelExecErrorCode.LEASE_INVALID
            if validation.revoked:
                code = AurelExecErrorCode.LEASE_REVOKED
            elif validation.expired:
                code = AurelExecErrorCode.LEASE_EXPIRED
            raise AurelExecValidationError(
                f"submit blocked: {validation.reason}", code=code, field="lease_id"
            )
        scope = lease.scope
        if scope.allowed_execution_mode is not request.requested_execution_mode:
            raise AurelExecValidationError(
                "submit blocked: lease scope binds mode "
                f"{scope.allowed_execution_mode.value}, request asks "
                f"{request.requested_execution_mode.value}",
                code=AurelExecErrorCode.LEASE_SCOPE_MISMATCH,
                field="requested_execution_mode",
            )
        if scope.allowed_tool_name is not None and (
            scope.allowed_tool_name != request.requested_tool_name
        ):
            raise AurelExecValidationError(
                "submit blocked: lease scope binds tool "
                f"{scope.allowed_tool_name!r}, request asks "
                f"{request.requested_tool_name!r}",
                code=AurelExecErrorCode.LEASE_SCOPE_MISMATCH,
                field="requested_tool_name",
            )
        if scope.allowed_args_hash is not None:
            args_hash = stable_hash(request.args_dict())
            if args_hash != scope.allowed_args_hash:
                raise AurelExecValidationError(
                    "submit blocked: command args do not match the lease's "
                    "bound args hash",
                    code=AurelExecErrorCode.LEASE_SCOPE_MISMATCH,
                    field="command_args",
                )

    def _validate_states(
        self,
        *,
        job: ExecJob,
        session: ExecutionSession,
        attempt: ExecutionAttempt,
    ) -> None:
        if session.status not in ACTIVE_SESSION_STATUSES:
            raise AurelExecValidationError(
                f"submit blocked: session is {session.status.value}, not active",
                code=AurelExecErrorCode.SESSION_INVALID,
                field="status",
            )
        if not attempt.session_id:
            raise AurelExecValidationError(
                "submit blocked: attempt has no bound session — a valid "
                "session is required for runtime submit",
                code=AurelExecErrorCode.SESSION_REQUIRED,
                field="session_id",
            )
        if attempt.session_id != session.session_id:
            raise AurelExecValidationError(
                "submit blocked: attempt is bound to a different session",
                code=AurelExecErrorCode.SESSION_JOB_MISMATCH,
                field="session_id",
            )
        if job.lifecycle_state not in (
            ExecLifecycleState.SESSION_BOUND,
            ExecLifecycleState.ATTEMPT_PENDING,
        ):
            raise AurelExecValidationError(
                f"submit blocked: job is {job.lifecycle_state.value}; it must "
                "be SESSION_BOUND or ATTEMPT_PENDING",
                code=AurelExecErrorCode.SUBMIT_STATE_INVALID,
                field="lifecycle_state",
            )
        if attempt.lifecycle_state not in (
            ExecLifecycleState.ATTEMPT_PENDING,
            ExecLifecycleState.READY_TO_SUBMIT,
        ):
            raise AurelExecValidationError(
                f"submit blocked: attempt is {attempt.lifecycle_state.value}",
                code=AurelExecErrorCode.SUBMIT_STATE_INVALID,
                field="lifecycle_state",
            )
        if attempt.runtime_submit_called:
            raise AurelExecValidationError(
                "submit blocked: this attempt already submitted — no retry in "
                "P4-EXEC-B; bounded recovery belongs to a later pack",
                code=AurelExecErrorCode.SUBMIT_STATE_INVALID,
                field="runtime_submit_called",
            )

    def submit_once(
        self,
        request: RuntimeBridgeSubmitRequest,
        *,
        job: ExecJob,
        lease: ExecutionLease,
        session: ExecutionSession,
        attempt: ExecutionAttempt,
        card: "AgentCard",
        current_tick: int,
    ) -> RuntimeBridgeExecution:
        """Validate everything, then call ``AgenticRuntime.submit()`` once.

        All validation failures raise before any kernel call — a blocked
        submit performs nothing. On the supported path this method performs
        exactly one governed submit and never retries.
        """
        self._validate_support(request)
        self._validate_coherence(
            request, job=job, lease=lease, session=session, attempt=attempt, card=card
        )
        self._validate_lease_scope(request, lease, current_tick=current_tick)
        self._validate_states(job=job, session=session, attempt=attempt)

        # deterministic pre-submit transitions (state arithmetic, no side effects)
        attempt = transition_execution_attempt(
            attempt, ExecLifecycleState.READY_TO_SUBMIT
        )
        attempt = transition_execution_attempt(attempt, ExecLifecycleState.RUNNING)
        if job.lifecycle_state is ExecLifecycleState.SESSION_BOUND:
            job = transition_exec_job(job, ExecLifecycleState.ATTEMPT_PENDING)
        job = transition_exec_job(
            job, ExecLifecycleState.RUNNING, updated_at_tick=current_tick
        )
        if session.status is ExecutionSessionStatus.OPEN:
            session = mark_session_running(session)

        envelope = CommandEnvelope.make(
            issuer_card_id=card.id,
            tool=request.requested_tool_name,
            args=request.args_dict(),
            rationale=request.rationale,
            declared_risk=RiskLevel.LOW,
            expected_effect=request.expected_effect,
        )

        # ---- the one governed execution syscall of this pack ---- #
        runtime_result = self._runtime.submit(envelope, card)

        trace_binding = build_exec_trace_binding(
            attempt_id=attempt.attempt_id,
            transition=runtime_result.transition,
        )
        outcome = normalize_runtime_result(
            runtime_result,
            attempt_id=attempt.attempt_id,
            exec_job_id=job.exec_job_id,
            session_id=session.session_id,
            tool_name=request.requested_tool_name,
            command_id=envelope.id,
        )

        final_attempt_state = (
            ExecLifecycleState.SUCCEEDED if outcome.success else ExecLifecycleState.FAILED
        )
        attempt = transition_execution_attempt(
            attempt,
            ExecLifecycleState.SUBMITTED,
            runtime_submit_called=True,
            runtime_submit_ref=outcome.trace_ref,
            command_id=envelope.id,
            command_envelope_hash=envelope.command_hash(),
            outcome_id=outcome.outcome_id,
            trace_binding_id=trace_binding.trace_binding_id,
            error_message=outcome.error_message,
            ended_at_tick=current_tick,
        )
        attempt = transition_execution_attempt(attempt, final_attempt_state)
        job = transition_exec_job(
            job,
            (
                ExecLifecycleState.SUCCEEDED
                if outcome.success
                else ExecLifecycleState.FAILED
            ),
            updated_at_tick=current_tick,
        )

        result = RuntimeBridgeSubmitResult(
            bridge_result_id="exec-bridge-result-"
            + stable_hash((request.bridge_request_id, envelope.id))[:16],
            bridge_request_id=request.bridge_request_id,
            runtime_submit_called=True,
            submit_status=RuntimeSubmitStatus.SUBMITTED,
            success=outcome.success,
            raw_result_summary=outcome.result_summary,
            truth_label=ExecTruthLabel.LIVE,
            runtime_submit_ref=outcome.trace_ref,
            command_id=envelope.id,
            error_message=outcome.error_message,
            outcome_id=outcome.outcome_id,
            trace_binding_id=trace_binding.trace_binding_id,
        )
        return RuntimeBridgeExecution(
            request=request,
            result=result,
            outcome=outcome,
            trace_binding=trace_binding,
            job=job,
            session=session,
            attempt=attempt,
        )


def build_runtime_bridge_submit_request(
    *,
    job: ExecJob,
    lease: ExecutionLease,
    session: ExecutionSession,
    attempt: ExecutionAttempt,
    issuer_card_id: str,
    requested_tool_name: str,
    requested_execution_mode: ExecutionMode,
    command_args: tuple[tuple[str, Any], ...],
    truth_label: ExecTruthLabel = ExecTruthLabel.DEV_FIXTURE,
) -> RuntimeBridgeSubmitRequest:
    """Build a coherent bridge request from the bound objects."""
    bridge_request_id = "exec-bridge-req-" + stable_hash(
        (attempt.attempt_id, requested_tool_name, command_args)
    )[:16]
    return RuntimeBridgeSubmitRequest(
        bridge_request_id=bridge_request_id,
        exec_job_id=job.exec_job_id,
        session_id=session.session_id,
        attempt_id=attempt.attempt_id,
        lease_id=lease.lease_id,
        issuer_card_id=issuer_card_id,
        requested_tool_name=requested_tool_name,
        requested_execution_mode=requested_execution_mode,
        command_args=command_args,
        truth_label=truth_label,
    )


def describe_unavailable_mode(
    mode: ExecutionMode, requested_tool_name: str | None = None
) -> RuntimeBridgeUnavailableReason:
    """Honest UNAVAILABLE reason for a mode the bridge refuses."""
    if mode in SUPPORTED_BRIDGE_EXECUTION_MODES:
        raise AurelExecValidationError(
            f"mode {mode.value} is supported; it has no unavailable reason",
            code=AurelExecErrorCode.ERROR,
            field="requested_execution_mode",
        )
    return RuntimeBridgeUnavailableReason(
        requested_execution_mode=mode,
        requested_tool_name=requested_tool_name,
        reason=(
            f"execution mode {mode.value} is UNAVAILABLE in P4-EXEC-B; only "
            "the safe read-only TOOL path crosses the bridge"
        ),
        future_pack_owner=UNSUPPORTED_MODE_FUTURE_OWNERS[mode],
    )


@dataclass(frozen=True)
class RuntimeSubmitProof(_ExecCanonicalMixin):
    """Evidence that AgenticRuntime.submit() was actually called once."""

    agentic_runtime_submit_called: bool
    submitted_tool: str
    command_id: str
    reason: str
    contract_version: str = RUNTIME_SUBMIT_PROOF_VERSION
    runtime_submit_ref: str | None = None
    direct_tool_dispatch_called: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        forbid_false(self, "agentic_runtime_submit_called")
        forbid_true(self, "direct_tool_dispatch_called", "trace_verified")
        require_nonempty(self, "submitted_tool", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "command_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_runtime_submit_proof(
    result: RuntimeBridgeSubmitResult, request: RuntimeBridgeSubmitRequest
) -> RuntimeSubmitProof:
    """Build submit proof from a real bridge result only. Never fakes."""
    if not result.runtime_submit_called or not result.command_id:
        raise AurelExecValidationError(
            "submit proof requires a bridge result whose submit actually happened",
            code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
            field="runtime_submit_called",
        )
    return RuntimeSubmitProof(
        agentic_runtime_submit_called=True,
        submitted_tool=request.requested_tool_name,
        command_id=result.command_id,
        reason=(
            "the bridge built a repo-standard CommandEnvelope and called the "
            "existing AgenticRuntime.submit() kernel exactly once"
        ),
        runtime_submit_ref=result.runtime_submit_ref,
    )


@dataclass(frozen=True)
class NoDirectDispatchProof(_ExecCanonicalMixin):
    """Evidence that AurelExec bypassed nothing: kernel submit only."""

    reason: str
    contract_version: str = NO_DIRECT_DISPATCH_PROOF_VERSION
    direct_tool_runtime_dispatch_called: bool = False
    direct_subprocess_called: bool = False
    direct_network_called: bool = False
    direct_raw_filesystem_execution_called: bool = False
    direct_sandbox_execution_called: bool = False
    direct_model_invoked: bool = False
    direct_verifier_executed: bool = False
    manual_trace_write: bool = False
    manual_ledger_write: bool = False
    manual_policy_enforced: bool = False
    manual_custos_enforced: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "direct_tool_runtime_dispatch_called",
            "direct_subprocess_called",
            "direct_network_called",
            "direct_raw_filesystem_execution_called",
            "direct_sandbox_execution_called",
            "direct_model_invoked",
            "direct_verifier_executed",
            "manual_trace_write",
            "manual_ledger_write",
            "manual_policy_enforced",
            "manual_custos_enforced",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_direct_dispatch_proof() -> NoDirectDispatchProof:
    return NoDirectDispatchProof(reason=DIRECT_DISPATCH_FORBIDDEN_REASON)


@dataclass(frozen=True)
class UnsupportedExecutionModeProof(_ExecCanonicalMixin):
    """Evidence that a non-TOOL mode remains structurally unavailable."""

    mode: ExecutionMode
    reason: str
    future_pack_owner: str
    contract_version: str = UNSUPPORTED_EXECUTION_MODE_PROOF_VERSION
    unavailable: bool = True

    def __post_init__(self) -> None:
        forbid_false(self, "unavailable")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)
        if self.mode in SUPPORTED_BRIDGE_EXECUTION_MODES:
            raise AurelExecValidationError(
                "a supported mode cannot carry an unsupported-mode proof",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="mode",
            )


def build_unsupported_execution_mode_proofs() -> tuple[UnsupportedExecutionModeProof, ...]:
    """One honest proof per unsupported execution mode."""
    proofs = []
    for mode in ExecutionMode:
        if mode in SUPPORTED_BRIDGE_EXECUTION_MODES:
            continue
        reason = describe_unavailable_mode(mode)
        proofs.append(
            UnsupportedExecutionModeProof(
                mode=mode,
                reason=reason.reason,
                future_pack_owner=reason.future_pack_owner,
            )
        )
    return tuple(proofs)
