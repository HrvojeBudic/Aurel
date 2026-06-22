"""Deterministic hashing for Aurel Communication Modes registry (P1.4.4)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .communication_modes import (
    AurelCommunicationModeRegistry,
    CommunicationModeInvariant,
    CommunicationModeRegistryHash,
    CommunicationModeSpec,
)


def _bool_map_to_dict(mapping: dict[str, bool]) -> dict[str, bool]:
    return {key: mapping[key] for key in sorted(mapping)}


def _mode_to_dict(mode: CommunicationModeSpec) -> dict[str, Any]:
    return {
        "boundaries": _bool_map_to_dict(dict(mode.boundaries)),
        "challenge_emphasis": _bool_map_to_dict(dict(mode.challenge_emphasis)),
        "cognitive_posture": mode.cognitive_posture,
        "name": mode.name,
        "output_bias": _bool_map_to_dict(dict(mode.output_bias)),
        "purpose": mode.purpose,
        "risk_emphasis": _bool_map_to_dict(dict(mode.risk_emphasis)),
    }


def _invariant_to_dict(invariant: CommunicationModeInvariant) -> dict[str, Any]:
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


def registry_to_canonical_dict(registry: AurelCommunicationModeRegistry) -> dict[str, Any]:
    """Convert registry to a canonical primitive dict for hashing."""
    notes: dict[str, Any] = {} if registry.notes is None else dict(registry.notes)
    gb = registry.global_boundaries
    invariants = sorted(
        (_invariant_to_dict(inv) for inv in registry.invariants),
        key=lambda item: item["id"],
    )
    modes = {
        name: _mode_to_dict(registry.modes[name])
        for name in sorted(registry.modes)
    }
    return {
        "applies_to_agent": registry.applies_to_agent,
        "global_boundaries": {
            "modes_can_canonize_output": gb.modes_can_canonize_output,
            "modes_can_change_autonomy": gb.modes_can_change_autonomy,
            "modes_can_disable_constitutional_floor": gb.modes_can_disable_constitutional_floor,
            "modes_can_execute_actions": gb.modes_can_execute_actions,
            "modes_can_grant_permissions": gb.modes_can_grant_permissions,
            "modes_can_override_identity_kernel": gb.modes_can_override_identity_kernel,
            "modes_can_override_operator_contract": gb.modes_can_override_operator_contract,
            "modes_can_override_persona_manifest": gb.modes_can_override_persona_manifest,
            "modes_can_override_policy": gb.modes_can_override_policy,
            "modes_can_write_memory_directly": gb.modes_can_write_memory_directly,
        },
        "invariants": invariants,
        "modes": modes,
        "notes": notes,
        "registry_class": registry.registry_class,
        "registry_name": registry.registry_name,
        "schema_version": registry.schema_version,
    }


def compute_communication_mode_registry_hash(
    registry: AurelCommunicationModeRegistry,
) -> CommunicationModeRegistryHash:
    """Compute deterministic SHA-256 hash of canonical registry representation."""
    canonical = registry_to_canonical_dict(registry)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return CommunicationModeRegistryHash(algorithm="sha256", value=digest)
