"""P1.4.12 source attestation CLI tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli"] + args,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=20,
    )


def test_attestation_cli_help():
    result = _run_cli(["identity", "attestation", "--help"])
    assert result.returncode == 0
    assert "list" in result.stdout
    assert "show" in result.stdout
    assert "validate" in result.stdout
    assert "verify-bundle" in result.stdout


def test_attestation_cli_list_outputs_json():
    result = _run_cli(["identity", "attestation", "list", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data) == 10
    keys = {item["record_key"] for item in data}
    assert "operator_contract" in keys
    assert "external_doctrine:agentic_os_asymmetric_teardown" in keys


def test_attestation_cli_show_outputs_source_attestation():
    result = _run_cli(["identity", "attestation", "show", "operator_contract", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["source_kind"] == "operator_contract"
    assert data["raw_source_hash"]
    assert data["canonical_typed_hash"]
    assert data["validation_status"] == "VALID"


def test_attestation_cli_validate_outputs_status():
    result = _run_cli(["identity", "attestation", "validate", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data == {"valid": True, "attestations": 10, "errors": []}


def test_attestation_cli_verify_bundle_reports_complete_attestations():
    result = _run_cli(["identity", "attestation", "verify-bundle", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True
    assert data["missing_attestations"] == []
    assert len(data["present_attestations"]) == 7


def test_attestation_cli_compare_outputs_hash_pair():
    result = _run_cli([
        "identity",
        "attestation",
        "compare",
        "--raw-path",
        "config/aurel/operator_contract.yaml",
        "--canonical-kind",
        "operator_contract",
        "--json",
    ])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["canonical_kind"] == "operator_contract"
    assert data["raw_matches_attestation"] is True
    assert data["raw_source_hash"] == data["attested_raw_source_hash"]
