"""P5.13 — Read-only trace CLI commands, resolver-backed."""

from __future__ import annotations

import argparse
import json

from agentic_runtime.cli_modules.trace_commands import (
    cmd_trace_audit,
    cmd_trace_inspect,
    cmd_trace_status,
    cmd_trace_verify,
)
from agentic_runtime.aurel_trace.trace_demo import build_demo_trace_substrate


def _args(**kw):
    return argparse.Namespace(**kw)


def test_trace_status_runs_and_is_json(capsys):
    rc = cmd_trace_status(_args(json=True))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dev_fixture"] is True
    assert len(payload["decisions"]) == 2


def test_trace_verify_runs(capsys):
    rc = cmd_trace_verify(_args(json=True))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "verifications" in payload


def test_trace_audit_runs(capsys):
    rc = cmd_trace_audit(_args(json=True))
    assert rc == 0
    audit = json.loads(capsys.readouterr().out)
    assert audit["targets_checked"] == 2
    assert audit["verified_count"] == 1


def test_trace_inspect_requires_target(capsys):
    rc = cmd_trace_inspect(_args(target=None))
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert "error" in payload


def test_trace_inspect_unknown_target_is_unavailable(capsys):
    rc = cmd_trace_inspect(_args(target="no-such-target"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "UNAVAILABLE"


def test_cli_only_prints_trace_verified_for_resolver_verified_target(capsys):
    # Cross-check CLI output against the resolver decisions directly.
    substrate = build_demo_trace_substrate()
    verified_ids = {
        d.target_id for d in substrate.decisions if d.status.value == "TRACE_VERIFIED"
    }
    cmd_trace_status(_args(json=True))
    payload = json.loads(capsys.readouterr().out)
    for decision in payload["decisions"]:
        if decision["status"] == "TRACE_VERIFIED":
            assert decision["target_id"] in verified_ids
            assert decision["verified"] is True
        else:
            assert decision["verified"] is False
    # And at least one target is honestly NOT verified.
    assert any(d["status"] != "TRACE_VERIFIED" for d in payload["decisions"])
