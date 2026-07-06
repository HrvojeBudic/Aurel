"""merge_gate.py — the canon-faithful merge gate.

The ONLY place a speculative worldline becomes LIVE state. Combines three
independent sources into one readiness verdict:

  - ABC compositionality conditions C1–C4 (Bhardwaj, Theorem 4.9)
  - DSE recoverable-boundary / discard-on-reject (Li et al.)
  - DSD Book 12 readiness blockers + verdict ladder (canon)

Every check is bound to a DSD no-collapse law via ``nc_merge_bindings.json`` and
verified in CI by :func:`nc_bindings.validate_coverage`. ``evaluate`` is pure
(no live sandbox needed); ``commit`` is the only method that mutates live state,
and only on a PASS verdict with authority resolved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

from ..core_types import AgentCard, CommandEnvelope, RiskLevel, VerifierResult
from . import nc_bindings
from .nc_bindings import NCBinding
from .sigma import GovernanceStateVector, _rank

if TYPE_CHECKING:  # pragma: no cover
    from ..worldline import MergeResult, WorldLineForest


class MergeVerdict(str, Enum):
    """DSD Book 12 verdict ladder — the merge-decision vocabulary."""

    PASS = "pass"
    PASS_WITH_WARNING = "pass_with_warning"
    REVIEW_REQUIRED = "review_required"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    NEEDS_AUTHORITY_REVIEW = "needs_authority_review"
    NEEDS_CANON_REVIEW = "needs_canon_review"
    INCONCLUSIVE = "inconclusive"
    FAIL = "fail"
    ROLLBACK_REQUIRED = "rollback_required"
    BLOCKING_FAIL = "blocking_fail"
    ARCHIVE_ONLY = "archive_only"


# Worst → best. Used to pick the final (risk-weighted) status among triggers.
_SEVERITY_ORDER: list[MergeVerdict] = [
    MergeVerdict.BLOCKING_FAIL,
    MergeVerdict.ROLLBACK_REQUIRED,
    MergeVerdict.FAIL,
    MergeVerdict.NEEDS_AUTHORITY_REVIEW,
    MergeVerdict.NEEDS_CANON_REVIEW,
    MergeVerdict.NEEDS_MORE_EVIDENCE,
    MergeVerdict.REVIEW_REQUIRED,
    MergeVerdict.INCONCLUSIVE,
    MergeVerdict.ARCHIVE_ONLY,
    MergeVerdict.PASS_WITH_WARNING,
    MergeVerdict.PASS,
]
_SEVERITY_RANK = {v: i for i, v in enumerate(_SEVERITY_ORDER)}

# Every gate id this module can emit. Bound to canon by validate_coverage().
GATE_IDS: frozenset[str] = frozenset({
    "C1_interface_compatibility",
    "C2_assumption_discharge",
    "C3_governance_consistency",
    "C4_recovery_independence",
    "state_verification",
    "simulation_live_resolved",
    "authority_resolved",
    "rollback_path_defined",
    "regression_baseline",
    "critical_slice",
    "memory_pollution",
})

_MERGEABLE = {MergeVerdict.PASS, MergeVerdict.PASS_WITH_WARNING}


@dataclass
class MergeContext:
    """Real evidence gathered from a speculative fork. No mocks: the caller
    (Praxis) supplies genuine values from the forked run."""

    cmd: CommandEnvelope
    verifier_result: VerifierResult
    sigma: GovernanceStateVector
    card: AgentCard
    child_write_paths: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()          # e.g. post-state hashes
    simulation_resolved: bool = False
    rollback_path_defined: bool = True
    is_isolated_fork: bool = True
    protected_test_touched: bool = False
    baseline_present: bool = True
    critical_slice_ok: bool = True
    memory_pollution_ok: bool = True
    soft_warnings: tuple[str, ...] = ()


@dataclass
class DeploymentReadinessDecision:
    """A readiness JUDGMENT — never the merge execution itself (Book 12 Ch 29)."""

    verdict: MergeVerdict
    final_status: MergeVerdict
    blockers: list[str] = field(default_factory=list)
    bindings: list[NCBinding] = field(default_factory=list)
    simulation_live_status: str = "UNRESOLVED"
    authority_status: str = "UNRESOLVED"
    evidence_refs: tuple[str, ...] = ()
    reasons: list[str] = field(default_factory=list)

    @property
    def mergeable(self) -> bool:
        return self.final_status in _MERGEABLE

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "final_status": self.final_status.value,
            "blockers": list(self.blockers),
            "nc_laws": [b.nc_law for b in self.bindings],
            "simulation_live_status": self.simulation_live_status,
            "authority_status": self.authority_status,
            "evidence_refs": list(self.evidence_refs),
            "reasons": list(self.reasons),
        }


class MergeGate:
    def __init__(self) -> None:
        # Fail fast at construction if any emitted gate is uncovered by canon.
        nc_bindings.validate_coverage(GATE_IDS)

    # ---- ABC compositionality C1–C4 (real predicates) ------------------- #
    @staticmethod
    def _c1_interface_compatible(ctx: MergeContext) -> bool:
        allowed = [p.replace("\\", "/") for p in ctx.card.authority.write_paths]
        for raw in ctx.child_write_paths:
            path = raw.replace("\\", "/").lstrip("/")
            if not any(
                path == a.rstrip("/") or path.startswith(a.rstrip("/") + "/") or a in ("*", "")
                for a in allowed
            ):
                return False
        return True

    @staticmethod
    def _c2_assumption_discharge(ctx: MergeContext) -> bool:
        if ctx.protected_test_touched and not ctx.card.authority.allow_protected_mutation:
            return False
        # A write that produced no post-state evidence has not discharged its
        # handoff assumption.
        if ctx.child_write_paths and not ctx.evidence_refs:
            return False
        return True

    @staticmethod
    def _c3_governance_consistent(ctx: MergeContext) -> bool:
        auth = ctx.card.authority
        if ctx.sigma.net_or_secrets_used and not (auth.allow_network or auth.allow_secrets):
            return False
        return True

    @staticmethod
    def _c4_recovery_independent(ctx: MergeContext) -> bool:
        return ctx.is_isolated_fork

    # ---- the evaluation ------------------------------------------------- #
    def evaluate(self, ctx: MergeContext) -> DeploymentReadinessDecision:
        blockers: list[str] = []

        if not self._c1_interface_compatible(ctx):
            blockers.append("C1_interface_compatibility")
        if not self._c2_assumption_discharge(ctx):
            blockers.append("C2_assumption_discharge")
        if not self._c3_governance_consistent(ctx):
            blockers.append("C3_governance_consistency")
        if not self._c4_recovery_independent(ctx):
            blockers.append("C4_recovery_independence")

        if not ctx.verifier_result.passed:
            blockers.append("state_verification")
        if not ctx.simulation_resolved:
            blockers.append("simulation_live_resolved")

        authority_ok = ctx.sigma.approval_occurred or _rank(
            ctx.sigma.max_sensitivity
        ) < _rank(RiskLevel.HIGH)
        if not authority_ok:
            blockers.append("authority_resolved")

        if not ctx.rollback_path_defined:
            blockers.append("rollback_path_defined")
        if not ctx.baseline_present:
            blockers.append("regression_baseline")
        if not ctx.critical_slice_ok:
            blockers.append("critical_slice")
        if not ctx.memory_pollution_ok:
            blockers.append("memory_pollution")

        bindings = [nc_bindings.binding_for(g) for g in blockers]
        final = self._final_status(bindings, ctx)
        reasons = [f"{b.gate_id}: {b.statement} ({b.nc_law})" for b in bindings]

        return DeploymentReadinessDecision(
            verdict=final,
            final_status=final,
            blockers=blockers,
            bindings=bindings,
            simulation_live_status="RESOLVED" if ctx.simulation_resolved else "UNRESOLVED",
            authority_status="RESOLVED" if authority_ok else "UNRESOLVED",
            evidence_refs=ctx.evidence_refs,
            reasons=reasons,
        )

    @staticmethod
    def _final_status(bindings: list[NCBinding], ctx: MergeContext) -> MergeVerdict:
        if not bindings:
            return (
                MergeVerdict.PASS_WITH_WARNING if ctx.soft_warnings else MergeVerdict.PASS
            )
        worst = min(
            (MergeVerdict(b.verdict_on_fail) for b in bindings),
            key=lambda v: _SEVERITY_RANK[v],
        )
        return worst

    # ---- the only mutation of live state -------------------------------- #
    def commit(
        self,
        decision: DeploymentReadinessDecision,
        forest: "WorldLineForest",
        parent_run_id: str,
        child_run_id: str,
    ) -> "Optional[MergeResult]":
        """Merge the fork into LIVE state — ONLY on a mergeable verdict.

        Returns the ``MergeResult`` on merge, or ``None`` when the fork is
        discarded (governance rejected it). A rejected fork never touches the
        forest, so live state is provably untouched.
        """
        if not decision.mergeable:
            return None
        return forest.merge(parent_run_id, [child_run_id])
