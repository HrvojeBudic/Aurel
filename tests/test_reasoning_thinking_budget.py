"""Track B, B1 — per-entity ThinkingBudget (deny-by-default, clamp ≤ ceiling)."""
from __future__ import annotations

from agentic_runtime import AgentCard, AgentClass, AuthorityScope, RiskLevel
from agentic_runtime.reasoning import EffortLevel, ThinkingBudget, for_card
from agentic_runtime.reasoning.thinking_budget import _EFFORT_RANK


def _card(cls, max_risk=RiskLevel.LOW):
    return AgentCard.make(name="x", agent_class=cls, mission="m",
                          authority=AuthorityScope(max_risk=max_risk))


def test_clamp_never_exceeds_ceiling():
    for ceiling in EffortLevel:
        tb = ThinkingBudget(effort_ceiling=ceiling)
        for requested in EffortLevel:
            out = tb.clamp(requested)
            assert _EFFORT_RANK[out] <= _EFFORT_RANK[ceiling]


def test_clamp_returns_requested_when_within_ceiling():
    tb = ThinkingBudget(effort_ceiling=EffortLevel.HIGH)
    assert tb.clamp(EffortLevel.LOW) is EffortLevel.LOW
    assert tb.clamp(EffortLevel.HIGH) is EffortLevel.HIGH


def test_clamp_none_or_unknown_collapses_to_reflex():
    tb = ThinkingBudget(effort_ceiling=EffortLevel.HIGH)
    assert tb.clamp(None) is EffortLevel.REFLEX


def test_for_card_writer_high_risk_gets_high_ceiling():
    tb = for_card(_card(AgentClass.EXECUTION, RiskLevel.HIGH))
    assert tb.effort_ceiling is EffortLevel.HIGH
    assert "deep" in tb.allowed_profile_tiers


def test_for_card_writer_low_risk_gets_medium_ceiling():
    assert for_card(_card(AgentClass.CORE, RiskLevel.LOW)).effort_ceiling is EffortLevel.MEDIUM


def test_for_card_readonly_and_unknown_are_conservative():
    assert for_card(_card(AgentClass.RESEARCH)).effort_ceiling is EffortLevel.MEDIUM
    assert for_card(_card(AgentClass.POLICY)).effort_ceiling is EffortLevel.LOW
    assert for_card(_card(AgentClass.MEMORY)).effort_ceiling is EffortLevel.LOW


def test_allows_profile():
    tb = ThinkingBudget(allowed_profile_tiers=("balanced",))
    assert tb.allows_profile("balanced") is True
    assert tb.allows_profile("deep") is False
