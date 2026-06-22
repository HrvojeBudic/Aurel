"""P1.5.15 Brain-Aware Evaluation Context tests.

Verifies: snapshot creation, brain_aware context attachment, success/failure
classification paths, anti-promotion, and no open-domain cognition.
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
    BrainAwareEvaluationContext,
    ContextRiskLevel,
    ContextSignal,
    EvaluationContextSnapshot,
    EvaluationFailureClassification,
    EvaluationFailureReason,
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
from agentic_runtime.golden_threads.thread_a import GoldenThreadAHarness

_TIMESTAMP = "2026-06-22T00:00:00+00:00"


def _make_trace_log() -> AurelTraceLog:
    return AurelTraceLog(trace_id="trace_p1_5_15_test_001")


def _make_trace_ref(trace_log: AurelTraceLog) -> TraceEventRef:
    event = trace_log.append(
        event_type=TraceEventType.STUB_EXECUTION_COMPLETED,
        actor_type="test",
        actor_id="p1_5_15",
        payload_json={"test": True},
        timestamp=_TIMESTAMP,
        status=TraceEventStatus.COMPLETED,
    )
    return trace_event_ref(event)


def _make_context() -> ContextBindingRef:
    return ContextBindingRef(
        context_id="ctx_001",
        context_type="test_stub",
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


class TestGoldenThreadABrainAware:
    """Golden Thread A produces brain-aware evaluation context."""

    def test_golden_thread_a_has_brain_aware_fields(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        assert result.brain_eval_context_id is not None
        assert result.failure_classification_id is not None
        assert result.failure_reason == "none"
        assert result.context_risk_level == "low"
        assert result.recommended_next_action == "none"
        assert harness.brain_aware_evaluation_context is not None

    def test_golden_thread_a_passes_with_low_risk(self) -> None:
        harness = GoldenThreadAHarness()
        result = harness.run_demo()
        assert result.passed is True
        assert result.failure_reason == "none"
        assert result.context_risk_level == "low"


class TestSnapshotCreation:
    """EvaluationContextSnapshot freezes diagnostic state."""

    def test_snapshot_stores_trace_ref(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        snapshot = EvaluationContextSnapshot(
            snapshot_id="snap_001",
            source_trace_event_ref=trace_ref,
            created_at=_TIMESTAMP,
        )
        assert snapshot.source_trace_event_ref.event_id == trace_ref.event_id

    def test_snapshot_stores_context_verifier_refs(self) -> None:
        trace_log = _make_trace_log()
        trace_ref = _make_trace_ref(trace_log)
        snapshot = EvaluationContextSnapshot(
            snapshot_id="snap_002",
            source_trace_event_ref=trace_ref,
            context_binding_ref="ctx_001",
            context_adequacy_ref="ca_001",
            verifier_result_refs=("v_001", "v_002"),
            evidence_refs=("ev_001",),
            capability_evidence_ref="cap_001",
            created_at=_TIMESTAMP,
        )
        assert snapshot.context_binding_ref == "ctx_001"
        assert snapshot.verifier_result_refs == ("v_001", "v_002")
        assert snapshot.capability_evidence_ref == "cap_001"


class TestBrainAwareContext:
    """BrainAwareEvaluationContext attaches failure classification."""

    def test_brain_ctx_wraps_classification(self) -> None:
        snapshot = EvaluationContextSnapshot(
            snapshot_id="snap_003",
            source_trace_event_ref=_make_trace_ref(_make_trace_log()),
            created_at=_TIMESTAMP,
        )
        classification = EvaluationFailureClassification(
            classification_id="class_001",
            primary_reason=EvaluationFailureReason.NONE,
            created_at=_TIMESTAMP,
        )
        brain = BrainAwareEvaluationContext(
            brain_eval_context_id="brain_001",
            evaluation_context_snapshot=snapshot,
            failure_classification=classification,
            recommended_next_action="none",
            created_at=_TIMESTAMP,
        )
        assert brain.failure_classification.primary_reason == EvaluationFailureReason.NONE
        assert brain.recommended_next_action == "none"


class TestAntiPromotion:
    """New P1.5.15 types do not introduce promotion/mutation capability."""

    _DISALLOWED = {
        "capability_promoted", "memory_written", "skill_created",
        "reflex_created", "policy_changed", "promote_capability",
        "mutate_policy", "commit_memory",
    }

    def test_context_signal_no_promotion_fields(self) -> None:
        fields = {f.name for f in ContextSignal.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_snapshot_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationContextSnapshot.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_classification_no_promotion_fields(self) -> None:
        fields = {f.name for f in EvaluationFailureClassification.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)

    def test_brain_ctx_no_promotion_fields(self) -> None:
        fields = {f.name for f in BrainAwareEvaluationContext.__dataclass_fields__.values()}
        assert not (fields & self._DISALLOWED)


class TestNoOpenDomainCognition:
    """Brain-aware context uses explicit flags only, no LLM/NLI/semantic detection."""

    def test_classify_uses_only_explicit_inputs(self) -> None:
        """classify_evaluation_context only accepts explicit typed inputs."""
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

    def test_classification_does_not_contain_llm_nli_fields(self) -> None:
        """verify no semantic detection fields exist on any contract."""
        for cls in (ContextSignal, EvaluationContextSnapshot,
                     EvaluationFailureClassification, BrainAwareEvaluationContext):
            fields = {f.name for f in cls.__dataclass_fields__.values()}
            prohibited = {"llm_judgment", "nli_verdict", "semantic_contradiction",
                          "theory_of_mind", "intent_engine", "noesis", "soul_integrity"}
            assert not (fields & prohibited), f"{cls.__name__} contains prohibited fields"
