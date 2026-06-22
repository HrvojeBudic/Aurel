"""P1.1 — Model configuration and secret boundary tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agentic_runtime.model_config import (
    ModelConfigError,
    ProviderConfigLoader,
)
from agentic_runtime.model_providers.mock_provider import MockProvider
from agentic_runtime.model_providers.schemas import STRUCTURED_PLAN_SCHEMA
from agentic_runtime.model_router import ModelRouter, ProviderModelClient
from agentic_runtime.plan_validator import PlanStatus, PlanValidator
from agentic_runtime.secrets import (
    EnvSecretProvider,
    SecretBoundaryViolation,
    SecretReference,
    SecretRedactor,
    assert_no_raw_secrets_in_yaml,
)
from agentic_runtime.yaml_minimal import YamlParseError, load_yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_CONFIG = REPO_ROOT / "agent" / "config"


def test_default_config_loads():
    bundle = ProviderConfigLoader.load_defaults()
    assert "mock" in bundle.providers
    assert "planning" in bundle.profiles
    assert bundle.runtime.local_only is True


def test_agent_config_files_load():
    bundle = ProviderConfigLoader(AGENT_CONFIG).load()
    assert bundle.providers["openai"].api_key_env == "OPENAI_API_KEY"
    assert bundle.profiles["coding"].purpose == "coding"
    assert bundle.runtime.store_raw_prompts is False


def test_invalid_provider_reference_fails(tmp_path):
    (tmp_path / "providers.yaml").write_text(
        "providers:\n  mock:\n    type: mock\n    residency: local\n",
        encoding="utf-8",
    )
    (tmp_path / "models.yaml").write_text(
        "profiles:\n  bad:\n    provider: missing\n    model: x\n    purpose: test\n    allowed_tasks: []\n",
        encoding="utf-8",
    )
    (tmp_path / "runtime.yaml").write_text("local_only: true\n", encoding="utf-8")
    with pytest.raises(ModelConfigError, match="unknown provider"):
        ProviderConfigLoader(tmp_path).load()


def test_raw_api_key_field_in_yaml_fails():
    data = {"providers": {"openai": {"api_key": "sk-secret"}}}
    with pytest.raises(SecretBoundaryViolation, match="raw secret field"):
        assert_no_raw_secrets_in_yaml(data)


def test_unknown_provider_rejected(tmp_path):
    (tmp_path / "providers.yaml").write_text("providers: {}\n", encoding="utf-8")
    (tmp_path / "models.yaml").write_text(
        "profiles:\n  x:\n    provider: ghost\n    model: m\n    purpose: p\n    allowed_tasks: []\n",
        encoding="utf-8",
    )
    (tmp_path / "runtime.yaml").write_text(
        "local_only: true\nallow_unconfigured_providers: false\n",
        encoding="utf-8",
    )
    with pytest.raises(ModelConfigError):
        ProviderConfigLoader(tmp_path).load()


def test_local_only_blocks_remote_model_profile(tmp_path):
    (tmp_path / "providers.yaml").write_text(
        "providers:\n"
        "  mock:\n    type: mock\n    residency: local\n"
        "  openai:\n    type: openai\n    residency: remote\n    api_key_env: OPENAI_API_KEY\n",
        encoding="utf-8",
    )
    (tmp_path / "models.yaml").write_text(
        "profiles:\n"
        "  remote_plan:\n    provider: openai\n    model: gpt-4\n"
        "    purpose: planning\n    allowed_tasks: [planning]\n",
        encoding="utf-8",
    )
    (tmp_path / "runtime.yaml").write_text(
        "local_only: true\nallow_remote_models: true\n",
        encoding="utf-8",
    )
    with pytest.raises(ModelConfigError, match="local_only"):
        ProviderConfigLoader(tmp_path).load()


def test_env_secret_resolves(monkeypatch):
    monkeypatch.setenv("TEST_P11_SECRET", "value-123")
    result = EnvSecretProvider().resolve(SecretReference("TEST_P11_SECRET"))
    assert result.ok
    assert result.value == "value-123"


def test_missing_secret_is_structured():
    result = EnvSecretProvider().resolve(SecretReference("MISSING_P11_SECRET_XYZ"))
    assert not result.ok
    assert "not configured" in result.error


def test_redactor_removes_real_looking_secrets():
    secret = "sk-test-abcdefghijklmnopqrstuvwxyz123456"
    text = f"failed auth with {secret} and OPENAI_API_KEY={secret}"
    redacted = SecretRedactor(known_values=[secret]).redact(text)
    assert secret not in redacted
    assert "[REDACTED]" in redacted


def test_provider_status_never_leaks_secret_values(monkeypatch):
    secret = "sk-test-never-print-this-value-abc123xyz"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    bundle = ProviderConfigLoader.load_defaults()
    # Enable remote in a copy-like runtime override via temp config
    router = ModelRouter(config=bundle)
    output = json.dumps(router.provider_status())
    assert secret not in output


def test_reports_errors_are_redacted():
    secret = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
    redacted = SecretRedactor().redact(f"auth failed: {secret}")
    assert "eyJhbGci" not in redacted


def test_mock_provider_still_works_offline():
    router = ModelRouter()
    raw, name = router.complete("balanced", "system", "GOAL: inspect")
    assert name == "mock"
    assert PlanValidator({"list_dir"}).parse_and_validate(raw).valid


def test_planning_profile_can_use_mock():
    bundle = ProviderConfigLoader.load_defaults()
    router = ModelRouter(config=bundle)
    router.select_profile("planning")
    raw, name = router.complete("planning", "system", "GOAL: inspect")
    assert name == "mock"
    assert PlanValidator({"list_dir"}).parse_and_validate(raw).valid


def test_local_only_allows_local_mock_profiles():
    bundle = ProviderConfigLoader.load_defaults()
    router = ModelRouter(config=bundle)
    router.select_profile("local_fast")
    raw, provider = router.complete("local_fast", "s", "GOAL: x")
    assert provider == "mock"
    assert PlanValidator({"list_dir"}).parse_and_validate(raw).valid


def test_local_only_blocks_openai_anthropic():
    bundle = ProviderConfigLoader.load_defaults()
    assert bundle.runtime.local_only
    router = ModelRouter(config=bundle)
    openai = bundle.providers["openai"]
    anthropic = bundle.providers["anthropic"]
    assert "local_only" in router._check_provider_allowed(openai, "test")
    assert "local_only" in router._check_provider_allowed(anthropic, "test")
    rows = {r["provider"]: r for r in router.provider_status()}
    assert rows["openai"]["enabled"] == "no"
    assert rows["anthropic"]["enabled"] == "no"


def test_remote_provider_missing_key_fails_safely(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    bundle = ProviderConfigLoader.load_defaults()
    router = ModelRouter(config=bundle)
    # openai should be disabled in provider status
    rows = {r["provider"]: r for r in router.provider_status()}
    assert rows["openai"]["secret_status"] == "missing"
    assert rows["openai"]["enabled"] == "no"


def test_existing_structured_completion_still_passes():
    router = ModelRouter()
    router.register("balanced", [ProviderModelClient(MockProvider())])
    raw, name = router.complete_structured(
        "balanced", "system", "divide zero", STRUCTURED_PLAN_SCHEMA,
    )
    assert name == "mock"
    data = json.loads(raw)
    assert "intent_summary" in data or "plan" in data


def test_cli_config_validate_passes():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", "config", "validate"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": f"src{os.pathsep}."},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "valid" in proc.stdout.lower()


def test_cli_models_list_does_not_leak_secrets(monkeypatch):
    secret = "sk-cli-leak-test-secret-value"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", "models", "list"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": f"src{os.pathsep}."},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert secret not in proc.stdout


def test_cli_providers_status_does_not_leak_secrets(monkeypatch):
    secret = "sk-cli-provider-status-secret"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", "providers", "status"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": f"src{os.pathsep}."},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert secret not in proc.stdout


def test_yaml_minimal_parses_agent_config():
    text = (AGENT_CONFIG / "runtime.yaml").read_text(encoding="utf-8")
    data = load_yaml(text)
    assert data["local_only"] is True


def test_yaml_minimal_parses_list_of_mappings_without_truncation():
    data = load_yaml(
        "items:\n"
        "  - name: first\n"
        "    description: one\n"
        "  - name: second\n"
        "    description: two\n"
    )
    assert data == {
        "items": [
            {"name": "first", "description": "one"},
            {"name": "second", "description": "two"},
        ]
    }


def test_yaml_minimal_rejects_unsupported_scalar_list_continuation():
    with pytest.raises(YamlParseError, match="unsupported nested scalar list item"):
        load_yaml(
            "items:\n"
            "  - first\n"
            "    description: one\n"
        )
