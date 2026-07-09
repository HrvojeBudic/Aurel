"""
f4b_seal.py — derived exit seal for the MCP client bridge phase (B6).

Derived, never declared: F4B is SEALED only when every slice (B0→B6) has an
importable module and a present report. Deferred surfaces stay explicit as
UNAVAILABLE — the live-server connection (operator opt-in), SSE streaming, the
parked security hardening (SSRF/egress guard, pin enforcement, per-server grant,
unicode de-smuggling, fence-nonce, fuzz drill), D2 (MCP tools as plan steps), and
A2A. SEALED means: Aurel can connect to an MCP server, discover + call tools under
governance, and land the tainted result in the ContextLoom — not that a live
server is wired or the hardening is built.
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_REPORTS_DIR = "agent/reports"


class SealStatus(str, Enum):
    SEALED = "SEALED"
    BLOCKED = "BLOCKED"


class ItemStatus(str, Enum):
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"


F4B_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("B0", "client-side JSON-RPC 2.0 codec",
     "agentic_runtime.mcp_client.jsonrpc_client", "AUREL_F4B_0_JSONRPC_CLIENT.md"),
    ("B1", "transports (stdio + Streamable HTTP)",
     "agentic_runtime.mcp_client.transport", "AUREL_F4B_1_TRANSPORT.md"),
    ("B2", "tool-result content model",
     "agentic_runtime.mcp_client.content", "AUREL_F4B_2_CONTENT.md"),
    ("B3", "MCP protocol client",
     "agentic_runtime.mcp_client.client", "AUREL_F4B_3_CLIENT.md"),
    ("B4", "bridge into governance",
     "agentic_runtime.mcp_client.bridge", "AUREL_F4B_4_BRIDGE.md"),
    ("B5", "server registry + connection manager",
     "agentic_runtime.mcp_client.registry", "AUREL_F4B_5_REGISTRY.md"),
    ("B6", "ContextLoom sink + CLI + exit seal",
     "agentic_runtime.mcp_client.loom_sink", "AUREL_F4B_6_EXIT_SEAL.md"),
)

F4B_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("live_server_connection",
     "no live external MCP server is wired; connection is operator opt-in via "
     "config/live/mcp_servers.yaml (enabled) + AUREL_MCP_CLIENT",
     "operator-enabled"),
    ("sse_streaming",
     "Streamable-HTTP SSE streaming responses not implemented; one JSON response "
     "per POST",
     "F4B follow-up"),
    ("security_hardening",
     "parked opt-in hardening (SSRF/egress guard, pin enforcement, per-server "
     "secret grant, unicode/ANSI de-smuggling, fence-nonce, MCP fuzz drill)",
     "opt-in when a live server is connected"),
    ("mcp_plan_steps_d2",
     "MCP tools as steps inside an LLM plan (STRUCTURED_PLAN_SCHEMA v2) not built",
     "D2 (later)"),
    ("a2a_messaging", "agent-to-agent messaging not implemented", "later"),
)


def _module_present(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ModuleNotFoundError, ValueError):
        return False


@dataclass(frozen=True)
class SealChecklistItem:
    slice_id: str
    title: str
    module: str
    report: str
    module_present: bool
    report_present: bool

    @property
    def status(self) -> ItemStatus:
        return ItemStatus.PASSED if (self.module_present and self.report_present) else ItemStatus.BLOCKED

    def to_dict(self) -> dict:
        return {
            "slice_id": self.slice_id, "title": self.title, "module": self.module,
            "report": self.report, "module_present": self.module_present,
            "report_present": self.report_present, "status": self.status.value,
        }


@dataclass(frozen=True)
class UnavailableSurface:
    surface_id: str
    reason: str
    future_owner: str

    def to_dict(self) -> dict:
        return {"surface_id": self.surface_id, "reason": self.reason,
                "future_owner": self.future_owner}


@dataclass(frozen=True)
class F4BExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    status: SealStatus

    @property
    def claims_live_server(self) -> bool:
        return False

    @property
    def claims_security_hardening(self) -> bool:
        return False

    @property
    def sealed(self) -> bool:
        return self.status is SealStatus.SEALED

    def to_dict(self) -> dict:
        return {
            "seal_id": self.seal_id, "status": self.status.value, "sealed": self.sealed,
            "passed": sum(1 for i in self.items if i.status is ItemStatus.PASSED),
            "blocked": sum(1 for i in self.items if i.status is ItemStatus.BLOCKED),
            "items": [i.to_dict() for i in self.items],
            "unavailable": [u.to_dict() for u in self.unavailable],
            "claims_live_server": self.claims_live_server,
            "claims_security_hardening": self.claims_security_hardening,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    if any(i.status is ItemStatus.BLOCKED for i in items):
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f4b_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f4b-mcp-client-bridge-exit-seal.v1",
) -> F4BExitSeal:
    base = Path(reports_dir)
    items = tuple(
        SealChecklistItem(
            slice_id=sid, title=title, module=module, report=report,
            module_present=_module_present(module),
            report_present=(base / report).is_file(),
        )
        for sid, title, module, report in F4B_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(s, r, o) for s, r, o in F4B_UNAVAILABLE
    )
    return F4BExitSeal(seal_id=seal_id, items=items, unavailable=unavailable,
                       status=_derive_status(items))
