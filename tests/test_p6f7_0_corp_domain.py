"""F7.0 seal — the Corp business domain (Client/Job registry + klijent nula).

The Business Plane wraps the mature governance machinery in a thin business layer:
a job references mandates (reused, never copied), a job cannot hide who it is for
(no-overclaim), and the registry validates every client + mandate reference at
build time, fail-closed. Klijent nula (the own repo) is the honest seed.
"""
from __future__ import annotations

import pytest

from agentic_runtime.corp import (
    CLIENT_ZERO_ID,
    JOB_ZERO_ID,
    ClientRecord,
    CorpRegistry,
    CorpValidationError,
    ClientNotFound,
    JobNotFound,
    JobRecord,
    JobStatus,
    client_zero,
    client_zero_job,
    default_corp_registry,
    flag_enabled,
)
from agentic_runtime.mandate import DEFAULT_MANDATE_ID, default_registry


# --- construction / no-overclaim ------------------------------------------------

def test_job_requires_non_empty_client_id():
    # A job cannot hide who it is for (structural no-overclaim).
    with pytest.raises(ValueError):
        JobRecord(job_id="j", client_id="")
    with pytest.raises(ValueError):
        JobRecord(job_id="", client_id="c")


def test_job_requires_closed_world_status():
    with pytest.raises(TypeError):
        JobRecord(job_id="j", client_id="c", status="active")  # type: ignore[arg-type]


def test_client_requires_id_and_name():
    with pytest.raises(ValueError):
        ClientRecord(client_id="", name="x")
    with pytest.raises(ValueError):
        ClientRecord(client_id="c", name="")


def test_make_mints_ids_and_carries_fields():
    c = ClientRecord.make("Acme", notes="n")
    assert c.client_id.startswith("client_") and c.name == "Acme"
    j = JobRecord.make(c.client_id, mandate_ids=("m1",), repos=("repoY",),
                       status=JobStatus.PROPOSED, title="t")
    assert j.job_id.startswith("job_") and j.client_id == c.client_id
    assert j.mandate_ids == ("m1",) and j.repos == ("repoY",)
    assert j.status is JobStatus.PROPOSED


# --- content hashing ------------------------------------------------------------

def test_content_hash_is_deterministic_and_content_addressed():
    a = client_zero()
    b = client_zero()
    assert a.content_hash == b.content_hash          # same content ⇒ same hash
    assert "created_at" not in a._hashable()          # content identity, not timestamp

    j1 = JobRecord(job_id="j", client_id="c", mandate_ids=("m1",))
    j2 = JobRecord(job_id="j", client_id="c", mandate_ids=("m1", "m2"))
    assert j1.content_hash != j2.content_hash          # mandate-set change ⇒ new hash
    assert "created_at" not in j1._hashable()


# --- registry resolution (fail-closed) ------------------------------------------

def test_registry_resolves_and_fails_closed():
    c = client_zero()
    j = client_zero_job()
    reg = CorpRegistry.from_records([c], [j], mandate_registry=default_registry())
    assert reg.resolve_client(CLIENT_ZERO_ID).client_id == CLIENT_ZERO_ID
    assert reg.resolve_job(JOB_ZERO_ID).job_id == JOB_ZERO_ID
    assert reg.resolve_client("nope") is None          # fail-closed
    assert reg.resolve_job("nope") is None
    with pytest.raises(ClientNotFound):
        reg.resolve_client_or_raise("nope")
    with pytest.raises(JobNotFound):
        reg.resolve_job_or_raise("nope")
    assert reg.client_ids() == (CLIENT_ZERO_ID,)
    assert reg.job_ids() == (JOB_ZERO_ID,)


def test_build_rejects_unknown_client_reference():
    # A job pointing at a client that does not exist is un-buildable.
    orphan = JobRecord(job_id="j", client_id="ghost")
    with pytest.raises(CorpValidationError):
        CorpRegistry.from_records([client_zero()], [orphan])


def test_build_rejects_unknown_mandate_reference():
    # A job pointing at authority that does not exist is un-buildable (fail-closed).
    bad = JobRecord(job_id="j", client_id=CLIENT_ZERO_ID, mandate_ids=("no-such-mandate",))
    with pytest.raises(CorpValidationError):
        CorpRegistry.from_records([client_zero()], [bad], mandate_registry=default_registry())


def test_build_skips_mandate_validation_without_registry():
    # No mandate_registry ⇒ mandate refs can't be validated, so they're not (honest).
    j = JobRecord(job_id="j", client_id=CLIENT_ZERO_ID, mandate_ids=("unchecked",))
    reg = CorpRegistry.from_records([client_zero()], [j])
    assert reg.resolve_job("j").mandate_ids == ("unchecked",)


# --- jobs_for_client / determinism ----------------------------------------------

def test_jobs_for_client_is_deterministic():
    c = client_zero()
    j_b = JobRecord(job_id="job-b", client_id=CLIENT_ZERO_ID)
    j_a = JobRecord(job_id="job-a", client_id=CLIENT_ZERO_ID)
    reg = CorpRegistry.from_records([c], [j_b, j_a], mandate_registry=default_registry())
    ids = tuple(j.job_id for j in reg.jobs_for_client(CLIENT_ZERO_ID))
    assert ids == ("job-a", "job-b")                   # sorted, order-independent
    assert reg.jobs_for_client("nobody") == ()


def test_registry_hash_deterministic():
    c = client_zero()
    j = client_zero_job()
    r1 = CorpRegistry.from_records([c], [j], mandate_registry=default_registry())
    r2 = CorpRegistry.from_records([c], [j], mandate_registry=default_registry())
    assert r1.canonical_hash() == r2.canonical_hash()


# --- klijent nula seed ----------------------------------------------------------

def test_default_corp_registry_resolves_client_zero():
    reg = default_corp_registry()
    assert reg.resolve_client(CLIENT_ZERO_ID).name.startswith("Klijent nula")
    job = reg.resolve_job(JOB_ZERO_ID)
    assert job.client_id == CLIENT_ZERO_ID
    assert job.mandate_ids == (DEFAULT_MANDATE_ID,)     # references real authority
    # The seed's mandate reference is validated against the mandate default registry.
    assert reg.mandate_registry.resolve(DEFAULT_MANDATE_ID) is not None


# --- flag -----------------------------------------------------------------------

def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_CORP", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_CORP", "1")
    assert flag_enabled() is True
