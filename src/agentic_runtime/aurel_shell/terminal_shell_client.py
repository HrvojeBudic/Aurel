"""P2.10-D terminal Shell client parity / read-only terminal read model.

Python owns terminal truth. CLI/TUI terminal views consume the P2.10-A/B/C Shell
contracts and expose read-only inspection only. This module does not implement
command execution, tool execution, approval execution, runtime control, sandbox
control, Shell LIVE, or a full TUI product.
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
    P2_10_C_FIXTURE_REL_PATH,
    P2_10_C_REPORT_PATH,
    P210CPrerequisiteGateStatus,
    build_desktop_shell_read_model,
    build_p2_10_c_desktop_shell_result,
)
from .multi_client_foundation import (
    P2_10_A_REPORT_PATH,
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_local_run_modes,
    build_shell_client_state,
)
from .shell_exit_readiness import P2_VSLICE_A_REPORT_PATH
from .web_shell_read_model import (
    P2_10_B_FIXTURE_REL_PATH,
    P2_10_B_REPORT_PATH,
    build_web_shell_read_model,
)

P2_10_D_PACK_ID = "P2.10-D"
P2_10_D_SECTION_ID = "P2.10"
P2_10_D_COVERED_RANGE = "P2.10-D"
P2_10_D_NEXT_PACK = "P2.10-E"
P2_10_D_REPORT_FILENAME = "P2_10_D_CLI_TUI_PARITY_BINDING.md"
P2_10_D_REPORT_PATH = f"agent/reports/{P2_10_D_REPORT_FILENAME}"
P2_10_D_RESULT_VERSION = "p2_10_d_terminal_shell_client_result.v1"
P2_10_D_TEST_CLIENT_REF = "tests/test_p210d_terminal_shell_client.py"
P2_10_D_TEST_PARITY_REF = "tests/test_p210d_cli_tui_parity_matrix.py"
P2_10_D_TEST_NO_EXECUTION_REF = "tests/test_p210d_terminal_no_execution.py"
P2_10_D_TEST_CLI_REF = "tests/test_p210d_cli_commands.py"
P2_10_D_CLI_MODULE_REF = "src/agentic_runtime/cli_modules/shell_commands.py"
P2_10_D_TERMINAL_MODULE_REF = "src/agentic_runtime/aurel_shell/terminal_shell_client.py"

# Historical truth at the P2.10-D seal moment (preserved for pack regression evidence).
P2_10_E_NOT_STARTED = True
P2_10_E_IMPLEMENTED = False

# Operator canon aligned with agent/STATE.md and surface_permission_inspection.py.
OPERATOR_CANON_LAST_COMPLETED_PACK = "P2.11-C"
OPERATOR_CANON_NEXT_PACK = "P2.11-D"
OPERATOR_CANON_NEXT_NOT_STARTED = True
P2_11_C_REPORT_PATH = "agent/reports/P2_11_C_SURFACE_PERMISSION_OPERATOR_INSPECTION.md"


class P210DPrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


class TerminalShellClientKind(str, Enum):
    CLI = "CLI"
    TUI = "TUI"


class TerminalShellRunMode(str, Enum):
    CLI_READ_ONLY = "CLI_READ_ONLY"
    CLI_CONTRACT_ONLY = "CLI_CONTRACT_ONLY"
    TUI_READ_ONLY = "TUI_READ_ONLY"
    TUI_CONTRACT_ONLY = "TUI_CONTRACT_ONLY"
    TERMINAL_JSON_EXPORT = "TERMINAL_JSON_EXPORT"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class TerminalShellCapability(str, Enum):
    VIEW_SHELL_STATUS = "VIEW_SHELL_STATUS"
    VIEW_CLIENTS = "VIEW_CLIENTS"
    VIEW_SURFACES = "VIEW_SURFACES"
    VIEW_TRUTH_LABELS = "VIEW_TRUTH_LABELS"
    VIEW_EVIDENCE_REFS = "VIEW_EVIDENCE_REFS"
    VIEW_LOCAL_RUN_MODES = "VIEW_LOCAL_RUN_MODES"
    VIEW_PARITY_MATRIX = "VIEW_PARITY_MATRIX"
    EXPORT_JSON = "EXPORT_JSON"
    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    APPROVE_ACTION = "APPROVE_ACTION"
    RUN_TOOL = "RUN_TOOL"
    START_RUNTIME = "START_RUNTIME"
    STOP_RUNTIME = "STOP_RUNTIME"
    DISPATCH_AGENT = "DISPATCH_AGENT"
    RUN_WORKFLOW = "RUN_WORKFLOW"
    WRITE_MEMORY = "WRITE_MEMORY"
    MODIFY_POLICY = "MODIFY_POLICY"
    MUTATE_IDENTITY = "MUTATE_IDENTITY"
    TRIGGER_SANDBOX = "TRIGGER_SANDBOX"


class TerminalShellCapabilityStatus(str, Enum):
    READ_ONLY_ALLOWED = "READ_ONLY_ALLOWED"
    DISABLED = "DISABLED"
    FUTURE_GATED = "FUTURE_GATED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class TerminalShellParityDimension(str, Enum):
    SURFACE_LIST_VISIBLE = "SURFACE_LIST_VISIBLE"
    SURFACE_AVAILABILITY_VISIBLE = "SURFACE_AVAILABILITY_VISIBLE"
    TRUTH_LABELS_VISIBLE = "TRUTH_LABELS_VISIBLE"
    EVIDENCE_REFS_VISIBLE = "EVIDENCE_REFS_VISIBLE"
    LOCAL_RUN_MODES_VISIBLE = "LOCAL_RUN_MODES_VISIBLE"
    COMMAND_PREFLIGHT_STATUS_VISIBLE = "COMMAND_PREFLIGHT_STATUS_VISIBLE"
    NO_OVERCLAIM_BOUNDARIES_VISIBLE = "NO_OVERCLAIM_BOUNDARIES_VISIBLE"
    JSON_EXPORT_AVAILABLE = "JSON_EXPORT_AVAILABLE"
    EXECUTION_DISABLED = "EXECUTION_DISABLED"


class TerminalShellToolingDecision(str, Enum):
    PATH_A_EXTEND_EXISTING = "PATH_A_EXTEND_EXISTING"
    PATH_B_MINIMAL_NEW = "PATH_B_MINIMAL_NEW"
    PATH_C_CONTRACT_ONLY = "PATH_C_CONTRACT_ONLY"


_TERMINAL_VIEWS: tuple[str, ...] = (
    "shell status",
    "shell clients",
    "shell surfaces",
    "shell parity",
    "shell evidence",
    "shell run-modes",
    "shell export-json",
)

_READ_ONLY_CAPABILITIES: tuple[TerminalShellCapability, ...] = (
    TerminalShellCapability.VIEW_SHELL_STATUS,
    TerminalShellCapability.VIEW_CLIENTS,
    TerminalShellCapability.VIEW_SURFACES,
    TerminalShellCapability.VIEW_TRUTH_LABELS,
    TerminalShellCapability.VIEW_EVIDENCE_REFS,
    TerminalShellCapability.VIEW_LOCAL_RUN_MODES,
    TerminalShellCapability.VIEW_PARITY_MATRIX,
    TerminalShellCapability.EXPORT_JSON,
)

_DISABLED_EXECUTION_CAPABILITIES: tuple[TerminalShellCapability, ...] = (
    TerminalShellCapability.EXECUTE_COMMAND,
    TerminalShellCapability.APPROVE_ACTION,
    TerminalShellCapability.RUN_TOOL,
    TerminalShellCapability.START_RUNTIME,
    TerminalShellCapability.STOP_RUNTIME,
    TerminalShellCapability.DISPATCH_AGENT,
    TerminalShellCapability.RUN_WORKFLOW,
    TerminalShellCapability.WRITE_MEMORY,
    TerminalShellCapability.MODIFY_POLICY,
    TerminalShellCapability.MUTATE_IDENTITY,
    TerminalShellCapability.TRIGGER_SANDBOX,
)

_FUTURE_GATED_CAPABILITIES: tuple[TerminalShellCapability, ...] = ()

_NO_OVERCLAIM_BOUNDARIES: tuple[tuple[str, str, str], ...] = (
    ("NO_COMMAND_EXECUTION_CLAIM", "arbitrary command execution", "terminal is read-only"),
    ("NO_TOOL_EXECUTION_CLAIM", "tool execution", "terminal does not call Tool Bus"),
    ("NO_APPROVAL_EXECUTION_CLAIM", "approval execution", "terminal does not approve actions"),
    ("NO_RUNTIME_CONTROL_CLAIM", "runtime control", "terminal does not start or stop runtime"),
    ("NO_SANDBOX_CONTROL_CLAIM", "sandbox control", "terminal does not trigger sandbox"),
    ("NO_WORKFLOW_EXECUTION_CLAIM", "workflow execution", "terminal does not run workflows"),
    ("NO_AGENT_DISPATCH_CLAIM", "agent dispatch", "terminal does not dispatch agents"),
    ("NO_MEMORY_WRITE_CLAIM", "memory write", "terminal does not write memory"),
    ("NO_POLICY_MUTATION_CLAIM", "policy mutation", "terminal does not mutate policy"),
    ("NO_IDENTITY_MUTATION_CLAIM", "identity mutation", "terminal does not mutate identity"),
    ("NO_SHELL_LIVE_CLAIM", "Shell LIVE", "read-only terminal parity is not Shell LIVE"),
    (
        "NO_FULL_CLI_AUTOMATION_CLAIM",
        "full CLI automation",
        "P2.10-D exposes inspection commands only",
    ),
    ("NO_FULL_TUI_PRODUCT_CLAIM", "full TUI product", "TUI is contract-only text parity"),
    (
        "NO_P2_20_SEAL_CLAIM",
        "final P2 seal",
        "P2 is not sealed; P2.20 final exit seal remains NOT_DONE",
    ),
)

_PARITY_CLIENTS: tuple[ShellClientKind, ...] = (
    ShellClientKind.WEB,
    ShellClientKind.DESKTOP_TAURI,
    ShellClientKind.CLI,
    ShellClientKind.TUI,
    ShellClientKind.MOBILE_FOUNDATION,
)


@dataclass(frozen=True)
class P210DPrerequisiteGate(_CanonicalMixin):
    p210c_report_found: bool
    p210c_report_path: str
    p210c_report_indexed: bool
    p210c_proves_desktop_wrapper_done: bool
    p210c_points_to_p210d: bool
    p210e_not_started: bool
    gate_status: P210DPrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class TerminalShellCapabilityEntry(_CanonicalMixin):
    capability: TerminalShellCapability
    status: TerminalShellCapabilityStatus
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class TerminalShellNoOverclaimBoundary(_CanonicalMixin):
    boundary_id: str
    forbidden_claim: str
    reason: str
    active: bool
    evidence_refs: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class TerminalShellClientContract(_CanonicalMixin):
    client_kind: TerminalShellClientKind
    source_shell_state_ref: str
    source_web_read_model_ref: str
    source_desktop_contract_ref: str
    available_terminal_views: tuple[str, ...]
    read_only_capabilities: tuple[TerminalShellCapabilityEntry, ...]
    disabled_execution_capabilities: tuple[TerminalShellCapabilityEntry, ...]
    future_gated_capabilities: tuple[TerminalShellCapabilityEntry, ...]
    truth_labels: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    no_overclaim_boundaries: tuple[TerminalShellNoOverclaimBoundary, ...]
    next_pack: str
    contract_hash: str


@dataclass(frozen=True)
class TerminalShellSurfaceStatus(_CanonicalMixin):
    surface_id: str
    surface_label: str
    available: bool
    truth_label: ShellClientTruthLabel
    supported_clients: tuple[ShellClientKind, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    status_hash: str


@dataclass(frozen=True)
class TerminalShellParityEntry(_CanonicalMixin):
    client_kind: ShellClientKind
    dimension: TerminalShellParityDimension
    supported: bool
    truth_label: ShellClientTruthLabel
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class TerminalShellParityMatrix(_CanonicalMixin):
    clients: tuple[ShellClientKind, ...]
    dimensions: tuple[TerminalShellParityDimension, ...]
    entries: tuple[TerminalShellParityEntry, ...]
    terminal_parity_summary: str
    missing_parity: tuple[str, ...]
    execution_disabled_proof: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True)
class TerminalShellCommandSpec(_CanonicalMixin):
    command_name: str
    description: str
    read_only: bool
    output_format: str
    source_read_model: str
    allowed: bool
    disabled_reason: str
    evidence_refs: tuple[str, ...]
    spec_hash: str


@dataclass(frozen=True)
class TerminalShellReadModel(_CanonicalMixin):
    terminal_client_status: str
    available_clients: tuple[ShellClientKind, ...]
    available_surfaces: tuple[str, ...]
    surface_availability: tuple[TerminalShellSurfaceStatus, ...]
    truth_label_summary: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[str, ...]
    local_run_modes: tuple[TerminalShellRunMode, ...]
    parity_summary: str
    limitations: tuple[str, ...]
    p2_vslice_status: ShellClientTruthLabel
    json_export_available: bool
    execution_disabled: bool
    next_pack_pointer: str
    source_shell_state_hash: str
    source_web_read_model_hash: str
    source_desktop_read_model_hash: str
    read_model_hash: str


@dataclass(frozen=True)
class P210DSideEffectProof(_CanonicalMixin):
    p2_10_e_implemented: bool = False
    arbitrary_command_execution_implemented: bool = False
    tool_execution_implemented: bool = False
    approval_execution_implemented: bool = False
    runtime_start_stop_implemented: bool = False
    sandbox_control_implemented: bool = False
    workflow_execution_implemented: bool = False
    agent_dispatch_implemented: bool = False
    memory_write_implemented: bool = False
    policy_mutation_implemented: bool = False
    identity_mutation_implemented: bool = False
    command_preflight_behavior_changed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    policy_behavior_changed: bool = False
    identity_behavior_changed: bool = False
    sandbox_behavior_changed: bool = False
    shell_live_claimed: bool = False
    full_terminal_automation_claimed: bool = False
    full_tui_product_claimed: bool = False


@dataclass(frozen=True)
class P210DResult(_CanonicalMixin):
    covered_pack: str
    prerequisite_gate: P210DPrerequisiteGate
    terminal_tooling_decision: TerminalShellToolingDecision
    terminal_client_contract: TerminalShellClientContract
    terminal_read_model: TerminalShellReadModel
    terminal_parity_matrix: TerminalShellParityMatrix
    terminal_command_specs: tuple[TerminalShellCommandSpec, ...]
    operator_testable_terminal_path: bool
    no_scope_expansion_proof: P210DSideEffectProof
    next_pack: str
    p210e_not_started: bool
    result_hash: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_p2_10_d_prerequisite_gate(
    *,
    p210c_report_exists: bool | None = None,
    p210c_report_indexed: bool | None = None,
) -> P210DPrerequisiteGate:
    report_path = _repo_root() / P2_10_C_REPORT_PATH
    if p210c_report_exists is None:
        p210c_report_exists = report_path.is_file()
    if p210c_report_indexed is None:
        reports_index = (_repo_root() / "agent" / "REPORTS.md").read_text(encoding="utf-8")
        p210c_report_indexed = "P2_10_C_TAURI_DESKTOP_LOCAL_SHELL" in reports_index

    blockers: list[str] = []
    p210c_proves_done = False
    p210c_points_to_d = False

    if not p210c_report_exists:
        blockers.append("P2.10-C report missing")
    if not p210c_report_indexed:
        blockers.append("P2.10-C report not indexed")

    if p210c_report_exists:
        try:
            p210c = build_p2_10_c_desktop_shell_result()
            p210c_proves_done = (
                p210c.prerequisite_gate.gate_status is P210CPrerequisiteGateStatus.GATE_PASSED
                and p210c.desktop_wrapper_contract.client_kind is ShellClientKind.DESKTOP_TAURI
                and p210c.desktop_read_model.next_pack_pointer == "P2.10-D"
            )
            p210c_points_to_d = p210c.next_pack == "P2.10-D"
            if not p210c_proves_done:
                blockers.append("P2.10-C did not prove desktop wrapper/read model DONE")
            if not p210c_points_to_d:
                blockers.append("P2.10-C did not point next to P2.10-D")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.10-C desktop shell result failed: {exc}")

    if not P2_10_E_NOT_STARTED:
        blockers.append("P2.10-E unexpectedly started")

    status = (
        P210DPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
        if blockers
        else P210DPrerequisiteGateStatus.GATE_PASSED
    )
    payload = {
        "p210c_report_found": p210c_report_exists,
        "p210c_report_path": P2_10_C_REPORT_PATH,
        "p210c_report_indexed": p210c_report_indexed,
        "p210c_proves_desktop_wrapper_done": p210c_proves_done,
        "p210c_points_to_p210d": p210c_points_to_d,
        "p210e_not_started": P2_10_E_NOT_STARTED,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P210DPrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def _capability_entry(
    capability: TerminalShellCapability,
    status: TerminalShellCapabilityStatus,
    *,
    limitations: tuple[str, ...],
) -> TerminalShellCapabilityEntry:
    payload = {
        "capability": capability,
        "status": status,
        "evidence_refs": (
            P2_10_D_TERMINAL_MODULE_REF,
            P2_10_C_REPORT_PATH,
        ),
        "limitations": limitations,
    }
    return TerminalShellCapabilityEntry(**payload, entry_hash=_hash_payload(payload))


def build_terminal_shell_no_overclaim_boundaries() -> tuple[TerminalShellNoOverclaimBoundary, ...]:
    boundaries: list[TerminalShellNoOverclaimBoundary] = []
    for boundary_id, forbidden, reason in _NO_OVERCLAIM_BOUNDARIES:
        payload = {
            "boundary_id": boundary_id,
            "forbidden_claim": forbidden,
            "reason": reason,
            "active": True,
            "evidence_refs": (
                P2_10_D_TERMINAL_MODULE_REF,
                P2_10_C_REPORT_PATH,
                P2_VSLICE_A_REPORT_PATH,
            ),
        }
        boundaries.append(
            TerminalShellNoOverclaimBoundary(
                **payload,
                boundary_hash=_hash_payload(payload),
            )
        )
    return tuple(boundaries)


def _operator_next_pack(*, operator_canon: bool) -> str:
    return OPERATOR_CANON_NEXT_PACK if operator_canon else P2_10_D_NEXT_PACK


def _operator_limitations(*, operator_canon: bool) -> tuple[str, ...]:
    if operator_canon:
        return (
            "terminal Shell client is read-only",
            "commands render read model data only",
            "P2.VSLICE-A remains PREFLIGHT_ONLY",
            "command execution, tool execution, runtime control, and sandbox control are disabled",
            f"{OPERATOR_CANON_NEXT_PACK} is next and not implemented",
            f"{OPERATOR_CANON_LAST_COMPLETED_PACK} is complete per agent canon",
        )
    return (
        "terminal Shell client is read-only",
        "commands render read model data only",
        "P2.VSLICE-A remains PREFLIGHT_ONLY",
        "command execution, tool execution, runtime control, and sandbox control are disabled",
        "P2.10-E is next and not implemented",
    )


def build_terminal_shell_client_contract(
    client_kind: TerminalShellClientKind = TerminalShellClientKind.CLI,
    *,
    operator_canon: bool = True,
) -> TerminalShellClientContract:
    web_read_model = build_web_shell_read_model()
    desktop_read_model = build_desktop_shell_read_model()
    source_state = build_shell_client_state(ShellClientKind.CLI)
    truth_label = (
        ShellClientTruthLabel.READ_ONLY
        if client_kind is TerminalShellClientKind.CLI
        else ShellClientTruthLabel.CONTRACT_ONLY
    )

    read_only = tuple(
        _capability_entry(
            cap,
            TerminalShellCapabilityStatus.READ_ONLY_ALLOWED,
            limitations=("read-only terminal inspection capability",),
        )
        for cap in _READ_ONLY_CAPABILITIES
    )
    disabled = tuple(
        _capability_entry(
            cap,
            TerminalShellCapabilityStatus.DISABLED,
            limitations=("execution or mutation capability disabled in P2.10-D",),
        )
        for cap in _DISABLED_EXECUTION_CAPABILITIES
    )
    future_gated = tuple(
        _capability_entry(
            cap,
            TerminalShellCapabilityStatus.FUTURE_GATED,
            limitations=("future pack required; not enabled in P2.10-D",),
        )
        for cap in _FUTURE_GATED_CAPABILITIES
    )
    no_overclaim = build_terminal_shell_no_overclaim_boundaries()

    payload = {
        "client_kind": client_kind,
        "source_shell_state_ref": (
            "src/agentic_runtime/aurel_shell/multi_client_foundation.py:ShellClientState"
        ),
        "source_web_read_model_ref": P2_10_B_FIXTURE_REL_PATH,
        "source_desktop_contract_ref": P2_10_C_FIXTURE_REL_PATH,
        "available_terminal_views": _TERMINAL_VIEWS,
        "read_only_capabilities": read_only,
        "disabled_execution_capabilities": disabled,
        "future_gated_capabilities": future_gated,
        "truth_labels": (
            truth_label,
            ShellClientTruthLabel.PREFLIGHT_ONLY,
            ShellClientTruthLabel.CONTRACT_ONLY,
            ShellClientTruthLabel.NOT_STARTED,
        ),
        "evidence_refs": tuple(
            dict.fromkeys(
                source_state.evidence_refs
                + tuple(ref.path for ref in web_read_model.evidence_refs)
                + desktop_read_model.evidence_refs
                + (
                    P2_10_A_REPORT_PATH,
                    P2_10_B_REPORT_PATH,
                    P2_10_C_REPORT_PATH,
                    P2_10_D_TERMINAL_MODULE_REF,
                    P2_10_D_CLI_MODULE_REF,
                    P2_VSLICE_A_REPORT_PATH,
                )
            )
        ),
        "limitations": (
            "terminal client consumes P2.10-A/B/C Shell truth",
            "read-only visibility does not equal execution",
            "terminal JSON export is not a live backend",
            "TUI is contract-only text parity, not a full TUI product",
        ),
        "no_overclaim_boundaries": no_overclaim,
        "next_pack": _operator_next_pack(operator_canon=operator_canon),
    }
    # Keep source model hashes in local variables so they are built and validated.
    _ = (web_read_model.read_model_hash, desktop_read_model.read_model_hash)
    contract = TerminalShellClientContract(**payload, contract_hash=_hash_payload(payload))
    assert_terminal_contract_read_only(contract)
    return contract


def _build_terminal_surface_statuses() -> tuple[TerminalShellSurfaceStatus, ...]:
    cli_state = build_shell_client_state(ShellClientKind.CLI)
    statuses: list[TerminalShellSurfaceStatus] = []
    for surface in cli_state.surface_availability:
        payload = {
            "surface_id": surface.surface_id,
            "surface_label": surface.surface_label,
            "available": surface.available,
            "truth_label": surface.truth_label,
            "supported_clients": surface.supported_clients,
            "evidence_refs": surface.evidence_refs,
            "limitations": surface.limitations
            + ("terminal presents surface truth as text/JSON only",),
        }
        statuses.append(
            TerminalShellSurfaceStatus(**payload, status_hash=_hash_payload(payload))
        )
    return tuple(statuses)


def _terminal_run_modes_for_cli_path() -> tuple[TerminalShellRunMode, ...]:
    return (
        TerminalShellRunMode.CLI_READ_ONLY,
        TerminalShellRunMode.TUI_CONTRACT_ONLY,
        TerminalShellRunMode.TERMINAL_JSON_EXPORT,
    )


def build_terminal_shell_parity_matrix() -> TerminalShellParityMatrix:
    entries: list[TerminalShellParityEntry] = []
    missing: list[str] = []
    for client_kind in _PARITY_CLIENTS:
        for dimension in TerminalShellParityDimension:
            supported = True
            truth_label = ShellClientTruthLabel.CONTRACT_ONLY
            limitations = (
                "parity means same truth, different presentation",
                "execution disabled remains visible",
            )
            if client_kind is ShellClientKind.CLI:
                truth_label = ShellClientTruthLabel.READ_ONLY
            elif client_kind is ShellClientKind.TUI:
                truth_label = ShellClientTruthLabel.CONTRACT_ONLY
                if dimension is TerminalShellParityDimension.JSON_EXPORT_AVAILABLE:
                    supported = False
                    truth_label = ShellClientTruthLabel.UNAVAILABLE
                    limitations = ("TUI is contract-only; JSON export is provided by CLI",)
            elif client_kind is ShellClientKind.MOBILE_FOUNDATION:
                if dimension is TerminalShellParityDimension.JSON_EXPORT_AVAILABLE:
                    supported = False
                    truth_label = ShellClientTruthLabel.NOT_STARTED
                    limitations = ("mobile foundation is not a runnable client",)
            if dimension is TerminalShellParityDimension.COMMAND_PREFLIGHT_STATUS_VISIBLE:
                truth_label = ShellClientTruthLabel.PREFLIGHT_ONLY
            if dimension is TerminalShellParityDimension.EXECUTION_DISABLED:
                supported = True
                truth_label = ShellClientTruthLabel.READ_ONLY
            if not supported:
                missing.append(f"{client_kind.value}:{dimension.value}")
            payload = {
                "client_kind": client_kind,
                "dimension": dimension,
                "supported": supported,
                "truth_label": truth_label,
                "evidence_refs": (
                    P2_10_A_REPORT_PATH,
                    P2_10_B_REPORT_PATH,
                    P2_10_C_REPORT_PATH,
                    P2_10_D_TERMINAL_MODULE_REF,
                ),
                "limitations": limitations,
            }
            entries.append(
                TerminalShellParityEntry(**payload, entry_hash=_hash_payload(payload))
            )

    payload = {
        "clients": _PARITY_CLIENTS,
        "dimensions": tuple(TerminalShellParityDimension),
        "entries": tuple(entries),
        "terminal_parity_summary": (
            "CLI/TUI parity means terminal can inspect the same Shell truth; "
            "it does not enable command execution or Shell LIVE."
        ),
        "missing_parity": tuple(missing),
        "execution_disabled_proof": tuple(cap.value for cap in _DISABLED_EXECUTION_CAPABILITIES),
        "evidence_refs": (
            P2_10_A_REPORT_PATH,
            P2_10_B_REPORT_PATH,
            P2_10_C_REPORT_PATH,
            P2_10_D_TERMINAL_MODULE_REF,
        ),
    }
    matrix = TerminalShellParityMatrix(**payload, matrix_hash=_hash_payload(payload))
    assert_terminal_parity_execution_disabled(matrix)
    return matrix


def build_terminal_shell_read_model(*, operator_canon: bool = True) -> TerminalShellReadModel:
    cli_state = build_shell_client_state(ShellClientKind.CLI)
    web_read_model = build_web_shell_read_model()
    desktop_read_model = build_desktop_shell_read_model()
    parity_matrix = build_terminal_shell_parity_matrix()
    run_modes = _terminal_run_modes_for_cli_path()
    surface_statuses = _build_terminal_surface_statuses()
    p210a_run_modes = build_shell_client_local_run_modes()

    operator_evidence = (P2_11_C_REPORT_PATH,) if operator_canon else ()
    evidence_refs = tuple(
        dict.fromkeys(
            cli_state.evidence_refs
            + web_read_model.client_status.evidence_refs
            + desktop_read_model.evidence_refs
            + tuple(entry.evidence_refs[0] for entry in p210a_run_modes)
            + (
                P2_10_A_REPORT_PATH,
                P2_10_B_REPORT_PATH,
                P2_10_C_REPORT_PATH,
                P2_10_D_TERMINAL_MODULE_REF,
                P2_10_D_CLI_MODULE_REF,
                P2_VSLICE_A_REPORT_PATH,
            )
            + operator_evidence
        )
    )
    payload = {
        "terminal_client_status": "READ_ONLY",
        "available_clients": _PARITY_CLIENTS,
        "available_surfaces": cli_state.available_surfaces,
        "surface_availability": surface_statuses,
        "truth_label_summary": (
            ShellClientTruthLabel.READ_ONLY,
            ShellClientTruthLabel.CONTRACT_ONLY,
            ShellClientTruthLabel.PREFLIGHT_ONLY,
            ShellClientTruthLabel.NOT_STARTED,
            ShellClientTruthLabel.UNAVAILABLE,
        ),
        "evidence_refs": evidence_refs,
        "local_run_modes": run_modes,
        "parity_summary": parity_matrix.terminal_parity_summary,
        "limitations": _operator_limitations(operator_canon=operator_canon),
        "p2_vslice_status": ShellClientTruthLabel.PREFLIGHT_ONLY,
        "json_export_available": True,
        "execution_disabled": True,
        "next_pack_pointer": _operator_next_pack(operator_canon=operator_canon),
        "source_shell_state_hash": cli_state.state_hash,
        "source_web_read_model_hash": web_read_model.read_model_hash,
        "source_desktop_read_model_hash": desktop_read_model.read_model_hash,
    }
    read_model = TerminalShellReadModel(**payload, read_model_hash=_hash_payload(payload))
    assert_terminal_read_model_derives_from_p210a_b_c(read_model)
    assert_terminal_read_model_no_execution(read_model)
    return read_model


def build_terminal_shell_command_specs() -> tuple[TerminalShellCommandSpec, ...]:
    specs = (
        ("shell status", "show terminal Shell status", "text/json"),
        ("shell clients", "list Shell clients", "text/json"),
        ("shell surfaces", "list Shell surfaces", "text/json"),
        ("shell parity", "print terminal parity matrix", "text/json"),
        ("shell evidence", "list evidence refs", "text/json"),
        ("shell run-modes", "list local run modes", "text/json"),
        ("shell export-json", "export deterministic terminal read model JSON", "json"),
    )
    command_specs: list[TerminalShellCommandSpec] = []
    for name, description, output_format in specs:
        payload = {
            "command_name": name,
            "description": description,
            "read_only": True,
            "output_format": output_format,
            "source_read_model": P2_10_D_TERMINAL_MODULE_REF,
            "allowed": True,
            "disabled_reason": "",
            "evidence_refs": (P2_10_D_CLI_MODULE_REF, P2_10_D_TERMINAL_MODULE_REF),
        }
        command_specs.append(TerminalShellCommandSpec(**payload, spec_hash=_hash_payload(payload)))
    return tuple(command_specs)


def build_p2_10_d_terminal_shell_result(
    *,
    skip_prerequisite_gate: bool = False,
) -> P210DResult:
    gate = build_p2_10_d_prerequisite_gate()
    if not skip_prerequisite_gate:
        assert_p2_10_d_prerequisite_gate_passed(gate)

    contract = build_terminal_shell_client_contract(operator_canon=False)
    read_model = build_terminal_shell_read_model(operator_canon=False)
    parity_matrix = build_terminal_shell_parity_matrix()
    command_specs = build_terminal_shell_command_specs()
    proof = P210DSideEffectProof()
    payload = {
        "covered_pack": P2_10_D_PACK_ID,
        "prerequisite_gate": gate,
        "terminal_tooling_decision": TerminalShellToolingDecision.PATH_A_EXTEND_EXISTING,
        "terminal_client_contract": contract,
        "terminal_read_model": read_model,
        "terminal_parity_matrix": parity_matrix,
        "terminal_command_specs": command_specs,
        "operator_testable_terminal_path": True,
        "no_scope_expansion_proof": proof,
        "next_pack": P2_10_D_NEXT_PACK,
        "p210e_not_started": P2_10_E_NOT_STARTED,
    }
    result = P210DResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_10_d_no_scope_expansion(result)
    return result


def serialize_terminal_shell_read_model(read_model: TerminalShellReadModel) -> str:
    return to_canonical_json(read_model.to_canonical_dict())


def serialize_p2_10_d_result(result: P210DResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def terminal_shell_read_model_to_json_safe_dict(
    read_model: TerminalShellReadModel | None = None,
) -> dict[str, object]:
    if read_model is None:
        read_model = build_terminal_shell_read_model()
    return read_model.to_canonical_dict()


def assert_p2_10_d_prerequisite_gate_passed(gate: P210DPrerequisiteGate) -> None:
    if gate.gate_status is not P210DPrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.10-D cannot proceed unless P2.10-C report exists, is indexed, "
            "proves desktop wrapper/read model DONE, points to P2.10-D, and P2.10-E is not started",
            field="gate_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_terminal_contract_read_only(contract: TerminalShellClientContract) -> None:
    for entry in contract.read_only_capabilities:
        if entry.status is not TerminalShellCapabilityStatus.READ_ONLY_ALLOWED:
            _reject(
                f"{entry.capability.value} must be read-only allowed",
                field="read_only_capabilities",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
    for entry in contract.disabled_execution_capabilities:
        if entry.status is not TerminalShellCapabilityStatus.DISABLED:
            _reject(
                f"{entry.capability.value} must be disabled",
                field="disabled_execution_capabilities",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
    if ShellClientTruthLabel.LIVE in contract.truth_labels:
        _reject(
            "terminal contract must not include LIVE truth label",
            field="truth_labels",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_terminal_read_model_derives_from_p210a_b_c(
    read_model: TerminalShellReadModel,
) -> None:
    cli_state = build_shell_client_state(ShellClientKind.CLI)
    web_read_model = build_web_shell_read_model()
    desktop_read_model = build_desktop_shell_read_model()
    if read_model.source_shell_state_hash != cli_state.state_hash:
        _reject(
            "terminal read model must derive from current CLI ShellClientState",
            field="source_shell_state_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if read_model.source_web_read_model_hash != web_read_model.read_model_hash:
        _reject(
            "terminal read model must preserve current WebShellReadModel hash",
            field="source_web_read_model_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if read_model.source_desktop_read_model_hash != desktop_read_model.read_model_hash:
        _reject(
            "terminal read model must preserve current DesktopShellReadModel hash",
            field="source_desktop_read_model_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if set(read_model.available_surfaces) != set(cli_state.available_surfaces):
        _reject(
            "terminal surfaces must match CLI ShellClientState surfaces",
            field="available_surfaces",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_terminal_read_model_no_execution(read_model: TerminalShellReadModel) -> None:
    if not read_model.execution_disabled:
        _reject(
            "terminal read model must keep execution disabled",
            field="execution_disabled",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if read_model.p2_vslice_status is not ShellClientTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A must remain PREFLIGHT_ONLY in P2.10-D",
            field="p2_vslice_status",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if ShellClientTruthLabel.LIVE in read_model.truth_label_summary:
        _reject(
            "terminal read model must not claim LIVE",
            field="truth_label_summary",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_terminal_parity_execution_disabled(matrix: TerminalShellParityMatrix) -> None:
    required_disabled = {cap.value for cap in _DISABLED_EXECUTION_CAPABILITIES}
    if set(matrix.execution_disabled_proof) != required_disabled:
        _reject(
            "terminal parity matrix must prove every execution capability disabled",
            field="execution_disabled_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    for entry in matrix.entries:
        if (
            entry.dimension is TerminalShellParityDimension.EXECUTION_DISABLED
            and not entry.supported
        ):
            _reject(
                f"{entry.client_kind.value} must expose execution-disabled proof",
                field="entries",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_p2_10_d_no_scope_expansion(result: P210DResult) -> None:
    proof = result.no_scope_expansion_proof
    if any(
        (
            proof.p2_10_e_implemented,
            proof.arbitrary_command_execution_implemented,
            proof.tool_execution_implemented,
            proof.approval_execution_implemented,
            proof.runtime_start_stop_implemented,
            proof.sandbox_control_implemented,
            proof.workflow_execution_implemented,
            proof.agent_dispatch_implemented,
            proof.memory_write_implemented,
            proof.policy_mutation_implemented,
            proof.identity_mutation_implemented,
            proof.command_preflight_behavior_changed,
            proof.p2_vslice_a_behavior_changed,
            proof.policy_behavior_changed,
            proof.identity_behavior_changed,
            proof.sandbox_behavior_changed,
            proof.shell_live_claimed,
            proof.full_terminal_automation_claimed,
            proof.full_tui_product_claimed,
        )
    ):
        _reject(
            "P2.10-D must not expand into execution, mutation, Shell LIVE, or P2.10-E",
            field="no_scope_expansion_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.next_pack != P2_10_D_NEXT_PACK or not result.p210e_not_started:
        _reject(
            "P2.10-D must point next to P2.10-E while keeping P2.10-E not started",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
