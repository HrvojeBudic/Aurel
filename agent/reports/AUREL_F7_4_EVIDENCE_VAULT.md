# AUREL F7.4 — Operations.Evidence Vault: trace search + receipt export (Output Passport)

_2026-07-11, branch `feat/f7-corp`. Completes the Output Passport — a receipt per job, with integrity._

## What shipped

The Evidence Vault answers *what happened, for whom, and can I prove it?* — read-only over the trace. It
**completes the Output Passport**: for a job (or run/mandate) it exports a self-contained bundle whose
integrity is checkable offline, built on the **real P5 verification machinery** (not a reinvented hash).
Additive behind `AUREL_CORP`.

- **`corp/evidence_vault.py`** — `EvidenceVaultQuery(trace, corp_registry=None)`:
  - `search(mandate_id, client_id, kind, run_id, limit)` — filters the business-visible records
    (budget/approval/praxis/status/memory) in deterministic replay order; a `client_id` resolves to its
    jobs' mandate_ids via the Corp registry (F7.0); each hit carries a deterministic `content_ref`; an
    empty result is empty (not UNAVAILABLE); `limit` truncates and says so (`truncated`).
  - `export_receipt_bundle(job_id | run_id | mandate_id)` — assembles the Output Passport:
    `{filtered records + chain_head_hash + a real P5 TraceVerificationReceipt}`. `verified` is derived
    **only** from an actual full-chain verification (`trace_run_ref_from_ledger` → `envelopes_from_ledger`
    → `verify_canonical_trace_hash_chain` → `build_trace_verification_receipt`) — `True` iff the chain
    PASSes (P5-TRACE-B never upgrades FAIL/PARTIAL). A tampered trace verifies FAIL ⇒ `verified=False`,
    and the bundle carries the chain head so the tamper is visible. An unknown job fails closed
    (`available=False`); an unverifiable trace is honestly not verified, with a reason.
- **`cli_modules/f7_commands.py` + `cli.py`** — `aurel corp vault [--mandate|--client|--kind|--run]
  [--json]` and `aurel corp export [--job|--run|--mandate] [--out PATH]` (read-only over the current
  runtime's trace; `export --out` writes the bundle JSON).

## Evidence

- Seal `tests/test_p6f7_4_evidence_vault.py` — **10 passed**: search by mandate returns exactly that
  mandate's records; client search via the registry; search by kind; empty result is empty; `limit`
  truncates honestly; export bundle carries a P5 receipt + chain head and **verifies PASS**
  (`TRACE_INTEGRITY_VERIFIED`); unknown job fails closed; **a tampered record ⇒ `verified=False`, status
  ≠ PASS**; the Vault is zero-write; klijent nula's default job exports cleanly.
- CLI smoke: `aurel corp vault` (0 records on a fresh runtime) and `aurel corp export --job job-zero`
  (honest `verified: false` on the empty chain, no crash). ruff + mypy clean. Front + F7 + aurel_trace
  receipts regression: **92 passed, 0 failed** (~0:41).

## Boundary (honest)

Search + export are **read-only over the trace** — zero mutation. `verified` is never a fabricated PASS;
it comes only from the P5 chain verification, which fails closed on tamper. Per-event refs are
deterministic **content** refs (the replay projection does not expose per-entry chain hashes); the
**bundle-level** integrity is the real P5 receipt + chain head. `run_id` filtering only matches records
that expose a `run_id` on replay (today: runtime status transitions) — the robust bundle key is `job_id`
(mandate-based, covers every record type carrying `mandate_id`). The CLI operates on the current runtime's
trace (a fresh runtime is near-empty); a real deployment points it at a live/persisted trace.

## Next

- **F7.6** — Agency wizard (environment templates + what-if dry-run through the real mandate gate).
- Then F7.7 Risk Register, F7.8 workbench, F7.9 KPI + React, F7.10 derived exit seal.
