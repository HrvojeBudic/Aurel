"""Delegation role-binding schema (P1.8.2).

Role model for delegator, delegate, and delegated subject references:
typed, deterministic, JSON-safe, side-effect-free role contracts that bind
to DelegationRef / DelegationIdentity without approving, executing, enforcing,
verifying, activating, or granting authority.

Architectural law:
  - DelegationPartyRoleRef identifies actor role; it does not verify authority,
    activate an agent, or approve/execute delegation.
  - DelegatedSubjectRef describes what is delegated; it does not execute
    task/action/output, prove permission, or verify subject authority.
  - DelegationRoleBinding binds role metadata; it is not approval, permission,
    runtime execution, or trace verification.
  - DelegationRoleBindingSet describes the delegation triangle; it does not
    approve, execute, enforce, verify, activate, or grant authority.
  - DelegationRoleSideEffects is hard proof that P1.8.2 is non-executing.
  - role_binding_hash exists ≠ TRACE_VERIFIED.
  - Role binding exists ≠ approval granted.
  - Delegator role ref exists ≠ delegator authority verified.
  - Delegate role ref exists ≠ delegate activated.
  - Delegated subject ref exists ≠ subject executed.
  - Role model exists ≠ resolver exists.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .foundation import (
    DELEGATION_SCHEMA_VERSION,
    DelegationActorKind,
    DelegationError,
    DelegationErrorCode,
    DelegationSerializationError,
    DelegationSourceLabel,
    DelegationSubjectKind,
    DelegationUnknownFieldError,
    DelegationValidationError,
    _optional_string,
    _parse_source_label,
    _required_string,
    stable_hash,
    to_canonical_json,
    validate_known_fields,
)

DELEGATION_ROLES_TASK_ID = "P1.8.2"
DELEGATION_PARTY_ROLE_REF_VERSION = "delegation_party_role_ref.v1"
DELEGATED_SUBJECT_REF_VERSION = "delegated_subject_ref.v1"
DELEGATION_ROLE_BINDING_VERSION = "delegation_role_binding.v1"
DELEGATION_ROLE_BINDING_SET_VERSION = "delegation_role_binding_set.v1"
DELEGATION_ROLE_SIDE_EFFECTS_VERSION = "delegation_role_side_effects.v1"
DELEGATION_ROLE_STATUS_REPORT_VERSION = "delegation_role_status_report.v1"

DELEGATION_ROLES_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.2; "
        "role schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.2"
    ),
    "Ledger Write": "Ledger write is not available in P1.8.2 role layer",
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.2 role layer"
    ),
    "Policy/Custos Enforcement": (
        "Policy/Custos enforcement scheduled for later P1.8 tasks; "
        "not P1.8.2"
    ),
    "Approval Activation": (
        "Approval activation is not available in P1.8.2 role layer"
    ),
    "Delegation Resolver": (
        "Delegation resolver scheduled for later P1.8 tasks; not P1.8.2"
    ),
    "Delegation Chain Resolver": (
        "Delegation chain resolver scheduled for later P1.8 tasks; not P1.8.2"
    ),
    "Authority Bridge": (
        "Authority bridge scheduled for later P1.8 tasks; not P1.8.2"
    ),
    "Identity Mesh Resolver": (
        "Identity mesh resolver scheduled for later P1.8 tasks; not P1.8.2"
    ),
    "Non-Repudiation Verifier": (
        "Non-repudiation verifier scheduled for later P1.8 tasks; not P1.8.2"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.2"
    ),
}

PARTY_ROLE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "role_ref_id",
    "delegation_ref_id",
    "actor_ref",
    "role_kind",
    "source_label",
    "role_ref_hash",
})

SUBJECT_ROLE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "subject_role_ref_id",
    "delegation_ref_id",
    "subject_ref",
    "subject_kind",
    "source_label",
    "subject_role_hash",
})

ROLE_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_kind",
    "role_ref_hash",
    "source_label",
    "binding_status",
    "binding_hash",
})

ROLE_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "delegator",
    "delegate",
    "subject",
    "source_label",
    "binding_status",
    "role_binding_hash",
    "side_effects",
})

ROLE_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "delegation_executed",
    "delegation_enforced",
    "delegate_activated",
    "subject_executed",
    "authority_verified",
})

ROLE_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationRoleKind(str, Enum):
    """Classifies delegation role shape; does not resolve, approve, execute,
       activate, verify, or enforce."""

    DELEGATOR = "DELEGATOR"
    DELEGATE = "DELEGATE"
    SUBJECT = "SUBJECT"
    OBSERVER = "OBSERVER"
    UNKNOWN = "UNKNOWN"


class DelegationRoleBindingStatus(str, Enum):
    """Declared status of role binding; does not grant authority or prove
       verification."""

    ROLE_BOUND = "ROLE_BOUND"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parsers
# ---------------------------------------------------------------------------


def _parse_role_kind(
    value: DelegationRoleKind | str,
) -> DelegationRoleKind:
    if isinstance(value, DelegationRoleKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationRoleKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid role_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="role_kind",
            ) from exc
    raise DelegationError(
        "role_kind must be a string or DelegationRoleKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="role_kind",
    )


def _parse_binding_status(
    value: DelegationRoleBindingStatus | str,
) -> DelegationRoleBindingStatus:
    if isinstance(value, DelegationRoleBindingStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationRoleBindingStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid binding_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="binding_status",
            ) from exc
    raise DelegationError(
        "binding_status must be a string or DelegationRoleBindingStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="binding_status",
    )


# ---------------------------------------------------------------------------
# DelegationPartyRoleRef
# ---------------------------------------------------------------------------


def compute_role_ref_hash(
    *,
    delegation_ref_id: str,
    actor_ref: str,
    role_kind: DelegationRoleKind,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_PARTY_ROLE_REF_VERSION,
) -> str:
    """Deterministic hash of role-bound actor reference content."""
    return stable_hash({
        "actor_ref": actor_ref,
        "delegation_ref_id": delegation_ref_id,
        "role_kind": role_kind.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationPartyRoleRef:
    """Role-bound wrapper around an actor reference for delegator/delegate.

    DelegationPartyRoleRef identifies actor role.
    It does not verify authority, activate an agent, or approve/execute delegation.
    """

    delegation_ref_id: str
    actor_ref: str
    role_kind: DelegationRoleKind
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_PARTY_ROLE_REF_VERSION
    role_ref_id: str = ""
    role_ref_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        actor_ref = _required_string(self.actor_ref, field_name="actor_ref")
        role_kind = _parse_role_kind(self.role_kind)
        source_label = _parse_source_label(self.source_label)

        if role_kind not in (DelegationRoleKind.DELEGATOR, DelegationRoleKind.DELEGATE):
            raise DelegationValidationError(
                f"PartyRoleRef role_kind must be DELEGATOR or DELEGATE, got {role_kind!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="role_kind",
            )

        role_ref_hash = compute_role_ref_hash(
            delegation_ref_id=delegation_ref_id,
            actor_ref=actor_ref,
            role_kind=role_kind,
            source_label=source_label,
            schema_version=schema_version,
        )
        role_ref_id = f"role:{role_ref_hash[:16]}"

        if self.role_ref_hash not in ("", role_ref_hash):
            raise DelegationValidationError(
                "role_ref_hash does not match role ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="role_ref_hash",
            )
        if self.role_ref_id not in ("", role_ref_id):
            raise DelegationValidationError(
                "role_ref_id does not match role ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="role_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "actor_ref", actor_ref)
        object.__setattr__(self, "role_kind", role_kind)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "role_ref_hash", role_ref_hash)
        object.__setattr__(self, "role_ref_id", role_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "actor_ref": self.actor_ref,
            "delegation_ref_id": self.delegation_ref_id,
            "role_kind": self.role_kind.value,
            "role_ref_hash": self.role_ref_hash,
            "role_ref_id": self.role_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationPartyRoleRef:
        validate_known_fields(data, PARTY_ROLE_REF_KNOWN_FIELDS, label="party_role_ref")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            actor_ref=data["actor_ref"],
            role_kind=data["role_kind"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_PARTY_ROLE_REF_VERSION),
            role_ref_id=data.get("role_ref_id", ""),
            role_ref_hash=data.get("role_ref_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegatedSubjectRef
# ---------------------------------------------------------------------------


def compute_subject_role_hash(
    *,
    delegation_ref_id: str,
    subject_ref: str,
    subject_kind: DelegationSubjectKind,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATED_SUBJECT_REF_VERSION,
) -> str:
    """Deterministic hash of role-bound delegated subject reference content."""
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "subject_kind": subject_kind.value,
        "subject_ref": subject_ref,
    })


@dataclass(frozen=True)
class DelegatedSubjectRef:
    """Role-bound wrapper around delegated subject data/ref.

    DelegatedSubjectRef describes what is delegated.
    It does not execute task/action/output, prove permission, or verify subject
    authority.
    """

    delegation_ref_id: str
    subject_ref: str
    subject_kind: DelegationSubjectKind
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATED_SUBJECT_REF_VERSION
    subject_role_ref_id: str = ""
    subject_role_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        subject_ref = _required_string(self.subject_ref, field_name="subject_ref")
        subject_kind = (
            self.subject_kind
            if isinstance(self.subject_kind, DelegationSubjectKind)
            else DelegationSubjectKind(self.subject_kind)
        )
        source_label = _parse_source_label(self.source_label)

        subject_role_hash = compute_subject_role_hash(
            delegation_ref_id=delegation_ref_id,
            subject_ref=subject_ref,
            subject_kind=subject_kind,
            source_label=source_label,
            schema_version=schema_version,
        )
        subject_role_ref_id = f"subjrole:{subject_role_hash[:16]}"

        if self.subject_role_hash not in ("", subject_role_hash):
            raise DelegationValidationError(
                "subject_role_hash does not match subject role content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="subject_role_hash",
            )
        if self.subject_role_ref_id not in ("", subject_role_ref_id):
            raise DelegationValidationError(
                "subject_role_ref_id does not match subject role content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="subject_role_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "subject_ref", subject_ref)
        object.__setattr__(self, "subject_kind", subject_kind)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "subject_role_hash", subject_role_hash)
        object.__setattr__(self, "subject_role_ref_id", subject_role_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "subject_kind": self.subject_kind.value,
            "subject_ref": self.subject_ref,
            "subject_role_hash": self.subject_role_hash,
            "subject_role_ref_id": self.subject_role_ref_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegatedSubjectRef:
        validate_known_fields(
            data, SUBJECT_ROLE_REF_KNOWN_FIELDS, label="delegated_subject_ref"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            subject_ref=data["subject_ref"],
            subject_kind=data["subject_kind"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATED_SUBJECT_REF_VERSION),
            subject_role_ref_id=data.get("subject_role_ref_id", ""),
            subject_role_hash=data.get("subject_role_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRoleBinding
# ---------------------------------------------------------------------------


def compute_role_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_kind: DelegationRoleKind,
    role_ref_hash: str,
    binding_status: DelegationRoleBindingStatus,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_ROLE_BINDING_VERSION,
) -> str:
    """Deterministic hash of a single role binding."""
    return stable_hash({
        "binding_status": binding_status.value,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "role_kind": role_kind.value,
        "role_ref_hash": role_ref_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationRoleBinding:
    """One role binding between delegation identity/ref and a role ref.

    DelegationRoleBinding binds role metadata.
    It is not approval, permission, runtime execution, or trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_kind: DelegationRoleKind
    role_ref_hash: str
    binding_status: DelegationRoleBindingStatus = DelegationRoleBindingStatus.ROLE_BOUND
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_ROLE_BINDING_VERSION
    binding_id: str = ""
    binding_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash, field_name="delegation_identity_hash"
        )
        role_kind = _parse_role_kind(self.role_kind)
        role_ref_hash = _required_string(self.role_ref_hash, field_name="role_ref_hash")
        binding_status = _parse_binding_status(self.binding_status)
        source_label = _parse_source_label(self.source_label)

        binding_hash = compute_role_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_kind=role_kind,
            role_ref_hash=role_ref_hash,
            binding_status=binding_status,
            source_label=source_label,
            schema_version=schema_version,
        )
        binding_id = f"rolebind:{binding_hash[:16]}"

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
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "role_kind", role_kind)
        object.__setattr__(self, "role_ref_hash", role_ref_hash)
        object.__setattr__(self, "binding_status", binding_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "binding_status": self.binding_status.value,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "role_kind": self.role_kind.value,
            "role_ref_hash": self.role_ref_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRoleBinding:
        validate_known_fields(data, ROLE_BINDING_KNOWN_FIELDS, label="role_binding")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_kind=data["role_kind"],
            role_ref_hash=data["role_ref_hash"],
            binding_status=data.get(
                "binding_status", DelegationRoleBindingStatus.ROLE_BOUND
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_ROLE_BINDING_VERSION),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRoleBindingSet
# ---------------------------------------------------------------------------


def compute_role_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    delegator: DelegationPartyRoleRef,
    delegate: DelegationPartyRoleRef,
    subject: DelegatedSubjectRef,
    binding_status: DelegationRoleBindingStatus,
    source_label: DelegationSourceLabel,
    side_effects: DelegationRoleSideEffects,
    schema_version: str = DELEGATION_ROLE_BINDING_SET_VERSION,
) -> str:
    """Deterministic hash of the full delegator→delegate→subject role binding set."""
    payload: dict[str, Any] = {
        "binding_status": binding_status.value,
        "delegate": delegate.to_canonical_dict(),
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "delegator": delegator.to_canonical_dict(),
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
        "subject": subject.to_canonical_dict(),
    }
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationRoleBindingSet:
    """Full delegator → delegate → subject triangle for one delegation.

    DelegationRoleBindingSet describes the delegation triangle.
    It does not approve, execute, enforce, verify, activate, or grant authority.
    """

    delegator: DelegationPartyRoleRef
    delegate: DelegationPartyRoleRef
    subject: DelegatedSubjectRef
    delegation_ref_id: str
    delegation_identity_hash: str
    side_effects: DelegationRoleSideEffects = field(
        default_factory=lambda: DelegationRoleSideEffects()
    )
    binding_status: DelegationRoleBindingStatus = DelegationRoleBindingStatus.ROLE_BOUND
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_ROLE_BINDING_SET_VERSION
    binding_set_id: str = ""
    role_binding_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash, field_name="delegation_identity_hash"
        )

        delegator = (
            self.delegator
            if isinstance(self.delegator, DelegationPartyRoleRef)
            else DelegationPartyRoleRef.from_dict(self.delegator)
        )
        delegate = (
            self.delegate
            if isinstance(self.delegate, DelegationPartyRoleRef)
            else DelegationPartyRoleRef.from_dict(self.delegate)
        )
        subject = (
            self.subject
            if isinstance(self.subject, DelegatedSubjectRef)
            else DelegatedSubjectRef.from_dict(self.subject)
        )

        binding_status = _parse_binding_status(self.binding_status)
        source_label = _parse_source_label(self.source_label)

        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationRoleSideEffects)
            else DelegationRoleSideEffects.from_dict(self.side_effects)
        )

        if delegator.role_kind is not DelegationRoleKind.DELEGATOR:
            raise DelegationValidationError(
                f"binding set delegator must have role_kind DELEGATOR, got {delegator.role_kind!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="delegator.role_kind",
            )
        if delegate.role_kind is not DelegationRoleKind.DELEGATE:
            raise DelegationValidationError(
                f"binding set delegate must have role_kind DELEGATE, got {delegate.role_kind!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="delegate.role_kind",
            )

        role_binding_hash = compute_role_binding_set_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            delegator=delegator,
            delegate=delegate,
            subject=subject,
            binding_status=binding_status,
            source_label=source_label,
            side_effects=side_effects,
            schema_version=schema_version,
        )
        binding_set_id = f"roleset:{role_binding_hash[:16]}"

        if self.role_binding_hash not in ("", role_binding_hash):
            raise DelegationValidationError(
                "role_binding_hash does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="role_binding_hash",
            )
        if self.binding_set_id not in ("", binding_set_id):
            raise DelegationValidationError(
                "binding_set_id does not match binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="binding_set_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "delegator", delegator)
        object.__setattr__(self, "delegate", delegate)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "binding_status", binding_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "binding_set_id", binding_set_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "binding_set_id": self.binding_set_id,
            "binding_status": self.binding_status.value,
            "delegate": self.delegate.to_canonical_dict(),
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "delegator": self.delegator.to_canonical_dict(),
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
            "subject": self.subject.to_canonical_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRoleBindingSet:
        validate_known_fields(
            data, ROLE_BINDING_SET_KNOWN_FIELDS, label="role_binding_set"
        )
        return cls(
            delegator=data["delegator"],
            delegate=data["delegate"],
            subject=data["subject"],
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            side_effects=data.get("side_effects", DelegationRoleSideEffects()),
            binding_status=data.get(
                "binding_status", DelegationRoleBindingStatus.ROLE_BOUND
            ),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_ROLE_BINDING_SET_VERSION
            ),
            binding_set_id=data.get("binding_set_id", ""),
            role_binding_hash=data.get("role_binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRoleSideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationRoleSideEffects:
    """Hard proof that P1.8.2 is non-executing; all fields default to false."""

    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    delegation_executed: bool = False
    delegation_enforced: bool = False
    delegate_activated: bool = False
    subject_executed: bool = False
    authority_verified: bool = False

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
            "custos_called": self.custos_called,
            "delegate_activated": self.delegate_activated,
            "delegation_enforced": self.delegation_enforced,
            "delegation_executed": self.delegation_executed,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "policy_called": self.policy_called,
            "runtime_mutated": self.runtime_mutated,
            "subject_executed": self.subject_executed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRoleSideEffects:
        validate_known_fields(
            data, ROLE_SIDE_EFFECTS_KNOWN_FIELDS, label="delegation_role_side_effects"
        )
        return cls(
            **{name: data.get(name, False) for name in ROLE_SIDE_EFFECTS_KNOWN_FIELDS}
        )


# ---------------------------------------------------------------------------
# DelegationRoleStatusReport
# ---------------------------------------------------------------------------


def compute_role_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationRoleSideEffects,
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
class DelegationRoleStatusReport:
    """Declares role model readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationRoleSideEffects = field(
        default_factory=DelegationRoleSideEffects,
    )
    schema_version: str = DELEGATION_ROLE_STATUS_REPORT_VERSION
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
            if isinstance(self.side_effects, DelegationRoleSideEffects)
            else DelegationRoleSideEffects.from_dict(self.side_effects)
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_role_status_report_hash(
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
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRoleStatusReport:
        validate_known_fields(
            data,
            ROLE_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_role_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get("side_effects", DelegationRoleSideEffects()),
            schema_version=data.get(
                "schema_version", DELEGATION_ROLE_STATUS_REPORT_VERSION
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_party_role_ref(
    delegation_ref_id: str,
    actor_ref: str,
    role_kind: DelegationRoleKind | str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationPartyRoleRef:
    """Build role-bound delegator or delegate reference without verifying authority."""
    return DelegationPartyRoleRef(
        delegation_ref_id=delegation_ref_id,
        actor_ref=actor_ref,
        role_kind=role_kind,
        source_label=source_label,
    )


def build_delegated_subject_ref(
    delegation_ref_id: str,
    subject_ref: str,
    subject_kind: DelegationSubjectKind | str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegatedSubjectRef:
    """Build role-bound delegated subject reference without executing subject."""
    return DelegatedSubjectRef(
        delegation_ref_id=delegation_ref_id,
        subject_ref=subject_ref,
        subject_kind=subject_kind,
        source_label=source_label,
    )


def build_delegation_role_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_kind: DelegationRoleKind | str,
    role_ref_hash: str,
    *,
    binding_status: DelegationRoleBindingStatus = DelegationRoleBindingStatus.ROLE_BOUND,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRoleBinding:
    """Build a single role binding without granting approval or permission."""
    return DelegationRoleBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_kind=role_kind,
        role_ref_hash=role_ref_hash,
        binding_status=binding_status,
        source_label=source_label,
    )


def build_delegation_role_binding_set(
    delegator: DelegationPartyRoleRef | Mapping[str, Any],
    delegate: DelegationPartyRoleRef | Mapping[str, Any],
    subject: DelegatedSubjectRef | Mapping[str, Any],
    delegation_ref_id: str,
    delegation_identity_hash: str,
    *,
    binding_status: DelegationRoleBindingStatus = DelegationRoleBindingStatus.ROLE_BOUND,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRoleBindingSet:
    """Build full delegation role binding set without approving, executing, or enforcing."""
    return DelegationRoleBindingSet(
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        binding_status=binding_status,
        source_label=source_label,
    )


def _default_role_available_contracts() -> dict[str, str]:
    return {
        "DelegationPartyRoleRef": DelegationSourceLabel.LIVE.value,
        "DelegationRoleBinding": DelegationSourceLabel.LIVE.value,
        "DelegationRoleBindingSet": DelegationSourceLabel.LIVE.value,
        "DelegationRoleKind": DelegationSourceLabel.LIVE.value,
        "DelegationRoleSideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationRoleStatusReport": DelegationSourceLabel.LIVE.value,
        "DelegatedSubjectRef": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_role_status_report() -> DelegationRoleStatusReport:
    """Return honest P1.8.2 role status report (non-executing)."""
    return DelegationRoleStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_role_available_contracts(),
        unavailable_bindings=DELEGATION_ROLES_UNAVAILABLE_BINDINGS,
        side_effects=DelegationRoleSideEffects(),
    )


def serialize_delegation_role_binding_set(binding_set: DelegationRoleBindingSet) -> str:
    """Serialize DelegationRoleBindingSet to deterministic canonical JSON."""
    return to_canonical_json(binding_set)


def hash_delegation_role_binding_set(binding_set: DelegationRoleBindingSet) -> str:
    """Return stable role_binding_hash for DelegationRoleBindingSet content."""
    return binding_set.role_binding_hash
