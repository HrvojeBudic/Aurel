"""
panic.py — `aurel panic`, the operator kill-switch (F6.7).

Panic is a hard stop: it records a governed `aurel_panic` event and signals a drop
to G0 (the most-governed level). It is a **governed record**, never a silent halt —
the reason and who pulled it ride the trace. Actually suspending a running daemon is
a LATER concern (the daemon is not built); today panic is the recorded, replayable
signal that everything downstream must honor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core_types import PraxisEventRecord

PANIC_EVENT = "aurel_panic"
_MARK = "PANIC"


@dataclass(frozen=True)
class PanicResult:
    halted: bool
    reason: str
    invoked_by: str
    dropped_to_g0: bool = True

    def to_dict(self) -> dict:
        return {"halted": self.halted, "reason": self.reason,
                "invoked_by": self.invoked_by, "dropped_to_g0": self.dropped_to_g0}


def panic(runtime: Any, reason: str, *, invoked_by: str = "operator") -> PanicResult:
    """Record a governed panic (halt → G0). Never silent — the reason is traced."""
    inner = getattr(runtime, "runtime", runtime)
    inner.trace.append_praxis_event(PraxisEventRecord.make(
        run_id=inner.trace.run_id, agent_id=invoked_by,
        event_type=PANIC_EVENT, subject_id="panic",
        summary=f"{_MARK}|{invoked_by}|{reason}"))
    return PanicResult(halted=True, reason=reason, invoked_by=invoked_by)


def panic_events_from_trace(trace: Any) -> list[dict]:
    """All panic signals, reconstructed from the trace."""
    out: list[dict] = []
    for ev in trace.replay():
        if ev.get("kind") != "praxis_event" or ev.get("event_type") != PANIC_EVENT:
            continue
        parts = str(ev.get("summary", "")).split("|", 2)
        if len(parts) < 3:
            continue
        out.append({"invoked_by": parts[1], "reason": parts[2]})
    return out
