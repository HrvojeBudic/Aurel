"""P1.5.14 Evaluation Runtime invariants (contract validation).

Validates that all 5 new contracts reject invalid states and that
serialization round-trips correctly. Also validates anti-promotion structure.
"""
from __future__ import annotations

import json

import pytest as pytest

from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationEvent,
    EvaluationEventKind,
    EvaluationMode,
    EvaluationRequest,
    EvaluationRun,
    EvaluationRunResult,
    EvaluationRunStatus,
    EvaluationTargetRef,
    EvaluationTargetType,
    evaluation_event_to_dict,
    evaluation_request_to_dict,
    evaluation_run_result_to_dict,
    evaluation_run_to_dict,
    evaluation_target_ref_to_dict,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventRef,
    TraceEventStatus,
    TraceEventType,
    trace_event_ref,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_valid_target_ref(trace_log: AurelTraceLog | None = None) -> tuple[TraceEventRef, EvaluationTargetRef]:
    if trace_log is None:
        trace_log = AurelTraceLog(trace_id="trace_p1_5_14_inv_001")
    event = trace_log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test_inv",
        actor_id="p1_5_14_inv",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    ref = trace_event_ref(event)
    target = EvaluationTargetRef(
        target_id="target_inv_001",
        target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
        source_trace_event_ref=ref,
        source_event_hash=ref.event_hash,
        evidence_refs=("ev_001",),
        created_at=_TIMESTAMP,
    )
    return ref, target


# ---------------------------------------------------------------------------
# EvaluationTargetRef invariants
# ---------------------------------------------------------------------------

class TestEvaluationTargetRefInvariants:
    def test_empty_target_id_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_002")
        ref, _ = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="target_id must not be empty"):
            EvaluationTargetRef(
                target_id="",
                target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
                source_trace_event_ref=ref,
                source_event_hash=ref.event_hash,
                evidence_refs=("ev_001",),
                created_at=_TIMESTAMP,
            )

    def test_whitespace_target_id_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_003")
        ref, _ = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="target_id must not be empty"):
            EvaluationTargetRef(
                target_id="   ",
                target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
                source_trace_event_ref=ref,
                source_event_hash=ref.event_hash,
                evidence_refs=("ev_001",),
                created_at=_TIMESTAMP,
            )

    def test_mismatched_hash_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_004")
        ref, _ = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="source_event_hash must match"):
            EvaluationTargetRef(
                target_id="t_001",
                target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
                source_trace_event_ref=ref,
                source_event_hash="wrong_hash",
                evidence_refs=("ev_001",),
                created_at=_TIMESTAMP,
            )

    def test_empty_created_at_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_005")
        ref, _ = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="created_at must not be empty"):
            EvaluationTargetRef(
                target_id="t_001",
                target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
                source_trace_event_ref=ref,
                source_event_hash=ref.event_hash,
                evidence_refs=("ev_001",),
                created_at="",
            )

    def test_missing_source_event_hash_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_005b")
        ref, _ = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="source_event_hash must not be empty"):
            EvaluationTargetRef(
                target_id="t_001",
                target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
                source_trace_event_ref=ref,
                source_event_hash="",
                evidence_refs=("ev_001",),
                created_at=_TIMESTAMP,
            )


# ---------------------------------------------------------------------------
# EvaluationRequest invariants
# ---------------------------------------------------------------------------

class TestEvaluationRequestInvariants:
    def test_empty_request_id_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_006")
        ref, target = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="request_id must not be empty"):
            EvaluationRequest(
                request_id="",
                target_ref=target,
                requested_by="tester",
                reason="Test.",
                evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
                created_at=_TIMESTAMP,
            )

    def test_empty_requested_by_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_007")
        ref, target = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="requested_by must not be empty"):
            EvaluationRequest(
                request_id="r1",
                target_ref=target,
                requested_by="",
                reason="Test.",
                evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
                created_at=_TIMESTAMP,
            )

    def test_empty_reason_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_008")
        ref, target = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="reason must not be empty"):
            EvaluationRequest(
                request_id="r1",
                target_ref=target,
                requested_by="tester",
                reason="",
                evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
                created_at=_TIMESTAMP,
            )


# ---------------------------------------------------------------------------
# EvaluationRun invariants
# ---------------------------------------------------------------------------

class TestEvaluationRunInvariants:
    def test_terminal_status_requires_completed_at(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_009")
        ref, target = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="completed_at is required"):
            EvaluationRun(
                run_id="run_1",
                request_id="req_1",
                target_ref=target,
                status=EvaluationRunStatus.PASSED,
                started_at=_TIMESTAMP,
            )

    def test_completed_at_requires_terminal_status(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_010")
        ref, target = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="completed_at may only be set"):
            EvaluationRun(
                run_id="run_1",
                request_id="req_1",
                target_ref=target,
                status=EvaluationRunStatus.RUNNING,
                started_at=_TIMESTAMP,
                completed_at=_TIMESTAMP,
            )

    def test_empty_run_id_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_011")
        ref, target = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="run_id must not be empty"):
            EvaluationRun(
                run_id="",
                request_id="req_1",
                target_ref=target,
                status=EvaluationRunStatus.PASSED,
                started_at=_TIMESTAMP,
                completed_at=_TIMESTAMP,
            )


# ---------------------------------------------------------------------------
# EvaluationEvent invariants
# ---------------------------------------------------------------------------

class TestEvaluationEventInvariants:
    def test_empty_event_id_raises(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_012")
        ref, _ = _make_valid_target_ref(trace_log)
        with pytest.raises(ValueError, match="evaluation_event_id must not be empty"):
            EvaluationEvent(
                evaluation_event_id="",
                run_id="r1",
                request_id="rq1",
                event_kind=EvaluationEventKind.EVALUATION_STARTED,
                source_trace_event_ref=ref,
                created_at=_TIMESTAMP,
            )


# ---------------------------------------------------------------------------
# EvaluationRunResult invariants
# ---------------------------------------------------------------------------

class TestEvaluationRunResultInvariants:
    def test_non_terminal_status_raises(self) -> None:
        with pytest.raises(ValueError, match="must be terminal"):
            EvaluationRunResult(
                run_id="r1",
                request_id="rq1",
                status=EvaluationRunStatus.RUNNING,
                summary="test",
                limitations=("lim1",),
                completed_at=_TIMESTAMP,
            )

    def test_empty_limitations_raises(self) -> None:
        with pytest.raises(ValueError, match="limitations must be non-empty"):
            EvaluationRunResult(
                run_id="r1",
                request_id="rq1",
                status=EvaluationRunStatus.PASSED,
                summary="test",
                limitations=(),
                completed_at=_TIMESTAMP,
            )

    def test_failed_without_errors_raises(self) -> None:
        with pytest.raises(ValueError, match="errors must be non-empty"):
            EvaluationRunResult(
                run_id="r1",
                request_id="rq1",
                status=EvaluationRunStatus.FAILED,
                summary="test",
                limitations=("lim1",),
                errors=(),
                completed_at=_TIMESTAMP,
            )

    def test_empty_completed_at_raises(self) -> None:
        with pytest.raises(ValueError, match="completed_at must not be empty"):
            EvaluationRunResult(
                run_id="r1",
                request_id="rq1",
                status=EvaluationRunStatus.PASSED,
                summary="test",
                limitations=("lim1",),
                completed_at="",
            )


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerializationRoundTrip:
    def test_target_ref_round_trips_through_json(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_020")
        ref, target = _make_valid_target_ref(trace_log)
        d = evaluation_target_ref_to_dict(target)
        json_str = json.dumps(d, default=str)
        parsed = json.loads(json_str)
        assert parsed["target_id"] == target.target_id
        assert parsed["target_type"] == target.target_type.value
        assert parsed["source_event_hash"] == target.source_event_hash

    def test_request_round_trips_through_json(self) -> None:
        trace_log = AurelTraceLog(trace_id="trace_inv_021")
        ref, target = _make_valid_target_ref(trace_log)
        req = EvaluationRequest(
            request_id="req_ser",
            target_ref=target,
            requested_by="tester",
            reason="Serialization test.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            required_verifier_kinds=("deterministic",),
            created_at=_TIMESTAMP,
        )
        d = evaluation_request_to_dict(req)
        json_str = json.dumps(d, default=str)
        parsed = json.loads(json_str)
        assert parsed["request_id"] == req.request_id
        assert parsed["evaluation_mode"] == req.evaluation_mode.value

    def test_result_round_trips_through_json(self) -> None:
        result = EvaluationRunResult(
            run_id="run_ser",
            request_id="req_ser",
            status=EvaluationRunStatus.PASSED,
            summary="Serialization test.",
            limitations=("lim1", "lim2"),
            errors=(),
            warnings=("warn1",),
            completed_at=_TIMESTAMP,
        )
        d = evaluation_run_result_to_dict(result)
        json_str = json.dumps(d, default=str)
        parsed = json.loads(json_str)
        assert parsed["status"] == "passed"
        assert "lim1" in parsed["limitations"]


# ---------------------------------------------------------------------------
# Anti-promotion structural invariants
# ---------------------------------------------------------------------------

class TestAntiPromotionStructure:
    """None of the 5 contracts expose promotion/mutation fields."""

    _DISALLOWED = {"capability_promoted", "memory_written", "skill_created",
                    "reflex_created", "policy_changed", "promote_capability",
                    "mutate_policy", "commit_memory"}

    def test_target_ref_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationTargetRef.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_request_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationRequest.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_run_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationRun.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_event_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationEvent.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_result_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationRunResult.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)
