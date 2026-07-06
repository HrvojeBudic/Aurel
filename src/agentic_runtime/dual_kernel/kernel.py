"""kernel.py — DualKernelRuntime facade: the first wiring into the live path.

A drop-in wrapper around a built ``Kernel`` that adds dual-kernel routing behind
a feature flag (``AUREL_DUAL_KERNEL=1``). It never edits ``runtime.py``.

  - flag OFF (default): ``submit`` is a pure pass-through to the inner runtime —
    bit-identical to today. No dual-kernel logic runs at all.
  - flag ON: each command is routed by measured autonomy (Σ + admit_step).
      FAST / HARD_GATED  → the existing, fully-traced inner ``submit`` (unchanged).
      GOVERNED           → a speculative PREFLIGHT in an ephemeral copy of the
                           live workspace; the merge gate judges the real verified
                           result; only on a PASS verdict does the command run for
                           real via the inner ``submit`` (which traces + mutates
                           live state normally). A rejected command never touches
                           live state and is returned blocked.

The speculative preflight uses a permissive approver — it only needs to produce a
real verifier result. Live governance is unchanged: the real execution still goes
through the inner runtime's real policy, HITL, verify and trace.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from ..core_types import AgentCard, CommandEnvelope, ObservationEnvelope, VerifierResult
from .merge_gate import DeploymentReadinessDecision, MergeContext, MergeGate
from .routing import AdmitDecision, Route
from .sigma import GovernanceStateVector, SigmaGovernor, _writes_of

if TYPE_CHECKING:  # pragma: no cover
    from ..runtime import CommandResult

_FLAG = "AUREL_DUAL_KERNEL"


def _flag_enabled() -> bool:
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass
class RouteRecord:
    command_id: str
    route: Route
    autonomy_index: int
    verdict: Optional[str] = None
    executed: bool = False
    reasons: list[str] = field(default_factory=list)


class DualKernelRuntime:
    def __init__(
        self,
        kernel: Any,
        *,
        enabled: Optional[bool] = None,
        sigma_gov: Optional[SigmaGovernor] = None,
        gate: Optional[MergeGate] = None,
        spec_approver: Optional[Any] = None,
    ) -> None:
        self.kernel = kernel
        self.runtime = kernel.runtime
        self.enabled = _flag_enabled() if enabled is None else enabled
        self.sigma_gov = sigma_gov or SigmaGovernor()
        self.gate = gate or MergeGate()
        self._spec_approver = spec_approver
        self._sigmas: dict[str, GovernanceStateVector] = {}
        self.route_log: list[RouteRecord] = []

    # ---- drop-in entry point ------------------------------------------- #
    def submit(self, cmd: CommandEnvelope, card: AgentCard) -> "CommandResult":
        if not self.enabled:
            return self.runtime.submit(cmd, card)  # bit-identical pass-through

        decision = self.runtime.policy.evaluate(cmd, card)  # same engine, pure
        sigma = self._sigma_for(cmd, card)
        admit: AdmitDecision = self.sigma_gov.admit_step(sigma, cmd, decision, card)
        rec = RouteRecord(cmd.id, admit.route, admit.autonomy_index,
                          reasons=admit.reasons)

        if admit.route in (Route.FAST, Route.HARD_GATED):
            result = self.runtime.submit(cmd, card)
            rec.executed = True
            rec.verdict = "inner_" + ("ok" if result.ok else "blocked")
        else:  # GOVERNED — speculative preflight, then real-on-pass
            verdict = self._preflight(cmd, card, sigma)
            rec.verdict = verdict.final_status.value
            if verdict.mergeable:
                result = self.runtime.submit(cmd, card)
                rec.executed = True
            else:
                result = self._blocked_result(cmd, verdict)

        self._sigmas[self._key(cmd)] = sigma.update(
            cmd, decision, approved=result.ok)
        self.route_log.append(rec)
        return result

    # ---- speculative preflight (real execution, ephemeral workspace) --- #
    def _preflight(
        self,
        cmd: CommandEnvelope,
        card: AgentCard,
        sigma: GovernanceStateVector,
    ) -> DeploymentReadinessDecision:
        live_root = getattr(self.runtime.tools.sandbox, "root", None)
        if not live_root:
            # non-filesystem sandbox: cannot speculate cheaply → treat as PASS
            # so the real inner submit (fully governed) still runs.
            return _auto_pass(cmd, sigma, card)

        from .. import build_runtime
        from ..sandbox import UnsafeLocalSandbox

        tmp = tempfile.mkdtemp(prefix="ar_spec_")
        try:
            shutil.copytree(live_root, tmp, dirs_exist_ok=True)
            child = build_runtime(
                sandbox=UnsafeLocalSandbox(root=tmp),
                approval_gate=self._spec_approver or _permissive_approver(),
                trace_backend="memory",
            )
            cr = child.runtime.submit(cmd, card)
            post_hash = cr.transition.entry_hash if cr.transition is not None else ""
            ctx = MergeContext(
                cmd=cmd,
                verifier_result=cr.verifier,
                sigma=sigma,
                card=card,
                child_write_paths=_writes_of(cmd),
                evidence_refs=(post_hash,) if post_hash else (),
                simulation_resolved=True,
                rollback_path_defined=True,
                is_isolated_fork=True,
            )
            return self.gate.evaluate(ctx)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ---- helpers -------------------------------------------------------- #
    def _key(self, cmd: CommandEnvelope) -> str:
        return cmd.parent_intent_id or "task_unbound"

    def _sigma_for(
        self, cmd: CommandEnvelope, card: AgentCard
    ) -> GovernanceStateVector:
        key = self._key(cmd)
        sigma = self._sigmas.get(key)
        if sigma is None:
            sigma = GovernanceStateVector(task_id=key, authority_card_id=card.id)
            self._sigmas[key] = sigma
        return sigma

    def _blocked_result(
        self, cmd: CommandEnvelope, verdict: DeploymentReadinessDecision
    ) -> "CommandResult":
        from ..runtime import CommandResult

        blockers = "; ".join(verdict.blockers) or verdict.final_status.value
        reason = f"merge gate {verdict.final_status.value}: {blockers}"
        obs = ObservationEnvelope.make(cmd.id, success=False, stderr=reason)
        vres = VerifierResult(False, "merge_gate",
                              reason=reason, code=verdict.final_status.value,
                              evidence=verdict.to_dict())
        return CommandResult(
            observation=obs, verifier=vres, decision=_null_decision(),
            transition=None)


# --------------------------------------------------------------------------- #
#  small helpers kept module-level to stay import-light
# --------------------------------------------------------------------------- #
def _permissive_approver() -> Any:
    from ..hitl import AutoApprover
    return AutoApprover(lambda r: True, allow_r2=True, allow_r3=True,
                        allow_r4=True, allow_r5=True)


def _null_decision() -> Any:
    from ..core_types import RiskLevel
    from ..policy import PolicyDecision, PolicyVerdict
    return PolicyDecision(verdict=PolicyVerdict.DENY, risk=RiskLevel.HIGH,
                          reasons=["merge gate rejected speculative fork"])


def _auto_pass(
    cmd: CommandEnvelope, sigma: GovernanceStateVector, card: AgentCard
) -> DeploymentReadinessDecision:
    from .merge_gate import MergeVerdict
    return DeploymentReadinessDecision(
        verdict=MergeVerdict.PASS, final_status=MergeVerdict.PASS,
        simulation_live_status="RESOLVED", authority_status="RESOLVED",
        reasons=["non-filesystem sandbox: preflight skipped, inner submit governs"])
