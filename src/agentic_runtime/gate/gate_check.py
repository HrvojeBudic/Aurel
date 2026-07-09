"""
gate_check.py — F3.1 governance preflight for an external executor's action.

Answers one question, read-only: *would Aurel's governance admit this
(tool, args) if an external executor proposed it?* It runs the exact same
contract + policy chain `runtime.submit` runs (contract registry → contract
input validation → policy evaluation), in the same order, over the same
evaluator objects — but it NEVER executes, charges budget, touches the sandbox,
or appends to the trace. The verdict is a **preflight, not final authorization**:
budget / sandbox / approval still apply when the action actually runs.

Fidelity comes from reuse, not re-implementation: `GateChecker.from_runtime`
binds to a live runtime's own `contracts`, `input_validator`, and `policy`, so
the gate can never drift from what `submit` would decide.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..core_types import AgentCard, CommandEnvelope, PolicyVerdict, RiskLevel
from ..external_ingress import (
    InjectionScanResult,
    SourceKind,
    TaintedContent,
    make_tainted,
    scan_for_injection,
)
from ..policy import PolicyEngine
from ..tool_contracts import ToolContractRegistry, ToolInputValidator

# Mirror of runtime._GOVERNANCE_SUBMIT_ARG_KEYS: governance-only submit args that
# are never part of a tool's contract surface. Kept local so this module stays
# light (no heavy runtime import); a seal test asserts it never drifts.
GATE_ARG_KEYS = frozenset({"_identity_invariant_signals", "_sandbox_backend_signals"})


def _contract_args(args: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in args.items() if k not in GATE_ARG_KEYS}


class GateVerdict(str, Enum):
    ALLOW = "allow"                      # contract + policy admit (preflight)
    REQUIRE_APPROVAL = "require_approval"  # policy admits only with HITL approval
    DENY = "deny"


class GatePhase(str, Enum):
    """Which chain stage produced the verdict."""

    CONTRACT_REGISTRY = "contract_registry"   # unknown / uncontracted tool
    CONTRACT_INPUT = "contract_input"         # args failed input validation
    POLICY = "policy"                         # policy denied
    ADMITTED = "admitted"                     # passed contract + policy (preflight)


@dataclass(frozen=True)
class GateCheckDecision:
    """The read-only verdict. ALLOW means 'no contract/policy objection', not
    final authorization (see ``preflight_only``)."""

    verdict: GateVerdict
    phase: GatePhase
    tool: str
    reasons: tuple[str, ...]
    risk: RiskLevel
    code: str                       # contract code on a contract denial, else ""
    provenance: TaintedContent
    injection_scan: InjectionScanResult
    preflight_only: bool = True

    @property
    def allowed(self) -> bool:
        """True only for a clean ALLOW. REQUIRE_APPROVAL and DENY are both False."""
        return self.verdict is GateVerdict.ALLOW

    @property
    def requires_approval(self) -> bool:
        return self.verdict is GateVerdict.REQUIRE_APPROVAL

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "phase": self.phase.value,
            "tool": self.tool,
            "reasons": list(self.reasons),
            "risk": self.risk.value,
            "code": self.code,
            "preflight_only": self.preflight_only,
            "provenance": self.provenance.to_dict(),
            "injection_scan": self.injection_scan.to_dict(),
        }


class GateChecker:
    """Read-only governance preflight over an existing runtime's evaluators."""

    def __init__(
        self,
        contracts: ToolContractRegistry,
        input_validator: ToolInputValidator,
        policy: PolicyEngine,
        registered_tools: set[str],
    ) -> None:
        self.contracts = contracts
        self.input_validator = input_validator
        self.policy = policy
        self.registered_tools = set(registered_tools)  # snapshot at bind time

    @classmethod
    def from_runtime(cls, runtime: Any) -> "GateChecker":
        """Bind a checker to a live runtime's governance surface (no execution).

        Accepts either an ``AgenticRuntime`` or the ``Kernel`` bundle returned by
        ``build_runtime`` (whose ``.runtime`` is the authoritative submit path).
        Reusing the same evaluator objects submit uses is what keeps the gate
        from ever drifting from the real decision.
        """
        inner = getattr(runtime, "runtime", runtime)
        return cls(
            contracts=inner.contracts,
            input_validator=inner.input_validator,
            policy=inner.policy,
            registered_tools=set(inner.tools.registered),
        )

    def check(
        self,
        *,
        card: AgentCard,
        tool: str,
        args: dict[str, Any],
        rationale: str = "",
        declared_risk: RiskLevel = RiskLevel.MEDIUM,
        expected_effect: str = "",
        origin_ref: str = "",
    ) -> GateCheckDecision:
        """Preflight a proposed action. Pure: mutates nothing, executes nothing."""
        # Provenance: the proposal came from outside → tainted, instruction-
        # ineligible, scanned advisorily (the scan is evidence, never the gate).
        proposal_text = json.dumps(
            {"tool": tool, "args": args, "rationale": rationale},
            sort_keys=True,
            default=str,
        )
        provenance = make_tainted(
            proposal_text, SourceKind.EXTERNAL_EXECUTOR, origin_ref or card.id
        )
        scan = scan_for_injection(proposal_text)

        def deny(
            phase: GatePhase, reasons: list[str], risk: RiskLevel, code: str = ""
        ) -> GateCheckDecision:
            return GateCheckDecision(
                verdict=GateVerdict.DENY,
                phase=phase,
                tool=tool,
                reasons=tuple(reasons),
                risk=risk,
                code=code,
                provenance=provenance,
                injection_scan=scan,
            )

        # ---- 0a. Contract registry — unknown / uncontracted tool. ---------- #
        contract, cres = self.contracts.resolve_for_execution(
            tool, self.registered_tools
        )
        if not cres.ok or contract is None:
            return deny(
                GatePhase.CONTRACT_REGISTRY, [cres.message], declared_risk, cres.code
            )

        # ---- 0b. Contract input validation. -------------------------------- #
        ires = self.input_validator.validate(contract, _contract_args(args))
        if not ires.ok:
            return deny(GatePhase.CONTRACT_INPUT, [ires.message], declared_risk, ires.code)

        # ---- 1. Policy — re-scores risk; may deny (capability/permission/…). #
        cmd = CommandEnvelope.make(
            issuer_card_id=card.id,
            tool=tool,
            args=args,
            rationale=rationale,
            declared_risk=declared_risk,
            expected_effect=expected_effect,
        )
        decision = self.policy.evaluate(cmd, card)
        if decision.verdict is PolicyVerdict.DENY:
            return deny(GatePhase.POLICY, list(decision.reasons), decision.risk)
        if decision.verdict is PolicyVerdict.REQUIRE_APPROVAL:
            return GateCheckDecision(
                verdict=GateVerdict.REQUIRE_APPROVAL,
                phase=GatePhase.POLICY,
                tool=tool,
                reasons=tuple(decision.reasons),
                risk=decision.risk,
                code="",
                provenance=provenance,
                injection_scan=scan,
            )

        return GateCheckDecision(
            verdict=GateVerdict.ALLOW,
            phase=GatePhase.ADMITTED,
            tool=tool,
            reasons=tuple(decision.reasons),
            risk=decision.risk,
            code="",
            provenance=provenance,
            injection_scan=scan,
        )
