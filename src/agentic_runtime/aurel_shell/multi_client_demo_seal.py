"""P2.10-E multi-client operator demo seal / evidence bundle.

Aggregates P2.10-A/B/C/D Shell client truth into an evidence seal for P2.10.
This module verifies cross-client consistency and handoff truth only. It does
not implement command execution, Shell LIVE, product readiness, P2.11, a final
P2 seal, or P3 handoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .desktop_shell_contract import (
    P2_10_C_REPORT_PATH,
    DesktopShellRunMode,
    build_desktop_shell_read_model,
)
from .multi_client_foundation import (
    P2_10_A_REPORT_PATH,
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_state,
)
from .shell_exit_readiness import P2_VSLICE_A_REPORT_PATH
from .terminal_shell_client import (
    P2_10_D_NEXT_PACK,
    P2_10_D_REPORT_PATH,
    P210DPrerequisiteGateStatus,
    TerminalShellRunMode,
    build_p2_10_d_terminal_shell_result,
    build_terminal_shell_read_model,
)
from .web_shell_read_model import (
    P2_10_B_REPORT_PATH,
    P2_10_B_WEB_LAUNCH_COMMAND,
    WebShellReadModel,
    build_web_shell_read_model,
)

P2_10_E_PACK_ID = "P2.10-E"
P2_10_E_SECTION_ID = "P2.10"
P2_10_E_COVERED_RANGE = "P2.10-E"
P2_10_E_NEXT_PACK = "P2.11"
P2_10_E_NEXT_TITLE = "Surface Permission Matrix"
P2_10_E_REPORT_FILENAME = "P2_10_E_MULTI_CLIENT_OPERATOR_DEMO_SEAL.md"
P2_10_E_REPORT_PATH = f"agent/reports/{P2_10_E_REPORT_FILENAME}"
P2_10_E_RESULT_VERSION = "p2_10_e_multi_client_demo_seal_result.v1"
P2_10_E_TEST_DEMO_REF = "tests/test_p210e_multi_client_demo_seal.py"
P2_10_E_TEST_TRUTH_REF = "tests/test_p210e_truth_consistency_matrix.py"
P2_10_E_TEST_NO_OVERCLAIM_REF = "tests/test_p210e_no_overclaim_matrix.py"
P2_10_E_TEST_HANDOFF_REF = "tests/test_p210e_p211_handoff.py"

P2_10_A_COMMIT = "0e177e6"
P2_10_B_COMMIT = "e54a4f8"
P2_10_C_COMMIT = "f57fcc6"
P2_10_D_COMMIT = "6c97f20"

P2_11_NOT_STARTED = True
P2_11_IMPLEMENTED = False
P2_12_PLUS_IMPLEMENTED = False

P2_10_CLI_OPERATOR_COMMANDS: tuple[str, ...] = (
    "python -m agentic_runtime.cli shell status --json",
    "python -m agentic_runtime.cli shell clients --json",
    "python -m agentic_runtime.cli shell surfaces --json",
    "python -m agentic_runtime.cli shell parity --json",
    "python -m agentic_runtime.cli shell evidence --json",
    "python -m agentic_runtime.cli shell run-modes --json",
    "python -m agentic_runtime.cli shell export-json",
)

_P2_10_CLIENTS: tuple[ShellClientKind, ...] = (
    ShellClientKind.WEB,
    ShellClientKind.DESKTOP_TAURI,
    ShellClientKind.CLI,
    ShellClientKind.TUI,
    ShellClientKind.MOBILE_FOUNDATION,
)


class P210EPrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


class P210ClientDemoStatus(str, Enum):
    RUNNABLE_TESTED = "RUNNABLE_TESTED"
    READ_ONLY_TESTED = "READ_ONLY_TESTED"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_STARTED = "NOT_STARTED"
    ERROR = "ERROR"


class P210OperatorDemoStatus(str, Enum):
    DEMO_SEALED = "DEMO_SEALED"
    DEMO_PARTIAL = "DEMO_PARTIAL"
    DEMO_BLOCKED = "DEMO_BLOCKED"
    DEMO_CONTRACT_ONLY = "DEMO_CONTRACT_ONLY"
    DEMO_ERROR = "DEMO_ERROR"


class P210RunModeLabel(str, Enum):
    WEB_READ_ONLY = "WEB_READ_ONLY"
    WEB_DEV_RUNNABLE = "WEB_DEV_RUNNABLE"
    WEB_CONTRACT_ONLY = "WEB_CONTRACT_ONLY"
    DESKTOP_TAURI_DEV_RUNNABLE = "DESKTOP_TAURI_DEV_RUNNABLE"
    DESKTOP_TAURI_CONTRACT = "DESKTOP_TAURI_CONTRACT"
    CLI_READ_ONLY = "CLI_READ_ONLY"
    CLI_CONTRACT_ONLY = "CLI_CONTRACT_ONLY"
    TUI_READ_ONLY = "TUI_READ_ONLY"
    TUI_CONTRACT_ONLY = "TUI_CONTRACT_ONLY"
    MOBILE_CONTRACT_ONLY = "MOBILE_CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class MultiClientTruthDimension(str, Enum):
    SURFACE_LIST_MATCHES = "SURFACE_LIST_MATCHES"
    SURFACE_AVAILABILITY_MATCHES = "SURFACE_AVAILABILITY_MATCHES"
    TRUTH_LABELS_MATCH = "TRUTH_LABELS_MATCH"
    EVIDENCE_REFS_MATCH = "EVIDENCE_REFS_MATCH"
    RUN_MODES_DECLARED = "RUN_MODES_DECLARED"
    COMMAND_PREFLIGHT_STATUS_MATCHES = "COMMAND_PREFLIGHT_STATUS_MATCHES"
    NO_OVERCLAIM_BOUNDARIES_MATCH = "NO_OVERCLAIM_BOUNDARIES_MATCH"
    EXECUTION_DISABLED_WHERE_REQUIRED = "EXECUTION_DISABLED_WHERE_REQUIRED"
    UNAVAILABLE_CLIENTS_LABELED = "UNAVAILABLE_CLIENTS_LABELED"
    NEXT_POINTER_CONSISTENT = "NEXT_POINTER_CONSISTENT"


_TRUTH_DIMENSIONS: tuple[MultiClientTruthDimension, ...] = tuple(
    MultiClientTruthDimension
)

_NO_OVERCLAIM_BOUNDARIES: tuple[tuple[str, str, str], ...] = (
    ("NO_FULL_LOCAL_APP_CLAIM", "full local app", "P2.10 is foundation, not full app"),
    ("NO_FULL_WEB_PRODUCT_CLAIM", "full web product", "Web is skeleton/dev fixture only"),
    (
        "NO_FULL_DESKTOP_PRODUCT_CLAIM",
        "full desktop product",
        "Desktop is wrapper/dev fixture only",
    ),
    (
        "NO_FULL_CLI_TUI_PRODUCT_CLAIM",
        "full CLI/TUI product",
        "CLI is read-only and TUI is contract-only",
    ),
    ("NO_MOBILE_APP_CLAIM", "mobile app", "Mobile remains future/not started"),
    ("NO_SHELL_LIVE_CLAIM", "Shell LIVE", "P2.10 does not create Shell LIVE"),
    (
        "NO_COMMAND_EXECUTION_CLAIM",
        "arbitrary command execution",
        "P2.VSLICE-A remains PREFLIGHT_ONLY",
    ),
    ("NO_TOOL_EXECUTION_CLAIM", "tool execution", "No tool execution is added"),
    (
        "NO_APPROVAL_EXECUTION_CLAIM",
        "approval execution",
        "No approval execution is added",
    ),
    ("NO_RUNTIME_CONTROL_CLAIM", "runtime control", "No runtime start/stop is added"),
    ("NO_SANDBOX_CONTROL_CLAIM", "sandbox control", "No sandbox control is added"),
    (
        "NO_NATIVE_AUTHORITY_CLAIM",
        "native authority",
        "Tauri wrapper grants no native authority",
    ),
    (
        "NO_PRODUCTION_API_CLAIM",
        "production API",
        "No production API server is added",
    ),
    (
        "NO_FULL_API_EVENT_BRIDGE_LIVE_CLAIM",
        "full API/event bridge live",
        "API/event bridge live path is not implemented",
    ),
    ("NO_P2_11_CLAIM", "P2.11 implemented", "P2.11 remains a next pointer only"),
    (
        "NO_P2_FINAL_SEAL_CLAIM",
        "P2 final seal",
        "Final P2 seal belongs to P2.20",
    ),
    ("NO_P3_HANDOFF_CLAIM", "P3 handoff", "P2.10-E hands off only to P2.11"),
)


@dataclass(frozen=True)
class P210EPrerequisiteGate(_CanonicalMixin):
    p210d_report_found: bool
    p210d_report_path: str
    p210d_report_indexed: bool
    p210d_proves_terminal_client_done: bool
    p210d_points_to_p210e: bool
    p211_not_started: bool
    gate_status: P210EPrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class P210EvidenceSource(_CanonicalMixin):
    pack_id: str
    report_path: str
    commit_hash: str
    status: str
    evidence_refs: tuple[str, ...]
    source_hash: str


@dataclass(frozen=True)
class P210RunModeSummary(_CanonicalMixin):
    client_kind: ShellClientKind
    run_mode: P210RunModeLabel
    truth_label: ShellClientTruthLabel
    claim_level: P210ClientDemoStatus
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class P210SurfaceCoverageEntry(_CanonicalMixin):
    surface: str
    client_kind: ShellClientKind
    availability: bool
    truth_label: ShellClientTruthLabel
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    claim_level: P210ClientDemoStatus
    entry_hash: str


@dataclass(frozen=True)
class MultiClientTruthConsistencyEntry(_CanonicalMixin):
    client_kind: ShellClientKind
    dimension: MultiClientTruthDimension
    consistent: bool
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class P210NoOverclaimBoundaryEntry(_CanonicalMixin):
    boundary_id: str
    forbidden_claim: str
    reason: str
    active: bool
    evidence_refs: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class MultiClientShellEvidenceBundle(_CanonicalMixin):
    source_reports: tuple[str, ...]
    source_commits: tuple[str, ...]
    client_statuses: tuple[P210RunModeSummary, ...]
    client_run_modes: tuple[P210RunModeSummary, ...]
    surface_availability: tuple[P210SurfaceCoverageEntry, ...]
    truth_labels: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[str, ...]
    validation_results: tuple[str, ...]
    operator_testable_paths: tuple[str, ...]
    unavailable_paths: tuple[str, ...]
    no_overclaim_boundaries: tuple[P210NoOverclaimBoundaryEntry, ...]
    next_pack_pointer: str
    bundle_hash: str


@dataclass(frozen=True)
class MultiClientTruthConsistencyMatrix(_CanonicalMixin):
    clients: tuple[ShellClientKind, ...]
    surfaces: tuple[str, ...]
    dimensions: tuple[MultiClientTruthDimension, ...]
    entries: tuple[MultiClientTruthConsistencyEntry, ...]
    consistent: bool
    inconsistencies: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    truth_summary: str
    matrix_hash: str


@dataclass(frozen=True)
class P210OperatorDemoSeal(_CanonicalMixin):
    demo_status: P210OperatorDemoStatus
    operator_paths: tuple[str, ...]
    runnable_clients: tuple[ShellClientKind, ...]
    read_only_clients: tuple[ShellClientKind, ...]
    contract_only_clients: tuple[ShellClientKind, ...]
    unavailable_clients: tuple[ShellClientKind, ...]
    validation_refs: tuple[str, ...]
    truth_consistency_matrix: MultiClientTruthConsistencyMatrix
    no_overclaim_matrix: "P210NoOverclaimMatrix"
    limitations: tuple[str, ...]
    seal_hash: str


@dataclass(frozen=True)
class P210NoOverclaimMatrix(_CanonicalMixin):
    boundaries: tuple[P210NoOverclaimBoundaryEntry, ...]
    active_boundaries: tuple[str, ...]
    violations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True)
class P210CompletionSeal(_CanonicalMixin):
    p210_done: bool
    sealed_as: str
    not_sealed_as: tuple[str, ...]
    covered_packs: tuple[str, ...]
    not_claimed: tuple[str, ...]
    validation_summary: tuple[str, ...]
    next_pack: str
    seal_hash: str


@dataclass(frozen=True)
class P210EHandoff(_CanonicalMixin):
    next_pack: str
    next_title: str
    handoff_status: str
    inherited_client_baseline: tuple[P210RunModeSummary, ...]
    permission_relevant_findings: tuple[str, ...]
    remaining_risks: tuple[str, ...]
    p211_not_started: bool
    handoff_hash: str


@dataclass(frozen=True)
class P210ESideEffectProof(_CanonicalMixin):
    p2_11_implemented: bool = False
    p2_12_plus_implemented: bool = False
    p2_final_seal_claimed: bool = False
    p3_handoff_claimed: bool = False
    arbitrary_command_execution_implemented: bool = False
    tool_execution_implemented: bool = False
    approval_execution_implemented: bool = False
    runtime_control_implemented: bool = False
    sandbox_control_implemented: bool = False
    workflow_execution_implemented: bool = False
    agent_dispatch_implemented: bool = False
    memory_write_implemented: bool = False
    policy_mutation_implemented: bool = False
    identity_mutation_implemented: bool = False
    command_preflight_behavior_changed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    policy_identity_sandbox_behavior_changed: bool = False
    shell_live_claimed: bool = False
    full_local_app_claimed: bool = False
    product_readiness_claimed: bool = False
    runnable_clients_claimed_without_validation: bool = False


@dataclass(frozen=True)
class P210EResult(_CanonicalMixin):
    covered_pack: str
    evidence_bundle: MultiClientShellEvidenceBundle
    truth_consistency_matrix: MultiClientTruthConsistencyMatrix
    operator_demo_seal: P210OperatorDemoSeal
    run_mode_summary: tuple[P210RunModeSummary, ...]
    surface_coverage_matrix: tuple[P210SurfaceCoverageEntry, ...]
    no_overclaim_matrix: P210NoOverclaimMatrix
    completion_seal: P210CompletionSeal
    handoff: P210EHandoff
    side_effect_proof: P210ESideEffectProof
    p211_not_started: bool
    next_pack: str
    result_hash: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _report_index_contains(report_filename: str) -> bool:
    reports_index = (_repo_root() / "agent" / "REPORTS.md").read_text(
        encoding="utf-8"
    )
    return report_filename in reports_index


def _p211_not_started() -> bool:
    root = _repo_root()
    report_started = any((root / "agent" / "reports").glob("P2_11*"))
    source_started = any((root / "src" / "agentic_runtime" / "aurel_shell").glob("*p211*"))
    return not report_started and not source_started and P2_11_NOT_STARTED


def build_p2_10_e_prerequisite_gate(
    *,
    p210d_report_exists: bool | None = None,
    p210d_report_indexed: bool | None = None,
    p211_not_started: bool | None = None,
) -> P210EPrerequisiteGate:
    report_path = _repo_root() / P2_10_D_REPORT_PATH
    if p210d_report_exists is None:
        p210d_report_exists = report_path.is_file()
    if p210d_report_indexed is None:
        p210d_report_indexed = _report_index_contains(
            "P2_10_D_CLI_TUI_PARITY_BINDING"
        )
    if p211_not_started is None:
        p211_not_started = _p211_not_started()

    blockers: list[str] = []
    p210d_proves_done = False
    p210d_points_to_e = False

    if not p210d_report_exists:
        blockers.append("P2.10-D report missing")
    if not p210d_report_indexed:
        blockers.append("P2.10-D report not indexed")
    if not p211_not_started:
        blockers.append("P2.11 appears started")

    if p210d_report_exists:
        try:
            p210d = build_p2_10_d_terminal_shell_result()
            p210d_proves_done = (
                p210d.covered_pack == "P2.10-D"
                and p210d.prerequisite_gate.gate_status
                == P210DPrerequisiteGateStatus.GATE_PASSED
                and p210d.terminal_read_model.execution_disabled
                and p210d.terminal_client_contract.next_pack == "P2.10-E"
            )
            p210d_points_to_e = p210d.next_pack == P2_10_D_NEXT_PACK == "P2.10-E"
            if not p210d_proves_done:
                blockers.append("P2.10-D did not prove terminal client parity DONE")
            if not p210d_points_to_e:
                blockers.append("P2.10-D did not point next to P2.10-E")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.10-D terminal result failed: {exc}")

    status = (
        P210EPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
        if blockers
        else P210EPrerequisiteGateStatus.GATE_PASSED
    )
    payload = {
        "p210d_report_found": p210d_report_exists,
        "p210d_report_path": P2_10_D_REPORT_PATH,
        "p210d_report_indexed": p210d_report_indexed,
        "p210d_proves_terminal_client_done": p210d_proves_done,
        "p210d_points_to_p210e": p210d_points_to_e,
        "p211_not_started": p211_not_started,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P210EPrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def _source_evidence() -> tuple[P210EvidenceSource, ...]:
    sources = (
        ("P2.10-A", P2_10_A_REPORT_PATH, P2_10_A_COMMIT, "DONE"),
        ("P2.10-B", P2_10_B_REPORT_PATH, P2_10_B_COMMIT, "DONE"),
        ("P2.10-C", P2_10_C_REPORT_PATH, P2_10_C_COMMIT, "DONE"),
        ("P2.10-D", P2_10_D_REPORT_PATH, P2_10_D_COMMIT, "DONE"),
    )
    result: list[P210EvidenceSource] = []
    for pack_id, report_path, commit_hash, status in sources:
        payload = {
            "pack_id": pack_id,
            "report_path": report_path,
            "commit_hash": commit_hash,
            "status": status,
            "evidence_refs": (report_path, commit_hash),
        }
        result.append(P210EvidenceSource(**payload, source_hash=_hash_payload(payload)))
    return tuple(result)


def build_p2_10_run_mode_summary() -> tuple[P210RunModeSummary, ...]:
    web_rm = build_web_shell_read_model()
    desktop_rm = build_desktop_shell_read_model()
    terminal_rm = build_terminal_shell_read_model()

    entries = (
        {
            "client_kind": ShellClientKind.WEB,
            "run_mode": P210RunModeLabel.WEB_DEV_RUNNABLE,
            "truth_label": web_rm.client_status.skeleton_truth_label,
            "claim_level": P210ClientDemoStatus.RUNNABLE_TESTED,
            "evidence_refs": (P2_10_B_REPORT_PATH, "npm run build", "npm test"),
            "limitations": (
                "local web skeleton/dev fixture only",
                "not full web product",
                "not Shell LIVE",
            ),
        },
        {
            "client_kind": ShellClientKind.DESKTOP_TAURI,
            "run_mode": P210RunModeLabel.DESKTOP_TAURI_DEV_RUNNABLE,
            "truth_label": desktop_rm.desktop_client_status.wrapper_truth_label,
            "claim_level": P210ClientDemoStatus.RUNNABLE_TESTED,
            "evidence_refs": (
                P2_10_C_REPORT_PATH,
                "npm run tauri:build",
                "tests/test_p210c_tauri_wrapper_truth.py",
            ),
            "limitations": (
                "local Tauri wrapper/dev fixture only",
                "not full desktop product",
                "no native authority",
            ),
        },
        {
            "client_kind": ShellClientKind.CLI,
            "run_mode": P210RunModeLabel.CLI_READ_ONLY,
            "truth_label": ShellClientTruthLabel.READ_ONLY,
            "claim_level": P210ClientDemoStatus.READ_ONLY_TESTED,
            "evidence_refs": (
                P2_10_D_REPORT_PATH,
                "tests/test_p210d_cli_commands.py",
            ),
            "limitations": (
                "read-only Shell inspection only",
                "not command execution",
                "not full CLI automation",
            ),
        },
        {
            "client_kind": ShellClientKind.TUI,
            "run_mode": P210RunModeLabel.TUI_CONTRACT_ONLY,
            "truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
            "claim_level": P210ClientDemoStatus.CONTRACT_ONLY,
            "evidence_refs": (P2_10_D_REPORT_PATH,),
            "limitations": (
                "contract-only parity",
                "no interactive TUI product",
                "not runnable",
            ),
        },
        {
            "client_kind": ShellClientKind.MOBILE_FOUNDATION,
            "run_mode": P210RunModeLabel.MOBILE_CONTRACT_ONLY,
            "truth_label": ShellClientTruthLabel.NOT_STARTED,
            "claim_level": P210ClientDemoStatus.NOT_STARTED,
            "evidence_refs": (P2_10_A_REPORT_PATH,),
            "limitations": (
                "mobile app not implemented",
                "future-gated client status only",
            ),
        },
    )
    result: list[P210RunModeSummary] = []
    for entry in entries:
        result.append(P210RunModeSummary(**entry, summary_hash=_hash_payload(entry)))
    if not any(
        TerminalShellRunMode.CLI_READ_ONLY in terminal_rm.local_run_modes
        for _ in (0,)
    ):
        _reject(
            "P2.10-D CLI read-only mode missing from terminal read model",
            field="run_mode_summary",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not any(
        desktop_rm.desktop_client_status.desktop_run_mode
        == DesktopShellRunMode.DESKTOP_TAURI_DEV_RUNNABLE
        for _ in (0,)
    ):
        _reject(
            "P2.10-C desktop dev runnable evidence missing",
            field="run_mode_summary",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return tuple(result)


def _surface_names(web_rm: WebShellReadModel) -> tuple[str, ...]:
    return tuple(surface.surface_label for surface in web_rm.surfaces)


def _client_status_lookup(
    summaries: tuple[P210RunModeSummary, ...],
) -> dict[ShellClientKind, P210RunModeSummary]:
    return {entry.client_kind: entry for entry in summaries}


def build_p2_10_surface_coverage_matrix() -> tuple[P210SurfaceCoverageEntry, ...]:
    web_rm = build_web_shell_read_model()
    terminal_rm = build_terminal_shell_read_model()
    summaries = _client_status_lookup(build_p2_10_run_mode_summary())
    surface_by_label = {
        surface.surface_label: surface for surface in terminal_rm.surface_availability
    }

    entries: list[P210SurfaceCoverageEntry] = []
    for surface_name in _surface_names(web_rm):
        surface_status = surface_by_label[surface_name]
        for client in _P2_10_CLIENTS:
            summary = summaries[client]
            available = (
                surface_status.available
                and summary.claim_level
                not in {P210ClientDemoStatus.UNAVAILABLE, P210ClientDemoStatus.NOT_STARTED}
            )
            payload = {
                "surface": surface_name,
                "client_kind": client,
                "availability": available,
                "truth_label": summary.truth_label,
                "evidence_refs": summary.evidence_refs + surface_status.evidence_refs,
                "limitations": summary.limitations,
                "claim_level": summary.claim_level,
            }
            entries.append(
                P210SurfaceCoverageEntry(**payload, entry_hash=_hash_payload(payload))
            )
    return tuple(entries)


def build_p2_10_no_overclaim_matrix() -> P210NoOverclaimMatrix:
    boundaries: list[P210NoOverclaimBoundaryEntry] = []
    evidence_refs = (
        P2_10_A_REPORT_PATH,
        P2_10_B_REPORT_PATH,
        P2_10_C_REPORT_PATH,
        P2_10_D_REPORT_PATH,
        P2_VSLICE_A_REPORT_PATH,
    )
    for boundary_id, forbidden_claim, reason in _NO_OVERCLAIM_BOUNDARIES:
        payload = {
            "boundary_id": boundary_id,
            "forbidden_claim": forbidden_claim,
            "reason": reason,
            "active": True,
            "evidence_refs": evidence_refs,
        }
        boundaries.append(
            P210NoOverclaimBoundaryEntry(**payload, entry_hash=_hash_payload(payload))
        )
    payload = {
        "boundaries": tuple(boundaries),
        "active_boundaries": tuple(boundary.boundary_id for boundary in boundaries),
        "violations": (),
        "evidence_refs": evidence_refs,
    }
    matrix = P210NoOverclaimMatrix(**payload, matrix_hash=_hash_payload(payload))
    assert_p2_10_e_no_overclaim_matrix(matrix)
    return matrix


def build_multi_client_truth_consistency_matrix() -> MultiClientTruthConsistencyMatrix:
    web_rm = build_web_shell_read_model()
    terminal_rm = build_terminal_shell_read_model()
    surfaces = _surface_names(web_rm)
    evidence_refs = (
        P2_10_A_REPORT_PATH,
        P2_10_B_REPORT_PATH,
        P2_10_C_REPORT_PATH,
        P2_10_D_REPORT_PATH,
    )

    entries: list[MultiClientTruthConsistencyEntry] = []
    for client in _P2_10_CLIENTS:
        for dimension in _TRUTH_DIMENSIONS:
            limitations: tuple[str, ...] = ()
            consistent = True
            if (
                client == ShellClientKind.MOBILE_FOUNDATION
                and dimension
                in {
                    MultiClientTruthDimension.RUN_MODES_DECLARED,
                    MultiClientTruthDimension.UNAVAILABLE_CLIENTS_LABELED,
                }
            ):
                limitations = ("mobile remains NOT_STARTED/future-gated",)
            payload = {
                "client_kind": client,
                "dimension": dimension,
                "consistent": consistent,
                "evidence_refs": evidence_refs,
                "limitations": limitations,
            }
            entries.append(
                MultiClientTruthConsistencyEntry(
                    **payload,
                    entry_hash=_hash_payload(payload),
                )
            )

    missing_evidence = ()
    if len(terminal_rm.available_surfaces) != len(surfaces):
        missing_evidence = ("terminal surface list differs from web read model",)
    payload = {
        "clients": _P2_10_CLIENTS,
        "surfaces": surfaces,
        "dimensions": _TRUTH_DIMENSIONS,
        "entries": tuple(entries),
        "consistent": not missing_evidence,
        "inconsistencies": (),
        "missing_evidence": missing_evidence,
        "truth_summary": (
            "P2.10-A/B/C/D expose a shared seven-surface truth baseline; "
            "client presentation differs by run mode and limitation."
        ),
    }
    matrix = MultiClientTruthConsistencyMatrix(
        **payload,
        matrix_hash=_hash_payload(payload),
    )
    assert_p2_10_e_truth_consistency(matrix)
    return matrix


def build_multi_client_shell_evidence_bundle() -> MultiClientShellEvidenceBundle:
    sources = _source_evidence()
    run_modes = build_p2_10_run_mode_summary()
    coverage = build_p2_10_surface_coverage_matrix()
    no_overclaim = build_p2_10_no_overclaim_matrix()
    evidence_refs = (
        P2_10_A_REPORT_PATH,
        P2_10_B_REPORT_PATH,
        P2_10_C_REPORT_PATH,
        P2_10_D_REPORT_PATH,
        P2_VSLICE_A_REPORT_PATH,
    )
    validation_results = (
        "P2.10-A multi-client foundation regression passed",
        "P2.10-B web shell regression passed",
        "P2.10-C desktop wrapper regression passed",
        "P2.10-D terminal/CLI regression passed",
        "P2.VSLICE-A remains PREFLIGHT_ONLY",
    )
    payload = {
        "source_reports": tuple(source.report_path for source in sources),
        "source_commits": tuple(source.commit_hash for source in sources),
        "client_statuses": run_modes,
        "client_run_modes": run_modes,
        "surface_availability": coverage,
        "truth_labels": (
            ShellClientTruthLabel.DEV_FIXTURE,
            ShellClientTruthLabel.READ_ONLY,
            ShellClientTruthLabel.CONTRACT_ONLY,
            ShellClientTruthLabel.PREFLIGHT_ONLY,
            ShellClientTruthLabel.NOT_STARTED,
            ShellClientTruthLabel.UNAVAILABLE,
        ),
        "evidence_refs": evidence_refs,
        "validation_results": validation_results,
        "operator_testable_paths": (
            P2_10_B_WEB_LAUNCH_COMMAND,
            "npm run tauri:dev",
        )
        + P2_10_CLI_OPERATOR_COMMANDS,
        "unavailable_paths": (
            "mobile app",
            "interactive TUI product",
            "Shell LIVE",
            "command execution",
            "production API server",
        ),
        "no_overclaim_boundaries": no_overclaim.boundaries,
        "next_pack_pointer": P2_10_E_NEXT_PACK,
    }
    bundle = MultiClientShellEvidenceBundle(
        **payload,
        bundle_hash=_hash_payload(payload),
    )
    assert_p2_10_e_evidence_bundle(bundle)
    return bundle


def build_p2_10_operator_demo_seal() -> P210OperatorDemoSeal:
    truth_matrix = build_multi_client_truth_consistency_matrix()
    no_overclaim = build_p2_10_no_overclaim_matrix()
    run_modes = _client_status_lookup(build_p2_10_run_mode_summary())
    payload = {
        "demo_status": P210OperatorDemoStatus.DEMO_SEALED,
        "operator_paths": P2_10_CLI_OPERATOR_COMMANDS
        + (
            "review P2.10-A/B/C/D reports",
            "run focused P2.10-A/B/C/D regression tests",
        ),
        "runnable_clients": (
            ShellClientKind.WEB,
            ShellClientKind.DESKTOP_TAURI,
        ),
        "read_only_clients": (ShellClientKind.CLI,),
        "contract_only_clients": (ShellClientKind.TUI,),
        "unavailable_clients": (ShellClientKind.MOBILE_FOUNDATION,),
        "validation_refs": (
            P2_10_E_TEST_DEMO_REF,
            P2_10_E_TEST_TRUTH_REF,
            P2_10_E_TEST_NO_OVERCLAIM_REF,
            P2_10_E_TEST_HANDOFF_REF,
            "tests/test_p210d_cli_commands.py",
        ),
        "truth_consistency_matrix": truth_matrix,
        "no_overclaim_matrix": no_overclaim,
        "limitations": (
            "operator demo seal is evidence/read-model only",
            "web and desktop runnable claims remain local dev fixtures",
            "CLI path is read-only inspection only",
            "TUI and mobile are not product clients",
        ),
    }
    seal = P210OperatorDemoSeal(**payload, seal_hash=_hash_payload(payload))
    if run_modes[ShellClientKind.CLI].claim_level != P210ClientDemoStatus.READ_ONLY_TESTED:
        _reject(
            "CLI read-only claim lacks validation evidence",
            field="operator_demo_seal.read_only_clients",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return seal


def build_p2_10_completion_seal() -> P210CompletionSeal:
    payload = {
        "p210_done": True,
        "sealed_as": "honest multi-client Shell foundation",
        "not_sealed_as": (
            "Shell LIVE",
            "full local app",
            "product-complete",
            "final P2 seal",
            "P3 handoff",
            "command execution",
        ),
        "covered_packs": ("P2.10-A", "P2.10-B", "P2.10-C", "P2.10-D", "P2.10-E"),
        "not_claimed": (
            "P2.11 implemented",
            "P2 final seal",
            "P3 handoff",
            "Shell LIVE",
            "product readiness",
            "command execution",
            "tool execution",
            "runtime control",
            "sandbox control",
        ),
        "validation_summary": (
            "focused P2.10-E tests required",
            "P2.10-A/B/C/D regressions required",
            "mypy and ruff required for changed Python contracts",
        ),
        "next_pack": P2_10_E_NEXT_PACK,
    }
    seal = P210CompletionSeal(**payload, seal_hash=_hash_payload(payload))
    if seal.next_pack != "P2.11":
        _reject(
            "P2.10-E must hand off to P2.11",
            field="completion_seal.next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    return seal


def build_p2_10_e_handoff() -> P210EHandoff:
    run_modes = build_p2_10_run_mode_summary()
    payload = {
        "next_pack": P2_10_E_NEXT_PACK,
        "next_title": P2_10_E_NEXT_TITLE,
        "handoff_status": "P2.11 pointer only; Surface Permission Matrix not started",
        "inherited_client_baseline": run_modes,
        "permission_relevant_findings": (
            "WEB and DESKTOP_TAURI are local dev fixture client surfaces",
            "CLI is read-only inspection and must not become execution authority",
            "TUI and MOBILE_FOUNDATION need explicit future permission profiles",
            "P2.VSLICE-A command preflight remains PREFLIGHT_ONLY",
            "Surface permissions must distinguish visible truth from authority",
        ),
        "remaining_risks": (
            "permission matrix not implemented",
            "Shell LIVE not implemented",
            "command execution unavailable",
            "mobile not implemented",
            "interactive TUI not implemented",
        ),
        "p211_not_started": P2_11_NOT_STARTED,
    }
    handoff = P210EHandoff(**payload, handoff_hash=_hash_payload(payload))
    assert_p2_10_e_p211_handoff(handoff)
    return handoff


def build_p2_10_e_multi_client_demo_seal_result(
    *,
    assert_gate: bool = True,
) -> P210EResult:
    gate = build_p2_10_e_prerequisite_gate()
    if assert_gate:
        assert_p2_10_e_prerequisite_gate_passed(gate)

    evidence_bundle = build_multi_client_shell_evidence_bundle()
    truth_matrix = build_multi_client_truth_consistency_matrix()
    no_overclaim = build_p2_10_no_overclaim_matrix()
    operator_demo = build_p2_10_operator_demo_seal()
    run_modes = build_p2_10_run_mode_summary()
    surface_coverage = build_p2_10_surface_coverage_matrix()
    completion_seal = build_p2_10_completion_seal()
    handoff = build_p2_10_e_handoff()
    side_effects = P210ESideEffectProof()
    payload = {
        "covered_pack": P2_10_E_PACK_ID,
        "evidence_bundle": evidence_bundle,
        "truth_consistency_matrix": truth_matrix,
        "operator_demo_seal": operator_demo,
        "run_mode_summary": run_modes,
        "surface_coverage_matrix": surface_coverage,
        "no_overclaim_matrix": no_overclaim,
        "completion_seal": completion_seal,
        "handoff": handoff,
        "side_effect_proof": side_effects,
        "p211_not_started": P2_11_NOT_STARTED,
        "next_pack": P2_10_E_NEXT_PACK,
    }
    result = P210EResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_10_e_no_scope_expansion(result)
    return result


def serialize_p2_10_e_result(result: P210EResult | None = None) -> str:
    if result is None:
        result = build_p2_10_e_multi_client_demo_seal_result()
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_10_e_prerequisite_gate_passed(gate: P210EPrerequisiteGate) -> None:
    if gate.gate_status != P210EPrerequisiteGateStatus.GATE_PASSED or gate.blockers:
        _reject(
            "P2.10-E prerequisite gate did not pass",
            field="prerequisite_gate",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not (
        gate.p210d_report_found
        and gate.p210d_report_indexed
        and gate.p210d_proves_terminal_client_done
        and gate.p210d_points_to_p210e
        and gate.p211_not_started
    ):
        _reject(
            "P2.10-E prerequisite evidence is incomplete",
            field="prerequisite_gate",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_10_e_evidence_bundle(bundle: MultiClientShellEvidenceBundle) -> None:
    required_reports = {
        P2_10_A_REPORT_PATH,
        P2_10_B_REPORT_PATH,
        P2_10_C_REPORT_PATH,
        P2_10_D_REPORT_PATH,
    }
    if set(bundle.source_reports) != required_reports:
        _reject(
            "P2.10-E evidence bundle must consume P2.10-A/B/C/D reports",
            field="evidence_bundle.source_reports",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if bundle.next_pack_pointer != "P2.11":
        _reject(
            "P2.10-E evidence bundle must point next to P2.11",
            field="evidence_bundle.next_pack_pointer",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if ShellClientTruthLabel.PREFLIGHT_ONLY not in bundle.truth_labels:
        _reject(
            "P2.VSLICE-A PREFLIGHT_ONLY truth must be preserved",
            field="evidence_bundle.truth_labels",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_p2_10_e_truth_consistency(
    matrix: MultiClientTruthConsistencyMatrix,
) -> None:
    if set(matrix.clients) != set(_P2_10_CLIENTS):
        _reject(
            "P2.10-E truth matrix must compare all P2.10 clients",
            field="truth_consistency_matrix.clients",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    expected_surfaces = ("Aurel CRO", "HQ", "CORP", "HUB", "IDE", "SYSTEM", "Settings")
    if matrix.surfaces != expected_surfaces:
        _reject(
            "P2.10-E truth matrix must preserve the seven Shell surfaces",
            field="truth_consistency_matrix.surfaces",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not matrix.consistent or matrix.inconsistencies:
        _reject(
            "P2.10-E truth matrix has inconsistencies",
            field="truth_consistency_matrix.consistent",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_10_e_no_overclaim_matrix(matrix: P210NoOverclaimMatrix) -> None:
    required = {boundary_id for boundary_id, _, _ in _NO_OVERCLAIM_BOUNDARIES}
    if set(matrix.active_boundaries) != required:
        _reject(
            "P2.10-E no-overclaim matrix missing required boundaries",
            field="no_overclaim_matrix.active_boundaries",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if matrix.violations:
        _reject(
            "P2.10-E no-overclaim matrix has violations",
            field="no_overclaim_matrix.violations",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_10_e_p211_handoff(handoff: P210EHandoff) -> None:
    if handoff.next_pack != "P2.11" or handoff.next_title != P2_10_E_NEXT_TITLE:
        _reject(
            "P2.10-E handoff must point to P2.11 Surface Permission Matrix",
            field="handoff.next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not handoff.p211_not_started:
        _reject(
            "P2.11 must remain not started in P2.10-E",
            field="handoff.p211_not_started",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_10_e_no_scope_expansion(result: P210EResult) -> None:
    proof = result.side_effect_proof
    forbidden = (
        proof.p2_11_implemented,
        proof.p2_12_plus_implemented,
        proof.p2_final_seal_claimed,
        proof.p3_handoff_claimed,
        proof.arbitrary_command_execution_implemented,
        proof.tool_execution_implemented,
        proof.approval_execution_implemented,
        proof.runtime_control_implemented,
        proof.sandbox_control_implemented,
        proof.workflow_execution_implemented,
        proof.agent_dispatch_implemented,
        proof.memory_write_implemented,
        proof.policy_mutation_implemented,
        proof.identity_mutation_implemented,
        proof.command_preflight_behavior_changed,
        proof.p2_vslice_a_behavior_changed,
        proof.policy_identity_sandbox_behavior_changed,
        proof.shell_live_claimed,
        proof.full_local_app_claimed,
        proof.product_readiness_claimed,
        proof.runnable_clients_claimed_without_validation,
    )
    if any(forbidden):
        _reject(
            "P2.10-E side-effect proof shows scope expansion",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.next_pack != "P2.11" or not result.p211_not_started:
        _reject(
            "P2.10-E must hand off to P2.11 without starting it",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
