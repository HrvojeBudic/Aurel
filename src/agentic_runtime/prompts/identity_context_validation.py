"""Validation rules for Identity Prompt Context Compiler (P1.4.5)."""
from __future__ import annotations

from .compiler_policy import (
    IPC_VALIDATOR_VERSION,
    IdentityPromptCompilerPolicy,
    IdentityPromptCompilerPolicyValidationResult,
)
from .identity_context import IdentityPromptContext, IdentityPromptValidationResult

POLICY_INVARIANT_KEY_RESOLVERS: dict[str, tuple[str, str]] = {
    "raw_yaml_in_prompt_forbidden": ("safety", "raw_yaml_in_prompt_forbidden"),
    "identity_kernel_overrides_all": ("dominance", "identity_kernel_overrides_all"),
    "operator_contract_overrides_persona_and_mode": (
        "dominance",
        "operator_contract_overrides_persona_and_mode",
    ),
    "mode_never_overrides_authority": ("dominance", "mode_never_overrides_authority"),
    "include_no_self_escalation": ("safety", "include_no_self_escalation"),
    "include_capability_honesty": ("safety", "include_capability_honesty"),
    "include_operator_final_authority": ("safety", "include_operator_final_authority"),
    "include_no_action_authority_statement": ("safety", "include_no_action_authority_statement"),
}


def _resolve_policy_invariant_value(
    policy: IdentityPromptCompilerPolicy,
    key: str,
) -> bool | None:
    resolver = POLICY_INVARIANT_KEY_RESOLVERS.get(key)
    if resolver is None:
        return None
    section_name, field_name = resolver
    section = getattr(policy, section_name, None)
    if section is None:
        return None
    return getattr(section, field_name, None)


def _must_equal(actual: bool, expected: bool, label: str, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected}, got {actual}")


def validate_identity_prompt_compiler_policy(
    policy: IdentityPromptCompilerPolicy,
) -> IdentityPromptCompilerPolicyValidationResult:
    """Strictly validate compiler policy configuration."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    if policy.applies_to_agent != "Aurel":
        errors.append('applies_to_agent must be "Aurel"')
    if policy.compiler_class != "safe_identity_context_compiler":
        errors.append('compiler_class must be "safe_identity_context_compiler"')

    req = policy.source_requirements
    for field_name, expected in (
        ("identity_kernel_required", True),
        ("persona_manifest_required", True),
        ("operator_contract_required", True),
        ("communication_mode_registry_required", True),
        ("selected_mode_required", True),
    ):
        actual = getattr(req, field_name)
        if actual is not expected:
            errors.append(f"source_requirements.{field_name} must be {expected}")

    safety = policy.safety
    for field_name, expected in (
        ("raw_yaml_in_prompt_forbidden", True),
        ("raw_config_dump_forbidden", True),
        ("include_source_hashes", True),
        ("include_authority_boundaries", True),
        ("include_capability_honesty", True),
        ("include_no_self_escalation", True),
        ("include_operator_final_authority", True),
        ("include_mode_boundaries", True),
        ("include_no_tool_authority_statement", True),
        ("include_no_action_authority_statement", True),
        ("include_no_memory_write_statement", True),
        ("include_no_policy_bypass_statement", True),
        ("include_no_canonization_statement", True),
    ):
        actual = getattr(safety, field_name)
        if actual is not expected:
            errors.append(f"safety.{field_name} must be {expected}")

    dominance = policy.dominance
    for field_name, expected in (
        ("identity_kernel_overrides_all", True),
        ("operator_contract_overrides_persona_and_mode", True),
        ("persona_boundaries_override_mode_style", True),
        ("mode_never_overrides_authority", True),
        ("lower_layer_contradiction_fails", True),
    ):
        actual = getattr(dominance, field_name)
        if actual is not expected:
            errors.append(f"dominance.{field_name} must be {expected}")

    sections = policy.prompt_sections
    for field_name, expected in (
        ("include_agent_identity_section", True),
        ("include_operator_relationship_section", True),
        ("include_persona_expression_section", True),
        ("include_active_mode_section", True),
        ("include_authority_boundaries_section", True),
        ("include_capability_honesty_section", True),
        ("include_non_goals_section", True),
        ("include_source_integrity_section", True),
    ):
        actual = getattr(sections, field_name)
        if actual is not expected:
            errors.append(f"prompt_sections.{field_name} must be {expected}")

    for invariant in policy.invariants:
        if not invariant.id.strip():
            errors.append("invariant id must be non-empty")
        if not invariant.key.strip():
            errors.append(f"invariant[{invariant.id}].key must be non-empty")
        if not invariant.statement.strip():
            errors.append(f"invariant[{invariant.id}].statement must be non-empty")
        if not invariant.rationale.strip():
            errors.append(f"invariant[{invariant.id}].rationale must be non-empty")
        if invariant.severity == "critical" and invariant.mutable:
            errors.append(f"invariant[{invariant.id}]: critical invariants must be immutable")
        resolved = _resolve_policy_invariant_value(policy, invariant.key)
        if resolved is None:
            errors.append(f"invariant[{invariant.id}]: unknown key {invariant.key!r}")
            continue
        if resolved != invariant.expected_value:
            errors.append(
                f"invariant[{invariant.id}]: expected_value {invariant.expected_value} "
                f"does not match policy field {invariant.key}={resolved}"
            )
        if invariant.severity == "critical" and invariant.violation_action != "fail_compile":
            critical_failures.append(
                f"invariant[{invariant.id}]: critical invariants must use fail_compile"
            )

    valid = not errors and not critical_failures
    return IdentityPromptCompilerPolicyValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def _require_phrase(
    text: str,
    phrases: tuple[str, ...],
    label: str,
    errors: list[str],
) -> None:
    if not any(phrase.lower() in text for phrase in phrases):
        errors.append(f"missing required content: {label}")


def validate_identity_prompt_context(context: IdentityPromptContext) -> IdentityPromptValidationResult:
    """Validate compiled prompt context required content."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    integrity_text = "\n".join(context.source_integrity_section).lower()
    capability_text = "\n".join(context.capability_honesty_section).lower()
    authority_text = "\n".join(context.authority_boundaries_section).lower()
    non_goals_text = "\n".join(context.non_goals_section).lower()
    operator_text = "\n".join(context.operator_relationship_section).lower()

    _require_phrase(operator_text, ("final authority", "operator remains final authority"), "operator final authority", errors)
    _require_phrase(authority_text, ("self-escalation", "self escalation", "cannot raise its own authority"), "no-self-escalation", errors)
    _require_phrase(capability_text, ("capability honesty", "unverified capabilit"), "capability honesty", errors)
    _require_phrase(authority_text, ("tool authority", "does not grant tool", "no tool authority"), "no tool authority", errors)
    _require_phrase(authority_text + non_goals_text, ("action authority", "does not authorize action", "no action authority"), "no action authority", errors)
    _require_phrase(authority_text + non_goals_text, ("autonomy",), "no autonomy change", errors)
    _require_phrase(authority_text + non_goals_text, ("policy bypass",), "no policy bypass", errors)
    _require_phrase(authority_text + non_goals_text, ("memory write", "memory writes"), "no memory write authorization", errors)
    _require_phrase(authority_text + non_goals_text, ("canoniz",), "no canonization authorization", errors)

    if not context.selected_mode.strip():
        errors.append("selected_mode must be non-empty")

    bundle = context.source_bundle
    for label, value in (
        ("identity_kernel_hash", bundle.identity_kernel_hash),
        ("persona_manifest_hash", bundle.persona_manifest_hash),
        ("operator_contract_hash", bundle.operator_contract_hash),
        ("communication_modes_hash", bundle.communication_modes_hash),
        ("compiler_policy_hash", bundle.compiler_policy_hash),
    ):
        if not value or len(value) != 64:
            errors.append(f"missing or invalid {label}")

    if bundle.identity_kernel_hash not in integrity_text:
        errors.append("source_integrity_section missing identity_kernel_hash")
    if bundle.selected_mode.lower() not in integrity_text:
        errors.append("source_integrity_section missing selected_mode")
    if context.compiler_version.lower() not in integrity_text:
        errors.append("source_integrity_section missing compiler_version")

    if context.selected_mode == "HERETIC":
        mode_text = "\n".join(context.active_mode_section).lower()
        heretic_checks = (
            (("candidate-only", "candidate only"), "HERETIC candidate-only"),
            (("real-world side effect", "no real-world side effect"), "HERETIC no real-world side effects"),
            (("modify identity", "cannot modify identity", "no identity modification"), "HERETIC no identity modification"),
            (("modify policy", "cannot modify policy", "no policy modification"), "HERETIC no policy modification"),
            (("modify memory", "cannot modify memory", "no memory modification"), "HERETIC no memory modification"),
            (("modify tool", "cannot modify tool", "no tool modification"), "HERETIC no tool modification"),
            (("modify autonomy", "cannot modify autonomy", "no autonomy modification"), "HERETIC no autonomy modification"),
            (("canoniz", "cannot canonize"), "HERETIC no direct canonization"),
        )
        for phrases, label in heretic_checks:
            _require_phrase(mode_text, phrases, label, errors)

    for err in errors:
        critical_failures.append(err)

    valid = not errors
    return IdentityPromptValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


__all__ = [
    "IPC_VALIDATOR_VERSION",
    "validate_identity_prompt_compiler_policy",
    "validate_identity_prompt_context",
]
