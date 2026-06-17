"""
Provider base contracts for P0.12 Real LLM Adapter Layer.

Providers generate structured plans only. They never execute tools and never
receive runtime authority to act.
"""
from __future__ import annotations

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

    def healthcheck(self) -> ProviderHealth: ...
