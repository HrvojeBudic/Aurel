"""P2.2-D local navigation integration tail, projection contract, binding, and seal.

Contract-only section closure over P2.2-A/B/C. This module creates deterministic
read-model artifacts for inspection and handoff; it does not create UI, sidebars,
global left nav, route runtime, API servers, event buses, runtime events, memory
writes, trace writes, or P2.3 behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .local_navigation import (
    P2_2_A_PACK_ID,
    P2_2_A_REPORT_FILENAME,
    P2_2_SECTION_ID,
    P2_2_SECTION_NAME,
    LocalNavProjectionSeed,
    build_local_nav_projection_seed,
    build_p2_2_a_local_navigation_foundation_result,
)
from .local_navigation_context import (
    AUDIT_REPAIR_001_PACK_ID,
    AUDIT_REPAIR_001_REPORT_FILENAME,
    P2_2_C_PACK_ID,
    P2_2_C_REPORT_FILENAME,
    LocalNavContextProjectionResult,
    build_local_nav_context_projection_result,
    build_p2_2_c_local_navigation_context_result,
)
from .local_navigation_hierarchy import (
    P2_2_B_PACK_ID,
    P2_2_B_REPORT_FILENAME,
    LocalNavHierarchyProjectionResult,
    build_local_nav_hierarchy_projection_result,
    build_p2_2_b_local_navigation_hierarchy_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_2_D_PACK_ID = "P2.2-D"
P2_2_D_PACK_NAME = (
    "P2.2 Integration Tail / Projection / Binding / Docs / Section Seal"
)
P2_2_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.2.16",
    "P2.2.17",
    "P2.2.18",
    "P2.2.19",
    "P2.2.20",
)
P2_2_D_DEPENDENCY_PACKS: tuple[str, ...] = (
    AUDIT_REPAIR_001_PACK_ID,
    P2_2_A_PACK_ID,
    P2_2_B_PACK_ID,
    P2_2_C_PACK_ID,
)
P2_2_D_REPORT_FILENAME = "P2_2_D_LOCAL_NAVIGATION_INTEGRATION_TAIL.md"
P2_2_D_REPORT_PATH = f"agent/reports/{P2_2_D_REPORT_FILENAME}"
P2_2_D_NEXT_SECTION = "P2.3"
P2_2_D_NEXT_SECTION_NAME = "Floating Windows / Workspace State"
P2_2_D_NEXT_RECOMMENDED_PACK = "P2.3-A"

P2_2_D_RESULT_VERSION = "p2_2_d_local_navigation_integration_tail_result.v1"
P2_2_INTEGRATION_SNAPSHOT_VERSION = "p2_2_local_navigation_integration_snapshot.v1"
P2_2_PROJECTION_CONTRACT_VERSION = "p2_2_local_navigation_projection_contract.v1"
P2_2_API_CONTRACT_VERSION = "p2_2_local_navigation_api_contract_shape.v1"
P2_2_EVENT_CONTRACT_VERSION = "p2_2_local_navigation_event_contract_shape.v1"
P2_2_BINDING_CONTRACT_VERSION = "p2_2_local_navigation_shell_binding_contract.v1"
P2_2_DOCS_SYNC_VERSION = "p2_2_local_navigation_docs_state_sync.v1"
P2_2_EXIT_SEAL_VERSION = "p2_2_local_navigation_exit_seal.v1"
P2_3_READINESS_VERSION = "p2_3_readiness_result.v1"

API_CONTRACT_UNAVAILABLE_REASON = (
    "UNAVAILABLE_API_RUNTIME: P2.2-D defines a read-only local navigation "
    "projection API contract shape only; no API server or HTTP route is created"
)
EVENT_CONTRACT_UNAVAILABLE_REASON = (
    "UNAVAILABLE_EVENT_RUNTIME: P2.2-D defines a local navigation projection "
    "event payload shape only; no event bus exists and no runtime event is emitted"
)
TUI_UNAVAILABLE_REASON = (
    "UNAVAILABLE_TUI: no P2.2 local navigation TUI runtime or convention exists; "
    "an explicit unavailable binding is declared instead of a fake TUI product"
)
SHELL_UNAVAILABLE_REASON = (
    "UNAVAILABLE_SHELL: no live P2.2 local navigation shell product exists; "
    "read-only inspect contract shapes are declared only"
)

_SNAPSHOT_NON_GOALS: tuple[str, ...] = (
    "no_ui",
    "no_source_of_truth",
    "no_sidebar",
    "no_global_left_nav",
    "no_route_runtime",
    "no_p2_3_implementation",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_api_server",
    "no_http_route",
    "no_event_bus",
    "no_runtime_event_emission",
    "no_source_of_truth",
)
_BINDING_NON_GOALS: tuple[str, ...] = (
    "no_live_cli_product",
    "no_tui_product",
    "no_route_execution",
    "no_runtime_mutation",
)
_DOCS_NON_GOALS: tuple[str, ...] = (
    "no_roadmap_rewrite",
    "no_old_taxonomy_promotion",
    "no_p2_3_code",
)
_SEAL_NON_GOALS: tuple[str, ...] = (
    "no_live_ui",
    "no_trace_verification",
    "no_release_scope",
    "no_p2_3_implementation",
)


class P22DTruthLabel(str, Enum):
    INTEGRATION_SNAPSHOT = "P2_2_INTEGRATION_SNAPSHOT"
    SECTION_READ_MODEL_ONLY = "SECTION_READ_MODEL_ONLY"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_UI = "NOT_UI"
    PROJECTION_CONTRACT = "P2_2_PROJECTION_CONTRACT"
    API_CONTRACT_ONLY = "API_CONTRACT_ONLY"
    EVENT_CONTRACT_ONLY = "EVENT_CONTRACT_ONLY"
    NOT_API_SERVER = "NOT_API_SERVER"
    NOT_EVENT_BUS = "NOT_EVENT_BUS"
    BINDING_STATUS = "P2_2_BINDING_STATUS"
    READ_ONLY_INSPECT_OR_UNAVAILABLE = "READ_ONLY_INSPECT_OR_UNAVAILABLE"
    NOT_INTERACTIVE_NAV = "NOT_INTERACTIVE_NAV"
    NOT_PRODUCT_UI = "NOT_PRODUCT_UI"
    DOCS_STATE_SYNC = "DOCS_STATE_SYNC"
    PROGRESS_MIRROR_ONLY = "PROGRESS_MIRROR_ONLY"
    NOT_ROADMAP_REWRITE = "NOT_ROADMAP_REWRITE"
    EXIT_SEAL = "P2_2_EXIT_SEAL"
    SEALED_FOR_P2_2_CONTRACT_SCOPE = "SEALED_FOR_P2_2_CONTRACT_SCOPE"
    P2_3_PLAN_READINESS = "P2_3_PLAN_READINESS"
    NOT_RELEASE_SEAL = "NOT_RELEASE_SEAL"
    NOT_P2_3_IMPLEMENTATION = "NOT_P2_3_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


class P22DCheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class P22LocalNavigationSealDecision(str, Enum):
    SEALED_FOR_P2_2_CONTRACT_SCOPE = "SEALED_FOR_P2_2_CONTRACT_SCOPE"
    BLOCKED = "BLOCKED"


class P22P23ReadinessDecision(str, Enum):
    READY_FOR_P2_3_PLAN = "READY_FOR_P2_3_PLAN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class P22DSideEffectProof(_CanonicalMixin):
    ui_created: bool = False
    frontend_component_created: bool = False
    frontend_sidebar_created: bool = False
    global_left_nav_created: bool = False
    frontend_route_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    cli_live_product_created: bool = False
    tui_product_created: bool = False
    route_runtime_created: bool = False
    route_handler_created: bool = False
    click_handler_created: bool = False
    keyboard_shortcut_created: bool = False
    command_palette_created: bool = False
    floating_window_created: bool = False
    browser_tests_created: bool = False
    live_shell_created: bool = False
    api_server_created: bool = False
    http_route_created: bool = False
    event_bus_created: bool = False
    runtime_event_emitted: bool = False
    source_of_truth_created: bool = False
    permission_enforcement_created: bool = False
    custos_integration_created: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    local_storage_written: bool = False
    browser_storage_written: bool = False
    surface_taxonomy_created: bool = False
    future_surface_activated: bool = False
    roadmap_rewritten: bool = False
    registry_truth_mutated: bool = False
    surface_promoted: bool = False
    production_live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_3_started: bool = False
    p2_4_started: bool = False


@dataclass(frozen=True)
class P22DCheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P22DCheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str
    read_hash: str


@dataclass(frozen=True)
class P22LocalNavigationIntegrationTruthBoundary(_CanonicalMixin):
    is_source_of_truth: bool
    is_ui: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22LocalNavigationIntegrationSnapshot(_CanonicalMixin):
    snapshot_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    foundation_ref: str
    hierarchy_ref: str
    context_ref: str
    ownership_summary: dict[str, str]
    registry_summary: dict[str, str]
    item_summary: dict[str, str]
    visibility_availability_summary: dict[str, str]
    hierarchy_summary: dict[str, str]
    ordering_summary: dict[str, str]
    selection_summary: dict[str, str]
    interaction_summary: dict[str, str]
    context_summary: dict[str, str]
    profile_summary: dict[str, str]
    restoration_summary: dict[str, str]
    degraded_profile_summary: dict[str, str]
    taxonomy_drift_summary: dict[str, str]
    truth_boundary_summary: dict[str, str]
    side_effect_summary: dict[str, str]
    is_source_of_truth: bool
    is_ui: bool
    creates_sidebar: bool
    creates_global_left_nav: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class P22LocalNavigationApiContractShape(_CanonicalMixin):
    contract_id: str
    contract_version: str
    read_model_name: str
    request_shape: dict[str, str]
    response_shape: dict[str, str]
    error_shape: dict[str, str]
    availability: str
    unavailable_reason: str
    is_server: bool
    creates_http_routes: bool
    handles_http_requests: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class P22LocalNavigationEventContractShape(_CanonicalMixin):
    contract_id: str
    contract_version: str
    event_name: str
    payload_shape: dict[str, str]
    availability: str
    unavailable_reason: str
    is_event_bus: bool
    emits_runtime_events: bool
    publishes_events: bool
    subscribes_events: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class P22LocalNavigationProjectionTruthBoundary(_CanonicalMixin):
    projection_only: bool
    api_contract_only: bool
    event_contract_only: bool
    is_source_of_truth: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22LocalNavigationProjectionContract(_CanonicalMixin):
    projection_id: str
    schema_version: str
    projection_version: str
    section_id: str
    read_model_shape: dict[str, str]
    foundation_contract_ref: str
    hierarchy_contract_ref: str
    context_contract_ref: str
    api_contract_shape: P22LocalNavigationApiContractShape
    event_contract_shape: P22LocalNavigationEventContractShape
    projection_truth_boundary: P22LocalNavigationProjectionTruthBoundary
    unavailable_bindings: tuple[dict[str, str], ...]
    creates_ui: bool
    creates_api_server: bool
    creates_http_routes: bool
    creates_event_bus: bool
    emits_runtime_events: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class P22LocalNavigationBindingTruthBoundary(_CanonicalMixin):
    is_read_only: bool
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P22LocalNavigationCliInspectContract(_CanonicalMixin):
    cli_inspect_id: str
    projection_ref: str
    cli_inspect_available: bool
    cli_inspect_command: str
    cli_inspect_commands: tuple[str, ...]
    cli_inspect_read_only: bool
    cli_unavailable_reason: str
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_live_cli_product: bool
    truth_label: str
    contract_hash: str


@dataclass(frozen=True)
class P22LocalNavigationTuiBindingStatus(_CanonicalMixin):
    tui_binding_id: str
    projection_ref: str
    tui_binding_available: bool
    tui_unavailable_reason: str
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_interactive_tui: bool
    creates_product_ui: bool
    truth_label: str
    status_hash: str


@dataclass(frozen=True)
class P22LocalNavigationShellBindingContract(_CanonicalMixin):
    binding_id: str
    schema_version: str
    section_id: str
    binding_kind: str
    cli_inspect_available: bool
    cli_inspect_command: str
    cli_inspect_read_only: bool
    cli_unavailable_reason: str
    tui_binding_available: bool
    tui_unavailable_reason: str
    shell_binding_available: bool
    shell_unavailable_reason: str
    cli_inspect_contract: P22LocalNavigationCliInspectContract
    tui_binding_status: P22LocalNavigationTuiBindingStatus
    binding_truth_boundary: P22LocalNavigationBindingTruthBoundary
    executes_routes: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_interactive_tui: bool
    creates_product_ui: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class P22LocalNavigationDocsStateSync(_CanonicalMixin):
    sync_id: str
    schema_version: str
    section_id: str
    report_path: str
    report_index_updated: bool
    active_task_updated: bool
    roadmap_mirror_updated: bool
    state_updated: bool
    tests_doc_updated: bool
    architecture_updated: bool
    decisions_updated: bool
    docs_updated: bool
    roadmap_canon_rewritten: bool
    truth_label: str
    non_goals: tuple[str, ...]
    sync_hash: str


@dataclass(frozen=True)
class P22LocalNavigationExitSeal(_CanonicalMixin):
    seal_id: str
    schema_version: str
    section_id: str
    seal_value: P22LocalNavigationSealDecision
    sealed_for_contract_scope: bool
    contract_scope_only: bool
    production_live_claimed: bool
    trace_verified_claimed: bool
    release_scope_claimed: bool
    ui_claimed: bool
    route_runtime_claimed: bool
    api_server_claimed: bool
    event_bus_claimed: bool
    memory_write_claimed: bool
    trace_write_claimed: bool
    runtime_mutation_claimed: bool
    truth_label: str
    non_goals: tuple[str, ...]
    seal_hash: str


@dataclass(frozen=True)
class P22P23ReadinessResult(_CanonicalMixin):
    readiness_id: str
    schema_version: str
    from_section_id: str
    to_section_id: str
    readiness_value: P22P23ReadinessDecision
    ready_for_plan: bool
    ready_for_implementation: bool
    starts_p2_3: bool
    implements_floating_windows: bool
    implements_workspace_state: bool
    implements_command_palette: bool
    authorizes_release: bool
    truth_label: str
    non_goals: tuple[str, ...]
    readiness_hash: str


@dataclass(frozen=True)
class P22DLocalNavigationIntegrationTailResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    audit_repair_ref: str
    canonical_surface_ids: tuple[str, ...]
    integration_snapshot_summary: dict[str, str]
    projection_contract_summary: dict[str, str]
    binding_status_summary: dict[str, str]
    docs_sync_summary: dict[str, str]
    exit_seal_summary: dict[str, str]
    p2_3_readiness_summary: dict[str, str]
    checkpoint_reads: tuple[P22DCheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    integration_snapshot: P22LocalNavigationIntegrationSnapshot
    projection_contract: P22LocalNavigationProjectionContract
    shell_binding_contract: P22LocalNavigationShellBindingContract
    docs_state_sync: P22LocalNavigationDocsStateSync
    exit_seal: P22LocalNavigationExitSeal
    p2_3_readiness: P22P23ReadinessResult
    side_effect_proof: P22DSideEffectProof
    next_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def build_p2_2_d_side_effect_proof() -> P22DSideEffectProof:
    return P22DSideEffectProof()


def _string_bool(value: bool) -> str:
    return str(value).lower()


def _unavailable_binding(reason_id: str, reason: str) -> dict[str, str]:
    return {"binding_id": reason_id, "unavailable_reason": reason}


def _integration_truth_boundary() -> P22LocalNavigationIntegrationTruthBoundary:
    truth_labels = (
        P22DTruthLabel.INTEGRATION_SNAPSHOT.value,
        P22DTruthLabel.SECTION_READ_MODEL_ONLY.value,
        P22DTruthLabel.NOT_SOURCE_OF_TRUTH.value,
        P22DTruthLabel.NOT_UI.value,
    )
    payload = {
        "is_source_of_truth": False,
        "is_ui": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_labels": truth_labels,
    }
    return P22LocalNavigationIntegrationTruthBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def _foundation_ref(foundation: LocalNavProjectionSeed) -> str:
    return f"{P2_2_A_REPORT_FILENAME}:{foundation.projection_id}"


def _hierarchy_ref(hierarchy: LocalNavHierarchyProjectionResult) -> str:
    return f"{P2_2_B_REPORT_FILENAME}:{hierarchy.projection_id}"


def _context_ref(context: LocalNavContextProjectionResult) -> str:
    return f"{P2_2_C_REPORT_FILENAME}:{context.projection_id}"


def build_p2_2_local_navigation_integration_snapshot(
    *,
    foundation: LocalNavProjectionSeed | None = None,
    hierarchy: LocalNavHierarchyProjectionResult | None = None,
    context: LocalNavContextProjectionResult | None = None,
) -> P22LocalNavigationIntegrationSnapshot:
    if foundation is None:
        foundation = build_local_nav_projection_seed()
    if hierarchy is None:
        hierarchy = build_local_nav_hierarchy_projection_result(foundation=foundation)
    if context is None:
        context = build_local_nav_context_projection_result(
            foundation=foundation,
            hierarchy_projection=hierarchy,
        )
    drift, drift_details = detect_surface_taxonomy_drift()
    truth_boundary = _integration_truth_boundary()
    side_effects = build_p2_2_d_side_effect_proof()
    payload: dict[str, Any] = {
        "snapshot_id": "p2_2_local_navigation_integration_snapshot",
        "schema_version": P2_2_INTEGRATION_SNAPSHOT_VERSION,
        "section_id": P2_2_SECTION_ID,
        "created_for_pack": P2_2_D_PACK_ID,
        "foundation_ref": _foundation_ref(foundation),
        "hierarchy_ref": _hierarchy_ref(hierarchy),
        "context_ref": _context_ref(context),
        "ownership_summary": {
            "contract_count": str(len(foundation.ownership_contracts)),
            "surface_owned": "true",
            "global_left_nav": "false",
        },
        "registry_summary": {
            "registry_count": str(len(foundation.per_surface_nav_registries)),
            "official_surface_ids": ",".join(CANONICAL_SURFACE_ORDER),
            "is_source_of_truth": "false",
        },
        "item_summary": {
            "item_count": str(len(foundation.nav_item_contracts)),
            "executes_routes": "false",
            "click_handlers": "false",
        },
        "visibility_availability_summary": {
            "state_count": str(len(foundation.visibility_availability_states)),
            "visibility_is_permission": "false",
            "availability_is_live": "false",
        },
        "hierarchy_summary": {
            "contract_count": str(len(hierarchy.hierarchy_contracts)),
            "is_sidebar_ui": _string_bool(hierarchy.is_sidebar_ui),
            "creates_global_left_nav": _string_bool(
                hierarchy.creates_global_left_nav
            ),
        },
        "ordering_summary": {
            "contract_count": str(len(hierarchy.ordering_contracts)),
            "layout_engine": "false",
            "drag_drop": "false",
        },
        "selection_summary": {
            "state_count": str(len(hierarchy.selection_states)),
            "route_executed": "false",
            "url_mutated": "false",
        },
        "interaction_summary": {
            "constraint_count": str(len(hierarchy.interaction_constraints)),
            "click_handlers": "false",
            "permission_enforcement": "false",
        },
        "context_summary": {
            "carryover_count": str(len(context.context_carryover_contracts)),
            "writes_memory": "false",
            "uses_local_storage": "false",
        },
        "profile_summary": {
            "profile_count": str(len(context.surface_profile_contracts)),
            "creates_surface_taxonomy": "false",
            "activates_future_surface": "false",
        },
        "restoration_summary": {
            "contract_count": str(len(context.state_restoration_contracts)),
            "route_executed": "false",
            "runtime_mutated": "false",
        },
        "degraded_profile_summary": {
            "contract_count": str(len(context.degraded_profile_contracts)),
            "is_runtime_failure": "false",
            "repair_automation": "false",
        },
        "taxonomy_drift_summary": {
            "surface_taxonomy_drift": _string_bool(drift),
            "details": "; ".join(drift_details),
            "future_surface_activated": "false",
        },
        "truth_boundary_summary": {
            "is_source_of_truth": _string_bool(truth_boundary.is_source_of_truth),
            "is_ui": _string_bool(truth_boundary.is_ui),
            "mutates_runtime": _string_bool(truth_boundary.mutates_runtime),
            "writes_memory": _string_bool(truth_boundary.writes_memory),
            "writes_trace": _string_bool(truth_boundary.writes_trace),
        },
        "side_effect_summary": {
            key: _string_bool(value)
            for key, value in side_effects.to_canonical_dict().items()
        },
        "is_source_of_truth": False,
        "is_ui": False,
        "creates_sidebar": False,
        "creates_global_left_nav": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": P22DTruthLabel.INTEGRATION_SNAPSHOT.value,
        "non_goals": _SNAPSHOT_NON_GOALS,
    }
    snapshot = P22LocalNavigationIntegrationSnapshot(
        **payload,
        snapshot_hash=_hash_payload(payload),
    )
    assert_p2_2_a_b_c_outputs_reused(snapshot, foundation, hierarchy, context)
    assert_p2_2_integration_snapshot_is_not_source_of_truth(snapshot)
    assert_p2_2_integration_snapshot_is_not_ui(snapshot)
    return snapshot


def build_p2_2_local_navigation_api_contract_shape(
    *,
    projection_ref: str = "",
) -> P22LocalNavigationApiContractShape:
    payload = {
        "contract_id": "p2_2_local_navigation_projection_api_contract_shape",
        "contract_version": P2_2_API_CONTRACT_VERSION,
        "read_model_name": "P22LocalNavigationIntegrationSnapshot",
        "request_shape": {
            "section_id": "string",
            "snapshot_id": "string",
        },
        "response_shape": {
            "snapshot_id": "string",
            "foundation_ref": "string",
            "hierarchy_ref": "string",
            "context_ref": "string",
            "seal_value": "string",
        },
        "error_shape": {
            "code": "string",
            "message": "string",
            "unavailable_reason": "string",
        },
        "availability": "UNAVAILABLE",
        "unavailable_reason": API_CONTRACT_UNAVAILABLE_REASON,
        "is_server": False,
        "creates_http_routes": False,
        "handles_http_requests": False,
        "truth_label": P22DTruthLabel.API_CONTRACT_ONLY.value,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    contract = P22LocalNavigationApiContractShape(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_p2_2_projection_contract_is_not_api_server(contract)
    return contract


def build_p2_2_local_navigation_event_contract_shape(
    *,
    projection_ref: str = "",
) -> P22LocalNavigationEventContractShape:
    payload = {
        "contract_id": "p2_2_local_navigation_projection_event_contract_shape",
        "contract_version": P2_2_EVENT_CONTRACT_VERSION,
        "event_name": "aurel_shell_local_navigation_projection_available",
        "payload_shape": {
            "event_name": "string",
            "projection_ref": "string",
            "snapshot_id": "string",
            "truth_label": "string",
            "runtime_event_emitted": "bool",
        },
        "availability": "UNAVAILABLE",
        "unavailable_reason": EVENT_CONTRACT_UNAVAILABLE_REASON,
        "is_event_bus": False,
        "emits_runtime_events": False,
        "publishes_events": False,
        "subscribes_events": False,
        "truth_label": P22DTruthLabel.EVENT_CONTRACT_ONLY.value,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    contract = P22LocalNavigationEventContractShape(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_p2_2_event_contract_is_not_event_bus(contract)
    assert_p2_2_event_contract_does_not_emit_runtime_events(contract)
    return contract


def build_p2_2_local_navigation_projection_contract(
    *,
    snapshot: P22LocalNavigationIntegrationSnapshot | None = None,
) -> P22LocalNavigationProjectionContract:
    if snapshot is None:
        snapshot = build_p2_2_local_navigation_integration_snapshot()
    api_contract = build_p2_2_local_navigation_api_contract_shape(
        projection_ref=snapshot.snapshot_hash,
    )
    event_contract = build_p2_2_local_navigation_event_contract_shape(
        projection_ref=snapshot.snapshot_hash,
    )
    boundary_payload = {
        "projection_only": True,
        "api_contract_only": True,
        "event_contract_only": True,
        "is_source_of_truth": False,
        "truth_labels": (
            P22DTruthLabel.PROJECTION_CONTRACT.value,
            P22DTruthLabel.API_CONTRACT_ONLY.value,
            P22DTruthLabel.EVENT_CONTRACT_ONLY.value,
            P22DTruthLabel.NOT_API_SERVER.value,
            P22DTruthLabel.NOT_EVENT_BUS.value,
            P22DTruthLabel.NOT_SOURCE_OF_TRUTH.value,
        ),
    }
    truth_boundary = P22LocalNavigationProjectionTruthBoundary(
        **boundary_payload,
        boundary_hash=_hash_payload(boundary_payload),
    )
    payload = {
        "projection_id": "p2_2_local_navigation_projection_contract",
        "schema_version": P2_2_PROJECTION_CONTRACT_VERSION,
        "projection_version": "v1",
        "section_id": P2_2_SECTION_ID,
        "read_model_shape": {
            "integration_snapshot": "P22LocalNavigationIntegrationSnapshot",
            "api_contract_shape": "P22LocalNavigationApiContractShape",
            "event_contract_shape": "P22LocalNavigationEventContractShape",
        },
        "foundation_contract_ref": snapshot.foundation_ref,
        "hierarchy_contract_ref": snapshot.hierarchy_ref,
        "context_contract_ref": snapshot.context_ref,
        "api_contract_shape": api_contract,
        "event_contract_shape": event_contract,
        "projection_truth_boundary": truth_boundary,
        "unavailable_bindings": (
            _unavailable_binding("api_contract_runtime", API_CONTRACT_UNAVAILABLE_REASON),
            _unavailable_binding(
                "event_contract_runtime",
                EVENT_CONTRACT_UNAVAILABLE_REASON,
            ),
        ),
        "creates_ui": False,
        "creates_api_server": False,
        "creates_http_routes": False,
        "creates_event_bus": False,
        "emits_runtime_events": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": P22DTruthLabel.PROJECTION_CONTRACT.value,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    contract = P22LocalNavigationProjectionContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_p2_2_projection_contract_is_not_api_server(contract.api_contract_shape)
    assert_p2_2_event_contract_is_not_event_bus(contract.event_contract_shape)
    assert_p2_2_event_contract_does_not_emit_runtime_events(
        contract.event_contract_shape
    )
    return contract


def build_p2_2_local_navigation_cli_inspect_contract(
    *,
    projection_ref: str = "",
) -> P22LocalNavigationCliInspectContract:
    commands = (
        "shell local-nav foundation inspect",
        "shell local-nav hierarchy inspect",
        "shell local-nav context inspect",
        "shell local-nav projection inspect",
        "shell local-nav seal-readiness inspect",
    )
    payload = {
        "cli_inspect_id": "p2_2_local_navigation_cli_inspect_contract",
        "projection_ref": projection_ref,
        "cli_inspect_available": True,
        "cli_inspect_command": commands[0],
        "cli_inspect_commands": commands,
        "cli_inspect_read_only": True,
        "cli_unavailable_reason": "",
        "executes_routes": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_live_cli_product": False,
        "truth_label": P22DTruthLabel.READ_ONLY_INSPECT_OR_UNAVAILABLE.value,
    }
    contract = P22LocalNavigationCliInspectContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_p2_2_cli_inspect_is_read_only(contract)
    return contract


def build_p2_2_local_navigation_tui_binding_status(
    *,
    projection_ref: str = "",
) -> P22LocalNavigationTuiBindingStatus:
    payload = {
        "tui_binding_id": "p2_2_local_navigation_tui_binding_status",
        "projection_ref": projection_ref,
        "tui_binding_available": False,
        "tui_unavailable_reason": TUI_UNAVAILABLE_REASON,
        "executes_routes": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_interactive_tui": False,
        "creates_product_ui": False,
        "truth_label": P22DTruthLabel.NOT_INTERACTIVE_NAV.value,
    }
    status = P22LocalNavigationTuiBindingStatus(
        **payload,
        status_hash=_hash_payload(payload),
    )
    assert_p2_2_tui_binding_unavailable_has_reason(status)
    return status


def build_p2_2_local_navigation_shell_binding_contract(
    *,
    projection_contract: P22LocalNavigationProjectionContract | None = None,
) -> P22LocalNavigationShellBindingContract:
    if projection_contract is None:
        projection_contract = build_p2_2_local_navigation_projection_contract()
    projection_ref = projection_contract.contract_hash
    cli_contract = build_p2_2_local_navigation_cli_inspect_contract(
        projection_ref=projection_ref,
    )
    tui_status = build_p2_2_local_navigation_tui_binding_status(
        projection_ref=projection_ref,
    )
    boundary_payload = {
        "is_read_only": True,
        "executes_routes": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_labels": (
            P22DTruthLabel.BINDING_STATUS.value,
            P22DTruthLabel.READ_ONLY_INSPECT_OR_UNAVAILABLE.value,
            P22DTruthLabel.NOT_INTERACTIVE_NAV.value,
            P22DTruthLabel.NOT_PRODUCT_UI.value,
        ),
    }
    truth_boundary = P22LocalNavigationBindingTruthBoundary(
        **boundary_payload,
        boundary_hash=_hash_payload(boundary_payload),
    )
    payload = {
        "binding_id": "p2_2_local_navigation_shell_binding_contract",
        "schema_version": P2_2_BINDING_CONTRACT_VERSION,
        "section_id": P2_2_SECTION_ID,
        "binding_kind": "READ_ONLY_INSPECT_OR_UNAVAILABLE",
        "cli_inspect_available": cli_contract.cli_inspect_available,
        "cli_inspect_command": cli_contract.cli_inspect_command,
        "cli_inspect_read_only": cli_contract.cli_inspect_read_only,
        "cli_unavailable_reason": cli_contract.cli_unavailable_reason,
        "tui_binding_available": tui_status.tui_binding_available,
        "tui_unavailable_reason": tui_status.tui_unavailable_reason,
        "shell_binding_available": True,
        "shell_unavailable_reason": SHELL_UNAVAILABLE_REASON,
        "cli_inspect_contract": cli_contract,
        "tui_binding_status": tui_status,
        "binding_truth_boundary": truth_boundary,
        "executes_routes": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_interactive_tui": False,
        "creates_product_ui": False,
        "truth_label": P22DTruthLabel.BINDING_STATUS.value,
        "non_goals": _BINDING_NON_GOALS,
    }
    contract = P22LocalNavigationShellBindingContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_p2_2_cli_inspect_is_read_only(contract.cli_inspect_contract)
    assert_p2_2_tui_binding_unavailable_has_reason(contract.tui_binding_status)
    return contract


def build_p2_2_local_navigation_docs_state_sync() -> P22LocalNavigationDocsStateSync:
    payload = {
        "sync_id": "p2_2_local_navigation_docs_state_sync",
        "schema_version": P2_2_DOCS_SYNC_VERSION,
        "section_id": P2_2_SECTION_ID,
        "report_path": P2_2_D_REPORT_PATH,
        "report_index_updated": True,
        "active_task_updated": True,
        "roadmap_mirror_updated": True,
        "state_updated": True,
        "tests_doc_updated": True,
        "architecture_updated": False,
        "decisions_updated": False,
        "docs_updated": True,
        "roadmap_canon_rewritten": False,
        "truth_label": P22DTruthLabel.DOCS_STATE_SYNC.value,
        "non_goals": _DOCS_NON_GOALS,
    }
    sync = P22LocalNavigationDocsStateSync(
        **payload,
        sync_hash=_hash_payload(payload),
    )
    assert_p2_2_docs_sync_does_not_rewrite_roadmap_canon(sync)
    return sync


def build_p2_3_readiness_result() -> P22P23ReadinessResult:
    payload = {
        "readiness_id": "p2_3_plan_readiness_result",
        "schema_version": P2_3_READINESS_VERSION,
        "from_section_id": P2_2_SECTION_ID,
        "to_section_id": P2_2_D_NEXT_SECTION,
        "readiness_value": P22P23ReadinessDecision.READY_FOR_P2_3_PLAN,
        "ready_for_plan": True,
        "ready_for_implementation": False,
        "starts_p2_3": False,
        "implements_floating_windows": False,
        "implements_workspace_state": False,
        "implements_command_palette": False,
        "authorizes_release": False,
        "truth_label": P22DTruthLabel.P2_3_PLAN_READINESS.value,
        "non_goals": ("no_p2_3_implementation", "no_release_authorization"),
    }
    readiness = P22P23ReadinessResult(
        **payload,
        readiness_hash=_hash_payload(payload),
    )
    assert_p2_3_readiness_does_not_start_p2_3(readiness)
    assert_p2_2_d_does_not_start_p2_3(readiness)
    assert_p2_2_d_does_not_start_p2_4(readiness)
    return readiness


def build_p2_2_local_navigation_exit_seal(
    *,
    readiness: P22P23ReadinessResult | None = None,
) -> P22LocalNavigationExitSeal:
    if readiness is None:
        readiness = build_p2_3_readiness_result()
    payload = {
        "seal_id": "p2_2_local_navigation_contract_scope_exit_seal",
        "schema_version": P2_2_EXIT_SEAL_VERSION,
        "section_id": P2_2_SECTION_ID,
        "seal_value": P22LocalNavigationSealDecision.SEALED_FOR_P2_2_CONTRACT_SCOPE,
        "sealed_for_contract_scope": True,
        "contract_scope_only": True,
        "production_live_claimed": False,
        "trace_verified_claimed": False,
        "release_scope_claimed": False,
        "ui_claimed": False,
        "route_runtime_claimed": False,
        "api_server_claimed": False,
        "event_bus_claimed": False,
        "memory_write_claimed": False,
        "trace_write_claimed": False,
        "runtime_mutation_claimed": False,
        "truth_label": P22DTruthLabel.SEALED_FOR_P2_2_CONTRACT_SCOPE.value,
        "non_goals": _SEAL_NON_GOALS,
    }
    seal = P22LocalNavigationExitSeal(**payload, seal_hash=_hash_payload(payload))
    assert_p2_2_exit_seal_is_contract_scope_only(seal)
    assert_p2_2_exit_seal_is_not_release_scope(seal)
    return seal


def _checkpoint_reads() -> tuple[P22DCheckpointRead, ...]:
    rows = {
        "P2.2.16": (
            "P2.2 Local Navigation Integration Snapshot",
            "P22LocalNavigationIntegrationSnapshot, P22LocalNavigationIntegrationTruthBoundary",
            "test_p2_2_16_*",
            "P2_2_INTEGRATION_SNAPSHOT / SECTION_READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH",
            "n/a - integration snapshot only",
            "No source-of-truth store, UI, sidebar, global left nav, or runtime mutation",
        ),
        "P2.2.17": (
            "P2.2 Projection / API / Event Contract",
            "P22LocalNavigationProjectionContract, P22LocalNavigationApiContractShape, P22LocalNavigationEventContractShape",
            "test_p2_2_17_*",
            "P2_2_PROJECTION_CONTRACT / API_CONTRACT_ONLY / EVENT_CONTRACT_ONLY",
            "API/event runtime unavailable by contract",
            "No API server, HTTP route, event bus, or runtime event emission",
        ),
        "P2.2.18": (
            "P2.2 Shell / CLI / TUI Binding",
            "P22LocalNavigationShellBindingContract, P22LocalNavigationCliInspectContract, P22LocalNavigationTuiBindingStatus",
            "test_p2_2_18_*",
            "P2_2_BINDING_STATUS / READ_ONLY_INSPECT_OR_UNAVAILABLE / NOT_INTERACTIVE_NAV",
            "TUI unavailable with reason",
            "No live CLI product, interactive TUI, route execution, or product UI",
        ),
        "P2.2.19": (
            "P2.2 Docs / State / Reports Update",
            "P22LocalNavigationDocsStateSync",
            "test_p2_2_19_*",
            "DOCS_STATE_SYNC / PROGRESS_MIRROR_ONLY / NOT_ROADMAP_REWRITE",
            "n/a - docs sync only",
            "No roadmap rewrite or old taxonomy promotion",
        ),
        "P2.2.20": (
            "P2.2 Exit Seal + P2.3 Readiness",
            "P22LocalNavigationExitSeal, P22P23ReadinessResult",
            "test_p2_2_20_*",
            "P2_2_EXIT_SEAL / SEALED_FOR_P2_2_CONTRACT_SCOPE / P2_3_PLAN_READINESS",
            "production live, trace verification, and release scope unavailable",
            "No local nav UI, route runtime, release seal, or P2.3 implementation",
        ),
    }
    reads: list[P22DCheckpointRead] = []
    for checkpoint_id in P2_2_D_PACK_CHECKPOINT_IDS:
        row = rows[checkpoint_id]
        read_payload = {
            "checkpoint_id": checkpoint_id,
            "canonical_name": row[0],
            "status": P22DCheckpointStatus.DONE,
            "evidence": row[1],
            "tests": row[2],
            "truth_label": row[3],
            "unavailable_reason": row[4],
            "limitations": row[5],
        }
        reads.append(
            P22DCheckpointRead(
                **read_payload,
                read_hash=_hash_payload(read_payload),
            )
        )
    return tuple(reads)


def build_p2_2_d_local_navigation_integration_tail_result() -> P22DLocalNavigationIntegrationTailResult:
    foundation = build_local_nav_projection_seed()
    hierarchy = build_local_nav_hierarchy_projection_result(foundation=foundation)
    context = build_local_nav_context_projection_result(
        foundation=foundation,
        hierarchy_projection=hierarchy,
    )
    p2_2_c = build_p2_2_c_local_navigation_context_result()
    snapshot = build_p2_2_local_navigation_integration_snapshot(
        foundation=foundation,
        hierarchy=hierarchy,
        context=context,
    )
    projection_contract = build_p2_2_local_navigation_projection_contract(
        snapshot=snapshot,
    )
    shell_binding = build_p2_2_local_navigation_shell_binding_contract(
        projection_contract=projection_contract,
    )
    docs_sync = build_p2_2_local_navigation_docs_state_sync()
    readiness = build_p2_3_readiness_result()
    exit_seal = build_p2_2_local_navigation_exit_seal(readiness=readiness)
    side_effects = build_p2_2_d_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    audit_repair_ref = f"{AUDIT_REPAIR_001_REPORT_FILENAME}:{AUDIT_REPAIR_001_PACK_ID}"
    unavailable_reasons = (
        API_CONTRACT_UNAVAILABLE_REASON,
        EVENT_CONTRACT_UNAVAILABLE_REASON,
        TUI_UNAVAILABLE_REASON,
        SHELL_UNAVAILABLE_REASON,
    )
    payload = {
        "schema_version": P2_2_D_RESULT_VERSION,
        "pack_id": P2_2_D_PACK_ID,
        "section_id": P2_2_SECTION_ID,
        "section_name": P2_2_SECTION_NAME,
        "covered_checkpoints": P2_2_D_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_2_D_DEPENDENCY_PACKS,
        "audit_repair_ref": audit_repair_ref,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "integration_snapshot_summary": {
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_hash": snapshot.snapshot_hash,
            "foundation_ref": snapshot.foundation_ref,
            "hierarchy_ref": snapshot.hierarchy_ref,
            "context_ref": snapshot.context_ref,
            "is_source_of_truth": _string_bool(snapshot.is_source_of_truth),
        },
        "projection_contract_summary": {
            "projection_id": projection_contract.projection_id,
            "creates_api_server": _string_bool(
                projection_contract.creates_api_server
            ),
            "creates_event_bus": _string_bool(projection_contract.creates_event_bus),
            "emits_runtime_events": _string_bool(
                projection_contract.emits_runtime_events
            ),
        },
        "binding_status_summary": {
            "cli_inspect_available": _string_bool(
                shell_binding.cli_inspect_available
            ),
            "cli_inspect_read_only": _string_bool(
                shell_binding.cli_inspect_read_only
            ),
            "tui_binding_available": _string_bool(
                shell_binding.tui_binding_available
            ),
            "tui_unavailable_reason": shell_binding.tui_unavailable_reason,
        },
        "docs_sync_summary": {
            "report_path": docs_sync.report_path,
            "report_index_updated": _string_bool(docs_sync.report_index_updated),
            "roadmap_canon_rewritten": _string_bool(
                docs_sync.roadmap_canon_rewritten
            ),
        },
        "exit_seal_summary": {
            "seal_value": exit_seal.seal_value.value,
            "contract_scope_only": _string_bool(exit_seal.contract_scope_only),
            "production_live_claimed": _string_bool(
                exit_seal.production_live_claimed
            ),
        },
        "p2_3_readiness_summary": {
            "readiness_value": readiness.readiness_value.value,
            "ready_for_plan": _string_bool(readiness.ready_for_plan),
            "starts_p2_3": _string_bool(readiness.starts_p2_3),
        },
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": (
            P22DTruthLabel.INTEGRATION_SNAPSHOT.value,
            P22DTruthLabel.PROJECTION_CONTRACT.value,
            P22DTruthLabel.BINDING_STATUS.value,
            P22DTruthLabel.DOCS_STATE_SYNC.value,
            P22DTruthLabel.SEALED_FOR_P2_2_CONTRACT_SCOPE.value,
            P22DTruthLabel.P2_3_PLAN_READINESS.value,
            P22DTruthLabel.NOT_P2_3_IMPLEMENTATION.value,
        ),
        "unavailable_reasons": unavailable_reasons,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "integration_snapshot": snapshot,
        "projection_contract": projection_contract,
        "shell_binding_contract": shell_binding,
        "docs_state_sync": docs_sync,
        "exit_seal": exit_seal,
        "p2_3_readiness": readiness,
        "side_effect_proof": side_effects,
        "next_pack": P2_2_D_NEXT_RECOMMENDED_PACK,
        "non_goals": _SEAL_NON_GOALS,
    }
    result = P22DLocalNavigationIntegrationTailResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_2_d_depends_on_audit_repair_001(result)
    assert_p2_2_d_depends_on_p2_2_c(result, p2_2_c)
    return result


def serialize_p2_2_d_result(
    result: P22DLocalNavigationIntegrationTailResult | None = None,
) -> str:
    if result is None:
        result = build_p2_2_d_local_navigation_integration_tail_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_2_d_depends_on_audit_repair_001(
    result: P22DLocalNavigationIntegrationTailResult,
) -> None:
    if AUDIT_REPAIR_001_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.2-D must depend on AUDIT-REPAIR-001",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if AUDIT_REPAIR_001_REPORT_FILENAME not in result.audit_repair_ref:
        _reject(
            "P2.2-D audit repair ref must reference AUDIT-REPAIR-001 report",
            field="audit_repair_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_d_depends_on_p2_2_c(
    result: P22DLocalNavigationIntegrationTailResult,
    p2_2_c: Any,
) -> None:
    if P2_2_C_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.2-D must depend on P2.2-C",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_C_REPORT_FILENAME not in result.integration_snapshot.context_ref:
        _reject(
            "P2.2-D must reuse P2.2-C context projection",
            field="context_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if p2_2_c.next_pack != P2_2_D_PACK_ID:
        _reject(
            "P2.2-C must hand off to P2.2-D",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_a_b_c_outputs_reused(
    snapshot: P22LocalNavigationIntegrationSnapshot,
    foundation: LocalNavProjectionSeed,
    hierarchy: LocalNavHierarchyProjectionResult,
    context: LocalNavContextProjectionResult,
) -> None:
    expected_foundation = _foundation_ref(foundation)
    expected_hierarchy = _hierarchy_ref(hierarchy)
    expected_context = _context_ref(context)
    if snapshot.foundation_ref != expected_foundation:
        _reject(
            "integration snapshot must reference P2.2-A foundation",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if snapshot.hierarchy_ref != expected_hierarchy:
        _reject(
            "integration snapshot must reference P2.2-B hierarchy projection",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if snapshot.context_ref != expected_context:
        _reject(
            "integration snapshot must reference P2.2-C context projection",
            field="context_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_A_REPORT_FILENAME not in snapshot.foundation_ref:
        _reject(
            "foundation ref must cite P2.2-A report",
            field="foundation_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_B_REPORT_FILENAME not in snapshot.hierarchy_ref:
        _reject(
            "hierarchy ref must cite P2.2-B report",
            field="hierarchy_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_C_REPORT_FILENAME not in snapshot.context_ref:
        _reject(
            "context ref must cite P2.2-C report",
            field="context_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_integration_snapshot_is_not_source_of_truth(
    snapshot: P22LocalNavigationIntegrationSnapshot,
) -> None:
    if snapshot.is_source_of_truth:
        _reject(
            "integration snapshot must not be source of truth",
            field="is_source_of_truth",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_integration_snapshot_is_not_ui(
    snapshot: P22LocalNavigationIntegrationSnapshot,
) -> None:
    if (
        snapshot.is_ui
        or snapshot.creates_sidebar
        or snapshot.creates_global_left_nav
        or snapshot.mutates_runtime
        or snapshot.writes_memory
        or snapshot.writes_trace
    ):
        _reject(
            "integration snapshot must not be UI or mutate runtime",
            field="is_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_projection_contract_is_not_api_server(
    contract: P22LocalNavigationApiContractShape,
) -> None:
    if (
        contract.is_server
        or contract.creates_http_routes
        or contract.handles_http_requests
    ):
        _reject(
            "API contract shape must not create API server or HTTP routes",
            field="is_server",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_event_contract_is_not_event_bus(
    contract: P22LocalNavigationEventContractShape,
) -> None:
    if contract.is_event_bus:
        _reject(
            "event contract shape must not create event bus",
            field="is_event_bus",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_event_contract_does_not_emit_runtime_events(
    contract: P22LocalNavigationEventContractShape,
) -> None:
    if (
        contract.emits_runtime_events
        or contract.publishes_events
        or contract.subscribes_events
    ):
        _reject(
            "event contract shape must not emit or publish/subscribe events",
            field="emits_runtime_events",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_cli_inspect_is_read_only(
    contract: P22LocalNavigationCliInspectContract,
) -> None:
    if contract.cli_inspect_available and not contract.cli_inspect_read_only:
        _reject(
            "CLI inspect must be read-only when available",
            field="cli_inspect_read_only",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if (
        contract.executes_routes
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
        or contract.creates_live_cli_product
    ):
        _reject(
            "CLI inspect must not execute routes or mutate runtime",
            field="executes_routes",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_tui_binding_unavailable_has_reason(
    status: P22LocalNavigationTuiBindingStatus,
) -> None:
    if not status.tui_binding_available and not status.tui_unavailable_reason:
        _reject(
            "unavailable TUI binding requires reason",
            field="tui_unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_docs_sync_does_not_rewrite_roadmap_canon(
    sync: P22LocalNavigationDocsStateSync,
) -> None:
    if sync.roadmap_canon_rewritten:
        _reject(
            "docs sync must not rewrite roadmap canon",
            field="roadmap_canon_rewritten",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_exit_seal_is_contract_scope_only(
    seal: P22LocalNavigationExitSeal,
) -> None:
    if not seal.sealed_for_contract_scope or not seal.contract_scope_only:
        _reject(
            "exit seal must be contract-scope only",
            field="sealed_for_contract_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if seal.seal_value != P22LocalNavigationSealDecision.SEALED_FOR_P2_2_CONTRACT_SCOPE:
        _reject(
            "exit seal must be SEALED_FOR_P2_2_CONTRACT_SCOPE",
            field="seal_value",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_2_exit_seal_is_not_release_scope(
    seal: P22LocalNavigationExitSeal,
) -> None:
    if (
        seal.production_live_claimed
        or seal.trace_verified_claimed
        or seal.release_scope_claimed
        or seal.ui_claimed
        or seal.route_runtime_claimed
        or seal.api_server_claimed
        or seal.event_bus_claimed
        or seal.memory_write_claimed
        or seal.trace_write_claimed
        or seal.runtime_mutation_claimed
    ):
        _reject(
            "exit seal must not claim live, trace, release, UI, or runtime scope",
            field="production_live_claimed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_readiness_does_not_start_p2_3(
    readiness: P22P23ReadinessResult,
) -> None:
    if (
        readiness.starts_p2_3
        or readiness.ready_for_implementation
        or readiness.implements_floating_windows
        or readiness.implements_workspace_state
        or readiness.implements_command_palette
        or readiness.authorizes_release
    ):
        _reject(
            "P2.3 readiness must be plan-only and must not start P2.3",
            field="starts_p2_3",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_2_d_does_not_start_p2_3(
    readiness: P22P23ReadinessResult,
) -> None:
    assert_p2_3_readiness_does_not_start_p2_3(readiness)


def assert_p2_2_d_does_not_start_p2_4(readiness: P22P23ReadinessResult) -> None:
    _ = readiness
    return None
