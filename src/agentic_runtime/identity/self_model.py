"""Aurel Self-Model runtime data models (P1.4.6)."""
from __future__ import annotations

from dataclasses import dataclass

from .capability_status import CapabilityStatus
from .self_model_policy import HashAlgorithm, ValidationStatus


@dataclass(frozen=True)
class SelfModelSourceBundle:
    identity_kernel_hash: str
    persona_manifest_hash: str
    operator_contract_hash: str
    communication_modes_hash: str
    identity_prompt_compiler_policy_hash: str
    identity_prompt_context_hash: str | None


@dataclass(frozen=True)
class SelfModelCapability:
    id: str
    name: str
    status: CapabilityStatus
    evidence_ref: str | None
    limitation: str | None
    roadmap_phase: str | None


@dataclass(frozen=True)
class SelfModelKnownLimitation:
    id: str
    description: str
    related_phase: str | None


@dataclass(frozen=True)
class SelfModelEvidencePosture:
    evaluation_mirror_available: bool
    verified_capability_claims_allowed: bool
    evidence_system_phase: str
    default_capability_claim_status: str


@dataclass(frozen=True)
class AurelSelfModel:
    schema_version: str
    agent_name: str
    agent_class: str
    runtime_version: str | None
    source_bundle: SelfModelSourceBundle
    identity_summary: tuple[str, ...]
    authority_boundaries: tuple[str, ...]
    active_prompt_context_available: bool
    capability_inventory: tuple[SelfModelCapability, ...]
    known_limitations: tuple[SelfModelKnownLimitation, ...]
    evidence_posture: SelfModelEvidencePosture
    non_goals: tuple[str, ...]
    next_unimplemented_modules: tuple[str, ...]


@dataclass(frozen=True)
class SelfModelValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class SelfModelHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class SelfModelAttestation:
    schema_version: str
    self_model_hash: str
    hash_algorithm: str
    identity_kernel_hash: str
    persona_manifest_hash: str
    operator_contract_hash: str
    communication_modes_hash: str
    identity_prompt_compiler_policy_hash: str
    identity_prompt_context_hash: str | None
    validation_status: ValidationStatus
    critical_failures: tuple[str, ...]
