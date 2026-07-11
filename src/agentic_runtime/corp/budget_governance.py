"""
budget_governance.py — allocation vs. spend per client / job / mandate (F7.2).

A **report, never enforcement**: the real budget cap still lives in the budget
gate + the F6.2 mandate gate (which already enforces `MandateScope.budget_cents`).
This view just composes what is already true:
  * **allocation** = `MandateScope.budget_cents` of the mandates a job references
    (resolved through the mandate registry the Corp registry holds, F7.0);
  * **spent** = the F7.1 cost attribution (`per_mandate` estimated cost);
  * **remaining** = allocation − spent (only when the allocation is bounded);
  * **deny_count** = the trace's `budget_decision` denials per mandate (F6.1).

Honesty: a mandate with no cap (`budget_cents == 0`, e.g. klijent nula's default
mandate) is **UNBOUNDED**, never a fabricated number; an unresolvable mandate is
**UNAVAILABLE** with a reason. Burn-rate / ETA **forecasting stays a declared
UNAVAILABLE seam** (later) — this view never predicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .cost import CostAttributionView

# Allocation status precedence when rolling mandates up to a job / client:
# a single "don't know" or "no cap" dominates a bounded sum (honest worst-case).
_STATUS_RANK = {"UNAVAILABLE": 0, "UNBOUNDED": 1, "AVAILABLE": 2}

_FORECASTING_SEAM = {
    "status": "UNAVAILABLE", "owner": "later",
    "reason": "burn-rate / ETA forecasting is a later seam; this view never predicts",
}


def _combine_status(statuses: list[str]) -> str:
    if not statuses:
        return "AVAILABLE"
    return min(statuses, key=lambda s: _STATUS_RANK.get(s, 2))


@dataclass(frozen=True)
class ClientBudgetView:
    """Allocation vs. spend rollup: mandate → job → client. Report, not authority."""

    available: bool
    reason: str = ""
    by_mandate: dict[str, dict] = field(default_factory=dict)
    by_job: dict[str, dict] = field(default_factory=dict)
    by_client: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def unavailable(cls, reason: str) -> "ClientBudgetView":
        return cls(available=False, reason=reason)

    @classmethod
    def build(
        cls,
        ledger: Any,
        corp_registry: Any,
        trace: Any = None,
        *,
        mandate_registry: Any = None,
    ) -> "ClientBudgetView":
        if corp_registry is None:
            return cls.unavailable("no corp registry")
        mreg = mandate_registry or getattr(corp_registry, "mandate_registry", None)
        cost = CostAttributionView.from_ledger(ledger, corp_registry, mandate_registry=mreg)
        spent_known = cost.available
        deny_counts = _deny_counts_from_trace(trace)

        by_mandate: dict[str, dict] = {}
        by_job: dict[str, dict] = {}
        by_client: dict[str, dict] = {}

        for cid in corp_registry.client_ids():
            client_entries: list[dict] = []
            for job in corp_registry.jobs_for_client(cid):
                job_entries: list[dict] = []
                for mid in job.mandate_ids:
                    entry = _mandate_entry(mid, mreg, cost, spent_known, deny_counts)
                    by_mandate.setdefault(mid, entry)
                    job_entries.append(entry)
                job_roll = _rollup(job_entries)
                job_roll.update(job_id=job.job_id, client_id=cid)
                by_job[job.job_id] = job_roll
                client_entries.append(job_roll)
            client_roll = _rollup(client_entries)
            client_roll.update(client_id=cid)
            by_client[cid] = client_roll

        return cls(available=True, by_mandate=by_mandate, by_job=by_job, by_client=by_client)

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "status": "AVAILABLE" if self.available else "UNAVAILABLE",
            "reason": self.reason,
            "by_mandate": self.by_mandate,
            "by_job": self.by_job,
            "by_client": self.by_client,
            "forecasting": dict(_FORECASTING_SEAM),
        }


def _mandate_entry(
    mid: str, mreg: Any, cost: CostAttributionView, spent_known: bool, deny_counts: dict[str, int]
) -> dict:
    spent = (float(cost.by_mandate.get(mid, {}).get("estimated_cost_cents", 0.0))
             if spent_known else None)
    deny = int(deny_counts.get(mid, 0))
    mandate = mreg.resolve(mid) if mreg is not None else None
    if mandate is None:
        return {"mandate_id": mid, "allocation_status": "UNAVAILABLE",
                "allocation_cents": None, "spent_cents": spent, "remaining_cents": None,
                "deny_count": deny, "reason": "mandate unresolved (no registry / unknown id)"}
    cap = float(getattr(mandate.scope, "budget_cents", 0.0) or 0.0)
    if cap <= 0:
        return {"mandate_id": mid, "allocation_status": "UNBOUNDED",
                "allocation_cents": None, "spent_cents": spent, "remaining_cents": None,
                "deny_count": deny, "reason": "no budget cap on mandate (inherit)"}
    remaining = (cap - spent) if spent is not None else None
    return {"mandate_id": mid, "allocation_status": "AVAILABLE",
            "allocation_cents": cap, "spent_cents": spent, "remaining_cents": remaining,
            "deny_count": deny, "reason": ""}


def _rollup(entries: list[dict]) -> dict:
    status = _combine_status([e["allocation_status"] for e in entries])
    alloc = (sum(e["allocation_cents"] or 0.0 for e in entries)
             if status == "AVAILABLE" else None)
    spents = [e["spent_cents"] for e in entries if e["spent_cents"] is not None]
    spent = sum(spents) if spents else (0.0 if entries and _spent_known(entries) else None)
    remaining = (alloc - spent) if (alloc is not None and spent is not None) else None
    return {
        "allocation_status": status,
        "allocation_cents": alloc,
        "spent_cents": spent,
        "remaining_cents": remaining,
        "deny_count": sum(int(e["deny_count"]) for e in entries),
    }


def _spent_known(entries: list[dict]) -> bool:
    # spent is known (a number, possibly 0) iff every entry carries a numeric spent.
    return all(e.get("spent_cents") is not None for e in entries)


def _deny_counts_from_trace(trace: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    if trace is None or not hasattr(trace, "replay"):
        return out
    for ev in trace.replay():
        if ev.get("kind") == "budget_decision" and ev.get("verdict") == "deny":
            mid = ev.get("mandate_id", "")
            if mid:
                out[mid] = out.get(mid, 0) + 1
    return out


__all__ = ["ClientBudgetView"]
