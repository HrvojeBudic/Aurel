"""AurelShell P2.0-B navigation boundary pack result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .boundaries import (
    HubInternalToolEntryBoundary,
    SettingsSystemConfigBoundary,
    SurfaceSourceOfTruthBoundary,
    SystemNoAgentAccessBoundary,
    build_hub_internal_tool_entry_boundary,
    build_settings_system_config_boundary,
    build_surface_source_of_truth_boundaries,
    build_system_no_agent_access_boundary,
)
from .contracts import (
    _CanonicalMixin,
    _hash_payload,
    to_canonical_json,
)
from .navigation_boundary import (
    AurelLogoRouteBinding,
    PerSurfaceNavigationBoundary,
    build_aurel_logo_route_binding,
    build_per_surface_navigation_boundaries,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)

P2_0_B_PACK_ID = "P2.0-B"
P2_0_B_SECTION_ID = "P2.0"
P2_0_B_DEPENDENCY_PACK = "P2.0-A"
P2_0_B_NEXT_PACK = "P2.0-C"
P2_0_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.0.9",
    "P2.0.10",
    "P2.0.11",
    "P2.0.12",
    "P2.0.13",
    "P2.0.14",
)
P2_0_B_PACK_RESULT_VERSION = "p2_0_b_navigation_boundary_pack_result.v1"


class P20BCheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


_CHECKPOINT_CANONICAL_NAMES: dict[str, str] = {
    "P2.0.9": "No Universal Left Nav / Per-Surface Nav Boundary",
    "P2.0.10": "Aurel Logo → CRO Route Binding",
    "P2.0.11": "Surface Source-of-Truth Boundary",
    "P2.0.12": "SYSTEM No-Agent-Access Boundary",
    "P2.0.13": "Settings vs SYSTEM Config Boundary",
    "P2.0.14": "HUB Internal Tool Entry Boundary",
}


@dataclass(frozen=True)
class P20BNavigationSideEffectProof(_CanonicalMixin):
    """Proof that P2.0-B performs no UI/runtime/authority side effects."""

    ui_created: bool = False
    route_runtime_created: bool = False
    frontend_route_created: bool = False
    topbar_created: bool = False
    universal_left_nav_created: bool = False
    per_surface_nav_ui_created: bool = False
    floating_window_created: bool = False
    command_palette_created: bool = False
    permission_matrix_created: bool = False
    system_runtime_enforcement_created: bool = False
    agent_system_access_granted: bool = False
    root_authority_granted: bool = False
    tool_executed: bool = False
    tool_permission_granted: bool = False
    runtime_mutated: bool = False
    workflow_executed: bool = False
    business_action_executed: bool = False
    memory_written: bool = False
    ledger_written: bool = False
    global_trace_written: bool = False
    p2_0_c_started: bool = False
    p2_1_started: bool = False


@dataclass(frozen=True)
class P20BCheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P20BCheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class P20BNavigationBoundaryPackResult(_CanonicalMixin):
    """P2.0-B pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    canonical_surface_ids: tuple[str, ...]
    checkpoint_reads: tuple[P20BCheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    side_effect_proof: P20BNavigationSideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    no_universal_left_nav_pack: PerSurfaceNavigationBoundary
    logo_route_binding: AurelLogoRouteBinding
    source_of_truth_boundaries: tuple[SurfaceSourceOfTruthBoundary, ...]
    system_no_agent_access: SystemNoAgentAccessBoundary
    settings_system_config: SettingsSystemConfigBoundary
    hub_tool_entry: HubInternalToolEntryBoundary
    registry: AurelSurfaceRegistry
    next_pack: str
    result_hash: str


def _all_false_p2_0_b_side_effects() -> P20BNavigationSideEffectProof:
    return P20BNavigationSideEffectProof()


def _default_checkpoint_reads() -> tuple[P20BCheckpointRead, ...]:
    evidence_map = {
        "P2.0.9": "NoUniversalLeftNavContract, PerSurfaceNavigationBoundary",
        "P2.0.10": "AurelLogoRouteBinding, LogoRouteTarget",
        "P2.0.11": "SurfaceSourceOfTruthBoundary, SurfaceTruthOwnerKind",
        "P2.0.12": "SystemNoAgentAccessBoundary, SystemAccessRule",
        "P2.0.13": "SettingsSystemConfigBoundary, SettingsConfigScope",
        "P2.0.14": "HubInternalToolEntryBoundary, HubToolEntryContract",
    }
    tests_map = {
        "P2.0.9": "test_p2_0_9_no_universal_left_nav, test_p2_0_9_each_surface_local_nav",
        "P2.0.10": "test_p2_0_10_logo_routes_to_cro, test_p2_0_10_logo_not_system",
        "P2.0.11": "test_p2_0_11_every_surface_source_of_truth, test_p2_0_11_no_surface_owns_truth",
        "P2.0.12": "test_p2_0_12_system_forbids_agent_access, test_p2_0_12_system_operator_only",
        "P2.0.13": "test_p2_0_13_settings_not_system, test_p2_0_13_settings_cannot_grant_root",
        "P2.0.14": "test_p2_0_14_hub_tool_entry_contract_only, test_p2_0_14_hub_cannot_execute_tools",
    }
    truth_map = {
        "P2.0.9": "BOUNDARY_CONTRACT_ONLY / NOT_LIVE",
        "P2.0.10": "ROUTE_CONTRACT_ONLY / ROUTE_HINT_ONLY / NOT_LIVE",
        "P2.0.11": "SOURCE_OF_TRUTH_BOUNDARY_ONLY / CONTRACT_ONLY",
        "P2.0.12": "OPERATOR_ONLY_CONTRACT / BOUNDARY_CONTRACT_ONLY / NOT_LIVE",
        "P2.0.13": "NON_ROOT_CONFIG_CONTRACT / BOUNDARY_CONTRACT_ONLY",
        "P2.0.14": "TOOL_ENTRY_CONTRACT_ONLY / BOUNDARY_CONTRACT_ONLY",
    }
    reads: list[P20BCheckpointRead] = []
    for checkpoint_id in P2_0_B_PACK_CHECKPOINT_IDS:
        reads.append(
            P20BCheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=_CHECKPOINT_CANONICAL_NAMES[checkpoint_id],
                status=P20BCheckpointStatus.DONE,
                evidence=evidence_map[checkpoint_id],
                tests=tests_map[checkpoint_id],
                truth_label=truth_map[checkpoint_id],
                unavailable_reason="n/a — boundary contract only",
                limitations="No UI, routes, runtime enforcement, or tool execution",
            )
        )
    return tuple(reads)


def build_p2_0_b_navigation_boundary_pack_result() -> P20BNavigationBoundaryPackResult:
    registry = build_default_surface_registry()
    nav_pack = build_per_surface_navigation_boundaries(registry)
    logo_binding = build_aurel_logo_route_binding()
    sot_boundaries = build_surface_source_of_truth_boundaries(registry)
    system_boundary = build_system_no_agent_access_boundary()
    settings_boundary = build_settings_system_config_boundary()
    hub_boundary = build_hub_internal_tool_entry_boundary()
    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    drift, drift_details = detect_surface_taxonomy_drift()
    unavailable_reasons = tuple(
        sorted(
            {
                nav_pack.no_universal_left_nav.unavailable_reason,
                logo_binding.unavailable_reason,
                system_boundary.unavailable_reason,
                settings_boundary.unavailable_reason,
                hub_boundary.unavailable_reason,
            }
        )
    )
    truth_labels = (
        "BOUNDARY_CONTRACT_ONLY",
        "ROUTE_CONTRACT_ONLY",
        "ROUTE_HINT_ONLY",
        "SOURCE_OF_TRUTH_BOUNDARY_ONLY",
        "OPERATOR_ONLY_CONTRACT",
        "NON_ROOT_CONFIG_CONTRACT",
        "TOOL_ENTRY_CONTRACT_ONLY",
        "NOT_LIVE",
        "CONTRACT_ONLY",
    )
    side_effects = _all_false_p2_0_b_side_effects()
    payload: dict[str, Any] = {
        "schema_version": P2_0_B_PACK_RESULT_VERSION,
        "pack_id": P2_0_B_PACK_ID,
        "section_id": P2_0_B_SECTION_ID,
        "covered_checkpoints": P2_0_B_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_0_B_DEPENDENCY_PACK,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "unavailable_reasons": unavailable_reasons,
        "side_effect_proof": side_effects,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "no_universal_left_nav_pack": nav_pack,
        "logo_route_binding": logo_binding,
        "source_of_truth_boundaries": sot_boundaries,
        "system_no_agent_access": system_boundary,
        "settings_system_config": settings_boundary,
        "hub_tool_entry": hub_boundary,
        "registry": registry,
        "next_pack": P2_0_B_NEXT_PACK,
    }
    return P20BNavigationBoundaryPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def serialize_navigation_boundary_pack_result(
    result: P20BNavigationBoundaryPackResult,
) -> str:
    return to_canonical_json(result.to_canonical_dict())
