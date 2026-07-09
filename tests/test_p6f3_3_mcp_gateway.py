"""F3.3 seal — Aurel as a governed MCP server.

Every inbound MCP call passes six gates: tainted MCP_CLIENT, allowlisted +
contracted, external-floor vs. authority/trust, F1 gate preflight, lease-scoped
real submit, and a governed track-record write. Proven here:

  1. Protocol — initialize / tools/list / unknown-method / malformed all behave.
  2. tools/list exposes only exposed+contracted tools, with an escalation-only
     external risk floor (a TRIVIAL tool is floored up to MEDIUM).
  3. Unexposed tool ⇒ GATEWAY_DENIED, track record DENIED, no execution.
  4. Floor above the operator card ceiling ⇒ hard DENY; within the card but above
     the trust-earned ceiling ⇒ REQUIRE_APPROVAL (bootstrap), neither executes.
  5. Gate denial (policy/permission) ⇒ GATEWAY_DENIED, DENIED recorded.
  6. ALLOW + trusted ⇒ real submit runs, evidence returned, SUCCESS recorded,
     inbound provenance is MCP_CLIENT + instruction-ineligible.
  7. Flag default OFF.
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.external_executor import (
    ExternalExecutorGrant,
    TrackRecordOutcome,
    make_external_executor,
)
from agentic_runtime.mcp_gateway import (
    GATEWAY_DENIED,
    GatewayToolRegistry,
    McpGateway,
    flag_enabled,
)
from agentic_runtime.mcp_gateway.jsonrpc import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
)


def _registry(runtime):
    inner = runtime.runtime
    reg = GatewayToolRegistry()
    reg.expose(inner.contracts.get("list_dir"))
    reg.expose(inner.contracts.get("git_status"))  # intrinsically TRIVIAL
    return reg


def _trusted_profile(max_risk=RiskLevel.MEDIUM, tools=("list_dir",)):
    prof = make_external_executor(
        "cc", ExternalExecutorGrant(allowed_tools=tools, read_paths=(".",),
                                    max_risk=max_risk)
    )
    for i in range(5):  # earn TRUSTED
        prof.ledger.record(
            outcome=TrackRecordOutcome.SUCCESS, tool="seed", action_ref=f"s{i}", tick=i
        )
    return prof


def _gateway(profile):
    rt = build_runtime()
    return McpGateway(rt, profile, _registry(rt)), profile


def _call(gw, name, arguments=None, rid=1):
    return gw.handle({
        "jsonrpc": "2.0", "id": rid, "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })


# --------------------------------------------------------------------------- #
# 1. Protocol.
# --------------------------------------------------------------------------- #
def test_initialize_and_tools_list():
    gw, _ = _gateway(_trusted_profile())
    init = gw.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init["result"]["protocolVersion"]
    assert init["result"]["serverInfo"]["name"] == "aurel"

    listed = gw.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in listed["result"]["tools"]}
    assert names == {"list_dir", "git_status"}


def test_unknown_method_and_malformed():
    gw, _ = _gateway(_trusted_profile())
    unk = gw.handle({"jsonrpc": "2.0", "id": 1, "method": "nope"})
    assert unk["error"]["code"] == METHOD_NOT_FOUND
    bad_ver = gw.handle({"jsonrpc": "1.0", "id": 1, "method": "initialize"})
    assert bad_ver["error"]["code"] == INVALID_REQUEST
    bad_params = gw.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": "not-an-object"})
    assert bad_params["error"]["code"] == INVALID_PARAMS


# --------------------------------------------------------------------------- #
# 2. Escalation-only external floor.
# --------------------------------------------------------------------------- #
def test_external_floor_escalation_only():
    rt = build_runtime()
    reg = GatewayToolRegistry()
    # git_status is intrinsically TRIVIAL; a TRIVIAL annotation cannot lower it.
    exposed = reg.expose(rt.runtime.contracts.get("git_status"),
                         external_risk_floor=RiskLevel.TRIVIAL)
    assert exposed.external_risk_floor is RiskLevel.MEDIUM


# --------------------------------------------------------------------------- #
# 3. Unexposed ⇒ denied, no execution.
# --------------------------------------------------------------------------- #
def test_unexposed_tool_denied():
    gw, prof = _gateway(_trusted_profile())
    resp = _call(gw, "read_file", {"path": "x"})
    assert resp["error"]["code"] == GATEWAY_DENIED
    assert prof.ledger.count(TrackRecordOutcome.DENIED) == 1
    assert prof.ledger.count(TrackRecordOutcome.SUCCESS) == 5  # only the seeds


# --------------------------------------------------------------------------- #
# 4. Floor vs. authority/trust.
# --------------------------------------------------------------------------- #
def test_floor_above_card_ceiling_hard_denies():
    # Untrusted card capped at LOW; list_dir floor MEDIUM > card LOW ⇒ hard DENY.
    prof = make_external_executor(
        "cc", ExternalExecutorGrant(allowed_tools=("list_dir",), max_risk=RiskLevel.LOW)
    )
    gw, _ = _gateway(prof)
    resp = _call(gw, "list_dir", {"path": "."})
    assert resp["error"]["code"] == GATEWAY_DENIED
    assert "card ceiling" in resp["error"]["message"]
    assert prof.ledger.entries[-1].note == "external_floor_exceeds_card"


def test_within_card_but_untrusted_requires_approval():
    # Card MEDIUM, but a fresh (untrusted) executor is capped at TRIVIAL ⇒ approval.
    prof = make_external_executor(
        "cc", ExternalExecutorGrant(allowed_tools=("list_dir",), read_paths=(".",),
                                    max_risk=RiskLevel.MEDIUM)
    )
    gw, _ = _gateway(prof)
    resp = _call(gw, "list_dir", {"path": "."})
    assert resp["error"]["code"] == GATEWAY_DENIED
    assert resp["error"]["data"]["needs_approval"] is True
    assert prof.ledger.entries[-1].note == "requires_approval_untrusted"


# --------------------------------------------------------------------------- #
# 5. Gate (policy/permission) denial.
# --------------------------------------------------------------------------- #
def test_gate_policy_denies_out_of_scope_tool():
    # Trusted, card allows only list_dir; git_status passes the floor but the
    # policy permission gate denies it (not in card scope).
    prof = _trusted_profile(tools=("list_dir",))
    gw, _ = _gateway(prof)
    resp = _call(gw, "git_status", {})
    assert resp["error"]["code"] == GATEWAY_DENIED
    assert resp["error"]["data"]["phase"] == "policy"
    assert prof.ledger.count(TrackRecordOutcome.DENIED) == 1


# --------------------------------------------------------------------------- #
# 6. ALLOW ⇒ real submit, evidence, SUCCESS, provenance.
# --------------------------------------------------------------------------- #
def test_allow_executes_and_records_success():
    prof = _trusted_profile(tools=("list_dir",))
    gw, _ = _gateway(prof)
    resp = _call(gw, "list_dir", {"path": "."})
    assert "result" in resp
    assert resp["result"]["isError"] is False
    ev = resp["result"]["x_evidence"]
    assert ev["runtime_submit_called"] is True
    assert ev["success"] is True
    # SUCCESS recorded (5 seeds + 1).
    assert prof.ledger.count(TrackRecordOutcome.SUCCESS) == 6
    # Inbound provenance is external + instruction-ineligible.
    prov = resp["result"]["x_provenance"]
    assert prov["source_kind"] == "mcp_client"
    assert prov["instruction_eligible"] is False


# --------------------------------------------------------------------------- #
# 7. Flag default OFF.
# --------------------------------------------------------------------------- #
def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_MCP_GATEWAY", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_MCP_GATEWAY", "1")
    assert flag_enabled() is True
