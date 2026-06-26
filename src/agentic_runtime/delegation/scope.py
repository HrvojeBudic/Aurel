"""Delegation scope / boundary model (P1.8.7).

Deterministic, versioned, JSON-safe, side-effect-free delegation scope and
boundary reference layer for delegation accountability. Binds declarative
scope refs, boundary refs, inclusion refs, exclusion refs, boundary matrix,
scope readiness profile, and scope envelope to DelegationRef /
DelegationIdentity / DelegationRoleBindingSet / DelegationConstraintSet /
DelegationAuthorityBindingSet / DelegationNonRepudiationBindingSet /
DelegationIdentityMeshBindingSet without granting permission, granting
access, enforcing boundaries, blocking runtime, mutating tool/data/memory/
path/network access, calling policy/Custos, creating approval, writing
Ledger, writing global trace, or mutating runtime.

Architectural law:
  - DelegationScopeRef exists does not mean permission is granted.
  - DelegationBoundaryRef exists does not mean boundary is enforced.
  - ScopeEnvelope exists does not mean runtime access control exists.
  - BoundaryMatrix exists does not mean enforcement matrix exists.
  - IN_SCOPE exists does not mean allowed.
  - OUT_OF_SCOPE exists does not mean blocked.
  - InclusionRef exists does not mean permission.
  - ExclusionRef exists does not mean denial.
  - ScopeReadinessProfile exists does not mean enforcement readiness
    guarantee.
  - Scope hash exists does not mean TRACE_VERIFIED.
  - scope_envelope_hash exists ≠ TRACE_VERIFIED.
  - scope_binding_set_hash exists ≠ proof of enforcement.
  - DelegationScopeRef is reference-only scope metadata; it does not
    grant permission, authorize access, enforce boundaries, or mutate
    tools, data, memory, paths, network, or runtime.
  - DelegationBoundaryRef is reference-only boundary metadata; it does
    not enforce boundaries, block runtime, or grant/deny access.
  - DelegationScopeInclusionRef is declared inclusion metadata; it is
    not permission, not allowed, not access grant.
  - DelegationScopeExclusionRef is declared exclusion metadata; it is
    not denial, not runtime block, not enforcement.
  - DelegationBoundaryMatrixEntry is metadata; it is not runtime rule,
    not policy decision, not access-control rule.
  - DelegationBoundaryMatrix is not enforcement matrix, not
    access-control matrix; it does not allow/block runtime behavior.
  - DelegationScopeReadinessProfile is presence/absence information;
    it is not enforcement readiness guarantee, not policy decision,
    not approval.
  - DelegationScopeEnvelope is a reference packet; it is not permission
    grant, not runtime access control, not boundary enforcement, not
    TRACE_VERIFIED.
  - DelegationScopeBinding binds scope/boundary metadata; it is not
    permission, not access control, not enforcement, not policy
    decision, not trace verification.
  - DelegationScopeBindingSet describes scope/boundary hooks; it does
    not grant access, enforce boundaries, or write Ledger/global trace.
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

DELEGATION_SCOPE_TASK_ID = "P1.8.7"
DELEGATION_SCOPE_REF_VERSION = "delegation_scope_ref.v1"
DELEGATION_BOUNDARY_REF_VERSION = "delegation_boundary_ref.v1"
DELEGATION_SCOPE_INCLUSION_REF_VERSION = "delegation_scope_inclusion_ref.v1"
DELEGATION_SCOPE_EXCLUSION_REF_VERSION = "delegation_scope_exclusion_ref.v1"
DELEGATION_BOUNDARY_MATRIX_ENTRY_VERSION = "delegation_boundary_matrix_entry.v1"
DELEGATION_BOUNDARY_MATRIX_VERSION = "delegation_boundary_matrix.v1"
DELEGATION_SCOPE_READINESS_PROFILE_VERSION = "delegation_scope_readiness_profile.v1"
DELEGATION_SCOPE_ENVELOPE_VERSION = "delegation_scope_envelope.v1"
DELEGATION_SCOPE_BINDING_VERSION = "delegation_scope_binding.v1"
DELEGATION_SCOPE_BINDING_SET_VERSION = "delegation_scope_binding_set.v1"
DELEGATION_SCOPE_SIDE_EFFECTS_VERSION = "delegation_scope_side_effects.v1"
DELEGATION_SCOPE_STATUS_REPORT_VERSION = "delegation_scope_status_report.v1"

DELEGATION_SCOPE_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.7; "
        "scope/boundary schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.7"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.7 "
        "scope boundary reference layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.7 "
        "scope boundary reference layer"
    ),
    "Permission Grant": (
        "Permission grant is not available in P1.8.7; "
        "scope refs are reference-only"
    ),
    "Access Control Engine": (
        "Access control engine scheduled for later P1.8 tasks; not P1.8.7"
    ),
    "Runtime Boundary Enforcer": (
        "Runtime boundary enforcer scheduled for later P1.8 tasks; not P1.8.7"
    ),
    "Tool Permission Mutation": (
        "Tool permission mutation is not available in P1.8.7; "
        "scope refs are reference-only"
    ),
    "Data Access Mutation": (
        "Data access mutation is not available in P1.8.7; "
        "scope refs are reference-only"
    ),
    "Memory Access Mutation": (
        "Memory access mutation is not available in P1.8.7; "
        "scope refs are reference-only"
    ),
    "Path Authorization": (
        "Path authorization scheduled for later P1.8 tasks; not P1.8.7"
    ),
    "Network Access Mutation": (
        "Network access mutation is not available in P1.8.7; "
        "scope refs are reference-only"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision scheduled for later P1.8 tasks; not P1.8.7"
    ),
    "Approval Creation": (
        "Approval creation is not available in P1.8.7; "
        "scope refs are reference-only"
    ),
    "Runtime Blocker": (
        "Runtime blocker scheduled for later P1.8 tasks; not P1.8.7"
    ),
    "P1.8.8 Expiry/Revocation Model": (
        "P1.8.8 expiry/revocation model is not available in P1.8.7"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 provenance/disclosure layer is not "
        "available in P1.8.7"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.7"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world)
# ---------------------------------------------------------------------------

SCOPE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "scope_ref_id",
    "delegation_ref_id",
    "scope_kind",
    "scope_ref",
    "scope_description",
    "source_label",
    "scope_status",
    "scope_hash",
})

BOUNDARY_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "boundary_ref_id",
    "delegation_ref_id",
    "boundary_kind",
    "boundary_dimension",
    "boundary_ref",
    "boundary_description",
    "source_label",
    "scope_status",
    "boundary_hash",
})

INCLUSION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "inclusion_ref_id",
    "delegation_ref_id",
    "scope_ref_id",
    "boundary_dimension",
    "inclusion_ref",
    "inclusion_description",
    "source_label",
    "scope_status",
    "inclusion_hash",
})

EXCLUSION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "exclusion_ref_id",
    "delegation_ref_id",
    "scope_ref_id",
    "boundary_dimension",
    "exclusion_ref",
    "exclusion_description",
    "source_label",
    "scope_status",
    "exclusion_hash",
})

MATRIX_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "entry_id",
    "delegation_ref_id",
    "dimension",
    "posture",
    "boundary_ref_id",
    "reason_ref",
    "source_label",
    "scope_status",
    "entry_hash",
})

BOUNDARY_MATRIX_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "boundary_matrix_id",
    "delegation_ref_id",
    "entries",
    "source_label",
    "boundary_matrix_hash",
})

READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "scope_readiness_profile_id",
    "delegation_ref_id",
    "has_scope_refs",
    "has_boundary_refs",
    "has_inclusion_refs",
    "has_exclusion_refs",
    "has_boundary_matrix",
    "has_tool_boundary",
    "has_data_boundary",
    "has_memory_boundary",
    "has_path_boundary",
    "has_runtime_boundary",
    "has_agent_boundary",
    "has_model_boundary",
    "has_network_boundary",
    "has_human_approval_boundary",
    "has_time_boundary",
    "has_risk_boundary",
    "missing_components",
    "enforcement_unavailable_reason",
    "source_label",
    "scope_readiness_hash",
})

SCOPE_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "scope_envelope_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_refs",
    "boundary_refs",
    "inclusion_refs",
    "exclusion_refs",
    "boundary_matrix_hash",
    "scope_readiness_hash",
    "source_label",
    "scope_envelope_hash",
})

SCOPE_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "scope_envelope_hash",
    "boundary_matrix_hash",
    "scope_readiness_hash",
    "source_label",
    "scope_status",
    "binding_hash",
})

SCOPE_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "scope_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_binding_set_hash",
    "bindings",
    "source_label",
    "scope_binding_set_hash",
    "side_effects",
})

SCOPE_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "permission_granted",
    "access_granted",
    "boundary_enforced",
    "runtime_blocked",
    "tool_permission_changed",
    "data_access_changed",
    "memory_access_changed",
    "path_authorized",
    "network_access_changed",
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

SCOPE_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationScopeKind(str, Enum):
    """Declared scope kind; scope kind does not grant permission or authorize access."""

    TASK_SCOPE = "TASK_SCOPE"
    TOOL_SCOPE = "TOOL_SCOPE"
    DATA_SCOPE = "DATA_SCOPE"
    MEMORY_SCOPE = "MEMORY_SCOPE"
    PATH_SCOPE = "PATH_SCOPE"
    RUNTIME_SCOPE = "RUNTIME_SCOPE"
    AGENT_SCOPE = "AGENT_SCOPE"
    MODEL_SCOPE = "MODEL_SCOPE"
    NETWORK_SCOPE = "NETWORK_SCOPE"
    APPROVAL_SCOPE = "APPROVAL_SCOPE"
    TIME_SCOPE = "TIME_SCOPE"
    RISK_SCOPE = "RISK_SCOPE"
    UNKNOWN = "UNKNOWN"


class DelegationBoundaryKind(str, Enum):
    """Declared boundary kind; boundary kind does not enforce or grant/deny permission."""

    INCLUSION = "INCLUSION"
    EXCLUSION = "EXCLUSION"
    LIMIT = "LIMIT"
    REQUIREMENT = "REQUIREMENT"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class DelegationScopeDimension(str, Enum):
    """Declared boundary dimension; dimension does not change tool/data/memory/path/network/runtime behavior."""

    TOOL = "TOOL"
    DATA = "DATA"
    MEMORY = "MEMORY"
    PATH = "PATH"
    RUNTIME = "RUNTIME"
    AGENT = "AGENT"
    MODEL = "MODEL"
    NETWORK = "NETWORK"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    TIME = "TIME"
    RISK = "RISK"
    UNKNOWN = "UNKNOWN"


class DelegationBoundaryPosture(str, Enum):
    """Declared boundary posture.

    IN_SCOPE is not allowed.
    OUT_OF_SCOPE is not blocked.
    REFERENCE_ONLY is not permission.
    UNAVAILABLE is honest unavailability.
    """

    IN_SCOPE = "IN_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class DelegationScopeStatus(str, Enum):
    """Status of scope/boundary schema availability; not enforcement or permission status."""

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parse helpers
# ---------------------------------------------------------------------------


def _parse_scope_kind(value: DelegationScopeKind | str) -> DelegationScopeKind:
    if isinstance(value, DelegationScopeKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationScopeKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid scope_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="scope_kind",
            ) from exc
    raise DelegationError(
        "scope_kind must be a string or DelegationScopeKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="scope_kind",
    )


def _parse_boundary_kind(value: DelegationBoundaryKind | str) -> DelegationBoundaryKind:
    if isinstance(value, DelegationBoundaryKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationBoundaryKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid boundary_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="boundary_kind",
            ) from exc
    raise DelegationError(
        "boundary_kind must be a string or DelegationBoundaryKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="boundary_kind",
    )


def _parse_scope_dimension(value: DelegationScopeDimension | str) -> DelegationScopeDimension:
    if isinstance(value, DelegationScopeDimension):
        return value
    if isinstance(value, str):
        try:
            return DelegationScopeDimension(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid dimension: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="dimension",
            ) from exc
    raise DelegationError(
        "dimension must be a string or DelegationScopeDimension",
        code=DelegationErrorCode.INVALID_ENUM,
        field="dimension",
    )


def _parse_boundary_posture(value: DelegationBoundaryPosture | str) -> DelegationBoundaryPosture:
    if isinstance(value, DelegationBoundaryPosture):
        return value
    if isinstance(value, str):
        try:
            return DelegationBoundaryPosture(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid posture: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="posture",
            ) from exc
    raise DelegationError(
        "posture must be a string or DelegationBoundaryPosture",
        code=DelegationErrorCode.INVALID_ENUM,
        field="posture",
    )


def _parse_scope_status(value: DelegationScopeStatus | str) -> DelegationScopeStatus:
    if isinstance(value, DelegationScopeStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationScopeStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid scope_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="scope_status",
            ) from exc
    raise DelegationError(
        "scope_status must be a string or DelegationScopeStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="scope_status",
    )


# ---------------------------------------------------------------------------
# DelegationScopeRef
# ---------------------------------------------------------------------------


def compute_scope_ref_hash(
    *,
    scope_kind: DelegationScopeKind,
    scope_ref: str,
    scope_description: str,
    delegation_ref_id: str,
    source_label: DelegationSourceLabel,
    scope_status: DelegationScopeStatus,
    schema_version: str = DELEGATION_SCOPE_REF_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "schema_version": schema_version,
        "scope_description": scope_description,
        "scope_kind": scope_kind.value,
        "scope_ref": scope_ref,
        "scope_status": scope_status.value,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeRef:
    """Reference-only declared scope metadata.

    DelegationScopeRef describes scope metadata.
    It does not grant permission, authorize access, enforce boundaries,
    or mutate tools, data, memory, paths, network, or runtime.
    """

    scope_kind: DelegationScopeKind
    scope_ref: str
    delegation_ref_id: str
    scope_description: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_SCOPE_REF_VERSION
    scope_ref_id: str = ""
    scope_hash: str = ""

    def __post_init__(self) -> None:
        scope_kind = _parse_scope_kind(self.scope_kind)
        scope_ref = _required_string(self.scope_ref, field_name="scope_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        scope_status = _parse_scope_status(self.scope_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        scope_description = (
            self.scope_description.strip()
            if isinstance(self.scope_description, str)
            else ""
        )

        scope_hash = compute_scope_ref_hash(
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            scope_description=scope_description,
            delegation_ref_id=delegation_ref_id,
            source_label=source_label,
            scope_status=scope_status,
            schema_version=schema_version,
        )
        scope_ref_id = f"scope:{scope_hash[:16]}"

        if self.scope_hash not in ("", scope_hash):
            raise DelegationValidationError(
                "scope_hash does not match scope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_hash",
            )
        if self.scope_ref_id not in ("", scope_ref_id):
            raise DelegationValidationError(
                "scope_ref_id does not match scope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_ref_id",
            )

        object.__setattr__(self, "scope_kind", scope_kind)
        object.__setattr__(self, "scope_ref", scope_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "scope_description", scope_description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_status", scope_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "scope_hash", scope_hash)
        object.__setattr__(self, "scope_ref_id", scope_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "schema_version": self.schema_version,
            "scope_description": self.scope_description,
            "scope_hash": self.scope_hash,
            "scope_kind": self.scope_kind.value,
            "scope_ref": self.scope_ref,
            "scope_ref_id": self.scope_ref_id,
            "scope_status": self.scope_status.value,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeRef:
        validate_known_fields(data, SCOPE_REF_KNOWN_FIELDS, label="delegation_scope_ref")
        return cls(
            scope_kind=data["scope_kind"],
            scope_ref=data["scope_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            scope_description=data.get("scope_description", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            scope_status=data.get("scope_status", DelegationScopeStatus.REFERENCE_ONLY),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_REF_VERSION),
            scope_ref_id=data.get("scope_ref_id", ""),
            scope_hash=data.get("scope_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationBoundaryRef
# ---------------------------------------------------------------------------


def compute_boundary_ref_hash(
    *,
    boundary_kind: DelegationBoundaryKind,
    boundary_dimension: DelegationScopeDimension,
    boundary_ref: str,
    boundary_description: str,
    delegation_ref_id: str,
    source_label: DelegationSourceLabel,
    scope_status: DelegationScopeStatus,
    schema_version: str = DELEGATION_BOUNDARY_REF_VERSION,
) -> str:
    return stable_hash({
        "boundary_description": boundary_description,
        "boundary_dimension": boundary_dimension.value,
        "boundary_kind": boundary_kind.value,
        "boundary_ref": boundary_ref,
        "delegation_ref_id": delegation_ref_id,
        "schema_version": schema_version,
        "scope_status": scope_status.value,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationBoundaryRef:
    """Reference-only declared boundary metadata.

    DelegationBoundaryRef describes boundary metadata.
    It does not enforce boundaries, block runtime, or grant/deny access.
    """

    boundary_kind: DelegationBoundaryKind
    boundary_dimension: DelegationScopeDimension
    boundary_ref: str
    delegation_ref_id: str
    boundary_description: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_BOUNDARY_REF_VERSION
    boundary_ref_id: str = ""
    boundary_hash: str = ""

    def __post_init__(self) -> None:
        boundary_kind = _parse_boundary_kind(self.boundary_kind)
        boundary_dimension = _parse_scope_dimension(self.boundary_dimension)
        boundary_ref = _required_string(self.boundary_ref, field_name="boundary_ref")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        scope_status = _parse_scope_status(self.scope_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        boundary_description = (
            self.boundary_description.strip()
            if isinstance(self.boundary_description, str)
            else ""
        )

        boundary_hash = compute_boundary_ref_hash(
            boundary_kind=boundary_kind,
            boundary_dimension=boundary_dimension,
            boundary_ref=boundary_ref,
            boundary_description=boundary_description,
            delegation_ref_id=delegation_ref_id,
            source_label=source_label,
            scope_status=scope_status,
            schema_version=schema_version,
        )
        boundary_ref_id = f"bnd:{boundary_hash[:16]}"

        if self.boundary_hash not in ("", boundary_hash):
            raise DelegationValidationError(
                "boundary_hash does not match boundary content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="boundary_hash",
            )
        if self.boundary_ref_id not in ("", boundary_ref_id):
            raise DelegationValidationError(
                "boundary_ref_id does not match boundary content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="boundary_ref_id",
            )

        object.__setattr__(self, "boundary_kind", boundary_kind)
        object.__setattr__(self, "boundary_dimension", boundary_dimension)
        object.__setattr__(self, "boundary_ref", boundary_ref)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "boundary_description", boundary_description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_status", scope_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "boundary_hash", boundary_hash)
        object.__setattr__(self, "boundary_ref_id", boundary_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundary_description": self.boundary_description,
            "boundary_dimension": self.boundary_dimension.value,
            "boundary_hash": self.boundary_hash,
            "boundary_kind": self.boundary_kind.value,
            "boundary_ref": self.boundary_ref,
            "boundary_ref_id": self.boundary_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "schema_version": self.schema_version,
            "scope_status": self.scope_status.value,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationBoundaryRef:
        validate_known_fields(data, BOUNDARY_REF_KNOWN_FIELDS, label="delegation_boundary_ref")
        return cls(
            boundary_kind=data["boundary_kind"],
            boundary_dimension=data["boundary_dimension"],
            boundary_ref=data["boundary_ref"],
            delegation_ref_id=data["delegation_ref_id"],
            boundary_description=data.get("boundary_description", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            scope_status=data.get("scope_status", DelegationScopeStatus.REFERENCE_ONLY),
            schema_version=data.get("schema_version", DELEGATION_BOUNDARY_REF_VERSION),
            boundary_ref_id=data.get("boundary_ref_id", ""),
            boundary_hash=data.get("boundary_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeInclusionRef
# ---------------------------------------------------------------------------


def compute_inclusion_ref_hash(
    *,
    delegation_ref_id: str,
    scope_ref_id: str,
    boundary_dimension: DelegationScopeDimension,
    inclusion_ref: str,
    inclusion_description: str,
    source_label: DelegationSourceLabel,
    scope_status: DelegationScopeStatus,
    schema_version: str = DELEGATION_SCOPE_INCLUSION_REF_VERSION,
) -> str:
    return stable_hash({
        "boundary_dimension": boundary_dimension.value,
        "delegation_ref_id": delegation_ref_id,
        "inclusion_description": inclusion_description,
        "inclusion_ref": inclusion_ref,
        "schema_version": schema_version,
        "scope_ref_id": scope_ref_id,
        "scope_status": scope_status.value,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeInclusionRef:
    """Explicit declared inclusion metadata.

    DelegationScopeInclusionRef describes what is declared in scope.
    It is not permission, not allowed, not access grant.
    """

    delegation_ref_id: str
    scope_ref_id: str
    boundary_dimension: DelegationScopeDimension
    inclusion_ref: str
    inclusion_description: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_SCOPE_INCLUSION_REF_VERSION
    inclusion_ref_id: str = ""
    inclusion_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        scope_ref_id = _required_string(self.scope_ref_id, field_name="scope_ref_id")
        boundary_dimension = _parse_scope_dimension(self.boundary_dimension)
        inclusion_ref = _required_string(self.inclusion_ref, field_name="inclusion_ref")
        source_label = _parse_source_label(self.source_label)
        scope_status = _parse_scope_status(self.scope_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        inclusion_description = (
            self.inclusion_description.strip()
            if isinstance(self.inclusion_description, str)
            else ""
        )

        inclusion_hash = compute_inclusion_ref_hash(
            delegation_ref_id=delegation_ref_id,
            scope_ref_id=scope_ref_id,
            boundary_dimension=boundary_dimension,
            inclusion_ref=inclusion_ref,
            inclusion_description=inclusion_description,
            source_label=source_label,
            scope_status=scope_status,
            schema_version=schema_version,
        )
        inclusion_ref_id = f"incl:{inclusion_hash[:16]}"

        if self.inclusion_hash not in ("", inclusion_hash):
            raise DelegationValidationError(
                "inclusion_hash does not match inclusion content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="inclusion_hash",
            )
        if self.inclusion_ref_id not in ("", inclusion_ref_id):
            raise DelegationValidationError(
                "inclusion_ref_id does not match inclusion content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="inclusion_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "scope_ref_id", scope_ref_id)
        object.__setattr__(self, "boundary_dimension", boundary_dimension)
        object.__setattr__(self, "inclusion_ref", inclusion_ref)
        object.__setattr__(self, "inclusion_description", inclusion_description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_status", scope_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "inclusion_hash", inclusion_hash)
        object.__setattr__(self, "inclusion_ref_id", inclusion_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundary_dimension": self.boundary_dimension.value,
            "delegation_ref_id": self.delegation_ref_id,
            "inclusion_description": self.inclusion_description,
            "inclusion_hash": self.inclusion_hash,
            "inclusion_ref": self.inclusion_ref,
            "inclusion_ref_id": self.inclusion_ref_id,
            "schema_version": self.schema_version,
            "scope_ref_id": self.scope_ref_id,
            "scope_status": self.scope_status.value,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeInclusionRef:
        validate_known_fields(data, INCLUSION_REF_KNOWN_FIELDS, label="delegation_scope_inclusion_ref")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            scope_ref_id=data["scope_ref_id"],
            boundary_dimension=data["boundary_dimension"],
            inclusion_ref=data["inclusion_ref"],
            inclusion_description=data.get("inclusion_description", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            scope_status=data.get("scope_status", DelegationScopeStatus.REFERENCE_ONLY),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_INCLUSION_REF_VERSION),
            inclusion_ref_id=data.get("inclusion_ref_id", ""),
            inclusion_hash=data.get("inclusion_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeExclusionRef
# ---------------------------------------------------------------------------


def compute_exclusion_ref_hash(
    *,
    delegation_ref_id: str,
    scope_ref_id: str,
    boundary_dimension: DelegationScopeDimension,
    exclusion_ref: str,
    exclusion_description: str,
    source_label: DelegationSourceLabel,
    scope_status: DelegationScopeStatus,
    schema_version: str = DELEGATION_SCOPE_EXCLUSION_REF_VERSION,
) -> str:
    return stable_hash({
        "boundary_dimension": boundary_dimension.value,
        "delegation_ref_id": delegation_ref_id,
        "exclusion_description": exclusion_description,
        "exclusion_ref": exclusion_ref,
        "schema_version": schema_version,
        "scope_ref_id": scope_ref_id,
        "scope_status": scope_status.value,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeExclusionRef:
    """Explicit declared exclusion metadata.

    DelegationScopeExclusionRef describes what is declared out of scope.
    It is not denial, not runtime block, not enforcement.
    """

    delegation_ref_id: str
    scope_ref_id: str
    boundary_dimension: DelegationScopeDimension
    exclusion_ref: str
    exclusion_description: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_SCOPE_EXCLUSION_REF_VERSION
    exclusion_ref_id: str = ""
    exclusion_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        scope_ref_id = _required_string(self.scope_ref_id, field_name="scope_ref_id")
        boundary_dimension = _parse_scope_dimension(self.boundary_dimension)
        exclusion_ref = _required_string(self.exclusion_ref, field_name="exclusion_ref")
        source_label = _parse_source_label(self.source_label)
        scope_status = _parse_scope_status(self.scope_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        exclusion_description = (
            self.exclusion_description.strip()
            if isinstance(self.exclusion_description, str)
            else ""
        )

        exclusion_hash = compute_exclusion_ref_hash(
            delegation_ref_id=delegation_ref_id,
            scope_ref_id=scope_ref_id,
            boundary_dimension=boundary_dimension,
            exclusion_ref=exclusion_ref,
            exclusion_description=exclusion_description,
            source_label=source_label,
            scope_status=scope_status,
            schema_version=schema_version,
        )
        exclusion_ref_id = f"excl:{exclusion_hash[:16]}"

        if self.exclusion_hash not in ("", exclusion_hash):
            raise DelegationValidationError(
                "exclusion_hash does not match exclusion content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="exclusion_hash",
            )
        if self.exclusion_ref_id not in ("", exclusion_ref_id):
            raise DelegationValidationError(
                "exclusion_ref_id does not match exclusion content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="exclusion_ref_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "scope_ref_id", scope_ref_id)
        object.__setattr__(self, "boundary_dimension", boundary_dimension)
        object.__setattr__(self, "exclusion_ref", exclusion_ref)
        object.__setattr__(self, "exclusion_description", exclusion_description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_status", scope_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "exclusion_hash", exclusion_hash)
        object.__setattr__(self, "exclusion_ref_id", exclusion_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundary_dimension": self.boundary_dimension.value,
            "delegation_ref_id": self.delegation_ref_id,
            "exclusion_description": self.exclusion_description,
            "exclusion_hash": self.exclusion_hash,
            "exclusion_ref": self.exclusion_ref,
            "exclusion_ref_id": self.exclusion_ref_id,
            "schema_version": self.schema_version,
            "scope_ref_id": self.scope_ref_id,
            "scope_status": self.scope_status.value,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeExclusionRef:
        validate_known_fields(data, EXCLUSION_REF_KNOWN_FIELDS, label="delegation_scope_exclusion_ref")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            scope_ref_id=data["scope_ref_id"],
            boundary_dimension=data["boundary_dimension"],
            exclusion_ref=data["exclusion_ref"],
            exclusion_description=data.get("exclusion_description", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            scope_status=data.get("scope_status", DelegationScopeStatus.REFERENCE_ONLY),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_EXCLUSION_REF_VERSION),
            exclusion_ref_id=data.get("exclusion_ref_id", ""),
            exclusion_hash=data.get("exclusion_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationBoundaryMatrixEntry
# ---------------------------------------------------------------------------


def compute_matrix_entry_hash(
    *,
    delegation_ref_id: str,
    dimension: DelegationScopeDimension,
    posture: DelegationBoundaryPosture,
    boundary_ref_id: str,
    reason_ref: str | None,
    source_label: DelegationSourceLabel,
    scope_status: DelegationScopeStatus,
    schema_version: str = DELEGATION_BOUNDARY_MATRIX_ENTRY_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "boundary_ref_id": boundary_ref_id,
        "delegation_ref_id": delegation_ref_id,
        "dimension": dimension.value,
        "posture": posture.value,
        "schema_version": schema_version,
        "scope_status": scope_status.value,
        "source_label": source_label.value,
    }
    if reason_ref is not None:
        payload["reason_ref"] = reason_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationBoundaryMatrixEntry:
    """Declarative boundary matrix row.

    DelegationBoundaryMatrixEntry is metadata.
    It is not runtime rule, not policy decision, not access-control rule.
    """

    delegation_ref_id: str
    dimension: DelegationScopeDimension
    posture: DelegationBoundaryPosture
    boundary_ref_id: str
    reason_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_BOUNDARY_MATRIX_ENTRY_VERSION
    entry_id: str = ""
    entry_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        dimension = _parse_scope_dimension(self.dimension)
        posture = _parse_boundary_posture(self.posture)
        boundary_ref_id = _required_string(
            self.boundary_ref_id, field_name="boundary_ref_id"
        )
        reason_ref = _optional_string(self.reason_ref)
        source_label = _parse_source_label(self.source_label)
        scope_status = _parse_scope_status(self.scope_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        entry_hash = compute_matrix_entry_hash(
            delegation_ref_id=delegation_ref_id,
            dimension=dimension,
            posture=posture,
            boundary_ref_id=boundary_ref_id,
            reason_ref=reason_ref,
            source_label=source_label,
            scope_status=scope_status,
            schema_version=schema_version,
        )
        entry_id = f"mxentry:{entry_hash[:16]}"

        if self.entry_hash not in ("", entry_hash):
            raise DelegationValidationError(
                "entry_hash does not match entry content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="entry_hash",
            )
        if self.entry_id not in ("", entry_id):
            raise DelegationValidationError(
                "entry_id does not match entry content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="entry_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "posture", posture)
        object.__setattr__(self, "boundary_ref_id", boundary_ref_id)
        object.__setattr__(self, "reason_ref", reason_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_status", scope_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "entry_hash", entry_hash)
        object.__setattr__(self, "entry_id", entry_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "boundary_ref_id": self.boundary_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "dimension": self.dimension.value,
            "entry_hash": self.entry_hash,
            "entry_id": self.entry_id,
            "posture": self.posture.value,
            "schema_version": self.schema_version,
            "scope_status": self.scope_status.value,
            "source_label": self.source_label.value,
        }
        if self.reason_ref is not None:
            payload["reason_ref"] = self.reason_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationBoundaryMatrixEntry:
        validate_known_fields(data, MATRIX_ENTRY_KNOWN_FIELDS, label="delegation_boundary_matrix_entry")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            dimension=data["dimension"],
            posture=data["posture"],
            boundary_ref_id=data["boundary_ref_id"],
            reason_ref=data.get("reason_ref"),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            scope_status=data.get("scope_status", DelegationScopeStatus.REFERENCE_ONLY),
            schema_version=data.get("schema_version", DELEGATION_BOUNDARY_MATRIX_ENTRY_VERSION),
            entry_id=data.get("entry_id", ""),
            entry_hash=data.get("entry_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationBoundaryMatrix
# ---------------------------------------------------------------------------


def compute_boundary_matrix_hash(
    *,
    delegation_ref_id: str,
    entries: tuple[DelegationBoundaryMatrixEntry, ...],
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_BOUNDARY_MATRIX_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "entries": [item.to_canonical_dict() for item in entries],
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationBoundaryMatrix:
    """Deterministic declarative boundary matrix.

    DelegationBoundaryMatrix is not enforcement matrix, not
    access-control matrix. It does not allow/block runtime behavior.
    """

    delegation_ref_id: str
    entries: tuple[DelegationBoundaryMatrixEntry, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_BOUNDARY_MATRIX_VERSION
    boundary_matrix_id: str = ""
    boundary_matrix_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        # deterministic ordering
        entries = tuple(sorted(
            [
                item if isinstance(item, DelegationBoundaryMatrixEntry)
                else DelegationBoundaryMatrixEntry.from_dict(item)
                for item in self.entries
            ],
            key=lambda e: (e.dimension.value, e.posture.value, e.entry_id),
        ))

        boundary_matrix_hash = compute_boundary_matrix_hash(
            delegation_ref_id=delegation_ref_id,
            entries=entries,
            source_label=source_label,
            schema_version=schema_version,
        )
        boundary_matrix_id = f"bmatrix:{boundary_matrix_hash[:16]}"

        if self.boundary_matrix_hash not in ("", boundary_matrix_hash):
            raise DelegationValidationError(
                "boundary_matrix_hash does not match matrix content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="boundary_matrix_hash",
            )
        if self.boundary_matrix_id not in ("", boundary_matrix_id):
            raise DelegationValidationError(
                "boundary_matrix_id does not match matrix content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="boundary_matrix_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "boundary_matrix_hash", boundary_matrix_hash)
        object.__setattr__(self, "boundary_matrix_id", boundary_matrix_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "boundary_matrix_hash": self.boundary_matrix_hash,
            "boundary_matrix_id": self.boundary_matrix_id,
            "delegation_ref_id": self.delegation_ref_id,
            "entries": [item.to_canonical_dict() for item in self.entries],
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationBoundaryMatrix:
        validate_known_fields(data, BOUNDARY_MATRIX_KNOWN_FIELDS, label="delegation_boundary_matrix")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            entries=tuple(data.get("entries", ())),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_BOUNDARY_MATRIX_VERSION),
            boundary_matrix_id=data.get("boundary_matrix_id", ""),
            boundary_matrix_hash=data.get("boundary_matrix_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeReadinessProfile
# ---------------------------------------------------------------------------


def compute_scope_readiness_hash(
    *,
    delegation_ref_id: str,
    has_scope_refs: bool,
    has_boundary_refs: bool,
    has_inclusion_refs: bool,
    has_exclusion_refs: bool,
    has_boundary_matrix: bool,
    has_tool_boundary: bool,
    has_data_boundary: bool,
    has_memory_boundary: bool,
    has_path_boundary: bool,
    has_runtime_boundary: bool,
    has_agent_boundary: bool,
    has_model_boundary: bool,
    has_network_boundary: bool,
    has_human_approval_boundary: bool,
    has_time_boundary: bool,
    has_risk_boundary: bool,
    missing_components: tuple[str, ...],
    enforcement_unavailable_reason: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_SCOPE_READINESS_PROFILE_VERSION,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "enforcement_unavailable_reason": enforcement_unavailable_reason,
        "has_agent_boundary": has_agent_boundary,
        "has_boundary_matrix": has_boundary_matrix,
        "has_boundary_refs": has_boundary_refs,
        "has_data_boundary": has_data_boundary,
        "has_exclusion_refs": has_exclusion_refs,
        "has_human_approval_boundary": has_human_approval_boundary,
        "has_inclusion_refs": has_inclusion_refs,
        "has_memory_boundary": has_memory_boundary,
        "has_model_boundary": has_model_boundary,
        "has_network_boundary": has_network_boundary,
        "has_path_boundary": has_path_boundary,
        "has_risk_boundary": has_risk_boundary,
        "has_runtime_boundary": has_runtime_boundary,
        "has_scope_refs": has_scope_refs,
        "has_time_boundary": has_time_boundary,
        "has_tool_boundary": has_tool_boundary,
        "missing_components": list(missing_components),
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeReadinessProfile:
    """Present/missing scope component profile.

    DelegationScopeReadinessProfile is presence/absence information.
    It is not enforcement readiness guarantee, not policy decision,
    not approval, not access control.
    """

    delegation_ref_id: str
    has_scope_refs: bool = False
    has_boundary_refs: bool = False
    has_inclusion_refs: bool = False
    has_exclusion_refs: bool = False
    has_boundary_matrix: bool = False
    has_tool_boundary: bool = False
    has_data_boundary: bool = False
    has_memory_boundary: bool = False
    has_path_boundary: bool = False
    has_runtime_boundary: bool = False
    has_agent_boundary: bool = False
    has_model_boundary: bool = False
    has_network_boundary: bool = False
    has_human_approval_boundary: bool = False
    has_time_boundary: bool = False
    has_risk_boundary: bool = False
    missing_components: tuple[str, ...] = ()
    enforcement_unavailable_reason: str = (
        "Enforcement is scheduled for later P1.8 tasks; not P1.8.7"
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_SCOPE_READINESS_PROFILE_VERSION
    scope_readiness_profile_id: str = ""
    scope_readiness_hash: str = ""

    def __post_init__(self) -> None:
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        enforcement_unavailable_reason = _required_string(
            self.enforcement_unavailable_reason,
            field_name="enforcement_unavailable_reason",
        )

        for attr_name in (
            "has_scope_refs", "has_boundary_refs", "has_inclusion_refs",
            "has_exclusion_refs", "has_boundary_matrix", "has_tool_boundary",
            "has_data_boundary", "has_memory_boundary", "has_path_boundary",
            "has_runtime_boundary", "has_agent_boundary", "has_model_boundary",
            "has_network_boundary", "has_human_approval_boundary",
            "has_time_boundary", "has_risk_boundary",
        ):
            value = getattr(self, attr_name)
            if not isinstance(value, bool):
                raise DelegationValidationError(
                    f"{attr_name} must be boolean",
                    code=DelegationErrorCode.VALIDATION_ERROR,
                    field=attr_name,
                )
                object.__setattr__(self, attr_name, value)

        missing_components = tuple(sorted(set(
            str(item) for item in self.missing_components
        )))

        scope_readiness_hash = compute_scope_readiness_hash(
            delegation_ref_id=delegation_ref_id,
            has_scope_refs=bool(getattr(self, "has_scope_refs")),
            has_boundary_refs=bool(getattr(self, "has_boundary_refs")),
            has_inclusion_refs=bool(getattr(self, "has_inclusion_refs")),
            has_exclusion_refs=bool(getattr(self, "has_exclusion_refs")),
            has_boundary_matrix=bool(getattr(self, "has_boundary_matrix")),
            has_tool_boundary=bool(getattr(self, "has_tool_boundary")),
            has_data_boundary=bool(getattr(self, "has_data_boundary")),
            has_memory_boundary=bool(getattr(self, "has_memory_boundary")),
            has_path_boundary=bool(getattr(self, "has_path_boundary")),
            has_runtime_boundary=bool(getattr(self, "has_runtime_boundary")),
            has_agent_boundary=bool(getattr(self, "has_agent_boundary")),
            has_model_boundary=bool(getattr(self, "has_model_boundary")),
            has_network_boundary=bool(getattr(self, "has_network_boundary")),
            has_human_approval_boundary=bool(getattr(self, "has_human_approval_boundary")),
            has_time_boundary=bool(getattr(self, "has_time_boundary")),
            has_risk_boundary=bool(getattr(self, "has_risk_boundary")),
            missing_components=missing_components,
            enforcement_unavailable_reason=enforcement_unavailable_reason,
            source_label=source_label,
            schema_version=schema_version,
        )
        scope_readiness_profile_id = f"srp:{scope_readiness_hash[:16]}"

        if self.scope_readiness_hash not in ("", scope_readiness_hash):
            raise DelegationValidationError(
                "scope_readiness_hash does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_readiness_hash",
            )
        if self.scope_readiness_profile_id not in ("", scope_readiness_profile_id):
            raise DelegationValidationError(
                "scope_readiness_profile_id does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_readiness_profile_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "enforcement_unavailable_reason", enforcement_unavailable_reason)
        object.__setattr__(self, "missing_components", missing_components)
        object.__setattr__(self, "scope_readiness_hash", scope_readiness_hash)
        object.__setattr__(self, "scope_readiness_profile_id", scope_readiness_profile_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "enforcement_unavailable_reason": self.enforcement_unavailable_reason,
            "has_agent_boundary": self.has_agent_boundary,
            "has_boundary_matrix": self.has_boundary_matrix,
            "has_boundary_refs": self.has_boundary_refs,
            "has_data_boundary": self.has_data_boundary,
            "has_exclusion_refs": self.has_exclusion_refs,
            "has_human_approval_boundary": self.has_human_approval_boundary,
            "has_inclusion_refs": self.has_inclusion_refs,
            "has_memory_boundary": self.has_memory_boundary,
            "has_model_boundary": self.has_model_boundary,
            "has_network_boundary": self.has_network_boundary,
            "has_path_boundary": self.has_path_boundary,
            "has_risk_boundary": self.has_risk_boundary,
            "has_runtime_boundary": self.has_runtime_boundary,
            "has_scope_refs": self.has_scope_refs,
            "has_time_boundary": self.has_time_boundary,
            "has_tool_boundary": self.has_tool_boundary,
            "missing_components": list(self.missing_components),
            "schema_version": self.schema_version,
            "scope_readiness_hash": self.scope_readiness_hash,
            "scope_readiness_profile_id": self.scope_readiness_profile_id,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeReadinessProfile:
        validate_known_fields(data, READINESS_PROFILE_KNOWN_FIELDS, label="delegation_scope_readiness_profile")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            has_scope_refs=data.get("has_scope_refs", False),
            has_boundary_refs=data.get("has_boundary_refs", False),
            has_inclusion_refs=data.get("has_inclusion_refs", False),
            has_exclusion_refs=data.get("has_exclusion_refs", False),
            has_boundary_matrix=data.get("has_boundary_matrix", False),
            has_tool_boundary=data.get("has_tool_boundary", False),
            has_data_boundary=data.get("has_data_boundary", False),
            has_memory_boundary=data.get("has_memory_boundary", False),
            has_path_boundary=data.get("has_path_boundary", False),
            has_runtime_boundary=data.get("has_runtime_boundary", False),
            has_agent_boundary=data.get("has_agent_boundary", False),
            has_model_boundary=data.get("has_model_boundary", False),
            has_network_boundary=data.get("has_network_boundary", False),
            has_human_approval_boundary=data.get("has_human_approval_boundary", False),
            has_time_boundary=data.get("has_time_boundary", False),
            has_risk_boundary=data.get("has_risk_boundary", False),
            missing_components=tuple(data.get("missing_components", ())),
            enforcement_unavailable_reason=data.get(
                "enforcement_unavailable_reason",
                "Enforcement is scheduled for later P1.8 tasks; not P1.8.7",
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_READINESS_PROFILE_VERSION),
            scope_readiness_profile_id=data.get("scope_readiness_profile_id", ""),
            scope_readiness_hash=data.get("scope_readiness_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeEnvelope
# ---------------------------------------------------------------------------


def compute_scope_envelope_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_refs: tuple[DelegationScopeRef, ...],
    boundary_refs: tuple[DelegationBoundaryRef, ...],
    inclusion_refs: tuple[DelegationScopeInclusionRef, ...],
    exclusion_refs: tuple[DelegationScopeExclusionRef, ...],
    boundary_matrix_hash: str,
    scope_readiness_hash: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_SCOPE_ENVELOPE_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "boundary_matrix_hash": boundary_matrix_hash,
        "boundary_refs": [item.to_canonical_dict() for item in boundary_refs],
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "exclusion_refs": [item.to_canonical_dict() for item in exclusion_refs],
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "inclusion_refs": [item.to_canonical_dict() for item in inclusion_refs],
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_readiness_hash": scope_readiness_hash,
        "scope_refs": [item.to_canonical_dict() for item in scope_refs],
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeEnvelope:
    """Deterministic packet of scope, boundary, matrix, readiness, and
    context hashes for one delegation context.

    DelegationScopeEnvelope is a reference packet.
    It is not permission grant, not runtime access control, not boundary
    enforcement, not TRACE_VERIFIED.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    boundary_matrix_hash: str
    scope_readiness_hash: str
    scope_refs: tuple[DelegationScopeRef, ...] = ()
    boundary_refs: tuple[DelegationBoundaryRef, ...] = ()
    inclusion_refs: tuple[DelegationScopeInclusionRef, ...] = ()
    exclusion_refs: tuple[DelegationScopeExclusionRef, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_SCOPE_ENVELOPE_VERSION
    scope_envelope_id: str = ""
    scope_envelope_hash: str = ""

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
        boundary_matrix_hash = _required_string(
            self.boundary_matrix_hash, field_name="boundary_matrix_hash"
        )
        scope_readiness_hash = _required_string(
            self.scope_readiness_hash, field_name="scope_readiness_hash"
        )
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        # deterministic ordering by ref_id
        scope_refs = tuple(sorted(
            [
                item if isinstance(item, DelegationScopeRef)
                else DelegationScopeRef.from_dict(item)
                for item in self.scope_refs
            ],
            key=lambda r: r.scope_ref_id,
        ))
        boundary_refs = tuple(sorted(
            [
                item if isinstance(item, DelegationBoundaryRef)
                else DelegationBoundaryRef.from_dict(item)
                for item in self.boundary_refs
            ],
            key=lambda r: r.boundary_ref_id,
        ))
        inclusion_refs = tuple(sorted(
            [
                item if isinstance(item, DelegationScopeInclusionRef)
                else DelegationScopeInclusionRef.from_dict(item)
                for item in self.inclusion_refs
            ],
            key=lambda r: r.inclusion_ref_id,
        ))
        exclusion_refs = tuple(sorted(
            [
                item if isinstance(item, DelegationScopeExclusionRef)
                else DelegationScopeExclusionRef.from_dict(item)
                for item in self.exclusion_refs
            ],
            key=lambda r: r.exclusion_ref_id,
        ))

        scope_envelope_hash = compute_scope_envelope_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
            scope_refs=scope_refs,
            boundary_refs=boundary_refs,
            inclusion_refs=inclusion_refs,
            exclusion_refs=exclusion_refs,
            boundary_matrix_hash=boundary_matrix_hash,
            scope_readiness_hash=scope_readiness_hash,
            source_label=source_label,
            schema_version=schema_version,
        )
        scope_envelope_id = f"senv:{scope_envelope_hash[:16]}"

        if self.scope_envelope_hash not in ("", scope_envelope_hash):
            raise DelegationValidationError(
                "scope_envelope_hash does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_envelope_hash",
            )
        if self.scope_envelope_id not in ("", scope_envelope_id):
            raise DelegationValidationError(
                "scope_envelope_id does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_envelope_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "authority_binding_set_hash", authority_binding_set_hash)
        object.__setattr__(self, "non_repudiation_binding_set_hash", non_repudiation_binding_set_hash)
        object.__setattr__(self, "identity_mesh_binding_set_hash", identity_mesh_binding_set_hash)
        object.__setattr__(self, "boundary_matrix_hash", boundary_matrix_hash)
        object.__setattr__(self, "scope_readiness_hash", scope_readiness_hash)
        object.__setattr__(self, "scope_refs", scope_refs)
        object.__setattr__(self, "boundary_refs", boundary_refs)
        object.__setattr__(self, "inclusion_refs", inclusion_refs)
        object.__setattr__(self, "exclusion_refs", exclusion_refs)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "scope_envelope_hash", scope_envelope_hash)
        object.__setattr__(self, "scope_envelope_id", scope_envelope_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "boundary_matrix_hash": self.boundary_matrix_hash,
            "boundary_refs": [item.to_canonical_dict() for item in self.boundary_refs],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "exclusion_refs": [item.to_canonical_dict() for item in self.exclusion_refs],
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "inclusion_refs": [item.to_canonical_dict() for item in self.inclusion_refs],
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_envelope_hash": self.scope_envelope_hash,
            "scope_envelope_id": self.scope_envelope_id,
            "scope_readiness_hash": self.scope_readiness_hash,
            "scope_refs": [item.to_canonical_dict() for item in self.scope_refs],
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeEnvelope:
        validate_known_fields(data, SCOPE_ENVELOPE_KNOWN_FIELDS, label="delegation_scope_envelope")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data["non_repudiation_binding_set_hash"],
            identity_mesh_binding_set_hash=data["identity_mesh_binding_set_hash"],
            boundary_matrix_hash=data["boundary_matrix_hash"],
            scope_readiness_hash=data["scope_readiness_hash"],
            scope_refs=tuple(data.get("scope_refs", ())),
            boundary_refs=tuple(data.get("boundary_refs", ())),
            inclusion_refs=tuple(data.get("inclusion_refs", ())),
            exclusion_refs=tuple(data.get("exclusion_refs", ())),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_ENVELOPE_VERSION),
            scope_envelope_id=data.get("scope_envelope_id", ""),
            scope_envelope_hash=data.get("scope_envelope_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeBinding
# ---------------------------------------------------------------------------


def compute_scope_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_envelope_hash: str,
    boundary_matrix_hash: str,
    scope_readiness_hash: str,
    source_label: DelegationSourceLabel,
    scope_status: DelegationScopeStatus,
    schema_version: str = DELEGATION_SCOPE_BINDING_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "boundary_matrix_hash": boundary_matrix_hash,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "scope_envelope_hash": scope_envelope_hash,
        "scope_readiness_hash": scope_readiness_hash,
        "scope_status": scope_status.value,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeBinding:
    """Binding between scope envelope and delegation context.

    DelegationScopeBinding binds scope/boundary metadata.
    It is not permission, not access control, not enforcement, not
    policy decision, not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    scope_envelope_hash: str
    boundary_matrix_hash: str
    scope_readiness_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_SCOPE_BINDING_VERSION
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
        scope_envelope_hash = _required_string(
            self.scope_envelope_hash, field_name="scope_envelope_hash"
        )
        boundary_matrix_hash = _required_string(
            self.boundary_matrix_hash, field_name="boundary_matrix_hash"
        )
        scope_readiness_hash = _required_string(
            self.scope_readiness_hash, field_name="scope_readiness_hash"
        )
        source_label = _parse_source_label(self.source_label)
        scope_status = _parse_scope_status(self.scope_status)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        binding_hash = compute_scope_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
            scope_envelope_hash=scope_envelope_hash,
            boundary_matrix_hash=boundary_matrix_hash,
            scope_readiness_hash=scope_readiness_hash,
            source_label=source_label,
            scope_status=scope_status,
            schema_version=schema_version,
        )
        binding_id = f"sbind:{binding_hash[:16]}"

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
        object.__setattr__(self, "non_repudiation_binding_set_hash", non_repudiation_binding_set_hash)
        object.__setattr__(self, "identity_mesh_binding_set_hash", identity_mesh_binding_set_hash)
        object.__setattr__(self, "scope_envelope_hash", scope_envelope_hash)
        object.__setattr__(self, "boundary_matrix_hash", boundary_matrix_hash)
        object.__setattr__(self, "scope_readiness_hash", scope_readiness_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "scope_status", scope_status)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "boundary_matrix_hash": self.boundary_matrix_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_envelope_hash": self.scope_envelope_hash,
            "scope_readiness_hash": self.scope_readiness_hash,
            "scope_status": self.scope_status.value,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeBinding:
        validate_known_fields(data, SCOPE_BINDING_KNOWN_FIELDS, label="delegation_scope_binding")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data["non_repudiation_binding_set_hash"],
            identity_mesh_binding_set_hash=data["identity_mesh_binding_set_hash"],
            scope_envelope_hash=data["scope_envelope_hash"],
            boundary_matrix_hash=data["boundary_matrix_hash"],
            scope_readiness_hash=data["scope_readiness_hash"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            scope_status=data.get("scope_status", DelegationScopeStatus.REFERENCE_ONLY),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_BINDING_VERSION),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeBindingSet
# ---------------------------------------------------------------------------


def compute_scope_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    bindings: tuple[DelegationScopeBinding, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationScopeSideEffects,
    schema_version: str = DELEGATION_SCOPE_BINDING_SET_VERSION,
) -> str:
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "bindings": [item.to_canonical_dict() for item in bindings],
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationScopeBindingSet:
    """Collection of scope bindings for one delegation.

    DelegationScopeBindingSet describes scope/boundary hooks.
    It does not grant access, enforce boundaries, or write
    Ledger/global trace.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_binding_set_hash: str
    bindings: tuple[DelegationScopeBinding, ...] = ()
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    side_effects: DelegationScopeSideEffects = field(
        default_factory=lambda: DelegationScopeSideEffects()
    )
    schema_version: str = DELEGATION_SCOPE_BINDING_SET_VERSION
    scope_binding_set_id: str = ""
    scope_binding_set_hash: str = ""

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
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")

        bindings = tuple(sorted(
            [
                item if isinstance(item, DelegationScopeBinding)
                else DelegationScopeBinding.from_dict(item)
                for item in self.bindings
            ],
            key=lambda b: b.binding_id,
        ))

        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationScopeSideEffects)
            else DelegationScopeSideEffects.from_dict(self.side_effects)
        )

        scope_binding_set_hash = compute_scope_binding_set_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
            bindings=bindings,
            source_label=source_label,
            side_effects=side_effects,
            schema_version=schema_version,
        )
        scope_binding_set_id = f"sbinds:{scope_binding_set_hash[:16]}"

        if self.scope_binding_set_hash not in ("", scope_binding_set_hash):
            raise DelegationValidationError(
                "scope_binding_set_hash does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_binding_set_hash",
            )
        if self.scope_binding_set_id not in ("", scope_binding_set_id):
            raise DelegationValidationError(
                "scope_binding_set_id does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="scope_binding_set_id",
            )

        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "authority_binding_set_hash", authority_binding_set_hash)
        object.__setattr__(self, "non_repudiation_binding_set_hash", non_repudiation_binding_set_hash)
        object.__setattr__(self, "identity_mesh_binding_set_hash", identity_mesh_binding_set_hash)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "scope_binding_set_hash", scope_binding_set_hash)
        object.__setattr__(self, "scope_binding_set_id", scope_binding_set_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "bindings": [item.to_canonical_dict() for item in self.bindings],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": self.identity_mesh_binding_set_hash,
            "non_repudiation_binding_set_hash": self.non_repudiation_binding_set_hash,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "scope_binding_set_hash": self.scope_binding_set_hash,
            "scope_binding_set_id": self.scope_binding_set_id,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeBindingSet:
        validate_known_fields(data, SCOPE_BINDING_SET_KNOWN_FIELDS, label="delegation_scope_binding_set")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data["non_repudiation_binding_set_hash"],
            identity_mesh_binding_set_hash=data["identity_mesh_binding_set_hash"],
            bindings=tuple(data.get("bindings", ())),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            side_effects=data.get("side_effects", DelegationScopeSideEffects()),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_BINDING_SET_VERSION),
            scope_binding_set_id=data.get("scope_binding_set_id", ""),
            scope_binding_set_hash=data.get("scope_binding_set_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationScopeSideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationScopeSideEffects:
    """Hard proof that P1.8.7 is non-permissioning, non-enforcing, non-mutating.

    All fields default to false.
    """

    permission_granted: bool = False
    access_granted: bool = False
    boundary_enforced: bool = False
    runtime_blocked: bool = False
    tool_permission_changed: bool = False
    data_access_changed: bool = False
    memory_access_changed: bool = False
    path_authorized: bool = False
    network_access_changed: bool = False
    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if not isinstance(value, bool):
                raise DelegationValidationError(
                    f"{item.name} must be boolean",
                    code=DelegationErrorCode.VALIDATION_ERROR,
                    field=item.name,
                )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "access_granted": self.access_granted,
            "approval_created": self.approval_created,
            "boundary_enforced": self.boundary_enforced,
            "custos_called": self.custos_called,
            "data_access_changed": self.data_access_changed,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "memory_access_changed": self.memory_access_changed,
            "network_access_changed": self.network_access_changed,
            "path_authorized": self.path_authorized,
            "permission_granted": self.permission_granted,
            "policy_called": self.policy_called,
            "runtime_blocked": self.runtime_blocked,
            "runtime_mutated": self.runtime_mutated,
            "tool_permission_changed": self.tool_permission_changed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeSideEffects:
        validate_known_fields(
            data, SCOPE_SIDE_EFFECTS_KNOWN_FIELDS, label="delegation_scope_side_effects"
        )
        return cls(
            **{name: data.get(name, False) for name in SCOPE_SIDE_EFFECTS_KNOWN_FIELDS}
        )


# ---------------------------------------------------------------------------
# DelegationScopeStatusReport
# ---------------------------------------------------------------------------


def compute_scope_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationScopeSideEffects,
) -> str:
    return stable_hash({
        "available_contracts": dict(
            sorted(available_contracts.items(), key=lambda item: item[0])
        ),
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "status_label": status_label.value,
        "unavailable_bindings": dict(
            sorted(unavailable_bindings.items(), key=lambda item: item[0])
        ),
    })


@dataclass(frozen=True)
class DelegationScopeStatusReport:
    """Declares scope/boundary module readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationScopeSideEffects = field(
        default_factory=DelegationScopeSideEffects,
    )
    schema_version: str = DELEGATION_SCOPE_STATUS_REPORT_VERSION
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
            if isinstance(self.side_effects, DelegationScopeSideEffects)
            else DelegationScopeSideEffects.from_dict(self.side_effects)
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_scope_status_report_hash(
            schema_version=schema_version,
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
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationScopeStatusReport:
        validate_known_fields(
            data,
            SCOPE_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_scope_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get("side_effects", DelegationScopeSideEffects()),
            schema_version=data.get("schema_version", DELEGATION_SCOPE_STATUS_REPORT_VERSION),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_scope_ref(
    scope_kind: DelegationScopeKind | str,
    scope_ref: str,
    delegation_ref_id: str,
    *,
    scope_description: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY,
) -> DelegationScopeRef:
    """Build reference-only scope ref without granting permission or
    authorizing access."""
    return DelegationScopeRef(
        scope_kind=scope_kind,
        scope_ref=scope_ref,
        delegation_ref_id=delegation_ref_id,
        scope_description=scope_description,
        source_label=source_label,
        scope_status=scope_status,
    )


def build_delegation_boundary_ref(
    boundary_kind: DelegationBoundaryKind | str,
    boundary_dimension: DelegationScopeDimension | str,
    boundary_ref: str,
    delegation_ref_id: str,
    *,
    boundary_description: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY,
) -> DelegationBoundaryRef:
    """Build reference-only boundary ref without enforcing boundaries or
    granting/denying access."""
    return DelegationBoundaryRef(
        boundary_kind=boundary_kind,
        boundary_dimension=boundary_dimension,
        boundary_ref=boundary_ref,
        delegation_ref_id=delegation_ref_id,
        boundary_description=boundary_description,
        source_label=source_label,
        scope_status=scope_status,
    )


def build_delegation_scope_inclusion_ref(
    delegation_ref_id: str,
    scope_ref_id: str,
    boundary_dimension: DelegationScopeDimension | str,
    inclusion_ref: str,
    *,
    inclusion_description: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationScopeInclusionRef:
    """Build declared inclusion ref without granting permission."""
    return DelegationScopeInclusionRef(
        delegation_ref_id=delegation_ref_id,
        scope_ref_id=scope_ref_id,
        boundary_dimension=boundary_dimension,
        inclusion_ref=inclusion_ref,
        inclusion_description=inclusion_description,
        source_label=source_label,
    )


def build_delegation_scope_exclusion_ref(
    delegation_ref_id: str,
    scope_ref_id: str,
    boundary_dimension: DelegationScopeDimension | str,
    exclusion_ref: str,
    *,
    exclusion_description: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationScopeExclusionRef:
    """Build declared exclusion ref without denying or blocking runtime."""
    return DelegationScopeExclusionRef(
        delegation_ref_id=delegation_ref_id,
        scope_ref_id=scope_ref_id,
        boundary_dimension=boundary_dimension,
        exclusion_ref=exclusion_ref,
        exclusion_description=exclusion_description,
        source_label=source_label,
    )


def build_delegation_boundary_matrix_entry(
    delegation_ref_id: str,
    dimension: DelegationScopeDimension | str,
    posture: DelegationBoundaryPosture | str,
    boundary_ref_id: str,
    *,
    reason_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationBoundaryMatrixEntry:
    """Build declarative boundary matrix entry without creating runtime rule
    or access-control rule."""
    return DelegationBoundaryMatrixEntry(
        delegation_ref_id=delegation_ref_id,
        dimension=dimension,
        posture=posture,
        boundary_ref_id=boundary_ref_id,
        reason_ref=reason_ref,
        source_label=source_label,
    )


def build_delegation_boundary_matrix(
    delegation_ref_id: str,
    entries: Sequence[DelegationBoundaryMatrixEntry | Mapping[str, Any]] | None = None,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationBoundaryMatrix:
    """Build declarative boundary matrix without creating enforcement matrix
    or access-control matrix."""
    return DelegationBoundaryMatrix(
        delegation_ref_id=delegation_ref_id,
        entries=tuple(entries) if entries is not None else (),
        source_label=source_label,
    )


def build_delegation_scope_readiness_profile(
    delegation_ref_id: str,
    *,
    has_scope_refs: bool = False,
    has_boundary_refs: bool = False,
    has_inclusion_refs: bool = False,
    has_exclusion_refs: bool = False,
    has_boundary_matrix: bool = False,
    has_tool_boundary: bool = False,
    has_data_boundary: bool = False,
    has_memory_boundary: bool = False,
    has_path_boundary: bool = False,
    has_runtime_boundary: bool = False,
    has_agent_boundary: bool = False,
    has_model_boundary: bool = False,
    has_network_boundary: bool = False,
    has_human_approval_boundary: bool = False,
    has_time_boundary: bool = False,
    has_risk_boundary: bool = False,
    missing_components: Sequence[str] | None = None,
    enforcement_unavailable_reason: str = (
        "Enforcement is scheduled for later P1.8 tasks; not P1.8.7"
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationScopeReadinessProfile:
    """Build presence/absence readiness profile without enforcement guarantee."""
    return DelegationScopeReadinessProfile(
        delegation_ref_id=delegation_ref_id,
        has_scope_refs=has_scope_refs,
        has_boundary_refs=has_boundary_refs,
        has_inclusion_refs=has_inclusion_refs,
        has_exclusion_refs=has_exclusion_refs,
        has_boundary_matrix=has_boundary_matrix,
        has_tool_boundary=has_tool_boundary,
        has_data_boundary=has_data_boundary,
        has_memory_boundary=has_memory_boundary,
        has_path_boundary=has_path_boundary,
        has_runtime_boundary=has_runtime_boundary,
        has_agent_boundary=has_agent_boundary,
        has_model_boundary=has_model_boundary,
        has_network_boundary=has_network_boundary,
        has_human_approval_boundary=has_human_approval_boundary,
        has_time_boundary=has_time_boundary,
        has_risk_boundary=has_risk_boundary,
        missing_components=tuple(missing_components) if missing_components is not None else (),
        enforcement_unavailable_reason=enforcement_unavailable_reason,
        source_label=source_label,
    )


def build_delegation_scope_envelope(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    boundary_matrix_hash: str,
    scope_readiness_hash: str,
    *,
    scope_refs: Sequence[DelegationScopeRef | Mapping[str, Any]] | None = None,
    boundary_refs: Sequence[DelegationBoundaryRef | Mapping[str, Any]] | None = None,
    inclusion_refs: Sequence[DelegationScopeInclusionRef | Mapping[str, Any]] | None = None,
    exclusion_refs: Sequence[DelegationScopeExclusionRef | Mapping[str, Any]] | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationScopeEnvelope:
    """Build scope envelope reference packet without granting permission or
    enforcing boundaries."""
    return DelegationScopeEnvelope(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        boundary_matrix_hash=boundary_matrix_hash,
        scope_readiness_hash=scope_readiness_hash,
        scope_refs=tuple(scope_refs) if scope_refs is not None else (),
        boundary_refs=tuple(boundary_refs) if boundary_refs is not None else (),
        inclusion_refs=tuple(inclusion_refs) if inclusion_refs is not None else (),
        exclusion_refs=tuple(exclusion_refs) if exclusion_refs is not None else (),
        source_label=source_label,
    )


def build_delegation_scope_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_envelope_hash: str,
    boundary_matrix_hash: str,
    scope_readiness_hash: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    scope_status: DelegationScopeStatus = DelegationScopeStatus.REFERENCE_ONLY,
) -> DelegationScopeBinding:
    """Build scope binding without granting permission, enforcing boundaries,
    or authorizing access."""
    return DelegationScopeBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_envelope_hash=scope_envelope_hash,
        boundary_matrix_hash=boundary_matrix_hash,
        scope_readiness_hash=scope_readiness_hash,
        source_label=source_label,
        scope_status=scope_status,
    )


def build_delegation_scope_binding_set(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    *,
    bindings: Sequence[DelegationScopeBinding | Mapping[str, Any]] | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    side_effects: DelegationScopeSideEffects | None = None,
) -> DelegationScopeBindingSet:
    """Build scope binding set without granting access, enforcing boundaries,
    or writing Ledger/global trace."""
    return DelegationScopeBindingSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        bindings=tuple(bindings) if bindings is not None else (),
        source_label=source_label,
        side_effects=side_effects or DelegationScopeSideEffects(),
    )


def _default_scope_available_contracts() -> dict[str, str]:
    return {
        "DelegationScopeRef": DelegationSourceLabel.LIVE.value,
        "DelegationBoundaryRef": DelegationSourceLabel.LIVE.value,
        "DelegationScopeInclusionRef": DelegationSourceLabel.LIVE.value,
        "DelegationScopeExclusionRef": DelegationSourceLabel.LIVE.value,
        "DelegationBoundaryMatrixEntry": DelegationSourceLabel.LIVE.value,
        "DelegationBoundaryMatrix": DelegationSourceLabel.LIVE.value,
        "DelegationScopeReadinessProfile": DelegationSourceLabel.LIVE.value,
        "DelegationScopeEnvelope": DelegationSourceLabel.LIVE.value,
        "DelegationScopeBinding": DelegationSourceLabel.LIVE.value,
        "DelegationScopeBindingSet": DelegationSourceLabel.LIVE.value,
        "DelegationScopeSideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationScopeStatusReport": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_scope_status_report() -> DelegationScopeStatusReport:
    """Return honest P1.8.7 scope/boundary status report (non-enforcing)."""
    return DelegationScopeStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_scope_available_contracts(),
        unavailable_bindings=DELEGATION_SCOPE_UNAVAILABLE_BINDINGS,
        side_effects=DelegationScopeSideEffects(),
    )


def serialize_delegation_scope_envelope(envelope: DelegationScopeEnvelope) -> str:
    """Serialize DelegationScopeEnvelope to deterministic canonical JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_scope_binding_set(binding_set: DelegationScopeBindingSet) -> str:
    """Serialize DelegationScopeBindingSet to deterministic canonical JSON."""
    return to_canonical_json(binding_set)


def hash_delegation_scope_ref(ref: DelegationScopeRef) -> str:
    """Return stable scope_hash for DelegationScopeRef content."""
    return ref.scope_hash


def hash_delegation_boundary_ref(ref: DelegationBoundaryRef) -> str:
    """Return stable boundary_hash for DelegationBoundaryRef content."""
    return ref.boundary_hash


def hash_delegation_scope_inclusion_ref(ref: DelegationScopeInclusionRef) -> str:
    """Return stable inclusion_hash for DelegationScopeInclusionRef content."""
    return ref.inclusion_hash


def hash_delegation_scope_exclusion_ref(ref: DelegationScopeExclusionRef) -> str:
    """Return stable exclusion_hash for DelegationScopeExclusionRef content."""
    return ref.exclusion_hash


def hash_delegation_boundary_matrix(matrix: DelegationBoundaryMatrix) -> str:
    """Return stable boundary_matrix_hash for DelegationBoundaryMatrix content."""
    return matrix.boundary_matrix_hash


def hash_delegation_scope_readiness_profile(
    profile: DelegationScopeReadinessProfile,
) -> str:
    """Return stable scope_readiness_hash for DelegationScopeReadinessProfile content."""
    return profile.scope_readiness_hash


def hash_delegation_scope_envelope(envelope: DelegationScopeEnvelope) -> str:
    """Return stable scope_envelope_hash for DelegationScopeEnvelope content."""
    return envelope.scope_envelope_hash


def hash_delegation_scope_binding_set(
    binding_set: DelegationScopeBindingSet,
) -> str:
    """Return stable scope_binding_set_hash for DelegationScopeBindingSet content."""
    return binding_set.scope_binding_set_hash
