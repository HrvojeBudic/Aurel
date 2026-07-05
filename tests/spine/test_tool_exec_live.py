"""SPINE-LIVE-1 tests — governed mutating path (write + test) with the gate."""

from __future__ import annotations

import pytest

from agentic_runtime import AutoApprover, UnsafeLocalSandbox, build_runtime
from agentic_runtime.core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
)
from agentic_runtime.spine import (
    SpineExecutionBlocked,
    SpineToolExecSession,
    ToolExecEvidenceRef,
)

_ORIGINAL = "VALUE = 1\n"
_PATCHED = "VALUE = 2\n"


class _FakeHardSandbox(UnsafeLocalSandbox):
    """Test-only backend: real file IO + run_shell, reported as hard-isolated.

    Stands in for a real Bubblewrap/Docker boundary so the gate's happy path is
    testable without bwrap/docker present in CI.
    """

    def __init__(self, root: str | None = None) -> None:
        super().__init__(root)
        self.is_hard_isolated = True
        self.is_security_boundary = True


def _card() -> AgentCard:
    return AgentCard.make(
        name="Spine Surgeon",
        agent_class=AgentClass.EXECUTION,
        mission="SPINE-LIVE governed mutating path",
        authority=AuthorityScope(
            write_paths=["calc.py", "test_calc.py"],
            read_paths=["*"],
            allow_network=False,
            allow_secrets=False,
            max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=["read_file", "write_file", "run_tests", "list_dir"],
        denied_tools=["network_fetch", "delete_file"],
        model_profile="balanced",
    )


def _kernel(sandbox):
    # Allow every risk class in tests so the approval gate never masks the
    # spine gate under test; write_file/run_tests are R2+ by default.
    return build_runtime(
        sandbox=sandbox,
        approval_gate=AutoApprover(
            lambda r: True,
            allow_r2=True,
            allow_r3=True,
            allow_r4=True,
            allow_r5=True,
        ),
    )


def _seed(kernel, content: str = _ORIGINAL) -> None:
    kernel.sandbox.write_file("calc.py", content)


def _session(kernel):
    return SpineToolExecSession(kernel.runtime, _card())


# --------------------------------------------------------------------------- #
#  The security gate
# --------------------------------------------------------------------------- #
def test_mutating_tool_without_hard_isolation_is_blocked():
    kernel = _kernel(UnsafeLocalSandbox())
    _seed(kernel)
    sess = _session(kernel)
    lease = sess.issue_lease([("write_file", {"path": "calc.py", "content": _PATCHED})])
    with pytest.raises(SpineExecutionBlocked, match="hard-isolated"):
        sess.submit_step("write_file", {"path": "calc.py", "content": _PATCHED}, lease)
    # fail-closed: the block performed nothing
    assert kernel.sandbox.read_file("calc.py") == _ORIGINAL


def test_tool_or_args_not_in_lease_is_blocked():
    kernel = _kernel(_FakeHardSandbox())
    _seed(kernel)
    sess = _session(kernel)
    lease = sess.issue_lease([("write_file", {"path": "calc.py", "content": _PATCHED})])
    # different args → not the leased (tool, args-hash) pair
    with pytest.raises(SpineExecutionBlocked, match="does not permit"):
        sess.submit_step("write_file", {"path": "calc.py", "content": "OTHER"}, lease)


# --------------------------------------------------------------------------- #
#  Live write with evidence
# --------------------------------------------------------------------------- #
def test_hard_isolated_write_succeeds_with_evidence():
    kernel = _kernel(_FakeHardSandbox())
    _seed(kernel)
    sess = _session(kernel)
    args = {"path": "calc.py", "content": _PATCHED}
    lease = sess.issue_lease([("write_file", args)])
    ev: ToolExecEvidenceRef = sess.submit_step("write_file", args, lease)
    assert ev.available is True
    assert ev.success is True
    assert ev.runtime_submit_called is True
    assert ev.command_id
    assert ev.before_state_hash != ev.after_state_hash
    assert kernel.sandbox.read_file("calc.py") == _PATCHED


def test_evidence_grants_no_authority():
    kernel = _kernel(_FakeHardSandbox())
    _seed(kernel)
    sess = _session(kernel)
    args = {"path": "calc.py", "content": _PATCHED}
    lease = sess.issue_lease([("write_file", args)])
    ev = sess.submit_step("write_file", args, lease)
    assert ev.authority_granted is False
    assert ev.permission_granted is False
    assert lease.authority_granted is False
    assert lease.permission_granted is False


# --------------------------------------------------------------------------- #
#  Multi-step run
# --------------------------------------------------------------------------- #
def test_multi_step_run_all_succeed_execution_available():
    kernel = _kernel(_FakeHardSandbox())
    _seed(kernel)
    sess = _session(kernel)
    steps = [
        ("write_file", {"path": "calc.py", "content": _PATCHED}),
        ("run_tests", {"command": ["python3", "-c", "import sys; sys.exit(0)"]}),
    ]
    lease = sess.issue_lease(steps)
    run = sess.run(lease, steps)
    assert run.success is True
    assert run.reverted is False
    assert run.execution_available is True
    assert len(run.step_evidence) == 2
    assert all(e.available for e in run.step_evidence)
    assert run.hard_isolation.available is True
    assert kernel.sandbox.read_file("calc.py") == _PATCHED


def test_failing_step_triggers_revert():
    kernel = _kernel(_FakeHardSandbox())
    _seed(kernel, _ORIGINAL)
    sess = _session(kernel)
    steps = [
        ("write_file", {"path": "calc.py", "content": _PATCHED}),
        ("run_tests", {"command": ["python3", "-c", "import sys; sys.exit(1)"]}),
    ]
    lease = sess.issue_lease(steps)
    run = sess.run(lease, steps, revert_on_failure=True)
    assert run.success is False
    assert run.reverted is True
    # both steps really ran through the kernel (submits happened)
    assert len(run.step_evidence) == 2
    assert run.step_evidence[0].success is True
    assert run.step_evidence[1].success is False
    # the compensating revert restored the original content
    assert kernel.sandbox.read_file("calc.py") == _ORIGINAL


# --------------------------------------------------------------------------- #
#  Read-only tools need no isolation (gate is scoped to mutating tools)
# --------------------------------------------------------------------------- #
def test_read_only_tool_needs_no_isolation():
    kernel = _kernel(UnsafeLocalSandbox())  # not hard-isolated
    _seed(kernel)
    sess = _session(kernel)
    args = {"path": "calc.py"}
    lease = sess.issue_lease([("read_file", args)])
    ev = sess.submit_step("read_file", args, lease, risk=RiskLevel.LOW)
    assert ev.runtime_submit_called is True
    assert ev.success is True
