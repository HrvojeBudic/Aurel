"""P1.4.5 — Identity Prompt Context renderer tests (cases #51-53)."""

from __future__ import annotations

from pathlib import Path

from agentic_runtime.identity.communication_modes import load_communication_mode_registry
from agentic_runtime.identity.kernel import load_identity_kernel
from agentic_runtime.identity.operator_contract import load_operator_contract
from agentic_runtime.identity.persona import load_persona_manifest
from agentic_runtime.prompts.compiler_policy import load_identity_prompt_compiler_policy
from agentic_runtime.prompts.identity_context_compiler import (
    compile_identity_prompt_context,
    render_identity_prompt_context,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _render(mode: str) -> str:
    result = compile_identity_prompt_context(
        load_identity_kernel(REPO_ROOT / "config" / "aurel" / "identity_kernel.yaml"),
        load_persona_manifest(REPO_ROOT / "config" / "aurel" / "persona_manifest.yaml"),
        load_operator_contract(REPO_ROOT / "config" / "aurel" / "operator_contract.yaml"),
        load_communication_mode_registry(REPO_ROOT / "config" / "aurel" / "communication_modes.yaml"),
        mode,
        load_identity_prompt_compiler_policy(
            REPO_ROOT / "config" / "aurel" / "identity_prompt_compiler.yaml"
        ),
    )
    assert result.valid and result.context is not None
    return render_identity_prompt_context(result.context)


def test_renderer_preserves_section_order():
    rendered = _render("FOCUS")
    headers = [line for line in rendered.splitlines() if line.startswith("## ")]
    assert headers == [
        "## agent_identity",
        "## operator_relationship",
        "## persona_expression",
        "## active_mode",
        "## authority_boundaries",
        "## capability_honesty",
        "## non_goals",
        "## source_integrity",
    ]


def test_renderer_includes_source_integrity_section():
    rendered = _render("DEPLOY")
    assert "## source_integrity" in rendered
    assert "identity_kernel_hash:" in rendered
    assert "compiler_policy_hash:" in rendered


def test_renderer_does_not_expose_raw_yaml():
    rendered = _render("HERETIC")
    assert "identity_kernel:" not in rendered
    assert "communication_modes:" not in rendered
    assert "operator_contract:" not in rendered
    assert "persona_manifest:" not in rendered
    assert "schema_version:" not in rendered
