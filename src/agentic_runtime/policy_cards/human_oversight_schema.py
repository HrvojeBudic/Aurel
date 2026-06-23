"""Human Oversight Policy Card Schema v1 (P1.6.4).

Centralized schema contract for HumanOversightPolicyCard. This module defines the
legal closed-world shape, dangerous field/key sets, schema versioning, default
R0-R6 oversight mappings, and default escalation rule seeds.
"""
from __future__ import annotations

from typing import Any

from .human_oversight import (
    ConfirmationRequirement,
    HumanOversightAction,
    HumanOversightEscalationRule,
    HumanOversightLevel,
    HumanOversightMode,
    HumanOversightTrigger,
    HumanOversightValidationIssue,
    HumanOversightValidationResult,
    OversightEvidenceRequirement,
    OversightEvidenceType,
    ReviewerRequirement,
    RiskTierOversightMapping,
)
from .risk_tiers import RiskTier


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSION: str = "1.0"

SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

# ---------------------------------------------------------------------------
# Required fields — must be present
# ---------------------------------------------------------------------------

HUMAN_OVERSIGHT_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "risk_tier_mappings",
)

HUMAN_OVERSIGHT_OPTIONAL_FIELDS: tuple[str, ...] = (
    "escalation_rules",
    "default_confirmation_requirement",
    "default_reviewer_requirement",
    "metadata",
)

HUMAN_OVERSIGHT_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "grant_authority",
    "bypass_policy",
    "policy_bypass",
    "disable_policy",
    "skip_policy",
    "skip_trace",
    "skip_evidence",
    "operator_not_required",
    "operator_override",
    "approval_grant",
    "auto_approve",
    "silent_approval",
    "skip_approval",
    "skip_confirmation",
    "bypass_oversight",
    "disable_trace",
    "risk_override",
    "runtime_resolver",
    "enforcement",
    "runtime_enforcement",
    "conflict_detector",
    "simulation_mode",
    "trace_hook",
    "unrestricted",
    "report_generator",
})

HUMAN_OVERSIGHT_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "risk_tier_mappings",
    "escalation_rules",
    "default_confirmation_requirement",
    "default_reviewer_requirement",
    "metadata",
)

# ---------------------------------------------------------------------------
# Required tiers for oversight mappings
# ---------------------------------------------------------------------------

REQUIRED_HUMAN_OVERSIGHT_RISK_TIERS: tuple[RiskTier, ...] = (
    RiskTier.R0,
    RiskTier.R1,
    RiskTier.R2,
    RiskTier.R3,
    RiskTier.R4,
    RiskTier.R5,
    RiskTier.R6,
)

# ---------------------------------------------------------------------------
# Sub-object required fields
# ---------------------------------------------------------------------------

HUMAN_OVERSIGHT_MAPPING_REQUIRED_FIELDS: tuple[str, ...] = (
    "risk_tier",
    "oversight_level",
    "oversight_mode",
    "action",
)

HUMAN_OVERSIGHT_MAPPING_OPTIONAL_FIELDS: tuple[str, ...] = (
    "confirmation_requirement",
    "reviewer_requirement",
    "evidence_requirements",
    "description",
)

HUMAN_OVERSIGHT_ESCALATION_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "trigger",
    "action",
)

HUMAN_OVERSIGHT_ESCALATION_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "minimum_risk_tier",
    "description",
)

HUMAN_OVERSIGHT_CONFIRMATION_REQUIRED_FIELDS: tuple[str, ...] = (
    "requires_explicit_confirmation",
    "confirmation_phrase_required",
    "preview_required",
    "shadow_diff_required",
    "reason_required",
    "evidence_required",
    "operator_identity_required",
    "expires_after_seconds",
)

HUMAN_OVERSIGHT_REVIEWER_REQUIRED_FIELDS: tuple[str, ...] = (
    "operator_required",
    "required_reviewer_role",
    "delegated_reviewer_allowed",
    "dual_review_required",
    "governance_board_required",
)

HUMAN_OVERSIGHT_EVIDENCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "evidence_type",
    "required",
    "description",
)

# ---------------------------------------------------------------------------
# Dangerous fields and metadata keys
# ---------------------------------------------------------------------------

HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES: frozenset[str] = HUMAN_OVERSIGHT_FORBIDDEN_FIELDS

HUMAN_OVERSIGHT_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "auto_approve",
    "operator_not_required",
    "skip_approval",
    "skip_confirmation",
    "bypass_policy",
    "bypass_oversight",
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
    "operator_override",
    "operator override",
    "unrestricted",
})

# ---------------------------------------------------------------------------
# Default R0-R6 oversight mappings
# ---------------------------------------------------------------------------

DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS: tuple[RiskTierOversightMapping, ...] = (
    # R0 — Informational
    RiskTierOversightMapping(
        risk_tier=RiskTier.R0,
        oversight_level=HumanOversightLevel.NONE,
        oversight_mode=HumanOversightMode.NONE,
        action=HumanOversightAction.NOTIFY_OPERATOR,
        description="No oversight required for informational actions.",
    ),
    # R1 — Safe Local Read
    RiskTierOversightMapping(
        risk_tier=RiskTier.R1,
        oversight_level=HumanOversightLevel.NONE,
        oversight_mode=HumanOversightMode.NONE,
        action=HumanOversightAction.NOTIFY_OPERATOR,
        evidence_requirements=(
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.TRACE_EVENT,
                required=False,
                description="Lightweight trace if applicable",
            ),
        ),
        description="No oversight required for safe local reads.",
    ),
    # R2 — Reversible Local Write
    RiskTierOversightMapping(
        risk_tier=RiskTier.R2,
        oversight_level=HumanOversightLevel.NOTIFY_ONLY,
        oversight_mode=HumanOversightMode.NOTIFICATION,
        action=HumanOversightAction.NOTIFY_OPERATOR,
        reviewer_requirement=ReviewerRequirement(
            delegated_reviewer_allowed=True,
        ),
        evidence_requirements=(
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.TRACE_EVENT,
                description="Notify and trace reversible writes.",
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.STATE_DIFF,
                required=False,
            ),
        ),
        description="Notification recommended for reversible local writes.",
    ),
    # R3 — Meaningful State Change
    RiskTierOversightMapping(
        risk_tier=RiskTier.R3,
        oversight_level=HumanOversightLevel.REVIEW_RECOMMENDED,
        oversight_mode=HumanOversightMode.REVIEW,
        action=HumanOversightAction.REQUEST_REVIEW,
        reviewer_requirement=ReviewerRequirement(
            operator_required=False,
        ),
        evidence_requirements=(
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.TRACE_EVENT,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.EVIDENCE_REF,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.STATE_DIFF,
            ),
        ),
        description="Review recommended for meaningful state changes.",
    ),
    # R4 — High Impact Compensatable
    RiskTierOversightMapping(
        risk_tier=RiskTier.R4,
        oversight_level=HumanOversightLevel.APPROVAL_REQUIRED,
        oversight_mode=HumanOversightMode.APPROVAL,
        action=HumanOversightAction.REQUEST_APPROVAL,
        reviewer_requirement=ReviewerRequirement(
            operator_required=True,
        ),
        evidence_requirements=(
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.POLICY_DECISION,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.RISK_TIER_DECISION,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.TRACE_EVENT,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.EVIDENCE_REF,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.STATE_DIFF,
            ),
        ),
        description="Human approval required for high-impact compensatable actions.",
    ),
    # R5 — Serious / Irreversible
    RiskTierOversightMapping(
        risk_tier=RiskTier.R5,
        oversight_level=HumanOversightLevel.EXPLICIT_CONFIRMATION_REQUIRED,
        oversight_mode=HumanOversightMode.EXPLICIT_CONFIRMATION,
        action=HumanOversightAction.REQUEST_EXPLICIT_CONFIRMATION,
        confirmation_requirement=ConfirmationRequirement(
            requires_explicit_confirmation=True,
            confirmation_phrase_required=True,
            preview_required=True,
            shadow_diff_required=True,
            reason_required=True,
            evidence_required=True,
            operator_identity_required=True,
        ),
        reviewer_requirement=ReviewerRequirement(
            operator_required=True,
        ),
        evidence_requirements=(
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.POLICY_DECISION,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.RISK_TIER_DECISION,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.EXPLICIT_CONFIRMATION_RECORD,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.SHADOW_DIFF,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.TRACE_EVENT,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.EVIDENCE_REF,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.OUTPUT_PASSPORT,
            ),
        ),
        description=(
            "Explicit Operator confirmation required for serious "
            "irreversible actions."
        ),
    ),
    # R6 — Denied / Forbidden
    RiskTierOversightMapping(
        risk_tier=RiskTier.R6,
        oversight_level=HumanOversightLevel.DENY,
        oversight_mode=HumanOversightMode.DENY,
        action=HumanOversightAction.DENY_ACTION,
        evidence_requirements=(
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.POLICY_DECISION,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.RISK_TIER_DECISION,
            ),
            OversightEvidenceRequirement(
                evidence_type=OversightEvidenceType.TRACE_EVENT,
            ),
        ),
        description="Denied; action must not proceed.",
    ),
)


# ---------------------------------------------------------------------------
# Default escalation rules
# ---------------------------------------------------------------------------

DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES: tuple[HumanOversightEscalationRule, ...] = (
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.RISK_TIER_AT_OR_ABOVE,
        action=HumanOversightAction.REQUEST_APPROVAL,
        minimum_risk_tier=RiskTier.R4,
        description="Escalate to approval at R4 or above.",
    ),
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.IRREVERSIBLE_ACTION,
        action=HumanOversightAction.REQUEST_EXPLICIT_CONFIRMATION,
        minimum_risk_tier=RiskTier.R5,
        description="Escalate to explicit confirmation for irreversible actions.",
    ),
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.EXTERNAL_EGRESS,
        action=HumanOversightAction.REQUEST_APPROVAL,
        minimum_risk_tier=RiskTier.R4,
        description="Escalate to approval on external egress.",
    ),
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.PROTECTED_PATH_WRITE,
        action=HumanOversightAction.REQUEST_EXPLICIT_CONFIRMATION,
        minimum_risk_tier=RiskTier.R5,
        description="Escalate to explicit confirmation for protected path writes.",
    ),
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.MISSING_EVIDENCE,
        action=HumanOversightAction.REQUIRE_ADDITIONAL_EVIDENCE,
        minimum_risk_tier=RiskTier.R3,
        description="Require additional evidence when evidence is missing.",
    ),
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.AUTHORITY_UNCERTAIN,
        action=HumanOversightAction.PAUSE_FOR_HUMAN,
        minimum_risk_tier=RiskTier.R3,
        description="Pause for human when authority is uncertain.",
    ),
    HumanOversightEscalationRule(
        trigger=HumanOversightTrigger.BUSINESS_PROCESS_HIGH_IMPACT,
        action=HumanOversightAction.REQUEST_GOVERNANCE_BOARD_REVIEW,
        minimum_risk_tier=RiskTier.R4,
        description="Escalate to governance board for high-impact business processes.",
    ),
)


# ---------------------------------------------------------------------------
# Schema export functions
# ---------------------------------------------------------------------------


def _mapping_to_dict(mapping: RiskTierOversightMapping) -> dict[str, Any]:
    result: dict[str, Any] = {
        "action": mapping.action.value,
        "description": mapping.description,
        "oversight_level": mapping.oversight_level.value,
        "oversight_mode": mapping.oversight_mode.value,
        "risk_tier": mapping.risk_tier.value,
    }
    if mapping.confirmation_requirement is not None:
        cr = mapping.confirmation_requirement
        result["confirmation_requirement"] = {
            "confirmation_phrase_required": cr.confirmation_phrase_required,
            "evidence_required": cr.evidence_required,
            "operator_identity_required": cr.operator_identity_required,
            "preview_required": cr.preview_required,
            "reason_required": cr.reason_required,
            "requires_explicit_confirmation": cr.requires_explicit_confirmation,
            "shadow_diff_required": cr.shadow_diff_required,
        }
        if cr.expires_after_seconds is not None:
            result["confirmation_requirement"]["expires_after_seconds"] = (
                cr.expires_after_seconds
            )
    if mapping.reviewer_requirement is not None:
        rr = mapping.reviewer_requirement
        result["reviewer_requirement"] = {
            "delegated_reviewer_allowed": rr.delegated_reviewer_allowed,
            "dual_review_required": rr.dual_review_required,
            "governance_board_required": rr.governance_board_required,
            "operator_required": rr.operator_required,
        }
        if rr.required_reviewer_role is not None:
            result["reviewer_requirement"]["required_reviewer_role"] = (
                rr.required_reviewer_role
            )
    if mapping.evidence_requirements:
        result["evidence_requirements"] = [
            {
                "description": e.description,
                "evidence_type": e.evidence_type.value,
                "required": e.required,
            }
            for e in mapping.evidence_requirements
        ]
    return result


def _escalation_to_dict(rule: HumanOversightEscalationRule) -> dict[str, Any]:
    result: dict[str, Any] = {
        "action": rule.action.value,
        "description": rule.description,
        "trigger": rule.trigger.value,
    }
    if rule.minimum_risk_tier is not None:
        result["minimum_risk_tier"] = rule.minimum_risk_tier.value
    return result


def export_human_oversight_policy_schema() -> dict[str, Any]:
    return {
        "canonical_fields": list(HUMAN_OVERSIGHT_CANONICAL_FIELDS),
        "confirmation_required_fields": list(HUMAN_OVERSIGHT_CONFIRMATION_REQUIRED_FIELDS),
        "dangerous_field_names": sorted(HUMAN_OVERSIGHT_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(HUMAN_OVERSIGHT_DANGEROUS_METADATA_KEYS),
        "default_escalation_rules": [
            _escalation_to_dict(rule)
            for rule in sorted(
                DEFAULT_HUMAN_OVERSIGHT_ESCALATION_RULES,
                key=lambda item: item.trigger.value,
            )
        ],
        "default_risk_tier_oversight_mappings": [
            _mapping_to_dict(mapping)
            for mapping in sorted(
                DEFAULT_RISK_TIER_OVERSIGHT_MAPPINGS,
                key=lambda item: item.risk_tier.value,
            )
        ],
        "escalation_rule_required_fields": list(HUMAN_OVERSIGHT_ESCALATION_RULE_REQUIRED_FIELDS),
        "evidence_required_fields": list(HUMAN_OVERSIGHT_EVIDENCE_REQUIRED_FIELDS),
        "forbidden_fields": sorted(HUMAN_OVERSIGHT_FORBIDDEN_FIELDS),
        "mapping_required_fields": list(HUMAN_OVERSIGHT_MAPPING_REQUIRED_FIELDS),
        "optional_fields": list(HUMAN_OVERSIGHT_OPTIONAL_FIELDS),
        "required_fields": list(HUMAN_OVERSIGHT_REQUIRED_FIELDS),
        "required_tiers": [tier.value for tier in REQUIRED_HUMAN_OVERSIGHT_RISK_TIERS],
        "reviewer_required_fields": list(HUMAN_OVERSIGHT_REVIEWER_REQUIRED_FIELDS),
        "schema_version": HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS),
    }


def get_human_oversight_policy_schema() -> dict[str, Any]:
    return export_human_oversight_policy_schema()


def is_supported_human_oversight_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS


def validate_human_oversight_policy_schema_version(
    version: object,
) -> HumanOversightValidationResult:
    errors: list[HumanOversightValidationIssue] = []
    warnings: list[HumanOversightValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            HumanOversightValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            HumanOversightValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_HUMAN_OVERSIGHT_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return HumanOversightValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
