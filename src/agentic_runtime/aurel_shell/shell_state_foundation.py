"""P2.8-A Shell State / Reports / Docs foundation contracts.

Contract-only Shell state snapshot, report reference registry, docs reference
registry, availability, governance source boundary, and foundation result over
P2.7-D section seal evidence. This module defines foundation gate, identity,
snapshot contract, source references, governance boundary, report/docs registries,
availability contract, no-runtime-mutation boundary, no-trace-memory-storage-write
boundary, foundation result, side-effect proof, and pack result.

Core law:
  - Shell state snapshot is not live Shell state.
  - Shell state scope is not session state engine.
  - Source reference is not storage persistence.
  - Report registry is not agent/REPORTS.md replacement.
  - Docs registry is not docs source-of-truth.
  - Report/docs availability is not permission enforcement.

It does not create live Shell state runtime, Shell runtime, session state engine,
persistent state store, database persistence, storage write, trace write, memory
write, report generator runtime, docs generator runtime, report publisher, docs
publisher, product UI, product behavior, CLI runner, TUI runtime, command
execution, runtime dispatch, permission enforcement, Custos decisioning, approval
runtime, LIVE, TRACE_VERIFIED, release scope, P2.8-B, P2.9, P2.10, or P2.13.
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
from .shell_binding_section_seal import (
    P2_7_D_PACK_ID,
    P2_7_D_REPORT_PATH,
    P2_7_D_VALIDATION_REF,
    P27DSideEffectProof,
    P27DShellBindingSectionSealResult,
    ShellBindingNoLiveBindingProof,
    ShellBindingP28HandoffContract,
    build_p2_7_d_shell_binding_section_seal_result,
)
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES

P2_8_A_PACK_ID = "P2.8-A"
P2_8_A_SECTION_ID = "P2.8"
P2_8_A_OFFICIAL_SECTION_NAME = "Shell State / Reports / Docs"
P2_8_A_DEPENDENCY_PACK = P2_7_D_PACK_ID
P2_8_A_NEXT_PACK = "P2.8-B"
P2_8_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.8.0",
    "P2.8.1",
    "P2.8.2",
    "P2.8.3",
    "P2.8.4",
    "P2.8.5",
)
P2_8_A_REPORT_FILENAME = "P2_8_A_SHELL_STATE_REPORTS_DOCS_FOUNDATION.md"
P2_8_A_REPORT_PATH = f"agent/reports/{P2_8_A_REPORT_FILENAME}"

P2_7_D_COMMIT_REF = "43e7240"

P2_8_A_GATE_VERSION = "p2_8_a_shell_state_foundation_gate.v1"
P2_8_A_IDENTITY_VERSION = "p2_8_a_shell_state_foundation_identity.v1"
P2_8_A_SNAPSHOT_VERSION = "p2_8_a_shell_state_snapshot_contract.v1"
P2_8_A_SOURCE_REF_VERSION = "p2_8_a_shell_state_source_reference.v1"
P2_8_A_GOVERNANCE_BOUNDARY_VERSION = (
    "p2_8_a_shell_state_governance_source_boundary.v1"
)
P2_8_A_REPORT_REGISTRY_VERSION = "p2_8_a_shell_report_reference_registry.v1"
P2_8_A_REPORT_ENTRY_VERSION = "p2_8_a_shell_report_reference_entry.v1"
P2_8_A_DOCS_REGISTRY_VERSION = "p2_8_a_shell_docs_reference_registry.v1"
P2_8_A_DOCS_ENTRY_VERSION = "p2_8_a_shell_docs_reference_entry.v1"
P2_8_A_AVAILABILITY_VERSION = "p2_8_a_shell_report_docs_availability_contract.v1"
P2_8_A_NO_RUNTIME_MUTATION_VERSION = (
    "p2_8_a_shell_state_no_runtime_mutation_boundary.v1"
)
P2_8_A_NO_WRITE_VERSION = (
    "p2_8_a_shell_state_no_trace_memory_storage_write_boundary.v1"
)
P2_8_A_FOUNDATION_RESULT_VERSION = "p2_8_a_shell_state_foundation_result.v1"
P2_8_A_RESULT_VERSION = "p2_8_a_shell_state_foundation_pack_result.v1"

P2_8_A_TEST_REF = "tests/aurel_shell/test_shell_state_foundation.py"
P2_8_A_VALIDATION_REF = "agent/TESTS.md#P2.8-A"
P2_8_A_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_8_A_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_AGENT_REPORTS_INDEX_REF = "agent/REPORTS.md"
_AGENT_GOVERNANCE_SOURCE = "agent/"
_AGENT_STATE_SOURCE = "agent/STATE.md"
_AGENT_ROADMAP_SOURCE = "agent/ROADMAP.md"

_UNAVAILABLE_CAPABILITIES: tuple[str, ...] = (
    "live Shell state runtime",
    "Shell state mutation",
    "session state engine",
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
    "P2.8-B implementation",
    "P2.9 implementation",
    "P2.10 implementation",
    "P2.13 implementation",
)

_REPORT_ENTRY_SPECS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "P2.7-D",
        "SECTION_SEAL",
        P2_7_D_REPORT_PATH,
        "P2.7.16-P2.7.20",
        "Shell / CLI / TUI Binding Section Seal",
    ),
    (
        "P2.7-A",
        "FOUNDATION",
        "agent/reports/P2_7_A_SHELL_CLI_TUI_BINDING_FOUNDATION.md",
        "P2.7.0-P2.7.5",
        "Shell / CLI / TUI Binding Foundation",
    ),
    (
        "P2.6-D",
        "SECTION_SEAL",
        "agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md",
        "P2.6.16-P2.6.20",
        "Surface Projection Section Seal",
    ),
)

_DOCS_ENTRY_SPECS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "AGENT_GOVERNANCE",
        "GOVERNANCE",
        "agent/AGENT.md",
        "agent/",
        "Agent governance entry",
    ),
    (
        "CODEOPS",
        "GOVERNANCE",
        "agent/CODEOPS.md",
        "agent/",
        "CodeOps protocol",
    ),
    (
        "ARCHITECTURE",
        "REFERENCE",
        "agent/ARCHITECTURE.md",
        "agent/",
        "Architecture reference",
    ),
)


class ShellStateFoundationGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellStateSnapshotScope(str, Enum):
    SECTION_SNAPSHOT_ONLY = "SECTION_SNAPSHOT_ONLY"
    REPORT_DOCS_REFERENCE_ONLY = "REPORT_DOCS_REFERENCE_ONLY"
    GOVERNANCE_SOURCE_REFERENCE_ONLY = "GOVERNANCE_SOURCE_REFERENCE_ONLY"
    DEV_FIXTURE_ONLY = "DEV_FIXTURE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ShellReportDocsAvailabilityStatus(str, Enum):
    CONTRACT_AVAILABLE = "CONTRACT_AVAILABLE"
    UNAVAILABLE_RUNTIME_REQUIRED = "UNAVAILABLE_RUNTIME_REQUIRED"
    UNAVAILABLE_P2_8_B_REQUIRED = "UNAVAILABLE_P2_8_B_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellStateFoundationTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    SHELL_STATE_FOUNDATION_ONLY = "SHELL_STATE_FOUNDATION_ONLY"
    SHELL_STATE_SNAPSHOT_ONLY = "SHELL_STATE_SNAPSHOT_ONLY"
    SNAPSHOT_SCOPE_ONLY = "SNAPSHOT_SCOPE_ONLY"
    SOURCE_REFERENCE_ONLY = "SOURCE_REFERENCE_ONLY"
    GOVERNANCE_SOURCE_BOUNDARY_ONLY = "GOVERNANCE_SOURCE_BOUNDARY_ONLY"
    REPORT_REFERENCE_REGISTRY_ONLY = "REPORT_REFERENCE_REGISTRY_ONLY"
    REPORT_REFERENCE_ENTRY_ONLY = "REPORT_REFERENCE_ENTRY_ONLY"
    DOCS_REFERENCE_REGISTRY_ONLY = "DOCS_REFERENCE_REGISTRY_ONLY"
    DOCS_REFERENCE_ENTRY_ONLY = "DOCS_REFERENCE_ENTRY_ONLY"
    REPORT_DOCS_AVAILABILITY_ONLY = "REPORT_DOCS_AVAILABILITY_ONLY"
    NO_RUNTIME_STATE_MUTATION_BOUNDARY = "NO_RUNTIME_STATE_MUTATION_BOUNDARY"
    NO_TRACE_MEMORY_STORAGE_WRITE_BOUNDARY = "NO_TRACE_MEMORY_STORAGE_WRITE_BOUNDARY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
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
    NOT_P2_8_B_IMPLEMENTATION = "NOT_P2_8_B_IMPLEMENTATION"
    NOT_P2_9_IMPLEMENTATION = "NOT_P2_9_IMPLEMENTATION"
    NOT_P2_10_IMPLEMENTATION = "NOT_P2_10_IMPLEMENTATION"
    NOT_P2_13_IMPLEMENTATION = "NOT_P2_13_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"


@dataclass(frozen=True)
class P28ASideEffectProof(_CanonicalMixin):
    shell_runtime_created: bool = False
    shell_state_runtime_created: bool = False
    session_state_engine_created: bool = False
    shell_state_mutated: bool = False
    runtime_state_mutated: bool = False
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
    p2_8_b_started: bool = False
    p2_9_started: bool = False
    p2_10_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class ShellStateFoundationGate(_CanonicalMixin):
    gate_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    dependency_pack: str
    dependency_report_ref: str
    dependency_commit_ref: str
    dependency_validation_ref: str
    dependency_section_seal_result_ref: str
    dependency_p2_8_handoff_ref: str
    dependency_no_live_binding_proof_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellStateFoundationGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellStateFoundationIdentity(_CanonicalMixin):
    identity_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    foundation_version: str
    source_handoff_ref: str
    source_section_seal_ref: str
    active_surface_set: tuple[str, ...]
    is_runtime_identity: bool
    is_product_identity: bool
    truth_label: str
    limitations: tuple[str, ...]
    identity_hash: str


@dataclass(frozen=True)
class ShellStateSourceReference(_CanonicalMixin):
    source_reference_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    source_kind: str
    source_path_or_ref: str
    source_pack: str
    source_report_ref: str
    source_contract_ref: str
    source_validation_ref: str
    is_storage_persistence: bool
    writes_storage: bool
    writes_trace: bool
    writes_memory: bool
    truth_label: str
    limitations: tuple[str, ...]
    source_reference_hash: str


@dataclass(frozen=True)
class ShellReportReferenceEntry(_CanonicalMixin):
    report_entry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    report_kind: str
    report_ref: str
    source_pack: str
    source_checkpoint_range: str
    available_as_reference: bool
    available_as_generated_report: bool
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellReportReferenceRegistry(_CanonicalMixin):
    report_registry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    registry_version: str
    report_entries: tuple[ShellReportReferenceEntry, ...]
    source_reports_index_ref: str
    is_agent_reports_replacement: bool
    generates_reports: bool
    publishes_reports: bool
    writes_reports_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class ShellDocsReferenceEntry(_CanonicalMixin):
    docs_entry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    docs_kind: str
    docs_ref: str
    source_pack: str
    source_checkpoint_range: str
    available_as_reference: bool
    available_as_generated_docs: bool
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellDocsReferenceRegistry(_CanonicalMixin):
    docs_registry_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    registry_version: str
    docs_entries: tuple[ShellDocsReferenceEntry, ...]
    source_docs_refs: tuple[str, ...]
    is_docs_source_of_truth: bool
    generates_docs: bool
    publishes_docs: bool
    writes_docs_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    registry_hash: str


@dataclass(frozen=True)
class ShellReportDocsAvailabilityContract(_CanonicalMixin):
    availability_contract_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    availability_status: ShellReportDocsAvailabilityStatus
    available_report_refs: tuple[str, ...]
    available_docs_refs: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    future_pack_refs: tuple[str, ...]
    enforces_permission: bool
    grants_permission: bool
    denies_permission: bool
    truth_label: str
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class ShellStateGovernanceSourceBoundary(_CanonicalMixin):
    governance_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    agent_governance_source: str
    agent_reports_source: str
    agent_state_source: str
    agent_roadmap_source: str
    replaces_agent_governance: bool
    replaces_agent_reports: bool
    creates_new_governance_source: bool
    creates_docs_source_of_truth: bool
    truth_label: str
    limitations: tuple[str, ...]
    governance_boundary_hash: str


@dataclass(frozen=True)
class ShellStateNoRuntimeMutationBoundary(_CanonicalMixin):
    no_runtime_mutation_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    shell_state_runtime_created: bool
    session_state_engine_created: bool
    runtime_state_mutated: bool
    shell_state_mutated: bool
    persistent_state_store_created: bool
    database_persistence_created: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellStateNoTraceMemoryStorageWriteBoundary(_CanonicalMixin):
    no_write_boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    trace_written: bool
    memory_written: bool
    storage_written: bool
    database_written: bool
    report_written_runtime: bool
    docs_written_runtime: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellStateSnapshotContract(_CanonicalMixin):
    snapshot_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    snapshot_scope: ShellStateSnapshotScope
    source_reference_refs: tuple[str, ...]
    report_registry_ref: str
    docs_registry_ref: str
    availability_ref: str
    is_live_shell_state: bool
    mutates_runtime_state: bool
    mutates_shell_state: bool
    truth_label: str
    limitations: tuple[str, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class ShellStateFoundationResult(_CanonicalMixin):
    foundation_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    foundation_gate: ShellStateFoundationGate
    foundation_identity: ShellStateFoundationIdentity
    snapshot_contract: ShellStateSnapshotContract
    governance_source_boundary: ShellStateGovernanceSourceBoundary
    report_registry: ShellReportReferenceRegistry
    docs_registry: ShellDocsReferenceRegistry
    availability_contract: ShellReportDocsAvailabilityContract
    no_runtime_mutation_boundary: ShellStateNoRuntimeMutationBoundary
    no_write_boundary: ShellStateNoTraceMemoryStorageWriteBoundary
    creates_live_shell_state: bool
    creates_shell_runtime: bool
    creates_persistent_store: bool
    creates_report_generator: bool
    creates_docs_generator: bool
    creates_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    foundation_result_hash: str


@dataclass(frozen=True)
class P28AShellStateFoundationResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_7_d_evidence_ref: str
    p2_7_d_section_seal_ref: str
    p2_7_d_handoff_ref: str
    p2_7_d_no_live_binding_proof_ref: str
    foundation_gate: ShellStateFoundationGate
    foundation_identity: ShellStateFoundationIdentity
    snapshot_contract: ShellStateSnapshotContract
    source_references: tuple[ShellStateSourceReference, ...]
    governance_source_boundary: ShellStateGovernanceSourceBoundary
    report_registry: ShellReportReferenceRegistry
    docs_registry: ShellDocsReferenceRegistry
    availability_contract: ShellReportDocsAvailabilityContract
    no_runtime_mutation_boundary: ShellStateNoRuntimeMutationBoundary
    no_write_boundary: ShellStateNoTraceMemoryStorageWriteBoundary
    foundation_result: ShellStateFoundationResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P28ASideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    starts_future_work: bool
    result_hash: str


def _section_seal_result_ref(
    seal_result: P27DShellBindingSectionSealResult,
) -> str:
    return (
        f"{seal_result.section_seal_result.section_seal_result_id}:"
        f"hash={seal_result.result_hash[:12]}"
    )


def _p2_8_handoff_ref(handoff: ShellBindingP28HandoffContract) -> str:
    return f"{handoff.handoff_contract_id}:hash={handoff.handoff_hash[:12]}"


def _no_live_binding_proof_ref(proof: ShellBindingNoLiveBindingProof) -> str:
    return f"{proof.no_live_binding_proof_id}:hash={proof.proof_hash[:12]}"


def assert_p2_7_d_section_seal_result_available(
    seal_result: P27DShellBindingSectionSealResult,
) -> None:
    if seal_result.pack_id != P2_7_D_PACK_ID or seal_result.starts_future_work:
        _reject(
            "P2.8-A requires P2.7-D section seal result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    handoff = seal_result.p2_8_handoff_contract
    if handoff.starts_p2_8 or handoff.implements_p2_8 or handoff.creates_shell_state_runtime:
        _reject(
            "P2.8-A requires P2.7-D handoff that does not implement P2.8",
            field="p2_8_handoff_contract",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellStateFoundationGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.8-A gate must ignore OMNI evidence by operator instruction",
            field="omni_evidence_ignored_by_operator_instruction",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_shell_state_snapshot_is_not_live_state(
    snapshot: ShellStateSnapshotContract,
) -> None:
    if (
        snapshot.is_live_shell_state
        or snapshot.mutates_runtime_state
        or snapshot.mutates_shell_state
    ):
        _reject(
            "Shell state snapshot must not be live or mutating",
            field="snapshot_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_shell_state_scope_is_not_session_state_engine(
    scope: ShellStateSnapshotScope,
) -> None:
    if scope == ShellStateSnapshotScope.ERROR:
        _reject(
            "Shell state snapshot scope must not be ERROR in foundation",
            field="snapshot_scope",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_source_reference_is_not_storage_persistence(
    source_ref: ShellStateSourceReference,
) -> None:
    if (
        source_ref.is_storage_persistence
        or source_ref.writes_storage
        or source_ref.writes_trace
        or source_ref.writes_memory
    ):
        _reject(
            "Source reference must not persist or write storage/trace/memory",
            field="source_reference_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_report_registry_is_not_agent_reports_replacement(
    registry: ShellReportReferenceRegistry,
) -> None:
    if (
        registry.is_agent_reports_replacement
        or registry.generates_reports
        or registry.publishes_reports
        or registry.writes_reports_runtime
    ):
        _reject(
            "Report registry must remain reference-only",
            field="report_registry_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_docs_registry_is_not_docs_source_of_truth(
    registry: ShellDocsReferenceRegistry,
) -> None:
    if (
        registry.is_docs_source_of_truth
        or registry.generates_docs
        or registry.publishes_docs
        or registry.writes_docs_runtime
    ):
        _reject(
            "Docs registry must remain reference-only",
            field="docs_registry_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_report_docs_availability_is_not_permission_enforcement(
    availability: ShellReportDocsAvailabilityContract,
) -> None:
    if (
        availability.enforces_permission
        or availability.grants_permission
        or availability.denies_permission
    ):
        _reject(
            "Report/docs availability must not enforce permissions",
            field="availability_contract_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_runtime_state_mutation(
    boundary: ShellStateNoRuntimeMutationBoundary,
) -> None:
    if not boundary.boundary_active or any(
        (
            boundary.shell_state_runtime_created,
            boundary.session_state_engine_created,
            boundary.runtime_state_mutated,
            boundary.shell_state_mutated,
            boundary.persistent_state_store_created,
            boundary.database_persistence_created,
        )
    ):
        _reject(
            "No-runtime-mutation boundary must be active with all flags false",
            field="no_runtime_mutation_boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_trace_memory_storage_writes(
    boundary: ShellStateNoTraceMemoryStorageWriteBoundary,
) -> None:
    if not boundary.boundary_active or any(
        (
            boundary.trace_written,
            boundary.memory_written,
            boundary.storage_written,
            boundary.database_written,
            boundary.report_written_runtime,
            boundary.docs_written_runtime,
        )
    ):
        _reject(
            "No-write boundary must be active with all write flags false",
            field="no_write_boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_a_does_not_start_future_work(
    result: P28AShellStateFoundationResult,
) -> None:
    proof = result.side_effect_proof
    if (
        result.starts_future_work
        or result.next_pack != P2_8_A_NEXT_PACK
        or proof.p2_8_b_started
        or proof.p2_9_started
        or proof.p2_10_started
        or proof.p2_13_started
    ):
        _reject(
            "P2.8-A must not start future packs",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_8_a_side_effects_all_false(proof: P28ASideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.8-A side effect {field.name} must remain false",
                field=field.name,
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def build_shell_state_foundation_gate(
    seal_result: P27DShellBindingSectionSealResult | None = None,
) -> ShellStateFoundationGate:
    if seal_result is None:
        seal_result = build_p2_7_d_shell_binding_section_seal_result()
    assert_p2_7_d_section_seal_result_available(seal_result)
    handoff = seal_result.p2_8_handoff_contract
    no_live = seal_result.no_live_binding_proof
    payload: dict[str, Any] = {
        "gate_id": "p2_8_a_shell_state_foundation_gate",
        "schema_version": P2_8_A_GATE_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "official_section_name": P2_8_A_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_8_A_DEPENDENCY_PACK,
        "dependency_report_ref": P2_7_D_REPORT_PATH,
        "dependency_commit_ref": P2_7_D_COMMIT_REF,
        "dependency_validation_ref": P2_7_D_VALIDATION_REF,
        "dependency_section_seal_result_ref": _section_seal_result_ref(seal_result),
        "dependency_p2_8_handoff_ref": _p2_8_handoff_ref(handoff),
        "dependency_no_live_binding_proof_ref": _no_live_binding_proof_ref(no_live),
        "dependency_side_effect_proof_ref": "P27DSideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellStateFoundationGateStatus.READY,
        "truth_label": ShellStateFoundationTruthBoundary.SHELL_STATE_FOUNDATION_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate does not create Shell state runtime",
        ),
    }
    gate = ShellStateFoundationGate(**payload, gate_hash=_hash_payload(payload))
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_shell_state_foundation_identity(
    seal_result: P27DShellBindingSectionSealResult | None = None,
) -> ShellStateFoundationIdentity:
    if seal_result is None:
        seal_result = build_p2_7_d_shell_binding_section_seal_result()
    handoff = seal_result.p2_8_handoff_contract
    payload: dict[str, Any] = {
        "identity_id": "p2_8_a_shell_state_foundation_identity",
        "schema_version": P2_8_A_IDENTITY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "official_section_name": P2_8_A_OFFICIAL_SECTION_NAME,
        "foundation_version": P2_8_A_IDENTITY_VERSION,
        "source_handoff_ref": _p2_8_handoff_ref(handoff),
        "source_section_seal_ref": _section_seal_result_ref(seal_result),
        "active_surface_set": OFFICIAL_ACTIVE_SURFACE_NAMES,
        "is_runtime_identity": False,
        "is_product_identity": False,
        "truth_label": ShellStateFoundationTruthBoundary.SHELL_STATE_FOUNDATION_ONLY.value,
        "limitations": (
            "identity is contract-only",
            "not runtime or product identity",
        ),
    }
    return ShellStateFoundationIdentity(
        **payload,
        identity_hash=_hash_payload(payload),
    )


def build_shell_state_source_reference(
    *,
    source_kind: str = "SECTION_SEAL",
    source_path_or_ref: str = P2_7_D_REPORT_PATH,
    source_pack: str = P2_7_D_PACK_ID,
    source_report_ref: str = P2_7_D_REPORT_PATH,
    source_contract_ref: str = "ShellBindingSectionSealResult",
    source_validation_ref: str = P2_7_D_VALIDATION_REF,
    entry_suffix: str = "p2_7_d",
) -> ShellStateSourceReference:
    payload: dict[str, Any] = {
        "source_reference_id": f"p2_8_a_shell_state_source_reference_{entry_suffix}",
        "schema_version": P2_8_A_SOURCE_REF_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "source_kind": source_kind,
        "source_path_or_ref": source_path_or_ref,
        "source_pack": source_pack,
        "source_report_ref": source_report_ref,
        "source_contract_ref": source_contract_ref,
        "source_validation_ref": source_validation_ref,
        "is_storage_persistence": False,
        "writes_storage": False,
        "writes_trace": False,
        "writes_memory": False,
        "truth_label": ShellStateFoundationTruthBoundary.SOURCE_REFERENCE_ONLY.value,
        "limitations": (
            "source reference is provenance pointer only",
            "does not persist or write storage/trace/memory",
        ),
    }
    source_ref = ShellStateSourceReference(
        **payload,
        source_reference_hash=_hash_payload(payload),
    )
    assert_source_reference_is_not_storage_persistence(source_ref)
    return source_ref


def build_shell_state_source_references() -> tuple[ShellStateSourceReference, ...]:
    return (
        build_shell_state_source_reference(),
        build_shell_state_source_reference(
            source_kind="HANDOFF_CONTRACT",
            source_path_or_ref="ShellBindingP28HandoffContract",
            source_pack=P2_7_D_PACK_ID,
            source_contract_ref="ShellBindingP28HandoffContract",
            entry_suffix="p2_8_handoff",
        ),
        build_shell_state_source_reference(
            source_kind="NO_LIVE_BINDING_PROOF",
            source_path_or_ref="ShellBindingNoLiveBindingProof",
            source_pack=P2_7_D_PACK_ID,
            source_contract_ref="ShellBindingNoLiveBindingProof",
            entry_suffix="no_live_binding",
        ),
    )


def build_shell_report_reference_entry(
    source_pack: str,
    report_kind: str,
    report_ref: str,
    checkpoint_range: str,
    *,
    entry_suffix: str,
) -> ShellReportReferenceEntry:
    payload: dict[str, Any] = {
        "report_entry_id": f"p2_8_a_shell_report_reference_entry_{entry_suffix}",
        "schema_version": P2_8_A_REPORT_ENTRY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "report_kind": report_kind,
        "report_ref": report_ref,
        "source_pack": source_pack,
        "source_checkpoint_range": checkpoint_range,
        "available_as_reference": True,
        "available_as_generated_report": False,
        "truth_label": ShellStateFoundationTruthBoundary.REPORT_REFERENCE_ENTRY_ONLY.value,
        "limitations": (
            "report entry is reference only",
            "not generated report output",
        ),
    }
    return ShellReportReferenceEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_report_reference_registry() -> ShellReportReferenceRegistry:
    entries = tuple(
        build_shell_report_reference_entry(
            source_pack,
            report_kind,
            report_ref,
            checkpoint_range,
            entry_suffix=source_pack.lower().replace(".", "_"),
        )
        for source_pack, report_kind, report_ref, checkpoint_range, _title in _REPORT_ENTRY_SPECS
    )
    payload: dict[str, Any] = {
        "report_registry_id": "p2_8_a_shell_report_reference_registry",
        "schema_version": P2_8_A_REPORT_REGISTRY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "registry_version": P2_8_A_REPORT_REGISTRY_VERSION,
        "report_entries": entries,
        "source_reports_index_ref": _AGENT_REPORTS_INDEX_REF,
        "is_agent_reports_replacement": False,
        "generates_reports": False,
        "publishes_reports": False,
        "writes_reports_runtime": False,
        "truth_label": ShellStateFoundationTruthBoundary.REPORT_REFERENCE_REGISTRY_ONLY.value,
        "limitations": (
            "registry is reference index only",
            "does not replace agent/REPORTS.md",
        ),
    }
    registry = ShellReportReferenceRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_report_registry_is_not_agent_reports_replacement(registry)
    return registry


def build_shell_docs_reference_entry(
    docs_kind: str,
    docs_ref: str,
    source_pack: str,
    checkpoint_range: str,
    *,
    entry_suffix: str,
) -> ShellDocsReferenceEntry:
    payload: dict[str, Any] = {
        "docs_entry_id": f"p2_8_a_shell_docs_reference_entry_{entry_suffix}",
        "schema_version": P2_8_A_DOCS_ENTRY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "docs_kind": docs_kind,
        "docs_ref": docs_ref,
        "source_pack": source_pack,
        "source_checkpoint_range": checkpoint_range,
        "available_as_reference": True,
        "available_as_generated_docs": False,
        "truth_label": ShellStateFoundationTruthBoundary.DOCS_REFERENCE_ENTRY_ONLY.value,
        "limitations": (
            "docs entry is reference only",
            "not generated docs output",
        ),
    }
    return ShellDocsReferenceEntry(**payload, entry_hash=_hash_payload(payload))


def build_shell_docs_reference_registry() -> ShellDocsReferenceRegistry:
    entries = tuple(
        build_shell_docs_reference_entry(
            docs_kind,
            docs_ref,
            source_pack,
            checkpoint_range,
            entry_suffix=entry_suffix.lower(),
        )
        for entry_suffix, docs_kind, docs_ref, source_pack, checkpoint_range in _DOCS_ENTRY_SPECS
    )
    source_docs_refs = tuple(entry.docs_ref for entry in entries)
    payload: dict[str, Any] = {
        "docs_registry_id": "p2_8_a_shell_docs_reference_registry",
        "schema_version": P2_8_A_DOCS_REGISTRY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "registry_version": P2_8_A_DOCS_REGISTRY_VERSION,
        "docs_entries": entries,
        "source_docs_refs": source_docs_refs,
        "is_docs_source_of_truth": False,
        "generates_docs": False,
        "publishes_docs": False,
        "writes_docs_runtime": False,
        "truth_label": ShellStateFoundationTruthBoundary.DOCS_REFERENCE_REGISTRY_ONLY.value,
        "limitations": (
            "registry is reference index only",
            "does not become docs source-of-truth",
        ),
    }
    registry = ShellDocsReferenceRegistry(
        **payload,
        registry_hash=_hash_payload(payload),
    )
    assert_docs_registry_is_not_docs_source_of_truth(registry)
    return registry


def build_shell_report_docs_availability_contract(
    report_registry: ShellReportReferenceRegistry | None = None,
    docs_registry: ShellDocsReferenceRegistry | None = None,
) -> ShellReportDocsAvailabilityContract:
    if report_registry is None:
        report_registry = build_shell_report_reference_registry()
    if docs_registry is None:
        docs_registry = build_shell_docs_reference_registry()
    payload: dict[str, Any] = {
        "availability_contract_id": "p2_8_a_shell_report_docs_availability_contract",
        "schema_version": P2_8_A_AVAILABILITY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "availability_status": ShellReportDocsAvailabilityStatus.CONTRACT_AVAILABLE,
        "available_report_refs": tuple(
            entry.report_ref for entry in report_registry.report_entries
        ),
        "available_docs_refs": docs_registry.source_docs_refs,
        "unavailable_capabilities": _UNAVAILABLE_CAPABILITIES,
        "future_pack_refs": (P2_8_A_NEXT_PACK, "P2.9", "P2.10", "P2.13"),
        "enforces_permission": False,
        "grants_permission": False,
        "denies_permission": False,
        "truth_label": ShellStateFoundationTruthBoundary.REPORT_DOCS_AVAILABILITY_ONLY.value,
        "limitations": (
            "availability is reference availability only",
            "does not enforce permissions",
        ),
    }
    availability = ShellReportDocsAvailabilityContract(
        **payload,
        availability_hash=_hash_payload(payload),
    )
    assert_report_docs_availability_is_not_permission_enforcement(availability)
    return availability


def build_shell_state_governance_source_boundary() -> ShellStateGovernanceSourceBoundary:
    payload: dict[str, Any] = {
        "governance_boundary_id": "p2_8_a_shell_state_governance_source_boundary",
        "schema_version": P2_8_A_GOVERNANCE_BOUNDARY_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "agent_governance_source": _AGENT_GOVERNANCE_SOURCE,
        "agent_reports_source": _AGENT_REPORTS_INDEX_REF,
        "agent_state_source": _AGENT_STATE_SOURCE,
        "agent_roadmap_source": _AGENT_ROADMAP_SOURCE,
        "replaces_agent_governance": False,
        "replaces_agent_reports": False,
        "creates_new_governance_source": False,
        "creates_docs_source_of_truth": False,
        "truth_label": (
            ShellStateFoundationTruthBoundary.GOVERNANCE_SOURCE_BOUNDARY_ONLY.value
        ),
        "limitations": (
            "agent/ remains governance source-of-truth",
            "does not replace agent/REPORTS.md",
        ),
    }
    return ShellStateGovernanceSourceBoundary(
        **payload,
        governance_boundary_hash=_hash_payload(payload),
    )


def build_shell_state_no_runtime_mutation_boundary() -> ShellStateNoRuntimeMutationBoundary:
    payload: dict[str, Any] = {
        "no_runtime_mutation_boundary_id": (
            "p2_8_a_shell_state_no_runtime_mutation_boundary"
        ),
        "schema_version": P2_8_A_NO_RUNTIME_MUTATION_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "shell_state_runtime_created": False,
        "session_state_engine_created": False,
        "runtime_state_mutated": False,
        "shell_state_mutated": False,
        "persistent_state_store_created": False,
        "database_persistence_created": False,
        "boundary_active": True,
        "truth_label": (
            ShellStateFoundationTruthBoundary.NO_RUNTIME_STATE_MUTATION_BOUNDARY.value
        ),
        "limitations": (
            "boundary is contract firewall only",
            "not runtime implementation",
        ),
    }
    boundary = ShellStateNoRuntimeMutationBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_runtime_state_mutation(boundary)
    return boundary


def build_shell_state_no_trace_memory_storage_write_boundary() -> (
    ShellStateNoTraceMemoryStorageWriteBoundary
):
    payload: dict[str, Any] = {
        "no_write_boundary_id": (
            "p2_8_a_shell_state_no_trace_memory_storage_write_boundary"
        ),
        "schema_version": P2_8_A_NO_WRITE_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "trace_written": False,
        "memory_written": False,
        "storage_written": False,
        "database_written": False,
        "report_written_runtime": False,
        "docs_written_runtime": False,
        "boundary_active": True,
        "truth_label": (
            ShellStateFoundationTruthBoundary.NO_TRACE_MEMORY_STORAGE_WRITE_BOUNDARY.value
        ),
        "limitations": (
            "boundary prevents trace/memory/storage writes",
            "not write layer implementation",
        ),
    }
    boundary = ShellStateNoTraceMemoryStorageWriteBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_no_trace_memory_storage_writes(boundary)
    return boundary


def build_shell_state_snapshot_contract(
    source_references: tuple[ShellStateSourceReference, ...] | None = None,
    report_registry: ShellReportReferenceRegistry | None = None,
    docs_registry: ShellDocsReferenceRegistry | None = None,
    availability: ShellReportDocsAvailabilityContract | None = None,
) -> ShellStateSnapshotContract:
    if source_references is None:
        source_references = build_shell_state_source_references()
    if report_registry is None:
        report_registry = build_shell_report_reference_registry()
    if docs_registry is None:
        docs_registry = build_shell_docs_reference_registry()
    if availability is None:
        availability = build_shell_report_docs_availability_contract(
            report_registry,
            docs_registry,
        )
    scope = ShellStateSnapshotScope.SECTION_SNAPSHOT_ONLY
    assert_shell_state_scope_is_not_session_state_engine(scope)
    payload: dict[str, Any] = {
        "snapshot_id": "p2_8_a_shell_state_snapshot_contract",
        "schema_version": P2_8_A_SNAPSHOT_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "snapshot_scope": scope,
        "source_reference_refs": tuple(
            ref.source_reference_id for ref in source_references
        ),
        "report_registry_ref": report_registry.report_registry_id,
        "docs_registry_ref": docs_registry.docs_registry_id,
        "availability_ref": availability.availability_contract_id,
        "is_live_shell_state": False,
        "mutates_runtime_state": False,
        "mutates_shell_state": False,
        "truth_label": ShellStateFoundationTruthBoundary.SHELL_STATE_SNAPSHOT_ONLY.value,
        "limitations": (
            "snapshot is contract-only read projection",
            "not live Shell state or session engine",
        ),
    }
    snapshot = ShellStateSnapshotContract(
        **payload,
        snapshot_hash=_hash_payload(payload),
    )
    assert_shell_state_snapshot_is_not_live_state(snapshot)
    return snapshot


def build_shell_state_foundation_result(
    seal_result: P27DShellBindingSectionSealResult | None = None,
) -> ShellStateFoundationResult:
    if seal_result is None:
        seal_result = build_p2_7_d_shell_binding_section_seal_result()
    gate = build_shell_state_foundation_gate(seal_result)
    identity = build_shell_state_foundation_identity(seal_result)
    source_references = build_shell_state_source_references()
    report_registry = build_shell_report_reference_registry()
    docs_registry = build_shell_docs_reference_registry()
    availability = build_shell_report_docs_availability_contract(
        report_registry,
        docs_registry,
    )
    governance = build_shell_state_governance_source_boundary()
    no_runtime = build_shell_state_no_runtime_mutation_boundary()
    no_write = build_shell_state_no_trace_memory_storage_write_boundary()
    snapshot = build_shell_state_snapshot_contract(
        source_references,
        report_registry,
        docs_registry,
        availability,
    )
    payload: dict[str, Any] = {
        "foundation_result_id": "p2_8_a_shell_state_foundation_result",
        "schema_version": P2_8_A_FOUNDATION_RESULT_VERSION,
        "section_id": P2_8_A_SECTION_ID,
        "created_for_pack": P2_8_A_PACK_ID,
        "official_section_name": P2_8_A_OFFICIAL_SECTION_NAME,
        "foundation_gate": gate,
        "foundation_identity": identity,
        "snapshot_contract": snapshot,
        "governance_source_boundary": governance,
        "report_registry": report_registry,
        "docs_registry": docs_registry,
        "availability_contract": availability,
        "no_runtime_mutation_boundary": no_runtime,
        "no_write_boundary": no_write,
        "creates_live_shell_state": False,
        "creates_shell_runtime": False,
        "creates_persistent_store": False,
        "creates_report_generator": False,
        "creates_docs_generator": False,
        "creates_product_behavior": False,
        "truth_label": ShellStateFoundationTruthBoundary.SHELL_STATE_FOUNDATION_ONLY.value,
        "limitations": (
            "foundation result is contract-only",
            "not product behavior or runtime",
        ),
    }
    return ShellStateFoundationResult(
        **payload,
        foundation_result_hash=_hash_payload(payload),
    )


def build_p2_8_a_side_effect_proof() -> P28ASideEffectProof:
    return P28ASideEffectProof()


def build_p2_8_a_shell_state_foundation_result() -> P28AShellStateFoundationResult:
    seal_result = build_p2_7_d_shell_binding_section_seal_result()
    foundation = build_shell_state_foundation_result(seal_result)
    source_references = build_shell_state_source_references()
    side_effects = build_p2_8_a_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    handoff = seal_result.p2_8_handoff_contract
    no_live = seal_result.no_live_binding_proof
    payload: dict[str, Any] = {
        "schema_version": P2_8_A_RESULT_VERSION,
        "pack_id": P2_8_A_PACK_ID,
        "section_id": P2_8_A_SECTION_ID,
        "official_section_name": P2_8_A_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_8_A_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_8_A_DEPENDENCY_PACK,
        "p2_7_d_evidence_ref": (
            f"{P2_7_D_REPORT_PATH}:{seal_result.result_hash[:12]}"
        ),
        "p2_7_d_section_seal_ref": _section_seal_result_ref(seal_result),
        "p2_7_d_handoff_ref": _p2_8_handoff_ref(handoff),
        "p2_7_d_no_live_binding_proof_ref": _no_live_binding_proof_ref(no_live),
        "foundation_gate": foundation.foundation_gate,
        "foundation_identity": foundation.foundation_identity,
        "snapshot_contract": foundation.snapshot_contract,
        "source_references": source_references,
        "governance_source_boundary": foundation.governance_source_boundary,
        "report_registry": foundation.report_registry,
        "docs_registry": foundation.docs_registry,
        "availability_contract": foundation.availability_contract,
        "no_runtime_mutation_boundary": foundation.no_runtime_mutation_boundary,
        "no_write_boundary": foundation.no_write_boundary,
        "foundation_result": foundation,
        "truth_labels": tuple(label.value for label in ShellStateFoundationTruthBoundary),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_8_A_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "starts_future_work": False,
    }
    result = P28AShellStateFoundationResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_8_a_does_not_start_future_work(result)
    assert_p2_8_a_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_8_a_result(
    result: P28AShellStateFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_a_shell_state_foundation_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_state_foundation_summary(
    result: P28AShellStateFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_8_a_shell_state_foundation_result()
    foundation = result.foundation_result
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.foundation_gate.gate_status.value}",
            f"snapshot_scope={result.snapshot_contract.snapshot_scope.value}",
            f"report_entries={len(result.report_registry.report_entries)}",
            f"docs_entries={len(result.docs_registry.docs_entries)}",
            f"next={result.next_pack}",
            f"live_shell_state={str(foundation.creates_live_shell_state).lower()}",
            f"shell_runtime={str(foundation.creates_shell_runtime).lower()}",
            f"report_generator={str(foundation.creates_report_generator).lower()}",
            f"docs_generator={str(foundation.creates_docs_generator).lower()}",
            f"product_behavior={str(foundation.creates_product_behavior).lower()}",
        )
    )
