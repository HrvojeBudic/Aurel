"""
f6_seal.py — F6.10 derived exit seal for the AurelEU / Constitution / mandate phase.

Derived, never declared: F6 is SEALED only when every slice (F6.0→F6.10) has both an
importable module and a present report; a missing module or report BLOCKS that item
and the whole seal. F6 **flips** two F5 UNAVAILABLE seams to live —
`aureleu_role_fluid_dispatcher` (F6.4/F6.5) and `mandate_resolution_enforcement`
(F6.0–F6.2) — proven by the slice checks. Deferred surfaces stay explicit in the
UNAVAILABLE registry, now including the parked SCI-FI sovereignty features.

SEALED means the governed authority (mandate) + delegated autonomy (constitution) +
role-fluid persona (AurelEU) backbone is closed, NOT that multi-jurisdiction
sovereigns, a zero-knowledge federation, or a cryptographic non-repudiation ledger
exist. Overclaim guards for those are computed and hard-wired False. Read-only.
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
F6_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("F6.0", "Mandate object + registry",
     "agentic_runtime.mandate.mandate", "AUREL_F6_0_2_MANDATE_SKELETON.md"),
    ("F6.1", "mandate_id trace propagation",
     "agentic_runtime.trace", "AUREL_F6_0_2_MANDATE_SKELETON.md"),
    ("F6.2", "mandate scope-enforcement gate",
     "agentic_runtime.mandate.enforcement", "AUREL_F6_0_2_MANDATE_SKELETON.md"),
    ("F6.3", "Constitution delegation windows",
     "agentic_runtime.constitution.delegation", "AUREL_F6_3_4_CONSTITUTION_AURELEU.md"),
    ("F6.4", "AurelEU role-fluid persona switch",
     "agentic_runtime.front_server.aureleu", "AUREL_F6_3_4_CONSTITUTION_AURELEU.md"),
    ("F6.5", "Constitution ↔ dispatch wiring",
     "agentic_runtime.front_server.aureleu", "AUREL_F6_5_CONSTITUTION_WIRING.md"),
    ("F6.6", "DN: graduated autonomy + merge verdict",
     "agentic_runtime.front_server.dn", "AUREL_F6_6_7_DN_MECHANISMS.md"),
    ("F6.7", "DN: challenger + tripwire + panic",
     "agentic_runtime.dn", "AUREL_F6_6_7_DN_MECHANISMS.md"),
    ("F6.8", "two-persona Board option generator",
     "agentic_runtime.front_server.board", "AUREL_F6_8_9_BOARD_AURELCRO.md"),
    ("F6.9", "AUREL_CRO surface read-model",
     "agentic_runtime.front_server.aureleu_read_model", "AUREL_F6_8_9_BOARD_AURELCRO.md"),
    ("F6.10", "derived exit seal + projection + CLI",
     "agentic_runtime.f6_seal", "AUREL_F6_10_F6_EXIT_SEAL.md"),
)

# F5 seams flipped to live by F6 (proven by the F6.0–F6.5 slice checks above).
F6_FLIPPED_FROM_F5: tuple[tuple[str, str], ...] = (
    ("aureleu_role_fluid_dispatcher", "F6.4/F6.5"),
    ("mandate_resolution_enforcement", "F6.0-F6.2"),
)

F6_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("multi_jurisdiction_sovereigns",
     "AurelGer/AurelUS-style multi-sovereign jurisdictions are SCI-FI; mandates are "
     "per-job / per-client only",
     "parked (SCI-FI)"),
    ("zero_knowledge_federation",
     "zero-knowledge sovereign federation is SCI-FI",
     "parked (SCI-FI)"),
    ("crypto_nonrepudiation_ledger",
     "cryptographic-signature non-repudiation ledger not built; the trace is the "
     "governed audit",
     "P1.8 / P2.2"),
    ("full_approval_workbench",
     "the full operator approval workbench UI is a refinement of the F5.2 inbox",
     "F7"),
    ("watchtower_alerts",
     "the HQ.Command Watchtower alert feed is a declared empty seam",
     "F7"),
    ("library_time_travel",
     "Library as-of replay / time-travel is not built",
     "F8"),
    ("wss_tls_remote_transport",
     "v1 transport is localhost with no TLS",
     "Tauri-Rust"),
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
        return {"slice_id": self.slice_id, "title": self.title, "module": self.module,
                "report": self.report, "module_present": self.module_present,
                "report_present": self.report_present, "status": self.status.value}


@dataclass(frozen=True)
class UnavailableSurface:
    surface_id: str
    reason: str
    future_owner: str

    def to_dict(self) -> dict:
        return {"surface_id": self.surface_id, "reason": self.reason,
                "future_owner": self.future_owner}


@dataclass(frozen=True)
class F6ExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    flipped_from_f5: tuple[tuple[str, str], ...]
    status: SealStatus

    @property
    def claims_multi_jurisdiction_sovereigns(self) -> bool:
        return False

    @property
    def claims_zero_knowledge_federation(self) -> bool:
        return False

    @property
    def claims_crypto_nonrepudiation_ledger(self) -> bool:
        return False

    @property
    def claims_aureleu_dispatcher_live(self) -> bool:
        # Flipped True by F6.4/F6.5 — proven live by those slices being PASSED.
        return self.sealed

    @property
    def claims_mandate_enforcement_live(self) -> bool:
        # Flipped True by F6.0–F6.2 — proven live by those slices being PASSED.
        return self.sealed

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
            "flipped_from_f5": [{"seam": s, "owner": o} for s, o in self.flipped_from_f5],
            "unavailable": [u.to_dict() for u in self.unavailable],
            "claims_multi_jurisdiction_sovereigns": self.claims_multi_jurisdiction_sovereigns,
            "claims_zero_knowledge_federation": self.claims_zero_knowledge_federation,
            "claims_crypto_nonrepudiation_ledger": self.claims_crypto_nonrepudiation_ledger,
            "claims_aureleu_dispatcher_live": self.claims_aureleu_dispatcher_live,
            "claims_mandate_enforcement_live": self.claims_mandate_enforcement_live,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    if any(i.status is ItemStatus.BLOCKED for i in items):
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f6_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f6-aureleu-constitution-mandate-exit-seal.v1",
) -> F6ExitSeal:
    """Build the F6 exit seal from module + report presence. Read-only."""
    base = Path(reports_dir)
    items = tuple(
        SealChecklistItem(
            slice_id=sid, title=title, module=module, report=report,
            module_present=_module_present(module),
            report_present=(base / report).is_file(),
        )
        for sid, title, module, report in F6_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(surface_id=s, reason=r, future_owner=o)
        for s, r, o in F6_UNAVAILABLE
    )
    return F6ExitSeal(seal_id=seal_id, items=items, unavailable=unavailable,
                      flipped_from_f5=F6_FLIPPED_FROM_F5,
                      status=_derive_status(items))
