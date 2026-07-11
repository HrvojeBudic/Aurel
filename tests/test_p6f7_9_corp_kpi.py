"""F7.9 seal (Python) — the Reflex Flywheel KPIs (reflex hit rate + cost per task).

Each KPI is honest about absence — an empty system reports UNAVAILABLE with a
reason, never a 0% that lies. Reflex hit rate is uses-weighted from the skill
library; cost per task is the per-run cost the budget ledger already tracks (F7.1).
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.core_types import CapabilityState, CommandEnvelope, RiskLevel
from agentic_runtime.corp import ReflexFlywheelView
from agentic_runtime.front_server import LiveReadModels
from agentic_runtime.skills import SkillLibrary


class _Skill:
    def __init__(self, state, success_count):
        self.state = state
        self.success_count = success_count


class _Skills:
    def __init__(self, skills):
        self._s = skills

    def all(self):
        return list(self._s)


# --- reflex hit rate --------------------------------------------------------------

def test_reflex_hit_rate_is_uses_weighted():
    skills = _Skills([
        _Skill(CapabilityState.REFLEX, 3),
        _Skill(CapabilityState.REFLEX, 2),
        _Skill(CapabilityState.ACTIVE, 5),
    ])
    reflex = ReflexFlywheelView.build(skills=skills).reflex
    assert reflex["status"] == "AVAILABLE"
    assert reflex["reflex_uses"] == 5 and reflex["total_uses"] == 10
    assert reflex["rate"] == 0.5
    assert reflex["by_state"]["reflex"] == 2


def test_reflex_unavailable_without_usage():
    assert ReflexFlywheelView.build(skills=_Skills([])).reflex["status"] == "UNAVAILABLE"
    zero = _Skills([_Skill(CapabilityState.ACTIVE, 0)])
    assert ReflexFlywheelView.build(skills=zero).reflex["status"] == "UNAVAILABLE"


def test_reflex_unavailable_without_library():
    assert ReflexFlywheelView.build(skills=None).reflex["status"] == "UNAVAILABLE"


def test_reflex_with_real_skill_library():
    lib = SkillLibrary()
    cmd = CommandEnvelope.make(issuer_card_id="c", tool="write_file", args={},
                               rationale="r", declared_risk=RiskLevel.LOW,
                               expected_effect="e")
    sk = lib.observe_success("s1", "desc", [cmd], "env-sig", {})
    sk.state = CapabilityState.REFLEX          # force a verified reflex
    sk.success_count = 4
    reflex = ReflexFlywheelView.build(skills=lib).reflex
    assert reflex["status"] == "AVAILABLE" and reflex["rate"] == 1.0   # only skill, in reflex


# --- cost per task ----------------------------------------------------------------

def test_cost_per_task_from_ledger():
    led = BudgetLedger()
    led.begin_run("run-a", "c", "i")
    led.charge_llm(usage=None, usd=0.50)       # 50 cents
    led.begin_run("run-b", "c", "i")
    led.charge_llm(usage=None, usd=0.30)       # 30 cents
    cpt = ReflexFlywheelView.build(ledger=led).cost_per_task
    assert cpt["status"] == "AVAILABLE"
    assert cpt["run_count"] == 2
    assert round(cpt["total_cost_cents"], 3) == 80.0
    assert round(cpt["avg_cost_cents"], 3) == 40.0
    assert [r["run_id"] for r in cpt["runs"]] == ["run-a", "run-b"]   # deterministic


def test_cost_per_task_unavailable_without_data():
    assert ReflexFlywheelView.build(ledger=None).cost_per_task["status"] == "UNAVAILABLE"
    assert ReflexFlywheelView.build(ledger=BudgetLedger()).cost_per_task["status"] == "UNAVAILABLE"


# --- live read model --------------------------------------------------------------

def test_corp_kpi_via_live_read_registry():
    rt = build_runtime()
    status, payload = LiveReadModels(rt).read("/read/corp/kpi")
    assert status == 200 and payload["model"] == "corp/kpi"
    # the runtime binds no skill library ⇒ reflex is honestly UNAVAILABLE, never 0%
    assert payload["reflex"]["status"] == "UNAVAILABLE"
    assert "cost_per_task" in payload
