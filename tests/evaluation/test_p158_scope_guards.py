"""Scope guard tests — P1.5.8."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.benchmark_hygiene import (
    BenchmarkHygieneStatus,
    P158_INVARIANTS,
    apply_hygiene_to_evidence_binding,
    assess_benchmark_hygiene,
    build_p158_benchmark_hygiene_report,
    example_clean_benchmark_fixture_boundary,
    resolve_hygiene_decision,
)
from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
)
from agentic_runtime.evaluation.evidence_claim_binding import (
    ClaimBindingStatus,
    ClaimSupportLevel,
    bind_evidence_to_claim,
)


def test_p158_does_not_run_benchmark():
    src = inspect.getsource(assess_benchmark_hygiene)
    assert "run_benchmark" not in src
    assert "execute_benchmark" not in src


def test_p158_does_not_execute_evaluation():
    src = inspect.getsource(resolve_hygiene_decision)
    assert "execute_evaluation" not in src
    assert "run_evaluation" not in src


def test_p158_does_not_create_evaluation_result():
    src = inspect.getsource(assess_benchmark_hygiene) + inspect.getsource(resolve_hygiene_decision)
    assert "EvaluationResult(" not in src


def test_p158_does_not_call_llm_or_tools():
    src = inspect.getsource(assess_benchmark_hygiene) + inspect.getsource(resolve_hygiene_decision)
    assert "call_tool" not in src.lower()
    assert "llm" not in src.lower()


def test_p158_does_not_verify_capability():
    report = build_p158_benchmark_hygiene_report()
    assert "verify capability" not in report.summary.lower()
    assert "verified" not in report.summary.lower()


def test_p158_does_not_mutate_claim_status():
    evidence = CapabilityEvidenceRecord(
        evidence_id="ev_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
        claim_id="claim_001",
    )
    binding = bind_evidence_to_claim(binding_id="b1", claim_id="claim_001", evidence=evidence)
    decision = resolve_hygiene_decision(
        decision_id="d1",
        assessment=assess_benchmark_hygiene(
            assessment_id="a1",
            boundary=example_clean_benchmark_fixture_boundary(),
        ),
    )
    changed = apply_hygiene_to_evidence_binding(binding=binding, hygiene_decision=decision)
    assert changed.claim_id == binding.claim_id
    assert not hasattr(changed, "claim_status")


def test_p158_does_not_create_verified_status():
    assert not hasattr(ClaimBindingStatus, "VERIFIED")
    assert not hasattr(BenchmarkHygieneStatus, "VERIFIED")


def test_p158_does_not_introduce_numeric_score():
    assessment = assess_benchmark_hygiene(
        assessment_id="a1",
        boundary=example_clean_benchmark_fixture_boundary(),
    )
    decision = resolve_hygiene_decision(decision_id="d1", assessment=assessment)
    assert not hasattr(assessment, "score")
    assert not hasattr(decision, "score")
    assert decision.max_allowed_support_level in (
        ClaimSupportLevel.NONE,
        ClaimSupportLevel.WEAK,
        ClaimSupportLevel.MODERATE,
        ClaimSupportLevel.STRONG,
        ClaimSupportLevel.UNKNOWN,
    )


def test_p158_does_not_implement_sparse_context_compiler():
    src = inspect.getsource(assess_benchmark_hygiene)
    assert "SparseContextCompiler" not in src


def test_p158_does_not_implement_hub_runtime():
    src = inspect.getsource(assess_benchmark_hygiene)
    assert "hub_runtime" not in src.lower()


def test_p158_prepares_p159_adversarial_eval_cases():
    report = build_p158_benchmark_hygiene_report()
    assert "P1.5.9" in report.next_module
    assert "Adversarial Evaluation Cases" in report.next_module


def test_p158_sparse_invariants_document_non_goals():
    joined = "\n".join(P158_INVARIANTS)
    assert "Sparse Context Compiler" in joined
    assert "P1.5.9" in joined
