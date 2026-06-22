"""P1.5.11A/B Golden Thread A vertical contract tests."""
from __future__ import annotations

from agentic_runtime.contracts.capability import CapabilityEvidenceStatus, EvidenceStrengthLevel
from agentic_runtime.contracts.context import ContextAdequacyStatus
from agentic_runtime.contracts.trace import TraceEventType, trace_event_to_dict
from agentic_runtime.contracts.verifier import VerifierResultStatus
from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness


def test_golden_thread_a_runs_end_to_end():
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.passed is True
    assert result.errors == ()

    event = harness.trace_log.get_event(result.trace_event_ref.event_id)
    assert event.event_type == TraceEventType.STUB_EXECUTION_COMPLETED
    assert event.event_hash == result.trace_event_ref.event_hash
    assert event.trace_id == result.trace_event_ref.trace_id
    assert trace_event_to_dict(event)["payload_json"]["execution_id"] == result.execution_id
    assert result.source_event_hash == result.trace_event_ref.event_hash

    chain_report = harness.trace_log.verify_chain(result.trace_event_ref.trace_id)
    assert chain_report.is_valid is True
    assert chain_report.checked_events >= 1

    assert result.context_binding_ref.context_id == "context_gta_001"
    assert result.context_adequacy_ref.status == ContextAdequacyStatus.ADEQUATE
    assert result.context_adequacy_ref.context_binding_ref == result.context_binding_ref
    assert result.context_adequacy_ref.safe_to_act is True

    assert result.evidence_ref.source_trace_event_ref == result.trace_event_ref
    assert result.evidence_ref.is_canonical is False
    assert result.evidence_strength == EvidenceStrengthLevel.VERIFIED

    assert harness.verifier_result is not None
    assert harness.verifier_result.status == VerifierResultStatus.PASS
    assert harness.verifier_result.limitations
    assert harness.verifier_result.evidence_refs == (result.evidence_ref,)

    assert harness.capability_evidence is not None
    assert harness.capability_evidence.status == CapabilityEvidenceStatus.VERIFIED
    assert result.capability_evidence_status == CapabilityEvidenceStatus.VERIFIED
    assert harness.capability_evidence.source_trace_event_ref == result.trace_event_ref
    assert harness.capability_evidence.source_event_hash == result.source_event_hash
    assert harness.capability_evidence.evidence_refs == (result.evidence_ref,)
    assert harness.capability_evidence.verifier_result_ref == result.verifier_result_ref
    assert harness.capability_evidence.context_binding_ref == result.context_binding_ref
    assert harness.capability_evidence.context_adequacy_ref == result.context_adequacy_ref.context_adequacy_id
    assert harness.capability_evidence.evidence_strength in (
        EvidenceStrengthLevel.STRONG,
        EvidenceStrengthLevel.VERIFIED,
    )
    assert harness.capability_evidence.limitations

    # P1.5.14: Evaluation Mirror runtime hook
    assert result.evaluation_request_id is not None
    assert result.evaluation_run_id is not None
    assert result.evaluation_result_status is not None
    assert result.evaluation_event_refs

    # P1.5.15: Brain-aware evaluation context
    assert result.brain_eval_context_id is not None
    assert result.failure_classification_id is not None
    assert result.failure_reason == "none"
    assert result.context_risk_level == "low"
    assert result.recommended_next_action == "none"

    # P1.5.16: Capability Claim Registry v2
    assert result.capability_claim_candidate_id is not None
    assert result.capability_claim_decision_id is not None
    assert result.capability_claim_id is not None
    assert result.capability_claim_status == "context_verified"
    assert result.capability_claim_report_id is not None
    assert harness.claim is not None
    assert harness.claim.status == "context_verified"
    assert harness.claim_report is not None
    assert harness.claim_report.limitations
    # NOT universal verified
    assert harness.claim.status != "verified"
    assert harness.claim.status != "verified_candidate"

    # P1.5.17: Operator Feedback Capture v2
    assert result.operator_feedback_id is not None
    assert result.operator_feedback_id == "feedback_gta_001"
    assert result.feedback_processing_report_id is not None
    assert result.feedback_signal_strength == "strong"
    assert len(result.feedback_candidate_actions) > 0
    assert result.claim_status_after_feedback == "context_verified"
    assert harness.operator_feedback is not None
    assert harness.operator_feedback.feedback_type == "approval"
    assert harness.feedback_report is not None
    assert len(harness.feedback_report.blocked_actions) > 0
    # Claim remains context_verified (not auto-universalized)
    assert result.claim_status_after_feedback != "verified"

    # P1.5.18: Evaluation <-> Memory Candidate Bridge
    assert result.memory_bridge_report_id is not None
    assert result.memory_candidate_id == "mem_gta_001"
    assert result.memory_candidate_type == "capability_lesson"
    assert result.memory_candidate_status == "candidate"
    assert result.memory_validation_report_id == "mem_val_gta_001"
    assert result.memory_committed is False  # MUST NEVER be True
    assert harness.memory_candidate is not None
    assert harness.memory_candidate.candidate_type.value == "capability_lesson"
    assert harness.memory_validation_report is not None
    assert harness.memory_validation_report.is_valid is True
    assert harness.memory_bridge_report is not None
    # Bridge report must contain created candidates
    assert len(harness.memory_bridge_report.created_memory_candidate_ids) > 0

    # P1.5.19: Integrated seal assertions
    assert result.p15_seal_report_id is not None
    assert result.gta_seal_report_id is not None
    assert result.invariant_checklist_id is not None
    assert result.contract_invariants_passed is True
    assert result.golden_thread_seal_passed is True
    assert result.invariant_failed_count == 0
    assert result.memory_committed is False
    assert harness.seal_report is not None
    assert harness.gta_seal_report is not None
    assert harness.invariant_checklist is not None
    assert result.p15_seal_passed is False  # cold-cache required


def test_golden_thread_a_runs_with_context_binding():
    harness = GoldenThreadAHarness()
    result = harness.run_demo()

    assert result.passed is True
    assert result.context_binding_ref.context_type == "golden_thread_stub"
    assert result.context_adequacy_ref.status == ContextAdequacyStatus.ADEQUATE
    assert result.source_event_hash == result.trace_event_ref.event_hash
    assert result.evidence_strength == EvidenceStrengthLevel.VERIFIED
    assert result.capability_evidence_status == CapabilityEvidenceStatus.VERIFIED
    assert harness.trace_log.verify_chain(result.trace_event_ref.trace_id).is_valid is True
    assert result.failure_reason == "none"
    assert result.context_risk_level == "low"
    assert result.capability_claim_status == "context_verified"
    assert result.capability_claim_id is not None
    assert result.operator_feedback_id is not None
    assert result.feedback_signal_strength == "strong"
    assert result.claim_status_after_feedback == "context_verified"

    # P1.5.18: Memory candidate assertions
    assert result.memory_candidate_id == "mem_gta_001"
    assert result.memory_candidate_type == "capability_lesson"
    assert result.memory_committed is False
    assert result.memory_bridge_report_id is not None
    assert result.memory_validation_report_id == "mem_val_gta_001"

    # P1.5.19: Integrated seal assertions
    assert result.p15_seal_report_id is not None
    assert result.gta_seal_report_id is not None
    assert result.invariant_checklist_id is not None
    assert result.contract_invariants_passed is True
    assert result.golden_thread_seal_passed is True
    assert result.invariant_failed_count == 0
    assert result.p15_seal_passed is False  # cold-cache required
    assert harness.seal_report is not None
    assert harness.gta_seal_report is not None
    assert harness.invariant_checklist is not None
