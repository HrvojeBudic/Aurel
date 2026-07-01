"""P2.10-B local web Shell skeleton / contract-bound client read model.

Derives a Python-owned WebShellReadModel from P2.10-A ShellClientState for
minimal TypeScript web skeleton consumption. Python owns Aurel truth;
TypeScript renders contracts only.

Does not implement Tauri desktop, mobile app, CLI/TUI parity, command execution,
Shell LIVE, production API server, or full API/event bridge live path.
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
    P2_10_A_NEXT_PACK,
    P2_10_A_REPORT_PATH,
    P2_10_C_NOT_STARTED,
    P2_10_D_NOT_STARTED,
    ShellClientKind,
    ShellClientTruthLabel,
    build_p2_10_a_multi_client_foundation_result,
    build_shell_client_state,
)
from .shell_exit_readiness import P2_VSLICE_A_REPORT_PATH

P2_10_B_PACK_ID = "P2.10-B"
P2_10_B_SECTION_ID = "P2.10"
P2_10_B_COVERED_RANGE = "P2.10-B"
P2_10_B_NEXT_PACK = "P2.10-C"
P2_10_B_REPORT_FILENAME = "P2_10_B_LOCAL_WEB_SHELL_SKELETON.md"
P2_10_B_REPORT_PATH = f"agent/reports/{P2_10_B_REPORT_FILENAME}"
P2_10_B_RESULT_VERSION = "p2_10_b_web_shell_read_model_result.v1"
P2_10_B_TEST_READ_MODEL_REF = "tests/test_p210b_web_shell_read_model.py"
P2_10_B_TEST_BINDING_REF = "tests/test_p210b_web_shell_contract_binding.py"
P2_10_B_WEB_ROOT = "web/shell"
P2_10_B_FIXTURE_REL_PATH = f"{P2_10_B_WEB_ROOT}/public/web-shell-read-model.json"
P2_10_B_WEB_LAUNCH_COMMAND = "npm run dev"
P2_10_B_WEB_LOCALLY_RUNNABLE = True
P2_10_E_NOT_STARTED = True


class P210BPrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


@dataclass(frozen=True)
class WebShellEvidenceRef(_CanonicalMixin):
    ref_id: str
    label: str
    path: str
    truth_label: ShellClientTruthLabel
    ref_hash: str


@dataclass(frozen=True)
class WebShellSurfaceView(_CanonicalMixin):
    surface_id: str
    surface_label: str
    available: bool
    truth_label: ShellClientTruthLabel
    in_surface_selector: bool
    in_topbar_right: bool
    left_nav_owned_by_surface: bool
    right_inspector_owned_by_surface: bool
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class WebShellClientStatus(_CanonicalMixin):
    active_client: ShellClientKind
    available_clients: tuple[ShellClientKind, ...]
    client_truth_label: ShellClientTruthLabel
    local_run_mode: str
    locally_runnable: bool
    launch_command: str
    launch_working_directory: str
    skeleton_truth_label: ShellClientTruthLabel
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    status_hash: str


@dataclass(frozen=True)
class WebShellNoOverclaimView(_CanonicalMixin):
    boundary_id: str
    forbidden_claim: str
    reason: str
    active: bool
    evidence_refs: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class WebShellReadModel(_CanonicalMixin):
    pack_id: str
    title: str
    client_status: WebShellClientStatus
    surfaces: tuple[WebShellSurfaceView, ...]
    truth_labels: tuple[ShellClientTruthLabel, ...]
    evidence_refs: tuple[WebShellEvidenceRef, ...]
    command_palette_availability: ShellClientTruthLabel
    p2_vslice_a_status: ShellClientTruthLabel
    local_run_mode: str
    limitations: tuple[str, ...]
    no_overclaim_boundaries: tuple[WebShellNoOverclaimView, ...]
    next_pack: str
    p210c_not_started: bool
    p210d_not_started: bool
    p210e_not_started: bool
    fixture_rel_path: str
    read_model_hash: str


@dataclass(frozen=True)
class P210BPrerequisiteGate(_CanonicalMixin):
    p210a_report_found: bool
    p210a_report_path: str
    p210a_report_indexed: bool
    p210a_proves_multi_client_done: bool
    p210a_points_to_p210b: bool
    p210c_not_started: bool
    p210d_not_started: bool
    gate_status: P210BPrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class P210BSideEffectProof(_CanonicalMixin):
    p2_10_c_implemented: bool = False
    p2_10_d_implemented: bool = False
    p2_10_e_implemented: bool = False
    tauri_desktop_implemented: bool = False
    mobile_app_implemented: bool = False
    cli_tui_parity_implemented: bool = False
    arbitrary_command_execution_implemented: bool = False
    command_preflight_behavior_changed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    policy_behavior_changed: bool = False
    identity_behavior_changed: bool = False
    sandbox_behavior_changed: bool = False
    production_api_server_implemented: bool = False
    full_api_event_bridge_live_implemented: bool = False
    shell_live_claimed: bool = False
    full_local_app_claimed: bool = False
    desktop_runnable_claimed: bool = False
    mobile_runnable_claimed: bool = False


@dataclass(frozen=True)
class P210BResult(_CanonicalMixin):
    covered_pack: str
    prerequisite_gate: P210BPrerequisiteGate
    read_model: WebShellReadModel
    source_client_state_hash: str
    side_effect_proof: P210BSideEffectProof
    next_pack: str
    result_hash: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_p2_10_b_prerequisite_gate(
    *,
    p210a_report_exists: bool | None = None,
    p210a_report_indexed: bool | None = None,
) -> P210BPrerequisiteGate:
    report_path = _repo_root() / P2_10_A_REPORT_PATH
    if p210a_report_exists is None:
        p210a_report_exists = report_path.is_file()
    if p210a_report_indexed is None:
        reports_index = (_repo_root() / "agent" / "REPORTS.md").read_text(encoding="utf-8")
        p210a_report_indexed = "P2_10_A_MULTI_CLIENT_SHELL_FOUNDATION" in reports_index

    blockers: list[str] = []
    p210a_proves_done = False
    p210a_points_to_b = False

    if not p210a_report_exists:
        blockers.append("P2.10-A report missing")
    if not p210a_report_indexed:
        blockers.append("P2.10-A report not indexed")

    if p210a_report_exists:
        try:
            p210a = build_p2_10_a_multi_client_foundation_result()
            p210a_proves_done = (
                p210a.covered_pack == "P2.10-A"
                and len(p210a.client_states) == 5
                and p210a.p210b_ready is True
            )
            p210a_points_to_b = p210a.next_pack == P2_10_A_NEXT_PACK == "P2.10-B"
            if not p210a_proves_done:
                blockers.append("P2.10-A did not prove multi-client foundation DONE")
            if not p210a_points_to_b:
                blockers.append("P2.10-A did not point next to P2.10-B")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.10-A foundation result failed: {exc}")

    if blockers:
        status = P210BPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
    else:
        status = P210BPrerequisiteGateStatus.GATE_PASSED

    payload = {
        "p210a_report_found": p210a_report_exists,
        "p210a_report_path": P2_10_A_REPORT_PATH,
        "p210a_report_indexed": p210a_report_indexed,
        "p210a_proves_multi_client_done": p210a_proves_done,
        "p210a_points_to_p210b": p210a_points_to_b,
        "p210c_not_started": P2_10_C_NOT_STARTED,
        "p210d_not_started": P2_10_D_NOT_STARTED,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P210BPrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def _build_web_shell_evidence_refs(
    client_state_evidence: tuple[str, ...],
) -> tuple[WebShellEvidenceRef, ...]:
    refs: list[WebShellEvidenceRef] = []
    for idx, path in enumerate(client_state_evidence):
        payload = {
            "ref_id": f"web_shell_evidence_{idx}",
            "label": Path(path).name if "/" in path else path,
            "path": path,
            "truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
        }
        refs.append(WebShellEvidenceRef(**payload, ref_hash=_hash_payload(payload)))
    fixture_payload = {
        "ref_id": "web_shell_fixture",
        "label": "web-shell-read-model.json",
        "path": P2_10_B_FIXTURE_REL_PATH,
        "truth_label": ShellClientTruthLabel.DEV_FIXTURE,
    }
    refs.append(
        WebShellEvidenceRef(**fixture_payload, ref_hash=_hash_payload(fixture_payload))
    )
    return tuple(refs)


def _build_web_shell_surface_views(
    client_state: object,
) -> tuple[WebShellSurfaceView, ...]:
    topbar = client_state.global_topbar_contract  # type: ignore[attr-defined]
    selector_ids = set(topbar.surface_selector_surface_ids)
    right_ids = set(topbar.right_side_surface_ids)
    nav_by_surface = {
        c.surface_id: c for c in client_state.per_surface_nav_inspector  # type: ignore[attr-defined]
    }
    availability_by_surface = {
        s.surface_id: s for s in client_state.surface_availability  # type: ignore[attr-defined]
    }
    views: list[WebShellSurfaceView] = []
    for surface_id in client_state.available_surfaces:  # type: ignore[attr-defined]
        avail = availability_by_surface[surface_id]
        nav = nav_by_surface[surface_id]
        payload = {
            "surface_id": surface_id,
            "surface_label": avail.surface_label,
            "available": avail.available,
            "truth_label": avail.truth_label,
            "in_surface_selector": surface_id in selector_ids,
            "in_topbar_right": surface_id in right_ids,
            "left_nav_owned_by_surface": nav.left_nav_owned_by_surface,
            "right_inspector_owned_by_surface": nav.right_inspector_owned_by_surface,
            "evidence_refs": avail.evidence_refs,
            "limitations": avail.limitations
            + ("web skeleton renders placeholder only; not full surface UI",),
        }
        views.append(WebShellSurfaceView(**payload, view_hash=_hash_payload(payload)))
    return tuple(views)


def build_web_shell_read_model(
    *,
    locally_runnable: bool | None = None,
    launch_command: str | None = None,
) -> WebShellReadModel:
    if locally_runnable is None:
        locally_runnable = P2_10_B_WEB_LOCALLY_RUNNABLE
    if launch_command is None:
        launch_command = P2_10_B_WEB_LAUNCH_COMMAND if locally_runnable else ""
    client_state = build_shell_client_state(ShellClientKind.WEB)
    surfaces = _build_web_shell_surface_views(client_state)
    evidence_refs = _build_web_shell_evidence_refs(client_state.evidence_refs)

    skeleton_label = (
        ShellClientTruthLabel.DEV_FIXTURE
        if locally_runnable
        else ShellClientTruthLabel.READ_ONLY
    )
    client_payload = {
        "active_client": ShellClientKind.WEB,
        "available_clients": client_state.available_clients,
        "client_truth_label": ShellClientTruthLabel.CONTRACT_ONLY,
        "local_run_mode": client_state.local_run_mode.value,
        "locally_runnable": locally_runnable,
        "launch_command": launch_command,
        "launch_working_directory": P2_10_B_WEB_ROOT if locally_runnable else "",
        "skeleton_truth_label": skeleton_label,
        "evidence_refs": client_state.evidence_refs + (P2_10_B_REPORT_PATH,),
        "limitations": client_state.limitations
        + (
            "web shell skeleton is contract-bound read model rendering only",
            "generated static JSON is not live backend",
            "runnable skeleton does not equal Shell LIVE or full local app",
        ),
    }
    client_status = WebShellClientStatus(
        **client_payload,
        status_hash=_hash_payload(client_payload),
    )

    no_overclaim: list[WebShellNoOverclaimView] = []
    boundaries = (
        ("NO_SHELL_LIVE_CLAIM", "Shell LIVE", "Shell LIVE is not claimed in P2.10-B"),
        (
            "NO_COMMAND_EXECUTION_CLAIM",
            "arbitrary command execution",
            "Command execution UI/actions are forbidden",
        ),
        (
            "NO_FULL_LOCAL_APP_CLAIM",
            "full local app complete",
            "Local web skeleton is not full local app",
        ),
        (
            "NO_DESKTOP_APP_CLAIM",
            "desktop app runnable",
            "Tauri desktop belongs to P2.10-C",
        ),
        (
            "NO_MOBILE_APP_CLAIM",
            "mobile app runnable",
            "Mobile app belongs to future packs",
        ),
        (
            "NO_PRODUCTION_API_CLAIM",
            "production API server",
            "No production API server in P2.10-B",
        ),
        (
            "NO_P2_10_C_D_E_CLAIM",
            "P2.10-C/D/E done",
            "Only P2.10-B web skeleton; C/D/E remain NOT_DONE",
        ),
    )
    for boundary_id, forbidden, reason in boundaries:
        payload = {
            "boundary_id": boundary_id,
            "forbidden_claim": forbidden,
            "reason": reason,
            "active": True,
            "evidence_refs": (P2_10_B_REPORT_PATH, P2_10_A_REPORT_PATH),
        }
        no_overclaim.append(
            WebShellNoOverclaimView(**payload, view_hash=_hash_payload(payload))
        )

    truth_labels = (
        skeleton_label,
        ShellClientTruthLabel.CONTRACT_ONLY,
        ShellClientTruthLabel.PREFLIGHT_ONLY,
        ShellClientTruthLabel.NOT_STARTED,
    )

    payload = {
        "pack_id": P2_10_B_PACK_ID,
        "title": "Aurel Shell Local Web Skeleton",
        "client_status": client_status,
        "surfaces": surfaces,
        "truth_labels": truth_labels,
        "evidence_refs": evidence_refs,
        "command_palette_availability": client_state.command_palette_availability,
        "p2_vslice_a_status": ShellClientTruthLabel.PREFLIGHT_ONLY,
        "local_run_mode": client_state.local_run_mode.value,
        "limitations": client_status.limitations,
        "no_overclaim_boundaries": tuple(no_overclaim),
        "next_pack": P2_10_B_NEXT_PACK,
        "p210c_not_started": P2_10_C_NOT_STARTED,
        "p210d_not_started": P2_10_D_NOT_STARTED,
        "p210e_not_started": P2_10_E_NOT_STARTED,
        "fixture_rel_path": P2_10_B_FIXTURE_REL_PATH,
    }
    return WebShellReadModel(**payload, read_model_hash=_hash_payload(payload))


def build_p2_10_b_web_shell_result(
    *,
    skip_prerequisite_gate: bool = False,
    locally_runnable: bool = False,
    launch_command: str = "",
) -> P210BResult:
    gate = build_p2_10_b_prerequisite_gate()
    if not skip_prerequisite_gate:
        assert_p2_10_b_prerequisite_gate_passed(gate)

    client_state = build_shell_client_state(ShellClientKind.WEB)
    read_model = build_web_shell_read_model(
        locally_runnable=locally_runnable,
        launch_command=launch_command,
    )
    side_effect_proof = P210BSideEffectProof()
    payload = {
        "covered_pack": P2_10_B_PACK_ID,
        "prerequisite_gate": gate,
        "read_model": read_model,
        "source_client_state_hash": client_state.state_hash,
        "side_effect_proof": side_effect_proof,
        "next_pack": P2_10_B_NEXT_PACK,
    }
    result = P210BResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_10_b_no_scope_expansion(result)
    assert_p2_vslice_a_remains_preflight_in_p210b(result)
    assert_web_shell_derives_from_p210a(result)
    return result


def serialize_web_shell_read_model(read_model: WebShellReadModel) -> str:
    return to_canonical_json(read_model.to_canonical_dict())


def serialize_p2_10_b_result(result: P210BResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def export_web_shell_read_model_fixture(
    output_path: Path | None = None,
    *,
    locally_runnable: bool | None = None,
    launch_command: str | None = None,
) -> Path:
    read_model = build_web_shell_read_model(
        locally_runnable=locally_runnable,
        launch_command=launch_command,
    )
    if output_path is None:
        output_path = _repo_root() / P2_10_B_FIXTURE_REL_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_web_shell_read_model(read_model), encoding="utf-8")
    return output_path


def assert_p2_10_b_prerequisite_gate_passed(gate: P210BPrerequisiteGate) -> None:
    if gate.gate_status is not P210BPrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.10-B cannot proceed unless P2.10-A report exists, is indexed, "
            "proves multi-client foundation DONE, and points to P2.10-B",
            field="gate_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_vslice_a_remains_preflight_in_p210b(result: P210BResult) -> None:
    rm = result.read_model
    if rm.p2_vslice_a_status is not ShellClientTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A must remain PREFLIGHT_ONLY in P2.10-B",
            field="p2_vslice_a_status",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if rm.command_palette_availability is not ShellClientTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "command palette must remain PREFLIGHT_ONLY in P2.10-B",
            field="command_palette_availability",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_web_shell_derives_from_p210a(result: P210BResult) -> None:
    web_state = build_shell_client_state(ShellClientKind.WEB)
    rm = result.read_model
    if rm.client_status.active_client is not ShellClientKind.WEB:
        _reject(
            "web read model active client must be WEB",
            field="active_client",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    contract_surfaces = set(web_state.available_surfaces)
    read_surfaces = {s.surface_id for s in rm.surfaces}
    if read_surfaces != contract_surfaces:
        _reject(
            "web read model surfaces must match P2.10-A ShellClientState",
            field="surfaces",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )
    if result.source_client_state_hash != web_state.state_hash:
        _reject(
            "source client state hash must match current WEB ShellClientState",
            field="source_client_state_hash",
            code=AurelShellErrorCode.SOURCE_OF_TRUTH_VIOLATION,
        )


def assert_p2_10_b_no_scope_expansion(result: P210BResult) -> None:
    proof = result.side_effect_proof
    if any(
        (
            proof.p2_10_c_implemented,
            proof.p2_10_d_implemented,
            proof.p2_10_e_implemented,
            proof.tauri_desktop_implemented,
            proof.mobile_app_implemented,
            proof.cli_tui_parity_implemented,
            proof.arbitrary_command_execution_implemented,
            proof.command_preflight_behavior_changed,
            proof.p2_vslice_a_behavior_changed,
            proof.policy_behavior_changed,
            proof.identity_behavior_changed,
            proof.sandbox_behavior_changed,
            proof.production_api_server_implemented,
            proof.full_api_event_bridge_live_implemented,
            proof.shell_live_claimed,
            proof.full_local_app_claimed,
            proof.desktop_runnable_claimed,
            proof.mobile_runnable_claimed,
        )
    ):
        _reject(
            "P2.10-B must not expand into C/D/E, desktop, mobile, execution, or overclaims",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    rm = result.read_model
    if rm.next_pack != "P2.10-C":
        _reject(
            "P2.10-B next pack must be P2.10-C",
            field="next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if not rm.p210c_not_started:
        _reject(
            "P2.10-C must remain not started",
            field="p210c_not_started",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_10_b_no_shell_live_or_execution_claim(result: P210BResult) -> None:
    rm = result.read_model
    for boundary in rm.no_overclaim_boundaries:
        if not boundary.active:
            _reject(
                f"boundary {boundary.boundary_id} must remain active",
                field="no_overclaim_boundaries",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    if ShellClientTruthLabel.LIVE in rm.truth_labels:
        _reject(
            "P2.10-B must not include LIVE truth label",
            field="truth_labels",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if P2_VSLICE_A_REPORT_PATH not in rm.client_status.evidence_refs:
        _reject(
            "P2.VSLICE-A evidence ref must be preserved",
            field="evidence_refs",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
