# AUREL F5.5 — HQ.Command Read-Model

_2026-07-10, branch `feat/f5-front-v1`. The operator's command surface, composed from live views._

## What shipped

`GET /read/hq/command` returns a **pure composition of live views** — no new store, zero writes.

- **`front_server/hq_command.py`** — `HQCommandReadModel` composes:
  - **run status** — the latest `runtime_status_transition` per run, from the trace
    (deterministic, sorted by run_id, with a per-run transition count).
  - **approvals** — the immutable approval audit (`ApprovalInbox.audit_from_trace`, F5.2), plus
    the in-process pending list *only* when an inbox instance is injected (`pending_source` says
    which — honest about pending being operational state, not a trace projection).
  - **budget burn** — `BudgetLedger.snapshot()` from the live runtime (usage + policy limits),
    or `UNAVAILABLE` when no ledger is bound.
  - **Watchtower** — a declared `UNAVAILABLE` seam (owner F7, empty `alerts`), and
    **predictive** burn/ETA likewise — never a fabricated alert.
- **`front_server/read_models.py`** — builders now receive the `LiveReadModels` context
  (`.trace` for pure projections, `.runtime` for live operational views like the budget
  ledger); `/read/hq/command` registered.

## Evidence

- Seal `tests/test_p6f5_5_hq_command.py` — **8 passed**: run status = latest per run
  (deterministic order); budget burn live/AVAILABLE (and UNAVAILABLE without a ledger); approval
  audit from trace + pending seam (empty/`unavailable` with no inbox, populated when injected);
  Watchtower + predictive UNAVAILABLE seams, `claims_watchtower_live` False; zero-write; live via
  `/read/hq/command`.
- ruff clean; mypy clean. Full F5 + front_server + conversation regression green (**67 passed**).

## Boundary (honest)

**Pending** approvals are in-process operational state (they hold command args for Phase-B
re-submit) — surfaced only when an inbox instance is injected, otherwise `pending_source:
"unavailable"`; the durable truth is the trace **audit**. The **Watchtower** alert feed is F7
(`CLAIMS_WATCHTOWER_LIVE` hard-wired False); **predictive** burn/ETA is a later seam. Budget burn
is the live ledger snapshot, not a trace projection (it is operational live truth).

## Next (remaining F5)

- **F5.6** — Board decision journal (optional).
- **F5.8** — React Front v1 wiring (SignalPanel + WorkOpsChatPanel + ApprovalInbox +
  LibraryExplorer + HQ.Command, all on `frontClient` → `/read/*` + `/proposals`).
- **F5.9** — derived exit seal + merge.
