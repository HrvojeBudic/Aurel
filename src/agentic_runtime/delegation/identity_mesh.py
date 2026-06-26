"""Delegation agent identity mesh reference binding (P1.8.6).

Deterministic, versioned, JSON-safe, side-effect-free agent identity mesh
reference-binding layer for delegation accountability. Binds reference-only
participant refs, relationship refs, mesh scope refs, identity mesh envelope,
readiness profile, and mesh relationship map to DelegationRef /
DelegationIdentity / DelegationRoleBindingSet / DelegationConstraintSet /
DelegationAuthorityBindingSet / DelegationNonRepudiationBindingSet without
resolving identity, authenticating participants, verifying relationships,
scoring trust, activating agents, granting authority, granting permission,
writing Ledger, writing global trace, or mutating runtime.

Architectural law:
  - AgentIdentityMeshRef exists does not mean identity is resolved.
  - ParticipantRef exists does not mean identity is authenticated.
  - RelationshipRef exists does not mean trust is verified.
  - IdentityMeshEnvelope exists does not mean live mesh exists.
  - MeshRelationshipMap exists does not mean graph engine exists.
  - MeshResolutionReadinessProfile exists does not mean trust score.
  - MeshScopeRef exists does not mean permission scope.
  - AgentRef exists does not mean agent is activated.
  - Mesh hash exists does not mean TRACE_VERIFIED.
  - identity_mesh_envelope_hash exists ≠ TRACE_VERIFIED.
  - identity_mesh_binding_set_hash exists ≠ proof of identity resolution.
  - DelegationMeshParticipantRef is a reference-only participant identity ref;
    it does not authenticate identity, resolve identity, or activate an agent.
  - DelegationMeshRelationshipRef is reference-only relationship metadata;
    it does not verify trust, prove relationship validity, or create a live
    graph edge.
  - DelegationMeshScopeRef is reference-only mesh scope context;
    it is not permission scope, data access scope, or authority grant.
  - DelegationIdentityMeshEnvelope is a reference packet;
    it is not identity resolution, not live mesh, not agent activation,
    not TRACE_VERIFIED.
  - DelegationMeshResolutionReadinessProfile is presence/absence information;
    it is not trust score, not identity resolution, not authority decision.
  - DelegationMeshRelationshipMap is reference-only relationship metadata;
    it is not graph engine, not trust graph, not live agent network.
  - DelegationIdentityMeshBinding binds identity mesh metadata;
    it is not identity resolution, not authentication, not trust verification,
    not authority grant, not permission grant, not agent activation,
    not trace verification.
  - DelegationIdentityMeshBindingSet describes identity mesh hooks;
    it does not resolve identity, activate agents, score trust, or write
    Ledger/global trace.
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

DELEGATION_IDENTITY_MESH_TASK_ID = "P1.8.6"
DELEGATION_MESH_PARTICIPANT_REF_VERSION = "delegation_mesh_participant_ref.v1"
DELEGATION_MESH_RELATIONSHIP_REF_VERSION = "delegation_mesh_relationship_ref.v1"
DELEGATION_MESH_SCOPE_REF_VERSION = "delegation_mesh_scope_ref.v1"
DELEGATION_IDENTITY_MESH_ENVELOPE_VERSION = "delegation_identity_mesh_envelope.v1"
DELEGATION_MESH_READINESS_PROFILE_VERSION = "delegation_mesh_readiness_profile.v1"
DELEGATION_MESH_RELATIONSHIP_MAP_VERSION = "delegation_mesh_relationship_map.v1"
DELEGATION_IDENTITY_MESH_BINDING_VERSION = "delegation_identity_mesh_binding.v1"
DELEGATION_IDENTITY_MESH_BINDING_SET_VERSION = "delegation_identity_mesh_binding_set.v1"
DELEGATION_IDENTITY_MESH_SIDE_EFFECTS_VERSION = "delegation_identity_mesh_side_effects.v1"
DELEGATION_IDENTITY_MESH_STATUS_REPORT_VERSION = "delegation_identity_mesh_status_report.v1"

DELEGATION_IDENTITY_MESH_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.6; "
        "identity mesh schema only"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.6 "
        "identity mesh reference binding"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.6 "
        "identity mesh reference binding"
    ),
    "Identity Resolver": (
        "Identity resolver scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Participant Authenticator": (
        "Participant authenticator scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Relationship Verifier": (
        "Relationship verifier scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Trust Scoring": (
        "Trust scoring scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Agent Activation": (
        "Agent activation scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Permission Grant": (
        "Permission grant is not available in P1.8.6; identity mesh refs are reference-only"
    ),
    "Authority Grant": (
        "Authority grant is not available in P1.8.6; identity mesh refs are reference-only"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Runtime Mesh Engine": (
        "Runtime mesh engine scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Live Agent Network": (
        "Live agent network scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Graph Database": (
        "Graph database scheduled for later P1.8 tasks; not P1.8.6"
    ),
    "Output Passport / P1.9": (
        "Output Passport is P1.9 scope; not P1.8.6"
    ),
    "P1.8.7 Scope / Boundary Model": (
        "P1.8.7 scope/boundary model is next; not P1.8.6"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.6"
    ),
}

PARTICIPANT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "participant_ref_id",
    "delegation_ref_id",
    "participant_kind",
    "participant_ref",
    "participant_label",
    "source_label",
    "mesh_ref_status",
    "participant_hash",
})

RELATIONSHIP_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "relationship_ref_id",
    "delegation_ref_id",
    "relationship_kind",
    "from_participant_ref_id",
    "to_participant_ref_id",
    "relationship_context_ref",
    "source_label",
    "mesh_ref_status",
    "relationship_hash",
})

MESH_SCOPE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "mesh_scope_ref_id",
    "delegation_ref_id",
    "mesh_scope_kind",
    "mesh_scope_ref",
    "source_label",
    "mesh_ref_status",
    "mesh_scope_hash",
})

MESH_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "identity_mesh_envelope_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "participant_refs",
    "relationship_refs",
    "mesh_scope_ref",
    "resolution_status",
    "source_label",
    "identity_mesh_envelope_hash",
})

READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "readiness_profile_id",
    "delegation_ref_id",
    "identity_mesh_envelope_hash",
    "has_operator_ref",
    "has_agent_ref",
    "has_system_ref",
    "has_service_ref",
    "has_role_ref",
    "has_subject_ref",
    "has_relationship_refs",
    "has_mesh_scope_ref",
    "has_authority_context",
    "has_evidence_context",
    "missing_components",
    "resolver_unavailable_reason",
    "source_label",
    "readiness_hash",
})

RELATIONSHIP_MAP_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "relationship_map_id",
    "delegation_ref_id",
    "participant_refs",
    "relationship_refs",
    "mesh_scope_ref",
    "source_label",
    "relationship_map_hash",
})

MESH_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "binding_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "identity_mesh_envelope_hash",
    "readiness_hash",
    "relationship_map_hash",
    "source_label",
    "resolution_status",
    "binding_hash",
})

MESH_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "identity_mesh_binding_set_id",
    "delegation_ref_id",
    "delegation_identity_hash",
    "role_binding_hash",
    "constraint_set_hash",
    "authority_binding_set_hash",
    "non_repudiation_binding_set_hash",
    "bindings",
    "source_label",
    "identity_mesh_binding_set_hash",
    "side_effects",
})

MESH_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "identity_resolved",
    "participant_authenticated",
    "relationship_verified",
    "trust_scored",
    "agent_activated",
    "authority_granted",
    "permission_granted",
    "policy_called",
    "custos_called",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

MESH_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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


class DelegationMeshParticipantKind(str, Enum):
    """Classifies the referenced identity mesh participant type.

    Participant kind classifies the identity reference type.
    It does not authenticate identity.
    It does not resolve identity.
    It does not activate an agent.
    """

    OPERATOR_REF = "OPERATOR_REF"
    AGENT_REF = "AGENT_REF"
    SYSTEM_REF = "SYSTEM_REF"
    SERVICE_REF = "SERVICE_REF"
    ROLE_REF = "ROLE_REF"
    SUBJECT_REF = "SUBJECT_REF"
    UNKNOWN = "UNKNOWN"


class DelegationMeshRelationshipKind(str, Enum):
    """Classifies a reference-only relationship between participant refs.

    Relationship kind classifies a reference-only relationship.
    It does not verify trust.
    It does not prove relationship validity.
    It does not create a live mesh edge.
    """

    DELEGATOR_TO_DELEGATE = "DELEGATOR_TO_DELEGATE"
    DELEGATE_TO_SUBJECT = "DELEGATE_TO_SUBJECT"
    OPERATOR_TO_AGENT = "OPERATOR_TO_AGENT"
    AGENT_TO_SERVICE = "AGENT_TO_SERVICE"
    SYSTEM_TO_AGENT = "SYSTEM_TO_AGENT"
    ROLE_TO_AGENT = "ROLE_TO_AGENT"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationMeshScopeKind(str, Enum):
    """Classifies where identity mesh context is declared.

    Mesh scope classifies where identity mesh context is declared.
    It is not permission scope.
    It is not data access scope.
    It is not authority grant.
    """

    DELEGATION_LOCAL = "DELEGATION_LOCAL"
    AGENT_LOCAL = "AGENT_LOCAL"
    SYSTEM_LOCAL = "SYSTEM_LOCAL"
    ORGANIZATION_LOCAL = "ORGANIZATION_LOCAL"
    TENANT_LOCAL = "TENANT_LOCAL"
    UNKNOWN = "UNKNOWN"


class DelegationMeshRefStatus(str, Enum):
    """Declared identity mesh reference availability.

    REFERENCE_ONLY means the mesh context is reference-only.
    DECLARED means mesh context was declared as metadata.
    Neither means identity is resolved, participant is authenticated,
    relationship is verified, trust is scored, or agent is activated.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationMeshResolutionStatus(str, Enum):
    """Mesh resolution status ladder.

    REFERENCE_ONLY is not resolved.
    RESOLUTION_UNAVAILABLE is not failure or success.
    RESOLVER_UNAVAILABLE is honest unavailability, not identity proof.
    NOT_RESOLVED means no identity resolution occurred.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    RESOLUTION_UNAVAILABLE = "RESOLUTION_UNAVAILABLE"
    RESOLVER_UNAVAILABLE = "RESOLVER_UNAVAILABLE"
    NOT_RESOLVED = "NOT_RESOLVED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Enum parsers
# ---------------------------------------------------------------------------


def _parse_mesh_participant_kind(
    value: DelegationMeshParticipantKind | str,
) -> DelegationMeshParticipantKind:
    if isinstance(value, DelegationMeshParticipantKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationMeshParticipantKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid participant_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="participant_kind",
            ) from exc
    raise DelegationError(
        "participant_kind must be a string or DelegationMeshParticipantKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="participant_kind",
    )


def _parse_mesh_relationship_kind(
    value: DelegationMeshRelationshipKind | str,
) -> DelegationMeshRelationshipKind:
    if isinstance(value, DelegationMeshRelationshipKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationMeshRelationshipKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid relationship_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="relationship_kind",
            ) from exc
    raise DelegationError(
        "relationship_kind must be a string or DelegationMeshRelationshipKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="relationship_kind",
    )


def _parse_mesh_scope_kind(
    value: DelegationMeshScopeKind | str,
) -> DelegationMeshScopeKind:
    if isinstance(value, DelegationMeshScopeKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationMeshScopeKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid mesh_scope_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="mesh_scope_kind",
            ) from exc
    raise DelegationError(
        "mesh_scope_kind must be a string or DelegationMeshScopeKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="mesh_scope_kind",
    )


def _parse_mesh_ref_status(
    value: DelegationMeshRefStatus | str,
) -> DelegationMeshRefStatus:
    if isinstance(value, DelegationMeshRefStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationMeshRefStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid mesh_ref_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="mesh_ref_status",
            ) from exc
    raise DelegationError(
        "mesh_ref_status must be a string or DelegationMeshRefStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="mesh_ref_status",
    )


def _parse_mesh_resolution_status(
    value: DelegationMeshResolutionStatus | str,
) -> DelegationMeshResolutionStatus:
    if isinstance(value, DelegationMeshResolutionStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationMeshResolutionStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid resolution_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="resolution_status",
            ) from exc
    raise DelegationError(
        "resolution_status must be a string or DelegationMeshResolutionStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="resolution_status",
    )


# ---------------------------------------------------------------------------
# DelegationMeshParticipantRef
# ---------------------------------------------------------------------------


def compute_mesh_participant_ref_hash(
    *,
    delegation_ref_id: str,
    participant_kind: DelegationMeshParticipantKind,
    participant_ref: str,
    participant_label: str,
    source_label: DelegationSourceLabel,
    mesh_ref_status: DelegationMeshRefStatus,
    schema_version: str = DELEGATION_MESH_PARTICIPANT_REF_VERSION,
) -> str:
    """Deterministic hash of participant ref content."""
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "mesh_ref_status": mesh_ref_status.value,
        "participant_kind": participant_kind.value,
        "participant_label": participant_label,
        "participant_ref": participant_ref,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationMeshParticipantRef:
    """One reference-only participant identity reference.

    ParticipantRef describes an identity reference.
    It does not authenticate identity.
    It does not resolve identity.
    It does not activate an agent.
    It does not grant authority or permission.
    """

    delegation_ref_id: str
    participant_kind: DelegationMeshParticipantKind
    participant_ref: str
    participant_label: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    mesh_ref_status: DelegationMeshRefStatus = DelegationMeshRefStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_MESH_PARTICIPANT_REF_VERSION
    participant_ref_id: str = ""
    participant_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        participant_kind = _parse_mesh_participant_kind(self.participant_kind)
        participant_ref = _required_string(
            self.participant_ref, field_name="participant_ref"
        )
        participant_label = _required_string(
            self.participant_label, field_name="participant_label"
        )
        source_label = _parse_source_label(self.source_label)
        mesh_ref_status = _parse_mesh_ref_status(self.mesh_ref_status)

        participant_hash = compute_mesh_participant_ref_hash(
            delegation_ref_id=delegation_ref_id,
            participant_kind=participant_kind,
            participant_ref=participant_ref,
            participant_label=participant_label,
            source_label=source_label,
            mesh_ref_status=mesh_ref_status,
            schema_version=schema_version,
        )
        participant_ref_id = f"mpr:{participant_hash[:16]}"

        if self.participant_hash not in ("", participant_hash):
            raise DelegationValidationError(
                "participant_hash does not match participant ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="participant_hash",
            )
        if self.participant_ref_id not in ("", participant_ref_id):
            raise DelegationValidationError(
                "participant_ref_id does not match participant ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="participant_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "participant_kind", participant_kind)
        object.__setattr__(self, "participant_ref", participant_ref)
        object.__setattr__(self, "participant_label", participant_label)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "mesh_ref_status", mesh_ref_status)
        object.__setattr__(self, "participant_hash", participant_hash)
        object.__setattr__(self, "participant_ref_id", participant_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "mesh_ref_status": self.mesh_ref_status.value,
            "participant_hash": self.participant_hash,
            "participant_kind": self.participant_kind.value,
            "participant_label": self.participant_label,
            "participant_ref": self.participant_ref,
            "participant_ref_id": self.participant_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationMeshParticipantRef:
        validate_known_fields(
            data,
            PARTICIPANT_REF_KNOWN_FIELDS,
            label="delegation_mesh_participant_ref",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            participant_kind=data["participant_kind"],
            participant_ref=data["participant_ref"],
            participant_label=data["participant_label"],
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            mesh_ref_status=data.get(
                "mesh_ref_status", DelegationMeshRefStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_MESH_PARTICIPANT_REF_VERSION
            ),
            participant_ref_id=data.get("participant_ref_id", ""),
            participant_hash=data.get("participant_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationMeshRelationshipRef
# ---------------------------------------------------------------------------


def compute_mesh_relationship_ref_hash(
    *,
    delegation_ref_id: str,
    relationship_kind: DelegationMeshRelationshipKind,
    from_participant_ref_id: str,
    to_participant_ref_id: str,
    relationship_context_ref: str | None,
    source_label: DelegationSourceLabel,
    mesh_ref_status: DelegationMeshRefStatus,
    schema_version: str = DELEGATION_MESH_RELATIONSHIP_REF_VERSION,
) -> str:
    """Deterministic hash of relationship ref content."""
    payload: dict[str, Any] = {
        "delegation_ref_id": delegation_ref_id,
        "from_participant_ref_id": from_participant_ref_id,
        "mesh_ref_status": mesh_ref_status.value,
        "relationship_kind": relationship_kind.value,
        "schema_version": schema_version,
        "source_label": source_label.value,
        "to_participant_ref_id": to_participant_ref_id,
    }
    if relationship_context_ref is not None:
        payload["relationship_context_ref"] = relationship_context_ref
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationMeshRelationshipRef:
    """One reference-only relationship between participant refs.

    RelationshipRef describes declared relationship metadata.
    It does not verify trust.
    It does not prove relationship validity.
    It does not create a live graph edge.
    It does not activate a mesh.
    """

    delegation_ref_id: str
    relationship_kind: DelegationMeshRelationshipKind
    from_participant_ref_id: str
    to_participant_ref_id: str
    relationship_context_ref: str | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    mesh_ref_status: DelegationMeshRefStatus = DelegationMeshRefStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_MESH_RELATIONSHIP_REF_VERSION
    relationship_ref_id: str = ""
    relationship_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        relationship_kind = _parse_mesh_relationship_kind(self.relationship_kind)
        from_participant_ref_id = _required_string(
            self.from_participant_ref_id,
            field_name="from_participant_ref_id",
        )
        to_participant_ref_id = _required_string(
            self.to_participant_ref_id, field_name="to_participant_ref_id"
        )
        relationship_context_ref = _optional_string(
            self.relationship_context_ref
        )
        source_label = _parse_source_label(self.source_label)
        mesh_ref_status = _parse_mesh_ref_status(self.mesh_ref_status)

        relationship_hash = compute_mesh_relationship_ref_hash(
            delegation_ref_id=delegation_ref_id,
            relationship_kind=relationship_kind,
            from_participant_ref_id=from_participant_ref_id,
            to_participant_ref_id=to_participant_ref_id,
            relationship_context_ref=relationship_context_ref,
            source_label=source_label,
            mesh_ref_status=mesh_ref_status,
            schema_version=schema_version,
        )
        relationship_ref_id = f"mrel:{relationship_hash[:16]}"

        if self.relationship_hash not in ("", relationship_hash):
            raise DelegationValidationError(
                "relationship_hash does not match relationship ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="relationship_hash",
            )
        if self.relationship_ref_id not in ("", relationship_ref_id):
            raise DelegationValidationError(
                "relationship_ref_id does not match relationship ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="relationship_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "relationship_kind", relationship_kind)
        object.__setattr__(
            self, "from_participant_ref_id", from_participant_ref_id
        )
        object.__setattr__(
            self, "to_participant_ref_id", to_participant_ref_id
        )
        object.__setattr__(
            self, "relationship_context_ref", relationship_context_ref
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "mesh_ref_status", mesh_ref_status)
        object.__setattr__(self, "relationship_hash", relationship_hash)
        object.__setattr__(self, "relationship_ref_id", relationship_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "delegation_ref_id": self.delegation_ref_id,
            "from_participant_ref_id": self.from_participant_ref_id,
            "mesh_ref_status": self.mesh_ref_status.value,
            "relationship_hash": self.relationship_hash,
            "relationship_kind": self.relationship_kind.value,
            "relationship_ref_id": self.relationship_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
            "to_participant_ref_id": self.to_participant_ref_id,
        }
        if self.relationship_context_ref is not None:
            payload["relationship_context_ref"] = (
                self.relationship_context_ref
            )
        return payload

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationMeshRelationshipRef:
        validate_known_fields(
            data,
            RELATIONSHIP_REF_KNOWN_FIELDS,
            label="delegation_mesh_relationship_ref",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            relationship_kind=data["relationship_kind"],
            from_participant_ref_id=data["from_participant_ref_id"],
            to_participant_ref_id=data["to_participant_ref_id"],
            relationship_context_ref=data.get("relationship_context_ref"),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            mesh_ref_status=data.get(
                "mesh_ref_status", DelegationMeshRefStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_MESH_RELATIONSHIP_REF_VERSION,
            ),
            relationship_ref_id=data.get("relationship_ref_id", ""),
            relationship_hash=data.get("relationship_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationMeshScopeRef
# ---------------------------------------------------------------------------


def compute_mesh_scope_ref_hash(
    *,
    delegation_ref_id: str,
    mesh_scope_kind: DelegationMeshScopeKind,
    mesh_scope_ref: str,
    source_label: DelegationSourceLabel,
    mesh_ref_status: DelegationMeshRefStatus,
    schema_version: str = DELEGATION_MESH_SCOPE_REF_VERSION,
) -> str:
    """Deterministic hash of mesh scope ref content."""
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "mesh_ref_status": mesh_ref_status.value,
        "mesh_scope_kind": mesh_scope_kind.value,
        "mesh_scope_ref": mesh_scope_ref,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationMeshScopeRef:
    """One reference-only mesh scope context.

    MeshScopeRef describes where identity mesh context applies.
    It is not permission scope.
    It is not data access scope.
    It is not authority grant.
    """

    delegation_ref_id: str
    mesh_scope_kind: DelegationMeshScopeKind
    mesh_scope_ref: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    mesh_ref_status: DelegationMeshRefStatus = DelegationMeshRefStatus.REFERENCE_ONLY
    schema_version: str = DELEGATION_MESH_SCOPE_REF_VERSION
    mesh_scope_ref_id: str = ""
    mesh_scope_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        mesh_scope_kind = _parse_mesh_scope_kind(self.mesh_scope_kind)
        mesh_scope_ref = _required_string(
            self.mesh_scope_ref, field_name="mesh_scope_ref"
        )
        source_label = _parse_source_label(self.source_label)
        mesh_ref_status = _parse_mesh_ref_status(self.mesh_ref_status)

        mesh_scope_hash = compute_mesh_scope_ref_hash(
            delegation_ref_id=delegation_ref_id,
            mesh_scope_kind=mesh_scope_kind,
            mesh_scope_ref=mesh_scope_ref,
            source_label=source_label,
            mesh_ref_status=mesh_ref_status,
            schema_version=schema_version,
        )
        mesh_scope_ref_id = f"msr:{mesh_scope_hash[:16]}"

        if self.mesh_scope_hash not in ("", mesh_scope_hash):
            raise DelegationValidationError(
                "mesh_scope_hash does not match mesh scope ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="mesh_scope_hash",
            )
        if self.mesh_scope_ref_id not in ("", mesh_scope_ref_id):
            raise DelegationValidationError(
                "mesh_scope_ref_id does not match mesh scope ref content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="mesh_scope_ref_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "mesh_scope_kind", mesh_scope_kind)
        object.__setattr__(self, "mesh_scope_ref", mesh_scope_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "mesh_ref_status", mesh_ref_status)
        object.__setattr__(self, "mesh_scope_hash", mesh_scope_hash)
        object.__setattr__(self, "mesh_scope_ref_id", mesh_scope_ref_id)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "mesh_ref_status": self.mesh_ref_status.value,
            "mesh_scope_hash": self.mesh_scope_hash,
            "mesh_scope_kind": self.mesh_scope_kind.value,
            "mesh_scope_ref": self.mesh_scope_ref,
            "mesh_scope_ref_id": self.mesh_scope_ref_id,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationMeshScopeRef:
        validate_known_fields(
            data,
            MESH_SCOPE_REF_KNOWN_FIELDS,
            label="delegation_mesh_scope_ref",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            mesh_scope_kind=data["mesh_scope_kind"],
            mesh_scope_ref=data["mesh_scope_ref"],
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            mesh_ref_status=data.get(
                "mesh_ref_status", DelegationMeshRefStatus.REFERENCE_ONLY
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_MESH_SCOPE_REF_VERSION
            ),
            mesh_scope_ref_id=data.get("mesh_scope_ref_id", ""),
            mesh_scope_hash=data.get("mesh_scope_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationIdentityMeshEnvelope
# ---------------------------------------------------------------------------


def _order_mesh_participant_refs(
    refs: Sequence[DelegationMeshParticipantRef],
) -> tuple[DelegationMeshParticipantRef, ...]:
    """Deterministic ordering by participant_ref_id."""
    return tuple(sorted(refs, key=lambda pr: pr.participant_ref_id))


def _order_mesh_relationship_refs(
    refs: Sequence[DelegationMeshRelationshipRef],
) -> tuple[DelegationMeshRelationshipRef, ...]:
    """Deterministic ordering by relationship_ref_id."""
    return tuple(sorted(refs, key=lambda rr: rr.relationship_ref_id))


def compute_identity_mesh_envelope_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    participant_refs: tuple[DelegationMeshParticipantRef, ...],
    relationship_refs: tuple[DelegationMeshRelationshipRef, ...],
    mesh_scope_ref: DelegationMeshScopeRef | None,
    resolution_status: DelegationMeshResolutionStatus,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_IDENTITY_MESH_ENVELOPE_VERSION,
) -> str:
    """Deterministic hash of the full identity mesh envelope."""
    payload: dict[str, Any] = {
        "authority_binding_set_hash": authority_binding_set_hash,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "participant_refs": [
            pr.to_canonical_dict() for pr in participant_refs
        ],
        "relationship_refs": [
            rr.to_canonical_dict() for rr in relationship_refs
        ],
        "resolution_status": resolution_status.value,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if mesh_scope_ref is not None:
        payload["mesh_scope_ref"] = mesh_scope_ref.to_canonical_dict()
    else:
        payload["mesh_scope_ref"] = None
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationIdentityMeshEnvelope:
    """Deterministic packet of participant refs, relationship refs,
       and mesh scope refs for one delegation context.

    IdentityMeshEnvelope is a reference packet.
    It is not identity resolution.
    It is not live mesh.
    It is not agent activation.
    It is not TRACE_VERIFIED.
    It does not authenticate participants, verify relationships, score trust,
    grant authority, grant permission, or mutate runtime.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    participant_refs: tuple[DelegationMeshParticipantRef, ...] = ()
    relationship_refs: tuple[DelegationMeshRelationshipRef, ...] = ()
    mesh_scope_ref: DelegationMeshScopeRef | None = None
    resolution_status: DelegationMeshResolutionStatus = (
        DelegationMeshResolutionStatus.REFERENCE_ONLY
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_IDENTITY_MESH_ENVELOPE_VERSION
    identity_mesh_envelope_id: str = ""
    identity_mesh_envelope_hash: str = ""

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
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash,
            field_name="authority_binding_set_hash",
        )
        non_repudiation_binding_set_hash = _required_string(
            self.non_repudiation_binding_set_hash,
            field_name="non_repudiation_binding_set_hash",
        )
        resolution_status = _parse_mesh_resolution_status(
            self.resolution_status
        )
        source_label = _parse_source_label(self.source_label)

        participant_refs = _order_mesh_participant_refs(
            tuple(
                pr
                if isinstance(pr, DelegationMeshParticipantRef)
                else DelegationMeshParticipantRef.from_dict(pr)
                for pr in self.participant_refs
            )
        )
        relationship_refs = _order_mesh_relationship_refs(
            tuple(
                rr
                if isinstance(rr, DelegationMeshRelationshipRef)
                else DelegationMeshRelationshipRef.from_dict(rr)
                for rr in self.relationship_refs
            )
        )
        mesh_scope_ref = self.mesh_scope_ref
        if mesh_scope_ref is not None and not isinstance(
            mesh_scope_ref, DelegationMeshScopeRef
        ):
            mesh_scope_ref = DelegationMeshScopeRef.from_dict(mesh_scope_ref)

        identity_mesh_envelope_hash = compute_identity_mesh_envelope_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            participant_refs=participant_refs,
            relationship_refs=relationship_refs,
            mesh_scope_ref=mesh_scope_ref,
            resolution_status=resolution_status,
            source_label=source_label,
            schema_version=schema_version,
        )
        identity_mesh_envelope_id = f"ime:{identity_mesh_envelope_hash[:16]}"

        if self.identity_mesh_envelope_hash not in (
            "",
            identity_mesh_envelope_hash,
        ):
            raise DelegationValidationError(
                "identity_mesh_envelope_hash does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="identity_mesh_envelope_hash",
            )
        if self.identity_mesh_envelope_id not in (
            "",
            identity_mesh_envelope_id,
        ):
            raise DelegationValidationError(
                "identity_mesh_envelope_id does not match envelope content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="identity_mesh_envelope_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
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
            self,
            "non_repudiation_binding_set_hash",
            non_repudiation_binding_set_hash,
        )
        object.__setattr__(self, "participant_refs", participant_refs)
        object.__setattr__(self, "relationship_refs", relationship_refs)
        object.__setattr__(self, "mesh_scope_ref", mesh_scope_ref)
        object.__setattr__(self, "resolution_status", resolution_status)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self, "identity_mesh_envelope_hash", identity_mesh_envelope_hash
        )
        object.__setattr__(
            self, "identity_mesh_envelope_id", identity_mesh_envelope_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_envelope_hash": self.identity_mesh_envelope_hash,
            "identity_mesh_envelope_id": self.identity_mesh_envelope_id,
            "non_repudiation_binding_set_hash": (
                self.non_repudiation_binding_set_hash
            ),
            "participant_refs": [
                pr.to_canonical_dict() for pr in self.participant_refs
            ],
            "relationship_refs": [
                rr.to_canonical_dict() for rr in self.relationship_refs
            ],
            "resolution_status": self.resolution_status.value,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.mesh_scope_ref is not None:
            payload["mesh_scope_ref"] = (
                self.mesh_scope_ref.to_canonical_dict()
            )
        else:
            payload["mesh_scope_ref"] = None
        return payload

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationIdentityMeshEnvelope:
        validate_known_fields(
            data,
            MESH_ENVELOPE_KNOWN_FIELDS,
            label="delegation_identity_mesh_envelope",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data[
                "non_repudiation_binding_set_hash"
            ],
            participant_refs=data.get("participant_refs", ()),
            relationship_refs=data.get("relationship_refs", ()),
            mesh_scope_ref=data.get("mesh_scope_ref"),
            resolution_status=data.get(
                "resolution_status",
                DelegationMeshResolutionStatus.REFERENCE_ONLY,
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_IDENTITY_MESH_ENVELOPE_VERSION
            ),
            identity_mesh_envelope_id=data.get(
                "identity_mesh_envelope_id", ""
            ),
            identity_mesh_envelope_hash=data.get(
                "identity_mesh_envelope_hash", ""
            ),
        )


# ---------------------------------------------------------------------------
# DelegationMeshResolutionReadinessProfile
# ---------------------------------------------------------------------------


def compute_mesh_readiness_profile_hash(
    *,
    delegation_ref_id: str,
    identity_mesh_envelope_hash: str,
    has_operator_ref: bool,
    has_agent_ref: bool,
    has_system_ref: bool,
    has_service_ref: bool,
    has_role_ref: bool,
    has_subject_ref: bool,
    has_relationship_refs: bool,
    has_mesh_scope_ref: bool,
    has_authority_context: bool,
    has_evidence_context: bool,
    missing_components: tuple[str, ...],
    resolver_unavailable_reason: str,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_MESH_READINESS_PROFILE_VERSION,
) -> str:
    """Deterministic hash of mesh resolution readiness profile."""
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
        "has_agent_ref": has_agent_ref,
        "has_authority_context": has_authority_context,
        "has_evidence_context": has_evidence_context,
        "has_mesh_scope_ref": has_mesh_scope_ref,
        "has_operator_ref": has_operator_ref,
        "has_relationship_refs": has_relationship_refs,
        "has_role_ref": has_role_ref,
        "has_service_ref": has_service_ref,
        "has_subject_ref": has_subject_ref,
        "has_system_ref": has_system_ref,
        "identity_mesh_envelope_hash": identity_mesh_envelope_hash,
        "missing_components": list(missing_components),
        "resolver_unavailable_reason": resolver_unavailable_reason,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationMeshResolutionReadinessProfile:
    """Present/missing identity mesh component profile, not trust score.

    ReadinessProfile is not identity resolution.
    ReadinessProfile is not trust score.
    ReadinessProfile is not authority.
    ReadinessProfile is not permission.
    ReadinessProfile is not agent activation.
    """

    delegation_ref_id: str
    identity_mesh_envelope_hash: str
    has_operator_ref: bool = False
    has_agent_ref: bool = False
    has_system_ref: bool = False
    has_service_ref: bool = False
    has_role_ref: bool = False
    has_subject_ref: bool = False
    has_relationship_refs: bool = False
    has_mesh_scope_ref: bool = False
    has_authority_context: bool = False
    has_evidence_context: bool = False
    missing_components: tuple[str, ...] = ()
    resolver_unavailable_reason: str = "identity mesh resolver not available in P1.8.6"
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_MESH_READINESS_PROFILE_VERSION
    readiness_profile_id: str = ""
    readiness_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        identity_mesh_envelope_hash = _required_string(
            self.identity_mesh_envelope_hash,
            field_name="identity_mesh_envelope_hash",
        )
        source_label = _parse_source_label(self.source_label)

        for name in (
            "has_operator_ref",
            "has_agent_ref",
            "has_system_ref",
            "has_service_ref",
            "has_role_ref",
            "has_subject_ref",
            "has_relationship_refs",
            "has_mesh_scope_ref",
            "has_authority_context",
            "has_evidence_context",
        ):
            if not isinstance(getattr(self, name), bool):
                raise DelegationValidationError(
                    f"{name} must be boolean",
                    code=DelegationErrorCode.VALIDATION_ERROR,
                    field=name,
                )

        resolver_unavailable_reason = _required_string(
            self.resolver_unavailable_reason,
            field_name="resolver_unavailable_reason",
        )
        missing_components = tuple(
            sorted(str(m) for m in self.missing_components)
        )

        readiness_hash = compute_mesh_readiness_profile_hash(
            delegation_ref_id=delegation_ref_id,
            identity_mesh_envelope_hash=identity_mesh_envelope_hash,
            has_operator_ref=self.has_operator_ref,
            has_agent_ref=self.has_agent_ref,
            has_system_ref=self.has_system_ref,
            has_service_ref=self.has_service_ref,
            has_role_ref=self.has_role_ref,
            has_subject_ref=self.has_subject_ref,
            has_relationship_refs=self.has_relationship_refs,
            has_mesh_scope_ref=self.has_mesh_scope_ref,
            has_authority_context=self.has_authority_context,
            has_evidence_context=self.has_evidence_context,
            missing_components=missing_components,
            resolver_unavailable_reason=resolver_unavailable_reason,
            source_label=source_label,
            schema_version=schema_version,
        )
        readiness_profile_id = f"mrp:{readiness_hash[:16]}"

        if self.readiness_hash not in ("", readiness_hash):
            raise DelegationValidationError(
                "readiness_hash does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="readiness_hash",
            )
        if self.readiness_profile_id not in ("", readiness_profile_id):
            raise DelegationValidationError(
                "readiness_profile_id does not match profile content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="readiness_profile_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(
            self, "identity_mesh_envelope_hash", identity_mesh_envelope_hash
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self,
            "resolver_unavailable_reason",
            resolver_unavailable_reason,
        )
        object.__setattr__(self, "missing_components", missing_components)
        object.__setattr__(self, "readiness_hash", readiness_hash)
        object.__setattr__(
            self, "readiness_profile_id", readiness_profile_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "delegation_ref_id": self.delegation_ref_id,
            "has_agent_ref": self.has_agent_ref,
            "has_authority_context": self.has_authority_context,
            "has_evidence_context": self.has_evidence_context,
            "has_mesh_scope_ref": self.has_mesh_scope_ref,
            "has_operator_ref": self.has_operator_ref,
            "has_relationship_refs": self.has_relationship_refs,
            "has_role_ref": self.has_role_ref,
            "has_service_ref": self.has_service_ref,
            "has_subject_ref": self.has_subject_ref,
            "has_system_ref": self.has_system_ref,
            "identity_mesh_envelope_hash": self.identity_mesh_envelope_hash,
            "missing_components": list(self.missing_components),
            "readiness_hash": self.readiness_hash,
            "readiness_profile_id": self.readiness_profile_id,
            "resolver_unavailable_reason": (
                self.resolver_unavailable_reason
            ),
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationMeshResolutionReadinessProfile:
        validate_known_fields(
            data,
            READINESS_PROFILE_KNOWN_FIELDS,
            label="delegation_mesh_resolution_readiness_profile",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            identity_mesh_envelope_hash=data["identity_mesh_envelope_hash"],
            has_operator_ref=data.get("has_operator_ref", False),
            has_agent_ref=data.get("has_agent_ref", False),
            has_system_ref=data.get("has_system_ref", False),
            has_service_ref=data.get("has_service_ref", False),
            has_role_ref=data.get("has_role_ref", False),
            has_subject_ref=data.get("has_subject_ref", False),
            has_relationship_refs=data.get("has_relationship_refs", False),
            has_mesh_scope_ref=data.get("has_mesh_scope_ref", False),
            has_authority_context=data.get("has_authority_context", False),
            has_evidence_context=data.get("has_evidence_context", False),
            missing_components=data.get("missing_components", ()),
            resolver_unavailable_reason=data.get(
                "resolver_unavailable_reason",
                "identity mesh resolver not available in P1.8.6",
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_MESH_READINESS_PROFILE_VERSION
            ),
            readiness_profile_id=data.get("readiness_profile_id", ""),
            readiness_hash=data.get("readiness_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationMeshRelationshipMap
# ---------------------------------------------------------------------------


def compute_mesh_relationship_map_hash(
    *,
    delegation_ref_id: str,
    participant_refs: tuple[DelegationMeshParticipantRef, ...],
    relationship_refs: tuple[DelegationMeshRelationshipRef, ...],
    mesh_scope_ref: DelegationMeshScopeRef | None,
    source_label: DelegationSourceLabel,
    schema_version: str = DELEGATION_MESH_RELATIONSHIP_MAP_VERSION,
) -> str:
    """Deterministic hash of mesh relationship map."""
    payload: dict[str, Any] = {
        "delegation_ref_id": delegation_ref_id,
        "participant_refs": [
            pr.to_canonical_dict() for pr in participant_refs
        ],
        "relationship_refs": [
            rr.to_canonical_dict() for rr in relationship_refs
        ],
        "schema_version": schema_version,
        "source_label": source_label.value,
    }
    if mesh_scope_ref is not None:
        payload["mesh_scope_ref"] = mesh_scope_ref.to_canonical_dict()
    else:
        payload["mesh_scope_ref"] = None
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationMeshRelationshipMap:
    """Reference-only relationship map, not graph engine.

    MeshRelationshipMap is not graph engine.
    MeshRelationshipMap is not trust graph.
    MeshRelationshipMap is not identity resolver.
    MeshRelationshipMap is not live agent network.
    """

    delegation_ref_id: str
    participant_refs: tuple[DelegationMeshParticipantRef, ...] = ()
    relationship_refs: tuple[DelegationMeshRelationshipRef, ...] = ()
    mesh_scope_ref: DelegationMeshScopeRef | None = None
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_MESH_RELATIONSHIP_MAP_VERSION
    relationship_map_id: str = ""
    relationship_map_hash: str = ""

    def __post_init__(self) -> None:
        schema_version = _required_string(
            self.schema_version, field_name="schema_version"
        )
        delegation_ref_id = _required_string(
            self.delegation_ref_id, field_name="delegation_ref_id"
        )
        source_label = _parse_source_label(self.source_label)

        participant_refs = _order_mesh_participant_refs(
            tuple(
                pr
                if isinstance(pr, DelegationMeshParticipantRef)
                else DelegationMeshParticipantRef.from_dict(pr)
                for pr in self.participant_refs
            )
        )
        relationship_refs = _order_mesh_relationship_refs(
            tuple(
                rr
                if isinstance(rr, DelegationMeshRelationshipRef)
                else DelegationMeshRelationshipRef.from_dict(rr)
                for rr in self.relationship_refs
            )
        )
        mesh_scope_ref = self.mesh_scope_ref
        if mesh_scope_ref is not None and not isinstance(
            mesh_scope_ref, DelegationMeshScopeRef
        ):
            mesh_scope_ref = DelegationMeshScopeRef.from_dict(mesh_scope_ref)

        relationship_map_hash = compute_mesh_relationship_map_hash(
            delegation_ref_id=delegation_ref_id,
            participant_refs=participant_refs,
            relationship_refs=relationship_refs,
            mesh_scope_ref=mesh_scope_ref,
            source_label=source_label,
            schema_version=schema_version,
        )
        relationship_map_id = f"mrm:{relationship_map_hash[:16]}"

        if self.relationship_map_hash not in ("", relationship_map_hash):
            raise DelegationValidationError(
                "relationship_map_hash does not match map content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="relationship_map_hash",
            )
        if self.relationship_map_id not in ("", relationship_map_id):
            raise DelegationValidationError(
                "relationship_map_id does not match map content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="relationship_map_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "delegation_ref_id", delegation_ref_id)
        object.__setattr__(self, "participant_refs", participant_refs)
        object.__setattr__(self, "relationship_refs", relationship_refs)
        object.__setattr__(self, "mesh_scope_ref", mesh_scope_ref)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self, "relationship_map_hash", relationship_map_hash
        )
        object.__setattr__(
            self, "relationship_map_id", relationship_map_id
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "delegation_ref_id": self.delegation_ref_id,
            "participant_refs": [
                pr.to_canonical_dict() for pr in self.participant_refs
            ],
            "relationship_map_hash": self.relationship_map_hash,
            "relationship_map_id": self.relationship_map_id,
            "relationship_refs": [
                rr.to_canonical_dict() for rr in self.relationship_refs
            ],
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }
        if self.mesh_scope_ref is not None:
            payload["mesh_scope_ref"] = (
                self.mesh_scope_ref.to_canonical_dict()
            )
        else:
            payload["mesh_scope_ref"] = None
        return payload

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationMeshRelationshipMap:
        validate_known_fields(
            data,
            RELATIONSHIP_MAP_KNOWN_FIELDS,
            label="delegation_mesh_relationship_map",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            participant_refs=data.get("participant_refs", ()),
            relationship_refs=data.get("relationship_refs", ()),
            mesh_scope_ref=data.get("mesh_scope_ref"),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_MESH_RELATIONSHIP_MAP_VERSION
            ),
            relationship_map_id=data.get("relationship_map_id", ""),
            relationship_map_hash=data.get("relationship_map_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationIdentityMeshBinding
# ---------------------------------------------------------------------------


def compute_identity_mesh_binding_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_envelope_hash: str,
    readiness_hash: str,
    relationship_map_hash: str,
    source_label: DelegationSourceLabel,
    resolution_status: DelegationMeshResolutionStatus,
    schema_version: str = DELEGATION_IDENTITY_MESH_BINDING_VERSION,
) -> str:
    """Deterministic hash of identity mesh binding."""
    return stable_hash({
        "authority_binding_set_hash": authority_binding_set_hash,
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "identity_mesh_envelope_hash": identity_mesh_envelope_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "readiness_hash": readiness_hash,
        "relationship_map_hash": relationship_map_hash,
        "resolution_status": resolution_status.value,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "source_label": source_label.value,
    })


@dataclass(frozen=True)
class DelegationIdentityMeshBinding:
    """Binding between identity mesh envelope and delegation
       identity/role/constraint/authority/evidence context.

    IdentityMeshBinding binds identity mesh metadata.
    It is not identity resolution.
    It is not authentication.
    It is not trust verification.
    It is not authority grant.
    It is not permission grant.
    It is not agent activation.
    It is not trace verification.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    identity_mesh_envelope_hash: str
    readiness_hash: str
    relationship_map_hash: str
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    resolution_status: DelegationMeshResolutionStatus = (
        DelegationMeshResolutionStatus.REFERENCE_ONLY
    )
    schema_version: str = DELEGATION_IDENTITY_MESH_BINDING_VERSION
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
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash,
            field_name="authority_binding_set_hash",
        )
        non_repudiation_binding_set_hash = _required_string(
            self.non_repudiation_binding_set_hash,
            field_name="non_repudiation_binding_set_hash",
        )
        identity_mesh_envelope_hash = _required_string(
            self.identity_mesh_envelope_hash,
            field_name="identity_mesh_envelope_hash",
        )
        readiness_hash = _required_string(
            self.readiness_hash, field_name="readiness_hash"
        )
        relationship_map_hash = _required_string(
            self.relationship_map_hash, field_name="relationship_map_hash"
        )
        source_label = _parse_source_label(self.source_label)
        resolution_status = _parse_mesh_resolution_status(
            self.resolution_status
        )

        binding_hash = compute_identity_mesh_binding_hash(
            delegation_ref_id=delegation_ref_id,
            delegation_identity_hash=delegation_identity_hash,
            role_binding_hash=role_binding_hash,
            constraint_set_hash=constraint_set_hash,
            authority_binding_set_hash=authority_binding_set_hash,
            non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
            identity_mesh_envelope_hash=identity_mesh_envelope_hash,
            readiness_hash=readiness_hash,
            relationship_map_hash=relationship_map_hash,
            source_label=source_label,
            resolution_status=resolution_status,
            schema_version=schema_version,
        )
        binding_id = f"imbind:{binding_hash[:16]}"

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
        object.__setattr__(
            self, "authority_binding_set_hash", authority_binding_set_hash
        )
        object.__setattr__(
            self,
            "non_repudiation_binding_set_hash",
            non_repudiation_binding_set_hash,
        )
        object.__setattr__(
            self, "identity_mesh_envelope_hash", identity_mesh_envelope_hash
        )
        object.__setattr__(self, "readiness_hash", readiness_hash)
        object.__setattr__(
            self, "relationship_map_hash", relationship_map_hash
        )
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(self, "resolution_status", resolution_status)
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
            "identity_mesh_envelope_hash": (
                self.identity_mesh_envelope_hash
            ),
            "non_repudiation_binding_set_hash": (
                self.non_repudiation_binding_set_hash
            ),
            "readiness_hash": self.readiness_hash,
            "relationship_map_hash": self.relationship_map_hash,
            "resolution_status": self.resolution_status.value,
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationIdentityMeshBinding:
        validate_known_fields(
            data,
            MESH_BINDING_KNOWN_FIELDS,
            label="delegation_identity_mesh_binding",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data[
                "non_repudiation_binding_set_hash"
            ],
            identity_mesh_envelope_hash=data[
                "identity_mesh_envelope_hash"
            ],
            readiness_hash=data["readiness_hash"],
            relationship_map_hash=data["relationship_map_hash"],
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            resolution_status=data.get(
                "resolution_status",
                DelegationMeshResolutionStatus.REFERENCE_ONLY,
            ),
            schema_version=data.get(
                "schema_version", DELEGATION_IDENTITY_MESH_BINDING_VERSION
            ),
            binding_id=data.get("binding_id", ""),
            binding_hash=data.get("binding_hash", ""),
        )


# ---------------------------------------------------------------------------
# DelegationIdentityMeshBindingSet
# ---------------------------------------------------------------------------


def _order_identity_mesh_bindings(
    bindings: Sequence[DelegationIdentityMeshBinding],
) -> tuple[DelegationIdentityMeshBinding, ...]:
    """Deterministic ordering by binding_id."""
    return tuple(sorted(bindings, key=lambda b: b.binding_id))


def compute_identity_mesh_binding_set_hash(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    bindings: tuple[DelegationIdentityMeshBinding, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationIdentityMeshSideEffects,
    schema_version: str = DELEGATION_IDENTITY_MESH_BINDING_SET_VERSION,
) -> str:
    """Deterministic hash of the full identity mesh binding set."""
    payload: dict[str, Any] = {
        "authority_binding_set_hash": authority_binding_set_hash,
        "bindings": [b.to_canonical_dict() for b in bindings],
        "constraint_set_hash": constraint_set_hash,
        "delegation_identity_hash": delegation_identity_hash,
        "delegation_ref_id": delegation_ref_id,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "role_binding_hash": role_binding_hash,
        "schema_version": schema_version,
        "side_effects": side_effects.to_canonical_dict(),
        "source_label": source_label.value,
    }
    return stable_hash(payload)


@dataclass(frozen=True)
class DelegationIdentityMeshBindingSet:
    """Collection of identity mesh bindings for one delegation.

    IdentityMeshBindingSet describes identity mesh hooks.
    It does not resolve identity.
    It does not activate agents.
    It does not score trust.
    It does not write Ledger/global trace.
    """

    delegation_ref_id: str
    delegation_identity_hash: str
    role_binding_hash: str
    constraint_set_hash: str
    authority_binding_set_hash: str
    non_repudiation_binding_set_hash: str
    bindings: tuple[DelegationIdentityMeshBinding, ...] = ()
    side_effects: DelegationIdentityMeshSideEffects = field(
        default_factory=lambda: DelegationIdentityMeshSideEffects()
    )
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE
    schema_version: str = DELEGATION_IDENTITY_MESH_BINDING_SET_VERSION
    identity_mesh_binding_set_id: str = ""
    identity_mesh_binding_set_hash: str = ""

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
        authority_binding_set_hash = _required_string(
            self.authority_binding_set_hash,
            field_name="authority_binding_set_hash",
        )
        non_repudiation_binding_set_hash = _required_string(
            self.non_repudiation_binding_set_hash,
            field_name="non_repudiation_binding_set_hash",
        )
        source_label = _parse_source_label(self.source_label)

        bindings = _order_identity_mesh_bindings(
            tuple(
                b
                if isinstance(b, DelegationIdentityMeshBinding)
                else DelegationIdentityMeshBinding.from_dict(b)
                for b in self.bindings
            )
        )
        side_effects = (
            self.side_effects
            if isinstance(
                self.side_effects, DelegationIdentityMeshSideEffects
            )
            else DelegationIdentityMeshSideEffects.from_dict(
                self.side_effects
            )
        )

        identity_mesh_binding_set_hash = (
            compute_identity_mesh_binding_set_hash(
                delegation_ref_id=delegation_ref_id,
                delegation_identity_hash=delegation_identity_hash,
                role_binding_hash=role_binding_hash,
                constraint_set_hash=constraint_set_hash,
                authority_binding_set_hash=authority_binding_set_hash,
                non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
                bindings=bindings,
                source_label=source_label,
                side_effects=side_effects,
                schema_version=schema_version,
            )
        )
        identity_mesh_binding_set_id = (
            f"imbset:{identity_mesh_binding_set_hash[:16]}"
        )

        if self.identity_mesh_binding_set_hash not in (
            "",
            identity_mesh_binding_set_hash,
        ):
            raise DelegationValidationError(
                "identity_mesh_binding_set_hash does not match "
                "binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="identity_mesh_binding_set_hash",
            )
        if self.identity_mesh_binding_set_id not in (
            "",
            identity_mesh_binding_set_id,
        ):
            raise DelegationValidationError(
                "identity_mesh_binding_set_id does not match "
                "binding set content",
                code=DelegationErrorCode.SERIALIZATION_ERROR,
                field="identity_mesh_binding_set_id",
            )

        object.__setattr__(self, "schema_version", schema_version)
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
            self,
            "non_repudiation_binding_set_hash",
            non_repudiation_binding_set_hash,
        )
        object.__setattr__(self, "bindings", bindings)
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "source_label", source_label)
        object.__setattr__(
            self,
            "identity_mesh_binding_set_hash",
            identity_mesh_binding_set_hash,
        )
        object.__setattr__(
            self,
            "identity_mesh_binding_set_id",
            identity_mesh_binding_set_id,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_binding_set_hash": self.authority_binding_set_hash,
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "constraint_set_hash": self.constraint_set_hash,
            "delegation_identity_hash": self.delegation_identity_hash,
            "delegation_ref_id": self.delegation_ref_id,
            "identity_mesh_binding_set_hash": (
                self.identity_mesh_binding_set_hash
            ),
            "identity_mesh_binding_set_id": (
                self.identity_mesh_binding_set_id
            ),
            "non_repudiation_binding_set_hash": (
                self.non_repudiation_binding_set_hash
            ),
            "role_binding_hash": self.role_binding_hash,
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "source_label": self.source_label.value,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationIdentityMeshBindingSet:
        validate_known_fields(
            data,
            MESH_BINDING_SET_KNOWN_FIELDS,
            label="delegation_identity_mesh_binding_set",
        )
        return cls(
            delegation_ref_id=data["delegation_ref_id"],
            delegation_identity_hash=data["delegation_identity_hash"],
            role_binding_hash=data["role_binding_hash"],
            constraint_set_hash=data["constraint_set_hash"],
            authority_binding_set_hash=data["authority_binding_set_hash"],
            non_repudiation_binding_set_hash=data[
                "non_repudiation_binding_set_hash"
            ],
            bindings=data.get("bindings", ()),
            side_effects=data.get(
                "side_effects", DelegationIdentityMeshSideEffects()
            ),
            source_label=data.get(
                "source_label", DelegationSourceLabel.DEV_FIXTURE
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_IDENTITY_MESH_BINDING_SET_VERSION,
            ),
            identity_mesh_binding_set_id=data.get(
                "identity_mesh_binding_set_id", ""
            ),
            identity_mesh_binding_set_hash=data.get(
                "identity_mesh_binding_set_hash", ""
            ),
        )


# ---------------------------------------------------------------------------
# DelegationIdentityMeshSideEffects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationIdentityMeshSideEffects:
    """Hard proof that P1.8.6 is non-resolving, non-authenticating,
       non-activating, and non-mutating; all fields default to false."""

    identity_resolved: bool = False
    participant_authenticated: bool = False
    relationship_verified: bool = False
    trust_scored: bool = False
    agent_activated: bool = False
    authority_granted: bool = False
    permission_granted: bool = False
    policy_called: bool = False
    custos_called: bool = False
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
            "agent_activated": self.agent_activated,
            "authority_granted": self.authority_granted,
            "custos_called": self.custos_called,
            "global_trace_written": self.global_trace_written,
            "identity_resolved": self.identity_resolved,
            "ledger_written": self.ledger_written,
            "participant_authenticated": self.participant_authenticated,
            "permission_granted": self.permission_granted,
            "policy_called": self.policy_called,
            "relationship_verified": self.relationship_verified,
            "runtime_mutated": self.runtime_mutated,
            "trust_scored": self.trust_scored,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationIdentityMeshSideEffects:
        validate_known_fields(
            data,
            MESH_SIDE_EFFECTS_KNOWN_FIELDS,
            label="delegation_identity_mesh_side_effects",
        )
        return cls(
            **{
                name: data.get(name, False)
                for name in MESH_SIDE_EFFECTS_KNOWN_FIELDS
            }
        )


# ---------------------------------------------------------------------------
# DelegationIdentityMeshStatusReport
# ---------------------------------------------------------------------------


def compute_identity_mesh_status_report_hash(
    *,
    schema_version: str,
    status_label: DelegationSourceLabel,
    available_contracts: Mapping[str, str],
    unavailable_bindings: Mapping[str, str],
    side_effects: DelegationIdentityMeshSideEffects,
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
class DelegationIdentityMeshStatusReport:
    """Reports identity mesh model readiness and unavailable surfaces."""

    status_label: DelegationSourceLabel
    available_contracts: Mapping[str, str]
    unavailable_bindings: Mapping[str, str]
    side_effects: DelegationIdentityMeshSideEffects = field(
        default_factory=DelegationIdentityMeshSideEffects,
    )
    schema_version: str = DELEGATION_IDENTITY_MESH_STATUS_REPORT_VERSION
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
            if isinstance(
                self.side_effects, DelegationIdentityMeshSideEffects
            )
            else DelegationIdentityMeshSideEffects.from_dict(
                self.side_effects
            )
        )

        available_contracts = MappingProxyType(dict(self.available_contracts))
        unavailable_bindings = MappingProxyType(
            dict(self.unavailable_bindings)
        )

        status_hash = compute_identity_mesh_status_report_hash(
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
        object.__setattr__(
            self, "available_contracts", available_contracts
        )
        object.__setattr__(
            self, "unavailable_bindings", unavailable_bindings
        )
        object.__setattr__(self, "side_effects", side_effects)
        object.__setattr__(self, "status_hash", status_hash)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "available_contracts": dict(
                sorted(
                    self.available_contracts.items(),
                    key=lambda item: item[0],
                )
            ),
            "schema_version": self.schema_version,
            "side_effects": self.side_effects.to_canonical_dict(),
            "status_hash": self.status_hash,
            "status_label": self.status_label.value,
            "unavailable_bindings": dict(
                sorted(
                    self.unavailable_bindings.items(),
                    key=lambda item: item[0],
                )
            ),
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> DelegationIdentityMeshStatusReport:
        validate_known_fields(
            data,
            MESH_STATUS_REPORT_KNOWN_FIELDS,
            label="delegation_identity_mesh_status_report",
        )
        return cls(
            status_label=data["status_label"],
            available_contracts=data["available_contracts"],
            unavailable_bindings=data["unavailable_bindings"],
            side_effects=data.get(
                "side_effects", DelegationIdentityMeshSideEffects()
            ),
            schema_version=data.get(
                "schema_version",
                DELEGATION_IDENTITY_MESH_STATUS_REPORT_VERSION,
            ),
            status_hash=data.get("status_hash", ""),
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def build_delegation_mesh_participant_ref(
    delegation_ref_id: str,
    participant_kind: DelegationMeshParticipantKind | str,
    participant_ref: str,
    participant_label: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    mesh_ref_status: DelegationMeshRefStatus = (
        DelegationMeshRefStatus.REFERENCE_ONLY
    ),
) -> DelegationMeshParticipantRef:
    """Build participant ref without resolving identity, authenticating
       participant, or activating an agent."""
    return DelegationMeshParticipantRef(
        delegation_ref_id=delegation_ref_id,
        participant_kind=participant_kind,
        participant_ref=participant_ref,
        participant_label=participant_label,
        source_label=source_label,
        mesh_ref_status=mesh_ref_status,
    )


def build_delegation_mesh_relationship_ref(
    delegation_ref_id: str,
    relationship_kind: DelegationMeshRelationshipKind | str,
    from_participant_ref_id: str,
    to_participant_ref_id: str,
    *,
    relationship_context_ref: str | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    mesh_ref_status: DelegationMeshRefStatus = (
        DelegationMeshRefStatus.REFERENCE_ONLY
    ),
) -> DelegationMeshRelationshipRef:
    """Build relationship ref without verifying trust, proving relationship
       validity, or creating a live mesh edge."""
    return DelegationMeshRelationshipRef(
        delegation_ref_id=delegation_ref_id,
        relationship_kind=relationship_kind,
        from_participant_ref_id=from_participant_ref_id,
        to_participant_ref_id=to_participant_ref_id,
        relationship_context_ref=relationship_context_ref,
        source_label=source_label,
        mesh_ref_status=mesh_ref_status,
    )


def build_delegation_mesh_scope_ref(
    delegation_ref_id: str,
    mesh_scope_kind: DelegationMeshScopeKind | str,
    mesh_scope_ref: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    mesh_ref_status: DelegationMeshRefStatus = (
        DelegationMeshRefStatus.REFERENCE_ONLY
    ),
) -> DelegationMeshScopeRef:
    """Build mesh scope ref without granting permission, data access,
       or authority."""
    return DelegationMeshScopeRef(
        delegation_ref_id=delegation_ref_id,
        mesh_scope_kind=mesh_scope_kind,
        mesh_scope_ref=mesh_scope_ref,
        source_label=source_label,
        mesh_ref_status=mesh_ref_status,
    )


def build_delegation_identity_mesh_envelope(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    *,
    participant_refs: Sequence[
        DelegationMeshParticipantRef | Mapping[str, Any]
    ] = (),
    relationship_refs: Sequence[
        DelegationMeshRelationshipRef | Mapping[str, Any]
    ] = (),
    mesh_scope_ref: DelegationMeshScopeRef | None = None,
    resolution_status: DelegationMeshResolutionStatus = (
        DelegationMeshResolutionStatus.REFERENCE_ONLY
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationIdentityMeshEnvelope:
    """Build identity mesh envelope without resolving identity,
       authenticating participants, verifying relationships, scoring trust,
       activating agents, or granting authority/permission."""
    return DelegationIdentityMeshEnvelope(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        participant_refs=participant_refs,
        relationship_refs=relationship_refs,
        mesh_scope_ref=mesh_scope_ref,
        resolution_status=resolution_status,
        source_label=source_label,
    )


def build_delegation_mesh_resolution_readiness_profile(
    delegation_ref_id: str,
    identity_mesh_envelope_hash: str,
    *,
    has_operator_ref: bool = False,
    has_agent_ref: bool = False,
    has_system_ref: bool = False,
    has_service_ref: bool = False,
    has_role_ref: bool = False,
    has_subject_ref: bool = False,
    has_relationship_refs: bool = False,
    has_mesh_scope_ref: bool = False,
    has_authority_context: bool = False,
    has_evidence_context: bool = False,
    missing_components: Sequence[str] = (),
    resolver_unavailable_reason: str = (
        "identity mesh resolver not available in P1.8.6"
    ),
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationMeshResolutionReadinessProfile:
    """Build readiness profile without scoring trust, confidence, validity,
       identity resolution, or authority."""
    return DelegationMeshResolutionReadinessProfile(
        delegation_ref_id=delegation_ref_id,
        identity_mesh_envelope_hash=identity_mesh_envelope_hash,
        has_operator_ref=has_operator_ref,
        has_agent_ref=has_agent_ref,
        has_system_ref=has_system_ref,
        has_service_ref=has_service_ref,
        has_role_ref=has_role_ref,
        has_subject_ref=has_subject_ref,
        has_relationship_refs=has_relationship_refs,
        has_mesh_scope_ref=has_mesh_scope_ref,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_components,
        resolver_unavailable_reason=resolver_unavailable_reason,
        source_label=source_label,
    )


def build_delegation_mesh_relationship_map(
    delegation_ref_id: str,
    *,
    participant_refs: Sequence[
        DelegationMeshParticipantRef | Mapping[str, Any]
    ] = (),
    relationship_refs: Sequence[
        DelegationMeshRelationshipRef | Mapping[str, Any]
    ] = (),
    mesh_scope_ref: DelegationMeshScopeRef | None = None,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationMeshRelationshipMap:
    """Build relationship map without implementing graph engine,
       trust graph, identity resolver, or live agent network."""
    return DelegationMeshRelationshipMap(
        delegation_ref_id=delegation_ref_id,
        participant_refs=participant_refs,
        relationship_refs=relationship_refs,
        mesh_scope_ref=mesh_scope_ref,
        source_label=source_label,
    )


def build_delegation_identity_mesh_binding(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_envelope_hash: str,
    readiness_hash: str,
    relationship_map_hash: str,
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
    resolution_status: DelegationMeshResolutionStatus = (
        DelegationMeshResolutionStatus.REFERENCE_ONLY
    ),
) -> DelegationIdentityMeshBinding:
    """Build identity mesh binding without resolving identity, authenticating
       participants, verifying relationships, scoring trust, or activating
       agents."""
    return DelegationIdentityMeshBinding(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_envelope_hash=identity_mesh_envelope_hash,
        readiness_hash=readiness_hash,
        relationship_map_hash=relationship_map_hash,
        source_label=source_label,
        resolution_status=resolution_status,
    )


def build_delegation_identity_mesh_binding_set(
    delegation_ref_id: str,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    bindings: Sequence[
        DelegationIdentityMeshBinding | Mapping[str, Any]
    ],
    *,
    source_label: DelegationSourceLabel = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationIdentityMeshBindingSet:
    """Build collection of identity mesh bindings without resolving identity,
       activating agents, scoring trust, or writing trace/Ledger."""
    return DelegationIdentityMeshBindingSet(
        delegation_ref_id=delegation_ref_id,
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        bindings=bindings,
        source_label=source_label,
    )


def _default_identity_mesh_available_contracts() -> dict[str, str]:
    return {
        "DelegationIdentityMeshBinding": DelegationSourceLabel.LIVE.value,
        "DelegationIdentityMeshBindingSet": DelegationSourceLabel.LIVE.value,
        "DelegationIdentityMeshEnvelope": DelegationSourceLabel.LIVE.value,
        "DelegationIdentityMeshSideEffects": DelegationSourceLabel.LIVE.value,
        "DelegationIdentityMeshStatusReport": DelegationSourceLabel.LIVE.value,
        "DelegationMeshParticipantKind": DelegationSourceLabel.LIVE.value,
        "DelegationMeshParticipantRef": DelegationSourceLabel.LIVE.value,
        "DelegationMeshRefStatus": DelegationSourceLabel.LIVE.value,
        "DelegationMeshRelationshipKind": DelegationSourceLabel.LIVE.value,
        "DelegationMeshRelationshipMap": DelegationSourceLabel.LIVE.value,
        "DelegationMeshRelationshipRef": DelegationSourceLabel.LIVE.value,
        "DelegationMeshResolutionReadinessProfile": (
            DelegationSourceLabel.LIVE.value
        ),
        "DelegationMeshResolutionStatus": DelegationSourceLabel.LIVE.value,
        "DelegationMeshScopeKind": DelegationSourceLabel.LIVE.value,
        "DelegationMeshScopeRef": DelegationSourceLabel.LIVE.value,
    }


def build_delegation_identity_mesh_status_report() -> (
    DelegationIdentityMeshStatusReport
):
    """Return honest P1.8.6 identity mesh status report (non-resolving)."""
    return DelegationIdentityMeshStatusReport(
        status_label=DelegationSourceLabel.DEV_FIXTURE,
        available_contracts=_default_identity_mesh_available_contracts(),
        unavailable_bindings=DELEGATION_IDENTITY_MESH_UNAVAILABLE_BINDINGS,
        side_effects=DelegationIdentityMeshSideEffects(),
    )


def serialize_delegation_mesh_participant_ref(
    participant_ref: DelegationMeshParticipantRef,
) -> str:
    """Serialize DelegationMeshParticipantRef to deterministic canonical JSON."""
    return to_canonical_json(participant_ref)


def serialize_delegation_mesh_relationship_ref(
    relationship_ref: DelegationMeshRelationshipRef,
) -> str:
    """Serialize DelegationMeshRelationshipRef to deterministic canonical JSON."""
    return to_canonical_json(relationship_ref)


def serialize_delegation_mesh_scope_ref(
    scope_ref: DelegationMeshScopeRef,
) -> str:
    """Serialize DelegationMeshScopeRef to deterministic canonical JSON."""
    return to_canonical_json(scope_ref)


def serialize_delegation_identity_mesh_envelope(
    envelope: DelegationIdentityMeshEnvelope,
) -> str:
    """Serialize DelegationIdentityMeshEnvelope to deterministic canonical JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_mesh_resolution_readiness_profile(
    profile: DelegationMeshResolutionReadinessProfile,
) -> str:
    """Serialize DelegationMeshResolutionReadinessProfile to deterministic
       canonical JSON."""
    return to_canonical_json(profile)


def serialize_delegation_mesh_relationship_map(
    relationship_map: DelegationMeshRelationshipMap,
) -> str:
    """Serialize DelegationMeshRelationshipMap to deterministic canonical JSON."""
    return to_canonical_json(relationship_map)


def serialize_delegation_identity_mesh_binding(
    binding: DelegationIdentityMeshBinding,
) -> str:
    """Serialize DelegationIdentityMeshBinding to deterministic canonical JSON."""
    return to_canonical_json(binding)


def serialize_delegation_identity_mesh_binding_set(
    binding_set: DelegationIdentityMeshBindingSet,
) -> str:
    """Serialize DelegationIdentityMeshBindingSet to deterministic
       canonical JSON."""
    return to_canonical_json(binding_set)


def hash_delegation_mesh_participant_ref(
    participant_ref: DelegationMeshParticipantRef,
) -> str:
    """Return stable participant_hash for DelegationMeshParticipantRef content."""
    return participant_ref.participant_hash


def hash_delegation_mesh_relationship_ref(
    relationship_ref: DelegationMeshRelationshipRef,
) -> str:
    """Return stable relationship_hash for DelegationMeshRelationshipRef
       content."""
    return relationship_ref.relationship_hash


def hash_delegation_mesh_scope_ref(
    scope_ref: DelegationMeshScopeRef,
) -> str:
    """Return stable mesh_scope_hash for DelegationMeshScopeRef content."""
    return scope_ref.mesh_scope_hash


def hash_delegation_identity_mesh_envelope(
    envelope: DelegationIdentityMeshEnvelope,
) -> str:
    """Return stable identity_mesh_envelope_hash for
       DelegationIdentityMeshEnvelope content."""
    return envelope.identity_mesh_envelope_hash


def hash_delegation_mesh_resolution_readiness_profile(
    profile: DelegationMeshResolutionReadinessProfile,
) -> str:
    """Return stable readiness_hash for
       DelegationMeshResolutionReadinessProfile content."""
    return profile.readiness_hash


def hash_delegation_mesh_relationship_map(
    relationship_map: DelegationMeshRelationshipMap,
) -> str:
    """Return stable relationship_map_hash for
       DelegationMeshRelationshipMap content."""
    return relationship_map.relationship_map_hash


def hash_delegation_identity_mesh_binding(
    binding: DelegationIdentityMeshBinding,
) -> str:
    """Return stable binding_hash for DelegationIdentityMeshBinding content."""
    return binding.binding_hash


def hash_delegation_identity_mesh_binding_set(
    binding_set: DelegationIdentityMeshBindingSet,
) -> str:
    """Return stable identity_mesh_binding_set_hash for
       DelegationIdentityMeshBindingSet content."""
    return binding_set.identity_mesh_binding_set_hash
