"""P5.16 — Replay-readiness / time-slice refs (readiness is NOT replay)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    ReplayReadinessAssessment,
    ReplayReadinessStatus,
    TraceTimeSliceRef,
    assess_replay_readiness,
    build_trace_time_slice_ref,
)

_REQUIRED = (
    "trace_run_ref",
    "chain_head_hash",
    "event_range",
    "canonical_event_refs",
    "evidence_refs",
    "verification_decisions",
    "schema_compatibility",
)


def _slice():
    return build_trace_time_slice_ref(
        start_ref="evt-0", end_ref="evt-3", start_index=0, end_index=3
    )


def test_time_slice_ref_is_stable():
    a = _slice()
    b = _slice()
    assert a.time_slice_ref_id == b.time_slice_ref_id


def test_inverted_range_fails_closed():
    with pytest.raises(AurelTraceError):
        build_trace_time_slice_ref(
            start_ref="evt-3", end_ref="evt-0", start_index=3, end_index=0
        )


def test_time_slice_ref_is_not_replay_or_restore():
    ref = _slice()
    assert ref.is_replay is False
    assert ref.is_snapshot is False
    assert ref.is_state_restore is False
    assert ref.is_fork is False
    for bad in ("is_replay", "is_snapshot", "is_state_restore", "is_fork"):
        with pytest.raises(AurelTraceError):
            TraceTimeSliceRef(
                time_slice_ref_id="t",
                start_ref="a",
                end_ref="b",
                **{bad: True},
            )


def test_full_inputs_ready_for_analysis_but_replay_unavailable():
    assessment = assess_replay_readiness(
        time_slice_ref=_slice(), required_inputs=_REQUIRED, present_inputs=_REQUIRED
    )
    assert assessment.status is ReplayReadinessStatus.READY_FOR_ANALYSIS
    # READY_FOR_ANALYSIS still does not mean replay is implemented.
    assert assessment.replay_implemented is False
    assert assessment.supports_fork is False
    assert assessment.supports_state_restore is False
    assert "not implemented" in assessment.unavailable_reason


def test_some_missing_inputs_is_partial():
    assessment = assess_replay_readiness(
        time_slice_ref=_slice(),
        required_inputs=_REQUIRED,
        present_inputs=_REQUIRED[:3],
    )
    assert assessment.status is ReplayReadinessStatus.PARTIAL
    assert len(assessment.missing_inputs) == 4


def test_no_present_inputs_is_missing_required_data():
    assessment = assess_replay_readiness(
        time_slice_ref=_slice(), required_inputs=_REQUIRED, present_inputs=()
    )
    assert assessment.status is ReplayReadinessStatus.MISSING_REQUIRED_DATA


def test_unsupported_input_key():
    assessment = assess_replay_readiness(
        time_slice_ref=_slice(),
        required_inputs=("bogus_input",),
        present_inputs=(),
    )
    assert assessment.status is ReplayReadinessStatus.UNSUPPORTED
    assert "bogus_input" in assessment.unsupported_inputs


def test_assessment_cannot_claim_replay():
    with pytest.raises(AurelTraceError):
        ReplayReadinessAssessment(
            assessment_id="a",
            time_slice_ref=_slice(),
            status=ReplayReadinessStatus.READY_FOR_ANALYSIS,
            required_inputs=_REQUIRED,
            present_inputs=_REQUIRED,
            replay_implemented=True,
        )
