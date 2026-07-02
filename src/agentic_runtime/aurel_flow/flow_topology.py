"""P3-FLOW-E runtime topology snapshot / vulnerability / diversity / decomposition
layer (P3.13.5-P3.13.9, P3.13.15-P3.13.24).

Topology as reliability mechanism: a runtime topology snapshot can amplify or
attenuate failure. A snapshot is a deterministic, read-only view — it is not
Trace and not proof. Vulnerability scores, cascade risk, verifier placement
hints, and aggregator attenuation frames are advisory only: naming a verifier
or aggregator placement never runs a verifier or creates a live aggregator.
Diversity signals guard against the redundancy illusion: more agents is not
automatically more reliability, and majority voting is not reliability unless
diversity is proven. Decomposition worthiness signals are hints only — they
never schedule resources or spawn agents; full scheduling belongs to a future
P3-FLOW-I pack.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_dynamic_graph import RealizedRuntimeGraph
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash
from .workflow_graph import WorkflowEdgeType, WorkflowGraph
from .workflow_state import WorkflowNodeState, WorkflowRun

RUNTIME_TOPOLOGY_SNAPSHOT_VERSION = "runtime_topology_snapshot.v1"
TOPOLOGY_SNAPSHOT_READ_MODEL_VERSION = "topology_snapshot_read_model.v1"
TOPOLOGY_RISK_READ_MODEL_VERSION = "topology_risk_read_model.v1"
DIVERSITY_RISK_READ_MODEL_VERSION = "diversity_risk_read_model.v1"

TOPOLOGY_TRACE_UNAVAILABLE_REASON = (
    "a runtime topology snapshot is a deterministic read-only view, not a "
    "trace record; the evidence spine belongs to P5 AurelTrace"
)
TOPOLOGY_RISK_PROOF_UNAVAILABLE_REASON = (
    "topology vulnerability, cascade risk, verifier-placement, and "
    "aggregator-attenuation objects are advisory hints, not proof; proof "
    "belongs to P5 AurelTrace and verifier/aggregator execution belongs to "
    "a future self-healing pack"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


class TopologyRiskLabel(str, Enum):
    """Advisory risk label. Never a proof claim."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class CascadeStatus(str, Enum):
    """Advisory cascade classification. Never a proof claim."""

    NO_CASCADE_RISK = "NO_CASCADE_RISK"
    LOCAL_CASCADE_RISK = "LOCAL_CASCADE_RISK"
    DOWNSTREAM_AMPLIFICATION_RISK = "DOWNSTREAM_AMPLIFICATION_RISK"
    WORKFLOW_WIDE_AMPLIFICATION_RISK = "WORKFLOW_WIDE_AMPLIFICATION_RISK"
    SYSTEMIC_RISK = "SYSTEMIC_RISK"
    UNKNOWN = "UNKNOWN"


class EdgeActivationState(str, Enum):
    """Topology edge activation state. PROPOSED is not applied."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PROPOSED = "PROPOSED"
    PRUNED_CANDIDATE = "PRUNED_CANDIDATE"
    REWEIGHTED_CANDIDATE = "REWEIGHTED_CANDIDATE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class EdgeReliabilityRole(str, Enum):
    """What an edge means for reliability. Naming a role executes nothing."""

    PRIMARY_FLOW = "PRIMARY_FLOW"
    FALLBACK_FLOW = "FALLBACK_FLOW"
    VERIFIER_FLOW = "VERIFIER_FLOW"
    AGGREGATOR_FLOW = "AGGREGATOR_FLOW"
    RECOVERY_FLOW = "RECOVERY_FLOW"
    ESCALATION_FLOW = "ESCALATION_FLOW"
    EVIDENCE_FLOW = "EVIDENCE_FLOW"
    PAUSE_FLOW = "PAUSE_FLOW"


_EDGE_TYPE_TO_RELIABILITY_ROLE: Mapping[WorkflowEdgeType, EdgeReliabilityRole] = {
    WorkflowEdgeType.DEFAULT: EdgeReliabilityRole.PRIMARY_FLOW,
    WorkflowEdgeType.CONDITIONAL: EdgeReliabilityRole.FALLBACK_FLOW,
    WorkflowEdgeType.APPROVAL_REQUIRED: EdgeReliabilityRole.PAUSE_FLOW,
    WorkflowEdgeType.ERROR: EdgeReliabilityRole.ESCALATION_FLOW,
    WorkflowEdgeType.ROLLBACK_CANDIDATE: EdgeReliabilityRole.RECOVERY_FLOW,
    WorkflowEdgeType.UNAVAILABLE: EdgeReliabilityRole.PRIMARY_FLOW,
}


@dataclass(frozen=True)
class RuntimeTopologyVersion(_CanonicalMixin):
    """A topology version marker. Versioning is bookkeeping, not proof."""

    version_number: int
    based_on_realized_graph_id: str
    based_on_graph_version: int


@dataclass(frozen=True)
class RuntimeTopologySnapshotRef(_CanonicalMixin):
    """Stable reference to a topology snapshot."""

    snapshot_id: str
    run_id: str
    topology_version_number: int


@dataclass(frozen=True)
class RuntimeTopologyNode(_CanonicalMixin):
    """A node's topology-level state. Ready is not necessarily safe."""

    node_id: str
    node_kind: str
    runtime_state: str
    ready_state: bool
    risk_label: TopologyRiskLabel
    truth_label: FlowTruthLabel


@dataclass(frozen=True)
class RuntimeTopologyEdge(_CanonicalMixin):
    """A topology edge with an explicit reliability role."""

    edge_id: str
    source_node_id: str
    target_node_id: str
    activation_state: EdgeActivationState
    reliability_role: EdgeReliabilityRole
    weight: float
    truth_label: FlowTruthLabel
    proposed: bool = False
    pruned: bool = False


@dataclass(frozen=True)
class RuntimeTopologySnapshot(_CanonicalMixin):
    """Deterministic, read-only topology view. Not Trace. Not proof."""

    snapshot_id: str
    contract_version: str
    run_id: str
    realized_graph_id: str
    topology_version: RuntimeTopologyVersion
    created_from_event_id: str
    nodes: tuple[RuntimeTopologyNode, ...]
    edges: tuple[RuntimeTopologyEdge, ...]
    truth_label: FlowTruthLabel
    snapshot_hash: str
    unavailable_reason: str = TOPOLOGY_TRACE_UNAVAILABLE_REASON
    trace_verified: bool = False
    execution_available: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "trace_verified", "execution_available", "proof_available"
        )


def build_runtime_topology_snapshot(
    *,
    realized_graph: RealizedRuntimeGraph,
    graph: WorkflowGraph,
    run: WorkflowRun,
    created_from_event_id: str = "",
) -> RuntimeTopologySnapshot:
    """Derive a deterministic topology snapshot from a graph + run pair."""

    if run.run_id != realized_graph.run_id:
        raise AurelFlowValidationError(
            f"run {run.run_id!r} does not match realized graph run "
            f"{realized_graph.run_id!r}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="run",
        )
    nodes = tuple(
        RuntimeTopologyNode(
            node_id=node.node_id,
            node_kind=node.node_type.value,
            runtime_state=run.state.node_states.get(
                node.node_id, WorkflowNodeState.NOT_STARTED
            ).value,
            ready_state=run.state.node_states.get(node.node_id)
            == WorkflowNodeState.READY,
            risk_label=TopologyRiskLabel.UNKNOWN,
            truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        )
        for node in graph.nodes
    )
    edges = tuple(
        RuntimeTopologyEdge(
            edge_id=edge.edge_id,
            source_node_id=edge.from_node_id,
            target_node_id=edge.to_node_id,
            activation_state=EdgeActivationState.ACTIVE,
            reliability_role=_EDGE_TYPE_TO_RELIABILITY_ROLE.get(
                edge.edge_type, EdgeReliabilityRole.PRIMARY_FLOW
            ),
            weight=1.0,
            truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        )
        for edge in graph.edges
    )
    version = RuntimeTopologyVersion(
        version_number=1,
        based_on_realized_graph_id=realized_graph.realized_graph_id,
        based_on_graph_version=realized_graph.graph_version,
    )
    payload = {
        "contract_version": RUNTIME_TOPOLOGY_SNAPSHOT_VERSION,
        "run_id": run.run_id,
        "realized_graph_id": realized_graph.realized_graph_id,
        "topology_version": version.version_number,
        "node_ids": tuple(node.node_id for node in nodes),
        "edge_ids": tuple(edge.edge_id for edge in edges),
        "run_step": run.state.step,
    }
    snapshot_id = "fltopo-" + stable_hash(payload)[:16]
    return RuntimeTopologySnapshot(
        snapshot_id=snapshot_id,
        contract_version=RUNTIME_TOPOLOGY_SNAPSHOT_VERSION,
        run_id=run.run_id,
        realized_graph_id=realized_graph.realized_graph_id,
        topology_version=version,
        created_from_event_id=created_from_event_id,
        nodes=nodes,
        edges=edges,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        snapshot_hash=stable_hash(payload),
    )


def runtime_topology_snapshot_ref(
    snapshot: RuntimeTopologySnapshot,
) -> RuntimeTopologySnapshotRef:
    return RuntimeTopologySnapshotRef(
        snapshot_id=snapshot.snapshot_id,
        run_id=snapshot.run_id,
        topology_version_number=snapshot.topology_version.version_number,
    )


@dataclass(frozen=True)
class TopologySnapshotReadModel(_CanonicalMixin):
    """Deterministic snapshot projection. Not Trace. Not proof."""

    read_model_version: str
    snapshot_id: str
    run_id: str
    node_count: int
    edge_count: int
    active_edge_count: int
    proposed_edge_count: int
    pruned_edge_count: int
    reliability_role_counts: Mapping[str, int]
    truth_label: FlowTruthLabel
    read_model_hash: str
    snapshot_is_not_trace: bool = True
    snapshot_is_not_proof: bool = True
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "trace_verified")
        _forbid_false(self, "snapshot_is_not_trace", "snapshot_is_not_proof")


def build_topology_snapshot_read_model(
    snapshot: RuntimeTopologySnapshot,
) -> TopologySnapshotReadModel:
    role_counts: dict[str, int] = {}
    for edge in snapshot.edges:
        key = edge.reliability_role.value
        role_counts[key] = role_counts.get(key, 0) + 1
    payload = {
        "read_model_version": TOPOLOGY_SNAPSHOT_READ_MODEL_VERSION,
        "snapshot_hash": snapshot.snapshot_hash,
    }
    return TopologySnapshotReadModel(
        read_model_version=TOPOLOGY_SNAPSHOT_READ_MODEL_VERSION,
        snapshot_id=snapshot.snapshot_id,
        run_id=snapshot.run_id,
        node_count=len(snapshot.nodes),
        edge_count=len(snapshot.edges),
        active_edge_count=sum(
            1 for edge in snapshot.edges if edge.activation_state is EdgeActivationState.ACTIVE
        ),
        proposed_edge_count=sum(1 for edge in snapshot.edges if edge.proposed),
        pruned_edge_count=sum(1 for edge in snapshot.edges if edge.pruned),
        reliability_role_counts=role_counts,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Topology vulnerability / error propagation (P3.13.15-P3.13.19)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TopologyVulnerabilityScore(_CanonicalMixin):
    """Advisory vulnerability score for a topology node. Not proof."""

    score_id: str
    contract_version: str
    snapshot_id: str
    target_node_id: str
    risk_label: TopologyRiskLabel
    rationale: str
    truth_label: FlowTruthLabel
    is_proof: bool = False
    is_advisory: bool = True

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")
        _forbid_false(self, "is_advisory")


def create_topology_vulnerability_score(
    *,
    snapshot: RuntimeTopologySnapshot,
    target_node_id: str,
    risk_label: TopologyRiskLabel,
    rationale: str,
) -> TopologyVulnerabilityScore:
    payload = {
        "contract_version": TOPOLOGY_RISK_READ_MODEL_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "target_node_id": target_node_id,
        "risk_label": risk_label.value,
        "rationale": rationale,
    }
    score_id = "fltvs-" + stable_hash(payload)[:16]
    return TopologyVulnerabilityScore(
        score_id=score_id,
        contract_version=TOPOLOGY_RISK_READ_MODEL_VERSION,
        snapshot_id=snapshot.snapshot_id,
        target_node_id=target_node_id,
        risk_label=risk_label,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ErrorPropagationPath(_CanonicalMixin):
    """A described potential failure path. Not a proof of propagation."""

    path_id: str
    snapshot_id: str
    origin_node_id: str
    node_path: tuple[str, ...]
    cascade_status: CascadeStatus
    truth_label: FlowTruthLabel
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")


def build_error_propagation_path(
    *,
    snapshot: RuntimeTopologySnapshot,
    origin_node_id: str,
    node_path: tuple[str, ...],
    cascade_status: CascadeStatus,
) -> ErrorPropagationPath:
    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "origin_node_id": origin_node_id,
        "node_path": node_path,
        "cascade_status": cascade_status.value,
    }
    path_id = "flepp-" + stable_hash(payload)[:16]
    return ErrorPropagationPath(
        path_id=path_id,
        snapshot_id=snapshot.snapshot_id,
        origin_node_id=origin_node_id,
        node_path=node_path,
        cascade_status=cascade_status,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class CascadeAmplificationRisk(_CanonicalMixin):
    """Advisory cascade/amplification risk for a propagation path. Not proof."""

    risk_id: str
    snapshot_id: str
    propagation_path: ErrorPropagationPath
    cascade_status: CascadeStatus
    amplification_factor_label: TopologyRiskLabel
    truth_label: FlowTruthLabel
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")


def create_cascade_amplification_risk(
    *,
    propagation_path: ErrorPropagationPath,
    amplification_factor_label: TopologyRiskLabel,
) -> CascadeAmplificationRisk:
    payload = {
        "propagation_path_id": propagation_path.path_id,
        "amplification_factor_label": amplification_factor_label.value,
    }
    risk_id = "flcar-" + stable_hash(payload)[:16]
    return CascadeAmplificationRisk(
        risk_id=risk_id,
        snapshot_id=propagation_path.snapshot_id,
        propagation_path=propagation_path,
        cascade_status=propagation_path.cascade_status,
        amplification_factor_label=amplification_factor_label,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class FailureAmplificationFrame(_CanonicalMixin):
    """Aggregated cascade risk view for a snapshot. Not proof."""

    frame_id: str
    snapshot_id: str
    cascade_risks: tuple[CascadeAmplificationRisk, ...]
    overall_risk_label: TopologyRiskLabel
    truth_label: FlowTruthLabel
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")


_RISK_ORDER: tuple[TopologyRiskLabel, ...] = (
    TopologyRiskLabel.UNKNOWN,
    TopologyRiskLabel.LOW,
    TopologyRiskLabel.MEDIUM,
    TopologyRiskLabel.HIGH,
    TopologyRiskLabel.CRITICAL,
)


def _highest_risk(labels: tuple[TopologyRiskLabel, ...]) -> TopologyRiskLabel:
    if not labels:
        return TopologyRiskLabel.UNKNOWN
    return max(labels, key=_RISK_ORDER.index)


def build_failure_amplification_frame(
    *,
    snapshot: RuntimeTopologySnapshot,
    cascade_risks: tuple[CascadeAmplificationRisk, ...],
) -> FailureAmplificationFrame:
    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "cascade_risk_ids": tuple(risk.risk_id for risk in cascade_risks),
    }
    frame_id = "flfaf-" + stable_hash(payload)[:16]
    overall = _highest_risk(
        tuple(risk.amplification_factor_label for risk in cascade_risks)
    )
    return FailureAmplificationFrame(
        frame_id=frame_id,
        snapshot_id=snapshot.snapshot_id,
        cascade_risks=cascade_risks,
        overall_risk_label=overall,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class IntermediateVerifierPlacementHint(_CanonicalMixin):
    """Suggests where a verifier could go. Never runs a verifier."""

    hint_id: str
    snapshot_id: str
    suggested_after_node_id: str
    rationale: str
    truth_label: FlowTruthLabel
    verifier_executed: bool = False
    verifier_created: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "verifier_executed", "verifier_created")


def create_intermediate_verifier_placement_hint(
    *, snapshot: RuntimeTopologySnapshot, suggested_after_node_id: str, rationale: str
) -> IntermediateVerifierPlacementHint:
    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "suggested_after_node_id": suggested_after_node_id,
        "rationale": rationale,
    }
    hint_id = "flivp-" + stable_hash(payload)[:16]
    return IntermediateVerifierPlacementHint(
        hint_id=hint_id,
        snapshot_id=snapshot.snapshot_id,
        suggested_after_node_id=suggested_after_node_id,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class AggregatorAttenuationFrame(_CanonicalMixin):
    """Suggests an aggregator placement. Never creates a live aggregator."""

    frame_id: str
    snapshot_id: str
    suggested_node_ids: tuple[str, ...]
    rationale: str
    truth_label: FlowTruthLabel
    aggregator_created: bool = False
    aggregator_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "aggregator_created", "aggregator_executed")


def create_aggregator_attenuation_frame(
    *, snapshot: RuntimeTopologySnapshot, suggested_node_ids: tuple[str, ...], rationale: str
) -> AggregatorAttenuationFrame:
    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "suggested_node_ids": suggested_node_ids,
        "rationale": rationale,
    }
    frame_id = "flaaf-" + stable_hash(payload)[:16]
    return AggregatorAttenuationFrame(
        frame_id=frame_id,
        snapshot_id=snapshot.snapshot_id,
        suggested_node_ids=suggested_node_ids,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class TopologyRiskReadModel(_CanonicalMixin):
    """Aggregated topology risk projection. Advisory only, never proof."""

    read_model_version: str
    snapshot_id: str
    vulnerability_score_count: int
    cascade_risk_count: int
    verifier_hint_count: int
    aggregator_frame_count: int
    highest_risk_label: TopologyRiskLabel
    truth_label: FlowTruthLabel
    read_model_hash: str
    unavailable_reason: str = TOPOLOGY_RISK_PROOF_UNAVAILABLE_REASON
    risk_is_advisory_not_proof: bool = True
    verifier_hint_is_not_execution: bool = True
    aggregator_hint_is_not_execution: bool = True
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available")
        _forbid_false(
            self,
            "risk_is_advisory_not_proof",
            "verifier_hint_is_not_execution",
            "aggregator_hint_is_not_execution",
        )


def build_topology_risk_read_model(
    *,
    snapshot: RuntimeTopologySnapshot,
    vulnerability_scores: tuple[TopologyVulnerabilityScore, ...] = (),
    cascade_risks: tuple[CascadeAmplificationRisk, ...] = (),
    verifier_hints: tuple[IntermediateVerifierPlacementHint, ...] = (),
    aggregator_frames: tuple[AggregatorAttenuationFrame, ...] = (),
) -> TopologyRiskReadModel:
    payload = {
        "read_model_version": TOPOLOGY_RISK_READ_MODEL_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "vulnerability_score_ids": tuple(s.score_id for s in vulnerability_scores),
        "cascade_risk_ids": tuple(r.risk_id for r in cascade_risks),
        "verifier_hint_ids": tuple(h.hint_id for h in verifier_hints),
        "aggregator_frame_ids": tuple(f.frame_id for f in aggregator_frames),
    }
    highest = _highest_risk(
        tuple(score.risk_label for score in vulnerability_scores)
        + tuple(risk.amplification_factor_label for risk in cascade_risks)
    )
    return TopologyRiskReadModel(
        read_model_version=TOPOLOGY_RISK_READ_MODEL_VERSION,
        snapshot_id=snapshot.snapshot_id,
        vulnerability_score_count=len(vulnerability_scores),
        cascade_risk_count=len(cascade_risks),
        verifier_hint_count=len(verifier_hints),
        aggregator_frame_count=len(aggregator_frames),
        highest_risk_label=highest,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Diversity / redundancy risk (P3.13.20-P3.13.24, part 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentDiversitySignal(_CanonicalMixin):
    """Whether a group of nodes has proven architectural diversity. Not proof."""

    signal_id: str
    member_node_ids: tuple[str, ...]
    diversity_proven: bool
    diversity_basis: str
    truth_label: FlowTruthLabel
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")


def create_agent_diversity_signal(
    *, member_node_ids: tuple[str, ...], diversity_proven: bool, diversity_basis: str
) -> AgentDiversitySignal:
    payload = {
        "member_node_ids": member_node_ids,
        "diversity_proven": diversity_proven,
        "diversity_basis": diversity_basis,
    }
    signal_id = "flads-" + stable_hash(payload)[:16]
    return AgentDiversitySignal(
        signal_id=signal_id,
        member_node_ids=member_node_ids,
        diversity_proven=diversity_proven,
        diversity_basis=diversity_basis,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class TrainingOverlapRisk(_CanonicalMixin):
    """Advisory risk that redundant agents share training/model lineage."""

    risk_id: str
    member_node_ids: tuple[str, ...]
    overlap_label: TopologyRiskLabel
    rationale: str
    truth_label: FlowTruthLabel
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")


def create_training_overlap_risk(
    *, member_node_ids: tuple[str, ...], overlap_label: TopologyRiskLabel, rationale: str
) -> TrainingOverlapRisk:
    payload = {
        "member_node_ids": member_node_ids,
        "overlap_label": overlap_label.value,
        "rationale": rationale,
    }
    risk_id = "fltor-" + stable_hash(payload)[:16]
    return TrainingOverlapRisk(
        risk_id=risk_id,
        member_node_ids=member_node_ids,
        overlap_label=overlap_label,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ErrorCorrelationRisk(_CanonicalMixin):
    """Advisory risk that redundant agents fail together. Not proof."""

    risk_id: str
    member_node_ids: tuple[str, ...]
    correlation_label: TopologyRiskLabel
    rationale: str
    truth_label: FlowTruthLabel
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")


def create_error_correlation_risk(
    *, member_node_ids: tuple[str, ...], correlation_label: TopologyRiskLabel, rationale: str
) -> ErrorCorrelationRisk:
    payload = {
        "member_node_ids": member_node_ids,
        "correlation_label": correlation_label.value,
        "rationale": rationale,
    }
    risk_id = "flecr-" + stable_hash(payload)[:16]
    return ErrorCorrelationRisk(
        risk_id=risk_id,
        member_node_ids=member_node_ids,
        correlation_label=correlation_label,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RedundancyIllusionWarning(_CanonicalMixin):
    """More agents or majority voting is not reliability unless diversity is proven."""

    warning_id: str
    member_node_ids: tuple[str, ...]
    diversity_proven: bool
    warning_text: str
    truth_label: FlowTruthLabel
    majority_vote_reliable: bool = False
    is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_proof")
        if self.majority_vote_reliable and not self.diversity_proven:
            raise AurelFlowValidationError(
                "majority_vote_reliable cannot be True unless diversity_proven "
                "is True — majority voting is not reliability without proven "
                "diversity",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="majority_vote_reliable",
            )


def create_redundancy_illusion_warning(
    *, member_node_ids: tuple[str, ...], diversity_proven: bool, warning_text: str
) -> RedundancyIllusionWarning:
    payload = {
        "member_node_ids": member_node_ids,
        "diversity_proven": diversity_proven,
        "warning_text": warning_text,
    }
    warning_id = "flriw-" + stable_hash(payload)[:16]
    return RedundancyIllusionWarning(
        warning_id=warning_id,
        member_node_ids=member_node_ids,
        diversity_proven=diversity_proven,
        warning_text=warning_text,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        majority_vote_reliable=False,
    )


@dataclass(frozen=True)
class ArchitecturalDiversityRequirement(_CanonicalMixin):
    """A future bound on required diversity. Requirement is not enforcement."""

    requirement_id: str
    member_node_ids: tuple[str, ...]
    required_dimension: str
    minimum_distinct_count: int
    truth_label: FlowTruthLabel
    enforced: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "enforced")


def create_architectural_diversity_requirement(
    *,
    member_node_ids: tuple[str, ...],
    required_dimension: str,
    minimum_distinct_count: int,
) -> ArchitecturalDiversityRequirement:
    payload = {
        "member_node_ids": member_node_ids,
        "required_dimension": required_dimension,
        "minimum_distinct_count": minimum_distinct_count,
    }
    requirement_id = "fladr-" + stable_hash(payload)[:16]
    return ArchitecturalDiversityRequirement(
        requirement_id=requirement_id,
        member_node_ids=member_node_ids,
        required_dimension=required_dimension,
        minimum_distinct_count=minimum_distinct_count,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class DiversityRequirementFrame(_CanonicalMixin):
    """Aggregated diversity requirements + signal for a redundant group."""

    frame_id: str
    member_node_ids: tuple[str, ...]
    requirements: tuple[ArchitecturalDiversityRequirement, ...]
    diversity_signal: AgentDiversitySignal
    truth_label: FlowTruthLabel
    enforced: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "enforced")


def build_diversity_requirement_frame(
    *,
    member_node_ids: tuple[str, ...],
    requirements: tuple[ArchitecturalDiversityRequirement, ...],
    diversity_signal: AgentDiversitySignal,
) -> DiversityRequirementFrame:
    payload = {
        "member_node_ids": member_node_ids,
        "requirement_ids": tuple(r.requirement_id for r in requirements),
        "diversity_signal_id": diversity_signal.signal_id,
    }
    frame_id = "fldrf-" + stable_hash(payload)[:16]
    return DiversityRequirementFrame(
        frame_id=frame_id,
        member_node_ids=member_node_ids,
        requirements=requirements,
        diversity_signal=diversity_signal,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class DiversityRiskReadModel(_CanonicalMixin):
    """Aggregated diversity/redundancy projection. Advisory only."""

    read_model_version: str
    diversity_signal_count: int
    training_overlap_risk_count: int
    error_correlation_risk_count: int
    redundancy_warning_count: int
    any_majority_vote_claimed_reliable_without_diversity: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    more_agents_is_not_more_reliability: bool = True
    majority_vote_requires_diversity: bool = True
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "proof_available", "any_majority_vote_claimed_reliable_without_diversity"
        )
        _forbid_false(
            self, "more_agents_is_not_more_reliability", "majority_vote_requires_diversity"
        )


def build_diversity_risk_read_model(
    *,
    diversity_signals: tuple[AgentDiversitySignal, ...] = (),
    training_overlap_risks: tuple[TrainingOverlapRisk, ...] = (),
    error_correlation_risks: tuple[ErrorCorrelationRisk, ...] = (),
    redundancy_warnings: tuple[RedundancyIllusionWarning, ...] = (),
) -> DiversityRiskReadModel:
    payload = {
        "read_model_version": DIVERSITY_RISK_READ_MODEL_VERSION,
        "diversity_signal_ids": tuple(s.signal_id for s in diversity_signals),
        "training_overlap_risk_ids": tuple(r.risk_id for r in training_overlap_risks),
        "error_correlation_risk_ids": tuple(r.risk_id for r in error_correlation_risks),
        "redundancy_warning_ids": tuple(w.warning_id for w in redundancy_warnings),
    }
    return DiversityRiskReadModel(
        read_model_version=DIVERSITY_RISK_READ_MODEL_VERSION,
        diversity_signal_count=len(diversity_signals),
        training_overlap_risk_count=len(training_overlap_risks),
        error_correlation_risk_count=len(error_correlation_risks),
        redundancy_warning_count=len(redundancy_warnings),
        any_majority_vote_claimed_reliable_without_diversity=False,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Decomposition worthiness seed (P3.13.20-P3.13.24, part 2)
# ---------------------------------------------------------------------------


class DecompositionBenefitLabel(str, Enum):
    """Advisory decomposition-benefit label. Never a scheduling decision."""

    NOT_WORTH_IT = "NOT_WORTH_IT"
    MARGINAL = "MARGINAL"
    WORTH_IT = "WORTH_IT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DecompositionWorthinessSignal(_CanonicalMixin):
    """Advisory decomposition-benefit hint. Never schedules or spawns agents."""

    signal_id: str
    target_node_id: str
    benefit_label: DecompositionBenefitLabel
    rationale: str
    truth_label: FlowTruthLabel
    schedules_resources: bool = False
    spawns_agents: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "schedules_resources", "spawns_agents")


def create_decomposition_worthiness_signal(
    *, target_node_id: str, benefit_label: DecompositionBenefitLabel, rationale: str
) -> DecompositionWorthinessSignal:
    payload = {
        "target_node_id": target_node_id,
        "benefit_label": benefit_label.value,
        "rationale": rationale,
    }
    signal_id = "fldws-" + stable_hash(payload)[:16]
    return DecompositionWorthinessSignal(
        signal_id=signal_id,
        target_node_id=target_node_id,
        benefit_label=benefit_label,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class CommunicationOverheadEstimate(_CanonicalMixin):
    """An estimate, not a measured runtime cost."""

    estimate_id: str
    target_node_id: str
    subtask_count: int
    overhead_label: TopologyRiskLabel
    rationale: str
    truth_label: FlowTruthLabel
    is_measured: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_measured")


def create_communication_overhead_estimate(
    *,
    target_node_id: str,
    subtask_count: int,
    overhead_label: TopologyRiskLabel,
    rationale: str,
) -> CommunicationOverheadEstimate:
    payload = {
        "target_node_id": target_node_id,
        "subtask_count": subtask_count,
        "overhead_label": overhead_label.value,
        "rationale": rationale,
    }
    estimate_id = "flcoe-" + stable_hash(payload)[:16]
    return CommunicationOverheadEstimate(
        estimate_id=estimate_id,
        target_node_id=target_node_id,
        subtask_count=subtask_count,
        overhead_label=overhead_label,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class AgentSplitRiskHint(_CanonicalMixin):
    """Advisory risk hint for splitting a node into multiple agents."""

    hint_id: str
    target_node_id: str
    risk_label: TopologyRiskLabel
    rationale: str
    truth_label: FlowTruthLabel
    spawns_agents: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "spawns_agents")


def create_agent_split_risk_hint(
    *, target_node_id: str, risk_label: TopologyRiskLabel, rationale: str
) -> AgentSplitRiskHint:
    payload = {
        "target_node_id": target_node_id,
        "risk_label": risk_label.value,
        "rationale": rationale,
    }
    hint_id = "flasr-" + stable_hash(payload)[:16]
    return AgentSplitRiskHint(
        hint_id=hint_id,
        target_node_id=target_node_id,
        risk_label=risk_label,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class SubtaskDimensionalityReductionHint(_CanonicalMixin):
    """Advisory hint naming which dimensions could reduce subtask complexity."""

    hint_id: str
    target_node_id: str
    suggested_dimensions: tuple[str, ...]
    rationale: str
    truth_label: FlowTruthLabel
    schedules_resources: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "schedules_resources")


def create_subtask_dimensionality_reduction_hint(
    *, target_node_id: str, suggested_dimensions: tuple[str, ...], rationale: str
) -> SubtaskDimensionalityReductionHint:
    payload = {
        "target_node_id": target_node_id,
        "suggested_dimensions": suggested_dimensions,
        "rationale": rationale,
    }
    hint_id = "flsdr-" + stable_hash(payload)[:16]
    return SubtaskDimensionalityReductionHint(
        hint_id=hint_id,
        target_node_id=target_node_id,
        suggested_dimensions=suggested_dimensions,
        rationale=rationale,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
