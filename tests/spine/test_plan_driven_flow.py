"""SPINE-LIVE-A tests — model plan realized as a live flow graph."""

from __future__ import annotations

import pytest

from agentic_runtime import UnsafeLocalSandbox
from agentic_runtime.aurel_flow.workflow_graph import validate_workflow_graph
from agentic_runtime.spine import PlanRealizationError, plan_to_flow, run_spine_slice

_FIXED = "VALUE = 2\n"

# a valid structured plan that fixes calc.py then runs its test
_PLAN_JSON = (
    '{"intent_summary": "fix calc", "plan": ['
    '{"step_id": "patch", "tool": "write_file", "args": {"path": "calc.py", '
    '"content": "VALUE = 2\\n"}, "risk": "medium", "reason": "set VALUE to 2"},'
    '{"step_id": "verify", "tool": "run_tests", "args": {"test_file": '
    '"test_calc.py"}, "risk": "low", "reason": "confirm the fix"}'
    '], "confidence": 0.9, "requires_approval": true, "assumptions": [], '
    '"refusal_reason": null}'
)


class _FakeHardSandbox(UnsafeLocalSandbox):
    def __init__(self, root: str | None = None) -> None:
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


class _ScriptedClient:
    """A model client that returns one fixed plan regardless of prompt."""

    name = "scripted-deepseek"

    def __init__(self, plan_json: str) -> None:
        self._plan = plan_json

    def complete(self, system: str, user: str) -> str:
        return self._plan


# --------------------------------------------------------------------------- #
#  plan_to_flow
# --------------------------------------------------------------------------- #
def test_plan_to_flow_builds_linear_graph():
    steps = [
        {"step_id": "patch", "tool": "write_file", "args": {"path": "calc.py", "content": _FIXED}},
        {"step_id": "verify", "tool": "run_tests", "args": {"test_file": "test_calc.py"}},
    ]
    graph, tasks = plan_to_flow(steps)
    assert validate_workflow_graph(graph).valid is True
    assert [n.node_id for n in graph.nodes] == ["patch", "verify"]
    assert tasks["patch"][0] == "write_file"
    assert tasks["verify"][0] == "run_tests"
    assert graph.entry_node_ids == ("patch",)
    assert graph.exit_node_ids == ("verify",)


def test_plan_to_flow_rejects_disallowed_tool():
    steps = [{"step_id": "x", "tool": "run_shell", "args": {"cmd": ["rm", "-rf", "/"]}}]
    with pytest.raises(PlanRealizationError, match="allowlist"):
        plan_to_flow(steps)


def test_plan_to_flow_rejects_empty_plan():
    with pytest.raises(PlanRealizationError, match="empty plan"):
        plan_to_flow([])


# --------------------------------------------------------------------------- #
#  plan-driven end-to-end
# --------------------------------------------------------------------------- #
def test_plan_driven_slice_executes_the_models_plan(tmp_path):
    result = run_spine_slice(
        trace_dir=tmp_path,
        run_id="plan-driven",
        sandbox=_FakeHardSandbox(),
        model_client=_ScriptedClient(_PLAN_JSON),
        plan_driven=True,
    )
    assert result.plan_driven is True
    assert result.model_call_available is True
    assert result.plan is not None
    assert len(result.plan["steps"]) == 2
    # the model's own steps were realized and dispatched
    assert [s["node_id"] for s in result.dispatch["step_results"]] == ["patch", "verify"]
    assert result.execution_available is True
    assert result.trace_verified is True
    assert result.shell_binding_live is True
    assert result.spine_live is True


def test_plan_driven_invalid_plan_is_honest_unavailable(tmp_path):
    result = run_spine_slice(
        trace_dir=tmp_path,
        run_id="plan-bad",
        sandbox=_FakeHardSandbox(),
        model_client=_ScriptedClient('{"not": "a plan"}'),
        plan_driven=True,
    )
    assert result.spine_live is False
    assert result.execution_available is False
    assert "invalid" in result.unavailable_reason or "realizable" in result.unavailable_reason
