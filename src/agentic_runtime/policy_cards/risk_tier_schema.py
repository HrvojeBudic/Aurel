"""Risk Tier Policy Card Schema v1 (P1.6.3).

Centralized schema contract for RiskTierPolicyCard. This module defines the
legal closed-world shape, dangerous field/key sets, schema versioning, default
R0-R6 definitions, and default action-class mapping seeds.
"""
from __future__ import annotations

from typing import Any

from .risk_tiers import (
    EvidenceExpectation,
    OversightLevel,
    ReversibilityLevel,
    RiskActionClass,
    RiskActionClassMapping,
    RiskTier,
    RiskTierDefinition,
    RiskTierValidationIssue,
    RiskTierValidationResult,
)


RISK_TIER_POLICY_CARD_SCHEMA_VERSION: str = "1.0"
SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

REQUIRED_RISK_TIERS: tuple[RiskTier, ...] = (
    RiskTier.R0,
    RiskTier.R1,
    RiskTier.R2,
    RiskTier.R3,
    RiskTier.R4,
    RiskTier.R5,
    RiskTier.R6,
)

RISK_TIER_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "tiers",
)

RISK_TIER_OPTIONAL_FIELDS: tuple[str, ...] = (
    "action_class_mappings",
    "metadata",
)

RISK_TIER_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
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
    "operator_not_required",
    "operator_override",
    "allow_untrusted_write",
    "silent_egress_allowed",
    "memory_write_allowed",
    "tool_write_allowed",
    "sandbox_override",
    "model_override",
    "risk_override",
    "runtime_resolver",
    "risk_classifier",
    "automatic_classifier",
    "enforcement",
    "runtime_enforcement",
    "conflict_detector",
    "simulation_mode",
    "trace_hook",
    "unrestricted",
})

RISK_TIER_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "tiers",
    "action_class_mappings",
    "metadata",
)

RISK_TIER_DEFINITION_REQUIRED_FIELDS: tuple[str, ...] = (
    "tier",
    "label",
    "description",
    "reversibility",
    "oversight",
    "evidence_expectation",
    "default_requires_trace",
    "default_requires_evidence",
    "default_requires_approval",
    "default_requires_explicit_confirmation",
    "default_requires_sandbox",
    "default_allows_external_egress",
    "default_allows_memory_write",
    "default_allows_tool_write",
    "default_allows_execution",
)

RISK_TIER_ACTION_MAPPING_REQUIRED_FIELDS: tuple[str, ...] = (
    "action_class",
    "default_tier",
)

RISK_TIER_ACTION_MAPPING_OPTIONAL_FIELDS: tuple[str, ...] = (
    "description",
)

RISK_TIER_DANGEROUS_FIELD_NAMES: frozenset[str] = RISK_TIER_FORBIDDEN_FIELDS

RISK_TIER_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "risk_override",
    "risk override",
    "authority_grant",
    "grant_authority",
    "authority",
    "permissions",
    "permission_grant",
    "bypass_policy",
    "policy_bypass",
    "skip_trace",
    "trace_bypass",
    "skip_evidence",
    "evidence_bypass",
    "operator_not_required",
    "operator override",
    "operator_override",
    "allow_untrusted_write",
    "silent_egress_allowed",
    "memory_write",
    "memory write",
    "tool_write",
    "tool write",
    "sandbox_override",
    "model_override",
    "network_access",
    "secret_access",
    "runtime_enforcement",
    "risk_classifier",
    "unrestricted",
})


DEFAULT_RISK_TIER_DEFINITIONS: tuple[RiskTierDefinition, ...] = (
    RiskTierDefinition(
        tier=RiskTier.R0,
        label="Informational",
        description="No action or state consequence.",
        reversibility=ReversibilityLevel.NONE,
        oversight=OversightLevel.NONE,
        evidence_expectation=EvidenceExpectation.NONE,
        default_requires_trace=False,
        default_requires_evidence=False,
        default_requires_approval=False,
        default_requires_explicit_confirmation=False,
        default_requires_sandbox=False,
        default_allows_external_egress=False,
        default_allows_memory_write=False,
        default_allows_tool_write=False,
        default_allows_execution=False,
    ),
    RiskTierDefinition(
        tier=RiskTier.R1,
        label="Safe Local Read",
        description="Low consequence local read or inspection.",
        reversibility=ReversibilityLevel.READ_ONLY,
        oversight=OversightLevel.NONE,
        evidence_expectation=EvidenceExpectation.LIGHTWEIGHT_TRACE,
        default_requires_trace=True,
        default_requires_evidence=False,
        default_requires_approval=False,
        default_requires_explicit_confirmation=False,
        default_requires_sandbox=False,
        default_allows_external_egress=False,
        default_allows_memory_write=False,
        default_allows_tool_write=False,
        default_allows_execution=False,
    ),
    RiskTierDefinition(
        tier=RiskTier.R2,
        label="Reversible Local Write",
        description="Low-impact local write that is reversible.",
        reversibility=ReversibilityLevel.REVERSIBLE,
        oversight=OversightLevel.OPTIONAL,
        evidence_expectation=EvidenceExpectation.TRACE_SUMMARY,
        default_requires_trace=True,
        default_requires_evidence=False,
        default_requires_approval=False,
        default_requires_explicit_confirmation=False,
        default_requires_sandbox=False,
        default_allows_external_egress=False,
        default_allows_memory_write=False,
        default_allows_tool_write=True,
        default_allows_execution=False,
    ),
    RiskTierDefinition(
        tier=RiskTier.R3,
        label="Meaningful State Change",
        description="Moderate-impact state change requiring stronger trace/evidence.",
        reversibility=ReversibilityLevel.REVERSIBLE,
        oversight=OversightLevel.REVIEW_RECOMMENDED,
        evidence_expectation=EvidenceExpectation.TRACE_EVIDENCE_REF,
        default_requires_trace=True,
        default_requires_evidence=True,
        default_requires_approval=False,
        default_requires_explicit_confirmation=False,
        default_requires_sandbox=True,
        default_allows_external_egress=False,
        default_allows_memory_write=True,
        default_allows_tool_write=True,
        default_allows_execution=True,
    ),
    RiskTierDefinition(
        tier=RiskTier.R4,
        label="High Impact Compensatable",
        description="High-impact action that may be compensatable but requires approval.",
        reversibility=ReversibilityLevel.COMPENSATABLE,
        oversight=OversightLevel.APPROVAL_REQUIRED,
        evidence_expectation=EvidenceExpectation.TRACE_EVIDENCE_APPROVAL,
        default_requires_trace=True,
        default_requires_evidence=True,
        default_requires_approval=True,
        default_requires_explicit_confirmation=False,
        default_requires_sandbox=True,
        default_allows_external_egress=False,
        default_allows_memory_write=True,
        default_allows_tool_write=True,
        default_allows_execution=True,
    ),
    RiskTierDefinition(
        tier=RiskTier.R5,
        label="Serious Irreversible",
        description=(
            "Serious irreversible or externally consequential action requiring "
            "explicit Operator confirmation."
        ),
        reversibility=ReversibilityLevel.IRREVERSIBLE,
        oversight=OversightLevel.EXPLICIT_OPERATOR_CONFIRMATION,
        evidence_expectation=(
            EvidenceExpectation.TRACE_SHADOW_DIFF_EXPLICIT_CONFIRMATION
        ),
        default_requires_trace=True,
        default_requires_evidence=True,
        default_requires_approval=True,
        default_requires_explicit_confirmation=True,
        default_requires_sandbox=True,
        default_allows_external_egress=False,
        default_allows_memory_write=True,
        default_allows_tool_write=True,
        default_allows_execution=True,
    ),
    RiskTierDefinition(
        tier=RiskTier.R6,
        label="Denied",
        description="Denied, forbidden, or unacceptable action.",
        reversibility=ReversibilityLevel.DENIED,
        oversight=OversightLevel.DENIED,
        evidence_expectation=EvidenceExpectation.DENIAL_TRACE,
        default_requires_trace=True,
        default_requires_evidence=True,
        default_requires_approval=False,
        default_requires_explicit_confirmation=False,
        default_requires_sandbox=False,
        default_allows_external_egress=False,
        default_allows_memory_write=False,
        default_allows_tool_write=False,
        default_allows_execution=False,
    ),
)

DEFAULT_RISK_ACTION_CLASS_MAPPINGS: tuple[RiskActionClassMapping, ...] = (
    RiskActionClassMapping(
        RiskActionClass.INFORMATIONAL,
        RiskTier.R0,
        "No-op, explanation, or non-state-changing information.",
    ),
    RiskActionClassMapping(
        RiskActionClass.READ_LOCAL,
        RiskTier.R1,
        "Local read or inspection.",
    ),
    RiskActionClassMapping(
        RiskActionClass.WRITE_LOCAL,
        RiskTier.R2,
        "Reversible low-impact local write.",
    ),
    RiskActionClassMapping(
        RiskActionClass.MODIFY_CODE,
        RiskTier.R3,
        "Meaningful code or repository state change.",
    ),
    RiskActionClassMapping(
        RiskActionClass.RUN_TESTS,
        RiskTier.R2,
        "Local test execution with bounded consequence.",
    ),
    RiskActionClassMapping(
        RiskActionClass.EXECUTE_COMMAND,
        RiskTier.R3,
        "Local command execution requiring governance.",
    ),
    RiskActionClassMapping(
        RiskActionClass.CALL_MODEL_LOCAL,
        RiskTier.R2,
        "Local model call without external egress.",
    ),
    RiskActionClassMapping(
        RiskActionClass.CALL_MODEL_EXTERNAL,
        RiskTier.R4,
        "External model call with egress.",
    ),
    RiskActionClassMapping(
        RiskActionClass.WRITE_MEMORY,
        RiskTier.R3,
        "Governed memory write candidate.",
    ),
    RiskActionClassMapping(
        RiskActionClass.READ_MEMORY,
        RiskTier.R1,
        "Governed memory read.",
    ),
    RiskActionClassMapping(
        RiskActionClass.SEND_EMAIL,
        RiskTier.R5,
        "Irreversible external communication.",
    ),
    RiskActionClassMapping(
        RiskActionClass.DELETE_FILE,
        RiskTier.R4,
        "Potentially compensatable local deletion.",
    ),
    RiskActionClassMapping(
        RiskActionClass.NETWORK_EGRESS,
        RiskTier.R4,
        "Network egress with external consequence.",
    ),
    RiskActionClassMapping(
        RiskActionClass.BUSINESS_DECISION,
        RiskTier.R4,
        "Operational business decision.",
    ),
    RiskActionClassMapping(
        RiskActionClass.FINANCIAL_ACTION,
        RiskTier.R5,
        "Serious external financial consequence.",
    ),
    RiskActionClassMapping(
        RiskActionClass.PROTECTED_PATH_WRITE,
        RiskTier.R5,
        "Protected or high-impact path write.",
    ),
    RiskActionClassMapping(
        RiskActionClass.SANDBOXED_TOOL_CALL,
        RiskTier.R3,
        "Governed sandboxed tool call proposal.",
    ),
    RiskActionClassMapping(
        RiskActionClass.EXTERNAL_API_CALL,
        RiskTier.R4,
        "External API call with egress.",
    ),
)


def _definition_to_dict(definition: RiskTierDefinition) -> dict[str, Any]:
    return {
        "default_allows_execution": definition.default_allows_execution,
        "default_allows_external_egress": definition.default_allows_external_egress,
        "default_allows_memory_write": definition.default_allows_memory_write,
        "default_allows_tool_write": definition.default_allows_tool_write,
        "default_requires_approval": definition.default_requires_approval,
        "default_requires_evidence": definition.default_requires_evidence,
        "default_requires_explicit_confirmation": (
            definition.default_requires_explicit_confirmation
        ),
        "default_requires_sandbox": definition.default_requires_sandbox,
        "default_requires_trace": definition.default_requires_trace,
        "description": definition.description,
        "evidence_expectation": definition.evidence_expectation.value,
        "label": definition.label,
        "oversight": definition.oversight.value,
        "reversibility": definition.reversibility.value,
        "tier": definition.tier.value,
    }


def _mapping_to_dict(mapping: RiskActionClassMapping) -> dict[str, Any]:
    return {
        "action_class": mapping.action_class.value,
        "default_tier": mapping.default_tier.value,
        "description": mapping.description,
    }


def export_risk_tier_policy_schema() -> dict[str, Any]:
    return {
        "canonical_fields": list(RISK_TIER_CANONICAL_FIELDS),
        "dangerous_field_names": sorted(RISK_TIER_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(RISK_TIER_DANGEROUS_METADATA_KEYS),
        "default_action_class_mappings": [
            _mapping_to_dict(mapping)
            for mapping in sorted(
                DEFAULT_RISK_ACTION_CLASS_MAPPINGS,
                key=lambda item: item.action_class.value,
            )
        ],
        "default_tier_definitions": [
            _definition_to_dict(definition)
            for definition in sorted(
                DEFAULT_RISK_TIER_DEFINITIONS,
                key=lambda item: item.tier.value,
            )
        ],
        "definition_required_fields": list(RISK_TIER_DEFINITION_REQUIRED_FIELDS),
        "forbidden_fields": sorted(RISK_TIER_FORBIDDEN_FIELDS),
        "mapping_optional_fields": list(RISK_TIER_ACTION_MAPPING_OPTIONAL_FIELDS),
        "mapping_required_fields": list(RISK_TIER_ACTION_MAPPING_REQUIRED_FIELDS),
        "optional_fields": list(RISK_TIER_OPTIONAL_FIELDS),
        "required_fields": list(RISK_TIER_REQUIRED_FIELDS),
        "required_tiers": [tier.value for tier in REQUIRED_RISK_TIERS],
        "schema_version": RISK_TIER_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS),
    }


def get_risk_tier_policy_schema() -> dict[str, Any]:
    return export_risk_tier_policy_schema()


def is_supported_risk_tier_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS


def validate_risk_tier_policy_schema_version(
    version: object,
) -> RiskTierValidationResult:
    errors: list[RiskTierValidationIssue] = []
    warnings: list[RiskTierValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            RiskTierValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            RiskTierValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_RISK_TIER_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return RiskTierValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
