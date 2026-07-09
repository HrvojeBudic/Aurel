# AUREL F4.1 — Budget-Aware Context Compression

_2026-07-09, branch `feat/f4-cognition-contextloom`. Second F4 slice (after F4.0 ContextLoom foundation)._

## What shipped

F4.0's budget fitting was drop-only at item granularity — a high-priority item bigger
than the budget was dropped whole. F4.1 makes items **compressible-to-fit**.

- **`context_loom/compression.py`** — `compress_item(item, max_tokens)` does
  **deterministic extractive truncation**: a head+tail slice with a middle-elision
  marker (`…[elided]…`), sized so `kept_tokens ≤ max_tokens`. It is honestly labelled
  `TRUNCATE_HEAD_TAIL` — **not** semantic summarization (no model call), so nothing
  overclaims an AI summary. Provenance is preserved (source kind, origin ref, priority,
  taint label, instruction-eligibility all unchanged); only the content shrinks, so it
  gets a fresh hash with the original hash retained in a `CompressionRecord`. Below
  `MIN_COMPRESS_TOKENS` (8) there is no viable slice, so the caller drops instead.
- **`context_loom/loom.py`** — `assemble` gains `compress: bool = False`. When set, the
  first overflowing (highest-priority) item is compressed into the remaining budget
  instead of dropped; if the remainder is `< MIN_COMPRESS_TOKENS` it is dropped. Every
  compression is recorded in the new **additive** `ContextBundle.compressed` field —
  **no silent loss**. `compress=False` (default) is byte-identical to F4.0 drop-only.

## Evidence

- Seal `tests/test_p6f4_1_context_compression.py` — **8 passed**: deterministic head+tail
  truncation within budget, elision marker present, record links original hash;
  deterministic across runs; provenance preserved (external stays ineligible, new hash);
  no-op when it already fits; `assemble(compress=True)` compresses an overflowing item
  instead of dropping (recorded) and drops when remainder < MIN (recorded in dropped, not
  compressed); `compress=False` is drop-only; a compressed external item stays
  instruction-ineligible + DATA-fenced in `to_prompt`.
- **F4.0 seal still green (12)** — the `compressed` field is additive (default empty),
  `compress=False` reproduces F4.0 exactly.
- ruff clean; mypy clean (4 source files); compileall OK. Only edited files are my own
  F4.0 modules (`loom.py`, `__init__.py`) — additive.

## Boundary (honest)

Compression is **extractive truncation, not summarization** — deterministic char slicing,
no model, no meaning-preservation guarantee beyond keeping head + tail. It is a budget
mechanism, not a comprehension one; a caller that needs faithful semantic compression
must do it upstream (and record it) before handing items to the Loom.

## Next

**F4.2 — trace binding.** Record each assembled bundle's `context_ref` (+ item provenance
and any drop/compression) as a trace event, so every context an entity reasoned over is
auditable and replayable — the Front Signal `context_refs`. Seal `test_p6f4_2_context_trace.py`.
