"""Policy Projection/API/Event Contract (P1.6.17).

Deterministic, JSON-safe, hash-ready read-model for P1.6 policy subsystem state.

P1.6.17 introduces the versioned policy projection/API/event contract required by
the Integration-First roadmap; it does NOT implement the final CLI binding, enforce
policy decisions, write to the Ledger, activate approvals, block commands, or change
runtime sandbox behavior.

Projection is not authority. Projection reports backend truth.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from .registry import PolicyCardRegistry


POLICY_PROJECTION_CONTRACT_VERSION: str = "policy_projection.v1"
POLICY_PROJECTION_GENERATED_BY: str = "custos-v0-p1617"
POLICY_PROJECTION_EVENT_VERSION: str = "policy_projection_event.v1"

CLI_BINDING_UNAVAILABLE_REASON: str = "CLI binding scheduled for P1.6.18"
SHELL_BINDING_UNAVAILABLE_REASON: str = "Shell binding not implemented in P1.6"

_SECTION_POLICY_REGISTRY = "policy_registry"
_SECTION_POLICY_RESOLVER = "policy_resolver"
_SECTION_CONFLICT_ALGEBRA = "conflict_algebra"
_SECTION_RESOLUTION_TRACE = "resolution_trace"
_SECTION_VIOLATION_TRACE = "violation_trace"
_SECTION_POLICY_HARNESS = "policy_harness"
_SECTION_CLI_BINDING = "cli_binding"
_SECTION_SHELL_BINDING = "shell_binding"

_ALL_SECTION_IDS: tuple[str, ...] = (
    _SECTION_POLICY_REGISTRY,
    _SECTION_POLICY_RESOLVER,
    _SECTION_CONFLICT_ALGEBRA,
    _SECTION_RESOLUTION_TRACE,
    _SECTION_VIOLATION_TRACE,
    _SECTION_POLICY_HARNESS,
    _SECTION_CLI_BINDING,
    _SECTION_SHELL_BINDING,
)

_SENSITIVE_METADATA_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "credential", "private_key", "access_key",
})
_SENSITIVE_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|credential|private[_-]?key|authorization)",
    re.IGNORECASE,
)
_COMMAND_BODY_KEYS = frozenset({
    "command", "command_body", "argv", "shell_command", "raw_command", "payload",
})


class PolicyProjectionSourceLabel(str, Enum):
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    SIMULATED = "SIMULATED"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class PolicyProjectionStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    SIMULATED = "simulated"


class PolicyProjectionEventType(str, Enum):
    POLICY_PROJECTION_BUILT = "POLICY_PROJECTION_BUILT"
    POLICY_SECTION_AVAILABLE = "POLICY_SECTION_AVAILABLE"
    POLICY_SECTION_UNAVAILABLE = "POLICY_SECTION_UNAVAILABLE"
    POLICY_PROJECTION_ERROR = "POLICY_PROJECTION_ERROR"


@dataclass(frozen=True)
class PolicyProjectionUnavailableReason:
    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ValueError("unavailable reason code must not be empty")
        if not self.message or not self.message.strip():
            raise ValueError("unavailable reason message must not be empty")

    def to_canonical_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class PolicyProjectionError:
    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ValueError("error code must not be empty")
        if not self.message or not self.message.strip():
            raise ValueError("error message must not be empty")

    def to_canonical_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class PolicyProjectionSection:
    section_id: str
    title: str
    status: PolicyProjectionStatus
    source: PolicyProjectionSourceLabel
    summary: str = ""
    capabilities: Mapping[str, str] = field(default_factory=dict)
    hashes: Mapping[str, str] = field(default_factory=dict)
    unavailable_reason: PolicyProjectionUnavailableReason | None = None
    error: PolicyProjectionError | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.section_id or not self.section_id.strip():
            raise ValueError("section_id must not be empty")
        if self.source is PolicyProjectionSourceLabel.UNAVAILABLE:
            if self.unavailable_reason is None:
                raise ValueError("UNAVAILABLE section requires unavailable_reason")
        if self.source is PolicyProjectionSourceLabel.ERROR:
            if self.error is None:
                raise ValueError("ERROR section requires error")

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "capabilities": dict(sorted(self.capabilities.items(), key=lambda i: i[0])),
            "hashes": dict(sorted(self.hashes.items(), key=lambda i: i[0])),
            "section_id": self.section_id,
            "source": self.source.value,
            "status": self.status.value,
            "summary": self.summary,
            "title": self.title,
        }
        if self.unavailable_reason is not None:
            result["unavailable_reason"] = self.unavailable_reason.to_canonical_dict()
        if self.error is not None:
            result["error"] = self.error.to_canonical_dict()
        if self.metadata:
            result["metadata"] = _sanitize_metadata(self.metadata)
        return dict(sorted(result.items(), key=lambda i: i[0]))


@dataclass(frozen=True)
class PolicyProjectionReadiness:
    registry_available: bool = False
    resolver_available: bool = False
    conflict_algebra_available: bool = False
    resolution_trace_available: bool = False
    violation_trace_available: bool = False
    harness_available: bool = False
    cli_binding_available: bool = False
    shell_binding_available: bool = False
    trace_binding_available: bool = False

    def to_canonical_dict(self) -> dict[str, bool]:
        return dict(sorted({
            "cli_binding_available": self.cli_binding_available,
            "conflict_algebra_available": self.conflict_algebra_available,
            "harness_available": self.harness_available,
            "registry_available": self.registry_available,
            "resolution_trace_available": self.resolution_trace_available,
            "resolver_available": self.resolver_available,
            "shell_binding_available": self.shell_binding_available,
            "trace_binding_available": self.trace_binding_available,
            "violation_trace_available": self.violation_trace_available,
        }.items(), key=lambda i: i[0]))


@dataclass(frozen=True)
class PolicyProjectionContract:
    contract_version: str = POLICY_PROJECTION_CONTRACT_VERSION
    projection_id: str = ""
    projection_hash: str = ""
    generated_by: str = POLICY_PROJECTION_GENERATED_BY
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE
    sections: tuple[PolicyProjectionSection, ...] = ()
    readiness: PolicyProjectionReadiness = field(default_factory=PolicyProjectionReadiness)
    unavailable_reasons: tuple[PolicyProjectionUnavailableReason, ...] = ()
    errors: tuple[PolicyProjectionError, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.contract_version != POLICY_PROJECTION_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {POLICY_PROJECTION_CONTRACT_VERSION}"
            )

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return policy_projection_to_json_safe_dict(self, include_hash=include_hash)

    def with_projection_hash(self) -> PolicyProjectionContract:
        h = policy_projection_hash(self)
        projection_id = f"policy-projection-{h[:16]}"
        return replace(self, projection_hash=h, projection_id=projection_id)


@dataclass(frozen=True)
class PolicyProjectionSnapshot:
    contract: PolicyProjectionContract
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            object.__setattr__(
                self,
                "generated_at",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        return {
            "contract": self.contract.to_canonical_dict(include_hash=include_hash),
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class PolicyRegistryProjection:
    section: PolicyProjectionSection

    @property
    def card_count(self) -> int:
        raw = self.section.capabilities.get("card_count", "0")
        try:
            return int(raw)
        except ValueError:
            return 0


@dataclass(frozen=True)
class PolicyResolverProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyConflictAlgebraProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyResolutionTraceProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyViolationTraceProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyHarnessProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyCliBindingProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyShellBindingProjection:
    section: PolicyProjectionSection


@dataclass(frozen=True)
class PolicyProjectionEvent:
    event_type: PolicyProjectionEventType
    event_version: str = POLICY_PROJECTION_EVENT_VERSION
    projection_hash: str = ""
    contract_version: str = POLICY_PROJECTION_CONTRACT_VERSION
    section_id: str = ""
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE
    status: PolicyProjectionStatus = PolicyProjectionStatus.AVAILABLE
    reason_codes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return policy_projection_event_to_json_safe_dict(self, include_hash=include_hash)


def _sanitize_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        key_str = str(key)
        key_lower = key_str.lower()
        if key_lower in _COMMAND_BODY_KEYS:
            continue
        if key_lower in _SENSITIVE_METADATA_KEYS or _SENSITIVE_PATTERN.search(key_str):
            continue
        if isinstance(value, Mapping):
            nested = _sanitize_metadata(value)
            if nested:
                sanitized[key_str] = nested
        elif isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key_str] = value
    return dict(sorted(sanitized.items(), key=lambda i: i[0]))


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, PolicyProjectionSection):
        return value.to_canonical_dict()
    if isinstance(value, PolicyProjectionReadiness):
        return value.to_canonical_dict()
    if isinstance(value, PolicyProjectionUnavailableReason):
        return value.to_canonical_dict()
    if isinstance(value, PolicyProjectionError):
        return value.to_canonical_dict()
    if isinstance(value, PolicyProjectionContract):
        return policy_projection_to_json_safe_dict(value, include_hash=False)
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _canonicalize(v) for k, v in sorted(value.items(), key=lambda i: i[0])}
    if hasattr(value, "to_canonical_dict"):
        return value.to_canonical_dict()
    return value


def _sections_to_canonical_dict(
    sections: Sequence[PolicyProjectionSection],
) -> dict[str, dict[str, Any]]:
    return {
        section.section_id: section.to_canonical_dict()
        for section in sorted(sections, key=lambda s: s.section_id)
    }


def policy_projection_to_json_safe_dict(
    contract: PolicyProjectionContract,
    *,
    include_hash: bool = True,
) -> dict[str, Any]:
    if not isinstance(contract, PolicyProjectionContract):
        raise ValueError("contract must be a PolicyProjectionContract")
    result: dict[str, Any] = {
        "contract_version": contract.contract_version,
        "errors": sorted(
            (error.to_canonical_dict() for error in contract.errors),
            key=lambda e: (e["code"], e["message"]),
        ),
        "generated_by": contract.generated_by,
        "metadata": _sanitize_metadata(contract.metadata),
        "projection_id": contract.projection_id,
        "readiness": contract.readiness.to_canonical_dict(),
        "sections": _sections_to_canonical_dict(contract.sections),
        "source": contract.source.value,
        "unavailable_reasons": sorted(
            (reason.to_canonical_dict() for reason in contract.unavailable_reasons),
            key=lambda r: (r["code"], r["message"]),
        ),
    }
    if include_hash and contract.projection_hash:
        result["projection_hash"] = contract.projection_hash
    return dict(sorted(result.items(), key=lambda i: i[0]))


def policy_projection_hash(contract: PolicyProjectionContract) -> str:
    canonical = json.dumps(
        policy_projection_to_json_safe_dict(contract, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def policy_projection_event_to_json_safe_dict(
    event: PolicyProjectionEvent,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    if not isinstance(event, PolicyProjectionEvent):
        raise ValueError("event must be a PolicyProjectionEvent")
    result: dict[str, Any] = {
        "contract_version": event.contract_version,
        "event_type": event.event_type.value,
        "event_version": event.event_version,
        "metadata": _sanitize_metadata(event.metadata),
        "projection_hash": event.projection_hash,
        "reason_codes": sorted(event.reason_codes),
        "section_id": event.section_id,
        "source": event.source.value,
        "status": event.status.value,
    }
    if include_hash:
        result["event_hash"] = policy_projection_event_hash(event)
    return dict(sorted(result.items(), key=lambda i: i[0]))


def policy_projection_event_hash(event: PolicyProjectionEvent) -> str:
    canonical = json.dumps(
        policy_projection_event_to_json_safe_dict(event, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_policy_registry_projection(
    *,
    registry: PolicyCardRegistry | None = None,
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
) -> PolicyRegistryProjection:
    from .registry import PolicyCardRegistry as RegistryCls

    capabilities: dict[str, str] = {
        "module": "agentic_runtime.policy_cards.registry",
        "registry_class": "PolicyCardRegistry",
        "family_count": "8",
    }
    hashes: dict[str, str] = {}
    summary = "Policy card registry module available"
    if registry is not None and isinstance(registry, RegistryCls):
        card_count = len(registry.list_card_ids())
        capabilities["card_count"] = str(card_count)
        if card_count > 0:
            hashes["registry_hash"] = registry.canonical_hash()
            summary = f"Policy card registry with {card_count} card(s)"
    section = PolicyProjectionSection(
        section_id=_SECTION_POLICY_REGISTRY,
        title="Policy Card Registry",
        status=PolicyProjectionStatus.AVAILABLE,
        source=source,
        summary=summary,
        capabilities=capabilities,
        hashes=hashes,
    )
    return PolicyRegistryProjection(section=section)


def build_policy_resolver_projection(
    *,
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
) -> PolicyResolverProjection:
    from .resolver import PolicyRuntimeResolver, resolve_policy_cards

    _ = PolicyRuntimeResolver
    _ = resolve_policy_cards
    section = PolicyProjectionSection(
        section_id=_SECTION_POLICY_RESOLVER,
        title="Policy Runtime Resolver",
        status=PolicyProjectionStatus.AVAILABLE,
        source=source,
        summary="Custos v0 shadow policy resolver available",
        capabilities={
            "module": "agentic_runtime.policy_cards.resolver",
            "resolver_class": "PolicyRuntimeResolver",
            "resolve_fn": "resolve_policy_cards",
            "mode": "shadow",
        },
    )
    return PolicyResolverProjection(section=section)


def build_policy_conflict_algebra_projection(
    *,
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
) -> PolicyConflictAlgebraProjection:
    from .conflict_algebra import resolve_policy_conflicts_strictest_wins

    _ = resolve_policy_conflicts_strictest_wins
    section = PolicyProjectionSection(
        section_id=_SECTION_CONFLICT_ALGEBRA,
        title="Policy Conflict Algebra",
        status=PolicyProjectionStatus.AVAILABLE,
        source=source,
        summary="Strictest-wins conflict algebra available",
        capabilities={
            "module": "agentic_runtime.policy_cards.conflict_algebra",
            "strategy": "strictest_wins",
        },
    )
    return PolicyConflictAlgebraProjection(section=section)


def build_policy_resolution_trace_projection(
    *,
    resolution_trace_hash: str = "",
    source: PolicyProjectionSourceLabel | None = None,
) -> PolicyResolutionTraceProjection:
    from .resolution_trace import (
        RESOLVER_VERSION,
        build_policy_resolution_trace_event,
        policy_trace_hash,
    )

    _ = build_policy_resolution_trace_event
    _ = policy_trace_hash
    effective_source = source or (
        PolicyProjectionSourceLabel.TRACE_VERIFIED
        if resolution_trace_hash
        else PolicyProjectionSourceLabel.LIVE
    )
    hashes: dict[str, str] = {}
    if resolution_trace_hash:
        hashes["resolution_trace_hash"] = resolution_trace_hash
    section = PolicyProjectionSection(
        section_id=_SECTION_RESOLUTION_TRACE,
        title="Policy Resolution Trace",
        status=PolicyProjectionStatus.AVAILABLE,
        source=effective_source,
        summary="Resolution trace hook available",
        capabilities={
            "module": "agentic_runtime.policy_cards.resolution_trace",
            "trace_version": RESOLVER_VERSION,
        },
        hashes=hashes,
    )
    return PolicyResolutionTraceProjection(section=section)


def build_policy_violation_trace_projection(
    *,
    violation_trace_hash: str = "",
    source: PolicyProjectionSourceLabel | None = None,
) -> PolicyViolationTraceProjection:
    from .violation_trace import build_policy_violation_trace_event, policy_violation_hash

    _ = build_policy_violation_trace_event
    _ = policy_violation_hash
    effective_source = source or (
        PolicyProjectionSourceLabel.TRACE_VERIFIED
        if violation_trace_hash
        else PolicyProjectionSourceLabel.LIVE
    )
    hashes: dict[str, str] = {}
    if violation_trace_hash:
        hashes["violation_trace_hash"] = violation_trace_hash
    section = PolicyProjectionSection(
        section_id=_SECTION_VIOLATION_TRACE,
        title="Policy Violation Trace",
        status=PolicyProjectionStatus.AVAILABLE,
        source=effective_source,
        summary="Violation trace hook available",
        capabilities={
            "module": "agentic_runtime.policy_cards.violation_trace",
        },
        hashes=hashes,
    )
    return PolicyViolationTraceProjection(section=section)


def build_policy_harness_projection(
    *,
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
) -> PolicyHarnessProjection:
    from .test_harness import HARNESS_VERSION, run_policy_harness_suite

    _ = run_policy_harness_suite
    section = PolicyProjectionSection(
        section_id=_SECTION_POLICY_HARNESS,
        title="Policy Test Harness",
        status=PolicyProjectionStatus.AVAILABLE,
        source=source,
        summary="Policy test harness available",
        capabilities={
            "module": "agentic_runtime.policy_cards.test_harness",
            "harness_version": HARNESS_VERSION,
        },
    )
    return PolicyHarnessProjection(section=section)


def build_policy_cli_binding_projection(*, available: bool = False) -> PolicyCliBindingProjection:
    if available:
        section = PolicyProjectionSection(
            section_id=_SECTION_CLI_BINDING,
            title="Policy CLI Binding",
            status=PolicyProjectionStatus.AVAILABLE,
            source=PolicyProjectionSourceLabel.LIVE,
            summary="Policy CLI binding available (P1.6.18)",
            capabilities={
                "module": "agentic_runtime.cli_modules.policy_commands",
                "binding": "cli",
            },
        )
    else:
        section = PolicyProjectionSection(
            section_id=_SECTION_CLI_BINDING,
            title="Policy CLI Binding",
            status=PolicyProjectionStatus.UNAVAILABLE,
            source=PolicyProjectionSourceLabel.UNAVAILABLE,
            summary="CLI binding not implemented in P1.6.17",
            unavailable_reason=PolicyProjectionUnavailableReason(
                code="CLI_BINDING_DEFERRED",
                message=CLI_BINDING_UNAVAILABLE_REASON,
            ),
        )
    return PolicyCliBindingProjection(section=section)


def build_policy_shell_binding_projection() -> PolicyShellBindingProjection:
    section = PolicyProjectionSection(
        section_id=_SECTION_SHELL_BINDING,
        title="Policy Shell Binding",
        status=PolicyProjectionStatus.UNAVAILABLE,
        source=PolicyProjectionSourceLabel.UNAVAILABLE,
        summary="Shell binding not implemented in P1.6",
        unavailable_reason=PolicyProjectionUnavailableReason(
            code="SHELL_BINDING_UNAVAILABLE",
            message=SHELL_BINDING_UNAVAILABLE_REASON,
        ),
    )
    return PolicyShellBindingProjection(section=section)


def _section_is_available(section: PolicyProjectionSection) -> bool:
    return section.status is PolicyProjectionStatus.AVAILABLE


def _build_readiness(sections: Sequence[PolicyProjectionSection]) -> PolicyProjectionReadiness:
    by_id = {section.section_id: section for section in sections}
    resolution = by_id.get(_SECTION_RESOLUTION_TRACE)
    violation = by_id.get(_SECTION_VIOLATION_TRACE)
    trace_binding = False
    if resolution is not None and _section_is_available(resolution):
        trace_binding = True
    if violation is not None and _section_is_available(violation):
        trace_binding = True
    return PolicyProjectionReadiness(
        registry_available=_section_is_available(by_id[_SECTION_POLICY_REGISTRY]),
        resolver_available=_section_is_available(by_id[_SECTION_POLICY_RESOLVER]),
        conflict_algebra_available=_section_is_available(by_id[_SECTION_CONFLICT_ALGEBRA]),
        resolution_trace_available=_section_is_available(by_id[_SECTION_RESOLUTION_TRACE]),
        violation_trace_available=_section_is_available(by_id[_SECTION_VIOLATION_TRACE]),
        harness_available=_section_is_available(by_id[_SECTION_POLICY_HARNESS]),
        cli_binding_available=_section_is_available(by_id[_SECTION_CLI_BINDING]),
        shell_binding_available=_section_is_available(by_id[_SECTION_SHELL_BINDING]),
        trace_binding_available=trace_binding,
    )


def _safe_build_section(
    builder: Any,
    *,
    section_id: str,
    title: str,
    kwargs: Mapping[str, Any] | None = None,
) -> PolicyProjectionSection:
    try:
        result = builder(**dict(kwargs or {}))
        if hasattr(result, "section"):
            return result.section
        if isinstance(result, PolicyProjectionSection):
            return result
        raise TypeError(f"builder for {section_id} returned unexpected type")
    except Exception as exc:
        return PolicyProjectionSection(
            section_id=section_id,
            title=title,
            status=PolicyProjectionStatus.ERROR,
            source=PolicyProjectionSourceLabel.ERROR,
            summary=f"Projection failed for {section_id}",
            error=PolicyProjectionError(
                code="PROJECTION_SECTION_ERROR",
                message=f"{type(exc).__name__}: {exc}",
            ),
        )


def build_policy_projection_contract(
    *,
    registry: PolicyCardRegistry | None = None,
    resolution_trace_hash: str = "",
    violation_trace_hash: str = "",
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
    cli_binding_available: bool = False,
) -> PolicyProjectionContract:
    registry_kwargs: dict[str, Any] = {"source": source}
    if registry is not None:
        registry_kwargs["registry"] = registry

    sections = (
        _safe_build_section(
            build_policy_registry_projection,
            section_id=_SECTION_POLICY_REGISTRY,
            title="Policy Card Registry",
            kwargs=registry_kwargs,
        ),
        _safe_build_section(
            build_policy_resolver_projection,
            section_id=_SECTION_POLICY_RESOLVER,
            title="Policy Runtime Resolver",
            kwargs={"source": source},
        ),
        _safe_build_section(
            build_policy_conflict_algebra_projection,
            section_id=_SECTION_CONFLICT_ALGEBRA,
            title="Policy Conflict Algebra",
            kwargs={"source": source},
        ),
        _safe_build_section(
            build_policy_resolution_trace_projection,
            section_id=_SECTION_RESOLUTION_TRACE,
            title="Policy Resolution Trace",
            kwargs={
                "resolution_trace_hash": resolution_trace_hash,
                "source": (
                    PolicyProjectionSourceLabel.TRACE_VERIFIED
                    if resolution_trace_hash
                    else source
                ),
            },
        ),
        _safe_build_section(
            build_policy_violation_trace_projection,
            section_id=_SECTION_VIOLATION_TRACE,
            title="Policy Violation Trace",
            kwargs={
                "violation_trace_hash": violation_trace_hash,
                "source": (
                    PolicyProjectionSourceLabel.TRACE_VERIFIED
                    if violation_trace_hash
                    else source
                ),
            },
        ),
        _safe_build_section(
            build_policy_harness_projection,
            section_id=_SECTION_POLICY_HARNESS,
            title="Policy Test Harness",
            kwargs={"source": source},
        ),
        build_policy_cli_binding_projection(available=cli_binding_available).section,
        build_policy_shell_binding_projection().section,
    )

    unavailable_reasons: list[PolicyProjectionUnavailableReason] = []
    for section in sections:
        if section.unavailable_reason is not None:
            unavailable_reasons.append(section.unavailable_reason)

    errors: list[PolicyProjectionError] = []
    for section in sections:
        if section.error is not None:
            errors.append(section.error)

    readiness = _build_readiness(sections)
    contract = PolicyProjectionContract(
        source=source,
        sections=sections,
        readiness=readiness,
        unavailable_reasons=tuple(unavailable_reasons),
        errors=tuple(errors),
        metadata=dict(metadata or {}),
    )
    return contract.with_projection_hash()


def build_policy_projection_snapshot(
    *,
    registry: PolicyCardRegistry | None = None,
    resolution_trace_hash: str = "",
    violation_trace_hash: str = "",
    source: PolicyProjectionSourceLabel = PolicyProjectionSourceLabel.LIVE,
    metadata: Mapping[str, Any] | None = None,
) -> PolicyProjectionSnapshot:
    contract = build_policy_projection_contract(
        registry=registry,
        resolution_trace_hash=resolution_trace_hash,
        violation_trace_hash=violation_trace_hash,
        source=source,
        metadata=metadata,
    )
    return PolicyProjectionSnapshot(contract=contract)


def build_policy_projection_event(
    *,
    event_type: PolicyProjectionEventType,
    contract: PolicyProjectionContract | None = None,
    section: PolicyProjectionSection | None = None,
    reason_codes: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> PolicyProjectionEvent:
    projection_hash = contract.projection_hash if contract is not None else ""
    section_id = section.section_id if section is not None else ""
    event_source = section.source if section is not None else PolicyProjectionSourceLabel.LIVE
    event_status = section.status if section is not None else PolicyProjectionStatus.AVAILABLE
    return PolicyProjectionEvent(
        event_type=event_type,
        projection_hash=projection_hash,
        section_id=section_id,
        source=event_source,
        status=event_status,
        reason_codes=tuple(sorted(reason_codes)),
        metadata=dict(metadata or {}),
    )
