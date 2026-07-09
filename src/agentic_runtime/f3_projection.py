"""
f3_projection.py — F3.5 read-only projections over the external-executor surface.

The read-model behind the Front WorkOPS.Code screen: given an external-executor
profile (F3.2) and the gateway's exposed-tool registry (F3.3), project — without
executing anything — the executor's standing (trust, ceilings, track record) and
exactly which exposed tools it could reach right now, and how.

The per-tool reachability classifier mirrors the gateway's step-3 floor/authority
logic (`server._tools_call`); the F3.5 seal cross-checks that it never drifts from
what the gateway actually decides.
"""
from __future__ import annotations

from .external_executor import ExternalExecutorProfile, _RISK_ORDER
from .mcp_gateway.tool_registry import ExposedTool, GatewayToolRegistry


def classify_reachability(profile: ExternalExecutorProfile, tool: ExposedTool) -> str:
    """How the executor stands to this tool right now (no execution).

    Mirrors the gateway floor gate: above the operator card ceiling ⇒ ``denied``;
    within the card but above the trust-earned ceiling ⇒ ``needs_approval``;
    otherwise ⇒ ``reachable`` (still subject to the F3.1 gate at call time).
    """
    floor = _RISK_ORDER[tool.external_risk_floor]
    card = _RISK_ORDER[profile.card.authority.max_risk]
    trust = _RISK_ORDER[profile.effective_max_risk]
    if floor > card:
        return "denied"
    if floor > trust:
        return "needs_approval"
    return "reachable"


def project_executor_standing(profile: ExternalExecutorProfile, recent: int = 5) -> dict:
    """Read-only standing of one external executor."""
    entries = profile.ledger.entries
    tail = entries[-recent:] if recent > 0 else entries
    record = profile.ledger.to_dict()
    return {
        "executor_id": profile.executor_id,
        "trust": profile.trust.value,
        "card_max_risk": profile.card.authority.max_risk.value,
        "effective_max_risk": profile.effective_max_risk.value,
        "track_record": {
            "total": len(entries),
            "successes": record["successes"],
            "failures": record["failures"],
            "denied": record["denied"],
            "blocked": record["blocked"],
        },
        "recent": [e.to_dict() for e in tail],
    }


def project_gateway_surface(
    registry: GatewayToolRegistry, profile: ExternalExecutorProfile
) -> dict:
    """What the executor could reach across the exposed tool surface (read-only)."""
    tools = []
    for name in sorted(registry.names()):
        tool = registry.get(name)
        if tool is None:
            continue
        tools.append(
            {
                "name": tool.name,
                "external_risk_floor": tool.external_risk_floor.value,
                "reachability": classify_reachability(profile, tool),
            }
        )
    return {
        "executor_id": profile.executor_id,
        "trust": profile.trust.value,
        "effective_max_risk": profile.effective_max_risk.value,
        "tools": tools,
    }
