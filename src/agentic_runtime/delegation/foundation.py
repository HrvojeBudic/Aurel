"""Delegation foundation schema (P1.8.0).

Foundation-only layer: typed delegation records without authorization,
enforcement, verification, runtime execution, or side effects.

Architectural law:
  - DelegationRecord describes delegation; it is not permission.
  - AuthorityRef declares context; it does not grant authority.
  - NonRepudiationRef is reference-only; it is not verified proof.
  - AgentIdentityMeshRef names mesh context; it does not activate agents.
  - Record hash exists; it is not trace verification.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field, fields
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

DELEGATION_TASK_ID = "P1.8.0"
DELEGATION_SCHEMA_VERSION = "delegation_foundation.v1"
DELEGATION_FOUNDATION_STATUS_VERSION = "delegation_foundation_status.v1"
DELEGATION_MODULE_NAME = "delegation"

DELEGATION_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model scheduled for later P1.8 tasks; "
        "not P1.8.0 foundation"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.0"
    ),
    "Ledger Write": "Ledger write is not available in P1.8.0 foundation",
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.0 foundation"
    ),
    "Policy/Custos Enforcement": (
        "Policy/Custos enforcement scheduled for later P1.8 tasks; "
        "not P1.8.0"
    ),
    "Approval Activation": (
        "Approval activation is not available in P1.8.0 foundation"
    ),
    "Identity Mesh Resolver": (
        "Identity mesh resolver scheduled for later P1.8 tasks; not P1.8.0"
    ),
    "Crypto Verifier": (
        "Cryptographic signature verification scheduled for later P1.8 tasks; "
        "not P1.8.0"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.0 foundation"
    ),
}

ACTOR_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "actor_id",
    "actor_kind",
    "display_name",
    "source_label",
    "actor_ref_hash",
})

SUBJECT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "subject_id",
    "subject_kind",
    "subject_ref",
    "description",
    "source_label",
    "subject_hash",
})

AUTHORITY_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "authority_ref_id",
    "authority_kind",
    "authority_basis",
    "policy_context_ref",
    "path_authority_ref",
    "source_label",
    "authority_ref_hash",
})

CONSTRAINT_KNOWN_FIELDS: frozenset[str] = frozenset({
    "constraint_id",
    "constraint_kind",
    "constraint_value",
    "required_review",
    "source_label",
    "constraint_hash",
})

NON_REPUDIATION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "non_repudiation_ref_id",
    "evidence_ref",
    "attestation_ref",
    "signature_ref",
    "trace_ref",
    "source_label",
    "proof_status",
    "non_repudiation_ref_hash",
})

IDENTITY_MESH_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "mesh_ref_id",
    "agent_ref",
    "identity_ref",
    "relationship_ref",
    "mesh_scope",
    "source_label",
    "mesh_ref_hash",
})

SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_called",
    "custos_called",
    "approval_created",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
    "delegation_enforced",
    "agent_activated",
    "identity_mesh_resolved",
    "crypto_signature_verified",
})

RECORD_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "delegation_id",
    "delegator",
    "delegate",
    "subject",
    "authority_ref",
    "constraints",
    "non_repudiation_ref",
    "identity_mesh_ref",
    "source_label",
    "created_at",
    "record_hash",
    "side_effects",
})

FOUNDATION_STATUS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "status_label",
    "capabilities",
    "unavailable_bindings",
    "side_effects",
    "status_hash",
})


class DelegationErrorCode(str, Enum):
    DELEGATION_UNAVAILABLE = "DELEGATION_UNAVAILABLE"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_ENUM = "INVALID_ENUM"
    INVALID_VERSION = "INVALID_VERSION"
    INVALID_SOURCE_LABEL = "INVALID_SOURCE_LABEL"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass(frozen=True)
class DelegationStructuredError:
    code: DelegationErrorCode
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class DelegationError(ValueError):
    """Base error for delegation foundation operations."""

    def __init__(
        self,
        message: str,
        *,
        code: DelegationErrorCode | None = None,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.details = details

    def to_structured(self) -> DelegationStructuredError:
        return DelegationStructuredError(
            code=self.code or DelegationErrorCode.DELEGATION_UNAVAILABLE,
            message=str(self),
            field=self.field,
            details=self.details,
        )


class DelegationValidationError(DelegationError):
    """Raised when delegation payload fails closed-world or enum validation."""


class DelegationUnknownFieldError(DelegationValidationError):
    """Raised when an unknown field is present — closed-world enforcement."""


class DelegationSerializationError(DelegationError):
    """Raised when canonical serialization fails."""


class DelegationSourceLabel(str, Enum):
    """Integration-First truth label for operator-visible delegation data."""

    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    SIMULATED = "SIMULATED"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class DelegationActorKind(str, Enum):
    """Declared actor kind; actor kind does not authenticate or authorize."""

    OPERATOR = "OPERATOR"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"
    SERVICE = "SERVICE"
    UNKNOWN = "UNKNOWN"


class DelegationSubjectKind(str, Enum):
    """Declared delegation subject kind; subject kind does not approve action."""

    ACTION = "ACTION"
    OUTPUT = "OUTPUT"
    TASK = "TASK"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    PATH = "PATH"
    SOURCE = "SOURCE"
    MEMORY_WRITE = "MEMORY_WRITE"
    POLICY_CONTEXT = "POLICY_CONTEXT"
    UNKNOWN = "UNKNOWN"


class DelegationAuthorityKind(str, Enum):
    """Declared authority context kind; authority kind does not grant authority."""

    OPERATOR_DECLARED = "OPERATOR_DECLARED"
    POLICY_CONTEXT_REFERENCED = "POLICY_CONTEXT_REFERENCED"
    PATH_AUTHORITY_REFERENCED = "PATH_AUTHORITY_REFERENCED"
    SYSTEM_DECLARED = "SYSTEM_DECLARED"
    UNKNOWN = "UNKNOWN"


class DelegationConstraintKind(str, Enum):
    """Declared constraint kind; constraint kind does not enforce limits."""

    TIME_BOUND = "TIME_BOUND"
    SCOPE_BOUND = "SCOPE_BOUND"
    TOOL_BOUND = "TOOL_BOUND"
    DATA_BOUND = "DATA_BOUND"
    RISK_BOUND = "RISK_BOUND"
    OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
    POLICY_REVIEW_REQUIRED = "POLICY_REVIEW_REQUIRED"
    UNKNOWN = "UNKNOWN"


class NonRepudiationProofStatus(str, Enum):
    """Evidence reference posture; not cryptographic finality or verified proof."""

    REFERENCE_ONLY = "REFERENCE_ONLY"
    EVIDENCE_REFERENCED = "EVIDENCE_REFERENCED"
    TRACE_REFERENCED = "TRACE_REFERENCED"
    SIGNATURE_REFERENCED = "SIGNATURE_REFERENCED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class DelegationFoundationCapability(str, Enum):
    """Declared delegation foundation capability surface."""

    FOUNDATION_SCHEMA = "FOUNDATION_SCHEMA"
    DELEGATION_RECORD = "DELEGATION_RECORD"
    ACTOR_REF = "ACTOR_REF"
    SUBJECT_REF = "SUBJECT_REF"
    AUTHORITY_REF = "AUTHORITY_REF"
    CONSTRAINT_REF = "CONSTRAINT_REF"
    NON_REPUDIATION_REF = "NON_REPUDIATION_REF"
    IDENTITY_MESH_REF = "IDENTITY_MESH_REF"
    PROJECTION_API_EVENT = "PROJECTION_API_EVENT"
    CLI_SHELL_TUI = "CLI_SHELL_TUI"
    LEDGER_WRITE = "LEDGER_WRITE"
    GLOBAL_TRACE_WRITE = "GLOBAL_TRACE_WRITE"
    POLICY_CUSTOS_ENFORCEMENT = "POLICY_CUSTOS_ENFORCEMENT"
    APPROVAL_ACTIVATION = "APPROVAL_ACTIVATION"
    RUNTIME_EXECUTION = "RUNTIME_EXECUTION"
    CRYPTO_VERIFIER = "CRYPTO_VERIFIER"


FOUNDATION_AVAILABLE_CAPABILITIES: frozenset[DelegationFoundationCapability] = frozenset({
    DelegationFoundationCapability.FOUNDATION_SCHEMA,
    DelegationFoundationCapability.DELEGATION_RECORD,
    DelegationFoundationCapability.ACTOR_REF,
    DelegationFoundationCapability.SUBJECT_REF,
    DelegationFoundationCapability.AUTHORITY_REF,
    DelegationFoundationCapability.CONSTRAINT_REF,
    DelegationFoundationCapability.NON_REPUDIATION_REF,
    DelegationFoundationCapability.IDENTITY_MESH_REF,
})

FOUNDATION_UNAVAILABLE_CAPABILITIES: frozenset[DelegationFoundationCapability] = frozenset({
    DelegationFoundationCapability.PROJECTION_API_EVENT,
    DelegationFoundationCapability.CLI_SHELL_TUI,
    DelegationFoundationCapability.LEDGER_WRITE,
    DelegationFoundationCapability.GLOBAL_TRACE_WRITE,
    DelegationFoundationCapability.POLICY_CUSTOS_ENFORCEMENT,
    DelegationFoundationCapability.APPROVAL_ACTIVATION,
    DelegationFoundationCapability.RUNTIME_EXECUTION,
    DelegationFoundationCapability.CRYPTO_VERIFIER,
})


def validate_known_fields(
    raw: Mapping[str, Any],
    known_fields: frozenset[str],
    *,
    label: str = "payload",
) -> None:
    """Reject unknown fields in dict/factory inputs (closed-world)."""
    unknown = set(raw.keys()) - known_fields
    if unknown:
        raise DelegationUnknownFieldError(
            f"{label}: unknown field(s): {', '.join(sorted(unknown))} — closed-world",
            code=DelegationErrorCode.UNKNOWN_FIELD,
            field=sorted(unknown)[0],
            details={"unknown_fields": sorted(unknown), "label": label},
        )


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_canonical_dict") and callable(value.to_canonical_dict):
        return value.to_canonical_dict()
    if isinstance(value, MappingABC):
        return {
            str(key): _to_jsonable(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise DelegationSerializationError(
        f"unsupported canonical value type: {type(value).__name__}",
        code=DelegationErrorCode.SERIALIZATION_ERROR,
    )


def to_canonical_dict(value: Any) -> dict[str, Any]:
    """Convert a delegation object into a deterministic canonical dict."""
    result = _to_jsonable(value)
    if not isinstance(result, dict):
        raise DelegationSerializationError(
            "canonical dict conversion requires a mapping-compatible object",
            code=DelegationErrorCode.SERIALIZATION_ERROR,
        )
    return result


def to_canonical_json(value: Any) -> str:
    """Produce deterministic canonical JSON (sorted keys, compact separators)."""
    canonical = to_canonical_dict(value)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    """Compute stable SHA-256 hex digest of canonical JSON representation."""
    canonical = to_canonical_json(value)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_source_label(value: DelegationSourceLabel | str) -> DelegationSourceLabel:
    if isinstance(value, DelegationSourceLabel):
        return value
    if isinstance(value, str):
        try:
            return DelegationSourceLabel(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid source_label: {value!r}",
                code=DelegationErrorCode.INVALID_SOURCE_LABEL,
                field="source_label",
            ) from exc
    raise DelegationError(
        "source_label must be a string or DelegationSourceLabel",
        code=DelegationErrorCode.INVALID_SOURCE_LABEL,
        field="source_label",
    )


def _parse_actor_kind(value: DelegationActorKind | str) -> DelegationActorKind:
    if isinstance(value, DelegationActorKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationActorKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid actor_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="actor_kind",
            ) from exc
    raise DelegationError(
        "actor_kind must be a string or DelegationActorKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="actor_kind",
    )


def _parse_subject_kind(value: DelegationSubjectKind | str) -> DelegationSubjectKind:
    if isinstance(value, DelegationSubjectKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationSubjectKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid subject_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="subject_kind",
            ) from exc
    raise DelegationError(
        "subject_kind must be a string or DelegationSubjectKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="subject_kind",
    )


def _parse_authority_kind(
    value: DelegationAuthorityKind | str,
) -> DelegationAuthorityKind:
    if isinstance(value, DelegationAuthorityKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationAuthorityKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid authority_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="authority_kind",
            ) from exc
    raise DelegationError(
        "authority_kind must be a string or DelegationAuthorityKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="authority_kind",
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


def _parse_proof_status(
    value: NonRepudiationProofStatus | str,
) -> NonRepudiationProofStatus:
    if isinstance(value, NonRepudiationProofStatus):
        return value
    if isinstance(value, str):
        try:
            return NonRepudiationProofStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid proof_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="proof_status",
            ) from exc
    raise DelegationError(
        "proof_status must be a string or NonRepudiationProofStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="proof_status",
    )


def _required_string(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DelegationValidationError(
            f"{field_name} must be a non-empty string",
            code=DelegationErrorCode.VALIDATION_ERROR,
            field=field_name,
        )
    return value.strip()


def _optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DelegationValidationError(
            "optional string field must be a string or None",
            code=DelegationErrorCode.VALIDATION_ERROR,
        )
    stripped = value.strip()
    return stripped or None


def compute_actor_ref_hash(
    *,
    actor_kind: DelegationActorKind,
    display_name: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "actor_kind": actor_kind.value,
        "display_name": display_name,
        "source_label": source_label.value,
    })


def compute_subject_hash(
    *,
    subject_kind: DelegationSubjectKind,
    subject_ref: str,
    description: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "description": description,
        "source_label": source_label.value,
        "subject_kind": subject_kind.value,
        "subject_ref": subject_ref,
    })


def compute_authority_ref_hash(
    *,
    authority_kind: DelegationAuthorityKind,
    authority_basis: str,
    policy_context_ref: str | None,
    path_authority_ref: str | None,
    source_label: DelegationSourceLabel,
) -> str:
    payload: dict[str, Any] = {
        "authority_basis": authority_basis,
        "authority_kind": authority_kind.value,
        "source_label": source_label.value,
    }
    if policy_context_ref is not None:
        payload["policy_context_ref"] = policy_context_ref
    if path_authority_ref is not None:
        payload["path_authority_ref"] = path_authority_ref
    return stable_hash(payload)


def compute_constraint_hash(
    *,
    constraint_kind: DelegationConstraintKind,
    constraint_value: str,
    required_review: bool,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "constraint_kind": constraint_kind.value,
        "constraint_value": constraint_value,
        "required_review": required_review,
        "source_label": source_label.value,
    })


def compute_non_repudiation_ref_hash(
    *,
    evidence_ref: str | None,
    attestation_ref: str | None,
    signature_ref: str | None,
    trace_ref: str | None,
    source_label: DelegationSourceLabel,
    proof_status: NonRepudiationProofStatus,
) -> str:
    payload: dict[str, Any] = {
        "proof_status": proof_status.value,
        "source_label": source_label.value,
    }
    if evidence_ref is not None:
        payload["evidence_ref"] = evidence_ref
    if attestation_ref is not None:
        payload["attestation_ref"] = attestation_ref
    if signature_ref is not None:
        payload["signature_ref"] = signature_ref
    if trace_ref is not None:
        payload["trace_ref"] = trace_ref
    return stable_hash(payload)


def compute_mesh_ref_hash(
    *,
    agent_ref: str,
    identity_ref: str,
    relationship_ref: str | None,
    mesh_scope: str,
    source_label: DelegationSourceLabel,
) -> str:
    payload: dict[str, Any] = {
        "agent_ref": agent_ref,
        "identity_ref": identity_ref,
        "mesh_scope": mesh_scope,
        "source_label": source_label.value,
    }
    if relationship_ref is not None:
        payload["relationship_ref"] = relationship_ref
    return stable_hash(payload)


def _record_content_payload(
    *,
    schema_version: str,
    delegator: DelegationActorRef,
    delegate: DelegationActorRef,
    subject: DelegationSubject,
    authority_ref: DelegationAuthorityRef,
    constraints: tuple[DelegationConstraint, ...],
    non_repudiation_ref: NonRepudiationRef,
    identity_mesh_ref: AgentIdentityMeshRef,
    source_label: DelegationSourceLabel,
    created_at: str,
    side_effects: DelegationSideEffects,
) -> dict[str, Any]:
    return {
        "authority_ref": authority_ref.to_canonical_dict(),
        "constraints": [
            item.to_canonical_dict()
            for item in sorted(constraints, key=lambda c: c.constraint_id)
        ],
        "created_at": created_at,
        "delegate": delegate.to_canonical_dict(),
        "delegator": delegator.to_canonical_dict(),
        "identity_mesh_ref": identity_mesh_ref.to_canonical_dict(),
        "non_repudiation_ref": non_repudiation_ref.to_canonical_dict(),
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
        "subject": subject.to_canonical_dict(),
    }


def compute_delegation_id(
    *,
    schema_version: str,
    delegator: DelegationActorRef,
    delegate: DelegationActorRef,
    subject: DelegationSubject,
    authority_ref: DelegationAuthorityRef,
    constraints: tuple[DelegationConstraint, ...],
    non_repudiation_ref: NonRepudiationRef,
    identity_mesh_ref: AgentIdentityMeshRef,
    source_label: DelegationSourceLabel,
    created_at: str,
    side_effects: DelegationSideEffects,
) -> str:
    content_hash = stable_hash(_record_content_payload(
        schema_version=schema_version,
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        authority_ref=authority_ref,
        constraints=constraints,
        non_repudiation_ref=non_repudiation_ref,
        identity_mesh_ref=identity_mesh_ref,
        source_label=source_label,
        created_at=created_at,
        side_effects=side_effects,
    ))
    return f"delegation:{content_hash[:16]}"


def compute_record_hash(
    *,
    schema_version: str,
    delegation_id: str,
    delegator: DelegationActorRef,
    delegate: DelegationActorRef,
    subject: DelegationSubject,
    authority_ref: DelegationAuthorityRef,
    constraints: tuple[DelegationConstraint, ...],
    non_repudiation_ref: NonRepudiationRef,
    identity_mesh_ref: AgentIdentityMeshRef,
    source_label: DelegationSourceLabel,
    created_at: str,
    side_effects: DelegationSideEffects,
) -> str:
    payload = _record_content_payload(
        schema_version=schema_version,
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        authority_ref=authority_ref,
        constraints=constraints,
        non_repudiation_ref=non_repudiation_ref,
        identity_mesh_ref=identity_mesh_ref,
        source_label=source_label,
        created_at=created_at,
        side_effects=side_effects,
    )
    payload["delegation_id"] = delegation_id
    return stable_hash(payload)


def compute_foundation_status_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    capabilities: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationSideEffects,
) -> str:
    return stable_hash({
        "capabilities": dict(sorted(capabilities.items(), key=lambda item: item[0])),
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "status_label": status_label.value,
        "unavailable_bindings": dict(
            sorted(unavailable_bindings.items(), key=lambda item: item[0])
        ),
    })


@dataclass(frozen=True)
class DelegationActorRef:
    """Stable reference to delegator or delegate; identifies, does not authenticate."""

    actor_kind: DelegationActorKind
    display_name: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    actor_id: str = ""
    actor_ref_hash: str = ""

    def __post_init__(self) -> None:
        actor_kind = _parse_actor_kind(self.actor_kind)
        display_name = _required_string(self.display_name, field_name="display_name")
        source_label = _parse_source_label(self.source_label)
        actor_ref_hash = compute_actor_ref_hash(
            actor_kind=actor_kind,
            display_name=display_name,
            source_label=source_label,
        )
        actor_id = f"actor:{actor_ref_hash[:16]}"
        if self.actor_ref_hash not in ("", actor_ref_hash):
            raise DelegationValidationError(
                "actor_ref_hash does not match actor content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="actor_ref_hash",
            )
        if self.actor_id not in ("", actor_id):
            raise DelegationValidationError(
                "actor_id does not match actor content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="actor_id",
            )
        object.__setattr__(self, "actor_kind", actor_kind)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "actor_ref_hash", actor_ref_hash)
        object.__setattr__(self, "actor_id", actor_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "actor_kind": self.actor_kind.value,
            "actor_ref_hash": self.actor_ref_hash,
            "display_name": self.display_name,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationActorRef:
        validate_known_fields(data, ACTOR_REF_KNOWN_FIELDS, label="delegation_actor_ref")
        return cls(
            actor_kind=data["actor_kind"],
            display_name=data["display_name"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            actor_id=data.get("actor_id", ""),
            actor_ref_hash=data.get("actor_ref_hash", ""),
        )


@dataclass(frozen=True)
class DelegationSubject:
    """Describes what the delegation is about; subject exists ≠ action is approved."""

    subject_kind: DelegationSubjectKind
    subject_ref: str
    description: str = ""
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    subject_id: str = ""
    subject_hash: str = ""

    def __post_init__(self) -> None:
        subject_kind = _parse_subject_kind(self.subject_kind)
        subject_ref = _required_string(self.subject_ref, field_name="subject_ref")
        description = self.description.strip() if isinstance(self.description, str) else ""
        source_label = _parse_source_label(self.source_label)
        subject_hash = compute_subject_hash(
            subject_kind=subject_kind,
            subject_ref=subject_ref,
            description=description,
            source_label=source_label,
        )
        subject_id = f"subject:{subject_hash[:16]}"
        if self.subject_hash not in ("", subject_hash):
            raise DelegationValidationError(
                "subject_hash does not match subject content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="subject_hash",
            )
        if self.subject_id not in ("", subject_id):
            raise DelegationValidationError(
                "subject_id does not match subject content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="subject_id",
            )
        object.__setattr__(self, "subject_kind", subject_kind)
        object.__setattr__(self, "subject_ref", subject_ref)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "subject_hash", subject_hash)
        object.__setattr__(self, "subject_id", subject_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "source_label": self.source_label.value,
            "subject_hash": self.subject_hash,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind.value,
            "subject_ref": self.subject_ref,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationSubject:
        validate_known_fields(data, SUBJECT_KNOWN_FIELDS, label="delegation_subject")
        return cls(
            subject_kind=data["subject_kind"],
            subject_ref=data["subject_ref"],
            description=data.get("description", ""),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            subject_id=data.get("subject_id", ""),
            subject_hash=data.get("subject_hash", ""),
        )


@dataclass(frozen=True)
class DelegationAuthorityRef:
    """Declares authority context reference; AuthorityRef exists ≠ authority was granted."""

    authority_kind: DelegationAuthorityKind
    authority_basis: str
    policy_context_ref: str | None = None
    path_authority_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    authority_ref_id: str = ""
    authority_ref_hash: str = ""

    def __post_init__(self) -> None:
        authority_kind = _parse_authority_kind(self.authority_kind)
        authority_basis = _required_string(
            self.authority_basis,
            field_name="authority_basis",
        )
        policy_context_ref = _optional_string(self.policy_context_ref)
        path_authority_ref = _optional_string(self.path_authority_ref)
        source_label = _parse_source_label(self.source_label)
        authority_ref_hash = compute_authority_ref_hash(
            authority_kind=authority_kind,
            authority_basis=authority_basis,
            policy_context_ref=policy_context_ref,
            path_authority_ref=path_authority_ref,
            source_label=source_label,
        )
        authority_ref_id = f"authority:{authority_ref_hash[:16]}"
        if self.authority_ref_hash not in ("", authority_ref_hash):
            raise DelegationValidationError(
                "authority_ref_hash does not match authority content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="authority_ref_hash",
            )
        if self.authority_ref_id not in ("", authority_ref_id):
            raise DelegationValidationError(
                "authority_ref_id does not match authority content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="authority_ref_id",
            )
        object.__setattr__(self, "authority_kind", authority_kind)
        object.__setattr__(self, "authority_basis", authority_basis)
        object.__setattr__(self, "policy_context_ref", policy_context_ref)
        object.__setattr__(self, "path_authority_ref", path_authority_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "authority_ref_hash", authority_ref_hash)
        object.__setattr__(self, "authority_ref_id", authority_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "authority_basis": self.authority_basis,
            "authority_kind": self.authority_kind.value,
            "authority_ref_hash": self.authority_ref_hash,
            "authority_ref_id": self.authority_ref_id,
            "source_label": self.source_label.value,
        }
        if self.policy_context_ref is not None:
            payload["policy_context_ref"] = self.policy_context_ref
        if self.path_authority_ref is not None:
            payload["path_authority_ref"] = self.path_authority_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationAuthorityRef:
        validate_known_fields(
            data,
            AUTHORITY_REF_KNOWN_FIELDS,
            label="delegation_authority_ref",
        )
        return cls(
            authority_kind=data["authority_kind"],
            authority_basis=data["authority_basis"],
            policy_context_ref=data.get("policy_context_ref"),
            path_authority_ref=data.get("path_authority_ref"),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            authority_ref_id=data.get("authority_ref_id", ""),
            authority_ref_hash=data.get("authority_ref_hash", ""),
        )


@dataclass(frozen=True)
class DelegationConstraint:
    """Captures declared limits; constraint is descriptive, it does not enforce."""

    constraint_kind: DelegationConstraintKind
    constraint_value: str
    required_review: bool = False
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    constraint_id: str = ""
    constraint_hash: str = ""

    def __post_init__(self) -> None:
        constraint_kind = _parse_constraint_kind(self.constraint_kind)
        constraint_value = _required_string(
            self.constraint_value,
            field_name="constraint_value",
        )
        if not isinstance(self.required_review, bool):
            raise DelegationValidationError(
                "required_review must be boolean",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="required_review",
            )
        source_label = _parse_source_label(self.source_label)
        constraint_hash = compute_constraint_hash(
            constraint_kind=constraint_kind,
            constraint_value=constraint_value,
            required_review=self.required_review,
            source_label=source_label,
        )
        constraint_id = f"constraint:{constraint_hash[:16]}"
        if self.constraint_hash not in ("", constraint_hash):
            raise DelegationValidationError(
                "constraint_hash does not match constraint content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="constraint_hash",
            )
        if self.constraint_id not in ("", constraint_id):
            raise DelegationValidationError(
                "constraint_id does not match constraint content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="constraint_id",
            )
        object.__setattr__(self, "constraint_kind", constraint_kind)
        object.__setattr__(self, "constraint_value", constraint_value)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "constraint_hash", constraint_hash)
        object.__setattr__(self, "constraint_id", constraint_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "constraint_hash": self.constraint_hash,
            "constraint_id": self.constraint_id,
            "constraint_kind": self.constraint_kind.value,
            "constraint_value": self.constraint_value,
            "required_review": self.required_review,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationConstraint:
        validate_known_fields(data, CONSTRAINT_KNOWN_FIELDS, label="delegation_constraint")
        return cls(
            constraint_kind=data["constraint_kind"],
            constraint_value=data["constraint_value"],
            required_review=data.get("required_review", False),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            constraint_id=data.get("constraint_id", ""),
            constraint_hash=data.get("constraint_hash", ""),
        )


@dataclass(frozen=True)
class NonRepudiationRef:
    """Future-ready evidence reference; NonRepudiationRef exists ≠ final proof exists."""

    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    proof_status: NonRepudiationProofStatus = NonRepudiationProofStatus.REFERENCE_ONLY
    evidence_ref: str | None = None
    attestation_ref: str | None = None
    signature_ref: str | None = None
    trace_ref: str | None = None
    non_repudiation_ref_id: str = ""
    non_repudiation_ref_hash: str = ""

    def __post_init__(self) -> None:
        source_label = _parse_source_label(self.source_label)
        proof_status = _parse_proof_status(self.proof_status)
        evidence_ref = _optional_string(self.evidence_ref)
        attestation_ref = _optional_string(self.attestation_ref)
        signature_ref = _optional_string(self.signature_ref)
        trace_ref = _optional_string(self.trace_ref)
        non_repudiation_ref_hash = compute_non_repudiation_ref_hash(
            evidence_ref=evidence_ref,
            attestation_ref=attestation_ref,
            signature_ref=signature_ref,
            trace_ref=trace_ref,
            source_label=source_label,
            proof_status=proof_status,
        )
        non_repudiation_ref_id = f"nonrep:{non_repudiation_ref_hash[:16]}"
        if self.non_repudiation_ref_hash not in ("", non_repudiation_ref_hash):
            raise DelegationValidationError(
                "non_repudiation_ref_hash does not match non-repudiation content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="non_repudiation_ref_hash",
            )
        if self.non_repudiation_ref_id not in ("", non_repudiation_ref_id):
            raise DelegationValidationError(
                "non_repudiation_ref_id does not match non-repudiation content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="non_repudiation_ref_id",
            )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "proof_status", proof_status)
        object.__setattr__(self, "evidence_ref", evidence_ref)
        object.__setattr__(self, "attestation_ref", attestation_ref)
        object.__setattr__(self, "signature_ref", signature_ref)
        object.__setattr__(self, "trace_ref", trace_ref)
        object.__setattr__(self, "non_repudiation_ref_hash", non_repudiation_ref_hash)
        object.__setattr__(self, "non_repudiation_ref_id", non_repudiation_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "non_repudiation_ref_hash": self.non_repudiation_ref_hash,
            "non_repudiation_ref_id": self.non_repudiation_ref_id,
            "proof_status": self.proof_status.value,
            "source_label": self.source_label.value,
        }
        if self.evidence_ref is not None:
            payload["evidence_ref"] = self.evidence_ref
        if self.attestation_ref is not None:
            payload["attestation_ref"] = self.attestation_ref
        if self.signature_ref is not None:
            payload["signature_ref"] = self.signature_ref
        if self.trace_ref is not None:
            payload["trace_ref"] = self.trace_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> NonRepudiationRef:
        validate_known_fields(
            data,
            NON_REPUDIATION_REF_KNOWN_FIELDS,
            label="non_repudiation_ref",
        )
        return cls(
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            proof_status=data.get("proof_status", NonRepudiationProofStatus.REFERENCE_ONLY),
            evidence_ref=data.get("evidence_ref"),
            attestation_ref=data.get("attestation_ref"),
            signature_ref=data.get("signature_ref"),
            trace_ref=data.get("trace_ref"),
            non_repudiation_ref_id=data.get("non_repudiation_ref_id", ""),
            non_repudiation_ref_hash=data.get("non_repudiation_ref_hash", ""),
        )


@dataclass(frozen=True)
class AgentIdentityMeshRef:
    """Future-ready identity mesh reference; mesh ref does not resolve or activate agents."""

    agent_ref: str
    identity_ref: str
    mesh_scope: str
    relationship_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    mesh_ref_id: str = ""
    mesh_ref_hash: str = ""

    def __post_init__(self) -> None:
        agent_ref = _required_string(self.agent_ref, field_name="agent_ref")
        identity_ref = _required_string(self.identity_ref, field_name="identity_ref")
        mesh_scope = _required_string(self.mesh_scope, field_name="mesh_scope")
        relationship_ref = _optional_string(self.relationship_ref)
        source_label = _parse_source_label(self.source_label)
        mesh_ref_hash = compute_mesh_ref_hash(
            agent_ref=agent_ref,
            identity_ref=identity_ref,
            relationship_ref=relationship_ref,
            mesh_scope=mesh_scope,
            source_label=source_label,
        )
        mesh_ref_id = f"mesh:{mesh_ref_hash[:16]}"
        if self.mesh_ref_hash not in ("", mesh_ref_hash):
            raise DelegationValidationError(
                "mesh_ref_hash does not match mesh content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="mesh_ref_hash",
            )
        if self.mesh_ref_id not in ("", mesh_ref_id):
            raise DelegationValidationError(
                "mesh_ref_id does not match mesh content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="mesh_ref_id",
            )
        object.__setattr__(self, "agent_ref", agent_ref)
        object.__setattr__(self, "identity_ref", identity_ref)
        object.__setattr__(self, "mesh_scope", mesh_scope)
        object.__setattr__(self, "relationship_ref", relationship_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "mesh_ref_hash", mesh_ref_hash)
        object.__setattr__(self, "mesh_ref_id", mesh_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "agent_ref": self.agent_ref,
            "identity_ref": self.identity_ref,
            "mesh_ref_hash": self.mesh_ref_hash,
            "mesh_ref_id": self.mesh_ref_id,
            "mesh_scope": self.mesh_scope,
            "source_label": self.source_label.value,
        }
        if self.relationship_ref is not None:
            payload["relationship_ref"] = self.relationship_ref
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AgentIdentityMeshRef:
        validate_known_fields(
            data,
            IDENTITY_MESH_REF_KNOWN_FIELDS,
            label="agent_identity_mesh_ref",
        )
        return cls(
            agent_ref=data["agent_ref"],
            identity_ref=data["identity_ref"],
            mesh_scope=data["mesh_scope"],
            relationship_ref=data.get("relationship_ref"),
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            mesh_ref_id=data.get("mesh_ref_id", ""),
            mesh_ref_hash=data.get("mesh_ref_hash", ""),
        )


@dataclass(frozen=True)
class DelegationSideEffects:
    """Hard proof that P1.8.0 is non-executing; all fields default to false."""

    policy_called: bool = False
    custos_called: bool = False
    approval_created: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False
    delegation_enforced: bool = False
    agent_activated: bool = False
    identity_mesh_resolved: bool = False
    crypto_signature_verified: bool = False

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
            "agent_activated": self.agent_activated,
            "approval_created": self.approval_created,
            "crypto_signature_verified": self.crypto_signature_verified,
            "custos_called": self.custos_called,
            "delegation_enforced": self.delegation_enforced,
            "global_trace_written": self.global_trace_written,
            "identity_mesh_resolved": self.identity_mesh_resolved,
            "ledger_written": self.ledger_written,
            "policy_called": self.policy_called,
            "runtime_mutated": self.runtime_mutated,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationSideEffects:
        validate_known_fields(data, SIDE_EFFECTS_KNOWN_FIELDS, label="delegation_side_effects")
        return cls(**{name: data.get(name, False) for name in SIDE_EFFECTS_KNOWN_FIELDS})


def _build_actor(value: DelegationActorRef | Mapping[str, Any]) -> DelegationActorRef:
    if isinstance(value, DelegationActorRef):
        return value
    return DelegationActorRef.from_dict(value)


def _build_subject(value: DelegationSubject | Mapping[str, Any]) -> DelegationSubject:
    if isinstance(value, DelegationSubject):
        return value
    return DelegationSubject.from_dict(value)


def _build_authority_ref(
    value: DelegationAuthorityRef | Mapping[str, Any],
) -> DelegationAuthorityRef:
    if isinstance(value, DelegationAuthorityRef):
        return value
    return DelegationAuthorityRef.from_dict(value)


def _build_constraint(
    value: DelegationConstraint | Mapping[str, Any],
) -> DelegationConstraint:
    if isinstance(value, DelegationConstraint):
        return value
    return DelegationConstraint.from_dict(value)


def _freeze_constraints(
    constraints: Sequence[DelegationConstraint | Mapping[str, Any]] | None,
) -> tuple[DelegationConstraint, ...]:
    if constraints is None:
        return ()
    return tuple(_build_constraint(item) for item in constraints)


def _build_non_repudiation_ref(
    value: NonRepudiationRef | Mapping[str, Any],
) -> NonRepudiationRef:
    if isinstance(value, NonRepudiationRef):
        return value
    return NonRepudiationRef.from_dict(value)


def _build_identity_mesh_ref(
    value: AgentIdentityMeshRef | Mapping[str, Any],
) -> AgentIdentityMeshRef:
    if isinstance(value, AgentIdentityMeshRef):
        return value
    return AgentIdentityMeshRef.from_dict(value)


@dataclass(frozen=True)
class DelegationRecord:
    """Central foundation object; describes delegation without executing it."""

    delegator: DelegationActorRef
    delegate: DelegationActorRef
    subject: DelegationSubject
    authority_ref: DelegationAuthorityRef
    constraints: tuple[DelegationConstraint, ...]
    non_repudiation_ref: NonRepudiationRef
    identity_mesh_ref: AgentIdentityMeshRef
    created_at: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_SCHEMA_VERSION
    delegation_id: str = ""
    record_hash: str = ""
    side_effects: DelegationSideEffects = field(default_factory=DelegationSideEffects)

    def __post_init__(self) -> None:
        delegator = _build_actor(self.delegator)
        delegate = _build_actor(self.delegate)
        subject = _build_subject(self.subject)
        authority_ref = _build_authority_ref(self.authority_ref)
        constraints = _freeze_constraints(self.constraints)
        non_repudiation_ref = _build_non_repudiation_ref(self.non_repudiation_ref)
        identity_mesh_ref = _build_identity_mesh_ref(self.identity_mesh_ref)
        created_at = _required_string(self.created_at, field_name="created_at")
        source_label = _parse_source_label(self.source_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        if schema_version != DELEGATION_SCHEMA_VERSION:
            raise DelegationValidationError(
                f"unsupported schema_version: {schema_version!r}",
                code=DelegationErrorCode.INVALID_VERSION,
                field="schema_version",
            )
        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationSideEffects)
            else DelegationSideEffects.from_dict(self.side_effects)
        )
        delegation_id = self.delegation_id or compute_delegation_id(
            schema_version=schema_version,
            delegator=delegator,
            delegate=delegate,
            subject=subject,
            authority_ref=authority_ref,
            constraints=constraints,
            non_repudiation_ref=non_repudiation_ref,
            identity_mesh_ref=identity_mesh_ref,
            source_label=source_label,
            created_at=created_at,
            side_effects=side_effects,
        )
        if self.delegation_id not in ("", delegation_id):
            raise DelegationValidationError(
                "delegation_id does not match record content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="delegation_id",
            )
        record_hash = compute_record_hash(
            schema_version=schema_version,
            delegation_id=delegation_id,
            delegator=delegator,
            delegate=delegate,
            subject=subject,
            authority_ref=authority_ref,
            constraints=constraints,
            non_repudiation_ref=non_repudiation_ref,
            identity_mesh_ref=identity_mesh_ref,
            source_label=source_label,
            created_at=created_at,
            side_effects=side_effects,
        )
        if self.record_hash not in ("", record_hash):
            raise DelegationValidationError(
                "record_hash does not match record content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="record_hash",
            )
        object.__setattr__(self, "delegator", delegator)
        object.__setattr__(self, "delegate", delegate)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "authority_ref", authority_ref)
        object.__setattr__(self, "constraints", constraints)
        object.__setattr__(self, "non_repudiation_ref", non_repudiation_ref)
        object.__setattr__(self, "identity_mesh_ref", identity_mesh_ref)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_id", delegation_id)
        object.__setattr__(self, "record_hash", record_hash)
        object.__setattr__(self, "side_effects", side_effects)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_ref": self.authority_ref.to_canonical_dict(),
            "constraints": [item.to_canonical_dict() for item in self.constraints],
            "created_at": self.created_at,
            "delegate": self.delegate.to_canonical_dict(),
            "delegation_id": self.delegation_id,
            "delegator": self.delegator.to_canonical_dict(),
            "identity_mesh_ref": self.identity_mesh_ref.to_canonical_dict(),
            "non_repudiation_ref": self.non_repudiation_ref.to_canonical_dict(),
            "record_hash": self.record_hash,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
            "subject": self.subject.to_canonical_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationRecord:
        validate_known_fields(data, RECORD_KNOWN_FIELDS, label="delegation_record")
        return cls(
            delegator=data["delegator"],
            delegate=data["delegate"],
            subject=data["subject"],
            authority_ref=data["authority_ref"],
            constraints=data.get("constraints", ()),
            non_repudiation_ref=data["non_repudiation_ref"],
            identity_mesh_ref=data["identity_mesh_ref"],
            created_at=data["created_at"],
            source_label=data.get("source_label", DelegationSourceLabel.DEV_FIXTURE),
            schema_version=data.get("schema_version", DELEGATION_SCHEMA_VERSION),
            delegation_id=data.get("delegation_id", ""),
            record_hash=data.get("record_hash", ""),
            side_effects=data.get("side_effects", DelegationSideEffects()),
        )


@dataclass(frozen=True)
class DelegationFoundationStatus:
    """Declares foundation readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    capabilities: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationSideEffects = field(default_factory=DelegationSideEffects)
    schema_version: str = DELEGATION_FOUNDATION_STATUS_VERSION
    status_hash: str = ""

    def __post_init__(self) -> None:
        status_label = _parse_source_label(self.status_label)
        schema_version = _required_string(self.schema_version, field_name="schema_version")
        if schema_version != DELEGATION_FOUNDATION_STATUS_VERSION:
            raise DelegationValidationError(
                f"unsupported schema_version: {schema_version!r}",
                code=DelegationErrorCode.INVALID_VERSION,
                field="schema_version",
            )
        if not isinstance(self.capabilities, MappingABC):
            raise DelegationValidationError(
                "capabilities must be a mapping",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="capabilities",
            )
        if not isinstance(self.unavailable_bindings, MappingABC):
            raise DelegationValidationError(
                "unavailable_bindings must be a mapping",
                code=DelegationErrorCode.VALIDATION_ERROR,
                field="unavailable_bindings",
            )
        side_effects = (
            self.side_effects
            if isinstance(self.side_effects, DelegationSideEffects)
            else DelegationSideEffects.from_dict(self.side_effects)
        )
        capabilities = MappingProxyType(dict(self.capabilities))
        unavailable_bindings = MappingProxyType(dict(self.unavailable_bindings))
        status_hash = compute_foundation_status_hash(
            schema_version=schema_version,
            status_label=status_label,
            capabilities=capabilities,
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
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "unavailable_bindings", unavailable_bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "status_hash", status_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "capabilities": dict(
                sorted(self.capabilities.items(), key=lambda item: item[0])
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
    def from_dict(cls, data: Mapping[str, Any]) -> DelegationFoundationStatus:
        validate_known_fields(
            data,
            FOUNDATION_STATUS_KNOWN_FIELDS,
            label="delegation_foundation_status",
        )
        return cls(
            status_label=data["status_label"],
            capabilities=data["capabilities"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get("side_effects", DelegationSideEffects()),
            schema_version=data.get("schema_version", DELEGATION_FOUNDATION_STATUS_VERSION),
            status_hash=data.get("status_hash", ""),
        )


def build_delegation_actor_ref(
    actor_kind: DelegationActorKind | str,
    display_name: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationActorRef:
    """Build deterministic actor reference without authenticating the actor."""
    return DelegationActorRef(
        actor_kind=actor_kind,
        display_name=display_name,
        source_label=source_label,
    )


def build_delegation_subject(
    subject_kind: DelegationSubjectKind | str,
    subject_ref: str,
    *,
    description: str = "",
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationSubject:
    """Build deterministic delegation subject without approving action."""
    return DelegationSubject(
        subject_kind=subject_kind,
        subject_ref=subject_ref,
        description=description,
        source_label=source_label,
    )


def build_delegation_authority_ref(
    authority_kind: DelegationAuthorityKind | str,
    authority_basis: str,
    *,
    policy_context_ref: str | None = None,
    path_authority_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAuthorityRef:
    """Build authority context reference without granting authority."""
    return DelegationAuthorityRef(
        authority_kind=authority_kind,
        authority_basis=authority_basis,
        policy_context_ref=policy_context_ref,
        path_authority_ref=path_authority_ref,
        source_label=source_label,
    )


def build_delegation_constraint(
    constraint_kind: DelegationConstraintKind | str,
    constraint_value: str,
    *,
    required_review: bool = False,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationConstraint:
    """Build descriptive constraint without enforcing it."""
    return DelegationConstraint(
        constraint_kind=constraint_kind,
        constraint_value=constraint_value,
        required_review=required_review,
        source_label=source_label,
    )


def build_non_repudiation_ref(
    *,
    proof_status: NonRepudiationProofStatus = NonRepudiationProofStatus.REFERENCE_ONLY,
    evidence_ref: str | None = None,
    attestation_ref: str | None = None,
    signature_ref: str | None = None,
    trace_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> NonRepudiationRef:
    """Build reference-only non-repudiation hook without verifying proof."""
    return NonRepudiationRef(
        proof_status=proof_status,
        evidence_ref=evidence_ref,
        attestation_ref=attestation_ref,
        signature_ref=signature_ref,
        trace_ref=trace_ref,
        source_label=source_label,
    )


def build_agent_identity_mesh_ref(
    agent_ref: str,
    identity_ref: str,
    mesh_scope: str,
    *,
    relationship_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> AgentIdentityMeshRef:
    """Build identity mesh reference without resolving or activating mesh."""
    return AgentIdentityMeshRef(
        agent_ref=agent_ref,
        identity_ref=identity_ref,
        mesh_scope=mesh_scope,
        relationship_ref=relationship_ref,
        source_label=source_label,
    )


def build_delegation_record(
    delegator: DelegationActorRef | Mapping[str, Any],
    delegate: DelegationActorRef | Mapping[str, Any],
    subject: DelegationSubject | Mapping[str, Any],
    authority_ref: DelegationAuthorityRef | Mapping[str, Any],
    constraints: Sequence[DelegationConstraint | Mapping[str, Any]] | None,
    non_repudiation_ref: NonRepudiationRef | Mapping[str, Any],
    identity_mesh_ref: AgentIdentityMeshRef | Mapping[str, Any],
    *,
    created_at: str,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    delegation_id: str = "",
) -> DelegationRecord:
    """Build delegation record without authorizing, executing, or enforcing."""
    return DelegationRecord(
        delegator=delegator,
        delegate=delegate,
        subject=subject,
        authority_ref=authority_ref,
        constraints=constraints,
        non_repudiation_ref=non_repudiation_ref,
        identity_mesh_ref=identity_mesh_ref,
        created_at=created_at,
        source_label=source_label,
        delegation_id=delegation_id,
    )


def _default_foundation_capabilities() -> dict[str, str]:
    capabilities: dict[str, str] = {}
    for capability in FOUNDATION_AVAILABLE_CAPABILITIES:
        capabilities[capability.value] = DelegationSourceLabel.LIVE.value
    for capability in FOUNDATION_UNAVAILABLE_CAPABILITIES:
        capabilities[capability.value] = DelegationSourceLabel.UNAVAILABLE.value
    return capabilities


def build_delegation_foundation_status() -> DelegationFoundationStatus:
    """Return honest P1.8.0 foundation capability status (non-executing)."""
    return DelegationFoundationStatus(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        capabilities=_default_foundation_capabilities(),
        unavailable_bindings=DELEGATION_UNAVAILABLE_BINDINGS,
        side_effects=DelegationSideEffects(),
    )


def serialize_delegation_record(record: DelegationRecord) -> str:
    """Serialize delegation record to deterministic canonical JSON."""
    return to_canonical_json(record)


def hash_delegation_record(record: DelegationRecord) -> str:
    """Return stable record hash for delegation record content."""
    return record.record_hash
