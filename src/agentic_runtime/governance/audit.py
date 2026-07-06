"""Governance drift audit (M6).

Anti-drift without new runtime hooks: from a run's *existing* trace records
(approval receipts carry ``risk_class`` + ``decided_by``; sandbox attestation
carries isolation state) infer the *minimal* governance level that would have
permitted the observed behavior, and compare it to the declared level. An agent
that auto-approved an R3 command while declared G1 is operating a level above
its declaration — silent drift toward HERETIC — and the audit surfaces it.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ..approval import ApprovalRiskClass
from .profile import GovernanceLevel, _PRESETS, _RISK_ORDER


def _risk_index(value: Any) -> Optional[int]:
    """Coerce a stored risk_class (enum or 'R2' string) to its 0..5 index."""
    if isinstance(value, ApprovalRiskClass):
        return _RISK_ORDER.index(value)
    if isinstance(value, str) and value.startswith("R") and value[1:].isdigit():
        n = int(value[1:])
        return n if 0 <= n <= 5 else None
    return None


def _min_level_for_auto_risk(risk_index: int) -> GovernanceLevel:
    """Lowest level whose auto-approval envelope covers ``risk_index``."""
    for level in GovernanceLevel:
        prof = _PRESETS[level]
        if _RISK_ORDER.index(prof.auto_approve_max) >= risk_index:
            return level
    return GovernanceLevel.G5


def infer_effective_level(replay_events: Iterable[dict]) -> dict:
    """Infer the minimal level consistent with what the run actually did.

    Signal = the highest risk class that was *auto-approved* (no human). The
    minimal level whose auto-approval envelope covers it is the effective level
    the run operated at, regardless of what it declared.
    """
    max_auto = -1
    auto_count = 0
    for ev in replay_events:
        if ev.get("kind") != "approval_receipt":
            continue
        decided_by = str(ev.get("decided_by", ""))
        outcome = str(ev.get("outcome", ""))
        if "auto" not in decided_by and "auto" not in outcome:
            continue  # a human decided this one; it implies no autonomy
        idx = _risk_index(ev.get("risk_class"))
        if idx is None:
            continue
        auto_count += 1
        max_auto = max(max_auto, idx)

    if max_auto < 0:
        level = GovernanceLevel.G0  # nothing needed autonomy
    else:
        level = _min_level_for_auto_risk(max_auto)
    return {
        "effective_level": level.value,
        "max_auto_approved_risk": None if max_auto < 0 else _RISK_ORDER[max_auto].value,
        "auto_approved_count": auto_count,
    }


def audit_governance(declared_level: GovernanceLevel, replay_events: Iterable[dict]) -> dict:
    """Compare inferred effective level to the declared one; flag upward drift."""
    events = list(replay_events)
    inferred = infer_effective_level(events)
    effective = GovernanceLevel(inferred["effective_level"])
    drift = effective.rank > declared_level.rank
    return {
        "declared_level": declared_level.value,
        "effective_level": effective.value,
        "drift_detected": drift,
        "max_auto_approved_risk": inferred["max_auto_approved_risk"],
        "auto_approved_count": inferred["auto_approved_count"],
        "reason": (
            f"run auto-approved up to {inferred['max_auto_approved_risk']} — needs "
            f"{effective.value} but declared {declared_level.value}"
            if drift else "effective level within declaration"
        ),
    }
