"""F8.1 — deterministic irreversibility taxonomy for Chronos fork-gate."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..core_types import CommandEnvelope, RiskLevel
from ..policy import PolicyDecision
from ..tools import ToolSideEffectType, ToolSpec

_IRREVERSIBLE_TOOLS = frozenset({"delete_file", "network_fetch"})
_EXTERNAL_SIDE_EFFECTS = frozenset({
    "network", "deploy", "publish", "payment", "mail", "secrets",
})
_GUARDCASE_SHELL_TOOLS = frozenset({"run_shell", "run_python", "run_tests"})


class IrreversibilityClass(str, Enum):
    REVERSIBLE = "reversible"
    GUARDED = "guarded"
    IRREVERSIBLE = "irreversible"


@dataclass(frozen=True)
class IrreversibilityResult:
    klass: IrreversibilityClass
    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("IrreversibilityResult requires a non-empty reason")


def classify_irreversibility(
    cmd: CommandEnvelope,
    tool_spec: Optional[ToolSpec] = None,
    decision: Optional[PolicyDecision] = None,
) -> IrreversibilityResult:
    """Classify a command's reversibility. Every class carries an explicit reason."""
    if cmd.args.get("irreversible") is True:
        return IrreversibilityResult(
            IrreversibilityClass.IRREVERSIBLE,
            "command explicitly marked irreversible",
        )

    if cmd.tool in _IRREVERSIBLE_TOOLS:
        return IrreversibilityResult(
            IrreversibilityClass.IRREVERSIBLE,
            f"tool {cmd.tool!r} is classified irreversible",
        )

    for key in ("side_effect", "effect_type", "action_kind"):
        val = str(cmd.args.get(key, "")).lower()
        if val in _EXTERNAL_SIDE_EFFECTS:
            return IrreversibilityResult(
                IrreversibilityClass.IRREVERSIBLE,
                f"side-effect {val!r} is irreversible",
            )

    for flag in ("deploy", "publish", "payment", "mail", "touches_secrets"):
        if cmd.args.get(flag) is True:
            return IrreversibilityResult(
                IrreversibilityClass.IRREVERSIBLE,
                f"argument {flag}=True marks irreversible action",
            )

    risk = decision.risk if decision is not None else cmd.declared_risk
    if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        if cmd.tool in {"run_shell", "network_fetch"} or cmd.args.get("touches_secrets"):
            return IrreversibilityResult(
                IrreversibilityClass.IRREVERSIBLE,
                f"high/critical risk external action ({cmd.tool})",
            )

    side_effect = tool_spec.side_effect_type if tool_spec else None
    if side_effect is ToolSideEffectType.SHELL_EXECUTION:
        if cmd.tool in _GUARDCASE_SHELL_TOOLS and not cmd.args.get("irreversible"):
            return IrreversibilityResult(
                IrreversibilityClass.GUARDED,
                f"shell execution via {cmd.tool!r} requires guarded handling",
            )

    if cmd.tool in {"write_file", "edit_file", "patch_file"}:
        return IrreversibilityResult(
            IrreversibilityClass.REVERSIBLE,
            "filesystem write is reversible",
        )
    if side_effect is ToolSideEffectType.FILESYSTEM_WRITE:
        return IrreversibilityResult(
            IrreversibilityClass.REVERSIBLE,
            "filesystem write side-effect is reversible",
        )
    if cmd.tool in {"read_file", "list_dir", "search_text", "git_status", "git_diff"}:
        return IrreversibilityResult(
            IrreversibilityClass.REVERSIBLE,
            "read-only command",
        )

    return IrreversibilityResult(
        IrreversibilityClass.REVERSIBLE,
        "default reversible classification",
    )


def influence_is_escalation_only(evidence: Any) -> bool:
    """True when fork-gate evidence carries no permit/lower-risk semantics."""
    if hasattr(evidence, "to_dict"):
        payload = evidence.to_dict()
    elif isinstance(evidence, dict):
        payload = evidence
    else:
        return True
    forbidden = frozenset({
        "permit", "auto_allow", "approved", "lower_risk", "reduce_risk",
        "grants_authority",
    })
    for key in payload:
        if str(key).lower() in forbidden:
            return False
        val = payload[key]
        if isinstance(val, bool) and key in ("approved", "permit", "auto_allow", "grants_authority"):
            return False
        if isinstance(val, str) and val.lower() in forbidden:
            return False
    return True
