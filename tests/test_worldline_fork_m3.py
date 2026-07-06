"""M3 — forkable lineage done-conditions (T1–T6).

A fork mints a NEW child run bound to a parent transition by a cryptographic
``ForkRef``. Parent and child each verify as independent linear chains; the
fork edge (persisted to ``forks.jsonl``) is the tamper-evident glue. The child
run's event chain hangs from a forked genesis ``sha(GENESIS, fork_hash)`` and
its metadata records exactly that genesis, so tampering either the edge or the
child's genesis is detectable.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    ForkRef,
    RiskLevel,
    StateStore,
    UnsafeLocalSandbox,
    WorldLineForest,
    build_runtime,
)
from agentic_runtime.core_types import CommandEnvelope, StateTransitionRecord
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.trace import GENESIS, PersistentTraceLedger


def _approver() -> AutoApprover:
    return AutoApprover(
        lambda r: True, allow_r2=True, allow_r3=True, allow_r4=True, allow_r5=True
    )


def _card() -> AgentCard:
    return AgentCard.make(
        name="M3 Agent", agent_class=AgentClass.EXECUTION, mission="fork test",
        authority=AuthorityScope(
            write_paths=["src/"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "run_tests", "list_dir"],
    )


def _cmd(card: AgentCard, tool: str, args: dict) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale="m3", declared_risk=RiskLevel.LOW, expected_effect="m3")


def _factory(root: str) -> UnsafeLocalSandbox:
    return UnsafeLocalSandbox(root=root)


def _retained_run(trace_dir: str, store: StateStore, ws_root: str, contents):
    """Build + seal a retained run writing one file per entry in ``contents``."""
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=ws_root),
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
    return kernel


def _drive_child(trace_dir, store, res, contents):
    """Continue a forked child run through the normal runtime and seal it."""
    kernel = build_runtime(
        sandbox=res.sandbox,
        approval_gate=_approver(),
        trace_backend="persistent",
        trace_dir=trace_dir,
        trace_run_id=res.child_run_id,
        retain_states=True,
        state_store=store,
    )
    card = _card()
    for i, c in enumerate(contents):
        r = kernel.runtime.submit(
            _cmd(card, "write_file", {"path": f"src/c{i}.py", "content": c}), card)
        assert r.ok
    kernel.trace.seal_run("completed")
    return kernel


def _transitions(kernel):
    return [e for e in kernel.trace if isinstance(e, StateTransitionRecord)]


def _verify(trace_dir, run_id) -> dict:
    return PersistentTraceLedger(base_dir=trace_dir, run_id=run_id).verify_persisted()


def _run_meta(trace_dir, run_id) -> dict:
    return json.loads(
        (Path(trace_dir) / "runs" / run_id / "metadata.json").read_text(encoding="utf-8"))


def _edge_binds(trace_dir, edge: dict) -> bool:
    """The M3 lineage invariant: an edge's recomputed child_genesis must equal
    the genesis its child run actually chains from (recorded in child metadata)."""
    ref = ForkRef.from_dict(edge)
    child_md = _run_meta(trace_dir, edge["child_run_id"])
    return ref.child_genesis_hash == child_md["genesis_hash"]


def _build_forked(tmp_path):
    """parent (3 transitions) + child forked at parent's 2nd transition (2 more)."""
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    parent = _retained_run(trace_dir, store, str(tmp_path / "ws"), ["A1\n", "B2\n", "C3\n"])
    forest = WorldLineForest(trace_dir)
    ptrans = _transitions(parent)
    res = forest.fork(parent.trace.run_id, ptrans[1].entry_hash, sandbox_factory=_factory)
    child = _drive_child(trace_dir, store, res, ["X9\n", "Y8\n"])
    return trace_dir, store, forest, parent, res, child


# --------------------------------------------------------------------------- #
# T1 — parent AND child each verify as independent linear chains.
# --------------------------------------------------------------------------- #
def test_t1_parent_and_child_verify_independently(tmp_path):
    trace_dir, _store, _forest, parent, res, child = _build_forked(tmp_path)

    assert _verify(trace_dir, parent.trace.run_id)["ok"]
    assert _verify(trace_dir, res.child_run_id)["ok"]

    # the child chains from the forked genesis, not GENESIS
    child_md = _run_meta(trace_dir, res.child_run_id)
    assert child_md["genesis_hash"] == res.fork_ref.child_genesis_hash
    assert child_md["genesis_hash"] != GENESIS
    # the parent chains from GENESIS (unchanged main line)
    assert _run_meta(trace_dir, parent.trace.run_id)["genesis_hash"] == GENESIS


# --------------------------------------------------------------------------- #
# T2 — the fork edge verifies: recomputed hashes match stored + bind the child.
# --------------------------------------------------------------------------- #
def test_t2_fork_edge_verifies(tmp_path):
    trace_dir, _store, forest, _parent, res, _child = _build_forked(tmp_path)

    edges = forest.forks()
    assert len(edges) == 1
    edge = edges[0]

    ref = ForkRef.from_dict(edge)
    assert ref.fork_hash == edge["fork_hash"]                    # derived-from-stored
    assert ref.child_genesis_hash == edge["child_genesis_hash"]
    assert ref.child_genesis_hash == res.fork_ref.child_genesis_hash
    assert _edge_binds(trace_dir, edge)                          # binds to child run


# --------------------------------------------------------------------------- #
# T3 — tampering the fork edge is detected (binding breaks).
# --------------------------------------------------------------------------- #
def test_t3_tampered_fork_edge_detected(tmp_path):
    trace_dir, _store, forest, _parent, _res, _child = _build_forked(tmp_path)
    forks_path = Path(trace_dir) / "forks.jsonl"

    edge = forest.forks()[0]
    assert _edge_binds(trace_dir, edge)                          # authentic first

    # Flip the parent_state_hash the edge claims to branch from. Even if an
    # attacker also recomputes the stored derived hashes to be self-consistent,
    # the edge no longer recomputes to the genesis the child actually chains from.
    tampered = dict(edge)
    tampered["parent_state_hash"] = "0" * 64
    tampered_ref = ForkRef.from_dict(tampered)
    tampered["fork_hash"] = tampered_ref.fork_hash               # self-consistent forgery
    tampered["child_genesis_hash"] = tampered_ref.child_genesis_hash
    forks_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")

    reloaded = forest.forks()[0]
    assert not _edge_binds(trace_dir, reloaded)                  # binding to child broken


# --------------------------------------------------------------------------- #
# T4 — tampering the child's genesis is detected at the first event (index 0).
# --------------------------------------------------------------------------- #
def test_t4_tampered_child_genesis_breaks_chain_at_index_0(tmp_path):
    trace_dir, _store, _forest, _parent, res, _child = _build_forked(tmp_path)

    assert _verify(trace_dir, res.child_run_id)["ok"]

    md_path = Path(trace_dir) / "runs" / res.child_run_id / "metadata.json"
    md = json.loads(md_path.read_text(encoding="utf-8"))
    md["genesis_hash"] = "f" * 64                                # forge the forked genesis
    md_path.write_text(json.dumps(md, indent=2, sort_keys=True), encoding="utf-8")

    report = _verify(trace_dir, res.child_run_id)
    assert report["ok"] is False
    assert report["broken_index"] == 0                          # first event no longer chains


# --------------------------------------------------------------------------- #
# T5 — fork-of-a-fork: a tampered ancestor edge fails the transitive lineage.
# --------------------------------------------------------------------------- #
def test_t5_fork_of_fork_transitive_tamper_fails(tmp_path):
    trace_dir, store, forest, parent, res, child = _build_forked(tmp_path)

    # grandchild forked from a transition in the child run
    ctrans = _transitions(child)
    gres = forest.fork(child.trace.run_id, ctrans[0].entry_hash, sandbox_factory=_factory)
    _drive_child(trace_dir, store, gres, ["Z1\n"])

    edges = {e["child_run_id"]: e for e in forest.forks()}
    assert len(edges) == 2
    child_edge = edges[res.child_run_id]           # parent -> child (the ancestor)
    grand_edge = edges[gres.child_run_id]          # child  -> grandchild

    def lineage_ok(edge) -> bool:
        """Walk grandchild -> root: every edge must bind and every run verify."""
        seen = set()
        while edge is not None:
            if not _edge_binds(trace_dir, edge):
                return False
            if not _verify(trace_dir, edge["parent_run_id"])["ok"]:
                return False
            seen.add(edge["child_run_id"])
            edge = edges.get(edge["parent_run_id"])
            if edge is not None and edge["child_run_id"] in seen:
                return False                        # cycle guard
        return True

    assert lineage_ok(grand_edge)                   # authentic lineage passes

    # Tamper the ANCESTOR edge (parent -> child); the grandchild is untouched but
    # its transitive lineage must now fail at the broken ancestor link.
    child_edge["parent_state_hash"] = "0" * 64
    forks_path = Path(trace_dir) / "forks.jsonl"
    forks_path.write_text(
        "\n".join(json.dumps(edges[cid]) for cid in
                  (res.child_run_id, gres.child_run_id)) + "\n", encoding="utf-8")
    edges = {e["child_run_id"]: e for e in forest.forks()}
    grand_edge = edges[gres.child_run_id]

    assert not lineage_ok(grand_edge)               # transitive tamper detected


# --------------------------------------------------------------------------- #
# T6 — fork-from-genesis via the parent's recorded initial_state_hash.
# --------------------------------------------------------------------------- #
def test_t6_fork_from_genesis(tmp_path):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    parent = _retained_run(trace_dir, store, str(tmp_path / "ws"), ["A1\n", "B2\n"])
    forest = WorldLineForest(trace_dir)

    res = forest.fork(parent.trace.run_id, GENESIS, sandbox_factory=_factory)

    # the child branches from the parent's genesis world-state (M1 initial_state_hash)
    parent_md = _run_meta(trace_dir, parent.trace.run_id)
    assert res.fork_ref.parent_entry_hash == GENESIS
    assert res.fork_ref.parent_state_hash == parent_md["initial_state_hash"]
    # the materialized child workspace hashes to that genesis state
    assert res.sandbox.state_hash() == parent_md["initial_state_hash"]

    child = _drive_child(trace_dir, store, res, ["N1\n"])
    assert _verify(trace_dir, res.child_run_id)["ok"]
    assert _edge_binds(trace_dir, forest.forks()[0])
    assert _run_meta(trace_dir, child.trace.run_id)["genesis_hash"] == res.fork_ref.child_genesis_hash
