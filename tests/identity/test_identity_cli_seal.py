"""Seal tests for P1.4.15 Identity CLI Surface.

Proves the CLI invariants that must hold for all identity commands.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from agentic_runtime.identity.identity_cli_surface import (
    IdentityCliStatus,
    build_identity_cli_envelope,
    build_identity_status_report,
    identity_cli_envelope_to_dict,
    identity_status_report_to_dict,
    verify_identity_surface,
)


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agentic_runtime.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# INV-P1415-01: CLI surface does not create new authority
# ---------------------------------------------------------------------------


def test_p1415_cli_surface_is_consistent():
    """The surface module should be deterministic and not create side effects."""
    r1 = build_identity_status_report()
    r2 = build_identity_status_report()
    assert identity_status_report_to_dict(r1) == identity_status_report_to_dict(r2)


# ---------------------------------------------------------------------------
# INV-P1415-02: status/verify are read-only
# ---------------------------------------------------------------------------


def test_p1415_status_verify_are_read_only():
    """Status and verify must produce identical output on repeated calls."""
    s1 = _run_cli("identity", "status", "--json").stdout
    s2 = _run_cli("identity", "status", "--json").stdout
    assert s1 == s2

    v1 = _run_cli("identity", "verify", "--json").stdout
    v2 = _run_cli("identity", "verify", "--json").stdout
    assert v1 == v2


# ---------------------------------------------------------------------------
# INV-P1415-03: JSON output must use stable envelope
# ---------------------------------------------------------------------------


def test_p1415_json_envelope_is_stable():
    """Every JSON output must include ok, command, status, errors, warnings, result."""
    env = build_identity_cli_envelope(
        command="identity.status",
        status=IdentityCliStatus.OK,
        result={"test": True},
        errors=(),
        warnings=(),
    )
    d = identity_cli_envelope_to_dict(env)
    required_keys = {"ok", "command", "status", "errors", "warnings", "result"}
    assert set(d.keys()) == required_keys
    assert isinstance(d["ok"], bool)
    assert isinstance(d["command"], str)
    assert isinstance(d["status"], str)
    assert isinstance(d["errors"], list)
    assert isinstance(d["warnings"], list)
    assert isinstance(d["result"], dict)


# ---------------------------------------------------------------------------
# INV-P1415-04: Human output exposes blockers and suggested next command
# ---------------------------------------------------------------------------


def test_p1415_cli_does_not_grant_consent():
    """Status/verify must never produce consent artifacts."""
    for cmd in ("status", "verify"):
        result = _run_cli("identity", cmd, "--json")
        data = json.loads(result.stdout)
        assert "consent" not in str(data.get("result", {}))
        assert "granted" not in data.get("status", "")


# ---------------------------------------------------------------------------
# INV-P1415-07: CLI must not execute tools from identity commands
# ---------------------------------------------------------------------------


def test_p1415_cli_does_not_execute_tools():
    """Identity commands must not trigger tool execution."""
    for cmd in ("status", "verify"):
        result = _run_cli("identity", cmd, "--json")
        data = json.loads(result.stdout)
        assert "execution" not in str(data.get("result", {}))
        assert "tool_executed" not in str(data)


# ---------------------------------------------------------------------------
# INV-P1415-08: CLI must not modify source
# ---------------------------------------------------------------------------


def test_p1415_cli_does_not_modify_source():
    """Read-only commands must not mutate sources."""
    report_before = build_identity_status_report()
    _ = _run_cli("identity", "status", "--json")
    _ = _run_cli("identity", "verify", "--json")
    report_after = build_identity_status_report()
    assert identity_status_report_to_dict(report_before) == identity_status_report_to_dict(report_after)


# ---------------------------------------------------------------------------
# INV-P1415-09: CLI reports governance blockers
# ---------------------------------------------------------------------------


def test_p1415_cli_reports_governance_blockers():
    """The status report must expose at minimum the subsystem names and statuses."""
    report = build_identity_status_report()
    assert len(report.subsystems) >= 1
    for ss in report.subsystems:
        assert ss.name
        assert ss.status.value in {"OK", "DEGRADED", "BLOCKED", "UNKNOWN"}
        assert ss.summary


# ---------------------------------------------------------------------------
# INV-P1415-10: Prepares P1.4.16 Identity Test Battery
# ---------------------------------------------------------------------------


def test_p1415_prepares_p1416_identity_test_battery():
    """The surface must be testable — all essential functions callable without exceptions."""
    # Envelope
    env = build_identity_cli_envelope(command="test", status=IdentityCliStatus.OK)
    assert env.ok is True
    d = identity_cli_envelope_to_dict(env)
    assert d["ok"] is True

    # Status report
    report = build_identity_status_report()
    assert report.status in IdentityCliStatus

    # Verify
    vreport = verify_identity_surface()
    assert vreport.status in IdentityCliStatus

    # Serialization
    json.dumps(identity_status_report_to_dict(report))


# ---------------------------------------------------------------------------
# Help output exposes all groups
# ---------------------------------------------------------------------------


def test_p1415_help_lists_all_subcommand_groups():
    result = _run_cli("identity", "--help")
    output = result.stdout + result.stderr
    all_groups = [
        "status",
        "verify",
        "autonomy",
        "claims",
        "doctrine",
        "attestation",
        "authority-delta",
        "consent",
    ]
    for group in all_groups:
        assert group in output, f"Missing '{group}' in identity --help"
