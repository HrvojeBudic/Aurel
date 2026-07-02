"""P3-FLOW-G self-healing projection / React readiness layer (P3.15.25-P3.15.30).

Read-only view models over the reliability control plane for a future
React/AurelShell surface. React is projection only: no component, route,
frontend state, API server, REST, or WebSocket exists or is claimed here.
A UI retry button is not recovery execution, and UI approval is not Custos
authority — this pack does not even define such buttons. The Python runtime
remains the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_diagnosis import (
    FailureClassificationFrame,
    RootCauseDiagnosis,
    RuntimeFailureSignal,
)
from .flow_recovery_budget import (
    GracefulDegradationFrame,
    HumanEscalationFrame,
    RecoveryBudgetReadModel,
)
from .flow_recovery_policy import RecoveryCandidateEnvelope
from .flow_reliability_control import DiagnosticLoopState, VerifyExpectationFrame
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

SELF_HEALING_PROJECTION_ENVELOPE_VERSION = "self_healing_projection_envelope.v1"
DIAGNOSTIC_TIMELINE_VIEW_MODEL_VERSION = "diagnostic_timeline_view_model.v1"
FAILURE_CARD_VIEW_MODEL_VERSION = "failure_card_view_model.v1"
RECOVERY_CANDIDATE_VIEW_MODEL_VERSION = "recovery_candidate_view_model.v1"
RECOVERY_BUDGET_VIEW_MODEL_VERSION = "recovery_budget_view_model.v1"
VERIFICATION_EXPECTATION_VIEW_MODEL_VERSION = (
    "verification_expectation_view_model.v1"
)
ESCALATION_VIEW_MODEL_VERSION = "escalation_view_model.v1"
RELIABILITY_CONTROL_REACT_PROJECTION_BOUNDARY_VERSION = (
    "reliability_control_react_projection_boundary.v1"
)

SELF_HEALING_PROJECTION_UNAVAILABLE_REASON = (
    "no React component, frontend route, frontend state, API server, REST, or "
    "WebSocket exists in P3-FLOW-G; these view models are read-only projection "
    "contracts for a future React/AurelShell surface, and no UI can execute "
    "retry, recovery, or approval through them"
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


@dataclass(frozen=True)
class DiagnosticTimelineViewModel(_CanonicalMixin):
    """Renderable diagnostic-loop timeline. Rendering controls nothing."""

    view_model_id: str
    view_model_version: str
    run_id: str
    loop_state_id: str
    phases_present: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_recovery_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only")
        _forbid_true(
            self, "frontend_mutation_allowed", "ui_recovery_execution_allowed"
        )


def build_diagnostic_timeline_view_model(
    loop_state: DiagnosticLoopState,
) -> DiagnosticTimelineViewModel:
    phases_present = tuple(
        phase_name
        for phase_name, present in (
            ("MONITOR", bool(loop_state.monitor_frame_id)),
            ("DETECT", bool(loop_state.detection_frame_id)),
            ("DIAGNOSE", bool(loop_state.diagnosis_frame_id)),
            ("RECOVER_CANDIDATE", bool(loop_state.recover_frame_id)),
            ("VERIFY_EXPECTATION", bool(loop_state.verify_expectation_frame_id)),
        )
        if present
    )
    payload = {
        "view_model_version": DIAGNOSTIC_TIMELINE_VIEW_MODEL_VERSION,
        "loop_state_id": loop_state.loop_state_id,
        "phases_present": phases_present,
    }
    return DiagnosticTimelineViewModel(
        view_model_id="flvtl-" + stable_hash(payload)[:16],
        view_model_version=DIAGNOSTIC_TIMELINE_VIEW_MODEL_VERSION,
        run_id=loop_state.run_id,
        loop_state_id=loop_state.loop_state_id,
        phases_present=phases_present,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class FailureCardViewModel(_CanonicalMixin):
    """Renderable failure card: kind, severity, category. Not proof."""

    view_model_id: str
    view_model_version: str
    run_id: str
    failure_signal_id: str
    failure_kind: str
    severity: str
    root_cause_category: str
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    frontend_mutation_allowed: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only")
        _forbid_true(self, "frontend_mutation_allowed", "proof_available")


def build_failure_card_view_model(
    failure_signal: RuntimeFailureSignal,
    classification: FailureClassificationFrame,
) -> FailureCardViewModel:
    if classification.failure_signal_id != failure_signal.failure_signal_id:
        raise AurelFlowValidationError(
            f"classification failure signal "
            f"{classification.failure_signal_id!r} does not match failure "
            f"signal {failure_signal.failure_signal_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="classification",
        )
    payload = {
        "view_model_version": FAILURE_CARD_VIEW_MODEL_VERSION,
        "failure_signal_id": failure_signal.failure_signal_id,
        "classification_id": classification.classification_id,
    }
    return FailureCardViewModel(
        view_model_id="flvfc-" + stable_hash(payload)[:16],
        view_model_version=FAILURE_CARD_VIEW_MODEL_VERSION,
        run_id=failure_signal.run_id,
        failure_signal_id=failure_signal.failure_signal_id,
        failure_kind=failure_signal.failure_kind.value,
        severity=classification.severity.value,
        root_cause_category=classification.root_cause_category.value,
        detail=failure_signal.detail,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class RecoveryCandidateViewModel(_CanonicalMixin):
    """Renderable recovery candidate. There is no UI button behind this."""

    view_model_id: str
    view_model_version: str
    run_id: str
    recovery_candidate_id: str
    candidate_kind: str
    requires_pre_recovery_checkpoint: bool
    requires_operator_review: bool
    truth_label: FlowTruthLabel
    diagnosis_summary: str = ""
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    ui_recovery_execution_allowed: bool = False
    ui_authority_granted: bool = False
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "react_projection_only",
            "requires_pre_recovery_checkpoint",
            "requires_operator_review",
        )
        _forbid_true(
            self,
            "ui_recovery_execution_allowed",
            "ui_authority_granted",
            "recovery_executed",
        )


def build_recovery_candidate_view_model(
    envelope: RecoveryCandidateEnvelope,
    *,
    diagnosis: RootCauseDiagnosis | None = None,
) -> RecoveryCandidateViewModel:
    diagnosis_summary = ""
    if diagnosis is not None:
        diagnosis_summary = (
            f"{diagnosis.candidate_root_cause.value} "
            f"({diagnosis.confidence.value} confidence, advisory)"
        )
    payload = {
        "view_model_version": RECOVERY_CANDIDATE_VIEW_MODEL_VERSION,
        "recovery_candidate_id": envelope.recovery_candidate_id,
        "diagnosis_id": diagnosis.diagnosis_id if diagnosis else "",
    }
    return RecoveryCandidateViewModel(
        view_model_id="flvrc-" + stable_hash(payload)[:16],
        view_model_version=RECOVERY_CANDIDATE_VIEW_MODEL_VERSION,
        run_id=envelope.run_id,
        recovery_candidate_id=envelope.recovery_candidate_id,
        candidate_kind=envelope.candidate_kind.value,
        requires_pre_recovery_checkpoint=envelope.requires_pre_recovery_checkpoint,
        requires_operator_review=envelope.requires_operator_review,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        diagnosis_summary=diagnosis_summary,
    )


@dataclass(frozen=True)
class RecoveryBudgetViewModel(_CanonicalMixin):
    """Renderable budget status. Showing budget grants nothing."""

    view_model_id: str
    view_model_version: str
    run_id: str
    budget_id: str
    budget_available: bool
    budget_exhausted: bool
    exhausted_dimensions: tuple[str, ...]
    attempts_display: str
    depth_display: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    budget_availability_is_not_permission: bool = True
    permission_granted: bool = False
    frontend_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "react_projection_only", "budget_availability_is_not_permission"
        )
        _forbid_true(self, "permission_granted", "frontend_mutation_allowed")


def build_recovery_budget_view_model(
    budget_read_model: RecoveryBudgetReadModel,
) -> RecoveryBudgetViewModel:
    payload = {
        "view_model_version": RECOVERY_BUDGET_VIEW_MODEL_VERSION,
        "read_model_hash": budget_read_model.read_model_hash,
    }
    return RecoveryBudgetViewModel(
        view_model_id="flvbg-" + stable_hash(payload)[:16],
        view_model_version=RECOVERY_BUDGET_VIEW_MODEL_VERSION,
        run_id=budget_read_model.run_id,
        budget_id=budget_read_model.budget_id,
        budget_available=budget_read_model.budget_available,
        budget_exhausted=budget_read_model.budget_exhausted,
        exhausted_dimensions=budget_read_model.exhausted_dimensions,
        attempts_display=(
            f"{budget_read_model.attempts_used}/{budget_read_model.attempt_limit}"
        ),
        depth_display=(
            f"{budget_read_model.depth_used}/{budget_read_model.depth_limit}"
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class VerificationExpectationViewModel(_CanonicalMixin):
    """Renderable verification expectation. An expectation is not verification."""

    view_model_id: str
    view_model_version: str
    run_id: str
    verify_expectation_frame_id: str
    recovery_candidate_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    verification_required: bool = True
    verification_available: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "verification_required")
        _forbid_true(
            self, "verification_available", "proof_available", "trace_verified"
        )


def build_verification_expectation_view_model(
    frame: VerifyExpectationFrame,
) -> VerificationExpectationViewModel:
    payload = {
        "view_model_version": VERIFICATION_EXPECTATION_VIEW_MODEL_VERSION,
        "verify_expectation_frame_id": frame.verify_expectation_frame_id,
    }
    return VerificationExpectationViewModel(
        view_model_id="flvve-" + stable_hash(payload)[:16],
        view_model_version=VERIFICATION_EXPECTATION_VIEW_MODEL_VERSION,
        run_id=frame.run_id,
        verify_expectation_frame_id=frame.verify_expectation_frame_id,
        recovery_candidate_id=frame.recovery_candidate_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class EscalationViewModel(_CanonicalMixin):
    """Renderable escalation card. A rendered escalation approves nothing."""

    view_model_id: str
    view_model_version: str
    run_id: str
    escalation_frame_id: str
    escalation_reason: str
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    requires_operator_review: bool = True
    approval_granted: bool = False
    ui_authority_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "requires_operator_review")
        _forbid_true(self, "approval_granted", "ui_authority_granted")


def build_escalation_view_model(frame: HumanEscalationFrame) -> EscalationViewModel:
    payload = {
        "view_model_version": ESCALATION_VIEW_MODEL_VERSION,
        "escalation_frame_id": frame.escalation_frame_id,
    }
    return EscalationViewModel(
        view_model_id="flves-" + stable_hash(payload)[:16],
        view_model_version=ESCALATION_VIEW_MODEL_VERSION,
        run_id=frame.run_id,
        escalation_frame_id=frame.escalation_frame_id,
        escalation_reason=frame.escalation_reason.value,
        detail=frame.detail,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class ReliabilityControlReactProjectionBoundary(_CanonicalMixin):
    """The React projection law for self-healing state, fail-closed."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_is_projection_only: bool = True
    python_runtime_is_source_of_truth: bool = True
    ui_retry_button_is_not_recovery_execution: bool = True
    ui_approval_is_not_custos_authority: bool = True
    frontend_mutation_allowed: bool = False
    ui_recovery_execution_allowed: bool = False
    ui_authority_granted: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "react_is_projection_only",
            "python_runtime_is_source_of_truth",
            "ui_retry_button_is_not_recovery_execution",
            "ui_approval_is_not_custos_authority",
        )
        _forbid_true(
            self,
            "frontend_mutation_allowed",
            "ui_recovery_execution_allowed",
            "ui_authority_granted",
            "api_server_implemented",
            "frontend_implemented",
        )


def build_reliability_control_react_projection_boundary() -> (
    ReliabilityControlReactProjectionBoundary
):
    payload = {
        "boundary_version": (
            RELIABILITY_CONTROL_REACT_PROJECTION_BOUNDARY_VERSION
        )
    }
    return ReliabilityControlReactProjectionBoundary(
        boundary_version=RELIABILITY_CONTROL_REACT_PROJECTION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class SelfHealingProjectionEnvelope(_CanonicalMixin):
    """Everything a future React/AurelShell may render about self-healing.

    Read-only by law: the envelope embeds the projection boundary and every
    view model it carries is projection-only.
    """

    envelope_id: str
    envelope_version: str
    run_id: str
    failure_cards: tuple[FailureCardViewModel, ...]
    diagnostic_timelines: tuple[DiagnosticTimelineViewModel, ...]
    recovery_candidates: tuple[RecoveryCandidateViewModel, ...]
    recovery_budgets: tuple[RecoveryBudgetViewModel, ...]
    verification_expectations: tuple[VerificationExpectationViewModel, ...]
    escalations: tuple[EscalationViewModel, ...]
    projection_boundary: ReliabilityControlReactProjectionBoundary
    truth_label: FlowTruthLabel
    envelope_hash: str = ""
    degradation_frame_ids: tuple[str, ...] = ()
    unavailable_reason: str = SELF_HEALING_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_recovery_execution_allowed: bool = False
    ui_authority_granted: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(
            self,
            "frontend_mutation_allowed",
            "ui_recovery_execution_allowed",
            "ui_authority_granted",
            "api_server_implemented",
            "frontend_implemented",
        )


def build_self_healing_projection_envelope(
    *,
    run_id: str,
    failure_cards: tuple[FailureCardViewModel, ...] = (),
    diagnostic_timelines: tuple[DiagnosticTimelineViewModel, ...] = (),
    recovery_candidates: tuple[RecoveryCandidateViewModel, ...] = (),
    recovery_budgets: tuple[RecoveryBudgetViewModel, ...] = (),
    verification_expectations: tuple[
        VerificationExpectationViewModel, ...
    ] = (),
    escalations: tuple[EscalationViewModel, ...] = (),
    degradation_frames: tuple[GracefulDegradationFrame, ...] = (),
) -> SelfHealingProjectionEnvelope:
    view_model_run_ids = (
        tuple(card.run_id for card in failure_cards)
        + tuple(timeline.run_id for timeline in diagnostic_timelines)
        + tuple(candidate.run_id for candidate in recovery_candidates)
        + tuple(budget.run_id for budget in recovery_budgets)
        + tuple(expectation.run_id for expectation in verification_expectations)
        + tuple(escalation.run_id for escalation in escalations)
        + tuple(frame.run_id for frame in degradation_frames)
    )
    for view_model_run_id in view_model_run_ids:
        if view_model_run_id != run_id:
            raise AurelFlowValidationError(
                f"view model run {view_model_run_id!r} does not match "
                f"envelope run {run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="view_models",
            )
    payload = {
        "envelope_version": SELF_HEALING_PROJECTION_ENVELOPE_VERSION,
        "run_id": run_id,
        "failure_card_ids": tuple(card.view_model_id for card in failure_cards),
        "timeline_ids": tuple(
            timeline.view_model_id for timeline in diagnostic_timelines
        ),
        "candidate_ids": tuple(
            candidate.view_model_id for candidate in recovery_candidates
        ),
        "budget_ids": tuple(budget.view_model_id for budget in recovery_budgets),
        "expectation_ids": tuple(
            expectation.view_model_id
            for expectation in verification_expectations
        ),
        "escalation_ids": tuple(
            escalation.view_model_id for escalation in escalations
        ),
        "degradation_frame_ids": tuple(
            frame.degradation_frame_id for frame in degradation_frames
        ),
    }
    return SelfHealingProjectionEnvelope(
        envelope_id="flshp-" + stable_hash(payload)[:16],
        envelope_version=SELF_HEALING_PROJECTION_ENVELOPE_VERSION,
        run_id=run_id,
        failure_cards=failure_cards,
        diagnostic_timelines=diagnostic_timelines,
        recovery_candidates=recovery_candidates,
        recovery_budgets=recovery_budgets,
        verification_expectations=verification_expectations,
        escalations=escalations,
        projection_boundary=build_reliability_control_react_projection_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        envelope_hash=stable_hash(payload),
        degradation_frame_ids=tuple(
            frame.degradation_frame_id for frame in degradation_frames
        ),
    )
