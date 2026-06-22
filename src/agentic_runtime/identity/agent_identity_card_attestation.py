"""Attestation for Agent Identity Card (P1.4.7)."""
from __future__ import annotations

import json
from pathlib import Path

from .agent_identity_card import AgentIdentityCardAttestation, AurelAgentIdentityCard
from .agent_identity_card_policy import AgentIdentityCardValidationResult


def build_agent_identity_card_attestation(
    card: AurelAgentIdentityCard,
    validation: AgentIdentityCardValidationResult,
) -> AgentIdentityCardAttestation:
    """Build attestation record for an agent identity card."""
    bindings = card.source_bindings
    status = "valid" if validation.valid else "invalid"
    return AgentIdentityCardAttestation(
        schema_version=card.schema_version,
        stable_agent_identity_hash=card.stable_agent_identity_hash or "",
        runtime_agent_identity_card_hash=card.runtime_agent_identity_card_hash or "",
        hash_algorithm="sha256",
        agent_id=card.agent.agent_id,
        agent_name=card.agent.agent_name,
        runtime_instance_id=card.runtime.runtime_instance_id or "",
        identity_kernel_hash=bindings.identity_kernel_hash or "",
        persona_manifest_hash=bindings.persona_manifest_hash or "",
        operator_contract_hash=bindings.operator_contract_hash or "",
        communication_modes_hash=bindings.communication_modes_hash or "",
        identity_prompt_compiler_policy_hash=bindings.identity_prompt_compiler_policy_hash or "",
        self_model_hash=bindings.self_model_hash or "",
        validation_status=status,
        critical_failures=validation.critical_failures,
    )


def write_agent_identity_card_attestation(
    attestation: AgentIdentityCardAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "stable_agent_identity_hash": attestation.stable_agent_identity_hash,
        "runtime_agent_identity_card_hash": attestation.runtime_agent_identity_card_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "agent_id": attestation.agent_id,
        "agent_name": attestation.agent_name,
        "runtime_instance_id": attestation.runtime_instance_id,
        "identity_kernel_hash": attestation.identity_kernel_hash,
        "persona_manifest_hash": attestation.persona_manifest_hash,
        "operator_contract_hash": attestation.operator_contract_hash,
        "communication_modes_hash": attestation.communication_modes_hash,
        "identity_prompt_compiler_policy_hash": attestation.identity_prompt_compiler_policy_hash,
        "self_model_hash": attestation.self_model_hash,
        "validation_status": attestation.validation_status,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
