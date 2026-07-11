"""
cost.py — Cost attribution: mandate → job → client (F7.1).

The budget ledger already counts everything per run; F6.1 already carries a
`mandate_id` on every budget-decision trace record; F7.0 gives clients + jobs
that reference mandates. F7.1 is the **pivot** that turns those facts into a
business answer: *what did this client / this job cost?*

Doctrine: attribution is a **report, never a verdict**. It reads the ledger's
additive `per_mandate` bucket (populated only while a mandate context is bound,
so the flag-off / no-mandate world is byte-identical) and rolls it up through the
Corp registry (job → client). A mandate no job references is reported honestly as
`unattributed`, never silently dropped or invented. With no ledger the view is
`UNAVAILABLE` with a reason (F5.5 discipline), never a fabricated zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# The metric keys a per-mandate bucket carries (mirrors budget.BudgetLedger).
_METRIC_KEYS = (
    "commands",
    "tool_calls",
    "sandbox_executions",
    "memory_writes",
    "llm_calls",
    "estimated_tokens",
    "estimated_cost_cents",
    "substantiated_charges",
    "estimate_only_charges",
)


def _zero_metrics() -> dict[str, float]:
    return {k: 0.0 for k in _METRIC_KEYS}


def _add_into(acc: dict[str, float], src: dict[str, Any]) -> None:
    for k in _METRIC_KEYS:
        acc[k] = acc.get(k, 0.0) + float(src.get(k, 0) or 0)


@dataclass(frozen=True)
class CostAttributionView:
    """A read-only rollup of cost by mandate → job → client. Report, not authority."""

    available: bool
    reason: str = ""
    by_mandate: dict[str, dict[str, float]] = field(default_factory=dict)
    by_job: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_client: dict[str, dict[str, float]] = field(default_factory=dict)
    unattributed: dict[str, float] = field(default_factory=_zero_metrics)

    @classmethod
    def unavailable(cls, reason: str) -> "CostAttributionView":
        return cls(available=False, reason=reason)

    @classmethod
    def from_ledger(
        cls,
        ledger: Any,
        corp_registry: Any = None,
        *,
        mandate_registry: Any = None,
    ) -> "CostAttributionView":
        """Pivot the ledger's `per_mandate` bucket up through the Corp registry.

        `corp_registry` maps mandate → job → client; when it is absent, cost is
        reported per mandate only (everything `unattributed`, honestly). A mandate
        no job references is `unattributed`, never dropped.
        """
        if ledger is None:
            return cls.unavailable("no budget ledger bound")
        per_mandate: dict[str, dict[str, Any]] = dict(getattr(ledger, "per_mandate", {}) or {})

        by_mandate: dict[str, dict[str, float]] = {}
        for mid in sorted(per_mandate):
            metrics = _zero_metrics()
            _add_into(metrics, per_mandate[mid])
            by_mandate[mid] = metrics

        mandate_to_job = _mandate_to_job_map(corp_registry)

        by_job: dict[str, dict[str, Any]] = {}
        by_client: dict[str, dict[str, float]] = {}
        unattributed = _zero_metrics()

        for mid in sorted(by_mandate):
            metrics = by_mandate[mid]
            job = mandate_to_job.get(mid)
            if job is None:
                _add_into(unattributed, metrics)
                continue
            slot = by_job.setdefault(
                job.job_id, {"client_id": job.client_id, "metrics": _zero_metrics()})
            _add_into(slot["metrics"], metrics)
            client_acc = by_client.setdefault(job.client_id, _zero_metrics())
            _add_into(client_acc, metrics)

        reason = "" if corp_registry is not None else "no corp registry — mandate-only rollup"
        return cls(
            available=True,
            reason=reason,
            by_mandate=by_mandate,
            by_job=by_job,
            by_client=by_client,
            unattributed=unattributed,
        )

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "reason": self.reason,
            "by_mandate": self.by_mandate,
            "by_job": self.by_job,
            "by_client": self.by_client,
            "unattributed": self.unattributed,
        }

    # --- trace cross-check ------------------------------------------------------

    @staticmethod
    def cost_cents_by_mandate_from_trace(trace: Any) -> dict[str, float]:
        """Read the max cumulative estimated-cost each mandate reached, from the
        trace's budget-decision records (`mandate_id` carried since F6.1).

        The ledger's `per_mandate` cost sums per-charge cents; a budget-decision's
        `used` is the *cumulative* run cost — so for a single run under a mandate
        the two agree. This is a per-run consistency reader (the replay dict has no
        run_id to sum across runs), used to prove attribution matches the audit.
        """
        out: dict[str, float] = {}
        if trace is None or not hasattr(trace, "replay"):
            return out
        for ev in trace.replay():
            if ev.get("kind") != "budget_decision":
                continue
            if ev.get("metric") != "max_estimated_cost_cents":
                continue
            if ev.get("verdict") != "allow":
                continue
            mid = ev.get("mandate_id")
            if not mid:
                continue
            out[mid] = max(out.get(mid, 0.0), float(ev.get("used", 0.0) or 0.0))
        return out


def _mandate_to_job_map(corp_registry: Any) -> dict[str, Any]:
    """Deterministic mandate_id → JobRecord map from a CorpRegistry.

    When a mandate is referenced by more than one job the sorted-first job wins
    (deterministic); such ambiguity is rare (a mandate is per-job by design).
    """
    mapping: dict[str, Any] = {}
    if corp_registry is None:
        return mapping
    for cid in corp_registry.client_ids():
        for job in corp_registry.jobs_for_client(cid):
            for mid in job.mandate_ids:
                mapping.setdefault(mid, job)
    return mapping


__all__ = ["CostAttributionView"]
