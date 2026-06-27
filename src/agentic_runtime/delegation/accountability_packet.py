"""Delegation accountability packet / integration summary reference model (P1.8.15).

Deterministic, versioned, JSON-safe, side-effect-free reference-only
accountability packet / integration summary metadata layer over P1.8.0-P1.8.14
delegation context.

Produces accountability component refs, coverage matrix entries, coverage
matrix, accountability profile, integration summary ref, integration summary
envelope, accountability packet envelope, accountability packet binding,
and accountability packet binding set without accountability verification,
component verification, coverage verification, compliance proof, trust scoring,
projection/API/event contract, CLI/Shell/TUI binding, policy/Custos decision,
approval creation, runtime execution, trace write, Ledger write, audit
finality, evidence verification, Output Passport behavior, P1.9 behavior,
P1.8.16 behavior, P1.8.17 behavior, P1.8.18 behavior, or runtime mutation.

Architectural law:
  - AccountabilityPacket exists does not mean accountability is proven.
  - IntegrationSummary exists does not mean system is integrated.
  - AccountabilityComponentRef exists does not mean component is verified.
  - CoverageMatrix exists does not mean compliance proof.
  - AccountabilityProfile exists does not mean trust score.
  - ComponentPresent exists does not mean verified.
  - MissingComponent exists does not mean runtime failure.
  - SummaryHash exists does not mean TRACE_VERIFIED.
  - Golden Thread exists does not mean trace verification.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any

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

DELEGATION_ACCOUNTABILITY_PACKET_TASK_ID = "P1.8.15"
DELEGATION_ACCOUNTABILITY_COMPONENT_REF_VERSION = "delegation_accountability_component_ref.v1"
DELEGATION_ACCOUNTABILITY_COVERAGE_MATRIX_ENTRY_VERSION = "delegation_accountability_coverage_matrix_entry.v1"
DELEGATION_ACCOUNTABILITY_COVERAGE_MATRIX_VERSION = "delegation_accountability_coverage_matrix.v1"
DELEGATION_ACCOUNTABILITY_PROFILE_VERSION = "delegation_accountability_profile.v1"
DELEGATION_INTEGRATION_SUMMARY_REF_VERSION = "delegation_integration_summary_ref.v1"
DELEGATION_INTEGRATION_SUMMARY_ENVELOPE_VERSION = "delegation_integration_summary_envelope.v1"
DELEGATION_ACCOUNTABILITY_PACKET_ENVELOPE_VERSION = "delegation_accountability_packet_envelope.v1"
DELEGATION_ACCOUNTABILITY_PACKET_BINDING_VERSION = "delegation_accountability_packet_binding.v1"
DELEGATION_ACCOUNTABILITY_PACKET_BINDING_SET_VERSION = "delegation_accountability_packet_binding_set.v1"
DELEGATION_ACCOUNTABILITY_PACKET_SIDE_EFFECTS_VERSION = "delegation_accountability_packet_side_effects.v1"
DELEGATION_ACCOUNTABILITY_PACKET_STATUS_REPORT_VERSION = "delegation_accountability_packet_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_ACCOUNTABILITY_PACKET_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.15; "
        "reference-only accountability packet metadata layer"
    ),
    "API/Event Contract": (
        "API/event contract is not available in P1.8.15; "
        "accountability packet is reference-only metadata, not API contract"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding is not available in P1.8.15; "
        "accountability packet is reference-only metadata, not CLI binding"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.15; "
        "accountability packet does not write trace"
    ),
    "Ledger Writer": (
        "Ledger writer is not available in P1.8.15; "
        "accountability packet does not write Ledger"
    ),
    "Ledger Finality": (
        "Ledger finality is not available in P1.8.15; "
        "accountability packet does not finalize Ledger"
    ),
    "Trace Verification": (
        "Trace verification is not available in P1.8.15; "
        "accountability packet hashes are not TRACE_VERIFIED"
    ),
    "Audit Finality": (
        "Audit finality is not available in P1.8.15; "
        "accountability packet does not finalize audit"
    ),
    "Evidence Verification": (
        "Evidence verification is not available in P1.8.15; "
        "accountability packet does not verify evidence"
    ),
    "Policy/Custos Decision": (
        "Policy/Custos decision is not available in P1.8.15; "
        "accountability packet does not make policy decisions"
    ),
    "Approval Creation": (
        "Approval creation is not available in P1.8.15; "
        "accountability packet does not create approval"
    ),
    "Runtime Execution": (
        "Runtime execution is not available in P1.8.15; "
        "accountability packet does not execute runtime"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 is not implemented in P1.8.15"
    ),
    "Accountability Verification": (
        "Accountability verification is not available in P1.8.15; "
        "AccountabilityPacket exists does not mean accountability is proven"
    ),
    "Component Verification": (
        "Component verification is not available in P1.8.15; "
        "AccountabilityComponentRef exists does not mean component is verified"
    ),
    "Coverage Verification": (
        "Coverage verification is not available in P1.8.15; "
        "CoverageMatrix exists does not mean compliance proof"
    ),
    "Compliance Proof": (
        "Compliance proof is not available in P1.8.15; "
        "CoverageMatrix is not compliance proof"
    ),
    "P1.8.16 Pre-Projection Readiness / Surface Contract Seed": (
        "P1.8.16 pre-projection readiness model is not implemented in P1.8.15"
    ),
    "P1.8.17 Projection/API/Event Contract": (
        "P1.8.17 projection/API/event contract is not implemented in P1.8.15"
    ),
    "P1.8.18 CLI/Shell/TUI Binding": (
        "P1.8.18 CLI/Shell/TUI binding is not implemented in P1.8.15"
    ),
    "P1.8.19 Docs/State/Report Seal Update": (
        "P1.8.19 docs/state/report seal update is not implemented in P1.8.15"
    ),
    "P1.8.20 Exit Seal Demo": (
        "P1.8.20 exit seal demo is not implemented in P1.8.15"
    ),
    "TRACE_VERIFIED Claim": (
        "TRACE_VERIFIED claim is not available in P1.8.15; "
        "accountability packet is reference-only metadata"
    ),
    "Global Trace Write": (
        "Global trace write is not available in P1.8.15; "
        "accountability packet does not write global trace"
    ),
    "Runtime Mutation": (
        "Runtime mutation is not available in P1.8.15; "
        "accountability packet does not mutate runtime"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world validation)
# ---------------------------------------------------------------------------

ACCOUNTABILITY_COMPONENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "component_ref_id",
    "delegation_ref_id",
    "component_family",
    "component_ref",
    "component_description",
    "component_hash",
    "source_label",
    "reference_status",
    "packet_status",
    "component_ref_hash",
})

COVERAGE_MATRIX_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "entry_id",
    "delegation_ref_id",
    "component_family",
    "present",
    "hash_present",
    "source_label_present",
    "finding_count",
    "unavailable_reason",
    "source_label",
    "entry_hash",
})

COVERAGE_MATRIX_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "coverage_matrix_id",
    "delegation_ref_id",
    "entries",
    "source_label",
    "coverage_matrix_hash",
})

ACCOUNTABILITY_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "accountability_profile_id",
    "delegation_ref_id",
    "has_foundation_context",
    "has_identity_context",
    "has_role_context",
    "has_constraint_context",
    "has_authority_context",
    "has_evidence_context",
    "has_identity_mesh_context",
    "has_scope_context",
    "has_lifecycle_context",
    "has_chain_context",
    "has_shadow_resolver_context",
    "has_operator_review_context",
    "has_policy_custos_bridge_context",
    "has_runtime_execution_readiness_context",
    "has_trace_audit_bridge_context",
    "missing_components",
    "projection_unavailable_reason",
    "api_event_contract_unavailable_reason",
    "cli_shell_tui_unavailable_reason",
    "trace_verification_unavailable_reason",
    "ledger_finality_unavailable_reason",
    "output_passport_unavailable_reason",
    "accountability_verification_unavailable_reason",
    "source_label",
    "profile_hash",
})

INTEGRATION_SUMMARY_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "integration_summary_ref_id",
    "delegation_ref_id",
    "integration_summary_ref",
    "integration_summary_description",
    "reference_status",
    "source_label",
    "packet_status",
    "integration_summary_ref_hash",
})

INTEGRATION_SUMMARY_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "integration_summary_envelope_id",
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
    "shadow_resolver_result_hash",
    "operator_review_binding_set_hash",
    "policy_custos_bridge_binding_set_hash",
    "runtime_execution_readiness_binding_set_hash",
    "trace_audit_bridge_binding_set_hash",
    "component_refs",
    "coverage_matrix_hash",
    "accountability_profile_hash",
    "source_label",
    "integration_summary_envelope_hash",
})

ACCOUNTABILITY_PACKET_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "accountability_packet_envelope_id",
    "delegation_ref_id",
    "integration_summary_envelope_hash",
    "component_refs",
    "coverage_matrix_hash",
    "accountability_profile_hash",
    "trace_audit_bridge_binding_set_hash",
    "golden_thread_ref",
    "next_handoff_ref",
    "source_label",
    "accountability_packet_envelope_hash",
})

PACKET_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
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
    "lifecycle_binding_set_hash",
    "chain_binding_set_hash",
    "shadow_resolver_result_hash",
    "operator_review_binding_set_hash",
    "policy_custos_bridge_binding_set_hash",
    "runtime_execution_readiness_binding_set_hash",
    "trace_audit_bridge_binding_set_hash",
    "integration_summary_envelope_hash",
    "accountability_packet_envelope_hash",
    "coverage_matrix_hash",
    "accountability_profile_hash",
    "source_label",
    "packet_status",
    "binding_hash",
})

PACKET_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "accountability_packet_binding_set_id",
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
    "shadow_resolver_result_hash",
    "operator_review_binding_set_hash",
    "policy_custos_bridge_binding_set_hash",
    "runtime_execution_readiness_binding_set_hash",
    "trace_audit_bridge_binding_set_hash",
    "bindings",
    "source_label",
    "accountability_packet_binding_set_hash",
    "side_effects",
})

PACKET_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "accountability_verified",
    "component_verified",
    "coverage_verified",
    "compliance_proven",
    "projection_created",
    "api_event_contract_created",
    "cli_shell_tui_bound",
    "policy_decision_emitted",
    "custos_decision_emitted",
    "approval_created",
    "runtime_executed",
    "trace_written",
    "ledger_written",
    "audit_finalized",
    "evidence_verified",
    "output_passport_created",
    "global_trace_written",
    "runtime_mutated",
})

PACKET_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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

class DelegationAccountabilityPacketKind(str, Enum):
    """Accountability packet kind classifier; does not prove accountability,
    verify components, create projection/API/CLI, or create Output Passport.

    Boundary:
      - Accountability packet kind classifies accountability packet /
        integration summary metadata.
      - It does not prove accountability.
      - It does not verify components.
      - It does not create projection/API/CLI.
      - It does not create Output Passport.
    """

    ACCOUNTABILITY_COMPONENT = "ACCOUNTABILITY_COMPONENT"
    COVERAGE_MATRIX = "COVERAGE_MATRIX"
    ACCOUNTABILITY_PROFILE = "ACCOUNTABILITY_PROFILE"
    INTEGRATION_SUMMARY = "INTEGRATION_SUMMARY"
    ACCOUNTABILITY_PACKET = "ACCOUNTABILITY_PACKET"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationAccountabilityPacketReferenceStatus(str, Enum):
    """Reference status ladder; never implies component verified,
    coverage verified, compliance proven, trust scored, projection created,
    CLI bound, trace verified, Ledger finalized, or Output Passport created.

    Boundary:
      - COMPONENT_REFERENCED is not component verified.
      - COVERAGE_MATRIX_REFERENCED is not compliance proof.
      - ACCOUNTABILITY_PROFILE_REFERENCED is not accountability proof.
      - INTEGRATION_SUMMARY_REFERENCED is not system integrated.
      - ACCOUNTABILITY_PACKET_REFERENCED is not accountability proven.
      - PROJECTION_UNAVAILABLE is honest unavailability, not projection failure.
      - API_EVENT_CONTRACT_UNAVAILABLE is honest unavailability, not API failure.
      - CLI_SHELL_TUI_UNAVAILABLE is honest unavailability, not CLI failure.
      - TRACE_VERIFICATION_UNAVAILABLE is honest unavailability, not trace failure.
      - LEDGER_FINALITY_UNAVAILABLE is honest unavailability, not Ledger failure.
      - OUTPUT_PASSPORT_UNAVAILABLE is honest unavailability, not P1.9 failure.
      - ACCOUNTABILITY_VERIFICATION_UNAVAILABLE is honest unavailability,
        not accountability failure.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    COMPONENT_REFERENCED = "COMPONENT_REFERENCED"
    COVERAGE_MATRIX_REFERENCED = "COVERAGE_MATRIX_REFERENCED"
    ACCOUNTABILITY_PROFILE_REFERENCED = "ACCOUNTABILITY_PROFILE_REFERENCED"
    INTEGRATION_SUMMARY_REFERENCED = "INTEGRATION_SUMMARY_REFERENCED"
    ACCOUNTABILITY_PACKET_REFERENCED = "ACCOUNTABILITY_PACKET_REFERENCED"
    PROJECTION_UNAVAILABLE = "PROJECTION_UNAVAILABLE"
    API_EVENT_CONTRACT_UNAVAILABLE = "API_EVENT_CONTRACT_UNAVAILABLE"
    CLI_SHELL_TUI_UNAVAILABLE = "CLI_SHELL_TUI_UNAVAILABLE"
    TRACE_VERIFICATION_UNAVAILABLE = "TRACE_VERIFICATION_UNAVAILABLE"
    LEDGER_FINALITY_UNAVAILABLE = "LEDGER_FINALITY_UNAVAILABLE"
    OUTPUT_PASSPORT_UNAVAILABLE = "OUTPUT_PASSPORT_UNAVAILABLE"
    ACCOUNTABILITY_VERIFICATION_UNAVAILABLE = "ACCOUNTABILITY_VERIFICATION_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationAccountabilityPacketStatus(str, Enum):
    """Accountability packet declaration status; does not imply accountability
    proven, system integrated, verified, compliant, projected, CLI-bound,
    traced, audited, or passported.

    Boundary:
      - REFERENCE_ONLY means accountability packet context is reference-only.
      - DECLARED means accountability packet context was declared as metadata.
      - Neither means accountability proven, integrated, verified, compliant,
        projected, CLI-bound, traced, audited, or passported.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationAccountabilityComponentFamily(str, Enum):
    """Accountability component family classifier; classifies P1.8 component
    metadata without representing component verification, proof, compliance,
    trace verification, or finality.

    Boundary:
      - Component family classifies P1.8 component metadata.
      - It does not represent component verification.
      - It does not represent proof, compliance, trace verification, or finality.
    """

    FOUNDATION_CONTEXT = "FOUNDATION_CONTEXT"
    IDENTITY_CONTEXT = "IDENTITY_CONTEXT"
    ROLE_CONTEXT = "ROLE_CONTEXT"
    CONSTRAINT_CONTEXT = "CONSTRAINT_CONTEXT"
    AUTHORITY_CONTEXT = "AUTHORITY_CONTEXT"
    EVIDENCE_CONTEXT = "EVIDENCE_CONTEXT"
    IDENTITY_MESH_CONTEXT = "IDENTITY_MESH_CONTEXT"
    SCOPE_CONTEXT = "SCOPE_CONTEXT"
    LIFECYCLE_CONTEXT = "LIFECYCLE_CONTEXT"
    CHAIN_CONTEXT = "CHAIN_CONTEXT"
    SHADOW_RESOLVER_CONTEXT = "SHADOW_RESOLVER_CONTEXT"
    OPERATOR_REVIEW_CONTEXT = "OPERATOR_REVIEW_CONTEXT"
    POLICY_CUSTOS_BRIDGE_CONTEXT = "POLICY_CUSTOS_BRIDGE_CONTEXT"
    RUNTIME_EXECUTION_READINESS_CONTEXT = "RUNTIME_EXECUTION_READINESS_CONTEXT"
    TRACE_AUDIT_BRIDGE_CONTEXT = "TRACE_AUDIT_BRIDGE_CONTEXT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# SideEffects (plain dataclass, all defaults False)
# ---------------------------------------------------------------------------

@dataclass
class DelegationAccountabilityPacketSideEffects:
    """Hard proof that P1.8.15 is non-verifying, non-projecting, non-approving,
    non-executing, non-writing, non-passporting, and non-mutating.
    All fields default to False."""

    accountability_verified: bool = False
    component_verified: bool = False
    coverage_verified: bool = False
    compliance_proven: bool = False
    projection_created: bool = False
    api_event_contract_created: bool = False
    cli_shell_tui_bound: bool = False
    policy_decision_emitted: bool = False
    custos_decision_emitted: bool = False
    approval_created: bool = False
    runtime_executed: bool = False
    trace_written: bool = False
    ledger_written: bool = False
    audit_finalized: bool = False
    evidence_verified: bool = False
    output_passport_created: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False


# ---------------------------------------------------------------------------
# Private enum parsers
# ---------------------------------------------------------------------------

def _parse_accountability_packet_kind(
    value: DelegationAccountabilityPacketKind | str,
) -> DelegationAccountabilityPacketKind:
    if isinstance(value, DelegationAccountabilityPacketKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationAccountabilityPacketKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid packet_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="packet_kind",
            ) from exc
    raise DelegationError(
        "packet_kind must be a string or DelegationAccountabilityPacketKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="packet_kind",
    )


def _parse_accountability_packet_reference_status(
    value: DelegationAccountabilityPacketReferenceStatus | str,
) -> DelegationAccountabilityPacketReferenceStatus:
    if isinstance(value, DelegationAccountabilityPacketReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationAccountabilityPacketReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationAccountabilityPacketReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )


def _parse_accountability_packet_status(
    value: DelegationAccountabilityPacketStatus | str,
) -> DelegationAccountabilityPacketStatus:
    if isinstance(value, DelegationAccountabilityPacketStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationAccountabilityPacketStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid packet_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="packet_status",
            ) from exc
    raise DelegationError(
        "packet_status must be a string or DelegationAccountabilityPacketStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="packet_status",
    )


def _parse_component_family(
    value: DelegationAccountabilityComponentFamily | str,
) -> DelegationAccountabilityComponentFamily:
    if isinstance(value, DelegationAccountabilityComponentFamily):
        return value
    if isinstance(value, str):
        try:
            return DelegationAccountabilityComponentFamily(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid component_family: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="component_family",
            ) from exc
    raise DelegationError(
        "component_family must be a string or DelegationAccountabilityComponentFamily",
        code=DelegationErrorCode.INVALID_ENUM,
        field="component_family",
    )


# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DelegationAccountabilityComponentRef:
    """One reference-only component summary for a major P1.8 component family.

    Boundary: AccountabilityComponentRef describes component coverage metadata.
    It does not verify the component. It does not prove accountability.
    It does not create TRACE_VERIFIED state.
    """

    schema_version: str
    component_ref_id: str
    delegation_ref_id: str
    component_family: DelegationAccountabilityComponentFamily
    component_ref: str | None
    component_description: str
    component_hash: str
    source_label: DelegationSourceLabel
    reference_status: DelegationAccountabilityPacketReferenceStatus
    packet_status: DelegationAccountabilityPacketStatus
    component_ref_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "component_ref_id": self.component_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "component_family": self.component_family.value,
            "component_ref": self.component_ref,
            "component_description": self.component_description,
            "component_hash": self.component_hash,
            "source_label": self.source_label.value,
            "reference_status": self.reference_status.value,
            "packet_status": self.packet_status.value,
            "component_ref_hash": self.component_ref_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityCoverageMatrixEntry:
    """One present/missing coverage row for a P1.8 component family.

    Boundary: CoverageMatrixEntry is not verification.
    Component presence is not proof.
    Finding count is not risk/trust/compliance score.
    Missing component is not runtime failure.
    """

    schema_version: str
    entry_id: str
    delegation_ref_id: str
    component_family: DelegationAccountabilityComponentFamily
    present: bool
    hash_present: bool
    source_label_present: bool
    finding_count: int
    unavailable_reason: str
    source_label: DelegationSourceLabel
    entry_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "delegation_ref_id": self.delegation_ref_id,
            "component_family": self.component_family.value,
            "present": self.present,
            "hash_present": self.hash_present,
            "source_label_present": self.source_label_present,
            "finding_count": self.finding_count,
            "unavailable_reason": self.unavailable_reason,
            "source_label": self.source_label.value,
            "entry_hash": self.entry_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityCoverageMatrix:
    """Lightweight reference-only matrix of P1.8 component coverage.

    Boundary: CoverageMatrix is not verification.
    CoverageMatrix is not compliance proof.
    CoverageMatrix is not accountability proof.
    CoverageMatrix is not projection/API contract.
    """

    schema_version: str
    coverage_matrix_id: str
    delegation_ref_id: str
    entries: tuple[DelegationAccountabilityCoverageMatrixEntry, ...]
    source_label: DelegationSourceLabel
    coverage_matrix_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "coverage_matrix_id": self.coverage_matrix_id,
            "delegation_ref_id": self.delegation_ref_id,
            "entries": [e.to_canonical_dict() for e in self.entries],
            "source_label": self.source_label.value,
            "coverage_matrix_hash": self.coverage_matrix_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityProfile:
    """Present/missing/unavailable accountability summary profile, not proof
    or score.

    Boundary: AccountabilityProfile is not accountability proof.
    AccountabilityProfile is not verification.
    AccountabilityProfile is not compliance score.
    AccountabilityProfile is not product-surface readiness.
    """

    schema_version: str
    accountability_profile_id: str
    delegation_ref_id: str
    has_foundation_context: bool
    has_identity_context: bool
    has_role_context: bool
    has_constraint_context: bool
    has_authority_context: bool
    has_evidence_context: bool
    has_identity_mesh_context: bool
    has_scope_context: bool
    has_lifecycle_context: bool
    has_chain_context: bool
    has_shadow_resolver_context: bool
    has_operator_review_context: bool
    has_policy_custos_bridge_context: bool
    has_runtime_execution_readiness_context: bool
    has_trace_audit_bridge_context: bool
    missing_components: tuple[str, ...]
    projection_unavailable_reason: str
    api_event_contract_unavailable_reason: str
    cli_shell_tui_unavailable_reason: str
    trace_verification_unavailable_reason: str
    ledger_finality_unavailable_reason: str
    output_passport_unavailable_reason: str
    accountability_verification_unavailable_reason: str
    source_label: DelegationSourceLabel
    profile_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "accountability_profile_id": self.accountability_profile_id,
            "delegation_ref_id": self.delegation_ref_id,
            "has_foundation_context": self.has_foundation_context,
            "has_identity_context": self.has_identity_context,
            "has_role_context": self.has_role_context,
            "has_constraint_context": self.has_constraint_context,
            "has_authority_context": self.has_authority_context,
            "has_evidence_context": self.has_evidence_context,
            "has_identity_mesh_context": self.has_identity_mesh_context,
            "has_scope_context": self.has_scope_context,
            "has_lifecycle_context": self.has_lifecycle_context,
            "has_chain_context": self.has_chain_context,
            "has_shadow_resolver_context": self.has_shadow_resolver_context,
            "has_operator_review_context": self.has_operator_review_context,
            "has_policy_custos_bridge_context": self.has_policy_custos_bridge_context,
            "has_runtime_execution_readiness_context": self.has_runtime_execution_readiness_context,
            "has_trace_audit_bridge_context": self.has_trace_audit_bridge_context,
            "missing_components": list(self.missing_components),
            "projection_unavailable_reason": self.projection_unavailable_reason,
            "api_event_contract_unavailable_reason": self.api_event_contract_unavailable_reason,
            "cli_shell_tui_unavailable_reason": self.cli_shell_tui_unavailable_reason,
            "trace_verification_unavailable_reason": self.trace_verification_unavailable_reason,
            "ledger_finality_unavailable_reason": self.ledger_finality_unavailable_reason,
            "output_passport_unavailable_reason": self.output_passport_unavailable_reason,
            "accountability_verification_unavailable_reason": self.accountability_verification_unavailable_reason,
            "source_label": self.source_label.value,
            "profile_hash": self.profile_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationIntegrationSummaryRef:
    """One reference-only integration summary metadata object.

    Boundary: IntegrationSummaryRef describes future summary metadata.
    It does not mean the system is integrated.
    It does not create projection/API contract.
    It does not verify the component stack.
    """

    schema_version: str
    integration_summary_ref_id: str
    delegation_ref_id: str
    integration_summary_ref: str | None
    integration_summary_description: str
    reference_status: DelegationAccountabilityPacketReferenceStatus
    source_label: DelegationSourceLabel
    packet_status: DelegationAccountabilityPacketStatus
    integration_summary_ref_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "integration_summary_ref_id": self.integration_summary_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "integration_summary_ref": self.integration_summary_ref,
            "integration_summary_description": self.integration_summary_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "packet_status": self.packet_status.value,
            "integration_summary_ref_hash": self.integration_summary_ref_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationIntegrationSummaryEnvelope:
    """Deterministic packet around all major P1.8 context hashes and component
    refs.

    Boundary: IntegrationSummaryEnvelope is a backend summary packet.
    It is not system integration.
    It is not projection/API contract.
    It is not TRACE_VERIFIED.
    It is not accountability proof.
    It does not verify components or create product surfaces.
    """

    schema_version: str
    integration_summary_envelope_id: str
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
    shadow_resolver_result_hash: str
    operator_review_binding_set_hash: str
    policy_custos_bridge_binding_set_hash: str
    runtime_execution_readiness_binding_set_hash: str
    trace_audit_bridge_binding_set_hash: str
    component_refs: tuple[DelegationAccountabilityComponentRef, ...]
    coverage_matrix_hash: str
    accountability_profile_hash: str
    source_label: DelegationSourceLabel
    integration_summary_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "integration_summary_envelope_id": self.integration_summary_envelope_id,
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
            "shadow_resolver_result_hash": self.shadow_resolver_result_hash,
            "operator_review_binding_set_hash": self.operator_review_binding_set_hash,
            "policy_custos_bridge_binding_set_hash": self.policy_custos_bridge_binding_set_hash,
            "runtime_execution_readiness_binding_set_hash": self.runtime_execution_readiness_binding_set_hash,
            "trace_audit_bridge_binding_set_hash": self.trace_audit_bridge_binding_set_hash,
            "component_refs": [cr.to_canonical_dict() for cr in self.component_refs],
            "coverage_matrix_hash": self.coverage_matrix_hash,
            "accountability_profile_hash": self.accountability_profile_hash,
            "source_label": self.source_label.value,
            "integration_summary_envelope_hash": self.integration_summary_envelope_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityPacketEnvelope:
    """Future-facing deterministic packet wrapper around integration summary
    envelope and related metadata.

    Boundary: AccountabilityPacketEnvelope exists does not prove accountability.
    AccountabilityPacketEnvelope hash is not TRACE_VERIFIED.
    AccountabilityPacketEnvelope is not Output Passport.
    AccountabilityPacketEnvelope is not section seal.
    AccountabilityPacketEnvelope is not projection/API contract.
    """

    schema_version: str
    accountability_packet_envelope_id: str
    delegation_ref_id: str
    integration_summary_envelope_hash: str
    component_refs: tuple[DelegationAccountabilityComponentRef, ...]
    coverage_matrix_hash: str
    accountability_profile_hash: str
    trace_audit_bridge_binding_set_hash: str
    golden_thread_ref: str
    next_handoff_ref: str
    source_label: DelegationSourceLabel
    accountability_packet_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "accountability_packet_envelope_id": self.accountability_packet_envelope_id,
            "delegation_ref_id": self.delegation_ref_id,
            "integration_summary_envelope_hash": self.integration_summary_envelope_hash,
            "component_refs": [cr.to_canonical_dict() for cr in self.component_refs],
            "coverage_matrix_hash": self.coverage_matrix_hash,
            "accountability_profile_hash": self.accountability_profile_hash,
            "trace_audit_bridge_binding_set_hash": self.trace_audit_bridge_binding_set_hash,
            "golden_thread_ref": self.golden_thread_ref,
            "next_handoff_ref": self.next_handoff_ref,
            "source_label": self.source_label.value,
            "accountability_packet_envelope_hash": self.accountability_packet_envelope_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityPacketBinding:
    """Binding between accountability packet envelope and full P1.8 context
    hashes.

    Boundary: AccountabilityPacketBinding binds summary metadata.
    It is not proof. It is not verification. It is not trace verification.
    It is not Ledger finality. It is not projection/API contract.
    """

    schema_version: str
    binding_id: str
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
    shadow_resolver_result_hash: str
    operator_review_binding_set_hash: str
    policy_custos_bridge_binding_set_hash: str
    runtime_execution_readiness_binding_set_hash: str
    trace_audit_bridge_binding_set_hash: str
    integration_summary_envelope_hash: str
    accountability_packet_envelope_hash: str
    coverage_matrix_hash: str
    accountability_profile_hash: str
    source_label: DelegationSourceLabel
    packet_status: DelegationAccountabilityPacketStatus
    binding_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "binding_id": self.binding_id,
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
            "shadow_resolver_result_hash": self.shadow_resolver_result_hash,
            "operator_review_binding_set_hash": self.operator_review_binding_set_hash,
            "policy_custos_bridge_binding_set_hash": self.policy_custos_bridge_binding_set_hash,
            "runtime_execution_readiness_binding_set_hash": self.runtime_execution_readiness_binding_set_hash,
            "trace_audit_bridge_binding_set_hash": self.trace_audit_bridge_binding_set_hash,
            "integration_summary_envelope_hash": self.integration_summary_envelope_hash,
            "accountability_packet_envelope_hash": self.accountability_packet_envelope_hash,
            "coverage_matrix_hash": self.coverage_matrix_hash,
            "accountability_profile_hash": self.accountability_profile_hash,
            "source_label": self.source_label.value,
            "packet_status": self.packet_status.value,
            "binding_hash": self.binding_hash,
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityPacketBindingSet:
    """Collection of accountability packet bindings for one delegation.

    Boundary: AccountabilityPacketBindingSet describes summary hooks.
    It does not verify accountability, verify components, prove compliance,
    create projection, bind CLI, approve, execute, write trace, write Ledger,
    finalize audit, verify evidence, create Output Passport, or mutate runtime.
    """

    schema_version: str
    accountability_packet_binding_set_id: str
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
    shadow_resolver_result_hash: str
    operator_review_binding_set_hash: str
    policy_custos_bridge_binding_set_hash: str
    runtime_execution_readiness_binding_set_hash: str
    trace_audit_bridge_binding_set_hash: str
    bindings: tuple[DelegationAccountabilityPacketBinding, ...]
    source_label: DelegationSourceLabel
    accountability_packet_binding_set_hash: str
    side_effects: DelegationAccountabilityPacketSideEffects

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "accountability_packet_binding_set_id": self.accountability_packet_binding_set_id,
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
            "shadow_resolver_result_hash": self.shadow_resolver_result_hash,
            "operator_review_binding_set_hash": self.operator_review_binding_set_hash,
            "policy_custos_bridge_binding_set_hash": self.policy_custos_bridge_binding_set_hash,
            "runtime_execution_readiness_binding_set_hash": self.runtime_execution_readiness_binding_set_hash,
            "trace_audit_bridge_binding_set_hash": self.trace_audit_bridge_binding_set_hash,
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "source_label": self.source_label.value,
            "accountability_packet_binding_set_hash": self.accountability_packet_binding_set_hash,
            "side_effects": {
                f.name: getattr(self.side_effects, f.name)
                for f in fields(DelegationAccountabilityPacketSideEffects)
            },
        }
        return result


@dataclass(frozen=True)
class DelegationAccountabilityPacketStatusReport:
    """Reports accountability packet model capability and unavailable surfaces.

    Boundary: StatusReport is reference-only metadata reporting.
    It does not prove accountability. It does not verify components.
    It does not prove compliance. It does not create projection/API contract.
    """

    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: dict[str, str]
    side_effects: DelegationAccountabilityPacketSideEffects
    status_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "status_label": self.status_label,
            "available_contracts": list(self.available_contracts),
            "unavailable_bindings": dict(self.unavailable_bindings),
            "side_effects": {
                f.name: getattr(self.side_effects, f.name)
                for f in fields(DelegationAccountabilityPacketSideEffects)
            },
            "status_hash": self.status_hash,
        }
        return result


# ---------------------------------------------------------------------------
# Private compute-hash helpers
# ---------------------------------------------------------------------------

def _compute_accountability_component_ref_hash(
    *,
    component_family: DelegationAccountabilityComponentFamily,
    component_ref: str | None,
    component_description: str,
    component_hash: str,
    reference_status: DelegationAccountabilityPacketReferenceStatus,
    source_label: DelegationSourceLabel,
    packet_status: DelegationAccountabilityPacketStatus,
) -> str:
    return stable_hash({
        "component_family": component_family.value,
        "component_ref": component_ref,
        "component_description": component_description,
        "component_hash": component_hash,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "packet_status": packet_status.value,
    })


def _compute_coverage_matrix_entry_hash(
    *,
    component_family: DelegationAccountabilityComponentFamily,
    present: bool,
    hash_present: bool,
    source_label_present: bool,
    finding_count: int,
    unavailable_reason: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "component_family": component_family.value,
        "present": present,
        "hash_present": hash_present,
        "source_label_present": source_label_present,
        "finding_count": finding_count,
        "unavailable_reason": unavailable_reason,
        "source_label": source_label.value,
    })


def _compute_coverage_matrix_hash(
    *,
    entry_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "entry_hashes": list(entry_hashes),
        "source_label": source_label.value,
    })


def _compute_accountability_profile_hash(
    *,
    has_foundation_context: bool,
    has_identity_context: bool,
    has_role_context: bool,
    has_constraint_context: bool,
    has_authority_context: bool,
    has_evidence_context: bool,
    has_identity_mesh_context: bool,
    has_scope_context: bool,
    has_lifecycle_context: bool,
    has_chain_context: bool,
    has_shadow_resolver_context: bool,
    has_operator_review_context: bool,
    has_policy_custos_bridge_context: bool,
    has_runtime_execution_readiness_context: bool,
    has_trace_audit_bridge_context: bool,
    missing_components: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "has_foundation_context": has_foundation_context,
        "has_identity_context": has_identity_context,
        "has_role_context": has_role_context,
        "has_constraint_context": has_constraint_context,
        "has_authority_context": has_authority_context,
        "has_evidence_context": has_evidence_context,
        "has_identity_mesh_context": has_identity_mesh_context,
        "has_scope_context": has_scope_context,
        "has_lifecycle_context": has_lifecycle_context,
        "has_chain_context": has_chain_context,
        "has_shadow_resolver_context": has_shadow_resolver_context,
        "has_operator_review_context": has_operator_review_context,
        "has_policy_custos_bridge_context": has_policy_custos_bridge_context,
        "has_runtime_execution_readiness_context": has_runtime_execution_readiness_context,
        "has_trace_audit_bridge_context": has_trace_audit_bridge_context,
        "missing_components": list(missing_components),
        "source_label": source_label.value,
    })


def _compute_integration_summary_ref_hash(
    *,
    integration_summary_ref: str | None,
    integration_summary_description: str,
    reference_status: DelegationAccountabilityPacketReferenceStatus,
    source_label: DelegationSourceLabel,
    packet_status: DelegationAccountabilityPacketStatus,
) -> str:
    return stable_hash({
        "integration_summary_ref": integration_summary_ref,
        "integration_summary_description": integration_summary_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "packet_status": packet_status.value,
    })


def _compute_integration_summary_envelope_hash(
    *,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_binding_set_hash: str,
    chain_binding_set_hash: str,
    shadow_resolver_result_hash: str,
    operator_review_binding_set_hash: str,
    policy_custos_bridge_binding_set_hash: str,
    runtime_execution_readiness_binding_set_hash: str,
    trace_audit_bridge_binding_set_hash: str,
    component_ref_hashes: tuple[str, ...],
    coverage_matrix_hash: str,
    accountability_profile_hash: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "delegation_identity_hash": delegation_identity_hash,
        "role_binding_hash": role_binding_hash,
        "constraint_set_hash": constraint_set_hash,
        "authority_binding_set_hash": authority_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "scope_binding_set_hash": scope_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "chain_binding_set_hash": chain_binding_set_hash,
        "shadow_resolver_result_hash": shadow_resolver_result_hash,
        "operator_review_binding_set_hash": operator_review_binding_set_hash,
        "policy_custos_bridge_binding_set_hash": policy_custos_bridge_binding_set_hash,
        "runtime_execution_readiness_binding_set_hash": runtime_execution_readiness_binding_set_hash,
        "trace_audit_bridge_binding_set_hash": trace_audit_bridge_binding_set_hash,
        "component_ref_hashes": list(component_ref_hashes),
        "coverage_matrix_hash": coverage_matrix_hash,
        "accountability_profile_hash": accountability_profile_hash,
        "source_label": source_label.value,
    })


def _compute_accountability_packet_envelope_hash(
    *,
    integration_summary_envelope_hash: str,
    component_ref_hashes: tuple[str, ...],
    coverage_matrix_hash: str,
    accountability_profile_hash: str,
    trace_audit_bridge_binding_set_hash: str,
    golden_thread_ref: str,
    next_handoff_ref: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "integration_summary_envelope_hash": integration_summary_envelope_hash,
        "component_ref_hashes": list(component_ref_hashes),
        "coverage_matrix_hash": coverage_matrix_hash,
        "accountability_profile_hash": accountability_profile_hash,
        "trace_audit_bridge_binding_set_hash": trace_audit_bridge_binding_set_hash,
        "golden_thread_ref": golden_thread_ref,
        "next_handoff_ref": next_handoff_ref,
        "source_label": source_label.value,
    })


def _compute_accountability_packet_binding_hash(
    *,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_binding_set_hash: str,
    chain_binding_set_hash: str,
    shadow_resolver_result_hash: str,
    operator_review_binding_set_hash: str,
    policy_custos_bridge_binding_set_hash: str,
    runtime_execution_readiness_binding_set_hash: str,
    trace_audit_bridge_binding_set_hash: str,
    integration_summary_envelope_hash: str,
    accountability_packet_envelope_hash: str,
    coverage_matrix_hash: str,
    accountability_profile_hash: str,
    source_label: DelegationSourceLabel,
    packet_status: DelegationAccountabilityPacketStatus,
) -> str:
    return stable_hash({
        "delegation_identity_hash": delegation_identity_hash,
        "role_binding_hash": role_binding_hash,
        "constraint_set_hash": constraint_set_hash,
        "authority_binding_set_hash": authority_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "scope_binding_set_hash": scope_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "chain_binding_set_hash": chain_binding_set_hash,
        "shadow_resolver_result_hash": shadow_resolver_result_hash,
        "operator_review_binding_set_hash": operator_review_binding_set_hash,
        "policy_custos_bridge_binding_set_hash": policy_custos_bridge_binding_set_hash,
        "runtime_execution_readiness_binding_set_hash": runtime_execution_readiness_binding_set_hash,
        "trace_audit_bridge_binding_set_hash": trace_audit_bridge_binding_set_hash,
        "integration_summary_envelope_hash": integration_summary_envelope_hash,
        "accountability_packet_envelope_hash": accountability_packet_envelope_hash,
        "coverage_matrix_hash": coverage_matrix_hash,
        "accountability_profile_hash": accountability_profile_hash,
        "source_label": source_label.value,
        "packet_status": packet_status.value,
    })


def _compute_accountability_packet_binding_set_hash(
    *,
    delegation_identity_hash: str,
    role_binding_hash: str,
    constraint_set_hash: str,
    authority_binding_set_hash: str,
    non_repudiation_binding_set_hash: str,
    identity_mesh_binding_set_hash: str,
    scope_binding_set_hash: str,
    lifecycle_binding_set_hash: str,
    chain_binding_set_hash: str,
    shadow_resolver_result_hash: str,
    operator_review_binding_set_hash: str,
    policy_custos_bridge_binding_set_hash: str,
    runtime_execution_readiness_binding_set_hash: str,
    trace_audit_bridge_binding_set_hash: str,
    binding_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "delegation_identity_hash": delegation_identity_hash,
        "role_binding_hash": role_binding_hash,
        "constraint_set_hash": constraint_set_hash,
        "authority_binding_set_hash": authority_binding_set_hash,
        "non_repudiation_binding_set_hash": non_repudiation_binding_set_hash,
        "identity_mesh_binding_set_hash": identity_mesh_binding_set_hash,
        "scope_binding_set_hash": scope_binding_set_hash,
        "lifecycle_binding_set_hash": lifecycle_binding_set_hash,
        "chain_binding_set_hash": chain_binding_set_hash,
        "shadow_resolver_result_hash": shadow_resolver_result_hash,
        "operator_review_binding_set_hash": operator_review_binding_set_hash,
        "policy_custos_bridge_binding_set_hash": policy_custos_bridge_binding_set_hash,
        "runtime_execution_readiness_binding_set_hash": runtime_execution_readiness_binding_set_hash,
        "trace_audit_bridge_binding_set_hash": trace_audit_bridge_binding_set_hash,
        "binding_hashes": list(binding_hashes),
        "source_label": source_label.value,
    })


def _compute_accountability_packet_status_report_hash(
    *,
    status_label: str,
    available_contracts: tuple[str, ...],
    unavailable_bindings: dict[str, str],
) -> str:
    return stable_hash({
        "status_label": status_label,
        "available_contracts": list(available_contracts),
        "unavailable_bindings": dict(unavailable_bindings),
    })


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------

def build_delegation_accountability_component_ref(
    *,
    component_ref_id: str,
    delegation_ref_id: str,
    component_family: DelegationAccountabilityComponentFamily | str = DelegationAccountabilityComponentFamily.UNKNOWN,
    component_ref: str | None = None,
    component_description: str = "",
    component_hash: str = "",
    reference_status: DelegationAccountabilityPacketReferenceStatus | str = DelegationAccountabilityPacketReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    packet_status: DelegationAccountabilityPacketStatus | str = DelegationAccountabilityPacketStatus.REFERENCE_ONLY,
) -> DelegationAccountabilityComponentRef:
    component_family_val = _parse_component_family(component_family)
    reference_status_val = _parse_accountability_packet_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    packet_status_val = _parse_accountability_packet_status(packet_status)
    component_ref_hash_val = _compute_accountability_component_ref_hash(
        component_family=component_family_val,
        component_ref=component_ref,
        component_description=component_description,
        component_hash=component_hash,
        reference_status=reference_status_val,
        source_label=source_label_val,
        packet_status=packet_status_val,
    )
    return DelegationAccountabilityComponentRef(
        schema_version=DELEGATION_ACCOUNTABILITY_COMPONENT_REF_VERSION,
        component_ref_id=component_ref_id,
        delegation_ref_id=delegation_ref_id,
        component_family=component_family_val,
        component_ref=component_ref,
        component_description=component_description,
        component_hash=component_hash,
        source_label=source_label_val,
        reference_status=reference_status_val,
        packet_status=packet_status_val,
        component_ref_hash=component_ref_hash_val,
    )


def build_delegation_accountability_coverage_matrix_entry(
    *,
    entry_id: str,
    delegation_ref_id: str,
    component_family: DelegationAccountabilityComponentFamily | str = DelegationAccountabilityComponentFamily.UNKNOWN,
    present: bool = False,
    hash_present: bool = False,
    source_label_present: bool = False,
    finding_count: int = 0,
    unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAccountabilityCoverageMatrixEntry:
    component_family_val = _parse_component_family(component_family)
    source_label_val = _parse_source_label(source_label)
    entry_hash_val = _compute_coverage_matrix_entry_hash(
        component_family=component_family_val,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=source_label_val,
    )
    return DelegationAccountabilityCoverageMatrixEntry(
        schema_version=DELEGATION_ACCOUNTABILITY_COVERAGE_MATRIX_ENTRY_VERSION,
        entry_id=entry_id,
        delegation_ref_id=delegation_ref_id,
        component_family=component_family_val,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=source_label_val,
        entry_hash=entry_hash_val,
    )


def build_delegation_accountability_coverage_matrix(
    *,
    coverage_matrix_id: str,
    delegation_ref_id: str,
    entries: Sequence[DelegationAccountabilityCoverageMatrixEntry] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAccountabilityCoverageMatrix:
    source_label_val = _parse_source_label(source_label)
    entries_tuple = tuple(entries)
    entry_hashes = tuple(e.entry_hash for e in entries_tuple)
    matrix_hash_val = _compute_coverage_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=source_label_val,
    )
    return DelegationAccountabilityCoverageMatrix(
        schema_version=DELEGATION_ACCOUNTABILITY_COVERAGE_MATRIX_VERSION,
        coverage_matrix_id=coverage_matrix_id,
        delegation_ref_id=delegation_ref_id,
        entries=entries_tuple,
        source_label=source_label_val,
        coverage_matrix_hash=matrix_hash_val,
    )


def build_delegation_accountability_profile(
    *,
    accountability_profile_id: str,
    delegation_ref_id: str,
    has_foundation_context: bool = False,
    has_identity_context: bool = False,
    has_role_context: bool = False,
    has_constraint_context: bool = False,
    has_authority_context: bool = False,
    has_evidence_context: bool = False,
    has_identity_mesh_context: bool = False,
    has_scope_context: bool = False,
    has_lifecycle_context: bool = False,
    has_chain_context: bool = False,
    has_shadow_resolver_context: bool = False,
    has_operator_review_context: bool = False,
    has_policy_custos_bridge_context: bool = False,
    has_runtime_execution_readiness_context: bool = False,
    has_trace_audit_bridge_context: bool = False,
    missing_components: Sequence[str] = (),
    projection_unavailable_reason: str = "",
    api_event_contract_unavailable_reason: str = "",
    cli_shell_tui_unavailable_reason: str = "",
    trace_verification_unavailable_reason: str = "",
    ledger_finality_unavailable_reason: str = "",
    output_passport_unavailable_reason: str = "",
    accountability_verification_unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAccountabilityProfile:
    source_label_val = _parse_source_label(source_label)
    missing_tuple = tuple(missing_components)
    profile_hash_val = _compute_accountability_profile_hash(
        has_foundation_context=has_foundation_context,
        has_identity_context=has_identity_context,
        has_role_context=has_role_context,
        has_constraint_context=has_constraint_context,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        has_identity_mesh_context=has_identity_mesh_context,
        has_scope_context=has_scope_context,
        has_lifecycle_context=has_lifecycle_context,
        has_chain_context=has_chain_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_operator_review_context=has_operator_review_context,
        has_policy_custos_bridge_context=has_policy_custos_bridge_context,
        has_runtime_execution_readiness_context=has_runtime_execution_readiness_context,
        has_trace_audit_bridge_context=has_trace_audit_bridge_context,
        missing_components=missing_tuple,
        source_label=source_label_val,
    )
    return DelegationAccountabilityProfile(
        schema_version=DELEGATION_ACCOUNTABILITY_PROFILE_VERSION,
        accountability_profile_id=accountability_profile_id,
        delegation_ref_id=delegation_ref_id,
        has_foundation_context=has_foundation_context,
        has_identity_context=has_identity_context,
        has_role_context=has_role_context,
        has_constraint_context=has_constraint_context,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        has_identity_mesh_context=has_identity_mesh_context,
        has_scope_context=has_scope_context,
        has_lifecycle_context=has_lifecycle_context,
        has_chain_context=has_chain_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_operator_review_context=has_operator_review_context,
        has_policy_custos_bridge_context=has_policy_custos_bridge_context,
        has_runtime_execution_readiness_context=has_runtime_execution_readiness_context,
        has_trace_audit_bridge_context=has_trace_audit_bridge_context,
        missing_components=missing_tuple,
        projection_unavailable_reason=projection_unavailable_reason,
        api_event_contract_unavailable_reason=api_event_contract_unavailable_reason,
        cli_shell_tui_unavailable_reason=cli_shell_tui_unavailable_reason,
        trace_verification_unavailable_reason=trace_verification_unavailable_reason,
        ledger_finality_unavailable_reason=ledger_finality_unavailable_reason,
        output_passport_unavailable_reason=output_passport_unavailable_reason,
        accountability_verification_unavailable_reason=accountability_verification_unavailable_reason,
        source_label=source_label_val,
        profile_hash=profile_hash_val,
    )


def build_delegation_integration_summary_ref(
    *,
    integration_summary_ref_id: str,
    delegation_ref_id: str,
    integration_summary_ref: str | None = None,
    integration_summary_description: str = "",
    reference_status: DelegationAccountabilityPacketReferenceStatus | str = DelegationAccountabilityPacketReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    packet_status: DelegationAccountabilityPacketStatus | str = DelegationAccountabilityPacketStatus.REFERENCE_ONLY,
) -> DelegationIntegrationSummaryRef:
    reference_status_val = _parse_accountability_packet_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    packet_status_val = _parse_accountability_packet_status(packet_status)
    integration_summary_ref_hash_val = _compute_integration_summary_ref_hash(
        integration_summary_ref=integration_summary_ref,
        integration_summary_description=integration_summary_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        packet_status=packet_status_val,
    )
    return DelegationIntegrationSummaryRef(
        schema_version=DELEGATION_INTEGRATION_SUMMARY_REF_VERSION,
        integration_summary_ref_id=integration_summary_ref_id,
        delegation_ref_id=delegation_ref_id,
        integration_summary_ref=integration_summary_ref,
        integration_summary_description=integration_summary_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        packet_status=packet_status_val,
        integration_summary_ref_hash=integration_summary_ref_hash_val,
    )


def build_delegation_integration_summary_envelope(
    *,
    integration_summary_envelope_id: str,
    delegation_ref_id: str,
    delegation_identity_hash: str = "",
    role_binding_hash: str = "",
    constraint_set_hash: str = "",
    authority_binding_set_hash: str = "",
    non_repudiation_binding_set_hash: str = "",
    identity_mesh_binding_set_hash: str = "",
    scope_binding_set_hash: str = "",
    lifecycle_binding_set_hash: str = "",
    chain_binding_set_hash: str = "",
    shadow_resolver_result_hash: str = "",
    operator_review_binding_set_hash: str = "",
    policy_custos_bridge_binding_set_hash: str = "",
    runtime_execution_readiness_binding_set_hash: str = "",
    trace_audit_bridge_binding_set_hash: str = "",
    component_refs: Sequence[DelegationAccountabilityComponentRef] = (),
    coverage_matrix_hash: str = "",
    accountability_profile_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationIntegrationSummaryEnvelope:
    source_label_val = _parse_source_label(source_label)
    component_refs_tuple = tuple(component_refs)
    component_ref_hashes = tuple(cr.component_ref_hash for cr in component_refs_tuple)
    envelope_hash_val = _compute_integration_summary_envelope_hash(
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_binding_set_hash=operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        component_ref_hashes=component_ref_hashes,
        coverage_matrix_hash=coverage_matrix_hash,
        accountability_profile_hash=accountability_profile_hash,
        source_label=source_label_val,
    )
    return DelegationIntegrationSummaryEnvelope(
        schema_version=DELEGATION_INTEGRATION_SUMMARY_ENVELOPE_VERSION,
        integration_summary_envelope_id=integration_summary_envelope_id,
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
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_binding_set_hash=operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        component_refs=component_refs_tuple,
        coverage_matrix_hash=coverage_matrix_hash,
        accountability_profile_hash=accountability_profile_hash,
        source_label=source_label_val,
        integration_summary_envelope_hash=envelope_hash_val,
    )


def build_delegation_accountability_packet_envelope(
    *,
    accountability_packet_envelope_id: str,
    delegation_ref_id: str,
    integration_summary_envelope_hash: str = "",
    component_refs: Sequence[DelegationAccountabilityComponentRef] = (),
    coverage_matrix_hash: str = "",
    accountability_profile_hash: str = "",
    trace_audit_bridge_binding_set_hash: str = "",
    golden_thread_ref: str = "",
    next_handoff_ref: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAccountabilityPacketEnvelope:
    source_label_val = _parse_source_label(source_label)
    component_refs_tuple = tuple(component_refs)
    component_ref_hashes = tuple(cr.component_ref_hash for cr in component_refs_tuple)
    packet_env_hash_val = _compute_accountability_packet_envelope_hash(
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        component_ref_hashes=component_ref_hashes,
        coverage_matrix_hash=coverage_matrix_hash,
        accountability_profile_hash=accountability_profile_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        golden_thread_ref=golden_thread_ref,
        next_handoff_ref=next_handoff_ref,
        source_label=source_label_val,
    )
    return DelegationAccountabilityPacketEnvelope(
        schema_version=DELEGATION_ACCOUNTABILITY_PACKET_ENVELOPE_VERSION,
        accountability_packet_envelope_id=accountability_packet_envelope_id,
        delegation_ref_id=delegation_ref_id,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        component_refs=component_refs_tuple,
        coverage_matrix_hash=coverage_matrix_hash,
        accountability_profile_hash=accountability_profile_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        golden_thread_ref=golden_thread_ref,
        next_handoff_ref=next_handoff_ref,
        source_label=source_label_val,
        accountability_packet_envelope_hash=packet_env_hash_val,
    )


def build_delegation_accountability_packet_binding(
    *,
    binding_id: str,
    delegation_ref_id: str,
    delegation_identity_hash: str = "",
    role_binding_hash: str = "",
    constraint_set_hash: str = "",
    authority_binding_set_hash: str = "",
    non_repudiation_binding_set_hash: str = "",
    identity_mesh_binding_set_hash: str = "",
    scope_binding_set_hash: str = "",
    lifecycle_binding_set_hash: str = "",
    chain_binding_set_hash: str = "",
    shadow_resolver_result_hash: str = "",
    operator_review_binding_set_hash: str = "",
    policy_custos_bridge_binding_set_hash: str = "",
    runtime_execution_readiness_binding_set_hash: str = "",
    trace_audit_bridge_binding_set_hash: str = "",
    integration_summary_envelope_hash: str = "",
    accountability_packet_envelope_hash: str = "",
    coverage_matrix_hash: str = "",
    accountability_profile_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    packet_status: DelegationAccountabilityPacketStatus | str = DelegationAccountabilityPacketStatus.REFERENCE_ONLY,
) -> DelegationAccountabilityPacketBinding:
    source_label_val = _parse_source_label(source_label)
    packet_status_val = _parse_accountability_packet_status(packet_status)
    binding_hash_val = _compute_accountability_packet_binding_hash(
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_binding_set_hash=operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        coverage_matrix_hash=coverage_matrix_hash,
        accountability_profile_hash=accountability_profile_hash,
        source_label=source_label_val,
        packet_status=packet_status_val,
    )
    return DelegationAccountabilityPacketBinding(
        schema_version=DELEGATION_ACCOUNTABILITY_PACKET_BINDING_VERSION,
        binding_id=binding_id,
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
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_binding_set_hash=operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        integration_summary_envelope_hash=integration_summary_envelope_hash,
        accountability_packet_envelope_hash=accountability_packet_envelope_hash,
        coverage_matrix_hash=coverage_matrix_hash,
        accountability_profile_hash=accountability_profile_hash,
        source_label=source_label_val,
        packet_status=packet_status_val,
        binding_hash=binding_hash_val,
    )


def build_delegation_accountability_packet_binding_set(
    *,
    accountability_packet_binding_set_id: str,
    delegation_ref_id: str,
    delegation_identity_hash: str = "",
    role_binding_hash: str = "",
    constraint_set_hash: str = "",
    authority_binding_set_hash: str = "",
    non_repudiation_binding_set_hash: str = "",
    identity_mesh_binding_set_hash: str = "",
    scope_binding_set_hash: str = "",
    lifecycle_binding_set_hash: str = "",
    chain_binding_set_hash: str = "",
    shadow_resolver_result_hash: str = "",
    operator_review_binding_set_hash: str = "",
    policy_custos_bridge_binding_set_hash: str = "",
    runtime_execution_readiness_binding_set_hash: str = "",
    trace_audit_bridge_binding_set_hash: str = "",
    bindings: Sequence[DelegationAccountabilityPacketBinding] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationAccountabilityPacketBindingSet:
    source_label_val = _parse_source_label(source_label)
    bindings_tuple = tuple(bindings)
    binding_hashes = tuple(b.binding_hash for b in bindings_tuple)
    set_hash_val = _compute_accountability_packet_binding_set_hash(
        delegation_identity_hash=delegation_identity_hash,
        role_binding_hash=role_binding_hash,
        constraint_set_hash=constraint_set_hash,
        authority_binding_set_hash=authority_binding_set_hash,
        non_repudiation_binding_set_hash=non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=identity_mesh_binding_set_hash,
        scope_binding_set_hash=scope_binding_set_hash,
        lifecycle_binding_set_hash=lifecycle_binding_set_hash,
        chain_binding_set_hash=chain_binding_set_hash,
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_binding_set_hash=operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        binding_hashes=binding_hashes,
        source_label=source_label_val,
    )
    return DelegationAccountabilityPacketBindingSet(
        schema_version=DELEGATION_ACCOUNTABILITY_PACKET_BINDING_SET_VERSION,
        accountability_packet_binding_set_id=accountability_packet_binding_set_id,
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
        shadow_resolver_result_hash=shadow_resolver_result_hash,
        operator_review_binding_set_hash=operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_binding_set_hash=trace_audit_bridge_binding_set_hash,
        bindings=bindings_tuple,
        source_label=source_label_val,
        accountability_packet_binding_set_hash=set_hash_val,
        side_effects=DelegationAccountabilityPacketSideEffects(),
    )


def build_delegation_accountability_packet_status_report(
    *,
    available_contracts: Sequence[str] = (),
    unavailable_bindings: dict[str, str] | None = None,
) -> DelegationAccountabilityPacketStatusReport:
    contracts_tuple = tuple(available_contracts)
    bindings_dict = dict(unavailable_bindings) if unavailable_bindings is not None else {}
    status_hash_val = _compute_accountability_packet_status_report_hash(
        status_label="DEV_FIXTURE — P1.8.15 Accountability Packet / Integration SummaryRef Model is reference-only, non-verifying, non-projecting, non-approving, non-executing, non-writing, non-passporting metadata.",
        available_contracts=contracts_tuple,
        unavailable_bindings=bindings_dict,
    )
    return DelegationAccountabilityPacketStatusReport(
        schema_version=DELEGATION_ACCOUNTABILITY_PACKET_STATUS_REPORT_VERSION,
        status_label=(
            "DEV_FIXTURE — P1.8.15 Accountability Packet / Integration SummaryRef "
            "Model is reference-only, non-verifying, non-projecting, non-approving, "
            "non-executing, non-writing, non-passporting metadata."
        ),
        available_contracts=contracts_tuple,
        unavailable_bindings=bindings_dict,
        side_effects=DelegationAccountabilityPacketSideEffects(),
        status_hash=status_hash_val,
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def serialize_delegation_integration_summary_envelope(
    envelope: DelegationIntegrationSummaryEnvelope,
) -> str:
    """Serialize integration summary envelope to canonical JSON."""
    return to_canonical_json(envelope.to_canonical_dict())


def serialize_delegation_accountability_packet_envelope(
    envelope: DelegationAccountabilityPacketEnvelope,
) -> str:
    """Serialize accountability packet envelope to canonical JSON."""
    return to_canonical_json(envelope.to_canonical_dict())


def serialize_delegation_accountability_packet_binding_set(
    binding_set: DelegationAccountabilityPacketBindingSet,
) -> str:
    """Serialize accountability packet binding set to canonical JSON."""
    return to_canonical_json(binding_set.to_canonical_dict())


# ---------------------------------------------------------------------------
# Hash functions (public)
# ---------------------------------------------------------------------------

def hash_delegation_accountability_component_ref(
    component_ref: DelegationAccountabilityComponentRef,
) -> str:
    """Return pre-computed deterministic component_ref_hash."""
    return component_ref.component_ref_hash


def hash_delegation_accountability_coverage_matrix_entry(
    entry: DelegationAccountabilityCoverageMatrixEntry,
) -> str:
    """Return pre-computed deterministic entry_hash."""
    return entry.entry_hash


def hash_delegation_accountability_coverage_matrix(
    matrix: DelegationAccountabilityCoverageMatrix,
) -> str:
    """Return pre-computed deterministic coverage_matrix_hash."""
    return matrix.coverage_matrix_hash


def hash_delegation_accountability_profile(
    profile: DelegationAccountabilityProfile,
) -> str:
    """Return pre-computed deterministic profile_hash."""
    return profile.profile_hash


def hash_delegation_integration_summary_ref(
    summary_ref: DelegationIntegrationSummaryRef,
) -> str:
    """Return pre-computed deterministic integration_summary_ref_hash."""
    return summary_ref.integration_summary_ref_hash


def hash_delegation_integration_summary_envelope(
    envelope: DelegationIntegrationSummaryEnvelope,
) -> str:
    """Return pre-computed deterministic integration_summary_envelope_hash."""
    return envelope.integration_summary_envelope_hash


def hash_delegation_accountability_packet_envelope(
    envelope: DelegationAccountabilityPacketEnvelope,
) -> str:
    """Return pre-computed deterministic accountability_packet_envelope_hash."""
    return envelope.accountability_packet_envelope_hash


def hash_delegation_accountability_packet_binding(
    binding: DelegationAccountabilityPacketBinding,
) -> str:
    """Return pre-computed deterministic binding_hash."""
    return binding.binding_hash


def hash_delegation_accountability_packet_binding_set(
    binding_set: DelegationAccountabilityPacketBindingSet,
) -> str:
    """Return pre-computed deterministic accountability_packet_binding_set_hash."""
    return binding_set.accountability_packet_binding_set_hash


def hash_delegation_accountability_packet_status_report(
    report: DelegationAccountabilityPacketStatusReport,
) -> str:
    """Return pre-computed deterministic status_hash."""
    return report.status_hash
