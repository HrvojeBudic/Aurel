"""
workbench.py — the Approval Workbench read-model (F7.8).

The F5.2 inbox gives the operator a *pending list*; the workbench gives them the
*context to decide* — each pending item enriched with its mandate summary, the
client/job it belongs to (F7.0), the mandate's budget state (F7.1/F7.2), the job's
open risks (F7.7), and the decision history for that tool (from the trace audit).

Doctrine (structural):
  * this is a **read-only composition** — it adds no decision path. The decision
    still goes only through the F5.2 two-phase `decide`; the inbox is untouched
    beyond carrying the mandate_id the command was submitted under.
  * pending stays honest operational state (`pending_source` discipline, F5.5):
    without an injected inbox there are no pending items, only the trace-derived
    tool history.
  * context with no source is **UNAVAILABLE with a reason**, never fabricated.

This slice flips the `full_approval_workbench` seam declared in F6.
"""
from __future__ import annotations

from typing import Any

from ..corp import ClientBudgetView, RiskRegisterProjection, corp_registry_from_trace
from ..corp.cost import _mandate_to_job_map
from .approval_inbox import ApprovalInbox

# The full operator approval workbench is built (F7.8, a read-only composition).
CLAIMS_FULL_APPROVAL_WORKBENCH = True

_RISK_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "trivial": 4}


class ApprovalWorkbenchReadModel:
    """Pending approvals enriched with mandate / client / budget / risk / history."""

    def __init__(self, trace: Any, corp_registry: Any, *, budget: Any = None,
                 inbox: Any = None) -> None:
        self._trace = trace
        self._corp = corp_registry
        self._budget = budget
        self._inbox = inbox
        # lazily-built shared context (one per read)
        self._mandate_to_job_cache: dict[str, Any] | None = None
        self._budget_view: ClientBudgetView | None = None
        self._risk_proj: RiskRegisterProjection | None = None

    @staticmethod
    def from_runtime(runtime: Any, *, inbox: Any = None,
                     corp_registry: Any = None) -> "ApprovalWorkbenchReadModel":
        inner = getattr(runtime, "runtime", runtime)
        reg = (corp_registry
               or getattr(inner, "corp_registry", None)
               or corp_registry_from_trace(inner.trace))
        return ApprovalWorkbenchReadModel(
            inner.trace, reg, budget=getattr(inner, "budget", None), inbox=inbox)

    # -- shared context (built once) ------------------------------------------- #
    def _mandate_to_job(self) -> dict[str, Any]:
        if self._mandate_to_job_cache is None:
            self._mandate_to_job_cache = _mandate_to_job_map(self._corp)
        return self._mandate_to_job_cache

    def _budgets(self) -> ClientBudgetView:
        if self._budget_view is None:
            self._budget_view = ClientBudgetView.build(self._budget, self._corp, self._trace)
        return self._budget_view

    def _risks(self) -> RiskRegisterProjection:
        if self._risk_proj is None:
            self._risk_proj = RiskRegisterProjection.from_trace(self._trace)
        return self._risk_proj

    # -- enrichment ------------------------------------------------------------ #
    def _mandate_summary(self, mandate_id: str) -> dict:
        mreg = getattr(self._corp, "mandate_registry", None) if self._corp else None
        if not mandate_id or mreg is None:
            return {"status": "UNAVAILABLE", "reason": "no mandate / mandate registry"}
        mandate = mreg.resolve(mandate_id)
        if mandate is None:
            return {"status": "UNAVAILABLE", "reason": f"unknown mandate {mandate_id!r}"}
        scope = mandate.scope
        return {"status": "AVAILABLE", "paths": list(scope.paths),
                "allowed_tools": list(scope.allowed_tools), "max_risk": scope.max_risk.value,
                "budget_cents": scope.budget_cents, "client_id": scope.client_id}

    def _attribution(self, mandate_id: str) -> dict:
        job = self._mandate_to_job().get(mandate_id) if mandate_id else None
        if job is None:
            return {"status": "UNAVAILABLE", "reason": "mandate maps to no job"}
        return {"status": "AVAILABLE", "job_id": job.job_id, "client_id": job.client_id}

    def _budget_context(self, mandate_id: str) -> dict:
        view = self._budgets()
        if not view.available:
            return {"status": "UNAVAILABLE", "reason": view.reason}
        entry = view.by_mandate.get(mandate_id)
        if entry is None:
            return {"status": "UNAVAILABLE", "reason": "mandate not in budget view"}
        return {"status": "AVAILABLE",
                **{k: entry[k] for k in ("allocation_status", "allocation_cents",
                                          "spent_cents", "remaining_cents", "deny_count")}}

    def _risks_for(self, mandate_id: str) -> list[dict]:
        job = self._mandate_to_job().get(mandate_id) if mandate_id else None
        if job is None:
            return []
        return [r.to_dict() for r in self._risks().active() if r.job_id == job.job_id]

    def _history_for(self, tool: str) -> list[dict]:
        return [a for a in ApprovalInbox.audit_from_trace(self._trace)
                if a.get("tool") == tool]

    def _enrich(self, item: dict) -> dict:
        mid = item.get("mandate_id", "")
        return {
            **item,
            "mandate": self._mandate_summary(mid),
            "attribution": self._attribution(mid),
            "budget": self._budget_context(mid),
            "risks": self._risks_for(mid),
            "history": self._history_for(item.get("tool", "")),
        }

    def items(self) -> list[dict]:
        if self._inbox is None:
            return []
        enriched = [self._enrich(p) for p in self._inbox.pending()]
        enriched.sort(key=lambda it: (_RISK_RANK.get(it.get("risk", ""), 9),
                                      it.get("request_id", "")))
        return enriched

    def tool_history(self) -> dict:
        """Decision counts per tool, from the trace audit (available without an inbox)."""
        counts: dict[str, dict[str, int]] = {}
        for a in ApprovalInbox.audit_from_trace(self._trace):
            tool = str(a.get("tool", ""))
            bucket = counts.setdefault(tool, {})
            outcome = str(a.get("outcome", ""))
            bucket[outcome] = bucket.get(outcome, 0) + 1
        return {t: counts[t] for t in sorted(counts)}

    def to_dict(self) -> dict:
        return {
            "items": self.items(),
            "pending_source": "inbox" if self._inbox is not None else "unavailable",
            "tool_history": self.tool_history(),
            "claims_full_workbench": CLAIMS_FULL_APPROVAL_WORKBENCH,
        }
