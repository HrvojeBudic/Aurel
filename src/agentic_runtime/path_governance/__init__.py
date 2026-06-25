"""Path Governance & Source Trust Foundation (P1.7.0).

Foundation-only package: labels, posture vocabulary, closed-world validation,
deterministic serialization, and honest capability reporting.
P1.7.1 adds deterministic path identity schema objects without enforcement.

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
from .canonical_path import (
    TRAVERSAL_WARNING,
    normalize_path_string,
    path_normalization_warnings,
)
from .path_identity import (
    CANONICAL_PATH_REF_KNOWN_FIELDS,
    PATH_IDENTITY_KNOWN_FIELDS,
    PATH_IDENTITY_SCHEMA_VERSION,
    PATH_IDENTITY_TASK_ID,
    PATH_REF_KNOWN_FIELDS,
    CanonicalPathRef,
    CanonicalizationStatus,
    PathIdentity,
    PathKind,
    PathRef,
    PathSensitivity,
    build_path_identity,
)
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
    "CANONICAL_PATH_REF_KNOWN_FIELDS",
    "PATH_GOVERNANCE_MODULE_NAME",
    "PATH_GOVERNANCE_MODULE_VERSION",
    "PATH_GOVERNANCE_TASK_ID",
    "PATH_GOVERNANCE_UNAVAILABLE_REASONS",
    "PATH_IDENTITY_KNOWN_FIELDS",
    "PATH_IDENTITY_SCHEMA_VERSION",
    "PATH_IDENTITY_TASK_ID",
    "PATH_REF_KNOWN_FIELDS",
    "TRAVERSAL_WARNING",
    "CanonicalPathRef",
    "CanonicalizationStatus",
    "PathGovernanceCapabilityStatus",
    "PathGovernanceError",
    "PathGovernanceErrorCode",
    "PathGovernanceSerializationError",
    "PathGovernanceStructuredError",
    "PathGovernanceUnknownFieldError",
    "PathGovernanceValidationError",
    "PathIdentity",
    "PathKind",
    "PathRef",
    "PathSensitivity",
    "ProjectionSourceLabel",
    "SourceTrustLabel",
    "build_path_identity",
    "get_path_governance_foundation_status",
    "normalize_path_string",
    "path_normalization_warnings",
    "stable_hash",
    "to_canonical_dict",
    "to_canonical_json",
    "validate_known_fields",
]
