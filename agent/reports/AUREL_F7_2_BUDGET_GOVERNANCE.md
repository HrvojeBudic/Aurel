# AUREL F7.2 — Budget governance: allocation vs. spend per client / job / mandate

_2026-07-11, branch `feat/f7-corp`. Fills the F7.5 `budget_governance` seam — a report, never enforcement._

## What shipped

Budget governance composes what is already true into an allocation-vs-spend answer. It is a **report,
never enforcement** — the real cap still lives in the budget gate + the F6.2 mandate gate (which already
enforces `MandateScope.budget_cents`). Additive behind `AUREL_CORP`; flips the F7.5 `budget_governance`
UNAVAILABLE seam (owner F7.2) to a live projection.

- **`corp/budget_governance.py`** — `ClientBudgetView.build(ledger, corp_registry, trace=None, *,
  mandate_registry=None)`:
  - **allocation** = `MandateScope.budget_cents` of the mandates a job references, resolved through the
    mandate registry the Corp registry holds (F7.0);
  - **spent** = the F7.1 `CostAttributionView` per-mandate estimated cost;
  - **remaining** = allocation − spent (only when the allocation is bounded and spend is known);
  - **deny_count** = the trace's `budget_decision` denials per mandate (F6.1's `mandate_id`).
  Rolls mandate → job → client with an honest worst-case status: a mandate with **no cap**
  (`budget_cents == 0`, e.g. klijent nula's default mandate) is **UNBOUNDED** (never a fabricated number);
  an **unresolvable** mandate is **UNAVAILABLE** with a reason; the job/client status is the worst of its
  parts (UNAVAILABLE > UNBOUNDED > AVAILABLE). Spend is `None` (unknown, not zero) when no ledger is
  bound. **Burn-rate / ETA forecasting stays a declared UNAVAILABLE seam** inside the view — this view
  never predicts.
- **`front_server/corp_read_model.py`** — the portfolio's `budget_governance` seam now returns the live
  `ClientBudgetView`; `CLAIMS_BUDGET_GOVERNANCE_LIVE` is `True` (built). `hq_command.predictive()` is
  **untouched** (predictive burn/ETA remains its own later seam).

## Evidence

- Seal `tests/test_p6f7_2_budget_governance.py` — **8 passed**: allocation from a bounded mandate;
  remaining = allocation − spent; rollup to job + client; no-cap mandate is UNBOUNDED (spend still shown,
  never a fake zero); unresolvable mandate is UNAVAILABLE; no corp registry ⇒ view UNAVAILABLE; deny_count
  from trace (per mandate + job rollup); forecasting stays an UNAVAILABLE seam; spend `None` without a
  ledger.
- Updated `tests/test_p6f7_5_corp_read_model.py` — the CORP portfolio's `budget_governance` is now live
  (`available`, forecasting UNAVAILABLE, `claims_budget_governance_live` True); alerts stay a seam (F7.3
  flag off). ruff + mypy clean (8 files). Front + F7 regression (hq-command / live-read-models /
  front-exit-seal / f6-exit-seal / budget + F7.0/1/2/3/5): **94 passed, 0 failed** (~1:18).

## Boundary (honest)

Governance is **read-only reporting** — no cap check, no verdict, cannot block. Allocation is only as
meaningful as the mandate's `budget_cents`; klijent nula's default mandate is uncapped, so its allocation
is honestly UNBOUNDED (the enforceable cap for private use comes from a per-job bounded mandate).
Forecasting/burn-ETA is not implemented (a declared seam in the view); `hq_command.predictive()` is
likewise still its own UNAVAILABLE seam.

## Next

- **F7.4** — Evidence Vault: trace search by mandate/client + receipt bundle export (Output Passport).
- Then F7.6 wizard, F7.7 Risk Register, F7.8 workbench, F7.9 KPI + React, F7.10 derived exit seal.
