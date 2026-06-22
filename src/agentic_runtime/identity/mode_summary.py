"""Deterministic safe summary for Aurel Communication Modes (P1.4.4).

This is a preparation object for the future P1.4.5 Identity Prompt Context
Compiler. It is NOT the compiler. The safe summary never exposes raw YAML and
never includes tool-permission, autonomy-changing, execution, or canonization
language.
"""
from __future__ import annotations

from .communication_modes import (
    AurelCommunicationModeRegistry,
    CommunicationModeSafeSummary,
    CommunicationModeSpec,
)
from .mode_registry import get_communication_mode


def _bool_map_rules(mapping: dict[str, bool], prefix: str) -> tuple[str, ...]:
    return tuple(
        f"{prefix}: {key.replace('_', ' ')}."
        for key in sorted(mapping)
        if mapping[key]
    )


def _authority_boundaries_for_mode(
    registry: AurelCommunicationModeRegistry,
    mode: CommunicationModeSpec,
) -> tuple[str, ...]:
    gb = registry.global_boundaries
    rules: list[str] = []
    if gb.modes_can_grant_permissions is False:
        rules.append("Modes cannot grant permissions or tool authority.")
    if gb.modes_can_change_autonomy is False:
        rules.append("Modes cannot change autonomy level.")
    if gb.modes_can_execute_actions is False:
        rules.append("Modes cannot execute actions.")
    if gb.modes_can_canonize_output is False:
        rules.append("Modes cannot canonize output.")
    if gb.modes_can_write_memory_directly is False:
        rules.append("Modes cannot write memory directly.")
    if gb.modes_can_override_identity_kernel is False:
        rules.append("Modes cannot override the Identity Kernel.")
    if gb.modes_can_override_persona_manifest is False:
        rules.append("Modes cannot override the Persona Manifest.")
    if gb.modes_can_override_operator_contract is False:
        rules.append("Modes cannot override the Operator Contract.")
    if gb.modes_can_override_policy is False:
        rules.append("Modes cannot override policy or governance.")
    if gb.modes_can_disable_constitutional_floor is False:
        rules.append("Modes cannot disable the constitutional floor.")

    for label, value in (
        ("grants permissions", mode.boundaries.get("grants_permissions")),
        ("changes autonomy", mode.boundaries.get("changes_autonomy")),
        ("executes actions", mode.boundaries.get("executes_actions")),
        ("canonizes output", mode.boundaries.get("canonizes_output")),
    ):
        if value is False:
            rules.append(f"This mode does not {label}.")

    if mode.name == "HERETIC":
        if mode.output_bias.get("candidate_only") is True:
            rules.append("Heretic output is candidate-only.")
        for label, key in (
            ("real-world side effects", "real_world_side_effects"),
            ("modify identity", "modifies_identity"),
            ("modify policy", "modifies_policy"),
            ("modify memory", "modifies_memory"),
            ("modify tools", "modifies_tools"),
            ("modify autonomy", "modifies_autonomy"),
        ):
            if mode.boundaries.get(key) is False:
                rules.append(f"Heretic has no {label} by default.")

    return tuple(rules)


def build_communication_mode_safe_summary(
    registry: AurelCommunicationModeRegistry,
    mode_name: str,
) -> CommunicationModeSafeSummary:
    """Build a deterministic, prompt-safe summary for one communication mode."""
    lookup = get_communication_mode(registry, mode_name)
    if not lookup.found or lookup.mode is None or lookup.mode_name is None:
        raise ValueError(lookup.error or f"unknown communication mode: {mode_name!r}")

    mode = lookup.mode
    return CommunicationModeSafeSummary(
        mode_name=lookup.mode_name,
        purpose=mode.purpose,
        cognitive_posture=mode.cognitive_posture,
        output_rules=_bool_map_rules(dict(mode.output_bias), "Output"),
        challenge_rules=_bool_map_rules(dict(mode.challenge_emphasis), "Challenge"),
        risk_rules=_bool_map_rules(dict(mode.risk_emphasis), "Risk"),
        authority_boundaries=_authority_boundaries_for_mode(registry, mode),
    )


def communication_mode_safe_summary_to_dict(summary: CommunicationModeSafeSummary) -> dict:
    """Serialize a safe summary to a plain dict (deterministic)."""
    payload: dict = {
        "mode_name": summary.mode_name,
        "purpose": summary.purpose,
        "cognitive_posture": summary.cognitive_posture,
        "output_rules": list(summary.output_rules),
        "challenge_rules": list(summary.challenge_rules),
        "risk_rules": list(summary.risk_rules),
        "authority_boundaries": list(summary.authority_boundaries),
    }
    if summary.mode_name == "HERETIC":
        payload["candidate_only"] = True
        payload["grants_permissions"] = False
        payload["changes_autonomy"] = False
        payload["executes_actions"] = False
        payload["real_world_side_effects"] = False
        payload["modifies_identity"] = False
        payload["modifies_policy"] = False
        payload["modifies_memory"] = False
    return payload
