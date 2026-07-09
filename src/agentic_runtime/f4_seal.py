"""
f4_seal.py — F4.4 derived exit seal for the cognition / ContextLoom phase.

Derived, never declared: F4 is SEALED only when every slice (F4.0→F4.4) has both
an importable module and a present report; a missing module or report BLOCKS that
item and the seal. Deferred surfaces stay explicit as UNAVAILABLE with a reason
and a future owner — SEALED means governed context assembly + a bounded loop over
it are closed, NOT that the loop runs a live model by default or that direction-B
(Aurel calling OUT to MCP servers) exists.

Overclaim guards (`claims_live_model_loop`, `claims_semantic_summarization`,
`claims_client_bridge_live`) are computed and hard-wired False. Read-only.
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


F4_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("F4.0", "ContextLoom foundation (governed context assembly)",
     "agentic_runtime.context_loom.loom", "AUREL_F4_0_CONTEXTLOOM.md"),
    ("F4.1", "budget-aware context compression",
     "agentic_runtime.context_loom.compression", "AUREL_F4_1_CONTEXT_COMPRESSION.md"),
    ("F4.2", "context trace binding (context_ref)",
     "agentic_runtime.context_loom.context_trace", "AUREL_F4_2_CONTEXT_TRACE.md"),
    ("F4.3", "interactive ReAct loop over the ContextLoom",
     "agentic_runtime.entity_loom_loop", "AUREL_F4_3_ENTITY_LOOP.md"),
    ("F4.4", "projection + CLI + F4 exit seal",
     "agentic_runtime.f4_seal", "AUREL_F4_4_EXIT_SEAL.md"),
)

F4_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("live_model_loop",
     "the loop is sealed under a stub/cassette planner; live-model driving is "
     "opt-in (RouterPlanner + a real router) and not part of the deterministic "
     "sealed path",
     "operator-enabled (router live)"),
    ("context_loom_wired_into_default_plan",
     "AgenticEntity still uses plain assemble_context; ContextLoom is opt-in via "
     "EntityLoomLoop, not wired into the default single-shot plan path",
     "F4 follow-up (AUREL_CONTEXTLOOM load-bearing)"),
    ("semantic_summarization",
     "context compression is extractive head+tail truncation, not semantic "
     "summarization (no model call)",
     "later"),
    ("mcp_client_bridge",
     "direction B (Aurel calls OUT to external MCP servers) still unbuilt; the "
     "ContextLoom is now its governed sink (data-only, provenance, budget) but "
     "the bridge itself is not implemented",
     "F4 follow-up / F5"),
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
class F4ExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    status: SealStatus

    @property
    def claims_live_model_loop(self) -> bool:
        return False

    @property
    def claims_semantic_summarization(self) -> bool:
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
            "claims_live_model_loop": self.claims_live_model_loop,
            "claims_semantic_summarization": self.claims_semantic_summarization,
            "claims_client_bridge_live": self.claims_client_bridge_live,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    if any(i.status is ItemStatus.BLOCKED for i in items):
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f4_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f4-cognition-contextloom-exit-seal.v1",
) -> F4ExitSeal:
    """Build the F4 exit seal from module + report presence. Read-only."""
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
        for sid, title, module, report in F4_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(surface_id=s, reason=r, future_owner=o)
        for s, r, o in F4_UNAVAILABLE
    )
    return F4ExitSeal(
        seal_id=seal_id,
        items=items,
        unavailable=unavailable,
        status=_derive_status(items),
    )
