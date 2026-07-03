"""P4-EXEC-F topology projection tests — honest visibility, no control,
and the runtime substrate boundary held structurally."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    BackpressureDecisionKind,
    build_backpressure_signal_if_needed,
    build_concurrency_window,
    build_exec_bench_sample,
    build_exec_bench_snapshot,
    build_execution_pressure_snapshot,
    build_harness_telemetry_snapshot,
    build_local_topology_profile,
    build_topology_projection,
    decide_backpressure,
)


def _full_state(*, saturated=False):
    topology = build_local_topology_profile()
    current = 1 if saturated else 0
    queue = 3 if saturated else 0
    window = build_concurrency_window(
        max_in_flight=1, current_in_flight=current, queue_depth=queue
    )
    pressure = build_execution_pressure_snapshot(
        queue_depth=queue, current_in_flight=current, max_in_flight=1
    )
    signal = build_backpressure_signal_if_needed(pressure)
    decision = decide_backpressure(pressure, signal=signal)
    bench = build_exec_bench_snapshot(
        (build_exec_bench_sample(started_at_tick=1, ended_at_tick=2,
                                 duration_ms=10, outcome_success=True),),
        pressure_level=pressure.pressure_level,
    )
    telemetry = build_harness_telemetry_snapshot(
        topology, window, pressure,
        backpressure_decision=decision, exec_bench_snapshot=bench,
    )
    return topology, window, pressure, signal, decision, bench, telemetry


def test_topology_projection_reports_pressure_backpressure_telemetry_and_unavailable_substrate():
    topology, window, pressure, signal, decision, bench, telemetry = _full_state(
        saturated=True
    )
    projection = build_topology_projection(
        topology, window, pressure,
        backpressure_signal=signal, backpressure_decision=decision,
        exec_bench_snapshot=bench, telemetry_snapshot=telemetry,
    )
    assert projection.topology_kind == "LOCAL_SINGLE_SLOT"
    assert projection.local_node_id == "local-node-0"
    assert projection.max_in_flight == 1
    assert projection.available_slots == 0
    assert projection.queue_depth == 3
    assert projection.pressure_level == "HIGH"
    assert projection.backpressure_signal_id == signal.backpressure_signal_id
    assert projection.backpressure_decision == BackpressureDecisionKind.BLOCK.value
    assert projection.operator_attention_required is True
    assert projection.exec_bench_snapshot_id == bench.exec_bench_snapshot_id
    assert projection.sample_count == 1
    assert projection.telemetry_snapshot_id == telemetry.telemetry_snapshot_id
    assert projection.unavailable_reasons  # substrate absences named


def test_projection_substrate_claims_are_unconstructible():
    topology, window, pressure, signal, decision, bench, telemetry = _full_state()
    projection = build_topology_projection(topology, window, pressure)
    for boundary_field in (
        "worker_pool_available",
        "remote_worker_available",
        "distributed_runtime_available",
        "async_dispatcher_available",
        "load_balancer_available",
        "durable_event_log_available",
        "deterministic_replay_engine_available",
        "workflow_exact_copy_available",
        "rust_wasm_substrate_available",
        "python_final_kernel_claim",
        "p5_proof_available",
        "p9_authority_available",
        "shell_ui_available",
        "react_frontend_available",
        "api_server_available",
    ):
        assert getattr(projection, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(projection, **{boundary_field: True})
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(projection, read_only=False)


def test_projection_is_read_only_and_frozen():
    topology, window, pressure, *_ = _full_state()
    projection = build_topology_projection(topology, window, pressure)
    assert projection.read_only is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        projection.pressure_level = "LOW"  # type: ignore[misc]
    for verb in ("execute", "control", "scale", "spawn", "route"):
        assert not hasattr(projection, verb)


def test_calm_state_projects_allow_without_signal():
    topology, window, pressure, signal, decision, bench, telemetry = _full_state()
    assert signal is None
    projection = build_topology_projection(
        topology, window, pressure, backpressure_decision=decision,
    )
    assert projection.pressure_level == "LOW"
    assert projection.backpressure_signal_id is None
    assert projection.backpressure_decision == BackpressureDecisionKind.ALLOW.value
    assert projection.operator_attention_required is False


def test_operator_testable_path_end_to_end():
    # topology + queue/slot inputs -> pressure -> backpressure -> telemetry -> projection
    topology, window, pressure, signal, decision, bench, telemetry = _full_state(
        saturated=True
    )
    projection = build_topology_projection(
        topology, window, pressure,
        backpressure_signal=signal, backpressure_decision=decision,
        exec_bench_snapshot=bench, telemetry_snapshot=telemetry,
    )
    # the whole chain is deterministic: rebuild and compare
    t2, w2, p2, s2, d2, b2, tel2 = _full_state(saturated=True)
    projection2 = build_topology_projection(
        t2, w2, p2, backpressure_signal=s2, backpressure_decision=d2,
        exec_bench_snapshot=b2, telemetry_snapshot=tel2,
    )
    assert projection == projection2
