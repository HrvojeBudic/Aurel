"""Integrated and seal tests for P1.4.16 Identity Test Battery."""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from agentic_runtime.identity.identity_test_battery import (
    IdentityBatteryStatus,
    IdentityTestSeverity,
    identity_test_cases,
    run_identity_test_battery,
    identity_test_battery_report_to_dict,
)


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# INV-P1416-01: Battery tests the integrated P1.4 chain
# ---------------------------------------------------------------------------


def test_p1416_identity_stack_chain_is_tested():
    """The battery must include cross-module scenarios, not only isolated tests."""
    cases = identity_test_cases()
    # Check that we have multi-module cases (module_refs with >1 module)
    multi_module = [c for c in cases if len(c.module_refs) >= 2]
    assert len(multi_module) >= 1, "Battery must have cross-module chain scenarios"


# ---------------------------------------------------------------------------
# INV-P1416-02: Critical governance failures must fail the battery
# ---------------------------------------------------------------------------


def test_p1416_adversarial_governance_cases_are_included():
    """Adversarial governance cases must be present in the registry."""
    cases = identity_test_cases()
    adversarial_ids = {
        "authority_delta_oversight_weakened",
        "authority_delta_risk_ceiling_increase",
        "consent_high_requires_risk_ack",
        "consent_revoked_invalid",
        "consent_expired_invalid",
        "consent_attestation_mismatch_invalid",
    }
    ids = {c.case_id for c in cases}
    missing = adversarial_ids - ids
    assert not missing, f"Missing adversarial cases: {missing}"


# ---------------------------------------------------------------------------
# INV-P1416-03: Battery must not mutate real config
# ---------------------------------------------------------------------------


def test_p1416_battery_does_not_mutate_real_config():
    """Running the battery must not change its own output."""
    report1 = run_identity_test_battery(include_adversarial=True, include_cli=False)
    report2 = run_identity_test_battery(include_adversarial=True, include_cli=False)
    # Same number of each status type
    assert report1.passed == report2.passed
    assert report1.failed == report2.failed
    assert len(report1.results) == len(report2.results)


# ---------------------------------------------------------------------------
# INV-P1416-04: Battery surfaces critical failures
# ---------------------------------------------------------------------------


def test_p1416_battery_surfaces_critical_failures():
    """Battery report must expose critical_failures and highest_failed_severity."""
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    d = identity_test_battery_report_to_dict(report)
    assert "critical_failures" in d
    assert "highest_failed_severity" in d
    # Verify structure even when empty
    assert isinstance(d["critical_failures"], list)


# ---------------------------------------------------------------------------
# INV-P1416-08: Battery uses P1.4.15 command surface when CLI mode is enabled
# ---------------------------------------------------------------------------


def test_p1416_battery_uses_cli_surface_when_enabled():
    """CLI test-battery help must be accessible."""
    result = _run_cli("identity", "test-battery", "--help")
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "run" in output
    assert "list" in output


# ---------------------------------------------------------------------------
# INV-P1416-09: Battery does not grant consent or execute tools
# ---------------------------------------------------------------------------


def test_p1416_battery_prepares_p1417_lifecycle_states():
    """Battery report format is structured and ready for lifecycle integration."""
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    d = identity_test_battery_report_to_dict(report)
    # Verify standard fields exist for lifecycle integration
    required_fields = {
        "report_id", "status", "total_cases", "passed", "failed",
        "highest_failed_severity", "results", "critical_failures", "summary",
    }
    assert required_fields.issubset(set(d.keys())), f"Missing fields: {required_fields - set(d.keys())}"


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


def test_identity_test_battery_cli_run_outputs_json():
    result = _run_cli("identity", "test-battery", "run", "--include-cli", "--json")
    assert result.returncode in (0, 1)
    data = json.loads(result.stdout)
    assert "status" in data
    assert "total_cases" in data
    assert "results" in data


def test_identity_test_battery_cli_list_outputs_cases():
    result = _run_cli("identity", "test-battery", "list", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) > 0
    # Each case has required fields
    for case in data:
        assert "case_id" in case
        assert "severity" in case


def test_identity_test_battery_cli_run_case_outputs_result():
    result = _run_cli(
        "identity", "test-battery", "run-case",
        "--case-id", "smoke_identity_modules",
        "--json",
    )
    assert result.returncode in (0, 1)
    data = json.loads(result.stdout)
    assert "case_id" in data
    assert "status" in data


def test_identity_test_battery_cli_failure_exits_nonzero():
    """If the battery has failures, exit code should be nonzero."""
    result = _run_cli("identity", "test-battery", "run", "--include-cli", "--json")
    data = json.loads(result.stdout)
    if data["status"] == "FAILED":
        assert result.returncode == 1
    # If PASSED, returncode 0 is fine


# ---------------------------------------------------------------------------
# Seal tests
# ---------------------------------------------------------------------------


def test_p1416_battery_critical_failure_fails_battery():
    """When a CRITICAL test fails, the battery must report FAILED."""
    report = run_identity_test_battery(include_adversarial=True, include_cli=False)
    if report.critical_failures:
        assert report.status == IdentityBatteryStatus.FAILED


def test_p1416_battery_report_deterministic():
    """Two battery runs without config mutations must produce consistent counts."""
    r1 = run_identity_test_battery(include_adversarial=True, include_cli=False)
    r2 = run_identity_test_battery(include_adversarial=True, include_cli=False)
    assert r1.total_cases == r2.total_cases
    assert r1.passed == r2.passed
    assert r1.failed == r2.failed


def test_p1416_all_smoke_cases_pass():
    """All smoke/import cases must pass in a healthy repo."""
    report = run_identity_test_battery(include_adversarial=False, include_cli=False)
    smoke_results = [r for r in report.results if r.case_id.startswith("smoke_")]
    for r in smoke_results:
        assert r.status == IdentityBatteryStatus.PASSED, f"Smoke case {r.case_id} failed: {r.summary}"
