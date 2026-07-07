"""Track B, B3 — adaptive reasoning allocation (pure logic, fail-closed)."""
from __future__ import annotations

from agentic_runtime import AgentCard, AgentClass, AuthorityScope, RiskLevel
from agentic_runtime.core_types import Intent
from agentic_runtime.reasoning import DifficultyBand, EffortLevel, allocate
from agentic_runtime.reasoning.reasoning_scheduler import enabled


class _NullRouter:
    def select_profile_for_task(self, task):
        return None


class _Prof:
    def __init__(self, name):
        self.name = name


class _RouterPicks:
    def __init__(self, name):
        self._name = name

    def select_profile_for_task(self, task):
        return _Prof(self._name)


def _card(cls, max_risk=RiskLevel.LOW, profile="balanced"):
    return AgentCard.make(name="x", agent_class=cls, mission="m",
                          authority=AuthorityScope(max_risk=max_risk),
                          model_profile=profile)


def test_high_difficulty_execution_gets_high_effort():
    alloc = allocate(intent=Intent.make("refactor and migrate the payment module"),
                     card=_card(AgentClass.EXECUTION, RiskLevel.HIGH),
                     memory_context="", router=_NullRouter())
    assert alloc.difficulty is DifficultyBand.HIGH
    assert alloc.effort is EffortLevel.HIGH
    assert alloc.chosen_profile == "balanced"   # router picked nothing → card default
    assert alloc.passes >= 1


def test_effort_clamped_by_budget_ceiling():
    # RESEARCH ceiling is MEDIUM → HIGH difficulty clamps down to MEDIUM effort
    alloc = allocate(
        intent=Intent.make("refactor and migrate everything now, delete the old code"),
        card=_card(AgentClass.RESEARCH, RiskLevel.HIGH),
        memory_context="", router=_NullRouter())
    assert alloc.effort is EffortLevel.MEDIUM
    assert "clamped=medium" in " ".join(alloc.reasons)


def test_router_selection_allowed_by_budget_is_used():
    alloc = allocate(intent=Intent.make("write a helper"),
                     card=_card(AgentClass.EXECUTION, RiskLevel.HIGH),
                     memory_context="", router=_RouterPicks("deep"))
    assert alloc.chosen_profile == "deep"


def test_router_selection_outside_budget_fails_closed():
    alloc = allocate(intent=Intent.make("write a helper"),
                     card=_card(AgentClass.RESEARCH),  # allows only "balanced"
                     memory_context="", router=_RouterPicks("deep"))
    assert alloc.chosen_profile == "balanced"
    assert any("fail_closed" in r for r in alloc.reasons)


def test_router_exception_is_swallowed_fail_closed():
    class _Boom:
        def select_profile_for_task(self, task):
            raise RuntimeError("router down")

    alloc = allocate(intent=Intent.make("do a thing"),
                     card=_card(AgentClass.EXECUTION), memory_context="", router=_Boom())
    assert alloc.chosen_profile == "balanced"


def test_enabled_reads_env(monkeypatch):
    monkeypatch.delenv("AUREL_REASONING_SCHEDULER", raising=False)
    assert enabled() is False
    monkeypatch.setenv("AUREL_REASONING_SCHEDULER", "1")
    assert enabled() is True
