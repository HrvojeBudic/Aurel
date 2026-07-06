"""DeepSeek live variant — provider wiring + spine cognition leg (stubbed HTTP)."""

from __future__ import annotations

import agentic_runtime.model_providers.deepseek_provider as dsp
from agentic_runtime.model_providers.base import ModelProviderConfig, ModelRequest
from agentic_runtime.model_providers.deepseek_provider import DeepSeekProvider
from agentic_runtime.model_router import create_provider
from agentic_runtime.spine.harness import build_deepseek_client

_PLAN_JSON = (
    '{"intent_summary": "fix calc", "plan": [{"step_id": "s1", "tool": '
    '"write_file", "args": {"path": "calc.py", "content": "VALUE = 2\\n"}, '
    '"risk": "medium", "reason": "patch"}], "confidence": 0.9, '
    '"requires_approval": true, "assumptions": [], "refusal_reason": null}'
)


def _stub_ok(monkeypatch, capture=None):
    def fake_post_json(url, payload, *, headers=None, timeout=30.0):
        if capture is not None:
            capture["url"] = url
            capture["payload"] = payload
            capture["headers"] = headers
        return ({"choices": [{"message": {"content": _PLAN_JSON}}]}, None, 12.0)

    monkeypatch.setattr(dsp, "post_json", fake_post_json)


def test_router_creates_deepseek_provider():
    provider = create_provider("deepseek")
    assert isinstance(provider, DeepSeekProvider)
    assert provider.name == "deepseek"


def test_deepseek_missing_key_is_honest_unavailable(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    provider = DeepSeekProvider()
    resp = provider.generate_structured_plan(
        ModelRequest(system_prompt="s", user_prompt="u")
    )
    assert resp.error and "DEEPSEEK_API_KEY" in resp.error
    assert resp.raw_text == ""


def test_deepseek_provider_hits_openai_compatible_endpoint(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    capture: dict = {}
    _stub_ok(monkeypatch, capture)
    provider = DeepSeekProvider(
        ModelProviderConfig(
            provider_name="deepseek",
            model_name="deepseek-v4-pro",
            api_key_env="DEEPSEEK_API_KEY",
            base_url="https://api.deepseek.com",
        )
    )
    resp = provider.generate_structured_plan(
        ModelRequest(system_prompt="plan in JSON", user_prompt="fix it")
    )
    assert resp.error is None
    assert resp.raw_text == _PLAN_JSON
    # OpenAI-compatible path + DeepSeek JSON mode + bearer auth
    assert capture["url"] == "https://api.deepseek.com/chat/completions"
    assert capture["payload"]["model"] == "deepseek-v4-pro"
    assert capture["payload"]["response_format"] == {"type": "json_object"}
    assert capture["headers"]["Authorization"] == "Bearer sk-test"


def test_build_deepseek_client_shorthands(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    _stub_ok(monkeypatch)
    pro = build_deepseek_client("pro")
    flash = build_deepseek_client("flash")
    assert pro.provider.config.model_name == "deepseek-v4-pro"
    assert flash.provider.config.model_name == "deepseek-v4-flash"


def test_spine_cognition_leg_live_with_deepseek(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    _stub_ok(monkeypatch)
    from agentic_runtime.spine.harness import _model_leg

    evidence, raw = _model_leg(build_deepseek_client("pro"), "fix calc")
    assert evidence.available is True
    assert evidence.model_name == "deepseek"
    assert evidence.response_hash
    assert raw
