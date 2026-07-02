"""P3-FLOW-F React / Python hybrid projection + migration readiness layer.

Backend-only projection envelopes and view models that a future React /
AurelShell surface may render. No React component, route, frontend state,
API server, REST/WebSocket endpoint, or migration is implemented here.
Python runtime remains the source of truth; React is projection only; a UI
replay/rollback button would execute nothing; migration readiness is not
migration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_checkpoint import (
    RuntimeCheckpointRef,
    RuntimeCheckpointSnapshot,
)
from .flow_replay import (
    CounterfactualReplayCandidate,
    RuntimeForkCandidate,
    RuntimeReplayPlan,
)
from .flow_reversible_state import (
    RecoveryCheckpointRequirement,
    RuntimeRevertCandidate,
    RuntimeStateDiffSummary,
)
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

REVERSIBLE_STATE_PROJECTION_ENVELOPE_VERSION = (
    "reversible_state_projection_envelope.v1"
)
CHECKPOINT_TIMELINE_VIEW_MODEL_VERSION = "checkpoint_timeline_view_model.v1"
REACT_PROJECTION_BOUNDARY_VERSION = "react_projection_boundary.v1"
PYTHON_RUNTIME_SOURCE_OF_TRUTH_VERSION = "python_runtime_source_of_truth.v1"
HYBRID_SERIALIZATION_CONTRACT_VERSION = "hybrid_serialization_contract.v1"
REVERSIBLE_STATE_MIGRATION_READINESS_VERSION = (
    "reversible_state_migration_readiness.v1"
)
PROJECTION_COMPATIBILITY_READ_MODEL_VERSION = (
    "projection_compatibility_read_model.v1"
)
MIGRATION_PROJECTION_READINESS_MATRIX_VERSION = (
    "migration_projection_readiness_matrix.v1"
)

FRONTEND_UNAVAILABLE_REASON = (
    "no React component, frontend route, frontend state, API server, REST "
    "endpoint, or WebSocket endpoint is implemented in P3-FLOW-F; view "
    "models are backend read models for a future projection surface only"
)
REVERSIBLE_MIGRATION_UNAVAILABLE_REASON = (
    "migration readiness metadata is not migration: no persistence, Rust/Go, "
    "generated-schema, or external-store migration is started or performed"
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


class ReversibleStateReadinessStatus(str, Enum):
    """Honest readiness statuses. Readiness is not implementation."""

    PYTHON_SOURCE_OF_TRUTH = "PYTHON_SOURCE_OF_TRUTH"
    REACT_PROJECTION_READY = "REACT_PROJECTION_READY"
    API_CONTRACT_READY = "API_CONTRACT_READY"
    SCHEMA_VERSIONED = "SCHEMA_VERSIONED"
    SERIALIZATION_READY = "SERIALIZATION_READY"
    PERSISTENCE_UNAVAILABLE = "PERSISTENCE_UNAVAILABLE"
    FRONTEND_NOT_IMPLEMENTED = "FRONTEND_NOT_IMPLEMENTED"
    MIGRATION_NOT_STARTED = "MIGRATION_NOT_STARTED"
    RUST_CORE_NOT_ACTIVE = "RUST_CORE_NOT_ACTIVE"
    EXTERNAL_STORE_NOT_ACTIVE = "EXTERNAL_STORE_NOT_ACTIVE"


# ---------------------------------------------------------------------------
# View models (future React rendering only; nothing renders here)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckpointTimelineEntryViewModel(_CanonicalMixin):
    """One row of a future checkpoint timeline. Display data only."""

    sequence: int
    entry_kind: str
    ref_id: str
    label: str
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "projection_only")


@dataclass(frozen=True)
class CheckpointTimelineViewModel(_CanonicalMixin):
    """Future React checkpoint timeline. Projection only; renders nothing."""

    view_model_version: str
    run_id: str
    entries: tuple[CheckpointTimelineEntryViewModel, ...]
    truth_label: FlowTruthLabel
    view_model_hash: str
    projection_only: bool = True
    mutation_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "projection_only")
        _forbid_true(self, "mutation_available")


def build_checkpoint_timeline_view_model(
    *, run_id: str, entries: tuple[CheckpointTimelineEntryViewModel, ...] = ()
) -> CheckpointTimelineViewModel:
    payload = {
        "view_model_version": CHECKPOINT_TIMELINE_VIEW_MODEL_VERSION,
        "run_id": run_id,
        "entry_refs": tuple(entry.ref_id for entry in entries),
    }
    return CheckpointTimelineViewModel(
        view_model_version=CHECKPOINT_TIMELINE_VIEW_MODEL_VERSION,
        run_id=run_id,
        entries=entries,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        view_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class CheckpointSnapshotViewModel(_CanonicalMixin):
    """Display projection of one checkpoint snapshot."""

    snapshot_id: str
    run_id: str
    workflow_state_step: int
    event_count: int
    node_state_count: int
    commitment_count: int
    truth_label: FlowTruthLabel
    projection_only: bool = True
    mutation_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "projection_only")
        _forbid_true(self, "mutation_available")


def build_checkpoint_snapshot_view_model(
    snapshot: RuntimeCheckpointSnapshot,
) -> CheckpointSnapshotViewModel:
    return CheckpointSnapshotViewModel(
        snapshot_id=snapshot.snapshot_id,
        run_id=snapshot.run_id,
        workflow_state_step=snapshot.workflow_state_step,
        event_count=snapshot.event_count,
        node_state_count=snapshot.node_state_count,
        commitment_count=snapshot.commitment_count,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class ForkCandidateViewModel(_CanonicalMixin):
    """Display projection of one fork candidate."""

    fork_candidate_id: str
    run_id: str
    branch_label: str
    fork_reason: str
    truth_label: FlowTruthLabel
    requires_operator_review: bool = True
    execution_available: bool = False
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "requires_operator_review", "projection_only")
        _forbid_true(self, "execution_available")


def build_fork_candidate_view_model(
    candidate: RuntimeForkCandidate,
) -> ForkCandidateViewModel:
    return ForkCandidateViewModel(
        fork_candidate_id=candidate.fork_candidate_id,
        run_id=candidate.run_id,
        branch_label=candidate.branch_label,
        fork_reason=candidate.fork_reason.value,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class ReplayPlanViewModel(_CanonicalMixin):
    """Display projection of one replay plan. A UI button executes nothing."""

    replay_plan_id: str
    run_id: str
    replay_mode: str
    availability: str
    included_event_count: int
    truth_label: FlowTruthLabel
    ui_replay_button_executes: bool = False
    execution_available: bool = False
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "projection_only")
        _forbid_true(self, "ui_replay_button_executes", "execution_available")


def build_replay_plan_view_model(plan: RuntimeReplayPlan) -> ReplayPlanViewModel:
    return ReplayPlanViewModel(
        replay_plan_id=plan.replay_plan_id,
        run_id=plan.run_id,
        replay_mode=plan.replay_mode.value,
        availability=plan.availability.value,
        included_event_count=len(plan.included_event_ids),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class CounterfactualBranchViewModel(_CanonicalMixin):
    """Display projection of one counterfactual branch."""

    counterfactual_candidate_id: str
    run_id: str
    branch_reason: str
    branch_label: str
    truth_label: FlowTruthLabel
    actual_history: bool = False
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "projection_only")
        _forbid_true(self, "actual_history")


def build_counterfactual_branch_view_model(
    candidate: CounterfactualReplayCandidate,
) -> CounterfactualBranchViewModel:
    return CounterfactualBranchViewModel(
        counterfactual_candidate_id=candidate.counterfactual_candidate_id,
        run_id=candidate.run_id,
        branch_reason=candidate.branch_reason.value,
        branch_label=candidate.branch_label,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class RevertCandidateViewModel(_CanonicalMixin):
    """Display projection of one revert candidate. A UI button rolls back nothing."""

    revert_candidate_id: str
    run_id: str
    target_checkpoint_id: str
    external_side_effects_present: bool
    truth_label: FlowTruthLabel
    safe_to_execute: bool = False
    ui_rollback_button_executes: bool = False
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "projection_only")
        _forbid_true(self, "safe_to_execute", "ui_rollback_button_executes")


def build_revert_candidate_view_model(
    candidate: RuntimeRevertCandidate,
) -> RevertCandidateViewModel:
    return RevertCandidateViewModel(
        revert_candidate_id=candidate.revert_candidate_id,
        run_id=candidate.affected_run_id,
        target_checkpoint_id=candidate.target_checkpoint_id,
        external_side_effects_present=candidate.external_side_effects_present,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class RuntimeDiffViewModel(_CanonicalMixin):
    """Display projection of one runtime diff."""

    diff_id: str
    left_checkpoint_id: str
    right_checkpoint_id: str
    diff_summary: str
    truth_label: FlowTruthLabel
    diff_is_not_proof: bool = True
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "diff_is_not_proof", "projection_only")


def build_runtime_diff_view_model(diff: RuntimeStateDiffSummary) -> RuntimeDiffViewModel:
    return RuntimeDiffViewModel(
        diff_id=diff.diff_id,
        left_checkpoint_id=diff.left_checkpoint_id,
        right_checkpoint_id=diff.right_checkpoint_id,
        diff_summary=diff.diff_summary,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class RecoveryCheckpointRequirementViewModel(_CanonicalMixin):
    """Display projection of one recovery checkpoint requirement."""

    requirement_id: str
    run_id: str
    required_checkpoint_kind: str
    truth_label: FlowTruthLabel
    pre_recovery_checkpoint_required: bool = True
    recovery_executed: bool = False
    projection_only: bool = True

    def __post_init__(self) -> None:
        _forbid_false(self, "pre_recovery_checkpoint_required", "projection_only")
        _forbid_true(self, "recovery_executed")


def build_recovery_checkpoint_requirement_view_model(
    requirement: RecoveryCheckpointRequirement,
) -> RecoveryCheckpointRequirementViewModel:
    return RecoveryCheckpointRequirementViewModel(
        requirement_id=requirement.requirement_id,
        run_id=requirement.run_id,
        required_checkpoint_kind=requirement.required_checkpoint_kind.value,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


# ---------------------------------------------------------------------------
# Projection envelope + hybrid / migration readiness contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReversibleStateProjectionEnvelope(_CanonicalMixin):
    """Everything a future React/AurelShell surface may render, read-only."""

    envelope_id: str
    contract_version: str
    schema_version: str
    run_id: str
    checkpoint_refs: tuple[RuntimeCheckpointRef, ...]
    checkpoint_snapshots: tuple[RuntimeCheckpointSnapshot, ...]
    fork_candidates: tuple[RuntimeForkCandidate, ...]
    replay_plans: tuple[RuntimeReplayPlan, ...]
    counterfactual_candidates: tuple[CounterfactualReplayCandidate, ...]
    revert_candidates: tuple[RuntimeRevertCandidate, ...]
    runtime_diffs: tuple[RuntimeStateDiffSummary, ...]
    recovery_checkpoint_requirements: tuple[RecoveryCheckpointRequirement, ...]
    truth_label: FlowTruthLabel
    envelope_hash: str
    unavailable_reasons: Mapping[str, str] = field(default_factory=dict)
    read_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_authority_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "read_only")
        _forbid_true(self, "frontend_mutation_allowed", "ui_authority_granted")


def build_reversible_state_projection_envelope(
    *,
    run_id: str,
    checkpoint_refs: tuple[RuntimeCheckpointRef, ...] = (),
    checkpoint_snapshots: tuple[RuntimeCheckpointSnapshot, ...] = (),
    fork_candidates: tuple[RuntimeForkCandidate, ...] = (),
    replay_plans: tuple[RuntimeReplayPlan, ...] = (),
    counterfactual_candidates: tuple[CounterfactualReplayCandidate, ...] = (),
    revert_candidates: tuple[RuntimeRevertCandidate, ...] = (),
    runtime_diffs: tuple[RuntimeStateDiffSummary, ...] = (),
    recovery_checkpoint_requirements: tuple[RecoveryCheckpointRequirement, ...] = (),
) -> ReversibleStateProjectionEnvelope:
    payload = {
        "contract_version": REVERSIBLE_STATE_PROJECTION_ENVELOPE_VERSION,
        "run_id": run_id,
        "checkpoint_ids": tuple(ref.checkpoint_id for ref in checkpoint_refs),
        "snapshot_ids": tuple(s.snapshot_id for s in checkpoint_snapshots),
        "fork_candidate_ids": tuple(c.fork_candidate_id for c in fork_candidates),
        "replay_plan_ids": tuple(p.replay_plan_id for p in replay_plans),
        "counterfactual_ids": tuple(
            c.counterfactual_candidate_id for c in counterfactual_candidates
        ),
        "revert_candidate_ids": tuple(
            c.revert_candidate_id for c in revert_candidates
        ),
        "diff_ids": tuple(d.diff_id for d in runtime_diffs),
        "requirement_ids": tuple(
            r.requirement_id for r in recovery_checkpoint_requirements
        ),
    }
    return ReversibleStateProjectionEnvelope(
        envelope_id="flrse-" + stable_hash(payload)[:16],
        contract_version=REVERSIBLE_STATE_PROJECTION_ENVELOPE_VERSION,
        schema_version="v1",
        run_id=run_id,
        checkpoint_refs=checkpoint_refs,
        checkpoint_snapshots=checkpoint_snapshots,
        fork_candidates=fork_candidates,
        replay_plans=replay_plans,
        counterfactual_candidates=counterfactual_candidates,
        revert_candidates=revert_candidates,
        runtime_diffs=runtime_diffs,
        recovery_checkpoint_requirements=recovery_checkpoint_requirements,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        envelope_hash=stable_hash(payload),
        unavailable_reasons={
            "frontend": FRONTEND_UNAVAILABLE_REASON,
            "migration": REVERSIBLE_MIGRATION_UNAVAILABLE_REASON,
        },
    )


@dataclass(frozen=True)
class ReactProjectionBoundary(_CanonicalMixin):
    """The React law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = FRONTEND_UNAVAILABLE_REASON
    react_projection_only: bool = True
    future_react_required_for_display_only: bool = True
    frontend_mutation_allowed: bool = False
    ui_authority_granted: bool = False
    ui_replay_execution_allowed: bool = False
    ui_rollback_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "react_projection_only", "future_react_required_for_display_only"
        )
        _forbid_true(
            self,
            "frontend_mutation_allowed",
            "ui_authority_granted",
            "ui_replay_execution_allowed",
            "ui_rollback_execution_allowed",
        )


def build_react_projection_boundary() -> ReactProjectionBoundary:
    payload = {"boundary_version": REACT_PROJECTION_BOUNDARY_VERSION}
    return ReactProjectionBoundary(
        boundary_version=REACT_PROJECTION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class PythonRuntimeSourceOfTruth(_CanonicalMixin):
    """Python runtime is the P3 source of truth. React never owns state."""

    contract_version: str
    truth_label: FlowTruthLabel
    contract_hash: str
    runtime_source_of_truth: str = "python"
    python_owns_runtime_state: bool = True
    react_owns_runtime_state: bool = False
    react_is_projection_only: bool = True

    def __post_init__(self) -> None:
        if self.runtime_source_of_truth != "python":
            raise AurelFlowValidationError(
                "runtime_source_of_truth must remain 'python' in P3",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="runtime_source_of_truth",
            )
        _forbid_false(self, "python_owns_runtime_state", "react_is_projection_only")
        _forbid_true(self, "react_owns_runtime_state")


def build_python_runtime_source_of_truth() -> PythonRuntimeSourceOfTruth:
    payload = {"contract_version": PYTHON_RUNTIME_SOURCE_OF_TRUTH_VERSION}
    return PythonRuntimeSourceOfTruth(
        contract_version=PYTHON_RUNTIME_SOURCE_OF_TRUTH_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        contract_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class HybridSerializationContract(_CanonicalMixin):
    """Versioned serialization posture for future projection/API compatibility.

    API contract readiness is not an API server; schema versioning is not
    generated schema tooling.
    """

    contract_id: str
    contract_version: str
    schema_name: str
    schema_version: str
    truth_label: FlowTruthLabel
    contract_hash: str
    unavailable_reason: str = FRONTEND_UNAVAILABLE_REASON
    deterministic_serialization: bool = True
    stable_ids_required: bool = True
    canonical_json: bool = True
    api_contract_ready: bool = True
    api_server_implemented: bool = False
    generated_schema_tooling: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "deterministic_serialization",
            "stable_ids_required",
            "canonical_json",
        )
        _forbid_true(self, "api_server_implemented", "generated_schema_tooling")


def build_hybrid_serialization_contract(
    *,
    schema_name: str = "aurel_flow.reversible_state",
    schema_version: str = "v1",
) -> HybridSerializationContract:
    payload = {
        "contract_version": HYBRID_SERIALIZATION_CONTRACT_VERSION,
        "schema_name": schema_name,
        "schema_version": schema_version,
    }
    return HybridSerializationContract(
        contract_id="flhsc-" + stable_hash(payload)[:16],
        contract_version=HYBRID_SERIALIZATION_CONTRACT_VERSION,
        schema_name=schema_name,
        schema_version=schema_version,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        contract_hash=stable_hash(payload),
    )


DEFAULT_REVERSIBLE_STATE_READINESS_STATUSES: tuple[
    ReversibleStateReadinessStatus, ...
] = (
    ReversibleStateReadinessStatus.PYTHON_SOURCE_OF_TRUTH,
    ReversibleStateReadinessStatus.REACT_PROJECTION_READY,
    ReversibleStateReadinessStatus.API_CONTRACT_READY,
    ReversibleStateReadinessStatus.SCHEMA_VERSIONED,
    ReversibleStateReadinessStatus.SERIALIZATION_READY,
    ReversibleStateReadinessStatus.PERSISTENCE_UNAVAILABLE,
    ReversibleStateReadinessStatus.FRONTEND_NOT_IMPLEMENTED,
    ReversibleStateReadinessStatus.MIGRATION_NOT_STARTED,
    ReversibleStateReadinessStatus.RUST_CORE_NOT_ACTIVE,
    ReversibleStateReadinessStatus.EXTERNAL_STORE_NOT_ACTIVE,
)


@dataclass(frozen=True)
class ReversibleStateMigrationReadiness(_CanonicalMixin):
    """Migration readiness metadata. Readiness is not migration."""

    readiness_id: str
    readiness_version: str
    statuses: tuple[ReversibleStateReadinessStatus, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = REVERSIBLE_MIGRATION_UNAVAILABLE_REASON
    migration_started: bool = False
    frontend_implemented: bool = False
    rust_core_active: bool = False
    external_store_active: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "migration_started",
            "frontend_implemented",
            "rust_core_active",
            "external_store_active",
        )


def build_reversible_state_migration_readiness() -> ReversibleStateMigrationReadiness:
    payload = {
        "readiness_version": REVERSIBLE_STATE_MIGRATION_READINESS_VERSION,
        "statuses": tuple(
            status.value for status in DEFAULT_REVERSIBLE_STATE_READINESS_STATUSES
        ),
    }
    return ReversibleStateMigrationReadiness(
        readiness_id="flmrr-" + stable_hash(payload)[:16],
        readiness_version=REVERSIBLE_STATE_MIGRATION_READINESS_VERSION,
        statuses=DEFAULT_REVERSIBLE_STATE_READINESS_STATUSES,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class ProjectionCompatibilityReadModel(_CanonicalMixin):
    """Deterministic projection-compatibility summary. Projection only."""

    read_model_version: str
    envelope_id: str
    view_model_count: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    all_view_models_projection_only: bool = True
    frontend_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "all_view_models_projection_only")
        _forbid_true(self, "frontend_mutation_allowed")


def build_projection_compatibility_read_model(
    envelope: ReversibleStateProjectionEnvelope, *, view_model_count: int = 0
) -> ProjectionCompatibilityReadModel:
    payload = {
        "read_model_version": PROJECTION_COMPATIBILITY_READ_MODEL_VERSION,
        "envelope_hash": envelope.envelope_hash,
        "view_model_count": view_model_count,
    }
    return ProjectionCompatibilityReadModel(
        read_model_version=PROJECTION_COMPATIBILITY_READ_MODEL_VERSION,
        envelope_id=envelope.envelope_id,
        view_model_count=view_model_count,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


DEFAULT_MIGRATION_PROJECTION_READINESS_ROWS: Mapping[str, str] = {
    "python_runtime": ReversibleStateReadinessStatus.PYTHON_SOURCE_OF_TRUTH.value,
    "react_projection": ReversibleStateReadinessStatus.REACT_PROJECTION_READY.value,
    "api_contract": ReversibleStateReadinessStatus.API_CONTRACT_READY.value,
    "schema": ReversibleStateReadinessStatus.SCHEMA_VERSIONED.value,
    "serialization": ReversibleStateReadinessStatus.SERIALIZATION_READY.value,
    "persistence": ReversibleStateReadinessStatus.PERSISTENCE_UNAVAILABLE.value,
    "frontend": ReversibleStateReadinessStatus.FRONTEND_NOT_IMPLEMENTED.value,
    "migration": ReversibleStateReadinessStatus.MIGRATION_NOT_STARTED.value,
    "rust_core": ReversibleStateReadinessStatus.RUST_CORE_NOT_ACTIVE.value,
    "external_store": ReversibleStateReadinessStatus.EXTERNAL_STORE_NOT_ACTIVE.value,
}


@dataclass(frozen=True)
class MigrationProjectionReadinessMatrix(_CanonicalMixin):
    """Per-surface readiness matrix. Marking readiness migrates nothing."""

    matrix_id: str
    matrix_version: str
    rows: Mapping[str, str]
    truth_label: FlowTruthLabel
    matrix_hash: str
    unavailable_reason: str = REVERSIBLE_MIGRATION_UNAVAILABLE_REASON
    python_source_of_truth: bool = True
    migration_started: bool = False
    api_server_implemented: bool = False
    frontend_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "python_source_of_truth")
        _forbid_true(
            self,
            "migration_started",
            "api_server_implemented",
            "frontend_implemented",
        )


def build_migration_projection_readiness_matrix() -> MigrationProjectionReadinessMatrix:
    rows = dict(DEFAULT_MIGRATION_PROJECTION_READINESS_ROWS)
    payload = {
        "matrix_version": MIGRATION_PROJECTION_READINESS_MATRIX_VERSION,
        "rows": rows,
    }
    return MigrationProjectionReadinessMatrix(
        matrix_id="flmpm-" + stable_hash(payload)[:16],
        matrix_version=MIGRATION_PROJECTION_READINESS_MATRIX_VERSION,
        rows=rows,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        matrix_hash=stable_hash(payload),
    )
