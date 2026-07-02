"""P3-FLOW-G self-healing projection / React readiness tests.

Every view model is projection-only: no frontend mutation, no UI recovery
execution, no UI authority, no API server, no frontend implementation.
"""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_flow import (
    AurelFlowValidationError,
    DegradationMode,
    DiagnosisConfidence,
    EscalationReason,
    FailureRootCauseCategory,
    FlowTruthLabel,
    RuntimeFailureKind,
    build_detection_frame,
    build_diagnosis_frame,
    build_diagnostic_loop_state,
    build_diagnostic_timeline_view_model,
    build_escalation_view_model,
    build_failure_card_view_model,
    build_flow_demo_bundle,
    build_graceful_degradation_frame,
    build_human_escalation_frame,
    build_monitor_frame,
    build_recover_frame,
    build_recovery_budget_read_model,
    build_recovery_budget_state,
    build_recovery_budget_view_model,
    build_recovery_candidate_view_model,
    build_reliability_control_react_projection_boundary,
    build_self_healing_projection_envelope,
    build_verification_expectation_view_model,
    build_verify_expectation_frame,
    classify_runtime_failure,
    create_recovery_budget,
    create_recovery_candidate_envelope,
    create_root_cause_diagnosis,
    create_runtime_failure_signal,
    select_recovery_candidate,
    DEFAULT_TARGETED_RECOVERY_POLICY,
)


def _projection_fixture():
    bundle = build_flow_demo_bundle()
    run = bundle.run
    signal = create_runtime_failure_signal(
        run,
        failure_kind=RuntimeFailureKind.TOOL_TIMEOUT,
        detail="projection test",
        node_id="fetch",
    )
    classification = classify_runtime_failure(signal)
    diagnosis = create_root_cause_diagnosis(
        signal,
        candidate_root_cause=FailureRootCauseCategory.TOOL_INFRASTRUCTURE,
        confidence=DiagnosisConfidence.MEDIUM,
    )
    selection = select_recovery_candidate(DEFAULT_TARGETED_RECOVERY_POLICY, signal)
    envelope = create_recovery_candidate_envelope(selection, diagnosis=diagnosis)
    monitor = build_monitor_frame(run)
    detection = build_detection_frame(monitor, signal)
    diagnosis_frame = build_diagnosis_frame(detection, diagnosis)
    recover = build_recover_frame(
        diagnosis_frame, recovery_candidate_id=envelope.recovery_candidate_id
    )
    verify = build_verify_expectation_frame(recover)
    loop = build_diagnostic_loop_state(
        monitor,
        detection_frame=detection,
        diagnosis_frame=diagnosis_frame,
        recover_frame=recover,
        verify_expectation_frame=verify,
    )
    budget = create_recovery_budget(run_id=run.run_id)
    budget_read_model = build_recovery_budget_read_model(
        budget, build_recovery_budget_state(budget)
    )
    escalation = build_human_escalation_frame(
        run_id=run.run_id,
        failure_signal_id=signal.failure_signal_id,
        escalation_reason=EscalationReason.HIGH_RISK_RECOVERY,
        detail="projection test escalation",
    )
    degradation = build_graceful_degradation_frame(
        run_id=run.run_id,
        failure_signal_id=signal.failure_signal_id,
        degradation_mode=DegradationMode.PARTIAL_RESULT,
        degradation_reason="projection test degradation",
    )
    return (
        bundle,
        signal,
        classification,
        diagnosis,
        envelope,
        loop,
        verify,
        budget_read_model,
        escalation,
        degradation,
    )


def test_failure_card_view_model_is_projection_only() -> None:
    (_bundle, signal, classification, *_rest) = _projection_fixture()
    card = build_failure_card_view_model(signal, classification)
    assert card.react_projection_only is True
    assert card.frontend_mutation_allowed is False
    assert card.proof_available is False
    assert card.failure_kind == "TOOL_TIMEOUT"
    assert card.severity == "MEDIUM"
    assert card.truth_label is FlowTruthLabel.READ_MODEL_ONLY


def test_failure_card_rejects_foreign_classification() -> None:
    (bundle, signal, _classification, *_rest) = _projection_fixture()
    other_signal = create_runtime_failure_signal(
        bundle.run,
        failure_kind=RuntimeFailureKind.SCHEMA_MISMATCH,
        detail="other",
    )
    with pytest.raises(AurelFlowValidationError):
        build_failure_card_view_model(
            signal, classify_runtime_failure(other_signal)
        )


def test_diagnostic_timeline_lists_all_loop_phases() -> None:
    loop = _projection_fixture()[5]
    timeline = build_diagnostic_timeline_view_model(loop)
    assert timeline.phases_present == (
        "MONITOR",
        "DETECT",
        "DIAGNOSE",
        "RECOVER_CANDIDATE",
        "VERIFY_EXPECTATION",
    )
    assert timeline.react_projection_only is True
    assert timeline.ui_recovery_execution_allowed is False


def test_recovery_candidate_view_model_has_no_execution_path() -> None:
    (_bundle, _signal, _classification, diagnosis, envelope, *_rest) = (
        _projection_fixture()
    )
    view_model = build_recovery_candidate_view_model(envelope, diagnosis=diagnosis)
    assert view_model.ui_recovery_execution_allowed is False
    assert view_model.ui_authority_granted is False
    assert view_model.recovery_executed is False
    assert view_model.requires_pre_recovery_checkpoint is True
    assert "advisory" in view_model.diagnosis_summary


def test_budget_view_model_shows_state_without_permission() -> None:
    (*_rest, budget_read_model, _escalation, _degradation) = _projection_fixture()
    view_model = build_recovery_budget_view_model(budget_read_model)
    assert view_model.budget_availability_is_not_permission is True
    assert view_model.permission_granted is False
    assert view_model.attempts_display == "0/3"


def test_verification_expectation_view_model_is_not_verification() -> None:
    verify = _projection_fixture()[6]
    view_model = build_verification_expectation_view_model(verify)
    assert view_model.verification_required is True
    assert view_model.verification_available is False
    assert view_model.proof_available is False
    assert view_model.trace_verified is False


def test_escalation_view_model_grants_nothing() -> None:
    (*_rest, escalation, _degradation) = _projection_fixture()
    view_model = build_escalation_view_model(escalation)
    assert view_model.approval_granted is False
    assert view_model.ui_authority_granted is False
    assert view_model.requires_operator_review is True


def test_react_projection_boundary_is_fail_closed() -> None:
    boundary = build_reliability_control_react_projection_boundary()
    assert boundary.react_is_projection_only is True
    assert boundary.python_runtime_is_source_of_truth is True
    assert boundary.ui_retry_button_is_not_recovery_execution is True
    assert boundary.ui_approval_is_not_custos_authority is True
    assert boundary.frontend_mutation_allowed is False
    assert boundary.ui_recovery_execution_allowed is False
    assert boundary.api_server_implemented is False
    assert boundary.frontend_implemented is False
    with pytest.raises(AurelFlowValidationError):
        type(boundary)(
            **{
                **{
                    field.name: getattr(boundary, field.name)
                    for field in boundary.__dataclass_fields__.values()
                },
                "frontend_implemented": True,
            }
        )


def test_projection_envelope_is_read_only_and_deterministic() -> None:
    (
        bundle,
        signal,
        classification,
        diagnosis,
        envelope,
        loop,
        verify,
        budget_read_model,
        escalation,
        degradation,
    ) = _projection_fixture()
    def build() -> object:
        return build_self_healing_projection_envelope(
            run_id=bundle.run.run_id,
            failure_cards=(
                build_failure_card_view_model(signal, classification),
            ),
            diagnostic_timelines=(build_diagnostic_timeline_view_model(loop),),
            recovery_candidates=(
                build_recovery_candidate_view_model(envelope, diagnosis=diagnosis),
            ),
            recovery_budgets=(
                build_recovery_budget_view_model(budget_read_model),
            ),
            verification_expectations=(
                build_verification_expectation_view_model(verify),
            ),
            escalations=(build_escalation_view_model(escalation),),
            degradation_frames=(degradation,),
        )

    first = build()
    second = build()
    assert first.envelope_id == second.envelope_id
    assert first.read_only is True
    assert first.react_projection_only is True
    assert first.frontend_mutation_allowed is False
    assert first.ui_recovery_execution_allowed is False
    assert first.api_server_implemented is False
    assert first.frontend_implemented is False
    assert first.projection_boundary.python_runtime_is_source_of_truth is True


def test_projection_envelope_rejects_foreign_view_models() -> None:
    (_bundle, signal, classification, *_rest) = _projection_fixture()
    card = build_failure_card_view_model(signal, classification)
    with pytest.raises(AurelFlowValidationError):
        build_self_healing_projection_envelope(
            run_id="other-run", failure_cards=(card,)
        )


def test_projection_construction_does_not_mutate_demo_run() -> None:
    (bundle, *_rest) = _projection_fixture()
    step_before = bundle.run.state.step
    lifecycle_before = bundle.run.state.lifecycle_status
    history_before = len(bundle.run.history)
    _projection_fixture()
    assert bundle.run.state.step == step_before
    assert bundle.run.state.lifecycle_status is lifecycle_before
    assert len(bundle.run.history) == history_before
