"""P2.4-D command palette section projection and contract-scope seal.

Contract-only section aggregation over P2.4-A/B/C. This module creates a
deterministic P2.4 read-model projection, explicit UNAVAILABLE binding status,
readiness audit, contract-scope demo, and section seal. It does not create a
command palette UI, selection UI, preview UI, keyboard shortcut handling,
command execution, command router/handler, approvals, permission enforcement,
storage, memory/trace writes, product behavior, release scope, or runtime
mutation.
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
from .global_command_discovery import (
    P2_4_A_COMMIT_REF,
    P2_4_B_PACK_ID,
    P2_4_B_REPORT_PATH,
    build_p2_4_b_command_discovery_result,
)
from .global_command_proposal import (
    P2_4_B_COMMIT_REF,
    P2_4_C_PACK_ID,
    P2_4_C_REPORT_PATH,
    P24CCommandProposalResult,
    build_p2_4_c_command_proposal_result,
)
from .global_command_registry import (
    P2_4_A_PACK_ID,
    P2_4_A_REPORT_PATH,
    P2_4_A_SECTION_ID,
    P24AGlobalCommandFoundationResult,
    build_p2_4_a_global_command_foundation_result,
)
from .read_model import detect_surface_taxonomy_drift
from .surface_registry import CANONICAL_SURFACE_ORDER

P2_4_D_PACK_ID = "P2.4-D"
P2_4_D_SECTION_ID = P2_4_A_SECTION_ID
P2_4_D_OFFICIAL_SECTION_NAME = "Command Palette / Global Commands"
P2_4_D_DEPENDENCY_PACK = P2_4_C_PACK_ID
P2_4_D_NEXT_PACK = "P2.5-A"
P2_4_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.4.16",
    "P2.4.17",
    "P2.4.18",
    "P2.4.19",
    "P2.4.20",
)
P2_4_D_REPORT_FILENAME = "P2_4_D_COMMAND_PALETTE_SECTION_SEAL.md"
P2_4_D_REPORT_PATH = f"agent/reports/{P2_4_D_REPORT_FILENAME}"

P2_4_C_COMMIT_REF = "cf5a615bae360d0c5312b6bf78ac1ab6d99c5500"
P2_4_C_REPORT_HASH_COMMIT_REF = "f70e1654f6574a9976191721021e580f7770f2ba"

P2_4_D_GATE_VERSION = "p2_4_d_global_command_section_gate.v1"
P2_4_D_INVENTORY_VERSION = "p2_4_d_global_command_contract_inventory.v1"
P2_4_D_PACK_ROLLUP_VERSION = "p2_4_d_global_command_pack_rollup.v1"
P2_4_D_CAPABILITY_VERSION = "p2_4_d_global_command_section_capability.v1"
P2_4_D_UNAVAILABLE_CAPABILITY_VERSION = (
    "p2_4_d_global_command_unavailable_capability.v1"
)
P2_4_D_BINDING_VERSION = "p2_4_d_global_command_binding_status.v1"
P2_4_D_AUDIT_FINDING_VERSION = "p2_4_d_global_command_audit_finding.v1"
P2_4_D_READINESS_AUDIT_VERSION = "p2_4_d_global_command_readiness_audit.v1"
P2_4_D_SECTION_SEAL_VERSION = "p2_4_d_global_command_section_seal.v1"
P2_4_D_DEMO_VERSION = "p2_4_d_global_command_contract_scope_demo.v1"
P2_4_D_PROJECTION_VERSION = "p2_4_d_global_command_section_projection.v1"
P2_4_D_RESULT_VERSION = "p2_4_d_command_palette_section_result.v1"

COMMAND_SECTION_BINDING_UNAVAILABLE_REASON = (
    "P2.4-D seals command palette contracts only. No compatible read-only "
    "command palette binding, CLI/TUI execution surface, keyboard shortcut "
    "surface, or product command palette UI exists in this repo scope."
)

_PROJECTION_NON_GOALS: tuple[str, ...] = (
    "no_live_ui",
    "no_source_of_truth_store",
    "no_product_behavior",
    "no_live_claim",
    "no_trace_verified_claim",
    "no_release_scope_claim",
    "no_command_execution",
    "no_p2_5_implementation",
)
_BINDING_NON_GOALS: tuple[str, ...] = (
    "no_command_palette_ui",
    "no_selection_ui",
    "no_preview_ui",
    "no_keyboard_shortcuts",
    "no_command_execution",
    "no_command_router",
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
    "no_p2_5_implementation",
)


class GlobalCommandSectionGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class GlobalCommandPackStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class GlobalCommandCapabilityStatus(str, Enum):
    AVAILABLE_CONTRACT_ONLY = "AVAILABLE_CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandBindingMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GlobalCommandSectionSealStatus(str, Enum):
    SEALED_CONTRACT_SCOPE = "SEALED_CONTRACT_SCOPE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class GlobalCommandAuditFindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"
    ERROR = "ERROR"


class GlobalCommandSectionAuditCategory(str, Enum):
    CONTRACT_COVERAGE = "CONTRACT_COVERAGE"
    UNAVAILABLE_CAPABILITY = "UNAVAILABLE_CAPABILITY"
    NO_FAKE_PRODUCT = "NO_FAKE_PRODUCT"
    NO_EXECUTION = "NO_EXECUTION"
    NO_UI = "NO_UI"
    NO_APPROVAL = "NO_APPROVAL"
    NO_PERMISSION = "NO_PERMISSION"
    NO_TRACE_VERIFIED = "NO_TRACE_VERIFIED"
    NO_RELEASE = "NO_RELEASE"
    FUTURE_WORK = "FUTURE_WORK"


class GlobalCommandSectionTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DECLARATIVE_ONLY = "DECLARATIVE_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    STATE_MIRROR_ONLY = "STATE_MIRROR_ONLY"
    READ_ONLY_OR_UNAVAILABLE = "READ_ONLY_OR_UNAVAILABLE"
    READINESS_AUDIT_ONLY = "READINESS_AUDIT_ONLY"
    NO_FAKE_PRODUCT_GATE = "NO_FAKE_PRODUCT_GATE"
    SEALED_CONTRACT_SCOPE = "SEALED_CONTRACT_SCOPE"
    CONTRACT_SCOPE_DEMO = "CONTRACT_SCOPE_DEMO"
    NOT_COMMAND_PALETTE_UI = "NOT_COMMAND_PALETTE_UI"
    NOT_SELECTION_UI = "NOT_SELECTION_UI"
    NOT_PREVIEW_UI = "NOT_PREVIEW_UI"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"
    NOT_COMMAND_ROUTER = "NOT_COMMAND_ROUTER"
    NOT_COMMAND_HANDLER = "NOT_COMMAND_HANDLER"
    NOT_INVOCATION = "NOT_INVOCATION"
    NOT_APPROVAL = "NOT_APPROVAL"
    NOT_AUTHORIZATION = "NOT_AUTHORIZATION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_RUNTIME_SIMULATION = "NOT_RUNTIME_SIMULATION"
    NOT_ROUTE_EXECUTION = "NOT_ROUTE_EXECUTION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_SOURCE_OF_TRUTH = "NOT_SOURCE_OF_TRUTH"


@dataclass(frozen=True)
class P24DSideEffectProof(_CanonicalMixin):
    command_palette_ui_created: bool = False
    selection_ui_created: bool = False
    preview_panel_ui_created: bool = False
    confirmation_modal_created: bool = False
    frontend_ui_created: bool = False
    browser_ui_created: bool = False
    tauri_app_created: bool = False
    desktop_app_created: bool = False
    keyboard_listener_created: bool = False
    shortcut_handler_created: bool = False
    live_search_created: bool = False
    command_execution_created: bool = False
    command_router_created: bool = False
    command_handler_created: bool = False
    command_invocation_created: bool = False
    approval_created: bool = False
    approval_activated: bool = False
    permission_enforcement_created: bool = False
    permission_granted: bool = False
    permission_denied: bool = False
    runtime_blocking_created: bool = False
    custos_integration_created: bool = False
    surface_runtime_switch_created: bool = False
    route_execution_created: bool = False
    route_handler_created: bool = False
    route_runtime_created: bool = False
    tool_invocation_created: bool = False
    workflow_dispatch_created: bool = False
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
    p2_5_started: bool = False
    p2_6_started: bool = False
    p2_7_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class GlobalCommandSectionGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_proposal_result_ref: str
    dependency_no_execution_boundary_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: GlobalCommandSectionGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class GlobalCommandContractInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_contracts: tuple[str, ...]
    discovery_contracts: tuple[str, ...]
    proposal_contracts: tuple[str, ...]
    section_projection_contracts: tuple[str, ...]
    missing_contracts: tuple[str, ...]
    duplicate_contracts_detected: bool
    source_of_truth_refs: tuple[str, ...]
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class GlobalCommandPackRollup(_CanonicalMixin):
    rollup_id: str
    schema_version: str
    section_id: str
    pack_id: str
    pack_name: str
    pack_status: GlobalCommandPackStatus
    report_ref: str
    commit_ref: str
    validation_ref: str
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class GlobalCommandSectionCapability(_CanonicalMixin):
    capability_id: str
    schema_version: str
    name: str
    status: GlobalCommandCapabilityStatus
    provided_by_pack: str
    evidence_ref: str
    truth_label: str
    limitations: tuple[str, ...]
    capability_hash: str


@dataclass(frozen=True)
class GlobalCommandSectionUnavailableCapability(_CanonicalMixin):
    capability_id: str
    schema_version: str
    name: str
    status: GlobalCommandCapabilityStatus
    unavailable_reason: str
    future_pack_or_section: str
    is_product_claim: bool
    truth_label: str
    limitations: tuple[str, ...]
    unavailable_capability_hash: str


@dataclass(frozen=True)
class GlobalCommandBindingStatus(_CanonicalMixin):
    binding_id: str
    schema_version: str
    binding_mode: GlobalCommandBindingMode
    binding_available: bool
    binding_kind: str
    read_only: bool
    executes_commands: bool
    invokes_handlers: bool
    routes_commands: bool
    mutates_runtime: bool
    unavailable_reason: str
    truth_label: str
    limitations: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True)
class GlobalCommandSectionAuditFinding(_CanonicalMixin):
    finding_id: str
    schema_version: str
    severity: GlobalCommandAuditFindingSeverity
    category: GlobalCommandSectionAuditCategory
    message: str
    evidence_ref: str
    required_action: str
    truth_label: str
    limitations: tuple[str, ...]
    finding_hash: str


@dataclass(frozen=True)
class GlobalCommandSectionReadinessAudit(_CanonicalMixin):
    audit_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    findings: tuple[GlobalCommandSectionAuditFinding, ...]
    passes_contract_scope: bool
    passes_product_scope: bool
    ui_available: bool
    execution_available: bool
    approval_available: bool
    permission_available: bool
    trace_verified_available: bool
    release_ready: bool
    authority_granted: bool
    truth_label: str
    limitations: tuple[str, ...]
    audit_hash: str


@dataclass(frozen=True)
class GlobalCommandSectionSeal(_CanonicalMixin):
    seal_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    seal_status: GlobalCommandSectionSealStatus
    sealed_scope: str
    sealed_as_product: bool
    sealed_as_live: bool
    sealed_as_trace_verified: bool
    sealed_as_release: bool
    next_pack: str
    conditions: tuple[str, ...]
    limitations: tuple[str, ...]
    truth_label: str
    seal_hash: str


@dataclass(frozen=True)
class GlobalCommandContractScopeDemo(_CanonicalMixin):
    demo_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    demo_kind: str
    uses_dev_fixture: bool
    uses_live_runtime: bool
    executes_commands: bool
    creates_ui: bool
    mutates_runtime: bool
    writes_memory: bool
    writes_trace: bool
    output_refs: tuple[str, ...]
    truth_label: str
    limitations: tuple[str, ...]
    demo_hash: str


@dataclass(frozen=True)
class GlobalCommandSectionProjection(_CanonicalMixin):
    projection_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    section_status: GlobalCommandSectionGateStatus
    pack_rollups: tuple[GlobalCommandPackRollup, ...]
    contract_inventory: GlobalCommandContractInventory
    capabilities: tuple[GlobalCommandSectionCapability, ...]
    unavailable_capabilities: tuple[GlobalCommandSectionUnavailableCapability, ...]
    binding_status: GlobalCommandBindingStatus
    readiness_audit_ref: str
    seal_ref: str
    contract_scope_demo_ref: str
    is_live_ui: bool
    is_source_of_truth: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_product_behavior: bool
    claims_release_scope: bool
    truth_label: str
    limitations: tuple[str, ...]
    projection_hash: str


@dataclass(frozen=True)
class GlobalCommandDocsStateReportSync(_CanonicalMixin):
    sync_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    report_created: bool
    report_indexed: bool
    active_task_updated: bool
    roadmap_mirror_updated: bool
    state_updated: bool
    duplicate_agent_state_created: bool
    product_release_claim_created: bool
    truth_label: str
    limitations: tuple[str, ...]
    sync_hash: str


@dataclass(frozen=True)
class P24DCommandPaletteSectionResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    section_gate: GlobalCommandSectionGate
    contract_inventory: GlobalCommandContractInventory
    pack_rollups: tuple[GlobalCommandPackRollup, ...]
    section_projection: GlobalCommandSectionProjection
    binding_status: GlobalCommandBindingStatus
    docs_state_report_sync: GlobalCommandDocsStateReportSync
    readiness_audit: GlobalCommandSectionReadinessAudit
    section_seal: GlobalCommandSectionSeal
    contract_scope_demo: GlobalCommandContractScopeDemo
    truth_labels: tuple[str, ...]
    unavailable_capabilities: tuple[GlobalCommandSectionUnavailableCapability, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P24DSideEffectProof
    canonical_surface_ids: tuple[str, ...]
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _enum_value(value: str | Enum) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _proposal_result_ref(result: P24CCommandProposalResult) -> str:
    return f"{result.proposal_result.proposal_result_id}:{result.proposal_result.proposal_result_hash}"


def _proposal_boundary_ref(result: P24CCommandProposalResult) -> str:
    boundary = result.no_execution_boundary
    return f"{boundary.boundary_id}:{boundary.boundary_hash}:active={str(boundary.boundary_active).lower()}"


def _foundation_ref(foundation: P24AGlobalCommandFoundationResult) -> str:
    registry = foundation.command_registry
    return f"{registry.registry_id}:{registry.registry_hash}"


def build_global_command_section_gate(
    proposal_result: P24CCommandProposalResult | None = None,
) -> GlobalCommandSectionGate:
    if proposal_result is None:
        proposal_result = build_p2_4_c_command_proposal_result()
    assert_p2_4_c_proposal_result_available(proposal_result)
    payload = {
        "gate_id": "p2_4_d_global_command_section_gate",
        "schema_version": P2_4_D_GATE_VERSION,
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "official_section_name": P2_4_D_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_4_D_DEPENDENCY_PACK,
        "dependency_report_ref": P2_4_C_REPORT_PATH,
        "dependency_commit_ref": P2_4_C_COMMIT_REF,
        "dependency_validation_ref": "agent/TESTS.md#P2.4-C",
        "dependency_proposal_result_ref": _proposal_result_ref(proposal_result),
        "dependency_no_execution_boundary_ref": _proposal_boundary_ref(proposal_result),
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": GlobalCommandSectionGateStatus.READY,
        "truth_label": GlobalCommandSectionTruthBoundary.CONTRACT_ONLY.value,
        "limitations": (
            "OMNI evidence is ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create command palette UI or command execution",
        ),
    }
    gate = GlobalCommandSectionGate(**payload, gate_hash=_hash_payload(payload))
    assert_section_gate_depends_on_p2_4_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_global_command_contract_inventory(
    foundation: P24AGlobalCommandFoundationResult | None = None,
    proposal_result: P24CCommandProposalResult | None = None,
) -> GlobalCommandContractInventory:
    if foundation is None:
        foundation = build_p2_4_a_global_command_foundation_result()
    if proposal_result is None:
        proposal_result = build_p2_4_c_command_proposal_result()
    payload = {
        "inventory_id": "p2_4_d_global_command_contract_inventory",
        "schema_version": P2_4_D_INVENTORY_VERSION,
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "official_section_name": P2_4_D_OFFICIAL_SECTION_NAME,
        "registry_contracts": (
            "CommandPaletteSectionGate",
            "GlobalCommandIdentity",
            "GlobalCommandRegistry",
            "GlobalCommandScope",
            "GlobalCommandSurfaceTarget",
            "GlobalCommandAvailability",
            "GlobalCommandInputContract",
        ),
        "discovery_contracts": (
            "GlobalCommandDiscoveryGate",
            "GlobalCommandQuery",
            "GlobalCommandFilter",
            "GlobalCommandMatch",
            "GlobalCommandDiscoveryContext",
            "GlobalCommandRanking",
            "GlobalCommandResultSet",
        ),
        "proposal_contracts": (
            "GlobalCommandProposalGate",
            "GlobalCommandSelectionIntent",
            "GlobalCommandProposal",
            "GlobalCommandInputPreview",
            "GlobalCommandImpactPreview",
            "GlobalCommandRequirementPreview",
            "GlobalCommandNoExecutionBoundary",
            "GlobalCommandProposalResult",
        ),
        "section_projection_contracts": (
            "GlobalCommandSectionGate",
            "GlobalCommandContractInventory",
            "GlobalCommandPackRollup",
            "GlobalCommandSectionProjection",
            "GlobalCommandBindingStatus",
            "GlobalCommandSectionReadinessAudit",
            "GlobalCommandSectionSeal",
            "GlobalCommandContractScopeDemo",
            "P24DSideEffectProof",
            "P24DCommandPaletteSectionResult",
        ),
        "missing_contracts": (),
        "duplicate_contracts_detected": False,
        "source_of_truth_refs": (
            f"{P2_4_A_REPORT_PATH}:{_foundation_ref(foundation)}",
            f"{P2_4_B_REPORT_PATH}:P2.4-B",
            f"{P2_4_C_REPORT_PATH}:{_proposal_result_ref(proposal_result)}",
        ),
        "truth_label": GlobalCommandSectionTruthBoundary.CONTRACT_ONLY.value,
        "limitations": (
            "Inventory references P2.4-A/B/C outputs; it does not duplicate them",
            "P2.4-D adds section projection and seal contracts only",
        ),
    }
    inventory = GlobalCommandContractInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    if inventory.duplicate_contracts_detected or inventory.missing_contracts:
        _reject(
            "P2.4-D contract inventory must not duplicate or miss known contracts",
            field="duplicate_contracts_detected",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    return inventory


def build_global_command_pack_rollup() -> tuple[GlobalCommandPackRollup, ...]:
    rows = (
        (
            P2_4_A_PACK_ID,
            "Command Palette / Global Commands Foundation",
            P2_4_A_REPORT_PATH,
            P2_4_A_COMMIT_REF,
            "agent/TESTS.md#P2.4-A",
        ),
        (
            P2_4_B_PACK_ID,
            "Command Search / Ranking / Context / Result Read Model Foundation",
            P2_4_B_REPORT_PATH,
            P2_4_B_COMMIT_REF,
            "agent/TESTS.md#P2.4-B",
        ),
        (
            P2_4_C_PACK_ID,
            "Command Proposal / Selection / Preview / No-Execution Boundary",
            P2_4_C_REPORT_PATH,
            P2_4_C_COMMIT_REF,
            "agent/TESTS.md#P2.4-C",
        ),
        (
            P2_4_D_PACK_ID,
            "Command Palette Integration Tail / Projection / Binding / Docs / Section Seal",
            P2_4_D_REPORT_PATH,
            "",
            "agent/TESTS.md#P2.4-D",
        ),
    )
    rollups: list[GlobalCommandPackRollup] = []
    for pack_id, name, report, commit, validation in rows:
        payload = {
            "rollup_id": f"p2_4_rollup:{pack_id}",
            "schema_version": P2_4_D_PACK_ROLLUP_VERSION,
            "section_id": P2_4_D_SECTION_ID,
            "pack_id": pack_id,
            "pack_name": name,
            "pack_status": GlobalCommandPackStatus.DONE,
            "report_ref": report,
            "commit_ref": commit,
            "validation_ref": validation,
            "truth_label": GlobalCommandSectionTruthBoundary.REPORT_ONLY.value,
            "limitations": (
                "Rollup is report/evidence reference only",
                "Rollup is not a source-of-truth store",
            ),
        }
        rollups.append(
            GlobalCommandPackRollup(**payload, rollup_hash=_hash_payload(payload))
        )
    return tuple(rollups)


def build_global_command_section_capabilities() -> (
    tuple[GlobalCommandSectionCapability, ...]
):
    rows = (
        (
            "command_registry_foundation",
            "command registry foundation",
            GlobalCommandCapabilityStatus.AVAILABLE_CONTRACT_ONLY,
            P2_4_A_PACK_ID,
            P2_4_A_REPORT_PATH,
        ),
        (
            "command_discovery_result_set",
            "command discovery/result-set read model",
            GlobalCommandCapabilityStatus.READ_MODEL_ONLY,
            P2_4_B_PACK_ID,
            P2_4_B_REPORT_PATH,
        ),
        (
            "command_proposal_no_execution_boundary",
            "command proposal/no-execution boundary",
            GlobalCommandCapabilityStatus.READ_MODEL_ONLY,
            P2_4_C_PACK_ID,
            P2_4_C_REPORT_PATH,
        ),
        (
            "section_projection_read_model",
            "section projection/read model",
            GlobalCommandCapabilityStatus.READ_MODEL_ONLY,
            P2_4_D_PACK_ID,
            P2_4_D_REPORT_PATH,
        ),
        (
            "section_readiness_audit",
            "section readiness audit",
            GlobalCommandCapabilityStatus.AVAILABLE_CONTRACT_ONLY,
            P2_4_D_PACK_ID,
            P2_4_D_REPORT_PATH,
        ),
        (
            "section_contract_scope_seal",
            "section contract-scope seal",
            GlobalCommandCapabilityStatus.AVAILABLE_CONTRACT_ONLY,
            P2_4_D_PACK_ID,
            P2_4_D_REPORT_PATH,
        ),
    )
    capabilities: list[GlobalCommandSectionCapability] = []
    for capability_id, name, status, pack_id, evidence in rows:
        payload = {
            "capability_id": capability_id,
            "schema_version": P2_4_D_CAPABILITY_VERSION,
            "name": name,
            "status": status,
            "provided_by_pack": pack_id,
            "evidence_ref": evidence,
            "truth_label": GlobalCommandSectionTruthBoundary.READ_MODEL_ONLY.value,
            "limitations": (
                "contract/read-model capability only",
                "not product behavior",
            ),
        }
        capabilities.append(
            GlobalCommandSectionCapability(
                **payload,
                capability_hash=_hash_payload(payload),
            )
        )
    return tuple(capabilities)


def build_global_command_unavailable_capabilities() -> (
    tuple[GlobalCommandSectionUnavailableCapability, ...]
):
    names = (
        ("actual_command_palette_ui", "actual command palette UI", "P2.5+"),
        ("selection_ui", "selection UI", "P2.5+"),
        ("preview_panel_ui", "preview panel UI", "P2.5+"),
        ("confirmation_modal", "confirmation modal", "P2.5+"),
        ("keyboard_shortcuts", "keyboard shortcuts", "P2.5+"),
        ("live_search", "live search", "P2.5+"),
        ("command_execution", "command execution", "future execution section"),
        ("command_router", "command router", "future execution section"),
        ("command_handler", "command handler", "future execution section"),
        ("approval_activation", "approval activation", "future approval section"),
        ("permission_enforcement", "permission enforcement", "future Custos section"),
        ("custos_integration", "Custos integration", "future Custos section"),
        ("route_execution", "route execution", "future route/runtime section"),
        ("surface_switching", "surface switching", "future route/runtime section"),
        ("tool_workflow_dispatch", "tool/workflow dispatch", "future execution section"),
        ("api_event_bridge", "API/event bridge", "future projection/runtime section"),
        ("memory_write", "memory write", "future memory section"),
        ("trace_write", "trace write", "future trace section"),
        ("runtime_mutation", "runtime mutation", "future runtime section"),
        ("release_scope", "release scope", "future release section"),
        ("trace_verified_seal", "TRACE_VERIFIED seal", "future trace verification section"),
    )
    capabilities: list[GlobalCommandSectionUnavailableCapability] = []
    for capability_id, name, future in names:
        payload = {
            "capability_id": capability_id,
            "schema_version": P2_4_D_UNAVAILABLE_CAPABILITY_VERSION,
            "name": name,
            "status": GlobalCommandCapabilityStatus.UNAVAILABLE,
            "unavailable_reason": COMMAND_SECTION_BINDING_UNAVAILABLE_REASON,
            "future_pack_or_section": future,
            "is_product_claim": False,
            "truth_label": GlobalCommandSectionTruthBoundary.UNAVAILABLE.value,
            "limitations": (
                "unavailable in P2.4-D",
                "must not be claimed as product behavior",
            ),
        }
        capabilities.append(
            GlobalCommandSectionUnavailableCapability(
                **payload,
                unavailable_capability_hash=_hash_payload(payload),
            )
        )
    return tuple(capabilities)


def build_global_command_binding_status(
    *,
    binding_mode: GlobalCommandBindingMode = GlobalCommandBindingMode.UNAVAILABLE,
    unavailable_reason: str = COMMAND_SECTION_BINDING_UNAVAILABLE_REASON,
) -> GlobalCommandBindingStatus:
    if binding_mode == GlobalCommandBindingMode.UNAVAILABLE and not unavailable_reason:
        _reject(
            "UNAVAILABLE command binding requires unavailable reason",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    is_read_only = binding_mode == GlobalCommandBindingMode.READ_ONLY
    payload = {
        "binding_id": "p2_4_d_global_command_binding_status",
        "schema_version": P2_4_D_BINDING_VERSION,
        "binding_mode": binding_mode,
        "binding_available": is_read_only,
        "binding_kind": "COMMAND_SECTION_BINDING_CONTRACT",
        "read_only": is_read_only,
        "executes_commands": False,
        "invokes_handlers": False,
        "routes_commands": False,
        "mutates_runtime": False,
        "unavailable_reason": "" if is_read_only else unavailable_reason,
        "truth_label": GlobalCommandSectionTruthBoundary.READ_ONLY_OR_UNAVAILABLE.value,
        "limitations": _BINDING_NON_GOALS,
    }
    binding = GlobalCommandBindingStatus(**payload, binding_hash=_hash_payload(payload))
    assert_binding_is_read_only_or_unavailable(binding)
    return binding


def _build_audit_finding(
    finding_id: str,
    category: GlobalCommandSectionAuditCategory,
    message: str,
    evidence_ref: str,
    required_action: str,
    *,
    severity: GlobalCommandAuditFindingSeverity = GlobalCommandAuditFindingSeverity.INFO,
) -> GlobalCommandSectionAuditFinding:
    payload = {
        "finding_id": finding_id,
        "schema_version": P2_4_D_AUDIT_FINDING_VERSION,
        "severity": severity,
        "category": category,
        "message": message,
        "evidence_ref": evidence_ref,
        "required_action": required_action,
        "truth_label": GlobalCommandSectionTruthBoundary.READINESS_AUDIT_ONLY.value,
        "limitations": _AUDIT_NON_GOALS,
    }
    return GlobalCommandSectionAuditFinding(
        **payload,
        finding_hash=_hash_payload(payload),
    )


def build_global_command_section_readiness_audit() -> (
    GlobalCommandSectionReadinessAudit
):
    findings = (
        _build_audit_finding(
            "p2_4_contract_coverage",
            GlobalCommandSectionAuditCategory.CONTRACT_COVERAGE,
            "P2.4-A/B/C/D contract/read-model coverage is present.",
            "P2.4-A/B/C/D reports and pack rollups",
            "None for contract scope.",
        ),
        _build_audit_finding(
            "p2_4_ui_unavailable",
            GlobalCommandSectionAuditCategory.NO_UI,
            "Command palette, selection, preview, and confirmation UI are unavailable.",
            "P24DSideEffectProof",
            "Do not claim product UI in P2.4-D.",
        ),
        _build_audit_finding(
            "p2_4_execution_unavailable",
            GlobalCommandSectionAuditCategory.NO_EXECUTION,
            "Command execution, router, handler, invocation, tools, and workflows are unavailable.",
            "P24DSideEffectProof",
            "Defer execution to a future authorized pack.",
        ),
        _build_audit_finding(
            "p2_4_approval_permission_unavailable",
            GlobalCommandSectionAuditCategory.NO_PERMISSION,
            "Approval activation, permission enforcement, and Custos integration are unavailable.",
            "P24DSideEffectProof",
            "Do not grant authority or enforce permissions in P2.4-D.",
        ),
        _build_audit_finding(
            "p2_4_trace_release_unavailable",
            GlobalCommandSectionAuditCategory.NO_TRACE_VERIFIED,
            "Trace verification and release readiness are unavailable.",
            "P24DCommandPaletteSectionResult",
            "Do not claim TRACE_VERIFIED or release scope.",
        ),
        _build_audit_finding(
            "p2_4_future_work_not_started",
            GlobalCommandSectionAuditCategory.FUTURE_WORK,
            "P2.5/P2.6/P2.7/P2.10/P2.13 are not started.",
            "P24DSideEffectProof",
            "Start future work only under a future dispatch.",
        ),
    )
    payload = {
        "audit_id": "p2_4_d_global_command_readiness_audit",
        "schema_version": P2_4_D_READINESS_AUDIT_VERSION,
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "findings": findings,
        "passes_contract_scope": True,
        "passes_product_scope": False,
        "ui_available": False,
        "execution_available": False,
        "approval_available": False,
        "permission_available": False,
        "trace_verified_available": False,
        "release_ready": False,
        "authority_granted": False,
        "truth_label": GlobalCommandSectionTruthBoundary.NO_FAKE_PRODUCT_GATE.value,
        "limitations": (
            "contract-scope readiness only",
            "not product scope",
            "not authorization",
            "not release readiness",
        ),
    }
    audit = GlobalCommandSectionReadinessAudit(
        **payload,
        audit_hash=_hash_payload(payload),
    )
    assert_audit_catches_forbidden_behavior(audit)
    return audit


def build_global_command_section_seal(
    audit: GlobalCommandSectionReadinessAudit | None = None,
) -> GlobalCommandSectionSeal:
    if audit is None:
        audit = build_global_command_section_readiness_audit()
    status = (
        GlobalCommandSectionSealStatus.SEALED_CONTRACT_SCOPE
        if audit.passes_contract_scope
        and not audit.passes_product_scope
        and not audit.release_ready
        else GlobalCommandSectionSealStatus.PARTIAL
    )
    payload = {
        "seal_id": "p2_4_command_palette_contract_scope_exit_seal",
        "schema_version": P2_4_D_SECTION_SEAL_VERSION,
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "seal_status": status,
        "sealed_scope": "CONTRACT_READ_MODEL_ONLY",
        "sealed_as_product": False,
        "sealed_as_live": False,
        "sealed_as_trace_verified": False,
        "sealed_as_release": False,
        "next_pack": P2_4_D_NEXT_PACK,
        "conditions": (
            "P2.4-C repo evidence gate passed",
            "P2.4-A/B/C rollup present",
            "section projection serializes deterministically",
            "binding is UNAVAILABLE or READ_ONLY",
            "readiness audit passes contract scope only",
            "side-effect proof remains all false",
        ),
        "limitations": (
            "contract/read-model section seal only",
            "not command palette product",
            "not LIVE",
            "not TRACE_VERIFIED",
            "not release scope",
        ),
        "truth_label": GlobalCommandSectionTruthBoundary.SEALED_CONTRACT_SCOPE.value,
    }
    seal = GlobalCommandSectionSeal(**payload, seal_hash=_hash_payload(payload))
    assert_section_seal_is_not_release(seal)
    return seal


def build_global_command_contract_scope_demo(
    seal: GlobalCommandSectionSeal | None = None,
) -> GlobalCommandContractScopeDemo:
    if seal is None:
        seal = build_global_command_section_seal()
    payload = {
        "demo_id": "p2_4_d_command_palette_contract_scope_demo",
        "schema_version": P2_4_D_DEMO_VERSION,
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "demo_kind": "CONTRACT_SCOPE_DEMO",
        "uses_dev_fixture": True,
        "uses_live_runtime": False,
        "executes_commands": False,
        "creates_ui": False,
        "mutates_runtime": False,
        "writes_memory": False,
        "writes_trace": False,
        "output_refs": (
            f"{seal.seal_id}:{seal.seal_hash}",
            "render_global_command_section_summary()",
            "serialize_p2_4_d_result()",
        ),
        "truth_label": GlobalCommandSectionTruthBoundary.CONTRACT_SCOPE_DEMO.value,
        "limitations": (
            "DEV_FIXTURE serialization proof only",
            "not live command palette behavior",
        ),
    }
    demo = GlobalCommandContractScopeDemo(**payload, demo_hash=_hash_payload(payload))
    assert_demo_is_contract_scope_only(demo)
    return demo


def build_global_command_docs_state_report_sync() -> GlobalCommandDocsStateReportSync:
    payload = {
        "sync_id": "p2_4_d_docs_state_report_sync",
        "schema_version": "p2_4_d_docs_state_report_sync.v1",
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "report_created": True,
        "report_indexed": True,
        "active_task_updated": True,
        "roadmap_mirror_updated": True,
        "state_updated": True,
        "duplicate_agent_state_created": False,
        "product_release_claim_created": False,
        "truth_label": GlobalCommandSectionTruthBoundary.REPORT_ONLY.value,
        "limitations": (
            "agent/ updates are evidence/progress mirrors only",
            "no duplicate state or release/product claim",
        ),
    }
    sync = GlobalCommandDocsStateReportSync(**payload, sync_hash=_hash_payload(payload))
    if sync.duplicate_agent_state_created or sync.product_release_claim_created:
        _reject(
            "P2.4-D docs sync must not create duplicate state or release claim",
            field="duplicate_agent_state_created",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    return sync


def build_global_command_section_projection(
    *,
    gate: GlobalCommandSectionGate | None = None,
    inventory: GlobalCommandContractInventory | None = None,
    pack_rollups: tuple[GlobalCommandPackRollup, ...] | None = None,
    binding_status: GlobalCommandBindingStatus | None = None,
    readiness_audit: GlobalCommandSectionReadinessAudit | None = None,
    section_seal: GlobalCommandSectionSeal | None = None,
    contract_scope_demo: GlobalCommandContractScopeDemo | None = None,
) -> GlobalCommandSectionProjection:
    if gate is None:
        gate = build_global_command_section_gate()
    if inventory is None:
        inventory = build_global_command_contract_inventory()
    if pack_rollups is None:
        pack_rollups = build_global_command_pack_rollup()
    capabilities = build_global_command_section_capabilities()
    unavailable = build_global_command_unavailable_capabilities()
    if binding_status is None:
        binding_status = build_global_command_binding_status()
    if readiness_audit is None:
        readiness_audit = build_global_command_section_readiness_audit()
    if section_seal is None:
        section_seal = build_global_command_section_seal(readiness_audit)
    if contract_scope_demo is None:
        contract_scope_demo = build_global_command_contract_scope_demo(section_seal)
    payload = {
        "projection_id": "p2_4_d_global_command_section_projection",
        "schema_version": P2_4_D_PROJECTION_VERSION,
        "section_id": P2_4_D_SECTION_ID,
        "created_for_pack": P2_4_D_PACK_ID,
        "official_section_name": P2_4_D_OFFICIAL_SECTION_NAME,
        "section_status": gate.gate_status,
        "pack_rollups": pack_rollups,
        "contract_inventory": inventory,
        "capabilities": capabilities,
        "unavailable_capabilities": unavailable,
        "binding_status": binding_status,
        "readiness_audit_ref": f"{readiness_audit.audit_id}:{readiness_audit.audit_hash}",
        "seal_ref": f"{section_seal.seal_id}:{section_seal.seal_hash}",
        "contract_scope_demo_ref": (
            f"{contract_scope_demo.demo_id}:{contract_scope_demo.demo_hash}"
        ),
        "is_live_ui": False,
        "is_source_of_truth": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_product_behavior": False,
        "claims_release_scope": False,
        "truth_label": GlobalCommandSectionTruthBoundary.READ_MODEL_ONLY.value,
        "limitations": _PROJECTION_NON_GOALS,
    }
    projection = GlobalCommandSectionProjection(
        **payload,
        projection_hash=_hash_payload(payload),
    )
    assert_projection_is_not_live_ui(projection)
    return projection


def build_p2_4_d_side_effect_proof() -> P24DSideEffectProof:
    return P24DSideEffectProof()


def build_p2_4_d_command_palette_section_result() -> (
    P24DCommandPaletteSectionResult
):
    foundation = build_p2_4_a_global_command_foundation_result()
    build_p2_4_b_command_discovery_result()
    proposal = build_p2_4_c_command_proposal_result()
    gate = build_global_command_section_gate(proposal)
    inventory = build_global_command_contract_inventory(foundation, proposal)
    rollups = build_global_command_pack_rollup()
    binding = build_global_command_binding_status()
    docs_sync = build_global_command_docs_state_report_sync()
    audit = build_global_command_section_readiness_audit()
    seal = build_global_command_section_seal(audit)
    demo = build_global_command_contract_scope_demo(seal)
    projection = build_global_command_section_projection(
        gate=gate,
        inventory=inventory,
        pack_rollups=rollups,
        binding_status=binding,
        readiness_audit=audit,
        section_seal=seal,
        contract_scope_demo=demo,
    )
    side_effects = build_p2_4_d_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_4_D_RESULT_VERSION,
        "pack_id": P2_4_D_PACK_ID,
        "section_id": P2_4_D_SECTION_ID,
        "official_section_name": P2_4_D_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_4_D_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_4_D_DEPENDENCY_PACK,
        "section_gate": gate,
        "contract_inventory": inventory,
        "pack_rollups": rollups,
        "section_projection": projection,
        "binding_status": binding,
        "docs_state_report_sync": docs_sync,
        "readiness_audit": audit,
        "section_seal": seal,
        "contract_scope_demo": demo,
        "truth_labels": (
            GlobalCommandSectionTruthBoundary.CONTRACT_ONLY.value,
            GlobalCommandSectionTruthBoundary.READ_MODEL_ONLY.value,
            GlobalCommandSectionTruthBoundary.READ_ONLY_OR_UNAVAILABLE.value,
            GlobalCommandSectionTruthBoundary.REPORT_ONLY.value,
            GlobalCommandSectionTruthBoundary.NO_FAKE_PRODUCT_GATE.value,
            GlobalCommandSectionTruthBoundary.SEALED_CONTRACT_SCOPE.value,
            GlobalCommandSectionTruthBoundary.CONTRACT_SCOPE_DEMO.value,
            GlobalCommandSectionTruthBoundary.DEV_FIXTURE.value,
            GlobalCommandSectionTruthBoundary.NOT_COMMAND_PALETTE_UI.value,
            GlobalCommandSectionTruthBoundary.NOT_EXECUTABLE.value,
            GlobalCommandSectionTruthBoundary.NOT_LIVE.value,
            GlobalCommandSectionTruthBoundary.NOT_TRACE_VERIFIED.value,
            GlobalCommandSectionTruthBoundary.NOT_PRODUCT_BEHAVIOR.value,
            GlobalCommandSectionTruthBoundary.NOT_RELEASE_SCOPE.value,
        ),
        "unavailable_capabilities": projection.unavailable_capabilities,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "canonical_surface_ids": CANONICAL_SURFACE_ORDER,
        "next_pack": P2_4_D_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P24DCommandPaletteSectionResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_4_d_does_not_start_future_work(result)
    assert_p2_4_d_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_4_d_result(
    result: P24DCommandPaletteSectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_d_command_palette_section_result()
    return to_canonical_json(result.to_canonical_dict())


def render_global_command_section_summary(
    result: P24DCommandPaletteSectionResult | None = None,
) -> str:
    if result is None:
        result = build_p2_4_d_command_palette_section_result()
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"status={result.section_seal.seal_status.value}",
            f"scope={result.section_seal.sealed_scope}",
            f"binding={result.binding_status.binding_mode.value}",
            f"next={result.next_pack}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"release_scope={str(result.claims_release_scope).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
        )
    )


def assert_p2_4_c_proposal_result_available(
    proposal_result: P24CCommandProposalResult,
) -> None:
    if proposal_result.pack_id != P2_4_C_PACK_ID or proposal_result.starts_future_work:
        _reject(
            "P2.4-D requires P2.4-C proposal result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    boundary = proposal_result.no_execution_boundary
    if not boundary.boundary_active or boundary.execution_allowed:
        _reject(
            "P2.4-D requires active P2.4-C no-execution boundary",
            field="no_execution_boundary",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if not proposal_result.proposal.unavailable_reason:
        _reject(
            "P2.4-D requires P2.4-C unavailable reason propagation",
            field="unavailable_reason",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_gate_depends_on_p2_4_c(gate: GlobalCommandSectionGate) -> None:
    if gate.dependency_pack != P2_4_C_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.4-D section gate must depend on passed P2.4-C repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not gate.dependency_proposal_result_ref or not gate.dependency_no_execution_boundary_ref:
        _reject(
            "P2.4-D section gate must reference P2.4-C proposal and no-execution boundary",
            field="dependency_proposal_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: GlobalCommandSectionGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.4-D gate must ignore OMNI evidence only by operator instruction",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_projection_is_not_live_ui(
    projection: GlobalCommandSectionProjection,
) -> None:
    if (
        projection.is_live_ui
        or projection.is_source_of_truth
        or projection.claims_live
        or projection.claims_trace_verified
        or projection.claims_product_behavior
        or projection.claims_release_scope
    ):
        _reject(
            "P2.4-D section projection must remain read-model only",
            field="is_live_ui",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_binding_is_read_only_or_unavailable(
    binding: GlobalCommandBindingStatus,
) -> None:
    mode = _enum_value(binding.binding_mode)
    if mode == GlobalCommandBindingMode.UNAVAILABLE.value:
        if binding.binding_available or not binding.unavailable_reason:
            _reject(
                "UNAVAILABLE binding must be unavailable and include reason",
                field="unavailable_reason",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    elif mode == GlobalCommandBindingMode.READ_ONLY.value:
        if not binding.binding_available or not binding.read_only:
            _reject(
                "READ_ONLY binding must be available and read-only",
                field="read_only",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    else:
        _reject(
            "P2.4-D binding must be READ_ONLY or UNAVAILABLE",
            field="binding_mode",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        binding.executes_commands
        or binding.invokes_handlers
        or binding.routes_commands
        or binding.mutates_runtime
    ):
        _reject(
            "P2.4-D binding must not execute, route, invoke, or mutate runtime",
            field="executes_commands",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_audit_catches_forbidden_behavior(
    audit: GlobalCommandSectionReadinessAudit,
) -> None:
    if not audit.passes_contract_scope:
        _reject(
            "P2.4-D audit must pass contract scope",
            field="passes_contract_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    forbidden = (
        audit.passes_product_scope,
        audit.ui_available,
        audit.execution_available,
        audit.approval_available,
        audit.permission_available,
        audit.trace_verified_available,
        audit.release_ready,
        audit.authority_granted,
    )
    if any(forbidden):
        _reject(
            "P2.4-D readiness audit must catch fake product/release/authority claims",
            field="passes_product_scope",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_section_seal_is_not_release(seal: GlobalCommandSectionSeal) -> None:
    if (
        seal.seal_status != GlobalCommandSectionSealStatus.SEALED_CONTRACT_SCOPE
        or seal.sealed_scope != "CONTRACT_READ_MODEL_ONLY"
        or seal.sealed_as_product
        or seal.sealed_as_live
        or seal.sealed_as_trace_verified
        or seal.sealed_as_release
    ):
        _reject(
            "P2.4-D section seal must be contract/read-model scope only",
            field="seal_status",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_demo_is_contract_scope_only(demo: GlobalCommandContractScopeDemo) -> None:
    if (
        not demo.uses_dev_fixture
        or demo.uses_live_runtime
        or demo.executes_commands
        or demo.creates_ui
        or demo.mutates_runtime
        or demo.writes_memory
        or demo.writes_trace
    ):
        _reject(
            "P2.4-D contract-scope demo must not become live product behavior",
            field="uses_live_runtime",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_d_does_not_start_future_work(
    result: P24DCommandPaletteSectionResult,
) -> None:
    if result.starts_future_work or result.next_pack != P2_4_D_NEXT_PACK:
        _reject(
            "P2.4-D result must not start future work",
            field="starts_future_work",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_5_started,
            proof.p2_6_started,
            proof.p2_7_started,
            proof.p2_10_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.4-D must not start P2.5/P2.6/P2.7/P2.10/P2.13",
            field="p2_5_started",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_4_d_side_effects_all_false(proof: P24DSideEffectProof) -> None:
    for field, value in proof.to_canonical_dict().items():
        if value is not False:
            _reject(
                "P2.4-D side-effect proof fields must all be false",
                field=field,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
