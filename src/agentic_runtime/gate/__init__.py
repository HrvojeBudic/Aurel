"""
gate — F3.1 governance preflight for external executors.

`aurel gate check` runs a proposed (tool, args) from an external executor (a
Claude Code session, another agent) through Aurel's real contract + policy chain
**read-only** — no execution, no budget charge, no sandbox touch, no trace
append — and returns allow/deny + reason. It is the backend of the Front
WorkOPS.Code screen: the same governed channel that will later actually run the
action, surfaced early as a preflight.

The proposed action enters as external-origin content (F3.0 taint), so it is
instruction-ineligible: the gate evaluates it as a *request*, never executes it
as an instruction. ALLOW is a preflight verdict, not final authorization —
budget / sandbox / approval still apply when the action runs through `submit`.
"""
from __future__ import annotations

from .gate_check import (
    GateCheckDecision,
    GateChecker,
    GatePhase,
    GateVerdict,
)

__all__ = [
    "GateCheckDecision",
    "GateChecker",
    "GatePhase",
    "GateVerdict",
]
