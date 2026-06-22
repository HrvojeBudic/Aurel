"""Behavioral Contract Schema v1 (P1.6.2).

Explicit, centralized, inspectable schema contract defining the legal shape
of every behavioral contract. All field classifications, forbidden fields,
dangerous metadata keys, and schema versioning originate here.

Architectural law:
  - Schema is the source of truth for contract validation.
  - Required/optional/forbidden/canonical fields must be centralized.
  - Metadata must remain descriptive only.
  - Behavioral contracts do not grant authority.
  - Runtime enforcement is not implemented in P1.6.2.
"""
from __future__ import annotations

from typing import Any

from .contracts import (
    BehavioralContractValidationIssue,
    BehavioralContractValidationResult,
)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

BEHAVIORAL_CONTRACT_SCHEMA_VERSION: str = "1.0"
SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)


# ---------------------------------------------------------------------------
# Field classifications
# ---------------------------------------------------------------------------

BEHAVIORAL_CONTRACT_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "identity",
    "status",
    "subject",
    "scope",
    "policy_card_refs",
    "obligations",
    "prohibitions",
    "preconditions",
    "postconditions",
    "evidence_requirements",
    "escalation_rules",
)

BEHAVIORAL_CONTRACT_OPTIONAL_FIELDS: tuple[str, ...] = (
    "source",
    "metadata",
)

BEHAVIORAL_CONTRACT_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "grant_authority",
    "permission_grant",
    "permissions_granted",
    "bypass_policy",
    "policy_bypass",
    "disable_policy",
    "skip_policy",
    "skip_trace",
    "skip_evidence",
    "ignore_evidence",
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
    "unrestricted",
    "execute_anyway",
    "ignore_contract",
    "disable_contract",
})

BEHAVIORAL_CONTRACT_CANONICAL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "identity",
    "status",
    "subject",
    "scope",
    "policy_card_refs",
    "obligations",
    "prohibitions",
    "preconditions",
    "postconditions",
    "evidence_requirements",
    "escalation_rules",
    "source",
    "metadata",
)

BEHAVIORAL_CONTRACT_CONTROL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "status",
)

BEHAVIORAL_CONTRACT_IDENTITY_FIELDS: tuple[str, ...] = (
    "contract_id",
    "slug",
    "name",
    "version",
    "namespace",
)

BEHAVIORAL_CONTRACT_SUBJECT_FIELDS: tuple[str, ...] = (
    "subject_type",
    "subject_id",
    "applies_to",
)

BEHAVIORAL_CONTRACT_BEHAVIOR_FIELDS: tuple[str, ...] = (
    "obligations",
    "prohibitions",
    "preconditions",
    "postconditions",
)

BEHAVIORAL_CONTRACT_EVIDENCE_FIELDS: tuple[str, ...] = (
    "evidence_requirements",
    "escalation_rules",
)

BEHAVIORAL_CONTRACT_SOURCE_FIELDS: tuple[str, ...] = (
    "source",
)

BEHAVIORAL_CONTRACT_DESCRIPTIVE_FIELDS: tuple[str, ...] = (
    "metadata",
)

BEHAVIORAL_CONTRACT_RUNTIME_FUTURE_FIELDS: frozenset[str] = frozenset({
    "runtime_enforcement",
    "resolver",
    "enforcement",
    "priority",
    "conditions",
    "effects",
    "actions",
    "enforcer",
})

BEHAVIORAL_CONTRACT_DANGEROUS_FIELD_NAMES: frozenset[str] = (
    BEHAVIORAL_CONTRACT_FORBIDDEN_FIELDS
)

BEHAVIORAL_CONTRACT_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
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
    "contract_bypass",
    "runtime_enforcement",
    "unrestricted",
})


# ---------------------------------------------------------------------------
# Schema export
# ---------------------------------------------------------------------------

def export_behavioral_contract_schema() -> dict[str, Any]:
    return {
        "schema_version": BEHAVIORAL_CONTRACT_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS),
        "required_fields": list(BEHAVIORAL_CONTRACT_REQUIRED_FIELDS),
        "optional_fields": list(BEHAVIORAL_CONTRACT_OPTIONAL_FIELDS),
        "forbidden_fields": sorted(BEHAVIORAL_CONTRACT_FORBIDDEN_FIELDS),
        "canonical_fields": list(BEHAVIORAL_CONTRACT_CANONICAL_FIELDS),
        "field_categories": {
            "control": list(BEHAVIORAL_CONTRACT_CONTROL_FIELDS),
            "identity": list(BEHAVIORAL_CONTRACT_IDENTITY_FIELDS),
            "subject": list(BEHAVIORAL_CONTRACT_SUBJECT_FIELDS),
            "behavior": list(BEHAVIORAL_CONTRACT_BEHAVIOR_FIELDS),
            "evidence": list(BEHAVIORAL_CONTRACT_EVIDENCE_FIELDS),
            "source": list(BEHAVIORAL_CONTRACT_SOURCE_FIELDS),
            "descriptive": list(BEHAVIORAL_CONTRACT_DESCRIPTIVE_FIELDS),
            "runtime_future": sorted(BEHAVIORAL_CONTRACT_RUNTIME_FUTURE_FIELDS),
        },
        "dangerous_metadata_keys": sorted(BEHAVIORAL_CONTRACT_DANGEROUS_METADATA_KEYS),
    }


def get_behavioral_contract_schema() -> dict[str, Any]:
    return export_behavioral_contract_schema()


def is_supported_behavioral_contract_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS


def validate_behavioral_contract_schema_version(
    version: object,
) -> BehavioralContractValidationResult:
    errors: list[BehavioralContractValidationIssue] = []
    warnings: list[BehavioralContractValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(BehavioralContractValidationIssue(
            code="MISSING_SCHEMA_VERSION",
            message=f"schema_version is required and must be one of: "
                     f"{', '.join(SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS)}",
            field="schema_version",
            severity="error",
        ))
    elif version not in SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS:
        errors.append(BehavioralContractValidationIssue(
            code="UNSUPPORTED_SCHEMA_VERSION",
            message=f"schema_version '{version}' is not supported; "
                     f"supported: {', '.join(SUPPORTED_BEHAVIORAL_CONTRACT_SCHEMA_VERSIONS)}",
            field="schema_version",
            severity="error",
        ))

    return BehavioralContractValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
