# Track A / A5 — Deterministic consolidation to CANDIDATE

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (additive; existing paths unchanged).

## Summary

A5 adds deterministic memory consolidation: cluster related memories and propose
a single **CANDIDATE** summary per cluster, linked to every source with A2
`SUMMARIZES` edges. The summary is always CANDIDATE (never VERIFIED/PROCEDURAL/
CANON, never auto-canonized), written through the existing governed funnel, and
sources are never destroyed or altered.

```
mem_consolidate → MemoryToolSession._mem_consolidate → consolidate(...):
    cluster_memories (deterministic, HashingEmbedder cosine, sorted by memory_id)
    → for each cluster ≥ min_size:
        charge → fabric.request_write(CANDIDATE summary)   [one governance write row]
        → for each source: charge → fabric.link(summary SUMMARIZES source)  [one link row]
```

## Files changed

**New — `src/agentic_runtime/memory_consolidation.py`**
- `cluster_memories(records, embedder, *, threshold=0.5, min_size=2)` — a
  deterministic greedy pass over records **sorted by `memory_id`**, embeddings
  computed fresh from content via the deterministic `HashingEmbedder`, seed-based
  single-linkage by `cosine ≥ threshold`; returns only clusters of size
  ≥ `min_size` (degenerate singletons dropped — fail-closed). No `hash()`, no RNG.
- `summarize_cluster(cluster)` — deterministic summary text; sources ordered by
  **`(content, memory_id)`** so the same content set yields byte-identical text
  across processes/fabrics (keyed on content, not the uuid id).
- `consolidate(fabric, records, *, writer_kind, created_by, source_run_id,
  threshold, min_size, charge=None)` — clusters, then for each qualifying cluster
  writes one governed CANDIDATE summary (`request_write`) + `SUMMARIZES` edges
  (`link`) to each source. `charge` is called once before each governed sub-write
  so a tool session meters honestly. Returns `ConsolidationResult`
  (`summaries`, `clusters_found`, `reason_code`, `produced`). Fail-closed: no
  qualifying cluster ⇒ `reason_code="no_consolidatable_cluster"`, nothing written.

**Edit — `src/agentic_runtime/memory_graph.py`**
- `MemoryRelation.SUMMARIZES = "summarizes"` (A2 reserved it for A5; not
  evidence-gated — a structural derivation, not a belief change).

**Edit — `src/agentic_runtime/memory_tools.py`**
- `mem_consolidate` added to `MEMORY_TOOL_NAMES`/`MEMORY_WRITE_TOOLS` and dispatch;
  `_mem_consolidate` handler gathers the given source ids from `by_id`, runs
  `consolidate` with `charge=self.budget.charge_memory_write` (one charge per
  governed sub-write), writer identity from the session (never a tool arg).
  `ok = result.produced`, honest `reason_code`.

**Edit — `src/agentic_runtime/tool_contracts.py`**
- `mem_consolidate` contract (`memory_ids` required; `threshold`/`min_size`
  optional); `"summarizes"` added to `_MEMORY_RELATIONS`.

**Edit — `src/agentic_runtime/praxis.py`**
- `submit_consolidation_to_governance(fabric, records, *, run_id, threshold,
  min_size)` — a standalone adapter mirroring `submit_memory_candidate_to_governance`,
  routing runtime-side consolidation through `consolidate(..., writer_kind="runtime")`.

## How consolidation stays CANDIDATE + governed

`proposed_truth_state` is **hard-coded** `MemoryTruthState.CANDIDATE` in
`consolidate` — no caller can request higher, and CANDIDATE is re-scored by
`evaluate_write` like any write. There is no parallel write path: the summary goes
through `fabric.request_write` and the edges through `fabric.link`. Seal §2 asserts
the summary record is CANDIDATE; §4 asserts an **agent**-triggered consolidation
still yields CANDIDATE (no elevation), and no source is promoted.

## Determinism proof

Clustering sorts records by `memory_id` and uses the deterministic `HashingEmbedder`
cosine — no `hash()` ordering, no randomness. Seal §1: `cluster_memories` called
twice on the same records yields identical groupings; `summarize_cluster` is
byte-identical; and a **second fresh fabric** with the same contents produces the
**same summary text** (because `summarize_cluster` keys on content, not the uuid
`memory_id`). Cosine separation on the seal data is wide (~0.68–0.84 within-cluster
vs ~0.10 across), so cluster membership is robust at `threshold=0.5`.

## Provenance preservation

The summary carries every source id in `evidence_refs` **and** `links`, plus a
`SUMMARIZES` edge summary→source for each source. Seal §2 asserts
`graph.neighbors(summary, SUMMARIZES) == sorted(source_ids)`, `evidence_refs`/`links`
== source ids, and — crucially — that every **source record is byte-for-byte
unchanged** (content, truth_state, superseded_by) after consolidation.

## No auto-canonize proof

Seal §2/§4: the summary is CANDIDATE for both operator and agent sessions;
consolidation never proposes VERIFIED/PROCEDURAL/CANON and never promotes a source.
Seal §5: degenerate/empty clusters mint nothing (no fabricated summary).

## Governance / trace invariants

- **One governance row per governed write.** Seal §2: exactly one `action="write"`
  row for the summary (`memory_id == summary_id`) and one `action="link"` row per
  `SUMMARIZES` edge (3); zero `StateTransitionRecord`.
- **One charge per sub-write.** Seal §2: `memory_writes == 4` (1 summary + 3 edges),
  `sandbox_executions == 0`.
- **Fail-closed.** Seal §5: dissimilar pair / empty / single id ⇒ `ok=False`,
  `no_consolidatable_cluster`, nothing written, nothing charged, no edges.
- **No-collapse.** Seal §7: an unrelated promoted (VERIFIED) record is untouched;
  `mem_add` and `retrieve` still work after consolidation.

## Spec-vs-code drift + decisions

- **D1 — provenance via `evidence_refs`/`links` + edges, not `source_trace_ids`.**
  The task mentions the summary's `source_trace_ids` pointing back to sources, but
  `evaluate_write` validates `source_trace_ids` as **trace entry ids** (unknown ⇒
  `invalid_trace_reference`). Source **memory** ids are not trace ids, so putting
  them there would fail governance. Smallest correct honest path: provenance rides
  `evidence_refs`/`links` (source memory ids) and the canonical `SUMMARIZES` edges;
  `source_trace_ids` is left governance-clean. Noted.
- **D2 — edges are separate governed link ops (one row each).** Consistent with A2
  and the task's "one governance row per consolidation write + edges": the summary
  is one `write` row; each `SUMMARIZES` edge is one `link` row; total = 1 + N. The
  tool charges once per sub-write (N+1).
- **D3 — `mem_consolidate` takes explicit `memory_ids`.** The caller proposes the
  candidate source set; the session clusters within it (deterministic), rather
  than scanning the whole store. Keeps the tool bounded, deterministic, and
  fail-closed (unknown ids are filtered; too-few survivors ⇒ no cluster).
- **D4 — praxis integration is a standalone adapter**, mirroring
  `submit_memory_candidate_to_governance`, rather than wiring into
  `process_experience` (minimal, matches the existing pattern; deeper metabolism
  wiring is out of A5 scope).
- **Durable (A3):** consolidation writes via the normal `request_write`/`link`
  funnels, so on a `DurableMemoryFabric` the summary + edges persist and rebuild
  normally (unlike A4's in-place revision) — no special handling needed.

## Validation (focused-first; full ~25 min suite intentionally skipped)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 5 source files.
- Seal `test_p6a5_consolidation.py` — **5 passed**.
- Directly-affected regression (timeout-wrapped): memory_p09, memory_write_policy_cards_p167,
  tool_contract_p10, tool_registry_p133, builtin_tool_manifests_p138, p6a0–p6a5 → **191 passed**;
  plus praxis_p16 + dual_kernel_praxis → **26 passed**. **0 failed.**

## Next: A6 — Hybrid retrieval

`memory_retrieval.py` (vector cosine + stdlib BM25-lite + graph expansion + as-of
filter + deterministic RRF sorted by `(score, memory_id)`), `memory_embedder.py`
(`NeuralEmbedderSeam` UNAVAILABLE). **Cross-lock:** if `assemble_context`
signature/behavior changes, co-update Track B's B2 (`difficulty_estimator`).
