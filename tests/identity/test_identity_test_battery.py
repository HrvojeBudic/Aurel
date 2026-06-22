"""Core tests for P1.4.16 Identity Test Battery."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.identity.identity_test_battery import (
    IdentityBatteryStatus,
    IdentityTestCase,
    IdentityTestResult,
    IdentityTestBatteryReport,
    IdentityTestSeverity,
    format_identity_test_battery_report,
    identity_test_battery_report_to_dict,
    identity_test_cases,
    identity_test_result_to_dict,
    run_identity_test_battery,
    run_identity_test_case,
)


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


def test_identity_test_case_registry_not_empty():
    cases = identity_test_cases()
    assert len(cases) > 0, "Test case registry must not be empty"


def test_identity_test_case_ids_are_unique():
    cases = identity_test_cases()
    ids = [c.case_id for c in cases]
    assert len(ids) == len(frozenset(ids)), f"Duplicate case IDs: {ids}"


def test_all_cases_have_module_refs():
    cases = identity_test_cases()
    for c in cases:
        assert c.module_refs, f"Case {c.case_id} has no module_refs"
        assert c.description, f"Case {c.case_id} has no description"


def test_all_cases_have_severity():
    cases = identity_test_cases()
    for c in cases:
        assert c.severity in IdentityTestSeverity


# ---------------------------------------------------------------------------
# Run battery tests
# ---------------------------------------------------------------------------


def test_run_identity_test_battery_returns_report():
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    assert isinstance(report, IdentityTestBatteryReport)
    assert report.total_cases > 0
    assert report.status in IdentityBatteryStatus


def test_battery_report_counts_results():
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    total = report.passed + report.failed + report.degraded + report.skipped
    assert total == report.total_cases
    assert len(report.results) == total


def test_battery_report_is_json_serializable():
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    d = identity_test_battery_report_to_dict(report)
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["status"] in {"PASSED", "FAILED", "DEGRADED", "SKIPPED"}
    assert isinstance(parsed["results"], list)


def test_battery_report_has_results_list():
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    d = identity_test_battery_report_to_dict(report)
    assert len(d["results"]) == report.total_cases


def test_battery_report_has_report_id():
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    assert report.report_id.startswith("itb_")


# ---------------------------------------------------------------------------
# Human summary tests
# ---------------------------------------------------------------------------


def test_battery_human_summary_mentions_failures():
    report = IdentityTestBatteryReport(
        report_id="test",
        status=IdentityBatteryStatus.FAILED,
        total_cases=5,
        passed=3,
        failed=2,
        degraded=0,
        skipped=0,
        highest_failed_severity=IdentityTestSeverity.CRITICAL,
        results=(),
        critical_failures=("case_x",),
        warnings=(),
        summary="test",
    )
    text = format_identity_test_battery_report(report)
    assert "FAILED" in text
    assert "case_x" in text
    assert "Failed: 2" in text


def test_battery_human_summary_mentions_next():
    report = IdentityTestBatteryReport(
        report_id="test",
        status=IdentityBatteryStatus.PASSED,
        total_cases=5,
        passed=5,
        failed=0,
        degraded=0,
        skipped=0,
        highest_failed_severity=None,
        results=(),
        critical_failures=(),
        warnings=(),
        summary="all good",
    )
    text = format_identity_test_battery_report(report)
    assert "Next:" in text


# ---------------------------------------------------------------------------
# Run single case tests
# ---------------------------------------------------------------------------


def test_run_single_case_returns_result():
    cases = identity_test_cases()
    smoke_case = [c for c in cases if c.case_id == "smoke_identity_modules"]
    if smoke_case:
        result = run_identity_test_case(smoke_case[0])
        assert isinstance(result, IdentityTestResult)
        assert result.case_id == "smoke_identity_modules"
        assert result.status in IdentityBatteryStatus


def test_run_case_without_runner_skips():
    fake_case = IdentityTestCase(
        case_id="nonexistent",
        name="Fake",
        description="Nonexistent case",
        severity=IdentityTestSeverity.INFO,
        module_refs=("none",),
        invariant_refs=(),
    )
    result = run_identity_test_case(fake_case)
    assert result.status == IdentityBatteryStatus.SKIPPED


# ---------------------------------------------------------------------------
# Test result serialization
# ---------------------------------------------------------------------------


def test_identity_test_result_to_dict():
    r = IdentityTestResult(
        case_id="test_1",
        status=IdentityBatteryStatus.PASSED,
        severity=IdentityTestSeverity.HIGH,
        summary="all good",
        errors=("e1",),
        warnings=("w1",),
        evidence_refs=("ref1",),
        duration_ms=42,
    )
    d = identity_test_result_to_dict(r)
    assert d["case_id"] == "test_1"
    assert d["status"] == "PASSED"
    assert d["severity"] == "HIGH"
    assert d["errors"] == ["e1"]
    assert d["duration_ms"] == 42


# ---------------------------------------------------------------------------
# Battery categories coverage
# ---------------------------------------------------------------------------


def test_battery_includes_smoke_cases():
    cases = identity_test_cases()
    smoke = [c for c in cases if c.case_id.startswith("smoke_")]
    assert len(smoke) >= 8, f"Expected at least 8 smoke cases, got {len(smoke)}"


def test_battery_includes_authority_delta_cases():
    cases = identity_test_cases()
    ad = [c for c in cases if "authority_delta" in c.case_id]
    assert len(ad) >= 3, f"Expected at least 3 authority delta cases, got {len(ad)}"


def test_battery_includes_consent_cases():
    cases = identity_test_cases()
    consent = [c for c in cases if c.case_id.startswith("consent_")]
    assert len(consent) >= 7, f"Expected at least 7 consent cases, got {len(consent)}"


def test_battery_includes_cli_cases():
    cases = identity_test_cases()
    cli_cases = [c for c in cases if c.case_id.startswith("cli_")]
    assert len(cli_cases) >= 4, f"Expected at least 4 CLI cases, got {len(cli_cases)}"
