"""P3-FLOW-H autonomy gates / safety candidates / drift-violation layer (P3.16).

A gate decision is not authority and not execution: it can hold, block,
freeze, downgrade, or require checkpoint/verifier/proof/authority — it can
never allow live action. Downgrade/freeze/resume/escalation are candidates
only; a violation signal creates a review need, never punishment or
enforcement; an operator override candidate is not Custos authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_autonomy import (
    AUTONOMY_AUTHORITY_UNAVAILABLE_REASON,
    GOVERNED_AUTONOMY_TIER_ORDER,
    AutonomyDecisionClass,
    GovernedAutonomyLevel,
    OperatorSelectedAutonomyMode,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUTONOMY_GATE_INPUT_VERSION = "autonomy_gate_input.v1"
AUTONOMY_GATE_RESULT_VERSION = "autonomy_gate_result.v1"
AUTONOMY_SAFETY_CANDIDATE_VERSION = "autonomy_safety_candidate.v1"
AUTONOMY_VIOLATION_SIGNAL_VERSION = "autonomy_violation_signal.v1"
OPERATOR_AUTONOMY_OVERRIDE_CANDIDATE_VERSION = (
    "operator_autonomy_override_candidate.v1"
)

GATE_AUTHORITY_UNAVAILABLE_REASON = (
    "a gate decision restricts a candidate; it grants no authority and "
    "executes nothing — P4 executes and P9 authorizes"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


class AutonomyGateDecision(str, Enum):
    """Closed-world gate outcomes. No outcome is authority or execution."""

    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HOLD = "HOLD"
    REQUIRE_OPERATOR_REVIEW = "REQUIRE_OPERATOR_REVIEW"
    REQUIRE_CHECKPOINT = "REQUIRE_CHECKPOINT"
    REQUIRE_VERIFIER = "REQUIRE_VERIFIER"
    REQUIRE_PROOF = "REQUIRE_PROOF"
    REQUIRE_AUTHORITY = "REQUIRE_AUTHORITY"
    DOWNGRADE_AUTONOMY = "DOWNGRADE_AUTONOMY"
    FREEZE_AUTONOMY = "FREEZE_AUTONOMY"
    BLOCK = "BLOCK"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class AutonomyGateInput(_CanonicalMixin):
    """Declared gate inputs. Nothing here is measured from live execution."""

    run_id: str
    level: GovernedAutonomyLevel
    decision_class: AutonomyDecisionClass
    risk_high: bool = False
    irreversible: bool = False
    reversibility_available: bool = True
    external_side_effect: bool = False
    budget_exhausted: bool = False
    retry_storm_active: bool = False
    no_progress_active: bool = False
    checkpoint_missing: bool = False


@dataclass(frozen=True)
class AutonomyGateResult(_CanonicalMixin):
    """One deterministic gate outcome. Not authority, not execution."""

    gate_id: str
    contract_version: str
    run_id: str
    decision: AutonomyGateDecision
    reason: str
    truth_label: FlowTruthLabel
    requires_operator_review: bool = False
    future_p4_required: bool = False
    future_p5_required: bool = False
    future_p9_required: bool = False
    unavailable_reason: str = GATE_AUTHORITY_UNAVAILABLE_REASON
    gate_is_not_authority: bool = True
    gate_is_not_execution: bool = True
    authority_granted: bool = False
    permission_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "gate_is_not_authority", "gate_is_not_execution")
        _forbid_true(
            self, "authority_granted", "permission_granted", "execution_available"
        )


def _gate_result(
    gate_input: AutonomyGateInput,
    decision: AutonomyGateDecision,
    reason: str,
    *,
    requires_operator_review: bool = False,
    future_p4_required: bool = False,
    future_p5_required: bool = False,
    future_p9_required: bool = False,
) -> AutonomyGateResult:
    payload = {
        "contract_version": AUTONOMY_GATE_RESULT_VERSION,
        "gate_input": gate_input.to_canonical_dict(),
        "decision": decision.value,
    }
    return AutonomyGateResult(
        gate_id="flagt-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_GATE_RESULT_VERSION,
        run_id=gate_input.run_id,
        decision=decision,
        reason=reason,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        requires_operator_review=requires_operator_review,
        future_p4_required=future_p4_required,
        future_p5_required=future_p5_required,
        future_p9_required=future_p9_required,
    )


def evaluate_autonomy_gate(gate_input: AutonomyGateInput) -> AutonomyGateResult:
    """Deterministic gate ladder over declared risk/reversibility/budget state."""

    if gate_input.budget_exhausted and gate_input.retry_storm_active:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.FREEZE_AUTONOMY,
            "budget exhausted during a retry storm: freeze autonomy candidate",
            requires_operator_review=True,
        )
    if gate_input.retry_storm_active:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.DOWNGRADE_AUTONOMY,
            "retry storm active: downgrade autonomy candidate",
            requires_operator_review=True,
        )
    if gate_input.no_progress_active:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.REQUIRE_OPERATOR_REVIEW,
            "no progress: the operator must review before more candidates",
            requires_operator_review=True,
        )
    if gate_input.budget_exhausted:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.HOLD,
            "recovery budget exhausted: hold candidates for operator review",
            requires_operator_review=True,
        )
    if gate_input.external_side_effect and gate_input.risk_high:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.BLOCK,
            "high-risk external side effect: blocked in P3",
            requires_operator_review=True,
            future_p4_required=True,
            future_p9_required=True,
        )
    if gate_input.external_side_effect:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.REQUIRE_AUTHORITY,
            "external side effect requires future P9 authority and P4 execution",
            requires_operator_review=True,
            future_p4_required=True,
            future_p9_required=True,
        )
    if gate_input.checkpoint_missing or (
        gate_input.irreversible and not gate_input.reversibility_available
    ):
        return _gate_result(
            gate_input,
            AutonomyGateDecision.REQUIRE_CHECKPOINT,
            "irreversible or checkpoint-missing action requires the "
            "P3-FLOW-F pre-recovery checkpoint discipline",
            requires_operator_review=True,
        )
    if gate_input.irreversible:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.REQUIRE_PROOF,
            "irreversible action requires future P5 proof even with "
            "reversibility available",
            requires_operator_review=True,
            future_p5_required=True,
        )
    if gate_input.risk_high:
        return _gate_result(
            gate_input,
            AutonomyGateDecision.REQUIRE_VERIFIER,
            "high-risk candidate requires a verifier expectation",
            requires_operator_review=True,
        )
    return _gate_result(
        gate_input,
        AutonomyGateDecision.ALLOW_CANDIDATE,
        "no gate trigger active: candidate may proceed as candidate only",
    )


class AutonomySafetyTrigger(str, Enum):
    """Why a safety candidate was raised."""

    RETRY_STORM = "RETRY_STORM"
    NO_PROGRESS = "NO_PROGRESS"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    SEMANTIC_SILENT_FAILURE = "SEMANTIC_SILENT_FAILURE"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    TOPOLOGY_AMPLIFICATION_RISK = "TOPOLOGY_AMPLIFICATION_RISK"
    DIVERSITY_CORRELATION_RISK = "DIVERSITY_CORRELATION_RISK"
    CHECKPOINT_MISSING = "CHECKPOINT_MISSING"
    OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
    POLICY_UNKNOWN = "POLICY_UNKNOWN"
    AUTHORITY_UNAVAILABLE = "AUTHORITY_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class AutonomySafetyCandidateKind(str, Enum):
    """Candidate-only safety responses. None of them acts."""

    DOWNGRADE_CANDIDATE = "DOWNGRADE_CANDIDATE"
    FREEZE_CANDIDATE = "FREEZE_CANDIDATE"
    RESUME_CANDIDATE = "RESUME_CANDIDATE"
    ESCALATION_CANDIDATE = "ESCALATION_CANDIDATE"


@dataclass(frozen=True)
class AutonomySafetyCandidate(_CanonicalMixin):
    """Downgrade/freeze/resume/escalation as candidates only.

    A downgrade candidate is not a mode change, a freeze candidate is not an
    execution stop, a resume candidate is not permission, and an escalation
    candidate is not approval.
    """

    candidate_id: str
    contract_version: str
    run_id: str
    kind: AutonomySafetyCandidateKind
    trigger: AutonomySafetyTrigger
    from_level: GovernedAutonomyLevel
    reason: str
    truth_label: FlowTruthLabel
    to_level: GovernedAutonomyLevel | None = None
    unavailable_reason: str = GATE_AUTHORITY_UNAVAILABLE_REASON
    requires_operator_review: bool = True
    mode_changed: bool = False
    execution_stopped: bool = False
    permission_granted: bool = False
    approval_granted: bool = False
    authority_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_operator_review")
        _forbid_true(
            self,
            "mode_changed",
            "execution_stopped",
            "permission_granted",
            "approval_granted",
            "authority_granted",
        )
        if self.kind is AutonomySafetyCandidateKind.DOWNGRADE_CANDIDATE:
            if self.to_level is None:
                raise AurelFlowValidationError(
                    "a downgrade candidate must name a target level",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="to_level",
                )
            from_tier = GOVERNED_AUTONOMY_TIER_ORDER.get(self.from_level)
            to_tier = GOVERNED_AUTONOMY_TIER_ORDER.get(self.to_level)
            if from_tier is None or to_tier is None or to_tier >= from_tier:
                raise AurelFlowValidationError(
                    "a downgrade candidate must move to a strictly lower "
                    "tier; anything else is a self-upgrade attempt",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="to_level",
                )


def build_autonomy_safety_candidate(
    *,
    run_id: str,
    kind: AutonomySafetyCandidateKind,
    trigger: AutonomySafetyTrigger,
    from_level: GovernedAutonomyLevel,
    reason: str,
    to_level: GovernedAutonomyLevel | None = None,
) -> AutonomySafetyCandidate:
    payload = {
        "contract_version": AUTONOMY_SAFETY_CANDIDATE_VERSION,
        "run_id": run_id,
        "kind": kind.value,
        "trigger": trigger.value,
        "from_level": from_level.value,
        "to_level": to_level.value if to_level else "",
        "reason": reason,
    }
    return AutonomySafetyCandidate(
        candidate_id="flasc-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_SAFETY_CANDIDATE_VERSION,
        run_id=run_id,
        kind=kind,
        trigger=trigger,
        from_level=from_level,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        to_level=to_level,
    )


class AutonomyViolationKind(str, Enum):
    """Closed-world autonomy drift/violation vocabulary."""

    SCOPE_EXCEEDED = "SCOPE_EXCEEDED"
    FORBIDDEN_ACTION_REQUESTED = "FORBIDDEN_ACTION_REQUESTED"
    EXTERNAL_SIDE_EFFECT_ATTEMPTED = "EXTERNAL_SIDE_EFFECT_ATTEMPTED"
    PROOF_IMPLIED_WITHOUT_TRACE = "PROOF_IMPLIED_WITHOUT_TRACE"
    AUTHORITY_IMPLIED_WITHOUT_CUSTOS = "AUTHORITY_IMPLIED_WITHOUT_CUSTOS"
    SELF_UPGRADE_ATTEMPTED = "SELF_UPGRADE_ATTEMPTED"
    BUDGET_EXHAUSTION_IGNORED = "BUDGET_EXHAUSTION_IGNORED"
    RETRY_STORM_GUARD_IGNORED = "RETRY_STORM_GUARD_IGNORED"
    NO_PROGRESS_GUARD_IGNORED = "NO_PROGRESS_GUARD_IGNORED"
    CHECKPOINT_REQUIREMENT_BYPASSED = "CHECKPOINT_REQUIREMENT_BYPASSED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class AutonomyViolationSignal(_CanonicalMixin):
    """A drift/violation record. Not punishment, not enforcement."""

    violation_id: str
    contract_version: str
    run_id: str
    kind: AutonomyViolationKind
    detail: str
    truth_label: FlowTruthLabel
    attempted_self_upgrade: bool = False
    requires_freeze_candidate: bool = False
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    requires_operator_review: bool = True
    violation_is_not_punishment: bool = True
    violation_is_not_enforcement: bool = True
    authority_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_operator_review",
            "violation_is_not_punishment",
            "violation_is_not_enforcement",
        )
        _forbid_true(self, "authority_granted", "execution_available")
        if (
            self.kind is AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED
            and not (self.attempted_self_upgrade and self.requires_freeze_candidate)
        ):
            raise AurelFlowValidationError(
                "a self-upgrade violation must mark attempted_self_upgrade "
                "and require a freeze candidate",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="attempted_self_upgrade",
            )


def build_autonomy_violation_signal(
    *,
    run_id: str,
    kind: AutonomyViolationKind,
    detail: str,
) -> AutonomyViolationSignal:
    is_self_upgrade = kind is AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED
    payload = {
        "contract_version": AUTONOMY_VIOLATION_SIGNAL_VERSION,
        "run_id": run_id,
        "kind": kind.value,
        "detail": detail,
    }
    return AutonomyViolationSignal(
        violation_id="flavs-" + stable_hash(payload)[:16],
        contract_version=AUTONOMY_VIOLATION_SIGNAL_VERSION,
        run_id=run_id,
        kind=kind,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        attempted_self_upgrade=is_self_upgrade,
        requires_freeze_candidate=is_self_upgrade,
    )


def detect_self_upgrade_violation(
    mode: OperatorSelectedAutonomyMode,
    *,
    requested_level: GovernedAutonomyLevel,
    requested_by_operator: bool,
) -> AutonomyViolationSignal | None:
    """A non-operator request for a strictly higher tier is a violation.

    Detection produces a review need, never enforcement. Operator requests
    are not violations — they become override candidates instead.
    """

    if requested_by_operator:
        return None
    current_tier = GOVERNED_AUTONOMY_TIER_ORDER.get(mode.level)
    requested_tier = GOVERNED_AUTONOMY_TIER_ORDER.get(requested_level)
    if requested_tier is None:
        # A9/UNAVAILABLE/ERROR is never a legal upgrade target for Aurel.
        return build_autonomy_violation_signal(
            run_id=mode.run_id,
            kind=AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED,
            detail=(
                f"non-operator request for untiered level "
                f"{requested_level.value} from {mode.level.value}"
            ),
        )
    if current_tier is None or requested_tier > current_tier:
        return build_autonomy_violation_signal(
            run_id=mode.run_id,
            kind=AutonomyViolationKind.SELF_UPGRADE_ATTEMPTED,
            detail=(
                f"non-operator request to raise autonomy from "
                f"{mode.level.value} to {requested_level.value}"
            ),
        )
    return None


@dataclass(frozen=True)
class OperatorAutonomyOverrideCandidate(_CanonicalMixin):
    """An operator's request to change autonomy. A candidate, not authority."""

    candidate_id: str
    contract_version: str
    run_id: str
    current_level: GovernedAutonomyLevel
    requested_level: GovernedAutonomyLevel
    requested_by_operator: str
    reason: str
    raises_autonomy: bool
    truth_label: FlowTruthLabel
    future_p9_required: bool
    unavailable_reason: str = AUTONOMY_AUTHORITY_UNAVAILABLE_REASON
    override_is_not_authority: bool = True
    requires_operator_review: bool = True
    permission_granted: bool = False
    authority_granted: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "override_is_not_authority", "requires_operator_review")
        _forbid_true(
            self, "permission_granted", "authority_granted", "execution_available"
        )
        if not self.requested_by_operator:
            raise AurelFlowValidationError(
                "an override candidate must name the requesting operator",
                code=AurelFlowErrorCode.EMPTY_ACTOR_ID,
                field="requested_by_operator",
            )
        if self.raises_autonomy and not self.future_p9_required:
            raise AurelFlowValidationError(
                "raising autonomy requires future P9 authority",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="future_p9_required",
            )


def build_operator_autonomy_override_candidate(
    *,
    run_id: str,
    current_level: GovernedAutonomyLevel,
    requested_level: GovernedAutonomyLevel,
    requested_by_operator: str,
    reason: str,
) -> OperatorAutonomyOverrideCandidate:
    current_tier = GOVERNED_AUTONOMY_TIER_ORDER.get(current_level, -1)
    requested_tier = GOVERNED_AUTONOMY_TIER_ORDER.get(requested_level)
    raises_autonomy = requested_tier is None or requested_tier > current_tier
    payload = {
        "contract_version": OPERATOR_AUTONOMY_OVERRIDE_CANDIDATE_VERSION,
        "run_id": run_id,
        "current_level": current_level.value,
        "requested_level": requested_level.value,
        "requested_by_operator": requested_by_operator,
        "reason": reason,
    }
    return OperatorAutonomyOverrideCandidate(
        candidate_id="flaoc-" + stable_hash(payload)[:16],
        contract_version=OPERATOR_AUTONOMY_OVERRIDE_CANDIDATE_VERSION,
        run_id=run_id,
        current_level=current_level,
        requested_level=requested_level,
        requested_by_operator=requested_by_operator,
        reason=reason,
        raises_autonomy=raises_autonomy,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        future_p9_required=raises_autonomy,
    )
