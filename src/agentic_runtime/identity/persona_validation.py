"""Validation rules for Aurel Persona Manifest (P1.4.2)."""
from __future__ import annotations

from pathlib import Path

from .persona import (
    PERSONA_VALIDATOR_VERSION,
    AurelPersonaManifest,
    PersonaManifestAttestation,
    PersonaManifestValidationResult,
    ValidationStatus,
)
from .persona_hash import compute_persona_manifest_hash

# Maps invariant key -> (section attribute, field) for expected_value cross-check.
# Top-level fields use section "" (the manifest itself).
PERSONA_INVARIANT_KEY_RESOLVERS: dict[str, tuple[str, str]] = {
    "can_grant_permissions": ("", "can_grant_permissions"),
    "can_override_identity_kernel": ("", "can_override_identity_kernel"),
    "can_override_policy": ("", "can_override_policy"),
    "can_change_autonomy": ("", "can_change_autonomy"),
    "never_claim_unverified_capability": ("honesty", "never_claim_unverified_capability"),
    "false_certainty_forbidden": ("voice", "false_certainty_forbidden"),
    "excessive_flattery_forbidden": ("voice", "excessive_flattery_forbidden"),
    "raw_manifest_in_prompt_forbidden": ("prompt_safety", "raw_manifest_in_prompt_forbidden"),
    "compile_to_safe_summary_required": ("prompt_safety", "compile_to_safe_summary_required"),
    "cannot_grant_tool_rights": ("boundaries", "cannot_grant_tool_rights"),
    "cannot_increase_autonomy": ("boundaries", "cannot_increase_autonomy"),
    "cannot_convert_style_into_authority": ("boundaries", "cannot_convert_style_into_authority"),
    "cannot_override_identity_kernel": ("boundaries", "cannot_override_identity_kernel"),
    "surface_material_risk": ("risk_communication", "surface_material_risk"),
    "warn_on_irreversible_actions": ("risk_communication", "warn_on_irreversible_actions"),
    "respect_operator_final_authority": (
        "operator_interaction",
        "respect_operator_final_authority",
    ),
    "must_not_replace_operator_judgment": (
        "operator_interaction",
        "must_not_replace_operator_judgment",
    ),
}


def _resolve_invariant_value(manifest: AurelPersonaManifest, key: str) -> bool | None:
    resolver = PERSONA_INVARIANT_KEY_RESOLVERS.get(key)
    if resolver is None:
        return None
    section_name, field_name = resolver
    target = manifest if section_name == "" else getattr(manifest, section_name)
    return getattr(target, field_name)


def validate_persona_manifest(
    manifest: AurelPersonaManifest,
) -> PersonaManifestValidationResult:
    """Validate manifest against P1.4.2 expression-contract rules."""
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

    must_equal(manifest.applies_to_agent, "Aurel", "applies_to_agent")
    must_equal(manifest.manifest_class, "expression_contract", "manifest_class")
    must_equal(manifest.authority_level, "none", "authority_level")

    must_equal(manifest.can_grant_permissions, False, "can_grant_permissions")
    must_equal(manifest.can_override_identity_kernel, False, "can_override_identity_kernel")
    must_equal(manifest.can_override_policy, False, "can_override_policy")
    must_equal(manifest.can_change_autonomy, False, "can_change_autonomy")

    must_equal(manifest.voice.false_certainty_forbidden, True, "voice.false_certainty_forbidden")
    must_equal(
        manifest.voice.excessive_flattery_forbidden, True, "voice.excessive_flattery_forbidden"
    )

    h = manifest.honesty
    must_equal(h.explain_uncertainty, True, "honesty.explain_uncertainty")
    must_equal(h.admit_missing_context, True, "honesty.admit_missing_context")
    must_equal(h.distinguish_fact_from_inference, True, "honesty.distinguish_fact_from_inference")
    must_equal(
        h.distinguish_planned_from_implemented,
        True,
        "honesty.distinguish_planned_from_implemented",
    )
    must_equal(
        h.distinguish_implemented_from_verified,
        True,
        "honesty.distinguish_implemented_from_verified",
    )
    must_equal(
        h.never_claim_unverified_capability, True, "honesty.never_claim_unverified_capability"
    )

    r = manifest.risk_communication
    must_equal(r.surface_material_risk, True, "risk_communication.surface_material_risk")
    must_equal(
        r.warn_on_irreversible_actions, True, "risk_communication.warn_on_irreversible_actions"
    )
    must_equal(
        r.warn_on_unverified_capability_claims,
        True,
        "risk_communication.warn_on_unverified_capability_claims",
    )

    c = manifest.challenge_behavior
    must_equal(c.challenge_weak_assumptions, True, "challenge_behavior.challenge_weak_assumptions")
    must_equal(
        c.challenge_governance_theater, True, "challenge_behavior.challenge_governance_theater"
    )
    must_equal(c.challenge_fake_capability, True, "challenge_behavior.challenge_fake_capability")
    must_equal(c.challenge_overbuilding, True, "challenge_behavior.challenge_overbuilding")

    o = manifest.operator_interaction
    must_equal(
        o.respect_operator_final_authority,
        True,
        "operator_interaction.respect_operator_final_authority",
    )
    must_equal(
        o.must_not_replace_operator_judgment,
        True,
        "operator_interaction.must_not_replace_operator_judgment",
    )
    must_equal(o.must_not_hide_tradeoffs, True, "operator_interaction.must_not_hide_tradeoffs")
    must_equal(o.must_not_pressure_operator, True, "operator_interaction.must_not_pressure_operator")

    b = manifest.boundaries
    must_equal(
        b.cannot_override_identity_kernel, True, "boundaries.cannot_override_identity_kernel"
    )
    must_equal(
        b.cannot_modify_operator_contract, True, "boundaries.cannot_modify_operator_contract"
    )
    must_equal(b.cannot_grant_tool_rights, True, "boundaries.cannot_grant_tool_rights")
    must_equal(b.cannot_increase_autonomy, True, "boundaries.cannot_increase_autonomy")
    must_equal(
        b.cannot_disable_constitutional_floor,
        True,
        "boundaries.cannot_disable_constitutional_floor",
    )
    must_equal(
        b.cannot_canonize_untrusted_input, True, "boundaries.cannot_canonize_untrusted_input"
    )
    must_equal(
        b.cannot_convert_style_into_authority,
        True,
        "boundaries.cannot_convert_style_into_authority",
    )

    p = manifest.prompt_safety
    must_equal(
        p.raw_manifest_in_prompt_forbidden,
        True,
        "prompt_safety.raw_manifest_in_prompt_forbidden",
    )
    must_equal(
        p.compile_to_safe_summary_required,
        True,
        "prompt_safety.compile_to_safe_summary_required",
    )
    must_equal(
        p.include_authority_boundaries_in_summary,
        True,
        "prompt_safety.include_authority_boundaries_in_summary",
    )
    must_equal(
        p.include_capability_honesty_in_summary,
        True,
        "prompt_safety.include_capability_honesty_in_summary",
    )

    seen_ids: set[str] = set()
    for invariant in manifest.invariants:
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

        actual = _resolve_invariant_value(manifest, invariant.key)
        if actual is None:
            fail(f"invariant {invariant.id}: unknown key {invariant.key!r}", critical=True)
            continue
        if invariant.expected_value != actual:
            fail(
                f"invariant {invariant.id}: expected_value {invariant.expected_value!r} "
                f"does not match manifest field {invariant.key}={actual!r}",
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
    return PersonaManifestValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def build_persona_manifest_attestation(
    manifest: AurelPersonaManifest,
    path: str | Path,
) -> PersonaManifestAttestation:
    """Build attestation record for a validated persona manifest."""
    validation = validate_persona_manifest(manifest)
    status: ValidationStatus = "valid" if validation.valid else "invalid"
    persona_hash = compute_persona_manifest_hash(manifest)
    return PersonaManifestAttestation(
        schema_version=manifest.schema_version,
        persona_hash=persona_hash.value,
        hash_algorithm=persona_hash.algorithm,
        config_path=str(Path(path)),
        validation_status=status,
        validator_version=PERSONA_VALIDATOR_VERSION,
        critical_failures=validation.critical_failures,
    )


def write_persona_manifest_attestation(
    attestation: PersonaManifestAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    import json

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "persona_hash": attestation.persona_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "config_path": attestation.config_path,
        "validation_status": attestation.validation_status,
        "validator_version": attestation.validator_version,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
