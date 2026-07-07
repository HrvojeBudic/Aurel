"""dual-kernel CLI surface — status / bindings / verify-ledger / show.

Direct cmd-function calls with real namespaces (fast, deterministic) plus a real
tampered-ledger case proving verify-ledger fails closed.
"""
from __future__ import annotations

import argparse
import json

from agentic_runtime.cli_modules.dual_kernel_commands import (
    cmd_dual_kernel_bindings,
    cmd_dual_kernel_show,
    cmd_dual_kernel_status,
    cmd_dual_kernel_verify_ledger,
)
from agentic_runtime.dual_kernel import DualKernelLedger


def _ns(**kw):
    return argparse.Namespace(**kw)


def test_status_reports_coverage_ok(capsys):
    rc = cmd_dual_kernel_status(_ns(json=True))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["canon_coverage"] == "ok"
    assert out["merge_gates"] == out["nc_bindings"] == 11


def test_bindings_lists_every_gate(capsys):
    rc = cmd_dual_kernel_bindings(_ns(json=True))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert "simulation_live_resolved" in out
    assert out["simulation_live_resolved"]["nc_law"] == "NC-01I-068"


def _write_ledger(path):
    led = DualKernelLedger(path=path)
    led.append(command_id="c0", task_id="t", route="governed", autonomy_index=4,
               verdict="pass", final_status="pass", nc_laws=["NC-01I-068"],
               executed=True)
    led.append(command_id="c1", task_id="t", route="hard", autonomy_index=8,
               verdict="inner_ok", final_status="inner_ok", executed=True)


def test_verify_ledger_ok(tmp_path, capsys):
    path = str(tmp_path / "dk.jsonl")
    _write_ledger(path)
    rc = cmd_dual_kernel_verify_ledger(_ns(path=path))
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"] is True and out["count"] == 2


def test_verify_ledger_detects_tamper(tmp_path, capsys):
    path = tmp_path / "dk.jsonl"
    _write_ledger(str(path))
    lines = path.read_text().splitlines()
    row = json.loads(lines[0])
    row["final_status"] = "blocking_fail"  # tamper without recomputing the hash
    lines[0] = json.dumps(row, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")

    rc = cmd_dual_kernel_verify_ledger(_ns(path=str(path)))
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["ok"] is False and out["reason"] == "payload tampered"


def test_show_projects_readmodel(tmp_path, capsys):
    path = str(tmp_path / "dk.jsonl")
    _write_ledger(path)
    rc = cmd_dual_kernel_show(_ns(path=path, json=True))
    proj = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert proj[0]["projection"] is True
    assert proj[0]["route"] == "governed"
