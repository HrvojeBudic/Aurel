"""
f8_seal.py — F8.6 derived exit seal for the Time Plane phase.

Derived, never declared: F8 is SEALED only when every slice (F8.0→F8.6) has both
an importable module and a present report. F8 **flips** the F7-carried seam
``library_time_travel`` to live (F8.4). Deferred surfaces stay explicit in the
UNAVAILABLE registry (Chronos UI forge → F9; policy editor / threat detection /
automated succession restore → LATER; distributed replay / HSM ceremony → SCI-FI).
Read-only.
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


F8_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("F8.0", "Chronos replay / fork / diff + CLI",
     "agentic_runtime.chronos", "AUREL_F8_0_CHRONOS_FOUNDATION.md"),
    ("F8.1", "Irreversibility gate: fork-before-irreversible evidence",
     "agentic_runtime.chronos.irreversibility", "AUREL_F8_1_IRREVERSIBILITY_GATE.md"),
    ("F8.2", "System surface: audit log + usage read-models",
     "agentic_runtime.front_server.system_read_model", "AUREL_F8_2_SYSTEM_AUDIT_USAGE.md"),
    ("F8.3", "System: model-routing + policy browser + archive",
     "agentic_runtime.front_server.read_models", "AUREL_F8_3_SYSTEM_MODEL_POLICY_ARCHIVE.md"),
    ("F8.4", "Library time-travel: as-of via memory_asof",
     "agentic_runtime.front_server.library", "AUREL_F8_4_LIBRARY_TIME_TRAVEL.md"),
    ("F8.5", "Succession drill + System React panel",
     "agentic_runtime.succession_drill", "AUREL_F8_5_SUCCESSION_DRILL_SYSTEM_PANEL.md"),
    ("F8.6", "derived exit seal + projection + CLI",
     "agentic_runtime.f8_seal", "AUREL_F8_6_F8_EXIT_SEAL.md"),
)

F8_FLIPPED_FROM_F7: tuple[tuple[str, str], ...] = (
    ("library_time_travel", "F8.4"),
)

F8_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("chronos_ui_forge",
     "Lab.Simulation Chronos UI forge is not built; CLI replay/fork/diff only",
     "F9"),
    ("policy_editor",
     "policy card browser is read-only; no governed policy editor",
     "LATER"),
    ("threat_detection_engine",
     "automated threat detection is not built",
     "LATER"),
    ("automated_succession_restore",
     "succession drill is semi-automatic; fully automated restore is not built",
     "LATER"),
    ("distributed_replay",
     "distributed / parallel replay across nodes is SCI-FI",
     "parked (SCI-FI)"),
    ("hsm_key_ceremony",
     "HSM key ceremony is SCI-FI",
     "parked (SCI-FI)"),
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
class F8ExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    flipped_from_f7: tuple[tuple[str, str], ...]
    status: SealStatus

    @property
    def sealed(self) -> bool:
        return self.status is SealStatus.SEALED

    @property
    def claims_library_time_travel_live(self) -> bool:
        return self.sealed

    @property
    def claims_distributed_replay(self) -> bool:
        return False

    @property
    def claims_hsm_key_ceremony(self) -> bool:
        return False

    @property
    def claims_chronos_ui_forge(self) -> bool:
        return False

    @property
    def claims_threat_detection_engine(self) -> bool:
        return False

    @property
    def claims_policy_editor(self) -> bool:
        return False

    @property
    def claims_automated_succession_restore(self) -> bool:
        return False

    def to_dict(self) -> dict:
        return {
            "seal_id": self.seal_id,
            "status": self.status.value,
            "sealed": self.sealed,
            "passed": sum(1 for i in self.items if i.status is ItemStatus.PASSED),
            "blocked": sum(1 for i in self.items if i.status is ItemStatus.BLOCKED),
            "items": [i.to_dict() for i in self.items],
            "flipped_from_f7": [{"seam": s, "owner": o} for s, o in self.flipped_from_f7],
            "unavailable": [u.to_dict() for u in self.unavailable],
            "claims_library_time_travel_live": self.claims_library_time_travel_live,
            "claims_distributed_replay": self.claims_distributed_replay,
            "claims_hsm_key_ceremony": self.claims_hsm_key_ceremony,
            "claims_chronos_ui_forge": self.claims_chronos_ui_forge,
            "claims_threat_detection_engine": self.claims_threat_detection_engine,
            "claims_policy_editor": self.claims_policy_editor,
            "claims_automated_succession_restore": self.claims_automated_succession_restore,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    if any(i.status is ItemStatus.BLOCKED for i in items):
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f8_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f8-time-plane-exit-seal.v1",
) -> F8ExitSeal:
    """Build the F8 exit seal from module + report presence. Read-only."""
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
        for sid, title, module, report in F8_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(surface_id=s, reason=r, future_owner=o)
        for s, r, o in F8_UNAVAILABLE
    )
    return F8ExitSeal(
        seal_id=seal_id,
        items=items,
        unavailable=unavailable,
        flipped_from_f7=F8_FLIPPED_FROM_F7,
        status=_derive_status(items),
    )


__all__ = [
    "F8ExitSeal",
    "F8_SLICES",
    "F8_UNAVAILABLE",
    "ItemStatus",
    "SealStatus",
    "build_f8_exit_seal",
]
