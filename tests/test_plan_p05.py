"""P0.5 planning failure truth patch tests."""

import json

from agentic_runtime import (
    AgentCard, AgentClass, AuthorityScope, Intent, PlanStatus,
    RiskLevel, build_runtime,
)
from tests.conftest import bounded_test_approver
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.plan_validator import PlanValidator
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _kernel(scripted: dict, tmp_path):
    mock = MockModelClient(scripted=scripted)
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        model_clients={"balanced": [mock]},
        approval_gate=bounded_test_approver(
            lambda r: r.command.tool in {"run_tests", "edit_file", "write_file"},
        ),
    )


def _card(**kw):
    defaults = dict(
        name="Planner", agent_class=AgentClass.EXECUTION,
        mission="test", authority=AuthorityScope(max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "edit_file", "run_tests", "list_dir"],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def test_empty_plan_halts(tmp_path):
    goal = "empty plan goal"
    kernel = _kernel({goal: json.dumps({"plan": []})}, tmp_path)
    entity = kernel.spawn(_card())
    report = entity.run(Intent.make(goal))
    assert report["status"] == "halted"
    assert report["planning_status"] == PlanStatus.EMPTY_PLAN.value
    assert report["actions_executed"] == 0
    assert len(kernel.trace.planning_failures()) == 1


def test_invalid_json_plan_halts(tmp_path):
    goal = "bad json"
    kernel = _kernel({goal: "not-json{{"}, tmp_path)
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["status"] in {"halted", "invalid_plan"}
    assert report["planning_status"] == PlanStatus.INVALID_JSON.value
    assert report["actions_executed"] == 0


def test_missing_tool_halts(tmp_path):
    goal = "missing tool"
    plan = {"plan": [{"args": {}, "reason": "x"}]}
    kernel = _kernel({goal: json.dumps(plan)}, tmp_path)
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["planning_status"] == PlanStatus.INVALID_SCHEMA.value
    assert "tool" in report["reason"]


def test_missing_args_halts(tmp_path):
    goal = "missing args"
    plan = {"plan": [{"tool": "read_file", "reason": "look"}]}
    kernel = _kernel({goal: json.dumps(plan)}, tmp_path)
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["planning_status"] == PlanStatus.INVALID_SCHEMA.value
    assert "args" in report["reason"]


def test_unknown_tool_halts(tmp_path):
    goal = "unknown tool"
    plan = {"plan": [{"tool": "fly_to_moon", "args": {}, "reason": "nope"}]}
    kernel = _kernel({goal: json.dumps(plan)}, tmp_path)
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["planning_status"] == PlanStatus.UNKNOWN_TOOL.value


def test_unsupported_command_halts(tmp_path):
    goal = "unsupported"
    plan = {"plan": [{"tool": "run_shell", "args": {"cmd": ["ls"]}, "reason": "x"}]}
    kernel = _kernel({goal: json.dumps(plan)}, tmp_path)
    card = _card()
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["planning_status"] == PlanStatus.UNSUPPORTED_COMMAND.value


def test_valid_plan_executes(tmp_path):
    goal = "valid plan"
    plan = {"plan": [
        {"tool": "edit_file", "args": {"path": "src/a.py", "find": "x", "replace": "y"},
         "reason": "fix bug"},
    ]}
    kernel = _kernel({goal: json.dumps(plan)}, tmp_path)
    kernel.sandbox.write_file("src/a.py", "x\n")
    card = _card(authority=AuthorityScope(write_paths=["src/"], max_risk=RiskLevel.HIGH))
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == "completed"
    assert report["actions_executed"] == 1


def test_planning_failure_is_traced(tmp_path):
    goal = "trace me"
    kernel = _kernel({goal: json.dumps({"plan": []})}, tmp_path)
    kernel.spawn(_card()).run(Intent.make(goal))
    failures = kernel.trace.planning_failures()
    assert len(failures) == 1
    assert failures[0].status == PlanStatus.EMPTY_PLAN.value
    assert kernel.trace.verify_chain()[0]


def test_no_action_not_completed(tmp_path):
    goal = "noop"
    kernel = _kernel({goal: json.dumps({"plan": []})}, tmp_path)
    report = kernel.spawn(_card()).run(Intent.make(goal))
    assert report["status"] != "completed"
    assert report["actions_executed"] == 0


def test_plan_validator_unit():
    reg = {"read_file", "write_file"}
    v = PlanValidator(reg, allowed_tools=["read_file"])
    ok = v.validate_steps([{"tool": "read_file", "args": {"path": "a"}, "reason": "r"}])
    assert ok.valid
    bad = v.validate_steps([{"tool": "write_file", "args": {}, "reason": "r"}])
    assert bad.status is PlanStatus.UNSUPPORTED_COMMAND
