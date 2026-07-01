"""CLI tests for P1.4.14 Operator Consent Binding."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

CANONICAL_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "consent"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def build_consent_cli_workspace(workspace: Path) -> dict[str, Path]:
    """Build mutable consent CLI artifacts under workspace (not tracked fixtures)."""
    paths: dict[str, Path] = {
        "delta_report": workspace / "delta_report.json",
        "request": workspace / "consent_request.json",
        "record": workspace / "consent_record.json",
        "denied": workspace / "consent_denied.json",
        "revoked": workspace / "consent_revoked.json",
        "delta_report_mismatch": workspace / "delta_report_mismatch.json",
    }

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
    paths["delta_report"].write_text(json.dumps(delta_report, indent=2))

    result = _run_cli(
        "identity", "consent", "request",
        "--delta-report", str(paths["delta_report"]),
        "--json",
    )
    if result.returncode == 0:
        paths["request"].write_text(result.stdout)

    if paths["request"].exists():
        grant = _run_cli(
            "identity", "consent", "grant",
            "--request", str(paths["request"]),
            "--operator-id", "operator.cli.test",
            "--ack-risk",
            "--json",
        )
        if grant.returncode == 0:
            paths["record"].write_text(grant.stdout)

    return paths


@pytest.fixture(scope="module")
def consent_cli_workspace(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Generate mutable consent CLI artifacts under tmp_path, not tracked fixtures."""
    return build_consent_cli_workspace(tmp_path_factory.mktemp("consent_cli"))


def test_consent_cli_request_outputs_json(consent_cli_workspace: dict[str, Path]):
    result = _run_cli(
        "identity", "consent", "request",
        "--delta-report", str(consent_cli_workspace["delta_report"]),
        "--json",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "request_id" in data
    assert "delta_ids" in data
    assert data["highest_severity"] == "HIGH"
    assert data["requires_explicit_risk_acknowledgement"] is True


def test_consent_cli_grant_outputs_record(consent_cli_workspace: dict[str, Path]):
    result = _run_cli(
        "identity", "consent", "grant",
        "--request", str(consent_cli_workspace["request"]),
        "--operator-id", "operator.cli.grant",
        "--ack-risk",
        "--json",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["status"] == "GRANTED"
    assert data["risk_acknowledged"] is True


def test_consent_cli_grant_requires_ack_risk_for_high_delta(consent_cli_workspace: dict[str, Path]):
    result = _run_cli(
        "identity", "consent", "grant",
        "--request", str(consent_cli_workspace["request"]),
        "--operator-id", "operator.cli.noack",
        "--json",
    )
    assert result.returncode == 1, "Should fail without --ack-risk for HIGH severity"
    data = json.loads(result.stdout)
    assert "risk_acknowledgement_required" in data.get("blockers", [])


def test_consent_cli_deny_outputs_denied_record(consent_cli_workspace: dict[str, Path]):
    result = _run_cli(
        "identity", "consent", "deny",
        "--request", str(consent_cli_workspace["request"]),
        "--operator-id", "operator.cli.deny",
        "--reason", "too broad scope",
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "DENIED"


def test_consent_cli_validate_accepts_valid_record(consent_cli_workspace: dict[str, Path]):
    assert consent_cli_workspace["record"].exists(), "Record fixture not built"
    result = _run_cli(
        "identity", "consent", "validate",
        "--record", str(consent_cli_workspace["record"]),
        "--delta-report", str(consent_cli_workspace["delta_report"]),
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_consent_cli_validate_rejects_attestation_mismatch(consent_cli_workspace: dict[str, Path]):
    mismatch_report: dict[str, Any] = {
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
    mismatch_path = consent_cli_workspace["delta_report_mismatch"]
    mismatch_path.write_text(json.dumps(mismatch_report, indent=2))

    assert consent_cli_workspace["record"].exists()
    result = _run_cli(
        "identity", "consent", "validate",
        "--record", str(consent_cli_workspace["record"]),
        "--delta-report", str(mismatch_path),
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["valid"] is False
    assert "old_attestation_mismatch" in data["blockers"]


def test_consent_cli_revoke_outputs_revoked_record(consent_cli_workspace: dict[str, Path]):
    assert consent_cli_workspace["record"].exists()
    result = _run_cli(
        "identity", "consent", "revoke",
        "--record", str(consent_cli_workspace["record"]),
        "--operator-id", "operator.cli.revoke",
        "--reason", "source changed",
        "--json",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "REVOKED"
    consent_cli_workspace["revoked"].write_text(json.dumps(data, indent=2))


def test_consent_cli_show_outputs_record(consent_cli_workspace: dict[str, Path]):
    assert consent_cli_workspace["revoked"].exists()
    result = _run_cli(
        "identity", "consent", "show",
        "--record", str(consent_cli_workspace["revoked"]),
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
