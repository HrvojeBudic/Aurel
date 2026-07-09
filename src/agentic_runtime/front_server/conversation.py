"""
conversation.py — the governed LLM conversation engine (F5.C).

The core of "talk to the LLM through Signal / WorkOPS". A conversation turn is a
**governed operation through the one door**, not a bypass: the operator's message
and the model's reply are both traced; the context is assembled by the ContextLoom
(F4) — provenance + taint + budget — and its `context_ref` rides on every message;
the model call is budget-charged (F2 router, cassette by default). The reply is one
of three modes: ANSWER (conversational text), PROPOSE (a valid plan ⇒ a
`ProposalEnvelope{kind:act}` → approval → `runtime.submit`), or UNAVAILABLE (router
refused / no key / budget exhausted ⇒ an honest non-answer, never fabricated).

The contract is **next-gen-ready**: it carries the N1–N8 seams (context_refs,
source_refs, truth_label, profile, mandate, bitemporal stamp) from day one,
empty/default until each F5.N feature lands.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from ..budget import BudgetExceeded
from ..context_loom import assemble, bind_context_to_trace, make_context_item
from ..context_loom.loom import ContextBundle
from ..core_types import MemoryTruthState, PraxisEventRecord, new_id, now
from ..external_ingress import SourceKind
from ..memory_bitemporal import BiTemporalStamp
from ..plan_validator import PlanValidator

CONVERSATION_MESSAGE_EVENT = "conversation_message"
CONVERSATION_REPLY_EVENT = "conversation_reply"
_MARK = "CONV"

CHAT_SYSTEM = (
    "You are Aurel, a governed private operating system. Answer the operator "
    "concisely and honestly. If fulfilling the request requires tool actions, "
    "respond with a structured plan; otherwise answer in plain text."
)

_FLAG = "AUREL_FRONT_CONVERSATION"


def flag_enabled() -> bool:
    """True iff the conversation flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


class ReplyMode(str, Enum):
    ANSWER = "answer"
    PROPOSE = "propose"
    UNAVAILABLE = "unavailable"


def _stamp() -> BiTemporalStamp:
    t = now()
    return BiTemporalStamp(valid_from=t, transaction_from=t)


@dataclass(frozen=True)
class ConversationTurn:
    turn_id: str
    room_id: str
    operator_identity: str
    role: str
    mandate_id: str                       # N5 seam
    text: str
    context_refs: tuple[str, ...] = ()     # N1 seam (operator-attached refs)
    bitemporal_stamp: BiTemporalStamp = field(default_factory=_stamp)  # N8 seam
    created_at: float = field(default_factory=now)

    @staticmethod
    def make(
        room_id: str,
        text: str,
        *,
        operator_identity: str,
        role: str = "operator",
        mandate_id: str = "default",
        context_refs: tuple[str, ...] = (),
    ) -> "ConversationTurn":
        return ConversationTurn(
            turn_id=new_id("turn"),
            room_id=room_id,
            operator_identity=operator_identity,
            role=role,
            mandate_id=mandate_id,
            text=text,
            context_refs=tuple(context_refs),
        )


@dataclass(frozen=True)
class ConversationReply:
    mode: ReplyMode
    text: str
    context_ref: str
    source_refs: tuple[str, ...] = ()                    # N1 seam (per-claim provenance)
    truth_label: MemoryTruthState = MemoryTruthState.CANDIDATE  # N2 seam
    profile_used: str = ""                               # N3/N7 seam
    usage_substantiated: bool = False
    proposal: Optional[dict] = None                      # PROPOSE mode
    bitemporal_stamp: BiTemporalStamp = field(default_factory=_stamp)  # N8 seam

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "text": self.text,
            "context_ref": self.context_ref,
            "source_refs": list(self.source_refs),
            "truth_label": self.truth_label.value,
            "profile_used": self.profile_used,
            "usage_substantiated": self.usage_substantiated,
            "proposal": self.proposal,
        }


# A profile selector maps (turn, bundle) → model profile name. N3 replaces the
# default with the difficulty estimator.
ProfileSelector = Callable[[ConversationTurn, ContextBundle], str]


@dataclass(frozen=True)
class HistoryEntry:
    role: str
    text: str
    context_ref: str
    turn_id: str

    def to_dict(self) -> dict:
        return {"role": self.role, "text": self.text,
                "context_ref": self.context_ref, "turn_id": self.turn_id}


def _summary(room_id: str, turn_id: str, role: str, ref: str, text: str) -> str:
    return f"{_MARK}|{room_id}|{turn_id}|{role}|{ref}|{text}"


class RoomHistoryProjection:
    """Room message history reconstructed purely from the trace (no own store)."""

    @staticmethod
    def from_trace(trace: Any, room_id: str) -> list[HistoryEntry]:
        out: list[HistoryEntry] = []
        for ev in trace.replay():
            if ev.get("kind") != "praxis_event":
                continue
            if ev.get("event_type") not in (
                CONVERSATION_MESSAGE_EVENT, CONVERSATION_REPLY_EVENT
            ):
                continue
            summary = str(ev.get("summary", ""))
            if not summary.startswith(_MARK + "|"):
                continue
            parts = summary.split("|", 5)
            if len(parts) < 6 or parts[1] != room_id:
                continue
            out.append(HistoryEntry(role=parts[3], text=parts[5],
                                    context_ref=parts[4], turn_id=parts[2]))
        return out


class ConversationEngine:
    """Governed LLM turn: assemble context → model → traced reply."""

    def __init__(
        self,
        runtime: Any,
        router: Any,
        *,
        plan_validator: Optional[PlanValidator] = None,
        profile_selector: Optional[ProfileSelector] = None,
        default_profile: str = "balanced",
        memory_k: int = 5,
        max_context_tokens: Optional[int] = None,
        system: str = CHAT_SYSTEM,
    ) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self._router = router
        self._default_profile = default_profile
        self._selector = profile_selector or (lambda turn, bundle: default_profile)
        self._memory_k = memory_k
        self._max_tokens = max_context_tokens
        self._system = system
        self._validator = plan_validator or PlanValidator(
            registered_tools=set(getattr(self._inner.tools, "registered", set()))
        )

    def _assemble(self, turn: ConversationTurn) -> ContextBundle:
        items = []
        for entry in RoomHistoryProjection.from_trace(self._inner.trace, turn.room_id):
            items.append(make_context_item(
                f"[{entry.role}] {entry.text}", SourceKind.INTERNAL, "room_history"))
        try:
            for rec in self._inner.memory.retrieve(turn.text, self._memory_k):
                items.append(make_context_item(rec.content, SourceKind.INTERNAL, "memory"))
        except (AttributeError, TypeError):
            pass
        items.append(make_context_item(turn.text, SourceKind.OPERATOR, turn.operator_identity))
        return assemble(items, max_tokens=self._max_tokens, compress=True)

    def _record(self, event_type: str, turn: ConversationTurn, role: str,
                ref: str, text: str) -> None:
        self._inner.trace.append_praxis_event(PraxisEventRecord.make(
            run_id=self._inner.trace.run_id,
            agent_id=turn.operator_identity,
            event_type=event_type,
            subject_id=turn.turn_id,
            summary=_summary(turn.room_id, turn.turn_id, role, ref, text),
        ))

    def _classify(self, raw: str) -> tuple[ReplyMode, str, Optional[dict]]:
        # 1. Router refusal (no key / blocked / no model) ⇒ honest UNAVAILABLE.
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("refusal_reason"):
                return ReplyMode.UNAVAILABLE, str(data["refusal_reason"]), None
        except (ValueError, TypeError):
            data = None
        # 2. A valid plan ⇒ PROPOSE.
        result = self._validator.parse_and_validate(raw)
        if result.valid and result.steps:
            return ReplyMode.PROPOSE, "", {"kind": "act", "steps": list(result.steps)}
        # 3. Otherwise the raw text is the conversational answer.
        return ReplyMode.ANSWER, raw, None

    def respond(self, turn: ConversationTurn) -> ConversationReply:
        bundle = self._assemble(turn)
        bind_context_to_trace(
            self._inner.trace, run_id=self._inner.trace.run_id,
            agent_id=turn.operator_identity, subject_id=turn.turn_id, bundle=bundle)
        ref = bundle.context_ref
        self._record(CONVERSATION_MESSAGE_EVENT, turn, turn.role, ref, turn.text)

        profile = self._selector(turn, bundle)

        try:
            self._inner.budget.ensure_context(
                run_id=self._inner.trace.run_id,
                agent_id=turn.operator_identity,
                intent_id=turn.turn_id)
            self._inner.budget.precheck_llm()
        except BudgetExceeded as e:
            return self._unavailable(turn, ref, profile, f"budget: {e}")

        try:
            raw, _model, usage = self._router.complete_with_usage(
                profile, self._system, bundle.to_prompt())
        except Exception as e:  # provider failure ⇒ honest UNAVAILABLE, never fake
            return self._unavailable(turn, ref, profile, f"router: {e}")
        try:
            self._inner.budget.charge_llm(usage=usage)
        except BudgetExceeded:
            pass  # already spent; do not fabricate

        mode, text, proposal = self._classify(raw)
        if mode is ReplyMode.UNAVAILABLE:
            return self._unavailable(turn, ref, profile, text)
        reply = ConversationReply(
            mode=mode, text=text, context_ref=ref, profile_used=profile,
            usage_substantiated=usage is not None, proposal=proposal,
        )
        self._record(CONVERSATION_REPLY_EVENT, turn, "assistant", ref,
                     text if mode is ReplyMode.ANSWER else f"[{mode.value}]")
        return reply

    def _unavailable(self, turn: ConversationTurn, ref: str, profile: str,
                     reason: str) -> ConversationReply:
        self._record(CONVERSATION_REPLY_EVENT, turn, "assistant", ref, f"[unavailable] {reason}")
        return ConversationReply(
            mode=ReplyMode.UNAVAILABLE, text=reason, context_ref=ref,
            profile_used=profile, usage_substantiated=False)
