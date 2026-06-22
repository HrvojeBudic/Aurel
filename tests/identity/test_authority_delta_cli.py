"""CLI tests for P1.4.13 Authority Delta Detector."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "authority_delta"
OLD_OP = str(FIXTURES / "operator_contract_low_risk.yaml")
NEW_OP = str(FIXTURES / "operator_contract_high_risk.yaml")


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_authority_delta_cli_compare_outputs_json():
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", OLD_OP,
        "--new", NEW_OP,
        "--source-kind", "operator_contract",
        "--json",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "deltas" in data
    assert "highest_severity" in data
    assert "requires_operator_consent" in data


def test_authority_delta_cli_compare_detects_risk_increase():
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", OLD_OP,
        "--new", NEW_OP,
        "--source-kind", "operator_contract",
        "--json",
    )
    data = json.loads(result.stdout)
    delta_types = [d["delta_type"] for d in data["deltas"]]
    assert "RISK_CEILING_INCREASED" in delta_types


def test_authority_delta_cli_compare_detects_oversight_weakened():
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", OLD_OP,
        "--new", NEW_OP,
        "--source-kind", "operator_contract",
        "--json",
    )
    data = json.loads(result.stdout)
    delta_types = [d["delta_type"] for d in data["deltas"]]
    assert "OVERSIGHT_WEAKENED" in delta_types


def test_authority_delta_cli_human_output_mentions_consent_required():
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", OLD_OP,
        "--new", NEW_OP,
        "--source-kind", "operator_contract",
    )
    assert result.returncode == 0
    assert "OPERATOR CONSENT" in result.stdout


def test_authority_delta_cli_help():
    result = _run_cli("identity", "authority-delta", "--help")
    assert result.returncode == 0


def test_authority_delta_cli_compare_help():
    result = _run_cli("identity", "authority-delta", "compare", "--help")
    assert result.returncode == 0


def test_authority_delta_cli_safe_to_auto_accept_false():
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", OLD_OP,
        "--new", NEW_OP,
        "--source-kind", "operator_contract",
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["safe_to_auto_accept"] is False


def test_authority_delta_cli_requires_evidence():
    old = str(FIXTURES / "doctrine_reference.yaml")
    new = str(FIXTURES / "doctrine_implemented.yaml")
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", old,
        "--new", new,
        "--source-kind", "external_doctrine",
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["requires_evidence"] is True


def test_authority_delta_cli_no_change_safe():
    result = _run_cli(
        "identity", "authority-delta", "compare",
        "--old", OLD_OP,
        "--new", OLD_OP,
        "--source-kind", "operator_contract",
        "--json",
    )
    data = json.loads(result.stdout)
    assert data["safe_to_auto_accept"] is True
    assert data["requires_operator_consent"] is False
    assert data["highest_severity"] == "INFO"
