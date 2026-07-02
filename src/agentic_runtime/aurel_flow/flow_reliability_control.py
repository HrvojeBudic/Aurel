"""P3-FLOW-G reliability control plane / diagnostic loop layer (P3.15.0-P3.15.9).

The reliability control plane represents Monitor -> Detect -> Diagnose ->
Recovery Candidate -> Verify Expectation as deterministic local state. A
RecoverFrame proposes recovery only; a VerifyExpectationFrame expects
verification only. Nothing in this module executes repair, retry, recovery,
rollback, or verification, and nothing writes Trace or Ledger. Recovery
execution belongs to P4 AurelExec, proof to P5 AurelTrace, and authority to
P9 Custos. There is deliberately no RECOVERED or HEALED control-loop phase:
in P3 the control plane structurally cannot claim a completed heal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_diagnosis import RootCauseDiagnosis, RuntimeFailureSignal
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash
from .workflow_state import WorkflowRun

AUREL_FLOW_G_PACK_ID = "P3-FLOW-G"
AUREL_FLOW_G_PACK_TITLE = (
    "Self-Healing Runtime Control Loop / Reliability Control Plane Pack"
)
AUREL_FLOW_G_REPORT_PATH = (
    "agent/reports/P3_FLOW_G_SELF_HEALING_RELIABILITY_CONTROL_PACK.md"
)

RELIABILITY_CONTROL_PLANE_VERSION = "reliability_control_plane.v1"
RELIABILITY_CONTROL_PLANE_STATE_VERSION = "reliability_control_plane_state.v1"
SELF_HEALING_CONTROL_LAW_BOUNDARY_VERSION = "self_healing_control_law_boundary.v1"
RELIABILITY_CONTROL_READ_MODEL_VERSION = "reliability_control_read_model.v1"
CONTROL_LOOP_TRANSITION_VERSION = "control_loop_transition.v1"
DIAGNOSTIC_LOOP_STATE_VERSION = "diagnostic_loop_state.v1"
DIAGNOSTIC_LOOP_READ_MODEL_VERSION = "diagnostic_loop_read_model.v1"
MONITOR_FRAME_VERSION = "monitor_frame.v1"
DETECTION_FRAME_VERSION = "detection_frame.v1"
DIAGNOSIS_FRAME_VERSION = "diagnosis_frame.v1"
RECOVER_FRAME_VERSION = "recover_frame.v1"
VERIFY_EXPECTATION_FRAME_VERSION = "verify_expectation_frame.v1"

CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON = (
    "the reliability control plane represents self-healing state only; no "
    "repair, retry, recovery, rollback, or verification executes in P3-FLOW-G "
    "— execution belongs to P4 AurelExec and proof to P5 AurelTrace"
)
VERIFICATION_EXPECTATION_UNAVAILABLE_REASON = (
    "a verification expectation expects future verification; no verifier runs "
    "and no proof exists in P3-FLOW-G — verified recovery belongs to P5 "
    "AurelTrace"
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


class ControlLoopPhase(str, Enum):
    """Where the reliability control loop stands.

    Deliberately closed-world: there is no RECOVERED, HEALED, or VERIFIED
    member. In P3 the loop can select, wait, degrade, escalate, or block —
    it structurally cannot claim a completed or verified heal.
    """

    IDLE = "IDLE"
    MONITORING = "MONITORING"
    DETECTED = "DETECTED"
    DIAGNOSING = "DIAGNOSING"
    DIAGNOSED = "DIAGNOSED"
    RECOVERY_CANDIDATE_SELECTED = "RECOVERY_CANDIDATE_SELECTED"
    WAITING_CHECKPOINT = "WAITING_CHECKPOINT"
    WAITING_BUDGET_CHECK = "WAITING_BUDGET_CHECK"
    WAITING_OPERATOR_REVIEW = "WAITING_OPERATOR_REVIEW"
    WAITING_EXECUTION_PLANE = "WAITING_EXECUTION_PLANE"
    WAITING_VERIFICATION = "WAITING_VERIFICATION"
    DEGRADED = "DEGRADED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ControlLoopTransition(_CanonicalMixin):
    """A recorded phase change. Recording a transition executes nothing."""

    transition_id: str
    contract_version: str
    control_plane_id: str
    run_id: str
    from_phase: ControlLoopPhase
    to_phase: ControlLoopPhase
    reason: str
    logical_sequence: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    repair_executed: bool = False
    recovery_executed: bool = False
    stop_executed: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "repair_executed",
            "recovery_executed",
            "stop_executed",
            "execution_available",
        )
        if self.from_phase is self.to_phase:
            raise AurelFlowValidationError(
                f"control loop transition must change phase; got "
                f"{self.from_phase.value} -> {self.to_phase.value}",
                code=AurelFlowErrorCode.INVALID_LIFECYCLE_TRANSITION,
                field="to_phase",
            )


def control_loop_transition(
    *,
    control_plane_id: str,
    run_id: str,
    from_phase: ControlLoopPhase,
    to_phase: ControlLoopPhase,
    reason: str,
    logical_sequence: int,
) -> ControlLoopTransition:
    payload = {
        "contract_version": CONTROL_LOOP_TRANSITION_VERSION,
        "control_plane_id": control_plane_id,
        "run_id": run_id,
        "from_phase": from_phase.value,
        "to_phase": to_phase.value,
        "reason": reason,
        "logical_sequence": logical_sequence,
    }
    return ControlLoopTransition(
        transition_id="flclt-" + stable_hash(payload)[:16],
        contract_version=CONTROL_LOOP_TRANSITION_VERSION,
        control_plane_id=control_plane_id,
        run_id=run_id,
        from_phase=from_phase,
        to_phase=to_phase,
        reason=reason,
        logical_sequence=logical_sequence,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ReliabilityControlPlane(_CanonicalMixin):
    """The reliability control plane identity for one run. Not an executor."""

    control_plane_id: str
    contract_version: str
    run_id: str
    created_by: str
    created_at_logical_sequence: int
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    recovery_executed: bool = False
    verification_available: bool = False
    trace_verified: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "recovery_executed",
            "verification_available",
            "trace_verified",
            "execution_available",
        )


def create_reliability_control_plane(
    run: WorkflowRun, *, created_by: str
) -> ReliabilityControlPlane:
    """Name a control plane over an existing run. Pure derivation; the logical
    sequence anchor is the run's own step counter, never a wall clock."""

    payload = {
        "contract_version": RELIABILITY_CONTROL_PLANE_VERSION,
        "run_id": run.run_id,
        "created_by": created_by,
        "created_at_logical_sequence": run.state.step,
    }
    return ReliabilityControlPlane(
        control_plane_id="flrcp-" + stable_hash(payload)[:16],
        contract_version=RELIABILITY_CONTROL_PLANE_VERSION,
        run_id=run.run_id,
        created_by=created_by,
        created_at_logical_sequence=run.state.step,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class ReliabilityControlPlaneState(_CanonicalMixin):
    """Current control-plane posture. State is bookkeeping, not execution."""

    state_id: str
    contract_version: str
    control_plane_id: str
    run_id: str
    current_phase: ControlLoopPhase
    truth_label: FlowTruthLabel
    current_failure_signal_id: str = ""
    current_diagnosis_id: str = ""
    selected_recovery_candidate_id: str = ""
    requires_checkpoint: bool = True
    requires_budget_check: bool = True
    requires_operator_review: bool = True
    requires_p4_execution: bool = True
    requires_p5_proof: bool = True
    requires_p9_authority_if_irreversible: bool = True
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    recovery_executed: bool = False
    verification_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_checkpoint",
            "requires_budget_check",
            "requires_operator_review",
            "requires_p4_execution",
            "requires_p5_proof",
            "requires_p9_authority_if_irreversible",
        )
        _forbid_true(
            self, "recovery_executed", "verification_available", "trace_verified"
        )


def build_reliability_control_plane_state(
    control_plane: ReliabilityControlPlane,
    *,
    current_phase: ControlLoopPhase,
    current_failure_signal_id: str = "",
    current_diagnosis_id: str = "",
    selected_recovery_candidate_id: str = "",
) -> ReliabilityControlPlaneState:
    payload = {
        "contract_version": RELIABILITY_CONTROL_PLANE_STATE_VERSION,
        "control_plane_id": control_plane.control_plane_id,
        "current_phase": current_phase.value,
        "current_failure_signal_id": current_failure_signal_id,
        "current_diagnosis_id": current_diagnosis_id,
        "selected_recovery_candidate_id": selected_recovery_candidate_id,
    }
    return ReliabilityControlPlaneState(
        state_id="flrps-" + stable_hash(payload)[:16],
        contract_version=RELIABILITY_CONTROL_PLANE_STATE_VERSION,
        control_plane_id=control_plane.control_plane_id,
        run_id=control_plane.run_id,
        current_phase=current_phase,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        current_failure_signal_id=current_failure_signal_id,
        current_diagnosis_id=current_diagnosis_id,
        selected_recovery_candidate_id=selected_recovery_candidate_id,
    )


@dataclass(frozen=True)
class SelfHealingControlLawBoundary(_CanonicalMixin):
    """The control-plane law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    detection_is_not_fix: bool = True
    diagnosis_is_not_proof: bool = True
    recovery_candidate_is_not_execution: bool = True
    budget_check_is_not_permission: bool = True
    verification_expectation_is_not_verification: bool = True
    escalation_is_not_approval: bool = True
    control_plane_executes_recovery: bool = False
    control_plane_writes_trace: bool = False
    control_plane_writes_ledger: bool = False
    control_plane_grants_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "detection_is_not_fix",
            "diagnosis_is_not_proof",
            "recovery_candidate_is_not_execution",
            "budget_check_is_not_permission",
            "verification_expectation_is_not_verification",
            "escalation_is_not_approval",
        )
        _forbid_true(
            self,
            "control_plane_executes_recovery",
            "control_plane_writes_trace",
            "control_plane_writes_ledger",
            "control_plane_grants_authority",
        )


def build_self_healing_control_law_boundary() -> SelfHealingControlLawBoundary:
    payload = {"boundary_version": SELF_HEALING_CONTROL_LAW_BOUNDARY_VERSION}
    return SelfHealingControlLawBoundary(
        boundary_version=SELF_HEALING_CONTROL_LAW_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ReliabilityControlReadModel(_CanonicalMixin):
    """Deterministic control-plane projection. Not execution, not proof."""

    read_model_version: str
    control_plane_id: str
    run_id: str
    current_phase: ControlLoopPhase
    transition_count: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    current_failure_signal_id: str = ""
    current_diagnosis_id: str = ""
    selected_recovery_candidate_id: str = ""
    recovery_executed: bool = False
    verification_available: bool = False
    trace_verified: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "recovery_executed",
            "verification_available",
            "trace_verified",
            "execution_available",
        )


def build_reliability_control_read_model(
    state: ReliabilityControlPlaneState,
    transitions: tuple[ControlLoopTransition, ...] = (),
) -> ReliabilityControlReadModel:
    for transition in transitions:
        if transition.control_plane_id != state.control_plane_id:
            raise AurelFlowValidationError(
                f"transition control plane {transition.control_plane_id!r} "
                f"does not match state control plane "
                f"{state.control_plane_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field="transitions",
            )
    payload = {
        "read_model_version": RELIABILITY_CONTROL_READ_MODEL_VERSION,
        "state_id": state.state_id,
        "transition_ids": tuple(
            transition.transition_id for transition in transitions
        ),
    }
    return ReliabilityControlReadModel(
        read_model_version=RELIABILITY_CONTROL_READ_MODEL_VERSION,
        control_plane_id=state.control_plane_id,
        run_id=state.run_id,
        current_phase=state.current_phase,
        transition_count=len(transitions),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
        current_failure_signal_id=state.current_failure_signal_id,
        current_diagnosis_id=state.current_diagnosis_id,
        selected_recovery_candidate_id=state.selected_recovery_candidate_id,
    )


@dataclass(frozen=True)
class MonitorFrame(_CanonicalMixin):
    """Read-only observation of a run's current posture. Watching is not acting."""

    monitor_frame_id: str
    contract_version: str
    run_id: str
    observed_step: int
    observed_lifecycle_status: str
    observed_node_count: int
    truth_label: FlowTruthLabel
    node_id: str = ""
    source_event_id: str = ""
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    read_only: bool = True
    mutation_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "read_only")
        _forbid_true(self, "mutation_available", "execution_available")


def build_monitor_frame(
    run: WorkflowRun, *, node_id: str = "", source_event_id: str = ""
) -> MonitorFrame:
    payload = {
        "contract_version": MONITOR_FRAME_VERSION,
        "run_id": run.run_id,
        "observed_step": run.state.step,
        "observed_lifecycle_status": run.state.lifecycle_status.value,
        "node_id": node_id,
        "source_event_id": source_event_id,
    }
    return MonitorFrame(
        monitor_frame_id="flmon-" + stable_hash(payload)[:16],
        contract_version=MONITOR_FRAME_VERSION,
        run_id=run.run_id,
        observed_step=run.state.step,
        observed_lifecycle_status=run.state.lifecycle_status.value,
        observed_node_count=len(run.state.node_states),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        node_id=node_id,
        source_event_id=source_event_id,
    )


@dataclass(frozen=True)
class DetectionFrame(_CanonicalMixin):
    """Binds a monitor observation to a detected failure. A detection is not a fix."""

    detection_frame_id: str
    contract_version: str
    run_id: str
    monitor_frame_id: str
    failure_signal_id: str
    detected_failure_kind: str
    truth_label: FlowTruthLabel
    node_id: str = ""
    source_event_id: str = ""
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    detection_is_not_fix: bool = True
    recovery_executed: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "detection_is_not_fix")
        _forbid_true(self, "recovery_executed", "proof_available")


def build_detection_frame(
    monitor_frame: MonitorFrame, failure_signal: RuntimeFailureSignal
) -> DetectionFrame:
    if monitor_frame.run_id != failure_signal.run_id:
        raise AurelFlowValidationError(
            f"monitor frame run {monitor_frame.run_id!r} does not match "
            f"failure signal run {failure_signal.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="failure_signal",
        )
    payload = {
        "contract_version": DETECTION_FRAME_VERSION,
        "monitor_frame_id": monitor_frame.monitor_frame_id,
        "failure_signal_id": failure_signal.failure_signal_id,
    }
    return DetectionFrame(
        detection_frame_id="fldet-" + stable_hash(payload)[:16],
        contract_version=DETECTION_FRAME_VERSION,
        run_id=failure_signal.run_id,
        monitor_frame_id=monitor_frame.monitor_frame_id,
        failure_signal_id=failure_signal.failure_signal_id,
        detected_failure_kind=failure_signal.failure_kind.value,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        node_id=failure_signal.node_id,
        source_event_id=failure_signal.source_event_id,
    )


@dataclass(frozen=True)
class DiagnosisFrame(_CanonicalMixin):
    """Binds a detection to an advisory diagnosis. Diagnosing proves nothing."""

    diagnosis_frame_id: str
    contract_version: str
    run_id: str
    detection_frame_id: str
    failure_signal_id: str
    diagnosis_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    diagnosis_is_not_proof: bool = True
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "diagnosis_is_not_proof")
        _forbid_true(self, "proof_available", "trace_verified")


def build_diagnosis_frame(
    detection_frame: DetectionFrame, diagnosis: RootCauseDiagnosis
) -> DiagnosisFrame:
    if detection_frame.failure_signal_id != diagnosis.failure_signal_id:
        raise AurelFlowValidationError(
            f"detection failure signal {detection_frame.failure_signal_id!r} "
            f"does not match diagnosis failure signal "
            f"{diagnosis.failure_signal_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="diagnosis",
        )
    payload = {
        "contract_version": DIAGNOSIS_FRAME_VERSION,
        "detection_frame_id": detection_frame.detection_frame_id,
        "diagnosis_id": diagnosis.diagnosis_id,
    }
    return DiagnosisFrame(
        diagnosis_frame_id="fldgf-" + stable_hash(payload)[:16],
        contract_version=DIAGNOSIS_FRAME_VERSION,
        run_id=detection_frame.run_id,
        detection_frame_id=detection_frame.detection_frame_id,
        failure_signal_id=detection_frame.failure_signal_id,
        diagnosis_id=diagnosis.diagnosis_id,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class RecoverFrame(_CanonicalMixin):
    """Proposes a recovery candidate. Proposing is not executing."""

    recover_frame_id: str
    contract_version: str
    run_id: str
    diagnosis_frame_id: str
    diagnosis_id: str
    recovery_candidate_id: str
    truth_label: FlowTruthLabel
    source_checkpoint_id: str = ""
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    proposes_only: bool = True
    requires_pre_recovery_checkpoint: bool = True
    recovery_executed: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "proposes_only", "requires_pre_recovery_checkpoint")
        _forbid_true(self, "recovery_executed", "execution_available")


def build_recover_frame(
    diagnosis_frame: DiagnosisFrame,
    *,
    recovery_candidate_id: str,
    source_checkpoint_id: str = "",
) -> RecoverFrame:
    payload = {
        "contract_version": RECOVER_FRAME_VERSION,
        "diagnosis_frame_id": diagnosis_frame.diagnosis_frame_id,
        "recovery_candidate_id": recovery_candidate_id,
        "source_checkpoint_id": source_checkpoint_id,
    }
    return RecoverFrame(
        recover_frame_id="flrcf-" + stable_hash(payload)[:16],
        contract_version=RECOVER_FRAME_VERSION,
        run_id=diagnosis_frame.run_id,
        diagnosis_frame_id=diagnosis_frame.diagnosis_frame_id,
        diagnosis_id=diagnosis_frame.diagnosis_id,
        recovery_candidate_id=recovery_candidate_id,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        source_checkpoint_id=source_checkpoint_id,
    )


@dataclass(frozen=True)
class VerifyExpectationFrame(_CanonicalMixin):
    """Expects future verification. An expectation is not verification."""

    verify_expectation_frame_id: str
    contract_version: str
    run_id: str
    recover_frame_id: str
    recovery_candidate_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = VERIFICATION_EXPECTATION_UNAVAILABLE_REASON
    verification_required: bool = True
    requires_post_recovery_comparison: bool = True
    requires_p5_proof: bool = True
    verification_available: bool = False
    verification_executed: bool = False
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "verification_required",
            "requires_post_recovery_comparison",
            "requires_p5_proof",
        )
        _forbid_true(
            self,
            "verification_available",
            "verification_executed",
            "proof_available",
            "trace_verified",
        )


def build_verify_expectation_frame(
    recover_frame: RecoverFrame,
) -> VerifyExpectationFrame:
    payload = {
        "contract_version": VERIFY_EXPECTATION_FRAME_VERSION,
        "recover_frame_id": recover_frame.recover_frame_id,
        "recovery_candidate_id": recover_frame.recovery_candidate_id,
    }
    return VerifyExpectationFrame(
        verify_expectation_frame_id="flvef-" + stable_hash(payload)[:16],
        contract_version=VERIFY_EXPECTATION_FRAME_VERSION,
        run_id=recover_frame.run_id,
        recover_frame_id=recover_frame.recover_frame_id,
        recovery_candidate_id=recover_frame.recovery_candidate_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class DiagnosticLoopState(_CanonicalMixin):
    """One pass of Monitor -> Detect -> Diagnose -> Recover -> Verify Expectation.

    The loop state links frames by id; it executes none of them.
    """

    loop_state_id: str
    contract_version: str
    run_id: str
    monitor_frame_id: str
    truth_label: FlowTruthLabel
    detection_frame_id: str = ""
    diagnosis_frame_id: str = ""
    recover_frame_id: str = ""
    verify_expectation_frame_id: str = ""
    failure_signal_id: str = ""
    diagnosis_id: str = ""
    recovery_candidate_id: str = ""
    unavailable_reason: str = CONTROL_PLANE_EXECUTION_UNAVAILABLE_REASON
    verification_required: bool = True
    verification_available: bool = False
    proof_available: bool = False
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "verification_required")
        _forbid_true(
            self, "verification_available", "proof_available", "recovery_executed"
        )


def build_diagnostic_loop_state(
    monitor_frame: MonitorFrame,
    *,
    detection_frame: DetectionFrame | None = None,
    diagnosis_frame: DiagnosisFrame | None = None,
    recover_frame: RecoverFrame | None = None,
    verify_expectation_frame: VerifyExpectationFrame | None = None,
) -> DiagnosticLoopState:
    for frame_name, frame_run_id in (
        ("detection_frame", detection_frame.run_id if detection_frame else None),
        ("diagnosis_frame", diagnosis_frame.run_id if diagnosis_frame else None),
        ("recover_frame", recover_frame.run_id if recover_frame else None),
        (
            "verify_expectation_frame",
            verify_expectation_frame.run_id if verify_expectation_frame else None,
        ),
    ):
        if frame_run_id is not None and frame_run_id != monitor_frame.run_id:
            raise AurelFlowValidationError(
                f"{frame_name} run {frame_run_id!r} does not match monitor "
                f"frame run {monitor_frame.run_id!r}",
                code=AurelFlowErrorCode.RUN_MISMATCH,
                field=frame_name,
            )
    payload = {
        "contract_version": DIAGNOSTIC_LOOP_STATE_VERSION,
        "monitor_frame_id": monitor_frame.monitor_frame_id,
        "detection_frame_id": (
            detection_frame.detection_frame_id if detection_frame else ""
        ),
        "diagnosis_frame_id": (
            diagnosis_frame.diagnosis_frame_id if diagnosis_frame else ""
        ),
        "recover_frame_id": recover_frame.recover_frame_id if recover_frame else "",
        "verify_expectation_frame_id": (
            verify_expectation_frame.verify_expectation_frame_id
            if verify_expectation_frame
            else ""
        ),
    }
    return DiagnosticLoopState(
        loop_state_id="fldls-" + stable_hash(payload)[:16],
        contract_version=DIAGNOSTIC_LOOP_STATE_VERSION,
        run_id=monitor_frame.run_id,
        monitor_frame_id=monitor_frame.monitor_frame_id,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        detection_frame_id=(
            detection_frame.detection_frame_id if detection_frame else ""
        ),
        diagnosis_frame_id=(
            diagnosis_frame.diagnosis_frame_id if diagnosis_frame else ""
        ),
        recover_frame_id=recover_frame.recover_frame_id if recover_frame else "",
        verify_expectation_frame_id=(
            verify_expectation_frame.verify_expectation_frame_id
            if verify_expectation_frame
            else ""
        ),
        failure_signal_id=(
            detection_frame.failure_signal_id if detection_frame else ""
        ),
        diagnosis_id=diagnosis_frame.diagnosis_id if diagnosis_frame else "",
        recovery_candidate_id=(
            recover_frame.recovery_candidate_id if recover_frame else ""
        ),
    )


@dataclass(frozen=True)
class DiagnosticLoopReadModel(_CanonicalMixin):
    """Deterministic diagnostic-loop projection."""

    read_model_version: str
    loop_state_id: str
    run_id: str
    has_detection: bool
    has_diagnosis: bool
    has_recovery_candidate: bool
    has_verify_expectation: bool
    truth_label: FlowTruthLabel
    read_model_hash: str
    verification_required: bool = True
    verification_available: bool = False
    recovery_executed: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "verification_required")
        _forbid_true(
            self, "verification_available", "recovery_executed", "proof_available"
        )


def build_diagnostic_loop_read_model(
    loop_state: DiagnosticLoopState,
) -> DiagnosticLoopReadModel:
    payload = {
        "read_model_version": DIAGNOSTIC_LOOP_READ_MODEL_VERSION,
        "loop_state_id": loop_state.loop_state_id,
    }
    return DiagnosticLoopReadModel(
        read_model_version=DIAGNOSTIC_LOOP_READ_MODEL_VERSION,
        loop_state_id=loop_state.loop_state_id,
        run_id=loop_state.run_id,
        has_detection=bool(loop_state.detection_frame_id),
        has_diagnosis=bool(loop_state.diagnosis_frame_id),
        has_recovery_candidate=bool(loop_state.recovery_candidate_id),
        has_verify_expectation=bool(loop_state.verify_expectation_frame_id),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
