"""F7.8 seal — the Approval Workbench read-model (context to decide).

Each pending item (F5.2 inbox) is enriched with its mandate summary, client/job
(F7.0), budget state (F7.1/F7.2), the job's open risks (F7.7), and the tool's
decision history (trace audit). Read-only composition: it adds no decision path —
the decision still goes only through F5.2 `decide`. Context with no source is
UNAVAILABLE, never fabricated. Flips the `full_approval_workbench` seam.
"""
from __future__ import annotations

from agentic_runtime.budget import BudgetLedger
from agentic_runtime.core_types import ApprovalReceiptRecord, RiskLevel
from agentic_runtime.corp import (
    CLIENT_ZERO_ID,
    CorpRegistry,
    JobRecord,
    RiskEntry,
    RiskStatus,
    client_zero,
    record_risk,
)
from agentic_runtime.front_server import (
    CLAIMS_FULL_APPROVAL_WORKBENCH,
    ApprovalWorkbenchReadModel,
)
from agentic_runtime.mandate import (
    Mandate,
    MandateRegistry,
    MandateScope,
    default_mandate,
)
from agentic_runtime.trace import InMemoryTraceLedger


class _StubInbox:
    def __init__(self, items):
        self._items = items

    def pending(self):
        return list(self._items)


def _mandate(mid="m-alpha"):
    return Mandate(mandate_id=mid, version="v1",
                   scope=MandateScope(paths=("clients/acme/",), client_id="acme",
                                      budget_cents=1000.0, allowed_tools=("write_file",),
                                      max_risk=RiskLevel.MEDIUM))


def _registry():
    mandate = _mandate()
    mreg = MandateRegistry.from_mandates([default_mandate(), mandate])
    job = JobRecord(job_id="job-a", client_id=CLIENT_ZERO_ID, mandate_ids=("m-alpha",))
    return CorpRegistry.from_records([client_zero()], [job], mandate_registry=mreg)


def _seed(trace, led):
    led.begin_run("run-a", "card-1", "i")
    led.set_mandate("m-alpha")
    led.charge_llm(usage=None, usd=1.00)                 # 100 cents spent under m-alpha
    record_risk(trace, RiskEntry(risk_id="rk1", job_id="job-a", client_id=CLIENT_ZERO_ID,
                                 likelihood=3, impact=4, tier=RiskLevel.HIGH))
    trace.append_approval_receipt(ApprovalReceiptRecord.make(
        run_id="run-a", issuer_card_id="card-1", request_id="old", receipt_id="rc1",
        tool="write_file", risk_class="high", outcome="approve", reason="ok",
        decided_by="operator", mandate_id="m-alpha"))


def _pending_item(mandate_id="m-alpha", tool="write_file", risk="medium", rid="rq1"):
    return {"request_id": rid, "tool": tool, "risk": risk, "summary": "s",
            "issuer": "card-1", "mandate_id": mandate_id}


def _workbench(inbox=None):
    trace = InMemoryTraceLedger("run-a")
    led = BudgetLedger()
    _seed(trace, led)
    return ApprovalWorkbenchReadModel(trace, _registry(), budget=led, inbox=inbox)


# --- enriched pending item ------------------------------------------------------

def test_pending_item_carries_full_context():
    wb = _workbench(_StubInbox([_pending_item()]))
    item = wb.items()[0]
    assert item["mandate"]["status"] == "AVAILABLE"
    assert item["mandate"]["paths"] == ["clients/acme/"]
    assert item["mandate"]["budget_cents"] == 1000.0
    assert item["attribution"]["job_id"] == "job-a"
    assert item["attribution"]["client_id"] == CLIENT_ZERO_ID
    assert item["budget"]["status"] == "AVAILABLE"
    assert round(item["budget"]["spent_cents"], 3) == 100.0
    assert round(item["budget"]["remaining_cents"], 3) == 900.0
    assert [r["risk_id"] for r in item["risks"]] == ["rk1"]
    assert item["history"] and item["history"][0]["outcome"] == "approve"


def test_context_without_source_is_unavailable():
    wb = _workbench(_StubInbox([_pending_item(mandate_id="ghost")]))
    item = wb.items()[0]
    assert item["mandate"]["status"] == "UNAVAILABLE"        # unknown mandate
    assert item["attribution"]["status"] == "UNAVAILABLE"    # maps to no job
    assert item["risks"] == []                               # honest, not fabricated


def test_items_sorted_by_risk_then_request_id():
    wb = _workbench(_StubInbox([
        _pending_item(risk="low", rid="a"),
        _pending_item(risk="critical", rid="b"),
        _pending_item(risk="low", rid="c"),
    ]))
    order = [(it["risk"], it["request_id"]) for it in wb.items()]
    assert order == [("critical", "b"), ("low", "a"), ("low", "c")]


# --- pending_source discipline (F5.5) -------------------------------------------

def test_no_inbox_pending_unavailable_but_history_live():
    wb = _workbench(inbox=None)
    d = wb.to_dict()
    assert d["items"] == [] and d["pending_source"] == "unavailable"
    # the trace-derived tool history is still available without an inbox
    assert d["tool_history"]["write_file"]["approve"] == 1


# --- read-only: no decision path ------------------------------------------------

def test_workbench_adds_no_decision_path():
    wb = _workbench(_StubInbox([_pending_item()]))
    # the workbench is a read model — it exposes no decide/submit/execute path.
    assert not hasattr(wb, "decide")
    assert not hasattr(wb, "submit")
    assert not hasattr(wb, "approve")


def test_flips_full_workbench_seam():
    wb = _workbench(_StubInbox([_pending_item()]))
    assert wb.to_dict()["claims_full_workbench"] is True
    assert CLAIMS_FULL_APPROVAL_WORKBENCH is True


# --- pending item carries mandate_id (F7.8 additive) ----------------------------

def test_pending_approval_dict_carries_mandate_id():
    from agentic_runtime.front_server.approval_inbox import PendingApproval
    p = PendingApproval(request_id="r", tool="t", risk="low", summary="s",
                        issuer="c", mandate_id="m-alpha")
    assert p.to_dict()["mandate_id"] == "m-alpha"
