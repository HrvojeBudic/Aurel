"""
corp_read_model.py — the CORP surface read-model (F7.5).

The Business Plane's home projection: a **portfolio tree** (client → job →
mandates → runs, with a status overlay) and a **task-runtime feed** (the live
chronological stream of transitions / approvals / budget decisions, filterable by
job). Both are **pure projections over the trace** + the Corp registry (F7.0) +
the cost view (F7.1) — zero writes, no new store.

Doctrine (honest):
  * run → job is resolved through the `mandate_id` each trace record already
    carries (F6.1) → the mandate's job (F7.0). A run whose mandate maps to no job
    is reported as **unassigned** — the link is never invented.
  * cost comes from the live budget ledger (F7.1); with no ledger it is honestly
    UNAVAILABLE, never a fabricated zero.
  * alerts (F7.3 Watchtower) and budget governance (F7.2) are **declared
    UNAVAILABLE seams** with their owner — not yet built, never over-claimed.
"""
from __future__ import annotations

from typing import Any

from ..corp import (
    ClientBudgetView,
    CostAttributionView,
    corp_registry_from_trace,
    derive_alerts,
    live_feed,
    watchtower_flag_enabled,
)
from ..corp.cost import _mandate_to_job_map

# Alerts are live when AUREL_WATCHTOWER is on (F7.3); budget governance is built
# (F7.2 — a pure allocation-vs-spend projection). Forecasting stays UNAVAILABLE.
CLAIMS_ALERTS_LIVE = False
CLAIMS_BUDGET_GOVERNANCE_LIVE = True

_FEED_KINDS = ("runtime_status_transition", "approval_receipt", "budget_decision")


class CorpReadModel:
    """Portfolio tree + task-runtime feed over the trace + Corp registry (zero writes)."""

    def __init__(self, trace: Any, corp_registry: Any, *, budget: Any = None) -> None:
        self._trace = trace
        self._corp = corp_registry
        self._budget = budget

    @staticmethod
    def from_runtime(runtime: Any, *, corp_registry: Any = None) -> "CorpReadModel":
        inner = getattr(runtime, "runtime", runtime)
        reg = (corp_registry
               or getattr(inner, "corp_registry", None)
               or corp_registry_from_trace(inner.trace))
        return CorpReadModel(inner.trace, reg, budget=getattr(inner, "budget", None))

    # -- run status + mandate (trace projection) ------------------------------- #
    def _runs_by_id(self) -> dict[str, dict]:
        """Latest status transition per run, carrying the run's mandate_id."""
        runs: dict[str, dict] = {}
        for ev in self._trace.replay():
            if ev.get("kind") != "runtime_status_transition":
                continue
            rid = str(ev.get("run_id", ""))
            entry = runs.setdefault(rid, {
                "run_id": rid, "status": "", "reason_code": "",
                "issuer": "", "mandate_id": "", "transitions": 0})
            entry["status"] = ev.get("to", "")
            entry["reason_code"] = ev.get("reason_code", "")
            entry["issuer"] = ev.get("issuer", "")
            if ev.get("mandate_id"):
                entry["mandate_id"] = ev.get("mandate_id")
            entry["transitions"] += 1
        return runs

    # -- portfolio tree -------------------------------------------------------- #
    def portfolio_view(self) -> dict:
        runs = self._runs_by_id()
        mandate_to_job = _mandate_to_job_map(self._corp)
        cost = CostAttributionView.from_ledger(self._budget, self._corp)

        runs_by_job: dict[str, list[dict]] = {}
        unassigned: list[dict] = []
        for rid in sorted(runs):
            entry = runs[rid]
            job = mandate_to_job.get(entry["mandate_id"]) if entry["mandate_id"] else None
            if job is None:
                unassigned.append(entry)
            else:
                runs_by_job.setdefault(job.job_id, []).append(entry)

        clients: list[dict] = []
        for cid in self._corp.client_ids():
            client = self._corp.resolve_client(cid)
            jobs_out: list[dict] = []
            for job in self._corp.jobs_for_client(cid):
                job_cost = (cost.by_job.get(job.job_id, {}).get("metrics")
                            if cost.available else None)
                jobs_out.append({
                    "job_id": job.job_id,
                    "title": job.title,
                    "status": job.status.value,
                    "mandate_ids": list(job.mandate_ids),
                    "repos": list(job.repos),
                    "runs": runs_by_job.get(job.job_id, []),
                    "cost": job_cost,
                })
            clients.append({
                "client_id": cid,
                "name": client.name if client else "",
                "jobs": jobs_out,
                "cost": cost.by_client.get(cid) if cost.available else None,
            })

        return {
            "clients": clients,
            "unassigned": unassigned,
            "cost": self._cost_status(cost),
            "alerts": self._alerts(),
            "budget_governance": self._budget_governance(),
            "claims_alerts_live": watchtower_flag_enabled(),
            "claims_budget_governance_live": CLAIMS_BUDGET_GOVERNANCE_LIVE,
        }

    # -- task-runtime feed ----------------------------------------------------- #
    def runtime_feed(self, job_id: str = "") -> dict:
        """The chronological trace stream, optionally filtered to one job's mandates."""
        mandates: set[str] = set()
        if job_id:
            job = self._corp.resolve_job(job_id)
            if job is None:
                return {"job": job_id, "available": False,
                        "reason": f"unknown job {job_id!r}", "events": []}
            mandates = set(job.mandate_ids)

        events: list[dict] = []
        for ev in self._trace.replay():
            kind = ev.get("kind")
            if kind not in _FEED_KINDS:
                continue
            mid = ev.get("mandate_id", "")
            if mandates and mid not in mandates:
                continue
            events.append(_normalize_feed_event(kind, ev))
        return {"job": job_id, "available": True, "events": events}

    # -- declared seams / honesty helpers -------------------------------------- #
    @staticmethod
    def _cost_status(cost: CostAttributionView) -> dict:
        if not cost.available:
            return {"status": "UNAVAILABLE", "reason": cost.reason}
        return {"status": "AVAILABLE", "unattributed": cost.unattributed}

    def _alerts(self) -> dict:
        """Live Watchtower alert count + feed when AUREL_WATCHTOWER is on (F7.3);
        else the byte-identical UNAVAILABLE seam."""
        if not watchtower_flag_enabled():
            return {"status": "UNAVAILABLE", "owner": "F7.3",
                    "reason": "Watchtower alerts are F7.3; not built yet", "count": 0}
        return live_feed(derive_alerts(self._trace, self._budget, self._corp))

    def _budget_governance(self) -> dict:
        """Live allocation-vs-spend view (F7.2). Report, never enforcement;
        forecasting stays a declared UNAVAILABLE seam inside the view."""
        return ClientBudgetView.build(self._budget, self._corp, self._trace).to_dict()


def _normalize_feed_event(kind: str, ev: dict) -> dict:
    """A compact, uniform feed entry — the fields common to the surface."""
    out = {"kind": kind, "issuer": ev.get("issuer", ""),
           "mandate_id": ev.get("mandate_id", "")}
    if kind == "runtime_status_transition":
        out.update(run_id=ev.get("run_id", ""), status=ev.get("to", ""),
                   reason_code=ev.get("reason_code", ""))
    elif kind == "approval_receipt":
        out.update(tool=ev.get("tool", ""), outcome=ev.get("outcome", ""),
                   risk_class=ev.get("risk_class", ""))
    elif kind == "budget_decision":
        out.update(metric=ev.get("metric", ""), verdict=ev.get("verdict", ""),
                   used=ev.get("used", 0.0), limit=ev.get("limit", 0.0))
    return out
