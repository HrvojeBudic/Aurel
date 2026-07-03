"""P3-FLOW-K no-production-claim boundary tests.

No K object can claim production readiness, release approval, or the final
P3 seal; readiness stays candidate-only and the K layer cannot certify.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

import agentic_runtime.aurel_flow as aurel_flow
from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    HarnessScenarioKind,
    P4HandoffReadinessCheck,
    QualityMetric,
    QualityMetricStatus,
    assess_p4_handoff_readiness,
    build_harness_evaluation_suite,
    build_harness_no_production_claim_boundary_proof,
    build_p4_readiness_not_p4_proof,
    build_runtime_quality_scorecard,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    create_quality_metric_item,
    derive_harness_evaluation_run,
)

_FLOW_PACKAGE_DIR = Path(aurel_flow.__file__).resolve().parent
_K_MODULES = (
    "flow_harness_evaluation.py",
    "flow_boundary_probes.py",
    "flow_quality_ops.py",
    "flow_harness_projection.py",
)


def _run():
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.READY_NODE_FIXTURE,
        fixture_label="ready",
        target_contracts=("WorkflowGraph",),
    )
    return derive_harness_evaluation_run(
        build_harness_evaluation_suite(
            suite_label="s",
            target_pack_range="P3",
            cases=(
                create_harness_evaluation_case(case_label="c", fixture=fixture),
            ),
        )
    )


def test_k_sources_never_default_production_or_seal_to_true() -> None:
    forbidden_assignments = (
        r"production_ready\s*:\s*bool\s*=\s*True",
        r"release_approved\s*:\s*bool\s*=\s*True",
        r"final_seal_performed\s*:\s*bool\s*=\s*True",
        r"p4_implemented\s*:\s*bool\s*=\s*True",
        r"ci_enforced\s*:\s*bool\s*=\s*True",
    )
    for filename in _K_MODULES:
        source = (_FLOW_PACKAGE_DIR / filename).read_text(encoding="utf-8")
        for pattern in forbidden_assignments:
            assert not re.search(pattern, source), (
                f"{filename} matches forbidden pattern {pattern!r}"
            )


def test_scorecard_cannot_claim_release_or_production() -> None:
    scorecard = build_runtime_quality_scorecard(
        run=_run(),
        metric_items=(
            create_quality_metric_item(
                metric=QualityMetric.CONTRACT_COMPLETENESS,
                status=QualityMetricStatus.STRONG,
                rationale="all dispatched contracts represented",
            ),
        ),
    )
    for forbidden_field in (
        "release_approved",
        "production_ready",
        "operator_approval_granted",
        "score_is_proof",
    ):
        assert getattr(scorecard, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(scorecard, **{forbidden_field: True})


def test_p4_readiness_stays_candidate_only_even_when_all_checks_pass() -> None:
    assessment = assess_p4_handoff_readiness(
        run=_run(),
        readiness_check_results=(
            (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
            (P4HandoffReadinessCheck.NO_RUNTIME_SUBMIT_WIRED, True),
        ),
    )
    assert assessment.ready_candidate is True
    assert assessment.p4_implemented is False
    assert assessment.execution_available is False


def test_no_production_claim_proof_is_all_false_and_fail_closed() -> None:
    proof = build_harness_no_production_claim_boundary_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "production_ready",
        "release_approved",
        "operator_approval_granted",
        "final_seal_performed",
        "live_claimed",
        "trace_verified_claimed",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_p4_readiness_not_p4_proof_is_all_false_and_fail_closed() -> None:
    proof = build_p4_readiness_not_p4_proof()
    for boundary_field in (
        "is_p5_trace_proof",
        "p4_implemented",
        "runtime_submit_wired",
        "dispatch_available",
        "execution_available",
        "worker_allocated",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
