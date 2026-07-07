"""A6 — Deterministic hybrid retrieval.

A read-only ranking over a memory fabric that fuses four signals:

* **Vector** — cosine of the deterministic ``HashingEmbedder`` embeddings.
* **Lexical** — a stdlib **BM25-lite** score over tokenized content.
* **Graph** — one-hop expansion along A2 edges from the top vector hits, so a
  record that is *linked* to a strong hit (but weak on its own) can surface.
* **As-of** — the A0 bi-temporal filter chooses the candidate pool: by default
  the *current* belief (open intervals, active, not deprecated/rejected); with an
  explicit ``as_of`` time it returns the *historical* belief (so a superseded A4
  version reappears for a past query).

Signals are fused with **Reciprocal Rank Fusion (RRF)** and the result is sorted
strictly by ``(-fused_score, memory_id)`` — no ``hash()`` ordering, no randomness,
so the same corpus + query is byte-reproducible. Retrieval is read-only: it mints
nothing, writes no trace, and mutates no record. Fail-closed: an empty/whitespace
query or an empty pool yields ``[]`` — never a fabricated hit.

This is an **additive** entry point. ``MemoryFabric.retrieve`` /
``assemble_context`` are unchanged and byte-identical (see the A6 report).
"""

from __future__ import annotations

import math
import re
from typing import Any, Optional

from .core_types import MemoryTruthState, TruthStatus
from .memory import cosine
from .memory_bitemporal import BiTemporalStamp

_RRF_K = 60           # standard RRF damping constant
_BM25_K1 = 1.5
_BM25_B = 0.75


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class _BM25Lite:
    """A minimal, deterministic BM25 over a fixed candidate corpus."""

    def __init__(self, docs_tokens: list[list[str]]) -> None:
        self.N = len(docs_tokens)
        self.avgdl = (sum(len(d) for d in docs_tokens) / self.N) if self.N else 0.0
        self.df: dict[str, int] = {}
        for d in docs_tokens:
            for term in set(d):
                self.df[term] = self.df.get(term, 0) + 1

    def score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not doc_tokens or self.N == 0 or self.avgdl == 0.0:
            return 0.0
        dl = len(doc_tokens)
        freq: dict[str, int] = {}
        for t in doc_tokens:
            freq[t] = freq.get(t, 0) + 1
        s = 0.0
        for term in set(query_tokens):
            tf = freq.get(term, 0)
            if tf == 0:
                continue
            n = self.df.get(term, 0)
            idf = math.log(1.0 + (self.N - n + 0.5) / (n + 0.5))
            denom = tf + _BM25_K1 * (1.0 - _BM25_B + _BM25_B * dl / self.avgdl)
            s += idf * (tf * (_BM25_K1 + 1.0)) / denom
        return s


def _candidate_pool(fabric: Any, as_of: Optional[tuple]) -> list[Any]:
    """The records eligible for ranking, honoring A0 as-of + A2/A4 physics."""
    records = list(fabric.by_id.values())
    if as_of is not None:
        # Historical belief: the A0 read model selects the temporally-correct set
        # (may include superseded versions). Only audit (rejected) is never a belief.
        from .memory_asof import AsOfView
        valid_time, transaction_time = as_of
        pool = AsOfView(records).as_of(valid_time, transaction_time)
        return [r for r in pool if r.truth_state is not MemoryTruthState.REJECTED]
    # Current belief: active, still-current (open intervals), not deprecated/rejected.
    return [
        r for r in records
        if r.is_active()
        and r.truth_status is not TruthStatus.DEPRECATED
        and r.truth_state is not MemoryTruthState.REJECTED
        and BiTemporalStamp.from_record(r).is_current()
    ]


def _ranked_ids(pool: list[Any], scores: dict[str, float]) -> list[str]:
    """Memory ids ordered by descending score, ``memory_id`` breaking ties."""
    return [r.memory_id for r in
            sorted(pool, key=lambda r: (-scores.get(r.memory_id, 0.0), r.memory_id))]


def _rrf(ranked_lists: list[list[str]], rrf_k: int) -> dict[str, float]:
    fused: dict[str, float] = {}
    for lst in ranked_lists:
        for rank, mid in enumerate(lst):
            fused[mid] = fused.get(mid, 0.0) + 1.0 / (rrf_k + rank + 1)
    return fused


def hybrid_retrieve(
    fabric: Any,
    query: str,
    *,
    k: int = 5,
    as_of: Optional[tuple] = None,
    expand_graph: bool = True,
    rrf_k: int = _RRF_K,
) -> list[Any]:
    """Deterministic hybrid ranking. Returns up to ``k`` records, read-only.

    ``as_of`` is an optional ``(valid_time, transaction_time)`` pair (either may be
    ``None`` for "current on that axis"); omit it for the current-belief pool.
    """
    q = (query or "").strip()
    if not q:
        return []                                   # fail-closed: no fabricated hits
    pool = _candidate_pool(fabric, as_of)
    if not pool:
        return []

    embedder = fabric.embedder
    q_vec = embedder.embed(q)
    q_tok = _tokenize(q)

    # Signal 1 — vector cosine (recompute embeddings from content, deterministic).
    doc_vecs = {r.memory_id: (r.embedding or embedder.embed(r.content)) for r in pool}
    vec_scores = {r.memory_id: cosine(q_vec, doc_vecs[r.memory_id]) for r in pool}

    # Signal 2 — BM25-lite lexical.
    doc_toks = {r.memory_id: _tokenize(r.content) for r in pool}
    bm25 = _BM25Lite(list(doc_toks.values()))
    bm_scores = {r.memory_id: bm25.score(q_tok, doc_toks[r.memory_id]) for r in pool}

    vec_ranked = _ranked_ids(pool, vec_scores)
    bm_ranked = _ranked_ids(pool, bm_scores)
    ranked_lists = [vec_ranked, bm_ranked]

    # Signal 3 — graph expansion: one hop from the top vector hits along A2 edges.
    if expand_graph and getattr(fabric, "graph", None) is not None:
        seeds = set(vec_ranked[:max(1, k)])
        pool_ids = {r.memory_id for r in pool}
        graph_score: dict[str, float] = {}
        for r in pool:
            adjacent = fabric.graph.edges_from(r.memory_id) + fabric.graph.edges_to(r.memory_id)
            hits = 0
            for e in adjacent:
                neighbor = e.to_id if e.from_id == r.memory_id else e.from_id
                if neighbor in seeds and neighbor != r.memory_id:
                    hits += 1
            if hits > 0 and r.memory_id in pool_ids:
                graph_score[r.memory_id] = float(hits)
        if graph_score:
            graph_ranked = sorted(graph_score,
                                  key=lambda m: (-graph_score[m], m))
            ranked_lists.append(graph_ranked)

    fused = _rrf(ranked_lists, rrf_k)
    ranked = sorted(pool, key=lambda r: (-fused.get(r.memory_id, 0.0), r.memory_id))
    return ranked[:k]


__all__ = ["hybrid_retrieve"]
