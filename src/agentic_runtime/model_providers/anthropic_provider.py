"""Optional Anthropic provider adapter.

Uses structured-output prompting only. No vendor tool calling is used.
"""
from __future__ import annotations

import json
import os

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus, TokenUsage)
from .http_utils import post_json
from .schemas import STRUCTURED_PLAN_SCHEMA


def _usage_from(data: dict | None) -> TokenUsage | None:
    """Extract real token usage from an Anthropic response, or None if absent."""
    usage = (data or {}).get("usage")
    if not isinstance(usage, dict):
        return None
    prompt = int(usage.get("input_tokens", 0) or 0)
    completion = int(usage.get("output_tokens", 0) or 0)
    return TokenUsage(prompt_tokens=prompt, completion_tokens=completion,
                      total_tokens=prompt + completion, reasoning_tokens=0)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, config: ModelProviderConfig | None = None) -> None:
        model = os.environ.get("AUREL_ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name=model,
            api_key_env="ANTHROPIC_API_KEY",
            base_url=os.environ.get("AUREL_ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
        )

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse:
        key = os.environ.get(self.config.api_key_env)
        if not key:
            return ModelResponse(
                self.name, self.config.model_name,
                error=f"{self.config.api_key_env} not configured")

        schema_hint = json.dumps(request.output_schema or STRUCTURED_PLAN_SCHEMA)
        user = (
            f"{request.user_prompt}\n\n"
            "Return valid JSON only. It must conform to this JSON Schema:\n"
            f"{schema_hint}"
        )
        payload = {
            "model": self.config.model_name,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": user}],
        }
        data, error, latency = post_json(
            f"{self.config.base_url.rstrip('/')}/v1/messages",
            payload,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            timeout=request.timeout_seconds,
        )
        if error:
            return ModelResponse(self.name, self.config.model_name,
                                 error=error, latency_ms=latency)
        try:
            content = (data or {}).get("content", [])
            raw = "".join(block.get("text", "") for block in content
                          if block.get("type") == "text")
            parsed = json.loads(raw) if raw else None
            return ModelResponse(
                self.name,
                self.config.model_name,
                raw_text=raw,
                parsed_json=parsed,
                usage=_usage_from(data),
                latency_ms=latency,
                finish_reason=(data or {}).get("stop_reason"),
            )
        except (TypeError, json.JSONDecodeError) as e:
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
