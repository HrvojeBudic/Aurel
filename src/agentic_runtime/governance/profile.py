"""Governance scale G0–G5 (M6) — the manual autonomy spectrum.

A ``GovernanceProfile`` is a *preset over knobs that already exist*: the
``AutoApprover`` risk envelope, the ``GovernanceEnforcementConfig`` mode, the
sandbox/attestation requirement (M0), and the anchored-trace requirement (M2).
It introduces no new enforcement mechanism; it names coherent points on the axis

    G0 ABSOLUTE GOVERNED  ⟷  G5 HERETIC (free from all discretionary gates)

and materializes each into the concrete parameters ``build_runtime`` accepts.

Two invariants hold at *every* level, HERETIC included — the constitutional
floor: the hash-chained, externally anchored trace stays on, and no component
may raise its own level. A run that cannot prove its history is not sovereign,
so trace-off is never a valid level; the tradeoff is resolved in favor of
keeping the record (see docs/canon/GOVERNANCE_SCALE.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..approval import ApprovalRiskClass
from ..core_types import new_id, now, sha
from ..governance_enforcement import GovernanceEnforcementConfig, GovernanceEnforcementMode


class GovernanceLevel(str, Enum):
    G0 = "G0"  # ABSOLUTE GOVERNED — human approves everything beyond read-only
    G1 = "G1"  # Supervised
    G2 = "G2"  # Trusted
    G3 = "G3"  # Autonomous-in-workspace
    G4 = "G4"  # Frontier — ceiling until an anchor exists
    G5 = "G5"  # HERETIC — free from discretionary gates; floor still holds

    @property
    def rank(self) -> int:
        return int(self.value[1:])


_RISK_ORDER = [
    ApprovalRiskClass.R0,
    ApprovalRiskClass.R1,
    ApprovalRiskClass.R2,
    ApprovalRiskClass.R3,
    ApprovalRiskClass.R4,
    ApprovalRiskClass.R5,
]


@dataclass(frozen=True)
class GovernanceProfile:
    """Derived gate state for one governance level."""

    level: GovernanceLevel
    # Highest risk class auto-approved without a human; classes above go to HITL.
    auto_approve_max: ApprovalRiskClass
    # Highest risk class permitted at all (hard ceiling; above this is refused).
    reversibility_cap: ApprovalRiskClass
    enforcement_mode: GovernanceEnforcementMode
    sandbox_required: bool
    attestation_required: bool
    trace_required: bool           # floor — True at every level
    anchor_required: bool          # floor for G5; strong-recommended below
    budget_hard: bool

    # ------------------------------------------------------------------ #
    def auto_approver_kwargs(self) -> dict[str, bool]:
        """Materialize the ``AutoApprover`` risk envelope for this level."""
        cap = _RISK_ORDER.index(self.auto_approve_max)
        return {
            f"allow_r{i}": (i <= cap) for i in range(6)
        }

    def enforcement_config(self) -> GovernanceEnforcementConfig:
        fail_closed = self.enforcement_mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED
        return GovernanceEnforcementConfig(
            mode=self.enforcement_mode,
            require_policy_context=fail_closed,
            require_identity_context=fail_closed,
            require_safe_sandbox_backend=self.sandbox_required,
            attach_submit_artifacts=True,
        )

    def permits_risk(self, risk_class: ApprovalRiskClass) -> bool:
        return _RISK_ORDER.index(risk_class) <= _RISK_ORDER.index(self.reversibility_cap)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "auto_approve_max": self.auto_approve_max.value,
            "reversibility_cap": self.reversibility_cap.value,
            "enforcement_mode": self.enforcement_mode.value,
            "sandbox_required": self.sandbox_required,
            "attestation_required": self.attestation_required,
            "trace_required": self.trace_required,
            "anchor_required": self.anchor_required,
            "budget_hard": self.budget_hard,
        }

    def config_hash(self) -> str:
        import json

        return sha(json.dumps(self.to_dict(), sort_keys=True))


# The spectrum. Trace is required at EVERY level (the floor).
_PRESETS: dict[GovernanceLevel, GovernanceProfile] = {
    GovernanceLevel.G0: GovernanceProfile(
        level=GovernanceLevel.G0,
        auto_approve_max=ApprovalRiskClass.R0,
        reversibility_cap=ApprovalRiskClass.R2,
        enforcement_mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        sandbox_required=True, attestation_required=True,
        trace_required=True, anchor_required=True, budget_hard=True,
    ),
    GovernanceLevel.G1: GovernanceProfile(
        level=GovernanceLevel.G1,
        auto_approve_max=ApprovalRiskClass.R1,
        reversibility_cap=ApprovalRiskClass.R3,
        enforcement_mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        sandbox_required=True, attestation_required=True,
        trace_required=True, anchor_required=True, budget_hard=True,
    ),
    GovernanceLevel.G2: GovernanceProfile(
        level=GovernanceLevel.G2,
        auto_approve_max=ApprovalRiskClass.R2,
        reversibility_cap=ApprovalRiskClass.R3,
        enforcement_mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        sandbox_required=True, attestation_required=True,
        trace_required=True, anchor_required=True, budget_hard=True,
    ),
    GovernanceLevel.G3: GovernanceProfile(
        level=GovernanceLevel.G3,
        auto_approve_max=ApprovalRiskClass.R3,
        reversibility_cap=ApprovalRiskClass.R4,
        enforcement_mode=GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        sandbox_required=True, attestation_required=True,
        trace_required=True, anchor_required=True, budget_hard=True,
    ),
    GovernanceLevel.G4: GovernanceProfile(
        level=GovernanceLevel.G4,
        auto_approve_max=ApprovalRiskClass.R4,
        reversibility_cap=ApprovalRiskClass.R5,
        enforcement_mode=GovernanceEnforcementMode.ADVISORY,
        sandbox_required=True, attestation_required=True,
        trace_required=True, anchor_required=True, budget_hard=False,
    ),
    GovernanceLevel.G5: GovernanceProfile(
        level=GovernanceLevel.G5,
        auto_approve_max=ApprovalRiskClass.R5,
        reversibility_cap=ApprovalRiskClass.R5,
        enforcement_mode=GovernanceEnforcementMode.SHADOW_ONLY,
        sandbox_required=False, attestation_required=False,
        trace_required=True,          # floor — never off, even in HERETIC
        anchor_required=True,         # floor — G5 refused without it
        budget_hard=False,
    ),
}


def profile_for(level: GovernanceLevel) -> GovernanceProfile:
    return _PRESETS[level]


def governed_approver(profile: GovernanceProfile):
    """Build the ``AutoApprover`` that enacts a profile's HITL envelope.

    A predicate additionally refuses any risk class above the reversibility cap,
    so the hard ceiling holds even where the auto-approve envelope would allow.
    """
    from ..hitl import AutoApprover

    def _within_cap(req) -> bool:
        return profile.permits_risk(req.risk_class)

    kw = profile.auto_approver_kwargs()
    return AutoApprover(
        _within_cap,
        allow_r0=kw["allow_r0"], allow_r1=kw["allow_r1"], allow_r2=kw["allow_r2"],
        allow_r3=kw["allow_r3"], allow_r4=kw["allow_r4"], allow_r5=kw["allow_r5"],
    )


def runtime_kwargs_for(profile: GovernanceProfile, *, trace_dir: str) -> dict:
    """Translate a profile into ``build_runtime`` keyword arguments.

    The profile is a preset over knobs that already exist — this is where it
    materializes them. Trace is always persistent + anchored (the floor).
    """
    return {
        "approval_gate": governed_approver(profile),
        "governance_enforcement_config": profile.enforcement_config(),
        "trace_backend": "persistent",
        "trace_dir": trace_dir,
        "trace_anchor": profile.anchor_required,
    }


class GovernanceFloorViolation(RuntimeError):
    """Raised when a requested level would breach the constitutional floor."""


@dataclass(frozen=True)
class OverrideReceipt:
    """An operator's audited authorization to exceed the agent ceiling.

    Raising above the agent ceiling (never above the system ceiling) requires
    one of these: a reason, a single-run scope, a TTL, and an operator identity.
    It is recorded like any approval receipt.
    """

    receipt_id: str
    operator: str
    from_level: GovernanceLevel
    to_level: GovernanceLevel
    run_id: str
    reason: str
    ttl_seconds: float
    issued_at: float = field(default_factory=now)

    def valid_at(self, when: Optional[float] = None) -> bool:
        when = now() if when is None else when
        return when <= self.issued_at + self.ttl_seconds

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "operator": self.operator,
            "from_level": self.from_level.value,
            "to_level": self.to_level.value,
            "run_id": self.run_id,
            "reason": self.reason,
            "ttl_seconds": self.ttl_seconds,
            "issued_at": self.issued_at,
        }


def issue_override(
    *, operator: str, from_level: GovernanceLevel, to_level: GovernanceLevel,
    run_id: str, reason: str, ttl_seconds: float = 3600.0,
) -> OverrideReceipt:
    if not operator.strip():
        raise ValueError("override requires an operator identity")
    if not reason.strip():
        raise ValueError("override requires a reason")
    return OverrideReceipt(
        receipt_id=new_id("govoverride"), operator=operator,
        from_level=from_level, to_level=to_level, run_id=run_id,
        reason=reason, ttl_seconds=ttl_seconds,
    )


@dataclass(frozen=True)
class ResolvedGovernance:
    level: GovernanceLevel
    profile: GovernanceProfile
    reason: str
    override_applied: bool = False


def resolve_effective(
    *,
    system_ceiling: GovernanceLevel,
    agent_ceiling: GovernanceLevel,
    task_request: GovernanceLevel,
    override: Optional[OverrideReceipt] = None,
    anchor_available: bool = False,
    attestation_ok: bool = False,
) -> ResolvedGovernance:
    """Resolve the effective level. Most restrictive wins; override is audited.

    ``effective = min(system, agent, task)`` — a task may only lower itself. A
    valid :class:`OverrideReceipt` may raise the *task* above the agent ceiling,
    never above the system ceiling. The constitutional floor caps the result:
    G5 is refused (capped to G4) unless both an external anchor and a green
    sandbox attestation are available.
    """
    base = min(system_ceiling, agent_ceiling, task_request, key=lambda g: g.rank)
    reason = f"min(system={system_ceiling.value}, agent={agent_ceiling.value}, task={task_request.value})"
    override_applied = False

    if override is not None and override.valid_at() and override.run_id:
        # Override may lift above the agent ceiling but never past the system one.
        candidate = min(override.to_level, system_ceiling, key=lambda g: g.rank)
        if candidate.rank > base.rank:
            base = candidate
            override_applied = True
            reason = (
                f"override by {override.operator} -> {candidate.value} "
                f"(capped at system={system_ceiling.value})"
            )

    # Constitutional floor: G5 requires anchor + attestation, else cap to G4.
    if base is GovernanceLevel.G5 and not (anchor_available and attestation_ok):
        base = GovernanceLevel.G4
        reason += "; G5 refused (needs anchored trace + sandbox attestation) -> capped to G4"

    return ResolvedGovernance(
        level=base, profile=profile_for(base), reason=reason,
        override_applied=override_applied,
    )
