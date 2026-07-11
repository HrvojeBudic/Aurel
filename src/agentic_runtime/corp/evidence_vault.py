"""
evidence_vault.py — Operations.Evidence Vault: trace search + receipt export (F7.4).

The Vault answers *what happened, for whom, and can I prove it?* — read-only over
the trace. It **completes the Output Passport**: for a job (or run) it exports a
self-contained bundle {filtered records + chain head + a real P5 verification
receipt} whose integrity is checkable offline. Doctrine:

  * search + export are **read-only over the trace** — zero mutation.
  * `verified` is **derived only from an actual P5 hash-chain verification** — it
    is `True` iff the chain PASSes (P5-TRACE-B never upgrades FAIL/PARTIAL). A
    tampered trace verifies FAIL ⇒ `verified=False`, and the bundle carries the
    chain head so the tamper is visible.
  * an empty result is empty, not UNAVAILABLE.
"""
from __future__ import annotations

from typing import Any

from ..aurel_trace import (
    AurelTraceError,
    TraceHashVerificationRequest,
    TraceVerificationScope,
    build_trace_verification_receipt,
    envelopes_from_ledger,
    trace_run_ref_from_ledger,
    verify_canonical_trace_hash_chain,
)
from ..core_types import canonical_json, sha

# The business-visible record kinds the Vault searches (each carries mandate_id
# since F6.1, except run_id which only runtime_status_transition exposes on replay).
_SEARCHABLE_KINDS = (
    "budget_decision",
    "approval_receipt",
    "praxis_event",
    "runtime_status_transition",
    "memory_governance",
)


def _content_ref(ev: dict) -> str:
    """A deterministic content reference for one event (same content ⇒ same ref)."""
    return "ev-" + sha(canonical_json(ev))[:16]


class EvidenceVaultQuery:
    """Read-only search + receipt-bundle export over one runtime's trace."""

    def __init__(self, trace: Any, corp_registry: Any = None) -> None:
        self._trace = trace
        self._corp = corp_registry

    @staticmethod
    def from_runtime(runtime: Any, *, corp_registry: Any = None) -> "EvidenceVaultQuery":
        inner = getattr(runtime, "runtime", runtime)
        return EvidenceVaultQuery(
            inner.trace, getattr(inner, "corp_registry", None) or corp_registry)

    def _client_mandates(self, client_id: str) -> set[str]:
        out: set[str] = set()
        if self._corp is None or not client_id:
            return out
        for job in self._corp.jobs_for_client(client_id):
            out.update(job.mandate_ids)
        return out

    def search(
        self,
        *,
        mandate_id: str = "",
        client_id: str = "",
        kind: str = "",
        run_id: str = "",
        limit: int = 0,
    ) -> dict:
        """Filter the trace's business records. Deterministic (replay order)."""
        client_mandates = self._client_mandates(client_id) if client_id else None
        events: list[dict] = []
        for ev in self._trace.replay():
            k = ev.get("kind", "")
            if k not in _SEARCHABLE_KINDS:
                continue
            if kind and k != kind:
                continue
            emid = ev.get("mandate_id", "")
            if mandate_id and emid != mandate_id:
                continue
            if client_mandates is not None and emid not in client_mandates:
                continue
            if run_id and str(ev.get("run_id", "")) != run_id:
                continue
            events.append({**ev, "content_ref": _content_ref(ev)})
        truncated = False
        if limit and len(events) > limit:
            events = events[:limit]
            truncated = True
        return {
            "count": len(events),
            "events": events,
            "truncated": truncated,
            "filters": {"mandate_id": mandate_id, "client_id": client_id,
                        "kind": kind, "run_id": run_id},
        }

    def export_receipt_bundle(
        self, *, job_id: str = "", run_id: str = "", mandate_id: str = ""
    ) -> dict:
        """Export a self-contained Output Passport for a job / run.

        The bundle carries the filtered records, the verified chain head, and a
        real P5 verification receipt (`verified` iff the chain PASSes). Read-only.
        """
        mandate_ids: tuple[str, ...] = ()
        if job_id:
            if self._corp is None:
                return {"output_passport": False, "available": False,
                        "reason": "no corp registry to resolve job"}
            job = self._corp.resolve_job(job_id)
            if job is None:
                return {"output_passport": False, "available": False,
                        "reason": f"unknown job {job_id!r}"}
            mandate_ids = job.mandate_ids

        events = self._bundle_events(mandate_ids, run_id, mandate_id)
        verification = self._verify()
        return {
            "output_passport": True,
            "available": True,
            "job_id": job_id,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "chain_head_hash": verification.get("chain_head_hash"),
            "verified": bool(verification.get("verified", False)),
            "verification": verification,
            "event_count": len(events),
            "events": events,
        }

    def _bundle_events(
        self, mandate_ids: tuple[str, ...], run_id: str, mandate_id: str
    ) -> list[dict]:
        out: list[dict] = []
        for ev in self._trace.replay():
            if ev.get("kind", "") not in _SEARCHABLE_KINDS:
                continue
            emid = ev.get("mandate_id", "")
            if mandate_ids and emid not in mandate_ids:
                continue
            if mandate_id and emid != mandate_id:
                continue
            if run_id and str(ev.get("run_id", "")) != run_id:
                continue
            out.append({**ev, "content_ref": _content_ref(ev)})
        return out

    def _verify(self) -> dict:
        """Run the real P5 full-chain verification over the trace. `verified` is
        True iff PASS; an unverifiable trace is honestly not verified, with a reason."""
        try:
            run_ref = trace_run_ref_from_ledger(self._trace)
            envelopes = envelopes_from_ledger(self._trace, trace_run_ref=run_ref)
            request = TraceHashVerificationRequest(
                verification_request_id=f"vault-{run_ref.trace_run_id}",
                trace_run_ref=run_ref,
                scope=TraceVerificationScope.FULL_CHAIN,
            )
            result = verify_canonical_trace_hash_chain(request, envelopes)
            return build_trace_verification_receipt(result, request).to_dict()
        except AurelTraceError as exc:  # unverifiable ⇒ honest, never a fake PASS
            return {"verified": False, "status": "UNAVAILABLE", "reason": str(exc),
                    "chain_head_hash": getattr(self._trace, "head", None)}


__all__ = ["EvidenceVaultQuery"]
