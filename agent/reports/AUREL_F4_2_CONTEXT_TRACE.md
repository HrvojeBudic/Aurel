# AUREL F4.2 — Context Trace Binding (`context_ref` → trace)

_2026-07-09, branch `feat/f4-cognition-contextloom`. Third F4 slice (after F4.0 foundation, F4.1 compression)._

## What shipped

New `context_loom/context_trace.py` — binds every assembled `ContextBundle` into the
hash-chained trace, so every context an entity reasons over is auditable and replayable.

- **`bind_context_to_trace(trace, run_id, agent_id, subject_id, bundle)`** — appends a
  `context_assembly` `PraxisEventRecord` (the existing hash-chained event vehicle, same
  one `entity.py` uses for reasoning events). Returns the record.
- **Replay-safe by design.** A pure trace replay carries praxis-event *summaries*, not
  details — so the bundle's `context_ref` is placed in the **summary** (not only
  details). `context_refs_from_replay(trace.replay())` reconstructs the Front Signal
  `context_refs` from the trace alone.
- **Leak-safe.** The event carries the `context_ref` + provenance (item hashes, source
  kinds, taint labels, drops, compressions) via `ContextBundle.to_dict`, which **excludes
  raw content**. The trace holds references, never the data — a scraped/tainted payload's
  text never lands in the trace.

## Evidence

- Seal `tests/test_p6f4_2_context_trace.py` — **5 passed**: binding appends a hash-chained
  `context_assembly` event (head advances); `context_ref` survives a pure replay and is
  reconstructed by `context_refs_from_replay`; multiple assemblies → ordered refs;
  **leak-safe** (raw scraped content absent from both summary and details, while its
  content hash IS present for audit); deterministic details.
- ruff clean; mypy clean (5 source files); compileall OK. Full F4 suite (F4.0+4.1+4.2)
  **25 passed**.
- **Purely additive** — no trace.py change (the context_ref-in-summary design avoids the
  A7-style replay-details surgery); only my own `context_loom/__init__.py` edited.

## Next

**F4.3 — interactive ReAct loop.** An `entity_loom_loop` that drives observe→think→act
through `runtime.submit`, assembling context each turn via the ContextLoom (F4.0–4.2:
provenance + taint + budget + trace-bound `context_ref`), router by intent, cassette by
default. Byte-identical to today's `AgenticEntity` when the flag is OFF. Seal
`test_p6f4_3_entity_loop.py`.
