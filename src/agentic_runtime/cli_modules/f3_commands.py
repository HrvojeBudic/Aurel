"""``aurel f3 seal`` / ``aurel f3 surface`` — F3.5 read-only inspection.

``seal`` prints the derived F3 exit seal (SEALED only when every slice module +
report is present; deferred surfaces stay explicit as UNAVAILABLE). ``surface``
projects, without executing anything, which exposed tools a demo external
executor could reach right now. Both are read-only; ``seal`` exits non-zero when
the phase is not SEALED so it can gate CI.
"""
from __future__ import annotations

import argparse
import json


def cmd_f3_seal(args: argparse.Namespace) -> int:
    from ..f3_seal import build_f3_exit_seal

    seal = build_f3_exit_seal(reports_dir=getattr(args, "reports_dir", "agent/reports"))
    if getattr(args, "json", False):
        print(json.dumps(seal.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"F3 exit seal: {seal.status.value}  "
              f"({seal.to_dict()['passed']} passed / {seal.to_dict()['blocked']} blocked)")
        for item in seal.items:
            mark = "ok" if item.status.value == "PASSED" else "BLOCKED"
            print(f"  [{mark:7}] {item.slice_id}  {item.title}")
        print("  unavailable (explicit, not overclaimed):")
        for u in seal.unavailable:
            print(f"    - {u.surface_id}: {u.reason}  → {u.future_owner}")
    return 0 if seal.sealed else 2


def cmd_f3_surface(args: argparse.Namespace) -> int:
    from ..core_types import RiskLevel
    from ..external_executor import (
        ExternalExecutorGrant,
        TrackRecordOutcome,
        make_external_executor,
    )
    from ..f3_projection import project_executor_standing, project_gateway_surface
    from ..mcp_gateway import GatewayToolRegistry

    # A demo profile + exposed surface (read-only illustration; no runtime built).
    grant = ExternalExecutorGrant(
        allowed_tools=("list_dir", "git_status"),
        read_paths=(".",),
        max_risk=RiskLevel.MEDIUM,
    )
    profile = make_external_executor(getattr(args, "executor", "demo-executor"), grant)
    if getattr(args, "trusted", False):
        for i in range(5):
            profile.ledger.record(
                outcome=TrackRecordOutcome.SUCCESS, tool="seed",
                action_ref=f"s{i}", tick=i,
            )

    from ..tool_contracts import default_contract_registry

    contracts = default_contract_registry()
    registry = GatewayToolRegistry()
    for name in ("list_dir", "git_status"):
        contract = contracts.get(name)
        if contract is not None:
            registry.expose(contract)

    out = {
        "standing": project_executor_standing(profile),
        "surface": project_gateway_surface(registry, profile),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0
