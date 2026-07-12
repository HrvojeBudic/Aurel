"""
system_read_model.py — F8.2 System surface read projections (operator-only).

Audit log and usage/quota views are **pure read-only projections** over governance
state (trace + budget ledger). Additive behind ``AUREL_SYSTEM`` (default OFF ⇒
honestly UNAVAILABLE). Zero writes; agents must not reach these paths.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from ..core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    MemoryGovernanceRecord,
    PlanningFailureRecord,
    PraxisEventRecord,
    RuntimeStatusTransitionRecord,
    SandboxAttestationRecord,
    SandboxViolationRecord,
    StateTransitionRecord,
    ToolContractViolationRecord,
    canonical_json,
    sha,
)

_FLAG = "AUREL_SYSTEM"
_TRUTH_LABEL_LIVE = "LIVE"
_TRUTH_LABEL_UNAVAILABLE = "UNAVAILABLE"


def flag_enabled() -> bool:
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


def unavailable_payload(*, reason: str = "AUREL_SYSTEM off") -> dict[str, Any]:
    return {
        "available": False,
        "status": _TRUTH_LABEL_UNAVAILABLE,
        "reason": reason,
        "truth_label": _TRUTH_LABEL_UNAVAILABLE,
        "operator_only": True,
    }


def _content_ref(ev: dict[str, Any]) -> str:
    return "ev-" + sha(canonical_json(ev))[:16]


def _audit_from_record(rec: Any, seq: int) -> Optional[dict[str, Any]]:
    created_at = float(getattr(rec, "created_at", 0.0) or 0.0)
    mandate_id = str(getattr(rec, "mandate_id", "") or "")
    if isinstance(rec, PlanningFailureRecord):
        ev = {
            "kind": "planning_failure",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "status": rec.status,
            "reason": rec.reason,
            "intent_id": rec.intent_id,
        }
    elif isinstance(rec, RuntimeStatusTransitionRecord):
        ev = {
            "kind": "runtime_status_transition",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "run_id": rec.run_id,
            "from": rec.from_status,
            "to": rec.to_status,
            "reason_code": rec.reason_code,
        }
    elif isinstance(rec, BudgetDecisionRecord):
        ev = {
            "kind": "budget_decision",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "metric": rec.metric,
            "verdict": rec.verdict,
            "used": rec.used,
            "limit": rec.limit,
        }
    elif isinstance(rec, MemoryGovernanceRecord):
        ev = {
            "kind": "memory_governance",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.agent_id,
            "mandate_id": mandate_id,
            "action": rec.action,
            "verdict": rec.verdict,
            "memory_id": rec.memory_id,
        }
    elif isinstance(rec, ToolContractViolationRecord):
        ev = {
            "kind": "tool_contract_violation",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "tool": rec.tool,
            "phase": rec.phase,
            "code": rec.code,
            "reason": rec.reason,
        }
    elif isinstance(rec, ApprovalReceiptRecord):
        ev = {
            "kind": "approval_receipt",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "tool": rec.tool,
            "risk_class": rec.risk_class,
            "outcome": rec.outcome,
            "reason": rec.reason,
        }
    elif isinstance(rec, PraxisEventRecord):
        ev = {
            "kind": "praxis_event",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.agent_id,
            "mandate_id": mandate_id,
            "event_type": rec.event_type,
            "subject_id": rec.subject_id,
            "summary": rec.summary,
        }
    elif isinstance(rec, SandboxViolationRecord):
        ev = {
            "kind": "sandbox_violation",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "tool": rec.tool,
            "action": rec.attempted_action,
            "reason": rec.reason,
        }
    elif isinstance(rec, SandboxAttestationRecord):
        ev = {
            "kind": "sandbox_attestation",
            "seq": seq,
            "created_at": created_at,
            "agent_id": "",
            "mandate_id": mandate_id,
            "backend": rec.backend,
            "available": rec.available,
            "hard_isolated": rec.hard_isolated,
        }
    elif isinstance(rec, StateTransitionRecord):
        ev = {
            "kind": "state_transition",
            "seq": seq,
            "created_at": created_at,
            "agent_id": rec.issuer_card_id,
            "mandate_id": mandate_id,
            "verdict": rec.policy_verdict.value,
            "verified": rec.verifier_result.passed,
        }
    else:
        return None
    return {**ev, "content_ref": _content_ref(ev)}


def _remaining(used: float, limit: float) -> Optional[float]:
    if limit <= 0:
        return None
    return max(0.0, limit - used)


def _policy_remaining(bucket: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    pairs = (
        ("commands", "max_commands_per_run"),
        ("tool_calls", "max_tool_calls_per_run"),
        ("sandbox_executions", "max_sandbox_executions"),
        ("file_writes", "max_file_writes"),
        ("memory_writes", "max_memory_writes"),
        ("estimated_tokens", "max_estimated_tokens"),
        ("estimated_cost_cents", "max_estimated_cost_cents"),
    )
    out: dict[str, Any] = {}
    for used_key, limit_key in pairs:
        used = float(bucket.get(used_key, 0) or 0)
        limit = float(policy.get(limit_key, 0) or 0)
        out[used_key] = {
            "used": used,
            "limit": limit,
            "remaining": _remaining(used, limit),
        }
    return out


@dataclass
class SystemReadModel:
    """Operator-only System surface projections (audit + usage)."""

    runtime: Any
    router: Any = None

    @classmethod
    def from_runtime(cls, runtime: Any, *, router: Any = None) -> "SystemReadModel":
        inner = getattr(runtime, "runtime", runtime)
        rtr = router if router is not None else getattr(runtime, "router", None)
        return cls(inner, router=rtr)

    def audit_log(
        self,
        *,
        kind: str = "",
        mandate_id: str = "",
        agent_id: str = "",
        since: float = 0.0,
        until: float = 0.0,
        offset: int = 0,
        limit: int = 0,
    ) -> dict[str, Any]:
        if not flag_enabled():
            return unavailable_payload()

        events: list[dict[str, Any]] = []
        for seq, rec in enumerate(self.runtime.trace):
            ev = _audit_from_record(rec, seq)
            if ev is None:
                continue
            if kind and ev.get("kind") != kind:
                continue
            if mandate_id and ev.get("mandate_id") != mandate_id:
                continue
            if agent_id and ev.get("agent_id") != agent_id:
                continue
            ts = float(ev.get("created_at", 0.0) or 0.0)
            if since and ts < since:
                continue
            if until and ts > until:
                continue
            events.append(ev)

        total = len(events)
        if offset:
            events = events[offset:]
        truncated = False
        if limit and len(events) > limit:
            events = events[:limit]
            truncated = True

        return {
            "available": True,
            "status": _TRUTH_LABEL_LIVE,
            "truth_label": _TRUTH_LABEL_LIVE,
            "operator_only": True,
            "count": len(events),
            "total": total,
            "events": events,
            "truncated": truncated,
            "filters": {
                "kind": kind,
                "mandate_id": mandate_id,
                "agent_id": agent_id,
                "since": since,
                "until": until,
                "offset": offset,
                "limit": limit,
            },
        }

    def usage(self) -> dict[str, Any]:
        if not flag_enabled():
            return unavailable_payload()

        ledger = self.runtime.budget
        snap = ledger.snapshot()
        policy = dict(snap.get("policy") or {})
        run_usage = dict(snap.get("usage") or {})

        by_mandate: list[dict[str, Any]] = []
        for mid in sorted(getattr(ledger, "per_mandate", {}) or {}):
            bucket = dict(ledger.per_mandate[mid])
            entry: dict[str, Any] = {
                "mandate_id": mid,
                "usage": bucket,
                "policy_remaining": _policy_remaining(bucket, policy),
            }
            corp = getattr(self.runtime, "corp_registry", None)
            mreg = getattr(corp, "mandate_registry", None) if corp else None
            if mreg is not None:
                from ..corp.budget_governance import ClientBudgetView

                view = ClientBudgetView.build(
                    ledger, corp, self.runtime.trace, mandate_registry=mreg,
                )
                if mid in view.by_mandate:
                    entry["budget"] = view.by_mandate[mid]
            by_mandate.append(entry)

        by_agent: list[dict[str, Any]] = []
        for aid in sorted(getattr(ledger, "per_agent", {}) or {}):
            raw = dict(ledger.per_agent[aid])
            runs = raw.pop("runs", set())
            by_agent.append({
                "agent_id": aid,
                "usage": {**raw, "runs": sorted(runs)},
                "policy_remaining": _policy_remaining(raw, policy),
            })

        return {
            "available": True,
            "status": _TRUTH_LABEL_LIVE,
            "truth_label": _TRUTH_LABEL_LIVE,
            "operator_only": True,
            "snapshot": snap,
            "run_usage": run_usage,
            "policy_remaining": _policy_remaining(run_usage, policy),
            "by_mandate": by_mandate,
            "by_agent": by_agent,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": flag_enabled(),
            "audit": self.audit_log(),
            "usage": self.usage(),
            "model_routing": self.model_routing(),
            "policies": self.policy_browser(),
            "archive": self.archive_status(),
        }

    def model_routing(self) -> dict[str, Any]:
        if not flag_enabled():
            return unavailable_payload()

        router = self.router
        if router is None:
            from ..model_router import ModelRouter
            router = ModelRouter()
            router.configure_default()

        profiles = router.list_model_profiles()
        providers = router.provider_status()
        health = {}
        for profile, rows in router.health().items():
            health[profile] = [
                {
                    "provider_name": h.provider_name,
                    "status": h.status.value if hasattr(h.status, "value") else str(h.status),
                    "model_name": h.model_name,
                    "message": h.message,
                }
                for h in rows
            ]

        return {
            "available": True,
            "status": _TRUTH_LABEL_LIVE,
            "truth_label": _TRUTH_LABEL_LIVE,
            "operator_only": True,
            "profiles": profiles,
            "active_profile": getattr(router, "_active_profile", None),
            "default_provider": router.default_provider,
            "providers": providers,
            "health": health,
            "promotion_gates": _promotion_gates_view(),
        }

    def policy_browser(self) -> dict[str, Any]:
        if not flag_enabled():
            return unavailable_payload()

        registry = getattr(self.runtime, "policy_card_registry", None)
        if registry is None:
            return {
                "available": True,
                "status": _TRUTH_LABEL_LIVE,
                "truth_label": _TRUTH_LABEL_LIVE,
                "operator_only": True,
                "registry_bound": False,
                "cards": [],
                "registry_canonical_hash": "",
                "reason": "no policy card registry bound",
            }

        canonical = registry.canonical_dict()
        cards = [_mask_secrets(dict(card)) for card in canonical["cards"]]

        return {
            "available": True,
            "status": _TRUTH_LABEL_LIVE,
            "truth_label": _TRUTH_LABEL_LIVE,
            "operator_only": True,
            "registry_bound": True,
            "cards": cards,
            "registry_canonical_hash": registry.canonical_hash(),
            "grants_authority": False,
        }

    def archive_status(self) -> dict[str, Any]:
        if not flag_enabled():
            return unavailable_payload()

        trace = self.runtime.trace
        from ..aurel_trace.persistent_integrity import (
            PersistentTraceBackendKind,
            assess_persistent_trace_backend,
            profile_persistent_trace_backend,
        )

        if not hasattr(trace, "verify_persisted"):
            return {
                "available": True,
                "status": _TRUTH_LABEL_LIVE,
                "truth_label": _TRUTH_LABEL_LIVE,
                "operator_only": True,
                "persistence": {"backend": "in_memory", "verified": False},
                "integrity": {
                    "status": _TRUTH_LABEL_UNAVAILABLE,
                    "reason": "in-memory trace — no persistent integrity profile",
                },
                "export_manifest": {
                    "available": False,
                    "reason": "no persistent export manifest source",
                },
                "receipt_backlog": {"count": 0, "items": []},
            }

        verify = trace.verify_persisted()
        receipt_path = getattr(trace, "receipt_path", None)
        receipt_exists = bool(receipt_path and receipt_path.exists())
        profile = profile_persistent_trace_backend(
            backend_kind=PersistentTraceBackendKind.JSONL,
            append_only_claim=True,
            hash_chain_supported=True,
            receipt_supported=receipt_exists,
            export_manifest_supported=False,
        )
        assessment = assess_persistent_trace_backend(profile)
        backlog = _receipt_backlog(trace, verify)

        export_manifest: dict[str, Any] = {
            "available": False,
            "reason": "no export manifest bound to runtime",
        }
        manifest = getattr(self.runtime, "_trace_export_manifest", None)
        if manifest is not None and hasattr(manifest, "to_dict"):
            export_manifest = {"available": True, **manifest.to_dict()}

        return {
            "available": True,
            "status": _TRUTH_LABEL_LIVE,
            "truth_label": _TRUTH_LABEL_LIVE,
            "operator_only": True,
            "persistence": verify,
            "integrity": assessment.to_dict(),
            "export_manifest": export_manifest,
            "receipt_backlog": backlog,
        }


def _promotion_gates_view() -> dict[str, Any]:
    """Read-only promotion gate evidence (never triggers promotion)."""
    blocked = sorted({
        "verify_capability", "commit_memory", "promote_skill", "create_skill",
        "create_reflex", "mutate_policy", "change_policy", "rewrite_trace",
        "canonize_roadmap", "override_verifier", "universalize_claim",
        "erase_limitation", "demote_skill", "canon_memory", "skill_memory",
    })
    return {
        "is_evidence_only": True,
        "grants_authority": False,
        "blocked_auto_actions": blocked,
    }


def _mask_secrets(value: Any) -> Any:
    from ..secrets import SecretRedactor
    redactor = SecretRedactor()

    if isinstance(value, dict):
        return {k: _mask_secrets(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_secrets(v) for v in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(token in lowered for token in ("secret", "password", "api_key", "token", "credential")):
            fp = sha(value)[:8]
            return f"<masked:{fp}>"
        return redactor.redact(value)
    return value


def _receipt_backlog(trace: Any, verify: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    receipt_path = getattr(trace, "receipt_path", None)
    if receipt_path is not None and not receipt_path.exists():
        items.append({
            "kind": "run_receipt",
            "run_id": getattr(trace, "run_id", ""),
            "status": "missing",
        })
    if not verify.get("ok", False):
        items.append({
            "kind": "chain_verification",
            "run_id": getattr(trace, "run_id", ""),
            "status": "failed",
            "reason": verify.get("reason", ""),
        })
    return {"count": len(items), "items": items}
