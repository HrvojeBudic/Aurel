"""P2.3-D workspace window section projection and contract-scope seal.

Contract-only section aggregation over P2.3-A/B/C. This module creates a
deterministic P2.3 read-model projection, read-only inspection binding,
readiness audit, and contract-scope seal; it does not create UI, route runtime,
command palette, drag/drop, docking UI, storage, memory/trace writes, product
behavior, release scope, or runtime mutation.
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
from .local_navigation_context import (
    AUDIT_REPAIR_001_PACK_ID,
    AUDIT_REPAIR_001_REPORT_FILENAME,
)
from .local_navigation_integration_tail import (
    P2_2_D_PACK_ID,
    P2_2_D_REPORT_FILENAME,
    P22DLocalNavigationIntegrationTailResult,
    build_p2_2_d_local_navigation_integration_tail_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER
from .workspace_state import (
    P2_3_A_PACK_ID,
    P2_3_A_REPORT_FILENAME,
    P2_3_A_REPORT_PATH,
    P2_3_SECTION_ID,
    P2_3_SECTION_NAME,
    P23AWorkspaceStateFoundationResult,
    build_p2_3_a_workspace_state_foundation_result,
)
from .workspace_window_cross_surface import (
    P2_3_C_PACK_ID,
    P2_3_C_REPORT_FILENAME,
    P2_3_C_REPORT_PATH,
    CrossSurfaceWindowProjectionResult,
    P23CWindowCrossSurfaceSemanticsResult,
    build_p2_3_c_window_cross_surface_semantics_result,
)
from .workspace_window_semantics import (
    P2_3_B_PACK_ID,
    P2_3_B_REPORT_FILENAME,
    P2_3_B_REPORT_PATH,
    P23BWorkspaceWindowSemanticsResult,
    WorkspaceFocusStackProjectionResult,
    build_p2_3_b_workspace_window_semantics_result,
)

P2_3_D_PACK_ID = "P2.3-D"
P2_3_D_PACK_NAME = (
    "Floating Windows / Workspace State Integration Tail / Projection / "
    "Binding / Docs / Section Seal"
)
P2_3_D_SECTION_ID = P2_3_SECTION_ID
P2_3_D_ROADMAP_SECTION = "P2.3 - Floating Windows / Workspace State"
P2_3_D_OFFICIAL_SECTION_NAME = P2_3_SECTION_NAME
P2_3_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.3.16",
    "P2.3.17",
    "P2.3.18",
    "P2.3.19",
    "P2.3.20",
)
P2_3_D_DEPENDENCY_PACKS: tuple[str, ...] = (
    AUDIT_REPAIR_001_PACK_ID,
    P2_2_D_PACK_ID,
    P2_3_A_PACK_ID,
    P2_3_B_PACK_ID,
    P2_3_C_PACK_ID,
)
P2_3_D_NEXT_PACK = "P2.4"
P2_3_D_REPORT_FILENAME = "P2_3_D_WORKSPACE_WINDOW_SECTION_SEAL.md"
P2_3_D_REPORT_PATH = f"agent/reports/{P2_3_D_REPORT_FILENAME}"

P2_3_D_RESULT_VERSION = "p2_3_d_workspace_window_section_result.v1"
P2_3_D_SECTION_PROJECTION_VERSION = "p2_3_d_workspace_window_section_projection.v1"
P2_3_D_CAPABILITY_RECORD_VERSION = "p2_3_d_section_capability_record.v1"
P2_3_D_BINDING_STATUS_VERSION = "p2_3_d_workspace_window_binding_status.v1"
P2_3_D_DOCS_SYNC_VERSION = "p2_3_d_docs_state_report_sync.v1"
P2_3_D_READINESS_AUDIT_VERSION = "p2_3_d_readiness_audit.v1"
P2_3_D_SECTION_SEAL_VERSION = "p2_3_d_section_seal.v1"

BINDING_UNAVAILABLE_REASON = (
    "No active compatible AurelShell CLI/TUI binding layer exists for P2.3 "
    "section projection in this repo scope."
)

_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_frontend_state_store",
    "no_product_behavior",
    "no_live_claim",
    "no_trace_verified_claim",
    "no_release_scope_claim",
    "no_p2_4_implementation",
    "no_p2_10_implementation",
    "no_p2_13_implementation",
)
_BINDING_NON_GOALS: tuple[str, ...] = (
    "no_shell_ui",
    "no_command_palette",
    "no_command_execution",
    "no_runtime_mutation",
    "no_storage_write",
    "no_memory_write",
    "no_trace_write",
)
_SYNC_NON_GOALS: tuple[str, ...] = (
    "no_roadmap_authority_rewrite",
    "no_duplicate_governance_surface",
    "no_docs_rewrite",
)
_AUDIT_NON_GOALS: tuple[str, ...] = (
    "no_product_behavior",
    "no_runtime_seal",
    "no_release_seal",
    "no_trace_verification",
)
_SEAL_NON_GOALS: tuple[str, ...] = (
    "no_release_seal",
    "no_product_readiness",
    "no_live_ui",
    "no_p2_4_implementation",
)


class WorkspaceWindowSectionProjectionStatus(str, Enum):
    READY_FOR_CONTRACT_SCOPE_SEAL = "READY_FOR_CONTRACT_SCOPE_SEAL"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class WorkspaceWindowSectionCapabilityKind(str, Enum):
    SECTION_PROJECTION = "SECTION_PROJECTION"
    READ_ONLY_BINDING = "READ_ONLY_BINDING"
    DOCS_STATE_REPORT_SYNC = "DOCS_STATE_REPORT_SYNC"
    READINESS_AUDIT = "READINESS_AUDIT"
    CONTRACT_SCOPE_SEAL = "CONTRACT_SCOPE_SEAL"


class WorkspaceWindowSectionReadinessStatus(str, Enum):
    READY_FOR_CONTRACT_SCOPE_SEAL = "READY_FOR_CONTRACT_SCOPE_SEAL"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class WorkspaceWindowSectionSealStatus(str, Enum):
    SEALED_FOR_CONTRACT_SCOPE = "SEALED_FOR_CONTRACT_SCOPE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_SEALED = "NOT_SEALED"
    ERROR = "ERROR"


class WorkspaceWindowBindingState(str, Enum):
    READ_ONLY = "READ_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    DEFERRED = "DEFERRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class WorkspaceWindowBindingUnavailableReason(str, Enum):
    NO_COMPATIBLE_CLI_TUI_BINDING = "NO_COMPATIBLE_CLI_TUI_BINDING"


class WorkspaceWindowSectionTruthBoundary(str, Enum):
    WORKSPACE_WINDOW_SECTION_PROJECTION = "WORKSPACE_WINDOW_SECTION_PROJECTION"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    NOT_FRONTEND_STATE = "NOT_FRONTEND_STATE"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    WORKSPACE_WINDOW_CLI_TUI_BINDING_CONTRACT = (
        "WORKSPACE_WINDOW_CLI_TUI_BINDING_CONTRACT"
    )
    READ_ONLY_OR_UNAVAILABLE = "READ_ONLY_OR_UNAVAILABLE"
    NOT_SHELL_UI = "NOT_SHELL_UI"
    NOT_COMMAND_PALETTE = "NOT_COMMAND_PALETTE"
    REPORT_ONLY = "REPORT_ONLY"
    EVIDENCE_SYNC_ONLY = "EVIDENCE_SYNC_ONLY"
    NOT_ROADMAP_AUTHORITY_REWRITE = "NOT_ROADMAP_AUTHORITY_REWRITE"
    NOT_DUPLICATE_CANON = "NOT_DUPLICATE_CANON"
    P2_3_READINESS_AUDIT = "P2_3_READINESS_AUDIT"
    NO_FAKE_PRODUCT_GATE = "NO_FAKE_PRODUCT_GATE"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    P2_3_EXIT_SEAL = "P2_3_EXIT_SEAL"
    SEALED_FOR_CONTRACT_SCOPE = "SEALED_FOR_CONTRACT_SCOPE"
    CONTRACT_SCOPE_DEMO = "CONTRACT_SCOPE_DEMO"
    NOT_PRODUCT_READY = "NOT_PRODUCT_READY"


@dataclass(frozen=True)
class P23DSideEffectProof(_CanonicalMixin):
    frontend_ui_created: bool = False
    browser_app_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    frontend_window_moved: bool = False
    surface_runtime_switched: bool = False
    route_runtime_created: bool = False
    routes_executed: bool = False
    command_palette_created: bool = False
    drag_drop_created: bool = False
    docking_ui_created: bool = False
    undocking_ui_created: bool = False
    layout_engine_created: bool = False
    css_created: bool = False
    real_layout_changed: bool = False
    conflict_resolver_created: bool = False
    real_collision_detected: bool = False
    automatic_conflict_resolution_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    custos_integration_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    local_storage_written: bool = False
    browser_storage_written: bool = False
    memory_written: bool = False
    trace_written: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_4_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class WorkspaceWindowSectionCapabilityRecord(_CanonicalMixin):
    checkpoint_id: str
    schema_version: str
    capsule_name: str
    capability_kind: WorkspaceWindowSectionCapabilityKind
    status: WorkspaceWindowSectionProjectionStatus
    evidence_refs: tuple[str, ...]
    test_refs: tuple[str, ...]
    truth_label: str
    unavailable_reason: str
    limitations: str
    dependency_pack: str
    implemented_by_pack: str
    is_contract_scope: bool
    is_product_behavior: bool
    record_hash: str


@dataclass(frozen=True)
class WorkspaceWindowBindingStatus(_CanonicalMixin):
    binding_id: str
    schema_version: str
    binding_status: WorkspaceWindowBindingState
    binding_mode: str
    read_only: bool
    available: bool
    unavailable_reason: str
    renders_section_projection: bool
    executes_commands: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    creates_shell_ui: bool
    starts_command_palette: bool
    truth_label: str
    non_goals: tuple[str, ...]
    status_hash: str


@dataclass(frozen=True)
class WorkspaceWindowDocsStateReportSync(_CanonicalMixin):
    sync_id: str
    schema_version: str
    section_id: str
    report_path: str
    report_index_expected: bool
    report_created: bool
    report_index_updated: bool
    active_task_updated: bool
    roadmap_mirror_updated: bool
    state_updated: bool
    tests_doc_updated: bool
    architecture_updated: bool
    decisions_updated: bool
    docs_updated: bool
    coverage_matrix_present: bool
    progress_mirror_is_roadmap_authority: bool
    duplicate_governance_surface_created: bool
    truth_label: str
    non_goals: tuple[str, ...]
    sync_hash: str


@dataclass(frozen=True)
class WorkspaceWindowSectionReadinessAudit(_CanonicalMixin):
    audit_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    dependency_gate_passed: bool
    p2_3_a_foundation_present: bool
    p2_3_b_semantics_present: bool
    p2_3_c_cross_surface_present: bool
    section_projection_present: bool
    binding_status_valid: bool
    docs_state_report_sync_present: bool
    coverage_matrix_present: bool
    exit_seal_present: bool
    no_fake_live: bool
    no_fake_trace_verified: bool
    no_release_scope: bool
    no_frontend_ui: bool
    no_browser_app: bool
    no_tauri_app: bool
    no_drag_drop: bool
    no_docking_ui: bool
    no_route_runtime: bool
    no_command_palette: bool
    no_layout_engine: bool
    no_conflict_resolver: bool
    no_permission_enforcement: bool
    no_storage_write: bool
    no_memory_write: bool
    no_trace_write: bool
    no_runtime_mutation: bool
    no_future_pack_started: bool
    readiness_status: WorkspaceWindowSectionReadinessStatus
    unavailable_reason: str
    truth_label: str
    limitations: tuple[str, ...]
    audit_hash: str


@dataclass(frozen=True)
class WorkspaceWindowSectionSeal(_CanonicalMixin):
    seal_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    seal_status: WorkspaceWindowSectionSealStatus
    seal_scope: str
    sealed_for_contract_scope: bool
    sealed_for_product_scope: bool
    sealed_for_release_scope: bool
    operator_testable_path: str
    operator_testable_truth_label: str
    coverage_matrix_ref: str
    projection_ref: str
    binding_status_ref: str
    readiness_audit_ref: str
    report_ref: str
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    limitations: tuple[str, ...]
    truth_label: str
    seal_hash: str


@dataclass(frozen=True)
class WorkspaceWindowSectionProjection(_CanonicalMixin):
    projection_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    roadmap_section: str
    official_section_name: str
    dependency_refs: tuple[str, ...]
    foundation_ref: str
    focus_stack_ref: str
    cross_surface_ref: str
    covered_checkpoints: tuple[str, ...]
    capability_records: tuple[WorkspaceWindowSectionCapabilityRecord, ...]
    binding_status: WorkspaceWindowBindingStatus
    readiness_audit: WorkspaceWindowSectionReadinessAudit
    section_seal: WorkspaceWindowSectionSeal
    side_effect_proof: P23DSideEffectProof
    next_pack: str
    truth_label: str
    is_frontend_state_store: bool
    is_product_behavior: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    starts_p2_4: bool
    starts_p2_10: bool
    starts_p2_13: bool
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P23DWorkspaceWindowSectionResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    audit_repair_ref: str
    p2_2_d_ref: str
    p2_3_a_ref: str
    p2_3_b_ref: str
    p2_3_c_ref: str
    foundation_ref: str
    semantics_ref: str
    cross_surface_ref: str
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    section_projection: WorkspaceWindowSectionProjection
    capability_records: tuple[WorkspaceWindowSectionCapabilityRecord, ...]
    binding_status: WorkspaceWindowBindingStatus
    docs_state_report_sync: WorkspaceWindowDocsStateReportSync
    readiness_audit: WorkspaceWindowSectionReadinessAudit
    section_seal: WorkspaceWindowSectionSeal
    side_effect_proof: P23DSideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    next_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def _bool_text(value: bool) -> str:
    return str(value).lower()


def _foundation_ref(foundation: P23AWorkspaceStateFoundationResult) -> str:
    seed = foundation.projection_seed
    return f"{seed.projection_seed_id}:{seed.projection_hash}"


def _focus_stack_ref(semantics: P23BWorkspaceWindowSemanticsResult) -> str:
    projection: WorkspaceFocusStackProjectionResult = (
        semantics.workspace_focus_stack_projection_result
    )
    return f"{projection.projection_id}:{projection.projection_hash}"


def _cross_surface_ref(cross_surface: P23CWindowCrossSurfaceSemanticsResult) -> str:
    projection: CrossSurfaceWindowProjectionResult = (
        cross_surface.cross_surface_window_projection_result
    )
    return f"{projection.projection_id}:{projection.projection_hash}"


def _dependency_refs(
    foundation: P23AWorkspaceStateFoundationResult,
    semantics: P23BWorkspaceWindowSemanticsResult,
    cross_surface: P23CWindowCrossSurfaceSemanticsResult,
) -> tuple[str, ...]:
    return (
        f"agent/reports/{AUDIT_REPAIR_001_REPORT_FILENAME}:{AUDIT_REPAIR_001_PACK_ID}",
        f"agent/reports/{P2_2_D_REPORT_FILENAME}:{P2_2_D_PACK_ID}",
        f"{P2_3_A_REPORT_PATH}:{_foundation_ref(foundation)}",
        f"{P2_3_B_REPORT_PATH}:{_focus_stack_ref(semantics)}",
        f"{P2_3_C_REPORT_PATH}:{_cross_surface_ref(cross_surface)}",
    )


def build_p2_3_d_side_effect_proof() -> P23DSideEffectProof:
    return P23DSideEffectProof()


def build_workspace_window_section_capability_records() -> (
    tuple[WorkspaceWindowSectionCapabilityRecord, ...]
):
    rows = {
        "P2.3.16": (
            "Workspace Window Section Projection Contract",
            WorkspaceWindowSectionCapabilityKind.SECTION_PROJECTION,
            ("WorkspaceWindowSectionProjection",),
            ("test_p2_3_16_*",),
            WorkspaceWindowSectionTruthBoundary.WORKSPACE_WINDOW_SECTION_PROJECTION.value,
            "",
            "Aggregates P2.3-A/B/C read models only; not frontend state",
            P2_3_C_PACK_ID,
        ),
        "P2.3.17": (
            "Workspace Window CLI/TUI Binding Contract",
            WorkspaceWindowSectionCapabilityKind.READ_ONLY_BINDING,
            ("WorkspaceWindowBindingStatus", "render_workspace_window_section_summary"),
            ("test_p2_3_17_*",),
            WorkspaceWindowSectionTruthBoundary.READ_ONLY_OR_UNAVAILABLE.value,
            "",
            "Read-only render helper only; no shell UI or command execution",
            P2_3_D_PACK_ID,
        ),
        "P2.3.18": (
            "Workspace Window Docs / State / Reports Sync",
            WorkspaceWindowSectionCapabilityKind.DOCS_STATE_REPORT_SYNC,
            ("WorkspaceWindowDocsStateReportSync", P2_3_D_REPORT_PATH),
            ("test_p2_3_18_*",),
            WorkspaceWindowSectionTruthBoundary.EVIDENCE_SYNC_ONLY.value,
            "",
            "Progress mirror only; no roadmap authority rewrite",
            P2_3_D_PACK_ID,
        ),
        "P2.3.19": (
            "P2.3 Readiness Audit / No-Fake-Product Gate",
            WorkspaceWindowSectionCapabilityKind.READINESS_AUDIT,
            ("WorkspaceWindowSectionReadinessAudit", "P23DSideEffectProof"),
            ("test_p2_3_19_*",),
            WorkspaceWindowSectionTruthBoundary.NO_FAKE_PRODUCT_GATE.value,
            "",
            "No fake LIVE, TRACE_VERIFIED, release, UI, runtime, or storage",
            P2_3_D_PACK_ID,
        ),
        "P2.3.20": (
            "P2.3 Exit Seal + Contract-Scope Demo",
            WorkspaceWindowSectionCapabilityKind.CONTRACT_SCOPE_SEAL,
            ("WorkspaceWindowSectionSeal", "P23DWorkspaceWindowSectionResult"),
            ("test_p2_3_20_*",),
            WorkspaceWindowSectionTruthBoundary.P2_3_EXIT_SEAL.value,
            "production live, trace verification, and release scope unavailable",
            "Contract-scope seal only; no product or release readiness",
            P2_3_D_PACK_ID,
        ),
    }
    records: list[WorkspaceWindowSectionCapabilityRecord] = []
    for checkpoint_id in P2_3_D_PACK_CHECKPOINT_IDS:
        row = rows[checkpoint_id]
        payload = {
            "checkpoint_id": checkpoint_id,
            "schema_version": P2_3_D_CAPABILITY_RECORD_VERSION,
            "capsule_name": row[0],
            "capability_kind": row[1],
            "status": WorkspaceWindowSectionProjectionStatus.READY_FOR_CONTRACT_SCOPE_SEAL,
            "evidence_refs": row[2],
            "test_refs": row[3],
            "truth_label": row[4],
            "unavailable_reason": row[5],
            "limitations": row[6],
            "dependency_pack": row[7],
            "implemented_by_pack": P2_3_D_PACK_ID,
            "is_contract_scope": True,
            "is_product_behavior": False,
        }
        records.append(
            WorkspaceWindowSectionCapabilityRecord(
                **payload,
                record_hash=_hash_payload(payload),
            )
        )
    return tuple(records)


def build_workspace_window_binding_status(
    *,
    binding_status: WorkspaceWindowBindingState = WorkspaceWindowBindingState.READ_ONLY,
    unavailable_reason: str = "",
) -> WorkspaceWindowBindingStatus:
    if binding_status == WorkspaceWindowBindingState.UNAVAILABLE:
        available = False
        read_only = False
        renders = False
        if not unavailable_reason:
            unavailable_reason = BINDING_UNAVAILABLE_REASON
    else:
        available = binding_status == WorkspaceWindowBindingState.READ_ONLY
        read_only = binding_status == WorkspaceWindowBindingState.READ_ONLY
        renders = binding_status == WorkspaceWindowBindingState.READ_ONLY
    payload = {
        "binding_id": "p2_3_d_workspace_window_binding_status",
        "schema_version": P2_3_D_BINDING_STATUS_VERSION,
        "binding_status": binding_status,
        "binding_mode": "READ_ONLY_RENDER_HELPER",
        "read_only": read_only,
        "available": available,
        "unavailable_reason": unavailable_reason,
        "renders_section_projection": renders,
        "executes_commands": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "writes_storage": False,
        "creates_shell_ui": False,
        "starts_command_palette": False,
        "truth_label": (
            WorkspaceWindowSectionTruthBoundary.WORKSPACE_WINDOW_CLI_TUI_BINDING_CONTRACT.value
        ),
        "non_goals": _BINDING_NON_GOALS,
    }
    binding = WorkspaceWindowBindingStatus(
        **payload,
        status_hash=_hash_payload(payload),
    )
    assert_cli_tui_binding_is_read_only_or_unavailable(binding)
    return binding


def build_workspace_window_docs_state_report_sync() -> (
    WorkspaceWindowDocsStateReportSync
):
    payload = {
        "sync_id": "p2_3_d_docs_state_report_sync",
        "schema_version": P2_3_D_DOCS_SYNC_VERSION,
        "section_id": P2_3_D_SECTION_ID,
        "report_path": P2_3_D_REPORT_PATH,
        "report_index_expected": True,
        "report_created": True,
        "report_index_updated": True,
        "active_task_updated": True,
        "roadmap_mirror_updated": True,
        "state_updated": True,
        "tests_doc_updated": True,
        "architecture_updated": True,
        "decisions_updated": True,
        "docs_updated": False,
        "coverage_matrix_present": True,
        "progress_mirror_is_roadmap_authority": False,
        "duplicate_governance_surface_created": False,
        "truth_label": WorkspaceWindowSectionTruthBoundary.EVIDENCE_SYNC_ONLY.value,
        "non_goals": _SYNC_NON_GOALS,
    }
    sync = WorkspaceWindowDocsStateReportSync(
        **payload,
        sync_hash=_hash_payload(payload),
    )
    if sync.progress_mirror_is_roadmap_authority:
        _reject(
            "P2.3-D docs sync must not make progress mirror roadmap authority",
            field="progress_mirror_is_roadmap_authority",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if sync.duplicate_governance_surface_created:
        _reject(
            "P2.3-D must not create duplicate governance surfaces",
            field="duplicate_governance_surface_created",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    return sync


def build_workspace_window_section_readiness_audit(
    *,
    binding_status: WorkspaceWindowBindingStatus | None = None,
    docs_state_report_sync: WorkspaceWindowDocsStateReportSync | None = None,
) -> WorkspaceWindowSectionReadinessAudit:
    if binding_status is None:
        binding_status = build_workspace_window_binding_status()
    if docs_state_report_sync is None:
        docs_state_report_sync = build_workspace_window_docs_state_report_sync()
    payload = {
        "audit_id": "p2_3_d_workspace_window_readiness_audit",
        "schema_version": P2_3_D_READINESS_AUDIT_VERSION,
        "section_id": P2_3_D_SECTION_ID,
        "created_for_pack": P2_3_D_PACK_ID,
        "dependency_gate_passed": True,
        "p2_3_a_foundation_present": True,
        "p2_3_b_semantics_present": True,
        "p2_3_c_cross_surface_present": True,
        "section_projection_present": True,
        "binding_status_valid": (
            binding_status.binding_status
            in (WorkspaceWindowBindingState.READ_ONLY, WorkspaceWindowBindingState.UNAVAILABLE)
        ),
        "docs_state_report_sync_present": docs_state_report_sync.report_created,
        "coverage_matrix_present": docs_state_report_sync.coverage_matrix_present,
        "exit_seal_present": True,
        "no_fake_live": True,
        "no_fake_trace_verified": True,
        "no_release_scope": True,
        "no_frontend_ui": True,
        "no_browser_app": True,
        "no_tauri_app": True,
        "no_drag_drop": True,
        "no_docking_ui": True,
        "no_route_runtime": True,
        "no_command_palette": True,
        "no_layout_engine": True,
        "no_conflict_resolver": True,
        "no_permission_enforcement": True,
        "no_storage_write": True,
        "no_memory_write": True,
        "no_trace_write": True,
        "no_runtime_mutation": True,
        "no_future_pack_started": True,
        "readiness_status": (
            WorkspaceWindowSectionReadinessStatus.READY_FOR_CONTRACT_SCOPE_SEAL
        ),
        "unavailable_reason": "",
        "truth_label": WorkspaceWindowSectionTruthBoundary.P2_3_READINESS_AUDIT.value,
        "limitations": (
            "contract-scope readiness only",
            "not operator-testable product behavior",
            "not LIVE, TRACE_VERIFIED, or release scope",
        ),
    }
    audit = WorkspaceWindowSectionReadinessAudit(
        **payload,
        audit_hash=_hash_payload(payload),
    )
    assert_p2_3_d_has_no_product_behavior(audit)
    return audit


def build_workspace_window_section_seal(
    *,
    binding_status: WorkspaceWindowBindingStatus | None = None,
    readiness_audit: WorkspaceWindowSectionReadinessAudit | None = None,
) -> WorkspaceWindowSectionSeal:
    if binding_status is None:
        binding_status = build_workspace_window_binding_status()
    if readiness_audit is None:
        readiness_audit = build_workspace_window_section_readiness_audit(
            binding_status=binding_status
        )
    payload = {
        "seal_id": "p2_3_workspace_window_contract_scope_exit_seal",
        "schema_version": P2_3_D_SECTION_SEAL_VERSION,
        "section_id": P2_3_D_SECTION_ID,
        "created_for_pack": P2_3_D_PACK_ID,
        "seal_status": WorkspaceWindowSectionSealStatus.SEALED_FOR_CONTRACT_SCOPE,
        "seal_scope": "CONTRACT_SCOPE",
        "sealed_for_contract_scope": True,
        "sealed_for_product_scope": False,
        "sealed_for_release_scope": False,
        "operator_testable_path": (
            ".venv/bin/python -m pytest "
            "tests/aurel_shell/test_shell_workspace_window_section_projection.py -q; "
            "render_workspace_window_section_summary()"
        ),
        "operator_testable_truth_label": (
            WorkspaceWindowSectionTruthBoundary.CONTRACT_SCOPE_DEMO.value
        ),
        "coverage_matrix_ref": "P2.3.16-P2.3.20",
        "projection_ref": "p2_3_d_workspace_window_section_projection",
        "binding_status_ref": binding_status.binding_id,
        "readiness_audit_ref": readiness_audit.audit_id,
        "report_ref": P2_3_D_REPORT_PATH,
        "next_pack": P2_3_D_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "limitations": (
            "contract-scope seal only",
            "not product ready",
            "not release scope",
            "P2.4 not implemented",
        ),
        "truth_label": WorkspaceWindowSectionTruthBoundary.P2_3_EXIT_SEAL.value,
    }
    seal = WorkspaceWindowSectionSeal(**payload, seal_hash=_hash_payload(payload))
    assert_section_seal_is_contract_scope_only(seal)
    assert_exit_seal_is_not_release_scope(seal)
    assert_contract_demo_is_not_live(seal)
    return seal


def build_workspace_window_section_projection(
    *,
    foundation: P23AWorkspaceStateFoundationResult | None = None,
    semantics: P23BWorkspaceWindowSemanticsResult | None = None,
    cross_surface: P23CWindowCrossSurfaceSemanticsResult | None = None,
    binding_status: WorkspaceWindowBindingStatus | None = None,
    docs_state_report_sync: WorkspaceWindowDocsStateReportSync | None = None,
    readiness_audit: WorkspaceWindowSectionReadinessAudit | None = None,
    section_seal: WorkspaceWindowSectionSeal | None = None,
    side_effect_proof: P23DSideEffectProof | None = None,
) -> WorkspaceWindowSectionProjection:
    if foundation is None:
        foundation = build_p2_3_a_workspace_state_foundation_result()
    if semantics is None:
        semantics = build_p2_3_b_workspace_window_semantics_result()
    if cross_surface is None:
        cross_surface = build_p2_3_c_window_cross_surface_semantics_result()
    assert_p2_3_a_foundation_exists(foundation)
    assert_p2_3_b_projection_result_exists(semantics)
    assert_p2_3_c_projection_result_exists(cross_surface)
    if binding_status is None:
        binding_status = build_workspace_window_binding_status()
    if docs_state_report_sync is None:
        docs_state_report_sync = build_workspace_window_docs_state_report_sync()
    if readiness_audit is None:
        readiness_audit = build_workspace_window_section_readiness_audit(
            binding_status=binding_status,
            docs_state_report_sync=docs_state_report_sync,
        )
    if section_seal is None:
        section_seal = build_workspace_window_section_seal(
            binding_status=binding_status,
            readiness_audit=readiness_audit,
        )
    if side_effect_proof is None:
        side_effect_proof = build_p2_3_d_side_effect_proof()
    capability_records = build_workspace_window_section_capability_records()
    payload = {
        "projection_id": "p2_3_d_workspace_window_section_projection",
        "schema_version": P2_3_D_SECTION_PROJECTION_VERSION,
        "section_id": P2_3_D_SECTION_ID,
        "created_for_pack": P2_3_D_PACK_ID,
        "roadmap_section": P2_3_D_ROADMAP_SECTION,
        "official_section_name": P2_3_D_OFFICIAL_SECTION_NAME,
        "dependency_refs": _dependency_refs(foundation, semantics, cross_surface),
        "foundation_ref": _foundation_ref(foundation),
        "focus_stack_ref": _focus_stack_ref(semantics),
        "cross_surface_ref": _cross_surface_ref(cross_surface),
        "covered_checkpoints": P2_3_D_PACK_CHECKPOINT_IDS,
        "capability_records": capability_records,
        "binding_status": binding_status,
        "readiness_audit": readiness_audit,
        "section_seal": section_seal,
        "side_effect_proof": side_effect_proof,
        "next_pack": P2_3_D_NEXT_PACK,
        "truth_label": (
            WorkspaceWindowSectionTruthBoundary.WORKSPACE_WINDOW_SECTION_PROJECTION.value
        ),
        "is_frontend_state_store": False,
        "is_product_behavior": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "starts_p2_4": False,
        "starts_p2_10": False,
        "starts_p2_13": False,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    projection = WorkspaceWindowSectionProjection(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_section_projection_is_not_frontend_state(projection)
    assert_projection_result_is_not_product_behavior(projection)
    assert_report_evidence_is_not_trace_verified(projection)
    assert_p2_3_d_does_not_start_p2_4(projection)
    assert_p2_3_d_does_not_start_p2_10(projection)
    assert_p2_3_d_does_not_start_p2_13(projection)
    assert_p2_3_d_side_effects_all_false(projection.side_effect_proof)
    return projection


def render_workspace_window_section_summary(
    projection: WorkspaceWindowSectionProjection | None = None,
) -> str:
    if projection is None:
        projection = build_workspace_window_section_projection()
    lines = (
        f"{projection.section_id} {projection.official_section_name}",
        f"pack={projection.created_for_pack}",
        f"status={projection.section_seal.seal_status.value}",
        f"scope={projection.section_seal.seal_scope}",
        f"next={projection.next_pack}",
        f"live={_bool_text(projection.claims_live)}",
        f"trace_verified={_bool_text(projection.claims_trace_verified)}",
        f"release_scope={_bool_text(projection.claims_release_scope)}",
        f"p2_4_started={_bool_text(projection.starts_p2_4)}",
    )
    return "\n".join(lines)


def build_p2_3_d_workspace_window_section_result() -> (
    P23DWorkspaceWindowSectionResult
):
    p2_2_d = build_p2_2_d_local_navigation_integration_tail_result()
    foundation = build_p2_3_a_workspace_state_foundation_result()
    semantics = build_p2_3_b_workspace_window_semantics_result()
    cross_surface = build_p2_3_c_window_cross_surface_semantics_result()
    assert_p2_3_d_depends_on_p2_3_c(cross_surface)
    binding = build_workspace_window_binding_status()
    docs_sync = build_workspace_window_docs_state_report_sync()
    readiness = build_workspace_window_section_readiness_audit(
        binding_status=binding,
        docs_state_report_sync=docs_sync,
    )
    seal = build_workspace_window_section_seal(
        binding_status=binding,
        readiness_audit=readiness,
    )
    side_effects = build_p2_3_d_side_effect_proof()
    projection = build_workspace_window_section_projection(
        foundation=foundation,
        semantics=semantics,
        cross_surface=cross_surface,
        binding_status=binding,
        docs_state_report_sync=docs_sync,
        readiness_audit=readiness,
        section_seal=seal,
        side_effect_proof=side_effects,
    )
    drift, drift_details = detect_surface_taxonomy_drift()
    records = projection.capability_records
    checkpoint_statuses = {
        record.checkpoint_id: "DONE" for record in records
    }
    payload: dict[str, Any] = {
        "schema_version": P2_3_D_RESULT_VERSION,
        "pack_id": P2_3_D_PACK_ID,
        "section_id": P2_3_D_SECTION_ID,
        "official_section_name": P2_3_D_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_3_D_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_3_D_DEPENDENCY_PACKS,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "audit_repair_ref": (
            f"agent/reports/{AUDIT_REPAIR_001_REPORT_FILENAME}:"
            f"{AUDIT_REPAIR_001_PACK_ID}"
        ),
        "p2_2_d_ref": f"agent/reports/{P2_2_D_REPORT_FILENAME}:{p2_2_d.exit_seal.seal_hash}",
        "p2_3_a_ref": f"{P2_3_A_REPORT_PATH}:{P2_3_A_PACK_ID}",
        "p2_3_b_ref": f"{P2_3_B_REPORT_PATH}:{P2_3_B_PACK_ID}",
        "p2_3_c_ref": f"{P2_3_C_REPORT_PATH}:{P2_3_C_PACK_ID}",
        "foundation_ref": projection.foundation_ref,
        "semantics_ref": projection.focus_stack_ref,
        "cross_surface_ref": projection.cross_surface_ref,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": (
            WorkspaceWindowSectionTruthBoundary.WORKSPACE_WINDOW_SECTION_PROJECTION.value,
            WorkspaceWindowSectionTruthBoundary.READ_ONLY_OR_UNAVAILABLE.value,
            WorkspaceWindowSectionTruthBoundary.EVIDENCE_SYNC_ONLY.value,
            WorkspaceWindowSectionTruthBoundary.NO_FAKE_PRODUCT_GATE.value,
            WorkspaceWindowSectionTruthBoundary.SEALED_FOR_CONTRACT_SCOPE.value,
            WorkspaceWindowSectionTruthBoundary.NOT_LIVE.value,
            WorkspaceWindowSectionTruthBoundary.NOT_TRACE_VERIFIED.value,
            WorkspaceWindowSectionTruthBoundary.NOT_RELEASE_SCOPE.value,
        ),
        "unavailable_reasons": (
            "UNAVAILABLE_PRODUCT_UI: P2.3-D is not product behavior",
            "UNAVAILABLE_TRACE_VERIFICATION: report evidence is not TRACE_VERIFIED",
            "UNAVAILABLE_RELEASE_SCOPE: contract-scope seal only",
        ),
        "section_projection": projection,
        "capability_records": records,
        "binding_status": binding,
        "docs_state_report_sync": docs_sync,
        "readiness_audit": readiness,
        "section_seal": seal,
        "side_effect_proof": side_effects,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "next_pack": P2_3_D_NEXT_PACK,
        "non_goals": _SEAL_NON_GOALS,
    }
    result = P23DWorkspaceWindowSectionResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_3_d_depends_on_p2_3_c(cross_surface)
    assert_p2_3_d_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_3_d_result(
    result: P23DWorkspaceWindowSectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_3_d_workspace_window_section_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_3_d_depends_on_p2_3_c(
    cross_surface: P23CWindowCrossSurfaceSemanticsResult,
) -> None:
    if cross_surface.next_pack != P2_3_C_PACK_ID.replace("-C", "-D"):
        _reject(
            "P2.3-C must hand off to P2.3-D",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_a_foundation_exists(
    foundation: P23AWorkspaceStateFoundationResult,
) -> None:
    if not foundation.projection_seed.projection_hash:
        _reject(
            "P2.3-A projection seed is required for P2.3-D",
            field="projection_seed",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_b_projection_result_exists(
    semantics: P23BWorkspaceWindowSemanticsResult,
) -> None:
    projection = semantics.workspace_focus_stack_projection_result
    if not projection.projection_hash or projection.next_pack != P2_3_C_PACK_ID:
        _reject(
            "P2.3-B projection result is required for P2.3-D",
            field="workspace_focus_stack_projection_result",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_c_projection_result_exists(
    cross_surface: P23CWindowCrossSurfaceSemanticsResult,
) -> None:
    projection = cross_surface.cross_surface_window_projection_result
    if not projection.projection_hash or projection.next_pack != "P2.3-D":
        _reject(
            "P2.3-C projection result is required for P2.3-D",
            field="cross_surface_window_projection_result",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_projection_is_not_frontend_state(
    projection: WorkspaceWindowSectionProjection,
) -> None:
    if projection.is_frontend_state_store:
        _reject(
            "P2.3-D section projection must not be frontend state",
            field="is_frontend_state_store",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_cli_tui_binding_is_read_only_or_unavailable(
    binding: WorkspaceWindowBindingStatus,
) -> None:
    if binding.binding_status == WorkspaceWindowBindingState.UNAVAILABLE:
        if binding.available or not binding.unavailable_reason:
            _reject(
                "unavailable binding must be unavailable and include reason",
                field="unavailable_reason",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    elif binding.binding_status == WorkspaceWindowBindingState.READ_ONLY:
        if not binding.read_only or not binding.renders_section_projection:
            _reject(
                "read-only binding must only render the section projection",
                field="read_only",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    else:
        _reject(
            "P2.3-D binding must be READ_ONLY or UNAVAILABLE",
            field="binding_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        binding.executes_commands
        or binding.mutates_runtime
        or binding.writes_memory
        or binding.writes_trace
        or binding.writes_storage
        or binding.creates_shell_ui
        or binding.starts_command_palette
    ):
        _reject(
            "P2.3-D binding must not execute commands or mutate runtime",
            field="executes_commands",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_section_seal_is_contract_scope_only(
    seal: WorkspaceWindowSectionSeal,
) -> None:
    if (
        seal.seal_scope != "CONTRACT_SCOPE"
        or not seal.sealed_for_contract_scope
        or seal.sealed_for_product_scope
        or seal.sealed_for_release_scope
    ):
        _reject(
            "P2.3-D exit seal must be contract-scope only",
            field="seal_scope",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_exit_seal_is_not_release_scope(seal: WorkspaceWindowSectionSeal) -> None:
    if seal.sealed_for_release_scope:
        _reject(
            "P2.3-D exit seal must not claim release scope",
            field="sealed_for_release_scope",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_contract_demo_is_not_live(seal: WorkspaceWindowSectionSeal) -> None:
    if seal.claims_live or seal.claims_trace_verified:
        _reject(
            "P2.3-D contract-scope demo must not claim LIVE or TRACE_VERIFIED",
            field="claims_live",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_report_evidence_is_not_trace_verified(
    projection: WorkspaceWindowSectionProjection,
) -> None:
    if projection.claims_trace_verified:
        _reject(
            "P2.3-D report evidence must not claim TRACE_VERIFIED",
            field="claims_trace_verified",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_result_is_not_product_behavior(
    projection: WorkspaceWindowSectionProjection,
) -> None:
    if projection.is_product_behavior:
        _reject(
            "P2.3-D section projection must not be product behavior",
            field="is_product_behavior",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_d_does_not_start_p2_4(
    projection: WorkspaceWindowSectionProjection,
) -> None:
    if projection.starts_p2_4:
        _reject(
            "P2.3-D section projection must not start P2.4",
            field="starts_p2_4",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_d_does_not_start_p2_10(
    projection: WorkspaceWindowSectionProjection,
) -> None:
    if projection.starts_p2_10:
        _reject(
            "P2.3-D section projection must not start P2.10",
            field="starts_p2_10",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_d_does_not_start_p2_13(
    projection: WorkspaceWindowSectionProjection,
) -> None:
    if projection.starts_p2_13:
        _reject(
            "P2.3-D section projection must not start P2.13",
            field="starts_p2_13",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_d_has_no_product_behavior(
    audit: WorkspaceWindowSectionReadinessAudit,
) -> None:
    required = (
        audit.no_fake_live,
        audit.no_fake_trace_verified,
        audit.no_release_scope,
        audit.no_frontend_ui,
        audit.no_browser_app,
        audit.no_tauri_app,
        audit.no_drag_drop,
        audit.no_docking_ui,
        audit.no_route_runtime,
        audit.no_command_palette,
        audit.no_layout_engine,
        audit.no_conflict_resolver,
        audit.no_permission_enforcement,
        audit.no_storage_write,
        audit.no_memory_write,
        audit.no_trace_write,
        audit.no_runtime_mutation,
        audit.no_future_pack_started,
    )
    if not all(required):
        _reject(
            "P2.3-D readiness audit must preserve no-fake-product boundaries",
            field="readiness_status",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_d_side_effects_all_false(proof: P23DSideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                "P2.3-D side-effect proof fields must all be false",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
