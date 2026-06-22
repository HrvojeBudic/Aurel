"""Validation rules for Aurel Communication Modes registry (P1.4.4)."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .communication_modes import (
    COMMUNICATION_MODES_VALIDATOR_VERSION,
    REQUIRED_MODES,
    AurelCommunicationModeRegistry,
    CommunicationModeAttestation,
    CommunicationModeSpec,
    CommunicationModeValidationResult,
    ValidationStatus,
)
from .mode_hash import compute_communication_mode_registry_hash

GLOBAL_BOUNDARY_KEYS = (
    "modes_can_grant_permissions",
    "modes_can_change_autonomy",
    "modes_can_override_identity_kernel",
    "modes_can_override_persona_manifest",
    "modes_can_override_operator_contract",
    "modes_can_override_policy",
    "modes_can_disable_constitutional_floor",
    "modes_can_write_memory_directly",
    "modes_can_canonize_output",
    "modes_can_execute_actions",
)

MODE_BOUNDARY_KEYS = (
    "grants_permissions",
    "changes_autonomy",
    "executes_actions",
    "canonizes_output",
)

HERETIC_BOUNDARY_KEYS = (
    "writes_files",
    "modifies_policy",
    "modifies_identity",
    "modifies_memory",
    "modifies_tools",
    "modifies_autonomy",
    "real_world_side_effects",
)


def _resolve_invariant_value(registry: AurelCommunicationModeRegistry, key: str) -> bool | None:
    if key in GLOBAL_BOUNDARY_KEYS:
        return getattr(registry.global_boundaries, key)
    parts = key.split(".")
    if len(parts) == 3:
        mode_name, section, field = parts
        mode = registry.modes.get(mode_name.upper())
        if mode is None:
            return None
        section_map = getattr(mode, section, None)
        if section_map is None or not hasattr(section_map, "get"):
            return None
        if field not in section_map:
            return None
        return section_map[field]
    return None


def _validate_mode_boundaries(
    mode: CommunicationModeSpec,
    *,
    fail: Callable[..., None],
) -> None:
    for field in MODE_BOUNDARY_KEYS:
        value = mode.boundaries.get(field)
        if value is not False:
            fail(
                f"modes.{mode.name}.boundaries.{field} must be false, got {value!r}",
                critical=True,
            )


def validate_communication_mode_registry(
    registry: AurelCommunicationModeRegistry,
) -> CommunicationModeValidationResult:
    """Validate registry against P1.4.4 communication mode rules."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    def fail(message: str, *, critical: bool = False) -> None:
        errors.append(message)
        if critical:
            critical_failures.append(message)

    def must_equal(actual: object, expected: object, label: str) -> None:
        if actual != expected:
            fail(f"{label} must be {expected!r}, got {actual!r}", critical=True)

    must_equal(registry.applies_to_agent, "Aurel", "applies_to_agent")
    must_equal(registry.registry_class, "mode_expression_registry", "registry_class")

    gb = registry.global_boundaries
    for field in GLOBAL_BOUNDARY_KEYS:
        must_equal(getattr(gb, field), False, f"global_boundaries.{field}")

    for required in sorted(REQUIRED_MODES):
        if required not in registry.modes:
            fail(f"missing required mode: {required}", critical=True)

    for mode in registry.modes.values():
        if not mode.purpose.strip():
            fail(f"modes.{mode.name}.purpose must be non-empty", critical=True)
        if not mode.cognitive_posture.strip():
            fail(f"modes.{mode.name}.cognitive_posture must be non-empty", critical=True)
        _validate_mode_boundaries(mode, fail=fail)

    heretic = registry.modes.get("HERETIC")
    if heretic is not None:
        must_equal(
            heretic.output_bias.get("candidate_only"),
            True,
            "modes.HERETIC.output_bias.candidate_only",
        )
        for field in HERETIC_BOUNDARY_KEYS:
            must_equal(
                heretic.boundaries.get(field),
                False,
                f"modes.HERETIC.boundaries.{field}",
            )

    seen_ids: set[str] = set()
    for invariant in registry.invariants:
        if not invariant.id.strip():
            fail("invariant id must be non-empty", critical=True)
            continue
        if invariant.id in seen_ids:
            fail(f"duplicate invariant id: {invariant.id}", critical=True)
        seen_ids.add(invariant.id)

        if not invariant.key.strip():
            fail(f"invariant {invariant.id}: key must be non-empty", critical=True)
        if not invariant.statement.strip():
            fail(f"invariant {invariant.id}: statement must be non-empty", critical=True)
        if not invariant.rationale.strip():
            fail(f"invariant {invariant.id}: rationale must be non-empty", critical=True)

        actual = _resolve_invariant_value(registry, invariant.key)
        if actual is None:
            fail(f"invariant {invariant.id}: unknown key {invariant.key!r}", critical=True)
            continue
        if invariant.expected_value != actual:
            fail(
                f"invariant {invariant.id}: expected_value {invariant.expected_value!r} "
                f"does not match registry field {invariant.key}={actual!r}",
                critical=True,
            )

        if invariant.severity == "critical":
            if invariant.mutable is not False:
                fail(
                    f"invariant {invariant.id}: critical invariants must be immutable",
                    critical=True,
                )
            if invariant.violation_action != "fail_boot":
                fail(
                    f"invariant {invariant.id}: critical invariants must use fail_boot",
                    critical=True,
                )
        elif invariant.violation_action == "fail_boot":
            warnings.append(
                f"invariant {invariant.id}: non-critical invariant uses fail_boot"
            )

    valid = not errors
    return CommunicationModeValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def build_communication_mode_attestation(
    registry: AurelCommunicationModeRegistry,
    path: str | Path,
) -> CommunicationModeAttestation:
    """Build attestation record for a validated communication mode registry."""
    validation = validate_communication_mode_registry(registry)
    status: ValidationStatus = "valid" if validation.valid else "invalid"
    registry_hash = compute_communication_mode_registry_hash(registry)
    return CommunicationModeAttestation(
        schema_version=registry.schema_version,
        registry_hash=registry_hash.value,
        hash_algorithm=registry_hash.algorithm,
        config_path=str(Path(path)),
        validation_status=status,
        validator_version=COMMUNICATION_MODES_VALIDATOR_VERSION,
        critical_failures=validation.critical_failures,
    )


def write_communication_mode_attestation(
    attestation: CommunicationModeAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    import json

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "registry_hash": attestation.registry_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "config_path": attestation.config_path,
        "validation_status": attestation.validation_status,
        "validator_version": attestation.validator_version,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
