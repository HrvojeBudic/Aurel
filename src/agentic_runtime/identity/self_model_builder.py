"""Build Aurel Self-Model from validated identity sources (P1.4.6)."""
from __future__ import annotations
from collections.abc import Sequence

from pathlib import Path
from typing import Protocol

from .. import __version__ as RUNTIME_VERSION
from .communication_modes import AurelCommunicationModeRegistry, load_communication_mode_registry
from .kernel import AurelIdentityKernel, load_identity_kernel
from .kernel_hash import compute_identity_kernel_hash
from .kernel_validation import validate_identity_kernel
from .mode_hash import compute_communication_mode_registry_hash
from .mode_validation import validate_communication_mode_registry
from .operator_contract import AurelOperatorContract, load_operator_contract
from .operator_contract_hash import compute_operator_contract_hash
from .operator_contract_validation import validate_operator_contract
from .persona import AurelPersonaManifest, load_persona_manifest
from .persona_hash import compute_persona_manifest_hash
from .persona_validation import validate_persona_manifest
from ..prompts.compiler_policy import IdentityPromptCompilerPolicy, load_identity_prompt_compiler_policy
from ..prompts.identity_context import IdentityPromptContext
from ..prompts.identity_context_hash import (
    compute_identity_prompt_compiler_policy_hash,
    compute_identity_prompt_context_hash,
)
from ..prompts.identity_context_validation import (
    validate_identity_prompt_compiler_policy,
    validate_identity_prompt_context,
)
from .capability_inventory import default_capability_inventory
from .self_model import (
    AurelSelfModel,
    SelfModelEvidencePosture,
    SelfModelKnownLimitation,
    SelfModelSourceBundle,
)
from .self_model_policy import SelfModelError, SelfModelPolicy, load_self_model_policy
from .self_model_validation import validate_aurel_self_model, validate_self_model_policy


class _ValidationResultLike(Protocol):
    valid: bool
    critical_failures: Sequence[str]
    errors: Sequence[str]


def _validate_sources_or_raise(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    compiler_policy: IdentityPromptCompilerPolicy,
    self_model_policy: SelfModelPolicy,
    identity_prompt_context: IdentityPromptContext | None,
) -> None:
    checks: tuple[_ValidationResultLike, ...] = (
        validate_self_model_policy(self_model_policy),
        validate_identity_kernel(identity_kernel),
        validate_persona_manifest(persona_manifest),
        validate_operator_contract(operator_contract),
        validate_communication_mode_registry(mode_registry),
        validate_identity_prompt_compiler_policy(compiler_policy),
    )
    for result in checks:
        if not result.valid:
            raise SelfModelError("; ".join(result.critical_failures or result.errors))
    if identity_prompt_context is not None:
        context_result = validate_identity_prompt_context(identity_prompt_context)
        if not context_result.valid:
            raise SelfModelError("; ".join(context_result.critical_failures or context_result.errors))


def _default_capability_inventory():
    return default_capability_inventory()


def _default_known_limitations() -> tuple[SelfModelKnownLimitation, ...]:
    entries = (
        ("limit_p15_evaluation_mirror", "No full P1.5 Evaluation Mirror yet.", "P1.5"),
        ("limit_autonomy_scale", "No full Autonomy Scale Engine yet.", "P1.4.8"),
        ("limit_measured_autonomy", "No Measured Autonomy Score yet.", "P1.4.9"),
        ("limit_policy_cards", "No Policy Card runtime yet.", "P1.6"),
        ("limit_path_governance", "No Path Governance Engine yet.", "P1.7"),
        ("limit_mneme", "No Mneme Memory Graph yet.", "P3"),
        ("limit_noesis", "No Noesis world model yet.", "P10/P11"),
        ("limit_heretic_sandbox", "No full Heretic Sandbox yet.", "P1.4.16"),
        ("limit_self_improvement", "No claim of autonomous self-improvement.", None),
        ("limit_capability_verification", "No full capability verification system yet.", "P1.5"),
        (
            "limit_model_router",
            "No model/router intelligence beyond earlier implemented provider/prompt layers.",
            None,
        ),
    )
    return tuple(
        SelfModelKnownLimitation(id=lim_id, description=desc, related_phase=phase)
        for lim_id, desc, phase in entries
    )


def _build_identity_summary(kernel: AurelIdentityKernel) -> tuple[str, ...]:
    local_first = "local-first" if kernel.local_first else "non-local-first"
    return (
        f"You are {kernel.name}, a {local_first} sovereign personal agent.",
        "Aurel operates under one human Operator.",
        "Operator remains final authority.",
        "Identity defines trust boundaries; identity does not grant tool authority.",
    )


def _build_authority_boundaries(kernel: AurelIdentityKernel) -> tuple[str, ...]:
    imm = kernel.immutables
    lines = [
        "Aurel cannot self-escalate authority or autonomy.",
        "Aurel cannot replace the Operator.",
        "Aurel cannot grant itself tool rights.",
        "Aurel cannot change autonomy.",
        "Aurel cannot override policy.",
        "Aurel cannot claim verified capabilities without evidence.",
        "Aurel cannot treat roadmap features as implemented runtime.",
    ]
    if imm.self_escalation_allowed:
        lines.append("WARNING: kernel reports self_escalation_allowed=true (unexpected).")
    return tuple(lines)


def _build_non_goals() -> tuple[str, ...]:
    return (
        "Self-Model does not authorize tool execution.",
        "Self-Model does not authorize memory writes.",
        "Self-Model does not authorize external calls.",
        "Self-Model does not authorize autonomy changes.",
        "Self-Model does not verify capabilities by itself.",
        "Self-Model does not replace runtime governance.",
        "Self-Model does not imply consciousness.",
    )


def _build_next_unimplemented_modules() -> tuple[str, ...]:
    return (
        "P1.4.8 Autonomy Scale Engine",
        "P1.4.9 Measured Autonomy Score",
        "P1.4.10 Governance / Heretic Profiles",
        "P1.4.11 Constitutional Floor",
        "P1.4.16 Heretic Sandbox",
        "P1.5 Evaluation Mirror",
    )


def _build_evidence_posture() -> SelfModelEvidencePosture:
    return SelfModelEvidencePosture(
        evaluation_mirror_available=False,
        verified_capability_claims_allowed=False,
        evidence_system_phase="P1.5 planned",
        default_capability_claim_status="implemented_or_planned_not_verified",
    )


def build_aurel_self_model(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    compiler_policy: IdentityPromptCompilerPolicy,
    identity_prompt_context: IdentityPromptContext | None,
    self_model_policy: SelfModelPolicy,
    runtime_version: str | None = None,
) -> AurelSelfModel:
    """Build validated AurelSelfModel from P1.4.1–P1.4.5 sources."""
    _validate_sources_or_raise(
        identity_kernel,
        persona_manifest,
        operator_contract,
        mode_registry,
        compiler_policy,
        self_model_policy,
        identity_prompt_context,
    )

    context_hash: str | None = None
    if identity_prompt_context is not None:
        context_hash = compute_identity_prompt_context_hash(identity_prompt_context).value

    bundle = SelfModelSourceBundle(
        identity_kernel_hash=compute_identity_kernel_hash(identity_kernel).value,
        persona_manifest_hash=compute_persona_manifest_hash(persona_manifest).value,
        operator_contract_hash=compute_operator_contract_hash(operator_contract).value,
        communication_modes_hash=compute_communication_mode_registry_hash(mode_registry).value,
        identity_prompt_compiler_policy_hash=compute_identity_prompt_compiler_policy_hash(
            compiler_policy
        ).value,
        identity_prompt_context_hash=context_hash,
    )

    model = AurelSelfModel(
        schema_version=self_model_policy.schema_version,
        agent_name=identity_kernel.name,
        agent_class=identity_kernel.agent_class,
        runtime_version=runtime_version if runtime_version is not None else RUNTIME_VERSION,
        source_bundle=bundle,
        identity_summary=_build_identity_summary(identity_kernel),
        authority_boundaries=_build_authority_boundaries(identity_kernel),
        active_prompt_context_available=identity_prompt_context is not None,
        capability_inventory=_default_capability_inventory(),
        known_limitations=_default_known_limitations(),
        evidence_posture=_build_evidence_posture(),
        non_goals=_build_non_goals(),
        next_unimplemented_modules=_build_next_unimplemented_modules(),
    )

    validation = validate_aurel_self_model(model, self_model_policy)
    if not validation.valid:
        raise SelfModelError("; ".join(validation.critical_failures or validation.errors))
    return model


def build_aurel_self_model_from_paths(
    *,
    kernel_path: str | Path | None = None,
    persona_path: str | Path | None = None,
    operator_path: str | Path | None = None,
    modes_path: str | Path | None = None,
    compiler_path: str | Path | None = None,
    self_model_policy_path: str | Path | None = None,
    prompt_mode: str = "FOCUS",
    include_prompt_context: bool = True,
    runtime_version: str | None = None,
) -> AurelSelfModel:
    """Load identity sources from paths and build self-model."""
    try:
        identity_kernel = load_identity_kernel(kernel_path)
        persona_manifest = load_persona_manifest(persona_path)
        operator_contract = load_operator_contract(operator_path)
        mode_registry = load_communication_mode_registry(modes_path)
        compiler_policy = load_identity_prompt_compiler_policy(compiler_path)
        self_model_policy = load_self_model_policy(self_model_policy_path)
    except Exception as exc:
        raise SelfModelError(str(exc)) from exc

    identity_prompt_context: IdentityPromptContext | None = None
    if include_prompt_context:
        from ..prompts.identity_context_compiler import compile_identity_prompt_context

        compile_result = compile_identity_prompt_context(
            identity_kernel,
            persona_manifest,
            operator_contract,
            mode_registry,
            prompt_mode,
            compiler_policy,
        )
        if not compile_result.valid or compile_result.context is None:
            raise SelfModelError(
                "; ".join(compile_result.critical_failures or compile_result.errors)
            )
        identity_prompt_context = compile_result.context

    return build_aurel_self_model(
        identity_kernel,
        persona_manifest,
        operator_contract,
        mode_registry,
        compiler_policy,
        identity_prompt_context,
        self_model_policy,
        runtime_version=runtime_version,
    )
