"""
board.py — the Board decision journal (F5.6).

A Board decision is a **governed record, not an execution.** The journal is a pure
trace projection (async — it feeds the weekly review, holds no own store). A
decision reaches action ONLY by "Convert to Proposal": it reduces to an `act`
`ProposalEnvelope` through the same one door (F5.0 dispatcher → approval inbox →
`runtime.submit`). The Board never calls a subsystem directly; real-time
multi-party debate is LATER.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ..core_types import PraxisEventRecord, new_id, now
from .proposal_dispatcher import KIND_ACT

BOARD_DECISION_EVENT = "board_decision"
_MARK = "BOARD"
_FLAG = "AUREL_FRONT_BOARD"


def flag_enabled() -> bool:
    """True iff the Board flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class BoardDecision:
    """A recorded Board decision. Provenance is mandatory; args ride the object."""

    decision_id: str
    title: str
    rationale: str
    proposed_tool: str
    proposed_args: dict
    decided_by: str
    risk: str = "medium"
    created_at: float = field(default_factory=now)

    def __post_init__(self) -> None:
        for field_name in ("title", "proposed_tool", "decided_by"):
            if not getattr(self, field_name):
                raise ValueError(f"BoardDecision requires a non-empty {field_name}")

    @staticmethod
    def make(title: str, *, rationale: str, proposed_tool: str,
             decided_by: str, proposed_args: dict | None = None,
             risk: str = "medium") -> "BoardDecision":
        return BoardDecision(
            decision_id=new_id("board"), title=title, rationale=rationale,
            proposed_tool=proposed_tool, proposed_args=dict(proposed_args or {}),
            decided_by=decided_by, risk=risk)

    def to_proposal(self) -> dict:
        """Convert to Proposal: an `act` for the one door (never direct execution)."""
        return {
            "kind": KIND_ACT,
            "tool": self.proposed_tool,
            "args": dict(self.proposed_args),
            "risk": self.risk,
            "rationale": self.rationale or self.title,
            "expected_effect": self.title,
        }


@dataclass(frozen=True)
class BoardJournalEntry:
    decision_id: str
    decided_by: str
    proposed_tool: str
    title: str

    def to_dict(self) -> dict:
        return {"decision_id": self.decision_id, "decided_by": self.decided_by,
                "proposed_tool": self.proposed_tool, "title": self.title}


def _summary(decision_id: str, decided_by: str, tool: str, title: str) -> str:
    return f"{_MARK}|{decision_id}|{decided_by}|{tool}|{title}"


class BoardJournal:
    """Records governed Board decisions and projects the journal from the trace."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)

    def record(self, decision: BoardDecision) -> BoardDecision:
        """Append a governed decision record to the trace. Records, never executes."""
        self._inner.trace.append_praxis_event(PraxisEventRecord.make(
            run_id=self._inner.trace.run_id,
            agent_id=decision.decided_by,
            event_type=BOARD_DECISION_EVENT,
            subject_id=decision.decision_id,
            summary=_summary(decision.decision_id, decision.decided_by,
                             decision.proposed_tool, decision.title),
        ))
        return decision

    @staticmethod
    def convert_to_proposal(decision: BoardDecision) -> dict:
        """Reduce a decision to an `act` proposal for the one door (F5.0)."""
        return decision.to_proposal()

    @staticmethod
    def from_trace(trace: Any) -> list[BoardJournalEntry]:
        """The decision journal, reconstructed purely from the trace (no own store)."""
        out: list[BoardJournalEntry] = []
        for ev in trace.replay():
            if ev.get("kind") != "praxis_event":
                continue
            if ev.get("event_type") != BOARD_DECISION_EVENT:
                continue
            summary = str(ev.get("summary", ""))
            if not summary.startswith(_MARK + "|"):
                continue
            parts = summary.split("|", 4)
            if len(parts) < 5:
                continue
            out.append(BoardJournalEntry(
                decision_id=parts[1], decided_by=parts[2],
                proposed_tool=parts[3], title=parts[4]))
        return out
