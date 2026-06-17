"""
plan_validator.py — Strict plan validation (P0.5).

The planner proposes structured steps; PlanValidator is the gate that prevents
empty, malformed, or unsupported plans from reaching tool execution.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .model_providers.schemas import (looks_like_structured_plan,
                                      validate_structured_plan_payload)


class PlanStatus(str, Enum):
    VALID = "valid"
    EMPTY_PLAN = "empty_plan"
    INVALID_JSON = "invalid_json"
    INVALID_SCHEMA = "invalid_schema"
    UNKNOWN_TOOL = "unknown_tool"
    UNSUPPORTED_COMMAND = "unsupported_command"


@dataclass
class PlanValidationResult:
    status: PlanStatus
    steps: list[dict] = field(default_factory=list)
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return self.status is PlanStatus.VALID


class PlanValidator:
    """Validate planner output before any tool is dispatched."""

    def __init__(
        self,
        registered_tools: set[str],
        allowed_tools: Optional[list[str]] = None,
    ) -> None:
        self.registered_tools = registered_tools
        self.allowed_tools = allowed_tools

    def parse_and_validate(self, raw: str) -> PlanValidationResult:
        text = raw.strip()
        if not text:
            return PlanValidationResult(
                PlanStatus.EMPTY_PLAN,
                reason="planner returned empty output",
            )

        if text.startswith("```"):
            text = text.strip("`")
            brace = text.find("{")
            if brace >= 0:
                text = text[brace:]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return PlanValidationResult(
                PlanStatus.INVALID_JSON,
                reason=f"planner output is not valid JSON: {e.msg}",
                details={"json_error": e.msg, "position": e.pos},
            )

        if not isinstance(data, dict):
            return PlanValidationResult(
                PlanStatus.INVALID_SCHEMA,
                reason="planner output must be a JSON object with a 'plan' array",
                details={"got_type": type(data).__name__},
            )

        if looks_like_structured_plan(data):
            structured = validate_structured_plan_payload(data)
            if not structured.ok:
                return PlanValidationResult(
                    PlanStatus.INVALID_SCHEMA,
                    reason="structured plan schema validation failed",
                    details={"errors": structured.errors},
                )

        refusal = data.get("refusal_reason")
        if isinstance(refusal, str) and refusal.strip():
            return PlanValidationResult(
                PlanStatus.EMPTY_PLAN,
                reason=f"model refused to produce executable plan: {refusal}",
                details={"refusal_reason": refusal},
            )

        plan = data.get("plan")
        if plan is None:
            return PlanValidationResult(
                PlanStatus.INVALID_SCHEMA,
                reason="planner output missing 'plan' field",
            )

        if not isinstance(plan, list):
            return PlanValidationResult(
                PlanStatus.INVALID_SCHEMA,
                reason="'plan' must be an array",
                details={"got_type": type(plan).__name__},
            )

        if len(plan) == 0:
            return PlanValidationResult(
                PlanStatus.EMPTY_PLAN,
                reason="planner returned an empty plan",
            )

        return self.validate_steps(plan)

    def validate_steps(self, plan: list[Any]) -> PlanValidationResult:
        normalized: list[dict] = []

        for index, step in enumerate(plan):
            if not isinstance(step, dict):
                return PlanValidationResult(
                    PlanStatus.INVALID_SCHEMA,
                    reason=f"plan step {index} must be an object",
                    details={"step_index": index, "got_type": type(step).__name__},
                )

            tool = step.get("tool")
            if not tool or not isinstance(tool, str) or not str(tool).strip():
                return PlanValidationResult(
                    PlanStatus.INVALID_SCHEMA,
                    reason=f"plan step {index} missing non-empty 'tool'",
                    details={"step_index": index},
                )

            args = step.get("args")
            if args is None:
                return PlanValidationResult(
                    PlanStatus.INVALID_SCHEMA,
                    reason=f"plan step {index} missing 'args'",
                    details={"step_index": index, "tool": tool},
                )
            if not isinstance(args, dict):
                return PlanValidationResult(
                    PlanStatus.INVALID_SCHEMA,
                    reason=f"plan step {index} 'args' must be an object",
                    details={"step_index": index, "tool": tool},
                )

            reason = step.get("reason") or step.get("rationale")
            if not reason or not isinstance(reason, str) or not str(reason).strip():
                return PlanValidationResult(
                    PlanStatus.INVALID_SCHEMA,
                    reason=f"plan step {index} missing non-empty 'reason'",
                    details={"step_index": index, "tool": tool},
                )

            tool_name = str(tool).strip()
            if tool_name not in self.registered_tools:
                return PlanValidationResult(
                    PlanStatus.UNKNOWN_TOOL,
                    reason=f"plan step {index} references unknown tool '{tool_name}'",
                    details={"step_index": index, "tool": tool_name},
                )

            if self.allowed_tools and tool_name not in self.allowed_tools:
                return PlanValidationResult(
                    PlanStatus.UNSUPPORTED_COMMAND,
                    reason=f"plan step {index} tool '{tool_name}' not permitted for this card",
                    details={"step_index": index, "tool": tool_name},
                )

            normalized.append(_normalize_step(step, tool_name, args, reason))

        return PlanValidationResult(PlanStatus.VALID, steps=normalized)


def _normalize_step(step: dict, tool: str, args: dict, reason: str) -> dict:
    """Map planner aliases to runtime step shape."""
    out = {
        "tool": tool,
        "args": args,
        "rationale": reason,
        "reason": reason,
    }
    if "expected_effect" in step:
        out["expected_effect"] = step["expected_effect"]
    if "step_id" in step:
        out["step_id"] = step["step_id"]
    risk = step.get("risk_level") or step.get("risk")
    if risk is not None:
        out["risk"] = risk
    return out
