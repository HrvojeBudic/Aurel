"""Sparse hygiene readiness tests — P1.5.8."""
from __future__ import annotations

import inspect
from dataclasses import replace

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkContaminationType,
    BenchmarkHygieneStatus,
    BenchmarkRepresentativeness,
    assess_benchmark_hygiene,
    build_p158_benchmark_hygiene_report,
    example_clean_benchmark_fixture_boundary,
    resolve_hygiene_decision,
)
from agentic_runtime.evaluation.evidence_claim_binding import ClaimSupportLevel


def test_context_leakage_detected_as_sparse_hygiene_risk():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        sparse_context_refs=("context_leakage:fixture_clean",),
    )
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert BenchmarkContaminationType.CONTEXT_LEAKAGE in assessment.contamination_types
    assert assessment.hygiene_status in (
        BenchmarkHygieneStatus.DEGRADED,
        BenchmarkHygieneStatus.CONTAMINATED,
        BenchmarkHygieneStatus.BLOCKED,
    )


def test_retrieval_leakage_detected():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        sparse_context_refs=("retrieval_leakage:fixture_clean",),
    )
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert BenchmarkContaminationType.RETRIEVAL_LEAKAGE in assessment.contamination_types


def test_lost_context_risk_can_degrade_hygiene():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        sparse_context_refs=("lost_context:fixture_clean",),
    )
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert BenchmarkContaminationType.LOST_CONTEXT_RISK in assessment.contamination_types
    assert decision.max_allowed_support_level == ClaimSupportLevel.WEAK


def test_contradiction_omission_can_warn_or_degrade():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        sparse_context_refs=("contradiction_omission:fixture_clean",),
    )
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert BenchmarkContaminationType.CONTRADICTION_OMISSION in assessment.contamination_types
    assert assessment.hygiene_status == BenchmarkHygieneStatus.DEGRADED


def test_multi_hop_edge_missing_can_warn_or_degrade():
    boundary = replace(
        example_clean_benchmark_fixture_boundary(),
        sparse_context_refs=("multi_hop_edge_missing:fixture_clean",),
    )
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
    )
    assert BenchmarkContaminationType.MULTI_HOP_EDGE_MISSING in assessment.contamination_types
    assert assessment.hygiene_status == BenchmarkHygieneStatus.DEGRADED


def test_sparse_hygiene_does_not_run_sparse_compiler():
    src = inspect.getsource(assess_benchmark_hygiene)
    assert "SparseContextCompiler" not in src
    assert "compile_sparse_context" not in src


def test_sparse_hygiene_does_not_claim_ssa_implemented():
    report = build_p158_benchmark_hygiene_report(sparse_hygiene_ready=True)
    assert "ssa" not in report.summary.lower()


def test_sparse_hygiene_does_not_claim_subquadratic_model_implemented():
    report = build_p158_benchmark_hygiene_report(sparse_hygiene_ready=True)
    assert "subquadratic" not in report.summary.lower()
