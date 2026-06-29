"""P2.5-D cross-surface handoff section projection and contract-scope seal.

Contract-only section aggregation over P2.5-A/B/C. This module creates a
deterministic P2.5 read-model projection, explicit read-only or UNAVAILABLE
binding status, readiness audit, contract-scope demo, and section seal. It
does not create projection UI, cross-surface UI, preview UI, explanation panel
UI, confirmation modal, operator confirmation UI, live Shell/TUI binding,
API/event bridge, handoff execution, surface switching, route execution,
approval activation, permission enforcement, storage, memory/trace writes,
product behavior, release scope, or runtime mutation.
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
from .cross_surface_handoff import (
    P2_5_A_PACK_ID,
    P2_5_A_REPORT_PATH,
    P25ACrossSurfaceHandoffResult,
    build_p2_5_a_fixture_handoff_pipeline,
)
from .cross_surface_handoff_context import (
    P2_5_A_COMMIT_REF,
    P2_5_B_PACK_ID,
    P2_5_B_REPORT_PATH,
    P25BHandoffContextResult,
    build_p2_5_b_handoff_context_result,
)
from .cross_surface_handoff_preview import (
    P2_5_B_COMMIT_REF,
    P2_5_C_PACK_ID,
    P2_5_C_REPORT_PATH,
    P25CHandoffPreviewResult,
    build_p2_5_c_handoff_preview_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_5_D_PACK_ID = "P2.5-D"
P2_5_D_SECTION_ID = "P2.5"
P2_5_D_OFFICIAL_SECTION_NAME = "Cross-Surface Handoff"
P2_5_D_DEPENDENCY_PACK = P2_5_C_PACK_ID
P2_5_D_NEXT_CANDIDATE = "P2.6-A"
P2_5_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.5.16",
    "P2.5.17",
    "P2.5.18",
    "P2.5.19",
    "P2.5.20",
)
P2_5_D_REPORT_FILENAME = "P2_5_D_HANDOFF_SECTION_SEAL.md"
P2_5_D_REPORT_PATH = f"agent/reports/{P2_5_D_REPORT_FILENAME}"

P2_5_C_COMMIT_REF = "790f93089fb49e9ef524de3ac2202aebf4e746ee"
P2_5_C_REPORT_HASH_COMMIT_REF = "04060b9"

HANDOFF_SECTION_BINDING_UNAVAILABLE_REASON = (
    "P2.5-D seals handoff contracts only. No compatible live Shell/TUI handoff "
    "binding, API/event bridge, projection UI, or handoff execution surface "
    "exists in this repo scope."
)

P2_5_D_GATE_VERSION = "p2_5_d_handoff_section_gate.v1"
P2_5_D_INVENTORY_VERSION = "p2_5_d_handoff_contract_inventory.v1"
P2_5_D_PACK_ROLLUP_VERSION = "p2_5_d_handoff_pack_rollup.v1"
P2_5_D_CAPABILITY_VERSION = "p2_5_d_handoff_section_capability.v1"
P2_5_D_UNAVAILABLE_CAPABILITY_VERSION = "p2_5_d_handoff_unavailable_capability.v1"
P2_5_D_BINDING_VERSION = "p2_5_d_handoff_binding_status.v1"
P2_5_D_AUDIT_FINDING_VERSION = "p2_5_d_handoff_audit_finding.v1"
P2_5_D_READINESS_AUDIT_VERSION = "p2_5_d_handoff_readiness_audit.v1"
P2_5_D_SECTION_SEAL_VERSION = "p2_5_d_handoff_section_seal.v1"
P2_5_D_DEMO_VERSION = "p2_5_d_handoff_contract_scope_demo.v1"
P2_5_D_PROJECTION_VERSION = "p2_5_d_handoff_section_projection.v1"
P2_5_D_DOCS_SYNC_VERSION = "p2_5_d_handoff_docs_state_report_sync.v1"
P2_5_D_RESULT_VERSION = "p2_5_d_handoff_section_result.v1"

_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_projection_ui",
    "no_live_binding",
    "no_api_event_bridge",
    "no_source_of_truth_store",
    "no_product_behavior",
    "no_live_claim",
    "no_trace_verified_claim",
    "no_release_scope_claim",
    "no_handoff_execution",
    "no_p2_6_implementation",
)
_BINDING_NON_GOALS: tuple[str, ...] = (
    "no_projection_ui",
    "no_cross_surface_ui",
    "no_preview_ui",
    "no_live_shell_binding",
    "no_live_tui_binding",
    "no_api_event_bridge",
    "no_handoff_execution",
    "no_route_execution",
    "no_runtime_mutation",
)
_AUDIT_NON_GOALS: tuple[str, ...] = (
    "no_authority_grant",
    "no_release_grant",
    "no_product_readiness",
    "no_trace_verification",
)
_SEAL_NON_GOALS: tuple[str, ...] = (
    "no_release_seal",
    "no_product_completion",
    "no_live_behavior",
    "no_trace_verification",
    "no_p2_6_implementation",
)


class CrossSurfaceHandoffSectionGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class CrossSurfaceHandoffPackStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class CrossSurfaceHandoffCapabilityStatus(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class CrossSurfaceHandoffBindingMode(str, Enum):
    READ_ONLY_CONTRACT_RENDER = "READ_ONLY_CONTRACT_RENDER"
    UNAVAILABLE = "UNAVAILABLE"
    DEV_FIXTURE_READ_MODEL = "DEV_FIXTURE_READ_MODEL"
    NOT_BOUND = "NOT_BOUND"


class CrossSurfaceHandoffSectionSealStatus(str, Enum):
    SEALED_CONTRACT_SCOPE = "SEALED_CONTRACT_SCOPE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class CrossSurfaceHandoffAuditFindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"
    ERROR = "ERROR"


class CrossSurfaceHandoffAuditFindingKind(str, Enum):
    FAKE_LIVE_CLAIM = "FAKE_LIVE_CLAIM"
    FAKE_TRACE_VERIFIED_CLAIM = "FAKE_TRACE_VERIFIED_CLAIM"
    FAKE_PRODUCT_BEHAVIOR_CLAIM = "FAKE_PRODUCT_BEHAVIOR_CLAIM"
    FAKE_RELEASE_SCOPE_CLAIM = "FAKE_RELEASE_SCOPE_CLAIM"
    FAKE_LIVE_HANDOFF_CLAIM = "FAKE_LIVE_HANDOFF_CLAIM"
    FAKE_LIVE_BINDING_CLAIM = "FAKE_LIVE_BINDING_CLAIM"
    FAKE_UI_PROJECTION_CLAIM = "FAKE_UI_PROJECTION_CLAIM"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNAVAILABLE_CAPABILITY = "UNAVAILABLE_CAPABILITY"
    CONTRACT_SCOPE_ONLY = "CONTRACT_SCOPE_ONLY"


class CrossSurfaceHandoffSectionTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    SECTION_SEAL_ONLY = "SECTION_SEAL_ONLY"
    CONTRACT_SCOPE_DEMO_ONLY = "CONTRACT_SCOPE_DEMO_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_UI = "NOT_UI"
    NOT_PROJECTION_UI = "NOT_PROJECTION_UI"
    NOT_LIVE_BINDING = "NOT_LIVE_BINDING"
    NOT_SHELL_EXECUTION_BINDING = "NOT_SHELL_EXECUTION_BINDING"
    NOT_TUI_EXECUTION_BINDING = "NOT_TUI_EXECUTION_BINDING"
    NOT_API_EVENT_BRIDGE = "NOT_API_EVENT_BRIDGE"
    NOT_HANDOFF_EXECUTION = "NOT_HANDOFF_EXECUTION"
    NOT_SURFACE_SWITCH = "NOT_SURFACE_SWITCH"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_REAL_OPERATOR_CONSENT = "NOT_REAL_OPERATOR_CONSENT"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_RUNTIME_MUTATION = "NOT_RUNTIME_MUTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    READINESS_AUDIT_ONLY = "READINESS_AUDIT_ONLY"
    NO_FAKE_HANDOFF_GATE = "NO_FAKE_HANDOFF_GATE"
    SEALED_CONTRACT_SCOPE = "SEALED_CONTRACT_SCOPE"
    STATE_MIRROR_ONLY = "STATE_MIRROR_ONLY"


@dataclass(frozen=True)
class P25DSideEffectProof(_CanonicalMixin):
    projection_ui_created: bool = False
    cross_surface_ui_created: bool = False
    preview_ui_created: bool = False
    explanation_panel_ui_created: bool = False
    confirmation_modal_created: bool = False
    operator_confirmation_ui_created: bool = False
    live_shell_binding_created: bool = False
    live_tui_binding_created: bool = False
    api_event_bridge_created: bool = False
    real_operator_consent_recorded: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    authorization_created: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    mneme_integration_created: bool = False
    handoff_execution_created: bool = False
    surface_runtime_switch_created: bool = False
    active_navigation_mutation_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
    api_server_created: bool = False
    http_routes_created: bool = False
    event_bus_created: bool = False
    runtime_events_emitted: bool = False
    memory_written: bool = False
    trace_written: bool = False
    storage_written: bool = False
    runtime_mutated: bool = False
    source_of_truth_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class CrossSurfaceHandoffSectionGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_preview_result_ref: str
    dependency_no_confirmation_boundary_ref: str
    dependency_no_execution_boundary_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: CrossSurfaceHandoffSectionGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffContractInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    included_packs: tuple[str, ...]
    contract_refs: tuple[str, ...]
    report_refs: tuple[str, ...]
    validation_refs: tuple[str, ...]
    commit_refs: tuple[str, ...]
    missing_contracts: tuple[str, ...]
    duplicates_source_of_truth: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffPackRollup(_CanonicalMixin):
    rollup_id: str
    schema_version: str
    section_id: str
    pack_id: str
    pack_name: str
    pack_status: CrossSurfaceHandoffPackStatus
    covered_checkpoints: tuple[str, ...]
    report_ref: str
    commit_ref: str
    validation_ref: str
    final_git_status_ref: str
    partial_or_unavailable_reason: str
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffSectionCapability(_CanonicalMixin):
    capability_id: str
    schema_version: str
    capability_name: str
    capability_status: CrossSurfaceHandoffCapabilityStatus
    covered_pack: str
    covered_checkpoints: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    truth_label: str
    limitations: tuple[str, ...]
    capability_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffUnavailableCapability(_CanonicalMixin):
    unavailable_id: str
    schema_version: str
    capability_name: str
    reason: str
    future_pack_or_section: str
    requires_ui_later: bool
    requires_route_runtime_later: bool
    requires_permission_later: bool
    requires_approval_later: bool
    requires_api_event_bridge_later: bool
    truth_label: str
    limitations: tuple[str, ...]
    unavailable_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffBindingStatus(_CanonicalMixin):
    binding_status_id: str
    schema_version: str
    section_id: str
    binding_mode: CrossSurfaceHandoffBindingMode
    read_only_render_available: bool
    live_shell_binding_created: bool
    live_tui_binding_created: bool
    api_event_bridge_created: bool
    handoff_execution_bound: bool
    route_execution_bound: bool
    unavailable_capabilities: tuple[str, ...]
    reason: str
    truth_label: str
    limitations: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffAuditFinding(_CanonicalMixin):
    finding_id: str
    schema_version: str
    severity: CrossSurfaceHandoffAuditFindingSeverity
    finding_kind: CrossSurfaceHandoffAuditFindingKind
    message: str
    blocked_claim: str
    evidence_ref: str
    truth_label: str
    limitations: tuple[str, ...]
    finding_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffReadinessAudit(_CanonicalMixin):
    audit_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    findings: tuple[CrossSurfaceHandoffAuditFinding, ...]
    blocks_live_claim: bool
    blocks_trace_verified_claim: bool
    blocks_product_behavior_claim: bool
    blocks_release_scope_claim: bool
    blocks_live_handoff_claim: bool
    blocks_live_binding_claim: bool
    blocks_ui_projection_claim: bool
    audit_passed_for_contract_scope: bool
    audit_passed_for_release_scope: bool
    truth_label: str
    limitations: tuple[str, ...]
    audit_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffSectionSeal(_CanonicalMixin):
    seal_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    seal_status: CrossSurfaceHandoffSectionSealStatus
    covered_checkpoints: tuple[str, ...]
    covered_packs: tuple[str, ...]
    contract_inventory_ref: str
    section_projection_ref: str
    binding_status_ref: str
    readiness_audit_ref: str
    contract_scope_demo_ref: str
    sealed_contract_scope: bool
    sealed_release_scope: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_product_behavior: bool
    claims_release_scope: bool
    truth_label: str
    limitations: tuple[str, ...]
    seal_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffContractScopeDemo(_CanonicalMixin):
    demo_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    demo_name: str
    uses_contract_inventory: bool
    uses_section_projection: bool
    uses_binding_status: bool
    uses_readiness_audit: bool
    uses_section_seal: bool
    executes_handoff: bool
    switches_surface: bool
    executes_route: bool
    creates_ui: bool
    creates_live_binding: bool
    writes_memory: bool
    writes_trace: bool
    writes_storage: bool
    mutates_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    demo_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffSectionProjection(_CanonicalMixin):
    projection_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    contract_inventory: CrossSurfaceHandoffContractInventory
    pack_rollup: tuple[CrossSurfaceHandoffPackRollup, ...]
    capabilities: tuple[CrossSurfaceHandoffSectionCapability, ...]
    unavailable_capabilities: tuple[CrossSurfaceHandoffUnavailableCapability, ...]
    binding_status_ref: str
    readiness_audit_ref: str
    section_seal_ref: str
    is_ui: bool
    is_live_binding: bool
    is_api_event_bridge: bool
    is_source_of_truth: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_product_behavior: bool
    claims_release_scope: bool
    truth_label: str
    limitations: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class CrossSurfaceHandoffDocsStateReportSync(_CanonicalMixin):
    sync_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    report_created: bool
    report_indexed: bool
    active_task_updated: bool
    roadmap_mirror_updated: bool
    state_updated: bool
    tests_updated: bool
    duplicate_agent_state_created: bool
    product_release_claim_created: bool
    next_candidate: str
    next_candidate_requires_canon_read: bool
    truth_label: str
    limitations: tuple[str, ...]
    sync_hash: str


@dataclass(frozen=True)
class P25DHandoffSectionResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    section_gate: CrossSurfaceHandoffSectionGate
    contract_inventory: CrossSurfaceHandoffContractInventory
    pack_rollup: tuple[CrossSurfaceHandoffPackRollup, ...]
    section_projection: CrossSurfaceHandoffSectionProjection
    binding_status: CrossSurfaceHandoffBindingStatus
    docs_state_report_sync: CrossSurfaceHandoffDocsStateReportSync
    readiness_audit: CrossSurfaceHandoffReadinessAudit
    section_seal: CrossSurfaceHandoffSectionSeal
    contract_scope_demo: CrossSurfaceHandoffContractScopeDemo
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P25DSideEffectProof
    canonical_surface_ids: tuple[str, ...]
    next_candidate: str
    next_candidate_requires_canon_read: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _preview_result_ref(preview: P25CHandoffPreviewResult) -> str:
    return (
        f"{preview.preview_result.preview_result_id}:"
        f"{preview.preview_result.preview_result_id}"
    )


def _no_confirmation_boundary_ref(preview: P25CHandoffPreviewResult) -> str:
    pr = preview.preview_result
    return (
        f"{pr.preview_result_id}:no_confirmation="
        f"{str(pr.no_confirmation_boundary_active).lower()}"
    )


def _no_execution_boundary_ref(preview: P25CHandoffPreviewResult) -> str:
    pr = preview.preview_result
    return (
        f"{pr.preview_result_id}:no_execution="
        f"{str(pr.no_execution_boundary_active).lower()}"
    )


def build_cross_surface_handoff_section_gate(
    preview_result: P25CHandoffPreviewResult | None = None,
) -> CrossSurfaceHandoffSectionGate:
    if preview_result is None:
        preview_result = build_p2_5_c_handoff_preview_result()
    assert_p2_5_c_preview_result_available(preview_result)
    payload = {
        "gate_id": "p2_5_d_handoff_section_gate",
        "schema_version": P2_5_D_GATE_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "official_section_name": P2_5_D_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_5_D_DEPENDENCY_PACK,
        "dependency_report_ref": P2_5_C_REPORT_PATH,
        "dependency_commit_ref": P2_5_C_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.5-C",
        "dependency_preview_result_ref": _preview_result_ref(preview_result),
        "dependency_no_confirmation_boundary_ref": _no_confirmation_boundary_ref(
            preview_result
        ),
        "dependency_no_execution_boundary_ref": _no_execution_boundary_ref(
            preview_result
        ),
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": CrossSurfaceHandoffSectionGateStatus.READY,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.CONTRACT_ONLY.value,
        "limitations": (
            "OMNI evidence is ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create projection UI or handoff execution",
        ),
    }
    gate = CrossSurfaceHandoffSectionGate(**payload, gate_hash=_hash_payload(payload))
    assert_section_gate_depends_on_p2_5_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_cross_surface_handoff_contract_inventory(
    foundation: P25ACrossSurfaceHandoffResult | None = None,
    context_result: P25BHandoffContextResult | None = None,
    preview_result: P25CHandoffPreviewResult | None = None,
) -> CrossSurfaceHandoffContractInventory:
    if foundation is None:
        foundation = build_p2_5_a_fixture_handoff_pipeline()
    if context_result is None:
        context_result = build_p2_5_b_handoff_context_result()
    if preview_result is None:
        preview_result = build_p2_5_c_handoff_preview_result()
    payload = {
        "inventory_id": "p2_5_d_handoff_contract_inventory",
        "schema_version": P2_5_D_INVENTORY_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "official_section_name": P2_5_D_OFFICIAL_SECTION_NAME,
        "included_packs": (P2_5_A_PACK_ID, P2_5_B_PACK_ID, P2_5_C_PACK_ID, P2_5_D_PACK_ID),
        "contract_refs": (
            "CrossSurfaceHandoffGate",
            "CrossSurfaceHandoffId",
            "CrossSurfaceHandoffIntent",
            "CrossSurfaceHandoffContextSnapshot",
            "CrossSurfaceHandoffAvailability",
            "CrossSurfaceHandoffPreviewGate",
            "CrossSurfaceHandoffPreviewResult",
            "CrossSurfaceHandoffSectionGate",
            "CrossSurfaceHandoffSectionProjection",
            "CrossSurfaceHandoffBindingStatus",
            "CrossSurfaceHandoffSectionSeal",
        ),
        "report_refs": (
            P2_5_A_REPORT_PATH,
            P2_5_B_REPORT_PATH,
            P2_5_C_REPORT_PATH,
            P2_5_D_REPORT_PATH,
        ),
        "validation_refs": (
            "agent/TESTS.md#P2.5-A",
            "agent/TESTS.md#P2.5-B",
            "agent/TESTS.md#P2.5-C",
            "agent/TESTS.md#P2.5-D",
        ),
        "commit_refs": (
            P2_5_A_COMMIT_REF,
            P2_5_B_COMMIT_REF,
            P2_5_C_COMMIT_REF,
            "",
        ),
        "missing_contracts": (),
        "duplicates_source_of_truth": False,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.CONTRACT_ONLY.value,
        "limitations": (
            "Inventory references P2.5-A/B/C outputs; it does not duplicate them",
            f"foundation_ref={foundation.foundation_result}",
            f"context_ref={context_result.context_result.context_result_id}",
            f"preview_ref={preview_result.preview_result.preview_result_id}",
        ),
    }
    inventory = CrossSurfaceHandoffContractInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    if inventory.duplicates_source_of_truth or inventory.missing_contracts:
        _reject(
            "P2.5-D contract inventory must not duplicate or miss known contracts",
            field="duplicates_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    return inventory


def build_cross_surface_handoff_pack_rollup() -> tuple[CrossSurfaceHandoffPackRollup, ...]:
    rows = (
        (
            P2_5_A_PACK_ID,
            "Cross-Surface Handoff Foundation",
            ("P2.5.0", "P2.5.1", "P2.5.2", "P2.5.3", "P2.5.4", "P2.5.5"),
            P2_5_A_REPORT_PATH,
            P2_5_A_COMMIT_REF,
            "agent/TESTS.md#P2.5-A",
            "clean",
            "",
        ),
        (
            P2_5_B_PACK_ID,
            "Handoff Context / Continuity / Conflict / Availability Read Model",
            ("P2.5.6", "P2.5.7", "P2.5.8", "P2.5.9", "P2.5.10"),
            P2_5_B_REPORT_PATH,
            P2_5_B_COMMIT_REF,
            "agent/TESTS.md#P2.5-B",
            "clean",
            "",
        ),
        (
            P2_5_C_PACK_ID,
            "Handoff Preview / Explanation / Operator Confirmation Boundary",
            ("P2.5.11", "P2.5.12", "P2.5.13", "P2.5.14", "P2.5.15"),
            P2_5_C_REPORT_PATH,
            P2_5_C_COMMIT_REF,
            "agent/TESTS.md#P2.5-C",
            "clean",
            "",
        ),
        (
            P2_5_D_PACK_ID,
            "Handoff Projection / Binding / Docs / Section Seal",
            P2_5_D_PACK_CHECKPOINT_IDS,
            P2_5_D_REPORT_PATH,
            "",
            "agent/TESTS.md#P2.5-D",
            "pending_commit",
            "",
        ),
    )
    rollups: list[CrossSurfaceHandoffPackRollup] = []
    for pack_id, name, checkpoints, report, commit, validation, git_status, reason in rows:
        payload = {
            "rollup_id": f"p2_5_rollup:{pack_id}",
            "schema_version": P2_5_D_PACK_ROLLUP_VERSION,
            "section_id": P2_5_D_SECTION_ID,
            "pack_id": pack_id,
            "pack_name": name,
            "pack_status": CrossSurfaceHandoffPackStatus.DONE,
            "covered_checkpoints": checkpoints,
            "report_ref": report,
            "commit_ref": commit,
            "validation_ref": validation,
            "final_git_status_ref": git_status,
            "partial_or_unavailable_reason": reason,
            "truth_label": CrossSurfaceHandoffSectionTruthBoundary.REPORT_ONLY.value,
            "limitations": (
                "Rollup is report/evidence reference only",
                "Rollup is not a source-of-truth store",
            ),
        }
        rollups.append(
            CrossSurfaceHandoffPackRollup(**payload, rollup_hash=_hash_payload(payload))
        )
    return tuple(rollups)


def build_cross_surface_handoff_section_capabilities() -> (
    tuple[CrossSurfaceHandoffSectionCapability, ...]
):
    rows = (
        (
            "handoff_foundation",
            "cross-surface handoff foundation",
            CrossSurfaceHandoffCapabilityStatus.CONTRACT_ONLY,
            P2_5_A_PACK_ID,
            ("P2.5.0", "P2.5.5"),
            (P2_5_A_REPORT_PATH,),
        ),
        (
            "handoff_context_read_model",
            "handoff context/availability read model",
            CrossSurfaceHandoffCapabilityStatus.READ_MODEL_ONLY,
            P2_5_B_PACK_ID,
            ("P2.5.6", "P2.5.10"),
            (P2_5_B_REPORT_PATH,),
        ),
        (
            "handoff_preview_boundary",
            "handoff preview/confirmation boundary",
            CrossSurfaceHandoffCapabilityStatus.READ_MODEL_ONLY,
            P2_5_C_PACK_ID,
            ("P2.5.11", "P2.5.15"),
            (P2_5_C_REPORT_PATH,),
        ),
        (
            "section_projection_read_model",
            "section projection/read model",
            CrossSurfaceHandoffCapabilityStatus.READ_MODEL_ONLY,
            P2_5_D_PACK_ID,
            ("P2.5.16", "P2.5.16"),
            (P2_5_D_REPORT_PATH,),
        ),
        (
            "section_readiness_audit",
            "section readiness audit",
            CrossSurfaceHandoffCapabilityStatus.CONTRACT_ONLY,
            P2_5_D_PACK_ID,
            ("P2.5.19", "P2.5.19"),
            (P2_5_D_REPORT_PATH,),
        ),
        (
            "section_contract_scope_seal",
            "section contract-scope seal",
            CrossSurfaceHandoffCapabilityStatus.CONTRACT_ONLY,
            P2_5_D_PACK_ID,
            ("P2.5.20", "P2.5.20"),
            (P2_5_D_REPORT_PATH,),
        ),
    )
    capabilities: list[CrossSurfaceHandoffSectionCapability] = []
    for cap_id, name, status, pack, checkpoints, evidence in rows:
        payload = {
            "capability_id": cap_id,
            "schema_version": P2_5_D_CAPABILITY_VERSION,
            "capability_name": name,
            "capability_status": status,
            "covered_pack": pack,
            "covered_checkpoints": checkpoints,
            "evidence_refs": evidence,
            "truth_label": CrossSurfaceHandoffSectionTruthBoundary.READ_MODEL_ONLY.value,
            "limitations": (
                "contract/read-model capability only",
                "not product behavior",
            ),
        }
        capabilities.append(
            CrossSurfaceHandoffSectionCapability(
                **payload,
                capability_hash=_hash_payload(payload),
            )
        )
    return tuple(capabilities)


def build_cross_surface_handoff_unavailable_capabilities() -> (
    tuple[CrossSurfaceHandoffUnavailableCapability, ...]
):
    rows = (
        ("actual cross-surface handoff execution", "future handoff execution section", True, True, True, True, True),
        ("live surface switching", "future route/runtime section", True, True, False, False, False),
        ("route execution", "future route/runtime section", False, True, False, False, False),
        ("route handler invocation", "future route/runtime section", False, True, False, False, False),
        ("route runtime", "future route/runtime section", False, True, False, False, False),
        ("projection UI", "future UI section", True, False, False, False, False),
        ("cross-surface UI", "future UI section", True, False, False, False, False),
        ("preview UI", "future UI section", True, False, False, False, False),
        ("explanation panel UI", "future UI section", True, False, False, False, False),
        ("confirmation modal", "future UI section", True, False, False, False, False),
        ("operator confirmation UI", "future UI section", True, False, False, False, False),
        ("real operator consent recording", "future consent section", True, False, True, True, False),
        ("approval activation", "future approval section", False, False, True, True, False),
        ("authorization", "future authorization section", False, False, True, False, False),
        ("permission enforcement", "future Custos section", False, False, True, False, False),
        ("Custos integration", "future Custos section", False, False, True, False, False),
        ("Mneme integration", "future Mneme section", False, False, False, False, False),
        ("workflow/tool dispatch", "future execution section", False, True, False, False, False),
        ("API/event bridge", "future projection/runtime section", False, False, False, False, True),
        ("Shell execution binding", "future Shell binding section", False, False, False, False, False),
        ("TUI execution binding", "future TUI binding section", False, False, False, False, False),
        ("storage write", "future storage section", False, False, False, False, False),
        ("memory write", "future memory section", False, False, False, False, False),
        ("trace write", "future trace section", False, False, False, False, False),
        ("runtime mutation", "future runtime section", False, True, False, False, False),
        ("LIVE handoff", "future live section", True, True, False, False, False),
        ("TRACE_VERIFIED handoff", "future trace verification section", False, False, False, False, False),
        ("product behavior", "future product section", True, False, False, False, False),
        ("release scope", "future release section", False, False, False, False, False),
    )
    capabilities: list[CrossSurfaceHandoffUnavailableCapability] = []
    for idx, (
        name,
        future,
        ui,
        route,
        perm,
        approval,
        api,
    ) in enumerate(rows):
        payload = {
            "unavailable_id": f"p2_5_d_unavailable:{idx}",
            "schema_version": P2_5_D_UNAVAILABLE_CAPABILITY_VERSION,
            "capability_name": name,
            "reason": HANDOFF_SECTION_BINDING_UNAVAILABLE_REASON,
            "future_pack_or_section": future,
            "requires_ui_later": ui,
            "requires_route_runtime_later": route,
            "requires_permission_later": perm,
            "requires_approval_later": approval,
            "requires_api_event_bridge_later": api,
            "truth_label": CrossSurfaceHandoffSectionTruthBoundary.UNAVAILABLE.value,
            "limitations": (
                "unavailable in P2.5-D",
                "must not be claimed as product behavior",
            ),
        }
        capabilities.append(
            CrossSurfaceHandoffUnavailableCapability(
                **payload,
                unavailable_hash=_hash_payload(payload),
            )
        )
    return tuple(capabilities)


def build_cross_surface_handoff_binding_status(
    *,
    binding_mode: CrossSurfaceHandoffBindingMode = (
        CrossSurfaceHandoffBindingMode.READ_ONLY_CONTRACT_RENDER
    ),
) -> CrossSurfaceHandoffBindingStatus:
    unavailable_names = tuple(
        cap.capability_name
        for cap in build_cross_surface_handoff_unavailable_capabilities()
    )
    read_only = binding_mode == CrossSurfaceHandoffBindingMode.READ_ONLY_CONTRACT_RENDER
    payload = {
        "binding_status_id": "p2_5_d_handoff_binding_status",
        "schema_version": P2_5_D_BINDING_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "binding_mode": binding_mode,
        "read_only_render_available": read_only,
        "live_shell_binding_created": False,
        "live_tui_binding_created": False,
        "api_event_bridge_created": False,
        "handoff_execution_bound": False,
        "route_execution_bound": False,
        "unavailable_capabilities": unavailable_names,
        "reason": (
            "Read-only contract summary render only via render helper"
            if read_only
            else HANDOFF_SECTION_BINDING_UNAVAILABLE_REASON
        ),
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.NOT_LIVE_BINDING.value,
        "limitations": _BINDING_NON_GOALS,
    }
    binding = CrossSurfaceHandoffBindingStatus(
        **payload,
        binding_hash=_hash_payload(payload),
    )
    assert_binding_status_is_not_live_binding(binding)
    return binding


def _build_audit_finding(
    finding_id: str,
    finding_kind: CrossSurfaceHandoffAuditFindingKind,
    message: str,
    blocked_claim: str,
    evidence_ref: str,
    *,
    severity: CrossSurfaceHandoffAuditFindingSeverity = (
        CrossSurfaceHandoffAuditFindingSeverity.INFO
    ),
) -> CrossSurfaceHandoffAuditFinding:
    payload = {
        "finding_id": finding_id,
        "schema_version": P2_5_D_AUDIT_FINDING_VERSION,
        "severity": severity,
        "finding_kind": finding_kind,
        "message": message,
        "blocked_claim": blocked_claim,
        "evidence_ref": evidence_ref,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.READINESS_AUDIT_ONLY.value,
        "limitations": _AUDIT_NON_GOALS,
    }
    return CrossSurfaceHandoffAuditFinding(
        **payload,
        finding_hash=_hash_payload(payload),
    )


def build_cross_surface_handoff_readiness_audit() -> CrossSurfaceHandoffReadinessAudit:
    findings = (
        _build_audit_finding(
            "p2_5_contract_coverage",
            CrossSurfaceHandoffAuditFindingKind.CONTRACT_SCOPE_ONLY,
            "P2.5-A/B/C/D contract/read-model coverage is present.",
            "",
            "P2.5-A/B/C/D reports and pack rollups",
        ),
        _build_audit_finding(
            "p2_5_fake_live_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_CLAIM,
            "LIVE handoff claims are blocked.",
            "LIVE",
            "P25DSideEffectProof",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_fake_trace_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_TRACE_VERIFIED_CLAIM,
            "TRACE_VERIFIED handoff claims are blocked.",
            "TRACE_VERIFIED",
            "P25DSideEffectProof",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_fake_product_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_PRODUCT_BEHAVIOR_CLAIM,
            "Product behavior claims are blocked.",
            "PRODUCT_BEHAVIOR",
            "P25DHandoffSectionResult",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_fake_release_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_RELEASE_SCOPE_CLAIM,
            "Release scope claims are blocked.",
            "RELEASE_SCOPE",
            "P25DHandoffSectionResult",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_fake_handoff_execution_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_HANDOFF_CLAIM,
            "Live handoff execution claims are blocked.",
            "LIVE_HANDOFF",
            "P25DSideEffectProof",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_fake_live_binding_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_BINDING_CLAIM,
            "Live binding claims are blocked.",
            "LIVE_BINDING",
            "CrossSurfaceHandoffBindingStatus",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_fake_ui_projection_blocked",
            CrossSurfaceHandoffAuditFindingKind.FAKE_UI_PROJECTION_CLAIM,
            "UI projection claims are blocked.",
            "UI_PROJECTION",
            "CrossSurfaceHandoffSectionProjection",
            severity=CrossSurfaceHandoffAuditFindingSeverity.BLOCKING,
        ),
        _build_audit_finding(
            "p2_5_unavailable_capabilities",
            CrossSurfaceHandoffAuditFindingKind.UNAVAILABLE_CAPABILITY,
            "Handoff execution, live binding, and projection UI remain unavailable.",
            "",
            "CrossSurfaceHandoffUnavailableCapability",
        ),
        _build_audit_finding(
            "p2_5_future_work_not_started",
            CrossSurfaceHandoffAuditFindingKind.MISSING_EVIDENCE,
            "P2.6/P2.7/P2.10/P2.13 are not started.",
            "",
            "P25DSideEffectProof",
        ),
    )
    payload = {
        "audit_id": "p2_5_d_handoff_readiness_audit",
        "schema_version": P2_5_D_READINESS_AUDIT_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "findings": findings,
        "blocks_live_claim": True,
        "blocks_trace_verified_claim": True,
        "blocks_product_behavior_claim": True,
        "blocks_release_scope_claim": True,
        "blocks_live_handoff_claim": True,
        "blocks_live_binding_claim": True,
        "blocks_ui_projection_claim": True,
        "audit_passed_for_contract_scope": True,
        "audit_passed_for_release_scope": False,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.NO_FAKE_HANDOFF_GATE.value,
        "limitations": (
            "contract-scope readiness only",
            "not product scope",
            "not authorization",
            "not release readiness",
        ),
    }
    audit = CrossSurfaceHandoffReadinessAudit(
        **payload,
        audit_hash=_hash_payload(payload),
    )
    assert_readiness_audit_catches_fake_live_claims(audit)
    return audit


def build_cross_surface_handoff_section_seal(
    audit: CrossSurfaceHandoffReadinessAudit | None = None,
    inventory: CrossSurfaceHandoffContractInventory | None = None,
    projection: CrossSurfaceHandoffSectionProjection | None = None,
    binding: CrossSurfaceHandoffBindingStatus | None = None,
    demo: CrossSurfaceHandoffContractScopeDemo | None = None,
) -> CrossSurfaceHandoffSectionSeal:
    if audit is None:
        audit = build_cross_surface_handoff_readiness_audit()
    if inventory is None:
        inventory = build_cross_surface_handoff_contract_inventory()
    if binding is None:
        binding = build_cross_surface_handoff_binding_status()
    if demo is None:
        demo = build_cross_surface_handoff_contract_scope_demo()
    projection_ref = (
        f"{projection.projection_id}:{projection.projection_hash}"
        if projection is not None
        else "pending:p2_5_d_handoff_section_projection"
    )
    status = (
        CrossSurfaceHandoffSectionSealStatus.SEALED_CONTRACT_SCOPE
        if audit.audit_passed_for_contract_scope
        and not audit.audit_passed_for_release_scope
        else CrossSurfaceHandoffSectionSealStatus.PARTIAL
    )
    payload = {
        "seal_id": "p2_5_handoff_contract_scope_exit_seal",
        "schema_version": P2_5_D_SECTION_SEAL_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "official_section_name": P2_5_D_OFFICIAL_SECTION_NAME,
        "seal_status": status,
        "covered_checkpoints": P2_5_D_PACK_CHECKPOINT_IDS,
        "covered_packs": (P2_5_A_PACK_ID, P2_5_B_PACK_ID, P2_5_C_PACK_ID, P2_5_D_PACK_ID),
        "contract_inventory_ref": f"{inventory.inventory_id}:{inventory.inventory_hash}",
        "section_projection_ref": projection_ref,
        "binding_status_ref": f"{binding.binding_status_id}:{binding.binding_hash}",
        "readiness_audit_ref": f"{audit.audit_id}:{audit.audit_hash}",
        "contract_scope_demo_ref": f"{demo.demo_id}:{demo.demo_hash}",
        "sealed_contract_scope": True,
        "sealed_release_scope": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_product_behavior": False,
        "claims_release_scope": False,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.SEALED_CONTRACT_SCOPE.value,
        "limitations": _SEAL_NON_GOALS,
    }
    seal = CrossSurfaceHandoffSectionSeal(**payload, seal_hash=_hash_payload(payload))
    assert_section_seal_is_not_release_seal(seal)
    return seal


def build_cross_surface_handoff_contract_scope_demo() -> CrossSurfaceHandoffContractScopeDemo:
    payload = {
        "demo_id": "p2_5_d_handoff_contract_scope_demo",
        "schema_version": P2_5_D_DEMO_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "demo_name": "P2.5 handoff contract-scope demo",
        "uses_contract_inventory": True,
        "uses_section_projection": True,
        "uses_binding_status": True,
        "uses_readiness_audit": True,
        "uses_section_seal": True,
        "executes_handoff": False,
        "switches_surface": False,
        "executes_route": False,
        "creates_ui": False,
        "creates_live_binding": False,
        "writes_memory": False,
        "writes_trace": False,
        "writes_storage": False,
        "mutates_runtime": False,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.CONTRACT_SCOPE_DEMO_ONLY.value,
        "limitations": (
            "DEV_FIXTURE serialization proof only",
            "not live handoff behavior",
        ),
    }
    demo = CrossSurfaceHandoffContractScopeDemo(**payload, demo_hash=_hash_payload(payload))
    assert_contract_scope_demo_is_not_runtime_demo(demo)
    return demo


def build_cross_surface_handoff_docs_state_report_sync() -> (
    CrossSurfaceHandoffDocsStateReportSync
):
    payload = {
        "sync_id": "p2_5_d_docs_state_report_sync",
        "schema_version": P2_5_D_DOCS_SYNC_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "report_created": True,
        "report_indexed": True,
        "active_task_updated": True,
        "roadmap_mirror_updated": True,
        "state_updated": True,
        "tests_updated": True,
        "duplicate_agent_state_created": False,
        "product_release_claim_created": False,
        "next_candidate": P2_5_D_NEXT_CANDIDATE,
        "next_candidate_requires_canon_read": True,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.REPORT_ONLY.value,
        "limitations": (
            "agent/ updates are evidence/progress mirrors only",
            "no duplicate state or release/product claim",
        ),
    }
    sync = CrossSurfaceHandoffDocsStateReportSync(
        **payload,
        sync_hash=_hash_payload(payload),
    )
    if sync.duplicate_agent_state_created or sync.product_release_claim_created:
        _reject(
            "P2.5-D docs sync must not create duplicate state or release claim",
            field="duplicate_agent_state_created",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    return sync


def build_cross_surface_handoff_section_projection(
    *,
    gate: CrossSurfaceHandoffSectionGate | None = None,
    inventory: CrossSurfaceHandoffContractInventory | None = None,
    pack_rollup: tuple[CrossSurfaceHandoffPackRollup, ...] | None = None,
    binding_status: CrossSurfaceHandoffBindingStatus | None = None,
    readiness_audit: CrossSurfaceHandoffReadinessAudit | None = None,
    section_seal: CrossSurfaceHandoffSectionSeal | None = None,
    contract_scope_demo: CrossSurfaceHandoffContractScopeDemo | None = None,
) -> CrossSurfaceHandoffSectionProjection:
    if gate is None:
        gate = build_cross_surface_handoff_section_gate()
    if inventory is None:
        inventory = build_cross_surface_handoff_contract_inventory()
    if pack_rollup is None:
        pack_rollup = build_cross_surface_handoff_pack_rollup()
    capabilities = build_cross_surface_handoff_section_capabilities()
    unavailable = build_cross_surface_handoff_unavailable_capabilities()
    if binding_status is None:
        binding_status = build_cross_surface_handoff_binding_status()
    if readiness_audit is None:
        readiness_audit = build_cross_surface_handoff_readiness_audit()
    if contract_scope_demo is None:
        contract_scope_demo = build_cross_surface_handoff_contract_scope_demo()
    if section_seal is None:
        section_seal = build_cross_surface_handoff_section_seal(
            audit=readiness_audit,
            inventory=inventory,
            binding=binding_status,
            demo=contract_scope_demo,
        )
    payload = {
        "projection_id": "p2_5_d_handoff_section_projection",
        "schema_version": P2_5_D_PROJECTION_VERSION,
        "section_id": P2_5_D_SECTION_ID,
        "created_for_pack": P2_5_D_PACK_ID,
        "official_section_name": P2_5_D_OFFICIAL_SECTION_NAME,
        "contract_inventory": inventory,
        "pack_rollup": pack_rollup,
        "capabilities": capabilities,
        "unavailable_capabilities": unavailable,
        "binding_status_ref": (
            f"{binding_status.binding_status_id}:{binding_status.binding_hash}"
        ),
        "readiness_audit_ref": (
            f"{readiness_audit.audit_id}:{readiness_audit.audit_hash}"
        ),
        "section_seal_ref": f"{section_seal.seal_id}:{section_seal.seal_hash}",
        "is_ui": False,
        "is_live_binding": False,
        "is_api_event_bridge": False,
        "is_source_of_truth": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_product_behavior": False,
        "claims_release_scope": False,
        "truth_label": CrossSurfaceHandoffSectionTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": _PROJECTION_NON_GOALS,
    }
    projection = CrossSurfaceHandoffSectionProjection(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_section_projection_is_not_ui(projection)
    return projection


def build_p2_5_d_side_effect_proof() -> P25DSideEffectProof:
    return P25DSideEffectProof()


def build_p2_5_d_handoff_section_result() -> P25DHandoffSectionResult:
    build_p2_5_a_fixture_handoff_pipeline()
    build_p2_5_b_handoff_context_result()
    preview = build_p2_5_c_handoff_preview_result()
    gate = build_cross_surface_handoff_section_gate(preview)
    inventory = build_cross_surface_handoff_contract_inventory(preview_result=preview)
    rollups = build_cross_surface_handoff_pack_rollup()
    binding = build_cross_surface_handoff_binding_status()
    docs_sync = build_cross_surface_handoff_docs_state_report_sync()
    audit = build_cross_surface_handoff_readiness_audit()
    demo = build_cross_surface_handoff_contract_scope_demo()
    projection = build_cross_surface_handoff_section_projection(
        gate=gate,
        inventory=inventory,
        pack_rollup=rollups,
        binding_status=binding,
        readiness_audit=audit,
        contract_scope_demo=demo,
    )
    seal = build_cross_surface_handoff_section_seal(
        audit=audit,
        inventory=inventory,
        projection=projection,
        binding=binding,
        demo=demo,
    )
    projection = build_cross_surface_handoff_section_projection(
        gate=gate,
        inventory=inventory,
        pack_rollup=rollups,
        binding_status=binding,
        readiness_audit=audit,
        section_seal=seal,
        contract_scope_demo=demo,
    )
    side_effects = build_p2_5_d_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_5_D_RESULT_VERSION,
        "pack_id": P2_5_D_PACK_ID,
        "section_id": P2_5_D_SECTION_ID,
        "official_section_name": P2_5_D_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_5_D_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_5_D_DEPENDENCY_PACK,
        "section_gate": gate,
        "contract_inventory": inventory,
        "pack_rollup": rollups,
        "section_projection": projection,
        "binding_status": binding,
        "docs_state_report_sync": docs_sync,
        "readiness_audit": audit,
        "section_seal": seal,
        "contract_scope_demo": demo,
        "truth_labels": tuple(b.value for b in CrossSurfaceHandoffSectionTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "next_candidate": P2_5_D_NEXT_CANDIDATE,
        "next_candidate_requires_canon_read": True,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P25DHandoffSectionResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_5_d_does_not_start_future_work(result)
    assert_p2_5_d_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_5_d_result(result: P25DHandoffSectionResult | None = None) -> str:
    if result is None:
        result = build_p2_5_d_handoff_section_result()
    return to_canonical_json(result.to_canonical_dict())


def render_cross_surface_handoff_section_summary(
    result: P25DHandoffSectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_5_d_handoff_section_result()
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"status={result.section_seal.seal_status.value}",
            f"sealed_contract_scope={str(result.section_seal.sealed_contract_scope).lower()}",
            f"binding={result.binding_status.binding_mode.value}",
            f"next={result.next_candidate}",
            f"next_requires_canon_read={str(result.next_candidate_requires_canon_read).lower()}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"release_scope={str(result.claims_release_scope).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


def assert_p2_5_c_preview_result_available(preview: P25CHandoffPreviewResult) -> None:
    if preview.pack_id != P2_5_C_PACK_ID or preview.starts_future_work:
        _reject(
            "P2.5-D requires P2.5-C preview result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    pr = preview.preview_result
    if not pr.no_confirmation_boundary_active or not pr.no_execution_boundary_active:
        _reject(
            "P2.5-D requires active P2.5-C no-confirmation and no-execution boundaries",
            field="no_confirmation_boundary_active",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_section_gate_depends_on_p2_5_c(gate: CrossSurfaceHandoffSectionGate) -> None:
    if gate.dependency_pack != P2_5_C_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.5-D section gate must depend on passed P2.5-C repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_preview_result_ref
        or not gate.dependency_no_confirmation_boundary_ref
        or not gate.dependency_no_execution_boundary_ref
    ):
        _reject(
            "P2.5-D section gate must reference P2.5-C preview and boundaries",
            field="dependency_preview_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: CrossSurfaceHandoffSectionGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.5-D gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_projection_is_not_ui(
    projection: CrossSurfaceHandoffSectionProjection,
) -> None:
    if (
        projection.is_ui
        or projection.is_live_binding
        or projection.is_api_event_bridge
        or projection.is_source_of_truth
        or projection.claims_live
        or projection.claims_trace_verified
        or projection.claims_product_behavior
        or projection.claims_release_scope
    ):
        _reject(
            "P2.5-D section projection must remain read-model only",
            field="is_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_binding_status_is_not_live_binding(
    binding: CrossSurfaceHandoffBindingStatus,
) -> None:
    if (
        binding.live_shell_binding_created
        or binding.live_tui_binding_created
        or binding.api_event_bridge_created
        or binding.handoff_execution_bound
        or binding.route_execution_bound
    ):
        _reject(
            "P2.5-D binding must not create live binding or execution",
            field="live_shell_binding_created",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_section_seal_is_not_release_seal(seal: CrossSurfaceHandoffSectionSeal) -> None:
    if (
        seal.sealed_release_scope
        or seal.claims_live
        or seal.claims_trace_verified
        or seal.claims_product_behavior
        or seal.claims_release_scope
    ):
        _reject(
            "P2.5-D section seal must be contract/read-model scope only",
            field="sealed_release_scope",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_contract_scope_demo_is_not_runtime_demo(
    demo: CrossSurfaceHandoffContractScopeDemo,
) -> None:
    if (
        demo.executes_handoff
        or demo.switches_surface
        or demo.executes_route
        or demo.creates_ui
        or demo.creates_live_binding
        or demo.writes_memory
        or demo.writes_trace
        or demo.writes_storage
        or demo.mutates_runtime
    ):
        _reject(
            "P2.5-D contract-scope demo must not become runtime behavior",
            field="executes_handoff",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_readiness_audit_catches_fake_live_claims(
    audit: CrossSurfaceHandoffReadinessAudit,
) -> None:
    if not audit.audit_passed_for_contract_scope:
        _reject(
            "P2.5-D audit must pass contract scope",
            field="audit_passed_for_contract_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if audit.audit_passed_for_release_scope:
        _reject(
            "P2.5-D audit must not pass release scope",
            field="audit_passed_for_release_scope",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    blocked_flags = (
        audit.blocks_live_claim,
        audit.blocks_trace_verified_claim,
        audit.blocks_product_behavior_claim,
        audit.blocks_release_scope_claim,
        audit.blocks_live_handoff_claim,
        audit.blocks_live_binding_claim,
        audit.blocks_ui_projection_claim,
    )
    if not all(blocked_flags):
        _reject(
            "P2.5-D audit must block fake live/product/release/UI claims",
            field="blocks_live_claim",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    kinds = {finding.finding_kind for finding in audit.findings}
    required = {
        CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_CLAIM,
        CrossSurfaceHandoffAuditFindingKind.FAKE_TRACE_VERIFIED_CLAIM,
        CrossSurfaceHandoffAuditFindingKind.FAKE_PRODUCT_BEHAVIOR_CLAIM,
        CrossSurfaceHandoffAuditFindingKind.FAKE_RELEASE_SCOPE_CLAIM,
        CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_HANDOFF_CLAIM,
        CrossSurfaceHandoffAuditFindingKind.FAKE_LIVE_BINDING_CLAIM,
        CrossSurfaceHandoffAuditFindingKind.FAKE_UI_PROJECTION_CLAIM,
    }
    if not required.issubset(kinds):
        _reject(
            "P2.5-D audit must include fake-claim findings",
            field="findings",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_5_d_does_not_start_future_work(result: P25DHandoffSectionResult) -> None:
    if (
        result.starts_future_work
        or result.next_candidate != P2_5_D_NEXT_CANDIDATE
        or not result.next_candidate_requires_canon_read
    ):
        _reject(
            "P2.5-D result must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_6_started,
            proof.p2_7_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.5-D must not start P2.6/P2.7/P2.10/P2.13",
            field="p2_6_started",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_5_d_side_effects_all_false(proof: P25DSideEffectProof) -> None:
    for field in fields(proof):
        value = getattr(proof, field.name)
        if value is not False:
            _reject(
                "P2.5-D side-effect proof fields must all be false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
