# Track A / A7 — Memory Explorer projection + CLI; close the D2 replay seam

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (additive; closes the A2/A3/A4 "D2" seam).

## Summary

A7 adds a **read-only** Memory Explorer that reconstructs the memory picture
*from the governed trace alone* (with the A3 durable store as an optional source
of record *content*), and a `memory` CLI surface mirroring the `reasoning` pattern.
To make a pure trace rebuild possible, it **closes the D2 seam**: edge and revision
specifics that previously lived only in the governance-row `details` — which
`trace.replay()` dropped — are now surfaced by `replay()`, so the graph and
belief-history views reconstruct from the trace with no fabric.

## Files changed

**Edit — `src/agentic_runtime/trace.py` (the D2 fix)**
- Both `replay()` implementations (`InMemoryTraceLedger`, `PersistentTraceLedger`)
  now add `"details": dict(rec.details)` to the yielded `memory_governance` dict.
  This is **purely additive** — every pre-existing key
  (`kind`/`issuer`/`action`/`verdict`/`memory_id`/`from`/`to`/`reason_code`) is
  unchanged. The persisted JSONL event already carried `details` (and
  reconstruction already read it), so only the in-memory dict projection needed
  the field. No schema/record-type churn.

**New — `src/agentic_runtime/memory_projection.py`**
- `MemoryProjection.from_trace(trace, backend=None)` / `.from_events(...)` — folds
  the ordered `memory_governance` events into read-only views:
  - **current_ids** — allowed writes/promotions/update-successors (first-seen
    order), minus any record later superseded (update), retracted, or forgotten.
  - **edges** (`edge_tuples()`) — A2 `link` rows via `details`
    (`from_id`/`to_id`/`relation`/`edge_id`) **plus** the A4 `SUPERSEDES`
    reconciliation edge synthesized from each `update` row's
    `target_id`/`new_memory_id` (A4 adds that edge inside the update op with no
    separate `link` row — see A4-D1 — so the projection reconstructs it from the
    update details to match the live graph).
  - **belief_history(id)** — the supersession chain from `revises`/`superseded_by`
    reconstructed from `update` rows.
  - **rejected** — governance *deny* rows (reason_code, action).
  - **content** — optional, from the A3 durable JSONL (by `memory_id`); `None`
    when no store is supplied (honest, never fabricated).
  Deterministic (every list sorted by a stable key); fail-closed (empty/absent
  trace ⇒ empty views; unknown id ⇒ `[]`).

**New — `src/agentic_runtime/cli_modules/memory_commands.py`**
- `memory explore` (current records + edge/rejected counts, + content when
  `--durable` is given), `memory history <memory_id>` (belief chain), `memory graph`
  (typed edges), `memory rejected` (deny rows). All read a `PersistentTraceLedger`
  under `--trace-dir`, project read-only, and support `--json`. Fail closed on a
  missing run (checks the events path *before* constructing the ledger, since
  constructing one materializes an empty run dir).

**Edit — `src/agentic_runtime/cli.py`**
- Registers the `memory` subparser group (`explore/history/graph/rejected`) with
  the shared `run_id` / `--trace-dir` / `--durable` / `--json` args, mirroring the
  `reasoning` group.

## Projection design (trace-only rebuild)

The trace carries governance *structure* (ids, states, verdicts, edge endpoints/
relations, revision pointers) but not record *content*. So the structural views
(current records, graph, belief-history, rejected) rebuild from the trace alone;
content is layered in only when the A3 durable store is provided. The projection
never reads a `MemoryFabric` — it consumes `replay()` events, so it is a true
projection over the single source of truth.

## How D2 was closed + replay-consumer updates

**Root cause:** `MemoryGovernanceRecord.details` (carrying edge
`from_id`/`to_id`/`relation`/`edge_id` for `link` rows and `target_id`/
`new_memory_id` for `update` rows) was hash-covered and persisted, but the
`replay()` dict projection omitted it — flagged as D2 in the A2/A3/A4 reports.

**Fix:** add `details` to the two `replay()` `memory_governance` branches (one
line each). **Additive** — no key removed or renamed.

**Consumer/test impact:** a grep found **no** test asserting the exact
`memory_governance` replay dict (no `== {...}` equality); all consumers
(`durable_memory._trace_index`, `cli_modules/governance_commands`,
`reasoning_commands`, demo harnesses) read specific keys via indexing/`.get()`, so
an added key is safe. Regression across every replay consumer
(trace_persistence, praxis, hitl, budget, state_machine, m6_governance_scale,
p6a0–p6a7) passes unchanged — **no consumer or test needed updating.**

## CLI commands added

`agentic-runtime memory explore|history|graph|rejected <run_id> [--trace-dir DIR]
[--durable JSONL] [--json]` — all read-only projections; verified via `main()`
end-to-end (parse → dispatch → honest fail-closed on a missing run).

## Trace-only == fabric proof

Seal §1: after a mixed workload (writes, a link, a promotion, an `mem_update`, and
a denied write), `MemoryProjection.from_trace(trace)` — handed only the trace —
equals the live fabric: `current_ids` == the fabric's current set, `edge_tuples()`
== `fabric.graph` edges (including the A4 SUPERSEDES edge), `belief_history(new)`
== `AsOfView.belief_history(new)`, and `rejected` count/reason == `fabric.rejected`.

## Seal (`tests/test_p6a7_memory_projection.py`, 6)

1. trace-only projection equals the live fabric across all four views.
2. D2 closed — `link` rows carry `from_id/to_id/relation/edge_id` and `update`
   rows carry `target_id/new_memory_id` in `replay()` details.
3. fail-closed — empty trace ⇒ empty views; unknown id ⇒ `[]`; content `None`
   without a durable store; `from_trace(None)` ⇒ empty.
4. durable store enriches records with content (A3).
5. CLI `explore/history/graph/rejected` return honest deterministic JSON; a bad
   run id fails closed (exit 1, structured error, no fabrication).
6. no-collapse — replay `details` is additive (all prior keys present);
   `retrieve`/`assemble_context` still work.

## Spec-vs-code drift + decisions

- **D1 — D2 closed by surfacing `details` in `replay()`, not by new record types.**
  Smallest correct honest path: the persisted event already carried `details`;
  only the dict projection needed it. One additive line per ledger; no
  `TraceLedgerBackend` Protocol / schema churn.
- **D2 — the A4 SUPERSEDES edge is reconstructed from the `update` row.** A4 adds
  that graph edge inside the update op (no separate `link` row, per A4-D1), so the
  projection synthesizes the matching `(new SUPERSEDES old)` edge from the update
  `details` — otherwise trace-only edges would be one short of the live graph.
- **D3 — rejected records compared by count/reason, not id.** Governance *deny*
  write rows carry `memory_id=""` (the denied write has no admitted record id),
  while the fabric keeps a rejected record with its own id — so the projection
  reports deny rows (count + reason_code) rather than inventing ids. Honest.
- **D4 — content only with a durable store.** The trace has no record content;
  `memory explore --durable <jsonl>` adds it, else content is `None` (no overclaim).
- **No new flag.** Projection + CLI are read-only and additive; nothing gated.

## Validation (focused-first; full ~25 min suite intentionally skipped)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 4 source files.
- Seal `test_p6a7_memory_projection.py` — **6 passed**.
- Directly-affected regression (timeout-wrapped): memory_p09, tool_contract_p10,
  tool_registry_p133, builtin_tool_manifests_p138, **trace_persistence_p06**,
  state_store_m0, state_machine_p07, budget_p08, hitl_p15, praxis_p16,
  m6_governance_scale, p6a0–p6a7 → **229 passed**; plus a read-only CLI suite
  (`test_p3_flow_c_cli_read_only`) **9 passed** and a `main()` parser smoke.
  **0 failed.**

## Next: A8a / A8b — Live promotion

A8a: `build_runtime` reconstructs a durable fabric, fails closed to in-RAM. A8b:
`runtime._record_command_memory` submits Praxis/eval candidates; promotion
monotonicity (two successes ⇒ procedural; failed run ⇒ no promotion).
