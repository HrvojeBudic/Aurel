"""P2.8-B Shell State read models / report-docs index contracts.

Contract-only read-model expansion over P2.8-A Shell State / Reports / Docs
foundation evidence. This module defines read model gate, registry, inventory,
section status, state snapshot read model, report/docs indexes, query/filter/sort
descriptors, availability, no-generation/no-runtime-mutation/no-write
boundaries, expansion result, side-effect proof, and pack result.

Core law:
  - Read model registry is not query runtime.
  - Read model inventory is not source-of-truth duplication.
  - Section status read model is not mutable Shell state.
  - Shell state snapshot read model is not live Shell state.
  - Report index is not agent/REPORTS.md replacement.
  - Docs index is not docs source-of-truth.
  - Query/filter/sort descriptors do not execute.
  - Report/docs family grouping does not generate reports/docs.

It does not create live Shell state runtime, Shell runtime, session state engine,
query runtime, filter runtime, sort runtime, persistent state store, database
persistence, storage write, trace write, memory write, report generator runtime,
docs generator runtime, report publisher, docs publisher, product UI, product
behavior, CLI runner, TUI runtime, command execution, runtime dispatch,
permission enforcement, Custos decisioning, approval runtime, LIVE,
TRACE_VERIFIED, release scope, P2.8-C, P2.8-D, P2.9, P2.10, or P2.13.
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
    P2_8_A_VALIDATION_REF,
    P28AShellStateFoundationResult,
    build_p2_8_a_shell_state_foundation_result,
)

P2_8_B_PACK_ID = "P2.8-B"
P2_8_B_SECTION_ID = "P2.8"
P2_8_B_OFFICIAL_SECTION_NAME = "Shell State / Reports / Docs"
P2_8_B_DEPENDENCY_PACK = P2_8_A_PACK_ID
P2_8_B_NEXT_PACK = "P2.8-C"
P2_8_B_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.8.6",
    "P2.8.7",
    "P2.8.8",
    "P2.8.9",
    "P2.8.10",
)
P2_8_B_REPORT_FILENAME = "P2_8_B_SHELL_STATE_READ_MODELS_REPORT_INDEX.md"
P2_8_B_REPORT_PATH = f"agent/reports/{P2_8_B_REPORT_FILENAME}"

P2_8_A_COMMIT_REF = "c6b995a"

P2_8_B_GATE_VERSION = "p2_8_b_shell_state_read_model_gate.v1"
P2_8_B_ENTRY_VERSION = "p2_8_b_shell_state_read_model_entry.v1"
P2_8_B_REGISTRY_VERSION = "p2_8_b_shell_state_read_model_registry.v1"
P2_8_B_INVENTORY_VERSION = "p2_8_b_shell_state_read_model_inventory.v1"
P2_8_B_SECTION_STATUS_VERSION = "p2_8_b_shell_section_status_read_model.v1"
P2_8_B_STATE_SNAPSHOT_VERSION = "p2_8_b_shell_state_snapshot_read_model.v1"
P2_8_B_REPORT_INDEX_VERSION = "p2_8_b_shell_report_index_read_model.v1"
P2_8_B_REPORT_ENTRY_VERSION = "p2_8_b_shell_report_index_entry.v1"
P2_8_B_REPORT_FAMILY_VERSION = "p2_8_b_shell_report_family_grouping.v1"
P2_8_B_DOCS_INDEX_VERSION = "p2_8_b_shell_docs_index_read_model.v1"
P2_8_B_DOCS_ENTRY_VERSION = "p2_8_b_shell_docs_index_entry.v1"
P2_8_B_DOCS_FAMILY_VERSION = "p2_8_b_shell_docs_family_grouping.v1"
P2_8_B_QUERY_DESCRIPTOR_VERSION = "p2_8_b_shell_report_docs_query_descriptor.v1"
P2_8_B_FILTER_DESCRIPTOR_VERSION = "p2_8_b_shell_report_docs_filter_descriptor.v1"
P2_8_B_SORT_DESCRIPTOR_VERSION = "p2_8_b_shell_report_docs_sort_descriptor.v1"
P2_8_B_AVAILABILITY_VERSION = "p2_8_b_shell_read_model_availability_rollup.v1"
P2_8_B_NO_GENERATION_VERSION = "p2_8_b_shell_read_model_no_generation_boundary.v1"
P2_8_B_NO_RUNTIME_MUTATION_VERSION = (
    "p2_8_b_shell_read_model_no_runtime_mutation_boundary.v1"
)
P2_8_B_NO_WRITE_VERSION = (
    "p2_8_b_shell_read_model_no_trace_memory_storage_write_boundary.v1"
)
P2_8_B_EXPANSION_RESULT_VERSION = "p2_8_b_shell_state_read_model_expansion_result.v1"
P2_8_B_RESULT_VERSION = "p2_8_b_shell_state_read_model_pack_result.v1"

P2_8_B_TEST_REF = "tests/aurel_shell/test_shell_state_read_models.py"
P2_8_B_VALIDATION_REF = "agent/TESTS.md#P2.8-B"
P2_8_B_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_8_B_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_GATE_ID = "p2_8_b_shell_state_read_model_gate"
_REGISTRY_ID = "p2_8_b_shell_state_read_model_registry"
_INVENTORY_ID = "p2_8_b_shell_state_read_model_inventory"
_SECTION_STATUS_ID = "p2_8_b_shell_section_status_read_model"
_STATE_SNAPSHOT_ID = "p2_8_b_shell_state_snapshot_read_model"
_REPORT_INDEX_ID = "p2_8_b_shell_report_index_read_model"
_DOCS_INDEX_ID = "p2_8_b_shell_docs_index_read_model"
_AVAILABILITY_ID = "p2_8_b_shell_read_model_availability_rollup"
_NO_GENERATION_ID = "p2_8_b_shell_read_model_no_generation_boundary"
_NO_RUNTIME_MUTATION_ID = "p2_8_b_shell_read_model_no_runtime_mutation_boundary"
_NO_WRITE_ID = "p2_8_b_shell_read_model_no_write_boundary"
_EXPANSION_RESULT_ID = "p2_8_b_shell_state_read_model_expansion_result"

_READ_MODEL_MANIFEST: tuple[tuple[str, str, str], ...] = (
    (_GATE_ID, "READ_MODEL_GATE", ""),
    (_REGISTRY_ID, "READ_MODEL_REGISTRY", ""),
    (_INVENTORY_ID, "READ_MODEL_INVENTORY", ""),
    (_SECTION_STATUS_ID, "SECTION_STATUS_READ_MODEL", ""),
    (_STATE_SNAPSHOT_ID, "STATE_SNAPSHOT_READ_MODEL", ""),
    (_REPORT_INDEX_ID, "REPORT_INDEX_READ_MODEL", ""),
    (_DOCS_INDEX_ID, "DOCS_INDEX_READ_MODEL", ""),
    ("p2_8_b_shell_report_docs_query_descriptor", "QUERY_DESCRIPTOR", P2_8_B_NEXT_PACK),
    (
        "p2_8_b_shell_report_docs_filter_descriptor",
        "FILTER_DESCRIPTOR",
        P2_8_B_NEXT_PACK,
    ),
    ("p2_8_b_shell_report_docs_sort_descriptor", "SORT_DESCRIPTOR", P2_8_B_NEXT_PACK),
    (_AVAILABILITY_ID, "READ_MODEL_AVAILABILITY_ROLLUP", ""),
    (_EXPANSION_RESULT_ID, "READ_MODEL_EXPANSION_RESULT", ""),
)

_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "live Shell state runtime",
    "Shell runtime",
    "session state engine",
    "query runtime",
    "filter runtime",
    "sort runtime",
    "persistent state store",
    "database persistence",
    "storage write",
    "trace write",
    "memory write",
    "report generator runtime",
    "docs generator runtime",
    "report publisher",
    "docs publisher",
    "permission enforcement",
    "product UI",
    "product behavior",
    "P2.8-C implementation",
    "P2.8-D implementation",
    "P2.9 implementation",
    "P2.10 implementation",
    "P2.13 implementation",
)


class ShellStateReadModelGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellReadModelAvailabilityStatus(str, Enum):
    CONTRACT_AVAILABLE = "CONTRACT_AVAILABLE"
    UNAVAILABLE_RUNTIME_REQUIRED = "UNAVAILABLE_RUNTIME_REQUIRED"
    UNAVAILABLE_P2_8_C_REQUIRED = "UNAVAILABLE_P2_8_C_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellReportDocsDescriptorMode(str, Enum):
    DESCRIPTOR_ONLY = "DESCRIPTOR_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class ShellStateReadModelTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    SHELL_STATE_READ_MODEL_ONLY = "SHELL_STATE_READ_MODEL_ONLY"
    READ_MODEL_REGISTRY_ONLY = "READ_MODEL_REGISTRY_ONLY"
    READ_MODEL_INVENTORY_ONLY = "READ_MODEL_INVENTORY_ONLY"
    SECTION_STATUS_READ_MODEL_ONLY = "SECTION_STATUS_READ_MODEL_ONLY"
    STATE_SNAPSHOT_READ_MODEL_ONLY = "STATE_SNAPSHOT_READ_MODEL_ONLY"
    REPORT_INDEX_READ_MODEL_ONLY = "REPORT_INDEX_READ_MODEL_ONLY"
    REPORT_INDEX_ENTRY_ONLY = "REPORT_INDEX_ENTRY_ONLY"
    REPORT_FAMILY_GROUPING_ONLY = "REPORT_FAMILY_GROUPING_ONLY"
    DOCS_INDEX_READ_MODEL_ONLY = "DOCS_INDEX_READ_MODEL_ONLY"
    DOCS_INDEX_ENTRY_ONLY = "DOCS_INDEX_ENTRY_ONLY"
    DOCS_FAMILY_GROUPING_ONLY = "DOCS_FAMILY_GROUPING_ONLY"
    QUERY_DESCRIPTOR_ONLY = "QUERY_DESCRIPTOR_ONLY"
    FILTER_DESCRIPTOR_ONLY = "FILTER_DESCRIPTOR_ONLY"
    SORT_DESCRIPTOR_ONLY = "SORT_DESCRIPTOR_ONLY"
    READ_MODEL_AVAILABILITY_ONLY = "READ_MODEL_AVAILABILITY_ONLY"
    NO_REPORT_DOCS_GENERATION_BOUNDARY = "NO_REPORT_DOCS_GENERATION_BOUNDARY"
    NO_RUNTIME_STATE_MUTATION_BOUNDARY = "NO_RUNTIME_STATE_MUTATION_BOUNDARY"
    NO_TRACE_MEMORY_STORAGE_WRITE_BOUNDARY = "NO_TRACE_MEMORY_STORAGE_WRITE_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
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
    NOT_REPORT_GENERATOR = "NOT_REPORT_GENERATOR"
    NOT_DOCS_GENERATOR = "NOT_DOCS_GENERATOR"
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
    NOT_P2_8_C_IMPLEMENTATION = "NOT_P2_8_C_IMPLEMENTATION"
    NOT_P2_8_D_IMPLEMENTATION = "NOT_P2_8_D_IMPLEMENTATION"
    NOT_P2_9_IMPLEMENTATION = "NOT_P2_9_IMPLEMENTATION"
    NOT_P2_10_IMPLEMENTATION = "NOT_P2_10_IMPLEMENTATION"
    NOT_P2_13_IMPLEMENTATION = "NOT_P2_13_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class P28BSideEffectProof(_CanonicalMixin):
    shell_runtime_created: bool = False
    shell_state_runtime_created: bool = False
    session_state_engine_created: bool = False
    shell_state_mutated: bool = False
    runtime_state_mutated: bool = False
    query_runtime_created: bool = False
    filter_runtime_created: bool = False
    sort_runtime_created: bool = False
    persistent_state_store_created: bool = False
    database_persistence_created: bool = False
    storage_written: bool = False
    trace_written: bool = False
    memory_written: bool = False
    report_generator_created: bool = False
    docs_generator_created: bool = False
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
    p2_8_c_started: bool = False
    p2_8_d_started: bool = False
    p2_9_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellStateReadModelGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_foundation_result_ref: str
    dependency_state_snapshot_ref: str
    dependency_report_registry_ref: str
    dependency_docs_registry_ref: str
    dependency_governance_source_boundary_ref: str
    dependency_no_runtime_mutation_boundary_ref: str
    dependency_no_write_boundary_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellStateReadModelGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellStateReadModelEntry(_CanonicalMixin):
    entry_id: str
    section_id: str
    created_for_pack: str
    read_model_name: str
    read_model_kind: str
    source_ref: str
    availability_status: ShellReadModelAvailabilityStatus
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellStateReadModelRegistry(_CanonicalMixin):
    registry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    registry_entries: tuple[ShellStateReadModelEntry, ...]
    source_foundation_ref: str
    is_query_runtime: bool
    executes_queries: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class ShellStateReadModelInventory(_CanonicalMixin):
    inventory_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    read_model_entries: tuple[str, ...]
    contract_refs: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    is_source_of_truth: bool
    duplicates_agent_governance: bool
    truth_label: str
    limitations: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True)
class ShellSectionStatusReadModel(_CanonicalMixin):
    section_status_read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    section_scope: str
    source_foundation_ref: str
    status_label: str
    is_mutable_shell_state: bool
    mutates_shell_state: bool
    mutates_runtime_state: bool
    truth_label: str
    limitations: tuple[str, ...]
    status_hash: str


@dataclass(frozen=True)
class ShellStateSnapshotReadModel(_CanonicalMixin):
    state_snapshot_read_model_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_snapshot_ref: str
    source_foundation_ref: str
    snapshot_scope: str
    is_live_shell_state: bool
    is_session_state_engine: bool
    mutates_shell_state: bool
    truth_label: str
    limitations: tuple[str, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class ShellReportIndexEntry(_CanonicalMixin):
    report_entry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    report_ref: str
    report_family: str
    source_pack: str
    checkpoint_range: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellReportFamilyGrouping(_CanonicalMixin):
    report_family_grouping_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    family_name: str
    report_refs: tuple[str, ...]
    grouping_reason: str
    is_report_generation: bool
    truth_label: str
    limitations: tuple[str, ...]
    grouping_hash: str


@dataclass(frozen=True)
class ShellReportIndexReadModel(_CanonicalMixin):
    report_index_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_agent_reports_ref: str
    source_report_registry_ref: str
    report_index_entries: tuple[ShellReportIndexEntry, ...]
    report_family_groupings: tuple[ShellReportFamilyGrouping, ...]
    is_agent_reports_replacement: bool
    is_report_generation: bool
    publishes_reports: bool
    truth_label: str
    limitations: tuple[str, ...]
    report_index_hash: str


@dataclass(frozen=True)
class ShellDocsIndexEntry(_CanonicalMixin):
    docs_entry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    docs_ref: str
    docs_family: str
    source_pack: str
    checkpoint_range: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellDocsFamilyGrouping(_CanonicalMixin):
    docs_family_grouping_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    family_name: str
    docs_refs: tuple[str, ...]
    grouping_reason: str
    is_docs_generation: bool
    truth_label: str
    limitations: tuple[str, ...]
    grouping_hash: str


@dataclass(frozen=True)
class ShellDocsIndexReadModel(_CanonicalMixin):
    docs_index_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_docs_registry_ref: str
    docs_index_entries: tuple[ShellDocsIndexEntry, ...]
    docs_family_groupings: tuple[ShellDocsFamilyGrouping, ...]
    is_docs_source_of_truth: bool
    is_docs_generation: bool
    publishes_docs: bool
    truth_label: str
    limitations: tuple[str, ...]
    docs_index_hash: str


@dataclass(frozen=True)
class ShellReportDocsQueryDescriptor(_CanonicalMixin):
    query_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    descriptor_mode: ShellReportDocsDescriptorMode
    query_scope: str
    query_fields: tuple[str, ...]
    query_reason: str
    is_query_runtime: bool
    executes_query: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellReportDocsFilterDescriptor(_CanonicalMixin):
    filter_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    descriptor_mode: ShellReportDocsDescriptorMode
    filter_scope: str
    filter_fields: tuple[str, ...]
    filter_reason: str
    is_filter_runtime: bool
    executes_filter: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellReportDocsSortDescriptor(_CanonicalMixin):
    sort_descriptor_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    descriptor_mode: ShellReportDocsDescriptorMode
    sort_scope: str
    sort_fields: tuple[str, ...]
    sort_reason: str
    is_sort_runtime: bool
    executes_sort: bool
    truth_label: str
    limitations: tuple[str, ...]
    descriptor_hash: str


@dataclass(frozen=True)
class ShellReadModelAvailabilityRollup(_CanonicalMixin):
    availability_rollup_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    available_read_models: tuple[str, ...]
    available_index_contracts: tuple[str, ...]
    available_descriptors: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    future_pack_refs: tuple[str, ...]
    enforces_permission: bool
    grants_permission: bool
    denies_permission: bool
    truth_label: str
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class ShellReadModelNoGenerationBoundary(_CanonicalMixin):
    no_generation_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    report_generator_created: bool
    docs_generator_created: bool
    report_publisher_created: bool
    docs_publisher_created: bool
    generated_docs: bool
    generated_reports: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellReadModelNoRuntimeMutationBoundary(_CanonicalMixin):
    no_runtime_mutation_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    shell_state_mutated: bool
    runtime_state_mutated: bool
    session_state_engine_created: bool
    query_runtime_created: bool
    filter_runtime_created: bool
    sort_runtime_created: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellReadModelNoTraceMemoryStorageWriteBoundary(_CanonicalMixin):
    no_write_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    trace_written: bool
    memory_written: bool
    storage_written: bool
    database_written: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellStateReadModelExpansionResult(_CanonicalMixin):
    expansion_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    read_model_gate: ShellStateReadModelGate
    read_model_registry: ShellStateReadModelRegistry
    read_model_inventory: ShellStateReadModelInventory
    section_status_read_model: ShellSectionStatusReadModel
    state_snapshot_read_model: ShellStateSnapshotReadModel
    report_index: ShellReportIndexReadModel
    docs_index: ShellDocsIndexReadModel
    query_descriptors: tuple[ShellReportDocsQueryDescriptor, ...]
    filter_descriptors: tuple[ShellReportDocsFilterDescriptor, ...]
    sort_descriptors: tuple[ShellReportDocsSortDescriptor, ...]
    availability_rollup: ShellReadModelAvailabilityRollup
    no_generation_boundary: ShellReadModelNoGenerationBoundary
    no_runtime_mutation_boundary: ShellReadModelNoRuntimeMutationBoundary
    no_write_boundary: ShellReadModelNoTraceMemoryStorageWriteBoundary
    creates_query_runtime: bool
    creates_generator_runtime: bool
    creates_write_path: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    expansion_hash: str


@dataclass(frozen=True)
class P28BShellStateReadModelResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_8_a_evidence_ref: str
    p2_8_a_foundation_result_ref: str
    p2_8_a_state_snapshot_ref: str
    p2_8_a_report_registry_ref: str
    p2_8_a_docs_registry_ref: str
    read_model_gate: ShellStateReadModelGate
    read_model_registry: ShellStateReadModelRegistry
    read_model_inventory: ShellStateReadModelInventory
    section_status_read_model: ShellSectionStatusReadModel
    state_snapshot_read_model: ShellStateSnapshotReadModel
    report_index: ShellReportIndexReadModel
    report_family_groupings: tuple[ShellReportFamilyGrouping, ...]
    docs_index: ShellDocsIndexReadModel
    docs_family_groupings: tuple[ShellDocsFamilyGrouping, ...]
    query_descriptors: tuple[ShellReportDocsQueryDescriptor, ...]
    filter_descriptors: tuple[ShellReportDocsFilterDescriptor, ...]
    sort_descriptors: tuple[ShellReportDocsSortDescriptor, ...]
    availability_rollup: ShellReadModelAvailabilityRollup
    no_generation_boundary: ShellReadModelNoGenerationBoundary
    no_runtime_mutation_boundary: ShellReadModelNoRuntimeMutationBoundary
    no_write_boundary: ShellReadModelNoTraceMemoryStorageWriteBoundary
    expansion_result: ShellStateReadModelExpansionResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P28BSideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _foundation_result_ref(result: P28AShellStateFoundationResult) -> str:
    foundation = result.foundation_result
    return (
        f"{foundation.foundation_result_id}:"
        f"hash={foundation.foundation_result_hash[:12]}"
    )


def _state_snapshot_ref(result: P28AShellStateFoundationResult) -> str:
    snapshot = result.snapshot_contract
    return f"{snapshot.snapshot_id}:hash={snapshot.snapshot_hash[:12]}"


def _report_registry_ref(result: P28AShellStateFoundationResult) -> str:
    registry = result.report_registry
    return f"{registry.report_registry_id}:hash={registry.registry_hash[:12]}"


def _docs_registry_ref(result: P28AShellStateFoundationResult) -> str:
    registry = result.docs_registry
    return f"{registry.docs_registry_id}:hash={registry.registry_hash[:12]}"


def _governance_boundary_ref(result: P28AShellStateFoundationResult) -> str:
    boundary = result.governance_source_boundary
    return (
        f"{boundary.governance_boundary_id}:"
        f"hash={boundary.governance_boundary_hash[:12]}"
    )


def _no_runtime_boundary_ref(result: P28AShellStateFoundationResult) -> str:
    boundary = result.no_runtime_mutation_boundary
    return f"{boundary.no_runtime_mutation_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _no_write_boundary_ref(result: P28AShellStateFoundationResult) -> str:
    boundary = result.no_write_boundary
    return f"{boundary.no_write_boundary_id}:hash={boundary.boundary_hash[:12]}"


def _p2_8_a_evidence_ref(result: P28AShellStateFoundationResult) -> str:
    return f"{P2_8_A_REPORT_PATH}:{result.result_hash[:12]}"


def assert_p2_8_a_foundation_result_available(
    result: P28AShellStateFoundationResult,
) -> None:
    if result.pack_id != P2_8_A_PACK_ID or result.starts_future_work:
        _reject(
            "P2.8-B requires a P2.8-A foundation result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.next_pack != P2_8_B_PACK_ID:
        _reject(
            "P2.8-B requires P2.8-A foundation pointing to P2.8-B",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if (
        result.foundation_result.creates_live_shell_state
        or result.foundation_result.creates_report_generator
        or result.foundation_result.creates_docs_generator
    ):
        _reject(
            "P2.8-A foundation dependency must not overclaim runtime/generation",
            field="foundation_result",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellStateReadModelGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.8-B gate must ignore OMNI evidence by operator instruction",
            field="omni_evidence_ignored_by_operator_instruction",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_read_model_gate_depends_on_p2_8_a(gate: ShellStateReadModelGate) -> None:
    if gate.dependency_pack != P2_8_A_PACK_ID or not gate.repo_evidence_gate_passed:
        _reject(
            "P2.8-B read model gate must depend on P2.8-A repo evidence",
            field="dependency_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_read_model_registry_is_not_query_runtime(
    registry: ShellStateReadModelRegistry,
) -> None:
    if registry.is_query_runtime or registry.executes_queries:
        _reject(
            "Read model registry must not execute queries",
            field="registry_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_read_model_inventory_does_not_duplicate_source_of_truth(
    inventory: ShellStateReadModelInventory,
) -> None:
    if inventory.is_source_of_truth or inventory.duplicates_agent_governance:
        _reject(
            "Read model inventory must not duplicate source-of-truth",
            field="inventory_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_section_status_read_model_does_not_mutate_shell_state(
    status: ShellSectionStatusReadModel,
) -> None:
    if status.is_mutable_shell_state or status.mutates_shell_state:
        _reject(
            "Section status read model must not mutate Shell state",
            field="section_status_read_model_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if status.mutates_runtime_state:
        _reject(
            "Section status read model must not mutate runtime state",
            field="section_status_read_model_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_state_snapshot_read_model_is_not_live_shell_state(
    snapshot: ShellStateSnapshotReadModel,
) -> None:
    if (
        snapshot.is_live_shell_state
        or snapshot.is_session_state_engine
        or snapshot.mutates_shell_state
    ):
        _reject(
            "State snapshot read model must not be live or mutating",
            field="state_snapshot_read_model_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_report_index_is_not_agent_reports_replacement(
    index: ShellReportIndexReadModel,
) -> None:
    if (
        index.is_agent_reports_replacement
        or index.is_report_generation
        or index.publishes_reports
    ):
        _reject(
            "Report index must remain read-model reference only",
            field="report_index_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_docs_index_is_not_docs_source_of_truth(
    index: ShellDocsIndexReadModel,
) -> None:
    if index.is_docs_source_of_truth or index.is_docs_generation or index.publishes_docs:
        _reject(
            "Docs index must remain read-model reference only",
            field="docs_index_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_report_docs_grouping_is_not_generation(
    grouping: ShellReportFamilyGrouping | ShellDocsFamilyGrouping,
) -> None:
    if isinstance(grouping, ShellReportFamilyGrouping):
        generated = grouping.is_report_generation
        field_name = "report_family_grouping_id"
    else:
        generated = grouping.is_docs_generation
        field_name = "docs_family_grouping_id"
    if generated:
        _reject(
            "Report/docs family grouping must not generate reports or docs",
            field=field_name,
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_query_filter_sort_descriptors_do_not_execute(
    query: ShellReportDocsQueryDescriptor,
    filter_descriptor: ShellReportDocsFilterDescriptor,
    sort: ShellReportDocsSortDescriptor,
) -> None:
    if query.is_query_runtime or query.executes_query:
        _reject(
            "Query descriptor must not execute queries",
            field="query_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if filter_descriptor.is_filter_runtime or filter_descriptor.executes_filter:
        _reject(
            "Filter descriptor must not execute filters",
            field="filter_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if sort.is_sort_runtime or sort.executes_sort:
        _reject(
            "Sort descriptor must not execute sorts",
            field="sort_descriptor_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_availability_rollup_is_not_permission_enforcement(
    availability: ShellReadModelAvailabilityRollup,
) -> None:
    if (
        availability.enforces_permission
        or availability.grants_permission
        or availability.denies_permission
    ):
        _reject(
            "Read-model availability rollup must not enforce permissions",
            field="availability_rollup_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_report_docs_generation(
    boundary: ShellReadModelNoGenerationBoundary,
) -> None:
    if not boundary.boundary_active or any(
        (
            boundary.report_generator_created,
            boundary.docs_generator_created,
            boundary.report_publisher_created,
            boundary.docs_publisher_created,
            boundary.generated_docs,
            boundary.generated_reports,
        )
    ):
        _reject(
            "No-generation boundary must be active with all flags false",
            field="no_generation_boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_runtime_state_mutation(
    boundary: ShellReadModelNoRuntimeMutationBoundary,
) -> None:
    if not boundary.boundary_active or any(
        (
            boundary.shell_state_mutated,
            boundary.runtime_state_mutated,
            boundary.session_state_engine_created,
            boundary.query_runtime_created,
            boundary.filter_runtime_created,
            boundary.sort_runtime_created,
        )
    ):
        _reject(
            "No-runtime-mutation boundary must be active with all flags false",
            field="no_runtime_mutation_boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_trace_memory_storage_writes(
    boundary: ShellReadModelNoTraceMemoryStorageWriteBoundary,
) -> None:
    if not boundary.boundary_active or any(
        (
            boundary.trace_written,
            boundary.memory_written,
            boundary.storage_written,
            boundary.database_written,
        )
    ):
        _reject(
            "No-write boundary must be active with all write flags false",
            field="no_write_boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_expansion_result_is_contract_only(
    expansion: ShellStateReadModelExpansionResult,
) -> None:
    if (
        expansion.creates_query_runtime
        or expansion.creates_generator_runtime
        or expansion.creates_write_path
        or expansion.creates_product_behavior
    ):
        _reject(
            "P2.8-B expansion result must remain contract-only",
            field="expansion_result_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_b_does_not_start_future_work(
    result: P28BShellStateReadModelResult,
) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or result.next_pack != P2_8_B_NEXT_PACK
        or proof.p2_8_c_started
        or proof.p2_8_d_started
        or proof.p2_9_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.8-B must not start future packs",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_b_side_effects_all_false(proof: P28BSideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.8-B side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def build_shell_state_read_model_gate(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellStateReadModelGate:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    assert_p2_8_a_foundation_result_available(foundation_result)
    payload: dict[str, Any] = {
        "gate_id": _GATE_ID,
        "schema_version": P2_8_B_GATE_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "official_section_name": P2_8_B_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_8_B_DEPENDENCY_PACK,
        "dependency_report_ref": P2_8_A_REPORT_PATH,
        "dependency_commit_ref": P2_8_A_COMMIT_REF,
        "dependency_validation_ref": P2_8_A_VALIDATION_REF,
        "dependency_foundation_result_ref": _foundation_result_ref(foundation_result),
        "dependency_state_snapshot_ref": _state_snapshot_ref(foundation_result),
        "dependency_report_registry_ref": _report_registry_ref(foundation_result),
        "dependency_docs_registry_ref": _docs_registry_ref(foundation_result),
        "dependency_governance_source_boundary_ref": _governance_boundary_ref(
            foundation_result
        ),
        "dependency_no_runtime_mutation_boundary_ref": _no_runtime_boundary_ref(
            foundation_result
        ),
        "dependency_no_write_boundary_ref": _no_write_boundary_ref(foundation_result),
        "dependency_side_effect_proof_ref": "P28ASideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellStateReadModelGateStatus.READY,
        "truth_label": ShellStateReadModelTruthBoundary.SHELL_STATE_READ_MODEL_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create Shell state runtime",
        ),
    }
    gate = ShellStateReadModelGate(**payload, gate_hash=_hash_payload(payload))
    assert_read_model_gate_depends_on_p2_8_a(gate)
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_shell_state_read_model_entry(
    read_model_name: str = _SECTION_STATUS_ID,
    read_model_kind: str = "SECTION_STATUS_READ_MODEL",
    source_ref: str = "P2.8-A:ShellStateFoundationResult",
    *,
    availability_status: ShellReadModelAvailabilityStatus = (
        ShellReadModelAvailabilityStatus.CONTRACT_AVAILABLE
    ),
) -> ShellStateReadModelEntry:
    payload: dict[str, Any] = {
        "entry_id": f"p2_8_b_entry_{read_model_name}",
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "read_model_name": read_model_name,
        "read_model_kind": read_model_kind,
        "source_ref": source_ref,
        "availability_status": availability_status,
        "truth_label": ShellStateReadModelTruthBoundary.SHELL_STATE_READ_MODEL_ONLY.value,
        "limitations": (
            "entry is descriptor/read-model metadata only",
            "entry does not create runtime query execution",
        ),
    }
    return ShellStateReadModelEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_state_read_model_registry(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellStateReadModelRegistry:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    source_ref = _foundation_result_ref(foundation_result)
    entries = tuple(
        build_shell_state_read_model_entry(
            read_model_name,
            read_model_kind,
            source_ref,
        )
        for read_model_name, read_model_kind, _future_pack in _READ_MODEL_MANIFEST
    )
    payload: dict[str, Any] = {
        "registry_id": _REGISTRY_ID,
        "schema_version": P2_8_B_REGISTRY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "official_section_name": P2_8_B_OFFICIAL_SECTION_NAME,
        "registry_entries": entries,
        "source_foundation_ref": source_ref,
        "is_query_runtime": False,
        "executes_queries": False,
        "truth_label": ShellStateReadModelTruthBoundary.READ_MODEL_REGISTRY_ONLY.value,
        "limitations": (
            "registry is a non-executable view catalog",
            "registry does not query runtime, database, or storage",
        ),
    }
    registry = ShellStateReadModelRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_read_model_registry_is_not_query_runtime(registry)
    return registry


def build_shell_state_read_model_inventory() -> ShellStateReadModelInventory:
    entries = tuple(read_model_id for read_model_id, _kind, _pack in _READ_MODEL_MANIFEST)
    payload: dict[str, Any] = {
        "inventory_id": _INVENTORY_ID,
        "schema_version": P2_8_B_INVENTORY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "read_model_entries": entries,
        "contract_refs": (
            "ShellStateReadModelGate",
            "ShellStateReadModelRegistry",
            "ShellSectionStatusReadModel",
            "ShellStateSnapshotReadModel",
            "ShellReportIndexReadModel",
            "ShellDocsIndexReadModel",
        ),
        "source_report_refs": (P2_8_A_REPORT_PATH, P2_8_B_REPORT_PATH),
        "is_source_of_truth": False,
        "duplicates_agent_governance": False,
        "truth_label": ShellStateReadModelTruthBoundary.READ_MODEL_INVENTORY_ONLY.value,
        "limitations": (
            "inventory references source evidence only",
            "inventory does not duplicate agent/ governance",
        ),
    }
    inventory = ShellStateReadModelInventory(
        **payload,
        inventory_hash=_hash_payload(payload),
    )
    assert_read_model_inventory_does_not_duplicate_source_of_truth(inventory)
    return inventory


def build_shell_section_status_read_model(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellSectionStatusReadModel:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    payload: dict[str, Any] = {
        "section_status_read_model_id": _SECTION_STATUS_ID,
        "schema_version": P2_8_B_SECTION_STATUS_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "official_section_name": P2_8_B_OFFICIAL_SECTION_NAME,
        "section_scope": "P2.8.0-P2.8.10 contract/read-model scope",
        "source_foundation_ref": _foundation_result_ref(foundation_result),
        "status_label": "OPENED_AND_EXPANDED_CONTRACT_ONLY",
        "is_mutable_shell_state": False,
        "mutates_shell_state": False,
        "mutates_runtime_state": False,
        "truth_label": (
            ShellStateReadModelTruthBoundary.SECTION_STATUS_READ_MODEL_ONLY.value
        ),
        "limitations": (
            "section status is read-only",
            "P2.8-B complete is not P2.8 complete",
        ),
    }
    status = ShellSectionStatusReadModel(**payload, status_hash=_hash_payload(payload))
    assert_section_status_read_model_does_not_mutate_shell_state(status)
    return status


def build_shell_state_snapshot_read_model(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellStateSnapshotReadModel:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    payload: dict[str, Any] = {
        "state_snapshot_read_model_id": _STATE_SNAPSHOT_ID,
        "schema_version": P2_8_B_STATE_SNAPSHOT_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "source_snapshot_ref": _state_snapshot_ref(foundation_result),
        "source_foundation_ref": _foundation_result_ref(foundation_result),
        "snapshot_scope": "P2.8-A snapshot contract projected as read model",
        "is_live_shell_state": False,
        "is_session_state_engine": False,
        "mutates_shell_state": False,
        "truth_label": (
            ShellStateReadModelTruthBoundary.STATE_SNAPSHOT_READ_MODEL_ONLY.value
        ),
        "limitations": (
            "snapshot read model is not live Shell state",
            "snapshot read model does not create a session state engine",
        ),
    }
    snapshot = ShellStateSnapshotReadModel(
        **payload,
        snapshot_hash=_hash_payload(payload),
    )
    assert_state_snapshot_read_model_is_not_live_shell_state(snapshot)
    return snapshot


def build_shell_report_index_entry(
    report_ref: str = P2_8_A_REPORT_PATH,
    report_family: str = "shell_state_reports_docs",
    source_pack: str = P2_8_A_PACK_ID,
    checkpoint_range: str = "P2.8.0-P2.8.5",
) -> ShellReportIndexEntry:
    suffix = source_pack.lower().replace(".", "_").replace("-", "_")
    payload: dict[str, Any] = {
        "report_entry_id": f"p2_8_b_shell_report_index_entry_{suffix}",
        "schema_version": P2_8_B_REPORT_ENTRY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "report_ref": report_ref,
        "report_family": report_family,
        "source_pack": source_pack,
        "checkpoint_range": checkpoint_range,
        "truth_label": ShellStateReadModelTruthBoundary.REPORT_INDEX_ENTRY_ONLY.value,
        "limitations": (
            "report index entry is a reference only",
            "entry does not generate or publish reports",
        ),
    }
    return ShellReportIndexEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_report_family_grouping(
    report_refs: tuple[str, ...] = (P2_8_A_REPORT_PATH,),
) -> ShellReportFamilyGrouping:
    payload: dict[str, Any] = {
        "report_family_grouping_id": "p2_8_b_shell_report_family_grouping",
        "schema_version": P2_8_B_REPORT_FAMILY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "family_name": "shell_state_reports_docs",
        "report_refs": report_refs,
        "grouping_reason": "semantic grouping for P2.8 report references",
        "is_report_generation": False,
        "truth_label": (
            ShellStateReadModelTruthBoundary.REPORT_FAMILY_GROUPING_ONLY.value
        ),
        "limitations": (
            "family grouping is semantic clustering only",
            "family grouping does not generate reports",
        ),
    }
    grouping = ShellReportFamilyGrouping(
        **payload,
        grouping_hash=_hash_payload(payload),
    )
    assert_report_docs_grouping_is_not_generation(grouping)
    return grouping


def build_shell_report_index_read_model(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellReportIndexReadModel:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    entries = tuple(
        build_shell_report_index_entry(
            entry.report_ref,
            "shell_state_reports_docs",
            entry.source_pack,
            entry.source_checkpoint_range,
        )
        for entry in foundation_result.report_registry.report_entries
    )
    grouping = build_shell_report_family_grouping(
        tuple(entry.report_ref for entry in entries),
    )
    payload: dict[str, Any] = {
        "report_index_id": _REPORT_INDEX_ID,
        "schema_version": P2_8_B_REPORT_INDEX_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "source_agent_reports_ref": "agent/REPORTS.md",
        "source_report_registry_ref": _report_registry_ref(foundation_result),
        "report_index_entries": entries,
        "report_family_groupings": (grouping,),
        "is_agent_reports_replacement": False,
        "is_report_generation": False,
        "publishes_reports": False,
        "truth_label": (
            ShellStateReadModelTruthBoundary.REPORT_INDEX_READ_MODEL_ONLY.value
        ),
        "limitations": (
            "report index reads references only",
            "report index does not replace agent/REPORTS.md",
        ),
    }
    index = ShellReportIndexReadModel(
        **payload,
        report_index_hash=_hash_payload(payload),
    )
    assert_report_index_is_not_agent_reports_replacement(index)
    return index


def build_shell_docs_index_entry(
    docs_ref: str = "agent/AGENT.md",
    docs_family: str = "agent_governance",
    source_pack: str = "agent/",
    checkpoint_range: str = "agent/",
) -> ShellDocsIndexEntry:
    suffix = docs_ref.replace("/", "_").replace(".", "_").replace("-", "_")
    payload: dict[str, Any] = {
        "docs_entry_id": f"p2_8_b_shell_docs_index_entry_{suffix}",
        "schema_version": P2_8_B_DOCS_ENTRY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "docs_ref": docs_ref,
        "docs_family": docs_family,
        "source_pack": source_pack,
        "checkpoint_range": checkpoint_range,
        "truth_label": ShellStateReadModelTruthBoundary.DOCS_INDEX_ENTRY_ONLY.value,
        "limitations": (
            "docs index entry is a reference only",
            "entry does not generate or publish docs",
        ),
    }
    return ShellDocsIndexEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_docs_family_grouping(
    docs_refs: tuple[str, ...] = ("agent/AGENT.md", "agent/CODEOPS.md"),
) -> ShellDocsFamilyGrouping:
    payload: dict[str, Any] = {
        "docs_family_grouping_id": "p2_8_b_shell_docs_family_grouping",
        "schema_version": P2_8_B_DOCS_FAMILY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "family_name": "agent_governance",
        "docs_refs": docs_refs,
        "grouping_reason": "semantic grouping for governance docs references",
        "is_docs_generation": False,
        "truth_label": ShellStateReadModelTruthBoundary.DOCS_FAMILY_GROUPING_ONLY.value,
        "limitations": (
            "family grouping is semantic clustering only",
            "family grouping does not generate docs",
        ),
    }
    grouping = ShellDocsFamilyGrouping(**payload, grouping_hash=_hash_payload(payload))
    assert_report_docs_grouping_is_not_generation(grouping)
    return grouping


def build_shell_docs_index_read_model(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellDocsIndexReadModel:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    entries = tuple(
        build_shell_docs_index_entry(
            entry.docs_ref,
            "agent_governance",
            entry.source_pack,
            entry.source_checkpoint_range,
        )
        for entry in foundation_result.docs_registry.docs_entries
    )
    grouping = build_shell_docs_family_grouping(tuple(entry.docs_ref for entry in entries))
    payload: dict[str, Any] = {
        "docs_index_id": _DOCS_INDEX_ID,
        "schema_version": P2_8_B_DOCS_INDEX_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "source_docs_registry_ref": _docs_registry_ref(foundation_result),
        "docs_index_entries": entries,
        "docs_family_groupings": (grouping,),
        "is_docs_source_of_truth": False,
        "is_docs_generation": False,
        "publishes_docs": False,
        "truth_label": ShellStateReadModelTruthBoundary.DOCS_INDEX_READ_MODEL_ONLY.value,
        "limitations": (
            "docs index reads references only",
            "docs index does not create docs source-of-truth",
        ),
    }
    index = ShellDocsIndexReadModel(**payload, docs_index_hash=_hash_payload(payload))
    assert_docs_index_is_not_docs_source_of_truth(index)
    return index


def build_shell_report_docs_query_descriptor() -> ShellReportDocsQueryDescriptor:
    payload: dict[str, Any] = {
        "query_descriptor_id": "p2_8_b_shell_report_docs_query_descriptor",
        "schema_version": P2_8_B_QUERY_DESCRIPTOR_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "descriptor_mode": ShellReportDocsDescriptorMode.DESCRIPTOR_ONLY,
        "query_scope": "report_docs_reference_query_shape",
        "query_fields": ("ref", "source_pack", "family", "checkpoint_range"),
        "query_reason": "future read-only inspection grammar",
        "is_query_runtime": False,
        "executes_query": False,
        "truth_label": ShellStateReadModelTruthBoundary.QUERY_DESCRIPTOR_ONLY.value,
        "limitations": (
            "query descriptor is not query runtime",
            "descriptor does not query runtime, database, or storage",
        ),
    }
    return ShellReportDocsQueryDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_report_docs_filter_descriptor() -> ShellReportDocsFilterDescriptor:
    payload: dict[str, Any] = {
        "filter_descriptor_id": "p2_8_b_shell_report_docs_filter_descriptor",
        "schema_version": P2_8_B_FILTER_DESCRIPTOR_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "descriptor_mode": ShellReportDocsDescriptorMode.DESCRIPTOR_ONLY,
        "filter_scope": "report_docs_reference_filter_shape",
        "filter_fields": ("source_pack", "family", "truth_label"),
        "filter_reason": "future read-only filter grammar",
        "is_filter_runtime": False,
        "executes_filter": False,
        "truth_label": ShellStateReadModelTruthBoundary.FILTER_DESCRIPTOR_ONLY.value,
        "limitations": (
            "filter descriptor is not filter runtime",
            "descriptor does not filter live data",
        ),
    }
    return ShellReportDocsFilterDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_report_docs_sort_descriptor() -> ShellReportDocsSortDescriptor:
    payload: dict[str, Any] = {
        "sort_descriptor_id": "p2_8_b_shell_report_docs_sort_descriptor",
        "schema_version": P2_8_B_SORT_DESCRIPTOR_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "descriptor_mode": ShellReportDocsDescriptorMode.DESCRIPTOR_ONLY,
        "sort_scope": "report_docs_reference_sort_shape",
        "sort_fields": ("source_pack", "checkpoint_range", "ref"),
        "sort_reason": "future read-only sort grammar",
        "is_sort_runtime": False,
        "executes_sort": False,
        "truth_label": ShellStateReadModelTruthBoundary.SORT_DESCRIPTOR_ONLY.value,
        "limitations": (
            "sort descriptor is not sort runtime",
            "descriptor does not sort live data",
        ),
    }
    return ShellReportDocsSortDescriptor(
        **payload,
        descriptor_hash=_hash_payload(payload),
    )


def build_shell_read_model_availability_rollup() -> ShellReadModelAvailabilityRollup:
    payload: dict[str, Any] = {
        "availability_rollup_id": _AVAILABILITY_ID,
        "schema_version": P2_8_B_AVAILABILITY_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "available_read_models": (
            _SECTION_STATUS_ID,
            _STATE_SNAPSHOT_ID,
            _REPORT_INDEX_ID,
            _DOCS_INDEX_ID,
        ),
        "available_index_contracts": (_REPORT_INDEX_ID, _DOCS_INDEX_ID),
        "available_descriptors": (
            "p2_8_b_shell_report_docs_query_descriptor",
            "p2_8_b_shell_report_docs_filter_descriptor",
            "p2_8_b_shell_report_docs_sort_descriptor",
        ),
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "future_pack_refs": (P2_8_B_NEXT_PACK, "P2.8-D", "P2.9", "P2.10", "P2.13"),
        "enforces_permission": False,
        "grants_permission": False,
        "denies_permission": False,
        "truth_label": ShellStateReadModelTruthBoundary.READ_MODEL_AVAILABILITY_ONLY.value,
        "limitations": (
            "availability is capability honesty only",
            "availability rollup does not enforce permissions",
        ),
    }
    availability = ShellReadModelAvailabilityRollup(
        **payload,
        availability_hash=_hash_payload(payload),
    )
    assert_availability_rollup_is_not_permission_enforcement(availability)
    return availability


def build_shell_read_model_no_generation_boundary() -> ShellReadModelNoGenerationBoundary:
    payload: dict[str, Any] = {
        "no_generation_boundary_id": _NO_GENERATION_ID,
        "schema_version": P2_8_B_NO_GENERATION_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "report_generator_created": False,
        "docs_generator_created": False,
        "report_publisher_created": False,
        "docs_publisher_created": False,
        "generated_docs": False,
        "generated_reports": False,
        "boundary_active": True,
        "truth_label": (
            ShellStateReadModelTruthBoundary.NO_REPORT_DOCS_GENERATION_BOUNDARY.value
        ),
        "limitations": (
            "boundary is contract-only",
            "not report/docs generator runtime",
        ),
    }
    boundary = ShellReadModelNoGenerationBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_report_docs_generation(boundary)
    return boundary


def build_shell_read_model_no_runtime_mutation_boundary() -> (
    ShellReadModelNoRuntimeMutationBoundary
):
    payload: dict[str, Any] = {
        "no_runtime_mutation_boundary_id": _NO_RUNTIME_MUTATION_ID,
        "schema_version": P2_8_B_NO_RUNTIME_MUTATION_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "shell_state_mutated": False,
        "runtime_state_mutated": False,
        "session_state_engine_created": False,
        "query_runtime_created": False,
        "filter_runtime_created": False,
        "sort_runtime_created": False,
        "boundary_active": True,
        "truth_label": (
            ShellStateReadModelTruthBoundary.NO_RUNTIME_STATE_MUTATION_BOUNDARY.value
        ),
        "limitations": (
            "boundary is contract-only",
            "not runtime implementation",
        ),
    }
    boundary = ShellReadModelNoRuntimeMutationBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_runtime_state_mutation(boundary)
    return boundary


def build_shell_read_model_no_trace_memory_storage_write_boundary() -> (
    ShellReadModelNoTraceMemoryStorageWriteBoundary
):
    payload: dict[str, Any] = {
        "no_write_boundary_id": _NO_WRITE_ID,
        "schema_version": P2_8_B_NO_WRITE_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "trace_written": False,
        "memory_written": False,
        "storage_written": False,
        "database_written": False,
        "boundary_active": True,
        "truth_label": (
            ShellStateReadModelTruthBoundary.NO_TRACE_MEMORY_STORAGE_WRITE_BOUNDARY.value
        ),
        "limitations": (
            "boundary prevents trace/memory/storage writes",
            "not write layer implementation",
        ),
    }
    boundary = ShellReadModelNoTraceMemoryStorageWriteBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_trace_memory_storage_writes(boundary)
    return boundary


def build_shell_state_read_model_expansion_result(
    foundation_result: P28AShellStateFoundationResult | None = None,
) -> ShellStateReadModelExpansionResult:
    if foundation_result is None:
        foundation_result = build_p2_8_a_shell_state_foundation_result()
    gate = build_shell_state_read_model_gate(foundation_result)
    registry = build_shell_state_read_model_registry(foundation_result)
    inventory = build_shell_state_read_model_inventory()
    section_status = build_shell_section_status_read_model(foundation_result)
    state_snapshot = build_shell_state_snapshot_read_model(foundation_result)
    report_index = build_shell_report_index_read_model(foundation_result)
    docs_index = build_shell_docs_index_read_model(foundation_result)
    query = build_shell_report_docs_query_descriptor()
    filter_descriptor = build_shell_report_docs_filter_descriptor()
    sort = build_shell_report_docs_sort_descriptor()
    availability = build_shell_read_model_availability_rollup()
    no_generation = build_shell_read_model_no_generation_boundary()
    no_runtime = build_shell_read_model_no_runtime_mutation_boundary()
    no_write = build_shell_read_model_no_trace_memory_storage_write_boundary()
    payload: dict[str, Any] = {
        "expansion_result_id": _EXPANSION_RESULT_ID,
        "schema_version": P2_8_B_EXPANSION_RESULT_VERSION,
        "section_id": P2_8_B_SECTION_ID,
        "created_for_pack": P2_8_B_PACK_ID,
        "official_section_name": P2_8_B_OFFICIAL_SECTION_NAME,
        "read_model_gate": gate,
        "read_model_registry": registry,
        "read_model_inventory": inventory,
        "section_status_read_model": section_status,
        "state_snapshot_read_model": state_snapshot,
        "report_index": report_index,
        "docs_index": docs_index,
        "query_descriptors": (query,),
        "filter_descriptors": (filter_descriptor,),
        "sort_descriptors": (sort,),
        "availability_rollup": availability,
        "no_generation_boundary": no_generation,
        "no_runtime_mutation_boundary": no_runtime,
        "no_write_boundary": no_write,
        "creates_query_runtime": False,
        "creates_generator_runtime": False,
        "creates_write_path": False,
        "creates_product_behavior": False,
        "truth_label": ShellStateReadModelTruthBoundary.SHELL_STATE_READ_MODEL_ONLY.value,
        "limitations": (
            "expansion result is contract-only",
            "not query runtime, generator runtime, write path, or product behavior",
        ),
    }
    expansion = ShellStateReadModelExpansionResult(
        **payload,
        expansion_hash=_hash_payload(payload),
    )
    assert_query_filter_sort_descriptors_do_not_execute(query, filter_descriptor, sort)
    assert_expansion_result_is_contract_only(expansion)
    return expansion


def build_p2_8_b_side_effect_proof() -> P28BSideEffectProof:
    return P28BSideEffectProof()


def build_p2_8_b_shell_state_read_model_result() -> P28BShellStateReadModelResult:
    foundation_result = build_p2_8_a_shell_state_foundation_result()
    expansion = build_shell_state_read_model_expansion_result(foundation_result)
    side_effects = build_p2_8_b_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    payload: dict[str, Any] = {
        "schema_version": P2_8_B_RESULT_VERSION,
        "pack_id": P2_8_B_PACK_ID,
        "section_id": P2_8_B_SECTION_ID,
        "official_section_name": P2_8_B_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_8_B_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_8_B_DEPENDENCY_PACK,
        "p2_8_a_evidence_ref": _p2_8_a_evidence_ref(foundation_result),
        "p2_8_a_foundation_result_ref": _foundation_result_ref(foundation_result),
        "p2_8_a_state_snapshot_ref": _state_snapshot_ref(foundation_result),
        "p2_8_a_report_registry_ref": _report_registry_ref(foundation_result),
        "p2_8_a_docs_registry_ref": _docs_registry_ref(foundation_result),
        "read_model_gate": expansion.read_model_gate,
        "read_model_registry": expansion.read_model_registry,
        "read_model_inventory": expansion.read_model_inventory,
        "section_status_read_model": expansion.section_status_read_model,
        "state_snapshot_read_model": expansion.state_snapshot_read_model,
        "report_index": expansion.report_index,
        "report_family_groupings": expansion.report_index.report_family_groupings,
        "docs_index": expansion.docs_index,
        "docs_family_groupings": expansion.docs_index.docs_family_groupings,
        "query_descriptors": expansion.query_descriptors,
        "filter_descriptors": expansion.filter_descriptors,
        "sort_descriptors": expansion.sort_descriptors,
        "availability_rollup": expansion.availability_rollup,
        "no_generation_boundary": expansion.no_generation_boundary,
        "no_runtime_mutation_boundary": expansion.no_runtime_mutation_boundary,
        "no_write_boundary": expansion.no_write_boundary,
        "expansion_result": expansion,
        "truth_labels": tuple(label.value for label in ShellStateReadModelTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_8_B_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P28BShellStateReadModelResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_8_b_does_not_start_future_work(result)
    assert_p2_8_b_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_8_b_result(
    result: P28BShellStateReadModelResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_b_shell_state_read_model_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_state_read_model_summary(
    result: P28BShellStateReadModelResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_b_shell_state_read_model_result()
    expansion = result.expansion_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.read_model_gate.gate_status.value}",
            f"registry_entries={len(result.read_model_registry.registry_entries)}",
            f"report_entries={len(result.report_index.report_index_entries)}",
            f"docs_entries={len(result.docs_index.docs_index_entries)}",
            f"next={result.next_pack}",
            f"query_runtime={str(expansion.creates_query_runtime).lower()}",
            f"generator_runtime={str(expansion.creates_generator_runtime).lower()}",
            f"write_path={str(expansion.creates_write_path).lower()}",
            f"product_behavior={str(expansion.creates_product_behavior).lower()}",
        )
    )
