"""Attestation for Identity Prompt Context (P1.4.5)."""
from __future__ import annotations

import json
from pathlib import Path

from .identity_context import IdentityPromptAttestation, IdentityPromptCompileResult


def build_identity_prompt_attestation(
    result: IdentityPromptCompileResult,
) -> IdentityPromptAttestation:
    """Build attestation record from compile result."""
    if not result.valid or result.context is None or result.context_hash is None:
        bundle_hashes = ("", "", "", "", "")
        selected_mode = ""
        compiler_version = ""
        if result.context is not None:
            bundle = result.context.source_bundle
            bundle_hashes = (
                bundle.identity_kernel_hash,
                bundle.persona_manifest_hash,
                bundle.operator_contract_hash,
                bundle.communication_modes_hash,
                bundle.compiler_policy_hash,
            )
            selected_mode = result.context.selected_mode
            compiler_version = result.context.compiler_version
        return IdentityPromptAttestation(
            schema_version="1.0",
            context_hash=result.context_hash or "",
            hash_algorithm="sha256",
            compiler_version=compiler_version,
            identity_kernel_hash=bundle_hashes[0],
            persona_manifest_hash=bundle_hashes[1],
            operator_contract_hash=bundle_hashes[2],
            communication_modes_hash=bundle_hashes[3],
            compiler_policy_hash=bundle_hashes[4],
            selected_mode=selected_mode,
            validation_status="invalid",
            critical_failures=result.critical_failures,
        )

    context = result.context
    bundle = context.source_bundle
    return IdentityPromptAttestation(
        schema_version=context.schema_version,
        context_hash=result.context_hash,
        hash_algorithm="sha256",
        compiler_version=context.compiler_version,
        identity_kernel_hash=bundle.identity_kernel_hash,
        persona_manifest_hash=bundle.persona_manifest_hash,
        operator_contract_hash=bundle.operator_contract_hash,
        communication_modes_hash=bundle.communication_modes_hash,
        compiler_policy_hash=bundle.compiler_policy_hash,
        selected_mode=bundle.selected_mode,
        validation_status="valid",
        critical_failures=(),
    )


def write_identity_prompt_attestation(
    attestation: IdentityPromptAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "context_hash": attestation.context_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "compiler_version": attestation.compiler_version,
        "identity_kernel_hash": attestation.identity_kernel_hash,
        "persona_manifest_hash": attestation.persona_manifest_hash,
        "operator_contract_hash": attestation.operator_contract_hash,
        "communication_modes_hash": attestation.communication_modes_hash,
        "compiler_policy_hash": attestation.compiler_policy_hash,
        "selected_mode": attestation.selected_mode,
        "validation_status": attestation.validation_status,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
