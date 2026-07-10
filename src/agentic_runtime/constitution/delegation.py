"""
delegation.py — Constitution delegation windows (F6.3).

A delegation window is the operator's machine-readable grant of autonomy: "for this
scope, up to this autonomy ceiling, until this time". Every **autonomous** action
(one taken without the operator in the loop) must cite an active delegation that
covers it; an action outside every active window is **denied fail-closed** and the
run drops to G0 with a notification. A delegation can never lift autonomy above the
identity kernel's constitutional floor (self-escalation stays A7-denied — enforced
by the kernel, not liftable here).

The window is a governed record: it is granted into the trace and the active set is
a pure trace projection (zero own store). Delegations fill the operator contract's
`delegation_grant_ref` / `autonomy_session_ref` placeholders (F6.3 `contract.py`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

from ..core_types import PraxisEventRecord, new_id, now
from ..identity.autonomy_scale_engine import AutonomyLevel, is_denied

_FLAG = "AUREL_CONSTITUTION"
DELEGATION_GRANT_EVENT = "delegation_grant"
_MARK = "DELG"

# Autonomy ranks for A0–A6 (A7 is denial, never a ceiling — compared via is_denied).
_LEVEL_RANK = {
    AutonomyLevel.A0_ANSWER_ONLY: 0,
    AutonomyLevel.A1_SUGGESTION: 1,
    AutonomyLevel.A2_DRAFT: 2,
    AutonomyLevel.A3_REVERSIBLE_LOCAL_ACTION: 3,
    AutonomyLevel.A4_GOVERNED_TOOL_ACTION: 4,
    AutonomyLevel.A5_CONDITIONAL_EXECUTION: 5,
    AutonomyLevel.A6_APPROVAL_GATED_HIGH_RISK: 6,
}


def flag_enabled() -> bool:
    """True iff the Constitution flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class DelegationWindow:
    """One operator grant: scope + autonomy ceiling + time window. Governed record."""

    delegation_id: str
    granted_by: str
    autonomy_ceiling: AutonomyLevel
    valid_from: float
    valid_until: float                       # 0 ⇒ no expiry
    action_categories: tuple[str, ...] = ()  # empty ⇒ all categories
    consent_ref: str = ""

    def __post_init__(self) -> None:
        if not self.delegation_id or not self.granted_by:
            raise ValueError("DelegationWindow requires delegation_id and granted_by")
        if is_denied(self.autonomy_ceiling):
            raise ValueError("a delegation ceiling cannot be A7_DENIED")

    @staticmethod
    def make(granted_by: str, autonomy_ceiling: AutonomyLevel, *,
             valid_from: Optional[float] = None, valid_until: float = 0.0,
             action_categories: tuple[str, ...] = (), consent_ref: str = "",
             ) -> "DelegationWindow":
        return DelegationWindow(
            delegation_id=new_id("delg"), granted_by=granted_by,
            autonomy_ceiling=autonomy_ceiling,
            valid_from=valid_from if valid_from is not None else now(),
            valid_until=valid_until, action_categories=tuple(action_categories),
            consent_ref=consent_ref)

    def is_active(self, at: float) -> bool:
        return self.valid_from <= at and (self.valid_until == 0.0 or at < self.valid_until)

    def covers(self, level: AutonomyLevel, category: str) -> bool:
        """True iff this window authorizes `level` for `category` (ignoring time)."""
        if is_denied(level):
            return False  # a denied action is never covered
        if _LEVEL_RANK[level] > _LEVEL_RANK[self.autonomy_ceiling]:
            return False  # above the ceiling
        return not self.action_categories or category in self.action_categories


@dataclass(frozen=True)
class DelegationDecision:
    """Cite-or-deny outcome for an autonomous action."""

    allowed: bool
    cited_delegation_id: str = ""
    reason: str = ""
    drop_to_g0: bool = False

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "cited_delegation_id": self.cited_delegation_id,
                "reason": self.reason, "drop_to_g0": self.drop_to_g0}


def require_delegation(
    level: AutonomyLevel, category: str, delegations: "list[DelegationWindow]", *, at: float
) -> DelegationDecision:
    """An autonomous action must cite an active window covering it, else fail-closed → G0."""
    if is_denied(level):
        return DelegationDecision(
            False, reason="action is constitutionally denied (A7)", drop_to_g0=True)
    for d in delegations:
        if d.is_active(at) and d.covers(level, category):
            return DelegationDecision(True, cited_delegation_id=d.delegation_id)
    return DelegationDecision(
        False,
        reason=f"no active delegation covers {level.value} for {category!r}",
        drop_to_g0=True)


def _summary(d: DelegationWindow) -> str:
    return (f"{_MARK}|{d.delegation_id}|{d.granted_by}|{d.autonomy_ceiling.value}|"
            f"{d.valid_from}|{d.valid_until}|{d.consent_ref}|"
            f"{','.join(d.action_categories)}")


class DelegationLedger:
    """Grants delegation windows into the trace and projects the active set."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)

    def grant(self, window: DelegationWindow) -> DelegationWindow:
        self._inner.trace.append_praxis_event(PraxisEventRecord.make(
            run_id=self._inner.trace.run_id, agent_id=window.granted_by,
            event_type=DELEGATION_GRANT_EVENT, subject_id=window.delegation_id,
            summary=_summary(window)))
        return window

    @staticmethod
    def from_trace(trace: Any) -> list[DelegationWindow]:
        """All granted delegation windows, reconstructed purely from the trace."""
        out: list[DelegationWindow] = []
        for ev in trace.replay():
            if ev.get("kind") != "praxis_event":
                continue
            if ev.get("event_type") != DELEGATION_GRANT_EVENT:
                continue
            summary = str(ev.get("summary", ""))
            if not summary.startswith(_MARK + "|"):
                continue
            parts = summary.split("|", 7)
            if len(parts) < 8:
                continue
            cats = tuple(c for c in parts[7].split(",") if c)
            out.append(DelegationWindow(
                delegation_id=parts[1], granted_by=parts[2],
                autonomy_ceiling=AutonomyLevel(parts[3]),
                valid_from=float(parts[4]), valid_until=float(parts[5]),
                consent_ref=parts[6], action_categories=cats))
        return out

    @staticmethod
    def active(trace: Any, *, at: float) -> list[DelegationWindow]:
        return [d for d in DelegationLedger.from_trace(trace) if d.is_active(at)]
