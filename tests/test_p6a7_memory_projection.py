"""A7 seal — Memory Explorer projection + CLI, and the closed D2 replay seam.

Proves:

1. A projection rebuilt from the trace ALONE equals the live fabric's current
   records / belief-history / graph / rejected.
2. D2 closed — edge (link) and revision (update) ``details`` now survive
   ``replay()``, so the graph and belief-history reconstruct from the trace alone.
3. Fail-closed: empty/absent trace ⇒ empty views; unknown id ⇒ []; content is
   None with no durable store (never fabricated).
4. Durable store enriches records with content (A3).
5. CLI ``memory explore/history/graph/rejected`` return honest, deterministic
   structured output; a bad run id fails closed.
6. No-collapse: the ``details`` addition to replay is additive (existing keys
   intact); existing write/promote/link/revision/retrieve are unaffected.
"""

from __future__ import annotations

import argparse
import json

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.memory_asof import AsOfView
from agentic_runtime.memory_governance import MemoryLinkRequest
from agentic_runtime.memory_projection import MemoryProjection
from agentic_runtime.memory_tools import MemoryToolSession
from agentic_runtime.trace import InMemoryTraceLedger, PersistentTraceLedger

RUN = "run_a7"


def _harness(trace=None):
    trace = trace or InMemoryTraceLedger(run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(trace)
    return fab, trace, BudgetLedger()


def _seed(fab, content, *, truth="candidate"):
    return fab.request_write(MemoryWriteRequest(
        content=content, proposed_truth_state=MemoryTruthState(truth),
        writer_kind="operator", source_run_id=RUN)).record


def _exercise(fab, session):
    """A mixed workload: writes, a link, a promotion, an update, and a deny."""
    a = _seed(fab, "the meeting is on monday")
    b = _seed(fab, "project kickoff notes")
    fab.link(MemoryLinkRequest(from_id=a.memory_id, to_id=b.memory_id,
                               relation="relates_to", writer_kind="operator",
                               source_run_id=RUN))
    fab.promote(b.memory_id, MemoryTruthState.VERIFIED,
                evidence_refs=["ev"], actor="operator")
    upd = session.invoke("mem_update", {"memory_id": a.memory_id,
                                        "content": "the meeting is on tuesday"})
    # A denied write ⇒ a rejected/audit record.
    fab.request_write(MemoryWriteRequest(
        content="agent tries canon", proposed_truth_state=MemoryTruthState.CANON,
        writer_kind="agent", source_run_id=RUN))
    return a, b, upd["new_memory_id"]


def _fabric_current(fab):
    return sorted(
        r.memory_id for r in fab.by_id.values()
        if r.is_active()
        and r.truth_status.value != "deprecated"
        and r.truth_state is not MemoryTruthState.REJECTED
        and r.valid_to is None and r.transaction_to is None)


# 1 + 2 ─ trace-only projection equals the live fabric across all views.
def test_trace_only_equals_fabric():
    fab, trace, budget = _harness()
    session = MemoryToolSession(fab, budget, writer_kind="operator")
    _a, _b, new_id = _exercise(fab, session)

    proj = MemoryProjection.from_trace(trace)   # trace ONLY — no fabric handed in

    # current records
    assert sorted(proj.current_ids) == _fabric_current(fab)
    # graph edges (includes the A4 SUPERSEDES reconciliation edge)
    fab_edges = sorted((e.from_id, e.to_id, e.relation.value) for e in fab.graph.all_edges())
    assert sorted(proj.edge_tuples()) == fab_edges
    # belief history matches AsOfView (record-view)
    fab_hist = [r.memory_id for r in AsOfView.from_fabric(fab).belief_history(new_id)]
    assert proj.belief_history(new_id) == fab_hist
    assert len(proj.belief_history(new_id)) == 2
    # rejected count matches the fabric's audit list
    assert len(proj.rejected) == len(fab.rejected) == 1
    assert proj.rejected[0]["reason_code"] == "agent_cannot_write_restricted"


# 2b ─ D2 closed: link + update details now survive replay().
def test_d2_details_survive_replay():
    fab, trace, budget = _harness()
    session = MemoryToolSession(fab, budget, writer_kind="operator")
    _exercise(fab, session)

    rows = [e for e in trace.replay() if e["kind"] == "memory_governance"]
    link_rows = [e for e in rows if e["action"] == "link" and e["verdict"] == "allow"]
    update_rows = [e for e in rows if e["action"] == "update" and e["verdict"] == "allow"]
    assert link_rows and update_rows
    ld = link_rows[0]["details"]
    assert {"from_id", "to_id", "relation", "edge_id"} <= set(ld)
    ud = update_rows[0]["details"]
    assert {"target_id", "new_memory_id"} <= set(ud)


# 3 ─ fail-closed on empty trace / unknown id / no durable content.
def test_projection_fail_closed():
    proj = MemoryProjection.from_trace(InMemoryTraceLedger(run_id="empty"))
    assert proj.current_ids == []
    assert proj.edge_tuples() == []
    assert proj.rejected == []
    assert proj.belief_history("mem_unknown") == []
    assert proj.content_for("mem_unknown") is None
    assert MemoryProjection.from_trace(None).current_ids == []


# 4 ─ durable store enriches records with content (A3).
def test_durable_content_enrichment(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREL_DURABLE_MEMORY", "1")
    from agentic_runtime.durable_memory import DurableMemoryFabric
    from agentic_runtime.memory_persistence import FileMemoryBackend

    path = str(tmp_path / "mem.jsonl")
    trace = InMemoryTraceLedger(run_id=RUN)
    fab = DurableMemoryFabric(FileMemoryBackend(path))
    fab.bind_trace(trace)
    rec = _seed(fab, "durable content here")

    proj = MemoryProjection.from_trace(trace, backend=FileMemoryBackend(path))
    assert proj.content_for(rec.memory_id) == "durable content here"
    records = {r["memory_id"]: r for r in proj.records()}
    assert records[rec.memory_id]["content"] == "durable content here"


# 5 ─ CLI subcommands: honest, deterministic structured output; bad run fails closed.
def test_cli_commands(tmp_path, capsys):
    from agentic_runtime.cli_modules.memory_commands import (cmd_memory_explore,
                                                             cmd_memory_graph,
                                                             cmd_memory_history,
                                                             cmd_memory_rejected)

    trace_dir = str(tmp_path)
    led = PersistentTraceLedger(base_dir=trace_dir, run_id=RUN)
    fab = MemoryFabric()
    fab.bind_trace(led)
    session = MemoryToolSession(fab, BudgetLedger(), writer_kind="operator")
    _a, _b, new_id = _exercise(fab, session)

    def _args(**kw):
        base = dict(run_id=RUN, trace_dir=trace_dir, durable=None, json=True)
        base.update(kw)
        return argparse.Namespace(**base)

    assert cmd_memory_explore(_args()) == 0
    explore = json.loads(capsys.readouterr().out)
    assert explore["edge_count"] >= 2 and explore["rejected_count"] == 1

    assert cmd_memory_graph(_args()) == 0
    graph = json.loads(capsys.readouterr().out)
    assert graph["count"] == explore["edge_count"]

    assert cmd_memory_history(_args(memory_id=new_id)) == 0
    hist = json.loads(capsys.readouterr().out)
    assert hist["found"] is True and len(hist["chain"]) == 2

    assert cmd_memory_rejected(_args()) == 0
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["count"] == 1

    # Bad run id ⇒ fail closed (exit 1, honest error), no fabrication.
    assert cmd_memory_explore(_args(run_id="does_not_exist")) == 1
    err = json.loads(capsys.readouterr().out)
    assert err["ok"] is False and "error" in err


# 6 ─ no-collapse: replay 'details' is additive; existing paths unaffected.
def test_no_collapse_replay_additive():
    fab, trace, budget = _harness()
    session = MemoryToolSession(fab, budget, writer_kind="operator")
    _exercise(fab, session)

    row = next(e for e in trace.replay() if e["kind"] == "memory_governance")
    # Every pre-D2 key is still present, plus the new additive 'details'.
    for key in ("kind", "issuer", "action", "verdict", "memory_id", "from", "to",
                "reason_code"):
        assert key in row
    assert "details" in row
    # Existing retrieval still works.
    assert isinstance(fab.assemble_context("meeting", k=5), str)
    assert any("tuesday" in r.content for r in fab.retrieve("meeting", k=5))
