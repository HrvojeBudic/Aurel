"""
chronos — F8 Time Plane: read-only forensic replay, fork simulation, causal diff.

Chronos does not introduce a second execution path. Replay and diff are read-only
over trace + state_store + worldline; fork mints an ephemeral child run only.

Additive behind ``AUREL_CHRONOS`` (default OFF ⇒ Chronos reads honestly UNAVAILABLE).
"""
from __future__ import annotations

import os

from .diff import ChronosDiff, DiffResult
from .fork import ChronosFork, ChronosForkResult
from .fork_gate import ForkGateEvidence, evaluate_fork_gate, flag_enabled as fork_gate_flag_enabled
from .irreversibility import (
    IrreversibilityClass,
    IrreversibilityResult,
    classify_irreversibility,
    influence_is_escalation_only,
)
from .replay import ChronosReplay, ReplayResult

_FLAG = "AUREL_CHRONOS"


def flag_enabled() -> bool:
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


__all__ = [
    "ChronosReplay",
    "ReplayResult",
    "ChronosFork",
    "ChronosForkResult",
    "ChronosDiff",
    "DiffResult",
    "ForkGateEvidence",
    "IrreversibilityClass",
    "IrreversibilityResult",
    "classify_irreversibility",
    "evaluate_fork_gate",
    "fork_gate_flag_enabled",
    "influence_is_escalation_only",
    "flag_enabled",
]
