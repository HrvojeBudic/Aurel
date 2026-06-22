"""P1.5.13 Golden Thread A uses normalized verifier results."""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.verifier import VerifierKind
from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness


def test_golden_thread_a_uses_normalized_verifier_result():
    """Golden Thread A must pass and use normalized VerifierResult via normalization layer."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    # Core assertion: Golden Thread A passes
    assert result.passed, f"Golden Thread A failed with errors: {result.errors}"

    # Normalization report exists and is normalized
    assert harness.normalization_report is not None, "Normalization report must exist"
    assert harness.normalization_report.normalization_status.value == "normalized"

    # VerifierResult is normalized
    assert result.verifier_kind == "evidence_integrity"
    assert result.normalization_report_id is not None
    assert result.normalization_status == "normalized"

    # VerifierResult has all required fields
    verifier = harness.verifier_result
    assert verifier is not None
    assert verifier.verifier_kind == VerifierKind.EVIDENCE_INTEGRITY
    assert len(verifier.limitations) > 0
    assert len(verifier.evidence_refs) > 0
    assert verifier.source_trace_event_ref is not None

    # CapabilityEvidenceRecord uses normalized VerifierResult
    assert harness.capability_evidence is not None
    assert harness.capability_evidence.verifier_result_ref == verifier.verifier_id

    # P1.5.12 EvaluationCase extraction still works
    assert result.evaluation_case_id is not None, "Evaluation case must be extracted"
    assert result.evaluation_case_kind == "positive"
    assert result.evaluation_case_status == "candidate"


def test_golden_thread_a_result_has_all_normalization_fields():
    """GoldenThreadAResult must include the new verifier_kind and normalization fields."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    # Check all new fields are populated
    assert result.verifier_kind is not None
    assert result.verifier_kind == "evidence_integrity"
    assert result.normalization_report_id is not None
    assert result.normalization_status is not None
    assert result.normalization_status == "normalized"
    assert result.evaluation_case_id is not None
    assert result.evaluation_case_status == "candidate"
