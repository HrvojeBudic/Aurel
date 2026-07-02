"""P3-FLOW-F revert / rollback candidate tests.

A revert candidate is a safety review object: ``safe_to_execute`` stays
False in P3, nothing rolls back, nothing reverts external state, and no
authority or permission is granted.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    RuntimeCheckpointKind,
    RuntimeCheckpointReason,
    build_flow_demo_bundle,
    build_revert_read_model,
    build_revert_safety_frame,
    build_rollback_authority_requirement,
    build_rollback_execution_boundary,
    create_runtime_checkpoint_ref,
    create_runtime_revert_candidate,
)


def _fixture():
    bundle = build_flow_demo_bundle()
    ref = create_runtime_checkpoint_ref(
        bundle.run,
        checkpoint_kind=RuntimeCheckpointKind.BEFORE_ROLLBACK_CANDIDATE,
        checkpoint_reason=RuntimeCheckpointReason.RECOVERY_PREPARATION,
        created_by="test-operator",
    )
    candidate = create_runtime_revert_candidate(
        target_checkpoint=ref,
        affected_node_ids=("fetch",),
        affected_event_ids=("rtev-example",),
        external_side_effects_present=True,
    )
    return bundle, ref, candidate


def test_revert_candidate_is_deterministic() -> None:
    _bundle, ref, candidate = _fixture()
    _b2, _ref2, candidate_again = _fixture()
    assert candidate == candidate_again
    assert candidate.revert_candidate_id.startswith("flrvc-")
    assert candidate.target_checkpoint_id == ref.checkpoint_id
    assert candidate.affected_run_id == ref.run_id


def test_revert_candidate_safe_to_execute_stays_false() -> None:
    _bundle, _ref, candidate = _fixture()
    assert candidate.safe_to_execute is False
    with pytest.raises(AurelFlowValidationError):
        replace(candidate, safe_to_execute=True)


def test_revert_candidate_cannot_have_rolled_back_or_reverted() -> None:
    _bundle, _ref, candidate = _fixture()
    assert candidate.rollback_executed is False
    assert candidate.external_state_reverted is False
    with pytest.raises(AurelFlowValidationError):
        replace(candidate, rollback_executed=True)
    with pytest.raises(AurelFlowValidationError):
        replace(candidate, external_state_reverted=True)


def test_revert_candidate_requires_operator_p4_p5_p9() -> None:
    _bundle, _ref, candidate = _fixture()
    for law_field in (
        "requires_operator_review",
        "requires_authority",
        "requires_p4_execution",
        "requires_p5_proof",
        "requires_p9_authority",
    ):
        assert getattr(candidate, law_field) is True
        with pytest.raises(AurelFlowValidationError):
            replace(candidate, **{law_field: False})


def test_revert_candidate_records_external_side_effects_honestly() -> None:
    _bundle, ref, candidate = _fixture()
    assert candidate.external_side_effects_present is True
    clean = create_runtime_revert_candidate(target_checkpoint=ref)
    assert clean.external_side_effects_present is False


def test_rollback_execution_boundary_laws_fail_closed() -> None:
    boundary = build_rollback_execution_boundary()
    assert boundary.rollback_candidate_is_not_execution is True
    assert boundary.revert_candidate_is_not_external_revert is True
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, rollback_executes=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, revert_executes=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, rollback_grants_authority=True)
    with pytest.raises(AurelFlowValidationError):
        replace(boundary, rollback_candidate_is_not_execution=False)


def test_revert_safety_frame_carries_candidate_posture() -> None:
    _bundle, _ref, candidate = _fixture()
    frame = build_revert_safety_frame(candidate)
    assert frame.revert_candidate_id == candidate.revert_candidate_id
    assert frame.run_id == candidate.affected_run_id
    assert frame.external_side_effects_present is True
    assert frame.safe_to_execute is False
    with pytest.raises(AurelFlowValidationError):
        replace(frame, safe_to_execute=True)
    with pytest.raises(AurelFlowValidationError):
        replace(frame, requires_p9_authority=False)


def test_rollback_authority_requirement_grants_nothing() -> None:
    _bundle, _ref, candidate = _fixture()
    requirement = build_rollback_authority_requirement(candidate)
    assert requirement.authority_granted is False
    assert requirement.permission_granted is False
    with pytest.raises(AurelFlowValidationError):
        replace(requirement, authority_granted=True)
    with pytest.raises(AurelFlowValidationError):
        replace(requirement, permission_granted=True)
    with pytest.raises(AurelFlowValidationError):
        replace(requirement, requires_p4_execution=False)


def test_revert_read_model_reports_no_rollback() -> None:
    _bundle, ref, candidate = _fixture()
    clean = create_runtime_revert_candidate(target_checkpoint=ref)
    read_model = build_revert_read_model((candidate, clean))
    assert read_model.revert_candidate_ids == (
        candidate.revert_candidate_id,
        clean.revert_candidate_id,
    )
    assert read_model.candidates_with_external_side_effects == 1
    assert read_model.any_safe_to_execute is False
    assert read_model.rollback_executed is False
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, any_safe_to_execute=True)
    with pytest.raises(AurelFlowValidationError):
        replace(read_model, rollback_executed=True)


def test_revert_construction_does_not_mutate_demo_run() -> None:
    bundle, ref, _candidate = _fixture()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)
    create_runtime_revert_candidate(target_checkpoint=ref)
    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before
