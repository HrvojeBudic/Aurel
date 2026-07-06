"""Praxis orchestrator — real fork → execute → gate → commit-or-discard.

No mocks: every run forks a genuine WorldLineForest, executes the command in the
fork through a real runtime (which executes AND verifies against real state), and
lets the merge gate decide. Proves the end-to-end governed speculative primitive
works and that a rejected fork never reaches live state.
"""
from __future__ import annotations

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    WorldLineForest,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope, Intent
from agentic_runtime.dual_kernel import (
    MergeVerdict,
    Praxis,
    SigmaGovernor,
)
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.policy import PolicyDecision, PolicyVerdict
from agentic_runtime.worldline import _read_tree


def _approver():
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _card():
    return AgentCard.make(
        name="Praxis", agent_class=AgentClass.EXECUTION, mission="praxis",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "list_dir"])


def _sigma(card):
    gov = SigmaGovernor()
    s = gov.register_task(card, Intent.make("feature"))
    return s.update(
        CommandEnvelope.make(issuer_card_id=card.id, tool="write_file",
                             args={"path": "src/feature.py", "content": "F\n"},
                             rationale="p", declared_risk=RiskLevel.LOW,
                             expected_effect="f"),
        PolicyDecision(verdict=PolicyVerdict.ALLOW, risk=RiskLevel.LOW, reasons=[]))


def _parent(tmp_path):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(), trace_backend="persistent",
        trace_dir=trace_dir, retain_states=True, state_store=store)
    card = _card()
    base = CommandEnvelope.make(issuer_card_id=card.id, tool="write_file",
                                args={"path": "src/base.py", "content": "BASE\n"},
                                rationale="p", declared_risk=RiskLevel.LOW,
                                expected_effect="base")
    r = kernel.runtime.submit(base, card)
    assert r.ok
    kernel.trace.seal_run("completed")
    forest = WorldLineForest(trace_dir)
    praxis = Praxis(forest, trace_dir=trace_dir, state_store=store,
                    approver=_approver())
    return praxis, forest, kernel.trace.run_id, r.transition.entry_hash, card


def test_execute_governed_merges_clean_write(tmp_path):
    praxis, forest, parent_id, entry, card = _parent(tmp_path)
    cmd = CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "src/feature.py", "content": "FEATURE\n"},
        rationale="p", declared_risk=RiskLevel.LOW, expected_effect="feature")

    out = praxis.execute_governed(
        parent_run_id=parent_id, entry_hash=entry, cmd=cmd, card=card,
        sigma=_sigma(card))

    assert out.child_ok is True
    assert out.decision.final_status is MergeVerdict.PASS
    assert out.merged is True
    assert out.merge_result is not None and out.merge_result.clean
    # live merged state actually contains the speculative write
    tree = _read_tree(forest.store, out.merge_result.merged_state_hash)
    assert tree.get("src/feature.py") in ("FEATURE\n", b"FEATURE\n")
    assert len(forest.merges()) == 1


def test_execute_governed_discards_rejected_fork(tmp_path):
    praxis, forest, parent_id, entry, card = _parent(tmp_path)
    # write OUTSIDE the card's authorised scope → policy denies in the fork →
    # child_ok False, verification fails → gate blocks → fork discarded.
    cmd = CommandEnvelope.make(
        issuer_card_id=card.id, tool="write_file",
        args={"path": "etc/passwd", "content": "PWN\n"},
        rationale="p", declared_risk=RiskLevel.LOW, expected_effect="escape")

    out = praxis.execute_governed(
        parent_run_id=parent_id, entry_hash=entry, cmd=cmd, card=card,
        sigma=_sigma(card))

    assert out.child_ok is False
    assert out.merged is False
    assert out.merge_result is None
    assert forest.merges() == []  # live state provably untouched
