"""F7.4 seal — Operations.Evidence Vault (trace search + receipt bundle export).

Read-only over the trace: search by mandate/client/kind/run, and export a
self-contained Output-Passport bundle whose `verified` flag comes only from a real
P5 hash-chain verification (True iff PASS). A tampered trace verifies FAIL ⇒ the
bundle is not verified, and the chain head makes the tamper visible. Zero writes.
"""
from __future__ import annotations

from agentic_runtime.core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    RuntimeStatusTransitionRecord,
)
from agentic_runtime.corp import (
    CLIENT_ZERO_ID,
    CorpRegistry,
    EvidenceVaultQuery,
    JobRecord,
    client_zero,
)
from agentic_runtime.mandate import DEFAULT_MANDATE_ID
from agentic_runtime.trace import InMemoryTraceLedger


def _seed(trace, mandate="m-alpha"):
    trace.append_status_transition(RuntimeStatusTransitionRecord.make(
        run_id="run-a", intent_id="i", issuer_card_id="c", from_status="planned",
        to_status="running", reason_code="dispatch", message="m", mandate_id=mandate))
    trace.append_budget_decision(BudgetDecisionRecord.make(
        run_id="run-a", intent_id="i", issuer_card_id="c", metric="max_llm_calls",
        verdict="allow", used=1, limit=40, mandate_id=mandate))
    trace.append_approval_receipt(ApprovalReceiptRecord.make(
        run_id="run-a", issuer_card_id="c", request_id="rq1", receipt_id="rc1",
        tool="write_file", risk_class="high", outcome="approve", reason="ok",
        decided_by="operator", mandate_id=mandate))
    # an unrelated event under a different mandate
    trace.append_budget_decision(BudgetDecisionRecord.make(
        run_id="run-b", intent_id="i", issuer_card_id="c", metric="max_llm_calls",
        verdict="allow", used=1, limit=40, mandate_id="m-other"))


def _registry(mandate="m-alpha"):
    # No mandate_registry ⇒ the m-alpha reference is unchecked; the Vault only needs
    # the job → mandate_ids → client structure, not mandate resolution.
    job = JobRecord(job_id="job-a", client_id=CLIENT_ZERO_ID, mandate_ids=(mandate,))
    return CorpRegistry.from_records([client_zero()], [job])


# --- search ---------------------------------------------------------------------

def test_search_by_mandate_returns_exact_records():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    res = EvidenceVaultQuery(trace).search(mandate_id="m-alpha")
    assert res["count"] == 3                              # 3 m-alpha records, not the m-other one
    assert all(ev["mandate_id"] == "m-alpha" for ev in res["events"])
    assert all(ev["content_ref"].startswith("ev-") for ev in res["events"])


def test_search_by_client_via_registry():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    res = EvidenceVaultQuery(trace, _registry()).search(client_id=CLIENT_ZERO_ID)
    assert res["count"] == 3                              # klijent nula's job → m-alpha
    assert {ev["mandate_id"] for ev in res["events"]} == {"m-alpha"}


def test_search_by_kind():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    res = EvidenceVaultQuery(trace).search(kind="approval_receipt")
    assert res["count"] == 1 and res["events"][0]["kind"] == "approval_receipt"


def test_empty_result_is_empty_not_unavailable():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    res = EvidenceVaultQuery(trace).search(mandate_id="nobody")
    assert res["count"] == 0 and res["events"] == []


def test_search_limit_truncates_honestly():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    res = EvidenceVaultQuery(trace).search(mandate_id="m-alpha", limit=2)
    assert res["count"] == 2 and res["truncated"] is True


# --- receipt bundle export (Output Passport) ------------------------------------

def test_export_bundle_has_receipt_and_chain_head_and_verifies():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    bundle = EvidenceVaultQuery(trace, _registry()).export_receipt_bundle(job_id="job-a")
    assert bundle["output_passport"] is True
    assert bundle["event_count"] == 3                    # job-a → m-alpha events
    assert bundle["chain_head_hash"]                      # real chain head present
    assert bundle["verified"] is True                    # intact chain PASSes
    assert bundle["verification"]["status"] == "PASS"
    assert bundle["verification"]["truth_label"] == "TRACE_INTEGRITY_VERIFIED"


def test_export_unknown_job_fails_closed():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    bundle = EvidenceVaultQuery(trace, _registry()).export_receipt_bundle(job_id="ghost")
    assert bundle["available"] is False and "unknown job" in bundle["reason"]


def test_tampered_trace_is_not_verified():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    q = EvidenceVaultQuery(trace, _registry())
    assert q.export_receipt_bundle(job_id="job-a")["verified"] is True
    # tamper a record's content after it was hash-chained
    trace._entries[0].to_status = "hacked"
    tampered = q.export_receipt_bundle(job_id="job-a")
    assert tampered["verified"] is False                 # verified only from a real PASS
    assert tampered["verification"]["status"] != "PASS"


# --- read-only ------------------------------------------------------------------

def test_vault_is_zero_write():
    trace = InMemoryTraceLedger("run-x")
    _seed(trace)
    before = len(list(trace.replay()))
    q = EvidenceVaultQuery(trace, _registry())
    q.search(mandate_id="m-alpha")
    q.export_receipt_bundle(job_id="job-a")
    assert len(list(trace.replay())) == before


def test_default_mandate_job_export():
    # klijent nula default job under DEFAULT_MANDATE_ID exports cleanly.
    from agentic_runtime.corp import default_corp_registry
    trace = InMemoryTraceLedger("run-x")
    _seed(trace, mandate=DEFAULT_MANDATE_ID)
    bundle = EvidenceVaultQuery(trace, default_corp_registry()).export_receipt_bundle(
        job_id="job-zero")
    assert bundle["event_count"] == 3 and bundle["verified"] is True
