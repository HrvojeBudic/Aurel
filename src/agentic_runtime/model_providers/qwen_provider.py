"""Qwen provider adapter (Alibaba DashScope, OpenAI-compatible chat API).

DashScope's compatible-mode endpoint is OpenAI-compatible; like DeepSeek it does
not support OpenAI's strict ``json_schema`` response format, so this adapter uses
JSON mode (``response_format: {"type": "json_object"}``) and relies on the
router's schema validation of the returned text. API keys are read from the
environment only; no vendor tool-calling is used.

Model ids (2026): ``qwen-max`` (planning-grade), ``qwen-plus``, ``qwen3-coder``.
This adapter is a deliberate thin clone of ``deepseek_provider.py`` — the F2
pattern is that every OpenAI-compatible provider differs only in constants.
"""
from __future__ import annotations

import json
import os

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus, TokenUsage)
from .http_utils import post_json

QWEN_DEFAULT_MODEL = "qwen-max"
QWEN_CODER_MODEL = "qwen3-coder"
QWEN_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_API_KEY_ENV = "DASHSCOPE_API_KEY"

_JSON_NUDGE = "\n\nRespond with a single valid JSON object only."


def _usage_from(data: dict | None) -> TokenUsage | None:
    """Extract real token usage from a Qwen (OpenAI-compatible) response."""
    usage = (data or {}).get("usage")
    if not isinstance(usage, dict):
        return None
    prompt = int(usage.get("prompt_tokens", 0) or 0)
    completion = int(usage.get("completion_tokens", 0) or 0)
    total = int(usage.get("total_tokens", 0) or 0) or (prompt + completion)
    details = usage.get("completion_tokens_details")
    reasoning = int(details.get("reasoning_tokens", 0) or 0) if isinstance(details, dict) else 0
    return TokenUsage(prompt_tokens=prompt, completion_tokens=completion,
                      total_tokens=total, reasoning_tokens=reasoning)


class QwenProvider:
    name = "qwen"

    def __init__(self, config: ModelProviderConfig | None = None) -> None:
        model = os.environ.get("AUREL_QWEN_MODEL", QWEN_DEFAULT_MODEL)
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name=model,
            api_key_env=QWEN_API_KEY_ENV,
            base_url=os.environ.get("AUREL_QWEN_BASE_URL", QWEN_DEFAULT_BASE_URL),
        )

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse:
        key = os.environ.get(self.config.api_key_env)
        if not key:
            return ModelResponse(
                self.name, self.config.model_name,
                error=f"{self.config.api_key_env} not configured")

        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt + _JSON_NUDGE},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_format": {"type": "json_object"},
        }
        data, error, latency = post_json(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=request.timeout_seconds,
        )
        if error:
            return ModelResponse(self.name, self.config.model_name,
                                 error=error, latency_ms=latency)
        try:
            choice = (data or {}).get("choices", [{}])[0]
            msg = choice.get("message", {})
            raw = msg.get("content") or ""
            parsed = json.loads(raw) if raw else None
            return ModelResponse(
                self.name,
                self.config.model_name,
                raw_text=raw,
                parsed_json=parsed,
                latency_ms=latency,
                finish_reason=choice.get("finish_reason"),
                refusal_reason=msg.get("refusal"),
                usage=_usage_from(data),
            )
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            return ModelResponse(self.name, self.config.model_name,
                                 error=f"malformed_provider_response:{type(e).__name__}",
                                 latency_ms=latency)

    def healthcheck(self) -> ProviderHealth:
        if not os.environ.get(self.config.api_key_env):
            return ProviderHealth(self.name, ProviderStatus.UNCONFIGURED,
                                  self.config.model_name,
                                  f"{self.config.api_key_env} not configured")
        return ProviderHealth(self.name, ProviderStatus.AVAILABLE,
                              self.config.model_name, "configured")
