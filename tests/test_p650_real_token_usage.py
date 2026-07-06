"""P0-S.1 — truthful token/cost accounting: real usage into the ledger.

Kills the fictional flat 1200-token / 0.01 USD estimate: a usage-bearing model
response records real tokens and marks the run substantiated; an absent usage
keeps the legacy estimate but stamps it estimate_only (never a synthesized
number). Real objects only.
"""
from __future__ import annotations

import pytest

from agentic_runtime.budget import BudgetExceeded, BudgetLedger, BudgetPolicy
from agentic_runtime.model_providers import anthropic_provider
from agentic_runtime.model_providers.base import ModelRequest, TokenUsage
from agentic_runtime.reasoning import TokenAccountingView


def _fake_post_json_with_usage(*_args, **_kwargs):
    data = {
        "content": [{"type": "text", "text": '{"steps": []}'}],
        "usage": {"input_tokens": 100, "output_tokens": 50},
        "stop_reason": "end_turn",
    }
    return data, None, 5.0


def test_anthropic_usage_populates_ledger_not_flat_estimate(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_provider, "post_json", _fake_post_json_with_usage)
    provider = anthropic_provider.AnthropicProvider()
    resp = provider.generate_structured_plan(
        ModelRequest(system_prompt="s", user_prompt="u"))

    assert resp.usage is not None
    assert resp.usage.total_tokens == 150  # real, not the flat 1200

    led = BudgetLedger()
    led.charge_llm(usage=resp.usage)
    snap = led.snapshot()["usage"]
    assert snap["estimated_tokens"] == 150
    assert snap["estimated_tokens"] != 1200
    assert snap["substantiated"] is True
    assert snap["estimate_only"] is False
    assert TokenAccountingView.from_snapshot(led.snapshot()).substantiated is True


def test_missing_usage_marks_estimate_only_and_substantiated_false():
    led = BudgetLedger()
    led.charge_llm()  # no usage → legacy estimate, honestly flagged
    snap = led.snapshot()["usage"]
    assert snap["estimated_tokens"] == 1200
    assert snap["estimate_only"] is True
    assert snap["substantiated"] is False
    view = TokenAccountingView.from_snapshot(led.snapshot())
    assert view.substantiated is False and view.estimate_only is True


def test_reasoning_tokens_charged_distinct_from_output_tokens():
    led = BudgetLedger()
    led.charge_llm(usage=TokenUsage(prompt_tokens=100, completion_tokens=50,
                                    total_tokens=190, reasoning_tokens=40))
    snap = led.snapshot()["usage"]
    assert snap["estimated_tokens"] == 190
    assert snap["thinking_tokens"] == 40
    view = TokenAccountingView.from_snapshot(led.snapshot())
    assert view.thinking_tokens == 40
    assert view.output_tokens == 150  # 190 total − 40 thinking


def test_mixed_history_is_not_substantiated():
    # substantiated is unconstructible-True: one estimate taints the whole run.
    led = BudgetLedger()
    led.charge_llm()  # estimate
    led.charge_llm(usage=TokenUsage(prompt_tokens=10, completion_tokens=10,
                                    total_tokens=20))
    view = TokenAccountingView.from_snapshot(led.snapshot())
    assert view.substantiated is False
    assert view.estimate_only is True


def test_real_usage_still_enforces_cap_via_check():
    led = BudgetLedger(BudgetPolicy(max_estimated_tokens=100))
    with pytest.raises(BudgetExceeded):
        led.charge_llm(usage=TokenUsage(prompt_tokens=200, completion_tokens=0,
                                        total_tokens=200))


def test_precheck_denies_before_call_without_mutating():
    led = BudgetLedger(BudgetPolicy(max_estimated_tokens=100))
    with pytest.raises(BudgetExceeded):
        led.precheck_llm()  # projected 1200 > 100 → deny before any call
    # nothing was recorded by the guard
    assert led.snapshot()["usage"]["estimated_tokens"] == 0
