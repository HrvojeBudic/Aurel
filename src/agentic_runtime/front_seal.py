"""
front_seal.py — F5.9 derived exit seal for the Aurel Front v1 phase.

Derived, never declared: F5 is SEALED only when every slice (F5.0a→F5.9) has both
an importable module and a present report; a missing module or report BLOCKS that
item and the whole seal. Deferred surfaces stay explicit in the UNAVAILABLE
registry — each with a reason and a future owner. SEALED means the one door (Signal
+ WorkOPS chat → governed conversation → approval → runtime.submit → live read
projections) is closed, NOT that a live model runs by default, nor that role-fluid
AurelEU / Watchtower / WorkOPS-Code / library time-travel / wss-TLS exist.

Overclaim guards (`claims_remote_websocket`, `claims_wss_tls`,
`claims_aureleu_dispatcher_live`, `claims_watchtower_live`, `claims_workops_ai_editor`,
`claims_library_time_travel`) are computed and hard-wired False. Read-only.
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


# (slice_id, title, importable module, per-slice report)
F5_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("F5.0a", "one-door HTTP server foundation",
     "agentic_runtime.front_server.server", "AUREL_F5_0A_ONE_DOOR.md"),
    ("F5.0b", "WebSocket transport (RFC 6455, stdlib)",
     "agentic_runtime.front_server.websocket", "AUREL_F5_0B_WEBSOCKET.md"),
    ("F5.C", "governed LLM conversation engine",
     "agentic_runtime.front_server.conversation", "AUREL_F5_C_CONVERSATION_ENGINE.md"),
    ("F5.1", "live read projections",
     "agentic_runtime.front_server.read_models", "AUREL_F5_1_LIVE_READ_MODELS.md"),
    ("F5.2", "persistent approval inbox + two-phase act",
     "agentic_runtime.front_server.approval_inbox", "AUREL_F5_2_APPROVAL_INBOX.md"),
    ("F5.3", "Signal chat contract",
     "agentic_runtime.front_server.signal", "AUREL_F5_3_SIGNAL_CHAT.md"),
    ("F5.4", "unified Library read-model",
     "agentic_runtime.front_server.library", "AUREL_F5_4_LIBRARY_READ_MODEL.md"),
    ("F5.5", "HQ.Command read-model",
     "agentic_runtime.front_server.hq_command", "AUREL_F5_5_HQ_COMMAND.md"),
    ("F5.6", "Board decision journal",
     "agentic_runtime.front_server.board", "AUREL_F5_6_BOARD_JOURNAL.md"),
    ("F5.7", "WorkOPS chat on the conversation engine",
     "agentic_runtime.front_server.workops", "AUREL_F5_7_WORKOPS_CHAT.md"),
    ("F5.8", "React Front v1 wiring (one door)",
     "agentic_runtime.front_server.proposal_dispatcher", "AUREL_F5_8_REACT_FRONT_WIRING.md"),
    ("F5.9", "derived exit seal + projection + CLI",
     "agentic_runtime.front_seal", "AUREL_F5_9_FRONT_EXIT_SEAL.md"),
)

F5_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("wss_tls_remote_transport",
     "v1 WebSocket is localhost with no TLS; wss/remote transport awaits a "
     "Tauri-Rust transport",
     "Tauri-Rust, by measurement"),
    ("aureleu_role_fluid_dispatcher",
     "AurelEU is a PARTIAL seam (one default persona); role-fluid persona switching "
     "and mandate resolution are not live",
     "F6"),
    ("watchtower_alerts",
     "the HQ.Command Watchtower alert feed is a declared empty seam; no live alerts",
     "F7"),
    ("workops_ai_editor",
     "WorkOPS Code (read-only file browser, terminal, AI-editor / collaboration) is "
     "not built; only WorkOPS chat is live",
     "after F7"),
    ("library_time_travel",
     "Library as-of replay / time-travel is not built; the export manifest is only "
     "projected when injected",
     "F8"),
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
        return {"surface_id": self.surface_id, "reason": self.reason,
                "future_owner": self.future_owner}


@dataclass(frozen=True)
class F5ExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    status: SealStatus

    @property
    def claims_remote_websocket(self) -> bool:
        return False

    @property
    def claims_wss_tls(self) -> bool:
        return False

    @property
    def claims_aureleu_dispatcher_live(self) -> bool:
        return False

    @property
    def claims_watchtower_live(self) -> bool:
        return False

    @property
    def claims_workops_ai_editor(self) -> bool:
        return False

    @property
    def claims_library_time_travel(self) -> bool:
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
            "claims_remote_websocket": self.claims_remote_websocket,
            "claims_wss_tls": self.claims_wss_tls,
            "claims_aureleu_dispatcher_live": self.claims_aureleu_dispatcher_live,
            "claims_watchtower_live": self.claims_watchtower_live,
            "claims_workops_ai_editor": self.claims_workops_ai_editor,
            "claims_library_time_travel": self.claims_library_time_travel,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    if any(i.status is ItemStatus.BLOCKED for i in items):
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f5_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f5-front-v1-exit-seal.v1",
) -> F5ExitSeal:
    """Build the F5 exit seal from module + report presence. Read-only."""
    base = Path(reports_dir)
    items = tuple(
        SealChecklistItem(
            slice_id=sid, title=title, module=module, report=report,
            module_present=_module_present(module),
            report_present=(base / report).is_file(),
        )
        for sid, title, module, report in F5_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(surface_id=s, reason=r, future_owner=o)
        for s, r, o in F5_UNAVAILABLE
    )
    return F5ExitSeal(seal_id=seal_id, items=items, unavailable=unavailable,
                      status=_derive_status(items))
