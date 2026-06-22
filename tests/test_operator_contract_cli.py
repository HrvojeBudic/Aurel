"""P1.4.3 — Operator Relationship Contract CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": f"src{os.pathsep}."},
        capture_output=True,
        text=True,
    )


# 47
def test_cli_validate_succeeds():
    proc = _cli("identity", "operator-contract", "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "valid" in proc.stdout.lower()


# 48
def test_cli_show_json_includes_contract_hash():
    proc = _cli("identity", "operator-contract", "show", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["contract_name"] == "Aurel Operator Relationship Contract"
    assert payload["contract_class"] == "principal_delegate_relationship"
    assert payload["principal_role"] == "final_authority"
    assert payload["delegate_role"] == "advisor_executor_under_authority"
    assert payload["operator_final_authority"] is True
    assert payload["aurel_final_authority"] is False
    assert payload["aurel_can_self_escalate"] is False
    assert payload["aurel_can_refuse_forbidden_action"] is True
    assert payload["aurel_must_challenge_when_risk_detected"] is True
    assert payload["manipulation_forbidden"] is True
    assert len(payload["contract_hash"]) == 64


# 49
def test_cli_hash_returns_sha256_value():
    proc = _cli("identity", "operator-contract", "hash")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    value = proc.stdout.strip()
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)


# 50, 52, 53
def test_cli_summary_json_returns_safe_summary():
    proc = _cli("identity", "operator-contract", "summary", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["contract_name"] == "Aurel Operator Relationship Contract"
    assert payload["non_manipulation_rules"]
    assert payload["challenge_rules"]
    assert payload["execution_authority_boundaries"]


# 54
def test_cli_summary_does_not_expose_raw_yaml():
    proc = _cli("identity", "operator-contract", "summary", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "operator_contract:" not in proc.stdout
    assert "expected_value" not in proc.stdout
    assert "violation_action" not in proc.stdout


def test_cli_attest_json():
    proc = _cli("identity", "operator-contract", "attest", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["contract_hash"]) == 64
