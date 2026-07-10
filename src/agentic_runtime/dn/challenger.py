"""
challenger.py — the challenger pass (F6.7).

A second-opinion pass over a risky proposal: a (typically cheaper / different)
model is asked to surface the strongest dissent — wrong assumptions, risks, cheaper
alternatives. It is **advisory only**: the challenge is attached to the proposal for
the operator, never executed. A router failure is an honest UNAVAILABLE dissent,
never a fabricated endorsement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CHALLENGER_SYSTEM = (
    "You are the challenger. Given a proposed plan, surface the STRONGEST dissent: "
    "wrong assumptions, hidden risks, and cheaper or safer alternatives. Critique "
    "only — never endorse by default, never execute. If you cannot find a real "
    "concern, say so plainly."
)


@dataclass(frozen=True)
class Challenge:
    """One advisory challenge. `advisory` is always True (never executes)."""

    dissent: str
    model: str
    profile: str
    available: bool = True
    advisory: bool = True

    def to_dict(self) -> dict:
        return {"dissent": self.dissent, "model": self.model, "profile": self.profile,
                "available": self.available, "advisory": self.advisory}


class ChallengerPass:
    """Runs an advisory second-opinion over a proposal through the F2 router."""

    def __init__(self, router: Any, *, profile: str = "challenger") -> None:
        self._router = router
        self._profile = profile

    def challenge(self, proposal_text: str) -> Challenge:
        try:
            raw, model, _usage = self._router.complete_with_usage(
                self._profile, CHALLENGER_SYSTEM, proposal_text)
        except Exception as e:  # provider failure ⇒ honest UNAVAILABLE, never a fake OK
            return Challenge(dissent=f"[unavailable] challenger router: {e}",
                             model="", profile=self._profile, available=False)
        return Challenge(dissent=raw, model=model, profile=self._profile)
