"""P3-FLOW-D read model determinism, serialization, and truth-label tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    FORBIDDEN_FLOW_TRUTH_LABELS,
    FlowRequestedActionKind,
    FlowTruthLabel,
    PauseHookKind,
    PauseHookReason,
    build_pause_hook_read_model,
    build_proof_expectation_read_model,
    build_semantic_silent_failure_boundary,
    build_submit_compatibility_read_model,
    create_evidence_requirement,
    create_execution_proposal_envelope,
    create_proof_expectation_envelope,
    create_runtime_pause_hook,
    create_semantic_support_expectation,
    create_unsupported_output_risk,
    to_canonical_json,
)


def _proof_expectation():
    return create_proof_expectation_envelope(
        proposal_id="flprop-x",
        execution_request_id="flexec-x",
        target_run_id="run-1",
        target_node_id="plan",
        required_verifier="aurel_trace://future",
        required_trace_expectation="trace event chain with output hash",
        evidence_requirements=(
            create_evidence_requirement(
                target_run_id="run-1",
                target_node_id="plan",
                evidence_kind="TOOL_OUTPUT_HASH",
                description="output hash must be traced",
            ),
        ),
    )


def test_submit_compatibility_read_model_deterministic():
    read_model_a = build_submit_compatibility_read_model()
    read_model_b = build_submit_compatibility_read_model()
    assert read_model_a == read_model_b
    assert read_model_a.read_model_hash == read_model_b.read_model_hash
    assert to_canonical_json(read_model_a) == to_canonical_json(read_model_b)


def test_proof_expectation_read_model_counts_failure_candidates():
    envelope = _proof_expectation()
    expectation = create_semantic_support_expectation(
        target_run_id="run-1", target_node_id="plan", claim_ref="claim-1"
    )
    risk = create_unsupported_output_risk(
        target_run_id="run-1",
        target_node_id="plan",
        output_ref="out-1",
        risk_reason="output has no supporting evidence",
    )
    read_model = build_proof_expectation_read_model(
        envelopes=(envelope,),
        semantic_support_expectations=(expectation,),
        unsupported_output_risks=(risk,),
    )
    assert read_model.envelope_count == 1
    assert read_model.evidence_requirement_count == 1
    assert read_model.semantic_support_expectation_count == 1
    assert read_model.unsupported_output_risk_count == 1
    # one requirement + one expectation + one risk, all failure candidates
    assert read_model.failure_candidate_count == 3
    assert read_model.proof_available is False
    assert read_model.trace_verified is False
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, proof_available=True)
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, future_p5_required=False)


def test_proof_expectation_envelope_is_not_proof():
    envelope = _proof_expectation()
    assert envelope.proof_available is False
    assert envelope.trace_verified is False
    assert envelope.future_p5_required is True
    with pytest.raises(AurelFlowValidationError):
        replace(envelope, trace_verified=True)


def test_semantic_silent_failure_boundary_bidirectional():
    boundary = build_semantic_silent_failure_boundary()
    assert boundary.missing_evidence_is_failure_candidate is True
    assert boundary.unsupported_output_is_failure_candidate is True
    assert boundary.silent_semantic_success_allowed is False
    assert boundary.evidence_requirement_is_evidence is False
    assert boundary.proof_expectation_is_proof is False
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, missing_evidence_is_failure_candidate=False)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, silent_semantic_success_allowed=True)


def test_pause_hook_read_model_deterministic_counts():
    hooks = tuple(
        create_runtime_pause_hook(
            hook_kind=kind,
            reason=reason,
            target_run_id="run-1",
            target_node_id="plan",
            waiting_for=waiting_for,
            safe_state_summary="paused",
        )
        for kind, reason, waiting_for in (
            (PauseHookKind.REASONING, PauseHookReason.WAITING_REASONING, "reasoning"),
            (PauseHookKind.VERIFIER, PauseHookReason.WAITING_VERIFIER, "verifier"),
            (PauseHookKind.OPERATOR, PauseHookReason.WAITING_OPERATOR, "operator"),
            (PauseHookKind.EVIDENCE, PauseHookReason.WAITING_EVIDENCE, "evidence"),
        )
    )
    read_model_a = build_pause_hook_read_model(hooks=hooks)
    read_model_b = build_pause_hook_read_model(hooks=hooks)
    assert read_model_a == read_model_b
    assert read_model_a.hook_count == 4
    assert read_model_a.resumable_count == 4
    assert read_model_a.reason_counts["WAITING_VERIFIER"] == 1
    assert read_model_a.kind_counts["OPERATOR"] == 1
    assert read_model_a.stores_hidden_chain_of_thought is False
    with pytest.raises(AurelFlowValidationError):
        replace(read_model_a, stores_hidden_chain_of_thought=True)


def test_no_forbidden_truth_labels_assigned():
    envelope = create_execution_proposal_envelope(
        run_id="run-1",
        node_id="plan",
        source_scheduler_decision_id="dec-1",
        source_runtime_event_id="evt-1",
        requested_action_kind=FlowRequestedActionKind.TOOL_CALL,
        requested_tool_or_executor_ref="tool://fs.read",
        proposal_reason="proposal only",
    )
    labeled = (
        envelope,
        _proof_expectation(),
        build_submit_compatibility_read_model(),
        build_semantic_silent_failure_boundary(),
    )
    for obj in labeled:
        assert obj.truth_label not in FORBIDDEN_FLOW_TRUTH_LABELS
        assert obj.truth_label in (
            FlowTruthLabel.CONTRACT_ONLY,
            FlowTruthLabel.READ_MODEL_ONLY,
            FlowTruthLabel.INTERNAL_ONLY,
        )


def test_canonical_json_round_trip_stability():
    import json

    read_model = build_submit_compatibility_read_model()
    payload = json.loads(to_canonical_json(read_model))
    assert payload["runtime_submit_wired"] is False
    assert payload["future_p4_required"] is True
    assert payload["boundary"]["submit_called"] is False
