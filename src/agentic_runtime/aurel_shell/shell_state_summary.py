"""P2.8-C Shell state summary / sync descriptor / read-only summary boundary.

Contract-only docs/report index summaries, Shell state read-only summaries,
sync descriptors/candidates, reference drift/missing/stale descriptors,
source comparison and limitation descriptors, availability, no-sync/no-generation/
no-write boundaries, summary boundary result, side-effect proof, and pack result
over P2.8-B read-model/index evidence.

Core law:
  - Sync descriptor is not sync runtime.
  - Sync candidate is not reconciliation execution.
  - Shell state summary is not mutable Shell state.
  - Summary bundle is not product summary UI.
  - Summary contract is not generator runtime.
  - Docs/report summary is not generated documentation/report.
  - Reference drift descriptor is not repair.
  - Missing reference descriptor is not auto-fix.
  - Stale reference descriptor is not refresh runtime.
  - Source comparison descriptor is not authority decision.
  - Summary limitation descriptor is not policy enforcement.

It does not create live Shell state runtime, Shell state sync runtime, state
reconciliation engine, repair/autofix action, refresh runtime, persistent state
store, database persistence, storage write, trace write, memory write, docs write,
reports write, report generator runtime, docs generator runtime, summary generator
runtime, report publisher, docs publisher, product UI, product behavior, CLI
runner, TUI runtime, command execution, runtime dispatch, permission enforcement,
Custos decisioning, approval runtime, LIVE, TRACE_VERIFIED, release scope,
P2.8-D, P2.9, P2.10, or P2.13.
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
from .shell_state_read_models import (
    P2_8_B_OFFICIAL_SECTION_NAME,
    P2_8_B_PACK_ID,
    P2_8_B_REPORT_PATH,
    P2_8_B_VALIDATION_REF,
    P28BShellStateReadModelResult,
    P28BSideEffectProof,
    build_p2_8_b_shell_state_read_model_result,
)

P2_8_C_PACK_ID = "P2.8-C"
P2_8_C_SECTION_ID = "P2.8"
P2_8_C_OFFICIAL_SECTION_NAME = P2_8_B_OFFICIAL_SECTION_NAME
P2_8_C_DEPENDENCY_PACK = P2_8_B_PACK_ID
P2_8_C_NEXT_PACK = "P2.8-D"
P2_8_C_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.8.11",
    "P2.8.12",
    "P2.8.13",
    "P2.8.14",
    "P2.8.15",
)
P2_8_C_REPORT_FILENAME = "P2_8_C_DOCS_INDEX_STATE_SYNC_READ_ONLY_SUMMARY.md"
P2_8_C_REPORT_PATH = f"agent/reports/{P2_8_C_REPORT_FILENAME}"

P2_8_B_COMMIT_REF = "8762a8a"

P2_8_C_GATE_VERSION = "p2_8_c_shell_state_summary_gate.v1"
P2_8_C_DOCS_SUMMARY_VERSION = "p2_8_c_shell_docs_index_summary.v1"
P2_8_C_REPORT_SUMMARY_VERSION = "p2_8_c_shell_report_index_summary.v1"
P2_8_C_STATE_SUMMARY_VERSION = "p2_8_c_shell_state_read_only_summary.v1"
P2_8_C_SUMMARY_BUNDLE_VERSION = "p2_8_c_shell_state_summary_bundle.v1"
P2_8_C_SYNC_DESCRIPTOR_VERSION = "p2_8_c_shell_state_sync_descriptor.v1"
P2_8_C_SYNC_CANDIDATE_VERSION = "p2_8_c_shell_state_sync_candidate.v1"
P2_8_C_DRIFT_DESCRIPTOR_VERSION = "p2_8_c_shell_reference_drift_descriptor.v1"
P2_8_C_MISSING_DESCRIPTOR_VERSION = "p2_8_c_shell_reference_missing_descriptor.v1"
P2_8_C_STALE_DESCRIPTOR_VERSION = "p2_8_c_shell_reference_stale_descriptor.v1"
P2_8_C_COMPARISON_DESCRIPTOR_VERSION = "p2_8_c_shell_source_comparison_descriptor.v1"
P2_8_C_LIMITATION_DESCRIPTOR_VERSION = "p2_8_c_shell_summary_limitation_descriptor.v1"
P2_8_C_AVAILABILITY_VERSION = "p2_8_c_shell_read_only_summary_availability.v1"
P2_8_C_NO_SYNC_VERSION = "p2_8_c_shell_summary_no_sync_runtime_boundary.v1"
P2_8_C_NO_GENERATION_VERSION = "p2_8_c_shell_summary_no_generation_boundary.v1"
P2_8_C_NO_WRITE_VERSION = "p2_8_c_shell_summary_no_write_boundary.v1"
P2_8_C_BOUNDARY_RESULT_VERSION = "p2_8_c_shell_state_summary_boundary_result.v1"
P2_8_C_RESULT_VERSION = "p2_8_c_shell_state_summary_pack_result.v1"

P2_8_C_TEST_REF = "tests/aurel_shell/test_shell_state_summary.py"
P2_8_C_VALIDATION_REF = "agent/TESTS.md#P2.8-C"
P2_8_C_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_8_C_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_GATE_ID = "p2_8_c_shell_state_summary_gate"
_DOCS_SUMMARY_ID = "p2_8_c_shell_docs_index_summary"
_REPORT_SUMMARY_ID = "p2_8_c_shell_report_index_summary"
_STATE_SUMMARY_ID = "p2_8_c_shell_state_read_only_summary"
_SUMMARY_BUNDLE_ID = "p2_8_c_shell_state_summary_bundle"
_SYNC_DESCRIPTOR_ID = "p2_8_c_shell_state_sync_descriptor"
_SYNC_CANDIDATE_ID = "p2_8_c_shell_state_sync_candidate"
_DRIFT_DESCRIPTOR_ID = "p2_8_c_shell_reference_drift_descriptor"
_MISSING_DESCRIPTOR_ID = "p2_8_c_shell_reference_missing_descriptor"
_STALE_DESCRIPTOR_ID = "p2_8_c_shell_reference_stale_descriptor"
_COMPARISON_DESCRIPTOR_ID = "p2_8_c_shell_source_comparison_descriptor"
_LIMITATION_DESCRIPTOR_ID = "p2_8_c_shell_summary_limitation_descriptor"
_AVAILABILITY_ID = "p2_8_c_shell_read_only_summary_availability"
_NO_SYNC_ID = "p2_8_c_shell_summary_no_sync_runtime_boundary"
_NO_GENERATION_ID = "p2_8_c_shell_summary_no_generation_boundary"
_NO_WRITE_ID = "p2_8_c_shell_summary_no_write_boundary"
_BOUNDARY_RESULT_ID = "p2_8_c_shell_state_summary_boundary_result"

_AGENT_REPORTS_REF = "agent/REPORTS.md"

_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "live Shell state runtime",
    "Shell state sync runtime",
    "state reconciliation engine",
    "repair/autofix action",
    "refresh runtime",
    "report generator runtime",
    "docs generator runtime",
    "summary generator runtime",
    "report publisher",
    "docs publisher",
    "storage write",
    "trace write",
    "memory write",
    "docs write",
    "reports write",
    "product UI",
    "product behavior",
    "P2.8-D implementation",
    "P2.9 implementation",
    "P2.10 implementation",
    "P2.13 implementation",
)


class ShellStateSummaryGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellStateSyncDescriptorMode(str, Enum):
    DESCRIPTOR_ONLY = "DESCRIPTOR_ONLY"
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    READ_ONLY_ANALYSIS_ONLY = "READ_ONLY_ANALYSIS_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class ShellReadOnlySummaryAvailabilityStatus(str, Enum):
    CONTRACT_AVAILABLE = "CONTRACT_AVAILABLE"
    UNAVAILABLE_RUNTIME_REQUIRED = "UNAVAILABLE_RUNTIME_REQUIRED"
    UNAVAILABLE_P2_8_D_REQUIRED = "UNAVAILABLE_P2_8_D_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellStateSummaryTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_ONLY_SUMMARY_ONLY = "READ_ONLY_SUMMARY_ONLY"
    DOCS_INDEX_SUMMARY_ONLY = "DOCS_INDEX_SUMMARY_ONLY"
    REPORT_INDEX_SUMMARY_ONLY = "REPORT_INDEX_SUMMARY_ONLY"
    SHELL_STATE_SUMMARY_ONLY = "SHELL_STATE_SUMMARY_ONLY"
    SUMMARY_BUNDLE_ONLY = "SUMMARY_BUNDLE_ONLY"
    SYNC_DESCRIPTOR_ONLY = "SYNC_DESCRIPTOR_ONLY"
    SYNC_CANDIDATE_ONLY = "SYNC_CANDIDATE_ONLY"
    REFERENCE_DRIFT_DESCRIPTOR_ONLY = "REFERENCE_DRIFT_DESCRIPTOR_ONLY"
    MISSING_REFERENCE_DESCRIPTOR_ONLY = "MISSING_REFERENCE_DESCRIPTOR_ONLY"
    STALE_REFERENCE_DESCRIPTOR_ONLY = "STALE_REFERENCE_DESCRIPTOR_ONLY"
    SOURCE_COMPARISON_DESCRIPTOR_ONLY = "SOURCE_COMPARISON_DESCRIPTOR_ONLY"
    SUMMARY_LIMITATION_DESCRIPTOR_ONLY = "SUMMARY_LIMITATION_DESCRIPTOR_ONLY"
    READ_ONLY_SUMMARY_AVAILABILITY_ONLY = "READ_ONLY_SUMMARY_AVAILABILITY_ONLY"
    NO_SYNC_RUNTIME_BOUNDARY = "NO_SYNC_RUNTIME_BOUNDARY"
    NO_GENERATION_BOUNDARY = "NO_GENERATION_BOUNDARY"
    NO_WRITE_BOUNDARY = "NO_WRITE_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_SYNC_RUNTIME = "NOT_SYNC_RUNTIME"
    NOT_STATE_RECONCILIATION_ENGINE = "NOT_STATE_RECONCILIATION_ENGINE"
    NOT_REPAIR_ACTION = "NOT_REPAIR_ACTION"
    NOT_AUTO_FIX = "NOT_AUTO_FIX"
    NOT_REFRESH_RUNTIME = "NOT_REFRESH_RUNTIME"
    NOT_QUERY_RUNTIME = "NOT_QUERY_RUNTIME"
    NOT_FILTER_RUNTIME = "NOT_FILTER_RUNTIME"
    NOT_SORT_RUNTIME = "NOT_SORT_RUNTIME"
    NOT_LIVE_SHELL_STATE = "NOT_LIVE_SHELL_STATE"
    NOT_SHELL_RUNTIME = "NOT_SHELL_RUNTIME"
    NOT_SHELL_STATE_RUNTIME = "NOT_SHELL_STATE_RUNTIME"
    NOT_SESSION_STATE_ENGINE = "NOT_SESSION_STATE_ENGINE"
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
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_CUSTOS_DECISION = "NOT_CUSTOS_DECISION"
    NOT_P2_8_D_IMPLEMENTATION = "NOT_P2_8_D_IMPLEMENTATION"
    NOT_P2_9_IMPLEMENTATION = "NOT_P2_9_IMPLEMENTATION"
    NOT_P2_10_IMPLEMENTATION = "NOT_P2_10_IMPLEMENTATION"
    NOT_P2_13_IMPLEMENTATION = "NOT_P2_13_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class P28CSideEffectProof(_CanonicalMixin):
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
    fix_written: bool = False
    refresh_written: bool = False
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
    p2_8_d_started: bool = False
    p2_9_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellStateSummaryGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_read_model_expansion_result_ref: str
    dependency_report_index_ref: str
    dependency_docs_index_ref: str
    dependency_no_generation_boundary_ref: str
    dependency_no_runtime_mutation_boundary_ref: str
    dependency_no_write_boundary_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellStateSummaryGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellDocsIndexSummary(_CanonicalMixin):
    docs_index_summary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_docs_index_ref: str
    source_docs_entries_ref: str
    summary_scope: str
    docs_family_refs: tuple[str, ...]
    docs_ref_count: int
    is_docs_generation: bool
    is_docs_source_of_truth: bool
    writes_docs: bool
    truth_label: str
    limitations: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class ShellReportIndexSummary(_CanonicalMixin):
    report_index_summary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_report_index_ref: str
    source_report_entries_ref: str
    source_agent_reports_ref: str
    summary_scope: str
    report_family_refs: tuple[str, ...]
    report_ref_count: int
    is_report_generation: bool
    is_agent_reports_replacement: bool
    writes_reports: bool
    truth_label: str
    limitations: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class ShellStateReadOnlySummary(_CanonicalMixin):
    state_summary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_section_status_ref: str
    source_state_snapshot_ref: str
    source_report_index_summary_ref: str
    source_docs_index_summary_ref: str
    summary_scope: str
    is_read_only: bool
    mutates_shell_state: bool
    mutates_runtime_state: bool
    is_product_ui: bool
    truth_label: str
    limitations: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class ShellStateSummaryBundle(_CanonicalMixin):
    summary_bundle_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    docs_index_summary_ref: str
    report_index_summary_ref: str
    state_read_only_summary_ref: str
    sync_descriptor_refs: tuple[str, ...]
    drift_descriptor_refs: tuple[str, ...]
    missing_descriptor_refs: tuple[str, ...]
    stale_descriptor_refs: tuple[str, ...]
    source_comparison_refs: tuple[str, ...]
    limitation_refs: tuple[str, ...]
    is_product_summary: bool
    is_generated_summary: bool
    requires_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    bundle_hash: str


@dataclass(frozen=True)
class ShellStateSyncDescriptor(_CanonicalMixin):
    sync_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    sync_descriptor_mode: ShellStateSyncDescriptorMode
    source_state_ref: str
    target_state_ref: str
    sync_reason: str
    sync_scope: str
    is_sync_runtime: bool
    executes_sync: bool
    mutates_shell_state: bool
    creates_reconciliation_engine: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellStateSyncCandidate(_CanonicalMixin):
    sync_candidate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    candidate_scope: str
    source_ref: str
    target_ref: str
    candidate_reason: str
    candidate_confidence_label: str
    is_reconciliation_execution: bool
    executes_candidate: bool
    creates_repair_action: bool
    truth_label: str
    limitations: tuple[str, ...]
    candidate_hash: str


@dataclass(frozen=True)
class ShellReferenceDriftDescriptor(_CanonicalMixin):
    drift_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_ref: str
    comparison_ref: str
    drift_kind: str
    drift_reason: str
    is_repair_action: bool
    executes_repair: bool
    writes_fix: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellReferenceMissingDescriptor(_CanonicalMixin):
    missing_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    expected_ref: str
    source_context_ref: str
    missing_kind: str
    missing_reason: str
    is_auto_fix: bool
    executes_auto_fix: bool
    writes_fix: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellReferenceStaleDescriptor(_CanonicalMixin):
    stale_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_ref: str
    stale_reason: str
    stale_age_label: str
    refresh_required: bool
    is_refresh_runtime: bool
    executes_refresh: bool
    writes_refresh: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellSourceComparisonDescriptor(_CanonicalMixin):
    comparison_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    left_source_ref: str
    right_source_ref: str
    comparison_scope: str
    comparison_reason: str
    is_authority_decision: bool
    decides_truth: bool
    enforces_policy: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellSummaryLimitationDescriptor(_CanonicalMixin):
    limitation_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    limitation_kind: str
    limitation_reason: str
    affected_summary_ref: str
    unavailable_capability: str
    requires_future_pack: str
    is_policy_enforcement: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellReadOnlySummaryAvailability(_CanonicalMixin):
    availability_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    availability_status: ShellReadOnlySummaryAvailabilityStatus
    available_summary_refs: tuple[str, ...]
    available_descriptor_refs: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    future_pack_refs: tuple[str, ...]
    enforces_permission: bool
    grants_permission: bool
    denies_permission: bool
    truth_label: str
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class ShellSummaryNoSyncRuntimeBoundary(_CanonicalMixin):
    no_sync_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    shell_state_sync_runtime_created: bool
    state_reconciliation_engine_created: bool
    sync_executed: bool
    repair_action_created: bool
    autofix_created: bool
    refresh_runtime_created: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellSummaryNoGenerationBoundary(_CanonicalMixin):
    no_generation_boundary_id: str
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
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellSummaryNoWriteBoundary(_CanonicalMixin):
    no_write_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    trace_written: bool
    memory_written: bool
    storage_written: bool
    database_written: bool
    docs_written: bool
    reports_written: bool
    fix_written: bool
    refresh_written: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellStateSummaryBoundaryResult(_CanonicalMixin):
    boundary_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    summary_gate: ShellStateSummaryGate
    docs_index_summary: ShellDocsIndexSummary
    report_index_summary: ShellReportIndexSummary
    state_read_only_summary: ShellStateReadOnlySummary
    summary_bundle: ShellStateSummaryBundle
    sync_descriptors: tuple[ShellStateSyncDescriptor, ...]
    sync_candidates: tuple[ShellStateSyncCandidate, ...]
    drift_descriptors: tuple[ShellReferenceDriftDescriptor, ...]
    missing_descriptors: tuple[ShellReferenceMissingDescriptor, ...]
    stale_descriptors: tuple[ShellReferenceStaleDescriptor, ...]
    source_comparisons: tuple[ShellSourceComparisonDescriptor, ...]
    summary_limitations: tuple[ShellSummaryLimitationDescriptor, ...]
    availability: ShellReadOnlySummaryAvailability
    no_sync_runtime_boundary: ShellSummaryNoSyncRuntimeBoundary
    no_generation_boundary: ShellSummaryNoGenerationBoundary
    no_write_boundary: ShellSummaryNoWriteBoundary
    creates_sync_runtime: bool
    creates_reconciliation_engine: bool
    creates_generator_runtime: bool
    creates_write_path: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P28CShellStateSummaryResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_8_b_evidence_ref: str
    p2_8_b_read_model_result_ref: str
    p2_8_b_report_index_ref: str
    p2_8_b_docs_index_ref: str
    summary_gate: ShellStateSummaryGate
    docs_index_summary: ShellDocsIndexSummary
    report_index_summary: ShellReportIndexSummary
    state_read_only_summary: ShellStateReadOnlySummary
    summary_bundle: ShellStateSummaryBundle
    sync_descriptors: tuple[ShellStateSyncDescriptor, ...]
    sync_candidates: tuple[ShellStateSyncCandidate, ...]
    drift_descriptors: tuple[ShellReferenceDriftDescriptor, ...]
    missing_descriptors: tuple[ShellReferenceMissingDescriptor, ...]
    stale_descriptors: tuple[ShellReferenceStaleDescriptor, ...]
    source_comparisons: tuple[ShellSourceComparisonDescriptor, ...]
    summary_limitations: tuple[ShellSummaryLimitationDescriptor, ...]
    availability: ShellReadOnlySummaryAvailability
    no_sync_runtime_boundary: ShellSummaryNoSyncRuntimeBoundary
    no_generation_boundary: ShellSummaryNoGenerationBoundary
    no_write_boundary: ShellSummaryNoWriteBoundary
    boundary_result: ShellStateSummaryBoundaryResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P28CSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _expansion_result_ref(result: P28BShellStateReadModelResult) -> str:
    expansion = result.expansion_result
    return (
        f"{expansion.expansion_result_id}:"
        f"hash={expansion.expansion_hash[:12]}"
    )


def _report_index_ref(result: P28BShellStateReadModelResult) -> str:
    index = result.report_index
    return f"{index.report_index_id}:hash={index.report_index_hash[:12]}"


def _docs_index_ref(result: P28BShellStateReadModelResult) -> str:
    index = result.docs_index
    return f"{index.docs_index_id}:hash={index.docs_index_hash[:12]}"


def _no_generation_boundary_ref(result: P28BShellStateReadModelResult) -> str:
    boundary = result.no_generation_boundary
    return f"{boundary.no_generation_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _no_runtime_mutation_boundary_ref(result: P28BShellStateReadModelResult) -> str:
    boundary = result.no_runtime_mutation_boundary
    return f"{boundary.no_runtime_mutation_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _no_write_boundary_ref(result: P28BShellStateReadModelResult) -> str:
    boundary = result.no_write_boundary
    return f"{boundary.no_write_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _section_status_ref(result: P28BShellStateReadModelResult) -> str:
    status = result.section_status_read_model
    return f"{status.section_status_read_model_id}:hash={status.status_hash[:12]}"


def _state_snapshot_ref(result: P28BShellStateReadModelResult) -> str:
    snapshot = result.state_snapshot_read_model
    return (
        f"{snapshot.state_snapshot_read_model_id}:"
        f"hash={snapshot.snapshot_hash[:12]}"
    )


def _p2_8_b_evidence_ref(result: P28BShellStateReadModelResult) -> str:
    return f"{P2_8_B_REPORT_PATH}:{result.result_hash[:12]}"


def _read_model_result_ref(result: P28BShellStateReadModelResult) -> str:
    return f"{result.pack_id}:{result.result_hash[:12]}"


def assert_p2_8_b_read_model_result_available(
    result: P28BShellStateReadModelResult,
) -> None:
    if result.pack_id != P2_8_B_PACK_ID or result.starts_future_work:
        _reject(
            "P2.8-C requires a P2.8-B read model result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.next_pack != P2_8_C_PACK_ID:
        _reject(
            "P2.8-C requires P2.8-B read model result pointing to P2.8-C",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        result.expansion_result.creates_query_runtime
        or result.expansion_result.creates_generator_runtime
        or result.expansion_result.creates_write_path
        or result.expansion_result.creates_product_behavior
    ):
        _reject(
            "P2.8-B dependency must not overclaim runtime/generation/write/product",
            field="expansion_result",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellStateSummaryGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.8-C gate must ignore OMNI evidence by operator instruction",
            field="omni_evidence_ignored_by_operator_instruction",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_summary_gate_depends_on_p2_8_b(gate: ShellStateSummaryGate) -> None:
    if gate.dependency_pack != P2_8_B_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.8-C summary gate must depend on P2.8-B repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_sync_descriptor_is_not_sync_runtime(
    descriptor: ShellStateSyncDescriptor,
) -> None:
    if (
        descriptor.is_sync_runtime
        or descriptor.executes_sync
        or descriptor.mutates_shell_state
        or descriptor.creates_reconciliation_engine
    ):
        _reject(
            "Sync descriptor must not execute sync or create reconciliation",
            field="sync_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_sync_candidate_is_not_reconciliation_execution(
    candidate: ShellStateSyncCandidate,
) -> None:
    if (
        candidate.is_reconciliation_execution
        or candidate.executes_candidate
        or candidate.creates_repair_action
    ):
        _reject(
            "Sync candidate must not execute reconciliation or repair",
            field="sync_candidate_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_summary_contract_is_not_generator(
    summary: ShellDocsIndexSummary | ShellReportIndexSummary | ShellStateReadOnlySummary,
) -> None:
    if isinstance(summary, ShellDocsIndexSummary):
        if summary.is_docs_generation or summary.writes_docs:
            _reject(
                "Docs index summary must not generate or write docs",
                field="docs_index_summary_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    elif isinstance(summary, ShellReportIndexSummary):
        if summary.is_report_generation or summary.writes_reports:
            _reject(
                "Report index summary must not generate or write reports",
                field="report_index_summary_id",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    elif summary.mutates_shell_state or summary.mutates_runtime_state or summary.is_product_ui:
        _reject(
            "Shell state read-only summary must not mutate state or be product UI",
            field="state_summary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_drift_missing_stale_do_not_repair(
    drift: ShellReferenceDriftDescriptor,
    missing: ShellReferenceMissingDescriptor,
    stale: ShellReferenceStaleDescriptor,
) -> None:
    if drift.is_repair_action or drift.executes_repair or drift.writes_fix:
        _reject(
            "Drift descriptor must not repair or write fixes",
            field="drift_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if missing.is_auto_fix or missing.executes_auto_fix or missing.writes_fix:
        _reject(
            "Missing descriptor must not auto-fix or write fixes",
            field="missing_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if stale.is_refresh_runtime or stale.executes_refresh or stale.writes_refresh:
        _reject(
            "Stale descriptor must not refresh or write refresh",
            field="stale_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_source_comparison_is_not_authority(
    comparison: ShellSourceComparisonDescriptor,
) -> None:
    if (
        comparison.is_authority_decision
        or comparison.decides_truth
        or comparison.enforces_policy
    ):
        _reject(
            "Source comparison must not decide truth or enforce policy",
            field="comparison_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_trace_memory_storage_report_docs_writes(
    boundary: ShellSummaryNoWriteBoundary,
) -> None:
    if not boundary.boundary_active or any(
        (
            boundary.trace_written,
            boundary.memory_written,
            boundary.storage_written,
            boundary.database_written,
            boundary.docs_written,
            boundary.reports_written,
            boundary.fix_written,
            boundary.refresh_written,
        )
    ):
        _reject(
            "No-write boundary must be active with all write flags false",
            field="no_write_boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_c_does_not_start_future_work(
    result: P28CShellStateSummaryResult,
) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or result.next_pack != P2_8_C_NEXT_PACK
        or proof.p2_8_d_started
        or proof.p2_9_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.8-C must not start future packs",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_c_side_effects_all_false(proof: P28CSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.8-C side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_summary_boundary_result_is_contract_only(
    boundary: ShellStateSummaryBoundaryResult,
) -> None:
    if (
        boundary.creates_sync_runtime
        or boundary.creates_reconciliation_engine
        or boundary.creates_generator_runtime
        or boundary.creates_write_path
        or boundary.creates_product_behavior
    ):
        _reject(
            "P2.8-C summary boundary result must remain contract-only",
            field="boundary_result_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def build_shell_state_summary_gate(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellStateSummaryGate:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    assert_p2_8_b_read_model_result_available(read_model_result)
    payload: dict[str, Any] = {
        "gate_id": _GATE_ID,
        "schema_version": P2_8_C_GATE_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "official_section_name": P2_8_C_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_8_C_DEPENDENCY_PACK,
        "dependency_report_ref": P2_8_B_REPORT_PATH,
        "dependency_commit_ref": P2_8_B_COMMIT_REF,
        "dependency_validation_ref": P2_8_B_VALIDATION_REF,
        "dependency_read_model_expansion_result_ref": _expansion_result_ref(
            read_model_result
        ),
        "dependency_report_index_ref": _report_index_ref(read_model_result),
        "dependency_docs_index_ref": _docs_index_ref(read_model_result),
        "dependency_no_generation_boundary_ref": _no_generation_boundary_ref(
            read_model_result
        ),
        "dependency_no_runtime_mutation_boundary_ref": _no_runtime_mutation_boundary_ref(
            read_model_result
        ),
        "dependency_no_write_boundary_ref": _no_write_boundary_ref(read_model_result),
        "dependency_side_effect_proof_ref": "P28BSideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellStateSummaryGateStatus.READY,
        "truth_label": ShellStateSummaryTruthBoundary.READ_ONLY_SUMMARY_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not sync, generate, or mutate Shell state",
        ),
    }
    gate = ShellStateSummaryGate(**payload, gate_hash=_hash_payload(payload))
    assert_summary_gate_depends_on_p2_8_b(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_shell_docs_index_summary(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellDocsIndexSummary:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    docs_index = read_model_result.docs_index
    family_refs = tuple(
        grouping.docs_family_grouping_id
        for grouping in docs_index.docs_family_groupings
    )
    payload: dict[str, Any] = {
        "docs_index_summary_id": _DOCS_SUMMARY_ID,
        "schema_version": P2_8_C_DOCS_SUMMARY_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "source_docs_index_ref": _docs_index_ref(read_model_result),
        "source_docs_entries_ref": f"{len(docs_index.docs_index_entries)} entries",
        "summary_scope": "P2.8.11 docs index read-only summary",
        "docs_family_refs": family_refs,
        "docs_ref_count": len(docs_index.docs_index_entries),
        "is_docs_generation": False,
        "is_docs_source_of_truth": False,
        "writes_docs": False,
        "truth_label": ShellStateSummaryTruthBoundary.DOCS_INDEX_SUMMARY_ONLY.value,
        "limitations": (
            "summary references P2.8-B docs index only",
            "not docs generation or source-of-truth",
        ),
    }
    summary = ShellDocsIndexSummary(**payload, summary_hash=_hash_payload(payload))
    assert_summary_contract_is_not_generator(summary)
    return summary


def build_shell_report_index_summary(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellReportIndexSummary:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    report_index = read_model_result.report_index
    family_refs = tuple(
        grouping.report_family_grouping_id
        for grouping in report_index.report_family_groupings
    )
    payload: dict[str, Any] = {
        "report_index_summary_id": _REPORT_SUMMARY_ID,
        "schema_version": P2_8_C_REPORT_SUMMARY_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "source_report_index_ref": _report_index_ref(read_model_result),
        "source_report_entries_ref": f"{len(report_index.report_index_entries)} entries",
        "source_agent_reports_ref": report_index.source_agent_reports_ref,
        "summary_scope": "P2.8.11 report index read-only summary",
        "report_family_refs": family_refs,
        "report_ref_count": len(report_index.report_index_entries),
        "is_report_generation": False,
        "is_agent_reports_replacement": False,
        "writes_reports": False,
        "truth_label": ShellStateSummaryTruthBoundary.REPORT_INDEX_SUMMARY_ONLY.value,
        "limitations": (
            "summary references P2.8-B report index only",
            "not report generation or agent/REPORTS.md replacement",
        ),
    }
    summary = ShellReportIndexSummary(**payload, summary_hash=_hash_payload(payload))
    assert_summary_contract_is_not_generator(summary)
    return summary


def build_shell_state_read_only_summary(
    read_model_result: P28BShellStateReadModelResult | None = None,
    *,
    docs_summary: ShellDocsIndexSummary | None = None,
    report_summary: ShellReportIndexSummary | None = None,
) -> ShellStateReadOnlySummary:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    if docs_summary is None:
        docs_summary = build_shell_docs_index_summary(read_model_result)
    if report_summary is None:
        report_summary = build_shell_report_index_summary(read_model_result)
    payload: dict[str, Any] = {
        "state_summary_id": _STATE_SUMMARY_ID,
        "schema_version": P2_8_C_STATE_SUMMARY_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "source_section_status_ref": _section_status_ref(read_model_result),
        "source_state_snapshot_ref": _state_snapshot_ref(read_model_result),
        "source_report_index_summary_ref": report_summary.report_index_summary_id,
        "source_docs_index_summary_ref": docs_summary.docs_index_summary_id,
        "summary_scope": "P2.8.12 Shell state read-only summary",
        "is_read_only": True,
        "mutates_shell_state": False,
        "mutates_runtime_state": False,
        "is_product_ui": False,
        "truth_label": ShellStateSummaryTruthBoundary.SHELL_STATE_SUMMARY_ONLY.value,
        "limitations": (
            "read-only summary over P2.8-B section status and snapshot",
            "not mutable Shell state or product UI",
        ),
    }
    summary = ShellStateReadOnlySummary(**payload, summary_hash=_hash_payload(payload))
    assert_summary_contract_is_not_generator(summary)
    return summary


def build_shell_state_sync_descriptor(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellStateSyncDescriptor:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    payload: dict[str, Any] = {
        "sync_descriptor_id": _SYNC_DESCRIPTOR_ID,
        "schema_version": P2_8_C_SYNC_DESCRIPTOR_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "sync_descriptor_mode": ShellStateSyncDescriptorMode.DESCRIPTOR_ONLY,
        "source_state_ref": _section_status_ref(read_model_result),
        "target_state_ref": _state_snapshot_ref(read_model_result),
        "sync_reason": "Describe potential section-status vs snapshot alignment intent",
        "sync_scope": "P2.8.13 read-only sync descriptor",
        "is_sync_runtime": False,
        "executes_sync": False,
        "mutates_shell_state": False,
        "creates_reconciliation_engine": False,
        "truth_label": ShellStateSummaryTruthBoundary.SYNC_DESCRIPTOR_ONLY.value,
        "limitations": (
            "sync descriptor is intent only",
            "not sync runtime or reconciliation engine",
        ),
    }
    descriptor = ShellStateSyncDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_sync_descriptor_is_not_sync_runtime(descriptor)
    return descriptor


def build_shell_state_sync_candidate(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellStateSyncCandidate:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    payload: dict[str, Any] = {
        "sync_candidate_id": _SYNC_CANDIDATE_ID,
        "schema_version": P2_8_C_SYNC_CANDIDATE_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "candidate_scope": "report-docs index alignment candidate",
        "source_ref": _report_index_ref(read_model_result),
        "target_ref": _docs_index_ref(read_model_result),
        "candidate_reason": "Non-executable candidate for report/docs index alignment",
        "candidate_confidence_label": "DEV_FIXTURE_DESCRIPTOR_ONLY",
        "is_reconciliation_execution": False,
        "executes_candidate": False,
        "creates_repair_action": False,
        "truth_label": ShellStateSummaryTruthBoundary.SYNC_CANDIDATE_ONLY.value,
        "limitations": (
            "candidate describes possible alignment only",
            "not reconciliation execution or repair",
        ),
    }
    candidate = ShellStateSyncCandidate(
        **payload,
        candidate_hash=_hash_payload(payload),
    )
    assert_sync_candidate_is_not_reconciliation_execution(candidate)
    return candidate


def build_shell_reference_drift_descriptor(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellReferenceDriftDescriptor:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    payload: dict[str, Any] = {
        "drift_descriptor_id": _DRIFT_DESCRIPTOR_ID,
        "schema_version": P2_8_C_DRIFT_DESCRIPTOR_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "source_ref": _report_index_ref(read_model_result),
        "comparison_ref": read_model_result.report_index.source_agent_reports_ref,
        "drift_kind": "INDEX_REFERENCE_OBSERVATION",
        "drift_reason": "Report index references agent/REPORTS.md without replacing it",
        "is_repair_action": False,
        "executes_repair": False,
        "writes_fix": False,
        "truth_label": ShellStateSummaryTruthBoundary.REFERENCE_DRIFT_DESCRIPTOR_ONLY.value,
        "limitations": (
            "drift descriptor is observation only",
            "not repair action",
        ),
    }
    return ShellReferenceDriftDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_reference_missing_descriptor(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellReferenceMissingDescriptor:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    payload: dict[str, Any] = {
        "missing_descriptor_id": _MISSING_DESCRIPTOR_ID,
        "schema_version": P2_8_C_MISSING_DESCRIPTOR_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "expected_ref": "live Shell state runtime",
        "source_context_ref": _expansion_result_ref(read_model_result),
        "missing_kind": "RUNTIME_UNAVAILABLE_BY_DESIGN",
        "missing_reason": "Live Shell state runtime is unavailable at P2.8-C scope",
        "is_auto_fix": False,
        "executes_auto_fix": False,
        "writes_fix": False,
        "truth_label": (
            ShellStateSummaryTruthBoundary.MISSING_REFERENCE_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "missing descriptor marks unavailable capability",
            "not auto-fix",
        ),
    }
    return ShellReferenceMissingDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_reference_stale_descriptor(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellReferenceStaleDescriptor:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    payload: dict[str, Any] = {
        "stale_descriptor_id": _STALE_DESCRIPTOR_ID,
        "schema_version": P2_8_C_STALE_DESCRIPTOR_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "source_ref": f"{P2_8_B_REPORT_PATH}:{P2_8_B_COMMIT_REF}",
        "stale_reason": "Commit ref may drift from latest mainline without refresh runtime",
        "stale_age_label": "DEV_FIXTURE_REFERENCE_AGE",
        "refresh_required": False,
        "is_refresh_runtime": False,
        "executes_refresh": False,
        "writes_refresh": False,
        "truth_label": (
            ShellStateSummaryTruthBoundary.STALE_REFERENCE_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "stale descriptor is observation only",
            "not refresh runtime",
        ),
    }
    return ShellReferenceStaleDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_source_comparison_descriptor(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellSourceComparisonDescriptor:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    payload: dict[str, Any] = {
        "comparison_descriptor_id": _COMPARISON_DESCRIPTOR_ID,
        "schema_version": P2_8_C_COMPARISON_DESCRIPTOR_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "left_source_ref": read_model_result.p2_8_a_evidence_ref,
        "right_source_ref": _expansion_result_ref(read_model_result),
        "comparison_scope": "P2.8-A foundation vs P2.8-B expansion observation",
        "comparison_reason": "Non-authoritative source comparison for summary context",
        "is_authority_decision": False,
        "decides_truth": False,
        "enforces_policy": False,
        "truth_label": (
            ShellStateSummaryTruthBoundary.SOURCE_COMPARISON_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "comparison does not decide truth or enforce policy",
            "observation only",
        ),
    }
    descriptor = ShellSourceComparisonDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )
    assert_source_comparison_is_not_authority(descriptor)
    return descriptor


def build_shell_summary_limitation_descriptor(
    state_summary: ShellStateReadOnlySummary | None = None,
) -> ShellSummaryLimitationDescriptor:
    if state_summary is None:
        state_summary = build_shell_state_read_only_summary()
    payload: dict[str, Any] = {
        "limitation_descriptor_id": _LIMITATION_DESCRIPTOR_ID,
        "schema_version": P2_8_C_LIMITATION_DESCRIPTOR_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "limitation_kind": "SECTION_SEAL_DEFERRED",
        "limitation_reason": "Read-only summary boundary does not seal P2.8 section",
        "affected_summary_ref": state_summary.state_summary_id,
        "unavailable_capability": "P2.8 section seal",
        "requires_future_pack": P2_8_C_NEXT_PACK,
        "is_policy_enforcement": False,
        "truth_label": (
            ShellStateSummaryTruthBoundary.SUMMARY_LIMITATION_DESCRIPTOR_ONLY.value
        ),
        "limitations": (
            "limitation descriptor is honesty only",
            "not policy enforcement",
        ),
    }
    return ShellSummaryLimitationDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_state_summary_bundle(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellStateSummaryBundle:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    docs_summary = build_shell_docs_index_summary(read_model_result)
    report_summary = build_shell_report_index_summary(read_model_result)
    state_summary = build_shell_state_read_only_summary(
        read_model_result,
        docs_summary=docs_summary,
        report_summary=report_summary,
    )
    sync_descriptor = build_shell_state_sync_descriptor(read_model_result)
    drift = build_shell_reference_drift_descriptor(read_model_result)
    missing = build_shell_reference_missing_descriptor(read_model_result)
    stale = build_shell_reference_stale_descriptor(read_model_result)
    comparison = build_shell_source_comparison_descriptor(read_model_result)
    limitation = build_shell_summary_limitation_descriptor(state_summary)
    payload: dict[str, Any] = {
        "summary_bundle_id": _SUMMARY_BUNDLE_ID,
        "schema_version": P2_8_C_SUMMARY_BUNDLE_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "docs_index_summary_ref": docs_summary.docs_index_summary_id,
        "report_index_summary_ref": report_summary.report_index_summary_id,
        "state_read_only_summary_ref": state_summary.state_summary_id,
        "sync_descriptor_refs": (sync_descriptor.sync_descriptor_id,),
        "drift_descriptor_refs": (drift.drift_descriptor_id,),
        "missing_descriptor_refs": (missing.missing_descriptor_id,),
        "stale_descriptor_refs": (stale.stale_descriptor_id,),
        "source_comparison_refs": (comparison.comparison_descriptor_id,),
        "limitation_refs": (limitation.limitation_descriptor_id,),
        "is_product_summary": False,
        "is_generated_summary": False,
        "requires_runtime": False,
        "truth_label": ShellStateSummaryTruthBoundary.SUMMARY_BUNDLE_ONLY.value,
        "limitations": (
            "bundle aggregates read-only summary contracts",
            "not product summary UI or generator runtime",
        ),
    }
    return ShellStateSummaryBundle(**payload, bundle_hash=_hash_payload(payload))


def build_shell_read_only_summary_availability(
    bundle: ShellStateSummaryBundle | None = None,
) -> ShellReadOnlySummaryAvailability:
    if bundle is None:
        bundle = build_shell_state_summary_bundle()
    payload: dict[str, Any] = {
        "availability_id": _AVAILABILITY_ID,
        "schema_version": P2_8_C_AVAILABILITY_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "availability_status": ShellReadOnlySummaryAvailabilityStatus.CONTRACT_AVAILABLE,
        "available_summary_refs": (
            bundle.docs_index_summary_ref,
            bundle.report_index_summary_ref,
            bundle.state_read_only_summary_ref,
        ),
        "available_descriptor_refs": bundle.sync_descriptor_refs
        + bundle.drift_descriptor_refs
        + bundle.missing_descriptor_refs
        + bundle.stale_descriptor_refs
        + bundle.source_comparison_refs
        + bundle.limitation_refs,
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "future_pack_refs": (P2_8_C_NEXT_PACK, "P2.9", "P2.10", "P2.13"),
        "enforces_permission": False,
        "grants_permission": False,
        "denies_permission": False,
        "truth_label": (
            ShellStateSummaryTruthBoundary.READ_ONLY_SUMMARY_AVAILABILITY_ONLY.value
        ),
        "limitations": (
            "availability is capability honesty only",
            "not permission enforcement",
        ),
    }
    return ShellReadOnlySummaryAvailability(
        **payload,
        availability_hash=_hash_payload(payload),
    )


def build_shell_summary_no_sync_runtime_boundary() -> ShellSummaryNoSyncRuntimeBoundary:
    payload: dict[str, Any] = {
        "no_sync_boundary_id": _NO_SYNC_ID,
        "schema_version": P2_8_C_NO_SYNC_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "shell_state_sync_runtime_created": False,
        "state_reconciliation_engine_created": False,
        "sync_executed": False,
        "repair_action_created": False,
        "autofix_created": False,
        "refresh_runtime_created": False,
        "boundary_active": True,
        "truth_label": ShellStateSummaryTruthBoundary.NO_SYNC_RUNTIME_BOUNDARY.value,
        "limitations": (
            "boundary is contract-only",
            "not sync runtime or reconciliation engine",
        ),
    }
    return ShellSummaryNoSyncRuntimeBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_summary_no_generation_boundary() -> ShellSummaryNoGenerationBoundary:
    payload: dict[str, Any] = {
        "no_generation_boundary_id": _NO_GENERATION_ID,
        "schema_version": P2_8_C_NO_GENERATION_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "report_generator_created": False,
        "docs_generator_created": False,
        "summary_generator_created": False,
        "report_publisher_created": False,
        "docs_publisher_created": False,
        "generated_docs": False,
        "generated_reports": False,
        "generated_summary": False,
        "boundary_active": True,
        "truth_label": ShellStateSummaryTruthBoundary.NO_GENERATION_BOUNDARY.value,
        "limitations": (
            "boundary is contract-only",
            "not report/docs/summary generator runtime",
        ),
    }
    return ShellSummaryNoGenerationBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_summary_no_write_boundary() -> ShellSummaryNoWriteBoundary:
    payload: dict[str, Any] = {
        "no_write_boundary_id": _NO_WRITE_ID,
        "schema_version": P2_8_C_NO_WRITE_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "trace_written": False,
        "memory_written": False,
        "storage_written": False,
        "database_written": False,
        "docs_written": False,
        "reports_written": False,
        "fix_written": False,
        "refresh_written": False,
        "boundary_active": True,
        "truth_label": ShellStateSummaryTruthBoundary.NO_WRITE_BOUNDARY.value,
        "limitations": (
            "boundary prevents trace/memory/storage/docs/report writes",
            "not write layer implementation",
        ),
    }
    boundary = ShellSummaryNoWriteBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_trace_memory_storage_report_docs_writes(boundary)
    return boundary


def build_shell_state_summary_boundary_result(
    read_model_result: P28BShellStateReadModelResult | None = None,
) -> ShellStateSummaryBoundaryResult:
    if read_model_result is None:
        read_model_result = build_p2_8_b_shell_state_read_model_result()
    summary_gate = build_shell_state_summary_gate(read_model_result)
    docs_summary = build_shell_docs_index_summary(read_model_result)
    report_summary = build_shell_report_index_summary(read_model_result)
    state_summary = build_shell_state_read_only_summary(
        read_model_result,
        docs_summary=docs_summary,
        report_summary=report_summary,
    )
    summary_bundle = build_shell_state_summary_bundle(read_model_result)
    sync_descriptor = build_shell_state_sync_descriptor(read_model_result)
    sync_candidate = build_shell_state_sync_candidate(read_model_result)
    drift = build_shell_reference_drift_descriptor(read_model_result)
    missing = build_shell_reference_missing_descriptor(read_model_result)
    stale = build_shell_reference_stale_descriptor(read_model_result)
    comparison = build_shell_source_comparison_descriptor(read_model_result)
    limitation = build_shell_summary_limitation_descriptor(state_summary)
    availability = build_shell_read_only_summary_availability(summary_bundle)
    no_sync = build_shell_summary_no_sync_runtime_boundary()
    no_generation = build_shell_summary_no_generation_boundary()
    no_write = build_shell_summary_no_write_boundary()
    assert_drift_missing_stale_do_not_repair(drift, missing, stale)
    payload: dict[str, Any] = {
        "boundary_result_id": _BOUNDARY_RESULT_ID,
        "schema_version": P2_8_C_BOUNDARY_RESULT_VERSION,
        "section_id": P2_8_C_SECTION_ID,
        "created_for_pack": P2_8_C_PACK_ID,
        "official_section_name": P2_8_C_OFFICIAL_SECTION_NAME,
        "summary_gate": summary_gate,
        "docs_index_summary": docs_summary,
        "report_index_summary": report_summary,
        "state_read_only_summary": state_summary,
        "summary_bundle": summary_bundle,
        "sync_descriptors": (sync_descriptor,),
        "sync_candidates": (sync_candidate,),
        "drift_descriptors": (drift,),
        "missing_descriptors": (missing,),
        "stale_descriptors": (stale,),
        "source_comparisons": (comparison,),
        "summary_limitations": (limitation,),
        "availability": availability,
        "no_sync_runtime_boundary": no_sync,
        "no_generation_boundary": no_generation,
        "no_write_boundary": no_write,
        "creates_sync_runtime": False,
        "creates_reconciliation_engine": False,
        "creates_generator_runtime": False,
        "creates_write_path": False,
        "creates_product_behavior": False,
        "truth_label": ShellStateSummaryTruthBoundary.READ_ONLY_SUMMARY_ONLY.value,
        "limitations": (
            "summary boundary result bundles contracts only",
            "no sync runtime, generator runtime, write path, or product behavior",
        ),
    }
    boundary = ShellStateSummaryBoundaryResult(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_summary_boundary_result_is_contract_only(boundary)
    return boundary


def build_p2_8_c_side_effect_proof() -> P28CSideEffectProof:
    return P28CSideEffectProof()


def build_p2_8_c_shell_state_summary_result() -> P28CShellStateSummaryResult:
    read_model_result = build_p2_8_b_shell_state_read_model_result()
    boundary = build_shell_state_summary_boundary_result(read_model_result)
    side_effects = build_p2_8_c_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_8_C_RESULT_VERSION,
        "pack_id": P2_8_C_PACK_ID,
        "section_id": P2_8_C_SECTION_ID,
        "official_section_name": P2_8_C_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_8_C_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_8_C_DEPENDENCY_PACK,
        "p2_8_b_evidence_ref": _p2_8_b_evidence_ref(read_model_result),
        "p2_8_b_read_model_result_ref": _read_model_result_ref(read_model_result),
        "p2_8_b_report_index_ref": _report_index_ref(read_model_result),
        "p2_8_b_docs_index_ref": _docs_index_ref(read_model_result),
        "summary_gate": boundary.summary_gate,
        "docs_index_summary": boundary.docs_index_summary,
        "report_index_summary": boundary.report_index_summary,
        "state_read_only_summary": boundary.state_read_only_summary,
        "summary_bundle": boundary.summary_bundle,
        "sync_descriptors": boundary.sync_descriptors,
        "sync_candidates": boundary.sync_candidates,
        "drift_descriptors": boundary.drift_descriptors,
        "missing_descriptors": boundary.missing_descriptors,
        "stale_descriptors": boundary.stale_descriptors,
        "source_comparisons": boundary.source_comparisons,
        "summary_limitations": boundary.summary_limitations,
        "availability": boundary.availability,
        "no_sync_runtime_boundary": boundary.no_sync_runtime_boundary,
        "no_generation_boundary": boundary.no_generation_boundary,
        "no_write_boundary": boundary.no_write_boundary,
        "boundary_result": boundary,
        "truth_labels": tuple(label.value for label in ShellStateSummaryTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_8_C_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P28CShellStateSummaryResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_8_c_does_not_start_future_work(result)
    assert_p2_8_c_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_8_c_result(
    result: P28CShellStateSummaryResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_c_shell_state_summary_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_state_summary_boundary(
    result: P28CShellStateSummaryResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_c_shell_state_summary_result()
    boundary = result.boundary_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.summary_gate.gate_status.value}",
            f"docs_refs={result.docs_index_summary.docs_ref_count}",
            f"report_refs={result.report_index_summary.report_ref_count}",
            f"next={result.next_pack}",
            f"sync_runtime={str(boundary.creates_sync_runtime).lower()}",
            f"generator_runtime={str(boundary.creates_generator_runtime).lower()}",
            f"write_path={str(boundary.creates_write_path).lower()}",
            f"product_behavior={str(boundary.creates_product_behavior).lower()}",
        )
    )
