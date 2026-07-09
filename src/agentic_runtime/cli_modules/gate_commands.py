"""``aurel gate check`` — F3.1 governance preflight for external executors.

Runs a proposed ``(tool, args)`` from an external executor through Aurel's real
contract + policy chain **read-only** and prints allow/deny + reason. Nothing
executes, no budget is charged, no state changes: it answers "would governance
admit this?" as a preflight the Front WorkOPS.Code screen will surface.

The proposal is read from ``--proposal`` (inline JSON) or ``--proposal-file``. An
optional ``--card`` JSON supplies the external executor's AgentCard; without it a
minimal least-privilege external-executor card is used. Honest output: a missing
tool contract or a policy denial is reported with its reason, never silently
passed; malformed JSON fails closed with exit 1.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json_arg(inline: str | None, file_path: str | None) -> Any:
    if inline is not None:
        return json.loads(inline)
    if file_path is not None:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    return None


def _default_external_card(name: str) -> Any:
    from ..core_types import AgentCard, AgentClass, AuthorityScope, RiskLevel

    return AgentCard.make(
        name=name,
        agent_class=AgentClass.EXECUTION,
        mission="external executor (F3.1 gate preflight)",
        authority=AuthorityScope(max_risk=RiskLevel.LOW),
    )


def _card_from_json(data: dict) -> Any:
    from ..core_types import AgentCard, AgentClass, AuthorityScope, RiskLevel

    auth_data = dict(data.get("authority", {}) or {})
    if "max_risk" in auth_data:
        auth_data["max_risk"] = RiskLevel(auth_data["max_risk"])
    authority = AuthorityScope(**auth_data)
    return AgentCard.make(
        name=data.get("name", "external-executor"),
        agent_class=AgentClass(data.get("agent_class", "execution")),
        mission=data.get("mission", "external executor (F3.1 gate preflight)"),
        authority=authority,
        allowed_tools=list(data.get("allowed_tools", [])),
        denied_tools=list(data.get("denied_tools", [])),
    )


def cmd_gate_check(args: argparse.Namespace) -> int:
    from .. import build_runtime
    from ..core_types import RiskLevel
    from ..gate import GateChecker

    try:
        proposal = _load_json_arg(
            getattr(args, "proposal", None), getattr(args, "proposal_file", None)
        )
    except (json.JSONDecodeError, OSError) as e:
        print(f"gate check: cannot read proposal ({e})")
        return 1
    if not isinstance(proposal, dict) or "tool" not in proposal:
        print('gate check: proposal must be a JSON object with a "tool" field')
        return 1

    try:
        card_data = _load_json_arg(
            getattr(args, "card", None), getattr(args, "card_file", None)
        )
    except (json.JSONDecodeError, OSError) as e:
        print(f"gate check: cannot read card ({e})")
        return 1

    card = (
        _card_from_json(card_data)
        if isinstance(card_data, dict)
        else _default_external_card(getattr(args, "executor", "external-executor"))
    )

    declared_risk = RiskLevel(proposal.get("declared_risk", "medium"))
    runtime = build_runtime()
    checker = GateChecker.from_runtime(runtime)
    decision = checker.check(
        card=card,
        tool=str(proposal["tool"]),
        args=dict(proposal.get("args", {}) or {}),
        rationale=str(proposal.get("rationale", "")),
        declared_risk=declared_risk,
        expected_effect=str(proposal.get("expected_effect", "")),
        origin_ref=getattr(args, "executor", "") or card.id,
    )

    if getattr(args, "json", False):
        print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"gate check  tool={decision.tool}  verdict={decision.verdict.value.upper()}"
              f"  phase={decision.phase.value}  risk={decision.risk.value}")
        if decision.reasons:
            for r in decision.reasons:
                print(f"  reason: {r}")
        if decision.code:
            print(f"  code: {decision.code}")
        if decision.injection_scan.has_findings:
            sev = decision.injection_scan.max_severity
            print(f"  advisory: proposal matched injection signatures "
                  f"(max_severity={sev.value if sev else 'none'})")
        if decision.allowed:
            print("  note: ALLOW is a governance preflight — budget / sandbox / "
                  "approval still apply at execution")
        elif decision.requires_approval:
            print("  note: policy admits only with operator approval (HITL)")
    # Exit 0 ALLOW, 3 REQUIRE_APPROVAL, 2 DENY (1 = usage/parse error).
    if decision.allowed:
        return 0
    if decision.requires_approval:
        return 3
    return 2
