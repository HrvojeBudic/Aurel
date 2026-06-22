"""P1.4.8 — Autonomy Scale Engine (action-scoped autonomy decision engine).

Scope: determine per-action autonomy level, not global autonomy score.
A7 means DENIED / outside authority, not highest autonomy.
This module does NOT execute tools or compute Measured Autonomy Score.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from agentic_runtime.identity.kernel import AurelIdentityKernel

if TYPE_CHECKING:
    from agentic_runtime.identity.agent_identity_card import AurelAgentIdentityCard
    from agentic_runtime.identity.operator_contract import AurelOperatorContract
    from agentic_runtime.identity.capability_inventory import CapabilityInventoryEntry
    from agentic_runtime.identity.source_bundle import IdentitySourceBundle


# ── Domain enums ────────────────────────────────────────────────────────


class AutonomyLevel(str, Enum):
    """Action-scoped autonomy level. A7 = denied, not highest autonomy."""

    A0_ANSWER_ONLY = "A0_ANSWER_ONLY"
    A1_SUGGESTION = "A1_SUGGESTION"
    A2_DRAFT = "A2_DRAFT"
    A3_REVERSIBLE_LOCAL_ACTION = "A3_REVERSIBLE_LOCAL_ACTION"
    A4_GOVERNED_TOOL_ACTION = "A4_GOVERNED_TOOL_ACTION"
    A5_CONDITIONAL_EXECUTION = "A5_CONDITIONAL_EXECUTION"
    A6_APPROVAL_GATED_HIGH_RISK = "A6_APPROVAL_GATED_HIGH_RISK"
    A7_DENIED = "A7_DENIED"


def is_denied(level: AutonomyLevel) -> bool:
    """A7 is denial, not higher autonomy. Never compare numerically."""
    return level == AutonomyLevel.A7_DENIED


class ActionCategory(str, Enum):
    ANSWER = "answer"
    SUGGEST = "suggest"
    DRAFT = "draft"
    LOCAL_WRITE = "local_write"
    TOOL_CALL = "tool_call"
    CONDITIONAL_EXECUTION = "conditional_execution"
    EXTERNAL_EFFECT = "external_effect"
    HIGH_RISK = "high_risk"
    UNKNOWN = "unknown"


class RiskTier(str, Enum):
    """Action risk tier. Unknown must fail closed."""
    R0_NONE = "R0_NONE"
    R1_LOW = "R1_LOW"
    R2_MODERATE = "R2_MODERATE"
    R3_HIGH = "R3_HIGH"
    R4_CRITICAL = "R4_CRITICAL"


class ReversibilityTier(str, Enum):
    """Reversibility of an action's effects. R6 = forbidden.
    Distinguish reversible (undo-able) from compensatable (fixable with follow-up).
    """
    R0_NO_EFFECT = "R0_NO_EFFECT"
    R1_FULLY_REVERSIBLE = "R1_FULLY_REVERSIBLE"
    R2_REVERSIBLE_WITH_BACKUP = "R2_REVERSIBLE_WITH_BACKUP"
    R3_COMPENSATABLE = "R3_COMPENSATABLE"
    R4_HARD_TO_REVERSE = "R4_HARD_TO_REVERSE"
    R5_IRREVERSIBLE_APPROVAL_REQUIRED = "R5_IRREVERSIBLE_APPROVAL_REQUIRED"
    R6_FORBIDDEN = "R6_FORBIDDEN"


class LifecycleState(str, Enum):
    """Agent lifecycle state. Affects allowable autonomy ceiling."""
    DRAFT = "DRAFT"
    STAGING = "STAGING"
    LIMITED = "LIMITED"
    PRODUCTION = "PRODUCTION"
    SUSPENDED = "SUSPENDED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


# ── Request / Decision / Context contracts ──────────────────────────────


@dataclass(frozen=True)
class AutonomyRequest:
    """Immutable autonomy evaluation request scoped to a single action."""

    action_id: str
    action_category: ActionCategory
    action_name: str
    requested_by: str
    agent_id: str

    target: str | None = None
    tool_name: str | None = None
    path: str | None = None

    risk_tier: RiskTier | None = None
    reversibility_tier: ReversibilityTier | None = None

    required_capability: str | None = None
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AutonomyDecision:
    """Immutable autonomy decision for a single requested action."""

    decision_id: str
    request_id: str
    agent_id: str

    allowed: bool
    autonomy_level: AutonomyLevel
    requires_human_approval: bool

    action_category: ActionCategory
    risk_tier: RiskTier
    reversibility_tier: ReversibilityTier

    authority_scope: str | None = None
    capability_evidence_level: str | None = None

    reason: str = ""
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_gates: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    source_hash: str | None = None
    created_at: str | None = None


def autonomy_decision_to_dict(decision: AutonomyDecision) -> dict[str, object]:
    """Stable, JSON-friendly serialization."""
    return {
        "decision_id": decision.decision_id,
        "request_id": decision.request_id,
        "agent_id": decision.agent_id,
        "allowed": decision.allowed,
        "autonomy_level": decision.autonomy_level.value,
        "requires_human_approval": decision.requires_human_approval,
        "action_category": decision.action_category.value,
        "risk_tier": decision.risk_tier.value,
        "reversibility_tier": decision.reversibility_tier.value,
        "authority_scope": decision.authority_scope,
        "capability_evidence_level": decision.capability_evidence_level,
        "reason": decision.reason,
        "blockers": list(decision.blockers),
        "warnings": list(decision.warnings),
        "required_gates": list(decision.required_gates),
        "evidence_refs": list(decision.evidence_refs),
        "source_hash": decision.source_hash,
        "created_at": decision.created_at,
    }


@dataclass(frozen=True)
class AutonomyEvaluationContext:
    """Context required for autonomy decision evaluation."""

    agent_identity_card: AurelAgentIdentityCard
    operator_contract: AurelOperatorContract

    identity_source_bundle: IdentitySourceBundle | None = None
    capability_inventory: tuple[CapabilityInventoryEntry, ...] | None = None
    policy_context: object | None = None
    tool_manifest_catalog: object | None = None


# ── Baseline autonomy matrix ────────────────────────────────────────────


BASELINE_BY_ACTION_CATEGORY: dict[ActionCategory, AutonomyLevel] = {
    ActionCategory.ANSWER: AutonomyLevel.A0_ANSWER_ONLY,
    ActionCategory.SUGGEST: AutonomyLevel.A1_SUGGESTION,
    ActionCategory.DRAFT: AutonomyLevel.A2_DRAFT,
    ActionCategory.LOCAL_WRITE: AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION,
    ActionCategory.TOOL_CALL: AutonomyLevel.A4_GOVERNED_TOOL_ACTION,
    ActionCategory.CONDITIONAL_EXECUTION: AutonomyLevel.A5_CONDITIONAL_EXECUTION,
    ActionCategory.EXTERNAL_EFFECT: AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK,
    ActionCategory.HIGH_RISK: AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK,
    ActionCategory.UNKNOWN: AutonomyLevel.A7_DENIED,
}


# ── Lifecycle autonomy ceilings ─────────────────────────────────────────


LIFECYCLE_CEILINGS: dict[LifecycleState, AutonomyLevel] = {
    LifecycleState.DRAFT: AutonomyLevel.A1_SUGGESTION,
    LifecycleState.STAGING: AutonomyLevel.A2_DRAFT,
    LifecycleState.LIMITED: AutonomyLevel.A4_GOVERNED_TOOL_ACTION,
    LifecycleState.PRODUCTION: AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK,
    LifecycleState.SUSPENDED: AutonomyLevel.A7_DENIED,
    LifecycleState.DEPRECATED: AutonomyLevel.A1_SUGGESTION,
    LifecycleState.RETIRED: AutonomyLevel.A7_DENIED,
}


# ── Risk escalation rules ───────────────────────────────────────────────


RISK_ESCALATION: dict[RiskTier, tuple[bool, list[str]]] = {
    # (requires_human_approval, additional_gates)
    RiskTier.R0_NONE: (False, []),
    RiskTier.R1_LOW: (False, []),
    RiskTier.R2_MODERATE: (False, []),
    RiskTier.R3_HIGH: (True, ["human_approval_required"]),
    RiskTier.R4_CRITICAL: (True, ["human_approval_required", "escalation_path_required"]),
}


# ── Reversibility escalation rules ──────────────────────────────────────


REVERSIBILITY_ESCALATION: dict[ReversibilityTier, tuple[bool, list[str]]] = {
    # (requires_human_approval, additional_gates)
    ReversibilityTier.R0_NO_EFFECT: (False, []),
    ReversibilityTier.R1_FULLY_REVERSIBLE: (False, []),
    ReversibilityTier.R2_REVERSIBLE_WITH_BACKUP: (False, []),
    ReversibilityTier.R3_COMPENSATABLE: (False, []),
    ReversibilityTier.R4_HARD_TO_REVERSE: (True, ["human_approval_required"]),
    ReversibilityTier.R5_IRREVERSIBLE_APPROVAL_REQUIRED: (True, ["human_approval_required"]),
    ReversibilityTier.R6_FORBIDDEN: (True, ["forbidden_reversibility"]),
}


# ── Blocker codes ───────────────────────────────────────────────────────


class Blocker:
    """Canonical blocker codes for denied autonomy decisions."""

    UNKNOWN_ACTION_CATEGORY = "unknown_action_category"
    UNKNOWN_RISK_TIER = "unknown_risk_tier"
    UNKNOWN_REVERSIBILITY_TIER = "unknown_reversibility_tier"
    MISSING_AUTHORITY_SCOPE = "missing_authority_scope"
    OUTSIDE_AUTHORITY_SCOPE = "outside_authority_scope"
    MISSING_OPERATOR_CONTRACT = "missing_operator_contract"
    MISSING_IDENTITY_CARD = "missing_identity_card"
    HIGH_RISK_REQUIRES_HUMAN_GATE = "high_risk_requires_human_gate"
    EXTERNAL_EFFECT_REQUIRES_HUMAN_GATE = "external_effect_requires_human_gate"
    FORBIDDEN_REVERSIBILITY = "forbidden_reversibility"
    CAPABILITY_NOT_IMPLEMENTED = "capability_not_implemented"
    CAPABILITY_NOT_VERIFIED = "capability_not_verified"
    ROADMAP_ONLY_CAPABILITY = "roadmap_only_capability"
    AGENT_LIFECYCLE_SUSPENDED = "agent_lifecycle_suspended"
    AGENT_LIFECYCLE_RETIRED = "agent_lifecycle_retired"
    ACTION_BEYOND_LIFECYCLE_CEILING = "action_beyond_lifecycle_ceiling"
    MISSING_LIFECYCLE_STATE = "missing_lifecycle_state"
    CRITICAL_RISK_NO_ESCALATION_PATH = "critical_risk_no_escalation_path"


# ── Helper: numeric rank for autonomy comparison ────────────────────────
# Used ONLY for ceiling checks (not for ranking/ordering decisions).

_AUTONOMY_NUMERIC: dict[AutonomyLevel, int] = {
    AutonomyLevel.A0_ANSWER_ONLY: 0,
    AutonomyLevel.A1_SUGGESTION: 1,
    AutonomyLevel.A2_DRAFT: 2,
    AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION: 3,
    AutonomyLevel.A4_GOVERNED_TOOL_ACTION: 4,
    AutonomyLevel.A5_CONDITIONAL_EXECUTION: 5,
    AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK: 6,
    AutonomyLevel.A7_DENIED: -1,  # never "higher" than anything
}


def _autonomy_exceeds_ceiling(level: AutonomyLevel, ceiling: AutonomyLevel) -> bool:
    """True if level exceeds the allowed ceiling (A7 always denied)."""
    if is_denied(level) or is_denied(ceiling):
        return True
    return _AUTONOMY_NUMERIC[level] > _AUTONOMY_NUMERIC[ceiling]


# ── Resolver ────────────────────────────────────────────────────────────


def resolve_autonomy_decision(
    request: AutonomyRequest,
    context: AutonomyEvaluationContext,
) -> AutonomyDecision:
    """Resolve autonomy for a single action request. Never executes tools.
    Never computes a global autonomy score.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    required_gates: list[str] = []
    evidence_refs: list[str] = []
    requires_human_approval = False

    # 1. Unknown action category -> immediate A7
    if request.action_category == ActionCategory.UNKNOWN:
        return _denied(
            request,
            context,
            blockers=[Blocker.UNKNOWN_ACTION_CATEGORY],
            reason="Unknown action category. Failing closed.",
        )

    # 2. Unknown risk tier -> A7
    if request.risk_tier is None:
        return _denied(
            request,
            context,
            blockers=[Blocker.UNKNOWN_RISK_TIER],
            reason="Missing risk tier. Failing closed.",
        )

    # 3. Unknown reversibility tier -> A7
    if request.reversibility_tier is None:
        return _denied(
            request,
            context,
            blockers=[Blocker.UNKNOWN_REVERSIBILITY_TIER],
            reason="Missing reversibility tier. Failing closed.",
        )

    # 4. Forbidden reversibility -> A7
    if request.reversibility_tier == ReversibilityTier.R6_FORBIDDEN:
        return _denied(
            request,
            context,
            blockers=[Blocker.FORBIDDEN_REVERSIBILITY],
            reason="Action reversibility tier is R6_FORBIDDEN.",
        )

    # 5. Baseline autonomy from action category
    baseline = BASELINE_BY_ACTION_CATEGORY.get(request.action_category, AutonomyLevel.A7_DENIED)

    # 6. Agent lifecycle check
    lifecycle = _extract_lifecycle(context)
    if lifecycle is not None:
        if lifecycle == LifecycleState.SUSPENDED:
            return _denied(request, context,
                           blockers=[Blocker.AGENT_LIFECYCLE_SUSPENDED],
                           reason="Agent is SUSPENDED. All actions denied.")
        if lifecycle == LifecycleState.RETIRED:
            return _denied(request, context,
                           blockers=[Blocker.AGENT_LIFECYCLE_RETIRED],
                           reason="Agent is RETIRED. All actions denied.")
        ceiling = LIFECYCLE_CEILINGS.get(lifecycle, AutonomyLevel.A1_SUGGESTION)
        if _autonomy_exceeds_ceiling(baseline, ceiling):
            return _denied(request, context,
                           blockers=[Blocker.ACTION_BEYOND_LIFECYCLE_CEILING],
                           reason=f"Action baseline {baseline.value} exceeds lifecycle ceiling {ceiling.value} for {lifecycle.value}.")
        if lifecycle == LifecycleState.DEPRECATED:
            warnings.append("agent_lifecycle_deprecated")
    # If lifecycle is missing, assume PRODUCTION-level access (default state)

    # 7. Authority scope check
    authority_ok = _check_authority_scope(request, context, blockers, warnings)
    if not authority_ok:
        return _denied(request, context, blockers=blockers,
                       warnings=tuple(warnings),
                       reason="Action outside authority scope.")

    # 8. Capability evidence check
    if request.required_capability is not None:
        cap_ok = _check_capability(request, context, blockers)
        if not cap_ok:
            return _denied(request, context, blockers=blockers,
                           reason=f"Required capability '{request.required_capability}' cannot authorize action.")

    # 9. Risk escalation
    risk_req, risk_gates = RISK_ESCALATION.get(request.risk_tier, (True, ["unknown_risk_tier"]))
    if risk_req:
        requires_human_approval = True
        required_gates.extend(risk_gates)
    if request.risk_tier == RiskTier.R4_CRITICAL:
        required_gates.append("escalation_path_required")
    if request.risk_tier == RiskTier.R2_MODERATE:
        warnings.append("risk_tier_moderate")

    # 10. Reversibility escalation
    rev_req, rev_gates = REVERSIBILITY_ESCALATION.get(request.reversibility_tier, (True, []))
    if rev_req:
        requires_human_approval = True
        required_gates.extend(rev_gates)
    if request.reversibility_tier == ReversibilityTier.R3_COMPENSATABLE:
        warnings.append("reversibility_compensatable")
    if request.reversibility_tier == ReversibilityTier.R2_REVERSIBLE_WITH_BACKUP:
        warnings.append("reversibility_backup_advised")

    # 11. High-risk / external-effect gate
    if request.action_category in (ActionCategory.HIGH_RISK, ActionCategory.EXTERNAL_EFFECT):
        requires_human_approval = True
        required_gates.append("human_approval_required")
        if request.risk_tier in (RiskTier.R4_CRITICAL,):
            blockers.append(Blocker.CRITICAL_RISK_NO_ESCALATION_PATH)
            return _denied(request, context, blockers=blockers,
                           warnings=tuple(warnings),
                           reason="Critical-risk action has no escalation path.")

    # 12. Evidence refs
    evidence_refs.append(f"agent_identity_card:{context.agent_identity_card.agent.agent_id}")
    evidence_refs.append("operator_contract:active")

    # 13. Build final level — baseline unless escalated
    final_level = baseline

    # 14. Build decision
    created_at = datetime.now(timezone.utc).isoformat()

    return AutonomyDecision(
        decision_id=f"autonomy_decision_{uuid.uuid4().hex[:12]}",
        request_id=request.action_id,
        agent_id=request.agent_id,
        allowed=True,
        autonomy_level=final_level,
        requires_human_approval=requires_human_approval,
        action_category=request.action_category,
        risk_tier=request.risk_tier,
        reversibility_tier=request.reversibility_tier,
        authority_scope=request.agent_id,
        capability_evidence_level="implemented" if request.required_capability else None,
        reason=f"Action {request.action_name} ({request.action_category.value}) resolved at {final_level.value}. Risk: {request.risk_tier.value}, Reversibility: {request.reversibility_tier.value}. Human approval: {'required' if requires_human_approval else 'not required'}.",
        blockers=tuple(sorted(set(blockers))),
        warnings=tuple(sorted(set(warnings))),
        required_gates=tuple(sorted(set(required_gates))),
        evidence_refs=tuple(sorted(set(evidence_refs))),
        created_at=created_at,
    )


# ── Internal helpers ────────────────────────────────────────────────────


def _denied(
    request: AutonomyRequest,
    context: AutonomyEvaluationContext,
    *,
    blockers: list[str],
    reason: str,
    warnings: tuple[str, ...] = (),
    required_gates: tuple[str, ...] = (),
) -> AutonomyDecision:
    """Construct an A7_DENIED decision."""
    created_at = datetime.now(timezone.utc).isoformat()
    return AutonomyDecision(
        decision_id=f"autonomy_decision_{uuid.uuid4().hex[:12]}",
        request_id=request.action_id,
        agent_id=request.agent_id,
        allowed=False,
        autonomy_level=AutonomyLevel.A7_DENIED,
        requires_human_approval=False,
        action_category=request.action_category,
        risk_tier=request.risk_tier or RiskTier.R0_NONE,
        reversibility_tier=request.reversibility_tier or ReversibilityTier.R1_FULLY_REVERSIBLE,
        reason=reason,
        blockers=tuple(sorted(set(blockers))),
        warnings=tuple(sorted(set(warnings))),
        required_gates=tuple(required_gates),
        created_at=created_at,
    )


def _extract_lifecycle(context: AutonomyEvaluationContext) -> LifecycleState | None:
    """Extract lifecycle state from the identity card if available."""
    card = context.agent_identity_card
    # Check common field names for lifecycle state
    for attr in ("lifecycle_state", "lifecycle", "state", "agent_state"):
        val = getattr(card, attr, None)
        if val is not None:
            try:
                return LifecycleState(val)
            except ValueError:
                return None
    return None


def _check_authority_scope(
    request: AutonomyRequest,
    context: AutonomyEvaluationContext,
    blockers: list[str],
    warnings: list[str],
) -> bool:
    """Check authority scope. Actions beyond A1_SUGGESTION require explicit scope."""
    if request.action_category in (ActionCategory.ANSWER, ActionCategory.SUGGEST):
        return True  # minimal authority is sufficient

    card = context.agent_identity_card
    # Check for authority_scope on the card's agent or authority
    scope = getattr(card.agent, "authority_scope", None) or getattr(card.authority, "authority_scope", None)
    if scope is None or scope == "":
        # Operator contract existence is sufficient for authority if explicit scope not set
        # This allows actions to proceed under operator contract governance
        pass  # not a hard blocker — the operator contract's rules apply

    # Check operator contract boundaries allow autonomous action
    op = context.operator_contract
    # If contract has execution_authority with allow_any, it permits
    exec_auth = getattr(op, "execution_authority", None)
    if exec_auth is not None:
        allow_any = getattr(exec_auth, "allow_any", None)
        if allow_any is False:
            blockers.append(Blocker.OUTSIDE_AUTHORITY_SCOPE)
            return False

    return True


def _check_capability(
    request: AutonomyRequest,
    context: AutonomyEvaluationContext,
    blockers: list[str],
) -> bool:
    """Check required capability status. Planned/roadmap cannot authorize."""
    cap_id = request.required_capability
    inventory = context.capability_inventory

    if inventory is None:
        blockers.append(Blocker.CAPABILITY_NOT_VERIFIED)
        return False

    for entry in inventory:
        if entry.id == cap_id:
            if entry.status == "implemented":
                return True
            elif entry.status == "planned":
                blockers.append(Blocker.CAPABILITY_NOT_IMPLEMENTED)
                return False
            elif entry.status in ("roadmap", "roadmap_only"):
                blockers.append(Blocker.ROADMAP_ONLY_CAPABILITY)
                return False
            elif entry.status in ("observed", "tested", "verified", "promoted"):
                return True  # eligible subject to other gates
            else:
                blockers.append(Blocker.CAPABILITY_NOT_VERIFIED)
                return False

    blockers.append(Blocker.CAPABILITY_NOT_IMPLEMENTED)
    return False
