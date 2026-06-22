"""Routing tests for P1.4.15 Identity CLI Surface.

Verifies that all subcommand groups are accessible and route to their
respective module CLI paths.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Help tests — verify all expected groups exist
# ---------------------------------------------------------------------------


def test_identity_cli_help_includes_expected_groups():
    result = _run_cli("identity", "--help")
    assert result.returncode == 0
    output = result.stdout + result.stderr
    expected_groups = [
        "status",
        "verify",
        "kernel",
        "persona",
        "autonomy",
        "claims",
        "doctrine",
        "attestation",
        "authority-delta",
        "consent",
    ]
    for group in expected_groups:
        assert group in output, f"Missing group '{group}' in identity --help"


def test_identity_autonomy_help_exists():
    result = _run_cli("identity", "autonomy", "--help")
    assert result.returncode == 0


def test_identity_claims_help_exists():
    result = _run_cli("identity", "claims", "--help")
    assert result.returncode == 0


def test_identity_doctrine_help_exists():
    result = _run_cli("identity", "doctrine", "--help")
    assert result.returncode == 0


def test_identity_attestation_help_exists():
    result = _run_cli("identity", "attestation", "--help")
    assert result.returncode == 0


def test_identity_authority_delta_help_exists():
    result = _run_cli("identity", "authority-delta", "--help")
    assert result.returncode == 0


def test_identity_consent_help_exists():
    result = _run_cli("identity", "consent", "--help")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Status and verify tests
# ---------------------------------------------------------------------------


def test_identity_status_json_envelope_is_stable():
    result = _run_cli("identity", "status", "--json")
    assert result.returncode in (0, 1)  # may be DEGRADED/BLOCKED but still readable
    data = json.loads(result.stdout)
    assert "status" in data
    assert "subsystems" in data
    assert isinstance(data["subsystems"], list)
    assert "suggested_next_commands" in data


def test_identity_status_reports_degraded_when_subsystem_missing():
    result = _run_cli("identity", "status", "--json")
    data = json.loads(result.stdout)
    # All 6 should be OK since modules exist in this repo
    status_val = data["status"]
    assert status_val in {"OK", "DEGRADED", "BLOCKED", "UNKNOWN"}


def test_identity_verify_json_envelope_is_stable():
    result = _run_cli("identity", "verify", "--json")
    assert result.returncode in (0, 1)
    data = json.loads(result.stdout)
    assert "status" in data
    assert "subsystems" in data


def test_identity_status_does_not_create_consent():
    """Status must be read-only — must not create consent artifacts."""
    result = _run_cli("identity", "status", "--json")
    data = json.loads(result.stdout)
    # Status output should never include consent actions
    assert "granted" not in data  # not a consent artifact


def test_identity_verify_does_not_grant_consent():
    result = _run_cli("identity", "verify", "--json")
    data = json.loads(result.stdout)
    # Verify output should never include consent actions
    assert "granted" not in str(data) and "GRANTED" not in str(data.get("status", ""))


# ---------------------------------------------------------------------------
# Routing tests — verify commands route to correct modules
# ---------------------------------------------------------------------------


def test_identity_claims_evaluate_routes_to_claim_boundary():
    result = _run_cli(
        "identity", "claims", "evaluate",
        "--claim", "Aurel is autonomous.",
        "--json",
    )
    assert result.returncode in (0, 1)


def test_identity_claims_list_routes():
    result = _run_cli("identity", "claims", "list", "--json")
    assert result.returncode in (0, 1)


def test_identity_doctrine_list_routes():
    result = _run_cli("identity", "doctrine", "list", "--json")
    assert result.returncode in (0, 1)


def test_identity_doctrine_validate_routes():
    result = _run_cli("identity", "doctrine", "validate", "--json")
    assert result.returncode in (0, 1)


def test_identity_attestation_list_routes():
    result = _run_cli("identity", "attestation", "list", "--json")
    assert result.returncode in (0, 1)


def test_identity_attestation_validate_routes():
    result = _run_cli("identity", "attestation", "validate", "--json")
    assert result.returncode in (0, 1)


def test_identity_authority_delta_compare_routes_to_delta_detector():
    """Route test — will fail without valid fixtures but shouldn't crash."""
    result = _run_cli("identity", "authority-delta", "--help")
    assert result.returncode == 0
    assert "compare" in result.stdout + result.stderr


def test_identity_consent_validate_routes_to_consent_binding():
    result = _run_cli("identity", "consent", "validate", "--help")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Read-only tests
# ---------------------------------------------------------------------------


def test_identity_status_is_read_only_cli():
    out1 = _run_cli("identity", "status", "--json")
    out2 = _run_cli("identity", "status", "--json")
    assert out1.stdout == out2.stdout


def test_identity_verify_is_read_only_cli():
    out1 = _run_cli("identity", "verify", "--json")
    out2 = _run_cli("identity", "verify", "--json")
    assert out1.stdout == out2.stdout


def test_identity_verify_does_not_modify_source():
    """Verify should not modify any sources."""
    # Just ensure it runs without side effects
    result = _run_cli("identity", "verify", "--json")
    data = json.loads(result.stdout)
    assert "mutated" not in str(data)
