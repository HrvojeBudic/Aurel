"""reasoning/ — proposal-only reasoning-allocation surface.

Nothing in this package executes or grants authority. It shapes only what is
requested (thinking budgets, allocation read-models); PlanValidator and
AgenticRuntime.submit remain the sole gates. Allocation ≠ authority.

P0-S.1 lands the truthful token-accounting read-model; later phases (P6.5.x)
add the thinking budget, difficulty estimator and reasoning scheduler.
"""
from __future__ import annotations

from .difficulty_estimator import DifficultyBand, estimate
from .thinking_budget import EffortLevel, ThinkingBudget, for_card
from .token_accounting import TokenAccountingView

__all__ = [
    "TokenAccountingView",
    "EffortLevel",
    "ThinkingBudget",
    "for_card",
    "DifficultyBand",
    "estimate",
]
