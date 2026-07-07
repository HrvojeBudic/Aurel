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
from agentic_runtime.core_types import Intent
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient

_GOAL = "write a file"
_PLAN = {_GOAL: json.dumps({"plan": [
    {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"},
     "reason": "do it"},
]})}


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
