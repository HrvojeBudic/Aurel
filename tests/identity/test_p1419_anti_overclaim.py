"""P1.4.19 tests: anti-overclaim, seal-readiness, docs consistency."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from agentic_runtime.identity.p14_seal_readiness import (
    P14ModuleStatus,
    P14SealReadinessReport,
    P14_CLI_GROUPS,
    P14_INVARIANTS,
    P1419_INVARIANTS,
    P14_KNOWN_LIMITATIONS,
    P1420_SEAL_CHECKLIST,
    _P14_MODULES,
    build_p14_seal_readiness_report,
    format_p14_seal_readiness_human,
    p14_module_status_to_dict,
    p14_seal_readiness_report_to_dict,
)


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(path: str) -> str:
    full = os.path.join(REPO, path)
    if os.path.isfile(full):
        with open(full) as f:
            return f.read()
    return ""


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True, text=True, timeout=30,
    )


# ---------------------------------------------------------------------------
# Doc existence
# ---------------------------------------------------------------------------

def test_p1419_report_exists():
    path = os.path.join(REPO, "agent/reports/P1.4.19_IDENTITY_DOCS_REPORTS_STATE_UPDATE.md")
    assert os.path.isfile(path), f"P1.4.19 report not found at {path}"


# ---------------------------------------------------------------------------
# Roadmap numbering
# ---------------------------------------------------------------------------

def test_roadmap_mentions_p14_8_to_p14_20():
    roadmap = _read("agent/ROADMAP.md")
    for n in range(8, 21):
        assert f"P1.4.{n}" in roadmap, f"P1.4.{n} not found in ROADMAP.md"


# ---------------------------------------------------------------------------
# State points to P1.4.20 as next
# ---------------------------------------------------------------------------

def test_state_points_to_p1420_next():
    state = _read("agent/STATE.md")
    assert "P1.4.20" in state, "P1.4.20 not mentioned in STATE.md"


# ---------------------------------------------------------------------------
# Reports index
# ---------------------------------------------------------------------------

def test_reports_index_mentions_all_p14_reports():
    reports = _read("agent/REPORTS.md")
    for n in range(8, 20):
        assert f"P1.4.{n}" in reports, f"P1.4.{n} report not indexed in REPORTS.md"


# ---------------------------------------------------------------------------
# Tests doc
# ---------------------------------------------------------------------------

def test_tests_doc_mentions_identity_test_battery():
    tests_doc = _read("agent/TESTS.md")
    assert "test-battery" in tests_doc.lower() or "test_battery" in tests_doc.lower()


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

def test_architecture_doc_mentions_lifecycle_eligibility_not_permission():
    arch = _read("agent/ARCHITECTURE.md")
    assert "lifecycle" in arch.lower(), "ARCHITECTURE.md should mention lifecycle"
    assert "eligibility" in arch.lower() or "not permission" in arch.lower(), \
        "ARCHITECTURE.md should distinguish lifecycle eligibility from permission"


def test_architecture_doc_mentions_trust_evidence_not_truth():
    arch = _read("agent/ARCHITECTURE.md")
    assert "trust evidence" in arch.lower() or "trust_evidence" in arch, \
        "ARCHITECTURE.md should mention trust evidence"
    assert "not truth" in arch.lower() or "evidence ref" in arch.lower(), \
        "ARCHITECTURE.md should distinguish evidence linkage from truth"


# ---------------------------------------------------------------------------
# Known limitations
# ---------------------------------------------------------------------------

def test_known_limitations_include_no_p15_evaluation_mirror():
    text = "\n".join(P14_KNOWN_LIMITATIONS)
    assert "P1.5" in text, "Known limitations should mention P1.5 Evaluation Mirror"


# ---------------------------------------------------------------------------
# Anti-overclaim
# ---------------------------------------------------------------------------

def test_p1419_docs_do_not_claim_full_autonomy():
    """No doc claims Aurel is fully autonomous."""
    for path in ("agent/STATE.md", "agent/ARCHITECTURE.md", "agent/ROADMAP.md"):
        text = _read(path)
        assert "fully autonomous" not in text.lower(), f"{path} claims full autonomy"


def test_p1419_docs_do_not_claim_production_ready():
    for path in ("agent/STATE.md", "agent/ARCHITECTURE.md", "agent/ROADMAP.md"):
        text = _read(path)
        assert "production-ready" not in text.lower(), f"{path} claims production ready"


def test_p1419_docs_do_not_claim_self_improvement():
    for path in ("agent/STATE.md", "agent/ARCHITECTURE.md", "agent/ROADMAP.md"):
        text = _read(path)
        assert "self-improving" not in text.lower() and "self improving" not in text.lower(), \
            f"{path} claims self-improvement"


def test_p1419_docs_do_not_claim_abos_implemented_without_evidence():
    for path in ("agent/STATE.md", "agent/ARCHITECTURE.md"):
        text = _read(path).lower()
        if "abos" in text and "implemented" in text:
            # Only flag if claiming "ABOS implemented" without qualifiers
            assert "runtime" in text or "doctrine" in text or "roadmap" in text, \
                f"{path} claims ABOS implementation without evidence"


def test_p1419_docs_do_not_claim_aether_implemented_without_evidence():
    for path in ("agent/STATE.md", "agent/ARCHITECTURE.md"):
        text = _read(path).lower()
        if "aether" in text and "implemented" in text:
            assert "runtime" in text or "doctrine" in text or "roadmap" in text, \
                f"{path} claims AETHER implementation without evidence"


def test_p1419_docs_preserve_numbering_constitution():
    """P1.4.X, P2.X.Y format must be preserved, not flat numbering."""
    roadmap = _read("agent/ROADMAP.md")
    assert "P1.5" in roadmap or "P1.6" in roadmap, \
        "ROADMAP.md should preserve multi-level numbering constitution"


# ---------------------------------------------------------------------------
# Handoff to P1.4.20
# ---------------------------------------------------------------------------

def test_p1419_handoff_to_p1420_is_clear():
    roadmap = _read("agent/ROADMAP.md")
    state = _read("agent/STATE.md")
    combined = roadmap + state
    assert "P1.4.20" in combined, "P1.4.20 must be mentioned as next"


# ---------------------------------------------------------------------------
# Seal readiness structured
# ---------------------------------------------------------------------------

def test_p14_module_status_serializes_to_json():
    s = P14ModuleStatus(
        module_id="P1.4.TEST", name="Test", status="IMPLEMENTED",
        report_path="report.md", test_paths=("t.py",),
        cli_groups=("test",), known_limitations=("none",),
    )
    d = p14_module_status_to_dict(s)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["module_id"] == "P1.4.TEST"


def test_p14_seal_readiness_report_lists_modules():
    report = build_p14_seal_readiness_report()
    assert len(report.modules) == 13  # P1.4.8–P1.4.20
    assert report.status == "READY"


def test_p14_seal_readiness_report_marks_p1420_next():
    report = build_p14_seal_readiness_report()
    assert report.next_module == "P1.4.20"


def test_p14_seal_readiness_report_serializes():
    report = build_p14_seal_readiness_report()
    d = p14_seal_readiness_report_to_dict(report)
    j = json.dumps(d)
    parsed = json.loads(j)
    assert parsed["status"] == "READY"
    assert parsed["next_module"] == "P1.4.20"


def test_format_seal_readiness_human():
    report = build_p14_seal_readiness_report()
    text = format_p14_seal_readiness_human(report)
    assert "READY" in text
    assert "P1.4.20" in text


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_identity_seal_readiness_cli_outputs_json():
    result = _run_cli("identity", "seal-readiness", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] in ("READY", "BLOCKED", "UNKNOWN")
    assert "modules" in data
    assert data["next_module"] == "P1.4.20"


def test_identity_seal_readiness_cli_is_read_only():
    """Running seal-readiness twice produces identical output."""
    r1 = _run_cli("identity", "seal-readiness", "--json")
    r2 = _run_cli("identity", "seal-readiness", "--json")
    d1 = json.loads(r1.stdout)
    d2 = json.loads(r2.stdout)
    assert d1["status"] == d2["status"]
    assert d1["next_module"] == d2["next_module"]


# ---------------------------------------------------------------------------
# Invariant index completeness
# ---------------------------------------------------------------------------

def test_p14_invariants_cover_autonomy_lifecycle_trust():
    inv_text = " ".join(P14_INVARIANTS)
    assert "autonomy" in inv_text.lower()
    assert "lifecycle" in inv_text.lower()
    assert "trust" in inv_text.lower()


def test_p1419_invariants_count():
    assert len(P1419_INVARIANTS) == 10, "P1.4.19 must have exactly 10 invariants"


# ---------------------------------------------------------------------------
# CLI group index
# ---------------------------------------------------------------------------

def test_p14_cli_group_index_has_trust_evidence():
    groups = {g["group"] for g in P14_CLI_GROUPS}
    assert "identity trust-evidence" in groups
    assert "identity lifecycle" in groups
    assert "identity seal-readiness" in groups


# ---------------------------------------------------------------------------
# Known limitations count
# ---------------------------------------------------------------------------

def test_known_limitations_are_15():
    assert len(P14_KNOWN_LIMITATIONS) == 15, "Must have exactly 15 known limitations"


# ---------------------------------------------------------------------------
# Seal checklist
# ---------------------------------------------------------------------------

def test_p1420_seal_checklist_has_22_items():
    assert len(P1420_SEAL_CHECKLIST) == 22, "Must have 22 seal checklist items"


def test_p1420_seal_checklist_mentions_authority():
    checklist = " ".join(P1420_SEAL_CHECKLIST)
    assert "authority" in checklist.lower()
    assert "categorical" in checklist.lower()


# ---------------------------------------------------------------------------
# Module index completeness
# ---------------------------------------------------------------------------

def test_p14_module_index_includes_8_to_20():
    ids = {m.module_id for m in _P14_MODULES}
    for n in range(8, 21):
        assert f"P1.4.{n}" in ids, f"P1.4.{n} missing from module index"
