# AUREL F5.C — Governed LLM Conversation Engine

_branch `feat/f5-front-v1`. Talk to the LLM as a governed operation through the one door._

## What shipped
`front_server/conversation.py` — `ConversationEngine`: a turn assembles context via the
ContextLoom (F4, provenance + taint + budget, `context_ref` on every message), calls the
budget-charged router, and returns one of three honest modes — ANSWER, PROPOSE (a valid plan ⇒
an `act` proposal → approval → `runtime.submit`), or UNAVAILABLE (router refusal / no key /
budget / provider failure — never fabricated). History is a pure trace projection
(`RoomHistoryProjection`), room-agnostic (reused by Signal and WorkOPS). Carries the N1–N8 seams
(context_refs, source_refs, truth_label, profile, mandate, bitemporal stamp) from day one.

## Evidence
Seal `tests/test_p6f5_c_conversation.py` — answer records + binds context; propose emits a
proposal, never executes; router refusal + provider failure ⇒ UNAVAILABLE; room history from
trace; next-gen contract fields present; flag defaults OFF.

## Boundary
Sealed under a stub/cassette router; live-model driving is opt-in. Effort-aware profile
selection (N3) and streaming (N4) are declared seams.
