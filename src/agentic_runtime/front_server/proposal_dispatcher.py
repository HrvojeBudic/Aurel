"""
proposal_dispatcher.py — the single reduction from UI intent to the kernel.

Every mutation the Front makes arrives here as a proposal and reduces to exactly
one of: a governed conversation turn (F5.C), a governed tool action via
`runtime.submit` (F5.2), or a read-only projection. It never touches a subsystem
directly.

  `converse` → `ConversationEngine.respond` (F5.3, when an engine is bound);
  `act` → `runtime.submit` two-phase (F5.2 skeleton). One door, two semantics.
"""
from __future__ import annotations

from typing import Any

# Proposal kinds the dispatcher will route.
KIND_CONVERSE = "converse"   # → ConversationEngine.respond (F5.C)
KIND_ACT = "act"             # → runtime.submit two-phase (F5.2)
_KNOWN_KINDS = (KIND_CONVERSE, KIND_ACT)

_REQUIRED_CONVERSE = ("room_id", "operator_identity", "role", "mandate_id", "text")


class ProposalRejected(ValueError):
    """A malformed / unroutable proposal. Fail-closed — nothing is dispatched."""


class ProposalDispatcher:
    """Reduces a proposal to a governed path."""

    def __init__(self, runtime: Any, *, conversation_engine: Any = None) -> None:
        # The kernel is the only executor; held for the F5.2 `act` reduction.
        self._runtime = getattr(runtime, "runtime", runtime)
        self._engine = conversation_engine

    def dispatch(self, proposal: Any) -> dict:
        """Validate + route a proposal. Fail-closed on shape."""
        if not isinstance(proposal, dict):
            raise ProposalRejected("proposal must be a JSON object")
        kind = proposal.get("kind")
        if kind not in _KNOWN_KINDS:
            raise ProposalRejected(f"unknown proposal kind {kind!r}")
        if kind == KIND_CONVERSE:
            return self._dispatch_converse(proposal)
        # `act` reduction lands in F5.2 (two-phase submit).
        return {"accepted": True, "kind": kind,
                "reduction": "runtime.submit two-phase (F5.2)", "wired": False}

    def _dispatch_converse(self, proposal: dict) -> dict:
        # Import here to avoid a package import cycle (signal ↔ dispatcher).
        from .conversation import ConversationTurn

        for f in _REQUIRED_CONVERSE:
            if not proposal.get(f):
                raise ProposalRejected(f"converse proposal requires {f!r}")
        if self._engine is None:
            return {"accepted": True, "kind": KIND_CONVERSE,
                    "reduction": "ConversationEngine.respond (F5.C)", "wired": False}
        turn = ConversationTurn.make(
            proposal["room_id"], proposal["text"],
            operator_identity=proposal["operator_identity"],
            role=proposal["role"], mandate_id=proposal["mandate_id"],
            context_refs=tuple(proposal.get("context_refs", []) or []),
        )
        reply = self._engine.respond(turn)
        return {"accepted": True, "kind": KIND_CONVERSE, "wired": True,
                "turn_id": turn.turn_id, "reply": reply.to_dict()}
