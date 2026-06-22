"""Benchmark hygiene serialization tests — P1.5.8."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkRepresentativeness,
    assess_benchmark_hygiene,
    benchmark_fixture_boundary_to_dict,
    benchmark_hygiene_assessment_to_dict,
    benchmark_hygiene_decision_to_dict,
    benchmark_hygiene_policy_to_dict,
    benchmark_hygiene_report_to_dict,
    build_default_benchmark_hygiene_policy,
    build_p158_benchmark_hygiene_report,
    example_clean_benchmark_fixture_boundary,
    resolve_hygiene_decision,
)


def test_benchmark_fixture_boundary_json_serializable():
    boundary = example_clean_benchmark_fixture_boundary()
    payload = benchmark_fixture_boundary_to_dict(boundary)
    encoded = json.dumps(payload)
    assert "fixture_clean_001" in encoded
    assert isinstance(payload["source_refs"], list)


def test_benchmark_hygiene_policy_json_serializable():
    policy = build_default_benchmark_hygiene_policy()
    payload = benchmark_hygiene_policy_to_dict(policy)
    encoded = json.dumps(payload)
    assert "default_p158" in encoded
    assert payload["block_answer_key_exposure"] is True


def test_benchmark_hygiene_assessment_json_serializable():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        evidence_refs=("ev_001",),
    )
    payload = benchmark_hygiene_assessment_to_dict(assessment)
    encoded = json.dumps(payload)
    assert "a1" in encoded
    assert payload["hygiene_status"] in ("CLEAN", "ACCEPTABLE")
    assert isinstance(payload["evidence_refs"], list)


def test_benchmark_hygiene_decision_json_serializable():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    payload = benchmark_hygiene_decision_to_dict(decision)
    encoded = json.dumps(payload)
    assert "d1" in encoded
    assert "assessment" in payload
    assert payload["max_allowed_support_level"] in ("MODERATE", "STRONG")


def test_benchmark_hygiene_report_json_serializable():
    report = build_p158_benchmark_hygiene_report(sparse_hygiene_ready=True)
    payload = benchmark_hygiene_report_to_dict(report)
    encoded = json.dumps(payload)
    assert "P1.5.8" in encoded
    assert "P1.5.9" in encoded


def test_nested_assessment_serializes_deterministically():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert benchmark_hygiene_decision_to_dict(decision) == benchmark_hygiene_decision_to_dict(decision)


def test_enums_serialize_as_stable_strings_and_tuples_as_lists():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    payload = benchmark_hygiene_assessment_to_dict(assessment)
    assert isinstance(payload["hygiene_status"], str)
    assert isinstance(payload["contamination_types"], list)
    assert isinstance(payload["source_refs"], list)


def test_serialization_has_no_hidden_claim_mutation_side_effects():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    payload = benchmark_hygiene_assessment_to_dict(assessment)
    assert "claim_status" not in payload
    assert "VERIFIED" not in json.dumps(payload)
