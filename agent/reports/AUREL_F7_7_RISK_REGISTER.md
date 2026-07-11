# AUREL F7.7 — Risk Register v1: governed entries + likelihood×impact heatmap

_2026-07-11, branch `feat/f7-corp`. A risk is governed evidence, not ephemeral state._

## What shipped

The Risk Register records risks as **governed trace records** (hash-chained praxis events, the same
append-only channel the Board journal and AurelEU events use), so the register and its heatmap are pure
projections that survive replay. Additive behind `AUREL_CORP`; a standalone module (no runtime edits).

- **`corp/risk_register.py`**:
  - `RiskEntry` (frozen: `risk_id`, `job_id`, `client_id`, `description`, `likelihood` 1–5, `impact` 1–5,
    `tier: RiskLevel`, `mitigation`, `status: RiskStatus`, `source`). Validated (id required, scale 1–5,
    typed tier/status); `score = likelihood × impact`. Round-trips through a praxis-event summary via a
    mark prefix + one JSON blob (split on the first `|` only) so **free text with pipes survives replay**.
  - `record_risk(trace, entry, *, mandate_id)` — the governed write: appends the entry as a
    `PraxisEventRecord` (event_type `risk_entry`, carrying `mandate_id`). `RiskEntry.risk_proposal()` is
    the one-door `act` payload (tool `corp_risk_add`) a UI posts to `POST /proposals`.
  - `RiskRegisterProjection.from_trace(trace)` — rebuilds the register from the trace: latest entry per
    `risk_id` wins (replay is chronological), `entries()`/`active()` deterministic, and `heatmap()` is a
    deterministic likelihood×impact cell list over the **active** entries. **Deletion is a status change**
    — closing a risk records a new `CLOSED` entry for the same `risk_id`; history stays in the trace, the
    projection keeps the latest, and a closed risk drops off the heatmap.
  - `CLAIMS_AUTO_RISK_DETECTION` is hard-wired **False** — auto-mining risks from drift-gates is a LATER
    seam; v1 is operator-entered only.

## Evidence

- Seal `tests/test_p6f7_7_risk_register.py` — **10 passed**: entry validates id + 1–5 scale; score;
  summary round-trips free text with pipes; foreign marks rejected; `record_risk` writes exactly one
  governed praxis event carrying `mandate_id`; projection rebuilds the register deterministically from the
  trace; heatmap counts cells; **deletion is a status change (risk_id kept, latest CLOSED, off the
  heatmap)**; `risk_proposal` is a one-door payload; auto-detection guard False.
- ruff + mypy clean; F7 subset regression (domain / vault / wizard / risk / corp-read-model):
  **50 passed, 0 failed**.

## Boundary (honest)

Recording a risk is a **governed trace append** (append-only, hash-chained, replayable) — consistent with
how the Board journal and AurelEU events are written; it is not routed through the executor `runtime.submit`
(a risk entry is operator metadata, not a sandboxed tool action). The `corp_risk_add` tool named by
`risk_proposal()` is **not registered** yet, so a submitted proposal fails closed until it is wired (a
forward seam) — `record_risk` is the primitive that handler would call after approval. Auto-detection from
drift-gates is not implemented (declared LATER seam).

## Next

- **F7.8** — Approval workbench refinement (pending items enriched with mandate/client/budget/risk
  context; flips the `full_approval_workbench` seam), which consumes this register per job.
- Then F7.9 KPI + React, F7.10 derived exit seal.
