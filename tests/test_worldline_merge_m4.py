"""M4 — integrated fork/merge lifecycle. Merge is the dual of fork.

Two children forked from one base state, each writing to the tree, are welded
back into a single merged world-state. Disjoint writes merge automatically and
the merge edge verifies; divergent writes to the same path are a MergeConflict
that persists nothing and pauses for operator review.
"""

from __future__ import annotations

import pytest

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
from agentic_runtime.core_types import CommandEnvelope
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.worldline import MergeError, verify_merge


def _approver() -> AutoApprover:
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _card() -> AgentCard:
    return AgentCard.make(
        name="M4 Agent", agent_class=AgentClass.EXECUTION, mission="merge test",
        authority=AuthorityScope(write_paths=["src/"], read_paths=["*"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "list_dir"],
    )


def _cmd(card, tool, args):
    return CommandEnvelope.make(
        issuer_card_id=card.id, tool=tool, args=args,
        rationale="m4", declared_risk=RiskLevel.LOW, expected_effect="m4")


def _parent(trace_dir, store, ws_root):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=ws_root), approval_gate=_approver(),
        trace_backend="persistent", trace_dir=trace_dir,
        retain_states=True, state_store=store,
    )
    card = _card()
    r = kernel.runtime.submit(
        _cmd(card, "write_file", {"path": "src/base.py", "content": "BASE\n"}), card)
    assert r.ok
    kernel.trace.seal_run("completed")
    return kernel, r.transition.entry_hash


def _drive_child(trace_dir, store, res, path, content):
    kernel = build_runtime(
        sandbox=res.sandbox, approval_gate=_approver(),
        trace_backend="persistent", trace_dir=trace_dir,
        trace_run_id=res.child_run_id, retain_states=True, state_store=store,
    )
    card = _card()
    r = kernel.runtime.submit(_cmd(card, "write_file", {"path": path, "content": content}), card)
    assert r.ok
    kernel.trace.seal_run("completed")
    return kernel


def _setup(tmp_path, child_a, child_b):
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel, entry = _parent(trace_dir, store, str(tmp_path / "ws"))
    forest = WorldLineForest(trace_dir)
    res_a = forest.fork(kernel.trace.run_id, entry, sandbox_factory=lambda r: UnsafeLocalSandbox(root=r))
    res_b = forest.fork(kernel.trace.run_id, entry, sandbox_factory=lambda r: UnsafeLocalSandbox(root=r))
    _drive_child(trace_dir, store, res_a, *child_a)
    _drive_child(trace_dir, store, res_b, *child_b)
    return trace_dir, forest, kernel.trace.run_id, res_a, res_b


def test_disjoint_merge_is_clean_and_verifies(tmp_path):
    trace_dir, forest, parent_id, res_a, res_b = _setup(
        tmp_path, ("src/a.py", "AAA\n"), ("src/b.py", "BBB\n"))
    result = forest.merge(parent_id, [res_a.child_run_id, res_b.child_run_id])

    assert result.clean, result.to_dict()
    assert result.merged_state_hash and forest.store.has(result.merged_state_hash)
    # the merged tree carries base + both branches' writes
    from agentic_runtime.worldline import _read_tree
    files = _read_tree(forest.store, result.merged_state_hash)
    assert files["src/base.py"] == b"BASE\n"
    assert files["src/a.py"] == b"AAA\n"
    assert files["src/b.py"] == b"BBB\n"

    # merge edge is persisted and the whole forest verifies (incl. the merge)
    assert len(forest.merges()) == 1
    report = forest.verify()
    assert report["ok"], report
    assert report["merge_count"] == 1


def test_conflicting_writes_produce_conflict_and_persist_nothing(tmp_path):
    trace_dir, forest, parent_id, res_a, res_b = _setup(
        tmp_path, ("src/shared.py", "FROM_A\n"), ("src/shared.py", "FROM_B\n"))
    result = forest.merge(parent_id, [res_a.child_run_id, res_b.child_run_id])

    assert not result.clean
    assert result.status == "CONFLICT"
    assert result.merged_state_hash is None
    assert [c.path for c in result.conflicts] == ["src/shared.py"]
    # nothing persisted on conflict — operator must resolve
    assert forest.merges() == []


def test_merge_requires_verified_retained_children(tmp_path):
    trace_dir, forest, parent_id, res_a, res_b = _setup(
        tmp_path, ("src/a.py", "AAA\n"), ("src/b.py", "BBB\n"))
    # an unknown child id has no lineage → MergeError
    with pytest.raises(MergeError, match="lineage"):
        forest.merge(parent_id, [res_a.child_run_id, "run-does-not-exist"])


def test_branch_and_merge_lifecycle(tmp_path):
    """The integrated fork→branch→merge one-call lifecycle (join = merge)."""
    trace_dir = str(tmp_path / "traces")
    store = StateStore(trace_dir)
    kernel, entry = _parent(trace_dir, store, str(tmp_path / "ws"))
    forest = WorldLineForest(trace_dir)

    def make_driver(path, content):
        def drive(res):
            _drive_child(trace_dir, store, res, path, content)
        return drive

    result = forest.branch_and_merge(
        kernel.trace.run_id,
        entry,
        [make_driver("src/x.py", "XXX\n"), make_driver("src/y.py", "YYY\n")],
        sandbox_factory=lambda r: UnsafeLocalSandbox(root=r),
    )
    assert result.clean, result.to_dict()
    from agentic_runtime.worldline import _read_tree
    files = _read_tree(forest.store, result.merged_state_hash)
    assert files["src/x.py"] == b"XXX\n" and files["src/y.py"] == b"YYY\n"
    assert forest.verify()["ok"]


def test_merge_edge_tamper_is_detected(tmp_path):
    trace_dir, forest, parent_id, res_a, res_b = _setup(
        tmp_path, ("src/a.py", "AAA\n"), ("src/b.py", "BBB\n"))
    result = forest.merge(parent_id, [res_a.child_run_id, res_b.child_run_id])
    edge = result.merge_ref.to_dict()
    # forge the merged_state_hash to a different (real) state → M1/M5 catches it
    edge["merged_state_hash"] = result.base_state_hash
    res = verify_merge(edge, trace_dir, forest.store)
    assert res["ok"] is False
