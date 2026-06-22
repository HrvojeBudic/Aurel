"""P1.5.10 baseline comparison policy and input validation tests."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.baseline_comparison import (
    BaselineComparisonInput,
    BaselineComparisonPolicy,
    BaselineReferenceKind,
    BaselineStatus,
    ComparisonDimension,
    build_default_baseline_comparison_policy,
    validate_baseline_comparison_input,
)
from tests.evaluation.test_baseline_reference import _make_ref


class TestBaselineComparisonPolicy:
    def test_default_policy_disallows_numeric_scores(self):
        policy = build_default_baseline_comparison_policy()
        assert policy.allow_numeric_scores is False
        assert policy.require_same_baseline_kind is True
        assert policy.require_hygiene_for_improvement is True
        assert policy.require_adversarial_coverage_for_improvement is True


class TestBaselineComparisonInputValidation:
    def _make_input(self, **kwargs) -> BaselineComparisonInput:
        defaults = {
            "comparison_id": "cmp_001",
            "baseline": _make_ref(baseline_id="baseline_001"),
            "current_ref": _make_ref(baseline_id="current_001"),
            "dimensions": (ComparisonDimension.OUTCOME,),
            "baseline_result": None,
            "current_result": None,
            "baseline_evidence_refs": (),
            "current_evidence_refs": (),
            "baseline_hygiene_refs": (),
            "current_hygiene_refs": (),
            "baseline_adversarial_case_refs": (),
            "current_adversarial_case_refs": (),
            "warnings": (),
            "blockers": (),
            "summary": "comparison input",
        }
        defaults.update(kwargs)
        return BaselineComparisonInput(**defaults)

    def test_comparison_input_requires_comparison_id(self):
        issues = validate_baseline_comparison_input(self._make_input(comparison_id=""))
        assert any("comparison_id must not be empty" in i for i in issues)

    def test_comparison_input_requires_dimensions(self):
        issues = validate_baseline_comparison_input(self._make_input(dimensions=()))
        assert any("requires at least one dimension" in i for i in issues)

    def test_unknown_dimension_blocks_or_warns(self):
        issues = validate_baseline_comparison_input(
            self._make_input(dimensions=(ComparisonDimension.UNKNOWN,))
        )
        assert any("UNKNOWN dimension" in i for i in issues)

    def test_kind_mismatch_blocks_when_policy_requires_same_kind(self):
        issues = validate_baseline_comparison_input(
            self._make_input(
                baseline=_make_ref(baseline_id="b1", kind=BaselineReferenceKind.EVALUATION_RESULT),
                current_ref=_make_ref(
                    baseline_id="c1",
                    kind=BaselineReferenceKind.ADVERSARIAL_COVERAGE,
                ),
            )
        )
        assert any("kind mismatch" in i for i in issues)

    def test_numeric_score_usage_rejected(self):
        issues = validate_baseline_comparison_input(
            self._make_input(summary="baseline_delta = +14.6 percent improvement")
        )
        assert any("numeric score" in i for i in issues)

    def test_blocked_baseline_blocks_comparison(self):
        issues = validate_baseline_comparison_input(
            self._make_input(
                baseline=_make_ref(
                    status=BaselineStatus.BLOCKED,
                    blockers=("blocked",),
                )
            )
        )
        assert any("blocks comparison" in i for i in issues)

    def test_blocked_current_ref_blocks_comparison(self):
        issues = validate_baseline_comparison_input(
            self._make_input(
                current_ref=_make_ref(
                    baseline_id="current_blocked",
                    status=BaselineStatus.BLOCKED,
                    blockers=("blocked",),
                )
            )
        )
        assert any("blocks comparison" in i for i in issues)

    def test_policy_json_serializable(self):
        from agentic_runtime.evaluation.baseline_comparison import baseline_comparison_policy_to_dict

        payload = baseline_comparison_policy_to_dict(build_default_baseline_comparison_policy())
        json.dumps(payload)
