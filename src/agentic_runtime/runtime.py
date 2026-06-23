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
from dataclasses import dataclass
from typing import Literal, Protocol

from .budget import BudgetExceeded, BudgetLedger
from .approval import (
    ApprovalDecision,
    ApprovalOutcome,
    ApprovalPolicy,
    ApprovalReceipt,
    ApprovalRequest,
    build_preview,
)
from .core_types import (AgentCard, ApprovalReceiptRecord, CommandEnvelope,
                         MemoryTruthState, ObservationEnvelope, PolicyVerdict,
                         RiskLevel, SandboxViolationRecord, StateTransitionRecord,
                         ToolContractViolationRecord, TruthStatus,
                         VerifierResult, new_id)
from .hitl import ApprovalGate
from .memory import MemoryFabric
from .memory_governance import MemoryWriteRequest
from .policy import PolicyEngine, PolicyDecision
from .sandbox_policy import SandboxDecision, SandboxPolicy
from .tool_contracts import (ContractValidationResult, ToolContractRegistry,
                             ToolInputValidator, ToolOutputValidator,
                             default_contract_registry)
from .tools import ToolRuntime
from .trace import TraceLedgerBackend
from .verifier import StateVerifier


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
                 sandbox_policy: SandboxPolicy | None = None) -> None:
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
        self.input_validator = ToolInputValidator()
        self.output_validator = ToolOutputValidator()
        self._write_lock = threading.Lock()  # single-writer canonical state

    def submit(self, cmd: CommandEnvelope, card: AgentCard) -> CommandResult:
        pre_policy_hash = self.tools.sandbox.state_hash()

        if cmd.issuer_card_id != card.id:
            return self._issuer_mismatch_blocked(pre_policy_hash, cmd, card)

        # ---- 0. TOOL CONTRACT — INPUT (before policy/budget/execution) -- #
        contract, gate = self.contracts.resolve_for_execution(
            cmd.tool, self.tools.registered)
        if not gate.ok:
            return self._contract_blocked(pre_policy_hash, cmd, gate, phase="registry")
        input_check = self.input_validator.validate(contract, cmd.args)
        if not input_check.ok:
            return self._contract_blocked(
                pre_policy_hash, cmd, input_check, phase="input")

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
            self._budget_blocked(pre_policy_hash, cmd, e)
            raise
        # ---- 1. POLICY ------------------------------------------------- #
        decision = self.policy.evaluate(cmd, card)
        if decision.verdict is PolicyVerdict.DENY:
            obs = ObservationEnvelope.make(cmd.id, success=False,
                stderr="DENIED by policy: " + "; ".join(decision.reasons))
            vres = VerifierResult(False, "policy", reason="denied")
            rec = self._append_transition(
                cmd, decision.verdict, obs, vres, pre_policy_hash, pre_policy_hash
            )
            return CommandResult(obs, vres, decision, transition=rec)

        # ---- 2. APPROVAL (HITL) ---------------------------------------- #
        tool_spec = self.tools.get(cmd.tool)
        requirement = self.approval_policy.resolve(cmd, decision, tool_spec)
        if requirement.auto_deny:
            return self._approval_blocked(
                pre_policy_hash, cmd, decision, requirement.reason,
                outcome=ApprovalOutcome.AUTO_DENIED,
                decided_by="approval_policy",
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
                )

        # ---- 2b. SANDBOX PROFILE --------------------------------------- #
        if self.sandbox_policy is not None:
            sb_decision = self.sandbox_policy.check_tool(
                cmd.tool, tool_spec, cmd.args)
            if not sb_decision.allowed:
                return self._sandbox_blocked(
                    pre_policy_hash, cmd, decision, sb_decision)

        # ---- 3. BUDGET ------------------------------------------------- #
        try:
            self.budget.charge_tool(agent_id=cmd.issuer_card_id)
            self.budget.charge_sandbox_execution()
        except BudgetExceeded as e:
            self._budget_blocked(pre_policy_hash, cmd, e)
            raise

        is_write = cmd.tool in _WRITE_TOOLS
        lock: _ContextLock = self._write_lock if is_write else _NullLock()
        with lock:
            before_hash = self.tools.sandbox.state_hash()
            snap_id = self.tools.sandbox.snapshot() if is_write else before_hash

            integrity_before = None
            if self.verifier.should_check_integrity(cmd):
                integrity_before = self.verifier.capture_integrity()

            obs = self.tools.dispatch(cmd)
            obs = self.budget.apply_output_caps(obs)
            try:
                self.budget.charge_time(obs.duration_s)
                self.budget.account_post_execution(cmd.tool, cmd.args, obs)
            except BudgetExceeded as e:
                rollback_err = ""
                if is_write:
                    _rolled, rollback_err = self._attempt_write_rollback(snap_id)
                self._budget_blocked(
                    before_hash, cmd, e, obs=obs, rollback_error=rollback_err or None)
                raise

            after_hash = self.tools.sandbox.state_hash()

            # ---- 6b. TOOL CONTRACT — OUTPUT (before verified success) -- #
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

        # ---- 8. TRACE (hash-chained) ---------------------------------- #
        if not output_check.ok:
            self._trace_contract_violation(cmd, "output", output_check)
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
        rec = self._append_transition(
            cmd, decision.verdict, obs, vres, before_hash, before_hash)
        return CommandResult(obs, vres, decision, transition=rec)

    def _sandbox_blocked(
        self,
        before_hash: str,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        sb_decision: SandboxDecision,
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
        rec = self._append_transition(
            cmd,
            PolicyVerdict.DENY,
            observation,
            vres,
            before_hash,
            before_hash,
        )
        _ = rec

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


def _short(args: dict) -> str:
    s = ", ".join(f"{k}={str(v)[:24]}" for k, v in list(args.items())[:3])
    return s


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
