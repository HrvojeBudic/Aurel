"""Centralized model/provider configuration (P1.1)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .secrets import SecretBoundaryViolation, assert_no_raw_secrets_in_yaml
from .yaml_minimal import YamlParseError, load_yaml

SUPPORTED_PROVIDER_TYPES = frozenset(
    {"mock", "ollama", "openai", "anthropic", "deepseek", "qwen", "kimi"}
)
REMOTE_PROVIDER_TYPES = frozenset({"openai", "anthropic", "deepseek", "qwen", "kimi"})
LOCAL_PROVIDER_TYPES = frozenset({"mock", "ollama"})


class ModelConfigError(ValueError):
    pass


class ModelRoutingMode(str, Enum):
    PROFILE = "profile"
    TASK = "task"
    DEFAULT = "default"


@dataclass
class ProviderProfile:
    name: str
    type: str
    description: str = ""
    residency: str = "local"
    api_key_env: str = ""
    base_url_env: str = ""
    default_model_env: str = ""
    default_base_url: str = ""
    default_model: str = ""

    @property
    def is_remote(self) -> bool:
        return self.residency == "remote" or self.type in REMOTE_PROVIDER_TYPES

    @property
    def is_local(self) -> bool:
        return not self.is_remote


@dataclass(frozen=True)
class FailoverTarget:
    """One ranked fallback (provider, model) link in a profile's chain (F2)."""
    provider: str
    model: str


@dataclass
class ModelProfile:
    name: str
    provider: str
    model: str
    purpose: str
    allowed_tasks: list[str] = field(default_factory=list)
    # F2: ranked failover chain after the primary. Absent ⇒ single-provider
    # profile, byte-identical to pre-F2 behavior.
    failover: list[FailoverTarget] = field(default_factory=list)

    @property
    def residency_label(self) -> str:
        return "local" if self.provider in ("mock", "ollama") else "remote"

    def chain(self) -> list[FailoverTarget]:
        """The full ranked chain: primary first, then failovers."""
        return [FailoverTarget(self.provider, self.model), *self.failover]


@dataclass
class RuntimeModelConfig:
    local_only: bool = True
    allow_remote_models: bool = False
    allow_unconfigured_providers: bool = False
    require_secret_redaction: bool = True
    trace_model_calls: bool = True
    trace_prompt_summaries_only: bool = True
    store_raw_prompts: bool = False
    store_raw_provider_responses: bool = False


@dataclass
class ModelConfigBundle:
    providers: dict[str, ProviderProfile] = field(default_factory=dict)
    profiles: dict[str, ModelProfile] = field(default_factory=dict)
    runtime: RuntimeModelConfig = field(default_factory=RuntimeModelConfig)
    config_dir: Optional[str] = None

    def get_profile(self, name: str) -> ModelProfile:
        profile = self.profiles.get(name)
        if profile is None:
            raise ModelConfigError(f"unknown model profile: {name}")
        return profile

    def get_provider(self, name: str) -> ProviderProfile:
        provider = self.providers.get(name)
        if provider is None:
            raise ModelConfigError(f"unknown provider: {name}")
        return provider

    def profile_for_task(self, task: str) -> Optional[ModelProfile]:
        for profile in self.profiles.values():
            if task in profile.allowed_tasks:
                return profile
        return None

    def list_profile_names(self) -> list[str]:
        return sorted(self.profiles.keys())


class ProviderConfigLoader:
    """Load and validate model/provider configuration from agent/config/."""

    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else _default_config_dir()

    def load(self) -> ModelConfigBundle:
        providers_data = self._load_file("providers.yaml")
        models_data = self._load_file("models.yaml")
        runtime_data = self._load_file("runtime.yaml")
        bundle = self._parse(providers_data, models_data, runtime_data)
        bundle.config_dir = str(self.config_dir)
        self._validate(bundle)
        return bundle

    @staticmethod
    def load_defaults() -> ModelConfigBundle:
        """Safe in-memory defaults for tests (no filesystem required)."""
        loader = ProviderConfigLoader(config_dir=_builtin_config_dir())
        return loader.load()

    def _load_file(self, name: str) -> dict[str, Any]:
        path = self.config_dir / name
        if not path.is_file():
            raise ModelConfigError(f"missing config file: {path}")
        try:
            data = load_yaml(path.read_text(encoding="utf-8"))
        except YamlParseError as e:
            raise ModelConfigError(f"invalid YAML in {path}: {e}") from e
        assert_no_raw_secrets_in_yaml(data)
        return data

    def _parse(
        self,
        providers_data: dict[str, Any],
        models_data: dict[str, Any],
        runtime_data: dict[str, Any],
    ) -> ModelConfigBundle:
        providers: dict[str, ProviderProfile] = {}
        raw_providers = providers_data.get("providers") or {}
        if not isinstance(raw_providers, dict):
            raise ModelConfigError("providers.yaml: 'providers' must be a mapping")
        for name, spec in raw_providers.items():
            if not isinstance(spec, dict):
                raise ModelConfigError(f"provider '{name}' must be a mapping")
            providers[name] = ProviderProfile(
                name=name,
                type=str(spec.get("type", "")).lower(),
                description=str(spec.get("description", "")),
                residency=str(spec.get("residency", "local")).lower(),
                api_key_env=str(spec.get("api_key_env", "")),
                base_url_env=str(spec.get("base_url_env", "")),
                default_model_env=str(spec.get("default_model_env", "")),
                default_base_url=str(spec.get("default_base_url", "")),
                default_model=str(spec.get("default_model", "")),
            )

        profiles: dict[str, ModelProfile] = {}
        raw_profiles = models_data.get("profiles") or {}
        if not isinstance(raw_profiles, dict):
            raise ModelConfigError("models.yaml: 'profiles' must be a mapping")
        for name, spec in raw_profiles.items():
            if not isinstance(spec, dict):
                raise ModelConfigError(f"model profile '{name}' must be a mapping")
            allowed = spec.get("allowed_tasks") or []
            if not isinstance(allowed, list):
                raise ModelConfigError(f"profile '{name}': allowed_tasks must be a list")
            provider = str(spec.get("provider", ""))
            model = str(spec.get("model", ""))
            purpose = str(spec.get("purpose", name))
            if not provider:
                raise ModelConfigError(f"profile '{name}': provider is required")
            if not model:
                raise ModelConfigError(f"profile '{name}': model is required")
            raw_failover = spec.get("failover") or []
            if not isinstance(raw_failover, list):
                raise ModelConfigError(f"profile '{name}': failover must be a list")
            failover: list[FailoverTarget] = []
            for idx, link in enumerate(raw_failover):
                if not isinstance(link, dict) or not link.get("provider") or not link.get("model"):
                    raise ModelConfigError(
                        f"profile '{name}': failover[{idx}] needs 'provider' and 'model'")
                failover.append(FailoverTarget(
                    provider=str(link["provider"]), model=str(link["model"])))
            profiles[name] = ModelProfile(
                name=name,
                provider=provider,
                model=model,
                purpose=purpose,
                allowed_tasks=[str(t) for t in allowed],
                failover=failover,
            )

        runtime = RuntimeModelConfig(
            local_only=bool(runtime_data.get("local_only", True)),
            allow_remote_models=bool(runtime_data.get("allow_remote_models", False)),
            allow_unconfigured_providers=bool(
                runtime_data.get("allow_unconfigured_providers", False)
            ),
            require_secret_redaction=bool(runtime_data.get("require_secret_redaction", True)),
            trace_model_calls=bool(runtime_data.get("trace_model_calls", True)),
            trace_prompt_summaries_only=bool(
                runtime_data.get("trace_prompt_summaries_only", True)
            ),
            store_raw_prompts=bool(runtime_data.get("store_raw_prompts", False)),
            store_raw_provider_responses=bool(
                runtime_data.get("store_raw_provider_responses", False)
            ),
        )
        return ModelConfigBundle(providers=providers, profiles=profiles, runtime=runtime)

    def _validate(self, bundle: ModelConfigBundle) -> None:
        for pname, profile in bundle.profiles.items():
            # F2: every link in the chain (primary + failover) obeys the same rules.
            for link in profile.chain():
                if link.provider not in bundle.providers:
                    if not bundle.runtime.allow_unconfigured_providers:
                        raise ModelConfigError(
                            f"profile '{pname}' references unknown provider '{link.provider}'"
                        )
                    continue
                provider = bundle.providers[link.provider]
                if provider.type not in SUPPORTED_PROVIDER_TYPES:
                    raise ModelConfigError(
                        f"provider '{link.provider}' has unsupported type '{provider.type}'"
                    )
                if provider.is_remote and not bundle.runtime.allow_remote_models:
                    raise ModelConfigError(
                        f"profile '{pname}' uses remote provider '{link.provider}' "
                        "but allow_remote_models is false"
                    )
                if bundle.runtime.local_only and provider.is_remote:
                    raise ModelConfigError(
                        f"profile '{pname}' uses remote provider '{link.provider}' "
                        "but local_only is true"
                    )

        for name, provider in bundle.providers.items():
            if provider.type not in SUPPORTED_PROVIDER_TYPES:
                if not bundle.runtime.allow_unconfigured_providers:
                    raise ModelConfigError(
                        f"provider '{name}' has unsupported type '{provider.type}'"
                    )


def default_config_dir() -> Path:
    """Return the canonical default model/provider config directory."""
    return _default_config_dir()


CONFIG_DIR_ENV = "AUREL_CONFIG_DIR"


def _default_config_dir() -> Path:
    # An explicit operator override wins over every packaged default. It is
    # fail-closed on purpose: silently falling back to the all-mock packaged
    # config when the operator named a directory would hide a live-model
    # misconfiguration behind plausible-looking offline answers.
    override = os.environ.get(CONFIG_DIR_ENV, "").strip()
    if override:
        chosen = Path(override).expanduser()
        if not chosen.is_dir():
            raise ModelConfigError(
                f"{CONFIG_DIR_ENV}={override!r} is not a directory")
        return chosen
    # src/agentic_runtime/model_config.py -> repo root is parents[2]
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / "agent" / "config"
    if candidate.is_dir():
        return candidate
    return _builtin_config_dir()


def _builtin_config_dir() -> Path:
    return Path(__file__).resolve().parent / "_default_config"
