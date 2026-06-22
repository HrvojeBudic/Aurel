"""P1.5.17 Operator Feedback Capture tests.

Verifies OperatorFeedbackRecord validation, target ref invariants,
and trace binding requirements.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.operator_feedback import (
    FeedbackSignalStrength,
    OperatorFeedbackRecord,
    OperatorFeedbackSentiment,
    OperatorFeedbackTargetRef,
    OperatorFeedbackTargetType,
    OperatorFeedbackType,
    derive_signal_strength,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventStatus,
    TraceEventType,
    trace_event_ref,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_ref() -> "trace_event_ref":
    log = AurelTraceLog(trace_id="trace_fb_cap_001")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="fb_cap",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_target(trace_ref=None, trace_hash=None) -> OperatorFeedbackTargetRef:
    return OperatorFeedbackTargetRef(
        target_id="claim_001",
        target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_hash,
    )


def _make_feedback(
    fb_type=OperatorFeedbackType.APPROVAL,
    sentiment=OperatorFeedbackSentiment.POSITIVE,
    target=None,
    actor_id="op",
    raw_text="Looks good.",
    limitations=("Test limitation.",),
    trace_ref=None,
) -> OperatorFeedbackRecord:
    return OperatorFeedbackRecord(
        feedback_id="fb_001",
        feedback_type=fb_type,
        sentiment=sentiment,
        target_ref=target or _make_target(),
        actor_id=actor_id,
        raw_text=raw_text,
        limitations=limitations,
        source_trace_event_ref=trace_ref,
        created_at=_TIMESTAMP,
    )


class TestOperatorFeedbackRequires:
    """Validation: required fields enforced."""

    def test_operator_feedback_requires_target_ref(self) -> None:
        with pytest.raises(ValueError):
            OperatorFeedbackRecord(
                feedback_id="fb_001",
                feedback_type=OperatorFeedbackType.APPROVAL,
                sentiment=OperatorFeedbackSentiment.POSITIVE,
                target_ref=None,  # type: ignore
                actor_id="op",
                raw_text="test",
                limitations=("limit",),
                created_at=_TIMESTAMP,
            )

    def test_operator_feedback_requires_actor_id(self) -> None:
        with pytest.raises(ValueError):
            _make_feedback(actor_id="")

    def test_operator_feedback_requires_limitations(self) -> None:
        with pytest.raises(ValueError):
            _make_feedback(limitations=())

    def test_operator_feedback_requires_some_content(self) -> None:
        with pytest.raises(ValueError):
            OperatorFeedbackRecord(
                feedback_id="fb_002",
                feedback_type=OperatorFeedbackType.APPROVAL,
                sentiment=OperatorFeedbackSentiment.POSITIVE,
                target_ref=_make_target(),
                actor_id="op",
                limitations=("limit",),
                created_at=_TIMESTAMP,
            )

    def test_target_id_required(self) -> None:
        with pytest.raises(ValueError):
            OperatorFeedbackTargetRef(
                target_id="",
                target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
            )

    def test_rating_range(self) -> None:
        with pytest.raises(ValueError):
            _make_feedback(
                fb_type=OperatorFeedbackType.RATING,
                raw_text=None,
            )  # missing content

        with pytest.raises(ValueError):
            OperatorFeedbackRecord(
                feedback_id="fb_003",
                feedback_type=OperatorFeedbackType.RATING,
                sentiment=OperatorFeedbackSentiment.NEUTRAL,
                target_ref=_make_target(),
                actor_id="op",
                rating=11,
                limitations=("limit",),
                created_at=_TIMESTAMP,
            )

    def test_salience_range(self) -> None:
        with pytest.raises(ValueError):
            OperatorFeedbackRecord(
                feedback_id="fb_004",
                feedback_type=OperatorFeedbackType.APPROVAL,
                sentiment=OperatorFeedbackSentiment.POSITIVE,
                target_ref=_make_target(),
                actor_id="op",
                raw_text="ok",
                salience=1.5,
                limitations=("limit",),
                created_at=_TIMESTAMP,
            )


class TestTargetRefInvariants:
    """OperatorFeedbackTargetRef invariants."""

    def test_target_ref_hash_must_match_when_both_present(self) -> None:
        trace_ref = _make_trace_ref()
        with pytest.raises(ValueError, match="source_event_hash must match"):
            OperatorFeedbackTargetRef(
                target_id="claim_001",
                target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
                source_trace_event_ref=trace_ref,
                source_event_hash="wrong_hash",
            )

    def test_target_ref_accepts_trace_ref_only(self) -> None:
        trace_ref = _make_trace_ref()
        target = OperatorFeedbackTargetRef(
            target_id="claim_001",
            target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
            source_trace_event_ref=trace_ref,
        )
        assert target.target_id == "claim_001"

    def test_target_ref_accepts_hash_only(self) -> None:
        target = OperatorFeedbackTargetRef(
            target_id="claim_001",
            target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
            source_event_hash="some_hash",
        )
        assert target.source_event_hash == "some_hash"


class TestTraceBinding:
    """Serious feedback should preserve trace binding when available."""

    def test_serious_feedback_preserves_trace_ref_when_available(self) -> None:
        trace_ref = _make_trace_ref()
        target = _make_target(trace_ref=trace_ref, trace_hash=trace_ref.event_hash)
        fb = _make_feedback(target=target, trace_ref=trace_ref)
        assert fb.source_trace_event_ref is not None
        assert fb.source_trace_event_ref.event_hash == trace_ref.event_hash

    def test_projection_only_feedback_derives_weak_or_moderate_signal(self) -> None:
        # No trace ref on target, no trace ref on feedback → projection-only
        target = OperatorFeedbackTargetRef(
            target_id="claim_001",
            target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
        )
        fb = OperatorFeedbackRecord(
            feedback_id="fb_proj",
            feedback_type=OperatorFeedbackType.APPROVAL,
            sentiment=OperatorFeedbackSentiment.POSITIVE,
            target_ref=target,
            actor_id="op",
            raw_text="looks good from projection",
            limitations=("Projection-only.",),
            created_at=_TIMESTAMP,
        )
        strength = derive_signal_strength(fb)
        assert strength in (FeedbackSignalStrength.WEAK, FeedbackSignalStrength.MODERATE)


class TestSignalStrengthDerivation:
    """Derive signal strength deterministically."""

    def test_safety_concern_is_blocking(self) -> None:
        fb = _make_feedback(fb_type=OperatorFeedbackType.SAFETY_CONCERN)
        assert derive_signal_strength(fb) == FeedbackSignalStrength.BLOCKING

    def test_policy_concern_is_blocking(self) -> None:
        fb = _make_feedback(fb_type=OperatorFeedbackType.POLICY_CONCERN)
        assert derive_signal_strength(fb) == FeedbackSignalStrength.BLOCKING

    def test_correction_is_strong(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.CORRECTION,
            raw_text="This is wrong, should be X.",
        )
        assert derive_signal_strength(fb) == FeedbackSignalStrength.STRONG

    def test_trace_bound_approval_is_strong(self) -> None:
        trace_ref = _make_trace_ref()
        target = _make_target(trace_ref=trace_ref, trace_hash=trace_ref.event_hash)
        fb = _make_feedback(target=target, trace_ref=trace_ref)
        assert derive_signal_strength(fb) == FeedbackSignalStrength.STRONG

    def test_projection_only_approval_is_moderate(self) -> None:
        target = OperatorFeedbackTargetRef(
            target_id="claim_001",
            target_type=OperatorFeedbackTargetType.CAPABILITY_CLAIM,
        )
        fb = _make_feedback(target=target)
        assert derive_signal_strength(fb) == FeedbackSignalStrength.MODERATE

    def test_memory_candidate_is_weak(self) -> None:
        fb = _make_feedback(
            fb_type=OperatorFeedbackType.MEMORY_CANDIDATE,
            raw_text="Remember this.",
        )
        assert derive_signal_strength(fb) == FeedbackSignalStrength.WEAK


class TestSerialization:
    """Serialization helpers work correctly."""

    def test_feedback_record_to_dict(self) -> None:
        from agentic_runtime.contracts.operator_feedback import (
            operator_feedback_record_to_dict,
        )
        fb = _make_feedback()
        d = operator_feedback_record_to_dict(fb)
        assert d["feedback_id"] == "fb_001"
        assert d["feedback_type"] == "approval"
        assert d["sentiment"] == "positive"
        assert d["actor_id"] == "op"
        assert d["raw_text"] == "Looks good."

    def test_target_ref_to_dict(self) -> None:
        from agentic_runtime.contracts.operator_feedback import (
            operator_feedback_target_ref_to_dict,
        )
        target = _make_target()
        d = operator_feedback_target_ref_to_dict(target)
        assert d["target_id"] == "claim_001"
        assert d["target_type"] == "capability_claim"

    def test_feedback_report_to_dict(self) -> None:
        from agentic_runtime.contracts.operator_feedback import (
            FeedbackProcessingReport,
            FeedbackSignalStrength,
            feedback_processing_report_to_dict,
        )
        report = FeedbackProcessingReport(
            report_id="r_001",
            feedback_id="fb_001",
            target_ref=_make_target(),
            signal_strength=FeedbackSignalStrength.STRONG,
            candidate_actions=(),
            created_candidates=(),
            blocked_actions=(),
            reason="Test.",
            created_at=_TIMESTAMP,
        )
        d = feedback_processing_report_to_dict(report)
        assert d["signal_strength"] == "strong"
