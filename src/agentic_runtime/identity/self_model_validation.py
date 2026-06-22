"""Validation rules for Aurel Self-Model (P1.4.6)."""
from __future__ import annotations

from .capability_status import ALLOWED_CAPABILITY_STATUSES, REQUIRED_CAPABILITY_STATUSES
from .self_model import AurelSelfModel, SelfModelCapability
from .self_model_policy import (
    SELF_MODEL_VALIDATOR_VERSION,
    SelfModelPolicy,
    SelfModelPolicyValidationResult,
)
from .self_model import SelfModelValidationResult

POLICY_INVARIANT_KEY_RESOLVERS: dict[str, tuple[str, str]] = {
    "never_claim_roadmap_as_runtime": ("honesty", "never_claim_roadmap_as_runtime"),
    "never_claim_verification_without_evidence": (
        "honesty",
        "never_claim_verification_without_evidence",
    ),
    "self_model_can_grant_authority": ("boundaries", "self_model_can_grant_authority"),
    "self_model_can_change_autonomy": ("boundaries", "self_model_can_change_autonomy"),
    "self_model_can_verify_capability_by_itself": (
        "boundaries",
        "self_model_can_verify_capability_by_itself",
    ),
    "self_model_can_write_memory": ("boundaries", "self_model_can_write_memory"),
    "self_model_can_modify_policy": ("boundaries", "self_model_can_modify_policy"),
}


from .capability_inventory import IMPLEMENTED_CAPABILITY_IDS, PLANNED_CAPABILITY_IDS

def _resolve_policy_invariant_value(policy: SelfModelPolicy, key: str) -> bool | None:
    resolver = POLICY_INVARIANT_KEY_RESOLVERS.get(key)
    if resolver is None:
        return None
    section_name, field_name = resolver
    section = getattr(policy, section_name, None)
    if section is None:
        return None
    return getattr(section, field_name, None)


def validate_self_model_policy(policy: SelfModelPolicy) -> SelfModelPolicyValidationResult:
    """Strictly validate self-model policy configuration."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    if policy.applies_to_agent != "Aurel":
        errors.append('applies_to_agent must be "Aurel"')
    if policy.policy_class != "honest_runtime_self_description":
        errors.append('policy_class must be "honest_runtime_self_description"')

    req = policy.source_requirements
    for field_name, expected in (
        ("identity_kernel_required", True),
        ("persona_manifest_required", True),
        ("operator_contract_required", True),
        ("communication_mode_registry_required", True),
        ("identity_prompt_compiler_policy_required", True),
    ):
        if getattr(req, field_name) is not expected:
            errors.append(f"source_requirements.{field_name} must be {expected}")

    honesty = policy.honesty
    for field_name, expected in (
        ("distinguish_planned_from_implemented", True),
        ("distinguish_implemented_from_verified", True),
        ("distinguish_unavailable_from_unverified", True),
        ("never_claim_roadmap_as_runtime", True),
        ("never_claim_verification_without_evidence", True),
        ("mark_unknown_as_unknown", True),
        ("expose_known_limitations", True),
    ):
        if getattr(honesty, field_name) is not expected:
            errors.append(f"honesty.{field_name} must be {expected}")

    allowed = set(policy.capability_statuses.allowed_statuses)
    if not REQUIRED_CAPABILITY_STATUSES.issubset(allowed):
        missing = sorted(REQUIRED_CAPABILITY_STATUSES - allowed)
        errors.append(f"capability_statuses.allowed_statuses missing required values: {missing}")

    boundaries = policy.boundaries
    for field_name, expected in (
        ("self_model_can_grant_authority", False),
        ("self_model_can_change_identity", False),
        ("self_model_can_change_autonomy", False),
        ("self_model_can_verify_capability_by_itself", False),
        ("self_model_can_write_memory", False),
        ("self_model_can_modify_policy", False),
    ):
        if getattr(boundaries, field_name) is not expected:
            errors.append(f"boundaries.{field_name} must be {expected}")

    sections = policy.required_sections
    for field_name, expected in (
        ("include_identity_summary", True),
        ("include_source_hashes", True),
        ("include_authority_boundaries", True),
        ("include_capability_inventory", True),
        ("include_known_limitations", True),
        ("include_non_goals", True),
        ("include_evidence_posture", True),
        ("include_next_unimplemented_modules", True),
    ):
        if getattr(sections, field_name) is not expected:
            errors.append(f"required_sections.{field_name} must be {expected}")

    for invariant in policy.invariants:
        if not invariant.id.strip():
            errors.append("invariant id must be non-empty")
        if not invariant.key.strip():
            errors.append(f"invariant[{invariant.id}].key must be non-empty")
        if not invariant.statement.strip():
            errors.append(f"invariant[{invariant.id}].statement must be non-empty")
        if not invariant.rationale.strip():
            errors.append(f"invariant[{invariant.id}].rationale must be non-empty")
        if invariant.severity == "critical" and invariant.mutable:
            errors.append(f"invariant[{invariant.id}]: critical invariants must be immutable")
        resolved = _resolve_policy_invariant_value(policy, invariant.key)
        if resolved is None:
            errors.append(f"invariant[{invariant.id}]: unknown key {invariant.key!r}")
            continue
        if resolved != invariant.expected_value:
            errors.append(
                f"invariant[{invariant.id}]: expected_value {invariant.expected_value} "
                f"does not match policy field {invariant.key}={resolved}"
            )
        if invariant.severity == "critical" and invariant.violation_action != "fail_build":
            critical_failures.append(
                f"invariant[{invariant.id}]: critical invariants must use fail_build"
            )

    valid = not errors and not critical_failures
    return SelfModelPolicyValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


def _require_phrase(text: str, phrases: tuple[str, ...], label: str, errors: list[str]) -> None:
    if not any(phrase.lower() in text for phrase in phrases):
        errors.append(f"missing required content: {label}")


def _forbidden_phrase(text: str, phrases: tuple[str, ...], label: str, errors: list[str]) -> None:
    if any(phrase.lower() in text for phrase in phrases):
        errors.append(f"forbidden content: {label}")


def _validate_capability(cap: SelfModelCapability, errors: list[str]) -> None:
    if cap.status not in ALLOWED_CAPABILITY_STATUSES:
        errors.append(f"capability[{cap.id}]: invalid status {cap.status!r}")
    if cap.status == "verified" and not cap.evidence_ref:
        errors.append(f"capability[{cap.id}]: verified status requires evidence_ref")
    if cap.id in PLANNED_CAPABILITY_IDS and cap.status == "implemented":
        errors.append(
            f"capability[{cap.id}]: planned roadmap module must not be marked implemented"
        )
    if cap.id in IMPLEMENTED_CAPABILITY_IDS and cap.status == "verified" and not cap.evidence_ref:
        errors.append(
            f"capability[{cap.id}]: implemented module must not be verified without evidence_ref"
        )


def validate_aurel_self_model(
    model: AurelSelfModel,
    policy: SelfModelPolicy,
) -> SelfModelValidationResult:
    """Validate compiled self-model required content and honesty rules."""
    errors: list[str] = []
    warnings: list[str] = []
    critical_failures: list[str] = []

    if model.agent_name != "Aurel":
        errors.append('agent_name must be "Aurel"')

    bundle = model.source_bundle
    for label, value in (
        ("identity_kernel_hash", bundle.identity_kernel_hash),
        ("persona_manifest_hash", bundle.persona_manifest_hash),
        ("operator_contract_hash", bundle.operator_contract_hash),
        ("communication_modes_hash", bundle.communication_modes_hash),
        ("identity_prompt_compiler_policy_hash", bundle.identity_prompt_compiler_policy_hash),
    ):
        if not value or len(value) != 64:
            errors.append(f"missing or invalid {label}")

    if not model.identity_summary:
        errors.append("identity_summary must be non-empty")
    if not model.authority_boundaries:
        errors.append("authority_boundaries must be non-empty")
    if not model.capability_inventory:
        errors.append("capability_inventory must be non-empty")
    if not model.known_limitations:
        errors.append("known_limitations must be non-empty")
    if not model.non_goals:
        errors.append("non_goals must be non-empty")
    if not model.next_unimplemented_modules:
        errors.append("next_unimplemented_modules must be non-empty")

    identity_text = "\n".join(model.identity_summary).lower()
    authority_text = "\n".join(model.authority_boundaries).lower()
    non_goals_text = "\n".join(model.non_goals).lower()

    _require_phrase(identity_text, ("aurel",), "agent identity", errors)
    _require_phrase(identity_text, ("operator", "final authority"), "operator relationship", errors)
    _require_phrase(authority_text, ("self-escalat", "cannot self-escalate"), "no self-escalation", errors)
    _require_phrase(
        authority_text,
        ("verified", "without evidence", "evidence"),
        "no verified claims without evidence",
        errors,
    )

    posture = model.evidence_posture
    if posture.evaluation_mirror_available:
        errors.append("evidence_posture must not claim Evaluation Mirror is available before P1.5")
    if posture.verified_capability_claims_allowed and not any(
        cap.evidence_ref for cap in model.capability_inventory if cap.status == "verified"
    ):
        if posture.verified_capability_claims_allowed:
            errors.append(
                "verified_capability_claims_allowed must be false without evidence-backed claims"
            )

    for cap in model.capability_inventory:
        _validate_capability(cap, errors)

    _require_phrase(non_goals_text, ("does not authorize autonomy", "does not change autonomy"), "non-goals autonomy boundary", errors)
    _require_phrase(non_goals_text, ("does not imply consciousness",), "non-goals consciousness boundary", errors)
    _require_phrase(
        non_goals_text,
        ("does not verify capabilities", "does not verify capability"),
        "non-goals self-verification boundary",
        errors,
    )
    _require_phrase(non_goals_text, ("does not grant authority", "does not authorize tool"), "non-goals authority boundary", errors)

    positive_text = "\n".join([identity_text, authority_text]).lower()
    _forbidden_phrase(
        positive_text,
        ("can grant authority", "grants authority"),
        "self-model must not grant authority",
        errors,
    )
    _forbidden_phrase(
        positive_text,
        ("can change autonomy", "changes autonomy"),
        "self-model must not change autonomy",
        errors,
    )

    if policy.honesty.never_claim_roadmap_as_runtime:
        for cap in model.capability_inventory:
            if cap.id in PLANNED_CAPABILITY_IDS and cap.status in ("implemented", "verified"):
                errors.append(
                    f"capability[{cap.id}]: roadmap module presented as active runtime feature"
                )

    for err in errors:
        critical_failures.append(err)

    valid = not errors
    return SelfModelValidationResult(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=tuple(critical_failures),
    )


__all__ = [
    "SELF_MODEL_VALIDATOR_VERSION",
    "validate_aurel_self_model",
    "validate_self_model_policy",
]
