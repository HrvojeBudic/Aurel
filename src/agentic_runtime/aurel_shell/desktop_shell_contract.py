"""P2.10-C Tauri desktop local shell / desktop wrapper contract.

Derives a Python-owned DesktopShellReadModel from P2.10-A ShellClientState and
P2.10-B WebShellReadModel for minimal Tauri desktop wrapper consumption.
Python owns Aurel truth; TypeScript renders contracts; Rust/Tauri wraps only.

Does not implement CLI/TUI parity, mobile app, command execution, native file
authority, native secrets access, native shell execution, or Shell LIVE.
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
from .multi_client_foundation import (
    P2_10_D_NOT_STARTED,
    ShellClientKind,
    ShellClientTruthLabel,
    build_shell_client_state,
)
from .shell_exit_readiness import P2_VSLICE_A_REPORT_PATH
from .web_shell_read_model import (
    P2_10_B_FIXTURE_REL_PATH,
    P2_10_B_REPORT_PATH,
    P2_10_B_WEB_ROOT,
    WebShellReadModel,
    build_p2_10_b_web_shell_result,
    build_web_shell_read_model,
)

P2_10_C_PACK_ID = "P2.10-C"
P2_10_C_SECTION_ID = "P2.10"
P2_10_C_COVERED_RANGE = "P2.10-C"
P2_10_C_NEXT_PACK = "P2.10-D"
P2_10_C_REPORT_FILENAME = "P2_10_C_TAURI_DESKTOP_LOCAL_SHELL.md"
P2_10_C_REPORT_PATH = f"agent/reports/{P2_10_C_REPORT_FILENAME}"
P2_10_C_RESULT_VERSION = "p2_10_c_desktop_shell_contract_result.v1"
P2_10_C_TEST_CONTRACT_REF = "tests/test_p210c_desktop_shell_contract.py"
P2_10_C_TEST_BOUNDARY_REF = "tests/test_p210c_desktop_capability_boundary.py"
P2_10_C_TEST_TAURI_REF = "tests/test_p210c_tauri_wrapper_truth.py"
P2_10_C_DESKTOP_ROOT = P2_10_B_WEB_ROOT
P2_10_C_FIXTURE_REL_PATH = f"{P2_10_C_DESKTOP_ROOT}/public/desktop-shell-read-model.json"
P2_10_C_TAURI_DIR = f"{P2_10_C_DESKTOP_ROOT}/src-tauri"
P2_10_C_TAURI_CONF = f"{P2_10_C_TAURI_DIR}/tauri.conf.json"
P2_10_C_TAURI_DEV_COMMAND = "npm run tauri:dev"
P2_10_C_TAURI_BUILD_COMMAND = "npm run tauri:build"
P2_10_E_NOT_STARTED = True


class P210CPrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


class DesktopShellCapability(str, Enum):
    LOAD_LOCAL_WEB_SHELL = "LOAD_LOCAL_WEB_SHELL"
    DISPLAY_CONTRACT_STATE = "DISPLAY_CONTRACT_STATE"
    DISPLAY_TRUTH_LABELS = "DISPLAY_TRUTH_LABELS"
    DISPLAY_EVIDENCE_REFS = "DISPLAY_EVIDENCE_REFS"
    DISPLAY_LIMITATIONS = "DISPLAY_LIMITATIONS"
    NATIVE_FILE_READ = "NATIVE_FILE_READ"
    NATIVE_FILE_WRITE = "NATIVE_FILE_WRITE"
    NATIVE_SECRET_ACCESS = "NATIVE_SECRET_ACCESS"
    NATIVE_SHELL_EXEC = "NATIVE_SHELL_EXEC"
    NATIVE_NETWORK_BRIDGE = "NATIVE_NETWORK_BRIDGE"
    NATIVE_APPROVAL_BRIDGE = "NATIVE_APPROVAL_BRIDGE"
    NATIVE_RUNTIME_CONTROL = "NATIVE_RUNTIME_CONTROL"
    NATIVE_SANDBOX_CONTROL = "NATIVE_SANDBOX_CONTROL"


class DesktopShellCapabilityStatus(str, Enum):
    ALLOWED_MINIMAL = "ALLOWED_MINIMAL"
    DISABLED = "DISABLED"
    FUTURE_GATED = "FUTURE_GATED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class DesktopShellRunMode(str, Enum):
    DESKTOP_TAURI_CONTRACT = "DESKTOP_TAURI_CONTRACT"
    DESKTOP_TAURI_READ_ONLY = "DESKTOP_TAURI_READ_ONLY"
    DESKTOP_TAURI_DEV_RUNNABLE = "DESKTOP_TAURI_DEV_RUNNABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class DesktopToolingDecision(str, Enum):
    PATH_A_EXTEND_EXISTING = "PATH_A_EXTEND_EXISTING"
    PATH_B_MINIMAL_NEW = "PATH_B_MINIMAL_NEW"
    PATH_C_CONTRACT_ONLY = "PATH_C_CONTRACT_ONLY"


_MINIMAL_ALLOWED_CAPABILITIES: tuple[DesktopShellCapability, ...] = (
    DesktopShellCapability.LOAD_LOCAL_WEB_SHELL,
    DesktopShellCapability.DISPLAY_CONTRACT_STATE,
    DesktopShellCapability.DISPLAY_TRUTH_LABELS,
    DesktopShellCapability.DISPLAY_EVIDENCE_REFS,
    DesktopShellCapability.DISPLAY_LIMITATIONS,
)

_DISABLED_NATIVE_CAPABILITIES: tuple[DesktopShellCapability, ...] = (
    DesktopShellCapability.NATIVE_FILE_READ,
    DesktopShellCapability.NATIVE_FILE_WRITE,
    DesktopShellCapability.NATIVE_SECRET_ACCESS,
    DesktopShellCapability.NATIVE_SHELL_EXEC,
)

_FUTURE_GATED_NATIVE_CAPABILITIES: tuple[DesktopShellCapability, ...] = (
    DesktopShellCapability.NATIVE_NETWORK_BRIDGE,
    DesktopShellCapability.NATIVE_APPROVAL_BRIDGE,
    DesktopShellCapability.NATIVE_RUNTIME_CONTROL,
    DesktopShellCapability.NATIVE_SANDBOX_CONTROL,
)

_DESKTOP_NO_OVERCLAIM_BOUNDARIES: tuple[tuple[str, str, str], ...] = (
    ("NO_FULL_DESKTOP_APP_CLAIM", "full desktop app complete", "Desktop wrapper is not full app"),
    (
        "NO_PRODUCTION_DESKTOP_APP_CLAIM",
        "production desktop app",
        "No production desktop claim in P2.10-C",
    ),
    ("NO_MOBILE_APP_CLAIM", "mobile app runnable", "Mobile belongs to future packs"),
    ("NO_CLI_TUI_PARITY_CLAIM", "CLI/TUI parity complete", "CLI/TUI belongs to P2.10-D"),
    ("NO_SHELL_LIVE_CLAIM", "Shell LIVE", "Shell LIVE is not claimed"),
    (
        "NO_COMMAND_EXECUTION_CLAIM",
        "arbitrary command execution",
        "Command execution is forbidden",
    ),
    (
        "NO_NATIVE_FILE_AUTHORITY_CLAIM",
        "native file authority",
        "Native file read/write is disabled",
    ),
    (
        "NO_NATIVE_SECRET_AUTHORITY_CLAIM",
        "native secrets authority",
        "Native secrets access is disabled",
    ),
    (
        "NO_NATIVE_SHELL_EXEC_CLAIM",
        "native shell execution",
        "Native shell execution is disabled",
    ),
    (
        "NO_NATIVE_RUNTIME_CONTROL_CLAIM",
        "native runtime control",
        "Native runtime control is future-gated",
    ),
    (
        "NO_NATIVE_SANDBOX_CONTROL_CLAIM",
        "native sandbox control",
        "Native sandbox control is future-gated",
    ),
    (
        "NO_SAFE_SANDBOX_CLAIM_UNLESS_PROVEN",
        "safe sandbox",
        "Safe sandbox is not proven in P2.10-C",
    ),
    ("NO_P2_10_D_E_CLAIM", "P2.10-D/E done", "P2.10-D/E remain NOT_DONE"),
)


@dataclass(frozen=True)
class DesktopShellCapabilityEntry(_CanonicalMixin):
    capability: DesktopShellCapability
    status: DesktopShellCapabilityStatus
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class DesktopShellCapabilityBoundary(_CanonicalMixin):
    client_kind: ShellClientKind
    allowed_capabilities: tuple[DesktopShellCapabilityEntry, ...]
    disabled_capabilities: tuple[DesktopShellCapabilityEntry, ...]
    future_gated_capabilities: tuple[DesktopShellCapabilityEntry, ...]
    unavailable_capabilities: tuple[DesktopShellCapabilityEntry, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    no_overclaim_boundaries: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class DesktopShellNoOverclaimBoundary(_CanonicalMixin):
    boundary_id: str
    forbidden_claim: str
    reason: str
    active: bool
    evidence_refs: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class DesktopShellClientStatus(_CanonicalMixin):
    active_client: ShellClientKind
    wrapped_client_kind: ShellClientKind
    client_truth_label: ShellClientTruthLabel
    wrapper_truth_label: ShellClientTruthLabel
    desktop_run_mode: DesktopShellRunMode
    locally_runnable: bool
    launch_command: str
    build_command: str
    launch_working_directory: str
    tauri_config_path: str
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    status_hash: str


@dataclass(frozen=True)
class DesktopShellWrappedWebShellStatus(_CanonicalMixin):
    source_read_model_ref: str
    source_read_model_hash: str
    web_client_truth_label: ShellClientTruthLabel
    web_local_run_mode: str
    web_locally_runnable: bool
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    status_hash: str


@dataclass(frozen=True)
class DesktopShellWrapperContract(_CanonicalMixin):
    client_kind: ShellClientKind
    wrapped_client_kind: ShellClientKind
    source_web_read_model_ref: str
    available_surfaces: tuple[str, ...]
    surface_availability: tuple[str, ...]
    truth_labels: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[str, ...]
    desktop_run_mode: DesktopShellRunMode
    desktop_capability_boundary: DesktopShellCapabilityBoundary
    limitations: tuple[str, ...]
    no_overclaim_boundaries: tuple[DesktopShellNoOverclaimBoundary, ...]
    next_pack: str
    contract_hash: str


@dataclass(frozen=True)
class DesktopShellReadModel(_CanonicalMixin):
    pack_id: str
    title: str
    desktop_client_status: DesktopShellClientStatus
    wrapped_web_shell_status: DesktopShellWrappedWebShellStatus
    available_surfaces: tuple[str, ...]
    surface_availability: tuple[str, ...]
    truth_label_summary: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[str, ...]
    desktop_run_mode: DesktopShellRunMode
    capability_boundary: DesktopShellCapabilityBoundary
    limitations: tuple[str, ...]
    p2_vslice_status: ShellClientTruthLabel
    next_pack_pointer: str
    p210d_not_started: bool
    p210e_not_started: bool
    fixture_rel_path: str
    read_model_hash: str


@dataclass(frozen=True)
class P210CPrerequisiteGate(_CanonicalMixin):
    p210b_report_found: bool
    p210b_report_path: str
    p210b_report_indexed: bool
    p210b_proves_web_shell_done: bool
    p210b_points_to_p210c: bool
    p210d_not_started: bool
    p210e_not_started: bool
    gate_status: P210CPrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class P210CSideEffectProof(_CanonicalMixin):
    p2_10_d_implemented: bool = False
    p2_10_e_implemented: bool = False
    mobile_app_implemented: bool = False
    cli_tui_parity_implemented: bool = False
    arbitrary_command_execution_implemented: bool = False
    command_preflight_behavior_changed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    policy_behavior_changed: bool = False
    identity_behavior_changed: bool = False
    sandbox_behavior_changed: bool = False
    native_file_read_enabled: bool = False
    native_file_write_enabled: bool = False
    native_secrets_access_enabled: bool = False
    native_shell_exec_enabled: bool = False
    native_approval_bridge_enabled: bool = False
    native_runtime_control_enabled: bool = False
    native_sandbox_control_enabled: bool = False
    shell_live_claimed: bool = False
    full_local_app_claimed: bool = False
    full_desktop_app_claimed: bool = False
    production_desktop_app_claimed: bool = False
    mobile_runnable_claimed: bool = False
    native_authority_bridge_claimed: bool = False


@dataclass(frozen=True)
class P210CResult(_CanonicalMixin):
    covered_pack: str
    prerequisite_gate: P210CPrerequisiteGate
    desktop_tooling_decision: DesktopToolingDecision
    desktop_wrapper_contract: DesktopShellWrapperContract
    desktop_capability_boundary: DesktopShellCapabilityBoundary
    desktop_read_model: DesktopShellReadModel
    tauri_wrapper_status: ShellClientTruthLabel
    operator_testable_desktop_path: bool
    source_client_state_hash: str
    source_web_read_model_hash: str
    side_effect_proof: P210CSideEffectProof
    next_pack: str
    p210d_not_started: bool
    result_hash: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _tauri_scaffold_exists() -> bool:
    root = _repo_root()
    return (root / P2_10_C_TAURI_CONF).is_file() and (root / P2_10_C_TAURI_DIR / "Cargo.toml").is_file()


def _resolve_desktop_run_mode(*, tauri_present: bool | None = None) -> DesktopShellRunMode:
    if tauri_present is None:
        tauri_present = _tauri_scaffold_exists()
    if tauri_present:
        return DesktopShellRunMode.DESKTOP_TAURI_DEV_RUNNABLE
    return DesktopShellRunMode.DESKTOP_TAURI_CONTRACT


def _resolve_wrapper_truth_label(run_mode: DesktopShellRunMode) -> ShellClientTruthLabel:
    if run_mode is DesktopShellRunMode.DESKTOP_TAURI_DEV_RUNNABLE:
        return ShellClientTruthLabel.DEV_FIXTURE
    return ShellClientTruthLabel.CONTRACT_ONLY


def _build_capability_entry(
    capability: DesktopShellCapability,
    status: DesktopShellCapabilityStatus,
    *,
    evidence_refs: tuple[str, ...] | None = None,
    limitations: tuple[str, ...] | None = None,
) -> DesktopShellCapabilityEntry:
    if evidence_refs is None:
        evidence_refs = (P2_10_C_REPORT_PATH, P2_10_C_TEST_BOUNDARY_REF)
    if limitations is None:
        limitations = ("capability boundary is contract-only in P2.10-C",)
    payload = {
        "capability": capability,
        "status": status,
        "evidence_refs": evidence_refs,
        "limitations": limitations,
    }
    return DesktopShellCapabilityEntry(**payload, entry_hash=_hash_payload(payload))


def build_desktop_shell_capability_boundary() -> DesktopShellCapabilityBoundary:
    allowed = tuple(
        _build_capability_entry(
            cap,
            DesktopShellCapabilityStatus.ALLOWED_MINIMAL,
            limitations=("minimal desktop wrapper capability only",),
        )
        for cap in _MINIMAL_ALLOWED_CAPABILITIES
    )
    disabled = tuple(
        _build_capability_entry(
            cap,
            DesktopShellCapabilityStatus.DISABLED,
            limitations=("native capability explicitly disabled in P2.10-C",),
        )
        for cap in _DISABLED_NATIVE_CAPABILITIES
    )
    future_gated = tuple(
        _build_capability_entry(
            cap,
            DesktopShellCapabilityStatus.FUTURE_GATED,
            limitations=("future pack required; not enabled in P2.10-C",),
        )
        for cap in _FUTURE_GATED_NATIVE_CAPABILITIES
    )
    payload = {
        "client_kind": ShellClientKind.DESKTOP_TAURI,
        "allowed_capabilities": allowed,
        "disabled_capabilities": disabled,
        "future_gated_capabilities": future_gated,
        "unavailable_capabilities": (),
        "evidence_refs": (
            P2_10_C_REPORT_PATH,
            P2_10_C_TEST_BOUNDARY_REF,
            P2_10_C_TAURI_CONF,
        ),
        "limitations": (
            "desktop capability boundary does not grant native authority",
            "disabled native capabilities remain off",
            "future-gated capabilities are not enabled",
        ),
        "no_overclaim_boundaries": tuple(b[0] for b in _DESKTOP_NO_OVERCLAIM_BOUNDARIES),
    }
    return DesktopShellCapabilityBoundary(**payload, boundary_hash=_hash_payload(payload))


def build_desktop_shell_no_overclaim_boundaries() -> tuple[DesktopShellNoOverclaimBoundary, ...]:
    boundaries: list[DesktopShellNoOverclaimBoundary] = []
    for boundary_id, forbidden, reason in _DESKTOP_NO_OVERCLAIM_BOUNDARIES:
        payload = {
            "boundary_id": boundary_id,
            "forbidden_claim": forbidden,
            "reason": reason,
            "active": True,
            "evidence_refs": (P2_10_C_REPORT_PATH, P2_10_B_REPORT_PATH),
        }
        boundaries.append(
            DesktopShellNoOverclaimBoundary(**payload, boundary_hash=_hash_payload(payload))
        )
    return tuple(boundaries)


def build_p2_10_c_prerequisite_gate(
    *,
    p210b_report_exists: bool | None = None,
    p210b_report_indexed: bool | None = None,
) -> P210CPrerequisiteGate:
    report_path = _repo_root() / P2_10_B_REPORT_PATH
    if p210b_report_exists is None:
        p210b_report_exists = report_path.is_file()
    if p210b_report_indexed is None:
        reports_index = (_repo_root() / "agent" / "REPORTS.md").read_text(encoding="utf-8")
        p210b_report_indexed = "P2_10_B_LOCAL_WEB_SHELL_SKELETON" in reports_index

    blockers: list[str] = []
    p210b_proves_done = False
    p210b_points_to_c = False

    if not p210b_report_exists:
        blockers.append("P2.10-B report missing")
    if not p210b_report_indexed:
        blockers.append("P2.10-B report not indexed")

    if p210b_report_exists:
        try:
            p210b = build_p2_10_b_web_shell_result()
            p210b_proves_done = (
                p210b.covered_pack == "P2.10-B"
                and p210b.read_model.client_status.active_client is ShellClientKind.WEB
            )
            p210b_points_to_c = p210b.next_pack == "P2.10-C"
            if not p210b_proves_done:
                blockers.append("P2.10-B did not prove local web shell/read model DONE")
            if not p210b_points_to_c:
                blockers.append("P2.10-B did not point next to P2.10-C")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.10-B web shell result failed: {exc}")

    if blockers:
        status = P210CPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    else:
        status = P210CPrerequisiteGateStatus.GATE_PASSED

    payload = {
        "p210b_report_found": p210b_report_exists,
        "p210b_report_path": P2_10_B_REPORT_PATH,
        "p210b_report_indexed": p210b_report_indexed,
        "p210b_proves_web_shell_done": p210b_proves_done,
        "p210b_points_to_p210c": p210b_points_to_c,
        "p210d_not_started": P2_10_D_NOT_STARTED,
        "p210e_not_started": P2_10_E_NOT_STARTED,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P210CPrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def build_desktop_shell_wrapper_contract(
    *,
    web_read_model: WebShellReadModel | None = None,
    capability_boundary: DesktopShellCapabilityBoundary | None = None,
    desktop_run_mode: DesktopShellRunMode | None = None,
) -> DesktopShellWrapperContract:
    if web_read_model is None:
        web_read_model = build_web_shell_read_model()
    if capability_boundary is None:
        capability_boundary = build_desktop_shell_capability_boundary()
    if desktop_run_mode is None:
        desktop_run_mode = _resolve_desktop_run_mode()

    desktop_state = build_shell_client_state(ShellClientKind.DESKTOP_TAURI)
    no_overclaim = build_desktop_shell_no_overclaim_boundaries()
    wrapper_label = _resolve_wrapper_truth_label(desktop_run_mode)

    truth_labels = (
        wrapper_label,
        ShellClientTruthLabel.CONTRACT_ONLY,
        ShellClientTruthLabel.PREFLIGHT_ONLY,
        ShellClientTruthLabel.NOT_STARTED,
    )
    evidence_refs = desktop_state.evidence_refs + (
        P2_10_B_REPORT_PATH,
        P2_10_B_FIXTURE_REL_PATH,
        P2_10_C_REPORT_PATH,
    )

    payload = {
        "client_kind": ShellClientKind.DESKTOP_TAURI,
        "wrapped_client_kind": ShellClientKind.WEB,
        "source_web_read_model_ref": P2_10_B_FIXTURE_REL_PATH,
        "available_surfaces": desktop_state.available_surfaces,
        "surface_availability": tuple(
            s.surface_id for s in desktop_state.surface_availability if s.available
        ),
        "truth_labels": truth_labels,
        "evidence_refs": evidence_refs,
        "desktop_run_mode": desktop_run_mode,
        "desktop_capability_boundary": capability_boundary,
        "limitations": desktop_state.limitations
        + (
            "desktop wrapper wraps P2.10-B web shell read model only",
            "Tauri native layer is minimal window shell only",
            "runnable desktop wrapper does not equal Shell LIVE or full local app",
        ),
        "no_overclaim_boundaries": no_overclaim,
        "next_pack": P2_10_C_NEXT_PACK,
    }
    return DesktopShellWrapperContract(**payload, contract_hash=_hash_payload(payload))


def build_desktop_shell_read_model(
    *,
    web_read_model: WebShellReadModel | None = None,
    wrapper_contract: DesktopShellWrapperContract | None = None,
    capability_boundary: DesktopShellCapabilityBoundary | None = None,
    desktop_run_mode: DesktopShellRunMode | None = None,
    locally_runnable: bool | None = None,
) -> DesktopShellReadModel:
    if web_read_model is None:
        web_read_model = build_web_shell_read_model()
    if capability_boundary is None:
        capability_boundary = build_desktop_shell_capability_boundary()
    if wrapper_contract is None:
        wrapper_contract = build_desktop_shell_wrapper_contract(
            web_read_model=web_read_model,
            capability_boundary=capability_boundary,
            desktop_run_mode=desktop_run_mode,
        )
    if desktop_run_mode is None:
        desktop_run_mode = wrapper_contract.desktop_run_mode

    tauri_present = _tauri_scaffold_exists()
    if locally_runnable is None:
        locally_runnable = (
            tauri_present
            and desktop_run_mode is DesktopShellRunMode.DESKTOP_TAURI_DEV_RUNNABLE
        )

    wrapper_label = _resolve_wrapper_truth_label(desktop_run_mode)
    launch_command = P2_10_C_TAURI_DEV_COMMAND if locally_runnable else ""
    build_command = P2_10_C_TAURI_BUILD_COMMAND if tauri_present else ""

    desktop_state = build_shell_client_state(ShellClientKind.DESKTOP_TAURI)
    client_payload = {
        "active_client": ShellClientKind.DESKTOP_TAURI,
        "wrapped_client_kind": ShellClientKind.WEB,
        "client_truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
        "wrapper_truth_label": wrapper_label,
        "desktop_run_mode": desktop_run_mode,
        "locally_runnable": locally_runnable,
        "launch_command": launch_command,
        "build_command": build_command,
        "launch_working_directory": P2_10_C_DESKTOP_ROOT if locally_runnable else "",
        "tauri_config_path": P2_10_C_TAURI_CONF if tauri_present else "",
        "evidence_refs": wrapper_contract.evidence_refs,
        "limitations": wrapper_contract.limitations,
    }
    desktop_client_status = DesktopShellClientStatus(
        **client_payload,
        status_hash=_hash_payload(client_payload),
    )

    wrapped_payload = {
        "source_read_model_ref": P2_10_B_FIXTURE_REL_PATH,
        "source_read_model_hash": web_read_model.read_model_hash,
        "web_client_truth_label": web_read_model.client_status.client_truth_label,
        "web_local_run_mode": web_read_model.local_run_mode,
        "web_locally_runnable": web_read_model.client_status.locally_runnable,
        "evidence_refs": (P2_10_B_REPORT_PATH, P2_10_B_FIXTURE_REL_PATH),
        "limitations": (
            "wrapped web shell status is inherited from P2.10-B",
            "desktop does not invent separate web truth",
        ),
    }
    wrapped_status = DesktopShellWrappedWebShellStatus(
        **wrapped_payload,
        status_hash=_hash_payload(wrapped_payload),
    )

    payload = {
        "pack_id": P2_10_C_PACK_ID,
        "title": "Aurel Shell Desktop Wrapper",
        "desktop_client_status": desktop_client_status,
        "wrapped_web_shell_status": wrapped_status,
        "available_surfaces": desktop_state.available_surfaces,
        "surface_availability": wrapper_contract.surface_availability,
        "truth_label_summary": wrapper_contract.truth_labels,
        "evidence_refs": wrapper_contract.evidence_refs,
        "desktop_run_mode": desktop_run_mode,
        "capability_boundary": capability_boundary,
        "limitations": wrapper_contract.limitations,
        "p2_vslice_status": ShellClientTruthLabel.PREFLIGHT_ONLY,
        "next_pack_pointer": P2_10_C_NEXT_PACK,
        "p210d_not_started": P2_10_D_NOT_STARTED,
        "p210e_not_started": P2_10_E_NOT_STARTED,
        "fixture_rel_path": P2_10_C_FIXTURE_REL_PATH,
    }
    return DesktopShellReadModel(**payload, read_model_hash=_hash_payload(payload))


def _resolve_desktop_tooling_decision() -> DesktopToolingDecision:
    if _tauri_scaffold_exists():
        return DesktopToolingDecision.PATH_B_MINIMAL_NEW
    return DesktopToolingDecision.PATH_C_CONTRACT_ONLY


def build_p2_10_c_desktop_shell_result(
    *,
    skip_prerequisite_gate: bool = False,
    locally_runnable: bool | None = None,
) -> P210CResult:
    gate = build_p2_10_c_prerequisite_gate()
    if not skip_prerequisite_gate:
        assert_p2_10_c_prerequisite_gate_passed(gate)

    web_read_model = build_web_shell_read_model()
    capability_boundary = build_desktop_shell_capability_boundary()
    desktop_run_mode = _resolve_desktop_run_mode()
    wrapper_contract = build_desktop_shell_wrapper_contract(
        web_read_model=web_read_model,
        capability_boundary=capability_boundary,
        desktop_run_mode=desktop_run_mode,
    )
    read_model = build_desktop_shell_read_model(
        web_read_model=web_read_model,
        wrapper_contract=wrapper_contract,
        capability_boundary=capability_boundary,
        desktop_run_mode=desktop_run_mode,
        locally_runnable=locally_runnable,
    )

    desktop_state = build_shell_client_state(ShellClientKind.DESKTOP_TAURI)
    tauri_status = _resolve_wrapper_truth_label(desktop_run_mode)
    operator_path = read_model.desktop_client_status.locally_runnable

    side_effect_proof = P210CSideEffectProof()
    payload = {
        "covered_pack": P2_10_C_PACK_ID,
        "prerequisite_gate": gate,
        "desktop_tooling_decision": _resolve_desktop_tooling_decision(),
        "desktop_wrapper_contract": wrapper_contract,
        "desktop_capability_boundary": capability_boundary,
        "desktop_read_model": read_model,
        "tauri_wrapper_status": tauri_status,
        "operator_testable_desktop_path": operator_path,
        "source_client_state_hash": desktop_state.state_hash,
        "source_web_read_model_hash": web_read_model.read_model_hash,
        "side_effect_proof": side_effect_proof,
        "next_pack": P2_10_C_NEXT_PACK,
        "p210d_not_started": P2_10_D_NOT_STARTED,
    }
    result = P210CResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_10_c_no_scope_expansion(result)
    assert_p2_vslice_a_remains_preflight_in_p210c(result)
    assert_desktop_shell_derives_from_p210a_b(result)
    return result


def serialize_desktop_shell_read_model(read_model: DesktopShellReadModel) -> str:
    return to_canonical_json(read_model.to_canonical_dict())


def serialize_p2_10_c_result(result: P210CResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def export_desktop_shell_read_model_fixture(
    output_path: Path | None = None,
    *,
    locally_runnable: bool | None = None,
) -> Path:
    read_model = build_desktop_shell_read_model(locally_runnable=locally_runnable)
    if output_path is None:
        output_path = _repo_root() / P2_10_C_FIXTURE_REL_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_desktop_shell_read_model(read_model), encoding="utf-8")
    return output_path


def assert_p2_10_c_prerequisite_gate_passed(gate: P210CPrerequisiteGate) -> None:
    if gate.gate_status is not P210CPrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.10-C cannot proceed unless P2.10-B report exists, is indexed, "
            "proves local web shell/read model DONE, and points to P2.10-C",
            field="gate_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_vslice_a_remains_preflight_in_p210c(result: P210CResult) -> None:
    rm = result.desktop_read_model
    if rm.p2_vslice_status is not ShellClientTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A must remain PREFLIGHT_ONLY in P2.10-C",
            field="p2_vslice_status",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_desktop_shell_derives_from_p210a_b(result: P210CResult) -> None:
    desktop_state = build_shell_client_state(ShellClientKind.DESKTOP_TAURI)
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = result.desktop_read_model
    contract = result.desktop_wrapper_contract

    if contract.client_kind is not ShellClientKind.DESKTOP_TAURI:
        _reject(
            "desktop wrapper client must be DESKTOP_TAURI",
            field="client_kind",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if contract.wrapped_client_kind is not ShellClientKind.WEB:
        _reject(
            "desktop wrapper must wrap WEB client",
            field="wrapped_client_kind",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if set(rm.available_surfaces) != set(desktop_state.available_surfaces):
        _reject(
            "desktop surfaces must match P2.10-A DESKTOP_TAURI ShellClientState",
            field="available_surfaces",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if result.source_client_state_hash != desktop_state.state_hash:
        _reject(
            "source client state hash must match DESKTOP_TAURI ShellClientState",
            field="source_client_state_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    web_rm = build_web_shell_read_model()
    if result.source_web_read_model_hash != web_rm.read_model_hash:
        _reject(
            "source web read model hash must match current WebShellReadModel",
            field="source_web_read_model_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if set(web_state.available_surfaces) != {s.surface_id for s in web_rm.surfaces}:
        _reject(
            "wrapped web read model must preserve WEB surfaces",
            field="source_web_read_model_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_p2_10_c_no_scope_expansion(result: P210CResult) -> None:
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_10_d_implemented,
            proof.p2_10_e_implemented,
            proof.mobile_app_implemented,
            proof.cli_tui_parity_implemented,
            proof.arbitrary_command_execution_implemented,
            proof.command_preflight_behavior_changed,
            proof.p2_vslice_a_behavior_changed,
            proof.policy_behavior_changed,
            proof.identity_behavior_changed,
            proof.sandbox_behavior_changed,
            proof.native_file_read_enabled,
            proof.native_file_write_enabled,
            proof.native_secrets_access_enabled,
            proof.native_shell_exec_enabled,
            proof.native_approval_bridge_enabled,
            proof.native_runtime_control_enabled,
            proof.native_sandbox_control_enabled,
            proof.shell_live_claimed,
            proof.full_local_app_claimed,
            proof.full_desktop_app_claimed,
            proof.production_desktop_app_claimed,
            proof.mobile_runnable_claimed,
            proof.native_authority_bridge_claimed,
        )
    ):
        _reject(
            "P2.10-C must not expand into D/E, mobile, CLI/TUI, execution, or native authority",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    rm = result.desktop_read_model
    if rm.next_pack_pointer != "P2.10-D":
        _reject(
            "P2.10-C next pack must be P2.10-D",
            field="next_pack_pointer",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not rm.p210d_not_started:
        _reject(
            "P2.10-D must remain not started",
            field="p210d_not_started",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_10_c_no_shell_live_or_native_authority(result: P210CResult) -> None:
    rm = result.desktop_read_model
    if ShellClientTruthLabel.LIVE in rm.truth_label_summary:
        _reject(
            "P2.10-C must not include LIVE truth label",
            field="truth_label_summary",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    for boundary in result.desktop_wrapper_contract.no_overclaim_boundaries:
        if not boundary.active:
            _reject(
                f"boundary {boundary.boundary_id} must remain active",
                field="no_overclaim_boundaries",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    if P2_VSLICE_A_REPORT_PATH not in rm.evidence_refs:
        _reject(
            "P2.VSLICE-A evidence ref must be preserved",
            field="evidence_refs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    for entry in rm.capability_boundary.disabled_capabilities:
        if entry.status is not DesktopShellCapabilityStatus.DISABLED:
            _reject(
                f"{entry.capability.value} must remain DISABLED",
                field="disabled_capabilities",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
