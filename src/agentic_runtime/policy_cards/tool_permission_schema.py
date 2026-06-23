"""Tool Permission Policy Card Schema v1 (P1.6.6).

Centralized schema contract for ToolPermissionPolicyCard. Defines the legal
closed-world shape, dangerous field/key sets, schema versioning, default
deny-by-default rules, and required vocabulary constants.
"""
from __future__ import annotations

from typing import Any

from .tool_permissions import (
    ToolPermissionValidationIssue,
    ToolPermissionValidationResult,
)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSION: str = "1.0"

SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

# ---------------------------------------------------------------------------
# Top-level field classification
# ---------------------------------------------------------------------------

TOOL_PERMISSION_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "permission_rules",
)

TOOL_PERMISSION_OPTIONAL_FIELDS: tuple[str, ...] = (
    "default_decision",
    "metadata",
)

TOOL_PERMISSION_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "tool_gateway",
    "runtime_enforcement",
    "enforcement",
    "bypass_policy",
    "bypass_tool_policy",
    "skip_policy",
    "policy_bypass",
    "disable_policy",
    "registry_resolver",
    "sandbox_execution",
    "network_blocking",
    "filesystem_enforcement",
    "path_enforcement",
    "memory_enforcement",
    "model_router",
    "runtime_resolver",
    "conflict_detector",
    "simulation_mode",
    "trace_hook",
    "unrestricted",
    "report_generator",
    "tool_override_backdoor",
})

TOOL_PERMISSION_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "permission_rules",
    "default_decision",
    "metadata",
)

# ---------------------------------------------------------------------------
# Sub-object field classification
# ---------------------------------------------------------------------------

TOOL_PERMISSION_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "matcher",
    "permission_type",
    "decision",
)

TOOL_PERMISSION_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "risk_ceiling",
    "required_oversight",
    "allowed_data_classes",
    "forbidden_data_classes",
    "allowed_scopes",
    "conditions",
    "sandbox_required",
    "trace_required",
    "evidence_required",
    "description",
)

TOOL_IDENTITY_MATCHER_REQUIRED_FIELDS: tuple[str, ...] = (
    "match_mode",
)

TOOL_IDENTITY_MATCHER_OPTIONAL_FIELDS: tuple[str, ...] = (
    "tool_name",
    "tool_id",
    "tool_category",
    "provider",
    "namespace",
)

TOOL_PERMISSION_CONDITION_REQUIRED_FIELDS: tuple[str, ...] = (
    "condition_type",
)

TOOL_PERMISSION_CONDITION_OPTIONAL_FIELDS: tuple[str, ...] = (
    "value",
    "description",
)

# ---------------------------------------------------------------------------
# Dangerous fields and metadata keys
# ---------------------------------------------------------------------------

TOOL_PERMISSION_DANGEROUS_FIELD_NAMES: frozenset[str] = TOOL_PERMISSION_FORBIDDEN_FIELDS

TOOL_PERMISSION_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "allow_all_tools",
    "allow_any_tool",
    "bypass_tool_policy",
    "skip_tool_policy",
    "tool_policy_bypass",
    "unrestricted_tool_access",
    "credential_access_allowed",
    "network_unrestricted",
    "shell_unrestricted",
    "external_egress_allowed",
    "filesystem_unrestricted",
    "memory_write_unrestricted",
    "operator_not_required",
    "skip_approval",
    "skip_sandbox",
    "skip_trace",
    "skip_evidence",
})

# ---------------------------------------------------------------------------
# Default rule constants
# ---------------------------------------------------------------------------

DANGEROUS_TOOL_PERMISSION_TYPES: frozenset[str] = frozenset({
    "credential_access",
    "shell_command",
    "execute",
    "delete",
    "network",
    "external_egress",
    "memory_write",
    "configuration_write",
    "database_write",
    "email_send",
    "github_write",
    "artifact_export",
})

HIGH_RISK_TOOL_PERMISSION_TYPES: frozenset[str] = frozenset({
    "credential_access",
    "shell_command",
    "delete",
    "external_egress",
    "configuration_write",
    "email_send",
})

DEFAULT_DENY_TOOL_CATEGORIES: frozenset[str] = frozenset({
    "unknown",
})

SAFE_CONDITION_TYPES: frozenset[str] = frozenset({
    "risk_at_or_below",
    "requires_approval",
    "requires_explicit_confirmation",
    "requires_sandbox",
    "requires_trace",
    "requires_evidence",
    "data_class_allowed",
    "residency_zone_allowed",
    "local_only",
    "path_scope_limited",
    "network_disabled",
    "external_egress_denied",
    "operator_required",
})

# ---------------------------------------------------------------------------
# Schema export
# ---------------------------------------------------------------------------


def export_tool_permission_policy_schema() -> dict[str, Any]:
    return {
        "schema_version": TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS),
        "required_fields": list(TOOL_PERMISSION_REQUIRED_FIELDS),
        "optional_fields": list(TOOL_PERMISSION_OPTIONAL_FIELDS),
        "forbidden_fields": sorted(TOOL_PERMISSION_FORBIDDEN_FIELDS),
        "canonical_fields": list(TOOL_PERMISSION_CANONICAL_FIELDS),
        "rule_required_fields": list(TOOL_PERMISSION_RULE_REQUIRED_FIELDS),
        "rule_optional_fields": list(TOOL_PERMISSION_RULE_OPTIONAL_FIELDS),
        "matcher_required_fields": list(TOOL_IDENTITY_MATCHER_REQUIRED_FIELDS),
        "matcher_optional_fields": list(TOOL_IDENTITY_MATCHER_OPTIONAL_FIELDS),
        "condition_required_fields": list(TOOL_PERMISSION_CONDITION_REQUIRED_FIELDS),
        "dangerous_field_names": sorted(TOOL_PERMISSION_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(TOOL_PERMISSION_DANGEROUS_METADATA_KEYS),
        "dangerous_permission_types": sorted(DANGEROUS_TOOL_PERMISSION_TYPES),
        "high_risk_permission_types": sorted(HIGH_RISK_TOOL_PERMISSION_TYPES),
        "default_deny_categories": sorted(DEFAULT_DENY_TOOL_CATEGORIES),
    }


def get_tool_permission_policy_schema() -> dict[str, Any]:
    return export_tool_permission_policy_schema()


def is_supported_tool_permission_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS


def validate_tool_permission_policy_schema_version(
    version: object,
) -> ToolPermissionValidationResult:
    errors: list[ToolPermissionValidationIssue] = []
    warnings: list[ToolPermissionValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            ToolPermissionValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            ToolPermissionValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_TOOL_PERMISSION_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return ToolPermissionValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
