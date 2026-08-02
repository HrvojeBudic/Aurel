"""Shared plain-prose completion over OpenAI-compatible chat endpoints.

The provider layer historically had exactly ONE path — ``generate_structured_plan``
— which demands JSON and converts any prose answer into
``malformed_provider_response``. That made a conversational reply structurally
impossible: the model could emit a tool plan or be reported as broken, nothing
else.

This is the prose path. Same endpoint, same auth, but **no** ``response_format``
and **no** ``json.loads``: what the model wrote is what the caller gets. Callers
that want a plan keep using ``generate_structured_plan``; the conversation engine
classifies the returned text itself, so a model that chooses to answer with a
plan is still routed to PROPOSE.

OpenAI, DeepSeek, Qwen and Kimi share the ``/chat/completions`` shape, so they
share this helper. Anthropic (``/v1/messages``) and Ollama (``/api/chat``) carry
their own implementations.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .base import ModelProviderConfig, ModelRequest, ModelResponse, TokenUsage
from .http_utils import post_json

# A provider-specific parser turning a raw response body into real token usage.
UsageParser = Callable[[Optional[dict[str, Any]]], Optional[TokenUsage]]


def openai_style_text(
    name: str,
    config: ModelProviderConfig,
    request: ModelRequest,
    *,
    usage_from: UsageParser,
) -> ModelResponse:
    """One prose completion against an OpenAI-compatible ``/chat/completions``."""
    key = config.resolve_api_key()
    if not key:
        return ModelResponse(name, config.model_name,
                             error=f"{config.api_key_env} not configured")

    payload = {
        "model": config.model_name,
        "messages": [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    data, error, latency = post_json(
        f"{config.base_url.rstrip('/')}/chat/completions",
        payload,
        headers={"Authorization": f"Bearer {key}"},
        timeout=request.timeout_seconds,
    )
    if error:
        return ModelResponse(name, config.model_name, error=error, latency_ms=latency)

    # Bound before the try so a malformed envelope still returns whatever text
    # was recovered — the caller decides what to do with a partial answer.
    raw = ""
    try:
        choice = (data or {}).get("choices", [{}])[0]
        msg = choice.get("message", {})
        raw = msg.get("content") or ""
        return ModelResponse(
            name,
            config.model_name,
            raw_text=raw,
            parsed_json=None,          # prose is never parsed
            usage=usage_from(data),
            latency_ms=latency,
            finish_reason=choice.get("finish_reason"),
            refusal_reason=msg.get("refusal"),
        )
    except (KeyError, IndexError, TypeError) as e:
        return ModelResponse(name, config.model_name, raw_text=raw,
                             error=f"malformed_provider_response:{type(e).__name__}",
                             latency_ms=latency)
