"""Build Agent Identity Card from validated identity sources (P1.4.7)."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .. import __version__ as RUNTIME_VERSION
from ..prompts.compiler_policy import IdentityPromptCompilerPolicy
from ..prompts.identity_context_hash import compute_identity_prompt_compiler_policy_hash
from ..prompts.identity_context_validation import validate_identity_prompt_compiler_policy
from .agent_identity_card import AurelAgentIdentityCard
from .agent_identity_card_hash import (
    compute_runtime_agent_identity_card_hash,
    compute_stable_agent_identity_hash,
)
from .agent_identity_card_policy import (
    AgentIdentityCardConfig,
    AgentIdentityCardError,
    AgentRuntimeIdentity,
    AgentSourceBindings,
    load_agent_identity_card_config,
)
from .agent_identity_card_validation import (
    validate_agent_identity_card,
    validate_agent_identity_card_config,
)
from .communication_modes import AurelCommunicationModeRegistry
from .kernel import AurelIdentityKernel
from .kernel_hash import compute_identity_kernel_hash
from .kernel_validation import validate_identity_kernel
from .mode_hash import compute_communication_mode_registry_hash
from .mode_validation import validate_communication_mode_registry
from .operator_contract import AurelOperatorContract
from .operator_contract_hash import compute_operator_contract_hash
from .operator_contract_validation import validate_operator_contract
from .persona import AurelPersonaManifest
from .persona_hash import compute_persona_manifest_hash
from .persona_validation import validate_persona_manifest
from .runtime_instance import generate_runtime_instance_id
from .self_model import AurelSelfModel
from .self_model_hash import compute_self_model_hash
from .self_model_validation import validate_aurel_self_model, validate_self_model_policy
from .self_model_policy import SelfModelPolicy, load_self_model_policy
from .source_bundle import (
    IdentitySourceBundle,
    build_aurel_self_model_from_bundle,
    load_identity_source_bundle,
)


def _validate_sources_or_raise(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    compiler_policy: IdentityPromptCompilerPolicy,
    self_model: AurelSelfModel,
    self_model_policy: SelfModelPolicy,
    card_config: AgentIdentityCardConfig,
) -> None:
    checks = (
        validate_agent_identity_card_config(card_config),
        validate_identity_kernel(identity_kernel),
        validate_persona_manifest(persona_manifest),
        validate_operator_contract(operator_contract),
        validate_communication_mode_registry(mode_registry),
        validate_identity_prompt_compiler_policy(compiler_policy),
        validate_self_model_policy(self_model_policy),
        validate_aurel_self_model(self_model, self_model_policy),
    )
    for result in checks:
        if not result.valid:
            raise AgentIdentityCardError("; ".join(result.critical_failures or result.errors))


def build_agent_identity_card(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    compiler_policy: IdentityPromptCompilerPolicy,
    self_model: AurelSelfModel,
    self_model_policy: SelfModelPolicy,
    card_config: AgentIdentityCardConfig,
    *,
    runtime_instance_id: str | None = None,
    runtime_version: str | None = None,
) -> AurelAgentIdentityCard:
    """Build validated Agent Identity Card with source-bound hashes."""
    _validate_sources_or_raise(
        identity_kernel,
        persona_manifest,
        operator_contract,
        mode_registry,
        compiler_policy,
        self_model,
        self_model_policy,
        card_config,
    )

    source_bindings = AgentSourceBindings(
        identity_kernel_hash=compute_identity_kernel_hash(identity_kernel).value,
        persona_manifest_hash=compute_persona_manifest_hash(persona_manifest).value,
        operator_contract_hash=compute_operator_contract_hash(operator_contract).value,
        communication_modes_hash=compute_communication_mode_registry_hash(mode_registry).value,
        identity_prompt_compiler_policy_hash=compute_identity_prompt_compiler_policy_hash(
            compiler_policy
        ).value,
        self_model_hash=compute_self_model_hash(self_model).value,
    )

    instance_id = runtime_instance_id or generate_runtime_instance_id().value
    runtime = AgentRuntimeIdentity(
        runtime_instance_id=instance_id,
        runtime_instance_id_strategy=card_config.runtime.runtime_instance_id_strategy,
        runtime_version=runtime_version if runtime_version is not None else RUNTIME_VERSION,
        runtime_started_at=None,
        runtime_machine_scope=card_config.runtime.runtime_machine_scope,
        local_first=card_config.runtime.local_first,
    )

    card_without_hashes = AurelAgentIdentityCard(
        schema_version=card_config.schema_version,
        card_name=card_config.card_name,
        card_class=card_config.card_class,
        applies_to_agent=card_config.applies_to_agent,
        agent=card_config.agent,
        authority=card_config.authority,
        source_bindings=source_bindings,
        runtime=runtime,
        identity_taxonomy=card_config.identity_taxonomy,
        future_placeholders=card_config.future_placeholders,
        boundaries=card_config.boundaries,
        invariants=card_config.invariants,
        stable_agent_identity_hash=None,
        runtime_agent_identity_card_hash=None,
        notes=card_config.notes,
    )

    stable_hash = compute_stable_agent_identity_hash(card_without_hashes)
    runtime_hash = compute_runtime_agent_identity_card_hash(card_without_hashes)

    card = replace(
        card_without_hashes,
        stable_agent_identity_hash=stable_hash,
        runtime_agent_identity_card_hash=runtime_hash,
    )

    validation = validate_agent_identity_card(card)
    if not validation.valid:
        raise AgentIdentityCardError("; ".join(validation.critical_failures or validation.errors))
    return card


def build_agent_identity_card_with_default_policy(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    compiler_policy: IdentityPromptCompilerPolicy,
    self_model: AurelSelfModel,
    card_config: AgentIdentityCardConfig,
    *,
    runtime_instance_id: str | None = None,
    runtime_version: str | None = None,
) -> AurelAgentIdentityCard:
    """Build agent identity card using the canonical default self-model policy."""
    return build_agent_identity_card(
        identity_kernel,
        persona_manifest,
        operator_contract,
        mode_registry,
        compiler_policy,
        self_model,
        load_self_model_policy(),
        card_config,
        runtime_instance_id=runtime_instance_id,
        runtime_version=runtime_version,
    )


def build_agent_identity_card_from_bundle(
    bundle: IdentitySourceBundle,
    *,
    prompt_mode: str = "FOCUS",
    include_prompt_context: bool = True,
    runtime_instance_id: str | None = None,
    runtime_version: str | None = None,
) -> AurelAgentIdentityCard:
    """Build agent identity card from a pre-loaded identity source bundle."""
    self_model = build_aurel_self_model_from_bundle(
        bundle,
        prompt_mode=prompt_mode,
        include_prompt_context=include_prompt_context,
        runtime_version=runtime_version,
    )
    return build_agent_identity_card(
        bundle.identity_kernel,
        bundle.persona_manifest,
        bundle.operator_contract,
        bundle.mode_registry,
        bundle.compiler_policy,
        self_model,
        bundle.self_model_policy,
        bundle.card_config,
        runtime_instance_id=runtime_instance_id,
        runtime_version=runtime_version,
    )


def build_agent_identity_card_from_paths(
    *,
    kernel_path: str | Path | None = None,
    persona_path: str | Path | None = None,
    operator_path: str | Path | None = None,
    modes_path: str | Path | None = None,
    compiler_path: str | Path | None = None,
    self_model_policy_path: str | Path | None = None,
    card_config_path: str | Path | None = None,
    prompt_mode: str = "FOCUS",
    include_prompt_context: bool = True,
    runtime_instance_id: str | None = None,
    runtime_version: str | None = None,
) -> AurelAgentIdentityCard:
    """Load identity sources from paths and build agent identity card."""
    bundle = load_identity_source_bundle(
        kernel_path=kernel_path,
        persona_path=persona_path,
        operator_path=operator_path,
        modes_path=modes_path,
        compiler_path=compiler_path,
        self_model_policy_path=self_model_policy_path,
        card_config_path=card_config_path,
    )
    return build_agent_identity_card_from_bundle(
        bundle,
        prompt_mode=prompt_mode,
        include_prompt_context=include_prompt_context,
        runtime_instance_id=runtime_instance_id,
        runtime_version=runtime_version,
    )
