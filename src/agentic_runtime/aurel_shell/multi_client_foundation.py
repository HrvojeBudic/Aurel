"""P2.10-A multi-client Shell foundation / client parity contracts.

Contract-only foundation layer defining client taxonomy, shared Shell client
state, parity matrix, local run mode boundaries, surface availability, and
no-overclaim boundaries for future web, desktop, mobile, CLI, and TUI clients.

Python owns Aurel truth. TypeScript consumes Shell contracts later. Rust is
only minimal Tauri wrapper glue later. This module does not implement web UI,
Tauri desktop, mobile apps, command execution, or Shell LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .client_consistency import ClientKind, build_multi_client_consistency_contract
from .cli_binding import (
    ShellBindingStatus,
    build_shell_cli_binding_contract,
    build_shell_tui_binding_contract,
)
from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .navigation_boundary import build_no_universal_left_nav_contract
from .shell_exit_final_seal import (
    P2_9_D_NEXT_PACK_IF_GATE_PASSES,
    P2_9_D_REPORT_PATH,
    build_p2_9_d_shell_exit_final_seal_result,
)
from .shell_exit_readiness import P2_VSLICE_A_REPORT_PATH
from .surface_registry import (
    CANONICAL_SURFACE_ORDER,
    SURFACE_KIND_DISPLAY_NAMES,
    AurelSurfaceKind,
    AurelSurfaceRegistry,
    build_default_surface_registry,
)
from .topbar import build_default_topbar_surface_registry, build_global_topbar_read_model

P2_10_A_PACK_ID = "P2.10-A"
P2_10_A_SECTION_ID = "P2.10"
P2_10_A_COVERED_RANGE = "P2.10-A"
P2_10_A_NEXT_PACK = "P2.10-B"
P2_10_A_REPORT_FILENAME = "P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION.md"
P2_10_A_REPORT_PATH = f"agent/reports/{P2_10_A_REPORT_FILENAME}"
P2_10_A_RESULT_VERSION = "p2_10_a_multi_client_foundation_result.v1"
P2_10_A_TEST_FOUNDATION_REF = "tests/test_p210a_multi_client_foundation.py"
P2_10_A_TEST_PARITY_REF = "tests/test_shell_client_parity_matrix.py"
P2_10_A_TEST_RUN_MODES_REF = "tests/test_shell_client_run_modes.py"

P2_10_B_NOT_STARTED = True
P2_10_C_NOT_STARTED = True
P2_10_D_NOT_STARTED = True

_SURFACE_SELECTOR_IDS: frozenset[str] = frozenset(
    {"aurel_cro", "hq", "corp", "hub", "ide"}
)
_TOPBAR_RIGHT_IDS: frozenset[str] = frozenset({"system", "settings"})


class ShellClientKind(str, Enum):
    WEB = "WEB"
    DESKTOP_TAURI = "DESKTOP_TAURI"
    MOBILE_FOUNDATION = "MOBILE_FOUNDATION"
    CLI = "CLI"
    TUI = "TUI"


class ShellClientLocality(str, Enum):
    LOCAL_DEV = "LOCAL_DEV"
    LOCAL_DESKTOP = "LOCAL_DESKTOP"
    LOCAL_TERMINAL = "LOCAL_TERMINAL"
    MOBILE_CONTRACT_ONLY = "MOBILE_CONTRACT_ONLY"
    REMOTE_UNAVAILABLE = "REMOTE_UNAVAILABLE"


class ShellClientRunMode(str, Enum):
    PYTHON_BACKEND_ONLY = "PYTHON_BACKEND_ONLY"
    WEB_DEV_SHELL_CONTRACT = "WEB_DEV_SHELL_CONTRACT"
    DESKTOP_TAURI_CONTRACT = "DESKTOP_TAURI_CONTRACT"
    CLI_TUI_CONTRACT = "CLI_TUI_CONTRACT"
    MOBILE_CONTRACT_ONLY = "MOBILE_CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


class ShellClientTruthLabel(str, Enum):
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    PREFLIGHT_ONLY = "PREFLIGHT_ONLY"
    READ_ONLY = "READ_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    NOT_STARTED = "NOT_STARTED"


class ShellClientCapability(str, Enum):
    VIEW_SURFACES = "VIEW_SURFACES"
    VIEW_TRUTH_LABELS = "VIEW_TRUTH_LABELS"
    VIEW_EVIDENCE_REFS = "VIEW_EVIDENCE_REFS"
    LIST_COMMANDS = "LIST_COMMANDS"
    PREFLIGHT_COMMANDS = "PREFLIGHT_COMMANDS"
    VIEW_LOCAL_RUN_MODE = "VIEW_LOCAL_RUN_MODE"
    VIEW_LEFT_NAV_CONTRACT = "VIEW_LEFT_NAV_CONTRACT"
    VIEW_RIGHT_INSPECTOR_CONTRACT = "VIEW_RIGHT_INSPECTOR_CONTRACT"
    VIEW_CLIENT_LIMITATIONS = "VIEW_CLIENT_LIMITATIONS"


class ShellClientParityDimension(str, Enum):
    SURFACE_SELECTOR_VISIBLE = "SURFACE_SELECTOR_VISIBLE"
    SURFACE_AVAILABILITY_VISIBLE = "SURFACE_AVAILABILITY_VISIBLE"
    TRUTH_LABELS_VISIBLE = "TRUTH_LABELS_VISIBLE"
    EVIDENCE_REFS_VISIBLE = "EVIDENCE_REFS_VISIBLE"
    COMMANDS_LIST_VISIBLE = "COMMANDS_LIST_VISIBLE"
    COMMAND_PREFLIGHT_VISIBLE = "COMMAND_PREFLIGHT_VISIBLE"
    LOCAL_RUN_MODE_VISIBLE = "LOCAL_RUN_MODE_VISIBLE"
    RIGHT_INSPECTOR_CONTRACT_VISIBLE = "RIGHT_INSPECTOR_CONTRACT_VISIBLE"
    LEFT_NAV_CONTRACT_VISIBLE = "LEFT_NAV_CONTRACT_VISIBLE"
    CLIENT_LIMITATIONS_VISIBLE = "CLIENT_LIMITATIONS_VISIBLE"


class P210APrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


_SHELL_CLIENT_KINDS: tuple[ShellClientKind, ...] = tuple(ShellClientKind)
_PARITY_DIMENSIONS: tuple[ShellClientParityDimension, ...] = tuple(ShellClientParityDimension)

_LEGACY_CLIENT_KIND_MAP: dict[ShellClientKind, ClientKind] = {
    ShellClientKind.WEB: ClientKind.WEB,
    ShellClientKind.DESKTOP_TAURI: ClientKind.DESKTOP,
    ShellClientKind.MOBILE_FOUNDATION: ClientKind.MOBILE,
    ShellClientKind.CLI: ClientKind.CLI,
    ShellClientKind.TUI: ClientKind.TUI,
}

_CLIENT_DISPLAY_NAMES: dict[ShellClientKind, str] = {
    ShellClientKind.WEB: "Web",
    ShellClientKind.DESKTOP_TAURI: "Desktop (Tauri contract)",
    ShellClientKind.MOBILE_FOUNDATION: "Mobile foundation",
    ShellClientKind.CLI: "CLI",
    ShellClientKind.TUI: "TUI",
}

_CLIENT_LOCALITIES: dict[ShellClientKind, ShellClientLocality] = {
    ShellClientKind.WEB: ShellClientLocality.LOCAL_DEV,
    ShellClientKind.DESKTOP_TAURI: ShellClientLocality.LOCAL_DESKTOP,
    ShellClientKind.MOBILE_FOUNDATION: ShellClientLocality.MOBILE_CONTRACT_ONLY,
    ShellClientKind.CLI: ShellClientLocality.LOCAL_TERMINAL,
    ShellClientKind.TUI: ShellClientLocality.LOCAL_TERMINAL,
}

_CLIENT_RUN_MODES: dict[ShellClientKind, ShellClientRunMode] = {
    ShellClientKind.WEB: ShellClientRunMode.WEB_DEV_SHELL_CONTRACT,
    ShellClientKind.DESKTOP_TAURI: ShellClientRunMode.DESKTOP_TAURI_CONTRACT,
    ShellClientKind.MOBILE_FOUNDATION: ShellClientRunMode.MOBILE_CONTRACT_ONLY,
    ShellClientKind.CLI: ShellClientRunMode.CLI_TUI_CONTRACT,
    ShellClientKind.TUI: ShellClientRunMode.CLI_TUI_CONTRACT,
}

_CLIENT_TRUTH_LABELS: dict[ShellClientKind, ShellClientTruthLabel] = {
    ShellClientKind.WEB: ShellClientTruthLabel.CONTRACT_ONLY,
    ShellClientKind.DESKTOP_TAURI: ShellClientTruthLabel.CONTRACT_ONLY,
    ShellClientKind.MOBILE_FOUNDATION: ShellClientTruthLabel.CONTRACT_ONLY,
    ShellClientKind.CLI: ShellClientTruthLabel.READ_ONLY,
    ShellClientKind.TUI: ShellClientTruthLabel.UNAVAILABLE,
}

_CLIENT_CAPABILITIES: dict[ShellClientKind, tuple[ShellClientCapability, ...]] = {
    ShellClientKind.WEB: (
        ShellClientCapability.VIEW_SURFACES,
        ShellClientCapability.VIEW_TRUTH_LABELS,
        ShellClientCapability.VIEW_EVIDENCE_REFS,
        ShellClientCapability.LIST_COMMANDS,
        ShellClientCapability.PREFLIGHT_COMMANDS,
        ShellClientCapability.VIEW_LOCAL_RUN_MODE,
        ShellClientCapability.VIEW_LEFT_NAV_CONTRACT,
        ShellClientCapability.VIEW_RIGHT_INSPECTOR_CONTRACT,
        ShellClientCapability.VIEW_CLIENT_LIMITATIONS,
    ),
    ShellClientKind.DESKTOP_TAURI: (
        ShellClientCapability.VIEW_SURFACES,
        ShellClientCapability.VIEW_TRUTH_LABELS,
        ShellClientCapability.VIEW_EVIDENCE_REFS,
        ShellClientCapability.LIST_COMMANDS,
        ShellClientCapability.PREFLIGHT_COMMANDS,
        ShellClientCapability.VIEW_LOCAL_RUN_MODE,
        ShellClientCapability.VIEW_LEFT_NAV_CONTRACT,
        ShellClientCapability.VIEW_RIGHT_INSPECTOR_CONTRACT,
        ShellClientCapability.VIEW_CLIENT_LIMITATIONS,
    ),
    ShellClientKind.MOBILE_FOUNDATION: (
        ShellClientCapability.VIEW_SURFACES,
        ShellClientCapability.VIEW_TRUTH_LABELS,
        ShellClientCapability.VIEW_EVIDENCE_REFS,
        ShellClientCapability.VIEW_LOCAL_RUN_MODE,
        ShellClientCapability.VIEW_CLIENT_LIMITATIONS,
    ),
    ShellClientKind.CLI: (
        ShellClientCapability.VIEW_SURFACES,
        ShellClientCapability.VIEW_TRUTH_LABELS,
        ShellClientCapability.VIEW_EVIDENCE_REFS,
        ShellClientCapability.LIST_COMMANDS,
        ShellClientCapability.PREFLIGHT_COMMANDS,
        ShellClientCapability.VIEW_LOCAL_RUN_MODE,
        ShellClientCapability.VIEW_LEFT_NAV_CONTRACT,
        ShellClientCapability.VIEW_RIGHT_INSPECTOR_CONTRACT,
        ShellClientCapability.VIEW_CLIENT_LIMITATIONS,
    ),
    ShellClientKind.TUI: (
        ShellClientCapability.VIEW_CLIENT_LIMITATIONS,
        ShellClientCapability.VIEW_LOCAL_RUN_MODE,
    ),
}

_NO_OVERCLAIM_BOUNDARIES: tuple[tuple[str, str, str], ...] = (
    (
        "NO_FULL_LOCAL_APP_CLAIM",
        "full local app complete",
        "P2.10-A defines contracts only; runnable local app belongs to P2.10-B+",
    ),
    (
        "NO_DESKTOP_APP_COMPLETE_CLAIM",
        "desktop app complete",
        "No Tauri scaffold or tested desktop runnable path exists",
    ),
    (
        "NO_MOBILE_APP_CLAIM",
        "mobile app runnable",
        "Mobile is contract-only foundation; no app-store product",
    ),
    (
        "NO_SHELL_LIVE_CLAIM",
        "Shell LIVE",
        "Shell product readiness and LIVE runtime remain unclaimed",
    ),
    (
        "NO_COMMAND_EXECUTION_CLAIM",
        "arbitrary command execution",
        "P2.VSLICE-A remains PREFLIGHT_ONLY; no command execution",
    ),
    (
        "NO_SAFE_SANDBOX_CLAIM_UNLESS_PROVEN",
        "safe sandbox proven",
        "Safe sandbox requires explicit proof; not claimed here",
    ),
    (
        "NO_PRODUCTION_API_CLAIM",
        "production API server",
        "API exposure remains schema-only with no-server boundary",
    ),
    (
        "NO_FULL_API_EVENT_BRIDGE_LIVE_CLAIM",
        "full API/event bridge live",
        "Event bridge remains contract-only with no-event-bus boundary",
    ),
    (
        "NO_P2_10_B_C_D_CLAIM",
        "P2.10-B/C/D done",
        "Only P2.10-A foundation is implemented; B/C/D remain NOT_DONE",
    ),
)


@dataclass(frozen=True)
class ShellClientSurfaceAvailability(_CanonicalMixin):
    surface_id: str
    surface_label: str
    available: bool
    truth_label: ShellClientTruthLabel
    supported_clients: tuple[ShellClientKind, ...]
    unsupported_clients: tuple[ShellClientKind, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    availability_hash: str


@dataclass(frozen=True)
class ShellGlobalTopbarContract(_CanonicalMixin):
    contract_id: str
    global_topbar_visible: bool
    surface_selector_surface_ids: tuple[str, ...]
    right_side_surface_ids: tuple[str, ...]
    no_universal_left_nav: bool
    per_surface_left_nav_required: bool
    per_surface_right_inspector_required: bool
    truth_label: ShellClientTruthLabel
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class ShellSurfaceNavInspectorContract(_CanonicalMixin):
    surface_id: str
    left_nav_owned_by_surface: bool
    right_inspector_owned_by_surface: bool
    global_left_nav_allowed: bool
    truth_label: ShellClientTruthLabel
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True)
class ShellClientLocalRunModeEntry(_CanonicalMixin):
    client_kind: ShellClientKind | None
    run_mode: ShellClientRunMode
    truth_label: ShellClientTruthLabel
    locally_runnable: bool
    contract_only: bool
    launch_command: str
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellClientState(_CanonicalMixin):
    client_kind: ShellClientKind
    locality: ShellClientLocality
    run_mode: ShellClientRunMode
    active_client: ShellClientKind
    available_clients: tuple[ShellClientKind, ...]
    active_surface: str
    available_surfaces: tuple[str, ...]
    surface_availability: tuple[ShellClientSurfaceAvailability, ...]
    global_topbar_contract: ShellGlobalTopbarContract
    per_surface_nav_inspector: tuple[ShellSurfaceNavInspectorContract, ...]
    capabilities: tuple[ShellClientCapability, ...]
    command_palette_availability: ShellClientTruthLabel
    truth_labels: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[str, ...]
    local_run_mode: ShellClientRunMode
    limitations: tuple[str, ...]
    state_hash: str


@dataclass(frozen=True)
class ShellClientParityEntry(_CanonicalMixin):
    client_kind: ShellClientKind
    dimension: ShellClientParityDimension
    supported: bool
    truth_label: ShellClientTruthLabel
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    entry_hash: str


@dataclass(frozen=True)
class ShellClientParityMatrix(_CanonicalMixin):
    clients: tuple[ShellClientKind, ...]
    dimensions: tuple[ShellClientParityDimension, ...]
    entries: tuple[ShellClientParityEntry, ...]
    parity_summary: str
    missing_parity: tuple[str, ...]
    no_overclaim_boundaries: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True)
class ShellClientNoOverclaimBoundary(_CanonicalMixin):
    boundary_id: str
    forbidden_claim: str
    reason: str
    active: bool
    evidence_refs: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True)
class P210APrerequisiteGate(_CanonicalMixin):
    p29d_report_found: bool
    p29d_report_path: str
    p29d_report_indexed: bool
    p29d_seals_p29: bool
    p29d_allows_p210a: bool
    gate_status: P210APrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class P210ASideEffectProof(_CanonicalMixin):
    p2_10_b_implemented: bool = False
    p2_10_c_implemented: bool = False
    p2_10_d_implemented: bool = False
    full_web_app_implemented: bool = False
    tauri_desktop_implemented: bool = False
    mobile_app_implemented: bool = False
    arbitrary_command_execution_implemented: bool = False
    command_preflight_behavior_changed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    policy_behavior_changed: bool = False
    identity_behavior_changed: bool = False
    sandbox_behavior_changed: bool = False
    shell_live_claimed: bool = False
    full_local_app_claimed: bool = False
    desktop_runnable_claimed: bool = False
    mobile_runnable_claimed: bool = False


@dataclass(frozen=True)
class P210AResult(_CanonicalMixin):
    covered_pack: str
    prerequisite_gate: P210APrerequisiteGate
    client_states: tuple[ShellClientState, ...]
    parity_matrix: ShellClientParityMatrix
    local_run_modes: tuple[ShellClientLocalRunModeEntry, ...]
    surface_contracts: tuple[ShellClientSurfaceAvailability, ...]
    no_overclaim_boundaries: tuple[ShellClientNoOverclaimBoundary, ...]
    legacy_client_kind_map: dict[str, str]
    p2_vslice_a_truth_label: ShellClientTruthLabel
    next_pack: str
    p210b_ready: bool
    p210b_not_started: bool
    p210c_not_started: bool
    p210d_not_started: bool
    side_effect_proof: P210ASideEffectProof
    result_hash: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _surface_kind_for_id(surface_id: str) -> AurelSurfaceKind:
    for kind, sid in {
        AurelSurfaceKind.AUREL_CRO: "aurel_cro",
        AurelSurfaceKind.HQ: "hq",
        AurelSurfaceKind.CORP: "corp",
        AurelSurfaceKind.HUB: "hub",
        AurelSurfaceKind.IDE: "ide",
        AurelSurfaceKind.SYSTEM: "system",
        AurelSurfaceKind.SETTINGS: "settings",
    }.items():
        if sid == surface_id:
            return kind
    _reject(
        f"unknown surface_id {surface_id}",
        field="surface_id",
        code=AurelShellErrorCode.VALIDATION_ERROR,
    )
    raise AssertionError("unreachable")


def map_shell_client_kind_to_legacy(client_kind: ShellClientKind) -> ClientKind:
    return _LEGACY_CLIENT_KIND_MAP[client_kind]


def build_p2_10_a_prerequisite_gate(
    *,
    p29d_report_exists: bool | None = None,
    p29d_report_indexed: bool | None = None,
) -> P210APrerequisiteGate:
    report_path = _repo_root() / P2_9_D_REPORT_PATH
    if p29d_report_exists is None:
        p29d_report_exists = report_path.is_file()
    if p29d_report_indexed is None:
        reports_index = (_repo_root() / "agent" / "REPORTS.md").read_text(encoding="utf-8")
        p29d_report_indexed = "P2_9_D_SHELL_EXIT_SEAL_FINAL_TAIL" in reports_index

    blockers: list[str] = []
    p29d_seals = False
    p29d_allows = False

    if not p29d_report_exists:
        blockers.append("P2.9-D report missing")
    if not p29d_report_indexed:
        blockers.append("P2.9-D report not indexed")

    if p29d_report_exists:
        p29d = build_p2_9_d_shell_exit_final_seal_result()
        p29d_seals = p29d.p29_done
        p29d_allows = (
            p29d.p210_entry_gate.allowed
            and p29d.handoff_pointer.next_pack == P2_9_D_NEXT_PACK_IF_GATE_PASSES
        )
        if not p29d_seals:
            blockers.append("P2.9-D did not seal P2.9")
        if not p29d_allows:
            blockers.append("P2.9-D did not allow P2.10-A as next pointer")

    if blockers:
        status = P210APrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    else:
        status = P210APrerequisiteGateStatus.GATE_PASSED

    payload = {
        "p29d_report_found": p29d_report_exists,
        "p29d_report_path": P2_9_D_REPORT_PATH,
        "p29d_report_indexed": p29d_report_indexed,
        "p29d_seals_p29": p29d_seals,
        "p29d_allows_p210a": p29d_allows,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P210APrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def build_shell_client_surface_availability(
    registry: AurelSurfaceRegistry | None = None,
) -> tuple[ShellClientSurfaceAvailability, ...]:
    if registry is None:
        registry = build_default_surface_registry()
    contract_clients = (
        ShellClientKind.WEB,
        ShellClientKind.DESKTOP_TAURI,
        ShellClientKind.MOBILE_FOUNDATION,
        ShellClientKind.CLI,
    )
    entries: list[ShellClientSurfaceAvailability] = []
    for surface_id in registry.canonical_surface_ids:
        kind = _surface_kind_for_id(surface_id)
        label = SURFACE_KIND_DISPLAY_NAMES[kind]
        supported = contract_clients
        unsupported = (ShellClientKind.TUI,)
        payload = {
            "surface_id": surface_id,
            "surface_label": label,
            "available": True,
            "truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
            "supported_clients": supported,
            "unsupported_clients": unsupported,
            "evidence_refs": (
                "src/agentic_runtime/aurel_shell/surface_registry.py",
                "src/agentic_runtime/aurel_shell/topbar.py",
            ),
            "limitations": (
                "surface availability is contract-only; not live UI or route execution",
                "TUI client has no surface binding",
            ),
        }
        entries.append(
            ShellClientSurfaceAvailability(
                **payload,
                availability_hash=_hash_payload(payload),
            )
        )
    assert len(entries) == 7
    return tuple(entries)


def build_shell_global_topbar_contract(
    registry: AurelSurfaceRegistry | None = None,
) -> ShellGlobalTopbarContract:
    if registry is None:
        registry = build_default_surface_registry()
    nav = build_no_universal_left_nav_contract()
    topbar_registry = build_default_topbar_surface_registry()
    topbar = build_global_topbar_read_model(registry=topbar_registry)
    selector_ids = tuple(
        sid for sid in registry.canonical_surface_ids if sid in _SURFACE_SELECTOR_IDS
    )
    right_ids = tuple(
        sid for sid in registry.canonical_surface_ids if sid in _TOPBAR_RIGHT_IDS
    )
    payload = {
        "contract_id": "shell_global_topbar_contract_p210a",
        "global_topbar_visible": True,
        "surface_selector_surface_ids": selector_ids,
        "right_side_surface_ids": right_ids,
        "no_universal_left_nav": not nav.global_left_nav_allowed,
        "per_surface_left_nav_required": nav.per_surface_nav_required,
        "per_surface_right_inspector_required": True,
        "truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
        "evidence_refs": (
            "src/agentic_runtime/aurel_shell/topbar.py",
            "src/agentic_runtime/aurel_shell/navigation_boundary.py",
            topbar.read_model_id,
        ),
        "limitations": (
            "global topbar contract is not live UI",
            "surface selector is not route execution",
            "SYSTEM/Settings are right-side topbar slots only",
        ),
    }
    return ShellGlobalTopbarContract(**payload, contract_hash=_hash_payload(payload))


def build_per_surface_nav_inspector_contracts(
    registry: AurelSurfaceRegistry | None = None,
) -> tuple[ShellSurfaceNavInspectorContract, ...]:
    if registry is None:
        registry = build_default_surface_registry()
    nav = build_no_universal_left_nav_contract()
    contracts: list[ShellSurfaceNavInspectorContract] = []
    for surface_id in registry.canonical_surface_ids:
        payload = {
            "surface_id": surface_id,
            "left_nav_owned_by_surface": nav.per_surface_nav_required,
            "right_inspector_owned_by_surface": True,
            "global_left_nav_allowed": nav.global_left_nav_allowed,
            "truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
            "evidence_refs": (
                "src/agentic_runtime/aurel_shell/navigation_boundary.py",
                "src/agentic_runtime/aurel_shell/local_navigation.py",
            ),
            "limitations": (
                "per-surface nav contract is not sidebar UI",
                "right inspector contract is not product panel",
            ),
        }
        contracts.append(
            ShellSurfaceNavInspectorContract(
                **payload,
                contract_hash=_hash_payload(payload),
            )
        )
    return tuple(contracts)


def build_shell_client_local_run_modes() -> tuple[ShellClientLocalRunModeEntry, ...]:
    entries: list[ShellClientLocalRunModeEntry] = []
    backend_payload = {
        "client_kind": None,
        "run_mode": ShellClientRunMode.PYTHON_BACKEND_ONLY,
        "truth_label": ShellClientTruthLabel.READ_ONLY,
        "locally_runnable": False,
        "contract_only": True,
        "launch_command": "",
        "evidence_refs": (P2_10_A_REPORT_PATH,),
        "limitations": ("Python backend contracts are read-only; not Shell LIVE",),
    }
    entries.append(
        ShellClientLocalRunModeEntry(
            **backend_payload,
            entry_hash=_hash_payload({**backend_payload, "scope": "backend"}),
        )
    )
    run_truth = {
        ShellClientKind.WEB: (
            ShellClientRunMode.WEB_DEV_SHELL_CONTRACT,
            ShellClientTruthLabel.CONTRACT_ONLY,
            "no npm run dev scaffold exists",
        ),
        ShellClientKind.DESKTOP_TAURI: (
            ShellClientRunMode.DESKTOP_TAURI_CONTRACT,
            ShellClientTruthLabel.CONTRACT_ONLY,
            "no tauri dev scaffold exists",
        ),
        ShellClientKind.MOBILE_FOUNDATION: (
            ShellClientRunMode.MOBILE_CONTRACT_ONLY,
            ShellClientTruthLabel.CONTRACT_ONLY,
            "mobile is contract-only foundation",
        ),
        ShellClientKind.CLI: (
            ShellClientRunMode.CLI_TUI_CONTRACT,
            ShellClientTruthLabel.READ_ONLY,
            "CLI inspect binding is read-only contract only",
        ),
        ShellClientKind.TUI: (
            ShellClientRunMode.UNAVAILABLE,
            ShellClientTruthLabel.UNAVAILABLE,
            "TUI binding is explicitly UNAVAILABLE",
        ),
    }
    cli_binding = build_shell_cli_binding_contract()
    tui_binding = build_shell_tui_binding_contract()
    for client_kind in _SHELL_CLIENT_KINDS:
        run_mode, truth_label, limitation = run_truth[client_kind]
        locally_runnable = False
        contract_only = truth_label in {
            ShellClientTruthLabel.CONTRACT_ONLY,
            ShellClientTruthLabel.READ_ONLY,
        }
        launch_command = ""
        evidence = [P2_10_A_REPORT_PATH]
        if client_kind is ShellClientKind.CLI:
            evidence.append("src/agentic_runtime/aurel_shell/cli_binding.py")
            if cli_binding.binding_status is not ShellBindingStatus.READ_ONLY_CONTRACT:
                limitation = "CLI binding must remain read-only contract"
        if client_kind is ShellClientKind.TUI:
            evidence.append("src/agentic_runtime/aurel_shell/cli_binding.py")
            if tui_binding.binding_status is not ShellBindingStatus.UNAVAILABLE:
                limitation = "TUI binding must remain UNAVAILABLE"
        payload = {
            "client_kind": client_kind,
            "run_mode": run_mode,
            "truth_label": truth_label,
            "locally_runnable": locally_runnable,
            "contract_only": contract_only,
            "launch_command": launch_command,
            "evidence_refs": tuple(evidence),
            "limitations": (limitation, "no fake launch command claimed"),
        }
        entries.append(
            ShellClientLocalRunModeEntry(**payload, entry_hash=_hash_payload(payload))
        )
    return tuple(entries)


def _parity_truth_for(
    client_kind: ShellClientKind,
    dimension: ShellClientParityDimension,
) -> tuple[bool, ShellClientTruthLabel]:
    if client_kind is ShellClientKind.TUI:
        if dimension in {
            ShellClientParityDimension.CLIENT_LIMITATIONS_VISIBLE,
            ShellClientParityDimension.LOCAL_RUN_MODE_VISIBLE,
        }:
            return True, ShellClientTruthLabel.UNAVAILABLE
        return False, ShellClientTruthLabel.UNAVAILABLE
    if client_kind is ShellClientKind.MOBILE_FOUNDATION:
        if dimension in {
            ShellClientParityDimension.COMMANDS_LIST_VISIBLE,
            ShellClientParityDimension.COMMAND_PREFLIGHT_VISIBLE,
            ShellClientParityDimension.RIGHT_INSPECTOR_CONTRACT_VISIBLE,
            ShellClientParityDimension.LEFT_NAV_CONTRACT_VISIBLE,
        }:
            return False, ShellClientTruthLabel.NOT_STARTED
    if dimension is ShellClientParityDimension.COMMAND_PREFLIGHT_VISIBLE:
        return True, ShellClientTruthLabel.PREFLIGHT_ONLY
    label = (
        ShellClientTruthLabel.READ_ONLY
        if client_kind is ShellClientKind.CLI
        else ShellClientTruthLabel.CONTRACT_ONLY
    )
    return True, label


def build_shell_client_parity_matrix() -> ShellClientParityMatrix:
    entries: list[ShellClientParityEntry] = []
    missing: list[str] = []
    for client_kind in _SHELL_CLIENT_KINDS:
        for dimension in _PARITY_DIMENSIONS:
            supported, truth_label = _parity_truth_for(client_kind, dimension)
            if not supported:
                missing.append(f"{client_kind.value}:{dimension.value}")
            payload = {
                "client_kind": client_kind,
                "dimension": dimension,
                "supported": supported,
                "truth_label": truth_label,
                "evidence_refs": (
                    P2_10_A_REPORT_PATH,
                    "src/agentic_runtime/aurel_shell/multi_client_foundation.py",
                ),
                "limitations": (
                    "parity does not require identical UI",
                    "parity preserves truth labels and evidence refs",
                ),
            }
            entries.append(
                ShellClientParityEntry(**payload, entry_hash=_hash_payload(payload))
            )
    payload = {
        "clients": _SHELL_CLIENT_KINDS,
        "dimensions": _PARITY_DIMENSIONS,
        "entries": tuple(entries),
        "parity_summary": (
            "Client parity means every client preserves the same truth labels, "
            "evidence refs, and availability states — not identical UI."
        ),
        "missing_parity": tuple(missing),
        "no_overclaim_boundaries": tuple(b[0] for b in _NO_OVERCLAIM_BOUNDARIES),
    }
    return ShellClientParityMatrix(**payload, matrix_hash=_hash_payload(payload))


def build_shell_client_no_overclaim_boundaries() -> tuple[ShellClientNoOverclaimBoundary, ...]:
    boundaries: list[ShellClientNoOverclaimBoundary] = []
    for boundary_id, forbidden, reason in _NO_OVERCLAIM_BOUNDARIES:
        payload = {
            "boundary_id": boundary_id,
            "forbidden_claim": forbidden,
            "reason": reason,
            "active": True,
            "evidence_refs": (P2_10_A_REPORT_PATH, P2_9_D_REPORT_PATH),
        }
        boundaries.append(
            ShellClientNoOverclaimBoundary(
                **payload,
                boundary_hash=_hash_payload(payload),
            )
        )
    return tuple(boundaries)


def build_shell_client_state(
    client_kind: ShellClientKind,
    registry: AurelSurfaceRegistry | None = None,
) -> ShellClientState:
    if registry is None:
        registry = build_default_surface_registry()
    surface_availability = build_shell_client_surface_availability(registry)
    topbar = build_shell_global_topbar_contract(registry)
    nav_inspector = build_per_surface_nav_inspector_contracts(registry)
    capabilities = _CLIENT_CAPABILITIES[client_kind]
    active_surface = CANONICAL_SURFACE_ORDER[0]
    payload = {
        "client_kind": client_kind,
        "locality": _CLIENT_LOCALITIES[client_kind],
        "run_mode": _CLIENT_RUN_MODES[client_kind],
        "active_client": client_kind,
        "available_clients": _SHELL_CLIENT_KINDS,
        "active_surface": active_surface,
        "available_surfaces": registry.canonical_surface_ids,
        "surface_availability": surface_availability,
        "global_topbar_contract": topbar,
        "per_surface_nav_inspector": nav_inspector,
        "capabilities": capabilities,
        "command_palette_availability": ShellClientTruthLabel.PREFLIGHT_ONLY,
        "truth_labels": (_CLIENT_TRUTH_LABELS[client_kind], ShellClientTruthLabel.PREFLIGHT_ONLY),
        "evidence_refs": (
            P2_VSLICE_A_REPORT_PATH,
            P2_9_D_REPORT_PATH,
            "src/agentic_runtime/aurel_shell/client_consistency.py",
        ),
        "local_run_mode": _CLIENT_RUN_MODES[client_kind],
        "limitations": (
            "client state is contract read model only",
            "not live frontend or command execution",
            f"legacy ClientKind mapping: {_LEGACY_CLIENT_KIND_MAP[client_kind].value}",
        ),
    }
    return ShellClientState(**payload, state_hash=_hash_payload(payload))


def build_p2_10_a_multi_client_foundation_result(
    *,
    skip_prerequisite_gate: bool = False,
) -> P210AResult:
    gate = build_p2_10_a_prerequisite_gate()
    if not skip_prerequisite_gate:
        assert_p2_10_a_prerequisite_gate_passed(gate)

    registry = build_default_surface_registry()
    build_multi_client_consistency_contract(registry)

    client_states = tuple(
        build_shell_client_state(client_kind, registry) for client_kind in _SHELL_CLIENT_KINDS
    )
    parity_matrix = build_shell_client_parity_matrix()
    local_run_modes = build_shell_client_local_run_modes()
    surface_contracts = build_shell_client_surface_availability(registry)
    no_overclaim = build_shell_client_no_overclaim_boundaries()
    side_effect_proof = P210ASideEffectProof()
    legacy_map = {
        kind.value: _LEGACY_CLIENT_KIND_MAP[kind].value for kind in _SHELL_CLIENT_KINDS
    }

    payload = {
        "covered_pack": P2_10_A_PACK_ID,
        "prerequisite_gate": gate,
        "client_states": client_states,
        "parity_matrix": parity_matrix,
        "local_run_modes": local_run_modes,
        "surface_contracts": surface_contracts,
        "no_overclaim_boundaries": no_overclaim,
        "legacy_client_kind_map": legacy_map,
        "p2_vslice_a_truth_label": ShellClientTruthLabel.PREFLIGHT_ONLY,
        "next_pack": P2_10_A_NEXT_PACK,
        "p210b_ready": True,
        "p210b_not_started": P2_10_B_NOT_STARTED,
        "p210c_not_started": P2_10_C_NOT_STARTED,
        "p210d_not_started": P2_10_D_NOT_STARTED,
        "side_effect_proof": side_effect_proof,
    }
    result = P210AResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_10_a_no_scope_expansion(result)
    assert_p2_vslice_a_remains_preflight_in_p210a(result)
    assert_client_parity_preserves_truth(result)
    return result


def serialize_p2_10_a_result(result: P210AResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_10_a_prerequisite_gate_passed(gate: P210APrerequisiteGate) -> None:
    if gate.gate_status is not P210APrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.10-A cannot proceed unless P2.9-D report exists, is indexed, seals P2.9, "
            "and allows P2.10-A as next pointer",
            field="gate_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_vslice_a_remains_preflight_in_p210a(result: P210AResult) -> None:
    if result.p2_vslice_a_truth_label is not ShellClientTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A must remain PREFLIGHT_ONLY in P2.10-A",
            field="p2_vslice_a_truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    for state in result.client_states:
        if state.command_palette_availability is not ShellClientTruthLabel.PREFLIGHT_ONLY:
            _reject(
                f"{state.client_kind.value} must keep command palette PREFLIGHT_ONLY",
                field="command_palette_availability",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )


def assert_client_parity_preserves_truth(result: P210AResult) -> None:
    for entry in result.parity_matrix.entries:
        if entry.supported and entry.truth_label is ShellClientTruthLabel.LIVE:
            _reject(
                f"{entry.client_kind.value} parity dimension {entry.dimension.value} "
                "must not claim LIVE",
                field="parity_matrix",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )
    if "identical UI" in result.parity_matrix.parity_summary.lower():
        if "not identical" not in result.parity_matrix.parity_summary.lower():
            _reject(
                "parity summary must clarify parity is not identical UI",
                field="parity_summary",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_p2_10_a_no_scope_expansion(result: P210AResult) -> None:
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_10_b_implemented,
            proof.p2_10_c_implemented,
            proof.p2_10_d_implemented,
            proof.full_web_app_implemented,
            proof.tauri_desktop_implemented,
            proof.mobile_app_implemented,
            proof.arbitrary_command_execution_implemented,
            proof.command_preflight_behavior_changed,
            proof.p2_vslice_a_behavior_changed,
            proof.policy_behavior_changed,
            proof.identity_behavior_changed,
            proof.sandbox_behavior_changed,
            proof.shell_live_claimed,
            proof.full_local_app_claimed,
            proof.desktop_runnable_claimed,
            proof.mobile_runnable_claimed,
        )
    ):
        _reject(
            "P2.10-A must not expand into B/C/D, apps, execution, or overclaims",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    for mode in result.local_run_modes:
        if mode.locally_runnable and mode.truth_label is ShellClientTruthLabel.LIVE:
            _reject(
                f"{mode.client_kind.value} must not claim locally runnable LIVE",
                field="local_run_modes",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )
        if mode.launch_command and mode.truth_label is ShellClientTruthLabel.LIVE:
            _reject(
                "launch commands must not accompany LIVE truth labels",
                field="local_run_modes",
                code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
            )


def assert_p2_10_a_no_shell_live_or_execution_claim(result: P210AResult) -> None:
    forbidden = {"Shell LIVE", "command execution", "full local app"}
    for boundary in result.no_overclaim_boundaries:
        if not boundary.active:
            _reject(
                f"boundary {boundary.boundary_id} must remain active",
                field="no_overclaim_boundaries",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    summary = result.parity_matrix.parity_summary
    for claim in forbidden:
        if claim.lower() in summary.lower() and "not" not in summary.lower():
            _reject(
                f"P2.10-A must not claim {claim}",
                field="parity_summary",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
