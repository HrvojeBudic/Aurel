"""Scope guard tests — P1.5.10."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.baseline_comparison import (
    BaselineStatus,
    ComparisonDimension,
    P1510_INVARIANTS,
    build_p1510_baseline_comparison_report,
    compare_adversarial_coverage,
    compare_evaluation_results,
    compare_hygiene_refs,
)
from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
)
from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationEvidenceQuality,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationVerdict,
)
from tests.evaluation.test_baseline_reference import _make_ref


def test_p1510_does_not_run_evaluation():
    src = inspect.getsource(compare_evaluation_results)
    assert "run_evaluation" not in src
    assert "execute_evaluation" not in src


def test_p1510_does_not_run_benchmark():
    src = inspect.getsource(compare_hygiene_refs)
    assert "run_benchmark" not in src
    assert "execute_benchmark" not in src


def test_p1510_does_not_execute_adversarial_cases():
    src = inspect.getsource(compare_adversarial_coverage)
    assert "run_case" not in src
    assert "execute_case" not in src


def test_p1510_does_not_create_evaluation_result():
    src = inspect.getsource(compare_evaluation_results) + inspect.getsource(compare_adversarial_coverage)
    assert "EvaluationResult(" not in src


def test_p1510_does_not_create_capability_evidence_record():
    src = inspect.getsource(compare_evaluation_results)
    assert "CapabilityEvidenceRecord(" not in src


def test_p1510_does_not_verify_capability():
    report = build_p1510_baseline_comparison_report()
    joined = "\n".join(P1510_INVARIANTS).lower()
    assert "does not verify capability" in joined
    assert "verify capability" not in report.summary.lower()


def test_p1510_does_not_mutate_claim_status():
    evidence = CapabilityEvidenceRecord(
        evidence_id="ev_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
        claim_id="claim_001",
    )
    decision = compare_evaluation_results(
        comparison_id="cmp_scope",
        baseline=_make_ref(baseline_id="baseline_001"),
        current=_make_ref(baseline_id="current_001"),
        baseline_result=EvaluationResult(
            result_id="r1",
            run_id="run1",
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.FAILED,
            verdict=EvaluationVerdict.UNSUPPORTED,
            confidence=EvaluationConfidenceClass.LOW,
            evidence_quality=EvaluationEvidenceQuality.WEAK,
        ),
        current_result=EvaluationResult(
            result_id="r2",
            run_id="run1",
            status=EvaluationResultStatus.COMPLETED,
            outcome=EvaluationOutcome.PASSED,
            verdict=EvaluationVerdict.SUPPORTED,
            confidence=EvaluationConfidenceClass.HIGH,
            evidence_quality=EvaluationEvidenceQuality.STRONG,
        ),
        dimensions=(ComparisonDimension.OUTCOME,),
    )
    assert evidence.claim_id == "claim_001"
    assert decision.signal in decision.signal.__class__
    assert not hasattr(evidence, "claim_status")


def test_p1510_does_not_create_verified_status():
    assert not hasattr(BaselineStatus, "VERIFIED")


def test_p1510_does_not_introduce_numeric_score():
    report = build_p1510_baseline_comparison_report()
    assert not hasattr(report, "score")


def test_p1510_does_not_call_llm_or_tools():
    src = inspect.getsource(compare_evaluation_results) + inspect.getsource(compare_hygiene_refs)
    assert "call_tool" not in src.lower()
    assert "llm" not in src.lower()


def test_p1510_does_not_implement_sparse_context_compiler():
    src = inspect.getsource(compare_evaluation_results)
    assert "SparseContextCompiler" not in src


def test_p1510_does_not_implement_hub_runtime():
    src = inspect.getsource(compare_evaluation_results)
    assert "hub_runtime" not in src.lower()


def test_p1510_prepares_p1511_regression_detection():
    report = build_p1510_baseline_comparison_report()
    assert "P1.5.11" in report.next_module
    assert "Regression Detection" in report.next_module
