"""difficulty_estimator.py — deterministic difficulty banding (Track B, B2).

Advisory only: maps a task's observable features to a difficulty band that the
reasoning scheduler (B3) uses to pick a System-1/System-2 effort. It is pure and
deterministic (no LLM, no randomness), emits no command, and is fail-closed —
an empty/ambiguous goal biases HIGH. Advisory ≠ authority.
"""
from __future__ import annotations

from enum import Enum
from typing import Sequence

from ..core_types import RiskLevel


class DifficultyBand(str, Enum):
    TRIVIAL = "trivial"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


_RISK_RANK: dict[RiskLevel, int] = {
    RiskLevel.TRIVIAL: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4,
}
_WRITE_VERBS = ("write", "delete", "deploy", "modify", "refactor", "migrate",
                "remove", "rename", "install", "publish", "overwrite")
_SPARSE_CONTEXT_CHARS = 40


def estimate(*, goal: str, constraints: Sequence[str], max_risk: RiskLevel,
             reflex_available: bool, memory_context: str = "") -> DifficultyBand:
    """Deterministic difficulty band from observable features."""
    text = (goal or "").strip()
    if not text:
        return DifficultyBand.HIGH          # ambiguous → fail closed (bias higher)
    if reflex_available:
        return DifficultyBand.TRIVIAL       # a verified reflex already handles it

    score = 0
    risk_rank = _RISK_RANK.get(max_risk, 1)
    if risk_rank >= 3:
        score += 2
    elif risk_rank == 2:
        score += 1
    if len(constraints) >= 3:
        score += 1
    if len(text) > 200:
        score += 1
    lowered = text.lower()
    if any(v in lowered for v in _WRITE_VERBS):
        score += 1
    if len(memory_context.strip()) < _SPARSE_CONTEXT_CHARS:
        score += 1                          # sparse prior knowledge → harder

    if score >= 4:
        return DifficultyBand.HIGH
    if score >= 2:
        return DifficultyBand.MODERATE
    if score == 1:
        return DifficultyBand.LOW
    return DifficultyBand.TRIVIAL
