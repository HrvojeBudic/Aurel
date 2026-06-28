"""Delegation action boundary contracts (P1.8-B).

P1.8-B covers P1.8.23 through P1.8.26 as a pure contract/read-model pack:

- P1.8.23 Proposal is not permission
- P1.8.24 Permission is not execution
- P1.8.25 Execution is not proof
- P1.8.26 Operator review is explicit state, not automatic execution

Boundary: these contracts describe semantic action separation. They do not
enforce runtime policy, call Custos, create approvals, grant live permissions,
execute tools/workflows, write memory, write Ledger/global trace, verify proof,
bind CLI/Shell/TUI, or mutate runtime state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, TypeVar

from .foundation import (
    DelegationErrorCode,
    DelegationSourceLabel,
    DelegationValidationError,
    stable_hash,
    to_canonical_json,
    validate_known_fields,
)

# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------

DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID = "P1.8-B"
DELEGATION_ACTION_BOUNDARY_PACK_CHECKPOINT_IDS = (
    "P1.8.23",
    "P1.8.24",
    "P1.8.25",
    "P1.8.26",
)

DELEGATION_PROPOSAL_BOUNDARY_VERSION = "delegation_proposal_boundary.v1"
DELEGATION_PERMISSION_BOUNDARY_VERSION = "delegation_permission_boundary.v1"
DELEGATION_EXECUTION_PROOF_BOUNDARY_VERSION = (
    "delegation_execution_proof_boundary.v1"
)
DELEGATION_OPERATOR_DECISION_BINDING_VERSION = (
    "operator_delegation_decision_binding.v1"
)
DELEGATION_ACTION_TRANSITION_CHECK_VERSION = (
    "delegation_action_transition_check.v1"
)
DELEGATION_ACTION_BOUNDARY_CHECKPOINT_READ_VERSION = (
    "delegation_action_boundary_checkpoint_read.v1"
)
DELEGATION_ACTION_BOUNDARY_READ_MODEL_VERSION = (
    "delegation_action_boundary_read_model.v1"
)
DELEGATION_ACTION_BOUNDARY_PACK_RESULT_VERSION = (
    "delegation_action_boundary_pack_result.v1"
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DelegationActionBoundaryKind(str, Enum):
    """Closed-world boundary taxonomy for P1.8.23-P1.8.26."""

    PROPOSAL_NOT_PERMISSION = "proposal_not_permission"
    PERMISSION_NOT_EXECUTION = "permission_not_execution"
    EXECUTION_NOT_PROOF = "execution_not_proof"
    OPERATOR_DECISION_BINDING = "operator_decision_binding"
    UNKNOWN = "unknown"


class DelegationActionState(str, Enum):
    """Closed-world action-state labels. States do not imply authority."""

    PROPOSED = "proposed"
    PERMISSION_CANDIDATE = "permission_candidate"
    PERMITTED = "permitted"
    EXECUTION_CANDIDATE = "execution_candidate"
    EXECUTED = "executed"
    PROOF_PENDING = "proof_pending"
    PROOF_UNAVAILABLE = "proof_unavailable"
    OPERATOR_REVIEW_PENDING = "operator_review_pending"
    OPERATOR_REVIEWED = "operator_reviewed"
    REJECTED = "rejected"
    STOPPED = "stopped"
    REVISION_REQUESTED = "revision_requested"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class DelegationOperatorDecisionState(str, Enum):
    """Closed-world operator decision labels."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    STOPPED = "stopped"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class DelegationActionTransitionVerdict(str, Enum):
    """Pure contract verdicts for attempted action-state transitions."""

    ALLOWED_AS_CONTRACT_STATE = "allowed_as_contract_state"
    REJECTED_SEMANTIC_COLLAPSE = "rejected_semantic_collapse"
    REQUIRES_PERMISSION = "requires_permission"
    REQUIRES_EXECUTION = "requires_execution"
    REQUIRES_EVIDENCE = "requires_evidence"
    REQUIRES_OPERATOR_DECISION = "requires_operator_decision"
    UNAVAILABLE_RUNTIME_ENFORCEMENT = "unavailable_runtime_enforcement"


class DelegationActionTruthLabel(str, Enum):
    """Truth labels for action-boundary contract data."""

    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    PERMISSION_ONLY = "PERMISSION_ONLY"
    PROOF_PENDING = "PROOF_PENDING"
    OPERATOR_DECISION_REQUIRED = "OPERATOR_DECISION_REQUIRED"
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"


class DelegationActionUnavailableReason(str, Enum):
    """Unavailable reasons for surfaces deliberately outside P1.8-B."""

    UNAVAILABLE_PERMISSION = "unavailable_permission"
    UNAVAILABLE_EXECUTION = "unavailable_execution"
    UNAVAILABLE_PROOF = "unavailable_proof"
    UNAVAILABLE_TRACE_VERIFICATION = "unavailable_trace_verification"
    UNAVAILABLE_AUTO_EXECUTION = "unavailable_auto_execution"
    UNAVAILABLE_RUNTIME_ENFORCEMENT = "unavailable_runtime_enforcement"
    CLI_SHELL_TUI_BINDING_P1_8_28 = "cli_shell_tui_binding_p1_8_28"
    POLICY_CUSTOS_DECISION_UNAVAILABLE = "policy_custos_decision_unavailable"
    APPROVAL_ACTIVATION_UNAVAILABLE = "approval_activation_unavailable"
    MEMORY_WRITE_UNAVAILABLE = "memory_write_unavailable"
    TOOL_WORKFLOW_EXECUTION_UNAVAILABLE = "tool_workflow_execution_unavailable"
    LEDGER_GLOBAL_TRACE_WRITE_UNAVAILABLE = "ledger_global_trace_write_unavailable"


class DelegationActionBoundaryStatus(str, Enum):
    """Read-model status labels for P1.8-B checkpoint rows."""

    CONTRACT_READY = "contract_ready"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    DelegationActionUnavailableReason.UNAVAILABLE_PERMISSION.value: (
        "Permission activation is UNAVAILABLE in P1.8-B; proposals are "
        "contract-only and cannot grant permission."
    ),
    DelegationActionUnavailableReason.UNAVAILABLE_EXECUTION.value: (
        "Execution is UNAVAILABLE in P1.8-B; permission contracts cannot start "
        "runtime, tool, or workflow execution."
    ),
    DelegationActionUnavailableReason.UNAVAILABLE_PROOF.value: (
        "Proof finality is UNAVAILABLE in P1.8-B; execution records are not "
        "verified proof."
    ),
    DelegationActionUnavailableReason.UNAVAILABLE_TRACE_VERIFICATION.value: (
        "Trace verification is UNAVAILABLE in P1.8-B; P1.8-B does not perform "
        "Ledger/global trace verification."
    ),
    DelegationActionUnavailableReason.UNAVAILABLE_AUTO_EXECUTION.value: (
        "Automatic execution from operator decision is UNAVAILABLE in P1.8-B; "
        "operator review is explicit state only."
    ),
    DelegationActionUnavailableReason.UNAVAILABLE_RUNTIME_ENFORCEMENT.value: (
        "Runtime enforcement is UNAVAILABLE in P1.8-B; this pack is "
        "contract-only and runtime enforcement belongs to later runtime/policy "
        "layers."
    ),
    DelegationActionUnavailableReason.CLI_SHELL_TUI_BINDING_P1_8_28.value: (
        "CLI/Shell/TUI binding is UNAVAILABLE in P1.8-B; owned by P1.8.28 "
        "Delegation Shell/CLI/TUI Binding."
    ),
    DelegationActionUnavailableReason.POLICY_CUSTOS_DECISION_UNAVAILABLE.value: (
        "Policy/Custos decisioning is UNAVAILABLE in P1.8-B; contracts do not "
        "call policy or Custos."
    ),
    DelegationActionUnavailableReason.APPROVAL_ACTIVATION_UNAVAILABLE.value: (
        "Approval activation is UNAVAILABLE in P1.8-B; operator review state is "
        "not HITL workflow execution."
    ),
    DelegationActionUnavailableReason.MEMORY_WRITE_UNAVAILABLE.value: (
        "Memory writes are UNAVAILABLE in P1.8-B; proposals and executions do "
        "not persist memory."
    ),
    DelegationActionUnavailableReason.TOOL_WORKFLOW_EXECUTION_UNAVAILABLE.value: (
        "Tool and workflow execution are UNAVAILABLE in P1.8-B; permission and "
        "operator states do not dispatch work."
    ),
    DelegationActionUnavailableReason.LEDGER_GLOBAL_TRACE_WRITE_UNAVAILABLE.value: (
        "Ledger/global trace writes are UNAVAILABLE in P1.8-B; deterministic "
        "hashes and report evidence are not trace finality."
    ),
}

DEFAULT_DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASONS = tuple(
    DelegationActionUnavailableReason(reason)
    for reason in DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASON_DETAILS
)


# ---------------------------------------------------------------------------
# Known fields
# ---------------------------------------------------------------------------


ACTION_BOUNDARY_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "permission_granted",
    "execution_started",
    "proof_verified",
    "operator_auto_approved",
    "custos_called",
    "policy_enforced",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "memory_written",
    "tool_invoked",
    "workflow_mutated",
    "runtime_mutated",
})

DELEGATION_PROPOSAL_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "boundary_kind",
    "action_state",
    "proposal_ref",
    "desired_action_ref",
    "permission_ref",
    "execution_ref",
    "proof_ref",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "proposal_boundary_hash",
})

DELEGATION_PERMISSION_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "boundary_kind",
    "action_state",
    "permission_ref",
    "proposal_ref",
    "execution_ref",
    "proof_ref",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "permission_boundary_hash",
})

DELEGATION_EXECUTION_PROOF_BOUNDARY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "boundary_kind",
    "action_state",
    "execution_ref",
    "evidence_ref",
    "trace_ref",
    "proof_claimed",
    "trace_verified",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "execution_proof_boundary_hash",
})

OPERATOR_DELEGATION_DECISION_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "checkpoint_id",
    "contract_version",
    "boundary_kind",
    "action_state",
    "decision_ref",
    "proposal_ref",
    "permission_ref",
    "execution_ref",
    "operator_decision_state",
    "final_claim_allowed",
    "continuation_allowed",
    "auto_execute",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "invariants",
    "side_effects",
    "operator_decision_binding_hash",
})

ACTION_TRANSITION_CHECK_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "source_state",
    "target_state",
    "boundary_kind",
    "verdict",
    "reason",
    "truth_label",
    "source_label",
    "transition_check_hash",
})

ACTION_BOUNDARY_CHECKPOINT_READ_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "checkpoint_id",
    "status",
    "evidence_ref",
    "contract_hash",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "checkpoint_read_hash",
})

ACTION_BOUNDARY_READ_MODEL_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "checkpoint_reads",
    "checkpoint_count",
    "truth_label",
    "source_label",
    "unavailable_reason_details",
    "side_effects",
    "read_model_hash",
})

ACTION_BOUNDARY_PACK_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "task_id",
    "checkpoint_ids",
    "proposal_boundary",
    "permission_boundary",
    "execution_proof_boundary",
    "operator_decision_binding",
    "read_model",
    "status",
    "truth_label",
    "source_label",
    "unavailable_reasons",
    "unavailable_reason_details",
    "side_effects",
    "result_hash",
})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


@dataclass(frozen=True)
class DelegationActionBoundarySideEffects(_CanonicalMixin):
    """Proof that P1.8-B performs no authority/execution/proof side effects."""

    permission_granted: bool = False
    execution_started: bool = False
    proof_verified: bool = False
    operator_auto_approved: bool = False
    custos_called: bool = False
    policy_enforced: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    memory_written: bool = False
    tool_invoked: bool = False
    workflow_mutated: bool = False
    runtime_mutated: bool = False


@dataclass(frozen=True)
class DelegationProposalBoundary(_CanonicalMixin):
    """P1.8.23 contract: proposal is intent only, not permission."""

    checkpoint_id: str
    contract_version: str
    boundary_kind: DelegationActionBoundaryKind
    action_state: DelegationActionState
    proposal_ref: str
    desired_action_ref: str
    permission_ref: str | None
    execution_ref: str | None
    proof_ref: str | None
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationActionUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActionBoundarySideEffects
    proposal_boundary_hash: str


@dataclass(frozen=True)
class DelegationPermissionBoundary(_CanonicalMixin):
    """P1.8.24 contract: permission is authorization state, not execution."""

    checkpoint_id: str
    contract_version: str
    boundary_kind: DelegationActionBoundaryKind
    action_state: DelegationActionState
    permission_ref: str
    proposal_ref: str
    execution_ref: str | None
    proof_ref: str | None
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationActionUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActionBoundarySideEffects
    permission_boundary_hash: str


@dataclass(frozen=True)
class DelegationExecutionProofBoundary(_CanonicalMixin):
    """P1.8.25 contract: execution record is not proof."""

    checkpoint_id: str
    contract_version: str
    boundary_kind: DelegationActionBoundaryKind
    action_state: DelegationActionState
    execution_ref: str
    evidence_ref: str | None
    trace_ref: str | None
    proof_claimed: bool
    trace_verified: bool
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationActionUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActionBoundarySideEffects
    execution_proof_boundary_hash: str


@dataclass(frozen=True)
class OperatorDelegationDecisionBinding(_CanonicalMixin):
    """P1.8.26 contract: operator decision state does not auto-execute."""

    checkpoint_id: str
    contract_version: str
    boundary_kind: DelegationActionBoundaryKind
    action_state: DelegationActionState
    decision_ref: str
    proposal_ref: str
    permission_ref: str | None
    execution_ref: str | None
    operator_decision_state: DelegationOperatorDecisionState
    final_claim_allowed: bool
    continuation_allowed: bool
    auto_execute: bool
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationActionUnavailableReason, ...]
    invariants: tuple[str, ...]
    side_effects: DelegationActionBoundarySideEffects
    operator_decision_binding_hash: str


@dataclass(frozen=True)
class DelegationActionTransitionCheck(_CanonicalMixin):
    """Pure contract transition verdict; never performs runtime enforcement."""

    schema_version: str
    source_state: DelegationActionState
    target_state: DelegationActionState
    boundary_kind: DelegationActionBoundaryKind
    verdict: DelegationActionTransitionVerdict
    reason: str
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    transition_check_hash: str


@dataclass(frozen=True)
class DelegationActionBoundaryCheckpointRead(_CanonicalMixin):
    """Compact read-model row for one P1.8-B checkpoint."""

    schema_version: str
    checkpoint_id: str
    status: DelegationActionBoundaryStatus
    evidence_ref: str
    contract_hash: str
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationActionUnavailableReason, ...]
    checkpoint_read_hash: str


@dataclass(frozen=True)
class DelegationActionBoundaryReadModel(_CanonicalMixin):
    """Compact P1.8-B read model containing exactly P1.8.23-P1.8.26."""

    schema_version: str
    task_id: str
    checkpoint_reads: tuple[DelegationActionBoundaryCheckpointRead, ...]
    checkpoint_count: int
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reason_details: dict[str, str]
    side_effects: DelegationActionBoundarySideEffects
    read_model_hash: str


@dataclass(frozen=True)
class DelegationActionBoundaryPackResult(_CanonicalMixin):
    """P1.8-B result envelope for the four action-boundary contracts."""

    schema_version: str
    task_id: str
    checkpoint_ids: tuple[str, ...]
    proposal_boundary: DelegationProposalBoundary
    permission_boundary: DelegationPermissionBoundary
    execution_proof_boundary: DelegationExecutionProofBoundary
    operator_decision_binding: OperatorDelegationDecisionBinding
    read_model: DelegationActionBoundaryReadModel
    status: DelegationActionBoundaryStatus
    truth_label: DelegationActionTruthLabel
    source_label: DelegationSourceLabel
    unavailable_reasons: tuple[DelegationActionUnavailableReason, ...]
    unavailable_reason_details: dict[str, str]
    side_effects: DelegationActionBoundarySideEffects
    result_hash: str


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


DELEGATION_PROPOSAL_BOUNDARY_INVARIANTS = (
    "Proposal describes intent, request, or candidate action only.",
    "Proposal cannot grant permission.",
    "Proposal cannot execute, write memory, invoke tools, mutate workflow, or claim proof.",
)

DELEGATION_PERMISSION_BOUNDARY_INVARIANTS = (
    "Permission may represent authorization state only.",
    "Permission may reference a proposal.",
    "Permission cannot start execution, invoke tools/workflows, mutate runtime, or claim proof.",
)

DELEGATION_EXECUTION_PROOF_BOUNDARY_INVARIANTS = (
    "Execution record is separate from proof.",
    "Execution cannot imply proof without evidence or trace support.",
    "TRACE_VERIFIED is unavailable in P1.8-B.",
)

OPERATOR_DELEGATION_DECISION_BINDING_INVARIANTS = (
    "Operator review state is explicit and testable.",
    "Approved operator decision does not auto-execute.",
    "Rejected, stopped, expired, or superseded decision blocks continuation.",
)


# ---------------------------------------------------------------------------
# Parse and canonical helpers
# ---------------------------------------------------------------------------


E = TypeVar("E", bound=Enum)


def _parse_enum(enum_type: type[E], value: E | str, field_name: str) -> E:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except ValueError as exc:
        raise DelegationValidationError(
            f"invalid {field_name}: {value!r}",
            code=DelegationErrorCode.INVALID_ENUM,
            field=field_name,
        ) from exc


def _parse_source_label(value: DelegationSourceLabel | str) -> DelegationSourceLabel:
    if isinstance(value, DelegationSourceLabel):
        return value
    try:
        return DelegationSourceLabel(value)
    except ValueError as exc:
        raise DelegationValidationError(
            f"invalid source_label: {value!r}",
            code=DelegationErrorCode.INVALID_SOURCE_LABEL,
            field="source_label",
        ) from exc


def _parse_unavailable_reasons(
    reasons: Sequence[DelegationActionUnavailableReason | str],
) -> tuple[DelegationActionUnavailableReason, ...]:
    return tuple(
        _parse_enum(
            DelegationActionUnavailableReason,
            reason,
            "unavailable_reasons",
        )
        for reason in reasons
    )


def _reject(message: str, *, field: str) -> None:
    raise DelegationValidationError(
        message,
        code=DelegationErrorCode.VALIDATION_ERROR,
        field=field,
    )


def _reject_live_or_trace_verified(truth_label: DelegationActionTruthLabel) -> None:
    if truth_label in {
        DelegationActionTruthLabel.LIVE,
        DelegationActionTruthLabel.TRACE_VERIFIED,
    }:
        _reject(
            "P1.8-B cannot claim LIVE or TRACE_VERIFIED truth",
            field="truth_label",
        )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}


def _reason_details() -> dict[str, str]:
    return dict(DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASON_DETAILS)


def _all_false_side_effects() -> DelegationActionBoundarySideEffects:
    return DelegationActionBoundarySideEffects()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _decision_final_allowed(
    state: DelegationOperatorDecisionState,
) -> bool:
    return state == DelegationOperatorDecisionState.APPROVED


def _decision_continuation_allowed(
    state: DelegationOperatorDecisionState,
) -> bool:
    return state == DelegationOperatorDecisionState.APPROVED


def _decision_action_state(
    state: DelegationOperatorDecisionState,
) -> DelegationActionState:
    if state == DelegationOperatorDecisionState.PENDING_REVIEW:
        return DelegationActionState.OPERATOR_REVIEW_PENDING
    if state == DelegationOperatorDecisionState.APPROVED:
        return DelegationActionState.OPERATOR_REVIEWED
    if state == DelegationOperatorDecisionState.REJECTED:
        return DelegationActionState.REJECTED
    if state == DelegationOperatorDecisionState.REVISION_REQUESTED:
        return DelegationActionState.REVISION_REQUESTED
    if state == DelegationOperatorDecisionState.STOPPED:
        return DelegationActionState.STOPPED
    if state == DelegationOperatorDecisionState.EXPIRED:
        return DelegationActionState.EXPIRED
    if state == DelegationOperatorDecisionState.SUPERSEDED:
        return DelegationActionState.SUPERSEDED
    return DelegationActionState.UNKNOWN


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def build_delegation_proposal_boundary(
    *,
    checkpoint_id: str = "P1.8.23",
    boundary_kind: DelegationActionBoundaryKind | str = (
        DelegationActionBoundaryKind.PROPOSAL_NOT_PERMISSION
    ),
    action_state: DelegationActionState | str = DelegationActionState.PROPOSED,
    proposal_ref: str = "proposal:p1.8-b.default",
    desired_action_ref: str = "desired-action:p1.8-b.contract-fixture",
    permission_ref: str | None = None,
    execution_ref: str | None = None,
    proof_ref: str | None = None,
    truth_label: DelegationActionTruthLabel | str = (
        DelegationActionTruthLabel.PROPOSAL_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationActionUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = DELEGATION_PROPOSAL_BOUNDARY_INVARIANTS,
) -> DelegationProposalBoundary:
    boundary_kind_val = _parse_enum(
        DelegationActionBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    action_state_val = _parse_enum(DelegationActionState, action_state, "action_state")
    truth_label_val = _parse_enum(
        DelegationActionTruthLabel,
        truth_label,
        "truth_label",
    )
    _reject_live_or_trace_verified(truth_label_val)
    if permission_ref is not None:
        _reject("proposal cannot contain active permission grant", field="permission_ref")
    if execution_ref is not None:
        _reject("proposal cannot contain execution result", field="execution_ref")
    if proof_ref is not None:
        _reject("proposal cannot claim proof", field="proof_ref")
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_PROPOSAL_BOUNDARY_VERSION,
        "boundary_kind": boundary_kind_val,
        "action_state": action_state_val,
        "proposal_ref": proposal_ref,
        "desired_action_ref": desired_action_ref,
        "permission_ref": permission_ref,
        "execution_ref": execution_ref,
        "proof_ref": proof_ref,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return DelegationProposalBoundary(
        **payload,
        proposal_boundary_hash=_hash_payload(payload),
    )


def build_delegation_permission_boundary(
    *,
    checkpoint_id: str = "P1.8.24",
    boundary_kind: DelegationActionBoundaryKind | str = (
        DelegationActionBoundaryKind.PERMISSION_NOT_EXECUTION
    ),
    action_state: DelegationActionState | str = DelegationActionState.PERMITTED,
    permission_ref: str = "permission:p1.8-b.contract-state",
    proposal_ref: str = "proposal:p1.8-b.default",
    execution_ref: str | None = None,
    proof_ref: str | None = None,
    truth_label: DelegationActionTruthLabel | str = (
        DelegationActionTruthLabel.PERMISSION_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationActionUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = DELEGATION_PERMISSION_BOUNDARY_INVARIANTS,
) -> DelegationPermissionBoundary:
    boundary_kind_val = _parse_enum(
        DelegationActionBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    action_state_val = _parse_enum(DelegationActionState, action_state, "action_state")
    truth_label_val = _parse_enum(
        DelegationActionTruthLabel,
        truth_label,
        "truth_label",
    )
    _reject_live_or_trace_verified(truth_label_val)
    if execution_ref is not None:
        _reject("permission cannot contain execution result", field="execution_ref")
    if proof_ref is not None:
        _reject("permission cannot claim proof", field="proof_ref")
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_PERMISSION_BOUNDARY_VERSION,
        "boundary_kind": boundary_kind_val,
        "action_state": action_state_val,
        "permission_ref": permission_ref,
        "proposal_ref": proposal_ref,
        "execution_ref": execution_ref,
        "proof_ref": proof_ref,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return DelegationPermissionBoundary(
        **payload,
        permission_boundary_hash=_hash_payload(payload),
    )


def build_delegation_execution_proof_boundary(
    *,
    checkpoint_id: str = "P1.8.25",
    boundary_kind: DelegationActionBoundaryKind | str = (
        DelegationActionBoundaryKind.EXECUTION_NOT_PROOF
    ),
    action_state: DelegationActionState | str = DelegationActionState.PROOF_PENDING,
    execution_ref: str = "execution:p1.8-b.recorded-state",
    evidence_ref: str | None = None,
    trace_ref: str | None = None,
    proof_claimed: bool = False,
    trace_verified: bool = False,
    truth_label: DelegationActionTruthLabel | str = (
        DelegationActionTruthLabel.PROOF_PENDING
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationActionUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = DELEGATION_EXECUTION_PROOF_BOUNDARY_INVARIANTS,
) -> DelegationExecutionProofBoundary:
    boundary_kind_val = _parse_enum(
        DelegationActionBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    action_state_val = _parse_enum(DelegationActionState, action_state, "action_state")
    truth_label_val = _parse_enum(
        DelegationActionTruthLabel,
        truth_label,
        "truth_label",
    )
    _reject_live_or_trace_verified(truth_label_val)
    if trace_verified:
        _reject("P1.8-B cannot mark trace verification true", field="trace_verified")
    if proof_claimed and not (evidence_ref or trace_ref):
        _reject(
            "proof claim requires evidence_ref or trace_ref",
            field="proof_claimed",
        )
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_EXECUTION_PROOF_BOUNDARY_VERSION,
        "boundary_kind": boundary_kind_val,
        "action_state": action_state_val,
        "execution_ref": execution_ref,
        "evidence_ref": evidence_ref,
        "trace_ref": trace_ref,
        "proof_claimed": proof_claimed,
        "trace_verified": trace_verified,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return DelegationExecutionProofBoundary(
        **payload,
        execution_proof_boundary_hash=_hash_payload(payload),
    )


def build_operator_delegation_decision_binding(
    *,
    checkpoint_id: str = "P1.8.26",
    boundary_kind: DelegationActionBoundaryKind | str = (
        DelegationActionBoundaryKind.OPERATOR_DECISION_BINDING
    ),
    decision_ref: str = "operator-decision:p1.8-b.pending",
    proposal_ref: str = "proposal:p1.8-b.default",
    permission_ref: str | None = None,
    execution_ref: str | None = None,
    operator_decision_state: DelegationOperatorDecisionState | str = (
        DelegationOperatorDecisionState.PENDING_REVIEW
    ),
    auto_execute: bool = False,
    truth_label: DelegationActionTruthLabel | str = (
        DelegationActionTruthLabel.OPERATOR_DECISION_REQUIRED
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    unavailable_reasons: Sequence[DelegationActionUnavailableReason | str] = (
        DEFAULT_DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASONS
    ),
    invariants: Sequence[str] = OPERATOR_DELEGATION_DECISION_BINDING_INVARIANTS,
) -> OperatorDelegationDecisionBinding:
    boundary_kind_val = _parse_enum(
        DelegationActionBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    decision_state_val = _parse_enum(
        DelegationOperatorDecisionState,
        operator_decision_state,
        "operator_decision_state",
    )
    truth_label_val = _parse_enum(
        DelegationActionTruthLabel,
        truth_label,
        "truth_label",
    )
    _reject_live_or_trace_verified(truth_label_val)
    if auto_execute:
        _reject("operator decision cannot auto-execute", field="auto_execute")
    source_label_val = _parse_source_label(source_label)
    reasons = _parse_unavailable_reasons(unavailable_reasons)
    side_effects = _all_false_side_effects()
    action_state_val = _decision_action_state(decision_state_val)
    final_claim_allowed = _decision_final_allowed(decision_state_val)
    continuation_allowed = _decision_continuation_allowed(decision_state_val)
    payload = {
        "checkpoint_id": checkpoint_id,
        "contract_version": DELEGATION_OPERATOR_DECISION_BINDING_VERSION,
        "boundary_kind": boundary_kind_val,
        "action_state": action_state_val,
        "decision_ref": decision_ref,
        "proposal_ref": proposal_ref,
        "permission_ref": permission_ref,
        "execution_ref": execution_ref,
        "operator_decision_state": decision_state_val,
        "final_claim_allowed": final_claim_allowed,
        "continuation_allowed": continuation_allowed,
        "auto_execute": auto_execute,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
        "unavailable_reasons": reasons,
        "invariants": tuple(invariants),
        "side_effects": side_effects,
    }
    return OperatorDelegationDecisionBinding(
        **payload,
        operator_decision_binding_hash=_hash_payload(payload),
    )


def build_delegation_action_transition_check(
    *,
    source_state: DelegationActionState | str,
    target_state: DelegationActionState | str,
    boundary_kind: DelegationActionBoundaryKind | str,
    verdict: DelegationActionTransitionVerdict | str,
    reason: str,
    truth_label: DelegationActionTruthLabel | str = (
        DelegationActionTruthLabel.CONTRACT_ONLY
    ),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationActionTransitionCheck:
    source_state_val = _parse_enum(
        DelegationActionState,
        source_state,
        "source_state",
    )
    target_state_val = _parse_enum(
        DelegationActionState,
        target_state,
        "target_state",
    )
    boundary_kind_val = _parse_enum(
        DelegationActionBoundaryKind,
        boundary_kind,
        "boundary_kind",
    )
    verdict_val = _parse_enum(
        DelegationActionTransitionVerdict,
        verdict,
        "verdict",
    )
    truth_label_val = _parse_enum(
        DelegationActionTruthLabel,
        truth_label,
        "truth_label",
    )
    _reject_live_or_trace_verified(truth_label_val)
    source_label_val = _parse_source_label(source_label)
    payload = {
        "schema_version": DELEGATION_ACTION_TRANSITION_CHECK_VERSION,
        "source_state": source_state_val,
        "target_state": target_state_val,
        "boundary_kind": boundary_kind_val,
        "verdict": verdict_val,
        "reason": reason,
        "truth_label": truth_label_val,
        "source_label": source_label_val,
    }
    return DelegationActionTransitionCheck(
        **payload,
        transition_check_hash=_hash_payload(payload),
    )


# ---------------------------------------------------------------------------
# Transition guard helpers
# ---------------------------------------------------------------------------


def assert_proposal_is_not_permission(
    proposal: DelegationProposalBoundary,
    *,
    target_state: DelegationActionState | str = DelegationActionState.PROPOSED,
) -> DelegationActionTransitionCheck:
    target_state_val = _parse_enum(DelegationActionState, target_state, "target_state")
    if target_state_val in {
        DelegationActionState.PERMISSION_CANDIDATE,
        DelegationActionState.PERMITTED,
    }:
        _reject(
            "proposal-to-permission semantic collapse rejected",
            field="target_state",
        )
    return build_delegation_action_transition_check(
        source_state=proposal.action_state,
        target_state=target_state_val,
        boundary_kind=proposal.boundary_kind,
        verdict=DelegationActionTransitionVerdict.ALLOWED_AS_CONTRACT_STATE,
        reason="proposal remains proposal-only contract state",
    )


def assert_permission_is_not_execution(
    permission: DelegationPermissionBoundary,
    *,
    target_state: DelegationActionState | str = DelegationActionState.PERMITTED,
) -> DelegationActionTransitionCheck:
    target_state_val = _parse_enum(DelegationActionState, target_state, "target_state")
    if target_state_val in {
        DelegationActionState.EXECUTION_CANDIDATE,
        DelegationActionState.EXECUTED,
    }:
        _reject(
            "permission-to-execution semantic collapse rejected",
            field="target_state",
        )
    return build_delegation_action_transition_check(
        source_state=permission.action_state,
        target_state=target_state_val,
        boundary_kind=permission.boundary_kind,
        verdict=DelegationActionTransitionVerdict.ALLOWED_AS_CONTRACT_STATE,
        reason="permission remains authorization-state contract only",
    )


def assert_execution_is_not_proof(
    execution: DelegationExecutionProofBoundary,
    *,
    target_truth_label: DelegationActionTruthLabel | str = (
        DelegationActionTruthLabel.PROOF_PENDING
    ),
) -> DelegationActionTransitionCheck:
    truth_label_val = _parse_enum(
        DelegationActionTruthLabel,
        target_truth_label,
        "target_truth_label",
    )
    if truth_label_val == DelegationActionTruthLabel.TRACE_VERIFIED:
        _reject(
            "execution-to-proof semantic collapse rejected",
            field="target_truth_label",
        )
    if execution.proof_claimed and not (execution.evidence_ref or execution.trace_ref):
        _reject(
            "execution cannot claim proof without evidence or trace support",
            field="proof_claimed",
        )
    return build_delegation_action_transition_check(
        source_state=execution.action_state,
        target_state=DelegationActionState.PROOF_PENDING,
        boundary_kind=execution.boundary_kind,
        verdict=DelegationActionTransitionVerdict.REQUIRES_EVIDENCE,
        reason="execution remains proof-pending until evidence and trace verification exist",
        truth_label=DelegationActionTruthLabel.PROOF_PENDING,
    )


def assert_operator_decision_is_not_auto_execution(
    binding: OperatorDelegationDecisionBinding,
    *,
    auto_execute: bool = False,
) -> DelegationActionTransitionCheck:
    if auto_execute or binding.auto_execute:
        _reject(
            "operator-approved-to-auto-execution semantic collapse rejected",
            field="auto_execute",
        )
    verdict = (
        DelegationActionTransitionVerdict.ALLOWED_AS_CONTRACT_STATE
        if binding.operator_decision_state == DelegationOperatorDecisionState.APPROVED
        else DelegationActionTransitionVerdict.REQUIRES_OPERATOR_DECISION
    )
    return build_delegation_action_transition_check(
        source_state=binding.action_state,
        target_state=binding.action_state,
        boundary_kind=binding.boundary_kind,
        verdict=verdict,
        reason="operator decision binding does not dispatch execution",
        truth_label=DelegationActionTruthLabel.OPERATOR_DECISION_REQUIRED,
    )


def _build_checkpoint_read(
    *,
    checkpoint_id: str,
    evidence_ref: str,
    contract_hash: str,
    truth_label: DelegationActionTruthLabel,
    unavailable_reasons: Sequence[DelegationActionUnavailableReason],
) -> DelegationActionBoundaryCheckpointRead:
    reasons = tuple(unavailable_reasons)
    payload = {
        "schema_version": DELEGATION_ACTION_BOUNDARY_CHECKPOINT_READ_VERSION,
        "checkpoint_id": checkpoint_id,
        "status": DelegationActionBoundaryStatus.CONTRACT_READY,
        "evidence_ref": evidence_ref,
        "contract_hash": contract_hash,
        "truth_label": truth_label,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": reasons,
    }
    return DelegationActionBoundaryCheckpointRead(
        **payload,
        checkpoint_read_hash=_hash_payload(payload),
    )


def build_default_delegation_action_boundary_read_model(
    *,
    proposal_boundary: DelegationProposalBoundary | None = None,
    permission_boundary: DelegationPermissionBoundary | None = None,
    execution_proof_boundary: DelegationExecutionProofBoundary | None = None,
    operator_decision_binding: OperatorDelegationDecisionBinding | None = None,
) -> DelegationActionBoundaryReadModel:
    proposal = proposal_boundary or build_delegation_proposal_boundary()
    permission = permission_boundary or build_delegation_permission_boundary(
        proposal_ref=proposal.proposal_ref
    )
    execution = execution_proof_boundary or build_delegation_execution_proof_boundary()
    decision = operator_decision_binding or build_operator_delegation_decision_binding(
        proposal_ref=proposal.proposal_ref,
        permission_ref=permission.permission_ref,
    )
    checkpoint_reads = (
        _build_checkpoint_read(
            checkpoint_id="P1.8.23",
            evidence_ref="DelegationProposalBoundary.proposal_boundary_hash",
            contract_hash=proposal.proposal_boundary_hash,
            truth_label=DelegationActionTruthLabel.PROPOSAL_ONLY,
            unavailable_reasons=proposal.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.24",
            evidence_ref="DelegationPermissionBoundary.permission_boundary_hash",
            contract_hash=permission.permission_boundary_hash,
            truth_label=DelegationActionTruthLabel.PERMISSION_ONLY,
            unavailable_reasons=permission.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.25",
            evidence_ref=(
                "DelegationExecutionProofBoundary."
                "execution_proof_boundary_hash"
            ),
            contract_hash=execution.execution_proof_boundary_hash,
            truth_label=DelegationActionTruthLabel.PROOF_PENDING,
            unavailable_reasons=execution.unavailable_reasons,
        ),
        _build_checkpoint_read(
            checkpoint_id="P1.8.26",
            evidence_ref=(
                "OperatorDelegationDecisionBinding."
                "operator_decision_binding_hash"
            ),
            contract_hash=decision.operator_decision_binding_hash,
            truth_label=DelegationActionTruthLabel.OPERATOR_DECISION_REQUIRED,
            unavailable_reasons=decision.unavailable_reasons,
        ),
    )
    side_effects = _all_false_side_effects()
    payload = {
        "schema_version": DELEGATION_ACTION_BOUNDARY_READ_MODEL_VERSION,
        "task_id": DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_count": len(checkpoint_reads),
        "truth_label": DelegationActionTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reason_details": _reason_details(),
        "side_effects": side_effects,
    }
    return DelegationActionBoundaryReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )


def build_p1_8_b_action_boundary_pack_result() -> DelegationActionBoundaryPackResult:
    proposal = build_delegation_proposal_boundary()
    permission = build_delegation_permission_boundary(proposal_ref=proposal.proposal_ref)
    execution = build_delegation_execution_proof_boundary()
    decision = build_operator_delegation_decision_binding(
        proposal_ref=proposal.proposal_ref,
        permission_ref=permission.permission_ref,
    )
    read_model = build_default_delegation_action_boundary_read_model(
        proposal_boundary=proposal,
        permission_boundary=permission,
        execution_proof_boundary=execution,
        operator_decision_binding=decision,
    )
    side_effects = _all_false_side_effects()
    unavailable_reasons = DEFAULT_DELEGATION_ACTION_BOUNDARY_UNAVAILABLE_REASONS
    payload = {
        "schema_version": DELEGATION_ACTION_BOUNDARY_PACK_RESULT_VERSION,
        "task_id": DELEGATION_ACTION_BOUNDARY_PACK_TASK_ID,
        "checkpoint_ids": DELEGATION_ACTION_BOUNDARY_PACK_CHECKPOINT_IDS,
        "proposal_boundary": proposal,
        "permission_boundary": permission,
        "execution_proof_boundary": execution,
        "operator_decision_binding": decision,
        "read_model": read_model,
        "status": DelegationActionBoundaryStatus.CONTRACT_READY,
        "truth_label": DelegationActionTruthLabel.DEV_FIXTURE,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
        "unavailable_reasons": unavailable_reasons,
        "unavailable_reason_details": _reason_details(),
        "side_effects": side_effects,
    }
    return DelegationActionBoundaryPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


# ---------------------------------------------------------------------------
# Hash functions
# ---------------------------------------------------------------------------


def hash_delegation_proposal_boundary(boundary: DelegationProposalBoundary) -> str:
    return boundary.proposal_boundary_hash


def hash_delegation_permission_boundary(boundary: DelegationPermissionBoundary) -> str:
    return boundary.permission_boundary_hash


def hash_delegation_execution_proof_boundary(
    boundary: DelegationExecutionProofBoundary,
) -> str:
    return boundary.execution_proof_boundary_hash


def hash_operator_delegation_decision_binding(
    binding: OperatorDelegationDecisionBinding,
) -> str:
    return binding.operator_decision_binding_hash


def hash_delegation_action_transition_check(
    check: DelegationActionTransitionCheck,
) -> str:
    return check.transition_check_hash


def hash_delegation_action_boundary_read_model(
    read_model: DelegationActionBoundaryReadModel,
) -> str:
    return read_model.read_model_hash


def hash_delegation_action_boundary_pack_result(
    result: DelegationActionBoundaryPackResult,
) -> str:
    return result.result_hash


# ---------------------------------------------------------------------------
# Serialize functions
# ---------------------------------------------------------------------------


def serialize_delegation_action_transition_check(
    check: DelegationActionTransitionCheck,
) -> str:
    payload = check.to_canonical_dict()
    validate_known_fields(
        payload,
        ACTION_TRANSITION_CHECK_KNOWN_FIELDS,
        label="DelegationActionTransitionCheck",
    )
    return to_canonical_json(payload)


def serialize_delegation_action_boundary_read_model(
    read_model: DelegationActionBoundaryReadModel,
) -> str:
    payload = read_model.to_canonical_dict()
    validate_known_fields(
        payload,
        ACTION_BOUNDARY_READ_MODEL_KNOWN_FIELDS,
        label="DelegationActionBoundaryReadModel",
    )
    return to_canonical_json(payload)


def serialize_delegation_action_boundary_pack_result(
    result: DelegationActionBoundaryPackResult,
) -> str:
    payload = result.to_canonical_dict()
    validate_known_fields(
        payload,
        ACTION_BOUNDARY_PACK_RESULT_KNOWN_FIELDS,
        label="DelegationActionBoundaryPackResult",
    )
    return to_canonical_json(payload)
