"""F6.1 seal — mandate_id propagation into trace records (additive, byte-identical when empty)."""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import (
    ApprovalReceiptRecord,
    BudgetDecisionRecord,
    MemoryGovernanceRecord,
    PraxisEventRecord,
    RuntimeStatusTransitionRecord,
)
from agentic_runtime.front_server import ConversationEngine, ProposalDispatcher, SignalMessage
from agentic_runtime.front_server.conversation import (
    CONVERSATION_MESSAGE_EVENT,
    CONVERSATION_REPLY_EVENT,
)
from agentic_runtime.front_server.workops import WorkOpsMessage

_CONV_EVENTS = (CONVERSATION_MESSAGE_EVENT, CONVERSATION_REPLY_EVENT)


def _conv_praxis(trace):
    return [e for e in trace.replay()
            if e.get("kind") == "praxis_event" and e.get("event_type") in _CONV_EVENTS]


class StubRouter:
    def complete_with_usage(self, profile, system, user):
        return "ok", "stub-model", {"total_tokens": 5}


# --- additive: empty mandate_id ⇒ hash byte-identical to pre-F6 ------------------

def test_empty_mandate_id_leaves_payload_hash_unchanged():
    # A record with mandate_id="" must hash exactly as if the field did not exist,
    # so all pre-F6 traces stay valid.
    r0 = PraxisEventRecord.make(run_id="r", agent_id="a", event_type="e",
                                subject_id="s", summary="hi")
    r_empty = PraxisEventRecord.make(run_id="r", agent_id="a", event_type="e",
                                     subject_id="s", summary="hi", mandate_id="")
    assert r0.payload_hash() == r_empty.payload_hash()


def test_nonempty_mandate_id_changes_hash_and_appears():
    r = PraxisEventRecord.make(run_id="r", agent_id="a", event_type="e",
                               subject_id="s", summary="hi", mandate_id="M1")
    r0 = PraxisEventRecord.make(run_id="r", agent_id="a", event_type="e",
                                subject_id="s", summary="hi")
    assert r.payload_hash() != r0.payload_hash()
    assert r.mandate_id == "M1"


def test_all_five_records_carry_mandate_id():
    recs = [
        PraxisEventRecord.make("r", "a", "e", "s", "x", mandate_id="M"),
        ApprovalReceiptRecord.make("r", "c", "req", "rc", "tool", "R2", "approved",
                                   "ok", "op", mandate_id="M"),
        RuntimeStatusTransitionRecord.make("r", "i", "c", "planned", "running",
                                            "dispatch", "m", mandate_id="M"),
        MemoryGovernanceRecord.make("r", "a", "write", "allow", "mid", "", "candidate",
                                    "rc", "m", mandate_id="M"),
        BudgetDecisionRecord.make("r", "i", "c", "tokens", "allow", 1.0, 9.0,
                                  mandate_id="M"),
    ]
    for rec in recs:
        assert rec.mandate_id == "M"
        # non-empty mandate participates in the hash
        assert rec.payload_hash()


# --- replay surfaces mandate_id (only when non-empty) ----------------------------

def test_replay_surfaces_mandate_only_when_present():
    rt = build_runtime()
    trace = rt.runtime.trace
    trace.append_status_transition(RuntimeStatusTransitionRecord.make(
        "run-x", "i", "c", "planned", "running", "dispatch", "m", mandate_id="M9"))
    trace.append_status_transition(RuntimeStatusTransitionRecord.make(
        "run-y", "i", "c", "planned", "running", "dispatch", "m"))  # empty
    events = [e for e in trace.replay() if e.get("kind") == "runtime_status_transition"]
    by_run = {e["run_id"]: e for e in events}
    assert by_run["run-x"]["mandate_id"] == "M9"
    assert "mandate_id" not in by_run["run-y"]  # empty ⇒ omitted (byte-identical)


# --- conversation path: default sentinel stays byte-identical --------------------

def test_default_conversation_mandate_is_not_traced():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    d = ProposalDispatcher(rt, conversation_engine=engine)
    # default mandate_id="default" ⇒ trace stays byte-identical (mandate omitted).
    d.dispatch(SignalMessage("signal:main", "op", "operator", "default", (), "hi").to_proposal())
    praxis = _conv_praxis(rt.runtime.trace)
    assert praxis and all("mandate_id" not in e for e in praxis)


def test_mandate_id_survives_persistent_reload(tmp_path):
    from agentic_runtime.trace import PersistentTraceLedger

    led = PersistentTraceLedger(base_dir=str(tmp_path), run_id="run_p")
    led.append_status_transition(RuntimeStatusTransitionRecord.make(
        "run_p", "i", "c", "planned", "running", "dispatch", "m", mandate_id="M7"))
    led.append_status_transition(RuntimeStatusTransitionRecord.make(
        "run_p", "i", "c", "planned", "running", "dispatch", "m"))  # empty

    reloaded = PersistentTraceLedger(base_dir=str(tmp_path), run_id="run_p")
    events = [e for e in reloaded.replay() if e.get("kind") == "runtime_status_transition"]
    mandates = [e.get("mandate_id") for e in events]
    assert "M7" in mandates                          # non-empty survived reload
    assert any("mandate_id" not in e for e in events)  # empty stayed omitted


def test_real_conversation_mandate_is_traced():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter())
    d = ProposalDispatcher(rt, conversation_engine=engine)
    d.dispatch(WorkOpsMessage("task-1", "op", "operator", "mandate_client_x", (), "go").to_proposal())
    praxis = _conv_praxis(rt.runtime.trace)
    assert praxis and all(e["mandate_id"] == "mandate_client_x" for e in praxis)
