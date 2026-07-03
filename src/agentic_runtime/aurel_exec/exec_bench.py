"""P4-EXEC-F ExecBench + harness telemetry — telemetry, not benchmark theater.

An ``ExecBenchSample`` records one measured local execution observation; an
``ExecBenchSnapshot`` aggregates only the samples it was given; a
``HarnessTelemetrySnapshot`` binds topology/window/pressure/backpressure/
bench state for future P4-G projection. No fake throughput, no synthetic
production benchmark, and no distributed metrics exist — those claims are
structurally unconstructible, and the aggregation arithmetic is
deterministic over provided samples only.
"""

from __future__ import annotations

from dataclasses import dataclass

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_pressure import (
    BackpressureDecision,
    ConcurrencyWindow,
    ExecutionPressureLevel,
    ExecutionPressureSnapshot,
)
from .exec_topology import (
    ASYNC_DISPATCHER_UNAVAILABLE_REASON,
    DISTRIBUTED_TOPOLOGY_UNAVAILABLE_REASON,
    REMOTE_TOPOLOGY_UNAVAILABLE_REASON,
    RUST_WASM_TOPOLOGY_UNAVAILABLE_REASON,
    WORKER_POOL_TOPOLOGY_UNAVAILABLE_REASON,
    ExecutionTopologyProfile,
)
from .exec_types import (
    ExecTruthLabel,
    _ExecCanonicalMixin,
    forbid_true,
    require_nonempty,
    stable_hash,
)

EXEC_BENCH_SAMPLE_VERSION = "exec_bench_sample.v1"
EXEC_BENCH_SNAPSHOT_VERSION = "exec_bench_snapshot.v1"
HARNESS_TELEMETRY_SNAPSHOT_VERSION = "harness_telemetry_snapshot.v1"
NO_FAKE_THROUGHPUT_PROOF_VERSION = "no_fake_throughput_proof.v1"

FAKE_THROUGHPUT_FORBIDDEN_REASON = (
    "ExecBench reports measured local samples only; throughput, production "
    "benchmark, and distributed metrics are never synthesized — no "
    "benchmark theater, no distributed theater"
)


@dataclass(frozen=True)
class ExecBenchSample(_ExecCanonicalMixin):
    """One measured local execution observation. Observation only."""

    exec_bench_sample_id: str
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_BENCH_SAMPLE_VERSION
    exec_job_id: str | None = None
    attempt_id: str | None = None
    mode: str | None = None
    started_at_tick: int | None = None
    ended_at_tick: int | None = None
    duration_ms: int | None = None
    outcome_success: bool | None = None
    verification_status: str | None = None
    failure_class: str | None = None
    pressure_level: ExecutionPressureLevel | None = None
    is_synthetic_benchmark: bool = False
    is_distributed_metric: bool = False
    is_production_claim: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "exec_bench_sample_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        forbid_true(
            self,
            "is_synthetic_benchmark",
            "is_distributed_metric",
            "is_production_claim",
        )
        if self.duration_ms is not None and (
            self.started_at_tick is None or self.ended_at_tick is None
        ):
            raise AurelExecValidationError(
                "duration_ms requires both started_at and ended_at "
                "observations — a duration without measurement is fake",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="duration_ms",
            )
        if self.duration_ms is not None and self.duration_ms < 0:
            raise AurelExecValidationError(
                "a negative duration is not a measurement",
                code=AurelExecErrorCode.ERROR,
                field="duration_ms",
            )

    @property
    def sample_hash(self) -> str:
        return stable_hash(self)


def build_exec_bench_sample(
    *,
    exec_job_id: str | None = None,
    attempt_id: str | None = None,
    mode: str | None = None,
    started_at_tick: int | None = None,
    ended_at_tick: int | None = None,
    duration_ms: int | None = None,
    outcome_success: bool | None = None,
    verification_status: str | None = None,
    failure_class: str | None = None,
    pressure_level: ExecutionPressureLevel | None = None,
    truth_label: ExecTruthLabel = ExecTruthLabel.LIVE,
) -> ExecBenchSample:
    """Record one measured local sample. Recording executes nothing."""
    return ExecBenchSample(
        exec_bench_sample_id="exec-bench-"
        + stable_hash((exec_job_id, attempt_id, started_at_tick, ended_at_tick))[:16],
        truth_label=truth_label,
        exec_job_id=exec_job_id,
        attempt_id=attempt_id,
        mode=mode,
        started_at_tick=started_at_tick,
        ended_at_tick=ended_at_tick,
        duration_ms=duration_ms,
        outcome_success=outcome_success,
        verification_status=verification_status,
        failure_class=failure_class,
        pressure_level=pressure_level,
    )


@dataclass(frozen=True)
class ExecBenchSnapshot(_ExecCanonicalMixin):
    """Aggregation over provided local samples only. Counts must be
    consistent with what was provided — synthetic claims unconstructible."""

    exec_bench_snapshot_id: str
    sample_count: int
    success_count: int
    failure_count: int
    pressure_level: ExecutionPressureLevel
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_BENCH_SNAPSHOT_VERSION
    avg_duration_ms: int | None = None
    max_duration_ms: int | None = None
    window_started_at_tick: int | None = None
    window_ended_at_tick: int | None = None
    is_synthetic_benchmark: bool = False
    is_distributed_metric: bool = False
    is_production_claim: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "exec_bench_snapshot_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        forbid_true(
            self,
            "is_synthetic_benchmark",
            "is_distributed_metric",
            "is_production_claim",
        )
        if min(self.sample_count, self.success_count, self.failure_count) < 0:
            raise AurelExecValidationError(
                "negative counts are not measurements",
                code=AurelExecErrorCode.ERROR,
                field="sample_count",
            )
        if self.success_count + self.failure_count > self.sample_count:
            raise AurelExecValidationError(
                "success + failure counts cannot exceed provided samples — "
                "a snapshot may not invent data",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="sample_count",
            )
        if self.sample_count == 0 and (
            self.avg_duration_ms is not None or self.max_duration_ms is not None
        ):
            raise AurelExecValidationError(
                "durations without samples are fake",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="avg_duration_ms",
            )

    @property
    def snapshot_hash(self) -> str:
        return stable_hash(self)


def build_exec_bench_snapshot(
    samples: tuple[ExecBenchSample, ...],
    *,
    pressure_level: ExecutionPressureLevel = ExecutionPressureLevel.NORMAL,
    truth_label: ExecTruthLabel = ExecTruthLabel.LIVE,
) -> ExecBenchSnapshot:
    """Aggregate exactly the provided samples. Deterministic arithmetic."""
    durations = [s.duration_ms for s in samples if s.duration_ms is not None]
    ticks_started = [
        s.started_at_tick for s in samples if s.started_at_tick is not None
    ]
    ticks_ended = [s.ended_at_tick for s in samples if s.ended_at_tick is not None]
    return ExecBenchSnapshot(
        exec_bench_snapshot_id="exec-benchsnap-"
        + stable_hash(tuple(s.exec_bench_sample_id for s in samples))[:16],
        sample_count=len(samples),
        success_count=sum(1 for s in samples if s.outcome_success is True),
        failure_count=sum(1 for s in samples if s.outcome_success is False),
        pressure_level=pressure_level,
        truth_label=truth_label,
        avg_duration_ms=(sum(durations) // len(durations)) if durations else None,
        max_duration_ms=max(durations) if durations else None,
        window_started_at_tick=min(ticks_started) if ticks_started else None,
        window_ended_at_tick=max(ticks_ended) if ticks_ended else None,
    )


@dataclass(frozen=True)
class HarnessTelemetrySnapshot(_ExecCanonicalMixin):
    """Binds topology/window/pressure/backpressure/bench state read-only
    for future P4-G projection. Never a substrate-readiness claim."""

    telemetry_snapshot_id: str
    topology_profile_id: str
    concurrency_window_id: str
    pressure_snapshot_id: str
    truth_label: ExecTruthLabel
    contract_version: str = HARNESS_TELEMETRY_SNAPSHOT_VERSION
    backpressure_decision_id: str | None = None
    exec_bench_snapshot_id: str | None = None
    unavailable_reasons: tuple[str, ...] = (
        WORKER_POOL_TOPOLOGY_UNAVAILABLE_REASON,
        REMOTE_TOPOLOGY_UNAVAILABLE_REASON,
        DISTRIBUTED_TOPOLOGY_UNAVAILABLE_REASON,
        ASYNC_DISPATCHER_UNAVAILABLE_REASON,
        RUST_WASM_TOPOLOGY_UNAVAILABLE_REASON,
    )
    worker_pool_available: bool = False
    remote_worker_available: bool = False
    distributed_runtime_available: bool = False
    async_dispatcher_available: bool = False
    rust_wasm_substrate_available: bool = False
    executes: bool = False

    def __post_init__(self) -> None:
        require_nonempty(
            self, "telemetry_snapshot_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(
            self, "topology_profile_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        forbid_true(
            self,
            "worker_pool_available",
            "remote_worker_available",
            "distributed_runtime_available",
            "async_dispatcher_available",
            "rust_wasm_substrate_available",
            "executes",
        )

    @property
    def telemetry_hash(self) -> str:
        return stable_hash(self)


def build_harness_telemetry_snapshot(
    topology: ExecutionTopologyProfile,
    window: ConcurrencyWindow,
    pressure_snapshot: ExecutionPressureSnapshot,
    *,
    backpressure_decision: BackpressureDecision | None = None,
    exec_bench_snapshot: ExecBenchSnapshot | None = None,
    truth_label: ExecTruthLabel = ExecTruthLabel.LIVE,
) -> HarnessTelemetrySnapshot:
    """Bind real local state objects into one telemetry view."""
    return HarnessTelemetrySnapshot(
        telemetry_snapshot_id="exec-telemetry-"
        + stable_hash(
            (
                topology.topology_profile_id,
                window.concurrency_window_id,
                pressure_snapshot.pressure_snapshot_id,
            )
        )[:16],
        topology_profile_id=topology.topology_profile_id,
        concurrency_window_id=window.concurrency_window_id,
        pressure_snapshot_id=pressure_snapshot.pressure_snapshot_id,
        truth_label=truth_label,
        backpressure_decision_id=(
            backpressure_decision.backpressure_decision_id
            if backpressure_decision is not None
            else None
        ),
        exec_bench_snapshot_id=(
            exec_bench_snapshot.exec_bench_snapshot_id
            if exec_bench_snapshot is not None
            else None
        ),
    )


@dataclass(frozen=True)
class NoFakeThroughputProof(_ExecCanonicalMixin):
    """Evidence that no throughput/benchmark/distributed metric is faked."""

    reason: str
    contract_version: str = NO_FAKE_THROUGHPUT_PROOF_VERSION
    fake_throughput_claim: bool = False
    synthetic_benchmark_claim: bool = False
    distributed_metrics_claim: bool = False
    production_benchmark_claim: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "fake_throughput_claim",
            "synthetic_benchmark_claim",
            "distributed_metrics_claim",
            "production_benchmark_claim",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_fake_throughput_proof() -> NoFakeThroughputProof:
    return NoFakeThroughputProof(reason=FAKE_THROUGHPUT_FORBIDDEN_REASON)
