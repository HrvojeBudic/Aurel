"""P1.4.5 — Identity Prompt Context Compiler tests (cases #1-43, #60-65)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from agentic_runtime.identity.communication_modes import (
    AurelCommunicationModeRegistry,
    CommunicationModeGlobalBoundaries,
    CommunicationModeSpec,
    load_communication_mode_registry,
)
from agentic_runtime.identity.kernel import AurelIdentityKernel, IdentityImmutables, load_identity_kernel
from agentic_runtime.identity.operator_contract import (
    AurelOperatorContract,
    OperatorAuthorityRules,
    load_operator_contract,
)
from agentic_runtime.identity.persona import AurelPersonaManifest, load_persona_manifest
from agentic_runtime.prompts.compiler_policy import (
    IdentityPromptCompilerPolicy,
    IdentityPromptCompilerSafety,
    load_identity_prompt_compiler_policy,
)
from agentic_runtime.prompts.identity_context import IdentityPromptContext
from agentic_runtime.prompts.identity_context_compiler import (
    compile_identity_prompt_context,
    compile_identity_prompt_context_from_paths,
    render_identity_prompt_context,
)
from agentic_runtime.prompts.identity_context_validation import validate_identity_prompt_context

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KERNEL = REPO_ROOT / "config" / "aurel" / "identity_kernel.yaml"
CANONICAL_PERSONA = REPO_ROOT / "config" / "aurel" / "persona_manifest.yaml"
CANONICAL_OPERATOR = REPO_ROOT / "config" / "aurel" / "operator_contract.yaml"
CANONICAL_MODES = REPO_ROOT / "config" / "aurel" / "communication_modes.yaml"
CANONICAL_COMPILER = REPO_ROOT / "config" / "aurel" / "identity_prompt_compiler.yaml"


@pytest.fixture(name="sources")
def fixture_sources():
    return {
        "kernel": load_identity_kernel(CANONICAL_KERNEL),
        "persona": load_persona_manifest(CANONICAL_PERSONA),
        "operator": load_operator_contract(CANONICAL_OPERATOR),
        "modes": load_communication_mode_registry(CANONICAL_MODES),
        "policy": load_identity_prompt_compiler_policy(CANONICAL_COMPILER),
    }


def _compile(sources, mode: str):
    return compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        mode,
        sources["policy"],
    )


def _full_text(result) -> str:
    assert result.context is not None
    return render_identity_prompt_context(result.context).lower()


@pytest.mark.parametrize(
    "mode",
    ["FOCUS", "DEBUG", "DEPLOY", "SHADOW", "EVOLVE", "CHANNEL", "HERETIC"],
)
def test_valid_sources_compile_all_modes(sources, mode):
    result = _compile(sources, mode)
    assert result.valid is True
    assert result.context is not None
    assert result.context.selected_mode == mode
    assert result.context_hash is not None
    assert len(result.context_hash) == 64


def test_unknown_mode_fails_safely(sources):
    result = _compile(sources, "UNKNOWN")
    assert result.valid is False
    assert result.context is None
    assert result.context_hash is None
    assert result.critical_failures
    assert any("does not exist" in c.reason for c in result.contradictions)


def test_lowercase_mode_normalizes(sources):
    result = _compile(sources, "deploy")
    assert result.valid is True
    assert result.context is not None
    assert result.context.selected_mode == "DEPLOY"


@pytest.mark.parametrize(
    ("missing_path_kwarg", "label"),
    [
        ("kernel_path", "kernel"),
        ("persona_path", "persona"),
        ("operator_path", "operator"),
        ("modes_path", "modes"),
        ("compiler_path", "compiler"),
    ],
)
def test_missing_source_fails_compile(missing_path_kwarg, label):
    kwargs = {
        "kernel_path": CANONICAL_KERNEL,
        "persona_path": CANONICAL_PERSONA,
        "operator_path": CANONICAL_OPERATOR,
        "modes_path": CANONICAL_MODES,
        "compiler_path": CANONICAL_COMPILER,
    }
    kwargs[missing_path_kwarg] = REPO_ROOT / "nonexistent" / f"{label}.yaml"
    result = compile_identity_prompt_context_from_paths("FOCUS", **kwargs)
    assert result.valid is False
    assert result.context is None


def test_invalid_identity_kernel_fails_compile(sources):
    bad_kernel = dataclasses.replace(
        sources["kernel"],
        immutables=dataclasses.replace(
            sources["kernel"].immutables,
            self_escalation_allowed=True,
        ),
    )
    result = compile_identity_prompt_context(
        bad_kernel,
        sources["persona"],
        sources["operator"],
        sources["modes"],
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False
    assert any("self-escalation" in c.reason.lower() for c in result.contradictions)


def test_invalid_persona_manifest_fails_compile(sources):
    bad_persona = dataclasses.replace(sources["persona"], can_grant_permissions=True)
    result = compile_identity_prompt_context(
        sources["kernel"],
        bad_persona,
        sources["operator"],
        sources["modes"],
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False
    assert any("grant permissions" in c.reason.lower() for c in result.contradictions)


def test_invalid_operator_contract_fails_compile(sources):
    bad_operator = dataclasses.replace(
        sources["operator"],
        authority=dataclasses.replace(
            sources["operator"].authority,
            aurel_final_authority=True,
        ),
    )
    result = compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        bad_operator,
        sources["modes"],
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False
    assert any("final authority" in c.reason.lower() for c in result.contradictions)


def test_invalid_communication_mode_registry_fails_compile(sources):
    bad_gb = dataclasses.replace(
        sources["modes"].global_boundaries,
        modes_can_execute_actions=True,
    )
    bad_modes = dataclasses.replace(sources["modes"], global_boundaries=bad_gb)
    result = compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        bad_modes,
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False
    assert any("execute actions" in c.reason.lower() for c in result.contradictions)


def test_invalid_compiler_policy_fails_compile(sources):
    bad_policy = dataclasses.replace(
        sources["policy"],
        safety=dataclasses.replace(
            sources["policy"].safety,
            raw_yaml_in_prompt_forbidden=False,
        ),
    )
    result = compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        "FOCUS",
        bad_policy,
    )
    assert result.valid is False
    assert any("raw yaml" in c.reason.lower() for c in result.contradictions)


def test_raw_yaml_in_prompt_forbidden(sources):
    result = _compile(sources, "FOCUS")
    rendered = render_identity_prompt_context(result.context)
    assert "identity_kernel:" not in rendered
    assert "schema_version:" not in rendered


def test_rendered_prompt_does_not_contain_raw_config_dump(sources):
    result = _compile(sources, "DEPLOY")
    rendered = render_identity_prompt_context(result.context)
    assert "operator_contract:" not in rendered
    assert "communication_modes:" not in rendered
    assert "persona_manifest:" not in rendered


def test_context_includes_operator_final_authority(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "final authority" in text


def test_context_includes_no_self_escalation(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "self-escalation" in text or "cannot raise its own authority" in text


def test_context_includes_no_tool_authority_statement(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "tool authority" in text


def test_context_includes_no_action_authority_statement(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "action authority" in text


def test_context_includes_no_autonomy_change_statement(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "autonomy" in text


def test_context_includes_no_memory_write_authorization(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "memory write" in text


def test_context_includes_no_policy_bypass_statement(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "policy bypass" in text


def test_context_includes_no_canonization_statement(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "canoniz" in text


def test_context_includes_capability_honesty_rule(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "capability honesty" in text or "unverified capabilit" in text


def test_context_distinguishes_planned_implemented_verified(sources):
    text = _full_text(_compile(sources, "FOCUS"))
    assert "planned" in text and "implemented" in text and "verified" in text


def test_context_includes_selected_mode(sources):
    result = _compile(sources, "CHANNEL")
    assert result.context is not None
    assert "CHANNEL" in render_identity_prompt_context(result.context)


def test_deploy_context_includes_test_orientation(sources):
    text = _full_text(_compile(sources, "DEPLOY"))
    assert "test orientation" in text or "acceptance criteria" in text


def test_shadow_context_includes_adversarial_orientation(sources):
    text = _full_text(_compile(sources, "SHADOW"))
    assert "adversarial" in text or "risk-first" in text


def test_heretic_context_includes_candidate_only(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "candidate-only" in text or "candidate only" in text


def test_heretic_context_includes_no_real_world_side_effects(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "real-world side effect" in text or "no real-world side effects" in text


def test_heretic_context_includes_no_identity_modification(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "modify identity" in text or "identity modification" in text


def test_heretic_context_includes_no_policy_modification(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "modify policy" in text or "policy modification" in text


def test_heretic_context_includes_no_memory_modification(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "modify memory" in text or "memory modification" in text


def test_heretic_context_includes_no_tool_modification(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "modify tool" in text or "tool modification" in text


def test_heretic_context_includes_no_autonomy_modification(sources):
    text = _full_text(_compile(sources, "HERETIC"))
    assert "modify autonomy" in text or "autonomy modification" in text


def test_context_includes_source_hashes(sources):
    result = _compile(sources, "FOCUS")
    assert result.context is not None
    integrity = "\n".join(result.context.source_integrity_section)
    assert "identity_kernel_hash:" in integrity
    assert len(result.context.source_bundle.identity_kernel_hash) == 64


def test_context_includes_compiler_version(sources):
    result = _compile(sources, "FOCUS")
    assert result.context is not None
    integrity = "\n".join(result.context.source_integrity_section)
    assert "compiler_version:" in integrity


def test_contradiction_mode_executes_actions_true_fails(sources):
    focus = sources["modes"].modes["FOCUS"]
    bad_focus = CommunicationModeSpec(
        name=focus.name,
        purpose=focus.purpose,
        cognitive_posture=focus.cognitive_posture,
        output_bias=dict(focus.output_bias),
        challenge_emphasis=dict(focus.challenge_emphasis),
        risk_emphasis=dict(focus.risk_emphasis),
        boundaries={**dict(focus.boundaries), "executes_actions": True},
    )
    bad_modes = dataclasses.replace(
        sources["modes"],
        modes={**dict(sources["modes"].modes), "FOCUS": bad_focus},
    )
    result = compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        bad_modes,
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False
    assert any("executes actions" in c.reason.lower() for c in result.contradictions)


def test_contradiction_persona_grants_permissions_true_fails(sources):
    bad_persona = dataclasses.replace(sources["persona"], can_grant_permissions=True)
    result = compile_identity_prompt_context(
        sources["kernel"],
        bad_persona,
        sources["operator"],
        sources["modes"],
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False


def test_contradiction_operator_aurel_final_authority_true_fails(sources):
    bad_operator = dataclasses.replace(
        sources["operator"],
        authority=dataclasses.replace(
            sources["operator"].authority,
            aurel_final_authority=True,
        ),
    )
    result = compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        bad_operator,
        sources["modes"],
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False


def test_contradiction_kernel_self_escalation_allowed_true_fails(sources):
    bad_kernel = dataclasses.replace(
        sources["kernel"],
        immutables=dataclasses.replace(
            sources["kernel"].immutables,
            self_escalation_allowed=True,
        ),
    )
    result = compile_identity_prompt_context(
        bad_kernel,
        sources["persona"],
        sources["operator"],
        sources["modes"],
        "FOCUS",
        sources["policy"],
    )
    assert result.valid is False


def test_contradiction_compiler_policy_raw_yaml_false_fails(sources):
    bad_policy = dataclasses.replace(
        sources["policy"],
        safety=dataclasses.replace(
            sources["policy"].safety,
            raw_yaml_in_prompt_forbidden=False,
        ),
    )
    result = compile_identity_prompt_context(
        sources["kernel"],
        sources["persona"],
        sources["operator"],
        sources["modes"],
        "FOCUS",
        bad_policy,
    )
    assert result.valid is False


def test_contradiction_missing_capability_honesty_fails_validation(sources):
    result = _compile(sources, "FOCUS")
    assert result.context is not None
    bad_context = dataclasses.replace(result.context, capability_honesty_section=())
    validation = validate_identity_prompt_context(bad_context)
    assert validation.valid is False
    assert any("capability honesty" in err for err in validation.errors)
