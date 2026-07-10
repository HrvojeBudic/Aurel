"""F6.7 seal — DN mechanisms (b): challenger pass + anti-stagnation tripwire + aurel panic."""
from __future__ import annotations

from agentic_runtime import build_runtime
from agentic_runtime.core_types import RuntimeStatusTransitionRecord
from agentic_runtime.dn import (
    ChallengerPass,
    check_stagnation,
    panic,
    panic_events_from_trace,
)


class StubRouter:
    def __init__(self, raw="Assumption X is unproven; a cheaper plan exists."):
        self._raw = raw
        self.calls = []

    def complete_with_usage(self, profile, system, user):
        self.calls.append((profile, system, user))
        return self._raw, "challenger-model", {"total_tokens": 8}


class BoomRouter:
    def complete_with_usage(self, profile, system, user):
        raise RuntimeError("provider down")


# --- challenger pass: advisory, honest ------------------------------------------

def test_challenger_surfaces_dissent_advisory():
    c = ChallengerPass(StubRouter()).challenge("plan: rm -rf everything")
    assert c.advisory is True and c.available is True
    assert "cheaper plan" in c.dissent and c.model == "challenger-model"


def test_challenger_router_failure_is_unavailable():
    c = ChallengerPass(BoomRouter()).challenge("plan")
    assert c.available is False and "unavailable" in c.dissent.lower()
    assert c.advisory is True  # never a fabricated endorsement


def test_challenger_does_not_execute():
    router = StubRouter()
    ChallengerPass(router).challenge("plan")
    # the only call is the advisory completion — no tool/runtime invocation
    assert len(router.calls) == 1


# --- anti-stagnation tripwire ---------------------------------------------------

def _seed_transitions(rt, pairs):
    for to, rc in pairs:
        rt.runtime.trace.append_status_transition(RuntimeStatusTransitionRecord.make(
            "run", "i", "c", "running", to, rc, "m"))


def test_tripwire_fires_on_stagnation():
    rt = build_runtime()
    _seed_transitions(rt, [("blocked", "retry")] * 3)
    res = check_stagnation(rt.runtime.trace, repeat_threshold=3)
    assert res.triggered is True and res.streak >= 3 and "anti-stagnation" in res.reason


def test_tripwire_quiet_on_progress():
    rt = build_runtime()
    _seed_transitions(rt, [("blocked", "retry"), ("succeeded", "ok"),
                           ("blocked", "retry")])  # progress breaks the streak
    assert check_stagnation(rt.runtime.trace, repeat_threshold=3).triggered is False


# --- aurel panic: governed kill-switch ------------------------------------------

def test_panic_records_governed_halt():
    rt = build_runtime()
    result = panic(rt, "runaway loop", invoked_by="operator")
    assert result.halted is True and result.dropped_to_g0 is True
    events = panic_events_from_trace(rt.runtime.trace)
    assert events == [{"invoked_by": "operator", "reason": "runaway loop"}]


def test_panic_is_never_silent():
    rt = build_runtime()
    before = len(list(rt.runtime.trace.replay()))
    panic(rt, "halt")
    after = len(list(rt.runtime.trace.replay()))
    assert after == before + 1  # exactly one governed record, never silent
