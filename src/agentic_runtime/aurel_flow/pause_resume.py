"""P3-FLOW-B workflow pause / operator decision signals (P3.4.x).

AurelFlow may pause and may accept internal operator decision state. An
OperatorDecisionSignal records operator intent (resume/stop/reject/hold) —
it is not an authority grant and not execution permission. Resume, stop and
reject affect internal AurelFlow lifecycle/node state only, via the P3-FLOW-A
safe transition maps; no node is ever executed. A ResponsibilityTransferFrame
records who should continue or respond without transferring authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import (
    AUTHORITY_UNAVAILABLE_REASON,
    EXECUTION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)
from .workflow_state import (
    WorkflowLifecycleStatus,
    WorkflowNodeState,
    WorkflowRun,
    lifecycle_transition,
    node_transition,
    transition_workflow_run,
)

WORKFLOW_PAUSE_STATE_VERSION = "workflow_pause_state.v1"
OPERATOR_DECISION_SIGNAL_VERSION = "operator_decision_signal.v1"
RESPONSIBILITY_TRANSFER_FRAME_VERSION = "responsibility_transfer_frame.v1"
WORKFLOW_PAUSE_READ_MODEL_VERSION = "workflow_pause_read_model.v1"


class WorkflowPauseReason(str, Enum):
    WAITING_OPERATOR = "WAITING_OPERATOR"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    WAITING_VERIFIER = "WAITING_VERIFIER"
    WAITING_REASONING = "WAITING_REASONING"
    WAITING_POLICY = "WAITING_POLICY"
    WAITING_COUNTERARGUMENT = "WAITING_COUNTERARGUMENT"
    WAITING_MEDIATION = "WAITING_MEDIATION"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class OperatorDecisionKind(str, Enum):
    RESUME = "RESUME"
    STOP = "STOP"
    REJECT = "REJECT"
    HOLD = "HOLD"
    REQUEST_VERIFICATION = "REQUEST_VERIFICATION"
    REQUEST_MEDIATION = "REQUEST_MEDIATION"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class WorkflowPauseState(_CanonicalMixin):
    """Paused/waiting runtime state with an explicit reason. Not execution."""

    pause_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    pause_reason: WorkflowPauseReason
    source_event_id: str
    waiting_for: str
    resumable: bool
    requires_operator_decision: bool
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    requires_authority: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("requires_authority", "execution_available"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"WorkflowPauseState.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class OperatorDecisionSignal(_CanonicalMixin):
    """Internal operator state signal. Not authority, not execution permission.

    Decision quality flags (counterargument / minority objection / mediation /
    decision pressure) are preserved for future deliberation layers.
    """

    decision_id: str
    contract_version: str
    operator_id: str
    decision_kind: OperatorDecisionKind
    target_run_id: str
    target_node_id: str
    reason: str
    counterargument_present: bool
    minority_objection_present: bool
    mediation_required: bool
    decision_pressure_warning: bool
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    authority_granted: bool = False
    execution_permission_granted: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("authority_granted", "execution_permission_granted"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"OperatorDecisionSignal.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class ResponsibilityTransferFrame(_CanonicalMixin):
    """Responsibility handoff record. Responsibility is not authority."""

    responsibility_frame_id: str
    contract_version: str
    from_actor: str
    to_actor: str
    target_run_id: str
    target_node_id: str
    reason: str
    scope: str
    handoff_state: str
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    authority_transferred: bool = False
    execution_permission_granted: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("authority_transferred", "execution_permission_granted"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"ResponsibilityTransferFrame.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class WorkflowPauseResult(_CanonicalMixin):
    """Result of pausing a run: internal lifecycle transition only."""

    pause_state: WorkflowPauseState
    run: WorkflowRun
    previous_lifecycle: WorkflowLifecycleStatus
    node_executed: bool = False
    execution_available: bool = False


@dataclass(frozen=True)
class WorkflowResumeRequest(_CanonicalMixin):
    request_id: str
    target_run_id: str
    decision_signal_id: str
    pause_id: str
    reason: str


@dataclass(frozen=True)
class WorkflowResumeResult(_CanonicalMixin):
    """Internal resume result. Resume is not execution."""

    request: WorkflowResumeRequest
    run: WorkflowRun
    resumed_internal: bool
    lifecycle_after: WorkflowLifecycleStatus
    reason: str
    node_executed: bool = False
    execution_available: bool = False


@dataclass(frozen=True)
class WorkflowStopRequest(_CanonicalMixin):
    request_id: str
    target_run_id: str
    decision_signal_id: str
    reason: str


@dataclass(frozen=True)
class WorkflowStopResult(_CanonicalMixin):
    """Internal stop result: lifecycle moves to CANCELLED. Not execution."""

    request: WorkflowStopRequest
    run: WorkflowRun
    stopped_internal: bool
    lifecycle_after: WorkflowLifecycleStatus
    reason: str
    node_executed: bool = False
    execution_available: bool = False


@dataclass(frozen=True)
class WorkflowRejectRequest(_CanonicalMixin):
    request_id: str
    target_run_id: str
    target_node_id: str
    decision_signal_id: str
    reason: str


@dataclass(frozen=True)
class WorkflowRejectResult(_CanonicalMixin):
    """Internal reject result: target node marked BLOCKED. Not execution."""

    request: WorkflowRejectRequest
    run: WorkflowRun
    rejected_internal: bool
    node_state_after: WorkflowNodeState
    reason: str
    node_executed: bool = False
    execution_available: bool = False


@dataclass(frozen=True)
class WorkflowPauseReadModel(_CanonicalMixin):
    """Pause/operator state read model with honest authority boundaries."""

    read_model_version: str
    run_id: str
    pause_states: tuple[WorkflowPauseState, ...]
    operator_signals: tuple[OperatorDecisionSignal, ...]
    responsibility_frames: tuple[ResponsibilityTransferFrame, ...]
    paused_count: int
    truth_label: FlowTruthLabel
    authority_unavailable_reason: str
    execution_unavailable_reason: str
    read_model_hash: str
    execution_available: bool = False
    authority_available: bool = False


def pause_workflow_run(
    run: WorkflowRun,
    *,
    pause_reason: WorkflowPauseReason,
    target_node_id: str = "",
    waiting_for: str = "",
    source_event_id: str = "",
    requires_operator_decision: bool = True,
    resumable: bool = True,
    metadata: Mapping[str, str] | None = None,
) -> WorkflowPauseResult:
    """Pause a run with an explicit reason via the safe lifecycle map.

    Internal AurelFlow state only; fails closed if the current lifecycle
    cannot pause (e.g. CREATED or terminal states).
    """

    previous = run.state.lifecycle_status
    paused_run = transition_workflow_run(
        run,
        lifecycle_transition(
            previous, WorkflowLifecycleStatus.PAUSED, reason=pause_reason.value
        ),
    )
    pause_id = "wfpause-" + stable_hash(
        {
            "run_id": run.run_id,
            "step": run.state.step,
            "pause_reason": pause_reason,
            "target_node_id": target_node_id,
        }
    )[:16]
    pause_state = WorkflowPauseState(
        pause_id=pause_id,
        contract_version=WORKFLOW_PAUSE_STATE_VERSION,
        target_run_id=run.run_id,
        target_node_id=target_node_id,
        pause_reason=pause_reason,
        source_event_id=source_event_id,
        waiting_for=waiting_for or pause_reason.value,
        resumable=resumable,
        requires_operator_decision=requires_operator_decision,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        metadata=dict(metadata or {}),
    )
    return WorkflowPauseResult(
        pause_state=pause_state,
        run=paused_run,
        previous_lifecycle=previous,
    )


def create_operator_decision_signal(
    *,
    operator_id: str,
    decision_kind: OperatorDecisionKind,
    target_run_id: str,
    target_node_id: str = "",
    reason: str = "",
    counterargument_present: bool = False,
    minority_objection_present: bool = False,
    mediation_required: bool = False,
    decision_pressure_warning: bool = False,
    metadata: Mapping[str, str] | None = None,
) -> OperatorDecisionSignal:
    if not operator_id:
        raise AurelFlowValidationError(
            "operator_id must be non-empty",
            code=AurelFlowErrorCode.EMPTY_ACTOR_ID,
            field="operator_id",
        )
    decision_id = "opdec-" + stable_hash(
        {
            "operator_id": operator_id,
            "decision_kind": decision_kind,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "reason": reason,
        }
    )[:16]
    return OperatorDecisionSignal(
        decision_id=decision_id,
        contract_version=OPERATOR_DECISION_SIGNAL_VERSION,
        operator_id=operator_id,
        decision_kind=decision_kind,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        reason=reason,
        counterargument_present=counterargument_present,
        minority_objection_present=minority_objection_present,
        mediation_required=mediation_required,
        decision_pressure_warning=decision_pressure_warning,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        metadata=dict(metadata or {}),
    )


def _require_signal(
    signal: OperatorDecisionSignal, expected: OperatorDecisionKind, run: WorkflowRun
) -> None:
    if signal.decision_kind is not expected:
        raise AurelFlowValidationError(
            f"operator signal kind {signal.decision_kind.value!r} does not authorize "
            f"a {expected.value} state change",
            code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
            field="decision_kind",
        )
    if signal.target_run_id != run.run_id:
        raise AurelFlowValidationError(
            f"operator signal targets run {signal.target_run_id!r}, not {run.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="target_run_id",
        )


def resume_workflow_run(
    run: WorkflowRun,
    pause_state: WorkflowPauseState,
    signal: OperatorDecisionSignal,
    *,
    reason: str = "",
) -> WorkflowResumeResult:
    """Resume internal lifecycle state (PAUSED -> RUNNING). Not execution."""

    _require_signal(signal, OperatorDecisionKind.RESUME, run)
    if pause_state.target_run_id != run.run_id:
        raise AurelFlowValidationError(
            f"pause state targets run {pause_state.target_run_id!r}, not {run.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="pause_state",
        )
    if not pause_state.resumable:
        raise AurelFlowValidationError(
            f"pause {pause_state.pause_id!r} is not resumable",
            code=AurelFlowErrorCode.NOT_RESUMABLE,
            field="resumable",
        )
    resumed_run = transition_workflow_run(
        run,
        lifecycle_transition(
            run.state.lifecycle_status,
            WorkflowLifecycleStatus.RUNNING,
            reason=reason or "operator resume signal recorded",
        ),
    )
    request = WorkflowResumeRequest(
        request_id="wfres-" + stable_hash(
            {"run_id": run.run_id, "pause_id": pause_state.pause_id, "signal": signal.decision_id}
        )[:16],
        target_run_id=run.run_id,
        decision_signal_id=signal.decision_id,
        pause_id=pause_state.pause_id,
        reason=reason,
    )
    return WorkflowResumeResult(
        request=request,
        run=resumed_run,
        resumed_internal=True,
        lifecycle_after=resumed_run.state.lifecycle_status,
        reason="internal lifecycle resumed; no node executed, no execution permission granted",
    )


def stop_workflow_run(
    run: WorkflowRun,
    signal: OperatorDecisionSignal,
    *,
    reason: str = "",
) -> WorkflowStopResult:
    """Stop internal lifecycle state (-> CANCELLED). Not execution."""

    _require_signal(signal, OperatorDecisionKind.STOP, run)
    stopped_run = transition_workflow_run(
        run,
        lifecycle_transition(
            run.state.lifecycle_status,
            WorkflowLifecycleStatus.CANCELLED,
            reason=reason or "operator stop signal recorded",
        ),
    )
    request = WorkflowStopRequest(
        request_id="wfstop-" + stable_hash(
            {"run_id": run.run_id, "signal": signal.decision_id}
        )[:16],
        target_run_id=run.run_id,
        decision_signal_id=signal.decision_id,
        reason=reason,
    )
    return WorkflowStopResult(
        request=request,
        run=stopped_run,
        stopped_internal=True,
        lifecycle_after=stopped_run.state.lifecycle_status,
        reason="internal lifecycle cancelled; no node executed",
    )


def reject_workflow_path(
    run: WorkflowRun,
    target_node_id: str,
    signal: OperatorDecisionSignal,
    *,
    reason: str = "",
) -> WorkflowRejectResult:
    """Mark a node BLOCKED as internal operator-reject state. Not execution."""

    _require_signal(signal, OperatorDecisionKind.REJECT, run)
    if target_node_id not in run.state.node_states:
        raise AurelFlowValidationError(
            f"node {target_node_id!r} is not part of run {run.run_id!r}",
            code=AurelFlowErrorCode.UNKNOWN_TRANSITION_TARGET,
            field="target_node_id",
        )
    current = run.state.node_states[target_node_id]
    rejected_run = transition_workflow_run(
        run,
        node_transition(
            target_node_id,
            current,
            WorkflowNodeState.BLOCKED,
            reason=reason or "operator reject signal recorded",
        ),
    )
    request = WorkflowRejectRequest(
        request_id="wfrej-" + stable_hash(
            {"run_id": run.run_id, "node": target_node_id, "signal": signal.decision_id}
        )[:16],
        target_run_id=run.run_id,
        target_node_id=target_node_id,
        decision_signal_id=signal.decision_id,
        reason=reason,
    )
    return WorkflowRejectResult(
        request=request,
        run=rejected_run,
        rejected_internal=True,
        node_state_after=rejected_run.state.node_states[target_node_id],
        reason="node marked BLOCKED as internal reject state; no node executed",
    )


def create_responsibility_transfer_frame(
    *,
    from_actor: str,
    to_actor: str,
    target_run_id: str,
    reason: str,
    target_node_id: str = "",
    scope: str = "RUN_CONTINUATION",
    handoff_state: str = "RECORDED",
    metadata: Mapping[str, str] | None = None,
) -> ResponsibilityTransferFrame:
    if not from_actor or not to_actor:
        raise AurelFlowValidationError(
            "from_actor and to_actor must be non-empty",
            code=AurelFlowErrorCode.EMPTY_ACTOR_ID,
            field="from_actor" if not from_actor else "to_actor",
        )
    frame_id = "resp-" + stable_hash(
        {
            "from_actor": from_actor,
            "to_actor": to_actor,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "scope": scope,
        }
    )[:16]
    return ResponsibilityTransferFrame(
        responsibility_frame_id=frame_id,
        contract_version=RESPONSIBILITY_TRANSFER_FRAME_VERSION,
        from_actor=from_actor,
        to_actor=to_actor,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        reason=reason,
        scope=scope,
        handoff_state=handoff_state,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        metadata=dict(metadata or {}),
    )


def build_workflow_pause_read_model(
    run_id: str,
    *,
    pause_states: tuple[WorkflowPauseState, ...] = (),
    operator_signals: tuple[OperatorDecisionSignal, ...] = (),
    responsibility_frames: tuple[ResponsibilityTransferFrame, ...] = (),
) -> WorkflowPauseReadModel:
    payload = {
        "read_model_version": WORKFLOW_PAUSE_READ_MODEL_VERSION,
        "run_id": run_id,
        "pause_ids": tuple(state.pause_id for state in pause_states),
        "signal_ids": tuple(signal.decision_id for signal in operator_signals),
        "frame_ids": tuple(frame.responsibility_frame_id for frame in responsibility_frames),
    }
    return WorkflowPauseReadModel(
        read_model_version=WORKFLOW_PAUSE_READ_MODEL_VERSION,
        run_id=run_id,
        pause_states=pause_states,
        operator_signals=operator_signals,
        responsibility_frames=responsibility_frames,
        paused_count=len(pause_states),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        authority_unavailable_reason=AUTHORITY_UNAVAILABLE_REASON,
        execution_unavailable_reason=EXECUTION_UNAVAILABLE_REASON,
        read_model_hash=stable_hash(payload),
    )
