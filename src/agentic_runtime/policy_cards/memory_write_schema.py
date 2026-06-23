"""Memory Write Policy Card Schema v1 (P1.6.7).

Centralized schema contract for MemoryWritePolicyCard. Defines the legal
closed-world shape, dangerous field/key sets, schema versioning, conservative
default deny-by-default memory write rules, and required vocabulary constants.

This module is schema/model only. It does not store, retrieve, consolidate,
promote, canonize or enforce memory at runtime.
"""
from __future__ import annotations

from typing import Any

from .memory_write import (
    MemoryRetentionClass,
    MemoryVerificationStatus,
    MemoryWriteDecision,
    MemoryWriteRequirement,
    MemoryWriteRequirementType,
    MemoryWriteRule,
    MemoryWriteType,
    MemoryWriteValidationIssue,
    MemoryWriteValidationResult,
    MemoryZone,
)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSION: str = "1.0"

SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

# ---------------------------------------------------------------------------
# Top-level field classification
# ---------------------------------------------------------------------------

MEMORY_WRITE_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "memory_rules",
)

MEMORY_WRITE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "default_decision",
    "metadata",
)

MEMORY_WRITE_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "memory_engine",
    "mneme",
    "storage_engine",
    "retrieval_engine",
    "consolidation_engine",
    "memory_graph",
    "canon_promotion",
    "skill_promotion",
    "verification_court",
    "runtime_enforcement",
    "enforcement",
    "bypass_policy",
    "bypass_memory_policy",
    "skip_memory_policy",
    "policy_bypass",
    "disable_policy",
    "runtime_resolver",
    "conflict_detector",
    "simulation_mode",
    "trace_hook",
    "report_generator",
    "memory_override_backdoor",
})

MEMORY_WRITE_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "memory_rules",
    "default_decision",
    "metadata",
)

# ---------------------------------------------------------------------------
# Sub-object field classification
# ---------------------------------------------------------------------------

MEMORY_WRITE_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "memory_zone",
    "write_type",
    "decision",
    "verification_status",
    "retention_class",
)

MEMORY_WRITE_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "requirements",
    "allowed_data_classes",
    "forbidden_data_classes",
    "risk_ceiling",
    "required_oversight",
    "trace_required",
    "evidence_required",
    "provenance_required",
    "description",
)

MEMORY_WRITE_REQUIREMENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "requirement_type",
)

MEMORY_WRITE_REQUIREMENT_OPTIONAL_FIELDS: tuple[str, ...] = (
    "required",
    "description",
)

# ---------------------------------------------------------------------------
# Dangerous fields and metadata keys
# ---------------------------------------------------------------------------

MEMORY_WRITE_DANGEROUS_FIELD_NAMES: frozenset[str] = MEMORY_WRITE_FORBIDDEN_FIELDS

MEMORY_WRITE_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "auto_canonize",
    "auto_verify",
    "auto_promote_skill",
    "remember_everything",
    "bypass_memory_policy",
    "skip_memory_policy",
    "memory_policy_bypass",
    "silent_memory_write",
    "canonicalize_without_review",
    "policy_memory_override",
    "operator_profile_override",
    "consent_not_required",
    "operator_not_required",
    "skip_evidence",
    "skip_provenance",
    "skip_trace",
    "store_credentials",
    "store_secrets",
    "externalize_memory",
})

# ---------------------------------------------------------------------------
# Protected zones / strict data classes
# ---------------------------------------------------------------------------

PROTECTED_MEMORY_ZONES: frozenset[str] = frozenset({
    "canon_memory",
    "policy_memory",
    "verified_skill_memory",
    "operator_profile",
})

STRICT_MEMORY_DATA_CLASSES: frozenset[str] = frozenset({
    "credentials",
    "operator_private",
    "sensitive_personal_data",
    "memory_record",
    "trace_record",
    "source_code",
})

# ---------------------------------------------------------------------------
# Default conservative memory write rules
# ---------------------------------------------------------------------------


def _req(
    requirement_type: MemoryWriteRequirementType,
    description: str = "",
) -> MemoryWriteRequirement:
    return MemoryWriteRequirement(
        requirement_type=requirement_type, required=True, description=description,
    )


DEFAULT_MEMORY_WRITE_RULES: tuple[MemoryWriteRule, ...] = (
    # Scratchpad — ephemeral, low friction, never durable truth
    MemoryWriteRule(
        memory_zone=MemoryZone.SCRATCHPAD,
        write_type=MemoryWriteType.TEMPORARY_NOTE,
        decision=MemoryWriteDecision.EPHEMERAL_ONLY,
        verification_status=MemoryVerificationStatus.UNVERIFIED,
        retention_class=MemoryRetentionClass.EPHEMERAL,
        trace_required=False,
        evidence_required=False,
        provenance_required=False,
        description="Scratchpad reasoning notes are ephemeral and never durable truth.",
    ),
    # Working memory — session-scoped task state
    MemoryWriteRule(
        memory_zone=MemoryZone.WORKING_MEMORY,
        write_type=MemoryWriteType.PROJECT_STATE,
        decision=MemoryWriteDecision.ALLOW,
        verification_status=MemoryVerificationStatus.UNVERIFIED,
        retention_class=MemoryRetentionClass.SESSION,
        trace_required=True,
        evidence_required=False,
        provenance_required=False,
        description="Working memory holds session/local task state.",
    ),
    # Episodic memory — candidate experience, evidence-linked
    MemoryWriteRule(
        memory_zone=MemoryZone.EPISODIC_MEMORY,
        write_type=MemoryWriteType.OBSERVATION,
        decision=MemoryWriteDecision.REQUIRES_EVIDENCE,
        verification_status=MemoryVerificationStatus.EVIDENCE_SUPPORTED,
        retention_class=MemoryRetentionClass.PROJECT_SCOPED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Episodic memory must be evidence and provenance bound.",
    ),
    # Semantic memory — durable knowledge, evidence required
    MemoryWriteRule(
        memory_zone=MemoryZone.SEMANTIC_MEMORY,
        write_type=MemoryWriteType.EVIDENCE_SUMMARY,
        decision=MemoryWriteDecision.REQUIRES_EVIDENCE,
        verification_status=MemoryVerificationStatus.EVIDENCE_SUPPORTED,
        retention_class=MemoryRetentionClass.LONG_LIVED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="No evidence-free semantic memory.",
    ),
    # Procedural memory — requires evaluation/verification gates
    MemoryWriteRule(
        memory_zone=MemoryZone.PROCEDURAL_MEMORY,
        write_type=MemoryWriteType.BEHAVIORAL_NOTE,
        decision=MemoryWriteDecision.REQUIRES_REVIEW,
        verification_status=MemoryVerificationStatus.CANDIDATE,
        retention_class=MemoryRetentionClass.LONG_LIVED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_EVALUATION_RESULT),
            _req(MemoryWriteRequirementType.REQUIRES_VERIFICATION),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Procedural memory must not become skill/reflex automatically.",
    ),
    # Operator profile — protected, review/consent/provenance
    MemoryWriteRule(
        memory_zone=MemoryZone.OPERATOR_PROFILE,
        write_type=MemoryWriteType.USER_PREFERENCE,
        decision=MemoryWriteDecision.REQUIRES_REVIEW,
        verification_status=MemoryVerificationStatus.OPERATOR_REVIEWED,
        retention_class=MemoryRetentionClass.LONG_LIVED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_USER_CONSENT),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Operator profile memory is protected and requires consent/review.",
    ),
    # Project memory — decisions/project state, evidence bound
    MemoryWriteRule(
        memory_zone=MemoryZone.PROJECT_MEMORY,
        write_type=MemoryWriteType.DECISION,
        decision=MemoryWriteDecision.REQUIRES_EVIDENCE,
        verification_status=MemoryVerificationStatus.EVIDENCE_SUPPORTED,
        retention_class=MemoryRetentionClass.PROJECT_SCOPED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Project decisions require evidence and provenance.",
    ),
    # Canon memory — highest scrutiny, no silent writes
    MemoryWriteRule(
        memory_zone=MemoryZone.CANON_MEMORY,
        write_type=MemoryWriteType.CANON_UPDATE,
        decision=MemoryWriteDecision.REQUIRES_CONFIRMATION,
        verification_status=MemoryVerificationStatus.EVIDENCE_SUPPORTED,
        retention_class=MemoryRetentionClass.AUDIT_RETAINED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
            _req(MemoryWriteRequirementType.REQUIRES_EXPLICIT_CONFIRMATION),
            _req(MemoryWriteRequirementType.REQUIRES_CONFLICT_CHECK),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="No silent canon memory writes; canonization only after future gates.",
    ),
    # Policy memory — governance memory, highest scrutiny
    MemoryWriteRule(
        memory_zone=MemoryZone.POLICY_MEMORY,
        write_type=MemoryWriteType.POLICY_RECORD,
        decision=MemoryWriteDecision.REQUIRES_CONFIRMATION,
        verification_status=MemoryVerificationStatus.OPERATOR_REVIEWED,
        retention_class=MemoryRetentionClass.AUDIT_RETAINED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_POLICY_AUTHORITY),
            _req(MemoryWriteRequirementType.REQUIRES_SOURCE_REFERENCE),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_OPERATOR_REVIEW),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Policy memory must not be casual memory; requires authority/governance.",
    ),
    # Evaluation memory — eval/verifier results
    MemoryWriteRule(
        memory_zone=MemoryZone.EVALUATION_MEMORY,
        write_type=MemoryWriteType.EVALUATION_RESULT,
        decision=MemoryWriteDecision.REQUIRES_EVIDENCE,
        verification_status=MemoryVerificationStatus.EVIDENCE_SUPPORTED,
        retention_class=MemoryRetentionClass.PROJECT_SCOPED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_EVALUATION_RESULT),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Evaluation memory records verifier/eval results.",
    ),
    # Skill candidate memory — candidate, not verified
    MemoryWriteRule(
        memory_zone=MemoryZone.SKILL_CANDIDATE_MEMORY,
        write_type=MemoryWriteType.SKILL_CANDIDATE,
        decision=MemoryWriteDecision.CANDIDATE_ONLY,
        verification_status=MemoryVerificationStatus.CANDIDATE,
        retention_class=MemoryRetentionClass.PROJECT_SCOPED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_EVALUATION_RESULT),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Candidate skill is not verified skill.",
    ),
    # Verified skill memory — requires evaluation/verification
    MemoryWriteRule(
        memory_zone=MemoryZone.VERIFIED_SKILL_MEMORY,
        write_type=MemoryWriteType.VERIFIED_SKILL,
        decision=MemoryWriteDecision.REQUIRES_REVIEW,
        verification_status=MemoryVerificationStatus.VERIFIED,
        retention_class=MemoryRetentionClass.LONG_LIVED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_EVALUATION_RESULT),
            _req(MemoryWriteRequirementType.REQUIRES_VERIFICATION),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Verified skill memory requires evaluation/verification; no auto-promotion.",
    ),
    # Audit memory — trace/evidence bound
    MemoryWriteRule(
        memory_zone=MemoryZone.AUDIT_MEMORY,
        write_type=MemoryWriteType.AUDIT_NOTE,
        decision=MemoryWriteDecision.ALLOW,
        verification_status=MemoryVerificationStatus.EVIDENCE_SUPPORTED,
        retention_class=MemoryRetentionClass.AUDIT_RETAINED,
        requirements=(
            _req(MemoryWriteRequirementType.REQUIRES_TRACE_REF),
            _req(MemoryWriteRequirementType.REQUIRES_EVIDENCE_REF),
        ),
        trace_required=True,
        evidence_required=True,
        provenance_required=True,
        description="Audit memory is trace and evidence bound.",
    ),
    # Forbidden zone — never store
    MemoryWriteRule(
        memory_zone=MemoryZone.FORBIDDEN,
        write_type=MemoryWriteType.TEMPORARY_NOTE,
        decision=MemoryWriteDecision.FORBIDDEN,
        verification_status=MemoryVerificationStatus.REJECTED,
        retention_class=MemoryRetentionClass.DO_NOT_STORE,
        trace_required=True,
        evidence_required=False,
        provenance_required=False,
        forbidden_data_classes=(
            "credentials", "operator_private", "sensitive_personal_data",
        ),
        description="Forbidden zone never allows durable writes.",
    ),
)

# ---------------------------------------------------------------------------
# Schema export
# ---------------------------------------------------------------------------


def export_memory_write_policy_schema() -> dict[str, Any]:
    return {
        "schema_version": MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS),
        "required_fields": list(MEMORY_WRITE_REQUIRED_FIELDS),
        "optional_fields": list(MEMORY_WRITE_OPTIONAL_FIELDS),
        "forbidden_fields": sorted(MEMORY_WRITE_FORBIDDEN_FIELDS),
        "canonical_fields": list(MEMORY_WRITE_CANONICAL_FIELDS),
        "rule_required_fields": list(MEMORY_WRITE_RULE_REQUIRED_FIELDS),
        "rule_optional_fields": list(MEMORY_WRITE_RULE_OPTIONAL_FIELDS),
        "requirement_required_fields": list(MEMORY_WRITE_REQUIREMENT_REQUIRED_FIELDS),
        "requirement_optional_fields": list(MEMORY_WRITE_REQUIREMENT_OPTIONAL_FIELDS),
        "dangerous_field_names": sorted(MEMORY_WRITE_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(MEMORY_WRITE_DANGEROUS_METADATA_KEYS),
        "protected_memory_zones": sorted(PROTECTED_MEMORY_ZONES),
        "strict_memory_data_classes": sorted(STRICT_MEMORY_DATA_CLASSES),
        "memory_zones": sorted(z.value for z in MemoryZone),
        "memory_write_types": sorted(t.value for t in MemoryWriteType),
        "memory_write_decisions": sorted(d.value for d in MemoryWriteDecision),
        "memory_verification_statuses": sorted(s.value for s in MemoryVerificationStatus),
        "memory_retention_classes": sorted(r.value for r in MemoryRetentionClass),
        "memory_write_requirement_types": sorted(
            r.value for r in MemoryWriteRequirementType
        ),
    }


def get_memory_write_policy_schema() -> dict[str, Any]:
    return export_memory_write_policy_schema()


def is_supported_memory_write_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS


def validate_memory_write_policy_schema_version(
    version: object,
) -> MemoryWriteValidationResult:
    errors: list[MemoryWriteValidationIssue] = []
    warnings: list[MemoryWriteValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            MemoryWriteValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            MemoryWriteValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_MEMORY_WRITE_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return MemoryWriteValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
