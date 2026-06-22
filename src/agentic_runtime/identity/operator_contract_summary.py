"""Deterministic safe summary for Aurel Operator Relationship Contract (P1.4.3).

This is a preparation object for the future P1.4.5 Identity Prompt Context
Compiler. It is NOT the compiler. The safe summary never exposes raw YAML and
never includes tool-permission or autonomy-granting language.
"""
from __future__ import annotations

from .operator_contract import AurelOperatorContract, OperatorContractSafeSummary


def build_operator_contract_safe_summary(
    contract: AurelOperatorContract,
) -> OperatorContractSafeSummary:
    """Build a deterministic, prompt-safe summary of the operator contract."""
    principal = contract.parties.principal
    delegate = contract.parties.delegate
    auth = contract.authority
    rel = contract.relationship_behavior
    nm = contract.non_manipulation
    exe = contract.execution_authority
    acc = contract.accountability
    boundaries = contract.boundaries

    principal_summary = (
        f"id={principal.id}; role={principal.role}; type={principal.type}; "
        "final authority over Aurel"
    )
    delegate_summary = (
        f"id={delegate.id}; role={delegate.role}; type={delegate.type}; "
        "advisor and executor under Operator authority"
    )

    authority_rules: tuple[str, ...] = tuple(
        rule
        for rule, active in (
            ("Operator remains final authority.", auth.operator_final_authority),
            ("Aurel is not final authority.", not auth.aurel_final_authority),
            ("Aurel cannot self-escalate authority or autonomy.", not auth.aurel_can_self_escalate),
            ("Aurel cannot replace or redefine the Operator.", not auth.aurel_can_replace_operator),
            (
                "Aurel cannot override Operator judgment as sovereign authority.",
                not auth.aurel_can_override_operator_judgment,
            ),
            (
                "Aurel can refuse actions forbidden by policy, law, or constitutional floor.",
                auth.aurel_can_refuse_forbidden_action,
            ),
        )
        if active
    )

    disagreement_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Aurel may disagree with the Operator.", rel.disagreement_allowed),
            ("Disagreement must be explained.", rel.disagreement_must_be_explained),
            ("Uncertainty must be disclosed.", rel.uncertainty_must_be_disclosed),
            ("Tradeoffs must be disclosed.", rel.tradeoffs_must_be_disclosed),
            ("Blind execution is forbidden.", rel.blind_execution_forbidden),
            ("Passive obedience is not required.", not rel.passive_obedience_required),
        )
        if enabled
    )

    challenge_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Aurel can challenge the Operator.", auth.aurel_can_challenge_operator),
            (
                "Aurel must challenge or warn when material risk is detected.",
                auth.aurel_must_challenge_when_risk_detected and rel.risk_challenge_required,
            ),
        )
        if enabled
    )

    non_manipulation_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Manipulation of the Operator is forbidden.", nm.manipulation_forbidden),
            ("Hidden persuasion is forbidden.", nm.hidden_persuasion_forbidden),
            ("Flattery over truth is forbidden.", nm.flattery_over_truth_forbidden),
            ("Emotional pressure is forbidden.", nm.emotional_pressure_forbidden),
            ("Dark-pattern guidance is forbidden.", nm.dark_pattern_guidance_forbidden),
            ("Coercive language is forbidden.", nm.coercive_language_forbidden),
        )
        if enabled
    )

    execution_authority_boundaries: tuple[str, ...] = tuple(
        rule
        for rule, active in (
            ("Tool access does not imply action authority.", not exe.tool_access_implies_authority),
            (
                "Serious actions require authority checks.",
                exe.serious_actions_require_authority_check,
            ),
            (
                "Irreversible actions require Operator approval.",
                exe.irreversible_actions_require_operator_approval,
            ),
            (
                "External side effects require policy allowance.",
                exe.external_side_effects_require_policy_allowance,
            ),
            (
                "Memory canon changes require approval or future policy.",
                exe.memory_canon_changes_require_approval_or_future_policy,
            ),
            (
                "Contract cannot override Identity Kernel.",
                boundaries.cannot_override_identity_kernel,
            ),
            (
                "Contract cannot override Persona Manifest boundaries.",
                boundaries.cannot_override_persona_manifest_boundaries,
            ),
            ("Contract cannot grant tool rights.", boundaries.cannot_grant_tool_rights),
            ("Contract cannot change autonomy.", boundaries.cannot_change_autonomy),
            (
                "Contract cannot disable constitutional floor.",
                boundaries.cannot_disable_constitutional_floor,
            ),
            (
                "Contract cannot canonize untrusted input.",
                boundaries.cannot_canonize_untrusted_input,
            ),
            (
                "Contract cannot expand delegation scope.",
                boundaries.cannot_expand_delegation_scope,
            ),
        )
        if active
    )

    accountability_rules: tuple[str, ...] = tuple(
        rule
        for rule, enabled in (
            ("Serious actions must be traceable.", acc.serious_actions_must_be_traceable),
            (
                "High-risk actions require Operator authorization reference.",
                acc.operator_authorization_ref_required_for_high_risk,
            ),
            ("Aurel must explain action basis.", acc.aurel_must_explain_action_basis),
            ("Aurel must surface reversibility.", acc.aurel_must_surface_reversibility),
            (
                "Aurel must surface known limitations.",
                acc.aurel_must_surface_known_limitations,
            ),
        )
        if enabled
    )

    return OperatorContractSafeSummary(
        contract_name=contract.name,
        principal_summary=principal_summary,
        delegate_summary=delegate_summary,
        authority_rules=authority_rules,
        disagreement_rules=disagreement_rules,
        challenge_rules=challenge_rules,
        non_manipulation_rules=non_manipulation_rules,
        execution_authority_boundaries=execution_authority_boundaries,
        accountability_rules=accountability_rules,
    )


def operator_contract_safe_summary_to_dict(summary: OperatorContractSafeSummary) -> dict:
    """Serialize a safe summary to a plain dict (deterministic)."""
    return {
        "contract_name": summary.contract_name,
        "principal_summary": summary.principal_summary,
        "delegate_summary": summary.delegate_summary,
        "authority_rules": list(summary.authority_rules),
        "disagreement_rules": list(summary.disagreement_rules),
        "challenge_rules": list(summary.challenge_rules),
        "non_manipulation_rules": list(summary.non_manipulation_rules),
        "execution_authority_boundaries": list(summary.execution_authority_boundaries),
        "accountability_rules": list(summary.accountability_rules),
    }
