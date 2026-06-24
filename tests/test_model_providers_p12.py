"""P0.12 — Real LLM Adapter Layer tests."""

from __future__ import annotations

import json
import os

import pytest

from agentic_runtime import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    Intent,
    PlanStatus,
    RiskLevel,
    build_runtime,
)
from agentic_runtime.hitl import AutoApprover
from agentic_runtime.model_providers.base import ModelRequest
from agentic_runtime.model_providers.http_utils import post_json
from agentic_runtime.model_providers.mock_provider import MockProvider
from agentic_runtime.model_providers.openai_provider import OpenAIProvider
from agentic_runtime.model_providers.schemas import (
    STRUCTURED_PLAN_SCHEMA,
    structured_plan_payload,
    validate_structured_plan_payload,
)
from agentic_runtime.model_router import (ModelRouter, ProviderModelClient)
from agentic_runtime.plan_validator import PlanValidator
from agentic_runtime.sandbox import UnsafeLocalSandbox


def _request() -> ModelRequest:
    return ModelRequest(
        system_prompt="plan only",
        user_prompt="GOAL: inspect",
        output_schema=STRUCTURED_PLAN_SCHEMA,
    )


def _card():
    return AgentCard.make(
        name="Planner",
        agent_class=AgentClass.EXECUTION,
        mission="test",
        authority=AuthorityScope(read_paths=["*"], write_paths=["src/"],
                                 max_risk=RiskLevel.HIGH),
        allowed_tools=["list_dir", "read_file", "write_file", "edit_file"],
    )


def test_mock_provider_valid_output():
    provider = MockProvider()
    resp = provider.generate_structured_plan(_request())
    assert resp.ok
    result = validate_structured_plan_payload(resp.parsed_json)
    assert result.ok
    assert result.plan[0]["tool"] == "list_dir"


def test_mock_provider_invalid_json_rejected():
    router = ModelRouter()
    router.register("balanced", [
        ProviderModelClient(MockProvider(failure_mode="invalid_json")),
    ])
    raw, provider_name = router.complete("balanced", "system", "GOAL: x")
    assert provider_name == "mock"
    result = PlanValidator({"list_dir"}).parse_and_validate(raw)
    assert result.status is PlanStatus.INVALID_JSON


def test_missing_required_field_rejected():
    router = ModelRouter()
    router.register("balanced", [
        ProviderModelClient(MockProvider(failure_mode="missing_required_field")),
    ])
    raw, _ = router.complete("balanced", "system", "GOAL: x")
    result = PlanValidator({"list_dir"}).parse_and_validate(raw)
    assert not result.valid
    assert result.status in {PlanStatus.EMPTY_PLAN, PlanStatus.INVALID_SCHEMA}


def test_router_default_provider_is_mock(monkeypatch):
    monkeypatch.delenv("AUREL_MODEL_PROVIDER", raising=False)
    router = ModelRouter()
    raw, provider_name = router.complete("balanced", "system", "GOAL: x")
    assert provider_name == "mock"
    assert PlanValidator({"list_dir"}).parse_and_validate(raw).valid


def test_router_selects_provider_from_env(monkeypatch):
    monkeypatch.setenv("AUREL_MODEL_PROVIDER", "ollama")
    router = ModelRouter()
    router.configure_default()
    assert router.default_provider == "ollama"
    health = router.health()["balanced"][0]
    assert health.provider_name == "ollama"


def test_provider_errors_are_structured():
    router = ModelRouter()
    router.register("balanced", [
        ProviderModelClient(MockProvider(failure_mode="provider_timeout")),
    ])
    raw, _ = router.complete("balanced", "system", "GOAL: x")
    data = json.loads(raw)
    assert data["plan"] == []
    assert "provider_timeout" in data["refusal_reason"]
    result = PlanValidator({"list_dir"}).parse_and_validate(raw)
    assert result.status is PlanStatus.EMPTY_PLAN


def test_no_api_key_leaks_in_error_messages(monkeypatch):
    secret = "sk-test-secret-never-log"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("AUREL_OPENAI_BASE_URL", "http://127.0.0.1:9")
    provider = OpenAIProvider()
    resp = provider.generate_structured_plan(ModelRequest(
        system_prompt="s",
        user_prompt="u",
        output_schema=STRUCTURED_PLAN_SCHEMA,
        timeout_seconds=0.1,
    ))
    assert resp.error
    assert secret not in resp.error
    assert secret not in (resp.raw_text or "")


def test_post_json_rejects_non_http_schemes():
    data, error, latency = post_json("file:///etc/passwd", {"x": 1})
    assert data is None
    assert error == "provider_error:ValueError"
    assert latency >= 0.0


def test_structured_plan_schema_validation():
    good = structured_plan_payload(
        [{
            "step_id": "s1",
            "tool": "list_dir",
            "args": {"path": "."},
            "risk": "trivial",
            "reason": "inspect",
        }],
        intent_summary="inspect",
        confidence=0.8,
        requires_approval=False,
    )
    assert validate_structured_plan_payload(good).ok

    bad = dict(good)
    bad.pop("confidence")
    result = validate_structured_plan_payload(bad)
    assert not result.ok
    assert any("confidence" in e for e in result.errors)


def test_refusal_produces_no_commands(tmp_path):
    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path)),
        approval_gate=AutoApprover(),
        model_clients={"balanced": [
            ProviderModelClient(MockProvider(failure_mode="refusal")),
        ]},
    )
    report = kernel.spawn(_card()).run(Intent.make("refuse this"))
    assert report["status"] == "halted"
    assert report["planning_status"] == PlanStatus.EMPTY_PLAN.value
    assert report["actions_executed"] == 0


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not configured",
)
def test_openai_integration_skipped_without_key():
    # This test intentionally does not call the network in normal offline runs.
    assert os.environ["OPENAI_API_KEY"]


@pytest.mark.skipif(
    os.environ.get("AUREL_RUN_OLLAMA_TESTS") != "1",
    reason="local Ollama integration tests not explicitly enabled",
)
def test_ollama_integration_skipped_by_default():
    assert os.environ.get("AUREL_RUN_OLLAMA_TESTS") == "1"
