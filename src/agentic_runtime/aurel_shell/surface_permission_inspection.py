"""P2.11-C surface permission operator inspection / CLI-Shell view binding.

Provides read-only operator inspection over the P2.11-B permission read model.
Inspection is visibility only. It does not enforce permissions, execute
commands, implement policy runtime, replace Custos, claim Shell LIVE, or
claim product readiness.
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
    P2_12_NOT_STARTED,
    SurfacePermissionAction,
    SurfacePermissionLevel,
    SurfacePermissionReason,
)
from .surface_permission_projection import (
    P2_11_B_PACK_ID,
    P2_11_B_REPORT_PATH,
    P2_11_C_NEXT_PACK,
    P2_11_C_NEXT_TITLE,
    SurfacePermissionActionView,
    SurfacePermissionClientView,
    SurfacePermissionEvidenceView,
    SurfacePermissionNoOverclaimView,
    SurfacePermissionProjectionEntry,
    SurfacePermissionReadModel,
    SurfacePermissionSurfaceView,
    build_p2_11_b_surface_permission_projection_result,
    build_surface_permission_evidence_views,
    build_surface_permission_no_overclaim_view,
    build_surface_permission_read_model,
    serialize_surface_permission_read_model,
)

P2_11_C_PACK_ID = "P2.11-C"
P2_11_C_SECTION_ID = "P2.11"
P2_11_C_TITLE = "Surface Permission Operator Inspection / CLI-Shell View Binding"
P2_11_C_REPORT_FILENAME = "P2_11_C_SURFACE_PERMISSION_OPERATOR_INSPECTION.md"
P2_11_C_REPORT_PATH = f"agent/reports/{P2_11_C_REPORT_FILENAME}"
P2_11_C_RESULT_VERSION = "p2_11_c_surface_permission_inspection_result.v1"

P2_11_D_NEXT_PACK = "P2.11-D"
P2_11_D_NEXT_TITLE = (
    "Surface Permission Inspection Parity / Evidence Consistency Gate"
)
P2_11_D_NOT_DONE = True

P2_11_C_TEST_INSPECTION_REF = "tests/test_p211c_surface_permission_inspection.py"
P2_11_C_TEST_FILTERS_REF = "tests/test_p211c_permission_inspection_filters.py"
P2_11_C_TEST_CLI_SHELL_REF = "tests/test_p211c_cli_shell_view_binding.py"
P2_11_C_TEST_NO_EXECUTION_REF = (
    "tests/test_p211c_permission_inspection_no_execution.py"
)
P2_11_C_TEST_HANDOFF_REF = "tests/test_p211c_p211d_handoff.py"

_SENSITIVE_SURFACES: tuple[str, ...] = ("system", "settings", "ide")

_SHELL_PANEL_IDS: tuple[str, ...] = (
    "PermissionSummaryPanel",
    "PermissionClientViewPanel",
    "PermissionSurfaceViewPanel",
    "PermissionActionViewPanel",
    "PermissionEvidencePanel",
    "PermissionSensitiveSurfacePanel",
    "PermissionNoOverclaimPanel",
)


class P211CPrerequisiteGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"
    GATE_REPAIR_REQUIRED = "GATE_REPAIR_REQUIRED"


class SurfacePermissionInspectionViewKind(str, Enum):
    SUMMARY = "SUMMARY"
    TABLE = "TABLE"
    JSON = "JSON"
    DETAIL = "DETAIL"
    REPORT = "REPORT"


@dataclass(frozen=True)
class P211CPrerequisiteGate(_CanonicalMixin):
    p211b_report_found: bool
    p211b_report_path: str
    p211b_report_indexed: bool
    p211b_proves_projection_read_model_done: bool
    p211b_points_to_p211c: bool
    p212_not_started: bool
    gate_status: P211CPrerequisiteGateStatus
    blockers: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class SurfacePermissionInspectionQuery(_CanonicalMixin):
    client_kind: ShellClientKind | None = None
    surface_id: str | None = None
    permission_action: SurfacePermissionAction | None = None
    permission_level: SurfacePermissionLevel | None = None
    reason: SurfacePermissionReason | None = None
    evidence_status: str | None = None
    sensitive_only: bool = False
    no_evidence_only: bool = False
    denied_only: bool = False
    future_gated_only: bool = False
    contract_only_only: bool = False
    unavailable_only: bool = False
    preflight_only_only: bool = False
    include_evidence: bool = True
    include_limitations: bool = True
    include_no_overclaim: bool = True
    format: SurfacePermissionInspectionViewKind = SurfacePermissionInspectionViewKind.SUMMARY


@dataclass(frozen=True)
class SurfacePermissionInspectionFilter(_CanonicalMixin):
    clients: tuple[ShellClientKind, ...] = ()
    surfaces: tuple[str, ...] = ()
    actions: tuple[SurfacePermissionAction, ...] = ()
    permission_levels: tuple[SurfacePermissionLevel, ...] = ()
    reasons: tuple[SurfacePermissionReason, ...] = ()
    evidence_statuses: tuple[str, ...] = ()
    sensitive_only: bool = False
    no_evidence_only: bool = False
    denied_only: bool = False
    future_gated_only: bool = False
    contract_only_only: bool = False
    unavailable_only: bool = False
    preflight_only_only: bool = False


@dataclass(frozen=True)
class SurfacePermissionInspectionNoExecutionProof(_CanonicalMixin):
    command_execution: bool = False
    tool_execution: bool = False
    approval_execution: bool = False
    runtime_control: bool = False
    sandbox_control: bool = False
    memory_write: bool = False
    policy_mutation: bool = False
    identity_mutation: bool = False
    permission_enforcement: bool = False
    full_policy_runtime: bool = False
    custos_enforcement: bool = False
    shell_live_claim: bool = False
    product_readiness_claim: bool = False
    violations: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SurfacePermissionInspectionView(_CanonicalMixin):
    view_kind: SurfacePermissionInspectionViewKind
    title: str
    rows: tuple[str, ...]
    summary: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    truth_notes: tuple[str, ...]
    view_hash: str


@dataclass(frozen=True)
class SurfacePermissionInspectionResult(_CanonicalMixin):
    query: SurfacePermissionInspectionQuery
    matched_entries: tuple[SurfacePermissionProjectionEntry, ...]
    matched_client_views: tuple[SurfacePermissionClientView, ...]
    matched_surface_views: tuple[SurfacePermissionSurfaceView, ...]
    matched_action_views: tuple[SurfacePermissionActionView, ...]
    matched_evidence_views: tuple[SurfacePermissionEvidenceView, ...]
    matched_no_overclaim_views: tuple[SurfacePermissionNoOverclaimView, ...]
    summary: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    no_execution_proof: SurfacePermissionInspectionNoExecutionProof
    result_hash: str


@dataclass(frozen=True)
class SurfacePermissionCliCommandSpec(_CanonicalMixin):
    command_name: str
    description: str
    arguments: tuple[str, ...]
    read_only: bool
    source_read_model: str
    output_format: str
    forbidden_side_effects: tuple[str, ...]
    no_execution_boundaries: tuple[str, ...]
    spec_hash: str


@dataclass(frozen=True)
class SurfacePermissionShellViewBinding(_CanonicalMixin):
    panel_id: str
    panel_title: str
    source_read_model: str
    supported_filters: tuple[str, ...]
    supported_views: tuple[SurfacePermissionInspectionViewKind, ...]
    read_only: bool
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    no_execution_boundaries: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True)
class SurfacePermissionInspectionExport(_CanonicalMixin):
    format: str
    source_read_model: str
    export_payload: str
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    read_only: bool
    deterministic: bool
    json_safe: bool
    export_hash: str


@dataclass(frozen=True)
class P211CHandoff(_CanonicalMixin):
    next_pack: str
    next_title: str
    handoff_status: str
    inspection_summary: tuple[str, ...]
    parity_validation_needs: tuple[str, ...]
    evidence_consistency_needs: tuple[str, ...]
    remaining_risks: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class P211CSideEffectProof(_CanonicalMixin):
    p2_11_d_implemented: bool = False
    p2_11_claimed_complete: bool = False
    p2_12_plus_implemented: bool = False
    p2_final_seal_claimed: bool = False
    p3_handoff_claimed: bool = False
    command_execution_implemented: bool = False
    tool_execution_implemented: bool = False
    approval_execution_implemented: bool = False
    runtime_control_implemented: bool = False
    sandbox_control_implemented: bool = False
    memory_write_implemented: bool = False
    policy_mutation_implemented: bool = False
    identity_mutation_implemented: bool = False
    permission_enforcement_implemented: bool = False
    full_policy_runtime_implemented: bool = False
    custos_enforcement_implemented: bool = False
    p2_vslice_a_behavior_changed: bool = False
    preflight_only_upgraded_to_execution: bool = False
    allowed_upgraded_to_final_authorization: bool = False
    shell_live_claimed: bool = False
    product_readiness_claimed: bool = False


@dataclass(frozen=True)
class P211CResult(_CanonicalMixin):
    covered_pack: str
    inspection_contract: tuple[str, ...]
    query_filter_model: tuple[str, ...]
    inspection_views: tuple[SurfacePermissionInspectionViewKind, ...]
    cli_command_specs: tuple[SurfacePermissionCliCommandSpec, ...]
    shell_view_binding: tuple[SurfacePermissionShellViewBinding, ...]
    inspection_export: SurfacePermissionInspectionExport
    no_execution_proof: SurfacePermissionInspectionNoExecutionProof
    handoff: P211CHandoff
    p211d_not_done: bool
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
    source_started = any(
        (root / "src" / "agentic_runtime" / "aurel_shell").glob("*p212*")
    )
    test_started = any((root / "tests").glob("test_p212*"))
    return not report_started and not source_started and not test_started


def _p211b_report_proves_done() -> bool:
    report_path = _repo_root() / P2_11_B_REPORT_PATH
    if not report_path.is_file():
        return False
    text = report_path.read_text(encoding="utf-8")
    return (
        "**Status:** DONE" in text
        and "Surface Permission Projection / Matrix Read Model" in text
        and "P2.11-C is next" in text
    )


def _p211b_points_to_p211c() -> bool:
    report_path = _repo_root() / P2_11_B_REPORT_PATH
    if not report_path.is_file():
        return False
    text = report_path.read_text(encoding="utf-8")
    return P2_11_C_NEXT_PACK in text and P2_11_C_NEXT_TITLE in text


def build_p2_11_c_prerequisite_gate(
    *,
    p211b_report_exists: bool | None = None,
    p211b_report_indexed: bool | None = None,
    p212_not_started: bool | None = None,
) -> P211CPrerequisiteGate:
    report_path = _repo_root() / P2_11_B_REPORT_PATH
    if p211b_report_exists is None:
        p211b_report_exists = report_path.is_file()
    if p211b_report_indexed is None:
        p211b_report_indexed = _report_index_contains(
            "P2_11_B_SURFACE_PERMISSION_PROJECTION_READ_MODEL"
        )
    if p212_not_started is None:
        p212_not_started = _p212_not_started() and P2_12_NOT_STARTED

    blockers: list[str] = []
    p211b_proves_done = False
    p211b_points_to_p211c = False

    if not p211b_report_exists:
        blockers.append("P2.11-B report missing")
    if not p211b_report_indexed:
        blockers.append("P2.11-B report not indexed")
    if not p212_not_started:
        blockers.append("P2.12+ appears started")

    if p211b_report_exists:
        p211b_proves_done = _p211b_report_proves_done()
        p211b_points_to_p211c = _p211b_points_to_p211c()
        if not p211b_proves_done:
            blockers.append(
                "P2.11-B did not prove permission projection/read model DONE"
            )
        if not p211b_points_to_p211c:
            blockers.append("P2.11-B did not point next to P2.11-C")
        try:
            p211b = build_p2_11_b_surface_permission_projection_result()
            if p211b.covered_pack != P2_11_B_PACK_ID:
                blockers.append("P2.11-B result pack mismatch")
            if p211b.handoff.next_pack != P2_11_C_NEXT_PACK:
                blockers.append("P2.11-B handoff does not point to P2.11-C")
        except (ValueError, AssertionError) as exc:
            blockers.append(f"P2.11-B projection result failed: {exc}")

    status = (
        P211CPrerequisiteGateStatus.GATE_REPAIR_REQUIRED
        if blockers
        else P211CPrerequisiteGateStatus.GATE_PASSED
    )
    payload = {
        "p211b_report_found": p211b_report_exists,
        "p211b_report_path": P2_11_B_REPORT_PATH,
        "p211b_report_indexed": p211b_report_indexed,
        "p211b_proves_projection_read_model_done": p211b_proves_done,
        "p211b_points_to_p211c": p211b_points_to_p211c,
        "p212_not_started": p212_not_started,
        "gate_status": status,
        "blockers": tuple(blockers),
    }
    return P211CPrerequisiteGate(**payload, gate_hash=_hash_payload(payload))


def build_surface_permission_inspection_filter(
    query: SurfacePermissionInspectionQuery,
) -> SurfacePermissionInspectionFilter:
    clients = (query.client_kind,) if query.client_kind is not None else ()
    surfaces = (query.surface_id,) if query.surface_id is not None else ()
    actions = (
        (query.permission_action,) if query.permission_action is not None else ()
    )
    levels = (
        (query.permission_level,) if query.permission_level is not None else ()
    )
    reasons = (query.reason,) if query.reason is not None else ()
    evidence_statuses = (
        (query.evidence_status,) if query.evidence_status is not None else ()
    )
    payload = {
        "clients": clients,
        "surfaces": surfaces,
        "actions": actions,
        "permission_levels": levels,
        "reasons": reasons,
        "evidence_statuses": evidence_statuses,
        "sensitive_only": query.sensitive_only,
        "no_evidence_only": query.no_evidence_only,
        "denied_only": query.denied_only,
        "future_gated_only": query.future_gated_only,
        "contract_only_only": query.contract_only_only,
        "unavailable_only": query.unavailable_only,
        "preflight_only_only": query.preflight_only_only,
    }
    return SurfacePermissionInspectionFilter(**payload)


def _entry_has_no_evidence(entry: SurfacePermissionProjectionEntry) -> bool:
    return (
        entry.reason is SurfacePermissionReason.NO_EVIDENCE
        or not entry.evidence_refs
    )


def _entry_matches_filter(
    entry: SurfacePermissionProjectionEntry,
    filter_model: SurfacePermissionInspectionFilter,
) -> bool:
    if filter_model.clients and entry.client_kind not in filter_model.clients:
        return False
    if filter_model.surfaces and entry.surface_id not in filter_model.surfaces:
        return False
    if filter_model.actions and entry.permission_action not in filter_model.actions:
        return False
    if (
        filter_model.permission_levels
        and entry.permission_level not in filter_model.permission_levels
    ):
        return False
    if filter_model.reasons and entry.reason not in filter_model.reasons:
        return False
    if filter_model.evidence_statuses:
        status = (
            "NO_EVIDENCE"
            if _entry_has_no_evidence(entry)
            else "EVIDENCE_PRESENT"
        )
        if status not in filter_model.evidence_statuses:
            return False
    if filter_model.sensitive_only and entry.surface_id not in _SENSITIVE_SURFACES:
        return False
    if filter_model.no_evidence_only and not _entry_has_no_evidence(entry):
        return False
    if (
        filter_model.denied_only
        and entry.permission_level is not SurfacePermissionLevel.DENIED
    ):
        return False
    if (
        filter_model.future_gated_only
        and entry.permission_level is not SurfacePermissionLevel.FUTURE_GATED
    ):
        return False
    if (
        filter_model.contract_only_only
        and entry.permission_level is not SurfacePermissionLevel.CONTRACT_ONLY
    ):
        return False
    if (
        filter_model.unavailable_only
        and entry.permission_level is not SurfacePermissionLevel.UNAVAILABLE
    ):
        return False
    if (
        filter_model.preflight_only_only
        and entry.permission_level is not SurfacePermissionLevel.PREFLIGHT_ONLY
    ):
        return False
    return True


def filter_surface_permission_read_model(
    read_model: SurfacePermissionReadModel,
    filter_model: SurfacePermissionInspectionFilter,
) -> tuple[SurfacePermissionProjectionEntry, ...]:
    return tuple(
        entry
        for entry in read_model.entries
        if _entry_matches_filter(entry, filter_model)
    )


def build_surface_permission_inspection_no_execution_proof(
    read_model: SurfacePermissionReadModel | None = None,
) -> SurfacePermissionInspectionNoExecutionProof:
    if read_model is None:
        read_model = build_surface_permission_read_model()
    violations: list[str] = []
    for entry in read_model.entries:
        if entry.permission_action in {
            SurfacePermissionAction.EXECUTE_COMMAND,
            SurfacePermissionAction.RUN_TOOL,
            SurfacePermissionAction.APPROVE_ACTION,
        }:
            if entry.permission_level in {
                SurfacePermissionLevel.ALLOWED,
                SurfacePermissionLevel.PREFLIGHT_ONLY,
            }:
                violations.append(
                    f"{entry.client_kind.value}:{entry.surface_id}:"
                    f"{entry.permission_action.value}"
                )
    return SurfacePermissionInspectionNoExecutionProof(
        evidence_refs=read_model.evidence_refs,
        violations=tuple(violations),
    )


def _matched_client_views(
    read_model: SurfacePermissionReadModel,
    filter_model: SurfacePermissionInspectionFilter,
) -> tuple[SurfacePermissionClientView, ...]:
    if not filter_model.clients:
        return read_model.client_views
    return tuple(
        view
        for view in read_model.client_views
        if view.client_kind in filter_model.clients
    )


def _matched_surface_views(
    read_model: SurfacePermissionReadModel,
    filter_model: SurfacePermissionInspectionFilter,
) -> tuple[SurfacePermissionSurfaceView, ...]:
    views = read_model.surface_views
    if filter_model.sensitive_only:
        views = read_model.sensitive_surface_views
    if filter_model.surfaces:
        views = tuple(view for view in views if view.surface_id in filter_model.surfaces)
    return views


def _matched_action_views(
    read_model: SurfacePermissionReadModel,
    filter_model: SurfacePermissionInspectionFilter,
) -> tuple[SurfacePermissionActionView, ...]:
    if not filter_model.actions:
        return read_model.action_views
    return tuple(
        view
        for view in read_model.action_views
        if view.permission_action in filter_model.actions
    )


def inspect_surface_permissions(
    query: SurfacePermissionInspectionQuery | None = None,
    *,
    read_model: SurfacePermissionReadModel | None = None,
) -> SurfacePermissionInspectionResult:
    if query is None:
        query = SurfacePermissionInspectionQuery()
    if read_model is None:
        read_model = build_surface_permission_read_model()

    filter_model = build_surface_permission_inspection_filter(query)
    matched_entries = filter_surface_permission_read_model(read_model, filter_model)
    from .surface_permission_matrix import build_surface_permission_matrix

    matrix = build_surface_permission_matrix()
    evidence_views = build_surface_permission_evidence_views(matrix)
    no_overclaim = build_surface_permission_no_overclaim_view(matrix)

    matched_evidence = evidence_views
    if query.no_evidence_only or (
        query.evidence_status == "NO_EVIDENCE"
    ):
        matched_evidence = tuple(
            view
            for view in evidence_views
            if view.entries_with_no_evidence
        )

    matched_no_overclaim = (no_overclaim,) if query.include_no_overclaim else ()

    evidence_refs: set[str] = set()
    for entry in matched_entries:
        evidence_refs.update(entry.evidence_refs)
    if query.include_evidence:
        evidence_refs.update(read_model.evidence_refs)

    limitations = (
        "P2.11-C inspection is read-only visibility over P2.11-B read model",
        "inspection is not enforcement; CLI/Shell binding is not execution",
        "PREFLIGHT_ONLY remains non-execution",
        "ALLOWED does not mean final authorization",
    )
    if query.include_limitations:
        limitations += read_model.limitations

    summary = (
        f"{len(matched_entries)} matched projection entries",
        f"{len(_matched_client_views(read_model, filter_model))} client views",
        f"{len(_matched_surface_views(read_model, filter_model))} surface views",
        f"{len(_matched_action_views(read_model, filter_model))} action views",
        "inspection does not mutate source read model",
    )

    no_execution_proof = build_surface_permission_inspection_no_execution_proof(
        read_model
    )
    payload = {
        "query": query,
        "matched_entries": matched_entries,
        "matched_client_views": _matched_client_views(read_model, filter_model),
        "matched_surface_views": _matched_surface_views(read_model, filter_model),
        "matched_action_views": _matched_action_views(read_model, filter_model),
        "matched_evidence_views": matched_evidence,
        "matched_no_overclaim_views": matched_no_overclaim,
        "summary": summary,
        "evidence_refs": tuple(sorted(evidence_refs)),
        "limitations": limitations,
        "no_execution_proof": no_execution_proof,
    }
    return SurfacePermissionInspectionResult(
        **payload,
        result_hash=_hash_payload(payload),
    )


def render_surface_permission_inspection(
    result: SurfacePermissionInspectionResult,
    *,
    view_kind: SurfacePermissionInspectionViewKind | None = None,
) -> SurfacePermissionInspectionView:
    kind = view_kind or result.query.format
    rows: list[str] = []
    truth_notes = (
        "inspection is visibility only",
        "inspection is not enforcement",
        "Shell view binding is not Shell LIVE",
    )

    if kind is SurfacePermissionInspectionViewKind.SUMMARY:
        title = "Surface Permission Inspection Summary"
        rows = list(result.summary)
    elif kind is SurfacePermissionInspectionViewKind.TABLE:
        title = "Surface Permission Inspection Table"
        for entry in result.matched_entries[:50]:
            rows.append(
                f"{entry.client_kind.value}\t{entry.surface_id}\t"
                f"{entry.permission_action.value}\t{entry.permission_level.value}\t"
                f"{entry.reason.value}"
            )
        if len(result.matched_entries) > 50:
            rows.append(f"... {len(result.matched_entries) - 50} more entries")
    elif kind is SurfacePermissionInspectionViewKind.JSON:
        title = "Surface Permission Inspection JSON"
        rows = [
            to_canonical_json(
                {
                    "summary": result.summary,
                    "matched_entry_count": len(result.matched_entries),
                    "evidence_refs": result.evidence_refs,
                    "limitations": result.limitations,
                }
            )
        ]
    elif kind is SurfacePermissionInspectionViewKind.DETAIL:
        title = "Surface Permission Inspection Detail"
        for entry in result.matched_entries[:20]:
            rows.append(
                f"{entry.client_kind.value}:{entry.surface_id}:"
                f"{entry.permission_action.value} -> {entry.permission_level.value} "
                f"({entry.reason.value}) evidence={','.join(entry.evidence_refs)}"
            )
        rows.extend(result.limitations)
    else:
        title = "Surface Permission Inspection Report"
        rows = list(result.summary)
        rows.append("no-overclaim boundaries preserved")
        rows.extend(result.no_execution_proof.evidence_refs[:5])

    payload = {
        "view_kind": kind,
        "title": title,
        "rows": tuple(rows),
        "summary": result.summary,
        "evidence_refs": result.evidence_refs,
        "limitations": result.limitations,
        "truth_notes": truth_notes,
    }
    return SurfacePermissionInspectionView(
        **payload,
        view_hash=_hash_payload(payload),
    )


def export_surface_permission_inspection(
    result: SurfacePermissionInspectionResult | None = None,
    *,
    read_model: SurfacePermissionReadModel | None = None,
) -> SurfacePermissionInspectionExport:
    if result is None:
        result = inspect_surface_permissions(read_model=read_model)
    if read_model is None:
        read_model = build_surface_permission_read_model()

    export_payload = serialize_surface_permission_read_model(read_model)
    if result.query != SurfacePermissionInspectionQuery():
        filtered = {
            "summary": result.summary,
            "matched_entry_count": len(result.matched_entries),
            "matched_entries": [
                entry.to_canonical_dict() for entry in result.matched_entries
            ],
            "evidence_refs": result.evidence_refs,
            "limitations": result.limitations,
            "no_execution_proof": result.no_execution_proof.to_canonical_dict(),
        }
        export_payload = to_canonical_json(filtered)

    payload = {
        "format": "json",
        "source_read_model": read_model.read_model_hash,
        "export_payload": export_payload,
        "evidence_refs": result.evidence_refs,
        "limitations": result.limitations
        + ("export is evidence/report output; export is not mutation",),
        "read_only": True,
        "deterministic": True,
        "json_safe": True,
    }
    return SurfacePermissionInspectionExport(
        **payload,
        export_hash=_hash_payload(payload),
    )


_FORBIDDEN_SIDE_EFFECTS: tuple[str, ...] = (
    "command_execution",
    "tool_execution",
    "approval_execution",
    "runtime_control",
    "sandbox_control",
    "memory_write",
    "policy_mutation",
    "identity_mutation",
    "permission_enforcement",
    "agent_dispatch",
    "workflow_execution",
)

_NO_EXECUTION_BOUNDARIES: tuple[str, ...] = (
    "inspects P2.11-B read model only",
    "read-only CLI output",
    "does not execute Aurel commands",
    "does not approve actions",
    "does not start/stop runtime",
    "does not trigger sandbox",
)


def build_surface_permission_cli_specs(
    read_model: SurfacePermissionReadModel | None = None,
) -> tuple[SurfacePermissionCliCommandSpec, ...]:
    if read_model is None:
        read_model = build_surface_permission_read_model()
    source = read_model.read_model_hash
    commands: list[tuple[str, str, tuple[str, ...], str]] = [
        (
            "shell permissions summary",
            "Summarize permission read model inspection",
            (),
            "text/json",
        ),
        (
            "shell permissions clients",
            "List client permission views",
            (),
            "text/json",
        ),
        (
            "shell permissions surfaces",
            "List surface permission views",
            (),
            "text/json",
        ),
        (
            "shell permissions actions",
            "List action permission views",
            (),
            "text/json",
        ),
        (
            "shell permissions show",
            "Show filtered permission entries",
            ("--client", "--surface", "--action", "--level"),
            "text/json",
        ),
        (
            "shell permissions evidence",
            "Inspect evidence refs and NO_EVIDENCE entries",
            ("--no-evidence",),
            "text/json",
        ),
        (
            "shell permissions sensitive",
            "Inspect sensitive surface limitations",
            (),
            "text/json",
        ),
        (
            "shell permissions export",
            "Export read-only permission inspection JSON",
            ("--json",),
            "json",
        ),
    ]
    specs: list[SurfacePermissionCliCommandSpec] = []
    for name, description, arguments, output_format in commands:
        payload = {
            "command_name": name,
            "description": description,
            "arguments": arguments,
            "read_only": True,
            "source_read_model": source,
            "output_format": output_format,
            "forbidden_side_effects": _FORBIDDEN_SIDE_EFFECTS,
            "no_execution_boundaries": _NO_EXECUTION_BOUNDARIES,
        }
        specs.append(
            SurfacePermissionCliCommandSpec(
                **payload,
                spec_hash=_hash_payload(payload),
            )
        )
    return tuple(specs)


def build_surface_permission_shell_view_bindings(
    read_model: SurfacePermissionReadModel | None = None,
) -> tuple[SurfacePermissionShellViewBinding, ...]:
    if read_model is None:
        read_model = build_surface_permission_read_model()
    source = read_model.read_model_hash
    supported_filters = (
        "client_kind",
        "surface_id",
        "permission_action",
        "permission_level",
        "reason",
        "evidence_status",
        "sensitive_only",
        "no_evidence_only",
        "denied_only",
        "future_gated_only",
        "contract_only_only",
        "unavailable_only",
        "preflight_only_only",
    )
    supported_views = tuple(SurfacePermissionInspectionViewKind)
    bindings: list[SurfacePermissionShellViewBinding] = []
    panel_titles = {
        "PermissionSummaryPanel": "Permission Summary",
        "PermissionClientViewPanel": "Client Permission Views",
        "PermissionSurfaceViewPanel": "Surface Permission Views",
        "PermissionActionViewPanel": "Action Permission Views",
        "PermissionEvidencePanel": "Evidence / NO_EVIDENCE",
        "PermissionSensitiveSurfacePanel": "Sensitive Surface Limitations",
        "PermissionNoOverclaimPanel": "No-Overclaim Boundaries",
    }
    for panel_id in _SHELL_PANEL_IDS:
        payload = {
            "panel_id": panel_id,
            "panel_title": panel_titles[panel_id],
            "source_read_model": source,
            "supported_filters": supported_filters,
            "supported_views": supported_views,
            "read_only": True,
            "evidence_refs": read_model.evidence_refs,
            "limitations": (
                "Shell view binding is contract/read-model binding only",
                "Shell view binding is not Shell LIVE",
                "binding does not execute or enforce permissions",
            ),
            "no_execution_boundaries": _NO_EXECUTION_BOUNDARIES,
        }
        bindings.append(
            SurfacePermissionShellViewBinding(
                **payload,
                binding_hash=_hash_payload(payload),
            )
        )
    return tuple(bindings)


def build_p2_11_c_handoff(
    result: SurfacePermissionInspectionResult | None = None,
) -> P211CHandoff:
    if result is None:
        result = inspect_surface_permissions()
    payload = {
        "next_pack": P2_11_D_NEXT_PACK,
        "next_title": P2_11_D_NEXT_TITLE,
        "handoff_status": (
            "P2.11-D next; inspection parity/evidence consistency not implemented"
        ),
        "inspection_summary": result.summary
        + ("P2.11 as a whole is not complete",),
        "parity_validation_needs": (
            "validate inspection views match matrix/projection truth",
            "validate CLI/Shell bindings preserve evidence and limitations",
            "validate NO_EVIDENCE visibility across operator paths",
        ),
        "evidence_consistency_needs": (
            "cross-check evidence refs across matrix/projection/inspection",
            "verify sensitive-surface limitations remain conservative",
            "verify no-overclaim boundaries remain active",
        ),
        "remaining_risks": (
            "P2.11-D not implemented",
            "P2.12 truth-label fixture discipline not implemented",
            "inspection is not runtime enforcement or Custos authorization",
            "Shell view binding is not full UI or Shell LIVE",
        ),
    }
    return P211CHandoff(**payload, handoff_hash=_hash_payload(payload))


def build_p2_11_c_surface_permission_inspection_result(
    *,
    assert_gate: bool = True,
) -> P211CResult:
    gate = build_p2_11_c_prerequisite_gate()
    if assert_gate and gate.gate_status is not P211CPrerequisiteGateStatus.GATE_PASSED:
        _reject(
            "P2.11-C prerequisite gate did not pass",
            field="prerequisite_gate",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    read_model = build_surface_permission_read_model()
    inspection = inspect_surface_permissions(read_model=read_model)
    export = export_surface_permission_inspection(inspection, read_model=read_model)
    no_execution_proof = build_surface_permission_inspection_no_execution_proof(
        read_model
    )
    handoff = build_p2_11_c_handoff(inspection)
    side_effects = P211CSideEffectProof()
    payload = {
        "covered_pack": P2_11_C_PACK_ID,
        "inspection_contract": (
            "SurfacePermissionInspectionQuery",
            "SurfacePermissionInspectionFilter",
            "SurfacePermissionInspectionResult",
            "SurfacePermissionInspectionView",
        ),
        "query_filter_model": (
            "client_kind",
            "surface_id",
            "permission_action",
            "permission_level",
            "reason",
            "evidence_status",
            "sensitive_only",
            "no_evidence_only",
            "denied_only",
            "future_gated_only",
            "contract_only_only",
            "unavailable_only",
            "preflight_only_only",
        ),
        "inspection_views": tuple(SurfacePermissionInspectionViewKind),
        "cli_command_specs": build_surface_permission_cli_specs(read_model),
        "shell_view_binding": build_surface_permission_shell_view_bindings(
            read_model
        ),
        "inspection_export": export,
        "no_execution_proof": no_execution_proof,
        "handoff": handoff,
        "p211d_not_done": P2_11_D_NOT_DONE,
        "p212_not_started": P2_12_NOT_STARTED,
    }
    result = P211CResult(**payload, result_hash=_hash_payload(payload))
    assert_p2_11_c_no_scope_expansion(result, side_effects)
    return result


def serialize_p2_11_c_result(result: P211CResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def assert_p2_11_c_no_scope_expansion(
    result: P211CResult,
    side_effects: P211CSideEffectProof,
) -> None:
    if any(side_effects.to_canonical_dict().values()):
        _reject(
            "P2.11-C side-effect proof must keep all execution/enforcement claims false",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    if result.handoff.next_pack != P2_11_D_NEXT_PACK:
        _reject(
            "P2.11-C must hand off to P2.11-D",
            field="handoff.next_pack",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    if result.no_execution_proof.violations:
        _reject(
            "no-execution proof must not report violations in P2.11-C inspection",
            field="no_execution_proof.violations",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
    for spec in result.cli_command_specs:
        if not spec.read_only:
            _reject(
                "CLI command specs must remain read-only",
                field="cli_command_specs.read_only",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )
    for binding in result.shell_view_binding:
        if not binding.read_only:
            _reject(
                "Shell view bindings must remain read-only",
                field="shell_view_binding.read_only",
                code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
            )


P2_11_C_VALIDATION_REFS: tuple[str, ...] = (
    P2_11_C_TEST_INSPECTION_REF,
    P2_11_C_TEST_FILTERS_REF,
    P2_11_C_TEST_CLI_SHELL_REF,
    P2_11_C_TEST_NO_EXECUTION_REF,
    P2_11_C_TEST_HANDOFF_REF,
)
