"""Track B, B6 — read-only reasoning workload projection + CLI."""
from __future__ import annotations

import argparse
import json

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.cli_modules.reasoning_commands import (
    cmd_reasoning_status,
    cmd_reasoning_workload,
)
from agentic_runtime.core_types import Intent, PraxisEventRecord
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.reasoning import WorkloadView


def _alloc(effort, difficulty="high", profile="balanced"):
    return PraxisEventRecord.make("r", "a", "reasoning_allocation", "s", "",
                                  {"effort": effort, "difficulty": difficulty,
                                   "profile": profile})


def _score(attempts, escalate):
    return PraxisEventRecord.make("r", "a", "reasoning_step_score", "s", "",
                                  {"attempts": attempts, "should_escalate": escalate,
                                   "advisory": True})


# ---- unit: pure fold ------------------------------------------------------- #
def test_from_records_folds_allocations_and_escalations():
    v = WorkloadView.from_records(
        [_alloc("high"), _alloc("medium", "moderate"), _score(2, True), _score(0, False)])
    assert v.allocations == 2
    assert v.effort_histogram == {"high": 1, "medium": 1}
    assert v.difficulty_histogram == {"high": 1, "moderate": 1}
    assert v.escalations == 1
    assert v.total_attempts == 2
    assert v.projection is True


def test_from_records_handles_replayed_praxis_dict():
    replayed = [{
        "event_type": "praxis_event",
        "payload": {"event_type": "reasoning_allocation",
                    "details": {"effort": "low", "difficulty": "low", "profile": "balanced"}},
    }]
    v = WorkloadView.from_records(replayed)
    assert v.allocations == 1 and v.effort_histogram == {"low": 1}


def test_budget_snapshot_propagates_honesty_flags():
    snap = {"usage": {"reasoning_passes": 3, "thinking_tokens": 40,
                      "thinking_calls": 2, "estimate_only": True, "substantiated": False}}
    v = WorkloadView.from_records([], budget_snapshot=snap)
    assert v.reasoning_passes == 3 and v.thinking_tokens == 40
    assert v.estimate_only is True and v.substantiated is False


def test_ignores_non_reasoning_records():
    v = WorkloadView.from_records([PraxisEventRecord.make("r", "a", "other", "s", "", {})])
    assert v.allocations == 0 and v.escalations == 0


# ---- CLI ------------------------------------------------------------------- #
def test_status_cli(capsys):
    rc = cmd_reasoning_status(argparse.Namespace(json=True))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["model_judge_available"] is False
    assert "high" in out["effort_levels"]


def test_workload_cli_over_persisted_run(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("AUREL_REASONING_SCHEDULER", "1")
    trace_dir = str(tmp_path / "traces")
    goal = "write a file"
    plan = {goal: json.dumps({"plan": [
        {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"}, "reason": "r"}]})}
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=AutoApprover(lambda r: True, allow_r2=True, allow_r3=True),
        trace_backend="persistent", trace_dir=trace_dir,
        model_clients={"balanced": [MockModelClient(scripted=plan)]})
    card = AgentCard.make(
        name="E", agent_class=AgentClass.EXECUTION, mission="m",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["write_file", "read_file"])
    run_id = kernel.trace.run_id
    assert kernel.spawn(card).plan(Intent.make(goal)).valid
    kernel.trace.seal_run("completed")

    rc = cmd_reasoning_workload(argparse.Namespace(
        run_id=run_id, trace_dir=trace_dir, json=True))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["projection"] is True
    assert out["allocations"] >= 1
    assert "balanced" in out["profile_histogram"]
