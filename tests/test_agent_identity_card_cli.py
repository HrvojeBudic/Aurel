"""P1.4.7 — Agent Identity Card CLI tests (cases #55-60)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_RUNTIME_ID = "aurel-runtime-00000000-0000-4000-8000-000000000001"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "agentic_runtime.cli",
        "identity",
        "card",
        *args,
        "--runtime-instance-id",
        FIXED_RUNTIME_ID,
    ]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**dict(**{"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"})},
        check=False,
    )


# 55
def test_cli_show_json():
    result = _run("show", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["agent_name"] == "Aurel"
    assert payload["runtime_instance_id"] == FIXED_RUNTIME_ID
    assert len(payload["stable_agent_identity_hash"]) == 64


# 56
def test_cli_validate_json():
    result = _run("validate", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["config_valid"] is True
    assert payload["card_valid"] is True


# 57
def test_cli_hash_json():
    result = _run("hash", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert len(payload["stable_agent_identity_hash"]) == 64
    assert len(payload["runtime_agent_identity_card_hash"]) == 64


# 58 covered in taxonomy tests


# 59
def test_cli_attest_json():
    result = _run("attest", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["stable_agent_identity_hash"]) == 64
    assert payload["runtime_instance_id"] == FIXED_RUNTIME_ID


# 60
def test_cli_taxonomy_json():
    result = _run("taxonomy", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    taxonomy = payload["identity_taxonomy"]
    assert taxonomy["agent_identity"] != taxonomy["human_principal_identity"]
    assert payload["agent_identity_equals_human"] is False
    assert len(payload["taxonomy_notes"]) == 3
