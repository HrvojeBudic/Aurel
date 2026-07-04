"""P4-EXEC-G exit seal tests — the seal is evidence, not vibes."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTruthLabel,
    GateResult,
    SealStatus,
    ValidationGateResult,
    build_p4_capability_coverage_matrix,
    build_p4_exit_seal,
    build_p4_handoff_matrix,
    build_truth_label_audit,
    build_unavailable_state_audit,
    build_validation_summary,
)


def _gate(result: GateResult, *, required: bool = True, name: str = "gate"):
    return ValidationGateResult(
        gate_name=name,
        command=".venv/bin/python -m pytest ...",
        result=result,
        notes=f"{result.value} recorded from an actual run",
        required=required,
    )


def _seal(*, focused=GateResult.PASS, large=GateResult.PASS, audit_labels=()):
    return build_p4_exit_seal(
        coverage_matrix=build_p4_capability_coverage_matrix(),
        handoff_matrix=build_p4_handoff_matrix(),
        truth_label_audit=build_truth_label_audit(audit_labels),
        unavailable_audit=build_unavailable_state_audit(),
        focused_validation=build_validation_summary((_gate(focused),)),
        large_validation=build_validation_summary((_gate(large),)),
        reports_indexed=("agent/reports/P4_EXEC_A_ADMISSION_LEASE_FOUNDATION.md",),
        remaining_risks=("documented in the seal report",),
    )


def test_p4_exit_seal_requires_large_validation_pass():
    sealed = _seal()
    assert sealed.seal_status is SealStatus.SEALED
    blocked = _seal(large=GateResult.FAIL)
    assert blocked.seal_status is SealStatus.SEAL_BLOCKED
    focused_blocked = _seal(focused=GateResult.FAIL)
    assert focused_blocked.seal_status is SealStatus.SEAL_BLOCKED
    # promoting a blocked seal to SEALED is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(blocked, seal_status=SealStatus.SEALED)


def test_validation_summary_verdict_is_derived_not_declared():
    passing = build_validation_summary((_gate(GateResult.PASS),))
    assert passing.all_required_gates_pass is True
    failing = build_validation_summary((_gate(GateResult.FAIL),))
    assert failing.all_required_gates_pass is False
    # a summary claiming pass over failing required gates is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(failing, all_required_gates_pass=True)
    # NOT_APPLICABLE / NOT_REQUIRED / WAIVED are acceptable; NOT_RUN on a
    # required gate blocks
    tolerant = build_validation_summary(
        (
            _gate(GateResult.PASS, name="pytest"),
            _gate(GateResult.NOT_APPLICABLE, name="glob"),
            _gate(GateResult.NOT_REQUIRED, name="coverage"),
            _gate(GateResult.WAIVED, name="full"),
            _gate(GateResult.NOT_RUN, required=False, name="pip_audit"),
        )
    )
    assert tolerant.all_required_gates_pass is True
    strict = build_validation_summary((_gate(GateResult.NOT_RUN, name="mypy"),))
    assert strict.all_required_gates_pass is False


def test_p4_exit_seal_is_evidence_backed():
    sealed = _seal()
    assert sealed.sealed_domain == "P4 AurelExec execution kernel foundation"
    assert sealed.covered_packs == (
        "P4-EXEC-A", "P4-EXEC-B", "P4-EXEC-C", "P4-EXEC-D",
        "P4-EXEC-E", "P4-EXEC-F", "P4-EXEC-G",
    )
    assert sealed.coverage_matrix_ref
    assert sealed.handoff_matrix_ref
    assert sealed.truth_label_audit_ref
    assert sealed.unavailable_audit_ref
    assert sealed.reports_indexed
    assert sealed.remaining_risks
    assert sealed.next_domain == "P5 AurelTrace Spine"
    # empty covered packs unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(sealed, covered_packs=())


def test_p4_exit_seal_does_not_claim_future_substrate_features():
    sealed = _seal()
    assert sealed.future_features_implemented is False
    assert sealed.python_final_kernel_claim is False
    assert sealed.trace_verified is False
    assert sealed.seal_is_runtime_mutation is False
    for boundary_field in (
        "future_features_implemented",
        "python_final_kernel_claim",
        "trace_verified",
        "seal_is_runtime_mutation",
    ):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(sealed, **{boundary_field: True})


def test_trace_verified_audit_error_blocks_the_seal():
    # inject a raw TRACE_VERIFIED via the audit path
    bad_seal = build_p4_exit_seal(
        coverage_matrix=build_p4_capability_coverage_matrix(),
        handoff_matrix=build_p4_handoff_matrix(),
        truth_label_audit=build_truth_label_audit(
            (), raw_label_values=("TRACE_VERIFIED",)
        ),
        unavailable_audit=build_unavailable_state_audit(),
        focused_validation=build_validation_summary((_gate(GateResult.PASS),)),
        large_validation=build_validation_summary((_gate(GateResult.PASS),)),
        reports_indexed=("r",),
        remaining_risks=("x",),
    )
    assert bad_seal.seal_status is SealStatus.SEAL_BLOCKED


def test_seal_is_deterministic_and_hashable():
    assert _seal().seal_hash == _seal().seal_hash
    assert _seal().truth_label is ExecTruthLabel.LIVE
