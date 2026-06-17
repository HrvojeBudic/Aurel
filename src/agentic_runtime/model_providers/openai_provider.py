"""Optional OpenAI provider adapter.

Uses stdlib HTTP, reads API keys from environment only, and requests structured
JSON. No vendor tool calling is used.
"""
from __future__ import annotations

import json
import os

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus)
from .http_utils import post_json
from .schemas import STRUCTURED_PLAN_SCHEMA


class OpenAIProvider:
    name = "openai"

    def __init__(self, config: ModelProviderConfig | None = None) -> None:
        model = os.environ.get("AUREL_OPENAI_MODEL", "gpt-4.1-mini")
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name=model,
            api_key_env="OPENAI_API_KEY",
            base_url=os.environ.get("AUREL_OPENAI_BASE_URL", "https://api.openai.com/v1"),
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
                {"role": "user", "content": request.user_prompt},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_plan",
                    "strict": True,
                    "schema": request.output_schema or STRUCTURED_PLAN_SCHEMA,
                },
            },
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
