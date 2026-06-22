"""P1.4.1 — Identity Kernel CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from agentic_runtime.identity.kernel_validation import (
    build_identity_kernel_attestation,
    validate_identity_kernel,
)
from agentic_runtime.identity.kernel import load_identity_kernel

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KERNEL = REPO_ROOT / "config" / "aurel" / "identity_kernel.yaml"


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": f"src{os.pathsep}."},
        capture_output=True,
        text=True,
    )


def test_cli_validate_returns_success_for_valid_kernel():
    proc = _cli("identity", "kernel", "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "valid" in proc.stdout.lower()


def test_cli_show_json_includes_kernel_hash():
    proc = _cli("identity", "kernel", "show", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["name"] == "Aurel"
    assert payload["class"] == "sovereign_personal_agent"
    assert payload["primary_operator"] == "single_human_operator"
    assert payload["final_authority"] == "operator"
    assert payload["local_first"] is True
    assert payload["operator_final_authority"] is True
    assert payload["self_escalation_allowed"] is False
    assert payload["hidden_goals_allowed"] is False
    assert payload["identity_replacement_allowed"] is False
    assert len(payload["kernel_hash"]) == 64


def test_cli_hash_returns_sha256_value():
    proc = _cli("identity", "kernel", "hash")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    value = proc.stdout.strip()
    assert len(value) == 64
    assert all(ch in "0123456789abcdef" for ch in value)


def test_attestation_object_includes_validation_status_and_kernel_hash():
    kernel = load_identity_kernel(CANONICAL_KERNEL)
    attestation = build_identity_kernel_attestation(kernel, CANONICAL_KERNEL)
    assert attestation.validation_status == "valid"
    assert len(attestation.kernel_hash) == 64
    assert validate_identity_kernel(kernel).valid is True


def test_cli_attest_json():
    proc = _cli("identity", "kernel", "attest", "--json")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["validation_status"] == "valid"
    assert len(payload["kernel_hash"]) == 64
