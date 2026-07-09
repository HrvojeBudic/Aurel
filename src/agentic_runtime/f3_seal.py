"""
f3_seal.py — F3.5 derived exit seal for the external-executor phase.

The seal is a *derived* verdict, never a self-assigned boolean. F3 is SEALED only
when every substantive slice (F3.0→F3.3 + this F3.5) has both an importable module
and a present report; a missing module or report BLOCKS that item and the seal.
Deferred surfaces (transport, content passthrough, the F3.4 client bridge, A2A)
stay explicit as UNAVAILABLE with a reason and a future owner — SEALED means the
inbound governed-executor path is closed, NOT that those surfaces exist.

Read-only and honest: `claims_transport_wired`, `claims_content_passthrough`, and
`claims_client_bridge_live` are computed and hard-wired False — the seal cannot
overclaim capability it does not have. Nothing here executes or mutates.
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_REPORTS_DIR = "agent/reports"


class SealStatus(str, Enum):
    SEALED = "SEALED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


class ItemStatus(str, Enum):
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"


# (slice_id, title, importable module, report filename).
F3_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("F3.0", "external ingress: taint & injection defense",
     "agentic_runtime.external_ingress.taint",
     "AUREL_F3_0_EXTERNAL_INGRESS_TAINT.md"),
    ("F3.1", "aurel gate check governance preflight",
     "agentic_runtime.gate.gate_check", "AUREL_F3_1_GATE_CHECK.md"),
    ("F3.2", "external-executor identity + budget + track record",
     "agentic_runtime.external_executor", "AUREL_F3_2_EXTERNAL_EXECUTOR.md"),
    ("F3.3", "mcp_gateway — Aurel as a governed MCP server",
     "agentic_runtime.mcp_gateway.server", "AUREL_F3_3_MCP_GATEWAY.md"),
    ("F3.5", "projection + CLI + F3 exit seal",
     "agentic_runtime.f3_seal", "AUREL_F3_5_EXIT_SEAL.md"),
)

# (surface_id, reason, future_owner) — explicitly not delivered in F3.
F3_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("mcp_transport",
     "stdio/HTTP JSON-RPC transport not wired; McpGateway.handle(dict) is the "
     "governed core, a transport loop is a thin shell",
     "F3 follow-up (AUREL_MCP_GATEWAY load-bearing)"),
    ("content_passthrough",
     "gateway returns governed evidence, not raw tool output; F2-redacted "
     "content passthrough deferred so nothing leaks by default",
     "F3 follow-up"),
    ("mcp_client_bridge",
     "direction B (Aurel calls OUT to external MCP servers) deferred; belongs "
     "atop ContextLoom where tainted external output has a governed consumer",
     "F4 (ContextLoom)"),
    ("a2a_messaging",
     "agent-to-agent messaging not implemented (largest surface, sequenced last)",
     "later (Track D, A2A last)"),
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
        if self.module_present and self.report_present:
            return ItemStatus.PASSED
        return ItemStatus.BLOCKED

    def to_dict(self) -> dict:
        return {
            "slice_id": self.slice_id,
            "title": self.title,
            "module": self.module,
            "report": self.report,
            "module_present": self.module_present,
            "report_present": self.report_present,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class UnavailableSurface:
    surface_id: str
    reason: str
    future_owner: str

    def to_dict(self) -> dict:
        return {
            "surface_id": self.surface_id,
            "reason": self.reason,
            "future_owner": self.future_owner,
        }


@dataclass(frozen=True)
class F3ExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    status: SealStatus

    # Honest overclaim guards — computed, hard-wired False.
    @property
    def claims_transport_wired(self) -> bool:
        return False

    @property
    def claims_content_passthrough(self) -> bool:
        return False

    @property
    def claims_client_bridge_live(self) -> bool:
        return False

    @property
    def sealed(self) -> bool:
        return self.status is SealStatus.SEALED

    def to_dict(self) -> dict:
        return {
            "seal_id": self.seal_id,
            "status": self.status.value,
            "sealed": self.sealed,
            "passed": sum(1 for i in self.items if i.status is ItemStatus.PASSED),
            "blocked": sum(1 for i in self.items if i.status is ItemStatus.BLOCKED),
            "items": [i.to_dict() for i in self.items],
            "unavailable": [u.to_dict() for u in self.unavailable],
            "claims_transport_wired": self.claims_transport_wired,
            "claims_content_passthrough": self.claims_content_passthrough,
            "claims_client_bridge_live": self.claims_client_bridge_live,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    """Derived, never declared: any BLOCKED ⇒ BLOCKED; all PASSED ⇒ SEALED."""
    if any(i.status is ItemStatus.BLOCKED for i in items):
        # A partially-present phase is BLOCKED, not silently SEALED. (There is no
        # PARTIAL path today — every slice is required — but the status is kept
        # for symmetry with the P5 seal vocabulary.)
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f3_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f3-external-executors-exit-seal.v1",
) -> F3ExitSeal:
    """Build the F3 exit seal from module presence + report presence. Read-only."""
    base = Path(reports_dir)
    items = tuple(
        SealChecklistItem(
            slice_id=sid,
            title=title,
            module=module,
            report=report,
            module_present=_module_present(module),
            report_present=(base / report).is_file(),
        )
        for sid, title, module, report in F3_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(surface_id=s, reason=r, future_owner=o)
        for s, r, o in F3_UNAVAILABLE
    )
    return F3ExitSeal(
        seal_id=seal_id,
        items=items,
        unavailable=unavailable,
        status=_derive_status(items),
    )
