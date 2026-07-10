"""
constitution — delegation windows + operator-contract wiring (F6.3).

The Constitution layer: the operator's machine-readable delegation of autonomy.
Every autonomous action cites an active window; an action outside every window is
denied fail-closed and the run drops to G0. Additive behind `AUREL_CONSTITUTION`.
"""
from __future__ import annotations

from .contract import autonomy_session_ref, delegation_grant_ref
from .delegation import (
    DELEGATION_GRANT_EVENT,
    DelegationDecision,
    DelegationLedger,
    DelegationWindow,
    flag_enabled,
    require_delegation,
)

__all__ = [
    "DelegationWindow",
    "DelegationDecision",
    "DelegationLedger",
    "require_delegation",
    "DELEGATION_GRANT_EVENT",
    "flag_enabled",
    "delegation_grant_ref",
    "autonomy_session_ref",
]
