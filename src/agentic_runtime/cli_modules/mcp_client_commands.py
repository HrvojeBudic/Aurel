"""``aurel mcp-client`` — F4B read-only inspection (list-servers / seal / demo).

``list-servers`` prints the configured external MCP servers (all disabled by
default). ``seal`` prints the derived F4B exit seal. ``demo`` runs the full
connect → list-tools → call → ContextLoom-sink path against an in-process fake
server (no network), showing that a hostile tool description + output stay tainted
and DATA-fenced. All read-only; nothing connects to a live server.
"""
from __future__ import annotations

import argparse
import json


def cmd_mcp_client_list_servers(args: argparse.Namespace) -> int:
    from ..mcp_client.registry import McpConfigError, McpServerRegistry

    path = getattr(args, "config", "config/live/mcp_servers.yaml")
    try:
        reg = McpServerRegistry.load(path)
    except McpConfigError as e:
        print(f"mcp-client: {e}")
        return 1
    servers = [reg.get(n).to_dict() for n in sorted(reg.names())]
    if getattr(args, "json", False):
        print(json.dumps(servers, indent=2, sort_keys=True))
    else:
        for s in servers:
            state = "enabled" if s["enabled"] else "disabled"
            where = s["url"] or f"{s['command']} {' '.join(s['args'])}".strip()
            print(f"  [{state:8}] {s['name']:16} {s['transport']:5} {where}")
    return 0


def cmd_mcp_client_seal(args: argparse.Namespace) -> int:
    from ..mcp_client.f4b_seal import build_f4b_exit_seal

    seal = build_f4b_exit_seal(reports_dir=getattr(args, "reports_dir", "agent/reports"))
    if getattr(args, "json", False):
        print(json.dumps(seal.to_dict(), indent=2, sort_keys=True))
    else:
        d = seal.to_dict()
        print(f"F4B exit seal: {seal.status.value}  "
              f"({d['passed']} passed / {d['blocked']} blocked)")
        for item in seal.items:
            mark = "ok" if item.status.value == "PASSED" else "BLOCKED"
            print(f"  [{mark:7}] {item.slice_id}  {item.title}")
        print("  unavailable (explicit, not overclaimed):")
        for u in seal.unavailable:
            print(f"    - {u.surface_id}: {u.reason}  → {u.future_owner}")
    return 0 if seal.sealed else 2


def cmd_mcp_client_demo(args: argparse.Namespace) -> int:
    from ..context_loom import assemble
    from ..mcp_client.client import McpClient
    from ..mcp_client.fake_server import FakeMcpServerTransport
    from ..mcp_client.loom_sink import sink_tool_result

    client = McpClient(FakeMcpServerTransport(), "fake-mcp")
    client.initialize()
    tools = client.list_tools()
    result = client.call_tool("echo", {"msg": "hello"})
    item = sink_tool_result(result, client.server_name)
    bundle = assemble([item])

    out = {
        "server": "fake-mcp",
        "tools": [t.to_dict() for t in tools],
        "tool_description_instruction_eligible": tools[0].description.instruction_eligible,
        "result_instruction_eligible": item.instruction_eligible,
        "context_ref": bundle.context_ref,
        "rendered_prompt": bundle.to_prompt(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0
