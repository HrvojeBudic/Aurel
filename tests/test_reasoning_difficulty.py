"""Track B, B2 — deterministic, advisory difficulty estimator (fail-closed)."""
from __future__ import annotations

from agentic_runtime.core_types import RiskLevel
from agentic_runtime.reasoning import DifficultyBand, estimate


def test_empty_goal_fails_closed_high():
    assert estimate(goal="   ", constraints=[], max_risk=RiskLevel.LOW,
                    reflex_available=False) is DifficultyBand.HIGH


def test_reflex_available_is_trivial():
    assert estimate(goal="deploy everything now", constraints=["a", "b", "c"],
                    max_risk=RiskLevel.HIGH, reflex_available=True) is DifficultyBand.TRIVIAL


def test_high_risk_write_sparse_context_is_high():
    band = estimate(goal="refactor and migrate the payment module",
                    constraints=["x", "y", "z"], max_risk=RiskLevel.HIGH,
                    reflex_available=False, memory_context="")
    assert band is DifficultyBand.HIGH


def test_simple_low_risk_read_with_rich_context_is_trivial():
    band = estimate(goal="summarize the file", constraints=[], max_risk=RiskLevel.LOW,
                    reflex_available=False, memory_context="x" * 200)
    assert band is DifficultyBand.TRIVIAL


def test_moderate_in_between():
    band = estimate(goal="write a short helper", constraints=[], max_risk=RiskLevel.MEDIUM,
                    reflex_available=False, memory_context="x" * 200)
    # medium risk (+1) + write verb (+1) = 2 → MODERATE
    assert band is DifficultyBand.MODERATE


def test_is_deterministic():
    args = dict(goal="modify config and redeploy", constraints=["a"],
                max_risk=RiskLevel.HIGH, reflex_available=False, memory_context="")
    assert estimate(**args) is estimate(**args)
