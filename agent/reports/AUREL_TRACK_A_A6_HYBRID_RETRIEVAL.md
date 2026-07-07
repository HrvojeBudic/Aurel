# Track A / A6 — Deterministic hybrid retrieval

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (additive; `retrieve`/`assemble_context` byte-identical).

## Summary

A6 adds a deterministic **hybrid** ranking that fuses four signals — vector cosine,
stdlib **BM25-lite** lexical, **graph expansion** along A2 edges, and the A0
**as-of** filter — with **Reciprocal Rank Fusion (RRF)**, sorted strictly by
`(-fused_score, memory_id)`. It is a **new additive entry point**
(`hybrid_retrieve`); the existing `retrieve`/`assemble_context` are untouched, so
Track B's B2 `difficulty_estimator` is unaffected. Retrieval is read-only: it
mints nothing, writes no trace, mutates no record, and fails closed on empty input.

## Files changed

**New — `src/agentic_runtime/memory_retrieval.py`**
- `hybrid_retrieve(fabric, query, *, k=5, as_of=None, expand_graph=True, rrf_k=60)`.
  - **Pool (A0/A2/A4 physics):** `_candidate_pool` — default = current belief
    (`is_active()` ∧ `truth_status != DEPRECATED` ∧ `truth_state != REJECTED` ∧
    `BiTemporalStamp.is_current()`), which excludes superseded/retracted/forgotten
    A4 records; with an `as_of=(valid_time, transaction_time)` it uses A0's
    `AsOfView.as_of(...)` (surfacing the historical belief, superseded versions
    included), excluding only audit (`REJECTED`).
  - **Vector:** cosine of `HashingEmbedder` embeddings (recomputed from content).
  - **BM25-lite:** `_BM25Lite` (k1=1.5, b=0.75) over tokenized content, deterministic.
  - **Graph:** one-hop expansion — records adjacent (via A2 edges) to the top
    vector hits get a third RRF signal, so a linked-but-weak record can surface.
  - **Fusion:** RRF over the ranked lists; final sort `(-fused, memory_id)`.
  - **Fail-closed:** empty/whitespace query or empty pool ⇒ `[]`.

**New — `src/agentic_runtime/memory_embedder.py`**
- `NeuralEmbedderSeam` — declared but honestly **unavailable**: `available` is a
  read-only `False`, `embed()` raises `NeuralEmbedderUnavailable`. The
  deterministic `HashingEmbedder` stays the only real embedder. No faked neural
  vectors.

**Edit — `src/agentic_runtime/memory.py`**
- Added `MemoryFabric.hybrid_retrieve(...)` — a thin **additive** method delegating
  to `memory_retrieval.hybrid_retrieve` (lazy import avoids the
  `memory ↔ memory_retrieval` cycle). **`retrieve` and `assemble_context` are
  unchanged (byte-identical).**

## Retrieval fusion design

Four independent signals, each producing (or contributing to) a ranked list of
`memory_id`s; RRF sums `1/(rrf_k + rank + 1)` across the lists a record appears in;
ties break by `memory_id`. Vector and BM25 rank the whole pool; graph contributes
a bonus list containing only records adjacent to the top-vector seeds (so being
linked to a strong hit is a genuine, additive boost — never a penalty). The as-of
filter is applied *before* scoring, as pool selection.

## Determinism proof

No `hash()` ordering, no randomness: BM25 and cosine are arithmetic over the
deterministic `HashingEmbedder`; every intermediate sort and the final sort use
`(-score, memory_id)`. Seal §1: repeated calls on the same fabric return
**identical ids**; a **fresh fabric** with the same contents returns **identical
ordered contents** (the seal corpus is graded 3/2/1/0 query-term overlap ⇒
tie-free ⇒ fully order-stable across fabrics). Note: for score-*tied* records the
`(score, memory_id)` tiebreak uses the uuid `memory_id`, so tie order is
fabric-specific by design — the seal's tie-free corpus makes cross-fabric order
fully stable, and the graph-contribution case uses a doc that deterministically
out-scores the linked one so the graph flip is uuid-robust (verified stable across
repeated fresh-uuid runs).

## As-of / graph correctness

- **Default excludes superseded/inactive.** Seal §3(a): after a real A4
  `mem_update`, the superseded old version is absent from `hybrid_retrieve` (its
  `transaction_to` is closed ⇒ `is_current()` False) while the new version is present.
- **As-of-past surfaces the prior belief.** Seal §3(b): with explicit bi-temporal
  times, `as_of=(1500, 1500)` returns the pre-revision record and excludes the
  successor (`transaction_from=2000`), while the default (current) query does the
  reverse — honoring A0 semantics and A4 supersession.
- **Graph honors A2 edges.** Seal §2: a near-zero-relevance record linked to the
  top hit is deterministically promoted above an equally-irrelevant unlinked record.

## NeuralEmbedderSeam honesty

Seal §5: `NeuralEmbedderSeam.available is False`; `embed()` raises
`NeuralEmbedderUnavailable`. No code path fabricates a neural embedding.

## Did `assemble_context` change? — NO. B2 handling.

**`assemble_context` and `retrieve` are unchanged (byte-identical).** Hybrid
retrieval is a new, opt-in method, so the cross-lock is not triggered. B2's
`reasoning/difficulty_estimator.py` consumes a `memory_context: str` **parameter**
(it checks its length against `_SPARSE_CONTEXT_CHARS`) and never calls
`assemble_context`/`retrieve` itself, so it is doubly insulated. Its suite
(`test_reasoning_difficulty.py`) was run and **passes** — no B2 changes were
needed or made.

## Spec-vs-code drift + decisions

- **D1 — additive entry point, not a change to `retrieve`.** The spec says "Edit
  `memory.py`", and the cross-lock warns against changing `assemble_context`.
  Smallest correct honest path: add `hybrid_retrieve` (additive) and leave
  `retrieve`/`assemble_context` byte-identical. `memory.py` is edited only to add
  the delegating method. No new flag needed (opt-in by being called).
- **D2 — no new flag.** Hybrid retrieval is opt-in by invocation; the default
  retrieval path is untouched, so `AUREL_DURABLE_MEMORY` stays as-is and nothing
  is gated.
- **D3 — as-of pool vs current pool.** Default retrieval selects the *current*
  belief (excludes superseded, honoring A4 — the as-of-filtered retrieval the
  masterplan places at A6). A0's `retrieve` deliberately ignored stamps; A6's
  `hybrid_retrieve` is where stamp-aware selection lands, without disturbing the
  legacy `retrieve`.
- **D4 — graph expansion is a bonus RRF list.** Being linked to a top hit adds a
  signal but never removes one, so graph expansion can only help recall, never
  suppress a directly-relevant record.

## Validation (focused-first; full ~25 min suite intentionally skipped)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 3 source files.
- Seal `test_p6a6_hybrid_retrieval.py` — **6 passed** (stable across repeated runs).
- Directly-affected regression (timeout-wrapped): memory_p09, memory_write_policy_cards_p167,
  tool_contract_p10, tool_registry_p133, builtin_tool_manifests_p138,
  **reasoning_difficulty (B2)**, p6a0–p6a6 → **203 passed, 0 failed**.

## Next: A7 — Memory Explorer projection + CLI

`memory_projection.py` (rebuilt only from trace memory-governance events + durable
store); edit `cli.py` (`memory explore/history/graph/rejected`, read-only). Mirror
the `reasoning`/`dual-kernel` CLI pattern. This is also where the A2/A3 D2 seam
(surfacing edge/revision `details` from the trace) can be closed.
