"""P4-EXEC-A admission request / deterministic admission gate chain.

The P3 → P4 admission bridge. A P3-like candidate (ready node, scheduling
intent, dispatchability frame) can be represented as an
``ExecAdmissionRequest`` and deterministically decided by ``decide_admission``
through an NCF-style hierarchical gate chain where the first blocking gate
locks the outcome.

An admission request is not execution. An admission decision is not
authorization: ADMIT means the candidate passed structural gates only —
Custos/P9 still owns authority, P5 still owns proof, and runtime.submit
remains unavailable until P4-EXEC-B. The gate chain has no side effects:
it calls no runtime, no tool, no model, no verifier, no Custos, no Trace,
and no sandbox.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
    P3_READY_MARKER,
    POLICY_SHADOW_ONLY_REASON,
    RUNTIME_SUBMIT_UNAVAILABLE_REASON,
    SANDBOX_REQUIRED_MODES,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    VERIFIER_REQUIRED_MODES,
    ExecAdmissionGateKind,
    ExecAdmissionState,
    ExecCustosStatus,
    ExecMissingRequirementKind,
    ExecPolicyStatus,
    ExecTraceStatus,
    ExecTruthLabel,
    ExecUnavailableSystem,
    ExecutionMode,
    TraceBindingStatus,
    _ExecCanonicalMixin,
    require_allowed_truth_label,
    require_nonempty,
    stable_hash,
)

EXEC_ADMISSION_REQUEST_VERSION = "exec_admission_request.v1"
EXEC_ADMISSION_DECISION_VERSION = "exec_admission_decision.v1"
EXEC_ADMISSION_GATE_RESULT_VERSION = "exec_admission_gate_result.v1"


@dataclass(frozen=True)
class ExecMissingRequirement(_ExecCanonicalMixin):
    """One named requirement the candidate is missing. Naming it is not
    fetching, resolving, or executing it."""

    kind: ExecMissingRequirementKind
    explanation: str

    def __post_init__(self) -> None:
        require_nonempty(self, "explanation", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class ExecUnavailableReason(_ExecCanonicalMixin):
    """One honestly unavailable system with its reason and future owner."""

    system: ExecUnavailableSystem
    reason: str
    future_pack_owner: str

    def __post_init__(self) -> None:
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


STANDARD_UNAVAILABLE_REASONS: tuple[ExecUnavailableReason, ...] = (
    ExecUnavailableReason(
        system=ExecUnavailableSystem.RUNTIME_SUBMIT,
        reason=RUNTIME_SUBMIT_UNAVAILABLE_REASON,
        future_pack_owner="P4-EXEC-B",
    ),
    ExecUnavailableReason(
        system=ExecUnavailableSystem.TRACE_VERIFICATION,
        reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
        future_pack_owner="P5 AurelTrace",
    ),
    ExecUnavailableReason(
        system=ExecUnavailableSystem.CUSTOS_ENFORCEMENT,
        reason=CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
        future_pack_owner="P9 Custos",
    ),
    ExecUnavailableReason(
        system=ExecUnavailableSystem.POLICY_ENFORCEMENT,
        reason=POLICY_SHADOW_ONLY_REASON,
        future_pack_owner="P9 Custos",
    ),
)


@dataclass(frozen=True)
class ExecAdmissionRequest(_ExecCanonicalMixin):
    """A P3-like candidate represented for admission. Not execution, not
    authorization; a request with an empty source ref is constructible so
    the gate chain can reject it deterministically."""

    request_id: str
    source_p3_candidate_ref: str
    source_dispatchability_reason: str
    requested_execution_mode: ExecutionMode
    contract_version: str = EXEC_ADMISSION_REQUEST_VERSION
    source_flow_run_id: str | None = None
    source_atomic_unit_id: str | None = None
    requested_tool_name: str | None = None
    requested_args_hash: str | None = None
    requested_sandbox_profile: str | None = None
    requested_budget_ref: str | None = None
    requested_authority_ref: str | None = None
    requested_policy_context_ref: str | None = None
    requested_verifier_ref: str | None = None
    requested_trace_binding: TraceBindingStatus = TraceBindingStatus.UNAVAILABLE
    truth_label: ExecTruthLabel = ExecTruthLabel.DEV_FIXTURE
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        require_nonempty(self, "request_id", code=AurelExecErrorCode.EMPTY_REQUEST_ID)
        require_allowed_truth_label(self)

    @property
    def request_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class ExecAdmissionGateResult(_ExecCanonicalMixin):
    """One gate's deterministic verdict. A gate result executes nothing."""

    gate: ExecAdmissionGateKind
    state: ExecAdmissionState
    reason: str
    missing: tuple[ExecMissingRequirement, ...] = ()
    contract_version: str = EXEC_ADMISSION_GATE_RESULT_VERSION

    def __post_init__(self) -> None:
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


@dataclass(frozen=True)
class ExecAdmissionDecision(_ExecCanonicalMixin):
    """Deterministic, closed-world admission decision.

    ADMIT does not mean authorized by Custos and does not mean executed.
    HOLD/REJECT/REQUIRE_* always carry a reason. Trace verification and
    policy enforcement are never claimed: the status vocabularies have no
    VERIFIED/ENFORCED members.
    """

    decision_id: str
    request_id: str
    state: ExecAdmissionState
    reason: str
    gate_results: tuple[ExecAdmissionGateResult, ...]
    missing_requirements: tuple[ExecMissingRequirement, ...]
    unavailable_reasons: tuple[ExecUnavailableReason, ...]
    truth_label: ExecTruthLabel
    policy_status: ExecPolicyStatus
    custos_status: ExecCustosStatus
    trace_status: ExecTraceStatus
    contract_version: str = EXEC_ADMISSION_DECISION_VERSION
    created_at_tick: int | None = None

    def __post_init__(self) -> None:
        require_nonempty(self, "decision_id", code=AurelExecErrorCode.EMPTY_DECISION_ID)
        require_nonempty(self, "request_id", code=AurelExecErrorCode.EMPTY_REQUEST_ID)
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_allowed_truth_label(self)

    @property
    def decision_hash(self) -> str:
        return stable_hash(self)

    @property
    def admitted(self) -> bool:
        return self.state is ExecAdmissionState.ADMIT


def _gate_source_validity(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if not request.source_p3_candidate_ref.strip():
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.SOURCE_VALIDITY,
            state=ExecAdmissionState.REJECT,
            reason="candidate has no P3 source ref; an unsourced candidate is rejected",
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.SOURCE_REF,
                    explanation="source_p3_candidate_ref is empty",
                ),
            ),
        )
    if request.requested_execution_mode in (ExecutionMode.UNAVAILABLE, ExecutionMode.ERROR):
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.SOURCE_VALIDITY,
            state=ExecAdmissionState.REJECT,
            reason=(
                f"requested execution mode {request.requested_execution_mode.value} "
                "is not an admittable mode"
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.SOURCE_VALIDITY,
        state=ExecAdmissionState.ADMIT,
        reason="source ref present and requested mode is admittable",
    )


def _gate_p3_readiness_marker(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    marker = request.source_dispatchability_reason.strip()
    if not marker:
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.P3_READINESS_MARKER,
            state=ExecAdmissionState.HOLD,
            reason="candidate carries no P3 dispatchability/readiness marker",
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.SOURCE_READINESS_MARKER,
                    explanation="source_dispatchability_reason is empty",
                ),
            ),
        )
    if marker != P3_READY_MARKER:
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.P3_READINESS_MARKER,
            state=ExecAdmissionState.HOLD,
            reason=(
                f"P3 marker {marker!r} is not {P3_READY_MARKER!r}; the candidate "
                "is not fully ready in P3 terms — and P3 readiness would still "
                "not imply P4 admission"
            ),
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.SOURCE_READINESS_MARKER,
                    explanation=f"marker is {marker!r}, expected {P3_READY_MARKER!r}",
                ),
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.P3_READINESS_MARKER,
        state=ExecAdmissionState.ADMIT,
        reason=(
            f"P3 marker is {P3_READY_MARKER!r}; readiness lets the candidate "
            "enter later gates only — P3 readiness is not P4 admission"
        ),
    )


def _gate_authority_ref(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if not request.requested_authority_ref:
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.AUTHORITY_REF,
            state=ExecAdmissionState.REQUIRE_OPERATOR,
            reason=(
                "candidate names no authority scope ref; an operator must bind "
                "one — the ref is a scope name, never a P9 grant"
            ),
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.AUTHORITY_REF,
                    explanation="requested_authority_ref is missing",
                ),
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.AUTHORITY_REF,
        state=ExecAdmissionState.ADMIT,
        reason="authority scope ref present; a ref is not P9 authorization",
    )


def _gate_sandbox_profile(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if (
        request.requested_execution_mode in SANDBOX_REQUIRED_MODES
        and not request.requested_sandbox_profile
    ):
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.SANDBOX_PROFILE,
            state=ExecAdmissionState.HOLD,
            reason=(
                f"mode {request.requested_execution_mode.value} requires a sandbox "
                "profile ref; none was named — naming one would still execute nothing"
            ),
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.SANDBOX_PROFILE,
                    explanation="requested_sandbox_profile is missing for a sandbox-required mode",
                ),
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.SANDBOX_PROFILE,
        state=ExecAdmissionState.ADMIT,
        reason="sandbox profile requirement satisfied; no sandbox is executed",
    )


def _gate_budget_ref(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if not request.requested_budget_ref:
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.BUDGET_REF,
            state=ExecAdmissionState.HOLD,
            reason="candidate names no budget scope ref; nothing is billed either way",
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.BUDGET_REF,
                    explanation="requested_budget_ref is missing",
                ),
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.BUDGET_REF,
        state=ExecAdmissionState.ADMIT,
        reason="budget scope ref present; a ref allocates and bills nothing",
    )


def _gate_verifier_requirement(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if (
        request.requested_execution_mode in VERIFIER_REQUIRED_MODES
        and not request.requested_verifier_ref
    ):
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.VERIFIER_REQUIREMENT,
            state=ExecAdmissionState.REQUIRE_VERIFIER,
            reason=(
                f"risky mode {request.requested_execution_mode.value} requires a "
                "verifier ref; a ref never runs the verifier"
            ),
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.VERIFIER_REF,
                    explanation="requested_verifier_ref is missing for a verifier-required mode",
                ),
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.VERIFIER_REQUIREMENT,
        state=ExecAdmissionState.ADMIT,
        reason="verifier requirement satisfied; no verifier is executed",
    )


def _gate_trace_binding_availability(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if request.requested_trace_binding is TraceBindingStatus.ERROR:
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.TRACE_BINDING_AVAILABILITY,
            state=ExecAdmissionState.ERROR,
            reason="trace binding status is ERROR; the candidate cannot be classified",
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.TRACE_BINDING_AVAILABILITY,
        state=ExecAdmissionState.ADMIT,
        reason=(
            "trace binding is honestly unavailable in P4-EXEC-A and does not "
            "block admission; binding belongs to P4-EXEC-B and proof to P5"
        ),
    )


def _gate_policy_custos_availability(request: ExecAdmissionRequest) -> ExecAdmissionGateResult:
    if not request.requested_policy_context_ref:
        return ExecAdmissionGateResult(
            gate=ExecAdmissionGateKind.POLICY_CUSTOS_AVAILABILITY,
            state=ExecAdmissionState.REQUIRE_POLICY,
            reason=(
                "candidate names no policy context ref; a ref would still be "
                "shadow-only — enforcement belongs to P9 Custos"
            ),
            missing=(
                ExecMissingRequirement(
                    kind=ExecMissingRequirementKind.POLICY_CONTEXT_REF,
                    explanation="requested_policy_context_ref is missing",
                ),
            ),
        )
    return ExecAdmissionGateResult(
        gate=ExecAdmissionGateKind.POLICY_CUSTOS_AVAILABILITY,
        state=ExecAdmissionState.ADMIT,
        reason=(
            "policy context ref present shadow-only; Custos enforcement is "
            "unavailable and admission is not authorization"
        ),
    )


_GATE_CHAIN = (
    _gate_source_validity,
    _gate_p3_readiness_marker,
    _gate_authority_ref,
    _gate_sandbox_profile,
    _gate_budget_ref,
    _gate_verifier_requirement,
    _gate_trace_binding_availability,
    _gate_policy_custos_availability,
)


def decide_admission(request: ExecAdmissionRequest) -> ExecAdmissionDecision:
    """Deterministically decide admission through the gate chain.

    Pure function: same request, same decision. The first non-ADMIT gate
    locks the outcome (NCF-style primary blocker). No side effects — no
    runtime.submit, no Custos call, no Trace write, no tool/model/sandbox.
    """
    gate_results: list[ExecAdmissionGateResult] = []
    locked: ExecAdmissionGateResult | None = None
    for gate in _GATE_CHAIN:
        result = gate(request)
        gate_results.append(result)
        if result.state is not ExecAdmissionState.ADMIT:
            locked = result
            break

    if locked is None:
        state = ExecAdmissionState.ADMIT
        reason = (
            "all admission gates passed; ADMIT is structural eligibility only — "
            "not P9 authorization, not execution, not proof"
        )
        missing: tuple[ExecMissingRequirement, ...] = ()
    else:
        state = locked.state
        reason = locked.reason
        missing = locked.missing

    policy_status = (
        ExecPolicyStatus.SHADOW_ONLY
        if request.requested_policy_context_ref
        else ExecPolicyStatus.ENFORCEMENT_UNAVAILABLE
    )
    decision_id = "exec-adm-" + stable_hash(
        (request.request_hash, state.value, reason)
    )[:16]
    return ExecAdmissionDecision(
        decision_id=decision_id,
        request_id=request.request_id,
        state=state,
        reason=reason,
        gate_results=tuple(gate_results),
        missing_requirements=missing,
        unavailable_reasons=STANDARD_UNAVAILABLE_REASONS,
        truth_label=request.truth_label,
        policy_status=policy_status,
        custos_status=ExecCustosStatus.ENFORCEMENT_UNAVAILABLE,
        trace_status=ExecTraceStatus.TRACE_VERIFICATION_UNAVAILABLE,
    )


def build_dev_fixture_admission_request(**overrides: object) -> ExecAdmissionRequest:
    """DEV_FIXTURE P3-like candidate for tests only. A fixture is not LIVE."""
    values: dict[str, object] = {
        "request_id": "exec-req-fixture-001",
        "source_p3_candidate_ref": (
            "aurel_flow.flow_dispatchability/DispatchabilityFrame:unit-fixture-001"
        ),
        "source_dispatchability_reason": P3_READY_MARKER,
        "requested_execution_mode": ExecutionMode.TOOL,
        "source_flow_run_id": "flow-run-fixture-001",
        "source_atomic_unit_id": "unit-fixture-001",
        "requested_tool_name": "read_file",
        "requested_args_hash": stable_hash({"path": "README.md"}),
        "requested_sandbox_profile": "sandbox-profile-readonly",
        "requested_budget_ref": "budget-scope-fixture-001",
        "requested_authority_ref": "authority-scope-fixture-001",
        "requested_policy_context_ref": "policy-context-fixture-001",
        "requested_verifier_ref": "verifier-ref-fixture-001",
        "requested_trace_binding": TraceBindingStatus.TRACE_BOUND_UNAVAILABLE,
        "truth_label": ExecTruthLabel.DEV_FIXTURE,
    }
    values.update(overrides)
    return ExecAdmissionRequest(**values)
