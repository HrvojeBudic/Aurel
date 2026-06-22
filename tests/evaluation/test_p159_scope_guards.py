"""Scope guard tests — P1.5.9."""
from __future__ import annotations

import inspect

from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialCaseStatus,
    P159_INVARIANTS,
    build_default_adversarial_case_set,
    build_p159_adversarial_case_report,
    register_adversarial_case,
    resolve_adversarial_cases_for_subject,
    validate_adversarial_case,
)
from agentic_runtime.evaluation.adversarial_cases import (
    AdversarialCaseRegistry,
)
from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRecord,
    CapabilityEvidenceStatus,
    CapabilityEvidenceStrength,
)


def test_p159_does_not_execute_cases():
    src = inspect.getsource(register_adversarial_case) + inspect.getsource(resolve_adversarial_cases_for_subject)
    assert "run_case" not in src
    assert "execute_case" not in src


def test_p159_does_not_run_benchmarks():
    src = inspect.getsource(build_default_adversarial_case_set)
    assert "run_benchmark" not in src
    assert "execute_benchmark" not in src


def test_p159_does_not_create_evaluation_result():
    src = inspect.getsource(validate_adversarial_case) + inspect.getsource(register_adversarial_case)
    assert "EvaluationResult(" not in src


def test_p159_does_not_call_llm_or_tools():
    src = inspect.getsource(build_default_adversarial_case_set) + inspect.getsource(register_adversarial_case)
    assert "call_tool" not in src.lower()
    assert "llm" not in src.lower()


def test_p159_does_not_verify_capability():
    report = build_p159_adversarial_case_report()
    assert "verify capability" not in report.summary.lower()
    joined = "\n".join(P159_INVARIANTS).lower()
    assert "does not verify capability" in joined or "does not execute evaluation" in joined


def test_p159_does_not_mutate_claim_status():
    evidence = CapabilityEvidenceRecord(
        evidence_id="ev_001",
        kind=CapabilityEvidenceKind.EVALUATION_RESULT,
        status=CapabilityEvidenceStatus.USABLE,
        strength=CapabilityEvidenceStrength.STRONG,
        claim_id="claim_001",
    )
    registry = AdversarialCaseRegistry(
        registry_id="adv_registry_scope",
        cases=(),
        warnings=(),
        blockers=(),
        summary="scope test",
    )
    case = build_default_adversarial_case_set()[0]
    updated = register_adversarial_case(registry=registry, case=case)
    assert updated.cases[0].case_id == case.case_id
    assert evidence.claim_id == "claim_001"
    assert not hasattr(evidence, "claim_status")


def test_p159_does_not_create_verified_status():
    assert not hasattr(AdversarialCaseStatus, "VERIFIED")


def test_p159_does_not_introduce_numeric_score():
    report = build_p159_adversarial_case_report()
    case = build_default_adversarial_case_set()[0]
    assert not hasattr(report, "score")
    assert not hasattr(case, "score")
    assert not hasattr(case, "difficulty_score")


def test_p159_does_not_implement_sparse_context_compiler():
    src = inspect.getsource(build_default_adversarial_case_set)
    assert "SparseContextCompiler" not in src


def test_p159_does_not_implement_hub_runtime():
    src = inspect.getsource(build_default_adversarial_case_set)
    assert "hub_runtime" not in src.lower()


def test_p159_prepares_p1510_baseline_comparison():
    report = build_p159_adversarial_case_report()
    assert "P1.5.10" in report.next_module
    assert "Baseline Comparison" in report.next_module
