"""P5-TRACE-D DEV_FIXTURE trace substrate for the read-only trace CLI.

This module builds a small, deterministic, in-memory demonstration trace and runs
the real P5-A→P5-D pipeline over it so the ``trace`` CLI has resolver-backed data
to display. It is **DEV_FIXTURE only**: it constructs an isolated in-memory demo
ledger it owns, never touches the runtime, never calls ``runtime.submit``, never
persists, and writes no files. The demo ledger construction lives here (not in the
pure resolver/query modules) to keep those side-effect free.

The demo deliberately produces a mix of honest verdicts: a fully-corroborated
CHAIN_HEAD target that resolves TRACE_VERIFIED, and a runtime-submit-binding target
whose real P5-B evidence is incomplete and therefore resolves below verified.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core_types import (
    BudgetDecisionRecord,
    PlanningFailureRecord,
    PolicyVerdict,
    RuntimeStatusTransitionRecord,
    StateTransitionRecord,
    VerifierResult,
)
from ..trace import InMemoryTraceLedger
from .evidence_ref import EvidenceKind, EvidenceRef, make_evidence_ref
from .runtime_submit_bridge import (
    RUNTIME_SUBMIT_DOMAIN,
    RuntimeSubmitTraceBinding,
    build_runtime_submit_trace_binding,
)
from .submit_coverage import (
    build_submit_trace_coverage_audit,
    build_submit_trace_coverage_report,
)
from .trace_receipts import TraceVerificationReceipt, build_trace_verification_receipt
from .trace_refs import TraceRunRef
from .trace_resolver import (
    TraceVerificationDecision,
    resolve_chain_head,
    resolve_runtime_submit_binding,
)
from .trace_verify import (
    TraceHashVerificationRequest,
    TraceHashVerificationResult,
    TraceVerificationScope,
    verify_canonical_trace_hash_chain,
)

DEMO_RUN_ID = "run_p5_trace_d_demo"

# Evidence kinds a CHAIN_HEAD demo target requires (fully satisfied below).
_CHAIN_HEAD_REQUIRED_EVIDENCE = (
    EvidenceKind.SANDBOX_EVIDENCE.value,
    EvidenceKind.VERIFIER_EVIDENCE.value,
    EvidenceKind.TRACE_APPEND_EVIDENCE.value,
)


def _state_transition(idx: int) -> StateTransitionRecord:
    return StateTransitionRecord(
        id=f"txn_{idx}",
        before_state_hash=f"before{idx}",
        command_hash=f"cmd{idx}",
        observation_hash=f"obs{idx}",
        after_state_hash=f"after{idx}",
        verifier_result=VerifierResult(passed=True, verifier="state"),
        policy_verdict=PolicyVerdict.ALLOW,
        issuer_card_id="card1",
        parent_intent_id=f"intent{idx}",
    )


def build_demo_ledger() -> InMemoryTraceLedger:
    """Build the isolated in-memory DEV_FIXTURE demo ledger (owned by this module)."""

    ledger = InMemoryTraceLedger(run_id=DEMO_RUN_ID)
    ledger.append(_state_transition(0))
    ledger.append_planning_failure(
        PlanningFailureRecord.make("intent1", "card1", "rejected", "bad plan")
    )
    ledger.append_budget_decision(
        BudgetDecisionRecord(
            id="bud_0",
            run_id=DEMO_RUN_ID,
            intent_id="intent2",
            issuer_card_id="card1",
            metric="tokens",
            verdict="allow",
            used=1.0,
            limit=10.0,
            reason="within budget",
        )
    )
    ledger.append_status_transition(
        RuntimeStatusTransitionRecord.make(
            run_id=DEMO_RUN_ID,
            intent_id="intent3",
            issuer_card_id="card1",
            from_status="running",
            to_status="completed",
            reason_code="ok",
            message="done",
        )
    )
    return ledger


@dataclass(frozen=True)
class DemoTraceSubstrate:
    """The deterministic demo inputs and resolver decisions for the CLI."""

    trace_run_ref: TraceRunRef
    hash_result: TraceHashVerificationResult
    receipt: TraceVerificationReceipt
    runtime_submit_binding: RuntimeSubmitTraceBinding
    chain_head_evidence: tuple[EvidenceRef, ...]
    decisions: tuple[TraceVerificationDecision, ...]


def build_demo_trace_substrate() -> DemoTraceSubstrate:
    """Run the real P5-A→P5-D pipeline over the DEV_FIXTURE demo ledger."""

    from . import envelopes_from_ledger, trace_run_ref_from_ledger

    ledger = build_demo_ledger()
    run_ref = trace_run_ref_from_ledger(ledger)
    envelopes = envelopes_from_ledger(ledger, trace_run_ref=run_ref)

    request = TraceHashVerificationRequest(
        verification_request_id="vr-demo",
        trace_run_ref=run_ref,
        scope=TraceVerificationScope.FULL_CHAIN,
    )
    hash_result = verify_canonical_trace_hash_chain(request, envelopes)
    receipt = build_trace_verification_receipt(hash_result, request)

    # Fully-present, receipt-backed evidence for the CHAIN_HEAD target.
    chain_head_evidence = tuple(
        make_evidence_ref(
            evidence_kind=EvidenceKind(kind_value),
            source_domain=RUNTIME_SUBMIT_DOMAIN,
            source_object_id=f"{kind_value}@{run_ref.trace_run_id}",
            verification_receipt_id=receipt.receipt_id,
        )
        for kind_value in _CHAIN_HEAD_REQUIRED_EVIDENCE
    )

    coverage_report = build_submit_trace_coverage_report(
        build_submit_trace_coverage_audit()
    )
    runtime_submit_binding = build_runtime_submit_trace_binding(coverage_report)

    chain_head_decision = resolve_chain_head(
        trace_run_id=run_ref.trace_run_id,
        receipt=receipt,
        hash_result=hash_result,
        evidence_refs=chain_head_evidence,
        required_evidence_kinds=_CHAIN_HEAD_REQUIRED_EVIDENCE,
    )
    submit_binding_decision = resolve_runtime_submit_binding(
        runtime_submit_binding,
        receipt=receipt,
        required_evidence_kinds=(
            EvidenceKind.COMMAND_EVIDENCE.value,
            EvidenceKind.ROLLBACK_EVIDENCE.value,
            EvidenceKind.MEMORY_EVIDENCE.value,
        ),
    )

    return DemoTraceSubstrate(
        trace_run_ref=run_ref,
        hash_result=hash_result,
        receipt=receipt,
        runtime_submit_binding=runtime_submit_binding,
        chain_head_evidence=chain_head_evidence,
        decisions=(chain_head_decision, submit_binding_decision),
    )
