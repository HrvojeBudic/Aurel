# AUREL F7.9 — Reflex Flywheel KPIs + CORP React surface

_2026-07-11, branch `feat/f7-corp`. The last F7 feature slice before the exit seal._

## What shipped

Two operator KPIs plus the CORP React surface that finally renders the Business Plane. Additive behind
`AUREL_CORP`; both KPIs are **honest about absence** (empty ⇒ UNAVAILABLE with a reason, never a lying 0%).

- **`corp/kpi.py`** — `ReflexFlywheelView.build(skills, ledger)`:
  - **reflex hit rate** — uses-weighted from the skill library (reflex-skill successes / all skill
    successes), with `by_state` breakdown; UNAVAILABLE without a library or usage.
  - **cost per task over time** — the per-run cost the budget ledger already tracks (F7.1), one entry per
    run (sorted, deterministic) plus total/avg; UNAVAILABLE without a ledger or runs.
  Registered `corp/kpi` on the read registry (the runtime binds no skill library, so `/read/corp/kpi`
  reports reflex UNAVAILABLE honestly, cost from the live ledger).
- **React (`web/shell`)** — `front-types.ts` gains `CorpPortfolioDTO`/`CorpKpiDTO`; `frontClient.ts`
  gains `corpPortfolio()` + `corpKpi()` read builders; `FrontSurface.tsx` gains a `CorpPanel`
  (portfolio tree client → job → runs, cost/budget/alerts seams, reflex + cost-per-task KPIs with
  visible UNAVAILABLE labels) wired for `case "corp"`. Every read goes through `frontClient` (the one
  door); fixture mode shows "no live data".

## Evidence

- Python seal `tests/test_p6f7_9_corp_kpi.py` — **7 passed**: reflex hit rate uses-weighted (rate 0.5
  from 5/10 uses) + `by_state`; UNAVAILABLE without usage / without a library; a real `SkillLibrary`
  reflex is AVAILABLE; cost per task from the ledger (2 runs, total 80¢, avg 40¢, deterministic order);
  UNAVAILABLE without a ledger/runs; `/read/corp/kpi` live with reflex honestly UNAVAILABLE.
- Vitest `web/shell/src/corp-surface.test.ts` — **3 passed** (of 17 total): frontClient exposes
  `corpPortfolio`/`corpKpi` on `corp/portfolio`+`corp/kpi`; `CorpPanel` reads only through frontClient
  (no direct fetch/WebSocket — the existing one-door test also stays green); wired for `case "corp"` with
  UNAVAILABLE rendered honestly. `tsc --noEmit` clean.
- ruff + mypy clean; Python front + F7 regression (kpi / live-read-models / hq-command / front-exit-seal /
  corp-read-model / workbench / f6-exit-seal): **51 passed, 0 failed**.

## Boundary (honest)

The runtime does not bind a skill library, so `/read/corp/kpi` reflex is UNAVAILABLE via the registry —
honest, not a fake rate; a richer wiring (entity's skill library) would make it live. The reflex hit rate
is a **skill-library-derived proxy** (uses-weighted), not a per-planning counter (reflex hits are memory
records, not distinct replay events). The CORP panel renders live data only in `live` mode; fixture mode
is the honest read-only fallback (F5.8). KPIs never fabricate — an empty system says UNAVAILABLE.

## Next

- **F7.10** — klijent-nula end-to-end + **derived exit seal** (flips `watchtower_alerts` +
  `full_approval_workbench`; parks the LATER/SCI-FI seams) + `aurel corp seal/status` + merge
  `feat/f7-corp` → master.
