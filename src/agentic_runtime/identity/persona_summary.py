"""Deterministic safe summary for Aurel Persona Manifest (P1.4.2).

This is a preparation object for the future P1.4.5 Identity Prompt Context
Compiler. It is NOT the compiler. The safe summary never exposes raw YAML and
never includes permission-, tool-, or autonomy-granting language.
"""
from __future__ import annotations

from .persona import AurelPersonaManifest, PersonaSafeSummary


def build_persona_safe_summary(manifest: AurelPersonaManifest) -> PersonaSafeSummary:
    """Build a deterministic, prompt-safe summary of the persona manifest."""
    voice = manifest.voice
    posture = manifest.posture
    honesty = manifest.honesty
    risk = manifest.risk_communication
    challenge = manifest.challenge_behavior
    boundaries = manifest.boundaries

    voice_summary = (
        f"style={voice.default_style}; tone={voice.default_tone}; "
        f"verbosity={voice.verbosity}; language={voice.language_behavior}"
    )

    active_postures = [
        label
        for label, enabled in (
            ("mentor", posture.mentor),
            ("architect", posture.architect),
            ("challenger", posture.challenger),
            ("mirror", posture.mirror),
            ("execution_assistant", posture.execution_assistant),
        )
        if enabled
    ]
    posture_summary = ", ".join(active_postures)

    honesty_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Explain uncertainty explicitly.", honesty.explain_uncertainty),
            ("Admit missing context.", honesty.admit_missing_context),
            ("Distinguish fact from inference.", honesty.distinguish_fact_from_inference),
            (
                "Distinguish planned from implemented.",
                honesty.distinguish_planned_from_implemented,
            ),
            (
                "Distinguish implemented from verified.",
                honesty.distinguish_implemented_from_verified,
            ),
            ("Cite sources when required.", honesty.cite_sources_when_required),
        )
        if enabled
    )

    risk_communication_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Surface material risk.", risk.surface_material_risk),
            ("Challenge unsafe instructions.", risk.challenge_unsafe_instructions),
            ("Warn on irreversible actions.", risk.warn_on_irreversible_actions),
            ("Warn on high uncertainty.", risk.warn_on_high_uncertainty),
            (
                "Warn on unverified capability claims.",
                risk.warn_on_unverified_capability_claims,
            ),
        )
        if enabled
    )

    challenge_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Challenge weak assumptions.", challenge.challenge_weak_assumptions),
            ("Challenge architectural collapse.", challenge.challenge_architectural_collapse),
            ("Challenge governance theater.", challenge.challenge_governance_theater),
            ("Challenge fake capability.", challenge.challenge_fake_capability),
            ("Challenge overbuilding.", challenge.challenge_overbuilding),
            (
                "Challenge speed-over-safety requests.",
                challenge.challenge_when_user_requests_speed_over_safety,
            ),
        )
        if enabled
    )

    authority_boundaries: tuple[str, ...] = tuple(
        rule
        for rule, active in (
            ("Persona has no authority level.", manifest.authority_level == "none"),
            ("Persona cannot grant permissions.", not manifest.can_grant_permissions),
            (
                "Persona cannot override the Identity Kernel.",
                boundaries.cannot_override_identity_kernel,
            ),
            ("Persona cannot override policy.", not manifest.can_override_policy),
            ("Persona cannot change autonomy.", not manifest.can_change_autonomy),
            ("Persona cannot grant tool rights.", boundaries.cannot_grant_tool_rights),
            ("Persona cannot increase autonomy.", boundaries.cannot_increase_autonomy),
            (
                "Persona cannot disable the constitutional floor.",
                boundaries.cannot_disable_constitutional_floor,
            ),
            (
                "Persona cannot canonize untrusted input.",
                boundaries.cannot_canonize_untrusted_input,
            ),
            (
                "Persona cannot convert style into authority.",
                boundaries.cannot_convert_style_into_authority,
            ),
        )
        if active
    )

    capability_honesty_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            (
                "Never claim unverified capabilities as active.",
                honesty.never_claim_unverified_capability,
            ),
            (
                "Distinguish planned, implemented, and verified capabilities.",
                honesty.distinguish_planned_from_implemented
                and honesty.distinguish_implemented_from_verified,
            ),
            ("Do not present uncertainty as certainty.", voice.false_certainty_forbidden),
        )
        if enabled
    )

    return PersonaSafeSummary(
        manifest_name=manifest.name,
        applies_to_agent=manifest.applies_to_agent,
        voice_summary=voice_summary,
        posture_summary=posture_summary,
        honesty_rules=honesty_rules,
        risk_communication_rules=risk_communication_rules,
        challenge_rules=challenge_rules,
        authority_boundaries=authority_boundaries,
        capability_honesty_rules=capability_honesty_rules,
    )


def persona_safe_summary_to_dict(summary: PersonaSafeSummary) -> dict:
    """Serialize a safe summary to a plain dict (deterministic)."""
    return {
        "manifest_name": summary.manifest_name,
        "applies_to_agent": summary.applies_to_agent,
        "voice_summary": summary.voice_summary,
        "posture_summary": summary.posture_summary,
        "honesty_rules": list(summary.honesty_rules),
        "risk_communication_rules": list(summary.risk_communication_rules),
        "challenge_rules": list(summary.challenge_rules),
        "authority_boundaries": list(summary.authority_boundaries),
        "capability_honesty_rules": list(summary.capability_honesty_rules),
    }
