"""P2.6-B surface projection schema / read-model expansion contracts.

Contract-only schema expansion over the P2.6-A projection/API/event bridge
foundation. This module defines read-model registry, schema inventory,
surface-specific schemas, API-shaped response/error envelopes, static query
grammar, and a no-live-endpoint boundary.

Core law:
  - Projection schema is not UI.
  - Projection registry is not source-of-truth.
  - Schema inventory is not storage.
  - API response envelope is not live HTTP response.
  - API error envelope is not runtime error handler.
  - Query/filter/sort/pagination contracts do not execute.
  - P2.6-B schema expansion result is not a live endpoint.
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
from .surface_projection_foundation import (
    OFFICIAL_ACTIVE_SURFACE_NAMES,
    P2_6_A_OFFICIAL_SECTION_NAME,
    P2_6_A_PACK_ID,
    P2_6_A_REPORT_PATH,
    P2_6_A_SECTION_ID,
    P26ASurfaceProjectionResult,
    build_p2_6_a_surface_projection_result,
)
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_6_B_PACK_ID = "P2.6-B"
P2_6_B_SECTION_ID = P2_6_A_SECTION_ID
P2_6_B_OFFICIAL_SECTION_NAME = P2_6_A_OFFICIAL_SECTION_NAME
P2_6_B_DEPENDENCY_PACK = P2_6_A_PACK_ID
P2_6_B_NEXT_PACK = "P2.6-C"
P2_6_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.6.6",
    "P2.6.7",
    "P2.6.8",
    "P2.6.9",
    "P2.6.10",
)
P2_6_B_REPORT_FILENAME = "P2_6_B_SURFACE_PROJECTION_SCHEMA_EXPANSION.md"
P2_6_B_REPORT_PATH = f"agent/reports/{P2_6_B_REPORT_FILENAME}"
P2_6_A_COMMIT_REF = "414243a278048660323065e5dae7a0b2f65ffd05"
P2_6_A_REPORT_HASH_COMMIT_REF = "fa561c9"

P2_6_B_GATE_VERSION = "p2_6_b_surface_projection_schema_gate.v1"
P2_6_B_REGISTRY_VERSION = "p2_6_b_surface_projection_read_model_registry.v1"
P2_6_B_INVENTORY_VERSION = "p2_6_b_surface_projection_schema_inventory.v1"
P2_6_B_SURFACE_SCHEMA_VERSION = "surface_projection.schema.v1"
P2_6_B_RESPONSE_ENVELOPE_VERSION = "surface_projection.response_envelope.v1"
P2_6_B_ERROR_ENVELOPE_VERSION = "surface_projection.error_envelope.v1"
P2_6_B_QUERY_CONTRACT_VERSION = "surface_projection.query_contract.v1"
P2_6_B_FILTER_CONTRACT_VERSION = "surface_projection.filter_contract.v1"
P2_6_B_SORT_CONTRACT_VERSION = "surface_projection.sort_contract.v1"
P2_6_B_PAGINATION_CONTRACT_VERSION = "surface_projection.pagination_contract.v1"
P2_6_B_NO_LIVE_ENDPOINT_BOUNDARY_VERSION = (
    "p2_6_b_surface_projection_no_live_endpoint_boundary.v1"
)
P2_6_B_SCHEMA_EXPANSION_RESULT_VERSION = (
    "p2_6_b_surface_projection_schema_expansion_result.v1"
)
P2_6_B_RESULT_VERSION = "p2_6_b_surface_projection_schema_result.v1"

NO_LIVE_ENDPOINT_REASON = (
    "P2.6-B defines projection read-model/API schema contracts only. No API "
    "server, HTTP route, route handler, live endpoint, live query, database "
    "query runtime, storage query runtime, or runtime bridge exists in this "
    "repo scope."
)


class SurfaceProjectionSchemaGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class SurfaceProjectionSchemaKind(str, Enum):
    SURFACE_REGISTRY_SCHEMA = "SURFACE_REGISTRY_SCHEMA"
    LOCAL_NAVIGATION_SCHEMA = "LOCAL_NAVIGATION_SCHEMA"
    WINDOW_STATE_SCHEMA = "WINDOW_STATE_SCHEMA"
    COMMAND_PALETTE_SCHEMA = "COMMAND_PALETTE_SCHEMA"
    CROSS_SURFACE_HANDOFF_SCHEMA = "CROSS_SURFACE_HANDOFF_SCHEMA"
    SECTION_SEAL_SCHEMA = "SECTION_SEAL_SCHEMA"
    DEV_FIXTURE_SCHEMA = "DEV_FIXTURE_SCHEMA"
    UNKNOWN_UNAVAILABLE = "UNKNOWN_UNAVAILABLE"


class SurfaceProjectionResponseStatus(str, Enum):
    OK_CONTRACT_ONLY = "OK_CONTRACT_ONLY"
    PARTIAL_CONTRACT_ONLY = "PARTIAL_CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR_CONTRACT_ONLY = "ERROR_CONTRACT_ONLY"


class SurfaceProjectionQueryMode(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_QUERYABLE = "NOT_QUERYABLE"


class SurfaceProjectionSchemaTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    API_SCHEMA_ONLY = "API_SCHEMA_ONLY"
    RESPONSE_ENVELOPE_ONLY = "RESPONSE_ENVELOPE_ONLY"
    ERROR_ENVELOPE_ONLY = "ERROR_ENVELOPE_ONLY"
    QUERY_CONTRACT_ONLY = "QUERY_CONTRACT_ONLY"
    FILTER_CONTRACT_ONLY = "FILTER_CONTRACT_ONLY"
    SORT_CONTRACT_ONLY = "SORT_CONTRACT_ONLY"
    PAGINATION_CONTRACT_ONLY = "PAGINATION_CONTRACT_ONLY"
    NO_LIVE_ENDPOINT_BOUNDARY = "NO_LIVE_ENDPOINT_BOUNDARY"
    NO_SERVER_BOUNDARY = "NO_SERVER_BOUNDARY"
    NO_ROUTE_HANDLER_BOUNDARY = "NO_ROUTE_HANDLER_BOUNDARY"
    NO_LIVE_QUERY_BOUNDARY = "NO_LIVE_QUERY_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_UI = "NOT_UI"
    NOT_API_SERVER = "NOT_API_SERVER"
    NOT_HTTP_ROUTE = "NOT_HTTP_ROUTE"
    NOT_ROUTE_HANDLER = "NOT_ROUTE_HANDLER"
    NOT_LIVE_ENDPOINT = "NOT_LIVE_ENDPOINT"
    NOT_LIVE_QUERY = "NOT_LIVE_QUERY"
    NOT_DATABASE_QUERY = "NOT_DATABASE_QUERY"
    NOT_STORAGE_QUERY = "NOT_STORAGE_QUERY"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_EVENT_BUS = "NOT_EVENT_BUS"
    NOT_EVENT_DISPATCH = "NOT_EVENT_DISPATCH"
    NOT_RUNTIME_BRIDGE = "NOT_RUNTIME_BRIDGE"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
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
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    SCHEMA_GATE_ONLY = "SCHEMA_GATE_ONLY"
    READ_MODEL_REGISTRY_ONLY = "READ_MODEL_REGISTRY_ONLY"
    SCHEMA_INVENTORY_ONLY = "SCHEMA_INVENTORY_ONLY"
    SURFACE_SCHEMA_ONLY = "SURFACE_SCHEMA_ONLY"
    SCHEMA_EXPANSION_RESULT_ONLY = "SCHEMA_EXPANSION_RESULT_ONLY"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_STORAGE = "NOT_STORAGE"
    NOT_HTTP_RESPONSE = "NOT_HTTP_RESPONSE"
    NOT_RUNTIME_ERROR_HANDLER = "NOT_RUNTIME_ERROR_HANDLER"


@dataclass(frozen=True)
class SurfaceProjectionSchemaGate(_CanonicalMixin):
    gate_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_foundation_result_ref: str
    dependency_no_server_boundary_ref: str
    dependency_no_event_bus_boundary_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: SurfaceProjectionSchemaGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfaceProjectionReadModelEntry(_CanonicalMixin):
    entry_id: str
    schema_kind: SurfaceProjectionSchemaKind
    schema_ref: str
    source_contract_ref: str
    surface_scope_ref: str
    available_as_contract: bool
    available_as_live_endpoint: bool
    requires_future_pack: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class SurfaceProjectionReadModelRegistry(_CanonicalMixin):
    registry_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_version: str
    entries: tuple[SurfaceProjectionReadModelEntry, ...]
    source_pack_refs: tuple[str, ...]
    source_section_refs: tuple[str, ...]
    duplicates_source_of_truth: bool
    is_source_of_truth: bool
    is_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSchemaVersion(_CanonicalMixin):
    schema_version_id: str
    schema_name: str
    schema_version: str
    schema_kind: SurfaceProjectionSchemaKind
    compatible_pack: str
    source_contract_ref: str
    breaking_change: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSchemaInventory(_CanonicalMixin):
    inventory_id: str
    section_id: str
    created_for_pack: str
    schema_versions: tuple[SurfaceProjectionSchemaVersion, ...]
    schema_refs: tuple[str, ...]
    source_contract_refs: tuple[str, ...]
    missing_schemas: tuple[str, ...]
    duplicates_source_of_truth: bool
    is_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class SurfaceSpecificProjectionSchema(_CanonicalMixin):
    schema_id: str
    schema_kind: SurfaceProjectionSchemaKind
    surface_ids: tuple[str, ...]
    official_surface_set: tuple[str, ...]
    source_contract_refs: tuple[str, ...]
    fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    unavailable_fields: tuple[str, ...]
    is_ui_schema: bool
    is_product_schema: bool
    duplicates_source_of_truth: bool
    mutates_state: bool
    truth_label: str
    limitations: tuple[str, ...]
    schema_hash: str


@dataclass(frozen=True)
class SurfaceProjectionResponseEnvelope(_CanonicalMixin):
    response_envelope_id: str
    schema_version: str
    status: SurfaceProjectionResponseStatus
    data_schema_ref: str
    error_schema_ref: str
    meta: tuple[str, ...]
    pagination_ref: str
    query_ref: str
    is_http_response: bool
    requires_server: bool
    requires_route_handler: bool
    truth_label: str
    limitations: tuple[str, ...]
    envelope_hash: str


@dataclass(frozen=True)
class SurfaceProjectionErrorEnvelope(_CanonicalMixin):
    error_envelope_id: str
    schema_version: str
    status: SurfaceProjectionResponseStatus
    error_code: str
    error_kind: str
    message_contract: str
    details_schema_ref: str
    is_runtime_error_handler: bool
    throws_exception: bool
    writes_trace: bool
    truth_label: str
    limitations: tuple[str, ...]
    envelope_hash: str


@dataclass(frozen=True)
class SurfaceProjectionFilterContract(_CanonicalMixin):
    filter_contract_id: str
    allowed_filter_fields: tuple[str, ...]
    filter_operator_contracts: tuple[str, ...]
    executes_filter: bool
    filters_runtime_state: bool
    filters_database: bool
    truth_label: str
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSortContract(_CanonicalMixin):
    sort_contract_id: str
    allowed_sort_fields: tuple[str, ...]
    sort_direction_contract: tuple[str, ...]
    executes_sort: bool
    sorts_runtime_state: bool
    sorts_database: bool
    truth_label: str
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceProjectionPaginationContract(_CanonicalMixin):
    pagination_contract_id: str
    pagination_mode: str
    page_size_contract: str
    cursor_contract: str
    offset_contract: str
    executes_pagination: bool
    paginates_runtime_state: bool
    paginates_database: bool
    truth_label: str
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceProjectionQueryContract(_CanonicalMixin):
    query_contract_id: str
    query_mode: SurfaceProjectionQueryMode
    allowed_query_fields: tuple[str, ...]
    filter_contract_ref: str
    sort_contract_ref: str
    pagination_contract_ref: str
    executes_live_query: bool
    queries_runtime_state: bool
    queries_database: bool
    queries_storage: bool
    truth_label: str
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class SurfaceProjectionNoLiveEndpointBoundary(_CanonicalMixin):
    boundary_id: str
    boundary_active: bool
    response_envelope_ref: str
    query_contract_ref: str
    prevents_api_server: bool
    prevents_http_routes: bool
    prevents_route_handlers: bool
    prevents_live_endpoint: bool
    prevents_live_query: bool
    prevents_database_query_runtime: bool
    prevents_storage_query_runtime: bool
    prevents_runtime_bridge: bool
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSchemaExpansionResult(_CanonicalMixin):
    schema_expansion_result_id: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    schema_gate: SurfaceProjectionSchemaGate
    read_model_registry: SurfaceProjectionReadModelRegistry
    schema_inventory: SurfaceProjectionSchemaInventory
    surface_schemas: tuple[SurfaceSpecificProjectionSchema, ...]
    response_envelope: SurfaceProjectionResponseEnvelope
    error_envelope: SurfaceProjectionErrorEnvelope
    query_contract: SurfaceProjectionQueryContract
    filter_contract: SurfaceProjectionFilterContract
    sort_contract: SurfaceProjectionSortContract
    pagination_contract: SurfaceProjectionPaginationContract
    no_live_endpoint_boundary: SurfaceProjectionNoLiveEndpointBoundary
    creates_api_server: bool
    creates_http_routes: bool
    creates_route_handlers: bool
    creates_live_endpoint: bool
    creates_live_query: bool
    creates_database_query_runtime: bool
    creates_event_bus: bool
    creates_runtime_bridge: bool
    creates_cli_binding: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    result_hash: str


@dataclass(frozen=True)
class P26BSideEffectProof(_CanonicalMixin):
    projection_ui_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    route_handler_created: bool = False
    live_endpoint_created: bool = False
    live_query_execution_created: bool = False
    database_query_runtime_created: bool = False
    storage_query_runtime_created: bool = False
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
    p2_6_c_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class P26BSurfaceProjectionSchemaResult(_CanonicalMixin):
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    schema_gate: SurfaceProjectionSchemaGate
    read_model_registry: SurfaceProjectionReadModelRegistry
    schema_inventory: SurfaceProjectionSchemaInventory
    surface_schemas: tuple[SurfaceSpecificProjectionSchema, ...]
    response_envelope: SurfaceProjectionResponseEnvelope
    error_envelope: SurfaceProjectionErrorEnvelope
    query_contract: SurfaceProjectionQueryContract
    filter_contract: SurfaceProjectionFilterContract
    sort_contract: SurfaceProjectionSortContract
    pagination_contract: SurfaceProjectionPaginationContract
    no_live_endpoint_boundary: SurfaceProjectionNoLiveEndpointBoundary
    schema_expansion_result: SurfaceProjectionSchemaExpansionResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P26BSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _schema_ref(kind: SurfaceProjectionSchemaKind) -> str:
    return f"surface_projection/{kind.value.lower()}:v1(contract-only)"


def _source_contract_ref(kind: SurfaceProjectionSchemaKind) -> str:
    refs = {
        SurfaceProjectionSchemaKind.SURFACE_REGISTRY_SCHEMA: "P2.1-A:SurfaceRegistry",
        SurfaceProjectionSchemaKind.LOCAL_NAVIGATION_SCHEMA: (
            "P2.2-D:P22LocalNavigationProjectionContract"
        ),
        SurfaceProjectionSchemaKind.WINDOW_STATE_SCHEMA: (
            "P2.3-D:WorkspaceWindowSectionProjection"
        ),
        SurfaceProjectionSchemaKind.COMMAND_PALETTE_SCHEMA: (
            "P2.4-D:GlobalCommandSectionProjection"
        ),
        SurfaceProjectionSchemaKind.CROSS_SURFACE_HANDOFF_SCHEMA: (
            "P2.5-D:CrossSurfaceHandoffSectionProjection"
        ),
        SurfaceProjectionSchemaKind.SECTION_SEAL_SCHEMA: (
            "P2.5-D:CrossSurfaceHandoffSectionSeal"
        ),
        SurfaceProjectionSchemaKind.DEV_FIXTURE_SCHEMA: (
            "P2.6-B:deterministic_schema_fixture"
        ),
        SurfaceProjectionSchemaKind.UNKNOWN_UNAVAILABLE: "UNAVAILABLE:unknown_schema",
    }
    return refs[kind]


def build_surface_projection_schema_gate(
    foundation_result: P26ASurfaceProjectionResult | None = None,
) -> SurfaceProjectionSchemaGate:
    if foundation_result is None:
        foundation_result = build_p2_6_a_surface_projection_result()
    payload: dict[str, Any] = {
        "gate_id": "p2_6_b_surface_projection_schema_gate",
        "section_id": P2_6_B_SECTION_ID,
        "created_for_pack": P2_6_B_PACK_ID,
        "official_section_name": P2_6_B_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_6_B_DEPENDENCY_PACK,
        "dependency_report_ref": P2_6_A_REPORT_PATH,
        "dependency_commit_ref": P2_6_A_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.6-A",
        "dependency_foundation_result_ref": (
            foundation_result.foundation_result.foundation_result_id
        ),
        "dependency_no_server_boundary_ref": (
            foundation_result.no_server_boundary.boundary_id
        ),
        "dependency_no_event_bus_boundary_ref": (
            foundation_result.no_event_bus_boundary.boundary_id
        ),
        "dependency_side_effect_proof_ref": "P26ASideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": SurfaceProjectionSchemaGateStatus.READY,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.SCHEMA_GATE_ONLY.value,
        "limitations": (
            "P2.6-A repo evidence remains the hard start gate",
            "OMNI evidence is ignored only by explicit operator instruction",
            "schema gate does not create API endpoints or live query runtime",
        ),
    }
    gate = SurfaceProjectionSchemaGate(**payload, gate_hash=_hash_payload(payload))
    if gate.dependency_pack != P2_6_A_PACK_ID:
        _reject(
            "P2.6-B schema gate must depend on P2.6-A",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return gate


def build_surface_projection_read_model_registry() -> (
    SurfaceProjectionReadModelRegistry
):
    entries = tuple(
        build_surface_projection_read_model_entry(kind)
        for kind in SurfaceProjectionSchemaKind
    )
    payload: dict[str, Any] = {
        "registry_id": "p2_6_b_surface_projection_read_model_registry",
        "section_id": P2_6_B_SECTION_ID,
        "created_for_pack": P2_6_B_PACK_ID,
        "official_section_name": P2_6_B_OFFICIAL_SECTION_NAME,
        "registry_version": P2_6_B_REGISTRY_VERSION,
        "entries": entries,
        "source_pack_refs": ("P2.1-A", "P2.2-D", "P2.3-D", "P2.4-D", "P2.5-D", "P2.6-A"),
        "source_section_refs": (
            "Global Topbar / Surface Registry",
            "Per-Surface Local Navigation",
            "Floating Windows / Workspace State",
            "Command Palette / Global Commands",
            "Cross-Surface Handoff",
            P2_6_B_OFFICIAL_SECTION_NAME,
        ),
        "duplicates_source_of_truth": False,
        "is_source_of_truth": False,
        "is_storage": False,
        "truth_label": (
            SurfaceProjectionSchemaTruthBoundary.READ_MODEL_REGISTRY_ONLY.value
        ),
        "limitations": (
            "Registry catalogs projection read-model schemas only",
            "registry does not own state, persist state, or duplicate canon",
        ),
    }
    registry = SurfaceProjectionReadModelRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_schema_registry_is_not_source_of_truth(registry)
    return registry


def build_surface_projection_read_model_entry(
    schema_kind: SurfaceProjectionSchemaKind,
) -> SurfaceProjectionReadModelEntry:
    future_pack = ""
    if schema_kind is SurfaceProjectionSchemaKind.UNKNOWN_UNAVAILABLE:
        future_pack = "P2.6-C/P2.7/P2.10/P2.13"
    payload: dict[str, Any] = {
        "entry_id": f"p2_6_b_read_model_entry_{schema_kind.value.lower()}",
        "schema_kind": schema_kind,
        "schema_ref": _schema_ref(schema_kind),
        "source_contract_ref": _source_contract_ref(schema_kind),
        "surface_scope_ref": "P2.6-A:SurfaceProjectionScope",
        "available_as_contract": schema_kind
        is not SurfaceProjectionSchemaKind.UNKNOWN_UNAVAILABLE,
        "available_as_live_endpoint": False,
        "requires_future_pack": future_pack,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": (
            "Read-model entry is contract inventory metadata only",
            "entry is not a live endpoint and does not dispatch queries",
        ),
    }
    entry = SurfaceProjectionReadModelEntry(**payload, entry_hash=_hash_payload(payload))
    if entry.available_as_live_endpoint:
        _reject(
            "Read-model entry must not be available as live endpoint",
            field="available_as_live_endpoint",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    return entry


def build_surface_projection_schema_inventory() -> SurfaceProjectionSchemaInventory:
    versions = tuple(
        build_surface_projection_schema_version(kind)
        for kind in SurfaceProjectionSchemaKind
    )
    payload: dict[str, Any] = {
        "inventory_id": "p2_6_b_surface_projection_schema_inventory",
        "section_id": P2_6_B_SECTION_ID,
        "created_for_pack": P2_6_B_PACK_ID,
        "schema_versions": versions,
        "schema_refs": tuple(version.schema_version_id for version in versions),
        "source_contract_refs": tuple(
            version.source_contract_ref for version in versions
        ),
        "missing_schemas": (),
        "duplicates_source_of_truth": False,
        "is_storage": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.SCHEMA_INVENTORY_ONLY.value,
        "limitations": (
            "Inventory references schemas and source contracts by ref only",
            "inventory is not storage and writes no source-of-truth state",
        ),
    }
    inventory = SurfaceProjectionSchemaInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    assert_schema_inventory_is_not_storage(inventory)
    return inventory


def build_surface_projection_schema_version(
    schema_kind: SurfaceProjectionSchemaKind,
) -> SurfaceProjectionSchemaVersion:
    payload: dict[str, Any] = {
        "schema_version_id": f"p2_6_b_schema_version_{schema_kind.value.lower()}",
        "schema_name": schema_kind.value.lower(),
        "schema_version": P2_6_B_SURFACE_SCHEMA_VERSION,
        "schema_kind": schema_kind,
        "compatible_pack": P2_6_B_PACK_ID,
        "source_contract_ref": _source_contract_ref(schema_kind),
        "breaking_change": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.API_SCHEMA_ONLY.value,
        "limitations": (
            "Schema version is deterministic contract metadata",
            "no breaking change to source contracts is introduced",
        ),
    }
    return SurfaceProjectionSchemaVersion(
        **payload,
        version_hash=_hash_payload(payload),
    )


def build_surface_specific_projection_schema(
    schema_kind: SurfaceProjectionSchemaKind,
) -> SurfaceSpecificProjectionSchema:
    fields_tuple = (
        "surface_id",
        "schema_kind",
        "schema_version",
        "source_contract_refs",
        "truth_label",
    )
    unavailable = ()
    if schema_kind is SurfaceProjectionSchemaKind.UNKNOWN_UNAVAILABLE:
        unavailable = ("live_endpoint", "live_query", "runtime_bridge")
    payload: dict[str, Any] = {
        "schema_id": f"p2_6_b_surface_schema_{schema_kind.value.lower()}",
        "schema_kind": schema_kind,
        "surface_ids": CANONICAL_SURFACE_ORDER,
        "official_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "source_contract_refs": (_source_contract_ref(schema_kind),),
        "fields": fields_tuple,
        "required_fields": ("surface_id", "schema_kind", "schema_version"),
        "optional_fields": ("source_contract_refs", "truth_label"),
        "unavailable_fields": unavailable,
        "is_ui_schema": False,
        "is_product_schema": False,
        "duplicates_source_of_truth": False,
        "mutates_state": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.SURFACE_SCHEMA_ONLY.value,
        "limitations": (
            "Surface-specific schema is contract/API shape only",
            "schema references source contracts instead of duplicating truth",
            "schema does not render UI, mutate runtime, or claim product behavior",
        ),
    }
    schema = SurfaceSpecificProjectionSchema(
        **payload,
        schema_hash=_hash_payload(payload),
    )
    assert_surface_schema_is_not_ui(schema)
    return schema


def build_default_surface_projection_schemas() -> (
    tuple[SurfaceSpecificProjectionSchema, ...]
):
    return tuple(
        build_surface_specific_projection_schema(kind)
        for kind in SurfaceProjectionSchemaKind
    )


def build_surface_projection_response_envelope() -> SurfaceProjectionResponseEnvelope:
    payload: dict[str, Any] = {
        "response_envelope_id": "p2_6_b_surface_projection_response_envelope",
        "schema_version": P2_6_B_RESPONSE_ENVELOPE_VERSION,
        "status": SurfaceProjectionResponseStatus.OK_CONTRACT_ONLY,
        "data_schema_ref": "p2_6_b_surface_projection_read_model_registry",
        "error_schema_ref": "p2_6_b_surface_projection_error_envelope",
        "meta": ("contract_only", "not_http_response", "not_live_endpoint"),
        "pagination_ref": "p2_6_b_surface_projection_pagination_contract",
        "query_ref": "p2_6_b_surface_projection_query_contract",
        "is_http_response": False,
        "requires_server": False,
        "requires_route_handler": False,
        "truth_label": (
            SurfaceProjectionSchemaTruthBoundary.RESPONSE_ENVELOPE_ONLY.value
        ),
        "limitations": (
            "Response envelope is API-shaped schema only",
            "it is not an HTTP response and requires no server or route handler",
        ),
    }
    envelope = SurfaceProjectionResponseEnvelope(
        **payload,
        envelope_hash=_hash_payload(payload),
    )
    assert_response_envelope_is_not_http_response(envelope)
    return envelope


def build_surface_projection_error_envelope() -> SurfaceProjectionErrorEnvelope:
    payload: dict[str, Any] = {
        "error_envelope_id": "p2_6_b_surface_projection_error_envelope",
        "schema_version": P2_6_B_ERROR_ENVELOPE_VERSION,
        "status": SurfaceProjectionResponseStatus.ERROR_CONTRACT_ONLY,
        "error_code": "surface_projection_contract_error",
        "error_kind": "CONTRACT_VALIDATION_ONLY",
        "message_contract": "stable non-runtime error message shape",
        "details_schema_ref": "surface_projection/error_details:v1(contract-only)",
        "is_runtime_error_handler": False,
        "throws_exception": False,
        "writes_trace": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.ERROR_ENVELOPE_ONLY.value,
        "limitations": (
            "Error envelope is schema only, not a runtime exception handler",
            "it throws no exception and writes no trace",
        ),
    }
    envelope = SurfaceProjectionErrorEnvelope(
        **payload,
        envelope_hash=_hash_payload(payload),
    )
    assert_error_envelope_is_not_runtime_error_handler(envelope)
    return envelope


def build_surface_projection_filter_contract() -> SurfaceProjectionFilterContract:
    payload: dict[str, Any] = {
        "filter_contract_id": "p2_6_b_surface_projection_filter_contract",
        "allowed_filter_fields": (
            "surface_id",
            "schema_kind",
            "truth_label",
            "available_as_contract",
        ),
        "filter_operator_contracts": ("eq", "in", "exists"),
        "executes_filter": False,
        "filters_runtime_state": False,
        "filters_database": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.FILTER_CONTRACT_ONLY.value,
        "limitations": (
            "Filter contract declares grammar only",
            "it does not filter runtime state or database records",
        ),
    }
    contract = SurfaceProjectionFilterContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_filter_sort_pagination_do_not_execute(filter_contract=contract)
    return contract


def build_surface_projection_sort_contract() -> SurfaceProjectionSortContract:
    payload: dict[str, Any] = {
        "sort_contract_id": "p2_6_b_surface_projection_sort_contract",
        "allowed_sort_fields": ("surface_id", "schema_kind", "schema_version"),
        "sort_direction_contract": ("asc", "desc"),
        "executes_sort": False,
        "sorts_runtime_state": False,
        "sorts_database": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.SORT_CONTRACT_ONLY.value,
        "limitations": (
            "Sort contract declares grammar only",
            "it does not sort runtime state or database records",
        ),
    }
    contract = SurfaceProjectionSortContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_filter_sort_pagination_do_not_execute(sort_contract=contract)
    return contract


def build_surface_projection_pagination_contract() -> (
    SurfaceProjectionPaginationContract
):
    payload: dict[str, Any] = {
        "pagination_contract_id": "p2_6_b_surface_projection_pagination_contract",
        "pagination_mode": "CURSOR_OR_OFFSET_CONTRACT_ONLY",
        "page_size_contract": "integer:min=1:max=100:default=25",
        "cursor_contract": "opaque_string_contract_only",
        "offset_contract": "integer:min=0",
        "executes_pagination": False,
        "paginates_runtime_state": False,
        "paginates_database": False,
        "truth_label": (
            SurfaceProjectionSchemaTruthBoundary.PAGINATION_CONTRACT_ONLY.value
        ),
        "limitations": (
            "Pagination contract declares grammar only",
            "it does not paginate runtime state or database records",
        ),
    }
    contract = SurfaceProjectionPaginationContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_filter_sort_pagination_do_not_execute(pagination_contract=contract)
    return contract


def build_surface_projection_query_contract(
    filter_contract: SurfaceProjectionFilterContract | None = None,
    sort_contract: SurfaceProjectionSortContract | None = None,
    pagination_contract: SurfaceProjectionPaginationContract | None = None,
) -> SurfaceProjectionQueryContract:
    if filter_contract is None:
        filter_contract = build_surface_projection_filter_contract()
    if sort_contract is None:
        sort_contract = build_surface_projection_sort_contract()
    if pagination_contract is None:
        pagination_contract = build_surface_projection_pagination_contract()
    payload: dict[str, Any] = {
        "query_contract_id": "p2_6_b_surface_projection_query_contract",
        "query_mode": SurfaceProjectionQueryMode.CONTRACT_ONLY,
        "allowed_query_fields": (
            "surface_id",
            "schema_kind",
            "schema_version",
            "truth_label",
        ),
        "filter_contract_ref": filter_contract.filter_contract_id,
        "sort_contract_ref": sort_contract.sort_contract_id,
        "pagination_contract_ref": pagination_contract.pagination_contract_id,
        "executes_live_query": False,
        "queries_runtime_state": False,
        "queries_database": False,
        "queries_storage": False,
        "truth_label": SurfaceProjectionSchemaTruthBoundary.QUERY_CONTRACT_ONLY.value,
        "limitations": (
            "Query contract is static grammar only",
            "it does not execute live queries or read runtime/database/storage",
        ),
    }
    contract = SurfaceProjectionQueryContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_query_contract_is_not_live_query(contract)
    return contract


def build_surface_projection_no_live_endpoint_boundary(
    response_envelope: SurfaceProjectionResponseEnvelope | None = None,
    query_contract: SurfaceProjectionQueryContract | None = None,
) -> SurfaceProjectionNoLiveEndpointBoundary:
    if response_envelope is None:
        response_envelope = build_surface_projection_response_envelope()
    if query_contract is None:
        query_contract = build_surface_projection_query_contract()
    payload: dict[str, Any] = {
        "boundary_id": "p2_6_b_surface_projection_no_live_endpoint_boundary",
        "boundary_active": True,
        "response_envelope_ref": response_envelope.response_envelope_id,
        "query_contract_ref": query_contract.query_contract_id,
        "prevents_api_server": True,
        "prevents_http_routes": True,
        "prevents_route_handlers": True,
        "prevents_live_endpoint": True,
        "prevents_live_query": True,
        "prevents_database_query_runtime": True,
        "prevents_storage_query_runtime": True,
        "prevents_runtime_bridge": True,
        "reason": NO_LIVE_ENDPOINT_REASON,
        "truth_label": (
            SurfaceProjectionSchemaTruthBoundary.NO_LIVE_ENDPOINT_BOUNDARY.value
        ),
        "limitations": (
            "Boundary is a safety firewall over schema contracts only",
            "it does not implement or authorize any live endpoint",
        ),
    }
    boundary = SurfaceProjectionNoLiveEndpointBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_live_endpoint_boundary_is_active(boundary)
    return boundary


def build_surface_projection_schema_expansion_result(
    schema_gate: SurfaceProjectionSchemaGate | None = None,
    read_model_registry: SurfaceProjectionReadModelRegistry | None = None,
    schema_inventory: SurfaceProjectionSchemaInventory | None = None,
    surface_schemas: tuple[SurfaceSpecificProjectionSchema, ...] | None = None,
    response_envelope: SurfaceProjectionResponseEnvelope | None = None,
    error_envelope: SurfaceProjectionErrorEnvelope | None = None,
    query_contract: SurfaceProjectionQueryContract | None = None,
    filter_contract: SurfaceProjectionFilterContract | None = None,
    sort_contract: SurfaceProjectionSortContract | None = None,
    pagination_contract: SurfaceProjectionPaginationContract | None = None,
    no_live_endpoint_boundary: SurfaceProjectionNoLiveEndpointBoundary | None = None,
) -> SurfaceProjectionSchemaExpansionResult:
    if schema_gate is None:
        schema_gate = build_surface_projection_schema_gate()
    if read_model_registry is None:
        read_model_registry = build_surface_projection_read_model_registry()
    if schema_inventory is None:
        schema_inventory = build_surface_projection_schema_inventory()
    if surface_schemas is None:
        surface_schemas = build_default_surface_projection_schemas()
    if response_envelope is None:
        response_envelope = build_surface_projection_response_envelope()
    if error_envelope is None:
        error_envelope = build_surface_projection_error_envelope()
    if filter_contract is None:
        filter_contract = build_surface_projection_filter_contract()
    if sort_contract is None:
        sort_contract = build_surface_projection_sort_contract()
    if pagination_contract is None:
        pagination_contract = build_surface_projection_pagination_contract()
    if query_contract is None:
        query_contract = build_surface_projection_query_contract(
            filter_contract,
            sort_contract,
            pagination_contract,
        )
    if no_live_endpoint_boundary is None:
        no_live_endpoint_boundary = build_surface_projection_no_live_endpoint_boundary(
            response_envelope,
            query_contract,
        )
    payload: dict[str, Any] = {
        "schema_expansion_result_id": (
            "p2_6_b_surface_projection_schema_expansion_result"
        ),
        "section_id": P2_6_B_SECTION_ID,
        "created_for_pack": P2_6_B_PACK_ID,
        "official_section_name": P2_6_B_OFFICIAL_SECTION_NAME,
        "schema_gate": schema_gate,
        "read_model_registry": read_model_registry,
        "schema_inventory": schema_inventory,
        "surface_schemas": surface_schemas,
        "response_envelope": response_envelope,
        "error_envelope": error_envelope,
        "query_contract": query_contract,
        "filter_contract": filter_contract,
        "sort_contract": sort_contract,
        "pagination_contract": pagination_contract,
        "no_live_endpoint_boundary": no_live_endpoint_boundary,
        "creates_api_server": False,
        "creates_http_routes": False,
        "creates_route_handlers": False,
        "creates_live_endpoint": False,
        "creates_live_query": False,
        "creates_database_query_runtime": False,
        "creates_event_bus": False,
        "creates_runtime_bridge": False,
        "creates_cli_binding": False,
        "creates_product_behavior": False,
        "truth_label": (
            SurfaceProjectionSchemaTruthBoundary.SCHEMA_EXPANSION_RESULT_ONLY.value
        ),
        "limitations": (
            "Schema expansion result bundles contract-only schema/read-model parts",
            "it creates no endpoint, live query, event bus, runtime bridge, or CLI",
        ),
    }
    result = SurfaceProjectionSchemaExpansionResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_no_live_endpoint_boundary_is_active(result.no_live_endpoint_boundary)
    return result


def build_p2_6_b_side_effect_proof() -> P26BSideEffectProof:
    return P26BSideEffectProof()


def build_p2_6_b_surface_projection_schema_result() -> (
    P26BSurfaceProjectionSchemaResult
):
    gate = build_surface_projection_schema_gate()
    registry = build_surface_projection_read_model_registry()
    inventory = build_surface_projection_schema_inventory()
    surface_schemas = build_default_surface_projection_schemas()
    response_envelope = build_surface_projection_response_envelope()
    error_envelope = build_surface_projection_error_envelope()
    filter_contract = build_surface_projection_filter_contract()
    sort_contract = build_surface_projection_sort_contract()
    pagination_contract = build_surface_projection_pagination_contract()
    query_contract = build_surface_projection_query_contract(
        filter_contract,
        sort_contract,
        pagination_contract,
    )
    boundary = build_surface_projection_no_live_endpoint_boundary(
        response_envelope,
        query_contract,
    )
    expansion = build_surface_projection_schema_expansion_result(
        schema_gate=gate,
        read_model_registry=registry,
        schema_inventory=inventory,
        surface_schemas=surface_schemas,
        response_envelope=response_envelope,
        error_envelope=error_envelope,
        query_contract=query_contract,
        filter_contract=filter_contract,
        sort_contract=sort_contract,
        pagination_contract=pagination_contract,
        no_live_endpoint_boundary=boundary,
    )
    proof = build_p2_6_b_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "pack_id": P2_6_B_PACK_ID,
        "section_id": P2_6_B_SECTION_ID,
        "official_section_name": P2_6_B_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_6_B_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_6_B_DEPENDENCY_PACK,
        "schema_gate": gate,
        "read_model_registry": registry,
        "schema_inventory": inventory,
        "surface_schemas": surface_schemas,
        "response_envelope": response_envelope,
        "error_envelope": error_envelope,
        "query_contract": query_contract,
        "filter_contract": filter_contract,
        "sort_contract": sort_contract,
        "pagination_contract": pagination_contract,
        "no_live_endpoint_boundary": boundary,
        "schema_expansion_result": expansion,
        "truth_labels": tuple(label.value for label in SurfaceProjectionSchemaTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": proof,
        "next_pack": P2_6_B_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P26BSurfaceProjectionSchemaResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_6_b_does_not_start_future_work(result)
    assert_p2_6_b_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_6_b_result(
    result: P26BSurfaceProjectionSchemaResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_b_surface_projection_schema_result()
    return to_canonical_json(result.to_canonical_dict())


def render_surface_projection_schema_contract_summary(
    result: P26BSurfaceProjectionSchemaResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_b_surface_projection_schema_result()
    return (
        f"{result.pack_id} {result.official_section_name}: "
        f"{len(result.read_model_registry.entries)} schema registry entries; "
        f"no_live_endpoint={result.no_live_endpoint_boundary.boundary_active}; "
        f"next={result.next_pack}; live={result.claims_live}"
    )


def assert_schema_registry_is_not_source_of_truth(
    registry: SurfaceProjectionReadModelRegistry,
) -> None:
    if registry.duplicates_source_of_truth or registry.is_source_of_truth:
        _reject(
            "Projection schema registry must not duplicate or own source-of-truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if registry.is_storage:
        _reject(
            "Projection schema registry must not be storage",
            field="is_storage",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_schema_inventory_is_not_storage(
    inventory: SurfaceProjectionSchemaInventory,
) -> None:
    if inventory.duplicates_source_of_truth or inventory.is_storage:
        _reject(
            "Schema inventory must not duplicate source-of-truth or act as storage",
            field="is_storage",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_surface_schema_is_not_ui(schema: SurfaceSpecificProjectionSchema) -> None:
    if schema.is_ui_schema or schema.is_product_schema or schema.mutates_state:
        _reject(
            "Surface projection schema must not be UI, product, or mutation",
            field="is_ui_schema",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if schema.duplicates_source_of_truth:
        _reject(
            "Surface projection schema must not duplicate source-of-truth",
            field="duplicates_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_response_envelope_is_not_http_response(
    envelope: SurfaceProjectionResponseEnvelope,
) -> None:
    if envelope.is_http_response or envelope.requires_server:
        _reject(
            "Response envelope must not be live HTTP response or require server",
            field="is_http_response",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if envelope.requires_route_handler:
        _reject(
            "Response envelope must not require route handler",
            field="requires_route_handler",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_error_envelope_is_not_runtime_error_handler(
    envelope: SurfaceProjectionErrorEnvelope,
) -> None:
    if envelope.is_runtime_error_handler or envelope.throws_exception:
        _reject(
            "Error envelope must not be runtime error handler or throw exception",
            field="is_runtime_error_handler",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if envelope.writes_trace:
        _reject(
            "Error envelope must not write trace",
            field="writes_trace",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_query_contract_is_not_live_query(
    contract: SurfaceProjectionQueryContract,
) -> None:
    if (
        contract.executes_live_query
        or contract.queries_runtime_state
        or contract.queries_database
        or contract.queries_storage
    ):
        _reject(
            "Query contract must not execute or query live/runtime/database/storage",
            field="executes_live_query",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_filter_sort_pagination_do_not_execute(
    *,
    filter_contract: SurfaceProjectionFilterContract | None = None,
    sort_contract: SurfaceProjectionSortContract | None = None,
    pagination_contract: SurfaceProjectionPaginationContract | None = None,
) -> None:
    if filter_contract is not None and (
        filter_contract.executes_filter
        or filter_contract.filters_runtime_state
        or filter_contract.filters_database
    ):
        _reject(
            "Filter contract must not execute against runtime/database data",
            field="executes_filter",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if sort_contract is not None and (
        sort_contract.executes_sort
        or sort_contract.sorts_runtime_state
        or sort_contract.sorts_database
    ):
        _reject(
            "Sort contract must not execute against runtime/database data",
            field="executes_sort",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if pagination_contract is not None and (
        pagination_contract.executes_pagination
        or pagination_contract.paginates_runtime_state
        or pagination_contract.paginates_database
    ):
        _reject(
            "Pagination contract must not execute against runtime/database data",
            field="executes_pagination",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_live_endpoint_boundary_is_active(
    boundary: SurfaceProjectionNoLiveEndpointBoundary,
) -> None:
    if not boundary.boundary_active:
        _reject(
            "No-live-endpoint boundary must be active",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    required = (
        boundary.prevents_api_server,
        boundary.prevents_http_routes,
        boundary.prevents_route_handlers,
        boundary.prevents_live_endpoint,
        boundary.prevents_live_query,
        boundary.prevents_database_query_runtime,
        boundary.prevents_storage_query_runtime,
        boundary.prevents_runtime_bridge,
    )
    if not all(required):
        _reject(
            "No-live-endpoint boundary must prevent all live endpoint paths",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_6_b_does_not_start_future_work(
    result: P26BSurfaceProjectionSchemaResult,
) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or proof.p2_6_c_started
        or proof.p2_7_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.6-B must not start P2.6-C/P2.7/P2.10/P2.13",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.next_pack != P2_6_B_NEXT_PACK:
        _reject(
            "P2.6-B next pack must be P2.6-C",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_6_b_side_effects_all_false(proof: P26BSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.6-B side-effect proof field must remain false: {field.name}",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
