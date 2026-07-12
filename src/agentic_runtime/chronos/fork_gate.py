"""F8.1 — fork-before-irreversible gate: speculative twin as HITL evidence only."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any, Optional

from ..core_types import AgentCard, CommandEnvelope, PraxisEventRecord
from ..policy import PolicyDecision

_FLAG = "AUREL_CHRONOS_FORK_GATE"


def flag_enabled() -> bool:
    return os.environ.get(_FLAG, "").strip() in ("1", "true", "TRUE", "on")


@dataclass(frozen=True)
class ForkGateEvidence:
    available: bool
    simulated: bool
    verdict: str
    outcome_preview: str
    fork_run_id: str
    reason: str
    is_escalation_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "simulated": self.simulated,
            "verdict": self.verdict,
            "outcome_preview": self.outcome_preview,
            "fork_run_id": self.fork_run_id,
            "reason": self.reason,
            "is_escalation_only": self.is_escalation_only,
        }

    def to_context_fragment(self) -> str:
        return "fork_gate|" + json.dumps(self.to_dict(), sort_keys=True)


def twin_available(runtime: Any) -> bool:
    root = getattr(getattr(runtime, "tools", None), "sandbox", None)
    live_root = getattr(root, "root", None)
    return bool(live_root)


def evaluate_fork_gate(
    cmd: CommandEnvelope,
    card: AgentCard,
    runtime: Any,
    decision: Optional[PolicyDecision] = None,
) -> ForkGateEvidence:
    """Fork+simulate an irreversible command in an ephemeral workspace twin."""
    live_root = getattr(runtime.tools.sandbox, "root", None)
    if not live_root:
        return ForkGateEvidence(
            available=False,
            simulated=False,
            verdict="",
            outcome_preview="",
            fork_run_id="",
            reason="fork gate twin UNAVAILABLE: no filesystem sandbox root",
        )

    from .. import build_runtime
    from ..dual_kernel.kernel import _permissive_approver
    from ..dual_kernel.merge_gate import MergeContext, MergeGate
    from ..dual_kernel.sigma import GovernanceStateVector, _writes_of
    from ..sandbox import UnsafeLocalSandbox

    try:
        runtime.budget.charge_simulation()
    except Exception as exc:
        return ForkGateEvidence(
            available=False,
            simulated=False,
            verdict="",
            outcome_preview="",
            fork_run_id="",
            reason=f"fork gate twin UNAVAILABLE: budget denied simulation ({exc})",
        )

    tmp = tempfile.mkdtemp(prefix="ar_fork_gate_")
    try:
        shutil.copytree(live_root, tmp, dirs_exist_ok=True)
        child = build_runtime(
            sandbox=UnsafeLocalSandbox(root=tmp),
            approval_gate=_permissive_approver(),
            trace_backend="memory",
        )
        cr = child.runtime.submit(cmd, card)
        sigma = GovernanceStateVector(
            task_id=cmd.id,
            authority_card_id=card.id,
        )
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
        verdict = MergeGate().evaluate(ctx)
        preview = _outcome_preview(cr)
        return ForkGateEvidence(
            available=True,
            simulated=True,
            verdict=verdict.final_status.value,
            outcome_preview=preview,
            fork_run_id=child.trace.run_id,
            reason="speculative fork simulation complete (evidence only)",
        )
    except Exception as exc:
        return ForkGateEvidence(
            available=False,
            simulated=False,
            verdict="",
            outcome_preview="",
            fork_run_id="",
            reason=f"fork gate twin UNAVAILABLE: simulation failed ({exc})",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def trace_fork_gate_evidence(runtime: Any, cmd: CommandEnvelope, evidence: ForkGateEvidence) -> None:
    """Append fork-gate evidence as non-authoritative praxis (escalation-only)."""
    runtime.trace.append_praxis_event(PraxisEventRecord.make(
        run_id=runtime.trace.run_id,
        agent_id=cmd.issuer_card_id,
        event_type="fork_gate_evidence",
        subject_id=cmd.id,
        summary=(
            f"simulated={evidence.simulated} verdict={evidence.verdict or 'n/a'} "
            f"fork_run={evidence.fork_run_id or 'n/a'}"
        ),
        details={
            "is_speculative": True,
            "advisory": True,
            "is_escalation_only": True,
            **evidence.to_dict(),
        },
    ))


def _outcome_preview(cr: Any) -> str:
    ok = getattr(cr, "ok", False)
    obs = getattr(cr, "observation", None)
    stderr = getattr(obs, "stderr", "") if obs is not None else ""
    stdout = getattr(obs, "stdout", "") if obs is not None else ""
    snippet = (stderr or stdout or "")[:240]
    return f"ok={ok} {snippet}".strip()
