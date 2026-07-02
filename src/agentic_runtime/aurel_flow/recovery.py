"""P3-FLOW-B failure / retry / recovery / rollback candidates (P3.5.x).

Candidate semantics only. RetryEligibility is not retry execution: no handler
is called, no worker exists, and execution stays unavailable. RecoveryProposal
is not recovery execution. RollbackCandidate is not rollback execution —
``safe_to_execute`` is permanently False in this pack. Failure propagation
risk is calculated from the declarative graph so downstream layers can see
local vs downstream vs workflow-blocking risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .types import (
    EXECUTION_UNAVAILABLE_REASON,
    FlowTruthLabel,
    _CanonicalMixin,
    stable_hash,
)
from .workflow_graph import DEPENDENCY_EDGE_TYPES, WorkflowGraph

FAILURE_ASSESSMENT_VERSION = "failure_assessment.v1"
RETRY_POLICY_VERSION = "retry_policy.v1"
RETRY_ELIGIBILITY_VERSION = "retry_eligibility.v1"
RECOVERY_PROPOSAL_VERSION = "recovery_proposal.v1"
ROLLBACK_CANDIDATE_VERSION = "rollback_candidate.v1"
FAILURE_RECOVERY_READ_MODEL_VERSION = "failure_recovery_read_model.v1"


class FailureClassification(str, Enum):
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    OPERATOR_REJECTED = "OPERATOR_REJECTED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    MISSING_EXECUTOR = "MISSING_EXECUTOR"
    EXTERNAL_EXECUTION_UNAVAILABLE = "EXTERNAL_EXECUTION_UNAVAILABLE"
    TIMEOUT_CANDIDATE = "TIMEOUT_CANDIDATE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class FailurePropagationRisk(str, Enum):
    LOCAL = "LOCAL"
    DOWNSTREAM_NODES = "DOWNSTREAM_NODES"
    WORKFLOW_BLOCKING = "WORKFLOW_BLOCKING"
    SYSTEMIC = "SYSTEMIC"
    UNKNOWN = "UNKNOWN"


class RollbackCandidateReason(str, Enum):
    FAILED_STATE_TRANSITION = "FAILED_STATE_TRANSITION"
    OPERATOR_REJECTED = "OPERATOR_REJECTED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    DOWNSTREAM_FAILURE = "DOWNSTREAM_FAILURE"
    RECOVERY_UNAVAILABLE = "RECOVERY_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class FailureAssessment(_CanonicalMixin):
    """Visible failure classification + propagation risk. Not a Trace verdict."""

    assessment_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    classification: FailureClassification
    propagation_risk: FailurePropagationRisk
    downstream_node_ids: tuple[str, ...]
    detail: str
    truth_label: FlowTruthLabel


@dataclass(frozen=True)
class RetryPolicy(_CanonicalMixin):
    """Declarative retry policy. Declares limits; executes nothing."""

    policy_id: str
    contract_version: str
    max_attempts: int
    cooldown_label: str
    retry_on: tuple[FailureClassification, ...]
    truth_label: FlowTruthLabel


@dataclass(frozen=True)
class RetryEligibility(_CanonicalMixin):
    """Candidate eligibility only. Eligible does not mean executable."""

    eligibility_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    eligible: bool
    reason: str
    attempt_count: int
    max_attempts: int
    cooldown_state: str
    failure_classification: FailureClassification
    failure_propagation_risk: FailurePropagationRisk
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    blocked_by_policy: bool = False
    blocked_by_missing_executor: bool = True
    execution_available: bool = False

    def __post_init__(self) -> None:
        if self.execution_available:
            raise AurelFlowValidationError(
                "RetryEligibility.execution_available must remain False; retry "
                "execution belongs to P4 AurelExec",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="execution_available",
            )


@dataclass(frozen=True)
class RetryDecision(_CanonicalMixin):
    """Eligibility decision record. Never a retry execution."""

    decision_id: str
    eligibility_id: str
    decided: str
    reason: str
    retry_executed: bool = False

    def __post_init__(self) -> None:
        if self.retry_executed:
            raise AurelFlowValidationError(
                "RetryDecision.retry_executed must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="retry_executed",
            )


@dataclass(frozen=True)
class RecoveryStep(_CanonicalMixin):
    """Declarative step description, not an executable action."""

    step_id: str
    order: int
    description: str
    step_kind: str = "DECLARATIVE"
    executable: bool = False
    requires_executor: bool = True

    def __post_init__(self) -> None:
        if self.executable:
            raise AurelFlowValidationError(
                "RecoveryStep.executable must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="executable",
            )


@dataclass(frozen=True)
class RecoveryFrame(_CanonicalMixin):
    """Recovery context and constraints for a specific failure."""

    frame_id: str
    target_run_id: str
    target_node_id: str
    failure_assessment_id: str
    failure_classification: FailureClassification
    failure_propagation_risk: FailurePropagationRisk
    constraints: tuple[str, ...]
    truth_label: FlowTruthLabel


@dataclass(frozen=True)
class RecoveryProposal(_CanonicalMixin):
    """Proposed recovery steps. AurelFlow proposes; it does not recover."""

    proposal_id: str
    contract_version: str
    failure_ref: str
    recovery_frame_id: str
    recovery_steps: tuple[RecoveryStep, ...]
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    requires_operator_review: bool = True
    requires_executor: bool = True
    execution_available: bool = False

    def __post_init__(self) -> None:
        if self.execution_available:
            raise AurelFlowValidationError(
                "RecoveryProposal.execution_available must remain False; recovery "
                "execution belongs to P4 AurelExec",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="execution_available",
            )


@dataclass(frozen=True)
class RollbackCandidate(_CanonicalMixin):
    """Rollback candidate record. Marking a candidate is not rolling back."""

    candidate_id: str
    contract_version: str
    target_run_id: str
    target_node_id: str
    target_state_ref: str
    reason: str
    candidate_reason: RollbackCandidateReason
    safe_to_prepare: bool
    truth_label: FlowTruthLabel
    metadata: Mapping[str, str] = field(default_factory=dict)
    safe_to_execute: bool = False
    execution_available: bool = False

    def __post_init__(self) -> None:
        for boundary_field in ("safe_to_execute", "execution_available"):
            if getattr(self, boundary_field):
                raise AurelFlowValidationError(
                    f"RollbackCandidate.{boundary_field} must remain False; rollback "
                    "execution belongs to P4 AurelExec",
                    code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field=boundary_field,
                )


@dataclass(frozen=True)
class FailureRecoveryReadModel(_CanonicalMixin):
    """Operator-inspectable recovery/candidate read model."""

    read_model_version: str
    run_id: str
    failure_assessments: tuple[FailureAssessment, ...]
    retry_eligibilities: tuple[RetryEligibility, ...]
    recovery_proposals: tuple[RecoveryProposal, ...]
    rollback_candidates: tuple[RollbackCandidate, ...]
    truth_label: FlowTruthLabel
    execution_unavailable_reason: str
    read_model_hash: str
    retry_executed: bool = False
    recovery_executed: bool = False
    rollback_executed: bool = False
    execution_available: bool = False


DEFAULT_RETRY_POLICY = RetryPolicy(
    policy_id="retry-policy-default",
    contract_version=RETRY_POLICY_VERSION,
    max_attempts=3,
    cooldown_label="NOT_APPLICABLE",
    retry_on=(
        FailureClassification.VALIDATION_FAILURE,
        FailureClassification.DEPENDENCY_FAILURE,
        FailureClassification.TIMEOUT_CANDIDATE,
    ),
    truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
)


def _downstream_node_ids(graph: WorkflowGraph, node_id: str) -> tuple[str, ...]:
    adjacency: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.edge_type in DEPENDENCY_EDGE_TYPES and edge.from_node_id in adjacency:
            adjacency[edge.from_node_id].append(edge.to_node_id)
    seen: set[str] = set()
    frontier = list(adjacency.get(node_id, []))
    while frontier:
        current = frontier.pop()
        if current in seen or current == node_id:
            continue
        seen.add(current)
        frontier.extend(adjacency.get(current, []))
    return tuple(sorted(seen))


def classify_failure(
    *,
    target_run_id: str,
    target_node_id: str,
    graph: WorkflowGraph | None = None,
    operator_rejected: bool = False,
    policy_blocked: bool = False,
    dependency_failed: bool = False,
    timeout_candidate: bool = False,
    missing_executor: bool = False,
    validation_failed: bool = False,
    systemic_hint: bool = False,
    detail: str = "",
) -> FailureAssessment:
    """Classify a failure and its propagation risk. Pure and deterministic.

    Propagation risk derives from declarative graph reachability: no
    dependents -> LOCAL; some dependents -> DOWNSTREAM_NODES; every exit node
    downstream -> WORKFLOW_BLOCKING. Without a graph the risk is UNKNOWN.
    """

    if operator_rejected:
        classification = FailureClassification.OPERATOR_REJECTED
    elif policy_blocked:
        classification = FailureClassification.POLICY_BLOCKED
    elif dependency_failed:
        classification = FailureClassification.DEPENDENCY_FAILURE
    elif timeout_candidate:
        classification = FailureClassification.TIMEOUT_CANDIDATE
    elif missing_executor:
        classification = FailureClassification.MISSING_EXECUTOR
    elif validation_failed:
        classification = FailureClassification.VALIDATION_FAILURE
    else:
        classification = FailureClassification.UNKNOWN

    downstream: tuple[str, ...] = ()
    if systemic_hint:
        risk = FailurePropagationRisk.SYSTEMIC
    elif graph is None:
        risk = FailurePropagationRisk.UNKNOWN
    else:
        downstream = _downstream_node_ids(graph, target_node_id)
        if not downstream:
            risk = FailurePropagationRisk.LOCAL
        elif graph.exit_node_ids and all(
            exit_id in downstream for exit_id in graph.exit_node_ids
        ):
            risk = FailurePropagationRisk.WORKFLOW_BLOCKING
        else:
            risk = FailurePropagationRisk.DOWNSTREAM_NODES

    assessment_id = "flfail-" + stable_hash(
        {
            "target_run_id": target_run_id,
            "target_node_id": target_node_id,
            "classification": classification,
            "risk": risk,
        }
    )[:16]
    return FailureAssessment(
        assessment_id=assessment_id,
        contract_version=FAILURE_ASSESSMENT_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        classification=classification,
        propagation_risk=risk,
        downstream_node_ids=downstream,
        detail=detail,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
    )


def calculate_retry_eligibility(
    policy: RetryPolicy,
    assessment: FailureAssessment,
    *,
    attempt_count: int,
    metadata: Mapping[str, str] | None = None,
) -> RetryEligibility:
    """Calculate candidate eligibility. Never retries anything."""

    blocked_by_policy = assessment.classification in (
        FailureClassification.OPERATOR_REJECTED,
        FailureClassification.POLICY_BLOCKED,
    )
    if blocked_by_policy:
        eligible = False
        reason = (
            f"{assessment.classification.value} failures are never retry-eligible: "
            "operator/policy decisions are not retried away"
        )
    elif attempt_count >= policy.max_attempts:
        eligible = False
        reason = f"attempt_count {attempt_count} reached max_attempts {policy.max_attempts}"
    elif assessment.classification not in policy.retry_on:
        eligible = False
        reason = (
            f"classification {assessment.classification.value} is not covered by "
            f"policy {policy.policy_id!r}"
        )
    else:
        eligible = True
        reason = (
            "retry candidate is eligible; retry execution remains unavailable "
            "(no executor exists in P3-FLOW-B)"
        )

    eligibility_id = "flretry-" + stable_hash(
        {
            "assessment_id": assessment.assessment_id,
            "policy_id": policy.policy_id,
            "attempt_count": attempt_count,
        }
    )[:16]
    return RetryEligibility(
        eligibility_id=eligibility_id,
        contract_version=RETRY_ELIGIBILITY_VERSION,
        target_run_id=assessment.target_run_id,
        target_node_id=assessment.target_node_id,
        eligible=eligible,
        reason=reason,
        attempt_count=attempt_count,
        max_attempts=policy.max_attempts,
        cooldown_state=policy.cooldown_label,
        failure_classification=assessment.classification,
        failure_propagation_risk=assessment.propagation_risk,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        metadata=dict(metadata or {}),
        blocked_by_policy=blocked_by_policy,
    )


def make_retry_decision(eligibility: RetryEligibility) -> RetryDecision:
    return RetryDecision(
        decision_id="flrdec-" + stable_hash({"eligibility_id": eligibility.eligibility_id})[:16],
        eligibility_id=eligibility.eligibility_id,
        decided="MARK_ELIGIBLE" if eligibility.eligible else "MARK_INELIGIBLE",
        reason=eligibility.reason,
    )


def build_recovery_frame(
    assessment: FailureAssessment,
    *,
    constraints: tuple[str, ...] = (),
) -> RecoveryFrame:
    return RecoveryFrame(
        frame_id="flrframe-" + stable_hash({"assessment_id": assessment.assessment_id})[:16],
        target_run_id=assessment.target_run_id,
        target_node_id=assessment.target_node_id,
        failure_assessment_id=assessment.assessment_id,
        failure_classification=assessment.classification,
        failure_propagation_risk=assessment.propagation_risk,
        constraints=constraints
        or ("no execution", "no external side effects", "operator review required"),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
    )


def build_recovery_proposal(
    frame: RecoveryFrame,
    *,
    step_descriptions: tuple[str, ...],
    metadata: Mapping[str, str] | None = None,
) -> RecoveryProposal:
    """Propose declarative recovery steps. AurelFlow does not recover."""

    steps = tuple(
        RecoveryStep(
            step_id="flrstep-" + stable_hash({"frame_id": frame.frame_id, "order": order})[:16],
            order=order,
            description=description,
        )
        for order, description in enumerate(step_descriptions)
    )
    return RecoveryProposal(
        proposal_id="flrprop-" + stable_hash(
            {"frame_id": frame.frame_id, "steps": step_descriptions}
        )[:16],
        contract_version=RECOVERY_PROPOSAL_VERSION,
        failure_ref=frame.failure_assessment_id,
        recovery_frame_id=frame.frame_id,
        recovery_steps=steps,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        metadata=dict(metadata or {}),
    )


def build_rollback_candidate(
    *,
    target_run_id: str,
    target_node_id: str,
    target_state_ref: str,
    candidate_reason: RollbackCandidateReason,
    reason: str,
    safe_to_prepare: bool = True,
    metadata: Mapping[str, str] | None = None,
) -> RollbackCandidate:
    """Mark a rollback candidate. Marking is not rolling back."""

    return RollbackCandidate(
        candidate_id="flrb-" + stable_hash(
            {
                "target_run_id": target_run_id,
                "target_node_id": target_node_id,
                "target_state_ref": target_state_ref,
                "candidate_reason": candidate_reason,
            }
        )[:16],
        contract_version=ROLLBACK_CANDIDATE_VERSION,
        target_run_id=target_run_id,
        target_node_id=target_node_id,
        target_state_ref=target_state_ref,
        reason=reason,
        candidate_reason=candidate_reason,
        safe_to_prepare=safe_to_prepare,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        metadata=dict(metadata or {}),
    )


def build_failure_recovery_read_model(
    run_id: str,
    *,
    failure_assessments: tuple[FailureAssessment, ...] = (),
    retry_eligibilities: tuple[RetryEligibility, ...] = (),
    recovery_proposals: tuple[RecoveryProposal, ...] = (),
    rollback_candidates: tuple[RollbackCandidate, ...] = (),
) -> FailureRecoveryReadModel:
    payload = {
        "read_model_version": FAILURE_RECOVERY_READ_MODEL_VERSION,
        "run_id": run_id,
        "assessment_ids": tuple(item.assessment_id for item in failure_assessments),
        "eligibility_ids": tuple(item.eligibility_id for item in retry_eligibilities),
        "proposal_ids": tuple(item.proposal_id for item in recovery_proposals),
        "candidate_ids": tuple(item.candidate_id for item in rollback_candidates),
    }
    return FailureRecoveryReadModel(
        read_model_version=FAILURE_RECOVERY_READ_MODEL_VERSION,
        run_id=run_id,
        failure_assessments=failure_assessments,
        retry_eligibilities=retry_eligibilities,
        recovery_proposals=recovery_proposals,
        rollback_candidates=rollback_candidates,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_BEHAVIOR,
        execution_unavailable_reason=EXECUTION_UNAVAILABLE_REASON,
        read_model_hash=stable_hash(payload),
    )
