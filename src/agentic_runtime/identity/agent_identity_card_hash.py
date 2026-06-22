"""Deterministic hashing for Agent Identity Card (P1.4.7)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .agent_identity_card import AurelAgentIdentityCard
from .agent_identity_card_policy import AgentIdentityInvariant


def _invariant_to_dict(invariant: AgentIdentityInvariant) -> dict[str, Any]:
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


def _agent_to_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    agent = card.agent
    return {
        "agent_class": agent.agent_class,
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "agent_type": agent.agent_type,
        "deployment_scope": agent.deployment_scope,
        "identity_version": agent.identity_version,
        "machine_scope": agent.machine_scope,
    }


def _authority_to_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    authority = card.authority
    return {
        "authority_source": authority.authority_source,
        "delegated_authority_required_for_actions": authority.delegated_authority_required_for_actions,
        "final_authority": authority.final_authority,
        "self_escalation_allowed": authority.self_escalation_allowed,
        "tool_access_implies_authority": authority.tool_access_implies_authority,
    }


def _source_bindings_to_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    bindings = card.source_bindings
    return {
        "communication_modes_hash": bindings.communication_modes_hash,
        "identity_kernel_hash": bindings.identity_kernel_hash,
        "identity_prompt_compiler_policy_hash": bindings.identity_prompt_compiler_policy_hash,
        "operator_contract_hash": bindings.operator_contract_hash,
        "persona_manifest_hash": bindings.persona_manifest_hash,
        "self_model_hash": bindings.self_model_hash,
    }


def _taxonomy_to_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    taxonomy = card.identity_taxonomy
    return {
        "agent_identity": taxonomy.agent_identity,
        "delegated_identity": taxonomy.delegated_identity,
        "human_principal_identity": taxonomy.human_principal_identity,
        "model_identity": taxonomy.model_identity,
        "workload_identity": taxonomy.workload_identity,
    }


def _boundaries_to_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    boundaries = card.boundaries
    return {
        "card_can_authorize_tools": boundaries.card_can_authorize_tools,
        "card_can_change_autonomy": boundaries.card_can_change_autonomy,
        "card_can_change_identity_kernel": boundaries.card_can_change_identity_kernel,
        "card_can_create_delegation": boundaries.card_can_create_delegation,
        "card_can_grant_authority": boundaries.card_can_grant_authority,
        "card_can_override_policy": boundaries.card_can_override_policy,
        "card_can_replace_operator": boundaries.card_can_replace_operator,
    }


def _notes_to_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    return {} if card.notes is None else dict(card.notes)


def stable_identity_to_canonical_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    """Canonical dict for stable agent identity hash (excludes runtime instance fields)."""
    invariants = sorted(
        (_invariant_to_dict(inv) for inv in card.invariants),
        key=lambda item: item["id"],
    )
    return {
        "agent": _agent_to_dict(card),
        "applies_to_agent": card.applies_to_agent,
        "authority": _authority_to_dict(card),
        "boundaries": _boundaries_to_dict(card),
        "card_class": card.card_class,
        "card_name": card.card_name,
        "identity_taxonomy": _taxonomy_to_dict(card),
        "invariants": invariants,
        "notes": _notes_to_dict(card),
        "schema_version": card.schema_version,
        "source_bindings": _source_bindings_to_dict(card),
    }


def runtime_card_to_canonical_dict(card: AurelAgentIdentityCard) -> dict[str, Any]:
    """Canonical dict for runtime card hash (includes runtime identity fields)."""
    stable = stable_identity_to_canonical_dict(card)
    runtime = card.runtime
    stable["runtime"] = {
        "local_first": runtime.local_first,
        "runtime_instance_id": runtime.runtime_instance_id,
        "runtime_instance_id_strategy": runtime.runtime_instance_id_strategy,
        "runtime_machine_scope": runtime.runtime_machine_scope,
        "runtime_version": runtime.runtime_version,
    }
    return stable


def _hash_canonical(canonical: dict[str, Any]) -> str:
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_stable_agent_identity_hash(card: AurelAgentIdentityCard) -> str:
    """Compute deterministic SHA-256 stable agent identity hash."""
    return _hash_canonical(stable_identity_to_canonical_dict(card))


def compute_runtime_agent_identity_card_hash(card: AurelAgentIdentityCard) -> str:
    """Compute deterministic SHA-256 runtime agent identity card hash."""
    return _hash_canonical(runtime_card_to_canonical_dict(card))
