"""
runtime.py — The Agentic Runtime kernel.

THE central law made literal (Hrvoje §3): the entity cannot act. It hands a
CommandEnvelope to the runtime; the runtime alone decides and executes. Every
command flows through one governed pipeline:

  CommandEnvelope
    -> Policy (capability/permission/authority + risk re-score)
    -> HITL gate (if REQUIRE_APPROVAL)
    -> Budget charge
    -> Sandbox SNAPSHOT (for rollback)            [before_state_hash]
    -> Tool execution in sandbox                  [ObservationEnvelope]
    -> State Verifier (real post-state, not claim)[after_state_hash]
    -> ROLLBACK if verification fails on a write
    -> Trace ledger append (hash-chained)         [StateTransitionRecord]
    -> Memory update (episodic + ephemeral)
    -> returns ObservationEnvelope + VerifierResult to the mind

Concurrency: canonical writes are serialized through a single lock so that only
one writer mutates canonical state at a time (single-threaded writes; parallel
reads happen via read-only sub-entities that never enter this write path).
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    from .state_store import StateStore

from .budget import BudgetExceeded, BudgetLedger
from .governance_enforcement import (
    GovernanceEnforcementConfig,
)
from .identity_invariant_enforcement import (
    IdentityInvariantEnforcementResult,
    IdentitySubmitWithInvariantResult,
    evaluate_identity_submit_with_invariants,
    identity_invariant_enforcement_to_artifact,
)
from .identity_submit_context import (
    IdentitySubmitContextLoader,
    IdentitySubmitPreflightResult,
    identity_submit_preflight_to_artifact,
)
from .policy_submit_influence import (
    PolicyResolverSubmitGateResult,
    evaluate_policy_resolver_submit_influence,
    policy_submit_gate_result_to_artifact,
)
from .approval import (
    ApprovalDecision,
    ApprovalOutcome,
    ApprovalPolicy,
    ApprovalReceipt,
    ApprovalRequest,
    ApprovalRequirement,
    build_preview,
)
from .core_types import (AgentCard, ApprovalReceiptRecord, CommandEnvelope,
                         MemoryTruthState, ObservationEnvelope, PolicyVerdict,
                         RiskLevel, SandboxViolationRecord, StateTransitionRecord,
                         ToolContractViolationRecord, TruthStatus,
                         VerifierResult, new_id)
from .hitl import ApprovalGate
from .memory import MemoryFabric
from .memory_bitemporal import _flag_enabled
from .memory_governance import MemoryWriteRequest
from .policy import PolicyEngine, PolicyDecision
from .policy_cards.context_binding import build_policy_resolution_context
from .policy_cards.registry import PolicyCardRegistry
from .policy_cards.resolver import resolve_policy_cards_from_registry
from .policy_cards.runtime_projection import (
    RuntimeEffectiveAction,
    RuntimePolicySnapshot,
    compute_runtime_policy_snapshot_hash,
    project_policy_resolution_against_runtime,
    shadow_projection_error_payload,
)
from .sandbox_policy import SandboxDecision, SandboxPolicy
from .sandbox_backend_gate import (
    SandboxBackendGateResult,
    evaluate_sandbox_backend_gate,
    sandbox_backend_gate_to_artifact,
    sandbox_backend_requirement_from_config,
)
from .sandbox_safety import resolve_wrapped_sandbox_backend
from .tool_contracts import (ContractValidationResult, ToolContractRegistry,
                             ToolInputValidator, ToolOutputValidator,
                             default_contract_registry)
from .tools import ToolRuntime
from .trace import TraceLedgerBackend
from .verifier import StateVerifier

_GOVERNANCE_SUBMIT_ARG_KEYS = frozenset({
    "_identity_invariant_signals",
    "_sandbox_backend_signals",
})


def _contract_args(args: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in args.items() if k not in _GOVERNANCE_SUBMIT_ARG_KEYS}


@dataclass
class CommandResult:
    observation: ObservationEnvelope
    verifier: VerifierResult
    decision: PolicyDecision
    transition: StateTransitionRecord | None
    rolled_back: bool = False
    approval_decision: ApprovalDecision | None = None
    approval_receipt: ApprovalReceipt | None = None

    @property
    def ok(self) -> bool:
        return self.observation.success and self.verifier.passed


_WRITE_TOOLS = {"edit_file", "write_file", "patch_file", "delete_file",
                "run_shell", "run_python", "run_tests",
                "mutate_protected_verification"}


class _ContextLock(Protocol):
    def __enter__(self) -> object: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> bool | None: ...


class AgenticRuntime:
    def __init__(self, tool_runtime: ToolRuntime, policy: PolicyEngine,
                 verifier: StateVerifier, trace: TraceLedgerBackend,
                 memory: MemoryFabric, approval_gate: ApprovalGate,
                 budget: BudgetLedger,
                 contracts: ToolContractRegistry | None = None,
                 approval_policy: ApprovalPolicy | None = None,
                 sandbox_policy: SandboxPolicy | None = None,
                 policy_card_registry: PolicyCardRegistry | None = None,
                 enable_policy_shadow_projection: bool = False,
                 governance_enforcement_config: GovernanceEnforcementConfig | None = None,
                 identity_context_loader: IdentitySubmitContextLoader | None = None,
                 retain_states: bool = False,
                 state_store: "StateStore | None" = None) -> None:
        self.tools = tool_runtime
        self.policy = policy
        self.verifier = verifier
        self.trace = trace
        self.memory = memory
        self.approval_gate = approval_gate
        self.budget = budget
        self.contracts = contracts or default_contract_registry()
        self.approval_policy = approval_policy or ApprovalPolicy()
        self.sandbox_policy = sandbox_policy
        self.policy_card_registry = policy_card_registry
        self.enable_policy_shadow_projection = enable_policy_shadow_projection
        self.governance_enforcement_config = (
            governance_enforcement_config or GovernanceEnforcementConfig()
        )
        self._governance_enforcement_explicit = (
            governance_enforcement_config is not None or identity_context_loader is not None
        )
        self.identity_context_loader = identity_context_loader
        self.input_validator = ToolInputValidator()
        self.output_validator = ToolOutputValidator()
        self._write_lock = threading.Lock()  # single-writer canonical state
        # M1 — content-addressed state retention (opt-in; off = zero change).
        self._retain_states = retain_states
        self._state_store = state_store
        self._initial_state_committed = False
        # A8b — live promotion driver, gated on the Track-A durable flag. Snapshot
        # the flag once so the flag-OFF path is byte-identical (the bridge is never
        # constructed or called). The bridge itself is created lazily on first use.
        self._durable_memory_enabled = _flag_enabled()
        self._memory_promotion_bridge: Any = None

    def _maybe_commit_initial_state(self, state_hash: str) -> None:
        """Once per run, persist the genesis workspace state to the CAS.

        ``state_hash`` is the pre-command state of the first submit — the run's
        initial world-state. Committing it (and recording ``initial_state_hash``
        in the trace metadata) is what later makes fork-from-genesis verifiable.
        Behind the retain flag; a no-op when off.
        """
        if not self._retain_states or self._state_store is None:
            return
        if self._initial_state_committed:
            return
        self._initial_state_committed = True
        self._state_store.put(self.tools.sandbox.root)
        setter = getattr(self.trace, "record_initial_state_hash", None)
        if setter is not None:
            setter(state_hash)

    def submit(self, cmd: CommandEnvelope, card: AgentCard) -> CommandResult:
        pre_policy_hash = self.tools.sandbox.state_hash()
        self._maybe_commit_initial_state(pre_policy_hash)

        if cmd.issuer_card_id != card.id:
            return self._issuer_mismatch_blocked(pre_policy_hash, cmd, card)

        # ---- 0. TOOL CONTRACT — INPUT (before policy/budget/execution) -- #
        contract, gate = self.contracts.resolve_for_execution(
            cmd.tool, self.tools.registered)
        if not gate.ok or contract is None:
            return self._contract_blocked(
                pre_policy_hash, cmd, gate, phase="registry", card=card)
        input_check = self.input_validator.validate(contract, _contract_args(cmd.args))
        if not input_check.ok:
            return self._contract_blocked(
                pre_policy_hash, cmd, input_check, phase="input", card=card)

        self.budget.ensure_context(
            run_id=self.trace.run_id,
            agent_id=cmd.issuer_card_id,
            intent_id=cmd.parent_intent_id or "intent_unbound",
        )
        try:
            self.budget.precheck_command(
                command_id=cmd.id,
                tool=cmd.tool,
                agent_id=cmd.issuer_card_id,
            )
        except BudgetExceeded as e:
            self._budget_blocked(pre_policy_hash, cmd, e, card=card)
            raise
        identity_submit = self._evaluate_identity_submit_with_invariants(cmd)
        if identity_submit is not None and identity_submit.should_block:
            reason = _identity_submit_block_reason(identity_submit)
            return self._governance_enforcement_blocked(
                pre_policy_hash,
                cmd,
                card,
                reason=reason,
                identity_submit=identity_submit,
            )
        sandbox_backend_gate = self._evaluate_sandbox_backend_gate(cmd)
        if sandbox_backend_gate is not None and sandbox_backend_gate.should_block:
            reason = _sandbox_backend_gate_block_reason(sandbox_backend_gate)
            return self._governance_enforcement_blocked(
                pre_policy_hash,
                cmd,
                card,
                reason=reason,
                identity_submit=identity_submit,
                sandbox_backend_gate=sandbox_backend_gate,
            )
        # ---- 1. POLICY ------------------------------------------------- #
        decision = self.policy.evaluate(cmd, card)
        if decision.verdict is PolicyVerdict.DENY:
            obs = ObservationEnvelope.make(cmd.id, success=False,
                stderr="DENIED by policy: " + "; ".join(decision.reasons))
            self._attach_submit_governance_artifacts(
                obs,
                identity_submit=identity_submit,
                sandbox_backend_gate=sandbox_backend_gate,
            )
            vres = VerifierResult(False, "policy", reason="denied")
            runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
                cmd,
                card,
                decision=decision,
                blocker_codes=("POLICY_DENY",),
            )
            self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
            rec = self._append_transition(
                cmd, decision.verdict, obs, vres, pre_policy_hash, pre_policy_hash
            )
            return CommandResult(obs, vres, decision, transition=rec)

        runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
            cmd,
            card,
            decision=decision,
        )
        policy_submit_gate = self._evaluate_policy_resolver_submit_influence(
            cmd,
            card,
            runtime_snapshot,
        )
        if policy_submit_gate is not None and policy_submit_gate.should_block:
            return self._governance_enforcement_blocked(
                pre_policy_hash,
                cmd,
                card,
                reason=policy_submit_gate.artifact.blocker_reason
                or "policy resolver submit influence failed closed",
                identity_submit=identity_submit,
                policy_submit_gate=policy_submit_gate,
                sandbox_backend_gate=sandbox_backend_gate,
            )

        # ---- 2. APPROVAL (HITL) ---------------------------------------- #
        tool_spec = self.tools.get(cmd.tool)
        requirement = self.approval_policy.resolve(cmd, decision, tool_spec)
        if requirement.auto_deny:
            return self._approval_blocked(
                pre_policy_hash, cmd, decision, requirement.reason,
                outcome=ApprovalOutcome.AUTO_DENIED,
                decided_by="approval_policy",
                card=card,
                approval_requirement=requirement,
            )

        preview = build_preview(cmd, self.tools.sandbox, tool_spec) if requirement.preview_required else None
        approval_decision: ApprovalDecision | None = None
        approval_receipt: ApprovalReceipt | None = None

        if requirement.auto_allow and not requirement.required:
            approval_request = ApprovalRequest.build(
                cmd,
                decision,
                risk_class=requirement.risk_class,
                preview=preview,
                tool_spec=tool_spec,
                context=cmd.rationale,
            )
            approval_decision = ApprovalDecision(
                request_id=approval_request.request_id,
                outcome=ApprovalOutcome.AUTO_APPROVED,
                reason=requirement.reason,
                decided_by="approval_policy",
                confirmation_level=0,
            )
            trace_rec = self._trace_approval(cmd, approval_request, approval_decision)
            approval_receipt = ApprovalReceipt.from_decision(
                approval_request,
                approval_decision,
                trace_id=trace_rec.id,
            )
        elif requirement.required or decision.verdict is PolicyVerdict.REQUIRE_APPROVAL:
            approval_request = ApprovalRequest.build(
                cmd,
                decision,
                risk_class=requirement.risk_class,
                preview=preview,
                tool_spec=tool_spec,
                confirmation_level=requirement.confirmation_level,
                strong_warning=requirement.strong_warning,
                context=cmd.rationale,
            )
            approval_decision = self.approval_gate.request(approval_request)
            trace_rec = self._trace_approval(cmd, approval_request, approval_decision)
            approval_receipt = ApprovalReceipt.from_decision(
                approval_request,
                approval_decision,
                trace_id=trace_rec.id,
            )
            if not approval_decision.approved:
                return self._approval_blocked(
                    pre_policy_hash,
                    cmd,
                    decision,
                    approval_decision.reason,
                    approval_decision=approval_decision,
                    approval_receipt=approval_receipt,
                    card=card,
                    approval_requirement=requirement,
                )

        # ---- 2b. SANDBOX PROFILE --------------------------------------- #
        sb_decision: SandboxDecision | None = None
        if self.sandbox_policy is not None:
            sb_decision = self.sandbox_policy.check_tool(
                cmd.tool, tool_spec, cmd.args)
            if not sb_decision.allowed:
                return self._sandbox_blocked(
                    pre_policy_hash,
                    cmd,
                    decision,
                    sb_decision,
                    card=card,
                    approval_requirement=requirement,
                )

        # ---- 3. BUDGET ------------------------------------------------- #
        try:
            self.budget.charge_tool(agent_id=cmd.issuer_card_id)
            self.budget.charge_sandbox_execution()
        except BudgetExceeded as e:
            self._budget_blocked(
                pre_policy_hash,
                cmd,
                e,
                card=card,
                decision=decision,
                approval_requirement=requirement,
                sandbox_decision=sb_decision,
            )
            raise

        is_write = cmd.tool in _WRITE_TOOLS
        lock: _ContextLock = self._write_lock if is_write else _NullLock()
        with lock:
            before_hash = self.tools.sandbox.state_hash()
            snap_id = self.tools.sandbox.snapshot() if is_write else before_hash

            integrity_before = None
            if self.verifier.should_check_integrity(cmd):
                integrity_before = self.verifier.capture_integrity()

            obs = self.tools.dispatch(replace(cmd, args=_contract_args(cmd.args)))
            obs = self.budget.apply_output_caps(obs)
            try:
                self.budget.charge_time(obs.duration_s)
                self.budget.account_post_execution(cmd.tool, cmd.args, obs)
            except BudgetExceeded as e:
                rollback_err = ""
                if is_write:
                    _rolled, rollback_err = self._attempt_write_rollback(snap_id)
                self._budget_blocked(
                    before_hash,
                    cmd,
                    e,
                    obs=obs,
                    rollback_error=rollback_err or None,
                    card=card,
                    decision=decision,
                    approval_requirement=requirement,
                    sandbox_decision=sb_decision,
                )
                raise

            after_hash = self.tools.sandbox.state_hash()

            # ---- 6b. TOOL CONTRACT — OUTPUT (before verified success) -- #
            assert contract is not None  # resolved at submit gate when registry gate passed
            output_check = self.output_validator.validate(contract, obs)
            if not output_check.ok:
                vres = VerifierResult(
                    False, "tool_output_contract",
                    reason=output_check.message,
                    code="OUTPUT_CONTRACT_VIOLATION",
                    evidence={"contract_code": output_check.code,
                              "arg": output_check.arg, **output_check.details})
            else:
                vres = self.verifier.verify(
                    cmd, obs, card,
                    integrity_before=integrity_before,
                    write_snapshot_id=snap_id if is_write else None,
                )

            # ---- 7. ROLLBACK on failed write -------------------------- #
            rolled_back = False
            if is_write and not vres.passed:
                rolled_back, rollback_err = self._attempt_write_rollback(snap_id)
                if rolled_back:
                    after_hash = self.tools.sandbox.state_hash()
                elif rollback_err:
                    vres = self._verifier_with_rollback_failure(vres, rollback_err)
            elif is_write and vres.passed:
                self.tools.sandbox.release_snapshot(snap_id)
                # M1 — retain the just-verified post-state in the CAS. The
                # committed hash equals `after_hash` (== the after_state_hash
                # recorded in the trace transition below). Behind the flag; the
                # ephemeral snapshot/rollback path above is untouched.
                if self._retain_states and self._state_store is not None:
                    self._state_store.put(self.tools.sandbox.root)

        # ---- 8. TRACE (hash-chained) ---------------------------------- #
        if not output_check.ok:
            self._trace_contract_violation(cmd, "output", output_check)
        runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
            cmd,
            card,
            decision=decision,
            approval_requirement=requirement,
            sandbox_decision=sb_decision,
        )
        self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
        self._attach_submit_governance_artifacts(
            obs,
            identity_submit=identity_submit,
            policy_submit_gate=policy_submit_gate,
            sandbox_backend_gate=sandbox_backend_gate,
        )
        rec = self._append_transition(
            cmd, decision.verdict, obs, vres, before_hash, after_hash
        )

        # ---- 9. MEMORY (governed: provenance + trace; P0.9) ----------- #
        try:
            self._record_command_memory(cmd, obs, vres, rec)
        except BudgetExceeded as e:
            return self._post_trace_budget_blocked(
                cmd, decision, obs, vres, rec, e,
                rolled_back=rolled_back,
                approval_decision=approval_decision,
                approval_receipt=approval_receipt,
            )

        return CommandResult(
            obs, vres, decision, transition=rec,
            rolled_back=rolled_back,
            approval_decision=approval_decision,
            approval_receipt=approval_receipt,
        )

    def _approval_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        reason: str,
        *,
        outcome: ApprovalOutcome = ApprovalOutcome.DENIED,
        decided_by: str = "approval_gate",
        approval_decision: ApprovalDecision | None = None,
        approval_receipt: ApprovalReceipt | None = None,
        card: AgentCard | None = None,
        approval_requirement: ApprovalRequirement | None = None,
    ) -> CommandResult:
        if approval_decision is None:
            approval_decision = ApprovalDecision(
                request_id=new_id("approval"),
                outcome=outcome,
                reason=reason,
                decided_by=decided_by,
            )
        obs = ObservationEnvelope.make(
            cmd.id,
            success=False,
            stderr=(f"HITL DENIED: tool '{cmd.tool}' blocked by approval "
                    f"(risk={decision.risk.value}); {reason}"),
            artifacts={
                "approval_outcome": approval_decision.outcome.value,
                "approval_reason": reason,
            },
        )
        vres = VerifierResult(
            False,
            "hitl",
            reason=f"approval required for {cmd.tool}; {reason}",
            code="HITL_DENIED",
            evidence={
                "approval_outcome": approval_decision.outcome.value,
                "decided_by": approval_decision.decided_by,
            },
        )
        if card is not None:
            runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
                cmd,
                card,
                decision=decision,
                approval_requirement=approval_requirement,
                approval_outcome=approval_decision.outcome.value,
                blocker_codes=("APPROVAL_DENIED",),
            )
            self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
        rec = self._append_transition(
            cmd, decision.verdict, obs, vres, before_hash, before_hash)
        return CommandResult(
            obs, vres, decision, transition=rec,
            approval_decision=approval_decision,
            approval_receipt=approval_receipt,
        )

    def _trace_approval(
        self,
        cmd: CommandEnvelope,
        request: ApprovalRequest,
        decision: ApprovalDecision,
    ) -> ApprovalReceiptRecord:
        preview_summary = request.preview.summary if request.preview else request.action_summary
        rec = ApprovalReceiptRecord.make(
            run_id=self.trace.run_id,
            issuer_card_id=cmd.issuer_card_id,
            request_id=request.request_id,
            receipt_id=new_id("approval_rcpt"),
            tool=cmd.tool,
            risk_class=request.risk_class.value,
            outcome=decision.outcome.value,
            reason=decision.reason,
            decided_by=decision.decided_by,
            preview_summary=preview_summary,
            approved_scope=list(request.affected_paths),
        )
        return self.trace.append_approval_receipt(rec)

    def _contract_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        check: ContractValidationResult,
        phase: str,
        card: AgentCard | None = None,
    ) -> CommandResult:
        """Input/registry contract violation: deny BEFORE policy/budget/exec."""
        self._trace_contract_violation(cmd, phase, check)
        obs = ObservationEnvelope.make(
            cmd.id, success=False,
            stderr=f"TOOL CONTRACT VIOLATION [{phase}/{check.code}]: {check.message}",
            artifacts={"contract_violation": True, "phase": phase,
                       "code": check.code})
        vres = VerifierResult(
            False, "tool_input_contract",
            reason=check.message, code="INPUT_CONTRACT_VIOLATION",
            evidence={"contract_code": check.code, "arg": check.arg,
                      "phase": phase, **check.details})
        decision = PolicyDecision(
            PolicyVerdict.DENY, RiskLevel.CRITICAL,
            [f"tool contract violation ({phase}): {check.message}"])
        if card is not None:
            runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
                cmd,
                card,
                decision=decision,
                blocker_codes=("TOOL_CONTRACT_BLOCK",),
            )
            self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
        rec = self._append_transition(
            cmd, decision.verdict, obs, vres, before_hash, before_hash)
        return CommandResult(obs, vres, decision, transition=rec)

    def _issuer_mismatch_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        card: AgentCard,
    ) -> CommandResult:
        """Reject when command issuer identity does not match the submitting card."""
        msg = (
            f"ISSUER_MISMATCH: cmd.issuer_card_id ({cmd.issuer_card_id}) "
            f"!= card.id ({card.id})"
        )
        obs = ObservationEnvelope.make(cmd.id, success=False, stderr=msg)
        vres = VerifierResult(
            False, "policy", reason="issuer_mismatch", code="ISSUER_MISMATCH")
        decision = PolicyDecision(
            PolicyVerdict.DENY, RiskLevel.CRITICAL, [msg])
        runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
            cmd,
            card,
            decision=decision,
            blocker_codes=("ISSUER_MISMATCH",),
        )
        self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
        rec = self._append_transition(
            cmd, decision.verdict, obs, vres, before_hash, before_hash)
        return CommandResult(obs, vres, decision, transition=rec)

    def _sandbox_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        sb_decision: SandboxDecision,
        *,
        card: AgentCard | None = None,
        approval_requirement: ApprovalRequirement | None = None,
    ) -> CommandResult:
        violation = sb_decision.violation
        profile = self.sandbox_policy.profile.profile_name if self.sandbox_policy else ""
        if violation:
            self.trace.append_sandbox_violation(SandboxViolationRecord.make(
                run_id=self.trace.run_id,
                issuer_card_id=cmd.issuer_card_id,
                profile_name=violation.profile_name or profile,
                tool=cmd.tool,
                attempted_action=violation.attempted_action,
                reason=violation.reason,
                attempted_path=violation.attempted_path,
                severity=violation.severity,
                details={"violation_id": violation.violation_id},
            ))
        obs = ObservationEnvelope.make(
            cmd.id,
            success=False,
            stderr=f"SANDBOX DENIED: {sb_decision.reason}",
            artifacts={
                "sandbox_violation": True,
                "profile_name": profile,
                "attempted_action": violation.attempted_action if violation else "",
                "attempted_path": violation.attempted_path if violation else "",
            },
        )
        vres = VerifierResult(
            False, "sandbox_policy",
            reason=sb_decision.reason,
            code="SANDBOX_VIOLATION",
            evidence={
                "profile_name": profile,
                "tool": cmd.tool,
            },
        )
        deny = PolicyDecision(
            PolicyVerdict.DENY, RiskLevel.HIGH,
            [f"sandbox violation: {sb_decision.reason}"],
        )
        if card is not None:
            runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
                cmd,
                card,
                decision=deny,
                approval_requirement=approval_requirement,
                sandbox_decision=sb_decision,
                blocker_codes=("SANDBOX_BLOCK",),
            )
            self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
        rec = self._append_transition(
            cmd, deny.verdict, obs, vres, before_hash, before_hash)
        return CommandResult(obs, vres, deny, transition=rec)

    def _trace_contract_violation(
        self,
        cmd: CommandEnvelope,
        phase: str,
        check: ContractValidationResult,
    ) -> None:
        self.trace.append_tool_contract_violation(
            ToolContractViolationRecord.make(
                run_id=self.trace.run_id,
                issuer_card_id=cmd.issuer_card_id,
                tool=cmd.tool,
                phase=phase,
                code=check.code,
                reason=check.message,
                arg=check.arg,
                details=check.details,
            ))

    def _record_command_memory(
        self,
        cmd: CommandEnvelope,
        obs: ObservationEnvelope,
        vres: VerifierResult,
        rec: StateTransitionRecord,
    ) -> None:
        summary = (f"{cmd.tool}({_short(cmd.args)}) -> "
                   f"{'ok' if obs.success else 'fail'}; "
                   f"verified={vres.passed} ({vres.reason})")
        self.budget.charge_memory_write()
        self.memory.request_write(MemoryWriteRequest(
            content=summary,
            proposed_truth_state=MemoryTruthState.RAW,
            writer_kind="runtime",
            created_by=cmd.issuer_card_id,
            source_run_id=self.trace.run_id,
            source_command_id=cmd.id,
            source_trace_ids=[rec.id],
        ))
        self.budget.charge_memory_write()
        self.memory.request_write(MemoryWriteRequest(
            content=summary,
            proposed_truth_state=MemoryTruthState.EPISODIC,
            writer_kind="runtime",
            created_by=cmd.issuer_card_id,
            source_run_id=self.trace.run_id,
            source_command_id=cmd.id,
            source_trace_ids=[rec.id],
            confidence=0.9 if vres.passed else 0.3,
            run_succeeded=vres.passed,
            truth_status=TruthStatus.VERIFIED if vres.passed else TruthStatus.CONTRADICTED,
            links=[rec.id],
        ))
        # A8b — live promotion. Additive and flag-gated: when the durable-memory
        # flag is OFF this branch never runs and the path above is byte-identical.
        # The bridge routes through the SAME governed funnel (request_write/promote):
        # a verified success submits/advances a governed procedure candidate; a
        # failed run promotes nothing (P0.9). Never raises into the command path.
        if self._durable_memory_enabled:
            try:
                self._observe_promotion(cmd, vres, rec)
            except Exception:  # noqa: BLE001 - promotion is advisory, never blocks a command
                pass

    def _observe_promotion(
        self,
        cmd: CommandEnvelope,
        vres: VerifierResult,
        rec: StateTransitionRecord,
    ) -> None:
        from .evaluation.memory_promotion_bridge import (MemoryCandidateBridge,
                                                         command_signature)
        if self._memory_promotion_bridge is None:
            self._memory_promotion_bridge = MemoryCandidateBridge()
        self._memory_promotion_bridge.observe(
            fabric=self.memory,
            budget=self.budget,
            signature=command_signature(cmd.tool, cmd.args),
            content=f"procedure candidate: {cmd.tool} (verified successes)",
            run_id=self.trace.run_id,
            trace_id=rec.id,
            run_succeeded=bool(vres.passed),
            created_by=cmd.issuer_card_id,
        )

    def _post_trace_budget_blocked(
        self,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        obs: ObservationEnvelope,
        vres: VerifierResult,
        rec: StateTransitionRecord,
        err: BudgetExceeded,
        *,
        rolled_back: bool,
        approval_decision: ApprovalDecision | None,
        approval_receipt: ApprovalReceipt | None,
    ) -> CommandResult:
        budget_vres = VerifierResult(
            False,
            "budget",
            reason=f"post-execution budget exceeded: {err}",
            code="BUDGET_EXCEEDED",
            evidence={"phase": "memory_write", "executed": True},
        )
        _ = rec
        return CommandResult(
            obs,
            budget_vres,
            decision,
            transition=rec,
            rolled_back=rolled_back,
            approval_decision=approval_decision,
            approval_receipt=approval_receipt,
        )

    def _attempt_write_rollback(self, snap_id: str) -> tuple[bool, str]:
        try:
            self.tools.sandbox.rollback(snap_id)
            return True, ""
        except (KeyError, NotImplementedError, OSError) as e:
            return False, str(e)

    @staticmethod
    def _verifier_with_rollback_failure(
        vres: VerifierResult,
        rollback_err: str,
    ) -> VerifierResult:
        evidence = dict(vres.evidence or {})
        evidence["rollback_error"] = rollback_err
        return VerifierResult(
            False,
            vres.verifier,
            reason=f"{vres.reason}; rollback failed: {rollback_err}",
            code="ROLLBACK_FAILED",
            evidence=evidence,
        )

    def _budget_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        err: BudgetExceeded,
        obs: ObservationEnvelope | None = None,
        rollback_error: str | None = None,
        card: AgentCard | None = None,
        decision: PolicyDecision | None = None,
        approval_requirement: ApprovalRequirement | None = None,
        sandbox_decision: SandboxDecision | None = None,
    ) -> None:
        reason = str(err)
        observation = obs or ObservationEnvelope.make(
            cmd.id,
            success=False,
            stderr=f"BUDGET EXCEEDED: {reason}",
            artifacts={"budget_exceeded": True},
        )
        observation.success = False
        observation.stderr = f"BUDGET EXCEEDED: {reason}"
        if rollback_error:
            observation.artifacts["rollback_error"] = rollback_error
        vres = VerifierResult(
            False,
            "budget",
            reason="budget exceeded",
            code="BUDGET_EXCEEDED",
        )
        if card is not None:
            runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
                cmd,
                card,
                decision=decision,
                approval_requirement=approval_requirement,
                sandbox_decision=sandbox_decision,
                blocker_codes=("BUDGET_EXCEEDED",),
            )
            self._attach_policy_shadow_projection(cmd, card, observation, runtime_snapshot)
        rec = self._append_transition(
            cmd,
            PolicyVerdict.DENY,
            observation,
            vres,
            before_hash,
            before_hash,
        )
        _ = rec

    def _evaluate_identity_submit_with_invariants(
        self,
        cmd: CommandEnvelope,
    ) -> IdentitySubmitWithInvariantResult | None:
        if not self._governance_enforcement_explicit:
            return None
        cfg = self.governance_enforcement_config
        return evaluate_identity_submit_with_invariants(
            mode=cfg.mode,
            require_identity_context=cfg.require_identity_context,
            loader=self.identity_context_loader,
            submit_metadata={"args": cmd.args},
        )

    def _evaluate_sandbox_backend_gate(
        self,
        cmd: CommandEnvelope,
    ) -> SandboxBackendGateResult | None:
        if not self._governance_enforcement_explicit:
            return None
        cfg = self.governance_enforcement_config
        requirement = sandbox_backend_requirement_from_config(
            mode=cfg.mode,
            require_safe_sandbox_backend=cfg.require_safe_sandbox_backend,
            gate_mode=None,
            submit_metadata={"args": cmd.args},
        )
        backend = resolve_wrapped_sandbox_backend(self.tools.sandbox)
        return evaluate_sandbox_backend_gate(
            mode=cfg.mode,
            backend=backend,
            requirement=requirement,
        )

    def _evaluate_policy_resolver_submit_influence(
        self,
        cmd: CommandEnvelope,
        card: AgentCard,
        runtime_snapshot: RuntimePolicySnapshot,
    ) -> PolicyResolverSubmitGateResult | None:
        if not self._governance_enforcement_explicit:
            return None
        cfg = self.governance_enforcement_config
        context = None
        if self.policy_card_registry is not None:
            try:
                context = self._build_policy_resolution_context_for_submit(
                    cmd,
                    card,
                    runtime_snapshot,
                )
            except Exception:
                context = None
        return evaluate_policy_resolver_submit_influence(
            mode=cfg.mode,
            require_policy_context=cfg.require_policy_context,
            registry=self.policy_card_registry,
            context=context,
        )

    def _attach_submit_governance_artifacts(
        self,
        obs: ObservationEnvelope,
        *,
        identity_submit: IdentitySubmitWithInvariantResult | None = None,
        identity_preflight: IdentitySubmitPreflightResult | None = None,
        identity_invariant_enforcement: IdentityInvariantEnforcementResult | None = None,
        policy_submit_gate: PolicyResolverSubmitGateResult | None = None,
        sandbox_backend_gate: SandboxBackendGateResult | None = None,
    ) -> None:
        if not self._governance_enforcement_explicit:
            return
        if not self.governance_enforcement_config.attach_submit_artifacts:
            return
        artifacts: dict[str, Any] = {
            "mode": self.governance_enforcement_config.mode.value,
            "truth_label": "ENFORCEMENT_BRIDGE",
        }
        if identity_submit is not None:
            artifacts["identity_submit_context"] = identity_submit.preflight.to_canonical_dict()
            artifacts["identity_invariant_enforcement"] = (
                identity_invariant_enforcement_to_artifact(
                    identity_submit.invariant_enforcement
                )
            )
        else:
            if identity_preflight is not None:
                artifacts["identity_submit_context"] = identity_submit_preflight_to_artifact(
                    identity_preflight
                )
            if identity_invariant_enforcement is not None:
                artifacts["identity_invariant_enforcement"] = (
                    identity_invariant_enforcement_to_artifact(
                        identity_invariant_enforcement
                    )
                )
        if policy_submit_gate is not None:
            artifacts["policy_submit_influence"] = policy_submit_gate_result_to_artifact(
                policy_submit_gate
            )
        if sandbox_backend_gate is not None:
            artifacts["sandbox_backend_gate"] = sandbox_backend_gate_to_artifact(
                sandbox_backend_gate
            )
        obs.artifacts["governance_enforcement"] = artifacts

    def _governance_enforcement_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        card: AgentCard,
        *,
        reason: str,
        identity_submit: IdentitySubmitWithInvariantResult | None = None,
        identity_preflight: IdentitySubmitPreflightResult | None = None,
        policy_submit_gate: PolicyResolverSubmitGateResult | None = None,
        sandbox_backend_gate: SandboxBackendGateResult | None = None,
    ) -> CommandResult:
        obs = ObservationEnvelope.make(
            cmd.id,
            success=False,
            stderr=f"GOVERNANCE ENFORCEMENT DENIED: {reason}",
        )
        self._attach_submit_governance_artifacts(
            obs,
            identity_submit=identity_submit,
            identity_preflight=identity_preflight,
            policy_submit_gate=policy_submit_gate,
            sandbox_backend_gate=sandbox_backend_gate,
        )
        preflight = (
            identity_submit.preflight
            if identity_submit is not None
            else identity_preflight
        )
        invariant_status = ""
        if identity_submit is not None:
            invariant_status = identity_submit.invariant_enforcement.decision.value
        vres = VerifierResult(
            False,
            "governance_enforcement",
            reason=reason,
            code="GOVERNANCE_ENFORCEMENT_DENIED",
            evidence={
                "mode": self.governance_enforcement_config.mode.value,
                "identity_status": (
                    preflight.status.value if preflight is not None else ""
                ),
                "identity_invariant_decision": invariant_status,
                "policy_status": (
                    policy_submit_gate.status.value if policy_submit_gate is not None else ""
                ),
                "sandbox_gate_decision": (
                    sandbox_backend_gate.decision.value
                    if sandbox_backend_gate is not None
                    else ""
                ),
                "sandbox_safety_class": (
                    sandbox_backend_gate.artifact.sandbox_safety_class
                    if sandbox_backend_gate is not None
                    else ""
                ),
            },
        )
        decision = PolicyDecision(
            PolicyVerdict.DENY,
            RiskLevel.CRITICAL,
            [f"governance enforcement: {reason}"],
        )
        runtime_snapshot = self._build_runtime_policy_snapshot_for_submit(
            cmd,
            card,
            decision=decision,
            blocker_codes=("GOVERNANCE_ENFORCEMENT_DENIED",),
        )
        self._attach_policy_shadow_projection(cmd, card, obs, runtime_snapshot)
        rec = self._append_transition(
            cmd,
            decision.verdict,
            obs,
            vres,
            before_hash,
            before_hash,
        )
        return CommandResult(obs, vres, decision, transition=rec)


    def _policy_shadow_enabled(self) -> bool:
        return bool(self.enable_policy_shadow_projection and self.policy_card_registry)

    def _build_policy_resolution_context_for_submit(
        self,
        cmd: CommandEnvelope,
        card: AgentCard,
        runtime_snapshot: RuntimePolicySnapshot,
    ):
        paths = tuple(
            str(value)
            for key in ("path", "file", "root", "repo_path")
            if (value := cmd.args.get(key)) is not None and isinstance(value, str)
        )
        network_targets = tuple(
            str(value)
            for key in ("url", "endpoint", "host")
            if (value := cmd.args.get(key)) is not None and isinstance(value, str)
        )
        profile = self.sandbox_policy.profile if self.sandbox_policy is not None else None
        requested_backend = profile.mode.value if profile is not None else None
        requested_filesystem_scope = None
        requested_egress = None
        if profile is not None:
            if not profile.allow_read and not profile.allow_write:
                requested_filesystem_scope = "no_filesystem"
            elif profile.allow_write:
                requested_filesystem_scope = "read_write_project"
            else:
                requested_filesystem_scope = "read_only_project"
            requested_egress = "any_egress" if profile.allow_network else "no_egress"

        decision_risk = runtime_snapshot.policy_risk or cmd.declared_risk.value
        return build_policy_resolution_context(
            {
                "agent_id": card.id,
                "command_id": cmd.id,
                "command_summary": f"{cmd.tool}: {cmd.expected_effect}",
                "requested_action": cmd.tool,
                "tool_name": cmd.tool,
                "runtime_risk": decision_risk,
                "command_class": _policy_card_command_class(cmd),
                "requested_sandbox_backend": requested_backend,
                "requested_filesystem_scope": requested_filesystem_scope,
                "requested_egress": requested_egress,
                "requested_paths": paths,
                "requested_network_targets": network_targets,
                "memory_write_intent": cmd.tool in {"write_memory", "memory_write"},
                "touches_secrets": _touches_secrets(cmd),
                "writes_files": _writes_files(cmd),
                "runs_shell": cmd.tool in {"run_shell", "run_python", "run_tests"},
                "installs_packages": _installs_packages(cmd),
                "requires_network": bool(network_targets) or cmd.tool == "network_fetch",
                "metadata": {
                    "runtime_effective_action": runtime_snapshot.runtime_effective_action.value,
                    "policy_verdict": runtime_snapshot.policy_verdict,
                    "approval_required": runtime_snapshot.approval_required,
                    "sandbox_allowed": runtime_snapshot.sandbox_allowed,
                },
            }
        )

    def _build_runtime_policy_snapshot_for_submit(
        self,
        cmd: CommandEnvelope,
        card: AgentCard,
        *,
        decision: PolicyDecision | None = None,
        approval_requirement: ApprovalRequirement | None = None,
        sandbox_decision: SandboxDecision | None = None,
        approval_outcome: str = "",
        blocker_codes: tuple[str, ...] = (),
    ) -> RuntimePolicySnapshot:
        _ = card
        action = RuntimeEffectiveAction.RUNTIME_UNKNOWN
        if blocker_codes:
            action = RuntimeEffectiveAction.RUNTIME_DENY
        elif decision is not None and decision.verdict is PolicyVerdict.DENY:
            action = RuntimeEffectiveAction.RUNTIME_DENY
        elif sandbox_decision is not None and not sandbox_decision.allowed:
            action = RuntimeEffectiveAction.RUNTIME_DENY
        elif approval_requirement is not None and approval_requirement.auto_deny:
            action = RuntimeEffectiveAction.RUNTIME_DENY
        elif (
            decision is not None
            and (
                decision.verdict is PolicyVerdict.REQUIRE_APPROVAL
                or (approval_requirement is not None and approval_requirement.required)
            )
        ):
            action = RuntimeEffectiveAction.RUNTIME_REQUIRE_APPROVAL
        elif decision is not None and decision.verdict is PolicyVerdict.ALLOW:
            action = RuntimeEffectiveAction.RUNTIME_ALLOW

        reasons = tuple(decision.reasons) if decision is not None else ()
        if approval_requirement is not None and approval_requirement.reason:
            reasons = (*reasons, approval_requirement.reason)
        if sandbox_decision is not None and sandbox_decision.reason:
            reasons = (*reasons, sandbox_decision.reason)

        return RuntimePolicySnapshot(
            runtime_effective_action=action,
            policy_verdict=decision.verdict.value if decision is not None else "",
            policy_risk=decision.risk.value if decision is not None else cmd.declared_risk.value,
            approval_required=bool(
                approval_requirement is not None
                and (approval_requirement.required or approval_requirement.auto_deny)
            ),
            approval_outcome=approval_outcome,
            sandbox_allowed=(
                sandbox_decision.allowed if sandbox_decision is not None else None
            ),
            blocker_codes=blocker_codes,
            reason_codes=tuple(sorted(set(reasons))),
            violations=blocker_codes,
            metadata={"tool": cmd.tool},
        )

    def _attach_policy_shadow_projection(
        self,
        cmd: CommandEnvelope,
        card: AgentCard,
        obs: ObservationEnvelope,
        runtime_snapshot: RuntimePolicySnapshot,
    ) -> None:
        if not self._policy_shadow_enabled():
            return
        registry = self.policy_card_registry
        context_hash = ""
        registry_hash = ""
        runtime_snapshot_hash = compute_runtime_policy_snapshot_hash(runtime_snapshot)
        try:
            if registry is None:
                return
            registry_hash = registry.canonical_hash()
            context = self._build_policy_resolution_context_for_submit(
                cmd, card, runtime_snapshot
            )
            context_hash = context.context_hash
            resolved = resolve_policy_cards_from_registry(context, registry)
            projection = project_policy_resolution_against_runtime(
                runtime_snapshot,
                resolved,
                registry_hash=registry_hash,
            )
            obs.artifacts["policy_shadow_projection"] = projection.to_canonical_dict()
        except Exception as exc:
            obs.artifacts["policy_shadow_projection"] = shadow_projection_error_payload(
                context_hash=context_hash,
                registry_hash=registry_hash,
                runtime_snapshot_hash=runtime_snapshot_hash,
                reason=type(exc).__name__,
            )

    def _append_transition(
        self,
        cmd: CommandEnvelope,
        verdict: PolicyVerdict,
        obs: ObservationEnvelope,
        vres: VerifierResult,
        before_hash: str,
        after_hash: str,
    ) -> StateTransitionRecord:
        rec = StateTransitionRecord(
            id=cmd.id.replace("cmd", "txn"),
            before_state_hash=before_hash,
            command_hash=cmd.command_hash(),
            observation_hash=obs.observation_hash(),
            after_state_hash=after_hash,
            verifier_result=vres,
            policy_verdict=verdict,
            issuer_card_id=cmd.issuer_card_id,
            parent_intent_id=cmd.parent_intent_id,
        )
        self.trace.append(rec)
        return rec



def _writes_files(cmd: CommandEnvelope) -> bool:
    return cmd.tool in {"edit_file", "write_file", "patch_file", "delete_file"}


def _touches_secrets(cmd: CommandEnvelope) -> bool:
    if cmd.args.get("touches_secrets") is True:
        return True
    for key in ("path", "file", "root", "repo_path"):
        value = cmd.args.get(key)
        if not isinstance(value, str):
            continue
        lowered = value.lower()
        if any(token in lowered for token in (".env", "secret", "credential", "token")):
            return True
    return False


def _installs_packages(cmd: CommandEnvelope) -> bool:
    if cmd.args.get("installs_packages") is True:
        return True
    raw = cmd.args.get("command") or cmd.args.get("argv") or cmd.args.get("cmd")
    if isinstance(raw, str):
        lowered = raw.lower()
        return "pip install" in lowered or "npm install" in lowered
    if isinstance(raw, list | tuple):
        joined = " ".join(str(part).lower() for part in raw)
        return "pip install" in joined or "npm install" in joined
    return False


def _policy_card_command_class(cmd: CommandEnvelope) -> str:
    if _touches_secrets(cmd):
        return "secret_touching_command"
    if cmd.tool == "delete_file" or cmd.args.get("irreversible") is True:
        return "destructive_command"
    if _installs_packages(cmd):
        return "package_install"
    if cmd.tool in {"run_shell", "run_python", "run_tests"}:
        return "shell_command"
    if cmd.tool == "network_fetch":
        return "network_command"
    if _writes_files(cmd):
        return "write_command"
    if cmd.tool in {"read_file", "list_dir", "search_text", "git_status", "git_diff"}:
        return "read_only_command"
    return "unknown_command"

def _short(args: dict) -> str:
    s = ", ".join(f"{k}={str(v)[:24]}" for k, v in list(args.items())[:3])
    return s


def _identity_submit_block_reason(result: IdentitySubmitWithInvariantResult) -> str:
    if result.preflight.should_block:
        return "identity submit context failed closed"
    artifact = result.invariant_enforcement.artifact
    if artifact.violations:
        return artifact.violations[0].message
    return "identity kernel invariant enforcement failed closed"


def _sandbox_backend_gate_block_reason(result: SandboxBackendGateResult) -> str:
    if result.artifact.violations:
        return result.artifact.violations[0].message
    if result.artifact.unavailable_reasons:
        return result.artifact.unavailable_reasons[0]
    return "sandbox backend gate failed closed"


class _NullLock:
    def __enter__(self) -> "_NullLock":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> Literal[False]:
        return False
