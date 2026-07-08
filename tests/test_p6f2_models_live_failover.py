"""F2 seal — live model profiles with failover chains + honest fail.

Proves: a config profile with a ``failover:`` chain registers ranked clients;
a refusing/erroring earlier link fails over to the next; a chain whose every
link is unusable returns an HONEST refusal (never a silent mock answer); the
standard-profile posture (AUREL_ALLOW_MOCK_FALLBACK=0) refuses the implicit
mock default; the shipped config/live bundle parses with the F2 chains; and a
chainless profile behaves byte-identically to pre-F2.
"""

from __future__ import annotations

import json

from agentic_runtime.governance.enforcement_profiles import (
    profile_process_env, profile_spec)
from agentic_runtime.model_config import (FailoverTarget, ModelConfigBundle,
                                          ModelProfile, ProviderConfigLoader,
                                          ProviderProfile, RuntimeModelConfig)
from agentic_runtime.model_router import ModelRouter

from agentic_runtime.model_providers.schemas import structured_plan_payload

PLAN = json.dumps(structured_plan_payload(
    [{"step_id": "s1", "tool": "read_file", "args": {"path": "a.py"},
      "reason": "look", "risk": "low"}],
    intent_summary="test", confidence=0.9, requires_approval=False,
    assumptions=[]))


def _bundle(profiles: dict, providers: dict | None = None) -> ModelConfigBundle:
    provs = providers or {
        "deepseek": ProviderProfile(name="deepseek", type="deepseek",
                                    residency="remote",
                                    api_key_env="DEEPSEEK_API_KEY",
                                    default_model="deepseek-v4-pro"),
        "qwen": ProviderProfile(name="qwen", type="qwen", residency="remote",
                                api_key_env="DASHSCOPE_API_KEY",
                                default_model="qwen-max"),
        "mock": ProviderProfile(name="mock", type="mock", residency="local",
                                default_model="mock-deterministic"),
    }
    return ModelConfigBundle(
        providers=provs,
        profiles=profiles,
        runtime=RuntimeModelConfig(local_only=False, allow_remote_models=True),
    )


def _chain_profile() -> ModelProfile:
    return ModelProfile(
        name="planning", provider="deepseek", model="deepseek-v4-pro",
        purpose="planning", allowed_tasks=["planning"],
        failover=[FailoverTarget("qwen", "qwen-max")])


class _ScriptedClient:
    """Stand-in ranked client: returns a fixed raw string."""

    def __init__(self, name: str, raw: str) -> None:
        self.name = name
        self._raw = raw

    def complete(self, system: str, user: str) -> str:
        return self._raw


def _refusal(reason: str) -> str:
    from agentic_runtime.model_providers.schemas import refusal_json
    return refusal_json(reason)


# 1 ─ a failover chain registers one ranked client per usable link.
def test_chain_registers_ranked_clients(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-a")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-b")
    router = ModelRouter(config=_bundle({"planning": _chain_profile()}))
    router.select_profile("planning")
    clients = router._profiles["planning"]
    assert [c.name for c in clients] == ["deepseek", "qwen"]


# 2 ─ a refusing first link fails over; the second link's answer is returned.
#     (config-less router: the ranked-client loop itself is under test)
def test_refusing_link_fails_over():
    router = ModelRouter()
    router.register("chain", [
        _ScriptedClient("dead-primary", _refusal("DEEPSEEK_API_KEY not configured")),
        _ScriptedClient("live-failover", PLAN),
    ])
    raw, name = router.complete("chain", "sys", "user")
    assert name == "live-failover"
    assert json.loads(raw)["intent_summary"] == "test"
    # All links refusing ⇒ the LAST refusal is returned honestly.
    router.register("dead", [
        _ScriptedClient("a", _refusal("no key A")),
        _ScriptedClient("b", _refusal("no key B")),
    ])
    raw2, name2 = router.complete("dead", "sys", "user")
    assert json.loads(raw2)["refusal_reason"] == "no key B"
    assert name2 == "b"


# 3 ─ all links unusable ⇒ HONEST refusal (never a silent mock answer).
def test_all_links_fail_is_honest_refusal(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    router = ModelRouter(config=_bundle({"planning": _chain_profile()}))
    raw, name = router.complete("planning", "sys", "user")
    data = json.loads(raw)
    assert data["refusal_reason"]                     # honest refusal envelope
    assert data["plan"] == []                          # no fabricated plan
    assert name in ("router", "planning", "deepseek", "qwen")


# 4 ─ missing key on the primary only ⇒ the keyed failover link answers.
def test_missing_primary_key_uses_failover_link(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-b")
    import agentic_runtime.model_providers.qwen_provider as qp
    monkeypatch.setattr(qp, "post_json", lambda *a, **k: (
        {"choices": [{"message": {"content": PLAN}, "finish_reason": "stop"}],
         "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
        "", 3.0))
    router = ModelRouter(config=_bundle({"planning": _chain_profile()}))
    raw, name, usage = router.complete_with_usage("planning", "sys", "user")
    assert name == "qwen"
    assert json.loads(raw)["intent_summary"] == "test"
    assert usage is not None and usage.total_tokens == 2


# 5 ─ standard posture: implicit mock default refuses honestly.
def test_standard_posture_refuses_silent_mock(monkeypatch):
    monkeypatch.delenv("AUREL_MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("AUREL_ALLOW_MOCK_FALLBACK", "0")
    router = ModelRouter()                            # no config, defaulted mock
    raw, name = router.complete("balanced", "sys", "user")
    data = json.loads(raw)
    assert "silent mock fallback is disabled" in data["refusal_reason"]
    # An EXPLICIT operator mock choice still works (not a silent fallback).
    monkeypatch.setenv("AUREL_MODEL_PROVIDER", "mock")
    explicit = ModelRouter()
    raw2, _ = explicit.complete("balanced", "sys", "user")
    assert not json.loads(raw2).get("refusal_reason")


# 5b ─ the standard/hardened profiles carry the posture; dev keeps mock.
def test_profiles_set_mock_fallback_posture():
    env: dict[str, str] = {}
    applied = profile_process_env(profile_spec("standard"), env=env)
    assert applied.get("AUREL_ALLOW_MOCK_FALLBACK") == "0"
    assert profile_spec("hardened").allow_mock_fallback is False
    assert profile_spec("dev").allow_mock_fallback is True
    dev_env: dict[str, str] = {}
    profile_process_env(profile_spec("dev"), env=dev_env)
    assert "AUREL_ALLOW_MOCK_FALLBACK" not in dev_env


# 6 ─ the shipped config/live bundle parses with the F2 chains.
def test_shipped_live_bundle_parses():
    bundle = ProviderConfigLoader("config/live").load()
    planning = bundle.get_profile("planning")
    assert planning.provider == "anthropic"
    assert [(f.provider, f.model) for f in planning.failover] == [
        ("deepseek", "deepseek-v4-pro"), ("qwen", "qwen-max")]
    assert bundle.get_profile("coding").failover[0].provider == "qwen"
    assert bundle.get_profile("challenger").failover[0].provider == "kimi"
    assert bundle.get_profile("summarization").failover[0].provider == "ollama"
    # Chainless profile stays valid (byte-identical pre-F2 shape).
    assert bundle.get_profile("local_fast").failover == []


# 7 ─ chainless profile: single client, exactly the pre-F2 registration.
def test_chainless_profile_single_client(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-a")
    prof = ModelProfile(name="solo", provider="deepseek", model="deepseek-v4-pro",
                        purpose="planning", allowed_tasks=["planning"])
    router = ModelRouter(config=_bundle({"solo": prof}))
    router.select_profile("solo")
    assert [c.name for c in router._profiles["solo"]] == ["deepseek"]
