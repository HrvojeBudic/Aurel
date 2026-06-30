"""P2.6-C surface projection event bridge boundary contracts.

Contract-only event bridge expansion over the P2.6-B projection schema/read-model
result. This module defines event-envelope registry/catalog semantics, payload
schema references, source-target mappings, causality/correlation/evidence refs,
subscription/delivery descriptors, and no-live-stream/no-runtime-dispatch
boundaries.

Core law:
  - Event envelope is not runtime event.
  - Event kind catalog is not event bus.
  - Event envelope registry is not dispatcher.
  - Payload schema ref is not payload execution.
  - Source-target mapping is not surface switching.
  - Evidence reference is not TRACE_VERIFIED.
  - Subscription/delivery descriptors are not runtimes.
  - P2.6-C event bridge boundary result is not runtime bridge.
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
from .read_model import detect_surface_taxonomy_drift
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES
from .surface_projection_schemas import (
    P2_6_B_OFFICIAL_SECTION_NAME,
    P2_6_B_PACK_ID,
    P2_6_B_REPORT_PATH,
    P2_6_B_SECTION_ID,
    P26BSurfaceProjectionSchemaResult,
    SurfaceProjectionSchemaKind,
    build_p2_6_b_surface_projection_schema_result,
)
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_6_C_PACK_ID = "P2.6-C"
P2_6_C_SECTION_ID = P2_6_B_SECTION_ID
P2_6_C_OFFICIAL_SECTION_NAME = P2_6_B_OFFICIAL_SECTION_NAME
P2_6_C_DEPENDENCY_PACK = P2_6_B_PACK_ID
P2_6_C_NEXT_PACK = "P2.6-D"
P2_6_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.6.11",
    "P2.6.12",
    "P2.6.13",
    "P2.6.14",
    "P2.6.15",
)
P2_6_C_REPORT_FILENAME = "P2_6_C_SURFACE_PROJECTION_EVENT_BRIDGE_BOUNDARY.md"
P2_6_C_REPORT_PATH = f"agent/reports/{P2_6_C_REPORT_FILENAME}"
P2_6_B_IMPLEMENTATION_COMMIT_REF = "7eca9c2"
P2_6_B_REPORT_HASH_COMMIT_REF = "f5df2e0"

P2_6_C_GATE_VERSION = "p2_6_c_surface_projection_event_bridge_gate.v1"
P2_6_C_REGISTRY_VERSION = "p2_6_c_surface_projection_event_envelope_registry.v1"
P2_6_C_CATALOG_VERSION = "p2_6_c_surface_projection_event_kind_catalog.v1"
P2_6_C_EVENT_SCHEMA_VERSION = "surface_projection.event_envelope.v1"
P2_6_C_SUBSCRIPTION_VERSION = "surface_projection.subscription_descriptor.v1"
P2_6_C_DELIVERY_VERSION = "surface_projection.delivery_descriptor.v1"
P2_6_C_NO_LIVE_STREAM_BOUNDARY_VERSION = (
    "p2_6_c_surface_projection_no_live_stream_boundary.v1"
)
P2_6_C_NO_RUNTIME_DISPATCH_BOUNDARY_VERSION = (
    "p2_6_c_surface_projection_no_runtime_dispatch_boundary.v1"
)
P2_6_C_BOUNDARY_RESULT_VERSION = (
    "p2_6_c_surface_projection_event_bridge_boundary_result.v1"
)
P2_6_C_RESULT_VERSION = "p2_6_c_surface_projection_event_bridge_result.v1"

NO_LIVE_STREAM_REASON = (
    "P2.6-C defines subscription and delivery descriptors only. No websocket, "
    "SSE, live stream, subscriber runtime, subscription runtime, delivery "
    "runtime, or delivery channel exists in this repo scope."
)

NO_RUNTIME_DISPATCH_REASON = (
    "P2.6-C defines event bridge boundary contracts only. No event bus, "
    "event dispatcher, event dispatch, runtime event emission, runtime bridge, "
    "runtime dispatch, API event bridge runtime, or trace write exists in this "
    "repo scope."
)


class SurfaceProjectionEventBridgeGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class SurfaceProjectionEventKind(str, Enum):
    SURFACE_REGISTRY_PROJECTED_CONTRACT = "SURFACE_REGISTRY_PROJECTED_CONTRACT"
    LOCAL_NAVIGATION_PROJECTED_CONTRACT = "LOCAL_NAVIGATION_PROJECTED_CONTRACT"
    WINDOW_STATE_PROJECTED_CONTRACT = "WINDOW_STATE_PROJECTED_CONTRACT"
    COMMAND_PALETTE_PROJECTED_CONTRACT = "COMMAND_PALETTE_PROJECTED_CONTRACT"
    CROSS_SURFACE_HANDOFF_PROJECTED_CONTRACT = (
        "CROSS_SURFACE_HANDOFF_PROJECTED_CONTRACT"
    )
    SECTION_SEAL_PROJECTED_CONTRACT = "SECTION_SEAL_PROJECTED_CONTRACT"
    SCHEMA_EXPANSION_PROJECTED_CONTRACT = "SCHEMA_EXPANSION_PROJECTED_CONTRACT"
    DEV_FIXTURE_EVENT = "DEV_FIXTURE_EVENT"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class SurfaceProjectionSubscriptionMode(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE_DESCRIPTOR_ONLY = "DEV_FIXTURE_DESCRIPTOR_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_SUBSCRIBABLE = "NOT_SUBSCRIBABLE"


class SurfaceProjectionDeliveryMode(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE_DESCRIPTOR_ONLY = "DEV_FIXTURE_DESCRIPTOR_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_DELIVERABLE = "NOT_DELIVERABLE"


class SurfaceProjectionEventBridgeTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    EVENT_BRIDGE_GATE_ONLY = "EVENT_BRIDGE_GATE_ONLY"
    EVENT_ENVELOPE_ONLY = "EVENT_ENVELOPE_ONLY"
    EVENT_KIND_CATALOG_ONLY = "EVENT_KIND_CATALOG_ONLY"
    PAYLOAD_SCHEMA_REF_ONLY = "PAYLOAD_SCHEMA_REF_ONLY"
    SOURCE_TARGET_MAPPING_ONLY = "SOURCE_TARGET_MAPPING_ONLY"
    CAUSALITY_REF_ONLY = "CAUSALITY_REF_ONLY"
    CORRELATION_REF_ONLY = "CORRELATION_REF_ONLY"
    EVIDENCE_REF_ONLY = "EVIDENCE_REF_ONLY"
    SUBSCRIPTION_DESCRIPTOR_ONLY = "SUBSCRIPTION_DESCRIPTOR_ONLY"
    DELIVERY_DESCRIPTOR_ONLY = "DELIVERY_DESCRIPTOR_ONLY"
    NO_LIVE_STREAM_BOUNDARY = "NO_LIVE_STREAM_BOUNDARY"
    NO_EVENT_BUS_BOUNDARY = "NO_EVENT_BUS_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    NO_TRACE_WRITE_BOUNDARY = "NO_TRACE_WRITE_BOUNDARY"
    EVENT_BRIDGE_BOUNDARY_RESULT_ONLY = "EVENT_BRIDGE_BOUNDARY_RESULT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_PAYLOAD_EXECUTION = "NOT_PAYLOAD_EXECUTION"
    NOT_RUNTIME_EVENT = "NOT_RUNTIME_EVENT"
    NOT_EVENT_BUS = "NOT_EVENT_BUS"
    NOT_EVENT_DISPATCH = "NOT_EVENT_DISPATCH"
    NOT_EVENT_DISPATCHER = "NOT_EVENT_DISPATCHER"
    NOT_EVENT_SUBSCRIBER = "NOT_EVENT_SUBSCRIBER"
    NOT_SUBSCRIBER_RUNTIME = "NOT_SUBSCRIBER_RUNTIME"
    NOT_SUBSCRIPTION_RUNTIME = "NOT_SUBSCRIPTION_RUNTIME"
    NOT_DELIVERY_CHANNEL = "NOT_DELIVERY_CHANNEL"
    NOT_DELIVERY_RUNTIME = "NOT_DELIVERY_RUNTIME"
    NOT_WEBSOCKET = "NOT_WEBSOCKET"
    NOT_SSE = "NOT_SSE"
    NOT_LIVE_STREAM = "NOT_LIVE_STREAM"
    NOT_RUNTIME_LINK = "NOT_RUNTIME_LINK"
    NOT_RUNTIME_BRIDGE = "NOT_RUNTIME_BRIDGE"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_API_EVENT_BRIDGE_RUNTIME = "NOT_API_EVENT_BRIDGE_RUNTIME"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
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
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class SurfaceProjectionEventBridgeGate(_CanonicalMixin):
    gate_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_schema_expansion_result_ref: str
    dependency_no_live_endpoint_boundary_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: SurfaceProjectionEventBridgeGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventPayloadSchemaRef(_CanonicalMixin):
    payload_ref_id: str
    source_pack: str
    source_schema_ref: str
    schema_kind: SurfaceProjectionSchemaKind
    schema_version: str
    payload_fields: tuple[str, ...]
    is_payload_execution: bool
    mutates_payload: bool
    truth_label: str
    limitations: tuple[str, ...]
    payload_ref_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventSourceTargetMapping(_CanonicalMixin):
    mapping_id: str
    source_surface_ids: tuple[str, ...]
    target_surface_ids: tuple[str, ...]
    official_surface_set: tuple[str, ...]
    source_projection_ref: str
    target_projection_ref: str
    switches_surface: bool
    executes_route: bool
    mutates_navigation: bool
    truth_label: str
    limitations: tuple[str, ...]
    mapping_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventCausalityRef(_CanonicalMixin):
    causality_ref_id: str
    causal_source_ref: str
    causal_chain_ref: str
    source_report_ref: str
    writes_trace: bool
    creates_trace_event: bool
    claims_trace_verified: bool
    truth_label: str
    limitations: tuple[str, ...]
    causality_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventCorrelationRef(_CanonicalMixin):
    correlation_ref_id: str
    correlation_key_contract: str
    correlation_scope: str
    runtime_link_created: bool
    mutates_runtime_context: bool
    truth_label: str
    limitations: tuple[str, ...]
    correlation_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventEvidenceRef(_CanonicalMixin):
    evidence_ref_id: str
    source_report_ref: str
    source_test_ref: str
    source_commit_ref: str
    evidence_kind: str
    claims_trace_verified: bool
    writes_trace: bool
    truth_label: str
    limitations: tuple[str, ...]
    evidence_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventEnvelopeEntry(_CanonicalMixin):
    entry_id: str
    event_kind: SurfaceProjectionEventKind
    event_schema_version: str
    payload_schema_ref: str
    source_target_mapping_ref: str
    causality_ref: str
    correlation_ref: str
    evidence_ref: str
    available_as_contract: bool
    available_as_runtime_event: bool
    requires_future_pack: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventKindSpec(_CanonicalMixin):
    event_kind_spec_id: str
    event_kind: SurfaceProjectionEventKind
    event_name: str
    event_description: str
    schema_version: str
    source_schema_ref: str
    target_schema_ref: str
    is_runtime_event: bool
    emits_runtime_event: bool
    truth_label: str
    limitations: tuple[str, ...]
    spec_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventKindCatalog(_CanonicalMixin):
    catalog_id: str
    section_id: str
    created_for_pack: str
    event_kinds: tuple[SurfaceProjectionEventKind, ...]
    event_kind_specs: tuple[SurfaceProjectionEventKindSpec, ...]
    is_event_bus: bool
    is_dispatcher: bool
    truth_label: str
    limitations: tuple[str, ...]
    catalog_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventEnvelopeRegistry(_CanonicalMixin):
    registry_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_version: str
    entries: tuple[SurfaceProjectionEventEnvelopeEntry, ...]
    event_kind_catalog_ref: str
    source_pack_refs: tuple[str, ...]
    source_section_refs: tuple[str, ...]
    is_event_bus: bool
    is_dispatcher: bool
    emits_runtime_events: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSubscriptionDescriptor(_CanonicalMixin):
    subscription_descriptor_id: str
    subscription_mode: SurfaceProjectionSubscriptionMode
    event_kind_refs: tuple[str, ...]
    filter_contract_ref: str
    subscriber_ref: str
    creates_subscriber_runtime: bool
    creates_subscription_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class SurfaceProjectionDeliveryDescriptor(_CanonicalMixin):
    delivery_descriptor_id: str
    delivery_mode: SurfaceProjectionDeliveryMode
    delivery_target_contract: str
    delivery_channel_ref: str
    creates_delivery_channel: bool
    creates_delivery_runtime: bool
    sends_message: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class SurfaceProjectionNoLiveStreamBoundary(_CanonicalMixin):
    boundary_id: str
    boundary_active: bool
    subscription_descriptor_ref: str
    delivery_descriptor_ref: str
    prevents_websocket: bool
    prevents_sse: bool
    prevents_live_stream: bool
    prevents_subscriber_runtime: bool
    prevents_delivery_runtime: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SurfaceProjectionNoRuntimeDispatchBoundary(_CanonicalMixin):
    boundary_id: str
    boundary_active: bool
    event_registry_ref: str
    event_kind_catalog_ref: str
    prevents_event_bus: bool
    prevents_event_dispatcher: bool
    prevents_event_dispatch: bool
    prevents_runtime_event_emission: bool
    prevents_runtime_bridge: bool
    prevents_runtime_dispatch: bool
    prevents_api_event_bridge_runtime: bool
    prevents_trace_write: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SurfaceProjectionEventBridgeBoundaryResult(_CanonicalMixin):
    event_bridge_boundary_result_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    event_bridge_gate: SurfaceProjectionEventBridgeGate
    event_envelope_registry: SurfaceProjectionEventEnvelopeRegistry
    event_kind_catalog: SurfaceProjectionEventKindCatalog
    payload_schema_refs: tuple[SurfaceProjectionEventPayloadSchemaRef, ...]
    source_target_mappings: tuple[SurfaceProjectionEventSourceTargetMapping, ...]
    causality_refs: tuple[SurfaceProjectionEventCausalityRef, ...]
    correlation_refs: tuple[SurfaceProjectionEventCorrelationRef, ...]
    evidence_refs: tuple[SurfaceProjectionEventEvidenceRef, ...]
    subscription_descriptor: SurfaceProjectionSubscriptionDescriptor
    delivery_descriptor: SurfaceProjectionDeliveryDescriptor
    no_live_stream_boundary: SurfaceProjectionNoLiveStreamBoundary
    no_runtime_dispatch_boundary: SurfaceProjectionNoRuntimeDispatchBoundary
    creates_event_bus: bool
    creates_event_dispatcher: bool
    creates_event_dispatch: bool
    creates_subscriber_runtime: bool
    creates_delivery_runtime: bool
    creates_live_stream: bool
    creates_runtime_event_emission: bool
    creates_runtime_bridge: bool
    creates_runtime_dispatch: bool
    creates_api_event_bridge_runtime: bool
    writes_trace: bool
    writes_memory: bool
    writes_storage: bool
    creates_cli_binding: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    result_hash: str


@dataclass(frozen=True)
class P26CSideEffectProof(_CanonicalMixin):
    event_bus_created: bool = False
    event_dispatcher_created: bool = False
    event_subscriber_runtime_created: bool = False
    subscription_runtime_created: bool = False
    delivery_runtime_created: bool = False
    delivery_channel_created: bool = False
    websocket_stream_created: bool = False
    sse_stream_created: bool = False
    live_stream_created: bool = False
    runtime_event_emitted: bool = False
    runtime_bridge_created: bool = False
    runtime_dispatch_created: bool = False
    api_event_bridge_runtime_created: bool = False
    trace_written: bool = False
    memory_written: bool = False
    storage_written: bool = False
    projection_ui_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    route_handler_created: bool = False
    live_endpoint_created: bool = False
    live_query_execution_created: bool = False
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
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_6_d_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class P26CSurfaceProjectionEventBridgeResult(_CanonicalMixin):
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    event_bridge_gate: SurfaceProjectionEventBridgeGate
    event_envelope_registry: SurfaceProjectionEventEnvelopeRegistry
    event_kind_catalog: SurfaceProjectionEventKindCatalog
    payload_schema_refs: tuple[SurfaceProjectionEventPayloadSchemaRef, ...]
    source_target_mappings: tuple[SurfaceProjectionEventSourceTargetMapping, ...]
    causality_refs: tuple[SurfaceProjectionEventCausalityRef, ...]
    correlation_refs: tuple[SurfaceProjectionEventCorrelationRef, ...]
    evidence_refs: tuple[SurfaceProjectionEventEvidenceRef, ...]
    subscription_descriptor: SurfaceProjectionSubscriptionDescriptor
    delivery_descriptor: SurfaceProjectionDeliveryDescriptor
    no_live_stream_boundary: SurfaceProjectionNoLiveStreamBoundary
    no_runtime_dispatch_boundary: SurfaceProjectionNoRuntimeDispatchBoundary
    event_bridge_boundary_result: SurfaceProjectionEventBridgeBoundaryResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P26CSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _schema_kind_for_event_kind(
    event_kind: SurfaceProjectionEventKind,
) -> SurfaceProjectionSchemaKind:
    mapping = {
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.SURFACE_REGISTRY_SCHEMA
        ),
        SurfaceProjectionEventKind.LOCAL_NAVIGATION_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.LOCAL_NAVIGATION_SCHEMA
        ),
        SurfaceProjectionEventKind.WINDOW_STATE_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.WINDOW_STATE_SCHEMA
        ),
        SurfaceProjectionEventKind.COMMAND_PALETTE_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.COMMAND_PALETTE_SCHEMA
        ),
        SurfaceProjectionEventKind.CROSS_SURFACE_HANDOFF_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.CROSS_SURFACE_HANDOFF_SCHEMA
        ),
        SurfaceProjectionEventKind.SECTION_SEAL_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.SECTION_SEAL_SCHEMA
        ),
        SurfaceProjectionEventKind.SCHEMA_EXPANSION_PROJECTED_CONTRACT: (
            SurfaceProjectionSchemaKind.DEV_FIXTURE_SCHEMA
        ),
        SurfaceProjectionEventKind.DEV_FIXTURE_EVENT: (
            SurfaceProjectionSchemaKind.DEV_FIXTURE_SCHEMA
        ),
        SurfaceProjectionEventKind.UNKNOWN_UNAVAILABLE: (
            SurfaceProjectionSchemaKind.UNKNOWN_UNAVAILABLE
        ),
    }
    return mapping[event_kind]


def _schema_ref_for_event_kind(event_kind: SurfaceProjectionEventKind) -> str:
    schema_kind = _schema_kind_for_event_kind(event_kind)
    return f"P2.6-B:{schema_kind.value.lower()}"


def build_surface_projection_event_bridge_gate(
    schema_result: P26BSurfaceProjectionSchemaResult | None = None,
) -> SurfaceProjectionEventBridgeGate:
    if schema_result is None:
        schema_result = build_p2_6_b_surface_projection_schema_result()
    payload: dict[str, Any] = {
        "gate_id": "p2_6_c_surface_projection_event_bridge_gate",
        "section_id": P2_6_C_SECTION_ID,
        "created_for_pack": P2_6_C_PACK_ID,
        "official_section_name": P2_6_C_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_6_C_DEPENDENCY_PACK,
        "dependency_report_ref": P2_6_B_REPORT_PATH,
        "dependency_commit_ref": P2_6_B_IMPLEMENTATION_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.6-B",
        "dependency_schema_expansion_result_ref": (
            schema_result.schema_expansion_result.schema_expansion_result_id
        ),
        "dependency_no_live_endpoint_boundary_ref": (
            schema_result.no_live_endpoint_boundary.boundary_id
        ),
        "dependency_side_effect_proof_ref": "P26BSideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": SurfaceProjectionEventBridgeGateStatus.READY,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.EVENT_BRIDGE_GATE_ONLY.value
        ),
        "limitations": (
            "P2.6-B repo evidence remains the hard start gate",
            "OMNI evidence is ignored only by explicit operator instruction",
            "event bridge gate does not create event bus or runtime dispatch",
        ),
    }
    gate = SurfaceProjectionEventBridgeGate(**payload, gate_hash=_hash_payload(payload))
    if gate.dependency_pack != P2_6_B_PACK_ID:
        _reject(
            "P2.6-C event bridge gate must depend on P2.6-B",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return gate


def build_surface_projection_event_payload_schema_ref(
    event_kind: SurfaceProjectionEventKind = (
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    ),
) -> SurfaceProjectionEventPayloadSchemaRef:
    schema_kind = _schema_kind_for_event_kind(event_kind)
    payload: dict[str, Any] = {
        "payload_ref_id": f"p2_6_c_payload_ref_{event_kind.value.lower()}",
        "source_pack": P2_6_B_PACK_ID,
        "source_schema_ref": _schema_ref_for_event_kind(event_kind),
        "schema_kind": schema_kind,
        "schema_version": P2_6_C_EVENT_SCHEMA_VERSION,
        "payload_fields": (
            "event_kind",
            "schema_ref",
            "source_surface_id",
            "target_surface_id",
            "evidence_ref",
        ),
        "is_payload_execution": False,
        "mutates_payload": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.PAYLOAD_SCHEMA_REF_ONLY.value
        ),
        "limitations": (
            "Payload schema ref points to P2.6-B schema contracts by ref only",
            "payload is not executed, mutated, or dispatched",
        ),
    }
    ref = SurfaceProjectionEventPayloadSchemaRef(
        **payload,
        payload_ref_hash=_hash_payload(payload),
    )
    if ref.is_payload_execution or ref.mutates_payload:
        _reject(
            "Payload schema reference must not execute or mutate payload",
            field="is_payload_execution",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    return ref


def build_surface_projection_event_source_target_mapping(
    event_kind: SurfaceProjectionEventKind = (
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    ),
) -> SurfaceProjectionEventSourceTargetMapping:
    payload: dict[str, Any] = {
        "mapping_id": f"p2_6_c_source_target_mapping_{event_kind.value.lower()}",
        "source_surface_ids": CANONICAL_SURFACE_ORDER,
        "target_surface_ids": CANONICAL_SURFACE_ORDER,
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "source_projection_ref": _schema_ref_for_event_kind(event_kind),
        "target_projection_ref": "P2.6-C:event_envelope_registry_contract",
        "switches_surface": False,
        "executes_route": False,
        "mutates_navigation": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.SOURCE_TARGET_MAPPING_ONLY.value
        ),
        "limitations": (
            "Source-target mapping is a projection relationship only",
            "mapping does not switch surfaces, execute routes, or mutate nav",
        ),
    }
    mapping = SurfaceProjectionEventSourceTargetMapping(
        **payload,
        mapping_hash=_hash_payload(payload),
    )
    if mapping.switches_surface or mapping.executes_route or mapping.mutates_navigation:
        _reject(
            "Source-target mapping must not switch surfaces or mutate navigation",
            field="switches_surface",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    return mapping


def build_surface_projection_event_causality_ref(
    event_kind: SurfaceProjectionEventKind = (
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    ),
) -> SurfaceProjectionEventCausalityRef:
    payload: dict[str, Any] = {
        "causality_ref_id": f"p2_6_c_causality_ref_{event_kind.value.lower()}",
        "causal_source_ref": _schema_ref_for_event_kind(event_kind),
        "causal_chain_ref": "P2.6-A->P2.6-B->P2.6-C:contract_chain",
        "source_report_ref": P2_6_B_REPORT_PATH,
        "writes_trace": False,
        "creates_trace_event": False,
        "claims_trace_verified": False,
        "truth_label": SurfaceProjectionEventBridgeTruthBoundary.CAUSALITY_REF_ONLY.value,
        "limitations": (
            "Causality ref is report/schema reference only",
            "it does not write trace or create trace events",
        ),
    }
    ref = SurfaceProjectionEventCausalityRef(
        **payload,
        causality_hash=_hash_payload(payload),
    )
    assert_causality_ref_is_not_trace_write(ref)
    return ref


def build_surface_projection_event_correlation_ref(
    event_kind: SurfaceProjectionEventKind = (
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    ),
) -> SurfaceProjectionEventCorrelationRef:
    payload: dict[str, Any] = {
        "correlation_ref_id": f"p2_6_c_correlation_ref_{event_kind.value.lower()}",
        "correlation_key_contract": f"{event_kind.value.lower()}:stable_key_contract",
        "correlation_scope": "P2.6 contract-only event envelope scope",
        "runtime_link_created": False,
        "mutates_runtime_context": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.CORRELATION_REF_ONLY.value
        ),
        "limitations": (
            "Correlation ref is static key grammar only",
            "it creates no runtime link and mutates no runtime context",
        ),
    }
    ref = SurfaceProjectionEventCorrelationRef(
        **payload,
        correlation_hash=_hash_payload(payload),
    )
    if ref.runtime_link_created or ref.mutates_runtime_context:
        _reject(
            "Correlation ref must not create runtime link or mutate context",
            field="runtime_link_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    return ref


def build_surface_projection_event_evidence_ref(
    event_kind: SurfaceProjectionEventKind = (
        SurfaceProjectionEventKind.SURFACE_REGISTRY_PROJECTED_CONTRACT
    ),
) -> SurfaceProjectionEventEvidenceRef:
    payload: dict[str, Any] = {
        "evidence_ref_id": f"p2_6_c_evidence_ref_{event_kind.value.lower()}",
        "source_report_ref": P2_6_B_REPORT_PATH,
        "source_test_ref": "tests/aurel_shell/test_shell_surface_projection_schemas.py",
        "source_commit_ref": P2_6_B_IMPLEMENTATION_COMMIT_REF,
        "evidence_kind": "REPORT_AND_VALIDATION_REF_ONLY",
        "claims_trace_verified": False,
        "writes_trace": False,
        "truth_label": SurfaceProjectionEventBridgeTruthBoundary.EVIDENCE_REF_ONLY.value,
        "limitations": (
            "Evidence ref cites report/test/commit evidence only",
            "report evidence is not TRACE_VERIFIED and writes no trace",
        ),
    }
    ref = SurfaceProjectionEventEvidenceRef(
        **payload,
        evidence_hash=_hash_payload(payload),
    )
    assert_evidence_ref_is_not_trace_verified(ref)
    return ref


def build_surface_projection_event_kind_spec(
    event_kind: SurfaceProjectionEventKind,
) -> SurfaceProjectionEventKindSpec:
    source_schema_ref = _schema_ref_for_event_kind(event_kind)
    payload: dict[str, Any] = {
        "event_kind_spec_id": f"p2_6_c_event_kind_spec_{event_kind.value.lower()}",
        "event_kind": event_kind,
        "event_name": event_kind.value.lower(),
        "event_description": (
            "Contract-only projected surface event kind; not runtime event"
        ),
        "schema_version": P2_6_C_EVENT_SCHEMA_VERSION,
        "source_schema_ref": source_schema_ref,
        "target_schema_ref": "P2.6-C:event_envelope_contract",
        "is_runtime_event": False,
        "emits_runtime_event": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.EVENT_KIND_CATALOG_ONLY.value
        ),
        "limitations": (
            "Event kind spec describes an allowed contract vocabulary only",
            "it is not runtime event emission and does not dispatch",
        ),
    }
    spec = SurfaceProjectionEventKindSpec(**payload, spec_hash=_hash_payload(payload))
    if spec.is_runtime_event or spec.emits_runtime_event:
        _reject(
            "Event kind spec must not be or emit a runtime event",
            field="is_runtime_event",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    return spec


def build_surface_projection_event_kind_catalog() -> SurfaceProjectionEventKindCatalog:
    specs = tuple(
        build_surface_projection_event_kind_spec(kind)
        for kind in SurfaceProjectionEventKind
    )
    payload: dict[str, Any] = {
        "catalog_id": "p2_6_c_surface_projection_event_kind_catalog",
        "section_id": P2_6_C_SECTION_ID,
        "created_for_pack": P2_6_C_PACK_ID,
        "event_kinds": tuple(SurfaceProjectionEventKind),
        "event_kind_specs": specs,
        "is_event_bus": False,
        "is_dispatcher": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.EVENT_KIND_CATALOG_ONLY.value
        ),
        "limitations": (
            "Catalog describes event kinds only",
            "catalog is not an event bus or dispatcher",
        ),
    }
    catalog = SurfaceProjectionEventKindCatalog(
        **payload,
        catalog_hash=_hash_payload(payload),
    )
    assert_event_kind_catalog_is_not_event_bus(catalog)
    return catalog


def build_surface_projection_event_envelope_entry(
    event_kind: SurfaceProjectionEventKind,
) -> SurfaceProjectionEventEnvelopeEntry:
    future_pack = ""
    if event_kind is SurfaceProjectionEventKind.UNKNOWN_UNAVAILABLE:
        future_pack = "P2.6-D/P2.7/P2.10/P2.13"
    payload: dict[str, Any] = {
        "entry_id": f"p2_6_c_event_envelope_entry_{event_kind.value.lower()}",
        "event_kind": event_kind,
        "event_schema_version": P2_6_C_EVENT_SCHEMA_VERSION,
        "payload_schema_ref": (
            f"p2_6_c_payload_ref_{event_kind.value.lower()}"
        ),
        "source_target_mapping_ref": (
            f"p2_6_c_source_target_mapping_{event_kind.value.lower()}"
        ),
        "causality_ref": f"p2_6_c_causality_ref_{event_kind.value.lower()}",
        "correlation_ref": f"p2_6_c_correlation_ref_{event_kind.value.lower()}",
        "evidence_ref": f"p2_6_c_evidence_ref_{event_kind.value.lower()}",
        "available_as_contract": event_kind
        is not SurfaceProjectionEventKind.UNKNOWN_UNAVAILABLE,
        "available_as_runtime_event": False,
        "requires_future_pack": future_pack,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.EVENT_ENVELOPE_ONLY.value
        ),
        "limitations": (
            "Event envelope entry is registry metadata only",
            "entry is not a runtime event and does not dispatch",
        ),
    }
    entry = SurfaceProjectionEventEnvelopeEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )
    if entry.available_as_runtime_event:
        _reject(
            "Event envelope entry must not be available as runtime event",
            field="available_as_runtime_event",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    return entry


def build_surface_projection_event_envelope_registry(
    event_kind_catalog: SurfaceProjectionEventKindCatalog | None = None,
) -> SurfaceProjectionEventEnvelopeRegistry:
    if event_kind_catalog is None:
        event_kind_catalog = build_surface_projection_event_kind_catalog()
    entries = tuple(
        build_surface_projection_event_envelope_entry(kind)
        for kind in SurfaceProjectionEventKind
    )
    payload: dict[str, Any] = {
        "registry_id": "p2_6_c_surface_projection_event_envelope_registry",
        "section_id": P2_6_C_SECTION_ID,
        "created_for_pack": P2_6_C_PACK_ID,
        "official_section_name": P2_6_C_OFFICIAL_SECTION_NAME,
        "registry_version": P2_6_C_REGISTRY_VERSION,
        "entries": entries,
        "event_kind_catalog_ref": event_kind_catalog.catalog_id,
        "source_pack_refs": ("P2.6-A", "P2.6-B"),
        "source_section_refs": (P2_6_C_OFFICIAL_SECTION_NAME,),
        "is_event_bus": False,
        "is_dispatcher": False,
        "emits_runtime_events": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.EVENT_ENVELOPE_ONLY.value
        ),
        "limitations": (
            "Registry catalogs event-envelope contracts only",
            "registry is not an event bus, dispatcher, or runtime emitter",
        ),
    }
    registry = SurfaceProjectionEventEnvelopeRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_event_envelope_registry_is_not_dispatcher(registry)
    return registry


def build_surface_projection_subscription_descriptor() -> (
    SurfaceProjectionSubscriptionDescriptor
):
    payload: dict[str, Any] = {
        "subscription_descriptor_id": "p2_6_c_subscription_descriptor",
        "subscription_mode": SurfaceProjectionSubscriptionMode.CONTRACT_ONLY,
        "event_kind_refs": tuple(kind.value for kind in SurfaceProjectionEventKind),
        "filter_contract_ref": "P2.6-B:surface_projection_filter_contract",
        "subscriber_ref": "UNAVAILABLE:subscriber_runtime_deferred",
        "creates_subscriber_runtime": False,
        "creates_subscription_runtime": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.SUBSCRIPTION_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "Subscription descriptor is contract grammar only",
            "it creates no subscriber runtime or subscription runtime",
        ),
    }
    descriptor = SurfaceProjectionSubscriptionDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_subscription_descriptor_is_not_subscriber_runtime(descriptor)
    return descriptor


def build_surface_projection_delivery_descriptor() -> (
    SurfaceProjectionDeliveryDescriptor
):
    payload: dict[str, Any] = {
        "delivery_descriptor_id": "p2_6_c_delivery_descriptor",
        "delivery_mode": SurfaceProjectionDeliveryMode.CONTRACT_ONLY,
        "delivery_target_contract": "P2.6-C:event_delivery_target_contract_only",
        "delivery_channel_ref": "UNAVAILABLE:delivery_channel_deferred",
        "creates_delivery_channel": False,
        "creates_delivery_runtime": False,
        "sends_message": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.DELIVERY_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "Delivery descriptor is contract grammar only",
            "it creates no delivery channel/runtime and sends no message",
        ),
    }
    descriptor = SurfaceProjectionDeliveryDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_delivery_descriptor_is_not_delivery_channel(descriptor)
    return descriptor


def build_surface_projection_no_live_stream_boundary(
    subscription_descriptor: SurfaceProjectionSubscriptionDescriptor | None = None,
    delivery_descriptor: SurfaceProjectionDeliveryDescriptor | None = None,
) -> SurfaceProjectionNoLiveStreamBoundary:
    if subscription_descriptor is None:
        subscription_descriptor = build_surface_projection_subscription_descriptor()
    if delivery_descriptor is None:
        delivery_descriptor = build_surface_projection_delivery_descriptor()
    payload: dict[str, Any] = {
        "boundary_id": "p2_6_c_surface_projection_no_live_stream_boundary",
        "boundary_active": True,
        "subscription_descriptor_ref": (
            subscription_descriptor.subscription_descriptor_id
        ),
        "delivery_descriptor_ref": delivery_descriptor.delivery_descriptor_id,
        "prevents_websocket": True,
        "prevents_sse": True,
        "prevents_live_stream": True,
        "prevents_subscriber_runtime": True,
        "prevents_delivery_runtime": True,
        "reason": NO_LIVE_STREAM_REASON,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.NO_LIVE_STREAM_BOUNDARY.value
        ),
        "limitations": (
            "Boundary is a safety firewall over descriptors only",
            "it does not implement websocket, SSE, or live stream delivery",
        ),
    }
    boundary = SurfaceProjectionNoLiveStreamBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_live_stream_boundary_is_active(boundary)
    return boundary


def build_surface_projection_no_runtime_dispatch_boundary(
    event_registry: SurfaceProjectionEventEnvelopeRegistry | None = None,
    event_kind_catalog: SurfaceProjectionEventKindCatalog | None = None,
) -> SurfaceProjectionNoRuntimeDispatchBoundary:
    if event_kind_catalog is None:
        event_kind_catalog = build_surface_projection_event_kind_catalog()
    if event_registry is None:
        event_registry = build_surface_projection_event_envelope_registry(
            event_kind_catalog
        )
    payload: dict[str, Any] = {
        "boundary_id": "p2_6_c_surface_projection_no_runtime_dispatch_boundary",
        "boundary_active": True,
        "event_registry_ref": event_registry.registry_id,
        "event_kind_catalog_ref": event_kind_catalog.catalog_id,
        "prevents_event_bus": True,
        "prevents_event_dispatcher": True,
        "prevents_event_dispatch": True,
        "prevents_runtime_event_emission": True,
        "prevents_runtime_bridge": True,
        "prevents_runtime_dispatch": True,
        "prevents_api_event_bridge_runtime": True,
        "prevents_trace_write": True,
        "reason": NO_RUNTIME_DISPATCH_REASON,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.NO_RUNTIME_DISPATCH_BOUNDARY.value
        ),
        "limitations": (
            "Boundary is a safety firewall over event contracts only",
            "it does not implement event bus, dispatcher, bridge, or trace write",
        ),
    }
    boundary = SurfaceProjectionNoRuntimeDispatchBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_runtime_dispatch_boundary_is_active(boundary)
    return boundary


def build_surface_projection_event_bridge_boundary_result(
    event_bridge_gate: SurfaceProjectionEventBridgeGate | None = None,
    event_envelope_registry: SurfaceProjectionEventEnvelopeRegistry | None = None,
    event_kind_catalog: SurfaceProjectionEventKindCatalog | None = None,
    payload_schema_refs: tuple[SurfaceProjectionEventPayloadSchemaRef, ...] | None = None,
    source_target_mappings: (
        tuple[SurfaceProjectionEventSourceTargetMapping, ...] | None
    ) = None,
    causality_refs: tuple[SurfaceProjectionEventCausalityRef, ...] | None = None,
    correlation_refs: tuple[SurfaceProjectionEventCorrelationRef, ...] | None = None,
    evidence_refs: tuple[SurfaceProjectionEventEvidenceRef, ...] | None = None,
    subscription_descriptor: SurfaceProjectionSubscriptionDescriptor | None = None,
    delivery_descriptor: SurfaceProjectionDeliveryDescriptor | None = None,
    no_live_stream_boundary: SurfaceProjectionNoLiveStreamBoundary | None = None,
    no_runtime_dispatch_boundary: (
        SurfaceProjectionNoRuntimeDispatchBoundary | None
    ) = None,
) -> SurfaceProjectionEventBridgeBoundaryResult:
    if event_bridge_gate is None:
        event_bridge_gate = build_surface_projection_event_bridge_gate()
    if event_kind_catalog is None:
        event_kind_catalog = build_surface_projection_event_kind_catalog()
    if event_envelope_registry is None:
        event_envelope_registry = build_surface_projection_event_envelope_registry(
            event_kind_catalog
        )
    if payload_schema_refs is None:
        payload_schema_refs = tuple(
            build_surface_projection_event_payload_schema_ref(kind)
            for kind in SurfaceProjectionEventKind
        )
    if source_target_mappings is None:
        source_target_mappings = tuple(
            build_surface_projection_event_source_target_mapping(kind)
            for kind in SurfaceProjectionEventKind
        )
    if causality_refs is None:
        causality_refs = tuple(
            build_surface_projection_event_causality_ref(kind)
            for kind in SurfaceProjectionEventKind
        )
    if correlation_refs is None:
        correlation_refs = tuple(
            build_surface_projection_event_correlation_ref(kind)
            for kind in SurfaceProjectionEventKind
        )
    if evidence_refs is None:
        evidence_refs = tuple(
            build_surface_projection_event_evidence_ref(kind)
            for kind in SurfaceProjectionEventKind
        )
    if subscription_descriptor is None:
        subscription_descriptor = build_surface_projection_subscription_descriptor()
    if delivery_descriptor is None:
        delivery_descriptor = build_surface_projection_delivery_descriptor()
    if no_live_stream_boundary is None:
        no_live_stream_boundary = build_surface_projection_no_live_stream_boundary(
            subscription_descriptor,
            delivery_descriptor,
        )
    if no_runtime_dispatch_boundary is None:
        no_runtime_dispatch_boundary = (
            build_surface_projection_no_runtime_dispatch_boundary(
                event_envelope_registry,
                event_kind_catalog,
            )
        )
    payload: dict[str, Any] = {
        "event_bridge_boundary_result_id": (
            "p2_6_c_surface_projection_event_bridge_boundary_result"
        ),
        "section_id": P2_6_C_SECTION_ID,
        "created_for_pack": P2_6_C_PACK_ID,
        "official_section_name": P2_6_C_OFFICIAL_SECTION_NAME,
        "event_bridge_gate": event_bridge_gate,
        "event_envelope_registry": event_envelope_registry,
        "event_kind_catalog": event_kind_catalog,
        "payload_schema_refs": payload_schema_refs,
        "source_target_mappings": source_target_mappings,
        "causality_refs": causality_refs,
        "correlation_refs": correlation_refs,
        "evidence_refs": evidence_refs,
        "subscription_descriptor": subscription_descriptor,
        "delivery_descriptor": delivery_descriptor,
        "no_live_stream_boundary": no_live_stream_boundary,
        "no_runtime_dispatch_boundary": no_runtime_dispatch_boundary,
        "creates_event_bus": False,
        "creates_event_dispatcher": False,
        "creates_event_dispatch": False,
        "creates_subscriber_runtime": False,
        "creates_delivery_runtime": False,
        "creates_live_stream": False,
        "creates_runtime_event_emission": False,
        "creates_runtime_bridge": False,
        "creates_runtime_dispatch": False,
        "creates_api_event_bridge_runtime": False,
        "writes_trace": False,
        "writes_memory": False,
        "writes_storage": False,
        "creates_cli_binding": False,
        "creates_product_behavior": False,
        "truth_label": (
            SurfaceProjectionEventBridgeTruthBoundary.EVENT_BRIDGE_BOUNDARY_RESULT_ONLY.value
        ),
        "limitations": (
            "Event bridge boundary result bundles event contracts only",
            "it creates no bus, dispatcher, stream, bridge, trace write, or CLI",
        ),
    }
    result = SurfaceProjectionEventBridgeBoundaryResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_no_live_stream_boundary_is_active(result.no_live_stream_boundary)
    assert_no_runtime_dispatch_boundary_is_active(
        result.no_runtime_dispatch_boundary
    )
    return result


def build_p2_6_c_side_effect_proof() -> P26CSideEffectProof:
    return P26CSideEffectProof()


def build_p2_6_c_surface_projection_event_bridge_result() -> (
    P26CSurfaceProjectionEventBridgeResult
):
    gate = build_surface_projection_event_bridge_gate()
    catalog = build_surface_projection_event_kind_catalog()
    registry = build_surface_projection_event_envelope_registry(catalog)
    payload_refs = tuple(
        build_surface_projection_event_payload_schema_ref(kind)
        for kind in SurfaceProjectionEventKind
    )
    mappings = tuple(
        build_surface_projection_event_source_target_mapping(kind)
        for kind in SurfaceProjectionEventKind
    )
    causality_refs = tuple(
        build_surface_projection_event_causality_ref(kind)
        for kind in SurfaceProjectionEventKind
    )
    correlation_refs = tuple(
        build_surface_projection_event_correlation_ref(kind)
        for kind in SurfaceProjectionEventKind
    )
    evidence_refs = tuple(
        build_surface_projection_event_evidence_ref(kind)
        for kind in SurfaceProjectionEventKind
    )
    subscription = build_surface_projection_subscription_descriptor()
    delivery = build_surface_projection_delivery_descriptor()
    live_stream_boundary = build_surface_projection_no_live_stream_boundary(
        subscription,
        delivery,
    )
    runtime_dispatch_boundary = build_surface_projection_no_runtime_dispatch_boundary(
        registry,
        catalog,
    )
    boundary_result = build_surface_projection_event_bridge_boundary_result(
        event_bridge_gate=gate,
        event_envelope_registry=registry,
        event_kind_catalog=catalog,
        payload_schema_refs=payload_refs,
        source_target_mappings=mappings,
        causality_refs=causality_refs,
        correlation_refs=correlation_refs,
        evidence_refs=evidence_refs,
        subscription_descriptor=subscription,
        delivery_descriptor=delivery,
        no_live_stream_boundary=live_stream_boundary,
        no_runtime_dispatch_boundary=runtime_dispatch_boundary,
    )
    proof = build_p2_6_c_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "pack_id": P2_6_C_PACK_ID,
        "section_id": P2_6_C_SECTION_ID,
        "official_section_name": P2_6_C_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_6_C_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_6_C_DEPENDENCY_PACK,
        "event_bridge_gate": gate,
        "event_envelope_registry": registry,
        "event_kind_catalog": catalog,
        "payload_schema_refs": payload_refs,
        "source_target_mappings": mappings,
        "causality_refs": causality_refs,
        "correlation_refs": correlation_refs,
        "evidence_refs": evidence_refs,
        "subscription_descriptor": subscription,
        "delivery_descriptor": delivery,
        "no_live_stream_boundary": live_stream_boundary,
        "no_runtime_dispatch_boundary": runtime_dispatch_boundary,
        "event_bridge_boundary_result": boundary_result,
        "truth_labels": tuple(
            label.value for label in SurfaceProjectionEventBridgeTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": proof,
        "next_pack": P2_6_C_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P26CSurfaceProjectionEventBridgeResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_6_c_does_not_start_future_work(result)
    assert_p2_6_c_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_6_c_result(
    result: P26CSurfaceProjectionEventBridgeResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_c_surface_projection_event_bridge_result()
    return to_canonical_json(result.to_canonical_dict())


def render_surface_projection_event_contract_summary(
    result: P26CSurfaceProjectionEventBridgeResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_c_surface_projection_event_bridge_result()
    return (
        f"{result.pack_id} {result.official_section_name}: "
        f"{len(result.event_envelope_registry.entries)} event envelope entries; "
        f"no_live_stream={result.no_live_stream_boundary.boundary_active}; "
        f"no_runtime_dispatch={result.no_runtime_dispatch_boundary.boundary_active}; "
        f"next={result.next_pack}; live={result.claims_live}"
    )


def assert_event_envelope_is_not_runtime_event(
    entry: SurfaceProjectionEventEnvelopeEntry,
) -> None:
    if entry.available_as_runtime_event:
        _reject(
            "Event envelope entry must not be runtime event",
            field="available_as_runtime_event",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_event_kind_catalog_is_not_event_bus(
    catalog: SurfaceProjectionEventKindCatalog,
) -> None:
    if catalog.is_event_bus or catalog.is_dispatcher:
        _reject(
            "Event kind catalog must not be event bus or dispatcher",
            field="is_event_bus",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_event_envelope_registry_is_not_dispatcher(
    registry: SurfaceProjectionEventEnvelopeRegistry,
) -> None:
    if registry.is_event_bus or registry.is_dispatcher or registry.emits_runtime_events:
        _reject(
            "Event envelope registry must not be event bus/dispatcher/emitter",
            field="is_dispatcher",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_subscription_descriptor_is_not_subscriber_runtime(
    descriptor: SurfaceProjectionSubscriptionDescriptor,
) -> None:
    if (
        descriptor.creates_subscriber_runtime
        or descriptor.creates_subscription_runtime
    ):
        _reject(
            "Subscription descriptor must not create subscriber/subscription runtime",
            field="creates_subscriber_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_delivery_descriptor_is_not_delivery_channel(
    descriptor: SurfaceProjectionDeliveryDescriptor,
) -> None:
    if (
        descriptor.creates_delivery_channel
        or descriptor.creates_delivery_runtime
        or descriptor.sends_message
    ):
        _reject(
            "Delivery descriptor must not create delivery runtime or send messages",
            field="creates_delivery_channel",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_causality_ref_is_not_trace_write(
    ref: SurfaceProjectionEventCausalityRef,
) -> None:
    if ref.writes_trace or ref.creates_trace_event or ref.claims_trace_verified:
        _reject(
            "Causality ref must not write trace or claim TRACE_VERIFIED",
            field="writes_trace",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_evidence_ref_is_not_trace_verified(
    ref: SurfaceProjectionEventEvidenceRef,
) -> None:
    if ref.claims_trace_verified or ref.writes_trace:
        _reject(
            "Evidence ref must not claim TRACE_VERIFIED or write trace",
            field="claims_trace_verified",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_live_stream_boundary_is_active(
    boundary: SurfaceProjectionNoLiveStreamBoundary,
) -> None:
    if not boundary.boundary_active:
        _reject(
            "No-live-stream boundary must be active",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    required = (
        boundary.prevents_websocket,
        boundary.prevents_sse,
        boundary.prevents_live_stream,
        boundary.prevents_subscriber_runtime,
        boundary.prevents_delivery_runtime,
    )
    if not all(required):
        _reject(
            "No-live-stream boundary must prevent all live stream paths",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_runtime_dispatch_boundary_is_active(
    boundary: SurfaceProjectionNoRuntimeDispatchBoundary,
) -> None:
    if not boundary.boundary_active:
        _reject(
            "No-runtime-dispatch boundary must be active",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    required = (
        boundary.prevents_event_bus,
        boundary.prevents_event_dispatcher,
        boundary.prevents_event_dispatch,
        boundary.prevents_runtime_event_emission,
        boundary.prevents_runtime_bridge,
        boundary.prevents_runtime_dispatch,
        boundary.prevents_api_event_bridge_runtime,
        boundary.prevents_trace_write,
    )
    if not all(required):
        _reject(
            "No-runtime-dispatch boundary must prevent all dispatch paths",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_6_c_does_not_start_future_work(
    result: P26CSurfaceProjectionEventBridgeResult,
) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or proof.p2_6_d_started
        or proof.p2_7_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.6-C must not start P2.6-D/P2.7/P2.10/P2.13",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.next_pack != P2_6_C_NEXT_PACK:
        _reject(
            "P2.6-C next pack must be P2.6-D",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_6_c_side_effects_all_false(proof: P26CSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.6-C side-effect proof field must remain false: {field.name}",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
