"""F5.C seal — the governed LLM conversation engine (talk to the LLM)."""
from __future__ import annotations

import json

from agentic_runtime import build_runtime
from agentic_runtime.context_loom import context_refs_from_replay
from agentic_runtime.core_types import MemoryTruthState
from agentic_runtime.front_server.conversation import (
    ConversationEngine,
    ConversationTurn,
    ReplyMode,
    RoomHistoryProjection,
    flag_enabled,
)
from agentic_runtime.model_providers.schemas import refusal_json

PLAN = json.dumps({"plan": [{"tool": "list_dir", "args": {"path": "."}, "reason": "look"}]})


class StubRouter:
    def __init__(self, raw, usage=None):
        self._raw = raw
        self._usage = usage if usage is not None else {"total_tokens": 12}
        self.last_prompt = None

    def complete_with_usage(self, profile, system, user):
        self.last_prompt = user
        return self._raw, "stub-model", self._usage


class BoomRouter:
    def complete_with_usage(self, profile, system, user):
        raise RuntimeError("provider down")


def _turn(text, room="signal:main"):
    return ConversationTurn.make(room, text, operator_identity="op", mandate_id="m1")


def test_answer_mode_records_and_binds_context():
    rt = build_runtime()
    router = StubRouter("The tests live under tests/.")
    reply = ConversationEngine(rt, router).respond(_turn("where do tests live?"))
    assert reply.mode is ReplyMode.ANSWER
    assert reply.text == "The tests live under tests/."
    assert reply.context_ref and reply.usage_substantiated is True
    assert "where do tests live?" in router.last_prompt
    assert reply.context_ref in context_refs_from_replay(rt.runtime.trace.replay())


def test_next_gen_ready_contract_fields():
    rt = build_runtime()
    reply = ConversationEngine(rt, StubRouter("hi")).respond(_turn("hello"))
    assert reply.truth_label is MemoryTruthState.CANDIDATE
    assert reply.bitemporal_stamp.valid_from is not None
    assert reply.profile_used
    assert reply.source_refs == ()


def test_propose_mode_emits_proposal_not_execution():
    rt = build_runtime()
    reply = ConversationEngine(rt, StubRouter(PLAN)).respond(_turn("list the repo"))
    assert reply.mode is ReplyMode.PROPOSE
    assert reply.proposal["kind"] == "act"
    assert reply.proposal["steps"][0]["tool"] == "list_dir"


def test_router_refusal_is_unavailable():
    rt = build_runtime()
    reply = ConversationEngine(rt, StubRouter(refusal_json("no api key"))).respond(_turn("hi"))
    assert reply.mode is ReplyMode.UNAVAILABLE
    assert "no api key" in reply.text
    assert reply.usage_substantiated is False


def test_provider_failure_is_unavailable():
    rt = build_runtime()
    reply = ConversationEngine(rt, BoomRouter()).respond(_turn("hi"))
    assert reply.mode is ReplyMode.UNAVAILABLE
    assert "provider down" in reply.text


def test_room_history_reconstructed_from_trace():
    rt = build_runtime()
    engine = ConversationEngine(rt, StubRouter("first answer"))
    engine.respond(_turn("first question", room="signal:main"))
    engine.respond(_turn("second question", room="signal:main"))
    engine.respond(_turn("other room", room="workops:1"))
    hist = RoomHistoryProjection.from_trace(rt.runtime.trace, "signal:main")
    assert [h.role for h in hist] == ["operator", "assistant", "operator", "assistant"]
    texts = [h.text for h in hist]
    assert "first question" in texts and "first answer" in texts
    assert all("other room" not in t for t in texts)


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_FRONT_CONVERSATION", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_FRONT_CONVERSATION", "1")
    assert flag_enabled() is True
