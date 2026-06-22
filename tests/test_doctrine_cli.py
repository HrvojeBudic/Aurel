"""P1.4.11 doctrine CLI tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli"] + args,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=15,
    )


def test_doctrine_cli_help():
    result = _run_cli(["identity", "doctrine", "--help"])
    assert result.returncode == 0
    assert "list" in result.stdout
    assert "show" in result.stdout
    assert "validate" in result.stdout
    assert "impact" in result.stdout
    assert "claims" in result.stdout


def test_doctrine_cli_list_outputs_json():
    result = _run_cli(["identity", "doctrine", "list", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data) == 3
    assert {item["doctrine_id"] for item in data} == {
        "agentic_os_asymmetric_teardown",
        "abos_design_principles_v1",
        "aether_v0_2",
    }


def test_doctrine_cli_show_outputs_seeded_doctrine():
    result = _run_cli([
        "identity",
        "doctrine",
        "show",
        "agentic_os_asymmetric_teardown",
        "--json",
    ])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["doctrine"]["doctrine_id"] == "agentic_os_asymmetric_teardown"
    assert data["doctrine"]["source_hash"]
    assert data["decision"]["accepted"] is True


def test_doctrine_cli_validate_passes_seed_registry():
    result = _run_cli(["identity", "doctrine", "validate", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data == {"valid": True, "doctrines": 3, "errors": []}


def test_doctrine_cli_impact_outputs_roadmap_mapping():
    result = _run_cli([
        "identity",
        "doctrine",
        "impact",
        "agentic_os_asymmetric_teardown",
        "--json",
    ])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    modules = {item["roadmap_module"] for item in data}
    assert "P20 Sovereign Agentic OS Seal" in modules
    assert all(item["implementation_status"] == "not_implemented_by_doctrine" for item in data)


def test_doctrine_cli_claims_outputs_boundaries():
    result = _run_cli([
        "identity",
        "doctrine",
        "claims",
        "aether_v0_2",
        "--json",
    ])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["doctrine_id"] == "aether_v0_2"
    assert any("multimodal intelligence extraction" in b for b in data["blocked_claims"])
    assert data["p1410_decisions"]
