"""Delegation identity / reference schema (P1.8.1).

Stable identity/reference layer for delegations: typed DelegationRef,
DelegationIdentity, DelegationRefBinding, DelegationIdentitySideEffects,
and DelegationIdentityStatusReport with deterministic hashing, closed-world
validation, honest truth labels, and explicit side-effect boundaries.

Architectural law:
  - DelegationRef identifies delegation; it does not approve, execute,
    verify, enforce, or prove non-repudiation.
  - DelegationIdentity binds identity metadata; it does not activate
    delegation, verify delegation, or prove non-repudiation.
  - DelegationRefBinding describes reference linkage; it is not
    verification, trace proof, or approval.
  - Record hash exists; it is not trace verification.
  - Identity hash exists; it is not proof.
  - DelegationRef exists ≠ delegation is approved.
  - DelegationIdentity exists ≠ delegation is verified.
  - Record hash exists ≠ TRACE_VERIFIED.
  - Identity binding exists ≠ runtime execution.
  - Identity hash exists ≠ non-repudiation proof.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .foundation import (
    DELEGATION_SCHEMA_VERSION,
    DelegationError,
    DelegationErrorCode,
    DelegationSerializationError,
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

DELEGATION_IDENTITY_TASK_ID = "P1.8.1"
DELEGATION_IDENTITY_SCHEMA_VERSION = "delegation_identity.v1"
DELEGATION_REF_SCHEMA_VERSION = "delegation_ref.v1"
DELEGATION_REF_BINDING_SCHEMA_VERSION = "delegation_ref_binding.v1"
DELEGATION_IDENTITY_SIDE_EFFECTS_VERSION = "delegation_identity_side_effects.v1"
DELEGATION_IDENTITY_STATUS_REPORT_VERSION = "delegation_identity_status_report.v1"

DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.1; "
        "identity/ref schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.1"
    ),
    "Ledger Write": "Ledger write is not available in P1.8.1 identity layer",
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.1 identity layer"
    ),
    "Policy/Custos Enforcement": (
        "Policy/Custos enforcement scheduled for later P1.8 tasks; "
        "not P1.8.1"
    ),
    "Approval Activation": (
        "Approval activation is not available in P1.8.1 identity layer"
    ),
    "Identity Resolver": (
        "Identity resolver scheduled for later P1.8 tasks; not P1.8.1"
    ),
    "Non-Repudiation Verifier": (
        "Non-repudiation verifier scheduled for later P1.8 tasks; not P1.8.1"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.1"
    ),
}

DELEGATION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "delegation_ref_id",
    "delegation_id",
    "record_hash",
    "source_label",
    "identity_kind",
    "ref_hash",
})

REF_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_id",
    "record_hash",
    "binding_kind",
    "source_label",
    "binding_hash",
})

IDENTITY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "delegation_ref",
    "delegator_ref",
    "delegate_ref",
    "subject_ref",
    "authority_ref",
    "record_hash",
    "source_label",
    "identity_status",
    "identity_hash",
})

IDENTITY_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "delegation_executed",
    "delegation_enforced",
    "identity_resolved",
    "non_repudiation_verified",
})

IDENTITY_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "status_label",
    "available_contracts",
    "unavailable_bindings",
    "side_effects",
    "status_hash",
})


class DelegationIdentityKind(str, Enum):
    """Classifies reference shape; does not resolve, approve, execute, or verify."""

    RECORD_REF = "RECORD_REF"
    CHAIN_REF = "CHAIN_REF"
    SUBJECT_REF = "SUBJECT_REF"
    ACTOR_BOUND_REF = "ACTOR_BOUND_REF"
    AUTHORITY_CONTEXT_REF = "AUTHORITY_CONTEXT_REF"
    UNKNOWN = "UNKNOWN"


class DelegationIdentityStatus(str, Enum):
    """Status of identity schema availability; not delegation runtime status."""

    ACTIVE_SCHEMA = "ACTIVE_SCHEMA"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationRefBindingKind(str, Enum):
    """Describes reference linkage; binding is not verification or trace proof."""

    RECORD_HASH_BINDING = "RECORD_HASH_BINDING"
    DELEGATION_ID_BINDING = "DELEGATION_ID_BINDING"
    SUBJECT_REF_BINDING = "SUBJECT_REF_BINDING"
    ACTOR_REF_BINDING = "ACTOR_REF_BINDING"
    AUTHORITY_REF_BINDING = "AUTHORITY_REF_BINDING"
    UNKNOWN = "UNKNOWN"


def _parse_identity_kind(
    value: DelegationIdentityKind | str,
) -> DelegationIdentityKind:
    if isinstance(value, DelegationIdentityKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationIdentityKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid identity_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="identity_kind",
            ) from exc
    raise DelegationError(
        "identity_kind must be a string or DelegationIdentityKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="identity_kind",
    )


def _parse_identity_status(
    value: DelegationIdentityStatus | str,
) -> DelegationIdentityStatus:
    if isinstance(value, DelegationIdentityStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationIdentityStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid identity_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="identity_status",
            ) from exc
    raise DelegationError(
        "identity_status must be a string or DelegationIdentityStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="identity_status",
    )


def _parse_binding_kind(
    value: DelegationRefBindingKind | str,
) -> DelegationRefBindingKind:
    if isinstance(value, DelegationRefBindingKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationRefBindingKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid binding_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="binding_kind",
            ) from exc
    raise DelegationError(
        "binding_kind must be a string or DelegationRefBindingKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="binding_kind",
    )


# ---------------------------------------------------------------------------
# DelegationRef
# ---------------------------------------------------------------------------


def compute_ref_hash(
    *,
    delegation_id: str,
    record_hash: str,
    source_label: DelegationSourceLabel,
    identity_kind: DelegationIdentityKind,
    schema_version: str = DELEGATION_REF_SCHEMA_VERSION,
) -> str:
    return stable_hash({
        "delegation_id": delegation_id,
        "identity_kind": identity_kind.value,
        "record_hash": record_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationRef:
    """Stable reference to a delegation record.

    DelegationRef identifies a delegation.
    It does not approve, execute, verify, enforce, or prove it.
    """

    delegation_id: str
    record_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    identity_kind: DelegationIdentityKind = DelegationIdentityKind.RECORD_REF
    schema_version: str = DELEGATION_REF_SCHEMA_VERSION
    delegation_ref_id: str = ""
    ref_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_id = _required_string(self.delegation_id, field_name="delegation_id")
        record_hash = _required_string(self.record_hash, field_name="record_hash")
        source_label = _parse_source_label(self.source_label)
        identity_kind = _parse_identity_kind(self.identity_kind)

        ref_hash = compute_ref_hash(
            delegation_id=delegation_id,
            record_hash=record_hash,
            source_label=source_label,
            identity_kind=identity_kind,
            schema_version=schema_version,
        )
        delegation_ref_id = f"ref:{ref_hash[:16]}"

        if self.ref_hash not in ("", ref_hash):
            raise DelegationValidationError(
                "ref_hash does not match ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="ref_hash",
            )
        if self.delegation_ref_id not in ("", delegation_ref_id):
            raise DelegationValidationError(
                "delegation_ref_id does not match ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="delegation_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_id", delegation_id)
        object.__setattr__(self, "record_hash", record_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "identity_kind", identity_kind)
        object.__setattr__(self, "ref_hash", ref_hash)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_kind": self.identity_kind.value,
            "record_hash": self.record_hash,
            "ref_hash": self.ref_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRef:
        validate_known_fields(data, DELEGATION_REF_KNOWN_FIELDS, label="delegation_ref")
        return cls(
            delegation_id=data["delegation_id"],
            record_hash=data["record_hash"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            identity_kind=data.get("identity_kind", DelegationIdentityKind.RECORD_REF),
            schema_version=data.get("schema_version", DELEGATION_REF_SCHEMA_VERSION),
            delegation_ref_id=data.get("delegation_ref_id", ""),
            ref_hash=data.get("ref_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationRefBinding
# ---------------------------------------------------------------------------


def compute_ref_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_id: str,
    record_hash: str,
    binding_kind: DelegationRefBindingKind,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_REF_BINDING_SCHEMA_VERSION,
) -> str:
    return stable_hash({
        "binding_kind": binding_kind.value,
        "delegation_id": delegation_id,
        "delegation_ref_id": delegation_ref_id,
        "record_hash": record_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationRefBinding:
    """Binding showing how a DelegationRef connects to a delegation record.

    Binding describes reference linkage.
    Binding is not verification, trace proof, or approval.
    """

    delegation_ref_id: str
    delegation_id: str
    record_hash: str
    binding_kind: DelegationRefBindingKind = DelegationRefBindingKind.RECORD_HASH_BINDING
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_REF_BINDING_SCHEMA_VERSION
    binding_id: str = ""
    binding_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_id = _required_string(self.delegation_id, field_name="delegation_id")
        record_hash = _required_string(self.record_hash, field_name="record_hash")
        binding_kind = _parse_binding_kind(self.binding_kind)
        source_label = _parse_source_label(self.source_label)

        binding_hash = compute_ref_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_id=delegation_id,
            record_hash=record_hash,
            binding_kind=binding_kind,
            source_label=source_label,
            schema_version=schema_version,
        )
        binding_id = f"bind:{binding_hash[:16]}"

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
        object.__setattr__(self, "delegation_id", delegation_id)
        object.__setattr__(self, "record_hash", record_hash)
        object.__setattr__(self, "binding_kind", binding_kind)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "binding_kind": self.binding_kind.value,
            "delegation_id": self.delegation_id,
            "delegation_ref_id": self.delegation_ref_id,
            "record_hash": self.record_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRefBinding:
        validate_known_fields(data, REF_BINDING_KNOWN_FIELDS, label="delegation_ref_binding")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_id=data["delegation_id"],
            record_hash=data["record_hash"],
            binding_kind=data.get("binding_kind", DelegationRefBindingKind.RECORD_HASH_BINDING),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_REF_BINDING_SCHEMA_VERSION),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationIdentity
# ---------------------------------------------------------------------------


def compute_identity_hash(
    *,
    delegation_ref: str,
    record_hash: str,
    delegator_ref: str | None,
    delegate_ref: str | None,
    subject_ref: str,
    authority_ref: str | None,
    source_label: DelegationSourceLabel,
    identity_status: DelegationIdentityStatus,
    schema_version: str = DELEGATION_IDENTITY_SCHEMA_VERSION,
) -> str:
    payload: dict[str, Any] = {
        "identity_status": identity_status.value,
        "record_hash": record_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "subject_ref": subject_ref,
    }
    # delegation_ref is always required; included as delegation_ref not
    # an embedded object to keep identity_hash tightly coupled to the ref id
    payload["delegation_ref"] = delegation_ref
    if delegator_ref is not None:
        payload["delegator_ref"] = delegator_ref
    if delegate_ref is not None:
        payload["delegate_ref"] = delegate_ref
    if authority_ref is not None:
        payload["authority_ref"] = authority_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationIdentity:
    """Full identity object for a delegation.

    DelegationIdentity binds identity metadata.
    It does not activate delegation, verify delegation, or prove non-repudiation.
    """

    delegation_ref: str
    subject_ref: str
    record_hash: str
    delegator_ref: str | None = None
    delegate_ref: str | None = None
    authority_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    identity_status: DelegationIdentityStatus = DelegationIdentityStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_IDENTITY_SCHEMA_VERSION
    identity_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref = _required_string(
            self.delegation_ref, field_name="delegation_ref"
        )
        subject_ref = _required_string(self.subject_ref, field_name="subject_ref")
        record_hash = _required_string(self.record_hash, field_name="record_hash")
        delegator_ref = _optional_string(self.delegator_ref)
        delegate_ref = _optional_string(self.delegate_ref)
        authority_ref = _optional_string(self.authority_ref)
        source_label = _parse_source_label(self.source_label)
        identity_status = _parse_identity_status(self.identity_status)

        identity_hash = compute_identity_hash(
            delegation_ref=delegation_ref,
            record_hash=record_hash,
            delegator_ref=delegator_ref,
            delegate_ref=delegate_ref,
            subject_ref=subject_ref,
            authority_ref=authority_ref,
            source_label=source_label,
            identity_status=identity_status,
            schema_version=schema_version,
        )

        if self.identity_hash not in ("", identity_hash):
            raise DelegationValidationError(
                "identity_hash does not match identity content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="identity_hash",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref", delegation_ref)
        object.__setattr__(self, "subject_ref", subject_ref)
        object.__setattr__(self, "record_hash", record_hash)
        object.__setattr__(self, "delegator_ref", delegator_ref)
        object.__setattr__(self, "delegate_ref", delegate_ref)
        object.__setattr__(self, "authority_ref", authority_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "identity_status", identity_status)
        object.__setattr__(self, "identity_hash", identity_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "delegation_ref": self.delegation_ref,
            "identity_hash": self.identity_hash,
            "identity_status": self.identity_status.value,
            "record_hash": self.record_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "subject_ref": self.subject_ref,
        }
        if self.delegator_ref is not None:
            payload["delegator_ref"] = self.delegator_ref
        if self.delegate_ref is not None:
            payload["delegate_ref"] = self.delegate_ref
        if self.authority_ref is not None:
            payload["authority_ref"] = self.authority_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationIdentity:
        validate_known_fields(data, IDENTITY_KNOWN_FIELDS, label="delegation_identity")
        return cls(
            delegation_ref=data["delegation_ref"],
            subject_ref=data["subject_ref"],
            record_hash=data["record_hash"],
            delegator_ref=data.get("delegator_ref"),
            delegate_ref=data.get("delegate_ref"),
            authority_ref=data.get("authority_ref"),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            identity_status=data.get(
                "identity_status", DelegationIdentityStatus.REFERENCE_ONLY
            ),
            schema_version=data.get("schema_version", DELEGATION_IDENTITY_SCHEMA_VERSION),
            identity_hash=data.get("identity_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationIdentitySideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationIdentitySideEffects:
    """Hard proof that P1.8.1 is non-executing; all fields default to false."""

    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    delegation_executed: bool = False
    delegation_enforced: bool = False
    identity_resolved: bool = False
    non_repudiation_verified: bool = False

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
            "custos_called": self.custos_called,
            "delegation_enforced": self.delegation_enforced,
            "delegation_executed": self.delegation_executed,
            "global_trace_written": self.global_trace_written,
            "identity_resolved": self.identity_resolved,
            "ledger_written": self.ledger_written,
            "non_repudiation_verified": self.non_repudiation_verified,
            "policy_called": self.policy_called,
            "runtime_mutated": self.runtime_mutated,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationIdentitySideEffects:
        validate_known_fields(
            data, IDENTITY_SIDE_EFFECTS_KNOWN_FIELDS, label="delegation_identity_side_effects"
        )
        return cls(
            **{name: data.get(name, False) for name in IDENTITY_SIDE_EFFECTS_KNOWN_FIELDS}
        )


# ---------------------------------------------------------------------------
# DelegationIdentityStatusReport
# ---------------------------------------------------------------------------


def compute_identity_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationIdentitySideEffects,
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
class DelegationIdentityStatusReport:
    """Declares identity module readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationIdentitySideEffects = field(
        default_factory=DelegationIdentitySideEffects,
    )
    schema_version: str = DELEGATION_IDENTITY_STATUS_REPORT_VERSION
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
            if isinstance(self.side_effects, DelegationIdentitySideEffects)
            else DelegationIdentitySideEffects.from_dict(self.side_effects)
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_identity_status_report_hash(
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
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationIdentityStatusReport:
        validate_known_fields(
            data,
            IDENTITY_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_identity_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get("side_effects", DelegationIdentitySideEffects()),
            schema_version=data.get(
                "schema_version", DELEGATION_IDENTITY_STATUS_REPORT_VERSION
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_ref(
    delegation_id: str,
    record_hash: str,
    *,
    identity_kind: DelegationIdentityKind = DelegationIdentityKind.RECORD_REF,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRef:
    """Build a stable delegation reference without approving or executing."""
    return DelegationRef(
        delegation_id=delegation_id,
        record_hash=record_hash,
        identity_kind=identity_kind,
        source_label=source_label,
    )


def build_delegation_ref_binding(
    delegation_ref_id: str,
    delegation_id: str,
    record_hash: str,
    *,
    binding_kind: DelegationRefBindingKind = DelegationRefBindingKind.RECORD_HASH_BINDING,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRefBinding:
    """Build a ref-to-record binding without verifying or proving trace."""
    return DelegationRefBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_id=delegation_id,
        record_hash=record_hash,
        binding_kind=binding_kind,
        source_label=source_label,
    )


def build_delegation_identity(
    delegation_ref: str,
    subject_ref: str,
    record_hash: str,
    *,
    delegator_ref: str | None = None,
    delegate_ref: str | None = None,
    authority_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationIdentity:
    """Build delegation identity metadata without activating or verifying."""
    return DelegationIdentity(
        delegation_ref=delegation_ref,
        subject_ref=subject_ref,
        record_hash=record_hash,
        delegator_ref=delegator_ref,
        delegate_ref=delegate_ref,
        authority_ref=authority_ref,
        source_label=source_label,
    )


def _default_identity_available_contracts() -> dict[str, str]:
    return {
        "DelegationRef": DelegationSourceLabel.LIVE.value,
        "DelegationRefBinding": DelegationSourceLabel.LIVE.value,
        "DelegationIdentity": DelegationSourceLabel.LIVE.value,
        "DelegationIdentitySideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationIdentityStatusReport": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_identity_status_report() -> DelegationIdentityStatusReport:
    """Return honest P1.8.1 identity status report (non-executing)."""
    return DelegationIdentityStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_identity_available_contracts(),
        unavailable_bindings=DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS,
        side_effects=DelegationIdentitySideEffects(),
    )


def serialize_delegation_ref(ref: DelegationRef) -> str:
    """Serialize DelegationRef to deterministic canonical JSON."""
    return to_canonical_json(ref)


def serialize_delegation_identity(identity: DelegationIdentity) -> str:
    """Serialize DelegationIdentity to deterministic canonical JSON."""
    return to_canonical_json(identity)


def hash_delegation_ref(ref: DelegationRef) -> str:
    """Return stable ref_hash for DelegationRef content."""
    return ref.ref_hash


def hash_delegation_identity(identity: DelegationIdentity) -> str:
    """Return stable identity_hash for DelegationIdentity content."""
    return identity.identity_hash
