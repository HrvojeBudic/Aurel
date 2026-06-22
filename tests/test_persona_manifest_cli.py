"""P1.4.2 — Persona Manifest CLI tests."""

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


# 26
def test_cli_validate_succeeds():
    proc = _cli("identity", "persona", "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "valid" in proc.stdout.lower()


# 27
def test_cli_show_json_includes_persona_hash():
    proc = _cli("identity", "persona", "show", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["manifest_name"] == "Aurel Default Persona"
    assert payload["applies_to_agent"] == "Aurel"
    assert payload["manifest_class"] == "expression_contract"
    assert payload["authority_level"] == "none"
    assert payload["can_grant_permissions"] is False
    assert payload["can_override_identity_kernel"] is False
    assert payload["can_override_policy"] is False
    assert payload["can_change_autonomy"] is False
    assert payload["never_claim_unverified_capability"] is True
    assert len(payload["persona_hash"]) == 64


# 28
def test_cli_hash_returns_sha256_value():
    proc = _cli("identity", "persona", "hash")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    value = proc.stdout.strip()
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)


# 29, 30, 31
def test_cli_summary_json_returns_safe_summary():
    proc = _cli("identity", "persona", "summary", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["manifest_name"] == "Aurel Default Persona"
    assert payload["authority_boundaries"]
    assert payload["capability_honesty_rules"]


# 32
def test_cli_summary_does_not_expose_raw_yaml():
    proc = _cli("identity", "persona", "summary", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "persona_manifest:" not in proc.stdout
    assert "expected_value" not in proc.stdout
    assert "violation_action" not in proc.stdout


def test_cli_attest_json():
    proc = _cli("identity", "persona", "attest", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["persona_hash"]) == 64
