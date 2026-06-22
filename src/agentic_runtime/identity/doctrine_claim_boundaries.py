"""P1.4.11 doctrine claim boundaries routed through P1.4.10."""
from __future__ import annotations

from .capability_claims import (
    ClaimEvidenceContext,
    CapabilityClaimDecision,
    capability_claim_decision_to_dict,
    evaluate_capability_claim,
    get_claim,
)
from .external_doctrine import ExternalDoctrineInput


_DOCTRINE_CLAIM_IDS: dict[str, tuple[str, ...]] = {
    "agentic_os_asymmetric_teardown": (
        "production_ready_agentic_os",
        "secure_sandboxing",
        "procedural_skill_library",
        "verified_memory",
    ),
    "abos_design_principles_v1": (
        "abos_deployment_layer",
        "global_autonomy",
    ),
    "aether_v0_2": (
        "aether_multimodal_intelligence",
        "aether_roadmap_layer",
    ),
}


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return tuple(result)


def doctrine_capability_claim_decisions(
    doctrine: ExternalDoctrineInput,
) -> tuple[CapabilityClaimDecision, ...]:
    """Evaluate doctrine-related implementation claims with P1.4.10."""
    decisions: list[CapabilityClaimDecision] = []
    ctx = ClaimEvidenceContext()
    for claim_id in _DOCTRINE_CLAIM_IDS.get(doctrine.doctrine_id, ()):
        claim = get_claim(claim_id)
        if claim is None:
            continue
        decisions.append(evaluate_capability_claim(claim, ctx))
    return tuple(decisions)


def blocked_doctrine_claims(doctrine: ExternalDoctrineInput) -> tuple[str, ...]:
    """Claims this doctrine does not authorize."""
    blocked = list(doctrine.claim_boundaries)
    for decision in doctrine_capability_claim_decisions(doctrine):
        if not decision.allowed:
            blocked.append(
                f"P1.4.10 blocks '{decision.original_claim_text}' as "
                f"{decision.allowed_status.value}."
            )
    return _dedupe(blocked)


def safe_doctrine_claim_notes(doctrine: ExternalDoctrineInput) -> tuple[str, ...]:
    """Safe doctrine-derived claim notes after P1.4.10 evaluation."""
    notes: list[str] = []
    for decision in doctrine_capability_claim_decisions(doctrine):
        if decision.safe_claim_text:
            notes.append(decision.safe_claim_text)

    if doctrine.doctrine_id == "agentic_os_asymmetric_teardown":
        notes.append("Aurel roadmap is influenced by Agentic OS runtime doctrine.")
    elif doctrine.doctrine_id == "abos_design_principles_v1":
        notes.append("Aurel roadmap includes ABOS deployment layer planned for P21.8.")
    elif doctrine.doctrine_id == "aether_v0_2":
        notes.append(
            "Aurel roadmap includes AETHER-style research/intelligence layer planned for P19."
        )
    else:
        notes.append("Doctrine is registered as roadmap influence, not capability evidence.")
    return _dedupe(notes)


def doctrine_claim_boundaries(
    doctrine: ExternalDoctrineInput,
) -> tuple[str, ...]:
    """Return claim boundary notes for doctrine assimilation."""
    notes = list(blocked_doctrine_claims(doctrine))
    notes.extend(safe_doctrine_claim_notes(doctrine))
    return _dedupe(notes)


def doctrine_claim_boundary_decisions_to_dict(
    doctrine: ExternalDoctrineInput,
) -> list[dict[str, object]]:
    return [
        capability_claim_decision_to_dict(decision)
        for decision in doctrine_capability_claim_decisions(doctrine)
    ]
