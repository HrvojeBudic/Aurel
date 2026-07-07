"""A6 seal — deterministic hybrid retrieval.

Proves the A6 invariants:

1. Deterministic ranking: same corpus+query ⇒ identical ordered ids across repeated
   calls (same fabric) and identical ordered contents across a fresh fabric.
2. Each signal contributes: vector cosine, BM25-lite lexical, and graph expansion.
3. As-of / supersession: default excludes superseded/inactive (A4/is_current);
   an as-of-past query surfaces the pre-revision belief (A0).
4. RRF fusion + strict (score, memory_id) ordering; empty/degenerate ⇒ [].
5. NeuralEmbedderSeam is honestly unavailable (never faked).
6. No-collapse: retrieval is read-only; retrieve/assemble_context are unchanged.
"""

from __future__ import annotations

import pytest

from agentic_runtime import MemoryFabric, MemoryTruthState, MemoryWriteRequest
from agentic_runtime.budget import BudgetLedger
from agentic_runtime.memory import HashingEmbedder, cosine
from agentic_runtime.memory_embedder import (NeuralEmbedderSeam,
                                             NeuralEmbedderUnavailable)
from agentic_runtime.memory_governance import MemoryLinkRequest
from agentic_runtime.memory_retrieval import _BM25Lite, _tokenize, hybrid_retrieve
from agentic_runtime.memory_tools import MemoryToolSession
from agentic_runtime.trace import InMemoryTraceLedger

RUN = "run_a6"

# Graded relevance to QUERY (3 / 2 / 1 / 0 shared query terms) ⇒ distinct fused
# scores ⇒ a tie-free, fully order-stable ranking across fresh fabrics.
CORPUS = [
    "database server crash outage at noon",
    "database server maintenance window tonight",
    "database backup nightly schedule report",
    "banana bread walnut recipe with honey",
]
QUERY = "database server crash"


def _fabric():
    fab = MemoryFabric()
    fab.bind_trace(InMemoryTraceLedger(run_id=RUN))
    return fab


def _seed(fab, content, *, truth="candidate"):
    return fab.request_write(MemoryWriteRequest(
        content=content, proposed_truth_state=MemoryTruthState(truth),
        writer_kind="operator", source_run_id=RUN)).record


# 1 ─ deterministic ranking across repeated calls and a fresh fabric.
def test_deterministic_ranking():
    fab = _fabric()
    [_seed(fab, c) for c in CORPUS]
    r1 = [r.memory_id for r in fab.hybrid_retrieve(QUERY, k=4)]
    r2 = [r.memory_id for r in fab.hybrid_retrieve(QUERY, k=4)]
    assert r1 == r2                                   # id-stable on the same fabric

    fab_b = _fabric()
    [_seed(fab_b, c) for c in CORPUS]
    contents_a = [r.content for r in fab.hybrid_retrieve(QUERY, k=4)]
    contents_b = [r.content for r in fab_b.hybrid_retrieve(QUERY, k=4)]
    assert contents_a == contents_b                   # content-stable across fabrics
    # The most relevant doc ranks first.
    assert contents_a[0] == "database server crash outage at noon"


# 2 ─ each signal contributes.
def test_vector_bm25_and_graph_each_contribute():
    # Vector: char-similar content scores above unrelated content.
    e = HashingEmbedder()
    qv = e.embed(QUERY)
    assert cosine(qv, e.embed("the database server crashed at noon")) > \
           cosine(qv, e.embed("banana bread recipe with walnuts and honey"))

    # BM25-lite: a doc with the exact query terms scores above one without.
    docs = [_tokenize(c) for c in CORPUS]
    bm = _BM25Lite(docs)
    with_terms = bm.score(_tokenize(QUERY), _tokenize("database server crash log"))
    without = bm.score(_tokenize(QUERY), _tokenize("banana bread recipe"))
    assert with_terms > without > -1  # (without == 0.0)
    assert without == 0.0

    # Graph expansion: a near-zero-relevance doc linked to the top hit is promoted
    # above an equally-irrelevant unlinked doc — the graph signal is the only
    # difference, so it strictly improves the linked doc's rank.
    fab = _fabric()
    strong = _seed(fab, "database server crash outage at noon")
    weak = _seed(fab, "quarterly financial planning spreadsheet")   # linked, 0 query terms
    _seed(fab, "server room temperature log")                       # unlinked, 1 query term
    fab.link(MemoryLinkRequest(from_id=weak.memory_id, to_id=strong.memory_id,
                               relation="relates_to", writer_kind="operator",
                               source_run_id=RUN))
    # Without graph the unlinked doc outranks weak (it shares "server"); the graph
    # boost from the edge to the top hit deterministically lifts weak above it.
    with_graph = [r.memory_id for r in fab.hybrid_retrieve(QUERY, k=3, expand_graph=True)]
    without_graph = [r.memory_id for r in fab.hybrid_retrieve(QUERY, k=3, expand_graph=False)]
    assert with_graph.index(weak.memory_id) < without_graph.index(weak.memory_id)


# 3 ─ as-of / supersession: default excludes superseded; as-of-past surfaces it.
def test_as_of_and_supersession_filter():
    # (a) Real A4 update ⇒ superseded old is excluded from the current pool.
    fab = _fabric()
    budget = BudgetLedger()
    old = _seed(fab, "the meeting is on monday")
    session = MemoryToolSession(fab, budget, writer_kind="operator")
    res = session.invoke("mem_update", {"memory_id": old.memory_id,
                                        "content": "the meeting is on tuesday"})
    new_id = res["new_memory_id"]
    current = [r.memory_id for r in fab.hybrid_retrieve("meeting", k=5)]
    assert new_id in current and old.memory_id not in current

    # (b) as-of-past surfaces the pre-revision belief (explicit bi-temporal times).
    fab2 = _fabric()
    o = _seed(fab2, "the meeting is on monday")
    n = _seed(fab2, "the meeting is on tuesday")
    o.superseded_by = n.memory_id
    o.valid_to = 2000.0
    o.transaction_to = 2000.0
    n.revises = o.memory_id
    n.transaction_from = 2000.0
    cur = [r.memory_id for r in fab2.hybrid_retrieve("meeting", k=5)]
    past = [r.memory_id for r in fab2.hybrid_retrieve("meeting", k=5, as_of=(1500.0, 1500.0))]
    assert o.memory_id not in cur and n.memory_id in cur
    assert o.memory_id in past and n.memory_id not in past


# 4 ─ fusion ordering + fail-closed on empty/degenerate.
def test_fusion_ordering_and_fail_closed():
    fab = _fabric()
    [_seed(fab, c) for c in CORPUS]
    ranked = fab.hybrid_retrieve(QUERY, k=10)
    ids = [r.memory_id for r in ranked]
    assert ids == sorted(set(ids), key=ids.index)     # no duplicates
    # Fail-closed: empty / whitespace query and an empty fabric ⇒ [].
    assert fab.hybrid_retrieve("", k=5) == []
    assert fab.hybrid_retrieve("   ", k=5) == []
    assert _fabric().hybrid_retrieve(QUERY, k=5) == []


# 5 ─ NeuralEmbedderSeam is honestly unavailable.
def test_neural_embedder_seam_unavailable():
    seam = NeuralEmbedderSeam(model="fake-neural-v1")
    assert seam.available is False
    with pytest.raises(NeuralEmbedderUnavailable):
        seam.embed("anything")


# 6 ─ no-collapse: retrieval is read-only; retrieve/assemble_context unaffected.
def test_no_collapse_read_only():
    fab = _fabric()
    [_seed(fab, c) for c in CORPUS]
    stats_before = fab.stats()
    baseline_retrieve = [r.content for r in _fabric_with(CORPUS).retrieve(QUERY, k=5)]

    fab.hybrid_retrieve(QUERY, k=5)                    # must not mutate the store

    assert fab.stats() == stats_before
    # retrieve still behaves exactly as before hybrid retrieval existed.
    assert [r.content for r in fab.retrieve(QUERY, k=5)] == baseline_retrieve
    assert isinstance(fab.assemble_context(QUERY, k=5), str)


def _fabric_with(contents):
    fab = _fabric()
    for c in contents:
        _seed(fab, c)
    return fab
