"""P1.4.5 — Identity Prompt Context CLI tests (cases #54-59)."""

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


def test_cli_compile_deploy_json_succeeds():
    proc = _cli("identity", "context", "compile", "--mode", "DEPLOY", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["valid"] is True
    assert payload["selected_mode"] == "DEPLOY"
    assert payload["agent_name"] == "Aurel"
    assert len(payload["context_hash"]) == 64
    assert "active_mode" in payload["sections"]


def test_cli_compile_heretic_json_succeeds():
    proc = _cli("identity", "context", "compile", "--mode", "HERETIC", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["valid"] is True
    assert payload["selected_mode"] == "HERETIC"
    active = "\n".join(payload["sections"]["active_mode"]).lower()
    assert "candidate-only" in active or "candidate only" in active


def test_cli_render_deploy_succeeds():
    proc = _cli("identity", "context", "render", "--mode", "DEPLOY")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "## agent_identity" in proc.stdout
    assert "## source_integrity" in proc.stdout


def test_cli_hash_shadow_returns_sha256_value():
    proc = _cli("identity", "context", "hash", "--mode", "SHADOW")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    value = proc.stdout.strip()
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)


def test_cli_compile_unknown_mode_fails_safely():
    proc = _cli("identity", "context", "compile", "--mode", "UNKNOWN", "--json")
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["valid"] is False


def test_cli_attest_includes_source_hashes_and_context_hash():
    proc = _cli("identity", "context", "attest", "--mode", "FOCUS", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["context_hash"]) == 64
    assert len(payload["identity_kernel_hash"]) == 64
    assert len(payload["persona_manifest_hash"]) == 64
    assert len(payload["operator_contract_hash"]) == 64
    assert len(payload["communication_modes_hash"]) == 64
    assert len(payload["compiler_policy_hash"]) == 64
