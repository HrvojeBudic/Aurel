"""constraints.py — hard / soft split with the ABC bounded-recovery bound.

From *Agent Behavioral Contracts* (Bhardwaj): only **hard** invariants block
synchronously; **soft** constraints tolerate transient violation if a recovery
map R restores them within a bounded window k. Lemma 3.10 quantifies why async +
recovery is as strong as blocking for the soft class:

    without recovery:  compliance(T) = q**T                (exponential decay)
    with recovery:     compliance(T) ≥ 1 − T·(1−q)·(1−r)   (linear decay)

Hard invariants below are real predicates over Σ + the command; they are the
only things that force a synchronous block.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable

from ..core_types import AgentCard, CommandEnvelope
from .sigma import GovernanceStateVector


@runtime_checkable
class HardInvariant(Protocol):
    name: str

    def holds(
        self,
        sigma: GovernanceStateVector,
        cmd: CommandEnvelope,
        card: AgentCard,
    ) -> bool:
        ...


@dataclass
class SoftConstraint:
    """Bounded-liveness: transient violation is fine if R recovers within k."""

    name: str
    predicate: Callable[[GovernanceStateVector], float]   # ≥ 1−δ ⇒ satisfied
    recovery: Callable[[GovernanceStateVector], list[CommandEnvelope]]
    k_max: int
    delta: float = 0.1

    def satisfied(self, sigma: GovernanceStateVector) -> bool:
        return self.predicate(sigma) >= (1.0 - self.delta)


# --------------------------------------------------------------------------- #
#  Built-in hard invariants (real predicates, no mocks).
# --------------------------------------------------------------------------- #
@dataclass
class NoSecretsEgress:
    name: str = "no_secrets_egress"

    def holds(self, sigma, cmd, card) -> bool:
        if not card.authority.allow_secrets and cmd.args.get("use_secrets"):
            return False
        if not card.authority.allow_network and cmd.tool == "network_fetch":
            return False
        return True


@dataclass
class ProtectedTestIntegrity:
    name: str = "protected_test_integrity"

    def holds(self, sigma, cmd, card) -> bool:
        path = cmd.args.get("path")
        if not path:
            return True
        norm = str(path).replace("\\", "/")
        for protected in card.authority.protected_test_paths:
            p = protected.replace("\\", "/")
            touches = norm == p or norm.startswith(p.rstrip("/") + "/")
            if touches and not card.authority.allow_protected_mutation:
                return False
        return True


@dataclass
class WithinAuthorityRisk:
    name: str = "within_authority_risk"

    def holds(self, sigma, cmd, card) -> bool:
        from .sigma import _rank  # local import: shared risk ranking
        return _rank(sigma.max_sensitivity) <= _rank(card.authority.max_risk)


@dataclass
class ConstraintSet:
    """Evaluates hard invariants; a single failure means synchronous block."""

    hard: list[HardInvariant] = field(default_factory=list)
    soft: list[SoftConstraint] = field(default_factory=list)

    @classmethod
    def default(cls) -> "ConstraintSet":
        return cls(hard=[
            NoSecretsEgress(),
            ProtectedTestIntegrity(),
            WithinAuthorityRisk(),
        ])

    def hard_violations(
        self,
        sigma: GovernanceStateVector,
        cmd: CommandEnvelope,
        card: AgentCard,
    ) -> list[str]:
        return [inv.name for inv in self.hard if not inv.holds(sigma, cmd, card)]

    def soft_violations(self, sigma: GovernanceStateVector) -> list[str]:
        return [c.name for c in self.soft if not c.satisfied(sigma)]


# --------------------------------------------------------------------------- #
#  ABC Lemma 3.10 — the "async is not weaker" bound, as real numbers.
# --------------------------------------------------------------------------- #
def no_recovery_compliance(q: float, steps: int) -> float:
    """Sustained compliance over ``steps`` with per-step reliability q, no recovery."""
    _check_prob(q)
    if steps < 0:
        raise ValueError("steps must be >= 0")
    return q ** steps


def compliance_lower_bound(q: float, r: float, steps: int) -> float:
    """Lower bound on sustained compliance WITH bounded recovery (rate r).

    ``1 − T·(1−q)·(1−r)``, clamped to [0, 1]. Recovery converts the exponential
    decay of :func:`no_recovery_compliance` into linear decay.
    """
    _check_prob(q)
    _check_prob(r)
    if steps < 0:
        raise ValueError("steps must be >= 0")
    bound = 1.0 - steps * (1.0 - q) * (1.0 - r)
    return max(0.0, min(1.0, bound))


def _check_prob(x: float) -> None:
    if not (0.0 <= x <= 1.0):
        raise ValueError(f"probability must be in [0, 1], got {x}")
