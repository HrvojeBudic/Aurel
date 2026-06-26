"""Delegation expiry / revocation lifecycle reference model (P1.8.8).

Deterministic, versioned, JSON-safe, side-effect-free delegation lifecycle
reference layer. Binds reference-only expiry refs, revocation refs,
suspension refs, renewal refs, supersession refs, revocation reason refs,
lifecycle readiness profile, and lifecycle envelope to DelegationRef /
DelegationIdentity / DelegationRoleBindingSet / DelegationConstraintSet /
DelegationAuthorityBindingSet / DelegationNonRepudiationBindingSet /
DelegationIdentityMeshBindingSet / DelegationScopeBindingSet without
runtime expiry, runtime revocation, scheduler activation, permission
removal, authority mutation, approval creation, policy/Custos decisioning,
trace write, Ledger write, runtime cancellation, or runtime mutation.

Architectural law:
  - ExpiryRef exists does not mean delegation expired.
  - RevocationRef exists does not mean delegation revoked.
  - SuspensionRef exists does not mean runtime paused.
  - RenewalRef exists does not mean authority renewed.
  - SupersessionRef exists does not mean old delegation invalidated.
  - ReasonRef exists does not mean reason verified.
  - LifecycleEnvelope exists does not mean lifecycle enforced.
  - LifecycleReadinessProfile exists does not mean scheduler active.
  - Lifecycle hash exists does not mean TRACE_VERIFIED.
  - DelegationExpiryRef exists ≠ runtime expiry.
  - DelegationRevocationRef exists ≠ runtime revocation.
  - DelegationSuspensionRef exists ≠ runtime pause.
  - DelegationRenewalRef exists ≠ authority renewed.
  - DelegationSupersessionRef exists ≠ old delegation invalidated.
  - DelegationRevocationReasonRef exists ≠ verified reason.
  - DelegationLifecycleEnvelope exists ≠ lifecycle enforcement.
  - DelegationLifecycleReadinessProfile exists ≠ scheduler active.
  - lifecycle_envelope_hash exists ≠ TRACE_VERIFIED.
  - lifecycle_binding_set_hash exists ≠ proof of revocation or expiry.
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

DELEGATION_LIFECYCLE_TASK_ID = "P1.8.8"
DELEGATION_EXPIRY_REF_VERSION = "delegation_expiry_ref.v1"
DELEGATION_REVOCATION_REF_VERSION = "delegation_revocation_ref.v1"
DELEGATION_SUSPENSION_REF_VERSION = "delegation_suspension_ref.v1"
DELEGATION_RENEWAL_REF_VERSION = "delegation_renewal_ref.v1"
DELEGATION_SUPERSESSION_REF_VERSION = "delegation_supersession_ref.v1"
DELEGATION_REVOCATION_REASON_REF_VERSION = "delegation_revocation_reason_ref.v1"
DELEGATION_LIFECYCLE_READINESS_PROFILE_VERSION = "delegation_lifecycle_readiness_profile.v1"
DELEGATION_LIFECYCLE_ENVELOPE_VERSION = "delegation_lifecycle_envelope.v1"
DELEGATION_LIFECYCLE_BINDING_VERSION = "delegation_lifecycle_binding.v1"
DELEGATION_LIFECYCLE_BINDING_SET_VERSION = "delegation_lifecycle_binding_set.v1"
DELEGATION_LIFECYCLE_SIDE_EFFECTS_VERSION = "delegation_lifecycle_side_effects.v1"
DELEGATION_LIFECYCLE_STATUS_REPORT_VERSION = "delegation_lifecycle_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_LIFECYCLE_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.8; "
        "lifecycle schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.8"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.8 lifecycle reference layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.8 "
        "lifecycle reference layer"
    ),
    "Runtime Expiry Engine": (
        "Runtime expiry engine scheduled for later P1.8 tasks; not P1.8.8"
    ),
    "Runtime Revocation Engine": (
        "Runtime revocation engine scheduled for later P1.8 tasks; not P1.8.8"
    ),
    "Runtime Suspension Engine": (
        "Runtime suspension is not available in P1.8.8; "
        "suspension refs are reference-only"
    ),
    "Authority Renewal": (
        "Authority renewal scheduled for later P1.8 tasks; not P1.8.8"
    ),
    "Supersession Enforcement": (
        "Supersession enforcement is not available in P1.8.8; "
        "supersession refs are reference-only"
    ),
    "Permission Removal": (
        "Permission removal is not available in P1.8.8; "
        "lifecycle refs are reference-only"
    ),
    "Scheduler/Timer Activation": (
        "Scheduler/timer activation is not available in P1.8.8; "
        "expiry refs are reference-only"
    ),
    "Runtime Cancellation": (
        "Runtime cancellation scheduled for later P1.8 tasks; not P1.8.8"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision scheduled for later P1.8 tasks; not P1.8.8"
    ),
    "Approval Creation": (
        "Approval creation is not available in P1.8.8; "
        "lifecycle refs are reference-only"
    ),
    "P1.8.9 Chain/Handoff Model": (
        "P1.8.9 chain/handoff model is not available in P1.8.8"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 provenance/disclosure layer is not "
        "available in P1.8.8"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.8"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world)
# ---------------------------------------------------------------------------

EXPIRY_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "expiry_ref_id",
    "delegation_ref_id",
    "expiry_ref",
    "expiry_description",
    "reference_status",
    "source_label",
    "lifecycle_status",
    "expiry_hash",
})

REVOCATION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "revocation_ref_id",
    "delegation_ref_id",
    "revocation_ref",
    "revocation_description",
    "reason_ref_id",
    "reference_status",
    "source_label",
    "lifecycle_status",
    "revocation_hash",
})

SUSPENSION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "suspension_ref_id",
    "delegation_ref_id",
    "suspension_ref",
    "suspension_description",
    "reference_status",
    "source_label",
    "lifecycle_status",
    "suspension_hash",
})

RENEWAL_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "renewal_ref_id",
    "delegation_ref_id",
    "renewal_ref",
    "renewal_description",
    "reference_status",
    "source_label",
    "lifecycle_status",
    "renewal_hash",
})

SUPERSESSION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "supersession_ref_id",
    "delegation_ref_id",
    "supersession_ref",
    "superseded_by_ref",
    "supersession_description",
    "reference_status",
    "source_label",
    "lifecycle_status",
    "supersession_hash",
})

REASON_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "reason_ref_id",
    "delegation_ref_id",
    "reason_kind",
    "reason_ref",
    "reason_description",
    "source_label",
    "lifecycle_status",
    "reason_hash",
})

LIFECYCLE_READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "lifecycle_readiness_profile_id",
    "delegation_ref_id",
    "has_expiry_refs",
    "has_revocation_refs",
    "has_suspension_refs",
    "has_renewal_refs",
    "has_supersession_refs",
    "has_reason_refs",
    "has_scope_context",
    "has_authority_context",
    "has_evidence_context",
    "has_identity_mesh_context",
    "missing_components",
    "enforcement_unavailable_reason",
    "scheduler_unavailable_reason",
    "source_label",
    "readiness_hash",
})

LIFECYCLE_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "lifecycle_envelope_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "expiry_refs",
    "revocation_refs",
    "suspension_refs",
    "renewal_refs",
    "supersession_refs",
    "reason_refs",
    "lifecycle_readiness_hash",
    "source_label",
    "lifecycle_envelope_hash",
})

LIFECYCLE_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
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
    "lifecycle_envelope_hash",
    "lifecycle_readiness_hash",
    "source_label",
    "lifecycle_status",
    "binding_hash",
})

LIFECYCLE_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "lifecycle_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_binding_set_hash",
    "bindings",
    "source_label",
    "lifecycle_binding_set_hash",
    "side_effects",
})

LIFECYCLE_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "runtime_expired",
    "runtime_revoked",
    "runtime_suspended",
    "authority_renewed",
    "delegation_superseded",
    "permission_removed",
    "scheduler_activated",
    "runtime_cancelled",
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

LIFECYCLE_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationLifecycleEventKind(str, Enum):
    """Declared lifecycle event kind; event kind does not change runtime state
    or enforce expiry/revocation."""

    EXPIRY = "EXPIRY"
    REVOCATION = "REVOCATION"
    SUSPENSION = "SUSPENSION"
    RENEWAL = "RENEWAL"
    SUPERSESSION = "SUPERSESSION"
    REASON = "REASON"
    UNKNOWN = "UNKNOWN"


class DelegationLifecycleReferenceStatus(str, Enum):
    """Lifecycle reference state.

    EXPIRY_REFERENCED is not runtime expired.
    REVOCATION_REFERENCED is not runtime revoked.
    SUSPENSION_REFERENCED is not runtime paused.
    RENEWAL_REFERENCED is not authority renewed.
    SUPERSESSION_REFERENCED is not old delegation invalidated.
    ENFORCEMENT_UNAVAILABLE is honest unavailability, not success/failure.
    SCHEDULER_UNAVAILABLE is honest unavailability, not scheduler state.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    EXPIRY_REFERENCED = "EXPIRY_REFERENCED"
    REVOCATION_REFERENCED = "REVOCATION_REFERENCED"
    SUSPENSION_REFERENCED = "SUSPENSION_REFERENCED"
    RENEWAL_REFERENCED = "RENEWAL_REFERENCED"
    SUPERSESSION_REFERENCED = "SUPERSESSION_REFERENCED"
    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    SCHEDULER_UNAVAILABLE = "SCHEDULER_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationLifecycleStatus(str, Enum):
    """Lifecycle context status.

    REFERENCE_ONLY means lifecycle context is reference-only.
    DECLARED means lifecycle context was declared as metadata.
    Neither means runtime expiry, revocation, suspension, renewal,
    or supersession occurred.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationRevocationReasonKind(str, Enum):
    """Declared revocation reason category.

    Reason kind classifies the reason reference.
    It does not verify reason truth.
    It does not enforce revocation.
    It does not represent policy/Custos decision.
    """

    OPERATOR_DECLARED = "OPERATOR_DECLARED"
    POLICY_CONTEXT = "POLICY_CONTEXT"
    AUTHORITY_CONTEXT = "AUTHORITY_CONTEXT"
    SCOPE_CONTEXT = "SCOPE_CONTEXT"
    RISK_CONTEXT = "RISK_CONTEXT"
    EVIDENCE_CONTEXT = "EVIDENCE_CONTEXT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parse helpers
# ---------------------------------------------------------------------------


def _parse_lifecycle_event_kind(
    value: DelegationLifecycleEventKind | str,
) -> DelegationLifecycleEventKind:
    if isinstance(value, DelegationLifecycleEventKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationLifecycleEventKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid lifecycle event kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="event_kind",
            ) from exc
    raise DelegationError(
        "event_kind must be a string or DelegationLifecycleEventKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="event_kind",
    )


def _parse_lifecycle_reference_status(
    value: DelegationLifecycleReferenceStatus | str,
) -> DelegationLifecycleReferenceStatus:
    if isinstance(value, DelegationLifecycleReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationLifecycleReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationLifecycleReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )


def _parse_lifecycle_status(
    value: DelegationLifecycleStatus | str,
) -> DelegationLifecycleStatus:
    if isinstance(value, DelegationLifecycleStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationLifecycleStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid lifecycle_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="lifecycle_status",
            ) from exc
    raise DelegationError(
        "lifecycle_status must be a string or DelegationLifecycleStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="lifecycle_status",
    )


def _parse_reason_kind(
    value: DelegationRevocationReasonKind | str,
) -> DelegationRevocationReasonKind:
    if isinstance(value, DelegationRevocationReasonKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationRevocationReasonKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reason_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reason_kind",
            ) from exc
    raise DelegationError(
        "reason_kind must be a string or DelegationRevocationReasonKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reason_kind",
    )


# ---------------------------------------------------------------------------
# Hash compute helpers
# ---------------------------------------------------------------------------


def compute_expiry_ref_hash(
    *,
    expiry_ref: str,
    expiry_description: str,
    delegation_ref_id: str,
    reference_status: DelegationLifecycleReferenceStatus,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_EXPIRY_REF_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "expiry_description": expiry_description,
        "expiry_ref": expiry_ref,
        "lifecycle_status": lifecycle_status.value,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_revocation_ref_hash(
    *,
    revocation_ref: str,
    revocation_description: str,
    delegation_ref_id: str,
    reason_ref_id: str | None,
    reference_status: DelegationLifecycleReferenceStatus,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_REVOCATION_REF_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "delegation_ref_id": delegation_ref_id,
        "lifecycle_status": lifecycle_status.value,
        "reference_status": reference_status.value,
        "revocation_description": revocation_description,
        "revocation_ref": revocation_ref,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if reason_ref_id is not None:
        payload["reason_ref_id"] = reason_ref_id
    return stable_hash(payload)


def compute_suspension_ref_hash(
    *,
    suspension_ref: str,
    suspension_description: str,
    delegation_ref_id: str,
    reference_status: DelegationLifecycleReferenceStatus,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_SUSPENSION_REF_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "lifecycle_status": lifecycle_status.value,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "suspension_description": suspension_description,
        "suspension_ref": suspension_ref,
    })


def compute_renewal_ref_hash(
    *,
    renewal_ref: str,
    renewal_description: str,
    delegation_ref_id: str,
    reference_status: DelegationLifecycleReferenceStatus,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_RENEWAL_REF_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "lifecycle_status": lifecycle_status.value,
        "reference_status": reference_status.value,
        "renewal_description": renewal_description,
        "renewal_ref": renewal_ref,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_supersession_ref_hash(
    *,
    supersession_ref: str,
    superseded_by_ref: str | None,
    supersession_description: str,
    delegation_ref_id: str,
    reference_status: DelegationLifecycleReferenceStatus,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_SUPERSESSION_REF_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "delegation_ref_id": delegation_ref_id,
        "lifecycle_status": lifecycle_status.value,
        "reference_status": reference_status.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "supersession_description": supersession_description,
        "supersession_ref": supersession_ref,
    }
    if superseded_by_ref is not None:
        payload["superseded_by_ref"] = superseded_by_ref
    return stable_hash(payload)


def compute_reason_ref_hash(
    *,
    reason_kind: DelegationRevocationReasonKind,
    reason_ref: str,
    reason_description: str,
    delegation_ref_id: str,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_REVOCATION_REASON_REF_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "lifecycle_status": lifecycle_status.value,
        "reason_description": reason_description,
        "reason_kind": reason_kind.value,
        "reason_ref": reason_ref,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


def compute_lifecycle_readiness_hash(
    *,
    delegation_ref_id: str,
    has_expiry_refs: bool,
    has_revocation_refs: bool,
    has_suspension_refs: bool,
    has_renewal_refs: bool,
    has_supersession_refs: bool,
    has_reason_refs: bool,
    has_scope_context: bool,
    has_authority_context: bool,
    has_evidence_context: bool,
    has_identity_mesh_context: bool,
    missing_components: tuple[str, ...],
    enforcement_unavailable_reason: str,
    scheduler_unavailable_reason: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_LIFECYCLE_READINESS_PROFILE_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "enforcement_unavailable_reason": enforcement_unavailable_reason,
        "has_authority_context": has_authority_context,
        "has_evidence_context": has_evidence_context,
        "has_expiry_refs": has_expiry_refs,
        "has_identity_mesh_context": has_identity_mesh_context,
        "has_reason_refs": has_reason_refs,
        "has_renewal_refs": has_renewal_refs,
        "has_revocation_refs": has_revocation_refs,
        "has_scope_context": has_scope_context,
        "has_supersession_refs": has_supersession_refs,
        "has_suspension_refs": has_suspension_refs,
        "missing_components": sorted(missing_components),
        "schema_version": schema_version,
        "scheduler_unavailable_reason": scheduler_unavailable_reason,
        "source_label": source_label.value,
    })


def compute_lifecycle_envelope_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    expiry_refs: tuple[str, ...],
    revocation_refs: tuple[str, ...],
    suspension_refs: tuple[str, ...],
    renewal_refs: tuple[str, ...],
    supersession_refs: tuple[str, ...],
    reason_refs: tuple[str, ...],
    lifecycle_readiness_hash: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_LIFECYCLE_ENVELOPE_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "expiry_refs": sorted(expiry_refs),
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "lifecycle_readiness_hash": lifecycle_readiness_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "reason_refs": sorted(reason_refs),
        "renewal_refs": sorted(renewal_refs),
        "revocation_refs": sorted(revocation_refs),
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_binding_set_hash": scope_binding_set_hash,
        "source_label": source_label.value,
        "supersession_refs": sorted(supersession_refs),
        "suspension_refs": sorted(suspension_refs),
    })


def compute_lifecycle_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_envelope_hash: str,
    lifecycle_readiness_hash: str,
    source_label: DelegationSourceLabel,
    lifecycle_status: DelegationLifecycleStatus,
    schema_version: str = DELEGATION_LIFECYCLE_BINDING_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "lifecycle_envelope_hash": lifecycle_envelope_hash,
        "lifecycle_readiness_hash": lifecycle_readiness_hash,
        "lifecycle_status": lifecycle_status.value,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_binding_set_hash": scope_binding_set_hash,
        "source_label": source_label.value,
    })


def compute_lifecycle_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    binding_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_LIFECYCLE_BINDING_SET_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "binding_hashes": sorted(binding_hashes),
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_binding_set_hash": scope_binding_set_hash,
        "source_label": source_label.value,
    })


def compute_lifecycle_status_report_hash(
    *,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: "DelegationLifecycleSideEffects",
) -> str:
    return stable_hash({
        "available_contracts": dict(sorted(available_contracts.items())),
        "side_effects": side_effects.to_canonical_dict(),
        "status_label": status_label.value,
        "unavailable_bindings": dict(sorted(unavailable_bindings.items())),
    })


# ---------------------------------------------------------------------------
# DelegationExpiryRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationExpiryRef:
    """Reference-only expiry metadata.

    DelegationExpiryRef describes expiry metadata.
    It does not expire delegation in runtime.
    It does not activate scheduler.
    It does not cancel execution.
    It does not remove permission or authority.
    """

    expiry_ref: str
    delegation_ref_id: str
    expiry_description: str = ""
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.EXPIRY_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED
    schema_version: str = DELEGATION_EXPIRY_REF_VERSION
    expiry_ref_id: str = ""
    expiry_hash: str = ""

    def __post_init__(self) -> None:
        expiry_ref = _required_string(self.expiry_ref, field_name="expiry_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        reference_status = _parse_lifecycle_reference_status(self.reference_status)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        expiry_description = (
            self.expiry_description.strip()
            if isinstance(self.expiry_description, str)
            else ""
        )

        expiry_hash = compute_expiry_ref_hash(
            expiry_ref=expiry_ref,
            expiry_description=expiry_description,
            delegation_ref_id=delegation_ref_id,
            reference_status=reference_status,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        expiry_ref_id = f"expiry:{expiry_hash[:16]}"

        if self.expiry_hash not in ("", expiry_hash):
            raise DelegationValidationError(
                "expiry_hash does not match expiry content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="expiry_hash",
            )
        if self.expiry_ref_id not in ("", expiry_ref_id):
            raise DelegationValidationError(
                "expiry_ref_id does not match expiry content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="expiry_ref_id",
            )

        object.__setattr__(self, "expiry_ref", expiry_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "expiry_description", expiry_description)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "expiry_hash", expiry_hash)
        object.__setattr__(self, "expiry_ref_id", expiry_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "expiry_description": self.expiry_description,
            "expiry_hash": self.expiry_hash,
            "expiry_ref": self.expiry_ref,
            "expiry_ref_id": self.expiry_ref_id,
            "lifecycle_status": self.lifecycle_status.value,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationExpiryRef:
        validate_known_fields(data, EXPIRY_REF_KNOWN_FIELDS, label="delegation_expiry_ref")
        return cls(
            expiry_ref=data["expiry_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            expiry_description=data.get("expiry_description", ""),
            reference_status=data.get(
                "reference_status",
                DelegationLifecycleReferenceStatus.EXPIRY_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.DECLARED,
            ),
            schema_version=data.get("schema_version", DELEGATION_EXPIRY_REF_VERSION),
            expiry_ref_id=data.get("expiry_ref_id", ""),
            expiry_hash=data.get("expiry_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRevocationRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationRevocationRef:
    """Reference-only revocation metadata.

    DelegationRevocationRef describes revocation metadata.
    It does not revoke delegation in runtime.
    It does not remove permission.
    It does not mutate authority.
    It does not cancel execution.
    """

    revocation_ref: str
    delegation_ref_id: str
    revocation_description: str = ""
    reason_ref_id: str | None = None
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.REVOCATION_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED
    schema_version: str = DELEGATION_REVOCATION_REF_VERSION
    revocation_ref_id: str = ""
    revocation_hash: str = ""

    def __post_init__(self) -> None:
        revocation_ref = _required_string(self.revocation_ref, field_name="revocation_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        reference_status = _parse_lifecycle_reference_status(self.reference_status)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        revocation_description = (
            self.revocation_description.strip()
            if isinstance(self.revocation_description, str)
            else ""
        )
        reason_ref_id = _optional_string(self.reason_ref_id)

        revocation_hash = compute_revocation_ref_hash(
            revocation_ref=revocation_ref,
            revocation_description=revocation_description,
            delegation_ref_id=delegation_ref_id,
            reason_ref_id=reason_ref_id,
            reference_status=reference_status,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        revocation_ref_id = f"revocation:{revocation_hash[:16]}"

        if self.revocation_hash not in ("", revocation_hash):
            raise DelegationValidationError(
                "revocation_hash does not match revocation content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="revocation_hash",
            )
        if self.revocation_ref_id not in ("", revocation_ref_id):
            raise DelegationValidationError(
                "revocation_ref_id does not match revocation content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="revocation_ref_id",
            )

        object.__setattr__(self, "revocation_ref", revocation_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "revocation_description", revocation_description)
        object.__setattr__(self, "reason_ref_id", reason_ref_id)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "revocation_hash", revocation_hash)
        object.__setattr__(self, "revocation_ref_id", revocation_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "delegation_ref_id": self.delegation_ref_id,
            "lifecycle_status": self.lifecycle_status.value,
            "reference_status": self.reference_status.value,
            "revocation_description": self.revocation_description,
            "revocation_hash": self.revocation_hash,
            "revocation_ref": self.revocation_ref,
            "revocation_ref_id": self.revocation_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.reason_ref_id is not None:
            result["reason_ref_id"] = self.reason_ref_id
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRevocationRef:
        validate_known_fields(
            data, REVOCATION_REF_KNOWN_FIELDS, label="delegation_revocation_ref"
        )
        return cls(
            revocation_ref=data["revocation_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            revocation_description=data.get("revocation_description", ""),
            reason_ref_id=data.get("reason_ref_id", None),
            reference_status=data.get(
                "reference_status",
                DelegationLifecycleReferenceStatus.REVOCATION_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.DECLARED,
            ),
            schema_version=data.get("schema_version", DELEGATION_REVOCATION_REF_VERSION),
            revocation_ref_id=data.get("revocation_ref_id", ""),
            revocation_hash=data.get("revocation_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationSuspensionRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationSuspensionRef:
    """Reference-only suspension metadata.

    DelegationSuspensionRef describes suspension metadata.
    It does not pause runtime.
    It does not suspend execution.
    It does not block tasks.
    """

    suspension_ref: str
    delegation_ref_id: str
    suspension_description: str = ""
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.SUSPENSION_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED
    schema_version: str = DELEGATION_SUSPENSION_REF_VERSION
    suspension_ref_id: str = ""
    suspension_hash: str = ""

    def __post_init__(self) -> None:
        suspension_ref = _required_string(self.suspension_ref, field_name="suspension_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        reference_status = _parse_lifecycle_reference_status(self.reference_status)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        suspension_description = (
            self.suspension_description.strip()
            if isinstance(self.suspension_description, str)
            else ""
        )

        suspension_hash = compute_suspension_ref_hash(
            suspension_ref=suspension_ref,
            suspension_description=suspension_description,
            delegation_ref_id=delegation_ref_id,
            reference_status=reference_status,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        suspension_ref_id = f"suspension:{suspension_hash[:16]}"

        if self.suspension_hash not in ("", suspension_hash):
            raise DelegationValidationError(
                "suspension_hash does not match suspension content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="suspension_hash",
            )
        if self.suspension_ref_id not in ("", suspension_ref_id):
            raise DelegationValidationError(
                "suspension_ref_id does not match suspension content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="suspension_ref_id",
            )

        object.__setattr__(self, "suspension_ref", suspension_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "suspension_description", suspension_description)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "suspension_hash", suspension_hash)
        object.__setattr__(self, "suspension_ref_id", suspension_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "lifecycle_status": self.lifecycle_status.value,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "suspension_description": self.suspension_description,
            "suspension_hash": self.suspension_hash,
            "suspension_ref": self.suspension_ref,
            "suspension_ref_id": self.suspension_ref_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationSuspensionRef:
        validate_known_fields(
            data, SUSPENSION_REF_KNOWN_FIELDS, label="delegation_suspension_ref"
        )
        return cls(
            suspension_ref=data["suspension_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            suspension_description=data.get("suspension_description", ""),
            reference_status=data.get(
                "reference_status",
                DelegationLifecycleReferenceStatus.SUSPENSION_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.DECLARED,
            ),
            schema_version=data.get("schema_version", DELEGATION_SUSPENSION_REF_VERSION),
            suspension_ref_id=data.get("suspension_ref_id", ""),
            suspension_hash=data.get("suspension_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRenewalRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationRenewalRef:
    """Reference-only renewal metadata.

    DelegationRenewalRef describes renewal metadata.
    It does not renew authority.
    It does not extend runtime permission.
    It does not reauthorize delegation.
    """

    renewal_ref: str
    delegation_ref_id: str
    renewal_description: str = ""
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.RENEWAL_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED
    schema_version: str = DELEGATION_RENEWAL_REF_VERSION
    renewal_ref_id: str = ""
    renewal_hash: str = ""

    def __post_init__(self) -> None:
        renewal_ref = _required_string(self.renewal_ref, field_name="renewal_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        reference_status = _parse_lifecycle_reference_status(self.reference_status)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        renewal_description = (
            self.renewal_description.strip()
            if isinstance(self.renewal_description, str)
            else ""
        )

        renewal_hash = compute_renewal_ref_hash(
            renewal_ref=renewal_ref,
            renewal_description=renewal_description,
            delegation_ref_id=delegation_ref_id,
            reference_status=reference_status,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        renewal_ref_id = f"renewal:{renewal_hash[:16]}"

        if self.renewal_hash not in ("", renewal_hash):
            raise DelegationValidationError(
                "renewal_hash does not match renewal content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="renewal_hash",
            )
        if self.renewal_ref_id not in ("", renewal_ref_id):
            raise DelegationValidationError(
                "renewal_ref_id does not match renewal content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="renewal_ref_id",
            )

        object.__setattr__(self, "renewal_ref", renewal_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "renewal_description", renewal_description)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "renewal_hash", renewal_hash)
        object.__setattr__(self, "renewal_ref_id", renewal_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "lifecycle_status": self.lifecycle_status.value,
            "reference_status": self.reference_status.value,
            "renewal_description": self.renewal_description,
            "renewal_hash": self.renewal_hash,
            "renewal_ref": self.renewal_ref,
            "renewal_ref_id": self.renewal_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRenewalRef:
        validate_known_fields(data, RENEWAL_REF_KNOWN_FIELDS, label="delegation_renewal_ref")
        return cls(
            renewal_ref=data["renewal_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            renewal_description=data.get("renewal_description", ""),
            reference_status=data.get(
                "reference_status",
                DelegationLifecycleReferenceStatus.RENEWAL_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.DECLARED,
            ),
            schema_version=data.get("schema_version", DELEGATION_RENEWAL_REF_VERSION),
            renewal_ref_id=data.get("renewal_ref_id", ""),
            renewal_hash=data.get("renewal_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationSupersessionRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationSupersessionRef:
    """Reference-only supersession metadata.

    DelegationSupersessionRef describes supersession metadata.
    It does not invalidate old delegation.
    It does not activate replacement delegation.
    It does not rewrite delegation history.
    """

    supersession_ref: str
    delegation_ref_id: str
    superseded_by_ref: str | None = None
    supersession_description: str = ""
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.SUPERSESSION_REFERENCED
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED
    schema_version: str = DELEGATION_SUPERSESSION_REF_VERSION
    supersession_ref_id: str = ""
    supersession_hash: str = ""

    def __post_init__(self) -> None:
        supersession_ref = _required_string(
            self.supersession_ref, field_name="supersession_ref"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        reference_status = _parse_lifecycle_reference_status(self.reference_status)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        supersession_description = (
            self.supersession_description.strip()
            if isinstance(self.supersession_description, str)
            else ""
        )
        superseded_by_ref = _optional_string(self.superseded_by_ref)

        supersession_hash = compute_supersession_ref_hash(
            supersession_ref=supersession_ref,
            superseded_by_ref=superseded_by_ref,
            supersession_description=supersession_description,
            delegation_ref_id=delegation_ref_id,
            reference_status=reference_status,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        supersession_ref_id = f"supersession:{supersession_hash[:16]}"

        if self.supersession_hash not in ("", supersession_hash):
            raise DelegationValidationError(
                "supersession_hash does not match supersession content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="supersession_hash",
            )
        if self.supersession_ref_id not in ("", supersession_ref_id):
            raise DelegationValidationError(
                "supersession_ref_id does not match supersession content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="supersession_ref_id",
            )

        object.__setattr__(self, "supersession_ref", supersession_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "superseded_by_ref", superseded_by_ref)
        object.__setattr__(self, "supersession_description", supersession_description)
        object.__setattr__(self, "reference_status", reference_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "supersession_hash", supersession_hash)
        object.__setattr__(self, "supersession_ref_id", supersession_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "delegation_ref_id": self.delegation_ref_id,
            "lifecycle_status": self.lifecycle_status.value,
            "reference_status": self.reference_status.value,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "supersession_description": self.supersession_description,
            "supersession_hash": self.supersession_hash,
            "supersession_ref": self.supersession_ref,
            "supersession_ref_id": self.supersession_ref_id,
        }
        if self.superseded_by_ref is not None:
            result["superseded_by_ref"] = self.superseded_by_ref
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationSupersessionRef:
        validate_known_fields(
            data, SUPERSESSION_REF_KNOWN_FIELDS, label="delegation_supersession_ref"
        )
        return cls(
            supersession_ref=data["supersession_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            superseded_by_ref=data.get("superseded_by_ref", None),
            supersession_description=data.get("supersession_description", ""),
            reference_status=data.get(
                "reference_status",
                DelegationLifecycleReferenceStatus.SUPERSESSION_REFERENCED,
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.DECLARED,
            ),
            schema_version=data.get("schema_version", DELEGATION_SUPERSESSION_REF_VERSION),
            supersession_ref_id=data.get("supersession_ref_id", ""),
            supersession_hash=data.get("supersession_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRevocationReasonRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationRevocationReasonRef:
    """Reference-only revocation reason metadata.

    DelegationRevocationReasonRef describes reason metadata.
    It does not verify reason truth.
    It does not prove revocation validity.
    It does not represent policy/Custos decision.
    It does not enforce revocation.
    """

    reason_ref: str
    delegation_ref_id: str
    reason_kind: DelegationRevocationReasonKind = (
        DelegationRevocationReasonKind.OPERATOR_DECLARED
    )
    reason_description: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED
    schema_version: str = DELEGATION_REVOCATION_REASON_REF_VERSION
    reason_ref_id: str = ""
    reason_hash: str = ""

    def __post_init__(self) -> None:
        reason_ref = _required_string(self.reason_ref, field_name="reason_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        reason_kind = _parse_reason_kind(self.reason_kind)
        source_label = _parse_source_label(self.source_label)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        reason_description = (
            self.reason_description.strip()
            if isinstance(self.reason_description, str)
            else ""
        )

        reason_hash = compute_reason_ref_hash(
            reason_kind=reason_kind,
            reason_ref=reason_ref,
            reason_description=reason_description,
            delegation_ref_id=delegation_ref_id,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        reason_ref_id = f"reason:{reason_hash[:16]}"

        if self.reason_hash not in ("", reason_hash):
            raise DelegationValidationError(
                "reason_hash does not match reason content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="reason_hash",
            )
        if self.reason_ref_id not in ("", reason_ref_id):
            raise DelegationValidationError(
                "reason_ref_id does not match reason content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="reason_ref_id",
            )

        object.__setattr__(self, "reason_ref", reason_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "reason_kind", reason_kind)
        object.__setattr__(self, "reason_description", reason_description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "reason_hash", reason_hash)
        object.__setattr__(self, "reason_ref_id", reason_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "lifecycle_status": self.lifecycle_status.value,
            "reason_description": self.reason_description,
            "reason_hash": self.reason_hash,
            "reason_kind": self.reason_kind.value,
            "reason_ref": self.reason_ref,
            "reason_ref_id": self.reason_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRevocationReasonRef:
        validate_known_fields(
            data, REASON_REF_KNOWN_FIELDS, label="delegation_revocation_reason_ref"
        )
        return cls(
            reason_ref=data["reason_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            reason_kind=data.get(
                "reason_kind",
                DelegationRevocationReasonKind.OPERATOR_DECLARED,
            ),
            reason_description=data.get("reason_description", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.DECLARED,
            ),
            schema_version=data.get("schema_version", DELEGATION_REVOCATION_REASON_REF_VERSION),
            reason_ref_id=data.get("reason_ref_id", ""),
            reason_hash=data.get("reason_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationLifecycleReadinessProfile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLifecycleReadinessProfile:
    """Present/missing lifecycle component profile.

    LifecycleReadinessProfile is presence/absence information.
    It is not enforcement readiness guarantee.
    It is not scheduler active.
    It is not policy decision.
    It is not approval.
    It is not runtime safety proof.
    """

    delegation_ref_id: str
    has_expiry_refs: bool = False
    has_revocation_refs: bool = False
    has_suspension_refs: bool = False
    has_renewal_refs: bool = False
    has_supersession_refs: bool = False
    has_reason_refs: bool = False
    has_scope_context: bool = False
    has_authority_context: bool = False
    has_evidence_context: bool = False
    has_identity_mesh_context: bool = False
    missing_components: tuple[str, ...] = ()
    enforcement_unavailable_reason: str = (
        "Enforcement is scheduled for later P1.8 tasks; not P1.8.8"
    )
    scheduler_unavailable_reason: str = (
        "Scheduler/timer activation is not available in P1.8.8; "
        "expiry refs are reference-only"
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_LIFECYCLE_READINESS_PROFILE_VERSION
    lifecycle_readiness_profile_id: str = ""
    readiness_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        enforcement_unavailable_reason = _required_string(
            self.enforcement_unavailable_reason, field_name="enforcement_unavailable_reason"
        )
        scheduler_unavailable_reason = _required_string(
            self.scheduler_unavailable_reason, field_name="scheduler_unavailable_reason"
        )
        missing_components = tuple(
            sorted(self.missing_components)
            if isinstance(self.missing_components, (tuple, list))
            else ()
        )

        readiness_hash = compute_lifecycle_readiness_hash(
            delegation_ref_id=delegation_ref_id,
            has_expiry_refs=bool(self.has_expiry_refs),
            has_revocation_refs=bool(self.has_revocation_refs),
            has_suspension_refs=bool(self.has_suspension_refs),
            has_renewal_refs=bool(self.has_renewal_refs),
            has_supersession_refs=bool(self.has_supersession_refs),
            has_reason_refs=bool(self.has_reason_refs),
            has_scope_context=bool(self.has_scope_context),
            has_authority_context=bool(self.has_authority_context),
            has_evidence_context=bool(self.has_evidence_context),
            has_identity_mesh_context=bool(self.has_identity_mesh_context),
            missing_components=missing_components,
            enforcement_unavailable_reason=enforcement_unavailable_reason,
            scheduler_unavailable_reason=scheduler_unavailable_reason,
            source_label=source_label,
            schema_version=schema_version,
        )
        lifecycle_readiness_profile_id = f"lifecycle_rd:{readiness_hash[:16]}"

        if self.readiness_hash not in ("", readiness_hash):
            raise DelegationValidationError(
                "readiness_hash does not match readiness content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="readiness_hash",
            )
        if self.lifecycle_readiness_profile_id not in ("", lifecycle_readiness_profile_id):
            raise DelegationValidationError(
                "lifecycle_readiness_profile_id does not match content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lifecycle_readiness_profile_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(
            self, "enforcement_unavailable_reason", enforcement_unavailable_reason
        )
        object.__setattr__(self, "scheduler_unavailable_reason", scheduler_unavailable_reason)
        object.__setattr__(self, "missing_components", missing_components)
        object.__setattr__(self, "readiness_hash", readiness_hash)
        object.__setattr__(
            self, "lifecycle_readiness_profile_id", lifecycle_readiness_profile_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "enforcement_unavailable_reason": self.enforcement_unavailable_reason,
            "has_authority_context": self.has_authority_context,
            "has_evidence_context": self.has_evidence_context,
            "has_expiry_refs": self.has_expiry_refs,
            "has_identity_mesh_context": self.has_identity_mesh_context,
            "has_reason_refs": self.has_reason_refs,
            "has_renewal_refs": self.has_renewal_refs,
            "has_revocation_refs": self.has_revocation_refs,
            "has_scope_context": self.has_scope_context,
            "has_supersession_refs": self.has_supersession_refs,
            "has_suspension_refs": self.has_suspension_refs,
            "lifecycle_readiness_profile_id": self.lifecycle_readiness_profile_id,
            "missing_components": list(self.missing_components),
            "readiness_hash": self.readiness_hash,
            "schema_version": self.schema_version,
            "scheduler_unavailable_reason": self.scheduler_unavailable_reason,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLifecycleReadinessProfile:
        validate_known_fields(
            data,
            LIFECYCLE_READINESS_PROFILE_KNOWN_FIELDS,
            label="delegation_lifecycle_readiness_profile",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            has_expiry_refs=data.get("has_expiry_refs", False),
            has_revocation_refs=data.get("has_revocation_refs", False),
            has_suspension_refs=data.get("has_suspension_refs", False),
            has_renewal_refs=data.get("has_renewal_refs", False),
            has_supersession_refs=data.get("has_supersession_refs", False),
            has_reason_refs=data.get("has_reason_refs", False),
            has_scope_context=data.get("has_scope_context", False),
            has_authority_context=data.get("has_authority_context", False),
            has_evidence_context=data.get("has_evidence_context", False),
            has_identity_mesh_context=data.get("has_identity_mesh_context", False),
            missing_components=tuple(data.get("missing_components", ())),
            enforcement_unavailable_reason=data.get(
                "enforcement_unavailable_reason",
                "Enforcement is scheduled for later P1.8 tasks; not P1.8.8",
            ),
            scheduler_unavailable_reason=data.get(
                "scheduler_unavailable_reason",
                "Scheduler/timer activation is not available in P1.8.8; "
                "expiry refs are reference-only",
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_LIFECYCLE_READINESS_PROFILE_VERSION
            ),
            lifecycle_readiness_profile_id=data.get(
                "lifecycle_readiness_profile_id", ""
            ),
            readiness_hash=data.get("readiness_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationLifecycleEnvelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLifecycleEnvelope:
    """Deterministic packet of lifecycle refs and context hashes.

    DelegationLifecycleEnvelope is a reference packet.
    It is not lifecycle enforcement.
    It is not runtime expiry.
    It is not runtime revocation.
    It is not scheduler activation.
    It is not TRACE_VERIFIED.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_binding_set_hash: str
    lifecycle_readiness_hash: str
    expiry_refs: tuple[str, ...] = ()
    revocation_refs: tuple[str, ...] = ()
    suspension_refs: tuple[str, ...] = ()
    renewal_refs: tuple[str, ...] = ()
    supersession_refs: tuple[str, ...] = ()
    reason_refs: tuple[str, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_LIFECYCLE_ENVELOPE_VERSION
    lifecycle_envelope_id: str = ""
    lifecycle_envelope_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash, field_name="delegation_identity_hash"
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash, field_name="authority_binding_set_hash"
        )
        non_repudiation_binding_set_hash = _required_string(
            self.non_repudiation_binding_set_hash,
            field_name="non_repudiation_binding_set_hash",
        )
        identity_mesh_binding_set_hash = _required_string(
            self.identity_mesh_binding_set_hash,
            field_name="identity_mesh_binding_set_hash",
        )
        scope_binding_set_hash = _required_string(
            self.scope_binding_set_hash, field_name="scope_binding_set_hash"
        )
        lifecycle_readiness_hash = _required_string(
            self.lifecycle_readiness_hash, field_name="lifecycle_readiness_hash"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        expiry_refs = tuple(sorted(self.expiry_refs))
        revocation_refs = tuple(sorted(self.revocation_refs))
        suspension_refs = tuple(sorted(self.suspension_refs))
        renewal_refs = tuple(sorted(self.renewal_refs))
        supersession_refs = tuple(sorted(self.supersession_refs))
        reason_refs = tuple(sorted(self.reason_refs))

        lifecycle_envelope_hash = compute_lifecycle_envelope_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
            scope_binding_set_hash=scope_binding_set_hash,
            expiry_refs=expiry_refs,
            revocation_refs=revocation_refs,
            suspension_refs=suspension_refs,
            renewal_refs=renewal_refs,
            supersession_refs=supersession_refs,
            reason_refs=reason_refs,
            lifecycle_readiness_hash=lifecycle_readiness_hash,
            source_label=source_label,
            schema_version=schema_version,
        )
        lifecycle_envelope_id = f"lifecycle_env:{lifecycle_envelope_hash[:16]}"

        if self.lifecycle_envelope_hash not in ("", lifecycle_envelope_hash):
            raise DelegationValidationError(
                "lifecycle_envelope_hash does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lifecycle_envelope_hash",
            )
        if self.lifecycle_envelope_id not in ("", lifecycle_envelope_id):
            raise DelegationValidationError(
                "lifecycle_envelope_id does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lifecycle_envelope_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "delegation_identity_hash", delegation_identity_hash
        )
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(
            self, "authority_binding_set_hash", authority_binding_set_hash
        )
        object.__setattr__(
            self, "non_repudiation_binding_set_hash", non_repudiation_binding_set_hash
        )
        object.__setattr__(
            self, "identity_mesh_binding_set_hash", identity_mesh_binding_set_hash
        )
        object.__setattr__(
            self, "scope_binding_set_hash", scope_binding_set_hash
        )
        object.__setattr__(
            self, "lifecycle_readiness_hash", lifecycle_readiness_hash
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "expiry_refs", expiry_refs)
        object.__setattr__(self, "revocation_refs", revocation_refs)
        object.__setattr__(self, "suspension_refs", suspension_refs)
        object.__setattr__(self, "renewal_refs", renewal_refs)
        object.__setattr__(self, "supersession_refs", supersession_refs)
        object.__setattr__(self, "reason_refs", reason_refs)
        object.__setattr__(self, "lifecycle_envelope_hash", lifecycle_envelope_hash)
        object.__setattr__(self, "lifecycle_envelope_id", lifecycle_envelope_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "expiry_refs": sorted(self.expiry_refs),
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "lifecycle_envelope_hash": self.lifecycle_envelope_hash,
            "lifecycle_envelope_id": self.lifecycle_envelope_id,
            "lifecycle_readiness_hash": self.lifecycle_readiness_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "reason_refs": sorted(self.reason_refs),
            "renewal_refs": sorted(self.renewal_refs),
            "revocation_refs": sorted(self.revocation_refs),
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "source_label": self.source_label.value,
            "supersession_refs": sorted(self.supersession_refs),
            "suspension_refs": sorted(self.suspension_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLifecycleEnvelope:
        validate_known_fields(
            data, LIFECYCLE_ENVELOPE_KNOWN_FIELDS, label="delegation_lifecycle_envelope"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data["non_repudiation_binding_set_hash"],
            identity_mesh_binding_set_hash=data["identity_mesh_binding_set_hash"],
            scope_binding_set_hash=data["scope_binding_set_hash"],
            lifecycle_readiness_hash=data["lifecycle_readiness_hash"],
            expiry_refs=tuple(data.get("expiry_refs", ())),
            revocation_refs=tuple(data.get("revocation_refs", ())),
            suspension_refs=tuple(data.get("suspension_refs", ())),
            renewal_refs=tuple(data.get("renewal_refs", ())),
            supersession_refs=tuple(data.get("supersession_refs", ())),
            reason_refs=tuple(data.get("reason_refs", ())),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_LIFECYCLE_ENVELOPE_VERSION
            ),
            lifecycle_envelope_id=data.get("lifecycle_envelope_id", ""),
            lifecycle_envelope_hash=data.get("lifecycle_envelope_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationLifecycleBinding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLifecycleBinding:
    """Binding between lifecycle envelope and delegation context.

    DelegationLifecycleBinding binds lifecycle metadata.
    It is not runtime lifecycle state.
    It is not enforcement.
    It is not scheduler state.
    It is not policy decision.
    It is not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_binding_set_hash: str
    lifecycle_envelope_hash: str
    lifecycle_readiness_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_LIFECYCLE_BINDING_VERSION
    binding_id: str = ""
    binding_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash, field_name="delegation_identity_hash"
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash, field_name="authority_binding_set_hash"
        )
        non_repudiation_binding_set_hash = _required_string(
            self.non_repudiation_binding_set_hash,
            field_name="non_repudiation_binding_set_hash",
        )
        identity_mesh_binding_set_hash = _required_string(
            self.identity_mesh_binding_set_hash,
            field_name="identity_mesh_binding_set_hash",
        )
        scope_binding_set_hash = _required_string(
            self.scope_binding_set_hash, field_name="scope_binding_set_hash"
        )
        lifecycle_envelope_hash = _required_string(
            self.lifecycle_envelope_hash, field_name="lifecycle_envelope_hash"
        )
        lifecycle_readiness_hash = _required_string(
            self.lifecycle_readiness_hash, field_name="lifecycle_readiness_hash"
        )
        source_label = _parse_source_label(self.source_label)
        lifecycle_status = _parse_lifecycle_status(self.lifecycle_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        binding_hash = compute_lifecycle_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
            scope_binding_set_hash=scope_binding_set_hash,
            lifecycle_envelope_hash=lifecycle_envelope_hash,
            lifecycle_readiness_hash=lifecycle_readiness_hash,
            source_label=source_label,
            lifecycle_status=lifecycle_status,
            schema_version=schema_version,
        )
        binding_id = f"lifecycle_binding:{binding_hash[:16]}"

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
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "authority_binding_set_hash", authority_binding_set_hash)
        object.__setattr__(
            self, "non_repudiation_binding_set_hash", non_repudiation_binding_set_hash
        )
        object.__setattr__(
            self, "identity_mesh_binding_set_hash", identity_mesh_binding_set_hash
        )
        object.__setattr__(self, "scope_binding_set_hash", scope_binding_set_hash)
        object.__setattr__(self, "lifecycle_envelope_hash", lifecycle_envelope_hash)
        object.__setattr__(self, "lifecycle_readiness_hash", lifecycle_readiness_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "lifecycle_envelope_hash": self.lifecycle_envelope_hash,
            "lifecycle_readiness_hash": self.lifecycle_readiness_hash,
            "lifecycle_status": self.lifecycle_status.value,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLifecycleBinding:
        validate_known_fields(
            data, LIFECYCLE_BINDING_KNOWN_FIELDS, label="delegation_lifecycle_binding"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data["non_repudiation_binding_set_hash"],
            identity_mesh_binding_set_hash=data["identity_mesh_binding_set_hash"],
            scope_binding_set_hash=data["scope_binding_set_hash"],
            lifecycle_envelope_hash=data["lifecycle_envelope_hash"],
            lifecycle_readiness_hash=data["lifecycle_readiness_hash"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            lifecycle_status=data.get(
                "lifecycle_status",
                DelegationLifecycleStatus.REFERENCE_ONLY,
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_LIFECYCLE_BINDING_VERSION
            ),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationLifecycleBindingSet
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLifecycleBindingSet:
    """Collection of lifecycle bindings for one delegation.

    DelegationLifecycleBindingSet describes lifecycle hooks.
    It does not expire or revoke delegations.
    It does not remove permissions.
    It does not activate scheduler.
    It does not write Ledger/global trace.
    It does not mutate runtime.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_binding_set_hash: str
    bindings: tuple[DelegationLifecycleBinding, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    side_effects: "DelegationLifecycleSideEffects | None" = None
    schema_version: str = DELEGATION_LIFECYCLE_BINDING_SET_VERSION
    lifecycle_binding_set_id: str = ""
    lifecycle_binding_set_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash, field_name="delegation_identity_hash"
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash, field_name="authority_binding_set_hash"
        )
        non_repudiation_binding_set_hash = _required_string(
            self.non_repudiation_binding_set_hash,
            field_name="non_repudiation_binding_set_hash",
        )
        identity_mesh_binding_set_hash = _required_string(
            self.identity_mesh_binding_set_hash,
            field_name="identity_mesh_binding_set_hash",
        )
        scope_binding_set_hash = _required_string(
            self.scope_binding_set_hash, field_name="scope_binding_set_hash"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        bindings = tuple(
            b if isinstance(b, DelegationLifecycleBinding)
            else DelegationLifecycleBinding.from_dict(b)
            for b in self.bindings
        )

        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationLifecycleSideEffects)
            else (
                DelegationLifecycleSideEffects.from_dict(self.side_effects)
                if self.side_effects is not None
                else DelegationLifecycleSideEffects()
            )
        )

        binding_hashes: tuple[str, ...] = tuple(
            sorted(b.binding_hash for b in bindings)
        )

        lifecycle_binding_set_hash = compute_lifecycle_binding_set_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
            scope_binding_set_hash=scope_binding_set_hash,
            binding_hashes=binding_hashes,
            source_label=source_label,
            schema_version=schema_version,
        )
        lifecycle_binding_set_id = f"lifecycle_bs:{lifecycle_binding_set_hash[:16]}"

        if self.lifecycle_binding_set_hash not in ("", lifecycle_binding_set_hash):
            raise DelegationValidationError(
                "lifecycle_binding_set_hash does not match content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lifecycle_binding_set_hash",
            )
        if self.lifecycle_binding_set_id not in ("", lifecycle_binding_set_id):
            raise DelegationValidationError(
                "lifecycle_binding_set_id does not match content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="lifecycle_binding_set_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "authority_binding_set_hash", authority_binding_set_hash)
        object.__setattr__(
            self, "non_repudiation_binding_set_hash", non_repudiation_binding_set_hash
        )
        object.__setattr__(
            self, "identity_mesh_binding_set_hash", identity_mesh_binding_set_hash
        )
        object.__setattr__(self, "scope_binding_set_hash", scope_binding_set_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(
            self, "lifecycle_binding_set_hash", lifecycle_binding_set_hash
        )
        object.__setattr__(
            self, "lifecycle_binding_set_id", lifecycle_binding_set_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "bindings": [
                b.to_canonical_dict()
                for b in sorted(self.bindings, key=lambda x: x.binding_id)
            ],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "lifecycle_binding_set_hash": self.lifecycle_binding_set_hash,
            "lifecycle_binding_set_id": self.lifecycle_binding_set_id,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLifecycleBindingSet:
        validate_known_fields(
            data,
            LIFECYCLE_BINDING_SET_KNOWN_FIELDS,
            label="delegation_lifecycle_binding_set",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data["non_repudiation_binding_set_hash"],
            identity_mesh_binding_set_hash=data["identity_mesh_binding_set_hash"],
            scope_binding_set_hash=data["scope_binding_set_hash"],
            bindings=tuple(data.get("bindings", ())),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            side_effects=data.get("side_effects", None),
            schema_version=data.get(
                "schema_version", DELEGATION_LIFECYCLE_BINDING_SET_VERSION
            ),
            lifecycle_binding_set_id=data.get("lifecycle_binding_set_id", ""),
            lifecycle_binding_set_hash=data.get("lifecycle_binding_set_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationLifecycleSideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLifecycleSideEffects:
    """Hard proof that P1.8.8 is non-enforcing, non-scheduling, non-revoking,
    and non-mutating. All fields default to false."""

    runtime_expired: bool = False
    runtime_revoked: bool = False
    runtime_suspended: bool = False
    authority_renewed: bool = False
    delegation_superseded: bool = False
    permission_removed: bool = False
    scheduler_activated: bool = False
    runtime_cancelled: bool = False
    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "approval_created": self.approval_created,
            "authority_renewed": self.authority_renewed,
            "custos_called": self.custos_called,
            "delegation_superseded": self.delegation_superseded,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "permission_removed": self.permission_removed,
            "policy_called": self.policy_called,
            "runtime_cancelled": self.runtime_cancelled,
            "runtime_expired": self.runtime_expired,
            "runtime_mutated": self.runtime_mutated,
            "runtime_revoked": self.runtime_revoked,
            "runtime_suspended": self.runtime_suspended,
            "scheduler_activated": self.scheduler_activated,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLifecycleSideEffects:
        validate_known_fields(
            data,
            LIFECYCLE_SIDE_EFFECTS_KNOWN_FIELDS,
            label="delegation_lifecycle_side_effects",
        )
        return cls(
            runtime_expired=data.get("runtime_expired", False),
            runtime_revoked=data.get("runtime_revoked", False),
            runtime_suspended=data.get("runtime_suspended", False),
            authority_renewed=data.get("authority_renewed", False),
            delegation_superseded=data.get("delegation_superseded", False),
            permission_removed=data.get("permission_removed", False),
            scheduler_activated=data.get("scheduler_activated", False),
            runtime_cancelled=data.get("runtime_cancelled", False),
            policy_called=data.get("policy_called", False),
            custos_called=data.get("custos_called", False),
            approval_created=data.get("approval_created", False),
            ledger_written=data.get("ledger_written", False),
            global_trace_written=data.get("global_trace_written", False),
            runtime_mutated=data.get("runtime_mutated", False),
        )

    @classmethod
    def all_false(cls) -> DelegationLifecycleSideEffects:
        """Factory for the canonical all-false side-effects object."""
        return cls()


# ---------------------------------------------------------------------------
# DelegationLifecycleStatusReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationLifecycleStatusReport:
    """Honest P1.8.8 lifecycle model readiness and unavailable surfaces report.

    Reports lifecycle model readiness and unavailable surfaces.
    Does not claim runtime expiry, revocation, scheduling, or enforcement.
    """

    status_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    available_contracts: Mapping[str, str] | None = None
    unavailable_bindings: Mapping[str, str] | None = None
    side_effects: DelegationLifecycleSideEffects | None = None
    schema_version: str = DELEGATION_LIFECYCLE_STATUS_REPORT_VERSION
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
            if isinstance(self.side_effects, DelegationLifecycleSideEffects)
            else DelegationLifecycleSideEffects.from_dict(self.side_effects)
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_lifecycle_status_report_hash(
            status_label=status_label,
            available_contracts=available_contracts,
            unavailable_bindings=unavailable_bindings,
            side_effects=side_effects,
        )

        if self.status_hash not in ("", status_hash):
            raise DelegationValidationError(
                "status_hash does not match status content",
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
            "available_contracts": dict(
                sorted(self.available_contracts.items(), key=lambda item: item[0])
            ),
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "status_hash": self.status_hash,
            "status_label": self.status_label.value,
            "unavailable_bindings": dict(
                sorted(self.unavailable_bindings.items(), key=lambda item: item[0])
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationLifecycleStatusReport:
        validate_known_fields(
            data,
            LIFECYCLE_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_lifecycle_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get("side_effects", DelegationLifecycleSideEffects()),
            schema_version=data.get(
                "schema_version", DELEGATION_LIFECYCLE_STATUS_REPORT_VERSION
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_expiry_ref(
    expiry_ref: str,
    delegation_ref_id: str,
    *,
    expiry_description: str = "",
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.EXPIRY_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED,
) -> DelegationExpiryRef:
    """Build reference-only expiry ref without expiring runtime delegation."""
    return DelegationExpiryRef(
        expiry_ref=expiry_ref,
        delegation_ref_id=delegation_ref_id,
        expiry_description=expiry_description,
        reference_status=reference_status,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_revocation_ref(
    revocation_ref: str,
    delegation_ref_id: str,
    *,
    revocation_description: str = "",
    reason_ref_id: str | None = None,
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.REVOCATION_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED,
) -> DelegationRevocationRef:
    """Build reference-only revocation ref without revoking runtime delegation."""
    return DelegationRevocationRef(
        revocation_ref=revocation_ref,
        delegation_ref_id=delegation_ref_id,
        revocation_description=revocation_description,
        reason_ref_id=reason_ref_id,
        reference_status=reference_status,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_suspension_ref(
    suspension_ref: str,
    delegation_ref_id: str,
    *,
    suspension_description: str = "",
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.SUSPENSION_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED,
) -> DelegationSuspensionRef:
    """Build reference-only suspension ref without pausing runtime."""
    return DelegationSuspensionRef(
        suspension_ref=suspension_ref,
        delegation_ref_id=delegation_ref_id,
        suspension_description=suspension_description,
        reference_status=reference_status,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_renewal_ref(
    renewal_ref: str,
    delegation_ref_id: str,
    *,
    renewal_description: str = "",
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.RENEWAL_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED,
) -> DelegationRenewalRef:
    """Build reference-only renewal ref without renewing authority."""
    return DelegationRenewalRef(
        renewal_ref=renewal_ref,
        delegation_ref_id=delegation_ref_id,
        renewal_description=renewal_description,
        reference_status=reference_status,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_supersession_ref(
    supersession_ref: str,
    delegation_ref_id: str,
    *,
    superseded_by_ref: str | None = None,
    supersession_description: str = "",
    reference_status: DelegationLifecycleReferenceStatus = (
        DelegationLifecycleReferenceStatus.SUPERSESSION_REFERENCED
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED,
) -> DelegationSupersessionRef:
    """Build reference-only supersession ref without invalidating old delegation."""
    return DelegationSupersessionRef(
        supersession_ref=supersession_ref,
        delegation_ref_id=delegation_ref_id,
        superseded_by_ref=superseded_by_ref,
        supersession_description=supersession_description,
        reference_status=reference_status,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_revocation_reason_ref(
    reason_ref: str,
    delegation_ref_id: str,
    *,
    reason_kind: DelegationRevocationReasonKind | str = (
        DelegationRevocationReasonKind.OPERATOR_DECLARED
    ),
    reason_description: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = DelegationLifecycleStatus.DECLARED,
) -> DelegationRevocationReasonRef:
    """Build reference-only reason ref without verifying reason or enforcing
    revocation."""
    return DelegationRevocationReasonRef(
        reason_ref=reason_ref,
        delegation_ref_id=delegation_ref_id,
        reason_kind=reason_kind,
        reason_description=reason_description,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_lifecycle_readiness_profile(
    delegation_ref_id: str,
    *,
    has_expiry_refs: bool = False,
    has_revocation_refs: bool = False,
    has_suspension_refs: bool = False,
    has_renewal_refs: bool = False,
    has_supersession_refs: bool = False,
    has_reason_refs: bool = False,
    has_scope_context: bool = False,
    has_authority_context: bool = False,
    has_evidence_context: bool = False,
    has_identity_mesh_context: bool = False,
    missing_components: Sequence[str] | None = None,
    enforcement_unavailable_reason: str = (
        "Enforcement is scheduled for later P1.8 tasks; not P1.8.8"
    ),
    scheduler_unavailable_reason: str = (
        "Scheduler/timer activation is not available in P1.8.8; "
        "expiry refs are reference-only"
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationLifecycleReadinessProfile:
    """Build presence/absence readiness profile without enforcement guarantee or
    scheduler activation."""
    return DelegationLifecycleReadinessProfile(
        delegation_ref_id=delegation_ref_id,
        has_expiry_refs=has_expiry_refs,
        has_revocation_refs=has_revocation_refs,
        has_suspension_refs=has_suspension_refs,
        has_renewal_refs=has_renewal_refs,
        has_supersession_refs=has_supersession_refs,
        has_reason_refs=has_reason_refs,
        has_scope_context=has_scope_context,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        has_identity_mesh_context=has_identity_mesh_context,
        missing_components=(
            tuple(missing_components) if missing_components is not None else ()
        ),
        enforcement_unavailable_reason=enforcement_unavailable_reason,
        scheduler_unavailable_reason=scheduler_unavailable_reason,
        source_label=source_label,
    )


def build_delegation_lifecycle_envelope(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_readiness_hash: str,
    *,
    expiry_refs: Sequence[str] | None = None,
    revocation_refs: Sequence[str] | None = None,
    suspension_refs: Sequence[str] | None = None,
    renewal_refs: Sequence[str] | None = None,
    supersession_refs: Sequence[str] | None = None,
    reason_refs: Sequence[str] | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationLifecycleEnvelope:
    """Build lifecycle envelope reference packet without enforcement, expiry,
    revocation, or scheduler activation."""
    return DelegationLifecycleEnvelope(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_readiness_hash=lifecycle_readiness_hash,
        expiry_refs=tuple(expiry_refs) if expiry_refs is not None else (),
        revocation_refs=tuple(revocation_refs) if revocation_refs is not None else (),
        suspension_refs=tuple(suspension_refs) if suspension_refs is not None else (),
        renewal_refs=tuple(renewal_refs) if renewal_refs is not None else (),
        supersession_refs=tuple(supersession_refs) if supersession_refs is not None else (),
        reason_refs=tuple(reason_refs) if reason_refs is not None else (),
        source_label=source_label,
    )


def build_delegation_lifecycle_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_envelope_hash: str,
    lifecycle_readiness_hash: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    lifecycle_status: DelegationLifecycleStatus = (
        DelegationLifecycleStatus.REFERENCE_ONLY
    ),
) -> DelegationLifecycleBinding:
    """Build lifecycle binding without enforcement, scheduler state, policy
    decision, or trace verification."""
    return DelegationLifecycleBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_envelope_hash=lifecycle_envelope_hash,
        lifecycle_readiness_hash=lifecycle_readiness_hash,
        source_label=source_label,
        lifecycle_status=lifecycle_status,
    )


def build_delegation_lifecycle_binding_set(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    *,
    bindings: Sequence[DelegationLifecycleBinding | Mapping[str, Any]] | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    side_effects: DelegationLifecycleSideEffects | None = None,
) -> DelegationLifecycleBindingSet:
    """Build lifecycle binding set without expiring, revoking, removing
    permissions, activating scheduler, or writing Ledger/global trace."""
    return DelegationLifecycleBindingSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        bindings=tuple(bindings) if bindings is not None else (),
        source_label=source_label,
        side_effects=side_effects or DelegationLifecycleSideEffects(),
    )


def _default_lifecycle_available_contracts() -> dict[str, str]:
    return {
        "DelegationExpiryRef": DelegationSourceLabel.LIVE.value,
        "DelegationRevocationRef": DelegationSourceLabel.LIVE.value,
        "DelegationSuspensionRef": DelegationSourceLabel.LIVE.value,
        "DelegationRenewalRef": DelegationSourceLabel.LIVE.value,
        "DelegationSupersessionRef": DelegationSourceLabel.LIVE.value,
        "DelegationRevocationReasonRef": DelegationSourceLabel.LIVE.value,
        "DelegationLifecycleReadinessProfile": DelegationSourceLabel.LIVE.value,
        "DelegationLifecycleEnvelope": DelegationSourceLabel.LIVE.value,
        "DelegationLifecycleBinding": DelegationSourceLabel.LIVE.value,
        "DelegationLifecycleBindingSet": DelegationSourceLabel.LIVE.value,
        "DelegationLifecycleSideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationLifecycleStatusReport": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_lifecycle_status_report() -> DelegationLifecycleStatusReport:
    """Return honest P1.8.8 lifecycle status report (non-enforcing)."""
    return DelegationLifecycleStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_lifecycle_available_contracts(),
        unavailable_bindings=DELEGATION_LIFECYCLE_UNAVAILABLE_BINDINGS,
        side_effects=DelegationLifecycleSideEffects(),
    )


def serialize_delegation_lifecycle_envelope(
    envelope: DelegationLifecycleEnvelope,
) -> str:
    """Serialize DelegationLifecycleEnvelope to deterministic canonical JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_lifecycle_binding_set(
    binding_set: DelegationLifecycleBindingSet,
) -> str:
    """Serialize DelegationLifecycleBindingSet to deterministic canonical JSON."""
    return to_canonical_json(binding_set)


def hash_delegation_expiry_ref(ref: DelegationExpiryRef) -> str:
    """Return stable expiry_hash for DelegationExpiryRef content."""
    return ref.expiry_hash


def hash_delegation_revocation_ref(ref: DelegationRevocationRef) -> str:
    """Return stable revocation_hash for DelegationRevocationRef content."""
    return ref.revocation_hash


def hash_delegation_suspension_ref(ref: DelegationSuspensionRef) -> str:
    """Return stable suspension_hash for DelegationSuspensionRef content."""
    return ref.suspension_hash


def hash_delegation_renewal_ref(ref: DelegationRenewalRef) -> str:
    """Return stable renewal_hash for DelegationRenewalRef content."""
    return ref.renewal_hash


def hash_delegation_supersession_ref(ref: DelegationSupersessionRef) -> str:
    """Return stable supersession_hash for DelegationSupersessionRef content."""
    return ref.supersession_hash


def hash_delegation_revocation_reason_ref(ref: DelegationRevocationReasonRef) -> str:
    """Return stable reason_hash for DelegationRevocationReasonRef content."""
    return ref.reason_hash


def hash_delegation_lifecycle_readiness_profile(
    profile: DelegationLifecycleReadinessProfile,
) -> str:
    """Return stable readiness_hash for DelegationLifecycleReadinessProfile content."""
    return profile.readiness_hash


def hash_delegation_lifecycle_envelope(
    envelope: DelegationLifecycleEnvelope,
) -> str:
    """Return stable lifecycle_envelope_hash for DelegationLifecycleEnvelope content."""
    return envelope.lifecycle_envelope_hash


def hash_delegation_lifecycle_binding_set(
    binding_set: DelegationLifecycleBindingSet,
) -> str:
    """Return stable lifecycle_binding_set_hash for DelegationLifecycleBindingSet
    content."""
    return binding_set.lifecycle_binding_set_hash
