"""
hq_command.py — the HQ.Command read-model (F5.5).

The operator's command surface: a **pure composition of live views** —
  - run status  — the latest `runtime_status_transition` per run (from the trace);
  - approvals   — the immutable approval audit (F5.2, from the trace) plus, when an
                  inbox instance is injected, its in-process pending list;
  - budget burn — `BudgetLedger.snapshot()` (live operational consumption + limits);
  - Watchtower  — a **PARTIAL seam**: the alert feed is F7, so it is declared
                  UNAVAILABLE with an empty list, never a fabricated alert.

No new store, no writes. The predictive burn/ETA is likewise a declared UNAVAILABLE
seam (later), and `CLAIMS_WATCHTOWER_LIVE` is hard-wired False so the missing feed
cannot be over-claimed.
"""
from __future__ import annotations

from typing import Any, Optional

from ..corp import derive_alerts, live_feed, watchtower_flag_enabled
from .approval_inbox import ApprovalInbox

# The default (flag-off) Watchtower claim. The reported value is derived from the
# AUREL_WATCHTOWER flag (F7.3): the feed only claims "live" when it is actually on.
CLAIMS_WATCHTOWER_LIVE = False


class HQCommandReadModel:
    """Live run status + approval inbox + budget burn + Watchtower (F7.3 when on)."""

    def __init__(self, trace: Any, *, budget: Any = None, inbox: Any = None,
                 corp_registry: Any = None) -> None:
        self._trace = trace
        self._budget = budget
        self._inbox = inbox
        self._corp = corp_registry

    @staticmethod
    def from_runtime(runtime: Any, *, inbox: Any = None) -> "HQCommandReadModel":
        inner = getattr(runtime, "runtime", runtime)
        return HQCommandReadModel(
            inner.trace, budget=getattr(inner, "budget", None), inbox=inbox,
            corp_registry=getattr(inner, "corp_registry", None))

    # -- run status (trace projection) ---------------------------------------- #
    def run_status(self) -> list[dict]:
        """The latest status transition per run, deterministically sorted by run_id."""
        runs: dict[str, dict] = {}
        for ev in self._trace.replay():
            if ev.get("kind") != "runtime_status_transition":
                continue
            rid = str(ev.get("run_id", ""))
            entry = runs.setdefault(rid, {
                "run_id": rid, "status": "", "reason_code": "",
                "issuer": "", "transitions": 0})
            entry["status"] = ev.get("to", "")
            entry["reason_code"] = ev.get("reason_code", "")
            entry["issuer"] = ev.get("issuer", "")
            entry["transitions"] += 1
        return [runs[k] for k in sorted(runs)]

    # -- approvals (audit + optional pending) --------------------------------- #
    def approvals(self) -> dict:
        audit = ApprovalInbox.audit_from_trace(self._trace)
        # Pending is in-process operational state (holds command args for Phase B),
        # not a trace projection — present only when an inbox instance is injected.
        pending = self._inbox.pending() if self._inbox is not None else []
        return {"audit": audit, "pending": pending,
                "pending_source": "inbox" if self._inbox is not None else "unavailable"}

    # -- budget burn (live operational snapshot) ------------------------------ #
    def budget(self) -> dict:
        if self._budget is None or not hasattr(self._budget, "snapshot"):
            return {"status": "UNAVAILABLE", "reason": "no budget ledger bound"}
        return {"status": "AVAILABLE", **self._budget.snapshot()}

    # -- Watchtower (F7.3 live when on) / predictive (declared seam) ----------- #
    def watchtower(self) -> dict:
        """Live alert feed when AUREL_WATCHTOWER is on (F7.3); else the byte-identical
        UNAVAILABLE stub. Read-only monitor — visibility, never authority."""
        if not watchtower_flag_enabled():
            return {"status": "UNAVAILABLE", "owner": "F7",
                    "reason": "Watchtower alert feed is F7; not live in F5",
                    "alerts": []}
        alerts = derive_alerts(self._trace, self._budget, self._corp, inbox=self._inbox)
        return live_feed(alerts)

    @staticmethod
    def predictive() -> dict:
        return {"status": "UNAVAILABLE", "owner": "later",
                "reason": "predictive burn / ETA is a later seam", "alerts": []}

    def to_dict(self) -> dict:
        return {
            "runs": self.run_status(),
            "approvals": self.approvals(),
            "budget": self.budget(),
            "watchtower": self.watchtower(),
            "predictive": self.predictive(),
            "claims_watchtower_live": watchtower_flag_enabled(),
        }
