"""Identity-related CLI command handlers (P1.4.7-MG extraction)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .common import optional_cli_path, repo_root

if TYPE_CHECKING:
    from ..identity.source_attestation import SourceAttestation

def _identity_kernel_path(args: argparse.Namespace) -> Path:
    if getattr(args, "kernel_path", None):
        return Path(args.kernel_path)
    return repo_root() / "config" / "aurel" / "identity_kernel.yaml"


def _identity_kernel_show_payload(kernel, kernel_hash: str) -> dict:
    return {
        "name": kernel.name,
        "class": kernel.agent_class,
        "primary_operator": kernel.primary_operator,
        "final_authority": kernel.final_authority,
        "local_first": kernel.local_first,
        "operator_final_authority": kernel.immutables.operator_final_authority,
        "self_escalation_allowed": kernel.immutables.self_escalation_allowed,
        "hidden_goals_allowed": kernel.immutables.hidden_goals_allowed,
        "identity_replacement_allowed": kernel.immutables.identity_replacement_allowed,
        "kernel_hash": kernel_hash,
    }


def cmd_identity_kernel_show(args: argparse.Namespace) -> int:
    from ..identity.kernel_hash import compute_identity_kernel_hash
    from ..identity.kernel import load_identity_kernel

    path = _identity_kernel_path(args)
    try:
        kernel = load_identity_kernel(path)
        kernel_hash = compute_identity_kernel_hash(kernel).value
        payload = _identity_kernel_show_payload(kernel, kernel_hash)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"identity kernel: {kernel.name}")
            print(f"  class: {kernel.agent_class}")
            print(f"  final_authority: {kernel.final_authority}")
            print(f"  kernel_hash: {kernel_hash}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"identity kernel show failed: {e}")
        return 1


def cmd_identity_kernel_validate(args: argparse.Namespace) -> int:
    from ..identity.kernel import load_identity_kernel
    from ..identity.kernel_validation import validate_identity_kernel

    path = _identity_kernel_path(args)
    try:
        kernel = load_identity_kernel(path)
        result = validate_identity_kernel(kernel)
        payload = {
            "valid": result.valid,
            "config_path": str(path),
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "critical_failures": list(result.critical_failures),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif result.valid:
            print("identity kernel: valid")
            print(f"  path: {path}")
        else:
            print("identity kernel: invalid")
            for err in result.errors:
                print(f"  - {err}")
        return 0 if result.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"identity kernel validate failed: {e}")
        return 1


def cmd_identity_kernel_hash(args: argparse.Namespace) -> int:
    from ..identity.kernel_hash import compute_identity_kernel_hash
    from ..identity.kernel import load_identity_kernel

    path = _identity_kernel_path(args)
    try:
        kernel = load_identity_kernel(path)
        kernel_hash = compute_identity_kernel_hash(kernel)
        payload = {
            "algorithm": kernel_hash.algorithm,
            "value": kernel_hash.value,
            "config_path": str(path),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(kernel_hash.value)
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"identity kernel hash failed: {e}")
        return 1


def cmd_identity_kernel_attest(args: argparse.Namespace) -> int:
    from ..identity.kernel import load_identity_kernel
    from ..identity.kernel_validation import (
        build_identity_kernel_attestation,
        write_identity_kernel_attestation,
    )

    path = _identity_kernel_path(args)
    try:
        kernel = load_identity_kernel(path)
        attestation = build_identity_kernel_attestation(kernel, path)
        if args.write:
            out_path = write_identity_kernel_attestation(
                attestation,
                Path(args.write),
            )
        else:
            out_path = None
        payload = {
            "schema_version": attestation.schema_version,
            "kernel_hash": attestation.kernel_hash,
            "hash_algorithm": attestation.hash_algorithm,
            "config_path": attestation.config_path,
            "validation_status": attestation.validation_status,
            "validator_version": attestation.validator_version,
            "critical_failures": list(attestation.critical_failures),
        }
        if out_path is not None:
            payload["attestation_path"] = str(out_path)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"validation_status: {attestation.validation_status}")
            print(f"kernel_hash: {attestation.kernel_hash}")
            if out_path is not None:
                print(f"written: {out_path}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"identity kernel attest failed: {e}")
        return 1


def _persona_manifest_path(args: argparse.Namespace) -> Path:
    if getattr(args, "persona_path", None):
        return Path(args.persona_path)
    return repo_root() / "config" / "aurel" / "persona_manifest.yaml"


def _persona_show_payload(manifest, persona_hash: str) -> dict:
    return {
        "manifest_name": manifest.name,
        "applies_to_agent": manifest.applies_to_agent,
        "manifest_class": manifest.manifest_class,
        "authority_level": manifest.authority_level,
        "can_grant_permissions": manifest.can_grant_permissions,
        "can_override_identity_kernel": manifest.can_override_identity_kernel,
        "can_override_policy": manifest.can_override_policy,
        "can_change_autonomy": manifest.can_change_autonomy,
        "never_claim_unverified_capability": manifest.honesty.never_claim_unverified_capability,
        "persona_hash": persona_hash,
    }


def cmd_identity_persona_show(args: argparse.Namespace) -> int:
    from ..identity.persona import load_persona_manifest
    from ..identity.persona_hash import compute_persona_manifest_hash

    path = _persona_manifest_path(args)
    try:
        manifest = load_persona_manifest(path)
        persona_hash = compute_persona_manifest_hash(manifest).value
        payload = _persona_show_payload(manifest, persona_hash)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"persona manifest: {manifest.name}")
            print(f"  applies_to_agent: {manifest.applies_to_agent}")
            print(f"  manifest_class: {manifest.manifest_class}")
            print(f"  authority_level: {manifest.authority_level}")
            print(f"  persona_hash: {persona_hash}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"persona show failed: {e}")
        return 1


def cmd_identity_persona_validate(args: argparse.Namespace) -> int:
    from ..identity.persona import load_persona_manifest
    from ..identity.persona_validation import validate_persona_manifest

    path = _persona_manifest_path(args)
    try:
        manifest = load_persona_manifest(path)
        result = validate_persona_manifest(manifest)
        payload = {
            "valid": result.valid,
            "config_path": str(path),
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "critical_failures": list(result.critical_failures),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif result.valid:
            print("persona manifest: valid")
            print(f"  path: {path}")
        else:
            print("persona manifest: invalid")
            for err in result.errors:
                print(f"  - {err}")
        return 0 if result.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"persona validate failed: {e}")
        return 1


def cmd_identity_persona_hash(args: argparse.Namespace) -> int:
    from ..identity.persona import load_persona_manifest
    from ..identity.persona_hash import compute_persona_manifest_hash

    path = _persona_manifest_path(args)
    try:
        manifest = load_persona_manifest(path)
        persona_hash = compute_persona_manifest_hash(manifest)
        payload = {
            "algorithm": persona_hash.algorithm,
            "value": persona_hash.value,
            "config_path": str(path),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(persona_hash.value)
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"persona hash failed: {e}")
        return 1


def cmd_identity_persona_attest(args: argparse.Namespace) -> int:
    from ..identity.persona import load_persona_manifest
    from ..identity.persona_validation import (
        build_persona_manifest_attestation,
        write_persona_manifest_attestation,
    )

    path = _persona_manifest_path(args)
    try:
        manifest = load_persona_manifest(path)
        attestation = build_persona_manifest_attestation(manifest, path)
        out_path = None
        if args.write:
            out_path = write_persona_manifest_attestation(attestation, Path(args.write))
        payload = {
            "schema_version": attestation.schema_version,
            "persona_hash": attestation.persona_hash,
            "hash_algorithm": attestation.hash_algorithm,
            "config_path": attestation.config_path,
            "validation_status": attestation.validation_status,
            "validator_version": attestation.validator_version,
            "critical_failures": list(attestation.critical_failures),
        }
        if out_path is not None:
            payload["attestation_path"] = str(out_path)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"validation_status: {attestation.validation_status}")
            print(f"persona_hash: {attestation.persona_hash}")
            if out_path is not None:
                print(f"written: {out_path}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"persona attest failed: {e}")
        return 1


def cmd_identity_persona_summary(args: argparse.Namespace) -> int:
    from ..identity.persona import load_persona_manifest
    from ..identity.persona_summary import (
        build_persona_safe_summary,
        persona_safe_summary_to_dict,
    )

    path = _persona_manifest_path(args)
    try:
        manifest = load_persona_manifest(path)
        summary = build_persona_safe_summary(manifest)
        payload = persona_safe_summary_to_dict(summary)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"persona safe summary: {summary.manifest_name}")
            print(f"  voice: {summary.voice_summary}")
            print(f"  posture: {summary.posture_summary}")
            print("  authority_boundaries:")
            for rule in summary.authority_boundaries:
                print(f"    - {rule}")
            print("  capability_honesty_rules:")
            for rule in summary.capability_honesty_rules:
                print(f"    - {rule}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"persona summary failed: {e}")
        return 1


def _operator_contract_path(args: argparse.Namespace) -> Path:
    if getattr(args, "contract_path", None):
        return Path(args.contract_path)
    return repo_root() / "config" / "aurel" / "operator_contract.yaml"


def _operator_contract_show_payload(contract, contract_hash: str) -> dict:
    return {
        "contract_name": contract.name,
        "contract_class": contract.contract_class,
        "principal_role": contract.parties.principal.role,
        "delegate_role": contract.parties.delegate.role,
        "operator_final_authority": contract.authority.operator_final_authority,
        "aurel_final_authority": contract.authority.aurel_final_authority,
        "aurel_can_self_escalate": contract.authority.aurel_can_self_escalate,
        "aurel_can_refuse_forbidden_action": contract.authority.aurel_can_refuse_forbidden_action,
        "aurel_must_challenge_when_risk_detected": (
            contract.authority.aurel_must_challenge_when_risk_detected
        ),
        "manipulation_forbidden": contract.non_manipulation.manipulation_forbidden,
        "contract_hash": contract_hash,
    }


def cmd_identity_operator_contract_show(args: argparse.Namespace) -> int:
    from ..identity.operator_contract import load_operator_contract
    from ..identity.operator_contract_hash import compute_operator_contract_hash

    path = _operator_contract_path(args)
    try:
        contract = load_operator_contract(path)
        contract_hash = compute_operator_contract_hash(contract).value
        payload = _operator_contract_show_payload(contract, contract_hash)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"operator contract: {contract.name}")
            print(f"  contract_class: {contract.contract_class}")
            print(f"  principal_role: {contract.parties.principal.role}")
            print(f"  delegate_role: {contract.parties.delegate.role}")
            print(f"  contract_hash: {contract_hash}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"operator contract show failed: {e}")
        return 1


def cmd_identity_operator_contract_validate(args: argparse.Namespace) -> int:
    from ..identity.operator_contract import load_operator_contract
    from ..identity.operator_contract_validation import validate_operator_contract

    path = _operator_contract_path(args)
    try:
        contract = load_operator_contract(path)
        result = validate_operator_contract(contract)
        payload = {
            "valid": result.valid,
            "config_path": str(path),
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "critical_failures": list(result.critical_failures),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif result.valid:
            print("operator contract: valid")
            print(f"  path: {path}")
        else:
            print("operator contract: invalid")
            for err in result.errors:
                print(f"  - {err}")
        return 0 if result.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"operator contract validate failed: {e}")
        return 1


def cmd_identity_operator_contract_hash(args: argparse.Namespace) -> int:
    from ..identity.operator_contract import load_operator_contract
    from ..identity.operator_contract_hash import compute_operator_contract_hash

    path = _operator_contract_path(args)
    try:
        contract = load_operator_contract(path)
        contract_hash = compute_operator_contract_hash(contract)
        payload = {
            "algorithm": contract_hash.algorithm,
            "value": contract_hash.value,
            "config_path": str(path),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(contract_hash.value)
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"operator contract hash failed: {e}")
        return 1


def cmd_identity_operator_contract_attest(args: argparse.Namespace) -> int:
    from ..identity.operator_contract import load_operator_contract
    from ..identity.operator_contract_validation import (
        build_operator_contract_attestation,
        write_operator_contract_attestation,
    )

    path = _operator_contract_path(args)
    try:
        contract = load_operator_contract(path)
        attestation = build_operator_contract_attestation(contract, path)
        out_path = None
        if args.write:
            out_path = write_operator_contract_attestation(attestation, Path(args.write))
        payload = {
            "schema_version": attestation.schema_version,
            "contract_hash": attestation.contract_hash,
            "hash_algorithm": attestation.hash_algorithm,
            "config_path": attestation.config_path,
            "validation_status": attestation.validation_status,
            "validator_version": attestation.validator_version,
            "critical_failures": list(attestation.critical_failures),
        }
        if out_path is not None:
            payload["attestation_path"] = str(out_path)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"validation_status: {attestation.validation_status}")
            print(f"contract_hash: {attestation.contract_hash}")
            if out_path is not None:
                print(f"written: {out_path}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"operator contract attest failed: {e}")
        return 1


def cmd_identity_operator_contract_summary(args: argparse.Namespace) -> int:
    from ..identity.operator_contract import load_operator_contract
    from ..identity.operator_contract_summary import (
        build_operator_contract_safe_summary,
        operator_contract_safe_summary_to_dict,
    )

    path = _operator_contract_path(args)
    try:
        contract = load_operator_contract(path)
        summary = build_operator_contract_safe_summary(contract)
        payload = operator_contract_safe_summary_to_dict(summary)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"operator contract safe summary: {summary.contract_name}")
            print(f"  principal: {summary.principal_summary}")
            print(f"  delegate: {summary.delegate_summary}")
            print("  authority_rules:")
            for rule in summary.authority_rules:
                print(f"    - {rule}")
            print("  challenge_rules:")
            for rule in summary.challenge_rules:
                print(f"    - {rule}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"operator contract summary failed: {e}")
        return 1


def _communication_modes_path(args: argparse.Namespace) -> Path:
    if getattr(args, "modes_path", None):
        return Path(args.modes_path)
    return repo_root() / "config" / "aurel" / "communication_modes.yaml"


def _communication_modes_list_payload(registry, registry_hash: str) -> dict:
    gb = registry.global_boundaries
    return {
        "registry_name": registry.registry_name,
        "modes": sorted(registry.modes.keys()),
        "modes_can_grant_permissions": gb.modes_can_grant_permissions,
        "modes_can_change_autonomy": gb.modes_can_change_autonomy,
        "modes_can_execute_actions": gb.modes_can_execute_actions,
        "registry_hash": registry_hash,
    }


def cmd_identity_modes_show(args: argparse.Namespace) -> int:
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.mode_hash import compute_communication_mode_registry_hash

    path = _communication_modes_path(args)
    try:
        registry = load_communication_mode_registry(path)
        registry_hash = compute_communication_mode_registry_hash(registry).value
        payload = _communication_modes_list_payload(registry, registry_hash)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"communication modes: {registry.registry_name}")
            print(f"  registry_class: {registry.registry_class}")
            print(f"  modes: {', '.join(payload['modes'])}")
            print(f"  registry_hash: {registry_hash}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"communication modes show failed: {e}")
        return 1


def cmd_identity_modes_validate(args: argparse.Namespace) -> int:
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.mode_validation import validate_communication_mode_registry

    path = _communication_modes_path(args)
    try:
        registry = load_communication_mode_registry(path)
        result = validate_communication_mode_registry(registry)
        payload = {
            "valid": result.valid,
            "config_path": str(path),
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "critical_failures": list(result.critical_failures),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif result.valid:
            print("communication modes: valid")
            print(f"  path: {path}")
        else:
            print("communication modes: invalid")
            for err in result.errors:
                print(f"  - {err}")
        return 0 if result.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"communication modes validate failed: {e}")
        return 1


def cmd_identity_modes_hash(args: argparse.Namespace) -> int:
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.mode_hash import compute_communication_mode_registry_hash

    path = _communication_modes_path(args)
    try:
        registry = load_communication_mode_registry(path)
        registry_hash = compute_communication_mode_registry_hash(registry)
        payload = {
            "algorithm": registry_hash.algorithm,
            "value": registry_hash.value,
            "config_path": str(path),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(registry_hash.value)
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"communication modes hash failed: {e}")
        return 1


def cmd_identity_modes_attest(args: argparse.Namespace) -> int:
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.mode_validation import (
        build_communication_mode_attestation,
        write_communication_mode_attestation,
    )

    path = _communication_modes_path(args)
    try:
        registry = load_communication_mode_registry(path)
        attestation = build_communication_mode_attestation(registry, path)
        out_path = None
        if args.write:
            out_path = write_communication_mode_attestation(attestation, Path(args.write))
        payload = {
            "schema_version": attestation.schema_version,
            "registry_hash": attestation.registry_hash,
            "hash_algorithm": attestation.hash_algorithm,
            "config_path": attestation.config_path,
            "validation_status": attestation.validation_status,
            "validator_version": attestation.validator_version,
            "critical_failures": list(attestation.critical_failures),
        }
        if out_path is not None:
            payload["attestation_path"] = str(out_path)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"validation_status: {attestation.validation_status}")
            print(f"registry_hash: {attestation.registry_hash}")
            if out_path is not None:
                print(f"written: {out_path}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"communication modes attest failed: {e}")
        return 1


def cmd_identity_modes_list(args: argparse.Namespace) -> int:
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.mode_hash import compute_communication_mode_registry_hash

    path = _communication_modes_path(args)
    try:
        registry = load_communication_mode_registry(path)
        registry_hash = compute_communication_mode_registry_hash(registry).value
        payload = _communication_modes_list_payload(registry, registry_hash)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"registry: {registry.registry_name}")
            for mode in payload["modes"]:
                print(f"  - {mode}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"communication modes list failed: {e}")
        return 1


def cmd_identity_modes_summary(args: argparse.Namespace) -> int:
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.mode_summary import (
        build_communication_mode_safe_summary,
        communication_mode_safe_summary_to_dict,
    )

    path = _communication_modes_path(args)
    try:
        registry = load_communication_mode_registry(path)
        summary = build_communication_mode_safe_summary(registry, args.mode)
        payload = communication_mode_safe_summary_to_dict(summary)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"mode safe summary: {summary.mode_name}")
            print(f"  purpose: {summary.purpose}")
            print(f"  cognitive_posture: {summary.cognitive_posture}")
            print("  authority_boundaries:")
            for rule in summary.authority_boundaries:
                print(f"    - {rule}")
        return 0
    except Exception as e:
        payload = {"error": str(e), "config_path": str(path), "mode": args.mode}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"communication modes summary failed: {e}")
        return 1


def _identity_prompt_compiler_path(args: argparse.Namespace) -> Path:
    if getattr(args, "compiler_path", None):
        return Path(args.compiler_path)
    from ..prompts.compiler_policy import default_identity_prompt_compiler_path

    return default_identity_prompt_compiler_path()


def _compile_identity_context(args: argparse.Namespace):
    from ..identity.communication_modes import load_communication_mode_registry
    from ..identity.kernel import load_identity_kernel
    from ..identity.operator_contract import load_operator_contract
    from ..identity.persona import load_persona_manifest
    from ..prompts.compiler_policy import load_identity_prompt_compiler_policy
    from ..prompts.identity_context_compiler import compile_identity_prompt_context

    kernel = load_identity_kernel(_identity_kernel_path(args))
    persona = load_persona_manifest(_persona_manifest_path(args))
    operator = load_operator_contract(_operator_contract_path(args))
    modes = load_communication_mode_registry(_communication_modes_path(args))
    policy = load_identity_prompt_compiler_policy(_identity_prompt_compiler_path(args))
    return compile_identity_prompt_context(
        kernel, persona, operator, modes, args.mode, policy
    )


def _identity_context_compile_payload(result) -> dict:
    if not result.valid or result.context is None:
        return {
            "valid": False,
            "selected_mode": "",
            "agent_name": "",
            "identity_kernel_hash": "",
            "persona_manifest_hash": "",
            "operator_contract_hash": "",
            "communication_modes_hash": "",
            "compiler_policy_hash": "",
            "context_hash": None,
            "sections": {},
            "critical_failures": list(result.critical_failures),
            "contradictions": [
                {
                    "id": c.id,
                    "source_layer": c.source_layer,
                    "key": c.key,
                    "reason": c.reason,
                }
                for c in result.contradictions
            ],
        }
    from ..prompts.identity_context_compiler import context_sections_dict

    ctx = result.context
    bundle = ctx.source_bundle
    return {
        "valid": True,
        "selected_mode": ctx.selected_mode,
        "agent_name": ctx.agent_name,
        "identity_kernel_hash": bundle.identity_kernel_hash,
        "persona_manifest_hash": bundle.persona_manifest_hash,
        "operator_contract_hash": bundle.operator_contract_hash,
        "communication_modes_hash": bundle.communication_modes_hash,
        "compiler_policy_hash": bundle.compiler_policy_hash,
        "context_hash": result.context_hash,
        "sections": context_sections_dict(ctx),
    }


def cmd_identity_context_compile(args: argparse.Namespace) -> int:
    try:
        result = _compile_identity_context(args)
        payload = _identity_context_compile_payload(result)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        elif result.valid and result.context is not None:
            print(f"identity context: valid mode={result.context.selected_mode}")
            print(f"  context_hash: {result.context_hash}")
        else:
            print("identity context: invalid")
            for failure in result.critical_failures:
                print(f"  - {failure}")
        return 0 if result.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e), "mode": args.mode}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"identity context compile failed: {e}")
        return 1


def cmd_identity_context_validate(args: argparse.Namespace) -> int:
    try:
        result = _compile_identity_context(args)
        payload = {
            "valid": result.valid,
            "selected_mode": args.mode,
            "critical_failures": list(result.critical_failures),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"identity context validate: {'valid' if result.valid else 'invalid'}")
            for failure in result.critical_failures:
                print(f"  - {failure}")
        return 0 if result.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e), "mode": args.mode}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"identity context validate failed: {e}")
        return 1


def cmd_identity_context_hash(args: argparse.Namespace) -> int:
    try:
        result = _compile_identity_context(args)
        if not result.valid or result.context_hash is None:
            if args.json:
                print(json.dumps({"valid": False, "context_hash": None}, indent=2))
            else:
                print("identity context hash: invalid compile")
            return 1
        if args.json:
            print(json.dumps({"valid": True, "context_hash": result.context_hash}, indent=2))
        else:
            print(result.context_hash)
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        else:
            print(f"identity context hash failed: {e}")
        return 1


def cmd_identity_context_render(args: argparse.Namespace) -> int:
    from ..prompts.identity_context_compiler import render_identity_prompt_context

    try:
        result = _compile_identity_context(args)
        if not result.valid or result.context is None:
            if args.json:
                print(json.dumps({"valid": False, "rendered": ""}, indent=2))
            else:
                print("identity context render: invalid compile")
            return 1
        rendered = render_identity_prompt_context(result.context)
        if args.json:
            print(json.dumps({"valid": True, "rendered": rendered}, indent=2))
        else:
            print(rendered, end="")
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        else:
            print(f"identity context render failed: {e}")
        return 1


def cmd_identity_context_attest(args: argparse.Namespace) -> int:
    from ..prompts.identity_context_attestation import (
        build_identity_prompt_attestation,
        write_identity_prompt_attestation,
    )

    try:
        result = _compile_identity_context(args)
        attestation = build_identity_prompt_attestation(result)
        if args.write:
            out_path = write_identity_prompt_attestation(attestation, args.write)
            payload: dict[str, object] = {
                "written": str(out_path),
                "validation_status": attestation.validation_status,
                "context_hash": attestation.context_hash,
            }
        else:
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
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"identity context attestation: {attestation.validation_status}")
            print(f"  context_hash: {attestation.context_hash}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"identity context attest failed: {e}")
        return 1


def _self_model_policy_path(args: argparse.Namespace) -> Path:
    if getattr(args, "self_model_policy_path", None):
        return Path(args.self_model_policy_path)
    from ..identity.self_model_policy import default_self_model_policy_path

    return default_self_model_policy_path()


def _build_self_model(args: argparse.Namespace):
    from ..identity.self_model_builder import build_aurel_self_model_from_paths

    prompt_mode = getattr(args, "prompt_mode", None) or "FOCUS"
    return build_aurel_self_model_from_paths(
        kernel_path=optional_cli_path(getattr(args, "kernel_path", "")),
        persona_path=optional_cli_path(getattr(args, "persona_path", "")),
        operator_path=optional_cli_path(getattr(args, "operator_path", "")),
        modes_path=optional_cli_path(getattr(args, "modes_path", "")),
        compiler_path=optional_cli_path(getattr(args, "compiler_path", "")),
        self_model_policy_path=optional_cli_path(getattr(args, "self_model_policy_path", "")),
        prompt_mode=prompt_mode,
        include_prompt_context=True,
    )


def _self_model_show_payload(model, model_hash: str) -> dict:
    bundle = model.source_bundle
    return {
        "agent_name": model.agent_name,
        "agent_class": model.agent_class,
        "runtime_version": model.runtime_version,
        "identity_kernel_hash": bundle.identity_kernel_hash,
        "persona_manifest_hash": bundle.persona_manifest_hash,
        "operator_contract_hash": bundle.operator_contract_hash,
        "communication_modes_hash": bundle.communication_modes_hash,
        "identity_prompt_compiler_policy_hash": bundle.identity_prompt_compiler_policy_hash,
        "identity_prompt_context_hash": bundle.identity_prompt_context_hash,
        "active_prompt_context_available": model.active_prompt_context_available,
        "capabilities": [
            {
                "id": cap.id,
                "name": cap.name,
                "status": cap.status,
                "evidence_ref": cap.evidence_ref,
                "limitation": cap.limitation,
                "roadmap_phase": cap.roadmap_phase,
            }
            for cap in model.capability_inventory
        ],
        "known_limitations": [item.description for item in model.known_limitations],
        "evidence_posture": {
            "evaluation_mirror_available": model.evidence_posture.evaluation_mirror_available,
            "verified_capability_claims_allowed": (
                model.evidence_posture.verified_capability_claims_allowed
            ),
            "evidence_system_phase": model.evidence_posture.evidence_system_phase,
            "default_capability_claim_status": (
                model.evidence_posture.default_capability_claim_status
            ),
        },
        "self_model_hash": model_hash,
    }


def cmd_identity_self_show(args: argparse.Namespace) -> int:
    from ..identity.self_model_hash import compute_self_model_hash
    from ..identity.self_model_policy import load_self_model_policy
    from ..identity.self_model_validation import validate_aurel_self_model

    try:
        model = _build_self_model(args)
        policy = load_self_model_policy(_self_model_policy_path(args))
        validation = validate_aurel_self_model(model, policy)
        model_hash = compute_self_model_hash(model).value
        payload = _self_model_show_payload(model, model_hash)
        payload["valid"] = validation.valid
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"self-model: {model.agent_name}")
            print(f"  self_model_hash: {model_hash}")
            print(f"  capabilities: {len(model.capability_inventory)}")
            print(f"  limitations: {len(model.known_limitations)}")
        return 0 if validation.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"self-model show failed: {e}")
        return 1


def cmd_identity_self_validate(args: argparse.Namespace) -> int:
    from ..identity.self_model_policy import load_self_model_policy
    from ..identity.self_model_validation import validate_aurel_self_model

    try:
        model = _build_self_model(args)
        policy = load_self_model_policy(_self_model_policy_path(args))
        validation = validate_aurel_self_model(model, policy)
        payload = {
            "valid": validation.valid,
            "critical_failures": list(validation.critical_failures),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"self-model validate: {'valid' if validation.valid else 'invalid'}")
            for failure in validation.critical_failures:
                print(f"  - {failure}")
        return 0 if validation.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"self-model validate failed: {e}")
        return 1


def cmd_identity_self_hash(args: argparse.Namespace) -> int:
    from ..identity.self_model_hash import compute_self_model_hash

    try:
        model = _build_self_model(args)
        model_hash = compute_self_model_hash(model).value
        if args.json:
            print(json.dumps({"valid": True, "self_model_hash": model_hash}, indent=2))
        else:
            print(model_hash)
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        else:
            print(f"self-model hash failed: {e}")
        return 1


def cmd_identity_self_capabilities(args: argparse.Namespace) -> int:
    try:
        model = _build_self_model(args)
        payload = {
            "capabilities": [
                {
                    "id": cap.id,
                    "name": cap.name,
                    "status": cap.status,
                    "evidence_ref": cap.evidence_ref,
                    "roadmap_phase": cap.roadmap_phase,
                }
                for cap in model.capability_inventory
            ]
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for cap in model.capability_inventory:
                print(f"{cap.id}: {cap.status} ({cap.roadmap_phase})")
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"self-model capabilities failed: {e}")
        return 1


def cmd_identity_self_limitations(args: argparse.Namespace) -> int:
    try:
        model = _build_self_model(args)
        payload = {
            "known_limitations": [
                {"id": item.id, "description": item.description, "related_phase": item.related_phase}
                for item in model.known_limitations
            ]
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for item in model.known_limitations:
                print(f"- {item.description}")
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"self-model limitations failed: {e}")
        return 1


def cmd_identity_self_attest(args: argparse.Namespace) -> int:
    from ..identity.self_model_attestation import build_self_model_attestation, write_self_model_attestation
    from ..identity.self_model_policy import load_self_model_policy
    from ..identity.self_model_validation import validate_aurel_self_model

    try:
        model = _build_self_model(args)
        policy = load_self_model_policy(_self_model_policy_path(args))
        validation = validate_aurel_self_model(model, policy)
        attestation = build_self_model_attestation(model, validation)
        if args.write:
            out_path = write_self_model_attestation(attestation, args.write)
            payload: dict[str, object] = {
                "written": str(out_path),
                "validation_status": attestation.validation_status,
                "self_model_hash": attestation.self_model_hash,
            }
        else:
            payload = {
                "schema_version": attestation.schema_version,
                "self_model_hash": attestation.self_model_hash,
                "hash_algorithm": attestation.hash_algorithm,
                "identity_kernel_hash": attestation.identity_kernel_hash,
                "persona_manifest_hash": attestation.persona_manifest_hash,
                "operator_contract_hash": attestation.operator_contract_hash,
                "communication_modes_hash": attestation.communication_modes_hash,
                "identity_prompt_compiler_policy_hash": (
                    attestation.identity_prompt_compiler_policy_hash
                ),
                "identity_prompt_context_hash": attestation.identity_prompt_context_hash,
                "validation_status": attestation.validation_status,
                "critical_failures": list(attestation.critical_failures),
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"self-model attestation: {attestation.validation_status}")
            print(f"  self_model_hash: {attestation.self_model_hash}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"self-model attest failed: {e}")
        return 1


def _agent_identity_card_path(args: argparse.Namespace) -> Path:
    if getattr(args, "card_config_path", None):
        return Path(args.card_config_path)
    from ..identity.agent_identity_card_policy import default_agent_identity_card_path

    return default_agent_identity_card_path()


def _build_agent_identity_card(args: argparse.Namespace):
    from ..identity.agent_identity_card_builder import build_agent_identity_card_from_paths

    prompt_mode = getattr(args, "prompt_mode", None) or "FOCUS"
    runtime_instance_id = getattr(args, "runtime_instance_id", None) or None
    if runtime_instance_id == "":
        runtime_instance_id = None
    return build_agent_identity_card_from_paths(
        kernel_path=optional_cli_path(getattr(args, "kernel_path", "")),
        persona_path=optional_cli_path(getattr(args, "persona_path", "")),
        operator_path=optional_cli_path(getattr(args, "operator_path", "")),
        modes_path=optional_cli_path(getattr(args, "modes_path", "")),
        compiler_path=optional_cli_path(getattr(args, "compiler_path", "")),
        self_model_policy_path=optional_cli_path(getattr(args, "self_model_policy_path", "")),
        card_config_path=optional_cli_path(getattr(args, "card_config_path", "")),
        prompt_mode=prompt_mode,
        include_prompt_context=True,
        runtime_instance_id=runtime_instance_id,
    )


def _agent_identity_card_show_payload(card) -> dict:
    bindings = card.source_bindings
    taxonomy = card.identity_taxonomy
    return {
        "agent_id": card.agent.agent_id,
        "agent_name": card.agent.agent_name,
        "agent_type": card.agent.agent_type,
        "runtime_instance_id": card.runtime.runtime_instance_id,
        "runtime_version": card.runtime.runtime_version,
        "identity_kernel_hash": bindings.identity_kernel_hash,
        "persona_manifest_hash": bindings.persona_manifest_hash,
        "operator_contract_hash": bindings.operator_contract_hash,
        "communication_modes_hash": bindings.communication_modes_hash,
        "identity_prompt_compiler_policy_hash": bindings.identity_prompt_compiler_policy_hash,
        "self_model_hash": bindings.self_model_hash,
        "stable_agent_identity_hash": card.stable_agent_identity_hash,
        "runtime_agent_identity_card_hash": card.runtime_agent_identity_card_hash,
        "identity_taxonomy": {
            "model_identity": taxonomy.model_identity,
            "agent_identity": taxonomy.agent_identity,
            "workload_identity": taxonomy.workload_identity,
            "delegated_identity": taxonomy.delegated_identity,
            "human_principal_identity": taxonomy.human_principal_identity,
        },
        "authority": {
            "authority_source": card.authority.authority_source,
            "final_authority": card.authority.final_authority,
            "self_escalation_allowed": card.authority.self_escalation_allowed,
            "delegated_authority_required_for_actions": (
                card.authority.delegated_authority_required_for_actions
            ),
            "tool_access_implies_authority": card.authority.tool_access_implies_authority,
        },
        "boundaries": {
            "card_can_grant_authority": card.boundaries.card_can_grant_authority,
            "card_can_create_delegation": card.boundaries.card_can_create_delegation,
            "card_can_authorize_tools": card.boundaries.card_can_authorize_tools,
        },
    }


def cmd_identity_card_show(args: argparse.Namespace) -> int:
    from ..identity.agent_identity_card_validation import validate_agent_identity_card

    try:
        card = _build_agent_identity_card(args)
        validation = validate_agent_identity_card(card)
        payload = _agent_identity_card_show_payload(card)
        payload["valid"] = validation.valid
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"agent-identity-card: {card.agent.agent_name}")
            print(f"  stable_agent_identity_hash: {card.stable_agent_identity_hash}")
            print(f"  runtime_agent_identity_card_hash: {card.runtime_agent_identity_card_hash}")
            print(f"  runtime_instance_id: {card.runtime.runtime_instance_id}")
        return 0 if validation.valid else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"agent-identity-card show failed: {e}")
        return 1


def cmd_identity_card_validate(args: argparse.Namespace) -> int:
    from ..identity.agent_identity_card_policy import load_agent_identity_card_config
    from ..identity.agent_identity_card_validation import (
        validate_agent_identity_card,
        validate_agent_identity_card_config,
    )

    try:
        card = _build_agent_identity_card(args)
        config = load_agent_identity_card_config(_agent_identity_card_path(args))
        config_validation = validate_agent_identity_card_config(config)
        card_validation = validate_agent_identity_card(card)
        critical_failures = list(
            config_validation.critical_failures + card_validation.critical_failures
        )
        payload: dict[str, object] = {
            "valid": config_validation.valid and card_validation.valid,
            "config_valid": config_validation.valid,
            "card_valid": card_validation.valid,
            "critical_failures": critical_failures,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                "agent-identity-card validate: "
                f"{'valid' if payload['valid'] else 'invalid'}"
            )
            for failure in critical_failures:
                print(f"  - {failure}")
        return 0 if payload["valid"] else 1
    except Exception as e:
        payload = {"valid": False, "error": str(e)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"agent-identity-card validate failed: {e}")
        return 1


def cmd_identity_card_hash(args: argparse.Namespace) -> int:
    try:
        card = _build_agent_identity_card(args)
        if args.json:
            print(
                json.dumps(
                    {
                        "valid": True,
                        "stable_agent_identity_hash": card.stable_agent_identity_hash,
                        "runtime_agent_identity_card_hash": card.runtime_agent_identity_card_hash,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(card.stable_agent_identity_hash)
            print(card.runtime_agent_identity_card_hash)
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        else:
            print(f"agent-identity-card hash failed: {e}")
        return 1


def cmd_identity_card_attest(args: argparse.Namespace) -> int:
    from ..identity.agent_identity_card_attestation import (
        build_agent_identity_card_attestation,
        write_agent_identity_card_attestation,
    )
    from ..identity.agent_identity_card_validation import validate_agent_identity_card

    try:
        card = _build_agent_identity_card(args)
        validation = validate_agent_identity_card(card)
        attestation = build_agent_identity_card_attestation(card, validation)
        if args.write:
            out_path = write_agent_identity_card_attestation(attestation, args.write)
            payload: dict[str, object] = {
                "written": str(out_path),
                "validation_status": attestation.validation_status,
                "stable_agent_identity_hash": attestation.stable_agent_identity_hash,
                "runtime_agent_identity_card_hash": attestation.runtime_agent_identity_card_hash,
            }
        else:
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
                "identity_prompt_compiler_policy_hash": (
                    attestation.identity_prompt_compiler_policy_hash
                ),
                "self_model_hash": attestation.self_model_hash,
                "validation_status": attestation.validation_status,
                "critical_failures": list(attestation.critical_failures),
            }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"agent-identity-card attestation: {attestation.validation_status}")
            print(f"  stable_agent_identity_hash: {attestation.stable_agent_identity_hash}")
        return 0 if attestation.validation_status == "valid" else 1
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"agent-identity-card attest failed: {e}")
        return 1


def cmd_identity_card_taxonomy(args: argparse.Namespace) -> int:
    from ..identity.identity_taxonomy import taxonomy_notes_for_null_fields

    try:
        card = _build_agent_identity_card(args)
        taxonomy = card.identity_taxonomy
        notes = taxonomy_notes_for_null_fields(
            taxonomy.model_identity,
            taxonomy.workload_identity,
            taxonomy.delegated_identity,
        )
        payload = {
            "identity_taxonomy": {
                "model_identity": taxonomy.model_identity,
                "agent_identity": taxonomy.agent_identity,
                "workload_identity": taxonomy.workload_identity,
                "delegated_identity": taxonomy.delegated_identity,
                "human_principal_identity": taxonomy.human_principal_identity,
            },
            "taxonomy_notes": list(notes),
            "agent_identity_equals_human": (
                taxonomy.agent_identity == taxonomy.human_principal_identity
            ),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"agent_identity: {taxonomy.agent_identity}")
            print(f"human_principal_identity: {taxonomy.human_principal_identity}")
            for note in notes:
                print(f"  note: {note}")
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"agent-identity-card taxonomy failed: {e}")
        return 1


# ── P1.4.8 Autonomy Scale Engine CLI ────────────────────────────────────


def cmd_identity_autonomy_evaluate(args: argparse.Namespace) -> int:
    """Evaluate autonomy for a single action. Does not execute tools."""
    from ..identity.autonomy_scale_engine import (
        ActionCategory,
        AutonomyRequest,
        AutonomyEvaluationContext,
        ReversibilityTier,
        RiskTier,
        autonomy_decision_to_dict,
    )
    from ..identity.autonomy_scale_engine_validation import (
        AutonomyValidationError,
        validate_and_resolve_autonomy,
    )
    from ..identity.operator_contract import load_operator_contract
    from ..identity.capability_inventory import default_capability_inventory

    try:
        # Parse enums from CLI args
        try:
            action_category = ActionCategory(args.action_category)
        except ValueError:
            if args.json:
                print(json.dumps({
                    "error": f"Invalid action category: {args.action_category}",
                    "valid_values": [ac.value for ac in ActionCategory],
                }, indent=2))
            else:
                print(f"error: invalid action category '{args.action_category}'")
                print(f"valid values: {[ac.value for ac in ActionCategory]}")
            return 1

        risk_tier: RiskTier | None = None
        if getattr(args, "risk_tier", None) and args.risk_tier != "":
            try:
                risk_tier = RiskTier(args.risk_tier)
            except ValueError:
                if args.json:
                    print(json.dumps({"error": f"Invalid risk tier: {args.risk_tier}",
                                       "valid_values": [rt.value for rt in RiskTier]}, indent=2))
                else:
                    print(f"error: invalid risk tier '{args.risk_tier}'")
                return 1

        reversibility_tier: ReversibilityTier | None = None
        if getattr(args, "reversibility_tier", None) and args.reversibility_tier != "":
            try:
                reversibility_tier = ReversibilityTier(args.reversibility_tier)
            except ValueError:
                if args.json:
                    print(json.dumps({"error": f"Invalid reversibility tier: {args.reversibility_tier}",
                                       "valid_values": [rt.value for rt in ReversibilityTier]}, indent=2))
                else:
                    print(f"error: invalid reversibility tier '{args.reversibility_tier}'")
                return 1

        # Load identity context
        card = _build_agent_identity_card(args)
        operator_path = _identity_operator_contract_path(args)
        operator_contract = load_operator_contract(operator_path)
        capability_inventory = default_capability_inventory()

        # Build request
        request = AutonomyRequest(
            action_id=getattr(args, "action_id", "cli_evaluate"),
            action_category=action_category,
            action_name=args.action_name,
            requested_by=getattr(args, "requested_by", "operator"),
            agent_id=card.agent.agent_id,
            target=getattr(args, "target", None),
            tool_name=getattr(args, "tool_name", None),
            path=getattr(args, "path", None),
            risk_tier=risk_tier,
            reversibility_tier=reversibility_tier,
            required_capability=getattr(args, "required_capability", None),
        )

        # Build context
        context = AutonomyEvaluationContext(
            agent_identity_card=card,
            operator_contract=operator_contract,
            capability_inventory=capability_inventory,
        )

        # Resolve
        try:
            decision = validate_and_resolve_autonomy(request, context)
        except AutonomyValidationError as e:
            if args.json:
                print(json.dumps({"error": str(e), "field": e.field}, indent=2))
            else:
                print(f"validation error: {e}")
            return 1

        # Output
        decision_dict = autonomy_decision_to_dict(decision)
        if args.json:
            print(json.dumps(decision_dict, indent=2, sort_keys=True))
        else:
            print(f"autonomy decision: {'ALLOWED' if decision.allowed else 'DENIED'}")
            print(f"  level: {decision.autonomy_level.value}")
            print(f"  category: {decision.action_category.value}")
            print(f"  risk: {decision.risk_tier.value}")
            print(f"  reversibility: {decision.reversibility_tier.value}")
            print(f"  human_approval: {'required' if decision.requires_human_approval else 'not required'}")
            print(f"  reason: {decision.reason}")
            if decision.blockers:
                print(f"  blockers: {', '.join(decision.blockers)}")
            if decision.warnings:
                print(f"  warnings: {', '.join(decision.warnings)}")
            if decision.required_gates:
                print(f"  required_gates: {', '.join(decision.required_gates)}")

        return 0 if decision.allowed else 1

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"autonomy evaluate failed: {e}")
        return 1


def _identity_operator_contract_path(args: argparse.Namespace) -> Path:
    if getattr(args, "operator_path", None):
        return Path(args.operator_path)
    return repo_root() / "config" / "aurel" / "operator_contract.yaml"


# ── P1.4.9 Measured Autonomy Score CLI ────────────────────────────────────


def cmd_identity_autonomy_measure(args: argparse.Namespace) -> int:
    """Measure autonomy from stored decision records. Does not execute tools."""
    from ..identity.autonomy_measurement import (
        AutonomyMeasurementWindow,
        AutonomyDecisionRecord,
        MeasuredAutonomyClass,
        MeasuredAutonomyReport,
        measure_autonomy_score,
        load_autonomy_decision_records,
        append_autonomy_decision_record,
        measured_autonomy_score_to_dict,
        measured_autonomy_report_to_dict,
    )
    from ..identity.autonomy_scale_engine import ActionCategory, ReversibilityTier, RiskTier

    try:
        records_path_str = getattr(args, "records_path", None)
        if records_path_str:
            records_path = Path(records_path_str)
        else:
            records_path = repo_root() / "agent" / "state" / "autonomy_decisions.jsonl"

        # Load existing records
        all_records = load_autonomy_decision_records(records_path)
        records = list(all_records)

        # Optionally evaluate and append a synthetic decision for testing
        if getattr(args, "evaluate_and_record", False):
            from ..identity.autonomy_scale_engine import AutonomyRequest, AutonomyEvaluationContext
            from ..identity.autonomy_scale_engine_validation import validate_and_resolve_autonomy

            card = _build_agent_identity_card(args)
            operator_path = _identity_operator_contract_path(args)
            from ..identity.operator_contract import load_operator_contract
            operator_contract = load_operator_contract(operator_path)

            try:
                action_category = ActionCategory(args.action_category)
            except ValueError:
                action_category = ActionCategory.ANSWER

            risk_tier = RiskTier.R1_LOW
            if getattr(args, "risk_tier", None) and args.risk_tier:
                try:
                    risk_tier = RiskTier(args.risk_tier)
                except ValueError:
                    pass

            reversibility_tier = ReversibilityTier.R1_FULLY_REVERSIBLE
            if getattr(args, "reversibility_tier", None) and args.reversibility_tier:
                try:
                    reversibility_tier = ReversibilityTier(args.reversibility_tier)
                except ValueError:
                    pass

            from ..identity.capability_inventory import default_capability_inventory
            request = AutonomyRequest(
                action_id=getattr(args, "action_id", f"measure_{len(records)}"),
                action_category=action_category,
                action_name=getattr(args, "action_name", "measure_record"),
                requested_by=getattr(args, "requested_by", "operator"),
                agent_id=card.agent.agent_id,
                risk_tier=risk_tier,
                reversibility_tier=reversibility_tier,
                required_capability=getattr(args, "required_capability", None),
            )
            context = AutonomyEvaluationContext(
                agent_identity_card=card,
                operator_contract=operator_contract,
                capability_inventory=default_capability_inventory(),
            )
            decision = validate_and_resolve_autonomy(request, context)
            record = AutonomyDecisionRecord(
                decision=decision,
                source="cli_measure",
            )
            append_autonomy_decision_record(records_path, record)
            records.append(record)

        # Build window
        agent_id = getattr(args, "agent_id", None)
        if not agent_id:
            card = _build_agent_identity_card(args)
            agent_id = card.agent.agent_id

        window = AutonomyMeasurementWindow(
            agent_id=agent_id,
            since=getattr(args, "since", None) or None,
            until=getattr(args, "until", None) or None,
            max_decisions=getattr(args, "max_decisions", 100),
            include_denied=not getattr(args, "exclude_denied", False),
            include_approval_required=True,
            minimum_decisions=getattr(args, "minimum_decisions", 5),
        )

        # Measure
        score = measure_autonomy_score(tuple(records), window)

        # Build report
        top_blockers = sorted(
            score.denial_reasons.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )
        top_blocker_keys = tuple(k for k, _ in top_blockers[:10])

        # Narrative
        narrative = _build_narrative(score)

        report = MeasuredAutonomyReport(
            score=score,
            narrative_summary=narrative,
            top_blockers=top_blocker_keys,
            recommended_next_gates=_recommend_gates(score),
            raw_decision_refs=score.evidence_refs,
        )

        # Output
        if args.json:
            report_dict = measured_autonomy_report_to_dict(report)
            print(json.dumps(report_dict, indent=2, sort_keys=True))
        else:
            score_dict = measured_autonomy_score_to_dict(score)
            print(f"Measured Autonomy — {score_dict['agent_id']}")
            print()
            print(f"Class: {score_dict['autonomy_class']}")
            print(f"Confidence: {score_dict['confidence']}")
            print(f"Total decisions: {score_dict['total_decisions']}")
            print(f"Allowed: {score_dict['allowed_count']}")
            print(f"Denied: {score_dict['denied_count']}")
            print(f"Approval required: {score_dict['approval_required_count']}")
            print()
            dom = score_dict.get("dominant_level", "—")
            hvl = score_dict.get("highest_verified_level", "—")
            print(f"Dominant level: {dom}")
            print(f"Highest verified level: {hvl}")
            print()
            if top_blockers:
                print("Top blockers:")
                for bk in top_blocker_keys:
                    print(f"  - {bk} ({score.denial_reasons.get(bk, 0)})")
            if score.limitations:
                print()
                print("Limitations:")
                for lim in score.limitations:
                    print(f"  - {lim}")
            print()
            print(f"Narrative: {narrative}")

        return 0

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"autonomy measure failed: {e}")
        return 1


def _build_narrative(score) -> str:
    """Build a human-readable narrative summary from a MeasuredAutonomyScore."""
    from ..identity.autonomy_measurement import MeasuredAutonomyClass

    ac = score.autonomy_class
    total = score.total_decisions
    allowed = score.allowed_count
    denied = score.denied_count

    parts = [f"Agent {score.agent_id}: {total} decisions evaluated."]

    if ac == MeasuredAutonomyClass.INSUFFICIENT_EVIDENCE:
        parts.append("Insufficient evidence to determine autonomy class.")
        return " ".join(parts)

    if ac == MeasuredAutonomyClass.DENIED_OR_UNTRUSTED:
        parts.append("Agent is DENIED or untrusted — majority of decisions denied.")
        return " ".join(parts)

    parts.append(f"{allowed} allowed, {denied} denied.")
    parts.append(f"Measured autonomy class: {ac.value}.")
    if score.highest_verified_level:
        parts.append(f"Highest verified level: {score.highest_verified_level.value}.")
    if score.approval_required_count > 0:
        parts.append(f"Human approval required in {score.approval_required_count} decisions.")
    if score.limitations:
        parts.append(f"Limitations: {', '.join(score.limitations)}.")
    return " ".join(parts)


def _recommend_gates(score) -> tuple[str, ...]:
    """Recommend next gates based on measurement patterns."""
    gates: list[str] = []
    denial_reasons = score.denial_reasons
    if "missing_authority_scope" in denial_reasons:
        gates.append("define_authority_scope")
    if "capability_not_implemented" in denial_reasons:
        gates.append("implement_required_capabilities")
    if "capability_not_verified" in denial_reasons:
        gates.append("verify_capabilities")
    if not score.limitations and score.total_decisions >= 10:
        gates.append("consider_higher_autonomy_with_guardrails")
    return tuple(gates)


# ── P1.4.10 Capability Claim Boundary Engine CLI ──────────────────────────


def cmd_identity_claims_evaluate(args: argparse.Namespace) -> int:
    """Evaluate a capability claim against evidence. Does NOT grant permissions."""
    import json as _json

    from ..identity.capability_claims import (
        CapabilityClaim,
        CapabilityClaimType,
        ClaimEvidenceContext,
        capability_claim_decision_to_dict,
        evaluate_capability_claim,
        get_claim,
    )

    claim_text = args.claim
    claim_id = args.claim_id

    if claim_id:
        claim = get_claim(claim_id)
        if claim is None:
            print(f"Unknown claim ID: {claim_id}", file=sys.stderr)
            return 1
    else:
        claim = CapabilityClaim(
            claim_id="ad-hoc",
            claim_text=claim_text,
            claim_type=CapabilityClaimType(args.claim_type) if args.claim_type else CapabilityClaimType.AUTONOMY,
        )

    ctx = ClaimEvidenceContext()
    decision = evaluate_capability_claim(claim, ctx)

    if args.json:
        print(_json.dumps(capability_claim_decision_to_dict(decision), indent=2))
    else:
        status_mark = "ALLOWED" if decision.allowed else "BLOCKED"
        print(f"Claim: {decision.original_claim_text}")
        print(f"Status: {status_mark} ({decision.allowed_status.value})")
        print(f"Reason: {decision.reason}")
        if decision.blockers:
            print(f"Blockers: {', '.join(decision.blockers)}")
        if decision.warnings:
            print(f"Warnings: {', '.join(decision.warnings)}")
        if decision.safe_claim_text:
            print(f"Safe rewrite: {decision.safe_claim_text}")
    return 0


def cmd_identity_claims_list(args: argparse.Namespace) -> int:
    """List all registered capability claims."""
    import json as _json

    from ..identity.capability_claims import list_claims

    claims = list_claims()
    if args.json:
        result = [{
            "claim_id": c.claim_id,
            "claim_text": c.claim_text,
            "claim_type": c.claim_type.value,
            "current_evidence_level": c.current_evidence_level,
        } for c in claims]
        print(_json.dumps(result, indent=2))
    else:
        for c in claims:
            evidence_note = c.current_evidence_level or "no-evidence"
            print(f"  [{c.claim_type.value} | {evidence_note}] {c.claim_id}: {c.claim_text}")
    return 0


def cmd_identity_claims_show(args: argparse.Namespace) -> int:
    """Show details for a specific registered claim."""
    import json as _json

    from ..identity.capability_claims import (
        ClaimEvidenceContext,
        capability_claim_decision_to_dict,
        evaluate_capability_claim,
        get_claim,
    )

    claim = get_claim(args.claim_id)
    if claim is None:
        print(f"Unknown claim ID: {args.claim_id}", file=sys.stderr)
        return 1

    ctx = ClaimEvidenceContext()
    decision = evaluate_capability_claim(claim, ctx)

    if args.json:
        print(_json.dumps(capability_claim_decision_to_dict(decision), indent=2))
    else:
        print(f"Claim ID: {claim.claim_id}")
        print(f"Claim text: {claim.claim_text}")
        print(f"Type: {claim.claim_type.value}")
        print(f"Current evidence level: {claim.current_evidence_level or 'none'}")
        print(f"Required evidence level: {claim.required_evidence_level or 'not specified'}")
        print(f"Required patches: {', '.join(claim.required_patch_refs) or 'none'}")
        print(f"Required seals: {', '.join(claim.required_seals) or 'none'}")
        print(f"Allowed: {decision.allowed}")
        print(f"Status: {decision.allowed_status.value}")
        print(f"Reason: {decision.reason}")
    return 0


def cmd_identity_claims_validate(args: argparse.Namespace) -> int:
    """Validate the claim registry. Ensures all claims can be evaluated."""
    from ..identity.capability_claims import (
        CapabilityClaimStatus,
        ClaimEvidenceContext,
        evaluate_capability_claim,
        list_claims,
    )

    claims = list_claims()
    ctx = ClaimEvidenceContext()
    failures = 0
    warnings = 0

    for claim in claims:
        decision = evaluate_capability_claim(claim, ctx)
        if not decision.allowed and decision.allowed_status == CapabilityClaimStatus.FORBIDDEN:
            if claim.current_evidence_level is None and claim.required_evidence_level not in ("roadmap_only",):
                warnings += 1
        if decision.blockers:
            if any("missing_evidence_requires" not in b for b in decision.blockers):
                failures += 1

    if args.json:
        print(json.dumps({"claims": len(claims), "failures": failures, "warnings": warnings}))
    else:
        print(f"Registry claims: {len(claims)}")
        print(f"Evaluation failures: {failures} (claims with evidence gaps)")
        print(f"Missing-evidence warnings: {warnings} (claims with no current evidence)")

    return 0


def cmd_identity_claims_rewrite(args: argparse.Namespace) -> int:
    """Produce a safe truthful rewrite of a claim."""
    import json as _json

    from ..identity.capability_claims import (
        CapabilityClaim,
        CapabilityClaimType,
        ClaimEvidenceContext,
        evaluate_capability_claim,
        get_claim,
        rewrite_claim_text_safely,
    )

    claim_text = args.claim
    claim_id = args.claim_id

    if claim_id:
        claim = get_claim(claim_id)
        if claim is None:
            print(f"Unknown claim ID: {claim_id}", file=sys.stderr)
            return 1
    else:
        safe = rewrite_claim_text_safely(claim_text)
        if safe is not None:
            if args.json:
                print(_json.dumps({"original": claim_text, "safe_rewrite": safe}, indent=2))
            else:
                print(f"Original: {claim_text}")
                print(f"Safe:     {safe}")
            return 0

        claim = CapabilityClaim(
            claim_id="ad-hoc",
            claim_text=claim_text,
            claim_type=CapabilityClaimType(args.claim_type) if args.claim_type else CapabilityClaimType.AUTONOMY,
        )

    ctx = ClaimEvidenceContext()
    decision = evaluate_capability_claim(claim, ctx)

    if args.json:
        print(_json.dumps({
            "original": decision.original_claim_text,
            "safe_rewrite": decision.safe_claim_text,
            "allowed": decision.allowed,
            "status": decision.allowed_status.value,
        }, indent=2))
    else:
        print(f"Original:  {decision.original_claim_text}")
        print(f"Safe:      {decision.safe_claim_text or '(no safe rewrite available)'}")
        print(f"Status:    {decision.allowed_status.value}")
    return 0

# -- P1.4.11 External Doctrine Assimilation Registry CLI ------------------


def cmd_identity_doctrine_list(args: argparse.Namespace) -> int:
    """List registered external doctrine inputs."""
    from ..identity.doctrine_registry import list_external_doctrine_inputs
    from ..identity.external_doctrine import external_doctrine_input_to_dict

    doctrines = list_external_doctrine_inputs()
    if args.json:
        print(json.dumps([external_doctrine_input_to_dict(d) for d in doctrines], indent=2))
    else:
        for doctrine in doctrines:
            print(
                f"  [{doctrine.source_type.value} | {doctrine.assimilation_status.value}] "
                f"{doctrine.doctrine_id}: {doctrine.name}"
            )
    return 0


def cmd_identity_doctrine_show(args: argparse.Namespace) -> int:
    """Show a registered doctrine input and assimilation decision."""
    from ..identity.doctrine_registry import (
        evaluate_doctrine_assimilation,
        get_external_doctrine_input,
    )
    from ..identity.external_doctrine import (
        doctrine_assimilation_decision_to_dict,
        external_doctrine_input_to_dict,
    )

    doctrine = get_external_doctrine_input(args.doctrine_id)
    if doctrine is None:
        print(f"Unknown doctrine ID: {args.doctrine_id}", file=sys.stderr)
        return 1

    decision = evaluate_doctrine_assimilation(doctrine)
    if args.json:
        print(json.dumps({
            "doctrine": external_doctrine_input_to_dict(doctrine),
            "decision": doctrine_assimilation_decision_to_dict(decision),
        }, indent=2))
    else:
        print(f"Doctrine ID: {doctrine.doctrine_id}")
        print(f"Name: {doctrine.name}")
        print(f"Status: {doctrine.assimilation_status.value}")
        print(f"Source type: {doctrine.source_type.value}")
        print(f"Source hash: {doctrine.source_hash}")
        print(f"Operator accepted: {doctrine.operator_accepted}")
        print(f"Accepted for mapping: {decision.accepted}")
        print(f"Reason: {decision.reason}")
    return 0


def cmd_identity_doctrine_validate(args: argparse.Namespace) -> int:
    """Validate the doctrine registry."""
    from ..identity.doctrine_registry import list_external_doctrine_inputs, validate_doctrine_registry

    doctrines = list_external_doctrine_inputs()
    errors = validate_doctrine_registry(doctrines)
    payload = {
        "valid": not errors,
        "doctrines": len(doctrines),
        "errors": list(errors),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif not errors:
        print("doctrine registry: valid")
        print(f"  doctrines: {len(doctrines)}")
        print("  doctrine may influence roadmap; doctrine does not grant capability")
    else:
        print("doctrine registry: invalid")
        for error in errors:
            print(f"  - {error}")
    return 0 if not errors else 1


def cmd_identity_doctrine_impact(args: argparse.Namespace) -> int:
    """Show roadmap impacts for a doctrine input."""
    from ..identity.doctrine_mapping import map_doctrine_to_roadmap
    from ..identity.doctrine_registry import get_external_doctrine_input
    from ..identity.external_doctrine import roadmap_impact_to_dict

    doctrine = get_external_doctrine_input(args.doctrine_id)
    if doctrine is None:
        print(f"Unknown doctrine ID: {args.doctrine_id}", file=sys.stderr)
        return 1

    impacts = map_doctrine_to_roadmap(doctrine)
    if args.json:
        print(json.dumps([roadmap_impact_to_dict(impact) for impact in impacts], indent=2))
    else:
        print(f"Roadmap impacts for {doctrine.doctrine_id}:")
        if not impacts:
            print("  none")
        for impact in impacts:
            print(
                f"  [{impact.impact_type.value} | {impact.implementation_status}] "
                f"{impact.roadmap_module}"
            )
    return 0


def cmd_identity_doctrine_claims(args: argparse.Namespace) -> int:
    """Show doctrine claim boundaries and P1.4.10 claim decisions."""
    from ..identity.doctrine_claim_boundaries import doctrine_claim_boundary_decisions_to_dict
    from ..identity.doctrine_registry import (
        evaluate_doctrine_assimilation,
        get_external_doctrine_input,
    )

    doctrine = get_external_doctrine_input(args.doctrine_id)
    if doctrine is None:
        print(f"Unknown doctrine ID: {args.doctrine_id}", file=sys.stderr)
        return 1

    decision = evaluate_doctrine_assimilation(doctrine)
    if args.json:
        print(json.dumps({
            "doctrine_id": doctrine.doctrine_id,
            "claim_boundaries": list(doctrine.claim_boundaries),
            "blocked_claims": list(decision.blocked_claims),
            "safe_claim_notes": list(decision.safe_claim_notes),
            "p1410_decisions": doctrine_claim_boundary_decisions_to_dict(doctrine),
        }, indent=2))
    else:
        print(f"Claim boundaries for {doctrine.doctrine_id}:")
        for claim in decision.blocked_claims:
            print(f"  - {claim}")
        print("Safe claim notes:")
        for note in decision.safe_claim_notes:
            print(f"  - {note}")
    return 0

# -- P1.4.12 Raw Source + Canonical Hash Attestation CLI -----------------


def _source_attestation_records() -> dict[str, SourceAttestation]:
    from ..identity.doctrine_registry import list_external_doctrine_inputs
    from ..identity.source_attestation import build_doctrine_source_attestation
    from ..identity.source_bundle import load_identity_source_bundle

    bundle = load_identity_source_bundle()
    records: dict[str, SourceAttestation] = {
        kind.value: attestation for kind, attestation in bundle.attestations.items()
    }
    for doctrine in list_external_doctrine_inputs():
        records[f"external_doctrine:{doctrine.doctrine_id}"] = build_doctrine_source_attestation(
            doctrine
        )
    return records


def _identity_attestation_records() -> dict[str, SourceAttestation]:
    from ..identity.source_bundle import load_identity_source_bundle

    bundle = load_identity_source_bundle()
    return {kind.value: attestation for kind, attestation in bundle.attestations.items()}


def cmd_identity_attestation_list(args: argparse.Namespace) -> int:
    """List source attestations."""
    from ..identity.source_attestation import source_attestation_to_dict

    records = _source_attestation_records()
    if args.json:
        print(json.dumps([
            {"record_key": key, **source_attestation_to_dict(attestation)}
            for key, attestation in sorted(records.items())
        ], indent=2))
    else:
        for key, attestation in sorted(records.items()):
            print(
                f"  [{attestation.source_kind.value} | {attestation.validation_status.value}] "
                f"{key}: {attestation.source_name}"
            )
    return 0


def cmd_identity_attestation_show(args: argparse.Namespace) -> int:
    """Show one source attestation."""
    from ..identity.source_attestation import source_attestation_to_dict

    records = _source_attestation_records()
    attestation = records.get(args.source_id)
    if attestation is None:
        print(f"Unknown source attestation: {args.source_id}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(source_attestation_to_dict(attestation), indent=2))
    else:
        print(f"Source: {args.source_id}")
        print(f"Kind: {attestation.source_kind.value}")
        print(f"Status: {attestation.validation_status.value}")
        print(f"Raw hash: {attestation.raw_source_hash}")
        print(f"Canonical hash: {attestation.canonical_typed_hash}")
        print("Hash proves integrity of seen source, not truth, trust, or capability.")
    return 0


def cmd_identity_attestation_validate(args: argparse.Namespace) -> int:
    """Validate source attestations."""
    from ..identity.source_attestation import validate_source_attestations

    records = _source_attestation_records()
    errors = validate_source_attestations(tuple(records.values()))
    payload = {
        "valid": not errors,
        "attestations": len(records),
        "errors": list(errors),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif not errors:
        print("source attestations: valid")
        print(f"  attestations: {len(records)}")
        print("  hash-based attestation only; not trust or capability verification")
    else:
        print("source attestations: invalid")
        for error in errors:
            print(f"  - {error}")
    return 0 if not errors else 1


def cmd_identity_attestation_verify_bundle(args: argparse.Namespace) -> int:
    """Verify the identity source bundle has all required attestations."""
    from ..identity.source_attestation import SourceKind, validate_source_attestations
    from ..identity.source_bundle import load_identity_source_bundle, validate_identity_source_bundle

    required = {
        SourceKind.IDENTITY_KERNEL,
        SourceKind.PERSONA_MANIFEST,
        SourceKind.OPERATOR_CONTRACT,
        SourceKind.COMMUNICATION_MODES,
        SourceKind.IDENTITY_PROMPT_COMPILER,
        SourceKind.SELF_MODEL_POLICY,
        SourceKind.AGENT_IDENTITY_CARD_CONFIG,
    }
    bundle = load_identity_source_bundle()
    missing = sorted(kind.value for kind in required - set(bundle.attestations))
    attestation_errors = validate_source_attestations(tuple(bundle.attestations.values()))
    bundle_errors = validate_identity_source_bundle(bundle)
    errors = tuple(f"missing_attestation:{item}" for item in missing) + attestation_errors + bundle_errors
    payload = {
        "valid": not errors,
        "required_attestations": sorted(kind.value for kind in required),
        "present_attestations": sorted(kind.value for kind in bundle.attestations),
        "missing_attestations": missing,
        "errors": list(errors),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif not errors:
        print("identity source bundle attestations: valid")
        print(f"  present: {len(bundle.attestations)}")
    else:
        print("identity source bundle attestations: invalid")
        for error in errors:
            print(f"  - {error}")
    return 0 if not errors else 1


def cmd_identity_attestation_compare(args: argparse.Namespace) -> int:
    """Compare a raw file hash with the attested canonical source for a kind."""
    from pathlib import Path as _Path

    from ..identity.source_attestation import SourceKind, hash_raw_source

    try:
        source_kind = SourceKind(args.canonical_kind)
    except ValueError:
        print(f"Unknown source kind: {args.canonical_kind}", file=sys.stderr)
        return 1
    identity_records = _identity_attestation_records()
    if source_kind.value not in identity_records:
        print(f"No identity attestation for source kind: {source_kind.value}", file=sys.stderr)
        return 1
    attestation = identity_records[source_kind.value]
    raw_path = _Path(args.raw_path)
    try:
        raw_hash = hash_raw_source(raw_path.read_bytes())
    except OSError as exc:
        print(f"Failed to read raw path: {exc}", file=sys.stderr)
        return 1
    payload = {
        "raw_path": str(raw_path),
        "canonical_kind": source_kind.value,
        "raw_source_hash": raw_hash,
        "attested_raw_source_hash": attestation.raw_source_hash,
        "canonical_typed_hash": attestation.canonical_typed_hash,
        "raw_matches_attestation": raw_hash == attestation.raw_source_hash,
        "attestation_id": attestation.attestation_id,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"raw_source_hash: {raw_hash}")
        print(f"canonical_typed_hash: {attestation.canonical_typed_hash}")
        print(f"raw_matches_attestation: {payload['raw_matches_attestation']}")
    return 0


# ---------------------------------------------------------------------------
# P1.4.13 Authority Delta Detector
# ---------------------------------------------------------------------------


def cmd_identity_authority_delta_compare(args: argparse.Namespace) -> int:
    """Compare two canonical source objects for authority deltas (P1.4.13)."""
    import json as _json

    from ..identity.authority_delta import (
        AuthorityDeltaInput,
        authority_delta_report_to_dict,
        detect_authority_deltas,
    )
    from ..yaml_minimal import load_yaml

    try:
        old_raw = Path(args.old).read_text(encoding="utf-8")
        new_raw = Path(args.new).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read input file: {exc}", file=sys.stderr)
        return 1

    try:
        old_obj = load_yaml(old_raw)
    except Exception as exc:
        print(f"Failed to parse old source: {exc}", file=sys.stderr)
        return 1

    try:
        new_obj = load_yaml(new_raw)
    except Exception as exc:
        print(f"Failed to parse new source: {exc}", file=sys.stderr)
        return 1

    delta_input = AuthorityDeltaInput(
        source_kind=args.source_kind,
        old_canonical_object=old_obj,
        new_canonical_object=new_obj,
    )

    report = detect_authority_deltas(delta_input)
    payload = authority_delta_report_to_dict(report)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Authority Delta Report: {report.report_id}")
        print(f"  source_kind: {report.source_kind}")
        print(f"  highest_severity: {report.highest_severity.value}")
        print(f"  requires_operator_consent: {report.requires_operator_consent}")
        print(f"  requires_evidence: {report.requires_evidence}")
        print(f"  safe_to_auto_accept: {report.safe_to_auto_accept}")
        print(f"  summary: {report.summary}")
        if report.deltas:
            print(f"  deltas: {len(report.deltas)}")
            for delta in report.deltas:
                print(f"    [{delta.severity.value}] {delta.delta_type.value}: {delta.field_path} "
                      f"({delta.old_value!r} -> {delta.new_value!r})")
                if delta.requires_operator_consent:
                    print(f"      OPERATOR CONSENT REQUIRED")
    return 0


# ---------------------------------------------------------------------------
# P1.4.14 Operator Consent Binding
# ---------------------------------------------------------------------------


def _load_json_or_yaml(path_str: str) -> dict:
    """Load a JSON or YAML file into a dict. Tries JSON first, then YAML."""
    from pathlib import Path as _Path

    from ..yaml_minimal import load_yaml

    raw = _Path(path_str).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    return load_yaml(raw)


def cmd_identity_consent_request(args: argparse.Namespace) -> int:
    """Build an operator consent request from an authority delta report JSON."""
    from ..identity.authority_delta import (
        AuthorityDelta,
        AuthorityDeltaReport,
        AuthorityDeltaSeverity,
        AuthorityDeltaType,
    )
    from ..identity.operator_consent import (
        OperatorConsentScope,
        build_operator_consent_request,
        operator_consent_request_to_dict,
    )

    try:
        data = _load_json_or_yaml(args.delta_report)
    except Exception as exc:
        print(f"Failed to read delta report: {exc}", file=sys.stderr)
        return 1

    # Reconstruct AuthorityDeltaReport from JSON
    deltas = tuple(
        AuthorityDelta(
            delta_id=d["delta_id"],
            delta_type=AuthorityDeltaType(d["delta_type"]),
            severity=AuthorityDeltaSeverity(d["severity"]),
            source_kind=d["source_kind"],
            field_path=d["field_path"],
            old_value=d.get("old_value"),
            new_value=d.get("new_value"),
            old_attestation_id=d.get("old_attestation_id"),
            new_attestation_id=d.get("new_attestation_id"),
            requires_operator_consent=d.get("requires_operator_consent", False),
            requires_evidence=d.get("requires_evidence", False),
            reason=d.get("reason", ""),
            blockers=tuple(d.get("blockers", ())),
            warnings=tuple(d.get("warnings", ())),
        )
        for d in data["deltas"]
    )
    report = AuthorityDeltaReport(
        report_id=data.get("report_id", ""),
        source_kind=data["source_kind"],
        deltas=deltas,
        highest_severity=AuthorityDeltaSeverity(data["highest_severity"]),
        requires_operator_consent=data.get("requires_operator_consent", False),
        requires_evidence=data.get("requires_evidence", False),
        summary=data.get("summary", ""),
        safe_to_auto_accept=data.get("safe_to_auto_accept", True),
        old_attestation_id=data.get("old_attestation_id"),
        new_attestation_id=data.get("new_attestation_id"),
    )

    scope = getattr(args, "scope", "DELTA_REPORT")
    try:
        requested_scope = OperatorConsentScope(scope)
    except ValueError:
        print(f"Unknown scope: {scope}", file=sys.stderr)
        return 1

    request = build_operator_consent_request(report, requested_scope=requested_scope)
    payload = operator_consent_request_to_dict(request)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Consent Request: {request.request_id}")
        print(f"  source_kind: {request.source_kind}")
        print(f"  delta_ids: {len(request.delta_ids)}")
        for did in request.delta_ids:
            print(f"    - {did}")
        print(f"  highest_severity: {request.highest_severity}")
        print(f"  requires_risk_ack: {request.requires_explicit_risk_acknowledgement}")
        print(f"\n{request.summary}")
    return 0


def cmd_identity_consent_grant(args: argparse.Namespace) -> int:
    """Grant operator consent from a consent request JSON."""
    from ..identity.operator_consent import (
        ConsentValidationError,
        OperatorConsentRequest,
        OperatorConsentScope,
        grant_operator_consent,
        operator_consent_record_to_dict,
    )

    try:
        data = _load_json_or_yaml(args.request)
    except Exception as exc:
        print(f"Failed to read consent request: {exc}", file=sys.stderr)
        return 1

    try:
        request = OperatorConsentRequest(
            request_id=data["request_id"],
            source_kind=data["source_kind"],
            delta_ids=tuple(data.get("delta_ids", ())),
            highest_severity=data["highest_severity"],
            old_attestation_id=data.get("old_attestation_id"),
            new_attestation_id=data.get("new_attestation_id"),
            summary=data.get("summary", ""),
            risk_summary=data.get("risk_summary", ""),
            requested_scope=OperatorConsentScope(data.get("requested_scope", "DELTA_REPORT")),
            requires_explicit_risk_acknowledgement=data.get(
                "requires_explicit_risk_acknowledgement", False
            ),
            created_at=data.get("created_at", ""),
            expires_at=data.get("expires_at"),
            evidence_refs=tuple(data.get("evidence_refs", ())),
        )
    except Exception as exc:
        print(f"Failed to parse consent request: {exc}", file=sys.stderr)
        return 1

    risk_ack = getattr(args, "ack_risk", False)
    operator_id = getattr(args, "operator_id", "operator.local")
    reason = getattr(args, "reason", None)

    try:
        record = grant_operator_consent(
            request,
            operator_id=operator_id,
            risk_acknowledged=risk_ack,
            reason=reason,
        )
    except ConsentValidationError as exc:
        payload = {"error": str(exc), "blockers": list(exc.blockers)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Consent grant failed: {exc}")
            for b in exc.blockers:
                print(f"  blocker: {b}")
        return 1

    payload = operator_consent_record_to_dict(record)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Consent Record: {record.consent_id}")
        print(f"  status: {record.status.value}")
        print(f"  operator_id: {record.operator_id}")
        print(f"  risk_acknowledged: {record.risk_acknowledged}")
    return 0


def cmd_identity_consent_deny(args: argparse.Namespace) -> int:
    """Deny a consent request."""
    from ..identity.operator_consent import (
        OperatorConsentRequest,
        OperatorConsentScope,
        deny_operator_consent,
        operator_consent_record_to_dict,
    )

    try:
        data = _load_json_or_yaml(args.request)
    except Exception as exc:
        print(f"Failed to read consent request: {exc}", file=sys.stderr)
        return 1

    try:
        request = OperatorConsentRequest(
            request_id=data["request_id"],
            source_kind=data["source_kind"],
            delta_ids=tuple(data.get("delta_ids", ())),
            highest_severity=data["highest_severity"],
            old_attestation_id=data.get("old_attestation_id"),
            new_attestation_id=data.get("new_attestation_id"),
            summary=data.get("summary", ""),
            risk_summary=data.get("risk_summary", ""),
            requested_scope=OperatorConsentScope(data.get("requested_scope", "DELTA_REPORT")),
            requires_explicit_risk_acknowledgement=data.get(
                "requires_explicit_risk_acknowledgement", False
            ),
            created_at=data.get("created_at", ""),
            expires_at=data.get("expires_at"),
        )
    except Exception as exc:
        print(f"Failed to parse consent request: {exc}", file=sys.stderr)
        return 1

    operator_id = getattr(args, "operator_id", "operator.local")
    reason = getattr(args, "reason", None)
    record = deny_operator_consent(request, operator_id=operator_id, reason=reason)
    payload = operator_consent_record_to_dict(record)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Consent denied: {record.consent_id}")
        print(f"  status: {record.status.value}")
        if reason:
            print(f"  reason: {reason}")
    return 0


def cmd_identity_consent_revoke(args: argparse.Namespace) -> int:
    """Revoke a previously granted consent record."""
    from ..identity.operator_consent import (
        ConsentValidationError,
        OperatorConsentRecord,
        OperatorConsentScope,
        OperatorConsentStatus,
        operator_consent_record_to_dict,
        revoke_operator_consent,
    )

    try:
        data = _load_json_or_yaml(args.record)
    except Exception as exc:
        print(f"Failed to read consent record: {exc}", file=sys.stderr)
        return 1

    try:
        record = OperatorConsentRecord(
            consent_id=data["consent_id"],
            request_id=data["request_id"],
            status=OperatorConsentStatus(data["status"]),
            scope=OperatorConsentScope(data.get("scope", "DELTA_REPORT")),
            operator_id=data["operator_id"],
            operator_display_name=data.get("operator_display_name"),
            source_kind=data["source_kind"],
            delta_ids=tuple(data.get("delta_ids", ())),
            old_attestation_id=data.get("old_attestation_id"),
            new_attestation_id=data.get("new_attestation_id"),
            highest_severity=data["highest_severity"],
            risk_acknowledged=data.get("risk_acknowledged", False),
            granted_at=data.get("granted_at"),
            denied_at=data.get("denied_at"),
            revoked_at=data.get("revoked_at"),
            expires_at=data.get("expires_at"),
            reason=data.get("reason"),
        )
    except Exception as exc:
        print(f"Failed to parse consent record: {exc}", file=sys.stderr)
        return 1

    operator_id = getattr(args, "operator_id", "operator.local")
    reason = getattr(args, "reason", None)

    try:
        revoked = revoke_operator_consent(record, operator_id=operator_id, reason=reason)
    except ConsentValidationError as exc:
        payload = {"error": str(exc), "blockers": list(exc.blockers)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Revoke failed: {exc}")
        return 1

    payload = operator_consent_record_to_dict(revoked)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Consent revoked: {revoked.consent_id}")
        print(f"  status: {revoked.status.value}")
        if reason:
            print(f"  reason: {reason}")
    return 0


def cmd_identity_consent_show(args: argparse.Namespace) -> int:
    """Show a consent record in readable format."""
    from ..identity.operator_consent import (
        OperatorConsentRecord,
        OperatorConsentScope,
        OperatorConsentStatus,
    )

    try:
        data = _load_json_or_yaml(args.record)
    except Exception as exc:
        print(f"Failed to read consent record: {exc}", file=sys.stderr)
        return 1

    try:
        record = OperatorConsentRecord(
            consent_id=data["consent_id"],
            request_id=data["request_id"],
            status=OperatorConsentStatus(data["status"]),
            scope=OperatorConsentScope(data.get("scope", "DELTA_REPORT")),
            operator_id=data["operator_id"],
            operator_display_name=data.get("operator_display_name"),
            source_kind=data["source_kind"],
            delta_ids=tuple(data.get("delta_ids", ())),
            old_attestation_id=data.get("old_attestation_id"),
            new_attestation_id=data.get("new_attestation_id"),
            highest_severity=data["highest_severity"],
            risk_acknowledged=data.get("risk_acknowledged", False),
            granted_at=data.get("granted_at"),
            denied_at=data.get("denied_at"),
            revoked_at=data.get("revoked_at"),
            expires_at=data.get("expires_at"),
            reason=data.get("reason"),
        )
    except Exception as exc:
        print(f"Failed to parse consent record: {exc}", file=sys.stderr)
        return 1

    if args.json:
        from ..identity.operator_consent import operator_consent_record_to_dict
        print(json.dumps(operator_consent_record_to_dict(record), indent=2))
    else:
        print(f"Consent Record: {record.consent_id}")
        print(f"  status: {record.status.value}")
        print(f"  scope: {record.scope.value}")
        print(f"  operator_id: {record.operator_id}")
        print(f"  source_kind: {record.source_kind}")
        print(f"  delta_ids ({len(record.delta_ids)}):")
        for did in record.delta_ids:
            print(f"    - {did}")
        print(f"  highest_severity: {record.highest_severity}")
        print(f"  risk_acknowledged: {record.risk_acknowledged}")
        print(f"  old_attestation_id: {record.old_attestation_id}")
        print(f"  new_attestation_id: {record.new_attestation_id}")
        if record.granted_at:
            print(f"  granted_at: {record.granted_at}")
        if record.denied_at:
            print(f"  denied_at: {record.denied_at}")
        if record.revoked_at:
            print(f"  revoked_at: {record.revoked_at}")
        if record.expires_at:
            print(f"  expires_at: {record.expires_at}")
        if record.reason:
            print(f"  reason: {record.reason}")
    return 0


def cmd_identity_consent_validate(args: argparse.Namespace) -> int:
    """Validate whether a consent record covers a delta report."""
    from ..identity.authority_delta import (
        AuthorityDelta,
        AuthorityDeltaReport,
        AuthorityDeltaSeverity,
        AuthorityDeltaType,
    )
    from ..identity.operator_consent import (
        ConsentBindingValidation,
        OperatorConsentRecord,
        OperatorConsentScope,
        OperatorConsentStatus,
        consent_binding_validation_to_dict,
        validate_operator_consent_binding,
    )

    try:
        rec_data = _load_json_or_yaml(args.record)
    except Exception as exc:
        print(f"Failed to read consent record: {exc}", file=sys.stderr)
        return 1
    try:
        rep_data = _load_json_or_yaml(args.delta_report)
    except Exception as exc:
        print(f"Failed to read delta report: {exc}", file=sys.stderr)
        return 1

    try:
        record = OperatorConsentRecord(
            consent_id=rec_data["consent_id"],
            request_id=rec_data["request_id"],
            status=OperatorConsentStatus(rec_data["status"]),
            scope=OperatorConsentScope(rec_data.get("scope", "DELTA_REPORT")),
            operator_id=rec_data["operator_id"],
            operator_display_name=rec_data.get("operator_display_name"),
            source_kind=rec_data["source_kind"],
            delta_ids=tuple(rec_data.get("delta_ids", ())),
            old_attestation_id=rec_data.get("old_attestation_id"),
            new_attestation_id=rec_data.get("new_attestation_id"),
            highest_severity=rec_data["highest_severity"],
            risk_acknowledged=rec_data.get("risk_acknowledged", False),
            granted_at=rec_data.get("granted_at"),
            denied_at=rec_data.get("denied_at"),
            revoked_at=rec_data.get("revoked_at"),
            expires_at=rec_data.get("expires_at"),
            reason=rec_data.get("reason"),
        )
    except Exception as exc:
        print(f"Failed to parse consent record: {exc}", file=sys.stderr)
        return 1

    deltas = tuple(
        AuthorityDelta(
            delta_id=d["delta_id"],
            delta_type=AuthorityDeltaType(d["delta_type"]),
            severity=AuthorityDeltaSeverity(d["severity"]),
            source_kind=d["source_kind"],
            field_path=d["field_path"],
            old_value=d.get("old_value"),
            new_value=d.get("new_value"),
            old_attestation_id=d.get("old_attestation_id"),
            new_attestation_id=d.get("new_attestation_id"),
            requires_operator_consent=d.get("requires_operator_consent", False),
            requires_evidence=d.get("requires_evidence", False),
            reason=d.get("reason", ""),
            blockers=tuple(d.get("blockers", ())),
            warnings=tuple(d.get("warnings", ())),
        )
        for d in rep_data["deltas"]
    )
    report = AuthorityDeltaReport(
        report_id=rep_data.get("report_id", ""),
        source_kind=rep_data["source_kind"],
        deltas=deltas,
        highest_severity=AuthorityDeltaSeverity(rep_data["highest_severity"]),
        requires_operator_consent=rep_data.get("requires_operator_consent", False),
        requires_evidence=rep_data.get("requires_evidence", False),
        summary=rep_data.get("summary", ""),
        safe_to_auto_accept=rep_data.get("safe_to_auto_accept", True),
        old_attestation_id=rep_data.get("old_attestation_id"),
        new_attestation_id=rep_data.get("new_attestation_id"),
    )

    validation = validate_operator_consent_binding(record, report)
    payload = consent_binding_validation_to_dict(validation)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Consent validation: {'valid' if validation.valid else 'invalid'}")
        print(f"  consent_id: {validation.consent_id}")
        print(f"  status: {validation.status.value if validation.status else 'N/A'}")
        if validation.covered_delta_ids:
            print(f"  covered deltas: {len(validation.covered_delta_ids)}")
        if validation.missing_delta_ids:
            print(f"  missing deltas: {len(validation.missing_delta_ids)}")
            for mid in validation.missing_delta_ids:
                print(f"    - {mid}")
        if validation.blockers:
            print(f"  blockers:")
            for b in validation.blockers:
                print(f"    - {b}")
        if validation.warnings:
            print(f"  warnings:")
            for w in validation.warnings:
                print(f"    - {w}")
        print(f"  reason: {validation.reason}")
    return 0 if validation.valid else 1


# ---------------------------------------------------------------------------
# P1.4.15 identity status / verify
# ---------------------------------------------------------------------------


def cmd_identity_status(args: argparse.Namespace) -> int:
    """Show overall P1.4 identity governance status. Read-only."""
    from ..identity.identity_cli_surface import (
        build_identity_status_report,
        identity_status_report_to_dict,
        format_identity_status_human,
    )

    report = build_identity_status_report()
    if args.json:
        print(json.dumps(identity_status_report_to_dict(report), indent=2))
    else:
        print(format_identity_status_human(report))

    if report.status.value == "BLOCKED":
        return 1
    return 0


def cmd_identity_verify(args: argparse.Namespace) -> int:
    """Run non-destructive validation across P1.4 modules. Read-only."""
    from ..identity.identity_cli_surface import (
        verify_identity_surface,
        identity_status_report_to_dict,
        format_identity_status_human,
    )

    report = verify_identity_surface()
    if args.json:
        print(json.dumps(identity_status_report_to_dict(report), indent=2))
    else:
        print(format_identity_status_human(report))

    if report.status.value == "BLOCKED":
        return 1
    return 0


# ---------------------------------------------------------------------------
# P1.4.16 identity test-battery
# ---------------------------------------------------------------------------


def cmd_identity_test_battery_run(args: argparse.Namespace) -> int:
    """Run the full identity test battery. Read-only."""
    import json as _json

    from ..identity.identity_test_battery import (
        identity_test_battery_report_to_dict,
        run_identity_test_battery,
        format_identity_test_battery_report,
    )

    include_adv = getattr(args, "include_adversarial", True)
    include_cli = getattr(args, "include_cli", True)

    report = run_identity_test_battery(
        include_adversarial=include_adv,
        include_cli=include_cli,
    )
    if args.json:
        payload = identity_test_battery_report_to_dict(report)
        print(_json.dumps(payload, indent=2))
    else:
        print(format_identity_test_battery_report(report))

    if report.status.value == "FAILED":
        return 1
    return 0


def cmd_identity_test_battery_list(args: argparse.Namespace) -> int:
    """List all registered identity test cases."""
    import json as _json

    from ..identity.identity_test_battery import identity_test_cases

    cases = identity_test_cases()
    if args.json:
        listing = [
            {
                "case_id": c.case_id,
                "name": c.name,
                "description": c.description,
                "severity": c.severity.value,
                "module_refs": list(c.module_refs),
                "invariant_refs": list(c.invariant_refs),
            }
            for c in cases
        ]
        print(_json.dumps(listing, indent=2))
    else:
        print(f"Identity Test Cases: {len(cases)}")
        for c in cases:
            print(f"  [{c.severity.value}] {c.case_id}: {c.name}")
    return 0


def cmd_identity_test_battery_run_case(args: argparse.Namespace) -> int:
    """Run a single identity test case by case_id."""
    import json as _json

    from ..identity.identity_test_battery import (
        identity_test_cases,
        identity_test_result_to_dict,
        run_identity_test_case,
    )

    case_map = {c.case_id: c for c in identity_test_cases()}
    case = case_map.get(args.case_id)
    if case is None:
        if args.json:
            print(_json.dumps({"error": f"Unknown case_id: {args.case_id}"}))
        else:
            print(f"Unknown case_id: {args.case_id}")
        return 1

    result = run_identity_test_case(case)
    if args.json:
        print(_json.dumps(identity_test_result_to_dict(result), indent=2))
    else:
        print(f"Case: {result.case_id}")
        print(f"  status: {result.status.value}")
        print(f"  summary: {result.summary}")
        if result.errors:
            for e in result.errors:
                print(f"  error: {e}")
        if result.warnings:
            for w in result.warnings:
                print(f"  warning: {w}")
    return 0 if result.status.value == "PASSED" else 1


# ---------------------------------------------------------------------------
# P1.4.17 identity lifecycle
# ---------------------------------------------------------------------------


def cmd_identity_lifecycle_show(args: argparse.Namespace) -> int:
    """Show the lifecycle state of an agent identity. Read-only."""
    import json as _json

    from ..identity.agent_lifecycle import (
        AgentLifecycleState,
        agent_lifecycle_eligibility_profile_to_dict,
        build_agent_lifecycle_eligibility_profile,
        format_lifecycle_profile_human,
    )

    try:
        state = AgentLifecycleState(args.state)
    except ValueError:
        if args.json:
            print(_json.dumps({"error": f"Unknown state: {args.state}"}))
        else:
            print(f"Unknown lifecycle state: {args.state}")
        return 1

    profile = build_agent_lifecycle_eligibility_profile(
        agent_id=args.agent_id,
        lifecycle_state=state,
    )
    if args.json:
        print(_json.dumps(agent_lifecycle_eligibility_profile_to_dict(profile), indent=2))
    else:
        print(format_lifecycle_profile_human(profile))
    return 0


def cmd_identity_lifecycle_profile(args: argparse.Namespace) -> int:
    """Build a lifecycle eligibility profile. Read-only."""
    import json as _json

    from ..identity.agent_lifecycle import (
        AgentLifecycleState,
        LifecycleReasonCode,
        agent_lifecycle_eligibility_profile_to_dict,
        build_agent_lifecycle_eligibility_profile,
        format_lifecycle_profile_human,
    )

    try:
        state = AgentLifecycleState(args.state)
    except ValueError:
        if args.json:
            print(_json.dumps({"error": f"Unknown state: {args.state}"}))
        else:
            print(f"Unknown lifecycle state: {args.state}")
        return 1

    reasons: tuple[LifecycleReasonCode, ...] = ()
    if hasattr(args, "reason") and args.reason:
        reason_codes_str = args.reason.split(",")
        try:
            reasons = tuple(LifecycleReasonCode(r.strip()) for r in reason_codes_str)
        except ValueError as exc:
            if args.json:
                print(_json.dumps({"error": str(exc)}))
            else:
                print(f"Unknown reason code: {exc}")
            return 1

    profile = build_agent_lifecycle_eligibility_profile(
        agent_id=args.agent_id,
        lifecycle_state=state,
        restriction_reasons=reasons,
    )
    if args.json:
        print(_json.dumps(agent_lifecycle_eligibility_profile_to_dict(profile), indent=2))
    else:
        print(format_lifecycle_profile_human(profile))
    return 0


def cmd_identity_lifecycle_validate_transition(args: argparse.Namespace) -> int:
    """Validate a lifecycle transition request. Read-only."""
    import json as _json

    from ..identity.agent_lifecycle import (
        AgentLifecycleState,
        AgentLifecycleTransitionRequest,
        LifecycleReasonCode,
        agent_lifecycle_transition_decision_to_dict,
        format_lifecycle_decision_human,
        validate_agent_lifecycle_transition,
    )

    try:
        old_state = AgentLifecycleState(args.old_state)
        new_state = AgentLifecycleState(args.new_state)
    except ValueError as exc:
        if args.json:
            print(_json.dumps({"error": str(exc)}))
        else:
            print(f"Invalid state: {exc}")
        return 1

    try:
        reason_code = LifecycleReasonCode(args.reason_code)
    except ValueError as exc:
        if args.json:
            print(_json.dumps({"error": str(exc)}))
        else:
            print(f"Invalid reason code: {exc}")
        return 1

    request = AgentLifecycleTransitionRequest(
        request_id=f"cli_req_{args.agent_id}",
        agent_id=args.agent_id,
        old_state=old_state,
        requested_state=new_state,
        reason_code=reason_code,
        reason_text=args.reason,
        requested_by=args.requested_by if hasattr(args, "requested_by") and args.requested_by else None,
        evidence_refs=tuple(args.evidence_ref) if hasattr(args, "evidence_ref") and args.evidence_ref else (),
        test_battery_refs=tuple(args.test_battery_ref) if hasattr(args, "test_battery_ref") and args.test_battery_ref else (),
    )

    decision = validate_agent_lifecycle_transition(request)
    if args.json:
        print(_json.dumps(agent_lifecycle_transition_decision_to_dict(decision), indent=2))
    else:
        print(format_lifecycle_decision_human(decision))
    return 0 if decision.allowed else 1


def cmd_identity_lifecycle_transitions(args: argparse.Namespace) -> int:
    """Show the default lifecycle transition policy. Read-only."""
    import json as _json

    from ..identity.agent_lifecycle import (
        agent_lifecycle_policy_to_dict,
        default_agent_lifecycle_policy,
    )

    policy = default_agent_lifecycle_policy()
    if args.json:
        print(_json.dumps(agent_lifecycle_policy_to_dict(policy), indent=2))
    else:
        print("Allowed transitions:")
        for src, targets in policy.allowed_transitions.items():
            target_str = ", ".join(t.value for t in targets)
            print(f"  {src.value} -> {target_str}")
        print(f"\nTerminal states: {', '.join(s.value for s in policy.terminal_states)}")
        print(f"Active requires evidence: {policy.active_requires_evidence}")
        print(f"Active requires test battery: {policy.active_requires_test_battery}")
        print(f"Restricted requires reason: {policy.restricted_requires_reason}")
        print(f"Revoked is terminal: {policy.revoked_is_terminal}")
    return 0


def cmd_identity_lifecycle_recommend(args: argparse.Namespace) -> int:
    """Recommend a lifecycle state change based on governance signals. Read-only."""
    import json as _json

    from ..identity.agent_lifecycle import (
        AgentLifecycleState,
        agent_lifecycle_transition_decision_to_dict,
        format_lifecycle_decision_human,
        recommend_lifecycle_state,
    )

    try:
        current_state = AgentLifecycleState(args.current_state)
    except ValueError as exc:
        if args.json:
            print(_json.dumps({"error": str(exc)}))
        else:
            print(f"Invalid state: {exc}")
        return 1

    decision = recommend_lifecycle_state(
        agent_id=args.agent_id,
        current_state=current_state,
        battery_status=args.battery_status if hasattr(args, "battery_status") and args.battery_status else None,
        highest_failed_severity=args.highest_failed_severity if hasattr(args, "highest_failed_severity") and args.highest_failed_severity else None,
    )
    if args.json:
        print(_json.dumps(agent_lifecycle_transition_decision_to_dict(decision), indent=2))
    else:
        print(format_lifecycle_decision_human(decision))
    return 0


# ---------------------------------------------------------------------------
# P1.4.18 identity trust-evidence
# ---------------------------------------------------------------------------


def cmd_identity_trust_evidence_requirements(args: argparse.Namespace) -> int:
    """Show trust evidence requirements for a lifecycle state. Read-only."""
    import json as _json

    from ..identity.trust_evidence import (
        default_trust_evidence_requirements_for_lifecycle,
        trust_evidence_requirement_to_dict,
    )

    reqs = default_trust_evidence_requirements_for_lifecycle(args.lifecycle_state)
    if args.json:
        print(_json.dumps([trust_evidence_requirement_to_dict(r) for r in reqs], indent=2))
    else:
        print(f"Trust evidence requirements for {args.lifecycle_state}:")
        for r in reqs:
            required = "REQUIRED" if r.required else "recommended"
            print(f"  [{required}] {r.kind.value}: {r.reason}")
    return 0


def cmd_identity_trust_evidence_build(args: argparse.Namespace) -> int:
    """Build a trust evidence bundle. Read-only."""
    import json as _json

    from ..identity.trust_evidence import (
        TrustEvidenceKind,
        TrustEvidenceRef,
        TrustEvidenceStatus,
        build_trust_evidence_bundle,
        format_trust_evidence_bundle_human,
        trust_evidence_bundle_to_dict,
    )

    refs: list[TrustEvidenceRef] = []
    evidence_ref_args = getattr(args, "evidence_ref", []) or []
    for i, raw in enumerate(evidence_ref_args):
        if ":" in raw:
            kind_str, ref_str = raw.split(":", 1)
            try:
                kind = TrustEvidenceKind(kind_str.upper())
            except ValueError:
                kind = TrustEvidenceKind.REPORT
        else:
            kind = TrustEvidenceKind.REPORT
            ref_str = raw
        refs.append(TrustEvidenceRef(
            evidence_id=f"cli_ev_{i}",
            kind=kind,
            ref=ref_str,
            status=TrustEvidenceStatus.PRESENT,
            summary=f"CLI-provided: {ref_str}",
        ))

    bundle = build_trust_evidence_bundle(
        agent_id=args.agent_id,
        lifecycle_state=args.lifecycle_state,
        evidence_refs=tuple(refs),
    )
    if args.json:
        print(_json.dumps(trust_evidence_bundle_to_dict(bundle), indent=2))
    else:
        print(format_trust_evidence_bundle_human(bundle))
    return 0


def cmd_identity_trust_evidence_validate(args: argparse.Namespace) -> int:
    """Validate a trust evidence bundle JSON file. Read-only."""
    import json as _json

    from ..identity.trust_evidence import (
        TrustEvidenceKind,
        TrustEvidenceRef,
        TrustEvidenceStatus,
        TrustPosture,
        build_trust_evidence_bundle,
        format_trust_evidence_report_human,
        trust_evidence_linkage_report_to_dict,
        validate_trust_evidence_bundle,
    )

    with open(args.bundle, "r") as f:
        raw = _json.load(f)

    refs = tuple(
        TrustEvidenceRef(
            evidence_id=r.get("evidence_id", ""),
            kind=TrustEvidenceKind(r.get("kind", "UNKNOWN")),
            ref=r.get("ref", ""),
            title=r.get("title"),
            status=TrustEvidenceStatus(r.get("status", "UNKNOWN")),
            produced_by_module=r.get("produced_by_module"),
            created_at=r.get("created_at"),
            expires_at=r.get("expires_at"),
            hash_ref=r.get("hash_ref"),
            source_attestation_id=r.get("source_attestation_id"),
            summary=r.get("summary", ""),
            warnings=tuple(r.get("warnings", [])),
            blockers=tuple(r.get("blockers", [])),
        )
        for r in raw.get("evidence_refs", [])
    )
    bundle = build_trust_evidence_bundle(
        agent_id=raw.get("agent_id", "unknown"),
        lifecycle_state=raw.get("lifecycle_state"),
        evidence_refs=refs,
    )
    report = validate_trust_evidence_bundle(bundle)
    if args.json:
        print(_json.dumps(trust_evidence_linkage_report_to_dict(report), indent=2))
    else:
        print(format_trust_evidence_report_human(report))
    return 1 if report.posture in (TrustPosture.BLOCKED, TrustPosture.UNSUPPORTED) else 0


def cmd_identity_trust_evidence_explain(args: argparse.Namespace) -> int:
    """Explain why an agent has its current trust posture. Read-only."""
    import json as _json

    from ..identity.trust_evidence import (
        TrustEvidenceKind,
        TrustEvidenceRef,
        TrustEvidenceStatus,
        build_trust_evidence_bundle,
        format_trust_evidence_bundle_human,
        trust_evidence_bundle_to_dict,
    )

    with open(args.bundle, "r") as f:
        raw = _json.load(f)

    refs = tuple(
        TrustEvidenceRef(
            evidence_id=r.get("evidence_id", ""),
            kind=TrustEvidenceKind(r.get("kind", "UNKNOWN")),
            ref=r.get("ref", ""),
            title=r.get("title"),
            status=TrustEvidenceStatus(r.get("status", "UNKNOWN")),
            produced_by_module=r.get("produced_by_module"),
            created_at=r.get("created_at"),
            expires_at=r.get("expires_at"),
            hash_ref=r.get("hash_ref"),
            source_attestation_id=r.get("source_attestation_id"),
            summary=r.get("summary", ""),
            warnings=tuple(r.get("warnings", [])),
            blockers=tuple(r.get("blockers", [])),
        )
        for r in raw.get("evidence_refs", [])
    )
    bundle = build_trust_evidence_bundle(
        agent_id=raw.get("agent_id", "unknown"),
        lifecycle_state=raw.get("lifecycle_state"),
        evidence_refs=refs,
    )
    if args.json:
        print(_json.dumps(trust_evidence_bundle_to_dict(bundle), indent=2))
    else:
        print(format_trust_evidence_bundle_human(bundle))
    return 0


# ---------------------------------------------------------------------------
# P1.4.19 identity seal-readiness
# ---------------------------------------------------------------------------


def cmd_identity_seal_readiness(args: argparse.Namespace) -> int:
    """Show P1.4 seal readiness summary. Read-only."""
    import json as _json

    from ..identity.p14_seal_readiness import (
        build_p14_seal_readiness_report,
        format_p14_seal_readiness_human,
        p14_seal_readiness_report_to_dict,
    )

    report = build_p14_seal_readiness_report()
    if args.json:
        print(_json.dumps(p14_seal_readiness_report_to_dict(report), indent=2))
    else:
        print(format_p14_seal_readiness_human(report))
    return 0 if report.status == "READY" else 1


# ---------------------------------------------------------------------------
# P1.4.20 identity p14-seal
# ---------------------------------------------------------------------------


def cmd_identity_p14_seal_run(args: argparse.Namespace) -> int:
    """Run the full P1.4 exit seal. Read-only."""
    import json as _json

    from ..identity.p14_exit_seal import (
        format_p14_seal_report,
        p14_seal_report_to_dict,
        run_p14_exit_seal,
    )

    report = run_p14_exit_seal()
    if args.json:
        print(_json.dumps(p14_seal_report_to_dict(report), indent=2))
    else:
        print(format_p14_seal_report(report))
    return 0 if report.decision.status.value.startswith("SEALED") else 1


def cmd_identity_p14_seal_list_checks(args: argparse.Namespace) -> int:
    """List all P1.4 exit seal checks. Read-only."""
    import json as _json

    from ..identity.p14_exit_seal import p14_seal_check_to_dict, p14_seal_checks

    checks = p14_seal_checks()
    if args.json:
        print(_json.dumps([p14_seal_check_to_dict(c) for c in checks], indent=2))
    else:
        for c in checks:
            print(f"  [{c.severity.value:8s}] {c.check_id}: {c.name}")
    return 0


def cmd_identity_p14_seal_run_check(args: argparse.Namespace) -> int:
    """Run a single P1.4 seal check. Read-only."""
    import json as _json

    from ..identity.p14_exit_seal import (
        P14SealCheckStatus,
        p14_seal_check_result_to_dict,
        p14_seal_checks,
        run_p14_seal_check,
    )

    checks = {c.check_id: c for c in p14_seal_checks()}
    if args.check_id not in checks:
        print(_json.dumps({"error": f"Unknown check: {args.check_id}"}))
        return 1
    result = run_p14_seal_check(checks[args.check_id])
    if args.json:
        print(_json.dumps(p14_seal_check_result_to_dict(result), indent=2))
    else:
        print(f"Check: {result.check_id}")
        print(f"Status: {result.status.value} ({result.severity.value})")
        print(f"Summary: {result.summary}")
        if result.errors:
            for e in result.errors:
                print(f"  Error: {e}")
    return 0 if result.status in (P14SealCheckStatus.PASSED, P14SealCheckStatus.WARNING) else 1
