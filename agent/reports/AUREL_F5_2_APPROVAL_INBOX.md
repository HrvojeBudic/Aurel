# AUREL F5.2 — Persistent Approval Inbox + Two-Phase `act` Submit

_2026-07-09, branch `feat/f5-front-v1`. The governed-action branch of the one door._

## What shipped

An approval-requiring proposal no longer silently auto-anything — it lands in a pending
inbox until the operator decides, and every decision is a governed trace record.

- **`approval_gates.py`** — `DeferredApprovalGate` (Phase A: returns **DEFERRED** → submit
  fails closed into a BLOCKED transition, nothing executes, the request is traced) and
  `PreDecidedApprovalGate` (Phase B: replays the operator's APPROVED/DENIED). Neither
  approves autonomously.
- **`approval_inbox.py`** — `ApprovalInbox` runs the two-phase submit by swapping the
  runtime's approval gate around each `submit` and **restoring it** (default behavior
  untouched). `submit_act` (Phase A) → pending / auto-executed / blocked; `decide` (Phase B)
  → re-submits the exact same command with the operator's decision. Honest split:
  **trace = immutable audit** (`audit_from_trace` reads every defer/approve/deny receipt);
  **inbox = actionable pending** (holds the `CommandEnvelope` in-process so Phase B can
  re-submit — the trace receipt does not carry the command args).
- **`proposal_dispatcher.py`** — the `act` reduction now routes through the inbox
  (`submit_act`), and a new `decide` kind routes to `inbox.decide`. One door, three governed
  semantics (converse / act / decide).

## Evidence

- Seal `tests/test_p6f5_2_proposal_approval.py` — **5 passed**: defer → pending + DEFERRED
  traced + nothing executed + **default gate restored**; approve → the command **executes**
  (real end-to-end via a governed MCP-bridged tool) + pending cleared + "approved" in audit;
  deny → not executed; unknown request fails closed; dispatcher `act`/`decide` route to the
  inbox; decide requires its fields.
- ruff clean; mypy clean (9 files); compileall OK. F5.0a/0b/C/3 regression green.

## Boundary (honest)

The pending inbox is in-process operational state (holding commands to re-submit), NOT a
claim of durable persistence — the immutable audit lives in the trace. A multi-step plan's
`act` currently submits its first step (multi-step orchestration is a refinement).

## Next

**F5.7 — WorkOPS chat** on the same `ConversationEngine` (a `workops:*` room) ⇒ ▶ milestone
2: talk to the LLM through WorkOPS. Then F5.1/4/5 projections, F5.8 React UI, F5.9 exit seal.
