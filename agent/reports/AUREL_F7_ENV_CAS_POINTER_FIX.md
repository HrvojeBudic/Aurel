# AUREL F7 — environment payload CAS-pointer: no silent truncation

_2026-07-12, follow-up bugfix to F7 corp_create_environment. Latent data-loss bug found by design review, confirmed by reproduction, fixed additively._

## The bug (real, reproduced)

`PraxisEventRecord.make` caps `summary` at 500 chars (`core_types.py`, `summary[:500]`).
`record_environment` wrote the **full canonical JSON payload** into the summary
(`ENV|{json}`), and `corp_registry_from_trace` parsed it back with `json.loads`.
A {client + job + mandate} payload over ~496 chars (long names, several scope paths/tools,
memory-zone rules) was **silently truncated at append time**: the event still chained and
verified, but the projection's parse failed, `_env_from_summary` returned `None`, and the
loop `continue`d — the environment **silently vanished from the registry** (portfolio, cost,
budget, workbench all lost it). Reproduced: a realistic long-named environment produced a
500-char summary and a registry containing only klijent nula.

## The fix (CAS-pointer, additive)

- **`corp/environment.py`** — the summary now carries only the payload's content address,
  `ENV|sha256:<sha256 of canonical_json(payload)>` (75 chars, can never hit the cap); the
  **full payload rides in the event's `details["env"]`** — `details` is already part of
  `payload_hash()` (hash-chained, tamper-evident), persisted in the JSONL event payload,
  and reconstructed by `_record_from_event` on reload. The store is the governed trace
  record itself, not the world-state `StateStore` (that is a tree-CAS keyed by
  `_tree_hash`, and the registry is doctrinally a **projection over the trace** — read
  models hold no store handle, and in-memory runtimes have none).
- **Read side** — new `_env_from_event`: prefer `details["env"]` (pointer format), fall
  back to the legacy inline `ENV|{json}` summary. **Append-only compatibility**: every
  pre-fix event on an existing trace keeps projecting byte-identically. (A pre-fix event
  that was *already* truncated never persisted its payload — it stays skipped, unrecoverable
  by construction.)
- **`trace.py`** — both `replay()` implementations (in-memory + persistent) now surface
  `details` on `praxis_event`, guarded `if rec.details:` per the F6 `mandate_id` convention
  (**empty ⇒ dict unchanged**, so every existing event's replay dict is byte-identical).
  Same seam A7 closed for `memory_governance`: the data was persisted but invisible to a
  pure replay. Side effect (derived-only): praxis events that already carried details
  (entity checkpoints, dual-kernel) now show them in replay, so their Evidence-Vault
  `content_ref` re-derives — nothing chain-stored changes.

## Evidence

- `tests/test_p6f7_create_environment.py` grew 4 tests (**10 passed**): a >500-char payload
  round-trips through `corp_registry_from_trace` field-for-field (scope paths/tools/budget,
  zone rules); the summary is a bounded `ENV|sha256:` pointer whose digest equals the
  content address of `details["env"]`; a legacy inline-summary event on the same trace still
  projects; a large environment survives a `PersistentTraceLedger` write → reload from disk.
- Full test suite regression: **9108 passed, 3 skipped, 0 failed** — the additive replay
  `details` broke no consumer (all praxis readers use `ev.get`). ruff clean; mypy: only the
  2 pre-existing `aurel_flow/flow_resource_prediction.py` errors (present on master, untouched).

## Boundary (honest)

- Pre-fix events that were already truncated are permanently unparseable — the payload
  bytes were never written. The projection skips them exactly as before; no repair pass.
- The pointer digest is not re-verified against `details["env"]` at projection time — chain
  verification (`verify_chain` / P5 receipts) already covers integrity; the digest is a
  stable content address for audit and cross-referencing.
