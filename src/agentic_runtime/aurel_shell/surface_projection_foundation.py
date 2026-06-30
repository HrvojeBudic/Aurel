"""P2.6-A surface projection / API / event bridge foundation contracts.

Contract-only bridge foundation over the sealed P2.5-D cross-surface handoff
section evidence. This module defines the *contracts* for surface projection,
API exposure, and event bridging — not the live bridge.

Core law:
  - Projection is not UI and is not source-of-truth.
  - API contract is not an API server; endpoint schema is not a route handler.
  - Event envelope is not an event bus; event stream descriptor is not a live
    runtime stream.
  - Bridge availability is not permission enforcement.
  - P2.6-A foundation result is not a live bridge.

It does not create projection UI, API server, HTTP routes, route handlers,
websocket/SSE runtime, event bus, event dispatch, runtime bridge, runtime
dispatch, surface switching, route/command execution, CLI/Shell/TUI binding,
approval activation, authorization, permission enforcement, Custos/Mneme
integration, memory/trace/storage writes, runtime mutation, source-of-truth
store, product behavior, release scope, LIVE, TRACE_VERIFIED, P2.6-B, P2.7,
P2.10, or P2.13.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .cross_surface_handoff_section_projection import (
    P2_5_D_OFFICIAL_SECTION_NAME,
    P2_5_D_PACK_ID,
    P2_5_D_REPORT_PATH,
    P25DHandoffSectionResult,
    build_p2_5_d_handoff_section_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_6_A_PACK_ID = "P2.6-A"
P2_6_A_SECTION_ID = "P2.6"
P2_6_A_OFFICIAL_SECTION_NAME = "Surface Projection / API / Event Bridge"
P2_6_A_DEPENDENCY_PACK = P2_5_D_PACK_ID
P2_6_A_NEXT_PACK = "P2.6-B"
P2_6_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.6.0",
    "P2.6.1",
    "P2.6.2",
    "P2.6.3",
    "P2.6.4",
    "P2.6.5",
)
P2_6_A_REPORT_FILENAME = "P2_6_A_SURFACE_PROJECTION_API_EVENT_FOUNDATION.md"
P2_6_A_REPORT_PATH = f"agent/reports/{P2_6_A_REPORT_FILENAME}"

# P2.5-D section seal implementation commit (recorded in the P2.5-D report).
P2_5_D_COMMIT_REF = "e27959012b71cd15d5be896dd5aa75e87ee00467"
P2_5_D_REPORT_HASH_COMMIT_REF = "4565798"

# Official active P2 surface display names (the seven-surface lock).
OFFICIAL_ACTIVE_SURFACE_NAMES: tuple[str, ...] = (
    "Aurel CRO",
    "HQ",
    "CORP",
    "HUB",
    "IDE",
    "SYSTEM",
    "Settings",
)

SURFACE_PROJECTION_NO_SERVER_REASON = (
    "P2.6-A defines API exposure as contract/schema only. No live API server, "
    "HTTP route, route handler, runtime handler, or external access exists in "
    "this repo scope. Live API serving is deferred to later P2.6/P2.7 work."
)
SURFACE_PROJECTION_NO_EVENT_BUS_REASON = (
    "P2.6-A defines event envelope and event stream as contracts/descriptors "
    "only. No event bus, event dispatch, websocket/SSE runtime, runtime bridge, "
    "or runtime dispatch exists in this repo scope. Live event bridging is "
    "deferred to later P2.6/P2.7 work."
)
SURFACE_PROJECTION_BINDING_UNAVAILABLE_REASON = (
    "P2.6-A is a projection/API/event bridge contract foundation only. No live "
    "API server, event bus, runtime bridge, or CLI/Shell/TUI binding exists in "
    "this repo scope."
)

P2_6_A_GATE_VERSION = "p2_6_a_surface_projection_gate.v1"
P2_6_A_IDENTITY_VERSION = "p2_6_a_surface_projection_identity.v1"
P2_6_A_SCOPE_VERSION = "p2_6_a_surface_projection_scope.v1"
P2_6_A_API_EXPOSURE_VERSION = "p2_6_a_surface_projection_api_exposure.v1"
P2_6_A_NO_SERVER_BOUNDARY_VERSION = "p2_6_a_surface_projection_no_server_boundary.v1"
P2_6_A_EVENT_ENVELOPE_VERSION = "p2_6_a_surface_projection_event_envelope.v1"
P2_6_A_EVENT_STREAM_VERSION = "p2_6_a_surface_projection_event_stream_descriptor.v1"
P2_6_A_NO_EVENT_BUS_BOUNDARY_VERSION = "p2_6_a_surface_projection_no_event_bus_boundary.v1"
P2_6_A_AVAILABILITY_VERSION = "p2_6_a_surface_projection_availability.v1"
P2_6_A_FOUNDATION_RESULT_VERSION = "p2_6_a_surface_projection_foundation_result.v1"
P2_6_A_RESULT_VERSION = "p2_6_a_surface_projection_result.v1"

# Exposed (contract-only) API schema labels.
P2_6_A_API_SCHEMA_NAME = "aurel_shell_surface_projection_read_model"
P2_6_A_API_SCHEMA_VERSION = "surface_projection.read_model.v1"
P2_6_A_EVENT_SCHEMA_VERSION = "surface_projection.event.v1"
P2_6_A_EVENT_STREAM_NAME = "aurel_shell_surface_projection_event_stream"
P2_6_A_EVENT_STREAM_VERSION_LABEL = "surface_projection.event_stream.v1"

# Capabilities that remain explicitly UNAVAILABLE at P2.6-A foundation scope.
SURFACE_PROJECTION_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "live API server",
    "HTTP routes",
    "route handlers",
    "websocket stream",
    "SSE stream",
    "event bus",
    "event dispatch",
    "runtime bridge",
    "runtime dispatch",
    "surface switching",
    "route execution",
    "command execution",
    "workflow/tool dispatch",
    "CLI binding",
    "Shell execution binding",
    "TUI binding",
    "approval activation",
    "authorization",
    "permission enforcement",
    "Custos integration",
    "Mneme integration",
    "trace write",
    "memory write",
    "storage write",
    "runtime mutation",
    "source-of-truth store",
    "LIVE projection",
    "TRACE_VERIFIED projection",
    "product behavior",
    "release scope",
    "P2.6-B implementation",
    "P2.7 binding",
    "P2.10 multi-client behavior",
    "P2.13 operator-testable product behavior",
)


class SurfaceProjectionGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class SurfaceProjectionKind(str, Enum):
    SURFACE_STATE_READ_MODEL = "SURFACE_STATE_READ_MODEL"
    SURFACE_REGISTRY_READ_MODEL = "SURFACE_REGISTRY_READ_MODEL"
    LOCAL_NAVIGATION_READ_MODEL = "LOCAL_NAVIGATION_READ_MODEL"
    WINDOW_STATE_READ_MODEL = "WINDOW_STATE_READ_MODEL"
    COMMAND_READ_MODEL = "COMMAND_READ_MODEL"
    HANDOFF_READ_MODEL = "HANDOFF_READ_MODEL"
    SECTION_SEAL_READ_MODEL = "SECTION_SEAL_READ_MODEL"
    DEV_FIXTURE_PROJECTION = "DEV_FIXTURE_PROJECTION"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class SurfaceProjectionApiExposureMode(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_SCHEMA_ONLY = "READ_MODEL_SCHEMA_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXPOSED = "NOT_EXPOSED"


class SurfaceProjectionEventKind(str, Enum):
    SURFACE_STATE_CHANGED_CONTRACT = "SURFACE_STATE_CHANGED_CONTRACT"
    SURFACE_REGISTRY_CHANGED_CONTRACT = "SURFACE_REGISTRY_CHANGED_CONTRACT"
    LOCAL_NAVIGATION_CHANGED_CONTRACT = "LOCAL_NAVIGATION_CHANGED_CONTRACT"
    WINDOW_STATE_CHANGED_CONTRACT = "WINDOW_STATE_CHANGED_CONTRACT"
    COMMAND_STATE_CHANGED_CONTRACT = "COMMAND_STATE_CHANGED_CONTRACT"
    HANDOFF_STATE_CHANGED_CONTRACT = "HANDOFF_STATE_CHANGED_CONTRACT"
    SECTION_SEALED_CONTRACT = "SECTION_SEALED_CONTRACT"
    DEV_FIXTURE_EVENT = "DEV_FIXTURE_EVENT"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class SurfaceProjectionAvailabilityStatus(str, Enum):
    AVAILABLE_CONTRACT_ONLY = "AVAILABLE_CONTRACT_ONLY"
    AVAILABLE_READ_MODEL_ONLY = "AVAILABLE_READ_MODEL_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class SurfaceProjectionTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    API_SCHEMA_ONLY = "API_SCHEMA_ONLY"
    EVENT_ENVELOPE_ONLY = "EVENT_ENVELOPE_ONLY"
    EVENT_STREAM_DESCRIPTOR_ONLY = "EVENT_STREAM_DESCRIPTOR_ONLY"
    NO_SERVER_BOUNDARY = "NO_SERVER_BOUNDARY"
    NO_EVENT_BUS_BOUNDARY = "NO_EVENT_BUS_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    NO_LIVE_BRIDGE_BOUNDARY = "NO_LIVE_BRIDGE_BOUNDARY"
    SECTION_GATE_ONLY = "SECTION_GATE_ONLY"
    PROJECTION_IDENTITY_ONLY = "PROJECTION_IDENTITY_ONLY"
    SURFACE_SCOPE_ONLY = "SURFACE_SCOPE_ONLY"
    AVAILABILITY_READ_MODEL_ONLY = "AVAILABILITY_READ_MODEL_ONLY"
    UNAVAILABLE_STATE_CONTRACT = "UNAVAILABLE_STATE_CONTRACT"
    FOUNDATION_RESULT_ONLY = "FOUNDATION_RESULT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_UI = "NOT_UI"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_API_SERVER = "NOT_API_SERVER"
    NOT_HTTP_ROUTE = "NOT_HTTP_ROUTE"
    NOT_ROUTE_HANDLER = "NOT_ROUTE_HANDLER"
    NOT_EXTERNAL_ACCESS = "NOT_EXTERNAL_ACCESS"
    NOT_RUNTIME_HANDLER = "NOT_RUNTIME_HANDLER"
    NOT_WEBSOCKET = "NOT_WEBSOCKET"
    NOT_SSE = "NOT_SSE"
    NOT_EVENT_BUS = "NOT_EVENT_BUS"
    NOT_EVENT_DISPATCH = "NOT_EVENT_DISPATCH"
    NOT_RUNTIME_BRIDGE = "NOT_RUNTIME_BRIDGE"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_WORKFLOW_DISPATCH = "NOT_WORKFLOW_DISPATCH"
    NOT_TOOL_INVOCATION = "NOT_TOOL_INVOCATION"
    NOT_CLI_BINDING = "NOT_CLI_BINDING"
    NOT_SHELL_EXECUTION_BINDING = "NOT_SHELL_EXECUTION_BINDING"
    NOT_TUI_BINDING = "NOT_TUI_BINDING"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class P26ASideEffectProof(_CanonicalMixin):
    projection_ui_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    route_handler_created: bool = False
    websocket_stream_created: bool = False
    sse_stream_created: bool = False
    event_bus_created: bool = False
    event_dispatch_created: bool = False
    runtime_bridge_created: bool = False
    runtime_dispatch_created: bool = False
    runtime_events_emitted: bool = False
    surface_switch_created: bool = False
    navigation_mutation_created: bool = False
    route_execution_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    workflow_dispatch_created: bool = False
    tool_invocation_created: bool = False
    cli_binding_created: bool = False
    shell_execution_binding_created: bool = False
    tui_binding_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    authorization_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    custos_integration_created: bool = False
    mneme_integration_created: bool = False
    memory_written: bool = False
    trace_written: bool = False
    storage_written: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_6_b_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class SurfaceProjectionGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_section_seal_ref: str
    dependency_readiness_audit_ref: str
    dependency_contract_scope_demo_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: SurfaceProjectionGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfaceProjectionIdentity(_CanonicalMixin):
    projection_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    projection_name: str
    projection_kind: SurfaceProjectionKind
    projection_version: str
    source_pack_ref: str
    source_section_ref: str
    is_ui: bool
    is_source_of_truth: bool
    claims_live: bool
    claims_trace_verified: bool
    truth_label: str
    limitations: tuple[str, ...]
    identity_hash: str


@dataclass(frozen=True)
class SurfaceProjectionScope(_CanonicalMixin):
    scope_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    surface_ids: tuple[str, ...]
    official_surface_set: tuple[str, ...]
    source_surface_ref: str
    target_surface_ref: str
    cross_surface_allowed_as_contract: bool
    switches_surface: bool
    executes_route: bool
    mutates_navigation: bool
    truth_label: str
    limitations: tuple[str, ...]
    scope_hash: str


@dataclass(frozen=True)
class SurfaceProjectionApiExposure(_CanonicalMixin):
    api_exposure_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    exposure_mode: SurfaceProjectionApiExposureMode
    schema_name: str
    api_schema_version: str
    endpoint_schema_ref: str
    read_model_shape: tuple[str, ...]
    external_access_enabled: bool
    http_server_created: bool
    http_routes_created: bool
    route_handler_created: bool
    runtime_handler_created: bool
    truth_label: str
    limitations: tuple[str, ...]
    exposure_hash: str


@dataclass(frozen=True)
class SurfaceProjectionNoServerBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    boundary_active: bool
    api_exposure_ref: str
    prevents_api_server: bool
    prevents_http_routes: bool
    prevents_route_handlers: bool
    prevents_external_access: bool
    prevents_runtime_handler: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventEnvelope(_CanonicalMixin):
    event_envelope_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    event_kind: SurfaceProjectionEventKind
    event_schema_version: str
    source_projection_ref: str
    source_surface_id: str
    payload_schema_ref: str
    causal_ref: str
    trace_ref: str
    is_runtime_event: bool
    emits_runtime_event: bool
    writes_trace: bool
    truth_label: str
    limitations: tuple[str, ...]
    envelope_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventStreamDescriptor(_CanonicalMixin):
    stream_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    event_envelope_refs: tuple[str, ...]
    stream_name: str
    stream_version: str
    is_live_stream: bool
    websocket_created: bool
    sse_created: bool
    subscriber_created: bool
    dispatcher_created: bool
    runtime_bridge_created: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class SurfaceProjectionNoEventBusBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    boundary_active: bool
    event_envelope_ref: str
    stream_descriptor_ref: str
    prevents_event_bus: bool
    prevents_event_dispatch: bool
    prevents_live_stream: bool
    prevents_websocket: bool
    prevents_sse: bool
    prevents_runtime_bridge: bool
    prevents_runtime_dispatch: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SurfaceProjectionAvailability(_CanonicalMixin):
    availability_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    availability_status: SurfaceProjectionAvailabilityStatus
    available_contracts: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    blocked_capabilities: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    future_pack_refs: tuple[str, ...]
    grants_permission: bool
    denies_permission: bool
    activates_approval: bool
    enforces_policy: bool
    truth_label: str
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class SurfaceProjectionFoundationResult(_CanonicalMixin):
    foundation_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    projection_identity: SurfaceProjectionIdentity
    projection_scope: SurfaceProjectionScope
    api_exposure: SurfaceProjectionApiExposure
    no_server_boundary: SurfaceProjectionNoServerBoundary
    event_envelope: SurfaceProjectionEventEnvelope
    event_stream_descriptor: SurfaceProjectionEventStreamDescriptor
    no_event_bus_boundary: SurfaceProjectionNoEventBusBoundary
    availability: SurfaceProjectionAvailability
    no_live_bridge_boundary_active: bool
    is_live_bridge: bool
    creates_api_server: bool
    creates_event_bus: bool
    creates_runtime_dispatch: bool
    creates_cli_binding: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    foundation_result_hash: str


@dataclass(frozen=True)
class P26ASurfaceProjectionResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    projection_gate: SurfaceProjectionGate
    projection_identity: SurfaceProjectionIdentity
    projection_scope: SurfaceProjectionScope
    api_exposure: SurfaceProjectionApiExposure
    no_server_boundary: SurfaceProjectionNoServerBoundary
    event_envelope: SurfaceProjectionEventEnvelope
    event_stream_descriptor: SurfaceProjectionEventStreamDescriptor
    no_event_bus_boundary: SurfaceProjectionNoEventBusBoundary
    availability: SurfaceProjectionAvailability
    foundation_result: SurfaceProjectionFoundationResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P26ASideEffectProof
    canonical_surface_ids: tuple[str, ...]
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


# ---------------------------------------------------------------------------
# Dependency reference helpers
# ---------------------------------------------------------------------------


def _section_seal_ref(result: P25DHandoffSectionResult) -> str:
    seal = result.section_seal
    return f"{seal.seal_id}:{seal.seal_status.value}"


def _readiness_audit_ref(result: P25DHandoffSectionResult) -> str:
    audit = result.readiness_audit
    return (
        f"{audit.audit_id}:contract_scope="
        f"{str(audit.audit_passed_for_contract_scope).lower()}"
    )


def _contract_scope_demo_ref(result: P25DHandoffSectionResult) -> str:
    return f"{result.contract_scope_demo.demo_id}:{result.contract_scope_demo.demo_name}"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_surface_projection_gate(
    section_result: P25DHandoffSectionResult | None = None,
) -> SurfaceProjectionGate:
    """P2.6.0 — surface projection section intake / gate over P2.5-D evidence."""
    if section_result is None:
        section_result = build_p2_5_d_handoff_section_result()
    assert_p2_5_d_section_seal_available(section_result)
    payload: dict[str, Any] = {
        "gate_id": "p2_6_a_surface_projection_gate",
        "schema_version": P2_6_A_GATE_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "official_section_name": P2_6_A_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_6_A_DEPENDENCY_PACK,
        "dependency_report_ref": P2_5_D_REPORT_PATH,
        "dependency_commit_ref": P2_5_D_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.5-D",
        "dependency_section_seal_ref": _section_seal_ref(section_result),
        "dependency_readiness_audit_ref": _readiness_audit_ref(section_result),
        "dependency_contract_scope_demo_ref": _contract_scope_demo_ref(section_result),
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": SurfaceProjectionGateStatus.READY,
        "truth_label": SurfaceProjectionTruthBoundary.SECTION_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence is ignored only by explicit operator instruction",
            "repo evidence gate over P2.5-D section seal remains required",
            "gate does not create projection UI, API server, or event bridge",
        ),
    }
    gate = SurfaceProjectionGate(**payload, gate_hash=_hash_payload(payload))
    assert_section_gate_depends_on_p2_5_d(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_surface_projection_identity() -> SurfaceProjectionIdentity:
    """P2.6.1 — projection identity read model (not UI, not source-of-truth)."""
    payload: dict[str, Any] = {
        "projection_id": "p2_6_a_surface_projection_identity",
        "schema_version": P2_6_A_IDENTITY_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "official_section_name": P2_6_A_OFFICIAL_SECTION_NAME,
        "projection_name": "aurel_shell_surface_projection",
        "projection_kind": SurfaceProjectionKind.SURFACE_STATE_READ_MODEL,
        "projection_version": "surface_projection.identity.v1",
        "source_pack_ref": P2_5_D_PACK_ID,
        "source_section_ref": P2_5_D_OFFICIAL_SECTION_NAME,
        "is_ui": False,
        "is_source_of_truth": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "truth_label": SurfaceProjectionTruthBoundary.PROJECTION_IDENTITY_ONLY.value,
        "limitations": (
            "Projection is a versioned read model over governed surface state",
            "projection does not own or mutate the real surface state",
            "projection is not UI and is not source-of-truth",
        ),
    }
    identity = SurfaceProjectionIdentity(
        **payload,
        identity_hash=_hash_payload(payload),
    )
    assert_projection_is_not_ui(identity)
    assert_projection_is_not_source_of_truth(identity)
    return identity


def build_surface_projection_scope() -> SurfaceProjectionScope:
    """P2.6.1 — official surface scope (does not switch surfaces or routes)."""
    payload: dict[str, Any] = {
        "scope_id": "p2_6_a_surface_projection_scope",
        "schema_version": P2_6_A_SCOPE_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "surface_ids": CANONICAL_SURFACE_ORDER,
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "source_surface_ref": CANONICAL_SURFACE_ORDER[0],
        "target_surface_ref": CANONICAL_SURFACE_ORDER[1],
        "cross_surface_allowed_as_contract": True,
        "switches_surface": False,
        "executes_route": False,
        "mutates_navigation": False,
        "truth_label": SurfaceProjectionTruthBoundary.SURFACE_SCOPE_ONLY.value,
        "limitations": (
            "Surface scope uses the official active P2 seven-surface set",
            "old surface taxonomy is not activated as P2.6-A canon",
            "scope does not switch surfaces, execute routes, or mutate navigation",
        ),
    }
    scope = SurfaceProjectionScope(**payload, scope_hash=_hash_payload(payload))
    assert_surface_scope_uses_official_surfaces(scope)
    return scope


def build_surface_projection_api_exposure() -> SurfaceProjectionApiExposure:
    """P2.6.2 — API exposure as contract/schema only (no server)."""
    payload: dict[str, Any] = {
        "api_exposure_id": "p2_6_a_surface_projection_api_exposure",
        "schema_version": P2_6_A_API_EXPOSURE_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "exposure_mode": SurfaceProjectionApiExposureMode.READ_MODEL_SCHEMA_ONLY,
        "schema_name": P2_6_A_API_SCHEMA_NAME,
        "api_schema_version": P2_6_A_API_SCHEMA_VERSION,
        "endpoint_schema_ref": "surface_projection/read_model:GET(contract-only)",
        "read_model_shape": (
            "surface_id",
            "projection_kind",
            "projection_version",
            "availability_status",
            "truth_label",
        ),
        "external_access_enabled": False,
        "http_server_created": False,
        "http_routes_created": False,
        "route_handler_created": False,
        "runtime_handler_created": False,
        "truth_label": SurfaceProjectionTruthBoundary.API_SCHEMA_ONLY.value,
        "limitations": (
            "API exposure is a read-model schema shape, not an API server",
            "endpoint schema is a contract reference, not a route handler",
            "no external access, HTTP server, HTTP route, or runtime handler exists",
        ),
    }
    exposure = SurfaceProjectionApiExposure(
        **payload,
        exposure_hash=_hash_payload(payload),
    )
    assert_api_contract_is_not_server(exposure)
    assert_endpoint_schema_is_not_route_handler(exposure)
    return exposure


def build_surface_projection_no_server_boundary(
    api_exposure: SurfaceProjectionApiExposure | None = None,
) -> SurfaceProjectionNoServerBoundary:
    """P2.6.2 — active no-server boundary firewall."""
    if api_exposure is None:
        api_exposure = build_surface_projection_api_exposure()
    payload: dict[str, Any] = {
        "boundary_id": "p2_6_a_surface_projection_no_server_boundary",
        "schema_version": P2_6_A_NO_SERVER_BOUNDARY_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "boundary_active": True,
        "api_exposure_ref": api_exposure.api_exposure_id,
        "prevents_api_server": True,
        "prevents_http_routes": True,
        "prevents_route_handlers": True,
        "prevents_external_access": True,
        "prevents_runtime_handler": True,
        "reason": SURFACE_PROJECTION_NO_SERVER_REASON,
        "truth_label": SurfaceProjectionTruthBoundary.NO_SERVER_BOUNDARY.value,
        "limitations": (
            "No-server boundary is a safety firewall over the API exposure contract",
            "it does not implement, schedule, or authorize any future API server",
        ),
    }
    boundary = SurfaceProjectionNoServerBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_server_boundary_is_active(boundary)
    return boundary


def build_surface_projection_event_envelope() -> SurfaceProjectionEventEnvelope:
    """P2.6.3 — event envelope as contract only (no bus, no runtime event)."""
    payload: dict[str, Any] = {
        "event_envelope_id": "p2_6_a_surface_projection_event_envelope",
        "schema_version": P2_6_A_EVENT_ENVELOPE_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "event_kind": SurfaceProjectionEventKind.SURFACE_STATE_CHANGED_CONTRACT,
        "event_schema_version": P2_6_A_EVENT_SCHEMA_VERSION,
        "source_projection_ref": "p2_6_a_surface_projection_identity",
        "source_surface_id": CANONICAL_SURFACE_ORDER[0],
        "payload_schema_ref": "surface_projection/event_payload:v1(contract-only)",
        "causal_ref": "",
        "trace_ref": P2_5_D_REPORT_PATH,
        "is_runtime_event": False,
        "emits_runtime_event": False,
        "writes_trace": False,
        "truth_label": SurfaceProjectionTruthBoundary.EVENT_ENVELOPE_ONLY.value,
        "limitations": (
            "Event envelope is a contract describing event shape, not an event bus",
            "trace_ref is a report/evidence reference only, not a new trace write",
            "no runtime event is emitted and no trace is written",
        ),
    }
    envelope = SurfaceProjectionEventEnvelope(
        **payload,
        envelope_hash=_hash_payload(payload),
    )
    assert_event_envelope_is_not_event_bus(envelope)
    return envelope


def build_surface_projection_event_stream_descriptor(
    event_envelope: SurfaceProjectionEventEnvelope | None = None,
) -> SurfaceProjectionEventStreamDescriptor:
    """P2.6.3 — event stream descriptor (not a live runtime stream)."""
    if event_envelope is None:
        event_envelope = build_surface_projection_event_envelope()
    payload: dict[str, Any] = {
        "stream_descriptor_id": "p2_6_a_surface_projection_event_stream_descriptor",
        "schema_version": P2_6_A_EVENT_STREAM_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "event_envelope_refs": (event_envelope.event_envelope_id,),
        "stream_name": P2_6_A_EVENT_STREAM_NAME,
        "stream_version": P2_6_A_EVENT_STREAM_VERSION_LABEL,
        "is_live_stream": False,
        "websocket_created": False,
        "sse_created": False,
        "subscriber_created": False,
        "dispatcher_created": False,
        "runtime_bridge_created": False,
        "truth_label": SurfaceProjectionTruthBoundary.EVENT_STREAM_DESCRIPTOR_ONLY.value,
        "limitations": (
            "Event stream descriptor describes a contract stream, not a live stream",
            "no websocket, SSE, subscriber, dispatcher, or runtime bridge is created",
        ),
    }
    descriptor = SurfaceProjectionEventStreamDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_event_stream_descriptor_is_not_live_stream(descriptor)
    return descriptor


def build_surface_projection_no_event_bus_boundary(
    event_envelope: SurfaceProjectionEventEnvelope | None = None,
    stream_descriptor: SurfaceProjectionEventStreamDescriptor | None = None,
) -> SurfaceProjectionNoEventBusBoundary:
    """P2.6.3 — active no-event-bus / no-runtime-dispatch boundary firewall."""
    if event_envelope is None:
        event_envelope = build_surface_projection_event_envelope()
    if stream_descriptor is None:
        stream_descriptor = build_surface_projection_event_stream_descriptor(
            event_envelope
        )
    payload: dict[str, Any] = {
        "boundary_id": "p2_6_a_surface_projection_no_event_bus_boundary",
        "schema_version": P2_6_A_NO_EVENT_BUS_BOUNDARY_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "boundary_active": True,
        "event_envelope_ref": event_envelope.event_envelope_id,
        "stream_descriptor_ref": stream_descriptor.stream_descriptor_id,
        "prevents_event_bus": True,
        "prevents_event_dispatch": True,
        "prevents_live_stream": True,
        "prevents_websocket": True,
        "prevents_sse": True,
        "prevents_runtime_bridge": True,
        "prevents_runtime_dispatch": True,
        "reason": SURFACE_PROJECTION_NO_EVENT_BUS_REASON,
        "truth_label": SurfaceProjectionTruthBoundary.NO_EVENT_BUS_BOUNDARY.value,
        "limitations": (
            "No-event-bus boundary is a safety firewall over event contracts",
            "it does not implement, schedule, or authorize any future event bus",
        ),
    }
    boundary = SurfaceProjectionNoEventBusBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_event_bus_boundary_is_active(boundary)
    return boundary


def build_surface_projection_availability() -> SurfaceProjectionAvailability:
    """P2.6.4 — availability / unavailable-state contract (not permission)."""
    payload: dict[str, Any] = {
        "availability_id": "p2_6_a_surface_projection_availability",
        "schema_version": P2_6_A_AVAILABILITY_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "availability_status": (
            SurfaceProjectionAvailabilityStatus.AVAILABLE_CONTRACT_ONLY
        ),
        "available_contracts": (
            "SurfaceProjectionIdentity",
            "SurfaceProjectionScope",
            "SurfaceProjectionApiExposure",
            "SurfaceProjectionEventEnvelope",
            "SurfaceProjectionEventStreamDescriptor",
        ),
        "unavailable_capabilities": SURFACE_PROJECTION_UNAVAILABLE_CAPABILITIES,
        "blocked_capabilities": (),
        "unavailable_reasons": (
            SURFACE_PROJECTION_NO_SERVER_REASON,
            SURFACE_PROJECTION_NO_EVENT_BUS_REASON,
            SURFACE_PROJECTION_BINDING_UNAVAILABLE_REASON,
        ),
        "future_pack_refs": (
            P2_6_A_NEXT_PACK,
            "P2.7",
            "P2.10",
            "P2.13",
        ),
        "grants_permission": False,
        "denies_permission": False,
        "activates_approval": False,
        "enforces_policy": False,
        "truth_label": (
            SurfaceProjectionTruthBoundary.AVAILABILITY_READ_MODEL_ONLY.value
        ),
        "limitations": (
            "Availability is capability honesty: UNAVAILABLE is a truthful state",
            "availability does not grant/deny permission, activate approval, or "
            "enforce policy",
            "availability does not mutate runtime",
        ),
    }
    availability = SurfaceProjectionAvailability(
        **payload,
        availability_hash=_hash_payload(payload),
    )
    assert_projection_availability_is_not_permission(availability)
    return availability


def build_surface_projection_foundation_result(
    projection_identity: SurfaceProjectionIdentity | None = None,
    projection_scope: SurfaceProjectionScope | None = None,
    api_exposure: SurfaceProjectionApiExposure | None = None,
    no_server_boundary: SurfaceProjectionNoServerBoundary | None = None,
    event_envelope: SurfaceProjectionEventEnvelope | None = None,
    event_stream_descriptor: SurfaceProjectionEventStreamDescriptor | None = None,
    no_event_bus_boundary: SurfaceProjectionNoEventBusBoundary | None = None,
    availability: SurfaceProjectionAvailability | None = None,
) -> SurfaceProjectionFoundationResult:
    """P2.6.5 — bundle the foundation with an active no-live-bridge boundary."""
    if projection_identity is None:
        projection_identity = build_surface_projection_identity()
    if projection_scope is None:
        projection_scope = build_surface_projection_scope()
    if api_exposure is None:
        api_exposure = build_surface_projection_api_exposure()
    if no_server_boundary is None:
        no_server_boundary = build_surface_projection_no_server_boundary(api_exposure)
    if event_envelope is None:
        event_envelope = build_surface_projection_event_envelope()
    if event_stream_descriptor is None:
        event_stream_descriptor = build_surface_projection_event_stream_descriptor(
            event_envelope
        )
    if no_event_bus_boundary is None:
        no_event_bus_boundary = build_surface_projection_no_event_bus_boundary(
            event_envelope, event_stream_descriptor
        )
    if availability is None:
        availability = build_surface_projection_availability()
    payload: dict[str, Any] = {
        "foundation_result_id": "p2_6_a_surface_projection_foundation_result",
        "schema_version": P2_6_A_FOUNDATION_RESULT_VERSION,
        "section_id": P2_6_A_SECTION_ID,
        "created_for_pack": P2_6_A_PACK_ID,
        "official_section_name": P2_6_A_OFFICIAL_SECTION_NAME,
        "projection_identity": projection_identity,
        "projection_scope": projection_scope,
        "api_exposure": api_exposure,
        "no_server_boundary": no_server_boundary,
        "event_envelope": event_envelope,
        "event_stream_descriptor": event_stream_descriptor,
        "no_event_bus_boundary": no_event_bus_boundary,
        "availability": availability,
        "no_live_bridge_boundary_active": True,
        "is_live_bridge": False,
        "creates_api_server": False,
        "creates_event_bus": False,
        "creates_runtime_dispatch": False,
        "creates_cli_binding": False,
        "creates_product_behavior": False,
        "truth_label": SurfaceProjectionTruthBoundary.FOUNDATION_RESULT_ONLY.value,
        "limitations": (
            "Foundation result bundles projection/API/event contracts only",
            "no-live-bridge boundary is active: this is not a live bridge",
            "no API server, event bus, runtime dispatch, CLI binding, or product "
            "behavior is created",
        ),
    }
    result = SurfaceProjectionFoundationResult(
        **payload,
        foundation_result_hash=_hash_payload(payload),
    )
    assert_no_live_bridge_boundary_is_active(result)
    return result


def build_p2_6_a_side_effect_proof() -> P26ASideEffectProof:
    return P26ASideEffectProof()


def build_p2_6_a_surface_projection_result() -> P26ASurfaceProjectionResult:
    """P2.6-A pack result over P2.5-D evidence."""
    section_result = build_p2_5_d_handoff_section_result()
    gate = build_surface_projection_gate(section_result)
    identity = build_surface_projection_identity()
    scope = build_surface_projection_scope()
    api_exposure = build_surface_projection_api_exposure()
    no_server_boundary = build_surface_projection_no_server_boundary(api_exposure)
    event_envelope = build_surface_projection_event_envelope()
    stream_descriptor = build_surface_projection_event_stream_descriptor(event_envelope)
    no_event_bus_boundary = build_surface_projection_no_event_bus_boundary(
        event_envelope, stream_descriptor
    )
    availability = build_surface_projection_availability()
    foundation = build_surface_projection_foundation_result(
        projection_identity=identity,
        projection_scope=scope,
        api_exposure=api_exposure,
        no_server_boundary=no_server_boundary,
        event_envelope=event_envelope,
        event_stream_descriptor=stream_descriptor,
        no_event_bus_boundary=no_event_bus_boundary,
        availability=availability,
    )
    side_effects = build_p2_6_a_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_6_A_RESULT_VERSION,
        "pack_id": P2_6_A_PACK_ID,
        "section_id": P2_6_A_SECTION_ID,
        "official_section_name": P2_6_A_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_6_A_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_6_A_DEPENDENCY_PACK,
        "projection_gate": gate,
        "projection_identity": identity,
        "projection_scope": scope,
        "api_exposure": api_exposure,
        "no_server_boundary": no_server_boundary,
        "event_envelope": event_envelope,
        "event_stream_descriptor": stream_descriptor,
        "no_event_bus_boundary": no_event_bus_boundary,
        "availability": availability,
        "foundation_result": foundation,
        "truth_labels": tuple(b.value for b in SurfaceProjectionTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "next_pack": P2_6_A_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P26ASurfaceProjectionResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_6_a_does_not_start_future_work(result)
    assert_p2_6_a_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_6_a_result(result: P26ASurfaceProjectionResult | None = None) -> str:
    if result is None:
        result = build_p2_6_a_surface_projection_result()
    return to_canonical_json(result.to_canonical_dict())


def render_surface_projection_contract_summary(
    result: P26ASurfaceProjectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_a_surface_projection_result()
    foundation = result.foundation_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"dependency={result.dependency_pack}",
            f"gate={result.projection_gate.gate_status.value}",
            f"projection_kind={result.projection_identity.projection_kind.value}",
            f"api_exposure={result.api_exposure.exposure_mode.value}",
            f"no_server_boundary={str(result.no_server_boundary.boundary_active).lower()}",
            f"event_kind={result.event_envelope.event_kind.value}",
            f"no_event_bus_boundary="
            f"{str(result.no_event_bus_boundary.boundary_active).lower()}",
            f"availability={result.availability.availability_status.value}",
            f"no_live_bridge="
            f"{str(foundation.no_live_bridge_boundary_active).lower()}",
            f"next={result.next_pack}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"release_scope={str(result.claims_release_scope).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


# ---------------------------------------------------------------------------
# Invariant assertions
# ---------------------------------------------------------------------------


def assert_p2_5_d_section_seal_available(result: P25DHandoffSectionResult) -> None:
    if result.pack_id != P2_5_D_PACK_ID or result.starts_future_work:
        _reject(
            "P2.6-A requires a sealed P2.5-D section result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    seal = result.section_seal
    if not seal.sealed_contract_scope or seal.sealed_release_scope:
        _reject(
            "P2.6-A requires the P2.5-D contract-scope section seal",
            field="sealed_contract_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not result.readiness_audit.audit_passed_for_contract_scope:
        _reject(
            "P2.6-A requires a passing P2.5-D contract-scope readiness audit",
            field="audit_passed_for_contract_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_gate_depends_on_p2_5_d(gate: SurfaceProjectionGate) -> None:
    if gate.dependency_pack != P2_5_D_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.6-A section gate must depend on passed P2.5-D repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_section_seal_ref
        or not gate.dependency_readiness_audit_ref
        or not gate.dependency_contract_scope_demo_ref
    ):
        _reject(
            "P2.6-A section gate must reference P2.5-D seal/audit/demo evidence",
            field="dependency_section_seal_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if gate.section_id != P2_6_A_SECTION_ID or (
        gate.official_section_name != P2_6_A_OFFICIAL_SECTION_NAME
    ):
        _reject(
            "P2.6-A section gate must declare section P2.6 Surface Projection / "
            "API / Event Bridge",
            field="official_section_name",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: SurfaceProjectionGate,
) -> None:
    if gate.omni_evidence_required or (
        not gate.omni_evidence_ignored_by_operator_instruction
    ):
        _reject(
            "P2.6-A gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_projection_is_not_ui(identity: SurfaceProjectionIdentity) -> None:
    if identity.is_ui or identity.claims_live or identity.claims_trace_verified:
        _reject(
            "P2.6-A projection identity must remain read-model only, not UI",
            field="is_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_is_not_source_of_truth(
    identity: SurfaceProjectionIdentity,
) -> None:
    if identity.is_source_of_truth:
        _reject(
            "P2.6-A projection identity must not be source-of-truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_surface_scope_uses_official_surfaces(scope: SurfaceProjectionScope) -> None:
    if tuple(scope.surface_ids) != tuple(CANONICAL_SURFACE_ORDER):
        _reject(
            "P2.6-A surface scope must use the official active P2 surface set",
            field="surface_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if scope.switches_surface or scope.executes_route or scope.mutates_navigation:
        _reject(
            "P2.6-A surface scope must not switch surfaces, execute routes, or "
            "mutate navigation",
            field="switches_surface",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_api_contract_is_not_server(exposure: SurfaceProjectionApiExposure) -> None:
    if (
        exposure.external_access_enabled
        or exposure.http_server_created
        or exposure.http_routes_created
        or exposure.runtime_handler_created
    ):
        _reject(
            "P2.6-A API exposure must be contract/schema only, not an API server",
            field="http_server_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_endpoint_schema_is_not_route_handler(
    exposure: SurfaceProjectionApiExposure,
) -> None:
    if exposure.route_handler_created:
        _reject(
            "P2.6-A endpoint schema must not be a route handler",
            field="route_handler_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_server_boundary_is_active(
    boundary: SurfaceProjectionNoServerBoundary,
) -> None:
    flags = (
        boundary.boundary_active,
        boundary.prevents_api_server,
        boundary.prevents_http_routes,
        boundary.prevents_route_handlers,
        boundary.prevents_external_access,
        boundary.prevents_runtime_handler,
    )
    if not all(flags):
        _reject(
            "P2.6-A no-server boundary must be active and prevent all server paths",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_event_envelope_is_not_event_bus(
    envelope: SurfaceProjectionEventEnvelope,
) -> None:
    if (
        envelope.is_runtime_event
        or envelope.emits_runtime_event
        or envelope.writes_trace
    ):
        _reject(
            "P2.6-A event envelope must be a contract only, not an event bus",
            field="emits_runtime_event",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_event_stream_descriptor_is_not_live_stream(
    descriptor: SurfaceProjectionEventStreamDescriptor,
) -> None:
    if (
        descriptor.is_live_stream
        or descriptor.websocket_created
        or descriptor.sse_created
        or descriptor.subscriber_created
        or descriptor.dispatcher_created
        or descriptor.runtime_bridge_created
    ):
        _reject(
            "P2.6-A event stream descriptor must not be a live runtime stream",
            field="is_live_stream",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_event_bus_boundary_is_active(
    boundary: SurfaceProjectionNoEventBusBoundary,
) -> None:
    flags = (
        boundary.boundary_active,
        boundary.prevents_event_bus,
        boundary.prevents_event_dispatch,
        boundary.prevents_live_stream,
        boundary.prevents_websocket,
        boundary.prevents_sse,
        boundary.prevents_runtime_bridge,
        boundary.prevents_runtime_dispatch,
    )
    if not all(flags):
        _reject(
            "P2.6-A no-event-bus boundary must be active and prevent all bus paths",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_availability_is_not_permission(
    availability: SurfaceProjectionAvailability,
) -> None:
    if (
        availability.grants_permission
        or availability.denies_permission
        or availability.activates_approval
        or availability.enforces_policy
    ):
        _reject(
            "P2.6-A availability must not enforce permission or activate approval",
            field="grants_permission",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_live_bridge_boundary_is_active(
    result: SurfaceProjectionFoundationResult,
) -> None:
    if not result.no_live_bridge_boundary_active:
        _reject(
            "P2.6-A foundation result must keep the no-live-bridge boundary active",
            field="no_live_bridge_boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if (
        result.is_live_bridge
        or result.creates_api_server
        or result.creates_event_bus
        or result.creates_runtime_dispatch
        or result.creates_cli_binding
        or result.creates_product_behavior
    ):
        _reject(
            "P2.6-A foundation result must not be a live bridge",
            field="is_live_bridge",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_6_a_does_not_start_future_work(
    result: P26ASurfaceProjectionResult,
) -> None:
    if result.starts_future_work or result.next_pack != P2_6_A_NEXT_PACK:
        _reject(
            "P2.6-A result must not start future work; next pack is P2.6-B",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if (
        result.claims_live
        or result.claims_trace_verified
        or result.claims_release_scope
        or result.claims_product_behavior
    ):
        _reject(
            "P2.6-A result must not claim live/trace-verified/release/product",
            field="claims_live",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_6_b_started,
            proof.p2_7_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.6-A must not start P2.6-B/P2.7/P2.10/P2.13",
            field="p2_6_b_started",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_6_a_side_effects_all_false(proof: P26ASideEffectProof) -> None:
    for field in fields(proof):
        value = getattr(proof, field.name)
        if value is not False:
            _reject(
                "P2.6-A side-effect proof fields must all be false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
