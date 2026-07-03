"""P3-FLOW-K harness evaluation core behavior tests.

An evaluation suite/run/case is deterministic fixture-backed grammar over
declared P3 contracts — never workflow execution.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FlowTruthLabel,
    HarnessScenarioKind,
    build_harness_evaluation_read_model,
    build_harness_evaluation_suite,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    derive_harness_evaluation_run,
)


def _fixture(kind=HarnessScenarioKind.READY_NODE_FIXTURE, label="ready"):
    return create_harness_scenario_fixture(
        fixture_kind=kind,
        fixture_label=label,
        target_contracts=("WorkflowGraph", "ReadyQueue"),
    )


def _suite():
    return build_harness_evaluation_suite(
        suite_label="p3-core",
        target_pack_range="P3.0-P3.18",
        cases=(
            create_harness_evaluation_case(
                case_label="ready-node", fixture=_fixture()
            ),
            create_harness_evaluation_case(
                case_label="intent",
                fixture=_fixture(
                    HarnessScenarioKind.SCHEDULING_INTENT_FIXTURE, "intent"
                ),
                target_contracts=("SchedulingIntent",),
            ),
        ),
    )


def test_suite_and_run_are_deterministic() -> None:
    first = derive_harness_evaluation_run(_suite())
    second = derive_harness_evaluation_run(_suite())
    assert first.evaluation_run_id == second.evaluation_run_id
    assert first == second


def test_run_aggregates_cases_and_target_contracts() -> None:
    run = derive_harness_evaluation_run(_suite(), run_label="nightly")
    assert run.run_label == "nightly"
    assert len(run.evaluation_case_ids) == 2
    assert run.target_contracts == (
        "ReadyQueue",
        "SchedulingIntent",
        "WorkflowGraph",
    )


def test_run_is_not_workflow_execution() -> None:
    run = derive_harness_evaluation_run(_suite())
    for forbidden_field in (
        "live_workflow",
        "workflow_executed",
        "runtime_submit_wired",
        "proof_available",
        "trace_verified",
        "production_ready",
    ):
        assert getattr(run, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(run, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(run, deterministic=False)


def test_case_requires_targets_and_uses_fixtures_only() -> None:
    case = create_harness_evaluation_case(
        case_label="ready-node", fixture=_fixture()
    )
    assert case.uses_dev_fixtures is True
    assert case.scenario_fixture_id.startswith("flksf-")
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(case, target_contracts=())
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(case, workflow_executed=True)


def test_suite_rejects_duplicates_and_emptiness() -> None:
    case = create_harness_evaluation_case(
        case_label="ready-node", fixture=_fixture()
    )
    with pytest.raises(AurelFlowValidationError):
        build_harness_evaluation_suite(
            suite_label="s", target_pack_range="P3", cases=(case, case)
        )
    with pytest.raises(AurelFlowValidationError):
        build_harness_evaluation_suite(
            suite_label="s", target_pack_range="P3", cases=()
        )


def test_read_model_carries_the_harness_boundary() -> None:
    read_model = build_harness_evaluation_read_model(
        derive_harness_evaluation_run(_suite())
    )
    assert read_model.case_count == 2
    assert read_model.target_contract_count == 3
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    assert read_model.boundary.evaluation_is_not_execution is True
    assert read_model.boundary.harness_result_is_not_proof is True
    assert read_model.boundary.coverage_is_not_production_readiness is True
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(
            read_model.boundary, evaluation_is_not_execution=False
        )
