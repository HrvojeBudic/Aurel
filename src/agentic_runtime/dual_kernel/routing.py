"""routing.py — measured autonomy → execution path.

Static, pre-execution scoring from artefacts the runtime already has (AgentCard,
AuthorityScope). Implements the code-inspection Autonomy Index (Cihon/Stein,
*Measuring AI Agent Autonomy*) fused with an identity-confidence gate (Otsuka
et al., *AI Identity*) and Σ's live risk signals.

    route = f(autonomy_index, Σ, identity_confidence)

Nothing here executes; it only decides which of three governed paths a step
takes. Every path still ends at the merge gate — FAST just verifies async.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from ..core_types import AgentCard, CommandEnvelope, RiskLevel
from ..policy import PolicyDecision

if TYPE_CHECKING:  # pragma: no cover
    from .sigma import GovernanceStateVector

# Autonomy-driving tool classes (code-inspection proxy for "Actions" axis).
_EXEC_TOOLS = frozenset({"run_tests", "run_shell", "network_fetch", "delete_file"})
_WRITE_TOOLS = frozenset({
    "write_file", "edit_file", "patch_file", "mutate_protected_verification",
})

_HIGH_RISK = frozenset({RiskLevel.HIGH, RiskLevel.CRITICAL})
_LOW_RISK = frozenset({RiskLevel.TRIVIAL, RiskLevel.LOW})

# Below this Declaration↔Observation correspondence, demote before a violation.
CONFIDENCE_FLOOR = 0.60
CONFIDENCE_HARD_FLOOR = 0.30


class Route(str, Enum):
    """The three governed execution paths."""

    FAST = "fast"            # index 0–3: optimistic + async post-verify + rollback
    GOVERNED = "governed"    # index 4–7: full fork → barrier → merge, inline verify
    HARD_GATED = "hard"      # index 8–10 or hard trigger: full chain + mandatory HITL


@dataclass
class AdmitDecision:
    route: Route
    autonomy_index: int
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)


def _actions_score(card: AgentCard) -> int:
    tools = set(card.allowed_tools)
    if tools & _EXEC_TOOLS:
        return 2
    if tools & _WRITE_TOOLS:
        return 1
    return 0


def _environment_score(card: AgentCard) -> int:
    auth = card.authority
    if auth.allow_network or auth.allow_secrets:
        return 2
    broad = any(p in ("*", "/", "") for p in auth.write_paths)
    return 1 if broad else 0


def _orchestration_score(card: AgentCard) -> int:
    n = len(card.escalation_policy)
    if n >= 2:
        return 2
    return 1 if n == 1 else 0


def _hitl_score(card: AgentCard) -> int:
    mr = card.authority.max_risk
    if mr in _HIGH_RISK:
        return 2
    if mr is RiskLevel.MEDIUM:
        return 1
    return 0


def _observability_score(card: AgentCard) -> int:
    # Trace is always-on and persistent in this runtime → fully observed.
    return 0


def autonomy_index(card: AgentCard) -> int:
    """0–10 static autonomy score. Higher = less freedom without governance."""
    return (
        _actions_score(card)
        + _environment_score(card)
        + _orchestration_score(card)
        + _hitl_score(card)
        + _observability_score(card)
    )


def route_for(
    *,
    index: int,
    sigma: "GovernanceStateVector",
    cmd: CommandEnvelope,
    decision: PolicyDecision,
    identity_confidence: float = 1.0,
    over_budget: bool = False,
) -> AdmitDecision:
    """Pick the execution path. Hard triggers always win over the index."""
    reasons: list[str] = [f"autonomy_index={index}"]

    # --- hard triggers: force the full chain regardless of index ------------ #
    if identity_confidence < CONFIDENCE_HARD_FLOOR:
        reasons.append("identity_confidence below hard floor")
        return AdmitDecision(Route.HARD_GATED, index, blocked=True, reasons=reasons)

    hard = False
    if index >= 8:
        hard = True
        reasons.append("index in hard-gated band (8–10)")
    if decision.risk in _HIGH_RISK and not sigma.approval_occurred:
        hard = True
        reasons.append("high-risk step without prior approval")
    if identity_confidence < CONFIDENCE_FLOOR:
        hard = True
        reasons.append("identity_confidence below floor")
    if over_budget:
        hard = True
        reasons.append("risk budget exhausted")
    if sigma.crosses_barrier(cmd):
        hard = True
        reasons.append("step crosses an information barrier")
    if hard:
        return AdmitDecision(Route.HARD_GATED, index, reasons=reasons)

    # --- fast path: reversible, low-consequence, well-scoped ---------------- #
    reversible = (
        index <= 3
        and decision.risk in _LOW_RISK
        and cmd.tool not in _EXEC_TOOLS
        and not sigma.net_or_secrets_used
    )
    if reversible:
        reasons.append("fast: reversible low-risk within scope")
        return AdmitDecision(Route.FAST, index, reasons=reasons)

    reasons.append("governed: standard fork → merge")
    return AdmitDecision(Route.GOVERNED, index, reasons=reasons)
