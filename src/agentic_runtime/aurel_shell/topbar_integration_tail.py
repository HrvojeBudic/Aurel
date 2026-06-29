"""P2.1-D topbar integration tail, projection contract, binding, and seal.

Contract-only section closure over P2.1-A/B/C. This module creates deterministic
read-model artifacts for inspection and handoff; it does not create UI, routes,
API servers, event buses, runtime events, local navigation, or P2.2 behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .read_model import detect_surface_taxonomy_drift
from .topbar import (
    P2_1_SECTION_ID,
    P2_1_SECTION_NAME,
    P21CheckpointRead,
    P21CheckpointStatus,
    SurfaceRegistry,
    TopbarReadModel,
    build_default_topbar_surface_registry,
    build_global_topbar_read_model,
    build_p2_1_a_global_topbar_surface_registry_result,
)
from .topbar_route_visibility import (
    P2_1_A_REPORT_FILENAME,
    P2_1_B_REPORT_FILENAME,
    P2_1_C_PACK_ID,
    P21CTopbarRouteVisibilityPackResult,
    TopbarRouteVisibilityProjection,
    build_p2_1_c_topbar_route_visibility_result,
    build_topbar_route_visibility_projection,
)
from .topbar_status import (
    P2_1_B_PACK_ID,
    P21BTopbarStatusSlotsPackResult,
    TopbarStatusProjection,
    build_p2_1_b_topbar_status_slots_result,
    build_topbar_status_projection,
)

P2_1_D_PACK_ID = "P2.1-D"
P2_1_D_PACK_NAME = (
    "P2.1 Integration Tail / Projection / Binding / Docs / Section Handoff"
)
P2_1_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.1.16",
    "P2.1.17",
    "P2.1.18",
    "P2.1.19",
    "P2.1.20",
)
P2_1_D_DEPENDENCY_PACKS: tuple[str, ...] = ("P2.1-A", "P2.1-B", "P2.1-C")
P2_1_D_REPORT_FILENAME = "P2_1_D_TOPBAR_INTEGRATION_TAIL.md"
P2_1_D_REPORT_PATH = f"agent/reports/{P2_1_D_REPORT_FILENAME}"
P2_1_D_NEXT_SECTION = "P2.2"
P2_1_D_NEXT_SECTION_NAME = "Per-Surface Local Navigation"
P2_1_D_NEXT_RECOMMENDED_PACK = "P2.2-A"

P2_1_D_RESULT_VERSION = "p2_1_d_topbar_integration_tail_result.v1"
P2_1_INTEGRATION_SNAPSHOT_VERSION = "p2_1_topbar_integration_snapshot.v1"
P2_1_CAPABILITY_MAP_VERSION = "p2_1_topbar_capability_map.v1"
P2_1_PROJECTION_CONTRACT_VERSION = "p2_1_topbar_projection_contract.v1"
P2_1_BINDING_CONTRACT_VERSION = "p2_1_topbar_shell_binding_contract.v1"
P2_1_DOCS_SYNC_VERSION = "p2_1_docs_state_report_sync.v1"
P2_1_EXIT_SEAL_VERSION = "p2_1_topbar_exit_seal.v1"
P2_2_READINESS_VERSION = "p2_2_readiness_result.v1"

API_CONTRACT_UNAVAILABLE_REASON = (
    "UNAVAILABLE_API_RUNTIME: P2.1-D defines a read-only topbar projection API "
    "contract shape only; no API server or HTTP route is created"
)
EVENT_CONTRACT_UNAVAILABLE_REASON = (
    "UNAVAILABLE_EVENT_RUNTIME: P2.1-D defines a topbar projection event "
    "payload shape only; no event bus exists and no runtime event is emitted"
)
TUI_UNAVAILABLE_REASON = (
    "UNAVAILABLE_TUI: no P2.1 topbar TUI runtime or convention exists; an "
    "explicit unavailable binding is declared instead of a fake TUI product"
)

_SNAPSHOT_NON_GOALS: tuple[str, ...] = (
    "no_ui",
    "no_source_of_truth",
    "no_route_runtime",
    "no_registry_truth_mutation",
    "no_p2_2_implementation",
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
    "no_surface_switch",
    "no_runtime_mutation",
)
_DOCS_NON_GOALS: tuple[str, ...] = (
    "no_roadmap_rewrite",
    "no_old_taxonomy_promotion",
    "no_p2_2_code",
)
_SEAL_NON_GOALS: tuple[str, ...] = (
    "no_live_ui",
    "no_trace_verification",
    "no_release_scope",
    "no_local_navigation",
    "no_p2_2_implementation",
)


class P21DTruthLabel(str, Enum):
    INTEGRATION_SNAPSHOT = "INTEGRATION_SNAPSHOT"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_LIVE_UI = "NOT_LIVE_UI"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    API_CONTRACT_ONLY = "API_CONTRACT_ONLY"
    EVENT_CONTRACT_ONLY = "EVENT_CONTRACT_ONLY"
    NOT_API_SERVER = "NOT_API_SERVER"
    NOT_EVENT_EMISSION = "NOT_EVENT_EMISSION"
    READ_ONLY_INSPECT = "READ_ONLY_INSPECT"
    CLI_CONTRACT_ONLY = "CLI_CONTRACT_ONLY"
    TUI_UNAVAILABLE_WITH_REASON = "TUI_UNAVAILABLE_WITH_REASON"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    REPORT_EVIDENCE = "REPORT_EVIDENCE"
    PROGRESS_MIRROR_ONLY = "PROGRESS_MIRROR_ONLY"
    NOT_ROADMAP_REWRITE = "NOT_ROADMAP_REWRITE"
    NOT_TAXONOMY_PROMOTION = "NOT_TAXONOMY_PROMOTION"
    SECTION_SEAL_CONTRACT_SCOPE = "SECTION_SEAL_CONTRACT_SCOPE"
    READY_FOR_P2_2_PLAN = "READY_FOR_P2_2_PLAN"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_P2_2_IMPLEMENTATION = "NOT_P2_2_IMPLEMENTATION"


class P21TopbarSealDecision(str, Enum):
    SEALED_FOR_P2_1_CONTRACT_SCOPE = "SEALED_FOR_P2_1_CONTRACT_SCOPE"
    BLOCKED = "BLOCKED"


class P21P22ReadinessDecision(str, Enum):
    READY_FOR_P2_2_PLAN = "READY_FOR_P2_2_PLAN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class P21DSideEffectProof(_CanonicalMixin):
    """P2.1-D side-effect / no-authority proof. Every field is false."""

    ui_created: bool = False
    frontend_component_created: bool = False
    frontend_route_created: bool = False
    web_client_created: bool = False
    desktop_client_created: bool = False
    mobile_client_created: bool = False
    cli_live_product_created: bool = False
    tui_product_created: bool = False
    route_runtime_created: bool = False
    route_handler_created: bool = False
    local_navigation_created: bool = False
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
    roadmap_rewritten: bool = False
    registry_truth_mutated: bool = False
    surface_promoted: bool = False
    production_live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_2_started: bool = False


@dataclass(frozen=True)
class P21TopbarIntegrationTruthBoundary(_CanonicalMixin):
    is_source_of_truth: bool
    is_live_ui: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P21TopbarIntegrationSnapshot(_CanonicalMixin):
    snapshot_id: str
    schema_version: str
    section_id: str
    section_name: str
    covered_packs: tuple[str, ...]
    covered_checkpoints: tuple[str, ...]
    registry_summary: dict[str, str]
    active_surface_summary: dict[str, str]
    switch_intent_summary: dict[str, str]
    operator_context_summary: dict[str, str]
    availability_summary: dict[str, str]
    protected_boundary_summary: dict[str, str]
    attention_status_summary: dict[str, str]
    route_visibility_summary: dict[str, str]
    interaction_constraint_summary: dict[str, str]
    blocked_deferred_summary: dict[str, str]
    registry_refinement_summary: dict[str, str]
    taxonomy_drift_summary: dict[str, str]
    truth_boundary_summary: dict[str, str]
    side_effect_summary: dict[str, str]
    unavailable_bindings: tuple[dict[str, str], ...]
    registry_ref: str
    topbar_read_model_ref: str
    status_projection_ref: str
    route_visibility_projection_ref: str
    p2_1_a_result_ref: str
    p2_1_b_result_ref: str
    p2_1_c_result_ref: str
    is_source_of_truth: bool
    is_live_ui: bool
    creates_ui: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_label: str
    non_goals: tuple[str, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class P21TopbarCapabilityMap(_CanonicalMixin):
    capability_map_id: str
    schema_version: str
    section_id: str
    capability_groups: dict[str, tuple[str, ...]]
    checkpoint_coverage: tuple[str, ...]
    p2_1_0_to_p2_1_5_summary: str
    p2_1_6_to_p2_1_10_summary: str
    p2_1_11_to_p2_1_15_summary: str
    p2_1_16_to_p2_1_20_summary: str
    missing_capabilities: tuple[str, ...]
    partial_capabilities: tuple[str, ...]
    unavailable_bindings: tuple[dict[str, str], ...]
    truth_label: str
    non_goals: tuple[str, ...]
    capability_map_hash: str


@dataclass(frozen=True)
class P21TopbarApiContractShape(_CanonicalMixin):
    api_contract_id: str
    projection_ref: str
    method_shape: str
    path_shape: str
    response_shape: dict[str, str]
    unavailable_reason: str
    api_server_created: bool
    http_route_created: bool
    mutates_runtime: bool
    truth_label: str
    contract_hash: str


@dataclass(frozen=True)
class P21TopbarEventContractShape(_CanonicalMixin):
    event_contract_id: str
    projection_ref: str
    event_name: str
    event_payload_shape: dict[str, str]
    unavailable_reason: str
    event_bus_created: bool
    runtime_event_emitted: bool
    mutates_runtime: bool
    writes_trace: bool
    truth_label: str
    contract_hash: str


@dataclass(frozen=True)
class P21TopbarProjectionTruthBoundary(_CanonicalMixin):
    projection_only: bool
    api_contract_only: bool
    event_contract_only: bool
    is_source_of_truth: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P21TopbarProjectionContract(_CanonicalMixin):
    contract_id: str
    schema_version: str
    projection_version: str
    section_id: str
    read_model_shape: dict[str, str]
    integration_snapshot_ref: str
    registry_contract_ref: str
    status_contract_ref: str
    route_visibility_contract_ref: str
    api_contract_shape: P21TopbarApiContractShape
    event_contract_shape: P21TopbarEventContractShape
    projection_truth_boundary: P21TopbarProjectionTruthBoundary
    api_server_created: bool
    http_route_created: bool
    event_bus_created: bool
    runtime_event_emitted: bool
    is_source_of_truth: bool
    truth_label: str
    unavailable_bindings: tuple[dict[str, str], ...]
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class P21TopbarBindingTruthBoundary(_CanonicalMixin):
    is_read_only: bool
    executes_routes: bool
    switches_surfaces: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P21TopbarCliInspectContract(_CanonicalMixin):
    cli_inspect_id: str
    projection_ref: str
    cli_inspect_available: bool
    cli_commands: tuple[str, ...]
    cli_unavailable_reason: str
    output_shape: dict[str, str]
    is_read_only: bool
    executes_routes: bool
    switches_surfaces: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_live_cli_product: bool
    truth_label: str
    contract_hash: str


@dataclass(frozen=True)
class P21TopbarTuiBindingStatus(_CanonicalMixin):
    tui_binding_id: str
    projection_ref: str
    tui_binding_available: bool
    tui_unavailable_reason: str
    is_read_only: bool
    executes_routes: bool
    switches_surfaces: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_tui_product: bool
    truth_label: str
    status_hash: str


@dataclass(frozen=True)
class P21TopbarShellBindingContract(_CanonicalMixin):
    binding_id: str
    schema_version: str
    section_id: str
    shell_binding_available: bool
    cli_inspect_available: bool
    cli_commands: tuple[str, ...]
    cli_unavailable_reason: str
    tui_binding_available: bool
    tui_unavailable_reason: str
    cli_inspect_contract: P21TopbarCliInspectContract
    tui_binding_status: P21TopbarTuiBindingStatus
    binding_truth_boundary: P21TopbarBindingTruthBoundary
    is_read_only: bool
    executes_routes: bool
    switches_surfaces: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_live_cli_product: bool
    creates_tui_product: bool
    truth_label: str
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class P21TopbarDocsSyncResult(_CanonicalMixin):
    sync_id: str
    schema_version: str
    report_created: bool
    report_path: str
    report_indexed: bool
    active_task_updated: bool
    roadmap_progress_updated: bool
    state_updated: bool
    decisions_updated: bool
    tests_updated: bool
    architecture_updated: bool
    architecture_update_reason: str
    roadmap_rewritten: bool
    old_taxonomy_promoted: bool
    truth_label: str
    non_goals: tuple[str, ...]
    sync_hash: str


@dataclass(frozen=True)
class P21TopbarDocsStateReportSync(_CanonicalMixin):
    sync_id: str
    schema_version: str
    docs_sync_result: P21TopbarDocsSyncResult
    report_path: str
    progress_mirror_only: bool
    next_task_points_to_p2_2_planning: bool
    p2_2_implementation_started: bool
    truth_labels: tuple[str, ...]
    sync_hash: str


@dataclass(frozen=True)
class P21TopbarExitSeal(_CanonicalMixin):
    seal_id: str
    schema_version: str
    section_id: str
    seal_decision: P21TopbarSealDecision
    sealed_scope: str
    ready_for_next_section: bool
    next_section: str
    next_pack_recommendation: str
    p2_2_readiness_decision: P21P22ReadinessDecision
    p2_1_a_evidence_checked: bool
    p2_1_b_evidence_checked: bool
    p2_1_c_evidence_checked: bool
    p2_1_d_evidence_checked: bool
    production_live_claimed: bool
    trace_verified_claimed: bool
    release_scope_claimed: bool
    visual_topbar_implemented: bool
    local_navigation_implemented: bool
    route_runtime_implemented: bool
    api_server_created: bool
    event_bus_created: bool
    p2_2_started: bool
    truth_label: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    non_goals: tuple[str, ...]
    seal_hash: str


@dataclass(frozen=True)
class P21P22ReadinessResult(_CanonicalMixin):
    readiness_id: str
    schema_version: str
    next_section: str
    next_section_name: str
    next_pack_recommendation: str
    p2_2_readiness_decision: P21P22ReadinessDecision
    readiness_is_plan_only: bool
    p2_2_started: bool
    p2_2_implemented: bool
    local_navigation_implemented: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    truth_label: str
    readiness_hash: str


@dataclass(frozen=True)
class P21DTopbarIntegrationTailPackResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    integration_snapshot_summary: dict[str, str]
    projection_contract_summary: dict[str, str]
    shell_cli_tui_binding_summary: dict[str, str]
    docs_sync_summary: dict[str, str]
    exit_seal_summary: dict[str, str]
    p2_2_readiness_summary: dict[str, str]
    checkpoint_reads: tuple[P21CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    side_effect_proof: P21DSideEffectProof
    integration_snapshot: P21TopbarIntegrationSnapshot
    capability_map: P21TopbarCapabilityMap
    projection_contract: P21TopbarProjectionContract
    shell_binding_contract: P21TopbarShellBindingContract
    docs_sync: P21TopbarDocsStateReportSync
    exit_seal: P21TopbarExitSeal
    p2_2_readiness: P21P22ReadinessResult
    next_section: str
    next_recommended_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def build_p2_1_d_side_effect_proof() -> P21DSideEffectProof:
    return P21DSideEffectProof()


def _string_bool(value: bool) -> str:
    return str(value).lower()


def _all_checkpoint_ids() -> tuple[str, ...]:
    return tuple(f"P2.1.{index}" for index in range(21))


def _unavailable_binding(reason_id: str, reason: str) -> dict[str, str]:
    return {"binding_id": reason_id, "unavailable_reason": reason}


def _collect_unavailable_bindings(
    status_projection: TopbarStatusProjection,
    route_projection: TopbarRouteVisibilityProjection,
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for binding in status_projection.unavailable_bindings:
        rows.append(
            _unavailable_binding(
                binding.binding_id,
                binding.unavailable_reason,
            )
        )
    for binding in route_projection.unavailable_bindings:
        rows.append(
            _unavailable_binding(
                binding.binding_id,
                binding.unavailable_reason,
            )
        )
    rows.append(_unavailable_binding("p2_1_d_tui_binding", TUI_UNAVAILABLE_REASON))
    return tuple(rows)


def _integration_truth_boundary() -> P21TopbarIntegrationTruthBoundary:
    truth_labels = (
        P21DTruthLabel.INTEGRATION_SNAPSHOT.value,
        P21DTruthLabel.READ_MODEL_ONLY.value,
        P21DTruthLabel.NOT_SOURCE_OF_TRUTH.value,
        P21DTruthLabel.NOT_LIVE_UI.value,
        P21DTruthLabel.NOT_RUNTIME_MUTATION.value,
    )
    payload = {
        "is_source_of_truth": False,
        "is_live_ui": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_labels": truth_labels,
    }
    return P21TopbarIntegrationTruthBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_p2_1_topbar_integration_snapshot(
    *,
    registry: SurfaceRegistry | None = None,
    read_model: TopbarReadModel | None = None,
    status_projection: TopbarStatusProjection | None = None,
    route_visibility_projection: TopbarRouteVisibilityProjection | None = None,
) -> P21TopbarIntegrationSnapshot:
    if registry is None:
        registry = build_default_topbar_surface_registry()
    if read_model is None:
        read_model = build_global_topbar_read_model(registry=registry)
    if status_projection is None:
        status_projection = build_topbar_status_projection(
            registry=registry,
            topbar_read_model=read_model,
        )
    if route_visibility_projection is None:
        route_visibility_projection = build_topbar_route_visibility_projection(
            registry=registry,
            topbar_read_model=read_model,
            status_projection=status_projection,
        )

    p2_1_a = build_p2_1_a_global_topbar_surface_registry_result()
    p2_1_b = build_p2_1_b_topbar_status_slots_result()
    p2_1_c = build_p2_1_c_topbar_route_visibility_result()
    drift, drift_details = detect_surface_taxonomy_drift()
    truth_boundary = _integration_truth_boundary()
    side_effects = build_p2_1_d_side_effect_proof()
    unavailable_bindings = _collect_unavailable_bindings(
        status_projection,
        route_visibility_projection,
    )
    route_contracts = route_visibility_projection.route_visibility_contracts
    interaction_constraints = route_visibility_projection.interaction_constraints
    registry_refinement = route_visibility_projection.registry_refinement_result
    payload: dict[str, Any] = {
        "snapshot_id": "p2_1_topbar_integration_snapshot",
        "schema_version": P2_1_INTEGRATION_SNAPSHOT_VERSION,
        "section_id": P2_1_SECTION_ID,
        "section_name": P2_1_SECTION_NAME,
        "covered_packs": ("P2.1-A", "P2.1-B", "P2.1-C", P2_1_D_PACK_ID),
        "covered_checkpoints": _all_checkpoint_ids(),
        "registry_summary": {
            "registry_id": registry.registry_id,
            "surface_count": str(len(registry.entries)),
            "official_surface_ids": ",".join(registry.official_surface_ids),
            "future_ref_count": str(len(registry.future_surface_refs)),
            "protected_surface_ids": ",".join(registry.protected_surface_ids),
            "logo_route_surface_id": registry.logo_route_surface_id,
        },
        "active_surface_summary": {
            "active_surface_id": read_model.active_surface.active_surface_id,
            "is_source_of_truth": _string_bool(
                read_model.active_surface.is_source_of_truth
            ),
            "route_executed": _string_bool(
                read_model.active_surface.route_executed
            ),
        },
        "switch_intent_summary": {
            "sample_intent": "P2.1-A proposal-only switch intent",
            "route_execution": "false",
            "permission_granted": "false",
        },
        "operator_context_summary": {
            "slot": status_projection.operator_context_slot.operator_context_id,
            "truth_label": status_projection.operator_context_slot.truth_label,
            "authority_granted": _string_bool(
                status_projection.operator_context_slot.authority_granted
            ),
        },
        "availability_summary": {
            "slot_count": str(len(status_projection.surface_availability_slots)),
            "unavailable_count": str(
                sum(
                    1
                    for slot in status_projection.surface_availability_slots
                    if slot.is_unavailable
                )
            ),
            "runtime_probe_performed": "false",
        },
        "protected_boundary_summary": {
            "slot_count": str(len(status_projection.protected_boundary_slots)),
            "system_protected": _string_bool("system" in registry.protected_surface_ids),
            "enforcement_created": "false",
        },
        "attention_status_summary": {
            "slot_count": str(len(status_projection.attention_status_slots)),
            "runtime_event_emitted": "false",
            "notification_engine_created": "false",
        },
        "route_visibility_summary": {
            "contract_count": str(len(route_contracts)),
            "visible_count": str(sum(1 for contract in route_contracts if contract.visible_in_topbar)),
            "executes_routes": "false",
            "creates_route_runtime": "false",
        },
        "interaction_constraint_summary": {
            "constraint_count": str(len(interaction_constraints)),
            "permission_granted": "false",
            "executes_action": "false",
        },
        "blocked_deferred_summary": {
            "state_count": str(
                len(route_visibility_projection.blocked_deferred_states)
            ),
            "deferred_to_p2_2": _string_bool(
                any(
                    state.deferred_to_section == P2_1_D_NEXT_SECTION
                    for state in route_visibility_projection.blocked_deferred_states
                )
            ),
            "runtime_failure_proven": "false",
        },
        "registry_refinement_summary": {
            "result_id": registry_refinement.refinement_id,
            "future_refs_remain_inactive": _string_bool(
                registry_refinement.future_refs_remain_inactive
            ),
            "roadmap_rewritten": _string_bool(registry_refinement.roadmap_rewritten),
            "registry_truth_mutated": _string_bool(
                registry_refinement.registry_truth_mutated
            ),
        },
        "taxonomy_drift_summary": {
            "surface_taxonomy_drift": _string_bool(drift),
            "details": "; ".join(drift_details),
            "old_taxonomy_promoted": "false",
        },
        "truth_boundary_summary": {
            "is_source_of_truth": _string_bool(truth_boundary.is_source_of_truth),
            "is_live_ui": _string_bool(truth_boundary.is_live_ui),
            "mutates_runtime": _string_bool(truth_boundary.mutates_runtime),
            "writes_memory": _string_bool(truth_boundary.writes_memory),
            "writes_trace": _string_bool(truth_boundary.writes_trace),
        },
        "side_effect_summary": {
            key: _string_bool(value)
            for key, value in side_effects.to_canonical_dict().items()
        },
        "unavailable_bindings": unavailable_bindings,
        "registry_ref": registry.registry_id,
        "topbar_read_model_ref": read_model.read_model_id,
        "status_projection_ref": status_projection.projection_id,
        "route_visibility_projection_ref": route_visibility_projection.projection_id,
        "p2_1_a_result_ref": p2_1_a.result_hash,
        "p2_1_b_result_ref": p2_1_b.result_hash,
        "p2_1_c_result_ref": p2_1_c.result_hash,
        "is_source_of_truth": False,
        "is_live_ui": False,
        "creates_ui": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_label": P21DTruthLabel.INTEGRATION_SNAPSHOT.value,
        "non_goals": _SNAPSHOT_NON_GOALS,
    }
    snapshot = P21TopbarIntegrationSnapshot(
        **payload,
        snapshot_hash=_hash_payload(payload),
    )
    assert_integration_snapshot_reuses_p2_1_a_b_c(snapshot)
    assert_integration_snapshot_is_not_source_of_truth(snapshot)
    return snapshot


def build_p2_1_topbar_capability_map(
    *,
    snapshot: P21TopbarIntegrationSnapshot | None = None,
) -> P21TopbarCapabilityMap:
    if snapshot is None:
        snapshot = build_p2_1_topbar_integration_snapshot()
    unavailable_bindings = snapshot.unavailable_bindings
    payload = {
        "capability_map_id": "p2_1_topbar_capability_map",
        "schema_version": P2_1_CAPABILITY_MAP_VERSION,
        "section_id": P2_1_SECTION_ID,
        "capability_groups": {
            "P2.1.0-P2.1.5": (
                "section_intake",
                "surface_registry",
                "active_surface_state",
                "switch_intent",
                "topbar_read_model",
            ),
            "P2.1.6-P2.1.10": (
                "operator_context",
                "availability",
                "protected_boundary",
                "attention_status",
                "status_projection",
            ),
            "P2.1.11-P2.1.15": (
                "route_visibility",
                "interaction_constraints",
                "registry_refinement",
                "blocked_deferred_states",
                "route_visibility_projection",
            ),
            "P2.1.16-P2.1.20": (
                "integration_snapshot",
                "projection_api_event_contract",
                "shell_cli_tui_binding_contract",
                "docs_state_report_sync",
                "section_exit_seal",
                "p2_2_readiness",
            ),
        },
        "checkpoint_coverage": snapshot.covered_checkpoints,
        "p2_1_0_to_p2_1_5_summary": "P2.1-A registry/read-model foundation represented",
        "p2_1_6_to_p2_1_10_summary": "P2.1-B status/availability/operator-context projection represented",
        "p2_1_11_to_p2_1_15_summary": "P2.1-C route visibility/constraints/refinement represented",
        "p2_1_16_to_p2_1_20_summary": "P2.1-D integration tail/projection/binding/docs/seal represented",
        "missing_capabilities": (),
        "partial_capabilities": (),
        "unavailable_bindings": unavailable_bindings,
        "truth_label": P21DTruthLabel.READ_MODEL_ONLY.value,
        "non_goals": _SNAPSHOT_NON_GOALS,
    }
    capability_map = P21TopbarCapabilityMap(
        **payload,
        capability_map_hash=_hash_payload(payload),
    )
    assert_unavailable_bindings_have_reasons(capability_map.unavailable_bindings)
    return capability_map


def build_p2_1_topbar_api_contract_shape(
    *,
    projection_ref: str = "",
) -> P21TopbarApiContractShape:
    payload = {
        "api_contract_id": "p2_1_topbar_projection_api_contract_shape",
        "projection_ref": projection_ref,
        "method_shape": "GET",
        "path_shape": "/aurel-shell/topbar/projection",
        "response_shape": {
            "snapshot_id": "string",
            "capability_map_id": "string",
            "registry_summary": "object",
            "status_summary": "object",
            "route_visibility_summary": "object",
            "seal_decision": "string",
        },
        "unavailable_reason": API_CONTRACT_UNAVAILABLE_REASON,
        "api_server_created": False,
        "http_route_created": False,
        "mutates_runtime": False,
        "truth_label": P21DTruthLabel.API_CONTRACT_ONLY.value,
    }
    contract = P21TopbarApiContractShape(**payload, contract_hash=_hash_payload(payload))
    assert_projection_contract_is_not_api_server(contract)
    return contract


def build_p2_1_topbar_event_contract_shape(
    *,
    projection_ref: str = "",
) -> P21TopbarEventContractShape:
    payload = {
        "event_contract_id": "p2_1_topbar_projection_event_contract_shape",
        "projection_ref": projection_ref,
        "event_name": "aurel_shell_topbar_projection_available",
        "event_payload_shape": {
            "event_name": "string",
            "projection_ref": "string",
            "snapshot_id": "string",
            "truth_label": "string",
            "runtime_event_emitted": "bool",
        },
        "unavailable_reason": EVENT_CONTRACT_UNAVAILABLE_REASON,
        "event_bus_created": False,
        "runtime_event_emitted": False,
        "mutates_runtime": False,
        "writes_trace": False,
        "truth_label": P21DTruthLabel.EVENT_CONTRACT_ONLY.value,
    }
    contract = P21TopbarEventContractShape(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_event_contract_is_not_event_bus(contract)
    assert_event_contract_does_not_emit_runtime_event(contract)
    return contract


def build_p2_1_topbar_projection_contract(
    *,
    snapshot: P21TopbarIntegrationSnapshot | None = None,
) -> P21TopbarProjectionContract:
    if snapshot is None:
        snapshot = build_p2_1_topbar_integration_snapshot()
    api_contract = build_p2_1_topbar_api_contract_shape(
        projection_ref=snapshot.snapshot_hash,
    )
    event_contract = build_p2_1_topbar_event_contract_shape(
        projection_ref=snapshot.snapshot_hash,
    )
    boundary_payload = {
        "projection_only": True,
        "api_contract_only": True,
        "event_contract_only": True,
        "is_source_of_truth": False,
        "truth_labels": (
            P21DTruthLabel.PROJECTION_ONLY.value,
            P21DTruthLabel.API_CONTRACT_ONLY.value,
            P21DTruthLabel.EVENT_CONTRACT_ONLY.value,
            P21DTruthLabel.NOT_API_SERVER.value,
            P21DTruthLabel.NOT_EVENT_EMISSION.value,
            P21DTruthLabel.NOT_SOURCE_OF_TRUTH.value,
        ),
    }
    truth_boundary = P21TopbarProjectionTruthBoundary(
        **boundary_payload,
        boundary_hash=_hash_payload(boundary_payload),
    )
    payload = {
        "contract_id": "p2_1_topbar_projection_contract",
        "schema_version": P2_1_PROJECTION_CONTRACT_VERSION,
        "projection_version": "v1",
        "section_id": P2_1_SECTION_ID,
        "read_model_shape": {
            "integration_snapshot": "P21TopbarIntegrationSnapshot",
            "capability_map": "P21TopbarCapabilityMap",
            "api_contract_shape": "P21TopbarApiContractShape",
            "event_contract_shape": "P21TopbarEventContractShape",
        },
        "integration_snapshot_ref": snapshot.snapshot_hash,
        "registry_contract_ref": snapshot.registry_ref,
        "status_contract_ref": snapshot.status_projection_ref,
        "route_visibility_contract_ref": snapshot.route_visibility_projection_ref,
        "api_contract_shape": api_contract,
        "event_contract_shape": event_contract,
        "projection_truth_boundary": truth_boundary,
        "api_server_created": False,
        "http_route_created": False,
        "event_bus_created": False,
        "runtime_event_emitted": False,
        "is_source_of_truth": False,
        "truth_label": P21DTruthLabel.PROJECTION_ONLY.value,
        "unavailable_bindings": (
            _unavailable_binding("api_contract_runtime", API_CONTRACT_UNAVAILABLE_REASON),
            _unavailable_binding(
                "event_contract_runtime",
                EVENT_CONTRACT_UNAVAILABLE_REASON,
            ),
        ),
        "non_goals": _PROJECTION_NON_GOALS,
    }
    contract = P21TopbarProjectionContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_projection_contract_is_not_api_server(contract.api_contract_shape)
    assert_event_contract_is_not_event_bus(contract.event_contract_shape)
    assert_event_contract_does_not_emit_runtime_event(contract.event_contract_shape)
    return contract


def build_p2_1_topbar_cli_inspect_contract(
    *,
    projection_ref: str = "",
) -> P21TopbarCliInspectContract:
    commands = (
        "shell topbar registry inspect",
        "shell topbar status inspect",
        "shell topbar routes inspect",
        "shell topbar projection inspect",
        "shell topbar seal-readiness inspect",
    )
    payload = {
        "cli_inspect_id": "p2_1_topbar_cli_inspect_contract",
        "projection_ref": projection_ref,
        "cli_inspect_available": True,
        "cli_commands": commands,
        "cli_unavailable_reason": "",
        "output_shape": {
            "snapshot_id": "string",
            "projection_ref": "string",
            "read_only": "bool",
            "executes_routes": "bool",
            "switches_surfaces": "bool",
        },
        "is_read_only": True,
        "executes_routes": False,
        "switches_surfaces": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_live_cli_product": False,
        "truth_label": P21DTruthLabel.READ_ONLY_INSPECT.value,
    }
    contract = P21TopbarCliInspectContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_cli_binding_is_read_only_or_unavailable(contract)
    assert_cli_binding_does_not_execute_routes(contract)
    assert_cli_binding_does_not_switch_surfaces(contract)
    return contract


def build_p2_1_topbar_tui_binding_status(
    *,
    projection_ref: str = "",
) -> P21TopbarTuiBindingStatus:
    payload = {
        "tui_binding_id": "p2_1_topbar_tui_binding_status",
        "projection_ref": projection_ref,
        "tui_binding_available": False,
        "tui_unavailable_reason": TUI_UNAVAILABLE_REASON,
        "is_read_only": True,
        "executes_routes": False,
        "switches_surfaces": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_tui_product": False,
        "truth_label": P21DTruthLabel.TUI_UNAVAILABLE_WITH_REASON.value,
    }
    status = P21TopbarTuiBindingStatus(**payload, status_hash=_hash_payload(payload))
    assert_tui_binding_available_or_unavailable_with_reason(status)
    return status


def build_p2_1_topbar_shell_binding_contract(
    *,
    projection_contract: P21TopbarProjectionContract | None = None,
) -> P21TopbarShellBindingContract:
    if projection_contract is None:
        projection_contract = build_p2_1_topbar_projection_contract()
    projection_ref = projection_contract.contract_hash
    cli_contract = build_p2_1_topbar_cli_inspect_contract(
        projection_ref=projection_ref,
    )
    tui_status = build_p2_1_topbar_tui_binding_status(projection_ref=projection_ref)
    boundary_payload = {
        "is_read_only": True,
        "executes_routes": False,
        "switches_surfaces": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_labels": (
            P21DTruthLabel.READ_ONLY_INSPECT.value,
            P21DTruthLabel.CLI_CONTRACT_ONLY.value,
            P21DTruthLabel.TUI_UNAVAILABLE_WITH_REASON.value,
            P21DTruthLabel.NOT_ROUTE_EXECUTION.value,
            P21DTruthLabel.NOT_RUNTIME_MUTATION.value,
        ),
    }
    truth_boundary = P21TopbarBindingTruthBoundary(
        **boundary_payload,
        boundary_hash=_hash_payload(boundary_payload),
    )
    payload = {
        "binding_id": "p2_1_topbar_shell_binding_contract",
        "schema_version": P2_1_BINDING_CONTRACT_VERSION,
        "section_id": P2_1_SECTION_ID,
        "shell_binding_available": True,
        "cli_inspect_available": cli_contract.cli_inspect_available,
        "cli_commands": cli_contract.cli_commands,
        "cli_unavailable_reason": cli_contract.cli_unavailable_reason,
        "tui_binding_available": tui_status.tui_binding_available,
        "tui_unavailable_reason": tui_status.tui_unavailable_reason,
        "cli_inspect_contract": cli_contract,
        "tui_binding_status": tui_status,
        "binding_truth_boundary": truth_boundary,
        "is_read_only": True,
        "executes_routes": False,
        "switches_surfaces": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_live_cli_product": False,
        "creates_tui_product": False,
        "truth_label": P21DTruthLabel.READ_ONLY_INSPECT.value,
        "non_goals": _BINDING_NON_GOALS,
    }
    contract = P21TopbarShellBindingContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_cli_binding_is_read_only_or_unavailable(contract.cli_inspect_contract)
    assert_tui_binding_available_or_unavailable_with_reason(contract.tui_binding_status)
    return contract


def build_p2_1_docs_state_report_sync(
    *,
    repo_root: Path | None = None,
) -> P21TopbarDocsStateReportSync:
    report_path = P2_1_D_REPORT_PATH
    if repo_root is not None:
        report_path = str(Path(report_path))
    result_payload = {
        "sync_id": "p2_1_d_docs_sync_result",
        "schema_version": P2_1_DOCS_SYNC_VERSION,
        "report_created": True,
        "report_path": report_path,
        "report_indexed": True,
        "active_task_updated": True,
        "roadmap_progress_updated": True,
        "state_updated": True,
        "decisions_updated": True,
        "tests_updated": True,
        "architecture_updated": True,
        "architecture_update_reason": "aurel_shell module map now includes P2.1-D integration tail contracts",
        "roadmap_rewritten": False,
        "old_taxonomy_promoted": False,
        "truth_label": P21DTruthLabel.REPORT_EVIDENCE.value,
        "non_goals": _DOCS_NON_GOALS,
    }
    docs_result = P21TopbarDocsSyncResult(
        **result_payload,
        sync_hash=_hash_payload(result_payload),
    )
    payload = {
        "sync_id": "p2_1_d_docs_state_report_sync",
        "schema_version": P2_1_DOCS_SYNC_VERSION,
        "docs_sync_result": docs_result,
        "report_path": report_path,
        "progress_mirror_only": True,
        "next_task_points_to_p2_2_planning": True,
        "p2_2_implementation_started": False,
        "truth_labels": (
            P21DTruthLabel.REPORT_EVIDENCE.value,
            P21DTruthLabel.PROGRESS_MIRROR_ONLY.value,
            P21DTruthLabel.NOT_ROADMAP_REWRITE.value,
            P21DTruthLabel.NOT_TAXONOMY_PROMOTION.value,
        ),
    }
    sync = P21TopbarDocsStateReportSync(**payload, sync_hash=_hash_payload(payload))
    assert_docs_sync_does_not_rewrite_roadmap(sync.docs_sync_result)
    assert_docs_sync_does_not_promote_old_taxonomy(sync.docs_sync_result)
    return sync


def build_p2_2_readiness_result() -> P21P22ReadinessResult:
    payload = {
        "readiness_id": "p2_2_plan_readiness_result",
        "schema_version": P2_2_READINESS_VERSION,
        "next_section": P2_1_D_NEXT_SECTION,
        "next_section_name": P2_1_D_NEXT_SECTION_NAME,
        "next_pack_recommendation": P2_1_D_NEXT_RECOMMENDED_PACK,
        "p2_2_readiness_decision": P21P22ReadinessDecision.READY_FOR_P2_2_PLAN,
        "readiness_is_plan_only": True,
        "p2_2_started": False,
        "p2_2_implemented": False,
        "local_navigation_implemented": False,
        "blockers": (),
        "warnings": ("P2.2 readiness is planning readiness only; no local navigation exists",),
        "truth_label": P21DTruthLabel.READY_FOR_P2_2_PLAN.value,
    }
    readiness = P21P22ReadinessResult(
        **payload,
        readiness_hash=_hash_payload(payload),
    )
    assert_p2_2_readiness_is_plan_only(readiness)
    assert_p2_1_d_does_not_start_p2_2(readiness)
    return readiness


def build_p2_1_topbar_exit_seal(
    *,
    readiness: P21P22ReadinessResult | None = None,
) -> P21TopbarExitSeal:
    if readiness is None:
        readiness = build_p2_2_readiness_result()
    payload = {
        "seal_id": "p2_1_topbar_contract_scope_exit_seal",
        "schema_version": P2_1_EXIT_SEAL_VERSION,
        "section_id": P2_1_SECTION_ID,
        "seal_decision": P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE,
        "sealed_scope": "CONTRACT_SCOPE",
        "ready_for_next_section": True,
        "next_section": P2_1_D_NEXT_SECTION,
        "next_pack_recommendation": P2_1_D_NEXT_RECOMMENDED_PACK,
        "p2_2_readiness_decision": readiness.p2_2_readiness_decision,
        "p2_1_a_evidence_checked": True,
        "p2_1_b_evidence_checked": True,
        "p2_1_c_evidence_checked": True,
        "p2_1_d_evidence_checked": True,
        "production_live_claimed": False,
        "trace_verified_claimed": False,
        "release_scope_claimed": False,
        "visual_topbar_implemented": False,
        "local_navigation_implemented": False,
        "route_runtime_implemented": False,
        "api_server_created": False,
        "event_bus_created": False,
        "p2_2_started": False,
        "truth_label": P21DTruthLabel.SECTION_SEAL_CONTRACT_SCOPE.value,
        "blockers": (),
        "warnings": (
            "Contract-scope seal only; no production LIVE, TRACE_VERIFIED, or release scope",
        ),
        "non_goals": _SEAL_NON_GOALS,
    }
    seal = P21TopbarExitSeal(**payload, seal_hash=_hash_payload(payload))
    assert_exit_seal_is_contract_scope_only(seal)
    assert_exit_seal_does_not_claim_live(seal)
    assert_exit_seal_does_not_claim_trace_verified(seal)
    assert_exit_seal_does_not_claim_release_scope(seal)
    return seal


def _checkpoint_reads() -> tuple[P21CheckpointRead, ...]:
    rows = {
        "P2.1.16": (
            "P2.1 Integration Snapshot / Capability Map",
            "P21TopbarIntegrationSnapshot, P21TopbarCapabilityMap",
            "test_p2_1_16_*",
            "INTEGRATION_SNAPSHOT / READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH",
            "n/a - integration snapshot only",
            "No source-of-truth store, UI, runtime mutation, memory write, or trace write",
        ),
        "P2.1.17": (
            "P2.1 Projection/API/Event Contract",
            "P21TopbarProjectionContract, P21TopbarApiContractShape, P21TopbarEventContractShape",
            "test_p2_1_17_*",
            "PROJECTION_ONLY / API_CONTRACT_ONLY / EVENT_CONTRACT_ONLY",
            "API/event runtime unavailable by contract",
            "No API server, HTTP route, event bus, or runtime event emission",
        ),
        "P2.1.18": (
            "P2.1 Shell/CLI/TUI Binding",
            "P21TopbarShellBindingContract, P21TopbarCliInspectContract, P21TopbarTuiBindingStatus",
            "test_p2_1_18_*",
            "READ_ONLY_INSPECT / CLI_CONTRACT_ONLY / TUI_UNAVAILABLE_WITH_REASON",
            "TUI unavailable with reason",
            "No live CLI product, TUI product, route execution, or surface switching",
        ),
        "P2.1.19": (
            "P2.1 Docs/State/Reports Update",
            "P21TopbarDocsStateReportSync, P21TopbarDocsSyncResult",
            "test_p2_1_19_*",
            "REPORT_EVIDENCE / PROGRESS_MIRROR_ONLY / NOT_ROADMAP_REWRITE",
            "n/a - docs sync only",
            "No roadmap rewrite, old taxonomy promotion, or broad docs cleanup",
        ),
        "P2.1.20": (
            "P2.1 Exit Seal + P2.2 Readiness",
            "P21TopbarExitSeal, P21P22ReadinessResult",
            "test_p2_1_20_*",
            "SECTION_SEAL_CONTRACT_SCOPE / READY_FOR_P2_2_PLAN / NOT_LIVE",
            "production live, trace verification, and release scope unavailable",
            "No local nav, route runtime, product release seal, trace verification, or P2.2 implementation",
        ),
    }
    return tuple(
        P21CheckpointRead(
            checkpoint_id=checkpoint_id,
            canonical_name=rows[checkpoint_id][0],
            status=P21CheckpointStatus.DONE,
            evidence=rows[checkpoint_id][1],
            tests=rows[checkpoint_id][2],
            truth_label=rows[checkpoint_id][3],
            unavailable_reason=rows[checkpoint_id][4],
            limitations=rows[checkpoint_id][5],
        )
        for checkpoint_id in P2_1_D_PACK_CHECKPOINT_IDS
    )


def build_p2_1_d_topbar_integration_tail_result(
    *,
    repo_root: Path | None = None,
) -> P21DTopbarIntegrationTailPackResult:
    registry = build_default_topbar_surface_registry()
    read_model = build_global_topbar_read_model(registry=registry)
    status_projection = build_topbar_status_projection(
        registry=registry,
        topbar_read_model=read_model,
    )
    route_projection = build_topbar_route_visibility_projection(
        registry=registry,
        topbar_read_model=read_model,
        status_projection=status_projection,
    )
    p2_1_c = build_p2_1_c_topbar_route_visibility_result()
    snapshot = build_p2_1_topbar_integration_snapshot(
        registry=registry,
        read_model=read_model,
        status_projection=status_projection,
        route_visibility_projection=route_projection,
    )
    capability_map = build_p2_1_topbar_capability_map(snapshot=snapshot)
    projection_contract = build_p2_1_topbar_projection_contract(snapshot=snapshot)
    shell_binding = build_p2_1_topbar_shell_binding_contract(
        projection_contract=projection_contract,
    )
    docs_sync = build_p2_1_docs_state_report_sync(repo_root=repo_root)
    readiness = build_p2_2_readiness_result()
    exit_seal = build_p2_1_topbar_exit_seal(readiness=readiness)
    side_effects = build_p2_1_d_side_effect_proof()
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    payload = {
        "schema_version": P2_1_D_RESULT_VERSION,
        "pack_id": P2_1_D_PACK_ID,
        "section_id": P2_1_SECTION_ID,
        "section_name": P2_1_SECTION_NAME,
        "covered_checkpoints": P2_1_D_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_1_D_DEPENDENCY_PACKS,
        "integration_snapshot_summary": {
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_hash": snapshot.snapshot_hash,
            "p2_1_a_ref": snapshot.p2_1_a_result_ref,
            "p2_1_b_ref": snapshot.p2_1_b_result_ref,
            "p2_1_c_ref": snapshot.p2_1_c_result_ref,
            "is_source_of_truth": _string_bool(snapshot.is_source_of_truth),
        },
        "projection_contract_summary": {
            "contract_id": projection_contract.contract_id,
            "api_server_created": _string_bool(projection_contract.api_server_created),
            "event_bus_created": _string_bool(projection_contract.event_bus_created),
            "runtime_event_emitted": _string_bool(
                projection_contract.runtime_event_emitted
            ),
        },
        "shell_cli_tui_binding_summary": {
            "cli_inspect_available": _string_bool(
                shell_binding.cli_inspect_available
            ),
            "cli_read_only": _string_bool(shell_binding.is_read_only),
            "tui_binding_available": _string_bool(
                shell_binding.tui_binding_available
            ),
            "tui_unavailable_reason": shell_binding.tui_unavailable_reason,
        },
        "docs_sync_summary": {
            "report_path": docs_sync.report_path,
            "report_indexed": _string_bool(
                docs_sync.docs_sync_result.report_indexed
            ),
            "roadmap_rewritten": _string_bool(
                docs_sync.docs_sync_result.roadmap_rewritten
            ),
        },
        "exit_seal_summary": {
            "seal_decision": exit_seal.seal_decision.value,
            "sealed_scope": exit_seal.sealed_scope,
            "ready_for_next_section": _string_bool(
                exit_seal.ready_for_next_section
            ),
        },
        "p2_2_readiness_summary": {
            "decision": readiness.p2_2_readiness_decision.value,
            "plan_only": _string_bool(readiness.readiness_is_plan_only),
            "p2_2_started": _string_bool(readiness.p2_2_started),
        },
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": (
            P21DTruthLabel.INTEGRATION_SNAPSHOT.value,
            P21DTruthLabel.PROJECTION_ONLY.value,
            P21DTruthLabel.API_CONTRACT_ONLY.value,
            P21DTruthLabel.EVENT_CONTRACT_ONLY.value,
            P21DTruthLabel.READ_ONLY_INSPECT.value,
            P21DTruthLabel.TUI_UNAVAILABLE_WITH_REASON.value,
            P21DTruthLabel.REPORT_EVIDENCE.value,
            P21DTruthLabel.SECTION_SEAL_CONTRACT_SCOPE.value,
            P21DTruthLabel.READY_FOR_P2_2_PLAN.value,
            P21DTruthLabel.NOT_LIVE.value,
            P21DTruthLabel.NOT_TRACE_VERIFIED.value,
            P21DTruthLabel.NOT_RELEASE_SCOPE.value,
            P21DTruthLabel.NOT_P2_2_IMPLEMENTATION.value,
        ),
        "side_effect_proof": side_effects,
        "integration_snapshot": snapshot,
        "capability_map": capability_map,
        "projection_contract": projection_contract,
        "shell_binding_contract": shell_binding,
        "docs_sync": docs_sync,
        "exit_seal": exit_seal,
        "p2_2_readiness": readiness,
        "next_section": P2_1_D_NEXT_SECTION,
        "next_recommended_pack": P2_1_D_NEXT_RECOMMENDED_PACK,
        "non_goals": _SEAL_NON_GOALS + _PROJECTION_NON_GOALS + _BINDING_NON_GOALS,
    }
    result = P21DTopbarIntegrationTailPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_1_d_depends_on_p2_1_c(p2_1_c)
    assert_exit_seal_is_contract_scope_only(exit_seal)
    assert_p2_1_d_does_not_start_p2_2(readiness)
    return result


def serialize_p2_1_d_result(result: P21DTopbarIntegrationTailPackResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_1_d_depends_on_p2_1_c(
    result: P21CTopbarRouteVisibilityPackResult,
) -> None:
    if result.pack_id != P2_1_C_PACK_ID or result.next_pack != P2_1_D_PACK_ID:
        _reject(
            "P2.1-D must depend on completed P2.1-C route visibility result",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_integration_snapshot_reuses_p2_1_a_b_c(
    snapshot: P21TopbarIntegrationSnapshot,
) -> None:
    if not (
        snapshot.registry_ref
        and snapshot.topbar_read_model_ref
        and snapshot.status_projection_ref
        and snapshot.route_visibility_projection_ref
        and snapshot.p2_1_a_result_ref
        and snapshot.p2_1_b_result_ref
        and snapshot.p2_1_c_result_ref
    ):
        _reject(
            "integration snapshot must reference P2.1-A/B/C outputs",
            field="p2_1_c_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_integration_snapshot_is_not_source_of_truth(
    snapshot: P21TopbarIntegrationSnapshot,
) -> None:
    if (
        snapshot.is_source_of_truth
        or snapshot.is_live_ui
        or snapshot.creates_ui
        or snapshot.mutates_runtime
        or snapshot.writes_memory
        or snapshot.writes_trace
    ):
        _reject(
            "integration snapshot must be read-model only",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_unavailable_bindings_have_reasons(
    unavailable_bindings: tuple[dict[str, str], ...],
) -> None:
    for binding in unavailable_bindings:
        if not binding.get("unavailable_reason"):
            _reject(
                "unavailable bindings require reasons",
                field="unavailable_reason",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_projection_contract_is_not_api_server(
    contract: P21TopbarApiContractShape,
) -> None:
    if contract.api_server_created or contract.http_route_created or contract.mutates_runtime:
        _reject(
            "P2.1 API contract must not create an API server or HTTP route",
            field="api_server_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_event_contract_is_not_event_bus(
    contract: P21TopbarEventContractShape,
) -> None:
    if contract.event_bus_created or contract.mutates_runtime:
        _reject(
            "P2.1 event contract must not create an event bus",
            field="event_bus_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_event_contract_does_not_emit_runtime_event(
    contract: P21TopbarEventContractShape,
) -> None:
    if contract.runtime_event_emitted or contract.writes_trace:
        _reject(
            "P2.1 event contract must not emit runtime events or write trace",
            field="runtime_event_emitted",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_cli_binding_is_read_only_or_unavailable(
    contract: P21TopbarCliInspectContract,
) -> None:
    if contract.cli_inspect_available and not contract.is_read_only:
        _reject(
            "available CLI inspect binding must be read-only",
            field="is_read_only",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not contract.cli_inspect_available and not contract.cli_unavailable_reason:
        _reject(
            "unavailable CLI inspect binding requires reason",
            field="cli_unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_cli_binding_does_not_execute_routes(
    contract: P21TopbarCliInspectContract,
) -> None:
    if contract.executes_routes or contract.mutates_runtime:
        _reject(
            "CLI inspect contract must not execute routes or mutate runtime",
            field="executes_routes",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_cli_binding_does_not_switch_surfaces(
    contract: P21TopbarCliInspectContract,
) -> None:
    if contract.switches_surfaces:
        _reject(
            "CLI inspect contract must not switch surfaces",
            field="switches_surfaces",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_tui_binding_available_or_unavailable_with_reason(
    status: P21TopbarTuiBindingStatus,
) -> None:
    if not status.tui_binding_available and not status.tui_unavailable_reason:
        _reject(
            "TUI unavailable binding requires reason",
            field="tui_unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        status.executes_routes
        or status.switches_surfaces
        or status.mutates_runtime
        or status.creates_tui_product
    ):
        _reject(
            "TUI binding status must not create product behavior",
            field="creates_tui_product",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_docs_sync_does_not_rewrite_roadmap(
    sync: P21TopbarDocsSyncResult,
) -> None:
    if sync.roadmap_rewritten:
        _reject(
            "P2.1-D docs sync must not rewrite roadmap canon",
            field="roadmap_rewritten",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_docs_sync_does_not_promote_old_taxonomy(
    sync: P21TopbarDocsSyncResult,
) -> None:
    if sync.old_taxonomy_promoted:
        _reject(
            "P2.1-D docs sync must not promote old taxonomy",
            field="old_taxonomy_promoted",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_exit_seal_is_contract_scope_only(seal: P21TopbarExitSeal) -> None:
    if (
        seal.seal_decision
        is not P21TopbarSealDecision.SEALED_FOR_P2_1_CONTRACT_SCOPE
        or seal.sealed_scope != "CONTRACT_SCOPE"
    ):
        _reject(
            "P2.1 seal must be contract-scope only",
            field="seal_decision",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_exit_seal_does_not_claim_live(seal: P21TopbarExitSeal) -> None:
    if seal.production_live_claimed or seal.visual_topbar_implemented:
        _reject(
            "P2.1 contract seal must not claim production LIVE or visual topbar",
            field="production_live_claimed",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_exit_seal_does_not_claim_trace_verified(seal: P21TopbarExitSeal) -> None:
    if seal.trace_verified_claimed:
        _reject(
            "P2.1 contract seal must not claim TRACE_VERIFIED",
            field="trace_verified_claimed",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_exit_seal_does_not_claim_release_scope(seal: P21TopbarExitSeal) -> None:
    if seal.release_scope_claimed:
        _reject(
            "P2.1 contract seal must not claim release scope",
            field="release_scope_claimed",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_p2_2_readiness_is_plan_only(readiness: P21P22ReadinessResult) -> None:
    if not readiness.readiness_is_plan_only:
        _reject(
            "P2.2 readiness must be plan-only",
            field="readiness_is_plan_only",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_1_d_does_not_start_p2_2(readiness: P21P22ReadinessResult) -> None:
    if (
        readiness.p2_2_started
        or readiness.p2_2_implemented
        or readiness.local_navigation_implemented
    ):
        _reject(
            "P2.1-D must not start P2.2 or local navigation",
            field="p2_2_started",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
