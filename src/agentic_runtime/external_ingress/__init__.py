"""
external_ingress — F3.0 external-content taint & injection defense (Track D / D0).

The security foundation for every F3 external-executor surface (gate-check,
MCP gateway, MCP client bridge, A2A). It carries **one structural doctrine**:

    Instruction-eligibility is forbidden by PROVENANCE, not by scanning.

Content that originated outside the trusted core (an MCP tool result, an
external executor's payload, a scraped page, an A2A message) can NEVER be
constructed into a plan or instruction — regardless of how "clean" a scan looks.
The only instruction source in Aurel remains model output through the
``PlanValidator``. The injection detector here is *advisory* data-channel
defense-in-depth: it annotates, it never gates. That separation is the whole
point — a heuristic that could *permit* would be a heuristic an attacker can
defeat; a structural forbid cannot be talked around.

The Track-D umbrella flag ``AUREL_EXTERNAL_INGRESS`` is defined here for
continuity. In F3.0 it is *defined-not-gating*: this package is a pure library,
opt-in by being called, so nothing branches on the flag yet. It becomes
load-bearing when F3.1+ wires ingress into the gate / gateway paths.
"""
from __future__ import annotations

import os

from .injection_detector import (
    InjectionFinding,
    InjectionScanResult,
    InjectionSignature,
    Severity,
    scan_for_injection,
)
from .sanitization import CrossingKind, SanitizationCrossing, cross_as_data
from .taint import (
    EXTERNAL_ORIGIN_KINDS,
    SourceKind,
    TaintLabel,
    TaintedContent,
    make_tainted,
)

_FLAG = "AUREL_EXTERNAL_INGRESS"


def flag_enabled() -> bool:
    """True iff the external-ingress flag is explicitly enabled (default OFF).

    Fail-closed: an empty or unrecognized value is False. Defined-not-gating in
    F3.0 — provided for F3.1+ wiring continuity.
    """
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


__all__ = [
    "EXTERNAL_ORIGIN_KINDS",
    "SourceKind",
    "TaintLabel",
    "TaintedContent",
    "make_tainted",
    "InjectionFinding",
    "InjectionScanResult",
    "InjectionSignature",
    "Severity",
    "scan_for_injection",
    "CrossingKind",
    "SanitizationCrossing",
    "cross_as_data",
    "flag_enabled",
]
