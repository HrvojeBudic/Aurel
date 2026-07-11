"""
f7_projection.py — the F7.10 north-star run projection (klijent nula).

A single read-only view composing the whole F7 Business Plane from one runtime's
trace + Corp registry: the portfolio tree, cost attribution, budget governance,
the Watchtower feed, the Evidence-Vault Output Passport, the Risk Register, and the
Reflex Flywheel KPIs. It proves the klijent-nula scenario (§7) is provably
replayable from the trace — every field is a pure projection, zero writes.
"""
from __future__ import annotations

from typing import Any

from .corp import (
    CLIENT_ZERO_ID,
    JOB_ZERO_ID,
    ClientBudgetView,
    CostAttributionView,
    EvidenceVaultQuery,
    ReflexFlywheelView,
    RiskRegisterProjection,
    default_corp_registry,
    derive_alerts,
    live_feed,
    watchtower_flag_enabled,
)
from .front_server.corp_read_model import CorpReadModel


class F7RunProjection:
    """The full klijent-nula Business Plane run, composed from the trace."""

    def __init__(self, runtime: Any, *, corp_registry: Any = None) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self._corp = corp_registry or default_corp_registry()

    def _watchtower(self, trace: Any, budget: Any) -> dict:
        if not watchtower_flag_enabled():
            return {"status": "UNAVAILABLE", "owner": "F7.3",
                    "reason": "Watchtower flag off", "alerts": []}
        return live_feed(derive_alerts(trace, budget, self._corp))

    def to_dict(self) -> dict:
        trace = self._inner.trace
        budget = getattr(self._inner, "budget", None)
        return {
            "client_zero": {"client_id": CLIENT_ZERO_ID, "job_id": JOB_ZERO_ID},
            "portfolio": CorpReadModel(trace, self._corp, budget=budget).portfolio_view(),
            "cost": CostAttributionView.from_ledger(budget, self._corp).to_dict(),
            "budget_governance": ClientBudgetView.build(budget, self._corp, trace).to_dict(),
            "watchtower": self._watchtower(trace, budget),
            "evidence_passport": EvidenceVaultQuery(trace, self._corp).export_receipt_bundle(
                job_id=JOB_ZERO_ID),
            "risks": RiskRegisterProjection.from_trace(trace).to_dict(),
            "kpi": ReflexFlywheelView.build(
                skills=getattr(self._inner, "skills", None), ledger=budget).to_dict(),
            "replayable": True,   # every field above is a pure trace/registry projection
        }
