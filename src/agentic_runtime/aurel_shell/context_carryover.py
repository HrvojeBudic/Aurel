"""AurelShell cross-surface context carryover contract (P2.0-C / P2.0.17).

Contract-only bounded context capsules for cross-surface continuity.
Context carryover is not memory write, runtime mutation, or authority transfer.

Architectural law:
  - Context carryover is not memory write.
  - Context carryover is not runtime mutation.
  - Context carryover is not authority transfer.
  - TraceRef is not TRACE_VERIFIED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
)
from .surface_registry import (
    AurelSurfaceKind,
    SURFACE_KIND_IDS,
)

AUREL_CONTEXT_CARRYOVER_CONTRACT_VERSION = "aurel_context_carryover_contract.v1"
AUREL_CONTEXT_CARRYOVER_PAYLOAD_VERSION = "aurel_context_carryover_payload.v1"

DEV_FIXTURE_CONTEXT_ID = "dev_fixture_context_carryover_001"


class ContextCarryoverTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    CONTEXT_CARRYOVER_CONTRACT_ONLY = "CONTEXT_CARRYOVER_CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    UNAVAILABLE = "UNAVAILABLE"


class ContextCarryoverScope(str, Enum):
    """Scope boundary for context carryover."""

    SURFACE_TRANSITION = "surface_transition"
    VIEW_CONTINUITY = "view_continuity"
    SELECTION_CONTINUITY = "selection_continuity"
    DEV_FIXTURE = "dev_fixture"


class ContextReferenceKind(str, Enum):
    """Reference types carried in context payloads — references only."""

    OBJECT_REF = "object_ref"
    DATA_REF = "data_ref"
    ARTIFACT_REF = "artifact_ref"
    TRACE_REF = "trace_ref"
    CONTEXT_REF = "context_ref"


class ContextCarryoverAvailability(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


_CONTEXT_NON_GOALS: tuple[str, ...] = (
    "no_memory_write",
    "no_mneme_integration",
    "no_trace_write",
    "no_trace_verification",
    "no_runtime_session_mutation",
    "no_authority_transfer",
)


@dataclass(frozen=True)
class ContextReference(_CanonicalMixin):
    """Scoped reference in a context carryover payload."""

    ref_kind: ContextReferenceKind
    ref_id: str
    description: str
    is_permission: bool = False
    is_memory_write: bool = False
    is_trace_verified: bool = False


@dataclass(frozen=True)
class ContextCarryoverBoundary(_CanonicalMixin):
    """Boundary constraints for context carryover."""

    writes_memory: bool
    mutates_runtime: bool
    grants_authority: bool
    writes_trace: bool
    is_trace_verified: bool
    has_scope: bool
    has_expiry_or_boundary: bool
    expiry_or_boundary_label: str


@dataclass(frozen=True)
class ContextCarryoverPayload(_CanonicalMixin):
    """Bounded context carryover payload."""

    schema_version: str
    context_id: str
    source_surface_id: str
    target_surface_id: str
    source_surface_kind: AurelSurfaceKind
    target_surface_kind: AurelSurfaceKind
    scope: ContextCarryoverScope
    payload_refs: tuple[ContextReference, ...]
    operator_intent: str
    selection_context: str
    view_context: str
    truth_label: ContextCarryoverTruthLabel
    availability: ContextCarryoverAvailability
    boundary: ContextCarryoverBoundary
    is_dev_fixture: bool
    non_goals: tuple[str, ...]
    payload_hash: str


@dataclass(frozen=True)
class CrossSurfaceContextCarryoverContract(_CanonicalMixin):
    """P2.0.17 — cross-surface context carryover contract container."""

    schema_version: str
    dev_fixture_payload: ContextCarryoverPayload
    truth_label: ContextCarryoverTruthLabel
    unavailable_reason: str
    non_goals: tuple[str, ...]
    contract_hash: str


def _default_context_boundary() -> ContextCarryoverBoundary:
    return ContextCarryoverBoundary(
        writes_memory=False,
        mutates_runtime=False,
        grants_authority=False,
        writes_trace=False,
        is_trace_verified=False,
        has_scope=True,
        has_expiry_or_boundary=True,
        expiry_or_boundary_label="contract_only_no_persistence",
    )


def build_context_carryover_payload(
    *,
    context_id: str = DEV_FIXTURE_CONTEXT_ID,
    source_kind: AurelSurfaceKind = AurelSurfaceKind.AUREL_CRO,
    target_kind: AurelSurfaceKind = AurelSurfaceKind.HQ,
    scope: ContextCarryoverScope = ContextCarryoverScope.DEV_FIXTURE,
    is_dev_fixture: bool = True,
) -> ContextCarryoverPayload:
    refs = (
        ContextReference(
            ref_kind=ContextReferenceKind.OBJECT_REF,
            ref_id="dev_fixture:object_ref_001",
            description="ObjectRef-like reference — not permission",
        ),
        ContextReference(
            ref_kind=ContextReferenceKind.DATA_REF,
            ref_id="dev_fixture:data_ref_001",
            description="DataRef-like reference",
        ),
        ContextReference(
            ref_kind=ContextReferenceKind.ARTIFACT_REF,
            ref_id="dev_fixture:artifact_ref_001",
            description="ArtifactRef-like reference",
        ),
        ContextReference(
            ref_kind=ContextReferenceKind.TRACE_REF,
            ref_id="dev_fixture:trace_ref_001",
            description="TraceRef-like reference — not TRACE_VERIFIED",
        ),
        ContextReference(
            ref_kind=ContextReferenceKind.CONTEXT_REF,
            ref_id="dev_fixture:context_ref_001",
            description="ContextRef-like reference — not memory write",
        ),
    )
    truth = (
        ContextCarryoverTruthLabel.DEV_FIXTURE
        if is_dev_fixture
        else ContextCarryoverTruthLabel.CONTEXT_CARRYOVER_CONTRACT_ONLY
    )
    payload = {
        "schema_version": AUREL_CONTEXT_CARRYOVER_PAYLOAD_VERSION,
        "context_id": context_id,
        "source_surface_id": SURFACE_KIND_IDS[source_kind],
        "target_surface_id": SURFACE_KIND_IDS[target_kind],
        "source_surface_kind": source_kind,
        "target_surface_kind": target_kind,
        "scope": scope,
        "payload_refs": refs,
        "operator_intent": "operator_carry_bounded_context",
        "selection_context": "dev_fixture_selection_context",
        "view_context": "dev_fixture_view_context",
        "truth_label": truth,
        "availability": ContextCarryoverAvailability.CONTRACT_ONLY,
        "boundary": _default_context_boundary(),
        "is_dev_fixture": is_dev_fixture,
        "non_goals": _CONTEXT_NON_GOALS,
    }
    return ContextCarryoverPayload(**payload, payload_hash=_hash_payload(payload))


def build_context_carryover_contract() -> CrossSurfaceContextCarryoverContract:
    dev_payload = build_context_carryover_payload()
    payload = {
        "schema_version": AUREL_CONTEXT_CARRYOVER_CONTRACT_VERSION,
        "dev_fixture_payload": dev_payload,
        "truth_label": ContextCarryoverTruthLabel.CONTEXT_CARRYOVER_CONTRACT_ONLY,
        "unavailable_reason": "context_carryover_contract_only_no_memory_or_trace",
        "non_goals": _CONTEXT_NON_GOALS,
    }
    return CrossSurfaceContextCarryoverContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )


def assert_context_carryover_does_not_write_memory(
    payload: ContextCarryoverPayload,
) -> None:
    if payload.boundary.writes_memory:
        _reject(
            "context carryover must not write memory",
            field="boundary.writes_memory",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    for ref in payload.payload_refs:
        if ref.is_memory_write:
            _reject(
                f"reference {ref.ref_id} must not be memory write",
                field="payload_refs",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_context_carryover_does_not_mutate_runtime(
    payload: ContextCarryoverPayload,
) -> None:
    if payload.boundary.mutates_runtime:
        _reject(
            "context carryover must not mutate runtime",
            field="boundary.mutates_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_carryover_does_not_grant_authority(
    payload: ContextCarryoverPayload,
) -> None:
    if payload.boundary.grants_authority:
        _reject(
            "context carryover must not grant authority",
            field="boundary.grants_authority",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_context_carryover_has_scope_boundary(
    payload: ContextCarryoverPayload,
) -> None:
    boundary = payload.boundary
    if not boundary.has_scope:
        _reject(
            "context carryover must have scope",
            field="boundary.has_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not boundary.has_expiry_or_boundary:
        _reject(
            "context carryover must have expiry or boundary",
            field="boundary.has_expiry_or_boundary",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_traceref_is_not_trace_verified(ref: ContextReference) -> None:
    if ref.ref_kind == ContextReferenceKind.TRACE_REF and ref.is_trace_verified:
        _reject(
            "TraceRef must not be TRACE_VERIFIED",
            field="is_trace_verified",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_objectref_is_not_permission(ref: ContextReference) -> None:
    if ref.ref_kind == ContextReferenceKind.OBJECT_REF and ref.is_permission:
        _reject(
            "ObjectRef must not be permission",
            field="is_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_contextref_is_not_memory_write(ref: ContextReference) -> None:
    if ref.ref_kind == ContextReferenceKind.CONTEXT_REF and ref.is_memory_write:
        _reject(
            "ContextRef must not be memory write",
            field="is_memory_write",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
