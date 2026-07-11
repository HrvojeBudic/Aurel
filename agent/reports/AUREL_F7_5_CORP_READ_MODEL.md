# AUREL F7.5 — CORP surface read-model: portfolio tree + task-runtime feed

_2026-07-11, branch `feat/f7-corp`. Closes the F7 walking skeleton (F7.0 → F7.1 → F7.5)._

## What shipped

The CORP surface gets its home projection: a **portfolio tree** (client → job → mandates → runs, with a
status overlay) and a **task-runtime feed** (the chronological trace stream, filterable by job). Both are
**pure projections** over the trace + the Corp registry (F7.0) + the cost view (F7.1) — zero writes, no
new store, registered on the existing one-door read registry.

- **`front_server/corp_read_model.py`** — `CorpReadModel.from_runtime(runtime, corp_registry=None)`
  (falls back to `default_corp_registry()` = klijent nula when none is bound). Two views:
  - `portfolio_view()` — resolves each run to its job through the `mandate_id` every
    `runtime_status_transition` carries (F6.1) → the mandate's job (F7.0's `_mandate_to_job_map`), latest
    transition per run as the status overlay. A run whose mandate maps to no job (or carries none) is
    reported as **`unassigned`** — the link is never invented. Cost per job/client comes from
    `CostAttributionView.from_ledger` (F7.1); with no ledger the cost block is honestly `UNAVAILABLE`,
    never a fabricated zero. Alerts (**F7.3 Watchtower**) and budget governance (**F7.2**) are declared
    `UNAVAILABLE` seams with their owner, and `CLAIMS_ALERTS_LIVE` / `CLAIMS_BUDGET_GOVERNANCE_LIVE` are
    hard-wired `False` so the not-yet-built surfaces cannot be over-claimed.
  - `runtime_feed(job_id="")` — the chronological (replay-order) stream of status transitions / approval
    receipts / budget decisions; a `job_id` filters to events carrying one of that job's mandate_ids;
    an unknown job fails closed (`available=False` + reason).
- **`front_server/read_models.py`** — registers `corp/portfolio` and `corp/runtime` (the latter takes an
  optional `?job=` param), consistent with how `aureleu` is registered regardless of its flag (reads are
  pure projections). **`front_server/__init__.py`** exports `CorpReadModel` + the two claim constants.

## Evidence

- Seal `tests/test_p6f7_5_corp_read_model.py` — **10 passed**: portfolio tree maps runs to klijent nula's
  job via the default mandate + status overlay = latest transition; unassigned runs honest (orphan mandate
  + mandate-less, never forced into a job); cost overlay present with a ledger and `None`/`UNAVAILABLE`
  without one; alerts + budget governance UNAVAILABLE seams with owners + claim guards False; runtime feed
  filters by job (only that mandate's events), unfiltered shows all, unknown job fails closed; zero-write;
  live via `/read/corp/portfolio` and `/read/corp/runtime?job=…`.
- ruff clean; mypy clean. Front-server + F6 + F7 regression (live-read-models / hq-command / front-exit-seal
  / one-door / library / board / aureleu-surface / dn / f6-exit-seal + F7.0/F7.1/F7.5): **94 passed, 0 failed** (~3:00).

## Boundary (honest)

Pure projection, **zero writes** — the CORP surface is read-only; the only Corp mutation (creating an
environment, F7.6) still goes through the one door. Run → job attribution is only as good as the mandate a
run carries: a run under a mandate no job references is `unassigned`, not silently attached. Cost is the
live ledger pivot (F7.1), UNAVAILABLE without a ledger. **Alerts (F7.3) and budget governance (F7.2) are
not built yet** — they are declared seams here, filled by their own slices; this slice does not fabricate
them. The read model defaults to the klijent-nula corp registry; a real deployment injects its own via a
runtime `corp_registry` attribute.

## Next

- **F7.3** — Watchtower: deterministic read-only alert derivation over trace + ledger, flipping the
  oldest F5 seam (`watchtower_alerts`) and this slice's `CLAIMS_ALERTS_LIVE`.
- Then **F7.2** budget governance, **F7.4** Evidence Vault, F7.6–F7.9, F7.10 seal.
