"""P3-FLOW-L boundary exit audit behavior tests.

The exit audit is a read-only category -> forbidden-attribute sweep: a FAIL
names its offender, an undeclared category is honestly NOT_APPLICABLE, and
the audit itself never enforces, mutates, or certifies anything.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    BoundaryExitCategory,
    FlowTruthLabel,
    P3AuditStatus,
    build_default_p3_pack_coverage_items,
    build_p3_coverage_summary,
    build_p4_execution_handoff_package,
    build_unavailable_systems_ledger,
    describe_execution_request_candidate,
    map_runtime_submit_boundary,
    run_boundary_exit_audit,
)


def _l_subjects():
    return (
        build_p3_coverage_summary(build_default_p3_pack_coverage_items()),
        build_unavailable_systems_ledger(),
        build_p4_execution_handoff_package(),
        map_runtime_submit_boundary(),
        describe_execution_request_candidate(
            candidate_label="demo", source_intent_ref="intent-1"
        ),
    )


def test_audit_passes_over_honest_l_objects() -> None:
    read_model = run_boundary_exit_audit(_l_subjects())
    assert read_model.all_applicable_passed is True
    assert read_model.failing_category_values == ()
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY
    statuses = {
        finding.category: finding.status for finding in read_model.findings
    }
    assert set(statuses) == set(BoundaryExitCategory)
    for category in (
        BoundaryExitCategory.NO_RUNTIME_SUBMIT,
        BoundaryExitCategory.NO_EXECUTION,
        BoundaryExitCategory.NO_DISPATCH,
        BoundaryExitCategory.NO_PRODUCTION_CLAIM,
        BoundaryExitCategory.NO_P4_IMPLEMENTATION,
        BoundaryExitCategory.NO_PERSISTENCE_IMPLEMENTATION,
    ):
        assert statuses[category] is P3AuditStatus.PASS


@dataclass(frozen=True)
class _ExecutingFake:
    workflow_executed: bool = True
    dispatch_available: bool = True
    runtime_submit_called: bool = True


def test_audit_fails_an_executing_fake_with_named_offenders() -> None:
    read_model = run_boundary_exit_audit((_ExecutingFake(),))
    assert read_model.all_applicable_passed is False
    failing = set(read_model.failing_category_values)
    assert BoundaryExitCategory.NO_EXECUTION.value in failing
    assert BoundaryExitCategory.NO_DISPATCH.value in failing
    assert BoundaryExitCategory.NO_RUNTIME_SUBMIT.value in failing
    fail_details = {
        finding.category: finding.detail
        for finding in read_model.findings
        if finding.status is P3AuditStatus.FAIL
    }
    assert (
        "_ExecutingFake.workflow_executed"
        in fail_details[BoundaryExitCategory.NO_EXECUTION]
    )


def test_undeclared_categories_are_honestly_not_applicable() -> None:
    @dataclass(frozen=True)
    class _NarrowSubject:
        workflow_executed: bool = False

    read_model = run_boundary_exit_audit((_NarrowSubject(),))
    statuses = {
        finding.category: finding.status for finding in read_model.findings
    }
    assert statuses[BoundaryExitCategory.NO_EXECUTION] is P3AuditStatus.PASS
    assert (
        statuses[BoundaryExitCategory.NO_NETWORK]
        is P3AuditStatus.NOT_APPLICABLE
    )
    # NOT_APPLICABLE never counts as failure
    assert read_model.all_applicable_passed is True


def test_audit_is_read_only_and_never_enforcement() -> None:
    read_model = run_boundary_exit_audit(_l_subjects())
    assert read_model.read_only is True
    with pytest.raises(AurelFlowValidationError):
        dataclasses.replace(read_model, read_only=False)
    for forbidden_field in (
        "enforcement_performed",
        "mutation_performed",
        "runtime_policy_changed",
        "production_ready",
    ):
        assert getattr(read_model, forbidden_field) is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(read_model, **{forbidden_field: True})
    for finding in read_model.findings:
        assert finding.enforcement_performed is False
        with pytest.raises(AurelFlowValidationError):
            dataclasses.replace(finding, enforcement_performed=True)


def test_audit_is_deterministic() -> None:
    first = run_boundary_exit_audit(_l_subjects())
    second = run_boundary_exit_audit(_l_subjects())
    assert first.read_model_id == second.read_model_id
