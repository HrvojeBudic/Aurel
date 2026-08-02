"""Provider-aware Model Router (P0.12 + P1.1 config boundary).

The model layer can only generate structured plans. It never executes tools.
The entity still sends model output through ``PlanValidator`` before the runtime
may turn steps into ``CommandEnvelope`` proposals.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, Protocol

from .model_config import (
    CONFIG_DIR_ENV,
    SUPPORTED_PROVIDER_TYPES,
    ModelConfigBundle,
    ModelConfigError,
    ModelProfile,
    ProviderConfigLoader,
    ProviderProfile,
)
from .model_providers.base import (ModelProvider, ModelProviderConfig,
                                   ModelRequest, ModelResponse, ProviderHealth,
                                   ProviderStatus)
from .model_providers.mock_provider import MockProvider
from .model_providers.schemas import (STRUCTURED_PLAN_SCHEMA, refusal_json,
                                      validate_structured_plan_text)
from .secrets import EnvSecretProvider, SecretRedactor
from .secrets_store import LayeredSecretProvider


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
    def __init__(
        self,
        default_provider: str | None = None,
        *,
        config: ModelConfigBundle | None = None,
        config_dir: str | Path | None = None,
        secret_provider: EnvSecretProvider | None = None,
    ) -> None:
        self._profiles: dict[str, list[ModelClient]] = {}
        # F2: distinguish an OPERATOR-CHOSEN provider (arg or env) from the
        # implicit "mock" default, so profiles that forbid a silent mock fallback
        # (standard/hardened set AUREL_ALLOW_MOCK_FALLBACK=0) can fail honestly.
        self._provider_defaulted = (
            default_provider is None and "AUREL_MODEL_PROVIDER" not in os.environ
        )
        self.default_provider = default_provider or os.environ.get(
            "AUREL_MODEL_PROVIDER", "mock")
        self._config = config
        # Opt-in: with AUREL_CONFIG_DIR unset a router built without an explicit
        # dir stays configless (the historical mock behavior). Setting it makes
        # every router in the process load the operator's providers/profiles.
        if config_dir is None and config is None:
            config_dir = os.environ.get(CONFIG_DIR_ENV, "").strip() or None
        self._config_dir = Path(config_dir) if config_dir else None
        # The full env → OS keyring → file-0600 chain, so a key stored with
        # `aurel secrets set` is visible to the model layer (not env-only).
        self._secrets = secret_provider or LayeredSecretProvider()
        self._redactor = SecretRedactor()
        if self._config is None and self._config_dir is not None:
            self._config = ProviderConfigLoader(self._config_dir).load()
        self._active_profile: Optional[str] = None

    @property
    def config(self) -> ModelConfigBundle | None:
        return self._config

    def load_config(self, config_dir: str | Path | None = None) -> ModelConfigBundle:
        loader = ProviderConfigLoader(config_dir or self._config_dir)
        self._config = loader.load()
        return self._config

    def list_model_profiles(self) -> list[str]:
        if self._config is None:
            return sorted(self._profiles.keys()) or ["balanced"]
        return self._config.list_profile_names()

    def select_profile(self, name: str) -> ModelProfile:
        if self._config is None:
            raise ModelConfigError("no model config loaded; call load_config() first")
        profile = self._config.get_profile(name)
        self._register_config_profile(profile)
        self._active_profile = name
        return profile

    def select_profile_for_task(self, task: str) -> ModelProfile | None:
        if self._config is None:
            return None
        profile = self._config.profile_for_task(task)
        if profile is None:
            return None
        self._register_config_profile(profile)
        self._active_profile = profile.name
        return profile

    def register(self, profile: str, clients: list[ModelClient]) -> None:
        self._profiles[profile] = clients

    def configure_default(self) -> None:
        """Register the default provider for ``balanced`` if none exists."""
        if "balanced" not in self._profiles:
            if self._config is not None:
                planning = self._config.profile_for_task("balanced")
                if planning is None:
                    planning = self._config.profile_for_task("planning")
                if planning is not None:
                    self._register_config_profile(planning)
                    return
            # F2 honest-fail: in profiles that forbid the silent mock fallback
            # (AUREL_ALLOW_MOCK_FALLBACK=0), an implicitly-defaulted "mock" with
            # no model config is refused honestly instead of silently answering.
            # An operator who EXPLICITLY chose mock (arg/env) still gets mock.
            mock_fallback_forbidden = (
                os.environ.get("AUREL_ALLOW_MOCK_FALLBACK", "1").strip() == "0"
            )
            if (mock_fallback_forbidden and self._provider_defaulted
                    and self.default_provider == "mock"):
                self.register("balanced", [_BlockedModelClient(
                    "balanced",
                    "no model provider configured (silent mock fallback is "
                    "disabled in this profile; set a provider key or "
                    "AUREL_MODEL_PROVIDER)",
                    redactor=self._redactor,
                )])
                return
            self.register("balanced", [ProviderModelClient(
                create_provider(self.default_provider))])

    def complete(self, profile: str, system: str, user: str) -> tuple[str, str]:
        self.configure_default()
        block = self._check_profile_allowed(profile)
        if block:
            return refusal_json(block), "router"
        clients = self._clients_for(profile)
        if not clients:
            return refusal_json(f"no model registered for profile '{profile}'"), "router"
        last_err = ""
        last_refusal: tuple[str, str] | None = None
        for i, client in enumerate(clients):  # ranked; failover down the list
            try:
                raw = client.complete(system, user)
            except Exception as e:  # provider down -> try next (commodity!)
                last_err = self._redactor.redact(f"{type(e).__name__}: {e}")
                continue
            normalized = _normalize_or_refuse(raw)
            # F2: a refusal envelope (missing key, HTTP failure, provider error)
            # fails over to the next ranked link; the LAST link's refusal is
            # returned honestly. Single-client profiles behave exactly as before.
            if _is_provider_refusal(normalized) and i < len(clients) - 1:
                last_refusal = (normalized, client.name)
                continue
            return normalized, client.name
        if last_refusal is not None:
            return last_refusal
        return refusal_json(
            self._redactor.redact(f"all providers failed for '{profile}': {last_err}")
        ), "router"

    def complete_with_usage(self, profile: str, system: str, user: str):
        """Like :meth:`complete`, but returns ``(raw, provider_name, usage)`` so
        callers can charge real token usage. ``usage`` is ``None`` on refusal /
        router-level block / providers that do not report it."""
        self.configure_default()
        block = self._check_profile_allowed(profile)
        if block:
            return refusal_json(block), "router", None
        clients = self._clients_for(profile)
        if not clients:
            return refusal_json(f"no model registered for profile '{profile}'"), "router", None
        last_err = ""
        last_refusal: tuple[str, str] | None = None
        for i, client in enumerate(clients):  # ranked; failover down the list
            try:
                if hasattr(client, "complete_with_usage"):
                    raw, usage = client.complete_with_usage(system, user)
                else:
                    # clients that don't surface usage → estimate_only downstream
                    raw, usage = client.complete(system, user), None
            except Exception as e:  # provider down -> try next (commodity!)
                last_err = self._redactor.redact(f"{type(e).__name__}: {e}")
                continue
            normalized = _normalize_or_refuse(raw)
            if _is_provider_refusal(normalized) and i < len(clients) - 1:
                last_refusal = (normalized, client.name)
                continue
            return normalized, client.name, usage
        if last_refusal is not None:
            return last_refusal[0], last_refusal[1], None
        return refusal_json(
            self._redactor.redact(f"all providers failed for '{profile}': {last_err}")
        ), "router", None

    def complete_text(self, profile: str, system: str, user: str):
        """Prose completion with the same ranked failover as
        :meth:`complete_with_usage`. Returns ``(raw, provider_name, usage)``.

        Crucially it does NOT run ``_normalize_or_refuse``: that helper validates
        text against the structured-plan schema, which would turn every prose
        answer — the whole point of this path — back into a refusal. Failover is
        therefore driven by explicit refusal envelopes only.
        """
        self.configure_default()
        block = self._check_profile_allowed(profile)
        if block:
            return refusal_json(block), "router", None
        clients = self._clients_for(profile)
        if not clients:
            return refusal_json(f"no model registered for profile '{profile}'"), "router", None
        last_err = ""
        last_refusal: tuple[str, str] | None = None
        for i, client in enumerate(clients):  # ranked; failover down the list
            try:
                if hasattr(client, "complete_text_with_usage"):
                    raw, usage = client.complete_text_with_usage(system, user)
                elif hasattr(client, "complete_with_usage"):
                    raw, usage = client.complete_with_usage(system, user)
                else:
                    raw, usage = client.complete(system, user), None
            except Exception as e:  # provider down -> try next
                last_err = self._redactor.redact(f"{type(e).__name__}: {e}")
                continue
            if _is_provider_refusal(raw) and i < len(clients) - 1:
                last_refusal = (raw, client.name)
                continue
            return raw, client.name, usage
        if last_refusal is not None:
            return last_refusal[0], last_refusal[1], None
        return refusal_json(
            self._redactor.redact(f"all providers failed for '{profile}': {last_err}")
        ), "router", None

    def complete_with_evidence(
        self, profile: str, system: str, user: str
    ):
        """SPINE-LIVE-0: ``complete()`` plus a live-with-evidence ref.

        Additive over ``complete()`` — same completion path, plus a
        ``ModelCallEvidenceRef`` proving a real model call happened. Refusals
        are captured honestly and are never ``available``. Imported lazily so
        the spine primitive stays optional and cycle-free.
        """
        from .spine.live_evidence import (
            ModelCallEvidenceRef,
            capture_model_call_evidence,
        )

        raw, model_name = self.complete(profile, system, user)
        evidence: ModelCallEvidenceRef = capture_model_call_evidence(
            profile=profile,
            model_name=model_name,
            system=system,
            user=user,
            raw_response=raw,
        )
        return raw, model_name, evidence

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
        block = self._check_profile_allowed(profile)
        if block:
            return refusal_json(block), "router"
        clients = self._clients_for(profile)
        if not clients:
            return refusal_json(f"no model registered for profile '{profile}'"), "router"
        last_err = ""
        last_refusal: tuple[str, str] | None = None
        for i, client in enumerate(clients):
            try:
                complete = getattr(client, "complete_structured", None)
                if complete is not None:
                    raw = complete(
                        system,
                        user,
                        output_schema,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                else:
                    raw = client.complete(system, user)
            except Exception as e:
                last_err = self._redactor.redact(f"{type(e).__name__}: {e}")
                continue
            if _is_provider_refusal(raw) and i < len(clients) - 1:
                last_refusal = (raw, client.name)
                continue
            return raw, client.name
        if last_refusal is not None:
            return last_refusal
        return refusal_json(
            self._redactor.redact(f"all providers failed for '{profile}': {last_err}")
        ), "router"

    def health(self) -> dict[str, list[ProviderHealth]]:
        out: dict[str, list[ProviderHealth]] = {}
        self.configure_default()
        for profile, clients in self._profiles.items():
            rows: list[ProviderHealth] = []
            for client in clients:
                provider = getattr(client, "provider", None)
                if provider is not None and hasattr(provider, "healthcheck"):
                    rows.append(self._redact_health(provider.healthcheck()))
                else:
                    rows.append(ProviderHealth(
                        provider_name=getattr(client, "name", "unknown"),
                        status=ProviderStatus.AVAILABLE,
                        message="legacy model client",
                    ))
            out[profile] = rows
        return out

    def provider_status(self) -> list[dict[str, str]]:
        """Configured provider status without secret values."""
        if self._config is None:
            self.configure_default()
            legacy: list[dict[str, str]] = []
            for profile, clients in self._profiles.items():
                for client in clients:
                    provider = getattr(client, "provider", None)
                    if provider is None:
                        continue
                    health = self._redact_health(provider.healthcheck())
                    legacy.append({
                        "profile": profile,
                        "provider": health.provider_name,
                        "status": health.status.value,
                        "model": health.model_name,
                        "message": self._redactor.redact(health.message),
                        "residency": "local" if health.provider_name in {"mock", "ollama"} else "remote",
                    })
            return legacy

        rows: list[dict[str, str]] = []
        for name, provider in sorted(self._config.providers.items()):
            enabled = self._provider_enabled(provider)
            secret_status = self._secret_status(provider)
            health = None
            if enabled:
                try:
                    inst = create_provider_from_profile(
                        provider,
                        provider.default_model,
                        self._secrets,
                    )
                    health = self._redact_health(inst.healthcheck())
                except Exception as e:
                    health = ProviderHealth(
                        provider_name=name,
                        status=ProviderStatus.ERROR,
                        message=self._redactor.redact(str(e)),
                    )
            rows.append({
                "provider": name,
                "type": provider.type,
                "residency": "remote" if provider.is_remote else "local",
                "configured": "yes" if enabled else "no",
                "enabled": "yes" if enabled else "no",
                "secret_status": secret_status,
                "status": health.status.value if health else ProviderStatus.UNCONFIGURED.value,
                "model": health.model_name if health else provider.default_model,
                "message": self._redactor.redact(health.message if health else ""),
            })
        return rows

    def _clients_for(self, profile: str) -> list[ModelClient]:
        if profile in self._profiles:
            return self._profiles[profile]
        if self._config is not None:
            try:
                mp = self._config.get_profile(profile)
                self._register_config_profile(mp)
                return self._profiles.get(profile, [])
            except ModelConfigError:
                pass
        return self._profiles.get(profile) or self._profiles.get("balanced") or []

    def _register_config_profile(self, profile: ModelProfile) -> None:
        # F2: a profile is a ranked chain (primary + failover links). Each link is
        # policy-checked independently; usable links become ranked clients so the
        # complete* loops fail over down the list. If NO link is usable the
        # profile registers a single honest blocked client (never silent mock).
        clients: list[ModelClient] = []
        blocks: list[str] = []
        for link in profile.chain():
            try:
                provider = self._config.get_provider(link.provider)
            except ModelConfigError as e:
                blocks.append(str(e))
                continue
            block = self._check_provider_allowed(provider, profile.name)
            if block:
                blocks.append(block)
                continue
            inst = create_provider_from_profile(provider, link.model, self._secrets)
            clients.append(ProviderModelClient(inst))
        if not clients:
            reason = "; ".join(blocks) or f"no usable provider for '{profile.name}'"
            self.register(profile.name, [
                _BlockedModelClient(profile.name, reason, redactor=self._redactor),
            ])
            return
        self.register(profile.name, clients)

    def _check_profile_allowed(self, profile: str) -> str:
        if self._config is None:
            return ""
        try:
            mp = self._config.get_profile(profile)
        except ModelConfigError:
            if profile == "balanced":
                return ""
            return ""
        # F2: a profile is allowed if ANY link in its chain is usable — a blocked
        # or keyless primary must not veto a healthy failover link. Only when
        # every link is blocked does the profile refuse (honest, combined reason).
        blocks: list[str] = []
        for link in mp.chain():
            provider = self._config.providers.get(link.provider)
            if provider is None:
                return ""
            block = self._check_provider_allowed(provider, profile)
            if not block:
                return ""
            blocks.append(block)
        return "; ".join(blocks)

    def _check_provider_allowed(self, provider: ProviderProfile, label: str) -> str:
        runtime = self._config.runtime
        if runtime.local_only and provider.is_remote:
            return f"local_only blocks remote provider '{provider.name}' for profile '{label}'"
        if provider.is_remote and not runtime.allow_remote_models:
            return f"allow_remote_models is false for provider '{provider.name}'"
        if provider.api_key_env:
            result = self._secrets.resolve_optional(provider.api_key_env)
            if not result.ok:
                return result.error
        return ""

    def _provider_enabled(self, provider: ProviderProfile) -> bool:
        runtime = self._config.runtime
        if provider.type not in SUPPORTED_PROVIDER_TYPES:
            return runtime.allow_unconfigured_providers
        if runtime.local_only and provider.is_remote:
            return False
        if provider.is_remote and not runtime.allow_remote_models:
            return False
        if provider.api_key_env:
            return self._secrets.resolve_optional(provider.api_key_env).ok
        return True

    def _secret_status(self, provider: ProviderProfile) -> str:
        if not provider.api_key_env:
            return "not_required"
        result = self._secrets.resolve_optional(provider.api_key_env)
        return "present" if result.ok else "missing"

    def _redact_health(self, health: ProviderHealth) -> ProviderHealth:
        return ProviderHealth(
            provider_name=health.provider_name,
            status=health.status,
            model_name=health.model_name,
            message=self._redactor.redact(health.message),
            latency_ms=health.latency_ms,
        )


class _BlockedModelClient:
    def __init__(self, name: str, reason: str, *, redactor: SecretRedactor) -> None:
        self.name = name
        self._reason = redactor.redact(reason)

    def complete(self, system: str, user: str) -> str:
        return refusal_json(self._reason)

    def complete_structured(
        self,
        system: str,
        user: str,
        output_schema: dict,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        return refusal_json(self._reason)


class ProviderModelClient:
    """Adapter from P0.12 provider protocol to the existing router client API."""

    def __init__(self, provider: ModelProvider, *, redactor: SecretRedactor | None = None) -> None:
        self.provider = provider
        self.name = getattr(provider, "name", "provider")
        self._redactor = redactor or SecretRedactor()

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
            return refusal_json(self._redactor.redact(resp.error))
        if resp.refusal_reason:
            return refusal_json(self._redactor.redact(resp.refusal_reason))
        return resp.raw_text

    def complete_with_usage(self, system: str, user: str):
        """Like :meth:`complete`, but also surfaces the provider's real
        ``TokenUsage`` (or ``None`` when unreported). Returns ``(raw, usage)``."""
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
            return refusal_json(self._redactor.redact(resp.error)), None
        if resp.refusal_reason:
            return refusal_json(self._redactor.redact(resp.refusal_reason)), None
        return resp.raw_text, resp.usage

    def complete_text_with_usage(self, system: str, user: str):
        """Prose completion. Returns ``(raw, usage)``; ``raw`` is a refusal
        envelope on failure so the router's failover logic still applies.

        Providers without ``complete_text`` fall back to the structured path —
        an older/third-party adapter degrades to plan-only rather than breaking.
        """
        req = ModelRequest(
            system_prompt=system,
            user_prompt=user,
            temperature=float(os.environ.get("AUREL_MODEL_TEMPERATURE", "0")),
            max_tokens=int(os.environ.get("AUREL_MODEL_MAX_TOKENS", "2048")),
            timeout_seconds=float(os.environ.get("AUREL_MODEL_TIMEOUT", "30")),
        )
        text_fn = getattr(self.provider, "complete_text", None)
        if text_fn is None:
            return self.complete_with_usage(system, user)
        resp = text_fn(req)
        if resp.error:
            return refusal_json(self._redactor.redact(resp.error)), None
        if resp.refusal_reason:
            return refusal_json(self._redactor.redact(resp.refusal_reason)), None
        return resp.raw_text, resp.usage

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
            return refusal_json(self._redactor.redact(resp.error))
        if resp.refusal_reason:
            return refusal_json(self._redactor.redact(resp.refusal_reason))
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
    if provider == "deepseek":
        from .model_providers.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider()
    if provider == "qwen":
        from .model_providers.qwen_provider import QwenProvider
        return QwenProvider()
    if provider == "kimi":
        from .model_providers.kimi_provider import KimiProvider
        return KimiProvider()
    return MockProvider(
        ModelProviderConfig(provider_name="mock", model_name="mock-deterministic"),
        failure_mode="refusal",
    )


def create_provider_from_profile(
    profile: ProviderProfile,
    model_name: str,
    secrets: EnvSecretProvider | None = None,
) -> ModelProvider:
    """Instantiate a provider from centralized configuration."""
    secrets = secrets or LayeredSecretProvider()
    model = model_name or profile.default_model
    if profile.default_model_env:
        model = os.environ.get(profile.default_model_env, model)
    base_url = profile.default_base_url
    if profile.base_url_env:
        base_url = os.environ.get(profile.base_url_env, base_url)
    api_key_env = profile.api_key_env
    api_key = ""
    if api_key_env:
        result = secrets.resolve_optional(api_key_env)
        if not result.ok and profile.is_remote:
            return _MissingSecretProvider(profile, result.error)
        # Carry the RESOLVED value, not just the variable name: the key may live
        # in the OS keyring or the 0600 file, where os.environ cannot see it.
        api_key = result.value or "" if result.ok else ""

    config = ModelProviderConfig(
        provider_name=profile.type,
        model_name=model,
        api_key_env=api_key_env,
        base_url=base_url,
        api_key=api_key,
    )
    if profile.type == "mock":
        return MockProvider(config)
    if profile.type == "openai":
        from .model_providers.openai_provider import OpenAIProvider
        return OpenAIProvider(config)
    if profile.type == "anthropic":
        from .model_providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(config)
    if profile.type == "ollama":
        from .model_providers.ollama_provider import OllamaProvider
        return OllamaProvider(config)
    if profile.type == "deepseek":
        from .model_providers.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider(config)
    if profile.type == "qwen":
        from .model_providers.qwen_provider import QwenProvider
        return QwenProvider(config)
    if profile.type == "kimi":
        from .model_providers.kimi_provider import KimiProvider
        return KimiProvider(config)
    return MockProvider(config, failure_mode="refusal")


class _MissingSecretProvider:
    """Structured unavailable provider when a remote secret is missing."""

    def __init__(self, profile: ProviderProfile, error: str) -> None:
        self.name = profile.type
        self.config = ModelProviderConfig(
            provider_name=profile.type,
            model_name=profile.default_model,
        )
        self._error = error

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(self.name, self.config.model_name, error=self._error)

    def healthcheck(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            status=ProviderStatus.UNCONFIGURED,
            model_name=self.config.model_name,
            message=self._error,
        )


def _is_provider_refusal(raw: str) -> bool:
    """True iff ``raw`` is the router/provider refusal envelope (F2 failover).

    Detection is deliberately narrow — exactly the ``refusal_payload`` signature
    (refusal_reason set, empty plan, intent_summary == "refused") — so a genuine
    model plan can never be mistaken for a provider failure."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    return (bool(data.get("refusal_reason"))
            and not data.get("plan")
            and data.get("intent_summary") == "refused")


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
