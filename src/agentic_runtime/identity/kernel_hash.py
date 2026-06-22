"""Deterministic hashing for Aurel Identity Kernel (P1.4.1)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .kernel import AurelIdentityKernel, IdentityKernelHash


def _invariant_to_dict(invariant: object) -> dict[str, Any]:
    from .kernel import IdentityInvariant

    assert isinstance(invariant, IdentityInvariant)
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


def kernel_to_canonical_dict(kernel: AurelIdentityKernel) -> dict[str, Any]:
    """Convert kernel to a canonical primitive dict for hashing."""
    notes: dict[str, Any]
    if kernel.notes is None:
        notes = {}
    else:
        notes = dict(kernel.notes)

    invariants = sorted(
        (_invariant_to_dict(inv) for inv in kernel.invariants),
        key=lambda item: item["id"],
    )

    return {
        "class": kernel.agent_class,
        "development_allowed": {
            "communication_refinement": kernel.development_allowed.communication_refinement,
            "memory_growth": kernel.development_allowed.memory_growth,
            "procedure_growth": kernel.development_allowed.procedure_growth,
            "skill_growth": kernel.development_allowed.skill_growth,
            "specialist_growth": kernel.development_allowed.specialist_growth,
            "world_model_revision": kernel.development_allowed.world_model_revision,
        },
        "development_forbidden": {
            "operator_replacement": kernel.development_forbidden.operator_replacement,
            "secret_goal_creation": kernel.development_forbidden.secret_goal_creation,
            "self_authority_expansion": kernel.development_forbidden.self_authority_expansion,
            "unapproved_identity_rewrite": kernel.development_forbidden.unapproved_identity_rewrite,
        },
        "final_authority": kernel.final_authority,
        "immutables": {
            "hidden_goals_allowed": kernel.immutables.hidden_goals_allowed,
            "identity_replacement_allowed": kernel.immutables.identity_replacement_allowed,
            "operator_final_authority": kernel.immutables.operator_final_authority,
            "policy_bypass_self_grant_allowed": kernel.immutables.policy_bypass_self_grant_allowed,
            "self_escalation_allowed": kernel.immutables.self_escalation_allowed,
            "untrusted_input_can_modify_identity": (
                kernel.immutables.untrusted_input_can_modify_identity
            ),
        },
        "invariants": invariants,
        "local_first": kernel.local_first,
        "name": kernel.name,
        "notes": notes,
        "primary_operator": kernel.primary_operator,
        "schema_version": kernel.schema_version,
    }


def compute_identity_kernel_hash(kernel: AurelIdentityKernel) -> IdentityKernelHash:
    """Compute deterministic SHA-256 hash of canonical kernel representation."""
    canonical = kernel_to_canonical_dict(kernel)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return IdentityKernelHash(algorithm="sha256", value=digest)
