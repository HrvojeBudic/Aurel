"""P2.11-A surface permission matrix foundation.

Defines a deterministic client x surface x action permission matrix over the
P2.10 multi-client Shell baseline. This is Shell-level pre-execution authority
modeling only. It does not execute commands, enforce full policy, replace
Custos, control runtime/sandbox state, write memory, mutate policy, mutate
identity, claim Shell LIVE, or claim product readiness.
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
from .multi_client_demo_seal import (
    P2_10_A_REPORT_PATH,
    P2_10_B_REPORT_PATH,
    P2_10_C_REPORT_PATH,
    P2_10_D_REPORT_PATH,
    P2_10_E_PACK_ID,
    P2_10_E_REPORT_PATH,
    P2_10_E_TEST_DEMO_REF,
    P2_10_E_TEST_HANDOFF_REF,
    P2_10_E_TEST_NO_OVERCLAIM_REF,
    P2_10_E_TEST_TRUTH_REF,
    P210EPrerequisiteGateStatus,
    build_p2_10_e_multi_client_demo_seal_result,
    build_p2_10_e_prerequisite_gate,
)
from .multi_client_foundation import ShellClientKind, ShellClientTruthLabel
from .shell_exit_readiness import P2_VSLICE_A_REPORT_PATH
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    SURFACE_KIND_DISPLAY_NAMES,
    AurelSurfaceKind,
    build_default_surface_registry,
)

P2_11_A_PACK_ID = "P2.11-A"
P2_11_A_SECTION_ID = "P2.11"
P2_11_A_TITLE = "Surface Permission Matrix Foundation / Client-Surface Authority Baseline"
P2_11_A_REPORT_FILENAME = "P2_11_A_SURFACE_PERMISSION_MATRIX_FOUNDATION.md"
P2_11_A_REPORT_PATH = f"agent/reports/{P2_11_A_REPORT_FILENAME}"
P2_11_A_RESULT_VERSION = "p2_11_a_surface_permission_matrix_result.v1"

P2_11_B_NEXT_PACK = "P2.11-B"
P2_11_B_NEXT_TITLE = "Surface Permission Projection / Matrix Read Model"
P2_11_B_NOT_DONE = True
P2_12_NOT_STARTED = True

P2_11_A_TEST_MATRIX_REF = "tests/test_p211a_surface_permission_matrix.py"
P2_11_A_TEST_BASELINE_REF = "tests/test_p211a_client_surface_authority_baseline.py"
P2_11_A_TEST_NO_EXECUTION_REF = "tests/test_p211a_surface_permission_no_execution.py"
P2_11_A_TEST_HANDOFF_REF = "tests/test_p211a_p211b_handoff.py"

_P2_10_CLIENTS: tuple[ShellClientKind, ...] = (
    ShellClientKind.WEB,
    ShellClientKind.DESKTOP_TAURI,
    ShellClientKind.CLI,
    ShellClientKind.TUI,
    ShellClientKind.MOBILE_FOUNDATION,
)

_SENSITIVE_SURFACES: tuple[str, ...] = ("system", "settings", "ide")


class P211APrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


class SurfacePermissionAction(str, Enum):
    SEE_SURFACE = "SEE_SURFACE"
    OPEN_SURFACE = "OPEN_SURFACE"
    FOCUS_SURFACE = "FOCUS_SURFACE"
    READ_SURFACE_STATE = "READ_SURFACE_STATE"
    INSPECT_SURFACE_EVIDENCE = "INSPECT_SURFACE_EVIDENCE"
    VIEW_SURFACE_COMMANDS = "VIEW_SURFACE_COMMANDS"
    REQUEST_COMMAND_PREFLIGHT = "REQUEST_COMMAND_PREFLIGHT"
    EXPORT_SURFACE_READ_MODEL = "EXPORT_SURFACE_READ_MODEL"
    VIEW_LIMITATIONS = "VIEW_LIMITATIONS"
    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    APPROVE_ACTION = "APPROVE_ACTION"
    RUN_TOOL = "RUN_TOOL"
    START_RUNTIME = "START_RUNTIME"
    STOP_RUNTIME = "STOP_RUNTIME"
    TRIGGER_SANDBOX = "TRIGGER_SANDBOX"
    WRITE_MEMORY = "WRITE_MEMORY"
    MODIFY_POLICY = "MODIFY_POLICY"
    MUTATE_IDENTITY = "MUTATE_IDENTITY"
    DISPATCH_AGENT = "DISPATCH_AGENT"
    RUN_WORKFLOW = "RUN_WORKFLOW"


class SurfacePermissionLevel(str, Enum):
    ALLOWED = "ALLOWED"
    READ_ONLY = "READ_ONLY"
    PREFLIGHT_ONLY = "PREFLIGHT_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    FUTURE_GATED = "FUTURE_GATED"
    UNAVAILABLE = "UNAVAILABLE"
    DENIED = "DENIED"
    ERROR = "ERROR"


class SurfacePermissionReason(str, Enum):
    P2_10_CLIENT_BASELINE = "P2_10_CLIENT_BASELINE"
    SURFACE_VISIBLE_IN_SHELL = "SURFACE_VISIBLE_IN_SHELL"
    CLIENT_READ_ONLY = "CLIENT_READ_ONLY"
    CLIENT_CONTRACT_ONLY = "CLIENT_CONTRACT_ONLY"
    CLIENT_UNAVAILABLE = "CLIENT_UNAVAILABLE"
    SURFACE_FUTURE_GATED = "SURFACE_FUTURE_GATED"
    SURFACE_SYSTEM_SENSITIVE = "SURFACE_SYSTEM_SENSITIVE"
    PREFLIGHT_AVAILABLE_ONLY = "PREFLIGHT_AVAILABLE_ONLY"
    EXECUTION_NOT_IMPLEMENTED = "EXECUTION_NOT_IMPLEMENTED"
    APPROVAL_EXECUTION_NOT_IMPLEMENTED = "APPROVAL_EXECUTION_NOT_IMPLEMENTED"
    TOOL_EXECUTION_NOT_IMPLEMENTED = "TOOL_EXECUTION_NOT_IMPLEMENTED"
    RUNTIME_CONTROL_NOT_IMPLEMENTED = "RUNTIME_CONTROL_NOT_IMPLEMENTED"
    SANDBOX_CONTROL_NOT_IMPLEMENTED = "SANDBOX_CONTROL_NOT_IMPLEMENTED"
    MEMORY_WRITE_NOT_IMPLEMENTED = "MEMORY_WRITE_NOT_IMPLEMENTED"
    POLICY_MUTATION_NOT_IMPLEMENTED = "POLICY_MUTATION_NOT_IMPLEMENTED"
    IDENTITY_MUTATION_NOT_IMPLEMENTED = "IDENTITY_MUTATION_NOT_IMPLEMENTED"
    MOBILE_FOUNDATION_ONLY = "MOBILE_FOUNDATION_ONLY"
    NO_EVIDENCE = "NO_EVIDENCE"
    ERROR = "ERROR"


class SurfacePermissionNoOverclaimBoundary(str, Enum):
    NO_COMMAND_EXECUTION_CLAIM = "NO_COMMAND_EXECUTION_CLAIM"
    NO_TOOL_EXECUTION_CLAIM = "NO_TOOL_EXECUTION_CLAIM"
    NO_APPROVAL_EXECUTION_CLAIM = "NO_APPROVAL_EXECUTION_CLAIM"
    NO_RUNTIME_CONTROL_CLAIM = "NO_RUNTIME_CONTROL_CLAIM"
    NO_SANDBOX_CONTROL_CLAIM = "NO_SANDBOX_CONTROL_CLAIM"
    NO_MEMORY_WRITE_CLAIM = "NO_MEMORY_WRITE_CLAIM"
    NO_POLICY_MUTATION_CLAIM = "NO_POLICY_MUTATION_CLAIM"
    NO_IDENTITY_MUTATION_CLAIM = "NO_IDENTITY_MUTATION_CLAIM"
    NO_FULL_POLICY_RUNTIME_CLAIM = "NO_FULL_POLICY_RUNTIME_CLAIM"
    NO_CUSTOS_ENFORCEMENT_CLAIM = "NO_CUSTOS_ENFORCEMENT_CLAIM"
    NO_SURFACE_TRUTH_LABEL_DISCIPLINE_CLAIM = "NO_SURFACE_TRUTH_LABEL_DISCIPLINE_CLAIM"
    NO_CLIENT_DEGRADATION_RULES_CLAIM = "NO_CLIENT_DEGRADATION_RULES_CLAIM"
    NO_SHELL_LIVE_CLAIM = "NO_SHELL_LIVE_CLAIM"
    NO_PRODUCT_READINESS_CLAIM = "NO_PRODUCT_READINESS_CLAIM"
    NO_P2_11_COMPLETE_CLAIM = "NO_P2_11_COMPLETE_CLAIM"
    NO_P2_12_CLAIM = "NO_P2_12_CLAIM"
    NO_P2_FINAL_SEAL_CLAIM = "NO_P2_FINAL_SEAL_CLAIM"
    NO_P3_HANDOFF_CLAIM = "NO_P3_HANDOFF_CLAIM"


SAFE_PRE_EXECUTION_ACTIONS: tuple[SurfacePermissionAction, ...] = (
    SurfacePermissionAction.SEE_SURFACE,
    SurfacePermissionAction.OPEN_SURFACE,
    SurfacePermissionAction.FOCUS_SURFACE,
    SurfacePermissionAction.READ_SURFACE_STATE,
    SurfacePermissionAction.INSPECT_SURFACE_EVIDENCE,
    SurfacePermissionAction.VIEW_SURFACE_COMMANDS,
    SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
    SurfacePermissionAction.EXPORT_SURFACE_READ_MODEL,
    SurfacePermissionAction.VIEW_LIMITATIONS,
)

DISABLED_EXECUTION_ACTIONS: tuple[SurfacePermissionAction, ...] = (
    SurfacePermissionAction.EXECUTE_COMMAND,
    SurfacePermissionAction.APPROVE_ACTION,
    SurfacePermissionAction.RUN_TOOL,
    SurfacePermissionAction.START_RUNTIME,
    SurfacePermissionAction.STOP_RUNTIME,
    SurfacePermissionAction.TRIGGER_SANDBOX,
    SurfacePermissionAction.WRITE_MEMORY,
    SurfacePermissionAction.MODIFY_POLICY,
    SurfacePermissionAction.MUTATE_IDENTITY,
    SurfacePermissionAction.DISPATCH_AGENT,
    SurfacePermissionAction.RUN_WORKFLOW,
)

_EXECUTION_ACTION_REASONS: dict[SurfacePermissionAction, SurfacePermissionReason] = {
    SurfacePermissionAction.EXECUTE_COMMAND: SurfacePermissionReason.EXECUTION_NOT_IMPLEMENTED,
    SurfacePermissionAction.APPROVE_ACTION: SurfacePermissionReason.APPROVAL_EXECUTION_NOT_IMPLEMENTED,
    SurfacePermissionAction.RUN_TOOL: SurfacePermissionReason.TOOL_EXECUTION_NOT_IMPLEMENTED,
    SurfacePermissionAction.START_RUNTIME: SurfacePermissionReason.RUNTIME_CONTROL_NOT_IMPLEMENTED,
    SurfacePermissionAction.STOP_RUNTIME: SurfacePermissionReason.RUNTIME_CONTROL_NOT_IMPLEMENTED,
    SurfacePermissionAction.TRIGGER_SANDBOX: SurfacePermissionReason.SANDBOX_CONTROL_NOT_IMPLEMENTED,
    SurfacePermissionAction.WRITE_MEMORY: SurfacePermissionReason.MEMORY_WRITE_NOT_IMPLEMENTED,
    SurfacePermissionAction.MODIFY_POLICY: SurfacePermissionReason.POLICY_MUTATION_NOT_IMPLEMENTED,
    SurfacePermissionAction.MUTATE_IDENTITY: SurfacePermissionReason.IDENTITY_MUTATION_NOT_IMPLEMENTED,
    SurfacePermissionAction.DISPATCH_AGENT: SurfacePermissionReason.EXECUTION_NOT_IMPLEMENTED,
    SurfacePermissionAction.RUN_WORKFLOW: SurfacePermissionReason.EXECUTION_NOT_IMPLEMENTED,
}

_EXECUTION_ACTION_LIMITATIONS: dict[SurfacePermissionAction, str] = {
    SurfacePermissionAction.EXECUTE_COMMAND: "command execution is not implemented in P2.11-A",
    SurfacePermissionAction.APPROVE_ACTION: "approval execution is not implemented in P2.11-A",
    SurfacePermissionAction.RUN_TOOL: "tool execution is not implemented in P2.11-A",
    SurfacePermissionAction.START_RUNTIME: "runtime start is not implemented in P2.11-A",
    SurfacePermissionAction.STOP_RUNTIME: "runtime stop is not implemented in P2.11-A",
    SurfacePermissionAction.TRIGGER_SANDBOX: "sandbox control is not implemented in P2.11-A",
    SurfacePermissionAction.WRITE_MEMORY: "memory writes are not implemented in P2.11-A",
    SurfacePermissionAction.MODIFY_POLICY: "policy mutation is not implemented in P2.11-A",
    SurfacePermissionAction.MUTATE_IDENTITY: "identity mutation is not implemented in P2.11-A",
    SurfacePermissionAction.DISPATCH_AGENT: "agent dispatch is not implemented in P2.11-A",
    SurfacePermissionAction.RUN_WORKFLOW: "workflow execution is not implemented in P2.11-A",
}

_BASE_EVIDENCE_REFS: tuple[str, ...] = (
    P2_10_A_REPORT_PATH,
    P2_10_B_REPORT_PATH,
    P2_10_C_REPORT_PATH,
    P2_10_D_REPORT_PATH,
    P2_10_E_REPORT_PATH,
    P2_VSLICE_A_REPORT_PATH,
)


@dataclass(frozen=True)
class P211APrerequisiteGate(_CanonicalMixin):
    p210e_report_found: bool
    p210e_report_path: str
    p210e_report_indexed: bool
    p210e_proves_p210_multi_client_sealed: bool
    p210e_points_to_p211: bool
    p212_not_started: bool
    gate_status: P211APrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfacePermissionEvidenceRef(_CanonicalMixin):
    source_pack: str
    source_report: str
    source_commit: str
    source_test: str
    source_object: str
    notes: str
    ref_hash: str


@dataclass(frozen=True)
class SurfacePermissionEntry(_CanonicalMixin):
    client_kind: ShellClientKind
    surface_id: str
    permission_action: SurfacePermissionAction
    permission_level: SurfacePermissionLevel
    reason: SurfacePermissionReason
    evidence_refs: tuple[SurfacePermissionEvidenceRef, ...]
    limitations: tuple[str, ...]
    source_pack_refs: tuple[str, ...]
    no_overclaim_boundaries: tuple[SurfacePermissionNoOverclaimBoundary, ...]
    entry_hash: str


@dataclass(frozen=True)
class ClientSurfaceAuthorityBaseline(_CanonicalMixin):
    clients: tuple[ShellClientKind, ...]
    surfaces: tuple[str, ...]
    permission_actions: tuple[SurfacePermissionAction, ...]
    sensitive_surfaces: tuple[str, ...]
    default_rules: tuple[str, ...]
    client_specific_rules: tuple[str, ...]
    surface_specific_rules: tuple[str, ...]
    evidence_refs: tuple[SurfacePermissionEvidenceRef, ...]
    baseline_hash: str


@dataclass(frozen=True)
class SurfacePermissionMatrixSummary(_CanonicalMixin):
    total_entries: int
    allowed_count: int
    read_only_count: int
    preflight_only_count: int
    contract_only_count: int
    future_gated_count: int
    unavailable_count: int
    denied_count: int
    error_count: int
    sensitive_surface_summary: tuple[str, ...]
    execution_disabled_summary: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class SurfacePermissionMatrix(_CanonicalMixin):
    entries: tuple[SurfacePermissionEntry, ...]
    clients: tuple[ShellClientKind, ...]
    surfaces: tuple[str, ...]
    actions: tuple[SurfacePermissionAction, ...]
    summary: SurfacePermissionMatrixSummary
    missing_entries: tuple[str, ...]
    inconsistencies: tuple[str, ...]
    evidence_refs: tuple[SurfacePermissionEvidenceRef, ...]
    matrix_hash: str


@dataclass(frozen=True)
class P211AHandoff(_CanonicalMixin):
    next_pack: str
    next_title: str
    handoff_status: str
    permission_baseline_summary: tuple[str, ...]
    read_model_projection_needs: tuple[str, ...]
    operator_inspection_needs: tuple[str, ...]
    remaining_risks: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class P211ASideEffectProof(_CanonicalMixin):
    p2_11_b_implemented: bool = False
    p2_11_claimed_complete: bool = False
    p2_12_plus_implemented: bool = False
    p2_final_seal_claimed: bool = False
    p3_handoff_claimed: bool = False
    command_execution_implemented: bool = False
    tool_execution_implemented: bool = False
    approval_execution_implemented: bool = False
    runtime_control_implemented: bool = False
    sandbox_control_implemented: bool = False
    workflow_execution_implemented: bool = False
    agent_dispatch_implemented: bool = False
    memory_write_implemented: bool = False
    policy_mutation_implemented: bool = False
    identity_mutation_implemented: bool = False
    full_policy_runtime_implemented: bool = False
    custos_enforcement_implemented: bool = False
    p2_vslice_a_behavior_changed: bool = False
    shell_live_claimed: bool = False
    product_readiness_claimed: bool = False


@dataclass(frozen=True)
class P211AResult(_CanonicalMixin):
    covered_pack: str
    prerequisite_gate: P211APrerequisiteGate
    authority_baseline: ClientSurfaceAuthorityBaseline
    permission_matrix: SurfacePermissionMatrix
    matrix_summary: SurfacePermissionMatrixSummary
    no_overclaim_boundaries: tuple[SurfacePermissionNoOverclaimBoundary, ...]
    handoff: P211AHandoff
    side_effect_proof: P211ASideEffectProof
    p211b_not_done: bool
    p212_not_started: bool
    result_hash: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _report_index_contains(report_filename: str) -> bool:
    reports_index = (_repo_root() / "agent" / "REPORTS.md").read_text(
        encoding="utf-8"
    )
    return report_filename in reports_index


def _p212_not_started() -> bool:
    root = _repo_root()
    report_started = any((root / "agent" / "reports").glob("P2_12*"))
    source_started = any((root / "src" / "agentic_runtime" / "aurel_shell").glob("*p212*"))
    test_started = any((root / "tests").glob("test_p212*"))
    return not report_started and not source_started and not test_started


def build_p2_11_a_prerequisite_gate(
    *,
    p210e_report_exists: bool | None = None,
    p210e_report_indexed: bool | None = None,
    p212_not_started: bool | None = None,
) -> P211APrerequisiteGate:
    report_path = _repo_root() / P2_10_E_REPORT_PATH
    if p210e_report_exists is None:
        p210e_report_exists = report_path.is_file()
    if p210e_report_indexed is None:
        p210e_report_indexed = _report_index_contains(
            "P2_10_E_MULTI_CLIENT_OPERATOR_DEMO_SEAL"
        )
    if p212_not_started is None:
        p212_not_started = _p212_not_started() and P2_12_NOT_STARTED

    blockers: list[str] = []
    p210e_proves_sealed = False
    p210e_points_to_p211 = False

    if not p210e_report_exists:
        blockers.append("P2.10-E report missing")
    if not p210e_report_indexed:
        blockers.append("P2.10-E report not indexed")
    if not p212_not_started:
        blockers.append("P2.12+ appears started")

    if p210e_report_exists:
        try:
            p210e_gate = build_p2_10_e_prerequisite_gate()
            p210e = build_p2_10_e_multi_client_demo_seal_result()
            p210e_proves_sealed = (
                p210e.covered_pack == P2_10_E_PACK_ID
                and p210e.completion_seal.p210_done
                and p210e.operator_demo_seal.demo_status.value == "DEMO_SEALED"
                and p210e_gate.gate_status is P210EPrerequisiteGateStatus.GATE_PASSED
            )
            p210e_points_to_p211 = (
                p210e.next_pack == "P2.11"
                and p210e.handoff.next_pack == "P2.11"
            )
            if not p210e_proves_sealed:
                blockers.append("P2.10-E did not prove P2.10 multi-client foundation sealed")
            if not p210e_points_to_p211:
                blockers.append("P2.10-E did not point next to P2.11")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.10-E seal result failed: {exc}")

    status = (
        P211APrerequisiteGateStatus.GATE_REPAIR_REQUIRED
        if blockers
        else P211APrerequisiteGateStatus.GATE_PASSED
    )
    payload = {
        "p210e_report_found": p210e_report_exists,
        "p210e_report_path": P2_10_E_REPORT_PATH,
        "p210e_report_indexed": p210e_report_indexed,
        "p210e_proves_p210_multi_client_sealed": p210e_proves_sealed,
        "p210e_points_to_p211": p210e_points_to_p211,
        "p212_not_started": p212_not_started,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P211APrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def _evidence_ref(
    *,
    source_pack: str,
    source_report: str,
    source_commit: str,
    source_test: str,
    source_object: str,
    notes: str,
) -> SurfacePermissionEvidenceRef:
    payload = {
        "source_pack": source_pack,
        "source_report": source_report,
        "source_commit": source_commit,
        "source_test": source_test,
        "source_object": source_object,
        "notes": notes,
    }
    return SurfacePermissionEvidenceRef(**payload, ref_hash=_hash_payload(payload))


def build_surface_permission_evidence_refs() -> tuple[SurfacePermissionEvidenceRef, ...]:
    return (
        _evidence_ref(
            source_pack="P2.10-A",
            source_report=P2_10_A_REPORT_PATH,
            source_commit="0e177e6",
            source_test="tests/test_p210a_multi_client_foundation.py",
            source_object="ShellClientState",
            notes="client taxonomy, surface availability, run-mode baseline",
        ),
        _evidence_ref(
            source_pack="P2.10-B",
            source_report=P2_10_B_REPORT_PATH,
            source_commit="e54a4f8",
            source_test="tests/test_p210b_web_shell_read_model.py",
            source_object="WebShellReadModel",
            notes="web read-model and local dev fixture surface visibility",
        ),
        _evidence_ref(
            source_pack="P2.10-C",
            source_report=P2_10_C_REPORT_PATH,
            source_commit="f57fcc6",
            source_test="tests/test_p210c_desktop_shell_contract.py",
            source_object="DesktopShellWrapperContract",
            notes="desktop wrapper contract and native authority denial",
        ),
        _evidence_ref(
            source_pack="P2.10-D",
            source_report=P2_10_D_REPORT_PATH,
            source_commit="6c97f20",
            source_test="tests/test_p210d_terminal_shell_client.py",
            source_object="TerminalShellReadModel",
            notes="read-only CLI inspection and terminal no-execution boundary",
        ),
        _evidence_ref(
            source_pack="P2.10-E",
            source_report=P2_10_E_REPORT_PATH,
            source_commit="9e5959f",
            source_test=P2_10_E_TEST_DEMO_REF,
            source_object="MultiClientShellEvidenceBundle",
            notes="P2.10 sealed as honest multi-client Shell foundation",
        ),
        _evidence_ref(
            source_pack="P2.VSLICE-A",
            source_report=P2_VSLICE_A_REPORT_PATH,
            source_commit="f59a586",
            source_test="tests/test_p2_command_preflight.py",
            source_object="CommandPreflightDecision",
            notes="PREFLIGHT_ONLY command preflight evidence; not execution",
        ),
    )


def _evidence_for_client(
    client: ShellClientKind,
    all_refs: tuple[SurfacePermissionEvidenceRef, ...],
) -> tuple[SurfacePermissionEvidenceRef, ...]:
    by_pack = {ref.source_pack: ref for ref in all_refs}
    if client is ShellClientKind.WEB:
        return (by_pack["P2.10-A"], by_pack["P2.10-B"], by_pack["P2.10-E"])
    if client is ShellClientKind.DESKTOP_TAURI:
        return (
            by_pack["P2.10-A"],
            by_pack["P2.10-B"],
            by_pack["P2.10-C"],
            by_pack["P2.10-E"],
        )
    if client in {ShellClientKind.CLI, ShellClientKind.TUI}:
        return (by_pack["P2.10-A"], by_pack["P2.10-D"], by_pack["P2.10-E"])
    return (by_pack["P2.10-A"], by_pack["P2.10-E"])


def _evidence_with_preflight(
    refs: tuple[SurfacePermissionEvidenceRef, ...],
    all_refs: tuple[SurfacePermissionEvidenceRef, ...],
) -> tuple[SurfacePermissionEvidenceRef, ...]:
    preflight = next(ref for ref in all_refs if ref.source_pack == "P2.VSLICE-A")
    if preflight in refs:
        return refs
    return refs + (preflight,)


def _surface_display(surface_id: str) -> str:
    registry = build_default_surface_registry()
    by_id = {surface.surface_id: surface.surface_kind for surface in registry.surfaces}
    return SURFACE_KIND_DISPLAY_NAMES[by_id[surface_id]]


def _safe_action_decision(
    client: ShellClientKind,
    surface_id: str,
    action: SurfacePermissionAction,
) -> tuple[SurfacePermissionLevel, SurfacePermissionReason, tuple[str, ...]]:
    limitations = (
        "P2.11-A is Shell-level pre-execution permission modeling only",
        "ALLOWED/READ_ONLY/PREFLIGHT_ONLY do not grant runtime authorization",
    )
    if surface_id in _SENSITIVE_SURFACES:
        limitations += (
            "sensitive surface: mutation, runtime, sandbox, policy, identity, and execution actions remain denied",
        )

    if client is ShellClientKind.MOBILE_FOUNDATION:
        if action in {
            SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
            SurfacePermissionAction.EXPORT_SURFACE_READ_MODEL,
            SurfacePermissionAction.VIEW_SURFACE_COMMANDS,
        }:
            return (
                SurfacePermissionLevel.FUTURE_GATED,
                SurfacePermissionReason.MOBILE_FOUNDATION_ONLY,
                limitations + ("mobile foundation is future-gated; no mobile app exists",),
            )
        return (
            SurfacePermissionLevel.CONTRACT_ONLY,
            SurfacePermissionReason.MOBILE_FOUNDATION_ONLY,
            limitations + ("mobile foundation remains contract-only",),
        )

    if client is ShellClientKind.TUI:
        return (
            SurfacePermissionLevel.CONTRACT_ONLY,
            SurfacePermissionReason.CLIENT_CONTRACT_ONLY,
            limitations + ("TUI remains contract-only; no interactive TUI product exists",),
        )

    if client is ShellClientKind.CLI:
        if action in {
            SurfacePermissionAction.OPEN_SURFACE,
            SurfacePermissionAction.FOCUS_SURFACE,
        }:
            return (
                SurfacePermissionLevel.UNAVAILABLE,
                SurfacePermissionReason.CLIENT_READ_ONLY,
                limitations + ("CLI has read-only inspection, not visual surface focus",),
            )
        if action is SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT:
            return (
                SurfacePermissionLevel.PREFLIGHT_ONLY,
                SurfacePermissionReason.PREFLIGHT_AVAILABLE_ONLY,
                limitations + ("preflight request is not command execution",),
            )
        return (
            SurfacePermissionLevel.READ_ONLY,
            SurfacePermissionReason.CLIENT_READ_ONLY,
            limitations + ("CLI exposes read-only inspection/export only",),
        )

    if action is SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT:
        return (
            SurfacePermissionLevel.PREFLIGHT_ONLY,
            SurfacePermissionReason.PREFLIGHT_AVAILABLE_ONLY,
            limitations + ("preflight request is not command execution",),
        )
    if action in {
        SurfacePermissionAction.READ_SURFACE_STATE,
        SurfacePermissionAction.INSPECT_SURFACE_EVIDENCE,
        SurfacePermissionAction.VIEW_SURFACE_COMMANDS,
        SurfacePermissionAction.EXPORT_SURFACE_READ_MODEL,
    }:
        return (
            SurfacePermissionLevel.READ_ONLY,
            SurfacePermissionReason.P2_10_CLIENT_BASELINE,
            limitations,
        )
    return (
        SurfacePermissionLevel.ALLOWED,
        SurfacePermissionReason.SURFACE_VISIBLE_IN_SHELL,
        limitations,
    )


def _build_permission_entry(
    *,
    client: ShellClientKind,
    surface_id: str,
    action: SurfacePermissionAction,
    all_refs: tuple[SurfacePermissionEvidenceRef, ...],
) -> SurfacePermissionEntry:
    evidence_refs = _evidence_for_client(client, all_refs)
    if action is SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT:
        evidence_refs = _evidence_with_preflight(evidence_refs, all_refs)

    if action in DISABLED_EXECUTION_ACTIONS:
        permission_level = SurfacePermissionLevel.DENIED
        reason = _EXECUTION_ACTION_REASONS[action]
        limitations = (
            _EXECUTION_ACTION_LIMITATIONS[action],
            "P2.11-A does not authorize runtime actions",
            "permission matrix is not full policy runtime or Custos enforcement",
        )
        if surface_id in _SENSITIVE_SURFACES:
            limitations += ("sensitive surface conservative denial preserved",)
    else:
        permission_level, reason, limitations = _safe_action_decision(
            client,
            surface_id,
            action,
        )

    payload = {
        "client_kind": client,
        "surface_id": surface_id,
        "permission_action": action,
        "permission_level": permission_level,
        "reason": reason,
        "evidence_refs": evidence_refs,
        "limitations": limitations,
        "source_pack_refs": _BASE_EVIDENCE_REFS,
        "no_overclaim_boundaries": tuple(SurfacePermissionNoOverclaimBoundary),
    }
    entry = SurfacePermissionEntry(**payload, entry_hash=_hash_payload(payload))
    assert_surface_permission_entry_has_required_evidence(entry)
    assert_surface_permission_entry_does_not_execute(entry)
    return entry


def build_client_surface_authority_baseline() -> ClientSurfaceAuthorityBaseline:
    evidence_refs = build_surface_permission_evidence_refs()
    payload = {
        "clients": _P2_10_CLIENTS,
        "surfaces": CANONICAL_SURFACE_ORDER,
        "permission_actions": tuple(SurfacePermissionAction),
        "sensitive_surfaces": _SENSITIVE_SURFACES,
        "default_rules": (
            "safe pre-execution actions are visibility/navigation/inspection/preflight/export only",
            "all execution/runtime/sandbox/policy/identity/memory/workflow actions are denied",
            "PREFLIGHT_ONLY means governed preflight request only, never command execution",
            "ALLOWED is scoped to the named Shell surface action only",
        ),
        "client_specific_rules": (
            "WEB uses P2.10-B local web read-model/dev fixture evidence",
            "DESKTOP_TAURI uses P2.10-C wrapper-bound desktop evidence",
            "CLI uses P2.10-D read-only terminal inspection/export evidence",
            "TUI remains contract-only terminal parity",
            "MOBILE_FOUNDATION remains contract-only/future-gated",
        ),
        "surface_specific_rules": (
            "SYSTEM, Settings, and IDE are sensitive surfaces",
            "sensitive surfaces allow visibility/read inspection only where client evidence supports it",
            "sensitive surfaces never allow mutation, execution, runtime control, sandbox control, policy mutation, or identity mutation",
            "canonical surface order is preserved from P2.0/P2.10 truth",
        ),
        "evidence_refs": evidence_refs,
    }
    baseline = ClientSurfaceAuthorityBaseline(
        **payload,
        baseline_hash=_hash_payload(payload),
    )
    assert_client_surface_authority_baseline_complete(baseline)
    return baseline


def _summarize(entries: tuple[SurfacePermissionEntry, ...]) -> SurfacePermissionMatrixSummary:
    counts = {level: 0 for level in SurfacePermissionLevel}
    for entry in entries:
        counts[entry.permission_level] += 1
    sensitive_entries = tuple(
        entry for entry in entries if entry.surface_id in _SENSITIVE_SURFACES
    )
    denied_execution = tuple(
        entry
        for entry in entries
        if entry.permission_action in DISABLED_EXECUTION_ACTIONS
        and entry.permission_level
        in {
            SurfacePermissionLevel.DENIED,
            SurfacePermissionLevel.UNAVAILABLE,
            SurfacePermissionLevel.FUTURE_GATED,
        }
    )
    payload = {
        "total_entries": len(entries),
        "allowed_count": counts[SurfacePermissionLevel.ALLOWED],
        "read_only_count": counts[SurfacePermissionLevel.READ_ONLY],
        "preflight_only_count": counts[SurfacePermissionLevel.PREFLIGHT_ONLY],
        "contract_only_count": counts[SurfacePermissionLevel.CONTRACT_ONLY],
        "future_gated_count": counts[SurfacePermissionLevel.FUTURE_GATED],
        "unavailable_count": counts[SurfacePermissionLevel.UNAVAILABLE],
        "denied_count": counts[SurfacePermissionLevel.DENIED],
        "error_count": counts[SurfacePermissionLevel.ERROR],
        "sensitive_surface_summary": (
            f"{len(sensitive_entries)} sensitive-surface entries across SYSTEM, Settings, and IDE",
            "all sensitive execution/mutation/runtime/sandbox actions denied",
        ),
        "execution_disabled_summary": (
            f"{len(denied_execution)} disabled execution-action entries are denied/unavailable/future-gated",
            "no execution/runtime/sandbox/policy/identity/memory/workflow action is allowed",
        ),
    }
    return SurfacePermissionMatrixSummary(**payload, summary_hash=_hash_payload(payload))


def _find_missing_entries(
    entries: tuple[SurfacePermissionEntry, ...],
    clients: tuple[ShellClientKind, ...],
    surfaces: tuple[str, ...],
    actions: tuple[SurfacePermissionAction, ...],
) -> tuple[str, ...]:
    present = {
        (entry.client_kind, entry.surface_id, entry.permission_action)
        for entry in entries
    }
    missing: list[str] = []
    for client in clients:
        for surface_id in surfaces:
            for action in actions:
                if (client, surface_id, action) not in present:
                    missing.append(f"{client.value}:{surface_id}:{action.value}")
    return tuple(missing)


def build_surface_permission_matrix() -> SurfacePermissionMatrix:
    baseline = build_client_surface_authority_baseline()
    entries: list[SurfacePermissionEntry] = []
    for client in baseline.clients:
        for surface_id in baseline.surfaces:
            for action in baseline.permission_actions:
                entries.append(
                    _build_permission_entry(
                        client=client,
                        surface_id=surface_id,
                        action=action,
                        all_refs=baseline.evidence_refs,
                    )
                )

    entry_tuple = tuple(entries)
    missing_entries = _find_missing_entries(
        entry_tuple,
        baseline.clients,
        baseline.surfaces,
        baseline.permission_actions,
    )
    inconsistencies: tuple[str, ...] = ()
    summary = _summarize(entry_tuple)
    payload = {
        "entries": entry_tuple,
        "clients": baseline.clients,
        "surfaces": baseline.surfaces,
        "actions": baseline.permission_actions,
        "summary": summary,
        "missing_entries": missing_entries,
        "inconsistencies": inconsistencies,
        "evidence_refs": baseline.evidence_refs,
    }
    matrix = SurfacePermissionMatrix(**payload, matrix_hash=_hash_payload(payload))
    assert_surface_permission_matrix_complete(matrix)
    assert_surface_permission_matrix_no_execution_allowed(matrix)
    assert_sensitive_surfaces_are_conservative(matrix)
    return matrix


def build_p2_11_a_handoff(
    matrix: SurfacePermissionMatrix | None = None,
) -> P211AHandoff:
    if matrix is None:
        matrix = build_surface_permission_matrix()
    payload = {
        "next_pack": P2_11_B_NEXT_PACK,
        "next_title": P2_11_B_NEXT_TITLE,
        "handoff_status": "P2.11-B next; projection/read-model not implemented in P2.11-A",
        "permission_baseline_summary": (
            f"{len(matrix.clients)} clients x {len(matrix.surfaces)} surfaces x {len(matrix.actions)} actions",
            "P2.11-A baseline is deterministic and evidence-bound",
            "P2.11 as a whole is not complete",
        ),
        "read_model_projection_needs": (
            "operator-facing matrix projection",
            "query/filter/grouping read model",
            "stable JSON export contract for permission entries",
        ),
        "operator_inspection_needs": (
            "surface/client/action filtering",
            "sensitive-surface limitation display",
            "no-execution boundary display",
        ),
        "remaining_risks": (
            "P2.11-B not implemented",
            "P2.12 truth-label fixture discipline not implemented",
            "permission matrix is not runtime enforcement",
            "mobile remains contract-only/future-gated",
        ),
    }
    return P211AHandoff(**payload, handoff_hash=_hash_payload(payload))


def build_p2_11_a_surface_permission_matrix_result(
    *,
    assert_gate: bool = True,
) -> P211AResult:
    gate = build_p2_11_a_prerequisite_gate()
    if assert_gate and gate.gate_status is not P211APrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.11-A prerequisite gate did not pass",
            field="prerequisite_gate",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    baseline = build_client_surface_authority_baseline()
    matrix = build_surface_permission_matrix()
    handoff = build_p2_11_a_handoff(matrix)
    side_effects = P211ASideEffectProof()
    payload = {
        "covered_pack": P2_11_A_PACK_ID,
        "prerequisite_gate": gate,
        "authority_baseline": baseline,
        "permission_matrix": matrix,
        "matrix_summary": matrix.summary,
        "no_overclaim_boundaries": tuple(SurfacePermissionNoOverclaimBoundary),
        "handoff": handoff,
        "side_effect_proof": side_effects,
        "p211b_not_done": P2_11_B_NOT_DONE,
        "p212_not_started": P2_12_NOT_STARTED,
    }
    result = P211AResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_11_a_no_scope_expansion(result)
    return result


def serialize_p2_11_a_result(result: P211AResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_client_surface_authority_baseline_complete(
    baseline: ClientSurfaceAuthorityBaseline,
) -> None:
    if baseline.clients != _P2_10_CLIENTS:
        _reject(
            "P2.11-A baseline must include all P2.10 clients",
            field="clients",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if baseline.surfaces != CANONICAL_SURFACE_ORDER:
        _reject(
            "P2.11-A baseline must preserve canonical surface order",
            field="surfaces",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if baseline.permission_actions != tuple(SurfacePermissionAction):
        _reject(
            "P2.11-A baseline must include every permission action",
            field="permission_actions",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if baseline.sensitive_surfaces != _SENSITIVE_SURFACES:
        _reject(
            "P2.11-A baseline must mark SYSTEM, Settings, and IDE sensitive",
            field="sensitive_surfaces",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_surface_permission_entry_has_required_evidence(
    entry: SurfacePermissionEntry,
) -> None:
    if not entry.evidence_refs:
        _reject(
            "surface permission entry must carry evidence refs",
            field="evidence_refs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not entry.limitations:
        _reject(
            "surface permission entry must carry limitations",
            field="limitations",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_surface_permission_entry_does_not_execute(
    entry: SurfacePermissionEntry,
) -> None:
    if (
        entry.permission_action in DISABLED_EXECUTION_ACTIONS
        and entry.permission_level
        not in {
            SurfacePermissionLevel.DENIED,
            SurfacePermissionLevel.UNAVAILABLE,
            SurfacePermissionLevel.FUTURE_GATED,
        }
    ):
        _reject(
            "disabled execution action must not be allowed",
            field="permission_level",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if (
        entry.permission_action is SurfacePermissionAction.EXECUTE_COMMAND
        and entry.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY
    ):
        _reject(
            "PREFLIGHT_ONLY must never be command execution",
            field="permission_action",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_surface_permission_matrix_complete(
    matrix: SurfacePermissionMatrix,
) -> None:
    if matrix.missing_entries:
        _reject(
            "surface permission matrix has missing entries",
            field="missing_entries",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    expected = len(_P2_10_CLIENTS) * len(CANONICAL_SURFACE_ORDER) * len(SurfacePermissionAction)
    if matrix.summary.total_entries != expected:
        _reject(
            "surface permission matrix entry count mismatch",
            field="summary.total_entries",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_surface_permission_matrix_no_execution_allowed(
    matrix: SurfacePermissionMatrix,
) -> None:
    for entry in matrix.entries:
        assert_surface_permission_entry_does_not_execute(entry)


def assert_sensitive_surfaces_are_conservative(matrix: SurfacePermissionMatrix) -> None:
    for entry in matrix.entries:
        if entry.surface_id not in _SENSITIVE_SURFACES:
            continue
        if entry.permission_action in DISABLED_EXECUTION_ACTIONS:
            if entry.permission_level not in {
                SurfacePermissionLevel.DENIED,
                SurfacePermissionLevel.UNAVAILABLE,
                SurfacePermissionLevel.FUTURE_GATED,
            }:
                _reject(
                    "sensitive surface execution/mutation action must be conservative",
                    field="sensitive_surface",
                    code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
                )


def assert_p2_11_a_no_scope_expansion(result: P211AResult) -> None:
    proof = result.side_effect_proof
    if any(proof.to_canonical_dict().values()):
        _reject(
            "P2.11-A side-effect proof must keep all execution/runtime/product claims false",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.handoff.next_pack != P2_11_B_NEXT_PACK:
        _reject(
            "P2.11-A must hand off to P2.11-B",
            field="handoff.next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def surface_permission_entry_lookup(
    matrix: SurfacePermissionMatrix,
    *,
    client_kind: ShellClientKind,
    surface_id: str,
    permission_action: SurfacePermissionAction,
) -> SurfacePermissionEntry:
    for entry in matrix.entries:
        if (
            entry.client_kind is client_kind
            and entry.surface_id == surface_id
            and entry.permission_action is permission_action
        ):
            return entry
    _reject(
        f"missing permission entry {client_kind.value}:{surface_id}:{permission_action.value}",
        field="entries",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def surface_permission_display_name(surface_id: str) -> str:
    return _surface_display(surface_id)


P2_11_A_VALIDATION_REFS: tuple[str, ...] = (
    P2_11_A_TEST_MATRIX_REF,
    P2_11_A_TEST_BASELINE_REF,
    P2_11_A_TEST_NO_EXECUTION_REF,
    P2_11_A_TEST_HANDOFF_REF,
    P2_10_E_TEST_DEMO_REF,
    P2_10_E_TEST_TRUTH_REF,
    P2_10_E_TEST_NO_OVERCLAIM_REF,
    P2_10_E_TEST_HANDOFF_REF,
)
