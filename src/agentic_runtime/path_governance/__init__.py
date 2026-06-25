"""Path Governance & Source Trust Foundation (P1.7.0).

Foundation-only package: labels, posture vocabulary, closed-world validation,
deterministic serialization, and honest capability reporting.

Architectural law:
  - Projection source labels describe operator-visible truth.
  - Source trust labels describe content origin/trust — a separate axis.
  - P1.7.0 does not resolve paths, enforce governance, bind CLI, or write Ledger.
"""
from __future__ import annotations

from .errors import (
    PathGovernanceError,
    PathGovernanceErrorCode,
    PathGovernanceSerializationError,
    PathGovernanceStructuredError,
    PathGovernanceUnknownFieldError,
    PathGovernanceValidationError,
)
from .foundation import (
    PATH_GOVERNANCE_UNAVAILABLE_REASONS,
    get_path_governance_foundation_status,
)
from .labels import ProjectionSourceLabel, SourceTrustLabel
from .serialization import stable_hash, to_canonical_dict, to_canonical_json
from .types import (
    CAPABILITY_STATUS_KNOWN_FIELDS,
    PATH_GOVERNANCE_MODULE_NAME,
    PATH_GOVERNANCE_MODULE_VERSION,
    PATH_GOVERNANCE_TASK_ID,
    FoundationPosture,
    PathGovernanceCapabilityStatus,
)
from .validation import validate_known_fields

__all__ = [
    "CAPABILITY_STATUS_KNOWN_FIELDS",
    "FoundationPosture",
    "PATH_GOVERNANCE_MODULE_NAME",
    "PATH_GOVERNANCE_MODULE_VERSION",
    "PATH_GOVERNANCE_TASK_ID",
    "PATH_GOVERNANCE_UNAVAILABLE_REASONS",
    "PathGovernanceCapabilityStatus",
    "PathGovernanceError",
    "PathGovernanceErrorCode",
    "PathGovernanceSerializationError",
    "PathGovernanceStructuredError",
    "PathGovernanceUnknownFieldError",
    "PathGovernanceValidationError",
    "ProjectionSourceLabel",
    "SourceTrustLabel",
    "get_path_governance_foundation_status",
    "stable_hash",
    "to_canonical_dict",
    "to_canonical_json",
    "validate_known_fields",
]
