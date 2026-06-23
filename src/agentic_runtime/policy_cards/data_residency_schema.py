"""Data Residency Policy Card Schema v1 (P1.6.5).

Centralized schema contract for DataResidencyPolicyCard. This module defines the
legal closed-world shape, dangerous field/key sets, schema versioning, default
strict data residency rules, and required/critical data class lists.
"""
from __future__ import annotations

from typing import Any

from .data_residency import (
    DataClass,
    DataResidencyValidationIssue,
    DataResidencyValidationResult,
)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSION: str = "1.0"

SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

DATA_RESIDENCY_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "residency_rules",
)

DATA_RESIDENCY_OPTIONAL_FIELDS: tuple[str, ...] = (
    "default_zone",
    "metadata",
)

DATA_RESIDENCY_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "grant_authority",
    "bypass_policy",
    "policy_bypass",
    "bypass_residency",
    "bypass_egress_guard",
    "externalize_memory",
    "externalize_trace",
    "disable_policy",
    "skip_policy",
    "skip_trace",
    "skip_evidence",
    "operator_not_required",
    "operator_override",
    "egress_override",
    "egress_override_backdoor",
    "data_class_override",
    "residency_override",
    "runtime_resolver",
    "enforcement",
    "runtime_enforcement",
    "conflict_detector",
    "simulation_mode",
    "trace_hook",
    "unrestricted",
    "report_generator",
})

DATA_RESIDENCY_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "residency_rules",
    "default_zone",
    "metadata",
)

# ---------------------------------------------------------------------------
# Sub-object required/optional field tuples
# ---------------------------------------------------------------------------

DATA_RESIDENCY_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "data_class",
    "residency_zone",
)

DATA_RESIDENCY_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "allowed_processing_locations",
    "egress_rule",
    "redaction_requirements",
    "storage_requirements",
    "exposure_rule",
    "description",
)

DATA_EGRESS_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "egress_allowed",
)

DATA_EGRESS_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "requires_redaction",
    "requires_operator_approval",
    "requires_encryption",
    "requires_audit_trace",
    "allowed_destinations",
    "forbidden_destinations",
)

DATA_EXPOSURE_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "local_model_allowed",
    "external_model_allowed",
    "tool_access_allowed",
    "web_search_allowed",
    "artifact_export_allowed",
    "memory_write_allowed",
    "external_api_allowed",
    "human_review_required",
)

REDACTION_REQUIREMENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "requirement_type",
    "required",
    "description",
)

STORAGE_REQUIREMENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "requirement_type",
    "required",
    "ttl_seconds",
    "description",
)

# ---------------------------------------------------------------------------
# Dangerous fields and metadata keys
# ---------------------------------------------------------------------------

DATA_RESIDENCY_DANGEROUS_FIELD_NAMES: frozenset[str] = DATA_RESIDENCY_FORBIDDEN_FIELDS

DATA_RESIDENCY_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "allow_secret_egress",
    "allow_credential_egress",
    "local_only_bypass",
    "bypass_residency",
    "bypass_egress_guard",
    "externalize_memory",
    "externalize_trace",
    "external_model_override",
    "operator_not_required",
    "skip_redaction",
    "skip_encryption",
    "skip_audit",
    "silent_egress_allowed",
    "data_class_override",
    "residency_override",
    "egress_override",
    "unrestricted",
})

# ---------------------------------------------------------------------------
# Required and strict data classes
# ---------------------------------------------------------------------------

REQUIRED_DATA_CLASSES: tuple[DataClass, ...] = (
    DataClass.CREDENTIALS,
    DataClass.OPERATOR_PRIVATE,
    DataClass.PERSONAL_DATA,
    DataClass.SENSITIVE_PERSONAL_DATA,
    DataClass.BUSINESS_CONFIDENTIAL,
    DataClass.FINANCIAL,
    DataClass.SOURCE_CODE,
    DataClass.MEMORY_RECORD,
    DataClass.TRACE_RECORD,
    DataClass.PUBLIC,
)

STRICT_LOCAL_ONLY_DATA_CLASSES: tuple[DataClass, ...] = (
    DataClass.CREDENTIALS,
    DataClass.OPERATOR_PRIVATE,
    DataClass.SENSITIVE_PERSONAL_DATA,
    DataClass.MEMORY_RECORD,
    DataClass.TRACE_RECORD,
    DataClass.SOURCE_CODE,
)

# ---------------------------------------------------------------------------
# Schema export
# ---------------------------------------------------------------------------


def export_data_residency_policy_schema() -> dict[str, Any]:
    return {
        "schema_version": DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS),
        "required_fields": list(DATA_RESIDENCY_REQUIRED_FIELDS),
        "optional_fields": list(DATA_RESIDENCY_OPTIONAL_FIELDS),
        "forbidden_fields": sorted(DATA_RESIDENCY_FORBIDDEN_FIELDS),
        "canonical_fields": list(DATA_RESIDENCY_CANONICAL_FIELDS),
        "rule_required_fields": list(DATA_RESIDENCY_RULE_REQUIRED_FIELDS),
        "rule_optional_fields": list(DATA_RESIDENCY_RULE_OPTIONAL_FIELDS),
        "egress_rule_required_fields": list(DATA_EGRESS_RULE_REQUIRED_FIELDS),
        "egress_rule_optional_fields": list(DATA_EGRESS_RULE_OPTIONAL_FIELDS),
        "exposure_rule_required_fields": list(DATA_EXPOSURE_RULE_REQUIRED_FIELDS),
        "redaction_requirement_required_fields": list(REDACTION_REQUIREMENT_REQUIRED_FIELDS),
        "storage_requirement_required_fields": list(STORAGE_REQUIREMENT_REQUIRED_FIELDS),
        "dangerous_field_names": sorted(DATA_RESIDENCY_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(DATA_RESIDENCY_DANGEROUS_METADATA_KEYS),
        "required_data_classes": [dc.value for dc in REQUIRED_DATA_CLASSES],
        "strict_local_only_data_classes": [dc.value for dc in STRICT_LOCAL_ONLY_DATA_CLASSES],
    }


def get_data_residency_policy_schema() -> dict[str, Any]:
    return export_data_residency_policy_schema()


def is_supported_data_residency_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS


def validate_data_residency_policy_schema_version(
    version: object,
) -> DataResidencyValidationResult:
    errors: list[DataResidencyValidationIssue] = []
    warnings: list[DataResidencyValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            DataResidencyValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            DataResidencyValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_DATA_RESIDENCY_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return DataResidencyValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
