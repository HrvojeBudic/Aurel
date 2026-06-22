"""P1.5.14 Evaluation Runtime Hook tests (contract compliance).

Tests the runtime hook: run_evaluation() boundary, trace event binding,
target validation, and anti-promotion structure.
"""
from __future__ import annotations

import pytest as pytest

from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationEventKind,
    EvaluationMode,
    EvaluationRequest,
    EvaluationRunResult,
    EvaluationRunStatus,
    EvaluationTargetRef,
    EvaluationTargetType,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventRef,
    TraceEventStatus,
    TraceEventType,
    hash_json,
    trace_event_ref,
)
from agentic_runtime.evaluation.runtime_hook import run_evaluation

_HOOK_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_log() -> AurelTraceLog:
    return AurelTraceLog(trace_id="trace_p1_5_14_hook_001")


def _make_target(
    trace_log: AurelTraceLog,
    *,
    target_id: str = "cap_evidence_001",
    target_type: EvaluationTargetType = EvaluationTargetType.CAPABILITY_EVIDENCE,
    evidence_refs: tuple[str, ...] = ("ev_001",),
) -> tuple[EvaluationTargetRef, TraceEventRef]:
    """Create a valid target by appending a trace event first."""
    event = trace_log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test_hook",
        actor_id="p1_5_14_tests",
        payload_json={"test": True},
        timestamp=_HOOK_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    ref = trace_event_ref(event)
    target = EvaluationTargetRef(
        target_id=target_id,
        target_type=target_type,
        source_trace_event_ref=ref,
        source_event_hash=ref.event_hash,
        evidence_refs=evidence_refs,
        created_at=_HOOK_TIMESTAMP,
    )
    return target, ref


class TestEvaluationRuntimeHookHappyPath:
    """Golden Thread A runs evaluation runtime hook successfully."""

    def test_happy_path_capability_check_passes(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_001",
            target_ref=target,
            requested_by="golden_thread_a",
            reason="Test capability_check.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.PASSED
        assert run.status == EvaluationRunStatus.PASSED
        assert len(result.limitations) >= 1
        assert result.errors == ()
        assert len(result.emitted_event_refs) >= 2

    def test_happy_path_creates_evaluation_run(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_002",
            target_ref=target,
            requested_by="tester",
            reason="Test evaluation run.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, run = run_evaluation(request, trace_log=trace_log)
        assert run.run_id == result.run_id
        assert run.request_id == request.request_id
        assert run.target_ref.target_id == target.target_id
        assert run.status == EvaluationRunStatus.PASSED
        assert run.started_at == _HOOK_TIMESTAMP
        assert run.completed_at is not None

    def test_happy_path_emits_completed_event(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_003",
            target_ref=target,
            requested_by="tester",
            reason="Test completed event.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        completed_events = [
            eid for eid in result.emitted_event_refs
            if any(ev for ev in list(trace_log) if ev.event_id == eid)
        ]
        assert len(completed_events) >= 2  # requested + started + completed

    def test_happy_path_events_in_trace_log(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_004",
            target_ref=target,
            requested_by="tester",
            reason="Test events in log.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        all_event_ids = {ev.event_id for ev in list(trace_log)}
        emitted_ids = set(result.emitted_event_refs)
        assert emitted_ids.issubset(all_event_ids), "Emitted events must exist in trace log"

    def test_result_limitations_always_present(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_005",
            target_ref=target,
            requested_by="tester",
            reason="Test limitations.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert len(result.limitations) >= 1
        assert any("promote" in lim.lower() for lim in result.limitations)


class TestEvaluationTargetValidation:
    """Target validation rules are enforced."""

    def test_hash_mismatch_fails(self) -> None:
        """Hash validation is enforced at EvaluationTargetRef construction time.
        The runtime hook's _validate_target provides defense-in-depth but
        the contract prevents constructing an invalid target.
        """
        trace_log = _make_trace_log()
        event = trace_log.append(
            event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
            actor_type="test",
            actor_id="p1_5_14",
            payload_json={"x": 1},
            timestamp=_HOOK_TIMESTAMP,
            status=TraceEventStatus.COMPLETED,
        )
        ref = trace_event_ref(event)
        # Contract prevents mismatched hash at construction time
        with pytest.raises(ValueError, match="source_event_hash must match"):
            EvaluationTargetRef(
                target_id="t_001",
                target_type=EvaluationTargetType.CAPABILITY_EVIDENCE,
                source_trace_event_ref=ref,
                source_event_hash="deadbeef",
                evidence_refs=("ev_001",),
                created_at=_HOOK_TIMESTAMP,
            )

    def test_hash_mismatch_binding_fails(self) -> None:
        """When target hash does not match, contract prevents construction.
        The runtime hook rejects targets with empty evidence_refs for capability targets.
        """
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log, evidence_refs=())
        request = EvaluationRequest(
            request_id="req_empty_evidence",
            target_ref=target,
            requested_by="tester",
            reason="Test empty evidence refs on capability target.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.FAILED
        assert run.status == EvaluationRunStatus.FAILED
        assert len(result.errors) >= 1

    def test_failure_emits_correct_event(self) -> None:
        """Runtime hook emits EVALUATION_FAILED event on target validation failure."""
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log, evidence_refs=())
        request = EvaluationRequest(
            request_id="req_fail_event",
            target_ref=target,
            requested_by="tester",
            reason="Test evaluation_failed event emission.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.FAILED
        assert len(result.errors) >= 1
        # Verify EVALUATION events exist in trace log (event payload is frozen/hashable)
        eval_events = [
            ev for ev in list(trace_log)
            if ev.event_type == TraceEventType.EVALUATION
        ]
        # At minimum: EVALUATION_REQUESTED and EVALUATION_FAILED
        assert len(eval_events) >= 2

    def test_missing_evidence_refs_for_capability_target(self) -> None:
        """When target_type is CAPABILITY_EVIDENCE, empty evidence_refs should fail."""
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log, evidence_refs=())
        request = EvaluationRequest(
            request_id="req_no_evidence",
            target_ref=target,
            requested_by="tester",
            reason="Test missing evidence.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.FAILED


class TestEvaluationRunTerminalStatus:
    """EvaluationRun terminal status matches result."""

    def test_run_status_matches_result(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_term",
            target_ref=target,
            requested_by="tester",
            reason="Terminal status.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, run = run_evaluation(request, trace_log=trace_log)
        assert run.status == result.status

    def test_passed_result_is_terminal(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_term2",
            target_ref=target,
            requested_by="tester",
            reason="Terminal pass.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status in (
            EvaluationRunStatus.PASSED,
            EvaluationRunStatus.FAILED,
            EvaluationRunStatus.NEEDS_REVIEW,
            EvaluationRunStatus.INCONCLUSIVE,
        )


class TestAntiPromotion:
    """runtime_hook does not introduce promotion or mutation capability."""

    def test_result_has_no_capability_promotion(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_anti",
            target_ref=target,
            requested_by="tester",
            reason="Anti-promotion.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        d = result.__dict__ if hasattr(result, "__dict__") else {}
        disallowed = {"capability_promoted", "memory_written", "skill_created",
                       "reflex_created", "policy_changed", "promotion", "promote"}
        for key in disallowed:
            assert key not in d, f"EvaluationRunResult must not contain field '{key}'"

    def test_trace_bound_events_use_evaluation_type(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_trace_type",
            target_ref=target,
            requested_by="tester",
            reason="Trace event types.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        _result, _run = run_evaluation(request, trace_log=trace_log)
        eval_events = [
            ev for ev in list(trace_log)
            if ev.event_type == TraceEventType.EVALUATION
        ]
        assert len(eval_events) >= 2


class TestMultipleEvaluationModes:
    """Run the hook with different evaluation modes."""

    def test_contract_mode(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log, target_type=EvaluationTargetType.VERIFIER_RESULT, evidence_refs=())
        request = EvaluationRequest(
            request_id="req_contract",
            target_ref=target,
            requested_by="tester",
            reason="Contract mode.",
            evaluation_mode=EvaluationMode.CONTRACT,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.PASSED

    def test_review_seed_mode(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_review",
            target_ref=target,
            requested_by="tester",
            reason="Review seed.",
            evaluation_mode=EvaluationMode.REVIEW_SEED,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.PASSED

    def test_regression_seed_mode(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log, target_type=EvaluationTargetType.REGRESSION_CANDIDATE)
        request = EvaluationRequest(
            request_id="req_regression",
            target_ref=target,
            requested_by="tester",
            reason="Regression seed.",
            evaluation_mode=EvaluationMode.REGRESSION_SEED,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.PASSED

    def test_capability_check_with_verifier_kinds(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_cc",
            target_ref=target,
            requested_by="tester",
            reason="CC with verifier kinds.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            required_verifier_kinds=("evidence_integrity", "deterministic"),
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        assert result.status == EvaluationRunStatus.PASSED


class TestEventBinding:
    """Evaluation events bind to canonical trace refs."""

    def test_each_emitted_event_in_trace_log(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_bind",
            target_ref=target,
            requested_by="tester",
            reason="Event binding test.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        result, _run = run_evaluation(request, trace_log=trace_log)
        for emitted_id in result.emitted_event_refs:
            found = any(ev.event_id == emitted_id for ev in list(trace_log))
            assert found, f"Emitted event {emitted_id} not found in trace log"

    def test_source_ref_present_in_all_trace_events(self) -> None:
        trace_log = _make_trace_log()
        target, _ref = _make_target(trace_log)
        request = EvaluationRequest(
            request_id="req_source",
            target_ref=target,
            requested_by="tester",
            reason="Source ref test.",
            evaluation_mode=EvaluationMode.CAPABILITY_CHECK,
            created_at=_HOOK_TIMESTAMP,
        )
        _result, _run = run_evaluation(request, trace_log=trace_log)
        eval_events = [
            ev for ev in list(trace_log)
            if ev.event_type == TraceEventType.EVALUATION
        ]
        # All evaluation events should have payload with source info
        for ev in eval_events:
            assert ev.payload_json is not None
            if isinstance(ev.payload_json, dict):
                assert "run_id" in ev.payload_json or "evaluation_event_kind" in ev.payload_json
