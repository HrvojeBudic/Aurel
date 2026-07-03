"""P4-EXEC-F ExecBench tests — measured local telemetry, no theater."""

from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.aurel_exec import (
    AurelExecValidationError,
    ExecutionPressureLevel,
    ExecTruthLabel,
    build_concurrency_window,
    build_exec_bench_sample,
    build_exec_bench_snapshot,
    build_execution_pressure_snapshot,
    build_harness_telemetry_snapshot,
    build_local_topology_profile,
    build_no_fake_throughput_proof,
    decide_backpressure,
)


def _sample(**overrides):
    values = dict(
        exec_job_id="exec-job-a",
        attempt_id="exec-attempt-a",
        mode="TOOL",
        started_at_tick=1,
        ended_at_tick=2,
        duration_ms=12,
        outcome_success=True,
    )
    values.update(overrides)
    return build_exec_bench_sample(**values)


def test_exec_bench_sample_records_only_measured_local_data():
    sample = _sample()
    assert sample.duration_ms == 12
    assert sample.outcome_success is True
    # a duration without both measurement points is unconstructible
    with pytest.raises(AurelExecValidationError):
        build_exec_bench_sample(duration_ms=12, started_at_tick=1)
    with pytest.raises(AurelExecValidationError):
        build_exec_bench_sample(duration_ms=12)
    with pytest.raises(AurelExecValidationError):
        _sample(duration_ms=-1)
    # theater claims are unconstructible
    for boundary_field in (
        "is_synthetic_benchmark",
        "is_distributed_metric",
        "is_production_claim",
    ):
        assert getattr(sample, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(sample, **{boundary_field: True})


def test_exec_bench_snapshot_aggregates_only_provided_samples():
    s1 = _sample()
    s2 = _sample(exec_job_id="exec-job-b", started_at_tick=3, ended_at_tick=5,
                 duration_ms=20, outcome_success=False)
    s3 = _sample(exec_job_id="exec-job-c", started_at_tick=6, ended_at_tick=7,
                 duration_ms=None, outcome_success=None)
    snapshot = build_exec_bench_snapshot((s1, s2, s3))
    assert snapshot.sample_count == 3
    assert snapshot.success_count == 1
    assert snapshot.failure_count == 1  # unknown outcome is neither
    assert snapshot.avg_duration_ms == 16  # (12+20)//2, measured only
    assert snapshot.max_duration_ms == 20
    assert snapshot.window_started_at_tick == 1
    assert snapshot.window_ended_at_tick == 7
    empty = build_exec_bench_snapshot(())
    assert empty.sample_count == 0
    assert empty.avg_duration_ms is None
    # determinism
    assert build_exec_bench_snapshot((s1, s2, s3)).snapshot_hash == snapshot.snapshot_hash


def test_exec_bench_does_not_claim_distributed_or_production_throughput():
    snapshot = build_exec_bench_snapshot((_sample(),))
    for boundary_field in (
        "is_synthetic_benchmark",
        "is_distributed_metric",
        "is_production_claim",
    ):
        assert getattr(snapshot, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(snapshot, **{boundary_field: True})
    # invented counts are unconstructible
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(snapshot, success_count=5)
    with pytest.raises(AurelExecValidationError):
        dataclasses.replace(build_exec_bench_snapshot(()), avg_duration_ms=10)
    proof = build_no_fake_throughput_proof()
    for boundary_field in (
        "fake_throughput_claim",
        "synthetic_benchmark_claim",
        "distributed_metrics_claim",
        "production_benchmark_claim",
    ):
        assert getattr(proof, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(proof, **{boundary_field: True})
    # no throughput vocabulary exists at all on bench objects
    for forbidden in ("throughput", "qps", "rps", "ops_per_second"):
        assert not hasattr(snapshot, forbidden)


def test_harness_telemetry_snapshot_binds_real_state_and_stays_unavailable_honest():
    topology = build_local_topology_profile()
    window = build_concurrency_window(max_in_flight=1, current_in_flight=0, queue_depth=0)
    pressure = build_execution_pressure_snapshot(
        queue_depth=0, current_in_flight=0, max_in_flight=1
    )
    decision = decide_backpressure(pressure)
    bench = build_exec_bench_snapshot((_sample(),), pressure_level=pressure.pressure_level)
    telemetry = build_harness_telemetry_snapshot(
        topology, window, pressure,
        backpressure_decision=decision, exec_bench_snapshot=bench,
    )
    assert telemetry.topology_profile_id == topology.topology_profile_id
    assert telemetry.concurrency_window_id == window.concurrency_window_id
    assert telemetry.pressure_snapshot_id == pressure.pressure_snapshot_id
    assert telemetry.backpressure_decision_id == decision.backpressure_decision_id
    assert telemetry.exec_bench_snapshot_id == bench.exec_bench_snapshot_id
    for boundary_field in (
        "worker_pool_available",
        "remote_worker_available",
        "distributed_runtime_available",
        "async_dispatcher_available",
        "rust_wasm_substrate_available",
        "executes",
    ):
        assert getattr(telemetry, boundary_field) is False
        with pytest.raises(AurelExecValidationError):
            dataclasses.replace(telemetry, **{boundary_field: True})
    assert telemetry.unavailable_reasons  # names what does not exist


def test_dev_fixture_samples_are_labeled_honestly():
    fixture = _sample(truth_label=ExecTruthLabel.DEV_FIXTURE)
    assert fixture.truth_label is ExecTruthLabel.DEV_FIXTURE
    snapshot = build_exec_bench_snapshot(
        (fixture,), pressure_level=ExecutionPressureLevel.NORMAL,
        truth_label=ExecTruthLabel.DEV_FIXTURE,
    )
    assert snapshot.truth_label is ExecTruthLabel.DEV_FIXTURE
