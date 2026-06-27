"""Delegation trace/audit bridge reference model (P1.8.14).

Deterministic, versioned, JSON-safe, side-effect-free reference-only
trace/audit/Ledger bridge metadata layer over P1.8.0-P1.8.13 delegation context.

Produces trace bridge refs, audit bridge refs, Ledger bridge refs,
trace event intent refs, audit event intent refs, Ledger entry placeholder
refs, replay context refs, fork context refs, causal chain context refs,
readiness matrix, readiness profile, envelope, binding, and binding set
without trace writer call, audit writer call, Ledger writer call, trace
event emission, audit event emission, Ledger entry write, audit finality,
replay execution, fork creation, causal verification, evidence verification,
Output Passport behavior, P1.9 behavior, trace verification, Ledger finality,
or runtime mutation.

Architectural law:
  - TraceBridgeRef exists does not mean trace written.
  - AuditBridgeRef exists does not mean audit completed.
  - LedgerBridgeRef exists does not mean Ledger entry written.
  - TraceEventIntentRef exists does not mean trace event emitted.
  - AuditEventIntentRef exists does not mean audit event emitted.
  - LedgerEntryPlaceholderRef exists does not mean Ledger entry exists.
  - ReplayContextRef exists does not mean replay executed.
  - ForkContextRef exists does not mean fork created.
  - CausalChainContextRef exists does not mean causal chain verified.
  - TraceAuditReadinessMatrix exists does not mean TRACE_VERIFIED.
  - TraceAuditReadinessProfile exists does not mean audit readiness proof.
  - Trace/audit hash exists does not mean TRACE_VERIFIED.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, fields
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

DELEGATION_TRACE_AUDIT_BRIDGE_TASK_ID = "P1.8.14"
DELEGATION_TRACE_BRIDGE_REF_VERSION = "delegation_trace_bridge_ref.v1"
DELEGATION_AUDIT_BRIDGE_REF_VERSION = "delegation_audit_bridge_ref.v1"
DELEGATION_LEDGER_BRIDGE_REF_VERSION = "delegation_ledger_bridge_ref.v1"
DELEGATION_TRACE_EVENT_INTENT_REF_VERSION = "delegation_trace_event_intent_ref.v1"
DELEGATION_AUDIT_EVENT_INTENT_REF_VERSION = "delegation_audit_event_intent_ref.v1"
DELEGATION_LEDGER_ENTRY_PLACEHOLDER_REF_VERSION = "delegation_ledger_entry_placeholder_ref.v1"
DELEGATION_REPLAY_CONTEXT_REF_VERSION = "delegation_replay_context_ref.v1"
DELEGATION_FORK_CONTEXT_REF_VERSION = "delegation_fork_context_ref.v1"
DELEGATION_CAUSAL_CHAIN_CONTEXT_REF_VERSION = "delegation_causal_chain_context_ref.v1"
DELEGATION_TRACE_AUDIT_READINESS_MATRIX_ENTRY_VERSION = "delegation_trace_audit_readiness_matrix_entry.v1"
DELEGATION_TRACE_AUDIT_READINESS_MATRIX_VERSION = "delegation_trace_audit_readiness_matrix.v1"
DELEGATION_TRACE_AUDIT_READINESS_PROFILE_VERSION = "delegation_trace_audit_readiness_profile.v1"
DELEGATION_TRACE_AUDIT_BRIDGE_ENVELOPE_VERSION = "delegation_trace_audit_bridge_envelope.v1"
DELEGATION_TRACE_AUDIT_BRIDGE_BINDING_VERSION = "delegation_trace_audit_bridge_binding.v1"
DELEGATION_TRACE_AUDIT_BRIDGE_BINDING_SET_VERSION = "delegation_trace_audit_bridge_binding_set.v1"
DELEGATION_TRACE_AUDIT_BRIDGE_SIDE_EFFECTS_VERSION = "delegation_trace_audit_bridge_side_effects.v1"
DELEGATION_TRACE_AUDIT_BRIDGE_STATUS_REPORT_VERSION = "delegation_trace_audit_bridge_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_TRACE_AUDIT_BRIDGE_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.14; "
        "reference-only metadata layer"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.14"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.14 trace/audit bridge layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.14 "
        "trace/audit bridge layer"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.14; "
        "TraceBridgeRef is reference-only metadata, not trace write"
    ),
    "Audit Writer": (
        "Audit writer is not available in P1.8.14; "
        "AuditBridgeRef is reference-only metadata, not audit write"
    ),
    "Ledger Writer": (
        "Ledger writer is not available in P1.8.14; "
        "LedgerBridgeRef is reference-only metadata, not Ledger write"
    ),
    "Trace Event Emitter": (
        "Trace event emitter is not available in P1.8.14; "
        "TraceEventIntentRef is reference-only intent, not trace event emission"
    ),
    "Audit Event Emitter": (
        "Audit event emitter is not available in P1.8.14; "
        "AuditEventIntentRef is reference-only intent, not audit event emission"
    ),
    "Ledger Entry Writer": (
        "Ledger entry writer is not available in P1.8.14; "
        "LedgerEntryPlaceholderRef is reference-only placeholder"
    ),
    "Audit Finalizer": (
        "Audit finalizer is not available in P1.8.14; "
        "AuditBridgeRef is reference-only metadata, not audit finality"
    ),
    "Replay Engine": (
        "Replay engine is not available in P1.8.14; "
        "ReplayContextRef is reference-only context, not replay execution"
    ),
    "Fork Engine": (
        "Fork engine is not available in P1.8.14; "
        "ForkContextRef is reference-only context, not fork creation"
    ),
    "Causal Verifier": (
        "Causal verifier is not available in P1.8.14; "
        "CausalChainContextRef is reference-only context, not causal verification"
    ),
    "Evidence Verifier": (
        "Evidence verifier is not available in P1.8.14; "
        "trace/audit bridge layer does not verify evidence"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 is not implemented in P1.8.14"
    ),
    "Trace Verifier": (
        "Trace verifier is not available in P1.8.14; "
        "trace/audit bridge layer does not verify trace"
    ),
    "Ledger Finalizer": (
        "Ledger finalizer is not available in P1.8.14; "
        "trace/audit bridge layer does not finalize Ledger"
    ),
    "P1.8.15 Accountability Packet / Integration SummaryRef Model": (
        "P1.8.15 accountability packet model is not implemented in P1.8.14"
    ),
    "Runtime Execution Logger": (
        "Runtime execution logger is not available in P1.8.14; "
        "trace/audit bridge layer does not log runtime execution"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world validation)
# ---------------------------------------------------------------------------

TRACE_BRIDGE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "trace_bridge_ref_id",
    "delegation_ref_id",
    "trace_bridge_ref",
    "trace_bridge_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "trace_bridge_hash",
})

AUDIT_BRIDGE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "audit_bridge_ref_id",
    "delegation_ref_id",
    "audit_bridge_ref",
    "audit_bridge_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "audit_bridge_hash",
})

LEDGER_BRIDGE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "ledger_bridge_ref_id",
    "delegation_ref_id",
    "ledger_bridge_ref",
    "ledger_bridge_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "ledger_bridge_hash",
})

TRACE_EVENT_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "trace_event_intent_ref_id",
    "delegation_ref_id",
    "trace_event_intent_ref",
    "trace_event_intent_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "trace_event_intent_hash",
})

AUDIT_EVENT_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "audit_event_intent_ref_id",
    "delegation_ref_id",
    "audit_event_intent_ref",
    "audit_event_intent_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "audit_event_intent_hash",
})

LEDGER_ENTRY_PLACEHOLDER_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "ledger_entry_placeholder_ref_id",
    "delegation_ref_id",
    "ledger_entry_placeholder_ref",
    "ledger_entry_placeholder_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "ledger_entry_placeholder_hash",
})

REPLAY_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "replay_context_ref_id",
    "delegation_ref_id",
    "trace_context_kind",
    "replay_context_ref",
    "replay_context_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "replay_context_hash",
})

FORK_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "fork_context_ref_id",
    "delegation_ref_id",
    "trace_context_kind",
    "fork_context_ref",
    "fork_context_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "fork_context_hash",
})

CAUSAL_CHAIN_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "causal_chain_context_ref_id",
    "delegation_ref_id",
    "trace_context_kind",
    "causal_chain_context_ref",
    "causal_chain_context_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "causal_chain_context_hash",
})

READINESS_MATRIX_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "entry_id",
    "delegation_ref_id",
    "family",
    "present",
    "hash_present",
    "source_label_present",
    "finding_count",
    "unavailable_reason",
    "source_label",
    "entry_hash",
})

READINESS_MATRIX_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "trace_audit_readiness_matrix_id",
    "delegation_ref_id",
    "entries",
    "source_label",
    "matrix_hash",
})

TRACE_AUDIT_READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "trace_audit_readiness_profile_id",
    "delegation_ref_id",
    "has_trace_bridge_refs",
    "has_audit_bridge_refs",
    "has_ledger_bridge_refs",
    "has_trace_event_intent_refs",
    "has_audit_event_intent_refs",
    "has_ledger_entry_placeholders",
    "has_replay_context_refs",
    "has_fork_context_refs",
    "has_causal_chain_context_refs",
    "has_runtime_execution_readiness_context",
    "has_policy_custos_bridge_context",
    "has_operator_review_context",
    "has_shadow_resolver_context",
    "has_authority_context",
    "has_evidence_context",
    "missing_components",
    "trace_writer_unavailable_reason",
    "audit_writer_unavailable_reason",
    "ledger_writer_unavailable_reason",
    "replay_engine_unavailable_reason",
    "fork_engine_unavailable_reason",
    "causal_verifier_unavailable_reason",
    "evidence_verifier_unavailable_reason",
    "output_passport_unavailable_reason",
    "source_label",
    "readiness_hash",
})

BRIDGE_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "trace_audit_bridge_envelope_id",
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
    "trace_bridge_refs",
    "audit_bridge_refs",
    "ledger_bridge_refs",
    "trace_event_intent_refs",
    "audit_event_intent_refs",
    "ledger_entry_placeholder_refs",
    "replay_context_refs",
    "fork_context_refs",
    "causal_chain_context_refs",
    "trace_audit_readiness_matrix_hash",
    "trace_audit_readiness_hash",
    "source_label",
    "trace_audit_bridge_envelope_hash",
})

BRIDGE_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
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
    "trace_audit_bridge_envelope_hash",
    "trace_audit_readiness_matrix_hash",
    "trace_audit_readiness_hash",
    "source_label",
    "bridge_status",
    "binding_hash",
})

BRIDGE_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "trace_audit_bridge_binding_set_id",
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
    "bindings",
    "source_label",
    "trace_audit_bridge_binding_set_hash",
    "side_effects",
})

BRIDGE_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "trace_writer_called",
    "audit_writer_called",
    "ledger_writer_called",
    "trace_event_emitted",
    "audit_event_emitted",
    "ledger_entry_written",
    "audit_finalized",
    "replay_executed",
    "fork_created",
    "causal_chain_verified",
    "evidence_verified",
    "output_passport_created",
    "trace_verified",
    "ledger_finalized",
    "global_trace_written",
    "runtime_mutated",
})

BRIDGE_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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

class DelegationTraceAuditBridgeKind(str, Enum):
    """Trace/audit bridge kind classifier; does not write trace, write Ledger,
    finalize audit, verify evidence, or produce Output Passport.

    Boundary:
      - Trace/audit bridge kind classifies trace/audit/Ledger metadata.
      - It does not write trace.
      - It does not write Ledger.
      - It does not finalize audit.
      - It does not verify evidence.
      - It does not produce Output Passport.
    """

    TRACE_BRIDGE = "TRACE_BRIDGE"
    AUDIT_BRIDGE = "AUDIT_BRIDGE"
    LEDGER_BRIDGE = "LEDGER_BRIDGE"
    TRACE_EVENT_INTENT = "TRACE_EVENT_INTENT"
    AUDIT_EVENT_INTENT = "AUDIT_EVENT_INTENT"
    LEDGER_ENTRY_PLACEHOLDER = "LEDGER_ENTRY_PLACEHOLDER"
    REPLAY_CONTEXT = "REPLAY_CONTEXT"
    FORK_CONTEXT = "FORK_CONTEXT"
    CAUSAL_CHAIN_CONTEXT = "CAUSAL_CHAIN_CONTEXT"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationTraceAuditBridgeReferenceStatus(str, Enum):
    """Reference status ladder; never implies trace written, audit completed,
    Ledger entry written, trace event emitted, audit event emitted, Ledger
    entry exists, replay executed, fork created, or causal verification.

    Boundary:
      - TRACE_BRIDGE_REFERENCED is not trace written.
      - AUDIT_BRIDGE_REFERENCED is not audit completed.
      - LEDGER_BRIDGE_REFERENCED is not Ledger entry written.
      - TRACE_EVENT_INTENT_REFERENCED is not trace event emitted.
      - AUDIT_EVENT_INTENT_REFERENCED is not audit event emitted.
      - LEDGER_ENTRY_PLACEHOLDER_REFERENCED is not Ledger entry.
      - REPLAY_CONTEXT_REFERENCED is not replay executed.
      - FORK_CONTEXT_REFERENCED is not fork created.
      - CAUSAL_CHAIN_CONTEXT_REFERENCED is not causal chain verified.
      - TRACE_WRITER_UNAVAILABLE is honest unavailability, not trace failure.
      - AUDIT_WRITER_UNAVAILABLE is honest unavailability, not audit failure.
      - LEDGER_WRITER_UNAVAILABLE is honest unavailability, not Ledger failure.
      - EVIDENCE_VERIFIER_UNAVAILABLE is honest unavailability, not evidence failure.
      - OUTPUT_PASSPORT_UNAVAILABLE is honest unavailability, not P1.9 failure.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    TRACE_BRIDGE_REFERENCED = "TRACE_BRIDGE_REFERENCED"
    AUDIT_BRIDGE_REFERENCED = "AUDIT_BRIDGE_REFERENCED"
    LEDGER_BRIDGE_REFERENCED = "LEDGER_BRIDGE_REFERENCED"
    TRACE_EVENT_INTENT_REFERENCED = "TRACE_EVENT_INTENT_REFERENCED"
    AUDIT_EVENT_INTENT_REFERENCED = "AUDIT_EVENT_INTENT_REFERENCED"
    LEDGER_ENTRY_PLACEHOLDER_REFERENCED = "LEDGER_ENTRY_PLACEHOLDER_REFERENCED"
    REPLAY_CONTEXT_REFERENCED = "REPLAY_CONTEXT_REFERENCED"
    FORK_CONTEXT_REFERENCED = "FORK_CONTEXT_REFERENCED"
    CAUSAL_CHAIN_CONTEXT_REFERENCED = "CAUSAL_CHAIN_CONTEXT_REFERENCED"
    TRACE_WRITER_UNAVAILABLE = "TRACE_WRITER_UNAVAILABLE"
    AUDIT_WRITER_UNAVAILABLE = "AUDIT_WRITER_UNAVAILABLE"
    LEDGER_WRITER_UNAVAILABLE = "LEDGER_WRITER_UNAVAILABLE"
    REPLAY_ENGINE_UNAVAILABLE = "REPLAY_ENGINE_UNAVAILABLE"
    FORK_ENGINE_UNAVAILABLE = "FORK_ENGINE_UNAVAILABLE"
    CAUSAL_VERIFIER_UNAVAILABLE = "CAUSAL_VERIFIER_UNAVAILABLE"
    EVIDENCE_VERIFIER_UNAVAILABLE = "EVIDENCE_VERIFIER_UNAVAILABLE"
    OUTPUT_PASSPORT_UNAVAILABLE = "OUTPUT_PASSPORT_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationTraceAuditBridgeStatus(str, Enum):
    """Bridge declaration status; does not imply trace write, audit finality,
    Ledger write, evidence verification, replay, fork, or Output Passport.

    Boundary:
      - REFERENCE_ONLY means trace/audit bridge context is reference-only.
      - DECLARED means trace/audit bridge context was declared as metadata.
      - Neither means trace written, Ledger written, audit finalized,
        evidence verified, replayed, forked, or passported.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationTraceContextKind(str, Enum):
    """Trace context kind classifier; does not write trace, verify causal chain,
    replay, or fork.

    Boundary:
      - TraceContextKind classifies future trace input metadata.
      - It does not write trace.
      - It does not verify causal chain.
      - It does not replay or fork.
    """

    TRACE_EVENT_CONTEXT = "TRACE_EVENT_CONTEXT"
    TRACE_CHAIN_CONTEXT = "TRACE_CHAIN_CONTEXT"
    TRACE_REPLAY_CONTEXT = "TRACE_REPLAY_CONTEXT"
    TRACE_FORK_CONTEXT = "TRACE_FORK_CONTEXT"
    TRACE_CAUSAL_CONTEXT = "TRACE_CAUSAL_CONTEXT"
    TRACE_EVIDENCE_CONTEXT = "TRACE_EVIDENCE_CONTEXT"
    UNKNOWN = "UNKNOWN"


class DelegationAuditContextKind(str, Enum):
    """Audit context kind classifier; does not complete audit, verify evidence,
    or create Output Passport.

    Boundary:
      - AuditContextKind classifies future audit input metadata.
      - It does not complete audit.
      - It does not verify evidence.
      - It does not create Output Passport.
    """

    AUDIT_EVENT_CONTEXT = "AUDIT_EVENT_CONTEXT"
    AUDIT_RECORD_CONTEXT = "AUDIT_RECORD_CONTEXT"
    AUDIT_EVIDENCE_CONTEXT = "AUDIT_EVIDENCE_CONTEXT"
    AUDIT_REVIEW_CONTEXT = "AUDIT_REVIEW_CONTEXT"
    AUDIT_LEDGER_CONTEXT = "AUDIT_LEDGER_CONTEXT"
    AUDIT_OUTPUT_PASSPORT_CONTEXT = "AUDIT_OUTPUT_PASSPORT_CONTEXT"
    UNKNOWN = "UNKNOWN"


class DelegationTraceAuditReadinessFamily(str, Enum):
    """Trace/audit readiness family classifier; does not represent trace
    verification, audit readiness, or risk score.

    Boundary:
      - Trace/audit readiness family classifies possible future trace/audit
        input context.
      - It does not represent trace verification.
      - It does not indicate audit readiness.
      - It does not score risk.
    """

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
    TRACE_CONTEXT = "TRACE_CONTEXT"
    AUDIT_CONTEXT = "AUDIT_CONTEXT"
    LEDGER_CONTEXT = "LEDGER_CONTEXT"
    REPLAY_CONTEXT = "REPLAY_CONTEXT"
    FORK_CONTEXT = "FORK_CONTEXT"
    CAUSAL_CONTEXT = "CAUSAL_CONTEXT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# SideEffects (plain dataclass, all defaults False)
# ---------------------------------------------------------------------------

@dataclass
class DelegationTraceAuditBridgeSideEffects:
    """Hard proof that P1.8.14 is non-writing, non-finalizing, non-verifying,
    non-replaying, non-forking, and non-passporting. All fields default to False."""

    trace_writer_called: bool = False
    audit_writer_called: bool = False
    ledger_writer_called: bool = False
    trace_event_emitted: bool = False
    audit_event_emitted: bool = False
    ledger_entry_written: bool = False
    audit_finalized: bool = False
    replay_executed: bool = False
    fork_created: bool = False
    causal_chain_verified: bool = False
    evidence_verified: bool = False
    output_passport_created: bool = False
    trace_verified: bool = False
    ledger_finalized: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False


# ---------------------------------------------------------------------------
# Private enum parsers
# ---------------------------------------------------------------------------

def _parse_trace_audit_bridge_kind(
    value: DelegationTraceAuditBridgeKind | str,
) -> DelegationTraceAuditBridgeKind:
    if isinstance(value, DelegationTraceAuditBridgeKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationTraceAuditBridgeKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid bridge_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="bridge_kind",
            ) from exc
    raise DelegationError(
        "bridge_kind must be a string or DelegationTraceAuditBridgeKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="bridge_kind",
    )


def _parse_trace_audit_bridge_reference_status(
    value: DelegationTraceAuditBridgeReferenceStatus | str,
) -> DelegationTraceAuditBridgeReferenceStatus:
    if isinstance(value, DelegationTraceAuditBridgeReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationTraceAuditBridgeReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationTraceAuditBridgeReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )


def _parse_trace_audit_bridge_status(
    value: DelegationTraceAuditBridgeStatus | str,
) -> DelegationTraceAuditBridgeStatus:
    if isinstance(value, DelegationTraceAuditBridgeStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationTraceAuditBridgeStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid bridge_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="bridge_status",
            ) from exc
    raise DelegationError(
        "bridge_status must be a string or DelegationTraceAuditBridgeStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="bridge_status",
    )


def _parse_trace_context_kind(
    value: DelegationTraceContextKind | str,
) -> DelegationTraceContextKind:
    if isinstance(value, DelegationTraceContextKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationTraceContextKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid trace_context_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="trace_context_kind",
            ) from exc
    raise DelegationError(
        "trace_context_kind must be a string or DelegationTraceContextKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="trace_context_kind",
    )


def _parse_audit_context_kind(
    value: DelegationAuditContextKind | str,
) -> DelegationAuditContextKind:
    if isinstance(value, DelegationAuditContextKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationAuditContextKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid audit_context_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="audit_context_kind",
            ) from exc
    raise DelegationError(
        "audit_context_kind must be a string or DelegationAuditContextKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="audit_context_kind",
    )


def _parse_readiness_family(
    value: DelegationTraceAuditReadinessFamily | str,
) -> DelegationTraceAuditReadinessFamily:
    if isinstance(value, DelegationTraceAuditReadinessFamily):
        return value
    if isinstance(value, str):
        try:
            return DelegationTraceAuditReadinessFamily(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid family: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="family",
            ) from exc
    raise DelegationError(
        "family must be a string or DelegationTraceAuditReadinessFamily",
        code=DelegationErrorCode.INVALID_ENUM,
        field="family",
    )


# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DelegationTraceBridgeRef:
    """One reference-only trace bridge metadata object.

    Boundary: TraceBridgeRef describes future trace bridge metadata.
    It does not write trace. It does not emit trace events.
    It does not verify trace. It does not write Ledger.
    """

    schema_version: str
    trace_bridge_ref_id: str
    delegation_ref_id: str
    trace_bridge_ref: str | None
    trace_bridge_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    trace_bridge_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "trace_bridge_ref_id": self.trace_bridge_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "trace_bridge_description": self.trace_bridge_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "trace_bridge_hash": self.trace_bridge_hash,
        }
        if self.trace_bridge_ref is not None:
            result["trace_bridge_ref"] = self.trace_bridge_ref
        return result


@dataclass(frozen=True)
class DelegationAuditBridgeRef:
    """One reference-only audit bridge metadata object.

    Boundary: AuditBridgeRef describes future audit bridge metadata.
    It does not finalize audit. It does not create audit record.
    It does not verify evidence. It does not write Ledger.
    """

    schema_version: str
    audit_bridge_ref_id: str
    delegation_ref_id: str
    audit_bridge_ref: str | None
    audit_bridge_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    audit_bridge_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "audit_bridge_ref_id": self.audit_bridge_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "audit_bridge_description": self.audit_bridge_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "audit_bridge_hash": self.audit_bridge_hash,
        }
        if self.audit_bridge_ref is not None:
            result["audit_bridge_ref"] = self.audit_bridge_ref
        return result


@dataclass(frozen=True)
class DelegationLedgerBridgeRef:
    """One reference-only Ledger bridge metadata object.

    Boundary: LedgerBridgeRef describes future Ledger bridge metadata.
    It does not write Ledger. It does not create Ledger entry.
    It does not finalize Ledger. It does not create audit finality.
    """

    schema_version: str
    ledger_bridge_ref_id: str
    delegation_ref_id: str
    ledger_bridge_ref: str | None
    ledger_bridge_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    ledger_bridge_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "ledger_bridge_ref_id": self.ledger_bridge_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "ledger_bridge_description": self.ledger_bridge_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "ledger_bridge_hash": self.ledger_bridge_hash,
        }
        if self.ledger_bridge_ref is not None:
            result["ledger_bridge_ref"] = self.ledger_bridge_ref
        return result


@dataclass(frozen=True)
class DelegationTraceEventIntentRef:
    """One reference-only trace event intent metadata object.

    Boundary: TraceEventIntentRef describes future trace event intent metadata.
    It does not emit trace event. It does not write trace.
    It does not create TraceEvent. It does not become TRACE_VERIFIED.
    """

    schema_version: str
    trace_event_intent_ref_id: str
    delegation_ref_id: str
    trace_event_intent_ref: str | None
    trace_event_intent_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    trace_event_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "trace_event_intent_ref_id": self.trace_event_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "trace_event_intent_description": self.trace_event_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "trace_event_intent_hash": self.trace_event_intent_hash,
        }
        if self.trace_event_intent_ref is not None:
            result["trace_event_intent_ref"] = self.trace_event_intent_ref
        return result


@dataclass(frozen=True)
class DelegationAuditEventIntentRef:
    """One reference-only audit event intent metadata object.

    Boundary: AuditEventIntentRef describes future audit event intent metadata.
    It does not emit audit event. It does not create audit record.
    It does not finalize audit.
    """

    schema_version: str
    audit_event_intent_ref_id: str
    delegation_ref_id: str
    audit_event_intent_ref: str | None
    audit_event_intent_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    audit_event_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "audit_event_intent_ref_id": self.audit_event_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "audit_event_intent_description": self.audit_event_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "audit_event_intent_hash": self.audit_event_intent_hash,
        }
        if self.audit_event_intent_ref is not None:
            result["audit_event_intent_ref"] = self.audit_event_intent_ref
        return result


@dataclass(frozen=True)
class DelegationLedgerEntryPlaceholderRef:
    """One reference-only placeholder for future Ledger entry.

    Boundary: LedgerEntryPlaceholderRef describes where a future Ledger entry
    may be referenced. It is not a Ledger entry. It is not Ledger write.
    It is not Ledger finality. It is not audit proof.
    """

    schema_version: str
    ledger_entry_placeholder_ref_id: str
    delegation_ref_id: str
    ledger_entry_placeholder_ref: str | None
    ledger_entry_placeholder_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    ledger_entry_placeholder_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "ledger_entry_placeholder_ref_id": self.ledger_entry_placeholder_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "ledger_entry_placeholder_description": self.ledger_entry_placeholder_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "ledger_entry_placeholder_hash": self.ledger_entry_placeholder_hash,
        }
        if self.ledger_entry_placeholder_ref is not None:
            result["ledger_entry_placeholder_ref"] = self.ledger_entry_placeholder_ref
        return result


@dataclass(frozen=True)
class DelegationReplayContextRef:
    """One reference-only replay context metadata object.

    Boundary: ReplayContextRef describes future replay context.
    It does not execute replay. It does not validate replay.
    It does not mutate state.
    """

    schema_version: str
    replay_context_ref_id: str
    delegation_ref_id: str
    trace_context_kind: DelegationTraceContextKind
    replay_context_ref: str | None
    replay_context_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    replay_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "replay_context_ref_id": self.replay_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "trace_context_kind": self.trace_context_kind.value,
            "replay_context_description": self.replay_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "replay_context_hash": self.replay_context_hash,
        }
        if self.replay_context_ref is not None:
            result["replay_context_ref"] = self.replay_context_ref
        return result


@dataclass(frozen=True)
class DelegationForkContextRef:
    """One reference-only fork context metadata object.

    Boundary: ForkContextRef describes future fork context.
    It does not create fork. It does not replay state.
    It does not mutate runtime.
    """

    schema_version: str
    fork_context_ref_id: str
    delegation_ref_id: str
    trace_context_kind: DelegationTraceContextKind
    fork_context_ref: str | None
    fork_context_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    fork_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "fork_context_ref_id": self.fork_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "trace_context_kind": self.trace_context_kind.value,
            "fork_context_description": self.fork_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "fork_context_hash": self.fork_context_hash,
        }
        if self.fork_context_ref is not None:
            result["fork_context_ref"] = self.fork_context_ref
        return result


@dataclass(frozen=True)
class DelegationCausalChainContextRef:
    """One reference-only causal chain context metadata object.

    Boundary: CausalChainContextRef describes future causal chain context.
    It does not verify causal chain. It does not prove causality.
    It does not create TRACE_VERIFIED state.
    """

    schema_version: str
    causal_chain_context_ref_id: str
    delegation_ref_id: str
    trace_context_kind: DelegationTraceContextKind
    causal_chain_context_ref: str | None
    causal_chain_context_description: str
    reference_status: DelegationTraceAuditBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    causal_chain_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "causal_chain_context_ref_id": self.causal_chain_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "trace_context_kind": self.trace_context_kind.value,
            "causal_chain_context_description": self.causal_chain_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "causal_chain_context_hash": self.causal_chain_context_hash,
        }
        if self.causal_chain_context_ref is not None:
            result["causal_chain_context_ref"] = self.causal_chain_context_ref
        return result


@dataclass(frozen=True)
class DelegationTraceAuditReadinessMatrixEntry:
    """One reference-only trace/audit readiness row for future trace/audit
    input context.

    Boundary: TraceAuditReadinessMatrixEntry is not trace verification.
    Input context presence is not TRACE_VERIFIED.
    Finding count is not audit score.
    Presence is not audit readiness proof.
    """

    schema_version: str
    entry_id: str
    delegation_ref_id: str
    family: DelegationTraceAuditReadinessFamily
    present: bool
    hash_present: bool
    source_label_present: bool
    finding_count: int
    unavailable_reason: str
    source_label: DelegationSourceLabel
    entry_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "delegation_ref_id": self.delegation_ref_id,
            "family": self.family.value,
            "present": self.present,
            "hash_present": self.hash_present,
            "source_label_present": self.source_label_present,
            "finding_count": self.finding_count,
            "unavailable_reason": self.unavailable_reason,
            "source_label": self.source_label.value,
            "entry_hash": self.entry_hash,
        }


@dataclass(frozen=True)
class DelegationTraceAuditReadinessMatrix:
    """Lightweight reference-only matrix of future trace/audit input contexts.

    Boundary: TraceAuditReadinessMatrix is not TRACE_VERIFIED.
    TraceAuditReadinessMatrix is not audit finality.
    TraceAuditReadinessMatrix is not evidence verification.
    TraceAuditReadinessMatrix is not Output Passport.
    """

    schema_version: str
    trace_audit_readiness_matrix_id: str
    delegation_ref_id: str
    entries: tuple[DelegationTraceAuditReadinessMatrixEntry, ...]
    source_label: DelegationSourceLabel
    matrix_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trace_audit_readiness_matrix_id": self.trace_audit_readiness_matrix_id,
            "delegation_ref_id": self.delegation_ref_id,
            "entries": [e.to_canonical_dict() for e in self.entries],
            "source_label": self.source_label.value,
            "matrix_hash": self.matrix_hash,
        }


@dataclass(frozen=True)
class DelegationTraceAuditReadinessProfile:
    """Present/missing trace/audit bridge component profile, not audit
    readiness or trace verification guarantee.

    Boundary: TraceAuditReadinessProfile is not trace/audit readiness proof.
    TraceAuditReadinessProfile is not TRACE_VERIFIED.
    TraceAuditReadinessProfile is not audit finality.
    TraceAuditReadinessProfile is not evidence verification.
    TraceAuditReadinessProfile is not Output Passport readiness.
    """

    schema_version: str
    trace_audit_readiness_profile_id: str
    delegation_ref_id: str
    has_trace_bridge_refs: bool
    has_audit_bridge_refs: bool
    has_ledger_bridge_refs: bool
    has_trace_event_intent_refs: bool
    has_audit_event_intent_refs: bool
    has_ledger_entry_placeholders: bool
    has_replay_context_refs: bool
    has_fork_context_refs: bool
    has_causal_chain_context_refs: bool
    has_runtime_execution_readiness_context: bool
    has_policy_custos_bridge_context: bool
    has_operator_review_context: bool
    has_shadow_resolver_context: bool
    has_authority_context: bool
    has_evidence_context: bool
    missing_components: tuple[str, ...]
    trace_writer_unavailable_reason: str
    audit_writer_unavailable_reason: str
    ledger_writer_unavailable_reason: str
    replay_engine_unavailable_reason: str
    fork_engine_unavailable_reason: str
    causal_verifier_unavailable_reason: str
    evidence_verifier_unavailable_reason: str
    output_passport_unavailable_reason: str
    source_label: DelegationSourceLabel
    readiness_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trace_audit_readiness_profile_id": self.trace_audit_readiness_profile_id,
            "delegation_ref_id": self.delegation_ref_id,
            "has_trace_bridge_refs": self.has_trace_bridge_refs,
            "has_audit_bridge_refs": self.has_audit_bridge_refs,
            "has_ledger_bridge_refs": self.has_ledger_bridge_refs,
            "has_trace_event_intent_refs": self.has_trace_event_intent_refs,
            "has_audit_event_intent_refs": self.has_audit_event_intent_refs,
            "has_ledger_entry_placeholders": self.has_ledger_entry_placeholders,
            "has_replay_context_refs": self.has_replay_context_refs,
            "has_fork_context_refs": self.has_fork_context_refs,
            "has_causal_chain_context_refs": self.has_causal_chain_context_refs,
            "has_runtime_execution_readiness_context": self.has_runtime_execution_readiness_context,
            "has_policy_custos_bridge_context": self.has_policy_custos_bridge_context,
            "has_operator_review_context": self.has_operator_review_context,
            "has_shadow_resolver_context": self.has_shadow_resolver_context,
            "has_authority_context": self.has_authority_context,
            "has_evidence_context": self.has_evidence_context,
            "missing_components": list(self.missing_components),
            "trace_writer_unavailable_reason": self.trace_writer_unavailable_reason,
            "audit_writer_unavailable_reason": self.audit_writer_unavailable_reason,
            "ledger_writer_unavailable_reason": self.ledger_writer_unavailable_reason,
            "replay_engine_unavailable_reason": self.replay_engine_unavailable_reason,
            "fork_engine_unavailable_reason": self.fork_engine_unavailable_reason,
            "causal_verifier_unavailable_reason": self.causal_verifier_unavailable_reason,
            "evidence_verifier_unavailable_reason": self.evidence_verifier_unavailable_reason,
            "output_passport_unavailable_reason": self.output_passport_unavailable_reason,
            "source_label": self.source_label.value,
            "readiness_hash": self.readiness_hash,
        }


@dataclass(frozen=True)
class DelegationTraceAuditBridgeEnvelope:
    """Deterministic packet of trace/audit/Ledger bridge refs and context hashes.

    Boundary: TraceAuditBridgeEnvelope is a reference packet.
    It is not trace write. It is not audit finality. It is not Ledger write.
    It is not evidence verification. It is not TRACE_VERIFIED.
    It is not Output Passport.
    """

    schema_version: str
    trace_audit_bridge_envelope_id: str
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
    trace_bridge_refs: tuple[str, ...]
    audit_bridge_refs: tuple[str, ...]
    ledger_bridge_refs: tuple[str, ...]
    trace_event_intent_refs: tuple[str, ...]
    audit_event_intent_refs: tuple[str, ...]
    ledger_entry_placeholder_refs: tuple[str, ...]
    replay_context_refs: tuple[str, ...]
    fork_context_refs: tuple[str, ...]
    causal_chain_context_refs: tuple[str, ...]
    trace_audit_readiness_matrix_hash: str
    trace_audit_readiness_hash: str
    source_label: DelegationSourceLabel
    trace_audit_bridge_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trace_audit_bridge_envelope_id": self.trace_audit_bridge_envelope_id,
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
            "trace_bridge_refs": list(self.trace_bridge_refs),
            "audit_bridge_refs": list(self.audit_bridge_refs),
            "ledger_bridge_refs": list(self.ledger_bridge_refs),
            "trace_event_intent_refs": list(self.trace_event_intent_refs),
            "audit_event_intent_refs": list(self.audit_event_intent_refs),
            "ledger_entry_placeholder_refs": list(self.ledger_entry_placeholder_refs),
            "replay_context_refs": list(self.replay_context_refs),
            "fork_context_refs": list(self.fork_context_refs),
            "causal_chain_context_refs": list(self.causal_chain_context_refs),
            "trace_audit_readiness_matrix_hash": self.trace_audit_readiness_matrix_hash,
            "trace_audit_readiness_hash": self.trace_audit_readiness_hash,
            "source_label": self.source_label.value,
            "trace_audit_bridge_envelope_hash": self.trace_audit_bridge_envelope_hash,
        }


@dataclass(frozen=True)
class DelegationTraceAuditBridgeBinding:
    """Binding between trace/audit bridge envelope and delegation context.

    Boundary: TraceAuditBridgeBinding binds bridge metadata.
    It is not trace verification. It is not audit proof.
    It is not Ledger finality. It is not evidence verification.
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
    trace_audit_bridge_envelope_hash: str
    trace_audit_readiness_matrix_hash: str
    trace_audit_readiness_hash: str
    source_label: DelegationSourceLabel
    bridge_status: DelegationTraceAuditBridgeStatus
    binding_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
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
            "trace_audit_bridge_envelope_hash": self.trace_audit_bridge_envelope_hash,
            "trace_audit_readiness_matrix_hash": self.trace_audit_readiness_matrix_hash,
            "trace_audit_readiness_hash": self.trace_audit_readiness_hash,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "binding_hash": self.binding_hash,
        }


@dataclass(frozen=True)
class DelegationTraceAuditBridgeBindingSet:
    """Collection of trace/audit bridge bindings for one delegation.

    Boundary: TraceAuditBridgeBindingSet describes trace/audit bridge hooks.
    It does not write trace, write Ledger, emit events, finalize audit,
    replay, fork, verify evidence, create Output Passport, write global
    trace, or mutate runtime.
    """

    schema_version: str
    trace_audit_bridge_binding_set_id: str
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
    bindings: tuple[DelegationTraceAuditBridgeBinding, ...]
    source_label: DelegationSourceLabel
    trace_audit_bridge_binding_set_hash: str
    side_effects: DelegationTraceAuditBridgeSideEffects

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trace_audit_bridge_binding_set_id": self.trace_audit_bridge_binding_set_id,
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
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "source_label": self.source_label.value,
            "trace_audit_bridge_binding_set_hash": self.trace_audit_bridge_binding_set_hash,
            "side_effects": {
                "trace_writer_called": self.side_effects.trace_writer_called,
                "audit_writer_called": self.side_effects.audit_writer_called,
                "ledger_writer_called": self.side_effects.ledger_writer_called,
                "trace_event_emitted": self.side_effects.trace_event_emitted,
                "audit_event_emitted": self.side_effects.audit_event_emitted,
                "ledger_entry_written": self.side_effects.ledger_entry_written,
                "audit_finalized": self.side_effects.audit_finalized,
                "replay_executed": self.side_effects.replay_executed,
                "fork_created": self.side_effects.fork_created,
                "causal_chain_verified": self.side_effects.causal_chain_verified,
                "evidence_verified": self.side_effects.evidence_verified,
                "output_passport_created": self.side_effects.output_passport_created,
                "trace_verified": self.side_effects.trace_verified,
                "ledger_finalized": self.side_effects.ledger_finalized,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
        }


@dataclass(frozen=True)
class DelegationTraceAuditBridgeStatusReport:
    """Reports trace/audit bridge model capability and unavailable surfaces.

    Boundary: Reference-only metadata reporting.
    """

    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: tuple[tuple[str, str], ...]
    side_effects: DelegationTraceAuditBridgeSideEffects
    status_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status_label": self.status_label,
            "available_contracts": list(self.available_contracts),
            "unavailable_bindings": [
                {"surface": k, "reason": v} for k, v in self.unavailable_bindings
            ],
            "side_effects": {
                "trace_writer_called": self.side_effects.trace_writer_called,
                "audit_writer_called": self.side_effects.audit_writer_called,
                "ledger_writer_called": self.side_effects.ledger_writer_called,
                "trace_event_emitted": self.side_effects.trace_event_emitted,
                "audit_event_emitted": self.side_effects.audit_event_emitted,
                "ledger_entry_written": self.side_effects.ledger_entry_written,
                "audit_finalized": self.side_effects.audit_finalized,
                "replay_executed": self.side_effects.replay_executed,
                "fork_created": self.side_effects.fork_created,
                "causal_chain_verified": self.side_effects.causal_chain_verified,
                "evidence_verified": self.side_effects.evidence_verified,
                "output_passport_created": self.side_effects.output_passport_created,
                "trace_verified": self.side_effects.trace_verified,
                "ledger_finalized": self.side_effects.ledger_finalized,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
            "status_hash": self.status_hash,
        }


# ---------------------------------------------------------------------------
# Private hash computation functions
# ---------------------------------------------------------------------------

def _compute_trace_bridge_ref_hash(
    *,
    trace_bridge_ref: str | None,
    trace_bridge_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "trace_bridge_ref": trace_bridge_ref,
        "trace_bridge_description": trace_bridge_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_audit_bridge_ref_hash(
    *,
    audit_bridge_ref: str | None,
    audit_bridge_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "audit_bridge_ref": audit_bridge_ref,
        "audit_bridge_description": audit_bridge_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_ledger_bridge_ref_hash(
    *,
    ledger_bridge_ref: str | None,
    ledger_bridge_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "ledger_bridge_ref": ledger_bridge_ref,
        "ledger_bridge_description": ledger_bridge_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_trace_event_intent_ref_hash(
    *,
    trace_event_intent_ref: str | None,
    trace_event_intent_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "trace_event_intent_ref": trace_event_intent_ref,
        "trace_event_intent_description": trace_event_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_audit_event_intent_ref_hash(
    *,
    audit_event_intent_ref: str | None,
    audit_event_intent_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "audit_event_intent_ref": audit_event_intent_ref,
        "audit_event_intent_description": audit_event_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_ledger_entry_placeholder_ref_hash(
    *,
    ledger_entry_placeholder_ref: str | None,
    ledger_entry_placeholder_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "ledger_entry_placeholder_ref": ledger_entry_placeholder_ref,
        "ledger_entry_placeholder_description": ledger_entry_placeholder_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_replay_context_ref_hash(
    *,
    trace_context_kind: DelegationTraceContextKind,
    replay_context_ref: str | None,
    replay_context_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "trace_context_kind": trace_context_kind.value,
        "replay_context_ref": replay_context_ref,
        "replay_context_description": replay_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_fork_context_ref_hash(
    *,
    trace_context_kind: DelegationTraceContextKind,
    fork_context_ref: str | None,
    fork_context_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "trace_context_kind": trace_context_kind.value,
        "fork_context_ref": fork_context_ref,
        "fork_context_description": fork_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_causal_chain_context_ref_hash(
    *,
    trace_context_kind: DelegationTraceContextKind,
    causal_chain_context_ref: str | None,
    causal_chain_context_description: str,
    reference_status: DelegationTraceAuditBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
) -> str:
    return stable_hash({
        "trace_context_kind": trace_context_kind.value,
        "causal_chain_context_ref": causal_chain_context_ref,
        "causal_chain_context_description": causal_chain_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_readiness_matrix_entry_hash(
    *,
    family: DelegationTraceAuditReadinessFamily,
    present: bool,
    hash_present: bool,
    source_label_present: bool,
    finding_count: int,
    unavailable_reason: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "family": family.value,
        "present": present,
        "hash_present": hash_present,
        "source_label_present": source_label_present,
        "finding_count": finding_count,
        "unavailable_reason": unavailable_reason,
        "source_label": source_label.value,
    })


def _compute_readiness_matrix_hash(
    *,
    entry_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "entry_hashes": sorted(entry_hashes),
        "source_label": source_label.value,
    })


def _compute_trace_audit_readiness_hash(
    *,
    has_trace_bridge_refs: bool,
    has_audit_bridge_refs: bool,
    has_ledger_bridge_refs: bool,
    has_trace_event_intent_refs: bool,
    has_audit_event_intent_refs: bool,
    has_ledger_entry_placeholders: bool,
    has_replay_context_refs: bool,
    has_fork_context_refs: bool,
    has_causal_chain_context_refs: bool,
    has_runtime_execution_readiness_context: bool,
    has_policy_custos_bridge_context: bool,
    has_operator_review_context: bool,
    has_shadow_resolver_context: bool,
    has_authority_context: bool,
    has_evidence_context: bool,
    missing_components: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "has_trace_bridge_refs": has_trace_bridge_refs,
        "has_audit_bridge_refs": has_audit_bridge_refs,
        "has_ledger_bridge_refs": has_ledger_bridge_refs,
        "has_trace_event_intent_refs": has_trace_event_intent_refs,
        "has_audit_event_intent_refs": has_audit_event_intent_refs,
        "has_ledger_entry_placeholders": has_ledger_entry_placeholders,
        "has_replay_context_refs": has_replay_context_refs,
        "has_fork_context_refs": has_fork_context_refs,
        "has_causal_chain_context_refs": has_causal_chain_context_refs,
        "has_runtime_execution_readiness_context": has_runtime_execution_readiness_context,
        "has_policy_custos_bridge_context": has_policy_custos_bridge_context,
        "has_operator_review_context": has_operator_review_context,
        "has_shadow_resolver_context": has_shadow_resolver_context,
        "has_authority_context": has_authority_context,
        "has_evidence_context": has_evidence_context,
        "missing_components": sorted(missing_components),
        "source_label": source_label.value,
    })


def _compute_trace_audit_bridge_envelope_hash(
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
    trace_audit_readiness_matrix_hash: str,
    trace_audit_readiness_hash: str,
    trace_bridge_refs: tuple[str, ...],
    audit_bridge_refs: tuple[str, ...],
    ledger_bridge_refs: tuple[str, ...],
    trace_event_intent_refs: tuple[str, ...],
    audit_event_intent_refs: tuple[str, ...],
    ledger_entry_placeholder_refs: tuple[str, ...],
    replay_context_refs: tuple[str, ...],
    fork_context_refs: tuple[str, ...],
    causal_chain_context_refs: tuple[str, ...],
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
        "trace_audit_readiness_matrix_hash": trace_audit_readiness_matrix_hash,
        "trace_audit_readiness_hash": trace_audit_readiness_hash,
        "trace_bridge_refs": sorted(trace_bridge_refs),
        "audit_bridge_refs": sorted(audit_bridge_refs),
        "ledger_bridge_refs": sorted(ledger_bridge_refs),
        "trace_event_intent_refs": sorted(trace_event_intent_refs),
        "audit_event_intent_refs": sorted(audit_event_intent_refs),
        "ledger_entry_placeholder_refs": sorted(ledger_entry_placeholder_refs),
        "replay_context_refs": sorted(replay_context_refs),
        "fork_context_refs": sorted(fork_context_refs),
        "causal_chain_context_refs": sorted(causal_chain_context_refs),
        "source_label": source_label.value,
    })


def _compute_trace_audit_bridge_binding_hash(
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
    trace_audit_bridge_envelope_hash: str,
    trace_audit_readiness_matrix_hash: str,
    trace_audit_readiness_hash: str,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationTraceAuditBridgeStatus,
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
        "trace_audit_bridge_envelope_hash": trace_audit_bridge_envelope_hash,
        "trace_audit_readiness_matrix_hash": trace_audit_readiness_matrix_hash,
        "trace_audit_readiness_hash": trace_audit_readiness_hash,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_trace_audit_bridge_binding_set_hash(
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
        "binding_hashes": sorted(binding_hashes),
        "source_label": source_label.value,
    })


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------

def build_delegation_trace_bridge_ref(
    *,
    trace_bridge_ref_id: str,
    delegation_ref_id: str,
    trace_bridge_ref: str | None = None,
    trace_bridge_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationTraceBridgeRef:
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    trace_bridge_hash_val = _compute_trace_bridge_ref_hash(
        trace_bridge_ref=trace_bridge_ref,
        trace_bridge_description=trace_bridge_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationTraceBridgeRef(
        schema_version=DELEGATION_TRACE_BRIDGE_REF_VERSION,
        trace_bridge_ref_id=trace_bridge_ref_id,
        delegation_ref_id=delegation_ref_id,
        trace_bridge_ref=trace_bridge_ref,
        trace_bridge_description=trace_bridge_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        trace_bridge_hash=trace_bridge_hash_val,
    )


def build_delegation_audit_bridge_ref(
    *,
    audit_bridge_ref_id: str,
    delegation_ref_id: str,
    audit_bridge_ref: str | None = None,
    audit_bridge_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationAuditBridgeRef:
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    audit_bridge_hash_val = _compute_audit_bridge_ref_hash(
        audit_bridge_ref=audit_bridge_ref,
        audit_bridge_description=audit_bridge_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationAuditBridgeRef(
        schema_version=DELEGATION_AUDIT_BRIDGE_REF_VERSION,
        audit_bridge_ref_id=audit_bridge_ref_id,
        delegation_ref_id=delegation_ref_id,
        audit_bridge_ref=audit_bridge_ref,
        audit_bridge_description=audit_bridge_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        audit_bridge_hash=audit_bridge_hash_val,
    )


def build_delegation_ledger_bridge_ref(
    *,
    ledger_bridge_ref_id: str,
    delegation_ref_id: str,
    ledger_bridge_ref: str | None = None,
    ledger_bridge_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationLedgerBridgeRef:
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    ledger_bridge_hash_val = _compute_ledger_bridge_ref_hash(
        ledger_bridge_ref=ledger_bridge_ref,
        ledger_bridge_description=ledger_bridge_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationLedgerBridgeRef(
        schema_version=DELEGATION_LEDGER_BRIDGE_REF_VERSION,
        ledger_bridge_ref_id=ledger_bridge_ref_id,
        delegation_ref_id=delegation_ref_id,
        ledger_bridge_ref=ledger_bridge_ref,
        ledger_bridge_description=ledger_bridge_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        ledger_bridge_hash=ledger_bridge_hash_val,
    )


def build_delegation_trace_event_intent_ref(
    *,
    trace_event_intent_ref_id: str,
    delegation_ref_id: str,
    trace_event_intent_ref: str | None = None,
    trace_event_intent_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationTraceEventIntentRef:
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    trace_event_intent_hash_val = _compute_trace_event_intent_ref_hash(
        trace_event_intent_ref=trace_event_intent_ref,
        trace_event_intent_description=trace_event_intent_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationTraceEventIntentRef(
        schema_version=DELEGATION_TRACE_EVENT_INTENT_REF_VERSION,
        trace_event_intent_ref_id=trace_event_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        trace_event_intent_ref=trace_event_intent_ref,
        trace_event_intent_description=trace_event_intent_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        trace_event_intent_hash=trace_event_intent_hash_val,
    )


def build_delegation_audit_event_intent_ref(
    *,
    audit_event_intent_ref_id: str,
    delegation_ref_id: str,
    audit_event_intent_ref: str | None = None,
    audit_event_intent_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationAuditEventIntentRef:
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    audit_event_intent_hash_val = _compute_audit_event_intent_ref_hash(
        audit_event_intent_ref=audit_event_intent_ref,
        audit_event_intent_description=audit_event_intent_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationAuditEventIntentRef(
        schema_version=DELEGATION_AUDIT_EVENT_INTENT_REF_VERSION,
        audit_event_intent_ref_id=audit_event_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        audit_event_intent_ref=audit_event_intent_ref,
        audit_event_intent_description=audit_event_intent_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        audit_event_intent_hash=audit_event_intent_hash_val,
    )


def build_delegation_ledger_entry_placeholder_ref(
    *,
    ledger_entry_placeholder_ref_id: str,
    delegation_ref_id: str,
    ledger_entry_placeholder_ref: str | None = None,
    ledger_entry_placeholder_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationLedgerEntryPlaceholderRef:
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    ledger_entry_placeholder_hash_val = _compute_ledger_entry_placeholder_ref_hash(
        ledger_entry_placeholder_ref=ledger_entry_placeholder_ref,
        ledger_entry_placeholder_description=ledger_entry_placeholder_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationLedgerEntryPlaceholderRef(
        schema_version=DELEGATION_LEDGER_ENTRY_PLACEHOLDER_REF_VERSION,
        ledger_entry_placeholder_ref_id=ledger_entry_placeholder_ref_id,
        delegation_ref_id=delegation_ref_id,
        ledger_entry_placeholder_ref=ledger_entry_placeholder_ref,
        ledger_entry_placeholder_description=ledger_entry_placeholder_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        ledger_entry_placeholder_hash=ledger_entry_placeholder_hash_val,
    )


def build_delegation_replay_context_ref(
    *,
    replay_context_ref_id: str,
    delegation_ref_id: str,
    trace_context_kind: DelegationTraceContextKind | str = DelegationTraceContextKind.TRACE_REPLAY_CONTEXT,
    replay_context_ref: str | None = None,
    replay_context_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationReplayContextRef:
    trace_context_kind_val = _parse_trace_context_kind(trace_context_kind)
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    replay_context_hash_val = _compute_replay_context_ref_hash(
        trace_context_kind=trace_context_kind_val,
        replay_context_ref=replay_context_ref,
        replay_context_description=replay_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationReplayContextRef(
        schema_version=DELEGATION_REPLAY_CONTEXT_REF_VERSION,
        replay_context_ref_id=replay_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        trace_context_kind=trace_context_kind_val,
        replay_context_ref=replay_context_ref,
        replay_context_description=replay_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        replay_context_hash=replay_context_hash_val,
    )


def build_delegation_fork_context_ref(
    *,
    fork_context_ref_id: str,
    delegation_ref_id: str,
    trace_context_kind: DelegationTraceContextKind | str = DelegationTraceContextKind.TRACE_FORK_CONTEXT,
    fork_context_ref: str | None = None,
    fork_context_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationForkContextRef:
    trace_context_kind_val = _parse_trace_context_kind(trace_context_kind)
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    fork_context_hash_val = _compute_fork_context_ref_hash(
        trace_context_kind=trace_context_kind_val,
        fork_context_ref=fork_context_ref,
        fork_context_description=fork_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationForkContextRef(
        schema_version=DELEGATION_FORK_CONTEXT_REF_VERSION,
        fork_context_ref_id=fork_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        trace_context_kind=trace_context_kind_val,
        fork_context_ref=fork_context_ref,
        fork_context_description=fork_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        fork_context_hash=fork_context_hash_val,
    )


def build_delegation_causal_chain_context_ref(
    *,
    causal_chain_context_ref_id: str,
    delegation_ref_id: str,
    trace_context_kind: DelegationTraceContextKind | str = DelegationTraceContextKind.TRACE_CAUSAL_CONTEXT,
    causal_chain_context_ref: str | None = None,
    causal_chain_context_description: str = "",
    reference_status: (
        DelegationTraceAuditBridgeReferenceStatus | str
    ) = DelegationTraceAuditBridgeReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationCausalChainContextRef:
    trace_context_kind_val = _parse_trace_context_kind(trace_context_kind)
    reference_status_val = _parse_trace_audit_bridge_reference_status(reference_status)
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    causal_chain_context_hash_val = _compute_causal_chain_context_ref_hash(
        trace_context_kind=trace_context_kind_val,
        causal_chain_context_ref=causal_chain_context_ref,
        causal_chain_context_description=causal_chain_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationCausalChainContextRef(
        schema_version=DELEGATION_CAUSAL_CHAIN_CONTEXT_REF_VERSION,
        causal_chain_context_ref_id=causal_chain_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        trace_context_kind=trace_context_kind_val,
        causal_chain_context_ref=causal_chain_context_ref,
        causal_chain_context_description=causal_chain_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        causal_chain_context_hash=causal_chain_context_hash_val,
    )


def build_delegation_trace_audit_readiness_matrix_entry(
    *,
    entry_id: str,
    delegation_ref_id: str,
    family: DelegationTraceAuditReadinessFamily | str = DelegationTraceAuditReadinessFamily.UNKNOWN,
    present: bool = False,
    hash_present: bool = False,
    source_label_present: bool = False,
    finding_count: int = 0,
    unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationTraceAuditReadinessMatrixEntry:
    family_val = _parse_readiness_family(family)
    source_label_val = _parse_source_label(source_label)
    entry_hash_val = _compute_readiness_matrix_entry_hash(
        family=family_val,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=source_label_val,
    )
    return DelegationTraceAuditReadinessMatrixEntry(
        schema_version=DELEGATION_TRACE_AUDIT_READINESS_MATRIX_ENTRY_VERSION,
        entry_id=entry_id,
        delegation_ref_id=delegation_ref_id,
        family=family_val,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=source_label_val,
        entry_hash=entry_hash_val,
    )


def build_delegation_trace_audit_readiness_matrix(
    *,
    trace_audit_readiness_matrix_id: str,
    delegation_ref_id: str,
    entries: Sequence[DelegationTraceAuditReadinessMatrixEntry] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationTraceAuditReadinessMatrix:
    source_label_val = _parse_source_label(source_label)
    entries_tuple = tuple(entries)
    entry_hashes = tuple(e.entry_hash for e in entries_tuple)
    matrix_hash_val = _compute_readiness_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=source_label_val,
    )
    return DelegationTraceAuditReadinessMatrix(
        schema_version=DELEGATION_TRACE_AUDIT_READINESS_MATRIX_VERSION,
        trace_audit_readiness_matrix_id=trace_audit_readiness_matrix_id,
        delegation_ref_id=delegation_ref_id,
        entries=entries_tuple,
        source_label=source_label_val,
        matrix_hash=matrix_hash_val,
    )


def build_delegation_trace_audit_readiness_profile(
    *,
    trace_audit_readiness_profile_id: str,
    delegation_ref_id: str,
    has_trace_bridge_refs: bool = False,
    has_audit_bridge_refs: bool = False,
    has_ledger_bridge_refs: bool = False,
    has_trace_event_intent_refs: bool = False,
    has_audit_event_intent_refs: bool = False,
    has_ledger_entry_placeholders: bool = False,
    has_replay_context_refs: bool = False,
    has_fork_context_refs: bool = False,
    has_causal_chain_context_refs: bool = False,
    has_runtime_execution_readiness_context: bool = False,
    has_policy_custos_bridge_context: bool = False,
    has_operator_review_context: bool = False,
    has_shadow_resolver_context: bool = False,
    has_authority_context: bool = False,
    has_evidence_context: bool = False,
    missing_components: Sequence[str] = (),
    trace_writer_unavailable_reason: str = "",
    audit_writer_unavailable_reason: str = "",
    ledger_writer_unavailable_reason: str = "",
    replay_engine_unavailable_reason: str = "",
    fork_engine_unavailable_reason: str = "",
    causal_verifier_unavailable_reason: str = "",
    evidence_verifier_unavailable_reason: str = "",
    output_passport_unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationTraceAuditReadinessProfile:
    source_label_val = _parse_source_label(source_label)
    missing_tuple = tuple(missing_components)
    readiness_hash_val = _compute_trace_audit_readiness_hash(
        has_trace_bridge_refs=has_trace_bridge_refs,
        has_audit_bridge_refs=has_audit_bridge_refs,
        has_ledger_bridge_refs=has_ledger_bridge_refs,
        has_trace_event_intent_refs=has_trace_event_intent_refs,
        has_audit_event_intent_refs=has_audit_event_intent_refs,
        has_ledger_entry_placeholders=has_ledger_entry_placeholders,
        has_replay_context_refs=has_replay_context_refs,
        has_fork_context_refs=has_fork_context_refs,
        has_causal_chain_context_refs=has_causal_chain_context_refs,
        has_runtime_execution_readiness_context=has_runtime_execution_readiness_context,
        has_policy_custos_bridge_context=has_policy_custos_bridge_context,
        has_operator_review_context=has_operator_review_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_tuple,
        source_label=source_label_val,
    )
    return DelegationTraceAuditReadinessProfile(
        schema_version=DELEGATION_TRACE_AUDIT_READINESS_PROFILE_VERSION,
        trace_audit_readiness_profile_id=trace_audit_readiness_profile_id,
        delegation_ref_id=delegation_ref_id,
        has_trace_bridge_refs=has_trace_bridge_refs,
        has_audit_bridge_refs=has_audit_bridge_refs,
        has_ledger_bridge_refs=has_ledger_bridge_refs,
        has_trace_event_intent_refs=has_trace_event_intent_refs,
        has_audit_event_intent_refs=has_audit_event_intent_refs,
        has_ledger_entry_placeholders=has_ledger_entry_placeholders,
        has_replay_context_refs=has_replay_context_refs,
        has_fork_context_refs=has_fork_context_refs,
        has_causal_chain_context_refs=has_causal_chain_context_refs,
        has_runtime_execution_readiness_context=has_runtime_execution_readiness_context,
        has_policy_custos_bridge_context=has_policy_custos_bridge_context,
        has_operator_review_context=has_operator_review_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_tuple,
        trace_writer_unavailable_reason=trace_writer_unavailable_reason,
        audit_writer_unavailable_reason=audit_writer_unavailable_reason,
        ledger_writer_unavailable_reason=ledger_writer_unavailable_reason,
        replay_engine_unavailable_reason=replay_engine_unavailable_reason,
        fork_engine_unavailable_reason=fork_engine_unavailable_reason,
        causal_verifier_unavailable_reason=causal_verifier_unavailable_reason,
        evidence_verifier_unavailable_reason=evidence_verifier_unavailable_reason,
        output_passport_unavailable_reason=output_passport_unavailable_reason,
        source_label=source_label_val,
        readiness_hash=readiness_hash_val,
    )


def build_delegation_trace_audit_bridge_envelope(
    *,
    trace_audit_bridge_envelope_id: str,
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
    trace_bridge_refs: Sequence[str] = (),
    audit_bridge_refs: Sequence[str] = (),
    ledger_bridge_refs: Sequence[str] = (),
    trace_event_intent_refs: Sequence[str] = (),
    audit_event_intent_refs: Sequence[str] = (),
    ledger_entry_placeholder_refs: Sequence[str] = (),
    replay_context_refs: Sequence[str] = (),
    fork_context_refs: Sequence[str] = (),
    causal_chain_context_refs: Sequence[str] = (),
    trace_audit_readiness_matrix_hash: str = "",
    trace_audit_readiness_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationTraceAuditBridgeEnvelope:
    source_label_val = _parse_source_label(source_label)
    tb_ids: tuple[str, ...] = tuple(trace_bridge_refs)
    ab_ids: tuple[str, ...] = tuple(audit_bridge_refs)
    lb_ids: tuple[str, ...] = tuple(ledger_bridge_refs)
    tei_ids: tuple[str, ...] = tuple(trace_event_intent_refs)
    aei_ids: tuple[str, ...] = tuple(audit_event_intent_refs)
    lep_ids: tuple[str, ...] = tuple(ledger_entry_placeholder_refs)
    rp_ids: tuple[str, ...] = tuple(replay_context_refs)
    fk_ids: tuple[str, ...] = tuple(fork_context_refs)
    cc_ids: tuple[str, ...] = tuple(causal_chain_context_refs)
    envelope_hash_val = _compute_trace_audit_bridge_envelope_hash(
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
        trace_audit_readiness_matrix_hash=trace_audit_readiness_matrix_hash,
        trace_audit_readiness_hash=trace_audit_readiness_hash,
        trace_bridge_refs=tb_ids,
        audit_bridge_refs=ab_ids,
        ledger_bridge_refs=lb_ids,
        trace_event_intent_refs=tei_ids,
        audit_event_intent_refs=aei_ids,
        ledger_entry_placeholder_refs=lep_ids,
        replay_context_refs=rp_ids,
        fork_context_refs=fk_ids,
        causal_chain_context_refs=cc_ids,
        source_label=source_label_val,
    )
    return DelegationTraceAuditBridgeEnvelope(
        schema_version=DELEGATION_TRACE_AUDIT_BRIDGE_ENVELOPE_VERSION,
        trace_audit_bridge_envelope_id=trace_audit_bridge_envelope_id,
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
        trace_bridge_refs=tb_ids,
        audit_bridge_refs=ab_ids,
        ledger_bridge_refs=lb_ids,
        trace_event_intent_refs=tei_ids,
        audit_event_intent_refs=aei_ids,
        ledger_entry_placeholder_refs=lep_ids,
        replay_context_refs=rp_ids,
        fork_context_refs=fk_ids,
        causal_chain_context_refs=cc_ids,
        trace_audit_readiness_matrix_hash=trace_audit_readiness_matrix_hash,
        trace_audit_readiness_hash=trace_audit_readiness_hash,
        source_label=source_label_val,
        trace_audit_bridge_envelope_hash=envelope_hash_val,
    )


def build_delegation_trace_audit_bridge_binding(
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
    trace_audit_bridge_envelope_hash: str = "",
    trace_audit_readiness_matrix_hash: str = "",
    trace_audit_readiness_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: (
        DelegationTraceAuditBridgeStatus | str
    ) = DelegationTraceAuditBridgeStatus.REFERENCE_ONLY,
) -> DelegationTraceAuditBridgeBinding:
    source_label_val = _parse_source_label(source_label)
    bridge_status_val = _parse_trace_audit_bridge_status(bridge_status)
    binding_hash_val = _compute_trace_audit_bridge_binding_hash(
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
        trace_audit_bridge_envelope_hash=trace_audit_bridge_envelope_hash,
        trace_audit_readiness_matrix_hash=trace_audit_readiness_matrix_hash,
        trace_audit_readiness_hash=trace_audit_readiness_hash,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
    )
    return DelegationTraceAuditBridgeBinding(
        schema_version=DELEGATION_TRACE_AUDIT_BRIDGE_BINDING_VERSION,
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
        trace_audit_bridge_envelope_hash=trace_audit_bridge_envelope_hash,
        trace_audit_readiness_matrix_hash=trace_audit_readiness_matrix_hash,
        trace_audit_readiness_hash=trace_audit_readiness_hash,
        source_label=source_label_val,
        bridge_status=bridge_status_val,
        binding_hash=binding_hash_val,
    )


def build_delegation_trace_audit_bridge_binding_set(
    *,
    trace_audit_bridge_binding_set_id: str,
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
    bindings: Sequence[DelegationTraceAuditBridgeBinding] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    side_effects: DelegationTraceAuditBridgeSideEffects | None = None,
) -> DelegationTraceAuditBridgeBindingSet:
    source_label_val = _parse_source_label(source_label)
    bindings_tuple = tuple(bindings)
    binding_hashes = tuple(b.binding_hash for b in bindings_tuple)
    se = side_effects if side_effects is not None else DelegationTraceAuditBridgeSideEffects()
    binding_set_hash_val = _compute_trace_audit_bridge_binding_set_hash(
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
        binding_hashes=binding_hashes,
        source_label=source_label_val,
    )
    return DelegationTraceAuditBridgeBindingSet(
        schema_version=DELEGATION_TRACE_AUDIT_BRIDGE_BINDING_SET_VERSION,
        trace_audit_bridge_binding_set_id=trace_audit_bridge_binding_set_id,
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
        bindings=bindings_tuple,
        source_label=source_label_val,
        trace_audit_bridge_binding_set_hash=binding_set_hash_val,
        side_effects=se,
    )


def build_delegation_trace_audit_bridge_status_report(
    *,
    status_label: str = "P1.8.14 REFERENCE-ONLY TRACE/AUDIT BRIDGE HOOK",
    available_contracts: Sequence[str] = (),
    unavailable_bindings: dict[str, str] | None = None,
    side_effects: DelegationTraceAuditBridgeSideEffects | None = None,
) -> DelegationTraceAuditBridgeStatusReport:
    se = side_effects if side_effects is not None else DelegationTraceAuditBridgeSideEffects()
    ub = unavailable_bindings or {}
    ub_items = tuple(sorted(ub.items()))
    ac = tuple(available_contracts)
    status_hash_val = stable_hash({
        "status_label": status_label,
        "available_contracts": sorted(ac),
        "unavailable_bindings": sorted(ub_items),
    })
    return DelegationTraceAuditBridgeStatusReport(
        schema_version=DELEGATION_TRACE_AUDIT_BRIDGE_STATUS_REPORT_VERSION,
        status_label=status_label,
        available_contracts=ac,
        unavailable_bindings=ub_items,
        side_effects=se,
        status_hash=status_hash_val,
    )


# ---------------------------------------------------------------------------
# Hash re-computation functions (public, from dataclass instances)
# ---------------------------------------------------------------------------

def hash_delegation_trace_bridge_ref(
    obj: DelegationTraceBridgeRef,
) -> str:
    return _compute_trace_bridge_ref_hash(
        trace_bridge_ref=obj.trace_bridge_ref,
        trace_bridge_description=obj.trace_bridge_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_audit_bridge_ref(
    obj: DelegationAuditBridgeRef,
) -> str:
    return _compute_audit_bridge_ref_hash(
        audit_bridge_ref=obj.audit_bridge_ref,
        audit_bridge_description=obj.audit_bridge_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_ledger_bridge_ref(
    obj: DelegationLedgerBridgeRef,
) -> str:
    return _compute_ledger_bridge_ref_hash(
        ledger_bridge_ref=obj.ledger_bridge_ref,
        ledger_bridge_description=obj.ledger_bridge_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_trace_event_intent_ref(
    obj: DelegationTraceEventIntentRef,
) -> str:
    return _compute_trace_event_intent_ref_hash(
        trace_event_intent_ref=obj.trace_event_intent_ref,
        trace_event_intent_description=obj.trace_event_intent_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_audit_event_intent_ref(
    obj: DelegationAuditEventIntentRef,
) -> str:
    return _compute_audit_event_intent_ref_hash(
        audit_event_intent_ref=obj.audit_event_intent_ref,
        audit_event_intent_description=obj.audit_event_intent_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_ledger_entry_placeholder_ref(
    obj: DelegationLedgerEntryPlaceholderRef,
) -> str:
    return _compute_ledger_entry_placeholder_ref_hash(
        ledger_entry_placeholder_ref=obj.ledger_entry_placeholder_ref,
        ledger_entry_placeholder_description=obj.ledger_entry_placeholder_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_replay_context_ref(
    obj: DelegationReplayContextRef,
) -> str:
    return _compute_replay_context_ref_hash(
        trace_context_kind=obj.trace_context_kind,
        replay_context_ref=obj.replay_context_ref,
        replay_context_description=obj.replay_context_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_fork_context_ref(
    obj: DelegationForkContextRef,
) -> str:
    return _compute_fork_context_ref_hash(
        trace_context_kind=obj.trace_context_kind,
        fork_context_ref=obj.fork_context_ref,
        fork_context_description=obj.fork_context_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_causal_chain_context_ref(
    obj: DelegationCausalChainContextRef,
) -> str:
    return _compute_causal_chain_context_ref_hash(
        trace_context_kind=obj.trace_context_kind,
        causal_chain_context_ref=obj.causal_chain_context_ref,
        causal_chain_context_description=obj.causal_chain_context_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_trace_audit_readiness_matrix_entry(
    obj: DelegationTraceAuditReadinessMatrixEntry,
) -> str:
    return _compute_readiness_matrix_entry_hash(
        family=obj.family,
        present=obj.present,
        hash_present=obj.hash_present,
        source_label_present=obj.source_label_present,
        finding_count=obj.finding_count,
        unavailable_reason=obj.unavailable_reason,
        source_label=obj.source_label,
    )


def hash_delegation_trace_audit_readiness_matrix(
    obj: DelegationTraceAuditReadinessMatrix,
) -> str:
    entry_hashes = tuple(e.entry_hash for e in obj.entries)
    return _compute_readiness_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=obj.source_label,
    )


def hash_delegation_trace_audit_readiness_profile(
    obj: DelegationTraceAuditReadinessProfile,
) -> str:
    return _compute_trace_audit_readiness_hash(
        has_trace_bridge_refs=obj.has_trace_bridge_refs,
        has_audit_bridge_refs=obj.has_audit_bridge_refs,
        has_ledger_bridge_refs=obj.has_ledger_bridge_refs,
        has_trace_event_intent_refs=obj.has_trace_event_intent_refs,
        has_audit_event_intent_refs=obj.has_audit_event_intent_refs,
        has_ledger_entry_placeholders=obj.has_ledger_entry_placeholders,
        has_replay_context_refs=obj.has_replay_context_refs,
        has_fork_context_refs=obj.has_fork_context_refs,
        has_causal_chain_context_refs=obj.has_causal_chain_context_refs,
        has_runtime_execution_readiness_context=obj.has_runtime_execution_readiness_context,
        has_policy_custos_bridge_context=obj.has_policy_custos_bridge_context,
        has_operator_review_context=obj.has_operator_review_context,
        has_shadow_resolver_context=obj.has_shadow_resolver_context,
        has_authority_context=obj.has_authority_context,
        has_evidence_context=obj.has_evidence_context,
        missing_components=obj.missing_components,
        source_label=obj.source_label,
    )


def hash_delegation_trace_audit_bridge_envelope(
    obj: DelegationTraceAuditBridgeEnvelope,
) -> str:
    return _compute_trace_audit_bridge_envelope_hash(
        delegation_identity_hash=obj.delegation_identity_hash,
        role_binding_hash=obj.role_binding_hash,
        constraint_set_hash=obj.constraint_set_hash,
        authority_binding_set_hash=obj.authority_binding_set_hash,
        non_repudiation_binding_set_hash=obj.non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=obj.identity_mesh_binding_set_hash,
        scope_binding_set_hash=obj.scope_binding_set_hash,
        lifecycle_binding_set_hash=obj.lifecycle_binding_set_hash,
        chain_binding_set_hash=obj.chain_binding_set_hash,
        shadow_resolver_result_hash=obj.shadow_resolver_result_hash,
        operator_review_binding_set_hash=obj.operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=obj.policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=obj.runtime_execution_readiness_binding_set_hash,
        trace_audit_readiness_matrix_hash=obj.trace_audit_readiness_matrix_hash,
        trace_audit_readiness_hash=obj.trace_audit_readiness_hash,
        trace_bridge_refs=obj.trace_bridge_refs,
        audit_bridge_refs=obj.audit_bridge_refs,
        ledger_bridge_refs=obj.ledger_bridge_refs,
        trace_event_intent_refs=obj.trace_event_intent_refs,
        audit_event_intent_refs=obj.audit_event_intent_refs,
        ledger_entry_placeholder_refs=obj.ledger_entry_placeholder_refs,
        replay_context_refs=obj.replay_context_refs,
        fork_context_refs=obj.fork_context_refs,
        causal_chain_context_refs=obj.causal_chain_context_refs,
        source_label=obj.source_label,
    )


def hash_delegation_trace_audit_bridge_binding(
    obj: DelegationTraceAuditBridgeBinding,
) -> str:
    return _compute_trace_audit_bridge_binding_hash(
        delegation_identity_hash=obj.delegation_identity_hash,
        role_binding_hash=obj.role_binding_hash,
        constraint_set_hash=obj.constraint_set_hash,
        authority_binding_set_hash=obj.authority_binding_set_hash,
        non_repudiation_binding_set_hash=obj.non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=obj.identity_mesh_binding_set_hash,
        scope_binding_set_hash=obj.scope_binding_set_hash,
        lifecycle_binding_set_hash=obj.lifecycle_binding_set_hash,
        chain_binding_set_hash=obj.chain_binding_set_hash,
        shadow_resolver_result_hash=obj.shadow_resolver_result_hash,
        operator_review_binding_set_hash=obj.operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=obj.policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=obj.runtime_execution_readiness_binding_set_hash,
        trace_audit_bridge_envelope_hash=obj.trace_audit_bridge_envelope_hash,
        trace_audit_readiness_matrix_hash=obj.trace_audit_readiness_matrix_hash,
        trace_audit_readiness_hash=obj.trace_audit_readiness_hash,
        source_label=obj.source_label,
        bridge_status=obj.bridge_status,
    )


def hash_delegation_trace_audit_bridge_binding_set(
    obj: DelegationTraceAuditBridgeBindingSet,
) -> str:
    binding_hashes = tuple(b.binding_hash for b in obj.bindings)
    return _compute_trace_audit_bridge_binding_set_hash(
        delegation_identity_hash=obj.delegation_identity_hash,
        role_binding_hash=obj.role_binding_hash,
        constraint_set_hash=obj.constraint_set_hash,
        authority_binding_set_hash=obj.authority_binding_set_hash,
        non_repudiation_binding_set_hash=obj.non_repudiation_binding_set_hash,
        identity_mesh_binding_set_hash=obj.identity_mesh_binding_set_hash,
        scope_binding_set_hash=obj.scope_binding_set_hash,
        lifecycle_binding_set_hash=obj.lifecycle_binding_set_hash,
        chain_binding_set_hash=obj.chain_binding_set_hash,
        shadow_resolver_result_hash=obj.shadow_resolver_result_hash,
        operator_review_binding_set_hash=obj.operator_review_binding_set_hash,
        policy_custos_bridge_binding_set_hash=obj.policy_custos_bridge_binding_set_hash,
        runtime_execution_readiness_binding_set_hash=obj.runtime_execution_readiness_binding_set_hash,
        binding_hashes=binding_hashes,
        source_label=obj.source_label,
    )


def hash_delegation_trace_audit_bridge_status_report(
    obj: DelegationTraceAuditBridgeStatusReport,
) -> str:
    return stable_hash({
        "status_label": obj.status_label,
        "available_contracts": sorted(obj.available_contracts),
        "unavailable_bindings": sorted(obj.unavailable_bindings),
    })


# ---------------------------------------------------------------------------
# Serialization functions
# ---------------------------------------------------------------------------

def serialize_delegation_trace_audit_bridge_envelope(
    obj: DelegationTraceAuditBridgeEnvelope,
) -> str:
    return to_canonical_json(obj.to_canonical_dict())


def serialize_delegation_trace_audit_bridge_binding_set(
    obj: DelegationTraceAuditBridgeBindingSet,
) -> str:
    return to_canonical_json(obj.to_canonical_dict())
