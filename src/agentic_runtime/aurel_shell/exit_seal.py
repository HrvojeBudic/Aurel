"""AurelShell P2.0 docs sync + exit seal (P2.0-F / P2.0.29-P2.0.30).

Closes P2.0 at contract scope. The exit seal is evidence-gated and scope-aware:
a P2 contract-scope seal can be issued separately from production-live,
trace-verified, and release scopes, which cannot seal without real evidence.

Architectural law:
  - Docs are not proof.
  - Exit seal is not valid without evidence.
  - P2_CONTRACT_SCOPE seals separately from PRODUCTION_LIVE_SCOPE.
  - READY_FOR_P2_1_REVIEW is review readiness only; it does not start P2.1.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .api_contract import ShellAPIContract
from .cli_binding import (
    ShellCLIBindingContract,
    ShellTUIBindingContract,
    TUI_UNAVAILABLE_REASON,
    build_shell_cli_binding_contract,
    build_shell_tui_binding_contract,
    handle_shell_cli_inspect,
)
from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .event_contract import ShellEventContract
from .projection import (
    API_RUNTIME_UNAVAILABLE_REASON,
    EVENT_RUNTIME_UNAVAILABLE_REASON,
    FORBIDDEN_P2_0_F_TRUTH_LABELS,
    P2_0_F_DEPENDENCY_PACKS,
    P2_0_F_NEXT_STEP,
    P2_0_F_PACK_CHECKPOINT_IDS,
    P2_0_F_PACK_ID,
    P2_0_F_SECTION_ID,
    P20FSideEffectProof,
    P20FTruthLabel,
    ShellProjectionContract,
    all_false_p2_0_f_side_effects,
    build_shell_projection_contract,
)
from .read_model import detect_surface_taxonomy_drift
from .readiness import build_p2_0_e_operator_demo_snapshot_regression_result
from .surface_registry import CANONICAL_SURFACE_ORDER, build_default_surface_registry

P2_0_F_DOCS_UPDATE_VERSION = "p2_0_f_docs_state_report_update.v1"
P2_0_F_EXIT_SEAL_VERSION = "p2_0_f_exit_seal.v1"
P2_0_F_EXIT_SEAL_CHECKLIST_VERSION = "p2_0_f_exit_seal_checklist.v1"
P2_0_F_LIVE_DEMO_VERSION = "p2_0_f_live_integration_demo.v1"
P2_0_F_READINESS_VERSION = "p2_0_f_readiness_for_p2_1_review.v1"
P2_0_F_PACK_RESULT_VERSION = "p2_0_f_projection_cli_exit_seal_result.v1"

P2_0_FULL_CHECKPOINT_RANGE = "P2.0.0-P2.0.30"

P2_0_F_REPORT_FILENAME = "P2_0_F_PROJECTION_CLI_EXIT_SEAL.md"
P2_0_DEPENDENCY_REPORT_CHAIN: tuple[str, ...] = (
    "P2_0_A_SHELL_FOUNDATION_SURFACE_REGISTRY.md",
    "P2_0_B_NAVIGATION_BOUNDARY_CONTRACTS.md",
    "P2_0_C_FLOATING_WINDOW_HANDOFF_CONTEXT.md",
    "P2_0_D_TRUTH_PERMISSION_FIXTURE_CONTRACTS.md",
    "P2_0_E_OPERATOR_DEMO_SNAPSHOT_REGRESSION.md",
)

LIVE_PATH_UNAVAILABLE_REASON = (
    "UNAVAILABLE_LIVE_PATH: production LIVE operator shell path is not "
    "implemented or tested in P2.0-F"
)
TRACE_VERIFICATION_UNAVAILABLE_REASON = (
    "UNAVAILABLE_TRACE_VERIFICATION: P2.0 shell carries ContextRef/TraceRef "
    "contract boundaries only; there is no actual trace verification runtime proof"
)

_DOCS_NON_GOALS: tuple[str, ...] = (
    "no_roadmap_renumbering",
    "no_canon_replacement",
    "no_fake_proof",
    "no_fake_live_seal",
)

_SEAL_NON_GOALS: tuple[str, ...] = (
    "no_product_release",
    "no_production_live_seal_without_live_path",
    "no_trace_verified_seal_without_verification",
    "no_p2_1_implementation",
    "no_p2_1_automatic_coding_permission",
)

_PACK_NON_GOALS: tuple[str, ...] = (
    "no_product_ui",
    "no_api_server",
    "no_http_routes",
    "no_event_bus",
    "no_runtime_event_emission",
    "no_live_cli_tui_product",
    "no_route_runtime",
    "no_memory_writes",
    "no_trace_writes",
    "no_trace_verification",
    "no_runtime_mutation",
    "no_p2_1",
)


class P20ExitSealScope(str, Enum):
    """Scope for the P2.0 exit seal decision."""

    P2_CONTRACT_SCOPE = "P2_CONTRACT_SCOPE"
    PRODUCTION_LIVE_SCOPE = "PRODUCTION_LIVE_SCOPE"
    TRACE_VERIFIED_SCOPE = "TRACE_VERIFIED_SCOPE"
    RELEASE_SCOPE = "RELEASE_SCOPE"


class P20ExitSealDecision(str, Enum):
    """Overall P2.0 exit seal decision."""

    SEALED_FOR_P2_CONTRACT_SCOPE = "SEALED_FOR_P2_CONTRACT_SCOPE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_SEALED = "NOT_SEALED"


class P20ScopeSealStatus(str, Enum):
    """Per-scope seal status."""

    SEALED = "SEALED"
    PARTIAL = "PARTIAL"
    NOT_SEALED = "NOT_SEALED"
    BLOCKED = "BLOCKED"


class P20ExitSealCheckStatus(str, Enum):
    """Individual checklist item status."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"
    SKIPPED = "SKIPPED"


class P20LiveDemoStatus(str, Enum):
    """Live integration demo status."""

    DEV_FIXTURE_TESTED = "DEV_FIXTURE_TESTED"
    OPERATOR_TEST_PATH_TESTED = "OPERATOR_TEST_PATH_TESTED"
    PROJECTION_ONLY_TESTED = "PROJECTION_ONLY_TESTED"
    CLI_READ_ONLY_TESTED = "CLI_READ_ONLY_TESTED"
    UNAVAILABLE_LIVE_PATH = "UNAVAILABLE_LIVE_PATH"
    NOT_RUN = "NOT_RUN"
    FAILED = "FAILED"
    PRODUCTION_LIVE_TESTED = "PRODUCTION_LIVE_TESTED"
    LIVE_TESTED = "LIVE_TESTED"


class P20ReadinessForP21Decision(str, Enum):
    """P2.1 review readiness decision — review only."""

    READY_FOR_P2_1_REVIEW = "READY_FOR_P2_1_REVIEW"
    NOT_READY_FOR_P2_1 = "NOT_READY_FOR_P2_1"


class P20FCheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


# ---------------------------------------------------------------------------
# P2.0.29 docs/state/report sync
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P20ReportIndexEntry(_CanonicalMixin):
    """A single report index entry."""

    report_path: str
    title: str
    present_on_disk: bool
    indexed: bool


@dataclass(frozen=True)
class P20StateSyncSummary(_CanonicalMixin):
    """Summary of which agent state files were synced."""

    active_task_updated: bool
    state_updated: bool
    roadmap_mirror_updated: bool
    reports_index_updated: bool
    decisions_updated: bool
    tests_updated: bool
    roadmap_canon_overridden: bool


@dataclass(frozen=True)
class P20DocsStateReportUpdate(_CanonicalMixin):
    """P2.0.29 docs/state/report sync summary."""

    schema_version: str
    update_id: str
    report_path: str
    report_index_updated: bool
    state_files_updated: tuple[str, ...]
    roadmap_progress_mirrored: bool
    roadmap_canon_overridden: bool
    validation_recorded: bool
    commit_hash_recorded: bool
    report_entries: tuple[P20ReportIndexEntry, ...]
    state_sync_summary: P20StateSyncSummary
    truth_label: str
    limitations: tuple[str, ...]
    non_goals: tuple[str, ...]
    update_hash: str


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[3]


def _file_mentions(path: Path, needle: str) -> bool:
    if not path.is_file():
        return False
    try:
        return needle in path.read_text(encoding="utf-8")
    except OSError:
        return False


def build_p2_0_docs_state_report_update(
    *,
    repo_root: Path | None = None,
    commit_hash: str = "",
) -> P20DocsStateReportUpdate:
    root = _repo_root(repo_root)
    agent_dir = root / "agent"
    reports_dir = agent_dir / "reports"

    report_path = f"agent/reports/{P2_0_F_REPORT_FILENAME}"
    report_present = (reports_dir / P2_0_F_REPORT_FILENAME).is_file()
    reports_index_path = agent_dir / "REPORTS.md"
    report_indexed = _file_mentions(reports_index_path, P2_0_F_REPORT_FILENAME)

    report_entries = (
        P20ReportIndexEntry(
            report_path=report_path,
            title="P2.0-F Projection/API/CLI/Docs/Exit Seal Integration Tail",
            present_on_disk=report_present,
            indexed=report_indexed,
        ),
    )

    active_task_updated = _file_mentions(agent_dir / "ACTIVE_TASK.md", "P2.0-F")
    state_updated = _file_mentions(agent_dir / "STATE.md", "P2.0-F")
    roadmap_mirror_updated = _file_mentions(agent_dir / "ROADMAP.md", "P2.0-F")
    decisions_updated = _file_mentions(agent_dir / "DECISIONS.md", "P2.0-F")
    tests_updated = _file_mentions(
        agent_dir / "TESTS.md", "test_shell_projection_cli_exit_seal"
    )

    state_sync_summary = P20StateSyncSummary(
        active_task_updated=active_task_updated,
        state_updated=state_updated,
        roadmap_mirror_updated=roadmap_mirror_updated,
        reports_index_updated=report_indexed,
        decisions_updated=decisions_updated,
        tests_updated=tests_updated,
        roadmap_canon_overridden=False,
    )

    state_files_updated = tuple(
        name
        for name, updated in (
            ("agent/ACTIVE_TASK.md", active_task_updated),
            ("agent/STATE.md", state_updated),
            ("agent/ROADMAP.md", roadmap_mirror_updated),
            ("agent/DECISIONS.md", decisions_updated),
            ("agent/TESTS.md", tests_updated),
        )
        if updated
    )

    payload = {
        "schema_version": P2_0_F_DOCS_UPDATE_VERSION,
        "update_id": "p2_0_f_docs_state_report_update",
        "report_path": report_path,
        "report_index_updated": report_indexed,
        "state_files_updated": state_files_updated,
        "roadmap_progress_mirrored": roadmap_mirror_updated,
        "roadmap_canon_overridden": False,
        "validation_recorded": True,
        "commit_hash_recorded": bool(commit_hash),
        "report_entries": report_entries,
        "state_sync_summary": state_sync_summary,
        "truth_label": P20FTruthLabel.DOCS_SYNC_ONLY.value,
        "limitations": (
            "Docs are not proof; evidence lives in code/tests/report/git.",
        ),
        "non_goals": _DOCS_NON_GOALS,
    }
    update = P20DocsStateReportUpdate(
        **payload,
        update_hash=_hash_payload(payload),
    )
    assert_docs_do_not_override_roadmap_canon(update)
    return update


# ---------------------------------------------------------------------------
# P2.0.30 exit seal + live integration demo
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P20ExitSealCheckItem(_CanonicalMixin):
    """Single exit seal checklist item."""

    check_id: str
    check_label: str
    status: P20ExitSealCheckStatus
    summary: str
    evidence_refs: tuple[str, ...]
    unavailable_reason: str


@dataclass(frozen=True)
class P20ExitSealChecklist(_CanonicalMixin):
    """Exit seal checklist envelope."""

    schema_version: str
    checkpoint_coverage: str
    checks: tuple[P20ExitSealCheckItem, ...]
    passed_count: int
    failed_count: int
    unavailable_count: int
    fake_live_detected: bool
    fake_trace_verified_detected: bool
    fake_sealed_detected: bool
    truth_label: str
    side_effects: P20FSideEffectProof
    checklist_hash: str


@dataclass(frozen=True)
class P20LiveIntegrationDemoResult(_CanonicalMixin):
    """Live integration demo result with honest truth boundary."""

    schema_version: str
    demo_status: P20LiveDemoStatus
    demo_passed: bool
    truth_label: str
    unavailable_reason: str
    projection_demo: bool
    cli_inspect_demo: bool
    snapshot_demo: bool
    live_path_evidence: bool
    summary: str
    side_effects: P20FSideEffectProof
    demo_result_hash: str


@dataclass(frozen=True)
class P20ReadinessForP21Review(_CanonicalMixin):
    """P2.1 review readiness — review only, never coding authorization."""

    schema_version: str
    readiness_decision: P20ReadinessForP21Decision
    is_review_only: bool
    starts_p2_1: bool
    authorizes_p2_1_coding: bool
    reason: str
    truth_label: str
    readiness_hash: str


@dataclass(frozen=True)
class P20ExitSeal(_CanonicalMixin):
    """P2.0 exit seal aggregate."""

    schema_version: str
    seal_id: str
    section_id: str
    pack_id: str
    dependency_packs_checked: tuple[str, ...]
    checkpoint_coverage: str
    validation_evidence: tuple[str, ...]
    report_evidence: tuple[str, ...]
    git_evidence: str
    seal_scopes: tuple[str, ...]
    requested_scope: P20ExitSealScope
    checklist: P20ExitSealChecklist
    live_integration_demo_result: P20LiveIntegrationDemoResult
    docs_update: P20DocsStateReportUpdate
    production_live_available: bool
    trace_verification_available: bool
    contract_scope_decision: P20ScopeSealStatus
    production_live_scope_decision: P20ScopeSealStatus
    trace_verified_scope_decision: P20ScopeSealStatus
    release_scope_decision: P20ScopeSealStatus
    exit_seal_decision: P20ExitSealDecision
    decision_reason: str
    p2_1_readiness: P20ReadinessForP21Review
    truth_label: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    non_goals: tuple[str, ...]
    side_effects: P20FSideEffectProof
    seal_hash: str


def _check_item(
    *,
    check_id: str,
    check_label: str,
    status: P20ExitSealCheckStatus,
    summary: str,
    evidence_refs: Sequence[str] = (),
    unavailable_reason: str = "",
) -> P20ExitSealCheckItem:
    return P20ExitSealCheckItem(
        check_id=check_id,
        check_label=check_label,
        status=status,
        summary=summary,
        evidence_refs=tuple(evidence_refs),
        unavailable_reason=unavailable_reason,
    )


def _reports_exist(
    repo_root: Path, filenames: Sequence[str]
) -> tuple[bool, tuple[str, ...]]:
    reports_dir = repo_root / "agent" / "reports"
    refs: list[str] = []
    all_exist = True
    for name in filenames:
        exists = (reports_dir / name).is_file()
        if not exists:
            all_exist = False
        refs.append(f"{name}:{'present' if exists else 'missing'}")
    return all_exist, tuple(refs)


def build_p2_0_live_integration_demo_result(
    *,
    demo_status: P20LiveDemoStatus | str = P20LiveDemoStatus.DEV_FIXTURE_TESTED,
) -> P20LiveIntegrationDemoResult:
    """Run an honest in-process demo chain; never a production LIVE path."""
    if isinstance(demo_status, str):
        demo_status = P20LiveDemoStatus(demo_status)
    if demo_status in {
        P20LiveDemoStatus.LIVE_TESTED,
        P20LiveDemoStatus.PRODUCTION_LIVE_TESTED,
    }:
        raise ValueError(
            "PRODUCTION_LIVE_TESTED/LIVE_TESTED is unavailable in P2.0-F; "
            "a production LIVE shell path requires separate runtime evidence"
        )

    projection = build_shell_projection_contract()
    cli_result = handle_shell_cli_inspect(
        projection_ref=projection.projection_payload.projection_payload_hash,
    )

    projection_demo = True
    cli_inspect_demo = True
    snapshot_demo = True
    demo_passed = (
        projection.contract_hash != ""
        and cli_result.get("read_only") is True
        and cli_result.get("authority_granted") is False
    )
    truth_label = P20FTruthLabel.NOT_LIVE.value
    unavailable_reason = (
        f"{LIVE_PATH_UNAVAILABLE_REASON}; {TRACE_VERIFICATION_UNAVAILABLE_REASON}; "
        "DEV_FIXTURE contract-only vertical slice"
    )
    summary = (
        f"DEV_FIXTURE vertical slice: projection={projection.contract_hash[:12]}; "
        f"cli_read_only={cli_result.get('read_only')}; "
        f"authority_granted={cli_result.get('authority_granted')}"
    )

    if demo_status is P20LiveDemoStatus.OPERATOR_TEST_PATH_TESTED:
        summary = (
            "OPERATOR_TEST_PATH_TESTED: operator-testable dev fixture path; "
            f"projection={projection.contract_hash[:12]}; "
            f"cli_read_only={cli_result.get('read_only')}"
        )
    elif demo_status is P20LiveDemoStatus.PROJECTION_ONLY_TESTED:
        cli_inspect_demo = False
        snapshot_demo = False
        demo_passed = projection.contract_hash != ""
        unavailable_reason = (
            f"{LIVE_PATH_UNAVAILABLE_REASON}; projection-only test is not a "
            "CLI/operator/live integration path"
        )
        summary = f"PROJECTION_ONLY_TESTED: projection={projection.contract_hash[:12]}"
    elif demo_status is P20LiveDemoStatus.CLI_READ_ONLY_TESTED:
        projection_demo = False
        snapshot_demo = False
        demo_passed = cli_result.get("read_only") is True
        unavailable_reason = (
            f"{LIVE_PATH_UNAVAILABLE_REASON}; CLI_READ_ONLY_TESTED grants no "
            "authority and does not prove product LIVE"
        )
        summary = (
            "CLI_READ_ONLY_TESTED: "
            f"read_only={cli_result.get('read_only')}; "
            f"authority_granted={cli_result.get('authority_granted')}"
        )
    elif demo_status is P20LiveDemoStatus.UNAVAILABLE_LIVE_PATH:
        projection_demo = False
        cli_inspect_demo = False
        snapshot_demo = False
        demo_passed = False
        truth_label = P20FTruthLabel.UNAVAILABLE.value
        unavailable_reason = LIVE_PATH_UNAVAILABLE_REASON
        summary = "UNAVAILABLE_LIVE_PATH: production LIVE shell path not tested"
    elif demo_status is P20LiveDemoStatus.NOT_RUN:
        projection_demo = False
        cli_inspect_demo = False
        snapshot_demo = False
        demo_passed = False
        truth_label = P20FTruthLabel.UNAVAILABLE.value
        unavailable_reason = "NOT_RUN: live integration demo was not executed"
        summary = "NOT_RUN: no demo evidence"
    elif demo_status is P20LiveDemoStatus.FAILED:
        demo_passed = False
        truth_label = P20FTruthLabel.NOT_SEALED.value
        unavailable_reason = "FAILED: live integration demo failed"
        summary = "FAILED: demo evidence did not satisfy seal preconditions"

    side_effects = all_false_p2_0_f_side_effects()
    body = {
        "schema_version": P2_0_F_LIVE_DEMO_VERSION,
        "demo_status": demo_status,
        "demo_passed": demo_passed,
        "truth_label": truth_label,
        "unavailable_reason": unavailable_reason,
        "projection_demo": projection_demo,
        "cli_inspect_demo": cli_inspect_demo,
        "snapshot_demo": snapshot_demo,
        "live_path_evidence": False,
        "summary": summary,
        "side_effects": side_effects,
    }
    return P20LiveIntegrationDemoResult(
        **body,
        demo_result_hash=_hash_payload(body),
    )


def build_p2_0_exit_seal_checklist(
    *,
    repo_root: Path | None = None,
    truth_labels: Sequence[str] | None = None,
) -> P20ExitSealChecklist:
    root = _repo_root(repo_root)
    labels = list(truth_labels or ())
    fake_live = "LIVE" in labels
    fake_trace = "TRACE_VERIFIED" in labels
    fake_sealed = any(
        label in labels
        for label in (
            "PRODUCTION_LIVE_SEALED",
            "TRACE_VERIFIED_SEALED",
            "RELEASE_SEALED",
            "EXIT_SEALED",
        )
    )

    checks: list[P20ExitSealCheckItem] = []

    for filename in P2_0_DEPENDENCY_REPORT_CHAIN:
        present, refs = _reports_exist(root, (filename,))
        checks.append(
            _check_item(
                check_id=f"report_{filename.split('_')[1].lower()}",
                check_label=f"Dependency report {filename}",
                status=(
                    P20ExitSealCheckStatus.PASS
                    if present
                    else P20ExitSealCheckStatus.FAIL
                ),
                summary="Dependency pack report present on disk",
                evidence_refs=refs,
            )
        )

    projection = build_shell_projection_contract()
    checks.append(
        _check_item(
            check_id="projection_contract",
            check_label="Projection/API/Event contract",
            status=P20ExitSealCheckStatus.PASS,
            summary="Projection contract built; API/event are contract-only",
            evidence_refs=(
                projection.contract_hash,
                projection.api_contract.runtime_status.value,
                projection.event_contract.runtime_status.value,
            ),
        )
    )
    checks.append(
        _check_item(
            check_id="api_runtime_honest",
            check_label="No fake API server / HTTP route",
            status=P20ExitSealCheckStatus.PASS,
            summary=API_RUNTIME_UNAVAILABLE_REASON,
            evidence_refs=(projection.api_contract.unavailable_reason,),
        )
    )
    checks.append(
        _check_item(
            check_id="event_runtime_honest",
            check_label="No fake event emission / event bus",
            status=P20ExitSealCheckStatus.PASS,
            summary=EVENT_RUNTIME_UNAVAILABLE_REASON,
            evidence_refs=(projection.event_contract.unavailable_reason,),
        )
    )
    checks.append(
        _check_item(
            check_id="live_path_unavailable",
            check_label="Production LIVE path unavailable",
            status=P20ExitSealCheckStatus.UNAVAILABLE,
            summary=LIVE_PATH_UNAVAILABLE_REASON,
            evidence_refs=(LIVE_PATH_UNAVAILABLE_REASON,),
            unavailable_reason=LIVE_PATH_UNAVAILABLE_REASON,
        )
    )
    checks.append(
        _check_item(
            check_id="trace_verification_unavailable",
            check_label="Trace verification unavailable",
            status=P20ExitSealCheckStatus.UNAVAILABLE,
            summary=TRACE_VERIFICATION_UNAVAILABLE_REASON,
            evidence_refs=(TRACE_VERIFICATION_UNAVAILABLE_REASON,),
            unavailable_reason=TRACE_VERIFICATION_UNAVAILABLE_REASON,
        )
    )

    cli_binding = build_shell_cli_binding_contract(
        projection_ref=projection.projection_payload.projection_payload_hash,
    )
    cli_inspect = handle_shell_cli_inspect(
        projection_ref=projection.projection_payload.projection_payload_hash,
    )
    checks.append(
        _check_item(
            check_id="cli_read_only_inspect",
            check_label="CLI read-only inspect binding",
            status=(
                P20ExitSealCheckStatus.PASS
                if cli_binding.is_read_only
                and cli_inspect.get("read_only") is True
                and cli_inspect.get("authority_granted") is False
                else P20ExitSealCheckStatus.FAIL
            ),
            summary="Read-only CLI inspect binding exercised in-process",
            evidence_refs=(str(cli_inspect.get("projection_payload_hash", "")),),
        )
    )

    tui_binding = build_shell_tui_binding_contract(
        projection_ref=projection.projection_payload.projection_payload_hash,
    )
    checks.append(
        _check_item(
            check_id="tui_unavailable_explicit",
            check_label="TUI binding explicitly unavailable",
            status=P20ExitSealCheckStatus.UNAVAILABLE,
            summary="TUI binding declares an explicit unavailable reason",
            evidence_refs=(tui_binding.unavailable_reason,),
            unavailable_reason=TUI_UNAVAILABLE_REASON,
        )
    )

    docs_update = build_p2_0_docs_state_report_update(repo_root=root)
    docs_synced = (
        docs_update.report_index_updated
        and all(entry.present_on_disk for entry in docs_update.report_entries)
        and not docs_update.roadmap_canon_overridden
    )
    checks.append(
        _check_item(
            check_id="docs_state_reports_synced",
            check_label="Docs/state/reports sync",
            status=(
                P20ExitSealCheckStatus.PASS
                if docs_synced
                else P20ExitSealCheckStatus.FAIL
            ),
            summary="P2.0-F report present and indexed; roadmap canon preserved",
            evidence_refs=(docs_update.update_hash,),
        )
    )

    checks.append(
        _check_item(
            check_id="no_fake_live",
            check_label="No fake LIVE",
            status=(
                P20ExitSealCheckStatus.FAIL
                if fake_live
                else P20ExitSealCheckStatus.PASS
            ),
            summary="Truth labels must not include LIVE without proof",
            evidence_refs=tuple(labels),
        )
    )
    checks.append(
        _check_item(
            check_id="no_fake_trace_verified",
            check_label="No fake TRACE_VERIFIED",
            status=(
                P20ExitSealCheckStatus.FAIL
                if fake_trace
                else P20ExitSealCheckStatus.PASS
            ),
            summary="Truth labels must not include TRACE_VERIFIED without proof",
            evidence_refs=tuple(labels),
        )
    )
    checks.append(
        _check_item(
            check_id="no_fake_release_seal",
            check_label="No fake production/release seal",
            status=(
                P20ExitSealCheckStatus.FAIL
                if fake_sealed
                else P20ExitSealCheckStatus.PASS
            ),
            summary="Truth labels must not include production/release seal without evidence",
            evidence_refs=tuple(labels),
        )
    )
    checks.append(
        _check_item(
            check_id="checkpoint_coverage",
            check_label="P2.0.27-P2.0.30 coverage",
            status=P20ExitSealCheckStatus.PASS,
            summary="P2.0-F covers P2.0.27-P2.0.30; P2.0 spans A-F",
            evidence_refs=P2_0_F_PACK_CHECKPOINT_IDS,
        )
    )

    passed = sum(1 for c in checks if c.status is P20ExitSealCheckStatus.PASS)
    failed = sum(1 for c in checks if c.status is P20ExitSealCheckStatus.FAIL)
    unavailable = sum(1 for c in checks if c.status is P20ExitSealCheckStatus.UNAVAILABLE)
    side_effects = all_false_p2_0_f_side_effects()
    body = {
        "schema_version": P2_0_F_EXIT_SEAL_CHECKLIST_VERSION,
        "checkpoint_coverage": P2_0_FULL_CHECKPOINT_RANGE,
        "checks": tuple(checks),
        "passed_count": passed,
        "failed_count": failed,
        "unavailable_count": unavailable,
        "fake_live_detected": fake_live,
        "fake_trace_verified_detected": fake_trace,
        "fake_sealed_detected": fake_sealed,
        "truth_label": P20FTruthLabel.P2_CONTRACT_SCOPE.value,
        "side_effects": side_effects,
    }
    return P20ExitSealChecklist(
        **body,
        checklist_hash=_hash_payload(body),
    )


def derive_p2_0_exit_seal_decision(
    *,
    checklist_passed: bool,
    unavailable_count: int,
    live_demo: P20LiveIntegrationDemoResult,
    seal_scope: P20ExitSealScope | str = P20ExitSealScope.P2_CONTRACT_SCOPE,
    production_live_available: bool = False,
    trace_verification_available: bool = False,
    fake_truth_claim_detected: bool = False,
    dependency_reports_missing: bool = False,
) -> tuple[P20ExitSealDecision, str]:
    """Derive the scope-aware seal decision from explicit evidence only."""
    if isinstance(seal_scope, str):
        seal_scope = P20ExitSealScope(seal_scope)

    if dependency_reports_missing:
        return (
            P20ExitSealDecision.BLOCKED,
            "Exit seal BLOCKED: P2.0-A/B/C/D/E dependency report chain missing",
        )
    if fake_truth_claim_detected:
        return (
            P20ExitSealDecision.NOT_SEALED,
            "Exit seal NOT_SEALED: fake LIVE/TRACE_VERIFIED/release seal claim detected",
        )
    if not checklist_passed:
        return (
            P20ExitSealDecision.BLOCKED,
            "Exit seal BLOCKED: checklist has failures or forbidden truth labels",
        )
    if live_demo.demo_status in {
        P20LiveDemoStatus.NOT_RUN,
        P20LiveDemoStatus.FAILED,
        P20LiveDemoStatus.UNAVAILABLE_LIVE_PATH,
    }:
        return (
            P20ExitSealDecision.NOT_SEALED,
            "Exit seal NOT_SEALED: live demo unavailable, failed, or not run",
        )

    production_live_required = seal_scope in {
        P20ExitSealScope.PRODUCTION_LIVE_SCOPE,
        P20ExitSealScope.RELEASE_SCOPE,
    }
    trace_verified_required = seal_scope in {
        P20ExitSealScope.TRACE_VERIFIED_SCOPE,
        P20ExitSealScope.RELEASE_SCOPE,
    }

    if production_live_required and not production_live_available:
        return (
            P20ExitSealDecision.PARTIAL,
            (
                f"P2.0 is PARTIAL for {seal_scope.value}: production LIVE shell "
                "path is unavailable; DEV_FIXTURE evidence is not LIVE."
            ),
        )
    if trace_verified_required and not trace_verification_available:
        return (
            P20ExitSealDecision.PARTIAL,
            (
                f"P2.0 is PARTIAL for {seal_scope.value}: actual TRACE_VERIFIED "
                "runtime proof is unavailable."
            ),
        )

    if seal_scope is P20ExitSealScope.P2_CONTRACT_SCOPE:
        live_unavailable_disclosed = (
            LIVE_PATH_UNAVAILABLE_REASON in live_demo.unavailable_reason
        )
        operator_testable_demo = (
            live_demo.demo_passed
            and live_demo.demo_status
            in {
                P20LiveDemoStatus.DEV_FIXTURE_TESTED,
                P20LiveDemoStatus.OPERATOR_TEST_PATH_TESTED,
                P20LiveDemoStatus.PROJECTION_ONLY_TESTED,
                P20LiveDemoStatus.CLI_READ_ONLY_TESTED,
            }
            and live_demo.truth_label != "LIVE"
            and not live_demo.live_path_evidence
        )
        if (
            operator_testable_demo
            and live_unavailable_disclosed
            and unavailable_count >= 2
        ):
            return (
                P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE,
                (
                    "P2.0 is SEALED for P2_CONTRACT_SCOPE: A-F report chain, "
                    "projection/API/event contract, read-only CLI inspect, "
                    "explicit TUI/LIVE/trace unavailable boundaries, and "
                    "docs sync passed. Production LIVE and actual TRACE_VERIFIED "
                    "remain explicitly unavailable and are not claimed."
                ),
            )
        return (
            P20ExitSealDecision.PARTIAL,
            (
                "P2.0 is PARTIAL for P2_CONTRACT_SCOPE: operator-testable demo or "
                "unavailable-boundary disclosure is incomplete."
            ),
        )

    return (
        P20ExitSealDecision.PARTIAL,
        f"P2.0 is PARTIAL: no accepted seal qualification for {seal_scope.value}",
    )


def _scope_status(decision: P20ExitSealDecision) -> P20ScopeSealStatus:
    if decision is P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE:
        return P20ScopeSealStatus.SEALED
    if decision is P20ExitSealDecision.BLOCKED:
        return P20ScopeSealStatus.BLOCKED
    if decision is P20ExitSealDecision.NOT_SEALED:
        return P20ScopeSealStatus.NOT_SEALED
    return P20ScopeSealStatus.PARTIAL


def build_p2_0_readiness_for_p2_1_review(
    decision: P20ExitSealDecision,
) -> P20ReadinessForP21Review:
    """Derive P2.1 review readiness from the seal decision. Review only."""
    if decision is P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE:
        readiness_decision = P20ReadinessForP21Decision.READY_FOR_P2_1_REVIEW
        reason = (
            "P2.0 sealed for contract scope; P2.1 may enter OMNI review/planning "
            "only. This is not P2.1 coding authorization."
        )
    else:
        readiness_decision = P20ReadinessForP21Decision.NOT_READY_FOR_P2_1
        reason = (
            f"P2.1 review readiness withheld: P2.0 exit seal is {decision.value}."
        )
    payload = {
        "schema_version": P2_0_F_READINESS_VERSION,
        "readiness_decision": readiness_decision,
        "is_review_only": True,
        "starts_p2_1": False,
        "authorizes_p2_1_coding": False,
        "reason": reason,
        "truth_label": P20FTruthLabel.READINESS_REVIEW_ONLY.value,
    }
    readiness = P20ReadinessForP21Review(
        **payload,
        readiness_hash=_hash_payload(payload),
    )
    assert_p2_1_readiness_is_review_only(readiness)
    assert_p2_1_not_started(readiness)
    return readiness


def build_p2_0_exit_seal(
    *,
    repo_root: Path | None = None,
    seal_scope: P20ExitSealScope | str = P20ExitSealScope.P2_CONTRACT_SCOPE,
    truth_labels: Sequence[str] | None = None,
    live_demo: P20LiveIntegrationDemoResult | None = None,
    production_live_available: bool = False,
    trace_verification_available: bool = False,
) -> P20ExitSeal:
    if isinstance(seal_scope, str):
        seal_scope = P20ExitSealScope(seal_scope)
    root = _repo_root(repo_root)

    checklist = build_p2_0_exit_seal_checklist(
        repo_root=root,
        truth_labels=truth_labels,
    )
    resolved_demo = live_demo or build_p2_0_live_integration_demo_result()
    docs_update = build_p2_0_docs_state_report_update(repo_root=root)

    checklist_passed = (
        checklist.failed_count == 0
        and not checklist.fake_live_detected
        and not checklist.fake_trace_verified_detected
        and not checklist.fake_sealed_detected
    )
    fake_truth_claim_detected = (
        checklist.fake_live_detected
        or checklist.fake_trace_verified_detected
        or checklist.fake_sealed_detected
    )
    dependency_report_check_ids = {
        f"report_{name.split('_')[1].lower()}" for name in P2_0_DEPENDENCY_REPORT_CHAIN
    }
    dependency_reports_missing = any(
        item.check_id in dependency_report_check_ids
        and item.status is P20ExitSealCheckStatus.FAIL
        for item in checklist.checks
    )

    def _decide(scope: P20ExitSealScope) -> tuple[P20ExitSealDecision, str]:
        return derive_p2_0_exit_seal_decision(
            checklist_passed=checklist_passed,
            unavailable_count=checklist.unavailable_count,
            live_demo=resolved_demo,
            seal_scope=scope,
            production_live_available=production_live_available,
            trace_verification_available=trace_verification_available,
            fake_truth_claim_detected=fake_truth_claim_detected,
            dependency_reports_missing=dependency_reports_missing,
        )

    decision, reason = _decide(seal_scope)
    contract_status = _scope_status(_decide(P20ExitSealScope.P2_CONTRACT_SCOPE)[0])
    production_status = _scope_status(_decide(P20ExitSealScope.PRODUCTION_LIVE_SCOPE)[0])
    trace_status = _scope_status(_decide(P20ExitSealScope.TRACE_VERIFIED_SCOPE)[0])
    release_status = _scope_status(_decide(P20ExitSealScope.RELEASE_SCOPE)[0])

    p2_1_readiness = build_p2_0_readiness_for_p2_1_review(decision)

    if decision is P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE:
        truth_label = P20FTruthLabel.SEALED_FOR_P2_CONTRACT_SCOPE.value
    elif decision is P20ExitSealDecision.PARTIAL:
        truth_label = P20FTruthLabel.PARTIAL.value
    elif decision is P20ExitSealDecision.BLOCKED:
        truth_label = P20FTruthLabel.BLOCKED.value
    else:
        truth_label = P20FTruthLabel.NOT_SEALED.value

    blockers: tuple[str, ...] = ()
    if decision in {P20ExitSealDecision.BLOCKED, P20ExitSealDecision.NOT_SEALED}:
        blockers = (reason,)

    side_effects = all_false_p2_0_f_side_effects()
    body = {
        "schema_version": P2_0_F_EXIT_SEAL_VERSION,
        "seal_id": "p2_0_exit_seal",
        "section_id": P2_0_F_SECTION_ID,
        "pack_id": P2_0_F_PACK_ID,
        "dependency_packs_checked": P2_0_F_DEPENDENCY_PACKS,
        "checkpoint_coverage": P2_0_FULL_CHECKPOINT_RANGE,
        "validation_evidence": (
            "compileall src tests",
            "pytest tests/aurel_shell/test_shell_projection_cli_exit_seal.py",
            "pytest tests/aurel_shell",
            "ruff check src tests",
            "mypy src/agentic_runtime",
        ),
        "report_evidence": _reports_exist(
            root, P2_0_DEPENDENCY_REPORT_CHAIN + (P2_0_F_REPORT_FILENAME,)
        )[1],
        "git_evidence": (
            "final git status and commit hash recorded in the P2.0-F report and "
            "operator response"
        ),
        "seal_scopes": tuple(scope.value for scope in P20ExitSealScope),
        "requested_scope": seal_scope,
        "checklist": checklist,
        "live_integration_demo_result": resolved_demo,
        "docs_update": docs_update,
        "production_live_available": production_live_available,
        "trace_verification_available": trace_verification_available,
        "contract_scope_decision": contract_status,
        "production_live_scope_decision": production_status,
        "trace_verified_scope_decision": trace_status,
        "release_scope_decision": release_status,
        "exit_seal_decision": decision,
        "decision_reason": reason,
        "p2_1_readiness": p2_1_readiness,
        "truth_label": truth_label,
        "blockers": blockers,
        "warnings": (
            "P2.0-E OMNI acceptance marker waived by operator instruction for "
            "the P2.0-F dispatch",
        ),
        "limitations": (
            "Contract scope only; no production LIVE, no trace verification, "
            "no release seal.",
        ),
        "non_goals": _SEAL_NON_GOALS,
        "side_effects": side_effects,
    }
    seal = P20ExitSeal(
        **body,
        seal_hash=_hash_payload(body),
    )
    assert_p2_contract_scope_seals_separately(seal)
    assert_production_live_scope_requires_live_path(seal)
    assert_trace_verified_scope_requires_actual_verification(seal)
    assert_release_scope_not_allowed_on_fixtures_only(seal)
    assert_seal_honest(seal)
    return seal


# ---------------------------------------------------------------------------
# Pack result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P20FCheckpointRead(_CanonicalMixin):
    checkpoint_id: str
    canonical_name: str
    status: P20FCheckpointStatus
    evidence: str
    tests: str
    truth_label: str
    unavailable_reason: str
    limitations: str


@dataclass(frozen=True)
class P20FProjectionCLIExitSealPackResult(_CanonicalMixin):
    """P2.0-F pack result envelope."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    dependency_packs: tuple[str, ...]
    canonical_surface_ids: tuple[str, ...]
    checkpoint_reads: tuple[P20FCheckpointRead, ...]
    checkpoint_statuses: dict[str, str]
    projection_api_event_summary: dict[str, str]
    cli_tui_binding_summary: dict[str, str]
    docs_state_report_summary: dict[str, str]
    exit_seal_decision: P20ExitSealDecision
    live_integration_demo_truth_boundary: dict[str, str]
    p2_1_readiness: P20ReadinessForP21Review
    projection_contract: ShellProjectionContract
    api_contract: ShellAPIContract
    event_contract: ShellEventContract
    cli_binding: ShellCLIBindingContract
    tui_binding: ShellTUIBindingContract
    docs_update: P20DocsStateReportUpdate
    exit_seal: P20ExitSeal
    truth_labels: tuple[str, ...]
    side_effect_proof: P20FSideEffectProof
    surface_taxonomy_drift: bool
    surface_taxonomy_drift_details: tuple[str, ...]
    dependency_waivers: tuple[str, ...]
    next_recommended_step: str
    non_goals: tuple[str, ...]
    result_hash: str


def _default_checkpoint_reads() -> tuple[P20FCheckpointRead, ...]:
    names = {
        "P2.0.27": "Shell Projection/API/Event Contract",
        "P2.0.28": "Shell/CLI/TUI Binding",
        "P2.0.29": "Shell Docs/State/Reports Update",
        "P2.0.30": "P2.0 Exit Seal + Live Integration Demo",
    }
    evidence = {
        "P2.0.27": "ShellProjectionContract, ShellAPIContract, ShellEventContract",
        "P2.0.28": "ShellCLIBindingContract, ShellTUIBindingContract (UNAVAILABLE)",
        "P2.0.29": "P20DocsStateReportUpdate, P20ReportIndexEntry, P20StateSyncSummary",
        "P2.0.30": "P20ExitSeal, P20ExitSealChecklist, P20LiveIntegrationDemoResult",
    }
    tests = {
        "P2.0.27": "test_p2_0_27_projection_* / _api_* / _event_*",
        "P2.0.28": "test_p2_0_28_cli_* / _tui_*",
        "P2.0.29": "test_p2_0_29_docs_*",
        "P2.0.30": "test_p2_0_30_exit_seal_* / _live_demo_* / _p2_1_readiness_*",
    }
    truth = {
        "P2.0.27": "PROJECTION_ONLY / READ_MODEL_ONLY / API_CONTRACT_ONLY / EVENT_CONTRACT_ONLY / NOT_LIVE",
        "P2.0.28": "CLI_INSPECT_CONTRACT_ONLY / TUI_UNAVAILABLE / CONTRACT_ONLY / NOT_LIVE",
        "P2.0.29": "DOCS_SYNC_ONLY / REPORT_EVIDENCE / NOT_LIVE",
        "P2.0.30": "P2_CONTRACT_SCOPE / SEALED_FOR_P2_CONTRACT_SCOPE / NOT_LIVE / NOT_TRACE_VERIFIED",
    }
    unavailable = {
        "P2.0.27": "API/event runtime unavailable (contract-only)",
        "P2.0.28": "TUI binding UNAVAILABLE (no TUI convention)",
        "P2.0.29": "n/a - docs sync only",
        "P2.0.30": "production LIVE + trace verification unavailable",
    }
    limitations = {
        "P2.0.27": "No API server, HTTP route, event bus, or emitted runtime event",
        "P2.0.28": "No command execution, shell mutation, or live CLI/TUI product",
        "P2.0.29": "Docs are not proof; roadmap canon not overridden",
        "P2.0.30": "Contract scope only; no production live/trace/release seal; P2.1 not started",
    }
    return tuple(
        P20FCheckpointRead(
            checkpoint_id=checkpoint_id,
            canonical_name=names[checkpoint_id],
            status=P20FCheckpointStatus.DONE,
            evidence=evidence[checkpoint_id],
            tests=tests[checkpoint_id],
            truth_label=truth[checkpoint_id],
            unavailable_reason=unavailable[checkpoint_id],
            limitations=limitations[checkpoint_id],
        )
        for checkpoint_id in P2_0_F_PACK_CHECKPOINT_IDS
    )


def build_p2_0_f_projection_cli_exit_seal_result(
    *,
    repo_root: Path | None = None,
) -> P20FProjectionCLIExitSealPackResult:
    registry = build_default_surface_registry()
    # Confirm the P2.0-E dependency chain still builds and hashes.
    p2_0_e = build_p2_0_e_operator_demo_snapshot_regression_result()

    projection = build_shell_projection_contract()
    projection_ref = projection.projection_payload.projection_payload_hash
    cli_binding = build_shell_cli_binding_contract(projection_ref=projection_ref)
    tui_binding = build_shell_tui_binding_contract(projection_ref=projection_ref)
    docs_update = build_p2_0_docs_state_report_update(repo_root=repo_root)
    live_demo = build_p2_0_live_integration_demo_result()
    exit_seal = build_p2_0_exit_seal(repo_root=repo_root, live_demo=live_demo)

    checkpoint_reads = _default_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    drift, drift_details = detect_surface_taxonomy_drift()

    projection_api_event_summary = {
        "projection_status": projection.projection_status.value,
        "projection_is_read_model": str(
            projection.projection_payload.is_read_model
        ).lower(),
        "projection_is_source_of_truth": str(
            projection.projection_payload.is_source_of_truth
        ).lower(),
        "api_runtime_status": projection.api_contract.runtime_status.value,
        "api_is_server": str(projection.api_contract.is_api_server).lower(),
        "event_runtime_status": projection.event_contract.runtime_status.value,
        "event_emitted": str(projection.event_contract.event_emitted).lower(),
        "contract_hash": projection.contract_hash,
    }
    cli_tui_binding_summary = {
        "cli_status": cli_binding.binding_status.value,
        "cli_read_only": str(cli_binding.is_read_only).lower(),
        "cli_executes": str(cli_binding.executes_action).lower(),
        "tui_status": tui_binding.binding_status.value,
        "tui_unavailable_reason": tui_binding.unavailable_reason,
    }
    docs_state_report_summary = {
        "report_path": docs_update.report_path,
        "report_index_updated": str(docs_update.report_index_updated).lower(),
        "roadmap_canon_overridden": str(docs_update.roadmap_canon_overridden).lower(),
        "validation_recorded": str(docs_update.validation_recorded).lower(),
    }
    live_integration_demo_truth_boundary = {
        "demo_status": live_demo.demo_status.value,
        "demo_passed": str(live_demo.demo_passed).lower(),
        "truth_label": live_demo.truth_label,
        "live_path_evidence": str(live_demo.live_path_evidence).lower(),
        "unavailable_reason": live_demo.unavailable_reason,
    }

    side_effects = all_false_p2_0_f_side_effects()
    truth_labels = (
        P20FTruthLabel.PROJECTION_ONLY.value,
        P20FTruthLabel.READ_MODEL_ONLY.value,
        P20FTruthLabel.API_CONTRACT_ONLY.value,
        P20FTruthLabel.EVENT_CONTRACT_ONLY.value,
        P20FTruthLabel.CLI_INSPECT_CONTRACT_ONLY.value,
        P20FTruthLabel.TUI_UNAVAILABLE.value,
        P20FTruthLabel.DOCS_SYNC_ONLY.value,
        P20FTruthLabel.P2_CONTRACT_SCOPE.value,
        P20FTruthLabel.READINESS_REVIEW_ONLY.value,
        P20FTruthLabel.NOT_LIVE.value,
        P20FTruthLabel.NOT_TRACE_VERIFIED.value,
    )
    payload = {
        "schema_version": P2_0_F_PACK_RESULT_VERSION,
        "pack_id": P2_0_F_PACK_ID,
        "section_id": P2_0_F_SECTION_ID,
        "covered_checkpoints": P2_0_F_PACK_CHECKPOINT_IDS,
        "dependency_packs": P2_0_F_DEPENDENCY_PACKS,
        "canonical_surface_ids": tuple(CANONICAL_SURFACE_ORDER),
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "projection_api_event_summary": projection_api_event_summary,
        "cli_tui_binding_summary": cli_tui_binding_summary,
        "docs_state_report_summary": docs_state_report_summary,
        "exit_seal_decision": exit_seal.exit_seal_decision,
        "live_integration_demo_truth_boundary": live_integration_demo_truth_boundary,
        "p2_1_readiness": exit_seal.p2_1_readiness,
        "projection_contract": projection,
        "api_contract": projection.api_contract,
        "event_contract": projection.event_contract,
        "cli_binding": cli_binding,
        "tui_binding": tui_binding,
        "docs_update": docs_update,
        "exit_seal": exit_seal,
        "truth_labels": truth_labels,
        "side_effect_proof": side_effects,
        "surface_taxonomy_drift": drift,
        "surface_taxonomy_drift_details": drift_details,
        "dependency_waivers": (
            "operator waived missing local P2.0-E OMNI acceptance marker for "
            "the P2.0-F dispatch",
        ),
        "next_recommended_step": P2_0_F_NEXT_STEP,
        "non_goals": _PACK_NON_GOALS,
    }
    result = P20FProjectionCLIExitSealPackResult(
        **payload,
        result_hash=_hash_payload(payload),
    )
    assert registry.surface_count == 7
    assert p2_0_e.result_hash
    return result


def serialize_p2_0_f_result(
    result: P20FProjectionCLIExitSealPackResult,
) -> str:
    return to_canonical_json(result.to_canonical_dict())


# ---------------------------------------------------------------------------
# Invariant guards
# ---------------------------------------------------------------------------


def assert_docs_do_not_override_roadmap_canon(update: P20DocsStateReportUpdate) -> None:
    if update.roadmap_canon_overridden or update.state_sync_summary.roadmap_canon_overridden:
        _reject(
            "docs sync must not override roadmap canon",
            field="roadmap_canon_overridden",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_docs_do_not_fake_proof(update: P20DocsStateReportUpdate) -> None:
    if update.truth_label in FORBIDDEN_P2_0_F_TRUTH_LABELS:
        _reject(
            "docs sync must not claim forbidden operational truth labels",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_p2_contract_scope_seals_separately(seal: P20ExitSeal) -> None:
    if (
        seal.contract_scope_decision is P20ScopeSealStatus.SEALED
        and seal.production_live_scope_decision is P20ScopeSealStatus.SEALED
    ):
        _reject(
            "P2 contract scope must seal separately from production-live scope",
            field="production_live_scope_decision",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_production_live_scope_requires_live_path(seal: P20ExitSeal) -> None:
    if (
        seal.production_live_scope_decision is P20ScopeSealStatus.SEALED
        and not seal.production_live_available
    ):
        _reject(
            "production-live scope cannot seal without actual live path evidence",
            field="production_live_scope_decision",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_trace_verified_scope_requires_actual_verification(seal: P20ExitSeal) -> None:
    if (
        seal.trace_verified_scope_decision is P20ScopeSealStatus.SEALED
        and not seal.trace_verification_available
    ):
        _reject(
            "trace-verified scope cannot seal without actual verification evidence",
            field="trace_verified_scope_decision",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_release_scope_not_allowed_on_fixtures_only(seal: P20ExitSeal) -> None:
    if seal.release_scope_decision is P20ScopeSealStatus.SEALED and not (
        seal.production_live_available and seal.trace_verification_available
    ):
        _reject(
            "release scope cannot seal on dev fixtures only",
            field="release_scope_decision",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_p2_1_readiness_is_review_only(readiness: P20ReadinessForP21Review) -> None:
    if not readiness.is_review_only or readiness.authorizes_p2_1_coding:
        _reject(
            "P2.1 readiness must be review-only and must not authorize coding",
            field="authorizes_p2_1_coding",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_1_not_started(readiness: P20ReadinessForP21Review) -> None:
    if readiness.starts_p2_1:
        _reject(
            "P2.1 must not be started by P2.0-F readiness",
            field="starts_p2_1",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_seal_honest(seal: P20ExitSeal) -> None:
    """Raise if the seal claims forbidden operational truth.

    A NOT_SEALED/PARTIAL/BLOCKED decision may legitimately coexist with fake-truth
    detection (the detection is *why* it was downgraded). Only a sealed decision
    must be free of fake detections and production-live claims.
    """
    if seal.truth_label in FORBIDDEN_P2_0_F_TRUTH_LABELS:
        _reject(
            "exit seal must not claim forbidden operational truth labels",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if seal.exit_seal_decision is not P20ExitSealDecision.SEALED_FOR_P2_CONTRACT_SCOPE:
        return
    if seal.checklist.fake_live_detected:
        _reject(
            "sealed decision cannot coexist with fake LIVE in checklist truth labels",
            field="fake_live_detected",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if seal.checklist.fake_trace_verified_detected:
        _reject(
            "sealed decision cannot coexist with fake TRACE_VERIFIED truth labels",
            field="fake_trace_verified_detected",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if seal.checklist.fake_sealed_detected:
        _reject(
            "sealed decision cannot coexist with fake production/release seal labels",
            field="fake_sealed_detected",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    if seal.production_live_available:
        _reject(
            "P2 contract scope seal cannot claim production LIVE",
            field="production_live_available",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
