"""Validation rules for Aurel Operator Relationship Contract (P1.4.3)."""
from __future__ import annotations

from pathlib import Path

from .operator_contract import (
    OPERATOR_CONTRACT_VALIDATOR_VERSION,
    AurelOperatorContract,
    OperatorContractAttestation,
    OperatorContractValidationResult,
    ValidationStatus,
)
from .operator_contract_hash import compute_operator_contract_hash

OPERATOR_CONTRACT_INVARIANT_KEY_RESOLVERS: dict[str, tuple[str, str]] = {
    "operator_final_authority": ("authority", "operator_final_authority"),
    "aurel_final_authority": ("authority", "aurel_final_authority"),
    "aurel_can_self_escalate": ("authority", "aurel_can_self_escalate"),
    "aurel_can_replace_operator": ("authority", "aurel_can_replace_operator"),
    "aurel_can_override_operator_judgment": ("authority", "aurel_can_override_operator_judgment"),
    "aurel_can_refuse_forbidden_action": ("authority", "aurel_can_refuse_forbidden_action"),
    "aurel_can_challenge_operator": ("authority", "aurel_can_challenge_operator"),
    "aurel_must_challenge_when_risk_detected": (
        "authority",
        "aurel_must_challenge_when_risk_detected",
    ),
    "disagreement_allowed": ("relationship_behavior", "disagreement_allowed"),
    "disagreement_must_be_explained": ("relationship_behavior", "disagreement_must_be_explained"),
    "risk_challenge_required": ("relationship_behavior", "risk_challenge_required"),
    "uncertainty_must_be_disclosed": ("relationship_behavior", "uncertainty_must_be_disclosed"),
    "tradeoffs_must_be_disclosed": ("relationship_behavior", "tradeoffs_must_be_disclosed"),
    "passive_obedience_required": ("relationship_behavior", "passive_obedience_required"),
    "blind_execution_forbidden": ("relationship_behavior", "blind_execution_forbidden"),
    "manipulation_forbidden": ("non_manipulation", "manipulation_forbidden"),
    "hidden_persuasion_forbidden": ("non_manipulation", "hidden_persuasion_forbidden"),
    "flattery_over_truth_forbidden": ("non_manipulation", "flattery_over_truth_forbidden"),
    "emotional_pressure_forbidden": ("non_manipulation", "emotional_pressure_forbidden"),
    "dark_pattern_guidance_forbidden": ("non_manipulation", "dark_pattern_guidance_forbidden"),
    "coercive_language_forbidden": ("non_manipulation", "coercive_language_forbidden"),
    "tool_access_implies_authority": ("execution_authority", "tool_access_implies_authority"),
    "serious_actions_require_authority_check": (
        "execution_authority",
        "serious_actions_require_authority_check",
    ),
    "irreversible_actions_require_operator_approval": (
        "execution_authority",
        "irreversible_actions_require_operator_approval",
    ),
    "external_side_effects_require_policy_allowance": (
        "execution_authority",
        "external_side_effects_require_policy_allowance",
    ),
    "memory_canon_changes_require_approval_or_future_policy": (
        "execution_authority",
        "memory_canon_changes_require_approval_or_future_policy",
    ),
    "serious_actions_must_be_traceable": (
        "accountability",
        "serious_actions_must_be_traceable",
    ),
    "operator_authorization_ref_required_for_high_risk": (
        "accountability",
        "operator_authorization_ref_required_for_high_risk",
    ),
    "aurel_must_explain_action_basis": ("accountability", "aurel_must_explain_action_basis"),
    "aurel_must_surface_reversibility": ("accountability", "aurel_must_surface_reversibility"),
    "aurel_must_surface_known_limitations": (
        "accountability",
        "aurel_must_surface_known_limitations",
    ),
    "cannot_override_identity_kernel": ("boundaries", "cannot_override_identity_kernel"),
    "cannot_override_persona_manifest_boundaries": (
        "boundaries",
        "cannot_override_persona_manifest_boundaries",
    ),
    "cannot_grant_tool_rights": ("boundaries", "cannot_grant_tool_rights"),
    "cannot_change_autonomy": ("boundaries", "cannot_change_autonomy"),
    "cannot_disable_constitutional_floor": (
        "boundaries",
        "cannot_disable_constitutional_floor",
    ),
    "cannot_canonize_untrusted_input": ("boundaries", "cannot_canonize_untrusted_input"),
    "cannot_expand_delegation_scope": ("boundaries", "cannot_expand_delegation_scope"),
}


def _resolve_invariant_value(contract: AurelOperatorContract, key: str) -> bool | None:
    resolver = OPERATOR_CONTRACT_INVARIANT_KEY_RESOLVERS.get(key)
    if resolver is None:
        return None
    section_name, field_name = resolver
    section = getattr(contract, section_name)
    return getattr(section, field_name)


def validate_operator_contract(
    contract: AurelOperatorContract,
) -> OperatorContractValidationResult:
    """Validate contract against P1.4.3 operator relationship rules."""
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

    must_equal(contract.applies_to_agent, "Aurel", "applies_to_agent")
    must_equal(
        contract.contract_class,
        "principal_delegate_relationship",
        "contract_class",
    )

    principal = contract.parties.principal
    delegate = contract.parties.delegate
    must_equal(principal.role, "final_authority", "parties.principal.role")
    must_equal(principal.type, "human_operator", "parties.principal.type")
    must_equal(delegate.role, "advisor_executor_under_authority", "parties.delegate.role")
    must_equal(delegate.type, "ai_agent", "parties.delegate.type")

    auth = contract.authority
    must_equal(auth.operator_final_authority, True, "authority.operator_final_authority")
    must_equal(auth.aurel_final_authority, False, "authority.aurel_final_authority")
    must_equal(auth.aurel_can_self_escalate, False, "authority.aurel_can_self_escalate")
    must_equal(auth.aurel_can_replace_operator, False, "authority.aurel_can_replace_operator")
    must_equal(
        auth.aurel_can_override_operator_judgment,
        False,
        "authority.aurel_can_override_operator_judgment",
    )
    must_equal(
        auth.aurel_can_refuse_forbidden_action,
        True,
        "authority.aurel_can_refuse_forbidden_action",
    )
    must_equal(auth.aurel_can_challenge_operator, True, "authority.aurel_can_challenge_operator")
    must_equal(
        auth.aurel_must_challenge_when_risk_detected,
        True,
        "authority.aurel_must_challenge_when_risk_detected",
    )

    rel = contract.relationship_behavior
    must_equal(rel.disagreement_allowed, True, "relationship_behavior.disagreement_allowed")
    must_equal(
        rel.disagreement_must_be_explained,
        True,
        "relationship_behavior.disagreement_must_be_explained",
    )
    must_equal(rel.risk_challenge_required, True, "relationship_behavior.risk_challenge_required")
    must_equal(
        rel.uncertainty_must_be_disclosed,
        True,
        "relationship_behavior.uncertainty_must_be_disclosed",
    )
    must_equal(
        rel.tradeoffs_must_be_disclosed,
        True,
        "relationship_behavior.tradeoffs_must_be_disclosed",
    )
    must_equal(
        rel.passive_obedience_required,
        False,
        "relationship_behavior.passive_obedience_required",
    )
    must_equal(
        rel.blind_execution_forbidden,
        True,
        "relationship_behavior.blind_execution_forbidden",
    )

    nm = contract.non_manipulation
    must_equal(nm.manipulation_forbidden, True, "non_manipulation.manipulation_forbidden")
    must_equal(
        nm.hidden_persuasion_forbidden,
        True,
        "non_manipulation.hidden_persuasion_forbidden",
    )
    must_equal(
        nm.flattery_over_truth_forbidden,
        True,
        "non_manipulation.flattery_over_truth_forbidden",
    )
    must_equal(
        nm.emotional_pressure_forbidden,
        True,
        "non_manipulation.emotional_pressure_forbidden",
    )
    must_equal(
        nm.dark_pattern_guidance_forbidden,
        True,
        "non_manipulation.dark_pattern_guidance_forbidden",
    )
    must_equal(
        nm.coercive_language_forbidden,
        True,
        "non_manipulation.coercive_language_forbidden",
    )

    exe = contract.execution_authority
    must_equal(
        exe.tool_access_implies_authority,
        False,
        "execution_authority.tool_access_implies_authority",
    )
    must_equal(
        exe.serious_actions_require_authority_check,
        True,
        "execution_authority.serious_actions_require_authority_check",
    )
    must_equal(
        exe.irreversible_actions_require_operator_approval,
        True,
        "execution_authority.irreversible_actions_require_operator_approval",
    )
    must_equal(
        exe.external_side_effects_require_policy_allowance,
        True,
        "execution_authority.external_side_effects_require_policy_allowance",
    )
    must_equal(
        exe.memory_canon_changes_require_approval_or_future_policy,
        True,
        "execution_authority.memory_canon_changes_require_approval_or_future_policy",
    )

    acc = contract.accountability
    must_equal(
        acc.serious_actions_must_be_traceable,
        True,
        "accountability.serious_actions_must_be_traceable",
    )
    must_equal(
        acc.operator_authorization_ref_required_for_high_risk,
        True,
        "accountability.operator_authorization_ref_required_for_high_risk",
    )
    must_equal(
        acc.aurel_must_explain_action_basis,
        True,
        "accountability.aurel_must_explain_action_basis",
    )
    must_equal(
        acc.aurel_must_surface_reversibility,
        True,
        "accountability.aurel_must_surface_reversibility",
    )
    must_equal(
        acc.aurel_must_surface_known_limitations,
        True,
        "accountability.aurel_must_surface_known_limitations",
    )

    b = contract.boundaries
    must_equal(
        b.cannot_override_identity_kernel,
        True,
        "boundaries.cannot_override_identity_kernel",
    )
    must_equal(
        b.cannot_override_persona_manifest_boundaries,
        True,
        "boundaries.cannot_override_persona_manifest_boundaries",
    )
    must_equal(b.cannot_grant_tool_rights, True, "boundaries.cannot_grant_tool_rights")
    must_equal(b.cannot_change_autonomy, True, "boundaries.cannot_change_autonomy")
    must_equal(
        b.cannot_disable_constitutional_floor,
        True,
        "boundaries.cannot_disable_constitutional_floor",
    )
    must_equal(
        b.cannot_canonize_untrusted_input,
        True,
        "boundaries.cannot_canonize_untrusted_input",
    )
    must_equal(
        b.cannot_expand_delegation_scope,
        True,
        "boundaries.cannot_expand_delegation_scope",
    )

    seen_ids: set[str] = set()
    for invariant in contract.invariants:
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

        actual = _resolve_invariant_value(contract, invariant.key)
        if actual is None:
            fail(f"invariant {invariant.id}: unknown key {invariant.key!r}", critical=True)
            continue
        if invariant.expected_value != actual:
            fail(
                f"invariant {invariant.id}: expected_value {invariant.expected_value!r} "
                f"does not match contract field {invariant.key}={actual!r}",
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
    return OperatorContractValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def build_operator_contract_attestation(
    contract: AurelOperatorContract,
    path: str | Path,
) -> OperatorContractAttestation:
    """Build attestation record for a validated operator contract."""
    validation = validate_operator_contract(contract)
    status: ValidationStatus = "valid" if validation.valid else "invalid"
    contract_hash = compute_operator_contract_hash(contract)
    return OperatorContractAttestation(
        schema_version=contract.schema_version,
        contract_hash=contract_hash.value,
        hash_algorithm=contract_hash.algorithm,
        config_path=str(Path(path)),
        validation_status=status,
        validator_version=OPERATOR_CONTRACT_VALIDATOR_VERSION,
        critical_failures=validation.critical_failures,
    )


def write_operator_contract_attestation(
    attestation: OperatorContractAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    import json

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "contract_hash": attestation.contract_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "config_path": attestation.config_path,
        "validation_status": attestation.validation_status,
        "validator_version": attestation.validator_version,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
