# AUREL F4.0 — ContextLoom Foundation (Governed Context Assembly)

_2026-07-09, branch `feat/f4-cognition-contextloom` (from the F3 tip). First F4 slice._

## What shipped

New package `src/agentic_runtime/context_loom/` — the governed upgrade of plain
context concatenation (`memory.assemble_context` is a bare string join with no
provenance / taint / budget / hash). Pure-library, stdlib-only, deterministic:

- **`context_item.py`** — `ContextItem` carries content **plus provenance** (F3.0
  `SourceKind` + derived `TaintLabel`) and therefore `instruction_eligible`
  (external origin ⇒ always False, reusing the F3.0 doctrine). `make_context_item`
  derives the label from provenance alone (no forging), assigns a default priority
  per origin (operator/internal high, external low), a sha256 content hash, and an
  honest char/4 token estimate (labelled — not a real tokenizer).
- **`loom.py`** — `assemble` turns items into a deterministic, content-addressed
  `ContextBundle`: **dedup** by content hash, **deterministic order**
  (`-priority, content_hash`; no RNG/`hash()`), **budget-aware with no silent loss**
  (a `max_tokens` ceiling drops lowest-priority items and *records* every
  `DroppedItem`), and a **`context_ref`** (sha256 over ordered item hashes) — the
  Front Signal reference and trace/replay key. `to_prompt` enforces the doctrine:
  instruction-eligible items render plainly; external items are **fenced as
  untrusted data**, so the model can read them but never obey them.
- **`__init__.py`** — exports + flag `AUREL_CONTEXTLOOM` (defined-not-gating).

## Evidence

- Seal `tests/test_p6f4_0_context_loom.py` — **12 passed**: external instruction-
  ineligible / internal eligible / priority ordering; deterministic + content-
  addressed + dedup + ref-changes-with-content + empty-input-stable; budget drops
  lowest-priority and records it / no-budget keeps all; render fences external as
  data / no fence when all internal; flag default OFF.
- ruff clean; mypy clean (3 source files); compileall OK.
- **Purely additive** — no existing file modified (`assemble_context` byte-identical).

## Next

**F4.1 — budget-aware compression.** Deepen `assemble`'s budget fitting beyond
drop-only: deterministic truncation/summary of oversized items (provenance
preserved, compression recorded), so a single large item can be fit rather than
wholly dropped. Seal `test_p6f4_1_context_compression.py`.
