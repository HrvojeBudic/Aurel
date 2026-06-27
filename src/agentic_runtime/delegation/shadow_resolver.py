"""Delegation shadow resolver / consistency model (P1.8.10).

Deterministic, versioned, JSON-safe, side-effect-free, shadow-only
diagnostic consistency layer over P1.8.0-P1.8.9 reference context hashes.
Produces diagnostic findings, a cross-family consistency matrix, a
readiness profile, a consistency snapshot, and a shadow resolver result
without policy decisioning, Custos calls, approval creation, authority
grant/deny, runtime allow/block, enforcement, delegation execution,
trace write, Ledger write, or runtime mutation.

Architectural law:
  - ShadowResolverResult exists does not mean policy decision.
  - ConsistencySnapshot exists does not mean delegation verified.
  - ConsistencyMatrix exists does not mean approval matrix.
  - ConsistencyFinding exists does not mean enforcement action.
  - CONFLICT_REFERENCED exists does not mean runtime denial.
  - PRESENT exists does not mean verified.
  - MISSING exists does not mean failed.
  - ReadinessProfile exists does not mean approval readiness.
  - Resolver hash exists does not mean TRACE_VERIFIED.
  - Shadow pass does not mean allowed.
  - Shadow fail does not mean blocked.
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

DELEGATION_SHADOW_RESOLVER_TASK_ID = "P1.8.10"
DELEGATION_SHADOW_RESOLVER_INPUT_ENVELOPE_VERSION = "delegation_shadow_resolver_input_envelope.v1"
DELEGATION_CONSISTENCY_FINDING_VERSION = "delegation_consistency_finding.v1"
DELEGATION_CONSISTENCY_MATRIX_ENTRY_VERSION = "delegation_consistency_matrix_entry.v1"
DELEGATION_CONSISTENCY_MATRIX_VERSION = "delegation_consistency_matrix.v1"
DELEGATION_SHADOW_RESOLVER_READINESS_PROFILE_VERSION = "delegation_shadow_resolver_readiness_profile.v1"
DELEGATION_CONSISTENCY_SNAPSHOT_VERSION = "delegation_consistency_snapshot.v1"
DELEGATION_SHADOW_RESOLVER_RESULT_VERSION = "delegation_shadow_resolver_result.v1"
DELEGATION_SHADOW_RESOLVER_SIDE_EFFECTS_VERSION = "delegation_shadow_resolver_side_effects.v1"
DELEGATION_SHADOW_RESOLVER_STATUS_REPORT_VERSION = "delegation_shadow_resolver_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_SHADOW_RESOLVER_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.10; "
        "diagnostic schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.10"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.10 shadow resolver layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.10 "
        "shadow resolver layer"
    ),
    "Policy Decision Engine": (
        "Policy decision engine is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    ),
    "Custos Resolver": (
        "Custos resolver is not available in P1.8.10; "
        "shadow resolver does not call Custos"
    ),
    "Approval System": (
        "Approval system is not available in P1.8.10; "
        "shadow resolver does not create approvals"
    ),
    "Authority Grant/Deny": (
        "Authority grant/deny is not available in P1.8.10; "
        "shadow resolver does not grant or deny authority"
    ),
    "Runtime Allow/Block": (
        "Runtime allow/block is not available in P1.8.10; "
        "shadow resolver does not allow or block runtime"
    ),
    "Enforcement Engine": (
        "Enforcement engine is not available in P1.8.10; "
        "shadow resolver does not enforce"
    ),
    "Delegation Executor": (
        "Delegation executor is not available in P1.8.10; "
        "shadow resolver does not execute delegations"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.10; "
        "shadow resolver does not write trace"
    ),
    "P1.8.11 Operator Approval Intent Model": (
        "P1.8.11 operator approval intent model is not available in P1.8.10"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 provenance/disclosure layer is not "
        "available in P1.8.10"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.10"
    ),
    "Chain Verifier": (
        "Chain verifier is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    ),
    "Evidence Verifier": (
        "Evidence verifier is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    ),
    "Identity Resolver": (
        "Identity resolver is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    ),
    "Scope Enforcer": (
        "Scope enforcer is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    ),
    "Lifecycle Enforcer": (
        "Lifecycle enforcer is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world validation frozensets)
# ---------------------------------------------------------------------------

INPUT_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "shadow_resolver_input_envelope_id",
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
    "source_label",
    "input_envelope_hash",
})

FINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "finding_id",
    "delegation_ref_id",
    "family",
    "finding_kind",
    "severity",
    "finding_ref",
    "finding_detail",
    "unavailable_reason",
    "source_label",
    "finding_hash",
})

MATRIX_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "entry_id",
    "delegation_ref_id",
    "family",
    "present",
    "hash_present",
    "delegation_ref_aligned",
    "source_label_present",
    "finding_count",
    "unavailable_reason",
    "source_label",
    "entry_hash",
})

CONSISTENCY_MATRIX_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "consistency_matrix_id",
    "delegation_ref_id",
    "entry_ids",
    "entry_hashes",
    "source_label",
    "matrix_hash",
})

READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "readiness_profile_id",
    "delegation_ref_id",
    "has_foundation",
    "has_identity",
    "has_roles",
    "has_constraints",
    "has_authority",
    "has_non_repudiation",
    "has_identity_mesh",
    "has_scope",
    "has_lifecycle",
    "has_chain",
    "missing_families",
    "policy_unavailable_reason",
    "custos_unavailable_reason",
    "approval_unavailable_reason",
    "runtime_unavailable_reason",
    "source_label",
    "readiness_hash",
})

SNAPSHOT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "consistency_snapshot_id",
    "delegation_ref_id",
    "input_envelope_hash",
    "finding_hashes",
    "matrix_hash",
    "readiness_hash",
    "source_label",
    "snapshot_hash",
})

SHADOW_RESULT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "shadow_resolver_result_id",
    "delegation_ref_id",
    "resolver_mode",
    "resolver_status",
    "input_envelope_hash",
    "snapshot_hash",
    "matrix_hash",
    "readiness_hash",
    "finding_count",
    "unavailable_bindings",
    "source_label",
    "result_hash",
    "side_effects",
})

SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_decision_made",
    "custos_called",
    "approval_created",
    "authority_granted",
    "authority_denied",
    "runtime_allowed",
    "runtime_blocked",
    "enforcement_performed",
    "delegation_executed",
    "trace_written",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationShadowResolverMode(str, Enum):
    """Diagnostic mode classifier; does not make policy decisions."""

    SHADOW_ONLY = "SHADOW_ONLY"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class DelegationConsistencyFamily(str, Enum):
    """P1.8 reference family classifier; does not verify correctness."""

    FOUNDATION = "FOUNDATION"
    IDENTITY = "IDENTITY"
    ROLES = "ROLES"
    CONSTRAINTS = "CONSTRAINTS"
    AUTHORITY = "AUTHORITY"
    NON_REPUDIATION = "NON_REPUDIATION"
    IDENTITY_MESH = "IDENTITY_MESH"
    SCOPE = "SCOPE"
    LIFECYCLE = "LIFECYCLE"
    CHAIN = "CHAIN"
    UNKNOWN = "UNKNOWN"


class DelegationConsistencyFindingKind(str, Enum):
    """Diagnostic finding kind; does not impose allow/deny/verify/fail semantics.

    Boundary:
      - PRESENT is not verified.
      - MISSING is not failed.
      - MISMATCH is not denied.
      - CONFLICT_REFERENCED is not runtime denial.
    """

    PRESENT = "PRESENT"
    MISSING = "MISSING"
    MISMATCH = "MISMATCH"
    CONFLICT_REFERENCED = "CONFLICT_REFERENCED"
    UNAVAILABLE = "UNAVAILABLE"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationConsistencySeverity(str, Enum):
    """Diagnostic severity; ERROR is not enforcement, WARNING is not denial."""

    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationShadowResolverStatus(str, Enum):
    """Shadow resolver status; SHADOW_EVALUATED is not policy decision."""

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    SHADOW_EVALUATED = "SHADOW_EVALUATED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# SideEffects (plain dataclass, all defaults False)
# ---------------------------------------------------------------------------


@dataclass
class DelegationShadowResolverSideEffects:
    """Hard proof that P1.8.10 is diagnostic only.  All fields default to False."""

    policy_decision_made: bool = False
    custos_called: bool = False
    approval_created: bool = False
    authority_granted: bool = False
    authority_denied: bool = False
    runtime_allowed: bool = False
    runtime_blocked: bool = False
    enforcement_performed: bool = False
    delegation_executed: bool = False
    trace_written: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False


# ---------------------------------------------------------------------------
# Private enum parsers
# ---------------------------------------------------------------------------


def _parse_shadow_resolver_mode(
    value: DelegationShadowResolverMode | str,
) -> DelegationShadowResolverMode:
    if isinstance(value, DelegationShadowResolverMode):
        return value
    if isinstance(value, str):
        try:
            return DelegationShadowResolverMode(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid resolver_mode: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="resolver_mode",
            ) from exc
    raise DelegationError(
        "resolver_mode must be a string or DelegationShadowResolverMode",
        code=DelegationErrorCode.INVALID_ENUM,
        field="resolver_mode",
    )


def _parse_consistency_family(
    value: DelegationConsistencyFamily | str,
) -> DelegationConsistencyFamily:
    if isinstance(value, DelegationConsistencyFamily):
        return value
    if isinstance(value, str):
        try:
            return DelegationConsistencyFamily(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid family: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="family",
            ) from exc
    raise DelegationError(
        "family must be a string or DelegationConsistencyFamily",
        code=DelegationErrorCode.INVALID_ENUM,
        field="family",
    )


def _parse_consistency_finding_kind(
    value: DelegationConsistencyFindingKind | str,
) -> DelegationConsistencyFindingKind:
    if isinstance(value, DelegationConsistencyFindingKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationConsistencyFindingKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid finding_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="finding_kind",
            ) from exc
    raise DelegationError(
        "finding_kind must be a string or DelegationConsistencyFindingKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="finding_kind",
    )


def _parse_consistency_severity(
    value: DelegationConsistencySeverity | str,
) -> DelegationConsistencySeverity:
    if isinstance(value, DelegationConsistencySeverity):
        return value
    if isinstance(value, str):
        try:
            return DelegationConsistencySeverity(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid severity: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="severity",
            ) from exc
    raise DelegationError(
        "severity must be a string or DelegationConsistencySeverity",
        code=DelegationErrorCode.INVALID_ENUM,
        field="severity",
    )


def _parse_shadow_resolver_status(
    value: DelegationShadowResolverStatus | str,
) -> DelegationShadowResolverStatus:
    if isinstance(value, DelegationShadowResolverStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationShadowResolverStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid resolver_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="resolver_status",
            ) from exc
    raise DelegationError(
        "resolver_status must be a string or DelegationShadowResolverStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="resolver_status",
    )


# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationShadowResolverInputEnvelope:
    """One deterministic, hash-ready envelope wrapping P1.8.0-P1.8.9 context hashes.

    Boundary: InputEnvelope exists ≠ approval request. InputEnvelope hash
    ≠ TRACE_VERIFIED. InputEnvelope does not authorize, deny, enforce,
    execute, or mutate runtime.
    """

    schema_version: str
    shadow_resolver_input_envelope_id: str
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
    source_label: DelegationSourceLabel
    input_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "shadow_resolver_input_envelope_id": self.shadow_resolver_input_envelope_id,
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
            "source_label": self.source_label.value,
            "input_envelope_hash": self.input_envelope_hash,
        }


@dataclass(frozen=True)
class DelegationConsistencyFinding:
    """One diagnostic finding about a P1.8 reference family.

    Boundary: Finding is diagnostic only. Finding does not authorize,
    deny, enforce, approve, or block runtime.
    """

    schema_version: str
    finding_id: str
    delegation_ref_id: str
    family: DelegationConsistencyFamily
    finding_kind: DelegationConsistencyFindingKind
    severity: DelegationConsistencySeverity
    finding_ref: str | None
    finding_detail: str
    unavailable_reason: str | None
    source_label: DelegationSourceLabel
    finding_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "finding_id": self.finding_id,
            "delegation_ref_id": self.delegation_ref_id,
            "family": self.family.value,
            "finding_kind": self.finding_kind.value,
            "severity": self.severity.value,
            "finding_detail": self.finding_detail,
            "source_label": self.source_label.value,
            "finding_hash": self.finding_hash,
        }
        if self.finding_ref is not None:
            result["finding_ref"] = self.finding_ref
        if self.unavailable_reason is not None:
            result["unavailable_reason"] = self.unavailable_reason
        return result


@dataclass(frozen=True)
class DelegationConsistencyMatrixEntry:
    """One diagnostic matrix row for one P1.8 reference family.

    Boundary: MatrixEntry is diagnostic only. Family alignment is not
    verification. Finding count is not risk score. Presence is not
    validation.
    """

    schema_version: str
    entry_id: str
    delegation_ref_id: str
    family: DelegationConsistencyFamily
    present: bool
    hash_present: bool
    delegation_ref_aligned: bool
    source_label_present: bool
    finding_count: int
    unavailable_reason: str | None
    source_label: DelegationSourceLabel
    entry_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "delegation_ref_id": self.delegation_ref_id,
            "family": self.family.value,
            "present": self.present,
            "hash_present": self.hash_present,
            "delegation_ref_aligned": self.delegation_ref_aligned,
            "source_label_present": self.source_label_present,
            "finding_count": self.finding_count,
            "source_label": self.source_label.value,
            "entry_hash": self.entry_hash,
        }
        if self.unavailable_reason is not None:
            result["unavailable_reason"] = self.unavailable_reason
        return result


@dataclass(frozen=True)
class DelegationConsistencyMatrix:
    """Cross-family diagnostic matrix over P1.8 families.

    Boundary: ConsistencyMatrix is not approval matrix, not policy matrix,
    not enforcement matrix, not verification.
    """

    schema_version: str
    consistency_matrix_id: str
    delegation_ref_id: str
    entries: tuple[DelegationConsistencyMatrixEntry, ...]
    source_label: DelegationSourceLabel
    matrix_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "consistency_matrix_id": self.consistency_matrix_id,
            "delegation_ref_id": self.delegation_ref_id,
            "entry_ids": [e.entry_id for e in self.entries],
            "entry_hashes": [e.entry_hash for e in self.entries],
            "source_label": self.source_label.value,
            "matrix_hash": self.matrix_hash,
        }


@dataclass(frozen=True)
class DelegationShadowResolverReadinessProfile:
    """Presence/absence profile for P1.8 reference families.

    Boundary: ReadinessProfile is not approval readiness, not policy
    decision, not execution readiness.
    """

    schema_version: str
    readiness_profile_id: str
    delegation_ref_id: str
    has_foundation: bool
    has_identity: bool
    has_roles: bool
    has_constraints: bool
    has_authority: bool
    has_non_repudiation: bool
    has_identity_mesh: bool
    has_scope: bool
    has_lifecycle: bool
    has_chain: bool
    missing_families: tuple[DelegationConsistencyFamily, ...]
    policy_unavailable_reason: str
    custos_unavailable_reason: str
    approval_unavailable_reason: str
    runtime_unavailable_reason: str
    source_label: DelegationSourceLabel
    readiness_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "readiness_profile_id": self.readiness_profile_id,
            "delegation_ref_id": self.delegation_ref_id,
            "has_foundation": self.has_foundation,
            "has_identity": self.has_identity,
            "has_roles": self.has_roles,
            "has_constraints": self.has_constraints,
            "has_authority": self.has_authority,
            "has_non_repudiation": self.has_non_repudiation,
            "has_identity_mesh": self.has_identity_mesh,
            "has_scope": self.has_scope,
            "has_lifecycle": self.has_lifecycle,
            "has_chain": self.has_chain,
            "missing_families": [f.value for f in self.missing_families],
            "policy_unavailable_reason": self.policy_unavailable_reason,
            "custos_unavailable_reason": self.custos_unavailable_reason,
            "approval_unavailable_reason": self.approval_unavailable_reason,
            "runtime_unavailable_reason": self.runtime_unavailable_reason,
            "source_label": self.source_label.value,
            "readiness_hash": self.readiness_hash,
        }


@dataclass(frozen=True)
class DelegationConsistencySnapshot:
    """One deterministic diagnostic snapshot combining input envelope,
    findings, matrix, and readiness profile.

    Boundary: ConsistencySnapshot is not delegation verification, not
    approval, not policy compliance, not trace verification.
    """

    schema_version: str
    consistency_snapshot_id: str
    delegation_ref_id: str
    input_envelope_hash: str
    finding_hashes: tuple[str, ...]
    matrix_hash: str
    readiness_hash: str
    source_label: DelegationSourceLabel
    snapshot_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "consistency_snapshot_id": self.consistency_snapshot_id,
            "delegation_ref_id": self.delegation_ref_id,
            "input_envelope_hash": self.input_envelope_hash,
            "finding_hashes": list(self.finding_hashes),
            "matrix_hash": self.matrix_hash,
            "readiness_hash": self.readiness_hash,
            "source_label": self.source_label.value,
            "snapshot_hash": self.snapshot_hash,
        }


@dataclass(frozen=True)
class DelegationShadowResolverResult:
    """Final shadow-only diagnostic result.

    Boundary: ShadowResolverResult is not policy decision, not approval,
    not authorization, not runtime allow/block, not enforcement,
    not TRACE_VERIFIED.
    """

    schema_version: str
    shadow_resolver_result_id: str
    delegation_ref_id: str
    resolver_mode: DelegationShadowResolverMode
    resolver_status: DelegationShadowResolverStatus
    input_envelope_hash: str
    snapshot_hash: str
    matrix_hash: str
    readiness_hash: str
    finding_count: int
    unavailable_bindings: tuple[str, ...]
    source_label: DelegationSourceLabel
    result_hash: str
    side_effects: DelegationShadowResolverSideEffects

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "shadow_resolver_result_id": self.shadow_resolver_result_id,
            "delegation_ref_id": self.delegation_ref_id,
            "resolver_mode": self.resolver_mode.value,
            "resolver_status": self.resolver_status.value,
            "input_envelope_hash": self.input_envelope_hash,
            "snapshot_hash": self.snapshot_hash,
            "matrix_hash": self.matrix_hash,
            "readiness_hash": self.readiness_hash,
            "finding_count": self.finding_count,
            "unavailable_bindings": sorted(self.unavailable_bindings),
            "source_label": self.source_label.value,
            "result_hash": self.result_hash,
            "side_effects": {
                "policy_decision_made": self.side_effects.policy_decision_made,
                "custos_called": self.side_effects.custos_called,
                "approval_created": self.side_effects.approval_created,
                "authority_granted": self.side_effects.authority_granted,
                "authority_denied": self.side_effects.authority_denied,
                "runtime_allowed": self.side_effects.runtime_allowed,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "enforcement_performed": self.side_effects.enforcement_performed,
                "delegation_executed": self.side_effects.delegation_executed,
                "trace_written": self.side_effects.trace_written,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
        }


@dataclass(frozen=True)
class DelegationShadowResolverStatusReport:
    """Reports shadow resolver capability and unavailable surfaces.

    Boundary: StatusReport is capability metadata only; it does not
    make policy decisions or mutate runtime.
    """

    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: dict[str, str]
    side_effects: DelegationShadowResolverSideEffects
    status_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status_label": self.status_label,
            "available_contracts": sorted(self.available_contracts),
            "unavailable_bindings": {
                k: self.unavailable_bindings[k]
                for k in sorted(self.unavailable_bindings)
            },
            "side_effects": {
                "policy_decision_made": self.side_effects.policy_decision_made,
                "custos_called": self.side_effects.custos_called,
                "approval_created": self.side_effects.approval_created,
                "authority_granted": self.side_effects.authority_granted,
                "authority_denied": self.side_effects.authority_denied,
                "runtime_allowed": self.side_effects.runtime_allowed,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "enforcement_performed": self.side_effects.enforcement_performed,
                "delegation_executed": self.side_effects.delegation_executed,
                "trace_written": self.side_effects.trace_written,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
            "status_hash": self.status_hash,
        }


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------


def compute_shadow_resolver_input_envelope_hash(
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
        "source_label": source_label.value,
    })


def compute_consistency_finding_hash(
    *,
    family: DelegationConsistencyFamily,
    finding_kind: DelegationConsistencyFindingKind,
    severity: DelegationConsistencySeverity,
    finding_ref: str | None,
    finding_detail: str,
    source_label: DelegationSourceLabel,
) -> str:
    payload: dict[str, Any] = {
        "family": family.value,
        "finding_kind": finding_kind.value,
        "severity": severity.value,
        "finding_detail": finding_detail,
        "source_label": source_label.value,
    }
    if finding_ref is not None:
        payload["finding_ref"] = finding_ref
    return stable_hash(payload)


def compute_consistency_matrix_entry_hash(
    *,
    family: DelegationConsistencyFamily,
    present: bool,
    hash_present: bool,
    delegation_ref_aligned: bool,
    source_label_present: bool,
    finding_count: int,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "family": family.value,
        "present": present,
        "hash_present": hash_present,
        "delegation_ref_aligned": delegation_ref_aligned,
        "source_label_present": source_label_present,
        "finding_count": finding_count,
        "source_label": source_label.value,
    })


def compute_consistency_matrix_hash(
    *,
    entry_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "entry_hashes": list(entry_hashes),
        "source_label": source_label.value,
    })


def compute_shadow_resolver_readiness_hash(
    *,
    has_foundation: bool,
    has_identity: bool,
    has_roles: bool,
    has_constraints: bool,
    has_authority: bool,
    has_non_repudiation: bool,
    has_identity_mesh: bool,
    has_scope: bool,
    has_lifecycle: bool,
    has_chain: bool,
    missing_families: tuple[DelegationConsistencyFamily, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "has_foundation": has_foundation,
        "has_identity": has_identity,
        "has_roles": has_roles,
        "has_constraints": has_constraints,
        "has_authority": has_authority,
        "has_non_repudiation": has_non_repudiation,
        "has_identity_mesh": has_identity_mesh,
        "has_scope": has_scope,
        "has_lifecycle": has_lifecycle,
        "has_chain": has_chain,
        "missing_families": [f.value for f in missing_families],
        "source_label": source_label.value,
    })


def compute_consistency_snapshot_hash(
    *,
    input_envelope_hash: str,
    finding_hashes: tuple[str, ...],
    matrix_hash: str,
    readiness_hash: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "input_envelope_hash": input_envelope_hash,
        "finding_hashes": list(finding_hashes),
        "matrix_hash": matrix_hash,
        "readiness_hash": readiness_hash,
        "source_label": source_label.value,
    })


def compute_shadow_resolver_result_hash(
    *,
    delegation_ref_id: str,
    resolver_mode: DelegationShadowResolverMode,
    resolver_status: DelegationShadowResolverStatus,
    input_envelope_hash: str,
    snapshot_hash: str,
    matrix_hash: str,
    readiness_hash: str,
    finding_count: int,
    unavailable_bindings: tuple[str, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationShadowResolverSideEffects,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "resolver_mode": resolver_mode.value,
        "resolver_status": resolver_status.value,
        "input_envelope_hash": input_envelope_hash,
        "snapshot_hash": snapshot_hash,
        "matrix_hash": matrix_hash,
        "readiness_hash": readiness_hash,
        "finding_count": finding_count,
        "unavailable_bindings": sorted(unavailable_bindings),
        "source_label": source_label.value,
        "side_effects": {
            "policy_decision_made": side_effects.policy_decision_made,
            "custos_called": side_effects.custos_called,
            "approval_created": side_effects.approval_created,
            "authority_granted": side_effects.authority_granted,
            "authority_denied": side_effects.authority_denied,
            "runtime_allowed": side_effects.runtime_allowed,
            "runtime_blocked": side_effects.runtime_blocked,
            "enforcement_performed": side_effects.enforcement_performed,
            "delegation_executed": side_effects.delegation_executed,
            "trace_written": side_effects.trace_written,
            "ledger_written": side_effects.ledger_written,
            "global_trace_written": side_effects.global_trace_written,
            "runtime_mutated": side_effects.runtime_mutated,
        },
    })


def compute_shadow_resolver_status_report_hash(
    *,
    available_contracts: tuple[str, ...],
    side_effects: DelegationShadowResolverSideEffects,
) -> str:
    return stable_hash({
        "available_contracts": sorted(available_contracts),
        "side_effects": {
            "policy_decision_made": side_effects.policy_decision_made,
            "custos_called": side_effects.custos_called,
            "approval_created": side_effects.approval_created,
            "authority_granted": side_effects.authority_granted,
            "authority_denied": side_effects.authority_denied,
            "runtime_allowed": side_effects.runtime_allowed,
            "runtime_blocked": side_effects.runtime_blocked,
            "enforcement_performed": side_effects.enforcement_performed,
            "delegation_executed": side_effects.delegation_executed,
            "trace_written": side_effects.trace_written,
            "ledger_written": side_effects.ledger_written,
            "global_trace_written": side_effects.global_trace_written,
            "runtime_mutated": side_effects.runtime_mutated,
        },
    })


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_delegation_shadow_resolver_input_envelope(
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
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    shadow_resolver_input_envelope_id: str | None = None,
) -> DelegationShadowResolverInputEnvelope:
    """Build a DelegationShadowResolverInputEnvelope from P1.8.0-P1.8.9 context hashes."""
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
    parsed_label = _parse_source_label(source_label)

    if shadow_resolver_input_envelope_id is None:
        shadow_resolver_input_envelope_id = f"shadow-env-{delegation_ref_id}"

    input_hash = compute_shadow_resolver_input_envelope_hash(
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
        source_label=parsed_label,
    )

    return DelegationShadowResolverInputEnvelope(
        schema_version=DELEGATION_SHADOW_RESOLVER_INPUT_ENVELOPE_VERSION,
        shadow_resolver_input_envelope_id=shadow_resolver_input_envelope_id,
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
        source_label=parsed_label,
        input_envelope_hash=input_hash,
    )


def build_delegation_consistency_finding(
    *,
    delegation_ref_id: str,
    family: DelegationConsistencyFamily | str,
    finding_kind: DelegationConsistencyFindingKind | str,
    severity: DelegationConsistencySeverity | str = DelegationConsistencySeverity.INFO,
    finding_ref: str | None = None,
    finding_detail: str = "",
    unavailable_reason: str | None = None,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    finding_id: str | None = None,
) -> DelegationConsistencyFinding:
    """Build a diagnostic DelegationConsistencyFinding."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_family = _parse_consistency_family(family)
    parsed_kind = _parse_consistency_finding_kind(finding_kind)
    parsed_severity = _parse_consistency_severity(severity)
    finding_ref_clean = _optional_string(finding_ref)
    if not finding_detail:
        finding_detail = f"{parsed_family.value} {parsed_kind.value}"
    parsed_label = _parse_source_label(source_label)
    unavailable_reason_clean = _optional_string(unavailable_reason)

    if finding_id is None:
        finding_id = f"finding-{parsed_family.value}-{parsed_kind.value}-{delegation_ref_id[:12]}"

    finding_hash = compute_consistency_finding_hash(
        family=parsed_family,
        finding_kind=parsed_kind,
        severity=parsed_severity,
        finding_ref=finding_ref_clean,
        finding_detail=finding_detail,
        source_label=parsed_label,
    )

    return DelegationConsistencyFinding(
        schema_version=DELEGATION_CONSISTENCY_FINDING_VERSION,
        finding_id=finding_id,
        delegation_ref_id=delegation_ref_id,
        family=parsed_family,
        finding_kind=parsed_kind,
        severity=parsed_severity,
        finding_ref=finding_ref_clean,
        finding_detail=finding_detail,
        unavailable_reason=unavailable_reason_clean,
        source_label=parsed_label,
        finding_hash=finding_hash,
    )


def build_delegation_consistency_matrix_entry(
    *,
    delegation_ref_id: str,
    family: DelegationConsistencyFamily | str,
    present: bool = False,
    hash_present: bool = False,
    delegation_ref_aligned: bool = False,
    source_label_present: bool = False,
    finding_count: int = 0,
    unavailable_reason: str | None = None,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    entry_id: str | None = None,
) -> DelegationConsistencyMatrixEntry:
    """Build a diagnostic DelegationConsistencyMatrixEntry."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_family = _parse_consistency_family(family)
    parsed_label = _parse_source_label(source_label)
    unavailable_reason_clean = _optional_string(unavailable_reason)
    if finding_count < 0:
        raise DelegationValidationError(
            "finding_count must be >= 0",
            code=DelegationErrorCode.VALIDATION_ERROR,
            field="finding_count",
        )

    if entry_id is None:
        entry_id = f"entry-{parsed_family.value}-{delegation_ref_id[:12]}"

    entry_hash = compute_consistency_matrix_entry_hash(
        family=parsed_family,
        present=present,
        hash_present=hash_present,
        delegation_ref_aligned=delegation_ref_aligned,
        source_label_present=source_label_present,
        finding_count=finding_count,
        source_label=parsed_label,
    )

    return DelegationConsistencyMatrixEntry(
        schema_version=DELEGATION_CONSISTENCY_MATRIX_ENTRY_VERSION,
        entry_id=entry_id,
        delegation_ref_id=delegation_ref_id,
        family=parsed_family,
        present=present,
        hash_present=hash_present,
        delegation_ref_aligned=delegation_ref_aligned,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason_clean,
        source_label=parsed_label,
        entry_hash=entry_hash,
    )


def build_delegation_consistency_matrix(
    *,
    delegation_ref_id: str,
    entries: Sequence[DelegationConsistencyMatrixEntry],
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    consistency_matrix_id: str | None = None,
) -> DelegationConsistencyMatrix:
    """Build a cross-family DelegationConsistencyMatrix."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)

    ordered_entries = tuple(sorted(entries, key=lambda e: e.family.value))
    entry_hashes = tuple(e.entry_hash for e in ordered_entries)

    if consistency_matrix_id is None:
        consistency_matrix_id = f"consistency-matrix-{delegation_ref_id[:12]}"

    matrix_hash = compute_consistency_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=parsed_label,
    )

    return DelegationConsistencyMatrix(
        schema_version=DELEGATION_CONSISTENCY_MATRIX_VERSION,
        consistency_matrix_id=consistency_matrix_id,
        delegation_ref_id=delegation_ref_id,
        entries=ordered_entries,
        source_label=parsed_label,
        matrix_hash=matrix_hash,
    )


def build_delegation_shadow_resolver_readiness_profile(
    *,
    delegation_ref_id: str,
    has_foundation: bool = False,
    has_identity: bool = False,
    has_roles: bool = False,
    has_constraints: bool = False,
    has_authority: bool = False,
    has_non_repudiation: bool = False,
    has_identity_mesh: bool = False,
    has_scope: bool = False,
    has_lifecycle: bool = False,
    has_chain: bool = False,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_profile_id: str | None = None,
) -> DelegationShadowResolverReadinessProfile:
    """Build a DelegationShadowResolverReadinessProfile."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)

    presence_map = {
        DelegationConsistencyFamily.FOUNDATION: has_foundation,
        DelegationConsistencyFamily.IDENTITY: has_identity,
        DelegationConsistencyFamily.ROLES: has_roles,
        DelegationConsistencyFamily.CONSTRAINTS: has_constraints,
        DelegationConsistencyFamily.AUTHORITY: has_authority,
        DelegationConsistencyFamily.NON_REPUDIATION: has_non_repudiation,
        DelegationConsistencyFamily.IDENTITY_MESH: has_identity_mesh,
        DelegationConsistencyFamily.SCOPE: has_scope,
        DelegationConsistencyFamily.LIFECYCLE: has_lifecycle,
        DelegationConsistencyFamily.CHAIN: has_chain,
    }

    missing = tuple(
        sorted(
            [f for f, present in presence_map.items() if not present],
            key=lambda f: f.value,
        )
    )

    policy_reason = (
        "Policy decision engine is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    )
    custos_reason = (
        "Custos resolver is not available in P1.8.10; "
        "shadow resolver does not call Custos"
    )
    approval_reason = (
        "Approval system is not available in P1.8.10; "
        "shadow resolver does not create approvals"
    )
    runtime_reason = (
        "Runtime delegation execution is not available in P1.8.10; "
        "shadow resolver is diagnostic only"
    )

    if readiness_profile_id is None:
        readiness_profile_id = f"sr-readiness-{delegation_ref_id[:12]}"

    readiness_hash = compute_shadow_resolver_readiness_hash(
        has_foundation=has_foundation,
        has_identity=has_identity,
        has_roles=has_roles,
        has_constraints=has_constraints,
        has_authority=has_authority,
        has_non_repudiation=has_non_repudiation,
        has_identity_mesh=has_identity_mesh,
        has_scope=has_scope,
        has_lifecycle=has_lifecycle,
        has_chain=has_chain,
        missing_families=missing,
        source_label=parsed_label,
    )

    return DelegationShadowResolverReadinessProfile(
        schema_version=DELEGATION_SHADOW_RESOLVER_READINESS_PROFILE_VERSION,
        readiness_profile_id=readiness_profile_id,
        delegation_ref_id=delegation_ref_id,
        has_foundation=has_foundation,
        has_identity=has_identity,
        has_roles=has_roles,
        has_constraints=has_constraints,
        has_authority=has_authority,
        has_non_repudiation=has_non_repudiation,
        has_identity_mesh=has_identity_mesh,
        has_scope=has_scope,
        has_lifecycle=has_lifecycle,
        has_chain=has_chain,
        missing_families=missing,
        policy_unavailable_reason=policy_reason,
        custos_unavailable_reason=custos_reason,
        approval_unavailable_reason=approval_reason,
        runtime_unavailable_reason=runtime_reason,
        source_label=parsed_label,
        readiness_hash=readiness_hash,
    )


def build_delegation_consistency_snapshot(
    *,
    delegation_ref_id: str,
    input_envelope_hash: str,
    findings: Sequence[DelegationConsistencyFinding],
    matrix: DelegationConsistencyMatrix,
    readiness_profile: DelegationShadowResolverReadinessProfile,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    consistency_snapshot_id: str | None = None,
) -> DelegationConsistencySnapshot:
    """Build a DelegationConsistencySnapshot."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    _required_string(input_envelope_hash, field_name="input_envelope_hash")
    parsed_label = _parse_source_label(source_label)

    finding_hashes = tuple(
        sorted([f.finding_hash for f in findings])
    )

    if consistency_snapshot_id is None:
        consistency_snapshot_id = f"snapshot-{delegation_ref_id[:12]}"

    snapshot_hash = compute_consistency_snapshot_hash(
        input_envelope_hash=input_envelope_hash,
        finding_hashes=finding_hashes,
        matrix_hash=matrix.matrix_hash,
        readiness_hash=readiness_profile.readiness_hash,
        source_label=parsed_label,
    )

    return DelegationConsistencySnapshot(
        schema_version=DELEGATION_CONSISTENCY_SNAPSHOT_VERSION,
        consistency_snapshot_id=consistency_snapshot_id,
        delegation_ref_id=delegation_ref_id,
        input_envelope_hash=input_envelope_hash,
        finding_hashes=finding_hashes,
        matrix_hash=matrix.matrix_hash,
        readiness_hash=readiness_profile.readiness_hash,
        source_label=parsed_label,
        snapshot_hash=snapshot_hash,
    )


def build_delegation_shadow_resolver_result(
    *,
    delegation_ref_id: str,
    input_envelope: DelegationShadowResolverInputEnvelope,
    snapshot: DelegationConsistencySnapshot,
    matrix: DelegationConsistencyMatrix,
    readiness_profile: DelegationShadowResolverReadinessProfile,
    findings: Sequence[DelegationConsistencyFinding],
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    shadow_resolver_result_id: str | None = None,
    resolver_mode: DelegationShadowResolverMode | str = DelegationShadowResolverMode.DIAGNOSTIC_ONLY,
) -> DelegationShadowResolverResult:
    """Build a DelegationShadowResolverResult."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)
    parsed_mode = _parse_shadow_resolver_mode(resolver_mode)

    side_effects = DelegationShadowResolverSideEffects()

    unavailable = tuple(sorted(DELEGATION_SHADOW_RESOLVER_UNAVAILABLE_BINDINGS.keys()))

    if shadow_resolver_result_id is None:
        shadow_resolver_result_id = f"sr-result-{delegation_ref_id[:12]}"

    finding_count = len(list(findings))

    result_hash = compute_shadow_resolver_result_hash(
        delegation_ref_id=delegation_ref_id,
        resolver_mode=parsed_mode,
        resolver_status=DelegationShadowResolverStatus.SHADOW_EVALUATED,
        input_envelope_hash=input_envelope.input_envelope_hash,
        snapshot_hash=snapshot.snapshot_hash,
        matrix_hash=matrix.matrix_hash,
        readiness_hash=readiness_profile.readiness_hash,
        finding_count=finding_count,
        unavailable_bindings=unavailable,
        source_label=parsed_label,
        side_effects=side_effects,
    )

    return DelegationShadowResolverResult(
        schema_version=DELEGATION_SHADOW_RESOLVER_RESULT_VERSION,
        shadow_resolver_result_id=shadow_resolver_result_id,
        delegation_ref_id=delegation_ref_id,
        resolver_mode=parsed_mode,
        resolver_status=DelegationShadowResolverStatus.SHADOW_EVALUATED,
        input_envelope_hash=input_envelope.input_envelope_hash,
        snapshot_hash=snapshot.snapshot_hash,
        matrix_hash=matrix.matrix_hash,
        readiness_hash=readiness_profile.readiness_hash,
        finding_count=finding_count,
        unavailable_bindings=unavailable,
        source_label=parsed_label,
        result_hash=result_hash,
        side_effects=side_effects,
    )


def build_delegation_shadow_resolver_status_report(
    *,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.LIVE,
) -> DelegationShadowResolverStatusReport:
    """Build a DelegationShadowResolverStatusReport."""
    _parse_source_label(source_label)  # validate label, result not needed in report
    side_effects = DelegationShadowResolverSideEffects()

    available = (
        "DelegationShadowResolverInputEnvelope",
        "DelegationConsistencyFinding",
        "DelegationConsistencyMatrixEntry",
        "DelegationConsistencyMatrix",
        "DelegationShadowResolverReadinessProfile",
        "DelegationConsistencySnapshot",
        "DelegationShadowResolverResult",
        "DelegationShadowResolverSideEffects",
        "DelegationShadowResolverStatusReport",
    )

    status_hash = compute_shadow_resolver_status_report_hash(
        available_contracts=available,
        side_effects=side_effects,
    )

    return DelegationShadowResolverStatusReport(
        schema_version=DELEGATION_SHADOW_RESOLVER_STATUS_REPORT_VERSION,
        status_label="Delegation Shadow Resolver / Consistency Model — Diagnostic Only",
        available_contracts=available,
        unavailable_bindings=dict(DELEGATION_SHADOW_RESOLVER_UNAVAILABLE_BINDINGS),
        side_effects=side_effects,
        status_hash=status_hash,
    )


# ---------------------------------------------------------------------------
# Serialize helpers
# ---------------------------------------------------------------------------


def serialize_delegation_shadow_resolver_input_envelope(
    input_envelope: DelegationShadowResolverInputEnvelope,
) -> str:
    """Serialize a DelegationShadowResolverInputEnvelope to deterministic JSON."""
    return to_canonical_json(input_envelope)


def serialize_delegation_consistency_matrix(
    matrix: DelegationConsistencyMatrix,
) -> str:
    """Serialize a DelegationConsistencyMatrix to deterministic JSON."""
    return to_canonical_json(matrix)


def serialize_delegation_shadow_resolver_result(
    result: DelegationShadowResolverResult,
) -> str:
    """Serialize a DelegationShadowResolverResult to deterministic JSON."""
    return to_canonical_json(result)


# ---------------------------------------------------------------------------
# Convenience hash wrappers
# ---------------------------------------------------------------------------


def hash_delegation_shadow_resolver_input_envelope(
    input_envelope: DelegationShadowResolverInputEnvelope,
) -> str:
    """Return the precomputed input_envelope_hash."""
    return input_envelope.input_envelope_hash


def hash_delegation_consistency_finding(
    finding: DelegationConsistencyFinding,
) -> str:
    """Return the precomputed finding_hash."""
    return finding.finding_hash


def hash_delegation_consistency_matrix_entry(
    entry: DelegationConsistencyMatrixEntry,
) -> str:
    """Return the precomputed entry_hash."""
    return entry.entry_hash


def hash_delegation_consistency_matrix(
    matrix: DelegationConsistencyMatrix,
) -> str:
    """Return the precomputed matrix_hash."""
    return matrix.matrix_hash


def hash_delegation_shadow_resolver_readiness_profile(
    profile: DelegationShadowResolverReadinessProfile,
) -> str:
    """Return the precomputed readiness_hash."""
    return profile.readiness_hash


def hash_delegation_consistency_snapshot(
    snapshot: DelegationConsistencySnapshot,
) -> str:
    """Return the precomputed snapshot_hash."""
    return snapshot.snapshot_hash


def hash_delegation_shadow_resolver_result(
    result: DelegationShadowResolverResult,
) -> str:
    """Return the precomputed result_hash."""
    return result.result_hash


def hash_delegation_shadow_resolver_status_report(
    report: DelegationShadowResolverStatusReport,
) -> str:
    """Return the precomputed status_hash."""
    return report.status_hash
