"""Benchmark fixture boundary validation tests — P1.5.8."""
from __future__ import annotations

from dataclasses import replace

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkContaminationType,
    BenchmarkHygieneRisk,
    classify_contamination_risk,
    example_clean_benchmark_fixture_boundary,
    validate_benchmark_fixture_boundary,
)


def test_validate_fixture_boundary_rejects_empty_fixture_id():
    boundary = replace(example_clean_benchmark_fixture_boundary(), fixture_id="")
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("fixture_id" in issue for issue in issues)


def test_validate_fixture_boundary_rejects_empty_fixture_name():
    boundary = replace(example_clean_benchmark_fixture_boundary(), fixture_name="")
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("fixture_name" in issue for issue in issues)


def test_missing_source_refs_warns_or_blocks():
    boundary = replace(example_clean_benchmark_fixture_boundary(), source_refs=(), dataset_refs=())
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("provenance" in issue for issue in issues)


def test_gold_label_in_allowed_context_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        allowed_context_refs=("source:benchmark_spec", "gold:fixture_clean"),
        forbidden_context_refs=("answer_key:fixture_clean",),
    )
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("gold label" in issue for issue in issues)
    risk, types = classify_contamination_risk(boundary)
    assert risk == BenchmarkHygieneRisk.HIGH
    assert BenchmarkContaminationType.FIXTURE_LEAKAGE in types


def test_expected_output_in_allowed_context_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        allowed_context_refs=("source:benchmark_spec", "expected:fixture_clean"),
        forbidden_context_refs=("answer_key:fixture_clean",),
    )
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("expected output" in issue for issue in issues)
    risk, types = classify_contamination_risk(boundary)
    assert risk == BenchmarkHygieneRisk.HIGH
    assert BenchmarkContaminationType.CONTEXT_LEAKAGE in types


def test_answer_key_in_allowed_context_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        allowed_context_refs=("source:benchmark_spec", "answer_key:fixture_clean"),
    )
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("answer key exposure" in issue for issue in issues)
    risk, types = classify_contamination_risk(boundary)
    assert risk == BenchmarkHygieneRisk.CRITICAL
    assert BenchmarkContaminationType.ANSWER_KEY_EXPOSURE in types


def test_forbidden_context_overlap_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        allowed_context_refs=("source:benchmark_spec", "gold:fixture_clean"),
        forbidden_context_refs=("gold:fixture_clean",),
    )
    issues = validate_benchmark_fixture_boundary(boundary)
    assert any("forbidden context" in issue for issue in issues)
    risk, types = classify_contamination_risk(boundary)
    assert risk == BenchmarkHygieneRisk.CRITICAL
    assert BenchmarkContaminationType.CONTEXT_LEAKAGE in types


def test_retrieval_leakage_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        known_exposure_refs=("retrieval_leakage:fixture_clean",),
    )
    risk, types = classify_contamination_risk(boundary)
    assert risk == BenchmarkHygieneRisk.HIGH
    assert BenchmarkContaminationType.RETRIEVAL_LEAKAGE in types


def test_source_overexposure_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        known_exposure_refs=("source_overexposure:fixture_clean",),
    )
    risk, types = classify_contamination_risk(boundary)
    assert risk == BenchmarkHygieneRisk.MEDIUM
    assert BenchmarkContaminationType.SOURCE_OVEREXPOSURE in types


def test_unknown_source_creates_unknown_or_medium_risk():
    boundary = replace(example_clean_benchmark_fixture_boundary(), source_refs=(), dataset_refs=())
    risk, types = classify_contamination_risk(boundary)
    assert risk in (BenchmarkHygieneRisk.UNKNOWN, BenchmarkHygieneRisk.MEDIUM)
    assert BenchmarkContaminationType.UNKNOWN in types


def test_clean_fixture_low_or_no_risk():
    risk, types = classify_contamination_risk(example_clean_benchmark_fixture_boundary())
    assert risk in (BenchmarkHygieneRisk.NONE, BenchmarkHygieneRisk.LOW)
    assert types == (BenchmarkContaminationType.NONE,)
