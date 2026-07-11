# AUREL F7.3 — Watchtower: read-only alert derivation + HQ.Command / CORP flip

_2026-07-11, branch `feat/f7-corp`. The first module that actively brings governance signals to the operator._

## What shipped

Watchtower is the Business Plane's **read-only monitor**: it derives governance alerts from facts already
in the trace + the live ledger and surfaces them — **visibility, never authority** (never blocks, never
executes, never changes a verdict). It flips the oldest F5 seam (`watchtower_alerts`) and the F7.5
`CLAIMS_ALERTS_LIVE` seam. Additive behind `AUREL_WATCHTOWER`; flag OFF ⇒ both surfaces keep their
byte-identical UNAVAILABLE stubs.

- **`corp/watchtower.py`** — `WatchtowerAlert` (frozen: `kind`, `severity`, `message`, `source_ref`,
  `mandate_id`, `client_id`) is **un-constructible without a `source_ref`** — an alert that cannot cite
  the trace entry / ledger metric it came from does not exist. `alert_id` is deterministic from
  `(kind, source_ref)`. `derive_alerts(trace, ledger=None, corp_registry=None, *, inbox=None)` runs five
  deterministic rules over one replay pass + one ledger snapshot:
  1. **BUDGET_DENY** (CRITICAL) — `budget_decision` with `verdict == "deny"`;
  2. **BUDGET_THRESHOLD** (WARN/CRITICAL) — a ledger metric at `> 80%` of its cap (from `snapshot()`);
  3. **MANDATE_BLOCK** (CRITICAL/WARN) — `runtime_status_transition` reaching a blocked/rejected/failed/
     needs-human state;
  4. **CONSTITUTION_VIOLATION** (CRITICAL) — `praxis_event` with `event_type == "constitution_violation"`;
  5. **APPROVAL_PENDING** (WARN) — items from an injected inbox's `pending()` (operational, optional).
  Client is resolved `mandate_id → job → client` via the Corp registry (F7.0). Alerts dedup by
  `source_ref` and sort by `(severity, alert_id)`. Fail-open on absence: no ledger ⇒ threshold rule
  skipped (never invented); no inbox ⇒ no pending alerts (operational, not a trace projection).
- **`front_server/hq_command.py`** — `watchtower()` is now flag-aware: OFF ⇒ the exact existing
  UNAVAILABLE stub (byte-identical); ON ⇒ `live_feed(derive_alerts(...))`. `claims_watchtower_live` is
  **derived** from the flag (True only when on). The module constant `CLAIMS_WATCHTOWER_LIVE` stays the
  documented default (False).
- **`front_server/corp_read_model.py`** — the F7.5 alerts seam flips the same way: OFF ⇒ UNAVAILABLE
  seam; ON ⇒ live feed; `claims_alerts_live` derived.

## Evidence

- Seal `tests/test_p6f7_3_watchtower.py` — **15 passed**: alert requires `source_ref`; `alert_id`
  deterministic; budget deny → CRITICAL alert with client resolved via the registry; blocked run →
  MANDATE_BLOCK; needs-human → WARN; non-blocked transition → no alert; constitution violation → alert;
  ledger threshold from snapshot; no ledger ⇒ threshold skipped; pending approval from inbox; dedup +
  severity ordering; **HQ.Command flag-off byte-identical + flag-on LIVE**; **CORP alerts flag-off
  UNAVAILABLE + flag-on LIVE via `/read/corp/portfolio`**.
- ruff clean; mypy clean (8 files). Front-server + F7 regression (hq-command / live-read-models /
  front-exit-seal / f6-exit-seal / aureleu-surface / budget + F7.0/1/3/5): **90 passed, 0 failed** (~1:06).

## Boundary (honest)

Watchtower is **read-only** — it derives and escalates, never blocks/executes/changes a verdict; a
fabricated alert (no `source_ref`) is un-constructible. Detection is only as good as what reaches
`replay()`: `budget_decision` and `praxis_event` carry `mandate_id` (F6.1) so their alerts attribute to a
client; **run-status transitions do not yet carry `mandate_id`** (the state machine does not populate it),
so a MANDATE_BLOCK alert attributes to a client only once that field is emitted — the rule is ready, the
emitter is the forward seam. A mandate *scope* denial today records a `StateTransitionRecord`, which
`replay()` does not yield — so scope blocks surface via the run-status transition the run loop drives to a
blocked state, not via the command-level record. Predictive burn/ETA remains a separate later seam.

## Next

- **F7.2** — budget governance (allocation vs. spend per client/job; forecasting stays UNAVAILABLE).
- Then **F7.4** Evidence Vault, F7.6 wizard, F7.7 Risk Register, F7.8 workbench, F7.9 KPI + React,
  F7.10 derived exit seal (flips `watchtower_alerts` + `full_approval_workbench`).
