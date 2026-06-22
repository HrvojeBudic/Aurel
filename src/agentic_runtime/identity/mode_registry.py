"""Mode lookup for Aurel Communication Modes registry (P1.4.4).

Lookup returns mode specs only. It does not create sessions, grant authority,
or execute actions.
"""
from __future__ import annotations

from .communication_modes import (
    AurelCommunicationModeRegistry,
    CommunicationModeLookupResult,
)


def get_communication_mode(
    registry: AurelCommunicationModeRegistry,
    mode_name: str,
) -> CommunicationModeLookupResult:
    """Look up a mode by name (case-insensitive); return canonical uppercase name."""
    if not isinstance(mode_name, str) or not mode_name.strip():
        return CommunicationModeLookupResult(
            found=False,
            mode_name=None,
            mode=None,
            error="mode name must be a non-empty string",
        )
    canonical = mode_name.strip().upper()
    mode = registry.modes.get(canonical)
    if mode is None:
        return CommunicationModeLookupResult(
            found=False,
            mode_name=None,
            mode=None,
            error=f"unknown communication mode: {mode_name!r}",
        )
    return CommunicationModeLookupResult(
        found=True,
        mode_name=canonical,
        mode=mode,
        error=None,
    )
