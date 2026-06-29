"""P2.3-A floating windows / workspace state foundation.

Contract-only workspace/window read models over the sealed P2.2 stack. This
module defines deterministic state contracts and projection seeds; it does not
create UI, a browser/Tauri app, draggable windows, storage, API/event runtime,
permission enforcement, memory/trace writes, or runtime mutation.
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
    P22LocalNavigationSealDecision,
    P22P23ReadinessDecision,
    build_p2_2_d_local_navigation_integration_tail_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_3_A_PACK_ID = "P2.3-A"
P2_3_SECTION_ID = "P2.3"
P2_3_SECTION_NAME = "Floating Windows / Workspace State"
P2_3_A_PACK_NAME = "Floating Windows / Workspace State Foundation"
P2_3_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.3.0",
    "P2.3.1",
    "P2.3.2",
    "P2.3.3",
    "P2.3.4",
    "P2.3.5",
)
P2_3_A_DEPENDENCY_PACKS: tuple[str, ...] = (
    AUDIT_REPAIR_001_PACK_ID,
    P2_2_D_PACK_ID,
)
P2_3_A_NEXT_PACK = "P2.3-B"
P2_3_A_REPORT_FILENAME = "P2_3_A_WORKSPACE_STATE_FOUNDATION.md"
P2_3_A_REPORT_PATH = f"agent/reports/{P2_3_A_REPORT_FILENAME}"

P2_3_A_REQUIRED_PREVIOUS_SEAL = (
    P22LocalNavigationSealDecision.SEALED_FOR_P2_2_CONTRACT_SCOPE.value
)
P2_3_A_REQUIRED_PREVIOUS_READINESS = (
    P22P23ReadinessDecision.READY_FOR_P2_3_PLAN.value
)
P2_3_A_PREVIOUS_REPORT = f"agent/reports/{P2_2_D_REPORT_FILENAME}"
P2_3_A_PREVIOUS_COMMIT = "d5ba094275131d4622339aa7e7c6db14285be34d"

P2_3_SECTION_INTAKE_GATE_VERSION = "p2_3_section_intake_gate.v1"
P2_3_WINDOW_IDENTITY_VERSION = "p2_3_floating_window_identity_contract.v1"
P2_3_WORKSPACE_STATE_VERSION = "p2_3_shell_workspace_state_contract.v1"
P2_3_LIFECYCLE_VERSION = "p2_3_floating_window_lifecycle_contract.v1"
P2_3_PLACEMENT_VERSION = "p2_3_floating_window_placement_intent_contract.v1"
P2_3_PROJECTION_SEED_VERSION = "p2_3_workspace_state_projection_seed.v1"
P2_3_A_RESULT_VERSION = "p2_3_a_workspace_state_foundation_result.v1"

_INTAKE_NON_GOALS: tuple[str, ...] = (
    "no_ui",
    "no_window_manager",
    "no_storage",
    "no_runtime_mutation",
    "no_p2_3_b",
)
_IDENTITY_NON_GOALS: tuple[str, ...] = (
    "no_duplicate_surface_registry",
    "no_window_instance_runtime",
    "no_permission_grant",
    "no_source_of_truth",
)
_WORKSPACE_NON_GOALS: tuple[str, ...] = (
    "no_browser_workspace",
    "no_old_workspace_surface_activation",
    "no_local_storage",
    "no_route_runtime",
)
_LIFECYCLE_NON_GOALS: tuple[str, ...] = (
    "no_runtime_lifecycle_engine",
    "no_event_bus",
    "no_notification_engine",
)
_PLACEMENT_NON_GOALS: tuple[str, ...] = (
    "no_css_layout",
    "no_z_index_runtime",
    "no_drag_drop",
    "no_window_manager",
)
_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_api_server",
    "no_event_runtime",
    "no_storage",
    "no_p2_3_b_implementation",
)


class P23CheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class FloatingWindowKind(str, Enum):
    SURFACE_PANEL = "SURFACE_PANEL"
    INSPECTOR = "INSPECTOR"
    CONTEXT_CARD = "CONTEXT_CARD"
    APPROVAL_PANEL = "APPROVAL_PANEL"
    TRACE_PANEL = "TRACE_PANEL"
    AGENT_CHAT_PANEL = "AGENT_CHAT_PANEL"
    DOCUMENT_PANEL = "DOCUMENT_PANEL"
    TOOL_PANEL = "TOOL_PANEL"
    SYSTEM_STATUS_PANEL = "SYSTEM_STATUS_PANEL"


class WorkspaceMode(str, Enum):
    SINGLE_SURFACE = "SINGLE_SURFACE"
    MULTI_WINDOW_READ_MODEL = "MULTI_WINDOW_READ_MODEL"
    REVIEW_WORKSPACE = "REVIEW_WORKSPACE"
    DEGRADED_UNAVAILABLE = "DEGRADED_UNAVAILABLE"


class FloatingWindowLifecycleState(str, Enum):
    DECLARED = "DECLARED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEFERRED = "DEFERRED"
    ERROR_BOUNDARY = "ERROR_BOUNDARY"


class FloatingWindowAvailability(str, Enum):
    CONTRACT_AVAILABLE = "CONTRACT_AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEFERRED = "DEFERRED"
    ERROR = "ERROR"


class PlacementIntent(str, Enum):
    DEFAULT = "DEFAULT"
    ANCHORED_TO_SURFACE = "ANCHORED_TO_SURFACE"
    SIDE_PANEL = "SIDE_PANEL"
    STACKED = "STACKED"
    OVERLAY_READ_MODEL = "OVERLAY_READ_MODEL"
    DEFERRED = "DEFERRED"


class LayerRole(str, Enum):
    BASE_WORKSPACE = "BASE_WORKSPACE"
    SURFACE_CONTENT = "SURFACE_CONTENT"
    FLOATING_PANEL = "FLOATING_PANEL"
    INSPECTION_LAYER = "INSPECTION_LAYER"
    STATUS_LAYER = "STATUS_LAYER"


class OwnerScope(str, Enum):
    SURFACE_OWNED = "SURFACE_OWNED"
    SHELL_READ_MODEL = "SHELL_READ_MODEL"
    OPERATOR_CONTEXT = "OPERATOR_CONTEXT"


class TruthBoundaryLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    PROJECTION_SEED_ONLY = "PROJECTION_SEED_ONLY"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"
    NOT_UI = "NOT_UI"
    NOT_RUNTIME = "NOT_RUNTIME"
    NOT_STORAGE = "NOT_STORAGE"
    NOT_AUTHORITY = "NOT_AUTHORITY"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    P2_2_DEPENDENCY_SEALED = "P2_2_DEPENDENCY_SEALED"
    P2_3_A_FOUNDATION = "P2_3_A_FOUNDATION"


@dataclass(frozen=True)
class P23ASideEffectProof(_CanonicalMixin):
    ui_created: bool = False
    browser_app_created: bool = False
    tauri_app_created: bool = False
    frontend_component_created: bool = False
    draggable_window_created: bool = False
    window_manager_created: bool = False
    css_layout_created: bool = False
    z_index_runtime_created: bool = False
    route_runtime_created: bool = False
    route_handler_created: bool = False
    api_server_created: bool = False
    http_route_created: bool = False
    event_bus_created: bool = False
    runtime_event_emitted: bool = False
    storage_created: bool = False
    local_storage_written: bool = False
    browser_storage_written: bool = False
    workspace_surface_created: bool = False
    old_workspace_activated: bool = False
    source_of_truth_created: bool = False
    permission_enforcement_created: bool = False
    authority_granted: bool = False
    custos_integration_created: bool = False
    tool_executed: bool = False
    workflow_started: bool = False
    memory_written: bool = False
    runtime_mutated: bool = False
    trace_written: bool = False
    global_trace_written: bool = False
    ledger_written: bool = False
    production_live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_3_b_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class P23CheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P23CheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str
    read_hash: str


@dataclass(frozen=True)
class P23SectionIntakeGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    pack_id: str
    section_id: str
    depends_on_packs: tuple[str, ...]
    required_previous_seal: str
    required_previous_readiness: str
    previous_report_ref: str
    previous_commit: str
    previous_seal_found: bool
    previous_readiness_found: bool
    audit_repair_report_ref: str
    audit_repair_required: bool
    audit_repair_found: bool
    gate_open: bool
    blocked_reasons: tuple[str, ...]
    starts_implementation: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class FloatingWindowIdentityContract(_CanonicalMixin):
    window_id: str
    schema_version: str
    window_kind: FloatingWindowKind
    owner_scope: OwnerScope
    owner_surface_id: str
    source_surface_id: str
    target_surface_id: str
    content_ref: str
    context_ref: str
    source_truth_boundary: TruthBoundaryLabel
    target_truth_boundary: TruthBoundaryLabel
    title: str
    owns_truth: bool
    grants_authority: bool
    executes_actions: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_ui: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class ShellWorkspaceStateContract(_CanonicalMixin):
    workspace_state_id: str
    schema_version: str
    workspace_mode: WorkspaceMode
    active_surface_id: str
    canonical_surface_ids: tuple[str, ...]
    floating_window_refs: tuple[str, ...]
    workspace_is_surface: bool
    old_workspace_surface_activated: bool
    is_source_of_truth: bool
    uses_browser_storage: bool
    uses_local_storage: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    creates_route_runtime: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class FloatingWindowLifecycleContract(_CanonicalMixin):
    lifecycle_id: str
    schema_version: str
    window_id: str
    lifecycle_state: FloatingWindowLifecycleState
    availability: FloatingWindowAvailability
    unavailable_reason: str
    deferred_to_pack: str
    error_boundary_reason: str
    runtime_lifecycle_engine: bool
    event_emitted: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class FloatingWindowPlacementIntentContract(_CanonicalMixin):
    placement_id: str
    schema_version: str
    window_id: str
    placement_intent: PlacementIntent
    layer_role: LayerRole
    anchor_surface_id: str
    order_hint: int
    placement_hint: str
    creates_css_layout: bool
    creates_z_index_runtime: bool
    creates_drag_drop: bool
    mutates_runtime: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class WorkspaceStateProjectionSeed(_CanonicalMixin):
    projection_seed_id: str
    schema_version: str
    pack_id: str
    section_id: str
    intake_gate_ref: str
    workspace_state_ref: str
    identity_contract_refs: tuple[str, ...]
    lifecycle_contract_refs: tuple[str, ...]
    placement_intent_refs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    next_pack: str
    projection_only: bool
    creates_ui: bool
    creates_api_server: bool
    creates_event_bus: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    truth_labels: tuple[str, ...]
    non_goals: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class P23AWorkspaceStateFoundationResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    audit_repair_ref: str
    p2_2_d_ref: str
    intake_gate_summary: dict[str, str]
    identity_summary: dict[str, str]
    workspace_state_summary: dict[str, str]
    lifecycle_summary: dict[str, str]
    placement_summary: dict[str, str]
    projection_seed_summary: dict[str, str]
    checkpoint_reads: tuple[P23CheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    truth_labels: tuple[str, ...]
    unavailable_reasons: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    intake_gate: P23SectionIntakeGate
    identity_contracts: tuple[FloatingWindowIdentityContract, ...]
    workspace_state: ShellWorkspaceStateContract
    lifecycle_contracts: tuple[FloatingWindowLifecycleContract, ...]
    placement_intents: tuple[FloatingWindowPlacementIntentContract, ...]
    projection_seed: WorkspaceStateProjectionSeed
    side_effect_proof: P23ASideEffectProof
    next_pack: str
    non_goals: tuple[str, ...]
    result_hash: str


def build_p2_3_a_side_effect_proof() -> P23ASideEffectProof:
    return P23ASideEffectProof()


def _string_bool(value: bool) -> str:
    return str(value).lower()


def _ref(report: str, ref_id: str) -> str:
    return f"{report}:{ref_id}"


def build_p2_3_section_intake_gate() -> P23SectionIntakeGate:
    p2_2_d = build_p2_2_d_local_navigation_integration_tail_result()
    previous_seal_found = (
        p2_2_d.exit_seal.seal_value.value == P2_3_A_REQUIRED_PREVIOUS_SEAL
    )
    previous_readiness_found = (
        p2_2_d.p2_3_readiness.readiness_value.value
        == P2_3_A_REQUIRED_PREVIOUS_READINESS
    )
    audit_repair_found = AUDIT_REPAIR_001_PACK_ID in p2_2_d.dependency_packs
    blocked_reasons: list[str] = []
    if not previous_seal_found:
        blocked_reasons.append("missing_p2_2_d_contract_scope_seal")
    if not previous_readiness_found:
        blocked_reasons.append("missing_ready_for_p2_3_plan")
    if not audit_repair_found:
        blocked_reasons.append("missing_audit_repair_001_gate")
    gate_open = not blocked_reasons
    payload = {
        "gate_id": "p2_3_section_intake_gate",
        "schema_version": P2_3_SECTION_INTAKE_GATE_VERSION,
        "pack_id": P2_3_A_PACK_ID,
        "section_id": P2_3_SECTION_ID,
        "depends_on_packs": P2_3_A_DEPENDENCY_PACKS,
        "required_previous_seal": P2_3_A_REQUIRED_PREVIOUS_SEAL,
        "required_previous_readiness": P2_3_A_REQUIRED_PREVIOUS_READINESS,
        "previous_report_ref": P2_3_A_PREVIOUS_REPORT,
        "previous_commit": P2_3_A_PREVIOUS_COMMIT,
        "previous_seal_found": previous_seal_found,
        "previous_readiness_found": previous_readiness_found,
        "audit_repair_report_ref": (
            f"agent/reports/{AUDIT_REPAIR_001_REPORT_FILENAME}"
        ),
        "audit_repair_required": True,
        "audit_repair_found": audit_repair_found,
        "gate_open": gate_open,
        "blocked_reasons": tuple(blocked_reasons),
        "starts_implementation": False,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.P2_2_DEPENDENCY_SEALED.value,
            TruthBoundaryLabel.NOT_RUNTIME.value,
        ),
        "non_goals": _INTAKE_NON_GOALS,
    }
    gate = P23SectionIntakeGate(**payload, gate_hash=_hash_payload(payload))
    assert_p2_3_section_gate_open_or_blocked_with_reasons(gate)
    assert_p2_3_section_gate_does_not_start_implementation(gate)
    return gate


def build_floating_window_identity_contract(
    *,
    window_kind: FloatingWindowKind = FloatingWindowKind.SURFACE_PANEL,
    owner_surface_id: str = "hq",
    source_surface_id: str = "aurel_cro",
    target_surface_id: str = "hq",
    content_ref: str = "read_model:p2_3_surface_panel_content_ref",
    context_ref: str = "context:p2_3_surface_panel_context_ref",
    title: str = "HQ Surface Panel",
) -> FloatingWindowIdentityContract:
    if owner_surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            "owner surface must be a canonical P2 surface",
            field="owner_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if source_surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            "source surface must be a canonical P2 surface",
            field="source_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if target_surface_id not in CANONICAL_SURFACE_ORDER:
        _reject(
            "target surface must be a canonical P2 surface",
            field="target_surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    payload = {
        "window_id": f"p2_3_a_{window_kind.value.lower()}_{owner_surface_id}",
        "schema_version": P2_3_WINDOW_IDENTITY_VERSION,
        "window_kind": window_kind,
        "owner_scope": OwnerScope.SURFACE_OWNED,
        "owner_surface_id": owner_surface_id,
        "source_surface_id": source_surface_id,
        "target_surface_id": target_surface_id,
        "content_ref": content_ref,
        "context_ref": context_ref,
        "source_truth_boundary": TruthBoundaryLabel.READ_MODEL_ONLY,
        "target_truth_boundary": TruthBoundaryLabel.READ_MODEL_ONLY,
        "title": title,
        "owns_truth": False,
        "grants_authority": False,
        "executes_actions": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_ui": False,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.READ_MODEL_ONLY.value,
            TruthBoundaryLabel.NOT_SOURCE_OF_TRUTH.value,
            TruthBoundaryLabel.NOT_AUTHORITY.value,
        ),
        "non_goals": _IDENTITY_NON_GOALS,
    }
    contract = FloatingWindowIdentityContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_floating_window_identity_uses_canonical_surfaces(contract)
    assert_floating_window_identity_has_refs(contract)
    assert_floating_window_identity_has_no_authority(contract)
    return contract


def build_floating_window_identity_contracts() -> tuple[FloatingWindowIdentityContract, ...]:
    return (
        build_floating_window_identity_contract(),
        build_floating_window_identity_contract(
            window_kind=FloatingWindowKind.INSPECTOR,
            owner_surface_id="ide",
            source_surface_id="hub",
            target_surface_id="ide",
            content_ref="read_model:p2_3_inspector_content_ref",
            context_ref="context:p2_3_inspector_context_ref",
            title="IDE Inspector",
        ),
        build_floating_window_identity_contract(
            window_kind=FloatingWindowKind.SYSTEM_STATUS_PANEL,
            owner_surface_id="settings",
            source_surface_id="system",
            target_surface_id="settings",
            content_ref="read_model:p2_3_system_status_content_ref",
            context_ref="context:p2_3_system_status_context_ref",
            title="System Status Panel",
        ),
    )


def build_shell_workspace_state_contract(
    *,
    identity_contracts: tuple[FloatingWindowIdentityContract, ...] | None = None,
) -> ShellWorkspaceStateContract:
    if identity_contracts is None:
        identity_contracts = build_floating_window_identity_contracts()
    payload = {
        "workspace_state_id": "p2_3_shell_workspace_state_contract",
        "schema_version": P2_3_WORKSPACE_STATE_VERSION,
        "workspace_mode": WorkspaceMode.MULTI_WINDOW_READ_MODEL,
        "active_surface_id": "aurel_cro",
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "floating_window_refs": tuple(c.window_id for c in identity_contracts),
        "workspace_is_surface": False,
        "old_workspace_surface_activated": False,
        "is_source_of_truth": False,
        "uses_browser_storage": False,
        "uses_local_storage": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "creates_route_runtime": False,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.READ_MODEL_ONLY.value,
            TruthBoundaryLabel.NOT_STORAGE.value,
            TruthBoundaryLabel.NOT_RUNTIME.value,
        ),
        "non_goals": _WORKSPACE_NON_GOALS,
    }
    contract = ShellWorkspaceStateContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_workspace_state_preserves_canonical_surfaces(contract)
    assert_workspace_state_is_not_old_workspace_or_storage(contract)
    return contract


def build_floating_window_lifecycle_contract(
    *,
    identity_contract: FloatingWindowIdentityContract | None = None,
    lifecycle_state: FloatingWindowLifecycleState = FloatingWindowLifecycleState.DECLARED,
) -> FloatingWindowLifecycleContract:
    if identity_contract is None:
        identity_contract = build_floating_window_identity_contract()
    availability = FloatingWindowAvailability.CONTRACT_AVAILABLE
    unavailable_reason = ""
    deferred_to_pack = ""
    error_boundary_reason = ""
    if lifecycle_state == FloatingWindowLifecycleState.UNAVAILABLE:
        availability = FloatingWindowAvailability.UNAVAILABLE
        unavailable_reason = "UNAVAILABLE_RUNTIME: no P2.3-A window runtime exists"
    elif lifecycle_state == FloatingWindowLifecycleState.DEFERRED:
        availability = FloatingWindowAvailability.DEFERRED
        deferred_to_pack = P2_3_A_NEXT_PACK
        unavailable_reason = "DEFERRED_TO_P2_3_B: interactive lifecycle deferred"
    elif lifecycle_state == FloatingWindowLifecycleState.ERROR_BOUNDARY:
        availability = FloatingWindowAvailability.ERROR
        error_boundary_reason = "ERROR_BOUNDARY_ONLY: no runtime error is claimed"
        unavailable_reason = "ERROR_BOUNDARY_ONLY: contract state, not runtime failure"
    payload = {
        "lifecycle_id": f"p2_3_lifecycle_{identity_contract.window_id}",
        "schema_version": P2_3_LIFECYCLE_VERSION,
        "window_id": identity_contract.window_id,
        "lifecycle_state": lifecycle_state,
        "availability": availability,
        "unavailable_reason": unavailable_reason,
        "deferred_to_pack": deferred_to_pack,
        "error_boundary_reason": error_boundary_reason,
        "runtime_lifecycle_engine": False,
        "event_emitted": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.READ_MODEL_ONLY.value,
            TruthBoundaryLabel.NOT_RUNTIME.value,
        ),
        "non_goals": _LIFECYCLE_NON_GOALS,
    }
    contract = FloatingWindowLifecycleContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_lifecycle_unavailable_deferred_error_have_reasons(contract)
    assert_lifecycle_has_no_runtime_effects(contract)
    return contract


def build_floating_window_placement_intent_contract(
    *,
    identity_contract: FloatingWindowIdentityContract | None = None,
    placement_intent: PlacementIntent = PlacementIntent.ANCHORED_TO_SURFACE,
    layer_role: LayerRole = LayerRole.FLOATING_PANEL,
    order_hint: int = 10,
) -> FloatingWindowPlacementIntentContract:
    if identity_contract is None:
        identity_contract = build_floating_window_identity_contract()
    payload = {
        "placement_id": f"p2_3_placement_{identity_contract.window_id}",
        "schema_version": P2_3_PLACEMENT_VERSION,
        "window_id": identity_contract.window_id,
        "placement_intent": placement_intent,
        "layer_role": layer_role,
        "anchor_surface_id": identity_contract.owner_surface_id,
        "order_hint": order_hint,
        "placement_hint": (
            "semantic placement hint only; no CSS, z-index, drag/drop, or layout runtime"
        ),
        "creates_css_layout": False,
        "creates_z_index_runtime": False,
        "creates_drag_drop": False,
        "mutates_runtime": False,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.PROJECTION_SEED_ONLY.value,
            TruthBoundaryLabel.NOT_UI.value,
        ),
        "non_goals": _PLACEMENT_NON_GOALS,
    }
    contract = FloatingWindowPlacementIntentContract(
        **payload,
        contract_hash=_hash_payload(payload),
    )
    assert_placement_intent_has_no_layout_runtime(contract)
    return contract


def build_workspace_state_projection_seed(
    *,
    intake_gate: P23SectionIntakeGate | None = None,
    identity_contracts: tuple[FloatingWindowIdentityContract, ...] | None = None,
    workspace_state: ShellWorkspaceStateContract | None = None,
    lifecycle_contracts: tuple[FloatingWindowLifecycleContract, ...] | None = None,
    placement_intents: tuple[FloatingWindowPlacementIntentContract, ...] | None = None,
) -> WorkspaceStateProjectionSeed:
    if intake_gate is None:
        intake_gate = build_p2_3_section_intake_gate()
    if identity_contracts is None:
        identity_contracts = build_floating_window_identity_contracts()
    if workspace_state is None:
        workspace_state = build_shell_workspace_state_contract(
            identity_contracts=identity_contracts,
        )
    if lifecycle_contracts is None:
        lifecycle_contracts = tuple(
            build_floating_window_lifecycle_contract(identity_contract=contract)
            for contract in identity_contracts
        )
    if placement_intents is None:
        placement_intents = tuple(
            build_floating_window_placement_intent_contract(
                identity_contract=contract,
                order_hint=index * 10,
            )
            for index, contract in enumerate(identity_contracts, start=1)
        )
    payload = {
        "projection_seed_id": "p2_3_workspace_state_projection_seed",
        "schema_version": P2_3_PROJECTION_SEED_VERSION,
        "pack_id": P2_3_A_PACK_ID,
        "section_id": P2_3_SECTION_ID,
        "intake_gate_ref": intake_gate.gate_hash,
        "workspace_state_ref": workspace_state.contract_hash,
        "identity_contract_refs": tuple(c.contract_hash for c in identity_contracts),
        "lifecycle_contract_refs": tuple(c.contract_hash for c in lifecycle_contracts),
        "placement_intent_refs": tuple(c.contract_hash for c in placement_intents),
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "next_pack": P2_3_A_NEXT_PACK,
        "projection_only": True,
        "creates_ui": False,
        "creates_api_server": False,
        "creates_event_bus": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.PROJECTION_SEED_ONLY.value,
            TruthBoundaryLabel.NOT_RUNTIME.value,
        ),
        "non_goals": _PROJECTION_NON_GOALS,
    }
    seed = WorkspaceStateProjectionSeed(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_seed_is_contract_only(seed)
    return seed


def _checkpoint_reads() -> tuple[P23CheckpointRead, ...]:
    rows = {
        "P2.3.0": (
            "P2.3 Section Intake Gate",
            "P23SectionIntakeGate",
            "test_p2_3_0_*",
            "CONTRACT_ONLY / P2_2_DEPENDENCY_SEALED",
            "n/a - dependency gate only",
            "Gate verifies prior seal/readiness; it does not start implementation",
        ),
        "P2.3.1": (
            "Floating Window Identity / Ownership",
            "FloatingWindowIdentityContract",
            "test_p2_3_1_*",
            "READ_MODEL_ONLY / NOT_SOURCE_OF_TRUTH / NOT_AUTHORITY",
            "n/a - identity contract only",
            "No runtime window instances, authority, or source-of-truth ownership",
        ),
        "P2.3.2": (
            "Shell Workspace Read-Model State",
            "ShellWorkspaceStateContract",
            "test_p2_3_2_*",
            "READ_MODEL_ONLY / NOT_STORAGE / NOT_RUNTIME",
            "old Workspace surface remains inactive",
            "Workspace is a read-model coordinate frame, not a top-level surface",
        ),
        "P2.3.3": (
            "Lifecycle / Availability Representation",
            "FloatingWindowLifecycleContract",
            "test_p2_3_3_*",
            "CONTRACT_ONLY / READ_MODEL_ONLY / NOT_RUNTIME",
            "runtime lifecycle unavailable by contract",
            "Unavailable/deferred/error states require reasons; no event runtime",
        ),
        "P2.3.4": (
            "Placement / Layering Intent",
            "FloatingWindowPlacementIntentContract",
            "test_p2_3_4_*",
            "PROJECTION_SEED_ONLY / NOT_UI",
            "layout runtime unavailable by contract",
            "Semantic hints only; no CSS, z-index runtime, drag/drop, or UI",
        ),
        "P2.3.5": (
            "Workspace State Projection Seed",
            "WorkspaceStateProjectionSeed, P23AWorkspaceStateFoundationResult",
            "test_p2_3_5_*",
            "PROJECTION_SEED_ONLY / NOT_RUNTIME",
            "API/event/storage runtime unavailable by contract",
            "Bundles P2.3-A contracts and hands off to P2.3-B only",
        ),
    }
    reads: list[P23CheckpointRead] = []
    for checkpoint_id in P2_3_A_PACK_CHECKPOINT_IDS:
        row = rows[checkpoint_id]
        payload = {
            "checkpoint_id": checkpoint_id,
            "canonical_name": row[0],
            "status": P23CheckpointStatus.DONE,
            "evidence": row[1],
            "tests": row[2],
            "truth_label": row[3],
            "unavailable_reason": row[4],
            "limitations": row[5],
        }
        reads.append(P23CheckpointRead(**payload, read_hash=_hash_payload(payload)))
    return tuple(reads)


def build_p2_3_a_workspace_state_foundation_result() -> P23AWorkspaceStateFoundationResult:
    intake_gate = build_p2_3_section_intake_gate()
    identity_contracts = build_floating_window_identity_contracts()
    workspace_state = build_shell_workspace_state_contract(
        identity_contracts=identity_contracts,
    )
    lifecycle_contracts = tuple(
        build_floating_window_lifecycle_contract(identity_contract=contract)
        for contract in identity_contracts
    )
    placement_intents = tuple(
        build_floating_window_placement_intent_contract(
            identity_contract=contract,
            order_hint=index * 10,
        )
        for index, contract in enumerate(identity_contracts, start=1)
    )
    projection_seed = build_workspace_state_projection_seed(
        intake_gate=intake_gate,
        identity_contracts=identity_contracts,
        workspace_state=workspace_state,
        lifecycle_contracts=lifecycle_contracts,
        placement_intents=placement_intents,
    )
    side_effects = build_p2_3_a_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    checkpoint_reads = _checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    payload = {
        "schema_version": P2_3_A_RESULT_VERSION,
        "pack_id": P2_3_A_PACK_ID,
        "section_id": P2_3_SECTION_ID,
        "section_name": P2_3_SECTION_NAME,
        "covered_checkpoints": P2_3_A_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_3_A_DEPENDENCY_PACKS,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "audit_repair_ref": (
            f"agent/reports/{AUDIT_REPAIR_001_REPORT_FILENAME}:"
            f"{AUDIT_REPAIR_001_PACK_ID}"
        ),
        "p2_2_d_ref": f"{P2_3_A_PREVIOUS_REPORT}:{P2_2_D_PACK_ID}",
        "intake_gate_summary": {
            "gate_open": _string_bool(intake_gate.gate_open),
            "required_previous_seal": intake_gate.required_previous_seal,
            "required_previous_readiness": intake_gate.required_previous_readiness,
            "starts_implementation": _string_bool(intake_gate.starts_implementation),
        },
        "identity_summary": {
            "contract_count": str(len(identity_contracts)),
            "owns_truth": "false",
            "grants_authority": "false",
            "canonical_surfaces_only": "true",
        },
        "workspace_state_summary": {
            "workspace_mode": workspace_state.workspace_mode.value,
            "workspace_is_surface": _string_bool(workspace_state.workspace_is_surface),
            "uses_storage": "false",
            "old_workspace_surface_activated": _string_bool(
                workspace_state.old_workspace_surface_activated
            ),
        },
        "lifecycle_summary": {
            "contract_count": str(len(lifecycle_contracts)),
            "runtime_lifecycle_engine": "false",
            "event_emitted": "false",
        },
        "placement_summary": {
            "intent_count": str(len(placement_intents)),
            "creates_css_layout": "false",
            "creates_z_index_runtime": "false",
        },
        "projection_seed_summary": {
            "projection_seed_id": projection_seed.projection_seed_id,
            "projection_only": _string_bool(projection_seed.projection_only),
            "next_pack": projection_seed.next_pack,
        },
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": (
            TruthBoundaryLabel.CONTRACT_ONLY.value,
            TruthBoundaryLabel.READ_MODEL_ONLY.value,
            TruthBoundaryLabel.PROJECTION_SEED_ONLY.value,
            TruthBoundaryLabel.NOT_SOURCE_OF_TRUTH.value,
            TruthBoundaryLabel.NOT_UI.value,
            TruthBoundaryLabel.NOT_RUNTIME.value,
            TruthBoundaryLabel.NOT_STORAGE.value,
            TruthBoundaryLabel.NOT_LIVE.value,
            TruthBoundaryLabel.NOT_TRACE_VERIFIED.value,
        ),
        "unavailable_reasons": (
            "UNAVAILABLE_UI: no P2.3-A product UI or draggable window runtime",
            "UNAVAILABLE_STORAGE: no browser/local storage runtime",
            "UNAVAILABLE_API_EVENT_RUNTIME: no API server or event bus",
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "intake_gate": intake_gate,
        "identity_contracts": identity_contracts,
        "workspace_state": workspace_state,
        "lifecycle_contracts": lifecycle_contracts,
        "placement_intents": placement_intents,
        "projection_seed": projection_seed,
        "side_effect_proof": side_effects,
        "next_pack": P2_3_A_NEXT_PACK,
        "non_goals": _PROJECTION_NON_GOALS,
    }
    result = P23AWorkspaceStateFoundationResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_3_a_depends_on_audit_repair_001_and_p2_2_d(result)
    assert_p2_3_a_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_3_a_result(
    result: P23AWorkspaceStateFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_3_a_workspace_state_foundation_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_3_section_gate_open_or_blocked_with_reasons(
    gate: P23SectionIntakeGate,
) -> None:
    if gate.gate_open and gate.blocked_reasons:
        _reject(
            "open P2.3 gate must not carry blocked reasons",
            field="blocked_reasons",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not gate.gate_open and not gate.blocked_reasons:
        _reject(
            "blocked P2.3 gate must carry blocked reasons",
            field="blocked_reasons",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_3_section_gate_does_not_start_implementation(
    gate: P23SectionIntakeGate,
) -> None:
    if gate.starts_implementation:
        _reject(
            "P2.3-A intake gate must not start runtime implementation",
            field="starts_implementation",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_floating_window_identity_uses_canonical_surfaces(
    contract: FloatingWindowIdentityContract,
) -> None:
    for field in ("owner_surface_id", "source_surface_id", "target_surface_id"):
        if getattr(contract, field) not in CANONICAL_SURFACE_ORDER:
            _reject(
                "floating window identity must use canonical P2 surface ids",
                field=field,
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_floating_window_identity_has_refs(
    contract: FloatingWindowIdentityContract,
) -> None:
    if not contract.content_ref or not contract.context_ref:
        _reject(
            "floating window identity requires content and context refs",
            field="content_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_floating_window_identity_has_no_authority(
    contract: FloatingWindowIdentityContract,
) -> None:
    if (
        contract.owns_truth
        or contract.grants_authority
        or contract.executes_actions
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
        or contract.creates_ui
    ):
        _reject(
            "floating window identity must not own truth, grant authority, execute, or mutate",
            field="owns_truth",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_workspace_state_preserves_canonical_surfaces(
    contract: ShellWorkspaceStateContract,
) -> None:
    if contract.canonical_surface_ids != CANONICAL_SURFACE_ORDER:
        _reject(
            "workspace state must preserve canonical surface order",
            field="canonical_surface_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_workspace_state_is_not_old_workspace_or_storage(
    contract: ShellWorkspaceStateContract,
) -> None:
    if (
        contract.workspace_is_surface
        or contract.old_workspace_surface_activated
        or contract.is_source_of_truth
        or contract.uses_browser_storage
        or contract.uses_local_storage
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
        or contract.creates_route_runtime
    ):
        _reject(
            "workspace state is read-model only, not old Workspace/storage/runtime",
            field="workspace_is_surface",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_lifecycle_unavailable_deferred_error_have_reasons(
    contract: FloatingWindowLifecycleContract,
) -> None:
    if (
        contract.lifecycle_state == FloatingWindowLifecycleState.UNAVAILABLE
        and not contract.unavailable_reason
    ):
        _reject(
            "unavailable lifecycle state requires reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        contract.lifecycle_state == FloatingWindowLifecycleState.DEFERRED
        and (not contract.unavailable_reason or not contract.deferred_to_pack)
    ):
        _reject(
            "deferred lifecycle state requires reason and deferred target",
            field="deferred_to_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        contract.lifecycle_state == FloatingWindowLifecycleState.ERROR_BOUNDARY
        and (not contract.unavailable_reason or not contract.error_boundary_reason)
    ):
        _reject(
            "error boundary lifecycle state requires explicit reason",
            field="error_boundary_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_lifecycle_has_no_runtime_effects(
    contract: FloatingWindowLifecycleContract,
) -> None:
    if (
        contract.runtime_lifecycle_engine
        or contract.event_emitted
        or contract.mutates_runtime
        or contract.writes_memory
        or contract.writes_trace
    ):
        _reject(
            "lifecycle contract must not create runtime lifecycle effects",
            field="runtime_lifecycle_engine",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_placement_intent_has_no_layout_runtime(
    contract: FloatingWindowPlacementIntentContract,
) -> None:
    if (
        contract.creates_css_layout
        or contract.creates_z_index_runtime
        or contract.creates_drag_drop
        or contract.mutates_runtime
    ):
        _reject(
            "placement intent must not create CSS/layout/z-index runtime",
            field="creates_css_layout",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_projection_seed_is_contract_only(seed: WorkspaceStateProjectionSeed) -> None:
    if (
        not seed.projection_only
        or seed.creates_ui
        or seed.creates_api_server
        or seed.creates_event_bus
        or seed.mutates_runtime
        or seed.writes_memory
        or seed.writes_trace
    ):
        _reject(
            "workspace projection seed must remain projection-only",
            field="projection_only",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_3_a_side_effects_all_false(proof: P23ASideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                "P2.3-A side-effect proof fields must all be false",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_p2_3_a_depends_on_audit_repair_001_and_p2_2_d(
    result: P23AWorkspaceStateFoundationResult,
) -> None:
    if AUDIT_REPAIR_001_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-A must depend on AUDIT-REPAIR-001",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_D_PACK_ID not in result.dependency_packs:
        _reject(
            "P2.3-A must depend on P2.2-D",
            field="dependency_packs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if AUDIT_REPAIR_001_REPORT_FILENAME not in result.audit_repair_ref:
        _reject(
            "P2.3-A must cite AUDIT-REPAIR-001 report",
            field="audit_repair_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if P2_2_D_REPORT_FILENAME not in result.p2_2_d_ref:
        _reject(
            "P2.3-A must cite P2.2-D report",
            field="p2_2_d_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
