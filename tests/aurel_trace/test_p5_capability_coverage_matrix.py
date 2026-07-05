"""P5.20 — P5 capability coverage matrix."""

from __future__ import annotations

from agentic_runtime.aurel_trace import (
    P5DownstreamOwner,
    P5ItemStatus,
    build_p5_capability_coverage_matrix,
)
from agentic_runtime.aurel_trace.p5_seal import _PACK_REPORTS

_ALL_REPORTS = tuple(_PACK_REPORTS.values())


def test_matrix_includes_all_major_capabilities():
    matrix = build_p5_capability_coverage_matrix(available_reports=_ALL_REPORTS)
    cap_ids = {r.capability_id for r in matrix.rows}
    for required in (
        "canonical_trace_envelope",
        "hash_verification",
        "verification_receipts",
        "schema_registry",
        "submit_coverage_audit",
        "evidence_refs",
        "runtime_submit_binding",
        "p3_binding",
        "p4_binding",
        "trace_verified_resolver",
        "trace_query_read_model",
        "trace_cli",
        "projection_feed",
        "golden_thread",
        "causal_graph",
        "time_slice_refs",
        "replay_readiness_assessment",
        "privacy_locality_labels",
        "redacted_trace_view",
        "export_manifest",
        "audit_bundle",
        "persistent_backend_profile",
        "persistent_integrity_assessment",
        "p5_seal_checklist",
        "p5_truth_label_audit",
        "p5_unavailable_registry",
        "p5_to_p6_handoff",
        "p5_to_p8_handoff",
        "p5_to_p9_handoff",
    ):
        assert required in cap_ids


def test_every_row_has_module_tests_report():
    matrix = build_p5_capability_coverage_matrix(available_reports=_ALL_REPORTS)
    for row in matrix.rows:
        assert row.module
        assert row.tests
        assert row.report
        assert row.status in P5ItemStatus


def test_downstream_owners_named_where_relevant():
    matrix = build_p5_capability_coverage_matrix(available_reports=_ALL_REPORTS)
    by_cap = {r.capability_id: r for r in matrix.rows}
    assert by_cap["p5_to_p6_handoff"].downstream_owner is P5DownstreamOwner.P6_DATA_OBJECT_PLANE
    assert by_cap["p5_to_p8_handoff"].downstream_owner is P5DownstreamOwner.P8_ATLAS_MODEL_ROUTER
    assert by_cap["p5_to_p9_handoff"].downstream_owner is P5DownstreamOwner.P9_CUSTOS_POLICY_RUNTIME
    assert by_cap["replay_readiness_assessment"].downstream_owner is P5DownstreamOwner.P13_REPLAY_FUTURE


def test_counts_deterministic_and_all_covered_with_full_evidence():
    a = build_p5_capability_coverage_matrix(available_reports=_ALL_REPORTS)
    b = build_p5_capability_coverage_matrix(available_reports=_ALL_REPORTS)
    assert a.to_dict() == b.to_dict()
    assert a.blocked_count == 0
    assert a.covered_count == len(a.rows)


def test_missing_report_blocks_matching_rows():
    partial = tuple(r for r in _ALL_REPORTS if "P5_TRACE_F" not in r)
    matrix = build_p5_capability_coverage_matrix(available_reports=partial)
    blocked = [r for r in matrix.rows if r.status is P5ItemStatus.BLOCKED]
    assert blocked
    assert all(r.pack_id == "P5-F" for r in blocked)
