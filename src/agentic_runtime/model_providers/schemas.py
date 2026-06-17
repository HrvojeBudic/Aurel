"""Canonical structured plan schema and lightweight validation."""
from __future__ import annotations

import json
from typing import Any

from .base import StructuredPlanResult

RISK_VALUES = ("trivial", "low", "medium", "high", "critical")

STRUCTURED_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "intent_summary",
        "plan",
        "confidence",
        "requires_approval",
        "assumptions",
        "refusal_reason",
    ],
    "properties": {
        "intent_summary": {"type": "string"},
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["step_id", "tool", "args", "risk", "reason"],
                "properties": {
                    "step_id": {"type": "string"},
                    "tool": {"type": "string"},
                    "args": {"type": "object"},
                    "risk": {"type": "string", "enum": list(RISK_VALUES)},
                    "reason": {"type": "string"},
                    # Accepted by existing skill/demo code; still explicit.
                    "expected_effect": {"type": "string"},
                },
            },
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "requires_approval": {"type": "boolean"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "refusal_reason": {"type": ["string", "null"]},
    },
}

STRUCTURED_PLAN_KEYS = frozenset(STRUCTURED_PLAN_SCHEMA["required"])


def structured_plan_payload(
    plan: list[dict[str, Any]],
    *,
    intent_summary: str = "",
    confidence: float = 0.5,
    requires_approval: bool = False,
    assumptions: list[str] | None = None,
    refusal_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "intent_summary": intent_summary,
        "plan": plan,
        "confidence": confidence,
        "requires_approval": requires_approval,
        "assumptions": assumptions or [],
        "refusal_reason": refusal_reason,
    }


def structured_plan_json(**kw: Any) -> str:
    return json.dumps(structured_plan_payload(**kw))


def refusal_payload(reason: str) -> dict[str, Any]:
    return structured_plan_payload(
        [],
        intent_summary="refused",
        confidence=0.0,
        requires_approval=False,
        assumptions=[],
        refusal_reason=reason,
    )


def refusal_json(reason: str) -> str:
    return json.dumps(refusal_payload(reason))


def validate_structured_plan_text(text: str) -> StructuredPlanResult:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return StructuredPlanResult(False, errors=[f"invalid_json: {e.msg}"])
    return validate_structured_plan_payload(data)


def validate_structured_plan_payload(data: Any) -> StructuredPlanResult:
    errors: list[str] = []
    if not isinstance(data, dict):
        return StructuredPlanResult(False, errors=["top-level value must be object"])

    extra = set(data) - STRUCTURED_PLAN_KEYS
    missing = STRUCTURED_PLAN_KEYS - set(data)
    if extra:
        errors.append(f"unexpected top-level fields: {sorted(extra)}")
    if missing:
        errors.append(f"missing top-level fields: {sorted(missing)}")

    intent_summary = data.get("intent_summary")
    if "intent_summary" in data and not isinstance(intent_summary, str):
        errors.append("intent_summary must be string")

    plan = data.get("plan")
    if "plan" in data and not isinstance(plan, list):
        errors.append("plan must be array")

    confidence = data.get("confidence")
    if "confidence" in data:
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            errors.append("confidence must be number")
        elif not 0.0 <= float(confidence) <= 1.0:
            errors.append("confidence must be between 0.0 and 1.0")

    requires_approval = data.get("requires_approval")
    if "requires_approval" in data and not isinstance(requires_approval, bool):
        errors.append("requires_approval must be boolean")

    assumptions = data.get("assumptions")
    if "assumptions" in data:
        if not isinstance(assumptions, list):
            errors.append("assumptions must be array")
        elif not all(isinstance(a, str) for a in assumptions):
            errors.append("assumptions entries must be strings")

    refusal = data.get("refusal_reason")
    if refusal is not None and not isinstance(refusal, str):
        errors.append("refusal_reason must be string or null")

    if isinstance(plan, list):
        if not plan and refusal is None:
            errors.append("plan may be empty only when refusal_reason is not null")
        for idx, step in enumerate(plan):
            errors.extend(_validate_step(idx, step))

    return StructuredPlanResult(
        ok=not errors,
        plan=plan if isinstance(plan, list) else [],
        errors=errors,
        refusal_reason=refusal if isinstance(refusal, str) else None,
        parsed_json=data,
    )


def _validate_step(idx: int, step: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(step, dict):
        return [f"plan[{idx}] must be object"]

    allowed = {"step_id", "tool", "args", "risk", "reason", "expected_effect"}
    required = {"step_id", "tool", "args", "risk", "reason"}
    extra = set(step) - allowed
    missing = required - set(step)
    if extra:
        errors.append(f"plan[{idx}] unexpected fields: {sorted(extra)}")
    if missing:
        errors.append(f"plan[{idx}] missing fields: {sorted(missing)}")
    for key in ("step_id", "tool", "risk", "reason"):
        if key in step and (not isinstance(step[key], str) or not step[key].strip()):
            errors.append(f"plan[{idx}].{key} must be non-empty string")
    if "args" in step and not isinstance(step["args"], dict):
        errors.append(f"plan[{idx}].args must be object")
    if "risk" in step and step["risk"] not in RISK_VALUES:
        errors.append(f"plan[{idx}].risk invalid: {step['risk']!r}")
    if "expected_effect" in step and not isinstance(step["expected_effect"], str):
        errors.append(f"plan[{idx}].expected_effect must be string")
    return errors


def looks_like_structured_plan(data: dict[str, Any]) -> bool:
    return bool(set(data) & (STRUCTURED_PLAN_KEYS - {"plan"}))
