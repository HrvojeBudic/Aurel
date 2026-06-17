"""P0.8 budget, resource, and cost enforcement tests."""

from __future__ import annotations

import json

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    BudgetLedger,
    BudgetPolicy,
    Intent,
    RiskLevel,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.sandbox import UnsafeLocalSandbox
from tests.conftest import bounded_test_approver


def _card(**kw):
    defaults = dict(
        name="Budget Agent",
        agent_class=AgentClass.EXECUTION,
        mission="budget tests",
        authority=AuthorityScope(write_paths=["src/", "."], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "edit_file", "run_shell", "run_tests", "list_dir"],
        denied_tools=[],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def _kernel(tmp_path, *, plan=None, policy=None):
    model_clients = None
    if plan:
        model_clients = {"balanced": [MockModelClient(scripted=plan)]}
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        model_clients=model_clients,
        approval_gate=bounded_test_approver(lambda _r: True, allow_r4=True),
        budget=BudgetLedger(policy=policy or BudgetPolicy()),
    )


def test_max_commands_enforced(tmp_path):
    goal = "two commands"
    plan = {
        goal: json.dumps(
            {"plan": [
                {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"}, "reason": "1"},
                {"tool": "write_file", "args": {"path": "src/b.py", "content": "b\n"}, "reason": "2"},
            ]}
        )
    }
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_commands_per_run=1))
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["reason_code"] == "budget_exceeded"
    assert report["status"] != "completed"


def test_max_tool_calls_enforced(tmp_path):
    goal = "two tools"
    plan = {
        goal: json.dumps(
            {"plan": [
                {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"}, "reason": "1"},
                {"tool": "read_file", "args": {"path": "src/a.py"}, "reason": "2"},
            ]}
        )
    }
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_tool_calls_per_run=1))
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["reason_code"] == "budget_exceeded"


def test_max_retries_enforced(tmp_path):
    goal = "retry limit"
    plan = {
        goal: json.dumps(
            {"plan": [
                {"tool": "edit_file", "args": {"path": "src/a.py", "find": "missing", "replace": "x"}, "reason": "fail"},
            ]}
        )
    }
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_retries_per_step=0))
    kernel.sandbox.write_file("src/a.py", "hello\n")
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["reason_code"] == "budget_exceeded"
    assert report["status"] == "halted"


def test_max_sandbox_executions_enforced(tmp_path):
    goal = "sandbox cap"
    plan = {goal: json.dumps({"plan": [{"tool": "read_file", "args": {"path": "src/a.py"}, "reason": "read"}]})}
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_sandbox_executions=0))
    kernel.sandbox.write_file("src/a.py", "x\n")
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["reason_code"] == "budget_exceeded"


def test_runtime_timeout_enforced(tmp_path):
    goal = "timeout now"
    plan = {goal: json.dumps({"plan": [{"tool": "read_file", "args": {"path": "src/a.py"}, "reason": "read"}]})}
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_runtime_seconds=0.0))
    kernel.sandbox.write_file("src/a.py", "x\n")
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["reason_code"] == "budget_exceeded"


def test_stdout_cap_enforced(tmp_path):
    kernel = _kernel(tmp_path, policy=BudgetPolicy(max_stdout_bytes=16))
    card = _card()
    cmd = CommandEnvelope.make(
        issuer_card_id=card.id,
        tool="run_shell",
        args={"cmd": ["python3", "-c", "print('x'*200)"]},
        rationale="emit large stdout",
        declared_risk=RiskLevel.HIGH,
        expected_effect="stdout",
    )
    res = kernel.runtime.submit(cmd, card)
    assert len(res.observation.stdout.encode("utf-8")) <= 16
    assert res.observation.artifacts.get("stdout_truncated") is True


def test_stderr_cap_enforced(tmp_path):
    kernel = _kernel(tmp_path, policy=BudgetPolicy(max_stderr_bytes=20))
    card = _card()
    cmd = CommandEnvelope.make(
        issuer_card_id=card.id,
        tool="run_shell",
        args={"cmd": ["python3", "-c", "import sys; sys.stderr.write('e'*200); raise SystemExit(1)"]},
        rationale="emit large stderr",
        declared_risk=RiskLevel.HIGH,
        expected_effect="stderr",
    )
    res = kernel.runtime.submit(cmd, card)
    assert len(res.observation.stderr.encode("utf-8")) <= 20
    assert res.observation.artifacts.get("stderr_truncated") is True


def test_file_write_limit_enforced(tmp_path):
    goal = "writes blocked"
    plan = {goal: json.dumps({"plan": [{"tool": "write_file", "args": {"path": "src/a.py", "content": "x\n"}, "reason": "write"}]})}
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_file_writes=0))
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["reason_code"] == "budget_exceeded"


def test_budget_exceeded_is_traced(tmp_path):
    goal = "trace budget"
    plan = {
        goal: json.dumps(
            {"plan": [
                {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"}, "reason": "1"},
                {"tool": "write_file", "args": {"path": "src/b.py", "content": "b\n"}, "reason": "2"},
            ]}
        )
    }
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_commands_per_run=1))
    kernel.spawn(_card()).run(Intent.make(goal))
    rows = list(kernel.trace.replay())
    assert any(r.get("kind") == "budget_decision" and r.get("verdict") == "deny" for r in rows)


def test_budget_exceeded_never_reports_completed(tmp_path):
    goal = "never completed"
    plan = {
        goal: json.dumps(
            {"plan": [
                {"tool": "write_file", "args": {"path": "src/a.py", "content": "a\n"}, "reason": "1"},
                {"tool": "write_file", "args": {"path": "src/b.py", "content": "b\n"}, "reason": "2"},
            ]}
        )
    }
    kernel = _kernel(tmp_path, plan=plan, policy=BudgetPolicy(max_tool_calls_per_run=1))
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["status"] != "completed"
    assert report["reason_code"] == "budget_exceeded"
    assert "usage" in report["budget"]
