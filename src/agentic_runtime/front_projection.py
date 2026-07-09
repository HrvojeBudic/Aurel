"""
front_projection.py — the F5.9 north-star run projection.

A single read-only view over the trace that composes the whole Front v1 chain —
Signal history → approval audit → run status → Library — so the north-star scenario
(operator intent in Signal → proposal → approval in HQ.Command → execution visible
→ artifact in Library) is provably replayable from the trace alone, with zero
direct UI calls. It is pure composition of the F5 read models; it writes nothing.
"""
from __future__ import annotations

from typing import Any

from .front_server.conversation import RoomHistoryProjection
from .front_server.hq_command import HQCommandReadModel
from .front_server.library import LibraryReadModel
from .front_server.workops import WorkOpsChatReadModel


class FrontRunProjection:
    """The full Signal → approval → exec → Library run, projected from the trace."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)

    def to_dict(self, *, signal_room: str = "signal:main") -> dict:
        trace = self._inner.trace
        hq = HQCommandReadModel.from_runtime(self._inner)
        lib = LibraryReadModel.from_trace(trace)
        return {
            "signal_history": [
                e.to_dict() for e in RoomHistoryProjection.from_trace(trace, signal_room)
            ],
            "workops_tasks": [t.to_dict() for t in WorkOpsChatReadModel.tasks(trace)],
            "runs": hq.run_status(),
            "approvals_audit": hq.approvals()["audit"],
            "library": {
                "min_truth_state": lib.min_truth_state(),
                "memory_by_tier": lib.memory_by_tier(),
                "assets_count": len(lib.assets()),
            },
            "replayable": True,  # every field above is a pure trace projection
        }
