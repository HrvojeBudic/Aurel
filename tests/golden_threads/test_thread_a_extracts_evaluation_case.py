"""P1.5.12 Golden Thread A candidate evaluation case extraction tests."""
from __future__ import annotations

from agentic_runtime.contracts.capability import CapabilityEvidenceStatus, EvidenceStrengthLevel
from agentic_runtime.contracts.context import ContextAdequacyStatus
from agentic_runtime.contracts.trace import TraceEventType
from agentic_runtime.contracts.verifier import VerifierResultStatus
from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness


def test_golden_thread_a_extracts_positive_evaluation_case():
    """Golden Thread A produces a positive candidate EvaluationCase."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.passed is True
    assert result.errors == ()

    # Existing P1.5.11A/B invariants still hold
    event = harness.trace_log.get_event(result.trace_event_ref.event_id)
    assert event.event_type == TraceEventType.STUB_EXECUTION_COMPLETED
    chain_report = harness.trace_log.verify_chain(result.trace_event_ref.trace_id)
    assert chain_report.is_valid is True

    assert harness.capability_evidence is not None
    assert harness.capability_evidence.status == CapabilityEvidenceStatus.VERIFIED
    assert harness.verifier_result is not None
    assert harness.verifier_result.status == VerifierResultStatus.PASS
    assert harness.context_adequacy_report is not None
    assert harness.context_adequacy_report.status == ContextAdequacyStatus.ADEQUATE

    # P1.5.12 extraction
    assert result.evaluation_case_id is not None, "expected a positive EvaluationCase"
    assert result.evaluation_case_kind == "positive"
    assert result.evaluation_case_status == "candidate"
    assert result.extraction_report_id is not None
    assert result.extraction_status == "extracted"

    # Trace binding preserved
    assert result.source_event_hash == result.trace_event_ref.event_hash

    # Candidate-only: nothing auto-promoted
    assert result.evaluation_case_status != "accepted"
    assert result.regression_candidate_id is None


def test_golden_thread_a_result_has_extraction_fields():
    """GoldenThreadAResult includes P1.5.12 extraction fields with defaults."""
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert hasattr(result, "evaluation_case_id")
    assert hasattr(result, "regression_candidate_id")
    assert hasattr(result, "extraction_report_id")
    assert hasattr(result, "evaluation_case_kind")
    assert hasattr(result, "evaluation_case_status")
    assert hasattr(result, "extraction_status")
