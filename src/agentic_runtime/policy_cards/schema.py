"""Policy Card Schema v1 (P1.6.1).

Explicit, centralized, inspectable schema contract defining the legal shape
of every policy card. All field classifications, forbidden fields, dangerous
metadata keys, and schema versioning originate here — the single source of
truth for policy card validation and export.

Architectural law:
  - Schema is the source of truth for validation.
  - Required/optional/forbidden/canonical fields must be centralized.
  - Metadata must remain descriptive only.
  - Runtime resolver fields are reserved but not accepted yet.
"""
from __future__ import annotations

from typing import Any

from .models import (
    PolicyCardValidationIssue,
    PolicyCardValidationResult,
)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

POLICY_CARD_SCHEMA_VERSION: str = "1.0"
"""Current canonical schema version. All valid policy cards must declare this."""

SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)
"""All schema versions that pass validation. Unlisted versions fail."""


# ---------------------------------------------------------------------------
# Required fields — must be present, must not be empty/null
# ---------------------------------------------------------------------------

POLICY_CARD_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "identity",
    "kind",
    "status",
    "scope",
    "description",
)

POLICY_CARD_IDENTITY_REQUIRED_FIELDS: tuple[str, ...] = (
    "card_id",
    "slug",
    "name",
    "version",
    "namespace",
)

POLICY_CARD_SCOPE_REQUIRED_FIELDS: tuple[str, ...] = (
    "scope_type",
)


# ---------------------------------------------------------------------------
# Optional fields — may be present, must validate shape when present
# ---------------------------------------------------------------------------

POLICY_CARD_OPTIONAL_FIELDS: tuple[str, ...] = (
    "risk_binding",
    "authority_binding",
    "source",
    "metadata",
)


# ---------------------------------------------------------------------------
# Forbidden top-level fields — any field that implies authority grant,
# policy bypass, safety override, or governance circumvention.
# ---------------------------------------------------------------------------

POLICY_CARD_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "shadow_authority_grant",
    "authority_grant",
    "grant_authority",
    "bypass_policy",
    "policy_bypass",
    "disable_policy",
    "skip_policy",
    "skip_trace",
    "skip_evidence",
    "allow_untrusted_write",
    "allow_secret_access",
    "disable_oversight",
    "operator_not_required",
    "operator_override",
    "silent_egress_allowed",
    "memory_write_allowed",
    "tool_write_allowed",
    "sandbox_override",
    "model_override",
    "risk_override",
    "permission_grant",
    "permissions_granted",
    "unrestricted",
})


# ---------------------------------------------------------------------------
# Canonical fields — fields that participate in canonical serialization/hash.
# Excludes raw_source_hash (raw transport artifact, not logical content).
# ---------------------------------------------------------------------------

POLICY_CARD_CANONICAL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "identity",
    "kind",
    "status",
    "scope",
    "description",
    "risk_binding",
    "authority_binding",
    "source",
    "metadata",
)


# ---------------------------------------------------------------------------
# Field categories — for schema inspection and documentation
# ---------------------------------------------------------------------------

POLICY_CARD_CONTROL_FIELDS: tuple[str, ...] = (
    "kind",
    "status",
    "scope",
    "schema_version",
)
"""Fields that affect card classification and lifecycle."""

POLICY_CARD_GOVERNANCE_FIELDS: tuple[str, ...] = (
    "risk_binding",
    "authority_binding",
)
"""Fields that will later affect policy/risk/authority decisions."""

POLICY_CARD_SOURCE_FIELDS: tuple[str, ...] = (
    "source",
)
"""Fields used for source/attestation readiness."""

POLICY_CARD_DESCRIPTIVE_FIELDS: tuple[str, ...] = (
    "description",
    "metadata",
)
"""Fields that describe but must not control authority."""

POLICY_CARD_RUNTIME_FUTURE_FIELDS: frozenset[str] = frozenset({
    "resolver",
    "resolution",
    "enforcement",
    "priority",
    "conditions",
    "effects",
    "actions",
})
"""Fields reserved for future runtime resolver — NOT accepted in P1.6.1 input."""

POLICY_CARD_IDENTITY_FIELDS: tuple[str, ...] = (
    "card_id",
    "slug",
    "name",
    "version",
    "namespace",
)
"""Fields that constitute the stable identity of a policy card."""


# ---------------------------------------------------------------------------
# Dangerous metadata keys — metadata must remain descriptive only.
# Any key implying authority, permission, bypass, or override is rejected.
# ---------------------------------------------------------------------------

POLICY_CARD_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "authority",
    "authority_grant",
    "grant_authority",
    "permissions",
    "permission_grant",
    "risk_override",
    "risk override",
    "egress",
    "memory_write",
    "memory write",
    "tool_write",
    "tool write",
    "sandbox_override",
    "sandbox override",
    "model_override",
    "model override",
    "operator_override",
    "operator override",
    "operator_not_required",
    "policy_bypass",
    "policy bypass",
    "bypass_policy",
    "trace_bypass",
    "trace bypass",
    "evidence_bypass",
    "delegation_grant",
    "secret_access",
    "network_access",
    "unrestricted",
})


# ---------------------------------------------------------------------------
# Combined known fields — all fields that may legitimately appear at top level
# ---------------------------------------------------------------------------

def _all_known_top_level_fields() -> frozenset[str]:
    """Union of required + optional fields that are valid top-level keys."""
    return frozenset(POLICY_CARD_REQUIRED_FIELDS + POLICY_CARD_OPTIONAL_FIELDS)


ALL_KNOWN_TOP_LEVEL_FIELDS: frozenset[str] = _all_known_top_level_fields()
"""All top-level fields accepted by the schema (required + optional)."""


# ---------------------------------------------------------------------------
# Schema export
# ---------------------------------------------------------------------------


def export_policy_card_schema() -> dict[str, Any]:
    """Export the full Policy Card Schema v1 as a deterministic dictionary.

    Returns a stable, inspectable dict with all schema constants, field
    classifications, and metadata. Suitable for CLI, docs, reports, and
    programmatic inspection.

    Output is deterministic: no runtime object addresses, no non-deterministic
    timestamps, keys are sorted.
    """
    return {
        "schema_version": POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS),
        "required_fields": list(POLICY_CARD_REQUIRED_FIELDS),
        "optional_fields": list(POLICY_CARD_OPTIONAL_FIELDS),
        "forbidden_fields": sorted(POLICY_CARD_FORBIDDEN_FIELDS),
        "canonical_fields": list(POLICY_CARD_CANONICAL_FIELDS),
        "field_categories": {
            "control": list(POLICY_CARD_CONTROL_FIELDS),
            "governance": list(POLICY_CARD_GOVERNANCE_FIELDS),
            "source": list(POLICY_CARD_SOURCE_FIELDS),
            "descriptive": list(POLICY_CARD_DESCRIPTIVE_FIELDS),
            "identity": list(POLICY_CARD_IDENTITY_FIELDS),
            "runtime_future": sorted(POLICY_CARD_RUNTIME_FUTURE_FIELDS),
        },
        "dangerous_metadata_keys": sorted(POLICY_CARD_DANGEROUS_METADATA_KEYS),
    }


def get_policy_card_schema() -> dict[str, Any]:
    """Alias for export_policy_card_schema()."""
    return export_policy_card_schema()


# ---------------------------------------------------------------------------
# Schema version helpers
# ---------------------------------------------------------------------------


def is_supported_policy_card_schema_version(version: str) -> bool:
    """Return True if the given schema version is supported."""
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS


def validate_policy_card_schema_version(
    version: object,
) -> PolicyCardValidationResult:
    """Validate a schema version string against supported versions.

    Returns a structured validation result. Use is_supported_* for a simple
    boolean check.
    """
    errors: list[PolicyCardValidationIssue] = []
    warnings: list[PolicyCardValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(PolicyCardValidationIssue(
            code="MISSING_SCHEMA_VERSION",
            message=f"schema_version is required and must be one of: "
                     f"{', '.join(SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS)}",
            field="schema_version",
            severity="error",
        ))
    elif version not in SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(PolicyCardValidationIssue(
            code="UNSUPPORTED_SCHEMA_VERSION",
            message=f"schema_version '{version}' is not supported; "
                     f"supported: {', '.join(SUPPORTED_POLICY_CARD_SCHEMA_VERSIONS)}",
            field="schema_version",
            severity="error",
        ))

    return PolicyCardValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
