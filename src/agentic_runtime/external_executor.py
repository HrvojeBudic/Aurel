"""
external_executor.py — F3.2 external-executor identity, budget, track record.

An external executor (a Claude Code session, another agent) is admitted to
Aurel's governed channel as three *bounded* things, never as a trusted peer:

  1. **Identity** — a LEAST-PRIVILEGE ``AgentCard`` derived from an operator
     ``ExternalExecutorGrant``. The card is never wider than the grant; there is
     no method that widens an executor's own scope. Widening requires a *new*
     operator grant — the executor cannot self-elevate.
  2. **Budget** — a HARD envelope: a ``BudgetPolicy`` clamped DOWN to the grant's
     caps (``min`` of the platform default and the grant). A grant can only
     tighten; it can never raise a ceiling above the platform default.
  3. **Track record** — an append-only, GOVERNED outcome ledger. Only the runtime
     records outcomes (from real gate / verifier results); the executor cannot
     write its own success. ``TrustLevel`` is DERIVED from the record, never set,
     and trust can only RESTRICT — a poor record lowers the effective risk
     ceiling; a good record never auto-widens authority beyond the card.

Pure value module: stdlib-only, deterministic, no runtime wiring. Nothing here
executes, charges, or mutates global state.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Optional

from .budget import BudgetPolicy
from .core_types import AgentCard, AgentClass, AuthorityScope, RiskLevel

# Local risk ordering (mirrors policy._RISK_ORDER) so this module stays light.
_RISK_ORDER: dict[RiskLevel, int] = {
    RiskLevel.TRIVIAL: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


def _min_risk(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    return a if _RISK_ORDER[a] <= _RISK_ORDER[b] else b


# --------------------------------------------------------------------------- #
# 1. Grant + least-privilege identity.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ExternalExecutorGrant:
    """What the operator authorizes for one external executor — the ceiling.

    Defaults are the tightest possible: no tools, read-only, LOW risk, no network,
    no secrets, platform-default budgets. A grant can only narrow from the
    platform baseline, never widen past it.
    """

    allowed_tools: tuple[str, ...] = ()
    read_paths: tuple[str, ...] = ()
    write_paths: tuple[str, ...] = ()
    max_risk: RiskLevel = RiskLevel.LOW
    allow_network: bool = False
    allow_secrets: bool = False
    # Hard budget caps; None ⇒ use the platform default (never exceeds it).
    max_commands: Optional[int] = None
    max_tool_calls: Optional[int] = None
    max_estimated_tokens: Optional[int] = None
    max_estimated_cost_cents: Optional[int] = None
    max_llm_calls: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "allowed_tools": list(self.allowed_tools),
            "read_paths": list(self.read_paths),
            "write_paths": list(self.write_paths),
            "max_risk": self.max_risk.value,
            "allow_network": self.allow_network,
            "allow_secrets": self.allow_secrets,
            "max_commands": self.max_commands,
            "max_tool_calls": self.max_tool_calls,
            "max_estimated_tokens": self.max_estimated_tokens,
            "max_estimated_cost_cents": self.max_estimated_cost_cents,
            "max_llm_calls": self.max_llm_calls,
        }


def derive_external_card(
    executor_id: str, grant: ExternalExecutorGrant, mission: str = ""
) -> AgentCard:
    """Derive a least-privilege AgentCard bounded exactly by the grant.

    The card is never wider than the grant: protected mutation is always off, and
    the authority scope is precisely the grant's paths / risk / network / secrets.
    """
    authority = AuthorityScope(
        write_paths=list(grant.write_paths),
        read_paths=list(grant.read_paths),
        allow_protected_mutation=False,
        allow_test_modification=False,
        allow_network=grant.allow_network,
        allow_secrets=grant.allow_secrets,
        max_risk=grant.max_risk,
    )
    return AgentCard.make(
        name=executor_id,
        agent_class=AgentClass.EXECUTION,
        mission=mission or f"external executor {executor_id} (F3.2)",
        authority=authority,
        allowed_tools=list(grant.allowed_tools),
        denied_tools=[],
    )


# --------------------------------------------------------------------------- #
# 2. Hard budget envelope.
# --------------------------------------------------------------------------- #
def _clamp(base: int, cap: Optional[int]) -> int:
    """Grant can only tighten: min(platform default, grant). None ⇒ default."""
    return base if cap is None else min(base, cap)


def budget_envelope(
    grant: ExternalExecutorGrant, base: Optional[BudgetPolicy] = None
) -> BudgetPolicy:
    """A BudgetPolicy clamped down to the grant. Never exceeds the platform base."""
    base = base or BudgetPolicy()
    return replace(
        base,
        max_commands_per_run=_clamp(base.max_commands_per_run, grant.max_commands),
        max_tool_calls_per_run=_clamp(base.max_tool_calls_per_run, grant.max_tool_calls),
        max_estimated_tokens=_clamp(base.max_estimated_tokens, grant.max_estimated_tokens),
        max_estimated_cost_cents=_clamp(
            base.max_estimated_cost_cents, grant.max_estimated_cost_cents
        ),
        max_llm_calls=_clamp(base.max_llm_calls, grant.max_llm_calls),
    )


# --------------------------------------------------------------------------- #
# 3. Governed track record + derived trust.
# --------------------------------------------------------------------------- #
class TrackRecordOutcome(str, Enum):
    SUCCESS = "success"    # action ran and verified
    FAILURE = "failure"    # action ran but failed verification
    DENIED = "denied"      # gate / policy denied it
    BLOCKED = "blocked"    # budget / sandbox blocked it


class TrustLevel(str, Enum):
    UNTRUSTED = "untrusted"  # no record, or a recent failure
    PROBATION = "probation"  # some clean successes, not yet enough
    TRUSTED = "trusted"      # sustained clean successes


# Trust derivation constants (deterministic).
PROBATION_MIN_SUCCESSES = 1
TRUSTED_MIN_SUCCESSES = 5
RECENT_WINDOW = 5  # a failure within the last N entries drops trust to UNTRUSTED

# Trust → the highest risk it will vouch for. Trust only ever *lowers* the
# effective ceiling below the card; TRUSTED adds no restriction of its own.
_TRUST_CEILING: dict[TrustLevel, RiskLevel] = {
    TrustLevel.UNTRUSTED: RiskLevel.TRIVIAL,
    TrustLevel.PROBATION: RiskLevel.LOW,
    TrustLevel.TRUSTED: RiskLevel.CRITICAL,  # no extra restriction; card still binds
}


@dataclass(frozen=True)
class TrackRecordEntry:
    """One immutable governed outcome. Recorded by the runtime, not the executor."""

    outcome: TrackRecordOutcome
    tool: str
    action_ref: str
    tick: int
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "outcome": self.outcome.value,
            "tool": self.tool,
            "action_ref": self.action_ref,
            "tick": self.tick,
            "note": self.note,
        }


@dataclass
class TrackRecordLedger:
    """Append-only outcome history for one external executor.

    ``record`` is the only writer and is intended to be called by the runtime
    from real gate / verifier results — never by the executor about itself. There
    is no method to edit or remove an entry.
    """

    executor_id: str
    _entries: list[TrackRecordEntry] = field(default_factory=list)

    def record(
        self,
        *,
        outcome: TrackRecordOutcome,
        tool: str,
        action_ref: str,
        tick: int,
        note: str = "",
    ) -> TrackRecordEntry:
        entry = TrackRecordEntry(
            outcome=outcome, tool=tool, action_ref=action_ref, tick=tick, note=note
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> tuple[TrackRecordEntry, ...]:
        return tuple(self._entries)

    def count(self, outcome: TrackRecordOutcome) -> int:
        return sum(1 for e in self._entries if e.outcome is outcome)

    def has_recent_failure(self, window: int = RECENT_WINDOW) -> bool:
        recent = self._entries[-window:] if window > 0 else self._entries
        return any(e.outcome is TrackRecordOutcome.FAILURE for e in recent)

    def trust_level(self) -> TrustLevel:
        """Derive trust from the record. Deterministic; a recent failure drops it."""
        if self.has_recent_failure():
            return TrustLevel.UNTRUSTED
        successes = self.count(TrackRecordOutcome.SUCCESS)
        if successes >= TRUSTED_MIN_SUCCESSES:
            return TrustLevel.TRUSTED
        if successes >= PROBATION_MIN_SUCCESSES:
            return TrustLevel.PROBATION
        return TrustLevel.UNTRUSTED

    def to_dict(self) -> dict:
        return {
            "executor_id": self.executor_id,
            "trust_level": self.trust_level().value,
            "successes": self.count(TrackRecordOutcome.SUCCESS),
            "failures": self.count(TrackRecordOutcome.FAILURE),
            "denied": self.count(TrackRecordOutcome.DENIED),
            "blocked": self.count(TrackRecordOutcome.BLOCKED),
            "entries": [e.to_dict() for e in self._entries],
        }


def effective_max_risk(card_max_risk: RiskLevel, trust: TrustLevel) -> RiskLevel:
    """The effective ceiling = min(card ceiling, trust ceiling).

    Trust can only *narrow*: a low-trust executor is capped below its card until
    it earns a record. It can never widen authority beyond what the card grants.
    """
    return _min_risk(card_max_risk, _TRUST_CEILING[trust])


# --------------------------------------------------------------------------- #
# Bundled profile.
# --------------------------------------------------------------------------- #
@dataclass
class ExternalExecutorProfile:
    """Identity + budget + track record for one external executor.

    Exposes no scope-widening method: to grant more, derive a new profile from a
    new grant. The trust it reports only ever lowers the effective ceiling.
    """

    executor_id: str
    grant: ExternalExecutorGrant
    card: AgentCard
    budget: BudgetPolicy
    ledger: TrackRecordLedger

    @property
    def trust(self) -> TrustLevel:
        return self.ledger.trust_level()

    @property
    def effective_max_risk(self) -> RiskLevel:
        return effective_max_risk(self.card.authority.max_risk, self.trust)

    def to_dict(self) -> dict:
        return {
            "executor_id": self.executor_id,
            "grant": self.grant.to_dict(),
            "card_id": self.card.id,
            "card_max_risk": self.card.authority.max_risk.value,
            "trust": self.trust.value,
            "effective_max_risk": self.effective_max_risk.value,
            "track_record": self.ledger.to_dict(),
        }


def make_external_executor(
    executor_id: str,
    grant: ExternalExecutorGrant,
    mission: str = "",
    base_budget: Optional[BudgetPolicy] = None,
) -> ExternalExecutorProfile:
    """Assemble a bounded external-executor profile from an operator grant."""
    return ExternalExecutorProfile(
        executor_id=executor_id,
        grant=grant,
        card=derive_external_card(executor_id, grant, mission),
        budget=budget_envelope(grant, base_budget),
        ledger=TrackRecordLedger(executor_id=executor_id),
    )
