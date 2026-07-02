"""P3-FLOW-C flow state projection layer (read-only operator visibility).

Projects the existing P3-FLOW-A/B substrate — actual code inventory, graph /
run / scheduler state, mediated commitments, responsibility, pause/operator
decisions, failure/recovery/rollback candidates, and demo truth — into
deterministic read models. Projection is not execution. Inspection is not
authority. Nothing here mutates a WorkflowRun, transitions a node, writes
Trace or Ledger, or claims LIVE / TRACE_VERIFIED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

from .demo import FlowDemoBundle
from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .read_model import FlowNoExecutionProof
from .runtime_behavior_read_model import RuntimeBehaviorReadModel
from .scheduler import SchedulerDecision, make_scheduler_decision
from .types import (
    AUREL_FLOW_C_PACK_ID,
    AUTHORITY_UNAVAILABLE_REASON,
    EXECUTION_UNAVAILABLE_REASON,
    LEDGER_UNAVAILABLE_REASON,
    PERSISTENCE_UNAVAILABLE_REASON,
    TOP_LEVEL_EXPORT_UNAVAILABLE_REASON,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)
from .workflow_graph import WorkflowGraph
from .workflow_state import WorkflowRun

FLOW_ACTUAL_CODE_INVENTORY_VERSION = "flow_actual_code_inventory.v1"
FLOW_STATE_PROJECTION_VERSION = "flow_state_projection.v1"
FLOW_BEHAVIOR_PROJECTION_VERSION = "flow_behavior_projection.v1"
FLOW_DEMO_TRUTH_PROJECTION_VERSION = "flow_demo_truth_projection.v1"

AUREL_FLOW_PACKAGE_NAME = "agentic_runtime.aurel_flow"

KNOWN_FLOW_A_MODULES: tuple[str, ...] = (
    "demo.py",
    "errors.py",
    "read_model.py",
    "scheduler.py",
    "types.py",
    "workflow_graph.py",
    "workflow_state.py",
)
KNOWN_FLOW_B_MODULES: tuple[str, ...] = (
    "pause_resume.py",
    "recovery.py",
    "runtime_behavior_read_model.py",
    "runtime_events.py",
    "state_commitment.py",
)
KNOWN_FLOW_C_MODULES: tuple[str, ...] = (
    "flow_cli.py",
    "flow_observability.py",
    "flow_projection.py",
    "flow_protocol.py",
    "flow_seal.py",
    "flow_timeline.py",
    "flow_wiring.py",
)


class FlowPackageExportStatus(str, Enum):
    """How the aurel_flow package is exposed. Closed-world."""

    PACKAGE_EXPORTED_INTERNAL = "PACKAGE_EXPORTED_INTERNAL"
    TOP_LEVEL_EXPORT_UNAVAILABLE = "TOP_LEVEL_EXPORT_UNAVAILABLE"


class FlowPublicSurfaceStatus(str, Enum):
    """Honest public-surface exposure status for a Flow capability."""

    NOT_WIRED = "NOT_WIRED"
    CLI_READ_ONLY = "CLI_READ_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    FUTURE_P3D = "FUTURE_P3D"
    FUTURE_P4 = "FUTURE_P4"
    FUTURE_P5 = "FUTURE_P5"
    FUTURE_P9 = "FUTURE_P9"


@dataclass(frozen=True)
class FlowPackageInventoryItem(_CanonicalMixin):
    """One actually-present module in the aurel_flow package."""

    module_name: str
    layer: str
    truth_label: FlowTruthLabel = FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE


@dataclass(frozen=True)
class FlowActualCodeInventoryReadModel(_CanonicalMixin):
    """What agentic_runtime.aurel_flow actually contains and how it is wired.

    Integration booleans fail closed: this pack cannot claim runtime.py /
    entity / repo_agent / build_runtime / trace / policy integration or a
    top-level export, because none exists.
    """

    read_model_version: str
    pack_id: str
    package_name: str
    module_count: int
    test_count: int
    known_flow_a_modules: tuple[str, ...]
    known_flow_b_modules: tuple[str, ...]
    known_flow_c_modules: tuple[str, ...]
    inventory_items: tuple[FlowPackageInventoryItem, ...]
    package_export_status: FlowPackageExportStatus
    cli_surface_status: FlowPublicSurfaceStatus
    production_deps: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reasons: Mapping[str, str]
    read_model_hash: str
    package_exported: bool = True
    top_level_exported: bool = False
    runtime_py_integrated: bool = False
    cli_integrated_read_only: bool = True
    agentic_entity_integrated: bool = False
    repo_agent_integrated: bool = False
    build_runtime_integrated: bool = False
    trace_integrated: bool = False
    policy_integrated: bool = False
    persistence_available: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "top_level_exported",
            "runtime_py_integrated",
            "agentic_entity_integrated",
            "repo_agent_integrated",
            "build_runtime_integrated",
            "trace_integrated",
            "policy_integrated",
            "persistence_available",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowActualCodeInventoryReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def _package_dir() -> Path:
    return Path(__file__).resolve().parent


def _repo_tests_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "tests"


def build_flow_actual_code_inventory(
    module_filenames: tuple[str, ...] | None = None,
    test_filenames: tuple[str, ...] | None = None,
    *,
    cli_read_only_implemented: bool = True,
) -> FlowActualCodeInventoryReadModel:
    """Build the inventory from repo truth (read-only directory listing) or
    from explicitly passed filenames. Never infers fake integration."""

    if module_filenames is None:
        module_filenames = tuple(
            sorted(path.name for path in _package_dir().glob("*.py"))
        )
    if test_filenames is None:
        tests_dir = _repo_tests_dir()
        test_filenames = (
            tuple(sorted(path.name for path in tests_dir.glob("test_p3_flow_*.py")))
            if tests_dir.is_dir()
            else ()
        )

    def _layer(name: str) -> str:
        if name in KNOWN_FLOW_A_MODULES:
            return "FLOW_A"
        if name in KNOWN_FLOW_B_MODULES:
            return "FLOW_B"
        if name in KNOWN_FLOW_C_MODULES:
            return "FLOW_C"
        return "PACKAGE"

    items = tuple(
        FlowPackageInventoryItem(module_name=name, layer=_layer(name))
        for name in module_filenames
    )
    unavailable_reasons = {
        "top_level_export": TOP_LEVEL_EXPORT_UNAVAILABLE_REASON,
        "execution": EXECUTION_UNAVAILABLE_REASON,
        "trace_verification": TRACE_VERIFICATION_UNAVAILABLE_REASON,
        "persistence": PERSISTENCE_UNAVAILABLE_REASON,
    }
    cli_status = (
        FlowPublicSurfaceStatus.CLI_READ_ONLY
        if cli_read_only_implemented
        else FlowPublicSurfaceStatus.NOT_WIRED
    )
    payload = {
        "read_model_version": FLOW_ACTUAL_CODE_INVENTORY_VERSION,
        "modules": module_filenames,
        "tests": test_filenames,
        "cli_status": cli_status.value,
    }
    return FlowActualCodeInventoryReadModel(
        read_model_version=FLOW_ACTUAL_CODE_INVENTORY_VERSION,
        pack_id=AUREL_FLOW_C_PACK_ID,
        package_name=AUREL_FLOW_PACKAGE_NAME,
        module_count=len(module_filenames),
        test_count=len(test_filenames),
        known_flow_a_modules=KNOWN_FLOW_A_MODULES,
        known_flow_b_modules=KNOWN_FLOW_B_MODULES,
        known_flow_c_modules=KNOWN_FLOW_C_MODULES,
        inventory_items=items,
        package_export_status=FlowPackageExportStatus.PACKAGE_EXPORTED_INTERNAL,
        cli_surface_status=cli_status,
        production_deps=(),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
        unavailable_reasons=unavailable_reasons,
        read_model_hash=stable_hash(payload),
        cli_integrated_read_only=cli_read_only_implemented,
    )


@dataclass(frozen=True)
class FlowProjectionTruth(_CanonicalMixin):
    """Hard truth booleans carried by every P3-FLOW-C projection."""

    truth_label: FlowTruthLabel
    execution_unavailable_reason: str = EXECUTION_UNAVAILABLE_REASON
    trace_unavailable_reason: str = TRACE_VERIFICATION_UNAVAILABLE_REASON
    live: bool = False
    trace_verified: bool = False
    execution_available: bool = False
    ledger_written: bool = False
    persistence_available: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "live",
            "trace_verified",
            "execution_available",
            "ledger_written",
            "persistence_available",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FlowProjectionTruth.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class FlowCapabilityProjection(_CanonicalMixin):
    """One capability's honest exposure status inside the projection."""

    capability: str
    status: FlowPublicSurfaceStatus
    truth_label: FlowTruthLabel
    reason: str


@dataclass(frozen=True)
class FlowBehaviorSummary(_CanonicalMixin):
    """Count summary of the P3-FLOW-B behavior loop for one run."""

    events_count: int = 0
    pause_count: int = 0
    commitment_count: int = 0
    mediated_output_count: int = 0
    operator_signal_count: int = 0
    responsibility_frame_count: int = 0
    retry_eligibility_count: int = 0
    recovery_proposal_count: int = 0
    rollback_candidate_count: int = 0
    failure_count: int = 0


@dataclass(frozen=True)
class FlowStateProjection(_CanonicalMixin):
    """Read-only projection of graph / run / scheduler / behavior state."""

    projection_version: str
    pack_id: str
    graph_id: str
    run_id: str
    run_key: str
    step: int
    lifecycle_status: str
    node_states: Mapping[str, str]
    ready_node_ids: tuple[str, ...]
    waiting_dependency_node_ids: tuple[str, ...]
    waiting_approval_node_ids: tuple[str, ...]
    blocked_node_ids: tuple[str, ...]
    next_ready_node_id: str
    behavior_summary: FlowBehaviorSummary
    capability_projections: tuple[FlowCapabilityProjection, ...]
    truth_labels: Mapping[str, str]
    truth: FlowProjectionTruth
    no_execution_proof: FlowNoExecutionProof
    projection_hash: str


FLOW_STATE_CAPABILITY_PROJECTIONS: tuple[FlowCapabilityProjection, ...] = (
    FlowCapabilityProjection(
        capability="flow_state_projection",
        status=FlowPublicSurfaceStatus.READ_MODEL_ONLY,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        reason="pure read-only projection over immutable run state",
    ),
    FlowCapabilityProjection(
        capability="execution",
        status=FlowPublicSurfaceStatus.FUTURE_P4,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=EXECUTION_UNAVAILABLE_REASON,
    ),
    FlowCapabilityProjection(
        capability="trace_verification",
        status=FlowPublicSurfaceStatus.FUTURE_P5,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
    ),
    FlowCapabilityProjection(
        capability="authority",
        status=FlowPublicSurfaceStatus.FUTURE_P9,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=AUTHORITY_UNAVAILABLE_REASON,
    ),
    FlowCapabilityProjection(
        capability="persistence",
        status=FlowPublicSurfaceStatus.UNAVAILABLE,
        truth_label=FlowTruthLabel.UNAVAILABLE,
        reason=PERSISTENCE_UNAVAILABLE_REASON,
    ),
)


def build_flow_state_projection(
    graph: WorkflowGraph,
    run: WorkflowRun,
    behavior_read_model: RuntimeBehaviorReadModel | None = None,
    scheduler_decision: SchedulerDecision | None = None,
) -> FlowStateProjection:
    """Project graph / run / scheduler / behavior truth. Pure and read-only:
    the input run is never mutated and no node state is transitioned."""

    decision = scheduler_decision or make_scheduler_decision(graph, run)
    if decision.run_id != run.run_id or decision.step != run.state.step:
        raise AurelFlowValidationError(
            f"scheduler decision {decision.run_id!r}@{decision.step} does not match "
            f"run {run.run_id!r}@{run.state.step}",
            code=AurelFlowErrorCode.GRAPH_RUN_MISMATCH,
            field="scheduler_decision",
        )
    reasons: dict[str, list[str]] = {
        "WAITING_DEPENDENCY": [],
        "WAITING_APPROVAL": [],
        "BLOCKED": [],
    }
    for node_decision in decision.node_decisions:
        bucket = reasons.get(node_decision.reason.value)
        if bucket is not None:
            bucket.append(node_decision.node_id)
    behavior_summary = FlowBehaviorSummary()
    if behavior_read_model is not None:
        behavior_summary = FlowBehaviorSummary(
            events_count=behavior_read_model.events_count,
            pause_count=len(behavior_read_model.pause_states),
            commitment_count=len(behavior_read_model.state_commitments),
            mediated_output_count=len(behavior_read_model.mediated_actor_outputs),
            operator_signal_count=len(behavior_read_model.operator_decision_signals),
            responsibility_frame_count=len(
                behavior_read_model.responsibility_transfer_frames
            ),
            retry_eligibility_count=len(behavior_read_model.retry_eligibilities),
            recovery_proposal_count=len(behavior_read_model.recovery_proposals),
            rollback_candidate_count=len(behavior_read_model.rollback_candidates),
            failure_count=len(behavior_read_model.failure_assessments),
        )
    node_states = {
        node_id: state.value for node_id, state in sorted(run.state.node_states.items())
    }
    truth_labels = {
        "graph": graph.truth_label.value,
        "run": run.truth_label.value,
        "scheduler": decision.truth_label.value,
        "projection": FlowTruthLabel.READ_MODEL_ONLY.value,
        "execution": FlowTruthLabel.UNAVAILABLE.value,
        "trace_verification": FlowTruthLabel.UNAVAILABLE.value,
    }
    payload = {
        "projection_version": FLOW_STATE_PROJECTION_VERSION,
        "graph_hash": graph.graph_hash,
        "run_id": run.run_id,
        "step": run.state.step,
        "decision_hash": decision.decision_hash,
        "behavior": behavior_summary.to_canonical_dict(),
    }
    return FlowStateProjection(
        projection_version=FLOW_STATE_PROJECTION_VERSION,
        pack_id=AUREL_FLOW_C_PACK_ID,
        graph_id=graph.graph_id,
        run_id=run.run_id,
        run_key=run.run_key,
        step=run.state.step,
        lifecycle_status=run.state.lifecycle_status.value,
        node_states=node_states,
        ready_node_ids=decision.ready_node_ids,
        waiting_dependency_node_ids=tuple(reasons["WAITING_DEPENDENCY"]),
        waiting_approval_node_ids=tuple(reasons["WAITING_APPROVAL"]),
        blocked_node_ids=tuple(reasons["BLOCKED"]),
        next_ready_node_id=decision.next_ready_node_id,
        behavior_summary=behavior_summary,
        capability_projections=FLOW_STATE_CAPABILITY_PROJECTIONS,
        truth_labels=truth_labels,
        truth=FlowProjectionTruth(truth_label=FlowTruthLabel.READ_MODEL_ONLY),
        no_execution_proof=FlowNoExecutionProof(),
        projection_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class MediatedActorOutputReadModel(_CanonicalMixin):
    """Projection of mediated actor outputs: mediation truth preserved."""

    read_model_version: str
    run_id: str
    output_ids: tuple[str, ...]
    output_count: int
    actor_ids: tuple[str, ...]
    truth: FlowProjectionTruth
    read_model_hash: str
    direct_state_mutation_allowed_any: bool = False

    def __post_init__(self) -> None:
        if self.direct_state_mutation_allowed_any:
            raise AurelFlowValidationError(
                "MediatedActorOutputReadModel.direct_state_mutation_allowed_any must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="direct_state_mutation_allowed_any",
            )


@dataclass(frozen=True)
class StateCommitmentReadModel(_CanonicalMixin):
    """Projection of internal state commitments: internal scope only."""

    read_model_version: str
    run_id: str
    commitment_ids: tuple[str, ...]
    commitment_count: int
    commit_statuses: tuple[str, ...]
    mutation_scopes: tuple[str, ...]
    ledger_unavailable_reason: str
    truth: FlowProjectionTruth
    read_model_hash: str
    ledger_written_any: bool = False
    external_side_effect_any: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("ledger_written_any", "external_side_effect_any"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"StateCommitmentReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class ResponsibilityTransferReadModel(_CanonicalMixin):
    """Projection of responsibility handoffs: never authority transfer."""

    read_model_version: str
    run_id: str
    frame_ids: tuple[str, ...]
    frame_count: int
    handoffs: tuple[str, ...]
    authority_unavailable_reason: str
    truth: FlowProjectionTruth
    read_model_hash: str
    authority_transferred_any: bool = False
    execution_permission_granted_any: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "authority_transferred_any",
            "execution_permission_granted_any",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"ResponsibilityTransferReadModel.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class OperatorDecisionQualityProjection(_CanonicalMixin):
    """Deliberation-quality visibility over operator decision signals."""

    signal_count: int
    counterargument_present_count: int
    minority_objection_count: int
    mediation_required_count: int
    decision_pressure_warning_count: int
    authority_granted_any: bool = False
    execution_permission_granted_any: bool = False

    def __post_init__(self) -> None:
        for boundary_field in (
            "authority_granted_any",
            "execution_permission_granted_any",
        ):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"OperatorDecisionQualityProjection.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class PauseDecisionReadModel(_CanonicalMixin):
    """Projection of pause states and operator decision signals."""

    read_model_version: str
    run_id: str
    pause_ids: tuple[str, ...]
    pause_count: int
    pause_reasons: tuple[str, ...]
    signal_ids: tuple[str, ...]
    signal_kinds: tuple[str, ...]
    decision_quality: OperatorDecisionQualityProjection
    authority_unavailable_reason: str
    truth: FlowProjectionTruth
    read_model_hash: str


@dataclass(frozen=True)
class FailureRecoveryProjection(_CanonicalMixin):
    """Projection of failure / retry / recovery candidates: never execution."""

    read_model_version: str
    run_id: str
    failure_classifications: tuple[str, ...]
    failure_propagation_risks: tuple[str, ...]
    retry_eligibility_ids: tuple[str, ...]
    eligible_retry_count: int
    ineligible_retry_count: int
    recovery_proposal_ids: tuple[str, ...]
    recovery_step_count: int
    execution_unavailable_reason: str
    truth: FlowProjectionTruth
    read_model_hash: str
    retry_executed_any: bool = False
    recovery_executed_any: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("retry_executed_any", "recovery_executed_any"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"FailureRecoveryProjection.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class RollbackCandidateProjection(_CanonicalMixin):
    """Projection of rollback candidates: marked only, never rolled back."""

    read_model_version: str
    run_id: str
    candidate_ids: tuple[str, ...]
    candidate_count: int
    candidate_reasons: tuple[str, ...]
    target_state_refs: tuple[str, ...]
    truth: FlowProjectionTruth
    read_model_hash: str
    safe_to_execute_any: bool = False
    rollback_executed_any: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("safe_to_execute_any", "rollback_executed_any"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RollbackCandidateProjection.{boundary_field} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


def _behavior_truth() -> FlowProjectionTruth:
    return FlowProjectionTruth(truth_label=FlowTruthLabel.READ_MODEL_ONLY)


def build_mediated_actor_output_read_model(
    behavior: RuntimeBehaviorReadModel,
) -> MediatedActorOutputReadModel:
    output_ids = tuple(item.output_id for item in behavior.mediated_actor_outputs)
    actor_ids = tuple(
        sorted({item.actor_id for item in behavior.mediated_actor_outputs})
    )
    return MediatedActorOutputReadModel(
        read_model_version=FLOW_BEHAVIOR_PROJECTION_VERSION,
        run_id=behavior.run_id,
        output_ids=output_ids,
        output_count=len(output_ids),
        actor_ids=actor_ids,
        truth=_behavior_truth(),
        read_model_hash=stable_hash(
            {"kind": "mediated_actor_output", "run_id": behavior.run_id, "ids": output_ids}
        ),
    )


def build_state_commitment_read_model(
    behavior: RuntimeBehaviorReadModel,
) -> StateCommitmentReadModel:
    commitment_ids = tuple(item.commitment_id for item in behavior.state_commitments)
    return StateCommitmentReadModel(
        read_model_version=FLOW_BEHAVIOR_PROJECTION_VERSION,
        run_id=behavior.run_id,
        commitment_ids=commitment_ids,
        commitment_count=len(commitment_ids),
        commit_statuses=tuple(
            item.commit_status.value for item in behavior.state_commitments
        ),
        mutation_scopes=tuple(
            item.mutation_scope for item in behavior.state_commitments
        ),
        ledger_unavailable_reason=LEDGER_UNAVAILABLE_REASON,
        truth=_behavior_truth(),
        read_model_hash=stable_hash(
            {"kind": "state_commitment", "run_id": behavior.run_id, "ids": commitment_ids}
        ),
    )


def build_responsibility_transfer_read_model(
    behavior: RuntimeBehaviorReadModel,
) -> ResponsibilityTransferReadModel:
    frame_ids = tuple(
        item.responsibility_frame_id
        for item in behavior.responsibility_transfer_frames
    )
    handoffs = tuple(
        f"{item.from_actor}->{item.to_actor}"
        for item in behavior.responsibility_transfer_frames
    )
    return ResponsibilityTransferReadModel(
        read_model_version=FLOW_BEHAVIOR_PROJECTION_VERSION,
        run_id=behavior.run_id,
        frame_ids=frame_ids,
        frame_count=len(frame_ids),
        handoffs=handoffs,
        authority_unavailable_reason=AUTHORITY_UNAVAILABLE_REASON,
        truth=_behavior_truth(),
        read_model_hash=stable_hash(
            {"kind": "responsibility_transfer", "run_id": behavior.run_id, "ids": frame_ids}
        ),
    )


def build_pause_decision_read_model(
    behavior: RuntimeBehaviorReadModel,
) -> PauseDecisionReadModel:
    pause_ids = tuple(item.pause_id for item in behavior.pause_states)
    signal_ids = tuple(
        item.decision_id for item in behavior.operator_decision_signals
    )
    signals = behavior.operator_decision_signals
    quality = OperatorDecisionQualityProjection(
        signal_count=len(signals),
        counterargument_present_count=sum(
            1 for item in signals if item.counterargument_present
        ),
        minority_objection_count=sum(
            1 for item in signals if item.minority_objection_present
        ),
        mediation_required_count=sum(1 for item in signals if item.mediation_required),
        decision_pressure_warning_count=sum(
            1 for item in signals if item.decision_pressure_warning
        ),
    )
    return PauseDecisionReadModel(
        read_model_version=FLOW_BEHAVIOR_PROJECTION_VERSION,
        run_id=behavior.run_id,
        pause_ids=pause_ids,
        pause_count=len(pause_ids),
        pause_reasons=tuple(
            item.pause_reason.value for item in behavior.pause_states
        ),
        signal_ids=signal_ids,
        signal_kinds=tuple(item.decision_kind.value for item in signals),
        decision_quality=quality,
        authority_unavailable_reason=AUTHORITY_UNAVAILABLE_REASON,
        truth=_behavior_truth(),
        read_model_hash=stable_hash(
            {
                "kind": "pause_decision",
                "run_id": behavior.run_id,
                "pause_ids": pause_ids,
                "signal_ids": signal_ids,
            }
        ),
    )


def build_failure_recovery_projection(
    behavior: RuntimeBehaviorReadModel,
) -> FailureRecoveryProjection:
    eligibility_ids = tuple(
        item.eligibility_id for item in behavior.retry_eligibilities
    )
    proposal_ids = tuple(item.proposal_id for item in behavior.recovery_proposals)
    return FailureRecoveryProjection(
        read_model_version=FLOW_BEHAVIOR_PROJECTION_VERSION,
        run_id=behavior.run_id,
        failure_classifications=behavior.failure_classifications,
        failure_propagation_risks=behavior.failure_propagation_risks,
        retry_eligibility_ids=eligibility_ids,
        eligible_retry_count=sum(
            1 for item in behavior.retry_eligibilities if item.eligible
        ),
        ineligible_retry_count=sum(
            1 for item in behavior.retry_eligibilities if not item.eligible
        ),
        recovery_proposal_ids=proposal_ids,
        recovery_step_count=sum(
            len(item.recovery_steps) for item in behavior.recovery_proposals
        ),
        execution_unavailable_reason=EXECUTION_UNAVAILABLE_REASON,
        truth=_behavior_truth(),
        read_model_hash=stable_hash(
            {
                "kind": "failure_recovery",
                "run_id": behavior.run_id,
                "eligibility_ids": eligibility_ids,
                "proposal_ids": proposal_ids,
            }
        ),
    )


def build_rollback_candidate_projection(
    behavior: RuntimeBehaviorReadModel,
) -> RollbackCandidateProjection:
    candidate_ids = tuple(item.candidate_id for item in behavior.rollback_candidates)
    return RollbackCandidateProjection(
        read_model_version=FLOW_BEHAVIOR_PROJECTION_VERSION,
        run_id=behavior.run_id,
        candidate_ids=candidate_ids,
        candidate_count=len(candidate_ids),
        candidate_reasons=tuple(
            item.candidate_reason.value for item in behavior.rollback_candidates
        ),
        target_state_refs=tuple(
            item.target_state_ref for item in behavior.rollback_candidates
        ),
        truth=_behavior_truth(),
        read_model_hash=stable_hash(
            {"kind": "rollback_candidate", "run_id": behavior.run_id, "ids": candidate_ids}
        ),
    )


@dataclass(frozen=True)
class FlowDemoTruthProjection(_CanonicalMixin):
    """Explicit demo truth: demo state is DEV_FIXTURE, never execution.

    The positive booleans must remain True and the negative booleans must
    remain False — both directions fail closed.
    """

    projection_version: str
    graph_id: str
    run_id: str
    truth_label: FlowTruthLabel = FlowTruthLabel.DEV_FIXTURE
    demo_completed_nodes_are_dev_fixture: bool = True
    demo_completion_is_not_execution: bool = True
    demo_rollback_edge_is_declarative: bool = True
    demo_rollback_edge_does_not_execute: bool = True
    demo_trace_verified: bool = False
    demo_live: bool = False

    def __post_init__(self) -> None:
        for required_true in (
            "demo_completed_nodes_are_dev_fixture",
            "demo_completion_is_not_execution",
            "demo_rollback_edge_is_declarative",
            "demo_rollback_edge_does_not_execute",
        ):
            if not getattr(self, required_true):
                raise AurelFlowValidationError(
                    f"FlowDemoTruthProjection.{required_true} must remain True",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=required_true,
                )
        for required_false in ("demo_trace_verified", "demo_live"):
            if getattr(self, required_false):
                raise AurelFlowValidationError(
                    f"FlowDemoTruthProjection.{required_false} must remain False",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=required_false,
                )


@dataclass(frozen=True)
class FlowDemoScenarioReadModel(_CanonicalMixin):
    """What the DEV_FIXTURE demo scenario actually contains."""

    read_model_version: str
    scenario_name: str
    graph_id: str
    run_id: str
    completed_node_ids: tuple[str, ...]
    failed_node_ids: tuple[str, ...]
    paused_node_ids: tuple[str, ...]
    rollback_candidate_node_ids: tuple[str, ...]
    demo_truth: FlowDemoTruthProjection
    truth_label: FlowTruthLabel
    read_model_hash: str


def build_flow_demo_truth_projection(bundle: FlowDemoBundle) -> FlowDemoTruthProjection:
    return FlowDemoTruthProjection(
        projection_version=FLOW_DEMO_TRUTH_PROJECTION_VERSION,
        graph_id=bundle.graph.graph_id,
        run_id=bundle.run.run_id,
    )


def build_flow_demo_scenario_read_model(
    bundle: FlowDemoBundle,
) -> FlowDemoScenarioReadModel:
    node_states = bundle.run.state.node_states
    completed = tuple(
        sorted(
            node_id
            for node_id, state in node_states.items()
            if state.value == "COMPLETED"
        )
    )
    failed = tuple(
        sorted(
            node_id for node_id, state in node_states.items() if state.value == "FAILED"
        )
    )
    paused = tuple(
        sorted({pause.target_node_id for pause in bundle.pause_states})
    )
    rollback_nodes = tuple(
        sorted({candidate.target_node_id for candidate in bundle.rollback_candidates})
    )
    demo_truth = build_flow_demo_truth_projection(bundle)
    payload = {
        "read_model_version": FLOW_DEMO_TRUTH_PROJECTION_VERSION,
        "graph_id": bundle.graph.graph_id,
        "run_id": bundle.run.run_id,
        "completed": completed,
        "failed": failed,
        "paused": paused,
        "rollback_nodes": rollback_nodes,
    }
    return FlowDemoScenarioReadModel(
        read_model_version=FLOW_DEMO_TRUTH_PROJECTION_VERSION,
        scenario_name="governed-change-behavior-demo",
        graph_id=bundle.graph.graph_id,
        run_id=bundle.run.run_id,
        completed_node_ids=completed,
        failed_node_ids=failed,
        paused_node_ids=paused,
        rollback_candidate_node_ids=rollback_nodes,
        demo_truth=demo_truth,
        truth_label=FlowTruthLabel.DEV_FIXTURE,
        read_model_hash=stable_hash(payload),
    )
