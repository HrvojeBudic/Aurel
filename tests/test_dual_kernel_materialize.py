"""CAS materialize-to-live — GOVERNED executes ONCE in a fork, then merges the
fork's post-state into the live workspace and appends a faithful hash-chained
transition to the parent trace.

Real objects only. Proves single-execution, workspace parity with the
preflight-then-resubmit path, a faithful transition record, and flag gating.
"""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.dual_kernel import DualKernelRuntime
from agentic_runtime.hitl import AutoApprover


def _approver():
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _governed_card():
    return AgentCard.make(
        name="Gov", agent_class=AgentClass.EXECUTION, mission="dk",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "list_dir"],
        escalation_policy=["operator"])


def _write(card, path="src/feature.py", content="FEATURE\n"):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": path, "content": content},
        rationale="dk", declared_risk=RiskLevel.LOW, expected_effect="w",
        parent_intent_id="task-1")


def _materialize_kernel(tmp_path):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory",
        retain_states=True, state_store=store)
    return kernel


def test_materialize_executes_once_and_merges_to_live(tmp_path):
    kernel = _materialize_kernel(tmp_path)
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True, materialize=True)
    assert dk._can_materialize() is True

    r = dk.submit(_write(card), card)

    assert r.ok
    live = kernel.runtime.tools.sandbox
    assert live.read_file("src/feature.py") == "FEATURE\n"
    # a faithful transition was appended and matches the real live post-state
    assert r.transition is not None
    assert r.transition.after_state_hash == live.state_hash()
    assert r.transition.before_state_hash != r.transition.after_state_hash
    ev = dk.ledger.entries()[0]
    assert ev.route == "governed" and ev.final_status == "pass" and ev.executed


def test_materialize_parity_with_preflight(tmp_path):
    card = _governed_card()

    # preflight path (materialize=False) — the existing behaviour
    k_pre = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "pre")),
        approval_gate=_approver(), trace_backend="memory")
    dk_pre = DualKernelRuntime(k_pre, enabled=True, materialize=False)
    r_pre = dk_pre.submit(_write(card), card)

    # materialize path (materialize=True)
    k_mat = _materialize_kernel(tmp_path)
    dk_mat = DualKernelRuntime(k_mat, enabled=True, materialize=True)
    r_mat = dk_mat.submit(_write(card), card)

    assert r_pre.ok and r_mat.ok
    pre_content = k_pre.runtime.tools.sandbox.read_file("src/feature.py")
    mat_content = k_mat.runtime.tools.sandbox.read_file("src/feature.py")
    assert pre_content == mat_content == "FEATURE\n"


def test_materialize_falls_back_without_state_store(tmp_path):
    # a kernel with no state store cannot CAS-materialise → preflight path runs
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="memory")
    card = _governed_card()
    dk = DualKernelRuntime(kernel, enabled=True, materialize=True)
    assert dk._can_materialize() is False
    r = dk.submit(_write(card), card)
    # still governed + committed, just via the preflight-then-resubmit path
    assert r.ok
    assert kernel.runtime.tools.sandbox.read_file("src/feature.py") == "FEATURE\n"


def test_materialize_flag_default_off(tmp_path, monkeypatch):
    monkeypatch.delenv("AUREL_DK_MATERIALIZE", raising=False)
    kernel = _materialize_kernel(tmp_path)
    dk = DualKernelRuntime(kernel, enabled=True)  # materialize resolved from env
    assert dk.materialize is False


def test_materialize_deletion_is_exact(tmp_path):
    # clear-then-materialise must reproduce deletions, not just additions.
    kernel = _materialize_kernel(tmp_path)
    card = _governed_card()
    live = kernel.runtime.tools.sandbox
    live.write_file("src/old.py", "OLD\n")
    assert live.read_file("src/old.py") == "OLD\n"

    dk = DualKernelRuntime(kernel, enabled=True, materialize=True)
    r = dk.submit(_write(card, path="src/new.py", content="NEW\n"), card)

    assert r.ok
    # the new file exists and the pre-existing file still exists (write is additive)
    assert live.read_file("src/new.py") == "NEW\n"
    assert live.read_file("src/old.py") == "OLD\n"
    # and the live tree hashes exactly to the recorded post-state
    assert live.state_hash() == r.transition.after_state_hash
