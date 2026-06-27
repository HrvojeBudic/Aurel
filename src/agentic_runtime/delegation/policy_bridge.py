"""Delegation policy/Custos bridge reference model (P1.8.12).

Deterministic, versioned, JSON-safe, side-effect-free reference-only
policy/Custos bridge metadata layer over P1.8.0-P1.8.11 delegation context.

Produces policy bridge refs, Custos bridge refs, policy context refs,
Custos context refs, policy decision request intent refs, Custos
decision request intent refs, policy decision response placeholder refs,
Custos decision response placeholder refs, compatibility matrix,
bridge readiness profile, bridge envelope, bridge binding, and bridge
binding set without policy engine call, Custos runtime call, decision
request execution, decision response, allow/deny emission,
approval/rejection creation, authority grant/deny, runtime allow/block,
enforcement, trace write, Ledger write, or runtime mutation.

Architectural law:
  - PolicyBridgeRef exists does not mean policy evaluated.
  - CustosBridgeRef exists does not mean Custos called.
  - PolicyContextRef exists does not mean policy compliance.
  - CustosContextRef exists does not mean Custos approval.
  - DecisionRequestIntentRef exists does not mean decision requested.
  - DecisionResponsePlaceholderRef exists does not mean decision response exists.
  - CompatibilityMatrix exists does not mean policy evaluation.
  - BridgeReadinessProfile exists does not mean decision readiness.
  - Policy/Custos bridge hash exists does not mean TRACE_VERIFIED.
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

DELEGATION_POLICY_CUSTOS_BRIDGE_TASK_ID = "P1.8.12"
DELEGATION_POLICY_BRIDGE_REF_VERSION = "delegation_policy_bridge_ref.v1"
DELEGATION_CUSTOS_BRIDGE_REF_VERSION = "delegation_custos_bridge_ref.v1"
DELEGATION_POLICY_CONTEXT_REF_VERSION = "delegation_policy_context_ref.v1"
DELEGATION_CUSTOS_CONTEXT_REF_VERSION = "delegation_custos_context_ref.v1"
DELEGATION_POLICY_DECISION_REQUEST_INTENT_REF_VERSION = "delegation_policy_decision_request_intent_ref.v1"
DELEGATION_CUSTOS_DECISION_REQUEST_INTENT_REF_VERSION = "delegation_custos_decision_request_intent_ref.v1"
DELEGATION_POLICY_DECISION_RESPONSE_PLACEHOLDER_REF_VERSION = "delegation_policy_decision_response_placeholder_ref.v1"
DELEGATION_CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REF_VERSION = "delegation_custos_decision_response_placeholder_ref.v1"
DELEGATION_POLICY_CUSTOS_COMPATIBILITY_MATRIX_ENTRY_VERSION = "delegation_policy_custos_compatibility_matrix_entry.v1"
DELEGATION_POLICY_CUSTOS_COMPATIBILITY_MATRIX_VERSION = "delegation_policy_custos_compatibility_matrix.v1"
DELEGATION_POLICY_CUSTOS_BRIDGE_READINESS_PROFILE_VERSION = "delegation_policy_custos_bridge_readiness_profile.v1"
DELEGATION_POLICY_CUSTOS_BRIDGE_ENVELOPE_VERSION = "delegation_policy_custos_bridge_envelope.v1"
DELEGATION_POLICY_CUSTOS_BRIDGE_BINDING_VERSION = "delegation_policy_custos_bridge_binding.v1"
DELEGATION_POLICY_CUSTOS_BRIDGE_BINDING_SET_VERSION = "delegation_policy_custos_bridge_binding_set.v1"
DELEGATION_POLICY_CUSTOS_BRIDGE_SIDE_EFFECTS_VERSION = "delegation_policy_custos_bridge_side_effects.v1"
DELEGATION_POLICY_CUSTOS_BRIDGE_STATUS_REPORT_VERSION = "delegation_policy_custos_bridge_status_report.v1"

# ---------------------------------------------------------------------------
# Unavailable bindings
# ---------------------------------------------------------------------------

DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS: dict[str, str] = {
    "Projection/API/Event/Read Model": (
        "Projection/API/event/read model is not available in P1.8.12; "
        "reference-only metadata layer"
    ),
    "CLI/Shell/TUI Binding": (
        "CLI/Shell/TUI binding scheduled for later P1.8 tasks; not P1.8.12"
    ),
    "Ledger Write": (
        "Ledger write is not available in P1.8.12 policy/Custos bridge layer"
    ),
    "Global Trace Write": (
        "Global trace spine write is not available in P1.8.12 "
        "policy/Custos bridge layer"
    ),
    "Policy Engine": (
        "Policy engine is not available in P1.8.12; "
        "PolicyBridgeRef is reference-only metadata, not policy evaluation"
    ),
    "Custos Runtime": (
        "Custos runtime is not available in P1.8.12; "
        "CustosBridgeRef is reference-only metadata, not Custos call"
    ),
    "Decision Engine": (
        "Decision engine is not available in P1.8.12; "
        "DecisionRequestIntentRef is reference-only intent, not decision request"
    ),
    "Decision Request Executor": (
        "Decision request executor is not available in P1.8.12; "
        "no actual decision request execution exists"
    ),
    "Decision Response Receiver": (
        "Decision response receiver is not available in P1.8.12; "
        "DecisionResponsePlaceholderRef is reference-only placeholder"
    ),
    "Allow/Deny Resolver": (
        "Allow/deny resolver is not available in P1.8.12; "
        "policy/Custos bridge does not emit allow/deny decisions"
    ),
    "Approval/Rejection Creation": (
        "Approval/rejection creation is not available in P1.8.12; "
        "policy/Custos bridge does not create approval or rejection"
    ),
    "Authority Grant/Deny": (
        "Authority grant/deny is not available in P1.8.12; "
        "policy/Custos bridge does not grant or deny authority"
    ),
    "Runtime Allow/Block": (
        "Runtime allow/block is not available in P1.8.12; "
        "policy/Custos bridge does not allow or block runtime"
    ),
    "Enforcement Engine": (
        "Enforcement engine is not available in P1.8.12; "
        "policy/Custos bridge does not enforce"
    ),
    "Trace Writer": (
        "Trace writer is not available in P1.8.12; "
        "policy/Custos bridge does not write trace events"
    ),
    "P1.8.13 Runtime/Execution ReadinessRef Model": (
        "P1.8.13 runtime/execution readiness model is not implemented in P1.8.12"
    ),
    "Output Passport / P1.9": (
        "Output Passport / P1.9 is not implemented in P1.8.12"
    ),
    "Runtime Delegation Execution": (
        "Runtime delegation execution is not available in P1.8.12; "
        "policy/Custos bridge is reference-only metadata"
    ),
}

# ---------------------------------------------------------------------------
# Known fields (closed-world validation)
# ---------------------------------------------------------------------------

POLICY_BRIDGE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "policy_bridge_ref_id",
    "delegation_ref_id",
    "policy_bridge_ref",
    "policy_bridge_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "policy_bridge_hash",
})

CUSTOS_BRIDGE_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "custos_bridge_ref_id",
    "delegation_ref_id",
    "custos_bridge_ref",
    "custos_bridge_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "custos_bridge_hash",
})

POLICY_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "policy_context_ref_id",
    "delegation_ref_id",
    "policy_context_kind",
    "policy_context_ref",
    "policy_context_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "policy_context_hash",
})

CUSTOS_CONTEXT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "custos_context_ref_id",
    "delegation_ref_id",
    "custos_context_kind",
    "custos_context_ref",
    "custos_context_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "custos_context_hash",
})

POLICY_DECISION_REQUEST_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "policy_decision_request_intent_ref_id",
    "delegation_ref_id",
    "policy_decision_request_intent_ref",
    "request_intent_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "request_intent_hash",
})

CUSTOS_DECISION_REQUEST_INTENT_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "custos_decision_request_intent_ref_id",
    "delegation_ref_id",
    "custos_decision_request_intent_ref",
    "request_intent_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "request_intent_hash",
})

POLICY_DECISION_RESPONSE_PLACEHOLDER_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "policy_decision_response_placeholder_ref_id",
    "delegation_ref_id",
    "policy_decision_response_placeholder_ref",
    "response_placeholder_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "response_placeholder_hash",
})

CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REF_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "custos_decision_response_placeholder_ref_id",
    "delegation_ref_id",
    "custos_decision_response_placeholder_ref",
    "response_placeholder_description",
    "reference_status",
    "source_label",
    "bridge_status",
    "response_placeholder_hash",
})

COMPATIBILITY_MATRIX_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset({
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

COMPATIBILITY_MATRIX_PB_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "compatibility_matrix_id",
    "delegation_ref_id",
    "entries",
    "source_label",
    "matrix_hash",
})

BRIDGE_READINESS_PROFILE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "bridge_readiness_profile_id",
    "delegation_ref_id",
    "has_policy_bridge_refs",
    "has_custos_bridge_refs",
    "has_policy_context_refs",
    "has_custos_context_refs",
    "has_policy_decision_request_intent_refs",
    "has_custos_decision_request_intent_refs",
    "has_policy_decision_response_placeholders",
    "has_custos_decision_response_placeholders",
    "has_operator_review_context",
    "has_shadow_resolver_context",
    "has_authority_context",
    "has_scope_context",
    "has_evidence_context",
    "missing_components",
    "policy_engine_unavailable_reason",
    "custos_runtime_unavailable_reason",
    "decision_engine_unavailable_reason",
    "enforcement_unavailable_reason",
    "trace_unavailable_reason",
    "ledger_unavailable_reason",
    "source_label",
    "readiness_hash",
})

BRIDGE_ENVELOPE_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "policy_custos_bridge_envelope_id",
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
    "policy_bridge_ref_ids",
    "custos_bridge_ref_ids",
    "policy_context_ref_ids",
    "custos_context_ref_ids",
    "policy_decision_request_intent_ref_ids",
    "custos_decision_request_intent_ref_ids",
    "policy_decision_response_placeholder_ref_ids",
    "custos_decision_response_placeholder_ref_ids",
    "compatibility_matrix_hash",
    "bridge_readiness_hash",
    "source_label",
    "policy_custos_bridge_envelope_hash",
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
    "policy_custos_bridge_envelope_hash",
    "bridge_readiness_hash",
    "compatibility_matrix_hash",
    "source_label",
    "bridge_status",
    "binding_hash",
})

BRIDGE_BINDING_SET_KNOWN_FIELDS: frozenset[str] = frozenset({
    "schema_version",
    "policy_custos_bridge_binding_set_id",
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
    "binding_ids",
    "source_label",
    "policy_custos_bridge_binding_set_hash",
    "side_effects",
})

BRIDGE_SIDE_EFFECTS_KNOWN_FIELDS: frozenset[str] = frozenset({
    "policy_engine_called",
    "custos_runtime_called",
    "decision_requested",
    "decision_response_received",
    "allow_decision_emitted",
    "deny_decision_emitted",
    "approval_created",
    "rejection_created",
    "authority_granted",
    "authority_denied",
    "runtime_allowed",
    "runtime_blocked",
    "enforcement_performed",
    "ledger_written",
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


class DelegationPolicyCustosBridgeKind(str, Enum):
    """Bridge kind classifier; does not evaluate policy or call Custos."""

    POLICY_BRIDGE = "POLICY_BRIDGE"
    CUSTOS_BRIDGE = "CUSTOS_BRIDGE"
    POLICY_CONTEXT = "POLICY_CONTEXT"
    CUSTOS_CONTEXT = "CUSTOS_CONTEXT"
    DECISION_REQUEST_INTENT = "DECISION_REQUEST_INTENT"
    DECISION_RESPONSE_PLACEHOLDER = "DECISION_RESPONSE_PLACEHOLDER"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNKNOWN = "UNKNOWN"


class DelegationPolicyCustosBridgeReferenceStatus(str, Enum):
    """Reference status ladder; never implies policy evaluation or Custos call.

    Boundary:
      - POLICY_BRIDGE_REFERENCED is not policy evaluated.
      - CUSTOS_BRIDGE_REFERENCED is not Custos called.
      - POLICY_CONTEXT_REFERENCED is not policy compliance.
      - CUSTOS_CONTEXT_REFERENCED is not Custos approval.
      - POLICY_DECISION_REQUEST_INTENT_REFERENCED is not policy decision requested.
      - CUSTOS_DECISION_REQUEST_INTENT_REFERENCED is not Custos decision requested.
      - POLICY_DECISION_RESPONSE_PLACEHOLDER_REFERENCED is not policy response.
      - CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REFERENCED is not Custos response.
      - POLICY_ENGINE_UNAVAILABLE is honest unavailability, not policy failure.
      - CUSTOS_RUNTIME_UNAVAILABLE is honest unavailability, not Custos failure.
      - DECISION_ENGINE_UNAVAILABLE is honest unavailability, not decision failure.
      - ENFORCEMENT_UNAVAILABLE is honest unavailability, not enforcement failure.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    POLICY_BRIDGE_REFERENCED = "POLICY_BRIDGE_REFERENCED"
    CUSTOS_BRIDGE_REFERENCED = "CUSTOS_BRIDGE_REFERENCED"
    POLICY_CONTEXT_REFERENCED = "POLICY_CONTEXT_REFERENCED"
    CUSTOS_CONTEXT_REFERENCED = "CUSTOS_CONTEXT_REFERENCED"
    POLICY_DECISION_REQUEST_INTENT_REFERENCED = "POLICY_DECISION_REQUEST_INTENT_REFERENCED"
    CUSTOS_DECISION_REQUEST_INTENT_REFERENCED = "CUSTOS_DECISION_REQUEST_INTENT_REFERENCED"
    POLICY_DECISION_RESPONSE_PLACEHOLDER_REFERENCED = "POLICY_DECISION_RESPONSE_PLACEHOLDER_REFERENCED"
    CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REFERENCED = "CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REFERENCED"
    POLICY_ENGINE_UNAVAILABLE = "POLICY_ENGINE_UNAVAILABLE"
    CUSTOS_RUNTIME_UNAVAILABLE = "CUSTOS_RUNTIME_UNAVAILABLE"
    DECISION_ENGINE_UNAVAILABLE = "DECISION_ENGINE_UNAVAILABLE"
    ENFORCEMENT_UNAVAILABLE = "ENFORCEMENT_UNAVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationPolicyCustosBridgeStatus(str, Enum):
    """Bridge declaration status; does not imply decision or compliance.

    Boundary:
      - REFERENCE_ONLY means bridge context is reference-only.
      - DECLARED means bridge context was declared as metadata.
      - Neither means policy evaluated, Custos called, decision requested,
        allow/deny emitted, or enforcement performed.
    """

    REFERENCE_ONLY = "REFERENCE_ONLY"
    DECLARED = "DECLARED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DelegationPolicyContextKind(str, Enum):
    """Policy context kind classifier; does not prove policy compliance.

    Boundary:
      - Policy context kind classifies future policy input metadata.
      - It does not prove policy compliance.
      - It does not evaluate policy.
    """

    IDENTITY_POLICY_CONTEXT = "IDENTITY_POLICY_CONTEXT"
    ROLE_POLICY_CONTEXT = "ROLE_POLICY_CONTEXT"
    CONSTRAINT_POLICY_CONTEXT = "CONSTRAINT_POLICY_CONTEXT"
    AUTHORITY_POLICY_CONTEXT = "AUTHORITY_POLICY_CONTEXT"
    SCOPE_POLICY_CONTEXT = "SCOPE_POLICY_CONTEXT"
    EVIDENCE_POLICY_CONTEXT = "EVIDENCE_POLICY_CONTEXT"
    OPERATOR_REVIEW_POLICY_CONTEXT = "OPERATOR_REVIEW_POLICY_CONTEXT"
    UNKNOWN = "UNKNOWN"


class DelegationCustosContextKind(str, Enum):
    """Custos context kind classifier; does not prove Custos approval.

    Boundary:
      - Custos context kind classifies future Custos input metadata.
      - It does not prove Custos approval.
      - It does not call Custos.
    """

    IDENTITY_CUSTOS_CONTEXT = "IDENTITY_CUSTOS_CONTEXT"
    ROLE_CUSTOS_CONTEXT = "ROLE_CUSTOS_CONTEXT"
    CONSTRAINT_CUSTOS_CONTEXT = "CONSTRAINT_CUSTOS_CONTEXT"
    AUTHORITY_CUSTOS_CONTEXT = "AUTHORITY_CUSTOS_CONTEXT"
    SCOPE_CUSTOS_CONTEXT = "SCOPE_CUSTOS_CONTEXT"
    EVIDENCE_CUSTOS_CONTEXT = "EVIDENCE_CUSTOS_CONTEXT"
    OPERATOR_REVIEW_CUSTOS_CONTEXT = "OPERATOR_REVIEW_CUSTOS_CONTEXT"
    UNKNOWN = "UNKNOWN"


class DelegationPolicyCustosCompatibilityFamily(str, Enum):
    """Compatibility family classifier; does not represent policy evaluation.

    Boundary:
      - Compatibility family classifies possible future policy/Custos input context.
      - It does not represent policy evaluation.
      - It does not indicate allow/deny.
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
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# SideEffects (plain dataclass, all defaults False)
# ---------------------------------------------------------------------------


@dataclass
class DelegationPolicyCustosBridgeSideEffects:
    """Hard proof that P1.8.12 is reference-only, non-decisioning,
    non-Custos-calling, non-enforcing, and non-mutating.  All fields
    default to False."""

    policy_engine_called: bool = False
    custos_runtime_called: bool = False
    decision_requested: bool = False
    decision_response_received: bool = False
    allow_decision_emitted: bool = False
    deny_decision_emitted: bool = False
    approval_created: bool = False
    rejection_created: bool = False
    authority_granted: bool = False
    authority_denied: bool = False
    runtime_allowed: bool = False
    runtime_blocked: bool = False
    enforcement_performed: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    runtime_mutated: bool = False


# ---------------------------------------------------------------------------
# Private enum parsers
# ---------------------------------------------------------------------------


def _parse_policy_custos_bridge_kind(
    value: DelegationPolicyCustosBridgeKind | str,
) -> DelegationPolicyCustosBridgeKind:
    if isinstance(value, DelegationPolicyCustosBridgeKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationPolicyCustosBridgeKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid bridge_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="bridge_kind",
            ) from exc
    raise DelegationError(
        "bridge_kind must be a string or DelegationPolicyCustosBridgeKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="bridge_kind",
    )


def _parse_policy_custos_bridge_reference_status(
    value: DelegationPolicyCustosBridgeReferenceStatus | str,
) -> DelegationPolicyCustosBridgeReferenceStatus:
    if isinstance(value, DelegationPolicyCustosBridgeReferenceStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationPolicyCustosBridgeReferenceStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid reference_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="reference_status",
            ) from exc
    raise DelegationError(
        "reference_status must be a string or DelegationPolicyCustosBridgeReferenceStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="reference_status",
    )


def _parse_policy_custos_bridge_status(
    value: DelegationPolicyCustosBridgeStatus | str,
) -> DelegationPolicyCustosBridgeStatus:
    if isinstance(value, DelegationPolicyCustosBridgeStatus):
        return value
    if isinstance(value, str):
        try:
            return DelegationPolicyCustosBridgeStatus(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid bridge_status: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="bridge_status",
            ) from exc
    raise DelegationError(
        "bridge_status must be a string or DelegationPolicyCustosBridgeStatus",
        code=DelegationErrorCode.INVALID_ENUM,
        field="bridge_status",
    )


def _parse_policy_context_kind(
    value: DelegationPolicyContextKind | str,
) -> DelegationPolicyContextKind:
    if isinstance(value, DelegationPolicyContextKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationPolicyContextKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid policy_context_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="policy_context_kind",
            ) from exc
    raise DelegationError(
        "policy_context_kind must be a string or DelegationPolicyContextKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="policy_context_kind",
    )


def _parse_custos_context_kind(
    value: DelegationCustosContextKind | str,
) -> DelegationCustosContextKind:
    if isinstance(value, DelegationCustosContextKind):
        return value
    if isinstance(value, str):
        try:
            return DelegationCustosContextKind(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid custos_context_kind: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="custos_context_kind",
            ) from exc
    raise DelegationError(
        "custos_context_kind must be a string or DelegationCustosContextKind",
        code=DelegationErrorCode.INVALID_ENUM,
        field="custos_context_kind",
    )


def _parse_compatibility_family(
    value: DelegationPolicyCustosCompatibilityFamily | str,
) -> DelegationPolicyCustosCompatibilityFamily:
    if isinstance(value, DelegationPolicyCustosCompatibilityFamily):
        return value
    if isinstance(value, str):
        try:
            return DelegationPolicyCustosCompatibilityFamily(value)
        except ValueError as exc:
            raise DelegationError(
                f"invalid family: {value!r}",
                code=DelegationErrorCode.INVALID_ENUM,
                field="family",
            ) from exc
    raise DelegationError(
        "family must be a string or DelegationPolicyCustosCompatibilityFamily",
        code=DelegationErrorCode.INVALID_ENUM,
        field="family",
    )


# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationPolicyBridgeRef:
    """One reference-only policy bridge metadata object.

    Boundary: PolicyBridgeRef describes future policy bridge metadata.
    It does not evaluate policy. It does not decide allow/deny.
    It does not call policy engine. It does not enforce.
    """

    schema_version: str
    policy_bridge_ref_id: str
    delegation_ref_id: str
    policy_bridge_ref: str | None
    policy_bridge_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    policy_bridge_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "policy_bridge_ref_id": self.policy_bridge_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "policy_bridge_description": self.policy_bridge_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "policy_bridge_hash": self.policy_bridge_hash,
        }
        if self.policy_bridge_ref is not None:
            result["policy_bridge_ref"] = self.policy_bridge_ref
        return result


@dataclass(frozen=True)
class DelegationCustosBridgeRef:
    """One reference-only Custos bridge metadata object.

    Boundary: CustosBridgeRef describes future Custos bridge metadata.
    It does not call Custos. It does not decide allow/deny.
    It does not approve. It does not enforce.
    """

    schema_version: str
    custos_bridge_ref_id: str
    delegation_ref_id: str
    custos_bridge_ref: str | None
    custos_bridge_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    custos_bridge_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "custos_bridge_ref_id": self.custos_bridge_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "custos_bridge_description": self.custos_bridge_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "custos_bridge_hash": self.custos_bridge_hash,
        }
        if self.custos_bridge_ref is not None:
            result["custos_bridge_ref"] = self.custos_bridge_ref
        return result


@dataclass(frozen=True)
class DelegationPolicyContextRef:
    """One reference-only policy context metadata object.

    Boundary: PolicyContextRef describes future policy input context.
    It does not prove policy compliance. It does not evaluate policy.
    It does not authorize runtime.
    """

    schema_version: str
    policy_context_ref_id: str
    delegation_ref_id: str
    policy_context_kind: DelegationPolicyContextKind
    policy_context_ref: str | None
    policy_context_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    policy_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "policy_context_ref_id": self.policy_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "policy_context_kind": self.policy_context_kind.value,
            "policy_context_description": self.policy_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "policy_context_hash": self.policy_context_hash,
        }
        if self.policy_context_ref is not None:
            result["policy_context_ref"] = self.policy_context_ref
        return result


@dataclass(frozen=True)
class DelegationCustosContextRef:
    """One reference-only Custos context metadata object.

    Boundary: CustosContextRef describes future Custos input context.
    It does not prove Custos approval. It does not call Custos.
    It does not authorize runtime.
    """

    schema_version: str
    custos_context_ref_id: str
    delegation_ref_id: str
    custos_context_kind: DelegationCustosContextKind
    custos_context_ref: str | None
    custos_context_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    custos_context_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "custos_context_ref_id": self.custos_context_ref_id,
            "delegation_ref_id": self.delegation_ref_id,
            "custos_context_kind": self.custos_context_kind.value,
            "custos_context_description": self.custos_context_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "custos_context_hash": self.custos_context_hash,
        }
        if self.custos_context_ref is not None:
            result["custos_context_ref"] = self.custos_context_ref
        return result


@dataclass(frozen=True)
class DelegationPolicyDecisionRequestIntentRef:
    """One reference-only intent to later request policy decision.

    Boundary: PolicyDecisionRequestIntentRef describes decision request intent
    metadata. It does not request a policy decision. It does not call policy
    engine. It does not produce allow/deny.
    """

    schema_version: str
    policy_decision_request_intent_ref_id: str
    delegation_ref_id: str
    policy_decision_request_intent_ref: str | None
    request_intent_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    request_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "policy_decision_request_intent_ref_id": (
                self.policy_decision_request_intent_ref_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "request_intent_description": self.request_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "request_intent_hash": self.request_intent_hash,
        }
        if self.policy_decision_request_intent_ref is not None:
            result["policy_decision_request_intent_ref"] = (
                self.policy_decision_request_intent_ref
            )
        return result


@dataclass(frozen=True)
class DelegationCustosDecisionRequestIntentRef:
    """One reference-only intent to later request Custos decision.

    Boundary: CustosDecisionRequestIntentRef describes decision request intent
    metadata. It does not request a Custos decision. It does not call Custos
    runtime. It does not produce allow/deny.
    """

    schema_version: str
    custos_decision_request_intent_ref_id: str
    delegation_ref_id: str
    custos_decision_request_intent_ref: str | None
    request_intent_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    request_intent_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "custos_decision_request_intent_ref_id": (
                self.custos_decision_request_intent_ref_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "request_intent_description": self.request_intent_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "request_intent_hash": self.request_intent_hash,
        }
        if self.custos_decision_request_intent_ref is not None:
            result["custos_decision_request_intent_ref"] = (
                self.custos_decision_request_intent_ref
            )
        return result


@dataclass(frozen=True)
class DelegationPolicyDecisionResponsePlaceholderRef:
    """One reference-only placeholder for future policy decision response.

    Boundary: PolicyDecisionResponsePlaceholderRef describes where a future
    response may be referenced. It is not a policy response. It is not
    allow/deny. It is not compliance proof.
    """

    schema_version: str
    policy_decision_response_placeholder_ref_id: str
    delegation_ref_id: str
    policy_decision_response_placeholder_ref: str | None
    response_placeholder_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    response_placeholder_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "policy_decision_response_placeholder_ref_id": (
                self.policy_decision_response_placeholder_ref_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "response_placeholder_description": self.response_placeholder_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "response_placeholder_hash": self.response_placeholder_hash,
        }
        if self.policy_decision_response_placeholder_ref is not None:
            result["policy_decision_response_placeholder_ref"] = (
                self.policy_decision_response_placeholder_ref
            )
        return result


@dataclass(frozen=True)
class DelegationCustosDecisionResponsePlaceholderRef:
    """One reference-only placeholder for future Custos decision response.

    Boundary: CustosDecisionResponsePlaceholderRef describes where a future
    Custos response may be referenced. It is not a Custos response. It is not
    allow/deny. It is not Custos approval.
    """

    schema_version: str
    custos_decision_response_placeholder_ref_id: str
    delegation_ref_id: str
    custos_decision_response_placeholder_ref: str | None
    response_placeholder_description: str
    reference_status: DelegationPolicyCustosBridgeReferenceStatus
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
    response_placeholder_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "custos_decision_response_placeholder_ref_id": (
                self.custos_decision_response_placeholder_ref_id
            ),
            "delegation_ref_id": self.delegation_ref_id,
            "response_placeholder_description": self.response_placeholder_description,
            "reference_status": self.reference_status.value,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "response_placeholder_hash": self.response_placeholder_hash,
        }
        if self.custos_decision_response_placeholder_ref is not None:
            result["custos_decision_response_placeholder_ref"] = (
                self.custos_decision_response_placeholder_ref
            )
        return result


@dataclass(frozen=True)
class DelegationPolicyCustosCompatibilityMatrixEntry:
    """One reference-only compatibility row for future policy/Custos input context.

    Boundary: CompatibilityMatrixEntry is not policy evaluation.
    Input compatibility is not allow/deny. Finding count is not risk score.
    Presence is not compliance.
    """

    schema_version: str
    entry_id: str
    delegation_ref_id: str
    family: DelegationPolicyCustosCompatibilityFamily
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
class DelegationPolicyCustosCompatibilityMatrix:
    """Lightweight reference-only matrix of future policy/Custos input contexts.

    Boundary: CompatibilityMatrix is not policy evaluation.
    CompatibilityMatrix is not Custos decision.
    CompatibilityMatrix is not approval matrix.
    CompatibilityMatrix is not compliance proof.
    """

    schema_version: str
    compatibility_matrix_id: str
    delegation_ref_id: str
    entries: tuple[DelegationPolicyCustosCompatibilityMatrixEntry, ...]
    source_label: DelegationSourceLabel
    matrix_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "compatibility_matrix_id": self.compatibility_matrix_id,
            "delegation_ref_id": self.delegation_ref_id,
            "entries": [e.to_canonical_dict() for e in self.entries],
            "source_label": self.source_label.value,
            "matrix_hash": self.matrix_hash,
        }


@dataclass(frozen=True)
class DelegationPolicyCustosBridgeReadinessProfile:
    """Present/missing bridge component profile, not decision/enforcement
    readiness guarantee.

    Boundary: BridgeReadinessProfile is not decision readiness.
    BridgeReadinessProfile is not policy compliance.
    BridgeReadinessProfile is not Custos approval.
    BridgeReadinessProfile is not enforcement readiness.
    BridgeReadinessProfile is not runtime safety proof.
    """

    schema_version: str
    bridge_readiness_profile_id: str
    delegation_ref_id: str
    has_policy_bridge_refs: bool
    has_custos_bridge_refs: bool
    has_policy_context_refs: bool
    has_custos_context_refs: bool
    has_policy_decision_request_intent_refs: bool
    has_custos_decision_request_intent_refs: bool
    has_policy_decision_response_placeholders: bool
    has_custos_decision_response_placeholders: bool
    has_operator_review_context: bool
    has_shadow_resolver_context: bool
    has_authority_context: bool
    has_scope_context: bool
    has_evidence_context: bool
    missing_components: tuple[str, ...]
    policy_engine_unavailable_reason: str
    custos_runtime_unavailable_reason: str
    decision_engine_unavailable_reason: str
    enforcement_unavailable_reason: str
    trace_unavailable_reason: str
    ledger_unavailable_reason: str
    source_label: DelegationSourceLabel
    readiness_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_readiness_profile_id": self.bridge_readiness_profile_id,
            "delegation_ref_id": self.delegation_ref_id,
            "has_policy_bridge_refs": self.has_policy_bridge_refs,
            "has_custos_bridge_refs": self.has_custos_bridge_refs,
            "has_policy_context_refs": self.has_policy_context_refs,
            "has_custos_context_refs": self.has_custos_context_refs,
            "has_policy_decision_request_intent_refs": (
                self.has_policy_decision_request_intent_refs
            ),
            "has_custos_decision_request_intent_refs": (
                self.has_custos_decision_request_intent_refs
            ),
            "has_policy_decision_response_placeholders": (
                self.has_policy_decision_response_placeholders
            ),
            "has_custos_decision_response_placeholders": (
                self.has_custos_decision_response_placeholders
            ),
            "has_operator_review_context": self.has_operator_review_context,
            "has_shadow_resolver_context": self.has_shadow_resolver_context,
            "has_authority_context": self.has_authority_context,
            "has_scope_context": self.has_scope_context,
            "has_evidence_context": self.has_evidence_context,
            "missing_components": list(self.missing_components),
            "policy_engine_unavailable_reason": (
                self.policy_engine_unavailable_reason
            ),
            "custos_runtime_unavailable_reason": (
                self.custos_runtime_unavailable_reason
            ),
            "decision_engine_unavailable_reason": (
                self.decision_engine_unavailable_reason
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
class DelegationPolicyCustosBridgeEnvelope:
    """Deterministic packet of policy/Custos bridge refs, context refs, decision
    request intents, response placeholders, compatibility matrix hash, bridge
    readiness hash, operator review binding set hash, and P1.8 context hashes
    for one delegation context.

    Boundary: PolicyCustosBridgeEnvelope is a reference packet.
    It is not policy decision. It is not Custos call.
    It is not allow/deny. It is not approval/rejection.
    It is not enforcement. It is not TRACE_VERIFIED.
    It does not call policy engine, call Custos, request decision,
    receive response, write trace, write Ledger, or mutate runtime.
    """

    schema_version: str
    policy_custos_bridge_envelope_id: str
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
    policy_bridge_ref_ids: tuple[str, ...]
    custos_bridge_ref_ids: tuple[str, ...]
    policy_context_ref_ids: tuple[str, ...]
    custos_context_ref_ids: tuple[str, ...]
    policy_decision_request_intent_ref_ids: tuple[str, ...]
    custos_decision_request_intent_ref_ids: tuple[str, ...]
    policy_decision_response_placeholder_ref_ids: tuple[str, ...]
    custos_decision_response_placeholder_ref_ids: tuple[str, ...]
    compatibility_matrix_hash: str
    bridge_readiness_hash: str
    source_label: DelegationSourceLabel
    policy_custos_bridge_envelope_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_custos_bridge_envelope_id": (
                self.policy_custos_bridge_envelope_id
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
            "policy_bridge_ref_ids": list(self.policy_bridge_ref_ids),
            "custos_bridge_ref_ids": list(self.custos_bridge_ref_ids),
            "policy_context_ref_ids": list(self.policy_context_ref_ids),
            "custos_context_ref_ids": list(self.custos_context_ref_ids),
            "policy_decision_request_intent_ref_ids": list(
                self.policy_decision_request_intent_ref_ids
            ),
            "custos_decision_request_intent_ref_ids": list(
                self.custos_decision_request_intent_ref_ids
            ),
            "policy_decision_response_placeholder_ref_ids": list(
                self.policy_decision_response_placeholder_ref_ids
            ),
            "custos_decision_response_placeholder_ref_ids": list(
                self.custos_decision_response_placeholder_ref_ids
            ),
            "compatibility_matrix_hash": self.compatibility_matrix_hash,
            "bridge_readiness_hash": self.bridge_readiness_hash,
            "source_label": self.source_label.value,
            "policy_custos_bridge_envelope_hash": (
                self.policy_custos_bridge_envelope_hash
            ),
        }


@dataclass(frozen=True)
class DelegationPolicyCustosBridgeBinding:
    """Binding between policy/Custos bridge envelope and delegation context.

    Boundary: PolicyCustosBridgeBinding binds bridge metadata.
    It is not policy decision. It is not Custos decision.
    It is not approval. It is not denial.
    It is not enforcement. It is not trace verification.
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
    policy_custos_bridge_envelope_hash: str
    bridge_readiness_hash: str
    compatibility_matrix_hash: str
    source_label: DelegationSourceLabel
    bridge_status: DelegationPolicyCustosBridgeStatus
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
            "policy_custos_bridge_envelope_hash": (
                self.policy_custos_bridge_envelope_hash
            ),
            "bridge_readiness_hash": self.bridge_readiness_hash,
            "compatibility_matrix_hash": self.compatibility_matrix_hash,
            "source_label": self.source_label.value,
            "bridge_status": self.bridge_status.value,
            "binding_hash": self.binding_hash,
        }


@dataclass(frozen=True)
class DelegationPolicyCustosBridgeBindingSet:
    """Collection of policy/Custos bridge bindings for one delegation.

    Boundary: PolicyCustosBridgeBindingSet describes bridge hooks.
    It does not call policy/Custos, request decisions, emit allow/deny,
    approve/reject, enforce, authorize runtime, write Ledger/global trace,
    or mutate runtime.
    """

    schema_version: str
    policy_custos_bridge_binding_set_id: str
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
    bindings: tuple[DelegationPolicyCustosBridgeBinding, ...]
    source_label: DelegationSourceLabel
    policy_custos_bridge_binding_set_hash: str
    side_effects: DelegationPolicyCustosBridgeSideEffects

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_custos_bridge_binding_set_id": (
                self.policy_custos_bridge_binding_set_id
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
            "bindings": [b.to_canonical_dict() for b in self.bindings],
            "source_label": self.source_label.value,
            "policy_custos_bridge_binding_set_hash": (
                self.policy_custos_bridge_binding_set_hash
            ),
            "side_effects": {
                "policy_engine_called": self.side_effects.policy_engine_called,
                "custos_runtime_called": self.side_effects.custos_runtime_called,
                "decision_requested": self.side_effects.decision_requested,
                "decision_response_received": (
                    self.side_effects.decision_response_received
                ),
                "allow_decision_emitted": self.side_effects.allow_decision_emitted,
                "deny_decision_emitted": self.side_effects.deny_decision_emitted,
                "approval_created": self.side_effects.approval_created,
                "rejection_created": self.side_effects.rejection_created,
                "authority_granted": self.side_effects.authority_granted,
                "authority_denied": self.side_effects.authority_denied,
                "runtime_allowed": self.side_effects.runtime_allowed,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "enforcement_performed": self.side_effects.enforcement_performed,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
        }


@dataclass
class DelegationPolicyCustosBridgeStatusReport:
    """Reports policy/Custos bridge model readiness and unavailable surfaces."""

    schema_version: str
    status_label: str
    available_contracts: tuple[str, ...]
    unavailable_bindings: dict[str, str]
    side_effects: DelegationPolicyCustosBridgeSideEffects
    status_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status_label": self.status_label,
            "available_contracts": list(self.available_contracts),
            "unavailable_bindings": dict(self.unavailable_bindings),
            "side_effects": {
                "policy_engine_called": self.side_effects.policy_engine_called,
                "custos_runtime_called": self.side_effects.custos_runtime_called,
                "decision_requested": self.side_effects.decision_requested,
                "decision_response_received": (
                    self.side_effects.decision_response_received
                ),
                "allow_decision_emitted": self.side_effects.allow_decision_emitted,
                "deny_decision_emitted": self.side_effects.deny_decision_emitted,
                "approval_created": self.side_effects.approval_created,
                "rejection_created": self.side_effects.rejection_created,
                "authority_granted": self.side_effects.authority_granted,
                "authority_denied": self.side_effects.authority_denied,
                "runtime_allowed": self.side_effects.runtime_allowed,
                "runtime_blocked": self.side_effects.runtime_blocked,
                "enforcement_performed": self.side_effects.enforcement_performed,
                "ledger_written": self.side_effects.ledger_written,
                "global_trace_written": self.side_effects.global_trace_written,
                "runtime_mutated": self.side_effects.runtime_mutated,
            },
            "status_hash": self.status_hash,
        }


# ---------------------------------------------------------------------------
# Private hash computation helpers
# ---------------------------------------------------------------------------


def _compute_policy_bridge_ref_hash(
    *,
    policy_bridge_ref: str | None,
    policy_bridge_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "policy_bridge_ref": policy_bridge_ref,
        "policy_bridge_description": policy_bridge_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_custos_bridge_ref_hash(
    *,
    custos_bridge_ref: str | None,
    custos_bridge_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "custos_bridge_ref": custos_bridge_ref,
        "custos_bridge_description": custos_bridge_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_policy_context_ref_hash(
    *,
    policy_context_kind: DelegationPolicyContextKind,
    policy_context_ref: str | None,
    policy_context_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "policy_context_kind": policy_context_kind.value,
        "policy_context_ref": policy_context_ref,
        "policy_context_description": policy_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_custos_context_ref_hash(
    *,
    custos_context_kind: DelegationCustosContextKind,
    custos_context_ref: str | None,
    custos_context_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "custos_context_kind": custos_context_kind.value,
        "custos_context_ref": custos_context_ref,
        "custos_context_description": custos_context_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_policy_decision_request_intent_ref_hash(
    *,
    policy_decision_request_intent_ref: str | None,
    request_intent_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "policy_decision_request_intent_ref": policy_decision_request_intent_ref,
        "request_intent_description": request_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_custos_decision_request_intent_ref_hash(
    *,
    custos_decision_request_intent_ref: str | None,
    request_intent_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "custos_decision_request_intent_ref": custos_decision_request_intent_ref,
        "request_intent_description": request_intent_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_policy_decision_response_placeholder_ref_hash(
    *,
    policy_decision_response_placeholder_ref: str | None,
    response_placeholder_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "policy_decision_response_placeholder_ref": policy_decision_response_placeholder_ref,
        "response_placeholder_description": response_placeholder_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_custos_decision_response_placeholder_ref_hash(
    *,
    custos_decision_response_placeholder_ref: str | None,
    response_placeholder_description: str,
    reference_status: DelegationPolicyCustosBridgeReferenceStatus,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "custos_decision_response_placeholder_ref": custos_decision_response_placeholder_ref,
        "response_placeholder_description": response_placeholder_description,
        "reference_status": reference_status.value,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_compatibility_matrix_entry_hash(
    *,
    family: DelegationPolicyCustosCompatibilityFamily,
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


def _compute_compatibility_matrix_hash(
    *,
    entry_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "entry_hashes": sorted(entry_hashes),
        "source_label": source_label.value,
    })


def _compute_bridge_readiness_profile_hash(
    *,
    has_policy_bridge_refs: bool,
    has_custos_bridge_refs: bool,
    has_policy_context_refs: bool,
    has_custos_context_refs: bool,
    has_policy_decision_request_intent_refs: bool,
    has_custos_decision_request_intent_refs: bool,
    has_policy_decision_response_placeholders: bool,
    has_custos_decision_response_placeholders: bool,
    has_operator_review_context: bool,
    has_shadow_resolver_context: bool,
    has_authority_context: bool,
    has_scope_context: bool,
    has_evidence_context: bool,
    missing_components: tuple[str, ...],
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "has_policy_bridge_refs": has_policy_bridge_refs,
        "has_custos_bridge_refs": has_custos_bridge_refs,
        "has_policy_context_refs": has_policy_context_refs,
        "has_custos_context_refs": has_custos_context_refs,
        "has_policy_decision_request_intent_refs": has_policy_decision_request_intent_refs,
        "has_custos_decision_request_intent_refs": has_custos_decision_request_intent_refs,
        "has_policy_decision_response_placeholders": has_policy_decision_response_placeholders,
        "has_custos_decision_response_placeholders": has_custos_decision_response_placeholders,
        "has_operator_review_context": has_operator_review_context,
        "has_shadow_resolver_context": has_shadow_resolver_context,
        "has_authority_context": has_authority_context,
        "has_scope_context": has_scope_context,
        "has_evidence_context": has_evidence_context,
        "missing_components": sorted(missing_components),
        "source_label": source_label.value,
    })


def _compute_policy_custos_bridge_envelope_hash(
    *,
    delegation_ref_id: str,
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
    policy_bridge_ref_ids: tuple[str, ...],
    custos_bridge_ref_ids: tuple[str, ...],
    policy_context_ref_ids: tuple[str, ...],
    custos_context_ref_ids: tuple[str, ...],
    policy_decision_request_intent_ref_ids: tuple[str, ...],
    custos_decision_request_intent_ref_ids: tuple[str, ...],
    policy_decision_response_placeholder_ref_ids: tuple[str, ...],
    custos_decision_response_placeholder_ref_ids: tuple[str, ...],
    compatibility_matrix_hash: str,
    bridge_readiness_hash: str,
    source_label: DelegationSourceLabel,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
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
        "policy_bridge_ref_ids": sorted(policy_bridge_ref_ids),
        "custos_bridge_ref_ids": sorted(custos_bridge_ref_ids),
        "policy_context_ref_ids": sorted(policy_context_ref_ids),
        "custos_context_ref_ids": sorted(custos_context_ref_ids),
        "policy_decision_request_intent_ref_ids": sorted(
            policy_decision_request_intent_ref_ids
        ),
        "custos_decision_request_intent_ref_ids": sorted(
            custos_decision_request_intent_ref_ids
        ),
        "policy_decision_response_placeholder_ref_ids": sorted(
            policy_decision_response_placeholder_ref_ids
        ),
        "custos_decision_response_placeholder_ref_ids": sorted(
            custos_decision_response_placeholder_ref_ids
        ),
        "compatibility_matrix_hash": compatibility_matrix_hash,
        "bridge_readiness_hash": bridge_readiness_hash,
        "source_label": source_label.value,
    })


def _compute_policy_custos_bridge_binding_hash(
    *,
    delegation_ref_id: str,
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
    policy_custos_bridge_envelope_hash: str,
    bridge_readiness_hash: str,
    compatibility_matrix_hash: str,
    source_label: DelegationSourceLabel,
    bridge_status: DelegationPolicyCustosBridgeStatus,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
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
        "policy_custos_bridge_envelope_hash": policy_custos_bridge_envelope_hash,
        "bridge_readiness_hash": bridge_readiness_hash,
        "compatibility_matrix_hash": compatibility_matrix_hash,
        "source_label": source_label.value,
        "bridge_status": bridge_status.value,
    })


def _compute_policy_custos_bridge_binding_set_hash(
    *,
    delegation_ref_id: str,
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
    binding_hashes: tuple[str, ...],
    source_label: DelegationSourceLabel,
    side_effects: DelegationPolicyCustosBridgeSideEffects,
) -> str:
    return stable_hash({
        "delegation_ref_id": delegation_ref_id,
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
        "binding_hashes": sorted(binding_hashes),
        "source_label": source_label.value,
        "side_effects": {
            "policy_engine_called": side_effects.policy_engine_called,
            "custos_runtime_called": side_effects.custos_runtime_called,
            "decision_requested": side_effects.decision_requested,
            "decision_response_received": side_effects.decision_response_received,
            "allow_decision_emitted": side_effects.allow_decision_emitted,
            "deny_decision_emitted": side_effects.deny_decision_emitted,
            "approval_created": side_effects.approval_created,
            "rejection_created": side_effects.rejection_created,
            "authority_granted": side_effects.authority_granted,
            "authority_denied": side_effects.authority_denied,
            "runtime_allowed": side_effects.runtime_allowed,
            "runtime_blocked": side_effects.runtime_blocked,
            "enforcement_performed": side_effects.enforcement_performed,
            "ledger_written": side_effects.ledger_written,
            "global_trace_written": side_effects.global_trace_written,
            "runtime_mutated": side_effects.runtime_mutated,
        },
    })


def _compute_policy_custos_bridge_status_report_hash(
    *,
    available_contracts: tuple[str, ...],
    side_effects: DelegationPolicyCustosBridgeSideEffects,
) -> str:
    return stable_hash({
        "available_contracts": sorted(available_contracts),
        "side_effects": {
            "policy_engine_called": side_effects.policy_engine_called,
            "custos_runtime_called": side_effects.custos_runtime_called,
            "decision_requested": side_effects.decision_requested,
            "decision_response_received": side_effects.decision_response_received,
            "allow_decision_emitted": side_effects.allow_decision_emitted,
            "deny_decision_emitted": side_effects.deny_decision_emitted,
            "approval_created": side_effects.approval_created,
            "rejection_created": side_effects.rejection_created,
            "authority_granted": side_effects.authority_granted,
            "authority_denied": side_effects.authority_denied,
            "runtime_allowed": side_effects.runtime_allowed,
            "runtime_blocked": side_effects.runtime_blocked,
            "enforcement_performed": side_effects.enforcement_performed,
            "ledger_written": side_effects.ledger_written,
            "global_trace_written": side_effects.global_trace_written,
            "runtime_mutated": side_effects.runtime_mutated,
        },
    })


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_delegation_policy_bridge_ref(
    *,
    delegation_ref_id: str,
    policy_bridge_ref: str | None = None,
    policy_bridge_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.POLICY_BRIDGE_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    policy_bridge_ref_id: str | None = None,
) -> DelegationPolicyBridgeRef:
    """Build a DelegationPolicyBridgeRef — reference-only, not policy evaluation."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    policy_bridge_ref_clean = _optional_string(policy_bridge_ref)

    if policy_bridge_ref_id is None:
        policy_bridge_ref_id = f"pb-policybridge-{delegation_ref_id[:12]}"

    policy_bridge_hash = _compute_policy_bridge_ref_hash(
        policy_bridge_ref=policy_bridge_ref_clean,
        policy_bridge_description=policy_bridge_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationPolicyBridgeRef(
        schema_version=DELEGATION_POLICY_BRIDGE_REF_VERSION,
        policy_bridge_ref_id=policy_bridge_ref_id,
        delegation_ref_id=delegation_ref_id,
        policy_bridge_ref=policy_bridge_ref_clean,
        policy_bridge_description=policy_bridge_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        policy_bridge_hash=policy_bridge_hash,
    )


def build_delegation_custos_bridge_ref(
    *,
    delegation_ref_id: str,
    custos_bridge_ref: str | None = None,
    custos_bridge_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.CUSTOS_BRIDGE_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    custos_bridge_ref_id: str | None = None,
) -> DelegationCustosBridgeRef:
    """Build a DelegationCustosBridgeRef — reference-only, not Custos call."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    custos_bridge_ref_clean = _optional_string(custos_bridge_ref)

    if custos_bridge_ref_id is None:
        custos_bridge_ref_id = f"pb-custosbridge-{delegation_ref_id[:12]}"

    custos_bridge_hash = _compute_custos_bridge_ref_hash(
        custos_bridge_ref=custos_bridge_ref_clean,
        custos_bridge_description=custos_bridge_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationCustosBridgeRef(
        schema_version=DELEGATION_CUSTOS_BRIDGE_REF_VERSION,
        custos_bridge_ref_id=custos_bridge_ref_id,
        delegation_ref_id=delegation_ref_id,
        custos_bridge_ref=custos_bridge_ref_clean,
        custos_bridge_description=custos_bridge_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        custos_bridge_hash=custos_bridge_hash,
    )


def build_delegation_policy_context_ref(
    *,
    delegation_ref_id: str,
    policy_context_kind: DelegationPolicyContextKind | str = DelegationPolicyContextKind.IDENTITY_POLICY_CONTEXT,
    policy_context_ref: str | None = None,
    policy_context_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.POLICY_CONTEXT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    policy_context_ref_id: str | None = None,
) -> DelegationPolicyContextRef:
    """Build a DelegationPolicyContextRef — reference-only, not policy compliance."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_context_kind = _parse_policy_context_kind(policy_context_kind)
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    policy_context_ref_clean = _optional_string(policy_context_ref)

    if policy_context_ref_id is None:
        policy_context_ref_id = f"pb-policyctx-{delegation_ref_id[:12]}"

    policy_context_hash = _compute_policy_context_ref_hash(
        policy_context_kind=parsed_context_kind,
        policy_context_ref=policy_context_ref_clean,
        policy_context_description=policy_context_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationPolicyContextRef(
        schema_version=DELEGATION_POLICY_CONTEXT_REF_VERSION,
        policy_context_ref_id=policy_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        policy_context_kind=parsed_context_kind,
        policy_context_ref=policy_context_ref_clean,
        policy_context_description=policy_context_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        policy_context_hash=policy_context_hash,
    )


def build_delegation_custos_context_ref(
    *,
    delegation_ref_id: str,
    custos_context_kind: DelegationCustosContextKind | str = DelegationCustosContextKind.IDENTITY_CUSTOS_CONTEXT,
    custos_context_ref: str | None = None,
    custos_context_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.CUSTOS_CONTEXT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    custos_context_ref_id: str | None = None,
) -> DelegationCustosContextRef:
    """Build a DelegationCustosContextRef — reference-only, not Custos approval."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_context_kind = _parse_custos_context_kind(custos_context_kind)
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    custos_context_ref_clean = _optional_string(custos_context_ref)

    if custos_context_ref_id is None:
        custos_context_ref_id = f"pb-custosctx-{delegation_ref_id[:12]}"

    custos_context_hash = _compute_custos_context_ref_hash(
        custos_context_kind=parsed_context_kind,
        custos_context_ref=custos_context_ref_clean,
        custos_context_description=custos_context_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationCustosContextRef(
        schema_version=DELEGATION_CUSTOS_CONTEXT_REF_VERSION,
        custos_context_ref_id=custos_context_ref_id,
        delegation_ref_id=delegation_ref_id,
        custos_context_kind=parsed_context_kind,
        custos_context_ref=custos_context_ref_clean,
        custos_context_description=custos_context_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        custos_context_hash=custos_context_hash,
    )


def build_delegation_policy_decision_request_intent_ref(
    *,
    delegation_ref_id: str,
    policy_decision_request_intent_ref: str | None = None,
    request_intent_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.POLICY_DECISION_REQUEST_INTENT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    policy_decision_request_intent_ref_id: str | None = None,
) -> DelegationPolicyDecisionRequestIntentRef:
    """Build a DelegationPolicyDecisionRequestIntentRef — reference-only,
    not decision request execution."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    intent_ref_clean = _optional_string(policy_decision_request_intent_ref)

    if policy_decision_request_intent_ref_id is None:
        policy_decision_request_intent_ref_id = (
            f"pb-polreqintent-{delegation_ref_id[:12]}"
        )

    request_intent_hash = _compute_policy_decision_request_intent_ref_hash(
        policy_decision_request_intent_ref=intent_ref_clean,
        request_intent_description=request_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationPolicyDecisionRequestIntentRef(
        schema_version=DELEGATION_POLICY_DECISION_REQUEST_INTENT_REF_VERSION,
        policy_decision_request_intent_ref_id=policy_decision_request_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        policy_decision_request_intent_ref=intent_ref_clean,
        request_intent_description=request_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        request_intent_hash=request_intent_hash,
    )


def build_delegation_custos_decision_request_intent_ref(
    *,
    delegation_ref_id: str,
    custos_decision_request_intent_ref: str | None = None,
    request_intent_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.CUSTOS_DECISION_REQUEST_INTENT_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    custos_decision_request_intent_ref_id: str | None = None,
) -> DelegationCustosDecisionRequestIntentRef:
    """Build a DelegationCustosDecisionRequestIntentRef — reference-only,
    not Custos decision request execution."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    intent_ref_clean = _optional_string(custos_decision_request_intent_ref)

    if custos_decision_request_intent_ref_id is None:
        custos_decision_request_intent_ref_id = (
            f"pb-cusreqintent-{delegation_ref_id[:12]}"
        )

    request_intent_hash = _compute_custos_decision_request_intent_ref_hash(
        custos_decision_request_intent_ref=intent_ref_clean,
        request_intent_description=request_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationCustosDecisionRequestIntentRef(
        schema_version=DELEGATION_CUSTOS_DECISION_REQUEST_INTENT_REF_VERSION,
        custos_decision_request_intent_ref_id=custos_decision_request_intent_ref_id,
        delegation_ref_id=delegation_ref_id,
        custos_decision_request_intent_ref=intent_ref_clean,
        request_intent_description=request_intent_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        request_intent_hash=request_intent_hash,
    )


def build_delegation_policy_decision_response_placeholder_ref(
    *,
    delegation_ref_id: str,
    policy_decision_response_placeholder_ref: str | None = None,
    response_placeholder_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.POLICY_DECISION_RESPONSE_PLACEHOLDER_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    policy_decision_response_placeholder_ref_id: str | None = None,
) -> DelegationPolicyDecisionResponsePlaceholderRef:
    """Build a DelegationPolicyDecisionResponsePlaceholderRef — reference-only,
    not policy response."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    placeholder_ref_clean = _optional_string(policy_decision_response_placeholder_ref)

    if policy_decision_response_placeholder_ref_id is None:
        policy_decision_response_placeholder_ref_id = (
            f"pb-polresplace-{delegation_ref_id[:12]}"
        )

    response_placeholder_hash = _compute_policy_decision_response_placeholder_ref_hash(
        policy_decision_response_placeholder_ref=placeholder_ref_clean,
        response_placeholder_description=response_placeholder_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationPolicyDecisionResponsePlaceholderRef(
        schema_version=DELEGATION_POLICY_DECISION_RESPONSE_PLACEHOLDER_REF_VERSION,
        policy_decision_response_placeholder_ref_id=(
            policy_decision_response_placeholder_ref_id
        ),
        delegation_ref_id=delegation_ref_id,
        policy_decision_response_placeholder_ref=placeholder_ref_clean,
        response_placeholder_description=response_placeholder_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        response_placeholder_hash=response_placeholder_hash,
    )


def build_delegation_custos_decision_response_placeholder_ref(
    *,
    delegation_ref_id: str,
    custos_decision_response_placeholder_ref: str | None = None,
    response_placeholder_description: str = "",
    reference_status: DelegationPolicyCustosBridgeReferenceStatus | str = DelegationPolicyCustosBridgeReferenceStatus.CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REFERENCED,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    custos_decision_response_placeholder_ref_id: str | None = None,
) -> DelegationCustosDecisionResponsePlaceholderRef:
    """Build a DelegationCustosDecisionResponsePlaceholderRef — reference-only,
    not Custos response."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_ref_status = _parse_policy_custos_bridge_reference_status(reference_status)
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)
    placeholder_ref_clean = _optional_string(custos_decision_response_placeholder_ref)

    if custos_decision_response_placeholder_ref_id is None:
        custos_decision_response_placeholder_ref_id = (
            f"pb-cusresplace-{delegation_ref_id[:12]}"
        )

    response_placeholder_hash = _compute_custos_decision_response_placeholder_ref_hash(
        custos_decision_response_placeholder_ref=placeholder_ref_clean,
        response_placeholder_description=response_placeholder_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationCustosDecisionResponsePlaceholderRef(
        schema_version=DELEGATION_CUSTOS_DECISION_RESPONSE_PLACEHOLDER_REF_VERSION,
        custos_decision_response_placeholder_ref_id=(
            custos_decision_response_placeholder_ref_id
        ),
        delegation_ref_id=delegation_ref_id,
        custos_decision_response_placeholder_ref=placeholder_ref_clean,
        response_placeholder_description=response_placeholder_description,
        reference_status=parsed_ref_status,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        response_placeholder_hash=response_placeholder_hash,
    )


def build_delegation_policy_custos_compatibility_matrix_entry(
    *,
    delegation_ref_id: str,
    family: DelegationPolicyCustosCompatibilityFamily | str = DelegationPolicyCustosCompatibilityFamily.IDENTITY_CONTEXT,
    present: bool = False,
    hash_present: bool = False,
    source_label_present: bool = False,
    finding_count: int = 0,
    unavailable_reason: str = "",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    entry_id: str | None = None,
) -> DelegationPolicyCustosCompatibilityMatrixEntry:
    """Build a DelegationPolicyCustosCompatibilityMatrixEntry — reference-only,
    not policy evaluation."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_family = _parse_compatibility_family(family)
    parsed_label = _parse_source_label(source_label)

    if entry_id is None:
        entry_id = f"pb-compentry-{delegation_ref_id[:12]}-{parsed_family.value[:8]}"

    entry_hash = _compute_compatibility_matrix_entry_hash(
        family=parsed_family,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=parsed_label,
    )

    return DelegationPolicyCustosCompatibilityMatrixEntry(
        schema_version=DELEGATION_POLICY_CUSTOS_COMPATIBILITY_MATRIX_ENTRY_VERSION,
        entry_id=entry_id,
        delegation_ref_id=delegation_ref_id,
        family=parsed_family,
        present=present,
        hash_present=hash_present,
        source_label_present=source_label_present,
        finding_count=finding_count,
        unavailable_reason=unavailable_reason,
        source_label=parsed_label,
        entry_hash=entry_hash,
    )


def build_delegation_policy_custos_compatibility_matrix(
    *,
    delegation_ref_id: str,
    entries: Sequence[DelegationPolicyCustosCompatibilityMatrixEntry] = (),
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    compatibility_matrix_id: str | None = None,
) -> DelegationPolicyCustosCompatibilityMatrix:
    """Build a DelegationPolicyCustosCompatibilityMatrix — reference-only,
    not policy evaluation."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)

    ordered_entries = tuple(sorted(entries, key=lambda e: e.entry_id))
    entry_hashes = tuple(e.entry_hash for e in ordered_entries)

    if compatibility_matrix_id is None:
        compatibility_matrix_id = f"pb-compmatrix-{delegation_ref_id[:12]}"

    matrix_hash = _compute_compatibility_matrix_hash(
        entry_hashes=entry_hashes,
        source_label=parsed_label,
    )

    return DelegationPolicyCustosCompatibilityMatrix(
        schema_version=DELEGATION_POLICY_CUSTOS_COMPATIBILITY_MATRIX_VERSION,
        compatibility_matrix_id=compatibility_matrix_id,
        delegation_ref_id=delegation_ref_id,
        entries=ordered_entries,
        source_label=parsed_label,
        matrix_hash=matrix_hash,
    )


def build_delegation_policy_custos_bridge_readiness_profile(
    *,
    delegation_ref_id: str,
    has_policy_bridge_refs: bool = False,
    has_custos_bridge_refs: bool = False,
    has_policy_context_refs: bool = False,
    has_custos_context_refs: bool = False,
    has_policy_decision_request_intent_refs: bool = False,
    has_custos_decision_request_intent_refs: bool = False,
    has_policy_decision_response_placeholders: bool = False,
    has_custos_decision_response_placeholders: bool = False,
    has_operator_review_context: bool = False,
    has_shadow_resolver_context: bool = False,
    has_authority_context: bool = False,
    has_scope_context: bool = False,
    has_evidence_context: bool = False,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_readiness_profile_id: str | None = None,
) -> DelegationPolicyCustosBridgeReadinessProfile:
    """Build a DelegationPolicyCustosBridgeReadinessProfile — reference-only,
    not decision readiness."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)

    missing: list[str] = []
    if not has_policy_bridge_refs:
        missing.append("policy_bridge_refs")
    if not has_custos_bridge_refs:
        missing.append("custos_bridge_refs")
    if not has_policy_context_refs:
        missing.append("policy_context_refs")
    if not has_custos_context_refs:
        missing.append("custos_context_refs")
    if not has_policy_decision_request_intent_refs:
        missing.append("policy_decision_request_intent_refs")
    if not has_custos_decision_request_intent_refs:
        missing.append("custos_decision_request_intent_refs")
    if not has_policy_decision_response_placeholders:
        missing.append("policy_decision_response_placeholders")
    if not has_custos_decision_response_placeholders:
        missing.append("custos_decision_response_placeholders")
    if not has_operator_review_context:
        missing.append("operator_review_context")
    if not has_shadow_resolver_context:
        missing.append("shadow_resolver_context")
    if not has_authority_context:
        missing.append("authority_context")
    if not has_scope_context:
        missing.append("scope_context")
    if not has_evidence_context:
        missing.append("evidence_context")

    missing_tuple = tuple(sorted(missing))

    if bridge_readiness_profile_id is None:
        bridge_readiness_profile_id = f"pb-readiness-{delegation_ref_id[:12]}"

    readiness_hash = _compute_bridge_readiness_profile_hash(
        has_policy_bridge_refs=has_policy_bridge_refs,
        has_custos_bridge_refs=has_custos_bridge_refs,
        has_policy_context_refs=has_policy_context_refs,
        has_custos_context_refs=has_custos_context_refs,
        has_policy_decision_request_intent_refs=has_policy_decision_request_intent_refs,
        has_custos_decision_request_intent_refs=has_custos_decision_request_intent_refs,
        has_policy_decision_response_placeholders=has_policy_decision_response_placeholders,
        has_custos_decision_response_placeholders=has_custos_decision_response_placeholders,
        has_operator_review_context=has_operator_review_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_scope_context=has_scope_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_tuple,
        source_label=parsed_label,
    )

    return DelegationPolicyCustosBridgeReadinessProfile(
        schema_version=DELEGATION_POLICY_CUSTOS_BRIDGE_READINESS_PROFILE_VERSION,
        bridge_readiness_profile_id=bridge_readiness_profile_id,
        delegation_ref_id=delegation_ref_id,
        has_policy_bridge_refs=has_policy_bridge_refs,
        has_custos_bridge_refs=has_custos_bridge_refs,
        has_policy_context_refs=has_policy_context_refs,
        has_custos_context_refs=has_custos_context_refs,
        has_policy_decision_request_intent_refs=has_policy_decision_request_intent_refs,
        has_custos_decision_request_intent_refs=has_custos_decision_request_intent_refs,
        has_policy_decision_response_placeholders=has_policy_decision_response_placeholders,
        has_custos_decision_response_placeholders=has_custos_decision_response_placeholders,
        has_operator_review_context=has_operator_review_context,
        has_shadow_resolver_context=has_shadow_resolver_context,
        has_authority_context=has_authority_context,
        has_scope_context=has_scope_context,
        has_evidence_context=has_evidence_context,
        missing_components=missing_tuple,
        policy_engine_unavailable_reason=(
            "Policy engine is not available in P1.8.12; "
            "PolicyBridgeRef is reference-only metadata, not policy evaluation"
        ),
        custos_runtime_unavailable_reason=(
            "Custos runtime is not available in P1.8.12; "
            "CustosBridgeRef is reference-only metadata, not Custos call"
        ),
        decision_engine_unavailable_reason=(
            "Decision engine is not available in P1.8.12; "
            "DecisionRequestIntentRef is reference-only intent, not decision request"
        ),
        enforcement_unavailable_reason=(
            "Enforcement engine is not available in P1.8.12; "
            "policy/Custos bridge does not enforce"
        ),
        trace_unavailable_reason=(
            "Trace writer is not available in P1.8.12; "
            "policy/Custos bridge does not write trace events"
        ),
        ledger_unavailable_reason=(
            "Ledger write is not available in P1.8.12; "
            "policy/Custos bridge is reference-only metadata"
        ),
        source_label=parsed_label,
        readiness_hash=readiness_hash,
    )


def build_delegation_policy_custos_bridge_envelope(
    *,
    delegation_ref_id: str,
    delegation_identity_hash: str = "0000000000000000000000000000000000000000",
    role_binding_hash: str = "0000000000000000000000000000000000000000",
    constraint_set_hash: str = "0000000000000000000000000000000000000000",
    authority_binding_set_hash: str = "0000000000000000000000000000000000000000",
    non_repudiation_binding_set_hash: str = "0000000000000000000000000000000000000000",
    identity_mesh_binding_set_hash: str = "0000000000000000000000000000000000000000",
    scope_binding_set_hash: str = "0000000000000000000000000000000000000000",
    lifecycle_binding_set_hash: str = "0000000000000000000000000000000000000000",
    chain_binding_set_hash: str = "0000000000000000000000000000000000000000",
    shadow_resolver_result_hash: str = "0000000000000000000000000000000000000000",
    operator_review_binding_set_hash: str = "0000000000000000000000000000000000000000",
    policy_bridge_refs: Sequence[DelegationPolicyBridgeRef] = (),
    custos_bridge_refs: Sequence[DelegationCustosBridgeRef] = (),
    policy_context_refs: Sequence[DelegationPolicyContextRef] = (),
    custos_context_refs: Sequence[DelegationCustosContextRef] = (),
    policy_decision_request_intent_refs: Sequence[DelegationPolicyDecisionRequestIntentRef] = (),
    custos_decision_request_intent_refs: Sequence[DelegationCustosDecisionRequestIntentRef] = (),
    policy_decision_response_placeholder_refs: Sequence[DelegationPolicyDecisionResponsePlaceholderRef] = (),
    custos_decision_response_placeholder_refs: Sequence[DelegationCustosDecisionResponsePlaceholderRef] = (),
    compatibility_matrix: DelegationPolicyCustosCompatibilityMatrix | None = None,
    readiness_profile: DelegationPolicyCustosBridgeReadinessProfile | None = None,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    policy_custos_bridge_envelope_id: str | None = None,
) -> DelegationPolicyCustosBridgeEnvelope:
    """Build a DelegationPolicyCustosBridgeEnvelope."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    _required_string(delegation_identity_hash, field_name="delegation_identity_hash")
    _required_string(role_binding_hash, field_name="role_binding_hash")
    _required_string(constraint_set_hash, field_name="constraint_set_hash")
    _required_string(authority_binding_set_hash, field_name="authority_binding_set_hash")
    _required_string(non_repudiation_binding_set_hash, field_name="non_repudiation_binding_set_hash")
    _required_string(identity_mesh_binding_set_hash, field_name="identity_mesh_binding_set_hash")
    _required_string(scope_binding_set_hash, field_name="scope_binding_set_hash")
    _required_string(lifecycle_binding_set_hash, field_name="lifecycle_binding_set_hash")
    _required_string(chain_binding_set_hash, field_name="chain_binding_set_hash")
    _required_string(shadow_resolver_result_hash, field_name="shadow_resolver_result_hash")
    _required_string(operator_review_binding_set_hash, field_name="operator_review_binding_set_hash")
    parsed_label = _parse_source_label(source_label)

    policy_bridge_ref_ids = tuple(sorted(
        r.policy_bridge_ref_id for r in policy_bridge_refs
    ))
    custos_bridge_ref_ids = tuple(sorted(
        r.custos_bridge_ref_id for r in custos_bridge_refs
    ))
    policy_context_ref_ids = tuple(sorted(
        r.policy_context_ref_id for r in policy_context_refs
    ))
    custos_context_ref_ids = tuple(sorted(
        r.custos_context_ref_id for r in custos_context_refs
    ))
    policy_dr_intent_ids = tuple(sorted(
        r.policy_decision_request_intent_ref_id
        for r in policy_decision_request_intent_refs
    ))
    custos_dr_intent_ids = tuple(sorted(
        r.custos_decision_request_intent_ref_id
        for r in custos_decision_request_intent_refs
    ))
    policy_dr_placeholder_ids = tuple(sorted(
        r.policy_decision_response_placeholder_ref_id
        for r in policy_decision_response_placeholder_refs
    ))
    custos_dr_placeholder_ids = tuple(sorted(
        r.custos_decision_response_placeholder_ref_id
        for r in custos_decision_response_placeholder_refs
    ))

    if compatibility_matrix is None:
        compat_hash = "0000000000000000000000000000000000000000"
    else:
        compat_hash = compatibility_matrix.matrix_hash

    if readiness_profile is None:
        bridge_readiness_hash = "0000000000000000000000000000000000000000"
    else:
        bridge_readiness_hash = readiness_profile.readiness_hash

    if policy_custos_bridge_envelope_id is None:
        policy_custos_bridge_envelope_id = (
            f"pb-envelope-{delegation_ref_id[:12]}"
        )

    envelope_hash = _compute_policy_custos_bridge_envelope_hash(
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
        policy_bridge_ref_ids=policy_bridge_ref_ids,
        custos_bridge_ref_ids=custos_bridge_ref_ids,
        policy_context_ref_ids=policy_context_ref_ids,
        custos_context_ref_ids=custos_context_ref_ids,
        policy_decision_request_intent_ref_ids=policy_dr_intent_ids,
        custos_decision_request_intent_ref_ids=custos_dr_intent_ids,
        policy_decision_response_placeholder_ref_ids=policy_dr_placeholder_ids,
        custos_decision_response_placeholder_ref_ids=custos_dr_placeholder_ids,
        compatibility_matrix_hash=compat_hash,
        bridge_readiness_hash=bridge_readiness_hash,
        source_label=parsed_label,
    )

    return DelegationPolicyCustosBridgeEnvelope(
        schema_version=DELEGATION_POLICY_CUSTOS_BRIDGE_ENVELOPE_VERSION,
        policy_custos_bridge_envelope_id=policy_custos_bridge_envelope_id,
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
        policy_bridge_ref_ids=policy_bridge_ref_ids,
        custos_bridge_ref_ids=custos_bridge_ref_ids,
        policy_context_ref_ids=policy_context_ref_ids,
        custos_context_ref_ids=custos_context_ref_ids,
        policy_decision_request_intent_ref_ids=policy_dr_intent_ids,
        custos_decision_request_intent_ref_ids=custos_dr_intent_ids,
        policy_decision_response_placeholder_ref_ids=policy_dr_placeholder_ids,
        custos_decision_response_placeholder_ref_ids=custos_dr_placeholder_ids,
        compatibility_matrix_hash=compat_hash,
        bridge_readiness_hash=bridge_readiness_hash,
        source_label=parsed_label,
        policy_custos_bridge_envelope_hash=envelope_hash,
    )


def build_delegation_policy_custos_bridge_binding(
    *,
    delegation_ref_id: str,
    envelope: DelegationPolicyCustosBridgeEnvelope,
    delegation_identity_hash: str = "0000000000000000000000000000000000000000",
    role_binding_hash: str = "0000000000000000000000000000000000000000",
    constraint_set_hash: str = "0000000000000000000000000000000000000000",
    authority_binding_set_hash: str = "0000000000000000000000000000000000000000",
    non_repudiation_binding_set_hash: str = "0000000000000000000000000000000000000000",
    identity_mesh_binding_set_hash: str = "0000000000000000000000000000000000000000",
    scope_binding_set_hash: str = "0000000000000000000000000000000000000000",
    lifecycle_binding_set_hash: str = "0000000000000000000000000000000000000000",
    chain_binding_set_hash: str = "0000000000000000000000000000000000000000",
    shadow_resolver_result_hash: str = "0000000000000000000000000000000000000000",
    operator_review_binding_set_hash: str = "0000000000000000000000000000000000000000",
    bridge_readiness_hash: str = "0000000000000000000000000000000000000000",
    compatibility_matrix_hash: str = "0000000000000000000000000000000000000000",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    bridge_status: DelegationPolicyCustosBridgeStatus | str = DelegationPolicyCustosBridgeStatus.DECLARED,
    binding_id: str | None = None,
) -> DelegationPolicyCustosBridgeBinding:
    """Build a DelegationPolicyCustosBridgeBinding."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    _required_string(delegation_identity_hash, field_name="delegation_identity_hash")
    _required_string(role_binding_hash, field_name="role_binding_hash")
    _required_string(constraint_set_hash, field_name="constraint_set_hash")
    _required_string(authority_binding_set_hash, field_name="authority_binding_set_hash")
    _required_string(non_repudiation_binding_set_hash, field_name="non_repudiation_binding_set_hash")
    _required_string(identity_mesh_binding_set_hash, field_name="identity_mesh_binding_set_hash")
    _required_string(scope_binding_set_hash, field_name="scope_binding_set_hash")
    _required_string(lifecycle_binding_set_hash, field_name="lifecycle_binding_set_hash")
    _required_string(chain_binding_set_hash, field_name="chain_binding_set_hash")
    _required_string(shadow_resolver_result_hash, field_name="shadow_resolver_result_hash")
    _required_string(operator_review_binding_set_hash, field_name="operator_review_binding_set_hash")
    _required_string(bridge_readiness_hash, field_name="bridge_readiness_hash")
    _required_string(compatibility_matrix_hash, field_name="compatibility_matrix_hash")
    parsed_label = _parse_source_label(source_label)
    parsed_bridge_status = _parse_policy_custos_bridge_status(bridge_status)

    if binding_id is None:
        binding_id = f"pb-binding-{delegation_ref_id[:12]}"

    binding_hash = _compute_policy_custos_bridge_binding_hash(
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
        policy_custos_bridge_envelope_hash=envelope.policy_custos_bridge_envelope_hash,
        bridge_readiness_hash=bridge_readiness_hash,
        compatibility_matrix_hash=compatibility_matrix_hash,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
    )

    return DelegationPolicyCustosBridgeBinding(
        schema_version=DELEGATION_POLICY_CUSTOS_BRIDGE_BINDING_VERSION,
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
        policy_custos_bridge_envelope_hash=envelope.policy_custos_bridge_envelope_hash,
        bridge_readiness_hash=bridge_readiness_hash,
        compatibility_matrix_hash=compatibility_matrix_hash,
        source_label=parsed_label,
        bridge_status=parsed_bridge_status,
        binding_hash=binding_hash,
    )


def build_delegation_policy_custos_bridge_binding_set(
    *,
    delegation_ref_id: str,
    bindings: Sequence[DelegationPolicyCustosBridgeBinding],
    delegation_identity_hash: str = "0000000000000000000000000000000000000000",
    role_binding_hash: str = "0000000000000000000000000000000000000000",
    constraint_set_hash: str = "0000000000000000000000000000000000000000",
    authority_binding_set_hash: str = "0000000000000000000000000000000000000000",
    non_repudiation_binding_set_hash: str = "0000000000000000000000000000000000000000",
    identity_mesh_binding_set_hash: str = "0000000000000000000000000000000000000000",
    scope_binding_set_hash: str = "0000000000000000000000000000000000000000",
    lifecycle_binding_set_hash: str = "0000000000000000000000000000000000000000",
    chain_binding_set_hash: str = "0000000000000000000000000000000000000000",
    shadow_resolver_result_hash: str = "0000000000000000000000000000000000000000",
    operator_review_binding_set_hash: str = "0000000000000000000000000000000000000000",
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.DEV_FIXTURE,
    policy_custos_bridge_binding_set_id: str | None = None,
) -> DelegationPolicyCustosBridgeBindingSet:
    """Build a DelegationPolicyCustosBridgeBindingSet."""
    _required_string(delegation_ref_id, field_name="delegation_ref_id")
    parsed_label = _parse_source_label(source_label)
    side_effects = DelegationPolicyCustosBridgeSideEffects()

    ordered_bindings = tuple(sorted(bindings, key=lambda b: b.binding_id))
    binding_hashes = tuple(b.binding_hash for b in ordered_bindings)

    if policy_custos_bridge_binding_set_id is None:
        policy_custos_bridge_binding_set_id = (
            f"pb-bindingset-{delegation_ref_id[:12]}"
        )

    binding_set_hash = _compute_policy_custos_bridge_binding_set_hash(
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
        binding_hashes=binding_hashes,
        source_label=parsed_label,
        side_effects=side_effects,
    )

    return DelegationPolicyCustosBridgeBindingSet(
        schema_version=DELEGATION_POLICY_CUSTOS_BRIDGE_BINDING_SET_VERSION,
        policy_custos_bridge_binding_set_id=policy_custos_bridge_binding_set_id,
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
        bindings=ordered_bindings,
        source_label=parsed_label,
        policy_custos_bridge_binding_set_hash=binding_set_hash,
        side_effects=side_effects,
    )


def build_delegation_policy_custos_bridge_status_report(
    *,
    source_label: DelegationSourceLabel | str = DelegationSourceLabel.LIVE,
) -> DelegationPolicyCustosBridgeStatusReport:
    """Build a DelegationPolicyCustosBridgeStatusReport."""
    _parse_source_label(source_label)
    side_effects = DelegationPolicyCustosBridgeSideEffects()

    available = (
        "DelegationPolicyBridgeRef",
        "DelegationCustosBridgeRef",
        "DelegationPolicyContextRef",
        "DelegationCustosContextRef",
        "DelegationPolicyDecisionRequestIntentRef",
        "DelegationCustosDecisionRequestIntentRef",
        "DelegationPolicyDecisionResponsePlaceholderRef",
        "DelegationCustosDecisionResponsePlaceholderRef",
        "DelegationPolicyCustosCompatibilityMatrixEntry",
        "DelegationPolicyCustosCompatibilityMatrix",
        "DelegationPolicyCustosBridgeReadinessProfile",
        "DelegationPolicyCustosBridgeEnvelope",
        "DelegationPolicyCustosBridgeBinding",
        "DelegationPolicyCustosBridgeBindingSet",
        "DelegationPolicyCustosBridgeSideEffects",
        "DelegationPolicyCustosBridgeStatusReport",
    )

    status_hash = _compute_policy_custos_bridge_status_report_hash(
        available_contracts=available,
        side_effects=side_effects,
    )

    return DelegationPolicyCustosBridgeStatusReport(
        schema_version=DELEGATION_POLICY_CUSTOS_BRIDGE_STATUS_REPORT_VERSION,
        status_label="Delegation Policy/Custos BridgeRef Model — Reference Only",
        available_contracts=available,
        unavailable_bindings=dict(DELEGATION_POLICY_CUSTOS_BRIDGE_UNAVAILABLE_BINDINGS),
        side_effects=side_effects,
        status_hash=status_hash,
    )


# ---------------------------------------------------------------------------
# Serialize helpers
# ---------------------------------------------------------------------------


def serialize_delegation_policy_custos_bridge_envelope(
    envelope: DelegationPolicyCustosBridgeEnvelope,
) -> str:
    """Serialize a DelegationPolicyCustosBridgeEnvelope to deterministic JSON."""
    return to_canonical_json(envelope)


def serialize_delegation_policy_custos_bridge_binding_set(
    binding_set: DelegationPolicyCustosBridgeBindingSet,
) -> str:
    """Serialize a DelegationPolicyCustosBridgeBindingSet to deterministic JSON."""
    return to_canonical_json(binding_set)


# ---------------------------------------------------------------------------
# Convenience hash wrappers
# ---------------------------------------------------------------------------


def hash_delegation_policy_bridge_ref(
    ref: DelegationPolicyBridgeRef,
) -> str:
    """Return the precomputed policy_bridge_hash."""
    return ref.policy_bridge_hash


def hash_delegation_custos_bridge_ref(
    ref: DelegationCustosBridgeRef,
) -> str:
    """Return the precomputed custos_bridge_hash."""
    return ref.custos_bridge_hash


def hash_delegation_policy_context_ref(
    ref: DelegationPolicyContextRef,
) -> str:
    """Return the precomputed policy_context_hash."""
    return ref.policy_context_hash


def hash_delegation_custos_context_ref(
    ref: DelegationCustosContextRef,
) -> str:
    """Return the precomputed custos_context_hash."""
    return ref.custos_context_hash


def hash_delegation_policy_decision_request_intent_ref(
    ref: DelegationPolicyDecisionRequestIntentRef,
) -> str:
    """Return the precomputed request_intent_hash."""
    return ref.request_intent_hash


def hash_delegation_custos_decision_request_intent_ref(
    ref: DelegationCustosDecisionRequestIntentRef,
) -> str:
    """Return the precomputed request_intent_hash."""
    return ref.request_intent_hash


def hash_delegation_policy_decision_response_placeholder_ref(
    ref: DelegationPolicyDecisionResponsePlaceholderRef,
) -> str:
    """Return the precomputed response_placeholder_hash."""
    return ref.response_placeholder_hash


def hash_delegation_custos_decision_response_placeholder_ref(
    ref: DelegationCustosDecisionResponsePlaceholderRef,
) -> str:
    """Return the precomputed response_placeholder_hash."""
    return ref.response_placeholder_hash


def hash_delegation_policy_custos_compatibility_matrix_entry(
    entry: DelegationPolicyCustosCompatibilityMatrixEntry,
) -> str:
    """Return the precomputed entry_hash."""
    return entry.entry_hash


def hash_delegation_policy_custos_compatibility_matrix(
    matrix: DelegationPolicyCustosCompatibilityMatrix,
) -> str:
    """Return the precomputed matrix_hash."""
    return matrix.matrix_hash


def hash_delegation_policy_custos_bridge_readiness_profile(
    profile: DelegationPolicyCustosBridgeReadinessProfile,
) -> str:
    """Return the precomputed readiness_hash."""
    return profile.readiness_hash


def hash_delegation_policy_custos_bridge_envelope(
    envelope: DelegationPolicyCustosBridgeEnvelope,
) -> str:
    """Return the precomputed policy_custos_bridge_envelope_hash."""
    return envelope.policy_custos_bridge_envelope_hash


def hash_delegation_policy_custos_bridge_binding(
    binding: DelegationPolicyCustosBridgeBinding,
) -> str:
    """Return the precomputed binding_hash."""
    return binding.binding_hash


def hash_delegation_policy_custos_bridge_binding_set(
    binding_set: DelegationPolicyCustosBridgeBindingSet,
) -> str:
    """Return the precomputed policy_custos_bridge_binding_set_hash."""
    return binding_set.policy_custos_bridge_binding_set_hash


def hash_delegation_policy_custos_bridge_status_report(
    report: DelegationPolicyCustosBridgeStatusReport,
) -> str:
    """Return the precomputed status_hash."""
    return report.status_hash
