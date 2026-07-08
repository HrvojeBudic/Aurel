"""Local Ollama provider adapter."""
from __future__ import annotations

import json
import os

from .base import (ModelProviderConfig, ModelRequest, ModelResponse,
                   ProviderHealth, ProviderStatus, TokenUsage)
from .http_utils import post_json
from .schemas import STRUCTURED_PLAN_SCHEMA


def _usage_from(data: dict | None) -> TokenUsage | None:
    """Extract real token usage from an Ollama /api/chat response, or None.

    Ollama reports ``prompt_eval_count`` (input) and ``eval_count`` (output)
    on the final non-streamed message.
    """
    if not isinstance(data, dict):
        return None
    prompt = int(data.get("prompt_eval_count", 0) or 0)
    completion = int(data.get("eval_count", 0) or 0)
    if not prompt and not completion:
        return None
    return TokenUsage(prompt_tokens=prompt, completion_tokens=completion,
                      total_tokens=prompt + completion)


class OllamaProvider:
    name = "ollama"

    def __init__(self, config: ModelProviderConfig | None = None) -> None:
        self.config = config or ModelProviderConfig(
            provider_name=self.name,
            model_name=os.environ.get("AUREL_OLLAMA_MODEL", "llama3.1"),
            base_url=(
                os.environ.get("AUREL_OLLAMA_BASE_URL")
                or os.environ.get("OLLAMA_BASE_URL")
                or "http://localhost:11434"
            ),
        )

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse:
        schema = request.output_schema or STRUCTURED_PLAN_SCHEMA
        user = (
            f"{request.user_prompt}\n\n"
            "Return valid JSON only. Do not call tools. The runtime will decide "
            "whether any planned tool may execute."
        )
        payload = {
            "model": self.config.model_name,
            "stream": False,
            "format": schema,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        data, error, latency = post_json(
            f"{self.config.base_url.rstrip('/')}/api/chat",
            payload,
            timeout=request.timeout_seconds,
        )
        if error:
            return ModelResponse(self.name, self.config.model_name,
                                 error=error, latency_ms=latency)
        try:
            raw = ((data or {}).get("message") or {}).get("content", "")
            parsed = json.loads(raw) if raw else None
            return ModelResponse(
                self.name,
                self.config.model_name,
                raw_text=raw,
                parsed_json=parsed,
                latency_ms=latency,
                finish_reason=(data or {}).get("done_reason"),
                usage=_usage_from(data),
            )
        except (TypeError, json.JSONDecodeError) as e:
            return ModelResponse(self.name, self.config.model_name,
                                 error=f"malformed_provider_response:{type(e).__name__}",
                                 latency_ms=latency)

    def healthcheck(self) -> ProviderHealth:
        return ProviderHealth(
            self.name,
            ProviderStatus.UNAVAILABLE,
            self.config.model_name,
            "healthcheck does not call local Ollama unless explicitly used",
        )
