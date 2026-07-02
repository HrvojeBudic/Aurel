"""P3-FLOW-B runtime behavior read model (operator-inspectable truth).

Aggregates the whole behavior loop — events, mediated outputs, state
commitments, pause state, operator signals, responsibility frames, retry
eligibility, recovery proposals, rollback candidates — with honest truth
labels and explicit unavailable boundaries. Inspecting behavior never
triggers execution. Nothing here is LIVE and nothing is TRACE_VERIFIED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .pause_resume import (
    OperatorDecisionSignal,
    ResponsibilityTransferFrame,
    WorkflowPauseState,
)
from .read_model import (
    FlowCapabilityAvailability,
    FlowNoExecutionProof,
    UNAVAILABLE_CAPABILITIES,
)
from .recovery import (
    FailureAssessment,
    RecoveryProposal,
    RetryEligibility,
    RollbackCandidate,
)
from .runtime_events import (
    RUNTIME_EVENT_IS_NOT_TRACE_BOUNDARY,
    RuntimeEventIsNotTraceBoundary,
    RuntimeEventRelationView,
    RuntimeEventStream,
    RuntimeEventStreamSnapshot,
    build_runtime_event_read_model,
    snapshot_runtime_event_stream,
)
from .state_commitment import MediatedActorOutput, RuntimeStateCommitment
from .types import (
    AUREL_FLOW_B_PACK_ID,
    AUTHORITY_UNAVAILABLE_REASON,
    CLI_BINDING_UNAVAILABLE_REASON,
    LEDGER_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
    to_canonical_json,
)

RUNTIME_BEHAVIOR_READ_MODEL_VERSION = "runtime_behavior_read_model.v1"


@dataclass(frozen=True)
class RuntimeBehaviorNoExecutionProof(_CanonicalMixin):
    """Behavior-loop no-execution proof: the P3-FLOW-A proof plus the
    behavior-specific negatives introduced by this pack."""

    foundation: FlowNoExecutionProof
    retry_executed: bool = False
    recovery_executed: bool = False
    rollback_executed: bool = False
    resume_executed_node: bool = False
    pause_executed_node: bool = False
    operator_signal_granted_authority: bool = False
    responsibility_authority_transferred: bool = False
    runtime_event_wrote_trace: bool = False
    runtime_event_wrote_ledger: bool = False
    state_commitment_wrote_ledger: bool = False


BEHAVIOR_UNAVAILABLE_CAPABILITIES: tuple[FlowCapabilityAvailability, ...] = (
    UNAVAILABLE_CAPABILITIES
    + (
        FlowCapabilityAvailability(
            capability="UNAVAILABLE_AUTHORITY",
            available=False,
            truth_label=FlowTruthLabel.UNAVAILABLE,
            reason=AUTHORITY_UNAVAILABLE_REASON,
        ),
        FlowCapabilityAvailability(
            capability="UNAVAILABLE_LEDGER",
            available=False,
            truth_label=FlowTruthLabel.UNAVAILABLE,
            reason=LEDGER_UNAVAILABLE_REASON,
        ),
    )
)


@dataclass(frozen=True)
class RuntimeBehaviorReadModel(_CanonicalMixin):
    """Operator-facing read model for the P3-FLOW-B behavior loop."""

    read_model_version: str
    pack_id: str
    run_id: str
    event_stream_snapshot: RuntimeEventStreamSnapshot | None
    events_count: int
    event_relations: tuple[RuntimeEventRelationView, ...]
    mediated_actor_outputs: tuple[MediatedActorOutput, ...]
    state_commitments: tuple[RuntimeStateCommitment, ...]
    pause_states: tuple[WorkflowPauseState, ...]
    operator_decision_signals: tuple[OperatorDecisionSignal, ...]
    responsibility_transfer_frames: tuple[ResponsibilityTransferFrame, ...]
    retry_eligibilities: tuple[RetryEligibility, ...]
    recovery_proposals: tuple[RecoveryProposal, ...]
    rollback_candidates: tuple[RollbackCandidate, ...]
    failure_assessments: tuple[FailureAssessment, ...]
    failure_classifications: tuple[str, ...]
    failure_propagation_risks: tuple[str, ...]
    predictability_labels: tuple[str, ...]
    truth_labels: Mapping[str, str]
    unavailable_capabilities: tuple[FlowCapabilityAvailability, ...]
    trace_boundary: RuntimeEventIsNotTraceBoundary
    no_execution_proof: RuntimeBehaviorNoExecutionProof
    cli_binding_unavailable_reason: str
    read_model_hash: str
    execution_available: bool = False
    trace_verified: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False


def build_runtime_behavior_read_model(
    run_id: str,
    *,
    event_stream: RuntimeEventStream | None = None,
    mediated_actor_outputs: tuple[MediatedActorOutput, ...] = (),
    state_commitments: tuple[RuntimeStateCommitment, ...] = (),
    pause_states: tuple[WorkflowPauseState, ...] = (),
    operator_decision_signals: tuple[OperatorDecisionSignal, ...] = (),
    responsibility_transfer_frames: tuple[ResponsibilityTransferFrame, ...] = (),
    retry_eligibilities: tuple[RetryEligibility, ...] = (),
    recovery_proposals: tuple[RecoveryProposal, ...] = (),
    rollback_candidates: tuple[RollbackCandidate, ...] = (),
    failure_assessments: tuple[FailureAssessment, ...] = (),
) -> RuntimeBehaviorReadModel:
    """Aggregate behavior truth deterministically. Pure; executes nothing."""

    snapshot = None
    relations: tuple[RuntimeEventRelationView, ...] = ()
    events_count = 0
    predictability_labels: tuple[str, ...] = ()
    if event_stream is not None:
        snapshot = snapshot_runtime_event_stream(event_stream)
        event_read_model = build_runtime_event_read_model(event_stream)
        relations = event_read_model.relations
        events_count = event_read_model.event_count
        predictability_labels = tuple(
            sorted({event.predictability_label for event in event_stream.events})
        )

    truth_labels = {
        "events": FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR.value,
        "state_commitments": FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR.value,
        "pause_states": FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR.value,
        "recovery": FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR.value,
        "execution": FlowTruthLabel.UNAVAILABLE.value,
        "trace_verification": FlowTruthLabel.UNAVAILABLE.value,
        "ledger": FlowTruthLabel.UNAVAILABLE.value,
        "authority": FlowTruthLabel.UNAVAILABLE.value,
        "cli_binding": FlowTruthLabel.UNAVAILABLE.value,
    }
    payload = {
        "read_model_version": RUNTIME_BEHAVIOR_READ_MODEL_VERSION,
        "run_id": run_id,
        "snapshot_hash": snapshot.snapshot_hash if snapshot else "",
        "commitment_ids": tuple(item.commitment_id for item in state_commitments),
        "pause_ids": tuple(item.pause_id for item in pause_states),
        "signal_ids": tuple(item.decision_id for item in operator_decision_signals),
        "frame_ids": tuple(
            item.responsibility_frame_id for item in responsibility_transfer_frames
        ),
        "eligibility_ids": tuple(item.eligibility_id for item in retry_eligibilities),
        "proposal_ids": tuple(item.proposal_id for item in recovery_proposals),
        "candidate_ids": tuple(item.candidate_id for item in rollback_candidates),
    }
    return RuntimeBehaviorReadModel(
        read_model_version=RUNTIME_BEHAVIOR_READ_MODEL_VERSION,
        pack_id=AUREL_FLOW_B_PACK_ID,
        run_id=run_id,
        event_stream_snapshot=snapshot,
        events_count=events_count,
        event_relations=relations,
        mediated_actor_outputs=mediated_actor_outputs,
        state_commitments=state_commitments,
        pause_states=pause_states,
        operator_decision_signals=operator_decision_signals,
        responsibility_transfer_frames=responsibility_transfer_frames,
        retry_eligibilities=retry_eligibilities,
        recovery_proposals=recovery_proposals,
        rollback_candidates=rollback_candidates,
        failure_assessments=failure_assessments,
        failure_classifications=tuple(
            assessment.classification.value for assessment in failure_assessments
        ),
        failure_propagation_risks=tuple(
            assessment.propagation_risk.value for assessment in failure_assessments
        ),
        predictability_labels=predictability_labels,
        truth_labels=truth_labels,
        unavailable_capabilities=BEHAVIOR_UNAVAILABLE_CAPABILITIES,
        trace_boundary=RUNTIME_EVENT_IS_NOT_TRACE_BOUNDARY,
        no_execution_proof=RuntimeBehaviorNoExecutionProof(foundation=FlowNoExecutionProof()),
        cli_binding_unavailable_reason=CLI_BINDING_UNAVAILABLE_REASON,
        read_model_hash=stable_hash(payload),
    )


def serialize_runtime_behavior_read_model(read_model: RuntimeBehaviorReadModel) -> str:
    """Deterministic JSON export for operator inspection."""

    return to_canonical_json(read_model)
