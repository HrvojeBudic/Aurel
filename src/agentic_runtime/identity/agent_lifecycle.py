"""P1.4.17 Agent Lifecycle Eligibility State Machine.

Governed lifecycle model for agent identities.
Lifecycle state determines operational lane eligibility, NOT authority.

P1.4.17 implements lifecycle eligibility, not runtime permission.
It does not execute tools, grant authority, grant consent, or mutate identity
state through validation/recommendation.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AgentLifecycleState(str, Enum):
    """Governed lifecycle state for agent identities."""
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"
    REVOKED = "REVOKED"

    @property
    def is_terminal(self) -> bool:
        return self == AgentLifecycleState.REVOKED


class LifecycleReasonCode(str, Enum):
    """Taxonomy of lifecycle state change reasons."""
    INITIAL_CREATION = "INITIAL_CREATION"
    READY_FOR_EVALUATION = "READY_FOR_EVALUATION"
    EVALUATION_PASSED = "EVALUATION_PASSED"
    EVALUATION_FAILED = "EVALUATION_FAILED"

    AUTHORITY_DELTA_UNRESOLVED = "AUTHORITY_DELTA_UNRESOLVED"
    AUTHORITY_DELTA_RESOLVED = "AUTHORITY_DELTA_RESOLVED"

    CONSENT_MISSING = "CONSENT_MISSING"
    CONSENT_GRANTED = "CONSENT_GRANTED"
    CONSENT_REVOKED = "CONSENT_REVOKED"
    CONSENT_EXPIRED = "CONSENT_EXPIRED"

    SOURCE_ATTESTATION_VALID = "SOURCE_ATTESTATION_VALID"
    SOURCE_ATTESTATION_FAILED = "SOURCE_ATTESTATION_FAILED"

    CLAIM_BOUNDARY_VALID = "CLAIM_BOUNDARY_VALID"
    CLAIM_BOUNDARY_VIOLATION = "CLAIM_BOUNDARY_VIOLATION"

    DOCTRINE_BOUNDARY_VALID = "DOCTRINE_BOUNDARY_VALID"
    DOCTRINE_BOUNDARY_VIOLATION = "DOCTRINE_BOUNDARY_VIOLATION"

    POLICY_VIOLATION = "POLICY_VIOLATION"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    OPERATOR_ACTION = "OPERATOR_ACTION"

    DEPRECATED_BY_NEW_VERSION = "DEPRECATED_BY_NEW_VERSION"
    RETIRED_BY_OPERATOR = "RETIRED_BY_OPERATOR"
    REVOKED_BY_OPERATOR = "REVOKED_BY_OPERATOR"


class LifecycleLane(str, Enum):
    """Operational lane categories. Lanes determine eligibility, not permission."""
    SANDBOX = "SANDBOX"
    EVALUATION = "EVALUATION"
    LOCAL_READ_ONLY = "LOCAL_READ_ONLY"
    LOCAL_REVERSIBLE = "LOCAL_REVERSIBLE"
    GOVERNED_RUNTIME = "GOVERNED_RUNTIME"
    EXTERNAL_EFFECT = "EXTERNAL_EFFECT"
    DELEGATION = "DELEGATION"
    PRODUCTION = "PRODUCTION"
    AUDIT_ONLY = "AUDIT_ONLY"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentLifecycleTransitionRequest:
    """A request to transition an agent identity to a new lifecycle state."""
    request_id: str
    agent_id: str
    old_state: AgentLifecycleState
    requested_state: AgentLifecycleState
    reason_code: LifecycleReasonCode
    reason_text: str
    requested_by: str | None = None
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_refs: tuple[str, ...] = ()
    consent_refs: tuple[str, ...] = ()
    test_battery_refs: tuple[str, ...] = ()
    authority_delta_refs: tuple[str, ...] = ()
    source_attestation_refs: tuple[str, ...] = ()
    claim_decision_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentLifecycleTransitionDecision:
    """A decision on a lifecycle transition request. Does NOT mutate state."""
    decision_id: str
    request_id: str
    agent_id: str
    old_state: AgentLifecycleState
    requested_state: AgentLifecycleState
    allowed: bool
    resulting_state: AgentLifecycleState | None = None
    requires_evidence: bool = False
    requires_consent: bool = False
    requires_test_battery: bool = False
    requires_operator_review: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class AgentLifecycleTransitionEvent:
    """A recorded transition event (if the decision was allowed). Does NOT apply state."""
    event_id: str
    request_id: str
    decision_id: str
    agent_id: str
    old_state: AgentLifecycleState
    new_state: AgentLifecycleState
    reason_code: LifecycleReasonCode
    reason_text: str
    evidence_refs: tuple[str, ...] = ()
    consent_refs: tuple[str, ...] = ()
    test_battery_refs: tuple[str, ...] = ()
    authority_delta_refs: tuple[str, ...] = ()
    source_attestation_refs: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class AgentLifecyclePolicy:
    """Transition policy: which transitions are allowed and what they require."""
    allowed_transitions: dict[AgentLifecycleState, tuple[AgentLifecycleState, ...]]
    terminal_states: tuple[AgentLifecycleState, ...]
    active_requires_evidence: bool = True
    active_requires_test_battery: bool = True
    restricted_requires_reason: bool = True
    revoked_is_terminal: bool = True


@dataclass(frozen=True)
class AgentLifecycleEligibilityProfile:
    """Lane eligibility profile for a given lifecycle state."""
    agent_id: str
    lifecycle_state: AgentLifecycleState
    eligible_lanes: tuple[LifecycleLane, ...]
    blocked_lanes: tuple[LifecycleLane, ...]
    required_gates: tuple[str, ...]
    restriction_reasons: tuple[LifecycleReasonCode, ...] = ()
    hard_blocked: bool = False
    audit_only: bool = False
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Default transition policy
# ---------------------------------------------------------------------------

_TRANSITIONS: dict[AgentLifecycleState, tuple[AgentLifecycleState, ...]] = {
    AgentLifecycleState.DRAFT: (
        AgentLifecycleState.CANDIDATE,
        AgentLifecycleState.RETIRED,
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.CANDIDATE: (
        AgentLifecycleState.DRAFT,
        AgentLifecycleState.ACTIVE,
        AgentLifecycleState.RESTRICTED,
        AgentLifecycleState.RETIRED,
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.ACTIVE: (
        AgentLifecycleState.RESTRICTED,
        AgentLifecycleState.SUSPENDED,
        AgentLifecycleState.DEPRECATED,
        AgentLifecycleState.RETIRED,
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.RESTRICTED: (
        AgentLifecycleState.ACTIVE,
        AgentLifecycleState.SUSPENDED,
        AgentLifecycleState.DEPRECATED,
        AgentLifecycleState.RETIRED,
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.SUSPENDED: (
        AgentLifecycleState.RESTRICTED,
        AgentLifecycleState.RETIRED,
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.DEPRECATED: (
        AgentLifecycleState.RETIRED,
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.RETIRED: (
        AgentLifecycleState.REVOKED,
    ),
    AgentLifecycleState.REVOKED: (),
}

_DEFAULT_TERMINAL_STATES: tuple[AgentLifecycleState, ...] = (
    AgentLifecycleState.REVOKED,
)


def default_agent_lifecycle_policy() -> AgentLifecyclePolicy:
    return AgentLifecyclePolicy(
        allowed_transitions=_TRANSITIONS,
        terminal_states=_DEFAULT_TERMINAL_STATES,
        active_requires_evidence=True,
        active_requires_test_battery=True,
        restricted_requires_reason=True,
        revoked_is_terminal=True,
    )


# ---------------------------------------------------------------------------
# Transition validation
# ---------------------------------------------------------------------------


def validate_agent_lifecycle_transition(
    request: AgentLifecycleTransitionRequest,
    policy: AgentLifecyclePolicy | None = None,
) -> AgentLifecycleTransitionDecision:
    """Validate a lifecycle transition request. Fails closed. Does NOT mutate state."""
    if policy is None:
        policy = default_agent_lifecycle_policy()

    decision_id = (
        "ltd_"
        + hashlib.sha256(
            f"{request.request_id}:{request.old_state.value}:{request.requested_state.value}".encode()
        ).hexdigest()[:20]
    )
    blockers: list[str] = []
    warnings: list[str] = []
    req_evidence = False
    req_consent = False
    req_test_battery = False
    req_operator_review = False

    # -- Guard: REVOKED is terminal --
    if policy.revoked_is_terminal and request.old_state == AgentLifecycleState.REVOKED:
        blockers.append("revoked_is_terminal")
        return AgentLifecycleTransitionDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            agent_id=request.agent_id,
            old_state=request.old_state,
            requested_state=request.requested_state,
            allowed=False,
            resulting_state=None,
            blockers=tuple(blockers),
            reason="REVOKED is terminal; no transitions allowed",
        )

    # -- Guard: check policy allows this transition --
    allowed_targets = policy.allowed_transitions.get(request.old_state, ())
    if request.requested_state not in allowed_targets:
        blockers.append(
            f"forbidden_transition:{request.old_state.value}->{request.requested_state.value}"
        )
        return AgentLifecycleTransitionDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            agent_id=request.agent_id,
            old_state=request.old_state,
            requested_state=request.requested_state,
            allowed=False,
            resulting_state=None,
            requires_evidence=req_evidence,
            requires_consent=req_consent,
            requires_test_battery=req_test_battery,
            requires_operator_review=req_operator_review,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            reason=f"Transition {request.old_state.value} -> {request.requested_state.value} is not allowed",
        )

    # -- Guard: non-trivial transitions require reason_text --
    if request.old_state != request.requested_state and not request.reason_text.strip():
        blockers.append("reason_text_required")

    # -- Specific transition requirements --

    # Any transition TO ACTIVE
    if request.requested_state == AgentLifecycleState.ACTIVE:
        req_evidence = policy.active_requires_evidence
        req_test_battery = policy.active_requires_test_battery
        if not request.evidence_refs:
            blockers.append("evidence_refs_required_for_active")
        if not request.test_battery_refs:
            blockers.append("test_battery_refs_required_for_active")

    # CANDIDATE → ACTIVE
    if (
        request.old_state == AgentLifecycleState.CANDIDATE
        and request.requested_state == AgentLifecycleState.ACTIVE
    ):
        if request.reason_code not in (
            LifecycleReasonCode.EVALUATION_PASSED,
            LifecycleReasonCode.OPERATOR_ACTION,
        ):
            blockers.append(
                f"invalid_reason_code_for_candidate_activation:{request.reason_code.value}"
            )
        if not request.evidence_refs:
            blockers.append("candidate_activation_requires_evidence_refs")
        if not request.test_battery_refs:
            blockers.append("candidate_activation_requires_test_battery_refs")
        # Authority delta refs without consent is a blocker
        if request.authority_delta_refs and not request.consent_refs:
            blockers.append("authority_delta_refs_require_consent_refs")

    # RESTRICTED → ACTIVE
    if (
        request.old_state == AgentLifecycleState.RESTRICTED
        and request.requested_state == AgentLifecycleState.ACTIVE
    ):
        req_evidence = True
        req_test_battery = True
        if not request.evidence_refs:
            blockers.append("restricted_activation_requires_repair_evidence")
        if request.reason_code in (
            LifecycleReasonCode.CONSENT_REVOKED,
            LifecycleReasonCode.CONSENT_EXPIRED,
            LifecycleReasonCode.AUTHORITY_DELTA_UNRESOLVED,
        ):
            req_consent = True
            if not request.consent_refs:
                blockers.append("restricted_activation_requires_consent_refs")

    # SUSPENDED → RESTRICTED
    if (
        request.old_state == AgentLifecycleState.SUSPENDED
        and request.requested_state == AgentLifecycleState.RESTRICTED
    ):
        if request.reason_code not in (
            LifecycleReasonCode.OPERATOR_ACTION,
            LifecycleReasonCode.EVALUATION_PASSED,
        ):
            warnings.append("suspended_to_restricted_requires_evidence")
        if not request.reason_text.strip():
            blockers.append("reason_text_required_for_suspended_to_restricted")

    # ACTIVE → REVOKED
    if (
        request.old_state == AgentLifecycleState.ACTIVE
        and request.requested_state == AgentLifecycleState.REVOKED
    ):
        if request.reason_code not in (
            LifecycleReasonCode.REVOKED_BY_OPERATOR,
            LifecycleReasonCode.SECURITY_INCIDENT,
            LifecycleReasonCode.OPERATOR_ACTION,
        ):
            blockers.append(
                f"active_revocation_requires_valid_reason_code:{request.reason_code.value}"
            )
        if not request.reason_text.strip():
            blockers.append("revocation_requires_reason_text")

    # -- Compose decision --
    allowed = len(blockers) == 0
    reason_parts = []
    if allowed:
        reason_parts.append(
            f"Transition {request.old_state.value} -> {request.requested_state.value} allowed"
        )
    else:
        reason_parts.append(
            f"Transition {request.old_state.value} -> {request.requested_state.value} blocked"
        )
    if req_evidence:
        reason_parts.append("requires evidence")
    if req_consent:
        reason_parts.append("requires consent")
    if req_test_battery:
        reason_parts.append("requires test_battery")

    return AgentLifecycleTransitionDecision(
        decision_id=decision_id,
        request_id=request.request_id,
        agent_id=request.agent_id,
        old_state=request.old_state,
        requested_state=request.requested_state,
        allowed=allowed,
        resulting_state=request.requested_state if allowed else None,
        requires_evidence=req_evidence,
        requires_consent=req_consent,
        requires_test_battery=req_test_battery,
        requires_operator_review=req_operator_review,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        reason="; ".join(reason_parts),
    )


# ---------------------------------------------------------------------------
# Eligibility profile builder
# ---------------------------------------------------------------------------


_ELIGIBILITY_MAP: dict[
    AgentLifecycleState,
    tuple[
        tuple[LifecycleLane, ...],  # eligible
        tuple[LifecycleLane, ...],  # blocked
        tuple[str, ...],            # required gates
    ],
] = {
    AgentLifecycleState.DRAFT: (
        (
            LifecycleLane.SANDBOX,
            LifecycleLane.LOCAL_READ_ONLY,
        ),
        (
            LifecycleLane.GOVERNED_RUNTIME,
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        (
            "identity_validation",
            "source_attestation",
        ),
    ),
    AgentLifecycleState.CANDIDATE: (
        (
            LifecycleLane.SANDBOX,
            LifecycleLane.EVALUATION,
            LifecycleLane.LOCAL_READ_ONLY,
            LifecycleLane.LOCAL_REVERSIBLE,
        ),
        (
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        (
            "identity_test_battery",
            "source_attestation",
            "claim_boundary",
        ),
    ),
    AgentLifecycleState.ACTIVE: (
        (
            LifecycleLane.SANDBOX,
            LifecycleLane.EVALUATION,
            LifecycleLane.LOCAL_READ_ONLY,
            LifecycleLane.LOCAL_REVERSIBLE,
            LifecycleLane.GOVERNED_RUNTIME,
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        (),
        (
            "authority_scope",
            "autonomy_decision",
            "consent_if_required",
            "tool_permission",
            "policy_check",
            "claim_boundary",
        ),
    ),
    AgentLifecycleState.SUSPENDED: (
        (LifecycleLane.AUDIT_ONLY,),
        (
            LifecycleLane.GOVERNED_RUNTIME,
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        (
            "repair_evidence",
            "operator_review",
        ),
    ),
    AgentLifecycleState.DEPRECATED: (
        (
            LifecycleLane.LOCAL_READ_ONLY,
            LifecycleLane.AUDIT_ONLY,
        ),
        (
            LifecycleLane.GOVERNED_RUNTIME,
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        ("migration_if_needed",),
    ),
    AgentLifecycleState.RETIRED: (
        (LifecycleLane.AUDIT_ONLY,),
        (
            LifecycleLane.SANDBOX,
            LifecycleLane.EVALUATION,
            LifecycleLane.LOCAL_READ_ONLY,
            LifecycleLane.LOCAL_REVERSIBLE,
            LifecycleLane.GOVERNED_RUNTIME,
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        (),
    ),
    AgentLifecycleState.REVOKED: (
        (LifecycleLane.AUDIT_ONLY,),
        (
            LifecycleLane.SANDBOX,
            LifecycleLane.EVALUATION,
            LifecycleLane.LOCAL_READ_ONLY,
            LifecycleLane.LOCAL_REVERSIBLE,
            LifecycleLane.GOVERNED_RUNTIME,
            LifecycleLane.EXTERNAL_EFFECT,
            LifecycleLane.DELEGATION,
            LifecycleLane.PRODUCTION,
        ),
        (),
    ),
}

# RESTRICTED base (overridden by reason codes)
_RESTRICTED_BASE: tuple[tuple[LifecycleLane, ...], tuple[LifecycleLane, ...], tuple[str, ...]] = (
    (
        LifecycleLane.SANDBOX,
        LifecycleLane.EVALUATION,
        LifecycleLane.LOCAL_READ_ONLY,
        LifecycleLane.LOCAL_REVERSIBLE,
    ),
    (
        LifecycleLane.EXTERNAL_EFFECT,
        LifecycleLane.DELEGATION,
        LifecycleLane.PRODUCTION,
    ),
    (
        "restriction_repair",
        "operator_review_if_required",
    ),
)

# Security-incident-level reasons → audit only
_SECURITY_LEVEL_REASONS = frozenset({
    LifecycleReasonCode.SECURITY_INCIDENT,
    LifecycleReasonCode.SOURCE_ATTESTATION_FAILED,
})

# Consent-expired-type reasons → block external/delegation + require consent repair
_CONSENT_BLOCK_REASONS = frozenset({
    LifecycleReasonCode.CONSENT_EXPIRED,
    LifecycleReasonCode.CONSENT_REVOKED,
})


def build_agent_lifecycle_eligibility_profile(
    *,
    agent_id: str,
    lifecycle_state: AgentLifecycleState,
    restriction_reasons: tuple[LifecycleReasonCode, ...] = (),
) -> AgentLifecycleEligibilityProfile:
    """Build lane eligibility profile based on lifecycle state and restriction reasons."""

    if lifecycle_state == AgentLifecycleState.RESTRICTED:
        # RESTRICTED uses reason-sensitive profile
        if set(restriction_reasons) & _SECURITY_LEVEL_REASONS:
            eligible = (LifecycleLane.AUDIT_ONLY,)
            blocked = (
                LifecycleLane.GOVERNED_RUNTIME,
                LifecycleLane.EXTERNAL_EFFECT,
                LifecycleLane.DELEGATION,
                LifecycleLane.PRODUCTION,
            )
            gates = ("incident_review", "operator_review")
            audit_only = True
        elif set(restriction_reasons) & _CONSENT_BLOCK_REASONS:
            eligible = _RESTRICTED_BASE[0]
            blocked = (
                LifecycleLane.EXTERNAL_EFFECT,
                LifecycleLane.DELEGATION,
                LifecycleLane.PRODUCTION,
            )
            gates = ("consent_repair", "authority_delta_resolution", "operator_review_if_required")
            audit_only = False
        else:
            eligible, blocked, gates = _RESTRICTED_BASE
            audit_only = False

        return AgentLifecycleEligibilityProfile(
            agent_id=agent_id,
            lifecycle_state=lifecycle_state,
            eligible_lanes=eligible,
            blocked_lanes=blocked,
            required_gates=gates,
            restriction_reasons=restriction_reasons,
            audit_only=audit_only,
            hard_blocked=audit_only,
            blockers=tuple(
                f"restricted:{r.value}" for r in restriction_reasons
            ) if restriction_reasons else (),
        )

    # Non-RESTRICTED states use the static map
    entry = _ELIGIBILITY_MAP.get(lifecycle_state)
    if entry is None:
        return AgentLifecycleEligibilityProfile(
            agent_id=agent_id,
            lifecycle_state=lifecycle_state,
            eligible_lanes=(),
            blocked_lanes=tuple(LifecycleLane),
            required_gates=(),
            restriction_reasons=restriction_reasons,
            hard_blocked=True,
            blockers=("unknown_lifecycle_state",),
        )

    eligible, blocked, gates = entry
    audit_only = eligible == (LifecycleLane.AUDIT_ONLY,)
    hard_blocked = lifecycle_state in (
        AgentLifecycleState.REVOKED,
        AgentLifecycleState.RETIRED,
    )

    return AgentLifecycleEligibilityProfile(
        agent_id=agent_id,
        lifecycle_state=lifecycle_state,
        eligible_lanes=eligible,
        blocked_lanes=blocked,
        required_gates=gates,
        restriction_reasons=restriction_reasons,
        audit_only=audit_only,
        hard_blocked=hard_blocked,
    )


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------


def recommend_lifecycle_state(
    *,
    agent_id: str,
    current_state: AgentLifecycleState,
    battery_status: str | None = None,
    highest_failed_severity: str | None = None,
    unresolved_authority_delta: bool = False,
    consent_valid: bool | None = None,
    source_attestation_valid: bool | None = None,
    claim_boundary_valid: bool | None = None,
) -> AgentLifecycleTransitionDecision:
    """Recommend a lifecycle state change based on governance signals.
    Does NOT apply the transition.
    """
    decision_id = "lrec_" + hashlib.sha256(
        f"{agent_id}:{current_state.value}:{battery_status or ''}".encode()
    ).hexdigest()[:20]
    request_id = "lrq_" + hashlib.sha256(
        f"recommend:{agent_id}:{current_state.value}".encode()
    ).hexdigest()[:16]

    # Battery signals
    if battery_status == "FAILED" and highest_failed_severity == "CRITICAL":
        if current_state not in (AgentLifecycleState.SUSPENDED, AgentLifecycleState.REVOKED, AgentLifecycleState.RETIRED):
            return AgentLifecycleTransitionDecision(
                decision_id=decision_id,
                request_id=request_id,
                agent_id=agent_id,
                old_state=current_state,
                requested_state=AgentLifecycleState.SUSPENDED,
                allowed=False,  # recommendation, not application
                resulting_state=AgentLifecycleState.SUSPENDED,
                requires_evidence=True,
                requires_test_battery=True,
                blockers=(),
                warnings=("recommend_suspension:failed_critical_battery",),
                reason="Battery FAILED with CRITICAL severity — recommend SUSPENDED",
                )
    if battery_status in ("FAILED", "DEGRADED"):
        if current_state == AgentLifecycleState.ACTIVE:
            return AgentLifecycleTransitionDecision(
                decision_id=decision_id,
                request_id=request_id,
                agent_id=agent_id,
                old_state=current_state,
                requested_state=AgentLifecycleState.RESTRICTED,
                allowed=False,
                resulting_state=AgentLifecycleState.RESTRICTED,
                requires_evidence=True,
                blockers=(),
                warnings=("recommend_restricted:degraded_battery",),
                reason="Battery DEGRADED — recommend RESTRICTED",
            )

    # Source attestation invalid
    if source_attestation_valid is False:
        if current_state not in (AgentLifecycleState.SUSPENDED, AgentLifecycleState.REVOKED, AgentLifecycleState.RETIRED):
            recommended_state = AgentLifecycleState.SUSPENDED
            return AgentLifecycleTransitionDecision(
                decision_id=decision_id,
                request_id=request_id,
                agent_id=agent_id,
                old_state=current_state,
                requested_state=recommended_state,
                allowed=False,
                resulting_state=recommended_state,
                requires_evidence=True,
                blockers=("source_attestation_failed",),
                reason="Source attestation invalid — recommend SUSPENDED",
            )

    # Consent invalid
    if consent_valid is False:
        if current_state == AgentLifecycleState.ACTIVE:
            recommended_state = AgentLifecycleState.RESTRICTED
            return AgentLifecycleTransitionDecision(
                decision_id=decision_id,
                request_id=request_id,
                agent_id=agent_id,
                old_state=current_state,
                requested_state=recommended_state,
                allowed=False,
                resulting_state=recommended_state,
                blockers=("consent_invalid",),
                reason="Required consent invalid — recommend RESTRICTED",
            )

    # Claim boundary invalid
    if claim_boundary_valid is False:
        if current_state == AgentLifecycleState.ACTIVE:
            recommended_state = AgentLifecycleState.RESTRICTED
            return AgentLifecycleTransitionDecision(
                decision_id=decision_id,
                request_id=request_id,
                agent_id=agent_id,
                old_state=current_state,
                requested_state=recommended_state,
                allowed=False,
                resulting_state=recommended_state,
                blockers=("claim_boundary_violation",),
                reason="Claim boundary violation — recommend RESTRICTED",
            )

    # CANDIDATE + PASSED battery → recommend ACTIVE
    if current_state == AgentLifecycleState.CANDIDATE and battery_status == "PASSED":
        if not unresolved_authority_delta and consent_valid is not False:
            recommended_state = AgentLifecycleState.ACTIVE
            return AgentLifecycleTransitionDecision(
                decision_id=decision_id,
                request_id=request_id,
                agent_id=agent_id,
                old_state=current_state,
                requested_state=recommended_state,
                allowed=False,
                resulting_state=recommended_state,
                requires_evidence=True,
                requires_test_battery=True,
                warnings=("recommend_active:candidate_battery_passed",),
                reason="CANDIDATE with PASSED battery — recommend ACTIVE (requires evidence + test_battery refs)",
            )

    # No recommendation needed
    return AgentLifecycleTransitionDecision(
        decision_id=decision_id,
        request_id=request_id,
        agent_id=agent_id,
        old_state=current_state,
        requested_state=current_state,
        allowed=False,
        resulting_state=None,
        reason="No lifecycle state change recommended",
        warnings=("no_recommendation",),
    )


# ---------------------------------------------------------------------------
# Transition event creation
# ---------------------------------------------------------------------------


def create_lifecycle_transition_event(
    request: AgentLifecycleTransitionRequest,
    decision: AgentLifecycleTransitionDecision,
) -> AgentLifecycleTransitionEvent | None:
    """Create a transition event only if the decision is allowed.
    Does NOT mutate identity state.
    """
    if not decision.allowed or decision.resulting_state is None:
        return None

    event_id = "lte_" + hashlib.sha256(
        f"{decision.decision_id}:{request.agent_id}:{decision.resulting_state.value}".encode()
    ).hexdigest()[:20]

    return AgentLifecycleTransitionEvent(
        event_id=event_id,
        request_id=request.request_id,
        decision_id=decision.decision_id,
        agent_id=request.agent_id,
        old_state=request.old_state,
        new_state=decision.resulting_state,
        reason_code=request.reason_code,
        reason_text=request.reason_text,
        evidence_refs=request.evidence_refs,
        consent_refs=request.consent_refs,
        test_battery_refs=request.test_battery_refs,
        authority_delta_refs=request.authority_delta_refs,
        source_attestation_refs=request.source_attestation_refs,
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _enum_value(v: object) -> str:
    if isinstance(v, Enum):
        return v.value
    return str(v)


def agent_lifecycle_transition_request_to_dict(
    request: AgentLifecycleTransitionRequest,
) -> dict[str, object]:
    return {
        "request_id": request.request_id,
        "agent_id": request.agent_id,
        "old_state": request.old_state.value,
        "requested_state": request.requested_state.value,
        "reason_code": request.reason_code.value,
        "reason_text": request.reason_text,
        "requested_by": request.requested_by,
        "requested_at": request.requested_at,
        "evidence_refs": list(request.evidence_refs),
        "consent_refs": list(request.consent_refs),
        "test_battery_refs": list(request.test_battery_refs),
        "authority_delta_refs": list(request.authority_delta_refs),
        "source_attestation_refs": list(request.source_attestation_refs),
        "claim_decision_refs": list(request.claim_decision_refs),
    }


def agent_lifecycle_transition_decision_to_dict(
    decision: AgentLifecycleTransitionDecision,
) -> dict[str, object]:
    return {
        "decision_id": decision.decision_id,
        "request_id": decision.request_id,
        "agent_id": decision.agent_id,
        "old_state": decision.old_state.value,
        "requested_state": decision.requested_state.value,
        "allowed": decision.allowed,
        "resulting_state": decision.resulting_state.value if decision.resulting_state else None,
        "requires_evidence": decision.requires_evidence,
        "requires_consent": decision.requires_consent,
        "requires_test_battery": decision.requires_test_battery,
        "requires_operator_review": decision.requires_operator_review,
        "blockers": list(decision.blockers),
        "warnings": list(decision.warnings),
        "reason": decision.reason,
    }


def agent_lifecycle_transition_event_to_dict(
    event: AgentLifecycleTransitionEvent,
) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "request_id": event.request_id,
        "decision_id": event.decision_id,
        "agent_id": event.agent_id,
        "old_state": event.old_state.value,
        "new_state": event.new_state.value,
        "reason_code": event.reason_code.value,
        "reason_text": event.reason_text,
        "evidence_refs": list(event.evidence_refs),
        "consent_refs": list(event.consent_refs),
        "test_battery_refs": list(event.test_battery_refs),
        "authority_delta_refs": list(event.authority_delta_refs),
        "source_attestation_refs": list(event.source_attestation_refs),
        "created_at": event.created_at,
    }


def agent_lifecycle_eligibility_profile_to_dict(
    profile: AgentLifecycleEligibilityProfile,
) -> dict[str, object]:
    return {
        "agent_id": profile.agent_id,
        "lifecycle_state": profile.lifecycle_state.value,
        "eligible_lanes": [lane.value for lane in profile.eligible_lanes],
        "blocked_lanes": [lane.value for lane in profile.blocked_lanes],
        "required_gates": list(profile.required_gates),
        "restriction_reasons": [r.value for r in profile.restriction_reasons],
        "hard_blocked": profile.hard_blocked,
        "audit_only": profile.audit_only,
        "warnings": list(profile.warnings),
        "blockers": list(profile.blockers),
    }


def agent_lifecycle_policy_to_dict(policy: AgentLifecyclePolicy) -> dict[str, object]:
    return {
        "allowed_transitions": {
            k.value: [t.value for t in v]
            for k, v in policy.allowed_transitions.items()
        },
        "terminal_states": [s.value for s in policy.terminal_states],
        "active_requires_evidence": policy.active_requires_evidence,
        "active_requires_test_battery": policy.active_requires_test_battery,
        "restricted_requires_reason": policy.restricted_requires_reason,
        "revoked_is_terminal": policy.revoked_is_terminal,
    }


# ---------------------------------------------------------------------------
# Human-readable formatters
# ---------------------------------------------------------------------------


def format_lifecycle_decision_human(decision: AgentLifecycleTransitionDecision) -> str:
    lines = [
        f"Lifecycle Transition Decision: {'ALLOWED' if decision.allowed else 'BLOCKED'}",
        f"  Agent: {decision.agent_id}",
        f"  {decision.old_state.value} -> {decision.requested_state.value}",
        f"  Resulting state: {decision.resulting_state.value if decision.resulting_state else 'N/A'}",
        f"  Reason: {decision.reason}",
    ]
    if decision.requires_evidence:
        lines.append("  Requires evidence: yes")
    if decision.requires_consent:
        lines.append("  Requires consent: yes")
    if decision.requires_test_battery:
        lines.append("  Requires test battery: yes")
    if decision.requires_operator_review:
        lines.append("  Requires operator review: yes")
    if decision.blockers:
        lines.append("  Blockers:")
        for b in decision.blockers:
            lines.append(f"    - {b}")
    if decision.warnings:
        lines.append("  Warnings:")
        for w in decision.warnings:
            lines.append(f"    - {w}")
    return "\n".join(lines)


def format_lifecycle_profile_human(profile: AgentLifecycleEligibilityProfile) -> str:
    lines = [
        f"Lifecycle Eligibility Profile: {profile.agent_id}",
        f"  State: {profile.lifecycle_state.value}",
        f"  Audit only: {profile.audit_only}",
        f"  Hard blocked: {profile.hard_blocked}",
        "",
        "  Eligible lanes:",
    ]
    for lane in profile.eligible_lanes:
        lines.append(f"    - {lane.value}")
    lines.append("  Blocked lanes:")
    for lane in profile.blocked_lanes:
        lines.append(f"    - {lane.value}")
    lines.append("  Required gates:")
    for gate in profile.required_gates:
        lines.append(f"    - {gate}")
    if profile.restriction_reasons:
        lines.append("  Restriction reasons:")
        for r in profile.restriction_reasons:
            lines.append(f"    - {r.value}")
    if profile.blockers:
        lines.append("  Blockers:")
        for b in profile.blockers:
            lines.append(f"    - {b}")
    if profile.warnings:
        lines.append("  Warnings:")
        for w in profile.warnings:
            lines.append(f"    - {w}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "AgentLifecycleState",
    "LifecycleReasonCode",
    "LifecycleLane",
    "AgentLifecycleTransitionRequest",
    "AgentLifecycleTransitionDecision",
    "AgentLifecycleTransitionEvent",
    "AgentLifecyclePolicy",
    "AgentLifecycleEligibilityProfile",
    "default_agent_lifecycle_policy",
    "validate_agent_lifecycle_transition",
    "build_agent_lifecycle_eligibility_profile",
    "recommend_lifecycle_state",
    "create_lifecycle_transition_event",
    "agent_lifecycle_transition_request_to_dict",
    "agent_lifecycle_transition_decision_to_dict",
    "agent_lifecycle_transition_event_to_dict",
    "agent_lifecycle_eligibility_profile_to_dict",
    "agent_lifecycle_policy_to_dict",
    "format_lifecycle_decision_human",
    "format_lifecycle_profile_human",
]
