"""Entity planner tests — extended for P0.5."""

import json

from agentic_runtime import AgentCard, AgentClass, AuthorityScope, Intent, PlanStatus, RiskLevel, build_runtime
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient


def test_empty_plan_halts():
    goal = "do nothing useful"
    mock = MockModelClient(scripted={goal: json.dumps({"plan": []})})
    kernel = build_runtime(
        model_clients={"balanced": [mock]},
        approval_gate=AutoApprover(),
    )
    card = AgentCard.make(
        name="Planner", agent_class=AgentClass.EXECUTION,
        mission="test", authority=AuthorityScope(max_risk=RiskLevel.MEDIUM))
    entity = kernel.spawn(card)
    report = entity.run(Intent.make(goal))
    assert report["status"] == "halted"
    assert report.get("planning_status") == PlanStatus.EMPTY_PLAN.value
    assert report["actions_executed"] == 0


def test_invalid_json_plan_halts():
    goal = "bad json plan"
    mock = MockModelClient(scripted={goal: "not json at all"})
    kernel = build_runtime(
        model_clients={"balanced": [mock]},
        approval_gate=AutoApprover(),
    )
    card = AgentCard.make(
        name="Planner", agent_class=AgentClass.EXECUTION,
        mission="test", authority=AuthorityScope(max_risk=RiskLevel.MEDIUM))
    entity = kernel.spawn(card)
    report = entity.run(Intent.make(goal))
    assert report["status"] in {"halted", "invalid_plan"}
    assert report.get("planning_status") == PlanStatus.INVALID_JSON.value
