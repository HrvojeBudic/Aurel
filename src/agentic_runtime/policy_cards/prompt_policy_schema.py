"""Prompt Policy Card Schema v1 (P1.6.8).

Centralized schema contract for PromptPolicyCard. Defines the legal closed-world
shape, dangerous field/key sets, schema versioning, prompt source/trust categories,
and strict default prompt handling rules that preserve instruction hierarchy.

This module is schema/model only. It does not compile prompts, enforce instruction
hierarchy, detect prompt injection, or block tools/memory at runtime.
"""
from __future__ import annotations

from typing import Any

from .prompt_policy import (
    PromptHandlingRule,
    PromptInjectionRisk,
    PromptInjectionSignal,
    PromptPolicyDecision,
    PromptPolicyValidationIssue,
    PromptPolicyValidationResult,
    PromptRole,
    PromptSourceType,
    PromptTrustLevel,
)


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------

PROMPT_POLICY_CARD_SCHEMA_VERSION: str = "1.0"

SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

# ---------------------------------------------------------------------------
# Top-level field classification
# ---------------------------------------------------------------------------

PROMPT_POLICY_REQUIRED_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "prompt_rules",
)

PROMPT_POLICY_OPTIONAL_FIELDS: tuple[str, ...] = (
    "default_decision",
    "metadata",
)

PROMPT_POLICY_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "authority_grant",
    "prompt_compiler",
    "prompt_assembler",
    "instruction_hierarchy_enforcer",
    "injection_detector",
    "jailbreak_detector",
    "runtime_enforcement",
    "enforcement",
    "bypass_policy",
    "bypass_prompt_policy",
    "skip_prompt_policy",
    "policy_bypass",
    "disable_policy",
    "runtime_resolver",
    "conflict_detector",
    "simulation_mode",
    "trace_hook",
    "report_generator",
    "prompt_override_backdoor",
})

PROMPT_POLICY_CANONICAL_FIELDS: tuple[str, ...] = (
    "policy_card",
    "schema_version",
    "prompt_rules",
    "default_decision",
    "metadata",
)

# ---------------------------------------------------------------------------
# Sub-object field classification
# ---------------------------------------------------------------------------

PROMPT_HANDLING_RULE_REQUIRED_FIELDS: tuple[str, ...] = (
    "source_type",
    "trust_level",
    "prompt_role",
    "decision",
)

PROMPT_HANDLING_RULE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "allowed_as_instruction",
    "allowed_as_context",
    "allowed_to_request_tools",
    "allowed_to_write_memory",
    "allowed_to_modify_policy",
    "allowed_to_modify_identity",
    "requires_provenance",
    "requires_redaction",
    "requires_review",
    "requires_sandbox",
    "local_only",
    "injection_risk",
    "injection_signals",
    "requirements",
    "risk_ceiling",
    "required_oversight",
    "description",
)

PROMPT_BOUNDARY_REQUIREMENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "requirement_type",
)

PROMPT_BOUNDARY_REQUIREMENT_OPTIONAL_FIELDS: tuple[str, ...] = (
    "required",
    "description",
)

PROMPT_INJECTION_SIGNAL_REQUIRED_FIELDS: tuple[str, ...] = (
    "pattern",
    "risk",
)

PROMPT_INJECTION_SIGNAL_OPTIONAL_FIELDS: tuple[str, ...] = (
    "description",
)

# ---------------------------------------------------------------------------
# Dangerous fields and metadata keys
# ---------------------------------------------------------------------------

PROMPT_POLICY_DANGEROUS_FIELD_NAMES: frozenset[str] = PROMPT_POLICY_FORBIDDEN_FIELDS

PROMPT_POLICY_DANGEROUS_METADATA_KEYS: frozenset[str] = frozenset({
    "ignore_policy",
    "bypass_prompt_policy",
    "skip_prompt_policy",
    "prompt_policy_bypass",
    "grant_prompt_authority",
    "grant_tool_access",
    "allow_jailbreak",
    "reveal_system_prompt",
    "reveal_developer_prompt",
    "modify_identity",
    "modify_policy",
    "auto_trust_external",
    "trust_unknown_source",
    "tool_output_as_instruction",
    "external_as_instruction",
    "memory_write_allowed",
    "operator_not_required",
    "skip_provenance",
    "skip_review",
    "skip_redaction",
    "secret_exfiltration_allowed",
})

# ---------------------------------------------------------------------------
# Prompt source / trust categories
# ---------------------------------------------------------------------------

TRUSTED_PROMPT_SOURCES: frozenset[str] = frozenset({
    "system_prompt",
    "developer_prompt",
    "operator_prompt",
})

UNTRUSTED_PROMPT_SOURCES: frozenset[str] = frozenset({
    "tool_output",
    "retrieved_memory",
    "retrieved_document",
    "web_content",
    "email_content",
    "file_content",
    "code_content",
    "external_api_content",
    "unknown",
})

EXTERNAL_PROMPT_SOURCES: frozenset[str] = frozenset({
    "web_content",
    "email_content",
    "file_content",
    "code_content",
    "external_api_content",
    "retrieved_document",
    "tool_output",
    "unknown",
})

PROTECTED_PROMPT_SOURCES: frozenset[str] = frozenset({
    "system_prompt",
    "developer_prompt",
    "operator_prompt",
})

# ---------------------------------------------------------------------------
# Default strict prompt handling rules
# ---------------------------------------------------------------------------


def _rule(
    source_type: PromptSourceType,
    trust_level: PromptTrustLevel,
    prompt_role: PromptRole,
    decision: PromptPolicyDecision,
    *,
    allowed_as_instruction: bool = False,
    allowed_as_context: bool = True,
    allowed_to_request_tools: bool = False,
    allowed_to_write_memory: bool = False,
    allowed_to_modify_policy: bool = False,
    allowed_to_modify_identity: bool = False,
    requires_provenance: bool = True,
    requires_redaction: bool = False,
    requires_review: bool = False,
    requires_sandbox: bool = False,
    local_only: bool = False,
    injection_risk: PromptInjectionRisk = PromptInjectionRisk.NONE,
    injection_signals: tuple[PromptInjectionSignal, ...] = (),
    description: str = "",
) -> PromptHandlingRule:
    return PromptHandlingRule(
        source_type=source_type,
        trust_level=trust_level,
        prompt_role=prompt_role,
        decision=decision,
        allowed_as_instruction=allowed_as_instruction,
        allowed_as_context=allowed_as_context,
        allowed_to_request_tools=allowed_to_request_tools,
        allowed_to_write_memory=allowed_to_write_memory,
        allowed_to_modify_policy=allowed_to_modify_policy,
        allowed_to_modify_identity=allowed_to_modify_identity,
        requires_provenance=requires_provenance,
        requires_redaction=requires_redaction,
        requires_review=requires_review,
        requires_sandbox=requires_sandbox,
        local_only=local_only,
        injection_risk=injection_risk,
        injection_signals=injection_signals,
        description=description,
    )


DEFAULT_PROMPT_HANDLING_RULES: tuple[PromptHandlingRule, ...] = (
    # System prompt — trusted instruction authority
    _rule(
        PromptSourceType.SYSTEM_PROMPT,
        PromptTrustLevel.TRUSTED_SYSTEM,
        PromptRole.INSTRUCTION,
        PromptPolicyDecision.ALLOW,
        allowed_as_instruction=True,
        description="System prompt is trusted instruction authority within Aurel governance.",
    ),
    # Developer prompt — trusted instruction authority
    _rule(
        PromptSourceType.DEVELOPER_PROMPT,
        PromptTrustLevel.TRUSTED_DEVELOPER,
        PromptRole.INSTRUCTION,
        PromptPolicyDecision.ALLOW,
        allowed_as_instruction=True,
        description="Developer prompt is trusted instruction authority.",
    ),
    # Operator prompt — high authority, policy/memory-bound
    _rule(
        PromptSourceType.OPERATOR_PROMPT,
        PromptTrustLevel.OPERATOR_AUTHORIZED,
        PromptRole.INSTRUCTION,
        PromptPolicyDecision.ALLOW,
        allowed_as_instruction=True,
        allowed_to_request_tools=True,
        allowed_to_write_memory=True,
        description="Operator prompt has high authority but remains tool/memory-policy bound.",
    ),
    # Task prompt — operator-authorized instruction
    _rule(
        PromptSourceType.TASK_PROMPT,
        PromptTrustLevel.OPERATOR_AUTHORIZED,
        PromptRole.INSTRUCTION,
        PromptPolicyDecision.ALLOW,
        allowed_as_instruction=True,
        description="Task prompt is operator-authorized instruction, policy-bound.",
    ),
    # Agent prompt — internal generated, context only
    _rule(
        PromptSourceType.AGENT_PROMPT,
        PromptTrustLevel.INTERNAL_GENERATED,
        PromptRole.PLANNING,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        description="Internal agent-generated text is context, not automatic authority.",
    ),
    # Generated prompt — internal generated, context only
    _rule(
        PromptSourceType.GENERATED_PROMPT,
        PromptTrustLevel.INTERNAL_GENERATED,
        PromptRole.CONTEXT,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        description="Generated text is context, not automatic authority.",
    ),
    # Tool output — untrusted data
    _rule(
        PromptSourceType.TOOL_OUTPUT,
        PromptTrustLevel.TOOL_OUTPUT_UNTRUSTED,
        PromptRole.DATA,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        requires_sandbox=True,
        injection_risk=PromptInjectionRisk.MEDIUM,
        description="Tool output is data/context, not command.",
    ),
    # Web content — external untrusted
    _rule(
        PromptSourceType.WEB_CONTENT,
        PromptTrustLevel.EXTERNAL_UNTRUSTED,
        PromptRole.DATA,
        PromptPolicyDecision.QUOTE_ONLY,
        allowed_as_instruction=False,
        requires_redaction=True,
        requires_sandbox=True,
        injection_risk=PromptInjectionRisk.HIGH,
        description="Web content may inform but never command.",
    ),
    # Email content — external untrusted
    _rule(
        PromptSourceType.EMAIL_CONTENT,
        PromptTrustLevel.EXTERNAL_UNTRUSTED,
        PromptRole.DATA,
        PromptPolicyDecision.QUOTE_ONLY,
        allowed_as_instruction=False,
        injection_risk=PromptInjectionRisk.HIGH,
        description="Email content is untrusted external content.",
    ),
    # File content — external untrusted
    _rule(
        PromptSourceType.FILE_CONTENT,
        PromptTrustLevel.EXTERNAL_UNTRUSTED,
        PromptRole.DATA,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        injection_risk=PromptInjectionRisk.MEDIUM,
        description="File content is content unless verified by a future resolver.",
    ),
    # Code content — external untrusted
    _rule(
        PromptSourceType.CODE_CONTENT,
        PromptTrustLevel.EXTERNAL_UNTRUSTED,
        PromptRole.DATA,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        injection_risk=PromptInjectionRisk.MEDIUM,
        description="Code content is content unless verified by a future resolver.",
    ),
    # Retrieved document — external untrusted
    _rule(
        PromptSourceType.RETRIEVED_DOCUMENT,
        PromptTrustLevel.EXTERNAL_UNTRUSTED,
        PromptRole.CONTEXT,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        injection_risk=PromptInjectionRisk.MEDIUM,
        description="Retrieved documents are context unless verified by a future resolver.",
    ),
    # Retrieved memory — context, not authority
    _rule(
        PromptSourceType.RETRIEVED_MEMORY,
        PromptTrustLevel.RETRIEVED_CONTEXT,
        PromptRole.CONTEXT,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        description="Retrieved memory is context, not automatic authority.",
    ),
    # External API content — external untrusted
    _rule(
        PromptSourceType.EXTERNAL_API_CONTENT,
        PromptTrustLevel.EXTERNAL_UNTRUSTED,
        PromptRole.DATA,
        PromptPolicyDecision.CONTEXT_ONLY,
        allowed_as_instruction=False,
        requires_sandbox=True,
        injection_risk=PromptInjectionRisk.HIGH,
        description="External API content is untrusted external content.",
    ),
    # Unknown source — deny posture
    _rule(
        PromptSourceType.UNKNOWN,
        PromptTrustLevel.UNKNOWN_UNTRUSTED,
        PromptRole.UNKNOWN,
        PromptPolicyDecision.DENY,
        allowed_as_instruction=False,
        allowed_as_context=False,
        requires_review=True,
        injection_risk=PromptInjectionRisk.HIGH,
        description="Unknown source cannot be trusted; deny by default.",
    ),
)

# ---------------------------------------------------------------------------
# Schema export
# ---------------------------------------------------------------------------


def export_prompt_policy_schema() -> dict[str, Any]:
    return {
        "schema_version": PROMPT_POLICY_CARD_SCHEMA_VERSION,
        "supported_versions": list(SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS),
        "required_fields": list(PROMPT_POLICY_REQUIRED_FIELDS),
        "optional_fields": list(PROMPT_POLICY_OPTIONAL_FIELDS),
        "forbidden_fields": sorted(PROMPT_POLICY_FORBIDDEN_FIELDS),
        "canonical_fields": list(PROMPT_POLICY_CANONICAL_FIELDS),
        "rule_required_fields": list(PROMPT_HANDLING_RULE_REQUIRED_FIELDS),
        "rule_optional_fields": list(PROMPT_HANDLING_RULE_OPTIONAL_FIELDS),
        "requirement_required_fields": list(PROMPT_BOUNDARY_REQUIREMENT_REQUIRED_FIELDS),
        "injection_signal_required_fields": list(PROMPT_INJECTION_SIGNAL_REQUIRED_FIELDS),
        "dangerous_field_names": sorted(PROMPT_POLICY_DANGEROUS_FIELD_NAMES),
        "dangerous_metadata_keys": sorted(PROMPT_POLICY_DANGEROUS_METADATA_KEYS),
        "trusted_prompt_sources": sorted(TRUSTED_PROMPT_SOURCES),
        "untrusted_prompt_sources": sorted(UNTRUSTED_PROMPT_SOURCES),
        "external_prompt_sources": sorted(EXTERNAL_PROMPT_SOURCES),
        "protected_prompt_sources": sorted(PROTECTED_PROMPT_SOURCES),
        "prompt_source_types": sorted(s.value for s in PromptSourceType),
        "prompt_trust_levels": sorted(t.value for t in PromptTrustLevel),
        "prompt_roles": sorted(r.value for r in PromptRole),
        "prompt_policy_decisions": sorted(d.value for d in PromptPolicyDecision),
        "prompt_injection_risks": sorted(r.value for r in PromptInjectionRisk),
    }


def get_prompt_policy_schema() -> dict[str, Any]:
    return export_prompt_policy_schema()


def is_supported_prompt_policy_schema_version(version: str) -> bool:
    if not isinstance(version, str) or not version.strip():
        return False
    return version in SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS


def validate_prompt_policy_schema_version(
    version: object,
) -> PromptPolicyValidationResult:
    errors: list[PromptPolicyValidationIssue] = []
    warnings: list[PromptPolicyValidationIssue] = []

    if not isinstance(version, str) or not version.strip():
        errors.append(
            PromptPolicyValidationIssue(
                code="MISSING_SCHEMA_VERSION",
                message=f"schema_version is required and must be one of: "
                f"{', '.join(SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )
    elif version not in SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS:
        errors.append(
            PromptPolicyValidationIssue(
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"schema_version '{version}' is not supported; "
                f"supported: {', '.join(SUPPORTED_PROMPT_POLICY_CARD_SCHEMA_VERSIONS)}",
                field="schema_version",
                severity="error",
            )
        )

    return PromptPolicyValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
