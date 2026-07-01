"""P1.ENF-A governance enforcement mode contracts.

These objects are small runtime contracts for the first enforcement bridge.
The default mode preserves existing behavior. Only ``ENFORCE_FAIL_CLOSED`` may
turn hard policy or identity preflight failures into submit blockers.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class GovernanceEnforcementMode(str, Enum):
    SHADOW_ONLY = "shadow_only"
    ADVISORY = "advisory"
    ENFORCE_FAIL_CLOSED = "enforce_fail_closed"
    DISABLED_UNAVAILABLE = "disabled_unavailable"


class GovernanceEnforcementModeStatus(str, Enum):
    SHADOW_COMPATIBLE = "shadow_compatible"
    ADVISORY_ONLY = "advisory_only"
    ENFORCING_FAIL_CLOSED = "enforcing_fail_closed"
    UNAVAILABLE = "unavailable"


class GovernanceEnforcementBoundary(str, Enum):
    POLICY_RESOLVER_SUBMIT_INFLUENCE = "policy_resolver_submit_influence"
    IDENTITY_SUBMIT_CONTEXT = "identity_submit_context"
    IDENTITY_KERNEL_INVARIANT = "identity_kernel_invariant"
    SANDBOX_BACKEND_GATE = "sandbox_backend_gate"
    ENTRYPOINT_BYPASS_GUARD = "entrypoint_bypass_guard"
    SIDE_EFFECT_PROOF = "side_effect_proof"


@dataclass(frozen=True)
class GovernanceEnforcementConfig:
    mode: GovernanceEnforcementMode = GovernanceEnforcementMode.SHADOW_ONLY
    require_policy_context: bool = False
    require_identity_context: bool = False
    require_safe_sandbox_backend: bool = False
    attach_submit_artifacts: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.mode, GovernanceEnforcementMode):
            raise TypeError("mode must be a GovernanceEnforcementMode")
        for field_name in (
            "require_policy_context",
            "require_identity_context",
            "require_safe_sandbox_backend",
            "attach_submit_artifacts",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be bool")

    @property
    def status(self) -> GovernanceEnforcementModeStatus:
        return _MODE_STATUS[self.mode]

    @property
    def can_fail_closed(self) -> bool:
        return self.mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "attach_submit_artifacts": self.attach_submit_artifacts,
            "mode": self.mode.value,
            "require_identity_context": self.require_identity_context,
            "require_policy_context": self.require_policy_context,
            "require_safe_sandbox_backend": self.require_safe_sandbox_backend,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class GovernanceEnforcementResult:
    mode: GovernanceEnforcementMode
    status: GovernanceEnforcementModeStatus
    boundary: GovernanceEnforcementBoundary
    truth_label: str
    blocked: bool = False
    reason_codes: tuple[str, ...] = ()
    artifacts: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.mode, GovernanceEnforcementMode):
            raise TypeError("mode must be a GovernanceEnforcementMode")
        if not isinstance(self.status, GovernanceEnforcementModeStatus):
            raise TypeError("status must be a GovernanceEnforcementModeStatus")
        if not isinstance(self.boundary, GovernanceEnforcementBoundary):
            raise TypeError("boundary must be a GovernanceEnforcementBoundary")
        if not isinstance(self.blocked, bool):
            raise TypeError("blocked must be bool")
        if not isinstance(self.reason_codes, tuple) or any(
            not isinstance(item, str) for item in self.reason_codes
        ):
            raise TypeError("reason_codes must be a tuple of strings")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "artifacts": _json_safe_mapping(self.artifacts),
            "blocked": self.blocked,
            "boundary": self.boundary.value,
            "mode": self.mode.value,
            "reason_codes": sorted(self.reason_codes),
            "status": self.status.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class P1ENFASideEffectProof:
    p2_9_b_implemented: bool = False
    p2_9_c_started: bool = False
    p2_9_d_started: bool = False
    p2_10_plus_started: bool = False
    full_custos_runtime_created: bool = False
    permission_matrix_created: bool = False
    shell_command_router_created: bool = False
    product_ui_created: bool = False
    identity_cli_refactored: bool = False
    golden_thread_b_created: bool = False
    sandbox_backend_rewritten: bool = False
    memory_behavior_rewritten: bool = False
    trace_ledger_rewritten: bool = False
    fake_trace_verified_claimed: bool = False
    fake_live_shell_claimed: bool = False

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "fake_live_shell_claimed": self.fake_live_shell_claimed,
            "fake_trace_verified_claimed": self.fake_trace_verified_claimed,
            "full_custos_runtime_created": self.full_custos_runtime_created,
            "golden_thread_b_created": self.golden_thread_b_created,
            "identity_cli_refactored": self.identity_cli_refactored,
            "memory_behavior_rewritten": self.memory_behavior_rewritten,
            "p2_10_plus_started": self.p2_10_plus_started,
            "p2_9_b_implemented": self.p2_9_b_implemented,
            "p2_9_c_started": self.p2_9_c_started,
            "p2_9_d_started": self.p2_9_d_started,
            "permission_matrix_created": self.permission_matrix_created,
            "product_ui_created": self.product_ui_created,
            "sandbox_backend_rewritten": self.sandbox_backend_rewritten,
            "shell_command_router_created": self.shell_command_router_created,
            "trace_ledger_rewritten": self.trace_ledger_rewritten,
        }


@dataclass(frozen=True)
class P1ENFAResult:
    mode: GovernanceEnforcementMode
    policy_influence_result: Mapping[str, Any]
    identity_submit_context_result: Mapping[str, Any]
    entrypoint_guard_result: Mapping[str, Any]
    side_effect_proof: P1ENFASideEffectProof = field(default_factory=P1ENFASideEffectProof)
    unavailable_capabilities: tuple[str, ...] = (
        "full_custos_runtime",
        "full_permission_matrix",
        "product_shell_command_router",
        "product_ui",
        "golden_thread_b",
        "safe_sandbox_backend_hardening",
    )
    next_recommended_pack: str = "P2.9-B"

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "entrypoint_guard_result": _json_safe_mapping(self.entrypoint_guard_result),
            "identity_submit_context_result": _json_safe_mapping(
                self.identity_submit_context_result
            ),
            "mode": self.mode.value,
            "next_recommended_pack": self.next_recommended_pack,
            "policy_influence_result": _json_safe_mapping(self.policy_influence_result),
            "side_effect_proof": self.side_effect_proof.to_canonical_dict(),
            "unavailable_capabilities": sorted(self.unavailable_capabilities),
        }

    @property
    def result_hash(self) -> str:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_MODE_STATUS: dict[GovernanceEnforcementMode, GovernanceEnforcementModeStatus] = {
    GovernanceEnforcementMode.SHADOW_ONLY: (
        GovernanceEnforcementModeStatus.SHADOW_COMPATIBLE
    ),
    GovernanceEnforcementMode.ADVISORY: GovernanceEnforcementModeStatus.ADVISORY_ONLY,
    GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED: (
        GovernanceEnforcementModeStatus.ENFORCING_FAIL_CLOSED
    ),
    GovernanceEnforcementMode.DISABLED_UNAVAILABLE: (
        GovernanceEnforcementModeStatus.UNAVAILABLE
    ),
}


def _json_safe_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    json.dumps(payload, sort_keys=True, default=str)
    return payload
