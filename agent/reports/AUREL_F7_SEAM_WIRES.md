# AUREL F7 seam wires — make klijent nula executable, not just projectable

_2026-07-11, branch `feat/f7-seam-wires`. Two quick forward-seam closures the F7 slices left._

## What shipped

F7 delivered the Business Plane as a projection layer; two small wires make parts of it actually
executable / live, closing forward seams the F7 reports flagged. Both additive.

- **Skill library → Reflex Flywheel KPI (F7.9).** The shared `SkillLibrary` now rides the inner runtime
  (`Kernel.__init__`: `runtime.skills = skills`), so the KPI read model reaches it without threading the
  Kernel through `LiveReadModels`. `/read/corp/kpi` now goes **live** once the library has usage (a fresh
  runtime is still honestly UNAVAILABLE — never a fake 0%).
- **`corp_risk_add` through the one door (F7.7).** The proposal dispatcher intercepts an `act` proposal
  whose `tool == "corp_risk_add"` and routes it to the governed Risk Register write (`record_risk` — a
  hash-chained praxis append, like the Board journal), never through the sandbox executor. So the Risk
  Register the wizard/UI proposes is now operator-writable end-to-end; invalid args fail closed, and the
  entry carries the proposal's `mandate_id`.

## Evidence

- Seal `tests/test_p6f7_seam_wires.py` — **7 passed**: the runtime exposes the shared skill library; the
  KPI goes live with skill usage (rate 1.0) and stays UNAVAILABLE without; a `risk_proposal()` routes to
  a governed record that appears in `RiskRegisterProjection`; the record carries `mandate_id`; invalid
  risk args fail closed; a normal tool `act` with no inbox stays the honest unwired path (F5.2).
- Regression fix: moving the corp interception into `_dispatch_act` initially reordered the
  "requires a tool" check ahead of the no-inbox path, breaking `test_proposals_routes_to_dispatcher`
  (`{"kind":"act"}` with no tool must still return the unwired 200). Restored the original order — the
  interception fires only when `tool == "corp_risk_add"`. F5.0a + seam wires **15 passed**; the
  dispatcher/build_runtime regression battery is otherwise green.
- ruff + mypy clean.

## Boundary (honest)

The corp record path is a **front-server governed append** (like the Board journal), not a
`runtime.submit` sandbox tool — a risk entry is operator metadata. The **third forward seam,
`corp_create_environment`, is not wired here**: making a created client/job/mandate persist and appear in
the portfolio needs a **trace-projected `CorpRegistry`** (the current registry is static config), which
is a proper small slice, not a quick wire. It remains a declared forward seam.

## Next

- Optionally: `corp_create_environment` as a trace-projected corp registry (a small slice) to make
  environment creation fully end-to-end.
- Then **F8 — Time Plane (Chronos + System ekran)**.
