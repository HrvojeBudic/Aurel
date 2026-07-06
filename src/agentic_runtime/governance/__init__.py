"""Governance layer (P1.4.0 floor; M6 governance scale G0–G5).

Architectural law:
  - Constitutional floor is non-bypassable (P1.4.11).
  - Persona is not authority; persona cannot override policy.
  - Operator remains final authority.

M6 adds the manual autonomy spectrum ``GovernanceLevel`` G0–G5 as presets over
existing knobs (approval envelope, enforcement mode, sandbox/anchor floor), the
``resolve_effective`` precedence rule (most restrictive wins; operator override
audited), and ``audit_governance`` drift detection.
"""
from __future__ import annotations

from .audit import audit_governance, infer_effective_level
from .profile import (
    GovernanceFloorViolation,
    GovernanceLevel,
    GovernanceProfile,
    OverrideReceipt,
    ResolvedGovernance,
    governed_approver,
    issue_override,
    profile_for,
    resolve_effective,
    runtime_kwargs_for,
)

__all__ = [
    "GovernanceLevel",
    "GovernanceProfile",
    "GovernanceFloorViolation",
    "OverrideReceipt",
    "ResolvedGovernance",
    "issue_override",
    "profile_for",
    "resolve_effective",
    "governed_approver",
    "runtime_kwargs_for",
    "audit_governance",
    "infer_effective_level",
]
