"""
approval_gates.py — the two-phase approval gates (F5.2).

`runtime.submit` is synchronous; it is never parked mid-pipeline. Instead the Front
runs an approval-requiring command TWICE:

  - **Phase A (propose)** — `DeferredApprovalGate.request` returns a **DEFERRED**
    decision. DEFERRED is not `approved`, so submit fails closed into a BLOCKED
    transition — nothing executes — and the approval request + decision are traced
    as a pending marker.
  - **Phase B (decide)** — the operator's decision is replayed by
    `PreDecidedApprovalGate`, which returns exactly APPROVED / DENIED. Re-submitting
    the same command then completes (approved) or BLOCKs (denied).

Both implement the `ApprovalGate` protocol (`request(req) -> ApprovalDecision`).
Neither approves autonomously — the operator disposes.
"""
from __future__ import annotations

from ..approval import ApprovalDecision, ApprovalOutcome, ApprovalRequest


class DeferredApprovalGate:
    """Phase A: never decides — parks the request for the operator (DEFERRED)."""

    def request(self, req: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=req.request_id,
            outcome=ApprovalOutcome.DEFERRED,
            reason="parked in the Front approval inbox for operator decision",
            decided_by="front_inbox",
            confirmation_level=0,
        )


class PreDecidedApprovalGate:
    """Phase B: replays the operator's already-made decision."""

    def __init__(self, approve: bool, *, decided_by: str = "operator",
                 reason: str = "") -> None:
        self._outcome = ApprovalOutcome.APPROVED if approve else ApprovalOutcome.DENIED
        self._decided_by = decided_by
        self._reason = reason or ("operator approved" if approve else "operator denied")

    def request(self, req: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(
            request_id=req.request_id,
            outcome=self._outcome,
            reason=self._reason,
            decided_by=self._decided_by,
            confirmation_level=1,
        )
