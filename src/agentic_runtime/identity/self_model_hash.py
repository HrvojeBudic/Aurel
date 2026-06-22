"""Deterministic hashing for Aurel Self-Model (P1.4.6)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .self_model import (
    AurelSelfModel,
    SelfModelCapability,
    SelfModelEvidencePosture,
    SelfModelHash,
    SelfModelKnownLimitation,
)
from .self_model_policy import SelfModelInvariant, SelfModelPolicy


def _invariant_to_dict(invariant: SelfModelInvariant) -> dict[str, Any]:
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


def policy_to_canonical_dict(policy: SelfModelPolicy) -> dict[str, Any]:
    """Convert self-model policy to a canonical primitive dict for hashing."""
    notes: dict[str, Any] = {} if policy.notes is None else dict(policy.notes)
    invariants = sorted(
        (_invariant_to_dict(inv) for inv in policy.invariants),
        key=lambda item: item["id"],
    )
    req = policy.source_requirements
    honesty = policy.honesty
    boundaries = policy.boundaries
    sections = policy.required_sections
    return {
        "applies_to_agent": policy.applies_to_agent,
        "boundaries": {
            "self_model_can_change_autonomy": boundaries.self_model_can_change_autonomy,
            "self_model_can_change_identity": boundaries.self_model_can_change_identity,
            "self_model_can_grant_authority": boundaries.self_model_can_grant_authority,
            "self_model_can_modify_policy": boundaries.self_model_can_modify_policy,
            "self_model_can_verify_capability_by_itself": (
                boundaries.self_model_can_verify_capability_by_itself
            ),
            "self_model_can_write_memory": boundaries.self_model_can_write_memory,
        },
        "capability_statuses": {
            "allowed_statuses": list(policy.capability_statuses.allowed_statuses),
        },
        "honesty": {
            "distinguish_implemented_from_verified": honesty.distinguish_implemented_from_verified,
            "distinguish_planned_from_implemented": honesty.distinguish_planned_from_implemented,
            "distinguish_unavailable_from_unverified": honesty.distinguish_unavailable_from_unverified,
            "expose_known_limitations": honesty.expose_known_limitations,
            "mark_unknown_as_unknown": honesty.mark_unknown_as_unknown,
            "never_claim_roadmap_as_runtime": honesty.never_claim_roadmap_as_runtime,
            "never_claim_verification_without_evidence": (
                honesty.never_claim_verification_without_evidence
            ),
        },
        "invariants": invariants,
        "name": policy.name,
        "notes": notes,
        "policy_class": policy.policy_class,
        "policy_version": policy.policy_version,
        "required_sections": {
            "include_authority_boundaries": sections.include_authority_boundaries,
            "include_capability_inventory": sections.include_capability_inventory,
            "include_evidence_posture": sections.include_evidence_posture,
            "include_identity_summary": sections.include_identity_summary,
            "include_known_limitations": sections.include_known_limitations,
            "include_next_unimplemented_modules": sections.include_next_unimplemented_modules,
            "include_non_goals": sections.include_non_goals,
            "include_source_hashes": sections.include_source_hashes,
        },
        "schema_version": policy.schema_version,
        "source_requirements": {
            "communication_mode_registry_required": req.communication_mode_registry_required,
            "identity_kernel_required": req.identity_kernel_required,
            "identity_prompt_compiler_policy_required": req.identity_prompt_compiler_policy_required,
            "operator_contract_required": req.operator_contract_required,
            "persona_manifest_required": req.persona_manifest_required,
        },
    }


def compute_self_model_policy_hash(policy: SelfModelPolicy) -> SelfModelHash:
    """Compute deterministic SHA-256 hash of canonical self-model policy."""
    canonical = policy_to_canonical_dict(policy)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return SelfModelHash(algorithm="sha256", value=digest)


def _capability_to_dict(cap: SelfModelCapability) -> dict[str, Any]:
    return {
        "evidence_ref": cap.evidence_ref,
        "id": cap.id,
        "limitation": cap.limitation,
        "name": cap.name,
        "roadmap_phase": cap.roadmap_phase,
        "status": cap.status,
    }


def _limitation_to_dict(item: SelfModelKnownLimitation) -> dict[str, Any]:
    return {
        "description": item.description,
        "id": item.id,
        "related_phase": item.related_phase,
    }


def _evidence_posture_to_dict(posture: SelfModelEvidencePosture) -> dict[str, Any]:
    return {
        "default_capability_claim_status": posture.default_capability_claim_status,
        "evaluation_mirror_available": posture.evaluation_mirror_available,
        "evidence_system_phase": posture.evidence_system_phase,
        "verified_capability_claims_allowed": posture.verified_capability_claims_allowed,
    }


def self_model_to_canonical_dict(model: AurelSelfModel) -> dict[str, Any]:
    """Convert self-model to a canonical primitive dict for hashing."""
    bundle = model.source_bundle
    capabilities = sorted(
        (_capability_to_dict(cap) for cap in model.capability_inventory),
        key=lambda item: item["id"],
    )
    limitations = sorted(
        (_limitation_to_dict(item) for item in model.known_limitations),
        key=lambda item: item["id"],
    )
    return {
        "active_prompt_context_available": model.active_prompt_context_available,
        "agent_class": model.agent_class,
        "agent_name": model.agent_name,
        "authority_boundaries": list(model.authority_boundaries),
        "capability_inventory": capabilities,
        "evidence_posture": _evidence_posture_to_dict(model.evidence_posture),
        "identity_summary": list(model.identity_summary),
        "known_limitations": limitations,
        "next_unimplemented_modules": list(model.next_unimplemented_modules),
        "non_goals": list(model.non_goals),
        "runtime_version": model.runtime_version,
        "schema_version": model.schema_version,
        "source_bundle": {
            "communication_modes_hash": bundle.communication_modes_hash,
            "identity_kernel_hash": bundle.identity_kernel_hash,
            "identity_prompt_compiler_policy_hash": bundle.identity_prompt_compiler_policy_hash,
            "identity_prompt_context_hash": bundle.identity_prompt_context_hash,
            "operator_contract_hash": bundle.operator_contract_hash,
            "persona_manifest_hash": bundle.persona_manifest_hash,
        },
    }


def compute_self_model_hash(model: AurelSelfModel) -> SelfModelHash:
    """Compute deterministic SHA-256 hash of canonical self-model representation."""
    canonical = self_model_to_canonical_dict(model)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return SelfModelHash(algorithm="sha256", value=digest)
