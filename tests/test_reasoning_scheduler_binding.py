"""Track B, B3+B4 — reasoning scheduler bound into entity.plan behind a flag.

Flag OFF (default): the planning path is byte-identical — no reasoning charge,
no reasoning_allocation trace event. Flag ON: one reasoning pass is charged and a
hash-chained reasoning_allocation event (safe summaries only) is recorded.
"""
from __future__ import annotations

import json

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.budget import BudgetLedger, BudgetPolicy
from agentic_runtime.core_types import Intent
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient

_GOAL = "write a file"
_PLAN = {_GOAL: json.dumps({"plan": [
    {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"},
     "reason": "do it"},
]})}

_MANY_GOAL = "many steps"
_MANY_STEPS = [{"tool": "write_file", "args": {"path": f"src/f{i}.py", "content": "x\n"},
                "reason": "r"} for i in range(9)]  # >8 clean steps → PRM escalates
_MANY_PLAN = {_MANY_GOAL: json.dumps({"plan": _MANY_STEPS})}


def _exec_card():
    return AgentCard.make(
        name="E", agent_class=AgentClass.EXECUTION, mission="m",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["write_file", "read_file"])


def _entity(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
        trace_backend="memory",
        model_clients={"balanced": [MockModelClient(scripted=_PLAN)]})
    card = AgentCard.make(
        name="E", agent_class=AgentClass.EXECUTION, mission="m",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["write_file", "read_file"])
    return kernel, kernel.spawn(card)


def _alloc_events(kernel):
    return [e for e in kernel.trace
            if getattr(e, "event_type", "") == "reasoning_allocation"]


def test_flag_off_is_byte_identical(tmp_path, monkeypatch):
    monkeypatch.delenv("AUREL_REASONING_SCHEDULER", raising=False)
    kernel, ent = _entity(tmp_path)
    res = ent.plan(Intent.make(_GOAL))
    assert res.valid
    assert kernel.runtime.budget.snapshot()["usage"]["reasoning_passes"] == 0
    assert _alloc_events(kernel) == []


def test_flag_on_charges_and_traces_allocation(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_REASONING_SCHEDULER", "1")
    kernel, ent = _entity(tmp_path)
    res = ent.plan(Intent.make(_GOAL))
    assert res.valid  # plan still produced via the chosen profile
    assert kernel.runtime.budget.snapshot()["usage"]["reasoning_passes"] == 1

    events = _alloc_events(kernel)
    assert len(events) == 1
    details = events[0].details
    assert details["effort"] in ("reflex", "low", "medium", "high")
    assert details["profile"] == "balanced"      # router had no config → card default
    assert "difficulty" in details
    # the trace record is hash-chained like every other trace entry
    assert events[0].entry_hash and events[0].prev_entry_hash


def _step_score_events(kernel):
    return [e for e in kernel.trace
            if getattr(e, "event_type", "") == "reasoning_step_score"]


def test_prm_escalates_bounded_by_pass_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_REASONING_SCHEDULER", "1")
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
        trace_backend="memory",
        model_clients={"balanced": [MockModelClient(scripted=_MANY_PLAN)]})
    ent = kernel.spawn(_exec_card())
    res = ent.plan(Intent.make(_MANY_GOAL))
    assert res.valid  # a valid (if oversized) plan is still returned

    # >8-step plan escalates; the mock returns the same plan each replan, so it is
    # bounded by the budget (1 base pass + at least one replan, never runaway).
    passes = kernel.runtime.budget.snapshot()["usage"]["reasoning_passes"]
    assert 2 <= passes <= 3   # base + 1..2 replans, capped by max_passes
    score_events = _step_score_events(kernel)
    assert len(score_events) == 1
    assert score_events[0].details["should_escalate"] is True
    assert score_events[0].details["attempts"] >= 1
    assert score_events[0].details["advisory"] is True


def test_reasoning_pass_cap_stops_escalation(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_REASONING_SCHEDULER", "1")
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
        trace_backend="memory",
        model_clients={"balanced": [MockModelClient(scripted=_MANY_PLAN)]},
        budget=BudgetLedger(BudgetPolicy(max_reasoning_passes_per_run=1)))
    ent = kernel.spawn(_exec_card())
    res = ent.plan(Intent.make(_MANY_GOAL))
    assert res.valid  # base plan kept despite the cap denying escalation
    # the cap comes alive: escalation is denied, so passes never run away
    assert kernel.runtime.budget.snapshot()["usage"]["reasoning_passes"] <= 2
