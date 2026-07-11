"""
proposal_dispatcher.py — the single reduction from UI intent to the kernel.

Every mutation the Front makes arrives here as a proposal and reduces to exactly
one of: a governed conversation turn (F5.C), a governed tool action via
`runtime.submit` (F5.2), or a read-only projection. It never touches a subsystem
directly.

  `converse` → `ConversationEngine.respond` (F5.3, when an engine is bound);
  `act` → `runtime.submit` two-phase (F5.2 skeleton). One door, two semantics.
"""
from __future__ import annotations

from typing import Any

# Proposal kinds the dispatcher will route.
KIND_CONVERSE = "converse"   # → ConversationEngine.respond (F5.C)
KIND_ACT = "act"             # → approval inbox → runtime.submit two-phase (F5.2)
KIND_DECIDE = "decide"       # → approval inbox decide (Phase B)
_KNOWN_KINDS = (KIND_CONVERSE, KIND_ACT, KIND_DECIDE)

_REQUIRED_CONVERSE = ("room_id", "operator_identity", "role", "mandate_id", "text")

_RISK = {"trivial": "trivial", "low": "low", "medium": "medium",
         "high": "high", "critical": "critical"}


class ProposalRejected(ValueError):
    """A malformed / unroutable proposal. Fail-closed — nothing is dispatched."""


class ProposalDispatcher:
    """Reduces a proposal to a governed path."""

    def __init__(self, runtime: Any, *, conversation_engine: Any = None,
                 approval_inbox: Any = None, card: Any = None,
                 aureleu: Any = None) -> None:
        # The kernel is the only executor; held for the `act` reduction.
        self._runtime = getattr(runtime, "runtime", runtime)
        self._engine = conversation_engine
        self._inbox = approval_inbox
        self._card = card
        self._aureleu = aureleu  # F6.4: role-fluid persona resolution (optional)

    def dispatch(self, proposal: Any) -> dict:
        """Validate + route a proposal. Fail-closed on shape."""
        if not isinstance(proposal, dict):
            raise ProposalRejected("proposal must be a JSON object")
        kind = proposal.get("kind")
        if kind not in _KNOWN_KINDS:
            raise ProposalRejected(f"unknown proposal kind {kind!r}")
        if kind == KIND_CONVERSE:
            return self._dispatch_converse(proposal)
        if kind == KIND_DECIDE:
            return self._dispatch_decide(proposal)
        return self._dispatch_act(proposal)

    def _dispatch_converse(self, proposal: dict) -> dict:
        # Import here to avoid a package import cycle (signal ↔ dispatcher).
        from .conversation import ConversationTurn

        for f in _REQUIRED_CONVERSE:
            if not proposal.get(f):
                raise ProposalRejected(f"converse proposal requires {f!r}")
        if self._engine is None:
            return {"accepted": True, "kind": KIND_CONVERSE,
                    "reduction": "ConversationEngine.respond (F5.C)", "wired": False}
        turn = ConversationTurn.make(
            proposal["room_id"], proposal["text"],
            operator_identity=proposal["operator_identity"],
            role=proposal["role"], mandate_id=proposal["mandate_id"],
            context_refs=tuple(proposal.get("context_refs", []) or []),
        )
        # F6.4: when AurelEU is bound and enabled, resolve the persona (a traced
        # switch) and hand the engine the compiled identity prompt; else F5 default.
        system = None
        persona_mode = None
        if self._aureleu is not None:
            from .aureleu import flag_enabled as _aureleu_on
            if _aureleu_on():
                res = self._aureleu.switch_persona(
                    turn.room_id, turn.role,
                    persona_ref=str(proposal.get("persona_ref", "") or ""),
                    operator_identity=turn.operator_identity)
                if res.valid:
                    system = res.system_prompt
                    persona_mode = res.mode
        reply = self._engine.respond(turn, system=system)
        out = {"accepted": True, "kind": KIND_CONVERSE, "wired": True,
               "turn_id": turn.turn_id, "reply": reply.to_dict()}
        if persona_mode is not None:
            out["persona_mode"] = persona_mode
        return out

    def _dispatch_act(self, proposal: dict) -> dict:
        # Accept either a direct {tool, args} or a plan's first step.
        steps = proposal.get("steps")
        step = steps[0] if isinstance(steps, list) and steps else proposal
        tool = step.get("tool")
        # F7-wire: a governed corp record (a risk entry) appends directly to the
        # trace like the Board journal — it is operator metadata, not a sandbox
        # tool action, so it never routes through runtime.submit.
        if str(tool) == "corp_risk_add":
            return self._dispatch_corp_risk_add(step, proposal)
        if str(tool) == "corp_create_environment":
            return self._dispatch_corp_create_environment(step, proposal)

        if self._inbox is None or self._card is None:
            return {"accepted": True, "kind": KIND_ACT,
                    "reduction": "approval inbox two-phase (F5.2)", "wired": False}
        from ..core_types import CommandEnvelope, RiskLevel

        if not tool:
            raise ProposalRejected("act proposal requires a 'tool'")
        risk = RiskLevel(_RISK.get(str(step.get("risk", "medium")), "medium"))
        cmd = CommandEnvelope.make(
            issuer_card_id=self._card.id, tool=str(tool),
            args=dict(step.get("args", {}) or {}),
            rationale=str(proposal.get("rationale", "front act proposal")),
            declared_risk=risk,
            expected_effect=str(proposal.get("expected_effect", tool)),
        )
        result = self._inbox.submit_act(cmd, self._card)
        return {"accepted": True, "kind": KIND_ACT, "wired": True, **result}

    def _dispatch_corp_risk_add(self, step: dict, proposal: dict) -> dict:
        """Append a governed Risk Register entry (F7.7) through the one door."""
        from ..corp import RiskEntry, record_risk

        args = dict(step.get("args", {}) or {})
        try:
            entry = RiskEntry.from_dict(args)
        except (ValueError, TypeError) as exc:
            raise ProposalRejected(f"invalid risk entry: {exc}") from exc
        rec = record_risk(self._runtime.trace, entry,
                          mandate_id=str(proposal.get("mandate_id", "") or ""))
        return {"accepted": True, "kind": KIND_ACT, "wired": True,
                "reduction": "governed corp risk record (F7.7)",
                "risk_id": entry.risk_id, "record_id": rec.id}

    def _dispatch_corp_create_environment(self, step: dict, proposal: dict) -> dict:
        """Create a governed environment (client + job + mandate) through the one door."""
        from ..corp import record_environment_from_payload

        try:
            rec, ids = record_environment_from_payload(
                self._runtime.trace, dict(step.get("args", {}) or {}),
                mandate_id=str(proposal.get("mandate_id", "") or ""))
        except (ValueError, TypeError) as exc:
            raise ProposalRejected(f"invalid environment: {exc}") from exc
        return {"accepted": True, "kind": KIND_ACT, "wired": True,
                "reduction": "governed corp environment (F7.6)",
                "record_id": rec.id, **ids}

    def _dispatch_decide(self, proposal: dict) -> dict:
        if self._inbox is None:
            raise ProposalRejected("no approval inbox bound")
        request_id = proposal.get("request_id")
        if not request_id:
            raise ProposalRejected("decide proposal requires 'request_id'")
        if "approve" not in proposal:
            raise ProposalRejected("decide proposal requires 'approve'")
        result = self._inbox.decide(str(request_id), bool(proposal["approve"]))
        return {"accepted": True, "kind": KIND_DECIDE, "wired": True, **result}
