"""P3-FLOW-K P4 handoff readiness behavior tests.

A P4 readiness assessment makes gaps visible without implementing P4:
runtime.submit stays unwired, nothing dispatches, no worker is allocated,
and every unsatisfied check must carry an explaining gap.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    HarnessScenarioKind,
    P4HandoffReadinessCheck,
    assess_p4_handoff_readiness,
    build_harness_evaluation_suite,
    build_p4_handoff_read_model,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    create_p4_handoff_gap,
    create_p4_handoff_risk,
    derive_harness_evaluation_run,
)


def _run():
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.P4_HANDOFF_FIXTURE,
        fixture_label="handoff",
        target_contracts=("P4HandoffClarityFrame",),
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


def _assessment(*, with_gap: bool):
    checks = (
        (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
        (P4HandoffReadinessCheck.SERVICE_REF_CONSUMPTION_SURFACE_EXISTS, True),
        (P4HandoffReadinessCheck.NO_RUNTIME_SUBMIT_WIRED, True),
        (
            P4HandoffReadinessCheck.P4_MINIMAL_BRIDGE_INPUTS_VISIBLE,
            not with_gap,
        ),
    )
    gaps = ()
    if with_gap:
        gaps = (
            create_p4_handoff_gap(
                readiness_check=(
                    P4HandoffReadinessCheck.P4_MINIMAL_BRIDGE_INPUTS_VISIBLE
                ),
                detail="bridge inputs not yet enumerated for this run",
            ),
        )
    return assess_p4_handoff_readiness(
        run=_run(),
        readiness_check_results=checks,
        gaps=gaps,
        risks=(
            create_p4_handoff_risk(
                risk_label="CALLER_DECLARED_CAPABILITIES",
                detail="P9 must never trust capability envelopes as permission",
            ),
        ),
        minimal_bridge_inputs=("SchedulingTopologyBridge",),
    )


def test_all_satisfied_checks_yield_a_ready_candidate_only() -> None:
    assessment = _assessment(with_gap=False)
    assert assessment.ready_candidate is True
    assert assessment.p4_implemented is False
    assert assessment.runtime_submit_wired is False
    assert assessment.dispatch_available is False
    assert assessment.execution_available is False
    assert assessment.worker_allocated is False


def test_unsatisfied_check_makes_the_gap_visible_and_blocks_readiness() -> None:
    assessment = _assessment(with_gap=True)
    assert assessment.ready_candidate is False
    assert len(assessment.gaps) == 1
    assert (
        assessment.gaps[0].readiness_check
        is P4HandoffReadinessCheck.P4_MINIMAL_BRIDGE_INPUTS_VISIBLE
    )


def test_unsatisfied_check_without_a_gap_is_unconstructible() -> None:
    with pytest.raises(AurelFlowValidationError):
        assess_p4_handoff_readiness(
            run=_run(),
            readiness_check_results=(
                (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, False),
            ),
            gaps=(),
        )


def test_duplicate_checks_are_unconstructible() -> None:
    with pytest.raises(AurelFlowValidationError):
        assess_p4_handoff_readiness(
            run=_run(),
            readiness_check_results=(
                (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
                (P4HandoffReadinessCheck.SCHEDULING_INTENT_EXISTS, True),
            ),
        )


def test_readiness_is_not_p4_structurally() -> None:
    assessment = _assessment(with_gap=False)
    for forbidden_field in (
        "p4_implemented",
        "runtime_submit_wired",
        "dispatch_available",
        "execution_available",
        "worker_allocated",
    ):
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(assessment, **{forbidden_field: True})
    for risk in assessment.risks:
        assert risk.mitigated is False
        assert risk.p4_implemented is False


def test_assessment_is_deterministic_and_read_model_counts() -> None:
    first = _assessment(with_gap=True)
    second = _assessment(with_gap=True)
    assert first.p4_handoff_readiness_id == second.p4_handoff_readiness_id
    read_model = build_p4_handoff_read_model(first)
    assert read_model.check_count == 4
    assert read_model.satisfied_count == 3
    assert read_model.gap_count == 1
    assert read_model.risk_count == 1
    assert read_model.ready_candidate is False
    assert read_model.p4_implemented is False
