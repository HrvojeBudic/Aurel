"""Deterministic hashing for Identity Prompt Context (P1.4.5)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .compiler_policy import IdentityPromptCompilerInvariant, IdentityPromptCompilerPolicy
from .identity_context import IdentityPromptContext, IdentityPromptContextHash


def _invariant_to_dict(invariant: IdentityPromptCompilerInvariant) -> dict[str, Any]:
    return {
        "expected_value": invariant.expected_value,
        "id": invariant.id,
        "key": invariant.key,
        "mutable": invariant.mutable,
        "rationale": invariant.rationale,
        "severity": invariant.severity,
        "statement": invariant.statement,
        "violation_action": invariant.violation_action,
    }


def policy_to_canonical_dict(policy: IdentityPromptCompilerPolicy) -> dict[str, Any]:
    """Convert compiler policy to a canonical primitive dict for hashing."""
    notes: dict[str, Any] = {} if policy.notes is None else dict(policy.notes)
    invariants = sorted(
        (_invariant_to_dict(inv) for inv in policy.invariants),
        key=lambda item: item["id"],
    )
    req = policy.source_requirements
    safety = policy.safety
    dominance = policy.dominance
    sections = policy.prompt_sections
    return {
        "applies_to_agent": policy.applies_to_agent,
        "compiler_class": policy.compiler_class,
        "compiler_version": policy.compiler_version,
        "dominance": {
            "identity_kernel_overrides_all": dominance.identity_kernel_overrides_all,
            "lower_layer_contradiction_fails": dominance.lower_layer_contradiction_fails,
            "mode_never_overrides_authority": dominance.mode_never_overrides_authority,
            "operator_contract_overrides_persona_and_mode": (
                dominance.operator_contract_overrides_persona_and_mode
            ),
            "persona_boundaries_override_mode_style": (
                dominance.persona_boundaries_override_mode_style
            ),
        },
        "invariants": invariants,
        "name": policy.name,
        "notes": notes,
        "prompt_sections": {
            "include_active_mode_section": sections.include_active_mode_section,
            "include_agent_identity_section": sections.include_agent_identity_section,
            "include_authority_boundaries_section": sections.include_authority_boundaries_section,
            "include_capability_honesty_section": sections.include_capability_honesty_section,
            "include_non_goals_section": sections.include_non_goals_section,
            "include_operator_relationship_section": sections.include_operator_relationship_section,
            "include_persona_expression_section": sections.include_persona_expression_section,
            "include_source_integrity_section": sections.include_source_integrity_section,
        },
        "safety": {
            "include_authority_boundaries": safety.include_authority_boundaries,
            "include_capability_honesty": safety.include_capability_honesty,
            "include_compiler_version": safety.include_compiler_version,
            "include_mode_boundaries": safety.include_mode_boundaries,
            "include_no_action_authority_statement": safety.include_no_action_authority_statement,
            "include_no_canonization_statement": safety.include_no_canonization_statement,
            "include_no_memory_write_statement": safety.include_no_memory_write_statement,
            "include_no_policy_bypass_statement": safety.include_no_policy_bypass_statement,
            "include_no_self_escalation": safety.include_no_self_escalation,
            "include_no_tool_authority_statement": safety.include_no_tool_authority_statement,
            "include_operator_final_authority": safety.include_operator_final_authority,
            "include_source_hashes": safety.include_source_hashes,
            "raw_config_dump_forbidden": safety.raw_config_dump_forbidden,
            "raw_yaml_in_prompt_forbidden": safety.raw_yaml_in_prompt_forbidden,
        },
        "schema_version": policy.schema_version,
        "source_requirements": {
            "communication_mode_registry_required": req.communication_mode_registry_required,
            "identity_kernel_required": req.identity_kernel_required,
            "operator_contract_required": req.operator_contract_required,
            "persona_manifest_required": req.persona_manifest_required,
            "selected_mode_required": req.selected_mode_required,
        },
    }


def compute_identity_prompt_compiler_policy_hash(
    policy: IdentityPromptCompilerPolicy,
) -> IdentityPromptContextHash:
    """Compute deterministic SHA-256 hash of canonical compiler policy."""
    canonical = policy_to_canonical_dict(policy)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return IdentityPromptContextHash(algorithm="sha256", value=digest)


def context_to_canonical_dict(context: IdentityPromptContext) -> dict[str, Any]:
    """Convert compiled context to a canonical primitive dict for hashing."""
    bundle = context.source_bundle
    return {
        "active_mode_section": list(context.active_mode_section),
        "agent_class": context.agent_class,
        "agent_identity_section": list(context.agent_identity_section),
        "agent_name": context.agent_name,
        "authority_boundaries_section": list(context.authority_boundaries_section),
        "capability_honesty_section": list(context.capability_honesty_section),
        "compiler_version": context.compiler_version,
        "non_goals_section": list(context.non_goals_section),
        "operator_relationship_section": list(context.operator_relationship_section),
        "persona_expression_section": list(context.persona_expression_section),
        "schema_version": context.schema_version,
        "selected_mode": context.selected_mode,
        "source_bundle": {
            "communication_modes_hash": bundle.communication_modes_hash,
            "compiler_policy_hash": bundle.compiler_policy_hash,
            "identity_kernel_hash": bundle.identity_kernel_hash,
            "operator_contract_hash": bundle.operator_contract_hash,
            "persona_manifest_hash": bundle.persona_manifest_hash,
            "selected_mode": bundle.selected_mode,
        },
        "source_integrity_section": list(context.source_integrity_section),
    }


def compute_identity_prompt_context_hash(context: IdentityPromptContext) -> IdentityPromptContextHash:
    """Compute deterministic SHA-256 hash of canonical context representation."""
    canonical = context_to_canonical_dict(context)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return IdentityPromptContextHash(algorithm="sha256", value=digest)
