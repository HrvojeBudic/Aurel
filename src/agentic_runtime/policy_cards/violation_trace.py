"""Policy Violation Trace Hook (P1.6.15).

Deterministic, JSON-safe, hash-ready shadow violation evidence objects.

P1.6.15 records shadow policy violation evidence; it does NOT enforce policy
decisions, write to the Ledger, activate approvals, block commands, or change
runtime sandbox behavior.

Violation evidence does not mean enforcement.
Nothing is enforced. Nothing is written to Ledger.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .resolution_result import ResolvedPolicySet
    from .runtime_projection import (
        CustosEffectiveAction,
        PolicyShadowProjection,
        RuntimePolicySnapshot,
    )


VIOLATION_VERSION: str = "custos-v0-p1615"
VIOLATION_EVENT_TYPE: str = "policy_violation_trace"
VIOLATION_PHASE: str = "custos_shadow_violation_evidence"

PolicyViolationHash = str

_SENSITIVE_METADATA_KEYS = frozenset({
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "private_key",
    "access_key",
})

_SENSITIVE_METADATA_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|credential|private[_-]?key|authorization)",
    re.IGNORECASE,
)

_COMMAND_BODY_KEYS = frozenset({
    "command",
    "command_body",
    "argv",
    "shell_command",
    "raw_command",
    "payload",
})


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PolicyViolationType(str, Enum):
    SHADOW_POLICY_VIOLATION_CANDIDATE = "SHADOW_POLICY_VIOLATION_CANDIDATE"
    P0_CUSTOS_MISMATCH = "P0_CUSTOS_MISMATCH"
    CUSTOS_STRICTER_THAN_RUNTIME = "CUSTOS_STRICTER_THAN_RUNTIME"
    RUNTIME_STRICTER_THAN_CUSTOS = "RUNTIME_STRICTER_THAN_CUSTOS"
    POLICY_CONTEXT_MISSING = "POLICY_CONTEXT_MISSING"
    POLICY_ADAPTER_ERROR = "POLICY_ADAPTER_ERROR"
    POLICY_CONFLICT_UNRESOLVED = "POLICY_CONFLICT_UNRESOLVED"
    POLICY_RESOLUTION_INCONSISTENT = "POLICY_RESOLUTION_INCONSISTENT"
    POLICY_TRACE_INCOMPLETE = "POLICY_TRACE_INCOMPLETE"
    POLICY_DESIGN_ERROR = "POLICY_DESIGN_ERROR"
    GOVERNANCE_DRIFT_SIGNAL = "GOVERNANCE_DRIFT_SIGNAL"


class PolicyViolationSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyViolationStatus(str, Enum):
    OBSERVED = "OBSERVED"
    SHADOW_ONLY = "SHADOW_ONLY"
    CANDIDATE = "CANDIDATE"
    CONFIRMED_BY_POLICY = "CONFIRMED_BY_POLICY"
    DISMISSED = "DISMISSED"
    NEEDS_OPERATOR_REVIEW = "NEEDS_OPERATOR_REVIEW"


_SEVERITY_RANK: dict[PolicyViolationSeverity, int] = {
    PolicyViolationSeverity.INFO: 0,
    PolicyViolationSeverity.LOW: 1,
    PolicyViolationSeverity.MEDIUM: 2,
    PolicyViolationSeverity.HIGH: 3,
    PolicyViolationSeverity.CRITICAL: 4,
}


def max_severity(
    current: PolicyViolationSeverity,
    candidate: PolicyViolationSeverity,
) -> PolicyViolationSeverity:
    if _SEVERITY_RANK[candidate] > _SEVERITY_RANK[current]:
        return candidate
    return current


_VIOLATION_TYPE_PRIORITY: dict[PolicyViolationType, int] = {
    PolicyViolationType.POLICY_CONTEXT_MISSING: 100,
    PolicyViolationType.POLICY_ADAPTER_ERROR: 90,
    PolicyViolationType.POLICY_TRACE_INCOMPLETE: 80,
    PolicyViolationType.POLICY_CONFLICT_UNRESOLVED: 70,
    PolicyViolationType.POLICY_RESOLUTION_INCONSISTENT: 65,
    PolicyViolationType.GOVERNANCE_DRIFT_SIGNAL: 60,
    PolicyViolationType.POLICY_DESIGN_ERROR: 55,
    PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME: 50,
    PolicyViolationType.P0_CUSTOS_MISMATCH: 45,
    PolicyViolationType.RUNTIME_STRICTER_THAN_CUSTOS: 20,
    PolicyViolationType.SHADOW_POLICY_VIOLATION_CANDIDATE: 10,
}


def _apply_violation_signal(
    *,
    violation_type: PolicyViolationType,
    severity: PolicyViolationSeverity,
    status: PolicyViolationStatus,
    current_type: PolicyViolationType,
    current_severity: PolicyViolationSeverity,
    current_status: PolicyViolationStatus,
) -> tuple[PolicyViolationType, PolicyViolationSeverity, PolicyViolationStatus]:
    if _VIOLATION_TYPE_PRIORITY[violation_type] >= _VIOLATION_TYPE_PRIORITY[current_type]:
        return violation_type, max_severity(current_severity, severity), status
    return current_type, max_severity(current_severity, severity), current_status


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyViolationTraceEvent:
    """Deterministic shadow violation evidence. No enforcement, no Ledger write."""

    trace_event_type: str = VIOLATION_EVENT_TYPE
    policy_phase: str = VIOLATION_PHASE
    resolver_version: str = VIOLATION_VERSION

    violation_trace_id: str = ""
    violation_hash: str | None = None
    violation_type: str = ""
    violation_severity: str = ""
    violation_status: str = ""

    policy_resolution_trace_id: str = ""
    policy_resolution_hash: str = ""
    conflict_hash: str = ""
    projection_hash: str = ""
    runtime_snapshot_hash: str = ""
    context_hash: str = ""
    registry_hash: str = ""

    p0_verdict: str = ""
    custos_shadow_action: str = ""
    strictest_decision_rank: str = ""
    alignment_status: str = ""

    shadow_only: bool = True
    enforced: bool = False

    reason_codes: tuple[str, ...] = ()
    conflict_codes: tuple[str, ...] = ()
    source_family_ids: tuple[str, ...] = ()
    source_card_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.shadow_only is not True:
            raise ValueError("shadow_only must be True")
        if self.enforced is not False:
            raise ValueError("enforced must be False")
        if self.trace_event_type != VIOLATION_EVENT_TYPE:
            raise ValueError(f"trace_event_type must be {VIOLATION_EVENT_TYPE}")
        for field_name in (
            "policy_resolution_trace_id",
            "policy_resolution_hash",
            "conflict_hash",
            "projection_hash",
            "runtime_snapshot_hash",
            "context_hash",
            "registry_hash",
        ):
            val = getattr(self, field_name)
            if val and not isinstance(val, str):
                raise ValueError(f"{field_name} must be a string")

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return policy_violation_canonical_dict(self, include_hash=include_hash)

    def with_violation_hash(self) -> PolicyViolationTraceEvent:
        h = policy_violation_hash(self)
        return replace(self, violation_hash=h, violation_trace_id=h)


@dataclass(frozen=True)
class PolicyViolationTraceEnvelope:
    """Wraps a violation event with evidence references for audit-readiness."""

    trace_event: PolicyViolationTraceEvent
    evidence_refs: tuple[PolicyViolationEvidenceRef, ...] = ()
    violation_binding: PolicyViolationBinding | None = None
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            object.__setattr__(
                self,
                "generated_at",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return build_policy_violation_trace_envelope_dict(self)


@dataclass(frozen=True)
class PolicyViolationEvidenceRef:
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
class PolicyViolationBinding:
    policy_resolution_trace_id: str = ""
    policy_resolution_hash: str = ""
    conflict_hash: str = ""
    projection_hash: str = ""
    runtime_snapshot_hash: str = ""
    context_hash: str = ""
    registry_hash: str = ""
    resolved_policy_hash: str = ""
    violation_trace_id: str = ""
    violation_hash: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "conflict_hash": self.conflict_hash,
            "context_hash": self.context_hash,
            "policy_resolution_hash": self.policy_resolution_hash,
            "policy_resolution_trace_id": self.policy_resolution_trace_id,
            "projection_hash": self.projection_hash,
            "registry_hash": self.registry_hash,
            "resolved_policy_hash": self.resolved_policy_hash,
            "runtime_snapshot_hash": self.runtime_snapshot_hash,
            "violation_hash": self.violation_hash,
            "violation_trace_id": self.violation_trace_id,
        }
        return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Metadata safety
# ---------------------------------------------------------------------------


def _assert_json_safe(
    value: object,
    path: str,
) -> None:
    if value is None or isinstance(value, str | int | float | bool):
        return
    if isinstance(value, list | tuple):
        for idx, item in enumerate(value):
            _assert_json_safe(item, f"{path}[{idx}]")
        return
    if isinstance(value, MappingABC):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"metadata key at {path} must be a string")
            _assert_json_safe(item, f"{path}.{key}")
        return
    raise ValueError(f"value at {path} is not JSON-safe")


def _sanitize_violation_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            continue
        key_lower = key.lower()
        if key_lower in _COMMAND_BODY_KEYS:
            continue
        if key_lower in _SENSITIVE_METADATA_KEYS or _SENSITIVE_METADATA_PATTERN.search(key):
            continue
        if isinstance(value, str) and len(value) > 256:
            continue
        try:
            _assert_json_safe(value, f"metadata.{key}")
        except ValueError:
            continue
        if isinstance(value, str) and _looks_like_secret(value):
            continue
        sanitized[key] = value
    return dict(sorted(sanitized.items(), key=lambda i: i[0]))


def _looks_like_secret(value: str) -> bool:
    if value.startswith("sk-") or value.startswith("Bearer "):
        return True
    if len(value) >= 32 and all(c in "0123456789abcdef" for c in value.lower()):
        return False
    return False


# ---------------------------------------------------------------------------
# Canonicalization & hashing
# ---------------------------------------------------------------------------


def policy_violation_canonical_dict(
    event: PolicyViolationTraceEvent,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    if not isinstance(event, PolicyViolationTraceEvent):
        raise ValueError("event must be a PolicyViolationTraceEvent")
    result: dict[str, Any] = {
        "alignment_status": event.alignment_status,
        "conflict_codes": sorted(event.conflict_codes),
        "conflict_hash": event.conflict_hash,
        "context_hash": event.context_hash,
        "custos_shadow_action": event.custos_shadow_action,
        "enforced": event.enforced,
        "p0_verdict": event.p0_verdict,
        "policy_phase": event.policy_phase,
        "policy_resolution_hash": event.policy_resolution_hash,
        "policy_resolution_trace_id": event.policy_resolution_trace_id,
        "projection_hash": event.projection_hash,
        "reason_codes": sorted(event.reason_codes),
        "registry_hash": event.registry_hash,
        "resolver_version": event.resolver_version,
        "runtime_snapshot_hash": event.runtime_snapshot_hash,
        "shadow_only": event.shadow_only,
        "source_card_ids": sorted(event.source_card_ids),
        "source_family_ids": sorted(event.source_family_ids),
        "strictest_decision_rank": event.strictest_decision_rank,
        "trace_event_type": event.trace_event_type,
        "violation_severity": event.violation_severity,
        "violation_status": event.violation_status,
        "violation_trace_id": event.violation_trace_id,
        "violation_type": event.violation_type,
    }
    if event.metadata:
        result["metadata"] = dict(sorted(dict(event.metadata).items(), key=lambda i: i[0]))
    if include_hash and event.violation_hash is not None:
        result["violation_hash"] = event.violation_hash
    return dict(sorted(result.items(), key=lambda i: i[0]))


def policy_violation_hash(event: PolicyViolationTraceEvent) -> PolicyViolationHash:
    canonical = json.dumps(
        policy_violation_canonical_dict(event, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def stable_policy_violation_trace_id(event: PolicyViolationTraceEvent) -> str:
    return policy_violation_hash(event)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


class _NormalizedRank(int, Enum):
    UNKNOWN = -1
    NOT_APPLICABLE = 0
    ALLOW = 1
    WARN = 2
    REQUIRE_APPROVAL = 3
    DENY = 4
    ERROR = 5


_P0_NORMALIZE: dict[str, _NormalizedRank] = {
    "allow": _NormalizedRank.ALLOW,
    "p0_allow": _NormalizedRank.ALLOW,
    "runtime_allow": _NormalizedRank.ALLOW,
    "warn": _NormalizedRank.WARN,
    "p0_warn": _NormalizedRank.WARN,
    "runtime_warn": _NormalizedRank.WARN,
    "require_approval": _NormalizedRank.REQUIRE_APPROVAL,
    "p0_require_approval": _NormalizedRank.REQUIRE_APPROVAL,
    "runtime_require_approval": _NormalizedRank.REQUIRE_APPROVAL,
    "deny": _NormalizedRank.DENY,
    "p0_deny": _NormalizedRank.DENY,
    "runtime_deny": _NormalizedRank.DENY,
    "unknown": _NormalizedRank.UNKNOWN,
    "runtime_unknown": _NormalizedRank.UNKNOWN,
    "not_applicable": _NormalizedRank.NOT_APPLICABLE,
    "error": _NormalizedRank.ERROR,
}

_CUSTOS_NORMALIZE: dict[str, _NormalizedRank] = {
    "would_allow": _NormalizedRank.ALLOW,
    "would_warn": _NormalizedRank.WARN,
    "would_require_approval": _NormalizedRank.REQUIRE_APPROVAL,
    "would_deny": _NormalizedRank.DENY,
    "would_not_apply": _NormalizedRank.NOT_APPLICABLE,
    "would_not_applicable": _NormalizedRank.NOT_APPLICABLE,
    "would_error": _NormalizedRank.ERROR,
    "custos_allow": _NormalizedRank.ALLOW,
    "custos_deny": _NormalizedRank.DENY,
    "custos_require_approval": _NormalizedRank.REQUIRE_APPROVAL,
}


def _normalize_key(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower().replace("-", "_")


def _normalize_p0_verdict(p0_verdict: str | None) -> _NormalizedRank:
    key = _normalize_key(p0_verdict)
    if not key:
        return _NormalizedRank.UNKNOWN
    return _P0_NORMALIZE.get(key, _NormalizedRank.UNKNOWN)


def _normalize_custos_action(custos_shadow_action: str | None) -> _NormalizedRank:
    key = _normalize_key(custos_shadow_action)
    if not key:
        return _NormalizedRank.UNKNOWN
    if key in _CUSTOS_NORMALIZE:
        return _CUSTOS_NORMALIZE[key]
    if key.startswith("would_"):
        return _CUSTOS_NORMALIZE.get(key, _NormalizedRank.UNKNOWN)
    return _NormalizedRank.UNKNOWN


def _is_allowish(rank: _NormalizedRank) -> bool:
    return rank in {_NormalizedRank.ALLOW, _NormalizedRank.WARN}


def _is_denyish(rank: _NormalizedRank) -> bool:
    return rank in {_NormalizedRank.DENY, _NormalizedRank.REQUIRE_APPROVAL}


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify_policy_violation(
    *,
    p0_verdict: str | None,
    custos_shadow_action: str | None,
    strictest_decision_rank: str | None = None,
    alignment_status: str | None = None,
    context_hash: str | None = None,
    registry_hash: str | None = None,
    policy_resolution_hash: str | None = None,
    policy_resolution_trace_id: str | None = None,
    conflict_hash: str | None = None,
    projection_hash: str | None = None,
    runtime_snapshot_hash: str | None = None,
    reason_codes: Sequence[str] = (),
    conflict_codes: Sequence[str] = (),
    source_family_ids: Sequence[str] = (),
    source_card_ids: Sequence[str] = (),
    metadata: Mapping[str, object] | None = None,
    resolved_policy_hash: str | None = None,
) -> PolicyViolationTraceEnvelope:
    """Classify shadow violation evidence from explicit governance signals."""
    reasons = list(reason_codes)
    conflicts = list(conflict_codes)
    violation_type = PolicyViolationType.SHADOW_POLICY_VIOLATION_CANDIDATE
    severity = PolicyViolationSeverity.INFO
    status = PolicyViolationStatus.SHADOW_ONLY

    ctx = context_hash or ""
    reg = registry_hash or ""
    res_trace_id = policy_resolution_trace_id or ""
    res_hash = policy_resolution_hash or ""
    conf_hash = conflict_hash or ""
    proj_hash = projection_hash or ""
    snap_hash = runtime_snapshot_hash or ""

    p0_rank = _normalize_p0_verdict(p0_verdict)
    custos_rank = _normalize_custos_action(custos_shadow_action)
    align = _normalize_key(alignment_status)

    if not ctx:
        reasons.append("missing_context_hash")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.POLICY_CONTEXT_MISSING,
            severity=PolicyViolationSeverity.MEDIUM,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )

    upper_reasons = {r.upper() for r in reasons}
    if "ADAPTER_ERROR" in upper_reasons:
        reasons.append("policy_adapter_error")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.POLICY_ADAPTER_ERROR,
            severity=PolicyViolationSeverity.HIGH,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )

    if not res_trace_id or not res_hash:
        reasons.append("missing_resolution_trace")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.POLICY_TRACE_INCOMPLETE,
            severity=PolicyViolationSeverity.MEDIUM,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )

    conflict_upper = {c.lower() for c in conflicts}
    if any(
        marker in conflict_upper
        for marker in ("policy_conflict_unresolved", "unresolved_conflict")
    ):
        reasons.append("policy_conflict_unresolved")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.POLICY_CONFLICT_UNRESOLVED,
            severity=PolicyViolationSeverity.HIGH,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )
    elif not conf_hash and conflicts:
        reasons.append("missing_conflict_metadata")

    p0_unknown = bool(p0_verdict) and p0_rank == _NormalizedRank.UNKNOWN
    custos_unknown = bool(custos_shadow_action) and custos_rank == _NormalizedRank.UNKNOWN
    if p0_unknown or custos_unknown:
        reasons.append("unknown_decision_vocabulary")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.GOVERNANCE_DRIFT_SIGNAL,
            severity=PolicyViolationSeverity.MEDIUM,
            status=PolicyViolationStatus.NEEDS_OPERATOR_REVIEW,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )
    elif _is_allowish(p0_rank) and custos_rank == _NormalizedRank.DENY:
        reasons.append("custos_stricter_than_runtime")
        reasons.append("shadow_policy_violation_candidate")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME,
            severity=PolicyViolationSeverity.CRITICAL,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )
    elif _is_allowish(p0_rank) and custos_rank == _NormalizedRank.REQUIRE_APPROVAL:
        reasons.append("custos_stricter_than_runtime")
        reasons.append("shadow_policy_violation_candidate")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.CUSTOS_STRICTER_THAN_RUNTIME,
            severity=PolicyViolationSeverity.HIGH,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )
    elif _is_denyish(p0_rank) and custos_rank == _NormalizedRank.ALLOW:
        reasons.append("runtime_stricter_than_custos")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.RUNTIME_STRICTER_THAN_CUSTOS,
            severity=PolicyViolationSeverity.LOW,
            status=PolicyViolationStatus.OBSERVED,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )
    elif p0_rank == _NormalizedRank.ALLOW and custos_rank == _NormalizedRank.ALLOW:
        reasons.append("alignment_observed")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.SHADOW_POLICY_VIOLATION_CANDIDATE,
            severity=PolicyViolationSeverity.INFO,
            status=PolicyViolationStatus.OBSERVED,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )

    if align == "custos_stricter":
        reasons.append("alignment_custos_stricter")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.P0_CUSTOS_MISMATCH,
            severity=PolicyViolationSeverity.HIGH,
            status=PolicyViolationStatus.CANDIDATE,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )
    elif align == "runtime_stricter":
        reasons.append("alignment_runtime_stricter")
        violation_type, severity, status = _apply_violation_signal(
            violation_type=PolicyViolationType.RUNTIME_STRICTER_THAN_CUSTOS,
            severity=PolicyViolationSeverity.LOW,
            status=PolicyViolationStatus.OBSERVED,
            current_type=violation_type,
            current_severity=severity,
            current_status=status,
        )

    if not proj_hash:
        reasons.append("missing_projection_hash")

    if not snap_hash:
        reasons.append("missing_runtime_snapshot_hash")

    event = build_policy_violation_trace_event(
        violation_type=violation_type.value,
        violation_severity=severity.value,
        violation_status=status.value,
        policy_resolution_trace_id=res_trace_id,
        policy_resolution_hash=res_hash,
        conflict_hash=conf_hash,
        projection_hash=proj_hash,
        runtime_snapshot_hash=snap_hash,
        context_hash=ctx,
        registry_hash=reg,
        p0_verdict=p0_verdict or "",
        custos_shadow_action=custos_shadow_action or "",
        strictest_decision_rank=strictest_decision_rank or "",
        alignment_status=alignment_status or "",
        reason_codes=reasons,
        conflict_codes=conflicts,
        source_family_ids=source_family_ids,
        source_card_ids=source_card_ids,
        metadata=metadata,
    )

    binding = PolicyViolationBinding(
        policy_resolution_trace_id=res_trace_id,
        policy_resolution_hash=res_hash,
        conflict_hash=conf_hash,
        projection_hash=proj_hash,
        runtime_snapshot_hash=snap_hash,
        context_hash=ctx,
        registry_hash=reg,
        resolved_policy_hash=resolved_policy_hash or "",
        violation_trace_id=event.violation_trace_id,
        violation_hash=event.violation_hash or "",
    )

    evidence_refs: list[PolicyViolationEvidenceRef] = []
    if res_hash:
        evidence_refs.append(
            PolicyViolationEvidenceRef(
                evidence_type="policy_resolution_trace",
                evidence_hash=res_hash,
                label="resolution_trace",
            )
        )
    if conf_hash:
        evidence_refs.append(
            PolicyViolationEvidenceRef(
                evidence_type="conflict_algebra",
                evidence_hash=conf_hash,
                label="conflict",
            )
        )
    if proj_hash:
        evidence_refs.append(
            PolicyViolationEvidenceRef(
                evidence_type="runtime_projection",
                evidence_hash=proj_hash,
                label="projection",
            )
        )

    return build_policy_violation_trace_envelope(
        event,
        evidence_refs=evidence_refs,
        binding=binding,
    )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_policy_violation_trace_event(
    *,
    violation_type: str = "",
    violation_severity: str = "",
    violation_status: str = "",
    policy_resolution_trace_id: str = "",
    policy_resolution_hash: str = "",
    conflict_hash: str = "",
    projection_hash: str = "",
    runtime_snapshot_hash: str = "",
    context_hash: str = "",
    registry_hash: str = "",
    p0_verdict: str = "",
    custos_shadow_action: str = "",
    strictest_decision_rank: str = "",
    alignment_status: str = "",
    reason_codes: Sequence[str] = (),
    conflict_codes: Sequence[str] = (),
    source_family_ids: Sequence[str] = (),
    source_card_ids: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> PolicyViolationTraceEvent:
    event = PolicyViolationTraceEvent(
        violation_type=violation_type,
        violation_severity=violation_severity,
        violation_status=violation_status,
        policy_resolution_trace_id=policy_resolution_trace_id,
        policy_resolution_hash=policy_resolution_hash,
        conflict_hash=conflict_hash,
        projection_hash=projection_hash,
        runtime_snapshot_hash=runtime_snapshot_hash,
        context_hash=context_hash,
        registry_hash=registry_hash,
        p0_verdict=p0_verdict,
        custos_shadow_action=custos_shadow_action,
        strictest_decision_rank=strictest_decision_rank,
        alignment_status=alignment_status,
        reason_codes=tuple(sorted(set(reason_codes))),
        conflict_codes=tuple(sorted(set(conflict_codes))),
        source_family_ids=tuple(sorted(source_family_ids)),
        source_card_ids=tuple(sorted(source_card_ids)),
        metadata=_sanitize_violation_metadata(metadata),
    )
    return event.with_violation_hash()


def build_policy_violation_trace_envelope(
    event: PolicyViolationTraceEvent,
    *,
    evidence_refs: Sequence[PolicyViolationEvidenceRef] = (),
    binding: PolicyViolationBinding | None = None,
) -> PolicyViolationTraceEnvelope:
    return PolicyViolationTraceEnvelope(
        trace_event=event,
        evidence_refs=tuple(evidence_refs),
        violation_binding=binding,
    )


def build_policy_violation_trace_envelope_dict(
    envelope: PolicyViolationTraceEnvelope,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "evidence_refs": [e.to_canonical_dict() for e in envelope.evidence_refs],
        "generated_at": envelope.generated_at,
        "trace_event": envelope.trace_event.to_canonical_dict(include_hash=True),
    }
    if envelope.violation_binding is not None:
        result["violation_binding"] = envelope.violation_binding.to_canonical_dict()
    return dict(sorted(result.items(), key=lambda i: i[0]))


# ---------------------------------------------------------------------------
# Binding helpers
# ---------------------------------------------------------------------------


def bind_policy_violation_from_resolution(
    resolution: ResolvedPolicySet,
    *,
    projection: PolicyShadowProjection | None = None,
    runtime_snapshot: RuntimePolicySnapshot | None = None,
) -> PolicyViolationTraceEnvelope:
    from .resolution_result import ResolvedPolicySet as RPS
    from .runtime_projection import (
        CustosEffectiveAction,
        PolicyShadowProjection as PSP,
        RuntimeEffectiveAction,
        RuntimePolicySnapshot as RPSnap,
    )

    if not isinstance(resolution, RPS):
        raise ValueError("resolution must be a ResolvedPolicySet")

    conflict_codes: list[str] = []
    strictest_rank = ""
    if resolution.conflict_resolution is not None:
        raw_codes = resolution.conflict_resolution.get("conflict_codes", ()) or ()
        conflict_codes = [str(c) for c in raw_codes]
        strictest_rank = str(resolution.conflict_resolution.get("winning_rank", ""))

    source_families = tuple(sorted({fd.family.value for fd in resolution.family_decisions}))

    p0_verdict = ""
    runtime_snapshot_hash = ""
    if runtime_snapshot is not None and isinstance(runtime_snapshot, RPSnap):
        p0_verdict = runtime_snapshot.policy_verdict or runtime_snapshot.runtime_effective_action.value
        runtime_snapshot_hash = runtime_snapshot.runtime_snapshot_hash or ""
    elif projection is not None and isinstance(projection, PSP):
        p0_verdict = projection.runtime_effective_action.value

    projection_hash = ""
    alignment_status = ""
    registry_hash = ""
    if projection is not None and isinstance(projection, PSP):
        projection_hash = projection.projection_hash or ""
        alignment_status = projection.alignment_status.value
        registry_hash = projection.registry_hash
        if not runtime_snapshot_hash:
            runtime_snapshot_hash = projection.runtime_snapshot_hash
        if not p0_verdict:
            p0_verdict = projection.runtime_effective_action.value

    custos_action = resolution.effective_shadow_action.value
    if projection is not None and isinstance(projection, PSP):
        custos_action = _custos_action_from_projection(projection.custos_effective_action)

    return classify_policy_violation(
        p0_verdict=p0_verdict,
        custos_shadow_action=custos_action,
        strictest_decision_rank=strictest_rank,
        alignment_status=alignment_status,
        context_hash=resolution.context_hash,
        registry_hash=registry_hash or (resolution.source_hashes[0] if resolution.source_hashes else ""),
        policy_resolution_hash=resolution.resolution_trace_hash or "",
        policy_resolution_trace_id=resolution.resolution_trace_id or "",
        conflict_hash=resolution.conflict_hash or "",
        projection_hash=projection_hash,
        runtime_snapshot_hash=runtime_snapshot_hash,
        reason_codes=resolution.reason_codes,
        conflict_codes=conflict_codes,
        source_family_ids=source_families,
        source_card_ids=resolution.applicable_card_ids,
        resolved_policy_hash=resolution.canonical_hash or "",
    )


def bind_policy_violation_from_projection(
    projection: PolicyShadowProjection,
    *,
    resolution: ResolvedPolicySet | None = None,
) -> PolicyViolationTraceEnvelope:
    from .resolution_result import ResolvedPolicySet as RPS
    from .runtime_projection import PolicyShadowProjection as PSP

    if not isinstance(projection, PSP):
        raise ValueError("projection must be a PolicyShadowProjection")

    if resolution is not None:
        return bind_policy_violation_from_resolution(
            resolution,
            projection=projection,
        )

    return classify_policy_violation(
        p0_verdict=projection.runtime_effective_action.value,
        custos_shadow_action=_custos_action_from_projection(projection.custos_effective_action),
        alignment_status=projection.alignment_status.value,
        context_hash=projection.context_hash,
        registry_hash=projection.registry_hash,
        policy_resolution_hash=projection.resolution_trace_hash,
        policy_resolution_trace_id=projection.resolution_trace_id,
        projection_hash=projection.projection_hash or "",
        runtime_snapshot_hash=projection.runtime_snapshot_hash,
        reason_codes=projection.reason_codes,
        resolved_policy_hash=projection.resolved_policy_hash,
    )


def _custos_action_from_projection(action: CustosEffectiveAction) -> str:
    from .runtime_projection import CustosEffectiveAction as CEA

    mapping: dict[CEA, str] = {
        CEA.WOULD_ALLOW: "would_allow",
        CEA.WOULD_WARN: "would_warn",
        CEA.WOULD_REQUIRE_APPROVAL: "would_require_approval",
        CEA.WOULD_DENY: "would_deny",
        CEA.WOULD_NOT_APPLICABLE: "would_not_apply",
        CEA.WOULD_ERROR: "would_error",
    }
    return mapping.get(action, action.value.lower())

