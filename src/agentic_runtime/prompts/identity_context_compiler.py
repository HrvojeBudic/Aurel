"""Identity Prompt Context Compiler (P1.4.5).

Compiles validated identity sources into a safe, hash-bound prompt context.
No LLM calls, no tool execution, no memory writes, no autonomy changes.
"""
from __future__ import annotations

from pathlib import Path

from ..identity.communication_modes import AurelCommunicationModeRegistry
from ..identity.kernel import AurelIdentityKernel, load_identity_kernel
from ..identity.kernel_hash import compute_identity_kernel_hash
from ..identity.kernel_validation import validate_identity_kernel
from ..identity.mode_hash import compute_communication_mode_registry_hash
from ..identity.mode_registry import get_communication_mode
from ..identity.mode_summary import build_communication_mode_safe_summary
from ..identity.mode_validation import validate_communication_mode_registry
from ..identity.operator_contract import AurelOperatorContract, load_operator_contract
from ..identity.operator_contract_hash import compute_operator_contract_hash
from ..identity.operator_contract_summary import build_operator_contract_safe_summary
from ..identity.operator_contract_validation import validate_operator_contract
from ..identity.persona import AurelPersonaManifest, load_persona_manifest
from ..identity.persona_hash import compute_persona_manifest_hash
from ..identity.persona_summary import build_persona_safe_summary
from ..identity.persona_validation import validate_persona_manifest
from .compiler_policy import (
    IdentityPromptCompilerPolicy,
    load_identity_prompt_compiler_policy,
)
from .identity_context import (
    IdentityPromptCompileResult,
    IdentityPromptContext,
    IdentityPromptContradiction,
    IdentityPromptSourceBundle,
)
from .identity_context_hash import (
    compute_identity_prompt_compiler_policy_hash,
    compute_identity_prompt_context_hash,
)
from .identity_context_validation import (
    validate_identity_prompt_compiler_policy,
    validate_identity_prompt_context,
)


def _contradiction(
    ctr_id: str,
    source_layer: str,
    key: str,
    expected: str,
    actual: str,
    reason: str,
    *,
    severity: str = "critical",
) -> IdentityPromptContradiction:
    return IdentityPromptContradiction(
        id=ctr_id,
        source_layer=source_layer,
        key=key,
        expected=expected,
        actual=actual,
        severity=severity,
        action="fail_compile",
        reason=reason,
    )


def _detect_source_contradictions(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    compiler_policy: IdentityPromptCompilerPolicy,
    selected_mode: str,
    *,
    kernel_valid: bool,
    persona_valid: bool,
    operator_valid: bool,
    modes_valid: bool,
    policy_valid: bool,
    mode_lookup_ok: bool,
) -> list[IdentityPromptContradiction]:
    contradictions: list[IdentityPromptContradiction] = []

    if not kernel_valid:
        contradictions.append(
            _contradiction(
                "CTR-001",
                "identity_kernel",
                "validation",
                "valid",
                "invalid",
                "Identity Kernel failed validation.",
            )
        )
    if not persona_valid:
        contradictions.append(
            _contradiction(
                "CTR-002",
                "persona_manifest",
                "validation",
                "valid",
                "invalid",
                "Persona Manifest failed validation.",
            )
        )
    if not operator_valid:
        contradictions.append(
            _contradiction(
                "CTR-003",
                "operator_contract",
                "validation",
                "valid",
                "invalid",
                "Operator Contract failed validation.",
            )
        )
    if not modes_valid:
        contradictions.append(
            _contradiction(
                "CTR-004",
                "communication_modes",
                "validation",
                "valid",
                "invalid",
                "Communication Mode Registry failed validation.",
            )
        )
    if not policy_valid:
        contradictions.append(
            _contradiction(
                "CTR-005",
                "compiler_policy",
                "validation",
                "valid",
                "invalid",
                "Compiler policy failed validation.",
            )
        )
    if not mode_lookup_ok:
        contradictions.append(
            _contradiction(
                "CTR-006",
                "communication_modes",
                "selected_mode",
                "known mode",
                selected_mode,
                f"Selected mode {selected_mode!r} does not exist.",
            )
        )

    if identity_kernel.immutables.self_escalation_allowed:
        contradictions.append(
            _contradiction(
                "CTR-007",
                "identity_kernel",
                "self_escalation_allowed",
                "false",
                "true",
                "Identity Kernel allows self-escalation.",
            )
        )

    if operator_contract.authority.aurel_final_authority:
        contradictions.append(
            _contradiction(
                "CTR-008",
                "operator_contract",
                "aurel_final_authority",
                "false",
                "true",
                "Operator Contract grants Aurel final authority.",
            )
        )

    if persona_manifest.can_grant_permissions:
        contradictions.append(
            _contradiction(
                "CTR-009",
                "persona_manifest",
                "can_grant_permissions",
                "false",
                "true",
                "Persona Manifest can grant permissions.",
            )
        )
    if persona_manifest.can_override_identity_kernel:
        contradictions.append(
            _contradiction(
                "CTR-010",
                "persona_manifest",
                "can_override_identity_kernel",
                "false",
                "true",
                "Persona Manifest can override Identity Kernel.",
            )
        )
    if persona_manifest.can_override_policy:
        contradictions.append(
            _contradiction(
                "CTR-011",
                "persona_manifest",
                "can_override_policy",
                "false",
                "true",
                "Persona Manifest can override policy.",
            )
        )
    if persona_manifest.can_change_autonomy:
        contradictions.append(
            _contradiction(
                "CTR-012",
                "persona_manifest",
                "can_change_autonomy",
                "false",
                "true",
                "Persona Manifest can change autonomy.",
            )
        )

    gb = mode_registry.global_boundaries
    if gb.modes_can_grant_permissions:
        contradictions.append(
            _contradiction(
                "CTR-013",
                "communication_modes",
                "modes_can_grant_permissions",
                "false",
                "true",
                "Communication Mode registry can grant permissions.",
            )
        )
    if gb.modes_can_change_autonomy:
        contradictions.append(
            _contradiction(
                "CTR-014",
                "communication_modes",
                "modes_can_change_autonomy",
                "false",
                "true",
                "Communication Mode registry can change autonomy.",
            )
        )
    if gb.modes_can_execute_actions:
        contradictions.append(
            _contradiction(
                "CTR-015",
                "communication_modes",
                "modes_can_execute_actions",
                "false",
                "true",
                "Communication Mode registry can execute actions.",
            )
        )
    if gb.modes_can_canonize_output:
        contradictions.append(
            _contradiction(
                "CTR-016",
                "communication_modes",
                "modes_can_canonize_output",
                "false",
                "true",
                "Communication Mode registry can canonize output.",
            )
        )

    lookup = get_communication_mode(mode_registry, selected_mode)
    if lookup.found and lookup.mode is not None:
        mode = lookup.mode
        if mode.boundaries.get("executes_actions") is True:
            contradictions.append(
                _contradiction(
                    "CTR-015b",
                    "communication_modes",
                    "executes_actions",
                    "false",
                    "true",
                    f"Mode {mode.name} executes actions.",
                )
            )
        if mode.name == "HERETIC":
            heretic_checks = (
                ("real_world_side_effects", "CTR-017", "real-world side effects"),
                ("modifies_identity", "CTR-018", "identity modification"),
                ("modifies_policy", "CTR-019", "policy modification"),
                ("modifies_memory", "CTR-020", "memory modification"),
                ("modifies_tools", "CTR-021", "tool modification"),
                ("modifies_autonomy", "CTR-022", "autonomy modification"),
            )
            for key, ctr_id, label in heretic_checks:
                if mode.boundaries.get(key) is True:
                    contradictions.append(
                        _contradiction(
                            ctr_id,
                            "communication_modes",
                            f"HERETIC.{key}",
                            "false",
                            "true",
                            f"HERETIC allows {label}.",
                        )
                    )
            if mode.output_bias.get("candidate_only") is not True:
                contradictions.append(
                    _contradiction(
                        "CTR-017b",
                        "communication_modes",
                        "HERETIC.candidate_only",
                        "true",
                        str(mode.output_bias.get("candidate_only")),
                        "HERETIC is not candidate-only.",
                    )
                )

    if not compiler_policy.safety.raw_yaml_in_prompt_forbidden:
        contradictions.append(
            _contradiction(
                "CTR-023",
                "compiler_policy",
                "raw_yaml_in_prompt_forbidden",
                "true",
                "false",
                "Compiler policy allows raw YAML in prompt.",
            )
        )
    if not compiler_policy.safety.include_source_hashes:
        contradictions.append(
            _contradiction(
                "CTR-024",
                "compiler_policy",
                "include_source_hashes",
                "true",
                "false",
                "Compiler policy does not require source hashes.",
            )
        )

    return contradictions


def _build_agent_identity_section(kernel: AurelIdentityKernel) -> tuple[str, ...]:
    local_first = "local-first" if kernel.local_first else "non-local-first"
    return (
        f"You are {kernel.name}, a {local_first} sovereign personal agent under one human Operator.",
        f"Agent class: {kernel.agent_class}.",
        "Your identity defines trust boundaries, not tool permissions.",
        "Identity does not grant runtime authority, tool rights, or action authority.",
        "Operator final authority is preserved by the Identity Kernel.",
    )


def _build_operator_relationship_section(
    operator_summary_rules: tuple[str, ...],
) -> tuple[str, ...]:
    lines = list(operator_summary_rules)
    lines.extend(
        (
            "Operator remains final authority over Aurel.",
            "Aurel may challenge material risk and refuse forbidden actions.",
            "Aurel must not manipulate the Operator.",
            "Aurel must surface known limitations and reversibility.",
        )
    )
    return tuple(lines)


def _build_persona_expression_section(
    persona_summary_rules: tuple[str, ...],
) -> tuple[str, ...]:
    lines = list(persona_summary_rules)
    lines.extend(
        (
            "Communicate clearly, structurally, and precisely.",
            "Explain uncertainty; avoid false certainty.",
            "Distinguish fact, inference, planned, implemented, verified, and unavailable.",
            "Surface material risk and challenge weak assumptions.",
        )
    )
    return tuple(lines)


def _build_active_mode_section(
    mode_name: str,
    mode_summary_rules: tuple[str, ...],
    mode_purpose: str,
    cognitive_posture: str,
) -> tuple[str, ...]:
    lines = [
        f"Active communication mode: {mode_name}.",
        f"Purpose: {mode_purpose}.",
        f"Cognitive posture: {cognitive_posture}.",
        "Mode shapes reasoning and output; mode does not grant authority.",
    ]
    lines.extend(mode_summary_rules)
    if mode_name == "DEPLOY":
        lines.append("Orientation: implementation planning, test orientation, and acceptance criteria.")
    if mode_name == "SHADOW":
        lines.append("Orientation: risk-first adversarial review and uncomfortable truth surfacing.")
    if mode_name == "HERETIC":
        lines.extend(
            (
                "HERETIC output is candidate-only.",
                "HERETIC has no real-world side effects by default.",
                "HERETIC cannot modify identity, policy, memory, tools, or autonomy.",
                "HERETIC cannot canonize output directly.",
            )
        )
    return tuple(lines)


def _build_authority_boundaries_section(
    kernel: AurelIdentityKernel,
    persona_boundaries: tuple[str, ...],
    mode_boundaries: tuple[str, ...],
) -> tuple[str, ...]:
    lines = list(persona_boundaries)
    lines.extend(mode_boundaries)
    if not kernel.immutables.self_escalation_allowed:
        lines.append("No self-escalation: Aurel cannot raise its own authority or autonomy.")
    lines.extend(
        (
            "Prompt context does not grant tool authority.",
            "Prompt context does not grant action authority.",
            "Prompt context does not authorize autonomy changes.",
            "Prompt context does not authorize policy bypass.",
            "Prompt context does not authorize memory writes.",
            "Prompt context does not authorize canonization.",
            "Prompt context does not authorize external side effects.",
        )
    )
    return tuple(lines)


def _build_capability_honesty_section(
    persona_capability_rules: tuple[str, ...],
) -> tuple[str, ...]:
    lines = list(persona_capability_rules)
    lines.extend(
        (
            "Capability honesty: do not claim unverified capabilities as active.",
            "Distinguish planned vs implemented vs verified capabilities.",
            "Future roadmap modules are planned/unverified unless evidence exists.",
            "Unsupported claims must be marked uncertain or unavailable.",
        )
    )
    return tuple(lines)


def _build_non_goals_section() -> tuple[str, ...]:
    return (
        "This prompt context does not authorize tool execution.",
        "This prompt context does not authorize memory writes.",
        "This prompt context does not authorize external calls.",
        "This prompt context does not authorize autonomy changes.",
        "This prompt context does not authorize policy bypass.",
        "This prompt context does not canonize output.",
        "This prompt context does not replace runtime governance.",
    )


def _build_source_integrity_section(
    bundle: IdentityPromptSourceBundle,
    compiler_version: str,
) -> tuple[str, ...]:
    return (
        f"identity_kernel_hash: {bundle.identity_kernel_hash}",
        f"persona_manifest_hash: {bundle.persona_manifest_hash}",
        f"operator_contract_hash: {bundle.operator_contract_hash}",
        f"communication_modes_hash: {bundle.communication_modes_hash}",
        f"compiler_policy_hash: {bundle.compiler_policy_hash}",
        f"selected_mode: {bundle.selected_mode}",
        f"compiler_version: {compiler_version}",
    )


def compile_identity_prompt_context(
    identity_kernel: AurelIdentityKernel,
    persona_manifest: AurelPersonaManifest,
    operator_contract: AurelOperatorContract,
    mode_registry: AurelCommunicationModeRegistry,
    selected_mode: str,
    compiler_policy: IdentityPromptCompilerPolicy,
) -> IdentityPromptCompileResult:
    """Compile validated identity sources into IdentityPromptContext."""
    errors: list[str] = []
    warnings: list[str] = []

    policy_validation = validate_identity_prompt_compiler_policy(compiler_policy)
    kernel_validation = validate_identity_kernel(identity_kernel)
    persona_validation = validate_persona_manifest(persona_manifest)
    operator_validation = validate_operator_contract(operator_contract)
    modes_validation = validate_communication_mode_registry(mode_registry)

    mode_lookup = get_communication_mode(mode_registry, selected_mode)
    normalized_mode = mode_lookup.mode_name or selected_mode
    mode_lookup_ok = mode_lookup.found and mode_lookup.mode is not None

    contradictions = _detect_source_contradictions(
        identity_kernel,
        persona_manifest,
        operator_contract,
        mode_registry,
        compiler_policy,
        selected_mode,
        kernel_valid=kernel_validation.valid,
        persona_valid=persona_validation.valid,
        operator_valid=operator_validation.valid,
        modes_valid=modes_validation.valid,
        policy_valid=policy_validation.valid,
        mode_lookup_ok=mode_lookup_ok,
    )

    critical = [c for c in contradictions if c.severity == "critical"]
    if critical:
        critical_failures = [c.reason for c in critical]
        return IdentityPromptCompileResult(
            valid=False,
            context=None,
            errors=tuple(errors),
            warnings=tuple(warnings),
            critical_failures=tuple(critical_failures),
            contradictions=tuple(contradictions),
            context_hash=None,
        )

    kernel_hash = compute_identity_kernel_hash(identity_kernel).value
    persona_hash = compute_persona_manifest_hash(persona_manifest).value
    operator_hash = compute_operator_contract_hash(operator_contract).value
    modes_hash = compute_communication_mode_registry_hash(mode_registry).value
    policy_hash = compute_identity_prompt_compiler_policy_hash(compiler_policy).value

    persona_summary = build_persona_safe_summary(persona_manifest)
    operator_summary = build_operator_contract_safe_summary(operator_contract)
    mode_summary = build_communication_mode_safe_summary(mode_registry, normalized_mode)
    mode_spec = mode_lookup.mode
    assert mode_spec is not None

    bundle = IdentityPromptSourceBundle(
        identity_kernel_hash=kernel_hash,
        persona_manifest_hash=persona_hash,
        operator_contract_hash=operator_hash,
        communication_modes_hash=modes_hash,
        compiler_policy_hash=policy_hash,
        selected_mode=normalized_mode,
    )

    context = IdentityPromptContext(
        schema_version=compiler_policy.schema_version,
        compiler_version=compiler_policy.compiler_version,
        agent_name=identity_kernel.name,
        agent_class=identity_kernel.agent_class,
        selected_mode=normalized_mode,
        source_bundle=bundle,
        agent_identity_section=_build_agent_identity_section(identity_kernel),
        operator_relationship_section=_build_operator_relationship_section(
            operator_summary.authority_rules
            + operator_summary.disagreement_rules
            + operator_summary.challenge_rules
            + operator_summary.non_manipulation_rules
            + operator_summary.accountability_rules
        ),
        persona_expression_section=_build_persona_expression_section(
            persona_summary.honesty_rules
            + persona_summary.risk_communication_rules
            + persona_summary.challenge_rules
            + (persona_summary.voice_summary, f"Postures: {persona_summary.posture_summary}.")
        ),
        active_mode_section=_build_active_mode_section(
            normalized_mode,
            mode_summary.output_rules
            + mode_summary.challenge_rules
            + mode_summary.risk_rules
            + mode_summary.authority_boundaries,
            mode_spec.purpose,
            mode_spec.cognitive_posture,
        ),
        authority_boundaries_section=_build_authority_boundaries_section(
            identity_kernel,
            persona_summary.authority_boundaries,
            mode_summary.authority_boundaries,
        ),
        capability_honesty_section=_build_capability_honesty_section(
            persona_summary.capability_honesty_rules
        ),
        non_goals_section=_build_non_goals_section(),
        source_integrity_section=_build_source_integrity_section(
            bundle, compiler_policy.compiler_version
        ),
    )

    context_validation = validate_identity_prompt_context(context)
    if not context_validation.valid:
        post_contradictions = list(contradictions)
        for idx, err in enumerate(context_validation.errors, start=25):
            post_contradictions.append(
                _contradiction(
                    f"CTR-{idx:03d}",
                    "compiled_context",
                    "content",
                    "present",
                    "missing",
                    err,
                )
            )
        critical_failures = list(context_validation.critical_failures)
        return IdentityPromptCompileResult(
            valid=False,
            context=None,
            errors=tuple(context_validation.errors),
            warnings=tuple(warnings),
            critical_failures=tuple(critical_failures),
            contradictions=tuple(post_contradictions),
            context_hash=None,
        )

    context_hash = compute_identity_prompt_context_hash(context).value
    return IdentityPromptCompileResult(
        valid=True,
        context=context,
        errors=tuple(errors),
        warnings=tuple(warnings),
        critical_failures=(),
        contradictions=tuple(contradictions),
        context_hash=context_hash,
    )


def compile_identity_prompt_context_from_paths(
    selected_mode: str,
    *,
    kernel_path: str | Path | None = None,
    persona_path: str | Path | None = None,
    operator_path: str | Path | None = None,
    modes_path: str | Path | None = None,
    compiler_path: str | Path | None = None,
) -> IdentityPromptCompileResult:
    """Load identity sources from paths and compile prompt context."""
    try:
        identity_kernel = load_identity_kernel(kernel_path)
        persona_manifest = load_persona_manifest(persona_path)
        operator_contract = load_operator_contract(operator_path)
        from ..identity.communication_modes import load_communication_mode_registry

        mode_registry = load_communication_mode_registry(modes_path)
        compiler_policy = load_identity_prompt_compiler_policy(compiler_path)
    except Exception as exc:
        return IdentityPromptCompileResult(
            valid=False,
            context=None,
            errors=(str(exc),),
            warnings=(),
            critical_failures=(str(exc),),
            contradictions=(
                _contradiction(
                    "CTR-000",
                    "loader",
                    "source",
                    "loaded",
                    "missing",
                    str(exc),
                ),
            ),
            context_hash=None,
        )
    return compile_identity_prompt_context(
        identity_kernel,
        persona_manifest,
        operator_contract,
        mode_registry,
        selected_mode,
        compiler_policy,
    )


_SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("agent_identity", "agent_identity_section"),
    ("operator_relationship", "operator_relationship_section"),
    ("persona_expression", "persona_expression_section"),
    ("active_mode", "active_mode_section"),
    ("authority_boundaries", "authority_boundaries_section"),
    ("capability_honesty", "capability_honesty_section"),
    ("non_goals", "non_goals_section"),
    ("source_integrity", "source_integrity_section"),
)


def render_identity_prompt_context(context: IdentityPromptContext) -> str:
    """Render compiled context as deterministic prompt fragment text."""
    parts: list[str] = []
    for header, attr in _SECTION_ORDER:
        lines = getattr(context, attr)
        parts.append(f"## {header}")
        parts.extend(f"- {line}" for line in lines)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def context_sections_dict(context: IdentityPromptContext) -> dict[str, list[str]]:
    """Serialize section tuples to dict for CLI JSON output."""
    return {
        header: list(getattr(context, attr))
        for header, attr in _SECTION_ORDER
    }
