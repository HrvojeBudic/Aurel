"""P2.11-B surface permission projection / matrix read model.

Projects the P2.11-A permission matrix into deterministic client, surface,
action, evidence, sensitive-surface, and no-overclaim read-model views. This
is inspection/projection only. It does not enforce permissions, execute
commands, implement policy runtime, replace Custos, or claim Shell LIVE.
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
from .multi_client_foundation import ShellClientKind
from .surface_permission_matrix import (
    DISABLED_EXECUTION_ACTIONS,
    P2_11_A_PACK_ID,
    P2_11_A_REPORT_PATH,
    P2_11_B_NEXT_PACK,
    P2_11_B_NEXT_TITLE,
    P2_12_NOT_STARTED,
    SAFE_PRE_EXECUTION_ACTIONS,
    SurfacePermissionAction,
    SurfacePermissionEntry,
    SurfacePermissionLevel,
    SurfacePermissionMatrix,
    SurfacePermissionNoOverclaimBoundary,
    SurfacePermissionReason,
    build_p2_11_a_surface_permission_matrix_result,
    build_surface_permission_matrix,
    surface_permission_entry_lookup,
)

P2_11_B_PACK_ID = "P2.11-B"
P2_11_B_SECTION_ID = "P2.11"
P2_11_B_TITLE = "Surface Permission Projection / Matrix Read Model"
P2_11_B_REPORT_FILENAME = "P2_11_B_SURFACE_PERMISSION_PROJECTION_READ_MODEL.md"
P2_11_B_REPORT_PATH = f"agent/reports/{P2_11_B_REPORT_FILENAME}"
P2_11_B_RESULT_VERSION = "p2_11_b_surface_permission_projection_result.v1"

P2_11_C_NEXT_PACK = "P2.11-C"
P2_11_C_NEXT_TITLE = "Surface Permission Operator Inspection / CLI-Shell View Binding"
P2_11_C_NOT_DONE = True

P2_11_B_TEST_PROJECTION_REF = "tests/test_p211b_surface_permission_projection.py"
P2_11_B_TEST_READ_MODEL_REF = "tests/test_p211b_matrix_read_model.py"
P2_11_B_TEST_NO_EXECUTION_REF = "tests/test_p211b_permission_projection_no_execution.py"
P2_11_B_TEST_HANDOFF_REF = "tests/test_p211b_p211c_handoff.py"

_SENSITIVE_SURFACES: tuple[str, ...] = ("system", "settings", "ide")

_CLIENT_RUN_MODE_LABELS: dict[ShellClientKind, str] = {
    ShellClientKind.WEB: "WEB_DEV_RUNNABLE",
    ShellClientKind.DESKTOP_TAURI: "DESKTOP_TAURI_DEV_RUNNABLE",
    ShellClientKind.CLI: "CLI_READ_ONLY",
    ShellClientKind.TUI: "TUI_CONTRACT_ONLY",
    ShellClientKind.MOBILE_FOUNDATION: "MOBILE_CONTRACT_ONLY",
}

_LEVEL_SUMMARY_KEYS: dict[SurfacePermissionLevel, str] = {
    SurfacePermissionLevel.PREFLIGHT_ONLY: "preflight_only_summary",
    SurfacePermissionLevel.DENIED: "denied_summary",
    SurfacePermissionLevel.UNAVAILABLE: "unavailable_summary",
    SurfacePermissionLevel.FUTURE_GATED: "future_gated_summary",
    SurfacePermissionLevel.CONTRACT_ONLY: "contract_only_summary",
}


class P211BPrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


class SurfacePermissionProjectionKind(str, Enum):
    FULL_MATRIX = "FULL_MATRIX"
    CLIENT_VIEW = "CLIENT_VIEW"
    SURFACE_VIEW = "SURFACE_VIEW"
    ACTION_VIEW = "ACTION_VIEW"
    EVIDENCE_VIEW = "EVIDENCE_VIEW"
    SENSITIVE_SURFACE_VIEW = "SENSITIVE_SURFACE_VIEW"
    NO_OVERCLAIM_VIEW = "NO_OVERCLAIM_VIEW"
    SUMMARY = "SUMMARY"


@dataclass(frozen=True)
class P211BPrerequisiteGate(_CanonicalMixin):
    p211a_report_found: bool
    p211a_report_path: str
    p211a_report_indexed: bool
    p211a_proves_matrix_foundation_done: bool
    p211a_points_to_p211b: bool
    p212_not_started: bool
    gate_status: P211BPrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfacePermissionProjectionEntry(_CanonicalMixin):
    projection_kind: SurfacePermissionProjectionKind
    client_kind: ShellClientKind
    surface_id: str
    permission_action: SurfacePermissionAction
    permission_level: SurfacePermissionLevel
    reason: SurfacePermissionReason
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    source_matrix_ref: str
    source_entry_ref: str
    entry_hash: str


@dataclass(frozen=True)
class SurfacePermissionClientView(_CanonicalMixin):
    client_kind: ShellClientKind
    run_mode: str
    surfaces_visible: tuple[str, ...]
    surfaces_openable: tuple[str, ...]
    surfaces_readable: tuple[str, ...]
    preflight_available_surfaces: tuple[str, ...]
    contract_only_surfaces: tuple[str, ...]
    future_gated_surfaces: tuple[str, ...]
    unavailable_surfaces: tuple[str, ...]
    denied_surfaces: tuple[str, ...]
    sensitive_surface_limitations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class SurfacePermissionSurfaceView(_CanonicalMixin):
    surface_id: str
    clients_with_visibility: tuple[ShellClientKind, ...]
    clients_with_open_access: tuple[ShellClientKind, ...]
    clients_with_read_access: tuple[ShellClientKind, ...]
    clients_with_preflight_only: tuple[ShellClientKind, ...]
    clients_contract_only: tuple[ShellClientKind, ...]
    clients_future_gated: tuple[ShellClientKind, ...]
    clients_unavailable: tuple[ShellClientKind, ...]
    clients_denied: tuple[ShellClientKind, ...]
    sensitive_surface_flag: bool
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class SurfacePermissionActionView(_CanonicalMixin):
    permission_action: SurfacePermissionAction
    allowed_clients_surfaces: tuple[str, ...]
    read_only_clients_surfaces: tuple[str, ...]
    preflight_only_clients_surfaces: tuple[str, ...]
    contract_only_clients_surfaces: tuple[str, ...]
    future_gated_clients_surfaces: tuple[str, ...]
    denied_clients_surfaces: tuple[str, ...]
    unavailable_clients_surfaces: tuple[str, ...]
    error_clients_surfaces: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class SurfacePermissionEvidenceView(_CanonicalMixin):
    source_pack: str
    source_report: str
    source_commit: str
    source_test: str
    source_object: str
    entries_supported: tuple[str, ...]
    entries_with_no_evidence: tuple[str, ...]
    notes: str
    view_hash: str


@dataclass(frozen=True)
class SurfacePermissionNoOverclaimView(_CanonicalMixin):
    boundaries: tuple[SurfacePermissionNoOverclaimBoundary, ...]
    active_boundaries: tuple[SurfacePermissionNoOverclaimBoundary, ...]
    violations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class SurfacePermissionProjectionSummary(_CanonicalMixin):
    total_entries: int
    client_view_count: int
    surface_view_count: int
    action_view_count: int
    evidence_ref_count: int
    no_evidence_count: int
    preflight_only_count: int
    denied_count: int
    unavailable_count: int
    future_gated_count: int
    contract_only_count: int
    error_count: int
    sensitive_surface_summary: tuple[str, ...]
    execution_disabled_summary: tuple[str, ...]
    summary_hash: str


@dataclass(frozen=True)
class SurfacePermissionReadModel(_CanonicalMixin):
    source_matrix_ref: str
    source_pack_refs: tuple[str, ...]
    clients: tuple[ShellClientKind, ...]
    surfaces: tuple[str, ...]
    safe_actions: tuple[SurfacePermissionAction, ...]
    disabled_actions: tuple[SurfacePermissionAction, ...]
    entries: tuple[SurfacePermissionProjectionEntry, ...]
    client_views: tuple[SurfacePermissionClientView, ...]
    surface_views: tuple[SurfacePermissionSurfaceView, ...]
    action_views: tuple[SurfacePermissionActionView, ...]
    sensitive_surface_views: tuple[SurfacePermissionSurfaceView, ...]
    preflight_only_summary: tuple[str, ...]
    denied_summary: tuple[str, ...]
    unavailable_summary: tuple[str, ...]
    future_gated_summary: tuple[str, ...]
    contract_only_summary: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    no_overclaim_boundaries: tuple[SurfacePermissionNoOverclaimBoundary, ...]
    next_pack_pointer: str
    read_model_hash: str


@dataclass(frozen=True)
class P211BHandoff(_CanonicalMixin):
    next_pack: str
    next_title: str
    handoff_status: str
    projection_summary: tuple[str, ...]
    operator_view_needs: tuple[str, ...]
    cli_shell_binding_needs: tuple[str, ...]
    remaining_risks: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class P211BSideEffectProof(_CanonicalMixin):
    p2_11_c_implemented: bool = False
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
    permission_enforcement_implemented: bool = False
    full_policy_runtime_implemented: bool = False
    custos_enforcement_implemented: bool = False
    p2_vslice_a_behavior_changed: bool = False
    shell_live_claimed: bool = False
    product_readiness_claimed: bool = False


@dataclass(frozen=True)
class P211BResult(_CanonicalMixin):
    covered_pack: str
    source_matrix_ref: str
    read_model: SurfacePermissionReadModel
    projection_summary: SurfacePermissionProjectionSummary
    no_overclaim_view: SurfacePermissionNoOverclaimView
    handoff: P211BHandoff
    side_effect_proof: P211BSideEffectProof
    p211c_not_done: bool
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


def _p211a_report_proves_done() -> bool:
    report_path = _repo_root() / P2_11_A_REPORT_PATH
    if not report_path.is_file():
        return False
    text = report_path.read_text(encoding="utf-8")
    return (
        "**Status:** DONE" in text
        and "Surface Permission Matrix Foundation" in text
        and "P2.11-B is next" in text
    )


def _p211a_points_to_p211b() -> bool:
    report_path = _repo_root() / P2_11_A_REPORT_PATH
    if not report_path.is_file():
        return False
    text = report_path.read_text(encoding="utf-8")
    return P2_11_B_NEXT_PACK in text and P2_11_B_NEXT_TITLE in text


def build_p2_11_b_prerequisite_gate(
    *,
    p211a_report_exists: bool | None = None,
    p211a_report_indexed: bool | None = None,
    p212_not_started: bool | None = None,
) -> P211BPrerequisiteGate:
    report_path = _repo_root() / P2_11_A_REPORT_PATH
    if p211a_report_exists is None:
        p211a_report_exists = report_path.is_file()
    if p211a_report_indexed is None:
        p211a_report_indexed = _report_index_contains(
            "P2_11_A_SURFACE_PERMISSION_MATRIX_FOUNDATION"
        )
    if p212_not_started is None:
        p212_not_started = _p212_not_started() and P2_12_NOT_STARTED

    blockers: list[str] = []
    p211a_proves_done = False
    p211a_points_to_p211b = False

    if not p211a_report_exists:
        blockers.append("P2.11-A report missing")
    if not p211a_report_indexed:
        blockers.append("P2.11-A report not indexed")
    if not p212_not_started:
        blockers.append("P2.12+ appears started")

    if p211a_report_exists:
        p211a_proves_done = _p211a_report_proves_done()
        p211a_points_to_p211b = _p211a_points_to_p211b()
        if not p211a_proves_done:
            blockers.append("P2.11-A did not prove permission matrix foundation DONE")
        if not p211a_points_to_p211b:
            blockers.append("P2.11-A did not point next to P2.11-B")
        try:
            p211a = build_p2_11_a_surface_permission_matrix_result()
            if p211a.covered_pack != P2_11_A_PACK_ID:
                blockers.append("P2.11-A result pack mismatch")
            if p211a.handoff.next_pack != P2_11_B_NEXT_PACK:
                blockers.append("P2.11-A handoff does not point to P2.11-B")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.11-A matrix result failed: {exc}")

    status = (
        P211BPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
        if blockers
        else P211BPrerequisiteGateStatus.GATE_PASSED
    )
    payload = {
        "p211a_report_found": p211a_report_exists,
        "p211a_report_path": P2_11_A_REPORT_PATH,
        "p211a_report_indexed": p211a_report_indexed,
        "p211a_proves_matrix_foundation_done": p211a_proves_done,
        "p211a_points_to_p211b": p211a_points_to_p211b,
        "p212_not_started": p212_not_started,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P211BPrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def _client_surface_key(client: ShellClientKind, surface_id: str) -> str:
    return f"{client.value}:{surface_id}"


def _evidence_ref_strings(
    entry: SurfacePermissionEntry,
) -> tuple[str, ...]:
    return tuple(ref.ref_hash for ref in entry.evidence_refs)


def _projection_entry_from_matrix_entry(
    matrix: SurfacePermissionMatrix,
    entry: SurfacePermissionEntry,
    *,
    projection_kind: SurfacePermissionProjectionKind = SurfacePermissionProjectionKind.FULL_MATRIX,
) -> SurfacePermissionProjectionEntry:
    payload = {
        "projection_kind": projection_kind,
        "client_kind": entry.client_kind,
        "surface_id": entry.surface_id,
        "permission_action": entry.permission_action,
        "permission_level": entry.permission_level,
        "reason": entry.reason,
        "evidence_refs": _evidence_ref_strings(entry),
        "limitations": entry.limitations,
        "source_matrix_ref": matrix.matrix_hash,
        "source_entry_ref": entry.entry_hash,
    }
    return SurfacePermissionProjectionEntry(
        **payload,
        entry_hash=_hash_payload(payload),
    )


def project_permissions_by_client(
    matrix: SurfacePermissionMatrix,
) -> tuple[SurfacePermissionClientView, ...]:
    views: list[SurfacePermissionClientView] = []
    for client in matrix.clients:
        visible: list[str] = []
        openable: list[str] = []
        readable: list[str] = []
        preflight: list[str] = []
        contract_only: list[str] = []
        future_gated: list[str] = []
        unavailable: list[str] = []
        denied: list[str] = []
        sensitive_limits: list[str] = []
        evidence: set[str] = set()

        for surface_id in matrix.surfaces:
            see = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.SEE_SURFACE,
            )
            open_entry = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.OPEN_SURFACE,
            )
            read_entry = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.READ_SURFACE_STATE,
            )
            preflight_entry = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
            )

            for ref in see.evidence_refs:
                evidence.add(ref.ref_hash)

            level = see.permission_level
            if level is SurfacePermissionLevel.DENIED:
                denied.append(surface_id)
            elif level is SurfacePermissionLevel.UNAVAILABLE:
                unavailable.append(surface_id)
            elif level is SurfacePermissionLevel.CONTRACT_ONLY:
                contract_only.append(surface_id)
                visible.append(surface_id)
            elif level is SurfacePermissionLevel.FUTURE_GATED:
                future_gated.append(surface_id)
                visible.append(surface_id)
            else:
                visible.append(surface_id)

            if open_entry.permission_level is SurfacePermissionLevel.ALLOWED:
                openable.append(surface_id)
            if read_entry.permission_level in {
                SurfacePermissionLevel.ALLOWED,
                SurfacePermissionLevel.READ_ONLY,
            }:
                readable.append(surface_id)
            if preflight_entry.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY:
                preflight.append(surface_id)
            if preflight_entry.permission_level is SurfacePermissionLevel.FUTURE_GATED:
                if surface_id not in future_gated:
                    future_gated.append(surface_id)

            if surface_id in _SENSITIVE_SURFACES:
                sensitive_limits.extend(
                    limitation
                    for limitation in see.limitations
                    if "sensitive" in limitation.lower()
                )

        payload = {
            "client_kind": client,
            "run_mode": _CLIENT_RUN_MODE_LABELS[client],
            "surfaces_visible": tuple(visible),
            "surfaces_openable": tuple(openable),
            "surfaces_readable": tuple(readable),
            "preflight_available_surfaces": tuple(preflight),
            "contract_only_surfaces": tuple(contract_only),
            "future_gated_surfaces": tuple(future_gated),
            "unavailable_surfaces": tuple(unavailable),
            "denied_surfaces": tuple(denied),
            "sensitive_surface_limitations": tuple(dict.fromkeys(sensitive_limits)),
            "evidence_refs": tuple(sorted(evidence)),
            "limitations": (
                "client view is projection only; not permission enforcement",
                "ALLOWED/READ_ONLY/PREFLIGHT_ONLY do not grant final authorization",
                f"{client.value} run mode preserved from P2.10/P2.11-A baseline",
            ),
        }
        views.append(
            SurfacePermissionClientView(**payload, view_hash=_hash_payload(payload))
        )
    return tuple(views)


def project_permissions_by_surface(
    matrix: SurfacePermissionMatrix,
) -> tuple[SurfacePermissionSurfaceView, ...]:
    views: list[SurfacePermissionSurfaceView] = []
    for surface_id in matrix.surfaces:
        with_visibility: list[ShellClientKind] = []
        with_open: list[ShellClientKind] = []
        with_read: list[ShellClientKind] = []
        with_preflight: list[ShellClientKind] = []
        contract_only: list[ShellClientKind] = []
        future_gated: list[ShellClientKind] = []
        unavailable: list[ShellClientKind] = []
        denied: list[ShellClientKind] = []
        evidence: set[str] = set()

        for client in matrix.clients:
            see = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.SEE_SURFACE,
            )
            open_entry = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.OPEN_SURFACE,
            )
            read_entry = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.READ_SURFACE_STATE,
            )
            preflight_entry = surface_permission_entry_lookup(
                matrix,
                client_kind=client,
                surface_id=surface_id,
                permission_action=SurfacePermissionAction.REQUEST_COMMAND_PREFLIGHT,
            )
            for ref in see.evidence_refs:
                evidence.add(ref.ref_hash)

            level = see.permission_level
            if level is SurfacePermissionLevel.DENIED:
                denied.append(client)
            elif level is SurfacePermissionLevel.UNAVAILABLE:
                unavailable.append(client)
            elif level is SurfacePermissionLevel.CONTRACT_ONLY:
                contract_only.append(client)
                with_visibility.append(client)
            elif level is SurfacePermissionLevel.FUTURE_GATED:
                future_gated.append(client)
                with_visibility.append(client)
            else:
                with_visibility.append(client)

            if open_entry.permission_level is SurfacePermissionLevel.ALLOWED:
                with_open.append(client)
            if read_entry.permission_level in {
                SurfacePermissionLevel.ALLOWED,
                SurfacePermissionLevel.READ_ONLY,
            }:
                with_read.append(client)
            if preflight_entry.permission_level is SurfacePermissionLevel.PREFLIGHT_ONLY:
                with_preflight.append(client)

        limitations = (
            "surface view is projection only; not permission enforcement",
            "sensitive surfaces remain conservative where flagged",
        )
        if surface_id in _SENSITIVE_SURFACES:
            limitations += (
                "sensitive surface: mutation/runtime/sandbox/execution remain denied",
            )

        payload = {
            "surface_id": surface_id,
            "clients_with_visibility": tuple(with_visibility),
            "clients_with_open_access": tuple(with_open),
            "clients_with_read_access": tuple(with_read),
            "clients_with_preflight_only": tuple(with_preflight),
            "clients_contract_only": tuple(contract_only),
            "clients_future_gated": tuple(future_gated),
            "clients_unavailable": tuple(unavailable),
            "clients_denied": tuple(denied),
            "sensitive_surface_flag": surface_id in _SENSITIVE_SURFACES,
            "evidence_refs": tuple(sorted(evidence)),
            "limitations": limitations,
        }
        views.append(
            SurfacePermissionSurfaceView(**payload, view_hash=_hash_payload(payload))
        )
    return tuple(views)


def project_permissions_by_action(
    matrix: SurfacePermissionMatrix,
) -> tuple[SurfacePermissionActionView, ...]:
    views: list[SurfacePermissionActionView] = []
    for action in matrix.actions:
        allowed: list[str] = []
        read_only: list[str] = []
        preflight_only: list[str] = []
        contract_only: list[str] = []
        future_gated: list[str] = []
        denied: list[str] = []
        unavailable: list[str] = []
        error: list[str] = []
        evidence: set[str] = set()

        for entry in matrix.entries:
            if entry.permission_action is not action:
                continue
            key = _client_surface_key(entry.client_kind, entry.surface_id)
            for ref in entry.evidence_refs:
                evidence.add(ref.ref_hash)
            level = entry.permission_level
            if level is SurfacePermissionLevel.ALLOWED:
                allowed.append(key)
            elif level is SurfacePermissionLevel.READ_ONLY:
                read_only.append(key)
            elif level is SurfacePermissionLevel.PREFLIGHT_ONLY:
                preflight_only.append(key)
            elif level is SurfacePermissionLevel.CONTRACT_ONLY:
                contract_only.append(key)
            elif level is SurfacePermissionLevel.FUTURE_GATED:
                future_gated.append(key)
            elif level is SurfacePermissionLevel.DENIED:
                denied.append(key)
            elif level is SurfacePermissionLevel.UNAVAILABLE:
                unavailable.append(key)
            elif level is SurfacePermissionLevel.ERROR:
                error.append(key)

        payload = {
            "permission_action": action,
            "allowed_clients_surfaces": tuple(sorted(allowed)),
            "read_only_clients_surfaces": tuple(sorted(read_only)),
            "preflight_only_clients_surfaces": tuple(sorted(preflight_only)),
            "contract_only_clients_surfaces": tuple(sorted(contract_only)),
            "future_gated_clients_surfaces": tuple(sorted(future_gated)),
            "denied_clients_surfaces": tuple(sorted(denied)),
            "unavailable_clients_surfaces": tuple(sorted(unavailable)),
            "error_clients_surfaces": tuple(sorted(error)),
            "evidence_refs": tuple(sorted(evidence)),
            "limitations": (
                "action view is projection only; not execution or enforcement",
                "PREFLIGHT_ONLY means governed preflight request only",
                "ALLOWED does not mean final authorization",
            ),
        }
        views.append(
            SurfacePermissionActionView(**payload, view_hash=_hash_payload(payload))
        )
    return tuple(views)


def build_surface_permission_evidence_views(
    matrix: SurfacePermissionMatrix,
) -> tuple[SurfacePermissionEvidenceView, ...]:
    views: list[SurfacePermissionEvidenceView] = []
    for ref in matrix.evidence_refs:
        supported: list[str] = []
        no_evidence: list[str] = []
        for entry in matrix.entries:
            key = f"{entry.client_kind.value}:{entry.surface_id}:{entry.permission_action.value}"
            entry_refs = {ev.ref_hash for ev in entry.evidence_refs}
            if ref.ref_hash in entry_refs:
                supported.append(key)
            if (
                entry.reason is SurfacePermissionReason.NO_EVIDENCE
                or not entry.evidence_refs
            ):
                no_evidence.append(key)

        payload = {
            "source_pack": ref.source_pack,
            "source_report": ref.source_report,
            "source_commit": ref.source_commit,
            "source_test": ref.source_test,
            "source_object": ref.source_object,
            "entries_supported": tuple(sorted(dict.fromkeys(supported))),
            "entries_with_no_evidence": tuple(sorted(dict.fromkeys(no_evidence))),
            "notes": ref.notes,
        }
        views.append(
            SurfacePermissionEvidenceView(**payload, view_hash=_hash_payload(payload))
        )
    return tuple(views)


def build_surface_permission_no_overclaim_view(
    matrix: SurfacePermissionMatrix,
) -> SurfacePermissionNoOverclaimView:
    boundaries = tuple(SurfacePermissionNoOverclaimBoundary)
    violations: list[str] = []
    for entry in matrix.entries:
        if entry.permission_action in DISABLED_EXECUTION_ACTIONS:
            if entry.permission_level in {
                SurfacePermissionLevel.ALLOWED,
                SurfacePermissionLevel.PREFLIGHT_ONLY,
                SurfacePermissionLevel.READ_ONLY,
            }:
                violations.append(
                    f"{entry.client_kind.value}:{entry.surface_id}:{entry.permission_action.value}"
                )
    evidence = tuple(ref.ref_hash for ref in matrix.evidence_refs)
    payload = {
        "boundaries": boundaries,
        "active_boundaries": boundaries,
        "violations": tuple(violations),
        "evidence_refs": evidence,
    }
    return SurfacePermissionNoOverclaimView(
        **payload,
        view_hash=_hash_payload(payload),
    )


def _level_summary_entries(
    matrix: SurfacePermissionMatrix,
    level: SurfacePermissionLevel,
) -> tuple[str, ...]:
    keys = [
        f"{entry.client_kind.value}:{entry.surface_id}:{entry.permission_action.value}"
        for entry in matrix.entries
        if entry.permission_level is level
    ]
    return tuple(sorted(keys))


def _build_projection_summary(
    matrix: SurfacePermissionMatrix,
    *,
    client_views: tuple[SurfacePermissionClientView, ...],
    surface_views: tuple[SurfacePermissionSurfaceView, ...],
    action_views: tuple[SurfacePermissionActionView, ...],
) -> SurfacePermissionProjectionSummary:
    no_evidence = sum(
        1
        for entry in matrix.entries
        if entry.reason is SurfacePermissionReason.NO_EVIDENCE
        or not entry.evidence_refs
    )
    sensitive_entries = [
        entry for entry in matrix.entries if entry.surface_id in _SENSITIVE_SURFACES
    ]
    denied_execution = [
        entry
        for entry in matrix.entries
        if entry.permission_action in DISABLED_EXECUTION_ACTIONS
        and entry.permission_level
        in {
            SurfacePermissionLevel.DENIED,
            SurfacePermissionLevel.UNAVAILABLE,
            SurfacePermissionLevel.FUTURE_GATED,
        }
    ]
    payload = {
        "total_entries": len(matrix.entries),
        "client_view_count": len(client_views),
        "surface_view_count": len(surface_views),
        "action_view_count": len(action_views),
        "evidence_ref_count": len(matrix.evidence_refs),
        "no_evidence_count": no_evidence,
        "preflight_only_count": matrix.summary.preflight_only_count,
        "denied_count": matrix.summary.denied_count,
        "unavailable_count": matrix.summary.unavailable_count,
        "future_gated_count": matrix.summary.future_gated_count,
        "contract_only_count": matrix.summary.contract_only_count,
        "error_count": matrix.summary.error_count,
        "sensitive_surface_summary": (
            f"{len(sensitive_entries)} sensitive-surface matrix entries projected",
            "SYSTEM, Settings, and IDE remain conservative in projection views",
        ),
        "execution_disabled_summary": (
            f"{len(denied_execution)} disabled execution entries remain non-executable",
            "projection does not upgrade PREFLIGHT_ONLY to execution",
        ),
    }
    return SurfacePermissionProjectionSummary(
        **payload,
        summary_hash=_hash_payload(payload),
    )


def build_surface_permission_read_model(
    matrix: SurfacePermissionMatrix | None = None,
) -> SurfacePermissionReadModel:
    if matrix is None:
        matrix = build_surface_permission_matrix()

    projection_entries = tuple(
        _projection_entry_from_matrix_entry(matrix, entry)
        for entry in matrix.entries
    )
    client_views = project_permissions_by_client(matrix)
    surface_views = project_permissions_by_surface(matrix)
    action_views = project_permissions_by_action(matrix)
    sensitive_surface_views = tuple(
        view for view in surface_views if view.sensitive_surface_flag
    )

    source_pack_refs = tuple(
        dict.fromkeys(
            ref.source_pack
            for ref in matrix.evidence_refs
        ).keys()
    )
    evidence_ref_hashes = tuple(ref.ref_hash for ref in matrix.evidence_refs)

    payload = {
        "source_matrix_ref": matrix.matrix_hash,
        "source_pack_refs": source_pack_refs,
        "clients": matrix.clients,
        "surfaces": matrix.surfaces,
        "safe_actions": SAFE_PRE_EXECUTION_ACTIONS,
        "disabled_actions": DISABLED_EXECUTION_ACTIONS,
        "entries": projection_entries,
        "client_views": client_views,
        "surface_views": surface_views,
        "action_views": action_views,
        "sensitive_surface_views": sensitive_surface_views,
        "preflight_only_summary": _level_summary_entries(
            matrix, SurfacePermissionLevel.PREFLIGHT_ONLY
        ),
        "denied_summary": _level_summary_entries(matrix, SurfacePermissionLevel.DENIED),
        "unavailable_summary": _level_summary_entries(
            matrix, SurfacePermissionLevel.UNAVAILABLE
        ),
        "future_gated_summary": _level_summary_entries(
            matrix, SurfacePermissionLevel.FUTURE_GATED
        ),
        "contract_only_summary": _level_summary_entries(
            matrix, SurfacePermissionLevel.CONTRACT_ONLY
        ),
        "evidence_refs": evidence_ref_hashes,
        "limitations": (
            "P2.11-B read model is projection/inspection only",
            "projection is not enforcement; read model is not execution",
            "PREFLIGHT_ONLY remains non-execution",
            "ALLOWED does not mean final authorization",
        ),
        "no_overclaim_boundaries": tuple(SurfacePermissionNoOverclaimBoundary),
        "next_pack_pointer": P2_11_C_NEXT_PACK,
    }
    read_model = SurfacePermissionReadModel(
        **payload,
        read_model_hash=_hash_payload(payload),
    )
    assert_surface_permission_read_model_complete(read_model, matrix)
    assert_surface_permission_read_model_no_execution_upgrade(read_model, matrix)
    return read_model


def serialize_surface_permission_read_model(
    read_model: SurfacePermissionReadModel,
) -> str:
    return to_canonical_json(read_model.to_canonical_dict())


def build_p2_11_b_handoff(
    read_model: SurfacePermissionReadModel | None = None,
    summary: SurfacePermissionProjectionSummary | None = None,
) -> P211BHandoff:
    if read_model is None:
        read_model = build_surface_permission_read_model()
    if summary is None:
        summary = _build_projection_summary(
            build_surface_permission_matrix(),
            client_views=read_model.client_views,
            surface_views=read_model.surface_views,
            action_views=read_model.action_views,
        )
    payload = {
        "next_pack": P2_11_C_NEXT_PACK,
        "next_title": P2_11_C_NEXT_TITLE,
        "handoff_status": "P2.11-C next; operator inspection/CLI binding not implemented in P2.11-B",
        "projection_summary": (
            f"{summary.total_entries} matrix entries projected",
            f"{summary.client_view_count} client views, {summary.surface_view_count} surface views, {summary.action_view_count} action views",
            "P2.11 as a whole is not complete",
        ),
        "operator_view_needs": (
            "CLI/TUI operator-facing permission inspection commands",
            "filter/group permission read model by client/surface/action",
            "display sensitive-surface limitations and no-execution boundaries",
        ),
        "cli_shell_binding_needs": (
            "bind read model to `python -m agentic_runtime.cli shell` inspect path",
            "stable JSON export for permission projection entries",
            "preserve read-only/no-execution contract from P2.10-D",
        ),
        "remaining_risks": (
            "P2.11-C not implemented",
            "P2.12 truth-label fixture discipline not implemented",
            "projection is not runtime enforcement or Custos authorization",
            "mobile remains contract-only/future-gated",
        ),
    }
    return P211BHandoff(**payload, handoff_hash=_hash_payload(payload))


def build_p2_11_b_surface_permission_projection_result(
    *,
    assert_gate: bool = True,
) -> P211BResult:
    gate = build_p2_11_b_prerequisite_gate()
    if assert_gate and gate.gate_status is not P211BPrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.11-B prerequisite gate did not pass",
            field="prerequisite_gate",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    matrix = build_surface_permission_matrix()
    read_model = build_surface_permission_read_model(matrix)
    summary = _build_projection_summary(
        matrix,
        client_views=read_model.client_views,
        surface_views=read_model.surface_views,
        action_views=read_model.action_views,
    )
    no_overclaim = build_surface_permission_no_overclaim_view(matrix)
    handoff = build_p2_11_b_handoff(read_model, summary)
    side_effects = P211BSideEffectProof()
    payload = {
        "covered_pack": P2_11_B_PACK_ID,
        "source_matrix_ref": matrix.matrix_hash,
        "read_model": read_model,
        "projection_summary": summary,
        "no_overclaim_view": no_overclaim,
        "handoff": handoff,
        "side_effect_proof": side_effects,
        "p211c_not_done": P2_11_C_NOT_DONE,
        "p212_not_started": P2_12_NOT_STARTED,
    }
    result = P211BResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_11_b_no_scope_expansion(result)
    return result


def serialize_p2_11_b_result(result: P211BResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_surface_permission_read_model_complete(
    read_model: SurfacePermissionReadModel,
    matrix: SurfacePermissionMatrix,
) -> None:
    if read_model.source_matrix_ref != matrix.matrix_hash:
        _reject(
            "read model must reference source matrix hash",
            field="source_matrix_ref",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if len(read_model.client_views) != len(matrix.clients):
        _reject(
            "read model must include all client views",
            field="client_views",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if len(read_model.surface_views) != len(matrix.surfaces):
        _reject(
            "read model must include all surface views",
            field="surface_views",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if len(read_model.action_views) != len(matrix.actions):
        _reject(
            "read model must include all action views",
            field="action_views",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if len(read_model.sensitive_surface_views) != len(_SENSITIVE_SURFACES):
        _reject(
            "read model must include all sensitive surface views",
            field="sensitive_surface_views",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if read_model.next_pack_pointer != P2_11_C_NEXT_PACK:
        _reject(
            "read model must point next to P2.11-C",
            field="next_pack_pointer",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_surface_permission_read_model_no_execution_upgrade(
    read_model: SurfacePermissionReadModel,
    matrix: SurfacePermissionMatrix,
) -> None:
    for action_view in read_model.action_views:
        if action_view.permission_action in DISABLED_EXECUTION_ACTIONS:
            assert not action_view.allowed_clients_surfaces
            assert not action_view.preflight_only_clients_surfaces
            assert not action_view.read_only_clients_surfaces

    for entry in matrix.entries:
        proj = next(
            e
            for e in read_model.entries
            if e.source_entry_ref == entry.entry_hash
        )
        if proj.permission_level != entry.permission_level:
            _reject(
                "projection must not upgrade permission level",
                field="permission_level",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


def assert_p2_11_b_no_scope_expansion(result: P211BResult) -> None:
    proof = result.side_effect_proof
    if any(proof.to_canonical_dict().values()):
        _reject(
            "P2.11-B side-effect proof must keep all execution/enforcement claims false",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.handoff.next_pack != P2_11_C_NEXT_PACK:
        _reject(
            "P2.11-B must hand off to P2.11-C",
            field="handoff.next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.no_overclaim_view.violations:
        _reject(
            "no-overclaim view must not report violations in P2.11-B projection",
            field="no_overclaim_view.violations",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


P2_11_B_VALIDATION_REFS: tuple[str, ...] = (
    P2_11_B_TEST_PROJECTION_REF,
    P2_11_B_TEST_READ_MODEL_REF,
    P2_11_B_TEST_NO_EXECUTION_REF,
    P2_11_B_TEST_HANDOFF_REF,
)
