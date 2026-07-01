"""P2.9-A Shell Exit Seal foundation contracts.

Contract-only Shell Exit Seal foundation over P2.8-D section seal evidence. This
module defines foundation gate, prior section evidence intake, section inventory
intake, exit criteria catalog, readiness dimensions, unavailable capability
declarations, no-release/no-product/no-live/no-completion boundaries, P2.9-B
handoff contract, foundation result, side-effect proof, and pack result.

Core law:
  - Shell Exit Seal foundation is not Shell Exit Seal completion.
  - Exit criteria catalog is not validation execution.
  - Readiness dimension is not product readiness.
  - P2.9-B handoff is not P2.9-B implementation.

It does not create completed Shell Exit Seal, release seal, product readiness,
live Shell runtime, multi-client runtime, frontend/product UI, operator-testable
product behavior, validation execution, trace verification, permission
enforcement, Custos decisioning, truth-label enforcement, runtime dispatch,
command execution, trace write, memory write, storage write, P2.9-B, P2.9-C,
P2.9-D, P2.10, P2.11, P2.12, P2.13, LIVE, or TRACE_VERIFIED.
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
from .shell_state_section_seal import (
    P2_8_D_PACK_ID,
    P2_8_D_REPORT_PATH,
    P2_8_D_TEST_REF,
    P2_8_D_VALIDATION_REF,
    P28DSideEffectProof,
    P28DShellStateSectionSealResult,
    ShellStateNoGenerationProof,
    ShellStateNoLiveStateProof,
    ShellStateNoSyncRuntimeProof,
    ShellStateNoWriteProof,
    ShellStateP29HandoffContract,
    build_p2_8_d_shell_state_section_seal_result,
    build_shell_state_no_generation_proof,
    build_shell_state_no_live_state_proof,
    build_shell_state_no_sync_runtime_proof,
    build_shell_state_no_write_proof,
    build_shell_state_p2_9_handoff_contract,
)
from .surface_projection_foundation import OFFICIAL_ACTIVE_SURFACE_NAMES

P2_9_A_PACK_ID = "P2.9-A"
P2_9_A_SECTION_ID = "P2.9"
P2_9_A_OFFICIAL_SECTION_NAME = "Shell Exit Seal"
P2_9_A_DEPENDENCY_PACK = P2_8_D_PACK_ID
P2_9_A_NEXT_PACK = "P2.9-B"
P2_9_A_NEXT_SECTION = "P2.9.6–P2.9.10 Shell Exit Seal Readiness / Validation / Evidence Matrix"
P2_9_A_PACK_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.9.0",
    "P2.9.1",
    "P2.9.2",
    "P2.9.3",
    "P2.9.4",
    "P2.9.5",
)
P2_9_A_REPORT_FILENAME = "P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md"
P2_9_A_REPORT_PATH = f"agent/reports/{P2_9_A_REPORT_FILENAME}"

P2_8_D_COMMIT_REF = "da62fb8"

P2_9_A_GATE_VERSION = "p2_9_a_shell_exit_seal_foundation_gate.v1"
P2_9_A_EVIDENCE_ENTRY_VERSION = "p2_9_a_shell_prior_section_evidence_entry.v1"
P2_9_A_EVIDENCE_INTAKE_VERSION = "p2_9_a_shell_prior_section_evidence_intake.v1"
P2_9_A_INVENTORY_ENTRY_VERSION = "p2_9_a_shell_section_inventory_entry.v1"
P2_9_A_INVENTORY_INTAKE_VERSION = "p2_9_a_shell_section_inventory_intake.v1"
P2_9_A_CRITERIA_CATALOG_VERSION = "p2_9_a_shell_exit_criteria_catalog.v1"
P2_9_A_CRITERION_VERSION = "p2_9_a_shell_exit_criterion.v1"
P2_9_A_READINESS_DIMENSION_VERSION = "p2_9_a_shell_exit_readiness_dimension.v1"
P2_9_A_UNAVAILABLE_DECL_VERSION = "p2_9_a_shell_exit_unavailable_capability_declaration.v1"
P2_9_A_UNAVAILABLE_ENTRY_VERSION = "p2_9_a_shell_exit_unavailable_capability_entry.v1"
P2_9_A_NO_RELEASE_VERSION = "p2_9_a_shell_exit_no_release_seal_boundary.v1"
P2_9_A_NO_PRODUCT_VERSION = "p2_9_a_shell_exit_no_product_readiness_boundary.v1"
P2_9_A_NO_LIVE_VERSION = "p2_9_a_shell_exit_no_live_runtime_boundary.v1"
P2_9_A_NO_P2_COMPLETE_VERSION = "p2_9_a_shell_exit_no_p2_complete_boundary.v1"
P2_9_A_NO_SHELL_COMPLETE_VERSION = "p2_9_a_shell_exit_no_shell_complete_boundary.v1"
P2_9_A_P2_9_B_HANDOFF_VERSION = "p2_9_a_shell_exit_p2_9_b_handoff_contract.v1"
P2_9_A_FOUNDATION_RESULT_VERSION = "p2_9_a_shell_exit_seal_foundation_result.v1"
P2_9_A_RESULT_VERSION = "p2_9_a_shell_exit_seal_foundation_pack_result.v1"

P2_9_A_TEST_REF = "tests/aurel_shell/test_shell_exit_seal_foundation.py"
P2_9_A_VALIDATION_REF = "agent/TESTS.md#P2.9-A"
P2_9_A_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    f".venv/bin/python -m pytest {P2_9_A_TEST_REF} -q",
    ".venv/bin/python -m pytest tests/aurel_shell -q",
    ".venv/bin/python -m ruff check src tests",
    ".venv/bin/python -m mypy src/agentic_runtime",
)

_EXIT_CRITERIA_CATEGORIES: tuple[str, ...] = (
    "evidence",
    "coverage",
    "validation",
    "boundaries",
    "availability",
    "unavailable_capabilities",
    "handoff_readiness",
    "no_overclaim",
)

_UNAVAILABLE_CAPABILITY_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("completed_shell_exit_seal", "completed Shell Exit Seal", "P2.9-B", "exit seal overclaim"),
    ("release_seal", "release seal", "P2.9-D", "release scope overclaim"),
    ("product_readiness", "product readiness", "P2.9-D", "product readiness overclaim"),
    ("p2_completion", "P2 completion", "P2.13", "P2 complete overclaim"),
    ("shell_completion", "Shell completion", "P2.9-D", "Shell complete overclaim"),
    ("live_shell_runtime", "live Shell runtime", "P2.10", "LIVE overclaim"),
    ("multi_client_runtime", "multi-client runtime", "P2.10", "multi-client overclaim"),
    ("frontend_product_ui", "frontend/product UI", "P2.10", "product UI overclaim"),
    (
        "operator_testable_product_behavior",
        "operator-testable product behavior",
        "P2.13",
        "product behavior overclaim",
    ),
    (
        "shell_exit_validation_execution",
        "Shell exit validation execution",
        "P2.9-B",
        "validation execution overclaim",
    ),
    ("final_evidence_validation", "final evidence validation", "P2.9-B", "TRACE_VERIFIED overclaim"),
    ("trace_verification", "trace verification", "P2.9-B", "TRACE_VERIFIED overclaim"),
    ("permission_enforcement", "permission enforcement", "P2.11", "permission overclaim"),
    ("custos_decisioning", "Custos decisioning", "P2.11", "Custos overclaim"),
    ("truth_label_enforcement", "truth-label enforcement", "P2.12", "truth-label overclaim"),
    ("runtime_dispatch", "runtime dispatch", "P2.10", "runtime dispatch overclaim"),
    ("command_execution", "command execution", "P2.10", "command execution overclaim"),
    ("p2_9_b_implementation", "P2.9-B implementation", "P2.9-B", "future pack overclaim"),
    ("p2_9_c_implementation", "P2.9-C implementation", "P2.9-C", "future pack overclaim"),
    ("p2_9_d_implementation", "P2.9-D implementation", "P2.9-D", "future pack overclaim"),
    ("p2_10_implementation", "P2.10 implementation", "P2.10", "future pack overclaim"),
    ("p2_11_implementation", "P2.11 implementation", "P2.11", "future pack overclaim"),
    ("p2_12_implementation", "P2.12 implementation", "P2.12", "future pack overclaim"),
    ("p2_13_implementation", "P2.13 implementation", "P2.13", "future pack overclaim"),
)

_PRIOR_SECTION_EVIDENCE_SPECS: tuple[tuple[str, str, str, str, str, str, str], ...] = (
    (
        "P2.0",
        "AurelShell Seven-Surface Cognitive OS Foundation",
        "P2.0-F",
        "agent/reports/P2_0_F_PROJECTION_CLI_EXIT_SEAL.md",
        "4565798",
        "tests/aurel_shell/test_shell_projection_cli_exit_seal.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.1",
        "Global Topbar / Surface Registry",
        "P2.1-D",
        "agent/reports/P2_1_D_TOPBAR_INTEGRATION_TAIL.md",
        "e279590",
        "tests/aurel_shell/test_topbar_integration_tail.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.2",
        "Per-Surface Local Navigation",
        "P2.2-D",
        "agent/reports/P2_2_D_LOCAL_NAVIGATION_INTEGRATION_TAIL.md",
        "196c3ba",
        "tests/aurel_shell/test_local_navigation_integration_tail.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.3",
        "Floating Windows / Workspace State",
        "P2.3-D",
        "agent/reports/P2_3_D_WORKSPACE_WINDOW_SECTION_SEAL.md",
        "790f930",
        "tests/aurel_shell/test_workspace_window_section_projection.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.4",
        "Command Palette / Global Commands",
        "P2.4-D",
        "agent/reports/P2_4_D_COMMAND_PALETTE_SECTION_SEAL.md",
        "04060b9",
        "tests/aurel_shell/test_global_command_section_projection.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.5",
        "Cross-Surface Handoff",
        "P2.5-D",
        "agent/reports/P2_5_D_HANDOFF_SECTION_SEAL.md",
        "e279590",
        "tests/aurel_shell/test_cross_surface_handoff_section_projection.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.6",
        "Surface Projection / API / Event Bridge",
        "P2.6-D",
        "agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md",
        "9c74a57",
        "tests/aurel_shell/test_surface_projection_section_seal.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.7",
        "Shell / CLI / TUI Binding",
        "P2.7-D",
        "agent/reports/P2_7_D_SHELL_CLI_TUI_BINDING_SECTION_SEAL.md",
        "43e7240",
        "tests/aurel_shell/test_shell_binding_section_seal.py",
        "SEALED_CONTRACT_ONLY",
    ),
    (
        "P2.8",
        "Shell State / Reports / Docs",
        "P2.8-D",
        P2_8_D_REPORT_PATH,
        P2_8_D_COMMIT_REF,
        P2_8_D_TEST_REF,
        "SEALED_CONTRACT_ONLY",
    ),
)

_READINESS_DIMENSION_SPECS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("evidence_readiness", "Prior section evidence intake completeness", ("evidence",)),
    ("coverage_readiness", "P2.0–P2.8 section inventory coverage", ("coverage",)),
    ("validation_readiness", "Exit validation matrix readiness", ("validation",)),
    ("boundary_readiness", "No-release/no-product/no-live boundaries", ("boundaries",)),
    ("availability_readiness", "Honest unavailable capability declarations", ("availability",)),
    (
        "handoff_readiness",
        "P2.9-B handoff contract readiness",
        ("handoff_readiness",),
    ),
)

_P2_9_B_HANDOFF_REASON = (
    "P2.9-A can hand off foundation contracts to P2.9-B, but it does not start "
    "P2.9-B or execute Shell Exit Seal validation."
)


class ShellExitSealFoundationGateStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


class ShellExitReadinessDimensionStatus(str, Enum):
    DEFINED_CONTRACT_ONLY = "DEFINED_CONTRACT_ONLY"
    UNAVAILABLE_VALIDATION_REQUIRED = "UNAVAILABLE_VALIDATION_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellExitP29BHandoffStatus(str, Enum):
    READY_FOR_P2_9_B_CONTRACT_HANDOFF = "READY_FOR_P2_9_B_CONTRACT_HANDOFF"
    UNAVAILABLE_P2_9_B_REQUIRED = "UNAVAILABLE_P2_9_B_REQUIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ShellExitSealFoundationTruthBoundary(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    EXIT_SEAL_FOUNDATION_ONLY = "EXIT_SEAL_FOUNDATION_ONLY"
    PRIOR_SECTION_EVIDENCE_INTAKE_ONLY = "PRIOR_SECTION_EVIDENCE_INTAKE_ONLY"
    SECTION_INVENTORY_INTAKE_ONLY = "SECTION_INVENTORY_INTAKE_ONLY"
    EXIT_CRITERIA_CATALOG_ONLY = "EXIT_CRITERIA_CATALOG_ONLY"
    EXIT_CRITERION_ONLY = "EXIT_CRITERION_ONLY"
    READINESS_DIMENSION_ONLY = "READINESS_DIMENSION_ONLY"
    UNAVAILABLE_CAPABILITY_DECLARATION_ONLY = "UNAVAILABLE_CAPABILITY_DECLARATION_ONLY"
    NO_RELEASE_SEAL_BOUNDARY = "NO_RELEASE_SEAL_BOUNDARY"
    NO_PRODUCT_READINESS_BOUNDARY = "NO_PRODUCT_READINESS_BOUNDARY"
    NO_LIVE_RUNTIME_BOUNDARY = "NO_LIVE_RUNTIME_BOUNDARY"
    NO_P2_COMPLETE_BOUNDARY = "NO_P2_COMPLETE_BOUNDARY"
    NO_SHELL_COMPLETE_BOUNDARY = "NO_SHELL_COMPLETE_BOUNDARY"
    P2_9_B_HANDOFF_CONTRACT_ONLY = "P2_9_B_HANDOFF_CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    REPORT_ONLY = "REPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_EXIT_SEAL_COMPLETE = "NOT_EXIT_SEAL_COMPLETE"
    NOT_RELEASE_SEAL = "NOT_RELEASE_SEAL"
    NOT_PRODUCT_READY = "NOT_PRODUCT_READY"
    NOT_P2_COMPLETE = "NOT_P2_COMPLETE"
    NOT_SHELL_COMPLETE = "NOT_SHELL_COMPLETE"
    NOT_LIVE_SHELL_RUNTIME = "NOT_LIVE_SHELL_RUNTIME"
    NOT_MULTI_CLIENT_RUNTIME = "NOT_MULTI_CLIENT_RUNTIME"
    NOT_FRONTEND_UI = "NOT_FRONTEND_UI"
    NOT_OPERATOR_TESTABLE_PRODUCT_BEHAVIOR = "NOT_OPERATOR_TESTABLE_PRODUCT_BEHAVIOR"
    NOT_TRACE_VERIFIED = "NOT_TRACE_VERIFIED"
    NOT_VALIDATION_EXECUTION = "NOT_VALIDATION_EXECUTION"
    NOT_PERMISSION_ENFORCEMENT = "NOT_PERMISSION_ENFORCEMENT"
    NOT_CUSTOS_DECISION = "NOT_CUSTOS_DECISION"
    NOT_TRUTH_LABEL_ENFORCEMENT = "NOT_TRUTH_LABEL_ENFORCEMENT"
    NOT_RUNTIME_DISPATCH = "NOT_RUNTIME_DISPATCH"
    NOT_COMMAND_EXECUTION = "NOT_COMMAND_EXECUTION"
    NOT_P2_9_B_IMPLEMENTATION = "NOT_P2_9_B_IMPLEMENTATION"
    NOT_P2_9_C_IMPLEMENTATION = "NOT_P2_9_C_IMPLEMENTATION"
    NOT_P2_9_D_IMPLEMENTATION = "NOT_P2_9_D_IMPLEMENTATION"
    NOT_P2_10_IMPLEMENTATION = "NOT_P2_10_IMPLEMENTATION"
    NOT_P2_11_IMPLEMENTATION = "NOT_P2_11_IMPLEMENTATION"
    NOT_P2_12_IMPLEMENTATION = "NOT_P2_12_IMPLEMENTATION"
    NOT_P2_13_IMPLEMENTATION = "NOT_P2_13_IMPLEMENTATION"
    NOT_LIVE = "NOT_LIVE"
    NOT_RELEASE_SCOPE = "NOT_RELEASE_SCOPE"
    NOT_PRODUCT_BEHAVIOR = "NOT_PRODUCT_BEHAVIOR"


@dataclass(frozen=True)
class ShellExitSealFoundationGate(_CanonicalMixin):
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
    dependency_p2_9_handoff_ref: str
    dependency_no_live_state_proof_ref: str
    dependency_no_sync_runtime_proof_ref: str
    dependency_no_generation_proof_ref: str
    dependency_no_write_proof_ref: str
    dependency_side_effect_proof_ref: str
    repo_evidence_gate_passed: bool
    omni_evidence_required: bool
    omni_evidence_ignored_by_operator_instruction: bool
    gate_status: ShellExitSealFoundationGateStatus
    truth_label: str
    limitations: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellPriorSectionEvidenceEntry(_CanonicalMixin):
    evidence_entry_id: str
    schema_version: str
    source_section_id: str
    source_section_name: str
    source_pack_or_seal: str
    source_report_ref: str
    source_commit_ref: str
    source_validation_ref: str
    source_status: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellPriorSectionEvidenceIntake(_CanonicalMixin):
    evidence_intake_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    source_sections: tuple[str, ...]
    evidence_entries: tuple[ShellPriorSectionEvidenceEntry, ...]
    source_report_refs: tuple[str, ...]
    source_commit_refs: tuple[str, ...]
    claims_trace_verified: bool
    replaces_agent_governance: bool
    duplicates_source_of_truth: bool
    truth_label: str
    limitations: tuple[str, ...]
    intake_hash: str


@dataclass(frozen=True)
class ShellSectionInventoryEntry(_CanonicalMixin):
    inventory_entry_id: str
    schema_version: str
    source_section_id: str
    source_section_name: str
    source_checkpoint_range: str
    source_seal_or_latest_pack: str
    source_report_ref: str
    source_status: str
    source_truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellSectionInventoryIntake(_CanonicalMixin):
    inventory_intake_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    inventory_entries: tuple[ShellSectionInventoryEntry, ...]
    source_sections: tuple[str, ...]
    is_governance_source: bool
    duplicates_agent_state: bool
    truth_label: str
    limitations: tuple[str, ...]
    intake_hash: str


@dataclass(frozen=True)
class ShellExitCriterion(_CanonicalMixin):
    criterion_id: str
    schema_version: str
    category: str
    name: str
    description: str
    required_evidence_ref: str
    status: str
    requires_future_pack: bool
    is_validation_execution: bool
    truth_label: str
    limitations: tuple[str, ...]
    criterion_hash: str


@dataclass(frozen=True)
class ShellExitCriteriaCatalog(_CanonicalMixin):
    criteria_catalog_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    criteria: tuple[ShellExitCriterion, ...]
    criteria_categories: tuple[str, ...]
    is_validation_execution: bool
    decides_authority: bool
    truth_label: str
    limitations: tuple[str, ...]
    catalog_hash: str


@dataclass(frozen=True)
class ShellExitReadinessDimension(_CanonicalMixin):
    readiness_dimension_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    dimension_name: str
    dimension_status: ShellExitReadinessDimensionStatus
    dimension_scope: str
    source_criteria_refs: tuple[str, ...]
    requires_validation_execution: bool
    claims_product_readiness: bool
    truth_label: str
    limitations: tuple[str, ...]
    dimension_hash: str


@dataclass(frozen=True)
class ShellExitUnavailableCapabilityEntry(_CanonicalMixin):
    capability_id: str
    schema_version: str
    capability_name: str
    unavailable_reason: str
    required_future_pack: str
    risk_if_overclaimed: str
    truth_label: str
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellExitUnavailableCapabilityDeclaration(_CanonicalMixin):
    unavailable_declaration_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    unavailable_entries: tuple[ShellExitUnavailableCapabilityEntry, ...]
    future_pack_refs: tuple[str, ...]
    implements_runtime: bool
    truth_label: str
    limitations: tuple[str, ...]
    declaration_hash: str


@dataclass(frozen=True)
class ShellExitNoReleaseSealBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    release_seal_created: bool
    release_readiness_claimed: bool
    release_scope_claimed: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellExitNoProductReadinessBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    product_readiness_claimed: bool
    product_behavior_claimed: bool
    operator_testable_product_behavior_claimed: bool
    frontend_ui_created: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellExitNoLiveRuntimeBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    live_shell_runtime_created: bool
    multi_client_runtime_created: bool
    runtime_dispatch_created: bool
    command_execution_created: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellExitNoP2CompleteBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    p2_complete_claimed: bool
    p2_release_claimed: bool
    p2_done_claimed: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellExitNoShellCompleteBoundary(_CanonicalMixin):
    boundary_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    shell_complete_claimed: bool
    shell_release_claimed: bool
    shell_done_claimed: bool
    boundary_active: bool
    truth_label: str
    limitations: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class ShellExitP29BHandoffContract(_CanonicalMixin):
    handoff_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    handoff_to_pack: str
    handoff_to_section: str
    handoff_status: ShellExitP29BHandoffStatus
    handoff_reason: str
    available_inputs: tuple[str, ...]
    required_next_work: tuple[str, ...]
    is_p2_9_b_implementation: bool
    starts_p2_9_b: bool
    truth_label: str
    limitations: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class ShellExitSealFoundationResult(_CanonicalMixin):
    foundation_result_id: str
    schema_version: str
    section_id: str
    created_for_pack: str
    official_section_name: str
    foundation_gate: ShellExitSealFoundationGate
    prior_section_evidence_intake: ShellPriorSectionEvidenceIntake
    section_inventory_intake: ShellSectionInventoryIntake
    exit_criteria_catalog: ShellExitCriteriaCatalog
    readiness_dimensions: tuple[ShellExitReadinessDimension, ...]
    unavailable_capability_declaration: ShellExitUnavailableCapabilityDeclaration
    no_release_seal_boundary: ShellExitNoReleaseSealBoundary
    no_product_readiness_boundary: ShellExitNoProductReadinessBoundary
    no_live_runtime_boundary: ShellExitNoLiveRuntimeBoundary
    no_p2_complete_boundary: ShellExitNoP2CompleteBoundary
    no_shell_complete_boundary: ShellExitNoShellCompleteBoundary
    p2_9_b_handoff_contract: ShellExitP29BHandoffContract
    is_completed_exit_seal: bool
    is_release_seal: bool
    claims_p2_complete: bool
    claims_shell_complete: bool
    claims_product_readiness: bool
    claims_live: bool
    claims_trace_verified: bool
    claims_product_behavior: bool
    truth_label: str
    limitations: tuple[str, ...]
    foundation_result_hash: str


@dataclass(frozen=True)
class P29ASideEffectProof(_CanonicalMixin):
    shell_exit_seal_completed: bool = False
    release_seal_created: bool = False
    product_readiness_claimed: bool = False
    p2_complete_claimed: bool = False
    shell_complete_claimed: bool = False
    live_shell_runtime_created: bool = False
    multi_client_runtime_created: bool = False
    frontend_ui_created: bool = False
    operator_testable_product_behavior_claimed: bool = False
    validation_execution_created: bool = False
    trace_verified_claimed: bool = False
    permission_enforcement_created: bool = False
    custos_decisioning_created: bool = False
    truth_label_enforcement_created: bool = False
    runtime_dispatch_created: bool = False
    command_execution_created: bool = False
    trace_written: bool = False
    memory_written: bool = False
    storage_written: bool = False
    agent_reports_replaced: bool = False
    agent_governance_replaced: bool = False
    live_claimed: bool = False
    release_scope_claimed: bool = False
    product_behavior_claimed: bool = False
    p2_9_b_started: bool = False
    p2_9_c_started: bool = False
    p2_9_d_started: bool = False
    p2_10_started: bool = False
    p2_11_started: bool = False
    p2_12_started: bool = False
    p2_13_started: bool = False


@dataclass(frozen=True)
class P29AShellExitSealFoundationResult(_CanonicalMixin):
    schema_version: str
    pack_id: str
    section_id: str
    official_section_name: str
    covered_checkpoints: tuple[str, ...]
    dependency_pack: str
    p2_8_d_evidence_ref: str
    p2_8_d_section_seal_result_ref: str
    p2_8_d_p2_9_handoff_ref: str
    foundation_gate: ShellExitSealFoundationGate
    prior_section_evidence_intake: ShellPriorSectionEvidenceIntake
    section_inventory_intake: ShellSectionInventoryIntake
    exit_criteria_catalog: ShellExitCriteriaCatalog
    readiness_dimensions: tuple[ShellExitReadinessDimension, ...]
    unavailable_capability_declaration: ShellExitUnavailableCapabilityDeclaration
    no_release_seal_boundary: ShellExitNoReleaseSealBoundary
    no_product_readiness_boundary: ShellExitNoProductReadinessBoundary
    no_live_runtime_boundary: ShellExitNoLiveRuntimeBoundary
    no_p2_complete_boundary: ShellExitNoP2CompleteBoundary
    no_shell_complete_boundary: ShellExitNoShellCompleteBoundary
    p2_9_b_handoff_contract: ShellExitP29BHandoffContract
    foundation_result: ShellExitSealFoundationResult
    truth_labels: tuple[str, ...]
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    side_effect_proof: P29ASideEffectProof
    next_pack: str
    claims_live: bool
    claims_trace_verified: bool
    claims_release_scope: bool
    claims_product_behavior: bool
    claims_product_readiness: bool
    claims_p2_complete: bool
    claims_shell_complete: bool
    starts_future_work: bool
    result_hash: str


def _section_seal_result_ref(seal_result: P28DShellStateSectionSealResult) -> str:
    seal = seal_result.section_seal_result
    return f"{seal.section_seal_result_id}:hash={seal_result.result_hash[:12]}"


def _p2_8_d_p2_9_handoff_ref(handoff: ShellStateP29HandoffContract) -> str:
    return f"{handoff.handoff_id}:hash={handoff.handoff_hash[:12]}"


def _no_live_state_proof_ref(proof: ShellStateNoLiveStateProof) -> str:
    return f"{proof.no_live_state_proof_id}:hash={proof.proof_hash[:12]}"


def _no_sync_runtime_proof_ref(proof: ShellStateNoSyncRuntimeProof) -> str:
    return f"{proof.no_sync_runtime_proof_id}:hash={proof.proof_hash[:12]}"


def _no_generation_proof_ref(proof: ShellStateNoGenerationProof) -> str:
    return f"{proof.no_generation_proof_id}:hash={proof.proof_hash[:12]}"


def _no_write_proof_ref(proof: ShellStateNoWriteProof) -> str:
    return f"{proof.no_write_proof_id}:hash={proof.proof_hash[:12]}"


def assert_p2_8_d_section_seal_result_available(
    seal_result: P28DShellStateSectionSealResult,
) -> None:
    if seal_result.pack_id != P2_8_D_PACK_ID or seal_result.starts_future_work:
        _reject(
            "P2.9-A requires P2.8-D section seal result without future work",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    handoff = seal_result.p2_9_handoff_contract
    if handoff.starts_p2_9 or handoff.is_p2_9_implementation:
        _reject(
            "P2.9-A requires P2.8-D handoff that does not implement P2.9",
            field="p2_9_handoff_contract",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_omni_evidence_is_ignored_by_operator_instruction(
    gate: ShellExitSealFoundationGate,
) -> None:
    if gate.omni_evidence_required or not gate.omni_evidence_ignored_by_operator_instruction:
        _reject(
            "P2.9-A gate must ignore OMNI evidence by operator instruction",
            field="omni_evidence_ignored_by_operator_instruction",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_foundation_is_not_final_exit_seal(
    foundation: ShellExitSealFoundationResult,
) -> None:
    if (
        foundation.is_completed_exit_seal
        or foundation.is_release_seal
        or foundation.claims_p2_complete
        or foundation.claims_shell_complete
    ):
        _reject(
            "Foundation result must not claim completed exit seal or completion",
            field="foundation_result_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_shell_exit_seal_is_not_release_seal(
    boundary: ShellExitNoReleaseSealBoundary,
) -> None:
    if (
        boundary.release_seal_created
        or boundary.release_readiness_claimed
        or boundary.release_scope_claimed
        or not boundary.boundary_active
    ):
        _reject(
            "No-release-seal boundary must remain active with all claims false",
            field="boundary_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_evidence_intake_is_not_trace_verified(
    intake: ShellPriorSectionEvidenceIntake,
) -> None:
    if (
        intake.claims_trace_verified
        or intake.replaces_agent_governance
        or intake.duplicates_source_of_truth
    ):
        _reject(
            "Prior section evidence intake must not claim TRACE_VERIFIED or replace governance",
            field="evidence_intake_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_criteria_catalog_does_not_execute_validation(
    catalog: ShellExitCriteriaCatalog,
) -> None:
    if catalog.is_validation_execution or catalog.decides_authority:
        _reject(
            "Exit criteria catalog must not execute validation or decide authority",
            field="criteria_catalog_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if any(criterion.is_validation_execution for criterion in catalog.criteria):
        _reject(
            "Exit criteria must not be validation execution",
            field="criteria",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_readiness_dimension_is_not_product_readiness(
    dimension: ShellExitReadinessDimension,
) -> None:
    if dimension.claims_product_readiness:
        _reject(
            "Readiness dimension must not claim product readiness",
            field="readiness_dimension_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_9_a_does_not_start_future_work(
    result: P29AShellExitSealFoundationResult,
) -> None:
    proof = result.side_effect_proof
    if result.starts_future_work or any(
        (
            proof.p2_9_b_started,
            proof.p2_9_c_started,
            proof.p2_9_d_started,
            proof.p2_10_started,
            proof.p2_11_started,
            proof.p2_12_started,
            proof.p2_13_started,
        )
    ):
        _reject(
            "P2.9-A must not start future packs",
            field="pack_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_9_a_side_effects_all_false(proof: P29ASideEffectProof) -> None:
    for field in fields(proof):
        if getattr(proof, field.name):
            _reject(
                f"P2.9-A side effect {field.name} must be false",
                field=field.name,
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_p2_9_b_handoff_is_not_p2_9_b_implementation(
    handoff: ShellExitP29BHandoffContract,
) -> None:
    if handoff.is_p2_9_b_implementation or handoff.starts_p2_9_b:
        _reject(
            "P2.9-B handoff must not start or implement P2.9-B",
            field="handoff_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def build_shell_exit_seal_foundation_gate(
    seal_result: P28DShellStateSectionSealResult | None = None,
) -> ShellExitSealFoundationGate:
    if seal_result is None:
        seal_result = build_p2_8_d_shell_state_section_seal_result()
    assert_p2_8_d_section_seal_result_available(seal_result)
    no_live = seal_result.no_live_state_proof
    no_sync = seal_result.no_sync_runtime_proof
    no_gen = seal_result.no_generation_proof
    no_write = seal_result.no_write_proof
    handoff = seal_result.p2_9_handoff_contract
    payload: dict[str, Any] = {
        "gate_id": "p2_9_a_shell_exit_seal_foundation_gate",
        "schema_version": P2_9_A_GATE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "official_section_name": P2_9_A_OFFICIAL_SECTION_NAME,
        "dependency_pack": P2_9_A_DEPENDENCY_PACK,
        "dependency_report_ref": P2_8_D_REPORT_PATH,
        "dependency_commit_ref": P2_8_D_COMMIT_REF,
        "dependency_validation_ref": P2_8_D_VALIDATION_REF,
        "dependency_section_seal_result_ref": _section_seal_result_ref(seal_result),
        "dependency_p2_9_handoff_ref": _p2_8_d_p2_9_handoff_ref(handoff),
        "dependency_no_live_state_proof_ref": _no_live_state_proof_ref(no_live),
        "dependency_no_sync_runtime_proof_ref": _no_sync_runtime_proof_ref(no_sync),
        "dependency_no_generation_proof_ref": _no_generation_proof_ref(no_gen),
        "dependency_no_write_proof_ref": _no_write_proof_ref(no_write),
        "dependency_side_effect_proof_ref": "P28DSideEffectProof:all_false",
        "repo_evidence_gate_passed": True,
        "omni_evidence_required": False,
        "omni_evidence_ignored_by_operator_instruction": True,
        "gate_status": ShellExitSealFoundationGateStatus.READY,
        "truth_label": ShellExitSealFoundationTruthBoundary.EXIT_SEAL_FOUNDATION_ONLY.value,
        "limitations": (
            "OMNI evidence ignored only by explicit operator instruction",
            "repo evidence gate remains required",
            "gate creates no completed Shell Exit Seal or release seal",
        ),
    }
    gate = ShellExitSealFoundationGate(**payload, gate_hash=_hash_payload(payload))
    assert_omni_evidence_is_ignored_by_operator_instruction(gate)
    return gate


def build_shell_prior_section_evidence_entry(
    source_section_id: str,
    source_section_name: str,
    source_pack_or_seal: str,
    source_report_ref: str,
    source_commit_ref: str,
    source_validation_ref: str,
    source_status: str,
) -> ShellPriorSectionEvidenceEntry:
    suffix = source_section_id.replace(".", "_").lower()
    payload: dict[str, Any] = {
        "evidence_entry_id": f"p2_9_a_prior_section_evidence_entry_{suffix}",
        "schema_version": P2_9_A_EVIDENCE_ENTRY_VERSION,
        "source_section_id": source_section_id,
        "source_section_name": source_section_name,
        "source_pack_or_seal": source_pack_or_seal,
        "source_report_ref": source_report_ref,
        "source_commit_ref": source_commit_ref,
        "source_validation_ref": source_validation_ref,
        "source_status": source_status,
        "truth_label": ShellExitSealFoundationTruthBoundary.REPORT_ONLY.value,
        "limitations": (
            "entry references evidence only",
            "entry does not become truth authority",
        ),
    }
    return ShellPriorSectionEvidenceEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_shell_prior_section_evidence_intake() -> ShellPriorSectionEvidenceIntake:
    entries = tuple(
        build_shell_prior_section_evidence_entry(
            source_section_id,
            source_section_name,
            source_pack_or_seal,
            source_report_ref,
            source_commit_ref,
            f"agent/TESTS.md#{source_pack_or_seal}",
            source_status,
        )
        for (
            source_section_id,
            source_section_name,
            source_pack_or_seal,
            source_report_ref,
            source_commit_ref,
            _test_ref,
            source_status,
        ) in _PRIOR_SECTION_EVIDENCE_SPECS
    )
    payload: dict[str, Any] = {
        "evidence_intake_id": "p2_9_a_shell_prior_section_evidence_intake",
        "schema_version": P2_9_A_EVIDENCE_INTAKE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "official_section_name": P2_9_A_OFFICIAL_SECTION_NAME,
        "source_sections": tuple(spec[0] for spec in _PRIOR_SECTION_EVIDENCE_SPECS),
        "evidence_entries": entries,
        "source_report_refs": tuple(entry.source_report_ref for entry in entries),
        "source_commit_refs": tuple(entry.source_commit_ref for entry in entries),
        "claims_trace_verified": False,
        "replaces_agent_governance": False,
        "duplicates_source_of_truth": False,
        "truth_label": (
            ShellExitSealFoundationTruthBoundary.PRIOR_SECTION_EVIDENCE_INTAKE_ONLY.value
        ),
        "limitations": (
            "intake references P2.0–P2.8 evidence by ref only",
            "does not claim TRACE_VERIFIED or replace agent governance",
        ),
    }
    intake = ShellPriorSectionEvidenceIntake(
        **payload,
        intake_hash=_hash_payload(payload),
    )
    assert_evidence_intake_is_not_trace_verified(intake)
    return intake


def build_shell_section_inventory_entry(
    source_section_id: str,
    source_section_name: str,
    source_checkpoint_range: str,
    source_seal_or_latest_pack: str,
    source_report_ref: str,
    source_status: str,
) -> ShellSectionInventoryEntry:
    suffix = source_section_id.replace(".", "_").lower()
    payload: dict[str, Any] = {
        "inventory_entry_id": f"p2_9_a_section_inventory_entry_{suffix}",
        "schema_version": P2_9_A_INVENTORY_ENTRY_VERSION,
        "source_section_id": source_section_id,
        "source_section_name": source_section_name,
        "source_checkpoint_range": source_checkpoint_range,
        "source_seal_or_latest_pack": source_seal_or_latest_pack,
        "source_report_ref": source_report_ref,
        "source_status": source_status,
        "source_truth_label": ShellExitSealFoundationTruthBoundary.CONTRACT_ONLY.value,
        "limitations": (
            "inventory entry references section evidence only",
            "does not duplicate agent state",
        ),
    }
    return ShellSectionInventoryEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_shell_section_inventory_intake() -> ShellSectionInventoryIntake:
    entries = tuple(
        build_shell_section_inventory_entry(
            source_section_id,
            source_section_name,
            f"{source_section_id}.0–{source_section_id}.20",
            source_pack_or_seal,
            source_report_ref,
            source_status,
        )
        for (
            source_section_id,
            source_section_name,
            source_pack_or_seal,
            source_report_ref,
            _commit,
            _test_ref,
            source_status,
        ) in _PRIOR_SECTION_EVIDENCE_SPECS
    )
    payload: dict[str, Any] = {
        "inventory_intake_id": "p2_9_a_shell_section_inventory_intake",
        "schema_version": P2_9_A_INVENTORY_INTAKE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "official_section_name": P2_9_A_OFFICIAL_SECTION_NAME,
        "inventory_entries": entries,
        "source_sections": tuple(spec[0] for spec in _PRIOR_SECTION_EVIDENCE_SPECS),
        "is_governance_source": False,
        "duplicates_agent_state": False,
        "truth_label": (
            ShellExitSealFoundationTruthBoundary.SECTION_INVENTORY_INTAKE_ONLY.value
        ),
        "limitations": (
            "inventory intake is reference-only",
            "does not duplicate agent governance state",
        ),
    }
    return ShellSectionInventoryIntake(
        **payload,
        intake_hash=_hash_payload(payload),
    )


def build_shell_exit_criterion(
    category: str,
    name: str,
    description: str,
    *,
    criterion_suffix: str,
    requires_future_pack: bool = True,
) -> ShellExitCriterion:
    payload: dict[str, Any] = {
        "criterion_id": f"p2_9_a_exit_criterion_{criterion_suffix}",
        "schema_version": P2_9_A_CRITERION_VERSION,
        "category": category,
        "name": name,
        "description": description,
        "required_evidence_ref": P2_8_D_REPORT_PATH,
        "status": "DEFINED_CONTRACT_ONLY",
        "requires_future_pack": requires_future_pack,
        "is_validation_execution": False,
        "truth_label": ShellExitSealFoundationTruthBoundary.EXIT_CRITERION_ONLY.value,
        "limitations": (
            "criterion is catalog descriptor only",
            "does not execute validation",
        ),
    }
    return ShellExitCriterion(**payload, criterion_hash=_hash_payload(payload))


def build_shell_exit_criteria_catalog() -> ShellExitCriteriaCatalog:
    criteria_specs: tuple[tuple[str, str, str, str], ...] = (
        ("evidence", "prior_section_evidence", "Prior P2 section evidence indexed", "evidence"),
        ("coverage", "section_inventory", "P2.0–P2.8 section inventory complete", "coverage"),
        ("validation", "exit_validation_matrix", "Exit validation matrix defined", "validation"),
        ("boundaries", "no_overclaim_boundaries", "No-release/no-product boundaries active", "boundaries"),
        ("availability", "unavailable_capabilities", "Unavailable capabilities declared", "availability"),
        (
            "unavailable_capabilities",
            "future_pack_honesty",
            "Future packs marked unavailable",
            "future_pack_honesty",
        ),
        ("handoff_readiness", "p2_9_b_handoff", "P2.9-B handoff contract ready", "handoff"),
        ("no_overclaim", "no_live_no_trace", "No LIVE/TRACE_VERIFIED/product overclaim", "no_overclaim"),
    )
    criteria = tuple(
        build_shell_exit_criterion(category, name, description, criterion_suffix=suffix)
        for category, name, description, suffix in criteria_specs
    )
    payload: dict[str, Any] = {
        "criteria_catalog_id": "p2_9_a_shell_exit_criteria_catalog",
        "schema_version": P2_9_A_CRITERIA_CATALOG_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "official_section_name": P2_9_A_OFFICIAL_SECTION_NAME,
        "criteria": criteria,
        "criteria_categories": _EXIT_CRITERIA_CATEGORIES,
        "is_validation_execution": False,
        "decides_authority": False,
        "truth_label": ShellExitSealFoundationTruthBoundary.EXIT_CRITERIA_CATALOG_ONLY.value,
        "limitations": (
            "catalog is non-executable checklist for later P2.9 packs",
            "does not decide authority",
        ),
    }
    catalog = ShellExitCriteriaCatalog(**payload, catalog_hash=_hash_payload(payload))
    assert_criteria_catalog_does_not_execute_validation(catalog)
    return catalog


def build_shell_exit_readiness_dimension(
    dimension_name: str,
    dimension_scope: str,
    source_criteria_refs: tuple[str, ...],
    *,
    requires_validation_execution: bool = True,
) -> ShellExitReadinessDimension:
    suffix = dimension_name.replace(" ", "_").lower()
    payload: dict[str, Any] = {
        "readiness_dimension_id": f"p2_9_a_exit_readiness_dimension_{suffix}",
        "schema_version": P2_9_A_READINESS_DIMENSION_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "dimension_name": dimension_name,
        "dimension_status": ShellExitReadinessDimensionStatus.DEFINED_CONTRACT_ONLY,
        "dimension_scope": dimension_scope,
        "source_criteria_refs": source_criteria_refs,
        "requires_validation_execution": requires_validation_execution,
        "claims_product_readiness": False,
        "truth_label": ShellExitSealFoundationTruthBoundary.READINESS_DIMENSION_ONLY.value,
        "limitations": (
            "readiness dimension is contract-only descriptor",
            "does not claim product readiness",
        ),
    }
    dimension = ShellExitReadinessDimension(
        **payload,
        dimension_hash=_hash_payload(payload),
    )
    assert_readiness_dimension_is_not_product_readiness(dimension)
    return dimension


def build_shell_exit_unavailable_capability_entry(
    capability_id: str,
    capability_name: str,
    required_future_pack: str,
    risk_if_overclaimed: str,
) -> ShellExitUnavailableCapabilityEntry:
    payload: dict[str, Any] = {
        "capability_id": capability_id,
        "schema_version": P2_9_A_UNAVAILABLE_ENTRY_VERSION,
        "capability_name": capability_name,
        "unavailable_reason": (
            f"{capability_name} is unavailable at P2.9-A foundation scope"
        ),
        "required_future_pack": required_future_pack,
        "risk_if_overclaimed": risk_if_overclaimed,
        "truth_label": ShellExitSealFoundationTruthBoundary.UNAVAILABLE.value,
        "limitations": (
            "capability honestly marked unavailable",
            "not runtime implementation",
        ),
    }
    return ShellExitUnavailableCapabilityEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def build_shell_exit_unavailable_capability_declaration() -> (
    ShellExitUnavailableCapabilityDeclaration
):
    entries = tuple(
        build_shell_exit_unavailable_capability_entry(
            capability_id,
            capability_name,
            required_future_pack,
            risk_if_overclaimed,
        )
        for capability_id, capability_name, required_future_pack, risk_if_overclaimed in (
            _UNAVAILABLE_CAPABILITY_SPECS
        )
    )
    future_packs = tuple(
        sorted({entry.required_future_pack for entry in entries})
    )
    payload: dict[str, Any] = {
        "unavailable_declaration_id": "p2_9_a_shell_exit_unavailable_capability_declaration",
        "schema_version": P2_9_A_UNAVAILABLE_DECL_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "unavailable_entries": entries,
        "future_pack_refs": future_packs,
        "implements_runtime": False,
        "truth_label": (
            ShellExitSealFoundationTruthBoundary.UNAVAILABLE_CAPABILITY_DECLARATION_ONLY.value
        ),
        "limitations": (
            "declaration marks capabilities unavailable honestly",
            "does not implement runtime",
        ),
    }
    return ShellExitUnavailableCapabilityDeclaration(
        **payload,
        declaration_hash=_hash_payload(payload),
    )


def build_shell_exit_no_release_seal_boundary() -> ShellExitNoReleaseSealBoundary:
    payload: dict[str, Any] = {
        "boundary_id": "p2_9_a_shell_exit_no_release_seal_boundary",
        "schema_version": P2_9_A_NO_RELEASE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "release_seal_created": False,
        "release_readiness_claimed": False,
        "release_scope_claimed": False,
        "boundary_active": True,
        "truth_label": ShellExitSealFoundationTruthBoundary.NO_RELEASE_SEAL_BOUNDARY.value,
        "limitations": (
            "boundary prevents release seal overclaim",
            "not release seal implementation",
        ),
    }
    boundary = ShellExitNoReleaseSealBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )
    assert_shell_exit_seal_is_not_release_seal(boundary)
    return boundary


def build_shell_exit_no_product_readiness_boundary() -> ShellExitNoProductReadinessBoundary:
    payload: dict[str, Any] = {
        "boundary_id": "p2_9_a_shell_exit_no_product_readiness_boundary",
        "schema_version": P2_9_A_NO_PRODUCT_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "product_readiness_claimed": False,
        "product_behavior_claimed": False,
        "operator_testable_product_behavior_claimed": False,
        "frontend_ui_created": False,
        "boundary_active": True,
        "truth_label": (
            ShellExitSealFoundationTruthBoundary.NO_PRODUCT_READINESS_BOUNDARY.value
        ),
        "limitations": (
            "boundary prevents product readiness overclaim",
            "not product readiness implementation",
        ),
    }
    return ShellExitNoProductReadinessBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_exit_no_live_runtime_boundary() -> ShellExitNoLiveRuntimeBoundary:
    payload: dict[str, Any] = {
        "boundary_id": "p2_9_a_shell_exit_no_live_runtime_boundary",
        "schema_version": P2_9_A_NO_LIVE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "live_shell_runtime_created": False,
        "multi_client_runtime_created": False,
        "runtime_dispatch_created": False,
        "command_execution_created": False,
        "boundary_active": True,
        "truth_label": ShellExitSealFoundationTruthBoundary.NO_LIVE_RUNTIME_BOUNDARY.value,
        "limitations": (
            "boundary prevents live runtime overclaim",
            "not runtime implementation",
        ),
    }
    return ShellExitNoLiveRuntimeBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_exit_no_p2_complete_boundary() -> ShellExitNoP2CompleteBoundary:
    payload: dict[str, Any] = {
        "boundary_id": "p2_9_a_shell_exit_no_p2_complete_boundary",
        "schema_version": P2_9_A_NO_P2_COMPLETE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "p2_complete_claimed": False,
        "p2_release_claimed": False,
        "p2_done_claimed": False,
        "boundary_active": True,
        "truth_label": ShellExitSealFoundationTruthBoundary.NO_P2_COMPLETE_BOUNDARY.value,
        "limitations": (
            "boundary prevents P2 completion overclaim",
            "P2.9-A foundation is not P2 complete",
        ),
    }
    return ShellExitNoP2CompleteBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_exit_no_shell_complete_boundary() -> ShellExitNoShellCompleteBoundary:
    payload: dict[str, Any] = {
        "boundary_id": "p2_9_a_shell_exit_no_shell_complete_boundary",
        "schema_version": P2_9_A_NO_SHELL_COMPLETE_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "shell_complete_claimed": False,
        "shell_release_claimed": False,
        "shell_done_claimed": False,
        "boundary_active": True,
        "truth_label": (
            ShellExitSealFoundationTruthBoundary.NO_SHELL_COMPLETE_BOUNDARY.value
        ),
        "limitations": (
            "boundary prevents Shell completion overclaim",
            "P2.9-A foundation is not Shell complete",
        ),
    }
    return ShellExitNoShellCompleteBoundary(
        **payload,
        boundary_hash=_hash_payload(payload),
    )


def build_shell_exit_p2_9_b_handoff_contract() -> ShellExitP29BHandoffContract:
    payload: dict[str, Any] = {
        "handoff_id": "p2_9_a_shell_exit_p2_9_b_handoff_contract",
        "schema_version": P2_9_A_P2_9_B_HANDOFF_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "handoff_to_pack": P2_9_A_NEXT_PACK,
        "handoff_to_section": P2_9_A_NEXT_SECTION,
        "handoff_status": ShellExitP29BHandoffStatus.READY_FOR_P2_9_B_CONTRACT_HANDOFF,
        "handoff_reason": _P2_9_B_HANDOFF_REASON,
        "available_inputs": (
            "ShellExitSealFoundationResult",
            "ShellExitCriteriaCatalog",
            "ShellPriorSectionEvidenceIntake",
            P2_9_A_REPORT_PATH,
        ),
        "required_next_work": (
            "P2.9.6–P2.9.10 Shell Exit Seal Readiness / Validation / Evidence Matrix",
        ),
        "is_p2_9_b_implementation": False,
        "starts_p2_9_b": False,
        "truth_label": (
            ShellExitSealFoundationTruthBoundary.P2_9_B_HANDOFF_CONTRACT_ONLY.value
        ),
        "limitations": (
            "P2.9-B handoff is contract boundary only",
            "handoff does not start P2.9-B implementation",
        ),
    }
    handoff = ShellExitP29BHandoffContract(
        **payload,
        handoff_hash=_hash_payload(payload),
    )
    assert_p2_9_b_handoff_is_not_p2_9_b_implementation(handoff)
    return handoff


def build_shell_exit_seal_foundation_result(
    seal_result: P28DShellStateSectionSealResult | None = None,
) -> ShellExitSealFoundationResult:
    if seal_result is None:
        seal_result = build_p2_8_d_shell_state_section_seal_result()
    gate = build_shell_exit_seal_foundation_gate(seal_result)
    evidence_intake = build_shell_prior_section_evidence_intake()
    inventory_intake = build_shell_section_inventory_intake()
    criteria_catalog = build_shell_exit_criteria_catalog()
    readiness_dimensions = tuple(
        build_shell_exit_readiness_dimension(name, scope, refs)
        for name, scope, refs in _READINESS_DIMENSION_SPECS
    )
    unavailable = build_shell_exit_unavailable_capability_declaration()
    no_release = build_shell_exit_no_release_seal_boundary()
    no_product = build_shell_exit_no_product_readiness_boundary()
    no_live = build_shell_exit_no_live_runtime_boundary()
    no_p2 = build_shell_exit_no_p2_complete_boundary()
    no_shell = build_shell_exit_no_shell_complete_boundary()
    handoff = build_shell_exit_p2_9_b_handoff_contract()
    payload: dict[str, Any] = {
        "foundation_result_id": "p2_9_a_shell_exit_seal_foundation_result",
        "schema_version": P2_9_A_FOUNDATION_RESULT_VERSION,
        "section_id": P2_9_A_SECTION_ID,
        "created_for_pack": P2_9_A_PACK_ID,
        "official_section_name": P2_9_A_OFFICIAL_SECTION_NAME,
        "foundation_gate": gate,
        "prior_section_evidence_intake": evidence_intake,
        "section_inventory_intake": inventory_intake,
        "exit_criteria_catalog": criteria_catalog,
        "readiness_dimensions": readiness_dimensions,
        "unavailable_capability_declaration": unavailable,
        "no_release_seal_boundary": no_release,
        "no_product_readiness_boundary": no_product,
        "no_live_runtime_boundary": no_live,
        "no_p2_complete_boundary": no_p2,
        "no_shell_complete_boundary": no_shell,
        "p2_9_b_handoff_contract": handoff,
        "is_completed_exit_seal": False,
        "is_release_seal": False,
        "claims_p2_complete": False,
        "claims_shell_complete": False,
        "claims_product_readiness": False,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_product_behavior": False,
        "truth_label": ShellExitSealFoundationTruthBoundary.EXIT_SEAL_FOUNDATION_ONLY.value,
        "limitations": (
            "foundation result is contract-only",
            "not completed Shell Exit Seal or release seal",
        ),
    }
    foundation = ShellExitSealFoundationResult(
        **payload,
        foundation_result_hash=_hash_payload(payload),
    )
    assert_foundation_is_not_final_exit_seal(foundation)
    return foundation


def build_p2_9_a_side_effect_proof() -> P29ASideEffectProof:
    return P29ASideEffectProof()


def build_p2_9_a_shell_exit_seal_foundation_result() -> P29AShellExitSealFoundationResult:
    seal_result = build_p2_8_d_shell_state_section_seal_result()
    foundation = build_shell_exit_seal_foundation_result(seal_result)
    side_effects = build_p2_9_a_side_effect_proof()
    drift, drift_details = detect_surface_taxonomy_drift()
    p2_8_handoff = seal_result.p2_9_handoff_contract
    payload: dict[str, Any] = {
        "schema_version": P2_9_A_RESULT_VERSION,
        "pack_id": P2_9_A_PACK_ID,
        "section_id": P2_9_A_SECTION_ID,
        "official_section_name": P2_9_A_OFFICIAL_SECTION_NAME,
        "covered_checkpoints": P2_9_A_PACK_CHECKPOINT_IDS,
        "dependency_pack": P2_9_A_DEPENDENCY_PACK,
        "p2_8_d_evidence_ref": f"{P2_8_D_REPORT_PATH}:{seal_result.result_hash[:12]}",
        "p2_8_d_section_seal_result_ref": _section_seal_result_ref(seal_result),
        "p2_8_d_p2_9_handoff_ref": _p2_8_d_p2_9_handoff_ref(p2_8_handoff),
        "foundation_gate": foundation.foundation_gate,
        "prior_section_evidence_intake": foundation.prior_section_evidence_intake,
        "section_inventory_intake": foundation.section_inventory_intake,
        "exit_criteria_catalog": foundation.exit_criteria_catalog,
        "readiness_dimensions": foundation.readiness_dimensions,
        "unavailable_capability_declaration": foundation.unavailable_capability_declaration,
        "no_release_seal_boundary": foundation.no_release_seal_boundary,
        "no_product_readiness_boundary": foundation.no_product_readiness_boundary,
        "no_live_runtime_boundary": foundation.no_live_runtime_boundary,
        "no_p2_complete_boundary": foundation.no_p2_complete_boundary,
        "no_shell_complete_boundary": foundation.no_shell_complete_boundary,
        "p2_9_b_handoff_contract": foundation.p2_9_b_handoff_contract,
        "foundation_result": foundation,
        "truth_labels": tuple(
            label.value for label in ShellExitSealFoundationTruthBoundary
        ),
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "side_effect_proof": side_effects,
        "next_pack": P2_9_A_NEXT_PACK,
        "claims_live": False,
        "claims_trace_verified": False,
        "claims_release_scope": False,
        "claims_product_behavior": False,
        "claims_product_readiness": False,
        "claims_p2_complete": False,
        "claims_shell_complete": False,
        "starts_future_work": False,
    }
    result = P29AShellExitSealFoundationResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert_p2_9_a_does_not_start_future_work(result)
    assert_p2_9_a_side_effects_all_false(result.side_effect_proof)
    return result


def serialize_p2_9_a_result(
    result: P29AShellExitSealFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_9_a_shell_exit_seal_foundation_result()
    return to_canonical_json(result.to_canonical_dict())


def render_shell_exit_seal_foundation_summary(
    result: P29AShellExitSealFoundationResult | None = None,
) -> str:
    if result is None:
        result = build_p2_9_a_shell_exit_seal_foundation_result()
    foundation = result.foundation_result
    catalog = foundation.exit_criteria_catalog
    unavailable = foundation.unavailable_capability_declaration
    return "\n".join(
        (
            f"{result.section_id} {result.official_section_name}",
            f"pack={result.pack_id}",
            f"gate={result.foundation_gate.gate_status.value}",
            f"prior_sections={len(foundation.prior_section_evidence_intake.evidence_entries)}",
            f"inventory_entries={len(foundation.section_inventory_intake.inventory_entries)}",
            f"criteria={len(catalog.criteria)}",
            f"readiness_dimensions={len(foundation.readiness_dimensions)}",
            f"unavailable_capabilities={len(unavailable.unavailable_entries)}",
            f"official_surfaces={len(OFFICIAL_ACTIVE_SURFACE_NAMES)}",
            f"next={result.next_pack}",
            f"completed_exit_seal={str(foundation.is_completed_exit_seal).lower()}",
            f"release_seal={str(foundation.is_release_seal).lower()}",
            f"product_readiness={str(foundation.claims_product_readiness).lower()}",
            f"p2_complete={str(foundation.claims_p2_complete).lower()}",
            f"shell_complete={str(foundation.claims_shell_complete).lower()}",
        )
    )
