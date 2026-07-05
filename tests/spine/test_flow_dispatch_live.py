"""SPINE-LIVE-2 tests — the flow dispatch loop over the real executor."""

from __future__ import annotations

from agentic_runtime import AutoApprover, UnsafeLocalSandbox, build_runtime
from agentic_runtime.aurel_flow.workflow_state import (
    WorkflowLifecycleStatus,
    WorkflowNodeState,
)
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
)
from agentic_runtime.spine import (
    FlowDispatcher,
    SpineToolExecSession,
    build_patch_test_graph,
    create_workflow_run,
)

_ORIGINAL = "VALUE = 1\n"
_PATCHED = "VALUE = 2\n"

_PASS = {"command": ["python3", "-c", "import sys; sys.exit(0)"]}
_FAIL = {"command": ["python3", "-c", "import sys; sys.exit(1)"]}


class _FakeHardSandbox(UnsafeLocalSandbox):
    def __init__(self, root: str | None = None) -> None:
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


def _card() -> AgentCard:
    return AgentCard.make(
        name="Spine Flow",
        agent_class=AgentClass.EXECUTION,
        mission="SPINE-LIVE flow dispatch",
        authority=AuthorityScope(
            write_paths=["calc.py"],
            read_paths=["*"],
            max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=["read_file", "write_file", "run_tests"],
        model_profile="balanced",
    )


def _kernel(sandbox):
    return build_runtime(
        sandbox=sandbox,
        approval_gate=AutoApprover(
            lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
        ),
    )


def _setup(sandbox, test_args):
    kernel = _kernel(sandbox)
    kernel.sandbox.write_file("calc.py", _ORIGINAL)
    session = SpineToolExecSession(kernel.runtime, _card())
    graph = build_patch_test_graph()
    run = create_workflow_run(graph)
    tasks = {
        "patch": ("write_file", {"path": "calc.py", "content": _PATCHED}),
        "test": ("run_tests", test_args),
    }
    steps = [tasks["patch"], tasks["test"]]
    lease = session.issue_lease(steps)
    return kernel, session, graph, run, tasks, lease


def test_two_node_graph_dispatches_and_completes():
    kernel, session, graph, run, tasks, lease = _setup(_FakeHardSandbox(), _PASS)
    result = FlowDispatcher(session).dispatch(graph, run, tasks, lease)

    assert result.success is True
    assert result.lifecycle_status is WorkflowLifecycleStatus.COMPLETED
    assert result.execution_available is True
    assert [s.node_id for s in result.step_results] == ["patch", "test"]
    assert all(s.dispatched for s in result.step_results)
    assert result.run.state.node_states["patch"] is WorkflowNodeState.COMPLETED
    assert result.run.state.node_states["test"] is WorkflowNodeState.COMPLETED
    # each node has a before + after checkpoint
    assert len(result.checkpoints) == 4
    assert kernel.sandbox.read_file("calc.py") == _PATCHED


def test_node_failure_halts_downstream():
    kernel, session, graph, run, tasks, lease = _setup(_FakeHardSandbox(), _FAIL)
    result = FlowDispatcher(session).dispatch(graph, run, tasks, lease)

    assert result.success is False
    assert result.lifecycle_status is WorkflowLifecycleStatus.FAILED
    # patch ran and completed; test ran and failed
    states = result.run.state.node_states
    assert states["patch"] is WorkflowNodeState.COMPLETED
    assert states["test"] is WorkflowNodeState.FAILED
    # the failing node is the last dispatched; nothing beyond it
    assert result.step_results[-1].node_id == "test"
    assert result.step_results[-1].success is False


def test_pause_before_test_then_resume_completes():
    kernel, session, graph, run, tasks, lease = _setup(_FakeHardSandbox(), _PASS)
    dispatcher = FlowDispatcher(session)

    # pause before the "test" node
    paused = dispatcher.dispatch(
        graph, run, tasks, lease,
        pause_before=lambda node_id, _run: node_id == "test",
    )
    assert paused.paused is True
    assert paused.lifecycle_status is WorkflowLifecycleStatus.PAUSED
    assert paused.run.state.node_states["patch"] is WorkflowNodeState.COMPLETED
    assert paused.run.state.node_states["test"] is WorkflowNodeState.NOT_STARTED
    assert [s.node_id for s in paused.step_results] == ["patch"]

    # resume from the recorded paused run — completes the test node
    resumed = dispatcher.dispatch(graph, paused.run, tasks, lease)
    assert resumed.paused is False
    assert resumed.success is True
    assert resumed.lifecycle_status is WorkflowLifecycleStatus.COMPLETED
    assert resumed.run.state.node_states["test"] is WorkflowNodeState.COMPLETED
    assert kernel.sandbox.read_file("calc.py") == _PATCHED


def test_dispatch_grants_no_execution_without_hard_isolation():
    # unsafe sandbox → the S1 gate fail-closes on the mutating patch node
    import pytest

    from agentic_runtime.spine import SpineExecutionBlocked

    kernel, session, graph, run, tasks, lease = _setup(UnsafeLocalSandbox(), _PASS)
    with pytest.raises(SpineExecutionBlocked, match="hard-isolated"):
        FlowDispatcher(session).dispatch(graph, run, tasks, lease)
    # fail-closed: file untouched
    assert kernel.sandbox.read_file("calc.py") == _ORIGINAL
