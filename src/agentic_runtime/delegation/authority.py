"""Delegation authority-reference binding (P1.8.4).

Reference-only authority context binding for delegation authority context.
Binds authority references to DelegationRef / DelegationIdentity /
DelegationRoleBindingSet / DelegationConstraintSet without granting
authority, verifying authority, creating approval, calling policy/Custos,
enforcing constraints, executing runtime actions, writing trace, or
writing Ledger.

Architectural law:
  - AuthorityRef exists ≠ authority granted.
  - Authority basis exists ≠ authority verified.
  - Policy context ref exists ≠ policy/Custos decision.
  - Path authority ref exists ≠ path authorized.
  - Operator declaration exists ≠ legal or operational authority proven.
  - Authority binding exists ≠ approval created.
  - Authority hash exists ≠ TRACE_VERIFIED.
  - Authority model exists ≠ authority resolver exists.
  - Authority binding set exists ≠ permission granted.
  - Constraint context ref exists ≠ constraint enforced.
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

DELEGATION_AUTHORITY_TASK_ID = "P1.8.4"
DELEGATION_AUTHORITY_REF_VERSION = "delegation_authority_ref.v1"
DELEGATION_AUTHORITY_BINDING_VERSION = "delegation_authority_binding.v1"
DELEGATION_AUTHORITY_BINDING_SET_VERSION = "delegation_authority_binding_set.v1"
DELEGATION_AUTHORITY_SIDE_EFFECTS_VERSION = "delegation_authority_side_effects.v1"
DELEGATION_AUTHORITY_STATUS_REPORT_VERSION = "delegation_authority_status_report.v1"

DELEGATION_AUTHORITY_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Approval Activation": (
        "Approval activation is not available in P1.8.4 authority-reference "
        "binding"
    ),
    "Authority Grant": (
        "Authority grant scheduled for later P1.8 tasks; not P1.8.4"
    ),
    "Authority Resolver": (
        "Authority resolver scheduled for later P1.8 tasks; not P1.8.4"
    ),
    "Authority Verifier": (
        "Authority verifier scheduled for later P1.8 tasks; not P1.8.4"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.4"
    ),
    "Constraint Enforcement": (
        "Constraint enforcement scheduled for later P1.8 tasks; "
        "not P1.8.4"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.4 "
        "authority-reference binding"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.4 authority-reference binding"
    ),
    "Non-Repudiation Verifier": (
        "Non-repudiation verifier scheduled for later P1.8 tasks; "
        "not P1.8.4"
    ),
    "Path Authorization": (
        "Path authorization scheduled for later P1.8 tasks; not P1.8.4"
    ),
    "Permission Grant": (
        "Permission grant is not available in P1.8.4; authority references "
        "are reference-only"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision scheduled for later P1.8 tasks; not P1.8.4"
    ),
    "Policy/Custos Enforcement": (
        "Policy/Custos enforcement scheduled for later P1.8 tasks; "
        "not P1.8.4"
    ),
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.4; "
        "authority-reference schema only"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.4"
    ),
    "Violation/Drift Detector": (
        "Violation/drift detector scheduled for later P1.8 tasks; "
        "not P1.8.4"
    ),
}

AUTHORITY_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "authority_ref_id",
    "delegation_ref_id",
    "authority_kind",
    "authority_basis",
    "policy_context_ref",
    "path_authority_ref",
    "constraint_context_ref",
    "source_label",
    "authority_status",
    "authority_ref_hash",
})

AUTHORITY_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_ref_id",
    "authority_ref_hash",
    "source_label",
    "binding_hash",
})

AUTHORITY_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "authority_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_refs",
    "bindings",
    "source_label",
    "authority_binding_set_hash",
    "side_effects",
})

AUTHORITY_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "custos_called",
    "approval_created",
    "permission_granted",
    "authority_verified",
    "path_authorized",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "constraint_enforced",
    "delegation_executed",
})

AUTHORITY_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationAuthorityRefKind(str, Enum):
    """Classifies the referenced authority context.

    AuthorityRef kind classifies the referenced authority context.
    It does not grant, verify, approve, resolve, enforce, or execute
    authority.
    """

    OPERATOR_DECLARED = "OPERATOR_DECLARED"
    POLICY_CONTEXT_REFERENCED = "POLICY_CONTEXT_REFERENCED"
    PATH_AUTHORITY_REFERENCED = "PATH_AUTHORITY_REFERENCED"
    SYSTEM_DECLARED = "SYSTEM_DECLARED"
    CONSTRAINT_CONTEXT_REFERENCED = "CONSTRAINT_CONTEXT_REFERENCED"
    UNKNOWN = "UNKNOWN"


class DelegationAuthorityRefStatus(str, Enum):
    """Declared authority reference availability.

    REFERENCE_ONLY means authority context is reference-only.
    DECLARED means authority context was declared as metadata.
    Neither means authority is granted, verified, approved, enforced,
    or executed.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parsers
# ---------------------------------------------------------------------------


def _parse_authority_ref_kind(
    value: DelegationAuthorityRefKind | str,
) -> DelegationAuthorityRefKind:
    if isinstance(value, DelegationAuthorityRefKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationAuthorityRefKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid authority_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="authority_kind",
            ) from exc
    raise DelegationError(
        "authority_kind must be a string or DelegationAuthorityRefKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="authority_kind",
    )


def _parse_authority_ref_status(
    value: DelegationAuthorityRefStatus | str,
) -> DelegationAuthorityRefStatus:
    if isinstance(value, DelegationAuthorityRefStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationAuthorityRefStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid authority_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="authority_status",
            ) from exc
    raise DelegationError(
        "authority_status must be a string or DelegationAuthorityRefStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="authority_status",
    )


# ---------------------------------------------------------------------------
# DelegationAuthorityRef
# ---------------------------------------------------------------------------


def compute_authority_ref_hash(
    *,
    delegation_ref_id: str,
    authority_kind: DelegationAuthorityRefKind,
    authority_basis: str,
    policy_context_ref: str | None,
    path_authority_ref: str | None,
    constraint_context_ref: str | None,
    source_label: DelegationSourceLabel,
    authority_status: DelegationAuthorityRefStatus,
    schema_version: str = DELEGATION_AUTHORITY_REF_VERSION,
) -> str:
    """Deterministic hash of authority reference content."""
    payload: dict[str, Any] = {
        "authority_basis": authority_basis,
        "authority_kind": authority_kind.value,
        "authority_status": authority_status.value,
        "delegation_ref_id": delegation_ref_id,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if policy_context_ref is not None:
        payload["policy_context_ref"] = policy_context_ref
    if path_authority_ref is not None:
        payload["path_authority_ref"] = path_authority_ref
    if constraint_context_ref is not None:
        payload["constraint_context_ref"] = constraint_context_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationAuthorityRef:
    """One declared/reference-only authority context object.

    DelegationAuthorityRef describes referenced authority context.
    It does not grant authority.
    It does not verify authority.
    It does not create approval.
    It does not call policy/Custos.
    It does not authorize paths.
    It does not mutate runtime, tools, scheduler, data access, trace,
    or Ledger.
    """

    delegation_ref_id: str
    authority_kind: DelegationAuthorityRefKind
    authority_basis: str
    policy_context_ref: str | None = None
    path_authority_ref: str | None = None
    constraint_context_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    authority_status: DelegationAuthorityRefStatus = (
        DelegationAuthorityRefStatus.REFERENCE_ONLY
    )
    schema_version: str = DELEGATION_AUTHORITY_REF_VERSION
    authority_ref_id: str = ""
    authority_ref_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        authority_kind = _parse_authority_ref_kind(self.authority_kind)
        authority_basis = _required_string(
            self.authority_basis, field_name="authority_basis"
        )
        policy_context_ref = _optional_string(self.policy_context_ref)
        path_authority_ref = _optional_string(self.path_authority_ref)
        constraint_context_ref = _optional_string(self.constraint_context_ref)
        source_label = _parse_source_label(self.source_label)
        authority_status = _parse_authority_ref_status(self.authority_status)

        authority_ref_hash = compute_authority_ref_hash(
            delegation_ref_id=delegation_ref_id,
            authority_kind=authority_kind,
            authority_basis=authority_basis,
            policy_context_ref=policy_context_ref,
            path_authority_ref=path_authority_ref,
            constraint_context_ref=constraint_context_ref,
            source_label=source_label,
            authority_status=authority_status,
            schema_version=schema_version,
        )
        authority_ref_id = f"authref:{authority_ref_hash[:16]}"

        if self.authority_ref_hash not in ("", authority_ref_hash):
            raise DelegationValidationError(
                "authority_ref_hash does not match authority ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="authority_ref_hash",
            )
        if self.authority_ref_id not in ("", authority_ref_id):
            raise DelegationValidationError(
                "authority_ref_id does not match authority ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="authority_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "authority_kind", authority_kind)
        object.__setattr__(self, "authority_basis", authority_basis)
        object.__setattr__(self, "policy_context_ref", policy_context_ref)
        object.__setattr__(self, "path_authority_ref", path_authority_ref)
        object.__setattr__(self, "constraint_context_ref", constraint_context_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "authority_status", authority_status)
        object.__setattr__(self, "authority_ref_hash", authority_ref_hash)
        object.__setattr__(self, "authority_ref_id", authority_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "authority_basis": self.authority_basis,
            "authority_kind": self.authority_kind.value,
            "authority_ref_hash": self.authority_ref_hash,
            "authority_ref_id": self.authority_ref_id,
            "authority_status": self.authority_status.value,
            "delegation_ref_id": self.delegation_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.policy_context_ref is not None:
            payload["policy_context_ref"] = self.policy_context_ref
        if self.path_authority_ref is not None:
            payload["path_authority_ref"] = self.path_authority_ref
        if self.constraint_context_ref is not None:
            payload["constraint_context_ref"] = self.constraint_context_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationAuthorityRef:
        validate_known_fields(
            data, AUTHORITY_REF_KNOWN_FIELDS, label="delegation_authority_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            authority_kind=data["authority_kind"],
            authority_basis=data["authority_basis"],
            policy_context_ref=data.get("policy_context_ref"),
            path_authority_ref=data.get("path_authority_ref"),
            constraint_context_ref=data.get("constraint_context_ref"),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            authority_status=data.get(
                "authority_status", DelegationAuthorityRefStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_AUTHORITY_REF_VERSION
            ),
            authority_ref_id=data.get("authority_ref_id", ""),
            authority_ref_hash=data.get("authority_ref_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationAuthorityBinding
# ---------------------------------------------------------------------------


def compute_authority_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_ref_id: str,
    authority_ref_hash: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_AUTHORITY_BINDING_VERSION,
) -> str:
    """Deterministic hash of an authority-to-identity/role/constraint binding."""
    return stable_hash({
        "authority_ref_hash": authority_ref_hash,
        "authority_ref_id": authority_ref_id,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationAuthorityBinding:
    """Binding between authority reference and delegation identity/role/constraint
       context.

    DelegationAuthorityBinding binds reference-only authority metadata.
    It is not authority grant.
    It is not approval.
    It is not permission.
    It is not policy decision.
    It is not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_ref_id: str
    authority_ref_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_AUTHORITY_BINDING_VERSION
    binding_id: str = ""
    binding_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash,
            field_name="delegation_identity_hash",
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        authority_ref_id = _required_string(
            self.authority_ref_id, field_name="authority_ref_id"
        )
        authority_ref_hash = _required_string(
            self.authority_ref_hash, field_name="authority_ref_hash"
        )
        source_label = _parse_source_label(self.source_label)

        binding_hash = compute_authority_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_ref_id=authority_ref_id,
            authority_ref_hash=authority_ref_hash,
            source_label=source_label,
            schema_version=schema_version,
        )
        binding_id = f"authbind:{binding_hash[:16]}"

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

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "delegation_identity_hash", delegation_identity_hash
        )
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "authority_ref_id", authority_ref_id)
        object.__setattr__(self, "authority_ref_hash", authority_ref_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_ref_hash": self.authority_ref_hash,
            "authority_ref_id": self.authority_ref_id,
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationAuthorityBinding:
        validate_known_fields(
            data,
            AUTHORITY_BINDING_KNOWN_FIELDS,
            label="delegation_authority_binding",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_ref_id=data["authority_ref_id"],
            authority_ref_hash=data["authority_ref_hash"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_AUTHORITY_BINDING_VERSION
            ),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationAuthorityBindingSet
# ---------------------------------------------------------------------------


def _order_authority_refs(
    refs: Sequence[DelegationAuthorityRef],
) -> tuple[DelegationAuthorityRef, ...]:
    """Deterministic ordering of authority refs by authority_ref_id."""
    return tuple(sorted(refs, key=lambda ar: ar.authority_ref_id))


def _order_authority_bindings(
    bindings: Sequence[DelegationAuthorityBinding],
) -> tuple[DelegationAuthorityBinding, ...]:
    """Deterministic ordering of authority bindings by binding_id."""
    return tuple(sorted(bindings, key=lambda b: b.binding_id))


def compute_authority_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_refs: tuple[DelegationAuthorityRef, ...],
    bindings: tuple[DelegationAuthorityBinding, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationAuthoritySideEffects,
    schema_version: str = DELEGATION_AUTHORITY_BINDING_SET_VERSION,
) -> str:
    """Deterministic hash of the full authority binding set."""
    payload: dict[str, Any] = {
        "authority_refs": [ar.to_canonical_dict() for ar in authority_refs],
        "bindings": [b.to_canonical_dict() for b in bindings],
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
    }
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationAuthorityBindingSet:
    """Collection of authority refs/bindings for one delegation.

    DelegationAuthorityBindingSet describes reference-only authority context.
    It does not grant authority.
    It does not verify authority.
    It does not approve work.
    It does not enforce constraints.
    It does not execute runtime behavior.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_refs: tuple[DelegationAuthorityRef, ...] = ()
    bindings: tuple[DelegationAuthorityBinding, ...] = ()
    side_effects: DelegationAuthoritySideEffects = field(
        default_factory=lambda: DelegationAuthoritySideEffects()
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_AUTHORITY_BINDING_SET_VERSION
    authority_binding_set_id: str = ""
    authority_binding_set_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash,
            field_name="delegation_identity_hash",
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_set_hash = _required_string(
            self.constraint_set_hash, field_name="constraint_set_hash"
        )
        source_label = _parse_source_label(self.source_label)

        authority_refs = _order_authority_refs(
            tuple(
                ar if isinstance(ar, DelegationAuthorityRef)
                else DelegationAuthorityRef.from_dict(ar)
                for ar in self.authority_refs
            )
        )
        bindings = _order_authority_bindings(
            tuple(
                b if isinstance(b, DelegationAuthorityBinding)
                else DelegationAuthorityBinding.from_dict(b)
                for b in self.bindings
            )
        )
        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationAuthoritySideEffects)
            else DelegationAuthoritySideEffects.from_dict(self.side_effects)
        )

        authority_binding_set_hash = compute_authority_binding_set_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_refs=authority_refs,
            bindings=bindings,
            source_label=source_label,
            side_effects=side_effects,
            schema_version=schema_version,
        )
        authority_binding_set_id = f"authbset:{authority_binding_set_hash[:16]}"

        if self.authority_binding_set_hash not in ("", authority_binding_set_hash):
            raise DelegationValidationError(
                "authority_binding_set_hash does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="authority_binding_set_hash",
            )
        if self.authority_binding_set_id not in ("", authority_binding_set_id):
            raise DelegationValidationError(
                "authority_binding_set_id does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="authority_binding_set_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "delegation_identity_hash", delegation_identity_hash
        )
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "authority_refs", authority_refs)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self, "authority_binding_set_hash", authority_binding_set_hash
        )
        object.__setattr__(
            self, "authority_binding_set_id", authority_binding_set_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "authority_binding_set_id": self.authority_binding_set_id,
            "authority_refs": [
                ar.to_canonical_dict() for ar in self.authority_refs
            ],
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationAuthorityBindingSet:
        validate_known_fields(
            data,
            AUTHORITY_BINDING_SET_KNOWN_FIELDS,
            label="delegation_authority_binding_set",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_refs=data.get("authority_refs", ()),
            bindings=data.get("bindings", ()),
            side_effects=data.get(
                "side_effects", DelegationAuthoritySideEffects()
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_AUTHORITY_BINDING_SET_VERSION
            ),
            authority_binding_set_id=data.get("authority_binding_set_id", ""),
            authority_binding_set_hash=data.get(
                "authority_binding_set_hash", ""
            ),
        )


# ---------------------------------------------------------------------------
# DelegationAuthoritySideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationAuthoritySideEffects:
    """Hard proof that P1.8.4 is non-authorizing, non-verifying, and non-mutating;
       all fields default to false."""

    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    permission_granted: bool = False
    authority_verified: bool = False
    path_authorized: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    constraint_enforced: bool = False
    delegation_executed: bool = False

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
            "approval_created": self.approval_created,
            "authority_verified": self.authority_verified,
            "constraint_enforced": self.constraint_enforced,
            "custos_called": self.custos_called,
            "delegation_executed": self.delegation_executed,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "path_authorized": self.path_authorized,
            "permission_granted": self.permission_granted,
            "policy_called": self.policy_called,
            "runtime_mutated": self.runtime_mutated,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationAuthoritySideEffects:
        validate_known_fields(
            data,
            AUTHORITY_SIDE_EFFECTS_KNOWN_FIELDS,
            label="delegation_authority_side_effects",
        )
        return cls(
            **{
                name: data.get(name, False)
                for name in AUTHORITY_SIDE_EFFECTS_KNOWN_FIELDS
            }
        )


# ---------------------------------------------------------------------------
# DelegationAuthorityStatusReport
# ---------------------------------------------------------------------------


def compute_authority_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationAuthoritySideEffects,
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
class DelegationAuthorityStatusReport:
    """Reports authority-reference model readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationAuthoritySideEffects = field(
        default_factory=DelegationAuthoritySideEffects,
    )
    schema_version: str = DELEGATION_AUTHORITY_STATUS_REPORT_VERSION
    status_hash: str = ""

    def __post_init__(self) -> None:
        status_label = _parse_source_label(self.status_label)
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )

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
            if isinstance(self.side_effects, DelegationAuthoritySideEffects)
            else DelegationAuthoritySideEffects.from_dict(self.side_effects)
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_authority_status_report_hash(
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
                sorted(
                    self.available_contracts.items(), key=lambda item: item[0]
                )
            ),
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "status_hash": self.status_hash,
            "status_label": self.status_label.value,
            "unavailable_bindings": dict(
                sorted(
                    self.unavailable_bindings.items(), key=lambda item: item[0]
                )
            ),
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationAuthorityStatusReport:
        validate_known_fields(
            data,
            AUTHORITY_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_authority_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get(
                "side_effects", DelegationAuthoritySideEffects()
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_AUTHORITY_STATUS_REPORT_VERSION
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_authority_ref(
    delegation_ref_id: str,
    authority_kind: DelegationAuthorityRefKind | str,
    authority_basis: str,
    *,
    policy_context_ref: str | None = None,
    path_authority_ref: str | None = None,
    constraint_context_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    authority_status: DelegationAuthorityRefStatus = (
        DelegationAuthorityRefStatus.REFERENCE_ONLY
    ),
) -> DelegationAuthorityRef:
    """Build authority context reference without granting authority."""
    return DelegationAuthorityRef(
        delegation_ref_id=delegation_ref_id,
        authority_kind=authority_kind,
        authority_basis=authority_basis,
        policy_context_ref=policy_context_ref,
        path_authority_ref=path_authority_ref,
        constraint_context_ref=constraint_context_ref,
        source_label=source_label,
        authority_status=authority_status,
    )


def build_delegation_authority_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_ref_id: str,
    authority_ref_hash: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAuthorityBinding:
    """Build authority-to-identity/role/constraint binding without granting,
       verifying, or approving."""
    return DelegationAuthorityBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_ref_id=authority_ref_id,
        authority_ref_hash=authority_ref_hash,
        source_label=source_label,
    )


def build_delegation_authority_binding_set(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_refs: Sequence[DelegationAuthorityRef | Mapping[str, Any]],
    bindings: Sequence[DelegationAuthorityBinding | Mapping[str, Any]],
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAuthorityBindingSet:
    """Build collection of authority refs/bindings without granting or
       enforcing authority."""
    return DelegationAuthorityBindingSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_refs=authority_refs,
        bindings=bindings,
        source_label=source_label,
    )


def _default_authority_available_contracts() -> dict[str, str]:
    return {
        "DelegationAuthorityBinding": DelegationSourceLabel.LIVE.value,
        "DelegationAuthorityBindingSet": DelegationSourceLabel.LIVE.value,
        "DelegationAuthorityRef": DelegationSourceLabel.LIVE.value,
        "DelegationAuthorityRefKind": DelegationSourceLabel.LIVE.value,
        "DelegationAuthorityRefStatus": DelegationSourceLabel.LIVE.value,
        "DelegationAuthoritySideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationAuthorityStatusReport": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_authority_status_report() -> DelegationAuthorityStatusReport:
    """Return honest P1.8.4 authority status report (non-authorizing)."""
    return DelegationAuthorityStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_authority_available_contracts(),
        unavailable_bindings=DELEGATION_AUTHORITY_UNAVAILABLE_BINDINGS,
        side_effects=DelegationAuthoritySideEffects(),
    )


def serialize_delegation_authority_ref(
    authority_ref: DelegationAuthorityRef,
) -> str:
    """Serialize DelegationAuthorityRef to deterministic canonical JSON."""
    return to_canonical_json(authority_ref)


def serialize_delegation_authority_binding_set(
    binding_set: DelegationAuthorityBindingSet,
) -> str:
    """Serialize DelegationAuthorityBindingSet to deterministic canonical JSON."""
    return to_canonical_json(binding_set)


def hash_delegation_authority_ref(
    authority_ref: DelegationAuthorityRef,
) -> str:
    """Return stable authority_ref_hash for DelegationAuthorityRef content."""
    return authority_ref.authority_ref_hash


def hash_delegation_authority_binding_set(
    binding_set: DelegationAuthorityBindingSet,
) -> str:
    """Return stable authority_binding_set_hash for
       DelegationAuthorityBindingSet content."""
    return binding_set.authority_binding_set_hash
