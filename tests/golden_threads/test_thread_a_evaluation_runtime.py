"""P1.5.14 Golden Thread A evaluation runtime tests.

Verifies that GoldenThreadAHarness.run_demo() now produces evaluation
runtime result fields and that P1.5.12 extraction and P1.5.13 normalization
still work.
"""
from __future__ import annotations

import pytest as pytest

from agentic_runtime.contracts.evaluation_runtime import EvaluationRunStatus
from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness


class TestGoldenThreadAEvaluationRuntime:
    """Golden Thread A integration with P1.5.14 evaluation runtime hook."""

    def test_gta_produces_evaluation_runtime_result(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        assert result.evaluation_request_id is not None
        assert result.evaluation_run_id is not None
        assert result.evaluation_run_status is not None
        assert result.evaluation_result_status is not None
        assert len(result.evaluation_event_refs) >= 2

    def test_gta_evaluation_result_is_passed(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        assert result.evaluation_result_status == EvaluationRunStatus.PASSED.value
        assert result.evaluation_run_status == EvaluationRunStatus.PASSED.value

    def test_p1512_extraction_still_works(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        assert result.evaluation_case_id is not None, "P1.5.12 extraction must still work"
        assert result.evaluation_case_kind is not None
        assert result.extraction_report_id is not None

    def test_p1513_normalization_still_works(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        assert result.verifier_kind is not None, "P1.5.13 normalization must still work"
        assert result.normalization_report_id is not None
        assert result.normalization_status is not None

    def test_gta_harness_stores_evaluation_instances(self) -> None:
        harness = GoldenThreadAHarness()
        _result = harness.run_demo()
        assert harness.evaluation_run_result is not None
        assert harness.evaluation_run is not None
        assert harness.evaluation_run_result.status == EvaluationRunStatus.PASSED
        assert harness.evaluation_run.status == EvaluationRunStatus.PASSED

    def test_gta_evaluation_events_in_trace_log(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        all_event_ids = {ev.event_id for ev in list(harness.trace_log)}
        emitted_ids = set(result.evaluation_event_refs)
        assert emitted_ids.issubset(all_event_ids), "All evaluation events must exist in trace log"
        # At minimum: evaluation_requested, evaluation_started, evaluation_target_validated,
        # evaluation_completed, plus the original stub execution event
        assert len(emitted_ids) >= 3
