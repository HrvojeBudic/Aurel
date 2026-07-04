"""Subprocess tests for read-only AurelExec CLI commands."""

from __future__ import annotations

import json

from tests.cli_helpers import run_cli


def test_exec_status_exits_zero_and_is_read_only_json() -> None:
    proc = run_cli("exec", "status")

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["read_only"] is True
    assert payload["shell_ui_available"] is False
    assert "categories" in payload
    assert "admission_state" in payload["categories"]
    assert "runtime_submit_state" in payload["categories"]
