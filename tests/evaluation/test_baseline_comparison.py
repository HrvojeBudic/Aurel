"""P1.5.10 core comparison engine tests."""
from __future__ import annotations

import inspect
import json

from agentic_runtime.evaluation.baseline_comparison import (
    BaselineComparisonDecision,
    BaselineReferenceKind,
    BaselineStatus,
    ComparisonConfidence,
    ComparisonDimension,
    ComparisonSignal,
    compare_adversarial_coverage,
    compare_evaluation_results,
    compare_hygiene_refs,
    resolve_baseline_comparison_decision,
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


class TestEvaluationResultComparison:
    def test_compare_supported_current_over_unsupported_baseline_improved(self):
        baseline = _make_ref(baseline_id="baseline_001")
        current = _make_ref(baseline_id="current_001")
        decision = compare_evaluation_results(
            comparison_id="cmp_001",
            baseline=baseline,
            current=current,
            baseline_result=_make_result(verdict=EvaluationVerdict.UNSUPPORTED),
            current_result=_make_result(verdict=EvaluationVerdict.SUPPORTED),
            dimensions=(ComparisonDimension.VERDICT,),
        )
        assert decision.signal == ComparisonSignal.IMPROVED
        assert ComparisonDimension.VERDICT in decision.improved_dimensions

    def test_compare_weaker_current_degraded(self):
        decision = compare_evaluation_results(
            comparison_id="cmp_002",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(outcome=EvaluationOutcome.PASSED),
            current_result=_make_result(outcome=EvaluationOutcome.FAILED),
            dimensions=(ComparisonDimension.OUTCOME,),
        )
        assert decision.signal == ComparisonSignal.DEGRADED

    def test_compare_same_result_unchanged(self):
        result = _make_result()
        decision = compare_evaluation_results(
            comparison_id="cmp_003",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=result,
            current_result=result,
            dimensions=(ComparisonDimension.OUTCOME, ComparisonDimension.VERDICT),
        )
        assert decision.signal == ComparisonSignal.UNCHANGED

    def test_compare_mixed_dimensions_mixed(self):
        decision = compare_evaluation_results(
            comparison_id="cmp_004",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(
                outcome=EvaluationOutcome.FAILED,
                verdict=EvaluationVerdict.SUPPORTED,
            ),
            current_result=_make_result(
                outcome=EvaluationOutcome.PASSED,
                verdict=EvaluationVerdict.UNSUPPORTED,
            ),
            dimensions=(ComparisonDimension.OUTCOME, ComparisonDimension.VERDICT),
        )
        assert decision.signal == ComparisonSignal.MIXED

    def test_compare_unknown_values_inconclusive(self):
        decision = compare_evaluation_results(
            comparison_id="cmp_005",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(verdict=EvaluationVerdict.UNKNOWN),
            current_result=_make_result(verdict=EvaluationVerdict.UNKNOWN),
            dimensions=(ComparisonDimension.VERDICT,),
        )
        assert decision.signal == ComparisonSignal.INCONCLUSIVE

    def test_comparison_does_not_verify_capability(self):
        decision = compare_evaluation_results(
            comparison_id="cmp_006",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(verdict=EvaluationVerdict.UNSUPPORTED),
            current_result=_make_result(verdict=EvaluationVerdict.SUPPORTED),
            dimensions=(ComparisonDimension.VERDICT,),
        )
        assert "verify" not in decision.summary.lower()

    def test_comparison_no_numeric_score(self):
        decision = compare_evaluation_results(
            comparison_id="cmp_007",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(),
            current_result=_make_result(),
            dimensions=(ComparisonDimension.OUTCOME,),
        )
        assert not hasattr(decision, "score")
        assert decision.confidence in ComparisonConfidence


class TestAdversarialCoverageComparison:
    def test_current_more_adversarial_refs_improved(self):
        decision = compare_adversarial_coverage(
            comparison_id="cmp_adv_001",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_case_refs=("adv_001",),
            current_case_refs=("adv_001", "adv_002"),
        )
        assert decision.signal == ComparisonSignal.IMPROVED

    def test_current_missing_baseline_adversarial_refs_degraded(self):
        decision = compare_adversarial_coverage(
            comparison_id="cmp_adv_002",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_case_refs=("adv_001", "adv_002"),
            current_case_refs=("adv_001",),
        )
        assert decision.signal == ComparisonSignal.DEGRADED

    def test_same_adversarial_refs_unchanged(self):
        refs = ("adv_001", "adv_002")
        decision = compare_adversarial_coverage(
            comparison_id="cmp_adv_003",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_case_refs=refs,
            current_case_refs=refs,
        )
        assert decision.signal == ComparisonSignal.UNCHANGED

    def test_no_adversarial_refs_inconclusive(self):
        decision = compare_adversarial_coverage(
            comparison_id="cmp_adv_004",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_case_refs=(),
            current_case_refs=(),
        )
        assert decision.signal == ComparisonSignal.INCONCLUSIVE

    def test_adversarial_comparison_does_not_execute_cases(self):
        src = inspect.getsource(compare_adversarial_coverage)
        assert "run_case" not in src
        assert "execute_case" not in src


class TestHygieneComparison:
    def test_current_hygiene_refs_when_baseline_lacks_improved(self):
        decision = compare_hygiene_refs(
            comparison_id="cmp_hyg_001",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_hygiene_refs=(),
            current_hygiene_refs=("hygiene_001",),
        )
        assert decision.signal == ComparisonSignal.IMPROVED

    def test_missing_current_hygiene_refs_degraded(self):
        decision = compare_hygiene_refs(
            comparison_id="cmp_hyg_002",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_hygiene_refs=("hygiene_001",),
            current_hygiene_refs=(),
        )
        assert decision.signal == ComparisonSignal.DEGRADED

    def test_both_hygiene_refs_unchanged_or_inconclusive(self):
        refs = ("hygiene_001",)
        decision = compare_hygiene_refs(
            comparison_id="cmp_hyg_003",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_hygiene_refs=refs,
            current_hygiene_refs=refs,
        )
        assert decision.signal == ComparisonSignal.UNCHANGED

    def test_hygiene_comparison_does_not_assess_hygiene_again(self):
        src = inspect.getsource(compare_hygiene_refs)
        assert "assess_benchmark_hygiene" not in src
        assert "resolve_hygiene_decision" not in src


class TestDecisionResolver:
    def _decision(self, signal: ComparisonSignal, dimension: ComparisonDimension) -> BaselineComparisonDecision:
        baseline = _make_ref(baseline_id="baseline_001")
        current = _make_ref(baseline_id="current_001")
        if signal == ComparisonSignal.IMPROVED:
            improved = (dimension,)
            degraded = ()
            unchanged = ()
        elif signal == ComparisonSignal.DEGRADED:
            improved = ()
            degraded = (dimension,)
            unchanged = ()
        elif signal == ComparisonSignal.UNCHANGED:
            improved = ()
            degraded = ()
            unchanged = (dimension,)
        else:
            improved = ()
            degraded = ()
            unchanged = ()
        return BaselineComparisonDecision(
            comparison_id="dim_cmp",
            signal=signal,
            confidence=ComparisonConfidence.MODERATE,
            dimensions_compared=(dimension,),
            improved_dimensions=improved,
            degraded_dimensions=degraded,
            unchanged_dimensions=unchanged,
            inconclusive_dimensions=(),
            baseline_id=baseline.baseline_id,
            current_id=current.baseline_id,
            warnings=(),
            blockers=(),
            summary="dimension decision",
        )

    def test_resolve_all_improved_improved(self):
        d1 = self._decision(ComparisonSignal.IMPROVED, ComparisonDimension.OUTCOME)
        d2 = self._decision(ComparisonSignal.IMPROVED, ComparisonDimension.VERDICT)
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_001",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            dimension_signals=(d1, d2),
        )
        assert decision.signal == ComparisonSignal.IMPROVED

    def test_resolve_all_unchanged_unchanged(self):
        d1 = self._decision(ComparisonSignal.UNCHANGED, ComparisonDimension.OUTCOME)
        d2 = self._decision(ComparisonSignal.UNCHANGED, ComparisonDimension.VERDICT)
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_002",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            dimension_signals=(d1, d2),
        )
        assert decision.signal == ComparisonSignal.UNCHANGED

    def test_resolve_mixed_improved_and_degraded_mixed(self):
        d1 = self._decision(ComparisonSignal.IMPROVED, ComparisonDimension.OUTCOME)
        d2 = self._decision(ComparisonSignal.DEGRADED, ComparisonDimension.VERDICT)
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_003",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            dimension_signals=(d1, d2),
        )
        assert decision.signal == ComparisonSignal.MIXED

    def test_resolve_only_inconclusive_inconclusive(self):
        d1 = self._decision(ComparisonSignal.INCONCLUSIVE, ComparisonDimension.OUTCOME)
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_004",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            dimension_signals=(d1,),
        )
        assert decision.signal == ComparisonSignal.INCONCLUSIVE

    def test_resolve_blocked_signal_dominates(self):
        blocked = BaselineComparisonDecision(
            comparison_id="blocked",
            signal=ComparisonSignal.BLOCKED,
            confidence=ComparisonConfidence.INSUFFICIENT,
            dimensions_compared=(ComparisonDimension.OUTCOME,),
            improved_dimensions=(),
            degraded_dimensions=(),
            unchanged_dimensions=(),
            inconclusive_dimensions=(ComparisonDimension.OUTCOME,),
            baseline_id="baseline_001",
            current_id="current_001",
            warnings=(),
            blockers=("blocked",),
            summary="blocked",
        )
        improved = self._decision(ComparisonSignal.IMPROVED, ComparisonDimension.VERDICT)
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_005",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            dimension_signals=(blocked, improved),
        )
        assert decision.signal == ComparisonSignal.BLOCKED

    def test_resolve_kind_mismatch_incomparable_or_blocked(self):
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_006",
            baseline=_make_ref(
                baseline_id="baseline_001",
                kind=BaselineReferenceKind.EVALUATION_RESULT,
            ),
            current=_make_ref(
                baseline_id="current_001",
                kind=BaselineReferenceKind.ADVERSARIAL_COVERAGE,
            ),
            dimension_signals=(),
        )
        assert decision.signal in (ComparisonSignal.INCONCLUSIVE, ComparisonSignal.INCOMPARABLE)

    def test_resolve_no_dimension_signals_inconclusive(self):
        decision = resolve_baseline_comparison_decision(
            comparison_id="cmp_resolve_007",
            baseline=_make_ref(baseline_id="baseline_001", kind=BaselineReferenceKind.MANUAL_REFERENCE),
            current=_make_ref(baseline_id="current_001", kind=BaselineReferenceKind.MANUAL_REFERENCE),
            dimension_signals=(),
        )
        assert decision.signal == ComparisonSignal.INCONCLUSIVE


class TestCoreEnums:
    def test_baseline_reference_kind_closed_world(self):
        from agentic_runtime.evaluation.baseline_comparison import BaselineReferenceKind as BRK
        from agentic_runtime.evaluation.baseline_comparison import BaselineStatus as BS
        from agentic_runtime.evaluation.baseline_comparison import ComparisonConfidence as CC
        from agentic_runtime.evaluation.baseline_comparison import ComparisonDimension as CD
        from agentic_runtime.evaluation.baseline_comparison import ComparisonSignal as CS

        assert BRK("EVALUATION_RESULT") == BRK.EVALUATION_RESULT
        assert BS("ACTIVE") == BS.ACTIVE
        assert CD("SPARSE_CONTEXT_QUALITY") == CD.SPARSE_CONTEXT_QUALITY
        assert CS("IMPROVED") == CS.IMPROVED
        assert CC("HIGH") == CC.HIGH

    def test_baseline_reference_json_serializable(self):
        from agentic_runtime.evaluation.baseline_comparison import baseline_reference_to_dict

        payload = baseline_reference_to_dict(_make_ref())
        json.dumps(payload)

    def test_baseline_comparison_decision_json_serializable(self):
        from agentic_runtime.evaluation.baseline_comparison import baseline_comparison_decision_to_dict

        decision = compare_evaluation_results(
            comparison_id="cmp_json",
            baseline=_make_ref(baseline_id="baseline_001"),
            current=_make_ref(baseline_id="current_001"),
            baseline_result=_make_result(),
            current_result=_make_result(),
            dimensions=(ComparisonDimension.OUTCOME,),
        )
        json.dumps(baseline_comparison_decision_to_dict(decision))
