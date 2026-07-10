# AUREL F6.8–F6.9 — Two-Persona Board Options + AUREL_CRO Surface

_2026-07-10, branch `feat/f6-aureleu`. AurelEU gets a home and a two-lens option generator._

## What shipped

- **F6.8 — two-persona planning → Board options** (`front_server/board.py`, `aureleu.py`, reuse flag
  `AUREL_FRONT_BOARD`): `AurelEUDispatcher.generate_options(topic, tool, args, router)` produces two
  **explicit, persona-diverse** options — a **risk-first (SHADOW)** and an **opportunity-first
  (DEPLOY)** framing over the same action (a router failure ⇒ honest UNAVAILABLE rationale). Each is
  a `BoardOption` recorded to the journal (`record_option`, projected via `options_from_trace`) and
  converts to an `act` proposal through the same one door (F5.6) — a *generator*, never an execution.
- **F6.9 — AUREL_CRO surface** (`front_server/aureleu_read_model.py`, `read_models.py`,
  `web/shell`): `AurelEUReadModel` composes the live F6 governance state — bound mandates,
  delegation windows, persona-switch history, and DN status — as a pure trace/registry projection
  (zero writes), surfaced at `GET /read/aureleu`. It declares `claims_aureleu_dispatcher_live = True`
  (the F5 seam is now live). React `AurelEUPanel` (on `aurel_cro`, beside Signal) reads it through the
  single `frontClient`; in fixture mode it renders nothing (honest — no live data).

## Evidence

- `tests/test_p6f6_8_two_persona_board.py` — **4**: two persona options (SHADOW + DEPLOY, distinct
  rationales); option → `act` proposal; options recorded + projected + live via `/read/board`;
  convert reduces through the one door to `runtime.submit` (pending → approve → executed).
- `tests/test_p6f6_9_aureleu_surface.py` — **4**: read-model composes mandates + delegations +
  persona switches + DN; live via `/read/aureleu` with `claims_aureleu_dispatcher_live = True`;
  zero-write; **one door preserved** (still exactly one mutation route).
- ruff + mypy clean; web/shell typecheck + vitest (one-door scan) + `vite build` green; browser
  preview: Aurel CRO renders with no console errors, honest fixture-mode behaviour.

## Boundary (honest)

The two-persona generator frames the *same* proposed action through two lenses (risk vs.
opportunity); richer divergent-action generation is later. The AUREL_CRO read-model returns all
delegation windows (deterministic) with their validity — "active-now" filtering is a UI concern to
keep the projection deterministic. The AurelEU panel is live-only (fixture mode shows nothing rather
than faking data).

## Next

- **F6.10** — derived F6 exit seal (each slice importable + report; **flip** the F5 UNAVAILABLE
  seams `aureleu_role_fluid_dispatcher` + `mandate` to SEALED; new UNAVAILABLE for SCI-FI
  multi-jurisdiction / kripto-ledger / full workbench), `aurel aureleu seal/status`, then merge to master.
