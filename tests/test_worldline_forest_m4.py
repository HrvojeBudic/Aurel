"""M4 — forest integrity, reachability GC, named branches (T7–T9).

verify_fork checks C1–C7 for a lineage edge; WorldLineForest.verify walks every
run + every fork topologically and returns a forest_root. gc keeps every fork's
parent-state reachable so collecting never orphans a retained lineage; a parent
state that was never retained (or forcibly lost) makes the fork UNVERIFIABLE
rather than silently OK. A plain linear run is byte-for-byte today.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    WorldLineForest,
    build_runtime,
    verify_fork,
)
from agentic_runtime.core_types import CommandEnvelope, StateTransitionRecord
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.trace import GENESIS, PersistentTraceLedger

_META_KEYS_TODAY = {
    "run_id", "status", "final_status", "started_at",
    "updated_at", "checkpoint_every", "genesis_hash",
}


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="M4 Agent", agent_class=AgentClass.EXECUTION, mission="forest test",
        authority=AuthorityScope(
            write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "run_tests", "list_dir"],
    )


def _cmd(card: AgentCard, tool: str, args: dict) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale="m4", declared_risk=RiskLevel.LOW, expected_effect="m4")


def _factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


def _run(trace_dir, store, sandbox, contents, run_id=None):
    kernel = build_runtime(
        sandbox=sandbox,
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        trace_run_id=run_id,
        retain_states=True,
        state_store=store,
    )
    card = _card()
    for i, c in enumerate(contents):
        r = kernel.runtime.submit(
            _cmd(card, "write_file", {"path": f"src/f{i}.py", "content": c}), card)
        assert r.ok
    kernel.trace.seal_run("completed")
    return kernel


def _transitions(kernel):
    return [e for e in kernel.trace if isinstance(e, StateTransitionRecord)]


def _parent_with_two_children(tmp_path):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    parent = _run(trace_dir, store, UnsafeLocalSandbox(root=str(tmp_path / "ws")),
                  ["A1\n", "B2\n", "C3\n"])
    forest = WorldLineForest(trace_dir)
    ptrans = _transitions(parent)
    # two duplicate sibling forks from the SAME parent transition
    a = forest.fork(parent.trace.run_id, ptrans[1].entry_hash, sandbox_factory=_factory)
    b = forest.fork(parent.trace.run_id, ptrans[1].entry_hash, sandbox_factory=_factory)
    _run(trace_dir, store, a.sandbox, ["X1\n"], run_id=a.child_run_id)
    _run(trace_dir, store, b.sandbox, ["Y1\n"], run_id=b.child_run_id)
    return trace_dir, store, forest, parent, a, b, ptrans


# --------------------------------------------------------------------------- #
# T7 — duplicate sibling forks both verify; their shared parent state survives GC.
# --------------------------------------------------------------------------- #
def test_t7_sibling_forks_verify_and_parent_survives_gc(tmp_path):
    trace_dir, store, forest, _parent, a, b, ptrans = _parent_with_two_children(tmp_path)

    shared_parent_state = ptrans[1].after_state_hash
    assert a.fork_ref.parent_state_hash == shared_parent_state
    assert b.fork_ref.parent_state_hash == shared_parent_state
    assert a.fork_ref.fork_hash != b.fork_ref.fork_hash          # distinct edges (ids differ)

    edges = forest.forks()
    assert len(edges) == 2
    for e in edges:
        assert verify_fork(e, trace_dir, store)["ok"]
    v = forest.verify()
    assert v["ok"] and v["fork_count"] == 2 and v["forest_root"]

    # GC keeps the shared parent state (it is a live fork parent), and both
    # sibling forks still verify afterwards.
    assert shared_parent_state in forest.live_states()
    forest.gc()
    assert store.has(shared_parent_state)
    for e in forest.forks():
        assert verify_fork(e, trace_dir, store)["ok"]
    assert forest.verify()["ok"]


# --------------------------------------------------------------------------- #
# T8 — a parent state that is gone (GC'd / never retained) => UNVERIFIABLE.
# --------------------------------------------------------------------------- #
def test_t8_missing_parent_state_is_unverifiable_not_silently_ok(tmp_path):
    trace_dir, store, forest, _parent, a, _b, _pt = _parent_with_two_children(tmp_path)

    edge = next(e for e in forest.forks() if e["fork_id"] == a.fork_ref.fork_id)
    assert verify_fork(edge, trace_dir, store)["ok"]            # healthy first

    # Forcibly lose the parent CAS node (models aggressive external GC or a run
    # that never retained states). Verification must FAIL loudly at C3.
    parent_state = edge["parent_state_hash"]
    shutil.rmtree(Path(trace_dir) / "states" / parent_state)

    res = verify_fork(edge, trace_dir, store)
    assert res["ok"] is False                                   # not silently OK
    assert res["failed_check"] == "C3"
    assert "UNVERIFIABLE" in res["reason"]
    # and the whole-forest verify surfaces it too
    fv = forest.verify()
    assert fv["ok"] is False and fv["stage"] == "fork"


# --------------------------------------------------------------------------- #
# T9 — a plain linear run (no retain, no fork) is byte-for-byte today.
# --------------------------------------------------------------------------- #
def test_t9_linear_default_is_unchanged(tmp_path):
    trace_dir = str(tmp_path / "traces")
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        retain_states=False,          # default off — the untouched main line
    )
    card = _card()
    kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A1\n"}), card)
    kernel.runtime.submit(_cmd(card, "write_file", {"path": "src/a.py", "content": "A2\n"}), card)
    kernel.trace.seal_run("completed")
    run_id = kernel.trace.run_id

    # metadata schema is exactly today's: genesis on GENESIS, no forked keys
    md = json.loads(
        (Path(trace_dir) / "runs" / run_id / "metadata.json").read_text(encoding="utf-8"))
    assert set(md.keys()) == _META_KEYS_TODAY
    assert md["genesis_hash"] == GENESIS
    assert "initial_state_hash" not in md

    # no forest side-files or CAS ever appear for a plain run
    assert not (Path(trace_dir) / "forks.jsonl").exists()
    assert not (Path(trace_dir) / "branches.jsonl").exists()
    assert not (Path(trace_dir) / "states").exists()

    # the run still verifies from GENESIS (genesis-threading is a no-op when off)
    assert PersistentTraceLedger(base_dir=trace_dir, run_id=run_id).verify_persisted()["ok"]

    # a forest over a fork-free base has no edges; its root is just the run head
    forest = WorldLineForest(trace_dir)
    assert forest.forks() == []
    assert forest.verify()["ok"]
    events = list((Path(trace_dir) / "runs" / run_id / "events.jsonl")
                  .read_text(encoding="utf-8").splitlines())
    head = json.loads(events[-1])["entry_hash"]
    assert forest.forest_root() == head            # single leaf folds to itself
