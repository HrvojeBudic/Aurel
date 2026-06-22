"""Validation rules for Agent Identity Card (P1.4.7)."""
from __future__ import annotations

import re

from .agent_identity_card import AurelAgentIdentityCard
from .agent_identity_card_policy import (
    AGENT_IDENTITY_CARD_VALIDATOR_VERSION,
    AgentIdentityCardConfig,
    AgentIdentityCardValidationResult,
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")

CARD_INVARIANT_KEY_RESOLVERS: dict[str, tuple[str, str]] = {
    "card_can_grant_authority": ("boundaries", "card_can_grant_authority"),
    "self_escalation_allowed": ("authority", "self_escalation_allowed"),
    "tool_access_implies_authority": ("authority", "tool_access_implies_authority"),
    "card_can_create_delegation": ("boundaries", "card_can_create_delegation"),
    "card_can_replace_operator": ("boundaries", "card_can_replace_operator"),
    "agent_type": ("agent", "agent_type"),
}


def _resolve_config_invariant_value(
    config: AgentIdentityCardConfig,
    key: str,
) -> bool | str | None:
    resolver = CARD_INVARIANT_KEY_RESOLVERS.get(key)
    if resolver is None:
        return None
    section_name, field_name = resolver
    section = getattr(config, section_name, None)
    if section is None:
        return None
    return getattr(section, field_name, None)


def validate_agent_identity_card_config(
    config: AgentIdentityCardConfig,
) -> AgentIdentityCardValidationResult:
    """Strictly validate agent identity card configuration."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    if config.applies_to_agent != "Aurel":
        errors.append('applies_to_agent must be "Aurel"')
    if config.card_class != "machine_readable_agent_identity":
        errors.append('card_class must be "machine_readable_agent_identity"')

    agent = config.agent
    if agent.agent_id != "aurel.local.operator.primary":
        errors.append('agent.agent_id must be "aurel.local.operator.primary"')
    if agent.agent_name != "Aurel":
        errors.append('agent.agent_name must be "Aurel"')
    if agent.agent_type != "ai_agent":
        errors.append('agent.agent_type must be "ai_agent"')
    if agent.agent_class != "sovereign_personal_agent":
        errors.append('agent.agent_class must be "sovereign_personal_agent"')
    if agent.identity_version != "1.4":
        errors.append('agent.identity_version must be "1.4"')
    if agent.deployment_scope != "single_operator_local_first":
        errors.append('agent.deployment_scope must be "single_operator_local_first"')
    if agent.machine_scope != "local":
        errors.append('agent.machine_scope must be "local"')

    authority = config.authority
    if authority.authority_source != "operator":
        errors.append('authority.authority_source must be "operator"')
    if authority.final_authority != "operator":
        errors.append('authority.final_authority must be "operator"')
    if authority.self_escalation_allowed is not False:
        errors.append("authority.self_escalation_allowed must be false")
    if authority.delegated_authority_required_for_actions is not True:
        errors.append("authority.delegated_authority_required_for_actions must be true")
    if authority.tool_access_implies_authority is not False:
        errors.append("authority.tool_access_implies_authority must be false")

    runtime = config.runtime
    if runtime.runtime_instance_id_strategy != "local_generated_uuid":
        errors.append('runtime.runtime_instance_id_strategy must be "local_generated_uuid"')
    if runtime.runtime_machine_scope != "local":
        errors.append('runtime.runtime_machine_scope must be "local"')
    if runtime.local_first is not True:
        errors.append("runtime.local_first must be true")

    taxonomy = config.identity_taxonomy
    if taxonomy.agent_identity != agent.agent_id:
        errors.append("identity_taxonomy.agent_identity must equal agent.agent_id")
    if not taxonomy.human_principal_identity.strip():
        errors.append("identity_taxonomy.human_principal_identity must be non-empty")
    if taxonomy.human_principal_identity == taxonomy.agent_identity:
        errors.append(
            "identity_taxonomy.human_principal_identity must differ from agent_identity"
        )

    boundaries = config.boundaries
    for field_name, expected in (
        ("card_can_grant_authority", False),
        ("card_can_change_identity_kernel", False),
        ("card_can_change_autonomy", False),
        ("card_can_create_delegation", False),
        ("card_can_authorize_tools", False),
        ("card_can_replace_operator", False),
        ("card_can_override_policy", False),
    ):
        if getattr(boundaries, field_name) is not expected:
            errors.append(f"boundaries.{field_name} must be {expected}")

    for invariant in config.invariants:
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
        resolved = _resolve_config_invariant_value(config, invariant.key)
        if resolved is None:
            errors.append(f"invariant[{invariant.id}]: unknown key {invariant.key!r}")
            continue
        if resolved != invariant.expected_value:
            errors.append(
                f"invariant[{invariant.id}]: expected_value {invariant.expected_value!r} "
                f"does not match config field {invariant.key}={resolved!r}"
            )
        if invariant.severity == "critical" and invariant.violation_action != "fail_build":
            critical_failures.append(
                f"invariant[{invariant.id}]: critical invariants must use fail_build"
            )

    valid = not errors and not critical_failures
    return AgentIdentityCardValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def _require_hash(value: str | None, label: str, errors: list[str]) -> None:
    if not value or not HEX64.match(value):
        errors.append(f"{label} must be a 64-character lowercase hex SHA-256 hash")


def validate_agent_identity_card(
    card: AurelAgentIdentityCard,
) -> AgentIdentityCardValidationResult:
    """Validate a built agent identity card."""
    config = AgentIdentityCardConfig(
        schema_version=card.schema_version,
        card_name=card.card_name,
        card_class=card.card_class,
        applies_to_agent=card.applies_to_agent,
        agent=card.agent,
        authority=card.authority,
        source_bindings=card.source_bindings,
        runtime=card.runtime,
        identity_taxonomy=card.identity_taxonomy,
        future_placeholders=card.future_placeholders,
        boundaries=card.boundaries,
        invariants=card.invariants,
        notes=card.notes,
    )
    config_result = validate_agent_identity_card_config(config)
    errors = list(config_result.errors)
    warnings = list(config_result.warnings)
    critical_failures = list(config_result.critical_failures)

    bindings = card.source_bindings
    _require_hash(bindings.identity_kernel_hash, "source_bindings.identity_kernel_hash", errors)
    _require_hash(bindings.persona_manifest_hash, "source_bindings.persona_manifest_hash", errors)
    _require_hash(
        bindings.operator_contract_hash,
        "source_bindings.operator_contract_hash",
        errors,
    )
    _require_hash(
        bindings.communication_modes_hash,
        "source_bindings.communication_modes_hash",
        errors,
    )
    _require_hash(
        bindings.identity_prompt_compiler_policy_hash,
        "source_bindings.identity_prompt_compiler_policy_hash",
        errors,
    )
    _require_hash(bindings.self_model_hash, "source_bindings.self_model_hash", errors)

    runtime_id = card.runtime.runtime_instance_id
    if not runtime_id or not runtime_id.strip():
        errors.append("runtime.runtime_instance_id must be non-empty on built card")
    elif not runtime_id.startswith("aurel-runtime-"):
        errors.append('runtime.runtime_instance_id must start with "aurel-runtime-"')

    if not card.runtime.runtime_version or not card.runtime.runtime_version.strip():
        errors.append("runtime.runtime_version must be non-empty on built card")

    if not card.stable_agent_identity_hash or not HEX64.match(card.stable_agent_identity_hash):
        errors.append("stable_agent_identity_hash must be a valid SHA-256 hash")
    if not card.runtime_agent_identity_card_hash or not HEX64.match(
        card.runtime_agent_identity_card_hash
    ):
        errors.append("runtime_agent_identity_card_hash must be a valid SHA-256 hash")

    valid = not errors and not critical_failures
    return AgentIdentityCardValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def validator_version() -> str:
    """Return agent identity card validator version."""
    return AGENT_IDENTITY_CARD_VALIDATOR_VERSION
