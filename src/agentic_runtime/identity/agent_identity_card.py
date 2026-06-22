"""Agent Identity Card runtime data models (P1.4.7)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Any

from .agent_identity_card_policy import (
    AgentAuthorityBinding,
    AgentFuturePlaceholders,
    AgentIdentityBoundaries,
    AgentIdentityConfig,
    AgentIdentityInvariant,
    AgentIdentityTaxonomy,
    AgentRuntimeIdentity,
    AgentSourceBindings,
    HashAlgorithm,
    ValidationStatus,
)


@dataclass(frozen=True)
class StableAgentIdentityHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class RuntimeAgentIdentityCardHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class AurelAgentIdentityCard:
    schema_version: str
    card_name: str
    card_class: str
    applies_to_agent: str
    agent: AgentIdentityConfig
    authority: AgentAuthorityBinding
    source_bindings: AgentSourceBindings
    runtime: AgentRuntimeIdentity
    identity_taxonomy: AgentIdentityTaxonomy
    future_placeholders: AgentFuturePlaceholders
    boundaries: AgentIdentityBoundaries
    invariants: tuple[AgentIdentityInvariant, ...]
    stable_agent_identity_hash: str | None
    runtime_agent_identity_card_hash: str | None
    notes: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class AgentIdentityCardAttestation:
    schema_version: str
    stable_agent_identity_hash: str
    runtime_agent_identity_card_hash: str
    hash_algorithm: str
    agent_id: str
    agent_name: str
    runtime_instance_id: str
    identity_kernel_hash: str
    persona_manifest_hash: str
    operator_contract_hash: str
    communication_modes_hash: str
    identity_prompt_compiler_policy_hash: str
    self_model_hash: str
    validation_status: ValidationStatus
    critical_failures: tuple[str, ...]
