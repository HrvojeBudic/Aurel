# AUREL F5.3 — Signal Chat Contract

_branch `feat/f5-front-v1`. The operator talks to Aurel — zero local state, one door._

## What shipped
`front_server/signal.py` — `SignalMessage`, structurally un-constructible without its
provenance (room_id / operator_identity / role / mandate_id required). It reduces to a
`converse` `ProposalEnvelope` through the dispatcher → `ConversationEngine` (F5.C); a message
never calls a subsystem directly. History is a pure trace projection (no own store);
`context_refs` are exactly F4 ContextLoom hashes.

## Evidence
Seal `tests/test_p6f5_3_signal_chat.py` — message requires provenance; reduces to a converse
proposal; dispatcher → LLM answer + history from trace; over WebSocket end-to-end; flag OFF.

## Boundary
`SIGNAL_CHAT` window is contract-only (executes nothing); AurelEU is a PARTIAL seam (one persona,
role-fluid switching is F6, `claims_aureleu_dispatcher_live` False).
