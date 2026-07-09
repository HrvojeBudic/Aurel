# AUREL F5.7 — WorkOPS Chat on the Conversation Engine (Milestone 2)

_2026-07-10, branch `feat/f5-front-v1`. Talk to the LLM through WorkOPS — same engine, task-scoped room._

## What shipped

Milestone 2 of F5: the operator now talks to the LLM through the **WorkOPS** surface using the
**same** governed `ConversationEngine` as Signal (F5.3) — a different, task-scoped room, the
same one door. No new executor, no new store.

- **`front_server/workops.py`** — `WorkOpsMessage` (frozen, **un-constructible without
  provenance**: task_id / operator_identity / role / mandate_id required) reduces to the same
  `converse` `ProposalEnvelope` as Signal, with `room_id = workops:<task_id>`. `WorkOpsChatReadModel`
  gives task tracking as a **pure trace projection** — `task_ids` / `history` / `tasks`
  reconstructed from the conversation events, deterministic (same trace ⇒ same view). The
  WorkOPS **Code** surface (file browser / terminal / AI-editor) is a LATER slice: its
  capability claims (`CLAIMS_WORKOPS_CODE_LIVE`, `_TERMINAL_LIVE`, `_AI_EDITOR`) are hard-wired
  `False` — an honest UNAVAILABLE seam, never over-claimed.
- **`front_server/conversation.py`** — new `rooms_from_trace(trace, prefix)` helper: distinct
  conversation rooms from the trace, sorted, prefix-filterable. The foundation for enumerating
  tasks/surfaces without an own store (also the N6 Signal↔WorkOPS handoff seam).
- **`front_server/__init__.py`** — exports the WorkOPS contract + read model + claims constants.

Reused as-is: `ConversationEngine`, `RoomHistoryProjection`, the `proposal_dispatcher`
`converse` reduction, the WebSocket one-door transport. WorkOPS added **zero** new backend paths.

## Evidence

- Seal `tests/test_p6f5_7_workops_chat.py` — **11 passed**: message un-constructible without
  provenance; room is task-scoped (`workops:<task_id>`); reduces to a `converse` proposal;
  dispatcher → LLM answer wired + history from trace; task list + per-task history isolated and
  deterministic; Signal and WorkOPS share one engine but keep separate rooms (N6 foundation);
  end-to-end over the `/ws` one door; Code-surface claims hard-wired `False`; flag defaults OFF.
- ruff clean; mypy clean (2 files). F5.0a/0b/C/2/3 + front_server regression green (**44 passed**).

## Boundary (honest)

This is the **chat** slice of F5.7. The WorkOPS **Code** surface — read-only file browser,
governed tool/terminal proposals, F3 Claude Code sessions, AI-editor — remains a later slice,
declared UNAVAILABLE (not faked) via the hard-wired claim constants. Task tracking is a trace
projection, not a durable task DB.

## Next

- **F5.1 / F5.4 / F5.5** — live projections / Library / HQ.Command read-models.
- **F5.8** — React UI (SignalPanel + WorkOpsChatPanel on the shared client).
- WorkOPS Code slice (file browser + governed tool proposals) after the projection layer.
