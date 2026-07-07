"""A5 seal — deterministic consolidation to CANDIDATE.

Proves the A5 invariants:

1. Deterministic clustering + summarization: same inputs ⇒ identical clusters and
   identical summary text (across two fresh fabrics), no hash()/randomness.
2. A consolidation summary is CANDIDATE (never higher), written through the
   governed funnel, with SUMMARIZES edges summary→each source.
3. Provenance preserved: the summary points back to every source
   (evidence_refs/links + SUMMARIZES edges); sources are never mutated.
4. An agent-triggered consolidation cannot elevate trust (still CANDIDATE).
5. Empty / degenerate clusters fail closed — no summary minted.
6. One governance write row per summary + one link row per edge; zero
   StateTransitionRecord.
7. No-collapse: existing write/promote/link/retrieve/revision unchanged.
"""

from __future__ import annotations

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.memory_consolidation import (cluster_memories,
                                                  consolidate, summarize_cluster)
from agentic_runtime.memory_graph import MemoryRelation
from agentic_runtime.memory_tools import MemoryToolSession
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a5"

SIMILAR = [
    "the database server crashed at noon",
    "the database server crashed at midnight",
    "the database server crashed during the nightly backup",
]
DIFFERENT = "quantum entanglement fundamentals for beginners"


def _harness():
    trace = InMemoryTraceLedger(run_id=RUN)
    fabric = MemoryFabric()
    fabric.bind_trace(trace)
    budget = BudgetLedger()
    return fabric, trace, budget


def _seed(fabric, content, *, truth="candidate"):
    return fabric.request_write(MemoryWriteRequest(
        content=content, proposed_truth_state=MemoryTruthState(truth),
        writer_kind="operator", source_run_id=RUN)).record


def _rows(trace, action):
    return [e for e in trace.replay()
            if e["kind"] == "memory_governance" and e["action"] == action]


def _state_rows(trace):
    return [e for e in trace.replay() if e["kind"] == "state_transition"]


# 1 ─ deterministic clustering + summary text (reproducible across fresh fabrics).
def test_deterministic_clustering_and_summary():
    fabric_a, _, _ = _harness()
    recs_a = [_seed(fabric_a, c) for c in SIMILAR] + [_seed(fabric_a, DIFFERENT)]

    # Same records, two calls ⇒ identical cluster structure and summary text.
    c1 = cluster_memories(recs_a, fabric_a.embedder, threshold=0.5)
    c2 = cluster_memories(recs_a, fabric_a.embedder, threshold=0.5)
    ids1 = [sorted(r.memory_id for r in c) for c in c1]
    ids2 = [sorted(r.memory_id for r in c) for c in c2]
    assert ids1 == ids2
    assert len(c1) == 1 and len(c1[0]) == 3          # 3 similar cluster; different dropped
    assert summarize_cluster(c1[0]) == summarize_cluster(c2[0])

    # A second fresh fabric with the SAME contents yields the SAME summary text
    # (content-keyed, not uuid-keyed).
    fabric_b, _, _ = _harness()
    recs_b = [_seed(fabric_b, c) for c in SIMILAR] + [_seed(fabric_b, DIFFERENT)]
    cb = cluster_memories(recs_b, fabric_b.embedder, threshold=0.5)
    assert summarize_cluster(cb[0]) == summarize_cluster(c1[0])


# 2 + 3 + 6 ─ summary is CANDIDATE, governed, edged, provenance preserved, traced once.
def test_summary_candidate_governed_with_edges_and_provenance():
    fabric, trace, budget = _harness()
    sources = [_seed(fabric, c) for c in SIMILAR]
    other = _seed(fabric, DIFFERENT)
    source_ids = sorted(s.memory_id for s in sources)
    snapshot = {s.memory_id: (s.content, s.truth_state, s.superseded_by) for s in sources}
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    result = session.invoke("mem_consolidate", {
        "memory_ids": [s.memory_id for s in sources] + [other.memory_id],
        "threshold": 0.5})

    assert result["ok"] is True
    assert result["clusters_found"] == 1
    summary = result["summaries"][0]
    sid = summary["summary_id"]

    # CANDIDATE — never higher.
    assert summary["truth_state"] == MemoryTruthState.CANDIDATE.value
    rec = fabric.by_id[sid]
    assert rec.truth_state is MemoryTruthState.CANDIDATE
    assert rec.content.startswith("Consolidated summary of 3 memories:")

    # SUMMARIZES edges summary → each source.
    assert sorted(fabric.graph.neighbors(sid, MemoryRelation.SUMMARIZES)) == source_ids
    assert summary["edge_ids"] and len(summary["edge_ids"]) == 3

    # Provenance: summary points back; sources are byte-for-byte unchanged.
    assert sorted(rec.evidence_refs) == source_ids
    assert sorted(rec.links) == source_ids
    for s in sources:
        assert (s.content, s.truth_state, s.superseded_by) == snapshot[s.memory_id]

    # One write row for the summary + one link row per edge; no state transitions.
    assert len(_rows(trace, "write")) - 4 == 1        # 4 seed writes + 1 summary write
    assert len([r for r in _rows(trace, "write") if r["memory_id"] == sid]) == 1
    assert len(_rows(trace, "link")) == 3
    assert len(_state_rows(trace)) == 0
    # One charge per governed sub-write: 1 summary + 3 edges.
    assert budget.memory_writes == 4
    assert budget.sandbox_executions == 0


# 4 ─ an agent-triggered consolidation cannot elevate trust (still CANDIDATE).
def test_agent_consolidation_cannot_elevate_trust():
    fabric, trace, budget = _harness()
    sources = [_seed(fabric, c) for c in SIMILAR]
    agent = MemoryToolSession(fabric, budget, writer_kind="agent")

    result = agent.invoke("mem_consolidate", {
        "memory_ids": [s.memory_id for s in sources], "threshold": 0.5})

    assert result["ok"] is True
    sid = result["summaries"][0]["summary_id"]
    assert fabric.by_id[sid].truth_state is MemoryTruthState.CANDIDATE   # never verified
    # No source was promoted either.
    assert all(fabric.by_id[s.memory_id].truth_state is MemoryTruthState.CANDIDATE
               for s in sources)


# 5 ─ empty / degenerate clusters fail closed (no summary minted).
def test_degenerate_clusters_fail_closed():
    fabric, trace, budget = _harness()
    a = _seed(fabric, SIMILAR[0])
    b = _seed(fabric, DIFFERENT)
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    writes_before = len(_rows(trace, "write"))

    # Two dissimilar records ⇒ no cluster of size >= 2.
    dissimilar = session.invoke("mem_consolidate", {
        "memory_ids": [a.memory_id, b.memory_id], "threshold": 0.5})
    assert dissimilar["ok"] is False
    assert dissimilar["reason_code"] == "no_consolidatable_cluster"

    # Empty input and single id ⇒ also fail closed.
    assert session.invoke("mem_consolidate", {"memory_ids": []})["ok"] is False
    assert session.invoke("mem_consolidate", {"memory_ids": [a.memory_id]})["ok"] is False

    # Nothing minted, nothing charged, no edges.
    assert len(_rows(trace, "write")) == writes_before
    assert len(_rows(trace, "link")) == 0
    assert budget.memory_writes == 0
    assert len(fabric.graph) == 0


# 7 ─ no-collapse: existing write/promote/link/retrieve unaffected by consolidation.
def test_no_collapse_existing_paths_unaffected():
    fabric, trace, budget = _harness()
    sources = [_seed(fabric, c) for c in SIMILAR]
    keep = _seed(fabric, "an unrelated verified fact about the moon")
    fabric.promote(keep.memory_id, MemoryTruthState.VERIFIED,
                   evidence_refs=["ev"], actor="operator")
    session = MemoryToolSession(fabric, budget, writer_kind="operator")

    session.invoke("mem_consolidate", {
        "memory_ids": [s.memory_id for s in sources], "threshold": 0.5})

    # Unrelated promoted record untouched; retrieval + a fresh add still work.
    assert fabric.by_id[keep.memory_id].truth_state is MemoryTruthState.VERIFIED
    assert session.invoke("mem_add", {"content": "brand new note"})["ok"] is True
    assert any("moon" in r.content for r in fabric.retrieve("moon", k=5))
