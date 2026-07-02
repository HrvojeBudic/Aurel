"""P3-FLOW-F fork candidate / replay plan / counterfactual layer
(P3.14.10-P3.14.19).

A fork candidate is a conceptual branch from a checkpoint — it never spawns a
worker and never duplicates external state. A replay plan is replay intent
only: nothing here re-runs events, and a replay cursor is a read-model
position marker, never a worker cursor. A counterfactual replay candidate is
an analysis branch: it is structurally forbidden from claiming it is actual
history or proof. Actual replay execution belongs to P4 AurelExec; verified
replay belongs to P5 AurelTrace; authority belongs to P9 Custos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_checkpoint import RuntimeCheckpointRef, RuntimeCheckpointSnapshot
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

RUNTIME_FORK_CANDIDATE_VERSION = "runtime_fork_candidate.v1"
RUNTIME_FORK_BOUNDARY_VERSION = "runtime_fork_boundary.v1"
FORK_SAFETY_FRAME_VERSION = "fork_safety_frame.v1"
RUNTIME_FORK_READ_MODEL_VERSION = "runtime_fork_read_model.v1"
RUNTIME_REPLAY_PLAN_VERSION = "runtime_replay_plan.v1"
RUNTIME_REPLAY_CURSOR_VERSION = "runtime_replay_cursor.v1"
REPLAY_BOUNDARY_VERSION = "replay_boundary.v1"
REPLAY_READ_MODEL_VERSION = "replay_read_model.v1"
COUNTERFACTUAL_REPLAY_CANDIDATE_VERSION = "counterfactual_replay_candidate.v1"
COUNTERFACTUAL_COMPARISON_FRAME_VERSION = "counterfactual_comparison_frame.v1"
COUNTERFACTUAL_TRUTH_BOUNDARY_VERSION = "counterfactual_truth_boundary.v1"
COUNTERFACTUAL_REPLAY_READ_MODEL_VERSION = "counterfactual_replay_read_model.v1"

FORK_EXECUTION_UNAVAILABLE_REASON = (
    "a fork candidate is a conceptual branch record only; no worker is "
    "spawned and no external state is duplicated — execution belongs to "
    "P4 AurelExec and authority belongs to P9 Custos"
)
REPLAY_EXECUTION_UNAVAILABLE_REASON = (
    "a replay plan is replay intent only; nothing re-runs events in "
    "P3-FLOW-F — replay execution belongs to P4 AurelExec and verified "
    "replay belongs to P5 AurelTrace"
)
COUNTERFACTUAL_PROOF_UNAVAILABLE_REASON = (
    "a counterfactual replay candidate is an analysis branch, never actual "
    "history and never proof; the evidence spine belongs to P5 AurelTrace"
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


# ---------------------------------------------------------------------------
# Fork candidates (P3.14.10-P3.14.14)
# ---------------------------------------------------------------------------


class RuntimeForkReason(str, Enum):
    """Why a conceptual branch was named. Naming spawns nothing."""

    RECOVERY_EXPLORATION = "RECOVERY_EXPLORATION"
    COUNTERFACTUAL_REPLAY = "COUNTERFACTUAL_REPLAY"
    OPERATOR_REVIEW_ALTERNATIVE = "OPERATOR_REVIEW_ALTERNATIVE"
    GRAPH_REVISION_ALTERNATIVE = "GRAPH_REVISION_ALTERNATIVE"
    VERIFIER_REQUESTED_BRANCH = "VERIFIER_REQUESTED_BRANCH"
    EVIDENCE_REQUIRED_BRANCH = "EVIDENCE_REQUIRED_BRANCH"
    BUDGET_SAFE_BRANCH = "BUDGET_SAFE_BRANCH"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class RuntimeForkCandidate(_CanonicalMixin):
    """Conceptual branch from a checkpoint/snapshot. Not a live branch."""

    fork_candidate_id: str
    contract_version: str
    source_checkpoint_id: str
    source_snapshot_id: str
    run_id: str
    fork_reason: RuntimeForkReason
    branch_label: str
    expected_divergence_point: str
    truth_label: FlowTruthLabel
    topology_snapshot_id: str = ""
    unavailable_reason: str = FORK_EXECUTION_UNAVAILABLE_REASON
    requires_operator_review: bool = True
    requires_permission: bool = True
    requires_future_p4_execution: bool = True
    requires_future_p5_proof: bool = True
    requires_future_p9_authority: bool = True
    worker_spawned: bool = False
    external_state_duplicated: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_operator_review",
            "requires_permission",
            "requires_future_p4_execution",
            "requires_future_p5_proof",
            "requires_future_p9_authority",
        )
        _forbid_true(
            self,
            "worker_spawned",
            "external_state_duplicated",
            "execution_available",
        )


def create_runtime_fork_candidate(
    *,
    checkpoint_ref: RuntimeCheckpointRef,
    snapshot: RuntimeCheckpointSnapshot,
    fork_reason: RuntimeForkReason,
    branch_label: str,
    expected_divergence_point: str = "",
) -> RuntimeForkCandidate:
    """Name a conceptual branch. No worker spawns; no state is duplicated."""

    if snapshot.checkpoint_ref_id != checkpoint_ref.checkpoint_id:
        raise AurelFlowValidationError(
            f"snapshot checkpoint {snapshot.checkpoint_ref_id!r} does not "
            f"match checkpoint {checkpoint_ref.checkpoint_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="snapshot",
        )
    payload = {
        "contract_version": RUNTIME_FORK_CANDIDATE_VERSION,
        "source_checkpoint_id": checkpoint_ref.checkpoint_id,
        "source_snapshot_id": snapshot.snapshot_id,
        "run_id": checkpoint_ref.run_id,
        "fork_reason": fork_reason.value,
        "branch_label": branch_label,
        "expected_divergence_point": expected_divergence_point,
    }
    return RuntimeForkCandidate(
        fork_candidate_id="flfkc-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_FORK_CANDIDATE_VERSION,
        source_checkpoint_id=checkpoint_ref.checkpoint_id,
        source_snapshot_id=snapshot.snapshot_id,
        run_id=checkpoint_ref.run_id,
        fork_reason=fork_reason,
        branch_label=branch_label,
        expected_divergence_point=expected_divergence_point,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        topology_snapshot_id=snapshot.topology_snapshot_id,
    )


@dataclass(frozen=True)
class RuntimeForkBoundary(_CanonicalMixin):
    """The fork law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = FORK_EXECUTION_UNAVAILABLE_REASON
    fork_is_not_execution: bool = True
    fork_spawns_worker: bool = False
    fork_duplicates_external_state: bool = False
    fork_grants_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "fork_is_not_execution")
        _forbid_true(
            self,
            "fork_spawns_worker",
            "fork_duplicates_external_state",
            "fork_grants_authority",
        )


def build_runtime_fork_boundary() -> RuntimeForkBoundary:
    payload = {"boundary_version": RUNTIME_FORK_BOUNDARY_VERSION}
    return RuntimeForkBoundary(
        boundary_version=RUNTIME_FORK_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ForkSafetyFrame(_CanonicalMixin):
    """Safety posture of one fork candidate. Never a permission grant."""

    frame_id: str
    frame_version: str
    fork_candidate_id: str
    run_id: str
    truth_label: FlowTruthLabel
    requires_operator_review: bool = True
    requires_future_p4_execution: bool = True
    requires_future_p5_proof: bool = True
    requires_future_p9_authority: bool = True
    safe_to_execute: bool = False
    worker_spawned: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_operator_review",
            "requires_future_p4_execution",
            "requires_future_p5_proof",
            "requires_future_p9_authority",
        )
        _forbid_true(self, "safe_to_execute", "worker_spawned")


def build_fork_safety_frame(candidate: RuntimeForkCandidate) -> ForkSafetyFrame:
    payload = {
        "frame_version": FORK_SAFETY_FRAME_VERSION,
        "fork_candidate_id": candidate.fork_candidate_id,
    }
    return ForkSafetyFrame(
        frame_id="flfsf-" + stable_hash(payload)[:16],
        frame_version=FORK_SAFETY_FRAME_VERSION,
        fork_candidate_id=candidate.fork_candidate_id,
        run_id=candidate.run_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RuntimeForkReadModel(_CanonicalMixin):
    """Deterministic fork-candidate projection. Fork is not execution."""

    read_model_version: str
    fork_candidate_ids: tuple[str, ...]
    fork_reason_counts: Mapping[str, int]
    truth_label: FlowTruthLabel
    read_model_hash: str
    fork_is_not_execution: bool = True
    worker_spawned: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "fork_is_not_execution")
        _forbid_true(self, "worker_spawned")


def build_runtime_fork_read_model(
    candidates: tuple[RuntimeForkCandidate, ...] = (),
) -> RuntimeForkReadModel:
    reason_counts: dict[str, int] = {}
    for candidate in candidates:
        key = candidate.fork_reason.value
        reason_counts[key] = reason_counts.get(key, 0) + 1
    payload = {
        "read_model_version": RUNTIME_FORK_READ_MODEL_VERSION,
        "fork_candidate_ids": tuple(c.fork_candidate_id for c in candidates),
    }
    return RuntimeForkReadModel(
        read_model_version=RUNTIME_FORK_READ_MODEL_VERSION,
        fork_candidate_ids=tuple(c.fork_candidate_id for c in candidates),
        fork_reason_counts=reason_counts,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Replay plans / cursors (P3.14.15-P3.14.19)
# ---------------------------------------------------------------------------


class ReplayMode(str, Enum):
    """What kind of replay is intended. Every member is intent, not execution."""

    READ_MODEL_REPLAY = "READ_MODEL_REPLAY"
    EVENT_SEQUENCE_REPLAY = "EVENT_SEQUENCE_REPLAY"
    COUNTERFACTUAL_REPLAY_CANDIDATE = "COUNTERFACTUAL_REPLAY_CANDIDATE"
    DIAGNOSTIC_REPLAY_CANDIDATE = "DIAGNOSTIC_REPLAY_CANDIDATE"
    RECOVERY_REPLAY_CANDIDATE = "RECOVERY_REPLAY_CANDIDATE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ReplayAvailability(str, Enum):
    """What a replay plan can honestly claim in P3.

    Deliberately closed-world: there is no EXECUTABLE and no LIVE member, so
    a replay plan structurally cannot claim executable replay.
    """

    PLAN_ONLY = "PLAN_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ReplayStepRef(_CanonicalMixin):
    """One planned replay step. A step reference re-runs nothing."""

    step_index: int
    event_id: str
    node_id: str = ""
    description: str = ""


@dataclass(frozen=True)
class RuntimeReplayPlan(_CanonicalMixin):
    """Replay intent over a checkpoint's event window. Never replay execution."""

    replay_plan_id: str
    contract_version: str
    run_id: str
    start_checkpoint_id: str
    replay_mode: ReplayMode
    availability: ReplayAvailability
    included_event_ids: tuple[str, ...]
    excluded_event_ids: tuple[str, ...]
    steps: tuple[ReplayStepRef, ...]
    truth_label: FlowTruthLabel
    plan_hash: str
    target_event_id: str = ""
    expected_state_hash: str = ""
    expected_topology_version_number: int = 0
    unavailable_reason: str = REPLAY_EXECUTION_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    requires_trace_verification: bool = True
    requires_operator_review: bool = True
    requires_p4_execution: bool = True
    requires_p5_proof: bool = True
    execution_available: bool = False
    worker_cursor_available: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_trace_verification",
            "requires_operator_review",
            "requires_p4_execution",
            "requires_p5_proof",
        )
        _forbid_true(
            self,
            "execution_available",
            "worker_cursor_available",
            "proof_available",
        )


def create_runtime_replay_plan(
    *,
    checkpoint_ref: RuntimeCheckpointRef,
    replay_mode: ReplayMode,
    included_event_ids: tuple[str, ...] = (),
    excluded_event_ids: tuple[str, ...] = (),
    target_event_id: str = "",
    expected_state_hash: str = "",
    expected_topology_version_number: int = 0,
    metadata: Mapping[str, str] | None = None,
) -> RuntimeReplayPlan:
    """Plan a replay window deterministically. Nothing re-runs."""

    steps = tuple(
        ReplayStepRef(step_index=index, event_id=event_id)
        for index, event_id in enumerate(included_event_ids)
    )
    payload = {
        "contract_version": RUNTIME_REPLAY_PLAN_VERSION,
        "run_id": checkpoint_ref.run_id,
        "start_checkpoint_id": checkpoint_ref.checkpoint_id,
        "replay_mode": replay_mode.value,
        "included_event_ids": included_event_ids,
        "excluded_event_ids": excluded_event_ids,
        "target_event_id": target_event_id,
    }
    return RuntimeReplayPlan(
        replay_plan_id="flrpl-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_REPLAY_PLAN_VERSION,
        run_id=checkpoint_ref.run_id,
        start_checkpoint_id=checkpoint_ref.checkpoint_id,
        replay_mode=replay_mode,
        availability=ReplayAvailability.PLAN_ONLY,
        included_event_ids=included_event_ids,
        excluded_event_ids=excluded_event_ids,
        steps=steps,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        plan_hash=stable_hash(payload),
        target_event_id=target_event_id,
        expected_state_hash=expected_state_hash,
        expected_topology_version_number=expected_topology_version_number,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class RuntimeReplayCursor(_CanonicalMixin):
    """Read-model position marker inside a replay plan. Not a worker cursor."""

    cursor_id: str
    contract_version: str
    replay_plan_id: str
    run_id: str
    position_index: int
    current_event_id: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = REPLAY_EXECUTION_UNAVAILABLE_REASON
    is_worker_cursor: bool = False
    advances_execution: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_worker_cursor", "advances_execution")


def create_runtime_replay_cursor(
    plan: RuntimeReplayPlan, *, position_index: int = 0
) -> RuntimeReplayCursor:
    """Mark a read-model position in a plan. Moving a marker executes nothing."""

    if position_index < 0 or position_index > len(plan.included_event_ids):
        raise AurelFlowValidationError(
            f"position_index {position_index} is outside the plan window of "
            f"{len(plan.included_event_ids)} included events",
            code=AurelFlowErrorCode.UNKNOWN_EVENT_REF,
            field="position_index",
        )
    current_event_id = (
        plan.included_event_ids[position_index]
        if position_index < len(plan.included_event_ids)
        else ""
    )
    payload = {
        "contract_version": RUNTIME_REPLAY_CURSOR_VERSION,
        "replay_plan_id": plan.replay_plan_id,
        "position_index": position_index,
    }
    return RuntimeReplayCursor(
        cursor_id="flrpc-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_REPLAY_CURSOR_VERSION,
        replay_plan_id=plan.replay_plan_id,
        run_id=plan.run_id,
        position_index=position_index,
        current_event_id=current_event_id,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class ReplayBoundary(_CanonicalMixin):
    """The replay law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = REPLAY_EXECUTION_UNAVAILABLE_REASON
    replay_plan_is_not_execution: bool = True
    replay_cursor_is_not_worker_cursor: bool = True
    read_model_replay_is_not_trace_replay: bool = True
    replay_executes: bool = False
    replay_proves: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "replay_plan_is_not_execution",
            "replay_cursor_is_not_worker_cursor",
            "read_model_replay_is_not_trace_replay",
        )
        _forbid_true(self, "replay_executes", "replay_proves")


def build_replay_boundary() -> ReplayBoundary:
    payload = {"boundary_version": REPLAY_BOUNDARY_VERSION}
    return ReplayBoundary(
        boundary_version=REPLAY_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class ReplayReadModel(_CanonicalMixin):
    """Deterministic replay-plan projection. Plans only, never executions."""

    read_model_version: str
    replay_plan_ids: tuple[str, ...]
    replay_mode_counts: Mapping[str, int]
    truth_label: FlowTruthLabel
    read_model_hash: str
    replay_is_plan_only: bool = True
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "replay_is_plan_only")
        _forbid_true(self, "execution_available")


def build_replay_read_model(
    plans: tuple[RuntimeReplayPlan, ...] = (),
) -> ReplayReadModel:
    mode_counts: dict[str, int] = {}
    for plan in plans:
        key = plan.replay_mode.value
        mode_counts[key] = mode_counts.get(key, 0) + 1
    payload = {
        "read_model_version": REPLAY_READ_MODEL_VERSION,
        "replay_plan_ids": tuple(plan.replay_plan_id for plan in plans),
    }
    return ReplayReadModel(
        read_model_version=REPLAY_READ_MODEL_VERSION,
        replay_plan_ids=tuple(plan.replay_plan_id for plan in plans),
        replay_mode_counts=mode_counts,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Counterfactual replay (P3.14.15-P3.14.19)
# ---------------------------------------------------------------------------


class CounterfactualBranchReason(str, Enum):
    """Why an alternative branch is being analyzed. Analysis is not history."""

    DIAGNOSIS = "DIAGNOSIS"
    OPERATOR_WHAT_IF = "OPERATOR_WHAT_IF"
    RECOVERY_PLANNING = "RECOVERY_PLANNING"
    GRAPH_REVISION_COMPARISON = "GRAPH_REVISION_COMPARISON"
    VERIFIER_PLACEMENT_ANALYSIS = "VERIFIER_PLACEMENT_ANALYSIS"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class CounterfactualReplayCandidate(_CanonicalMixin):
    """Alternative branch for analysis. Structurally never actual history."""

    counterfactual_candidate_id: str
    contract_version: str
    source_checkpoint_id: str
    run_id: str
    branch_reason: CounterfactualBranchReason
    branch_label: str
    truth_label: FlowTruthLabel
    source_topology_snapshot_id: str = ""
    alternative_revision_proposal_id: str = ""
    alternative_operator_decision_id: str = ""
    unavailable_reason: str = COUNTERFACTUAL_PROOF_UNAVAILABLE_REASON
    counterfactual: bool = True
    actual_history: bool = False
    trace_verified: bool = False
    proof_available: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "counterfactual")
        _forbid_true(
            self,
            "actual_history",
            "trace_verified",
            "proof_available",
            "execution_available",
        )


def create_counterfactual_replay_candidate(
    *,
    checkpoint_ref: RuntimeCheckpointRef,
    branch_reason: CounterfactualBranchReason,
    branch_label: str,
    source_topology_snapshot_id: str = "",
    alternative_revision_proposal_id: str = "",
    alternative_operator_decision_id: str = "",
) -> CounterfactualReplayCandidate:
    """Name an alternative branch for analysis. History is never rewritten."""

    payload = {
        "contract_version": COUNTERFACTUAL_REPLAY_CANDIDATE_VERSION,
        "source_checkpoint_id": checkpoint_ref.checkpoint_id,
        "run_id": checkpoint_ref.run_id,
        "branch_reason": branch_reason.value,
        "branch_label": branch_label,
        "alternative_revision_proposal_id": alternative_revision_proposal_id,
        "alternative_operator_decision_id": alternative_operator_decision_id,
    }
    return CounterfactualReplayCandidate(
        counterfactual_candidate_id="flcfr-" + stable_hash(payload)[:16],
        contract_version=COUNTERFACTUAL_REPLAY_CANDIDATE_VERSION,
        source_checkpoint_id=checkpoint_ref.checkpoint_id,
        run_id=checkpoint_ref.run_id,
        branch_reason=branch_reason,
        branch_label=branch_label,
        truth_label=FlowTruthLabel.SIMULATED,
        source_topology_snapshot_id=source_topology_snapshot_id,
        alternative_revision_proposal_id=alternative_revision_proposal_id,
        alternative_operator_decision_id=alternative_operator_decision_id,
    )


@dataclass(frozen=True)
class CounterfactualComparisonFrame(_CanonicalMixin):
    """Comparison of a counterfactual branch to its baseline checkpoint."""

    frame_id: str
    frame_version: str
    counterfactual_candidate_id: str
    baseline_checkpoint_id: str
    compared_dimensions: tuple[str, ...]
    divergence_summary: str
    truth_label: FlowTruthLabel
    is_actual_history: bool = False
    proves_outcome: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "is_actual_history", "proves_outcome")


def build_counterfactual_comparison_frame(
    candidate: CounterfactualReplayCandidate,
    *,
    compared_dimensions: tuple[str, ...] = (),
    divergence_summary: str = "",
) -> CounterfactualComparisonFrame:
    payload = {
        "frame_version": COUNTERFACTUAL_COMPARISON_FRAME_VERSION,
        "counterfactual_candidate_id": candidate.counterfactual_candidate_id,
        "compared_dimensions": compared_dimensions,
    }
    return CounterfactualComparisonFrame(
        frame_id="flccf-" + stable_hash(payload)[:16],
        frame_version=COUNTERFACTUAL_COMPARISON_FRAME_VERSION,
        counterfactual_candidate_id=candidate.counterfactual_candidate_id,
        baseline_checkpoint_id=candidate.source_checkpoint_id,
        compared_dimensions=compared_dimensions,
        divergence_summary=divergence_summary,
        truth_label=FlowTruthLabel.SIMULATED,
    )


@dataclass(frozen=True)
class CounterfactualTruthBoundary(_CanonicalMixin):
    """The counterfactual law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = COUNTERFACTUAL_PROOF_UNAVAILABLE_REASON
    counterfactual_is_not_history: bool = True
    counterfactual_is_not_proof: bool = True
    counterfactual_rewrites_history: bool = False
    counterfactual_executes: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "counterfactual_is_not_history", "counterfactual_is_not_proof"
        )
        _forbid_true(self, "counterfactual_rewrites_history", "counterfactual_executes")


def build_counterfactual_truth_boundary() -> CounterfactualTruthBoundary:
    payload = {"boundary_version": COUNTERFACTUAL_TRUTH_BOUNDARY_VERSION}
    return CounterfactualTruthBoundary(
        boundary_version=COUNTERFACTUAL_TRUTH_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class CounterfactualReplayReadModel(_CanonicalMixin):
    """Deterministic counterfactual projection. Branches, never history."""

    read_model_version: str
    counterfactual_candidate_ids: tuple[str, ...]
    branch_reason_counts: Mapping[str, int]
    truth_label: FlowTruthLabel
    read_model_hash: str
    counterfactual_is_not_history: bool = True
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "counterfactual_is_not_history")
        _forbid_true(self, "proof_available")


def build_counterfactual_replay_read_model(
    candidates: tuple[CounterfactualReplayCandidate, ...] = (),
) -> CounterfactualReplayReadModel:
    reason_counts: dict[str, int] = {}
    for candidate in candidates:
        key = candidate.branch_reason.value
        reason_counts[key] = reason_counts.get(key, 0) + 1
    payload = {
        "read_model_version": COUNTERFACTUAL_REPLAY_READ_MODEL_VERSION,
        "counterfactual_candidate_ids": tuple(
            c.counterfactual_candidate_id for c in candidates
        ),
    }
    return CounterfactualReplayReadModel(
        read_model_version=COUNTERFACTUAL_REPLAY_READ_MODEL_VERSION,
        counterfactual_candidate_ids=tuple(
            c.counterfactual_candidate_id for c in candidates
        ),
        branch_reason_counts=reason_counts,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
