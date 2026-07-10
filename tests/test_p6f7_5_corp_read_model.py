"""F7.5 seal — the CORP surface read-model (portfolio tree + task-runtime feed).

A pure projection over the trace + the Corp registry (F7.0) + the cost view (F7.1):
client → job → mandates → runs (status overlay), plus a chronological feed
filterable by job. Run → job resolves through the `mandate_id` each trace record
carries (F6.1); a run whose mandate maps to no job is honestly `unassigned`. Alerts
(F7.3) and budget governance (F7.2) are declared UNAVAILABLE seams. Zero writes.
"""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RuntimeStatusTransitionRecord
from agentic_runtime.corp import CLIENT_ZERO_ID, JOB_ZERO_ID
from agentic_runtime.front_server import (
    CLAIMS_ALERTS_LIVE,
    CLAIMS_BUDGET_GOVERNANCE_LIVE,
    CorpReadModel,
    LiveReadModels,
)
from agentic_runtime.mandate import DEFAULT_MANDATE_ID


def _seed(rt):
    """Two runs under klijent nula's default mandate, one orphan, one mandate-less."""
    trace = rt.runtime.trace
    rows = (
        ("run-a", "planned", "running", "dispatch", DEFAULT_MANDATE_ID),
        ("run-a", "running", "succeeded", "verified", DEFAULT_MANDATE_ID),
        ("run-b", "planned", "blocked", "mandate_scope", "ghost-mandate"),   # maps to no job
        ("run-c", "planned", "running", "dispatch", ""),                      # no mandate at all
    )
    for run_id, frm, to, rc, mid in rows:
        trace.append_status_transition(RuntimeStatusTransitionRecord.make(
            run_id=run_id, intent_id="i", issuer_card_id="card-1",
            from_status=frm, to_status=to, reason_code=rc, message="m",
            mandate_id=mid))


def _charge_cost(rt):
    budget = rt.runtime.budget
    budget.begin_run("run-a", "card-1", "i")
    budget.set_mandate(DEFAULT_MANDATE_ID)
    budget.charge_tool("card-1")


# --- portfolio tree ---------------------------------------------------------------

def test_portfolio_tree_maps_runs_to_klijent_nula():
    rt = build_runtime()
    _seed(rt)
    view = CorpReadModel.from_runtime(rt).portfolio_view()
    clients = {c["client_id"]: c for c in view["clients"]}
    assert CLIENT_ZERO_ID in clients
    jobs = {j["job_id"]: j for j in clients[CLIENT_ZERO_ID]["jobs"]}
    assert JOB_ZERO_ID in jobs
    run_ids = {r["run_id"] for r in jobs[JOB_ZERO_ID]["runs"]}
    assert run_ids == {"run-a"}                                  # run-a maps via default mandate
    assert jobs[JOB_ZERO_ID]["runs"][0]["status"] == "succeeded"  # latest transition overlay


def test_unassigned_runs_are_honest():
    rt = build_runtime()
    _seed(rt)
    view = CorpReadModel.from_runtime(rt).portfolio_view()
    unassigned = {r["run_id"] for r in view["unassigned"]}
    assert unassigned == {"run-b", "run-c"}                      # orphan mandate + mandate-less
    # the link is never invented — run-b's ghost mandate is not forced into a job


# --- cost overlay (F7.1) ----------------------------------------------------------

def test_cost_overlay_present_with_ledger():
    rt = build_runtime()
    _seed(rt)
    _charge_cost(rt)
    view = CorpReadModel.from_runtime(rt).portfolio_view()
    assert view["cost"]["status"] == "AVAILABLE"
    job = next(j for c in view["clients"] if c["client_id"] == CLIENT_ZERO_ID
               for j in c["jobs"] if j["job_id"] == JOB_ZERO_ID)
    assert job["cost"]["tool_calls"] == 1
    client = next(c for c in view["clients"] if c["client_id"] == CLIENT_ZERO_ID)
    assert client["cost"]["tool_calls"] == 1


def test_cost_unavailable_without_ledger():
    rt = build_runtime()
    _seed(rt)
    cm = CorpReadModel(rt.runtime.trace, CorpReadModel.from_runtime(rt)._corp, budget=None)
    view = cm.portfolio_view()
    assert view["cost"]["status"] == "UNAVAILABLE"
    job = next(j for c in view["clients"] if c["client_id"] == CLIENT_ZERO_ID
               for j in c["jobs"] if j["job_id"] == JOB_ZERO_ID)
    assert job["cost"] is None                                   # honest, not a fabricated zero


# --- declared seams (F7.2 / F7.3) -------------------------------------------------

def test_alerts_and_budget_governance_are_unavailable_seams():
    rt = build_runtime()
    view = CorpReadModel.from_runtime(rt).portfolio_view()
    assert view["alerts"]["status"] == "UNAVAILABLE" and view["alerts"]["owner"] == "F7.3"
    assert view["budget_governance"]["status"] == "UNAVAILABLE"
    assert view["budget_governance"]["owner"] == "F7.2"
    assert view["claims_alerts_live"] is False and CLAIMS_ALERTS_LIVE is False
    assert (view["claims_budget_governance_live"] is False
            and CLAIMS_BUDGET_GOVERNANCE_LIVE is False)


# --- task-runtime feed ------------------------------------------------------------

def test_runtime_feed_filters_by_job():
    rt = build_runtime()
    _seed(rt)
    cm = CorpReadModel.from_runtime(rt)
    feed = cm.runtime_feed(JOB_ZERO_ID)
    assert feed["available"] is True
    # only events carrying the job's mandate (DEFAULT_MANDATE_ID) appear
    assert all(ev["mandate_id"] == DEFAULT_MANDATE_ID for ev in feed["events"])
    run_ids = {ev.get("run_id") for ev in feed["events"] if ev["kind"] == "runtime_status_transition"}
    assert run_ids == {"run-a"}


def test_runtime_feed_unfiltered_shows_all():
    rt = build_runtime()
    _seed(rt)
    feed = CorpReadModel.from_runtime(rt).runtime_feed()
    run_ids = {ev.get("run_id") for ev in feed["events"]
               if ev["kind"] == "runtime_status_transition"}
    assert run_ids == {"run-a", "run-b", "run-c"}               # no filter ⇒ everything


def test_runtime_feed_unknown_job_fails_closed():
    rt = build_runtime()
    feed = CorpReadModel.from_runtime(rt).runtime_feed("no-such-job")
    assert feed["available"] is False and "unknown job" in feed["reason"]
    assert feed["events"] == []


# --- purity + live-read integration -----------------------------------------------

def test_corp_read_model_is_zero_write():
    rt = build_runtime()
    _seed(rt)
    before = len(list(rt.runtime.trace.replay()))
    CorpReadModel.from_runtime(rt).portfolio_view()
    CorpReadModel.from_runtime(rt).runtime_feed(JOB_ZERO_ID)
    after = len(list(rt.runtime.trace.replay()))
    assert after == before


def test_corp_via_live_read_registry():
    rt = build_runtime()
    _seed(rt)
    status, payload = LiveReadModels(rt).read("/read/corp/portfolio")
    assert status == 200 and payload["live"] is True and payload["model"] == "corp/portfolio"
    assert any(c["client_id"] == CLIENT_ZERO_ID for c in payload["clients"])
    assert payload["alerts"]["status"] == "UNAVAILABLE"

    status2, payload2 = LiveReadModels(rt).read("/read/corp/runtime?job=" + JOB_ZERO_ID)
    assert status2 == 200 and payload2["model"] == "corp/runtime"
    assert payload2["available"] is True
