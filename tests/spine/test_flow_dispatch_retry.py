"""M3 — opt-in retry in the flow dispatcher, driven by sealed recovery read-models.

Retry *decisions* come from ``aurel_flow.recovery`` (classify + eligibility);
retry *execution* (sandbox rollback + re-submit) happens in the dispatcher. A
flaky node recovers; an unrecoverable one exhausts its budget and PAUSES with an
operator recovery proposal; a policy-blocked node is never retried.
"""

from __future__ import annotations

from agentic_runtime import UnsafeLocalSandbox
from agentic_runtime.aurel_flow.recovery import DEFAULT_RETRY_POLICY
from agentic_runtime.aurel_flow.workflow_state import WorkflowLifecycleStatus
from agentic_runtime.spine import (
    FlowDispatcher,
    build_patch_test_graph,
    create_workflow_run,
)
from agentic_runtime.spine.live_evidence import LiveEvidenceLabel
from agentic_runtime.spine.tool_exec import (
    TOOL_EXEC_EVIDENCE_VERSION,
    ToolExecEvidenceRef,
    ToolExecLease,
)


def _evidence(tool: str, *, success: bool, blocked: str = "") -> ToolExecEvidenceRef:
    return ToolExecEvidenceRef(
        exec_id="ev",
        contract_version=TOOL_EXEC_EVIDENCE_VERSION,
        tool=tool,
        tool_args_hash="h",
        command_id="cmd" if not blocked else "",
        before_state_hash="b",
        after_state_hash="a",
        success=success,
        runtime_submit_called=not blocked,
        verifier_passed=success,
        rolled_back=not success,
        label=LiveEvidenceLabel.LIVE,
        blocked_reason=blocked,
    )


class _ScriptedSession:
    """Minimal session double: each node's success follows a scripted list."""

    def __init__(self, script: dict[str, list[bool]], *, blocked: set[str] | None = None):
        self.sandbox = UnsafeLocalSandbox()
        self.script = {k: list(v) for k, v in script.items()}
        self.blocked = blocked or set()
        self.calls: dict[str, int] = {}

    def issue_lease(self, steps, **kw) -> ToolExecLease:
        return ToolExecLease(
            lease_id="l", session_id="s", contract_version="v",
            bound_steps=tuple(("t", "h") for _ in steps),
            issued_at_tick=0, expires_at_tick=10**9,
        )

    def submit_step(self, tool, args, lease, *, current_tick=0, risk=None):
        node = args.get("_node", tool)
        self.calls[node] = self.calls.get(node, 0) + 1
        if node in self.blocked:
            return _evidence(tool, success=False, blocked="policy: not in card scope")
        outcomes = self.script.get(node, [True])
        idx = min(self.calls[node] - 1, len(outcomes) - 1)
        return _evidence(tool, success=outcomes[idx])


def _graph_run():
    graph = build_patch_test_graph()
    run = create_workflow_run(graph)
    return graph, run


def _tasks():
    return {
        "patch": ("write_file", {"path": "calc.py", "content": "x", "_node": "patch"}),
        "test": ("run_tests", {"_node": "test"}),
    }


def test_flaky_node_recovers_within_budget():
    # patch always ok; test fails once then succeeds
    session = _ScriptedSession({"patch": [True], "test": [False, True]})
    graph, run = _graph_run()
    result = FlowDispatcher(session).dispatch(
        graph, run, _tasks(), session.issue_lease([]), retry_policy=DEFAULT_RETRY_POLICY
    )
    assert result.success is True
    assert result.lifecycle_status is WorkflowLifecycleStatus.COMPLETED
    test_step = [s for s in result.step_results if s.node_id == "test"][0]
    assert test_step.attempts == 2
    assert session.calls["test"] == 2


def test_unrecoverable_node_exhausts_and_pauses_with_proposal():
    session = _ScriptedSession({"patch": [True], "test": [False]})  # always fails
    graph, run = _graph_run()
    result = FlowDispatcher(session).dispatch(
        graph, run, _tasks(), session.issue_lease([]), retry_policy=DEFAULT_RETRY_POLICY
    )
    assert result.success is False
    assert result.paused is True
    assert result.lifecycle_status is WorkflowLifecycleStatus.PAUSED
    assert result.recovery_proposal is not None
    assert session.calls["test"] == DEFAULT_RETRY_POLICY.max_attempts


def test_policy_blocked_node_is_not_retried():
    session = _ScriptedSession({"patch": [True]}, blocked={"test"})
    graph, run = _graph_run()
    result = FlowDispatcher(session).dispatch(
        graph, run, _tasks(), session.issue_lease([]), retry_policy=DEFAULT_RETRY_POLICY
    )
    assert result.success is False
    assert result.lifecycle_status is WorkflowLifecycleStatus.FAILED
    assert result.recovery_proposal is None
    assert session.calls["test"] == 1  # blocked failures are never retried


def test_no_policy_is_single_shot():
    session = _ScriptedSession({"patch": [True], "test": [False, True]})
    graph, run = _graph_run()
    result = FlowDispatcher(session).dispatch(
        graph, run, _tasks(), session.issue_lease([])
    )
    # without a retry policy the failing test node fails the run on first attempt
    assert result.success is False
    assert result.lifecycle_status is WorkflowLifecycleStatus.FAILED
    assert session.calls["test"] == 1
