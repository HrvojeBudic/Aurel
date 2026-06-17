"""P0.7 runtime state machine and failure semantics tests."""

from __future__ import annotations

import json

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    ExecutionStatus,
    InMemoryTraceLedger,
    Intent,
    RiskLevel,
    RuntimeStateMachine,
    build_runtime,
)
from tests.conftest import bounded_test_approver
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_router import MockModelClient
from agentic_runtime.sandbox import ExecResult, UnsafeLocalSandbox


def _card(**kw):
    defaults = dict(
        name="Stateful Agent",
        agent_class=AgentClass.EXECUTION,
        mission="p07 tests",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "edit_file", "run_tests", "run_shell", "list_dir"],
        denied_tools=[],
    )
    defaults.update(kw)
    return AgentCard.make(**defaults)


def _kernel(tmp_path, *, scripted: dict, approver=None, sandbox=None):
    return build_runtime(
        sandbox=sandbox or UnsafeLocalSandbox(root=str(tmp_path)),
        model_clients={"balanced": [MockModelClient(scripted=scripted)]},
        approval_gate=approver or bounded_test_approver(
            lambda r: r.command.tool in {"run_tests", "edit_file", "write_file"},
        ),
    )


def test_legal_transitions_persisted():
    trace = InMemoryTraceLedger(run_id="run_test_legal")
    sm = RuntimeStateMachine(trace=trace, run_id="run_test_legal", intent_id="intent_x", agent_id="card_x")
    sm.transition(ExecutionStatus.PLANNING, "planning", "planning")
    sm.transition(ExecutionStatus.PLANNED, "planned", "planned")
    sm.transition(ExecutionStatus.RUNNING, "running", "running")
    sm.transition(ExecutionStatus.COMPLETED, "done", "completed")

    assert sm.status is ExecutionStatus.COMPLETED
    rows = list(trace.replay())
    state_rows = [r for r in rows if r.get("kind") == "runtime_status_transition"]
    assert len(state_rows) == 5  # created + 4 transitions
    assert trace.verify_chain()[0]


def test_illegal_transition_rejected():
    trace = InMemoryTraceLedger(run_id="run_test_illegal")
    sm = RuntimeStateMachine(trace=trace, run_id="run_test_illegal", intent_id="intent_x", agent_id="card_x")
    with pytest.raises(ValueError):
        sm.transition(ExecutionStatus.COMPLETED, "illegal", "cannot jump")
    sm.transition(ExecutionStatus.PLANNING, "planning", "planning")
    sm.transition(ExecutionStatus.PLANNED, "planned", "planned")
    with pytest.raises(ValueError):
        sm.transition(ExecutionStatus.COMPLETED, "illegal", "cannot skip running")


def test_policy_denial_returns_rejected(tmp_path):
    goal = "policy denied plan"
    plan = {
        "plan": [
            {"tool": "edit_file", "args": {"path": "/etc/passwd", "find": "a", "replace": "b"}, "reason": "bad"}
        ]
    }
    kernel = _kernel(tmp_path, scripted={goal: json.dumps(plan)})
    card = _card(authority=AuthorityScope(write_paths=["src/"], max_risk=RiskLevel.HIGH))
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == ExecutionStatus.REJECTED.value
    assert report["reason_code"] == "policy_denied"


def test_needs_human_when_approval_required(tmp_path):
    goal = "approval needed"
    plan = {"plan": [{"tool": "run_tests", "args": {"test_file": "test_ok.py"}, "reason": "verify"}]}
    kernel = _kernel(
        tmp_path,
        scripted={goal: json.dumps(plan)},
        approver=AutoApprover(lambda r: False),
    )
    kernel.sandbox.write_file("test_ok.py", "assert True\n")
    card = _card(authority=AuthorityScope(write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.MEDIUM))
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == ExecutionStatus.NEEDS_HUMAN.value
    assert report["reason_code"] in {"needs_human_approval", "needs_human_after_partial_execution"}


class _BrokenSandbox(UnsafeLocalSandbox):
    def run_shell(self, cmd: list[str], timeout: float = 10.0) -> ExecResult:  # pragma: no cover - deterministic
        return ExecResult(
            exit_code=127,
            stdout="",
            stderr="sandbox error: blocked",
            timed_out=False,
            truncated=False,
            fs_diff={},
            sandbox_mode=self.mode.value,
            error_kind="sandbox_error",
        )


def test_sandbox_failure_returns_failed(tmp_path):
    goal = "sandbox fails"
    plan = {"plan": [{"tool": "run_shell", "args": {"cmd": ["python3", "-V"]}, "reason": "probe"}]}
    kernel = _kernel(
        tmp_path,
        scripted={goal: json.dumps(plan)},
        sandbox=_BrokenSandbox(root=str(tmp_path)),
        approver=bounded_test_approver(lambda r: r.command.tool == "run_shell", allow_r4=True),
    )
    card = _card(authority=AuthorityScope(write_paths=["."], read_paths=["*"], max_risk=RiskLevel.HIGH))
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] in {
        ExecutionStatus.FAILED.value,
        ExecutionStatus.HALTED.value,
    }
    assert report["reason_code"] == "sandbox_failure"


def test_verifier_failure_rolls_back_and_sets_verification_failed(tmp_path):
    goal = "verifier fail"
    plan = {
        "plan": [
            {
                "tool": "run_shell",
                "args": {"cmd": ["python3", "-c", "open('test_x.py','w').write('x')"]},
                "reason": "introduce protected mutation",
            }
        ]
    }
    kernel = _kernel(
        tmp_path,
        scripted={goal: json.dumps(plan)},
        approver=bounded_test_approver(lambda r: r.command.tool == "run_shell", allow_r4=True),
    )
    kernel.verifier.test_integrity.snapshot()
    card = _card(authority=AuthorityScope(write_paths=["."], read_paths=["*"], max_risk=RiskLevel.HIGH))
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == ExecutionStatus.VERIFICATION_FAILED.value
    assert report["reason_code"] == "verification_failed"
    assert "test_x.py" not in kernel.sandbox.list_dir(".")


def test_partial_execution_never_reports_completed(tmp_path):
    goal = "partial run"
    plan = {
        "plan": [
            {"tool": "write_file", "args": {"path": "src/a.py", "content": "x\n"}, "reason": "first"},
            {"tool": "edit_file", "args": {"path": "/etc/passwd", "find": "a", "replace": "b"}, "reason": "second"},
        ]
    }
    kernel = _kernel(tmp_path, scripted={goal: json.dumps(plan)})
    card = _card(authority=AuthorityScope(write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH))
    report = kernel.spawn(card).run(Intent.make(goal))
    assert report["status"] == ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION.value
    assert report["actions_executed"] == 1


def test_successful_completion_has_outcome_shape_and_trace_refs(tmp_path):
    goal = "successful run"
    plan = {"plan": [{"tool": "write_file", "args": {"path": "src/a.py", "content": "ok\n"}, "reason": "write"}]}
    kernel = _kernel(tmp_path, scripted={goal: json.dumps(plan)})
    card = _card(authority=AuthorityScope(write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH))
    report = kernel.spawn(card).run(Intent.make(goal))

    assert report["status"] == ExecutionStatus.COMPLETED.value
    assert report["reason_code"] == "run_completed"
    assert report["run_id"] == kernel.trace.run_id
    assert report["trace_refs"]["run_id"] == kernel.trace.run_id
    assert report["trace_refs"]["last_transition_id"]
    assert isinstance(report["evidence_refs"], list)

    rows = list(kernel.trace.replay())
    assert any(r.get("kind") == "runtime_status_transition" for r in rows)
