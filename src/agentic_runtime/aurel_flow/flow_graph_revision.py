"""P3-FLOW-E graph plasticity / revision proposal / edge candidate layer
(P3.13.10-P3.13.14).

Dynamic topology is not arbitrary self-modification: a ``GraphPlasticityMode``
controls whether a graph is locked, proposal-only, review-required, or
unavailable, and a locked mode blocks revision proposals outright. A
``RuntimeGraphRevisionProposal`` names a possible add/prune/reweight/insert/
split/merge candidate; naming it never dispatches, never executes, and never
grants authority. A ``RuntimeGraphRevisionDecision`` records a decision over
a proposal — it still never dispatches or creates a live agent. Execution
belongs to P4 AurelExec; authority belongs to P9 Custos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_topology import EdgeActivationState, EdgeReliabilityRole
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

GRAPH_PLASTICITY_POLICY_VERSION = "graph_plasticity_policy.v1"
GRAPH_PLASTICITY_BOUNDARY_VERSION = "graph_plasticity_boundary.v1"
RUNTIME_GRAPH_REVISION_PROPOSAL_VERSION = "runtime_graph_revision_proposal.v1"
RUNTIME_GRAPH_REVISION_DECISION_VERSION = "runtime_graph_revision_decision.v1"
RUNTIME_GRAPH_REVISION_READ_MODEL_VERSION = "runtime_graph_revision_read_model.v1"
EDGE_REVISION_CANDIDATE_VERSION = "edge_revision_candidate.v1"

REVISION_EXECUTION_UNAVAILABLE_REASON = (
    "graph revision proposals and decisions describe a possible topology "
    "change only; nothing here dispatches, executes, spawns an agent, or "
    "grants authority — execution belongs to P4 AurelExec and authority "
    "belongs to P9 Custos"
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


class GraphPlasticityMode(str, Enum):
    """Closed-world graph plasticity vocabulary."""

    STATIC_LOCKED = "STATIC_LOCKED"
    TEMPLATE_REALIZED_ONCE = "TEMPLATE_REALIZED_ONCE"
    REVISION_PROPOSAL_ONLY = "REVISION_PROPOSAL_ONLY"
    CONTROLLED_INTERNAL_REVISION = "CONTROLLED_INTERNAL_REVISION"
    OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
    VERIFIER_REVIEW_REQUIRED = "VERIFIER_REVIEW_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


LOCKED_PLASTICITY_MODES: tuple[GraphPlasticityMode, ...] = (
    GraphPlasticityMode.STATIC_LOCKED,
    GraphPlasticityMode.TEMPLATE_REALIZED_ONCE,
    GraphPlasticityMode.UNAVAILABLE,
    GraphPlasticityMode.ERROR,
)

REVIEW_REQUIRED_PLASTICITY_MODES: tuple[GraphPlasticityMode, ...] = (
    GraphPlasticityMode.OPERATOR_REVIEW_REQUIRED,
    GraphPlasticityMode.VERIFIER_REVIEW_REQUIRED,
)


class GraphRevisionCandidateKind(str, Enum):
    """Closed-world candidate vocabulary for topology revision proposals."""

    ADD_NODE_CANDIDATE = "ADD_NODE_CANDIDATE"
    REMOVE_NODE_CANDIDATE = "REMOVE_NODE_CANDIDATE"
    ADD_EDGE_CANDIDATE = "ADD_EDGE_CANDIDATE"
    PRUNE_EDGE_CANDIDATE = "PRUNE_EDGE_CANDIDATE"
    REWEIGHT_EDGE_CANDIDATE = "REWEIGHT_EDGE_CANDIDATE"
    INSERT_VERIFIER_NODE_CANDIDATE = "INSERT_VERIFIER_NODE_CANDIDATE"
    INSERT_AGGREGATOR_NODE_CANDIDATE = "INSERT_AGGREGATOR_NODE_CANDIDATE"
    SPLIT_NODE_CANDIDATE = "SPLIT_NODE_CANDIDATE"
    MERGE_NODE_CANDIDATE = "MERGE_NODE_CANDIDATE"
    HOLD_TOPOLOGY = "HOLD_TOPOLOGY"
    REJECT_REVISION = "REJECT_REVISION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class GraphRevisionDecisionKind(str, Enum):
    """Closed-world decision vocabulary. No EXECUTE/DISPATCH/APPLY_LIVE member."""

    ACCEPT_AS_CANDIDATE = "ACCEPT_AS_CANDIDATE"
    DEFER_FOR_OPERATOR_REVIEW = "DEFER_FOR_OPERATOR_REVIEW"
    DEFER_FOR_VERIFIER_REVIEW = "DEFER_FOR_VERIFIER_REVIEW"
    HOLD = "HOLD"
    REJECT = "REJECT"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RuntimeGraphRevisionReason(str, Enum):
    """Why a revision proposal was raised. Naming a reason is not a proposal."""

    TOPOLOGY_VULNERABILITY_DETECTED = "TOPOLOGY_VULNERABILITY_DETECTED"
    CASCADE_RISK_DETECTED = "CASCADE_RISK_DETECTED"
    VERIFIER_PLACEMENT_SUGGESTED = "VERIFIER_PLACEMENT_SUGGESTED"
    AGGREGATOR_PLACEMENT_SUGGESTED = "AGGREGATOR_PLACEMENT_SUGGESTED"
    REDUNDANCY_ILLUSION_DETECTED = "REDUNDANCY_ILLUSION_DETECTED"
    DECOMPOSITION_HINT = "DECOMPOSITION_HINT"
    OPERATOR_REQUESTED = "OPERATOR_REQUESTED"
    RECOVERY_PROPOSED_TOPOLOGY_CHANGE = "RECOVERY_PROPOSED_TOPOLOGY_CHANGE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class GraphPlasticityPolicy(_CanonicalMixin):
    """A run's plasticity mode + allowed candidate kinds. Not an authority grant."""

    policy_id: str
    contract_version: str
    run_id: str
    mode: GraphPlasticityMode
    allowed_candidate_kinds: tuple[GraphRevisionCandidateKind, ...]
    truth_label: FlowTruthLabel
    grants_execution_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "grants_execution_authority")


def create_graph_plasticity_policy(
    *,
    run_id: str,
    mode: GraphPlasticityMode,
    allowed_candidate_kinds: tuple[GraphRevisionCandidateKind, ...] | None = None,
) -> GraphPlasticityPolicy:
    if allowed_candidate_kinds is None:
        allowed_candidate_kinds = (
            ()
            if mode in LOCKED_PLASTICITY_MODES
            else tuple(
                kind
                for kind in GraphRevisionCandidateKind
                if kind not in (GraphRevisionCandidateKind.UNAVAILABLE, GraphRevisionCandidateKind.ERROR)
            )
        )
    payload = {
        "contract_version": GRAPH_PLASTICITY_POLICY_VERSION,
        "run_id": run_id,
        "mode": mode.value,
        "allowed_candidate_kinds": tuple(kind.value for kind in allowed_candidate_kinds),
    }
    policy_id = "flppl-" + stable_hash(payload)[:16]
    return GraphPlasticityPolicy(
        policy_id=policy_id,
        contract_version=GRAPH_PLASTICITY_POLICY_VERSION,
        run_id=run_id,
        mode=mode,
        allowed_candidate_kinds=allowed_candidate_kinds,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class GraphPlasticityBoundary(_CanonicalMixin):
    """Derived review/lock posture for a plasticity policy. Not authority."""

    boundary_version: str
    policy: GraphPlasticityPolicy
    requires_operator_review: bool
    requires_verifier_review: bool
    revision_blocked: bool
    truth_label: FlowTruthLabel
    boundary_hash: str
    grants_execution_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "grants_execution_authority")


def build_graph_plasticity_boundary(policy: GraphPlasticityPolicy) -> GraphPlasticityBoundary:
    payload = {
        "boundary_version": GRAPH_PLASTICITY_BOUNDARY_VERSION,
        "policy_id": policy.policy_id,
    }
    return GraphPlasticityBoundary(
        boundary_version=GRAPH_PLASTICITY_BOUNDARY_VERSION,
        policy=policy,
        requires_operator_review=policy.mode is GraphPlasticityMode.OPERATOR_REVIEW_REQUIRED,
        requires_verifier_review=policy.mode is GraphPlasticityMode.VERIFIER_REVIEW_REQUIRED,
        revision_blocked=policy.mode in LOCKED_PLASTICITY_MODES,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class RuntimeGraphRevisionProposal(_CanonicalMixin):
    """A candidate topology change. Proposal is not execution and not authority."""

    proposal_id: str
    contract_version: str
    run_id: str
    realized_graph_id: str
    source_snapshot_id: str
    candidate_kind: GraphRevisionCandidateKind
    reason: RuntimeGraphRevisionReason
    reason_detail: str
    affected_node_ids: tuple[str, ...]
    affected_edge_ids: tuple[str, ...]
    requires_operator_review: bool
    requires_verifier_review: bool
    requires_permission: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = REVISION_EXECUTION_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    execution_available: bool = False
    authority_granted: bool = False
    dispatch_available: bool = False
    future_p4_required: bool = True
    future_p9_required: bool = True

    def __post_init__(self) -> None:
        _forbid_true(
            self, "execution_available", "authority_granted", "dispatch_available"
        )
        _forbid_false(self, "future_p4_required", "future_p9_required")


def create_runtime_graph_revision_proposal(
    *,
    plasticity_boundary: GraphPlasticityBoundary,
    run_id: str,
    realized_graph_id: str,
    source_snapshot_id: str,
    candidate_kind: GraphRevisionCandidateKind,
    reason: RuntimeGraphRevisionReason,
    reason_detail: str = "",
    affected_node_ids: tuple[str, ...] = (),
    affected_edge_ids: tuple[str, ...] = (),
    metadata: Mapping[str, str] | None = None,
) -> RuntimeGraphRevisionProposal:
    """Propose a topology revision candidate. Fails closed when the policy
    blocks revision, and when the candidate kind is not on the allow-list."""

    if plasticity_boundary.revision_blocked:
        raise AurelFlowValidationError(
            f"graph plasticity mode {plasticity_boundary.policy.mode.value!r} "
            "blocks revision proposals",
            code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
            field="plasticity_boundary",
        )
    if candidate_kind not in plasticity_boundary.policy.allowed_candidate_kinds:
        raise AurelFlowValidationError(
            f"candidate kind {candidate_kind.value!r} is not allowed by policy "
            f"{plasticity_boundary.policy.policy_id!r}",
            code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
            field="candidate_kind",
        )
    payload = {
        "contract_version": RUNTIME_GRAPH_REVISION_PROPOSAL_VERSION,
        "run_id": run_id,
        "realized_graph_id": realized_graph_id,
        "source_snapshot_id": source_snapshot_id,
        "candidate_kind": candidate_kind.value,
        "reason": reason.value,
        "reason_detail": reason_detail,
        "affected_node_ids": affected_node_ids,
        "affected_edge_ids": affected_edge_ids,
    }
    proposal_id = "flgrp-" + stable_hash(payload)[:16]
    return RuntimeGraphRevisionProposal(
        proposal_id=proposal_id,
        contract_version=RUNTIME_GRAPH_REVISION_PROPOSAL_VERSION,
        run_id=run_id,
        realized_graph_id=realized_graph_id,
        source_snapshot_id=source_snapshot_id,
        candidate_kind=candidate_kind,
        reason=reason,
        reason_detail=reason_detail,
        affected_node_ids=affected_node_ids,
        affected_edge_ids=affected_edge_ids,
        requires_operator_review=plasticity_boundary.requires_operator_review,
        requires_verifier_review=plasticity_boundary.requires_verifier_review,
        requires_permission=True,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class RuntimeGraphRevisionDecision(_CanonicalMixin):
    """A decision over a revision proposal. Decision is not dispatch."""

    decision_id: str
    contract_version: str
    proposal_id: str
    decision_kind: GraphRevisionDecisionKind
    accepted_as_candidate: bool
    reason: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = REVISION_EXECUTION_UNAVAILABLE_REASON
    applied_to_internal_topology: bool = False
    execution_available: bool = False
    authority_granted: bool = False
    dispatch_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "applied_to_internal_topology",
            "execution_available",
            "authority_granted",
            "dispatch_available",
        )


def create_runtime_graph_revision_decision(
    *,
    proposal: RuntimeGraphRevisionProposal,
    decision_kind: GraphRevisionDecisionKind,
    reason: str,
) -> RuntimeGraphRevisionDecision:
    payload = {
        "contract_version": RUNTIME_GRAPH_REVISION_DECISION_VERSION,
        "proposal_id": proposal.proposal_id,
        "decision_kind": decision_kind.value,
        "reason": reason,
    }
    decision_id = "flgrd-" + stable_hash(payload)[:16]
    return RuntimeGraphRevisionDecision(
        decision_id=decision_id,
        contract_version=RUNTIME_GRAPH_REVISION_DECISION_VERSION,
        proposal_id=proposal.proposal_id,
        decision_kind=decision_kind,
        accepted_as_candidate=decision_kind is GraphRevisionDecisionKind.ACCEPT_AS_CANDIDATE,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RuntimeGraphRevisionReadModel(_CanonicalMixin):
    """Deterministic revision projection. Revision is not execution/authority."""

    read_model_version: str
    proposal_count: int
    decision_count: int
    candidate_kind_counts: Mapping[str, int]
    decision_kind_counts: Mapping[str, int]
    blocked_proposal_attempts: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    revision_is_not_execution: bool = True
    revision_is_not_authority: bool = True
    dispatch_available: bool = False
    authority_granted_any: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "dispatch_available", "authority_granted_any")
        _forbid_false(self, "revision_is_not_execution", "revision_is_not_authority")


def build_runtime_graph_revision_read_model(
    *,
    proposals: tuple[RuntimeGraphRevisionProposal, ...] = (),
    decisions: tuple[RuntimeGraphRevisionDecision, ...] = (),
    blocked_proposal_attempts: int = 0,
) -> RuntimeGraphRevisionReadModel:
    candidate_kind_counts: dict[str, int] = {}
    for proposal in proposals:
        key = proposal.candidate_kind.value
        candidate_kind_counts[key] = candidate_kind_counts.get(key, 0) + 1
    decision_kind_counts: dict[str, int] = {}
    for decision in decisions:
        key = decision.decision_kind.value
        decision_kind_counts[key] = decision_kind_counts.get(key, 0) + 1
    payload = {
        "read_model_version": RUNTIME_GRAPH_REVISION_READ_MODEL_VERSION,
        "proposal_ids": tuple(p.proposal_id for p in proposals),
        "decision_ids": tuple(d.decision_id for d in decisions),
        "blocked_proposal_attempts": blocked_proposal_attempts,
    }
    return RuntimeGraphRevisionReadModel(
        read_model_version=RUNTIME_GRAPH_REVISION_READ_MODEL_VERSION,
        proposal_count=len(proposals),
        decision_count=len(decisions),
        candidate_kind_counts=candidate_kind_counts,
        decision_kind_counts=decision_kind_counts,
        blocked_proposal_attempts=blocked_proposal_attempts,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Edge candidates (P3.13.10-P3.13.14, edge-level detail)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EdgeAddCandidate(_CanonicalMixin):
    """Candidate to add an edge later. Naming an edge does not create one."""

    candidate_id: str
    proposal_id: str
    source_node_id: str
    target_node_id: str
    reliability_role: EdgeReliabilityRole
    activation_state: EdgeActivationState
    weight: float
    truth_label: FlowTruthLabel
    edge_created: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "edge_created")


def create_edge_add_candidate(
    *,
    proposal: RuntimeGraphRevisionProposal,
    source_node_id: str,
    target_node_id: str,
    reliability_role: EdgeReliabilityRole,
    weight: float = 1.0,
) -> EdgeAddCandidate:
    payload = {
        "contract_version": EDGE_REVISION_CANDIDATE_VERSION,
        "proposal_id": proposal.proposal_id,
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "reliability_role": reliability_role.value,
        "weight": weight,
    }
    candidate_id = "fledg-" + stable_hash(payload)[:16]
    return EdgeAddCandidate(
        candidate_id=candidate_id,
        proposal_id=proposal.proposal_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        reliability_role=reliability_role,
        activation_state=EdgeActivationState.PROPOSED,
        weight=weight,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class EdgePruneCandidate(_CanonicalMixin):
    """Candidate to prune an edge later. Naming a prune does not prune it."""

    candidate_id: str
    proposal_id: str
    target_edge_id: str
    activation_state: EdgeActivationState
    truth_label: FlowTruthLabel
    edge_pruned: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "edge_pruned")


def create_edge_prune_candidate(
    *, proposal: RuntimeGraphRevisionProposal, target_edge_id: str
) -> EdgePruneCandidate:
    payload = {
        "contract_version": EDGE_REVISION_CANDIDATE_VERSION,
        "proposal_id": proposal.proposal_id,
        "target_edge_id": target_edge_id,
    }
    candidate_id = "fledg-" + stable_hash(payload)[:16]
    return EdgePruneCandidate(
        candidate_id=candidate_id,
        proposal_id=proposal.proposal_id,
        target_edge_id=target_edge_id,
        activation_state=EdgeActivationState.PRUNED_CANDIDATE,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class EdgeReweightCandidate(_CanonicalMixin):
    """Candidate to reweight an edge later. Naming a weight does not apply it."""

    candidate_id: str
    proposal_id: str
    target_edge_id: str
    proposed_weight: float
    activation_state: EdgeActivationState
    truth_label: FlowTruthLabel
    edge_reweighted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "edge_reweighted")


def create_edge_reweight_candidate(
    *, proposal: RuntimeGraphRevisionProposal, target_edge_id: str, proposed_weight: float
) -> EdgeReweightCandidate:
    payload = {
        "contract_version": EDGE_REVISION_CANDIDATE_VERSION,
        "proposal_id": proposal.proposal_id,
        "target_edge_id": target_edge_id,
        "proposed_weight": proposed_weight,
    }
    candidate_id = "fledg-" + stable_hash(payload)[:16]
    return EdgeReweightCandidate(
        candidate_id=candidate_id,
        proposal_id=proposal.proposal_id,
        target_edge_id=target_edge_id,
        proposed_weight=proposed_weight,
        activation_state=EdgeActivationState.REWEIGHTED_CANDIDATE,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
