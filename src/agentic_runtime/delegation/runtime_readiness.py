"""Delegation runtime/execution readiness reference model (P1.8.13).

Deterministic, versioned, JSON-safe, side-effect-free reference-only
runtime/execution readiness metadata layer over P1.8.0-P1.8.12 delegation context.

Produces runtime readiness refs, execution precondition refs, execution
blocker refs, runtime admission intent refs, runtime admission placeholder
refs, runtime context refs, tool execution context refs, runtime session
placeholder refs, execution target refs, readiness matrix, readiness
profile, readiness envelope, readiness binding, and readiness binding set
without runtime engine call, execution engine call, admission gate call,
runtime admission, runtime block enforcement, execution allow/block,
tool dispatch, runtime session creation, execution target selection,
policy/Custos call, enforcement, trace write, Ledger write, or runtime mutation.

Architectural law:
  - RuntimeReadinessRef exists does not mean runtime ready.
  - ExecutionPreconditionRef exists does not mean precondition satisfied.
  - ExecutionBlockerRef exists does not mean runtime blocked.
  - RuntimeAdmissionIntentRef exists does not mean runtime admitted.
  - RuntimeAdmissionPlaceholderRef exists does not mean admission result.
  - RuntimeContextRef exists does not mean runtime initialized.
  - ToolExecutionContextRef exists does not mean tool dispatched.
  - RuntimeSessionPlaceholderRef exists does not mean runtime session created.
  - ExecutionTargetRef exists does not mean dispatch target selected.
  - ReadinessMatrix exists does not mean execution readiness.
  - RuntimeExecutionReadinessProfile exists does not mean execution readiness proof.
  - Runtime readiness hash exists does not mean TRACE_VERIFIED.
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

DELEGATION_RUNTIME_EXECUTION_READINESS_TASK_ID = "P1.8.13"
DELEGATION_RUNTIME_READINESS_REF_VERSION = "delegation_runtime_readiness_ref.v1"
DELEGATION_EXECUTION_PRECONDITION_REF_VERSION = "delegation_execution_precondition_ref.v1"
DELEGATION_EXECUTION_BLOCKER_REF_VERSION = "delegation_execution_blocker_ref.v1"
DELEGATION_RUNTIME_ADMISSION_INTENT_REF_VERSION = "delegation_runtime_admission_intent_ref.v1"
DELEGATION_RUNTIME_ADMISSION_PLACEHOLDER_REF_VERSION = "delegation_runtime_admission_placeholder_ref.v1"
DELEGATION_RUNTIME_CONTEXT_REF_VERSION = "delegation_runtime_context_ref.v1"
DELEGATION_TOOL_EXECUTION_CONTEXT_REF_VERSION = "delegation_tool_execution_context_ref.v1"
DELEGATION_RUNTIME_SESSION_PLACEHOLDER_REF_VERSION = "delegation_runtime_session_placeholder_ref.v1"
DELEGATION_EXECUTION_TARGET_REF_VERSION = "delegation_execution_target_ref.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_MATRIX_ENTRY_VERSION = "delegation_runtime_execution_readiness_matrix_entry.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_MATRIX_VERSION = "delegation_runtime_execution_readiness_matrix.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_PROFILE_VERSION = "delegation_runtime_execution_readiness_profile.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_ENVELOPE_VERSION = "delegation_runtime_execution_readiness_envelope.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_BINDING_VERSION = "delegation_runtime_execution_readiness_binding.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_BINDING_SET_VERSION = "delegation_runtime_execution_readiness_binding_set.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_SIDE_EFFECTS_VERSION = "delegation_runtime_execution_readiness_side_effects.v1"
DELEGATION_RUNTIME_EXECUTION_READINESS_STATUS_REPORT_VERSION = "delegation_runtime_execution_readiness_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_RUNTIME_EXECUTION_READINESS_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.13; "
        "reference-only metadata layer"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.13"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.13 runtime/execution readiness layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.13 "
        "runtime/execution readiness layer"
    ),
    "Runtime Engine": (
        "Runtime engine is not available in P1.8.13; "
        "RuntimeReadinessRef is reference-only metadata, not runtime execution"
    ),
    "Execution Engine": (
        "Execution engine is not available in P1.8.13; "
        "ExecutionPreconditionRef is reference-only metadata, not execution"
    ),
    "Admission Gate": (
        "Admission gate is not available in P1.8.13; "
        "RuntimeAdmissionIntentRef is reference-only intent, not runtime admission"
    ),
    "Tool Dispatcher": (
        "Tool dispatcher is not available in P1.8.13; "
        "ToolExecutionContextRef is reference-only context, not tool dispatch"
    ),
    "Runtime Session Runtime": (
        "Runtime session runtime is not available in P1.8.13; "
        "RuntimeSessionPlaceholderRef is reference-only placeholder"
    ),
    "Execution Target Selector": (
        "Execution target selector is not available in P1.8.13; "
        "ExecutionTargetRef is reference-only metadata, not target selection"
    ),
    "Runtime Allow/Block": (
        "Runtime allow/block is not available in P1.8.13; "
        "runtime/execution readiness layer does not allow or block runtime"
    ),
    "Enforcement Engine": (
        "Enforcement engine is not available in P1.8.13; "
        "runtime/execution readiness layer does not enforce"
    ),
    "Policy/Custos Evaluator": (
        "Policy/Custos evaluator is not available in P1.8.13; "
        "runtime/execution readiness layer does not call policy/Custos"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.13; "
        "runtime/execution readiness layer does not write trace events"
    ),
    "P1.8.14 Trace/Audit BridgeRef Model": (
        "P1.8.14 trace/audit bridge model is not implemented in P1.8.13"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 is not implemented in P1.8.13"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.13; "
        "runtime/execution readiness layer is reference-only metadata"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world validation)
# ---------------------------------------------------------------------------

RUNTIME_READINESS_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_readiness_ref_id",
    "delegation_ref_id",
    "runtime_readiness_ref",
    "runtime_readiness_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "runtime_readiness_hash",
})

EXECUTION_PRECONDITION_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "execution_precondition_ref_id",
    "delegation_ref_id",
    "execution_precondition_ref",
    "precondition_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "precondition_hash",
})

EXECUTION_BLOCKER_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "execution_blocker_ref_id",
    "delegation_ref_id",
    "execution_blocker_ref",
    "blocker_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "blocker_hash",
})

RUNTIME_ADMISSION_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_admission_intent_ref_id",
    "delegation_ref_id",
    "runtime_admission_intent_ref",
    "admission_intent_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "admission_intent_hash",
})

RUNTIME_ADMISSION_PLACEHOLDER_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_admission_placeholder_ref_id",
    "delegation_ref_id",
    "runtime_admission_placeholder_ref",
    "admission_placeholder_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "admission_placeholder_hash",
})

RUNTIME_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_context_ref_id",
    "delegation_ref_id",
    "runtime_context_kind",
    "runtime_context_ref",
    "runtime_context_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "runtime_context_hash",
})

TOOL_EXECUTION_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "tool_execution_context_ref_id",
    "delegation_ref_id",
    "execution_context_kind",
    "tool_execution_context_ref",
    "tool_execution_context_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "tool_context_hash",
})

RUNTIME_SESSION_PLACEHOLDER_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_session_placeholder_ref_id",
    "delegation_ref_id",
    "runtime_session_placeholder_ref",
    "session_placeholder_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "session_placeholder_hash",
})

EXECUTION_TARGET_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "execution_target_ref_id",
    "delegation_ref_id",
    "execution_target_ref",
    "execution_target_description",
    "reference_status",
    "source_label",
    "readiness_status",
    "execution_target_hash",
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
    "readiness_matrix_id",
    "delegation_ref_id",
    "entries",
    "source_label",
    "matrix_hash",
})

READINESS_READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_execution_readiness_profile_id",
    "delegation_ref_id",
    "has_runtime_readiness_refs",
    "has_execution_precondition_refs",
    "has_execution_blocker_refs",
    "has_runtime_admission_intent_refs",
    "has_runtime_admission_placeholders",
    "has_runtime_context_refs",
    "has_tool_execution_context_refs",
    "has_runtime_session_placeholders",
    "has_execution_target_refs",
    "has_policy_custos_bridge_context",
    "has_operator_review_context",
    "has_shadow_resolver_context",
    "has_authority_context",
    "has_scope_context",
    "has_evidence_context",
    "missing_components",
    "runtime_engine_unavailable_reason",
    "execution_engine_unavailable_reason",
    "tool_dispatch_unavailable_reason",
    "session_runtime_unavailable_reason",
    "admission_gate_unavailable_reason",
    "enforcement_unavailable_reason",
    "trace_unavailable_reason",
    "ledger_unavailable_reason",
    "source_label",
    "readiness_hash",
})

READINESS_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_execution_readiness_envelope_id",
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
    "runtime_readiness_ref_ids",
    "execution_precondition_ref_ids",
    "execution_blocker_ref_ids",
    "runtime_admission_intent_ref_ids",
    "runtime_admission_placeholder_ref_ids",
    "runtime_context_ref_ids",
    "tool_execution_context_ref_ids",
    "runtime_session_placeholder_ref_ids",
    "execution_target_ref_ids",
    "readiness_matrix_hash",
    "runtime_execution_readiness_hash",
    "source_label",
    "runtime_execution_readiness_envelope_hash",
})

READINESS_BINDING_KNOWN_FIELDS: frozenset[str] = frozenset({
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
    "runtime_execution_readiness_envelope_hash",
    "readiness_matrix_hash",
    "readiness_hash",
    "source_label",
    "readiness_status",
    "binding_hash",
})

READINESS_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "runtime_execution_readiness_binding_set_id",
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
    "bindings",
    "source_label",
    "runtime_execution_readiness_binding_set_hash",
    "side_effects",
})

READINESS_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "runtime_engine_called",
    "execution_engine_called",
    "admission_gate_called",
    "runtime_admitted",
    "runtime_blocked",
    "execution_allowed",
    "execution_blocked",
    "tool_dispatched",
    "runtime_session_created",
    "execution_target_selected",
    "enforcement_performed",
    "policy_called",
    "custos_called",
    "ledger_written",
    "global_trace_written",
    "runtime_mutated",
})

READINESS_STATUS_REPORT_KNOWN_FIELDS: frozenset[str] = frozenset({
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

class DelegationRuntimeExecutionReadinessKind(str, Enum):
    """Readiness kind classifier; does not admit runtime or execute.

    Boundary:
      - Readiness kind classifies runtime/execution readiness metadata.
      - It does not admit runtime.
      - It does not execute.
      - It does not dispatch tools.
      - It does not enforce.
      - It does not mutate runtime.
    """

    RUNTIME_READINESS = "RUNTIME_READINESS"
    EXECUTION_PRECONDITION = "EXECUTION_PRECONDITION"
    EXECUTION_BLOCKER = "EXECUTION_BLOCKER"
    RUNTIME_ADMISSION_INTENT = "RUNTIME_ADMISSION_INTENT"
    RUNTIME_ADMISSION_PLACEHOLDER = "RUNTIME_ADMISSION_PLACEHOLDER"
    RUNTIME_CONTEXT = "RUNTIME_CONTEXT"
    TOOL_EXECUTION_CONTEXT = "TOOL_EXECUTION_CONTEXT"
    RUNTIME_SESSION_PLACEHOLDER = "RUNTIME_SESSION_PLACEHOLDER"
    EXECUTION_TARGET = "EXECUTION_TARGET"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"

class DelegationRuntimeExecutionReadinessReferenceStatus(str, Enum):
    """Reference status ladder; never implies runtime ready, execution,
    admission, dispatch, or enforcement.

    Boundary:
      - RUNTIME_READINESS_REFERENCED is not runtime ready.
      - EXECUTION_PRECONDITION_REFERENCED is not precondition satisfied.
      - EXECUTION_BLOCKER_REFERENCED is not runtime block enforcement.
      - RUNTIME_ADMISSION_INTENT_REFERENCED is not runtime admitted.
      - RUNTIME_ADMISSION_PLACEHOLDER_REFERENCED is not admission result.
      - RUNTIME_CONTEXT_REFERENCED is not runtime initialized.
      - TOOL_EXECUTION_CONTEXT_REFERENCED is not tool dispatch.
      - RUNTIME_SESSION_PLACEHOLDER_REFERENCED is not session creation.
      - EXECUTION_TARGET_REFERENCED is not dispatch target selected.
      - RUNTIME_ENGINE_UNAVAILABLE is honest unavailability, not runtime failure.
      - EXECUTION_ENGINE_UNAVAILABLE is honest unavailability, not execution failure.
      - TOOL_DISPATCH_UNAVAILABLE is honest unavailability, not dispatch failure.
      - SESSION_RUNTIME_UNAVAILABLE is honest unavailability, not session failure.
      - ADMISSION_GATE_UNAVAILABLE is honest unavailability, not admission denial.
      - ENFORCEMENT_UNAVAILABLE is honest unavailability, not enforcement failure.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    RUNTIME_READINESS_REFERENCED = "RUNTIME_READINESS_REFERENCED"
    EXECUTION_PRECONDITION_REFERENCED = "EXECUTION_PRECONDITION_REFERENCED"
    EXECUTION_BLOCKER_REFERENCED = "EXECUTION_BLOCKER_REFERENCED"
    RUNTIME_ADMISSION_INTENT_REFERENCED = "RUNTIME_ADMISSION_INTENT_REFERENCED"
    RUNTIME_ADMISSION_PLACEHOLDER_REFERENCED = "RUNTIME_ADMISSION_PLACEHOLDER_REFERENCED"
    RUNTIME_CONTEXT_REFERENCED = "RUNTIME_CONTEXT_REFERENCED"
    TOOL_EXECUTION_CONTEXT_REFERENCED = "TOOL_EXECUTION_CONTEXT_REFERENCED"
    RUNTIME_SESSION_PLACEHOLDER_REFERENCED = "RUNTIME_SESSION_PLACEHOLDER_REFERENCED"
    EXECUTION_TARGET_REFERENCED = "EXECUTION_TARGET_REFERENCED"
    RUNTIME_ENGINE_UNAVAILABLE = "RUNTIME_ENGINE_UNAVAILABLE"
    EXECUTION_ENGINE_UNAVAILABLE = "EXECUTION_ENGINE_UNAVAILABLE"
    TOOL_DISPATCH_UNAVAILABLE = "TOOL_DISPATCH_UNAVAILABLE"
    SESSION_RUNTIME_UNAVAILABLE = "SESSION_RUNTIME_UNAVAILABLE"
    ADMISSION_GATE_UNAVAILABLE = "ADMISSION_GATE_UNAVAILABLE"
    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class DelegationRuntimeExecutionReadinessStatus(str, Enum):
    """Readiness declaration status; does not imply execution, admission,
    or enforcement.

    Boundary:
      - REFERENCE_ONLY means runtime/execution readiness context is reference-only.
      - DECLARED means readiness context was declared as metadata.
      - Neither means runtime ready, admitted, allowed, blocked, executed,
        dispatched, or enforced.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class DelegationRuntimeContextKind(str, Enum):
    """Runtime context kind classifier; does not initialize runtime.

    Boundary:
      - RuntimeContextKind classifies future runtime input metadata.
      - It does not initialize runtime.
      - It does not create sessions.
      - It does not call workers.
      - It does not dispatch tools.
    """

    AUREL_FLOW_RUNTIME_CONTEXT = "AUREL_FLOW_RUNTIME_CONTEXT"
    AUREL_EXEC_CONTEXT = "AUREL_EXEC_CONTEXT"
    SCHEDULER_CONTEXT = "SCHEDULER_CONTEXT"
    SESSION_CONTEXT = "SESSION_CONTEXT"
    WORKER_CONTEXT = "WORKER_CONTEXT"
    SANDBOX_CONTEXT = "SANDBOX_CONTEXT"
    TOOL_GATEWAY_CONTEXT = "TOOL_GATEWAY_CONTEXT"
    UNKNOWN = "UNKNOWN"

class DelegationExecutionContextKind(str, Enum):
    """Execution context kind classifier; does not execute tools.

    Boundary:
      - ExecutionContextKind classifies future execution input metadata.
      - It does not execute tools.
      - It does not dispatch models.
      - It does not run code.
      - It does not select targets.
    """

    TOOL_CONTEXT = "TOOL_CONTEXT"
    MODEL_CONTEXT = "MODEL_CONTEXT"
    CODE_EXECUTION_CONTEXT = "CODE_EXECUTION_CONTEXT"
    WORKFLOW_CONTEXT = "WORKFLOW_CONTEXT"
    TASK_CONTEXT = "TASK_CONTEXT"
    SESSION_CONTEXT = "SESSION_CONTEXT"
    TARGET_CONTEXT = "TARGET_CONTEXT"
    UNKNOWN = "UNKNOWN"

class DelegationRuntimeExecutionReadinessFamily(str, Enum):
    """Readiness family classifier; does not represent execution readiness.

    Boundary:
      - Readiness family classifies possible future runtime/execution input context.
      - It does not represent execution readiness.
      - It does not indicate executable.
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
    RUNTIME_CONTEXT = "RUNTIME_CONTEXT"
    TOOL_CONTEXT = "TOOL_CONTEXT"
    SESSION_CONTEXT = "SESSION_CONTEXT"
    TARGET_CONTEXT = "TARGET_CONTEXT"
    UNKNOWN = "UNKNOWN"

# ---------------------------------------------------------------------------
# SideEffects (plain dataclass, all defaults False)
# ---------------------------------------------------------------------------

@dataclass
class DelegationRuntimeExecutionReadinessSideEffects:
    """Hard proof that P1.8.13 is non-admitting, non-executing,
    non-dispatching, non-enforcing, and non-mutating.  All fields
    default to False."""

    runtime_engine_called: bool = False
    execution_engine_called: bool = False
    admission_gate_called: bool = False
    runtime_admitted: bool = False
    runtime_blocked: bool = False
    execution_allowed: bool = False
    execution_blocked: bool = False
    tool_dispatched: bool = False
    runtime_session_created: bool = False
    execution_target_selected: bool = False
    enforcement_performed: bool = False
    policy_called: bool = False
    custos_called: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False

# ---------------------------------------------------------------------------
# Private enum parsers
# ---------------------------------------------------------------------------

def _parse_runtime_execution_readiness_kind(
    value: DelegationRuntimeExecutionReadinessKind | str,
) -> DelegationRuntimeExecutionReadinessKind:
    if isinstance(value, DelegationRuntimeExecutionReadinessKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationRuntimeExecutionReadinessKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid readiness_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="readiness_kind",
            ) from exc
    raise DelegationError(
        "readiness_kind must be a string or DelegationRuntimeExecutionReadinessKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="readiness_kind",
    )

def _parse_runtime_execution_readiness_reference_status(
    value: DelegationRuntimeExecutionReadinessReferenceStatus | str,
) -> DelegationRuntimeExecutionReadinessReferenceStatus:
    if isinstance(value, DelegationRuntimeExecutionReadinessReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationRuntimeExecutionReadinessReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationRuntimeExecutionReadinessReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )

def _parse_runtime_execution_readiness_status(
    value: DelegationRuntimeExecutionReadinessStatus | str,
) -> DelegationRuntimeExecutionReadinessStatus:
    if isinstance(value, DelegationRuntimeExecutionReadinessStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationRuntimeExecutionReadinessStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid readiness_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="readiness_status",
            ) from exc
    raise DelegationError(
        "readiness_status must be a string or DelegationRuntimeExecutionReadinessStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="readiness_status",
    )

def _parse_runtime_context_kind(
    value: DelegationRuntimeContextKind | str,
) -> DelegationRuntimeContextKind:
    if isinstance(value, DelegationRuntimeContextKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationRuntimeContextKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid runtime_context_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="runtime_context_kind",
            ) from exc
    raise DelegationError(
        "runtime_context_kind must be a string or DelegationRuntimeContextKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="runtime_context_kind",
    )

def _parse_execution_context_kind(
    value: DelegationExecutionContextKind | str,
) -> DelegationExecutionContextKind:
    if isinstance(value, DelegationExecutionContextKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationExecutionContextKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid execution_context_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="execution_context_kind",
            ) from exc
    raise DelegationError(
        "execution_context_kind must be a string or DelegationExecutionContextKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="execution_context_kind",
    )

def _parse_readiness_family(
    value: DelegationRuntimeExecutionReadinessFamily | str,
) -> DelegationRuntimeExecutionReadinessFamily:
    if isinstance(value, DelegationRuntimeExecutionReadinessFamily):
        return value
    if isinstance(value, str):
        try:
            return DelegationRuntimeExecutionReadinessFamily(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid family: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="family",
            ) from exc
    raise DelegationError(
        "family must be a string or DelegationRuntimeExecutionReadinessFamily",
        code=DelegationErrorCode.INVALID_ENUM,
        field="family",
    )

# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DelegationRuntimeReadinessRef:
    """One reference-only runtime readiness metadata object.

    Boundary: RuntimeReadinessRef describes future runtime readiness metadata.
    It does not make runtime ready. It does not admit runtime.
    It does not execute. It does not enforce.
    """

    schema_version: str
    runtime_readiness_ref_id: str
    delegation_ref_id: str
    runtime_readiness_ref: str | None
    runtime_readiness_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    runtime_readiness_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "runtime_readiness_ref_id": self.runtime_readiness_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "runtime_readiness_description": self.runtime_readiness_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "runtime_readiness_hash": self.runtime_readiness_hash,
        }
        if self.runtime_readiness_ref is not None:
            result["runtime_readiness_ref"] = self.runtime_readiness_ref
        return result

@dataclass(frozen=True)
class DelegationExecutionPreconditionRef:
    """One reference-only execution precondition metadata object.

    Boundary: ExecutionPreconditionRef describes precondition metadata.
    It does not satisfy preconditions. It does not approve execution.
    It does not allow runtime.
    """

    schema_version: str
    execution_precondition_ref_id: str
    delegation_ref_id: str
    execution_precondition_ref: str | None
    precondition_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    precondition_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "execution_precondition_ref_id": self.execution_precondition_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "precondition_description": self.precondition_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "precondition_hash": self.precondition_hash,
        }
        if self.execution_precondition_ref is not None:
            result["execution_precondition_ref"] = self.execution_precondition_ref
        return result

@dataclass(frozen=True)
class DelegationExecutionBlockerRef:
    """One reference-only execution blocker metadata object.

    Boundary: ExecutionBlockerRef describes blocker metadata.
    It does not block runtime. It does not deny execution.
    It does not enforce. It does not mutate runtime.
    """

    schema_version: str
    execution_blocker_ref_id: str
    delegation_ref_id: str
    execution_blocker_ref: str | None
    blocker_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    blocker_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "execution_blocker_ref_id": self.execution_blocker_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "blocker_description": self.blocker_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "blocker_hash": self.blocker_hash,
        }
        if self.execution_blocker_ref is not None:
            result["execution_blocker_ref"] = self.execution_blocker_ref
        return result

@dataclass(frozen=True)
class DelegationRuntimeAdmissionIntentRef:
    """One reference-only runtime admission intent metadata object.

    Boundary: RuntimeAdmissionIntentRef describes admission intent metadata.
    It does not admit runtime. It does not call admission gate.
    It does not allow execution.
    """

    schema_version: str
    runtime_admission_intent_ref_id: str
    delegation_ref_id: str
    runtime_admission_intent_ref: str | None
    admission_intent_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    admission_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "runtime_admission_intent_ref_id": self.runtime_admission_intent_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "admission_intent_description": self.admission_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "admission_intent_hash": self.admission_intent_hash,
        }
        if self.runtime_admission_intent_ref is not None:
            result["runtime_admission_intent_ref"] = self.runtime_admission_intent_ref
        return result

@dataclass(frozen=True)
class DelegationRuntimeAdmissionPlaceholderRef:
    """One reference-only placeholder for future runtime admission result.

    Boundary: RuntimeAdmissionPlaceholderRef describes where a future admission
    result may be referenced. It is not admission result. It is not allow/block.
    It is not execution permission.
    """

    schema_version: str
    runtime_admission_placeholder_ref_id: str
    delegation_ref_id: str
    runtime_admission_placeholder_ref: str | None
    admission_placeholder_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    admission_placeholder_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "runtime_admission_placeholder_ref_id": self.runtime_admission_placeholder_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "admission_placeholder_description": self.admission_placeholder_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "admission_placeholder_hash": self.admission_placeholder_hash,
        }
        if self.runtime_admission_placeholder_ref is not None:
            result["runtime_admission_placeholder_ref"] = self.runtime_admission_placeholder_ref
        return result

@dataclass(frozen=True)
class DelegationRuntimeContextRef:
    """One reference-only runtime context metadata object.

    Boundary: RuntimeContextRef describes future runtime context.
    It does not initialize runtime. It does not create sessions.
    It does not call workers. It does not execute.
    """

    schema_version: str
    runtime_context_ref_id: str
    delegation_ref_id: str
    runtime_context_kind: DelegationRuntimeContextKind
    runtime_context_ref: str | None
    runtime_context_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    runtime_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "runtime_context_ref_id": self.runtime_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "runtime_context_kind": self.runtime_context_kind.value,
            "runtime_context_description": self.runtime_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "runtime_context_hash": self.runtime_context_hash,
        }
        if self.runtime_context_ref is not None:
            result["runtime_context_ref"] = self.runtime_context_ref
        return result

@dataclass(frozen=True)
class DelegationToolExecutionContextRef:
    """One reference-only tool execution context metadata object.

    Boundary: ToolExecutionContextRef describes future tool execution context.
    It does not dispatch a tool. It does not prove a tool is executable.
    It does not call a tool gateway.
    """

    schema_version: str
    tool_execution_context_ref_id: str
    delegation_ref_id: str
    execution_context_kind: DelegationExecutionContextKind
    tool_execution_context_ref: str | None
    tool_execution_context_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    tool_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "tool_execution_context_ref_id": self.tool_execution_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "execution_context_kind": self.execution_context_kind.value,
            "tool_execution_context_description": self.tool_execution_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "tool_context_hash": self.tool_context_hash,
        }
        if self.tool_execution_context_ref is not None:
            result["tool_execution_context_ref"] = self.tool_execution_context_ref
        return result

@dataclass(frozen=True)
class DelegationRuntimeSessionPlaceholderRef:
    """One reference-only runtime session placeholder metadata object.

    Boundary: RuntimeSessionPlaceholderRef describes where a future runtime
    session may be referenced. It is not session creation. It is not runtime
    initialization. It is not worker allocation.
    """

    schema_version: str
    runtime_session_placeholder_ref_id: str
    delegation_ref_id: str
    runtime_session_placeholder_ref: str | None
    session_placeholder_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    session_placeholder_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "runtime_session_placeholder_ref_id": self.runtime_session_placeholder_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "session_placeholder_description": self.session_placeholder_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "session_placeholder_hash": self.session_placeholder_hash,
        }
        if self.runtime_session_placeholder_ref is not None:
            result["runtime_session_placeholder_ref"] = self.runtime_session_placeholder_ref
        return result

@dataclass(frozen=True)
class DelegationExecutionTargetRef:
    """One reference-only execution target metadata object.

    Boundary: ExecutionTargetRef describes future execution target metadata.
    It does not select a target. It does not dispatch execution.
    It does not bind actual runtime.
    """

    schema_version: str
    execution_target_ref_id: str
    delegation_ref_id: str
    execution_target_ref: str | None
    execution_target_description: str
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
    execution_target_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "execution_target_ref_id": self.execution_target_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "execution_target_description": self.execution_target_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "execution_target_hash": self.execution_target_hash,
        }
        if self.execution_target_ref is not None:
            result["execution_target_ref"] = self.execution_target_ref
        return result

@dataclass(frozen=True)
class DelegationRuntimeExecutionReadinessMatrixEntry:
    """One reference-only readiness row for future runtime/execution input context.

    Boundary: ReadinessMatrixEntry is not execution readiness.
    Input context presence is not executable.
    Finding count is not risk score.
    Presence is not runtime readiness.
    """

    schema_version: str
    entry_id: str
    delegation_ref_id: str
    family: DelegationRuntimeExecutionReadinessFamily
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
class DelegationRuntimeExecutionReadinessMatrix:
    """Lightweight reference-only matrix of future runtime/execution input contexts.

    Boundary: ReadinessMatrix is not execution readiness.
    ReadinessMatrix is not runtime admission.
    ReadinessMatrix is not enforcement matrix.
    ReadinessMatrix is not runtime safety proof.
    """

    schema_version: str
    readiness_matrix_id: str
    delegation_ref_id: str
    entries: tuple[DelegationRuntimeExecutionReadinessMatrixEntry, ...]
    source_label: DelegationSourceLabel
    matrix_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "readiness_matrix_id": self.readiness_matrix_id,
            "delegation_ref_id": self.delegation_ref_id,
            "entries": [e.to_canonical_dict() for e in self.entries],
            "source_label": self.source_label.value,
            "matrix_hash": self.matrix_hash,
        }

@dataclass(frozen=True)
class DelegationRuntimeExecutionReadinessProfile:
    """Present/missing runtime/execution readiness component profile,
    not execution/admission/enforcement readiness guarantee.

    Boundary: RuntimeExecutionReadinessProfile is not execution readiness.
    RuntimeExecutionReadinessProfile is not admission readiness.
    RuntimeExecutionReadinessProfile is not enforcement readiness.
    RuntimeExecutionReadinessProfile is not runtime safety proof.
    """

    schema_version: str
    runtime_execution_readiness_profile_id: str
    delegation_ref_id: str
    has_runtime_readiness_refs: bool
    has_execution_precondition_refs: bool
    has_execution_blocker_refs: bool
    has_runtime_admission_intent_refs: bool
    has_runtime_admission_placeholders: bool
    has_runtime_context_refs: bool
    has_tool_execution_context_refs: bool
    has_runtime_session_placeholders: bool
    has_execution_target_refs: bool
    has_policy_custos_bridge_context: bool
    has_operator_review_context: bool
    has_shadow_resolver_context: bool
    has_authority_context: bool
    has_scope_context: bool
    has_evidence_context: bool
    missing_components: tuple[str, ...]
    runtime_engine_unavailable_reason: str
    execution_engine_unavailable_reason: str
    tool_dispatch_unavailable_reason: str
    session_runtime_unavailable_reason: str
    admission_gate_unavailable_reason: str
    enforcement_unavailable_reason: str
    trace_unavailable_reason: str
    ledger_unavailable_reason: str
    source_label: DelegationSourceLabel
    readiness_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "runtime_execution_readiness_profile_id": (
                self.runtime_execution_readiness_profile_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "has_runtime_readiness_refs": self.has_runtime_readiness_refs,
            "has_execution_precondition_refs": self.has_execution_precondition_refs,
            "has_execution_blocker_refs": self.has_execution_blocker_refs,
            "has_runtime_admission_intent_refs": self.has_runtime_admission_intent_refs,
            "has_runtime_admission_placeholders": self.has_runtime_admission_placeholders,
            "has_runtime_context_refs": self.has_runtime_context_refs,
            "has_tool_execution_context_refs": self.has_tool_execution_context_refs,
            "has_runtime_session_placeholders": self.has_runtime_session_placeholders,
            "has_execution_target_refs": self.has_execution_target_refs,
            "has_policy_custos_bridge_context": self.has_policy_custos_bridge_context,
            "has_operator_review_context": self.has_operator_review_context,
            "has_shadow_resolver_context": self.has_shadow_resolver_context,
            "has_authority_context": self.has_authority_context,
            "has_scope_context": self.has_scope_context,
            "has_evidence_context": self.has_evidence_context,
            "missing_components": list(self.missing_components),
            "runtime_engine_unavailable_reason": (
                self.runtime_engine_unavailable_reason
            ),
            "execution_engine_unavailable_reason": (
                self.execution_engine_unavailable_reason
            ),
            "tool_dispatch_unavailable_reason": (
                self.tool_dispatch_unavailable_reason
            ),
            "session_runtime_unavailable_reason": (
                self.session_runtime_unavailable_reason
            ),
            "admission_gate_unavailable_reason": (
                self.admission_gate_unavailable_reason
            ),
            "enforcement_unavailable_reason": (
                self.enforcement_unavailable_reason
            ),
            "trace_unavailable_reason": self.trace_unavailable_reason,
            "ledger_unavailable_reason": self.ledger_unavailable_reason,
            "source_label": self.source_label.value,
            "readiness_hash": self.readiness_hash,
        }

@dataclass(frozen=True)
class DelegationRuntimeExecutionReadinessEnvelope:
    """Deterministic packet of runtime readiness refs, execution precondition refs,
    blocker refs, admission intent refs, admission placeholders, runtime/tool/session/
    target refs, readiness matrix hash, readiness profile hash, policy/Custos bridge
    binding set hash, and P1.8 context hashes for one delegation context.

    Boundary: RuntimeExecutionReadinessEnvelope is a reference packet.
    It is not runtime ready. It is not runtime admission.
    It is not execution allowed. It is not runtime block.
    It is not enforcement. It is not TRACE_VERIFIED.
    It does not call runtime, dispatch tools, create sessions, select targets,
    write trace, write Ledger, or mutate runtime.
    """

    schema_version: str
    runtime_execution_readiness_envelope_id: str
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
    runtime_readiness_ref_ids: tuple[str, ...]
    execution_precondition_ref_ids: tuple[str, ...]
    execution_blocker_ref_ids: tuple[str, ...]
    runtime_admission_intent_ref_ids: tuple[str, ...]
    runtime_admission_placeholder_ref_ids: tuple[str, ...]
    runtime_context_ref_ids: tuple[str, ...]
    tool_execution_context_ref_ids: tuple[str, ...]
    runtime_session_placeholder_ref_ids: tuple[str, ...]
    execution_target_ref_ids: tuple[str, ...]
    readiness_matrix_hash: str
    runtime_execution_readiness_hash: str
    source_label: DelegationSourceLabel
    runtime_execution_readiness_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "runtime_execution_readiness_envelope_id": (
                self.runtime_execution_readiness_envelope_id
            ),
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
            "policy_custos_bridge_binding_set_hash": (
                self.policy_custos_bridge_binding_set_hash
            ),
            "runtime_readiness_ref_ids": list(self.runtime_readiness_ref_ids),
            "execution_precondition_ref_ids": list(self.execution_precondition_ref_ids),
            "execution_blocker_ref_ids": list(self.execution_blocker_ref_ids),
            "runtime_admission_intent_ref_ids": list(self.runtime_admission_intent_ref_ids),
            "runtime_admission_placeholder_ref_ids": list(
                self.runtime_admission_placeholder_ref_ids
            ),
            "runtime_context_ref_ids": list(self.runtime_context_ref_ids),
            "tool_execution_context_ref_ids": list(self.tool_execution_context_ref_ids),
            "runtime_session_placeholder_ref_ids": list(
                self.runtime_session_placeholder_ref_ids
            ),
            "execution_target_ref_ids": list(self.execution_target_ref_ids),
            "readiness_matrix_hash": self.readiness_matrix_hash,
            "runtime_execution_readiness_hash": self.runtime_execution_readiness_hash,
            "source_label": self.source_label.value,
            "runtime_execution_readiness_envelope_hash": (
                self.runtime_execution_readiness_envelope_hash
            ),
        }

@dataclass(frozen=True)
class DelegationRuntimeExecutionReadinessBinding:
    """Binding between runtime/execution readiness envelope and delegation
    identity/role/constraint/authority/evidence/identity mesh/scope/lifecycle/
    chain/shadow resolver/operator review/policy-Custos bridge context.

    Boundary: RuntimeExecutionReadinessBinding binds readiness metadata.
    It is not runtime admission. It is not execution permission.
    It is not runtime block. It is not enforcement.
    It is not trace verification.
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
    runtime_execution_readiness_envelope_hash: str
    readiness_matrix_hash: str
    readiness_hash: str
    source_label: DelegationSourceLabel
    readiness_status: DelegationRuntimeExecutionReadinessStatus
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
            "policy_custos_bridge_binding_set_hash": (
                self.policy_custos_bridge_binding_set_hash
            ),
            "runtime_execution_readiness_envelope_hash": (
                self.runtime_execution_readiness_envelope_hash
            ),
            "readiness_matrix_hash": self.readiness_matrix_hash,
            "readiness_hash": self.readiness_hash,
            "source_label": self.source_label.value,
            "readiness_status": self.readiness_status.value,
            "binding_hash": self.binding_hash,
        }

@dataclass(frozen=True)
class DelegationRuntimeExecutionReadinessBindingSet:
    """Collection of runtime/execution readiness bindings for one delegation.

    Boundary: RuntimeExecutionReadinessBindingSet describes readiness hooks.
    It does not call runtime, execute, dispatch tools, create sessions,
    admit/block runtime, enforce, write Ledger/global trace, or mutate runtime.
    """

    schema_version: str
    runtime_execution_readiness_binding_set_id: str
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
    bindings: tuple[DelegationRuntimeExecutionReadinessBinding, ...]
    source_label: DelegationSourceLabel
    runtime_execution_readiness_binding_set_hash: str
    side_effects: DelegationRuntimeExecutionReadinessSideEffects

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "runtime_execution_readiness_binding_set_id": (
                self.runtime_execution_readiness_binding_set_id
            ),
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
            "policy_custos_bridge_binding_set_hash": (
                self.policy_custos_bridge_binding_set_hash
            ),
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "source_label": self.source_label.value,
            "runtime_execution_readiness_binding_set_hash": (
                self.runtime_execution_readiness_binding_set_hash
            ),
            "side_effects": {
                "runtime_engine_called": self.side_effects.runtime_engine_called,
                "execution_engine_called": self.side_effects.execution_engine_called,
                "admission_gate_called": self.side_effects.admission_gate_called,
                "runtime_admitted": self.side_effects.runtime_admitted,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "execution_allowed": self.side_effects.execution_allowed,
                "execution_blocked": self.side_effects.execution_blocked,
                "tool_dispatched": self.side_effects.tool_dispatched,
                "runtime_session_created": self.side_effects.runtime_session_created,
                "execution_target_selected": self.side_effects.execution_target_selected,
                "enforcement_performed": self.side_effects.enforcement_performed,
                "policy_called": self.side_effects.policy_called,
                "custos_called": self.side_effects.custos_called,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
        }

@dataclass
class DelegationRuntimeExecutionReadinessStatusReport:
    """Reports runtime/execution readiness model capability and unavailable surfaces."""

    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: dict[str, str]
    side_effects: DelegationRuntimeExecutionReadinessSideEffects
    status_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status_label": self.status_label,
            "available_contracts": list(self.available_contracts),
            "unavailable_bindings": dict(self.unavailable_bindings),
            "side_effects": {
                "runtime_engine_called": self.side_effects.runtime_engine_called,
                "execution_engine_called": self.side_effects.execution_engine_called,
                "admission_gate_called": self.side_effects.admission_gate_called,
                "runtime_admitted": self.side_effects.runtime_admitted,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "execution_allowed": self.side_effects.execution_allowed,
                "execution_blocked": self.side_effects.execution_blocked,
                "tool_dispatched": self.side_effects.tool_dispatched,
                "runtime_session_created": self.side_effects.runtime_session_created,
                "execution_target_selected": self.side_effects.execution_target_selected,
                "enforcement_performed": self.side_effects.enforcement_performed,
                "policy_called": self.side_effects.policy_called,
                "custos_called": self.side_effects.custos_called,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
            "status_hash": self.status_hash,
        }

# ---------------------------------------------------------------------------
# Private hash computation helpers
# ---------------------------------------------------------------------------

def _compute_runtime_readiness_ref_hash(
    *,
    runtime_readiness_ref: str | None,
    runtime_readiness_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "runtime_readiness_ref": runtime_readiness_ref,
        "runtime_readiness_description": runtime_readiness_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_execution_precondition_ref_hash(
    *,
    execution_precondition_ref: str | None,
    precondition_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "execution_precondition_ref": execution_precondition_ref,
        "precondition_description": precondition_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_execution_blocker_ref_hash(
    *,
    execution_blocker_ref: str | None,
    blocker_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "execution_blocker_ref": execution_blocker_ref,
        "blocker_description": blocker_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_runtime_admission_intent_ref_hash(
    *,
    runtime_admission_intent_ref: str | None,
    admission_intent_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "runtime_admission_intent_ref": runtime_admission_intent_ref,
        "admission_intent_description": admission_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_runtime_admission_placeholder_ref_hash(
    *,
    runtime_admission_placeholder_ref: str | None,
    admission_placeholder_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "runtime_admission_placeholder_ref": runtime_admission_placeholder_ref,
        "admission_placeholder_description": admission_placeholder_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_runtime_context_ref_hash(
    *,
    runtime_context_kind: DelegationRuntimeContextKind,
    runtime_context_ref: str | None,
    runtime_context_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "runtime_context_kind": runtime_context_kind.value,
        "runtime_context_ref": runtime_context_ref,
        "runtime_context_description": runtime_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_tool_execution_context_ref_hash(
    *,
    execution_context_kind: DelegationExecutionContextKind,
    tool_execution_context_ref: str | None,
    tool_execution_context_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "execution_context_kind": execution_context_kind.value,
        "tool_execution_context_ref": tool_execution_context_ref,
        "tool_execution_context_description": tool_execution_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_runtime_session_placeholder_ref_hash(
    *,
    runtime_session_placeholder_ref: str | None,
    session_placeholder_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "runtime_session_placeholder_ref": runtime_session_placeholder_ref,
        "session_placeholder_description": session_placeholder_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_execution_target_ref_hash(
    *,
    execution_target_ref: str | None,
    execution_target_description: str,
    reference_status: DelegationRuntimeExecutionReadinessReferenceStatus,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
) -> str:
    return stable_hash({
        "execution_target_ref": execution_target_ref,
        "execution_target_description": execution_target_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_readiness_matrix_entry_hash(
    *,
    family: DelegationRuntimeExecutionReadinessFamily,
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

def _compute_runtime_execution_readiness_readiness_hash(
    *,
    has_runtime_readiness_refs: bool,
    has_execution_precondition_refs: bool,
    has_execution_blocker_refs: bool,
    has_runtime_admission_intent_refs: bool,
    has_runtime_admission_placeholders: bool,
    has_runtime_context_refs: bool,
    has_tool_execution_context_refs: bool,
    has_runtime_session_placeholders: bool,
    has_execution_target_refs: bool,
    has_policy_custos_bridge_context: bool,
    has_operator_review_context: bool,
    has_shadow_resolver_context: bool,
    has_authority_context: bool,
    has_scope_context: bool,
    has_evidence_context: bool,
    missing_components: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "has_runtime_readiness_refs": has_runtime_readiness_refs,
        "has_execution_precondition_refs": has_execution_precondition_refs,
        "has_execution_blocker_refs": has_execution_blocker_refs,
        "has_runtime_admission_intent_refs": has_runtime_admission_intent_refs,
        "has_runtime_admission_placeholders": has_runtime_admission_placeholders,
        "has_runtime_context_refs": has_runtime_context_refs,
        "has_tool_execution_context_refs": has_tool_execution_context_refs,
        "has_runtime_session_placeholders": has_runtime_session_placeholders,
        "has_execution_target_refs": has_execution_target_refs,
        "has_policy_custos_bridge_context": has_policy_custos_bridge_context,
        "has_operator_review_context": has_operator_review_context,
        "has_shadow_resolver_context": has_shadow_resolver_context,
        "has_authority_context": has_authority_context,
        "has_scope_context": has_scope_context,
        "has_evidence_context": has_evidence_context,
        "missing_components": sorted(missing_components),
        "source_label": source_label.value,
    })

def _compute_runtime_execution_readiness_envelope_hash(
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
    readiness_matrix_hash: str,
    runtime_execution_readiness_hash: str,
    runtime_readiness_ref_ids: tuple[str, ...],
    execution_precondition_ref_ids: tuple[str, ...],
    execution_blocker_ref_ids: tuple[str, ...],
    runtime_admission_intent_ref_ids: tuple[str, ...],
    runtime_admission_placeholder_ref_ids: tuple[str, ...],
    runtime_context_ref_ids: tuple[str, ...],
    tool_execution_context_ref_ids: tuple[str, ...],
    runtime_session_placeholder_ref_ids: tuple[str, ...],
    execution_target_ref_ids: tuple[str, ...],
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
        "readiness_matrix_hash": readiness_matrix_hash,
        "runtime_execution_readiness_hash": runtime_execution_readiness_hash,
        "runtime_readiness_ref_ids": sorted(runtime_readiness_ref_ids),
        "execution_precondition_ref_ids": sorted(execution_precondition_ref_ids),
        "execution_blocker_ref_ids": sorted(execution_blocker_ref_ids),
        "runtime_admission_intent_ref_ids": sorted(runtime_admission_intent_ref_ids),
        "runtime_admission_placeholder_ref_ids": sorted(
            runtime_admission_placeholder_ref_ids
        ),
        "runtime_context_ref_ids": sorted(runtime_context_ref_ids),
        "tool_execution_context_ref_ids": sorted(tool_execution_context_ref_ids),
        "runtime_session_placeholder_ref_ids": sorted(
            runtime_session_placeholder_ref_ids
        ),
        "execution_target_ref_ids": sorted(execution_target_ref_ids),
        "source_label": source_label.value,
    })

def _compute_runtime_execution_readiness_binding_hash(
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
    runtime_execution_readiness_envelope_hash: str,
    readiness_matrix_hash: str,
    readiness_hash: str,
    source_label: DelegationSourceLabel,
    readiness_status: DelegationRuntimeExecutionReadinessStatus,
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
        "runtime_execution_readiness_envelope_hash": runtime_execution_readiness_envelope_hash,
        "readiness_matrix_hash": readiness_matrix_hash,
        "readiness_hash": readiness_hash,
        "source_label": source_label.value,
        "readiness_status": readiness_status.value,
    })

def _compute_runtime_execution_readiness_binding_set_hash(
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
        "binding_hashes": sorted(binding_hashes),
        "source_label": source_label.value,
    })

# ---------------------------------------------------------------------------
# Public builder functions
# ---------------------------------------------------------------------------

def build_delegation_runtime_readiness_ref(
    *,
    runtime_readiness_ref_id: str,
    delegation_ref_id: str,
    runtime_readiness_ref: str | None = None,
    runtime_readiness_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationRuntimeReadinessRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    runtime_readiness_hash_val = _compute_runtime_readiness_ref_hash(
        runtime_readiness_ref=runtime_readiness_ref,
        runtime_readiness_description=runtime_readiness_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationRuntimeReadinessRef(
        schema_version=DELEGATION_RUNTIME_READINESS_REF_VERSION,
        runtime_readiness_ref_id=runtime_readiness_ref_id,
        delegation_ref_id=delegation_ref_id,
        runtime_readiness_ref=runtime_readiness_ref,
        runtime_readiness_description=runtime_readiness_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        runtime_readiness_hash=runtime_readiness_hash_val,
    )

    return record

def build_delegation_execution_precondition_ref(
    *,
    execution_precondition_ref_id: str,
    delegation_ref_id: str,
    execution_precondition_ref: str | None = None,
    precondition_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationExecutionPreconditionRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    precondition_hash_val = _compute_execution_precondition_ref_hash(
        execution_precondition_ref=execution_precondition_ref,
        precondition_description=precondition_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationExecutionPreconditionRef(
        schema_version=DELEGATION_EXECUTION_PRECONDITION_REF_VERSION,
        execution_precondition_ref_id=execution_precondition_ref_id,
        delegation_ref_id=delegation_ref_id,
        execution_precondition_ref=execution_precondition_ref,
        precondition_description=precondition_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        precondition_hash=precondition_hash_val,
    )

    return record

def build_delegation_execution_blocker_ref(
    *,
    execution_blocker_ref_id: str,
    delegation_ref_id: str,
    execution_blocker_ref: str | None = None,
    blocker_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationExecutionBlockerRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    blocker_hash_val = _compute_execution_blocker_ref_hash(
        execution_blocker_ref=execution_blocker_ref,
        blocker_description=blocker_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationExecutionBlockerRef(
        schema_version=DELEGATION_EXECUTION_BLOCKER_REF_VERSION,
        execution_blocker_ref_id=execution_blocker_ref_id,
        delegation_ref_id=delegation_ref_id,
        execution_blocker_ref=execution_blocker_ref,
        blocker_description=blocker_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        blocker_hash=blocker_hash_val,
    )

    return record

def build_delegation_runtime_admission_intent_ref(
    *,
    runtime_admission_intent_ref_id: str,
    delegation_ref_id: str,
    runtime_admission_intent_ref: str | None = None,
    admission_intent_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationRuntimeAdmissionIntentRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    admission_intent_hash_val = _compute_runtime_admission_intent_ref_hash(
        runtime_admission_intent_ref=runtime_admission_intent_ref,
        admission_intent_description=admission_intent_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationRuntimeAdmissionIntentRef(
        schema_version=DELEGATION_RUNTIME_ADMISSION_INTENT_REF_VERSION,
        runtime_admission_intent_ref_id=runtime_admission_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        runtime_admission_intent_ref=runtime_admission_intent_ref,
        admission_intent_description=admission_intent_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        admission_intent_hash=admission_intent_hash_val,
    )

    return record

def build_delegation_runtime_admission_placeholder_ref(
    *,
    runtime_admission_placeholder_ref_id: str,
    delegation_ref_id: str,
    runtime_admission_placeholder_ref: str | None = None,
    admission_placeholder_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationRuntimeAdmissionPlaceholderRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    admission_placeholder_hash_val = _compute_runtime_admission_placeholder_ref_hash(
        runtime_admission_placeholder_ref=runtime_admission_placeholder_ref,
        admission_placeholder_description=admission_placeholder_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationRuntimeAdmissionPlaceholderRef(
        schema_version=DELEGATION_RUNTIME_ADMISSION_PLACEHOLDER_REF_VERSION,
        runtime_admission_placeholder_ref_id=runtime_admission_placeholder_ref_id,
        delegation_ref_id=delegation_ref_id,
        runtime_admission_placeholder_ref=runtime_admission_placeholder_ref,
        admission_placeholder_description=admission_placeholder_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        admission_placeholder_hash=admission_placeholder_hash_val,
    )

    return record

def build_delegation_runtime_context_ref(
    *,
    runtime_context_ref_id: str,
    delegation_ref_id: str,
    runtime_context_kind: DelegationRuntimeContextKind | str = DelegationRuntimeContextKind.UNKNOWN,
    runtime_context_ref: str | None = None,
    runtime_context_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationRuntimeContextRef:
    runtime_context_kind_val = _parse_runtime_context_kind(runtime_context_kind)
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    runtime_context_hash_val = _compute_runtime_context_ref_hash(
        runtime_context_kind=runtime_context_kind_val,
        runtime_context_ref=runtime_context_ref,
        runtime_context_description=runtime_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationRuntimeContextRef(
        schema_version=DELEGATION_RUNTIME_CONTEXT_REF_VERSION,
        runtime_context_ref_id=runtime_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        runtime_context_kind=runtime_context_kind_val,
        runtime_context_ref=runtime_context_ref,
        runtime_context_description=runtime_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        runtime_context_hash=runtime_context_hash_val,
    )

    return record

def build_delegation_tool_execution_context_ref(
    *,
    tool_execution_context_ref_id: str,
    delegation_ref_id: str,
    execution_context_kind: DelegationExecutionContextKind | str = DelegationExecutionContextKind.UNKNOWN,
    tool_execution_context_ref: str | None = None,
    tool_execution_context_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationToolExecutionContextRef:
    execution_context_kind_val = _parse_execution_context_kind(execution_context_kind)
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    tool_context_hash_val = _compute_tool_execution_context_ref_hash(
        execution_context_kind=execution_context_kind_val,
        tool_execution_context_ref=tool_execution_context_ref,
        tool_execution_context_description=tool_execution_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationToolExecutionContextRef(
        schema_version=DELEGATION_TOOL_EXECUTION_CONTEXT_REF_VERSION,
        tool_execution_context_ref_id=tool_execution_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        execution_context_kind=execution_context_kind_val,
        tool_execution_context_ref=tool_execution_context_ref,
        tool_execution_context_description=tool_execution_context_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        tool_context_hash=tool_context_hash_val,
    )

    return record

def build_delegation_runtime_session_placeholder_ref(
    *,
    runtime_session_placeholder_ref_id: str,
    delegation_ref_id: str,
    runtime_session_placeholder_ref: str | None = None,
    session_placeholder_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationRuntimeSessionPlaceholderRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    session_placeholder_hash_val = _compute_runtime_session_placeholder_ref_hash(
        runtime_session_placeholder_ref=runtime_session_placeholder_ref,
        session_placeholder_description=session_placeholder_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationRuntimeSessionPlaceholderRef(
        schema_version=DELEGATION_RUNTIME_SESSION_PLACEHOLDER_REF_VERSION,
        runtime_session_placeholder_ref_id=runtime_session_placeholder_ref_id,
        delegation_ref_id=delegation_ref_id,
        runtime_session_placeholder_ref=runtime_session_placeholder_ref,
        session_placeholder_description=session_placeholder_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        session_placeholder_hash=session_placeholder_hash_val,
    )

    return record

def build_delegation_execution_target_ref(
    *,
    execution_target_ref_id: str,
    delegation_ref_id: str,
    execution_target_ref: str | None = None,
    execution_target_description: str = "",
    reference_status: (
        DelegationRuntimeExecutionReadinessReferenceStatus | str
    ) = DelegationRuntimeExecutionReadinessReferenceStatus.REFERENCE_ONLY,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationExecutionTargetRef:
    reference_status_val = _parse_runtime_execution_readiness_reference_status(
        reference_status
    )
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    execution_target_hash_val = _compute_execution_target_ref_hash(
        execution_target_ref=execution_target_ref,
        execution_target_description=execution_target_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationExecutionTargetRef(
        schema_version=DELEGATION_EXECUTION_TARGET_REF_VERSION,
        execution_target_ref_id=execution_target_ref_id,
        delegation_ref_id=delegation_ref_id,
        execution_target_ref=execution_target_ref,
        execution_target_description=execution_target_description,
        reference_status=reference_status_val,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        execution_target_hash=execution_target_hash_val,
    )

    return record

def build_delegation_runtime_execution_readiness_matrix_entry(
    *,
    entry_id: str,
    delegation_ref_id: str,
    family: DelegationRuntimeExecutionReadinessFamily | str = DelegationRuntimeExecutionReadinessFamily.UNKNOWN,
    present: bool = False,
    hash_present: bool = False,
    source_label_present: bool = False,
    finding_count: int = 0,
    unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRuntimeExecutionReadinessMatrixEntry:
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
    record = DelegationRuntimeExecutionReadinessMatrixEntry(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_MATRIX_ENTRY_VERSION,
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

    return record

def build_delegation_runtime_execution_readiness_matrix(
    *,
    readiness_matrix_id: str,
    delegation_ref_id: str,
    entries: (
        Sequence[DelegationRuntimeExecutionReadinessMatrixEntry] | None
    ) = None,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRuntimeExecutionReadinessMatrix:
    source_label_val = _parse_source_label(source_label)
    entry_seq: Sequence[DelegationRuntimeExecutionReadinessMatrixEntry] = entries or ()
    sorted_entries = tuple(
        sorted(entry_seq, key=lambda e: (e.family.value, e.entry_id))
    )
    entry_hashes = tuple(e.entry_hash for e in sorted_entries)
    matrix_hash_val = _compute_readiness_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=source_label_val,
    )
    record = DelegationRuntimeExecutionReadinessMatrix(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_MATRIX_VERSION,
        readiness_matrix_id=readiness_matrix_id,
        delegation_ref_id=delegation_ref_id,
        entries=sorted_entries,
        source_label=source_label_val,
        matrix_hash=matrix_hash_val,
    )

    return record

def build_delegation_runtime_execution_readiness_profile(
    *,
    runtime_execution_readiness_profile_id: str,
    delegation_ref_id: str,
    has_runtime_readiness_refs: bool = False,
    has_execution_precondition_refs: bool = False,
    has_execution_blocker_refs: bool = False,
    has_runtime_admission_intent_refs: bool = False,
    has_runtime_admission_placeholders: bool = False,
    has_runtime_context_refs: bool = False,
    has_tool_execution_context_refs: bool = False,
    has_runtime_session_placeholders: bool = False,
    has_execution_target_refs: bool = False,
    has_policy_custos_bridge_context: bool = False,
    has_operator_review_context: bool = False,
    has_shadow_resolver_context: bool = False,
    has_authority_context: bool = False,
    has_scope_context: bool = False,
    has_evidence_context: bool = False,
    missing_components: Sequence[str] | None = None,
    runtime_engine_unavailable_reason: str = "",
    execution_engine_unavailable_reason: str = "",
    tool_dispatch_unavailable_reason: str = "",
    session_runtime_unavailable_reason: str = "",
    admission_gate_unavailable_reason: str = "",
    enforcement_unavailable_reason: str = "",
    trace_unavailable_reason: str = "",
    ledger_unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRuntimeExecutionReadinessProfile:
    source_label_val = _parse_source_label(source_label)
    missing = tuple(sorted(set(missing_components or ())))
    readiness_hash_val = _compute_runtime_execution_readiness_readiness_hash(
        has_runtime_readiness_refs=has_runtime_readiness_refs,
        has_execution_precondition_refs=has_execution_precondition_refs,
        has_execution_blocker_refs=has_execution_blocker_refs,
        has_runtime_admission_intent_refs=has_runtime_admission_intent_refs,
        has_runtime_admission_placeholders=has_runtime_admission_placeholders,
        has_runtime_context_refs=has_runtime_context_refs,
        has_tool_execution_context_refs=has_tool_execution_context_refs,
        has_runtime_session_placeholders=has_runtime_session_placeholders,
        has_execution_target_refs=has_execution_target_refs,
        has_policy_custos_bridge_context=has_policy_custos_bridge_context,
        has_operator_review_context=has_operator_review_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_scope_context=has_scope_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing,
        source_label=source_label_val,
    )
    record = DelegationRuntimeExecutionReadinessProfile(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_PROFILE_VERSION,
        runtime_execution_readiness_profile_id=runtime_execution_readiness_profile_id,
        delegation_ref_id=delegation_ref_id,
        has_runtime_readiness_refs=has_runtime_readiness_refs,
        has_execution_precondition_refs=has_execution_precondition_refs,
        has_execution_blocker_refs=has_execution_blocker_refs,
        has_runtime_admission_intent_refs=has_runtime_admission_intent_refs,
        has_runtime_admission_placeholders=has_runtime_admission_placeholders,
        has_runtime_context_refs=has_runtime_context_refs,
        has_tool_execution_context_refs=has_tool_execution_context_refs,
        has_runtime_session_placeholders=has_runtime_session_placeholders,
        has_execution_target_refs=has_execution_target_refs,
        has_policy_custos_bridge_context=has_policy_custos_bridge_context,
        has_operator_review_context=has_operator_review_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_scope_context=has_scope_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing,
        runtime_engine_unavailable_reason=runtime_engine_unavailable_reason,
        execution_engine_unavailable_reason=execution_engine_unavailable_reason,
        tool_dispatch_unavailable_reason=tool_dispatch_unavailable_reason,
        session_runtime_unavailable_reason=session_runtime_unavailable_reason,
        admission_gate_unavailable_reason=admission_gate_unavailable_reason,
        enforcement_unavailable_reason=enforcement_unavailable_reason,
        trace_unavailable_reason=trace_unavailable_reason,
        ledger_unavailable_reason=ledger_unavailable_reason,
        source_label=source_label_val,
        readiness_hash=readiness_hash_val,
    )

    return record

def build_delegation_runtime_execution_readiness_envelope(
    *,
    runtime_execution_readiness_envelope_id: str,
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
    runtime_readiness_ref_ids: Sequence[str] | None = None,
    execution_precondition_ref_ids: Sequence[str] | None = None,
    execution_blocker_ref_ids: Sequence[str] | None = None,
    runtime_admission_intent_ref_ids: Sequence[str] | None = None,
    runtime_admission_placeholder_ref_ids: Sequence[str] | None = None,
    runtime_context_ref_ids: Sequence[str] | None = None,
    tool_execution_context_ref_ids: Sequence[str] | None = None,
    runtime_session_placeholder_ref_ids: Sequence[str] | None = None,
    execution_target_ref_ids: Sequence[str] | None = None,
    readiness_matrix_hash: str = "",
    runtime_execution_readiness_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
) -> DelegationRuntimeExecutionReadinessEnvelope:
    source_label_val = _parse_source_label(source_label)
    rr_ids: tuple[str, ...] = tuple(runtime_readiness_ref_ids or ())
    ep_ids: tuple[str, ...] = tuple(execution_precondition_ref_ids or ())
    eb_ids: tuple[str, ...] = tuple(execution_blocker_ref_ids or ())
    ai_ids: tuple[str, ...] = tuple(runtime_admission_intent_ref_ids or ())
    ap_ids: tuple[str, ...] = tuple(runtime_admission_placeholder_ref_ids or ())
    rc_ids: tuple[str, ...] = tuple(runtime_context_ref_ids or ())
    te_ids: tuple[str, ...] = tuple(tool_execution_context_ref_ids or ())
    sp_ids: tuple[str, ...] = tuple(runtime_session_placeholder_ref_ids or ())
    et_ids: tuple[str, ...] = tuple(execution_target_ref_ids or ())
    envelope_hash_val = _compute_runtime_execution_readiness_envelope_hash(
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
        readiness_matrix_hash=readiness_matrix_hash,
        runtime_execution_readiness_hash=runtime_execution_readiness_hash,
        runtime_readiness_ref_ids=rr_ids,
        execution_precondition_ref_ids=ep_ids,
        execution_blocker_ref_ids=eb_ids,
        runtime_admission_intent_ref_ids=ai_ids,
        runtime_admission_placeholder_ref_ids=ap_ids,
        runtime_context_ref_ids=rc_ids,
        tool_execution_context_ref_ids=te_ids,
        runtime_session_placeholder_ref_ids=sp_ids,
        execution_target_ref_ids=et_ids,
        source_label=source_label_val,
    )
    record = DelegationRuntimeExecutionReadinessEnvelope(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_ENVELOPE_VERSION,
        runtime_execution_readiness_envelope_id=runtime_execution_readiness_envelope_id,
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
        runtime_readiness_ref_ids=rr_ids,
        execution_precondition_ref_ids=ep_ids,
        execution_blocker_ref_ids=eb_ids,
        runtime_admission_intent_ref_ids=ai_ids,
        runtime_admission_placeholder_ref_ids=ap_ids,
        runtime_context_ref_ids=rc_ids,
        tool_execution_context_ref_ids=te_ids,
        runtime_session_placeholder_ref_ids=sp_ids,
        execution_target_ref_ids=et_ids,
        readiness_matrix_hash=readiness_matrix_hash,
        runtime_execution_readiness_hash=runtime_execution_readiness_hash,
        source_label=source_label_val,
        runtime_execution_readiness_envelope_hash=envelope_hash_val,
    )

    return record

def build_delegation_runtime_execution_readiness_binding(
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
    runtime_execution_readiness_envelope_hash: str = "",
    readiness_matrix_hash: str = "",
    readiness_hash: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    readiness_status: (
        DelegationRuntimeExecutionReadinessStatus | str
    ) = DelegationRuntimeExecutionReadinessStatus.REFERENCE_ONLY,
) -> DelegationRuntimeExecutionReadinessBinding:
    source_label_val = _parse_source_label(source_label)
    readiness_status_val = _parse_runtime_execution_readiness_status(readiness_status)
    binding_hash_val = _compute_runtime_execution_readiness_binding_hash(
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
        runtime_execution_readiness_envelope_hash=runtime_execution_readiness_envelope_hash,
        readiness_matrix_hash=readiness_matrix_hash,
        readiness_hash=readiness_hash,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
    )
    record = DelegationRuntimeExecutionReadinessBinding(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_BINDING_VERSION,
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
        runtime_execution_readiness_envelope_hash=runtime_execution_readiness_envelope_hash,
        readiness_matrix_hash=readiness_matrix_hash,
        readiness_hash=readiness_hash,
        source_label=source_label_val,
        readiness_status=readiness_status_val,
        binding_hash=binding_hash_val,
    )

    return record

def build_delegation_runtime_execution_readiness_binding_set(
    *,
    runtime_execution_readiness_binding_set_id: str,
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
    bindings: Sequence[DelegationRuntimeExecutionReadinessBinding] | None = None,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    side_effects: DelegationRuntimeExecutionReadinessSideEffects | None = None,
) -> DelegationRuntimeExecutionReadinessBindingSet:
    source_label_val = _parse_source_label(source_label)
    binding_seq: Sequence[DelegationRuntimeExecutionReadinessBinding] = bindings or ()
    sorted_bindings = tuple(
        sorted(binding_seq, key=lambda b: b.binding_id)
    )
    binding_hashes = tuple(b.binding_hash for b in sorted_bindings)
    side_effects_val = (
        side_effects if side_effects is not None
        else DelegationRuntimeExecutionReadinessSideEffects()
    )
    binding_set_hash_val = _compute_runtime_execution_readiness_binding_set_hash(
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
        binding_hashes=binding_hashes,
        source_label=source_label_val,
    )
    record = DelegationRuntimeExecutionReadinessBindingSet(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_BINDING_SET_VERSION,
        runtime_execution_readiness_binding_set_id=runtime_execution_readiness_binding_set_id,
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
        bindings=sorted_bindings,
        source_label=source_label_val,
        runtime_execution_readiness_binding_set_hash=binding_set_hash_val,
        side_effects=side_effects_val,
    )

    return record

def build_delegation_runtime_execution_readiness_status_report(
    *,
    status_label: str = "P1.8.13_REFERENCE_ONLY",
    available_contracts: Sequence[str] | None = None,
    unavailable_bindings: dict[str, str] | None = None,
    side_effects: DelegationRuntimeExecutionReadinessSideEffects | None = None,
) -> DelegationRuntimeExecutionReadinessStatusReport:
    contracts = tuple(available_contracts or ())
    bindings = dict(unavailable_bindings) if unavailable_bindings is not None else dict(DELEGATION_RUNTIME_EXECUTION_READINESS_UNAVAILABLE_BINDINGS)
    se = (
        side_effects if side_effects is not None
        else DelegationRuntimeExecutionReadinessSideEffects()
    )
    status_hash_val = stable_hash({
        "status_label": status_label,
        "available_contracts": sorted(contracts),
        "unavailable_bindings_keys": sorted(bindings.keys()),
    })
    record = DelegationRuntimeExecutionReadinessStatusReport(
        schema_version=DELEGATION_RUNTIME_EXECUTION_READINESS_STATUS_REPORT_VERSION,
        status_label=status_label,
        available_contracts=contracts,
        unavailable_bindings=bindings,
        side_effects=se,
        status_hash=status_hash_val,
    )

    return record

# ---------------------------------------------------------------------------
# Public hash functions
# ---------------------------------------------------------------------------

def hash_delegation_runtime_readiness_ref(
    obj: DelegationRuntimeReadinessRef,
) -> str:
    return _compute_runtime_readiness_ref_hash(
        runtime_readiness_ref=obj.runtime_readiness_ref,
        runtime_readiness_description=obj.runtime_readiness_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_execution_precondition_ref(
    obj: DelegationExecutionPreconditionRef,
) -> str:
    return _compute_execution_precondition_ref_hash(
        execution_precondition_ref=obj.execution_precondition_ref,
        precondition_description=obj.precondition_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_execution_blocker_ref(
    obj: DelegationExecutionBlockerRef,
) -> str:
    return _compute_execution_blocker_ref_hash(
        execution_blocker_ref=obj.execution_blocker_ref,
        blocker_description=obj.blocker_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_runtime_admission_intent_ref(
    obj: DelegationRuntimeAdmissionIntentRef,
) -> str:
    return _compute_runtime_admission_intent_ref_hash(
        runtime_admission_intent_ref=obj.runtime_admission_intent_ref,
        admission_intent_description=obj.admission_intent_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_runtime_admission_placeholder_ref(
    obj: DelegationRuntimeAdmissionPlaceholderRef,
) -> str:
    return _compute_runtime_admission_placeholder_ref_hash(
        runtime_admission_placeholder_ref=obj.runtime_admission_placeholder_ref,
        admission_placeholder_description=obj.admission_placeholder_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_runtime_context_ref(
    obj: DelegationRuntimeContextRef,
) -> str:
    return _compute_runtime_context_ref_hash(
        runtime_context_kind=obj.runtime_context_kind,
        runtime_context_ref=obj.runtime_context_ref,
        runtime_context_description=obj.runtime_context_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_tool_execution_context_ref(
    obj: DelegationToolExecutionContextRef,
) -> str:
    return _compute_tool_execution_context_ref_hash(
        execution_context_kind=obj.execution_context_kind,
        tool_execution_context_ref=obj.tool_execution_context_ref,
        tool_execution_context_description=obj.tool_execution_context_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_runtime_session_placeholder_ref(
    obj: DelegationRuntimeSessionPlaceholderRef,
) -> str:
    return _compute_runtime_session_placeholder_ref_hash(
        runtime_session_placeholder_ref=obj.runtime_session_placeholder_ref,
        session_placeholder_description=obj.session_placeholder_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_execution_target_ref(
    obj: DelegationExecutionTargetRef,
) -> str:
    return _compute_execution_target_ref_hash(
        execution_target_ref=obj.execution_target_ref,
        execution_target_description=obj.execution_target_description,
        reference_status=obj.reference_status,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_runtime_execution_readiness_matrix_entry(
    obj: DelegationRuntimeExecutionReadinessMatrixEntry,
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

def hash_delegation_runtime_execution_readiness_matrix(
    obj: DelegationRuntimeExecutionReadinessMatrix,
) -> str:
    entry_hashes = tuple(e.entry_hash for e in obj.entries)
    return _compute_readiness_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=obj.source_label,
    )

def hash_delegation_runtime_execution_readiness_profile(
    obj: DelegationRuntimeExecutionReadinessProfile,
) -> str:
    return _compute_runtime_execution_readiness_readiness_hash(
        has_runtime_readiness_refs=obj.has_runtime_readiness_refs,
        has_execution_precondition_refs=obj.has_execution_precondition_refs,
        has_execution_blocker_refs=obj.has_execution_blocker_refs,
        has_runtime_admission_intent_refs=obj.has_runtime_admission_intent_refs,
        has_runtime_admission_placeholders=obj.has_runtime_admission_placeholders,
        has_runtime_context_refs=obj.has_runtime_context_refs,
        has_tool_execution_context_refs=obj.has_tool_execution_context_refs,
        has_runtime_session_placeholders=obj.has_runtime_session_placeholders,
        has_execution_target_refs=obj.has_execution_target_refs,
        has_policy_custos_bridge_context=obj.has_policy_custos_bridge_context,
        has_operator_review_context=obj.has_operator_review_context,
        has_shadow_resolver_context=obj.has_shadow_resolver_context,
        has_authority_context=obj.has_authority_context,
        has_scope_context=obj.has_scope_context,
        has_evidence_context=obj.has_evidence_context,
        missing_components=obj.missing_components,
        source_label=obj.source_label,
    )

def hash_delegation_runtime_execution_readiness_envelope(
    obj: DelegationRuntimeExecutionReadinessEnvelope,
) -> str:
    return _compute_runtime_execution_readiness_envelope_hash(
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
        readiness_matrix_hash=obj.readiness_matrix_hash,
        runtime_execution_readiness_hash=obj.runtime_execution_readiness_hash,
        runtime_readiness_ref_ids=obj.runtime_readiness_ref_ids,
        execution_precondition_ref_ids=obj.execution_precondition_ref_ids,
        execution_blocker_ref_ids=obj.execution_blocker_ref_ids,
        runtime_admission_intent_ref_ids=obj.runtime_admission_intent_ref_ids,
        runtime_admission_placeholder_ref_ids=obj.runtime_admission_placeholder_ref_ids,
        runtime_context_ref_ids=obj.runtime_context_ref_ids,
        tool_execution_context_ref_ids=obj.tool_execution_context_ref_ids,
        runtime_session_placeholder_ref_ids=obj.runtime_session_placeholder_ref_ids,
        execution_target_ref_ids=obj.execution_target_ref_ids,
        source_label=obj.source_label,
    )

def hash_delegation_runtime_execution_readiness_binding(
    obj: DelegationRuntimeExecutionReadinessBinding,
) -> str:
    return _compute_runtime_execution_readiness_binding_hash(
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
        runtime_execution_readiness_envelope_hash=obj.runtime_execution_readiness_envelope_hash,
        readiness_matrix_hash=obj.readiness_matrix_hash,
        readiness_hash=obj.readiness_hash,
        source_label=obj.source_label,
        readiness_status=obj.readiness_status,
    )

def hash_delegation_runtime_execution_readiness_binding_set(
    obj: DelegationRuntimeExecutionReadinessBindingSet,
) -> str:
    binding_hashes = tuple(b.binding_hash for b in obj.bindings)
    return _compute_runtime_execution_readiness_binding_set_hash(
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
        binding_hashes=binding_hashes,
        source_label=obj.source_label,
    )

def hash_delegation_runtime_execution_readiness_status_report(
    obj: DelegationRuntimeExecutionReadinessStatusReport,
) -> str:
    return obj.status_hash

# ---------------------------------------------------------------------------
# Public serialization functions
# ---------------------------------------------------------------------------

def serialize_delegation_runtime_execution_readiness_envelope(
    obj: DelegationRuntimeExecutionReadinessEnvelope,
) -> str:
    return to_canonical_json(obj.to_canonical_dict())

def serialize_delegation_runtime_execution_readiness_binding_set(
    obj: DelegationRuntimeExecutionReadinessBindingSet,
) -> str:
    return to_canonical_json(obj.to_canonical_dict())
