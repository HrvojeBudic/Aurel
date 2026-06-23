"""Sandbox Policy Card Schema v1 (P1.6.9).

Centralized schema contract for SandboxPolicyCard. This module defines the
legal closed-world shape, dangerous field/key sets, schema versioning, and
schema export functions. Default runtime objects live in sandbox.py.

Import note: to avoid circular imports, this module does NOT import from
.sandbox at module level. Schema export helpers import on demand.
"""
from __future__ import annotations

from typing import Any

from .risk_tiers import RiskTier


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

SANDBOX_POLICY_CARD_SCHEMA_VERSION: str = "1.0"

SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

# ---------------------------------------------------------------------------
# Required fields — must be present
# ---------------------------------------------------------------------------

SANDBOX_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
)

SANDBOX_OPTIONAL_FIELDS: tuple[str, ...] = (
    "backend_rules",
    "filesystem_rules",
    "egress_rules",
    "command_rules",
    "risk_tier_mappings",
    "approval_policy",
    "metadata",
)

SANDBOX_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "grant_authority",
    "bypass_policy",
    "policy_bypass",
    "disable_policy",
    "skip_policy",
    "skip_trace",
    "skip_evidence",
    "runtime_enforcement",
    "runtime",
    "enforce",
    "block_execution",
    "execute",
    "executor",
    "sandbox_engine",
    "docker_backend",
    "bubblewrap_backend",
    "unsafe_override",
    "risk_override",
    "unrestricted",
    "allow_all",
    "any_backend",
    "any_filesystem",
    "any_egress",
    "any_command",
})

SANDBOX_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "backend_rules",
    "filesystem_rules",
    "egress_rules",
    "command_rules",
    "risk_tier_mappings",
    "approval_policy",
    "metadata",
)

# ---------------------------------------------------------------------------
# Sub-object required fields
# ---------------------------------------------------------------------------

SANDBOX_BACKEND_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "rule_id",
)

SANDBOX_BACKEND_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "allowed_backends",
    "denied_backends",
    "minimum_posture",
    "description",
)

SANDBOX_FILESYSTEM_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "rule_id",
)

SANDBOX_FILESYSTEM_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "scope",
    "allowed_paths",
    "denied_paths",
    "allowlist_paths",
    "description",
)

SANDBOX_EGRESS_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "rule_id",
)

SANDBOX_EGRESS_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "egress_policy",
    "allowed_targets",
    "denied_targets",
    "description",
)

SANDBOX_COMMAND_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "rule_id",
    "command_class",
)

SANDBOX_COMMAND_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "decision",
    "required_egress_policy",
    "required_backend",
    "risk_ceiling",
    "required_oversight",
    "description",
)

SANDBOX_RISK_TIER_MAPPING_REQUIRED_FIELDS: tuple[str, ...] = (
    "risk_tier",
    "minimum_backend",
)

SANDBOX_RISK_TIER_MAPPING_OPTIONAL_FIELDS: tuple[str, ...] = (
    "minimum_filesystem_scope",
    "minimum_egress_policy",
    "requires_approval",
    "requires_isolated_backend",
    "description",
)

# ---------------------------------------------------------------------------
# Dangerous fields and metadata keys
# ---------------------------------------------------------------------------

SANDBOX_DANGEROUS_FIELD_NAMES: frozenset[str] = SANDBOX_FORBIDDEN_FIELDS

SANDBOX_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "auto_approve",
    "skip_approval",
    "skip_confirmation",
    "bypass_policy",
    "bypass_sandbox",
    "silent_approval",
    "approval_grant",
    "authority_grant",
    "grant_authority",
    "authority",
    "risk_override",
    "risk override",
    "disable_trace",
    "skip_evidence",
    "skip_trace",
    "trace_bypass",
    "evidence_bypass",
    "unsafe_override",
    "unrestricted",
    "allow_all",
    "any_backend",
    "any_filesystem",
    "any_egress",
})

# ---------------------------------------------------------------------------
# Required risk tiers for sandbox mappings
# ---------------------------------------------------------------------------

REQUIRED_SANDBOX_RISK_TIERS: tuple[RiskTier, ...] = (
    RiskTier.R0,
    RiskTier.R1,
    RiskTier.R2,
    RiskTier.R3,
    RiskTier.R4,
    RiskTier.R5,
    RiskTier.R6,
)

# ---------------------------------------------------------------------------
# Schema export functions
# ---------------------------------------------------------------------------


def _backend_rule_to_dict(rule: object) -> dict[str, Any]:
    """Export a SandboxBackendRule to dict form (lazy import)."""
    from .sandbox import SandboxBackendRule  # noqa: PLC0415
    assert isinstance(rule, SandboxBackendRule)
    result: dict[str, Any] = {
        "rule_id": rule.rule_id,
        "description": rule.description,
    }
    if rule.allowed_backends:
        result["allowed_backends"] = [b.value for b in rule.allowed_backends]
    if rule.denied_backends:
        result["denied_backends"] = [b.value for b in rule.denied_backends]
    if rule.minimum_posture is not None:
        result["minimum_posture"] = rule.minimum_posture.value
    return result


def _filesystem_rule_to_dict(rule: object) -> dict[str, Any]:
    from .sandbox import SandboxFilesystemScopeRule  # noqa: PLC0415
    assert isinstance(rule, SandboxFilesystemScopeRule)
    result: dict[str, Any] = {
        "rule_id": rule.rule_id,
        "description": rule.description,
    }
    if rule.scope is not None:
        result["scope"] = rule.scope.value
    if rule.allowed_paths:
        result["allowed_paths"] = list(rule.allowed_paths)
    if rule.denied_paths:
        result["denied_paths"] = list(rule.denied_paths)
    if rule.allowlist_paths:
        result["allowlist_paths"] = list(rule.allowlist_paths)
    return result


def _egress_rule_to_dict(rule: object) -> dict[str, Any]:
    from .sandbox import SandboxEgressRule  # noqa: PLC0415
    assert isinstance(rule, SandboxEgressRule)
    result: dict[str, Any] = {
        "rule_id": rule.rule_id,
        "description": rule.description,
    }
    if rule.egress_policy is not None:
        result["egress_policy"] = rule.egress_policy.value
    if rule.allowed_targets:
        result["allowed_targets"] = list(rule.allowed_targets)
    if rule.denied_targets:
        result["denied_targets"] = list(rule.denied_targets)
    return result


def _command_rule_to_dict(rule: object) -> dict[str, Any]:
    from .sandbox import SandboxCommandClassRule  # noqa: PLC0415
    assert isinstance(rule, SandboxCommandClassRule)
    result: dict[str, Any] = {
        "rule_id": rule.rule_id,
        "command_class": rule.command_class.value,
        "decision": rule.decision.value,
        "description": rule.description,
    }
    if rule.required_egress_policy is not None:
        result["required_egress_policy"] = rule.required_egress_policy.value
    if rule.required_backend is not None:
        result["required_backend"] = rule.required_backend.value
    if rule.risk_ceiling is not None:
        result["risk_ceiling"] = rule.risk_ceiling
    if rule.required_oversight is not None:
        result["required_oversight"] = rule.required_oversight
    return result


def _risk_tier_mapping_to_dict(mapping: object) -> dict[str, Any]:
    from .sandbox import RiskTierSandboxMapping  # noqa: PLC0415
    assert isinstance(mapping, RiskTierSandboxMapping)
    result: dict[str, Any] = {
        "description": mapping.description,
        "minimum_backend": mapping.minimum_backend.value,
        "minimum_filesystem_scope": mapping.minimum_filesystem_scope.value,
        "minimum_egress_policy": mapping.minimum_egress_policy.value,
        "requires_approval": mapping.requires_approval,
        "requires_isolated_backend": mapping.requires_isolated_backend,
        "risk_tier": mapping.risk_tier.value,
    }
    return result


def export_sandbox_policy_schema() -> dict[str, Any]:
    from .sandbox import (  # noqa: PLC0415
        DEFAULT_APPROVAL_REQUIREMENTS,
        DEFAULT_BACKEND_RULES,
        DEFAULT_COMMAND_RULES,
        DEFAULT_EGRESS_RULES,
        DEFAULT_FILESYSTEM_RULES,
        DEFAULT_RISK_TIER_SANDBOX_MAPPINGS,
    )

    return {
        "canonical_fields": list(SANDBOX_CANONICAL_FIELDS),
        "dangerous_field_names": sorted(SANDBOX_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(SANDBOX_DANGEROUS_METADATA_KEYS),
        "default_approval_requirements": sorted(
            [a.value for a in DEFAULT_APPROVAL_REQUIREMENTS]
        ),
        "default_backend_rules": [
            _backend_rule_to_dict(r) for r in DEFAULT_BACKEND_RULES
        ],
        "default_command_rules": [
            _command_rule_to_dict(r) for r in sorted(
                DEFAULT_COMMAND_RULES, key=lambda item: item.command_class.value,
            )
        ],
        "default_egress_rules": [
            _egress_rule_to_dict(r) for r in DEFAULT_EGRESS_RULES
        ],
        "default_filesystem_rules": [
            _filesystem_rule_to_dict(r) for r in DEFAULT_FILESYSTEM_RULES
        ],
        "default_risk_tier_sandbox_mappings": [
            _risk_tier_mapping_to_dict(m) for m in sorted(
                DEFAULT_RISK_TIER_SANDBOX_MAPPINGS,
                key=lambda item: item.risk_tier.value,
            )
        ],
        "forbidden_fields": sorted(SANDBOX_FORBIDDEN_FIELDS),
        "optional_fields": list(SANDBOX_OPTIONAL_FIELDS),
        "required_fields": list(SANDBOX_REQUIRED_FIELDS),
        "required_tiers": [tier.value for tier in REQUIRED_SANDBOX_RISK_TIERS],
        "sandbox_backend_rule_required_fields": list(SANDBOX_BACKEND_RULE_REQUIRED_FIELDS),
        "sandbox_command_rule_required_fields": list(SANDBOX_COMMAND_RULE_REQUIRED_FIELDS),
        "sandbox_egress_rule_required_fields": list(SANDBOX_EGRESS_RULE_REQUIRED_FIELDS),
        "sandbox_filesystem_rule_required_fields": list(SANDBOX_FILESYSTEM_RULE_REQUIRED_FIELDS),
        "sandbox_risk_tier_mapping_required_fields": list(SANDBOX_RISK_TIER_MAPPING_REQUIRED_FIELDS),
        "schema_version": SANDBOX_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS),
    }


def get_sandbox_policy_schema() -> dict[str, Any]:
    return export_sandbox_policy_schema()


def is_supported_sandbox_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS


def validate_sandbox_policy_schema_version(
    version: object,
) -> object:
    from .sandbox import SandboxValidationIssue, SandboxValidationResult  # noqa: PLC0415

    errors: list[SandboxValidationIssue] = []
    warnings: list[SandboxValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            SandboxValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            SandboxValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_SANDBOX_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return SandboxValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
