"""P1.ENF-A policy resolver influence for runtime submit preflight."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .governance_enforcement import GovernanceEnforcementMode
from .policy_cards.registry import PolicyCardRegistry
from .policy_cards.resolution_context import PolicyResolutionContext
from .policy_cards.resolution_result import FamilyDecision, ResolvedPolicySet
from .policy_cards.resolver import resolve_policy_cards_from_registry


class PolicyResolverSubmitInfluenceStatus(str, Enum):
    SHADOW_ONLY = "shadow_only"
    ADVISORY_RECORDED = "advisory_recorded"
    ALLOW = "allow"
    BLOCKED_POLICY_DENY = "blocked_policy_deny"
    BLOCKED_POLICY_ERROR = "blocked_policy_error"
    BLOCKED_STRICT_CONFLICT = "blocked_strict_conflict"
    BLOCKED_MISSING_REQUIRED_CONTEXT = "blocked_missing_required_context"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class PolicyResolverSubmitArtifact:
    mode: GovernanceEnforcementMode
    status: PolicyResolverSubmitInfluenceStatus
    enforced: bool
    context_hash: str = ""
    registry_hash: str = ""
    resolved_policy_hash: str = ""
    overall_decision: str = ""
    effective_shadow_action: str = ""
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    blocker_reason: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "blocker_reason": self.blocker_reason,
            "context_hash": self.context_hash,
            "effective_shadow_action": self.effective_shadow_action,
            "enforced": self.enforced,
            "mode": self.mode.value,
            "overall_decision": self.overall_decision,
            "reason_codes": sorted(self.reason_codes),
            "registry_hash": self.registry_hash,
            "resolved_policy_hash": self.resolved_policy_hash,
            "status": self.status.value,
            "violations": sorted(self.violations),
            "warnings": sorted(self.warnings),
        }

    @property
    def artifact_hash(self) -> str:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicyResolverSubmitGateResult:
    status: PolicyResolverSubmitInfluenceStatus
    should_block: bool
    artifact: PolicyResolverSubmitArtifact
    resolved_policy: ResolvedPolicySet | None = None
    error_type: str = ""

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact.to_canonical_dict(),
            "artifact_hash": self.artifact.artifact_hash,
            "error_type": self.error_type,
            "should_block": self.should_block,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class PolicyResolverSubmitInfluence:
    mode: GovernanceEnforcementMode
    require_policy_context: bool = False

    def evaluate(
        self,
        *,
        registry: PolicyCardRegistry | None,
        context: PolicyResolutionContext | None,
    ) -> PolicyResolverSubmitGateResult:
        return evaluate_policy_resolver_submit_influence(
            mode=self.mode,
            require_policy_context=self.require_policy_context,
            registry=registry,
            context=context,
        )


@dataclass(frozen=True)
class PolicyResolverShadowCompatibilityProof:
    shadow_preserves_existing_submit_behavior: bool = True
    advisory_preserves_existing_submit_behavior: bool = True
    enforce_fail_closed_is_explicit_mode_only: bool = True
    default_mode: str = GovernanceEnforcementMode.SHADOW_ONLY.value

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "advisory_preserves_existing_submit_behavior": (
                self.advisory_preserves_existing_submit_behavior
            ),
            "default_mode": self.default_mode,
            "enforce_fail_closed_is_explicit_mode_only": (
                self.enforce_fail_closed_is_explicit_mode_only
            ),
            "shadow_preserves_existing_submit_behavior": (
                self.shadow_preserves_existing_submit_behavior
            ),
        }


def evaluate_policy_resolver_submit_influence(
    *,
    mode: GovernanceEnforcementMode,
    require_policy_context: bool,
    registry: PolicyCardRegistry | None,
    context: PolicyResolutionContext | None,
) -> PolicyResolverSubmitGateResult:
    if mode is GovernanceEnforcementMode.DISABLED_UNAVAILABLE:
        return _result(
            mode,
            PolicyResolverSubmitInfluenceStatus.UNAVAILABLE,
            enforced=False,
            should_block=False,
            blocker_reason="policy submit influence disabled/unavailable",
        )

    if registry is None or context is None:
        status = PolicyResolverSubmitInfluenceStatus.UNAVAILABLE
        should_block = False
        if mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED and require_policy_context:
            status = PolicyResolverSubmitInfluenceStatus.BLOCKED_MISSING_REQUIRED_CONTEXT
            should_block = True
        return _result(
            mode,
            status,
            enforced=should_block,
            should_block=should_block,
            blocker_reason="required policy resolver context unavailable"
            if should_block
            else "policy resolver context unavailable",
        )

    try:
        registry_hash = registry.canonical_hash()
        resolved = resolve_policy_cards_from_registry(context, registry)
        status = _status_for_resolved(mode, resolved)
        should_block = _should_block(mode, status)
        artifact = PolicyResolverSubmitArtifact(
            mode=mode,
            status=status,
            enforced=should_block,
            context_hash=context.context_hash,
            registry_hash=registry_hash,
            resolved_policy_hash=resolved.canonical_hash or "",
            overall_decision=resolved.overall_decision.value,
            effective_shadow_action=resolved.effective_shadow_action.value,
            reason_codes=resolved.reason_codes,
            warnings=resolved.warnings,
            violations=resolved.violations,
            blocker_reason=_blocker_reason(status) if should_block else "",
        )
        return PolicyResolverSubmitGateResult(
            status=status,
            should_block=should_block,
            artifact=artifact,
            resolved_policy=resolved,
        )
    except Exception as exc:
        should_block = mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED
        status = (
            PolicyResolverSubmitInfluenceStatus.ERROR
            if not should_block
            else PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_ERROR
        )
        return _result(
            mode,
            status,
            enforced=should_block,
            should_block=should_block,
            blocker_reason=f"policy resolver error: {type(exc).__name__}",
            error_type=type(exc).__name__,
        )


def policy_submit_gate_result_to_artifact(
    result: PolicyResolverSubmitGateResult,
) -> dict[str, Any]:
    return result.to_canonical_dict()


def _status_for_resolved(
    mode: GovernanceEnforcementMode,
    resolved: ResolvedPolicySet,
) -> PolicyResolverSubmitInfluenceStatus:
    if mode is GovernanceEnforcementMode.SHADOW_ONLY:
        return PolicyResolverSubmitInfluenceStatus.SHADOW_ONLY
    if mode is GovernanceEnforcementMode.ADVISORY:
        return PolicyResolverSubmitInfluenceStatus.ADVISORY_RECORDED
    if _has_strict_conflict(resolved):
        return PolicyResolverSubmitInfluenceStatus.BLOCKED_STRICT_CONFLICT
    if resolved.overall_decision is FamilyDecision.DENY:
        return PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_DENY
    if resolved.overall_decision is FamilyDecision.ERROR:
        return PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_ERROR
    return PolicyResolverSubmitInfluenceStatus.ALLOW


def _should_block(
    mode: GovernanceEnforcementMode,
    status: PolicyResolverSubmitInfluenceStatus,
) -> bool:
    if mode is not GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED:
        return False
    return status in {
        PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_DENY,
        PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_ERROR,
        PolicyResolverSubmitInfluenceStatus.BLOCKED_STRICT_CONFLICT,
        PolicyResolverSubmitInfluenceStatus.BLOCKED_MISSING_REQUIRED_CONTEXT,
    }


def _has_strict_conflict(resolved: ResolvedPolicySet) -> bool:
    candidates = (
        *resolved.reason_codes,
        *resolved.warnings,
        *resolved.violations,
    )
    return any("CONFLICT" in item.upper() and "STRICT" in item.upper() for item in candidates)


def _blocker_reason(status: PolicyResolverSubmitInfluenceStatus) -> str:
    return {
        PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_DENY: (
            "policy resolver returned deny"
        ),
        PolicyResolverSubmitInfluenceStatus.BLOCKED_POLICY_ERROR: (
            "policy resolver returned or raised error"
        ),
        PolicyResolverSubmitInfluenceStatus.BLOCKED_STRICT_CONFLICT: (
            "policy resolver reported strict conflict"
        ),
        PolicyResolverSubmitInfluenceStatus.BLOCKED_MISSING_REQUIRED_CONTEXT: (
            "required policy resolver context missing"
        ),
    }.get(status, "")


def _result(
    mode: GovernanceEnforcementMode,
    status: PolicyResolverSubmitInfluenceStatus,
    *,
    enforced: bool,
    should_block: bool,
    blocker_reason: str = "",
    error_type: str = "",
) -> PolicyResolverSubmitGateResult:
    artifact = PolicyResolverSubmitArtifact(
        mode=mode,
        status=status,
        enforced=enforced,
        blocker_reason=blocker_reason,
    )
    return PolicyResolverSubmitGateResult(
        status=status,
        should_block=should_block,
        artifact=artifact,
        error_type=error_type,
    )
