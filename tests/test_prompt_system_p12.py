"""P1.2 — Prompt System Seed tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentic_runtime.model_config import ProviderConfigLoader
from agentic_runtime.model_router import ModelRouter
from agentic_runtime.prompt_system import (
    PromptRegistry,
    PromptRenderError,
    PromptValidationError,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts"
AGENT_CONFIG = REPO_ROOT / "agent" / "config"


def _manifest(
    *,
    prompt_id: str = "test_prompt",
    version: str = "0.1.0",
    owner: str = "tests",
    template: str = "Hello {{ name }}",
    risk_tier: str = "low",
    allowed_model_profiles: str = "  - planning\n",
    policy_extra: str = "",
    output_schema: str = "output_schema:\n  type: object\n  required:\n    - answer\n",
) -> str:
    return (
        f"id: {prompt_id}\n"
        f"version: {version}\n"
        f"owner: {owner}\n"
        "status: active\n"
        "purpose: test prompt\n"
        "description: Test manifest.\n"
        "allowed_model_profiles:\n"
        f"{allowed_model_profiles}"
        "allowed_tasks:\n"
        "  - planning\n"
        f"risk_tier: {risk_tier}\n"
        "input_schema:\n"
        "  type: object\n"
        "  required:\n"
        "    - name\n"
        f"{output_schema}"
        "policy:\n"
        "  may_execute_tools: false\n"
        "  may_modify_files: false\n"
        "  may_request_secrets: false\n"
        "  may_expand_authority: false\n"
        "  raw_prompt_trace_allowed: false\n"
        "  trace_summary_required: true\n"
        f"{policy_extra}"
        "forbidden:\n"
        "  - execute_tools\n"
        "  - modify_files\n"
        "  - reveal_secrets\n"
        "  - override_policy\n"
        "  - ignore_custos\n"
        "  - change_tests_without_permission\n"
        "evals:\n"
        "  - test_eval\n"
        "template:\n"
        f"  - {template}\n"
    )


def _write_prompt(tmp_path: Path, text: str) -> Path:
    root = tmp_path / "prompts"
    root.mkdir()
    (root / "prompt.yaml").write_text(text, encoding="utf-8")
    return root


def test_valid_prompt_loads():
    registry = PromptRegistry(PROMPTS_DIR).load()
    prompt = registry.get("repo_planner")
    assert prompt.metadata.id == "repo_planner"
    assert prompt.metadata.version


def test_registry_lists_prompts():
    registry = PromptRegistry(PROMPTS_DIR).load()
    ids = {p.id for p in registry.list_prompts()}
    assert {"repo_planner", "reviewer", "summarizer", "patch_synthesizer"} <= ids


def test_registry_get_unknown_fails_safely():
    registry = PromptRegistry(PROMPTS_DIR).load()
    with pytest.raises(PromptValidationError, match="unknown prompt id"):
        registry.get("missing_prompt")


def test_missing_id_rejected(tmp_path):
    root = _write_prompt(tmp_path, _manifest().replace("id: test_prompt\n", ""))
    with pytest.raises(PromptValidationError, match="id is required"):
        PromptRegistry(root).load()


def test_missing_version_rejected(tmp_path):
    root = _write_prompt(tmp_path, _manifest().replace("version: 0.1.0\n", ""))
    with pytest.raises(PromptValidationError, match="version is required"):
        PromptRegistry(root).load()


def test_missing_owner_rejected(tmp_path):
    root = _write_prompt(tmp_path, _manifest().replace("owner: tests\n", ""))
    with pytest.raises(PromptValidationError, match="owner is required"):
        PromptRegistry(root).load()


def test_missing_template_rejected(tmp_path):
    root = _write_prompt(tmp_path, _manifest().replace("template:\n  - Hello {{ name }}\n", ""))
    with pytest.raises(PromptValidationError, match="template is required"):
        PromptRegistry(root).load()


def test_serious_prompt_missing_output_schema_rejected(tmp_path):
    root = _write_prompt(
        tmp_path,
        _manifest(risk_tier="medium", output_schema=""),
    )
    with pytest.raises(PromptValidationError, match="serious prompts require output_schema"):
        PromptRegistry(root).load()


@pytest.mark.parametrize(
    "risk_tier",
    ["trivial", "low", "medium", "high", "critical", "r0", "r1", "r2", "r3", "r4", "r5"],
)
def test_documented_risk_tiers_load(tmp_path, risk_tier):
    root = _write_prompt(tmp_path, _manifest(risk_tier=risk_tier))
    prompt = PromptRegistry(root).load().get("test_prompt")
    assert prompt.metadata.risk_tier == risk_tier


def test_unknown_risk_tier_rejected(tmp_path):
    root = _write_prompt(tmp_path, _manifest(risk_tier="nonsense"))
    with pytest.raises(PromptValidationError, match="invalid risk_tier"):
        PromptRegistry(root).load()


def test_blank_risk_tier_rejected(tmp_path):
    root = _write_prompt(tmp_path, _manifest(risk_tier='""'))
    with pytest.raises(PromptValidationError, match="risk_tier is required"):
        PromptRegistry(root).load()


def test_missing_risk_tier_rejected(tmp_path):
    text = _manifest().replace("risk_tier: low\n", "")
    root = _write_prompt(tmp_path, text)
    with pytest.raises(PromptValidationError, match="risk_tier is required"):
        PromptRegistry(root).load()


def test_allowed_model_profiles_must_be_list(tmp_path):
    text = _manifest().replace(
        "allowed_model_profiles:\n  - planning\n",
        "allowed_model_profiles: planning\n",
    )
    root = _write_prompt(tmp_path, text)
    with pytest.raises(PromptValidationError, match="allowed_model_profiles must be a list"):
        PromptRegistry(root).load()


def test_policy_may_expand_authority_true_rejected(tmp_path):
    text = _manifest().replace("may_expand_authority: false", "may_expand_authority: true")
    root = _write_prompt(tmp_path, text)
    with pytest.raises(PromptValidationError, match="may_expand_authority"):
        PromptRegistry(root).load()


def test_policy_may_request_secrets_true_rejected(tmp_path):
    text = _manifest().replace("may_request_secrets: false", "may_request_secrets: true")
    root = _write_prompt(tmp_path, text)
    with pytest.raises(PromptValidationError, match="may_request_secrets"):
        PromptRegistry(root).load()


def test_planning_prompt_may_execute_tools_true_rejected(tmp_path):
    text = _manifest().replace("may_execute_tools: false", "may_execute_tools: true")
    root = _write_prompt(tmp_path, text)
    with pytest.raises(PromptValidationError, match="planning prompts may not execute tools"):
        PromptRegistry(root).load()


def test_prompt_with_raw_api_key_rejected(tmp_path):
    text = _manifest(template="Do not store sk-test-secret-value-123456789")
    root = _write_prompt(tmp_path, text)
    with pytest.raises(PromptValidationError, match="raw secret-like"):
        PromptRegistry(root).load()


def test_template_renders_with_variables(tmp_path):
    root = _write_prompt(tmp_path, _manifest())
    result = PromptRegistry(root).load().render("test_prompt", {"name": "Aurel"})
    assert result.rendered_prompt == ""
    assert result.trace_summary.prompt_id == "test_prompt"
    assert "Aurel" in result.trace_summary.rendered_preview_redacted


def test_raw_prompt_request_obeys_manifest_policy_denied(tmp_path):
    root = _write_prompt(tmp_path, _manifest())
    result = PromptRegistry(root).load().render(
        "test_prompt",
        {"name": "Aurel"},
        include_raw_prompt=True,
    )
    assert result.rendered_prompt == ""
    assert result.trace_summary.raw_prompt_stored is False


def test_raw_prompt_request_allowed_only_when_manifest_policy_allows(tmp_path):
    text = _manifest().replace(
        "raw_prompt_trace_allowed: false",
        "raw_prompt_trace_allowed: true",
    )
    root = _write_prompt(tmp_path, text)
    result = PromptRegistry(root).load().render(
        "test_prompt",
        {"name": "Aurel"},
        include_raw_prompt=True,
    )
    assert result.rendered_prompt == "Hello Aurel"
    assert result.trace_summary.raw_prompt_stored is False


def test_missing_variable_fails_safely(tmp_path):
    root = _write_prompt(tmp_path, _manifest())
    with pytest.raises(PromptRenderError, match="missing template variables"):
        PromptRegistry(root).load().render("test_prompt", {})


def test_render_records_variables_and_hashes(tmp_path):
    root = _write_prompt(tmp_path, _manifest())
    summary = PromptRegistry(root).load().render("test_prompt", {"name": "Aurel"}).trace_summary
    assert summary.variables_used == ["name"]
    assert len(summary.rendered_hash) == 64
    assert len(summary.template_hash) == 64
    assert summary.raw_prompt_stored is False


def test_render_preview_redacted_and_bounded(tmp_path):
    root = _write_prompt(tmp_path, _manifest(template="Value {{ name }}"))
    value = "plain text " * 80
    summary = PromptRegistry(root).load().render("test_prompt", {"name": value}).trace_summary
    assert len(summary.rendered_preview_redacted) <= 240
    assert "truncated" in summary.rendered_preview_redacted


def test_render_rejects_secret_like_variable(tmp_path):
    root = _write_prompt(tmp_path, _manifest())
    with pytest.raises(PromptRenderError, match="raw secret-like"):
        PromptRegistry(root).load().render("test_prompt", {"name": "sk-test-secret-value-123456"})


def test_allowed_model_profiles_validate_against_agent_config():
    bundle = ProviderConfigLoader(AGENT_CONFIG).load()
    registry = PromptRegistry(
        PROMPTS_DIR,
        model_config=bundle,
        validate_model_profiles=True,
    ).load()
    assert registry.get("repo_planner").metadata.allowed_model_profiles


def test_invalid_model_profile_reference_fails_when_enabled(tmp_path):
    text = _manifest(allowed_model_profiles="  - missing_profile\n")
    root = _write_prompt(tmp_path, text)
    bundle = ProviderConfigLoader(AGENT_CONFIG).load()
    with pytest.raises(PromptValidationError, match="unknown model profile"):
        PromptRegistry(root, model_config=bundle, validate_model_profiles=True).load()


def test_invalid_model_profile_reference_loads_without_config(tmp_path):
    text = _manifest(allowed_model_profiles="  - missing_profile\n")
    root = _write_prompt(tmp_path, text)
    registry = PromptRegistry(root).load()
    assert registry.get("test_prompt").metadata.allowed_model_profiles == ["missing_profile"]


def test_mock_offline_mode_still_works_without_api_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    raw, provider = ModelRouter().complete("balanced", "system", "GOAL: inspect")
    assert provider == "mock"
    assert "list_dir" in raw


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": f"src{os.pathsep}."},
        capture_output=True,
        text=True,
    )


def test_cli_prompts_validate_succeeds():
    proc = _cli("prompts", "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "valid" in proc.stdout.lower()


def test_cli_prompts_list_succeeds():
    proc = _cli("prompts", "list")
    assert proc.returncode == 0
    assert "repo_planner" in proc.stdout


def test_cli_prompts_show_does_not_leak_raw_secrets(monkeypatch):
    secret = "sk-cli-prompt-secret-value"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    proc = _cli("prompts", "show", "repo_planner")
    assert proc.returncode == 0
    assert secret not in proc.stdout
    assert "template" not in proc.stdout


def test_cli_prompts_render_returns_trace_safe_summary():
    proc = _cli("prompts", "render", "repo_planner", "--var", "objective=test", "--dry-run")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["prompt_id"] == "repo_planner"
    assert payload["raw_prompt_stored"] is False
    assert "rendered_hash" in payload
    assert "You produce bounded" not in proc.stdout
