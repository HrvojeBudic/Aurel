"""
default.py — the default (passthrough) mandate (F6.0).

The default mandate is the honest baseline that reproduces F5 behaviour: it
declares a scope (so it is a real, constructible mandate — no-overclaim) but adds
no path/repo/tool restriction, so the F6.2 gate is a passthrough. Every turn whose
`mandate_id` is `"default"` resolves here; this keeps the flag-off / no-mandate
path byte-identical to F5.
"""
from __future__ import annotations

from .mandate import Mandate, MandateScope
from .registry import MandateRegistry

DEFAULT_MANDATE_ID = "default"


def default_mandate() -> Mandate:
    """The passthrough mandate: a declared, permissive scope (no extra restriction)."""
    return Mandate(
        mandate_id=DEFAULT_MANDATE_ID,
        version="v1",
        scope=MandateScope(client_id="default"),  # permissive: no path/tool cap
        persona_ref="default",
    )


def default_registry(*, policy_registry: object = None) -> MandateRegistry:
    """A registry containing only the default mandate."""
    return MandateRegistry.from_mandates([default_mandate()], policy_registry=policy_registry)
