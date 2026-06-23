"""P1.5.16 Capability Claim Status Derivation tests.

Verifies deterministic status derivation from evaluation results.
"""
from __future__ import annotations

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    EvidenceStrengthLevel,
)
from agentic_runtime.contracts.capability_claims import (
    CapabilityClaimStatus,
)
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
)
from agentic_runtime.contracts.evaluation_context import (
    BrainAwareEvaluationContext,
    ContextRiskLevel,
    EvaluationContextSnapshot,
    EvaluationFailureClassification,
    EvaluationFailureReason,
)
from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationRunResult,
    EvaluationRunStatus,
)
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventStatus,
    TraceEventType,
    trace_event_ref,
)
from agentic_runtime.contracts.verifier import (
    VerifierKind,
    VerifierResult,
    VerifierResultStatus,
)
from agentic_runtime.evaluation.capability_claim_derivation import (
    derive_capability_claim_candidate,
)

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_ref() -> tuple[AurelTraceLog, "trace_event_ref"]:
    from agentic_runtime.contracts.trace import trace_event_ref as _ref
    log = AurelTraceLog(trace_id="trace_deriv_001")
    event = log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="deriv",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return log, _ref(event)


def _make_context_binding() -> ContextBindingRef:
    return ContextBindingRef(
        context_id="ctx_deriv_001",
        context_type="test_stub",
        source_refs=("docs/test.md",),
        assumptions=("No real execution.",),
        created_at=_TIMESTAMP,
    )


def _make_pass_eval_result() -> EvaluationRunResult:
    return EvaluationRunResult(
        run_id="eval_run_pass",
        request_id="req_pass",
        status=EvaluationRunStatus.PASSED,
        summary="Passed evaluation.",
        limitations=("Test limitation.",),
        completed_at=_TIMESTAMP,
    )


def _make_fail_eval_result() -> EvaluationRunResult:
    return EvaluationRunResult(
        run_id="eval_run_fail",
        request_id="req_fail",
        status=EvaluationRunStatus.FAILED,
        summary="Failed evaluation.",
        errors=("Test error.",),
        limitations=("Test limitation.",),
        completed_at=_TIMESTAMP,
    )


def _make_inconclusive_eval_result() -> EvaluationRunResult:
    return EvaluationRunResult(
        run_id="eval_run_inc",
        request_id="req_inc",
        status=EvaluationRunStatus.INCONCLUSIVE,
        summary="Inconclusive evaluation.",
        limitations=("Test limitation.",),
        completed_at=_TIMESTAMP,
    )


def _make_needs_review_eval_result() -> EvaluationRunResult:
    return EvaluationRunResult(
        run_id="eval_run_review",
        request_id="req_review",
        status=EvaluationRunStatus.NEEDS_REVIEW,
        summary="Needs review.",
        limitations=("Test limitation.",),
        completed_at=_TIMESTAMP,
    )


def _make_brain_ctx(
    primary_reason: EvaluationFailureReason = EvaluationFailureReason.NONE,
    risk_level: ContextRiskLevel = ContextRiskLevel.LOW,
) -> BrainAwareEvaluationContext:
    trace_log, trace_ref = _make_trace_ref()
    snapshot = EvaluationContextSnapshot(
        snapshot_id="snap_001",
        source_trace_event_ref=trace_ref,
        created_at=_TIMESTAMP,
    )
    from agentic_runtime.contracts.evaluation_context import ContextSignal
    signals: tuple[ContextSignal, ...] = ()
    if primary_reason != EvaluationFailureReason.NONE:
        signals = (
            ContextSignal(
                signal_id="signal_crit",
                signal_type="critical_context",
                severity="critical",
                reason="Test critical context signal.",
                created_at=_TIMESTAMP,
            ),
        )
    classification = EvaluationFailureClassification(
        classification_id="class_001",
        primary_reason=primary_reason,
        context_risk_level=risk_level,
        signals=signals,
        created_at=_TIMESTAMP,
    )
    return BrainAwareEvaluationContext(
        brain_eval_context_id="brain_001",
        evaluation_context_snapshot=snapshot,
        failure_classification=classification,
        recommended_next_action="block_promotion",
        created_at=_TIMESTAMP,
    )


def _make_cap_evidence(strength: EvidenceStrengthLevel = EvidenceStrengthLevel.VERIFIED) -> CapabilityEvidenceRecord:
    trace_log, trace_ref = _make_trace_ref()
    return CapabilityEvidenceRecord(
        capability_evidence_id="cap_ev_001",
        capability_id="cap.test",
        source_trace_event_ref=trace_ref,
        source_event_hash=trace_ref.event_hash,
        evidence_refs=("ev_001",),
        verifier_result_ref="ver_001",
        context_binding_ref="ctx_001",
        context_adequacy_ref="ca_001",
        evidence_strength=strength,
        status=CapabilityEvidenceStatus.UNVERIFIED,
        limitations=("Test limitation.",),
        created_at=_TIMESTAMP,
    )


def _make_verifier(status: VerifierResultStatus = VerifierResultStatus.PASS) -> VerifierResult:
    trace_log, trace_ref = _make_trace_ref()
    return VerifierResult(
        verifier_id="ver_001",
        verifier_kind=VerifierKind.EVIDENCE_INTEGRITY,
        target_ref="target_001",
        status=status,
        confidence=1.0,
        reason="Test.",
        limitations=("Test limitation.",),
        evidence_refs=("ev_001",),
        source_trace_event_ref=trace_ref,
        created_at=_TIMESTAMP,
    )


class TestSuccessfulDerivation:
    """Passed evaluation derives context_verified candidate."""

    def test_passed_derives_context_verified(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.CONTEXT_VERIFIED
        assert "context_verified" in candidate.proposed_claim_text.lower()

    def test_not_universal_verified(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status != CapabilityClaimStatus.VERIFIED
        assert candidate.proposed_status != CapabilityClaimStatus.VERIFIED_CANDIDATE


class TestWeakEvidenceDerivation:
    """Weak evidence derives weakly_supported claim."""

    def test_weak_evidence_derives_weakly_supported(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.WEAK),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.WEAKLY_SUPPORTED

    def test_moderate_evidence_derives_weakly_supported(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.MODERATE),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.WEAKLY_SUPPORTED


class TestFailedDerivation:
    """Failed evaluation derives failed claim."""

    def test_failed_evaluation_derives_failed(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_fail_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.FAILED

    def test_verifier_failed_derives_failed(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.FAIL),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.FAILED

    def test_critical_context_blocks_positive_claim(self) -> None:
        brain = _make_brain_ctx(
            primary_reason=EvaluationFailureReason.UNSAFE_CONTEXT,
            risk_level=ContextRiskLevel.CRITICAL,
        )
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=brain,
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.FAILED

    def test_unsafe_context_blocks_positive_claim(self) -> None:
        ctx = _make_context_binding()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_unsafe",
            context_binding_ref=ctx,
            status=ContextAdequacyStatus.UNSAFE,
            safe_to_act=False,
            requires_operator_clarification=True,
            created_at=_TIMESTAMP,
        )
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            context_adequacy=context_adequacy,
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.FAILED

    def test_insufficient_context_blocks_positive_claim(self) -> None:
        ctx = _make_context_binding()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_insuff",
            context_binding_ref=ctx,
            status=ContextAdequacyStatus.INSUFFICIENT,
            requires_operator_clarification=True,
            created_at=_TIMESTAMP,
        )
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            context_adequacy=context_adequacy,
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.FAILED


class TestInconclusiveDerivation:
    """Inconclusive results derive experimental claim."""

    def test_inconclusive_derives_experimental(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_inconclusive_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.PASS),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.EXPERIMENTAL

    def test_verifier_inconclusive_derives_experimental(self) -> None:
        candidate = derive_capability_claim_candidate(
            evaluation_result=_make_pass_eval_result(),
            brain_context=_make_brain_ctx(),
            capability_evidence=_make_cap_evidence(EvidenceStrengthLevel.VERIFIED),
            verifier_result=_make_verifier(VerifierResultStatus.INCONCLUSIVE),
            capability_id="cap.test",
        )
        assert candidate.proposed_status == CapabilityClaimStatus.EXPERIMENTAL


class TestGoldenThreadAPath:
    """Default Golden Thread A path: context_verified."""

    def test_golden_thread_a_produces_context_verified(self) -> None:
        from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness
        harness = GoldenThreadAHarness()
        harness.run_demo()
        assert harness.claim_candidate is not None
        assert harness.claim_candidate.proposed_status == CapabilityClaimStatus.CONTEXT_VERIFIED
        assert harness.claim is not None
        assert harness.claim.status == CapabilityClaimStatus.CONTEXT_VERIFIED
