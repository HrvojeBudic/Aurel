"""reasoning_scheduler.py — adaptive System-1/System-2 allocation (Track B, B3).

Maps a task's difficulty (B2) through the entity's thinking budget (B1) to a
clamped effort and a model profile, fail-closed. Proposal-only: it shapes only
what is *requested* — PlanValidator and runtime.submit remain the sole gates,
and a blocked/absent selection never silently upgrades effort.

Bound into entity.plan behind AUREL_REASONING_SCHEDULER (default off ⇒ the
planning path is byte-identical to today).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from .difficulty_estimator import DifficultyBand, estimate
from .thinking_budget import EffortLevel, for_card

_FLAG = "AUREL_REASONING_SCHEDULER"

_EFFORT_FOR_BAND: dict[DifficultyBand, EffortLevel] = {
    DifficultyBand.TRIVIAL: EffortLevel.REFLEX,
    DifficultyBand.LOW: EffortLevel.LOW,
    DifficultyBand.MODERATE: EffortLevel.MEDIUM,
    DifficultyBand.HIGH: EffortLevel.HIGH,
}
_PASSES_FOR_EFFORT: dict[EffortLevel, int] = {
    EffortLevel.REFLEX: 1, EffortLevel.LOW: 1,
    EffortLevel.MEDIUM: 2, EffortLevel.HIGH: 3,
}


def enabled() -> bool:
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class ReasoningAllocation:
    difficulty: DifficultyBand
    requested_effort: EffortLevel
    effort: EffortLevel          # clamped ≤ budget ceiling
    chosen_profile: str
    passes: int                  # reasoning passes allowed (≥ 1)
    reasons: tuple[str, ...]


def allocate(*, intent: Any, card: Any, memory_context: str, router: Any,
             reflex_available: bool = False) -> ReasoningAllocation:
    difficulty = estimate(
        goal=intent.text, constraints=list(getattr(intent, "constraints", []) or []),
        max_risk=card.authority.max_risk, reflex_available=reflex_available,
        memory_context=memory_context)
    budget = for_card(card)
    requested = _EFFORT_FOR_BAND[difficulty]
    effort = budget.clamp(requested)
    reasons = [f"difficulty={difficulty.value}",
               f"requested={requested.value}", f"clamped={effort.value}"]
    chosen = _select_profile(router, intent.text, card, budget, reasons)
    passes = max(1, min(budget.max_passes, _PASSES_FOR_EFFORT[effort]))
    return ReasoningAllocation(difficulty, requested, effort, chosen, passes,
                               tuple(reasons))


def _select_profile(router: Any, task: str, card: Any, budget: Any,
                    reasons: list[str]) -> str:
    """Adaptive selection clamped by the budget's allowed tiers. Fail-closed:
    anything not explicitly allowed falls back to the card's own profile — never
    a silent upgrade."""
    default = getattr(card, "model_profile", "balanced")
    selected = None
    try:
        selected = router.select_profile_for_task(task)
    except Exception:
        selected = None
    name = getattr(selected, "name", None) if selected is not None else None
    if name and budget.allows_profile(name):
        reasons.append(f"router→{name}")
        return name
    reasons.append(f"fail_closed→{default}")
    return default
