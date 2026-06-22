"""Attestation for Aurel Self-Model (P1.4.6)."""
from __future__ import annotations

import json
from pathlib import Path

from .self_model import AurelSelfModel, SelfModelAttestation, SelfModelValidationResult
from .self_model_hash import compute_self_model_hash


def build_self_model_attestation(
    model: AurelSelfModel,
    validation: SelfModelValidationResult,
) -> SelfModelAttestation:
    """Build attestation record for a self-model."""
    bundle = model.source_bundle
    model_hash = compute_self_model_hash(model)
    status = "valid" if validation.valid else "invalid"
    return SelfModelAttestation(
        schema_version=model.schema_version,
        self_model_hash=model_hash.value,
        hash_algorithm=model_hash.algorithm,
        identity_kernel_hash=bundle.identity_kernel_hash,
        persona_manifest_hash=bundle.persona_manifest_hash,
        operator_contract_hash=bundle.operator_contract_hash,
        communication_modes_hash=bundle.communication_modes_hash,
        identity_prompt_compiler_policy_hash=bundle.identity_prompt_compiler_policy_hash,
        identity_prompt_context_hash=bundle.identity_prompt_context_hash,
        validation_status=status,
        critical_failures=validation.critical_failures,
    )


def write_self_model_attestation(
    attestation: SelfModelAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "self_model_hash": attestation.self_model_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "identity_kernel_hash": attestation.identity_kernel_hash,
        "persona_manifest_hash": attestation.persona_manifest_hash,
        "operator_contract_hash": attestation.operator_contract_hash,
        "communication_modes_hash": attestation.communication_modes_hash,
        "identity_prompt_compiler_policy_hash": attestation.identity_prompt_compiler_policy_hash,
        "identity_prompt_context_hash": attestation.identity_prompt_context_hash,
        "validation_status": attestation.validation_status,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
