"""P2.8-D Shell State / Reports / Docs section seal contracts.

Contract-only section seal over P2.8-A/B/C evidence. This module creates the
P2.8 section seal gate, contract inventory, coverage matrix, section read model,
availability rollup, runtime unavailable rollup, P2.9 handoff contract, validation
rollup, evidence rollup, contract-scope demo, no-live/no-sync/no-generation/no-write
proofs, section seal result, side-effect proof, and pack result.

It does not create live Shell state runtime, Shell state sync runtime, state
reconciliation engine, repair/autofix action, refresh runtime, persistent state
store, database persistence, storage/trace/memory/docs/reports writes, report/docs/
summary generator runtime, report/docs publisher, product UI, product behavior,
CLI runner, TUI runtime, command execution, runtime dispatch, permission
enforcement, Custos decisioning, approval runtime, release seal, P2.9, P2.10,
P2.11, P2.12, P2.13, LIVE, or TRACE_VERIFIED.
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
from .shell_state_foundation import (
    P2_8_A_PACK_ID,
    P2_8_A_REPORT_PATH,
    P2_8_A_TEST_REF,
    P2_8_A_VALIDATION_REF,
    P28AShellStateFoundationResult,
    build_p2_8_a_shell_state_foundation_result,
)
from .shell_state_read_models import (
    P2_8_B_PACK_ID,
    P2_8_B_REPORT_PATH,
    P2_8_B_TEST_REF,
    P2_8_B_VALIDATION_REF,
    P28BShellStateReadModelResult,
    build_p2_8_b_shell_state_read_model_result,
)
from .shell_state_summary import (
    P2_8_C_PACK_ID,
    P2_8_C_REPORT_PATH,
    P2_8_C_TEST_REF,
    P2_8_C_VALIDATION_REF,
    P28CShellStateSummaryResult,
    build_p2_8_c_shell_state_summary_result,
)
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES

P2_8_D_PACK_ID = "P2.8-D"
P2_8_D_SECTION_ID = "P2.8"
P2_8_D_OFFICIAL_SECTION_NAME = "Shell State / Reports / Docs"
P2_8_D_DEPENDENCY_PACK = P2_8_C_PACK_ID
P2_8_D_NEXT_PACK = "P2.9-A"
P2_8_D_NEXT_SECTION = "P2.9 — Shell Exit Seal"
P2_8_D_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.8.16",
    "P2.8.17",
    "P2.8.18",
    "P2.8.19",
    "P2.8.20",
)
P2_8_D_FULL_SECTION_CHECKPOINTS: tuple[str, ...] = tuple(
    f"P2.8.{index}" for index in range(21)
)
P2_8_D_REPORT_FILENAME = "P2_8_D_SHELL_STATE_REPORTS_DOCS_SECTION_SEAL.md"
P2_8_D_REPORT_PATH = f"agent/reports/{P2_8_D_REPORT_FILENAME}"

P2_8_A_COMMIT_REF = "c6b995a"
P2_8_B_COMMIT_REF = "8762a8a"
P2_8_C_COMMIT_REF = "1ceef88"

P2_8_D_GATE_VERSION = "p2_8_d_shell_state_section_seal_gate.v1"
P2_8_D_INVENTORY_VERSION = "p2_8_d_shell_state_section_contract_inventory.v1"
P2_8_D_ENTRY_VERSION = "p2_8_d_shell_state_section_contract_entry.v1"
P2_8_D_COVERAGE_MATRIX_VERSION = "p2_8_d_shell_state_section_coverage_matrix.v1"
P2_8_D_COVERAGE_ENTRY_VERSION = "p2_8_d_shell_state_section_coverage_entry.v1"
P2_8_D_READ_MODEL_VERSION = "p2_8_d_shell_state_section_read_model.v1"
P2_8_D_AVAILABILITY_ROLLUP_VERSION = (
    "p2_8_d_shell_state_reports_docs_availability_rollup.v1"
)
P2_8_D_RUNTIME_UNAVAILABLE_VERSION = (
    "p2_8_d_shell_state_runtime_unavailable_rollup.v1"
)
P2_8_D_P2_9_HANDOFF_VERSION = "p2_8_d_shell_state_p2_9_handoff_contract.v1"
P2_8_D_VALIDATION_ROLLUP_VERSION = "p2_8_d_shell_state_section_validation_rollup.v1"
P2_8_D_EVIDENCE_ROLLUP_VERSION = "p2_8_d_shell_state_section_evidence_rollup.v1"
P2_8_D_DEMO_VERSION = "p2_8_d_shell_state_section_contract_scope_demo.v1"
P2_8_D_NO_LIVE_STATE_VERSION = "p2_8_d_shell_state_no_live_state_proof.v1"
P2_8_D_NO_SYNC_VERSION = "p2_8_d_shell_state_no_sync_runtime_proof.v1"
P2_8_D_NO_GENERATION_VERSION = "p2_8_d_shell_state_no_generation_proof.v1"
P2_8_D_NO_WRITE_VERSION = "p2_8_d_shell_state_no_write_proof.v1"
P2_8_D_SECTION_SEAL_RESULT_VERSION = "p2_8_d_shell_state_section_seal_result.v1"
P2_8_D_RESULT_VERSION = "p2_8_d_shell_state_section_seal_pack_result.v1"

P2_8_D_TEST_REF = "tests/aurel_shell/test_shell_state_section_seal.py"
P2_8_D_VALIDATION_REF = "agent/TESTS.md#P2.8-D"
P2_8_D_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_8_D_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_RUNTIME_UNAVAILABLE_REASON = (
    "P2.8-D seals Shell State / Reports / Docs contracts only. Live Shell state, "
    "sync runtime, generators, write path, product, and future-pack capabilities "
    "are unavailable by design."
)
_P2_9_HANDOFF_REASON = (
    "P2.8-D can hand off contract evidence to P2.9-A, but it does not start "
    "P2.9 or create Shell Exit Seal behavior."
)
_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "Live Shell state runtime",
    "Shell state sync runtime",
    "State reconciliation engine",
    "Repair/autofix action",
    "Refresh runtime",
    "Persistent state store",
    "Database persistence",
    "Trace write",
    "Memory write",
    "Storage write",
    "Docs write",
    "Reports write",
    "Report generator runtime",
    "Docs generator runtime",
    "Summary generator runtime",
    "Report publisher",
    "Docs publisher",
    "Product UI",
    "Product behavior",
    "CLI runner",
    "TUI runtime",
    "Command execution",
    "Runtime dispatch",
    "Permission enforcement",
    "Custos decisioning",
    "P2.9 implementation",
    "P2.10 implementation",
    "P2.11 implementation",
    "P2.12 implementation",
    "P2.13 implementation",
)

_CHECKPOINT_SPECS: tuple[tuple[str, str, str, str, str, str, str], ...] = (
    (
        "P2.8.0",
        "Shell State Section Intake / P2.7-D Handoff Gate",
        P2_8_A_PACK_ID,
        P2_8_A_REPORT_PATH,
        P2_8_A_TEST_REF,
        P2_8_A_COMMIT_REF,
        "ShellStateFoundationGate",
    ),
    (
        "P2.8.1",
        "Shell State Snapshot / Scope Contract",
        P2_8_A_PACK_ID,
        P2_8_A_REPORT_PATH,
        P2_8_A_TEST_REF,
        P2_8_A_COMMIT_REF,
        "ShellStateSnapshotContract",
    ),
    (
        "P2.8.2",
        "Shell Report Reference Registry Contract",
        P2_8_A_PACK_ID,
        P2_8_A_REPORT_PATH,
        P2_8_A_TEST_REF,
        P2_8_A_COMMIT_REF,
        "ShellReportReferenceRegistry",
    ),
    (
        "P2.8.3",
        "Shell Docs Reference Registry Contract",
        P2_8_A_PACK_ID,
        P2_8_A_REPORT_PATH,
        P2_8_A_TEST_REF,
        P2_8_A_COMMIT_REF,
        "ShellDocsReferenceRegistry",
    ),
    (
        "P2.8.4",
        "Report / Docs Availability / Governance Source Boundary",
        P2_8_A_PACK_ID,
        P2_8_A_REPORT_PATH,
        P2_8_A_TEST_REF,
        P2_8_A_COMMIT_REF,
        "ShellReportDocsAvailabilityContract",
    ),
    (
        "P2.8.5",
        "Shell State Foundation Result / No-Runtime-State-Mutation Contract",
        P2_8_A_PACK_ID,
        P2_8_A_REPORT_PATH,
        P2_8_A_TEST_REF,
        P2_8_A_COMMIT_REF,
        "ShellStateFoundationResult",
    ),
    (
        "P2.8.6",
        "Shell State Read Model Registry / Inventory Contract",
        P2_8_B_PACK_ID,
        P2_8_B_REPORT_PATH,
        P2_8_B_TEST_REF,
        P2_8_B_COMMIT_REF,
        "ShellStateReadModelInventory",
    ),
    (
        "P2.8.7",
        "Shell Section Status / State Snapshot Read Model Contract",
        P2_8_B_PACK_ID,
        P2_8_B_REPORT_PATH,
        P2_8_B_TEST_REF,
        P2_8_B_COMMIT_REF,
        "ShellSectionStatusReadModel",
    ),
    (
        "P2.8.8",
        "Shell Report Index / Report Family Grouping Contract",
        P2_8_B_PACK_ID,
        P2_8_B_REPORT_PATH,
        P2_8_B_TEST_REF,
        P2_8_B_COMMIT_REF,
        "ShellReportIndexReadModel",
    ),
    (
        "P2.8.9",
        "Docs Index / Query / Filter / Sort Descriptor Contract",
        P2_8_B_PACK_ID,
        P2_8_B_REPORT_PATH,
        P2_8_B_TEST_REF,
        P2_8_B_COMMIT_REF,
        "ShellDocsIndexReadModel",
    ),
    (
        "P2.8.10",
        "Read Model Expansion Result / No-Generation / No-Runtime-Mutation Contract",
        P2_8_B_PACK_ID,
        P2_8_B_REPORT_PATH,
        P2_8_B_TEST_REF,
        P2_8_B_COMMIT_REF,
        "ShellStateReadModelExpansionResult",
    ),
    (
        "P2.8.11",
        "Docs / Reports Index Summary Contract",
        P2_8_C_PACK_ID,
        P2_8_C_REPORT_PATH,
        P2_8_C_TEST_REF,
        P2_8_C_COMMIT_REF,
        "ShellDocsIndexSummary",
    ),
    (
        "P2.8.12",
        "Shell State Read-Only Summary Contract",
        P2_8_C_PACK_ID,
        P2_8_C_REPORT_PATH,
        P2_8_C_TEST_REF,
        P2_8_C_COMMIT_REF,
        "ShellStateReadOnlySummary",
    ),
    (
        "P2.8.13",
        "State Sync Descriptor / Candidate Contract",
        P2_8_C_PACK_ID,
        P2_8_C_REPORT_PATH,
        P2_8_C_TEST_REF,
        P2_8_C_COMMIT_REF,
        "ShellStateSyncDescriptor",
    ),
    (
        "P2.8.14",
        "Reference Drift / Missing / Stale Descriptor Contract",
        P2_8_C_PACK_ID,
        P2_8_C_REPORT_PATH,
        P2_8_C_TEST_REF,
        P2_8_C_COMMIT_REF,
        "ShellReferenceDriftDescriptor",
    ),
    (
        "P2.8.15",
        "Read-Only Summary Boundary Result / No-Sync / No-Generation Contract",
        P2_8_C_PACK_ID,
        P2_8_C_REPORT_PATH,
        P2_8_C_TEST_REF,
        P2_8_C_COMMIT_REF,
        "ShellStateSummaryBoundaryResult",
    ),
    (
        "P2.8.16",
        "Shell State / Reports / Docs Contract Inventory Rollup",
        P2_8_D_PACK_ID,
        P2_8_D_REPORT_PATH,
        P2_8_D_TEST_REF,
        "PENDING_AT_BUILD",
        "ShellStateSectionContractInventory",
    ),
    (
        "P2.8.17",
        "P2.8 Section Read Model / Section Status Contract",
        P2_8_D_PACK_ID,
        P2_8_D_REPORT_PATH,
        P2_8_D_TEST_REF,
        "PENDING_AT_BUILD",
        "ShellStateSectionReadModel",
    ),
    (
        "P2.8.18",
        "Availability / Runtime Unavailable / P2.9 Handoff Contract",
        P2_8_D_PACK_ID,
        P2_8_D_REPORT_PATH,
        P2_8_D_TEST_REF,
        "PENDING_AT_BUILD",
        "ShellStateP29HandoffContract",
    ),
    (
        "P2.8.19",
        "Docs / State / Reports Synchronization / Evidence Rollup",
        P2_8_D_PACK_ID,
        P2_8_D_REPORT_PATH,
        P2_8_D_TEST_REF,
        "PENDING_AT_BUILD",
        "ShellStateSectionEvidenceRollup",
    ),
    (
        "P2.8.20",
        "Section Exit Seal / Contract-Scope Demo / No-Live-State Proof",
        P2_8_D_PACK_ID,
        P2_8_D_REPORT_PATH,
        P2_8_D_TEST_REF,
        "PENDING_AT_BUILD",
        "ShellStateSectionSealResult",
    ),
)


class ShellStateSectionSealGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellStateSectionContractEntryStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ShellStateSectionCoverageEntryStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ShellStateSectionStatus(str, Enum):
    SEALED_CONTRACT_ONLY = "SEALED_CONTRACT_ONLY"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellStateP29HandoffStatus(str, Enum):
    READY_FOR_P2_9_CONTRACT_HANDOFF = "READY_FOR_P2_9_CONTRACT_HANDOFF"
    UNAVAILABLE_P2_9_REQUIRED = "UNAVAILABLE_P2_9_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellStateSectionValidationStatus(str, Enum):
    RECORDED_IN_REPORT = "RECORDED_IN_REPORT"
    NOT_RUN_AT_BUILD = "NOT_RUN_AT_BUILD"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellStateSectionSealTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    SECTION_SEAL_ONLY = "SECTION_SEAL_ONLY"
    SHELL_STATE_REPORTS_DOCS_SECTION_SEAL_ONLY = (
        "SHELL_STATE_REPORTS_DOCS_SECTION_SEAL_ONLY"
    )
    CONTRACT_INVENTORY_ONLY = "CONTRACT_INVENTORY_ONLY"
    COVERAGE_MATRIX_ONLY = "COVERAGE_MATRIX_ONLY"
    SECTION_READ_MODEL_ONLY = "SECTION_READ_MODEL_ONLY"
    SECTION_STATUS_ONLY = "SECTION_STATUS_ONLY"
    AVAILABILITY_ROLLUP_ONLY = "AVAILABILITY_ROLLUP_ONLY"
    RUNTIME_UNAVAILABLE_ROLLUP_ONLY = "RUNTIME_UNAVAILABLE_ROLLUP_ONLY"
    P2_9_HANDOFF_CONTRACT_ONLY = "P2_9_HANDOFF_CONTRACT_ONLY"
    VALIDATION_ROLLUP_ONLY = "VALIDATION_ROLLUP_ONLY"
    EVIDENCE_ROLLUP_ONLY = "EVIDENCE_ROLLUP_ONLY"
    CONTRACT_SCOPE_DEMO_ONLY = "CONTRACT_SCOPE_DEMO_ONLY"
    NO_LIVE_STATE_PROOF = "NO_LIVE_STATE_PROOF"
    NO_SYNC_RUNTIME_PROOF = "NO_SYNC_RUNTIME_PROOF"
    NO_GENERATION_PROOF = "NO_GENERATION_PROOF"
    NO_WRITE_PROOF = "NO_WRITE_PROOF"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_RELEASE_SEAL = "NOT_RELEASE_SEAL"
    NOT_P2_COMPLETE = "NOT_P2_COMPLETE"
    NOT_SHELL_COMPLETE = "NOT_SHELL_COMPLETE"
    NOT_LIVE_SHELL_STATE = "NOT_LIVE_SHELL_STATE"
    NOT_SHELL_RUNTIME = "NOT_SHELL_RUNTIME"
    NOT_SHELL_STATE_RUNTIME = "NOT_SHELL_STATE_RUNTIME"
    NOT_SYNC_RUNTIME = "NOT_SYNC_RUNTIME"
    NOT_STATE_RECONCILIATION_ENGINE = "NOT_STATE_RECONCILIATION_ENGINE"
    NOT_REPAIR_ACTION = "NOT_REPAIR_ACTION"
    NOT_AUTO_FIX = "NOT_AUTO_FIX"
    NOT_REFRESH_RUNTIME = "NOT_REFRESH_RUNTIME"
    NOT_PERSISTENT_STATE_STORE = "NOT_PERSISTENT_STATE_STORE"
    NOT_DATABASE_PERSISTENCE = "NOT_DATABASE_PERSISTENCE"
    NOT_STORAGE_WRITE = "NOT_STORAGE_WRITE"
    NOT_TRACE_WRITE = "NOT_TRACE_WRITE"
    NOT_MEMORY_WRITE = "NOT_MEMORY_WRITE"
    NOT_DOCS_WRITE = "NOT_DOCS_WRITE"
    NOT_REPORT_WRITE = "NOT_REPORT_WRITE"
    NOT_REPORT_GENERATOR = "NOT_REPORT_GENERATOR"
    NOT_DOCS_GENERATOR = "NOT_DOCS_GENERATOR"
    NOT_SUMMARY_GENERATOR = "NOT_SUMMARY_GENERATOR"
    NOT_REPORT_PUBLISHER = "NOT_REPORT_PUBLISHER"
    NOT_DOCS_PUBLISHER = "NOT_DOCS_PUBLISHER"
    NOT_AGENT_REPORTS_REPLACEMENT = "NOT_AGENT_REPORTS_REPLACEMENT"
    NOT_AGENT_GOVERNANCE_REPLACEMENT = "NOT_AGENT_GOVERNANCE_REPLACEMENT"
    NOT_DOCS_SOURCE_OF_TRUTH = "NOT_DOCS_SOURCE_OF_TRUTH"
    NOT_PRODUCT_UI = "NOT_PRODUCT_UI"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_CUSTOS_DECISION = "NOT_CUSTOS_DECISION"
    NOT_P2_9_IMPLEMENTATION = "NOT_P2_9_IMPLEMENTATION"
    NOT_P2_10_IMPLEMENTATION = "NOT_P2_10_IMPLEMENTATION"
    NOT_P2_11_IMPLEMENTATION = "NOT_P2_11_IMPLEMENTATION"
    NOT_P2_12_IMPLEMENTATION = "NOT_P2_12_IMPLEMENTATION"
    NOT_P2_13_IMPLEMENTATION = "NOT_P2_13_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_PRODUCT_DEMO = "NOT_PRODUCT_DEMO"
    NOT_INVENTED_PASS = "NOT_INVENTED_PASS"
    SECTION_SEAL_GATE_ONLY = "SECTION_SEAL_GATE_ONLY"


@dataclass(frozen=True)
class P28DSideEffectProof(_CanonicalMixin):
    shell_runtime_created: bool = False
    shell_state_runtime_created: bool = False
    shell_state_sync_runtime_created: bool = False
    state_reconciliation_engine_created: bool = False
    shell_state_mutated: bool = False
    runtime_state_mutated: bool = False
    sync_executed: bool = False
    repair_action_created: bool = False
    autofix_created: bool = False
    refresh_runtime_created: bool = False
    persistent_state_store_created: bool = False
    database_persistence_created: bool = False
    storage_written: bool = False
    trace_written: bool = False
    memory_written: bool = False
    docs_written: bool = False
    reports_written: bool = False
    report_generator_created: bool = False
    docs_generator_created: bool = False
    summary_generator_created: bool = False
    report_publisher_created: bool = False
    docs_publisher_created: bool = False
    agent_reports_replaced: bool = False
    agent_governance_replaced: bool = False
    docs_source_of_truth_created: bool = False
    product_ui_created: bool = False
    product_behavior_claimed: bool = False
    cli_runner_created: bool = False
    tui_runtime_created: bool = False
    command_execution_created: bool = False
    runtime_dispatch_created: bool = False
    permission_enforcement_created: bool = False
    custos_decisioning_created: bool = False
    approval_runtime_created: bool = False
    live_claimed: bool = False
    trace_verified_claimed: bool = False
    release_scope_claimed: bool = False
    p2_complete_claimed: bool = False
    shell_complete_claimed: bool = False
    p2_9_started: bool = False
    p2_10_started: bool = False
    p2_11_started: bool = False
    p2_12_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellStateSectionSealGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_summary_boundary_result_ref: str
    dependency_no_sync_runtime_boundary_ref: str
    dependency_no_generation_boundary_ref: str
    dependency_no_write_boundary_ref: str
    dependency_side_effect_proof_ref: str
    p2_8_a_evidence_ref: str
    p2_8_b_evidence_ref: str
    p2_8_c_evidence_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellStateSectionSealGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellStateSectionContractEntry(_CanonicalMixin):
    contract_entry_id: str
    schema_version: str
    section_id: str
    source_pack: str
    checkpoint_range: str
    contract_name: str
    contract_ref: str
    source_report_ref: str
    source_test_ref: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellStateSectionContractInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    source_packs: tuple[str, ...]
    contract_entries: tuple[ShellStateSectionContractEntry, ...]
    source_report_refs: tuple[str, ...]
    source_evidence_refs: tuple[str, ...]
    is_source_of_truth: bool
    duplicates_agent_governance: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class ShellStateSectionCoverageEntry(_CanonicalMixin):
    checkpoint_id: str
    capsule_name: str
    status: ShellStateSectionCoverageEntryStatus
    source_pack: str
    source_report_ref: str
    source_contract_ref: str
    source_tests_ref: str
    truth_label: str
    unavailable_reason: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellStateSectionCoverageMatrix(_CanonicalMixin):
    coverage_matrix_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    coverage_entries: tuple[ShellStateSectionCoverageEntry, ...]
    covered_checkpoint_range: str
    full_section_range: str
    does_invent_done: bool
    truth_label: str
    limitations: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True)
class ShellStateSectionReadModel(_CanonicalMixin):
    section_read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    section_status: ShellStateSectionStatus
    coverage_matrix_ref: str
    contract_inventory_ref: str
    availability_rollup_ref: str
    runtime_unavailable_rollup_ref: str
    p2_9_handoff_ref: str
    evidence_rollup_ref: str
    is_release_seal: bool
    claims_p2_complete: bool
    claims_shell_complete: bool
    claims_live_shell_state: bool
    truth_label: str
    limitations: tuple[str, ...]
    read_model_hash: str


@dataclass(frozen=True)
class ShellStateReportsDocsAvailabilityRollup(_CanonicalMixin):
    availability_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    available_contracts: tuple[str, ...]
    available_read_models: tuple[str, ...]
    available_summary_boundaries: tuple[str, ...]
    available_reports_docs_refs: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    enforces_permission: bool
    grants_permission: bool
    denies_permission: bool
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellStateRuntimeUnavailableRollup(_CanonicalMixin):
    runtime_unavailable_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    live_shell_state_runtime_unavailable: bool
    shell_state_sync_runtime_unavailable: bool
    state_reconciliation_unavailable: bool
    persistent_store_unavailable: bool
    trace_write_unavailable: bool
    memory_write_unavailable: bool
    storage_write_unavailable: bool
    docs_report_write_unavailable: bool
    generator_runtime_unavailable: bool
    product_ui_unavailable: bool
    p2_9_implementation_unavailable: bool
    unavailable_reasons: tuple[str, ...]
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellStateP29HandoffContract(_CanonicalMixin):
    handoff_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    handoff_to_pack: str
    handoff_to_section: str
    handoff_status: ShellStateP29HandoffStatus
    handoff_reason: str
    available_inputs: tuple[str, ...]
    required_next_work: tuple[str, ...]
    is_p2_9_implementation: bool
    starts_p2_9: bool
    truth_label: str
    limitations: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class ShellStateSectionValidationRollup(_CanonicalMixin):
    validation_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_validation_refs: tuple[str, ...]
    current_validation_refs: tuple[str, ...]
    validation_commands: tuple[str, ...]
    validation_statuses: tuple[str, ...]
    invented_pass: bool
    missing_validation_reason: str
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellStateSectionEvidenceRollup(_CanonicalMixin):
    evidence_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_packs: tuple[str, ...]
    source_reports: tuple[str, ...]
    source_commits: tuple[str, ...]
    source_contracts: tuple[str, ...]
    source_tests: tuple[str, ...]
    claims_trace_verified: bool
    replaces_agent_governance: bool
    truth_label: str
    limitations: tuple[str, ...]
    rollup_hash: str


@dataclass(frozen=True)
class ShellStateSectionContractScopeDemo(_CanonicalMixin):
    contract_scope_demo_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    demo_scope: str
    demo_inputs: tuple[str, ...]
    demo_outputs: tuple[str, ...]
    uses_live_runtime: bool
    is_product_demo: bool
    claims_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    demo_hash: str


@dataclass(frozen=True)
class ShellStateNoLiveStateProof(_CanonicalMixin):
    no_live_state_proof_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    live_shell_state_runtime_created: bool
    shell_runtime_created: bool
    shell_state_runtime_created: bool
    shell_state_mutated: bool
    runtime_state_mutated: bool
    claims_live_shell_state: bool
    proof_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    proof_hash: str


@dataclass(frozen=True)
class ShellStateNoSyncRuntimeProof(_CanonicalMixin):
    no_sync_runtime_proof_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    shell_state_sync_runtime_created: bool
    state_reconciliation_engine_created: bool
    sync_executed: bool
    repair_action_created: bool
    autofix_created: bool
    refresh_runtime_created: bool
    proof_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    proof_hash: str


@dataclass(frozen=True)
class ShellStateNoGenerationProof(_CanonicalMixin):
    no_generation_proof_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    report_generator_created: bool
    docs_generator_created: bool
    summary_generator_created: bool
    report_publisher_created: bool
    docs_publisher_created: bool
    generated_docs: bool
    generated_reports: bool
    generated_summary: bool
    proof_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    proof_hash: str


@dataclass(frozen=True)
class ShellStateNoWriteProof(_CanonicalMixin):
    no_write_proof_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    trace_written: bool
    memory_written: bool
    storage_written: bool
    database_written: bool
    docs_written: bool
    reports_written: bool
    proof_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    proof_hash: str


@dataclass(frozen=True)
class ShellStateSectionSealResult(_CanonicalMixin):
    section_seal_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    section_status: ShellStateSectionStatus
    section_seal_gate: ShellStateSectionSealGate
    contract_inventory: ShellStateSectionContractInventory
    coverage_matrix: ShellStateSectionCoverageMatrix
    section_read_model: ShellStateSectionReadModel
    availability_rollup: ShellStateReportsDocsAvailabilityRollup
    runtime_unavailable_rollup: ShellStateRuntimeUnavailableRollup
    p2_9_handoff_contract: ShellStateP29HandoffContract
    validation_rollup: ShellStateSectionValidationRollup
    evidence_rollup: ShellStateSectionEvidenceRollup
    contract_scope_demo: ShellStateSectionContractScopeDemo
    no_live_state_proof: ShellStateNoLiveStateProof
    no_sync_runtime_proof: ShellStateNoSyncRuntimeProof
    no_generation_proof: ShellStateNoGenerationProof
    no_write_proof: ShellStateNoWriteProof
    is_release_seal: bool
    claims_p2_complete: bool
    claims_shell_complete: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_product_behavior: bool
    claims_release_scope: bool
    truth_label: str
    limitations: tuple[str, ...]
    seal_result_hash: str


@dataclass(frozen=True)
class P28DShellStateSectionSealResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    full_section_coverage: tuple[str, ...]
    dependency_pack: str
    p2_8_a_evidence_ref: str
    p2_8_b_evidence_ref: str
    p2_8_c_evidence_ref: str
    p2_8_d_evidence_ref: str
    section_seal_gate: ShellStateSectionSealGate
    contract_inventory: ShellStateSectionContractInventory
    coverage_matrix: ShellStateSectionCoverageMatrix
    section_read_model: ShellStateSectionReadModel
    availability_rollup: ShellStateReportsDocsAvailabilityRollup
    runtime_unavailable_rollup: ShellStateRuntimeUnavailableRollup
    p2_9_handoff_contract: ShellStateP29HandoffContract
    validation_rollup: ShellStateSectionValidationRollup
    evidence_rollup: ShellStateSectionEvidenceRollup
    contract_scope_demo: ShellStateSectionContractScopeDemo
    no_live_state_proof: ShellStateNoLiveStateProof
    no_sync_runtime_proof: ShellStateNoSyncRuntimeProof
    no_generation_proof: ShellStateNoGenerationProof
    no_write_proof: ShellStateNoWriteProof
    section_seal_result: ShellStateSectionSealResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P28DSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    claims_p2_complete: bool
    claims_shell_complete: bool
    starts_future_work: bool
    result_hash: str


def _p2_8_a_evidence_ref(result: P28AShellStateFoundationResult) -> str:
    return f"{P2_8_A_REPORT_PATH}:{result.result_hash[:12]}"


def _p2_8_b_evidence_ref(result: P28BShellStateReadModelResult) -> str:
    return f"{P2_8_B_REPORT_PATH}:{result.result_hash[:12]}"


def _p2_8_c_evidence_ref(result: P28CShellStateSummaryResult) -> str:
    return f"{P2_8_C_REPORT_PATH}:{result.result_hash[:12]}"


def _summary_boundary_result_ref(result: P28CShellStateSummaryResult) -> str:
    boundary = result.boundary_result
    return (
        f"{boundary.boundary_result_id}:"
        f"hash={boundary.boundary_hash[:12]}"
    )


def _no_sync_boundary_ref(result: P28CShellStateSummaryResult) -> str:
    boundary = result.no_sync_runtime_boundary
    return f"{boundary.no_sync_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _no_generation_boundary_ref(result: P28CShellStateSummaryResult) -> str:
    boundary = result.no_generation_boundary
    return f"{boundary.no_generation_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _no_write_boundary_ref(result: P28CShellStateSummaryResult) -> str:
    boundary = result.no_write_boundary
    return f"{boundary.no_write_boundary_id}:hash={boundary.boundary_hash[:12]}"


def build_shell_state_section_seal_gate(
    summary_result: P28CShellStateSummaryResult | None = None,
) -> ShellStateSectionSealGate:
    if summary_result is None:
        summary_result = build_p2_8_c_shell_state_summary_result()
    assert_p2_8_c_summary_result_available(summary_result)
    payload: dict[str, Any] = {
        "gate_id": "p2_8_d_shell_state_section_seal_gate",
        "schema_version": P2_8_D_GATE_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "official_section_name": P2_8_D_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_8_D_DEPENDENCY_PACK,
        "dependency_report_ref": P2_8_C_REPORT_PATH,
        "dependency_commit_ref": P2_8_C_COMMIT_REF,
        "dependency_validation_ref": P2_8_C_VALIDATION_REF,
        "dependency_summary_boundary_result_ref": _summary_boundary_result_ref(
            summary_result
        ),
        "dependency_no_sync_runtime_boundary_ref": _no_sync_boundary_ref(
            summary_result
        ),
        "dependency_no_generation_boundary_ref": _no_generation_boundary_ref(
            summary_result
        ),
        "dependency_no_write_boundary_ref": _no_write_boundary_ref(summary_result),
        "dependency_side_effect_proof_ref": "P28CSideEffectProof:all_false",
        "p2_8_a_evidence_ref": P2_8_A_REPORT_PATH,
        "p2_8_b_evidence_ref": P2_8_B_REPORT_PATH,
        "p2_8_c_evidence_ref": P2_8_C_REPORT_PATH,
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellStateSectionSealGateStatus.READY,
        "truth_label": ShellStateSectionSealTruthBoundary.SECTION_SEAL_GATE_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate creates no live Shell state, sync, generator, or write runtime",
        ),
    }
    gate = ShellStateSectionSealGate(**payload, gate_hash=_hash_payload(payload))
    assert_section_gate_depends_on_p2_8_c(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def _build_contract_entry(
    checkpoint_id: str,
    capsule_name: str,
    source_pack: str,
    source_report_ref: str,
    source_test_ref: str,
    source_commit_ref: str,
    contract_ref: str,
) -> ShellStateSectionContractEntry:
    payload: dict[str, Any] = {
        "contract_entry_id": (
            f"p2_8_contract_entry_{checkpoint_id.replace('.', '_').lower()}"
        ),
        "schema_version": P2_8_D_ENTRY_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "source_pack": source_pack,
        "checkpoint_range": checkpoint_id,
        "contract_name": capsule_name,
        "contract_ref": contract_ref,
        "source_report_ref": source_report_ref,
        "source_test_ref": source_test_ref,
        "truth_label": ShellStateSectionSealTruthBoundary.REPORT_ONLY.value,
        "limitations": (
            "entry references source evidence only",
            "entry does not duplicate source-of-truth contracts",
        ),
    }
    return ShellStateSectionContractEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_shell_state_section_contract_inventory() -> ShellStateSectionContractInventory:
    entries = tuple(
        _build_contract_entry(
            checkpoint_id,
            capsule_name,
            source_pack,
            source_report_ref,
            source_test_ref,
            source_commit_ref,
            contract_ref,
        )
        for (
            checkpoint_id,
            capsule_name,
            source_pack,
            source_report_ref,
            source_test_ref,
            source_commit_ref,
            contract_ref,
        ) in _CHECKPOINT_SPECS
    )
    payload: dict[str, Any] = {
        "inventory_id": "p2_8_d_shell_state_section_contract_inventory",
        "schema_version": P2_8_D_INVENTORY_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "official_section_name": P2_8_D_OFFICIAL_SECTION_NAME,
        "source_packs": (
            P2_8_A_PACK_ID,
            P2_8_B_PACK_ID,
            P2_8_C_PACK_ID,
            P2_8_D_PACK_ID,
        ),
        "contract_entries": entries,
        "source_report_refs": (
            P2_8_A_REPORT_PATH,
            P2_8_B_REPORT_PATH,
            P2_8_C_REPORT_PATH,
            P2_8_D_REPORT_PATH,
        ),
        "source_evidence_refs": (
            P2_8_A_VALIDATION_REF,
            P2_8_B_VALIDATION_REF,
            P2_8_C_VALIDATION_REF,
            P2_8_D_VALIDATION_REF,
        ),
        "is_source_of_truth": False,
        "duplicates_agent_governance": False,
        "truth_label": ShellStateSectionSealTruthBoundary.CONTRACT_INVENTORY_ONLY.value,
        "limitations": (
            "inventory references P2.8-A/B/C/D evidence by ref",
            "inventory does not duplicate source evidence or agent governance",
        ),
    }
    inventory = ShellStateSectionContractInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    assert_contract_inventory_is_not_source_of_truth_duplication(inventory)
    return inventory


def _build_coverage_entry(
    checkpoint_id: str,
    capsule_name: str,
    source_pack: str,
    source_report_ref: str,
    source_test_ref: str,
    source_contract_ref: str,
) -> ShellStateSectionCoverageEntry:
    payload: dict[str, Any] = {
        "checkpoint_id": checkpoint_id,
        "capsule_name": capsule_name,
        "status": ShellStateSectionCoverageEntryStatus.DONE,
        "source_pack": source_pack,
        "source_report_ref": source_report_ref,
        "source_contract_ref": source_contract_ref,
        "source_tests_ref": source_test_ref,
        "truth_label": ShellStateSectionSealTruthBoundary.REPORT_ONLY.value,
        "unavailable_reason": (
            _RUNTIME_UNAVAILABLE_REASON if source_pack == P2_8_D_PACK_ID else ""
        ),
        "limitations": (
            "coverage entry references recorded evidence only",
            "status DONE requires source pack evidence",
        ),
    }
    return ShellStateSectionCoverageEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_shell_state_section_coverage_matrix() -> ShellStateSectionCoverageMatrix:
    entries = tuple(
        _build_coverage_entry(
            checkpoint_id,
            capsule_name,
            source_pack,
            source_report_ref,
            source_test_ref,
            source_contract_ref,
        )
        for (
            checkpoint_id,
            capsule_name,
            source_pack,
            source_report_ref,
            source_test_ref,
            _source_commit_ref,
            source_contract_ref,
        ) in _CHECKPOINT_SPECS
    )
    payload: dict[str, Any] = {
        "coverage_matrix_id": "p2_8_d_shell_state_section_coverage_matrix",
        "schema_version": P2_8_D_COVERAGE_MATRIX_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "official_section_name": P2_8_D_OFFICIAL_SECTION_NAME,
        "coverage_entries": entries,
        "covered_checkpoint_range": "P2.8.16-P2.8.20",
        "full_section_range": "P2.8.0-P2.8.20",
        "does_invent_done": False,
        "truth_label": ShellStateSectionSealTruthBoundary.COVERAGE_MATRIX_ONLY.value,
        "limitations": (
            "coverage matrix indexes evidence by checkpoint",
            "matrix does not invent DONE without source evidence",
        ),
    }
    matrix = ShellStateSectionCoverageMatrix(
        **payload,
        matrix_hash=_hash_payload(payload),
    )
    assert_coverage_matrix_does_not_invent_done(matrix)
    return matrix


def build_shell_state_section_read_model(
    inventory: ShellStateSectionContractInventory | None = None,
    coverage_matrix: ShellStateSectionCoverageMatrix | None = None,
) -> ShellStateSectionReadModel:
    if inventory is None:
        inventory = build_shell_state_section_contract_inventory()
    if coverage_matrix is None:
        coverage_matrix = build_shell_state_section_coverage_matrix()
    payload: dict[str, Any] = {
        "section_read_model_id": "p2_8_d_shell_state_section_read_model",
        "schema_version": P2_8_D_READ_MODEL_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "official_section_name": P2_8_D_OFFICIAL_SECTION_NAME,
        "section_status": ShellStateSectionStatus.SEALED_CONTRACT_ONLY,
        "coverage_matrix_ref": coverage_matrix.coverage_matrix_id,
        "contract_inventory_ref": inventory.inventory_id,
        "availability_rollup_ref": "p2_8_d_shell_state_reports_docs_availability_rollup",
        "runtime_unavailable_rollup_ref": (
            "p2_8_d_shell_state_runtime_unavailable_rollup"
        ),
        "p2_9_handoff_ref": "p2_8_d_shell_state_p2_9_handoff_contract",
        "evidence_rollup_ref": "p2_8_d_shell_state_section_evidence_rollup",
        "is_release_seal": False,
        "claims_p2_complete": False,
        "claims_shell_complete": False,
        "claims_live_shell_state": False,
        "truth_label": ShellStateSectionSealTruthBoundary.SECTION_READ_MODEL_ONLY.value,
        "limitations": (
            "section read model is contract-only",
            "section seal is not release seal, Shell complete, P2 complete, or live Shell state",
        ),
    }
    read_model = ShellStateSectionReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )
    assert_shell_state_section_complete_is_not_live_shell_state(read_model)
    assert_p2_8_complete_is_not_p2_complete(read_model)
    return read_model


def build_shell_state_reports_docs_availability_rollup() -> (
    ShellStateReportsDocsAvailabilityRollup
):
    payload: dict[str, Any] = {
        "availability_rollup_id": "p2_8_d_shell_state_reports_docs_availability_rollup",
        "schema_version": P2_8_D_AVAILABILITY_ROLLUP_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "available_contracts": (
            "ShellStateFoundationResult",
            "ShellStateReadModelExpansionResult",
            "ShellStateSummaryBoundaryResult",
            "ShellStateSectionSealResult",
        ),
        "available_read_models": (
            "ShellSectionStatusReadModel",
            "ShellStateSnapshotReadModel",
            "ShellReportIndexReadModel",
            "ShellDocsIndexReadModel",
            "ShellStateSectionReadModel",
        ),
        "available_summary_boundaries": (
            "ShellStateSummaryBoundaryResult",
            "ShellSummaryNoSyncRuntimeBoundary",
            "ShellSummaryNoGenerationBoundary",
            "ShellSummaryNoWriteBoundary",
        ),
        "available_reports_docs_refs": (
            P2_8_A_REPORT_PATH,
            P2_8_B_REPORT_PATH,
            P2_8_C_REPORT_PATH,
            P2_8_D_REPORT_PATH,
            "agent/REPORTS.md",
        ),
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "enforces_permission": False,
        "grants_permission": False,
        "denies_permission": False,
        "truth_label": ShellStateSectionSealTruthBoundary.AVAILABILITY_ROLLUP_ONLY.value,
        "limitations": (
            "contract availability is not live Shell state",
            "availability rollup does not enforce permission",
        ),
    }
    rollup = ShellStateReportsDocsAvailabilityRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_availability_rollup_is_not_permission_enforcement(rollup)
    return rollup


def build_shell_state_runtime_unavailable_rollup() -> (
    ShellStateRuntimeUnavailableRollup
):
    payload: dict[str, Any] = {
        "runtime_unavailable_rollup_id": (
            "p2_8_d_shell_state_runtime_unavailable_rollup"
        ),
        "schema_version": P2_8_D_RUNTIME_UNAVAILABLE_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "live_shell_state_runtime_unavailable": True,
        "shell_state_sync_runtime_unavailable": True,
        "state_reconciliation_unavailable": True,
        "persistent_store_unavailable": True,
        "trace_write_unavailable": True,
        "memory_write_unavailable": True,
        "storage_write_unavailable": True,
        "docs_report_write_unavailable": True,
        "generator_runtime_unavailable": True,
        "product_ui_unavailable": True,
        "p2_9_implementation_unavailable": True,
        "unavailable_reasons": (
            _RUNTIME_UNAVAILABLE_REASON,
            _P2_9_HANDOFF_REASON,
        ),
        "truth_label": (
            ShellStateSectionSealTruthBoundary.RUNTIME_UNAVAILABLE_ROLLUP_ONLY.value
        ),
        "limitations": (
            "runtime unavailable rollup is honesty metadata only",
            "rollup creates no runtime",
        ),
    }
    return ShellStateRuntimeUnavailableRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )


def build_shell_state_p2_9_handoff_contract() -> ShellStateP29HandoffContract:
    payload: dict[str, Any] = {
        "handoff_id": "p2_8_d_shell_state_p2_9_handoff_contract",
        "schema_version": P2_8_D_P2_9_HANDOFF_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "handoff_to_pack": P2_8_D_NEXT_PACK,
        "handoff_to_section": P2_8_D_NEXT_SECTION,
        "handoff_status": ShellStateP29HandoffStatus.READY_FOR_P2_9_CONTRACT_HANDOFF,
        "handoff_reason": _P2_9_HANDOFF_REASON,
        "available_inputs": (
            "ShellStateSectionSealResult",
            "ShellStateSectionContractInventory",
            "ShellStateSectionCoverageMatrix",
            P2_8_D_REPORT_PATH,
        ),
        "required_next_work": (
            "P2.9.0-P2.9.5 Shell Exit Seal Foundation",
        ),
        "is_p2_9_implementation": False,
        "starts_p2_9": False,
        "truth_label": ShellStateSectionSealTruthBoundary.P2_9_HANDOFF_CONTRACT_ONLY.value,
        "limitations": (
            "P2.9 handoff is a contract boundary only",
            "handoff does not start P2.9 or create Shell Exit Seal behavior",
        ),
    }
    handoff = ShellStateP29HandoffContract(
        **payload,
        handoff_hash=_hash_payload(payload),
    )
    assert_p2_9_handoff_is_not_p2_9_implementation(handoff)
    return handoff


def build_shell_state_section_validation_rollup() -> ShellStateSectionValidationRollup:
    payload: dict[str, Any] = {
        "validation_rollup_id": "p2_8_d_shell_state_section_validation_rollup",
        "schema_version": P2_8_D_VALIDATION_ROLLUP_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "source_validation_refs": (
            P2_8_A_VALIDATION_REF,
            P2_8_B_VALIDATION_REF,
            P2_8_C_VALIDATION_REF,
            P2_8_D_VALIDATION_REF,
        ),
        "current_validation_refs": (P2_8_D_VALIDATION_REF,),
        "validation_commands": P2_8_D_VALIDATION_COMMANDS,
        "validation_statuses": ("NOT_RUN_AT_BUILD",),
        "invented_pass": False,
        "missing_validation_reason": "",
        "truth_label": ShellStateSectionSealTruthBoundary.VALIDATION_ROLLUP_ONLY.value,
        "limitations": (
            "validation results are recorded in the agent report after commands run",
            "validation rollup does not invent PASS",
        ),
    }
    rollup = ShellStateSectionValidationRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_validation_rollup_does_not_invent_pass(rollup)
    return rollup


def build_shell_state_section_evidence_rollup() -> ShellStateSectionEvidenceRollup:
    payload: dict[str, Any] = {
        "evidence_rollup_id": "p2_8_d_shell_state_section_evidence_rollup",
        "schema_version": P2_8_D_EVIDENCE_ROLLUP_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "source_packs": (
            P2_8_A_PACK_ID,
            P2_8_B_PACK_ID,
            P2_8_C_PACK_ID,
            P2_8_D_PACK_ID,
        ),
        "source_reports": (
            P2_8_A_REPORT_PATH,
            P2_8_B_REPORT_PATH,
            P2_8_C_REPORT_PATH,
            P2_8_D_REPORT_PATH,
        ),
        "source_commits": (
            P2_8_A_COMMIT_REF,
            P2_8_B_COMMIT_REF,
            P2_8_C_COMMIT_REF,
            "PENDING_AT_BUILD",
        ),
        "source_contracts": (
            "ShellStateFoundationResult",
            "ShellStateReadModelExpansionResult",
            "ShellStateSummaryBoundaryResult",
            "ShellStateSectionSealResult",
        ),
        "source_tests": (
            P2_8_A_TEST_REF,
            P2_8_B_TEST_REF,
            P2_8_C_TEST_REF,
            P2_8_D_TEST_REF,
        ),
        "claims_trace_verified": False,
        "replaces_agent_governance": False,
        "truth_label": ShellStateSectionSealTruthBoundary.EVIDENCE_ROLLUP_ONLY.value,
        "limitations": (
            "evidence rollup references reports/commits/tests by ref",
            "rollup does not claim TRACE_VERIFIED or replace agent governance",
        ),
    }
    rollup = ShellStateSectionEvidenceRollup(
        **payload,
        rollup_hash=_hash_payload(payload),
    )
    assert_evidence_rollup_is_not_trace_verified(rollup)
    return rollup


def build_shell_state_section_contract_scope_demo(
    inventory: ShellStateSectionContractInventory | None = None,
    read_model: ShellStateSectionReadModel | None = None,
) -> ShellStateSectionContractScopeDemo:
    if inventory is None:
        inventory = build_shell_state_section_contract_inventory()
    if read_model is None:
        read_model = build_shell_state_section_read_model(inventory=inventory)
    payload: dict[str, Any] = {
        "contract_scope_demo_id": "p2_8_d_shell_state_section_contract_scope_demo",
        "schema_version": P2_8_D_DEMO_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "demo_scope": "CONTRACT_ONLY",
        "demo_inputs": (
            inventory.inventory_id,
            read_model.section_read_model_id,
        ),
        "demo_outputs": ("serialize_p2_8_d_result",),
        "uses_live_runtime": False,
        "is_product_demo": False,
        "claims_product_behavior": False,
        "truth_label": ShellStateSectionSealTruthBoundary.CONTRACT_SCOPE_DEMO_ONLY.value,
        "limitations": (
            "contract-scope demo validates serialization and contract shape only",
            "demo is not product demo or live demo",
        ),
    }
    demo = ShellStateSectionContractScopeDemo(
        **payload,
        demo_hash=_hash_payload(payload),
    )
    assert_contract_scope_demo_is_not_product_demo(demo)
    return demo


def build_shell_state_no_live_state_proof() -> ShellStateNoLiveStateProof:
    payload: dict[str, Any] = {
        "no_live_state_proof_id": "p2_8_d_shell_state_no_live_state_proof",
        "schema_version": P2_8_D_NO_LIVE_STATE_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "live_shell_state_runtime_created": False,
        "shell_runtime_created": False,
        "shell_state_runtime_created": False,
        "shell_state_mutated": False,
        "runtime_state_mutated": False,
        "claims_live_shell_state": False,
        "proof_active": True,
        "truth_label": ShellStateSectionSealTruthBoundary.NO_LIVE_STATE_PROOF.value,
        "limitations": (
            "proof records absence of live Shell state at P2.8-D scope",
            "proof is not live Shell state",
        ),
    }
    proof = ShellStateNoLiveStateProof(**payload, proof_hash=_hash_payload(payload))
    assert_no_live_state_proof_is_active(proof)
    return proof


def build_shell_state_no_sync_runtime_proof() -> ShellStateNoSyncRuntimeProof:
    payload: dict[str, Any] = {
        "no_sync_runtime_proof_id": "p2_8_d_shell_state_no_sync_runtime_proof",
        "schema_version": P2_8_D_NO_SYNC_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "shell_state_sync_runtime_created": False,
        "state_reconciliation_engine_created": False,
        "sync_executed": False,
        "repair_action_created": False,
        "autofix_created": False,
        "refresh_runtime_created": False,
        "proof_active": True,
        "truth_label": ShellStateSectionSealTruthBoundary.NO_SYNC_RUNTIME_PROOF.value,
        "limitations": (
            "proof records absence of sync/reconciliation/repair at P2.8-D scope",
            "proof is not sync runtime",
        ),
    }
    proof = ShellStateNoSyncRuntimeProof(**payload, proof_hash=_hash_payload(payload))
    assert_no_sync_runtime_proof_is_active(proof)
    return proof


def build_shell_state_no_generation_proof() -> ShellStateNoGenerationProof:
    payload: dict[str, Any] = {
        "no_generation_proof_id": "p2_8_d_shell_state_no_generation_proof",
        "schema_version": P2_8_D_NO_GENERATION_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "report_generator_created": False,
        "docs_generator_created": False,
        "summary_generator_created": False,
        "report_publisher_created": False,
        "docs_publisher_created": False,
        "generated_docs": False,
        "generated_reports": False,
        "generated_summary": False,
        "proof_active": True,
        "truth_label": ShellStateSectionSealTruthBoundary.NO_GENERATION_PROOF.value,
        "limitations": (
            "proof records absence of generator/publisher runtime at P2.8-D scope",
            "proof is not generator runtime",
        ),
    }
    proof = ShellStateNoGenerationProof(**payload, proof_hash=_hash_payload(payload))
    assert_no_generation_proof_is_active(proof)
    return proof


def build_shell_state_no_write_proof() -> ShellStateNoWriteProof:
    payload: dict[str, Any] = {
        "no_write_proof_id": "p2_8_d_shell_state_no_write_proof",
        "schema_version": P2_8_D_NO_WRITE_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "trace_written": False,
        "memory_written": False,
        "storage_written": False,
        "database_written": False,
        "docs_written": False,
        "reports_written": False,
        "proof_active": True,
        "truth_label": ShellStateSectionSealTruthBoundary.NO_WRITE_PROOF.value,
        "limitations": (
            "proof records absence of trace/memory/storage/docs/report writes",
            "proof is not write layer",
        ),
    }
    proof = ShellStateNoWriteProof(**payload, proof_hash=_hash_payload(payload))
    assert_no_write_proof_is_active(proof)
    return proof


def build_shell_state_section_seal_result(
    gate: ShellStateSectionSealGate | None = None,
    inventory: ShellStateSectionContractInventory | None = None,
    coverage_matrix: ShellStateSectionCoverageMatrix | None = None,
    read_model: ShellStateSectionReadModel | None = None,
    availability_rollup: ShellStateReportsDocsAvailabilityRollup | None = None,
    runtime_unavailable_rollup: ShellStateRuntimeUnavailableRollup | None = None,
    p2_9_handoff_contract: ShellStateP29HandoffContract | None = None,
    validation_rollup: ShellStateSectionValidationRollup | None = None,
    evidence_rollup: ShellStateSectionEvidenceRollup | None = None,
    contract_scope_demo: ShellStateSectionContractScopeDemo | None = None,
    no_live_state_proof: ShellStateNoLiveStateProof | None = None,
    no_sync_runtime_proof: ShellStateNoSyncRuntimeProof | None = None,
    no_generation_proof: ShellStateNoGenerationProof | None = None,
    no_write_proof: ShellStateNoWriteProof | None = None,
) -> ShellStateSectionSealResult:
    if gate is None:
        gate = build_shell_state_section_seal_gate()
    if inventory is None:
        inventory = build_shell_state_section_contract_inventory()
    if coverage_matrix is None:
        coverage_matrix = build_shell_state_section_coverage_matrix()
    if read_model is None:
        read_model = build_shell_state_section_read_model(inventory, coverage_matrix)
    if availability_rollup is None:
        availability_rollup = build_shell_state_reports_docs_availability_rollup()
    if runtime_unavailable_rollup is None:
        runtime_unavailable_rollup = build_shell_state_runtime_unavailable_rollup()
    if p2_9_handoff_contract is None:
        p2_9_handoff_contract = build_shell_state_p2_9_handoff_contract()
    if validation_rollup is None:
        validation_rollup = build_shell_state_section_validation_rollup()
    if evidence_rollup is None:
        evidence_rollup = build_shell_state_section_evidence_rollup()
    if contract_scope_demo is None:
        contract_scope_demo = build_shell_state_section_contract_scope_demo(
            inventory=inventory,
            read_model=read_model,
        )
    if no_live_state_proof is None:
        no_live_state_proof = build_shell_state_no_live_state_proof()
    if no_sync_runtime_proof is None:
        no_sync_runtime_proof = build_shell_state_no_sync_runtime_proof()
    if no_generation_proof is None:
        no_generation_proof = build_shell_state_no_generation_proof()
    if no_write_proof is None:
        no_write_proof = build_shell_state_no_write_proof()
    payload: dict[str, Any] = {
        "section_seal_result_id": "p2_8_d_shell_state_section_seal_result",
        "schema_version": P2_8_D_SECTION_SEAL_RESULT_VERSION,
        "section_id": P2_8_D_SECTION_ID,
        "created_for_pack": P2_8_D_PACK_ID,
        "official_section_name": P2_8_D_OFFICIAL_SECTION_NAME,
        "section_status": ShellStateSectionStatus.SEALED_CONTRACT_ONLY,
        "section_seal_gate": gate,
        "contract_inventory": inventory,
        "coverage_matrix": coverage_matrix,
        "section_read_model": read_model,
        "availability_rollup": availability_rollup,
        "runtime_unavailable_rollup": runtime_unavailable_rollup,
        "p2_9_handoff_contract": p2_9_handoff_contract,
        "validation_rollup": validation_rollup,
        "evidence_rollup": evidence_rollup,
        "contract_scope_demo": contract_scope_demo,
        "no_live_state_proof": no_live_state_proof,
        "no_sync_runtime_proof": no_sync_runtime_proof,
        "no_generation_proof": no_generation_proof,
        "no_write_proof": no_write_proof,
        "is_release_seal": False,
        "claims_p2_complete": False,
        "claims_shell_complete": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_product_behavior": False,
        "claims_release_scope": False,
        "truth_label": ShellStateSectionSealTruthBoundary.SECTION_SEAL_ONLY.value,
        "limitations": (
            "section seal is not release seal",
            "P2.8 complete is not P2 complete",
            "Shell State section complete is not live Shell state",
        ),
    }
    result = ShellStateSectionSealResult(
        **payload,
        seal_result_hash=_hash_payload(payload),
    )
    assert_section_seal_is_not_release_seal(result)
    return result


def build_p2_8_d_side_effect_proof() -> P28DSideEffectProof:
    return P28DSideEffectProof()


def build_p2_8_d_shell_state_section_seal_result() -> P28DShellStateSectionSealResult:
    foundation = build_p2_8_a_shell_state_foundation_result()
    read_model_result = build_p2_8_b_shell_state_read_model_result()
    summary_result = build_p2_8_c_shell_state_summary_result()
    gate = build_shell_state_section_seal_gate(summary_result)
    inventory = build_shell_state_section_contract_inventory()
    coverage_matrix = build_shell_state_section_coverage_matrix()
    read_model = build_shell_state_section_read_model(inventory, coverage_matrix)
    availability_rollup = build_shell_state_reports_docs_availability_rollup()
    runtime_unavailable_rollup = build_shell_state_runtime_unavailable_rollup()
    p2_9_handoff = build_shell_state_p2_9_handoff_contract()
    validation_rollup = build_shell_state_section_validation_rollup()
    evidence_rollup = build_shell_state_section_evidence_rollup()
    contract_scope_demo = build_shell_state_section_contract_scope_demo(
        inventory, read_model
    )
    no_live_state_proof = build_shell_state_no_live_state_proof()
    no_sync_runtime_proof = build_shell_state_no_sync_runtime_proof()
    no_generation_proof = build_shell_state_no_generation_proof()
    no_write_proof = build_shell_state_no_write_proof()
    section_seal_result = build_shell_state_section_seal_result(
        gate=gate,
        inventory=inventory,
        coverage_matrix=coverage_matrix,
        read_model=read_model,
        availability_rollup=availability_rollup,
        runtime_unavailable_rollup=runtime_unavailable_rollup,
        p2_9_handoff_contract=p2_9_handoff,
        validation_rollup=validation_rollup,
        evidence_rollup=evidence_rollup,
        contract_scope_demo=contract_scope_demo,
        no_live_state_proof=no_live_state_proof,
        no_sync_runtime_proof=no_sync_runtime_proof,
        no_generation_proof=no_generation_proof,
        no_write_proof=no_write_proof,
    )
    side_effects = build_p2_8_d_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_8_D_RESULT_VERSION,
        "pack_id": P2_8_D_PACK_ID,
        "section_id": P2_8_D_SECTION_ID,
        "official_section_name": P2_8_D_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_8_D_PACK_CHECKPOINT_IDS,
        "full_section_coverage": P2_8_D_FULL_SECTION_CHECKPOINTS,
        "dependency_pack": P2_8_D_DEPENDENCY_PACK,
        "p2_8_a_evidence_ref": _p2_8_a_evidence_ref(foundation),
        "p2_8_b_evidence_ref": _p2_8_b_evidence_ref(read_model_result),
        "p2_8_c_evidence_ref": _p2_8_c_evidence_ref(summary_result),
        "p2_8_d_evidence_ref": P2_8_D_REPORT_PATH,
        "section_seal_gate": gate,
        "contract_inventory": inventory,
        "coverage_matrix": coverage_matrix,
        "section_read_model": read_model,
        "availability_rollup": availability_rollup,
        "runtime_unavailable_rollup": runtime_unavailable_rollup,
        "p2_9_handoff_contract": p2_9_handoff,
        "validation_rollup": validation_rollup,
        "evidence_rollup": evidence_rollup,
        "contract_scope_demo": contract_scope_demo,
        "no_live_state_proof": no_live_state_proof,
        "no_sync_runtime_proof": no_sync_runtime_proof,
        "no_generation_proof": no_generation_proof,
        "no_write_proof": no_write_proof,
        "section_seal_result": section_seal_result,
        "truth_labels": tuple(
            label.value for label in ShellStateSectionSealTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_8_D_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "claims_p2_complete": False,
        "claims_shell_complete": False,
        "starts_future_work": False,
    }
    result = P28DShellStateSectionSealResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_8_d_does_not_start_future_work(result)
    assert_p2_8_d_side_effects_all_false(result.side_effect_proof)
    assert_contract_inventory_is_not_source_of_truth_duplication(result.contract_inventory)
    return result


def serialize_p2_8_d_result(
    result: P28DShellStateSectionSealResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_d_shell_state_section_seal_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_state_section_seal_summary(
    result: P28DShellStateSectionSealResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_d_shell_state_section_seal_result()
    unavailable = result.runtime_unavailable_rollup
    handoff = result.p2_9_handoff_contract
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.section_seal_gate.gate_status.value}",
            f"section_status={result.section_read_model.section_status.value}",
            f"inventory_entries={len(result.contract_inventory.contract_entries)}",
            f"coverage_entries={len(result.coverage_matrix.coverage_entries)}",
            f"unavailable_capabilities={len(unavailable.unavailable_reasons)}",
            f"next={result.next_pack}",
            f"handoff_to={handoff.handoff_to_pack}",
            f"live={str(result.claims_live).lower()}",
            f"trace_verified={str(result.claims_trace_verified).lower()}",
            f"shell_complete={str(result.claims_shell_complete).lower()}",
            f"p2_complete={str(result.claims_p2_complete).lower()}",
            f"product_behavior={str(result.claims_product_behavior).lower()}",
            f"p2_9_started={str(handoff.starts_p2_9).lower()}",
        )
    )


def assert_p2_8_c_summary_result_available(
    result: P28CShellStateSummaryResult,
) -> None:
    if result.pack_id != P2_8_C_PACK_ID or result.starts_future_work:
        _reject(
            "P2.8-D requires P2.8-C summary result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.next_pack != P2_8_D_PACK_ID:
        _reject(
            "P2.8-D requires P2.8-C result pointing to P2.8-D",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.side_effect_proof.p2_8_d_started:
        _reject(
            "P2.8-C must not have started P2.8-D",
            field="side_effect_proof",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_gate_depends_on_p2_8_c(
    gate: ShellStateSectionSealGate,
) -> None:
    if (
        gate.dependency_pack != P2_8_D_DEPENDENCY_PACK
        or not gate.repo_evidence_gate_passed
    ):
        _reject(
            "P2.8-D section seal gate must depend on passed P2.8-C repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        not gate.dependency_summary_boundary_result_ref
        or not gate.dependency_no_sync_runtime_boundary_ref
        or not gate.dependency_no_generation_boundary_ref
        or not gate.dependency_no_write_boundary_ref
        or not gate.dependency_side_effect_proof_ref
    ):
        _reject(
            "P2.8-D gate must reference P2.8-C summary boundary and safety boundaries",
            field="dependency_summary_boundary_result_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellStateSectionSealGate,
) -> None:
    if (
        gate.omni_evidence_required
        or not gate.omni_evidence_ignored_by_operator_instruction
    ):
        _reject(
            "OMNI evidence must be ignored as hard gate for P2.8-D dispatch",
            field="omni_evidence_required",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_seal_is_not_release_seal(
    result: ShellStateSectionSealResult,
) -> None:
    if (
        result.is_release_seal
        or result.claims_live
        or result.claims_trace_verified
        or result.claims_shell_complete
        or result.claims_p2_complete
        or result.claims_product_behavior
        or result.claims_release_scope
    ):
        _reject(
            "P2.8-D section seal must not claim release/live/Shell/P2/product behavior",
            field="is_release_seal",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_shell_state_section_complete_is_not_live_shell_state(
    read_model: ShellStateSectionReadModel,
) -> None:
    if read_model.is_release_seal or read_model.claims_live_shell_state:
        _reject(
            "P2.8-D read model must not claim live Shell state or release seal",
            field="claims_live_shell_state",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_complete_is_not_p2_complete(
    read_model: ShellStateSectionReadModel,
) -> None:
    if read_model.claims_p2_complete or read_model.claims_shell_complete:
        _reject(
            "P2.8 completion must not claim P2 or Shell completion",
            field="claims_p2_complete",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_contract_scope_demo_is_not_product_demo(
    demo: ShellStateSectionContractScopeDemo,
) -> None:
    if demo.is_product_demo or demo.uses_live_runtime or demo.claims_product_behavior:
        _reject(
            "P2.8-D contract-scope demo must not be product/live/runtime demo",
            field="is_product_demo",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_9_handoff_is_not_p2_9_implementation(
    handoff: ShellStateP29HandoffContract,
) -> None:
    if handoff.starts_p2_9 or handoff.is_p2_9_implementation:
        _reject(
            "P2.9 handoff contract must not start or implement P2.9",
            field="starts_p2_9",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_validation_rollup_does_not_invent_pass(
    rollup: ShellStateSectionValidationRollup,
) -> None:
    if rollup.invented_pass:
        _reject(
            "P2.8-D validation rollup must not invent PASS",
            field="invented_pass",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_evidence_rollup_is_not_trace_verified(
    rollup: ShellStateSectionEvidenceRollup,
) -> None:
    if rollup.claims_trace_verified or rollup.replaces_agent_governance:
        _reject(
            "P2.8-D evidence rollup must not claim TRACE_VERIFIED or replace governance",
            field="claims_trace_verified",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_availability_rollup_is_not_permission_enforcement(
    rollup: ShellStateReportsDocsAvailabilityRollup,
) -> None:
    if rollup.enforces_permission or rollup.grants_permission or rollup.denies_permission:
        _reject(
            "P2.8-D availability rollup must not enforce/grant/deny permission",
            field="enforces_permission",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_coverage_matrix_does_not_invent_done(
    matrix: ShellStateSectionCoverageMatrix,
) -> None:
    if matrix.does_invent_done:
        _reject(
            "P2.8-D coverage matrix must not invent DONE",
            field="does_invent_done",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_live_state_proof_is_active(proof: ShellStateNoLiveStateProof) -> None:
    if (
        not proof.proof_active
        or proof.live_shell_state_runtime_created
        or proof.shell_runtime_created
        or proof.shell_state_runtime_created
        or proof.shell_state_mutated
        or proof.runtime_state_mutated
        or proof.claims_live_shell_state
    ):
        _reject(
            "P2.8-D no-live-state proof must be active with all live fields false",
            field="proof_active",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_sync_runtime_proof_is_active(proof: ShellStateNoSyncRuntimeProof) -> None:
    if (
        not proof.proof_active
        or proof.shell_state_sync_runtime_created
        or proof.state_reconciliation_engine_created
        or proof.sync_executed
        or proof.repair_action_created
        or proof.autofix_created
        or proof.refresh_runtime_created
    ):
        _reject(
            "P2.8-D no-sync-runtime proof must be active with all sync fields false",
            field="proof_active",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_generation_proof_is_active(proof: ShellStateNoGenerationProof) -> None:
    if (
        not proof.proof_active
        or proof.report_generator_created
        or proof.docs_generator_created
        or proof.summary_generator_created
        or proof.report_publisher_created
        or proof.docs_publisher_created
        or proof.generated_docs
        or proof.generated_reports
        or proof.generated_summary
    ):
        _reject(
            "P2.8-D no-generation proof must be active with all generation fields false",
            field="proof_active",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_write_proof_is_active(proof: ShellStateNoWriteProof) -> None:
    if (
        not proof.proof_active
        or proof.trace_written
        or proof.memory_written
        or proof.storage_written
        or proof.database_written
        or proof.docs_written
        or proof.reports_written
    ):
        _reject(
            "P2.8-D no-write proof must be active with all write fields false",
            field="proof_active",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_d_does_not_start_future_work(
    result: P28DShellStateSectionSealResult,
) -> None:
    if result.next_pack != P2_8_D_NEXT_PACK or result.starts_future_work:
        _reject(
            "P2.8-D must hand off to P2.9-A without starting future work",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    proof = result.side_effect_proof
    if (
        proof.p2_9_started
        or proof.p2_10_started
        or proof.p2_11_started
        or proof.p2_12_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.8-D side-effect proof must not start P2.9/P2.10/P2.11/P2.12/P2.13",
            field="side_effect_proof",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_d_side_effects_all_false(proof: P28DSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name) is not False:
            _reject(
                "P2.8-D side-effect proof booleans must all be false",
                field=field.name,
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_contract_inventory_is_not_source_of_truth_duplication(
    inventory: ShellStateSectionContractInventory,
) -> None:
    if inventory.is_source_of_truth or inventory.duplicates_agent_governance:
        _reject(
            "P2.8-D inventory must not duplicate source evidence or agent governance",
            field="is_source_of_truth",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
