"""Kimi provider adapter (Moonshot AI, OpenAI-compatible chat API).

Moonshot's endpoint is OpenAI-compatible; like DeepSeek/Qwen it uses JSON mode
(``response_format: {"type": "json_object"}``) with the router validating the
returned text against the schema. API keys are read from the environment only;
no vendor tool-calling is used.

Model ids (2026): ``kimi-k2`` (cheap challenger/review-grade),
``moonshot-v1-128k``. This adapter is a deliberate thin clone of
``deepseek_provider.py`` — every OpenAI-compatible provider differs only in
constants.
"""
from __future__ import annotations

import json
import os

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus, TokenUsage)
from .chat_common import openai_style_text
from .http_utils import post_json

KIMI_DEFAULT_MODEL = "kimi-k2"
KIMI_LONG_MODEL = "moonshot-v1-128k"
KIMI_DEFAULT_BASE_URL = "https://api.moonshot.ai/v1"
KIMI_API_KEY_ENV = "MOONSHOT_API_KEY"

_JSON_NUDGE = "\n\nRespond with a single valid JSON object only."


def _usage_from(data: dict | None) -> TokenUsage | None:
    """Extract real token usage from a Kimi (OpenAI-compatible) response."""
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


class KimiProvider:
    name = "kimi"

    def __init__(self, config: ModelProviderConfig | None = None) -> None:
        model = os.environ.get("AUREL_KIMI_MODEL", KIMI_DEFAULT_MODEL)
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name=model,
            api_key_env=KIMI_API_KEY_ENV,
            base_url=os.environ.get("AUREL_KIMI_BASE_URL", KIMI_DEFAULT_BASE_URL),
        )

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse:
        key = self.config.resolve_api_key()
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
        raw = ""
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
            return ModelResponse(self.name, self.config.model_name, raw_text=raw,
                                 error=f"malformed_provider_response:{type(e).__name__}",
                                 latency_ms=latency)

    def complete_text(self, request: ModelRequest) -> ModelResponse:
        """Prose completion — no JSON mode, no parsing (see chat_common)."""
        return openai_style_text(self.name, self.config, request,
                                 usage_from=_usage_from)

    def healthcheck(self) -> ProviderHealth:
        if not self.config.resolve_api_key():
            return ProviderHealth(self.name, ProviderStatus.UNCONFIGURED,
                                  self.config.model_name,
                                  f"{self.config.api_key_env} not configured")
        return ProviderHealth(self.name, ProviderStatus.AVAILABLE,
                              self.config.model_name, "configured")
