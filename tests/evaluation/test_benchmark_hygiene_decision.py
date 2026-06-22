"""Benchmark hygiene decision tests — P1.5.8."""
from __future__ import annotations

from dataclasses import replace

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkRepresentativeness,
    assess_benchmark_hygiene,
    build_default_benchmark_hygiene_policy,
    example_clean_benchmark_fixture_boundary,
    example_leaky_benchmark_fixture_boundary,
    resolve_hygiene_decision,
)
from agentic_runtime.evaluation.evidence_claim_binding import (
    ClaimBindingRelationship,
    ClaimBindingStatus,
    ClaimSupportLevel,
)


def test_critical_contamination_blocks_claim_support():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_leaky_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert decision.evidence_usable_for_claim_support is False
    assert decision.max_allowed_support_level == ClaimSupportLevel.NONE
    assert decision.recommended_binding_relationship == ClaimBindingRelationship.BLOCKS
    assert decision.recommended_binding_status == ClaimBindingStatus.BLOCKED


def test_high_contamination_blocks_or_limits_support():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        allowed_context_refs=("source:benchmark_spec", "gold:fixture_clean"),
        forbidden_context_refs=("answer_key:fixture_clean",),
    )
    policy = replace(build_default_benchmark_hygiene_policy(), block_high_contamination=False)
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        policy=policy,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment, policy=policy)
    assert decision.max_allowed_support_level == ClaimSupportLevel.WEAK
    assert decision.recommended_binding_relationship == ClaimBindingRelationship.INSUFFICIENT


def test_degraded_hygiene_caps_support():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.NARROW,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert decision.evidence_usable_for_claim_support is True
    assert decision.max_allowed_support_level == ClaimSupportLevel.MODERATE


def test_stale_hygiene_caps_support():
    boundary = replace(example_clean_benchmark_fixture_boundary(), updated_at="stale")
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert decision.max_allowed_support_level == ClaimSupportLevel.WEAK
    assert decision.recommended_binding_status == ClaimBindingStatus.STALE


def test_insufficient_provenance_caps_support():
    boundary = replace(example_clean_benchmark_fixture_boundary(), source_refs=(), dataset_refs=())
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert decision.max_allowed_support_level == ClaimSupportLevel.WEAK
    assert decision.recommended_binding_relationship == ClaimBindingRelationship.INSUFFICIENT


def test_clean_hygiene_allows_moderate_or_strong_support():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert decision.evidence_usable_for_claim_support is True
    assert decision.max_allowed_support_level in (
        ClaimSupportLevel.MODERATE,
        ClaimSupportLevel.STRONG,
    )


def test_hygiene_decision_no_numeric_score():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert not hasattr(decision, "score")
    assert "score=" not in str(decision).lower()
