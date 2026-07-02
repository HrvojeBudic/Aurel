"""P3-FLOW-G targeted recovery policy / candidate envelope tests.

Recovery is targeted, never blind: the default policy is total over the
failure taxonomy and deterministic. A selection is not execution, an
envelope is not recovery, and every candidate fail-closes into the
P3-FLOW-F checkpoint discipline.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    DEFAULT_TARGETED_RECOVERY_POLICY,
    DiagnosisConfidence,
    FailureRootCauseCategory,
    RecoveryCandidateKind,
    RuntimeFailureKind,
    build_flow_demo_bundle,
    build_recovery_candidate_boundary,
    build_recovery_candidate_read_model,
    build_recovery_policy_read_model,
    build_targeted_recovery_policy,
    create_recovery_candidate_envelope,
    create_recovery_checkpoint_requirement,
    create_root_cause_diagnosis,
    create_runtime_failure_signal,
    select_recovery_candidate,
)


def _selection_fixture(kind: RuntimeFailureKind):
    bundle = build_flow_demo_bundle()
    signal = create_runtime_failure_signal(
        bundle.run, failure_kind=kind, detail="policy test"
    )
    selection = select_recovery_candidate(DEFAULT_TARGETED_RECOVERY_POLICY, signal)
    return bundle, signal, selection


def test_default_policy_covers_every_failure_kind() -> None:
    read_model = build_recovery_policy_read_model(DEFAULT_TARGETED_RECOVERY_POLICY)
    assert read_model.covers_all_failure_kinds is True
    assert read_model.covered_failure_kind_count == len(RuntimeFailureKind)
    assert read_model.policy_executes is False
    assert read_model.blind_retry_allowed is False


@pytest.mark.parametrize(
    ("failure_kind", "expected_candidate"),
    [
        (RuntimeFailureKind.TOOL_TIMEOUT, RecoveryCandidateKind.BACKOFF_RETRY_CANDIDATE),
        (
            RuntimeFailureKind.TOOL_RATE_LIMITED,
            RecoveryCandidateKind.DELAYED_RETRY_CANDIDATE,
        ),
        (
            RuntimeFailureKind.TOOL_UNAVAILABLE,
            RecoveryCandidateKind.USE_FALLBACK_EDGE_CANDIDATE,
        ),
        (
            RuntimeFailureKind.SCHEMA_MISMATCH,
            RecoveryCandidateKind.ARGUMENT_REPAIR_CANDIDATE,
        ),
        (
            RuntimeFailureKind.MALFORMED_JSON,
            RecoveryCandidateKind.STRUCTURE_REPAIR_CANDIDATE,
        ),
        (
            RuntimeFailureKind.MISSING_FIELD,
            RecoveryCandidateKind.FIELD_COMPLETION_CANDIDATE,
        ),
        (
            RuntimeFailureKind.CONTEXT_DECAY,
            RecoveryCandidateKind.REFRESH_CONTEXT_CANDIDATE,
        ),
        (
            RuntimeFailureKind.CONTRADICTORY_EVIDENCE,
            RecoveryCandidateKind.CROSS_CHECK_SOURCES_CANDIDATE,
        ),
        (
            RuntimeFailureKind.SEMANTIC_SILENT_FAILURE,
            RecoveryCandidateKind.EVIDENCE_VERIFICATION_CANDIDATE,
        ),
        (
            RuntimeFailureKind.RETRY_STORM,
            RecoveryCandidateKind.GRACEFUL_TERMINATION_CANDIDATE,
        ),
        (
            RuntimeFailureKind.NO_PROGRESS,
            RecoveryCandidateKind.HUMAN_ESCALATION_CANDIDATE,
        ),
        (
            RuntimeFailureKind.CHECKPOINT_REQUIRED_MISSING,
            RecoveryCandidateKind.HOLD_CANDIDATE,
        ),
    ],
)
def test_targeted_mapping_is_deterministic(
    failure_kind: RuntimeFailureKind,
    expected_candidate: RecoveryCandidateKind,
) -> None:
    _bundle, _signal, selection = _selection_fixture(failure_kind)
    assert selection.selected_candidate_kind is expected_candidate
    assert selection.selection_is_not_execution is True
    assert selection.recovery_executed is False


def test_topology_amplification_maps_to_verifier_with_prune_alternative() -> None:
    _bundle, _signal, selection = _selection_fixture(
        RuntimeFailureKind.TOPOLOGY_AMPLIFICATION_RISK
    )
    assert selection.selected_candidate_kind is (
        RecoveryCandidateKind.INSERT_VERIFIER_CANDIDATE
    )
    assert selection.alternative_candidate_kinds == (
        RecoveryCandidateKind.PRUNE_RISKY_EDGE_CANDIDATE,
    )


def test_candidate_kind_vocabulary_has_no_executed_member() -> None:
    kind_values = {kind.value for kind in RecoveryCandidateKind}
    assert "EXECUTED" not in kind_values
    assert "APPLIED" not in kind_values
    assert "COMPLETED" not in kind_values


def test_partial_policy_fail_closes() -> None:
    with pytest.raises(AurelFlowValidationError):
        build_targeted_recovery_policy(
            DEFAULT_TARGETED_RECOVERY_POLICY.rules[:5]
        )


def test_selection_is_deterministic() -> None:
    _bundle, signal, selection = _selection_fixture(RuntimeFailureKind.TOOL_TIMEOUT)
    again = select_recovery_candidate(DEFAULT_TARGETED_RECOVERY_POLICY, signal)
    assert again.selection_id == selection.selection_id


def test_candidate_envelope_embeds_flow_f_checkpoint_discipline() -> None:
    _bundle, _signal, selection = _selection_fixture(RuntimeFailureKind.TOOL_TIMEOUT)
    envelope = create_recovery_candidate_envelope(selection)
    assert envelope.requires_pre_recovery_checkpoint is True
    assert envelope.requires_post_recovery_comparison is True
    assert envelope.requires_p4_execution is True
    assert envelope.requires_p5_proof is True
    assert envelope.requires_p9_authority_if_irreversible is True
    assert envelope.recovery_checkpoint_requirement_id.startswith("flrcq-")
    assert envelope.execution_available is False
    assert envelope.recovery_executed is False
    assert envelope.execution_requirement.permission_granted is False
    assert envelope.verification_requirement.verification_available is False


def test_candidate_envelope_binds_explicit_requirement_and_rejects_mismatch() -> None:
    _bundle, _signal, selection = _selection_fixture(RuntimeFailureKind.TOOL_TIMEOUT)
    requirement = create_recovery_checkpoint_requirement(run_id=selection.run_id)
    envelope = create_recovery_candidate_envelope(
        selection, checkpoint_requirement=requirement
    )
    assert envelope.recovery_checkpoint_requirement_id == requirement.requirement_id
    foreign = create_recovery_checkpoint_requirement(run_id="other-run")
    with pytest.raises(AurelFlowValidationError):
        create_recovery_candidate_envelope(selection, checkpoint_requirement=foreign)


def test_candidate_envelope_rejects_foreign_diagnosis() -> None:
    bundle, signal, selection = _selection_fixture(RuntimeFailureKind.TOOL_TIMEOUT)
    other_signal = create_runtime_failure_signal(
        bundle.run,
        failure_kind=RuntimeFailureKind.SCHEMA_MISMATCH,
        detail="other",
    )
    foreign_diagnosis = create_root_cause_diagnosis(
        other_signal,
        candidate_root_cause=FailureRootCauseCategory.SCHEMA_CONTRACT,
        confidence=DiagnosisConfidence.MEDIUM,
    )
    with pytest.raises(AurelFlowValidationError):
        create_recovery_candidate_envelope(selection, diagnosis=foreign_diagnosis)


def test_candidate_read_model_and_boundary_fail_closed() -> None:
    bundle, _signal, selection = _selection_fixture(RuntimeFailureKind.TOOL_TIMEOUT)
    envelope = create_recovery_candidate_envelope(selection)
    read_model = build_recovery_candidate_read_model(
        bundle.run.run_id, (envelope,)
    )
    assert read_model.candidate_count == 1
    assert read_model.all_require_pre_recovery_checkpoint is True
    assert read_model.all_require_post_recovery_comparison is True
    assert read_model.any_execution_available is False
    boundary = build_recovery_candidate_boundary()
    assert boundary.candidate_is_not_execution is True
    assert boundary.candidate_is_not_authority is True
    assert boundary.candidate_executes is False
    with pytest.raises(AurelFlowValidationError):
        build_recovery_candidate_read_model("other-run", (envelope,))


def test_policy_layer_does_not_mutate_demo_run() -> None:
    bundle, signal, selection = _selection_fixture(RuntimeFailureKind.TOOL_TIMEOUT)
    step_before = bundle.run.state.step
    history_before = len(bundle.run.history)
    create_recovery_candidate_envelope(selection)
    select_recovery_candidate(DEFAULT_TARGETED_RECOVERY_POLICY, signal)
    assert bundle.run.state.step == step_before
    assert len(bundle.run.history) == history_before
