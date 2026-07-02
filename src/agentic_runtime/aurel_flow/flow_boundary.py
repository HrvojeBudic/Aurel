"""P3-FLOW-D proposal / permission / execution / proof boundary.

AurelFlow gains legal grammar for future action, not the action itself.
Proposal is not permission. Permission request is not permission. Permission
is not execution. Execution is not proof. Proof expectation is not proof.
AurelFlow is the control plane; AurelExec (P4) is the future data/execution
plane; AurelTrace (P5) is the proof plane; Custos (P9) is the authority
plane. Nothing in this module calls runtime.submit, dispatches, approves,
executes repair, or enforces budgets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_proof_expectation import ProofExpectationEnvelope
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

AUREL_FLOW_D_PACK_ID = "P3-FLOW-D"
AUREL_FLOW_D_PACK_TITLE = "Authority / Control Boundary Pack"
AUREL_FLOW_D_REPORT_PATH = (
    "agent/reports/P3_FLOW_D_AUTHORITY_CONTROL_BOUNDARY_PACK.md"
)

FLOW_TO_SUBMIT_BOUNDARY_VERSION = "flow_to_submit_boundary.v1"
CONTROL_PLANE_DATA_PLANE_BOUNDARY_VERSION = "control_plane_data_plane_boundary.v1"
EXECUTION_PROPOSAL_ENVELOPE_VERSION = "execution_proposal_envelope.v1"
PERMISSION_REQUEST_ENVELOPE_VERSION = "permission_request_envelope.v1"
EXECUTION_REQUEST_ENVELOPE_VERSION = "execution_request_envelope.v1"
SUBMIT_COMPATIBILITY_READ_MODEL_VERSION = "submit_compatibility_read_model.v1"
BOUNDARY_TRUTH_READ_MODEL_VERSION = "boundary_truth_read_model.v1"
RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION = "reliability_control_plane_boundary.v1"
RECOVERY_POLICY_BOUNDARY_VERSION = "recovery_policy_boundary.v1"
RECOVERY_EXECUTION_BOUNDARY_VERSION = "recovery_execution_boundary.v1"
RECOVERY_BUDGET_BOUNDARY_VERSION = "recovery_budget_boundary.v1"

PERMISSION_UNAVAILABLE_REASON = (
    "no permission or authority can be granted by AurelFlow; a permission "
    "request envelope describes what P9 Custos must authorize later — "
    "permission request is not permission"
)
SUBMIT_BRIDGE_UNAVAILABLE_REASON = (
    "runtime.submit is not wired and is never called by AurelFlow; the "
    "Flow-to-submit bridge is a described future P4 handoff boundary only"
)
DISPATCH_UNAVAILABLE_REASON = (
    "no execution dispatch exists in AurelFlow; an execution request envelope "
    "describes what P4 AurelExec must dispatch later — request is not dispatch"
)
RECOVERY_EXECUTION_UNAVAILABLE_REASON = (
    "recovery/repair execution is not implemented; the recovery policy "
    "boundary can propose and expect repair only — repair execution belongs "
    "to P4 AurelExec under future self-healing packs"
)
BUDGET_ENFORCEMENT_UNAVAILABLE_REASON = (
    "no budget ledger or enforcement runtime exists; recovery budget "
    "requirements describe future bounds only — requirement is not enforcement"
)

BOUNDARY_LAWS: tuple[str, ...] = (
    "proposal is not permission",
    "permission request is not permission",
    "permission is not execution",
    "execution is not proof",
    "proof expectation is not proof",
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


class FlowRequestedActionKind(str, Enum):
    """Descriptive action vocabulary for envelopes. Naming is not dispatching."""

    TOOL_CALL = "TOOL_CALL"
    COMMAND = "COMMAND"
    LLM_CALL = "LLM_CALL"
    RECOVERY_STEP = "RECOVERY_STEP"
    ROLLBACK = "ROLLBACK"
    CUSTOM = "CUSTOM"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class FlowToSubmitBoundary(_CanonicalMixin):
    """Described future boundary to runtime.submit. Never crossed here."""

    boundary_version: str
    submit_target: str
    description: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = SUBMIT_BRIDGE_UNAVAILABLE_REASON
    future_p4_required: bool = True
    runtime_submit_wired: bool = False
    submit_called: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "runtime_submit_wired", "submit_called", "execution_available"
        )
        _forbid_false(self, "future_p4_required")


def build_flow_to_submit_boundary() -> FlowToSubmitBoundary:
    description = (
        "AurelFlow envelopes are shaped for a future AgenticRuntime.submit "
        "handoff; the bridge itself belongs to P4 and is not wired"
    )
    payload = {
        "boundary_version": FLOW_TO_SUBMIT_BOUNDARY_VERSION,
        "submit_target": "AgenticRuntime.submit",
    }
    return FlowToSubmitBoundary(
        boundary_version=FLOW_TO_SUBMIT_BOUNDARY_VERSION,
        submit_target="AgenticRuntime.submit",
        description=description,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ControlPlaneDataPlaneBoundary(_CanonicalMixin):
    """AurelFlow is control plane; execution/proof/authority planes are future."""

    boundary_version: str
    control_plane: str
    data_plane: str
    proof_plane: str
    authority_plane: str
    projection_plane: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    control_plane_executes: bool = False
    data_plane_active: bool = False
    proof_plane_active: bool = False
    authority_plane_active: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "control_plane_executes",
            "data_plane_active",
            "proof_plane_active",
            "authority_plane_active",
        )


def build_control_plane_data_plane_boundary() -> ControlPlaneDataPlaneBoundary:
    payload = {"boundary_version": CONTROL_PLANE_DATA_PLANE_BOUNDARY_VERSION}
    return ControlPlaneDataPlaneBoundary(
        boundary_version=CONTROL_PLANE_DATA_PLANE_BOUNDARY_VERSION,
        control_plane="AurelFlow (P3, local orchestration law)",
        data_plane="AurelExec (P4, future execution plane)",
        proof_plane="AurelTrace (P5, future proof plane)",
        authority_plane="Custos (P9, future authority plane)",
        projection_plane="AurelShell (P2, operator projection surface)",
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ExecutionProposalEnvelope(_CanonicalMixin):
    """AurelFlow proposal for future execution. Proposal is not permission."""

    proposal_id: str
    contract_version: str
    run_id: str
    node_id: str
    source_scheduler_decision_id: str
    source_runtime_event_id: str
    requested_action_kind: FlowRequestedActionKind
    requested_tool_or_executor_ref: str
    proposal_reason: str
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    execution_available: bool = False
    permission_granted: bool = False
    authority_granted: bool = False
    proposal_is_permission: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "execution_available",
            "permission_granted",
            "authority_granted",
            "proposal_is_permission",
        )


def create_execution_proposal_envelope(
    *,
    run_id: str,
    node_id: str,
    source_scheduler_decision_id: str,
    source_runtime_event_id: str,
    requested_action_kind: FlowRequestedActionKind,
    requested_tool_or_executor_ref: str,
    proposal_reason: str,
    metadata: Mapping[str, str] | None = None,
) -> ExecutionProposalEnvelope:
    proposal_id = "flprop-" + stable_hash(
        {
            "contract_version": EXECUTION_PROPOSAL_ENVELOPE_VERSION,
            "run_id": run_id,
            "node_id": node_id,
            "source_scheduler_decision_id": source_scheduler_decision_id,
            "source_runtime_event_id": source_runtime_event_id,
            "requested_action_kind": requested_action_kind.value,
            "requested_tool_or_executor_ref": requested_tool_or_executor_ref,
        }
    )[:16]
    return ExecutionProposalEnvelope(
        proposal_id=proposal_id,
        contract_version=EXECUTION_PROPOSAL_ENVELOPE_VERSION,
        run_id=run_id,
        node_id=node_id,
        source_scheduler_decision_id=source_scheduler_decision_id,
        source_runtime_event_id=source_runtime_event_id,
        requested_action_kind=requested_action_kind,
        requested_tool_or_executor_ref=requested_tool_or_executor_ref,
        proposal_reason=proposal_reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class PermissionRequestEnvelope(_CanonicalMixin):
    """Describes required permission. Requesting is not granting."""

    permission_request_id: str
    contract_version: str
    proposal_id: str
    run_id: str
    node_id: str
    required_permission_scope: str
    required_authority_scope: str
    required_policy_family: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = PERMISSION_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    future_p9_required: bool = True
    permission_granted: bool = False
    authority_granted: bool = False
    permission_request_is_permission: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "permission_granted",
            "authority_granted",
            "permission_request_is_permission",
        )
        _forbid_false(self, "future_p9_required")


def create_permission_request_envelope(
    *,
    proposal: ExecutionProposalEnvelope,
    required_permission_scope: str,
    required_authority_scope: str,
    required_policy_family: str,
    metadata: Mapping[str, str] | None = None,
) -> PermissionRequestEnvelope:
    permission_request_id = "flperm-" + stable_hash(
        {
            "contract_version": PERMISSION_REQUEST_ENVELOPE_VERSION,
            "proposal_id": proposal.proposal_id,
            "required_permission_scope": required_permission_scope,
            "required_authority_scope": required_authority_scope,
            "required_policy_family": required_policy_family,
        }
    )[:16]
    return PermissionRequestEnvelope(
        permission_request_id=permission_request_id,
        contract_version=PERMISSION_REQUEST_ENVELOPE_VERSION,
        proposal_id=proposal.proposal_id,
        run_id=proposal.run_id,
        node_id=proposal.node_id,
        required_permission_scope=required_permission_scope,
        required_authority_scope=required_authority_scope,
        required_policy_family=required_policy_family,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class ExecutionRequestEnvelope(_CanonicalMixin):
    """Describes a future execution request. Request is not dispatch."""

    execution_request_id: str
    contract_version: str
    proposal_id: str
    permission_request_id: str
    requested_executor_ref: str
    requested_tool_or_executor_ref: str
    required_sandbox_profile: str
    required_budget_profile: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = DISPATCH_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    future_p4_required: bool = True
    execution_available: bool = False
    execution_dispatched: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "execution_available", "execution_dispatched", "permission_granted"
        )
        _forbid_false(self, "future_p4_required")


def create_execution_request_envelope(
    *,
    proposal: ExecutionProposalEnvelope,
    permission_request: PermissionRequestEnvelope,
    requested_executor_ref: str,
    required_sandbox_profile: str,
    required_budget_profile: str,
    metadata: Mapping[str, str] | None = None,
) -> ExecutionRequestEnvelope:
    if permission_request.proposal_id != proposal.proposal_id:
        raise AurelFlowValidationError(
            "permission request "
            f"{permission_request.permission_request_id!r} does not belong to "
            f"proposal {proposal.proposal_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="permission_request",
        )
    execution_request_id = "flexec-" + stable_hash(
        {
            "contract_version": EXECUTION_REQUEST_ENVELOPE_VERSION,
            "proposal_id": proposal.proposal_id,
            "permission_request_id": permission_request.permission_request_id,
            "requested_executor_ref": requested_executor_ref,
        }
    )[:16]
    return ExecutionRequestEnvelope(
        execution_request_id=execution_request_id,
        contract_version=EXECUTION_REQUEST_ENVELOPE_VERSION,
        proposal_id=proposal.proposal_id,
        permission_request_id=permission_request.permission_request_id,
        requested_executor_ref=requested_executor_ref,
        requested_tool_or_executor_ref=proposal.requested_tool_or_executor_ref,
        required_sandbox_profile=required_sandbox_profile,
        required_budget_profile=required_budget_profile,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class SubmitCompatibilityReadModel(_CanonicalMixin):
    """Future submit compatibility view. Compatibility is not a bridge."""

    read_model_version: str
    boundary: FlowToSubmitBoundary
    compatible_envelope_contract_versions: tuple[str, ...]
    truth_label: FlowTruthLabel
    read_model_hash: str
    unavailable_reason: str = SUBMIT_BRIDGE_UNAVAILABLE_REASON
    future_p4_required: bool = True
    runtime_submit_wired: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "runtime_submit_wired", "execution_available")
        _forbid_false(self, "future_p4_required")


def build_submit_compatibility_read_model() -> SubmitCompatibilityReadModel:
    compatible_versions = (
        EXECUTION_PROPOSAL_ENVELOPE_VERSION,
        PERMISSION_REQUEST_ENVELOPE_VERSION,
        EXECUTION_REQUEST_ENVELOPE_VERSION,
    )
    payload = {
        "read_model_version": SUBMIT_COMPATIBILITY_READ_MODEL_VERSION,
        "compatible_envelope_contract_versions": compatible_versions,
    }
    return SubmitCompatibilityReadModel(
        read_model_version=SUBMIT_COMPATIBILITY_READ_MODEL_VERSION,
        boundary=build_flow_to_submit_boundary(),
        compatible_envelope_contract_versions=compatible_versions,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class BoundaryTruthReadModel(_CanonicalMixin):
    """Aggregated no-permission / no-execution / no-proof truth."""

    read_model_version: str
    proposal_count: int
    permission_request_count: int
    execution_request_count: int
    proof_expectation_count: int
    laws: tuple[str, ...]
    truth_label: FlowTruthLabel
    read_model_hash: str
    proposal_is_not_permission: bool = True
    permission_request_is_not_permission: bool = True
    permission_is_not_execution: bool = True
    execution_is_not_proof: bool = True
    proof_expectation_is_not_proof: bool = True
    permission_granted_any: bool = False
    authority_granted_any: bool = False
    execution_dispatched_any: bool = False
    proof_available_any: bool = False
    trace_verified_any: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "permission_granted_any",
            "authority_granted_any",
            "execution_dispatched_any",
            "proof_available_any",
            "trace_verified_any",
        )
        _forbid_false(
            self,
            "proposal_is_not_permission",
            "permission_request_is_not_permission",
            "permission_is_not_execution",
            "execution_is_not_proof",
            "proof_expectation_is_not_proof",
        )


def build_boundary_truth_read_model(
    *,
    proposals: tuple[ExecutionProposalEnvelope, ...],
    permission_requests: tuple[PermissionRequestEnvelope, ...],
    execution_requests: tuple[ExecutionRequestEnvelope, ...],
    proof_expectations: tuple[ProofExpectationEnvelope, ...],
) -> BoundaryTruthReadModel:
    payload = {
        "read_model_version": BOUNDARY_TRUTH_READ_MODEL_VERSION,
        "proposal_ids": tuple(proposal.proposal_id for proposal in proposals),
        "permission_request_ids": tuple(
            request.permission_request_id for request in permission_requests
        ),
        "execution_request_ids": tuple(
            request.execution_request_id for request in execution_requests
        ),
        "proof_expectation_ids": tuple(
            expectation.proof_expectation_id for expectation in proof_expectations
        ),
    }
    return BoundaryTruthReadModel(
        read_model_version=BOUNDARY_TRUTH_READ_MODEL_VERSION,
        proposal_count=len(proposals),
        permission_request_count=len(permission_requests),
        execution_request_count=len(execution_requests),
        proof_expectation_count=len(proof_expectations),
        laws=BOUNDARY_LAWS,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


class ControlPlaneSignalKind(str, Enum):
    """What the control plane may signal. Signaling is not executing."""

    MONITOR = "MONITOR"
    DETECT = "DETECT"
    DIAGNOSE_REQUIRED = "DIAGNOSE_REQUIRED"
    RECOVERY_PROPOSED = "RECOVERY_PROPOSED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    LIMIT = "LIMIT"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ControlPlaneSignal(_CanonicalMixin):
    """A control-plane observation/expectation signal. Not an action."""

    signal_id: str
    contract_version: str
    signal_kind: ControlPlaneSignalKind
    target_run_id: str
    target_node_id: str
    reason: str
    truth_label: FlowTruthLabel
    executes_repair: bool = False
    proves_success: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "executes_repair", "proves_success", "execution_available")


def create_control_plane_signal(
    *,
    signal_kind: ControlPlaneSignalKind,
    target_run_id: str,
    target_node_id: str,
    reason: str,
) -> ControlPlaneSignal:
    signal_id = "flcps-" + stable_hash(
        {
            "contract_version": RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
            "signal_kind": signal_kind.value,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "reason": reason,
        }
    )[:16]
    return ControlPlaneSignal(
        signal_id=signal_id,
        contract_version=RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
        signal_kind=signal_kind,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class DataPlaneBoundaryRef(_CanonicalMixin):
    """Reference to the future data/execution plane. A ref is not a plane."""

    plane_name: str = "AurelExec"
    owning_phase: str = "P4"
    description: str = (
        "future execution/data plane; AurelFlow refers to it and hands off to "
        "it later, never reaches into it"
    )
    data_plane_active: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "data_plane_active")


@dataclass(frozen=True)
class DiagnosticExpectation(_CanonicalMixin):
    """Control plane can require diagnosis; it cannot perform it here."""

    expectation_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    diagnosis_scope: str
    truth_label: FlowTruthLabel
    future_pack: str = "P3-FLOW self-healing pack (P3.15)"
    diagnosis_required: bool = True
    diagnosis_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "diagnosis_performed")
        _forbid_false(self, "diagnosis_required")


def create_diagnostic_expectation(
    *, target_run_id: str, target_node_id: str, diagnosis_scope: str
) -> DiagnosticExpectation:
    expectation_id = "fldiag-" + stable_hash(
        {
            "contract_version": RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "diagnosis_scope": diagnosis_scope,
        }
    )[:16]
    return DiagnosticExpectation(
        expectation_id=expectation_id,
        contract_version=RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        diagnosis_scope=diagnosis_scope,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class VerifierNodeExpectation(_CanonicalMixin):
    """A node whose output must be verified later. Expectation is not verification."""

    expectation_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    verifier_kind: str
    truth_label: FlowTruthLabel
    future_p5_required: bool = True
    verification_required: bool = True
    verification_performed: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "verification_performed", "proof_available")
        _forbid_false(self, "verification_required", "future_p5_required")


def create_verifier_node_expectation(
    *, target_run_id: str, target_node_id: str, verifier_kind: str
) -> VerifierNodeExpectation:
    expectation_id = "flvne-" + stable_hash(
        {
            "contract_version": RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "verifier_kind": verifier_kind,
        }
    )[:16]
    return VerifierNodeExpectation(
        expectation_id=expectation_id,
        contract_version=RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        verifier_kind=verifier_kind,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ValidationNodeExpectation(_CanonicalMixin):
    """A node whose output must be validated later. Expectation is not validation."""

    expectation_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    validation_kind: str
    truth_label: FlowTruthLabel
    validation_required: bool = True
    validation_performed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "validation_performed")
        _forbid_false(self, "validation_required")


def create_validation_node_expectation(
    *, target_run_id: str, target_node_id: str, validation_kind: str
) -> ValidationNodeExpectation:
    expectation_id = "flval-" + stable_hash(
        {
            "contract_version": RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "validation_kind": validation_kind,
        }
    )[:16]
    return ValidationNodeExpectation(
        expectation_id=expectation_id,
        contract_version=RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        validation_kind=validation_kind,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RecoveryExecutionBoundary(_CanonicalMixin):
    """Repair proposals stop here: execution is on the other side."""

    boundary_version: str
    owning_phase: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = RECOVERY_EXECUTION_UNAVAILABLE_REASON
    recovery_proposal_allowed: bool = True
    recovery_execution_available: bool = False
    repair_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "recovery_execution_available", "repair_executed")
        _forbid_false(self, "recovery_proposal_allowed")


@dataclass(frozen=True)
class RecoveryPolicyBoundary(_CanonicalMixin):
    """Recovery policy can propose/require; it cannot execute or prove."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = RECOVERY_EXECUTION_UNAVAILABLE_REASON
    can_require_diagnosis: bool = True
    can_require_verification: bool = True
    can_propose_repair: bool = True
    executes_repair: bool = False
    proves_success: bool = False
    enforcement_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "executes_repair", "proves_success", "enforcement_available")
        _forbid_false(
            self, "can_require_diagnosis", "can_require_verification", "can_propose_repair"
        )


def build_recovery_policy_boundary() -> RecoveryPolicyBoundary:
    payload = {"boundary_version": RECOVERY_POLICY_BOUNDARY_VERSION}
    return RecoveryPolicyBoundary(
        boundary_version=RECOVERY_POLICY_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ReliabilityControlPlaneBoundary(_CanonicalMixin):
    """Reliability as a bounded control problem. The loop itself is future."""

    boundary_version: str
    plane_boundary: ControlPlaneDataPlaneBoundary
    recovery_policy: RecoveryPolicyBoundary
    recovery_execution: RecoveryExecutionBoundary
    data_plane_ref: DataPlaneBoundaryRef
    allowed_signal_kinds: tuple[ControlPlaneSignalKind, ...]
    future_loop: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    control_plane_executes: bool = False
    self_healing_loop_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "control_plane_executes", "self_healing_loop_implemented")


def build_reliability_control_plane_boundary() -> ReliabilityControlPlaneBoundary:
    payload = {"boundary_version": RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION}
    return ReliabilityControlPlaneBoundary(
        boundary_version=RELIABILITY_CONTROL_PLANE_BOUNDARY_VERSION,
        plane_boundary=build_control_plane_data_plane_boundary(),
        recovery_policy=build_recovery_policy_boundary(),
        recovery_execution=RecoveryExecutionBoundary(
            boundary_version=RECOVERY_EXECUTION_BOUNDARY_VERSION,
            owning_phase="P4",
            truth_label=FlowTruthLabel.CONTRACT_ONLY,
        ),
        data_plane_ref=DataPlaneBoundaryRef(),
        allowed_signal_kinds=tuple(ControlPlaneSignalKind),
        future_loop=(
            "Monitor -> Detect -> Diagnose -> Recover -> Verify belongs to a "
            "future self-healing pack; this pack seeds the boundary only"
        ),
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


class BudgetUnavailableReason(str, Enum):
    """Why no budget can be consulted or enforced today."""

    NO_BUDGET_LEDGER = "NO_BUDGET_LEDGER"
    NO_ENFORCEMENT_RUNTIME = "NO_ENFORCEMENT_RUNTIME"
    FUTURE_PACK_REQUIRED = "FUTURE_PACK_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class RecoveryBudgetDimension(str, Enum):
    """Dimensions a future recovery budget must bound."""

    ATTEMPTS = "ATTEMPTS"
    LATENCY_MS = "LATENCY_MS"
    COST_UNITS = "COST_UNITS"
    DEPTH = "DEPTH"


@dataclass(frozen=True)
class RecoveryBudgetRequirement(_CanonicalMixin):
    """A future bound on recovery. Requirement is not enforcement."""

    requirement_id: str
    contract_version: str
    dimension: RecoveryBudgetDimension
    limit_value: int
    applies_to: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = BUDGET_ENFORCEMENT_UNAVAILABLE_REASON
    budget_enforced: bool = False
    budget_is_permission: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "budget_enforced", "budget_is_permission")


def create_recovery_budget_requirement(
    *, dimension: RecoveryBudgetDimension, limit_value: int, applies_to: str
) -> RecoveryBudgetRequirement:
    requirement_id = "flbud-" + stable_hash(
        {
            "contract_version": RECOVERY_BUDGET_BOUNDARY_VERSION,
            "dimension": dimension.value,
            "limit_value": limit_value,
            "applies_to": applies_to,
        }
    )[:16]
    return RecoveryBudgetRequirement(
        requirement_id=requirement_id,
        contract_version=RECOVERY_BUDGET_BOUNDARY_VERSION,
        dimension=dimension,
        limit_value=limit_value,
        applies_to=applies_to,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class BudgetRequiredForAutoContinue(_CanonicalMixin):
    """Future auto-continue must be budgeted; unbudgeted auto-continue is illegal."""

    requirements: tuple[RecoveryBudgetRequirement, ...]
    truth_label: FlowTruthLabel
    auto_continue_without_budget_allowed: bool = False
    budget_enforced: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "auto_continue_without_budget_allowed", "budget_enforced")


@dataclass(frozen=True)
class BudgetRequiredForRepair(_CanonicalMixin):
    """Future repair must be budgeted; unbudgeted repair is illegal."""

    requirements: tuple[RecoveryBudgetRequirement, ...]
    truth_label: FlowTruthLabel
    repair_without_budget_allowed: bool = False
    budget_enforced: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "repair_without_budget_allowed", "budget_enforced")


@dataclass(frozen=True)
class RecoveryBudgetBoundary(_CanonicalMixin):
    """Recovery budget truth: bounds are described, never enforced here."""

    boundary_version: str
    auto_continue_gate: BudgetRequiredForAutoContinue
    repair_gate: BudgetRequiredForRepair
    unavailable_reason_kind: BudgetUnavailableReason
    unavailable_reason: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    budget_enforced: bool = False
    budget_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "budget_enforced", "budget_available")


def build_recovery_budget_boundary(
    *,
    auto_continue_requirements: tuple[RecoveryBudgetRequirement, ...],
    repair_requirements: tuple[RecoveryBudgetRequirement, ...],
) -> RecoveryBudgetBoundary:
    payload = {
        "boundary_version": RECOVERY_BUDGET_BOUNDARY_VERSION,
        "auto_continue_requirement_ids": tuple(
            requirement.requirement_id for requirement in auto_continue_requirements
        ),
        "repair_requirement_ids": tuple(
            requirement.requirement_id for requirement in repair_requirements
        ),
    }
    return RecoveryBudgetBoundary(
        boundary_version=RECOVERY_BUDGET_BOUNDARY_VERSION,
        auto_continue_gate=BudgetRequiredForAutoContinue(
            requirements=auto_continue_requirements,
            truth_label=FlowTruthLabel.CONTRACT_ONLY,
        ),
        repair_gate=BudgetRequiredForRepair(
            requirements=repair_requirements,
            truth_label=FlowTruthLabel.CONTRACT_ONLY,
        ),
        unavailable_reason_kind=BudgetUnavailableReason.NO_ENFORCEMENT_RUNTIME,
        unavailable_reason=BUDGET_ENFORCEMENT_UNAVAILABLE_REASON,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )
