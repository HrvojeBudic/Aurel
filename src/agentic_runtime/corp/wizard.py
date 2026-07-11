"""
wizard.py — the Agency wizard: environment templates + what-if impact (F7.6).

The wizard drafts a **governed environment** (a client + job + mandate) and shows,
*before creating anything*, what that mandate would allow or deny. Doctrine:

  * the wizard **creates nothing directly** — `to_proposal()` produces the payload
    a UI posts to the one door (`POST /proposals`, kind `act`); creation is an
    approval away, a governed record, never a side effect of drafting.
  * `what_if()` is a **dry-run through the real F6.2 gate**
    (`evaluate_mandate_scope_check`) — the same code that enforces at runtime — so
    the preview cannot drift from reality. It is **evidence, not authority**: the
    `ImpactReport` is advisory and grants no permission (a what-if verdict never
    approves an action).
  * an `EnvironmentTemplate` is **un-constructible without a scope** (it inherits
    the Mandate no-overclaim law).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..core_types import RiskLevel, now
from ..mandate import Mandate, MandateScope
from ..mandate.enforcement import evaluate_mandate_scope_check

_DRAFT_MANDATE_ID = "template-draft"
_CREATE_TOOL = "corp_create_environment"


@dataclass(frozen=True)
class SampleAction:
    """A probe run through the mandate gate. Exposes exactly what the gate reads."""

    tool: str
    declared_risk: RiskLevel = RiskLevel.LOW
    args: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvironmentTemplate:
    """A draft {client + job + mandate} — a plan, never a created environment."""

    client_name: str
    job_title: str
    scope: MandateScope                                 # required — no-overclaim
    persona_ref: str = "default"
    memory_zone_rules: Mapping[str, str] = field(default_factory=dict)
    repos: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.client_name:
            raise ValueError("EnvironmentTemplate requires a client_name")
        if not self.job_title:
            raise ValueError("EnvironmentTemplate requires a job_title")
        if not isinstance(self.scope, MandateScope):
            raise TypeError("EnvironmentTemplate requires a declared MandateScope (no-overclaim)")

    def to_mandate(self) -> Mandate:
        """The draft mandate this template would create (stable id, for what-if)."""
        return Mandate(
            mandate_id=_DRAFT_MANDATE_ID, version="draft", scope=self.scope,
            persona_ref=self.persona_ref, memory_zone_rules=dict(self.memory_zone_rules))

    def to_proposal(self) -> dict:
        """The one-door proposal payload (kind `act`). Creates nothing by itself."""
        return {
            "kind": "act",
            "tool": _CREATE_TOOL,
            "args": {
                "client_name": self.client_name,
                "job_title": self.job_title,
                "persona_ref": self.persona_ref,
                "scope": self.scope.to_dict(),
                "memory_zone_rules": dict(self.memory_zone_rules),
                "repos": list(self.repos),
            },
            "risk": "medium",
            "rationale": f"create governed environment for {self.client_name!r}",
            "expected_effect": "register client + job + mandate under the one door",
        }


@dataclass(frozen=True)
class ImpactReport:
    """The what-if result: what the drafted mandate would deny / allow. Advisory."""

    results: tuple[dict, ...]

    @property
    def blocked_count(self) -> int:
        return sum(1 for r in self.results if r["would_block"])

    @property
    def allowed_count(self) -> int:
        return sum(1 for r in self.results if not r["would_block"])

    # Structural: a what-if is evidence, never authority.
    @property
    def is_advisory(self) -> bool:
        return True

    @property
    def grants_authority(self) -> bool:
        return False

    def to_dict(self) -> dict:
        return {
            "results": list(self.results),
            "blocked_count": self.blocked_count,
            "allowed_count": self.allowed_count,
            "is_advisory": self.is_advisory,
            "grants_authority": self.grants_authority,
        }


def what_if(template: EnvironmentTemplate, sample_actions: Iterable[SampleAction]) -> ImpactReport:
    """Dry-run each sample action through the real F6.2 mandate gate. Evidence, not authority."""
    mandate = template.to_mandate()
    at = now()
    results: list[dict] = []
    for action in sample_actions:
        verdict = evaluate_mandate_scope_check(action, None, mandate, now=at)
        results.append({
            "tool": action.tool,
            "risk": action.declared_risk.value,
            "would_block": verdict.should_block,
            "reason": verdict.reason,
        })
    return ImpactReport(tuple(results))


__all__ = ["EnvironmentTemplate", "SampleAction", "ImpactReport", "what_if"]
