"""token_accounting.py — a read-model over the budget snapshot's token usage.

Splits a run's token spend into output (prompt+completion) vs distinct thinking
tokens, and reports whether the figures are *substantiated* (backed by a real
usage-bearing model response) or merely *estimate_only*.

No-overclaim, structural: ``substantiated`` is a read-only property derived from
the ledger's charge counts. There is no constructor path that sets it True
without a substantiated charge having been recorded — a view built from an
estimate-only snapshot can never claim to be substantiated.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenAccountingView:
    estimated_tokens: int
    thinking_tokens: int
    substantiated_charges: int
    estimate_only_charges: int

    @property
    def output_tokens(self) -> int:
        """Prompt+completion tokens (the non-thinking spend)."""
        return max(0, self.estimated_tokens - self.thinking_tokens)

    @property
    def estimate_only(self) -> bool:
        return self.estimate_only_charges > 0

    @property
    def substantiated(self) -> bool:
        """True only when every recorded LLM charge carried real usage.

        Unconstructible-True without a substantiated charge: mixed or
        estimate-only histories are never substantiated.
        """
        return self.substantiated_charges > 0 and self.estimate_only_charges == 0

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> "TokenAccountingView":
        usage = snapshot.get("usage", {}) if isinstance(snapshot, dict) else {}
        return cls(
            estimated_tokens=int(usage.get("estimated_tokens", 0)),
            thinking_tokens=int(usage.get("thinking_tokens", 0)),
            substantiated_charges=int(usage.get("substantiated_charges", 0)),
            estimate_only_charges=int(usage.get("estimate_only_charges", 0)),
        )
