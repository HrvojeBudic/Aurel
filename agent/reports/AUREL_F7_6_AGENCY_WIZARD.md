# AUREL F7.6 — Agency wizard: environment templates + what-if impact report

_2026-07-11, branch `feat/f7-corp`. Draft a governed environment; preview it through the real gate before creating anything._

## What shipped

The Agency wizard drafts a **governed environment** (a client + job + mandate) and shows, *before creating
anything*, what that mandate would allow or deny — by running the preview through the **same F6.2 gate**
that enforces at runtime. Additive behind `AUREL_CORP`; a pure module (no runtime edits, no dispatcher
change).

- **`corp/wizard.py`**:
  - `EnvironmentTemplate` (frozen: `client_name`, `job_title`, `scope: MandateScope`, `persona_ref`,
    `memory_zone_rules`, `repos`) — **un-constructible without a scope** (inherits the Mandate
    no-overclaim law). `to_mandate()` builds the draft mandate (stable id) for the preview.
  - `what_if(template, sample_actions) → ImpactReport` — dry-runs each `SampleAction` through the **real**
    `evaluate_mandate_scope_check` (the very code `runtime.submit` calls at F6.2), so the preview cannot
    drift from reality. `SampleAction` exposes exactly what the gate reads (`tool`, `declared_risk`,
    `args`). The `ImpactReport` is **evidence, not authority** — `is_advisory` hard-wired True,
    `grants_authority` hard-wired False; a what-if verdict never approves an action.
  - `to_proposal()` → the one-door payload (`kind: "act"`, tool `corp_create_environment`) a UI posts to
    `POST /proposals`. It **creates nothing by itself** — creation is an approval away, a governed record.
    Calling it twice yields an identical payload (pure, no side effects).

## Evidence

- Seal `tests/test_p6f7_6_agency_wizard.py` — **7 passed**: template requires a scope + names
  (no-overclaim); what-if predicts DENY/allow correctly (in-scope path allowed; out-of-paths, tool not in
  allow-list, and risk-over-ceiling all blocked); **what-if matches the real gate on an equivalent
  `CommandEnvelope`**; the ImpactReport is advisory and grants no authority; `to_proposal` is a one-door
  `act` payload, not direct creation, and is pure/repeatable.
- ruff + mypy clean; full F7 suite (F7.0–F7.6): **74 passed, 0 failed**.

## Boundary (honest)

The wizard **creates nothing** — `what_if` is a side-effect-free evaluation (evidence, never authority),
and `to_proposal` only builds the payload; the actual `corp_create_environment` tool is **not registered**
yet, so a submitted proposal fails closed at the tool registry (no execution) until that creation tool is
wired — a forward seam. The proposal dispatcher is structurally unchanged; the wizard is a payload
generator only.

## Next

- **F7.7** — Risk Register v1 (governed entries through the one door + likelihood×impact heatmap;
  auto-detection stays a LATER seam).
- Then F7.8 workbench, F7.9 KPI + React, F7.10 derived exit seal.
