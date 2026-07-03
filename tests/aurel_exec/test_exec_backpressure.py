"""P4-EXEC-F pressure snapshot / backpressure tests — feedback, not recovery."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    BackpressureDecisionKind,
    BackpressureSignalKind,
    ExecutionPressureLevel,
    build_backpressure_signal_if_needed,
    build_execution_pressure_snapshot,
    classify_pre_submit_block,
    create_algedonic_signal_if_needed,
    decide_backpressure,
)


def _snapshot(**overrides):
    values = dict(queue_depth=0, current_in_flight=0, max_in_flight=1)
    values.update(overrides)
    return build_execution_pressure_snapshot(**values)


def test_pressure_snapshot_reflects_queue_inflight_failures_and_algedonic_inputs():
    calm = _snapshot()
    assert calm.pressure_level is ExecutionPressureLevel.LOW
    assert calm.recent_failures == 0
    assert calm.recent_algedonic_signals == 0
    # real P4-E judgment objects feed the pressure derivation
    critical_failure = classify_pre_submit_block("XX", exec_job_id="exec-job-a")
    algedonic = create_algedonic_signal_if_needed(critical_failure)
    assert algedonic is not None
    pressured = _snapshot(
        queue_depth=3,
        current_in_flight=1,
        failure_classifications=(critical_failure,),
        algedonic_signals=(algedonic,),
    )
    assert pressured.recent_failures == 1
    assert pressured.recent_algedonic_signals == 1
    assert pressured.pressure_level is ExecutionPressureLevel.CRITICAL
    # a snapshot whose level contradicts the derivation is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(pressured, pressure_level=ExecutionPressureLevel.LOW)
    # determinism
    assert _snapshot().snapshot_hash == _snapshot().snapshot_hash


def test_backpressure_signal_emitted_for_high_pressure():
    calm = _snapshot()
    assert build_backpressure_signal_if_needed(calm) is None
    saturated = _snapshot(queue_depth=3, current_in_flight=1)  # HIGH
    signal = build_backpressure_signal_if_needed(saturated)
    assert signal is not None
    assert signal.signal_kind is BackpressureSignalKind.NO_AVAILABLE_SLOTS
    assert signal.severity is ExecutionPressureLevel.HIGH
    # algedonic input dominates the kind priority
    critical_failure = classify_pre_submit_block("XX", exec_job_id="exec-job-a")
    algedonic = create_algedonic_signal_if_needed(critical_failure)
    urgent = _snapshot(
        queue_depth=3, current_in_flight=1, algedonic_signals=(algedonic,)
    )
    urgent_signal = build_backpressure_signal_if_needed(urgent)
    assert urgent_signal.signal_kind is BackpressureSignalKind.ALGEDONIC_ACTIVE
    assert urgent_signal.operator_attention_required is True


def test_backpressure_signal_grants_no_authority():
    saturated = _snapshot(queue_depth=3, current_in_flight=1)
    signal = build_backpressure_signal_if_needed(saturated)
    assert signal.grants_authority is False
    assert signal.bypasses_custos is False
    assert signal.executes_recovery is False
    for boundary_field in ("grants_authority", "bypasses_custos", "executes_recovery"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(signal, **{boundary_field: True})
    assert "never retries" in signal.message or "never" in signal.message


def test_backpressure_decision_does_not_retry_recover_or_rollback():
    critical_failure = classify_pre_submit_block("XX", exec_job_id="exec-job-a")
    algedonic = create_algedonic_signal_if_needed(critical_failure)
    critical = _snapshot(
        queue_depth=3, current_in_flight=1, algedonic_signals=(algedonic,)
    )
    decision = decide_backpressure(critical)
    assert decision.decision is BackpressureDecisionKind.ESCALATE
    assert decision.block_new_work is True
    assert decision.requires_operator_attention is True
    for boundary_field in (
        "executes_retry",
        "executes_recovery",
        "executes_rollback",
        "grants_authority",
    ):
        assert getattr(decision, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(decision, **{boundary_field: True})
    for verb in ("retry", "recover", "rollback", "execute", "authorize"):
        assert not hasattr(decision, verb)


def test_backpressure_decision_ladder_is_deterministic():
    assert decide_backpressure(_snapshot()).decision is BackpressureDecisionKind.ALLOW
    # HIGH + no slots -> BLOCK
    saturated = _snapshot(queue_depth=3, current_in_flight=1)
    assert decide_backpressure(saturated).decision is BackpressureDecisionKind.BLOCK
    # HIGH with a free slot -> DELAY with recommendation
    high_with_slot = _snapshot(queue_depth=5, current_in_flight=1, max_in_flight=2)
    if high_with_slot.pressure_level is ExecutionPressureLevel.HIGH:
        delayed = decide_backpressure(high_with_slot)
        assert delayed.decision is BackpressureDecisionKind.DELAY
        assert delayed.recommended_delay_ms == 300
    # ELEVATED + no slots -> HOLD
    elevated_full = _snapshot(current_in_flight=1)
    assert elevated_full.pressure_level is ExecutionPressureLevel.ELEVATED
    assert decide_backpressure(elevated_full).decision is BackpressureDecisionKind.HOLD
    # determinism
    first = decide_backpressure(saturated)
    second = decide_backpressure(saturated)
    assert first == second


def test_decision_flags_must_agree_with_kind():
    decision = decide_backpressure(_snapshot())
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(decision, block_new_work=True)
    hold = decide_backpressure(_snapshot(current_in_flight=1))
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(hold, hold_new_work=False)
