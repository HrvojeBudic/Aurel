"""P1.4.4 — Communication Modes CLI tests."""

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


# 48
def test_cli_validate_succeeds():
    proc = _cli("identity", "modes", "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "valid" in proc.stdout.lower()


# 49
def test_cli_list_json_includes_all_required_modes():
    proc = _cli("identity", "modes", "list", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["registry_name"] == "Aurel Communication Modes"
    assert payload["modes"] == [
        "CHANNEL",
        "DEBUG",
        "DEPLOY",
        "EVOLVE",
        "FOCUS",
        "HERETIC",
        "SHADOW",
    ]
    assert payload["modes_can_grant_permissions"] is False
    assert payload["modes_can_change_autonomy"] is False
    assert payload["modes_can_execute_actions"] is False
    assert len(payload["registry_hash"]) == 64


# 50
def test_cli_show_json_includes_registry_hash():
    proc = _cli("identity", "modes", "show", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["registry_name"] == "Aurel Communication Modes"
    assert len(payload["registry_hash"]) == 64


# 51
def test_cli_hash_returns_sha256_value():
    proc = _cli("identity", "modes", "hash")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    value = proc.stdout.strip()
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)


# 52, 53
def test_cli_summary_heretic_json_includes_candidate_only_and_no_side_effects():
    proc = _cli("identity", "modes", "summary", "HERETIC", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["mode_name"] == "HERETIC"
    assert payload["candidate_only"] is True
    assert payload["real_world_side_effects"] is False
    assert payload["grants_permissions"] is False
    assert payload["changes_autonomy"] is False
    assert payload["executes_actions"] is False
    assert payload["modifies_identity"] is False
    assert payload["modifies_policy"] is False
    assert payload["modifies_memory"] is False
    assert "Attack assumptions" in payload["purpose"]


def test_cli_attest_json():
    proc = _cli("identity", "modes", "attest", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["registry_hash"]) == 64
