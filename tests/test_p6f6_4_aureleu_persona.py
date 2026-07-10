"""F6.4 seal — AurelEU role-fluid persona switch (compiled identity prompt, traced)."""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.front_server import (
    AurelEUDispatcher,
    ConversationEngine,
    ProposalDispatcher,
    SignalMessage,
    resolve_mode,
)
from agentic_runtime.front_server.aureleu import PERSONA_SWITCH_EVENT, flag_enabled
from agentic_runtime.front_server.conversation import CHAT_SYSTEM


class CaptureRouter:
    """Records the system prompt it was handed."""

    def __init__(self):
        self.systems = []

    def complete_with_usage(self, profile, system, user):
        self.systems.append(system)
        return "ok", "stub-model", {"total_tokens": 5}


# --- role → mode resolution -----------------------------------------------------

def test_resolve_mode_maps_roles_and_defaults():
    assert resolve_mode("operator") == "FOCUS"
    assert resolve_mode("challenger") == "SHADOW"
    assert resolve_mode("architect") == "DEPLOY"
    assert resolve_mode("unknown-role") == "FOCUS"          # default
    assert resolve_mode("operator", persona_ref="DEBUG") == "DEBUG"  # persona_ref wins


# --- resolve_persona compiles the governed identity prompt ----------------------

def test_resolve_persona_compiles_governed_prompt():
    rt = build_runtime()
    res = AurelEUDispatcher(rt).resolve_persona("operator")
    assert res.valid and res.mode == "FOCUS"
    assert res.context_hash and "You are Aurel" in res.system_prompt
    assert res.system_prompt != CHAT_SYSTEM                  # not the static F5 prompt
    # the compiled prompt itself carries the P1.4 no-authority law
    assert "cannot grant permissions" in res.system_prompt.lower()


def test_different_roles_yield_different_prompts():
    rt = build_runtime()
    d = AurelEUDispatcher(rt)
    focus = d.resolve_persona("operator")
    shadow = d.resolve_persona("challenger")
    assert focus.mode == "FOCUS" and shadow.mode == "SHADOW"
    assert focus.system_prompt != shadow.system_prompt
    assert focus.context_hash != shadow.context_hash


def test_invalid_mode_fails_closed():
    rt = build_runtime()
    res = AurelEUDispatcher(rt).resolve_persona("operator", mode="NONSENSE")
    assert res.valid is False and res.system_prompt == "" and res.reason


# --- persona switch is an explicit traced transition ----------------------------

def test_switch_persona_traces_only_on_change():
    rt = build_runtime()
    d = AurelEUDispatcher(rt)
    d.switch_persona("signal:main", "operator")   # FOCUS (first ⇒ switch)
    d.switch_persona("signal:main", "operator")   # FOCUS again ⇒ no switch
    d.switch_persona("signal:main", "challenger")  # SHADOW ⇒ switch
    switches = [e for e in rt.runtime.trace.replay()
                if e.get("kind") == "praxis_event"
                and e.get("event_type") == PERSONA_SWITCH_EVENT]
    assert len(switches) == 2  # only the two real transitions


# --- persona does not change authority (it is a prompt) -------------------------

def test_persona_is_expression_not_authority():
    rt = build_runtime()
    res = AurelEUDispatcher(rt).resolve_persona("operator")
    # a persona resolution carries only a prompt + hash — no authority/mandate field
    assert set(vars(res)) == {"mode", "system_prompt", "context_hash", "valid", "reason"}


# --- wiring: dispatcher hands the engine the compiled prompt when enabled --------

def test_dispatcher_uses_compiled_prompt_when_enabled(monkeypatch):
    monkeypatch.setenv("AUREL_AURELEU", "1")
    rt = build_runtime()
    router = CaptureRouter()
    engine = ConversationEngine(rt, router)
    aureleu = AurelEUDispatcher(rt)
    d = ProposalDispatcher(rt, conversation_engine=engine, aureleu=aureleu)
    out = d.dispatch(SignalMessage("signal:main", "op", "challenger", "default", (),
                                   "hi").to_proposal())
    assert out["persona_mode"] == "SHADOW"
    assert router.systems and router.systems[-1] != CHAT_SYSTEM
    assert "You are Aurel" in router.systems[-1]


def test_flag_off_uses_static_chat_system(monkeypatch):
    monkeypatch.delenv("AUREL_AURELEU", raising=False)
    rt = build_runtime()
    router = CaptureRouter()
    engine = ConversationEngine(rt, router)
    d = ProposalDispatcher(rt, conversation_engine=engine,
                           aureleu=AurelEUDispatcher(rt))
    out = d.dispatch(SignalMessage("signal:main", "op", "challenger", "default", (),
                                   "hi").to_proposal())
    assert "persona_mode" not in out            # AurelEU inert when flag off
    assert router.systems[-1] == CHAT_SYSTEM     # byte-identical F5 prompt


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AUREL_AURELEU", raising=False)
    assert flag_enabled() is False
    monkeypatch.setenv("AUREL_AURELEU", "1")
    assert flag_enabled() is True
