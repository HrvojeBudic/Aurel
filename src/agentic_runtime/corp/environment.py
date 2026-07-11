"""
environment.py — governed environment creation + trace-projected registry (F7 wire).

The Agency wizard (F7.6) drafts a {client + job + mandate}; this closes the loop so
the operator can actually **create** one through the one door. A created environment
is a **governed trace record** (a hash-chained praxis event, like the Risk Register
and the Board journal), and the Corp registry the read models use is rebuilt from
the trace — so a created client/job/mandate persists and appears in the portfolio,
cost, budget, and workbench views.

Doctrine: creation is a governed append, never an ambient config edit. The registry
is a **projection over the trace** seeded by klijent nula (the default), so with no
environment events it is byte-identical to `default_corp_registry()`. Mandates
created here are resolvable (folded into the projected MandateRegistry) so cost /
budget attribution links; deterministic ids (content-hashed) keep it replayable.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from ..core_types import PraxisEventRecord, RiskLevel, canonical_json, sha
from ..mandate import Mandate, MandateRegistry, MandateScope, default_mandate
from .default import client_zero, client_zero_job
from .domain import ClientRecord, JobRecord, JobStatus
from .registry import CorpRegistry

CORP_ENVIRONMENT_EVENT = "corp_environment"
_ENV_MARK = "ENV"


def _scope_from_dict(d: Mapping[str, Any]) -> MandateScope:
    return MandateScope(
        paths=tuple(d.get("paths", []) or []),
        repos=tuple(d.get("repos", []) or []),
        client_id=str(d.get("client_id", "") or ""),
        budget_cents=float(d.get("budget_cents", 0.0) or 0.0),
        allowed_tools=tuple(d.get("allowed_tools", []) or []),
        max_risk=RiskLevel(d.get("max_risk", "critical")),
    )


def _env_ids(client_name: str, job_title: str, scope: MandateScope,
             persona_ref: str, mandate_override: str) -> tuple[str, str, str]:
    h = sha(canonical_json({
        "client_name": client_name, "job_title": job_title,
        "scope": scope.to_dict(), "persona_ref": persona_ref}))[:10]
    return f"client-{h}", f"job-{h}", (mandate_override or f"mandate-{h}")


def record_environment(
    trace: Any,
    *,
    client_name: str,
    job_title: str,
    scope: MandateScope,
    persona_ref: str = "default",
    memory_zone_rules: Optional[Mapping[str, str]] = None,
    repos: tuple[str, ...] = (),
    mandate_id: str = "",
    agent_id: str = "operator",
) -> tuple[PraxisEventRecord, dict]:
    """Append a governed environment (client + job + mandate) to the trace."""
    if not client_name or not job_title:
        raise ValueError("record_environment requires client_name and job_title")
    client_id, job_id, mandate_id = _env_ids(
        client_name, job_title, scope, persona_ref, mandate_id)
    # the mandate confines to this client; the job carries the client for attribution
    scope_for_mandate = MandateScope(
        paths=scope.paths, repos=scope.repos, client_id=client_id,
        budget_cents=scope.budget_cents, allowed_tools=scope.allowed_tools,
        max_risk=scope.max_risk)
    zones = dict(memory_zone_rules or {})
    payload = {
        "client": {"client_id": client_id, "name": client_name, "notes": ""},
        "mandate": {"mandate_id": mandate_id, "version": "v1",
                    "scope": scope_for_mandate.to_dict(), "persona_ref": persona_ref,
                    "memory_zone_rules": zones},
        "job": {"job_id": job_id, "client_id": client_id, "mandate_ids": [mandate_id],
                "repos": list(repos), "status": JobStatus.ACTIVE.value, "title": job_title},
    }
    rec = PraxisEventRecord.make(
        run_id=getattr(trace, "run_id", ""), agent_id=agent_id,
        event_type=CORP_ENVIRONMENT_EVENT, subject_id=client_id,
        summary=f"{_ENV_MARK}|{canonical_json(payload)}", mandate_id=mandate_id)
    trace.append_praxis_event(rec)
    return rec, {"client_id": client_id, "job_id": job_id, "mandate_id": mandate_id}


def record_environment_from_payload(
    trace: Any, args: Mapping[str, Any], *, mandate_id: str = "", agent_id: str = "operator"
) -> tuple[PraxisEventRecord, dict]:
    """Record an environment from the Agency-wizard `to_proposal()` args."""
    a = dict(args or {})
    return record_environment(
        trace,
        client_name=str(a.get("client_name", "")),
        job_title=str(a.get("job_title", "")),
        scope=_scope_from_dict(a.get("scope", {}) or {}),
        persona_ref=str(a.get("persona_ref", "default") or "default"),
        memory_zone_rules=a.get("memory_zone_rules", {}) or {},
        repos=tuple(a.get("repos", []) or []),
        mandate_id=mandate_id, agent_id=agent_id)


def _env_from_summary(summary: str) -> Optional[dict]:
    parts = str(summary).split("|", 1)
    if len(parts) != 2 or parts[0] != _ENV_MARK:
        return None
    try:
        return json.loads(parts[1])
    except (ValueError, TypeError):
        return None


def _rebuild(env: dict) -> tuple[ClientRecord, JobRecord, Mandate]:
    c = env["client"]
    client = ClientRecord(client_id=c["client_id"], name=c["name"], notes=c.get("notes", ""))
    m = env["mandate"]
    mandate = Mandate(mandate_id=m["mandate_id"], version=m.get("version", "v1"),
                      scope=_scope_from_dict(m["scope"]),
                      persona_ref=m.get("persona_ref", "default"),
                      memory_zone_rules=dict(m.get("memory_zone_rules", {})))
    j = env["job"]
    job = JobRecord(job_id=j["job_id"], client_id=j["client_id"],
                    mandate_ids=tuple(j.get("mandate_ids", [])),
                    repos=tuple(j.get("repos", [])),
                    status=JobStatus(j.get("status", "active")), title=j.get("title", ""))
    return client, job, mandate


def corp_registry_from_trace(trace: Any) -> CorpRegistry:
    """The Corp registry = klijent nula (default) + every environment created on the
    trace. With no environment events this is byte-identical to `default_corp_registry`."""
    czero = client_zero()
    clients: dict[str, ClientRecord] = {czero.client_id: czero}
    jobs: dict[str, JobRecord] = {client_zero_job().job_id: client_zero_job()}
    dmand = default_mandate()
    mandates: dict[str, Mandate] = {dmand.mandate_id: dmand}

    if trace is not None and hasattr(trace, "replay"):
        for ev in trace.replay():
            if ev.get("kind") != "praxis_event":
                continue
            if ev.get("event_type") != CORP_ENVIRONMENT_EVENT:
                continue
            env = _env_from_summary(ev.get("summary", ""))
            if env is None:
                continue
            client, job, mandate = _rebuild(env)
            clients[client.client_id] = client         # latest wins (replay chronological)
            jobs[job.job_id] = job
            mandates[mandate.mandate_id] = mandate

    mreg = MandateRegistry.from_mandates(list(mandates.values()))
    return CorpRegistry.from_records(
        list(clients.values()), list(jobs.values()), mandate_registry=mreg)


__all__ = ["record_environment", "record_environment_from_payload",
           "corp_registry_from_trace", "CORP_ENVIRONMENT_EVENT"]
