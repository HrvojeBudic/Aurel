"""F7 corp_create_environment — governed environment creation + trace-projected registry.

Closes the third F7 forward seam: the Agency wizard (F7.6) can now actually CREATE
an environment through the one door. A created {client + job + mandate} is a governed
trace record, and the Corp registry the read models use is rebuilt from the trace —
so the created client/job appears in the portfolio and its cost attributes. With no
environment events the registry is byte-identical to klijent nula (the default).
"""
from __future__ import annotations

import pytest

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RiskLevel
from agentic_runtime.corp import (
    CLIENT_ZERO_ID,
    JOB_ZERO_ID,
    corp_registry_from_trace,
    default_corp_registry,
    record_environment,
)
from agentic_runtime.corp.wizard import EnvironmentTemplate
from agentic_runtime.front_server import CorpReadModel, LiveReadModels, ProposalDispatcher
from agentic_runtime.front_server.proposal_dispatcher import ProposalRejected
from agentic_runtime.mandate import MandateScope
from agentic_runtime.trace import InMemoryTraceLedger


def _template():
    return EnvironmentTemplate(
        client_name="Acme", job_title="Repo Y work",
        scope=MandateScope(paths=("clients/acme/",), budget_cents=1000.0,
                           allowed_tools=("write_file",), max_risk=RiskLevel.MEDIUM),
        persona_ref="advisor", repos=("repoY",))


# --- byte-identical baseline ------------------------------------------------------

def test_empty_trace_registry_is_klijent_nula():
    reg = corp_registry_from_trace(InMemoryTraceLedger("r"))
    assert reg.client_ids() == (CLIENT_ZERO_ID,)
    assert reg.job_ids() == (JOB_ZERO_ID,)
    # same shape as the static default
    assert reg.canonical_hash() == default_corp_registry().canonical_hash()


# --- governed creation ⇒ projected registry --------------------------------------

def test_record_environment_appears_in_projected_registry():
    trace = InMemoryTraceLedger("r")
    rec, ids = record_environment(
        trace, client_name="Acme", job_title="Repo Y work",
        scope=_template().scope, persona_ref="advisor", repos=("repoY",))
    reg = corp_registry_from_trace(trace)
    # klijent nula + the created client both present
    assert CLIENT_ZERO_ID in reg.client_ids() and ids["client_id"] in reg.client_ids()
    job = reg.resolve_job(ids["job_id"])
    assert job.client_id == ids["client_id"] and job.mandate_ids == (ids["mandate_id"],)
    # the created mandate is resolvable (so cost/budget can attribute)
    assert reg.mandate_registry.resolve(ids["mandate_id"]) is not None


def test_creation_is_deterministic_and_replayable():
    t1, t2 = InMemoryTraceLedger("a"), InMemoryTraceLedger("b")
    _, ids1 = record_environment(t1, client_name="Acme", job_title="J",
                                 scope=_template().scope)
    _, ids2 = record_environment(t2, client_name="Acme", job_title="J",
                                 scope=_template().scope)
    assert ids1 == ids2                    # content-hashed ids ⇒ deterministic


# --- through the one door (wizard → dispatcher → portfolio) -----------------------

def test_wizard_proposal_creates_environment_end_to_end():
    rt = build_runtime()
    dispatcher = ProposalDispatcher(rt)
    res = dispatcher.dispatch(_template().to_proposal())
    assert res["accepted"] is True and res["wired"] is True
    assert "governed corp environment" in res["reduction"]
    created_client = res["client_id"]

    # the created environment now shows in the CORP portfolio read model
    view = CorpReadModel.from_runtime(rt).portfolio_view()
    ids = {c["client_id"] for c in view["clients"]}
    assert created_client in ids and CLIENT_ZERO_ID in ids


def test_create_environment_via_live_read_registry():
    rt = build_runtime()
    ProposalDispatcher(rt).dispatch(_template().to_proposal())
    status, payload = LiveReadModels(rt).read("/read/corp/portfolio")
    assert status == 200
    names = {c["name"] for c in payload["clients"]}
    assert "Acme" in names


def test_invalid_environment_fails_closed():
    rt = build_runtime()
    bad = {"kind": "act", "tool": "corp_create_environment",
           "args": {"client_name": "", "job_title": "J", "scope": {}}}   # empty client
    with pytest.raises(ProposalRejected):
        ProposalDispatcher(rt).dispatch(bad)
