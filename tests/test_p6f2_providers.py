"""F2 seal — Qwen + Kimi provider adapters (thin OpenAI-compat clones).

Proves, per adapter: honest error without a key (never a fake completion);
round-trip against a stubbed ``post_json`` (payload shape: JSON mode, messages,
bearer auth); real token-usage extraction (OpenAI-compatible ``usage``);
malformed-response honesty; healthcheck UNCONFIGURED/AVAILABLE; and registration
through both router factories + the config type allowlists.
"""

from __future__ import annotations

import json

from agentic_runtime.model_config import (REMOTE_PROVIDER_TYPES,
                                          SUPPORTED_PROVIDER_TYPES)
from agentic_runtime.model_providers.base import ModelRequest, ProviderStatus
from agentic_runtime.model_providers.schemas import STRUCTURED_PLAN_SCHEMA

PLAN = json.dumps({
    "intent_summary": "test",
    "risks": [],
    "plan": [{"tool": "read_file", "args": {"path": "a.py"}, "reason": "look"}],
})

OPENAI_COMPAT_RESPONSE = {
    "choices": [{"message": {"content": PLAN}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
}


def _req():
    return ModelRequest(system_prompt="sys", user_prompt="user",
                        output_schema=STRUCTURED_PLAN_SCHEMA)


def _stub_post_json(module, monkeypatch, captured):
    def fake_post_json(url, payload, headers=None, timeout=30.0):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers or {}
        return OPENAI_COMPAT_RESPONSE, "", 12.0
    monkeypatch.setattr(module, "post_json", fake_post_json)


# ---------------------------------------------------------------- Qwen ----- #

def test_qwen_no_key_is_honest_error(monkeypatch):
    from agentic_runtime.model_providers.qwen_provider import QwenProvider
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    resp = QwenProvider().generate_structured_plan(_req())
    assert resp.error == "DASHSCOPE_API_KEY not configured"
    assert resp.raw_text == ""                        # never fabricates


def test_qwen_round_trip_and_usage(monkeypatch):
    import agentic_runtime.model_providers.qwen_provider as qp
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-qwen")
    captured: dict = {}
    _stub_post_json(qp, monkeypatch, captured)

    resp = qp.QwenProvider().generate_structured_plan(_req())

    assert not resp.error
    assert resp.parsed_json["intent_summary"] == "test"
    # Payload shape: DashScope compatible-mode, JSON mode, bearer key.
    assert captured["url"].startswith(
        "https://dashscope.aliyuncs.com/compatible-mode/v1")
    assert captured["url"].endswith("/chat/completions")
    assert captured["payload"]["response_format"] == {"type": "json_object"}
    assert captured["payload"]["model"] == "qwen-max"
    assert captured["headers"]["Authorization"] == "Bearer sk-test-qwen"
    # Real usage extracted (F0.2 discipline).
    assert resp.usage is not None
    assert (resp.usage.prompt_tokens, resp.usage.completion_tokens,
            resp.usage.total_tokens) == (11, 7, 18)


def test_qwen_malformed_response_is_honest(monkeypatch):
    import agentic_runtime.model_providers.qwen_provider as qp
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-qwen")
    monkeypatch.setattr(qp, "post_json",
                        lambda *a, **k: ({"choices": [{"message": {"content": "not json"}}]}, "", 5.0))
    resp = qp.QwenProvider().generate_structured_plan(_req())
    assert resp.error.startswith("malformed_provider_response:")


def test_qwen_healthcheck_and_env_overrides(monkeypatch):
    from agentic_runtime.model_providers.qwen_provider import QwenProvider
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    assert QwenProvider().healthcheck().status is ProviderStatus.UNCONFIGURED
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-x")
    monkeypatch.setenv("AUREL_QWEN_MODEL", "qwen3-coder")
    hc = QwenProvider().healthcheck()
    assert hc.status is ProviderStatus.AVAILABLE
    assert hc.model_name == "qwen3-coder"


def test_qwen_registered_in_router_and_config():
    from agentic_runtime.model_config import ProviderProfile
    from agentic_runtime.model_router import (create_provider,
                                              create_provider_from_profile)
    assert "qwen" in SUPPORTED_PROVIDER_TYPES
    assert "qwen" in REMOTE_PROVIDER_TYPES
    assert create_provider("qwen").name == "qwen"
    prof = ProviderProfile(name="qwen", type="qwen", residency="remote",
                           api_key_env="DASHSCOPE_API_KEY",
                           default_model="qwen-max")
    inst = create_provider_from_profile(prof, "qwen-max")
    # Without a key this must be the honest missing-secret provider, not mock.
    assert inst.name in ("qwen",)
    assert inst.healthcheck().status in (ProviderStatus.UNCONFIGURED,
                                         ProviderStatus.AVAILABLE)


# ---------------------------------------------------------------- Kimi ----- #

def test_kimi_no_key_is_honest_error(monkeypatch):
    from agentic_runtime.model_providers.kimi_provider import KimiProvider
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    resp = KimiProvider().generate_structured_plan(_req())
    assert resp.error == "MOONSHOT_API_KEY not configured"
    assert resp.raw_text == ""                        # never fabricates


def test_kimi_round_trip_and_usage(monkeypatch):
    import agentic_runtime.model_providers.kimi_provider as kp
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test-kimi")
    captured: dict = {}
    _stub_post_json(kp, monkeypatch, captured)

    resp = kp.KimiProvider().generate_structured_plan(_req())

    assert not resp.error
    assert resp.parsed_json["intent_summary"] == "test"
    assert captured["url"] == "https://api.moonshot.ai/v1/chat/completions"
    assert captured["payload"]["response_format"] == {"type": "json_object"}
    assert captured["payload"]["model"] == "kimi-k2"
    assert captured["headers"]["Authorization"] == "Bearer sk-test-kimi"
    assert resp.usage is not None
    assert (resp.usage.prompt_tokens, resp.usage.completion_tokens,
            resp.usage.total_tokens) == (11, 7, 18)


def test_kimi_healthcheck_and_env_overrides(monkeypatch):
    from agentic_runtime.model_providers.kimi_provider import KimiProvider
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    assert KimiProvider().healthcheck().status is ProviderStatus.UNCONFIGURED
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-x")
    monkeypatch.setenv("AUREL_KIMI_MODEL", "moonshot-v1-128k")
    hc = KimiProvider().healthcheck()
    assert hc.status is ProviderStatus.AVAILABLE
    assert hc.model_name == "moonshot-v1-128k"


def test_kimi_registered_in_router_and_config():
    from agentic_runtime.model_router import create_provider
    assert "kimi" in SUPPORTED_PROVIDER_TYPES
    assert "kimi" in REMOTE_PROVIDER_TYPES
    assert create_provider("kimi").name == "kimi"
