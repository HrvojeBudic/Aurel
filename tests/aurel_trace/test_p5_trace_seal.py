"""P5.20 — P5 exit-seal checklist and derived seal status."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    P5ExitSealReport,
    P5ItemStatus,
    P5TraceSealStatus,
    build_all_p5_handoff_contracts,
    build_p5_capability_coverage_matrix,
    build_p5_exit_seal_report,
    build_p5_trace_seal_checklist,
    build_p5_truth_label_audit,
    build_p5_unavailable_surface_registry,
)
from agentic_runtime.aurel_trace.p5_seal import _PACK_REPORTS

_ALL_REPORTS = tuple(_PACK_REPORTS.values())


def _report(*, available, audit=None):
    checklist = build_p5_trace_seal_checklist(available_reports=available)
    matrix = build_p5_capability_coverage_matrix(available_reports=available)
    return build_p5_exit_seal_report(
        checklist=checklist,
        coverage_matrix=matrix,
        truth_label_audit=audit or build_p5_truth_label_audit(),
        unavailable_registry=build_p5_unavailable_surface_registry(),
        handoffs=build_all_p5_handoff_contracts(),
        remaining_risks=("replay remains UNAVAILABLE",),
    )


def test_checklist_covers_all_six_packs():
    checklist = build_p5_trace_seal_checklist(available_reports=_ALL_REPORTS)
    packs = {i.pack_id for i in checklist.items}
    assert packs == {"P5-A", "P5-B", "P5-C", "P5-D", "P5-E", "P5-F"}
    assert checklist.status is P5TraceSealStatus.SEALED
    assert checklist.blocked_count == 0


def test_missing_report_blocks_checklist_and_seal():
    partial = tuple(r for r in _ALL_REPORTS if "P5_TRACE_D" not in r)
    checklist = build_p5_trace_seal_checklist(available_reports=partial)
    assert checklist.status is P5TraceSealStatus.BLOCKED
    blocked = [i for i in checklist.items if i.status is P5ItemStatus.BLOCKED]
    assert len(blocked) == 1
    assert blocked[0].pack_id == "P5-D"
    report = _report(available=partial)
    assert report.seal_status is P5TraceSealStatus.BLOCKED


def test_full_evidence_seals():
    report = _report(available=_ALL_REPORTS)
    assert report.seal_status is P5TraceSealStatus.SEALED
    assert report.next_domain.startswith("P6")


def test_checklist_is_deterministic():
    a = build_p5_trace_seal_checklist(available_reports=_ALL_REPORTS).to_dict()
    b = build_p5_trace_seal_checklist(available_reports=_ALL_REPORTS).to_dict()
    assert a == b


def test_seal_report_never_claims_production_readiness():
    report = _report(available=_ALL_REPORTS)
    assert report.claims_production_readiness is False
    assert report.claims_legal_compliance is False
    assert report.claims_replay_live is False
    assert report.claims_p6_implemented is False
    with pytest.raises(AurelTraceError):
        P5ExitSealReport(
            report_id="r",
            seal_status=P5TraceSealStatus.SEALED,
            checklist=report.checklist,
            coverage_matrix=report.coverage_matrix,
            truth_label_audit=report.truth_label_audit,
            unavailable_registry=report.unavailable_registry,
            handoff_p6=report.handoff_p6,
            handoff_p8=report.handoff_p8,
            handoff_p9=report.handoff_p9,
            remaining_risks=(),
            claims_production_readiness=True,
        )


def test_unavailable_registry_lists_required_surfaces():
    registry = build_p5_unavailable_surface_registry()
    names = {s.name for s in registry.surfaces}
    for required in (
        "actual replay",
        "production distributed ledger",
        "external export service",
        "legal compliance certification",
        "P6 object/data storage",
        "P8 model routing",
        "P9 policy enforcement",
        "Rust/WASM durable substrate",
    ):
        assert required in names
    for surface in registry.surfaces:
        assert surface.reason and surface.future_owner
