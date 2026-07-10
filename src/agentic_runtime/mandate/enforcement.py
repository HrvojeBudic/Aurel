"""
enforcement.py — the mandate scope-enforcement gate (F6.2).

This is where `mandate_id` stops being a passenger and becomes authority. Given a
command, the issuing card, and the resolved mandate, the check returns a block
reason iff the command falls **outside** the mandate's scope. The gate only ever
*tightens*: it runs after the policy engine has already verified `card.authority`,
and it can only add a denial, never widen. Fail-closed: a missing or expired
mandate blocks.

Scope checks (all intersecting): tool allow-list, risk ceiling, write-path
confinement, expiry. Policy-card aggregation over `mandate.policy_card_ids` is a
declared follow-up seam (needs the PolicyCardRegistry resolver wired in).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..core_types import RiskLevel
from .mandate import Mandate

_RISK_RANK = {
    RiskLevel.TRIVIAL: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4,
}

# Argument keys whose string values are treated as write targets for confinement.
_PATH_KEYS = ("path", "file_path", "filepath", "paths", "dir", "directory",
              "target", "target_path", "filename", "dest", "destination")


@dataclass(frozen=True)
class MandateCheckResult:
    """The verdict of a mandate scope check. `should_block` ⇒ deny with `reason`."""

    should_block: bool
    reason: str = ""

    def to_dict(self) -> dict:
        return {"should_block": self.should_block, "reason": self.reason}


def _candidate_paths(args: dict) -> list[str]:
    out: list[str] = []
    for key in _PATH_KEYS:
        val = args.get(key)
        if isinstance(val, str) and val:
            out.append(val)
        elif isinstance(val, (list, tuple)):
            out.extend(v for v in val if isinstance(v, str) and v)
    return out


def evaluate_mandate_scope_check(
    cmd: Any, card: Any, mandate: Optional[Mandate], *, now: float
) -> MandateCheckResult:
    """Block iff `cmd` falls outside `mandate`'s scope. Fail-closed on absence/expiry."""
    if mandate is None:
        return MandateCheckResult(True, "mandate scope: unknown mandate_id (fail-closed)")
    if mandate.is_expired(now):
        return MandateCheckResult(
            True, f"mandate scope: mandate {mandate.mandate_id} is expired (fail-closed)")

    scope = mandate.scope

    # 1. Tool allow-list (empty ⇒ inherit the card's allow-list).
    if scope.allowed_tools and cmd.tool not in scope.allowed_tools:
        return MandateCheckResult(
            True, f"mandate scope: tool {cmd.tool!r} not in mandate allow-list")

    # 2. Risk ceiling (CRITICAL ceiling ⇒ inherit the card).
    if _RISK_RANK[cmd.declared_risk] > _RISK_RANK[scope.max_risk]:
        return MandateCheckResult(
            True,
            f"mandate scope: risk {cmd.declared_risk.value} exceeds mandate "
            f"ceiling {scope.max_risk.value}")

    # 3. Write-path confinement (empty ⇒ inherit the card's authority paths).
    if scope.paths:
        for target in _candidate_paths(dict(cmd.args or {})):
            if not any(target.startswith(p) for p in scope.paths):
                return MandateCheckResult(
                    True,
                    f"mandate scope: path {target!r} outside mandate paths "
                    f"{list(scope.paths)}")

    return MandateCheckResult(False, "")
