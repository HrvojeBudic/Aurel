"""P4-EXEC-B ExecTraceBinding tests — bound is not verified."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTraceBinding,
    ExecTruthLabel,
    build_exec_trace_binding,
)
from tests.aurel_exec._bridge_helpers import (
    _FakeTransition,
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def test_binding_captures_real_transition_refs():
    binding = build_exec_trace_binding(
        attempt_id="exec-attempt-x", transition=_FakeTransition()
    )
    assert binding.trace_bound is True
    assert binding.runtime_trace_ref == "txn_fake_0001"
    assert binding.trace_event_ref == "deadbeef" * 8
    assert binding.truth_label is ExecTruthLabel.TRACE_BOUND
    assert binding.trace_verified is False
    assert binding.p5_required is True


def test_binding_without_transition_is_honestly_unbound():
    binding = build_exec_trace_binding(attempt_id="exec-attempt-x", transition=None)
    assert binding.trace_bound is False
    assert binding.runtime_trace_ref is None
    assert binding.trace_event_ref is None
    assert binding.truth_label is ExecTruthLabel.UNAVAILABLE


def test_trace_binding_never_claims_trace_verified():
    binding = build_exec_trace_binding(
        attempt_id="exec-attempt-x", transition=_FakeTransition()
    )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(binding, trace_verified=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(binding, p5_required=False)
    assert "TRACE_VERIFIED" not in ExecTruthLabel.__members__


def test_bound_claim_requires_a_real_ref_and_vice_versa():
    with pytest.raises(AurelExecValidationError):
        ExecTraceBinding(
            trace_binding_id="exec-trace-bind-x",
            attempt_id="exec-attempt-x",
            trace_bound=True,
            truth_label=ExecTruthLabel.TRACE_BOUND,
            runtime_trace_ref=None,
        )
    with pytest.raises(AurelExecValidationError):
        ExecTraceBinding(
            trace_binding_id="exec-trace-bind-x",
            attempt_id="exec-attempt-x",
            trace_bound=False,
            truth_label=ExecTruthLabel.TRACE_BOUND,
        )
    # a bound binding must carry TRACE_BOUND, not any other label
    with pytest.raises(AurelExecValidationError):
        ExecTraceBinding(
            trace_binding_id="exec-trace-bind-x",
            attempt_id="exec-attempt-x",
            trace_bound=True,
            truth_label=ExecTruthLabel.DEV_FIXTURE,
            runtime_trace_ref="txn_x",
        )


def test_bridge_produces_binding_from_real_result_shape():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    assert execution.trace_binding.trace_bound is True
    assert execution.trace_binding.attempt_id == attempt.attempt_id
    assert execution.attempt.trace_binding_id == execution.trace_binding.trace_binding_id


def test_bridge_stays_honest_when_runtime_returns_no_transition():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake(with_transition=False)
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    assert execution.trace_binding.trace_bound is False
    assert execution.trace_binding.truth_label is ExecTruthLabel.UNAVAILABLE
    assert execution.outcome.trace_ref is None
