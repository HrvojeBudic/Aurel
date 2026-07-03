"""P4-EXEC-A no-trace-verified boundary tests.

Proves nothing in this pack is or can claim trace-verified, no Trace/Ledger
is written, and proof belongs to P5 AurelTrace. Trace-bound is not
trace-verified — and in P4-EXEC-A even trace binding is unavailable.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTraceStatus,
    ExecTruthLabel,
    ExecUnavailableSystem,
    TraceBindingStatus,
    build_dev_fixture_admission_request,
    build_exec_projection,
    build_no_trace_verified_proof,
    decide_admission,
)


def test_exec_truth_label_cannot_express_trace_verified():
    assert "TRACE_VERIFIED" not in ExecTruthLabel.__members__
    assert ExecTruthLabel.TRACE_VERIFIED_UNAVAILABLE.value == "TRACE_VERIFIED_UNAVAILABLE"


def test_trace_status_vocabularies_have_no_verified_member():
    assert "VERIFIED" not in ExecTraceStatus.__members__
    assert "TRACE_VERIFIED" not in ExecTraceStatus.__members__
    assert "BOUND" not in TraceBindingStatus.__members__
    assert "VERIFIED" not in TraceBindingStatus.__members__


def test_every_admission_decision_marks_trace_verification_unavailable():
    decision = decide_admission(build_dev_fixture_admission_request())
    assert decision.trace_status is ExecTraceStatus.TRACE_VERIFICATION_UNAVAILABLE
    trace_reasons = [
        reason
        for reason in decision.unavailable_reasons
        if reason.system is ExecUnavailableSystem.TRACE_VERIFICATION
    ]
    assert trace_reasons
    assert trace_reasons[0].future_pack_owner == "P5 AurelTrace"


def test_projection_cannot_claim_trace_verified_available():
    decision = decide_admission(build_dev_fixture_admission_request())
    projection = build_exec_projection(decision)
    assert projection.trace_verified_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, trace_verified_available=True)


def test_no_trace_verified_proof_is_fail_closed_and_names_p5():
    proof = build_no_trace_verified_proof()
    assert proof.trace_verified is False
    assert proof.trace_written is False
    assert proof.ledger_written is False
    assert proof.future_pack_owner == "P5 AurelTrace"
    for boundary_field in ("trace_verified", "trace_written", "ledger_written"):
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})


def test_aurel_exec_never_imports_trace_or_ledger_modules():
    from pathlib import Path

    import agentic_runtime.aurel_exec as aurel_exec

    for module_path in sorted(Path(aurel_exec.__file__).parent.glob("*.py")):
        source = module_path.read_text(encoding="utf-8")
        for forbidden in (
            "from ..trace import",
            "from agentic_runtime.trace import",
            "TraceLedger",
            "import trace",
        ):
            assert forbidden not in source, f"{module_path.name} contains {forbidden!r}"
