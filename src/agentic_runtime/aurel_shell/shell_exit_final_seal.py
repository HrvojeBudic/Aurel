"""P2.9-D Shell Exit Seal final tail contracts.

Contract-only final tail layer for P2.9.16-P2.9.20. It consumes the
P2.9-C finalization handoff, aggregates P2.9-A/B/C/D evidence, evaluates the
P2.10 entry gate, and exposes a handoff pointer when the gate passes.

This module does not implement P2.10, execute commands, create Shell product
UI, mutate sandbox/identity/policy behavior, or upgrade P2.VSLICE-A from
PREFLIGHT_ONLY to LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)
from .shell_exit_finalization import (
    P2_9_B_IMPLEMENTATION_COMMIT_REF,
    P2_9_C_CHECKPOINT_IDS,
    P2_9_C_NEXT_PACK,
    P2_9_C_NEXT_RANGE,
    P2_9_C_REPORT_PATH,
    P2_9_C_REQUIRED_REPORTS,
    P2_9_C_WORKING_LABELS,
    P29CResult,
    ShellExitFinalizationStatus,
    build_p2_9_c_evidence_refs,
    build_p2_9_c_shell_exit_finalization_result,
)
from .shell_exit_readiness import (
    OLD_P2_9_B_OVERLAY_COMMIT_REF,
    OLD_P2_9_B_OVERLAY_REPORT_PATH,
    P1_ENF_A_COMMIT_REF,
    P1_ENF_A_REPORT_PATH,
    P1_ENF_D1_COMMIT_REF,
    P1_ENF_D1_REPORT_PATH,
    P1_ENF_E_COMMIT_REF,
    P1_ENF_E_REPORT_PATH,
    P2_9_A_COMMIT_REF,
    P2_9_A_R1_COMMIT_REF,
    P2_9_A_R1_REPORT_PATH,
    P2_9_A_REPORT_PATH,
    P2_9_B_CHECKPOINT_IDS,
    P2_9_B_R1_COMMIT_REF,
    P2_9_B_R1_REPORT_PATH,
    P2_9_B_REPORT_PATH,
    P2_REVIEW_A_COMMIT_REF,
    P2_REVIEW_A_REPORT_PATH,
    P2_VSLICE_A_COMMIT_REF,
    P2_VSLICE_A_REPORT_PATH,
    ShellExitEvidenceKind,
    ShellExitEvidenceRef,
    ShellExitTruthLabel,
)

P2_9_D_PACK_ID = "P2.9-D"
P2_9_D_SECTION_ID = "P2.9"
P2_9_D_COVERED_RANGE = "P2.9.16-P2.9.20"
P2_9_D_FULL_CHECKPOINT_RANGE = "P2.9.0-P2.9.20"
P2_9_D_NEXT_PACK_IF_GATE_PASSES = "P2.10-A"
P2_9_D_NEXT_RANGE_IF_GATE_PASSES = "P2.10-A"
P2_9_D_REPAIR_PACK = "P2.9-D-R1"
P2_9_D_REPAIR_RANGE = "P2.9.16-P2.9.20 repair"
P2_9_D_REPORT_FILENAME = "P2_9_D_SHELL_EXIT_SEAL_FINAL_TAIL.md"
P2_9_D_REPORT_PATH = f"agent/reports/{P2_9_D_REPORT_FILENAME}"
P2_9_D_RESULT_VERSION = "p2_9_d_shell_exit_final_seal_result.v1"
P2_9_D_TEST_FINAL_SEAL_REF = "tests/test_shell_exit_final_seal.py"
P2_9_D_TEST_GATE_REF = "tests/test_p29d_p210_entry_gate.py"
P2_9_D_TEST_HANDOFF_REF = "tests/test_p29d_final_tail_handoff.py"

P2_9_C_IMPLEMENTATION_COMMIT_REF = "5f4aa0b"
P2_9_C_REPORT_HASH_COMMIT_REF = "f6fbbeb"

P2_9_D_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.9.16",
    "P2.9.17",
    "P2.9.18",
    "P2.9.19",
    "P2.9.20",
)

P2_9_D_WORKING_LABELS: dict[str, str] = {
    "P2.9.16": "Final Tail Intake / P2.9-C Handoff Verification",
    "P2.9.17": "Full P2.9 Seal Aggregation Contract",
    "P2.9.18": "P2.10 Entry Gate / Blocker Resolution Matrix",
    "P2.9.19": "Final Shell Exit Seal Result Contract",
    "P2.9.20": "P2.9 Exit Seal Report / P2.10 Handoff Pointer",
}

P2_9_D_REQUIRED_REPORTS: tuple[str, ...] = (
    P2_9_A_REPORT_PATH,
    P2_9_A_R1_REPORT_PATH,
    P2_9_B_R1_REPORT_PATH,
    P2_9_B_REPORT_PATH,
    P2_9_C_REPORT_PATH,
    OLD_P2_9_B_OVERLAY_REPORT_PATH,
    P2_REVIEW_A_REPORT_PATH,
    P2_VSLICE_A_REPORT_PATH,
    P1_ENF_A_REPORT_PATH,
    P1_ENF_D1_REPORT_PATH,
    P1_ENF_E_REPORT_PATH,
)

P2_9_D_COMPLETED_RANGES: tuple[str, ...] = (
    "P2.9.0-P2.9.5",
    "P2.9.6-P2.9.10",
    "P2.9.11-P2.9.15",
    "P2.9.16-P2.9.20",
)

P2_9_D_P210_GATE_CONDITIONS: tuple[str, ...] = (
    "P2.9 complete",
    "P2.9-D done",
    "P2.10 not started",
    "no Shell LIVE overclaim",
    "no command execution overclaim",
    "no product UI overclaim",
    "safe sandbox not claimed if unavailable",
    "P2.VSLICE-A remains PREFLIGHT_ONLY",
    "full suite/coverage not claimed unless run",
    "state/report index clean",
    "final git clean",
)

P2_9_D_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    ".venv/bin/python -m pytest tests/test_shell_exit_final_seal.py -q",
    ".venv/bin/python -m pytest tests/test_p29d_p210_entry_gate.py -q",
    ".venv/bin/python -m pytest tests/test_p29d_final_tail_handoff.py -q",
    ".venv/bin/python -m pytest tests/test_shell_exit_finalization.py "
    "tests/test_p29c_release_boundaries.py tests/test_p29c_finalization_evidence_bundle.py -q",
    ".venv/bin/python -m pytest tests/test_shell_exit_readiness.py "
    "tests/test_shell_exit_validation_matrix.py tests/test_p29b_shell_exit_evidence_matrix.py -q",
    ".venv/bin/python -m pytest tests/test_p2_command_palette_vslice.py -q",
    ".venv/bin/python -m pytest tests/test_p2_command_preflight.py -q",
    ".venv/bin/python -m pytest tests/test_p2_vertical_slice_review.py -q",
    ".venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q",
    ".venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q",
    ".venv/bin/python -m mypy src/agentic_runtime",
    ".venv/bin/python -m ruff check src tests",
)


class ShellExitSectionSealStatus(str, Enum):
    P29_SEALED = "P29_SEALED"
    P29_PARTIAL = "P29_PARTIAL"
    P29_BLOCKED = "P29_BLOCKED"
    P29_REPAIR_REQUIRED = "P29_REPAIR_REQUIRED"
    P29_ERROR = "P29_ERROR"


class ShellExitP210GateStatus(str, Enum):
    P210_HANDOFF_ALLOWED = "P210_HANDOFF_ALLOWED"
    P210_BLOCKED = "P210_BLOCKED"
    P210_REPAIR_REQUIRED = "P210_REPAIR_REQUIRED"
    P210_ERROR = "P210_ERROR"


class ShellExitFinalSealStatus(str, Enum):
    FINAL_SEAL_READY = "FINAL_SEAL_READY"
    FINAL_SEAL_BLOCKED = "FINAL_SEAL_BLOCKED"
    FINAL_SEAL_PARTIAL = "FINAL_SEAL_PARTIAL"
    FINAL_SEAL_ERROR = "FINAL_SEAL_ERROR"


class ShellExitHandoffStatus(str, Enum):
    HANDOFF_READY = "HANDOFF_READY"
    HANDOFF_BLOCKED = "HANDOFF_BLOCKED"
    HANDOFF_REPAIR_REQUIRED = "HANDOFF_REPAIR_REQUIRED"
    HANDOFF_ERROR = "HANDOFF_ERROR"


@dataclass(frozen=True)
class ShellExitFinalTailIntake(_CanonicalMixin):
    source_reports: tuple[str, ...]
    source_commits: tuple[str, ...]
    p29c_result_ref: str
    p29c_handoff_ref: str
    completed_ranges: tuple[str, ...]
    not_done_ranges: tuple[str, ...]
    blocked_ranges: tuple[str, ...]
    repair_required_ranges: tuple[str, ...]
    c_ready_for_d: bool
    p210_started: bool
    intake_status: ShellExitSectionSealStatus
    failure_reason: str
    intake_hash: str


@dataclass(frozen=True)
class ShellExitP29SealAggregate(_CanonicalMixin):
    covered_section: str
    checkpoint_range: str
    completed_ranges: tuple[str, ...]
    range_results: tuple[str, ...]
    all_checkpoints_done: bool
    partial_checkpoints: tuple[str, ...]
    blocked_checkpoints: tuple[str, ...]
    repair_required_checkpoints: tuple[str, ...]
    section_status: ShellExitSectionSealStatus
    truth_labels: tuple[ShellExitTruthLabel, ...]
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    notes: tuple[str, ...]
    aggregate_hash: str


@dataclass(frozen=True)
class ShellExitP210EntryGate(_CanonicalMixin):
    gate_id: str
    required_conditions: tuple[str, ...]
    condition_results: tuple[tuple[str, bool], ...]
    blockers: tuple[str, ...]
    allowed: bool
    gate_status: ShellExitP210GateStatus
    p210_handoff_only: bool
    p210_implementation_started: bool
    notes: tuple[str, ...]
    gate_hash: str


@dataclass(frozen=True)
class ShellExitP210GateDecision(_CanonicalMixin):
    decision: ShellExitP210GateStatus
    allowed_next_pointer: str
    blocked_reason: str
    repair_pointer: str
    handoff_scope: str
    not_implementation: bool
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    decision_hash: str


@dataclass(frozen=True)
class ShellExitFinalSealResult(_CanonicalMixin):
    seal_id: str
    section: str
    final_status: ShellExitFinalSealStatus
    sealed_as: str
    not_sealed_as: tuple[str, ...]
    product_later_boundaries: tuple[str, ...]
    unavailable_capabilities: tuple[str, ...]
    preflight_only_capabilities: tuple[str, ...]
    no_overclaim_proofs: tuple[str, ...]
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    seal_hash: str


@dataclass(frozen=True)
class ShellExitP29CompletionReport(_CanonicalMixin):
    completed_section: str
    completed_ranges: tuple[str, ...]
    checkpoint_statuses: tuple[str, ...]
    seal_result: ShellExitFinalSealResult
    gate_decision: ShellExitP210GateDecision
    report_path: str
    state_update: str
    next_pointer: str
    notes: tuple[str, ...]
    report_hash: str


@dataclass(frozen=True)
class ShellExitP210HandoffPointer(_CanonicalMixin):
    next_pack: str
    next_range: str
    handoff_status: ShellExitHandoffStatus
    p210_allowed: bool
    p210_started: bool
    preconditions: tuple[str, ...]
    inherited_evidence: tuple[ShellExitEvidenceRef, ...]
    warnings: tuple[str, ...]
    pointer_hash: str


@dataclass(frozen=True)
class P29DSideEffectProof(_CanonicalMixin):
    p2_10_implemented: bool = False
    p2_10_started: bool = False
    p2_10_module_created: bool = False
    p2_10_tests_created: bool = False
    p2_vslice_a_behavior_changed: bool = False
    command_preflight_behavior_changed: bool = False
    arbitrary_command_execution_implemented: bool = False
    shell_product_ui_implemented: bool = False
    safe_sandbox_claimed: bool = False
    shell_live_claimed: bool = False
    product_readiness_claimed: bool = False
    roadmap_checkpoint_ids_renamed: bool = False
    roadmap_numbering_changed: bool = False
    old_p2_9_b_deleted: bool = False
    old_p2_9_b_reverted: bool = False


@dataclass(frozen=True)
class P29DResult(_CanonicalMixin):
    covered_range: str
    final_tail_intake: ShellExitFinalTailIntake
    p29_seal_aggregate: ShellExitP29SealAggregate
    p210_entry_gate: ShellExitP210EntryGate
    p210_gate_decision: ShellExitP210GateDecision
    final_seal_result: ShellExitFinalSealResult
    completion_report: ShellExitP29CompletionReport
    handoff_pointer: ShellExitP210HandoffPointer
    side_effect_proof: P29DSideEffectProof
    p29_done: bool
    p210_next: bool
    p2_vslice_a_truth_label: ShellExitTruthLabel
    result_hash: str


def _evidence_ref(
    *,
    ref_id: str,
    kind: ShellExitEvidenceKind,
    path: str,
    symbol: str,
    commit: str,
    description: str,
    truth_label: ShellExitTruthLabel,
) -> ShellExitEvidenceRef:
    payload = {
        "ref_id": ref_id,
        "kind": kind,
        "path": path,
        "symbol": symbol,
        "commit": commit,
        "description": description,
        "truth_label": truth_label,
    }
    return ShellExitEvidenceRef(**payload, evidence_ref_hash=_hash_payload(payload))


def build_p2_9_d_evidence_refs() -> tuple[ShellExitEvidenceRef, ...]:
    prior_refs = build_p2_9_c_evidence_refs()
    return (
        *prior_refs,
        _evidence_ref(
            ref_id="p2_9_c_finalization_report",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_C_REPORT_PATH,
            symbol="P2.9.11-P2.9.15 DONE / C_READY_FOR_D",
            commit=P2_9_C_IMPLEMENTATION_COMMIT_REF,
            description="P2.9-C finalization evidence and P2.9-D handoff",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
        _evidence_ref(
            ref_id="p2_9_c_report_hash_commit",
            kind=ShellExitEvidenceKind.COMMIT,
            path=P2_9_C_REPORT_PATH,
            symbol="P2.9-C report hash record",
            commit=P2_9_C_REPORT_HASH_COMMIT_REF,
            description="Docs commit recording P2.9-C report hash field",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="p2_9_d_final_tail_tests",
            kind=ShellExitEvidenceKind.TEST,
            path=P2_9_D_TEST_FINAL_SEAL_REF,
            symbol="P2.9-D focused tests",
            commit="pending-current-pack",
            description="Focused tests for P2.9-D final seal contracts",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
        _evidence_ref(
            ref_id="p2_9_d_agent_state",
            kind=ShellExitEvidenceKind.STATE,
            path="agent/STATE.md",
            symbol="P2.9-D state sync",
            commit="pending-current-pack",
            description="State/report pointer sync for P2.9-D",
            truth_label=ShellExitTruthLabel.READ_ONLY,
        ),
    )


def _refs_by_id(refs: tuple[ShellExitEvidenceRef, ...]) -> dict[str, ShellExitEvidenceRef]:
    return {ref.ref_id: ref for ref in refs}


def _p29c_ready_for_d(p29c_result: P29CResult) -> bool:
    return (
        p29c_result.decision_aggregate.sealed_checkpoints == P2_9_C_CHECKPOINT_IDS
        and p29c_result.decision_aggregate.aggregate_status is ShellExitFinalizationStatus.C_READY_FOR_D
        and p29c_result.p29d_handoff.next_pack == P2_9_C_NEXT_PACK
        and p29c_result.p29d_handoff.next_range == P2_9_C_NEXT_RANGE
        and p29c_result.p29d_handoff.p29d_handoff_ready
        and p29c_result.p29d_next
        and not p29c_result.p210_allowed
        and not p29c_result.p29d_handoff.p210_allowed
    )


def build_shell_exit_final_tail_intake(
    p29c_result: P29CResult | None = None,
    *,
    p210_started: bool = False,
) -> ShellExitFinalTailIntake:
    p29c_result = p29c_result or build_p2_9_c_shell_exit_finalization_result()
    c_ready = _p29c_ready_for_d(p29c_result)
    passed = c_ready and not p210_started
    failure_parts: list[str] = []
    if not c_ready:
        failure_parts.append("P2.9-C did not produce C_READY_FOR_D / P2.9-D handoff")
    if p210_started:
        failure_parts.append("P2.10+ already started")
    payload = {
        "source_reports": P2_9_D_REQUIRED_REPORTS,
        "source_commits": (
            P2_9_A_COMMIT_REF,
            P2_9_A_R1_COMMIT_REF,
            P2_9_B_R1_COMMIT_REF,
            P2_9_B_IMPLEMENTATION_COMMIT_REF,
            P2_9_C_IMPLEMENTATION_COMMIT_REF,
            P2_9_C_REPORT_HASH_COMMIT_REF,
            OLD_P2_9_B_OVERLAY_COMMIT_REF,
            P2_REVIEW_A_COMMIT_REF,
            P2_VSLICE_A_COMMIT_REF,
            P1_ENF_A_COMMIT_REF,
            P1_ENF_D1_COMMIT_REF,
            P1_ENF_E_COMMIT_REF,
        ),
        "p29c_result_ref": P2_9_C_REPORT_PATH,
        "p29c_handoff_ref": "P2.9-C:p29d_handoff",
        "completed_ranges": (
            "P2.9.0-P2.9.5",
            "P2.9.6-P2.9.10",
            "P2.9.11-P2.9.15",
        ),
        "not_done_ranges": () if passed else (P2_9_D_COVERED_RANGE,),
        "blocked_ranges": () if passed else (P2_9_D_COVERED_RANGE,),
        "repair_required_ranges": () if passed else (P2_9_D_COVERED_RANGE,),
        "c_ready_for_d": c_ready,
        "p210_started": p210_started,
        "intake_status": ShellExitSectionSealStatus.P29_SEALED
        if passed
        else ShellExitSectionSealStatus.P29_REPAIR_REQUIRED,
        "failure_reason": "; ".join(failure_parts),
    }
    return ShellExitFinalTailIntake(**payload, intake_hash=_hash_payload(payload))


def build_shell_exit_p29_seal_aggregate(
    intake: ShellExitFinalTailIntake | None = None,
    *,
    p29d_done: bool = True,
) -> ShellExitP29SealAggregate:
    intake = intake or build_shell_exit_final_tail_intake()
    refs = build_p2_9_d_evidence_refs()
    done = (
        intake.intake_status is ShellExitSectionSealStatus.P29_SEALED
        and p29d_done
        and not intake.p210_started
    )
    completed = P2_9_D_COMPLETED_RANGES if done else intake.completed_ranges
    blocked = () if done else P2_9_D_CHECKPOINT_IDS
    repair = () if done else P2_9_D_CHECKPOINT_IDS
    payload = {
        "covered_section": "P2.9 Shell Exit Foundation",
        "checkpoint_range": P2_9_D_FULL_CHECKPOINT_RANGE,
        "completed_ranges": completed,
        "range_results": (
            "P2.9-A / P2.9.0-P2.9.5 DONE",
            "true P2.9-B / P2.9.6-P2.9.10 DONE",
            "P2.9-C / P2.9.11-P2.9.15 DONE / C_READY_FOR_D",
            "P2.9-D / P2.9.16-P2.9.20 DONE" if done else "P2.9-D repair required",
        ),
        "all_checkpoints_done": done,
        "partial_checkpoints": (),
        "blocked_checkpoints": blocked,
        "repair_required_checkpoints": repair,
        "section_status": ShellExitSectionSealStatus.P29_SEALED
        if done
        else ShellExitSectionSealStatus.P29_REPAIR_REQUIRED,
        "truth_labels": (
            ShellExitTruthLabel.CONTRACT_ONLY,
            ShellExitTruthLabel.EVIDENCE_SEALED,
            ShellExitTruthLabel.PREFLIGHT_ONLY,
            ShellExitTruthLabel.UNAVAILABLE,
        ),
        "evidence_refs": refs,
        "notes": (
            "P2.9 is sealed only as honest Shell exit foundation.",
            "The seal does not mean Shell LIVE, command execution, safe sandbox, product readiness, full suite, or coverage.",
        ),
    }
    return ShellExitP29SealAggregate(**payload, aggregate_hash=_hash_payload(payload))


def build_shell_exit_p210_entry_gate(
    aggregate: ShellExitP29SealAggregate,
    *,
    p210_started: bool = False,
    no_shell_live_overclaim: bool = True,
    no_command_execution_overclaim: bool = True,
    no_product_ui_overclaim: bool = True,
    safe_sandbox_not_claimed_if_unavailable: bool = True,
    p2_vslice_a_remains_preflight_only: bool = True,
    full_suite_coverage_not_claimed_unless_run: bool = True,
    state_report_index_clean: bool = True,
    final_git_clean: bool = True,
) -> ShellExitP210EntryGate:
    condition_results = (
        ("P2.9 complete", aggregate.section_status is ShellExitSectionSealStatus.P29_SEALED),
        ("P2.9-D done", aggregate.all_checkpoints_done),
        ("P2.10 not started", not p210_started),
        ("no Shell LIVE overclaim", no_shell_live_overclaim),
        ("no command execution overclaim", no_command_execution_overclaim),
        ("no product UI overclaim", no_product_ui_overclaim),
        ("safe sandbox not claimed if unavailable", safe_sandbox_not_claimed_if_unavailable),
        ("P2.VSLICE-A remains PREFLIGHT_ONLY", p2_vslice_a_remains_preflight_only),
        ("full suite/coverage not claimed unless run", full_suite_coverage_not_claimed_unless_run),
        ("state/report index clean", state_report_index_clean),
        ("final git clean", final_git_clean),
    )
    blockers = tuple(name for name, passed in condition_results if not passed)
    allowed = not blockers
    payload = {
        "gate_id": "p2_9_d_p210_entry_gate",
        "required_conditions": P2_9_D_P210_GATE_CONDITIONS,
        "condition_results": condition_results,
        "blockers": blockers,
        "allowed": allowed,
        "gate_status": ShellExitP210GateStatus.P210_HANDOFF_ALLOWED
        if allowed
        else ShellExitP210GateStatus.P210_REPAIR_REQUIRED,
        "p210_handoff_only": True,
        "p210_implementation_started": p210_started,
        "notes": (
            "P2.10 gate may allow only a roadmap handoff pointer.",
            "P2.10 implementation remains false in P2.9-D.",
        ),
    }
    return ShellExitP210EntryGate(**payload, gate_hash=_hash_payload(payload))


def build_shell_exit_p210_gate_decision(
    gate: ShellExitP210EntryGate,
    evidence_refs: tuple[ShellExitEvidenceRef, ...] | None = None,
) -> ShellExitP210GateDecision:
    evidence_refs = evidence_refs or build_p2_9_d_evidence_refs()
    payload = {
        "decision": gate.gate_status,
        "allowed_next_pointer": P2_9_D_NEXT_PACK_IF_GATE_PASSES if gate.allowed else "",
        "blocked_reason": "" if gate.allowed else "; ".join(gate.blockers),
        "repair_pointer": "" if gate.allowed else P2_9_D_REPAIR_PACK,
        "handoff_scope": "roadmap pointer only; no P2.10 implementation",
        "not_implementation": True,
        "evidence_refs": evidence_refs,
    }
    return ShellExitP210GateDecision(**payload, decision_hash=_hash_payload(payload))


def build_shell_exit_final_seal_result(
    aggregate: ShellExitP29SealAggregate,
    gate: ShellExitP210EntryGate,
    evidence_refs: tuple[ShellExitEvidenceRef, ...] | None = None,
) -> ShellExitFinalSealResult:
    evidence_refs = evidence_refs or build_p2_9_d_evidence_refs()
    ready = aggregate.section_status is ShellExitSectionSealStatus.P29_SEALED and gate.allowed
    payload = {
        "seal_id": "p2_9_shell_exit_final_seal",
        "section": P2_9_D_SECTION_ID,
        "final_status": ShellExitFinalSealStatus.FINAL_SEAL_READY
        if ready
        else ShellExitFinalSealStatus.FINAL_SEAL_BLOCKED,
        "sealed_as": "honest Shell exit foundation; contract/readiness/finalization/final-tail evidence sealed",
        "not_sealed_as": (
            "Shell product LIVE",
            "full Shell product UI",
            "arbitrary command execution",
            "full command runtime",
            "full API/event bridge",
            "safe sandbox",
            "product readiness",
            "full suite PASS",
            "coverage PASS",
        ),
        "product_later_boundaries": (
            "Product UI and Shell LIVE remain future P2.10+ work.",
            "Command execution/runtime remains unavailable in this seal.",
            "P2.10 handoff pointer is not P2.10 implementation.",
        ),
        "unavailable_capabilities": (
            "Shell LIVE",
            "full Shell product UI",
            "arbitrary command execution",
            "full command runtime",
            "full API/event bridge",
            "SAFE_VERIFIED sandbox",
        ),
        "preflight_only_capabilities": ("P2.VSLICE-A governed command palette preflight",),
        "no_overclaim_proofs": (
            "P2.VSLICE-A remains PREFLIGHT_ONLY.",
            "P2.9 seal is not product readiness.",
            "P2.10+ remains not started in P2.9-D.",
            "Full suite and coverage are not claimed unless run.",
        ),
        "evidence_refs": evidence_refs,
    }
    return ShellExitFinalSealResult(**payload, seal_hash=_hash_payload(payload))


def build_shell_exit_p29_completion_report(
    aggregate: ShellExitP29SealAggregate,
    gate_decision: ShellExitP210GateDecision,
    final_seal_result: ShellExitFinalSealResult,
) -> ShellExitP29CompletionReport:
    next_pointer = (
        gate_decision.allowed_next_pointer
        if gate_decision.allowed_next_pointer
        else gate_decision.repair_pointer
    )
    checkpoint_statuses = tuple(
        f"{checkpoint}:DONE:{P2_9_D_WORKING_LABELS[checkpoint]}" for checkpoint in P2_9_D_CHECKPOINT_IDS
    )
    payload = {
        "completed_section": "P2.9",
        "completed_ranges": aggregate.completed_ranges,
        "checkpoint_statuses": checkpoint_statuses,
        "seal_result": final_seal_result,
        "gate_decision": gate_decision,
        "report_path": P2_9_D_REPORT_PATH,
        "state_update": "P2.9 sealed as honest Shell exit foundation; P2.10+ not started.",
        "next_pointer": next_pointer,
        "notes": (
            "Completion report records P2.9-D final-tail scope only.",
            "P2.10 pointer is a handoff pointer and does not create P2.10 implementation state.",
        ),
    }
    return ShellExitP29CompletionReport(**payload, report_hash=_hash_payload(payload))


def build_shell_exit_p210_handoff_pointer(
    gate: ShellExitP210EntryGate,
    evidence_refs: tuple[ShellExitEvidenceRef, ...] | None = None,
) -> ShellExitP210HandoffPointer:
    evidence_refs = evidence_refs or build_p2_9_d_evidence_refs()
    allowed = gate.allowed
    payload = {
        "next_pack": P2_9_D_NEXT_PACK_IF_GATE_PASSES if allowed else P2_9_D_REPAIR_PACK,
        "next_range": P2_9_D_NEXT_RANGE_IF_GATE_PASSES if allowed else P2_9_D_REPAIR_RANGE,
        "handoff_status": ShellExitHandoffStatus.HANDOFF_READY
        if allowed
        else ShellExitHandoffStatus.HANDOFF_REPAIR_REQUIRED,
        "p210_allowed": allowed,
        "p210_started": False,
        "preconditions": gate.required_conditions,
        "inherited_evidence": evidence_refs,
        "warnings": (
            "P2.10 handoff is not P2.10 implementation.",
            "Shell LIVE, product readiness, command execution, safe sandbox, full suite, and coverage remain unclaimed.",
        ),
    }
    return ShellExitP210HandoffPointer(**payload, pointer_hash=_hash_payload(payload))


def build_p2_9_d_shell_exit_final_seal_result(
    p29c_result: P29CResult | None = None,
    *,
    p29d_done: bool = True,
    p210_started: bool = False,
    state_report_index_clean: bool = True,
    final_git_clean: bool = True,
) -> P29DResult:
    intake = build_shell_exit_final_tail_intake(p29c_result, p210_started=p210_started)
    aggregate = build_shell_exit_p29_seal_aggregate(intake, p29d_done=p29d_done)
    gate = build_shell_exit_p210_entry_gate(
        aggregate,
        p210_started=p210_started,
        state_report_index_clean=state_report_index_clean,
        final_git_clean=final_git_clean,
    )
    refs = build_p2_9_d_evidence_refs()
    gate_decision = build_shell_exit_p210_gate_decision(gate, refs)
    final_seal = build_shell_exit_final_seal_result(aggregate, gate, refs)
    completion_report = build_shell_exit_p29_completion_report(aggregate, gate_decision, final_seal)
    handoff_pointer = build_shell_exit_p210_handoff_pointer(gate, refs)
    side_effect_proof = P29DSideEffectProof()
    payload = {
        "covered_range": P2_9_D_COVERED_RANGE,
        "final_tail_intake": intake,
        "p29_seal_aggregate": aggregate,
        "p210_entry_gate": gate,
        "p210_gate_decision": gate_decision,
        "final_seal_result": final_seal,
        "completion_report": completion_report,
        "handoff_pointer": handoff_pointer,
        "side_effect_proof": side_effect_proof,
        "p29_done": aggregate.section_status is ShellExitSectionSealStatus.P29_SEALED,
        "p210_next": handoff_pointer.next_pack == P2_9_D_NEXT_PACK_IF_GATE_PASSES,
        "p2_vslice_a_truth_label": ShellExitTruthLabel.PREFLIGHT_ONLY,
    }
    return P29DResult(**payload, result_hash=_hash_payload(payload))


def serialize_p2_9_d_result(result: P29DResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def render_p2_9_d_coverage_rows(result: P29DResult) -> tuple[str, ...]:
    rows: list[str] = []
    for checkpoint_id in P2_9_D_CHECKPOINT_IDS:
        truth_label = (
            ShellExitTruthLabel.PREFLIGHT_ONLY
            if checkpoint_id == "P2.9.19"
            else ShellExitTruthLabel.CONTRACT_ONLY
        )
        next_action = (
            P2_9_D_NEXT_PACK_IF_GATE_PASSES
            if checkpoint_id == "P2.9.20" and result.p210_entry_gate.allowed
            else "covered by P2.9-D"
        )
        rows.append(
            "| {checkpoint} | {label} | DONE | {truth} | {evidence} | {gap} | {next_action} |".format(
                checkpoint=checkpoint_id,
                label=P2_9_D_WORKING_LABELS[checkpoint_id],
                truth=truth_label.value,
                evidence=P2_9_C_REPORT_PATH,
                gap="No Shell LIVE/product/command execution/safe sandbox/full-suite/coverage claim",
                next_action=next_action,
            )
        )
    return tuple(rows)


def assert_p2_9_d_prerequisite_gate_passed(intake: ShellExitFinalTailIntake) -> None:
    if intake.intake_status is not ShellExitSectionSealStatus.P29_SEALED:
        _reject(
            "P2.9-D cannot proceed unless P2.9-C proves P2.9.11-P2.9.15 DONE and C_READY_FOR_D",
            field="intake_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_9_aggregate_sealed(aggregate: ShellExitP29SealAggregate) -> None:
    if not aggregate.all_checkpoints_done or aggregate.section_status is not ShellExitSectionSealStatus.P29_SEALED:
        _reject(
            "P2.9 can be sealed only when P2.9.0-P2.9.20 are covered as DONE/final-tail truth",
            field="p29_seal_aggregate",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p210_gate_handoff_only(result: P29DResult) -> None:
    if (
        result.p210_entry_gate.p210_implementation_started
        or result.handoff_pointer.p210_started
        or not result.p210_gate_decision.not_implementation
    ):
        _reject(
            "P2.9-D may create only a P2.10 handoff pointer, not P2.10 implementation",
            field="p210_entry_gate",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p210_gate_decision_consistent(result: P29DResult) -> None:
    if result.p210_entry_gate.allowed:
        if result.handoff_pointer.next_pack != P2_9_D_NEXT_PACK_IF_GATE_PASSES or not result.p210_next:
            _reject(
                "Passing P2.10 gate must point to P2.10-A",
                field="handoff_pointer",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )
    elif result.handoff_pointer.next_pack != P2_9_D_REPAIR_PACK:
        _reject(
            "Failing P2.10 gate must point to P2.9-D-R1 repair",
            field="handoff_pointer",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_vslice_a_remains_preflight_in_p29d(result: P29DResult) -> None:
    if result.p2_vslice_a_truth_label is not ShellExitTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A must remain PREFLIGHT_ONLY in P2.9-D",
            field="p2_vslice_a_truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_p2_9_d_no_scope_expansion(result: P29DResult) -> None:
    if any(result.side_effect_proof.to_canonical_dict().values()):
        _reject(
            "P2.9-D final tail must not create runtime, UI, command execution, P2.10, or roadmap side effects",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
