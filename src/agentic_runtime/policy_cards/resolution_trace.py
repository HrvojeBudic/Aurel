"""Policy Resolution Trace Hook (P1.6.14).

Deterministic, JSON-safe, hash-ready trace-compatible policy evidence objects.

P1.6.14 creates trace-compatible policy resolution evidence; it does NOT write
to the Ledger, enforce policy decisions, activate approvals, block commands,
or change runtime sandbox behavior.

Trace-compatible does not mean Ledger-integrated.
Evidence-ready does not mean enforced.
Nothing is enforced. Nothing is written to Ledger.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


RESOLVER_VERSION: str = "custos-v0-p1614"
TRACE_EVENT_TYPE: str = "policy_resolution_trace"
POLICY_PHASE: str = "custos_shadow_resolution"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyResolutionTraceEvent:
    """Deterministic trace-compatible policy resolution evidence.

    This is a pure data object: no enforcement, no Ledger write, no side effects.
    shadow_only is always True, enforced is always False.
    """

    trace_event_type: str = TRACE_EVENT_TYPE
    policy_phase: str = POLICY_PHASE
    resolver_version: str = RESOLVER_VERSION

    registry_hash: str = ""
    context_hash: str = ""
    resolution_hash: str = ""
    conflict_hash: str = ""
    projection_hash: str = ""
    runtime_snapshot_hash: str = ""

    effective_shadow_action: str = ""
    strictest_decision_rank: str = ""

    shadow_only: bool = True
    enforced: bool = False

    source_family_ids: tuple[str, ...] = ()
    source_card_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    conflict_codes: tuple[str, ...] = ()

    metadata: Mapping[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    trace_hash: str | None = None

    def __post_init__(self) -> None:
        if self.shadow_only is not True:
            raise ValueError("shadow_only must be True")
        if self.enforced is not False:
            raise ValueError("enforced must be False")
        if self.trace_event_type != TRACE_EVENT_TYPE:
            raise ValueError(f"trace_event_type must be {TRACE_EVENT_TYPE}")
        for field_name in ("registry_hash", "context_hash", "resolution_hash",
                           "conflict_hash", "projection_hash", "runtime_snapshot_hash"):
            val = getattr(self, field_name)
            if val and (not isinstance(val, str)):
                raise ValueError(f"{field_name} must be a string")

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return policy_trace_canonical_dict(self, include_hash=include_hash)

    def with_trace_hash(self) -> "PolicyResolutionTraceEvent":
        h = policy_trace_hash(self)
        return replace(self, trace_hash=h, trace_id=h)


@dataclass(frozen=True)
class PolicyResolutionTraceEnvelope:
    """Wraps a trace event with evidence references for audit-readiness."""

    trace_event: PolicyResolutionTraceEvent
    evidence_refs: tuple["PolicyResolutionEvidenceRef", ...] = ()
    trace_binding: "PolicyTraceBinding | None" = None
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            object.__setattr__(
                self, "generated_at",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return build_policy_resolution_trace_envelope_dict(self)


@dataclass(frozen=True)
class PolicyResolutionEvidenceRef:
    """Reference to a piece of trace evidence."""
    evidence_type: str
    evidence_hash: str
    label: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_hash or not isinstance(self.evidence_hash, str):
            raise ValueError("evidence_hash must be a non-empty string")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "evidence_hash": self.evidence_hash,
            "label": self.label,
        }


@dataclass(frozen=True)
class PolicyTraceBinding:
    """Binding record linking trace to resolution/projection identifiers."""
    resolution_trace_id: str = ""
    resolution_trace_hash: str = ""
    resolution_id: str = ""
    registry_hash: str = ""
    context_hash: str = ""
    conflict_hash: str = ""
    projection_hash: str = ""
    runtime_snapshot_hash: str = ""
    resolved_policy_hash: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "resolution_trace_id": self.resolution_trace_id,
            "resolution_trace_hash": self.resolution_trace_hash,
            "resolution_id": self.resolution_id,
            "registry_hash": self.registry_hash,
            "context_hash": self.context_hash,
            "conflict_hash": self.conflict_hash,
            "projection_hash": self.projection_hash,
            "runtime_snapshot_hash": self.runtime_snapshot_hash,
            "resolved_policy_hash": self.resolved_policy_hash,
        }
        return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Canonicalization & hashing
# ---------------------------------------------------------------------------


def policy_trace_canonical_dict(
    event: PolicyResolutionTraceEvent,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    """Deterministic canonical dict for trace event. Sorted fields, stable output."""
    if not isinstance(event, PolicyResolutionTraceEvent):
        raise ValueError("event must be a PolicyResolutionTraceEvent")
    result: dict[str, Any] = {
        "conflict_codes": sorted(event.conflict_codes),
        "conflict_hash": event.conflict_hash,
        "context_hash": event.context_hash,
        "effective_shadow_action": event.effective_shadow_action,
        "enforced": event.enforced,
        "policy_phase": event.policy_phase,
        "projection_hash": event.projection_hash,
        "reason_codes": sorted(event.reason_codes),
        "registry_hash": event.registry_hash,
        "resolution_hash": event.resolution_hash,
        "resolver_version": event.resolver_version,
        "runtime_snapshot_hash": event.runtime_snapshot_hash,
        "shadow_only": event.shadow_only,
        "source_card_ids": sorted(event.source_card_ids),
        "source_family_ids": sorted(event.source_family_ids),
        "strictest_decision_rank": event.strictest_decision_rank,
        "trace_event_type": event.trace_event_type,
    }
    if event.trace_id:
        result["trace_id"] = event.trace_id
    if event.metadata:
        result["metadata"] = dict(sorted(
            dict(event.metadata).items(), key=lambda i: i[0],
        ))
    if include_hash and event.trace_hash is not None:
        result["trace_hash"] = event.trace_hash
    return dict(sorted(result.items(), key=lambda i: i[0]))


def policy_trace_hash(event: PolicyResolutionTraceEvent) -> str:
    """Deterministic SHA-256 hash of canonical trace dict."""
    canonical = json.dumps(
        policy_trace_canonical_dict(event, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_policy_resolution_trace_event(
    *,
    registry_hash: str = "",
    context_hash: str = "",
    resolution_hash: str = "",
    conflict_hash: str = "",
    projection_hash: str = "",
    runtime_snapshot_hash: str = "",
    effective_shadow_action: str = "",
    strictest_decision_rank: str = "",
    source_family_ids: Sequence[str] = (),
    source_card_ids: Sequence[str] = (),
    reason_codes: Sequence[str] = (),
    conflict_codes: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> PolicyResolutionTraceEvent:
    """Build a fully-initialized trace event from policy resolution metadata.

    All hash fields are optional; missing values are explicit (empty string).
    Trace ID is derived deterministically from the canonical hash.
    """
    event = PolicyResolutionTraceEvent(
        registry_hash=registry_hash,
        context_hash=context_hash,
        resolution_hash=resolution_hash,
        conflict_hash=conflict_hash,
        projection_hash=projection_hash,
        runtime_snapshot_hash=runtime_snapshot_hash,
        effective_shadow_action=effective_shadow_action,
        strictest_decision_rank=strictest_decision_rank,
        source_family_ids=tuple(sorted(source_family_ids)),
        source_card_ids=tuple(sorted(source_card_ids)),
        reason_codes=tuple(sorted(reason_codes)),
        conflict_codes=tuple(sorted(conflict_codes)),
        metadata=dict(metadata or {}),
    )
    return event.with_trace_hash()


def build_policy_resolution_trace_envelope(
    event: PolicyResolutionTraceEvent,
    *,
    evidence_refs: Sequence[PolicyResolutionEvidenceRef] = (),
    binding: PolicyTraceBinding | None = None,
) -> PolicyResolutionTraceEnvelope:
    """Wrap a trace event with evidence refs and optional binding."""
    return PolicyResolutionTraceEnvelope(
        trace_event=event,
        evidence_refs=tuple(evidence_refs),
        trace_binding=binding,
    )


def build_policy_resolution_trace_envelope_dict(
    envelope: PolicyResolutionTraceEnvelope,
) -> dict[str, Any]:
    """Deterministic canonical dict for trace envelope."""
    result: dict[str, Any] = {
        "generated_at": envelope.generated_at,
        "trace_event": envelope.trace_event.to_canonical_dict(include_hash=True),
        "evidence_refs": [e.to_canonical_dict() for e in envelope.evidence_refs],
    }
    if envelope.trace_binding is not None:
        result["trace_binding"] = envelope.trace_binding.to_canonical_dict()
    return dict(sorted(result.items(), key=lambda i: i[0]))
