"""P2.6-D surface projection / API / event bridge section seal.

Contract-only section aggregation over P2.6-A/B/C. This module creates a
deterministic P2.6 section read model, bridge/binding availability rollup,
no-live-infrastructure proof, validation rollup, contract-scope demo, and
section seal. It does not create API server, HTTP routes, route handlers,
live endpoints, live query execution, event bus, event dispatcher, subscriber
runtime, websocket/SSE, live stream, runtime event emission, runtime bridge,
runtime dispatch, API event bridge runtime, trace/memory/storage writes,
CLI/Shell/TUI binding, product behavior, release scope, or runtime mutation.
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
from .surface_projection_events import (
    P2_6_C_PACK_ID,
    P2_6_C_REPORT_PATH,
    P26CSurfaceProjectionEventBridgeResult,
    build_p2_6_c_surface_projection_event_bridge_result,
)
from .surface_projection_foundation import (
    P2_6_A_PACK_ID,
    P2_6_A_REPORT_PATH,
    P2_6_A_SECTION_ID,
    build_p2_6_a_surface_projection_result,
)
from .surface_projection_schemas import (
    P2_6_B_PACK_ID,
    P2_6_B_REPORT_PATH,
    build_p2_6_b_surface_projection_schema_result,
)
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_6_D_PACK_ID = "P2.6-D"
P2_6_D_SECTION_ID = P2_6_A_SECTION_ID
P2_6_D_OFFICIAL_SECTION_NAME = "Surface Projection / API / Event Bridge"
P2_6_D_DEPENDENCY_PACK = P2_6_C_PACK_ID
P2_6_D_NEXT_PACK = "P2.7-A"
P2_6_D_NEXT_SECTION = "P2.7"
P2_6_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.6.16",
    "P2.6.17",
    "P2.6.18",
    "P2.6.19",
    "P2.6.20",
)
P2_6_D_FULL_SECTION_CHECKPOINTS: tuple[str, ...] = tuple(
    f"P2.6.{index}" for index in range(21)
)
P2_6_D_REPORT_FILENAME = "P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md"
P2_6_D_REPORT_PATH = f"agent/reports/{P2_6_D_REPORT_FILENAME}"

P2_6_A_COMMIT_REF = "414243a278048660323065e5dae7a0b2f65ffd05"
P2_6_B_COMMIT_REF = "7eca9c2db20c446d0e0c3191fb641e8687100db6"
P2_6_C_COMMIT_REF = "ba87a101a618f684f67bff8467a7ecb48c5d75dc"

P2_6_D_GATE_VERSION = "p2_6_d_surface_projection_section_seal_gate.v1"
P2_6_D_INVENTORY_VERSION = "p2_6_d_surface_projection_section_contract_inventory.v1"
P2_6_D_READ_MODEL_VERSION = "p2_6_d_surface_projection_section_read_model.v1"
P2_6_D_READ_MODEL_VERSION_META = "p2_6_d_surface_projection_section_read_model_version.v1"
P2_6_D_AVAILABILITY_ROLLUP_VERSION = (
    "p2_6_d_surface_projection_bridge_availability_rollup.v1"
)
P2_6_D_BINDING_AVAILABILITY_VERSION = (
    "p2_6_d_surface_projection_binding_availability.v1"
)
P2_6_D_NO_LIVE_INFRA_PROOF_VERSION = (
    "p2_6_d_surface_projection_no_live_infrastructure_proof.v1"
)
P2_6_D_VALIDATION_ROLLUP_VERSION = (
    "p2_6_d_surface_projection_section_validation_rollup.v1"
)
P2_6_D_DEMO_VERSION = "p2_6_d_surface_projection_contract_scope_demo.v1"
P2_6_D_SECTION_SEAL_RESULT_VERSION = (
    "p2_6_d_surface_projection_section_seal_result.v1"
)
P2_6_D_RESULT_VERSION = "p2_6_d_surface_projection_section_seal_pack_result.v1"

P2_6_A_TEST_REF = "tests/aurel_shell/test_shell_surface_projection_foundation.py"
P2_6_B_TEST_REF = "tests/aurel_shell/test_shell_surface_projection_schemas.py"
P2_6_C_TEST_REF = "tests/aurel_shell/test_shell_surface_projection_events.py"
P2_6_D_TEST_REF = "tests/aurel_shell/test_shell_surface_projection_section_seal.py"

P2_6_A_VALIDATION_REF = "agent/TESTS.md#P2.6-A"
P2_6_B_VALIDATION_REF = "agent/TESTS.md#P2.6-B"
P2_6_C_VALIDATION_REF = "agent/TESTS.md#P2.6-C"
P2_6_D_VALIDATION_REF = "agent/TESTS.md#P2.6-D"

P2_6_D_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_6_D_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_BINDING_UNAVAILABLE_REASON = (
    "P2.6-D seals projection/API/event contracts only. Shell/CLI/TUI binding "
    "remains UNAVAILABLE until P2.7-A."
)

_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "live API server",
    "HTTP routes",
    "route handlers",
    "live endpoints",
    "live query runtime",
    "event bus",
    "event dispatcher",
    "subscriber runtime",
    "websocket/SSE/live stream",
    "runtime event emission",
    "runtime bridge",
    "runtime dispatch",
    "API event bridge runtime",
    "trace write",
    "memory write",
    "storage write",
    "CLI/Shell/TUI binding",
    "surface switching",
    "command execution",
    "workflow/tool dispatch",
    "permission enforcement",
    "approval activation",
    "product behavior",
    "release scope",
    "P2.7 implementation",
    "P2.10 implementation",
    "P2.13 implementation",
)

_CHECKPOINT_SPECS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("P2.6.0", "Surface Projection Section Gate", P2_6_A_PACK_ID, P2_6_A_REPORT_PATH, P2_6_A_TEST_REF, P2_6_A_COMMIT_REF),
    ("P2.6.1", "Projection Identity", P2_6_A_PACK_ID, P2_6_A_REPORT_PATH, P2_6_A_TEST_REF, P2_6_A_COMMIT_REF),
    ("P2.6.2", "Projection Scope", P2_6_A_PACK_ID, P2_6_A_REPORT_PATH, P2_6_A_TEST_REF, P2_6_A_COMMIT_REF),
    ("P2.6.3", "API Exposure / No-Server Boundary", P2_6_A_PACK_ID, P2_6_A_REPORT_PATH, P2_6_A_TEST_REF, P2_6_A_COMMIT_REF),
    ("P2.6.4", "Event Envelope / No-Event-Bus Boundary", P2_6_A_PACK_ID, P2_6_A_REPORT_PATH, P2_6_A_TEST_REF, P2_6_A_COMMIT_REF),
    ("P2.6.5", "Projection Availability / Foundation Result", P2_6_A_PACK_ID, P2_6_A_REPORT_PATH, P2_6_A_TEST_REF, P2_6_A_COMMIT_REF),
    ("P2.6.6", "Schema Gate / Read Model Registry", P2_6_B_PACK_ID, P2_6_B_REPORT_PATH, P2_6_B_TEST_REF, P2_6_B_COMMIT_REF),
    ("P2.6.7", "Schema Inventory / Surface Schemas", P2_6_B_PACK_ID, P2_6_B_REPORT_PATH, P2_6_B_TEST_REF, P2_6_B_COMMIT_REF),
    ("P2.6.8", "API Response / Error Envelopes", P2_6_B_PACK_ID, P2_6_B_REPORT_PATH, P2_6_B_TEST_REF, P2_6_B_COMMIT_REF),
    ("P2.6.9", "Query / Filter / Sort / Pagination Contracts", P2_6_B_PACK_ID, P2_6_B_REPORT_PATH, P2_6_B_TEST_REF, P2_6_B_COMMIT_REF),
    ("P2.6.10", "No-Live-Endpoint Boundary / Schema Expansion Result", P2_6_B_PACK_ID, P2_6_B_REPORT_PATH, P2_6_B_TEST_REF, P2_6_B_COMMIT_REF),
    ("P2.6.11", "Event Envelope Registry / Event Kind Catalog", P2_6_C_PACK_ID, P2_6_C_REPORT_PATH, P2_6_C_TEST_REF, P2_6_C_COMMIT_REF),
    ("P2.6.12", "Event Payload / Source-Target Mapping", P2_6_C_PACK_ID, P2_6_C_REPORT_PATH, P2_6_C_TEST_REF, P2_6_C_COMMIT_REF),
    ("P2.6.13", "Event Causality / Correlation / Evidence Refs", P2_6_C_PACK_ID, P2_6_C_REPORT_PATH, P2_6_C_TEST_REF, P2_6_C_COMMIT_REF),
    ("P2.6.14", "Subscription / Delivery Descriptors", P2_6_C_PACK_ID, P2_6_C_REPORT_PATH, P2_6_C_TEST_REF, P2_6_C_COMMIT_REF),
    ("P2.6.15", "No-Live-Stream / No-Runtime-Dispatch Boundary", P2_6_C_PACK_ID, P2_6_C_REPORT_PATH, P2_6_C_TEST_REF, P2_6_C_COMMIT_REF),
    ("P2.6.16", "Projection / API / Event Contract Inventory Rollup", P2_6_D_PACK_ID, P2_6_D_REPORT_PATH, P2_6_D_TEST_REF, "PENDING_AT_BUILD"),
    ("P2.6.17", "Section Projection / API / Event Read Model Contract", P2_6_D_PACK_ID, P2_6_D_REPORT_PATH, P2_6_D_TEST_REF, "PENDING_AT_BUILD"),
    ("P2.6.18", "Shell / CLI / TUI Binding Availability Contract", P2_6_D_PACK_ID, P2_6_D_REPORT_PATH, P2_6_D_TEST_REF, "PENDING_AT_BUILD"),
    ("P2.6.19", "Docs / State / Reports Synchronization", P2_6_D_PACK_ID, P2_6_D_REPORT_PATH, P2_6_D_TEST_REF, "PENDING_AT_BUILD"),
    ("P2.6.20", "Section Exit Seal / Contract-Scope Demo / No-Live-Bridge Proof", P2_6_D_PACK_ID, P2_6_D_REPORT_PATH, P2_6_D_TEST_REF, "PENDING_AT_BUILD"),
)


class SurfaceProjectionSectionSealGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class SurfaceProjectionSectionContractEntryStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class SurfaceProjectionBindingAvailabilityStatus(str, Enum):
    UNAVAILABLE_P2_7_REQUIRED = "UNAVAILABLE_P2_7_REQUIRED"
    CONTRACT_READY = "CONTRACT_READY"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class SurfaceProjectionSectionSealStatus(str, Enum):
    SEALED_CONTRACT_ONLY = "SEALED_CONTRACT_ONLY"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class SurfaceProjectionSectionReadModelStatus(str, Enum):
    SEALED_CONTRACT_ONLY = "SEALED_CONTRACT_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class SurfaceProjectionSectionSealTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    SECTION_SEAL_ONLY = "SECTION_SEAL_ONLY"
    SECTION_READ_MODEL_ONLY = "SECTION_READ_MODEL_ONLY"
    CONTRACT_INVENTORY_ONLY = "CONTRACT_INVENTORY_ONLY"
    AVAILABILITY_ROLLUP_ONLY = "AVAILABILITY_ROLLUP_ONLY"
    BINDING_AVAILABILITY_ONLY = "BINDING_AVAILABILITY_ONLY"
    VALIDATION_ROLLUP_ONLY = "VALIDATION_ROLLUP_ONLY"
    CONTRACT_SCOPE_DEMO_ONLY = "CONTRACT_SCOPE_DEMO_ONLY"
    NO_LIVE_INFRASTRUCTURE_PROOF = "NO_LIVE_INFRASTRUCTURE_PROOF"
    NO_SERVER_BOUNDARY = "NO_SERVER_BOUNDARY"
    NO_ROUTE_HANDLER_BOUNDARY = "NO_ROUTE_HANDLER_BOUNDARY"
    NO_LIVE_ENDPOINT_BOUNDARY = "NO_LIVE_ENDPOINT_BOUNDARY"
    NO_LIVE_QUERY_BOUNDARY = "NO_LIVE_QUERY_BOUNDARY"
    NO_EVENT_BUS_BOUNDARY = "NO_EVENT_BUS_BOUNDARY"
    NO_RUNTIME_DISPATCH_BOUNDARY = "NO_RUNTIME_DISPATCH_BOUNDARY"
    NO_TRACE_WRITE_BOUNDARY = "NO_TRACE_WRITE_BOUNDARY"
    NO_P2_7_STARTED_BOUNDARY = "NO_P2_7_STARTED_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_API_SERVER = "NOT_API_SERVER"
    NOT_HTTP_ROUTE = "NOT_HTTP_ROUTE"
    NOT_ROUTE_HANDLER = "NOT_ROUTE_HANDLER"
    NOT_LIVE_ENDPOINT = "NOT_LIVE_ENDPOINT"
    NOT_LIVE_QUERY = "NOT_LIVE_QUERY"
    NOT_EVENT_BUS = "NOT_EVENT_BUS"
    NOT_EVENT_DISPATCHER = "NOT_EVENT_DISPATCHER"
    NOT_SUBSCRIBER_RUNTIME = "NOT_SUBSCRIBER_RUNTIME"
    NOT_WEBSOCKET = "NOT_WEBSOCKET"
    NOT_SSE = "NOT_SSE"
    NOT_LIVE_STREAM = "NOT_LIVE_STREAM"
    NOT_RUNTIME_BRIDGE = "NOT_RUNTIME_BRIDGE"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_API_EVENT_BRIDGE_RUNTIME = "NOT_API_EVENT_BRIDGE_RUNTIME"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_CLI_BINDING = "NOT_CLI_BINDING"
    NOT_SHELL_EXECUTION_BINDING = "NOT_SHELL_EXECUTION_BINDING"
    NOT_TUI_BINDING = "NOT_TUI_BINDING"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_WORKFLOW_DISPATCH = "NOT_WORKFLOW_DISPATCH"
    NOT_TOOL_INVOCATION = "NOT_TOOL_INVOCATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_SHELL_COMPLETE = "NOT_SHELL_COMPLETE"
    NOT_P2_COMPLETE = "NOT_P2_COMPLETE"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    SECTION_SEAL_GATE_ONLY = "SECTION_SEAL_GATE_ONLY"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_INVENTED_PASS = "NOT_INVENTED_PASS"
    STATE_MIRROR_ONLY = "STATE_MIRROR_ONLY"


@dataclass(frozen=True)
class P26DSideEffectProof(_CanonicalMixin):
    api_server_created: bool = False
    http_routes_created: bool = False
    route_handler_created: bool = False
    live_endpoint_created: bool = False
    live_query_execution_created: bool = False
    event_bus_created: bool = False
    event_dispatcher_created: bool = False
    event_subscriber_runtime_created: bool = False
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
    shell_complete_claimed: bool = False
    p2_complete_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class SurfaceProjectionSectionSealGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_event_bridge_boundary_result_ref: str
    dependency_no_runtime_dispatch_boundary_ref: str
    dependency_side_effect_proof_ref: str
    p2_6_a_report_ref: str
    p2_6_b_report_ref: str
    p2_6_c_report_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: SurfaceProjectionSectionSealGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSectionContractEntry(_CanonicalMixin):
    entry_id: str
    checkpoint_id: str
    checkpoint_capsule: str
    source_pack: str
    source_report_ref: str
    source_test_ref: str
    source_commit_ref: str
    contract_ref: str
    status: SurfaceProjectionSectionContractEntryStatus
    truth_label: str
    unavailable_reason: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSectionContractInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    inventory_version: str
    contract_entries: tuple[SurfaceProjectionSectionContractEntry, ...]
    covered_checkpoints: tuple[str, ...]
    source_pack_refs: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    duplicates_source_of_truth: bool
    is_source_of_truth: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSectionReadModelVersion(_CanonicalMixin):
    version_id: str
    schema_version: str
    read_model_name: str
    read_model_version: str
    compatible_section: str
    compatible_pack: str
    source_contract_refs: tuple[str, ...]
    breaking_change: bool
    truth_label: str
    limitations: tuple[str, ...]
    version_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSectionReadModel(_CanonicalMixin):
    read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    read_model_version: SurfaceProjectionSectionReadModelVersion
    projection_contract_refs: tuple[str, ...]
    api_schema_contract_refs: tuple[str, ...]
    event_bridge_contract_refs: tuple[str, ...]
    availability_rollup_ref: str
    binding_availability_ref: str
    section_status: SurfaceProjectionSectionReadModelStatus
    is_live_endpoint: bool
    is_api_server: bool
    is_event_bus: bool
    truth_label: str
    limitations: tuple[str, ...]
    read_model_hash: str


@dataclass(frozen=True)
class SurfaceProjectionBridgeAvailabilityRollup(_CanonicalMixin):
    availability_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
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
    rollup_hash: str


@dataclass(frozen=True)
class SurfaceProjectionBindingAvailability(_CanonicalMixin):
    binding_availability_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    availability_status: SurfaceProjectionBindingAvailabilityStatus
    next_required_pack: str
    next_required_section: str
    available_as_contract: bool
    creates_cli_binding: bool
    creates_shell_execution_binding: bool
    creates_tui_binding: bool
    starts_p2_7: bool
    truth_label: str
    limitations: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True)
class SurfaceProjectionNoLiveInfrastructureProof(_CanonicalMixin):
    proof_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    api_server_created: bool
    http_routes_created: bool
    route_handler_created: bool
    live_endpoint_created: bool
    live_query_execution_created: bool
    event_bus_created: bool
    event_dispatcher_created: bool
    event_subscriber_runtime_created: bool
    websocket_stream_created: bool
    sse_stream_created: bool
    live_stream_created: bool
    runtime_event_emitted: bool
    runtime_bridge_created: bool
    runtime_dispatch_created: bool
    api_event_bridge_runtime_created: bool
    trace_written: bool
    memory_written: bool
    storage_written: bool
    cli_binding_created: bool
    shell_execution_binding_created: bool
    tui_binding_created: bool
    product_behavior_created: bool
    release_scope_claimed: bool
    truth_label: str
    limitations: tuple[str, ...]
    proof_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSectionValidationRollup(_CanonicalMixin):
    validation_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    p2_6_a_validation_ref: str
    p2_6_b_validation_ref: str
    p2_6_c_validation_ref: str
    p2_6_d_validation_commands: tuple[str, ...]
    p2_6_d_validation_results: tuple[str, ...]
    focused_tests_ref: str
    nearby_regression_ref: str
    ruff_result: str
    mypy_result: str
    compileall_result: str
    invented_pass: bool
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class SurfaceProjectionContractScopeDemo(_CanonicalMixin):
    demo_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    demo_name: str
    demo_scope: str
    inventory_ref: str
    read_model_ref: str
    availability_ref: str
    seal_result_ref: str
    is_product_demo: bool
    requires_live_api: bool
    requires_event_bridge: bool
    requires_cli_binding: bool
    truth_label: str
    limitations: tuple[str, ...]
    demo_hash: str


@dataclass(frozen=True)
class SurfaceProjectionSectionSealResult(_CanonicalMixin):
    section_seal_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    seal_status: SurfaceProjectionSectionSealStatus
    section_seal_gate: SurfaceProjectionSectionSealGate
    contract_inventory: SurfaceProjectionSectionContractInventory
    section_read_model: SurfaceProjectionSectionReadModel
    availability_rollup: SurfaceProjectionBridgeAvailabilityRollup
    binding_availability: SurfaceProjectionBindingAvailability
    no_live_infrastructure_proof: SurfaceProjectionNoLiveInfrastructureProof
    validation_rollup: SurfaceProjectionSectionValidationRollup
    contract_scope_demo: SurfaceProjectionContractScopeDemo
    covered_checkpoints: tuple[str, ...]
    full_section_coverage: tuple[str, ...]
    next_pack: str
    creates_api_server: bool
    creates_http_routes: bool
    creates_route_handlers: bool
    creates_live_endpoint: bool
    creates_event_bus: bool
    creates_runtime_bridge: bool
    creates_cli_binding: bool
    creates_product_behavior: bool
    claims_release_scope: bool
    claims_shell_complete: bool
    claims_p2_complete: bool
    truth_label: str
    limitations: tuple[str, ...]
    seal_result_hash: str


@dataclass(frozen=True)
class P26DSurfaceProjectionSectionSealResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    full_section_coverage: tuple[str, ...]
    dependency_pack: str
    p2_6_a_evidence_ref: str
    p2_6_b_evidence_ref: str
    p2_6_c_evidence_ref: str
    section_seal_gate: SurfaceProjectionSectionSealGate
    contract_inventory: SurfaceProjectionSectionContractInventory
    section_read_model: SurfaceProjectionSectionReadModel
    availability_rollup: SurfaceProjectionBridgeAvailabilityRollup
    binding_availability: SurfaceProjectionBindingAvailability
    no_live_infrastructure_proof: SurfaceProjectionNoLiveInfrastructureProof
    validation_rollup: SurfaceProjectionSectionValidationRollup
    contract_scope_demo: SurfaceProjectionContractScopeDemo
    section_seal_result: SurfaceProjectionSectionSealResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P26DSideEffectProof
    canonical_surface_ids: tuple[str, ...]
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    claims_shell_complete: bool
    claims_p2_complete: bool
    starts_future_work: bool
    result_hash: str


def _event_bridge_boundary_result_ref(
    event_result: P26CSurfaceProjectionEventBridgeResult,
) -> str:
    boundary = event_result.event_bridge_boundary_result
    return (
        f"{boundary.event_bridge_boundary_result_id}:"
        f"hash={boundary.result_hash[:12]}"
    )


def _no_runtime_dispatch_boundary_ref(
    event_result: P26CSurfaceProjectionEventBridgeResult,
) -> str:
    boundary = event_result.no_runtime_dispatch_boundary
    return (
        f"{boundary.boundary_id}:active="
        f"{str(boundary.boundary_active).lower()}"
    )


def build_surface_projection_section_seal_gate(
    event_result: P26CSurfaceProjectionEventBridgeResult | None = None,
) -> SurfaceProjectionSectionSealGate:
    if event_result is None:
        event_result = build_p2_6_c_surface_projection_event_bridge_result()
    assert_p2_6_c_event_bridge_result_available(event_result)
    payload: dict[str, Any] = {
        "gate_id": "p2_6_d_surface_projection_section_seal_gate",
        "schema_version": P2_6_D_GATE_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "official_section_name": P2_6_D_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_6_D_DEPENDENCY_PACK,
        "dependency_report_ref": P2_6_C_REPORT_PATH,
        "dependency_commit_ref": P2_6_C_COMMIT_REF,
        "dependency_validation_ref": P2_6_C_VALIDATION_REF,
        "dependency_event_bridge_boundary_result_ref": _event_bridge_boundary_result_ref(
            event_result
        ),
        "dependency_no_runtime_dispatch_boundary_ref": _no_runtime_dispatch_boundary_ref(
            event_result
        ),
        "dependency_side_effect_proof_ref": "P26CSideEffectProof:all_false",
        "p2_6_a_report_ref": P2_6_A_REPORT_PATH,
        "p2_6_b_report_ref": P2_6_B_REPORT_PATH,
        "p2_6_c_report_ref": P2_6_C_REPORT_PATH,
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": SurfaceProjectionSectionSealGateStatus.READY,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.SECTION_SEAL_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create live API, event bus, or CLI binding",
        ),
    }
    gate = SurfaceProjectionSectionSealGate(**payload, gate_hash=_hash_payload(payload))
    assert_section_gate_depends_on_p2_6_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def _build_contract_entry(
    checkpoint_id: str,
    checkpoint_capsule: str,
    source_pack: str,
    source_report_ref: str,
    source_test_ref: str,
    source_commit_ref: str,
    contract_ref: str,
) -> SurfaceProjectionSectionContractEntry:
    payload: dict[str, Any] = {
        "entry_id": f"p2_6_contract_entry_{checkpoint_id.replace('.', '_').lower()}",
        "checkpoint_id": checkpoint_id,
        "checkpoint_capsule": checkpoint_capsule,
        "source_pack": source_pack,
        "source_report_ref": source_report_ref,
        "source_test_ref": source_test_ref,
        "source_commit_ref": source_commit_ref,
        "contract_ref": contract_ref,
        "status": SurfaceProjectionSectionContractEntryStatus.DONE,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.REPORT_ONLY.value,
        "unavailable_reason": "",
        "limitations": ("references source evidence only", "not source-of-truth duplication"),
    }
    return SurfaceProjectionSectionContractEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_surface_projection_section_contract_inventory() -> (
    SurfaceProjectionSectionContractInventory
):
    entries = tuple(
        _build_contract_entry(
            checkpoint_id,
            capsule,
            pack,
            report,
            test,
            commit,
            f"surface_projection:{checkpoint_id}:{pack}",
        )
        for checkpoint_id, capsule, pack, report, test, commit in _CHECKPOINT_SPECS
    )
    payload: dict[str, Any] = {
        "inventory_id": "p2_6_d_surface_projection_section_contract_inventory",
        "schema_version": P2_6_D_INVENTORY_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "official_section_name": P2_6_D_OFFICIAL_SECTION_NAME,
        "inventory_version": P2_6_D_INVENTORY_VERSION,
        "contract_entries": entries,
        "covered_checkpoints": P2_6_D_FULL_SECTION_CHECKPOINTS,
        "source_pack_refs": (
            P2_6_A_PACK_ID,
            P2_6_B_PACK_ID,
            P2_6_C_PACK_ID,
            P2_6_D_PACK_ID,
        ),
        "source_report_refs": (
            P2_6_A_REPORT_PATH,
            P2_6_B_REPORT_PATH,
            P2_6_C_REPORT_PATH,
            P2_6_D_REPORT_PATH,
        ),
        "duplicates_source_of_truth": False,
        "is_source_of_truth": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.CONTRACT_INVENTORY_ONLY.value,
        "limitations": (
            "inventory references P2.6-A/B/C/D evidence by ref",
            "does not duplicate source-of-truth contracts",
        ),
    }
    return SurfaceProjectionSectionContractInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )


def build_surface_projection_section_read_model_version() -> (
    SurfaceProjectionSectionReadModelVersion
):
    payload: dict[str, Any] = {
        "version_id": "p2_6_d_surface_projection_section_read_model_version",
        "schema_version": P2_6_D_READ_MODEL_VERSION_META,
        "read_model_name": "surface_projection_section_read_model",
        "read_model_version": P2_6_D_READ_MODEL_VERSION,
        "compatible_section": P2_6_D_SECTION_ID,
        "compatible_pack": P2_6_D_PACK_ID,
        "source_contract_refs": (
            "SurfaceProjectionGate",
            "SurfaceProjectionSchemaGate",
            "SurfaceProjectionEventBridgeGate",
            "SurfaceProjectionSectionSealGate",
        ),
        "breaking_change": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.SECTION_READ_MODEL_ONLY.value,
        "limitations": ("read model version is contract metadata only",),
    }
    return SurfaceProjectionSectionReadModelVersion(
        **payload,
        version_hash=_hash_payload(payload),
    )


def build_surface_projection_bridge_availability_rollup() -> (
    SurfaceProjectionBridgeAvailabilityRollup
):
    payload: dict[str, Any] = {
        "availability_rollup_id": "p2_6_d_surface_projection_bridge_availability_rollup",
        "schema_version": P2_6_D_AVAILABILITY_ROLLUP_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "available_contracts": (
            "SurfaceProjectionGate",
            "SurfaceProjectionSchemaGate",
            "SurfaceProjectionEventBridgeGate",
            "SurfaceProjectionSectionSealGate",
            "SurfaceProjectionSectionContractInventory",
            "SurfaceProjectionSectionReadModel",
        ),
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "blocked_capabilities": (),
        "unavailable_reasons": (
            "P2.6-D seals contracts only; live bridge deferred to later packs",
            _BINDING_UNAVAILABLE_REASON,
        ),
        "future_pack_refs": ("P2.7-A", "P2.10-A", "P2.13-A"),
        "grants_permission": False,
        "denies_permission": False,
        "activates_approval": False,
        "enforces_policy": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.AVAILABILITY_ROLLUP_ONLY.value,
        "limitations": (
            "availability rollup is honesty metadata only",
            "does not grant or deny permission",
        ),
    }
    return SurfaceProjectionBridgeAvailabilityRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )


def build_surface_projection_binding_availability() -> (
    SurfaceProjectionBindingAvailability
):
    payload: dict[str, Any] = {
        "binding_availability_id": "p2_6_d_surface_projection_binding_availability",
        "schema_version": P2_6_D_BINDING_AVAILABILITY_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "availability_status": SurfaceProjectionBindingAvailabilityStatus.UNAVAILABLE_P2_7_REQUIRED,
        "next_required_pack": P2_6_D_NEXT_PACK,
        "next_required_section": P2_6_D_NEXT_SECTION,
        "available_as_contract": True,
        "creates_cli_binding": False,
        "creates_shell_execution_binding": False,
        "creates_tui_binding": False,
        "starts_p2_7": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.BINDING_AVAILABILITY_ONLY.value,
        "limitations": (
            "binding availability is a P2.7 handoff boundary",
            "availability is not binding",
        ),
    }
    result = SurfaceProjectionBindingAvailability(
        **payload,
        binding_hash=_hash_payload(payload),
    )
    assert_binding_availability_is_not_binding(result)
    assert_p2_7_readiness_is_not_p2_7_start(result)
    return result


def build_surface_projection_no_live_infrastructure_proof() -> (
    SurfaceProjectionNoLiveInfrastructureProof
):
    payload: dict[str, Any] = {
        "proof_id": "p2_6_d_surface_projection_no_live_infrastructure_proof",
        "schema_version": P2_6_D_NO_LIVE_INFRA_PROOF_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "api_server_created": False,
        "http_routes_created": False,
        "route_handler_created": False,
        "live_endpoint_created": False,
        "live_query_execution_created": False,
        "event_bus_created": False,
        "event_dispatcher_created": False,
        "event_subscriber_runtime_created": False,
        "websocket_stream_created": False,
        "sse_stream_created": False,
        "live_stream_created": False,
        "runtime_event_emitted": False,
        "runtime_bridge_created": False,
        "runtime_dispatch_created": False,
        "api_event_bridge_runtime_created": False,
        "trace_written": False,
        "memory_written": False,
        "storage_written": False,
        "cli_binding_created": False,
        "shell_execution_binding_created": False,
        "tui_binding_created": False,
        "product_behavior_created": False,
        "release_scope_claimed": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.NO_LIVE_INFRASTRUCTURE_PROOF.value,
        "limitations": (
            "proof records absence of live infrastructure at P2.6-D scope",
            "proof is not live infrastructure",
        ),
    }
    proof = SurfaceProjectionNoLiveInfrastructureProof(
        **payload,
        proof_hash=_hash_payload(payload),
    )
    assert_no_live_infrastructure_proof_is_active(proof)
    return proof


def build_surface_projection_section_validation_rollup() -> (
    SurfaceProjectionSectionValidationRollup
):
    payload: dict[str, Any] = {
        "validation_rollup_id": "p2_6_d_surface_projection_section_validation_rollup",
        "schema_version": P2_6_D_VALIDATION_ROLLUP_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "p2_6_a_validation_ref": P2_6_A_VALIDATION_REF,
        "p2_6_b_validation_ref": P2_6_B_VALIDATION_REF,
        "p2_6_c_validation_ref": P2_6_C_VALIDATION_REF,
        "p2_6_d_validation_commands": P2_6_D_VALIDATION_COMMANDS,
        "p2_6_d_validation_results": (),
        "focused_tests_ref": P2_6_D_TEST_REF,
        "nearby_regression_ref": "tests/aurel_shell",
        "ruff_result": "NOT_RUN_AT_BUILD",
        "mypy_result": "NOT_RUN_AT_BUILD",
        "compileall_result": "NOT_RUN_AT_BUILD",
        "invented_pass": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.VALIDATION_ROLLUP_ONLY.value,
        "limitations": (
            "validation results recorded in report after commands run",
            "rollup does not invent PASS",
        ),
    }
    rollup = SurfaceProjectionSectionValidationRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_validation_rollup_does_not_invent_pass(rollup)
    return rollup


def build_surface_projection_section_read_model(
    availability_rollup: SurfaceProjectionBridgeAvailabilityRollup | None = None,
    binding_availability: SurfaceProjectionBindingAvailability | None = None,
) -> SurfaceProjectionSectionReadModel:
    if availability_rollup is None:
        availability_rollup = build_surface_projection_bridge_availability_rollup()
    if binding_availability is None:
        binding_availability = build_surface_projection_binding_availability()
    version = build_surface_projection_section_read_model_version()
    payload: dict[str, Any] = {
        "read_model_id": "p2_6_d_surface_projection_section_read_model",
        "schema_version": P2_6_D_READ_MODEL_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "official_section_name": P2_6_D_OFFICIAL_SECTION_NAME,
        "read_model_version": version,
        "projection_contract_refs": (
            "SurfaceProjectionGate",
            "SurfaceProjectionFoundationResult",
            "SurfaceProjectionSectionReadModel",
        ),
        "api_schema_contract_refs": (
            "SurfaceProjectionApiExposure",
            "SurfaceProjectionSchemaGate",
            "SurfaceProjectionResponseEnvelope",
        ),
        "event_bridge_contract_refs": (
            "SurfaceProjectionEventEnvelope",
            "SurfaceProjectionEventBridgeGate",
            "SurfaceProjectionEventBridgeBoundaryResult",
        ),
        "availability_rollup_ref": availability_rollup.availability_rollup_id,
        "binding_availability_ref": binding_availability.binding_availability_id,
        "section_status": SurfaceProjectionSectionReadModelStatus.SEALED_CONTRACT_ONLY,
        "is_live_endpoint": False,
        "is_api_server": False,
        "is_event_bus": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.SECTION_READ_MODEL_ONLY.value,
        "limitations": (
            "section read model is contract-only",
            "not live endpoint, API server, or event bus",
        ),
    }
    read_model = SurfaceProjectionSectionReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )
    assert_section_read_model_is_not_live_endpoint(read_model)
    return read_model


def build_surface_projection_contract_scope_demo(
    inventory: SurfaceProjectionSectionContractInventory | None = None,
    read_model: SurfaceProjectionSectionReadModel | None = None,
    availability_rollup: SurfaceProjectionBridgeAvailabilityRollup | None = None,
    seal_result_ref: str = "p2_6_d_surface_projection_section_seal_result",
) -> SurfaceProjectionContractScopeDemo:
    if inventory is None:
        inventory = build_surface_projection_section_contract_inventory()
    if read_model is None:
        read_model = build_surface_projection_section_read_model()
    if availability_rollup is None:
        availability_rollup = build_surface_projection_bridge_availability_rollup()
    payload: dict[str, Any] = {
        "demo_id": "p2_6_d_surface_projection_contract_scope_demo",
        "schema_version": P2_6_D_DEMO_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "demo_name": "p2_6_surface_projection_section_contract_scope_demo",
        "demo_scope": "CONTRACT_SCOPE_ONLY",
        "inventory_ref": inventory.inventory_id,
        "read_model_ref": read_model.read_model_id,
        "availability_ref": availability_rollup.availability_rollup_id,
        "seal_result_ref": seal_result_ref,
        "is_product_demo": False,
        "requires_live_api": False,
        "requires_event_bridge": False,
        "requires_cli_binding": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.CONTRACT_SCOPE_DEMO_ONLY.value,
        "limitations": (
            "contract-scope demo validates shape and evidence only",
            "not product demo",
        ),
    }
    demo = SurfaceProjectionContractScopeDemo(**payload, demo_hash=_hash_payload(payload))
    assert_contract_scope_demo_is_not_product_demo(demo)
    return demo


def build_surface_projection_section_seal_result(
    gate: SurfaceProjectionSectionSealGate | None = None,
    inventory: SurfaceProjectionSectionContractInventory | None = None,
    read_model: SurfaceProjectionSectionReadModel | None = None,
    availability_rollup: SurfaceProjectionBridgeAvailabilityRollup | None = None,
    binding_availability: SurfaceProjectionBindingAvailability | None = None,
    no_live_proof: SurfaceProjectionNoLiveInfrastructureProof | None = None,
    validation_rollup: SurfaceProjectionSectionValidationRollup | None = None,
    contract_scope_demo: SurfaceProjectionContractScopeDemo | None = None,
) -> SurfaceProjectionSectionSealResult:
    if gate is None:
        gate = build_surface_projection_section_seal_gate()
    if inventory is None:
        inventory = build_surface_projection_section_contract_inventory()
    if availability_rollup is None:
        availability_rollup = build_surface_projection_bridge_availability_rollup()
    if binding_availability is None:
        binding_availability = build_surface_projection_binding_availability()
    if read_model is None:
        read_model = build_surface_projection_section_read_model(
            availability_rollup,
            binding_availability,
        )
    if no_live_proof is None:
        no_live_proof = build_surface_projection_no_live_infrastructure_proof()
    if validation_rollup is None:
        validation_rollup = build_surface_projection_section_validation_rollup()
    if contract_scope_demo is None:
        contract_scope_demo = build_surface_projection_contract_scope_demo(
            inventory=inventory,
            read_model=read_model,
            availability_rollup=availability_rollup,
            seal_result_ref="p2_6_d_surface_projection_section_seal_result",
        )
    payload: dict[str, Any] = {
        "section_seal_result_id": "p2_6_d_surface_projection_section_seal_result",
        "schema_version": P2_6_D_SECTION_SEAL_RESULT_VERSION,
        "section_id": P2_6_D_SECTION_ID,
        "created_for_pack": P2_6_D_PACK_ID,
        "official_section_name": P2_6_D_OFFICIAL_SECTION_NAME,
        "seal_status": SurfaceProjectionSectionSealStatus.SEALED_CONTRACT_ONLY,
        "section_seal_gate": gate,
        "contract_inventory": inventory,
        "section_read_model": read_model,
        "availability_rollup": availability_rollup,
        "binding_availability": binding_availability,
        "no_live_infrastructure_proof": no_live_proof,
        "validation_rollup": validation_rollup,
        "contract_scope_demo": contract_scope_demo,
        "covered_checkpoints": P2_6_D_PACK_CHECKPOINT_IDS,
        "full_section_coverage": P2_6_D_FULL_SECTION_CHECKPOINTS,
        "next_pack": P2_6_D_NEXT_PACK,
        "creates_api_server": False,
        "creates_http_routes": False,
        "creates_route_handlers": False,
        "creates_live_endpoint": False,
        "creates_event_bus": False,
        "creates_runtime_bridge": False,
        "creates_cli_binding": False,
        "creates_product_behavior": False,
        "claims_release_scope": False,
        "claims_shell_complete": False,
        "claims_p2_complete": False,
        "truth_label": SurfaceProjectionSectionSealTruthBoundary.SECTION_SEAL_ONLY.value,
        "limitations": (
            "section seal is not release seal",
            "P2.6 complete is not P2 complete",
        ),
    }
    result = SurfaceProjectionSectionSealResult(
        **payload,
        seal_result_hash=_hash_payload(payload),
    )
    assert_section_seal_is_not_release_seal(result)
    return result


def build_p2_6_d_side_effect_proof() -> P26DSideEffectProof:
    return P26DSideEffectProof()


def build_p2_6_d_surface_projection_section_seal_result() -> (
    P26DSurfaceProjectionSectionSealResult
):
    foundation = build_p2_6_a_surface_projection_result()
    schema = build_p2_6_b_surface_projection_schema_result()
    event_result = build_p2_6_c_surface_projection_event_bridge_result()
    gate = build_surface_projection_section_seal_gate(event_result)
    inventory = build_surface_projection_section_contract_inventory()
    availability_rollup = build_surface_projection_bridge_availability_rollup()
    binding_availability = build_surface_projection_binding_availability()
    read_model = build_surface_projection_section_read_model(
        availability_rollup,
        binding_availability,
    )
    no_live_proof = build_surface_projection_no_live_infrastructure_proof()
    validation_rollup = build_surface_projection_section_validation_rollup()
    section_seal_result = build_surface_projection_section_seal_result(
        gate=gate,
        inventory=inventory,
        read_model=read_model,
        availability_rollup=availability_rollup,
        binding_availability=binding_availability,
        no_live_proof=no_live_proof,
        validation_rollup=validation_rollup,
    )
    contract_scope_demo = build_surface_projection_contract_scope_demo(
        inventory=inventory,
        read_model=read_model,
        availability_rollup=availability_rollup,
        seal_result_ref=section_seal_result.section_seal_result_id,
    )
    side_effects = build_p2_6_d_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_6_D_RESULT_VERSION,
        "pack_id": P2_6_D_PACK_ID,
        "section_id": P2_6_D_SECTION_ID,
        "official_section_name": P2_6_D_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_6_D_PACK_CHECKPOINT_IDS,
        "full_section_coverage": P2_6_D_FULL_SECTION_CHECKPOINTS,
        "dependency_pack": P2_6_D_DEPENDENCY_PACK,
        "p2_6_a_evidence_ref": f"{P2_6_A_REPORT_PATH}:{foundation.result_hash[:12]}",
        "p2_6_b_evidence_ref": f"{P2_6_B_REPORT_PATH}:{schema.result_hash[:12]}",
        "p2_6_c_evidence_ref": f"{P2_6_C_REPORT_PATH}:{event_result.result_hash[:12]}",
        "section_seal_gate": gate,
        "contract_inventory": inventory,
        "section_read_model": read_model,
        "availability_rollup": availability_rollup,
        "binding_availability": binding_availability,
        "no_live_infrastructure_proof": no_live_proof,
        "validation_rollup": validation_rollup,
        "contract_scope_demo": contract_scope_demo,
        "section_seal_result": section_seal_result,
        "truth_labels": tuple(
            label.value for label in SurfaceProjectionSectionSealTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "next_pack": P2_6_D_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "claims_shell_complete": False,
        "claims_p2_complete": False,
        "starts_future_work": False,
    }
    result = P26DSurfaceProjectionSectionSealResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_6_d_does_not_start_future_work(result)
    assert_p2_6_d_side_effects_all_false(result.side_effect_proof)
    assert_contract_inventory_is_not_source_of_truth_duplication(result.contract_inventory)
    return result


def serialize_p2_6_d_result(
    result: P26DSurfaceProjectionSectionSealResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_d_surface_projection_section_seal_result()
    return to_canonical_json(result.to_canonical_dict())


def render_surface_projection_section_seal_summary(
    result: P26DSurfaceProjectionSectionSealResult | None = None,
) -> str:
    if result is None:
        result = build_p2_6_d_surface_projection_section_seal_result()
    seal = result.section_seal_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"status={seal.seal_status.value}",
            f"binding={result.binding_availability.availability_status.value}",
            f"next={result.next_pack}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"release_scope={str(result.claims_release_scope).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


def assert_p2_6_c_event_bridge_result_available(
    event_result: P26CSurfaceProjectionEventBridgeResult,
) -> None:
    if event_result.pack_id != P2_6_C_PACK_ID or event_result.starts_future_work:
        _reject(
            "P2.6-D requires P2.6-C event bridge result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    boundary = event_result.no_runtime_dispatch_boundary
    if not boundary.boundary_active:
        _reject(
            "P2.6-D requires active P2.6-C no-runtime-dispatch boundary",
            field="boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_section_gate_depends_on_p2_6_c(
    gate: SurfaceProjectionSectionSealGate,
) -> None:
    if gate.dependency_pack != P2_6_C_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.6-D section gate must depend on passed P2.6-C repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_event_bridge_boundary_result_ref
        or not gate.dependency_no_runtime_dispatch_boundary_ref
        or not gate.dependency_side_effect_proof_ref
    ):
        _reject(
            "P2.6-D section gate must reference P2.6-C bridge boundaries",
            field="dependency_event_bridge_boundary_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: SurfaceProjectionSectionSealGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.6-D gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_6_d_does_not_start_future_work(
    result: P26DSurfaceProjectionSectionSealResult,
) -> None:
    proof = result.side_effect_proof
    if result.starts_future_work or proof.p2_7_started or proof.p2_10_started or proof.p2_13_started:
        _reject(
            "P2.6-D must not start P2.7, P2.10, or P2.13",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_6_d_side_effects_all_false(proof: P26DSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.6-D side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_section_seal_is_not_release_seal(
    seal_result: SurfaceProjectionSectionSealResult,
) -> None:
    if (
        seal_result.claims_release_scope
        or seal_result.claims_shell_complete
        or seal_result.claims_p2_complete
    ):
        _reject(
            "P2.6-D section seal must not claim release, shell, or P2 completion",
            field="claims_release_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_complete_is_not_shell_complete(
    result: P26DSurfaceProjectionSectionSealResult,
) -> None:
    if result.claims_shell_complete or result.claims_p2_complete:
        _reject(
            "P2.6 section complete is not shell or P2 complete",
            field="claims_shell_complete",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_6_complete_is_not_p2_complete(
    result: P26DSurfaceProjectionSectionSealResult,
) -> None:
    assert_section_complete_is_not_shell_complete(result)


def assert_contract_scope_demo_is_not_product_demo(
    demo: SurfaceProjectionContractScopeDemo,
) -> None:
    if demo.is_product_demo or demo.requires_live_api or demo.requires_event_bridge:
        _reject(
            "P2.6-D contract-scope demo must not require live API or product behavior",
            field="is_product_demo",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_binding_availability_is_not_binding(
    binding: SurfaceProjectionBindingAvailability,
) -> None:
    if (
        binding.creates_cli_binding
        or binding.creates_shell_execution_binding
        or binding.creates_tui_binding
    ):
        _reject(
            "P2.6-D binding availability must not create CLI/Shell/TUI binding",
            field="creates_cli_binding",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_7_readiness_is_not_p2_7_start(
    binding: SurfaceProjectionBindingAvailability,
) -> None:
    if binding.starts_p2_7:
        _reject(
            "P2.7 readiness handoff is not P2.7 start",
            field="starts_p2_7",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_section_read_model_is_not_live_endpoint(
    read_model: SurfaceProjectionSectionReadModel,
) -> None:
    if read_model.is_live_endpoint or read_model.is_api_server or read_model.is_event_bus:
        _reject(
            "P2.6-D section read model must not be live endpoint, API server, or event bus",
            field="is_live_endpoint",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_contract_inventory_is_not_source_of_truth_duplication(
    inventory: SurfaceProjectionSectionContractInventory,
) -> None:
    if inventory.duplicates_source_of_truth or inventory.is_source_of_truth:
        _reject(
            "P2.6-D contract inventory must not duplicate or become source-of-truth",
            field="duplicates_source_of_truth",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_evidence_rollup_is_not_trace_verified(
    result: P26DSurfaceProjectionSectionSealResult,
) -> None:
    if result.claims_trace_verified or result.side_effect_proof.trace_verified_claimed:
        _reject(
            "P2.6-D evidence rollup must not claim TRACE_VERIFIED",
            field="claims_trace_verified",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_validation_rollup_does_not_invent_pass(
    rollup: SurfaceProjectionSectionValidationRollup,
) -> None:
    if rollup.invented_pass:
        _reject(
            "P2.6-D validation rollup must not invent PASS",
            field="invented_pass",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_live_infrastructure_proof_is_active(
    proof: SurfaceProjectionNoLiveInfrastructureProof,
) -> None:
    live_fields = (
        proof.api_server_created,
        proof.http_routes_created,
        proof.route_handler_created,
        proof.live_endpoint_created,
        proof.live_query_execution_created,
        proof.event_bus_created,
        proof.event_dispatcher_created,
        proof.event_subscriber_runtime_created,
        proof.websocket_stream_created,
        proof.sse_stream_created,
        proof.live_stream_created,
        proof.runtime_event_emitted,
        proof.runtime_bridge_created,
        proof.runtime_dispatch_created,
        proof.api_event_bridge_runtime_created,
        proof.trace_written,
        proof.memory_written,
        proof.storage_written,
        proof.cli_binding_created,
        proof.product_behavior_created,
        proof.release_scope_claimed,
    )
    if any(live_fields):
        _reject(
            "P2.6-D no-live-infrastructure proof must keep all live fields false",
            field="api_server_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_no_p2_7_started_boundary_is_active(
    binding: SurfaceProjectionBindingAvailability,
) -> None:
    if binding.starts_p2_7 or binding.availability_status != (
        SurfaceProjectionBindingAvailabilityStatus.UNAVAILABLE_P2_7_REQUIRED
    ):
        _reject(
            "P2.6-D must keep P2.7 binding unavailable until P2.7-A",
            field="starts_p2_7",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
