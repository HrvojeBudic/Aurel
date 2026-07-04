"""P4-EXEC-G status projection tests — read-only aggregation over P4-A..F."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    STATUS_CATEGORIES,
    build_dev_fixture_admission_request,
    build_exec_status_read_model,
    build_local_topology_profile,
    build_execution_pressure_snapshot,
    decide_admission,
    decide_backpressure,
)
from tests.aurel_exec._bridge_helpers import (
    bridge_with_fake,
    build_bound_slice,
    build_bridge_request,
)


def _full_inputs():
    _, decision, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    topology = build_local_topology_profile()
    pressure = build_execution_pressure_snapshot(
        queue_depth=0, current_in_flight=0, max_in_flight=1
    )
    return dict(
        admission_decision=decision,
        lease=lease,
        job=execution.job,
        attempt=execution.attempt,
        session=execution.session,
        outcome=execution.outcome,
        trace_binding=execution.trace_binding,
        topology=topology,
        pressure_snapshot=pressure,
        backpressure_decision=decide_backpressure(pressure),
    )


def test_exec_status_projection_aggregates_p4_state_read_only():
    status = build_exec_status_read_model(**_full_inputs())
    assert [name for name, _ in status.categories] == list(STATUS_CATEGORIES)
    assert status.category("admission_state") == "ADMIT"
    assert status.category("job_state") == "SUCCEEDED"
    assert status.category("runtime_submit_state") == "SUBMITTED_ONCE"
    assert status.category("outcome_state") == "RUNTIME_SUCCESS"
    assert status.category("trace_binding_state") == "TRACE_BOUND"
    assert status.category("topology_state") == "LOCAL_SINGLE_SLOT"
    assert status.category("pressure_state") == "LOW"
    assert status.category("backpressure_state") == "ALLOW"
    assert status.read_only is True
    # read-only proof: frozen + no mutation/execution surface
    with pytest.raises(dataclasses.FrozenInstanceError):
        status.exec_job_id = "x"  # type: ignore[misc]
    for verb in ("submit", "execute", "run", "retry", "recover", "rollback",
                 "mutate", "approve", "enforce", "verify"):
        assert not hasattr(status, verb)


def test_missing_projection_categories_are_unavailable_with_reason():
    _, decision, job, lease, session, attempt = build_bound_slice()
    status = build_exec_status_read_model(admission_decision=decision, job=job)
    assert status.category("admission_state") == "ADMIT"
    assert status.category("queue_state") == "UNAVAILABLE"
    assert status.category("verification_state") == "UNAVAILABLE"
    unavailable_names = {name for name, _ in status.unavailable_reasons}
    assert "queue_state" in unavailable_names
    assert "verification_state" in unavailable_names
    # every UNAVAILABLE category carries a reason; stripping reasons is
    # unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(status, unavailable_reasons=())


def test_status_boundary_claims_are_unconstructible():
    status = build_exec_status_read_model()
    for boundary_field in (
        "mutates_runtime",
        "executes",
        "verifies_trace",
        "enforces_policy",
        "grants_authority",
        "shell_ui_available",
    ):
        assert getattr(status, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(status, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(status, read_only=False)


def test_status_category_totality_is_structural():
    status = build_exec_status_read_model()
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(status, categories=status.categories[:-1])
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(
            status, categories=status.categories + (("extra_state", "X"),)
        )


def test_aggregation_is_deterministic():
    inputs = _full_inputs()
    first = build_exec_status_read_model(**inputs)
    second = build_exec_status_read_model(**inputs)
    assert first == second
    assert first.status_hash == second.status_hash


def test_aggregator_never_touches_the_kernel():
    # the aggregator consumes objects; the fake kernel records zero calls
    # beyond the single bridge submit that produced the inputs
    _, decision, job, lease, session, attempt = build_bound_slice()
    bridge, fake, card = bridge_with_fake()
    request = build_bridge_request(job, lease, session, attempt)
    execution = bridge.submit_once(
        request, job=job, lease=lease, session=session, attempt=attempt,
        card=card, current_tick=5,
    )
    calls_before = len(fake.submit_calls)
    build_exec_status_read_model(
        admission_decision=decision, job=execution.job, attempt=execution.attempt,
        session=execution.session, outcome=execution.outcome,
    )
    assert len(fake.submit_calls) == calls_before == 1
