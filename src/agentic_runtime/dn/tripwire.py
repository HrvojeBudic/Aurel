"""
tripwire.py — the anti-stagnation tripwire (F6.7).

Detects a stuck loop from the trace alone: a run of identical non-terminal status
transitions (same to-status + reason_code) with no intervening progress. On trip it
**escalates fail-closed** (the caller must stop / re-plan / hand to the operator);
it never silently lets the loop continue. Pure projection over the trace.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_TERMINAL = {"succeeded", "completed", "done"}


@dataclass(frozen=True)
class TripwireResult:
    triggered: bool
    reason: str = ""
    streak: int = 0

    def to_dict(self) -> dict:
        return {"triggered": self.triggered, "reason": self.reason, "streak": self.streak}


def check_stagnation(trace: Any, *, repeat_threshold: int = 3) -> TripwireResult:
    """Trip iff `repeat_threshold` consecutive identical non-terminal transitions occur
    with no terminal (progress) transition breaking the streak. Fail-closed on trip."""
    if repeat_threshold < 1:
        repeat_threshold = 1
    streak = 0
    prev: Any = None
    for ev in trace.replay():
        if ev.get("kind") != "runtime_status_transition":
            continue
        to = ev.get("to", "")
        if to in _TERMINAL:
            streak = 0
            prev = None
            continue
        key = (to, ev.get("reason_code", ""))
        streak = streak + 1 if key == prev else 1
        prev = key
        if streak >= repeat_threshold:
            return TripwireResult(
                True,
                f"anti-stagnation: {streak}x '{to}'/{ev.get('reason_code', '')} "
                f"with no progress",
                streak=streak)
    return TripwireResult(False, streak=streak)
