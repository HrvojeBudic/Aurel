"""P3-FLOW-L read-only seal projection (P3.20).

React is projection only: a UI seal badge is not production readiness, a UI
release-approval control is not authority, and a UI P4 handoff action is not
runtime.submit. No React component, frontend route, API server, REST, or
WebSocket exists; Python remains the P3 source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_domain_seal import (
    KEvaluationSummary,
    P3CoverageSummary,
    P3DomainSeal,
)
from .flow_p3_audit import (
    BoundaryExitAuditReadModel,
    TruthLabelAuditReadModel,
    UnavailableSystemsLedger,
)
from .flow_p4_handoff import (
    P4ExecutionHandoffPackage,
    RuntimeSubmitBoundaryMap,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

P3_SEAL_STATUS_VIEW_MODEL_VERSION = "p3_seal_status_view_model.v1"
P3_COVERAGE_SUMMARY_VIEW_MODEL_VERSION = (
    "p3_coverage_summary_view_model.v1"
)
P3_AUDIT_VIEW_MODEL_VERSION = "p3_audit_view_model.v1"
P4_HANDOFF_VIEW_MODEL_VERSION = "p4_handoff_view_model.v1"
P3_SEAL_REACT_PROJECTION_BOUNDARY_VERSION = (
    "p3_seal_react_projection_boundary.v1"
)
P3_SEAL_PROJECTION_ENVELOPE_VERSION = "p3_seal_projection_envelope.v1"

P3_NEXT_TASK_RECOMMENDATION = (
    "P4-EXEC-A — AurelExec Minimal Execution Bridge / runtime.submit "
    "Boundary"
)
SEAL_PROJECTION_UNAVAILABLE_REASON = (
    "no React component, frontend route, API server, REST, or WebSocket "
    "exists in P3-FLOW-L; these view models are read-only — a UI seal "
    "badge is not production readiness, a UI release approval is not "
    "authority, and a UI P4 handoff action is not runtime.submit"
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


_SEAL_UI_POWERLESSNESS_FALSE_FIELDS: tuple[str, ...] = (
    "frontend_mutation_allowed",
    "ui_release_approval_authority",
    "ui_runtime_submit_allowed",
    "ui_execution_allowed",
    "ui_production_ready_badge_authoritative",
    "api_server_implemented",
    "frontend_implemented",
)


@dataclass(frozen=True)
class _SealViewModelBase(_CanonicalMixin):
    """Shared UI-powerlessness boundary for every seal view model."""

    view_model_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = SEAL_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_release_approval_authority: bool = False
    ui_runtime_submit_allowed: bool = False
    ui_execution_allowed: bool = False
    ui_production_ready_badge_authoritative: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(self, *_SEAL_UI_POWERLESSNESS_FALSE_FIELDS)


@dataclass(frozen=True)
class P3SealStatusViewModel(_SealViewModelBase):
    """The seal badge, rendered read-only. A badge is not readiness."""

    seal_id: str = ""
    p3_control_plane_sealed: bool = True
    sealed_pack_count: int = 0
    production_ready: bool = False
    release_approved: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _forbid_true(self, "production_ready", "release_approved")


@dataclass(frozen=True)
class P3CoverageSummaryViewModel(_SealViewModelBase):
    """A-L coverage counts, rendered read-only."""

    coverage_summary_id: str = ""
    covered_count: int = 0
    partial_count: int = 0
    missing_count: int = 0
    unavailable_count: int = 0
    blocked_count: int = 0
    error_count: int = 0
    fully_covered: bool = False


@dataclass(frozen=True)
class P3AuditViewModel(_SealViewModelBase):
    """Truth-label / boundary-exit / unavailable posture, read-only."""

    truth_label_audit_read_model_id: str = ""
    boundary_exit_read_model_id: str = ""
    unavailable_ledger_id: str = ""
    truth_label_failing_category_values: tuple[str, ...] = ()
    boundary_exit_failing_category_values: tuple[str, ...] = ()
    unavailable_system_count: int = 0


@dataclass(frozen=True)
class P4HandoffViewModel(_SealViewModelBase):
    """P4 handoff posture, rendered read-only. A view dispatches nothing."""

    package_id: str = ""
    boundary_map_id: str = ""
    handoff_surface_count: int = 0
    runtime_submit_primary_status_value: str = ""


def build_p3_seal_status_view_model(
    seal: P3DomainSeal,
) -> P3SealStatusViewModel:
    payload = {
        "contract_version": P3_SEAL_STATUS_VIEW_MODEL_VERSION,
        "seal_id": seal.seal_id,
    }
    return P3SealStatusViewModel(
        view_model_id="fllvs-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_STATUS_VIEW_MODEL_VERSION,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        seal_id=seal.seal_id,
        p3_control_plane_sealed=seal.p3_control_plane_sealed,
        sealed_pack_count=len(seal.sealed_pack_values),
    )


def build_p3_coverage_summary_view_model(
    summary: P3CoverageSummary,
) -> P3CoverageSummaryViewModel:
    payload = {
        "contract_version": P3_COVERAGE_SUMMARY_VIEW_MODEL_VERSION,
        "coverage_summary_id": summary.coverage_summary_id,
    }
    return P3CoverageSummaryViewModel(
        view_model_id="fllvc-" + stable_hash(payload)[:16],
        contract_version=P3_COVERAGE_SUMMARY_VIEW_MODEL_VERSION,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        coverage_summary_id=summary.coverage_summary_id,
        covered_count=summary.covered_count,
        partial_count=summary.partial_count,
        missing_count=summary.missing_count,
        unavailable_count=summary.unavailable_count,
        blocked_count=summary.blocked_count,
        error_count=summary.error_count,
        fully_covered=summary.fully_covered,
    )


def build_p3_audit_view_model(
    *,
    truth_label_audit: TruthLabelAuditReadModel,
    boundary_exit_audit: BoundaryExitAuditReadModel,
    unavailable_ledger: UnavailableSystemsLedger,
) -> P3AuditViewModel:
    payload = {
        "contract_version": P3_AUDIT_VIEW_MODEL_VERSION,
        "truth_label_audit_read_model_id": truth_label_audit.read_model_id,
        "boundary_exit_read_model_id": boundary_exit_audit.read_model_id,
        "unavailable_ledger_id": unavailable_ledger.ledger_id,
    }
    return P3AuditViewModel(
        view_model_id="fllva-" + stable_hash(payload)[:16],
        contract_version=P3_AUDIT_VIEW_MODEL_VERSION,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        truth_label_audit_read_model_id=truth_label_audit.read_model_id,
        boundary_exit_read_model_id=boundary_exit_audit.read_model_id,
        unavailable_ledger_id=unavailable_ledger.ledger_id,
        truth_label_failing_category_values=(
            truth_label_audit.failing_category_values
        ),
        boundary_exit_failing_category_values=(
            boundary_exit_audit.failing_category_values
        ),
        unavailable_system_count=len(unavailable_ledger.entries),
    )


def build_p4_handoff_view_model(
    *,
    package: P4ExecutionHandoffPackage,
    boundary_map: RuntimeSubmitBoundaryMap,
) -> P4HandoffViewModel:
    payload = {
        "contract_version": P4_HANDOFF_VIEW_MODEL_VERSION,
        "package_id": package.package_id,
        "boundary_map_id": boundary_map.boundary_map_id,
    }
    return P4HandoffViewModel(
        view_model_id="fllvh-" + stable_hash(payload)[:16],
        contract_version=P4_HANDOFF_VIEW_MODEL_VERSION,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        package_id=package.package_id,
        boundary_map_id=boundary_map.boundary_map_id,
        handoff_surface_count=len(package.items),
        runtime_submit_primary_status_value=(
            boundary_map.primary_status.value
        ),
    )


@dataclass(frozen=True)
class P3SealReactProjectionBoundary(_CanonicalMixin):
    """The seal React law as fail-closed data."""

    boundary_id: str
    contract_version: str
    truth_label: FlowTruthLabel
    runtime_source_of_truth: str = "python"
    unavailable_reason: str = SEAL_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    ui_seal_badge_is_not_production_readiness: bool = True
    ui_release_approval_is_not_authority: bool = True
    ui_handoff_action_is_not_runtime_submit: bool = True
    frontend_mutation_allowed: bool = False
    ui_release_approval_authority: bool = False
    ui_runtime_submit_allowed: bool = False
    ui_execution_allowed: bool = False
    ui_production_ready_badge_authoritative: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "react_projection_only",
            "ui_seal_badge_is_not_production_readiness",
            "ui_release_approval_is_not_authority",
            "ui_handoff_action_is_not_runtime_submit",
        )
        _forbid_true(self, *_SEAL_UI_POWERLESSNESS_FALSE_FIELDS)
        if self.runtime_source_of_truth != "python":
            raise AurelFlowValidationError(
                "the Python runtime is the P3 source of truth",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_source_of_truth",
            )


def build_p3_seal_react_projection_boundary() -> (
    P3SealReactProjectionBoundary
):
    payload = {
        "contract_version": P3_SEAL_REACT_PROJECTION_BOUNDARY_VERSION
    }
    return P3SealReactProjectionBoundary(
        boundary_id="fllrb-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_REACT_PROJECTION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class P3SealProjectionEnvelope(_CanonicalMixin):
    """Everything a future surface may render about the P3 seal."""

    projection_envelope_id: str
    contract_version: str
    seal_view: P3SealStatusViewModel
    coverage_view: P3CoverageSummaryViewModel
    audit_view: P3AuditViewModel
    handoff_view: P4HandoffViewModel
    k_evaluation_summary_id: str
    boundary: P3SealReactProjectionBoundary
    truth_label: FlowTruthLabel
    next_task_recommendation: str = P3_NEXT_TASK_RECOMMENDATION
    unavailable_reason: str = SEAL_PROJECTION_UNAVAILABLE_REASON
    react_projection_only: bool = True
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_release_approval_authority: bool = False
    ui_runtime_submit_allowed: bool = False
    ui_execution_allowed: bool = False
    ui_production_ready_badge_authoritative: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "react_projection_only", "read_only")
        _forbid_true(self, *_SEAL_UI_POWERLESSNESS_FALSE_FIELDS)


def build_p3_seal_projection_envelope(
    *,
    seal_view: P3SealStatusViewModel,
    coverage_view: P3CoverageSummaryViewModel,
    audit_view: P3AuditViewModel,
    handoff_view: P4HandoffViewModel,
    k_evaluation_summary: KEvaluationSummary,
) -> P3SealProjectionEnvelope:
    payload = {
        "contract_version": P3_SEAL_PROJECTION_ENVELOPE_VERSION,
        "view_model_ids": tuple(
            sorted(
                (
                    seal_view.view_model_id,
                    coverage_view.view_model_id,
                    audit_view.view_model_id,
                    handoff_view.view_model_id,
                )
            )
        ),
        "k_evaluation_summary_id": (
            k_evaluation_summary.k_evaluation_summary_id
        ),
    }
    return P3SealProjectionEnvelope(
        projection_envelope_id="fllpe-" + stable_hash(payload)[:16],
        contract_version=P3_SEAL_PROJECTION_ENVELOPE_VERSION,
        seal_view=seal_view,
        coverage_view=coverage_view,
        audit_view=audit_view,
        handoff_view=handoff_view,
        k_evaluation_summary_id=(
            k_evaluation_summary.k_evaluation_summary_id
        ),
        boundary=build_p3_seal_react_projection_boundary(),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )
