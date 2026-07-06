"""sigma.py — the O(1) governance state-vector Σ.

Replaces "re-scan the whole path on every step" (Kaptein, *Runtime Governance:
Policies on Paths*) with a compact, monotone sufficient statistic. Updating Σ is
O(1) and — for the class of path policies used here — provably equivalent to
re-deriving over the full step history.

Two-phase split (§4.2):
  - ``register_task`` runs identity-only policy ONCE at task start.
  - ``admit_step`` reads Σ (never the raw path) and routes each step.

Σ is monotone: no field ever weakens across a task, so an admitted-cheap prefix
can never retroactively hide a later high-consequence step.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from ..core_types import AgentCard, CommandEnvelope, Intent, RiskLevel
from ..policy import PolicyDecision
from . import routing

if TYPE_CHECKING:  # pragma: no cover
    pass

_RISK_RANK: dict[RiskLevel, int] = {
    RiskLevel.TRIVIAL: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}

_WRITE_TOOLS = frozenset({
    "write_file", "edit_file", "patch_file", "delete_file",
    "mutate_protected_verification",
})
_NET_TOOLS = frozenset({"network_fetch"})


def _rank(risk: RiskLevel) -> int:
    return _RISK_RANK.get(risk, 0)


def _max_risk(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    return a if _rank(a) >= _rank(b) else b


def _writes_of(cmd: CommandEnvelope) -> tuple[str, ...]:
    if cmd.tool not in _WRITE_TOOLS:
        return ()
    path = cmd.args.get("path")
    return (str(path),) if path else ()


def _touches_net_or_secrets(cmd: CommandEnvelope) -> bool:
    if cmd.tool in _NET_TOOLS:
        return True
    return bool(cmd.args.get("use_secrets") or cmd.args.get("secret"))


def _barriers_of(cmd: CommandEnvelope) -> frozenset[str]:
    """Top-level path segment of any touched path — an information-barrier tag.

    Barrier policies (Kaptein) fire when one side of a named barrier was touched
    earlier and the other side is touched now; tracking touched top-level
    compartments in Σ is the compact sufficient statistic that check needs.
    """
    tags: set[str] = set()
    for key in ("path", "src", "dst", "url"):
        val = cmd.args.get(key)
        if not val:
            continue
        seg = str(val).replace("\\", "/").lstrip("/").split("/", 1)[0]
        if seg:
            tags.add(seg)
    return frozenset(tags)


@dataclass(frozen=True)
class GovernanceStateVector:
    """Compact O(1) sufficient statistic for path governance."""

    task_id: str
    authority_card_id: str
    max_sensitivity: RiskLevel = RiskLevel.TRIVIAL
    barrier_tags: frozenset[str] = field(default_factory=frozenset)
    approval_occurred: bool = False
    step_count: int = 0
    risk_budget_spent: float = 0.0
    write_paths_touched: tuple[str, ...] = ()
    net_or_secrets_used: bool = False

    def update(
        self,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        *,
        step_cost: float = 0.0,
        approved: bool = False,
    ) -> "GovernanceStateVector":
        """Fold one step into Σ. O(1), monotone (no field ever weakens)."""
        return replace(
            self,
            step_count=self.step_count + 1,
            max_sensitivity=_max_risk(self.max_sensitivity, decision.risk),
            barrier_tags=self.barrier_tags | _barriers_of(cmd),
            approval_occurred=self.approval_occurred or approved,
            risk_budget_spent=self.risk_budget_spent + max(0.0, step_cost),
            write_paths_touched=self.write_paths_touched + _writes_of(cmd),
            net_or_secrets_used=self.net_or_secrets_used
            or _touches_net_or_secrets(cmd),
        )

    def crosses_barrier(self, cmd: CommandEnvelope) -> bool:
        """True if this step touches a compartment other than any already touched.

        Degenerate on an empty Σ (first step establishes the compartment).
        """
        if not self.barrier_tags:
            return False
        return bool(_barriers_of(cmd) - self.barrier_tags)


@dataclass
class SigmaGovernor:
    """Owns Σ for a task and routes each step. Custos control-plane entry point."""

    risk_budget: float = float("inf")

    def register_task(self, card: AgentCard, intent: Intent) -> GovernanceStateVector:
        """Phase 1 — identity-only, runs ONCE. Depends on A, never on the path."""
        return GovernanceStateVector(
            task_id=intent.id,
            authority_card_id=card.id,
        )

    def admit_step(
        self,
        sigma: GovernanceStateVector,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        card: AgentCard,
        *,
        identity_confidence: float = 1.0,
    ) -> "routing.AdmitDecision":
        """Phase 2 — per-step. Reads Σ (not the raw path) and picks a route."""
        idx = routing.autonomy_index(card)
        over_budget = sigma.risk_budget_spent > self.risk_budget
        return routing.route_for(
            index=idx,
            sigma=sigma,
            cmd=cmd,
            decision=decision,
            identity_confidence=identity_confidence,
            over_budget=over_budget,
        )
