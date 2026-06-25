"""Path governance source and trust labels (P1.7.0).

ProjectionSourceLabel describes operator-visible projection truth.
SourceTrustLabel describes content trust/origin — a separate axis.
"""
from __future__ import annotations

from enum import Enum


class ProjectionSourceLabel(str, Enum):
    """Integration-First truth label for operator-visible path governance data."""

    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    SIMULATED = "SIMULATED"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class SourceTrustLabel(str, Enum):
    """Content trust/origin label — not interchangeable with projection source."""

    TRUSTED = "TRUSTED"
    OPERATOR_PROVIDED = "OPERATOR_PROVIDED"
    INTERNAL_REPO = "INTERNAL_REPO"
    LOCAL_PRIVATE = "LOCAL_PRIVATE"
    TOOL_GENERATED = "TOOL_GENERATED"
    EXTERNAL = "EXTERNAL"
    UNTRUSTED = "UNTRUSTED"
    UNKNOWN = "UNKNOWN"
    QUARANTINED = "QUARANTINED"
