"""P4-EXEC-G truth-label audit tests — honest labels, no TRACE_VERIFIED."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecTruthLabel,
    build_exec_status_read_model,
    build_truth_label_audit,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def test_projection_truth_labels_do_not_claim_trace_verified():
    assert "TRACE_VERIFIED" not in ExecTruthLabel.__members__
    # a status category valued TRACE_VERIFIED is unconstructible
    status = build_exec_status_read_model()
    tampered = tuple(
        (name, "TRACE_VERIFIED" if name == "trace_binding_state" else value)
        for name, value in status.categories
    )
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(status, categories=tampered)


def test_truth_label_audit_censuses_real_labels():
    _, decision, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    labels = (
        decision.truth_label,          # DEV_FIXTURE
        execution.result.truth_label,  # LIVE
        execution.trace_binding.truth_label,  # TRACE_BOUND
    )
    audit = build_truth_label_audit(labels)
    assert audit.audit_status == "PASS"
    assert audit.live_items == 1
    assert audit.dev_fixture_items == 1
    assert audit.trace_bound_items == 1
    assert audit.trace_verified_items == 0
    assert audit.fake_trace_verified_risks == ()


def test_raw_trace_verified_label_forces_error():
    audit = build_truth_label_audit((), raw_label_values=("TRACE_VERIFIED",))
    assert audit.audit_status == "ERROR"
    assert audit.trace_verified_items == 1
    assert audit.fake_trace_verified_risks
    # an audit hiding TRACE_VERIFIED items behind PASS is unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(audit, audit_status="PASS")


def test_audit_is_deterministic():
    labels = (ExecTruthLabel.LIVE, ExecTruthLabel.UNAVAILABLE)
    assert build_truth_label_audit(labels) == build_truth_label_audit(labels)


def test_status_read_model_labels_are_carried_honestly():
    _, decision, job, lease, session, attempt = build_bound_slice()
    status = build_exec_status_read_model(
        admission_decision=decision, job=job, lease=lease
    )
    assert ExecTruthLabel.DEV_FIXTURE in status.truth_labels
    assert not any(
        label.value == "TRACE_VERIFIED" for label in status.truth_labels
    )
    # empty aggregation is honestly UNAVAILABLE, never LIVE
    empty = build_exec_status_read_model()
    assert empty.truth_labels == (ExecTruthLabel.UNAVAILABLE,)
