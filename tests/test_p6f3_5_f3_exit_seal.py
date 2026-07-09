"""F3.5 seal — projection + CLI + derived F3 exit seal.

  1. Derived status — SEALED only when every slice's module + report is present;
     a missing report or module BLOCKS the item and the seal (hermetic tmp-dir).
  2. Honest — overclaim guards hard-False; UNAVAILABLE surfaces explicit with a
     reason and future owner.
  3. Projections — executor standing + gateway surface; reachability classifier
     does NOT drift from the gateway's actual verdict (reachable/approval/denied).
  4. Real repo — the live reports dir seals SEALED.
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.external_executor import (
    ExternalExecutorGrant,
    TrackRecordOutcome,
    make_external_executor,
)
from agentic_runtime.f3_projection import (
    classify_reachability,
    project_executor_standing,
    project_gateway_surface,
)
from agentic_runtime.f3_seal import (
    F3_SLICES,
    SealStatus,
    build_f3_exit_seal,
)
from agentic_runtime.mcp_gateway import GatewayToolRegistry, McpGateway


def _write_all_reports(d):
    for _sid, _title, _module, report in F3_SLICES:
        (d / report).write_text("stub", encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. Derived status.
# --------------------------------------------------------------------------- #
def test_all_present_is_sealed(tmp_path):
    _write_all_reports(tmp_path)
    seal = build_f3_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.SEALED
    assert seal.sealed is True
    assert all(i.status.value == "PASSED" for i in seal.items)


def test_missing_report_blocks(tmp_path):
    _write_all_reports(tmp_path)
    # Remove one report ⇒ that item and the seal are BLOCKED.
    (tmp_path / F3_SLICES[0][3]).unlink()
    seal = build_f3_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED
    assert seal.sealed is False
    blocked = [i for i in seal.items if i.status.value == "BLOCKED"]
    assert blocked and blocked[0].slice_id == "F3.0"


def test_empty_reports_dir_blocks(tmp_path):
    seal = build_f3_exit_seal(reports_dir=str(tmp_path))
    assert seal.status is SealStatus.BLOCKED  # modules present, reports absent


# --------------------------------------------------------------------------- #
# 2. Honesty.
# --------------------------------------------------------------------------- #
def test_overclaim_guards_are_false(tmp_path):
    _write_all_reports(tmp_path)
    seal = build_f3_exit_seal(reports_dir=str(tmp_path))
    assert seal.claims_transport_wired is False
    assert seal.claims_content_passthrough is False
    assert seal.claims_client_bridge_live is False


def test_unavailable_surfaces_explicit(tmp_path):
    _write_all_reports(tmp_path)
    seal = build_f3_exit_seal(reports_dir=str(tmp_path))
    ids = {u.surface_id for u in seal.unavailable}
    assert {"mcp_transport", "content_passthrough", "mcp_client_bridge"} <= ids
    for u in seal.unavailable:
        assert u.reason and u.future_owner  # never a bare UNAVAILABLE


# --------------------------------------------------------------------------- #
# 3. Projections + no-drift cross-check vs. the real gateway.
# --------------------------------------------------------------------------- #
def _profile(max_risk=RiskLevel.MEDIUM, trusted=False):
    prof = make_external_executor(
        "cc", ExternalExecutorGrant(allowed_tools=("list_dir",), read_paths=(".",),
                                    max_risk=max_risk)
    )
    if trusted:
        for i in range(5):
            prof.ledger.record(outcome=TrackRecordOutcome.SUCCESS, tool="s",
                               action_ref=f"s{i}", tick=i)
    return prof


def test_executor_standing_projection():
    prof = _profile(trusted=True)
    standing = project_executor_standing(prof)
    assert standing["trust"] == "trusted"
    assert standing["effective_max_risk"] == "medium"
    assert standing["track_record"]["successes"] == 5


def test_reachability_matches_gateway_verdict():
    # Build the real gateway and assert projection == actual outcome, 3 ways.
    rt = build_runtime()
    reg = GatewayToolRegistry()
    reg.expose(rt.runtime.contracts.get("list_dir"))
    tool = reg.get("list_dir")

    # (a) trusted MEDIUM ⇒ reachable ⇒ gateway executes (result, not error).
    trusted = _profile(max_risk=RiskLevel.MEDIUM, trusted=True)
    assert classify_reachability(trusted, tool) == "reachable"
    gw = McpGateway(rt, trusted, reg)
    resp = gw.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                      "params": {"name": "list_dir", "arguments": {"path": "."}}})
    assert "result" in resp

    # (b) untrusted within card ⇒ needs_approval ⇒ gateway denies with needs_approval.
    boot = _profile(max_risk=RiskLevel.MEDIUM, trusted=False)
    assert classify_reachability(boot, tool) == "needs_approval"
    gw2 = McpGateway(build_runtime(), boot, reg)
    r2 = gw2.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "list_dir", "arguments": {"path": "."}}})
    assert r2["error"]["data"].get("needs_approval") is True

    # (c) card below floor ⇒ denied ⇒ gateway hard-denies over card.
    low = _profile(max_risk=RiskLevel.LOW, trusted=False)
    assert classify_reachability(low, tool) == "denied"
    gw3 = McpGateway(build_runtime(), low, reg)
    r3 = gw3.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "list_dir", "arguments": {"path": "."}}})
    assert "card ceiling" in r3["error"]["message"]


def test_gateway_surface_projection():
    prof = _profile(trusted=True)
    reg = GatewayToolRegistry()
    rt = build_runtime()
    for name in ("list_dir", "git_status"):
        reg.expose(rt.runtime.contracts.get(name))
    surface = project_gateway_surface(reg, prof)
    assert {t["name"] for t in surface["tools"]} == {"list_dir", "git_status"}
    assert all(t["reachability"] == "reachable" for t in surface["tools"])


# --------------------------------------------------------------------------- #
# 4. Real repo seals SEALED.
# --------------------------------------------------------------------------- #
def test_real_reports_dir_is_sealed():
    seal = build_f3_exit_seal()  # default agent/reports
    assert seal.status is SealStatus.SEALED, seal.to_dict()
