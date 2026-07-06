"""M2 — WorldLineForest.checkout done-conditions.

Checkout must reconstruct the exact post-state of any persisted transition into a
fresh sandbox (state_hash == recorded after_state_hash), fail clearly on unknown
entries and un-retained states, and never mutate the source run.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    CheckoutError,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    WorldLineForest,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope, StateTransitionRecord
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.trace import PersistentTraceLedger


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="M2 Agent", agent_class=AgentClass.EXECUTION, mission="checkout test",
        authority=AuthorityScope(
            write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "run_tests", "list_dir"],
    )


def _cmd(card: AgentCard, tool: str, args: dict) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale="m2", declared_risk=RiskLevel.LOW, expected_effect="m2")


def _unsafe_factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


def _retained_run(tmp_path, contents: list[str]):
    """Build a retained run that writes src/a.py once per entry in ``contents``."""
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        retain_states=True,
        state_store=store,
    )
    card = _card()
    for i, c in enumerate(contents):
        r = kernel.runtime.submit(
            _cmd(card, "write_file", {"path": f"src/f{i}.py", "content": c}), card)
        assert r.ok
    kernel.trace.seal_run("completed")
    return kernel, trace_dir


def _transitions(kernel):
    return [e for e in kernel.trace if isinstance(e, StateTransitionRecord)]


def test_checkout_every_transition_reconstructs_recorded_state(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A1\n", "B2\n", "C3\n"])
    forest = WorldLineForest(trace_dir)
    run_id = kernel.trace.run_id

    transitions = _transitions(kernel)
    assert len(transitions) == 3
    src_ws = kernel.sandbox.root
    for rec in transitions:
        sbx = forest.checkout(run_id, rec.entry_hash, sandbox_factory=_unsafe_factory)
        assert sbx.state_hash() == rec.after_state_hash   # exact reconstruction
        assert sbx.root != src_ws                          # a genuinely fresh workspace


def test_checkout_unknown_entry_raises(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A1\n"])
    forest = WorldLineForest(trace_dir)

    with pytest.raises(CheckoutError):
        forest.checkout(kernel.trace.run_id, "not-a-real-entry-hash",
                        sandbox_factory=_unsafe_factory)


def test_checkout_unknown_run_raises(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A1\n"])
    forest = WorldLineForest(trace_dir)
    entry = _transitions(kernel)[0].entry_hash

    with pytest.raises(CheckoutError):
        forest.checkout("run_does_not_exist", entry, sandbox_factory=_unsafe_factory)


def test_checkout_unretained_state_gives_actionable_error(tmp_path):
    # Flag OFF: the transition is persisted, but its state was never sent to CAS.
    trace_dir = str(tmp_path / "traces")
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        retain_states=False,
    )
    card = _card()
    r = kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A1\n"}), card)
    assert r.ok
    kernel.trace.seal_run("completed")

    forest = WorldLineForest(trace_dir)
    with pytest.raises(CheckoutError) as ei:
        forest.checkout(kernel.trace.run_id, r.transition.entry_hash,
                        sandbox_factory=_unsafe_factory)
    assert "retain_states=True" in str(ei.value)   # actionable


def test_checkout_does_not_mutate_source_run(tmp_path):
    kernel, trace_dir = _retained_run(tmp_path, ["A1\n", "B2\n"])
    forest = WorldLineForest(trace_dir)
    run_id = kernel.trace.run_id
    run_dir = Path(trace_dir) / "runs" / run_id
    states_dir = Path(trace_dir) / "states"

    events_before = (run_dir / "events.jsonl").read_bytes()
    meta_before = (run_dir / "metadata.json").read_bytes()
    states_before = sorted(p.name for p in states_dir.iterdir())
    ws_files_before = sorted(UnsafeLocalSandbox(root=kernel.sandbox.root).list_dir("src"))

    for rec in _transitions(kernel):
        forest.checkout(run_id, rec.entry_hash, sandbox_factory=_unsafe_factory)

    assert (run_dir / "events.jsonl").read_bytes() == events_before   # trace byte-identical
    assert (run_dir / "metadata.json").read_bytes() == meta_before
    assert sorted(p.name for p in states_dir.iterdir()) == states_before  # no new CAS nodes
    assert sorted(UnsafeLocalSandbox(root=kernel.sandbox.root).list_dir("src")) == ws_files_before

    # re-verify the persisted chain from a fresh reader
    assert PersistentTraceLedger(base_dir=trace_dir, run_id=run_id).verify_persisted()["ok"]
