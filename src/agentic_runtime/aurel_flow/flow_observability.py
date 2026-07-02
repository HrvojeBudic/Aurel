"""P3-FLOW-C observability-ready metric/correlation envelopes.

Local, deterministic metric envelopes over Flow projections and seals.
Observability-ready is not OpenTelemetry integration: there is no exporter,
no network export, and no external dependency. Frames are inspection data.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .runtime_behavior_read_model import RuntimeBehaviorReadModel
from .types import (
    OBSERVABILITY_EXPORT_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)

FLOW_OBSERVATION_FRAME_VERSION = "flow_observation_frame.v1"


@dataclass(frozen=True)
class FlowObservationCorrelation(_CanonicalMixin):
    """Correlation keys binding a metric to flow objects."""

    run_id: str = ""
    node_id: str = ""
    event_id: str = ""
    correlation_id: str = ""
    projection_id: str = ""
    seal_id: str = ""


@dataclass(frozen=True)
class _FlowMetricBase(_CanonicalMixin):
    """Shared shape for local flow metrics. Export claims fail closed."""

    metric_name: str
    metric_value: int
    correlation: FlowObservationCorrelation
    truth_label: FlowTruthLabel = FlowTruthLabel.READ_MODEL_ONLY
    exporter: str = "NONE"
    exported: bool = False

    def __post_init__(self) -> None:
        if self.exported:
            raise AurelFlowValidationError(
                f"{type(self).__name__}.exported must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="exported",
            )


@dataclass(frozen=True)
class FlowProcessMetric(_FlowMetricBase):
    """Metric about local flow process state (runs, events, pauses)."""


@dataclass(frozen=True)
class FlowProjectionMetric(_FlowMetricBase):
    """Metric about projection construction (entry counts, node counts)."""


@dataclass(frozen=True)
class FlowSealMetric(_FlowMetricBase):
    """Metric about seal evaluation (check counts per status)."""


@dataclass(frozen=True)
class FlowObservationFrame(_CanonicalMixin):
    """Deterministic local envelope of flow metrics. Never exported."""

    frame_version: str
    frame_id: str
    correlation: FlowObservationCorrelation
    process_metrics: tuple[FlowProcessMetric, ...]
    projection_metrics: tuple[FlowProjectionMetric, ...]
    seal_metrics: tuple[FlowSealMetric, ...]
    export_unavailable_reason: str
    truth_label: FlowTruthLabel
    frame_hash: str
    opentelemetry_integrated: bool = False
    network_export_available: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("opentelemetry_integrated", "network_export_available"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowObservationFrame.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def build_flow_observation_frame(
    behavior: RuntimeBehaviorReadModel,
    *,
    projection_id: str = "",
    seal_id: str = "",
    seal_metrics: tuple[FlowSealMetric, ...] = (),
) -> FlowObservationFrame:
    """Build a local metric envelope from behavior truth. Pure and local."""

    correlation = FlowObservationCorrelation(
        run_id=behavior.run_id,
        projection_id=projection_id,
        seal_id=seal_id,
    )
    process_metrics = (
        FlowProcessMetric(
            metric_name="flow.events.count",
            metric_value=behavior.events_count,
            correlation=correlation,
        ),
        FlowProcessMetric(
            metric_name="flow.pauses.count",
            metric_value=len(behavior.pause_states),
            correlation=correlation,
        ),
        FlowProcessMetric(
            metric_name="flow.state_commitments.count",
            metric_value=len(behavior.state_commitments),
            correlation=correlation,
        ),
        FlowProcessMetric(
            metric_name="flow.failures.count",
            metric_value=len(behavior.failure_assessments),
            correlation=correlation,
        ),
    )
    projection_metrics = (
        FlowProjectionMetric(
            metric_name="flow.recovery_proposals.count",
            metric_value=len(behavior.recovery_proposals),
            correlation=correlation,
        ),
        FlowProjectionMetric(
            metric_name="flow.rollback_candidates.count",
            metric_value=len(behavior.rollback_candidates),
            correlation=correlation,
        ),
    )
    payload = {
        "frame_version": FLOW_OBSERVATION_FRAME_VERSION,
        "run_id": behavior.run_id,
        "metrics": tuple(
            (metric.metric_name, metric.metric_value)
            for metric in process_metrics + projection_metrics + seal_metrics
        ),
    }
    return FlowObservationFrame(
        frame_version=FLOW_OBSERVATION_FRAME_VERSION,
        frame_id=stable_hash(payload),
        correlation=correlation,
        process_metrics=process_metrics,
        projection_metrics=projection_metrics,
        seal_metrics=seal_metrics,
        export_unavailable_reason=OBSERVABILITY_EXPORT_UNAVAILABLE_REASON,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        frame_hash=stable_hash(payload),
    )
