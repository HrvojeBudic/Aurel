"""DeepSeek provider adapter (OpenAI-compatible chat API).

DeepSeek's chat endpoint is OpenAI-compatible but does not support OpenAI's
strict ``json_schema`` response format, so this adapter uses DeepSeek's JSON
mode (``response_format: {"type": "json_object"}``) and relies on the router's
schema validation of the returned text. API keys are read from the environment
only; no vendor tool-calling is used.

Model ids (2026): ``deepseek-v4-pro`` and ``deepseek-v4-flash``. The legacy
``deepseek-chat`` / ``deepseek-reasoner`` names are retired after 2026-07-24.
"""
from __future__ import annotations

import json
import os

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus)
from .http_utils import post_json

DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-pro"
DEEPSEEK_FLASH_MODEL = "deepseek-v4-flash"
DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"

_JSON_NUDGE = "\n\nRespond with a single valid JSON object only."


class DeepSeekProvider:
    name = "deepseek"

    def __init__(self, config: ModelProviderConfig | None = None) -> None:
        model = os.environ.get("AUREL_DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL)
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name=model,
            api_key_env=DEEPSEEK_API_KEY_ENV,
            base_url=os.environ.get(
                "AUREL_DEEPSEEK_BASE_URL", DEEPSEEK_DEFAULT_BASE_URL
            ),
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
