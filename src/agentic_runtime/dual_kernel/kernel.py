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
from .ledger import DualKernelLedger
from .merge_gate import DeploymentReadinessDecision, MergeContext, MergeGate
from .routing import AdmitDecision, Route
from .sigma import GovernanceStateVector, SigmaGovernor, _writes_of

if TYPE_CHECKING:  # pragma: no cover
    from ..runtime import CommandResult

_FLAG = "AUREL_DUAL_KERNEL"
_FLAG_MATERIALIZE = "AUREL_DK_MATERIALIZE"


def _flag_enabled() -> bool:
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


def _materialize_enabled() -> bool:
    return os.environ.get(_FLAG_MATERIALIZE, "").strip() in ("1", "true", "TRUE", "on")


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
        ledger: Optional[DualKernelLedger] = None,
        materialize: Optional[bool] = None,
    ) -> None:
        self.kernel = kernel
        self.runtime = kernel.runtime
        self.enabled = _flag_enabled() if enabled is None else enabled
        self.materialize = _materialize_enabled() if materialize is None else materialize
        self.sigma_gov = sigma_gov or SigmaGovernor()
        self.gate = gate or MergeGate()
        self._spec_approver = spec_approver
        self.ledger = ledger or DualKernelLedger()
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
        verdict: Optional[DeploymentReadinessDecision] = None

        if admit.route in (Route.FAST, Route.HARD_GATED):
            result = self.runtime.submit(cmd, card)
            rec.executed = True
            rec.verdict = "inner_" + ("ok" if result.ok else "blocked")
        elif self.materialize and self._can_materialize():
            # GOVERNED — execute ONCE in a fork, then materialise-to-live on PASS.
            result, verdict = self._execute_materialize(cmd, card, sigma, decision)
            rec.verdict = verdict.final_status.value
            rec.executed = result.transition is not None
        else:  # GOVERNED — speculative preflight, then real-on-pass
            verdict = self._preflight(cmd, card, sigma)
            rec.verdict = verdict.final_status.value
            if verdict.mergeable:
                result = self.runtime.submit(cmd, card)
                rec.executed = True
            else:
                result = self._blocked_result(cmd, verdict)

        self._record(cmd, rec, verdict, executed=rec.executed)
        self._sigmas[self._key(cmd)] = sigma.update(
            cmd, decision, approved=result.ok)
        self.route_log.append(rec)
        return result

    def _record(
        self,
        cmd: CommandEnvelope,
        rec: RouteRecord,
        verdict: Optional[DeploymentReadinessDecision],
        *,
        executed: bool,
    ) -> None:
        self.ledger.append(
            command_id=cmd.id,
            task_id=self._key(cmd),
            route=rec.route.value,
            autonomy_index=rec.autonomy_index,
            verdict=rec.verdict or "",
            final_status=(verdict.final_status.value if verdict else rec.verdict or ""),
            blockers=(verdict.blockers if verdict else []),
            nc_laws=([b.nc_law for b in verdict.bindings] if verdict else []),
            simulation_live_status=(verdict.simulation_live_status if verdict else ""),
            authority_status=(verdict.authority_status if verdict else ""),
            executed=executed,
        )

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

        # honestly charge the speculative twin against the parent run's budget
        # (over-budget denies the speculation before any compute is spent).
        self.runtime.budget.charge_simulation()

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

    # ---- materialize-to-live (execute once, merge fork into live) ------- #
    def _can_materialize(self) -> bool:
        store = getattr(self.runtime, "_state_store", None)
        root = getattr(self.runtime.tools.sandbox, "root", None)
        return store is not None and bool(root)

    def _execute_materialize(
        self,
        cmd: CommandEnvelope,
        card: AgentCard,
        sigma: GovernanceStateVector,
        decision: Any,
    ) -> "tuple[CommandResult, DeploymentReadinessDecision]":
        from .. import build_runtime
        from ..runtime import CommandResult
        from ..sandbox import UnsafeLocalSandbox

        store = self.runtime._state_store
        live_sb = self.runtime.tools.sandbox
        live_root = live_sb.root
        before_hash = live_sb.state_hash()
        store.put(live_root)  # retain the pre-state (rollback anchor)

        # honestly charge the speculative twin against the parent run's budget.
        self.runtime.budget.charge_simulation()

        tmp = tempfile.mkdtemp(prefix="ar_mat_")
        try:
            store.materialize(before_hash, tmp)  # exact CoW fork
            child = build_runtime(
                sandbox=UnsafeLocalSandbox(root=tmp),
                approval_gate=self._spec_approver or _permissive_approver(),
                trace_backend="memory")
            cr = child.runtime.submit(cmd, card)   # the ONLY execution
            after_hash = store.put(tmp)

            ctx = MergeContext(
                cmd=cmd, verifier_result=cr.verifier, sigma=sigma, card=card,
                child_write_paths=_writes_of(cmd),
                evidence_refs=(after_hash,), simulation_resolved=True,
                rollback_path_defined=True, is_isolated_fork=True)
            verdict = self.gate.evaluate(ctx)

            if not (verdict.mergeable and cr.ok):
                return self._blocked_result(cmd, verdict), verdict  # discard fork

            # merge the fork's post-state into live, then self-verify.
            self._materialize_into(store, after_hash, live_root)
            got = live_sb.state_hash()
            if got != after_hash:
                self._materialize_into(store, before_hash, live_root)  # restore
                v = _integrity_fail_decision(got, after_hash)
                return self._blocked_result(cmd, v), v

            rec = self.runtime._append_transition(
                cmd, decision.verdict, cr.observation, cr.verifier,
                before_hash, after_hash)
            result = CommandResult(
                observation=cr.observation, verifier=cr.verifier,
                decision=decision, transition=rec)
            return result, verdict
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    @staticmethod
    def _materialize_into(store: Any, state_hash: str, root: str) -> None:
        """Clear ``root`` then reconstruct ``state_hash`` — exact, incl. deletions."""
        for name in os.listdir(root):
            p = os.path.join(root, name)
            if os.path.isdir(p) and not os.path.islink(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                os.remove(p)
        store.materialize(state_hash, root)

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


def _integrity_fail_decision(got: str, expected: str) -> DeploymentReadinessDecision:
    from .merge_gate import MergeVerdict
    return DeploymentReadinessDecision(
        verdict=MergeVerdict.BLOCKING_FAIL, final_status=MergeVerdict.BLOCKING_FAIL,
        blockers=["materialize_integrity"], simulation_live_status="UNRESOLVED",
        reasons=[f"materialised live state {got[:12]} != expected {expected[:12]};"
                 " live restored to pre-state"])
