"""
watchtower.py — the Watchtower read-only alert derivation (F7.3).

Watchtower is the Business Plane's **read-only monitor**: it derives governance
alerts from facts already in the trace + the live ledger and surfaces them to the
operator (HQ.Command, CORP portfolio). It is the first module that *actively*
brings signals to the operator — but it is **visibility, never authority**: it
never blocks, never executes, never changes a verdict.

Doctrine (structural):
  * a `WatchtowerAlert` is **un-constructible without a `source_ref`** — an alert
    that cannot cite the trace entry / ledger metric it came from does not exist
    (no fabricated alerts).
  * rules are pure functions over one `replay()` pass + one ledger snapshot,
    deterministic (no `hash()`, no wall-clock — only fields from the records), and
    the result is sorted by `(severity, alert_id)`.
  * additive behind `AUREL_WATCHTOWER` (default OFF ⇒ the HQ.Command / CORP seams
    stay byte-identical UNAVAILABLE stubs).

The same derivation feeds both surfaces that declared the seam — HQ.Command's
Watchtower (F5.5) and the CORP portfolio's alerts (F7.5) — one source, two homes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..core_types import canonical_json, sha
from .cost import _mandate_to_job_map

_FLAG = "AUREL_WATCHTOWER"


def flag_enabled() -> bool:
    """True iff the Watchtower flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


class AlertSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


class AlertKind(str, Enum):
    BUDGET_DENY = "budget_deny"
    BUDGET_THRESHOLD = "budget_threshold"
    MANDATE_BLOCK = "mandate_block"
    CONSTITUTION_VIOLATION = "constitution_violation"
    APPROVAL_PENDING = "approval_pending"


_SEVERITY_RANK = {AlertSeverity.CRITICAL: 0, AlertSeverity.WARN: 1, AlertSeverity.INFO: 2}

# Run-status transitions that warrant an alert, with their severity.
_BLOCKED_STATUS_SEVERITY = {
    "rejected": AlertSeverity.CRITICAL,
    "failed": AlertSeverity.CRITICAL,
    "verification_failed": AlertSeverity.CRITICAL,
    "failed_with_partial_execution": AlertSeverity.CRITICAL,
    "halted": AlertSeverity.CRITICAL,
    "blocked": AlertSeverity.CRITICAL,      # defensive (not a current ExecutionStatus value)
    "denied": AlertSeverity.CRITICAL,       # defensive
    "needs_human": AlertSeverity.WARN,
}

# Run-usage metric → policy cap, for the >80% threshold rule (read from a snapshot).
_THRESHOLD_METRICS = (
    ("estimated_cost_cents", "max_estimated_cost_cents"),
    ("estimated_tokens", "max_estimated_tokens"),
    ("tool_calls", "max_tool_calls_per_run"),
    ("sandbox_executions", "max_sandbox_executions"),
    ("commands", "max_commands_per_run"),
    ("memory_writes", "max_memory_writes"),
)


@dataclass(frozen=True)
class WatchtowerAlert:
    """A governance alert citing the trace entry / ledger metric it came from."""

    kind: AlertKind
    severity: AlertSeverity
    message: str
    source_ref: str                 # required — no fabricated alert
    mandate_id: str = ""
    client_id: str = ""

    def __post_init__(self) -> None:
        if not self.source_ref:
            raise ValueError("WatchtowerAlert requires a source_ref (no fabricated alert)")
        if not isinstance(self.kind, AlertKind):
            raise TypeError("WatchtowerAlert requires an AlertKind")
        if not isinstance(self.severity, AlertSeverity):
            raise TypeError("WatchtowerAlert requires an AlertSeverity")

    @property
    def alert_id(self) -> str:
        """Deterministic identity from (kind, source_ref) — same source ⇒ same id."""
        return sha(canonical_json({"kind": self.kind.value, "source_ref": self.source_ref}))[:16]

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "kind": self.kind.value,
            "severity": self.severity.value,
            "message": self.message,
            "source_ref": self.source_ref,
            "mandate_id": self.mandate_id,
            "client_id": self.client_id,
        }


def derive_alerts(
    trace: Any,
    ledger: Any = None,
    corp_registry: Any = None,
    *,
    inbox: Any = None,
) -> list[WatchtowerAlert]:
    """Derive alerts from one trace replay + one ledger snapshot. Read-only.

    Deterministic and fail-open on absence: no trace ⇒ no trace-derived alerts; no
    ledger ⇒ the budget-threshold rule is skipped (never invented); no inbox ⇒ no
    pending-approval alerts (pending is operational state, not a trace projection).
    Alerts dedup by `source_ref` and sort by `(severity, alert_id)`.
    """
    mandate_to_job = _mandate_to_job_map(corp_registry)

    def client_of(mandate_id: str) -> str:
        job = mandate_to_job.get(mandate_id) if mandate_id else None
        return job.client_id if job is not None else ""

    by_source: dict[str, WatchtowerAlert] = {}

    def add(alert: WatchtowerAlert) -> None:
        by_source.setdefault(alert.source_ref, alert)

    # -- trace-derived rules (one replay pass) --------------------------------- #
    if trace is not None and hasattr(trace, "replay"):
        for ev in trace.replay():
            kind = ev.get("kind")
            if kind == "budget_decision" and ev.get("verdict") == "deny":
                mid = ev.get("mandate_id", "")
                metric = ev.get("metric", "")
                src = f"budget_deny:{metric}:{mid}:{ev.get('used', 0)}"
                add(WatchtowerAlert(
                    AlertKind.BUDGET_DENY, AlertSeverity.CRITICAL,
                    f"budget '{metric}' denied at {ev.get('used', 0)}/{ev.get('limit', 0)}",
                    src, mandate_id=mid, client_id=client_of(mid)))
            elif kind == "runtime_status_transition":
                to = str(ev.get("to", ""))
                severity = _BLOCKED_STATUS_SEVERITY.get(to)
                if severity is None:
                    continue
                mid = ev.get("mandate_id", "")
                rc = ev.get("reason_code", "")
                src = f"mandate_block:{ev.get('run_id', '')}:{to}:{rc}"
                add(WatchtowerAlert(
                    AlertKind.MANDATE_BLOCK, severity,
                    f"run {ev.get('run_id', '')} → {to} ({rc})",
                    src, mandate_id=mid, client_id=client_of(mid)))
            elif kind == "praxis_event" and ev.get("event_type") == "constitution_violation":
                mid = ev.get("mandate_id", "") or _cvio_mandate(ev)
                reason = _cvio_reason(ev)
                src = f"constitution_violation:{mid}:{reason}"
                add(WatchtowerAlert(
                    AlertKind.CONSTITUTION_VIOLATION, AlertSeverity.CRITICAL,
                    f"constitution violation ({reason})",
                    src, mandate_id=mid, client_id=client_of(mid)))

    # -- ledger threshold rule (live snapshot) --------------------------------- #
    if ledger is not None and hasattr(ledger, "snapshot"):
        for alert in _threshold_alerts(ledger.snapshot()):
            add(alert)

    # -- pending-approval rule (operational, optional) ------------------------- #
    if inbox is not None and hasattr(inbox, "pending"):
        for item in inbox.pending():
            rid = str(item.get("request_id", ""))
            if not rid:
                continue
            mid = str(item.get("mandate_id", ""))
            add(WatchtowerAlert(
                AlertKind.APPROVAL_PENDING, AlertSeverity.WARN,
                f"approval pending: {item.get('tool', '')}",
                f"approval_pending:{rid}", mandate_id=mid, client_id=client_of(mid)))

    return sorted(by_source.values(), key=lambda a: (_SEVERITY_RANK[a.severity], a.alert_id))


def live_feed(alerts: list[WatchtowerAlert]) -> dict:
    """The standard live Watchtower feed dict (shared by HQ.Command + CORP)."""
    return {
        "status": "LIVE",
        "source": "trace+ledger",
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


def _threshold_alerts(snapshot: dict) -> list[WatchtowerAlert]:
    usage = snapshot.get("usage", {}) or {}
    policy = snapshot.get("policy", {}) or {}
    out: list[WatchtowerAlert] = []
    checks: list[tuple[str, float, float]] = [
        ("llm_calls", float(snapshot.get("llm_calls", 0) or 0),
         float(policy.get("max_llm_calls", 0) or 0)),
    ]
    for usage_key, policy_key in _THRESHOLD_METRICS:
        checks.append((usage_key, float(usage.get(usage_key, 0) or 0),
                       float(policy.get(policy_key, 0) or 0)))
    for name, value, limit in checks:
        if limit <= 0 or value <= 0.8 * limit:
            continue
        severity = AlertSeverity.CRITICAL if value >= limit else AlertSeverity.WARN
        out.append(WatchtowerAlert(
            AlertKind.BUDGET_THRESHOLD, severity,
            f"budget '{name}' at {value:.1f}/{limit:.1f} (>80%)",
            f"budget_threshold:{name}"))
    return out


def _cvio_parts(ev: dict) -> list[str]:
    return str(ev.get("summary", "")).split("|", 2)


def _cvio_mandate(ev: dict) -> str:
    parts = _cvio_parts(ev)
    return parts[1] if len(parts) >= 2 else ""


def _cvio_reason(ev: dict) -> str:
    parts = _cvio_parts(ev)
    return parts[2] if len(parts) >= 3 else ""


__all__ = [
    "WatchtowerAlert",
    "AlertSeverity",
    "AlertKind",
    "derive_alerts",
    "live_feed",
    "flag_enabled",
]
