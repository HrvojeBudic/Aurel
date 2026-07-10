"""
contract.py — fill the operator contract's delegation placeholders (F6.3).

The P1.4 operator contract reserved null placeholders for exactly this phase:
`delegation_grant_ref` and `autonomy_session_ref` (`identity/operator_contract.py`).
F6 populates them from the active delegation windows — a machine-readable pointer to
the grant an autonomous action cites — without mutating the immutable contract itself.
"""
from __future__ import annotations

from .delegation import DelegationWindow


def delegation_grant_ref(delegations: "list[DelegationWindow]", *, at: float) -> str:
    """The active delegation id an autonomous action cites, or '' (none active)."""
    for d in delegations:
        if d.is_active(at):
            return d.delegation_id
    return ""


def autonomy_session_ref(delegations: "list[DelegationWindow]", *, at: float) -> str:
    """The active autonomy-session anchor (the same active delegation in F6)."""
    return delegation_grant_ref(delegations, at=at)
