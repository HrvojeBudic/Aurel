"""P3-FLOW-F revert candidate / runtime diff / recovery checkpoint layer
(P3.14.20-P3.14.30).

A revert/rollback candidate is a safety review object: ``safe_to_execute``
stays False in P3, nothing rolls back, and no external state is reverted.
A runtime diff is a deterministic comparison of two local state points — a
comparison, never proof, never replay, never rollback. A recovery checkpoint
requirement prepares the future P3-FLOW-G self-healing discipline: it can
require a pre-recovery checkpoint and a post-recovery comparison frame, but
it never executes recovery and a comparison expectation is not verification.
Rollback execution belongs to P4 AurelExec; proof belongs to P5 AurelTrace;
authority belongs to P9 Custos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_checkpoint import (
    CheckpointStateEnvelope,
    RuntimeCheckpointKind,
    RuntimeCheckpointRef,
)
from .flow_topology import RuntimeTopologySnapshot
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

RUNTIME_REVERT_CANDIDATE_VERSION = "runtime_revert_candidate.v1"
ROLLBACK_EXECUTION_BOUNDARY_VERSION = "rollback_execution_boundary.v1"
REVERT_SAFETY_FRAME_VERSION = "revert_safety_frame.v1"
ROLLBACK_AUTHORITY_REQUIREMENT_VERSION = "rollback_authority_requirement.v1"
REVERT_READ_MODEL_VERSION = "revert_read_model.v1"
RUNTIME_STATE_DIFF_SUMMARY_VERSION = "runtime_state_diff_summary.v1"
CHECKPOINT_DIFF_FRAME_VERSION = "checkpoint_diff_frame.v1"
TOPOLOGY_DIFF_FRAME_VERSION = "topology_diff_frame.v1"
EVENT_STREAM_DIFF_FRAME_VERSION = "event_stream_diff_frame.v1"
COMMITMENT_DIFF_FRAME_VERSION = "commitment_diff_frame.v1"
DIFF_READ_MODEL_VERSION = "diff_read_model.v1"
DIFF_TRUTH_BOUNDARY_VERSION = "diff_truth_boundary.v1"
RECOVERY_CHECKPOINT_REQUIREMENT_VERSION = "recovery_checkpoint_requirement.v1"
PRE_RECOVERY_CHECKPOINT_REF_VERSION = "pre_recovery_checkpoint_ref.v1"
POST_RECOVERY_COMPARISON_FRAME_VERSION = "post_recovery_comparison_frame.v1"
RECOVERY_STATE_PRESERVATION_FRAME_VERSION = "recovery_state_preservation_frame.v1"
RECOVERY_CHECKPOINT_READ_MODEL_VERSION = "recovery_checkpoint_read_model.v1"
RECOVERY_CHECKPOINT_BOUNDARY_VERSION = "recovery_checkpoint_boundary.v1"

REVERT_EXECUTION_UNAVAILABLE_REASON = (
    "a revert/rollback candidate is a safety review object only; nothing "
    "rolls back or reverts in P3-FLOW-F — rollback execution belongs to P4 "
    "AurelExec, proof to P5 AurelTrace, authority to P9 Custos"
)
DIFF_PROOF_UNAVAILABLE_REASON = (
    "a runtime diff is a deterministic local comparison, never proof of "
    "correctness; the evidence spine belongs to P5 AurelTrace"
)
RECOVERY_EXECUTION_UNAVAILABLE_REASON = (
    "a recovery checkpoint requirement prepares future self-healing "
    "discipline only; it never executes recovery and a post-recovery "
    "comparison expectation is not verification"
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
# Revert / rollback candidates (P3.14.20-P3.14.24)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeRevertCandidate(_CanonicalMixin):
    """Candidate for future revert/rollback review. Never rollback execution."""

    revert_candidate_id: str
    contract_version: str
    target_checkpoint_id: str
    affected_run_id: str
    affected_node_ids: tuple[str, ...]
    affected_event_ids: tuple[str, ...]
    affected_topology_snapshot_ids: tuple[str, ...]
    external_side_effects_present: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = REVERT_EXECUTION_UNAVAILABLE_REASON
    safe_to_execute: bool = False
    requires_operator_review: bool = True
    requires_authority: bool = True
    requires_p4_execution: bool = True
    requires_p5_proof: bool = True
    requires_p9_authority: bool = True
    rollback_executed: bool = False
    external_state_reverted: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "safe_to_execute", "rollback_executed", "external_state_reverted"
        )
        _forbid_false(
            self,
            "requires_operator_review",
            "requires_authority",
            "requires_p4_execution",
            "requires_p5_proof",
            "requires_p9_authority",
        )


def create_runtime_revert_candidate(
    *,
    target_checkpoint: RuntimeCheckpointRef,
    affected_node_ids: tuple[str, ...] = (),
    affected_event_ids: tuple[str, ...] = (),
    affected_topology_snapshot_ids: tuple[str, ...] = (),
    external_side_effects_present: bool = False,
) -> RuntimeRevertCandidate:
    """Name a revert/rollback review candidate. Nothing rolls back."""

    payload = {
        "contract_version": RUNTIME_REVERT_CANDIDATE_VERSION,
        "target_checkpoint_id": target_checkpoint.checkpoint_id,
        "affected_run_id": target_checkpoint.run_id,
        "affected_node_ids": affected_node_ids,
        "affected_event_ids": affected_event_ids,
        "affected_topology_snapshot_ids": affected_topology_snapshot_ids,
        "external_side_effects_present": external_side_effects_present,
    }
    return RuntimeRevertCandidate(
        revert_candidate_id="flrvc-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_REVERT_CANDIDATE_VERSION,
        target_checkpoint_id=target_checkpoint.checkpoint_id,
        affected_run_id=target_checkpoint.run_id,
        affected_node_ids=affected_node_ids,
        affected_event_ids=affected_event_ids,
        affected_topology_snapshot_ids=affected_topology_snapshot_ids,
        external_side_effects_present=external_side_effects_present,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RollbackExecutionBoundary(_CanonicalMixin):
    """The rollback law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = REVERT_EXECUTION_UNAVAILABLE_REASON
    rollback_candidate_is_not_execution: bool = True
    revert_candidate_is_not_external_revert: bool = True
    rollback_executes: bool = False
    revert_executes: bool = False
    rollback_grants_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "rollback_candidate_is_not_execution",
            "revert_candidate_is_not_external_revert",
        )
        _forbid_true(
            self, "rollback_executes", "revert_executes", "rollback_grants_authority"
        )


def build_rollback_execution_boundary() -> RollbackExecutionBoundary:
    payload = {"boundary_version": ROLLBACK_EXECUTION_BOUNDARY_VERSION}
    return RollbackExecutionBoundary(
        boundary_version=ROLLBACK_EXECUTION_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class RevertSafetyFrame(_CanonicalMixin):
    """Safety posture of one revert candidate. ``safe_to_execute`` stays False."""

    frame_id: str
    frame_version: str
    revert_candidate_id: str
    run_id: str
    external_side_effects_present: bool
    truth_label: FlowTruthLabel
    safe_to_execute: bool = False
    requires_operator_review: bool = True
    requires_p4_execution: bool = True
    requires_p5_proof: bool = True
    requires_p9_authority: bool = True

    def __post_init__(self) -> None:
        _forbid_true(self, "safe_to_execute")
        _forbid_false(
            self,
            "requires_operator_review",
            "requires_p4_execution",
            "requires_p5_proof",
            "requires_p9_authority",
        )


def build_revert_safety_frame(candidate: RuntimeRevertCandidate) -> RevertSafetyFrame:
    payload = {
        "frame_version": REVERT_SAFETY_FRAME_VERSION,
        "revert_candidate_id": candidate.revert_candidate_id,
    }
    return RevertSafetyFrame(
        frame_id="flrsf-" + stable_hash(payload)[:16],
        frame_version=REVERT_SAFETY_FRAME_VERSION,
        revert_candidate_id=candidate.revert_candidate_id,
        run_id=candidate.affected_run_id,
        external_side_effects_present=candidate.external_side_effects_present,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RollbackAuthorityRequirement(_CanonicalMixin):
    """What future rollback would require. A requirement grants nothing."""

    requirement_id: str
    requirement_version: str
    revert_candidate_id: str
    truth_label: FlowTruthLabel
    requires_operator_review: bool = True
    requires_p4_execution: bool = True
    requires_p5_proof: bool = True
    requires_p9_authority: bool = True
    authority_granted: bool = False
    permission_granted: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requires_operator_review",
            "requires_p4_execution",
            "requires_p5_proof",
            "requires_p9_authority",
        )
        _forbid_true(self, "authority_granted", "permission_granted")


def build_rollback_authority_requirement(
    candidate: RuntimeRevertCandidate,
) -> RollbackAuthorityRequirement:
    payload = {
        "requirement_version": ROLLBACK_AUTHORITY_REQUIREMENT_VERSION,
        "revert_candidate_id": candidate.revert_candidate_id,
    }
    return RollbackAuthorityRequirement(
        requirement_id="flrar-" + stable_hash(payload)[:16],
        requirement_version=ROLLBACK_AUTHORITY_REQUIREMENT_VERSION,
        revert_candidate_id=candidate.revert_candidate_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RevertReadModel(_CanonicalMixin):
    """Deterministic revert-candidate projection. Nothing has rolled back."""

    read_model_version: str
    revert_candidate_ids: tuple[str, ...]
    candidates_with_external_side_effects: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    any_safe_to_execute: bool = False
    rollback_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "any_safe_to_execute", "rollback_executed")


def build_revert_read_model(
    candidates: tuple[RuntimeRevertCandidate, ...] = (),
) -> RevertReadModel:
    payload = {
        "read_model_version": REVERT_READ_MODEL_VERSION,
        "revert_candidate_ids": tuple(c.revert_candidate_id for c in candidates),
    }
    return RevertReadModel(
        read_model_version=REVERT_READ_MODEL_VERSION,
        revert_candidate_ids=tuple(c.revert_candidate_id for c in candidates),
        candidates_with_external_side_effects=sum(
            1 for c in candidates if c.external_side_effects_present
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Runtime diff summaries (P3.14.25-P3.14.30)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeStateDiffSummary(_CanonicalMixin):
    """Deterministic comparison of two runtime state points. Not proof."""

    diff_id: str
    contract_version: str
    left_checkpoint_id: str
    right_checkpoint_id: str
    added_node_ids: tuple[str, ...]
    removed_node_ids: tuple[str, ...]
    changed_node_ids: tuple[str, ...]
    added_edge_ids: tuple[str, ...]
    removed_edge_ids: tuple[str, ...]
    changed_edge_ids: tuple[str, ...]
    added_event_ids: tuple[str, ...]
    omitted_event_ids: tuple[str, ...]
    changed_commitment_ids: tuple[str, ...]
    diff_summary: str
    truth_label: FlowTruthLabel
    diff_hash: str
    left_topology_snapshot_id: str = ""
    right_topology_snapshot_id: str = ""
    unavailable_reason: str = DIFF_PROOF_UNAVAILABLE_REASON
    proof_available: bool = False
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available", "trace_verified")


def _diff_topology_edges(
    left: RuntimeTopologySnapshot | None, right: RuntimeTopologySnapshot | None
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    left_edges = {edge.edge_id: edge for edge in (left.edges if left else ())}
    right_edges = {edge.edge_id: edge for edge in (right.edges if right else ())}
    added = tuple(sorted(set(right_edges) - set(left_edges)))
    removed = tuple(sorted(set(left_edges) - set(right_edges)))
    changed = tuple(
        sorted(
            edge_id
            for edge_id in set(left_edges) & set(right_edges)
            if left_edges[edge_id] != right_edges[edge_id]
        )
    )
    return added, removed, changed


def build_runtime_state_diff_summary(
    *,
    left_envelope: CheckpointStateEnvelope,
    right_envelope: CheckpointStateEnvelope,
    left_topology: RuntimeTopologySnapshot | None = None,
    right_topology: RuntimeTopologySnapshot | None = None,
    left_event_ids: tuple[str, ...] = (),
    right_event_ids: tuple[str, ...] = (),
    left_commitment_ids: tuple[str, ...] = (),
    right_commitment_ids: tuple[str, ...] = (),
) -> RuntimeStateDiffSummary:
    """Compare two checkpoint state envelopes deterministically.

    Plain set arithmetic over already-recorded local state. Comparing state
    points proves nothing, replays nothing, and rolls back nothing.
    """

    if left_envelope.run_id != right_envelope.run_id:
        raise AurelFlowValidationError(
            f"left envelope run {left_envelope.run_id!r} does not match right "
            f"envelope run {right_envelope.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="right_envelope",
        )
    left_nodes = dict(left_envelope.node_states)
    right_nodes = dict(right_envelope.node_states)
    added_node_ids = tuple(sorted(set(right_nodes) - set(left_nodes)))
    removed_node_ids = tuple(sorted(set(left_nodes) - set(right_nodes)))
    changed_node_ids = tuple(
        sorted(
            node_id
            for node_id in set(left_nodes) & set(right_nodes)
            if left_nodes[node_id] != right_nodes[node_id]
        )
    )
    added_edge_ids, removed_edge_ids, changed_edge_ids = _diff_topology_edges(
        left_topology, right_topology
    )
    added_event_ids = tuple(sorted(set(right_event_ids) - set(left_event_ids)))
    omitted_event_ids = tuple(sorted(set(left_event_ids) - set(right_event_ids)))
    changed_commitment_ids = tuple(
        sorted(set(left_commitment_ids) ^ set(right_commitment_ids))
    )
    total_changes = (
        len(added_node_ids)
        + len(removed_node_ids)
        + len(changed_node_ids)
        + len(added_edge_ids)
        + len(removed_edge_ids)
        + len(changed_edge_ids)
        + len(added_event_ids)
        + len(omitted_event_ids)
        + len(changed_commitment_ids)
    )
    payload = {
        "contract_version": RUNTIME_STATE_DIFF_SUMMARY_VERSION,
        "left_checkpoint_id": left_envelope.checkpoint_id,
        "right_checkpoint_id": right_envelope.checkpoint_id,
        "added_node_ids": added_node_ids,
        "removed_node_ids": removed_node_ids,
        "changed_node_ids": changed_node_ids,
        "added_edge_ids": added_edge_ids,
        "removed_edge_ids": removed_edge_ids,
        "changed_edge_ids": changed_edge_ids,
        "added_event_ids": added_event_ids,
        "omitted_event_ids": omitted_event_ids,
        "changed_commitment_ids": changed_commitment_ids,
    }
    return RuntimeStateDiffSummary(
        diff_id="fldif-" + stable_hash(payload)[:16],
        contract_version=RUNTIME_STATE_DIFF_SUMMARY_VERSION,
        left_checkpoint_id=left_envelope.checkpoint_id,
        right_checkpoint_id=right_envelope.checkpoint_id,
        added_node_ids=added_node_ids,
        removed_node_ids=removed_node_ids,
        changed_node_ids=changed_node_ids,
        added_edge_ids=added_edge_ids,
        removed_edge_ids=removed_edge_ids,
        changed_edge_ids=changed_edge_ids,
        added_event_ids=added_event_ids,
        omitted_event_ids=omitted_event_ids,
        changed_commitment_ids=changed_commitment_ids,
        diff_summary=f"{total_changes} recorded change(s) between state points",
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        diff_hash=stable_hash(payload),
        left_topology_snapshot_id=(
            left_topology.snapshot_id if left_topology is not None else ""
        ),
        right_topology_snapshot_id=(
            right_topology.snapshot_id if right_topology is not None else ""
        ),
    )


@dataclass(frozen=True)
class CheckpointDiffFrame(_CanonicalMixin):
    """Checkpoint-level slice of a runtime diff."""

    frame_id: str
    frame_version: str
    diff_id: str
    left_checkpoint_id: str
    right_checkpoint_id: str
    step_delta: int
    lifecycle_changed: bool
    node_change_count: int
    truth_label: FlowTruthLabel
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available")


def build_checkpoint_diff_frame(
    diff: RuntimeStateDiffSummary,
    *,
    left_envelope: CheckpointStateEnvelope,
    right_envelope: CheckpointStateEnvelope,
) -> CheckpointDiffFrame:
    payload = {"frame_version": CHECKPOINT_DIFF_FRAME_VERSION, "diff_id": diff.diff_id}
    return CheckpointDiffFrame(
        frame_id="flcdf-" + stable_hash(payload)[:16],
        frame_version=CHECKPOINT_DIFF_FRAME_VERSION,
        diff_id=diff.diff_id,
        left_checkpoint_id=diff.left_checkpoint_id,
        right_checkpoint_id=diff.right_checkpoint_id,
        step_delta=right_envelope.step - left_envelope.step,
        lifecycle_changed=(
            left_envelope.lifecycle_status != right_envelope.lifecycle_status
        ),
        node_change_count=(
            len(diff.added_node_ids)
            + len(diff.removed_node_ids)
            + len(diff.changed_node_ids)
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class TopologyDiffFrame(_CanonicalMixin):
    """Topology-level slice of a runtime diff."""

    frame_id: str
    frame_version: str
    diff_id: str
    left_topology_snapshot_id: str
    right_topology_snapshot_id: str
    edge_change_count: int
    truth_label: FlowTruthLabel
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available")


def build_topology_diff_frame(diff: RuntimeStateDiffSummary) -> TopologyDiffFrame:
    payload = {"frame_version": TOPOLOGY_DIFF_FRAME_VERSION, "diff_id": diff.diff_id}
    return TopologyDiffFrame(
        frame_id="fltdf-" + stable_hash(payload)[:16],
        frame_version=TOPOLOGY_DIFF_FRAME_VERSION,
        diff_id=diff.diff_id,
        left_topology_snapshot_id=diff.left_topology_snapshot_id,
        right_topology_snapshot_id=diff.right_topology_snapshot_id,
        edge_change_count=(
            len(diff.added_edge_ids)
            + len(diff.removed_edge_ids)
            + len(diff.changed_edge_ids)
        ),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class EventStreamDiffFrame(_CanonicalMixin):
    """Event-stream slice of a runtime diff."""

    frame_id: str
    frame_version: str
    diff_id: str
    added_event_count: int
    omitted_event_count: int
    truth_label: FlowTruthLabel
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available")


def build_event_stream_diff_frame(
    diff: RuntimeStateDiffSummary,
) -> EventStreamDiffFrame:
    payload = {
        "frame_version": EVENT_STREAM_DIFF_FRAME_VERSION,
        "diff_id": diff.diff_id,
    }
    return EventStreamDiffFrame(
        frame_id="fledf-" + stable_hash(payload)[:16],
        frame_version=EVENT_STREAM_DIFF_FRAME_VERSION,
        diff_id=diff.diff_id,
        added_event_count=len(diff.added_event_ids),
        omitted_event_count=len(diff.omitted_event_ids),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class CommitmentDiffFrame(_CanonicalMixin):
    """Commitment slice of a runtime diff."""

    frame_id: str
    frame_version: str
    diff_id: str
    changed_commitment_count: int
    truth_label: FlowTruthLabel
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available")


def build_commitment_diff_frame(diff: RuntimeStateDiffSummary) -> CommitmentDiffFrame:
    payload = {"frame_version": COMMITMENT_DIFF_FRAME_VERSION, "diff_id": diff.diff_id}
    return CommitmentDiffFrame(
        frame_id="flcmf-" + stable_hash(payload)[:16],
        frame_version=COMMITMENT_DIFF_FRAME_VERSION,
        diff_id=diff.diff_id,
        changed_commitment_count=len(diff.changed_commitment_ids),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class DiffReadModel(_CanonicalMixin):
    """Deterministic diff projection. A comparison, never proof."""

    read_model_version: str
    diff_id: str
    total_change_count: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    diff_is_not_proof: bool = True
    diff_is_not_replay: bool = True
    diff_is_not_rollback: bool = True
    trace_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "diff_is_not_proof", "diff_is_not_replay", "diff_is_not_rollback"
        )
        _forbid_true(self, "trace_verified")


def build_diff_read_model(diff: RuntimeStateDiffSummary) -> DiffReadModel:
    total_change_count = (
        len(diff.added_node_ids)
        + len(diff.removed_node_ids)
        + len(diff.changed_node_ids)
        + len(diff.added_edge_ids)
        + len(diff.removed_edge_ids)
        + len(diff.changed_edge_ids)
        + len(diff.added_event_ids)
        + len(diff.omitted_event_ids)
        + len(diff.changed_commitment_ids)
    )
    payload = {
        "read_model_version": DIFF_READ_MODEL_VERSION,
        "diff_hash": diff.diff_hash,
    }
    return DiffReadModel(
        read_model_version=DIFF_READ_MODEL_VERSION,
        diff_id=diff.diff_id,
        total_change_count=total_change_count,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class DiffTruthBoundary(_CanonicalMixin):
    """The diff law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = DIFF_PROOF_UNAVAILABLE_REASON
    diff_is_not_proof: bool = True
    diff_is_not_replay: bool = True
    diff_is_not_rollback: bool = True
    diff_proves_correctness: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self, "diff_is_not_proof", "diff_is_not_replay", "diff_is_not_rollback"
        )
        _forbid_true(self, "diff_proves_correctness")


def build_diff_truth_boundary() -> DiffTruthBoundary:
    payload = {"boundary_version": DIFF_TRUTH_BOUNDARY_VERSION}
    return DiffTruthBoundary(
        boundary_version=DIFF_TRUTH_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


# ---------------------------------------------------------------------------
# Recovery checkpoint requirements (P3.14.25-P3.14.30)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecoveryCheckpointRequirement(_CanonicalMixin):
    """Pre-recovery checkpoint discipline for future self-healing (P3-FLOW-G).

    A requirement requires; it never executes recovery and never verifies.
    """

    requirement_id: str
    contract_version: str
    run_id: str
    required_checkpoint_kind: RuntimeCheckpointKind
    truth_label: FlowTruthLabel
    failure_or_recovery_candidate_id: str = ""
    unavailable_reason: str = RECOVERY_EXECUTION_UNAVAILABLE_REASON
    pre_recovery_checkpoint_required: bool = True
    post_recovery_comparison_required: bool = True
    state_preservation_required: bool = True
    requires_operator_review: bool = True
    requires_p4_execution_for_repair: bool = True
    requires_p5_proof_for_verification: bool = True
    requires_p9_authority_if_irreversible: bool = True
    recovery_executed: bool = False
    verification_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "pre_recovery_checkpoint_required",
            "post_recovery_comparison_required",
            "state_preservation_required",
            "requires_operator_review",
            "requires_p4_execution_for_repair",
            "requires_p5_proof_for_verification",
            "requires_p9_authority_if_irreversible",
        )
        _forbid_true(self, "recovery_executed", "verification_available")


def create_recovery_checkpoint_requirement(
    *,
    run_id: str,
    required_checkpoint_kind: RuntimeCheckpointKind = (
        RuntimeCheckpointKind.BEFORE_RECOVERY
    ),
    failure_or_recovery_candidate_id: str = "",
) -> RecoveryCheckpointRequirement:
    payload = {
        "contract_version": RECOVERY_CHECKPOINT_REQUIREMENT_VERSION,
        "run_id": run_id,
        "required_checkpoint_kind": required_checkpoint_kind.value,
        "failure_or_recovery_candidate_id": failure_or_recovery_candidate_id,
    }
    return RecoveryCheckpointRequirement(
        requirement_id="flrcq-" + stable_hash(payload)[:16],
        contract_version=RECOVERY_CHECKPOINT_REQUIREMENT_VERSION,
        run_id=run_id,
        required_checkpoint_kind=required_checkpoint_kind,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        failure_or_recovery_candidate_id=failure_or_recovery_candidate_id,
    )


@dataclass(frozen=True)
class PreRecoveryCheckpointRef(_CanonicalMixin):
    """Binding of a named checkpoint to a recovery requirement."""

    ref_id: str
    ref_version: str
    requirement_id: str
    checkpoint_id: str
    run_id: str
    satisfies_requirement: bool
    truth_label: FlowTruthLabel
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "recovery_executed")


def build_pre_recovery_checkpoint_ref(
    requirement: RecoveryCheckpointRequirement,
    checkpoint_ref: RuntimeCheckpointRef,
) -> PreRecoveryCheckpointRef:
    if checkpoint_ref.run_id != requirement.run_id:
        raise AurelFlowValidationError(
            f"checkpoint run {checkpoint_ref.run_id!r} does not match "
            f"requirement run {requirement.run_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="checkpoint_ref",
        )
    payload = {
        "ref_version": PRE_RECOVERY_CHECKPOINT_REF_VERSION,
        "requirement_id": requirement.requirement_id,
        "checkpoint_id": checkpoint_ref.checkpoint_id,
    }
    return PreRecoveryCheckpointRef(
        ref_id="flprc-" + stable_hash(payload)[:16],
        ref_version=PRE_RECOVERY_CHECKPOINT_REF_VERSION,
        requirement_id=requirement.requirement_id,
        checkpoint_id=checkpoint_ref.checkpoint_id,
        run_id=requirement.run_id,
        satisfies_requirement=(
            checkpoint_ref.checkpoint_kind is requirement.required_checkpoint_kind
        ),
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class PostRecoveryComparisonFrame(_CanonicalMixin):
    """Expectation that recovery is followed by a comparison. Not verification."""

    frame_id: str
    frame_version: str
    requirement_id: str
    run_id: str
    truth_label: FlowTruthLabel
    expected_diff_id: str = ""
    comparison_expected: bool = True
    comparison_is_not_verification: bool = True
    verification_available: bool = False
    proof_available: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "comparison_expected", "comparison_is_not_verification")
        _forbid_true(self, "verification_available", "proof_available")


def build_post_recovery_comparison_frame(
    requirement: RecoveryCheckpointRequirement, *, expected_diff_id: str = ""
) -> PostRecoveryComparisonFrame:
    payload = {
        "frame_version": POST_RECOVERY_COMPARISON_FRAME_VERSION,
        "requirement_id": requirement.requirement_id,
        "expected_diff_id": expected_diff_id,
    }
    return PostRecoveryComparisonFrame(
        frame_id="flpoc-" + stable_hash(payload)[:16],
        frame_version=POST_RECOVERY_COMPARISON_FRAME_VERSION,
        requirement_id=requirement.requirement_id,
        run_id=requirement.run_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        expected_diff_id=expected_diff_id,
    )


@dataclass(frozen=True)
class RecoveryStatePreservationFrame(_CanonicalMixin):
    """State-preservation posture around future recovery. Local only."""

    frame_id: str
    frame_version: str
    requirement_id: str
    run_id: str
    pre_recovery_checkpoint_id: str
    truth_label: FlowTruthLabel
    preservation_required: bool = True
    preservation_is_local_only: bool = True
    external_persistence: bool = False
    recovery_executed: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "preservation_required", "preservation_is_local_only")
        _forbid_true(self, "external_persistence", "recovery_executed")


def build_recovery_state_preservation_frame(
    requirement: RecoveryCheckpointRequirement,
    pre_recovery_ref: PreRecoveryCheckpointRef,
) -> RecoveryStatePreservationFrame:
    if pre_recovery_ref.requirement_id != requirement.requirement_id:
        raise AurelFlowValidationError(
            f"pre-recovery ref requirement {pre_recovery_ref.requirement_id!r} "
            f"does not match requirement {requirement.requirement_id!r}",
            code=AurelFlowErrorCode.RUN_MISMATCH,
            field="pre_recovery_ref",
        )
    payload = {
        "frame_version": RECOVERY_STATE_PRESERVATION_FRAME_VERSION,
        "requirement_id": requirement.requirement_id,
        "pre_recovery_checkpoint_id": pre_recovery_ref.checkpoint_id,
    }
    return RecoveryStatePreservationFrame(
        frame_id="flrsp-" + stable_hash(payload)[:16],
        frame_version=RECOVERY_STATE_PRESERVATION_FRAME_VERSION,
        requirement_id=requirement.requirement_id,
        run_id=requirement.run_id,
        pre_recovery_checkpoint_id=pre_recovery_ref.checkpoint_id,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


@dataclass(frozen=True)
class RecoveryCheckpointBoundary(_CanonicalMixin):
    """The recovery-checkpoint law as a fail-closed structural object."""

    boundary_version: str
    truth_label: FlowTruthLabel
    boundary_hash: str
    unavailable_reason: str = RECOVERY_EXECUTION_UNAVAILABLE_REASON
    requirement_is_not_recovery_execution: bool = True
    comparison_expectation_is_not_verification: bool = True
    recovery_executes: bool = False
    recovery_verified: bool = False

    def __post_init__(self) -> None:
        _forbid_false(
            self,
            "requirement_is_not_recovery_execution",
            "comparison_expectation_is_not_verification",
        )
        _forbid_true(self, "recovery_executes", "recovery_verified")


def build_recovery_checkpoint_boundary() -> RecoveryCheckpointBoundary:
    payload = {"boundary_version": RECOVERY_CHECKPOINT_BOUNDARY_VERSION}
    return RecoveryCheckpointBoundary(
        boundary_version=RECOVERY_CHECKPOINT_BOUNDARY_VERSION,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        boundary_hash=stable_hash(payload),
    )


@dataclass(frozen=True)
class RecoveryCheckpointReadModel(_CanonicalMixin):
    """Deterministic recovery-requirement projection. Recovery never ran."""

    read_model_version: str
    requirement_ids: tuple[str, ...]
    truth_label: FlowTruthLabel
    read_model_hash: str
    recovery_executed: bool = False
    verification_available: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "recovery_executed", "verification_available")


def build_recovery_checkpoint_read_model(
    requirements: tuple[RecoveryCheckpointRequirement, ...] = (),
) -> RecoveryCheckpointReadModel:
    payload = {
        "read_model_version": RECOVERY_CHECKPOINT_READ_MODEL_VERSION,
        "requirement_ids": tuple(r.requirement_id for r in requirements),
    }
    return RecoveryCheckpointReadModel(
        read_model_version=RECOVERY_CHECKPOINT_READ_MODEL_VERSION,
        requirement_ids=tuple(r.requirement_id for r in requirements),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
