"""P4-EXEC-B no-trace-verified boundary tests.

Even with a real submit and real captured trace refs, nothing in AurelExec
can claim TRACE_VERIFIED: trace-bound is not trace-verified, and P5 remains
required. Nothing writes trace/ledger from AurelExec — refs come from what
the kernel itself already recorded.
"""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTruthLabel,
    build_exec_projection,
    build_no_trace_verified_proof,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def _real_shaped_execution():
    _, decision, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    return decision, execution


def test_trace_binding_never_claims_trace_verified_even_after_real_submit():
    decision, execution = _real_shaped_execution()
    binding = execution.trace_binding
    assert binding.trace_bound is True
    assert binding.trace_verified is False
    assert binding.p5_required is True
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(binding, trace_verified=True)


def test_outcome_and_result_never_claim_trace_verification():
    decision, execution = _real_shaped_execution()
    assert execution.outcome.trace_verified is False
    assert execution.result.trace_verified is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(execution.outcome, trace_verified=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(execution.result, trace_verified=True)


def test_trace_verified_label_remains_unconstructible():
    assert "TRACE_VERIFIED" not in ExecTruthLabel.__members__
    assert ExecTruthLabel.TRACE_BOUND.value == "TRACE_BOUND"


def test_projection_keeps_trace_verification_unavailable_after_submit():
    decision, execution = _real_shaped_execution()
    projection = build_exec_projection(
        decision,
        job=execution.job,
        attempt=execution.attempt,
        session=execution.session,
        outcome=execution.outcome,
        trace_binding=execution.trace_binding,
    )
    assert projection.trace_bound is True
    assert projection.trace_verified_available is False
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, trace_verified_available=True)
    assert "P5" in projection.trace_verified_unavailable_reason


def test_no_trace_verified_proof_still_holds_and_names_p5():
    proof = build_no_trace_verified_proof()
    assert proof.trace_verified is False
    assert proof.trace_written is False
    assert proof.ledger_written is False
    assert proof.future_pack_owner == "P5 AurelTrace"
