# Track A / A3 — DurableMemoryFabric (durable memory as a trace projection)

**Date:** 2026-07-07
**Branch:** `feat/track-a-memory` (unmerged, not pushed)
**Status:** DONE (additive; byte-identical when the flag is OFF).

## Summary

A3 makes memory durable **without** making the durable store a second source of
truth. `DurableMemoryFabric` mirrors every governed write (record) and edge to a
JSONL backend, and can rebuild the in-RAM store from that backend — but on
rebuild it re-verifies each persisted entry against the governed trace and
**quarantines** anything the trace does not attest. The trace stays the single
source of truth; disk is a projection.

```
write  →  MemoryFabric funnel (governs + traces)  →  _store  →  backend.append   (mirror)
rebuild:  backend.load()  →  re-verify vs bound trace  →  admit | QUARANTINE     (projection)
```

## Files changed

**New — `src/agentic_runtime/memory_persistence.py`**
- `atomic_write_text(path, text)` — temp sibling → `fsync` → `os.replace` → `fsync` dir (state_store's crash-safety idiom for a single file); a reader never sees a partial write.
- `FileMemoryBackend` — append-only JSONL; each `append` buffers then rewrites the whole log atomically with `json.dumps(sort_keys=True)` (deterministic); lazy (no file until first append); defensive parse skips any corrupt line.
- `ExternalMemoryBackend` — declared but honestly **unavailable**: constructible, `available` is a read-only `False`, every op raises `MemoryBackendUnavailable`. No faked durability.
- `MemoryBackend` Protocol + `MemoryBackendUnavailable`.

**New — `src/agentic_runtime/durable_memory.py`**
- `DurableMemoryFabric(MemoryFabric)` — reads `AUREL_DURABLE_MEMORY` **once at construction** (`_persist_enabled`); `durable_enabled` also requires `backend.available`. Overrides `_store` (mirror admitted record — promotions re-store ⇒ append a new version line) and `link` (mirror allowed edge). `load(trace=None)` rebuilds: dedupe records by `memory_id` keeping the last (append-only ⇒ current), admit anchored ones via the non-persisting base `_store`, then admit edges; returns a `list[DurableMemoryGovernanceRecord]` (also on `quarantine_report`), with `quarantined()` helper.
- Re-verification: `_record_anchored` = every `source_trace_ids` ∈ known trace entries **and** the trace carries a governed *allow* event for the record's `memory_id`; `_edge_anchored` additionally requires both endpoints admitted (an edge to a quarantined endpoint is quarantined). Reason codes: `anchored`, `unverified_source_trace`, `unanchored_no_governance_event`, `endpoint_quarantined`.
- Deterministic record/edge JSONL (de)serializers; embedding dropped on persist and recomputed on admit (compact + deterministic via `HashingEmbedder`).

**Edit — `src/agentic_runtime/core_types.py`**
- New `DurableMemoryGovernanceRecord` (id, run_id, action=`load_record`/`load_edge`, verdict=`admit`/`quarantine`, memory_id, reason_code, source_trace_ids, + `payload_hash`/`prev_entry_hash`/`entry_hash`/`to_dict`) — a hash-chainable audit atom for each rebuild decision.

## How durability projects over the trace

- **Nothing is admitted the trace doesn't attest.** On rebuild, `allow_writes` /
  `allow_links` are drawn from the trace's `memory_governance` *allow* rows and
  `known_ids` from the trace entries; a JSONL entry survives only if it matches.
  A poisoned/injected record (memory_id absent from the trace) is quarantined —
  this is the memory-poisoning defense the funnel was built for, now extended to
  the durable surface.
- **Append-only on disk, current-state in RAM.** Promotions append new version
  lines; rebuild keeps the last version per `memory_id`, so the projection is the
  current belief while history stays on disk.

## Flag goes load-bearing (as required)

`AUREL_DURABLE_MEMORY` is now **load-bearing** in A3 (A0–A2 defined it but branched
on nothing). Read once at construction:
- **OFF (default):** `durable_enabled` is False ⇒ `_store`/`link` never touch the
  backend, `load()` is a no-op, no file is created. `DurableMemoryFabric` is
  structurally **byte-identical** to `MemoryFabric` (seal §1 proves equal
  `stats()`/graph size/retrieval, and no file on disk).
- **ON:** records + edges persist and rebuild against the trace.

No wiring into `build_runtime`/entity (that is A8 — the durable factory +
fail-closed-to-RAM fallback). No revision/retract (A4). No retrieval re-rank (A6).

## Quarantine behavior + how tested (seal `tests/test_p6a3_durable_memory.py`, 7)

- §1 flag OFF ⇒ no persistence, byte-identical, `load()` no-op.
- §2 flag ON ⇒ 3 JSONL lines (2 records + 1 edge); **two rebuilds ⇒ identical**
  `stats()`/`by_id`/graph and identical report (deterministic).
- §3 injected poison record (`mem_poison`, never governed) ⇒ **quarantined**
  (`unanchored_no_governance_event`), absent from `by_id`; legit record admitted.
- §3b record with dangling `source_trace_ids` ⇒ **quarantined**
  (`unverified_source_trace`).
- §4 atomic write — `os.replace` monkeypatched to raise mid-write ⇒ prior complete
  file intact, no `.tmp-` leftover.
- §5 `ExternalMemoryBackend.available is False`; `append`/`load` raise; a durable
  fabric wrapping it has `durable_enabled False`, still writes in RAM, `load()`
  inert — **no overclaim**.
- §6 no-collapse — flag ON, in-RAM write/promote(candidate→verified)/link/retrieve
  identical to a plain fabric.

## Spec-vs-code drift + decisions

- **D1 (main) — `DurableMemoryGovernanceRecord` is a returned report, not a ledger
  append.** The spec lists it as a `core_types` edit; the natural reading is that
  rebuild decisions feed the hash-chained trace. Adding a new `append_*` across the
  `TraceLedgerBackend` Protocol + both ledger implementations + `replay()` is broad
  surface for A3. Smallest correct honest path: ship the named type as a
  **hash-chainable** record and have `load()` **return** the admit/quarantine
  report (and expose it on `quarantine_report`). The invariant holds — durable load
  admits nothing the trace doesn't attest, so the report is a projection, not a
  competing authority — and A8 can append these to the ledger when it wires the
  durable factory. Noted so A8 closes the loop.
- **D2 — re-verification is within-session (bound trace), not cross-run.** "Re-verify
  against the bound trace" only defends if the trace that attests the records is
  present. A3 verifies against the **currently bound** trace (defends against
  tampering/poisoning of the JSONL within a session). **Cross-run durability** (a
  persistent trace spanning process restarts, via the `trace_anchor` / persistent
  ledger) is out of A3 scope — the *mechanism* is sealed here; wiring a durable
  trace across runs is deferred (A8/beyond). Flagged as a known seam.
- **D3 — full-file atomic rewrite per append.** Rather than `O_APPEND` line writes
  (which can leave a partial last line on crash), each append re-serializes the
  whole log and `os.replace`s it, matching state_store's "never a partial state
  visible" guarantee. Fine for realistic memory sizes; revisit if logs get large.
- **D4 — edges persisted too.** The spec says "overrides store/relocate/link"; A3
  persists records (via `_store`, which `_relocate` calls on promote) **and** edges
  (via `link`). An edge to a quarantined endpoint is itself quarantined (fail-closed).
- **Minor — embedding dropped on persist** (recomputed deterministically on admit);
  `ExternalMemoryBackend` is the no-overclaim seam the masterplan names.

## Validation (focused-first; full ~25 min suite intentionally skipped)

- `compileall` OK; `ruff` clean; `python -m mypy` — no issues, on the 3 source files.
- Seal `test_p6a3_durable_memory.py` — **7 passed**.
- Directly-affected regression (timeout-wrapped): memory_p09, memory_write_policy_cards_p167, tool_contract_p10, tool_registry_p133, builtin_tool_manifests_p138, p6a0, p6a1, p6a2, p6a3 → **180 passed**; plus state_store_m0 + trace_persistence_p06 → **19 passed**. **0 failed.**

## Next: A4 — Belief revision

`memory_revision.py` (`apply_update`/`retract`/`forget` → governed requests);
edit `memory_tools.py`, `memory_governance.py`. Non-destructive: `mem_forget`
marks retention only; FORGET forbidden on audit (rejected/canon/policy);
as-of-past returns pre-revision belief. This is where `mem_update`/`mem_delete`
flip from `requires_a4` to live, and where record-field supersession
(`superseded_by`/`revises` + interval closure) is wired to reconcile with A2's
edge-only supersession.
