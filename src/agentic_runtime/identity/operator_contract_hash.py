"""Deterministic hashing for Aurel Operator Relationship Contract (P1.4.3)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .operator_contract import AurelOperatorContract, OperatorContractHash, OperatorContractInvariant


def _invariant_to_dict(invariant: OperatorContractInvariant) -> dict[str, Any]:
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


def contract_to_canonical_dict(contract: AurelOperatorContract) -> dict[str, Any]:
    """Convert contract to a canonical primitive dict for hashing."""
    notes: dict[str, Any] = {} if contract.notes is None else dict(contract.notes)
    invariants = sorted(
        (_invariant_to_dict(inv) for inv in contract.invariants),
        key=lambda item: item["id"],
    )
    parties = contract.parties
    authority = contract.authority
    relationship = contract.relationship_behavior
    non_manipulation = contract.non_manipulation
    execution = contract.execution_authority
    accountability = contract.accountability
    placeholders = contract.future_placeholders
    boundaries = contract.boundaries

    return {
        "accountability": {
            "aurel_must_explain_action_basis": accountability.aurel_must_explain_action_basis,
            "aurel_must_surface_known_limitations": (
                accountability.aurel_must_surface_known_limitations
            ),
            "aurel_must_surface_reversibility": accountability.aurel_must_surface_reversibility,
            "operator_authorization_ref_required_for_high_risk": (
                accountability.operator_authorization_ref_required_for_high_risk
            ),
            "serious_actions_must_be_traceable": accountability.serious_actions_must_be_traceable,
        },
        "applies_to_agent": contract.applies_to_agent,
        "authority": {
            "aurel_can_challenge_operator": authority.aurel_can_challenge_operator,
            "aurel_can_override_operator_judgment": authority.aurel_can_override_operator_judgment,
            "aurel_can_refuse_forbidden_action": authority.aurel_can_refuse_forbidden_action,
            "aurel_can_replace_operator": authority.aurel_can_replace_operator,
            "aurel_can_self_escalate": authority.aurel_can_self_escalate,
            "aurel_final_authority": authority.aurel_final_authority,
            "aurel_must_challenge_when_risk_detected": (
                authority.aurel_must_challenge_when_risk_detected
            ),
            "operator_final_authority": authority.operator_final_authority,
        },
        "boundaries": {
            "cannot_canonize_untrusted_input": boundaries.cannot_canonize_untrusted_input,
            "cannot_change_autonomy": boundaries.cannot_change_autonomy,
            "cannot_disable_constitutional_floor": (
                boundaries.cannot_disable_constitutional_floor
            ),
            "cannot_expand_delegation_scope": boundaries.cannot_expand_delegation_scope,
            "cannot_grant_tool_rights": boundaries.cannot_grant_tool_rights,
            "cannot_override_identity_kernel": boundaries.cannot_override_identity_kernel,
            "cannot_override_persona_manifest_boundaries": (
                boundaries.cannot_override_persona_manifest_boundaries
            ),
        },
        "contract_class": contract.contract_class,
        "execution_authority": {
            "external_side_effects_require_policy_allowance": (
                execution.external_side_effects_require_policy_allowance
            ),
            "irreversible_actions_require_operator_approval": (
                execution.irreversible_actions_require_operator_approval
            ),
            "memory_canon_changes_require_approval_or_future_policy": (
                execution.memory_canon_changes_require_approval_or_future_policy
            ),
            "serious_actions_require_authority_check": (
                execution.serious_actions_require_authority_check
            ),
            "tool_access_implies_authority": execution.tool_access_implies_authority,
        },
        "future_placeholders": {
            "approval_workbench_ref": placeholders.approval_workbench_ref,
            "autonomy_session_ref": placeholders.autonomy_session_ref,
            "delegation_grant_ref": placeholders.delegation_grant_ref,
            "non_repudiation_attestation_ref": placeholders.non_repudiation_attestation_ref,
        },
        "invariants": invariants,
        "name": contract.name,
        "non_manipulation": {
            "coercive_language_forbidden": non_manipulation.coercive_language_forbidden,
            "dark_pattern_guidance_forbidden": non_manipulation.dark_pattern_guidance_forbidden,
            "emotional_pressure_forbidden": non_manipulation.emotional_pressure_forbidden,
            "flattery_over_truth_forbidden": non_manipulation.flattery_over_truth_forbidden,
            "hidden_persuasion_forbidden": non_manipulation.hidden_persuasion_forbidden,
            "manipulation_forbidden": non_manipulation.manipulation_forbidden,
        },
        "notes": notes,
        "parties": {
            "delegate": {
                "id": parties.delegate.id,
                "role": parties.delegate.role,
                "type": parties.delegate.type,
            },
            "principal": {
                "id": parties.principal.id,
                "role": parties.principal.role,
                "type": parties.principal.type,
            },
        },
        "relationship_behavior": {
            "blind_execution_forbidden": relationship.blind_execution_forbidden,
            "disagreement_allowed": relationship.disagreement_allowed,
            "disagreement_must_be_explained": relationship.disagreement_must_be_explained,
            "passive_obedience_required": relationship.passive_obedience_required,
            "risk_challenge_required": relationship.risk_challenge_required,
            "tradeoffs_must_be_disclosed": relationship.tradeoffs_must_be_disclosed,
            "uncertainty_must_be_disclosed": relationship.uncertainty_must_be_disclosed,
        },
        "schema_version": contract.schema_version,
    }


def compute_operator_contract_hash(contract: AurelOperatorContract) -> OperatorContractHash:
    """Compute deterministic SHA-256 hash of canonical contract representation."""
    canonical = contract_to_canonical_dict(contract)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return OperatorContractHash(algorithm="sha256", value=digest)
