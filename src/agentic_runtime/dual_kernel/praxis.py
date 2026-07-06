"""praxis.py — the execution-plane orchestrator.

Ties the dual-kernel pieces into one working primitive:

    fork()  →  execute-in-fork (real runtime + verify)  →  barrier (seal)
            →  MergeGate.evaluate  →  commit-or-discard

``execute_governed`` runs a command speculatively in a forked WorldLine, gathers
REAL evidence (the fork's verified post-state, not a claim), lets the merge gate
judge it, and merges to live state only on a PASS verdict. A rejected fork is
discarded and live state is provably untouched.

Additive: nothing here mutates ``runtime.py``. The child runtime is built via a
pluggable factory so Praxis stays decoupled from ``build_runtime``'s signature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional, TYPE_CHECKING

from ..core_types import AgentCard, CommandEnvelope, VerifierResult
from ..sandbox import SandboxBackend
from .merge_gate import DeploymentReadinessDecision, MergeContext, MergeGate
from .sigma import GovernanceStateVector, _writes_of

if TYPE_CHECKING:  # pragma: no cover
    from ..worldline import MergeResult, WorldLineForest

# (sandbox, child_run_id) -> a kernel exposing .runtime.submit / .trace.seal_run
ChildKernelFactory = Callable[[SandboxBackend, str], Any]


@dataclass
class SpeculativeOutcome:
    child_run_id: str
    decision: DeploymentReadinessDecision
    merged: bool
    child_ok: bool
    verifier_result: VerifierResult
    post_state_hash: str
    merge_result: "Optional[MergeResult]" = None

    def to_dict(self) -> dict:
        return {
            "child_run_id": self.child_run_id,
            "merged": self.merged,
            "child_ok": self.child_ok,
            "post_state_hash": self.post_state_hash,
            "decision": self.decision.to_dict(),
        }


class Praxis:
    """Execution plane. Runs governed speculative work over a WorldLineForest."""

    def __init__(
        self,
        forest: "WorldLineForest",
        *,
        trace_dir: str,
        state_store: Any,
        approver: Any,
        gate: Optional[MergeGate] = None,
        child_kernel_factory: Optional[ChildKernelFactory] = None,
    ) -> None:
        self.forest = forest
        self.trace_dir = trace_dir
        self.state_store = state_store
        self.approver = approver
        self.gate = gate or MergeGate()
        self._child_factory = child_kernel_factory or self._default_child_factory

    def _default_child_factory(self, sandbox: SandboxBackend, run_id: str) -> Any:
        from .. import build_runtime  # lazy: avoids import-time coupling
        return build_runtime(
            sandbox=sandbox,
            approval_gate=self.approver,
            trace_backend="persistent",
            trace_dir=self.trace_dir,
            trace_run_id=run_id,
            retain_states=True,
            state_store=self.state_store,
        )

    def execute_governed(
        self,
        *,
        parent_run_id: str,
        entry_hash: str,
        cmd: CommandEnvelope,
        card: AgentCard,
        sigma: GovernanceStateVector,
        sandbox_factory: Optional[Callable[[str], SandboxBackend]] = None,
    ) -> SpeculativeOutcome:
        """Fork → speculate → gate → commit-or-discard. Real evidence, no mocks."""
        from ..sandbox import UnsafeLocalSandbox

        factory = sandbox_factory or (lambda p: UnsafeLocalSandbox(root=p))

        # 1. fork a fresh worldline from the parent's chosen point (O(1) CoW).
        fork = self.forest.fork(parent_run_id, entry_hash, sandbox_factory=factory)

        # 2. execute IN the fork through a real runtime (executes + verifies).
        kernel = self._child_factory(fork.sandbox, fork.child_run_id)
        cr = kernel.runtime.submit(cmd, card)
        # 3. barrier: seal the child run — nothing has touched live state yet.
        kernel.trace.seal_run("completed" if cr.ok else "failed")

        post_hash = cr.transition.entry_hash if cr.transition is not None else ""
        evidence = (post_hash,) if post_hash else ()

        # 4. gather REAL evidence into a merge context.
        ctx = MergeContext(
            cmd=cmd,
            verifier_result=cr.verifier,
            sigma=sigma,
            card=card,
            child_write_paths=_writes_of(cmd),
            evidence_refs=evidence,
            simulation_resolved=True,   # verify ran against the real forked state
            rollback_path_defined=True,  # the fork itself is the rollback point
            is_isolated_fork=True,
        )

        # 5. judge, then commit-or-discard. commit() merges only on PASS.
        decision = self.gate.evaluate(ctx)
        merge = self.gate.commit(decision, self.forest, parent_run_id, fork.child_run_id)

        return SpeculativeOutcome(
            child_run_id=fork.child_run_id,
            decision=decision,
            merged=merge is not None,
            child_ok=cr.ok,
            verifier_result=cr.verifier,
            post_state_hash=post_hash,
            merge_result=merge,
        )
