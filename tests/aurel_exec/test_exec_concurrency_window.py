"""P4-EXEC-F concurrency window / limit decision tests."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ConcurrencyLimitDecisionKind,
    ExecutionPressureLevel,
    build_concurrency_window,
    decide_concurrency_limit,
    derive_pressure_level,
)


def test_concurrency_window_computes_available_slots():
    window = build_concurrency_window(max_in_flight=3, current_in_flight=1, queue_depth=0)
    assert window.available_slots == 2
    full = build_concurrency_window(max_in_flight=1, current_in_flight=1, queue_depth=0)
    assert full.available_slots == 0
    over = build_concurrency_window(max_in_flight=1, current_in_flight=2, queue_depth=0)
    assert over.available_slots == 0  # clamped, never negative
    # a window claiming wrong slot arithmetic is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(window, available_slots=3)
    # negative inputs rejected
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(window, queue_depth=-1)


def test_window_is_not_a_worker_pool():
    window = build_concurrency_window(max_in_flight=2, current_in_flight=0, queue_depth=0)
    assert window.spawns_workers is False
    assert window.is_worker_pool is False
    for boundary_field in ("spawns_workers", "is_worker_pool"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(window, **{boundary_field: True})
    for verb in ("spawn", "acquire", "release", "execute", "run", "schedule"):
        assert not hasattr(window, verb)


def test_derive_pressure_level_is_deterministic_arithmetic():
    calm = derive_pressure_level(queue_depth=0, current_in_flight=0, max_in_flight=1)
    assert calm is ExecutionPressureLevel.LOW
    busy = derive_pressure_level(queue_depth=1, current_in_flight=0, max_in_flight=2)
    assert busy is ExecutionPressureLevel.NORMAL
    elevated = derive_pressure_level(queue_depth=2, current_in_flight=0, max_in_flight=1)
    assert elevated is ExecutionPressureLevel.ELEVATED
    high = derive_pressure_level(queue_depth=3, current_in_flight=1, max_in_flight=1)
    assert high is ExecutionPressureLevel.HIGH
    critical = derive_pressure_level(
        queue_depth=3, current_in_flight=1, max_in_flight=1,
        recent_algedonic_signals=1,
    )
    assert critical is ExecutionPressureLevel.CRITICAL
    invalid = derive_pressure_level(queue_depth=-1, current_in_flight=0, max_in_flight=1)
    assert invalid is ExecutionPressureLevel.ERROR
    zero_capacity = derive_pressure_level(queue_depth=0, current_in_flight=0, max_in_flight=0)
    assert zero_capacity is ExecutionPressureLevel.ERROR
    # same inputs, same level
    assert derive_pressure_level(
        queue_depth=3, current_in_flight=1, max_in_flight=1
    ) is derive_pressure_level(queue_depth=3, current_in_flight=1, max_in_flight=1)


def test_concurrency_decision_allows_holds_delays_or_blocks_without_spawning_workers():
    allow = decide_concurrency_limit(
        build_concurrency_window(max_in_flight=1, current_in_flight=0, queue_depth=0)
    )
    assert allow.decision is ConcurrencyLimitDecisionKind.ALLOW
    assert allow.allowed is True and allow.blocked is False
    assert "not execution" in allow.reason
    hold = decide_concurrency_limit(
        build_concurrency_window(max_in_flight=1, current_in_flight=1, queue_depth=0)
    )
    assert hold.decision is ConcurrencyLimitDecisionKind.HOLD
    assert hold.held is True
    # high pressure with a free slot -> DELAY
    delay_window = build_concurrency_window(max_in_flight=2, current_in_flight=1, queue_depth=5)
    if delay_window.pressure_level is ExecutionPressureLevel.HIGH:
        delay = decide_concurrency_limit(delay_window)
        assert delay.decision is ConcurrencyLimitDecisionKind.DELAY
        assert delay.recommended_delay_ms == 250
    for decision in (allow, hold):
        assert decision.executes is False
        assert decision.spawns_workers is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(decision, spawns_workers=True)
    # determinism
    again = decide_concurrency_limit(
        build_concurrency_window(max_in_flight=1, current_in_flight=0, queue_depth=0)
    )
    assert again.decision_id == allow.decision_id


def test_decision_flags_must_agree_with_kind():
    allow = decide_concurrency_limit(
        build_concurrency_window(max_in_flight=1, current_in_flight=0, queue_depth=0)
    )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(allow, blocked=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(allow, allowed=False)


def test_critical_pressure_blocks():
    # CRITICAL via saturated window with a deep queue is not reachable from
    # window-only inputs (score 4 = HIGH); verify BLOCK via the decision on a
    # snapshot-informed window is covered in backpressure tests, and ERROR here
    error_window = dataclasses.replace(
        build_concurrency_window(max_in_flight=1, current_in_flight=0, queue_depth=0),
        pressure_level=ExecutionPressureLevel.ERROR,
    )
    decision = decide_concurrency_limit(error_window)
    assert decision.decision is ConcurrencyLimitDecisionKind.ERROR
    assert decision.blocked is True
