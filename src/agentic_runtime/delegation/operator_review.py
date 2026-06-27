"""Delegation operator review / approval-intent reference model (P1.8.11).

Deterministic, versioned, JSON-safe, side-effect-free reference-only
operator review and approval-intent metadata layer over P1.8.0-P1.8.10
delegation context.

Produces review refs, approval/rejection/escalation/more-context intent refs,
rationale refs, readiness profile, review envelope, review binding, and review
binding set without actual approval, rejection, escalation, signature
verification, HITL workflow execution, authority grant/deny, policy/Custos
decisioning, runtime allow/block, trace write, Ledger write, or runtime
mutation.

Architectural law:
  - OperatorReviewRef exists does not mean review completed.
  - ApprovalIntentRef exists does not mean approval granted.
  - RejectionIntentRef exists does not mean request denied.
  - EscalationIntentRef exists does not mean escalation executed.
  - MoreContextIntentRef exists does not mean runtime blocked.
  - ReviewRationaleRef exists does not mean rationale verified.
  - OperatorReviewEnvelope exists does not mean approval record.
  - OperatorReviewReadinessProfile exists does not mean approval readiness.
  - Review hash exists does not mean TRACE_VERIFIED.
  - Intent exists does not mean operator decision.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any

from .foundation import (
    DelegationError,
    DelegationErrorCode,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    _optional_string,
    _parse_source_label,
    _required_string,
    stable_hash,
    to_canonical_json,
    validate_known_fields,
)

# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------

DELEGATION_OPERATOR_REVIEW_TASK_ID = "P1.8.11"
DELEGATION_OPERATOR_REVIEW_REF_VERSION = "delegation_operator_review_ref.v1"
DELEGATION_APPROVAL_INTENT_REF_VERSION = "delegation_approval_intent_ref.v1"
DELEGATION_REJECTION_INTENT_REF_VERSION = "delegation_rejection_intent_ref.v1"
DELEGATION_ESCALATION_INTENT_REF_VERSION = "delegation_escalation_intent_ref.v1"
DELEGATION_MORE_CONTEXT_INTENT_REF_VERSION = "delegation_more_context_intent_ref.v1"
DELEGATION_REVIEW_RATIONALE_REF_VERSION = "delegation_review_rationale_ref.v1"
DELEGATION_OPERATOR_REVIEW_READINESS_PROFILE_VERSION = "delegation_operator_review_readiness_profile.v1"
DELEGATION_OPERATOR_REVIEW_ENVELOPE_VERSION = "delegation_operator_review_envelope.v1"
DELEGATION_OPERATOR_REVIEW_BINDING_VERSION = "delegation_operator_review_binding.v1"
DELEGATION_OPERATOR_REVIEW_BINDING_SET_VERSION = "delegation_operator_review_binding_set.v1"
DELEGATION_OPERATOR_REVIEW_SIDE_EFFECTS_VERSION = "delegation_operator_review_side_effects.v1"
DELEGATION_OPERATOR_REVIEW_STATUS_REPORT_VERSION = "delegation_operator_review_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.11; "
        "reference-only metadata layer"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.11"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.11 operator review layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.11 "
        "operator review layer"
    ),
    "Approval Engine": (
        "Approval engine is not available in P1.8.11; "
        "ApprovalIntentRef is reference-only intent, not approval granted"
    ),
    "Rejection Engine": (
        "Rejection engine is not available in P1.8.11; "
        "RejectionIntentRef is reference-only intent, not denial"
    ),
    "Operator Decision System": (
        "Operator decision system is not available in P1.8.11; "
        "review refs are reference-only metadata"
    ),
    "Signature Verifier": (
        "Signature verifier is not available in P1.8.11; "
        "no cryptographic signature verification exists"
    ),
    "HITL Workflow Executor": (
        "HITL workflow executor is not available in P1.8.11; "
        "no human-in-the-loop workflow execution exists"
    ),
    "Authority Grant/Deny": (
        "Authority grant/deny is not available in P1.8.11; "
        "operator review layer does not grant or deny authority"
    ),
    "Policy/Custos Bridge": (
        "Policy/Custos bridge is not available in P1.8.11; "
        "operator review does not call policy or Custos"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision is not available in P1.8.11; "
        "operator review does not make policy decisions"
    ),
    "Runtime Authorization": (
        "Runtime authorization is not available in P1.8.11; "
        "operator review does not authorize runtime"
    ),
    "Runtime Allow/Block": (
        "Runtime allow/block is not available in P1.8.11; "
        "operator review does not allow or block runtime"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.11; "
        "operator review does not write trace events"
    ),
    "P1.8.12 Policy/Custos BridgeRef Model": (
        "P1.8.12 policy/Custos bridge model is not implemented in P1.8.11"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 is not implemented in P1.8.11"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.11; "
        "operator review is reference-only metadata"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world validation)
# ---------------------------------------------------------------------------

OPERATOR_REVIEW_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "review_ref_id",
    "delegation_ref_id",
    "review_kind",
    "review_ref",
    "review_description",
    "reference_status",
    "source_label",
    "review_status",
    "review_hash",
})

APPROVAL_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "approval_intent_ref_id",
    "delegation_ref_id",
    "approval_intent_ref",
    "approval_intent_description",
    "reference_status",
    "source_label",
    "review_status",
    "approval_intent_hash",
})

REJECTION_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "rejection_intent_ref_id",
    "delegation_ref_id",
    "rejection_intent_ref",
    "rejection_intent_description",
    "reference_status",
    "source_label",
    "review_status",
    "rejection_intent_hash",
})

ESCALATION_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "escalation_intent_ref_id",
    "delegation_ref_id",
    "escalation_intent_ref",
    "escalation_intent_description",
    "reference_status",
    "source_label",
    "review_status",
    "escalation_intent_hash",
})

MORE_CONTEXT_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "more_context_intent_ref_id",
    "delegation_ref_id",
    "more_context_intent_ref",
    "more_context_intent_description",
    "reference_status",
    "source_label",
    "review_status",
    "more_context_intent_hash",
})

RATIONALE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "rationale_ref_id",
    "delegation_ref_id",
    "rationale_kind",
    "rationale_ref",
    "rationale_description",
    "source_label",
    "review_status",
    "rationale_hash",
})

REVIEW_READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "operator_review_readiness_profile_id",
    "delegation_ref_id",
    "has_review_refs",
    "has_approval_intent_refs",
    "has_rejection_intent_refs",
    "has_escalation_intent_refs",
    "has_more_context_intent_refs",
    "has_rationale_refs",
    "has_shadow_resolver_context",
    "has_authority_context",
    "has_scope_context",
    "has_evidence_context",
    "missing_components",
    "approval_engine_unavailable_reason",
    "signature_verifier_unavailable_reason",
    "hitl_workflow_unavailable_reason",
    "custos_unavailable_reason",
    "runtime_unavailable_reason",
    "source_label",
    "readiness_hash",
})

OPERATOR_REVIEW_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "operator_review_envelope_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "lifecycle_binding_set_hash",
    "chain_binding_set_hash",
    "shadow_resolver_result_hash",
    "review_ref_ids",
    "approval_intent_ref_ids",
    "rejection_intent_ref_ids",
    "escalation_intent_ref_ids",
    "more_context_intent_ref_ids",
    "rationale_ref_ids",
    "review_readiness_hash",
    "source_label",
    "operator_review_envelope_hash",
})

REVIEW_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "lifecycle_binding_set_hash",
    "chain_binding_set_hash",
    "shadow_resolver_result_hash",
    "operator_review_envelope_hash",
    "review_readiness_hash",
    "source_label",
    "review_status",
    "binding_hash",
})

REVIEW_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "operator_review_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "lifecycle_binding_set_hash",
    "chain_binding_set_hash",
    "shadow_resolver_result_hash",
    "binding_ids",
    "source_label",
    "operator_review_binding_set_hash",
    "side_effects",
})

REVIEW_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "approval_granted",
    "rejection_enforced",
    "escalation_executed",
    "more_context_block_created",
    "operator_decision_recorded",
    "signature_verified",
    "hitl_workflow_started",
    "authority_granted",
    "authority_denied",
    "policy_called",
    "custos_called",
    "runtime_allowed",
    "runtime_blocked",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

REVIEW_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "status_label",
    "available_contracts",
    "unavailable_bindings",
    "side_effects",
    "status_hash",
})

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DelegationOperatorReviewKind(str, Enum):
    """Review kind classifier; does not complete review or record decision."""

    OPERATOR_REVIEW = "OPERATOR_REVIEW"
    CONSISTENCY_REVIEW = "CONSISTENCY_REVIEW"
    AUTHORITY_REVIEW = "AUTHORITY_REVIEW"
    SCOPE_REVIEW = "SCOPE_REVIEW"
    RISK_REVIEW = "RISK_REVIEW"
    EVIDENCE_REVIEW = "EVIDENCE_REVIEW"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationOperatorReviewIntentKind(str, Enum):
    """Intent kind classifier; does not approve, reject, escalate, or block."""

    APPROVAL_INTENT = "APPROVAL_INTENT"
    REJECTION_INTENT = "REJECTION_INTENT"
    ESCALATION_INTENT = "ESCALATION_INTENT"
    MORE_CONTEXT_INTENT = "MORE_CONTEXT_INTENT"
    COMMENT_ONLY = "COMMENT_ONLY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationOperatorReviewReferenceStatus(str, Enum):
    """Reference status ladder; never implies approval/rejection/execution.

    Boundary:
      - REVIEW_REFERENCED is not review completed.
      - APPROVAL_INTENT_REFERENCED is not approved.
      - REJECTION_INTENT_REFERENCED is not denied.
      - ESCALATION_INTENT_REFERENCED is not escalated.
      - MORE_CONTEXT_INTENT_REFERENCED is not runtime block.
      - APPROVAL_ENGINE_UNAVAILABLE is honest unavailability, not approval failure.
      - SIGNATURE_VERIFIER_UNAVAILABLE is honest unavailability, not signature failure.
      - HITL_WORKFLOW_UNAVAILABLE is honest unavailability, not workflow failure.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    REVIEW_REFERENCED = "REVIEW_REFERENCED"
    APPROVAL_INTENT_REFERENCED = "APPROVAL_INTENT_REFERENCED"
    REJECTION_INTENT_REFERENCED = "REJECTION_INTENT_REFERENCED"
    ESCALATION_INTENT_REFERENCED = "ESCALATION_INTENT_REFERENCED"
    MORE_CONTEXT_INTENT_REFERENCED = "MORE_CONTEXT_INTENT_REFERENCED"
    APPROVAL_ENGINE_UNAVAILABLE = "APPROVAL_ENGINE_UNAVAILABLE"
    SIGNATURE_VERIFIER_UNAVAILABLE = "SIGNATURE_VERIFIER_UNAVAILABLE"
    HITL_WORKFLOW_UNAVAILABLE = "HITL_WORKFLOW_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationOperatorReviewStatus(str, Enum):
    """Review declaration status; does not imply decision or approval.

    Boundary:
      - REFERENCE_ONLY means review context is reference-only.
      - DECLARED means review/intent context was declared as metadata.
      - Neither means review completed, approval granted, rejection enforced,
        escalation executed, or operator decision recorded.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationReviewRationaleKind(str, Enum):
    """Rationale kind classifier; does not verify rationale or justify approval.

    Boundary:
      - Rationale kind classifies rationale metadata.
      - It does not verify rationale.
      - It does not justify approval.
      - It does not represent policy/Custos decision.
    """

    CONSISTENCY_CONTEXT = "CONSISTENCY_CONTEXT"
    AUTHORITY_CONTEXT = "AUTHORITY_CONTEXT"
    SCOPE_CONTEXT = "SCOPE_CONTEXT"
    LIFECYCLE_CONTEXT = "LIFECYCLE_CONTEXT"
    CHAIN_CONTEXT = "CHAIN_CONTEXT"
    RISK_CONTEXT = "RISK_CONTEXT"
    OPERATOR_NOTE = "OPERATOR_NOTE"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# SideEffects (plain dataclass, all defaults False)
# ---------------------------------------------------------------------------


@dataclass
class DelegationOperatorReviewSideEffects:
    """Hard proof that P1.8.11 is reference-only, non-approving, non-rejecting,
    non-HITL, non-signing, and non-mutating.  All fields default to False."""

    approval_granted: bool = False
    rejection_enforced: bool = False
    escalation_executed: bool = False
    more_context_block_created: bool = False
    operator_decision_recorded: bool = False
    signature_verified: bool = False
    hitl_workflow_started: bool = False
    authority_granted: bool = False
    authority_denied: bool = False
    policy_called: bool = False
    custos_called: bool = False
    runtime_allowed: bool = False
    runtime_blocked: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False


# ---------------------------------------------------------------------------
# Private enum parsers
# ---------------------------------------------------------------------------


def _parse_operator_review_kind(
    value: DelegationOperatorReviewKind | str,
) -> DelegationOperatorReviewKind:
    if isinstance(value, DelegationOperatorReviewKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationOperatorReviewKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid review_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="review_kind",
            ) from exc
    raise DelegationError(
        "review_kind must be a string or DelegationOperatorReviewKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="review_kind",
    )


def _parse_operator_review_intent_kind(
    value: DelegationOperatorReviewIntentKind | str,
) -> DelegationOperatorReviewIntentKind:
    if isinstance(value, DelegationOperatorReviewIntentKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationOperatorReviewIntentKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid intent_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="intent_kind",
            ) from exc
    raise DelegationError(
        "intent_kind must be a string or DelegationOperatorReviewIntentKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="intent_kind",
    )


def _parse_operator_review_reference_status(
    value: DelegationOperatorReviewReferenceStatus | str,
) -> DelegationOperatorReviewReferenceStatus:
    if isinstance(value, DelegationOperatorReviewReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationOperatorReviewReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationOperatorReviewReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )


def _parse_operator_review_status(
    value: DelegationOperatorReviewStatus | str,
) -> DelegationOperatorReviewStatus:
    if isinstance(value, DelegationOperatorReviewStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationOperatorReviewStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid review_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="review_status",
            ) from exc
    raise DelegationError(
        "review_status must be a string or DelegationOperatorReviewStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="review_status",
    )


def _parse_review_rationale_kind(
    value: DelegationReviewRationaleKind | str,
) -> DelegationReviewRationaleKind:
    if isinstance(value, DelegationReviewRationaleKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationReviewRationaleKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid rationale_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="rationale_kind",
            ) from exc
    raise DelegationError(
        "rationale_kind must be a string or DelegationReviewRationaleKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="rationale_kind",
    )


# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationOperatorReviewRef:
    """One reference-only operator review metadata object.

    Boundary: OperatorReviewRef describes review metadata.
    It does not complete review. It does not record operator decision.
    It does not approve, reject, authorize, deny, enforce, or execute.
    """

    schema_version: str
    review_ref_id: str
    delegation_ref_id: str
    review_kind: DelegationOperatorReviewKind
    review_ref: str | None
    review_description: str
    reference_status: DelegationOperatorReviewReferenceStatus
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    review_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "review_ref_id": self.review_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "review_kind": self.review_kind.value,
            "review_description": self.review_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "review_hash": self.review_hash,
        }
        if self.review_ref is not None:
            result["review_ref"] = self.review_ref
        return result


@dataclass(frozen=True)
class DelegationApprovalIntentRef:
    """One reference-only approval intent metadata object.

    Boundary: ApprovalIntentRef describes approval intent metadata.
    It does not grant approval. It does not authorize runtime.
    It does not grant authority. It does not create approval.
    """

    schema_version: str
    approval_intent_ref_id: str
    delegation_ref_id: str
    approval_intent_ref: str | None
    approval_intent_description: str
    reference_status: DelegationOperatorReviewReferenceStatus
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    approval_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "approval_intent_ref_id": self.approval_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "approval_intent_description": self.approval_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "approval_intent_hash": self.approval_intent_hash,
        }
        if self.approval_intent_ref is not None:
            result["approval_intent_ref"] = self.approval_intent_ref
        return result


@dataclass(frozen=True)
class DelegationRejectionIntentRef:
    """One reference-only rejection intent metadata object.

    Boundary: RejectionIntentRef describes rejection intent metadata.
    It does not deny request. It does not block runtime.
    It does not remove authority. It does not enforce rejection.
    """

    schema_version: str
    rejection_intent_ref_id: str
    delegation_ref_id: str
    rejection_intent_ref: str | None
    rejection_intent_description: str
    reference_status: DelegationOperatorReviewReferenceStatus
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    rejection_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "rejection_intent_ref_id": self.rejection_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "rejection_intent_description": self.rejection_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "rejection_intent_hash": self.rejection_intent_hash,
        }
        if self.rejection_intent_ref is not None:
            result["rejection_intent_ref"] = self.rejection_intent_ref
        return result


@dataclass(frozen=True)
class DelegationEscalationIntentRef:
    """One reference-only escalation intent metadata object.

    Boundary: EscalationIntentRef describes escalation intent metadata.
    It does not execute escalation. It does not route workflow.
    It does not notify humans. It does not start HITL workflow.
    """

    schema_version: str
    escalation_intent_ref_id: str
    delegation_ref_id: str
    escalation_intent_ref: str | None
    escalation_intent_description: str
    reference_status: DelegationOperatorReviewReferenceStatus
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    escalation_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "escalation_intent_ref_id": self.escalation_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "escalation_intent_description": self.escalation_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "escalation_intent_hash": self.escalation_intent_hash,
        }
        if self.escalation_intent_ref is not None:
            result["escalation_intent_ref"] = self.escalation_intent_ref
        return result


@dataclass(frozen=True)
class DelegationMoreContextIntentRef:
    """One reference-only more-context intent metadata object.

    Boundary: MoreContextIntentRef describes a request-for-more-context intent.
    It does not block runtime. It does not deny approval.
    It does not start workflow. It does not request external data.
    """

    schema_version: str
    more_context_intent_ref_id: str
    delegation_ref_id: str
    more_context_intent_ref: str | None
    more_context_intent_description: str
    reference_status: DelegationOperatorReviewReferenceStatus
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    more_context_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "more_context_intent_ref_id": self.more_context_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "more_context_intent_description": self.more_context_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "more_context_intent_hash": self.more_context_intent_hash,
        }
        if self.more_context_intent_ref is not None:
            result["more_context_intent_ref"] = self.more_context_intent_ref
        return result


@dataclass(frozen=True)
class DelegationReviewRationaleRef:
    """One reference-only rationale metadata object.

    Boundary: RationaleRef describes rationale metadata.
    It does not verify rationale truth.
    It does not justify approval.
    It does not prove decision validity.
    It does not represent policy/Custos decision.
    """

    schema_version: str
    rationale_ref_id: str
    delegation_ref_id: str
    rationale_kind: DelegationReviewRationaleKind
    rationale_ref: str | None
    rationale_description: str
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    rationale_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "rationale_ref_id": self.rationale_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "rationale_kind": self.rationale_kind.value,
            "rationale_description": self.rationale_description,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "rationale_hash": self.rationale_hash,
        }
        if self.rationale_ref is not None:
            result["rationale_ref"] = self.rationale_ref
        return result


@dataclass(frozen=True)
class DelegationOperatorReviewReadinessProfile:
    """Present/missing review component profile, not approval/HITL readiness guarantee.

    Boundary: OperatorReviewReadinessProfile is not approval readiness.
    OperatorReviewReadinessProfile is not operator decision.
    OperatorReviewReadinessProfile is not HITL workflow state.
    OperatorReviewReadinessProfile is not runtime safety proof.
    """

    schema_version: str
    operator_review_readiness_profile_id: str
    delegation_ref_id: str
    has_review_refs: bool
    has_approval_intent_refs: bool
    has_rejection_intent_refs: bool
    has_escalation_intent_refs: bool
    has_more_context_intent_refs: bool
    has_rationale_refs: bool
    has_shadow_resolver_context: bool
    has_authority_context: bool
    has_scope_context: bool
    has_evidence_context: bool
    missing_components: tuple[str, ...]
    approval_engine_unavailable_reason: str
    signature_verifier_unavailable_reason: str
    hitl_workflow_unavailable_reason: str
    custos_unavailable_reason: str
    runtime_unavailable_reason: str
    source_label: DelegationSourceLabel
    readiness_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operator_review_readiness_profile_id": (
                self.operator_review_readiness_profile_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "has_review_refs": self.has_review_refs,
            "has_approval_intent_refs": self.has_approval_intent_refs,
            "has_rejection_intent_refs": self.has_rejection_intent_refs,
            "has_escalation_intent_refs": self.has_escalation_intent_refs,
            "has_more_context_intent_refs": self.has_more_context_intent_refs,
            "has_rationale_refs": self.has_rationale_refs,
            "has_shadow_resolver_context": self.has_shadow_resolver_context,
            "has_authority_context": self.has_authority_context,
            "has_scope_context": self.has_scope_context,
            "has_evidence_context": self.has_evidence_context,
            "missing_components": list(self.missing_components),
            "approval_engine_unavailable_reason": (
                self.approval_engine_unavailable_reason
            ),
            "signature_verifier_unavailable_reason": (
                self.signature_verifier_unavailable_reason
            ),
            "hitl_workflow_unavailable_reason": (
                self.hitl_workflow_unavailable_reason
            ),
            "custos_unavailable_reason": self.custos_unavailable_reason,
            "runtime_unavailable_reason": self.runtime_unavailable_reason,
            "source_label": self.source_label.value,
            "readiness_hash": self.readiness_hash,
        }


@dataclass(frozen=True)
class DelegationOperatorReviewEnvelope:
    """Deterministic packet of review refs, intent refs, rationale refs,
    and P1.8 context hashes for one delegation context.

    Boundary: OperatorReviewEnvelope is a reference packet.
    It is not approval record. It is not operator decision.
    It is not HITL workflow state. It is not signature verification.
    It is not TRACE_VERIFIED.
    It does not approve, reject, escalate, authorize, deny, write trace,
    write Ledger, call policy/Custos, or mutate runtime.
    """

    schema_version: str
    operator_review_envelope_id: str
    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_binding_set_hash: str
    lifecycle_binding_set_hash: str
    chain_binding_set_hash: str
    shadow_resolver_result_hash: str
    review_ref_ids: tuple[str, ...]
    approval_intent_ref_ids: tuple[str, ...]
    rejection_intent_ref_ids: tuple[str, ...]
    escalation_intent_ref_ids: tuple[str, ...]
    more_context_intent_ref_ids: tuple[str, ...]
    rationale_ref_ids: tuple[str, ...]
    review_readiness_hash: str
    source_label: DelegationSourceLabel
    operator_review_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operator_review_envelope_id": self.operator_review_envelope_id,
            "delegation_ref_id": self.delegation_ref_id,
            "delegation_identity_hash": self.delegation_identity_hash,
            "role_binding_hash": self.role_binding_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "chain_binding_set_hash": self.chain_binding_set_hash,
            "shadow_resolver_result_hash": self.shadow_resolver_result_hash,
            "review_ref_ids": list(self.review_ref_ids),
            "approval_intent_ref_ids": list(self.approval_intent_ref_ids),
            "rejection_intent_ref_ids": list(self.rejection_intent_ref_ids),
            "escalation_intent_ref_ids": list(self.escalation_intent_ref_ids),
            "more_context_intent_ref_ids": list(self.more_context_intent_ref_ids),
            "rationale_ref_ids": list(self.rationale_ref_ids),
            "review_readiness_hash": self.review_readiness_hash,
            "source_label": self.source_label.value,
            "operator_review_envelope_hash": self.operator_review_envelope_hash,
        }


@dataclass(frozen=True)
class DelegationOperatorReviewBinding:
    """Binding between operator review envelope and delegation context.

    Boundary: OperatorReviewBinding binds review metadata.
    It is not approval. It is not denial.
    It is not operator decision. It is not policy decision.
    It is not trace verification.
    """

    schema_version: str
    binding_id: str
    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_binding_set_hash: str
    lifecycle_binding_set_hash: str
    chain_binding_set_hash: str
    shadow_resolver_result_hash: str
    operator_review_envelope_hash: str
    review_readiness_hash: str
    source_label: DelegationSourceLabel
    review_status: DelegationOperatorReviewStatus
    binding_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "binding_id": self.binding_id,
            "delegation_ref_id": self.delegation_ref_id,
            "delegation_identity_hash": self.delegation_identity_hash,
            "role_binding_hash": self.role_binding_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "chain_binding_set_hash": self.chain_binding_set_hash,
            "shadow_resolver_result_hash": self.shadow_resolver_result_hash,
            "operator_review_envelope_hash": self.operator_review_envelope_hash,
            "review_readiness_hash": self.review_readiness_hash,
            "source_label": self.source_label.value,
            "review_status": self.review_status.value,
            "binding_hash": self.binding_hash,
        }


@dataclass(frozen=True)
class DelegationOperatorReviewBindingSet:
    """Collection of operator review bindings for one delegation.

    Boundary: OperatorReviewBindingSet describes review/intent hooks.
    It does not approve, reject, escalate, verify signature, start HITL
    workflow, authorize runtime, write Ledger/global trace, or mutate runtime.
    """

    schema_version: str
    operator_review_binding_set_id: str
    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_binding_set_hash: str
    lifecycle_binding_set_hash: str
    chain_binding_set_hash: str
    shadow_resolver_result_hash: str
    bindings: tuple[DelegationOperatorReviewBinding, ...]
    source_label: DelegationSourceLabel
    operator_review_binding_set_hash: str
    side_effects: DelegationOperatorReviewSideEffects

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operator_review_binding_set_id": self.operator_review_binding_set_id,
            "delegation_ref_id": self.delegation_ref_id,
            "delegation_identity_hash": self.delegation_identity_hash,
            "role_binding_hash": self.role_binding_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "chain_binding_set_hash": self.chain_binding_set_hash,
            "shadow_resolver_result_hash": self.shadow_resolver_result_hash,
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "source_label": self.source_label.value,
            "operator_review_binding_set_hash": self.operator_review_binding_set_hash,
            "side_effects": {
                "approval_granted": self.side_effects.approval_granted,
                "rejection_enforced": self.side_effects.rejection_enforced,
                "escalation_executed": self.side_effects.escalation_executed,
                "more_context_block_created": self.side_effects.more_context_block_created,
                "operator_decision_recorded": self.side_effects.operator_decision_recorded,
                "signature_verified": self.side_effects.signature_verified,
                "hitl_workflow_started": self.side_effects.hitl_workflow_started,
                "authority_granted": self.side_effects.authority_granted,
                "authority_denied": self.side_effects.authority_denied,
                "policy_called": self.side_effects.policy_called,
                "custos_called": self.side_effects.custos_called,
                "runtime_allowed": self.side_effects.runtime_allowed,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "approval_created": self.side_effects.approval_created,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
        }


@dataclass
class DelegationOperatorReviewStatusReport:
    """Reports operator review model readiness and unavailable surfaces."""

    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: dict[str, str]
    side_effects: DelegationOperatorReviewSideEffects
    status_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status_label": self.status_label,
            "available_contracts": list(self.available_contracts),
            "unavailable_bindings": dict(self.unavailable_bindings),
            "side_effects": {
                "approval_granted": self.side_effects.approval_granted,
                "rejection_enforced": self.side_effects.rejection_enforced,
                "escalation_executed": self.side_effects.escalation_executed,
                "more_context_block_created": self.side_effects.more_context_block_created,
                "operator_decision_recorded": self.side_effects.operator_decision_recorded,
                "signature_verified": self.side_effects.signature_verified,
                "hitl_workflow_started": self.side_effects.hitl_workflow_started,
                "authority_granted": self.side_effects.authority_granted,
                "authority_denied": self.side_effects.authority_denied,
                "policy_called": self.side_effects.policy_called,
                "custos_called": self.side_effects.custos_called,
                "runtime_allowed": self.side_effects.runtime_allowed,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "approval_created": self.side_effects.approval_created,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
            "status_hash": self.status_hash,
        }


# ---------------------------------------------------------------------------
# Private hash computation helpers
# ---------------------------------------------------------------------------


def _compute_operator_review_ref_hash(
    *,
    review_kind: DelegationOperatorReviewKind,
    review_ref: str | None,
    review_description: str,
    reference_status: DelegationOperatorReviewReferenceStatus,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "review_kind": review_kind.value,
        "review_ref": review_ref,
        "review_description": review_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_approval_intent_ref_hash(
    *,
    approval_intent_ref: str | None,
    approval_intent_description: str,
    reference_status: DelegationOperatorReviewReferenceStatus,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "approval_intent_ref": approval_intent_ref,
        "approval_intent_description": approval_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_rejection_intent_ref_hash(
    *,
    rejection_intent_ref: str | None,
    rejection_intent_description: str,
    reference_status: DelegationOperatorReviewReferenceStatus,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "rejection_intent_ref": rejection_intent_ref,
        "rejection_intent_description": rejection_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_escalation_intent_ref_hash(
    *,
    escalation_intent_ref: str | None,
    escalation_intent_description: str,
    reference_status: DelegationOperatorReviewReferenceStatus,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "escalation_intent_ref": escalation_intent_ref,
        "escalation_intent_description": escalation_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_more_context_intent_ref_hash(
    *,
    more_context_intent_ref: str | None,
    more_context_intent_description: str,
    reference_status: DelegationOperatorReviewReferenceStatus,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "more_context_intent_ref": more_context_intent_ref,
        "more_context_intent_description": more_context_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_review_rationale_ref_hash(
    *,
    rationale_kind: DelegationReviewRationaleKind,
    rationale_ref: str | None,
    rationale_description: str,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "rationale_kind": rationale_kind.value,
        "rationale_ref": rationale_ref,
        "rationale_description": rationale_description,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_operator_review_readiness_hash(
    *,
    has_review_refs: bool,
    has_approval_intent_refs: bool,
    has_rejection_intent_refs: bool,
    has_escalation_intent_refs: bool,
    has_more_context_intent_refs: bool,
    has_rationale_refs: bool,
    has_shadow_resolver_context: bool,
    has_authority_context: bool,
    has_scope_context: bool,
    has_evidence_context: bool,
    missing_components: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "has_review_refs": has_review_refs,
        "has_approval_intent_refs": has_approval_intent_refs,
        "has_rejection_intent_refs": has_rejection_intent_refs,
        "has_escalation_intent_refs": has_escalation_intent_refs,
        "has_more_context_intent_refs": has_more_context_intent_refs,
        "has_rationale_refs": has_rationale_refs,
        "has_shadow_resolver_context": has_shadow_resolver_context,
        "has_authority_context": has_authority_context,
        "has_scope_context": has_scope_context,
        "has_evidence_context": has_evidence_context,
        "missing_components": sorted(missing_components),
        "source_label": source_label.value,
    })


def _compute_operator_review_envelope_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_binding_set_hash: str,
    chain_binding_set_hash: str,
    shadow_resolver_result_hash: str,
    review_ref_ids: tuple[str, ...],
    approval_intent_ref_ids: tuple[str, ...],
    rejection_intent_ref_ids: tuple[str, ...],
    escalation_intent_ref_ids: tuple[str, ...],
    more_context_intent_ref_ids: tuple[str, ...],
    rationale_ref_ids: tuple[str, ...],
    review_readiness_hash: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "delegation_identity_hash": delegation_identity_hash,
        "role_binding_hash": role_binding_hash,
        "constraint_set_hash": constraint_set_hash,
        "authority_binding_set_hash": authority_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "scope_binding_set_hash": scope_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "chain_binding_set_hash": chain_binding_set_hash,
        "shadow_resolver_result_hash": shadow_resolver_result_hash,
        "review_ref_ids": sorted(review_ref_ids),
        "approval_intent_ref_ids": sorted(approval_intent_ref_ids),
        "rejection_intent_ref_ids": sorted(rejection_intent_ref_ids),
        "escalation_intent_ref_ids": sorted(escalation_intent_ref_ids),
        "more_context_intent_ref_ids": sorted(more_context_intent_ref_ids),
        "rationale_ref_ids": sorted(rationale_ref_ids),
        "review_readiness_hash": review_readiness_hash,
        "source_label": source_label.value,
    })


def _compute_operator_review_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_binding_set_hash: str,
    chain_binding_set_hash: str,
    shadow_resolver_result_hash: str,
    operator_review_envelope_hash: str,
    review_readiness_hash: str,
    source_label: DelegationSourceLabel,
    review_status: DelegationOperatorReviewStatus,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "delegation_identity_hash": delegation_identity_hash,
        "role_binding_hash": role_binding_hash,
        "constraint_set_hash": constraint_set_hash,
        "authority_binding_set_hash": authority_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "scope_binding_set_hash": scope_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "chain_binding_set_hash": chain_binding_set_hash,
        "shadow_resolver_result_hash": shadow_resolver_result_hash,
        "operator_review_envelope_hash": operator_review_envelope_hash,
        "review_readiness_hash": review_readiness_hash,
        "source_label": source_label.value,
        "review_status": review_status.value,
    })


def _compute_operator_review_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_binding_set_hash: str,
    chain_binding_set_hash: str,
    shadow_resolver_result_hash: str,
    binding_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationOperatorReviewSideEffects,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "delegation_identity_hash": delegation_identity_hash,
        "role_binding_hash": role_binding_hash,
        "constraint_set_hash": constraint_set_hash,
        "authority_binding_set_hash": authority_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "scope_binding_set_hash": scope_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "chain_binding_set_hash": chain_binding_set_hash,
        "shadow_resolver_result_hash": shadow_resolver_result_hash,
        "binding_hashes": sorted(binding_hashes),
        "source_label": source_label.value,
        "side_effects": {
            "approval_granted": side_effects.approval_granted,
            "rejection_enforced": side_effects.rejection_enforced,
            "escalation_executed": side_effects.escalation_executed,
            "more_context_block_created": side_effects.more_context_block_created,
            "operator_decision_recorded": side_effects.operator_decision_recorded,
            "signature_verified": side_effects.signature_verified,
            "hitl_workflow_started": side_effects.hitl_workflow_started,
            "authority_granted": side_effects.authority_granted,
            "authority_denied": side_effects.authority_denied,
            "policy_called": side_effects.policy_called,
            "custos_called": side_effects.custos_called,
            "runtime_allowed": side_effects.runtime_allowed,
            "runtime_blocked": side_effects.runtime_blocked,
            "approval_created": side_effects.approval_created,
            "ledger_written": side_effects.ledger_written,
            "global_trace_written": side_effects.global_trace_written,
            "runtime_mutated": side_effects.runtime_mutated,
        },
    })


def _compute_operator_review_status_report_hash(
    *,
    available_contracts: tuple[str, ...],
    side_effects: DelegationOperatorReviewSideEffects,
) -> str:
    return stable_hash({
        "available_contracts": sorted(available_contracts),
        "side_effects": {
            "approval_granted": side_effects.approval_granted,
            "rejection_enforced": side_effects.rejection_enforced,
            "escalation_executed": side_effects.escalation_executed,
            "more_context_block_created": side_effects.more_context_block_created,
            "operator_decision_recorded": side_effects.operator_decision_recorded,
            "signature_verified": side_effects.signature_verified,
            "hitl_workflow_started": side_effects.hitl_workflow_started,
            "authority_granted": side_effects.authority_granted,
            "authority_denied": side_effects.authority_denied,
            "policy_called": side_effects.policy_called,
            "custos_called": side_effects.custos_called,
            "runtime_allowed": side_effects.runtime_allowed,
            "runtime_blocked": side_effects.runtime_blocked,
            "approval_created": side_effects.approval_created,
            "ledger_written": side_effects.ledger_written,
            "global_trace_written": side_effects.global_trace_written,
            "runtime_mutated": side_effects.runtime_mutated,
        },
    })


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_delegation_operator_review_ref(
    *,
    delegation_ref_id: str,
    review_kind: DelegationOperatorReviewKind | str = DelegationOperatorReviewKind.REFERENCE_ONLY,
    review_ref: str | None = None,
    review_description: str = "",
    reference_status: DelegationOperatorReviewReferenceStatus | str = DelegationOperatorReviewReferenceStatus.REVIEW_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    review_ref_id: str | None = None,
) -> DelegationOperatorReviewRef:
    """Build a DelegationOperatorReviewRef."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_kind = _parse_operator_review_kind(review_kind)
    parsed_ref_status = _parse_operator_review_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)
    review_ref_clean = _optional_string(review_ref)

    if review_ref_id is None:
        review_ref_id = f"or-review-{delegation_ref_id[:12]}"

    review_hash = _compute_operator_review_ref_hash(
        review_kind=parsed_kind,
        review_ref=review_ref_clean,
        review_description=review_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationOperatorReviewRef(
        schema_version=DELEGATION_OPERATOR_REVIEW_REF_VERSION,
        review_ref_id=review_ref_id,
        delegation_ref_id=delegation_ref_id,
        review_kind=parsed_kind,
        review_ref=review_ref_clean,
        review_description=review_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
        review_hash=review_hash,
    )


def build_delegation_approval_intent_ref(
    *,
    delegation_ref_id: str,
    approval_intent_ref: str | None = None,
    approval_intent_description: str = "",
    reference_status: DelegationOperatorReviewReferenceStatus | str = DelegationOperatorReviewReferenceStatus.APPROVAL_INTENT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    approval_intent_ref_id: str | None = None,
) -> DelegationApprovalIntentRef:
    """Build a DelegationApprovalIntentRef — reference-only, not approval."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_operator_review_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)
    approval_intent_ref_clean = _optional_string(approval_intent_ref)

    if approval_intent_ref_id is None:
        approval_intent_ref_id = f"or-approval-{delegation_ref_id[:12]}"

    approval_intent_hash = _compute_approval_intent_ref_hash(
        approval_intent_ref=approval_intent_ref_clean,
        approval_intent_description=approval_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationApprovalIntentRef(
        schema_version=DELEGATION_APPROVAL_INTENT_REF_VERSION,
        approval_intent_ref_id=approval_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        approval_intent_ref=approval_intent_ref_clean,
        approval_intent_description=approval_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
        approval_intent_hash=approval_intent_hash,
    )


def build_delegation_rejection_intent_ref(
    *,
    delegation_ref_id: str,
    rejection_intent_ref: str | None = None,
    rejection_intent_description: str = "",
    reference_status: DelegationOperatorReviewReferenceStatus | str = DelegationOperatorReviewReferenceStatus.REJECTION_INTENT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    rejection_intent_ref_id: str | None = None,
) -> DelegationRejectionIntentRef:
    """Build a DelegationRejectionIntentRef — reference-only, not denial."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_operator_review_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)
    rejection_intent_ref_clean = _optional_string(rejection_intent_ref)

    if rejection_intent_ref_id is None:
        rejection_intent_ref_id = f"or-rejection-{delegation_ref_id[:12]}"

    rejection_intent_hash = _compute_rejection_intent_ref_hash(
        rejection_intent_ref=rejection_intent_ref_clean,
        rejection_intent_description=rejection_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationRejectionIntentRef(
        schema_version=DELEGATION_REJECTION_INTENT_REF_VERSION,
        rejection_intent_ref_id=rejection_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        rejection_intent_ref=rejection_intent_ref_clean,
        rejection_intent_description=rejection_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
        rejection_intent_hash=rejection_intent_hash,
    )


def build_delegation_escalation_intent_ref(
    *,
    delegation_ref_id: str,
    escalation_intent_ref: str | None = None,
    escalation_intent_description: str = "",
    reference_status: DelegationOperatorReviewReferenceStatus | str = DelegationOperatorReviewReferenceStatus.ESCALATION_INTENT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    escalation_intent_ref_id: str | None = None,
) -> DelegationEscalationIntentRef:
    """Build a DelegationEscalationIntentRef — reference-only, not escalation."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_operator_review_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)
    escalation_intent_ref_clean = _optional_string(escalation_intent_ref)

    if escalation_intent_ref_id is None:
        escalation_intent_ref_id = f"or-escalation-{delegation_ref_id[:12]}"

    escalation_intent_hash = _compute_escalation_intent_ref_hash(
        escalation_intent_ref=escalation_intent_ref_clean,
        escalation_intent_description=escalation_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationEscalationIntentRef(
        schema_version=DELEGATION_ESCALATION_INTENT_REF_VERSION,
        escalation_intent_ref_id=escalation_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        escalation_intent_ref=escalation_intent_ref_clean,
        escalation_intent_description=escalation_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
        escalation_intent_hash=escalation_intent_hash,
    )


def build_delegation_more_context_intent_ref(
    *,
    delegation_ref_id: str,
    more_context_intent_ref: str | None = None,
    more_context_intent_description: str = "",
    reference_status: DelegationOperatorReviewReferenceStatus | str = DelegationOperatorReviewReferenceStatus.MORE_CONTEXT_INTENT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    more_context_intent_ref_id: str | None = None,
) -> DelegationMoreContextIntentRef:
    """Build a DelegationMoreContextIntentRef — reference-only, not runtime block."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_operator_review_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)
    more_context_intent_ref_clean = _optional_string(more_context_intent_ref)

    if more_context_intent_ref_id is None:
        more_context_intent_ref_id = f"or-morecontext-{delegation_ref_id[:12]}"

    more_context_intent_hash = _compute_more_context_intent_ref_hash(
        more_context_intent_ref=more_context_intent_ref_clean,
        more_context_intent_description=more_context_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationMoreContextIntentRef(
        schema_version=DELEGATION_MORE_CONTEXT_INTENT_REF_VERSION,
        more_context_intent_ref_id=more_context_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        more_context_intent_ref=more_context_intent_ref_clean,
        more_context_intent_description=more_context_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        review_status=parsed_review_status,
        more_context_intent_hash=more_context_intent_hash,
    )


def build_delegation_review_rationale_ref(
    *,
    delegation_ref_id: str,
    rationale_kind: DelegationReviewRationaleKind | str = DelegationReviewRationaleKind.OPERATOR_NOTE,
    rationale_ref: str | None = None,
    rationale_description: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    rationale_ref_id: str | None = None,
) -> DelegationReviewRationaleRef:
    """Build a DelegationReviewRationaleRef — reference-only, not verified."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_rationale_kind = _parse_review_rationale_kind(rationale_kind)
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)
    rationale_ref_clean = _optional_string(rationale_ref)

    if rationale_ref_id is None:
        rationale_ref_id = f"or-rationale-{delegation_ref_id[:12]}"

    rationale_hash = _compute_review_rationale_ref_hash(
        rationale_kind=parsed_rationale_kind,
        rationale_ref=rationale_ref_clean,
        rationale_description=rationale_description,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationReviewRationaleRef(
        schema_version=DELEGATION_REVIEW_RATIONALE_REF_VERSION,
        rationale_ref_id=rationale_ref_id,
        delegation_ref_id=delegation_ref_id,
        rationale_kind=parsed_rationale_kind,
        rationale_ref=rationale_ref_clean,
        rationale_description=rationale_description,
        source_label=parsed_label,
        review_status=parsed_review_status,
        rationale_hash=rationale_hash,
    )


def build_delegation_operator_review_readiness_profile(
    *,
    delegation_ref_id: str,
    has_review_refs: bool = False,
    has_approval_intent_refs: bool = False,
    has_rejection_intent_refs: bool = False,
    has_escalation_intent_refs: bool = False,
    has_more_context_intent_refs: bool = False,
    has_rationale_refs: bool = False,
    has_shadow_resolver_context: bool = False,
    has_authority_context: bool = False,
    has_scope_context: bool = False,
    has_evidence_context: bool = False,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    operator_review_readiness_profile_id: str | None = None,
) -> DelegationOperatorReviewReadinessProfile:
    """Build a DelegationOperatorReviewReadinessProfile."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)

    missing: list[str] = []
    if not has_review_refs:
        missing.append("review_refs")
    if not has_approval_intent_refs:
        missing.append("approval_intent_refs")
    if not has_rejection_intent_refs:
        missing.append("rejection_intent_refs")
    if not has_escalation_intent_refs:
        missing.append("escalation_intent_refs")
    if not has_more_context_intent_refs:
        missing.append("more_context_intent_refs")
    if not has_rationale_refs:
        missing.append("rationale_refs")
    if not has_shadow_resolver_context:
        missing.append("shadow_resolver_context")
    if not has_authority_context:
        missing.append("authority_context")
    if not has_scope_context:
        missing.append("scope_context")
    if not has_evidence_context:
        missing.append("evidence_context")

    missing_tuple = tuple(sorted(missing))

    if operator_review_readiness_profile_id is None:
        operator_review_readiness_profile_id = f"or-readiness-{delegation_ref_id[:12]}"

    readiness_hash = _compute_operator_review_readiness_hash(
        has_review_refs=has_review_refs,
        has_approval_intent_refs=has_approval_intent_refs,
        has_rejection_intent_refs=has_rejection_intent_refs,
        has_escalation_intent_refs=has_escalation_intent_refs,
        has_more_context_intent_refs=has_more_context_intent_refs,
        has_rationale_refs=has_rationale_refs,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_scope_context=has_scope_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_tuple,
        source_label=parsed_label,
    )

    return DelegationOperatorReviewReadinessProfile(
        schema_version=DELEGATION_OPERATOR_REVIEW_READINESS_PROFILE_VERSION,
        operator_review_readiness_profile_id=operator_review_readiness_profile_id,
        delegation_ref_id=delegation_ref_id,
        has_review_refs=has_review_refs,
        has_approval_intent_refs=has_approval_intent_refs,
        has_rejection_intent_refs=has_rejection_intent_refs,
        has_escalation_intent_refs=has_escalation_intent_refs,
        has_more_context_intent_refs=has_more_context_intent_refs,
        has_rationale_refs=has_rationale_refs,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_scope_context=has_scope_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_tuple,
        approval_engine_unavailable_reason=(
            "Approval engine is not available in P1.8.11; "
            "ApprovalIntentRef is reference-only intent, not approval granted"
        ),
        signature_verifier_unavailable_reason=(
            "Signature verifier is not available in P1.8.11; "
            "no cryptographic signature verification exists"
        ),
        hitl_workflow_unavailable_reason=(
            "HITL workflow executor is not available in P1.8.11; "
            "no human-in-the-loop workflow execution exists"
        ),
        custos_unavailable_reason=(
            "Custos resolver is not available in P1.8.11; "
            "operator review does not call Custos"
        ),
        runtime_unavailable_reason=(
            "Runtime delegation execution is not available in P1.8.11; "
            "operator review is reference-only metadata"
        ),
        source_label=parsed_label,
        readiness_hash=readiness_hash,
    )


def build_delegation_operator_review_envelope(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str = "0000000000000000000000000000000000000000",
    role_binding_hash: str = "0000000000000000000000000000000000000000",
    constraint_set_hash: str = "0000000000000000000000000000000000000000",
    authority_binding_set_hash: str = "0000000000000000000000000000000000000000",
    non_repudiation_binding_set_hash: str = "0000000000000000000000000000000000000000",
    identity_mesh_binding_set_hash: str = "0000000000000000000000000000000000000000",
    scope_binding_set_hash: str = "0000000000000000000000000000000000000000",
    lifecycle_binding_set_hash: str = "0000000000000000000000000000000000000000",
    chain_binding_set_hash: str = "0000000000000000000000000000000000000000",
    shadow_resolver_result_hash: str = "0000000000000000000000000000000000000000",
    review_refs: Sequence[DelegationOperatorReviewRef] = (),
    approval_intent_refs: Sequence[DelegationApprovalIntentRef] = (),
    rejection_intent_refs: Sequence[DelegationRejectionIntentRef] = (),
    escalation_intent_refs: Sequence[DelegationEscalationIntentRef] = (),
    more_context_intent_refs: Sequence[DelegationMoreContextIntentRef] = (),
    rationale_refs: Sequence[DelegationReviewRationaleRef] = (),
    readiness_profile: DelegationOperatorReviewReadinessProfile | None = None,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    operator_review_envelope_id: str | None = None,
) -> DelegationOperatorReviewEnvelope:
    """Build a DelegationOperatorReviewEnvelope."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    _required_string(delegation_identity_hash, field_name="delegation_identity_hash")
    _required_string(role_binding_hash, field_name="role_binding_hash")
    _required_string(constraint_set_hash, field_name="constraint_set_hash")
    _required_string(authority_binding_set_hash, field_name="authority_binding_set_hash")
    _required_string(non_repudiation_binding_set_hash, field_name="non_repudiation_binding_set_hash")
    _required_string(identity_mesh_binding_set_hash, field_name="identity_mesh_binding_set_hash")
    _required_string(scope_binding_set_hash, field_name="scope_binding_set_hash")
    _required_string(lifecycle_binding_set_hash, field_name="lifecycle_binding_set_hash")
    _required_string(chain_binding_set_hash, field_name="chain_binding_set_hash")
    _required_string(shadow_resolver_result_hash, field_name="shadow_resolver_result_hash")
    parsed_label = _parse_source_label(source_label)

    review_ref_ids = tuple(sorted(r.review_ref_id for r in review_refs))
    approval_intent_ref_ids = tuple(sorted(r.approval_intent_ref_id for r in approval_intent_refs))
    rejection_intent_ref_ids = tuple(sorted(r.rejection_intent_ref_id for r in rejection_intent_refs))
    escalation_intent_ref_ids = tuple(sorted(r.escalation_intent_ref_id for r in escalation_intent_refs))
    more_context_intent_ref_ids = tuple(sorted(r.more_context_intent_ref_id for r in more_context_intent_refs))
    rationale_ref_ids = tuple(sorted(r.rationale_ref_id for r in rationale_refs))

    if readiness_profile is None:
        review_readiness_hash = "0000000000000000000000000000000000000000"
    else:
        review_readiness_hash = readiness_profile.readiness_hash

    if operator_review_envelope_id is None:
        operator_review_envelope_id = f"or-envelope-{delegation_ref_id[:12]}"

    envelope_hash = _compute_operator_review_envelope_hash(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        review_ref_ids=review_ref_ids,
        approval_intent_ref_ids=approval_intent_ref_ids,
        rejection_intent_ref_ids=rejection_intent_ref_ids,
        escalation_intent_ref_ids=escalation_intent_ref_ids,
        more_context_intent_ref_ids=more_context_intent_ref_ids,
        rationale_ref_ids=rationale_ref_ids,
        review_readiness_hash=review_readiness_hash,
        source_label=parsed_label,
    )

    return DelegationOperatorReviewEnvelope(
        schema_version=DELEGATION_OPERATOR_REVIEW_ENVELOPE_VERSION,
        operator_review_envelope_id=operator_review_envelope_id,
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        review_ref_ids=review_ref_ids,
        approval_intent_ref_ids=approval_intent_ref_ids,
        rejection_intent_ref_ids=rejection_intent_ref_ids,
        escalation_intent_ref_ids=escalation_intent_ref_ids,
        more_context_intent_ref_ids=more_context_intent_ref_ids,
        rationale_ref_ids=rationale_ref_ids,
        review_readiness_hash=review_readiness_hash,
        source_label=parsed_label,
        operator_review_envelope_hash=envelope_hash,
    )


def build_delegation_operator_review_binding(
    *,
    delegation_ref_id: str,
    envelope: DelegationOperatorReviewEnvelope,
    delegation_identity_hash: str = "0000000000000000000000000000000000000000",
    role_binding_hash: str = "0000000000000000000000000000000000000000",
    constraint_set_hash: str = "0000000000000000000000000000000000000000",
    authority_binding_set_hash: str = "0000000000000000000000000000000000000000",
    non_repudiation_binding_set_hash: str = "0000000000000000000000000000000000000000",
    identity_mesh_binding_set_hash: str = "0000000000000000000000000000000000000000",
    scope_binding_set_hash: str = "0000000000000000000000000000000000000000",
    lifecycle_binding_set_hash: str = "0000000000000000000000000000000000000000",
    chain_binding_set_hash: str = "0000000000000000000000000000000000000000",
    shadow_resolver_result_hash: str = "0000000000000000000000000000000000000000",
    review_readiness_hash: str = "0000000000000000000000000000000000000000",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    review_status: DelegationOperatorReviewStatus | str = DelegationOperatorReviewStatus.DECLARED,
    binding_id: str | None = None,
) -> DelegationOperatorReviewBinding:
    """Build a DelegationOperatorReviewBinding."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    _required_string(delegation_identity_hash, field_name="delegation_identity_hash")
    _required_string(role_binding_hash, field_name="role_binding_hash")
    _required_string(constraint_set_hash, field_name="constraint_set_hash")
    _required_string(authority_binding_set_hash, field_name="authority_binding_set_hash")
    _required_string(non_repudiation_binding_set_hash, field_name="non_repudiation_binding_set_hash")
    _required_string(identity_mesh_binding_set_hash, field_name="identity_mesh_binding_set_hash")
    _required_string(scope_binding_set_hash, field_name="scope_binding_set_hash")
    _required_string(lifecycle_binding_set_hash, field_name="lifecycle_binding_set_hash")
    _required_string(chain_binding_set_hash, field_name="chain_binding_set_hash")
    _required_string(shadow_resolver_result_hash, field_name="shadow_resolver_result_hash")
    _required_string(review_readiness_hash, field_name="review_readiness_hash")
    parsed_label = _parse_source_label(source_label)
    parsed_review_status = _parse_operator_review_status(review_status)

    if binding_id is None:
        binding_id = f"or-binding-{delegation_ref_id[:12]}"

    binding_hash = _compute_operator_review_binding_hash(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_envelope_hash=envelope.operator_review_envelope_hash,
        review_readiness_hash=review_readiness_hash,
        source_label=parsed_label,
        review_status=parsed_review_status,
    )

    return DelegationOperatorReviewBinding(
        schema_version=DELEGATION_OPERATOR_REVIEW_BINDING_VERSION,
        binding_id=binding_id,
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_envelope_hash=envelope.operator_review_envelope_hash,
        review_readiness_hash=review_readiness_hash,
        source_label=parsed_label,
        review_status=parsed_review_status,
        binding_hash=binding_hash,
    )


def build_delegation_operator_review_binding_set(
    *,
    delegation_ref_id: str,
    bindings: Sequence[DelegationOperatorReviewBinding],
    delegation_identity_hash: str = "0000000000000000000000000000000000000000",
    role_binding_hash: str = "0000000000000000000000000000000000000000",
    constraint_set_hash: str = "0000000000000000000000000000000000000000",
    authority_binding_set_hash: str = "0000000000000000000000000000000000000000",
    non_repudiation_binding_set_hash: str = "0000000000000000000000000000000000000000",
    identity_mesh_binding_set_hash: str = "0000000000000000000000000000000000000000",
    scope_binding_set_hash: str = "0000000000000000000000000000000000000000",
    lifecycle_binding_set_hash: str = "0000000000000000000000000000000000000000",
    chain_binding_set_hash: str = "0000000000000000000000000000000000000000",
    shadow_resolver_result_hash: str = "0000000000000000000000000000000000000000",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    operator_review_binding_set_id: str | None = None,
) -> DelegationOperatorReviewBindingSet:
    """Build a DelegationOperatorReviewBindingSet."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)
    side_effects = DelegationOperatorReviewSideEffects()

    ordered_bindings = tuple(sorted(bindings, key=lambda b: b.binding_id))
    binding_hashes = tuple(b.binding_hash for b in ordered_bindings)

    if operator_review_binding_set_id is None:
        operator_review_binding_set_id = f"or-bindingset-{delegation_ref_id[:12]}"

    binding_set_hash = _compute_operator_review_binding_set_hash(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        binding_hashes=binding_hashes,
        source_label=parsed_label,
        side_effects=side_effects,
    )

    return DelegationOperatorReviewBindingSet(
        schema_version=DELEGATION_OPERATOR_REVIEW_BINDING_SET_VERSION,
        operator_review_binding_set_id=operator_review_binding_set_id,
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        bindings=ordered_bindings,
        source_label=parsed_label,
        operator_review_binding_set_hash=binding_set_hash,
        side_effects=side_effects,
    )


def build_delegation_operator_review_status_report(
    *,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.LIVE,
) -> DelegationOperatorReviewStatusReport:
    """Build a DelegationOperatorReviewStatusReport."""
    _parse_source_label(source_label)
    side_effects = DelegationOperatorReviewSideEffects()

    available = (
        "DelegationOperatorReviewRef",
        "DelegationApprovalIntentRef",
        "DelegationRejectionIntentRef",
        "DelegationEscalationIntentRef",
        "DelegationMoreContextIntentRef",
        "DelegationReviewRationaleRef",
        "DelegationOperatorReviewReadinessProfile",
        "DelegationOperatorReviewEnvelope",
        "DelegationOperatorReviewBinding",
        "DelegationOperatorReviewBindingSet",
        "DelegationOperatorReviewSideEffects",
        "DelegationOperatorReviewStatusReport",
    )

    status_hash = _compute_operator_review_status_report_hash(
        available_contracts=available,
        side_effects=side_effects,
    )

    return DelegationOperatorReviewStatusReport(
        schema_version=DELEGATION_OPERATOR_REVIEW_STATUS_REPORT_VERSION,
        status_label="Delegation Operator Review / ApprovalIntentRef Model — Reference Only",
        available_contracts=available,
        unavailable_bindings=dict(DELEGATION_OPERATOR_REVIEW_UNAVAILABLE_BINDINGS),
        side_effects=side_effects,
        status_hash=status_hash,
    )


# ---------------------------------------------------------------------------
# Serialize helpers
# ---------------------------------------------------------------------------


def serialize_delegation_operator_review_envelope(
    envelope: DelegationOperatorReviewEnvelope,
) -> str:
    """Serialize a DelegationOperatorReviewEnvelope to deterministic JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_operator_review_binding_set(
    binding_set: DelegationOperatorReviewBindingSet,
) -> str:
    """Serialize a DelegationOperatorReviewBindingSet to deterministic JSON."""
    return to_canonical_json(binding_set)


# ---------------------------------------------------------------------------
# Convenience hash wrappers
# ---------------------------------------------------------------------------


def hash_delegation_operator_review_ref(
    review_ref: DelegationOperatorReviewRef,
) -> str:
    """Return the precomputed review_hash."""
    return review_ref.review_hash


def hash_delegation_approval_intent_ref(
    approval_intent_ref: DelegationApprovalIntentRef,
) -> str:
    """Return the precomputed approval_intent_hash."""
    return approval_intent_ref.approval_intent_hash


def hash_delegation_rejection_intent_ref(
    rejection_intent_ref: DelegationRejectionIntentRef,
) -> str:
    """Return the precomputed rejection_intent_hash."""
    return rejection_intent_ref.rejection_intent_hash


def hash_delegation_escalation_intent_ref(
    escalation_intent_ref: DelegationEscalationIntentRef,
) -> str:
    """Return the precomputed escalation_intent_hash."""
    return escalation_intent_ref.escalation_intent_hash


def hash_delegation_more_context_intent_ref(
    more_context_intent_ref: DelegationMoreContextIntentRef,
) -> str:
    """Return the precomputed more_context_intent_hash."""
    return more_context_intent_ref.more_context_intent_hash


def hash_delegation_review_rationale_ref(
    rationale_ref: DelegationReviewRationaleRef,
) -> str:
    """Return the precomputed rationale_hash."""
    return rationale_ref.rationale_hash


def hash_delegation_operator_review_readiness_profile(
    profile: DelegationOperatorReviewReadinessProfile,
) -> str:
    """Return the precomputed readiness_hash."""
    return profile.readiness_hash


def hash_delegation_operator_review_envelope(
    envelope: DelegationOperatorReviewEnvelope,
) -> str:
    """Return the precomputed operator_review_envelope_hash."""
    return envelope.operator_review_envelope_hash


def hash_delegation_operator_review_binding(
    binding: DelegationOperatorReviewBinding,
) -> str:
    """Return the precomputed binding_hash."""
    return binding.binding_hash


def hash_delegation_operator_review_binding_set(
    binding_set: DelegationOperatorReviewBindingSet,
) -> str:
    """Return the precomputed operator_review_binding_set_hash."""
    return binding_set.operator_review_binding_set_hash


def hash_delegation_operator_review_status_report(
    report: DelegationOperatorReviewStatusReport,
) -> str:
    """Return the precomputed status_hash."""
    return report.status_hash
