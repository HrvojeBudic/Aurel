"""P4-EXEC-B ExecRuntimeBridge tests (fake kernel with the real surface)."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecErrorCode,
    AurelExecValidationError,
    ExecLifecycleState,
    ExecRuntimeBridge,
    ExecTruthLabel,
    ExecutionMode,
    ExecutionSessionStatus,
    RuntimeSubmitStatus,
    revoke_execution_lease,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def _submit(bridge, fake, card, *, job, lease, session, attempt, request=None, tick=5):
    request = request or build_bridge_request(job, lease, session, attempt)
    return bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=tick,
    )


def test_runtime_bridge_calls_agentic_runtime_submit():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    execution = _submit(bridge, fake, card, job=job, lease=lease, session=session, attempt=attempt)
    assert len(fake.submit_calls) == 1
    envelope, submitted_card = fake.submit_calls[0]
    assert envelope.tool == "read_file"
    assert envelope.args == {"path": "notes/hello.txt"}
    assert envelope.issuer_card_id == card.id
    assert submitted_card is card
    assert execution.result.runtime_submit_called is True
    assert execution.result.submit_status is RuntimeSubmitStatus.SUBMITTED
    assert execution.result.truth_label is ExecTruthLabel.LIVE
    assert execution.attempt.runtime_submit_called is True
    assert execution.attempt.command_id == envelope.id
    assert execution.attempt.command_envelope_hash == envelope.command_hash()


def test_bridge_submits_exactly_once_and_never_retries():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    execution = _submit(bridge, fake, card, job=job, lease=lease, session=session, attempt=attempt)
    # re-submitting the already-submitted attempt is refused before any call
    with pytest.raises(AurelExecValidationError) as excinfo:
        _submit(
            bridge, fake, card,
            job=execution.job, lease=lease, session=execution.session,
            attempt=execution.attempt,
        )
    assert excinfo.value.code is AurelExecErrorCode.SUBMIT_STATE_INVALID
    assert len(fake.submit_calls) == 1


def test_bridge_updates_job_session_attempt_states():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    execution = _submit(bridge, fake, card, job=job, lease=lease, session=session, attempt=attempt)
    assert execution.job.lifecycle_state is ExecLifecycleState.SUCCEEDED
    assert execution.attempt.lifecycle_state is ExecLifecycleState.SUCCEEDED
    assert execution.session.status is ExecutionSessionStatus.RUNNING


def test_expired_lease_blocks_runtime_submit():
    _, _, job, lease, session, attempt = build_bound_slice(expires_at_tick=10)
    bridge, fake, card = bridge_with_fake()
    with pytest.raises(AurelExecValidationError) as excinfo:
        _submit(bridge, fake, card, job=job, lease=lease, session=session,
                attempt=attempt, tick=10)
    assert excinfo.value.code is AurelExecErrorCode.LEASE_EXPIRED
    assert fake.submit_calls == []


def test_revoked_lease_blocks_runtime_submit():
    _, _, job, lease, session, attempt = build_bound_slice()
    revoked = revoke_execution_lease(lease)
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, revoked, session, attempt)
    with pytest.raises(AurelExecValidationError) as excinfo:
        bridge.submit_once(request, job=job, lease=revoked, session=session,
                           attempt=attempt, card=card, current_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.LEASE_REVOKED
    assert fake.submit_calls == []


def test_scope_mismatch_blocks_runtime_submit():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    # args differ from the lease's bound args hash
    request = build_bridge_request(
        job, lease, session, attempt,
        command_args=(("path", "notes/other.txt"),),
    )
    with pytest.raises(AurelExecValidationError) as excinfo:
        bridge.submit_once(request, job=job, lease=lease, session=session,
                           attempt=attempt, card=card, current_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.LEASE_SCOPE_MISMATCH
    assert fake.submit_calls == []


def test_tool_mismatch_against_lease_scope_blocks_submit():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    mismatched_lease = dataclasses.replace(
        lease, scope=dataclasses.replace(lease.scope, allowed_tool_name="list_dir")
    )
    with pytest.raises(AurelExecValidationError) as excinfo:
        bridge.submit_once(
            request, job=job, lease=mismatched_lease, session=session,
            attempt=attempt, card=card, current_tick=5,
        )
    assert excinfo.value.code in (
        AurelExecErrorCode.LEASE_SCOPE_MISMATCH,
        AurelExecErrorCode.BRIDGE_REQUEST_MISMATCH,
    )
    assert fake.submit_calls == []


def test_bridge_request_object_mismatch_is_refused():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt, issuer_card_id="card_other")
    with pytest.raises(AurelExecValidationError) as excinfo:
        bridge.submit_once(request, job=job, lease=lease, session=session,
                           attempt=attempt, card=card, current_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.BRIDGE_REQUEST_MISMATCH
    assert fake.submit_calls == []


def test_bridge_requires_a_kernel_with_a_submit_surface():
    class _NoSubmit:
        pass

    with pytest.raises(AurelExecValidationError) as excinfo:
        ExecRuntimeBridge(_NoSubmit())
    assert excinfo.value.code is AurelExecErrorCode.RUNTIME_KERNEL_INVALID


def test_unsupported_mode_is_refused_before_any_kernel_call():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(
        job, lease, session, attempt,
        requested_execution_mode=ExecutionMode.TERMINAL,
    )
    with pytest.raises(AurelExecValidationError) as excinfo:
        bridge.submit_once(request, job=job, lease=lease, session=session,
                           attempt=attempt, card=card, current_tick=5)
    assert excinfo.value.code is AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE
    assert fake.submit_calls == []


def test_bridge_result_reflects_runtime_failure_honestly():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake(succeed=False)
    execution = _submit(bridge, fake, card, job=job, lease=lease, session=session, attempt=attempt)
    assert execution.result.runtime_submit_called is True
    assert execution.result.success is False
    assert "FileNotFoundError" in (execution.result.error_message or "")
    assert execution.job.lifecycle_state is ExecLifecycleState.FAILED
    assert execution.attempt.lifecycle_state is ExecLifecycleState.FAILED


def test_bridge_result_boundary_claims_are_unconstructible():
    _, _, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    execution = _submit(bridge, fake, card, job=job, lease=lease, session=session, attempt=attempt)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(execution.result, direct_tool_dispatch_called=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(execution.result, trace_verified=True)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(
            execution.result, runtime_submit_called=False
        )  # submitted status without the call is unconstructible
