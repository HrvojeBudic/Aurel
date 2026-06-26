"""Delegation / Non-Repudiation / Agent Identity Mesh (P1.8).

Foundation layer (P1.8.0): typed delegation records, reference-only evidence hooks,
identity mesh references, deterministic serialization, and honest capability reporting.

Identity / reference layer (P1.8.1): stable DelegationRef, DelegationIdentity,
DelegationRefBinding, and status report with deterministic hashing.

Role-binding layer (P1.8.2): typed, deterministic, JSON-safe role contracts for
delegator/delegate/subject bound to DelegationRef/DelegationIdentity without
approving, executing, enforcing, verifying, activating, or granting authority.

Constraint model layer (P1.8.3): declared constraint contracts bound to
DelegationRef / DelegationIdentity / DelegationRoleBindingSet without enforcing,
approving, blocking, verifying, resolving, or mutating runtime behavior.

P1.8 does not authorize, enforce, verify, execute, or write trace/Ledger.

Architectural law:
  - DelegationRecord is not permission.
  - AuthorityRef is not granted authority.
  - NonRepudiationRef is not verified proof.
  - AgentIdentityMeshRef is not live mesh activation.
  - DelegationRef is not approval.
  - DelegationIdentity is not verification.
  - DelegationRefBinding is not trace proof.
  - record_hash is not TRACE_VERIFIED.
  - identity_hash is not proof.
  - DelegationPartyRoleRef is not verified authority.
  - DelegatedSubjectRef is not subject execution.
  - DelegationRoleBinding is not approval or permission.
  - DelegationRoleBindingSet is not enforcement.
  - role_binding_hash is not TRACE_VERIFIED.
  - Role model exists ≠ resolver exists.
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

from .foundation import (
    ACTOR_REF_KNOWN_FIELDS,
    AUTHORITY_REF_KNOWN_FIELDS,
    CONSTRAINT_KNOWN_FIELDS,
    DELEGATION_FOUNDATION_STATUS_VERSION,
    DELEGATION_MODULE_NAME,
    DELEGATION_SCHEMA_VERSION,
    DELEGATION_TASK_ID,
    DELEGATION_UNAVAILABLE_BINDINGS,
    FOUNDATION_STATUS_KNOWN_FIELDS,
    IDENTITY_MESH_REF_KNOWN_FIELDS,
    NON_REPUDIATION_REF_KNOWN_FIELDS,
    RECORD_KNOWN_FIELDS,
    SIDE_EFFECTS_KNOWN_FIELDS,
    SUBJECT_KNOWN_FIELDS,
    AgentIdentityMeshRef,
    DelegationActorKind,
    DelegationActorRef,
    DelegationAuthorityKind,
    DelegationAuthorityRef,
    DelegationConstraint,
    DelegationConstraintKind,
    DelegationError,
    DelegationErrorCode,
    DelegationFoundationCapability,
    DelegationFoundationStatus,
    DelegationRecord,
    DelegationSerializationError,
    DelegationSideEffects,
    DelegationSourceLabel,
    DelegationStructuredError,
    DelegationSubject,
    DelegationSubjectKind,
    DelegationUnknownFieldError,
    DelegationValidationError,
    NonRepudiationProofStatus,
    NonRepudiationRef,
    build_agent_identity_mesh_ref,
    build_delegation_actor_ref,
    build_delegation_authority_ref,
    build_delegation_constraint,
    build_delegation_foundation_status,
    build_delegation_record,
    build_delegation_subject,
    build_non_repudiation_ref,
    hash_delegation_record,
    serialize_delegation_record,
    stable_hash,
    to_canonical_dict,
    to_canonical_json,
    validate_known_fields,
)

from .identity import (
    DELEGATION_IDENTITY_SCHEMA_VERSION,
    DELEGATION_IDENTITY_SIDE_EFFECTS_VERSION,
    DELEGATION_IDENTITY_STATUS_REPORT_VERSION,
    DELEGATION_IDENTITY_TASK_ID,
    DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS,
    DELEGATION_REF_BINDING_SCHEMA_VERSION,
    DELEGATION_REF_KNOWN_FIELDS,
    DELEGATION_REF_SCHEMA_VERSION,
    IDENTITY_KNOWN_FIELDS,
    IDENTITY_SIDE_EFFECTS_KNOWN_FIELDS,
    IDENTITY_STATUS_REPORT_KNOWN_FIELDS,
    REF_BINDING_KNOWN_FIELDS,
    DelegationIdentity,
    DelegationIdentityKind,
    DelegationIdentitySideEffects,
    DelegationIdentityStatus,
    DelegationIdentityStatusReport,
    DelegationRef,
    DelegationRefBinding,
    DelegationRefBindingKind,
    build_delegation_identity,
    build_delegation_identity_status_report,
    build_delegation_ref,
    build_delegation_ref_binding,
    hash_delegation_identity,
    hash_delegation_ref,
    serialize_delegation_identity,
    serialize_delegation_ref,
)

from .roles import (
    DELEGATED_SUBJECT_REF_VERSION,
    DELEGATION_PARTY_ROLE_REF_VERSION,
    DELEGATION_ROLE_BINDING_SET_VERSION,
    DELEGATION_ROLE_BINDING_VERSION,
    DELEGATION_ROLES_TASK_ID,
    DELEGATION_ROLES_UNAVAILABLE_BINDINGS,
    DELEGATION_ROLE_SIDE_EFFECTS_VERSION,
    DELEGATION_ROLE_STATUS_REPORT_VERSION,
    PARTY_ROLE_REF_KNOWN_FIELDS,
    ROLE_BINDING_KNOWN_FIELDS,
    ROLE_BINDING_SET_KNOWN_FIELDS,
    ROLE_SIDE_EFFECTS_KNOWN_FIELDS,
    ROLE_STATUS_REPORT_KNOWN_FIELDS,
    SUBJECT_ROLE_REF_KNOWN_FIELDS,
    DelegatedSubjectRef,
    DelegationPartyRoleRef,
    DelegationRoleBinding,
    DelegationRoleBindingSet,
    DelegationRoleBindingStatus,
    DelegationRoleKind,
    DelegationRoleSideEffects,
    DelegationRoleStatusReport,
    build_delegated_subject_ref,
    build_delegation_party_role_ref,
    build_delegation_role_binding,
    build_delegation_role_binding_set,
    build_delegation_role_status_report,
    compute_role_binding_hash,
    compute_role_binding_set_hash,
    compute_role_ref_hash,
    compute_role_status_report_hash,
    compute_subject_role_hash,
    hash_delegation_role_binding_set,
    serialize_delegation_role_binding_set,
)

from .constraints import (
    CONSTRAINT_BINDING_KNOWN_FIELDS,
    CONSTRAINT_REF_KNOWN_FIELDS,
    CONSTRAINT_SET_KNOWN_FIELDS,
    CONSTRAINT_SIDE_EFFECTS_KNOWN_FIELDS,
    CONSTRAINT_STATUS_REPORT_KNOWN_FIELDS,
    DELEGATION_CONSTRAINTS_TASK_ID,
    DELEGATION_CONSTRAINTS_UNAVAILABLE_BINDINGS,
    DELEGATION_CONSTRAINT_BINDING_VERSION,
    DELEGATION_CONSTRAINT_REF_VERSION,
    DELEGATION_CONSTRAINT_SET_VERSION,
    DELEGATION_CONSTRAINT_SIDE_EFFECTS_VERSION,
    DELEGATION_CONSTRAINT_STATUS_REPORT_VERSION,
    DelegationConstraintBinding,
    DelegationConstraintRef,
    DelegationConstraintSet,
    DelegationConstraintSeverity,
    DelegationConstraintSideEffects,
    DelegationConstraintStatus,
    DelegationConstraintStatusReport,
    build_delegation_constraint_binding,
    build_delegation_constraint_ref,
    build_delegation_constraint_set,
    build_delegation_constraint_status_report,
    hash_delegation_constraint_ref,
    hash_delegation_constraint_set,
    serialize_delegation_constraint_ref,
    serialize_delegation_constraint_set,
)

__all__ = [
    # P1.8.0 foundation constants
    "ACTOR_REF_KNOWN_FIELDS",
    "AUTHORITY_REF_KNOWN_FIELDS",
    "CONSTRAINT_KNOWN_FIELDS",
    "DELEGATION_FOUNDATION_STATUS_VERSION",
    "DELEGATION_MODULE_NAME",
    "DELEGATION_SCHEMA_VERSION",
    "DELEGATION_TASK_ID",
    "DELEGATION_UNAVAILABLE_BINDINGS",
    "FOUNDATION_STATUS_KNOWN_FIELDS",
    "IDENTITY_MESH_REF_KNOWN_FIELDS",
    "NON_REPUDIATION_REF_KNOWN_FIELDS",
    "RECORD_KNOWN_FIELDS",
    "SIDE_EFFECTS_KNOWN_FIELDS",
    "SUBJECT_KNOWN_FIELDS",
    # P1.8.0 enums
    "DelegationActorKind",
    "DelegationAuthorityKind",
    "DelegationConstraintKind",
    "DelegationFoundationCapability",
    "DelegationErrorCode",
    "DelegationSourceLabel",
    "DelegationSubjectKind",
    "NonRepudiationProofStatus",
    # P1.8.0 dataclasses
    "AgentIdentityMeshRef",
    "DelegationActorRef",
    "DelegationAuthorityRef",
    "DelegationConstraint",
    "DelegationFoundationStatus",
    "DelegationRecord",
    "DelegationSideEffects",
    "DelegationStructuredError",
    "DelegationSubject",
    "NonRepudiationRef",
    # P1.8.0 errors
    "DelegationError",
    "DelegationSerializationError",
    "DelegationUnknownFieldError",
    "DelegationValidationError",
    # P1.8.0 builders / helpers
    "build_agent_identity_mesh_ref",
    "build_delegation_actor_ref",
    "build_delegation_authority_ref",
    "build_delegation_constraint",
    "build_delegation_foundation_status",
    "build_delegation_record",
    "build_delegation_subject",
    "build_non_repudiation_ref",
    "hash_delegation_record",
    "serialize_delegation_record",
    "stable_hash",
    "to_canonical_dict",
    "to_canonical_json",
    "validate_known_fields",
    # P1.8.1 identity constants
    "DELEGATION_IDENTITY_SCHEMA_VERSION",
    "DELEGATION_IDENTITY_SIDE_EFFECTS_VERSION",
    "DELEGATION_IDENTITY_STATUS_REPORT_VERSION",
    "DELEGATION_IDENTITY_TASK_ID",
    "DELEGATION_IDENTITY_UNAVAILABLE_BINDINGS",
    "DELEGATION_REF_BINDING_SCHEMA_VERSION",
    "DELEGATION_REF_KNOWN_FIELDS",
    "DELEGATION_REF_SCHEMA_VERSION",
    "IDENTITY_KNOWN_FIELDS",
    "IDENTITY_SIDE_EFFECTS_KNOWN_FIELDS",
    "IDENTITY_STATUS_REPORT_KNOWN_FIELDS",
    "REF_BINDING_KNOWN_FIELDS",
    # P1.8.1 enums
    "DelegationIdentityKind",
    "DelegationIdentityStatus",
    "DelegationRefBindingKind",
    # P1.8.1 dataclasses
    "DelegationIdentity",
    "DelegationIdentitySideEffects",
    "DelegationIdentityStatusReport",
    "DelegationRef",
    "DelegationRefBinding",
    # P1.8.1 builders / helpers
    "build_delegation_identity",
    "build_delegation_identity_status_report",
    "build_delegation_ref",
    "build_delegation_ref_binding",
    "hash_delegation_identity",
    "hash_delegation_ref",
    "serialize_delegation_identity",
    "serialize_delegation_ref",
    # P1.8.2 role constants
    "DELEGATED_SUBJECT_REF_VERSION",
    "DELEGATION_PARTY_ROLE_REF_VERSION",
    "DELEGATION_ROLE_BINDING_SET_VERSION",
    "DELEGATION_ROLE_BINDING_VERSION",
    "DELEGATION_ROLES_TASK_ID",
    "DELEGATION_ROLES_UNAVAILABLE_BINDINGS",
    "DELEGATION_ROLE_SIDE_EFFECTS_VERSION",
    "DELEGATION_ROLE_STATUS_REPORT_VERSION",
    "PARTY_ROLE_REF_KNOWN_FIELDS",
    "ROLE_BINDING_KNOWN_FIELDS",
    "ROLE_BINDING_SET_KNOWN_FIELDS",
    "ROLE_SIDE_EFFECTS_KNOWN_FIELDS",
    "ROLE_STATUS_REPORT_KNOWN_FIELDS",
    "SUBJECT_ROLE_REF_KNOWN_FIELDS",
    # P1.8.2 enums
    "DelegationRoleBindingStatus",
    "DelegationRoleKind",
    # P1.8.2 dataclasses
    "DelegatedSubjectRef",
    "DelegationPartyRoleRef",
    "DelegationRoleBinding",
    "DelegationRoleBindingSet",
    "DelegationRoleSideEffects",
    "DelegationRoleStatusReport",
    # P1.8.2 builders / helpers / hash functions
    "build_delegated_subject_ref",
    "build_delegation_party_role_ref",
    "build_delegation_role_binding",
    "build_delegation_role_binding_set",
    "build_delegation_role_status_report",
    "compute_role_binding_hash",
    "compute_role_binding_set_hash",
    "compute_role_ref_hash",
    "compute_role_status_report_hash",
    "compute_subject_role_hash",
    "hash_delegation_role_binding_set",
    "serialize_delegation_role_binding_set",
    # P1.8.3 constraint constants
    "CONSTRAINT_BINDING_KNOWN_FIELDS",
    "CONSTRAINT_REF_KNOWN_FIELDS",
    "CONSTRAINT_SET_KNOWN_FIELDS",
    "CONSTRAINT_SIDE_EFFECTS_KNOWN_FIELDS",
    "CONSTRAINT_STATUS_REPORT_KNOWN_FIELDS",
    "DELEGATION_CONSTRAINTS_TASK_ID",
    "DELEGATION_CONSTRAINTS_UNAVAILABLE_BINDINGS",
    "DELEGATION_CONSTRAINT_BINDING_VERSION",
    "DELEGATION_CONSTRAINT_REF_VERSION",
    "DELEGATION_CONSTRAINT_SET_VERSION",
    "DELEGATION_CONSTRAINT_SIDE_EFFECTS_VERSION",
    "DELEGATION_CONSTRAINT_STATUS_REPORT_VERSION",
    # P1.8.3 enums
    "DelegationConstraintSeverity",
    "DelegationConstraintStatus",
    # P1.8.3 dataclasses
    "DelegationConstraintBinding",
    "DelegationConstraintRef",
    "DelegationConstraintSet",
    "DelegationConstraintSideEffects",
    "DelegationConstraintStatusReport",
    # P1.8.3 builders / helpers / hash functions
    "build_delegation_constraint_binding",
    "build_delegation_constraint_ref",
    "build_delegation_constraint_set",
    "build_delegation_constraint_status_report",
    "hash_delegation_constraint_ref",
    "hash_delegation_constraint_set",
    "serialize_delegation_constraint_ref",
    "serialize_delegation_constraint_set",
]
