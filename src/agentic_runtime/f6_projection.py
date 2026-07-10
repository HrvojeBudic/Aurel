"""
f6_projection.py — the F6.10 north-star run projection.

A single read-only view composing the whole F6 chain from the trace: the operator's
Signal history, the AurelEU governance state (bound mandates, delegation windows,
persona switches, DN status), and any constitution violations — so the north-star
scenario (Signal intent under a mandate → AurelEU resolves persona + cites a
delegation → dispatch → in-scope proceeds / out-of-scope denied → mandate_id in
every record) is provably replayable from the trace. Pure composition; zero writes.
"""
from __future__ import annotations

from typing import Any

from .front_server.aureleu import CONSTITUTION_VIOLATION_EVENT
from .front_server.aureleu_read_model import AurelEUReadModel
from .front_server.conversation import RoomHistoryProjection


class F6RunProjection:
    """The full Signal → AurelEU (mandate + delegation + persona) run, from the trace."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)

    def _violations(self) -> list[dict]:
        out: list[dict] = []
        for ev in self._inner.trace.replay():
            if ev.get("kind") != "praxis_event":
                continue
            if ev.get("event_type") != CONSTITUTION_VIOLATION_EVENT:
                continue
            parts = str(ev.get("summary", "")).split("|", 2)
            if len(parts) >= 3:
                out.append({"mandate_id": parts[1], "reason": parts[2]})
        return out

    def to_dict(self, *, signal_room: str = "signal:main") -> dict:
        trace = self._inner.trace
        aureleu = AurelEUReadModel(self._inner).to_dict()
        return {
            "signal_history": [
                e.to_dict() for e in RoomHistoryProjection.from_trace(trace, signal_room)
            ],
            "aureleu": aureleu,
            "constitution_violations": self._violations(),
            "replayable": True,  # every field above is a pure trace projection
        }
