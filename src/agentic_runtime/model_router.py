"""Provider-aware Model Router (P0.12).

The model layer can only generate structured plans. It never executes tools.
The entity still sends model output through ``PlanValidator`` before the runtime
may turn steps into ``CommandEnvelope`` proposals.
"""
from __future__ import annotations

import json
import os
from typing import Optional, Protocol

from .model_providers.base import (ModelProvider, ModelProviderConfig,
                                   ModelRequest, ProviderHealth,
                                   ProviderStatus)
from .model_providers.mock_provider import MockProvider
from .model_providers.schemas import (STRUCTURED_PLAN_SCHEMA, refusal_json,
                                      validate_structured_plan_text)


class ModelClient(Protocol):
    name: str
    def complete(self, system: str, user: str) -> str: ...


class MockModelClient:
    """Backward-compatible deterministic client used by existing tests.

    Scripted responses are returned exactly as supplied so legacy plan-validator
    tests can still exercise invalid JSON / old plan shapes. Unscripted output
    is now the P0.12 structured plan shape.
    """
    name = "mock-deterministic"

    def __init__(
        self,
        scripted: Optional[dict[str, str]] = None,
        failure_mode: Optional[str] = None,
    ) -> None:
        self.provider = MockProvider(scripted=scripted, failure_mode=failure_mode)

    def complete(self, system: str, user: str) -> str:
        req = ModelRequest(
            system_prompt=system,
            user_prompt=user,
            output_schema=STRUCTURED_PLAN_SCHEMA,
        )
        resp = self.provider.generate_structured_plan(req)
        if resp.error:
            return refusal_json(resp.error)
        return resp.raw_text


class ModelRouter:
    def __init__(self, default_provider: str | None = None) -> None:
        self._profiles: dict[str, list[ModelClient]] = {}
        self.default_provider = default_provider or os.environ.get(
            "AUREL_MODEL_PROVIDER", "mock")

    def register(self, profile: str, clients: list[ModelClient]) -> None:
        self._profiles[profile] = clients

    def configure_default(self) -> None:
        """Register the default provider for ``balanced`` if none exists."""
        if "balanced" not in self._profiles:
            self.register("balanced", [ProviderModelClient(
                create_provider(self.default_provider))])

    def complete(self, profile: str, system: str, user: str) -> tuple[str, str]:
        self.configure_default()
        clients = self._profiles.get(profile) or self._profiles.get("balanced")
        if not clients:
            return refusal_json(f"no model registered for profile '{profile}'"), "router"
        last_err = ""
        for client in clients:  # ranked; failover down the list
            try:
                raw = client.complete(system, user)
                return _normalize_or_refuse(raw), client.name
            except Exception as e:  # provider down -> try next (commodity!)
                last_err = f"{type(e).__name__}: {e}"
                continue
        return refusal_json(f"all providers failed for '{profile}': {last_err}"), "router"

    def complete_structured(
        self,
        profile: str,
        system: str,
        user: str,
        output_schema: dict,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> tuple[str, str]:
        """Return provider text for a caller-supplied schema.

        ``complete()`` preserves the P0.12 entity plan schema normalization.
        Repository planning uses a different proposal-only schema, so it needs a
        raw structured completion path without vendor tool-calling.
        """
        self.configure_default()
        clients = self._profiles.get(profile) or self._profiles.get("balanced")
        if not clients:
            return refusal_json(f"no model registered for profile '{profile}'"), "router"
        last_err = ""
        for client in clients:
            try:
                complete = getattr(client, "complete_structured", None)
                if complete is not None:
                    return complete(
                        system,
                        user,
                        output_schema,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ), client.name
                return client.complete(system, user), client.name
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                continue
        return refusal_json(f"all providers failed for '{profile}': {last_err}"), "router"

    def health(self) -> dict[str, list[ProviderHealth]]:
        out: dict[str, list[ProviderHealth]] = {}
        self.configure_default()
        for profile, clients in self._profiles.items():
            rows: list[ProviderHealth] = []
            for client in clients:
                provider = getattr(client, "provider", None)
                if provider is not None and hasattr(provider, "healthcheck"):
                    rows.append(provider.healthcheck())
                else:
                    rows.append(ProviderHealth(
                        provider_name=getattr(client, "name", "unknown"),
                        status=ProviderStatus.AVAILABLE,
                        message="legacy model client",
                    ))
            out[profile] = rows
        return out


class ProviderModelClient:
    """Adapter from P0.12 provider protocol to the existing router client API."""

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider
        self.name = getattr(provider, "name", "provider")

    def complete(self, system: str, user: str) -> str:
        req = ModelRequest(
            system_prompt=system,
            user_prompt=user,
            output_schema=STRUCTURED_PLAN_SCHEMA,
            temperature=float(os.environ.get("AUREL_MODEL_TEMPERATURE", "0")),
            max_tokens=int(os.environ.get("AUREL_MODEL_MAX_TOKENS", "2048")),
            timeout_seconds=float(os.environ.get("AUREL_MODEL_TIMEOUT", "30")),
        )
        resp = self.provider.generate_structured_plan(req)
        if resp.error:
            return refusal_json(resp.error)
        if resp.refusal_reason:
            return refusal_json(resp.refusal_reason)
        return resp.raw_text

    def complete_structured(
        self,
        system: str,
        user: str,
        output_schema: dict,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        req = ModelRequest(
            system_prompt=system,
            user_prompt=user,
            output_schema=output_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=float(os.environ.get("AUREL_MODEL_TIMEOUT", "30")),
        )
        resp = self.provider.generate_structured_plan(req)
        if resp.error:
            return refusal_json(resp.error)
        if resp.refusal_reason:
            return refusal_json(resp.refusal_reason)
        return resp.raw_text


def create_provider(name: str | None) -> ModelProvider:
    provider = (name or "mock").lower()
    if provider == "mock":
        return MockProvider()
    if provider == "openai":
        from .model_providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if provider == "anthropic":
        from .model_providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if provider == "ollama":
        from .model_providers.ollama_provider import OllamaProvider
        return OllamaProvider()
    return MockProvider(
        ModelProviderConfig(provider_name="mock", model_name="mock-deterministic"),
        failure_mode="refusal",
    )


def _normalize_or_refuse(raw: str) -> str:
    """Normalize provider output while preserving legacy scripted tests.

    Structured outputs must pass P0.12 schema validation. Legacy tests that only
    return ``{"plan": ...}`` remain accepted and are normalized with default
    structured fields so the entity still reaches ``PlanValidator``.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(data, dict):
        return raw

    if set(data) == {"plan"} or ("plan" in data and "intent_summary" not in data):
        # Legacy scripted tests intentionally exercise PlanValidator's old
        # failure modes (empty plan, missing step fields, unknown tools).
        return raw

    result = validate_structured_plan_text(raw)
    if result.ok:
        return raw
    return refusal_json("provider schema violation: " + "; ".join(result.errors))
