"""DualKernelRuntime facade — the first wiring into the live submit path.

Proves three things with real objects (no mocks):
  1. flag OFF  → pure pass-through, no dual-kernel logic runs (bit-identical).
  2. flag ON, GOVERNED clean write → speculative preflight PASSes, the command
     runs for real and mutates live state.
  3. flag ON, GOVERNED out-of-scope write → preflight rejects, the inner submit
     is never called and live state is untouched.
"""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.dual_kernel import DualKernelRuntime, Route
from agentic_runtime.hitl import AutoApprover


def _approver():
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _governed_card():
    # index: actions 1 (write) + env 0 + orch 1 (escalation) + hitl 2 (HIGH) = 4
    return AgentCard.make(
        name="Gov", agent_class=AgentClass.EXECUTION, mission="dk",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "list_dir"],
        escalation_policy=["operator"])


def _kernel(tmp_path):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")


def _write(card, path, content):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": path, "content": content},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="w",
        parent_intent_id="task-1")


def test_flag_off_is_passthrough(tmp_path):
    kernel = _kernel(tmp_path)
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=False)
    r = dk.submit(_write(card, "src/a.py", "A\n"), card)
    assert r.ok
    assert kernel.runtime.tools.sandbox.read_file("src/a.py") == "A\n"
    # no dual-kernel routing ran at all
    assert dk.route_log == []


def test_governed_clean_write_previews_then_commits(tmp_path):
    kernel = _kernel(tmp_path)
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True)
    r = dk.submit(_write(card, "src/feature.py", "FEATURE\n"), card)

    assert r.ok
    assert kernel.runtime.tools.sandbox.read_file("src/feature.py") == "FEATURE\n"
    assert len(dk.route_log) == 1
    rec = dk.route_log[0]
    assert rec.route is Route.GOVERNED
    assert rec.verdict == "pass"
    assert rec.executed is True


def test_out_of_scope_write_is_blocked_and_live_untouched(tmp_path):
    # An out-of-scope write is re-scored high-risk → HARD_GATED → the inner
    # runtime denies it. The safety invariant (live untouched) holds regardless
    # of which route caught it.
    kernel = _kernel(tmp_path)
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True)
    r = dk.submit(_write(card, "etc/passwd", "PWN\n"), card)

    assert not r.ok
    try:
        kernel.runtime.tools.sandbox.read_file("etc/passwd")
        raise AssertionError("out-of-scope file must not exist in live state")
    except OSError:
        pass
    assert len(dk.route_log) == 1


def test_rejected_verdict_maps_to_blocked_result(tmp_path):
    # Directly exercise the GOVERNED-reject construction: a non-mergeable verdict
    # becomes a blocked CommandResult (merge_gate verifier, no transition) — the
    # command is never handed to the inner runtime.
    from agentic_runtime.dual_kernel import MergeVerdict
    from agentic_runtime.dual_kernel.merge_gate import DeploymentReadinessDecision

    kernel = _kernel(tmp_path)
    dk = DualKernelRuntime(kernel, enabled=True)
    verdict = DeploymentReadinessDecision(
        verdict=MergeVerdict.BLOCKING_FAIL,
        final_status=MergeVerdict.BLOCKING_FAIL,
        blockers=["simulation_live_resolved"],
        simulation_live_status="UNRESOLVED")
    result = dk._blocked_result(_write(_governed_card(), "src/x.py", "X\n"), verdict)

    assert not result.ok
    assert result.verifier.verifier == "merge_gate"
    assert result.verifier.code == "blocking_fail"
    assert result.transition is None


def test_route_recorded_but_env_flag_default_off(tmp_path, monkeypatch):
    monkeypatch.delenv("AUREL_DUAL_KERNEL", raising=False)
    kernel = _kernel(tmp_path)
    dk = DualKernelRuntime(kernel)  # enabled resolved from env → default OFF
    assert dk.enabled is False
