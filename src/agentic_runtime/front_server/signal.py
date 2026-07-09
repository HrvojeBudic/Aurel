"""
signal.py — the Signal chat contract (F5.3).

A Signal message is the operator talking to Aurel. It has **zero local state** —
history is a trace projection (F5.C `RoomHistoryProjection`) — and it is
**structurally un-constructible without its provenance**: identity, role,
mandate_id, room_id and context_refs are required constructor arguments, so you
cannot make a `SignalMessage` that lacks who/where/under-what-mandate it came from.
A message never calls a subsystem directly: it reduces to a `converse`
`ProposalEnvelope` through the one door (the dispatcher → `ConversationEngine`).

`context_refs` are exactly F4 ContextLoom hashes — the operator attaches Library
references to a message; they ride the turn as provenance.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from .conversation import ConversationTurn
from .proposal_dispatcher import KIND_CONVERSE

_FLAG = "AUREL_FRONT_SIGNAL"


def flag_enabled() -> bool:
    """True iff the Signal flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class SignalMessage:
    """One operator message. All provenance fields are mandatory (no defaults)."""

    room_id: str
    operator_identity: str
    role: str
    mandate_id: str
    context_refs: tuple[str, ...]
    text: str

    def __post_init__(self) -> None:
        for field_name in ("room_id", "operator_identity", "role", "mandate_id"):
            if not getattr(self, field_name):
                raise ValueError(f"SignalMessage requires a non-empty {field_name}")

    def to_proposal(self) -> dict:
        """Reduce to a `converse` proposal for the one door."""
        return {
            "kind": KIND_CONVERSE,
            "room_id": self.room_id,
            "operator_identity": self.operator_identity,
            "role": self.role,
            "mandate_id": self.mandate_id,
            "context_refs": list(self.context_refs),
            "text": self.text,
        }

    def to_turn(self) -> ConversationTurn:
        return ConversationTurn.make(
            self.room_id, self.text,
            operator_identity=self.operator_identity,
            role=self.role, mandate_id=self.mandate_id,
            context_refs=tuple(self.context_refs),
        )
