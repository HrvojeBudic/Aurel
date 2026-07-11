# AUREL F7.8 — Approval workbench refinement: context to decide

_2026-07-11, branch `feat/f7-corp`. Flips the `full_approval_workbench` seam — read-only composition, no new decision path._

## What shipped

The F5.2 inbox gives the operator a *pending list*; the workbench gives them the *context to decide*. Each
pending item is enriched with the facts the earlier F7 slices already produce. Additive behind
`AUREL_CORP`; flips the F6-declared `full_approval_workbench` seam.

- **`front_server/workbench.py`** — `ApprovalWorkbenchReadModel` enriches each pending item with:
  - **mandate summary** — scope paths/tools/max_risk/budget (from the mandate registry the Corp registry
    holds);
  - **attribution** — client/job (F7.0, via mandate → job → client);
  - **budget** — the mandate's allocation/spent/remaining/deny-count (F7.1/F7.2);
  - **risks** — the job's active risk entries (F7.7);
  - **history** — the tool's decision history from the trace audit (`ApprovalInbox.audit_from_trace`).
  Items sort deterministically by `(risk, request_id)` (riskier first). Any context with **no source is
  `UNAVAILABLE` with a reason** (unknown mandate, no ledger, mandate maps to no job) — never fabricated.
  `tool_history()` (decision counts per tool from the audit) is available even without an inbox.
- **`front_server/approval_inbox.py`** — `PendingApproval` gains an additive `mandate_id` (default `""`,
  set from the card at `submit_act`) so a pending item carries the authority it was submitted under. The
  two-phase `decide` flow is **unchanged**.
- **`read_models.py`** — registers `corp/workbench` (no inbox via the pure read registry ⇒ pending
  honestly unavailable, tool history still live — the F5.5 `pending_source` discipline).

## Evidence

- Seal `tests/test_p6f7_8_approval_workbench.py` — **7 passed**: a pending item carries full context
  (mandate/attribution/budget spent=100¢ remaining=900¢/risks/history); context without a source is
  UNAVAILABLE (unknown mandate → no job → empty risks); items sorted by risk then request_id; **no inbox ⇒
  pending unavailable but tool history live**; the workbench exposes **no decide/submit/approve path**
  (read-only); the `full_approval_workbench` claim is True; `PendingApproval` carries `mandate_id`.
- ruff + mypy clean; front (F5.2/F5.5) + F6-exit-seal + F7 regression: **59 passed, 0 failed**.

## Boundary (honest)

This is a **read-only composition** — it adds no decision path. The decision still goes only through the
F5.2 two-phase `decide`; the inbox change is purely additive (`mandate_id` on the pending item). Via the
pure read registry there is no inbox, so `/read/corp/workbench` shows pending `unavailable` (operational
state, F5.5 discipline) with the trace-derived tool history live; the enriched pending items appear when
the model is constructed with an injected inbox (as the front server does). Context sections degrade to
UNAVAILABLE with a reason rather than inventing values.

## Next

- **F7.9** — Reflex Flywheel KPIs (reflex hit rate + cost-per-task, UNAVAILABLE without data) + the CORP
  React panel.
- Then **F7.10** — klijent-nula E2E + derived exit seal (flips `watchtower_alerts` +
  `full_approval_workbench`) + merge.
