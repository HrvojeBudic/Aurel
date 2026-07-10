"""
aureleu.py — the AurelEU role-fluid dispatcher (F6.4).

AurelEU is not a new executor — it is the resolution layer *inside* the one door:
given a message's `(role, mandate)`, it resolves the persona/mode and compiles the
governed identity prompt (reusing the P1.4 `identity_prompt_compiler`, which already
enforces the cross-layer dominance kernel > contract > persona > mode). A persona
switch is an **explicit, traced transition** (`persona_switch`), never silent.

Doctrine (P1.4): persona is *expression*, not authority. AurelEU changes how Aurel
speaks (the system prompt), never what it may do — authority is the mandate (F6.2),
and the compiled prompt itself carries the "persona cannot grant permissions" law.
When the compiler reports a contradiction, resolution fails **closed** (no prompt).

Additive behind `AUREL_AURELEU`: OFF ⇒ the conversation engine uses the static
CHAT_SYSTEM (F5, byte-identical). This slice flips the F5 seam
`claims_aureleu_dispatcher_live` from False to live.
"""
from __future__ import annotations

import os
import types as _types
from dataclasses import dataclass
from typing import Any, Optional

from ..core_types import PraxisEventRecord, RiskLevel
from ..identity.autonomy_scale_engine import AutonomyLevel
from ..prompts.identity_context_compiler import compile_identity_prompt_context_from_paths

_FLAG = "AUREL_AURELEU"
PERSONA_SWITCH_EVENT = "persona_switch"
CONSTITUTION_VIOLATION_EVENT = "constitution_violation"
_MARK = "PERS"
_CVIO_MARK = "CVIO"

_VALID_MODES = ("FOCUS", "DEBUG", "DEPLOY", "SHADOW", "EVOLVE", "CHANNEL", "HERETIC")
_ROLE_TO_MODE = {
    "operator": "FOCUS",
    "architect": "DEPLOY",
    "deploy": "DEPLOY",
    "challenger": "SHADOW",
    "shadow": "SHADOW",
    "debug": "DEBUG",
    "evolve": "EVOLVE",
    "channel": "CHANNEL",
}
_DEFAULT_MODE = "FOCUS"

# The sections composed into the system prompt (order = dominance top→bottom).
_PROMPT_SECTIONS = (
    "agent_identity_section",
    "operator_relationship_section",
    "persona_expression_section",
    "active_mode_section",
    "authority_boundaries_section",
    "capability_honesty_section",
    "non_goals_section",
)


def flag_enabled() -> bool:
    """True iff the AurelEU flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


def resolve_mode(role: str, persona_ref: str = "") -> str:
    """Map (role, mandate persona_ref) → a communication mode. Defaults to FOCUS."""
    for cand in (persona_ref, role):
        if not cand:
            continue
        up = cand.upper()
        if up in _VALID_MODES:
            return up
        low = cand.lower()
        if low in _ROLE_TO_MODE:
            return _ROLE_TO_MODE[low]
    return _DEFAULT_MODE


def _render(context: Any) -> str:
    lines: list[str] = []
    for name in _PROMPT_SECTIONS:
        lines.extend(getattr(context, name, ()) or ())
    return "\n".join(lines)


@dataclass(frozen=True)
class PersonaResolution:
    """The resolved persona for a turn. `valid=False` ⇒ fail-closed (no prompt)."""

    mode: str
    system_prompt: str
    context_hash: str
    valid: bool
    reason: str = ""


@dataclass(frozen=True)
class DispatchAuthorization:
    """Pre-dispatch verdict: a sub-agent dispatch needs authority + autonomy."""

    allowed: bool
    mandate_id: str = ""
    cited_delegation_id: str = ""
    reason: str = ""
    drop_to_g0: bool = False

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "mandate_id": self.mandate_id,
                "cited_delegation_id": self.cited_delegation_id,
                "reason": self.reason, "drop_to_g0": self.drop_to_g0}


class AurelEUDispatcher:
    """Resolves persona/mode and compiles the governed identity prompt, one door."""

    def __init__(self, runtime: Any) -> None:
        self._inner = getattr(runtime, "runtime", runtime)
        self._current: dict[str, str] = {}  # room_id → current mode (operational)

    def resolve_persona(self, role: str, persona_ref: str = "", *,
                        mode: Optional[str] = None) -> PersonaResolution:
        """Compile the identity prompt for (role, mandate). Fail-closed on contradiction."""
        selected = mode or resolve_mode(role, persona_ref)
        result = compile_identity_prompt_context_from_paths(selected)
        if not result.valid or result.context is None:
            reason = "; ".join(result.critical_failures or result.errors) or "compile failed"
            return PersonaResolution(selected, "", "", False, reason=reason)
        return PersonaResolution(
            selected, _render(result.context), result.context_hash or "", True)

    def switch_persona(self, room_id: str, role: str, *, persona_ref: str = "",
                       operator_identity: str = "operator") -> PersonaResolution:
        """Resolve + record an explicit persona switch when the mode changes."""
        res = self.resolve_persona(role, persona_ref)
        prev = self._current.get(room_id)
        if res.valid and res.mode != prev:
            self._inner.trace.append_praxis_event(PraxisEventRecord.make(
                run_id=self._inner.trace.run_id, agent_id=operator_identity,
                event_type=PERSONA_SWITCH_EVENT, subject_id=room_id,
                summary=f"{_MARK}|{room_id}|{prev or ''}|{res.mode}|{res.context_hash}"))
            self._current[room_id] = res.mode
        return res

    # -- F6.5: Constitution ↔ dispatch wiring -------------------------------- #
    def authorize_dispatch(
        self, *, mandate_id: str, autonomy_level: AutonomyLevel, category: str,
        at: float, tool: Optional[str] = None, path: Optional[str] = None,
        risk: Optional[RiskLevel] = None, operator_identity: str = "operator",
    ) -> DispatchAuthorization:
        """Before dispatching a sub-agent (an autonomous action), require BOTH a valid,
        in-scope **mandate** (authority) and a cited active **delegation** (autonomy).
        Any gap ⇒ a traced `constitution_violation` + drop-to-G0, and no dispatch."""
        # Import here to avoid a package import cycle (constitution ↔ front_server).
        from ..constitution.delegation import DelegationLedger, require_delegation
        from ..mandate.enforcement import evaluate_mandate_scope_check

        registry = getattr(self._inner, "_mandate_registry", None)
        mandate = registry.resolve(mandate_id) if registry is not None else None
        if mandate is None or mandate.is_expired(at):
            return self._deny_dispatch(
                mandate_id, "no valid mandate for dispatch (fail-closed)", operator_identity)

        # Mandate scope (authority) — only when an action target is given.
        if tool is not None or path is not None or risk is not None:
            probe = _types.SimpleNamespace(
                tool=tool or "", args=({"path": path} if path else {}),
                declared_risk=risk or RiskLevel.LOW)
            scope = evaluate_mandate_scope_check(probe, None, mandate, now=at)
            if scope.should_block:
                return self._deny_dispatch(mandate_id, scope.reason, operator_identity)

        # Delegation (autonomy) — an autonomous action must cite an active window.
        active = DelegationLedger.active(self._inner.trace, at=at)
        decision = require_delegation(autonomy_level, category, active, at=at)
        if not decision.allowed:
            return self._deny_dispatch(mandate_id, decision.reason, operator_identity)

        return DispatchAuthorization(
            True, mandate_id=mandate_id, cited_delegation_id=decision.cited_delegation_id)

    def _deny_dispatch(self, mandate_id: str, reason: str, operator_identity: str
                       ) -> DispatchAuthorization:
        self._inner.trace.append_praxis_event(PraxisEventRecord.make(
            run_id=self._inner.trace.run_id, agent_id=operator_identity,
            event_type=CONSTITUTION_VIOLATION_EVENT, subject_id=mandate_id or "-",
            summary=f"{_CVIO_MARK}|{mandate_id}|{reason}",
            mandate_id=("" if mandate_id in ("", "default") else mandate_id)))
        return DispatchAuthorization(
            False, mandate_id=mandate_id, reason=reason, drop_to_g0=True)
