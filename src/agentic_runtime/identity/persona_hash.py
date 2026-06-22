"""Deterministic hashing for Aurel Persona Manifest (P1.4.2)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .persona import AurelPersonaManifest, PersonaInvariant, PersonaManifestHash


def _invariant_to_dict(invariant: PersonaInvariant) -> dict[str, Any]:
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


def persona_to_canonical_dict(manifest: AurelPersonaManifest) -> dict[str, Any]:
    """Convert manifest to a canonical primitive dict for hashing."""
    notes: dict[str, Any] = {} if manifest.notes is None else dict(manifest.notes)
    invariants = sorted(
        (_invariant_to_dict(inv) for inv in manifest.invariants),
        key=lambda item: item["id"],
    )
    voice = manifest.voice
    posture = manifest.posture
    honesty = manifest.honesty
    risk = manifest.risk_communication
    challenge = manifest.challenge_behavior
    operator = manifest.operator_interaction
    boundaries = manifest.boundaries
    prompt_safety = manifest.prompt_safety

    return {
        "applies_to_agent": manifest.applies_to_agent,
        "authority_level": manifest.authority_level,
        "boundaries": {
            "cannot_canonize_untrusted_input": boundaries.cannot_canonize_untrusted_input,
            "cannot_convert_style_into_authority": (
                boundaries.cannot_convert_style_into_authority
            ),
            "cannot_disable_constitutional_floor": (
                boundaries.cannot_disable_constitutional_floor
            ),
            "cannot_grant_tool_rights": boundaries.cannot_grant_tool_rights,
            "cannot_increase_autonomy": boundaries.cannot_increase_autonomy,
            "cannot_modify_operator_contract": boundaries.cannot_modify_operator_contract,
            "cannot_override_identity_kernel": boundaries.cannot_override_identity_kernel,
        },
        "can_change_autonomy": manifest.can_change_autonomy,
        "can_grant_permissions": manifest.can_grant_permissions,
        "can_override_identity_kernel": manifest.can_override_identity_kernel,
        "can_override_policy": manifest.can_override_policy,
        "challenge_behavior": {
            "challenge_architectural_collapse": challenge.challenge_architectural_collapse,
            "challenge_fake_capability": challenge.challenge_fake_capability,
            "challenge_governance_theater": challenge.challenge_governance_theater,
            "challenge_overbuilding": challenge.challenge_overbuilding,
            "challenge_weak_assumptions": challenge.challenge_weak_assumptions,
            "challenge_when_user_requests_speed_over_safety": (
                challenge.challenge_when_user_requests_speed_over_safety
            ),
        },
        "honesty": {
            "admit_missing_context": honesty.admit_missing_context,
            "cite_sources_when_required": honesty.cite_sources_when_required,
            "distinguish_fact_from_inference": honesty.distinguish_fact_from_inference,
            "distinguish_implemented_from_verified": (
                honesty.distinguish_implemented_from_verified
            ),
            "distinguish_planned_from_implemented": (
                honesty.distinguish_planned_from_implemented
            ),
            "explain_uncertainty": honesty.explain_uncertainty,
            "never_claim_unverified_capability": honesty.never_claim_unverified_capability,
        },
        "invariants": invariants,
        "manifest_class": manifest.manifest_class,
        "name": manifest.name,
        "notes": notes,
        "operator_interaction": {
            "may_disagree_with_operator": operator.may_disagree_with_operator,
            "must_explain_disagreement": operator.must_explain_disagreement,
            "must_not_hide_tradeoffs": operator.must_not_hide_tradeoffs,
            "must_not_pressure_operator": operator.must_not_pressure_operator,
            "must_not_replace_operator_judgment": operator.must_not_replace_operator_judgment,
            "respect_operator_final_authority": operator.respect_operator_final_authority,
        },
        "posture": {
            "architect": posture.architect,
            "challenger": posture.challenger,
            "execution_assistant": posture.execution_assistant,
            "manipulative_persuasion": posture.manipulative_persuasion,
            "mentor": posture.mentor,
            "mirror": posture.mirror,
            "passive_servility": posture.passive_servility,
        },
        "prompt_safety": {
            "compile_to_safe_summary_required": prompt_safety.compile_to_safe_summary_required,
            "include_authority_boundaries_in_summary": (
                prompt_safety.include_authority_boundaries_in_summary
            ),
            "include_capability_honesty_in_summary": (
                prompt_safety.include_capability_honesty_in_summary
            ),
            "raw_manifest_in_prompt_forbidden": prompt_safety.raw_manifest_in_prompt_forbidden,
        },
        "risk_communication": {
            "challenge_unsafe_instructions": risk.challenge_unsafe_instructions,
            "surface_material_risk": risk.surface_material_risk,
            "warn_on_high_uncertainty": risk.warn_on_high_uncertainty,
            "warn_on_irreversible_actions": risk.warn_on_irreversible_actions,
            "warn_on_unverified_capability_claims": risk.warn_on_unverified_capability_claims,
        },
        "schema_version": manifest.schema_version,
        "voice": {
            "default_style": voice.default_style,
            "default_tone": voice.default_tone,
            "excessive_flattery_forbidden": voice.excessive_flattery_forbidden,
            "false_certainty_forbidden": voice.false_certainty_forbidden,
            "language_behavior": voice.language_behavior,
            "markdown_preferred": voice.markdown_preferred,
            "poetic_layer_allowed": voice.poetic_layer_allowed,
            "symbolic_layer_allowed": voice.symbolic_layer_allowed,
            "verbosity": voice.verbosity,
        },
    }


def compute_persona_manifest_hash(manifest: AurelPersonaManifest) -> PersonaManifestHash:
    """Compute deterministic SHA-256 hash of canonical manifest representation."""
    canonical = persona_to_canonical_dict(manifest)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return PersonaManifestHash(algorithm="sha256", value=digest)
