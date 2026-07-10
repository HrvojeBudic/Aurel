"""
dn — DN (dynamic-negotiation) governance mechanisms (F6.7).

Advisory challenger pass, anti-stagnation tripwire, and the `aurel panic` kill-switch.
Each is fail-closed / advisory and leaves a governed record; none changes the default
execution path. The dual-kernel σ-governor + merge-gate are surfaced separately in
`front_server/dn.py` (F6.6).
"""
from __future__ import annotations

from .challenger import CHALLENGER_SYSTEM, Challenge, ChallengerPass
from .panic import PANIC_EVENT, PanicResult, panic, panic_events_from_trace
from .tripwire import TripwireResult, check_stagnation

__all__ = [
    "ChallengerPass",
    "Challenge",
    "CHALLENGER_SYSTEM",
    "check_stagnation",
    "TripwireResult",
    "panic",
    "panic_events_from_trace",
    "PanicResult",
    "PANIC_EVENT",
]
