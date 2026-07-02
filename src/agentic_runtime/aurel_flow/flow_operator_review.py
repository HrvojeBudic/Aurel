"""P3-FLOW-D operator review / continue / stop / rollback loop.

Operator review is a review/intention layer only. Operator review is not
approval. Operator decision signal is not authority. A continue/stop/reject/
rollback candidate names a possible next action; it never mutates runtime
state, executes, authorizes, or rolls anything back. Authority belongs to
P9 Custos; execution belongs to P4 AurelExec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import AUTHORITY_UNAVAILABLE_REASON, FlowTruthLabel, _CanonicalMixin, stable_hash

OPERATOR_REVIEW_FRAME_VERSION = "operator_review_frame.v1"
OPERATOR_REVIEW_DECISION_VERSION = "operator_review_decision.v1"
REVIEW_CANDIDATE_VERSION = "operator_review_candidate.v1"
OPERATOR_REVIEW_READ_MODEL_VERSION = "operator_review_read_model.v1"


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


class OperatorReviewDecisionKind(str, Enum):
    """Closed-world review intents. APPROVE/EXECUTE are not in this vocabulary."""

    CONTINUE_CANDIDATE = "CONTINUE_CANDIDATE"
    STOP_CANDIDATE = "STOP_CANDIDATE"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"
    REQUEST_VERIFICATION = "REQUEST_VERIFICATION"
    REQUEST_MEDIATION = "REQUEST_MEDIATION"
    REQUEST_REASONING = "REQUEST_REASONING"
    REQUEST_RECOVERY_PROPOSAL = "REQUEST_RECOVERY_PROPOSAL"
    REQUEST_ROLLBACK_CANDIDATE = "REQUEST_ROLLBACK_CANDIDATE"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    HOLD = "HOLD"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class OperatorReviewFrame(_CanonicalMixin):
    """What is up for review and which intents are available. Not approval."""

    frame_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    proposal_id: str
    pause_ref: str
    recovery_proposal_ref: str
    proof_expectation_ref: str
    review_reason: str
    available_decision_kinds: tuple[OperatorReviewDecisionKind, ...]
    truth_label: FlowTruthLabel
    authority_unavailable_reason: str = AUTHORITY_UNAVAILABLE_REASON
    metadata: Mapping[str, str] = field(default_factory=dict)
    authority_granted: bool = False
    execution_permission_granted: bool = False
    execution_available: bool = False
    mutates_runtime_state: bool = False
    review_is_approval: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "execution_permission_granted",
            "execution_available",
            "mutates_runtime_state",
            "review_is_approval",
        )


def create_operator_review_frame(
    *,
    target_run_id: str,
    target_node_id: str,
    proposal_id: str = "",
    pause_ref: str = "",
    recovery_proposal_ref: str = "",
    proof_expectation_ref: str = "",
    review_reason: str,
    available_decision_kinds: tuple[OperatorReviewDecisionKind, ...] = tuple(
        OperatorReviewDecisionKind
    ),
    metadata: Mapping[str, str] | None = None,
) -> OperatorReviewFrame:
    frame_id = "florf-" + stable_hash(
        {
            "contract_version": OPERATOR_REVIEW_FRAME_VERSION,
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "proposal_id": proposal_id,
            "pause_ref": pause_ref,
            "recovery_proposal_ref": recovery_proposal_ref,
            "proof_expectation_ref": proof_expectation_ref,
            "review_reason": review_reason,
        }
    )[:16]
    return OperatorReviewFrame(
        frame_id=frame_id,
        contract_version=OPERATOR_REVIEW_FRAME_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        proposal_id=proposal_id,
        pause_ref=pause_ref,
        recovery_proposal_ref=recovery_proposal_ref,
        proof_expectation_ref=proof_expectation_ref,
        review_reason=review_reason,
        available_decision_kinds=available_decision_kinds,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class OperatorReviewDecision(_CanonicalMixin):
    """A recorded review intent. Intent is not authority and not execution."""

    review_decision_id: str
    contract_version: str
    frame_id: str
    operator_id: str
    decision_kind: OperatorReviewDecisionKind
    reason: str
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    authority_granted: bool = False
    execution_permission_granted: bool = False
    execution_available: bool = False
    mutates_runtime_state: bool = False
    decision_is_authority: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "execution_permission_granted",
            "execution_available",
            "mutates_runtime_state",
            "decision_is_authority",
        )


def create_operator_review_decision(
    *,
    frame: OperatorReviewFrame,
    operator_id: str,
    decision_kind: OperatorReviewDecisionKind,
    reason: str,
    metadata: Mapping[str, str] | None = None,
) -> OperatorReviewDecision:
    if decision_kind not in frame.available_decision_kinds:
        raise AurelFlowValidationError(
            f"decision kind {decision_kind.value!r} is not available on frame "
            f"{frame.frame_id!r}",
            code=AurelFlowErrorCode.SIGNAL_KIND_MISMATCH,
            field="decision_kind",
        )
    review_decision_id = "flord-" + stable_hash(
        {
            "contract_version": OPERATOR_REVIEW_DECISION_VERSION,
            "frame_id": frame.frame_id,
            "operator_id": operator_id,
            "decision_kind": decision_kind.value,
            "reason": reason,
        }
    )[:16]
    return OperatorReviewDecision(
        review_decision_id=review_decision_id,
        contract_version=OPERATOR_REVIEW_DECISION_VERSION,
        frame_id=frame.frame_id,
        operator_id=operator_id,
        decision_kind=decision_kind,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        metadata=dict(metadata or {}),
    )


@dataclass(frozen=True)
class _ReviewCandidateBase(_CanonicalMixin):
    """Shared shape for review candidates: named next actions, never actions."""

    candidate_id: str
    contract_version: str
    frame_id: str
    target_run_id: str
    target_node_id: str
    reason: str
    truth_label: FlowTruthLabel
    authority_granted: bool = False
    execution_permission_granted: bool = False
    execution_available: bool = False
    mutates_runtime_state: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted",
            "execution_permission_granted",
            "execution_available",
            "mutates_runtime_state",
        )


@dataclass(frozen=True)
class ContinueCandidate(_ReviewCandidateBase):
    """Candidate to continue later. Naming continue is not resuming."""

    decision_kind: OperatorReviewDecisionKind = (
        OperatorReviewDecisionKind.CONTINUE_CANDIDATE
    )


@dataclass(frozen=True)
class StopCandidate(_ReviewCandidateBase):
    """Candidate to stop later. Naming stop is not stopping."""

    decision_kind: OperatorReviewDecisionKind = OperatorReviewDecisionKind.STOP_CANDIDATE


@dataclass(frozen=True)
class RejectCandidate(_ReviewCandidateBase):
    """Candidate to reject later. Naming reject is not rejecting."""

    decision_kind: OperatorReviewDecisionKind = (
        OperatorReviewDecisionKind.REJECT_CANDIDATE
    )


@dataclass(frozen=True)
class RollbackReviewCandidate(_ReviewCandidateBase):
    """Rollback for review only. Reviewing a rollback is not rolling back."""

    rollback_candidate_ref: str = ""
    decision_kind: OperatorReviewDecisionKind = (
        OperatorReviewDecisionKind.REQUEST_ROLLBACK_CANDIDATE
    )
    rollback_executed: bool = False
    safe_to_execute: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _forbid_true(self, "rollback_executed", "safe_to_execute")


def _candidate_id(kind: str, frame: OperatorReviewFrame, reason: str) -> str:
    return "florc-" + stable_hash(
        {
            "contract_version": REVIEW_CANDIDATE_VERSION,
            "kind": kind,
            "frame_id": frame.frame_id,
            "reason": reason,
        }
    )[:16]


def create_continue_candidate(
    *, frame: OperatorReviewFrame, reason: str
) -> ContinueCandidate:
    return ContinueCandidate(
        candidate_id=_candidate_id("CONTINUE", frame, reason),
        contract_version=REVIEW_CANDIDATE_VERSION,
        frame_id=frame.frame_id,
        target_run_id=frame.target_run_id,
        target_node_id=frame.target_node_id,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def create_stop_candidate(*, frame: OperatorReviewFrame, reason: str) -> StopCandidate:
    return StopCandidate(
        candidate_id=_candidate_id("STOP", frame, reason),
        contract_version=REVIEW_CANDIDATE_VERSION,
        frame_id=frame.frame_id,
        target_run_id=frame.target_run_id,
        target_node_id=frame.target_node_id,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def create_reject_candidate(
    *, frame: OperatorReviewFrame, reason: str
) -> RejectCandidate:
    return RejectCandidate(
        candidate_id=_candidate_id("REJECT", frame, reason),
        contract_version=REVIEW_CANDIDATE_VERSION,
        frame_id=frame.frame_id,
        target_run_id=frame.target_run_id,
        target_node_id=frame.target_node_id,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
    )


def create_rollback_review_candidate(
    *, frame: OperatorReviewFrame, reason: str, rollback_candidate_ref: str
) -> RollbackReviewCandidate:
    return RollbackReviewCandidate(
        candidate_id=_candidate_id("ROLLBACK_REVIEW", frame, reason),
        contract_version=REVIEW_CANDIDATE_VERSION,
        frame_id=frame.frame_id,
        target_run_id=frame.target_run_id,
        target_node_id=frame.target_node_id,
        reason=reason,
        truth_label=FlowTruthLabel.CONTRACT_ONLY,
        rollback_candidate_ref=rollback_candidate_ref,
    )


@dataclass(frozen=True)
class OperatorReviewReadModel(_CanonicalMixin):
    """Deterministic review projection. Review visibility is not approval."""

    read_model_version: str
    frame_count: int
    decision_count: int
    decision_kind_counts: Mapping[str, int]
    continue_candidate_count: int
    stop_candidate_count: int
    reject_candidate_count: int
    rollback_review_candidate_count: int
    truth_label: FlowTruthLabel
    read_model_hash: str
    operator_review_is_not_approval: bool = True
    responsibility_transfer_is_not_authority_transfer: bool = True
    authority_granted_any: bool = False
    execution_permission_granted_any: bool = False
    execution_available: bool = False
    mutates_runtime_state: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "authority_granted_any",
            "execution_permission_granted_any",
            "execution_available",
            "mutates_runtime_state",
        )
        _forbid_false(
            self,
            "operator_review_is_not_approval",
            "responsibility_transfer_is_not_authority_transfer",
        )


def build_operator_review_read_model(
    *,
    frames: tuple[OperatorReviewFrame, ...],
    decisions: tuple[OperatorReviewDecision, ...] = (),
    continue_candidates: tuple[ContinueCandidate, ...] = (),
    stop_candidates: tuple[StopCandidate, ...] = (),
    reject_candidates: tuple[RejectCandidate, ...] = (),
    rollback_review_candidates: tuple[RollbackReviewCandidate, ...] = (),
) -> OperatorReviewReadModel:
    decision_kind_counts: dict[str, int] = {}
    for decision in decisions:
        key = decision.decision_kind.value
        decision_kind_counts[key] = decision_kind_counts.get(key, 0) + 1
    payload = {
        "read_model_version": OPERATOR_REVIEW_READ_MODEL_VERSION,
        "frame_ids": tuple(frame.frame_id for frame in frames),
        "decision_ids": tuple(decision.review_decision_id for decision in decisions),
        "candidate_ids": tuple(
            candidate.candidate_id
            for candidate in (
                *continue_candidates,
                *stop_candidates,
                *reject_candidates,
                *rollback_review_candidates,
            )
        ),
    }
    return OperatorReviewReadModel(
        read_model_version=OPERATOR_REVIEW_READ_MODEL_VERSION,
        frame_count=len(frames),
        decision_count=len(decisions),
        decision_kind_counts=decision_kind_counts,
        continue_candidate_count=len(continue_candidates),
        stop_candidate_count=len(stop_candidates),
        reject_candidate_count=len(reject_candidates),
        rollback_review_candidate_count=len(rollback_review_candidates),
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
        read_model_hash=stable_hash(payload),
    )
