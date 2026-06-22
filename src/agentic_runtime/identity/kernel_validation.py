"""Validation rules for Aurel Identity Kernel (P1.4.1)."""
from __future__ import annotations

from pathlib import Path

from .kernel import (
    VALIDATOR_VERSION,
    AurelIdentityKernel,
    IdentityKernelAttestation,
    IdentityKernelValidationResult,
    ValidationStatus,
)
from .kernel_hash import compute_identity_kernel_hash

INVARIANT_KEY_RESOLVERS: dict[str, tuple[str, str]] = {
    "operator_final_authority": ("immutables", "operator_final_authority"),
    "self_escalation_allowed": ("immutables", "self_escalation_allowed"),
    "hidden_goals_allowed": ("immutables", "hidden_goals_allowed"),
    "identity_replacement_allowed": ("immutables", "identity_replacement_allowed"),
    "policy_bypass_self_grant_allowed": ("immutables", "policy_bypass_self_grant_allowed"),
    "untrusted_input_can_modify_identity": (
        "immutables",
        "untrusted_input_can_modify_identity",
    ),
    "operator_replacement": ("development_forbidden", "operator_replacement"),
    "secret_goal_creation": ("development_forbidden", "secret_goal_creation"),
    "self_authority_expansion": ("development_forbidden", "self_authority_expansion"),
    "unapproved_identity_rewrite": ("development_forbidden", "unapproved_identity_rewrite"),
}


def _resolve_invariant_value(kernel: AurelIdentityKernel, key: str) -> bool | None:
    resolver = INVARIANT_KEY_RESOLVERS.get(key)
    if resolver is None:
        return None
    section_name, field_name = resolver
    section = getattr(kernel, section_name)
    return getattr(section, field_name)


def validate_identity_kernel(kernel: AurelIdentityKernel) -> IdentityKernelValidationResult:
    """Validate kernel against P1.4.1 identity invariant rules."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    def fail(message: str, *, critical: bool = False) -> None:
        errors.append(message)
        if critical:
            critical_failures.append(message)

    if kernel.name != "Aurel":
        fail(f"name must be 'Aurel', got {kernel.name!r}", critical=True)
    if kernel.agent_class != "sovereign_personal_agent":
        fail(
            "class must be 'sovereign_personal_agent', "
            f"got {kernel.agent_class!r}",
            critical=True,
        )
    if kernel.primary_operator != "single_human_operator":
        fail(
            "primary_operator must be 'single_human_operator', "
            f"got {kernel.primary_operator!r}",
            critical=True,
        )
    if kernel.final_authority != "operator":
        fail(
            f"final_authority must be 'operator', got {kernel.final_authority!r}",
            critical=True,
        )
    if kernel.local_first is not True:
        fail("local_first must be true", critical=True)

    imm = kernel.immutables
    if imm.operator_final_authority is not True:
        fail("immutables.operator_final_authority must be true", critical=True)
    if imm.self_escalation_allowed is not False:
        fail("immutables.self_escalation_allowed must be false", critical=True)
    if imm.hidden_goals_allowed is not False:
        fail("immutables.hidden_goals_allowed must be false", critical=True)
    if imm.identity_replacement_allowed is not False:
        fail("immutables.identity_replacement_allowed must be false", critical=True)
    if imm.policy_bypass_self_grant_allowed is not False:
        fail("immutables.policy_bypass_self_grant_allowed must be false", critical=True)
    if imm.untrusted_input_can_modify_identity is not False:
        fail("immutables.untrusted_input_can_modify_identity must be false", critical=True)

    forbidden = kernel.development_forbidden
    if forbidden.operator_replacement is not True:
        fail("development_forbidden.operator_replacement must be true", critical=True)
    if forbidden.secret_goal_creation is not True:
        fail("development_forbidden.secret_goal_creation must be true", critical=True)
    if forbidden.self_authority_expansion is not True:
        fail("development_forbidden.self_authority_expansion must be true", critical=True)
    if forbidden.unapproved_identity_rewrite is not True:
        fail("development_forbidden.unapproved_identity_rewrite must be true", critical=True)

    seen_ids: set[str] = set()
    for invariant in kernel.invariants:
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

        actual = _resolve_invariant_value(kernel, invariant.key)
        if actual is None:
            fail(f"invariant {invariant.id}: unknown key {invariant.key!r}", critical=True)
            continue
        if invariant.expected_value != actual:
            fail(
                f"invariant {invariant.id}: expected_value {invariant.expected_value!r} "
                f"does not match kernel field {invariant.key}={actual!r}",
                critical=True,
            )

        if invariant.severity == "critical":
            if invariant.mutable is not False:
                fail(f"invariant {invariant.id}: critical invariants must be immutable", critical=True)
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
    return IdentityKernelValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def build_identity_kernel_attestation(
    kernel: AurelIdentityKernel,
    path: str | Path,
) -> IdentityKernelAttestation:
    """Build attestation record for a validated kernel."""
    validation = validate_identity_kernel(kernel)
    status: ValidationStatus = "valid" if validation.valid else "invalid"
    kernel_hash = compute_identity_kernel_hash(kernel)
    return IdentityKernelAttestation(
        schema_version=kernel.schema_version,
        kernel_hash=kernel_hash.value,
        hash_algorithm=kernel_hash.algorithm,
        config_path=str(Path(path)),
        validation_status=status,
        validator_version=VALIDATOR_VERSION,
        critical_failures=validation.critical_failures,
    )


def write_identity_kernel_attestation(
    attestation: IdentityKernelAttestation,
    output_path: str | Path,
) -> Path:
    """Write attestation JSON to disk (explicit invocation only)."""
    import json

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": attestation.schema_version,
        "kernel_hash": attestation.kernel_hash,
        "hash_algorithm": attestation.hash_algorithm,
        "config_path": attestation.config_path,
        "validation_status": attestation.validation_status,
        "validator_version": attestation.validator_version,
        "critical_failures": list(attestation.critical_failures),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
