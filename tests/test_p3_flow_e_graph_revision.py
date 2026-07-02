"""P3-FLOW-E graph plasticity / revision proposal / edge candidate tests
(P3.13.10-P3.13.14)."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    EdgeActivationState,
    EdgeAddCandidate,
    EdgePruneCandidate,
    EdgeReliabilityRole,
    EdgeReweightCandidate,
    FlowTruthLabel,
    GraphPlasticityBoundary,
    GraphPlasticityMode,
    GraphPlasticityPolicy,
    GraphRealizationReason,
    GraphRevisionCandidateKind,
    GraphRevisionDecisionKind,
    RuntimeGraphRevisionDecision,
    RuntimeGraphRevisionProposal,
    RuntimeGraphRevisionReadModel,
    RuntimeGraphRevisionReason,
    build_flow_demo_bundle,
    build_graph_plasticity_boundary,
    build_runtime_graph_revision_read_model,
    build_runtime_topology_snapshot,
    create_edge_add_candidate,
    create_edge_prune_candidate,
    create_edge_reweight_candidate,
    create_graph_plasticity_policy,
    create_runtime_graph_revision_decision,
    create_runtime_graph_revision_proposal,
    create_workflow_template,
    realize_runtime_graph,
)


def _setup():
    bundle = build_flow_demo_bundle()
    template = create_workflow_template(bundle.graph)
    realized = realize_runtime_graph(
        template=template, run=bundle.run, realization_reason=GraphRealizationReason.RUN_CREATED
    )
    snapshot = build_runtime_topology_snapshot(
        realized_graph=realized, graph=bundle.graph, run=bundle.run
    )
    return bundle, realized, snapshot


def _proposal(boundary: GraphPlasticityBoundary, bundle, realized, snapshot, **kwargs):
    defaults = dict(
        plasticity_boundary=boundary,
        run_id=bundle.run.run_id,
        realized_graph_id=realized.realized_graph_id,
        source_snapshot_id=snapshot.snapshot_id,
        candidate_kind=GraphRevisionCandidateKind.INSERT_VERIFIER_NODE_CANDIDATE,
        reason=RuntimeGraphRevisionReason.VERIFIER_PLACEMENT_SUGGESTED,
        affected_node_ids=("fetch",),
    )
    defaults.update(kwargs)
    return create_runtime_graph_revision_proposal(**defaults)


def test_plasticity_mode_is_closed_world() -> None:
    assert GraphPlasticityMode.STATIC_LOCKED in GraphPlasticityMode
    forbidden = {"EXECUTE", "DISPATCH", "APPLY_LIVE", "AUTO_APPLY"}
    assert forbidden.isdisjoint({member.name for member in GraphPlasticityMode})


def test_locked_mode_blocks_revision_proposal() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.STATIC_LOCKED
    )
    boundary = build_graph_plasticity_boundary(policy)
    assert boundary.revision_blocked is True
    with pytest.raises(AurelFlowValidationError):
        _proposal(boundary, bundle, realized, snapshot)


def test_review_required_mode_sets_review_flags() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.OPERATOR_REVIEW_REQUIRED
    )
    boundary = build_graph_plasticity_boundary(policy)
    assert boundary.requires_operator_review is True
    assert boundary.requires_verifier_review is False
    assert boundary.revision_blocked is False
    proposal = _proposal(boundary, bundle, realized, snapshot)
    assert proposal.requires_operator_review is True
    assert isinstance(proposal, RuntimeGraphRevisionProposal)


def test_proposal_only_mode_creates_proposal_state_only() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(boundary, bundle, realized, snapshot)
    assert proposal.execution_available is False
    assert proposal.dispatch_available is False
    assert proposal.authority_granted is False


def test_proposal_rejects_disallowed_candidate_kind() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id,
        mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY,
        allowed_candidate_kinds=(GraphRevisionCandidateKind.HOLD_TOPOLOGY,),
    )
    boundary = build_graph_plasticity_boundary(policy)
    with pytest.raises(AurelFlowValidationError):
        _proposal(
            boundary,
            bundle,
            realized,
            snapshot,
            candidate_kind=GraphRevisionCandidateKind.ADD_EDGE_CANDIDATE,
        )


def test_decision_kind_has_no_execute_member() -> None:
    forbidden = {"EXECUTE", "DISPATCH", "APPLY_LIVE", "APPROVE", "AUTHORIZE"}
    assert forbidden.isdisjoint({member.name for member in GraphRevisionDecisionKind})


def test_decision_does_not_dispatch_or_grant_authority() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(boundary, bundle, realized, snapshot)
    decision = create_runtime_graph_revision_decision(
        proposal=proposal, decision_kind=GraphRevisionDecisionKind.ACCEPT_AS_CANDIDATE, reason="ok"
    )
    assert isinstance(decision, RuntimeGraphRevisionDecision)
    assert decision.execution_available is False
    assert decision.authority_granted is False
    assert decision.dispatch_available is False
    assert decision.applied_to_internal_topology is False
    assert decision.accepted_as_candidate is True


def test_revision_read_model_asserts_boundary_truth() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(boundary, bundle, realized, snapshot)
    decision = create_runtime_graph_revision_decision(
        proposal=proposal, decision_kind=GraphRevisionDecisionKind.HOLD, reason="hold"
    )
    read_model = build_runtime_graph_revision_read_model(
        proposals=(proposal,), decisions=(decision,), blocked_proposal_attempts=1
    )
    assert isinstance(read_model, RuntimeGraphRevisionReadModel)
    assert read_model.revision_is_not_execution is True
    assert read_model.revision_is_not_authority is True
    assert read_model.proposal_count == 1
    assert read_model.decision_count == 1
    assert read_model.blocked_proposal_attempts == 1


def test_edge_add_candidate_does_not_create_edge() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(
        boundary, bundle, realized, snapshot, candidate_kind=GraphRevisionCandidateKind.ADD_EDGE_CANDIDATE
    )
    candidate = create_edge_add_candidate(
        proposal=proposal,
        source_node_id="fetch",
        target_node_id="verifier-x",
        reliability_role=EdgeReliabilityRole.VERIFIER_FLOW,
    )
    assert isinstance(candidate, EdgeAddCandidate)
    assert candidate.edge_created is False
    assert candidate.activation_state is EdgeActivationState.PROPOSED
    edge_ids_before = {edge.edge_id for edge in snapshot.edges}
    assert candidate.candidate_id not in edge_ids_before


def test_edge_prune_candidate_does_not_prune_edge() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(
        boundary, bundle, realized, snapshot, candidate_kind=GraphRevisionCandidateKind.PRUNE_EDGE_CANDIDATE
    )
    target_edge_id = snapshot.edges[0].edge_id
    candidate = create_edge_prune_candidate(proposal=proposal, target_edge_id=target_edge_id)
    assert isinstance(candidate, EdgePruneCandidate)
    assert candidate.edge_pruned is False
    assert candidate.activation_state is EdgeActivationState.PRUNED_CANDIDATE
    # the snapshot itself is untouched.
    assert all(not edge.pruned for edge in snapshot.edges)


def test_edge_reweight_candidate_does_not_apply_weight() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(
        boundary,
        bundle,
        realized,
        snapshot,
        candidate_kind=GraphRevisionCandidateKind.REWEIGHT_EDGE_CANDIDATE,
    )
    target_edge = snapshot.edges[0]
    candidate = create_edge_reweight_candidate(
        proposal=proposal, target_edge_id=target_edge.edge_id, proposed_weight=0.25
    )
    assert isinstance(candidate, EdgeReweightCandidate)
    assert candidate.edge_reweighted is False
    assert candidate.proposed_weight == 0.25
    # the snapshot edge itself is untouched by proposing a new weight.
    assert target_edge.weight == 1.0


def test_insert_verifier_and_aggregator_candidates_do_not_execute() -> None:
    bundle, realized, snapshot = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.CONTROLLED_INTERNAL_REVISION
    )
    boundary = build_graph_plasticity_boundary(policy)
    verifier_proposal = _proposal(
        boundary,
        bundle,
        realized,
        snapshot,
        candidate_kind=GraphRevisionCandidateKind.INSERT_VERIFIER_NODE_CANDIDATE,
    )
    aggregator_proposal = _proposal(
        boundary,
        bundle,
        realized,
        snapshot,
        candidate_kind=GraphRevisionCandidateKind.INSERT_AGGREGATOR_NODE_CANDIDATE,
        reason=RuntimeGraphRevisionReason.AGGREGATOR_PLACEMENT_SUGGESTED,
    )
    for proposal in (verifier_proposal, aggregator_proposal):
        assert proposal.execution_available is False
        assert proposal.dispatch_available is False


def test_plasticity_policy_boolean_fails_closed() -> None:
    bundle, _, _ = _setup()
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    with pytest.raises(AurelFlowValidationError):
        GraphPlasticityPolicy(
            policy_id="flppl-fake",
            contract_version=policy.contract_version,
            run_id=bundle.run.run_id,
            mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY,
            allowed_candidate_kinds=(),
            truth_label=FlowTruthLabel.CONTRACT_ONLY,
            grants_execution_authority=True,
        )


def test_revision_construction_does_not_mutate_demo_run() -> None:
    bundle, realized, snapshot = _setup()
    step_before = bundle.run.state.step
    history_before = len(bundle.run.history)
    policy = create_graph_plasticity_policy(
        run_id=bundle.run.run_id, mode=GraphPlasticityMode.REVISION_PROPOSAL_ONLY
    )
    boundary = build_graph_plasticity_boundary(policy)
    proposal = _proposal(boundary, bundle, realized, snapshot)
    create_runtime_graph_revision_decision(
        proposal=proposal, decision_kind=GraphRevisionDecisionKind.HOLD, reason="hold"
    )
    assert bundle.run.state.step == step_before
    assert len(bundle.run.history) == history_before
