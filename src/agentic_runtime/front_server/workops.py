"""
workops.py — WorkOPS chat on the conversation engine (F5.7, milestone 2).

Talk to the LLM through the WorkOPS surface. WorkOPS is **task-scoped**: every
message belongs to a task, and its room is ``workops:<task_id>``. The chat rides
the SAME governed `ConversationEngine` as Signal (F5.3) — a different room, the
same one door (a message reduces to a `converse` `ProposalEnvelope`, never a direct
subsystem call). A `WorkOpsMessage` is **un-constructible without its provenance**:
task_id, operator_identity, role and mandate_id are required, so you cannot make a
WorkOPS message that lacks who/under-what-task/under-what-mandate it came from.

History and task tracking are **pure trace projections** (zero own store): the
task list and per-task history are reconstructed from the conversation events, so
the same trace always yields the same WorkOPS view.

The WorkOPS **Code** surface (read-only file browser, F3 Claude Code sessions,
AI-editor / collaboration) is a LATER slice. Its capability claims are hard-wired
`False` here so its absence is an honest UNAVAILABLE seam, never over-claimed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from .conversation import (
    ConversationTurn,
    HistoryEntry,
    RoomHistoryProjection,
    rooms_from_trace,
)
from .proposal_dispatcher import KIND_CONVERSE

_FLAG = "AUREL_FRONT_WORKOPS"
_ROOM_PREFIX = "workops:"

# Honest capability claims for the deferred WorkOPS Code surface. Hard-wired False:
# the file browser / terminal / AI-editor are a later slice (dispatch §F5.7). A
# boolean that would lie is not constructible True here — the absence is declared,
# not faked.
CLAIMS_WORKOPS_CODE_LIVE = False
CLAIMS_WORKOPS_TERMINAL_LIVE = False
CLAIMS_WORKOPS_AI_EDITOR = False


def flag_enabled() -> bool:
    """True iff the WorkOPS flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


def workops_room(task_id: str) -> str:
    """The conversation room for a WorkOPS task (``workops:<task_id>``)."""
    if not task_id:
        raise ValueError("workops_room requires a non-empty task_id")
    return f"{_ROOM_PREFIX}{task_id}"


@dataclass(frozen=True)
class WorkOpsMessage:
    """One operator message in a WorkOPS task. All provenance is mandatory (no defaults)."""

    task_id: str
    operator_identity: str
    role: str
    mandate_id: str
    context_refs: tuple[str, ...]
    text: str

    def __post_init__(self) -> None:
        for field_name in ("task_id", "operator_identity", "role", "mandate_id"):
            if not getattr(self, field_name):
                raise ValueError(f"WorkOpsMessage requires a non-empty {field_name}")

    @property
    def room_id(self) -> str:
        return workops_room(self.task_id)

    def to_proposal(self) -> dict:
        """Reduce to a `converse` proposal for the one door (same as Signal, task room)."""
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


@dataclass(frozen=True)
class WorkOpsTask:
    """A tracked WorkOPS task, derived from the trace. Zero own state."""

    task_id: str
    room_id: str
    message_count: int
    last_text: str

    def to_dict(self) -> dict:
        return {"task_id": self.task_id, "room_id": self.room_id,
                "message_count": self.message_count, "last_text": self.last_text}


class WorkOpsChatReadModel:
    """WorkOPS chat as a pure trace projection — same engine, task-scoped rooms.

    Task tracking is not a store: `task_ids`/`tasks`/`history` are reconstructed
    from the conversation events, deterministically (the same trace ⇒ the same view).
    """

    @staticmethod
    def task_ids(trace: object) -> list[str]:
        """The WorkOPS task ids present in the trace, sorted."""
        return [r[len(_ROOM_PREFIX):] for r in rooms_from_trace(trace, _ROOM_PREFIX)]

    @staticmethod
    def history(trace: object, task_id: str) -> list[HistoryEntry]:
        """The message history for one WorkOPS task (operator + assistant turns)."""
        return RoomHistoryProjection.from_trace(trace, workops_room(task_id))

    @staticmethod
    def tasks(trace: object) -> list[WorkOpsTask]:
        """All tracked WorkOPS tasks with their message counts and last message."""
        out: list[WorkOpsTask] = []
        for task_id in WorkOpsChatReadModel.task_ids(trace):
            hist = WorkOpsChatReadModel.history(trace, task_id)
            last = hist[-1].text if hist else ""
            out.append(WorkOpsTask(
                task_id=task_id, room_id=workops_room(task_id),
                message_count=len(hist), last_text=last))
        return out
