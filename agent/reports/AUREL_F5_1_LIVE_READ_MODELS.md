# AUREL F5.1 — Live Read Projections behind `GET /read/{model}`

_2026-07-10, branch `feat/f5-front-v1`. The read side of the one door goes live._

## What shipped

`GET /read/{model}` no longer returns a static placeholder — it returns a **pure live
projection over the trace**. Same trace ⇒ same bytes; a new governed event deterministically
changes the read; no read path writes or calls a subsystem beyond `replay()`.

- **`front_server/read_models.py`** — `LiveReadModels`, a registry mapping a model name to a
  deterministic builder `(trace, params) → dict`. Five live projections, all reusing the
  projections the one door already produces:
  - `signal/history?room=` → `RoomHistoryProjection`
  - `workops/history?task=` → `WorkOpsChatReadModel.history`
  - `workops/tasks` → `WorkOpsChatReadModel.tasks`
  - `approvals` → `ApprovalInbox.audit_from_trace`
  - `rooms?prefix=` → `rooms_from_trace`

  Unknown model → **404**; malformed params (e.g. `workops/history` with no `task`) →
  **400** (`ReadModelError`). The trace is resolved **lazily** per read (a runtime that is
  never read is never touched), so construction stays as tolerant as the dispatcher's.
- **`front_server/server.py`** — `FrontApp.handle_read` delegates to `LiveReadModels.read`;
  `FrontApp` builds one `LiveReadModels` alongside the dispatcher.

The P2.10-B static shell contract model (`build_web_shell_read_model`) is deliberately left
untouched — it is a *contract* read model (client status / surfaces / no-overclaim), a
different doctrine object from these live trace projections.

## Evidence

- Seal `tests/test_p6f5_1_live_read_models.py` — **8 passed**: read == direct replay-derived
  projection (Signal history, WorkOPS tasks); read is live (append a turn → the same
  `LiveReadModels` reflects it) and deterministic (two reads byte-identical); reads never
  grow the trace (zero writes); unknown model → 404; `workops/history` requires `task`;
  rooms/approvals projections; end-to-end over the one-door HTTP `GET`.
- F5.0a updated: the old `test_read_placeholder` became `test_read_is_live_projection`
  (empty trace ⇒ empty rooms, live; unregistered model ⇒ 404) and its fixture now uses a
  real `build_runtime()`.
- ruff clean; mypy clean. Full F5 + front_server + conversation regression green (**52 passed**).

## Boundary (honest)

The `approvals` read is the **trace audit** (the immutable record). The in-process **pending**
inbox (operational state that holds command args for Phase-B re-submit) is not a pure trace
projection and is composed separately by HQ.Command (F5.5). Server-OFF ⇒ there is no live
read at all; the web/shell dev fixture is the honest fallback (F5.8), never a faked "live".

## Next

- **F5.4 / F5.5** — Library + HQ.Command read-models composed on this registry.
- **F5.8** — React UI reading `/read/*` and posting to `/proposals` through one client.
