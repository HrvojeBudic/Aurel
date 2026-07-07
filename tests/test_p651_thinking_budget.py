"""P0-S.2 — shared reasoning/simulation budget seam.

charge_reasoning() and charge_simulation() route through the same _check() as
every other charge: overspend raises BudgetExceeded and traces a deny. This is
the seam the reasoning scheduler (Track B), the sim-gate (Track C), and the
dual-kernel speculative fork charge against. Real objects only.
"""
from __future__ import annotations

import pytest

from agentic_runtime.budget import BudgetExceeded, BudgetLedger, BudgetPolicy
from agentic_runtime.model_providers.base import TokenUsage


class _FakeTrace:
    def __init__(self) -> None:
        self.records: list = []

    def append_budget_decision(self, rec):
        self.records.append(rec)
        return rec


def _denies(trace: _FakeTrace, metric: str) -> list:
    return [r for r in trace.records if r.metric == metric and r.verdict == "deny"]


def _ledger(**caps) -> tuple[BudgetLedger, _FakeTrace]:
    tr = _FakeTrace()
    led = BudgetLedger(BudgetPolicy(**caps))
    led.bind_trace(tr)
    return led, tr


def test_charge_reasoning_passes_overspend_raises_and_traces_deny():
    led, tr = _ledger(max_reasoning_passes_per_run=2)
    led.charge_reasoning()
    led.charge_reasoning()
    with pytest.raises(BudgetExceeded):
        led.charge_reasoning()  # 3rd pass > 2
    assert _denies(tr, "max_reasoning_passes_per_run")


def test_charge_reasoning_thinking_calls_cap_traces_deny():
    led, tr = _ledger(max_thinking_calls=1)
    led.charge_reasoning()
    with pytest.raises(BudgetExceeded):
        led.charge_reasoning()
    assert _denies(tr, "max_thinking_calls")


def test_charge_reasoning_token_reservation_cap_traces_deny():
    led, tr = _ledger(max_thinking_tokens=100)
    with pytest.raises(BudgetExceeded):
        led.charge_reasoning(tokens=200)
    assert _denies(tr, "max_thinking_tokens")


def test_charge_simulation_overspend_raises_and_traces_deny():
    led, tr = _ledger(max_simulation_execs=1)
    led.charge_simulation()
    with pytest.raises(BudgetExceeded):
        led.charge_simulation()
    assert _denies(tr, "max_simulation_execs")


def test_real_reasoning_tokens_from_usage_are_capped():
    led, tr = _ledger(max_thinking_tokens=50)
    with pytest.raises(BudgetExceeded):
        led.charge_llm(usage=TokenUsage(prompt_tokens=10, completion_tokens=10,
                                        total_tokens=20, reasoning_tokens=100))
    assert _denies(tr, "max_thinking_tokens")


def test_ordinary_llm_charge_does_not_check_thinking_cap():
    # usage=None (mock path) charges no reasoning tokens → no thinking-cap check,
    # so the common path stays trace-identical to P0-S.1.
    led, tr = _ledger(max_thinking_tokens=200_000)
    led.charge_llm()
    assert _denies(tr, "max_thinking_tokens") == []
    assert not any(r.metric == "max_thinking_tokens" for r in tr.records)


def test_snapshot_exposes_reasoning_and_simulation_counters():
    led, _ = _ledger()
    led.charge_reasoning(tokens=500)
    led.charge_simulation()
    usage = led.snapshot()["usage"]
    assert usage["reasoning_passes"] == 1
    assert usage["thinking_calls"] == 1
    assert usage["thinking_tokens"] == 500
    assert usage["simulation_execs"] == 1
    policy = led.snapshot()["policy"]
    for cap in ("max_thinking_tokens", "max_thinking_calls",
                "max_reasoning_passes_per_run", "max_simulation_execs"):
        assert cap in policy
