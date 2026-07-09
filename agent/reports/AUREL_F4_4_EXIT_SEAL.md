# AUREL F4.4 — Projection + CLI + F4 Exit Seal

_2026-07-09, branch `feat/f4-cognition-contextloom`. Final F4 slice — closes the cognition / ContextLoom phase._

## What shipped

- **`f4_seal.py`** — the **derived** F4 exit seal (never a self-assigned boolean).
  `build_f4_exit_seal` checks every slice (F4.0→F4.4) for an importable module AND a
  present report; a missing one BLOCKS the item and the seal. Deferred surfaces stay
  explicit in an `UnavailableSurface` registry — `live_model_loop`,
  `context_loom_wired_into_default_plan`, `semantic_summarization`, `mcp_client_bridge`
  — each with a reason and future owner. Overclaim guards
  `claims_live_model_loop` / `claims_semantic_summarization` / `claims_client_bridge_live`
  are computed and hard-wired False.
- **`f4_projection.py`** — read-only read-models: `project_loop_run` (turns, context_refs,
  termination) and `project_context_bundle` (provenance mix by source kind, external
  count, budget outcome, rendered length).
- **`cli_modules/f4_commands.py` + `cli.py`** — `aurel f4 seal [--json]` (exit 2 when not
  SEALED, CI-gateable) and `aurel f4 loom [--max-tokens]` (projects a demo ContextLoom
  assembly — operator + memory + scraped item — showing provenance, budget drop/compress,
  and the external-fenced render).

## Evidence

- Seal `tests/test_p6f4_4_f4_exit_seal.py` — derived SEALED when all present / BLOCKED on a
  missing report or module (hermetic tmp-dir); overclaim guards False; UNAVAILABLE registry
  explicit with owners; loop-run + bundle projections; real-repo SEALED.
- ruff clean; mypy clean; compileall OK. Only existing file touched: `cli.py` (additive
  subparser + import).

## F4 phase — closed

Aurel now assembles context as a governed mechanism and reasons over it in a bounded loop:

- **F4.0** ContextLoom foundation — provenance-labelled, taint-aware (external data-only),
  deterministic, content-addressed (`context_ref`).
- **F4.1** budget-aware compression — extractive truncation to fit, no silent loss.
- **F4.2** trace binding — `context_ref` into the hash-chained trace, replay-safe + leak-safe.
- **F4.3** interactive ReAct loop — observe→think→act through `runtime.submit`, context via
  the Loom each turn, cassette-by-default via an injectable planner.
- **F4.4** derived exit seal + read-only projections + CLI.

**Explicitly deferred (UNAVAILABLE, not overclaimed):** live-model loop driving; wiring the
ContextLoom into the default `AgenticEntity.plan` path; semantic (vs extractive)
summarization; direction-B MCP client bridge (Aurel calling OUT — the ContextLoom is now its
governed sink, but the bridge itself is unbuilt).

## Next

**F5 — Aurel Front v1 (Signal + WorkOPS + HQ core)**, per `AUREL_PLAN_02` — the ContextLoom
`context_ref`s are exactly Signal's per-message `context_refs`. Or build the deferred
direction-B MCP client bridge onto the ContextLoom sink first. Operator decides.
