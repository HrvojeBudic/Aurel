"""P1.7.19 tests: docs/state/reports truth sync and anti-overclaim anchors."""
from __future__ import annotations

import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

P17_REPORTS = [
    "P1.7.0_PATH_GOVERNANCE_SOURCE_TRUST_FOUNDATION.md",
    "P1.7.1_PATH_IDENTITY_CANONICAL_PATH_SCHEMA.md",
    "P1.7.2_SOURCE_IDENTITY_SOURCE_REF_SCHEMA.md",
    "P1.7.3_SOURCE_TRUST_LABEL_TAXONOMY.md",
    "P1.7.4_TRUSTED_ROOT_SCOPE_REGISTRY_SEED.md",
    "P1.7.5_PATH_NORMALIZATION_ESCAPE_DETECTION_CONTRACT.md",
    "P1.7.6_PATH_AUTHORITY_SCOPE_MODEL.md",
    "P1.7.7_UNTRUSTED_CONTENT_BOUNDARY_MODEL.md",
    "P1.7.8_SOURCE_PROVENANCE_EVIDENCE_BINDING_SEED.md",
    "P1.7.9_PATH_SOURCE_RISK_CLASSIFICATION_MODEL.md",
    "P1.7.10_PATH_GOVERNANCE_RESOLVER_SHADOW_MODE.md",
    "P1.7.11_SOURCE_TRUST_RESOLVER_SHADOW_MODE.md",
    "P1.7.12_PATH_SOURCE_CONFLICT_PRECEDENCE_RULES.md",
    "P1.7.13_PATH_RESOLUTION_TRACE_HOOK.md",
    "P1.7.14_PATH_VIOLATION_DRIFT_TRACE_HOOK.md",
    "P1.7.15_PATH_GOVERNANCE_TEST_HARNESS.md",
    "P1.7.16_POLICY_CONTEXT_BRIDGE.md",
    "P1.7.17_PATH_GOVERNANCE_PROJECTION_API_EVENT_CONTRACT.md",
    "P1.7.18_PATH_GOVERNANCE_CLI_TUI_BINDING.md",
    "P1.7.19_DOCS_STATE_REPORTS_UPDATE.md",
]


def _read(path: str) -> str:
    full = os.path.join(REPO, path)
    if os.path.isfile(full):
        with open(full) as f:
            return f.read()
    return ""


def test_p17_report_files_exist():
    for name in P17_REPORTS:
        path = os.path.join(REPO, "agent/reports", name)
        assert os.path.isfile(path), f"Missing report: {name}"


def test_reports_index_references_p17_reports():
    reports = _read("agent/REPORTS.md")
    for n in range(0, 20):
        assert f"P1.7.{n}" in reports, f"P1.7.{n} not indexed in REPORTS.md"


def test_roadmap_marks_p17_19_complete_p17_20_next():
    roadmap = _read("agent/ROADMAP.md")
    assert "P1.7.19" in roadmap
    assert "P1.7.20" in roadmap
    assert "Docs / State / Reports Update" in roadmap or "Docs/State/Reports Update" in roadmap


def test_active_task_points_to_p17_20_next():
    active = _read("agent/ACTIVE_TASK.md")
    assert "P1.7.20" in active
    assert "Exit Seal" in active


def test_state_contains_unavailable_anchors():
    state = _read("agent/STATE.md")
    for phrase in ("Shell UI", "HTTP", "policy runtime", "Ledger", "global trace"):
        assert phrase in state, f"STATE.md missing unavailable anchor: {phrase}"


def test_tests_doc_contains_p17_validation_command():
    tests_doc = _read("agent/TESTS.md")
    assert "test_p1_7_0_foundation" in tests_doc


def test_docs_do_not_claim_p17_20_complete():
    scanned = "\n".join(
        _read(p)
        for p in (
            "agent/ACTIVE_TASK.md",
            "agent/STATE.md",
            "agent/ROADMAP.md",
        )
    )
    assert "P1.7.20 COMPLETE" not in scanned
    assert "P1.7 section SEALED" not in scanned.upper()


def test_p17_19_report_exists():
    path = os.path.join(REPO, "agent/reports/P1.7.19_DOCS_STATE_REPORTS_UPDATE.md")
    assert os.path.isfile(path)
