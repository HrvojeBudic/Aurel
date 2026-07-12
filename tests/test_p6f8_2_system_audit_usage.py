"""F8.2 seal — System surface audit log + usage read-models."""
from __future__ import annotations

import json

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import BudgetDecisionRecord, PraxisEventRecord
from agentic_runtime.front_server import LiveReadModels, SystemReadModel
from agentic_runtime.front_server.system_read_model import flag_enabled
from agentic_runtime.mandate import Mandate, MandateRegistry, MandateScope, default_mandate
from agentic_runtime.corp import CLIENT_ZERO_ID, CorpRegistry, JobRecord, client_zero
from agentic_runtime.core_types import RiskLevel


def _seed_audit(trace, *, mandate_id: str = "m-audit", agent_id: str = "agent-a"):
    trace.append_praxis_event(PraxisEventRecord.make(
        run_id=trace.run_id,
        agent_id=agent_id,
        event_type="system_probe",
        subject_id="subj-1",
        summary="probe one",
        mandate_id=mandate_id,
    ))
    trace.append_praxis_event(PraxisEventRecord.make(
        run_id=trace.run_id,
        agent_id="agent-b",
        event_type="system_probe",
        subject_id="subj-2",
        summary="probe two",
        mandate_id="m-other",
    ))
    trace.append_budget_decision(BudgetDecisionRecord.make(
        run_id=trace.run_id,
        intent_id="intent-audit",
        issuer_card_id=agent_id,
        metric="max_tool_calls_per_run",
        verdict="warn",
        used=3.0,
        limit=10.0,
        mandate_id=mandate_id,
    ))


@pytest.fixture(autouse=True)
def _system_off(monkeypatch):
    monkeypatch.delenv("AUREL_SYSTEM", raising=False)


def test_audit_filters_kind_mandate_agent_deterministic(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    rt = build_runtime()
    _seed_audit(rt.runtime.trace)
    model = SystemReadModel.from_runtime(rt)

    all_events = model.audit_log()["events"]
    by_kind = model.audit_log(kind="praxis_event")["events"]
    assert all(e["kind"] == "praxis_event" for e in by_kind)
    assert len(by_kind) < len(all_events)

    by_mandate = model.audit_log(mandate_id="m-audit")["events"]
    assert by_mandate
    assert all(e.get("mandate_id") == "m-audit" for e in by_mandate)

    by_agent = model.audit_log(agent_id="agent-a")["events"]
    assert by_agent
    assert all(e.get("agent_id") == "agent-a" for e in by_agent)

    first_ts = by_kind[0]["created_at"]
    by_time = model.audit_log(since=first_ts, until=first_ts)["events"]
    assert all(e["created_at"] == first_ts for e in by_time)

    a = json.dumps(model.audit_log(kind="budget_decision"), sort_keys=True)
    b = json.dumps(model.audit_log(kind="budget_decision"), sort_keys=True)
    assert a == b


def test_audit_empty_filter_is_empty_not_unavailable(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    rt = build_runtime()
    body = SystemReadModel.from_runtime(rt).audit_log(kind="praxis_event")
    assert body["available"] is True
    assert body["count"] == 0
    assert body["events"] == []


def test_usage_from_live_ledger_and_remaining(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    mandate = Mandate(
        mandate_id="m-budget",
        version="v1",
        scope=MandateScope(client_id=CLIENT_ZERO_ID, budget_cents=1000.0, max_risk=RiskLevel.MEDIUM),
    )
    mreg = MandateRegistry.from_mandates([default_mandate(), mandate])
    job = JobRecord(job_id="job-budget", client_id=CLIENT_ZERO_ID, mandate_ids=(mandate.mandate_id,))
    corp = CorpRegistry.from_records([client_zero()], [job], mandate_registry=mreg)
    rt = build_runtime()
    rt.runtime.corp_registry = corp
    ledger = rt.runtime.budget
    ledger.begin_run("run-u", "agent-u", "intent-u")
    ledger.set_mandate(mandate.mandate_id)
    ledger.charge_tool(agent_id="agent-u")
    ledger.charge_tool(agent_id="agent-u")

    usage = SystemReadModel.from_runtime(rt).usage()
    assert usage["available"] is True
    assert usage["snapshot"]["tool_calls"] >= 2
    rem = usage["policy_remaining"]["tool_calls"]
    assert rem["used"] >= 2
    assert rem["remaining"] == rem["limit"] - rem["used"]

    mandate_entry = next(e for e in usage["by_mandate"] if e["mandate_id"] == mandate.mandate_id)
    assert mandate_entry["budget"]["allocation_cents"] == 1000.0
    assert mandate_entry["budget"]["remaining_cents"] is not None

    agent_entry = next(e for e in usage["by_agent"] if e["agent_id"] == "agent-u")
    assert agent_entry["usage"]["tool_calls"] >= 2


def test_reads_never_write(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    rt = build_runtime()
    _seed_audit(rt.runtime.trace)
    reads = LiveReadModels(rt)
    before = len(list(rt.runtime.trace.replay()))
    reads.read("/read/system/audit")
    reads.read("/read/system/usage")
    after = len(list(rt.runtime.trace.replay()))
    assert after == before


def test_system_reads_live_when_flag_on(monkeypatch):
    monkeypatch.setenv("AUREL_SYSTEM", "1")
    rt = build_runtime()
    _seed_audit(rt.runtime.trace)
    reads = LiveReadModels(rt)
    audit_status, audit = reads.read("/read/system/audit?kind=praxis_event")
    usage_status, usage = reads.read("/read/system/usage")
    assert audit_status == 200 and audit["available"] is True
    assert usage_status == 200 and usage["available"] is True
    assert audit["model"] == "system/audit"
    assert usage["model"] == "system/usage"
    assert audit["operator_only"] is True


def test_system_reads_unavailable_when_flag_off():
    rt = build_runtime()
    reads = LiveReadModels(rt)
    _status, audit = reads.read("/read/system/audit")
    _status2, usage = reads.read("/read/system/usage")
    assert audit["available"] is False
    assert audit["status"] == "UNAVAILABLE"
    assert usage["available"] is False
    assert flag_enabled() is False


def test_system_projections_boundary():
    from agentic_runtime.aurel_shell.boundaries import build_system_read_model_projections

    projections = build_system_read_model_projections()
    paths = {p.read_path for p in projections}
    assert "/read/system/audit" in paths
    assert "/read/system/usage" in paths
    assert all(p.operator_only and p.zero_write for p in projections)
