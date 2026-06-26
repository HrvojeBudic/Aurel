"""Delegation chain / handoff reference model (P1.8.9).

Deterministic, versioned, JSON-safe, side-effect-free delegation chain
and handoff reference layer. Binds reference-only chain refs, predecessor
refs, successor refs, handoff refs, handoff claim refs, acceptance claim
refs, responsibility transfer claim refs, a reference-only lineage map,
a chain continuity readiness profile, and a chain envelope to
DelegationRef / DelegationIdentity / DelegationRoleBindingSet /
DelegationConstraintSet / DelegationAuthorityBindingSet /
DelegationNonRepudiationBindingSet / DelegationIdentityMeshBindingSet /
DelegationScopeBindingSet / DelegationLifecycleBindingSet without
live handoff, responsibility transfer, authority transfer, acceptance
verification, predecessor/successor verification, successor activation,
chain verification, runtime owner mutation, policy/Custos decisioning,
trace write, Ledger write, or runtime mutation.

Architectural law:
  - DelegationChainRef exists does not mean chain is verified.
  - DelegationHandoffRef exists does not mean handoff was executed.
  - PredecessorRef exists does not mean predecessor is valid.
  - SuccessorRef exists does not mean successor is activated.
  - HandoffClaimRef exists does not mean handoff occurred.
  - AcceptanceClaimRef exists does not mean acceptance is verified.
  - ResponsibilityTransferClaimRef exists does not mean responsibility
    was transferred.
  - LineageMap exists does not mean graph engine exists.
  - ContinuityReadinessProfile exists does not mean continuity is proven.
  - Chain hash exists does not mean TRACE_VERIFIED.
  - DelegationChainRef exists ≠ chain verified.
  - DelegationHandoffRef exists ≠ handoff executed.
  - DelegationPredecessorRef exists ≠ predecessor valid.
  - DelegationSuccessorRef exists ≠ successor activated.
  - DelegationHandoffClaimRef exists ≠ handoff occurred.
  - DelegationHandoffAcceptanceClaimRef exists ≠ acceptance verified.
  - DelegationResponsibilityTransferClaimRef exists ≠ responsibility transferred.
  - DelegationLineageMap exists ≠ graph engine.
  - DelegationChainContinuityReadinessProfile exists ≠ continuity proven.
  - chain_envelope_hash exists ≠ TRACE_VERIFIED.
  - chain_binding_set_hash exists ≠ proof of transfer, handoff, or chain validity.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

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

DELEGATION_CHAIN_TASK_ID = "P1.8.9"
DELEGATION_CHAIN_REF_VERSION = "delegation_chain_ref.v1"
DELEGATION_PREDECESSOR_REF_VERSION = "delegation_predecessor_ref.v1"
DELEGATION_SUCCESSOR_REF_VERSION = "delegation_successor_ref.v1"
DELEGATION_HANDOFF_REF_VERSION = "delegation_handoff_ref.v1"
DELEGATION_HANDOFF_CLAIM_REF_VERSION = "delegation_handoff_claim_ref.v1"
DELEGATION_HANDOFF_ACCEPTANCE_CLAIM_REF_VERSION = "delegation_handoff_acceptance_claim_ref.v1"
DELEGATION_RESPONSIBILITY_TRANSFER_CLAIM_REF_VERSION = "delegation_responsibility_transfer_claim_ref.v1"
DELEGATION_LINEAGE_MAP_VERSION = "delegation_lineage_map.v1"
DELEGATION_CHAIN_CONTINUITY_READINESS_PROFILE_VERSION = "delegation_chain_continuity_readiness_profile.v1"
DELEGATION_CHAIN_ENVELOPE_VERSION = "delegation_chain_envelope.v1"
DELEGATION_CHAIN_BINDING_VERSION = "delegation_chain_binding.v1"
DELEGATION_CHAIN_BINDING_SET_VERSION = "delegation_chain_binding_set.v1"
DELEGATION_CHAIN_SIDE_EFFECTS_VERSION = "delegation_chain_side_effects.v1"
DELEGATION_CHAIN_STATUS_REPORT_VERSION = "delegation_chain_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_CHAIN_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.9; "
        "chain schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.9"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.9 chain reference layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.9 "
        "chain reference layer"
    ),
    "Live Handoff Executor": (
        "Live handoff executor is not available in P1.8.9; "
        "handoff refs are reference-only"
    ),
    "Responsibility Transfer Engine": (
        "Responsibility transfer engine scheduled for later P1.8 tasks; "
        "not P1.8.9"
    ),
    "Authority Transfer Engine": (
        "Authority transfer engine is not available in P1.8.9; "
        "chain refs are reference-only"
    ),
    "Handoff Acceptance Verifier": (
        "Handoff acceptance verifier is not available in P1.8.9; "
        "acceptance claim refs are reference-only"
    ),
    "Predecessor/Successor Verifier": (
        "Predecessor/successor verifier is not available in P1.8.9; "
        "predecessor/successor refs are reference-only"
    ),
    "Chain Verifier": (
        "Chain verifier is not available in P1.8.9; "
        "chain refs are reference-only"
    ),
    "Lineage Graph Engine": (
        "Lineage graph engine is not available in P1.8.9; "
        "lineage map is reference-only"
    ),
    "Runtime Owner Mutation": (
        "Runtime owner mutation is not available in P1.8.9; "
        "chain refs are reference-only and non-mutating"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision scheduled for later P1.8 tasks; not P1.8.9"
    ),
    "Approval Creation": (
        "Approval creation is not available in P1.8.9; "
        "chain refs are reference-only"
    ),
    "P1.8.10 Shadow Resolver / Consistency Model": (
        "P1.8.10 shadow resolver / consistency model is not available in P1.8.9"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 provenance/disclosure layer is not "
        "available in P1.8.9"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.9"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world)
# ---------------------------------------------------------------------------

CHAIN_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "chain_ref_id",
    "delegation_ref_id",
    "chain_link_kind",
    "chain_ref",
    "chain_description",
    "reference_status",
    "source_label",
    "chain_status",
    "chain_hash",
})

PREDECESSOR_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "predecessor_ref_id",
    "delegation_ref_id",
    "predecessor_delegation_ref",
    "predecessor_context_ref",
    "reference_status",
    "source_label",
    "chain_status",
    "predecessor_hash",
})

SUCCESSOR_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "successor_ref_id",
    "delegation_ref_id",
    "successor_delegation_ref",
    "successor_context_ref",
    "reference_status",
    "source_label",
    "chain_status",
    "successor_hash",
})

HANDOFF_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "handoff_ref_id",
    "delegation_ref_id",
    "handoff_kind",
    "from_ref",
    "to_ref",
    "handoff_context_ref",
    "reference_status",
    "source_label",
    "chain_status",
    "handoff_hash",
})

HANDOFF_CLAIM_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "handoff_claim_ref_id",
    "delegation_ref_id",
    "handoff_ref_id",
    "claim_ref",
    "claim_statement",
    "reference_status",
    "source_label",
    "chain_status",
    "handoff_claim_hash",
})

ACCEPTANCE_CLAIM_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "acceptance_claim_ref_id",
    "delegation_ref_id",
    "handoff_ref_id",
    "acceptance_ref",
    "acceptance_statement",
    "reference_status",
    "source_label",
    "chain_status",
    "acceptance_claim_hash",
})

TRANSFER_CLAIM_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "transfer_claim_ref_id",
    "delegation_ref_id",
    "handoff_ref_id",
    "transfer_ref",
    "transfer_statement",
    "reference_status",
    "source_label",
    "chain_status",
    "transfer_claim_hash",
})

LINEAGE_MAP_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "lineage_map_id",
    "delegation_ref_id",
    "predecessor_refs",
    "successor_refs",
    "handoff_refs",
    "chain_refs",
    "source_label",
    "lineage_map_hash",
})

CHAIN_READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "continuity_readiness_profile_id",
    "delegation_ref_id",
    "has_chain_refs",
    "has_predecessor_refs",
    "has_successor_refs",
    "has_handoff_refs",
    "has_handoff_claim_refs",
    "has_acceptance_claim_refs",
    "has_transfer_claim_refs",
    "has_lifecycle_context",
    "has_scope_context",
    "has_authority_context",
    "has_evidence_context",
    "has_identity_mesh_context",
    "missing_components",
    "chain_verifier_unavailable_reason",
    "handoff_executor_unavailable_reason",
    "source_label",
    "readiness_hash",
})

CHAIN_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "chain_envelope_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "lifecycle_binding_set_hash",
    "chain_refs",
    "predecessor_refs",
    "successor_refs",
    "handoff_refs",
    "handoff_claim_refs",
    "handoff_acceptance_claim_refs",
    "responsibility_transfer_claim_refs",
    "lineage_map_hash",
    "continuity_readiness_hash",
    "source_label",
    "chain_envelope_hash",
})

CHAIN_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
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
    "chain_envelope_hash",
    "lineage_map_hash",
    "continuity_readiness_hash",
    "source_label",
    "chain_status",
    "binding_hash",
})

CHAIN_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "chain_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "lifecycle_binding_set_hash",
    "bindings",
    "source_label",
    "chain_binding_set_hash",
    "side_effects",
})

CHAIN_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "handoff_executed",
    "responsibility_transferred",
    "acceptance_verified",
    "authority_transferred",
    "predecessor_verified",
    "successor_activated",
    "chain_verified",
    "lineage_graph_built",
    "runtime_owner_changed",
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

CHAIN_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationChainLinkKind(str, Enum):
    """Declared chain link category.

    Chain link kind classifies chain metadata.
    It does not verify chain lineage.
    It does not activate successor.
    It does not transfer responsibility.
    """

    ROOT = "ROOT"
    PREDECESSOR = "PREDECESSOR"
    SUCCESSOR = "SUCCESSOR"
    DERIVED_FROM = "DERIVED_FROM"
    CONTINUED_BY = "CONTINUED_BY"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    HANDOFF = "HANDOFF"
    UNKNOWN = "UNKNOWN"


class DelegationHandoffKind(str, Enum):
    """Declared handoff category.

    Handoff kind classifies declared handoff metadata.
    It does not execute handoff.
    It does not verify acceptance.
    It does not transfer authority or responsibility.
    """

    OPERATOR_TO_OPERATOR = "OPERATOR_TO_OPERATOR"
    OPERATOR_TO_AGENT = "OPERATOR_TO_AGENT"
    AGENT_TO_AGENT = "AGENT_TO_AGENT"
    AGENT_TO_SERVICE = "AGENT_TO_SERVICE"
    SERVICE_TO_AGENT = "SERVICE_TO_AGENT"
    SYSTEM_TO_AGENT = "SYSTEM_TO_AGENT"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationChainReferenceStatus(str, Enum):
    """Chain reference state.

    CHAIN_REFERENCED is not chain verified.
    PREDECESSOR_REFERENCED is not predecessor valid.
    SUCCESSOR_REFERENCED is not successor activated.
    HANDOFF_REFERENCED is not handoff executed.
    HANDOFF_CLAIM_REFERENCED is not proof handoff occurred.
    ACCEPTANCE_CLAIM_REFERENCED is not acceptance verification.
    TRANSFER_CLAIM_REFERENCED is not responsibility transfer.
    CHAIN_VERIFIER_UNAVAILABLE is honest unavailability, not failure/success.
    HANDOFF_EXECUTOR_UNAVAILABLE is honest unavailability, not failure/success.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    CHAIN_REFERENCED = "CHAIN_REFERENCED"
    PREDECESSOR_REFERENCED = "PREDECESSOR_REFERENCED"
    SUCCESSOR_REFERENCED = "SUCCESSOR_REFERENCED"
    HANDOFF_REFERENCED = "HANDOFF_REFERENCED"
    HANDOFF_CLAIM_REFERENCED = "HANDOFF_CLAIM_REFERENCED"
    ACCEPTANCE_CLAIM_REFERENCED = "ACCEPTANCE_CLAIM_REFERENCED"
    TRANSFER_CLAIM_REFERENCED = "TRANSFER_CLAIM_REFERENCED"
    CHAIN_VERIFIER_UNAVAILABLE = "CHAIN_VERIFIER_UNAVAILABLE"
    HANDOFF_EXECUTOR_UNAVAILABLE = "HANDOFF_EXECUTOR_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationChainStatus(str, Enum):
    """Chain context status.

    REFERENCE_ONLY means chain/handoff context is reference-only.
    DECLARED means chain/handoff context was declared as metadata.
    Neither means chain verified, handoff executed, acceptance verified,
    responsibility transferred, or successor activated.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parse helpers
# ---------------------------------------------------------------------------


def _parse_chain_link_kind(
    value: DelegationChainLinkKind | str,
) -> DelegationChainLinkKind:
    if isinstance(value, DelegationChainLinkKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationChainLinkKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid chain_link_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="chain_link_kind",
            ) from exc
    raise DelegationError(
        "chain_link_kind must be a string or DelegationChainLinkKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="chain_link_kind",
    )


def _parse_handoff_kind(
    value: DelegationHandoffKind | str,
) -> DelegationHandoffKind:
    if isinstance(value, DelegationHandoffKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationHandoffKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid handoff_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="handoff_kind",
            ) from exc
    raise DelegationError(
        "handoff_kind must be a string or DelegationHandoffKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="handoff_kind",
    )


def _parse_chain_reference_status(
    value: DelegationChainReferenceStatus | str,
) -> DelegationChainReferenceStatus:
    if isinstance(value, DelegationChainReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationChainReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationChainReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )


def _parse_chain_status(
    value: DelegationChainStatus | str,
) -> DelegationChainStatus:
    if isinstance(value, DelegationChainStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationChainStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid chain_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="chain_status",
            ) from exc
    raise DelegationError(
        "chain_status must be a string or DelegationChainStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="chain_status",
    )


# ---------------------------------------------------------------------------
# Hash compute helpers
# ---------------------------------------------------------------------------


def compute_chain_ref_hash(
    *,
    delegation_ref_id: str,
    chain_link_kind: DelegationChainLinkKind,
    chain_ref: str,
    chain_description: str,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_CHAIN_REF_VERSION,
) -> str:
    return stable_hash({
        "chain_description": chain_description,
        "chain_link_kind": chain_link_kind.value,
        "chain_ref": chain_ref,
        "chain_status": chain_status.value,
        "delegation_ref_id": delegation_ref_id,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_predecessor_ref_hash(
    *,
    delegation_ref_id: str,
    predecessor_delegation_ref: str,
    predecessor_context_ref: str | None,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_PREDECESSOR_REF_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "chain_status": chain_status.value,
        "delegation_ref_id": delegation_ref_id,
        "predecessor_delegation_ref": predecessor_delegation_ref,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if predecessor_context_ref is not None:
        payload["predecessor_context_ref"] = predecessor_context_ref
    return stable_hash(payload)


def compute_successor_ref_hash(
    *,
    delegation_ref_id: str,
    successor_delegation_ref: str,
    successor_context_ref: str | None,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_SUCCESSOR_REF_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "chain_status": chain_status.value,
        "delegation_ref_id": delegation_ref_id,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "successor_delegation_ref": successor_delegation_ref,
    }
    if successor_context_ref is not None:
        payload["successor_context_ref"] = successor_context_ref
    return stable_hash(payload)


def compute_handoff_ref_hash(
    *,
    delegation_ref_id: str,
    handoff_kind: DelegationHandoffKind,
    from_ref: str,
    to_ref: str,
    handoff_context_ref: str | None,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_HANDOFF_REF_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "chain_status": chain_status.value,
        "delegation_ref_id": delegation_ref_id,
        "from_ref": from_ref,
        "handoff_kind": handoff_kind.value,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "to_ref": to_ref,
    }
    if handoff_context_ref is not None:
        payload["handoff_context_ref"] = handoff_context_ref
    return stable_hash(payload)


def compute_handoff_claim_ref_hash(
    *,
    delegation_ref_id: str,
    handoff_ref_id: str,
    claim_ref: str,
    claim_statement: str,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_HANDOFF_CLAIM_REF_VERSION,
) -> str:
    return stable_hash({
        "chain_status": chain_status.value,
        "claim_ref": claim_ref,
        "claim_statement": claim_statement,
        "delegation_ref_id": delegation_ref_id,
        "handoff_ref_id": handoff_ref_id,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_acceptance_claim_ref_hash(
    *,
    delegation_ref_id: str,
    handoff_ref_id: str,
    acceptance_ref: str,
    acceptance_statement: str,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_HANDOFF_ACCEPTANCE_CLAIM_REF_VERSION,
) -> str:
    return stable_hash({
        "acceptance_ref": acceptance_ref,
        "acceptance_statement": acceptance_statement,
        "chain_status": chain_status.value,
        "delegation_ref_id": delegation_ref_id,
        "handoff_ref_id": handoff_ref_id,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_transfer_claim_ref_hash(
    *,
    delegation_ref_id: str,
    handoff_ref_id: str,
    transfer_ref: str,
    transfer_statement: str,
    reference_status: DelegationChainReferenceStatus,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_RESPONSIBILITY_TRANSFER_CLAIM_REF_VERSION,
) -> str:
    return stable_hash({
        "chain_status": chain_status.value,
        "delegation_ref_id": delegation_ref_id,
        "handoff_ref_id": handoff_ref_id,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "transfer_ref": transfer_ref,
        "transfer_statement": transfer_statement,
    })


def compute_lineage_map_hash(
    *,
    delegation_ref_id: str,
    predecessor_refs: tuple[str, ...],
    successor_refs: tuple[str, ...],
    handoff_refs: tuple[str, ...],
    chain_refs: tuple[str, ...],
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_LINEAGE_MAP_VERSION,
) -> str:
    return stable_hash({
        "chain_refs": sorted(chain_refs),
        "delegation_ref_id": delegation_ref_id,
        "handoff_refs": sorted(handoff_refs),
        "predecessor_refs": sorted(predecessor_refs),
        "schema_version": schema_version,
        "source_label": source_label.value,
        "successor_refs": sorted(successor_refs),
    })


def compute_chain_readiness_hash(
    *,
    delegation_ref_id: str,
    has_chain_refs: bool,
    has_predecessor_refs: bool,
    has_successor_refs: bool,
    has_handoff_refs: bool,
    has_handoff_claim_refs: bool,
    has_acceptance_claim_refs: bool,
    has_transfer_claim_refs: bool,
    has_lifecycle_context: bool,
    has_scope_context: bool,
    has_authority_context: bool,
    has_evidence_context: bool,
    has_identity_mesh_context: bool,
    missing_components: tuple[str, ...],
    chain_verifier_unavailable_reason: str,
    handoff_executor_unavailable_reason: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_CHAIN_CONTINUITY_READINESS_PROFILE_VERSION,
) -> str:
    return stable_hash({
        "chain_verifier_unavailable_reason": chain_verifier_unavailable_reason,
        "delegation_ref_id": delegation_ref_id,
        "handoff_executor_unavailable_reason": handoff_executor_unavailable_reason,
        "has_acceptance_claim_refs": has_acceptance_claim_refs,
        "has_authority_context": has_authority_context,
        "has_chain_refs": has_chain_refs,
        "has_evidence_context": has_evidence_context,
        "has_handoff_claim_refs": has_handoff_claim_refs,
        "has_handoff_refs": has_handoff_refs,
        "has_identity_mesh_context": has_identity_mesh_context,
        "has_lifecycle_context": has_lifecycle_context,
        "has_predecessor_refs": has_predecessor_refs,
        "has_scope_context": has_scope_context,
        "has_successor_refs": has_successor_refs,
        "has_transfer_claim_refs": has_transfer_claim_refs,
        "missing_components": sorted(missing_components),
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_chain_envelope_hash(
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
    chain_refs: tuple[str, ...],
    predecessor_refs: tuple[str, ...],
    successor_refs: tuple[str, ...],
    handoff_refs: tuple[str, ...],
    handoff_claim_refs: tuple[str, ...],
    handoff_acceptance_claim_refs: tuple[str, ...],
    responsibility_transfer_claim_refs: tuple[str, ...],
    lineage_map_hash: str,
    continuity_readiness_hash: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_CHAIN_ENVELOPE_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "chain_refs": sorted(chain_refs),
        "constraint_set_hash": constraint_set_hash,
        "continuity_readiness_hash": continuity_readiness_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "handoff_acceptance_claim_refs": sorted(handoff_acceptance_claim_refs),
        "handoff_claim_refs": sorted(handoff_claim_refs),
        "handoff_refs": sorted(handoff_refs),
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "lineage_map_hash": lineage_map_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "predecessor_refs": sorted(predecessor_refs),
        "responsibility_transfer_claim_refs": sorted(responsibility_transfer_claim_refs),
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_binding_set_hash": scope_binding_set_hash,
        "source_label": source_label.value,
        "successor_refs": sorted(successor_refs),
    })


def compute_chain_binding_hash(
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
    chain_envelope_hash: str,
    lineage_map_hash: str,
    continuity_readiness_hash: str,
    source_label: DelegationSourceLabel,
    chain_status: DelegationChainStatus,
    schema_version: str = DELEGATION_CHAIN_BINDING_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "chain_envelope_hash": chain_envelope_hash,
        "chain_status": chain_status.value,
        "constraint_set_hash": constraint_set_hash,
        "continuity_readiness_hash": continuity_readiness_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "lineage_map_hash": lineage_map_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_binding_set_hash": scope_binding_set_hash,
        "source_label": source_label.value,
    })


def compute_chain_binding_set_hash(
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
    binding_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_CHAIN_BINDING_SET_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "binding_hashes": sorted(binding_hashes),
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_binding_set_hash": scope_binding_set_hash,
        "source_label": source_label.value,
    })


def compute_chain_status_report_hash(
    *,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: "DelegationChainSideEffects",
) -> str:
    return stable_hash({
        "available_contracts": dict(sorted(available_contracts.items())),
        "side_effects": side_effects.to_canonical_dict(),
        "status_label": status_label.value,
        "unavailable_bindings": dict(sorted(unavailable_bindings.items())),
    })


# ---------------------------------------------------------------------------
# DelegationChainRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationChainRef:
    """Reference-only chain metadata.

    DelegationChainRef describes chain metadata.
    It does not verify chain lineage.
    It does not traverse a graph.
    It does not mutate runtime ownership.
    """

    delegation_ref_id: str
    chain_link_kind: DelegationChainLinkKind = DelegationChainLinkKind.UNKNOWN
    chain_ref: str = ""
    chain_description: str = ""
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.CHAIN_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_CHAIN_REF_VERSION
    chain_ref_id: str = ""
    chain_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        chain_link_kind = _parse_chain_link_kind(self.chain_link_kind)
        chain_ref = (
            self.chain_ref.strip()
            if isinstance(self.chain_ref, str)
            else ""
        )
        chain_description = (
            self.chain_description.strip()
            if isinstance(self.chain_description, str)
            else ""
        )
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        chain_hash = compute_chain_ref_hash(
            delegation_ref_id=delegation_ref_id,
            chain_link_kind=chain_link_kind,
            chain_ref=chain_ref,
            chain_description=chain_description,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        chain_ref_id = f"chain:{chain_hash[:16]}"

        if self.chain_hash not in ("", chain_hash):
            raise DelegationValidationError(
                "chain_hash does not match chain content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="chain_hash",
            )
        if self.chain_ref_id not in ("", chain_ref_id):
            raise DelegationValidationError(
                "chain_ref_id does not match chain content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="chain_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "chain_link_kind", chain_link_kind)
        object.__setattr__(self, "chain_ref", chain_ref)
        object.__setattr__(self, "chain_description", chain_description)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "chain_hash", chain_hash)
        object.__setattr__(self, "chain_ref_id", chain_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_description": self.chain_description,
            "chain_hash": self.chain_hash,
            "chain_link_kind": self.chain_link_kind.value,
            "chain_ref": self.chain_ref,
            "chain_ref_id": self.chain_ref_id,
            "chain_status": self.chain_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationChainRef:
        validate_known_fields(data, CHAIN_REF_KNOWN_FIELDS, label="delegation_chain_ref")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            chain_link_kind=data.get(
                "chain_link_kind", DelegationChainLinkKind.UNKNOWN
            ),
            chain_ref=data.get("chain_ref", ""),
            chain_description=data.get("chain_description", ""),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.CHAIN_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get("schema_version", DELEGATION_CHAIN_REF_VERSION),
            chain_ref_id=data.get("chain_ref_id", ""),
            chain_hash=data.get("chain_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationPredecessorRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationPredecessorRef:
    """Reference-only predecessor metadata.

    DelegationPredecessorRef describes declared predecessor metadata.
    It does not validate predecessor.
    It does not verify lineage.
    It does not prove chain continuity.
    """

    delegation_ref_id: str
    predecessor_delegation_ref: str = ""
    predecessor_context_ref: str | None = None
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.PREDECESSOR_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_PREDECESSOR_REF_VERSION
    predecessor_ref_id: str = ""
    predecessor_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        predecessor_delegation_ref = (
            self.predecessor_delegation_ref.strip()
            if isinstance(self.predecessor_delegation_ref, str)
            else ""
        )
        predecessor_context_ref = _optional_string(self.predecessor_context_ref)
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        predecessor_hash = compute_predecessor_ref_hash(
            delegation_ref_id=delegation_ref_id,
            predecessor_delegation_ref=predecessor_delegation_ref,
            predecessor_context_ref=predecessor_context_ref,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        predecessor_ref_id = f"predecessor:{predecessor_hash[:16]}"

        if self.predecessor_hash not in ("", predecessor_hash):
            raise DelegationValidationError(
                "predecessor_hash does not match predecessor content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="predecessor_hash",
            )
        if self.predecessor_ref_id not in ("", predecessor_ref_id):
            raise DelegationValidationError(
                "predecessor_ref_id does not match predecessor content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="predecessor_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "predecessor_delegation_ref", predecessor_delegation_ref)
        object.__setattr__(self, "predecessor_context_ref", predecessor_context_ref)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "predecessor_hash", predecessor_hash)
        object.__setattr__(self, "predecessor_ref_id", predecessor_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "chain_status": self.chain_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "predecessor_delegation_ref": self.predecessor_delegation_ref,
            "predecessor_hash": self.predecessor_hash,
            "predecessor_ref_id": self.predecessor_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.predecessor_context_ref is not None:
            result["predecessor_context_ref"] = self.predecessor_context_ref
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationPredecessorRef:
        validate_known_fields(
            data, PREDECESSOR_REF_KNOWN_FIELDS, label="delegation_predecessor_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            predecessor_delegation_ref=data.get("predecessor_delegation_ref", ""),
            predecessor_context_ref=data.get("predecessor_context_ref"),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.PREDECESSOR_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_PREDECESSOR_REF_VERSION
            ),
            predecessor_ref_id=data.get("predecessor_ref_id", ""),
            predecessor_hash=data.get("predecessor_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationSuccessorRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationSuccessorRef:
    """Reference-only successor metadata.

    DelegationSuccessorRef describes declared successor metadata.
    It does not activate successor.
    It does not invalidate current delegation.
    It does not transfer authority or responsibility.
    """

    delegation_ref_id: str
    successor_delegation_ref: str = ""
    successor_context_ref: str | None = None
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.SUCCESSOR_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_SUCCESSOR_REF_VERSION
    successor_ref_id: str = ""
    successor_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        successor_delegation_ref = (
            self.successor_delegation_ref.strip()
            if isinstance(self.successor_delegation_ref, str)
            else ""
        )
        successor_context_ref = _optional_string(self.successor_context_ref)
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        successor_hash = compute_successor_ref_hash(
            delegation_ref_id=delegation_ref_id,
            successor_delegation_ref=successor_delegation_ref,
            successor_context_ref=successor_context_ref,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        successor_ref_id = f"successor:{successor_hash[:16]}"

        if self.successor_hash not in ("", successor_hash):
            raise DelegationValidationError(
                "successor_hash does not match successor content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="successor_hash",
            )
        if self.successor_ref_id not in ("", successor_ref_id):
            raise DelegationValidationError(
                "successor_ref_id does not match successor content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="successor_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "successor_delegation_ref", successor_delegation_ref)
        object.__setattr__(self, "successor_context_ref", successor_context_ref)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "successor_hash", successor_hash)
        object.__setattr__(self, "successor_ref_id", successor_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "chain_status": self.chain_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "successor_delegation_ref": self.successor_delegation_ref,
            "successor_hash": self.successor_hash,
            "successor_ref_id": self.successor_ref_id,
        }
        if self.successor_context_ref is not None:
            result["successor_context_ref"] = self.successor_context_ref
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationSuccessorRef:
        validate_known_fields(
            data, SUCCESSOR_REF_KNOWN_FIELDS, label="delegation_successor_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            successor_delegation_ref=data.get("successor_delegation_ref", ""),
            successor_context_ref=data.get("successor_context_ref"),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.SUCCESSOR_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_SUCCESSOR_REF_VERSION
            ),
            successor_ref_id=data.get("successor_ref_id", ""),
            successor_hash=data.get("successor_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationHandoffRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationHandoffRef:
    """Reference-only handoff metadata.

    DelegationHandoffRef describes handoff metadata.
    It does not execute handoff.
    It does not verify acceptance.
    It does not transfer responsibility.
    It does not change runtime owner.
    """

    delegation_ref_id: str
    handoff_kind: DelegationHandoffKind = DelegationHandoffKind.REFERENCE_ONLY
    from_ref: str = ""
    to_ref: str = ""
    handoff_context_ref: str | None = None
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.HANDOFF_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_HANDOFF_REF_VERSION
    handoff_ref_id: str = ""
    handoff_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        handoff_kind = _parse_handoff_kind(self.handoff_kind)
        from_ref = (
            self.from_ref.strip()
            if isinstance(self.from_ref, str)
            else ""
        )
        to_ref = (
            self.to_ref.strip()
            if isinstance(self.to_ref, str)
            else ""
        )
        handoff_context_ref = _optional_string(self.handoff_context_ref)
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        handoff_hash = compute_handoff_ref_hash(
            delegation_ref_id=delegation_ref_id,
            handoff_kind=handoff_kind,
            from_ref=from_ref,
            to_ref=to_ref,
            handoff_context_ref=handoff_context_ref,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        handoff_ref_id = f"handoff:{handoff_hash[:16]}"

        if self.handoff_hash not in ("", handoff_hash):
            raise DelegationValidationError(
                "handoff_hash does not match handoff content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="handoff_hash",
            )
        if self.handoff_ref_id not in ("", handoff_ref_id):
            raise DelegationValidationError(
                "handoff_ref_id does not match handoff content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="handoff_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "handoff_kind", handoff_kind)
        object.__setattr__(self, "from_ref", from_ref)
        object.__setattr__(self, "to_ref", to_ref)
        object.__setattr__(self, "handoff_context_ref", handoff_context_ref)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "handoff_hash", handoff_hash)
        object.__setattr__(self, "handoff_ref_id", handoff_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "chain_status": self.chain_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "from_ref": self.from_ref,
            "handoff_hash": self.handoff_hash,
            "handoff_kind": self.handoff_kind.value,
            "handoff_ref_id": self.handoff_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "to_ref": self.to_ref,
        }
        if self.handoff_context_ref is not None:
            result["handoff_context_ref"] = self.handoff_context_ref
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationHandoffRef:
        validate_known_fields(
            data, HANDOFF_REF_KNOWN_FIELDS, label="delegation_handoff_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            handoff_kind=data.get(
                "handoff_kind", DelegationHandoffKind.REFERENCE_ONLY
            ),
            from_ref=data.get("from_ref", ""),
            to_ref=data.get("to_ref", ""),
            handoff_context_ref=data.get("handoff_context_ref"),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.HANDOFF_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_HANDOFF_REF_VERSION
            ),
            handoff_ref_id=data.get("handoff_ref_id", ""),
            handoff_hash=data.get("handoff_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationHandoffClaimRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationHandoffClaimRef:
    """Reference-only claim that a handoff was declared.

    DelegationHandoffClaimRef describes a claim.
    It does not prove handoff occurred.
    It does not execute handoff.
    It does not verify responsibility transfer.
    """

    delegation_ref_id: str
    handoff_ref_id: str
    claim_ref: str = ""
    claim_statement: str = ""
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.HANDOFF_CLAIM_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_HANDOFF_CLAIM_REF_VERSION
    handoff_claim_ref_id: str = ""
    handoff_claim_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        handoff_ref_id = _required_string(
            self.handoff_ref_id, field_name="handoff_ref_id"
        )
        claim_ref = (
            self.claim_ref.strip()
            if isinstance(self.claim_ref, str)
            else ""
        )
        claim_statement = (
            self.claim_statement.strip()
            if isinstance(self.claim_statement, str)
            else ""
        )
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        handoff_claim_hash = compute_handoff_claim_ref_hash(
            delegation_ref_id=delegation_ref_id,
            handoff_ref_id=handoff_ref_id,
            claim_ref=claim_ref,
            claim_statement=claim_statement,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        handoff_claim_ref_id = f"handoff-claim:{handoff_claim_hash[:16]}"

        if self.handoff_claim_hash not in ("", handoff_claim_hash):
            raise DelegationValidationError(
                "handoff_claim_hash does not match claim content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="handoff_claim_hash",
            )
        if self.handoff_claim_ref_id not in ("", handoff_claim_ref_id):
            raise DelegationValidationError(
                "handoff_claim_ref_id does not match claim content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="handoff_claim_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "handoff_ref_id", handoff_ref_id)
        object.__setattr__(self, "claim_ref", claim_ref)
        object.__setattr__(self, "claim_statement", claim_statement)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "handoff_claim_hash", handoff_claim_hash)
        object.__setattr__(self, "handoff_claim_ref_id", handoff_claim_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_status": self.chain_status.value,
            "claim_ref": self.claim_ref,
            "claim_statement": self.claim_statement,
            "delegation_ref_id": self.delegation_ref_id,
            "handoff_claim_hash": self.handoff_claim_hash,
            "handoff_claim_ref_id": self.handoff_claim_ref_id,
            "handoff_ref_id": self.handoff_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationHandoffClaimRef:
        validate_known_fields(
            data, HANDOFF_CLAIM_REF_KNOWN_FIELDS, label="delegation_handoff_claim_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            handoff_ref_id=data["handoff_ref_id"],
            claim_ref=data.get("claim_ref", ""),
            claim_statement=data.get("claim_statement", ""),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.HANDOFF_CLAIM_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_HANDOFF_CLAIM_REF_VERSION
            ),
            handoff_claim_ref_id=data.get("handoff_claim_ref_id", ""),
            handoff_claim_hash=data.get("handoff_claim_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationHandoffAcceptanceClaimRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationHandoffAcceptanceClaimRef:
    """Reference-only claim that a handoff was accepted.

    DelegationHandoffAcceptanceClaimRef describes an acceptance claim.
    It does not verify acceptance.
    It does not prove delegate accepted.
    It does not activate successor.
    It does not transfer responsibility.
    """

    delegation_ref_id: str
    handoff_ref_id: str
    acceptance_ref: str = ""
    acceptance_statement: str = ""
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.ACCEPTANCE_CLAIM_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_HANDOFF_ACCEPTANCE_CLAIM_REF_VERSION
    acceptance_claim_ref_id: str = ""
    acceptance_claim_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        handoff_ref_id = _required_string(
            self.handoff_ref_id, field_name="handoff_ref_id"
        )
        acceptance_ref = (
            self.acceptance_ref.strip()
            if isinstance(self.acceptance_ref, str)
            else ""
        )
        acceptance_statement = (
            self.acceptance_statement.strip()
            if isinstance(self.acceptance_statement, str)
            else ""
        )
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        acceptance_claim_hash = compute_acceptance_claim_ref_hash(
            delegation_ref_id=delegation_ref_id,
            handoff_ref_id=handoff_ref_id,
            acceptance_ref=acceptance_ref,
            acceptance_statement=acceptance_statement,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        acceptance_claim_ref_id = f"acceptance-claim:{acceptance_claim_hash[:16]}"

        if self.acceptance_claim_hash not in ("", acceptance_claim_hash):
            raise DelegationValidationError(
                "acceptance_claim_hash does not match acceptance content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="acceptance_claim_hash",
            )
        if self.acceptance_claim_ref_id not in ("", acceptance_claim_ref_id):
            raise DelegationValidationError(
                "acceptance_claim_ref_id does not match acceptance content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="acceptance_claim_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "handoff_ref_id", handoff_ref_id)
        object.__setattr__(self, "acceptance_ref", acceptance_ref)
        object.__setattr__(self, "acceptance_statement", acceptance_statement)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "acceptance_claim_hash", acceptance_claim_hash)
        object.__setattr__(self, "acceptance_claim_ref_id", acceptance_claim_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "acceptance_claim_hash": self.acceptance_claim_hash,
            "acceptance_claim_ref_id": self.acceptance_claim_ref_id,
            "acceptance_ref": self.acceptance_ref,
            "acceptance_statement": self.acceptance_statement,
            "chain_status": self.chain_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "handoff_ref_id": self.handoff_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationHandoffAcceptanceClaimRef:
        validate_known_fields(
            data,
            ACCEPTANCE_CLAIM_REF_KNOWN_FIELDS,
            label="delegation_handoff_acceptance_claim_ref",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            handoff_ref_id=data["handoff_ref_id"],
            acceptance_ref=data.get("acceptance_ref", ""),
            acceptance_statement=data.get("acceptance_statement", ""),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.ACCEPTANCE_CLAIM_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_HANDOFF_ACCEPTANCE_CLAIM_REF_VERSION,
            ),
            acceptance_claim_ref_id=data.get("acceptance_claim_ref_id", ""),
            acceptance_claim_hash=data.get("acceptance_claim_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationResponsibilityTransferClaimRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationResponsibilityTransferClaimRef:
    """Reference-only claim that responsibility transfer was declared.

    DelegationResponsibilityTransferClaimRef describes a transfer claim.
    It does not transfer responsibility.
    It does not transfer authority.
    It does not mutate runtime owner.
    It does not verify acceptance.
    """

    delegation_ref_id: str
    handoff_ref_id: str
    transfer_ref: str = ""
    transfer_statement: str = ""
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.TRANSFER_CLAIM_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_RESPONSIBILITY_TRANSFER_CLAIM_REF_VERSION
    transfer_claim_ref_id: str = ""
    transfer_claim_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        handoff_ref_id = _required_string(
            self.handoff_ref_id, field_name="handoff_ref_id"
        )
        transfer_ref = (
            self.transfer_ref.strip()
            if isinstance(self.transfer_ref, str)
            else ""
        )
        transfer_statement = (
            self.transfer_statement.strip()
            if isinstance(self.transfer_statement, str)
            else ""
        )
        reference_status = _parse_chain_reference_status(self.reference_status)
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        transfer_claim_hash = compute_transfer_claim_ref_hash(
            delegation_ref_id=delegation_ref_id,
            handoff_ref_id=handoff_ref_id,
            transfer_ref=transfer_ref,
            transfer_statement=transfer_statement,
            reference_status=reference_status,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        transfer_claim_ref_id = f"transfer-claim:{transfer_claim_hash[:16]}"

        if self.transfer_claim_hash not in ("", transfer_claim_hash):
            raise DelegationValidationError(
                "transfer_claim_hash does not match transfer content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="transfer_claim_hash",
            )
        if self.transfer_claim_ref_id not in ("", transfer_claim_ref_id):
            raise DelegationValidationError(
                "transfer_claim_ref_id does not match transfer content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="transfer_claim_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "handoff_ref_id", handoff_ref_id)
        object.__setattr__(self, "transfer_ref", transfer_ref)
        object.__setattr__(self, "transfer_statement", transfer_statement)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "transfer_claim_hash", transfer_claim_hash)
        object.__setattr__(self, "transfer_claim_ref_id", transfer_claim_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_status": self.chain_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "handoff_ref_id": self.handoff_ref_id,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "transfer_claim_hash": self.transfer_claim_hash,
            "transfer_claim_ref_id": self.transfer_claim_ref_id,
            "transfer_ref": self.transfer_ref,
            "transfer_statement": self.transfer_statement,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationResponsibilityTransferClaimRef:
        validate_known_fields(
            data,
            TRANSFER_CLAIM_REF_KNOWN_FIELDS,
            label="delegation_responsibility_transfer_claim_ref",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            handoff_ref_id=data["handoff_ref_id"],
            transfer_ref=data.get("transfer_ref", ""),
            transfer_statement=data.get("transfer_statement", ""),
            reference_status=data.get(
                "reference_status",
                DelegationChainReferenceStatus.TRANSFER_CLAIM_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_RESPONSIBILITY_TRANSFER_CLAIM_REF_VERSION,
            ),
            transfer_claim_ref_id=data.get("transfer_claim_ref_id", ""),
            transfer_claim_hash=data.get("transfer_claim_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationLineageMap
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLineageMap:
    """Reference-only lineage map, not graph engine.

    DelegationLineageMap is not graph engine.
    It is not verified lineage.
    It is not runtime traversal.
    It is not chain verifier.
    """

    delegation_ref_id: str
    predecessor_refs: tuple[str, ...] = ()
    successor_refs: tuple[str, ...] = ()
    handoff_refs: tuple[str, ...] = ()
    chain_refs: tuple[str, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_LINEAGE_MAP_VERSION
    lineage_map_id: str = ""
    lineage_map_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        _predecessor_refs: tuple[str, ...] = (
            tuple(self.predecessor_refs)
            if isinstance(self.predecessor_refs, (tuple, list))
            else ()
        )
        _successor_refs: tuple[str, ...] = (
            tuple(self.successor_refs)
            if isinstance(self.successor_refs, (tuple, list))
            else ()
        )
        _handoff_refs: tuple[str, ...] = (
            tuple(self.handoff_refs)
            if isinstance(self.handoff_refs, (tuple, list))
            else ()
        )
        _chain_refs: tuple[str, ...] = (
            tuple(self.chain_refs)
            if isinstance(self.chain_refs, (tuple, list))
            else ()
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        lineage_map_hash = compute_lineage_map_hash(
            delegation_ref_id=delegation_ref_id,
            predecessor_refs=_predecessor_refs,
            successor_refs=_successor_refs,
            handoff_refs=_handoff_refs,
            chain_refs=_chain_refs,
            source_label=source_label,
            schema_version=schema_version,
        )
        lineage_map_id = f"lineage:{lineage_map_hash[:16]}"

        if self.lineage_map_hash not in ("", lineage_map_hash):
            raise DelegationValidationError(
                "lineage_map_hash does not match lineage map content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lineage_map_hash",
            )
        if self.lineage_map_id not in ("", lineage_map_id):
            raise DelegationValidationError(
                "lineage_map_id does not match lineage map content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lineage_map_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "predecessor_refs", _predecessor_refs)
        object.__setattr__(self, "successor_refs", _successor_refs)
        object.__setattr__(self, "handoff_refs", _handoff_refs)
        object.__setattr__(self, "chain_refs", _chain_refs)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "lineage_map_hash", lineage_map_hash)
        object.__setattr__(self, "lineage_map_id", lineage_map_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_refs": sorted(self.chain_refs),
            "delegation_ref_id": self.delegation_ref_id,
            "handoff_refs": sorted(self.handoff_refs),
            "lineage_map_hash": self.lineage_map_hash,
            "lineage_map_id": self.lineage_map_id,
            "predecessor_refs": sorted(self.predecessor_refs),
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "successor_refs": sorted(self.successor_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLineageMap:
        validate_known_fields(
            data, LINEAGE_MAP_KNOWN_FIELDS, label="delegation_lineage_map"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            predecessor_refs=tuple(data.get("predecessor_refs", ())),
            successor_refs=tuple(data.get("successor_refs", ())),
            handoff_refs=tuple(data.get("handoff_refs", ())),
            chain_refs=tuple(data.get("chain_refs", ())),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_LINEAGE_MAP_VERSION),
            lineage_map_id=data.get("lineage_map_id", ""),
            lineage_map_hash=data.get("lineage_map_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationChainContinuityReadinessProfile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationChainContinuityReadinessProfile:
    """Present/missing chain and handoff component profile, not continuity proof.

    ContinuityReadinessProfile is not chain verification.
    It is not handoff executable.
    It is not continuity proof.
    It is not authority transfer.
    """

    delegation_ref_id: str
    has_chain_refs: bool = False
    has_predecessor_refs: bool = False
    has_successor_refs: bool = False
    has_handoff_refs: bool = False
    has_handoff_claim_refs: bool = False
    has_acceptance_claim_refs: bool = False
    has_transfer_claim_refs: bool = False
    has_lifecycle_context: bool = False
    has_scope_context: bool = False
    has_authority_context: bool = False
    has_evidence_context: bool = False
    has_identity_mesh_context: bool = False
    missing_components: tuple[str, ...] = ()
    chain_verifier_unavailable_reason: str = (
        "Chain verifier is not available; "
        "chain/handoff metadata is reference-only."
    )
    handoff_executor_unavailable_reason: str = (
        "Handoff executor is not available; "
        "handoff refs are reference-only."
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_CHAIN_CONTINUITY_READINESS_PROFILE_VERSION
    continuity_readiness_profile_id: str = ""
    readiness_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        _missing_components: tuple[str, ...] = (
            tuple(self.missing_components)
            if isinstance(self.missing_components, (tuple, list))
            else ()
        )
        _chain_verifier_unavailable_reason = (
            self.chain_verifier_unavailable_reason.strip()
            if isinstance(self.chain_verifier_unavailable_reason, str)
            else ""
        )
        _handoff_executor_unavailable_reason = (
            self.handoff_executor_unavailable_reason.strip()
            if isinstance(self.handoff_executor_unavailable_reason, str)
            else ""
        )

        readiness_hash = compute_chain_readiness_hash(
            delegation_ref_id=delegation_ref_id,
            has_chain_refs=self.has_chain_refs,
            has_predecessor_refs=self.has_predecessor_refs,
            has_successor_refs=self.has_successor_refs,
            has_handoff_refs=self.has_handoff_refs,
            has_handoff_claim_refs=self.has_handoff_claim_refs,
            has_acceptance_claim_refs=self.has_acceptance_claim_refs,
            has_transfer_claim_refs=self.has_transfer_claim_refs,
            has_lifecycle_context=self.has_lifecycle_context,
            has_scope_context=self.has_scope_context,
            has_authority_context=self.has_authority_context,
            has_evidence_context=self.has_evidence_context,
            has_identity_mesh_context=self.has_identity_mesh_context,
            missing_components=_missing_components,
            chain_verifier_unavailable_reason=_chain_verifier_unavailable_reason,
            handoff_executor_unavailable_reason=_handoff_executor_unavailable_reason,
            source_label=source_label,
            schema_version=schema_version,
        )
        continuity_readiness_profile_id = f"chain-readiness:{readiness_hash[:16]}"

        if self.readiness_hash not in ("", readiness_hash):
            raise DelegationValidationError(
                "readiness_hash does not match readiness profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="readiness_hash",
            )
        if self.continuity_readiness_profile_id not in (
            "",
            continuity_readiness_profile_id,
        ):
            raise DelegationValidationError(
                "continuity_readiness_profile_id does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="continuity_readiness_profile_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "missing_components", _missing_components)
        object.__setattr__(
            self,
            "chain_verifier_unavailable_reason",
            _chain_verifier_unavailable_reason,
        )
        object.__setattr__(
            self,
            "handoff_executor_unavailable_reason",
            _handoff_executor_unavailable_reason,
        )
        object.__setattr__(self, "readiness_hash", readiness_hash)
        object.__setattr__(
            self,
            "continuity_readiness_profile_id",
            continuity_readiness_profile_id,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_verifier_unavailable_reason": (
                self.chain_verifier_unavailable_reason
            ),
            "continuity_readiness_profile_id": (
                self.continuity_readiness_profile_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "handoff_executor_unavailable_reason": (
                self.handoff_executor_unavailable_reason
            ),
            "has_acceptance_claim_refs": self.has_acceptance_claim_refs,
            "has_authority_context": self.has_authority_context,
            "has_chain_refs": self.has_chain_refs,
            "has_evidence_context": self.has_evidence_context,
            "has_handoff_claim_refs": self.has_handoff_claim_refs,
            "has_handoff_refs": self.has_handoff_refs,
            "has_identity_mesh_context": self.has_identity_mesh_context,
            "has_lifecycle_context": self.has_lifecycle_context,
            "has_predecessor_refs": self.has_predecessor_refs,
            "has_scope_context": self.has_scope_context,
            "has_successor_refs": self.has_successor_refs,
            "has_transfer_claim_refs": self.has_transfer_claim_refs,
            "missing_components": sorted(self.missing_components),
            "readiness_hash": self.readiness_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationChainContinuityReadinessProfile:
        validate_known_fields(
            data,
            CHAIN_READINESS_PROFILE_KNOWN_FIELDS,
            label="delegation_chain_continuity_readiness_profile",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            has_chain_refs=data.get("has_chain_refs", False),
            has_predecessor_refs=data.get("has_predecessor_refs", False),
            has_successor_refs=data.get("has_successor_refs", False),
            has_handoff_refs=data.get("has_handoff_refs", False),
            has_handoff_claim_refs=data.get("has_handoff_claim_refs", False),
            has_acceptance_claim_refs=data.get("has_acceptance_claim_refs", False),
            has_transfer_claim_refs=data.get("has_transfer_claim_refs", False),
            has_lifecycle_context=data.get("has_lifecycle_context", False),
            has_scope_context=data.get("has_scope_context", False),
            has_authority_context=data.get("has_authority_context", False),
            has_evidence_context=data.get("has_evidence_context", False),
            has_identity_mesh_context=data.get("has_identity_mesh_context", False),
            missing_components=tuple(data.get("missing_components", ())),
            chain_verifier_unavailable_reason=data.get(
                "chain_verifier_unavailable_reason",
                "Chain verifier is not available.",
            ),
            handoff_executor_unavailable_reason=data.get(
                "handoff_executor_unavailable_reason",
                "Handoff executor is not available.",
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version",
                DELEGATION_CHAIN_CONTINUITY_READINESS_PROFILE_VERSION,
            ),
            continuity_readiness_profile_id=data.get(
                "continuity_readiness_profile_id", ""
            ),
            readiness_hash=data.get("readiness_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationChainEnvelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationChainEnvelope:
    """Deterministic packet of chain/handoff refs and context hashes.

    ChainEnvelope is a reference packet.
    It is not chain verification.
    It is not handoff execution.
    It is not responsibility transfer.
    It is not authority transfer.
    It is not TRACE_VERIFIED.
    """

    delegation_ref_id: str
    delegation_identity_hash: str = ""
    role_binding_hash: str = ""
    constraint_set_hash: str = ""
    authority_binding_set_hash: str = ""
    non_repudiation_binding_set_hash: str = ""
    identity_mesh_binding_set_hash: str = ""
    scope_binding_set_hash: str = ""
    lifecycle_binding_set_hash: str = ""
    chain_refs: tuple[str, ...] = ()
    predecessor_refs: tuple[str, ...] = ()
    successor_refs: tuple[str, ...] = ()
    handoff_refs: tuple[str, ...] = ()
    handoff_claim_refs: tuple[str, ...] = ()
    handoff_acceptance_claim_refs: tuple[str, ...] = ()
    responsibility_transfer_claim_refs: tuple[str, ...] = ()
    lineage_map_hash: str = ""
    continuity_readiness_hash: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_CHAIN_ENVELOPE_VERSION
    chain_envelope_id: str = ""
    chain_envelope_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        _chain_refs: tuple[str, ...] = (
            tuple(self.chain_refs)
            if isinstance(self.chain_refs, (tuple, list))
            else ()
        )
        _predecessor_refs: tuple[str, ...] = (
            tuple(self.predecessor_refs)
            if isinstance(self.predecessor_refs, (tuple, list))
            else ()
        )
        _successor_refs: tuple[str, ...] = (
            tuple(self.successor_refs)
            if isinstance(self.successor_refs, (tuple, list))
            else ()
        )
        _handoff_refs: tuple[str, ...] = (
            tuple(self.handoff_refs)
            if isinstance(self.handoff_refs, (tuple, list))
            else ()
        )
        _handoff_claim_refs: tuple[str, ...] = (
            tuple(self.handoff_claim_refs)
            if isinstance(self.handoff_claim_refs, (tuple, list))
            else ()
        )
        _handoff_acceptance_claim_refs: tuple[str, ...] = (
            tuple(self.handoff_acceptance_claim_refs)
            if isinstance(self.handoff_acceptance_claim_refs, (tuple, list))
            else ()
        )
        _responsibility_transfer_claim_refs: tuple[str, ...] = (
            tuple(self.responsibility_transfer_claim_refs)
            if isinstance(
                self.responsibility_transfer_claim_refs, (tuple, list)
            )
            else ()
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        chain_envelope_hash = compute_chain_envelope_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=self.delegation_identity_hash,
            role_binding_hash=self.role_binding_hash,
            constraint_set_hash=self.constraint_set_hash,
            authority_binding_set_hash=self.authority_binding_set_hash,
            non_repudiation_binding_set_hash=self.non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=self.identity_mesh_binding_set_hash,
            scope_binding_set_hash=self.scope_binding_set_hash,
            lifecycle_binding_set_hash=self.lifecycle_binding_set_hash,
            chain_refs=_chain_refs,
            predecessor_refs=_predecessor_refs,
            successor_refs=_successor_refs,
            handoff_refs=_handoff_refs,
            handoff_claim_refs=_handoff_claim_refs,
            handoff_acceptance_claim_refs=_handoff_acceptance_claim_refs,
            responsibility_transfer_claim_refs=_responsibility_transfer_claim_refs,
            lineage_map_hash=self.lineage_map_hash,
            continuity_readiness_hash=self.continuity_readiness_hash,
            source_label=source_label,
            schema_version=schema_version,
        )
        chain_envelope_id = f"chain-envelope:{chain_envelope_hash[:16]}"

        if self.chain_envelope_hash not in ("", chain_envelope_hash):
            raise DelegationValidationError(
                "chain_envelope_hash does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="chain_envelope_hash",
            )
        if self.chain_envelope_id not in ("", chain_envelope_id):
            raise DelegationValidationError(
                "chain_envelope_id does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="chain_envelope_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "chain_refs", _chain_refs)
        object.__setattr__(self, "predecessor_refs", _predecessor_refs)
        object.__setattr__(self, "successor_refs", _successor_refs)
        object.__setattr__(self, "handoff_refs", _handoff_refs)
        object.__setattr__(self, "handoff_claim_refs", _handoff_claim_refs)
        object.__setattr__(
            self, "handoff_acceptance_claim_refs", _handoff_acceptance_claim_refs
        )
        object.__setattr__(
            self,
            "responsibility_transfer_claim_refs",
            _responsibility_transfer_claim_refs,
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "chain_envelope_hash", chain_envelope_hash)
        object.__setattr__(self, "chain_envelope_id", chain_envelope_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "chain_envelope_hash": self.chain_envelope_hash,
            "chain_envelope_id": self.chain_envelope_id,
            "chain_refs": sorted(self.chain_refs),
            "constraint_set_hash": self.constraint_set_hash,
            "continuity_readiness_hash": self.continuity_readiness_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "handoff_acceptance_claim_refs": sorted(
                self.handoff_acceptance_claim_refs
            ),
            "handoff_claim_refs": sorted(self.handoff_claim_refs),
            "handoff_refs": sorted(self.handoff_refs),
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "lineage_map_hash": self.lineage_map_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "predecessor_refs": sorted(self.predecessor_refs),
            "responsibility_transfer_claim_refs": sorted(
                self.responsibility_transfer_claim_refs
            ),
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "source_label": self.source_label.value,
            "successor_refs": sorted(self.successor_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationChainEnvelope:
        validate_known_fields(
            data, CHAIN_ENVELOPE_KNOWN_FIELDS, label="delegation_chain_envelope"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data.get("delegation_identity_hash", ""),
            role_binding_hash=data.get("role_binding_hash", ""),
            constraint_set_hash=data.get("constraint_set_hash", ""),
            authority_binding_set_hash=data.get("authority_binding_set_hash", ""),
            non_repudiation_binding_set_hash=data.get(
                "non_repudiation_binding_set_hash", ""
            ),
            identity_mesh_binding_set_hash=data.get(
                "identity_mesh_binding_set_hash", ""
            ),
            scope_binding_set_hash=data.get("scope_binding_set_hash", ""),
            lifecycle_binding_set_hash=data.get("lifecycle_binding_set_hash", ""),
            chain_refs=tuple(data.get("chain_refs", ())),
            predecessor_refs=tuple(data.get("predecessor_refs", ())),
            successor_refs=tuple(data.get("successor_refs", ())),
            handoff_refs=tuple(data.get("handoff_refs", ())),
            handoff_claim_refs=tuple(data.get("handoff_claim_refs", ())),
            handoff_acceptance_claim_refs=tuple(
                data.get("handoff_acceptance_claim_refs", ())
            ),
            responsibility_transfer_claim_refs=tuple(
                data.get("responsibility_transfer_claim_refs", ())
            ),
            lineage_map_hash=data.get("lineage_map_hash", ""),
            continuity_readiness_hash=data.get("continuity_readiness_hash", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_CHAIN_ENVELOPE_VERSION
            ),
            chain_envelope_id=data.get("chain_envelope_id", ""),
            chain_envelope_hash=data.get("chain_envelope_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationChainBinding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationChainBinding:
    """Binding between chain envelope and delegation context.

    ChainBinding binds chain/handoff metadata.
    It is not runtime chain state.
    It is not handoff execution.
    It is not transfer.
    It is not policy decision.
    It is not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str = ""
    role_binding_hash: str = ""
    constraint_set_hash: str = ""
    authority_binding_set_hash: str = ""
    non_repudiation_binding_set_hash: str = ""
    identity_mesh_binding_set_hash: str = ""
    scope_binding_set_hash: str = ""
    lifecycle_binding_set_hash: str = ""
    chain_envelope_hash: str = ""
    lineage_map_hash: str = ""
    continuity_readiness_hash: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED
    schema_version: str = DELEGATION_CHAIN_BINDING_VERSION
    binding_id: str = ""
    binding_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        chain_status = _parse_chain_status(self.chain_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        binding_hash = compute_chain_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=self.delegation_identity_hash,
            role_binding_hash=self.role_binding_hash,
            constraint_set_hash=self.constraint_set_hash,
            authority_binding_set_hash=self.authority_binding_set_hash,
            non_repudiation_binding_set_hash=self.non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=self.identity_mesh_binding_set_hash,
            scope_binding_set_hash=self.scope_binding_set_hash,
            lifecycle_binding_set_hash=self.lifecycle_binding_set_hash,
            chain_envelope_hash=self.chain_envelope_hash,
            lineage_map_hash=self.lineage_map_hash,
            continuity_readiness_hash=self.continuity_readiness_hash,
            source_label=source_label,
            chain_status=chain_status,
            schema_version=schema_version,
        )
        binding_id = f"chain-binding:{binding_hash[:16]}"

        if self.binding_hash not in ("", binding_hash):
            raise DelegationValidationError(
                "binding_hash does not match binding content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="binding_hash",
            )
        if self.binding_id not in ("", binding_id):
            raise DelegationValidationError(
                "binding_id does not match binding content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="binding_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "chain_status", chain_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "chain_envelope_hash": self.chain_envelope_hash,
            "chain_status": self.chain_status.value,
            "constraint_set_hash": self.constraint_set_hash,
            "continuity_readiness_hash": self.continuity_readiness_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "lineage_map_hash": self.lineage_map_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationChainBinding:
        validate_known_fields(
            data, CHAIN_BINDING_KNOWN_FIELDS, label="delegation_chain_binding"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data.get("delegation_identity_hash", ""),
            role_binding_hash=data.get("role_binding_hash", ""),
            constraint_set_hash=data.get("constraint_set_hash", ""),
            authority_binding_set_hash=data.get("authority_binding_set_hash", ""),
            non_repudiation_binding_set_hash=data.get(
                "non_repudiation_binding_set_hash", ""
            ),
            identity_mesh_binding_set_hash=data.get(
                "identity_mesh_binding_set_hash", ""
            ),
            scope_binding_set_hash=data.get("scope_binding_set_hash", ""),
            lifecycle_binding_set_hash=data.get("lifecycle_binding_set_hash", ""),
            chain_envelope_hash=data.get("chain_envelope_hash", ""),
            lineage_map_hash=data.get("lineage_map_hash", ""),
            continuity_readiness_hash=data.get("continuity_readiness_hash", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            chain_status=data.get(
                "chain_status", DelegationChainStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_CHAIN_BINDING_VERSION
            ),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationChainBindingSet
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationChainBindingSet:
    """Collection of chain bindings for one delegation.

    ChainBindingSet describes chain/handoff hooks.
    It does not transfer responsibility.
    It does not execute handoff.
    It does not activate successors.
    It does not write Ledger/global trace.
    It does not mutate runtime.
    """

    delegation_ref_id: str
    delegation_identity_hash: str = ""
    role_binding_hash: str = ""
    constraint_set_hash: str = ""
    authority_binding_set_hash: str = ""
    non_repudiation_binding_set_hash: str = ""
    identity_mesh_binding_set_hash: str = ""
    scope_binding_set_hash: str = ""
    lifecycle_binding_set_hash: str = ""
    bindings: tuple[DelegationChainBinding, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    side_effects: DelegationChainSideEffects | None = None
    schema_version: str = DELEGATION_CHAIN_BINDING_SET_VERSION
    chain_binding_set_id: str = ""
    chain_binding_set_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        _bindings: tuple[DelegationChainBinding, ...]
        if self.bindings and not isinstance(self.bindings, (tuple, list)):
            _bindings = (self.bindings,)
        elif isinstance(self.bindings, list):
            _bindings = tuple(self.bindings)
        else:
            _bindings = self.bindings
        object.__setattr__(self, "bindings", _bindings)

        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationChainSideEffects)
            else DelegationChainSideEffects()
        )
        object.__setattr__(self, "side_effects", side_effects)

        binding_hashes = tuple(b.binding_hash for b in _bindings if b.binding_hash)

        chain_binding_set_hash = compute_chain_binding_set_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=self.delegation_identity_hash,
            role_binding_hash=self.role_binding_hash,
            constraint_set_hash=self.constraint_set_hash,
            authority_binding_set_hash=self.authority_binding_set_hash,
            non_repudiation_binding_set_hash=self.non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=self.identity_mesh_binding_set_hash,
            scope_binding_set_hash=self.scope_binding_set_hash,
            lifecycle_binding_set_hash=self.lifecycle_binding_set_hash,
            binding_hashes=binding_hashes,
            source_label=source_label,
            schema_version=schema_version,
        )
        chain_binding_set_id = f"chain-binding-set:{chain_binding_set_hash[:16]}"

        if self.chain_binding_set_hash not in ("", chain_binding_set_hash):
            raise DelegationValidationError(
                "chain_binding_set_hash does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="chain_binding_set_hash",
            )
        if self.chain_binding_set_id not in ("", chain_binding_set_id):
            raise DelegationValidationError(
                "chain_binding_set_id does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="chain_binding_set_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "chain_binding_set_hash", chain_binding_set_hash)
        object.__setattr__(self, "chain_binding_set_id", chain_binding_set_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "chain_binding_set_hash": self.chain_binding_set_hash,
            "chain_binding_set_id": self.chain_binding_set_id,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationChainBindingSet:
        validate_known_fields(
            data,
            CHAIN_BINDING_SET_KNOWN_FIELDS,
            label="delegation_chain_binding_set",
        )
        raw_bindings = data.get("bindings", ())
        bindings = tuple(
            DelegationChainBinding.from_dict(b)
            if isinstance(b, MappingABC)
            else b
            for b in raw_bindings
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data.get("delegation_identity_hash", ""),
            role_binding_hash=data.get("role_binding_hash", ""),
            constraint_set_hash=data.get("constraint_set_hash", ""),
            authority_binding_set_hash=data.get("authority_binding_set_hash", ""),
            non_repudiation_binding_set_hash=data.get(
                "non_repudiation_binding_set_hash", ""
            ),
            identity_mesh_binding_set_hash=data.get(
                "identity_mesh_binding_set_hash", ""
            ),
            scope_binding_set_hash=data.get("scope_binding_set_hash", ""),
            lifecycle_binding_set_hash=data.get("lifecycle_binding_set_hash", ""),
            bindings=bindings,
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            side_effects=data.get("side_effects"),
            schema_version=data.get(
                "schema_version", DELEGATION_CHAIN_BINDING_SET_VERSION
            ),
            chain_binding_set_id=data.get("chain_binding_set_id", ""),
            chain_binding_set_hash=data.get("chain_binding_set_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationChainSideEffects
# ---------------------------------------------------------------------------


@dataclass
class DelegationChainSideEffects:
    """Hard proof that P1.8.9 is non-executing, non-transferring,
    non-verifying, and non-mutating. All fields default to false."""

    handoff_executed: bool = False
    responsibility_transferred: bool = False
    acceptance_verified: bool = False
    authority_transferred: bool = False
    predecessor_verified: bool = False
    successor_activated: bool = False
    chain_verified: bool = False
    lineage_graph_built: bool = False
    runtime_owner_changed: bool = False
    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "acceptance_verified": self.acceptance_verified,
            "approval_created": self.approval_created,
            "authority_transferred": self.authority_transferred,
            "chain_verified": self.chain_verified,
            "custos_called": self.custos_called,
            "global_trace_written": self.global_trace_written,
            "handoff_executed": self.handoff_executed,
            "ledger_written": self.ledger_written,
            "lineage_graph_built": self.lineage_graph_built,
            "policy_called": self.policy_called,
            "predecessor_verified": self.predecessor_verified,
            "responsibility_transferred": self.responsibility_transferred,
            "runtime_mutated": self.runtime_mutated,
            "runtime_owner_changed": self.runtime_owner_changed,
            "successor_activated": self.successor_activated,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationChainSideEffects:
        validate_known_fields(
            data,
            CHAIN_SIDE_EFFECTS_KNOWN_FIELDS,
            label="delegation_chain_side_effects",
        )
        return cls(
            handoff_executed=data.get("handoff_executed", False),
            responsibility_transferred=data.get("responsibility_transferred", False),
            acceptance_verified=data.get("acceptance_verified", False),
            authority_transferred=data.get("authority_transferred", False),
            predecessor_verified=data.get("predecessor_verified", False),
            successor_activated=data.get("successor_activated", False),
            chain_verified=data.get("chain_verified", False),
            lineage_graph_built=data.get("lineage_graph_built", False),
            runtime_owner_changed=data.get("runtime_owner_changed", False),
            policy_called=data.get("policy_called", False),
            custos_called=data.get("custos_called", False),
            approval_created=data.get("approval_created", False),
            ledger_written=data.get("ledger_written", False),
            global_trace_written=data.get("global_trace_written", False),
            runtime_mutated=data.get("runtime_mutated", False),
        )


# ---------------------------------------------------------------------------
# DelegationChainStatusReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationChainStatusReport:
    """Honest P1.8.9 chain/handoff model readiness and unavailable surfaces report.

    Reports chain/handoff model readiness and unavailable surfaces.
    Does not claim chain verification, handoff execution, responsibility
    transfer, or authority transfer.
    """

    status_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    available_contracts: Mapping[str, str] | None = None
    unavailable_bindings: Mapping[str, str] | None = None
    side_effects: DelegationChainSideEffects | None = None
    schema_version: str = DELEGATION_CHAIN_STATUS_REPORT_VERSION
    status_hash: str = ""

    def __post_init__(self) -> None:
        status_label = _parse_source_label(self.status_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        if not isinstance(self.available_contracts, MappingABC):
            raise DelegationValidationError(
                "available_contracts must be a mapping",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="available_contracts",
            )
        if not isinstance(self.unavailable_bindings, MappingABC):
            raise DelegationValidationError(
                "unavailable_bindings must be a mapping",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="unavailable_bindings",
            )

        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationChainSideEffects)
            else DelegationChainSideEffects.from_dict(
                self.side_effects if self.side_effects is not None else {}
            )
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_chain_status_report_hash(
            status_label=status_label,
            available_contracts=available_contracts,
            unavailable_bindings=unavailable_bindings,
            side_effects=side_effects,
        )

        if self.status_hash not in ("", status_hash):
            raise DelegationValidationError(
                "status_hash does not match status report content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="status_hash",
            )

        object.__setattr__(self, "status_label", status_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "available_contracts", available_contracts)
        object.__setattr__(self, "unavailable_bindings", unavailable_bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "status_hash", status_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "available_contracts": dict(sorted(self.available_contracts.items())),
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "status_hash": self.status_hash,
            "status_label": self.status_label.value,
            "unavailable_bindings": dict(sorted(self.unavailable_bindings.items())),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationChainStatusReport:
        validate_known_fields(
            data,
            CHAIN_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_chain_status_report",
        )
        return cls(
            status_label=data.get("status_label", DelegationSourceLabel.DEV_FIXTURE),
            available_contracts=data.get("available_contracts", {}),
            unavailable_bindings=data.get("unavailable_bindings", {}),
            side_effects=data.get("side_effects"),
            schema_version=data.get(
                "schema_version", DELEGATION_CHAIN_STATUS_REPORT_VERSION
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Default available contracts
# ---------------------------------------------------------------------------


def _default_chain_available_contracts() -> dict[str, str]:
    return {
        "DelegationChainRef": DelegationSourceLabel.LIVE.value,
        "DelegationPredecessorRef": DelegationSourceLabel.LIVE.value,
        "DelegationSuccessorRef": DelegationSourceLabel.LIVE.value,
        "DelegationHandoffRef": DelegationSourceLabel.LIVE.value,
        "DelegationHandoffClaimRef": DelegationSourceLabel.LIVE.value,
        "DelegationHandoffAcceptanceClaimRef": DelegationSourceLabel.LIVE.value,
        "DelegationResponsibilityTransferClaimRef": DelegationSourceLabel.LIVE.value,
        "DelegationLineageMap": DelegationSourceLabel.LIVE.value,
        "DelegationChainContinuityReadinessProfile": DelegationSourceLabel.LIVE.value,
        "DelegationChainEnvelope": DelegationSourceLabel.LIVE.value,
        "DelegationChainBinding": DelegationSourceLabel.LIVE.value,
        "DelegationChainBindingSet": DelegationSourceLabel.LIVE.value,
        "DelegationChainSideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationChainStatusReport": DelegationSourceLabel.LIVE.value,
    }


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def build_delegation_chain_ref(
    delegation_ref_id: str,
    *,
    chain_link_kind: DelegationChainLinkKind = DelegationChainLinkKind.UNKNOWN,
    chain_ref: str = "",
    chain_description: str = "",
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.CHAIN_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationChainRef:
    """Build a reference-only DelegationChainRef (DEV_FIXTURE)."""
    return DelegationChainRef(
        delegation_ref_id=delegation_ref_id,
        chain_link_kind=chain_link_kind,
        chain_ref=chain_ref,
        chain_description=chain_description,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_predecessor_ref(
    delegation_ref_id: str,
    *,
    predecessor_delegation_ref: str = "",
    predecessor_context_ref: str | None = None,
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.PREDECESSOR_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationPredecessorRef:
    """Build a reference-only DelegationPredecessorRef (DEV_FIXTURE)."""
    return DelegationPredecessorRef(
        delegation_ref_id=delegation_ref_id,
        predecessor_delegation_ref=predecessor_delegation_ref,
        predecessor_context_ref=predecessor_context_ref,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_successor_ref(
    delegation_ref_id: str,
    *,
    successor_delegation_ref: str = "",
    successor_context_ref: str | None = None,
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.SUCCESSOR_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationSuccessorRef:
    """Build a reference-only DelegationSuccessorRef (DEV_FIXTURE)."""
    return DelegationSuccessorRef(
        delegation_ref_id=delegation_ref_id,
        successor_delegation_ref=successor_delegation_ref,
        successor_context_ref=successor_context_ref,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_handoff_ref(
    delegation_ref_id: str,
    *,
    handoff_kind: DelegationHandoffKind = DelegationHandoffKind.REFERENCE_ONLY,
    from_ref: str = "",
    to_ref: str = "",
    handoff_context_ref: str | None = None,
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.HANDOFF_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationHandoffRef:
    """Build a reference-only DelegationHandoffRef (DEV_FIXTURE)."""
    return DelegationHandoffRef(
        delegation_ref_id=delegation_ref_id,
        handoff_kind=handoff_kind,
        from_ref=from_ref,
        to_ref=to_ref,
        handoff_context_ref=handoff_context_ref,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_handoff_claim_ref(
    delegation_ref_id: str,
    handoff_ref_id: str,
    *,
    claim_ref: str = "",
    claim_statement: str = "",
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.HANDOFF_CLAIM_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationHandoffClaimRef:
    """Build a reference-only DelegationHandoffClaimRef (DEV_FIXTURE)."""
    return DelegationHandoffClaimRef(
        delegation_ref_id=delegation_ref_id,
        handoff_ref_id=handoff_ref_id,
        claim_ref=claim_ref,
        claim_statement=claim_statement,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_handoff_acceptance_claim_ref(
    delegation_ref_id: str,
    handoff_ref_id: str,
    *,
    acceptance_ref: str = "",
    acceptance_statement: str = "",
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.ACCEPTANCE_CLAIM_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationHandoffAcceptanceClaimRef:
    """Build a reference-only DelegationHandoffAcceptanceClaimRef (DEV_FIXTURE)."""
    return DelegationHandoffAcceptanceClaimRef(
        delegation_ref_id=delegation_ref_id,
        handoff_ref_id=handoff_ref_id,
        acceptance_ref=acceptance_ref,
        acceptance_statement=acceptance_statement,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_responsibility_transfer_claim_ref(
    delegation_ref_id: str,
    handoff_ref_id: str,
    *,
    transfer_ref: str = "",
    transfer_statement: str = "",
    reference_status: DelegationChainReferenceStatus = (
        DelegationChainReferenceStatus.TRANSFER_CLAIM_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationResponsibilityTransferClaimRef:
    """Build a reference-only DelegationResponsibilityTransferClaimRef (DEV_FIXTURE)."""
    return DelegationResponsibilityTransferClaimRef(
        delegation_ref_id=delegation_ref_id,
        handoff_ref_id=handoff_ref_id,
        transfer_ref=transfer_ref,
        transfer_statement=transfer_statement,
        reference_status=reference_status,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_lineage_map(
    delegation_ref_id: str,
    *,
    predecessor_refs: tuple[str, ...] = (),
    successor_refs: tuple[str, ...] = (),
    handoff_refs: tuple[str, ...] = (),
    chain_refs: tuple[str, ...] = (),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationLineageMap:
    """Build a reference-only DelegationLineageMap (DEV_FIXTURE)."""
    return DelegationLineageMap(
        delegation_ref_id=delegation_ref_id,
        predecessor_refs=predecessor_refs,
        successor_refs=successor_refs,
        handoff_refs=handoff_refs,
        chain_refs=chain_refs,
        source_label=source_label,
    )


def build_delegation_chain_continuity_readiness_profile(
    delegation_ref_id: str,
    *,
    has_chain_refs: bool = False,
    has_predecessor_refs: bool = False,
    has_successor_refs: bool = False,
    has_handoff_refs: bool = False,
    has_handoff_claim_refs: bool = False,
    has_acceptance_claim_refs: bool = False,
    has_transfer_claim_refs: bool = False,
    has_lifecycle_context: bool = False,
    has_scope_context: bool = False,
    has_authority_context: bool = False,
    has_evidence_context: bool = False,
    has_identity_mesh_context: bool = False,
    missing_components: tuple[str, ...] = (),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationChainContinuityReadinessProfile:
    """Build a reference-only DelegationChainContinuityReadinessProfile (DEV_FIXTURE)."""
    return DelegationChainContinuityReadinessProfile(
        delegation_ref_id=delegation_ref_id,
        has_chain_refs=has_chain_refs,
        has_predecessor_refs=has_predecessor_refs,
        has_successor_refs=has_successor_refs,
        has_handoff_refs=has_handoff_refs,
        has_handoff_claim_refs=has_handoff_claim_refs,
        has_acceptance_claim_refs=has_acceptance_claim_refs,
        has_transfer_claim_refs=has_transfer_claim_refs,
        has_lifecycle_context=has_lifecycle_context,
        has_scope_context=has_scope_context,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        has_identity_mesh_context=has_identity_mesh_context,
        missing_components=missing_components,
        source_label=source_label,
    )


def build_delegation_chain_envelope(
    delegation_ref_id: str,
    *,
    delegation_identity_hash: str = "",
    role_binding_hash: str = "",
    constraint_set_hash: str = "",
    authority_binding_set_hash: str = "",
    non_repudiation_binding_set_hash: str = "",
    identity_mesh_binding_set_hash: str = "",
    scope_binding_set_hash: str = "",
    lifecycle_binding_set_hash: str = "",
    chain_refs: tuple[str, ...] = (),
    predecessor_refs: tuple[str, ...] = (),
    successor_refs: tuple[str, ...] = (),
    handoff_refs: tuple[str, ...] = (),
    handoff_claim_refs: tuple[str, ...] = (),
    handoff_acceptance_claim_refs: tuple[str, ...] = (),
    responsibility_transfer_claim_refs: tuple[str, ...] = (),
    lineage_map_hash: str = "",
    continuity_readiness_hash: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationChainEnvelope:
    """Build a reference-only DelegationChainEnvelope (DEV_FIXTURE)."""
    return DelegationChainEnvelope(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_refs=chain_refs,
        predecessor_refs=predecessor_refs,
        successor_refs=successor_refs,
        handoff_refs=handoff_refs,
        handoff_claim_refs=handoff_claim_refs,
        handoff_acceptance_claim_refs=handoff_acceptance_claim_refs,
        responsibility_transfer_claim_refs=responsibility_transfer_claim_refs,
        lineage_map_hash=lineage_map_hash,
        continuity_readiness_hash=continuity_readiness_hash,
        source_label=source_label,
    )


def build_delegation_chain_binding(
    delegation_ref_id: str,
    *,
    delegation_identity_hash: str = "",
    role_binding_hash: str = "",
    constraint_set_hash: str = "",
    authority_binding_set_hash: str = "",
    non_repudiation_binding_set_hash: str = "",
    identity_mesh_binding_set_hash: str = "",
    scope_binding_set_hash: str = "",
    lifecycle_binding_set_hash: str = "",
    chain_envelope_hash: str = "",
    lineage_map_hash: str = "",
    continuity_readiness_hash: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    chain_status: DelegationChainStatus = DelegationChainStatus.DECLARED,
) -> DelegationChainBinding:
    """Build a reference-only DelegationChainBinding (DEV_FIXTURE)."""
    return DelegationChainBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_envelope_hash=chain_envelope_hash,
        lineage_map_hash=lineage_map_hash,
        continuity_readiness_hash=continuity_readiness_hash,
        source_label=source_label,
        chain_status=chain_status,
    )


def build_delegation_chain_binding_set(
    delegation_ref_id: str,
    *,
    delegation_identity_hash: str = "",
    role_binding_hash: str = "",
    constraint_set_hash: str = "",
    authority_binding_set_hash: str = "",
    non_repudiation_binding_set_hash: str = "",
    identity_mesh_binding_set_hash: str = "",
    scope_binding_set_hash: str = "",
    lifecycle_binding_set_hash: str = "",
    bindings: tuple[DelegationChainBinding, ...] = (),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationChainBindingSet:
    """Build a reference-only DelegationChainBindingSet (DEV_FIXTURE)."""
    return DelegationChainBindingSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        bindings=bindings,
        source_label=source_label,
    )


def build_delegation_chain_status_report() -> DelegationChainStatusReport:
    """Return honest P1.8.9 chain/handoff status report (non-executing)."""
    return DelegationChainStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_chain_available_contracts(),
        unavailable_bindings=DELEGATION_CHAIN_UNAVAILABLE_BINDINGS,
        side_effects=DelegationChainSideEffects(),
    )


# ---------------------------------------------------------------------------
# Serialize helpers
# ---------------------------------------------------------------------------


def serialize_delegation_chain_envelope(
    envelope: DelegationChainEnvelope,
) -> str:
    """Serialize DelegationChainEnvelope to deterministic canonical JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_chain_binding_set(
    binding_set: DelegationChainBindingSet,
) -> str:
    """Serialize DelegationChainBindingSet to deterministic canonical JSON."""
    return to_canonical_json(binding_set)


# ---------------------------------------------------------------------------
# Hash helpers (return stored hash from object)
# ---------------------------------------------------------------------------


def hash_delegation_chain_ref(ref: DelegationChainRef) -> str:
    """Return stable chain_hash for DelegationChainRef content."""
    return ref.chain_hash


def hash_delegation_predecessor_ref(ref: DelegationPredecessorRef) -> str:
    """Return stable predecessor_hash for DelegationPredecessorRef content."""
    return ref.predecessor_hash


def hash_delegation_successor_ref(ref: DelegationSuccessorRef) -> str:
    """Return stable successor_hash for DelegationSuccessorRef content."""
    return ref.successor_hash


def hash_delegation_handoff_ref(ref: DelegationHandoffRef) -> str:
    """Return stable handoff_hash for DelegationHandoffRef content."""
    return ref.handoff_hash


def hash_delegation_handoff_claim_ref(ref: DelegationHandoffClaimRef) -> str:
    """Return stable handoff_claim_hash for DelegationHandoffClaimRef content."""
    return ref.handoff_claim_hash


def hash_delegation_handoff_acceptance_claim_ref(
    ref: DelegationHandoffAcceptanceClaimRef,
) -> str:
    """Return stable acceptance_claim_hash for DelegationHandoffAcceptanceClaimRef content."""
    return ref.acceptance_claim_hash


def hash_delegation_responsibility_transfer_claim_ref(
    ref: DelegationResponsibilityTransferClaimRef,
) -> str:
    """Return stable transfer_claim_hash for DelegationResponsibilityTransferClaimRef content."""
    return ref.transfer_claim_hash


def hash_delegation_lineage_map(map_: DelegationLineageMap) -> str:
    """Return stable lineage_map_hash for DelegationLineageMap content."""
    return map_.lineage_map_hash


def hash_delegation_chain_continuity_readiness_profile(
    profile: DelegationChainContinuityReadinessProfile,
) -> str:
    """Return stable readiness_hash for DelegationChainContinuityReadinessProfile content."""
    return profile.readiness_hash


def hash_delegation_chain_envelope(envelope: DelegationChainEnvelope) -> str:
    """Return stable chain_envelope_hash for DelegationChainEnvelope content."""
    return envelope.chain_envelope_hash


def hash_delegation_chain_binding(binding: DelegationChainBinding) -> str:
    """Return stable binding_hash for DelegationChainBinding content."""
    return binding.binding_hash


def hash_delegation_chain_binding_set(
    binding_set: DelegationChainBindingSet,
) -> str:
    """Return stable chain_binding_set_hash for DelegationChainBindingSet content."""
    return binding_set.chain_binding_set_hash
