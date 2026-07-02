"""P3-FLOW-G reliability control plane / diagnostic loop tests.

The control plane and diagnostic loop represent self-healing state only:
no phase, transition, or frame executes repair, recovery, or verification.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    ControlLoopPhase,
    ControlLoopTransition,
    DiagnosisConfidence,
    DiagnosisEvidenceKind,
    FailureRootCauseCategory,
    FlowTruthLabel,
    RuntimeFailureKind,
    build_detection_frame,
    build_diagnosis_frame,
    build_diagnostic_loop_read_model,
    build_diagnostic_loop_state,
    build_flow_demo_bundle,
    build_monitor_frame,
    build_recover_frame,
    build_reliability_control_plane_state,
    build_reliability_control_read_model,
    build_self_healing_control_law_boundary,
    build_verify_expectation_frame,
    control_loop_transition,
    create_diagnosis_evidence_ref,
    create_reliability_control_plane,
    create_root_cause_diagnosis,
    create_runtime_failure_signal,
)


def _plane_fixture():
    bundle = build_flow_demo_bundle()
    plane = create_reliability_control_plane(bundle.run, created_by="test")
    return bundle, plane


def _loop_fixture():
    bundle, plane = _plane_fixture()
    monitor = build_monitor_frame(bundle.run)
    signal = create_runtime_failure_signal(
        bundle.run,
        failure_kind=RuntimeFailureKind.TOOL_TIMEOUT,
        detail="test timeout",
        node_id="fetch",
    )
    detection = build_detection_frame(monitor, signal)
    diagnosis = create_root_cause_diagnosis(
        signal,
        candidate_root_cause=FailureRootCauseCategory.TOOL_INFRASTRUCTURE,
        confidence=DiagnosisConfidence.MEDIUM,
        diagnostic_evidence_refs=(
            create_diagnosis_evidence_ref(
                evidence_kind=DiagnosisEvidenceKind.FAILURE_SIGNAL,
                target_id=signal.failure_signal_id,
            ),
        ),
    )
    diagnosis_frame = build_diagnosis_frame(detection, diagnosis)
    recover = build_recover_frame(
        diagnosis_frame, recovery_candidate_id="flrce-testcandidate00"
    )
    verify = build_verify_expectation_frame(recover)
    return bundle, plane, monitor, signal, detection, diagnosis_frame, recover, verify


def test_control_plane_is_deterministic() -> None:
    bundle, plane = _plane_fixture()
    again = create_reliability_control_plane(bundle.run, created_by="test")
    assert again.control_plane_id == plane.control_plane_id
    assert plane.control_plane_id.startswith("flrcp-")
    assert plane.created_at_logical_sequence == bundle.run.state.step


def test_control_plane_cannot_claim_execution_or_verification() -> None:
    bundle, plane = _plane_fixture()
    for forbidden_field in (
        "recovery_executed",
        "verification_available",
        "trace_verified",
        "execution_available",
    ):
        with pytest.raises(AurelFlowValidationError):
            type(plane)(
                **{
                    **{
                        field.name: getattr(plane, field.name)
                        for field in plane.__dataclass_fields__.values()
                    },
                    forbidden_field: True,
                }
            )


def test_control_loop_phase_is_closed_world_without_healed_member() -> None:
    phase_values = {phase.value for phase in ControlLoopPhase}
    assert "RECOVERED" not in phase_values
    assert "HEALED" not in phase_values
    assert "VERIFIED" not in phase_values
    assert {
        "IDLE",
        "MONITORING",
        "DETECTED",
        "DIAGNOSING",
        "DIAGNOSED",
        "RECOVERY_CANDIDATE_SELECTED",
        "WAITING_CHECKPOINT",
        "WAITING_BUDGET_CHECK",
        "WAITING_OPERATOR_REVIEW",
        "WAITING_EXECUTION_PLANE",
        "WAITING_VERIFICATION",
        "DEGRADED",
        "ESCALATED",
        "BLOCKED",
        "UNAVAILABLE",
        "ERROR",
    } == phase_values


def test_control_loop_transition_must_change_phase_and_executes_nothing() -> None:
    bundle, plane = _plane_fixture()
    transition = control_loop_transition(
        control_plane_id=plane.control_plane_id,
        run_id=bundle.run.run_id,
        from_phase=ControlLoopPhase.MONITORING,
        to_phase=ControlLoopPhase.DETECTED,
        reason="test",
        logical_sequence=bundle.run.state.step,
    )
    assert transition.repair_executed is False
    assert transition.recovery_executed is False
    assert transition.stop_executed is False
    with pytest.raises(AurelFlowValidationError):
        control_loop_transition(
            control_plane_id=plane.control_plane_id,
            run_id=bundle.run.run_id,
            from_phase=ControlLoopPhase.MONITORING,
            to_phase=ControlLoopPhase.MONITORING,
            reason="no-op",
            logical_sequence=bundle.run.state.step,
        )


def test_transition_cannot_claim_repair_executed() -> None:
    bundle, plane = _plane_fixture()
    with pytest.raises(AurelFlowValidationError):
        ControlLoopTransition(
            transition_id="flclt-forged00000000",
            contract_version="control_loop_transition.v1",
            control_plane_id=plane.control_plane_id,
            run_id=bundle.run.run_id,
            from_phase=ControlLoopPhase.MONITORING,
            to_phase=ControlLoopPhase.DETECTED,
            reason="forged",
            logical_sequence=0,
            truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
            repair_executed=True,
        )


def test_plane_state_requires_all_future_gates() -> None:
    _bundle, plane = _plane_fixture()
    state = build_reliability_control_plane_state(
        plane, current_phase=ControlLoopPhase.IDLE
    )
    assert state.requires_checkpoint is True
    assert state.requires_budget_check is True
    assert state.requires_operator_review is True
    assert state.requires_p4_execution is True
    assert state.requires_p5_proof is True
    assert state.requires_p9_authority_if_irreversible is True
    assert state.recovery_executed is False


def test_monitor_frame_is_read_only_observation() -> None:
    bundle, _plane = _plane_fixture()
    monitor = build_monitor_frame(bundle.run)
    assert monitor.read_only is True
    assert monitor.mutation_available is False
    assert monitor.observed_step == bundle.run.state.step
    assert monitor.observed_lifecycle_status == (
        bundle.run.state.lifecycle_status.value
    )


def test_detection_frame_rejects_run_mismatch() -> None:
    bundle, _plane = _plane_fixture()
    other_bundle = build_flow_demo_bundle()
    monitor = build_monitor_frame(bundle.run)
    signal = create_runtime_failure_signal(
        other_bundle.run,
        failure_kind=RuntimeFailureKind.TOOL_TIMEOUT,
        detail="mismatch",
    )
    forged_signal = type(signal)(
        **{
            **{
                field.name: getattr(signal, field.name)
                for field in signal.__dataclass_fields__.values()
            },
            "run_id": "other-run",
        }
    )
    with pytest.raises(AurelFlowValidationError):
        build_detection_frame(monitor, forged_signal)


def test_recover_frame_proposes_only_and_verify_frame_expects_only() -> None:
    (*_rest, recover, verify) = _loop_fixture()
    assert recover.proposes_only is True
    assert recover.requires_pre_recovery_checkpoint is True
    assert recover.recovery_executed is False
    assert verify.verification_required is True
    assert verify.verification_available is False
    assert verify.verification_executed is False
    assert verify.proof_available is False
    assert verify.trace_verified is False


def test_diagnostic_loop_state_links_all_frames_without_execution() -> None:
    (
        _bundle,
        _plane,
        monitor,
        signal,
        detection,
        diagnosis_frame,
        recover,
        verify,
    ) = _loop_fixture()
    loop = build_diagnostic_loop_state(
        monitor,
        detection_frame=detection,
        diagnosis_frame=diagnosis_frame,
        recover_frame=recover,
        verify_expectation_frame=verify,
    )
    assert loop.failure_signal_id == signal.failure_signal_id
    assert loop.recovery_executed is False
    read_model = build_diagnostic_loop_read_model(loop)
    assert read_model.has_detection is True
    assert read_model.has_diagnosis is True
    assert read_model.has_recovery_candidate is True
    assert read_model.has_verify_expectation is True
    assert read_model.verification_available is False
    assert read_model.truth_label is FlowTruthLabel.READ_MODEL_ONLY


def test_control_read_model_rejects_foreign_transition() -> None:
    bundle, plane = _plane_fixture()
    state = build_reliability_control_plane_state(
        plane, current_phase=ControlLoopPhase.MONITORING
    )
    foreign = control_loop_transition(
        control_plane_id="flrcp-someoneelse000",
        run_id=bundle.run.run_id,
        from_phase=ControlLoopPhase.IDLE,
        to_phase=ControlLoopPhase.MONITORING,
        reason="foreign",
        logical_sequence=0,
    )
    with pytest.raises(AurelFlowValidationError):
        build_reliability_control_read_model(state, (foreign,))


def test_control_law_boundary_is_fail_closed() -> None:
    boundary = build_self_healing_control_law_boundary()
    assert boundary.detection_is_not_fix is True
    assert boundary.diagnosis_is_not_proof is True
    assert boundary.recovery_candidate_is_not_execution is True
    assert boundary.budget_check_is_not_permission is True
    assert boundary.verification_expectation_is_not_verification is True
    assert boundary.escalation_is_not_approval is True
    assert boundary.control_plane_executes_recovery is False
    assert boundary.control_plane_grants_authority is False


def test_control_plane_construction_does_not_mutate_demo_run() -> None:
    bundle, _plane = _plane_fixture()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)
    _loop_fixture()
    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before
