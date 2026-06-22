"""P1.5.1 serialization tests."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.evaluation_objects import (
    EvaluationCriterionResult,
    EvaluationEvidenceQuality,
    EvaluationOutcome,
    EvaluationVerdict,
    aggregate_evaluation_results,
    build_p151_object_model_report,
    evaluation_criterion_result_to_dict,
    evaluation_object_model_report_to_dict,
    evaluation_result_set_to_dict,
    evaluation_result_to_dict,
    example_supported_evaluation_result,
    resolve_evaluation_result_from_criteria,
)


def test_criterion_result_serializes():
    cr = EvaluationCriterionResult(
        criterion_id="c1", outcome=EvaluationOutcome.PASSED,
        verdict=EvaluationVerdict.SUPPORTED,
        evidence_quality=EvaluationEvidenceQuality.ADEQUATE,
        evidence_refs=("ev1",),
    )
    d = evaluation_criterion_result_to_dict(cr)
    p = json.loads(json.dumps(d))
    assert p["criterion_id"] == "c1"
    assert p["outcome"] == "PASSED"


def test_result_set_serializes():
    r = example_supported_evaluation_result()
    rs = aggregate_evaluation_results(result_set_id="rs1", run_id="run1", results=(r,))
    d = evaluation_result_set_to_dict(rs)
    p = json.loads(json.dumps(d))
    assert p["result_set_id"] == "rs1"
    assert p["aggregate_outcome"] == "PASSED"


def test_object_model_report_serializes():
    report = build_p151_object_model_report()
    d = evaluation_object_model_report_to_dict(report)
    p = json.loads(json.dumps(d))
    assert p["status"] == "READY"
    assert "P1.5.2" in p["next_module"]


def test_resolved_result_roundtrip():
    r = resolve_evaluation_result_from_criteria(
        result_id="r1", run_id="run1",
        criterion_results=(
            EvaluationCriterionResult(
                "c1", EvaluationOutcome.PASSED, EvaluationVerdict.SUPPORTED,
                EvaluationEvidenceQuality.STRONG, evidence_refs=("ev1",),
            ),
        ),
        evidence_refs=("ev1",),
    )
    d = evaluation_result_to_dict(r)
    assert d["verdict"] == "SUPPORTED"
    assert d["verdict"] != "VERIFIED"
