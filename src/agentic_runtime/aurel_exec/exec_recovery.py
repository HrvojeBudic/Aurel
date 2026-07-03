"""P4-EXEC-E bounded recovery plan — a plan is not recovery execution.

A ``BoundedRecoveryPlan`` recommends exactly one bounded action for a
classified failure and declares its approval/evidence requirements. It
executes nothing: ``recovery_executed``, automatic retry, and rollback
execution are structurally False/unavailable. Every retry-shaped
recommendation requires operator approval — there is no self-healing loop
and the bridge is never re-submitted by this pack. The action vocabulary is
E-local (``BoundedRecoveryActionKind``) because the A-pack already exports
a `RecoveryActionKind` vocabulary with different admission-era semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_failure import FailureClass, FailureClassification
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_nonempty,
    stable_hash,
)

BOUNDED_RECOVERY_PLAN_VERSION = "bounded_recovery_plan.v1"
NO_AUTOMATIC_RETRY_PROOF_VERSION = "no_automatic_retry_proof.v1"
NO_SELF_HEALING_PROOF_VERSION = "no_self_healing_proof.v1"

AUTOMATIC_RETRY_UNAVAILABLE_REASON = (
    "automatic retry is unavailable; every retry-shaped recommendation "
    "requires operator approval and a fresh pass through the full "
    "admission/lease/session/claim/bridge guard chain — the bridge is never "
    "re-submitted by the judgment layer"
)
SELF_HEALING_UNAVAILABLE_REASON = (
    "no recovery engine or self-healing loop exists; a bounded recovery "
    "plan recommends one action and stops — repair execution belongs to a "
    "future pack under P9 authority with P5 evidence"
)


class BoundedRecoveryActionKind(str, Enum):
    NONE = "NONE"
    RETRY_SAME_INPUT = "RETRY_SAME_INPUT"
    RETRY_WITH_CONTEXT_REFRESH = "RETRY_WITH_CONTEXT_REFRESH"
    RETRY_WITH_LOWER_RISK_MODE = "RETRY_WITH_LOWER_RISK_MODE"
    REQUEST_OPERATOR_REVIEW = "REQUEST_OPERATOR_REVIEW"
    ESCALATE_ALGEDONIC = "ESCALATE_ALGEDONIC"
    ROLLBACK_REF_ONLY = "ROLLBACK_REF_ONLY"
    STOP = "STOP"


_RETRY_ACTIONS = (
    BoundedRecoveryActionKind.RETRY_SAME_INPUT,
    BoundedRecoveryActionKind.RETRY_WITH_CONTEXT_REFRESH,
    BoundedRecoveryActionKind.RETRY_WITH_LOWER_RISK_MODE,
)

# Total deterministic recommendation table:
# FailureClass -> (action, requires_operator_approval, requires_p9, requires_p5)
RECOVERY_RECOMMENDATIONS: dict[
    FailureClass, tuple[BoundedRecoveryActionKind, bool, bool, bool]
] = {
    FailureClass.NONE: (BoundedRecoveryActionKind.NONE, False, False, False),
    FailureClass.RUNTIME_ERROR: (
        BoundedRecoveryActionKind.REQUEST_OPERATOR_REVIEW, True, False, False,
    ),
    FailureClass.POLICY_BLOCKED: (BoundedRecoveryActionKind.STOP, True, True, False),
    FailureClass.LEASE_INVALID: (
        BoundedRecoveryActionKind.RETRY_WITH_CONTEXT_REFRESH, True, False, False,
    ),
    FailureClass.MODE_UNAVAILABLE: (
        BoundedRecoveryActionKind.RETRY_WITH_LOWER_RISK_MODE, True, False, False,
    ),
    FailureClass.VERIFICATION_FAILED: (
        BoundedRecoveryActionKind.ESCALATE_ALGEDONIC, True, False, True,
    ),
    FailureClass.VERIFIER_UNAVAILABLE: (
        BoundedRecoveryActionKind.REQUEST_OPERATOR_REVIEW, True, False, True,
    ),
    FailureClass.OUTPUT_CONTRACT_FAILED: (
        BoundedRecoveryActionKind.ROLLBACK_REF_ONLY, True, True, True,
    ),
    FailureClass.TOOL_ERROR: (
        BoundedRecoveryActionKind.RETRY_SAME_INPUT, True, False, False,
    ),
    FailureClass.TIMEOUT: (
        BoundedRecoveryActionKind.RETRY_WITH_CONTEXT_REFRESH, True, False, False,
    ),
    FailureClass.RESOURCE_EXHAUSTED: (
        BoundedRecoveryActionKind.ESCALATE_ALGEDONIC, True, True, False,
    ),
    FailureClass.UNKNOWN_ERROR: (
        BoundedRecoveryActionKind.ESCALATE_ALGEDONIC, True, True, True,
    ),
}


@dataclass(frozen=True)
class BoundedRecoveryPlan(_ExecCanonicalMixin):
    """One bounded recommendation. Never recovery execution."""

    recovery_plan_id: str
    failure_classification_id: str
    exec_job_id: str
    attempt_id: str
    allowed: bool
    recommended_action: BoundedRecoveryActionKind
    max_attempts: int
    remaining_attempts: int
    requires_operator_approval: bool
    requires_p9_authority: bool
    requires_p5_evidence: bool
    reason: str
    truth_label: ExecTruthLabel
    contract_version: str = BOUNDED_RECOVERY_PLAN_VERSION
    recovery_executed: bool = False
    automatic_retry_available: bool = False
    rollback_execution_available: bool = False
    self_healing_available: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "recovery_plan_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(
            self,
            "recovery_executed",
            "automatic_retry_available",
            "rollback_execution_available",
            "self_healing_available",
        )
        if self.remaining_attempts < 0 or self.remaining_attempts > self.max_attempts:
            raise AurelExecValidationError(
                "remaining_attempts must be within [0, max_attempts]",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="remaining_attempts",
            )
        if (
            self.recommended_action in _RETRY_ACTIONS
            and not self.requires_operator_approval
        ):
            raise AurelExecValidationError(
                "a retry-shaped recommendation without operator approval is "
                "automatic retry, which is unavailable",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="requires_operator_approval",
            )
        if self.recommended_action in _RETRY_ACTIONS and self.remaining_attempts == 0:
            raise AurelExecValidationError(
                "a retry-shaped recommendation with zero remaining attempts "
                "is unconstructible; the plan must downgrade to review",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="recommended_action",
            )

    @property
    def plan_hash(self) -> str:
        return stable_hash(self)


def create_bounded_recovery_plan(
    classification: FailureClassification,
    *,
    max_attempts: int = 1,
    attempts_used: int = 0,
) -> BoundedRecoveryPlan:
    """Create one deterministic bounded plan. Creating executes nothing.

    Retry-shaped recommendations with exhausted attempts deterministically
    downgrade to REQUEST_OPERATOR_REVIEW — no loop, no storm.
    """
    action, operator, p9, p5 = RECOVERY_RECOMMENDATIONS[classification.failure_class]
    remaining = max(0, max_attempts - attempts_used)
    reason = (
        f"bounded recommendation for {classification.failure_class.value}: "
        f"{action.value}; the plan executes nothing"
    )
    if action in _RETRY_ACTIONS and remaining == 0:
        action = BoundedRecoveryActionKind.REQUEST_OPERATOR_REVIEW
        reason = (
            f"retry budget exhausted for {classification.failure_class.value}; "
            "downgraded to operator review — no retry storm"
        )
        operator = True
    return BoundedRecoveryPlan(
        recovery_plan_id="exec-recovery-plan-"
        + stable_hash((classification.failure_classification_id, action.value, remaining))[:16],
        failure_classification_id=classification.failure_classification_id,
        exec_job_id=classification.exec_job_id,
        attempt_id=classification.attempt_id,
        allowed=action is not BoundedRecoveryActionKind.NONE,
        recommended_action=action,
        max_attempts=max_attempts,
        remaining_attempts=remaining,
        requires_operator_approval=operator,
        requires_p9_authority=p9,
        requires_p5_evidence=p5,
        reason=reason,
        truth_label=ExecTruthLabel.LIVE,
    )


@dataclass(frozen=True)
class NoAutomaticRetryProof(_ExecCanonicalMixin):
    """Evidence that no automatic retry path exists."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_AUTOMATIC_RETRY_PROOF_VERSION
    automatic_retry_available: bool = False
    bridge_resubmit_performed: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "automatic_retry_available", "bridge_resubmit_performed")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_automatic_retry_proof() -> NoAutomaticRetryProof:
    return NoAutomaticRetryProof(
        reason=AUTOMATIC_RETRY_UNAVAILABLE_REASON,
        future_pack_owner="future scoped-retry pack under operator approval + P9",
    )


@dataclass(frozen=True)
class NoSelfHealingProof(_ExecCanonicalMixin):
    """Evidence that no recovery engine or self-healing loop exists."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_SELF_HEALING_PROOF_VERSION
    recovery_execution_available: bool = False
    self_healing_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "recovery_execution_available", "self_healing_available")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_self_healing_proof() -> NoSelfHealingProof:
    return NoSelfHealingProof(
        reason=SELF_HEALING_UNAVAILABLE_REASON,
        future_pack_owner="future bounded-recovery execution pack under P9 authority",
    )
