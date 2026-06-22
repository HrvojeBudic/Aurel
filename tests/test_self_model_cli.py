"""P1.4.6 — Self-Model CLI tests (cases #55-60)."""

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


def test_cli_self_show_json_succeeds():
    proc = _cli("identity", "self", "show", "--json", "--prompt-mode", "FOCUS")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["agent_name"] == "Aurel"
    assert payload["agent_class"] == "sovereign_personal_agent"
    assert len(payload["self_model_hash"]) == 64
    assert payload["active_prompt_context_available"] is True
    assert any(c["id"] == "evaluation_mirror" for c in payload["capabilities"])


def test_cli_self_capabilities_json_succeeds():
    proc = _cli("identity", "self", "capabilities", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert "capabilities" in payload
    assert any(c["status"] == "planned" for c in payload["capabilities"])


def test_cli_self_limitations_json_succeeds():
    proc = _cli("identity", "self", "limitations", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert len(payload["known_limitations"]) >= 10
    assert any("Evaluation Mirror" in item["description"] for item in payload["known_limitations"])


def test_cli_self_hash_returns_sha256_value():
    proc = _cli("identity", "self", "hash")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    value = proc.stdout.strip()
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)


def test_cli_self_validate_succeeds():
    proc = _cli("identity", "self", "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "valid" in proc.stdout.lower()


def test_cli_self_attest_includes_source_hashes_and_self_model_hash():
    proc = _cli("identity", "self", "attest", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["self_model_hash"]) == 64
    assert len(payload["identity_kernel_hash"]) == 64
    assert len(payload["persona_manifest_hash"]) == 64
    assert len(payload["operator_contract_hash"]) == 64
    assert len(payload["communication_modes_hash"]) == 64
    assert len(payload["identity_prompt_compiler_policy_hash"]) == 64
