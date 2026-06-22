"""Capability status classification for Aurel Self-Model (P1.4.6)."""
from __future__ import annotations

from typing import Literal

CapabilityStatus = Literal[
    "planned",
    "implemented",
    "verified",
    "unavailable",
    "unknown",
    "partial",
    "experimental",
]

ALLOWED_CAPABILITY_STATUSES: frozenset[str] = frozenset(
    {
        "planned",
        "implemented",
        "verified",
        "unavailable",
        "unknown",
        "partial",
        "experimental",
    }
)

REQUIRED_CAPABILITY_STATUSES: frozenset[str] = frozenset(
    {
        "planned",
        "implemented",
        "verified",
        "unavailable",
        "unknown",
        "partial",
        "experimental",
    }
)
