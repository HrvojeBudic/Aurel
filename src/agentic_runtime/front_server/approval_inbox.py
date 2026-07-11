"""
approval_inbox.py — the persistent approval inbox (F5.2).

A governed proposal that requires approval does not silently auto-anything — it
lands here as **pending** until the operator decides, and the decision is itself a
governed trace record.

Two layers, honestly separated:
  - **Trace = audit.** Every approval decision (defer / approve / deny) is an
    `ApprovalReceiptRecord` in the hash-chained trace — the immutable record.
    `audit_from_trace` reads it back.
  - **Inbox = actionable pending.** Re-submitting a command needs the command
    itself (its args), which the trace receipt does not carry. So the inbox holds
    the pending `CommandEnvelope` in-process (operational plumbing, not truth) so
    Phase B can re-submit exactly the same command.

The inbox swaps the runtime's approval gate around each submit (Phase A deferred,
Phase B pre-decided) and restores it — the default gate behavior is untouched.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..approval import ApprovalOutcome
from ..core_types import CommandEnvelope
from .approval_gates import DeferredApprovalGate, PreDecidedApprovalGate


@dataclass(frozen=True)
class PendingApproval:
    request_id: str
    tool: str
    risk: str
    summary: str
    issuer: str
    mandate_id: str = ""            # F7.8 — the authority the command was submitted under

    def to_dict(self) -> dict:
        return {"request_id": self.request_id, "tool": self.tool, "risk": self.risk,
                "summary": self.summary, "issuer": self.issuer,
                "mandate_id": self.mandate_id}


class ApprovalInbox:
    """In-process pending registry over one runtime's two-phase submit."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self._pending: dict[str, tuple[CommandEnvelope, Any, PendingApproval]] = {}

    def _with_gate(self, gate: Any, cmd: CommandEnvelope, card: Any) -> Any:
        prev = self._inner.approval_gate
        self._inner.approval_gate = gate
        try:
            return self._inner.submit(cmd, card)
        finally:
            self._inner.approval_gate = prev

    def submit_act(self, cmd: CommandEnvelope, card: Any) -> dict:
        """Phase A: propose. Deferred ⇒ pending; auto-allowed ⇒ executed; else blocked."""
        res = self._with_gate(DeferredApprovalGate(), cmd, card)
        dec = res.approval_decision
        if dec is not None and dec.outcome is ApprovalOutcome.DEFERRED:
            pend = PendingApproval(
                request_id=dec.request_id, tool=cmd.tool,
                risk=res.decision.risk.value, summary=cmd.expected_effect or cmd.tool,
                issuer=cmd.issuer_card_id, mandate_id=getattr(card, "mandate_id", ""),
            )
            self._pending[dec.request_id] = (cmd, card, pend)
            return {"status": "pending", "request_id": dec.request_id, "tool": cmd.tool}
        if res.ok:
            return {"status": "executed", "tool": cmd.tool}
        reason = (res.approval_decision.reason if res.approval_decision
                  else (res.verifier.reason if res.verifier else "blocked"))
        return {"status": "blocked", "tool": cmd.tool, "reason": reason}

    def decide(self, request_id: str, approve: bool) -> dict:
        """Phase B: re-submit the pending command with the operator's decision."""
        entry = self._pending.pop(request_id, None)
        if entry is None:
            return {"status": "unknown_request", "request_id": request_id}
        cmd, card, _pend = entry
        res = self._with_gate(PreDecidedApprovalGate(approve), cmd, card)
        if approve and res.ok:
            return {"status": "executed", "request_id": request_id, "tool": cmd.tool}
        return {"status": "denied" if not approve else "blocked",
                "request_id": request_id, "tool": cmd.tool}

    def pending(self) -> list[dict]:
        return [p.to_dict() for (_c, _card, p) in self._pending.values()]

    def get_pending(self, request_id: str) -> Optional[dict]:
        entry = self._pending.get(request_id)
        return entry[2].to_dict() if entry else None

    @staticmethod
    def audit_from_trace(trace: Any) -> list[dict]:
        """Every approval decision from the trace (the immutable audit view)."""
        out: list[dict] = []
        for ev in trace.replay():
            if ev.get("kind") == "approval_receipt":
                out.append({"tool": ev.get("tool"), "outcome": ev.get("outcome"),
                            "risk_class": ev.get("risk_class"),
                            "decided_by": ev.get("decided_by"),
                            "reason": ev.get("reason")})
        return out
