"""P1.5.10 serialization tests — Baseline Comparison Model."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.baseline_comparison import (
    BaselineComparisonInput,
    ComparisonDimension,
    baseline_comparison_input_to_dict,
    baseline_comparison_report_to_dict,
    build_p1510_baseline_comparison_report,
    example_active_baseline_reference,
    example_current_baseline_reference,
)
from tests.evaluation.test_baseline_reference import _make_ref


class TestSerialization:
    def test_report_serialization(self):
        report = build_p1510_baseline_comparison_report(
            comparisons_created=2,
            baseline_refs_created=2,
            sparse_comparison_ready=True,
        )
        payload = baseline_comparison_report_to_dict(report)
        json.dumps(payload)
        assert payload["status"] == "READY"
        assert payload["sparse_comparison_ready"] is True
        assert "P1.5.11" in payload["next_module"]

    def test_comparison_input_serialization(self):
        inp = BaselineComparisonInput(
            comparison_id="cmp_serial",
            baseline=example_active_baseline_reference(),
            current_ref=example_current_baseline_reference(),
            dimensions=(ComparisonDimension.OUTCOME, ComparisonDimension.VERDICT),
            baseline_result=None,
            current_result=None,
            baseline_evidence_refs=(),
            current_evidence_refs=(),
            baseline_hygiene_refs=(),
            current_hygiene_refs=(),
            baseline_adversarial_case_refs=(),
            current_adversarial_case_refs=(),
            warnings=(),
            blockers=(),
            summary="serialization test",
        )
        payload = baseline_comparison_input_to_dict(inp)
        json.dumps(payload)
        assert payload["comparison_id"] == "cmp_serial"
        assert len(payload["dimensions"]) == 2
