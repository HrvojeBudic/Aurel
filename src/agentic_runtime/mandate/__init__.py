"""
mandate — the Mandate runtime object + resolution + (F6.2) enforcement.

F6: a mandate is authority (distinct from persona = expression). It travels with a
dispatched agent, is content-hashed + versioned, resolves from `mandate_id`, and
only ever *tightens* an AgentCard's authority. Additive behind `AUREL_MANDATE`
(default OFF ⇒ the default passthrough mandate reproduces F5).
"""
from __future__ import annotations

from .default import DEFAULT_MANDATE_ID, default_mandate, default_registry
from .enforcement import MandateCheckResult, evaluate_mandate_scope_check
from .mandate import Mandate, MandateScope, flag_enabled
from .registry import MandateNotFound, MandateRegistry

__all__ = [
    "Mandate",
    "MandateScope",
    "MandateRegistry",
    "MandateNotFound",
    "default_mandate",
    "default_registry",
    "DEFAULT_MANDATE_ID",
    "flag_enabled",
    "MandateCheckResult",
    "evaluate_mandate_scope_check",
]
