"""P3-FLOW-K contract coverage matrix / scenario fixture behavior tests.

Coverage is closed-world and never production readiness; fixtures are
deterministic DEV_FIXTURE data, never live workflows.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    ContractCoverageArea,
    ContractCoverageStatus,
    FlowTruthLabel,
    HarnessScenarioKind,
    build_contract_coverage_matrix,
    build_contract_coverage_read_model,
    build_harness_evaluation_suite,
    build_harness_scenario_catalog,
    build_harness_scenario_read_model,
    create_contract_coverage_item,
    create_harness_evaluation_case,
    create_harness_scenario_fixture,
    derive_harness_evaluation_run,
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
                create_harness_evaluation_case(
                    case_label="c", fixture=fixture
                ),
            ),
        )
    )


def _matrix():
    return build_contract_coverage_matrix(
        run=_run(),
        coverage_items=(
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.WORKFLOW_GRAPH,
                status=ContractCoverageStatus.COVERED,
                evidence_note="test_p3_flow_a_workflow_graph.py",
            ),
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.SCHEDULING_INTENT,
                status=ContractCoverageStatus.PARTIAL,
                evidence_note="ready-state bridge from A scheduler pending",
            ),
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.P4_HANDOFF_CLARITY,
                status=ContractCoverageStatus.MISSING,
                evidence_note="no dedicated K case yet",
            ),
        ),
    )


def test_matrix_counts_statuses_deterministically() -> None:
    first = _matrix()
    second = _matrix()
    assert first.coverage_matrix_id == second.coverage_matrix_id
    assert first.covered_count == 1
    assert first.partial_count == 1
    assert first.missing_count == 1
    assert first.blocked_count == 0


def test_coverage_is_not_production_readiness_or_proof() -> None:
    matrix = _matrix()
    for forbidden_field in (
        "production_ready",
        "proof_available",
        "trace_verified",
    ):
        assert getattr(matrix, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(matrix, **{forbidden_field: True})


def test_matrix_rejects_duplicate_areas() -> None:
    item = create_contract_coverage_item(
        coverage_area=ContractCoverageArea.WORKFLOW_GRAPH,
        status=ContractCoverageStatus.COVERED,
        evidence_note="x",
    )
    with pytest.raises(AurelFlowValidationError):
        build_contract_coverage_matrix(run=_run(), coverage_items=(item, item))


def test_missing_or_blocked_items_must_explain_themselves() -> None:
    with pytest.raises(AurelFlowValidationError):
        create_contract_coverage_item(
            coverage_area=ContractCoverageArea.TOPOLOGY_RISK,
            status=ContractCoverageStatus.MISSING,
            evidence_note="",
        )


def test_coverage_vocabularies_are_closed_world() -> None:
    status_values = {status.value for status in ContractCoverageStatus}
    assert status_values == {
        "COVERED",
        "PARTIAL",
        "MISSING",
        "UNAVAILABLE",
        "BLOCKED",
        "ERROR",
    }
    area_values = {area.value for area in ContractCoverageArea}
    assert "SCHEDULING_INTENT" in area_values
    assert "COMPOUND_TOPOLOGY" in area_values
    assert "PRODUCTION_READY" not in area_values


def test_coverage_read_model_reports_full_coverage_honestly() -> None:
    read_model = build_contract_coverage_read_model(_matrix())
    assert read_model.area_count == 3
    assert read_model.fully_covered is False
    covered_only = build_contract_coverage_matrix(
        run=_run(),
        coverage_items=(
            create_contract_coverage_item(
                coverage_area=ContractCoverageArea.WORKFLOW_GRAPH,
                status=ContractCoverageStatus.COVERED,
                evidence_note="x",
            ),
        ),
    )
    assert build_contract_coverage_read_model(covered_only).fully_covered is True


def test_fixtures_are_dev_fixture_and_never_live() -> None:
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.RETRY_STORM_FIXTURE,
        fixture_label="storm",
        target_contracts=("RetryStormGuard",),
    )
    assert fixture.truth_label is FlowTruthLabel.DEV_FIXTURE
    for forbidden_field in (
        "live_data",
        "live_workflow",
        "production_simulation",
        "workflow_executed",
    ):
        assert getattr(fixture, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(fixture, **{forbidden_field: True})
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(
            fixture, truth_label=FlowTruthLabel.LIVE
        )


def test_catalog_rejects_duplicates_and_read_model_counts() -> None:
    fixture = create_harness_scenario_fixture(
        fixture_kind=HarnessScenarioKind.P4_HANDOFF_FIXTURE,
        fixture_label="handoff",
        target_contracts=("P4HandoffClarityFrame",),
    )
    with pytest.raises(AurelFlowValidationError):
        build_harness_scenario_catalog((fixture, fixture))
    catalog = build_harness_scenario_catalog((fixture,))
    assert catalog.contains_fixture(fixture.fixture_id) is True
    read_model = build_harness_scenario_read_model(catalog)
    assert read_model.fixture_count == 1
    assert read_model.fixture_kind_counts == (("P4_HANDOFF_FIXTURE", 1),)
    assert read_model.target_contract_count == 1
