"""
mandate.py — the Mandate object (F6.0).

A **mandate** is the runtime object that carries *authority* through the one door:
a versioned, content-hashed bundle of {scope, persona, policy-card references,
memory-zone rules, optional authority tightening} that travels with a dispatched
agent. It is the tamed "legislation as a runtime object": per-job / per-client
(e.g. "client X, only repo Y, budget Z, EU-data zones"), never multi-sovereign
jurisdictions (SCI-FI, parked).

Doctrine (P1.4): a mandate is **authority**, distinct from persona (expression).
A mandate only ever *tightens* an AgentCard's authority — the enforcement gate
(F6.2) intersects, never widens. This module is the data model + hashing only;
resolution is F6.0 (`registry.py`) and enforcement is F6.2.

`mandate_id` is un-constructible without a declared `scope` — you cannot mint a
mandate that hides what it governs (structural no-overclaim).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

from ..core_types import AuthorityScope, RiskLevel, canonical_json, new_id, now, sha

_FLAG = "AUREL_MANDATE"


def flag_enabled() -> bool:
    """True iff the mandate flag is explicitly enabled (default OFF)."""
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class MandateScope:
    """What a mandate confines an agent to. Empty fields mean "inherit the card"."""

    paths: tuple[str, ...] = ()            # write-path prefixes the mandate confines to
    repos: tuple[str, ...] = ()            # repo roots
    client_id: str = ""                    # per-client tag
    budget_cents: float = 0.0              # 0 = no extra budget cap (inherit)
    allowed_tools: tuple[str, ...] = ()    # empty = inherit the card's allow-list
    max_risk: RiskLevel = RiskLevel.CRITICAL  # ceiling; CRITICAL = inherit the card

    def is_permissive(self) -> bool:
        """True when the scope adds no path/repo/tool restriction (a passthrough)."""
        return not (self.paths or self.repos or self.allowed_tools)

    def to_dict(self) -> dict:
        return {
            "paths": list(self.paths),
            "repos": list(self.repos),
            "client_id": self.client_id,
            "budget_cents": self.budget_cents,
            "allowed_tools": list(self.allowed_tools),
            "max_risk": self.max_risk.value,
        }


@dataclass(frozen=True)
class Mandate:
    """A versioned, content-hashed authority bundle that travels with an agent."""

    mandate_id: str
    version: str
    scope: MandateScope                                     # required — must be declared
    persona_ref: str = "default"
    policy_card_ids: tuple[str, ...] = ()                   # references into a PolicyCardRegistry
    memory_zone_rules: Mapping[str, str] = field(default_factory=dict)  # zone -> "allow"|"deny"
    authority_overrides: Optional[AuthorityScope] = None    # tightening only (F6.2 intersects)
    expires_at: float = 0.0                                 # 0 = no expiry
    created_at: float = field(default_factory=now)

    def __post_init__(self) -> None:
        for field_name in ("mandate_id", "version"):
            if not getattr(self, field_name):
                raise ValueError(f"Mandate requires a non-empty {field_name}")
        if not isinstance(self.scope, MandateScope):
            raise TypeError("Mandate requires a declared MandateScope (no-overclaim)")

    @staticmethod
    def make(
        version: str,
        scope: MandateScope,
        *,
        persona_ref: str = "default",
        policy_card_ids: tuple[str, ...] = (),
        memory_zone_rules: Optional[Mapping[str, str]] = None,
        authority_overrides: Optional[AuthorityScope] = None,
        expires_at: float = 0.0,
    ) -> "Mandate":
        return Mandate(
            mandate_id=new_id("mandate"), version=version, scope=scope,
            persona_ref=persona_ref, policy_card_ids=tuple(policy_card_ids),
            memory_zone_rules=dict(memory_zone_rules or {}),
            authority_overrides=authority_overrides, expires_at=expires_at,
        )

    def is_expired(self, at: float) -> bool:
        """Fail-closed expiry: an expired mandate is treated as absent by the gate."""
        return self.expires_at > 0 and at >= self.expires_at

    def _hashable(self) -> dict:
        # created_at is deliberately excluded — the hash is a content identity.
        return {
            "mandate_id": self.mandate_id,
            "version": self.version,
            "scope": self.scope.to_dict(),
            "persona_ref": self.persona_ref,
            "policy_card_ids": list(self.policy_card_ids),
            "memory_zone_rules": dict(self.memory_zone_rules),
            "authority_overrides": (
                self.authority_overrides.to_dict() if self.authority_overrides else None
            ),
            "expires_at": self.expires_at,
        }

    @property
    def content_hash(self) -> str:
        """Deterministic content identity: same content ⇒ same hash (versioning)."""
        return sha(canonical_json(self._hashable()))

    def to_dict(self) -> dict:
        return {**self._hashable(), "content_hash": self.content_hash}
