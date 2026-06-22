"""Canonical P1.4 capability inventory for self-model honesty (P1.4.7-MG)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .self_model import SelfModelCapability

CapabilityStatus = Literal["planned", "implemented"]


@dataclass(frozen=True)
class CapabilityInventoryEntry:
    id: str
    name: str
    status: CapabilityStatus
    roadmap_phase: str


CAPABILITY_INVENTORY: tuple[CapabilityInventoryEntry, ...] = (
    CapabilityInventoryEntry("identity_kernel", "Identity Kernel", "implemented", "P1.4.1"),
    CapabilityInventoryEntry("persona_manifest", "Persona Manifest", "implemented", "P1.4.2"),
    CapabilityInventoryEntry(
        "operator_relationship_contract",
        "Operator Relationship Contract",
        "implemented",
        "P1.4.3",
    ),
    CapabilityInventoryEntry("communication_modes", "Communication Modes", "implemented", "P1.4.4"),
    CapabilityInventoryEntry(
        "identity_prompt_context_compiler",
        "Identity Prompt Context Compiler",
        "implemented",
        "P1.4.5",
    ),
    CapabilityInventoryEntry("self_model", "Self-Model", "implemented", "P1.4.6"),
    CapabilityInventoryEntry("agent_identity_card", "Agent Identity Card", "implemented", "P1.4.7"),
    CapabilityInventoryEntry(
        "autonomy_scale_engine", "Autonomy Scale Engine", "implemented", "P1.4.8"
    ),
    CapabilityInventoryEntry(
        "measured_autonomy_score", "Measured Autonomy Score", "implemented", "P1.4.9"
    ),
    CapabilityInventoryEntry(
        "capability_claim_boundary", "Capability Claim Boundary Engine", "implemented", "P1.4.10"
    ),
    CapabilityInventoryEntry("policy_cards", "Policy Cards & Behavioral Contracts", "planned", "P1.6"),
    CapabilityInventoryEntry("path_governance", "Path Governance Engine", "planned", "P1.7"),
    CapabilityInventoryEntry("evaluation_mirror", "Evaluation Mirror", "planned", "P1.5"),
    CapabilityInventoryEntry("mneme_memory_graph", "Mneme Memory Graph", "planned", "P3"),
    CapabilityInventoryEntry("noesis_world_model", "Noesis World Model", "planned", "P10/P11"),
    CapabilityInventoryEntry("heretic_sandbox", "Heretic Sandbox", "planned", "P1.4.16"),
)

PLANNED_CAPABILITY_IDS = frozenset(
    entry.id for entry in CAPABILITY_INVENTORY if entry.status == "planned"
)
IMPLEMENTED_CAPABILITY_IDS = frozenset(
    entry.id for entry in CAPABILITY_INVENTORY if entry.status == "implemented"
)


def default_capability_inventory() -> tuple[SelfModelCapability, ...]:
    """Return the canonical capability inventory for Aurel self-model."""
    return tuple(
        SelfModelCapability(
            id=entry.id,
            name=entry.name,
            status=entry.status,
            evidence_ref=None,
            limitation=None,
            roadmap_phase=entry.roadmap_phase,
        )
        for entry in CAPABILITY_INVENTORY
    )


__all__ = [
    "CAPABILITY_INVENTORY",
    "CapabilityInventoryEntry",
    "CapabilityStatus",
    "IMPLEMENTED_CAPABILITY_IDS",
    "PLANNED_CAPABILITY_IDS",
    "default_capability_inventory",
]
