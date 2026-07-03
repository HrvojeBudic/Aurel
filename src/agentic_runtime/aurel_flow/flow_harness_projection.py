"""P3-FLOW-K evaluation projection / P3 seal input / K boundary proofs (P3.19).

React is projection only: a UI quality score is not approval, a UI harness
action is not runtime execution, and a UI readiness badge is not production
readiness. The P3 seal input frame gathers what P3-FLOW-L will need and is
structurally not the final seal (`final_seal_performed` is unconstructible
True and `requires_p3_flow_l` unconstructible False). The K boundary proofs
are named Harness* because the P3-FLOW-I pack already exports
NoExecutionBoundaryProof from flow_scheduling_projection.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_boundary_probes import (
    BoundaryComplianceReadModel,
    RuntimeInvariantReadModel,
)
from .flow_harness_evaluation import (
    ContractCoverageMatrix,
    RuntimeHarnessEvaluationRun,
)
from .flow_quality_ops import (
    P4HandoffReadinessAssessment,
    QualityScorecardReadModel,
    RegressionGuardReadModel,
    RuntimeQualityScorecard,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

EVALUATION_RUN_VIEW_MODEL_VERSION = "evaluation_run_view_model.v1"
COVERAGE_MATRIX_VIEW_MODEL_VERSION = "coverage_matrix_view_model.v1"
BOUNDARY_COMPLIANCE_VIEW_MODEL_VERSION = "boundary_compliance_view_model.v1"
INVARIANT_FINDING_VIEW_MODEL_VERSION = "invariant_finding_view_model.v1"
QUALITY_SCORECARD_VIEW_MODEL_VERSION = "quality_scorecard_view_model.v1"
P4_HANDOFF_READINESS_VIEW_MODEL_VERSION = (
    "p4_handoff_readiness_view_model.v1"
)
REGRESSION_GUARD_VIEW_MODEL_VERSION = "regression_guard_view_model.v1"
HARNESS_EVALUATION_PROJECTION_ENVELOPE_VERSION = (
    "harness_evaluation_projection_envelope.v1"
)
HARNESS_EVALUATION_REACT_PROJECTION_BOUNDARY_VERSION = (
    "harness_evaluation_react_projection_boundary.v1"
)
P3_SEAL_INPUT_FRAME_VERSION = "p3_seal_input_frame.v1"
P3_SEAL_READINESS_FINDING_VERSION = "p3_seal_readiness_finding.v1"
P3_SEAL_BLOCKING_RISK_VERSION = "p3_seal_blocking_risk.v1"
P3_SEAL_INPUT_READ_MODEL_VERSION = "p3_seal_input_read_model.v1"
HARNESS_NO_EXECUTION_PROOF_VERSION = "harness_no_execution_boundary_proof.v1"
HARNESS_NO_PROOF_PROOF_VERSION = "harness_no_proof_boundary_proof.v1"
HARNESS_NO_PRODUCTION_CLAIM_PROOF_VERSION = (
    "harness_no_production_claim_boundary_proof.v1"
)
P4_READINESS_NOT_P4_PROOF_VERSION = "p4_readiness_not_p4_proof.v1"

EVALUATION_PROJECTION_UNAVAILABLE_REASON = (
    "no React component, frontend route, frontend state, API server, REST, "
    "or WebSocket exists in P3-FLOW-K; these view models are read-only — a "
    "UI quality score is not approval, a UI harness action is not runtime "
    "execution, and a UI readiness badge is not production readiness"
)
SEAL_INPUT_UNAVAILABLE_REASON = (
    "a P3 seal input frame gathers evidence pointers for P3-FLOW-L: the "
    "final P3 seal is not performed here, seal readiness is not seal "
    "approval, and nothing becomes production-ready or trace-verified"
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


_UI_POWERLESSNESS_FALSE_FIELDS: tuple[str, ...] = (
    "frontend_mutation_allowed",
    "ui_quality_score_approval",
    "ui_harness_execution_allowed",
    "ui_production_ready_badge_authoritative",
    "api_server_implemented",
    "frontend_implemented",
)


@dataclass(frozen=True)
class _HarnessViewModelBase(_CanonicalMixin):
    """Shared UI-powerlessness boundary for every evaluation view model."""

    view_model_id: str
    contract_version: str
    evaluation_run_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = EVALUATION_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_quality_score_approval: bool = False
    ui_harness_execution_allowed: bool = False
    ui_production_ready_badge_authoritative: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(self, *_UI_POWERLESSNESS_FALSE_FIELDS)


@dataclass(frozen=True)
class EvaluationRunViewModel(_HarnessViewModelBase):
    """One harness run, rendered read-only."""

    run_label: str = ""
    target_pack_range: str = ""
    case_count: int = 0


@dataclass(frozen=True)
class CoverageMatrixViewModel(_HarnessViewModelBase):
    """One coverage matrix, rendered read-only."""

    coverage_matrix_id: str = ""
    covered_count: int = 0
    partial_count: int = 0
    missing_count: int = 0
    blocked_count: int = 0


@dataclass(frozen=True)
class BoundaryComplianceViewModel(_HarnessViewModelBase):
    """Boundary compliance posture, rendered read-only."""

    compliance_read_model_id: str = ""
    probe_count: int = 0
    failing_probe_ids: tuple[str, ...] = ()
    all_applicable_passed: bool = False


@dataclass(frozen=True)
class InvariantFindingViewModel(_HarnessViewModelBase):
    """Invariant posture, rendered read-only."""

    invariant_read_model_id: str = ""
    probe_count: int = 0
    violated_probe_ids: tuple[str, ...] = ()
    all_applicable_satisfied: bool = False


@dataclass(frozen=True)
class QualityScorecardViewModel(_HarnessViewModelBase):
    """Advisory scorecard, rendered read-only. Never an approval badge."""

    scorecard_id: str = ""
    metric_status_values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class P4HandoffReadinessViewModel(_HarnessViewModelBase):
    """P4 readiness posture, rendered read-only. Badge is not readiness."""

    p4_handoff_readiness_id: str = ""
    satisfied_count: int = 0
    check_count: int = 0
    gap_count: int = 0
    ready_candidate: bool = False


@dataclass(frozen=True)
class RegressionGuardViewModel(_HarnessViewModelBase):
    """Regression guard posture, rendered read-only."""

    guard_read_model_id: str = ""
    guard_rail_count: int = 0
    failing_guard_kind_values: tuple[str, ...] = ()
    all_passed: bool = False


def build_evaluation_run_view_model(
    run: RuntimeHarnessEvaluationRun,
) -> EvaluationRunViewModel:
    payload = {
        "contract_version": EVALUATION_RUN_VIEW_MODEL_VERSION,
        "evaluation_run_id": run.evaluation_run_id,
    }
    return EvaluationRunViewModel(
        view_model_id="flkvr-" + stable_hash(payload)[:16],
        contract_version=EVALUATION_RUN_VIEW_MODEL_VERSION,
        evaluation_run_id=run.evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        run_label=run.run_label,
        target_pack_range=run.target_pack_range,
        case_count=len(run.evaluation_case_ids),
    )


def build_coverage_matrix_view_model(
    matrix: ContractCoverageMatrix,
) -> CoverageMatrixViewModel:
    payload = {
        "contract_version": COVERAGE_MATRIX_VIEW_MODEL_VERSION,
        "coverage_matrix_id": matrix.coverage_matrix_id,
    }
    return CoverageMatrixViewModel(
        view_model_id="flkvc-" + stable_hash(payload)[:16],
        contract_version=COVERAGE_MATRIX_VIEW_MODEL_VERSION,
        evaluation_run_id=matrix.evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        coverage_matrix_id=matrix.coverage_matrix_id,
        covered_count=matrix.covered_count,
        partial_count=matrix.partial_count,
        missing_count=matrix.missing_count,
        blocked_count=matrix.blocked_count,
    )


def build_boundary_compliance_view_model(
    *,
    evaluation_run_id: str,
    read_model: BoundaryComplianceReadModel,
) -> BoundaryComplianceViewModel:
    payload = {
        "contract_version": BOUNDARY_COMPLIANCE_VIEW_MODEL_VERSION,
        "compliance_read_model_id": read_model.read_model_id,
    }
    return BoundaryComplianceViewModel(
        view_model_id="flkvb-" + stable_hash(payload)[:16],
        contract_version=BOUNDARY_COMPLIANCE_VIEW_MODEL_VERSION,
        evaluation_run_id=evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        compliance_read_model_id=read_model.read_model_id,
        probe_count=read_model.probe_count,
        failing_probe_ids=read_model.failing_probe_ids,
        all_applicable_passed=read_model.all_applicable_passed,
    )


def build_invariant_finding_view_model(
    *,
    evaluation_run_id: str,
    read_model: RuntimeInvariantReadModel,
) -> InvariantFindingViewModel:
    payload = {
        "contract_version": INVARIANT_FINDING_VIEW_MODEL_VERSION,
        "invariant_read_model_id": read_model.read_model_id,
    }
    return InvariantFindingViewModel(
        view_model_id="flkvi-" + stable_hash(payload)[:16],
        contract_version=INVARIANT_FINDING_VIEW_MODEL_VERSION,
        evaluation_run_id=evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        invariant_read_model_id=read_model.read_model_id,
        probe_count=read_model.probe_count,
        violated_probe_ids=read_model.violated_probe_ids,
        all_applicable_satisfied=read_model.all_applicable_satisfied,
    )


def build_quality_scorecard_view_model(
    scorecard: RuntimeQualityScorecard,
) -> QualityScorecardViewModel:
    payload = {
        "contract_version": QUALITY_SCORECARD_VIEW_MODEL_VERSION,
        "scorecard_id": scorecard.scorecard_id,
    }
    return QualityScorecardViewModel(
        view_model_id="flkvq-" + stable_hash(payload)[:16],
        contract_version=QUALITY_SCORECARD_VIEW_MODEL_VERSION,
        evaluation_run_id=scorecard.evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        scorecard_id=scorecard.scorecard_id,
        metric_status_values=tuple(
            (item.metric.value, item.status.value)
            for item in scorecard.metric_items
        ),
    )


def build_p4_handoff_readiness_view_model(
    assessment: P4HandoffReadinessAssessment,
) -> P4HandoffReadinessViewModel:
    payload = {
        "contract_version": P4_HANDOFF_READINESS_VIEW_MODEL_VERSION,
        "p4_handoff_readiness_id": assessment.p4_handoff_readiness_id,
    }
    return P4HandoffReadinessViewModel(
        view_model_id="flkvp-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_READINESS_VIEW_MODEL_VERSION,
        evaluation_run_id=assessment.evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        p4_handoff_readiness_id=assessment.p4_handoff_readiness_id,
        satisfied_count=sum(
            1
            for _check, satisfied in assessment.readiness_check_results
            if satisfied
        ),
        check_count=len(assessment.readiness_check_results),
        gap_count=len(assessment.gaps),
        ready_candidate=assessment.ready_candidate,
    )


def build_regression_guard_view_model(
    *,
    evaluation_run_id: str,
    read_model: RegressionGuardReadModel,
) -> RegressionGuardViewModel:
    payload = {
        "contract_version": REGRESSION_GUARD_VIEW_MODEL_VERSION,
        "guard_read_model_id": read_model.read_model_id,
    }
    return RegressionGuardViewModel(
        view_model_id="flkvg-" + stable_hash(payload)[:16],
        contract_version=REGRESSION_GUARD_VIEW_MODEL_VERSION,
        evaluation_run_id=evaluation_run_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        guard_read_model_id=read_model.read_model_id,
        guard_rail_count=read_model.guard_rail_count,
        failing_guard_kind_values=read_model.failing_guard_kind_values,
        all_passed=read_model.all_passed,
    )


@dataclass(frozen=True)
class HarnessEvaluationReactProjectionBoundary(_CanonicalMixin):
    """The evaluation React law as fail-closed data."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    runtime_source_of_truth: str = "python"
    unavailable_reason: str = EVALUATION_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    ui_quality_score_is_not_approval: bool = True
    ui_harness_action_is_not_execution: bool = True
    ui_readiness_badge_is_not_production_readiness: bool = True
    frontend_mutation_allowed: bool = False
    ui_quality_score_approval: bool = False
    ui_harness_execution_allowed: bool = False
    ui_production_ready_badge_authoritative: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "react_projection_only",
            "ui_quality_score_is_not_approval",
            "ui_harness_action_is_not_execution",
            "ui_readiness_badge_is_not_production_readiness",
        )
        _forbid_true(self, *_UI_POWERLESSNESS_FALSE_FIELDS)
        if self.runtime_source_of_truth != "python":
            raise AurelFlowValidationError(
                "the Python runtime is the P3 source of truth",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_source_of_truth",
            )


def build_harness_react_projection_boundary() -> (
    HarnessEvaluationReactProjectionBoundary
):
    payload = {
        "contract_version": (
            HARNESS_EVALUATION_REACT_PROJECTION_BOUNDARY_VERSION
        )
    }
    return HarnessEvaluationReactProjectionBoundary(
        boundary_id="flkrb-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_REACT_PROJECTION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class HarnessEvaluationProjectionEnvelope(_CanonicalMixin):
    """Everything a future surface may render about P3 evaluation."""

    projection_envelope_id: str
    contract_version: str
    evaluation_run_id: str
    run_view: EvaluationRunViewModel
    coverage_view: CoverageMatrixViewModel | None
    compliance_view: BoundaryComplianceViewModel | None
    invariant_view: InvariantFindingViewModel | None
    scorecard_view: QualityScorecardViewModel | None
    p4_readiness_view: P4HandoffReadinessViewModel | None
    guard_view: RegressionGuardViewModel | None
    boundary: HarnessEvaluationReactProjectionBoundary
    truth_label: FlowTruthLabel
    unavailable_reason: str = EVALUATION_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_quality_score_approval: bool = False
    ui_harness_execution_allowed: bool = False
    ui_production_ready_badge_authoritative: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(self, *_UI_POWERLESSNESS_FALSE_FIELDS)


def build_harness_evaluation_projection_envelope(
    *,
    run_view: EvaluationRunViewModel,
    coverage_view: CoverageMatrixViewModel | None = None,
    compliance_view: BoundaryComplianceViewModel | None = None,
    invariant_view: InvariantFindingViewModel | None = None,
    scorecard_view: QualityScorecardViewModel | None = None,
    p4_readiness_view: P4HandoffReadinessViewModel | None = None,
    guard_view: RegressionGuardViewModel | None = None,
) -> HarnessEvaluationProjectionEnvelope:
    views = tuple(
        view
        for view in (
            coverage_view,
            compliance_view,
            invariant_view,
            scorecard_view,
            p4_readiness_view,
            guard_view,
        )
        if view is not None
    )
    for view in views:
        if view.evaluation_run_id != run_view.evaluation_run_id:
            raise AurelFlowValidationError(
                f"view {view.view_model_id!r} belongs to run "
                f"{view.evaluation_run_id!r}, not "
                f"{run_view.evaluation_run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="views",
            )
    payload = {
        "contract_version": HARNESS_EVALUATION_PROJECTION_ENVELOPE_VERSION,
        "view_model_ids": tuple(
            sorted(
                [run_view.view_model_id]
                + [view.view_model_id for view in views]
            )
        ),
    }
    return HarnessEvaluationProjectionEnvelope(
        projection_envelope_id="flkpe-" + stable_hash(payload)[:16],
        contract_version=HARNESS_EVALUATION_PROJECTION_ENVELOPE_VERSION,
        evaluation_run_id=run_view.evaluation_run_id,
        run_view=run_view,
        coverage_view=coverage_view,
        compliance_view=compliance_view,
        invariant_view=invariant_view,
        scorecard_view=scorecard_view,
        p4_readiness_view=p4_readiness_view,
        guard_view=guard_view,
        boundary=build_harness_react_projection_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class P3SealReadinessFinding(_CanonicalMixin):
    """One positive readiness observation for P3-FLOW-L. Not approval."""

    finding_id: str
    contract_version: str
    finding_label: str
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    seal_approved: bool = False
    final_seal_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "seal_approved", "final_seal_performed")


@dataclass(frozen=True)
class P3SealBlockingRisk(_CanonicalMixin):
    """One risk P3-FLOW-L must resolve or accept. Not enforcement."""

    risk_id: str
    contract_version: str
    risk_label: str
    detail: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    seal_blocked_by_k: bool = False
    final_seal_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "seal_blocked_by_k", "final_seal_performed")


def _seal_finding(finding_label: str, detail: str) -> P3SealReadinessFinding:
    payload = {
        "contract_version": P3_SEAL_READINESS_FINDING_VERSION,
        "finding_label": finding_label,
        "detail": detail,
    }
    return P3SealReadinessFinding(
        finding_id="flksr-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_READINESS_FINDING_VERSION,
        finding_label=finding_label,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


def _seal_risk(risk_label: str, detail: str) -> P3SealBlockingRisk:
    payload = {
        "contract_version": P3_SEAL_BLOCKING_RISK_VERSION,
        "risk_label": risk_label,
        "detail": detail,
    }
    return P3SealBlockingRisk(
        risk_id="flksk-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_BLOCKING_RISK_VERSION,
        risk_label=risk_label,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P3SealInputFrame(_CanonicalMixin):
    """Evidence pointers for the P3-FLOW-L final seal. Not the seal."""

    seal_input_id: str
    contract_version: str
    evaluation_run_id: str
    coverage_matrix_id: str
    boundary_compliance_read_model_id: str
    invariant_read_model_id: str
    quality_scorecard_id: str
    p4_handoff_readiness_id: str
    readiness_findings: tuple[P3SealReadinessFinding, ...]
    blocking_risks: tuple[P3SealBlockingRisk, ...]
    seal_ready_candidate: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    requires_p3_flow_l: bool = True
    final_seal_performed: bool = False
    production_ready: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p3_flow_l")
        _forbid_true(
            self, "final_seal_performed", "production_ready", "trace_verified"
        )
        if self.seal_ready_candidate and self.blocking_risks:
            raise AurelFlowValidationError(
                "a seal-ready candidate cannot carry blocking risks",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="seal_ready_candidate",
            )


def build_p3_seal_input_frame(
    *,
    run: RuntimeHarnessEvaluationRun,
    coverage_matrix: ContractCoverageMatrix,
    compliance_read_model: BoundaryComplianceReadModel,
    invariant_read_model: RuntimeInvariantReadModel,
    scorecard: RuntimeQualityScorecard,
    p4_assessment: P4HandoffReadinessAssessment,
) -> P3SealInputFrame:
    """Deterministic gather: readiness findings and blocking risks are derived.

    Missing/blocked coverage, failing compliance probes, violated invariants,
    and an unready P4 assessment each become a blocking risk; clean layers
    become readiness findings. Deriving is not sealing.
    """

    for source_name, source_run_id in (
        ("coverage_matrix", coverage_matrix.evaluation_run_id),
        ("scorecard", scorecard.evaluation_run_id),
        ("p4_assessment", p4_assessment.evaluation_run_id),
    ):
        if source_run_id != run.evaluation_run_id:
            raise AurelFlowValidationError(
                f"{source_name} belongs to run {source_run_id!r}, not "
                f"{run.evaluation_run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field=source_name,
            )
    findings: list[P3SealReadinessFinding] = []
    risks: list[P3SealBlockingRisk] = []
    if coverage_matrix.missing_count or coverage_matrix.blocked_count:
        risks.append(
            _seal_risk(
                "COVERAGE_GAPS",
                f"{coverage_matrix.missing_count} missing and "
                f"{coverage_matrix.blocked_count} blocked coverage areas",
            )
        )
    else:
        findings.append(
            _seal_finding(
                "COVERAGE_REPRESENTED",
                "no coverage area is missing or blocked",
            )
        )
    if compliance_read_model.failing_probe_ids:
        risks.append(
            _seal_risk(
                "BOUNDARY_COMPLIANCE_FAILURES",
                f"{len(compliance_read_model.failing_probe_ids)} failing "
                "compliance probes",
            )
        )
    else:
        findings.append(
            _seal_finding(
                "BOUNDARY_COMPLIANCE_CLEAN",
                "no applicable compliance probe failed",
            )
        )
    if invariant_read_model.violated_probe_ids:
        risks.append(
            _seal_risk(
                "INVARIANT_VIOLATIONS",
                f"{len(invariant_read_model.violated_probe_ids)} violated "
                "invariant probes",
            )
        )
    else:
        findings.append(
            _seal_finding(
                "INVARIANTS_SATISFIED",
                "no applicable invariant probe is violated",
            )
        )
    if not p4_assessment.ready_candidate:
        risks.append(
            _seal_risk(
                "P4_READINESS_GAPS",
                f"{len(p4_assessment.gaps)} P4 readiness gaps remain visible",
            )
        )
    else:
        findings.append(
            _seal_finding(
                "P4_HANDOFF_READY_CANDIDATE",
                "every P4 readiness check is satisfied (candidate only)",
            )
        )
    payload = {
        "contract_version": P3_SEAL_INPUT_FRAME_VERSION,
        "evaluation_run_id": run.evaluation_run_id,
        "coverage_matrix_id": coverage_matrix.coverage_matrix_id,
        "compliance_read_model_id": compliance_read_model.read_model_id,
        "invariant_read_model_id": invariant_read_model.read_model_id,
        "quality_scorecard_id": scorecard.scorecard_id,
        "p4_handoff_readiness_id": p4_assessment.p4_handoff_readiness_id,
    }
    return P3SealInputFrame(
        seal_input_id="flksi-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_INPUT_FRAME_VERSION,
        evaluation_run_id=run.evaluation_run_id,
        coverage_matrix_id=coverage_matrix.coverage_matrix_id,
        boundary_compliance_read_model_id=compliance_read_model.read_model_id,
        invariant_read_model_id=invariant_read_model.read_model_id,
        quality_scorecard_id=scorecard.scorecard_id,
        p4_handoff_readiness_id=p4_assessment.p4_handoff_readiness_id,
        readiness_findings=tuple(findings),
        blocking_risks=tuple(risks),
        seal_ready_candidate=not risks,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class P3SealInputReadModel(_CanonicalMixin):
    """Deterministic read model over one seal input frame."""

    read_model_id: str
    contract_version: str
    seal_input_id: str
    evaluation_run_id: str
    readiness_finding_count: int
    blocking_risk_count: int
    seal_ready_candidate: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    requires_p3_flow_l: bool = True
    final_seal_performed: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_p3_flow_l")
        _forbid_true(self, "final_seal_performed", "production_ready")


def build_p3_seal_input_read_model(
    frame: P3SealInputFrame,
) -> P3SealInputReadModel:
    payload = {
        "contract_version": P3_SEAL_INPUT_READ_MODEL_VERSION,
        "seal_input_id": frame.seal_input_id,
    }
    return P3SealInputReadModel(
        read_model_id="flksn-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_INPUT_READ_MODEL_VERSION,
        seal_input_id=frame.seal_input_id,
        evaluation_run_id=frame.evaluation_run_id,
        readiness_finding_count=len(frame.readiness_findings),
        blocking_risk_count=len(frame.blocking_risks),
        seal_ready_candidate=frame.seal_ready_candidate,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class HarnessNoExecutionBoundaryProof(_CanonicalMixin):
    """All-false execution booleans for the K layer. Report evidence only.

    Named Harness* because P3-FLOW-I already exports NoExecutionBoundaryProof.
    """

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    workflow_executed: bool = False
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    execution_available: bool = False
    service_runtime_available: bool = False
    network_called: bool = False
    model_invoked: bool = False
    tool_invoked: bool = False
    sandbox_executed: bool = False
    trace_written: bool = False
    ledger_written: bool = False
    memory_access_performed: bool = False
    policy_mutated: bool = False
    identity_mutated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "workflow_executed",
            "runtime_submit_wired",
            "dispatch_available",
            "execution_available",
            "service_runtime_available",
            "network_called",
            "model_invoked",
            "tool_invoked",
            "sandbox_executed",
            "trace_written",
            "ledger_written",
            "memory_access_performed",
            "policy_mutated",
            "identity_mutated",
        )


@dataclass(frozen=True)
class HarnessNoProofBoundaryProof(_CanonicalMixin):
    """Evaluation results are never proof. Report evidence only."""

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    proof_available: bool = False
    trace_verified: bool = False
    harness_result_is_proof: bool = False
    coverage_is_proof: bool = False
    score_is_proof: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "proof_available",
            "trace_verified",
            "harness_result_is_proof",
            "coverage_is_proof",
            "score_is_proof",
        )


@dataclass(frozen=True)
class HarnessNoProductionClaimBoundaryProof(_CanonicalMixin):
    """No K object claims production readiness. Report evidence only."""

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    production_ready: bool = False
    release_approved: bool = False
    operator_approval_granted: bool = False
    final_seal_performed: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "production_ready",
            "release_approved",
            "operator_approval_granted",
            "final_seal_performed",
            "live_claimed",
            "trace_verified_claimed",
        )


@dataclass(frozen=True)
class P4ReadinessNotP4Proof(_CanonicalMixin):
    """P4 readiness assessment is not P4. Report evidence only."""

    proof_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_INPUT_UNAVAILABLE_REASON
    is_p5_trace_proof: bool = False
    p4_implemented: bool = False
    runtime_submit_wired: bool = False
    dispatch_available: bool = False
    execution_available: bool = False
    worker_allocated: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "is_p5_trace_proof",
            "p4_implemented",
            "runtime_submit_wired",
            "dispatch_available",
            "execution_available",
            "worker_allocated",
        )


def build_harness_no_execution_boundary_proof() -> (
    HarnessNoExecutionBoundaryProof
):
    payload = {"contract_version": HARNESS_NO_EXECUTION_PROOF_VERSION}
    return HarnessNoExecutionBoundaryProof(
        proof_id="flkxp-" + stable_hash(payload)[:16],
        contract_version=HARNESS_NO_EXECUTION_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def build_harness_no_proof_boundary_proof() -> HarnessNoProofBoundaryProof:
    payload = {"contract_version": HARNESS_NO_PROOF_PROOF_VERSION}
    return HarnessNoProofBoundaryProof(
        proof_id="flknp-" + stable_hash(payload)[:16],
        contract_version=HARNESS_NO_PROOF_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def build_harness_no_production_claim_boundary_proof() -> (
    HarnessNoProductionClaimBoundaryProof
):
    payload = {"contract_version": HARNESS_NO_PRODUCTION_CLAIM_PROOF_VERSION}
    return HarnessNoProductionClaimBoundaryProof(
        proof_id="flknc-" + stable_hash(payload)[:16],
        contract_version=HARNESS_NO_PRODUCTION_CLAIM_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def build_p4_readiness_not_p4_proof() -> P4ReadinessNotP4Proof:
    payload = {"contract_version": P4_READINESS_NOT_P4_PROOF_VERSION}
    return P4ReadinessNotP4Proof(
        proof_id="flkn4-" + stable_hash(payload)[:16],
        contract_version=P4_READINESS_NOT_P4_PROOF_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )
