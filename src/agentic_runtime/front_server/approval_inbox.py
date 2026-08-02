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

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from ..approval import ApprovalOutcome
from ..core_types import CommandEnvelope, RiskLevel
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


class PendingStoreError(RuntimeError):
    """A parked command could not be restored under the current authority."""


class ApprovalInbox:
    """Pending registry over one runtime's two-phase submit.

    Pending items are persisted so a restart does not silently drop everything an
    operator was asked to decide. What is persisted is the **command**, never the
    ``AgentCard``: authority must come from the live process, not from a file on
    disk that anyone able to write to the trace directory could forge. On restore
    the command is re-bound to the card the server was constructed with, and the
    recorded ``issuer_card_id`` must still match it — the operator card's id is
    derived from its own authority content, so a changed scope or risk ceiling
    changes the id and the stale item is refused rather than executed under
    permissions its proposer never had.
    """

    def __init__(self, runtime: Any, *, card: Any = None,
                 store_dir: Optional[str] = None) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self._pending: dict[str, tuple[CommandEnvelope, Any, PendingApproval]] = {}
        self._card = card
        self._store_dir = store_dir or self._default_store_dir()
        self._rehydrate()

    # -- persistence ------------------------------------------------------- #
    def _default_store_dir(self) -> Optional[str]:
        """``<trace base_dir>/pending``, or None for a non-durable ledger.

        An in-memory trace has nothing to be continuous with, so persisting
        pending items beside it would outlive the very history that explains
        them. No directory ⇒ in-process only, exactly as before.
        """
        base = getattr(self._inner.trace, "base_dir", None)
        return os.path.join(str(base), "pending") if base else None

    def _path_for(self, request_id: str) -> Optional[str]:
        if not self._store_dir or "/" in request_id or "\\" in request_id:
            return None
        return os.path.join(self._store_dir, f"{request_id}.json")

    def _persist(self, request_id: str, cmd: CommandEnvelope,
                 pend: "PendingApproval") -> None:
        path = self._path_for(request_id)
        if not path:
            return
        try:
            os.makedirs(self._store_dir, exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"command": cmd.to_dict(), "pending": pend.to_dict()}, fh)
            os.replace(tmp, path)          # atomic: never a half-written item
        except OSError:
            pass  # durability is best-effort; the in-process queue still works

    def _forget(self, request_id: str) -> None:
        path = self._path_for(request_id)
        if not path:
            return
        try:
            os.remove(path)
        except OSError:
            pass

    def _rehydrate(self) -> None:
        """Restore parked commands from a previous process."""
        if not self._store_dir or not os.path.isdir(self._store_dir):
            return
        for name in sorted(os.listdir(self._store_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self._store_dir, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    payload = json.load(fh)
                cmd = self._command_from(payload["command"])
                pend = PendingApproval(**payload["pending"])
            except (OSError, ValueError, KeyError, TypeError):
                continue  # unreadable item: leave the file, skip the entry
            self._pending[pend.request_id] = (cmd, self._card, pend)

    @staticmethod
    def _command_from(data: dict) -> CommandEnvelope:
        """Rebuild an envelope from its own ``to_dict``. Only the command — the
        card is never taken from disk."""
        return CommandEnvelope(
            id=str(data["id"]),
            issuer_card_id=str(data["issuer_card_id"]),
            tool=str(data["tool"]),
            args=dict(data.get("args") or {}),
            rationale=str(data.get("rationale", "")),
            declared_risk=RiskLevel(str(data["declared_risk"])),
            expected_effect=str(data.get("expected_effect", "")),
            parent_intent_id=data.get("parent_intent_id"),
        )

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
            self._persist(dec.request_id, cmd, pend)
            return {"status": "pending", "request_id": dec.request_id, "tool": cmd.tool}
        if res.ok:
            return {"status": "executed", "tool": cmd.tool}
        reason = (res.approval_decision.reason if res.approval_decision
                  else (res.verifier.reason if res.verifier else "blocked"))
        return {"status": "blocked", "tool": cmd.tool, "reason": reason}

    def decide(self, request_id: str, approve: bool) -> dict:
        """Phase B: re-submit the pending command with the operator's decision."""
        entry = self._pending.get(request_id)
        if entry is None:
            return {"status": "unknown_request", "request_id": request_id}
        cmd, card, _pend = entry
        # Refusals below leave the item PARKED. Consuming a request the operator
        # was never actually able to decide would destroy it: they could not
        # restart under the original authority and approve it afterwards, and the
        # durable record would be gone with it.
        if card is None:
            return {"status": "blocked", "request_id": request_id, "tool": cmd.tool,
                    "reason": "no agent card bound; cannot re-submit"}
        # The parked command names the authority it was proposed under. Executing
        # it against a different envelope would grant permissions its proposer
        # never had, so a mismatch is refused rather than reconciled.
        if cmd.issuer_card_id != getattr(card, "id", None):
            return {"status": "blocked", "request_id": request_id, "tool": cmd.tool,
                    "reason": "authority changed since this was parked "
                              f"(proposed under {cmd.issuer_card_id}, "
                              f"now {getattr(card, 'id', '')}); re-propose it"}
        # The operator's decision is real from here on, so the item is consumed.
        self._pending.pop(request_id, None)
        self._forget(request_id)
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
