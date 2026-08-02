"""Deterministic offline provider used by tests and demos."""
from __future__ import annotations

import json
import time
from typing import Optional

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus)
from .schemas import structured_plan_payload


class MockProvider:
    name = "mock"

    def __init__(
        self,
        config: Optional[ModelProviderConfig] = None,
        *,
        scripted: Optional[dict[str, str]] = None,
        failure_mode: Optional[str] = None,
    ) -> None:
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name="mock-deterministic",
        )
        self.scripted = scripted or {}
        self.failure_mode = failure_mode

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse:
        t0 = time.perf_counter()
        if self.failure_mode == "provider_timeout":
            return self._response("", t0, error="provider_timeout")
        if self.failure_mode == "invalid_json":
            return self._response("{not valid json", t0)
        if self.failure_mode == "missing_required_field":
            return self._response(json.dumps({"intent_summary": "missing plan"}), t0)
        if self.failure_mode == "refusal":
            raw = json.dumps(structured_plan_payload(
                [],
                intent_summary="refused by mock",
                confidence=0.0,
                requires_approval=False,
                assumptions=[],
                refusal_reason="mock refusal",
            ))
            return self._response(raw, t0, refusal_reason="mock refusal")
        if self.failure_mode == "empty_plan":
            raw = json.dumps(structured_plan_payload(
                [],
                intent_summary="empty mock plan",
                confidence=0.4,
                requires_approval=False,
                assumptions=[],
                refusal_reason=None,
            ))
            return self._response(raw, t0)

        for key, response in self.scripted.items():
            if key in request.user_prompt:
                return self._response(response, t0)

        if _is_repo_plan_schema(request.output_schema):
            raw = json.dumps(_repo_plan_payload(request.user_prompt))
            return self._response(raw, t0)

        raw = json.dumps(structured_plan_payload(
            [{
                "step_id": "step_1",
                "tool": "list_dir",
                "args": {"path": "."},
                "risk": "trivial",
                "reason": "inspect workspace before acting",
                "expected_effect": "no state change",
            }],
            intent_summary="inspect workspace",
            confidence=0.7,
            requires_approval=False,
            assumptions=[],
            refusal_reason=None,
        ))
        return self._response(raw, t0)

    def complete_text(self, request: ModelRequest) -> ModelResponse:
        """Deterministic prose reply, so the offline default can hold a
        conversation instead of only emitting plans.

        Scripted entries and failure modes are honoured exactly as on the
        structured path — a test that scripts a reply gets that reply verbatim,
        and a test that asks for a timeout still gets one.
        """
        t0 = time.perf_counter()
        if self.failure_mode == "provider_timeout":
            return self._response("", t0, error="provider_timeout")
        if self.failure_mode == "refusal":
            return self._response("", t0, refusal_reason="mock refusal")

        for key, response in self.scripted.items():
            if key in request.user_prompt:
                return self._response(response, t0)

        return self._response(
            "This is the deterministic offline mock provider. No real model is "
            "configured, so this reply is canned rather than reasoned. Set a "
            "provider key and point AUREL_CONFIG_DIR at a live config to get a "
            "real answer.",
            t0,
        )

    def healthcheck(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            status=ProviderStatus.AVAILABLE,
            model_name=self.config.model_name,
            message="deterministic offline mock provider",
        )

    def _response(
        self,
        raw: str,
        t0: float,
        *,
        error: str | None = None,
        refusal_reason: str | None = None,
    ) -> ModelResponse:
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
        return ModelResponse(
            provider_name=self.name,
            model_name=self.config.model_name,
            raw_text=raw,
            parsed_json=parsed,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            refusal_reason=refusal_reason,
            error=error,
        )


def _is_repo_plan_schema(schema: dict) -> bool:
    required = set(schema.get("required", [])) if isinstance(schema, dict) else set()
    return {"objective_summary", "files_to_modify", "proposed_steps"}.issubset(required)


def _repo_plan_payload(prompt: str) -> dict:
    target = "calculator.py"
    inspect = ["calculator.py", "test_calculator.py"]
    summary = "Fix repository task"
    if "divide" in prompt or "zero-division" in prompt or "zero division" in prompt:
        summary = "Add explicit zero-division validation to divide()."
    return {
        "objective_summary": summary,
        "files_to_inspect": inspect,
        "files_to_modify": [target],
        "proposed_steps": [
            {
                "step_id": "inspect",
                "action_type": "inspect",
                "target_path": target,
                "tool_name": "read_file",
                "reason": "Inspect the implementation before proposing a patch.",
                "expected_output": "Bounded source context for the target file.",
                "risk_class": "low",
            },
            {
                "step_id": "patch",
                "action_type": "patch",
                "target_path": target,
                "tool_name": "patch_file",
                "reason": "Apply the smallest source-only fix through the runtime.",
                "expected_output": "A narrow patch for the target implementation file.",
                "risk_class": "medium",
            },
            {
                "step_id": "test",
                "action_type": "test",
                "tool_name": "run_tests",
                "reason": "Verify behavior with the configured tests.",
                "expected_output": "The requested test command passes.",
                "risk_class": "medium",
            },
        ],
        "risk_level": "medium",
        "expected_tests": ["configured test command"],
        "requires_approval": True,
        "assumptions": ["Patch generation remains deterministic and governed."],
        "refusal_reason": None,
    }
