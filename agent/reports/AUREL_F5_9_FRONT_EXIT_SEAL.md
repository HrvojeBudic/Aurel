# AUREL F5.9 — Front v1 Derived Exit Seal + Projection + CLI

_2026-07-10, branch `feat/f5-front-v1`. F5 is sealed — derived, never declared._

## What shipped

The Front v1 phase closes with a **derived** exit seal, a north-star run projection, and CLI.

- **`front_seal.py`** — `build_f5_exit_seal()` derives `SEALED` **only** when every slice
  (F5.0a, F5.0b, F5.C, F5.1–F5.8, F5.9) has both an importable module and a present report; any
  missing module or report `BLOCK`s that item and the whole seal. The UNAVAILABLE registry lists
  each deferred surface with a reason + owner: `wss_tls_remote_transport` (Tauri-Rust),
  `aureleu_role_fluid_dispatcher` (F6), `watchtower_alerts` (F7), `workops_ai_editor` (after F7),
  `library_time_travel` (F8). Six overclaim guards are hard-wired `False`.
- **`front_projection.py`** — `FrontRunProjection` composes Signal history + WorkOPS tasks +
  run status + approval audit + Library into one read-only view: the north-star chain (Signal
  intent → proposal → approval → execution → Library artifact) is provably replayable from the
  trace, zero direct UI calls.
- **CLI** — `aurel front seal [--json]` (derived seal, exit 1 if BLOCKED), `aurel front demo`
  (north-star projection), alongside the existing `aurel front serve`.

## Evidence

- Seal `tests/test_p6f5_9_front_exit_seal.py` — the derived seal is `SEALED` with all 12 slices
  PASSED; a missing report BLOCKs deterministically; all six overclaim guards `False`; the
  UNAVAILABLE registry is non-empty with owners; the north-star projection composes and is
  replayable; every read is a pure trace projection (zero direct UI calls proven by the single
  mutation route).
- Full F5 Python regression green; `web/shell` vitest + typecheck + build green.

## The F5 phase (what is now closed)

The operator talks to the LLM through **Signal and WorkOPS** on one governed conversation
engine; messages reduce to `converse`/`act`/`decide` proposals through **one door**
(`POST /proposals`); approvals persist as a two-phase inbox; reads are **live trace
projections** (signal/workops history, tasks, approvals, Library, HQ.Command, Board); the React
shell wires them through a single `frontClient` and degrades honestly to read-only fixture mode.

## Boundary (honest)

SEALED means the governed conversational + one-door + live-projection backbone is closed — NOT
that a live model runs by default (opt-in), nor that role-fluid AurelEU (F6), Watchtower (F7),
WorkOPS Code / AI-editor (after F7), Library time-travel (F8), or wss/TLS remote transport
exist. Those remain explicit UNAVAILABLE seams carried forward.

## Next

- Merge `feat/f5-front-v1` → master.
- **F6** — AurelEU dispatcher + Constitution + mandates (unlocks the deferred AurelEU/mandate seams).
