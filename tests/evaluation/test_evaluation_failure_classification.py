"""P1.5.15 Evaluation Failure Classification tests.

Verifies every classification rule: success, unsafe, hash_mismatch,
missing context, verifier failed, partial context, weak evidence,
verifier inconclusive, multiple signals, constraints propagation.
"""
from __future__ import annotations

import pytest as pytest

from agentic_runtime.contracts.capability import (
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    EvidenceStrengthLevel,
)
from agentic_runtime.contracts.context import (
    ContextAdequacyReport,
    ContextAdequacyStatus,
    ContextBindingRef,
)
from agentic_runtime.contracts.evaluation_context import (
    ContextRiskLevel,
    EvaluationFailureReason,
)
from agentic_runtime.contracts.evaluation_runtime import (
    EvaluationRunResult,
    EvaluationRunStatus,
)
from agentic_runtime.contracts.evidence import EvidenceRef, build_evidence_ref
from agentic_runtime.contracts.trace import (
    AurelTraceLog,
    TraceEventRef,
    TraceEventStatus,
    TraceEventType,
    hash_json,
    trace_event_ref,
)
from agentic_runtime.contracts.verifier import (
    VerifierKind,
    VerifierResult,
    VerifierResultStatus,
)
from agentic_runtime.evaluation.context_diagnostics import classify_evaluation_context

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_log() -> AurelTraceLog:
    return AurelTraceLog(trace_id="trace_p1_5_15_class_001")


def _make_trace_ref(trace_log: AurelTraceLog) -> TraceEventRef:
    event = trace_log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="p1_5_15_classifier",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_context() -> ContextBindingRef:
    return ContextBindingRef(
        context_id="ctx_001",
        context_type="test",
        source_refs=("docs/test.md",),
        assumptions=("No real execution.",),
        created_at=_TIMESTAMP,
    )


def _make_verifier(trace_ref: TraceEventRef, status: VerifierResultStatus = VerifierResultStatus.PASS) -> VerifierResult:
    return VerifierResult(
        verifier_id="verifier_test_001",
        verifier_kind=VerifierKind.EVIDENCE_INTEGRITY,
        target_ref="target_001",
        status=status,
        confidence=1.0,
        reason="Test verifier reason.",
        limitations=("Test limitation only.",),
        evidence_refs=(_make_evidence_ref(trace_ref),),
        source_trace_event_ref=trace_ref,
        created_at=_TIMESTAMP,
    )


def _make_evidence_ref(trace_ref: TraceEventRef) -> EvidenceRef:
    return build_evidence_ref(
        evidence_id="evidence_test_001",
        source_trace_event_ref=trace_ref,
        evidence_type="test_stub",
        content={"test": True},
        summary="Test evidence.",
    )


class TestSuccess:
    """All clean → primary_reason=none, risk_level=low."""

    def test_all_clean_success(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_001",
            context_binding_ref=context,
            status=ContextAdequacyStatus.ADEQUATE,
            created_at=_TIMESTAMP,
        )
        verifier = _make_verifier(trace_ref)

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.NONE
        assert classification.context_risk_level == ContextRiskLevel.LOW
        assert not classification.requires_operator_clarification
        assert not classification.blocks_verified_capability
        assert not classification.blocks_positive_eval_case


class TestMissingContext:
    """Insufficient context → missing_context, high risk."""

    def test_missing_context_insufficient(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_002",
            context_binding_ref=context,
            status=ContextAdequacyStatus.INSUFFICIENT,
            created_at=_TIMESTAMP,
            requires_operator_clarification=True,
        )
        verifier = _make_verifier(trace_ref)

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.MISSING_CONTEXT
        assert classification.context_risk_level == ContextRiskLevel.HIGH
        assert classification.blocks_positive_eval_case

    def test_missing_context_binding(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        verifier = _make_verifier(trace_ref)

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=None,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.MISSING_CONTEXT
        assert classification.context_risk_level == ContextRiskLevel.HIGH


class TestUnsafeContext:
    """Unsafe context → unsafe_context, critical risk, blocks both."""

    def test_unsafe_context(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_003",
            context_binding_ref=context,
            status=ContextAdequacyStatus.UNSAFE,
            safe_to_act=False,
            requires_operator_clarification=True,
            created_at=_TIMESTAMP,
        )

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.UNSAFE_CONTEXT
        assert classification.context_risk_level == ContextRiskLevel.CRITICAL
        assert classification.blocks_verified_capability
        assert classification.blocks_positive_eval_case


class TestPartialContext:
    """Partial context → missing_context, medium risk, needs clarification."""

    def test_partial_context(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_004",
            context_binding_ref=context,
            status=ContextAdequacyStatus.PARTIAL,
            created_at=_TIMESTAMP,
        )

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.MISSING_CONTEXT
        assert classification.context_risk_level == ContextRiskLevel.MEDIUM
        assert classification.requires_operator_clarification


class TestWeakEvidence:
    """WEAK/MODERATE/NONE evidence → weak_evidence, medium risk."""

    @pytest.mark.parametrize("strength", [
        EvidenceStrengthLevel.WEAK,
        EvidenceStrengthLevel.MODERATE,
        EvidenceStrengthLevel.NONE,
    ])
    def test_weak_evidence(self, strength: EvidenceStrengthLevel) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_005",
            context_binding_ref=context,
            status=ContextAdequacyStatus.ADEQUATE,
            created_at=_TIMESTAMP,
        )
        verifier = _make_verifier(trace_ref)
        capability = CapabilityEvidenceRecord(
            capability_evidence_id="cap_001",
            capability_id="cap.test",
            source_trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
            evidence_refs=("ev_001",),
            verifier_result_ref=verifier.verifier_id,
            context_binding_ref=context.context_id,
            context_adequacy_ref=context_adequacy.context_adequacy_id,
            evidence_strength=strength,
            status=CapabilityEvidenceStatus.UNVERIFIED,
            limitations=("Test limitation.",),
            created_at=_TIMESTAMP,
        )

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            capability_evidence=capability,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.WEAK_EVIDENCE
        assert classification.context_risk_level == ContextRiskLevel.MEDIUM
        assert classification.blocks_positive_eval_case


class TestVerifierFailed:
    """Verifier FAIL → verifier_failed, high risk."""

    def test_verifier_failed(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_006",
            context_binding_ref=context,
            status=ContextAdequacyStatus.ADEQUATE,
            created_at=_TIMESTAMP,
        )
        verifier = _make_verifier(trace_ref, status=VerifierResultStatus.FAIL)

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.VERIFIER_FAILED
        assert classification.context_risk_level == ContextRiskLevel.HIGH
        assert classification.blocks_positive_eval_case


class TestVerifierInconclusive:
    """Verifier INCONCLUSIVE → verifier_inconclusive, medium risk."""

    def test_verifier_inconclusive(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_007",
            context_binding_ref=context,
            status=ContextAdequacyStatus.ADEQUATE,
            created_at=_TIMESTAMP,
        )
        verifier = _make_verifier(trace_ref, status=VerifierResultStatus.INCONCLUSIVE)

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        assert classification.primary_reason == EvaluationFailureReason.VERIFIER_INCONCLUSIVE
        assert classification.context_risk_level == ContextRiskLevel.MEDIUM
        assert classification.requires_operator_clarification


class TestHashMismatch:
    """Hash mismatch → hash_mismatch, critical risk."""

    def test_hash_mismatch(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_008",
            context_binding_ref=context,
            status=ContextAdequacyStatus.ADEQUATE,
            created_at=_TIMESTAMP,
        )
        verifier = _make_verifier(trace_ref)

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            verifier_results=(verifier,),
            trace_event_ref=trace_ref,
            source_event_hash="wrong_hash_999",
        )
        assert classification.primary_reason == EvaluationFailureReason.HASH_MISMATCH
        assert classification.context_risk_level == ContextRiskLevel.CRITICAL
        assert classification.blocks_verified_capability
        assert classification.blocks_positive_eval_case


class TestMultipleSignalsPriority:
    """When multiple failure conditions exist, most severe wins (critical > high > medium > low)."""

    def test_unsafe_beats_missing_context(self) -> None:
        """Unsafe context is critical; missing_context is high → unsafe wins."""
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_009",
            context_binding_ref=context,
            status=ContextAdequacyStatus.UNSAFE,
            safe_to_act=False,
            requires_operator_clarification=True,
            created_at=_TIMESTAMP,
        )

        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            trace_event_ref=trace_ref,
            source_event_hash=trace_ref.event_hash,
        )
        # UNSAFE is checked first and returns critical
        assert classification.primary_reason == EvaluationFailureReason.UNSAFE_CONTEXT
        assert classification.context_risk_level == ContextRiskLevel.CRITICAL

    def test_hash_mismatch_beats_missing_context(self) -> None:
        """Hash mismatch (critical) beats missing_context (high)."""
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        context = _make_context()
        context_adequacy = ContextAdequacyReport(
            context_adequacy_id="ca_010",
            context_binding_ref=context,
            status=ContextAdequacyStatus.INSUFFICIENT,
            requires_operator_clarification=True,
            created_at=_TIMESTAMP,
        )

        # Hash mismatch is checked BEFORE missing context
        brain, snap, classification = classify_evaluation_context(
            context_binding_ref=context,
            context_adequacy_report=context_adequacy,
            trace_event_ref=trace_ref,
            source_event_hash="bad_hash",
        )
        assert classification.primary_reason == EvaluationFailureReason.HASH_MISMATCH


class TestConstraints:
    """Failed result requires failure_classification_Ref, unreview needs recommended_next_action."""

    def test_failed_result_needs_failure_classification(self) -> None:
        result = EvaluationRunResult(
            run_id="run_001",
            request_id="req_001",
            status=EvaluationRunStatus.FAILED,
            summary="Test failure.",
            errors=("Test error.",),
            limitations=("Test limitation.",),
            completed_at=_TIMESTAMP,
            failure_classification_ref="class_001",
        )
        assert result.failure_classification_ref == "class_001"

    def test_needs_review_result_needs_next_action(self) -> None:
        result = EvaluationRunResult(
            run_id="run_002",
            request_id="req_002",
            status=EvaluationRunStatus.NEEDS_REVIEW,
            summary="Test needs review.",
            limitations=("Test limitation.",),
            completed_at=_TIMESTAMP,
            recommended_next_action="ask_operator",
        )
        assert result.recommended_next_action == "ask_operator"

    def test_critical_risk_blocks_passed(self) -> None:
        """Context risk level critical should not be passed."""
        result = EvaluationRunResult(
            run_id="run_003",
            request_id="req_003",
            status=EvaluationRunStatus.FAILED,
            summary="Test with critical risk.",
            errors=("Critical context risk.",),
            limitations=("Test limitation.",),
            completed_at=_TIMESTAMP,
            context_limitations=("Risk level is critical.",),
            failure_classification_ref="class_002",
        )
        assert result.status != EvaluationRunStatus.PASSED
        assert result.failure_classification_ref is not None

    def test_context_limitations_propagate(self) -> None:
        result = EvaluationRunResult(
            run_id="run_004",
            request_id="req_004",
            status=EvaluationRunStatus.FAILED,
            summary="Test with context limitations.",
            errors=("Test error.",),
            limitations=("Test limitation.",),
            completed_at=_TIMESTAMP,
            context_limitations=("Missing context binding.", "Evidence is weak."),
            failure_classification_ref="class_003",
        )
        assert len(result.context_limitations) == 2
        assert any("Missing context binding" in s for s in result.context_limitations)
        assert any("Evidence is weak" in s for s in result.context_limitations)
