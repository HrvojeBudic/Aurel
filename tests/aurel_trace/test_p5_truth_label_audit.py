"""P5.20 — P5 truth-label overclaim audit."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    P5TraceSealStatus,
    P5TruthFindingKind,
    P5TruthLabelAudit,
    build_all_p5_handoff_contracts,
    build_p5_capability_coverage_matrix,
    build_p5_exit_seal_report,
    build_p5_trace_seal_checklist,
    build_p5_truth_label_audit,
    build_p5_unavailable_surface_registry,
)
from agentic_runtime.aurel_trace.p5_seal import _PACK_REPORTS

_ALL_REPORTS = tuple(_PACK_REPORTS.values())


def test_honest_audit_passes():
    audit = build_p5_truth_label_audit()
    assert audit.passed is True
    assert audit.findings == ()


@pytest.mark.parametrize(
    "surface,kind",
    [
        ("trace_verified_label", P5TruthFindingKind.FAKE_TRACE_VERIFIED),
        ("replay", P5TruthFindingKind.FAKE_REPLAY),
        ("external_export", P5TruthFindingKind.FAKE_EXPORT_COMPLIANCE),
        ("production_durability", P5TruthFindingKind.FAKE_PRODUCTION_DURABILITY),
        ("shell_api", P5TruthFindingKind.FAKE_SHELL_API_AVAILABILITY),
        ("p6_implementation", P5TruthFindingKind.FAKE_P6_IMPLEMENTATION),
        ("p8_implementation", P5TruthFindingKind.FAKE_P8_IMPLEMENTATION),
        ("p9_implementation", P5TruthFindingKind.FAKE_P9_IMPLEMENTATION),
        ("policy_authority", P5TruthFindingKind.FAKE_POLICY_AUTHORITY),
        ("object_plane_ownership", P5TruthFindingKind.FAKE_OBJECT_PLANE_OWNERSHIP),
    ],
)
def test_fake_live_claim_is_detected(surface, kind):
    audit = build_p5_truth_label_audit(live_surface_claims={surface: True})
    assert audit.passed is False
    kinds = {f.finding_kind for f in audit.overclaims}
    assert kind in kinds


def test_blocking_audit_prevents_seal():
    audit = build_p5_truth_label_audit(live_surface_claims={"replay": True})
    report = build_p5_exit_seal_report(
        checklist=build_p5_trace_seal_checklist(available_reports=_ALL_REPORTS),
        coverage_matrix=build_p5_capability_coverage_matrix(available_reports=_ALL_REPORTS),
        truth_label_audit=audit,
        unavailable_registry=build_p5_unavailable_surface_registry(),
        handoffs=build_all_p5_handoff_contracts(),
    )
    assert report.seal_status is P5TraceSealStatus.BLOCKED


def test_passed_audit_cannot_carry_blocking_finding():
    audit = build_p5_truth_label_audit(live_surface_claims={"replay": True})
    finding = audit.findings[0]
    with pytest.raises(AurelTraceError):
        P5TruthLabelAudit(
            audit_id="a",
            findings=(finding,),
            passed=True,
            checked_surfaces=(),
        )
