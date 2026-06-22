"""Identity Prompt Context data models (P1.4.5)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .compiler_policy import HashAlgorithm, ValidationStatus

ContradictionSeverity = Literal["warning", "critical"]
ContradictionAction = Literal["warn", "fail_compile"]


@dataclass(frozen=True)
class IdentityPromptSourceBundle:
    identity_kernel_hash: str
    persona_manifest_hash: str
    operator_contract_hash: str
    communication_modes_hash: str
    compiler_policy_hash: str
    selected_mode: str


@dataclass(frozen=True)
class IdentityPromptSection:
    name: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class IdentityPromptContext:
    schema_version: str
    compiler_version: str
    agent_name: str
    agent_class: str
    selected_mode: str
    source_bundle: IdentityPromptSourceBundle
    agent_identity_section: tuple[str, ...]
    operator_relationship_section: tuple[str, ...]
    persona_expression_section: tuple[str, ...]
    active_mode_section: tuple[str, ...]
    authority_boundaries_section: tuple[str, ...]
    capability_honesty_section: tuple[str, ...]
    non_goals_section: tuple[str, ...]
    source_integrity_section: tuple[str, ...]


@dataclass(frozen=True)
class IdentityPromptContextHash:
    algorithm: HashAlgorithm
    value: str


@dataclass(frozen=True)
class IdentityPromptContradiction:
    id: str
    source_layer: str
    key: str
    expected: str
    actual: str
    severity: ContradictionSeverity
    action: ContradictionAction
    reason: str


@dataclass(frozen=True)
class IdentityPromptCompileResult:
    valid: bool
    context: IdentityPromptContext | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]
    contradictions: tuple[IdentityPromptContradiction, ...]
    context_hash: str | None


@dataclass(frozen=True)
class IdentityPromptValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_failures: tuple[str, ...]


@dataclass(frozen=True)
class IdentityPromptBoundaryCheck:
    name: str
    present: bool
    required: bool


@dataclass(frozen=True)
class IdentityPromptAttestation:
    schema_version: str
    context_hash: str
    hash_algorithm: str
    compiler_version: str
    identity_kernel_hash: str
    persona_manifest_hash: str
    operator_contract_hash: str
    communication_modes_hash: str
    compiler_policy_hash: str
    selected_mode: str
    validation_status: ValidationStatus
    critical_failures: tuple[str, ...]
