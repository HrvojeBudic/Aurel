"""P1.6.18 — Policy CLI projection output tests."""
from __future__ import annotations

import json
import re

from tests.cli_helpers import run_cli

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|credential|private[_-]?key|authorization)",
    re.IGNORECASE,
)


def _walk_keys(obj: object, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.append(path)
            keys.extend(_walk_keys(value, path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            keys.extend(_walk_keys(item, f"{prefix}[{idx}]"))
    return keys


class TestPolicyStatusTextOutput:
    def test_status_contains_section_names(self):
        proc = run_cli("policy", "status")
        assert proc.returncode == 0
        for section_id in (
            "policy_registry",
            "policy_resolver",
            "conflict_algebra",
            "resolution_trace",
            "violation_trace",
            "policy_harness",
            "cli_binding",
            "shell_binding",
        ):
            assert section_id in proc.stdout

    def test_status_contains_source_labels(self):
        proc = run_cli("policy", "status")
        assert "LIVE" in proc.stdout
        assert "UNAVAILABLE" in proc.stdout

    def test_status_contains_readiness_flags(self):
        proc = run_cli("policy", "status")
        assert "Readiness:" in proc.stdout
        assert "cli_binding_available: true" in proc.stdout
        assert "shell_binding_available: false" in proc.stdout


class TestPolicyProjectionJsonOutput:
    def test_projection_json_is_valid(self):
        proc = run_cli("policy", "projection", "--json")
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert isinstance(payload, dict)

    def test_json_contains_contract_version(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert payload["contract_version"] == "policy_projection.v1"

    def test_json_contains_projection_hash(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert len(payload["projection_hash"]) == 64

    def test_json_contains_sections(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert "cli_binding" in payload["sections"]
        assert "shell_binding" in payload["sections"]

    def test_json_contains_readiness(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert payload["readiness"]["cli_binding_available"] is True
        assert payload["readiness"]["shell_binding_available"] is False

    def test_json_is_deterministic_across_runs(self):
        proc1 = run_cli("policy", "projection", "--json")
        proc2 = run_cli("policy", "projection", "--json")
        assert json.loads(proc1.stdout) == json.loads(proc2.stdout)

    def test_json_has_no_decorative_text(self):
        proc = run_cli("policy", "projection", "--json")
        stdout = proc.stdout.strip()
        assert stdout.startswith("{")
        assert stdout.endswith("}")
        json.loads(stdout)

    def test_json_does_not_contain_secret_like_keys(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        for key_path in _walk_keys(payload):
            assert not _SENSITIVE_KEY_PATTERN.search(key_path)


class TestPolicyUnavailableOutput:
    def test_unavailable_lists_shell_binding(self):
        proc = run_cli("policy", "unavailable")
        assert proc.returncode == 0
        assert "shell_binding" in proc.stdout
        assert "UNAVAILABLE" in proc.stdout

    def test_cli_does_not_invent_live_for_unavailable_sections(self):
        proc = run_cli("policy", "unavailable")
        assert "shell_binding" in proc.stdout
        assert "Shell binding not implemented in P1.6" in proc.stdout

    def test_cli_binding_is_live_not_unavailable(self):
        proc = run_cli("policy", "projection", "--json")
        payload = json.loads(proc.stdout)
        assert payload["sections"]["cli_binding"]["source"] == "LIVE"
        assert payload["sections"]["shell_binding"]["source"] == "UNAVAILABLE"
