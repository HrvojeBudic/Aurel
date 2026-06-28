"""Output Passport integration tail: CLI binding, docs sync, pack result (P1.9-D).

CLI inspect is read-only. Shell/TUI binding is not product UI.
Docs sync is not proof.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .foundation import (
    OutputPassportCheckpointRead,
    OutputPassportCheckpointStatus,
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    OutputPassportUnavailableReason,
    build_p1_9_a_passport_pack_result,
    stable_hash,
    to_canonical_json,
)
from .bindings import build_p1_9_b_read_model_test_harness_binding_pack_result
from .projection import build_output_passport_projection_contract
from .readiness_audit import build_p1_9_c_truth_boundary_failure_readiness_pack_result

OUTPUT_PASSPORT_P1_9_D_PACK_TASK_ID = "P1.9-D"
OUTPUT_PASSPORT_P1_9_D_SECTION_ID = "P1.9"
OUTPUT_PASSPORT_P1_9_D_CHECKPOINT_IDS = (
    "P1.9.27",
    "P1.9.28",
    "P1.9.29",
    "P1.9.30",
)
OUTPUT_PASSPORT_P1_9_D_NEXT_SECTION = "P2"
OUTPUT_PASSPORT_P1_9_D_PACK_RESULT_VERSION = (
    "output_passport_p1_9_d_pack_result.v1"
)
OUTPUT_PASSPORT_CLI_BINDING_VERSION = "output_passport_cli_binding.v1"
OUTPUT_PASSPORT_INSPECT_COMMAND_VERSION = (
    "output_passport_inspect_command.v1"
)
OUTPUT_PASSPORT_DOCS_SYNC_VERSION = "output_passport_docs_sync.v1"

TUI_BINDING_UNAVAILABLE_REASON = (
    "UNAVAILABLE_TUI_BINDING: TUI product surface not implemented in P1.9-D; "
    "read-only CLI inspect only"
)
SHELL_UI_UNAVAILABLE_REASON = (
    "UNAVAILABLE: P2 shell UI not implemented in P1.9-D"
)

P19_REPORT_CHAIN: tuple[str, ...] = (
    "P1_9_A_PASSPORT_IDENTITY_ATTRIBUTION_HASH_PACK.md",
    "P1_9_B_READ_MODEL_TEST_HARNESS_BINDING_PACK.md",
    "P1_9_C_TRUTH_BOUNDARY_FAILURE_READINESS_PACK.md",
    "P1_9_D_INTEGRATION_TAIL_PACK.md",
)

P19_D_UNAVAILABLE_REASON_DETAILS: dict[str, str] = {
    OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE.value: (
        "TUI binding unavailable in P1.9-D; CLI read-only inspect available"
    ),
    OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE.value: (
        "Projection runtime unavailable; projection contract available in P1.9.27"
    ),
    OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE.value: (
        "Trace verification unavailable; boundary contract only"
    ),
    OutputPassportUnavailableReason.RUNTIME_GENERATION_UNAVAILABLE.value: (
        "Live runtime passport generation unavailable"
    ),
}


class OutputPassportCLIBindingStatus(str, Enum):
    """CLI binding availability."""

    CLI_READ_ONLY = "CLI_READ_ONLY"
    UNAVAILABLE_CLI_BINDING = "UNAVAILABLE_CLI_BINDING"


class OutputPassportTUIBindingStatus(str, Enum):
    """TUI binding availability."""

    UNAVAILABLE_TUI_BINDING = "UNAVAILABLE_TUI_BINDING"
    TUI_READ_ONLY = "TUI_READ_ONLY"


class OutputPassportShellBindingUnavailableReason(str, Enum):
    """Shell binding unavailable taxonomy."""

    SHELL_UI_UNAVAILABLE = "SHELL_UI_UNAVAILABLE"
    P2_SHELL_NOT_STARTED = "P2_SHELL_NOT_STARTED"


class OutputPassportInspectCommandKind(str, Enum):
    """Read-only inspect commands."""

    INSPECT = "inspect"
    PROJECTION = "projection"
    UNAVAILABLE = "unavailable"


class P19P2ReadinessStatus(str, Enum):
    """P2 gate derived from seal evidence."""

    NOT_READY_FOR_P2 = "NOT_READY_FOR_P2"
    READY_FOR_P2_REVIEW = "READY_FOR_P2_REVIEW"
    BLOCKED = "BLOCKED"


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


@dataclass(frozen=True)
class P19DIntegrationTailSideEffectProof(_CanonicalMixin):
    """Extended side-effect truth for P1.9-D integration tail."""

    ledger_written: bool = False
    global_trace_written: bool = False
    trace_verified: bool = False
    evidence_finalized: bool = False
    memory_read: bool = False
    memory_written: bool = False
    policy_enforced: bool = False
    custos_called: bool = False
    authority_granted: bool = False
    approval_created: bool = False
    business_action_executed: bool = False
    workflow_executed: bool = False
    workflow_mutated: bool = False
    agent_executed: bool = False
    agent_authority_created: bool = False
    tool_executed: bool = False
    tool_permission_granted: bool = False
    runtime_mutated: bool = False
    passport_verified: bool = False
    event_emitted: bool = False
    api_server_started: bool = False
    cli_mutation_command_created: bool = False
    shell_ui_created: bool = False
    tui_product_ui_created: bool = False
    p2_started: bool = False
    exit_sealed: bool = False
    live_demo_passed: bool = False


@dataclass(frozen=True)
class OutputPassportInspectCommandContract(_CanonicalMixin):
    """Read-only inspect command contract."""

    schema_version: str
    command_kind: OutputPassportInspectCommandKind
    command_label: str
    read_only: bool
    dev_fixture_supported: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    contract_hash: str


@dataclass(frozen=True)
class OutputPassportCLIBindingStatusRecord(_CanonicalMixin):
    """CLI binding status record."""

    status: OutputPassportCLIBindingStatus
    inspect_command: OutputPassportInspectCommandContract
    unavailable_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputPassportTUIBindingStatusRecord(_CanonicalMixin):
    """TUI binding status record."""

    status: OutputPassportTUIBindingStatus
    unavailable_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel


@dataclass(frozen=True)
class OutputPassportReportIndexEntry(_CanonicalMixin):
    """Report index entry for docs sync."""

    report_filename: str
    pack_id: str
    indexed: bool
    truth_label: OutputPassportTruthLabel


@dataclass(frozen=True)
class OutputPassportStateSyncSummary(_CanonicalMixin):
    """State/progress sync summary."""

    active_task_updated: bool
    roadmap_mirror_updated: bool
    state_updated: bool
    reports_index_updated: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    summary_hash: str


@dataclass(frozen=True)
class OutputPassportDocsStateReportUpdate(_CanonicalMixin):
    """Docs/state/reports sync contract."""

    schema_version: str
    report_entries: tuple[OutputPassportReportIndexEntry, ...]
    state_sync_summary: OutputPassportStateSyncSummary
    report_chain: tuple[str, ...]
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    update_hash: str


@dataclass(frozen=True)
class P19DIntegrationTailPackResult(_CanonicalMixin):
    """P1.9-D integration tail pack result."""

    schema_version: str
    pack_id: str
    section_id: str
    covered_checkpoints: tuple[str, ...]
    checkpoint_reads: tuple[OutputPassportCheckpointRead, ...]
    checkpoint_statuses: Mapping[str, str]
    truth_labels: tuple[OutputPassportTruthLabel, ...]
    unavailable_reasons: tuple[OutputPassportUnavailableReason, ...]
    unavailable_reason_details: Mapping[str, str]
    projection_api_event_summary: str
    cli_tui_binding_summary: str
    docs_state_report_sync_summary: str
    exit_seal_checklist_summary: str
    live_integration_demo_summary: str
    p2_readiness_status: P19P2ReadinessStatus
    p2_readiness_reason: str
    next_section: str
    side_effect_proof: P19DIntegrationTailSideEffectProof
    source_label: OutputPassportSourceLabel
    result_hash: str


def build_output_passport_cli_binding_contract(
    *,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportInspectCommandContract:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_INSPECT_COMMAND_VERSION,
        "command_kind": OutputPassportInspectCommandKind.INSPECT,
        "command_label": "output-passport inspect --dev-fixture",
        "read_only": True,
        "dev_fixture_supported": True,
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportInspectCommandContract(
        **body,
        contract_hash=_hash_payload(body),
    )


def handle_output_passport_cli_inspect(
    *,
    dev_fixture: bool = True,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> dict[str, Any]:
    """Read-only CLI inspect handler; no mutation or authority."""
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    projection = build_output_passport_projection_contract(source_label=source_label)
    seal_summary = "exit_seal_pending_in_p1_9_30"
    if not dev_fixture:
        seal_summary = "dev_fixture_required_for_inspect"

    return {
        "command": "output-passport inspect",
        "dev_fixture": dev_fixture,
        "read_only": True,
        "authority_granted": False,
        "approval_created": False,
        "projection_payload_hash": projection.projection_payload.projection_payload_hash,
        "read_model_ref": projection.projection_payload.passport_read_model_ref,
        "projection_status": projection.projection_status.value,
        "api_runtime_status": projection.api_contract.runtime_status.value,
        "event_runtime_status": projection.event_contract.runtime_status.value,
        "trace_truth_boundary_summary": (
            projection.projection_payload.trace_truth_boundary_summary
        ),
        "seal_readiness_summary": seal_summary,
        "truth_labels": [
            OutputPassportTruthLabel.CONTRACT_ONLY.value,
            OutputPassportTruthLabel.DEV_FIXTURE.value,
        ],
        "source_label": source_label.value,
    }


def build_output_passport_cli_binding_status(
    *,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportCLIBindingStatusRecord:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    inspect = build_output_passport_cli_binding_contract(source_label=source_label)
    return OutputPassportCLIBindingStatusRecord(
        status=OutputPassportCLIBindingStatus.CLI_READ_ONLY,
        inspect_command=inspect,
        unavailable_reason="",
        truth_label=OutputPassportTruthLabel.CONTRACT_ONLY,
        source_label=source_label,
    )


def build_output_passport_tui_binding_status(
    *,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportTUIBindingStatusRecord:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    return OutputPassportTUIBindingStatusRecord(
        status=OutputPassportTUIBindingStatus.UNAVAILABLE_TUI_BINDING,
        unavailable_reason=TUI_BINDING_UNAVAILABLE_REASON,
        truth_label=OutputPassportTruthLabel.UNAVAILABLE,
        source_label=source_label,
    )


def build_output_passport_docs_state_report_update(
    *,
    repo_root: Path | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> OutputPassportDocsStateReportUpdate:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    root = repo_root or Path(__file__).resolve().parents[3]
    reports_dir = root / "agent" / "reports"
    pack_ids = ("P1.9-A", "P1.9-B", "P1.9-C", "P1.9-D")
    entries: list[OutputPassportReportIndexEntry] = []
    for filename, pack_id in zip(P19_REPORT_CHAIN, pack_ids, strict=True):
        indexed = (reports_dir / filename).is_file()
        entries.append(
            OutputPassportReportIndexEntry(
                report_filename=filename,
                pack_id=pack_id,
                indexed=indexed,
                truth_label=OutputPassportTruthLabel.CONTRACT_ONLY,
            )
        )

    state_sync_body = {
        "active_task_updated": True,
        "roadmap_mirror_updated": True,
        "state_updated": True,
        "reports_index_updated": True,
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
    }
    state_sync = OutputPassportStateSyncSummary(
        **state_sync_body,
        summary_hash=_hash_payload(state_sync_body),
    )
    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_DOCS_SYNC_VERSION,
        "report_entries": tuple(entries),
        "state_sync_summary": state_sync,
        "report_chain": P19_REPORT_CHAIN,
        "truth_label": OutputPassportTruthLabel.CONTRACT_ONLY,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return OutputPassportDocsStateReportUpdate(
        **body,
        update_hash=_hash_payload(body),
    )


def _default_p1_9_d_checkpoint_reads() -> tuple[OutputPassportCheckpointRead, ...]:
    definitions = (
        ("P1.9.27", "Output Passport Projection/API/Event Contract"),
        ("P1.9.28", "Output Passport Shell/CLI/TUI Binding"),
        ("P1.9.29", "Output Passport Docs/State/Reports Update"),
        ("P1.9.30", "P1.9 Exit Seal + Live Integration Demo"),
    )
    truth_map = {
        "P1.9.27": OutputPassportTruthLabel.CONTRACT_ONLY,
        "P1.9.28": OutputPassportTruthLabel.CONTRACT_ONLY,
        "P1.9.29": OutputPassportTruthLabel.CONTRACT_ONLY,
        "P1.9.30": OutputPassportTruthLabel.CONTRACT_ONLY,
    }
    limitations_map = {
        "P1.9.27": (
            "Projection is not execution.",
            "API contract is not API server.",
            "Event contract is not emitted event.",
        ),
        "P1.9.28": (
            "CLI inspect is read-only.",
            "TUI binding unavailable.",
            "No P2 shell UI.",
        ),
        "P1.9.29": (
            "Docs sync is not proof.",
            "Roadmap mirror only.",
        ),
        "P1.9.30": (
            "P1 contract-scope seal is evidence-gated.",
            "Live demo is DEV_FIXTURE/operator-testable unless proven production LIVE.",
            "Trace verification remains unavailable unless actual verifier proof exists.",
        ),
    }
    reads: list[OutputPassportCheckpointRead] = []
    for checkpoint_id, canonical_name in definitions:
        reads.append(
            OutputPassportCheckpointRead(
                checkpoint_id=checkpoint_id,
                canonical_name=canonical_name,
                status=OutputPassportCheckpointStatus.DONE,
                truth_label=truth_map[checkpoint_id],
                unavailable_reason=None,
                limitations=limitations_map[checkpoint_id],
                evidence_ref=f"{checkpoint_id.lower().replace('.', '_')}_contract",
            )
        )
    return tuple(reads)


def _all_false_p19d_side_effects() -> P19DIntegrationTailSideEffectProof:
    return P19DIntegrationTailSideEffectProof()


def build_p1_9_d_integration_tail_pack_result(
    *,
    repo_root: Path | None = None,
) -> P19DIntegrationTailPackResult:
    from .exit_seal import (
        build_p1_9_exit_seal_checklist,
        build_p1_9_live_integration_demo_result,
        run_p1_9_exit_seal_checklist,
    )

    projection = build_output_passport_projection_contract()
    cli_status = build_output_passport_cli_binding_status()
    tui_status = build_output_passport_tui_binding_status()
    docs_update = build_output_passport_docs_state_report_update(repo_root=repo_root)
    seal_checklist = build_p1_9_exit_seal_checklist(repo_root=repo_root)
    seal_result = run_p1_9_exit_seal_checklist(seal_checklist)
    live_demo = build_p1_9_live_integration_demo_result()

    p1_9_a = build_p1_9_a_passport_pack_result()
    p1_9_b = build_p1_9_b_read_model_test_harness_binding_pack_result()
    p1_9_c = build_p1_9_c_truth_boundary_failure_readiness_pack_result()

    projection_summary = (
        f"projection={projection.contract_hash[:12]}; "
        f"api={projection.api_contract.runtime_status.value}; "
        f"event={projection.event_contract.runtime_status.value}"
    )
    cli_tui_summary = (
        f"cli={cli_status.status.value}; "
        f"tui={tui_status.status.value}; "
        f"command={cli_status.inspect_command.command_label}"
    )
    docs_summary = (
        f"reports_indexed={sum(1 for e in docs_update.report_entries if e.indexed)}; "
        f"chain={len(docs_update.report_chain)}"
    )
    seal_summary = (
        f"decision={seal_result.decision.value}; "
        f"qualification={seal_result.seal_qualification.value}; "
        f"passed={seal_result.checklist_passed}; "
        f"checks={len(seal_result.checklist.checks)}"
    )
    live_summary = (
        f"status={live_demo.demo_status.value}; "
        f"truth={live_demo.truth_label.value}; "
        f"passed={live_demo.demo_passed}"
    )

    p2_status = seal_result.p2_readiness_status
    p2_reason = seal_result.p2_readiness_reason

    checkpoint_reads = _default_p1_9_d_checkpoint_reads()
    checkpoint_statuses = {
        read.checkpoint_id: read.status.value for read in checkpoint_reads
    }
    truth_labels = (
        OutputPassportTruthLabel.CONTRACT_ONLY,
        OutputPassportTruthLabel.DEV_FIXTURE,
        OutputPassportTruthLabel.NOT_VERIFIED,
        OutputPassportTruthLabel.UNAVAILABLE,
    )
    unavailable_reasons = (
        OutputPassportUnavailableReason.CLI_SHELL_TUI_UNAVAILABLE,
        OutputPassportUnavailableReason.PROJECTION_UNAVAILABLE,
        OutputPassportUnavailableReason.TRACE_VERIFICATION_UNAVAILABLE,
        OutputPassportUnavailableReason.RUNTIME_GENERATION_UNAVAILABLE,
    )
    side_effects = _all_false_p19d_side_effects()

    result_payload = {
        "schema_version": OUTPUT_PASSPORT_P1_9_D_PACK_RESULT_VERSION,
        "pack_id": OUTPUT_PASSPORT_P1_9_D_PACK_TASK_ID,
        "section_id": OUTPUT_PASSPORT_P1_9_D_SECTION_ID,
        "covered_checkpoints": OUTPUT_PASSPORT_P1_9_D_CHECKPOINT_IDS,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_statuses": checkpoint_statuses,
        "truth_labels": truth_labels,
        "unavailable_reasons": unavailable_reasons,
        "unavailable_reason_details": P19_D_UNAVAILABLE_REASON_DETAILS,
        "projection_api_event_summary": projection_summary,
        "cli_tui_binding_summary": cli_tui_summary,
        "docs_state_report_sync_summary": docs_summary,
        "exit_seal_checklist_summary": seal_summary,
        "live_integration_demo_summary": live_summary,
        "p2_readiness_status": p2_status,
        "p2_readiness_reason": p2_reason,
        "next_section": OUTPUT_PASSPORT_P1_9_D_NEXT_SECTION,
        "side_effect_proof": side_effects,
        "source_label": OutputPassportSourceLabel.DEV_FIXTURE,
        "p1_9_a_pack": p1_9_a.pack_id,
        "p1_9_b_pack": p1_9_b.pack_id,
        "p1_9_c_pack": p1_9_c.pack_id,
    }
    return P19DIntegrationTailPackResult(
        schema_version=result_payload["schema_version"],
        pack_id=result_payload["pack_id"],
        section_id=result_payload["section_id"],
        covered_checkpoints=result_payload["covered_checkpoints"],
        checkpoint_reads=result_payload["checkpoint_reads"],
        checkpoint_statuses=result_payload["checkpoint_statuses"],
        truth_labels=result_payload["truth_labels"],
        unavailable_reasons=result_payload["unavailable_reasons"],
        unavailable_reason_details=result_payload["unavailable_reason_details"],
        projection_api_event_summary=projection_summary,
        cli_tui_binding_summary=cli_tui_summary,
        docs_state_report_sync_summary=docs_summary,
        exit_seal_checklist_summary=seal_summary,
        live_integration_demo_summary=live_summary,
        p2_readiness_status=p2_status,
        p2_readiness_reason=p2_reason,
        next_section=OUTPUT_PASSPORT_P1_9_D_NEXT_SECTION,
        side_effect_proof=side_effects,
        source_label=OutputPassportSourceLabel.DEV_FIXTURE,
        result_hash=_hash_payload(result_payload),
    )


def serialize_p1_9_d_integration_tail_pack_result(
    result: P19DIntegrationTailPackResult,
) -> str:
    return to_canonical_json(result)
