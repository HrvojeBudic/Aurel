# AUREL F4.3 — Interactive ReAct Loop over the ContextLoom

_2026-07-09, branch `feat/f4-cognition-contextloom`. Fourth F4 slice (after F4.0–4.2 ContextLoom)._

## What shipped

New `src/agentic_runtime/entity_loom_loop.py` — an additive observe→think→act loop
that drives actions through the real `runtime.submit` kernel while assembling its
context each turn through the ContextLoom (F4.0–4.2). **`entity.py` is untouched**:
the existing single-shot `AgenticEntity` planner path is byte-identical.

- **`EntityLoomLoop`** — each turn: **observe** (operator intent + memory recall +
  prior tool observations → a governed `ContextBundle`, budget-fit with compression,
  `context_ref` bound to the trace via F4.2); **think** (hand the bundle to an
  injectable `Planner` → steps or `done`); **act** (submit each step through the
  governed kernel; fold each observation back as an INTERNAL trusted context item).
  Termination is always bounded: `done` / `no_steps` / `no_progress` / `budget_exceeded`
  / `max_turns`.
- **`Planner` protocol + `PlanTurn`** — an injectable `(bundle, card) -> PlanTurn`, so
  the loop is deterministic under a stub/cassette.
- **`RouterPlanner`** — the production adapter: assemble → router (cassette by default)
  → `PlanValidator`, exactly as `AgenticEntity.plan` does but fed the ContextLoom prompt
  (external items already fenced as data); charges the budget when one is supplied.
- Flag `AUREL_ENTITY_LOOP` (defined-not-gating; opt-in by construction).

## Evidence

- Seal `tests/test_p6f4_3_entity_loop.py` — **7 passed**: each turn assembles + binds a
  `context_ref` and the loop's refs match a pure trace replay; a successful step's
  observation folds into the next turn's context as an INTERNAL item; operator intent
  leads and is instruction-eligible; bounded termination (done / no_progress on a
  contract-blocked step / max_turns with exact executed count); `RouterPlanner` validates
  a stub router's plan into steps and returns `done` on invalid output; flag default OFF.
- ruff clean; mypy clean (1 source file); compileall OK.
- **Purely additive** — no existing file modified (`entity.py` byte-identical).

## Next

**F4.4 — projection + CLI + F4 exit seal.** Read-only projection of a loop run (turns,
`context_refs`, terminated reason) + `aurel f4 seal` derived exit seal over F4.0–4.4 with
explicit UNAVAILABLE surfaces (live-model loop, direction-B MCP client bridge). Seal
`test_p6f4_4_f4_exit_seal.py`.
