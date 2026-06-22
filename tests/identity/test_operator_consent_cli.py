"""CLI tests for P1.4.14 Operator Consent Binding."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "consent"

# Build report and request fixtures at module scope
_DELTA_REPORT_PATH = FIXTURES / "delta_report.json"
_REQUEST_PATH = FIXTURES / "consent_request.json"
_RECORD_PATH = FIXTURES / "consent_record.json"
_DENIED_PATH = FIXTURES / "consent_denied.json"
_REVOKED_PATH = FIXTURES / "consent_revoked.json"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.fixture(scope="module", autouse=True)
def _build_fixtures():
    """Build JSON fixtures needed for CLI tests."""
    FIXTURES.mkdir(parents=True, exist_ok=True)

    delta_report = {
        "report_id": "adr_test_cli",
        "source_kind": "operator_contract",
        "deltas": [
            {
                "delta_id": "adt_cli_1",
                "delta_type": "RISK_CEILING_INCREASED",
                "severity": "HIGH",
                "source_kind": "operator_contract",
                "field_path": "risk_ceiling",
                "old_value": "low",
                "new_value": "high",
                "old_attestation_id": "srcatt_old_cli",
                "new_attestation_id": "srcatt_new_cli",
                "requires_operator_consent": True,
                "requires_evidence": False,
                "reason": "risk ceiling increased",
                "blockers": ["operator_consent_required"],
                "warnings": [],
            }
        ],
        "highest_severity": "HIGH",
        "requires_operator_consent": True,
        "requires_evidence": False,
        "summary": "CLI test delta report",
        "safe_to_auto_accept": False,
        "old_attestation_id": "srcatt_old_cli",
        "new_attestation_id": "srcatt_new_cli",
    }
    _DELTA_REPORT_PATH.write_text(json.dumps(delta_report, indent=2))

    # Build consent request via CLI
    result = _run_cli(
        "identity", "consent", "request",
        "--delta-report", str(_DELTA_REPORT_PATH),
        "--json",
    )
    if result.returncode == 0:
        _REQUEST_PATH.write_text(result.stdout)


@pytest.fixture(scope="module", autouse=True)
def _build_record():
    """Build a consent record via CLI grant."""
    if not _REQUEST_PATH.exists():
        return
    result = _run_cli(
        "identity", "consent", "grant",
        "--request", str(_REQUEST_PATH),
        "--operator-id", "operator.cli.test",
        "--ack-risk",
        "--json",
    )
    if result.returncode == 0:
        _RECORD_PATH.write_text(result.stdout)


def test_consent_cli_request_outputs_json():
    result = _run_cli(
        "identity", "consent", "request",
        "--delta-report", str(_DELTA_REPORT_PATH),
        "--json",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "request_id" in data
    assert "delta_ids" in data
    assert data["highest_severity"] == "HIGH"
    assert data["requires_explicit_risk_acknowledgement"] is True


def test_consent_cli_grant_outputs_record():
    result = _run_cli(
        "identity", "consent", "grant",
        "--request", str(_REQUEST_PATH),
        "--operator-id", "operator.cli.grant",
        "--ack-risk",
        "--json",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["status"] == "GRANTED"
    assert data["risk_acknowledged"] is True


def test_consent_cli_grant_requires_ack_risk_for_high_delta():
    result = _run_cli(
        "identity", "consent", "grant",
        "--request", str(_REQUEST_PATH),
        "--operator-id", "operator.cli.noack",
        "--json",
    )
    assert result.returncode == 1, "Should fail without --ack-risk for HIGH severity"
    data = json.loads(result.stdout)
    assert "risk_acknowledgement_required" in data.get("blockers", [])


def test_consent_cli_deny_outputs_denied_record():
    result = _run_cli(
        "identity", "consent", "deny",
        "--request", str(_REQUEST_PATH),
        "--operator-id", "operator.cli.deny",
        "--reason", "too broad scope",
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "DENIED"


def test_consent_cli_validate_accepts_valid_record():
    assert _RECORD_PATH.exists(), "Record fixture not built"
    result = _run_cli(
        "identity", "consent", "validate",
        "--record", str(_RECORD_PATH),
        "--delta-report", str(_DELTA_REPORT_PATH),
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_consent_cli_validate_rejects_attestation_mismatch():
    mismatch_report = {
        "report_id": "adr_mismatch",
        "source_kind": "operator_contract",
        "deltas": [
            {
                "delta_id": "adt_cli_1",
                "delta_type": "RISK_CEILING_INCREASED",
                "severity": "HIGH",
                "source_kind": "operator_contract",
                "field_path": "risk_ceiling",
                "old_value": "low",
                "new_value": "high",
                "old_attestation_id": "srcatt_DIFFERENT",
                "new_attestation_id": "srcatt_DIFFERENT2",
                "requires_operator_consent": True,
                "requires_evidence": False,
                "reason": "mismatch",
                "blockers": [],
                "warnings": [],
            }
        ],
        "highest_severity": "HIGH",
        "requires_operator_consent": True,
        "requires_evidence": False,
        "summary": "Mismatch delta report",
        "safe_to_auto_accept": False,
        "old_attestation_id": "srcatt_DIFFERENT",
        "new_attestation_id": "srcatt_DIFFERENT2",
    }
    mismatch_path = FIXTURES / "delta_report_mismatch.json"
    mismatch_path.write_text(json.dumps(mismatch_report, indent=2))

    assert _RECORD_PATH.exists()
    result = _run_cli(
        "identity", "consent", "validate",
        "--record", str(_RECORD_PATH),
        "--delta-report", str(mismatch_path),
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["valid"] is False
    assert "old_attestation_mismatch" in data["blockers"]


def test_consent_cli_revoke_outputs_revoked_record():
    assert _RECORD_PATH.exists()
    result = _run_cli(
        "identity", "consent", "revoke",
        "--record", str(_RECORD_PATH),
        "--operator-id", "operator.cli.revoke",
        "--reason", "source changed",
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "REVOKED"
    # Save for show test
    _REVOKED_PATH.write_text(json.dumps(data, indent=2))


def test_consent_cli_show_outputs_record():
    assert _REVOKED_PATH.exists()
    result = _run_cli(
        "identity", "consent", "show",
        "--record", str(_REVOKED_PATH),
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "REVOKED"
    assert data["consent_id"] is not None


def test_consent_cli_help():
    result = _run_cli("identity", "consent", "--help")
    assert result.returncode == 0


def test_consent_cli_subcommand_help():
    for subcmd in ("request", "grant", "deny", "revoke", "show", "validate"):
        result = _run_cli("identity", "consent", subcmd, "--help")
        assert result.returncode == 0, f"{subcmd} --help failed: {result.stderr}"
