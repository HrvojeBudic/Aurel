# AUREL F5.6 — Board Decision Journal

_2026-07-10, branch `feat/f5-front-v1`. A record, not an executor — action only through the one door._

## What shipped

`GET /read/board` returns the Board decision journal — a **pure trace projection**. A decision
is a governed record; it reaches action ONLY by "Convert to Proposal".

- **`front_server/board.py`** — `BoardDecision` (governed record; `title`/`proposed_tool`/
  `decided_by` mandatory) whose `to_proposal()` reduces to an `act` for the one door.
  `BoardJournal.record()` appends a governed decision event to the trace (records, never
  executes); `BoardJournal.from_trace()` reconstructs the journal purely from the trace (no own
  store); `BoardJournal.convert_to_proposal(decision)` yields the `act` proposal that the F5.0
  dispatcher routes through approval → `runtime.submit`.
- **`front_server/read_models.py`** — `/read/board` registered.

## Evidence

- Seal `tests/test_p6f5_6_board_journal.py` — **7 passed**: decision requires its fields;
  `convert_to_proposal` is an `act` (tool/args/risk); record projects to the journal from the
  trace; **recording executes nothing** (bridged echo tool never called); Convert → dispatcher
  `act` → **pending** → approve → `runtime.submit` **executes** (ran only after approval, via a
  real governed MCP-bridged tool); live via `/read/board`; flag `AUREL_FRONT_BOARD` defaults OFF.
- ruff clean; mypy clean. Full F5 + front_server + conversation regression green (**74 passed**).

## Boundary (honest)

The Board is a **projection + proposal**, with no other path: recording is a governed journal
append (async — it feeds the weekly review); the only route to action is Convert → the same one
door (F5.0), never a direct subsystem call. **Real-time multi-party debate is LATER.** A
decision's `proposed_args` ride the live object (mirroring F5.2 pending): the trace journal lists
decisions for review; conversion uses the live decision's args.

## Next (remaining F5)

- **F5.8** — React Front v1 wiring (`frontClient` → `/read/*` + `/proposals`; SignalPanel,
  WorkOpsChatPanel, ApprovalInbox, LibraryExplorer, BoardJournal, HQ.Command).
- **F5.9** — derived exit seal + merge `feat/f5-front-v1` → master.
