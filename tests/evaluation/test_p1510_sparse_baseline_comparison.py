"""P1.5.10 sparse baseline comparison readiness tests."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.baseline_comparison import (
    ComparisonDimension,
    ComparisonSignal,
    compare_evaluation_results,
)
from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationConfidenceClass,
    EvaluationEvidenceQuality,
    EvaluationFailureMode,
    EvaluationOutcome,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationVerdict,
)
from tests.evaluation.test_baseline_reference import _make_ref


def _make_result(**kwargs) -> EvaluationResult:
    defaults = {
        "result_id": "result_001",
        "run_id": "run_001",
        "status": EvaluationResultStatus.COMPLETED,
        "outcome": EvaluationOutcome.PASSED,
        "verdict": EvaluationVerdict.SUPPORTED,
        "confidence": EvaluationConfidenceClass.HIGH,
        "evidence_quality": EvaluationEvidenceQuality.STRONG,
        "failure_modes": (EvaluationFailureMode.NONE,),
    }
    defaults.update(kwargs)
    return EvaluationResult(**defaults)


class TestSparseDimensions:
    def test_sparse_context_quality_dimension_supported(self):
        assert ComparisonDimension.SPARSE_CONTEXT_QUALITY.value == "SPARSE_CONTEXT_QUALITY"

    def test_evidence_recall_dimension_supported(self):
        assert ComparisonDimension.EVIDENCE_RECALL.value == "EVIDENCE_RECALL"

    def test_lost_context_risk_dimension_supported(self):
        assert ComparisonDimension.LOST_CONTEXT_RISK.value == "LOST_CONTEXT_RISK"

    def test_multi_hop_trace_integrity_dimension_supported(self):
        assert ComparisonDimension.MULTI_HOP_TRACE_INTEGRITY.value == "MULTI_HOP_TRACE_INTEGRITY"

    def test_contradiction_survival_dimension_supported(self):
        assert ComparisonDimension.CONTRADICTION_SURVIVAL.value == "CONTRADICTION_SURVIVAL"

    def test_context_budget_efficiency_dimension_supported(self):
        assert ComparisonDimension.CONTEXT_BUDGET_EFFICIENCY.value == "CONTEXT_BUDGET_EFFICIENCY"

    def test_governed_context_selection_dimension_supported(self):
        assert ComparisonDimension.GOVERNED_CONTEXT_SELECTION.value == "GOVERNED_CONTEXT_SELECTION"

    def test_authority_aware_retrieval_dimension_supported(self):
        assert ComparisonDimension.AUTHORITY_AWARE_RETRIEVAL.value == "AUTHORITY_AWARE_RETRIEVAL"

    def test_sparse_dimension_comparison_via_failure_modes(self):
        decision = compare_evaluation_results(
            comparison_id="cmp_sparse_001",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(
                failure_modes=(EvaluationFailureMode.MISSING_EVIDENCE,)
            ),
            current_result=_make_result(failure_modes=(EvaluationFailureMode.NONE,)),
            dimensions=(ComparisonDimension.LOST_CONTEXT_RISK,),
        )
        assert decision.signal == ComparisonSignal.IMPROVED

    def test_sparse_comparison_does_not_run_sparse_compiler(self):
        src = inspect.getsource(compare_evaluation_results)
        assert "SparseContextCompiler" not in src

    def test_sparse_comparison_does_not_claim_ssa_implemented(self):
        from agentic_runtime.evaluation.baseline_comparison import P1510_INVARIANTS

        joined = "\n".join(P1510_INVARIANTS)
        assert "SSA" in joined or "subquadratic" in joined

    def test_sparse_comparison_does_not_claim_subquadratic_model_implemented(self):
        src = inspect.getsource(compare_evaluation_results)
        assert "subquadratic" not in src.lower()
