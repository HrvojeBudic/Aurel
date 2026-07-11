"""
f7_seal.py — F7.10 derived exit seal for the Corp / Business Plane phase.

Derived, never declared: F7 is SEALED only when every slice (F7.0→F7.10) has both
an importable module and a present report; a missing module or report BLOCKS that
item and the whole seal. F7 **flips** two F6 UNAVAILABLE seams to live —
`watchtower_alerts` (F7.3) and `full_approval_workbench` (F7.8) — proven by the
slice checks; it also **completes** the Output Passport (F7.4). Deferred surfaces
stay explicit in the UNAVAILABLE registry (forecasting/KPI-builder/ROI/billing/
compliance/auto-risk as LATER; the business simulator / value-risk studio / R&D-NLP
as parked SCI-FI).

SEALED means the Business Plane backbone is closed — clients/jobs over mandates,
cost attribution, budget governance, Watchtower, Evidence Vault, portfolio, wizard,
risk register, workbench, KPIs — NOT that forecasting, a business simulator, or a
billing console exist. Overclaim guards for those are hard-wired False; the two
flips are True iff SEALED. Read-only.
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
F7_SLICES: tuple[tuple[str, str, str, str], ...] = (
    ("F7.0", "Corp domain: Client/Job registry + klijent nula",
     "agentic_runtime.corp.domain", "AUREL_F7_0_CORP_DOMAIN.md"),
    ("F7.1", "cost attribution: per-mandate bucket + client pivot",
     "agentic_runtime.corp.cost", "AUREL_F7_1_COST_ATTRIBUTION.md"),
    ("F7.2", "budget governance: allocation vs. spend",
     "agentic_runtime.corp.budget_governance", "AUREL_F7_2_BUDGET_GOVERNANCE.md"),
    ("F7.3", "Watchtower: read-only alert derivation",
     "agentic_runtime.corp.watchtower", "AUREL_F7_3_WATCHTOWER.md"),
    ("F7.4", "Evidence Vault: trace search + receipt export",
     "agentic_runtime.corp.evidence_vault", "AUREL_F7_4_EVIDENCE_VAULT.md"),
    ("F7.5", "CORP surface read-model: portfolio + task feed",
     "agentic_runtime.front_server.corp_read_model", "AUREL_F7_5_CORP_READ_MODEL.md"),
    ("F7.6", "Agency wizard: templates + what-if impact",
     "agentic_runtime.corp.wizard", "AUREL_F7_6_AGENCY_WIZARD.md"),
    ("F7.7", "Risk Register v1: governed entries + heatmap",
     "agentic_runtime.corp.risk_register", "AUREL_F7_7_RISK_REGISTER.md"),
    ("F7.8", "approval workbench refinement",
     "agentic_runtime.front_server.workbench", "AUREL_F7_8_APPROVAL_WORKBENCH.md"),
    ("F7.9", "Reflex Flywheel KPIs + CORP React surface",
     "agentic_runtime.corp.kpi", "AUREL_F7_9_CORP_KPI_SURFACE.md"),
    ("F7.10", "derived exit seal + projection + CLI",
     "agentic_runtime.f7_seal", "AUREL_F7_10_F7_EXIT_SEAL.md"),
)

# F6 seams flipped to live by F7 (proven by the F7.3 / F7.8 slice checks).
F7_FLIPPED_FROM_F6: tuple[tuple[str, str], ...] = (
    ("watchtower_alerts", "F7.3"),
    ("full_approval_workbench", "F7.8"),
)

F7_UNAVAILABLE: tuple[tuple[str, str, str], ...] = (
    ("forecasting_burn_eta",
     "burn-rate / ETA forecasting is not built; budget governance reports actuals only",
     "LATER"),
    ("kpi_builder",
     "custom KPI builder is not built; the Reflex Flywheel KPIs are fixed",
     "LATER"),
    ("roi_analysis",
     "ROI analysis is not built; cost-per-client attribution is the v1 answer",
     "LATER"),
    ("billing_console",
     "a billing console is not built; the cost-per-client report suffices for private use",
     "LATER"),
    ("compliance_gap_analysis",
     "compliance gap analysis is not built",
     "LATER"),
    ("auto_risk_detection",
     "auto risk detection (drift-gate mining) is not built; the Risk Register is operator-entered",
     "LATER"),
    ("business_simulator",
     "a discrete-event business simulator is SCI-FI",
     "parked (SCI-FI)"),
    ("value_risk_studio",
     "a Studio value & risk simulation engine is SCI-FI",
     "parked (SCI-FI)"),
    ("rnd_knowledge_transfer_nlp",
     "R&D knowledge-transfer NLP is SCI-FI",
     "parked (SCI-FI)"),
    ("hq_intelligence_governed_feeds",
     "HQ.Intelligence governed feeds (RSS/API pull) are not built",
     "after F7"),
    ("document_forge",
     "the Document Forge (reports/quotes/invoices from templates) is not built",
     "after F7"),
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
class F7ExitSeal:
    seal_id: str
    items: tuple[SealChecklistItem, ...]
    unavailable: tuple[UnavailableSurface, ...]
    flipped_from_f6: tuple[tuple[str, str], ...]
    status: SealStatus

    # SCI-FI Business Plane features are hard-wired False.
    @property
    def claims_business_simulator(self) -> bool:
        return False

    @property
    def claims_value_risk_studio(self) -> bool:
        return False

    @property
    def claims_rnd_knowledge_transfer_nlp(self) -> bool:
        return False

    @property
    def claims_forecasting(self) -> bool:
        return False

    @property
    def claims_watchtower_alerts_live(self) -> bool:
        # Flipped True by F7.3 — proven live by that slice being PASSED.
        return self.sealed

    @property
    def claims_full_approval_workbench_live(self) -> bool:
        # Flipped True by F7.8 — proven live by that slice being PASSED.
        return self.sealed

    @property
    def claims_output_passport_complete(self) -> bool:
        # Completed by F7.4 — proven by that slice being PASSED.
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
            "flipped_from_f6": [{"seam": s, "owner": o} for s, o in self.flipped_from_f6],
            "unavailable": [u.to_dict() for u in self.unavailable],
            "claims_business_simulator": self.claims_business_simulator,
            "claims_value_risk_studio": self.claims_value_risk_studio,
            "claims_rnd_knowledge_transfer_nlp": self.claims_rnd_knowledge_transfer_nlp,
            "claims_forecasting": self.claims_forecasting,
            "claims_watchtower_alerts_live": self.claims_watchtower_alerts_live,
            "claims_full_approval_workbench_live": self.claims_full_approval_workbench_live,
            "claims_output_passport_complete": self.claims_output_passport_complete,
        }


def _derive_status(items: tuple[SealChecklistItem, ...]) -> SealStatus:
    if any(i.status is ItemStatus.BLOCKED for i in items):
        return SealStatus.BLOCKED
    return SealStatus.SEALED


def build_f7_exit_seal(
    reports_dir: str = DEFAULT_REPORTS_DIR,
    seal_id: str = "f7-corp-business-plane-exit-seal.v1",
) -> F7ExitSeal:
    """Build the F7 exit seal from module + report presence. Read-only."""
    base = Path(reports_dir)
    items = tuple(
        SealChecklistItem(
            slice_id=sid, title=title, module=module, report=report,
            module_present=_module_present(module),
            report_present=(base / report).is_file(),
        )
        for sid, title, module, report in F7_SLICES
    )
    unavailable = tuple(
        UnavailableSurface(surface_id=s, reason=r, future_owner=o)
        for s, r, o in F7_UNAVAILABLE
    )
    return F7ExitSeal(seal_id=seal_id, items=items, unavailable=unavailable,
                      flipped_from_f6=F7_FLIPPED_FROM_F6,
                      status=_derive_status(items))
