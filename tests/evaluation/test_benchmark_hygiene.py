"""Core benchmark hygiene tests — P1.5.8."""
from __future__ import annotations

from dataclasses import replace

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkContaminationType,
    BenchmarkFreshnessStatus,
    BenchmarkHygieneRisk,
    BenchmarkHygieneStatus,
    BenchmarkRepresentativeness,
    assess_benchmark_hygiene,
    build_default_benchmark_hygiene_policy,
    example_clean_benchmark_fixture_boundary,
    example_leaky_benchmark_fixture_boundary,
)


def test_benchmark_hygiene_status_closed_world():
    assert {s.value for s in BenchmarkHygieneStatus} == {
        "CLEAN",
        "ACCEPTABLE",
        "DEGRADED",
        "CONTAMINATED",
        "STALE",
        "INSUFFICIENT_PROVENANCE",
        "BLOCKED",
        "UNKNOWN",
    }


def test_benchmark_hygiene_risk_closed_world():
    assert {r.value for r in BenchmarkHygieneRisk} == {
        "NONE",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        "UNKNOWN",
    }


def test_contamination_type_closed_world():
    assert {t.value for t in BenchmarkContaminationType} == {
        "NONE",
        "TRAINING_CONTAMINATION",
        "CONTEXT_LEAKAGE",
        "FIXTURE_LEAKAGE",
        "ANSWER_KEY_EXPOSURE",
        "RETRIEVAL_LEAKAGE",
        "SOURCE_OVEREXPOSURE",
        "OPERATOR_HINT_LEAKAGE",
        "OVERFIT_FIXTURE",
        "STALE_FIXTURE",
        "DUPLICATE_CASE",
        "LOST_CONTEXT_RISK",
        "CONTRADICTION_OMISSION",
        "MULTI_HOP_EDGE_MISSING",
        "UNKNOWN",
    }


def test_freshness_status_closed_world():
    assert {s.value for s in BenchmarkFreshnessStatus} == {
        "CURRENT",
        "RECENT",
        "AGING",
        "STALE",
        "EXPIRED",
        "UNKNOWN",
    }


def test_representativeness_closed_world():
    assert {r.value for r in BenchmarkRepresentativeness} == {
        "REPRESENTATIVE",
        "PARTIAL",
        "NARROW",
        "SYNTHETIC_ONLY",
        "TOY_ONLY",
        "UNKNOWN",
    }


def test_default_hygiene_policy_safe_values():
    policy = build_default_benchmark_hygiene_policy()
    assert policy.require_fixture_provenance is True
    assert policy.block_high_contamination is True
    assert policy.block_answer_key_exposure is True
    assert policy.block_unknown_source_for_strong_support is True
    assert policy.downgrade_stale_benchmarks is True
    assert policy.require_negative_controls_for_strong_support is True
    assert policy.require_representative_fixture_for_strong_support is True


def test_assess_clean_fixture_acceptable_or_clean():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert assessment.hygiene_status in (
        BenchmarkHygieneStatus.CLEAN,
        BenchmarkHygieneStatus.ACCEPTABLE,
    )
    assert assessment.contamination_risk == BenchmarkHygieneRisk.NONE


def test_assess_contaminated_fixture_blocked_or_contaminated():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_leaky_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert assessment.hygiene_status in (
        BenchmarkHygieneStatus.BLOCKED,
        BenchmarkHygieneStatus.CONTAMINATED,
    )
    assert assessment.contamination_risk == BenchmarkHygieneRisk.CRITICAL
    assert BenchmarkContaminationType.ANSWER_KEY_EXPOSURE in assessment.contamination_types


def test_assess_stale_fixture_degraded_or_stale():
    boundary = replace(example_clean_benchmark_fixture_boundary(), updated_at="stale")
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert assessment.hygiene_status == BenchmarkHygieneStatus.STALE


def test_assess_unknown_provenance_insufficient():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        source_refs=(),
        dataset_refs=(),
    )
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert assessment.hygiene_status == BenchmarkHygieneStatus.INSUFFICIENT_PROVENANCE
    assert assessment.contamination_risk == BenchmarkHygieneRisk.UNKNOWN


def test_assess_narrow_representativeness_downgrades():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.NARROW,
    )
    assert assessment.hygiene_status == BenchmarkHygieneStatus.DEGRADED


def test_assessment_no_numeric_score():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert not hasattr(assessment, "score")
    assert "score=" not in str(assessment).lower()
