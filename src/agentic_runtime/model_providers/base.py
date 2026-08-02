"""
Provider base contracts for P0.12 Real LLM Adapter Layer.

Providers generate structured plans only. They never execute tools and never
receive runtime authority to act.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    UNCONFIGURED = "unconfigured"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0   # extended-thinking / reasoning tokens, when the provider reports them


@dataclass
class ProviderHealth:
    provider_name: str
    status: ProviderStatus
    model_name: str = ""
    message: str = ""
    latency_ms: Optional[float] = None

    @property
    def ok(self) -> bool:
        return self.status is ProviderStatus.AVAILABLE


@dataclass
class ModelProviderConfig:
    provider_name: str
    model_name: str = ""
    api_key_env: str = ""
    base_url: str = ""
    timeout_seconds: float = 30.0
    temperature: float = 0.0
    max_tokens: int = 2048
    extra_headers: dict[str, str] = field(default_factory=dict)
    # The RESOLVED key, when the caller already went through the secret chain
    # (env → OS keyring → file-0600). Empty means "read api_key_env yourself",
    # which keeps every adapter constructed without a config working unchanged.
    # Never serialize this field — `to_dict`-style helpers must skip it.
    api_key: str = ""

    def resolve_api_key(self) -> str:
        """The key to authenticate with: the resolved value, else the env var.

        Adapters must call this instead of reading ``os.environ`` directly, or a
        key that lives only in the keyring/file backend is invisible to them.
        """
        if self.api_key:
            return self.api_key
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "") or ""


@dataclass
class ModelRequest:
    system_prompt: str
    user_prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.0
    max_tokens: int = 2048
    timeout_seconds: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)
    reasoning_effort: str = "auto"   # request-only hint; providers MAY ignore. No execution/dispatch semantics.


@dataclass
class ModelResponse:
    provider_name: str
    model_name: str
    raw_text: str = ""
    parsed_json: Optional[dict[str, Any]] = None
    usage: Optional[TokenUsage] = None
    latency_ms: Optional[float] = None
    finish_reason: Optional[str] = None
    refusal_reason: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class StructuredPlanResult:
    ok: bool
    plan: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    refusal_reason: Optional[str] = None
    parsed_json: Optional[dict[str, Any]] = None


class ModelProvider(Protocol):
    name: str

    def generate_structured_plan(self, request: ModelRequest) -> ModelResponse: ...

    def complete_text(self, request: ModelRequest) -> ModelResponse:
        """Prose completion: no JSON mode, no parsing, raw_text is the answer.

        Optional by design. Callers must probe with ``getattr`` and fall back to
        ``generate_structured_plan`` so third-party and test-double providers
        that predate this method keep working.
        """
        ...

    def healthcheck(self) -> ProviderHealth: ...
