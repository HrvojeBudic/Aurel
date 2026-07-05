"""P5.7 — Read-only submit trace coverage audit."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    SubmitCoverageStatus,
    SubmitEvidenceRequirementKind,
    SubmitTraceCoverageAudit,
    TraceTruthLabel,
    build_submit_trace_coverage_audit,
)


def test_audit_covers_all_fourteen_requirement_kinds():
    audit = build_submit_trace_coverage_audit()
    kinds = {r.requirement_kind for r in audit.requirements}
    assert kinds == set(SubmitEvidenceRequirementKind)
    assert len(audit.requirements) == len(list(SubmitEvidenceRequirementKind))


def test_requirement_list_is_deterministic():
    a = build_submit_trace_coverage_audit()
    b = build_submit_trace_coverage_audit()
    assert a.to_dict() == b.to_dict()


def test_every_requirement_has_owner_pack():
    audit = build_submit_trace_coverage_audit()
    for requirement in audit.requirements:
        assert requirement.owner_pack.strip()
        assert requirement.truth_label is TraceTruthLabel.LIVE


def test_audit_classifies_covered_partial_missing():
    audit = build_submit_trace_coverage_audit()
    summary = audit.summary
    assert summary.total == 14
    # The audit must honestly report gaps — not fake full coverage.
    assert summary.covered > 0
    assert summary.partial > 0
    assert summary.missing > 0
    assert (
        summary.covered
        + summary.partial
        + summary.missing
        + summary.unsupported
        + summary.unknown
        == summary.total
    )


def test_covered_kinds_are_the_expected_discrete_records():
    audit = build_submit_trace_coverage_audit()
    covered = {r.requirement_kind for r in audit.covered_requirements}
    assert SubmitEvidenceRequirementKind.TRACE_APPEND_RECORDED in covered
    assert SubmitEvidenceRequirementKind.SANDBOX_BEFORE_HASH_RECORDED in covered
    assert SubmitEvidenceRequirementKind.VERIFIER_RESULT_RECORDED in covered
    assert SubmitEvidenceRequirementKind.HITL_DECISION_RECORDED in covered
    assert SubmitEvidenceRequirementKind.BUDGET_DECISION_RECORDED in covered


def test_command_and_policy_evidence_is_partial():
    audit = build_submit_trace_coverage_audit()
    by_kind = {r.requirement_kind: r for r in audit.requirements}
    assert (
        by_kind[SubmitEvidenceRequirementKind.COMMAND_ENVELOPE_RECORDED].current_status
        is SubmitCoverageStatus.PARTIAL
    )
    assert (
        by_kind[SubmitEvidenceRequirementKind.POLICY_DECISION_RECORDED].current_status
        is SubmitCoverageStatus.PARTIAL
    )


def test_audit_is_read_only_and_not_a_bridge():
    audit = build_submit_trace_coverage_audit()
    assert audit.runtime_submit_path_inspected is True
    assert audit.modifies_submit is False
    assert audit.adds_trace_append is False
    assert audit.is_bridge is False


def test_audit_read_only_guards_are_unconstructible():
    audit = build_submit_trace_coverage_audit()
    with pytest.raises(AurelTraceError):
        SubmitTraceCoverageAudit(
            audit_id="a",
            runtime_submit_path_inspected=True,
            requirements=audit.requirements,
            is_bridge=True,
        )
