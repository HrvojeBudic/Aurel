"""
server.py — Aurel as a governed MCP server (F3.3).

An external MCP client (a Claude Code session, another agent) reaches Aurel's
tools only through this one door. Every ``tools/call`` is:

  1. **Tainted** — arguments enter as ``make_tainted(..., MCP_CLIENT)``:
     external-origin, instruction-ineligible (F3.0).
  2. **Allowlisted** — the tool must be explicitly exposed AND contracted, else
     it is never listed and never runs (F3.3 registry).
  3. **Floor-checked** — the tool's escalation-only external risk floor must fit
     under the executor's trust-adjusted ceiling (F3.2). An untrusted client can
     not reach a MEDIUM-floor tool until it earns a track record.
  4. **Preflighted** — run through the F3.1 gate (contract + policy) under the
     executor's least-privilege card. DENY / REQUIRE_APPROVAL never execute.
  5. **Executed under a lease** — on ALLOW, a ``SpineToolExecSession`` issues a
     lease bound to exactly this (tool, args) and calls the real
     ``runtime.submit`` kernel (budget / sandbox / approval all apply here — this
     is where a preflight becomes real execution).
  6. **Recorded** — the outcome (SUCCESS / FAILURE / DENIED / BLOCKED) is written
     to the executor's governed track record, feeding its future trust.

The JSON-RPC result carries governed *evidence* of the submit, not raw internal
tool output — full (F2-redacted) content passthrough is a later refinement, so
the gateway never leaks internal data by default.
"""
from __future__ import annotations

import json
from typing import Any

from ..external_executor import ExternalExecutorProfile, TrackRecordOutcome
from ..external_ingress import SourceKind, make_tainted
from ..gate import GateChecker, GateVerdict
from ..spine.tool_exec import SpineExecutionBlocked, SpineToolExecSession
from .jsonrpc import (
    GATEWAY_DENIED,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JsonRpcRequest,
    error,
    parse_request,
    success,
)
from .tool_registry import GatewayToolRegistry

MCP_PROTOCOL_VERSION = "2024-11-05"
GATEWAY_VERSION = "aurel_mcp_gateway.v1"


class McpGateway:
    """One governed MCP server bound to one external-executor profile."""

    def __init__(
        self,
        runtime: Any,
        profile: ExternalExecutorProfile,
        exposed: GatewayToolRegistry,
        *,
        server_name: str = "aurel",
        tick: int = 0,
    ) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self.profile = profile
        self.exposed = exposed
        self.server_name = server_name
        self.tick = tick
        self.gate = GateChecker.from_runtime(runtime)
        self._session = SpineToolExecSession(runtime=self._inner, card=profile.card)

    # ----------------------------------------------------------------- #
    # JSON-RPC dispatch.
    # ----------------------------------------------------------------- #
    def handle(self, raw: Any) -> dict:
        """Handle one JSON-RPC request dict; return one JSON-RPC response dict."""
        parsed = parse_request(raw)
        if isinstance(parsed, dict):  # a parse/validation error response
            return parsed
        req: JsonRpcRequest = parsed

        if req.method == "initialize":
            return self._initialize(req)
        if req.method == "tools/list":
            return success(req.id, {"tools": self.exposed.list_tools()})
        if req.method == "tools/call":
            return self._tools_call(req)
        return error(req.id, METHOD_NOT_FOUND, f"unknown method '{req.method}'")

    def _initialize(self, req: JsonRpcRequest) -> dict:
        return success(
            req.id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "serverInfo": {"name": self.server_name, "version": GATEWAY_VERSION},
                "capabilities": {"tools": {}},
                "x_executor": self.profile.executor_id,
            },
        )

    # ----------------------------------------------------------------- #
    # tools/call — the governed execution path.
    # ----------------------------------------------------------------- #
    def _record(self, outcome: TrackRecordOutcome, tool: str, note: str = "") -> None:
        self.profile.ledger.record(
            outcome=outcome,
            tool=tool,
            action_ref=f"mcp:{self.profile.executor_id}:{tool}",
            tick=self.tick,
            note=note,
        )

    def _tools_call(self, req: JsonRpcRequest) -> dict:
        name = req.params.get("name")
        arguments = req.params.get("arguments", {})
        if not isinstance(name, str) or not name:
            return error(req.id, INVALID_PARAMS, "tools/call requires a string 'name'")
        if not isinstance(arguments, dict):
            return error(req.id, INVALID_PARAMS, "'arguments' must be an object")

        # 1. Provenance — inbound call is external, instruction-ineligible.
        tainted = make_tainted(
            json.dumps({"name": name, "arguments": arguments}, sort_keys=True),
            SourceKind.MCP_CLIENT,
            origin_ref=self.profile.executor_id,
        )
        prov = tainted.to_dict()

        # 2. Allowlist — not exposed ⇒ never runs.
        tool = self.exposed.get(name)
        if tool is None:
            self._record(TrackRecordOutcome.DENIED, name, "not_exposed")
            return error(
                req.id, GATEWAY_DENIED, f"tool '{name}' is not exposed",
                {"provenance": prov},
            )

        # 3. External risk floor vs. the executor's authority AND trust.
        #    - above the operator's card ceiling  ⇒ hard DENY (never authorized).
        #    - within the card but above the trust-earned ceiling ⇒ REQUIRE_APPROVAL
        #      (authorized, but the executor has not yet earned autonomous trust —
        #      this is the bootstrap path: approved runs build the track record).
        from ..external_executor import _RISK_ORDER  # local: light, avoids cycle

        floor = _RISK_ORDER[tool.external_risk_floor]
        card_ceiling = _RISK_ORDER[self.profile.card.authority.max_risk]
        trust_ceiling = _RISK_ORDER[self.profile.effective_max_risk]
        if floor > card_ceiling:
            self._record(TrackRecordOutcome.DENIED, name, "external_floor_exceeds_card")
            return error(
                req.id, GATEWAY_DENIED,
                f"external risk floor {tool.external_risk_floor.value} exceeds "
                f"operator card ceiling {self.profile.card.authority.max_risk.value}",
                {"provenance": prov},
            )
        if floor > trust_ceiling:
            self._record(TrackRecordOutcome.DENIED, name, "requires_approval_untrusted")
            return error(
                req.id, GATEWAY_DENIED,
                "authorized but executor not yet trusted — requires operator approval",
                {"needs_approval": True, "trust": self.profile.trust.value,
                 "provenance": prov},
            )

        # 4. Gate preflight — contract + policy under the least-privilege card.
        decision = self.gate.check(
            card=self.profile.card,
            tool=name,
            args=arguments,
            rationale="mcp gateway tools/call",
            declared_risk=tool.external_risk_floor,
            origin_ref=self.profile.executor_id,
        )
        if decision.verdict is GateVerdict.DENY:
            self._record(TrackRecordOutcome.DENIED, name, "; ".join(decision.reasons))
            return error(
                req.id, GATEWAY_DENIED, "denied by governance",
                {"phase": decision.phase.value, "reasons": list(decision.reasons),
                 "provenance": prov},
            )
        if decision.verdict is GateVerdict.REQUIRE_APPROVAL:
            self._record(TrackRecordOutcome.DENIED, name, "requires_approval")
            return error(
                req.id, GATEWAY_DENIED, "requires operator approval (not executed)",
                {"needs_approval": True, "reasons": list(decision.reasons),
                 "provenance": prov},
            )

        # 5. Execute under a lease — real governed submit (budget/sandbox/approval).
        lease = self._session.issue_lease([(name, arguments)])
        try:
            ev = self._session.submit_step(
                name, arguments, lease,
                current_tick=self.tick, risk=tool.external_risk_floor,
            )
        except SpineExecutionBlocked as e:
            self._record(TrackRecordOutcome.BLOCKED, name, str(e))
            return error(
                req.id, GATEWAY_DENIED, "execution blocked before kernel call",
                {"blocked_reason": str(e), "provenance": prov},
            )

        # 6. Record the outcome; return governed evidence (not raw output).
        if ev.success:
            self._record(TrackRecordOutcome.SUCCESS, name)
            return success(
                req.id,
                {
                    "isError": False,
                    "content": [{"type": "text",
                                 "text": f"{name} executed (verifier_passed="
                                         f"{ev.verifier_passed})"}],
                    "x_evidence": ev.to_dict(),
                    "x_provenance": prov,
                },
            )
        self._record(TrackRecordOutcome.FAILURE, name, "submit_failed")
        return error(
            req.id, GATEWAY_DENIED, f"'{name}' executed but did not succeed",
            {"verifier_passed": ev.verifier_passed, "rolled_back": ev.rolled_back,
             "x_evidence": ev.to_dict(), "provenance": prov},
        )
