"""Core tests for P1.4.15 Identity CLI Surface."""
from __future__ import annotations

import json

import pytest

from agentic_runtime.identity.identity_cli_surface import (
    ALL_SUBSYSTEMS,
    IdentityCliEnvelope,
    IdentityCliStatus,
    IdentityStatusReport,
    IdentitySubsystemStatus,
    build_identity_cli_envelope,
    build_identity_status_report,
    format_envelope_human,
    format_identity_status_human,
    identity_cli_envelope_to_dict,
    identity_status_report_to_dict,
    identity_substatus_to_dict,
    verify_identity_surface,
)


# ---------------------------------------------------------------------------
# Envelope tests
# ---------------------------------------------------------------------------


def test_cli_json_output_has_ok_command_status_errors_warnings_result():
    env = build_identity_cli_envelope(
        command="identity.status",
        status=IdentityCliStatus.OK,
        result={"subsystem_count": 6},
    )
    d = identity_cli_envelope_to_dict(env)
    assert "ok" in d
    assert "command" in d
    assert "status" in d
    assert "errors" in d
    assert "warnings" in d
    assert "result" in d


def test_cli_errors_use_standard_envelope():
    env = build_identity_cli_envelope(
        command="identity.verify",
        status=IdentityCliStatus.BLOCKED,
        errors=("missing_attestation",),
    )
    d = identity_cli_envelope_to_dict(env)
    assert d["ok"] is False
    assert d["status"] == "BLOCKED"
    assert "missing_attestation" in d["errors"]


def test_cli_envelope_ok_false_when_errors_present():
    env = build_identity_cli_envelope(
        command="test",
        status=IdentityCliStatus.OK,
        errors=("some_error",),
    )
    assert env.ok is False


def test_cli_envelope_ok_false_when_status_blocked():
    env = build_identity_cli_envelope(
        command="test",
        status=IdentityCliStatus.BLOCKED,
    )
    assert env.ok is False


def test_cli_envelope_ok_false_when_status_degraded():
    env = build_identity_cli_envelope(
        command="test",
        status=IdentityCliStatus.DEGRADED,
    )
    assert env.ok is False


def test_cli_envelope_ok_true_when_ok_and_no_errors():
    env = build_identity_cli_envelope(
        command="test",
        status=IdentityCliStatus.OK,
        errors=(),
    )
    assert env.ok is True


def test_cli_envelope_serializes_enums_as_strings():
    env = build_identity_cli_envelope(
        command="test",
        status=IdentityCliStatus.DEGRADED,
        result={"key": "value"},
        warnings=("warn1",),
    )
    d = identity_cli_envelope_to_dict(env)
    assert isinstance(d["status"], str)
    assert d["status"] == "DEGRADED"
    assert isinstance(d["errors"], list)
    assert isinstance(d["warnings"], list)


def test_identity_cli_envelope_deterministic():
    env1 = build_identity_cli_envelope(command="test", status=IdentityCliStatus.OK)
    env2 = build_identity_cli_envelope(command="test", status=IdentityCliStatus.OK)
    assert identity_cli_envelope_to_dict(env1) == identity_cli_envelope_to_dict(env2)


# ---------------------------------------------------------------------------
# Subsystem status tests
# ---------------------------------------------------------------------------


def test_identity_substatus_to_dict():
    ss = IdentitySubsystemStatus(
        name="test_sub",
        status=IdentityCliStatus.OK,
        summary="all good",
        errors=("e1",),
        warnings=("w1",),
    )
    d = identity_substatus_to_dict(ss)
    assert d["name"] == "test_sub"
    assert d["status"] == "OK"
    assert "e1" in d["errors"]
    assert "w1" in d["warnings"]


# ---------------------------------------------------------------------------
# Status report tests
# ---------------------------------------------------------------------------


def test_identity_status_reports_subsystems():
    report = build_identity_status_report()
    assert len(report.subsystems) == len(ALL_SUBSYSTEMS)
    names = {s.name for s in report.subsystems}
    for expected in ALL_SUBSYSTEMS:
        assert expected in names, f"Missing subsystem: {expected}"


def test_identity_status_is_read_only():
    """Calling status multiple times should not change behavior."""
    r1 = build_identity_status_report()
    r2 = build_identity_status_report()
    assert identity_status_report_to_dict(r1) == identity_status_report_to_dict(r2)


def test_identity_status_suggests_next_command_when_not_ok():
    report = build_identity_status_report()
    if report.status != IdentityCliStatus.OK:
        assert len(report.suggested_next_commands) > 0


def test_identity_status_report_serializable():
    report = build_identity_status_report()
    d = identity_status_report_to_dict(report)
    assert "status" in d
    assert "subsystems" in d
    assert "errors" in d
    assert isinstance(d["subsystems"], list)
    # Verify JSON round-trip
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["status"] == report.status.value


def test_identity_status_subsystems_have_non_empty_names():
    report = build_identity_status_report()
    for ss in report.subsystems:
        assert ss.name, f"Subsystem has empty name: {ss}"
        assert ss.summary, f"Subsystem {ss.name} has empty summary"


# ---------------------------------------------------------------------------
# Verify tests
# ---------------------------------------------------------------------------


def test_identity_verify_is_read_only():
    r1 = verify_identity_surface()
    r2 = verify_identity_surface()
    assert identity_status_report_to_dict(r1) == identity_status_report_to_dict(r2)


def test_identity_verify_does_not_mutate_state():
    """Verify should produce a report without side effects."""
    before = build_identity_status_report()
    _ = verify_identity_surface()
    after = build_identity_status_report()
    assert identity_status_report_to_dict(before) == identity_status_report_to_dict(after)


def test_identity_verify_reports_subsystems():
    report = verify_identity_surface()
    assert len(report.subsystems) == len(ALL_SUBSYSTEMS)


# ---------------------------------------------------------------------------
# Human-readable output tests
# ---------------------------------------------------------------------------


def test_format_identity_status_human_contains_keywords():
    report = build_identity_status_report()
    text = format_identity_status_human(report)
    assert "Identity Status:" in text
    assert "Summary:" in text


def test_format_envelope_human_contains_keywords():
    env = build_identity_cli_envelope(
        command="test",
        status=IdentityCliStatus.DEGRADED,
        errors=("err1",),
        warnings=("warn1",),
    )
    text = format_envelope_human(env)
    assert "Command:" in text
    assert "Status:" in text
    assert "DEGRADED" in text
    assert "Errors:" in text
    assert "err1" in text


def test_human_output_exposes_blockers():
    report = IdentityStatusReport(
        status=IdentityCliStatus.BLOCKED,
        subsystems=(
            IdentitySubsystemStatus(
                name="test",
                status=IdentityCliStatus.BLOCKED,
                summary="broken",
                errors=("test_error",),
            ),
        ),
        errors=("test_error",),
        suggested_next_commands=("fix it",),
    )
    text = format_identity_status_human(report)
    assert "BLOCKED" in text
    assert "test_error" in text
    assert "fix it" in text


def test_human_output_does_not_hide_blockers():
    report = IdentityStatusReport(
        status=IdentityCliStatus.BLOCKED,
        subsystems=(),
        errors=("fatal_error",),
        warnings=("minor_warning",),
        suggested_next_commands=(),
    )
    text = format_identity_status_human(report)
    assert "fatal_error" in text
    assert "Blockers:" in text
