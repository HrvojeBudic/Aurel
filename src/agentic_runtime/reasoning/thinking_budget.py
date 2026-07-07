"""thinking_budget.py — per-entity reasoning budget (Track B, B1).

Deny-by-default reasoning envelope: an effort ceiling, allowed model-profile
tiers, and hard pass/token/call limits. ``clamp`` provably never returns an
effort above the ceiling; unknown / missing effort collapses to REFLEX.

Resolved from an AgentCard's class + authority (no AgentCard field is added, so
existing card serialization stays byte-identical). Proposal-only: a budget
shapes what may be *requested*; PlanValidator and runtime.submit remain the sole
gates. Allocation ≠ authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..core_types import AgentClass, RiskLevel


class EffortLevel(str, Enum):
    REFLEX = "reflex"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_EFFORT_RANK: dict[EffortLevel, int] = {
    EffortLevel.REFLEX: 0, EffortLevel.LOW: 1,
    EffortLevel.MEDIUM: 2, EffortLevel.HIGH: 3,
}
_HIGH_RISK = frozenset({RiskLevel.HIGH, RiskLevel.CRITICAL})


@dataclass(frozen=True)
class ThinkingBudget:
    effort_ceiling: EffortLevel = EffortLevel.LOW
    allowed_profile_tiers: tuple[str, ...] = ("balanced",)
    max_passes: int = 2
    max_thinking_tokens: int = 20_000
    max_thinking_calls: int = 8

    def clamp(self, requested: Optional[EffortLevel]) -> EffortLevel:
        """Deny-by-default: unknown/None → REFLEX; else min(requested, ceiling).
        The result is provably ≤ ``effort_ceiling``."""
        rank = _EFFORT_RANK.get(requested) if requested is not None else None
        if rank is None:
            return EffortLevel.REFLEX
        return requested if rank <= _EFFORT_RANK[self.effort_ceiling] else self.effort_ceiling

    def allows_profile(self, tier: str) -> bool:
        return tier in self.allowed_profile_tiers


_CONSERVATIVE = ThinkingBudget()  # LOW ceiling, minimal passes — the safe floor


def for_card(card: Any) -> ThinkingBudget:
    """Conservative per-class default. Never unlimited; missing → conservative."""
    cls = getattr(card, "agent_class", None)
    max_risk = getattr(getattr(card, "authority", None), "max_risk", RiskLevel.LOW)
    if cls in (AgentClass.CORE, AgentClass.EXECUTION):
        ceiling = EffortLevel.HIGH if max_risk in _HIGH_RISK else EffortLevel.MEDIUM
        return ThinkingBudget(effort_ceiling=ceiling, max_passes=3,
                              allowed_profile_tiers=("balanced", "deep"))
    if cls in (AgentClass.RESEARCH, AgentClass.CRITIC):
        return ThinkingBudget(effort_ceiling=EffortLevel.MEDIUM)
    # MEMORY, POLICY, or unknown class → most conservative floor
    return _CONSERVATIVE
