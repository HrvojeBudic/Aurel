"""Custos shadow projection against the P0 runtime posture (P1.6.12).

This module compares an already-authoritative runtime outcome with a Custos
shadow resolution. It is observability-only: the projection never enforces,
approves, submits, executes, or blocks anything.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping

from .errors import (
    PolicyRuntimeProjectionError,
    PolicyRuntimeSnapshotValidationError,
    PolicyShadowProjectionError,
)
from .resolution_result import (
    PolicyFamily,
    ResolvedPolicySet,
    ShadowAction,
    compute_resolved_policy_set_hash,
)


class RuntimeEffectiveAction(str, Enum):
    RUNTIME_ALLOW = "RUNTIME_ALLOW"
    RUNTIME_WARN = "RUNTIME_WARN"
    RUNTIME_REQUIRE_APPROVAL = "RUNTIME_REQUIRE_APPROVAL"
    RUNTIME_DENY = "RUNTIME_DENY"
    RUNTIME_UNKNOWN = "RUNTIME_UNKNOWN"


class CustosEffectiveAction(str, Enum):
    WOULD_ALLOW = "WOULD_ALLOW"
    WOULD_WARN = "WOULD_WARN"
    WOULD_REQUIRE_APPROVAL = "WOULD_REQUIRE_APPROVAL"
    WOULD_DENY = "WOULD_DENY"
    WOULD_NOT_APPLICABLE = "WOULD_NOT_APPLICABLE"
    WOULD_ERROR = "WOULD_ERROR"


class PolicyRuntimeAlignment(str, Enum):
    ALIGNED = "ALIGNED"
    CUSTOS_STRICTER = "CUSTOS_STRICTER"
    RUNTIME_STRICTER = "RUNTIME_STRICTER"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    SHADOW_ERROR = "SHADOW_ERROR"


class PolicyRuntimeMismatch(str, Enum):
    RUNTIME_ALLOWED_CUSTOS_WOULD_DENY = "RUNTIME_ALLOWED_CUSTOS_WOULD_DENY"
    RUNTIME_ALLOWED_CUSTOS_WOULD_REQUIRE_APPROVAL = (
        "RUNTIME_ALLOWED_CUSTOS_WOULD_REQUIRE_APPROVAL"
    )
    RUNTIME_ALLOWED_CUSTOS_WOULD_WARN = "RUNTIME_ALLOWED_CUSTOS_WOULD_WARN"
    RUNTIME_DENIED_CUSTOS_WOULD_ALLOW = "RUNTIME_DENIED_CUSTOS_WOULD_ALLOW"
    RUNTIME_REQUIRES_APPROVAL_CUSTOS_WOULD_ALLOW = (
        "RUNTIME_REQUIRES_APPROVAL_CUSTOS_WOULD_ALLOW"
    )
    RUNTIME_WARNED_CUSTOS_WOULD_ALLOW = "RUNTIME_WARNED_CUSTOS_WOULD_ALLOW"
    RUNTIME_CONTEXT_INSUFFICIENT = "RUNTIME_CONTEXT_INSUFFICIENT"
    CUSTOS_CONTEXT_INSUFFICIENT = "CUSTOS_CONTEXT_INSUFFICIENT"
    CUSTOS_SHADOW_RESOLUTION_ERROR = "CUSTOS_SHADOW_RESOLUTION_ERROR"
    SANDBOX_POLICY_CARD_STRICTER_THAN_RUNTIME = (
        "SANDBOX_POLICY_CARD_STRICTER_THAN_RUNTIME"
    )
    RUNTIME_POLICY_STRICTER_THAN_CUSTOS = "RUNTIME_POLICY_STRICTER_THAN_CUSTOS"


@dataclass(frozen=True)
class RuntimePolicySnapshot:
    """Deterministic summary of the P0 runtime posture for one submitted command."""

    runtime_effective_action: RuntimeEffectiveAction
    policy_verdict: str = ""
    policy_risk: str = ""
    approval_required: bool = False
    approval_outcome: str = ""
    sandbox_allowed: bool | None = None
    blocker_codes: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    runtime_snapshot_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_effective_action, RuntimeEffectiveAction):
            raise PolicyRuntimeSnapshotValidationError(
                "runtime_effective_action must be a RuntimeEffectiveAction"
            )
        if not isinstance(self.approval_required, bool):
            raise PolicyRuntimeSnapshotValidationError("approval_required must be boolean")
        if self.sandbox_allowed is not None and not isinstance(self.sandbox_allowed, bool):
            raise PolicyRuntimeSnapshotValidationError(
                "sandbox_allowed must be boolean or None"
            )
        _validate_string_tuple(
            self.blocker_codes,
            "blocker_codes",
            PolicyRuntimeSnapshotValidationError,
        )
        _validate_string_tuple(
            self.reason_codes,
            "reason_codes",
            PolicyRuntimeSnapshotValidationError,
        )
        _validate_string_tuple(
            self.warnings,
            "warnings",
            PolicyRuntimeSnapshotValidationError,
        )
        _validate_string_tuple(
            self.violations,
            "violations",
            PolicyRuntimeSnapshotValidationError,
        )
        _validate_metadata(self.metadata, "metadata", PolicyRuntimeSnapshotValidationError)
        _validate_optional_hash(
            self.runtime_snapshot_hash,
            "runtime_snapshot_hash",
            PolicyRuntimeSnapshotValidationError,
        )

    def to_canonical_dict(self, *, include_hash: bool = False) -> dict[str, Any]:
        return runtime_policy_snapshot_to_canonical_dict(self, include_hash=include_hash)

    def with_runtime_snapshot_hash(self) -> "RuntimePolicySnapshot":
        return replace(self, runtime_snapshot_hash=compute_runtime_policy_snapshot_hash(self))


@dataclass(frozen=True)
class PolicyShadowProjection:
    """Shadow-only comparison payload attached to runtime observations."""

    runtime_effective_action: RuntimeEffectiveAction
    custos_effective_action: CustosEffectiveAction
    alignment_status: PolicyRuntimeAlignment
    mismatch_codes: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    context_hash: str = ""
    registry_hash: str = ""
    resolved_policy_hash: str = ""
    runtime_snapshot_hash: str = ""
    projection_hash: str | None = None
    enabled: bool = True
    mode: str = "shadow_only"
    enforced: bool = False

    def __post_init__(self) -> None:
        if self.enabled is not True:
            raise PolicyShadowProjectionError("enabled must be True")
        if self.mode != "shadow_only":
            raise PolicyShadowProjectionError("mode must be shadow_only")
        if self.enforced is not False:
            raise PolicyShadowProjectionError("enforced must be False")
        if not isinstance(self.runtime_effective_action, RuntimeEffectiveAction):
            raise PolicyShadowProjectionError(
                "runtime_effective_action must be a RuntimeEffectiveAction"
            )
        if not isinstance(self.custos_effective_action, CustosEffectiveAction):
            raise PolicyShadowProjectionError(
                "custos_effective_action must be a CustosEffectiveAction"
            )
        if not isinstance(self.alignment_status, PolicyRuntimeAlignment):
            raise PolicyShadowProjectionError(
                "alignment_status must be a PolicyRuntimeAlignment"
            )
        _validate_string_tuple(
            self.mismatch_codes,
            "mismatch_codes",
            PolicyShadowProjectionError,
        )
        _validate_string_tuple(
            self.reason_codes,
            "reason_codes",
            PolicyShadowProjectionError,
        )
        _validate_string_tuple(
            self.warnings,
            "warnings",
            PolicyShadowProjectionError,
        )
        _validate_string_tuple(
            self.violations,
            "violations",
            PolicyShadowProjectionError,
        )
        for field_name in (
            "context_hash",
            "registry_hash",
            "resolved_policy_hash",
            "runtime_snapshot_hash",
        ):
            value = getattr(self, field_name)
            if value and (not isinstance(value, str) or not value.strip()):
                raise PolicyShadowProjectionError(f"{field_name} must be a string")
        _validate_optional_hash(
            self.projection_hash,
            "projection_hash",
            PolicyShadowProjectionError,
        )

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        return policy_shadow_projection_to_canonical_dict(self, include_hash=include_hash)

    def with_projection_hash(self) -> "PolicyShadowProjection":
        return replace(self, projection_hash=compute_policy_shadow_projection_hash(self))


def runtime_policy_snapshot_to_canonical_dict(
    snapshot: RuntimePolicySnapshot,
    *,
    include_hash: bool = False,
) -> dict[str, Any]:
    if not isinstance(snapshot, RuntimePolicySnapshot):
        raise PolicyRuntimeSnapshotValidationError(
            "snapshot must be a RuntimePolicySnapshot"
        )
    result: dict[str, Any] = {
        "approval_required": snapshot.approval_required,
        "blocker_codes": sorted(snapshot.blocker_codes),
        "metadata": dict(sorted(dict(snapshot.metadata).items(), key=lambda item: item[0])),
        "reason_codes": sorted(snapshot.reason_codes),
        "runtime_effective_action": snapshot.runtime_effective_action.value,
        "violations": sorted(snapshot.violations),
        "warnings": sorted(snapshot.warnings),
    }
    if snapshot.policy_verdict:
        result["policy_verdict"] = snapshot.policy_verdict
    if snapshot.policy_risk:
        result["policy_risk"] = snapshot.policy_risk
    if snapshot.approval_outcome:
        result["approval_outcome"] = snapshot.approval_outcome
    if snapshot.sandbox_allowed is not None:
        result["sandbox_allowed"] = snapshot.sandbox_allowed
    if include_hash and snapshot.runtime_snapshot_hash is not None:
        result["runtime_snapshot_hash"] = snapshot.runtime_snapshot_hash
    _assert_json_safe(result, "runtime_snapshot")
    return dict(sorted(result.items(), key=lambda item: item[0]))


def serialize_runtime_policy_snapshot_canonical(snapshot: RuntimePolicySnapshot) -> str:
    return json.dumps(
        runtime_policy_snapshot_to_canonical_dict(snapshot, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_runtime_policy_snapshot_hash(snapshot: RuntimePolicySnapshot) -> str:
    canonical = serialize_runtime_policy_snapshot_canonical(snapshot)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def policy_shadow_projection_to_canonical_dict(
    projection: PolicyShadowProjection,
    *,
    include_hash: bool = True,
) -> dict[str, Any]:
    if not isinstance(projection, PolicyShadowProjection):
        raise PolicyShadowProjectionError("projection must be a PolicyShadowProjection")
    result: dict[str, Any] = {
        "alignment_status": projection.alignment_status.value,
        "context_hash": projection.context_hash,
        "custos_effective_action": projection.custos_effective_action.value,
        "enabled": projection.enabled,
        "enforced": projection.enforced,
        "mismatch_codes": sorted(projection.mismatch_codes),
        "mode": projection.mode,
        "reason_codes": sorted(projection.reason_codes),
        "registry_hash": projection.registry_hash,
        "resolved_policy_hash": projection.resolved_policy_hash,
        "runtime_effective_action": projection.runtime_effective_action.value,
        "runtime_snapshot_hash": projection.runtime_snapshot_hash,
        "violations": sorted(projection.violations),
        "warnings": sorted(projection.warnings),
    }
    if include_hash and projection.projection_hash is not None:
        result["projection_hash"] = projection.projection_hash
    _assert_json_safe(result, "policy_shadow_projection")
    return dict(sorted(result.items(), key=lambda item: item[0]))


def serialize_policy_shadow_projection_canonical(
    projection: PolicyShadowProjection,
) -> str:
    return json.dumps(
        policy_shadow_projection_to_canonical_dict(projection, include_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_policy_shadow_projection_hash(projection: PolicyShadowProjection) -> str:
    canonical = serialize_policy_shadow_projection_canonical(projection)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def project_policy_resolution_against_runtime(
    runtime_snapshot: RuntimePolicySnapshot,
    resolved_policy: ResolvedPolicySet,
    *,
    registry_hash: str = "",
) -> PolicyShadowProjection:
    """Compare the authoritative runtime posture with a Custos shadow result."""
    if not isinstance(runtime_snapshot, RuntimePolicySnapshot):
        raise PolicyRuntimeProjectionError(
            "runtime_snapshot must be a RuntimePolicySnapshot"
        )
    if not isinstance(resolved_policy, ResolvedPolicySet):
        raise PolicyRuntimeProjectionError(
            "resolved_policy must be a ResolvedPolicySet"
        )
    if not isinstance(registry_hash, str):
        raise PolicyRuntimeProjectionError("registry_hash must be a string")

    snapshot = runtime_snapshot.with_runtime_snapshot_hash()
    runtime_action = snapshot.runtime_effective_action
    custos_action = _custos_effective_action(resolved_policy.effective_shadow_action)
    alignment, mismatches = _alignment(runtime_action, custos_action)

    if _sandbox_family_stricter_than_allow(resolved_policy) and runtime_action is (
        RuntimeEffectiveAction.RUNTIME_ALLOW
    ):
        mismatches.append(
            PolicyRuntimeMismatch.SANDBOX_POLICY_CARD_STRICTER_THAN_RUNTIME.value
        )
    if (
        runtime_action
        in {
            RuntimeEffectiveAction.RUNTIME_DENY,
            RuntimeEffectiveAction.RUNTIME_REQUIRE_APPROVAL,
            RuntimeEffectiveAction.RUNTIME_WARN,
        }
        and custos_action is CustosEffectiveAction.WOULD_ALLOW
    ):
        mismatches.append(PolicyRuntimeMismatch.RUNTIME_POLICY_STRICTER_THAN_CUSTOS.value)

    resolved_hash = resolved_policy.canonical_hash or compute_resolved_policy_set_hash(
        resolved_policy
    )
    projection = PolicyShadowProjection(
        runtime_effective_action=runtime_action,
        custos_effective_action=custos_action,
        alignment_status=alignment,
        mismatch_codes=tuple(sorted(set(mismatches))),
        reason_codes=tuple(sorted(set(resolved_policy.reason_codes + snapshot.reason_codes))),
        warnings=tuple(sorted(set(resolved_policy.warnings + snapshot.warnings))),
        violations=tuple(sorted(set(resolved_policy.violations + snapshot.violations))),
        context_hash=resolved_policy.context_hash,
        registry_hash=registry_hash,
        resolved_policy_hash=resolved_hash,
        runtime_snapshot_hash=snapshot.runtime_snapshot_hash or "",
    )
    return projection.with_projection_hash()


def shadow_projection_error_payload(
    *,
    context_hash: str = "",
    registry_hash: str = "",
    runtime_snapshot_hash: str = "",
    reason: str = "",
) -> dict[str, Any]:
    """Build the non-fatal observation payload for projection failures."""
    reason_codes = [PolicyRuntimeMismatch.CUSTOS_SHADOW_RESOLUTION_ERROR.value]
    if reason:
        reason_codes.append(reason)
    projection = PolicyShadowProjection(
        runtime_effective_action=RuntimeEffectiveAction.RUNTIME_UNKNOWN,
        custos_effective_action=CustosEffectiveAction.WOULD_ERROR,
        alignment_status=PolicyRuntimeAlignment.SHADOW_ERROR,
        mismatch_codes=(PolicyRuntimeMismatch.CUSTOS_SHADOW_RESOLUTION_ERROR.value,),
        reason_codes=tuple(reason_codes),
        context_hash=context_hash,
        registry_hash=registry_hash,
        runtime_snapshot_hash=runtime_snapshot_hash,
    ).with_projection_hash()
    return projection.to_canonical_dict()


def _custos_effective_action(action: ShadowAction) -> CustosEffectiveAction:
    mapping = {
        ShadowAction.WOULD_ALLOW: CustosEffectiveAction.WOULD_ALLOW,
        ShadowAction.WOULD_WARN: CustosEffectiveAction.WOULD_WARN,
        ShadowAction.WOULD_REQUIRE_APPROVAL: (
            CustosEffectiveAction.WOULD_REQUIRE_APPROVAL
        ),
        ShadowAction.WOULD_DENY: CustosEffectiveAction.WOULD_DENY,
        ShadowAction.WOULD_NOT_APPLY: CustosEffectiveAction.WOULD_NOT_APPLICABLE,
        ShadowAction.WOULD_ERROR: CustosEffectiveAction.WOULD_ERROR,
    }
    try:
        return mapping[action]
    except KeyError as exc:
        raise PolicyRuntimeProjectionError(
            f"unknown shadow action: {getattr(action, 'value', action)}"
        ) from exc


def _alignment(
    runtime_action: RuntimeEffectiveAction,
    custos_action: CustosEffectiveAction,
) -> tuple[PolicyRuntimeAlignment, list[str]]:
    if custos_action is CustosEffectiveAction.WOULD_ERROR:
        return (
            PolicyRuntimeAlignment.SHADOW_ERROR,
            [PolicyRuntimeMismatch.CUSTOS_SHADOW_RESOLUTION_ERROR.value],
        )
    if runtime_action is RuntimeEffectiveAction.RUNTIME_UNKNOWN:
        return (
            PolicyRuntimeAlignment.INSUFFICIENT_CONTEXT,
            [PolicyRuntimeMismatch.RUNTIME_CONTEXT_INSUFFICIENT.value],
        )
    if custos_action is CustosEffectiveAction.WOULD_NOT_APPLICABLE:
        return (
            PolicyRuntimeAlignment.INSUFFICIENT_CONTEXT,
            [PolicyRuntimeMismatch.CUSTOS_CONTEXT_INSUFFICIENT.value],
        )

    matrix: dict[
        tuple[RuntimeEffectiveAction, CustosEffectiveAction],
        tuple[PolicyRuntimeAlignment, list[str]],
    ] = {
        (
            RuntimeEffectiveAction.RUNTIME_ALLOW,
            CustosEffectiveAction.WOULD_ALLOW,
        ): (PolicyRuntimeAlignment.ALIGNED, []),
        (
            RuntimeEffectiveAction.RUNTIME_ALLOW,
            CustosEffectiveAction.WOULD_DENY,
        ): (
            PolicyRuntimeAlignment.CUSTOS_STRICTER,
            [PolicyRuntimeMismatch.RUNTIME_ALLOWED_CUSTOS_WOULD_DENY.value],
        ),
        (
            RuntimeEffectiveAction.RUNTIME_ALLOW,
            CustosEffectiveAction.WOULD_REQUIRE_APPROVAL,
        ): (
            PolicyRuntimeAlignment.CUSTOS_STRICTER,
            [
                PolicyRuntimeMismatch.RUNTIME_ALLOWED_CUSTOS_WOULD_REQUIRE_APPROVAL.value
            ],
        ),
        (
            RuntimeEffectiveAction.RUNTIME_ALLOW,
            CustosEffectiveAction.WOULD_WARN,
        ): (
            PolicyRuntimeAlignment.CUSTOS_STRICTER,
            [PolicyRuntimeMismatch.RUNTIME_ALLOWED_CUSTOS_WOULD_WARN.value],
        ),
        (
            RuntimeEffectiveAction.RUNTIME_DENY,
            CustosEffectiveAction.WOULD_ALLOW,
        ): (
            PolicyRuntimeAlignment.RUNTIME_STRICTER,
            [PolicyRuntimeMismatch.RUNTIME_DENIED_CUSTOS_WOULD_ALLOW.value],
        ),
        (
            RuntimeEffectiveAction.RUNTIME_REQUIRE_APPROVAL,
            CustosEffectiveAction.WOULD_ALLOW,
        ): (
            PolicyRuntimeAlignment.RUNTIME_STRICTER,
            [
                PolicyRuntimeMismatch.RUNTIME_REQUIRES_APPROVAL_CUSTOS_WOULD_ALLOW.value
            ],
        ),
        (
            RuntimeEffectiveAction.RUNTIME_WARN,
            CustosEffectiveAction.WOULD_ALLOW,
        ): (
            PolicyRuntimeAlignment.RUNTIME_STRICTER,
            [PolicyRuntimeMismatch.RUNTIME_WARNED_CUSTOS_WOULD_ALLOW.value],
        ),
    }
    return matrix.get((runtime_action, custos_action), (PolicyRuntimeAlignment.ALIGNED, []))


def _sandbox_family_stricter_than_allow(resolved_policy: ResolvedPolicySet) -> bool:
    for decision in resolved_policy.family_decisions:
        if decision.family is PolicyFamily.SANDBOX and decision.effective_shadow_action in {
            ShadowAction.WOULD_DENY,
            ShadowAction.WOULD_REQUIRE_APPROVAL,
            ShadowAction.WOULD_WARN,
            ShadowAction.WOULD_ERROR,
        }:
            return True
    return False


def _validate_string_tuple(
    values: tuple[str, ...],
    field_name: str,
    exc_type: type[Exception],
) -> None:
    if not isinstance(values, tuple) or any(not isinstance(v, str) for v in values):
        raise exc_type(f"{field_name} must be a tuple of strings")


def _validate_metadata(
    metadata: Mapping[str, Any],
    path: str,
    exc_type: type[Exception],
) -> None:
    if not isinstance(metadata, MappingABC):
        raise exc_type(f"{path} must be a mapping")
    _assert_json_safe(metadata, path, exc_type=exc_type)


def _validate_optional_hash(
    value: str | None,
    field_name: str,
    exc_type: type[Exception],
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or len(value) != 64:
        raise exc_type(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise exc_type(f"{field_name} must be a SHA-256 hex digest") from exc


def _assert_json_safe(
    value: object,
    path: str,
    *,
    exc_type: type[Exception] = PolicyShadowProjectionError,
) -> None:
    if value is None or isinstance(value, str | int | float | bool):
        return
    if isinstance(value, list | tuple):
        for idx, item in enumerate(value):
            _assert_json_safe(item, f"{path}[{idx}]", exc_type=exc_type)
        return
    if isinstance(value, MappingABC):
        for key, item in value.items():
            if not isinstance(key, str):
                raise exc_type(f"metadata key at {path} must be a string")
            _assert_json_safe(item, f"{path}.{key}", exc_type=exc_type)
        return
    raise exc_type(f"value at {path} is not JSON-safe")
