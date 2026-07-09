# AUREL F5.8 — React Front v1 Wiring (one door, DTO parity, fixture honesty)

_2026-07-10, branch `feat/f5-front-v1`. The UI gets exactly one path to the backend._

## What shipped

The React shell now talks to the live Front server through a **single door**, and degrades
honestly to read-only fixture mode when the server is off.

- **`web/shell/src/frontClient.ts`** — the ONLY module allowed to touch `fetch`/`WebSocket`.
  `read()` → `GET /read/{model}` (pure projections: signal/workops history, tasks, approvals,
  library, hq/command, board). `propose()` → `POST /proposals` (the single mutation route);
  `decide()` is a `decide` proposal through the same door. `openStream()` opens `/ws` (a stream,
  not a second door). `connect()` probes `/health`: unreachable ⇒ **fixture mode** with every
  proposal action disabled — never a faked submit.
- **`web/shell/src/front-types.ts`** — DTOs mirroring the Python `to_dict()` shapes
  (ProposalEnvelope converse/act/decide, conversation reply, room history, WorkOPS tasks,
  approvals, library, hq/command, board).
- **`web/shell/src/components/front/FrontSurface.tsx`** — per-surface live panels: Signal chat
  (`aurel_cro`), WorkOPS chat + task list (`ide`), HQ.Command runs + approval inbox + Board
  journal (`hq`), Library explorer (`hub`). Signal and WorkOPS share one `ChatPanel` — same
  conversation engine, different room.
- **`web/shell/src/App.tsx`** — connects the client on mount and shows an honest Front-mode
  banner (LIVE vs read-only fixture).

## Evidence

- Python seal `tests/test_p6f5_8_ui_one_door.py` — **4 passed**: exactly one mutation route
  (`POST /proposals`); a UI "send message" reduces to a converse proposal end-to-end; reads never
  mutate (two reads identical); a POST to a read path → 404 (never a mutation via read verb).
- vitest `src/front-one-door.test.ts` — **3 passed**: no source file except `frontClient.ts`
  calls `fetch`/`new WebSocket`; every mutation is a ProposalEnvelope kind; the client's only POST
  target is `/proposals`. Full web/shell suite **14 passed**; `tsc` typecheck clean; `vite build`
  clean.
- Browser preview (no Front server running): banner reads "read-only fixture mode — proposals
  disabled"; the Signal composer input + Send button are **disabled** with placeholder
  "read-only fixture mode" — verified honest offline behavior, no fake LIVE.

## Boundary (honest)

`main.tsx` still bootstraps from the static `web-shell-read-model.json` fixture (the P2.10-B
contract shell) and is exempt from the one-door scan for that bootstrap read; all *runtime*
backend access goes through `frontClient`. `wss`/TLS + remote transport remains UNAVAILABLE
(v1 is localhost, no TLS). DTO parity is asserted by shape here; a generated `contract_manifest`
diff can tighten it later.

## Next

- **F5.9** — derived Front v1 exit seal (every slice importable + report present; UNAVAILABLE
  registry; overclaim guards False) + `aurel front seal/serve/demo`, then merge to master.
