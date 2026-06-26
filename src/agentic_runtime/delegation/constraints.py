"""Delegation constraint model (P1.8.3).

Declared constraint contracts bound to DelegationRef / DelegationIdentity /
DelegationRoleBindingSet without enforcing, approving, blocking, verifying,
resolving, or mutating runtime behavior.

Architectural law:
  - Constraint exists ≠ constraint enforced.
  - Required review exists ≠ approval created.
  - Risk bound exists ≠ policy/Custos decision.
  - Tool bound exists ≠ tool permission changed.
  - Data bound exists ≠ data access changed.
  - Time bound exists ≠ scheduler changed.
  - Constraint hash exists ≠ TRACE_VERIFIED.
  - Constraint set exists ≠ runtime blocking.
  - Constraint model exists ≠ resolver exists.
  - Constraint binding exists ≠ authority granted.
"""
from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .foundation import (
    DelegationConstraintKind,
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

DELEGATION_CONSTRAINTS_TASK_ID = "P1.8.3"
DELEGATION_CONSTRAINT_REF_VERSION = "delegation_constraint_ref.v1"
DELEGATION_CONSTRAINT_BINDING_VERSION = "delegation_constraint_binding.v1"
DELEGATION_CONSTRAINT_SET_VERSION = "delegation_constraint_set.v1"
DELEGATION_CONSTRAINT_SIDE_EFFECTS_VERSION = "delegation_constraint_side_effects.v1"
DELEGATION_CONSTRAINT_STATUS_REPORT_VERSION = "delegation_constraint_status_report.v1"

DELEGATION_CONSTRAINTS_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Approval Activation": (
        "Approval activation is not available in P1.8.3 constraint model"
    ),
    "Authority Bridge": (
        "Authority bridge scheduled for later P1.8 tasks; not P1.8.3"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.3"
    ),
    "Constraint Enforcement": (
        "Constraint enforcement scheduled for later P1.8 tasks; not P1.8.3"
    ),
    "Data Access Mutation": (
        "Data access mutation is not available in P1.8.3; constraints are "
        "declared only"
    ),
    "Delegation Chain Resolver": (
        "Delegation chain resolver scheduled for later P1.8 tasks; not P1.8.3"
    ),
    "Delegation Resolver": (
        "Delegation resolver scheduled for later P1.8 tasks; not P1.8.3"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.3 constraint model"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.3 constraint model"
    ),
    "Non-Repudiation Verifier": (
        "Non-repudiation verifier scheduled for later P1.8 tasks; not P1.8.3"
    ),
    "Policy/Custos Enforcement": (
        "Policy/Custos enforcement scheduled for later P1.8 tasks; "
        "not P1.8.3"
    ),
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.3; "
        "constraint schema only"
    ),
    "Runtime Blocker": (
        "Runtime blocking is not available in P1.8.3; constraints are "
        "declared only"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.3"
    ),
    "Scheduler Mutation": (
        "Scheduler mutation is not available in P1.8.3; time bounds are "
        "declared only"
    ),
    "Tool Permission Mutation": (
        "Tool permission mutation is not available in P1.8.3; tool bounds are "
        "declared only"
    ),
    "Violation/Drift Detector": (
        "Violation/drift detector scheduled for later P1.8 tasks; not P1.8.3"
    ),
}

CONSTRAINT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "constraint_ref_id",
    "delegation_ref_id",
    "constraint_kind",
    "constraint_value",
    "constraint_severity",
    "required_review",
    "review_ref",
    "source_label",
    "constraint_status",
    "constraint_hash",
})

CONSTRAINT_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_ref_id",
    "constraint_hash",
    "source_label",
    "binding_hash",
})

CONSTRAINT_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "constraint_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraints",
    "bindings",
    "source_label",
    "constraint_set_hash",
    "side_effects",
})

CONSTRAINT_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "constraint_enforced",
    "delegation_blocked",
    "tool_permission_changed",
    "data_access_changed",
    "scheduler_changed",
    "authority_verified",
})

CONSTRAINT_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationConstraintSeverity(str, Enum):
    """Describes importance/risk posture; does not trigger policy decisions or
       runtime blocking."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class DelegationConstraintStatus(str, Enum):
    """Declared constraint availability; does not imply enforcement, approval,
       verification, or execution."""

    DECLARED = "DECLARED"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parsers
# ---------------------------------------------------------------------------


def _parse_constraint_severity(
    value: DelegationConstraintSeverity | str,
) -> DelegationConstraintSeverity:
    if isinstance(value, DelegationConstraintSeverity):
        return value
    if isinstance(value, str):
        try:
            return DelegationConstraintSeverity(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid constraint_severity: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="constraint_severity",
            ) from exc
    raise DelegationError(
        "constraint_severity must be a string or DelegationConstraintSeverity",
        code=DelegationErrorCode.INVALID_ENUM,
        field="constraint_severity",
    )


def _parse_constraint_status(
    value: DelegationConstraintStatus | str,
) -> DelegationConstraintStatus:
    if isinstance(value, DelegationConstraintStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationConstraintStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid constraint_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="constraint_status",
            ) from exc
    raise DelegationError(
        "constraint_status must be a string or DelegationConstraintStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="constraint_status",
    )


def _parse_constraint_kind(
    value: DelegationConstraintKind | str,
) -> DelegationConstraintKind:
    if isinstance(value, DelegationConstraintKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationConstraintKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid constraint_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="constraint_kind",
            ) from exc
    raise DelegationError(
        "constraint_kind must be a string or DelegationConstraintKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="constraint_kind",
    )


# ---------------------------------------------------------------------------
# DelegationConstraintRef
# ---------------------------------------------------------------------------


def compute_constraint_ref_hash(
    *,
    delegation_ref_id: str,
    constraint_kind: DelegationConstraintKind,
    constraint_value: str,
    constraint_severity: DelegationConstraintSeverity,
    required_review: bool,
    review_ref: str | None,
    source_label: DelegationSourceLabel,
    constraint_status: DelegationConstraintStatus,
    schema_version: str = DELEGATION_CONSTRAINT_REF_VERSION,
) -> str:
    """Deterministic hash of declared constraint reference content."""
    payload: dict[str, Any] = {
        "constraint_kind": constraint_kind.value,
        "constraint_severity": constraint_severity.value,
        "constraint_status": constraint_status.value,
        "constraint_value": constraint_value,
        "delegation_ref_id": delegation_ref_id,
        "required_review": required_review,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if review_ref is not None:
        payload["review_ref"] = review_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationConstraintRef:
    """One declared delegation constraint reference.

    DelegationConstraintRef describes a declared constraint.
    It does not enforce the constraint.
    It does not create approval.
    It does not call policy/Custos.
    It does not mutate runtime, tools, scheduler, data access, trace, or Ledger.
    """

    delegation_ref_id: str
    constraint_kind: DelegationConstraintKind
    constraint_value: str
    constraint_severity: DelegationConstraintSeverity = (
        DelegationConstraintSeverity.MEDIUM
    )
    required_review: bool = False
    review_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    constraint_status: DelegationConstraintStatus = DelegationConstraintStatus.DECLARED
    schema_version: str = DELEGATION_CONSTRAINT_REF_VERSION
    constraint_ref_id: str = ""
    constraint_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        constraint_kind = _parse_constraint_kind(self.constraint_kind)
        constraint_value = _required_string(
            self.constraint_value, field_name="constraint_value"
        )
        constraint_severity = _parse_constraint_severity(self.constraint_severity)
        if not isinstance(self.required_review, bool):
            raise DelegationValidationError(
                "required_review must be boolean",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="required_review",
            )
        review_ref = _optional_string(self.review_ref)
        source_label = _parse_source_label(self.source_label)
        constraint_status = _parse_constraint_status(self.constraint_status)

        constraint_hash = compute_constraint_ref_hash(
            delegation_ref_id=delegation_ref_id,
            constraint_kind=constraint_kind,
            constraint_value=constraint_value,
            constraint_severity=constraint_severity,
            required_review=self.required_review,
            review_ref=review_ref,
            source_label=source_label,
            constraint_status=constraint_status,
            schema_version=schema_version,
        )
        constraint_ref_id = f"consref:{constraint_hash[:16]}"

        if self.constraint_hash not in ("", constraint_hash):
            raise DelegationValidationError(
                "constraint_hash does not match constraint ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="constraint_hash",
            )
        if self.constraint_ref_id not in ("", constraint_ref_id):
            raise DelegationValidationError(
                "constraint_ref_id does not match constraint ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="constraint_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "constraint_kind", constraint_kind)
        object.__setattr__(self, "constraint_value", constraint_value)
        object.__setattr__(self, "constraint_severity", constraint_severity)
        object.__setattr__(self, "required_review", self.required_review)
        object.__setattr__(self, "review_ref", review_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "constraint_status", constraint_status)
        object.__setattr__(self, "constraint_hash", constraint_hash)
        object.__setattr__(self, "constraint_ref_id", constraint_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "constraint_hash": self.constraint_hash,
            "constraint_kind": self.constraint_kind.value,
            "constraint_ref_id": self.constraint_ref_id,
            "constraint_severity": self.constraint_severity.value,
            "constraint_status": self.constraint_status.value,
            "constraint_value": self.constraint_value,
            "delegation_ref_id": self.delegation_ref_id,
            "required_review": self.required_review,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.review_ref is not None:
            payload["review_ref"] = self.review_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationConstraintRef:
        validate_known_fields(data, CONSTRAINT_REF_KNOWN_FIELDS, label="constraint_ref")
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            constraint_kind=data["constraint_kind"],
            constraint_value=data["constraint_value"],
            constraint_severity=data.get(
                "constraint_severity", DelegationConstraintSeverity.MEDIUM
            ),
            required_review=data.get("required_review", False),
            review_ref=data.get("review_ref"),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            constraint_status=data.get(
                "constraint_status", DelegationConstraintStatus.DECLARED
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_CONSTRAINT_REF_VERSION
            ),
            constraint_ref_id=data.get("constraint_ref_id", ""),
            constraint_hash=data.get("constraint_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationConstraintBinding
# ---------------------------------------------------------------------------


def compute_constraint_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_ref_id: str,
    constraint_hash: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_CONSTRAINT_BINDING_VERSION,
) -> str:
    """Deterministic hash of a constraint-to-identity/role binding."""
    return stable_hash({
        "constraint_hash": constraint_hash,
        "constraint_ref_id": constraint_ref_id,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationConstraintBinding:
    """Binding between a declared constraint and delegation identity/role context.

    DelegationConstraintBinding binds declared constraint metadata.
    It is not enforcement.
    It is not approval.
    It is not permission.
    It is not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_ref_id: str
    constraint_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_CONSTRAINT_BINDING_VERSION
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
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        constraint_ref_id = _required_string(
            self.constraint_ref_id, field_name="constraint_ref_id"
        )
        constraint_hash = _required_string(
            self.constraint_hash, field_name="constraint_hash"
        )
        source_label = _parse_source_label(self.source_label)

        binding_hash = compute_constraint_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_ref_id=constraint_ref_id,
            constraint_hash=constraint_hash,
            source_label=source_label,
            schema_version=schema_version,
        )
        binding_id = f"consbind:{binding_hash[:16]}"

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
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraint_ref_id", constraint_ref_id)
        object.__setattr__(self, "constraint_hash", constraint_hash)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "binding_hash", binding_hash)
        object.__setattr__(self, "binding_id", binding_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "binding_hash": self.binding_hash,
            "binding_id": self.binding_id,
            "constraint_hash": self.constraint_hash,
            "constraint_ref_id": self.constraint_ref_id,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationConstraintBinding:
        validate_known_fields(
            data, CONSTRAINT_BINDING_KNOWN_FIELDS, label="constraint_binding"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_ref_id=data["constraint_ref_id"],
            constraint_hash=data["constraint_hash"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_CONSTRAINT_BINDING_VERSION
            ),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationConstraintSet
# ---------------------------------------------------------------------------


def _order_constraints(
    constraints: Sequence[DelegationConstraintRef],
) -> tuple[DelegationConstraintRef, ...]:
    """Deterministic ordering of constraints by constraint_ref_id."""
    return tuple(
        sorted(constraints, key=lambda cr: cr.constraint_ref_id)
    )


def _order_bindings(
    bindings: Sequence[DelegationConstraintBinding],
) -> tuple[DelegationConstraintBinding, ...]:
    """Deterministic ordering of bindings by binding_id."""
    return tuple(
        sorted(bindings, key=lambda b: b.binding_id)
    )


def compute_constraint_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraints: tuple[DelegationConstraintRef, ...],
    bindings: tuple[DelegationConstraintBinding, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationConstraintSideEffects,
    schema_version: str = DELEGATION_CONSTRAINT_SET_VERSION,
) -> str:
    """Deterministic hash of the full constraint set."""
    payload: dict[str, Any] = {
        "bindings": [b.to_canonical_dict() for b in bindings],
        "constraints": [cr.to_canonical_dict() for cr in constraints],
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
    }
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationConstraintSet:
    """Collection of declared constraints for one delegation.

    DelegationConstraintSet describes declared limits.
    It does not enforce limits.
    It does not approve work.
    It does not block runtime.
    It does not grant or revoke access.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraints: tuple[DelegationConstraintRef, ...] = ()
    bindings: tuple[DelegationConstraintBinding, ...] = ()
    side_effects: DelegationConstraintSideEffects = field(
        default_factory=lambda: DelegationConstraintSideEffects()
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_CONSTRAINT_SET_VERSION
    constraint_set_id: str = ""
    constraint_set_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        delegation_identity_hash = _required_string(
            self.delegation_identity_hash, field_name="delegation_identity_hash"
        )
        role_binding_hash = _required_string(
            self.role_binding_hash, field_name="role_binding_hash"
        )
        source_label = _parse_source_label(self.source_label)

        constraints = _order_constraints(
            tuple(
                cr if isinstance(cr, DelegationConstraintRef)
                else DelegationConstraintRef.from_dict(cr)
                for cr in self.constraints
            )
        )
        bindings = _order_bindings(
            tuple(
                b if isinstance(b, DelegationConstraintBinding)
                else DelegationConstraintBinding.from_dict(b)
                for b in self.bindings
            )
        )
        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationConstraintSideEffects)
            else DelegationConstraintSideEffects.from_dict(self.side_effects)
        )

        constraint_set_hash = compute_constraint_set_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraints=constraints,
            bindings=bindings,
            source_label=source_label,
            side_effects=side_effects,
            schema_version=schema_version,
        )
        constraint_set_id = f"consset:{constraint_set_hash[:16]}"

        if self.constraint_set_hash not in ("", constraint_set_hash):
            raise DelegationValidationError(
                "constraint_set_hash does not match constraint set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="constraint_set_hash",
            )
        if self.constraint_set_id not in ("", constraint_set_id):
            raise DelegationValidationError(
                "constraint_set_id does not match constraint set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="constraint_set_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "delegation_identity_hash", delegation_identity_hash)
        object.__setattr__(self, "role_binding_hash", role_binding_hash)
        object.__setattr__(self, "constraints", constraints)
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "constraint_set_hash", constraint_set_hash)
        object.__setattr__(self, "constraint_set_id", constraint_set_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "constraint_set_hash": self.constraint_set_hash,
            "constraint_set_id": self.constraint_set_id,
            "constraints": [cr.to_canonical_dict() for cr in self.constraints],
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationConstraintSet:
        validate_known_fields(
            data, CONSTRAINT_SET_KNOWN_FIELDS, label="constraint_set"
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraints=data.get("constraints", ()),
            bindings=data.get("bindings", ()),
            side_effects=data.get("side_effects", DelegationConstraintSideEffects()),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get(
                "schema_version", DELEGATION_CONSTRAINT_SET_VERSION
            ),
            constraint_set_id=data.get("constraint_set_id", ""),
            constraint_set_hash=data.get("constraint_set_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationConstraintSideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationConstraintSideEffects:
    """Hard proof that P1.8.3 is non-enforcing and non-mutating; all fields default
       to false."""

    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    constraint_enforced: bool = False
    delegation_blocked: bool = False
    tool_permission_changed: bool = False
    data_access_changed: bool = False
    scheduler_changed: bool = False
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
            "constraint_enforced": self.constraint_enforced,
            "custos_called": self.custos_called,
            "data_access_changed": self.data_access_changed,
            "delegation_blocked": self.delegation_blocked,
            "global_trace_written": self.global_trace_written,
            "ledger_written": self.ledger_written,
            "policy_called": self.policy_called,
            "runtime_mutated": self.runtime_mutated,
            "scheduler_changed": self.scheduler_changed,
            "tool_permission_changed": self.tool_permission_changed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationConstraintSideEffects:
        validate_known_fields(
            data,
            CONSTRAINT_SIDE_EFFECTS_KNOWN_FIELDS,
            label="delegation_constraint_side_effects",
        )
        return cls(
            **{
                name: data.get(name, False)
                for name in CONSTRAINT_SIDE_EFFECTS_KNOWN_FIELDS
            }
        )


# ---------------------------------------------------------------------------
# DelegationConstraintStatusReport
# ---------------------------------------------------------------------------


def compute_constraint_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationConstraintSideEffects,
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
class DelegationConstraintStatusReport:
    """Reports constraint model readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationConstraintSideEffects = field(
        default_factory=DelegationConstraintSideEffects,
    )
    schema_version: str = DELEGATION_CONSTRAINT_STATUS_REPORT_VERSION
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
            if isinstance(self.side_effects, DelegationConstraintSideEffects)
            else DelegationConstraintSideEffects.from_dict(self.side_effects)
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))

        status_hash = compute_constraint_status_report_hash(
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
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationConstraintStatusReport:
        validate_known_fields(
            data,
            CONSTRAINT_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_constraint_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get("side_effects", DelegationConstraintSideEffects()),
            schema_version=data.get(
                "schema_version", DELEGATION_CONSTRAINT_STATUS_REPORT_VERSION
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_constraint_ref(
    delegation_ref_id: str,
    constraint_kind: DelegationConstraintKind | str,
    constraint_value: str,
    *,
    constraint_severity: DelegationConstraintSeverity = (
        DelegationConstraintSeverity.MEDIUM
    ),
    required_review: bool = False,
    review_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationConstraintRef:
    """Build a declared constraint reference without enforcing it."""
    return DelegationConstraintRef(
        delegation_ref_id=delegation_ref_id,
        constraint_kind=constraint_kind,
        constraint_value=constraint_value,
        constraint_severity=constraint_severity,
        required_review=required_review,
        review_ref=review_ref,
        source_label=source_label,
    )


def build_delegation_constraint_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_ref_id: str,
    constraint_hash: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationConstraintBinding:
    """Build a constraint-to-identity binding without enforcing, approving,
       or granting permission."""
    return DelegationConstraintBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_ref_id=constraint_ref_id,
        constraint_hash=constraint_hash,
        source_label=source_label,
    )


def build_delegation_constraint_set(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraints: Sequence[DelegationConstraintRef | Mapping[str, Any]],
    bindings: Sequence[DelegationConstraintBinding | Mapping[str, Any]],
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationConstraintSet:
    """Build a collection of declared constraints without enforcing limits."""
    return DelegationConstraintSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraints=constraints,
        bindings=bindings,
        source_label=source_label,
    )


def _default_constraint_available_contracts() -> dict[str, str]:
    return {
        "DelegationConstraintBinding": DelegationSourceLabel.LIVE.value,
        "DelegationConstraintRef": DelegationSourceLabel.LIVE.value,
        "DelegationConstraintSet": DelegationSourceLabel.LIVE.value,
        "DelegationConstraintSeverity": DelegationSourceLabel.LIVE.value,
        "DelegationConstraintSideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationConstraintStatus": DelegationSourceLabel.LIVE.value,
        "DelegationConstraintStatusReport": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_constraint_status_report() -> DelegationConstraintStatusReport:
    """Return honest P1.8.3 constraint status report (non-enforcing)."""
    return DelegationConstraintStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_constraint_available_contracts(),
        unavailable_bindings=DELEGATION_CONSTRAINTS_UNAVAILABLE_BINDINGS,
        side_effects=DelegationConstraintSideEffects(),
    )


def serialize_delegation_constraint_ref(
    constraint_ref: DelegationConstraintRef,
) -> str:
    """Serialize DelegationConstraintRef to deterministic canonical JSON."""
    return to_canonical_json(constraint_ref)


def serialize_delegation_constraint_set(
    constraint_set: DelegationConstraintSet,
) -> str:
    """Serialize DelegationConstraintSet to deterministic canonical JSON."""
    return to_canonical_json(constraint_set)


def hash_delegation_constraint_ref(
    constraint_ref: DelegationConstraintRef,
) -> str:
    """Return stable constraint_hash for DelegationConstraintRef content."""
    return constraint_ref.constraint_hash


def hash_delegation_constraint_set(
    constraint_set: DelegationConstraintSet,
) -> str:
    """Return stable constraint_set_hash for DelegationConstraintSet content."""
    return constraint_set.constraint_set_hash
