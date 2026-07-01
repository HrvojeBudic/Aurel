"""P2.9-B Shell Exit Seal readiness / validation / evidence matrix.

Contract-only readiness layer for P2.9.6-P2.9.10. It binds P2.9-B-R1,
the retained old P2.9-B evidence overlay, P2.REVIEW-A, and P2.VSLICE-A
without upgrading preflight evidence into command execution or Shell LIVE.

This module evaluates readiness and seal evidence. It does not execute commands,
create Shell product UI, mutate sandbox/identity/policy behavior, start P2.9-C/D,
or allow P2.10.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    _CanonicalMixin,
    _hash_payload,
    _reject,
    to_canonical_json,
)

P2_9_B_PACK_ID = "P2.9-B"
P2_9_B_SECTION_ID = "P2.9"
P2_9_B_COVERED_RANGE = "P2.9.6-P2.9.10"
P2_9_B_NEXT_PACK = "P2.9-C"
P2_9_B_NEXT_RANGE = "P2.9.11-P2.9.15"
P2_9_B_REPORT_FILENAME = "P2_9_B_SHELL_EXIT_SEAL_READINESS_VALIDATION_EVIDENCE_MATRIX.md"
P2_9_B_REPORT_PATH = f"agent/reports/{P2_9_B_REPORT_FILENAME}"
P2_9_B_TEST_READINESS_REF = "tests/test_shell_exit_readiness.py"
P2_9_B_TEST_VALIDATION_REF = "tests/test_shell_exit_validation_matrix.py"
P2_9_B_TEST_MATRIX_REF = "tests/test_p29b_shell_exit_evidence_matrix.py"
P2_9_B_VALIDATION_REF = "agent/TESTS.md#P2.9-B"
P2_9_B_RESULT_VERSION = "p2_9_b_shell_exit_readiness_result.v1"

P2_9_B_R1_REPORT_PATH = (
    "agent/reports/P2_9_B_R1_ROADMAP_GRANULARITY_RECONCILIATION_P2_9_X_COVERAGE_MATRIX.md"
)
OLD_P2_9_B_OVERLAY_REPORT_PATH = (
    "agent/reports/P2_9_B_SHELL_EXIT_SEAL_VERTICAL_SLICE_EVIDENCE_CONSUMPTION.md"
)
P2_VSLICE_A_REPORT_PATH = "agent/reports/P2_VSLICE_A_GOVERNED_COMMAND_PALETTE_PREFLIGHT.md"
P2_REVIEW_A_REPORT_PATH = "agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md"
P2_9_A_REPORT_PATH = "agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md"
P2_9_A_R1_REPORT_PATH = (
    "agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md"
)
P1_ENF_A_REPORT_PATH = "agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md"
P1_ENF_D1_REPORT_PATH = (
    "agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md"
)
P1_ENF_E_REPORT_PATH = (
    "agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md"
)

P2_9_B_R1_COMMIT_REF = "0ce98df"
OLD_P2_9_B_OVERLAY_COMMIT_REF = "9082da7"
P2_VSLICE_A_COMMIT_REF = "f59a586"
P2_REVIEW_A_COMMIT_REF = "3f49dd8"
P2_9_A_COMMIT_REF = "0e8a7b4"
P2_9_A_R1_COMMIT_REF = "ab1b2ba"
P1_ENF_A_COMMIT_REF = "07c65b5"
P1_ENF_D1_COMMIT_REF = "1b85e40"
P1_ENF_E_COMMIT_REF = "b271065"

P2_9_B_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.9.6",
    "P2.9.7",
    "P2.9.8",
    "P2.9.9",
    "P2.9.10",
)

P2_9_B_WORKING_LABELS: dict[str, str] = {
    "P2.9.6": "Shell Exit Readiness Contract",
    "P2.9.7": "Shell Exit Validation Matrix",
    "P2.9.8": "Vertical Slice Evidence Binding",
    "P2.9.9": "Checkpoint-Level Seal Evidence Matrix",
    "P2.9.10": "Integration Tail / P2.9-C Handoff Contract",
}

P2_9_B_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    ".venv/bin/python -m pytest tests/test_shell_exit_readiness.py -q",
    ".venv/bin/python -m pytest tests/test_shell_exit_validation_matrix.py -q",
    ".venv/bin/python -m pytest tests/test_p29b_shell_exit_evidence_matrix.py -q",
    ".venv/bin/python -m pytest tests/test_p2_command_palette_vslice.py -q",
    ".venv/bin/python -m pytest tests/test_p2_command_preflight.py -q",
    ".venv/bin/python -m pytest tests/test_p2_vertical_slice_review.py -q",
    ".venv/bin/python -m pytest tests/test_validation_truth_gates.py tests/test_drift_gates.py -q",
    ".venv/bin/python -m pytest tests/test_golden_thread_b_governance_continuity.py -q",
    ".venv/bin/python -m mypy src/agentic_runtime",
    ".venv/bin/python -m ruff check src tests",
)

_FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "Shell LIVE",
    "full Shell product UI",
    "arbitrary command execution",
    "full command runtime",
    "full API/event bridge",
    "safe sandbox without proof",
    "P2.9-C completion",
    "P2.9-D completion",
    "P2.10+ start",
)


class ShellExitCheckpointStatus(str, Enum):
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    NOT_DONE = "NOT_DONE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    N_A_WRONG_SCOPE = "N_A_WRONG_SCOPE"


class ShellExitTruthLabel(str, Enum):
    TRACE_VERIFIED = "TRACE_VERIFIED"
    EVIDENCE_SEALED = "EVIDENCE_SEALED"
    PREFLIGHT_ONLY = "PREFLIGHT_ONLY"
    READ_ONLY = "READ_ONLY"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_DONE = "NOT_DONE"
    ERROR = "ERROR"


class ShellExitValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    UNAVAILABLE = "UNAVAILABLE"
    N_A = "N_A"


class ShellExitEvidenceKind(str, Enum):
    REPORT = "REPORT"
    TEST = "TEST"
    CODE = "CODE"
    STATE = "STATE"
    ROADMAP = "ROADMAP"
    COMMIT = "COMMIT"
    OPERATOR_PATH = "OPERATOR_PATH"


@dataclass(frozen=True)
class ShellExitEvidenceRef(_CanonicalMixin):
    ref_id: str
    kind: ShellExitEvidenceKind
    path: str
    symbol: str
    commit: str
    description: str
    truth_label: ShellExitTruthLabel
    evidence_ref_hash: str


@dataclass(frozen=True)
class ShellExitReadinessDimension(_CanonicalMixin):
    dimension_id: str
    checkpoint_id: str
    required: bool
    status: ShellExitCheckpointStatus
    truth_label: ShellExitTruthLabel
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    failure_reason: str
    notes: tuple[str, ...]
    dimension_hash: str


@dataclass(frozen=True)
class ShellExitReadinessContract(_CanonicalMixin):
    contract_id: str
    checkpoint_id: str
    working_label: str
    required_dimensions: tuple[str, ...]
    optional_dimensions: tuple[str, ...]
    allowed_evidence_kinds: tuple[ShellExitEvidenceKind, ...]
    allowed_truth_labels: tuple[ShellExitTruthLabel, ...]
    forbidden_claims: tuple[str, ...]
    dimensions: tuple[ShellExitReadinessDimension, ...]
    status: ShellExitCheckpointStatus
    truth_label: ShellExitTruthLabel
    contract_hash: str


@dataclass(frozen=True)
class ShellExitValidationCheck(_CanonicalMixin):
    check_id: str
    checkpoint_id: str
    description: str
    required: bool
    status: ShellExitValidationStatus
    truth_label: ShellExitTruthLabel
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    failure_reason: str
    notes: tuple[str, ...]
    check_hash: str


@dataclass(frozen=True)
class ShellExitValidationMatrix(_CanonicalMixin):
    matrix_id: str
    checkpoint_id: str
    checks: tuple[ShellExitValidationCheck, ...]
    required_check_ids: tuple[str, ...]
    pass_check_ids: tuple[str, ...]
    fail_check_ids: tuple[str, ...]
    not_run_check_ids: tuple[str, ...]
    unavailable_check_ids: tuple[str, ...]
    status: ShellExitCheckpointStatus
    truth_label: ShellExitTruthLabel
    matrix_hash: str


@dataclass(frozen=True)
class ShellExitEvidenceBinding(_CanonicalMixin):
    checkpoint_id: str
    source_report: str
    source_commit: str
    source_artifact: str
    source_test: str
    evidence_kind: ShellExitEvidenceKind
    truth_label: ShellExitTruthLabel
    supports_done: bool
    supports_partial: bool
    notes: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True)
class ShellExitCheckpointSeal(_CanonicalMixin):
    checkpoint_id: str
    working_label: str
    status: ShellExitCheckpointStatus
    truth_label: ShellExitTruthLabel
    readiness_dimensions: tuple[ShellExitReadinessDimension, ...]
    validation_checks: tuple[ShellExitValidationCheck, ...]
    evidence_bindings: tuple[ShellExitEvidenceBinding, ...]
    remaining_gaps: tuple[str, ...]
    next_action: str
    seal_hash: str


@dataclass(frozen=True)
class ShellExitIntegrationTail(_CanonicalMixin):
    completed_range: str
    next_pack: str
    next_range: str
    p29c_handoff_ready: bool
    p29d_handoff_ready: bool
    p210_allowed: bool
    p210_block_reason: str
    inherited_evidence_refs: tuple[ShellExitEvidenceRef, ...]
    remaining_gaps: tuple[str, ...]
    tail_hash: str


@dataclass(frozen=True)
class ShellExitP29BHandoff(_CanonicalMixin):
    handoff_id: str
    completed_pack: str
    completed_range: str
    next_pack: str
    next_range: str
    p29c_status: ShellExitCheckpointStatus
    p29d_status: ShellExitCheckpointStatus
    p210_status: ShellExitCheckpointStatus
    p210_allowed: bool
    no_p2_10_start_claim: bool
    handoff_hash: str


@dataclass(frozen=True)
class P29BSideEffectProof(_CanonicalMixin):
    shell_live_claimed: bool = False
    shell_product_ui_created: bool = False
    command_execution_implemented: bool = False
    full_command_runtime_implemented: bool = False
    api_event_bridge_runtime_implemented: bool = False
    safe_sandbox_claimed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    command_preflight_behavior_expanded: bool = False
    p2_9_c_implemented: bool = False
    p2_9_d_implemented: bool = False
    p2_10_started: bool = False
    old_p2_9_b_deleted: bool = False
    old_p2_9_b_reverted: bool = False
    roadmap_checkpoint_ids_renamed: bool = False
    roadmap_numbering_changed: bool = False


@dataclass(frozen=True)
class P29BResult(_CanonicalMixin):
    covered_range: str
    checkpoint_seals: tuple[ShellExitCheckpointSeal, ...]
    done_checkpoints: tuple[str, ...]
    partial_checkpoints: tuple[str, ...]
    not_done_checkpoints: tuple[str, ...]
    blocked_checkpoints: tuple[str, ...]
    unavailable_checkpoints: tuple[str, ...]
    integration_tail: ShellExitIntegrationTail
    handoff: ShellExitP29BHandoff
    side_effect_proof: P29BSideEffectProof
    old_p2_9_b_retained_as_overlay: bool
    p2_vslice_a_truth_label: ShellExitTruthLabel
    p29c_next: bool
    p210_allowed: bool
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


def build_p2_9_b_evidence_refs() -> tuple[ShellExitEvidenceRef, ...]:
    return (
        _evidence_ref(
            ref_id="p2_9_b_r1_coverage_matrix",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_B_R1_REPORT_PATH,
            symbol="P2.9.6 next pointer",
            commit=P2_9_B_R1_COMMIT_REF,
            description="Corrected roadmap pointer and P2.9.x coverage matrix",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="old_p2_9_b_overlay",
            kind=ShellExitEvidenceKind.REPORT,
            path=OLD_P2_9_B_OVERLAY_REPORT_PATH,
            symbol="retained evidence overlay",
            commit=OLD_P2_9_B_OVERLAY_COMMIT_REF,
            description="Old P2.9-B evidence overlay retained, not true granular completion",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="p2_vslice_a_preflight",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_VSLICE_A_REPORT_PATH,
            symbol="P2.VSLICE-A",
            commit=P2_VSLICE_A_COMMIT_REF,
            description="Governed command palette preflight vertical slice",
            truth_label=ShellExitTruthLabel.PREFLIGHT_ONLY,
        ),
        _evidence_ref(
            ref_id="p2_review_a_decision",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_REVIEW_A_REPORT_PATH,
            symbol="P2.VSLICE-A selected",
            commit=P2_REVIEW_A_COMMIT_REF,
            description="First true P2 vertical slice decision",
            truth_label=ShellExitTruthLabel.READ_ONLY,
        ),
        _evidence_ref(
            ref_id="p2_9_a_foundation",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_A_REPORT_PATH,
            symbol="P2.9.0-P2.9.5",
            commit=P2_9_A_COMMIT_REF,
            description="P2.9-A Shell Exit Seal foundation",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
        _evidence_ref(
            ref_id="p2_9_b_tests",
            kind=ShellExitEvidenceKind.TEST,
            path=P2_9_B_TEST_MATRIX_REF,
            symbol="P2.9-B focused evidence matrix tests",
            commit="pending-current-pack",
            description="Focused tests for P2.9.6-P2.9.10 readiness contracts",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
    )


def _refs_by_id(refs: tuple[ShellExitEvidenceRef, ...]) -> dict[str, ShellExitEvidenceRef]:
    return {ref.ref_id: ref for ref in refs}


def _dimension(
    *,
    dimension_id: str,
    checkpoint_id: str,
    required: bool,
    status: ShellExitCheckpointStatus,
    truth_label: ShellExitTruthLabel,
    evidence_refs: tuple[ShellExitEvidenceRef, ...],
    failure_reason: str = "",
    notes: tuple[str, ...] = (),
) -> ShellExitReadinessDimension:
    payload = {
        "dimension_id": dimension_id,
        "checkpoint_id": checkpoint_id,
        "required": required,
        "status": status,
        "truth_label": truth_label,
        "evidence_refs": evidence_refs,
        "failure_reason": failure_reason,
        "notes": notes,
    }
    return ShellExitReadinessDimension(**payload, dimension_hash=_hash_payload(payload))


def _validation_check(
    *,
    check_id: str,
    checkpoint_id: str,
    description: str,
    required: bool,
    status: ShellExitValidationStatus,
    truth_label: ShellExitTruthLabel,
    evidence_refs: tuple[ShellExitEvidenceRef, ...],
    failure_reason: str = "",
    notes: tuple[str, ...] = (),
) -> ShellExitValidationCheck:
    payload = {
        "check_id": check_id,
        "checkpoint_id": checkpoint_id,
        "description": description,
        "required": required,
        "status": status,
        "truth_label": truth_label,
        "evidence_refs": evidence_refs,
        "failure_reason": failure_reason,
        "notes": notes,
    }
    return ShellExitValidationCheck(**payload, check_hash=_hash_payload(payload))


def _binding(
    *,
    checkpoint_id: str,
    source_report: str,
    source_commit: str,
    source_artifact: str,
    source_test: str,
    evidence_kind: ShellExitEvidenceKind,
    truth_label: ShellExitTruthLabel,
    supports_done: bool,
    supports_partial: bool,
    notes: tuple[str, ...],
) -> ShellExitEvidenceBinding:
    payload = {
        "checkpoint_id": checkpoint_id,
        "source_report": source_report,
        "source_commit": source_commit,
        "source_artifact": source_artifact,
        "source_test": source_test,
        "evidence_kind": evidence_kind,
        "truth_label": truth_label,
        "supports_done": supports_done,
        "supports_partial": supports_partial,
        "notes": notes,
    }
    return ShellExitEvidenceBinding(**payload, binding_hash=_hash_payload(payload))


def _status_from_required_dimensions(
    dimensions: tuple[ShellExitReadinessDimension, ...],
) -> ShellExitCheckpointStatus:
    required = tuple(d for d in dimensions if d.required)
    if not required:
        return ShellExitCheckpointStatus.NOT_DONE
    if all(d.status is ShellExitCheckpointStatus.DONE for d in required):
        return ShellExitCheckpointStatus.DONE
    if any(d.status in {ShellExitCheckpointStatus.BLOCKED, ShellExitCheckpointStatus.UNAVAILABLE} for d in required):
        return ShellExitCheckpointStatus.BLOCKED
    if any(d.status is ShellExitCheckpointStatus.PARTIAL for d in required):
        return ShellExitCheckpointStatus.PARTIAL
    return ShellExitCheckpointStatus.NOT_DONE


def build_shell_exit_readiness_contract(
    checkpoint_id: str,
    *,
    dimensions: tuple[ShellExitReadinessDimension, ...] | None = None,
) -> ShellExitReadinessContract:
    if checkpoint_id not in P2_9_B_CHECKPOINT_IDS:
        _reject(
            "P2.9-B readiness contract only covers P2.9.6-P2.9.10",
            field="checkpoint_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    refs = _refs_by_id(build_p2_9_b_evidence_refs())
    if dimensions is None:
        truth_label = (
            ShellExitTruthLabel.PREFLIGHT_ONLY
            if checkpoint_id == "P2.9.8"
            else ShellExitTruthLabel.CONTRACT_ONLY
        )
        dimensions = (
            _dimension(
                dimension_id="ROADMAP_COVERAGE",
                checkpoint_id=checkpoint_id,
                required=True,
                status=ShellExitCheckpointStatus.DONE,
                truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
                evidence_refs=(refs["p2_9_b_r1_coverage_matrix"],),
                notes=("R1 identifies P2.9.6 as next and covers P2.9.6-P2.9.10.",),
            ),
            _dimension(
                dimension_id="REPORT_EVIDENCE",
                checkpoint_id=checkpoint_id,
                required=True,
                status=ShellExitCheckpointStatus.DONE,
                truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
                evidence_refs=(refs["old_p2_9_b_overlay"], refs["p2_9_a_foundation"]),
                notes=("Old P2.9-B is consumed as retained overlay, not direct completion.",),
            ),
            _dimension(
                dimension_id="TEST_EVIDENCE",
                checkpoint_id=checkpoint_id,
                required=True,
                status=ShellExitCheckpointStatus.DONE,
                truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
                evidence_refs=(refs["p2_9_b_tests"],),
                notes=("Focused P2.9-B readiness tests bind this contract layer.",),
            ),
            _dimension(
                dimension_id="TRUTH_LABEL",
                checkpoint_id=checkpoint_id,
                required=True,
                status=ShellExitCheckpointStatus.DONE,
                truth_label=truth_label,
                evidence_refs=(refs["p2_vslice_a_preflight"],)
                if checkpoint_id == "P2.9.8"
                else (refs["p2_9_b_r1_coverage_matrix"],),
                notes=("PREFLIGHT_ONLY remains preflight-only; CONTRACT_ONLY remains contract-only.",),
            ),
            _dimension(
                dimension_id="NO_OVERCLAIM",
                checkpoint_id=checkpoint_id,
                required=True,
                status=ShellExitCheckpointStatus.DONE,
                truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
                evidence_refs=(refs["p2_9_b_r1_coverage_matrix"], refs["old_p2_9_b_overlay"]),
                notes=("Forbidden claims are denied by contract and side-effect proof.",),
            ),
            _dimension(
                dimension_id="HANDOFF_READY",
                checkpoint_id=checkpoint_id,
                required=checkpoint_id == "P2.9.10",
                status=ShellExitCheckpointStatus.DONE,
                truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
                evidence_refs=(refs["p2_9_b_r1_coverage_matrix"],),
                notes=("P2.9-C is next; P2.10 remains blocked.",),
            ),
        )
    status = _status_from_required_dimensions(dimensions)
    payload = {
        "contract_id": f"{checkpoint_id}:shell_exit_readiness_contract",
        "checkpoint_id": checkpoint_id,
        "working_label": P2_9_B_WORKING_LABELS[checkpoint_id],
        "required_dimensions": tuple(d.dimension_id for d in dimensions if d.required),
        "optional_dimensions": tuple(d.dimension_id for d in dimensions if not d.required),
        "allowed_evidence_kinds": tuple(ShellExitEvidenceKind),
        "allowed_truth_labels": tuple(ShellExitTruthLabel),
        "forbidden_claims": _FORBIDDEN_CLAIMS,
        "dimensions": dimensions,
        "status": status,
        "truth_label": ShellExitTruthLabel.PREFLIGHT_ONLY
        if checkpoint_id == "P2.9.8"
        else ShellExitTruthLabel.CONTRACT_ONLY,
    }
    return ShellExitReadinessContract(**payload, contract_hash=_hash_payload(payload))


def _matrix_status(checks: tuple[ShellExitValidationCheck, ...]) -> ShellExitCheckpointStatus:
    required = tuple(c for c in checks if c.required)
    if any(c.status is ShellExitValidationStatus.FAIL for c in required):
        return ShellExitCheckpointStatus.BLOCKED
    if any(c.status in {ShellExitValidationStatus.NOT_RUN, ShellExitValidationStatus.UNAVAILABLE} for c in required):
        return ShellExitCheckpointStatus.PARTIAL
    if required and all(c.status is ShellExitValidationStatus.PASS for c in required):
        return ShellExitCheckpointStatus.DONE
    return ShellExitCheckpointStatus.NOT_DONE


def build_shell_exit_validation_matrix(
    checkpoint_id: str,
    *,
    checks: tuple[ShellExitValidationCheck, ...] | None = None,
) -> ShellExitValidationMatrix:
    if checkpoint_id not in P2_9_B_CHECKPOINT_IDS:
        _reject(
            "P2.9-B validation matrix only covers P2.9.6-P2.9.10",
            field="checkpoint_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    refs = _refs_by_id(build_p2_9_b_evidence_refs())
    if checks is None:
        checks = (
            _validation_check(
                check_id=f"{checkpoint_id}:required_readiness_dimensions",
                checkpoint_id=checkpoint_id,
                description="Required readiness dimensions pass before checkpoint DONE.",
                required=True,
                status=ShellExitValidationStatus.PASS,
                truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
                evidence_refs=(refs["p2_9_b_tests"],),
            ),
            _validation_check(
                check_id=f"{checkpoint_id}:truth_labels_preserved",
                checkpoint_id=checkpoint_id,
                description="PREFLIGHT_ONLY/CONTRACT_ONLY/UNAVAILABLE are not escalated.",
                required=True,
                status=ShellExitValidationStatus.PASS,
                truth_label=ShellExitTruthLabel.PREFLIGHT_ONLY
                if checkpoint_id == "P2.9.8"
                else ShellExitTruthLabel.CONTRACT_ONLY,
                evidence_refs=(refs["p2_vslice_a_preflight"], refs["old_p2_9_b_overlay"]),
            ),
            _validation_check(
                check_id=f"{checkpoint_id}:no_scope_expansion",
                checkpoint_id=checkpoint_id,
                description="No Shell LIVE, command execution, P2.9-C/D, or P2.10+ claim.",
                required=True,
                status=ShellExitValidationStatus.PASS,
                truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
                evidence_refs=(refs["p2_9_b_r1_coverage_matrix"], refs["p2_9_b_tests"]),
            ),
            _validation_check(
                check_id=f"{checkpoint_id}:safe_sandbox_not_claimed",
                checkpoint_id=checkpoint_id,
                description="SAFE_VERIFIED sandbox remains unavailable unless proven.",
                required=False,
                status=ShellExitValidationStatus.UNAVAILABLE,
                truth_label=ShellExitTruthLabel.UNAVAILABLE,
                evidence_refs=(
                    _evidence_ref(
                        ref_id="p1_enf_e_sandbox_gate",
                        kind=ShellExitEvidenceKind.REPORT,
                        path=P1_ENF_E_REPORT_PATH,
                        symbol="SAFE_VERIFIED unavailable",
                        commit=P1_ENF_E_COMMIT_REF,
                        description="Sandbox safe backend proof unavailable",
                        truth_label=ShellExitTruthLabel.UNAVAILABLE,
                    ),
                ),
                notes=("UNAVAILABLE is retained and does not become PASS.",),
            ),
        )
    pass_ids = tuple(c.check_id for c in checks if c.status is ShellExitValidationStatus.PASS)
    fail_ids = tuple(c.check_id for c in checks if c.status is ShellExitValidationStatus.FAIL)
    not_run_ids = tuple(c.check_id for c in checks if c.status is ShellExitValidationStatus.NOT_RUN)
    unavailable_ids = tuple(c.check_id for c in checks if c.status is ShellExitValidationStatus.UNAVAILABLE)
    payload = {
        "matrix_id": f"{checkpoint_id}:shell_exit_validation_matrix",
        "checkpoint_id": checkpoint_id,
        "checks": checks,
        "required_check_ids": tuple(c.check_id for c in checks if c.required),
        "pass_check_ids": pass_ids,
        "fail_check_ids": fail_ids,
        "not_run_check_ids": not_run_ids,
        "unavailable_check_ids": unavailable_ids,
        "status": _matrix_status(checks),
        "truth_label": ShellExitTruthLabel.PREFLIGHT_ONLY
        if checkpoint_id == "P2.9.8"
        else ShellExitTruthLabel.CONTRACT_ONLY,
    }
    return ShellExitValidationMatrix(**payload, matrix_hash=_hash_payload(payload))


def build_p2_vslice_a_evidence_binding() -> ShellExitEvidenceBinding:
    return _binding(
        checkpoint_id="P2.9.8",
        source_report=P2_VSLICE_A_REPORT_PATH,
        source_commit=P2_VSLICE_A_COMMIT_REF,
        source_artifact="src/agentic_runtime/aurel_shell/command_preflight.py",
        source_test="tests/test_p2_command_preflight.py",
        evidence_kind=ShellExitEvidenceKind.OPERATOR_PATH,
        truth_label=ShellExitTruthLabel.PREFLIGHT_ONLY,
        supports_done=True,
        supports_partial=False,
        notes=(
            "Supports vertical-slice evidence binding only.",
            "Does not support Shell LIVE or command execution claims.",
        ),
    )


def build_shell_exit_evidence_bindings(checkpoint_id: str) -> tuple[ShellExitEvidenceBinding, ...]:
    common = (
        _binding(
            checkpoint_id=checkpoint_id,
            source_report=P2_9_B_R1_REPORT_PATH,
            source_commit=P2_9_B_R1_COMMIT_REF,
            source_artifact="agent/ROADMAP.md",
            source_test=P2_9_B_TEST_MATRIX_REF,
            evidence_kind=ShellExitEvidenceKind.ROADMAP,
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
            supports_done=True,
            supports_partial=False,
            notes=("R1 corrected next pointer and identified P2.9.6 as next.",),
        ),
        _binding(
            checkpoint_id=checkpoint_id,
            source_report=OLD_P2_9_B_OVERLAY_REPORT_PATH,
            source_commit=OLD_P2_9_B_OVERLAY_COMMIT_REF,
            source_artifact="P2 section seal matrix",
            source_test="tests/test_p2_command_palette_vslice.py",
            evidence_kind=ShellExitEvidenceKind.REPORT,
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
            supports_done=True,
            supports_partial=False,
            notes=("Old P2.9-B is retained as overlay evidence only.",),
        ),
    )
    if checkpoint_id == "P2.9.8":
        return (*common, build_p2_vslice_a_evidence_binding())
    if checkpoint_id == "P2.9.10":
        return (
            *common,
            _binding(
                checkpoint_id=checkpoint_id,
                source_report=P2_9_B_REPORT_PATH,
                source_commit="pending-current-pack",
                source_artifact="ShellExitIntegrationTail",
                source_test=P2_9_B_TEST_MATRIX_REF,
                evidence_kind=ShellExitEvidenceKind.CODE,
                truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
                supports_done=True,
                supports_partial=False,
                notes=("Integration tail points to P2.9-C and blocks P2.10.",),
            ),
        )
    return common


def build_shell_exit_checkpoint_seal(checkpoint_id: str) -> ShellExitCheckpointSeal:
    contract = build_shell_exit_readiness_contract(checkpoint_id)
    matrix = build_shell_exit_validation_matrix(checkpoint_id)
    bindings = build_shell_exit_evidence_bindings(checkpoint_id)
    required_ok = contract.status is ShellExitCheckpointStatus.DONE
    validation_ok = matrix.status is ShellExitCheckpointStatus.DONE
    binding_ok = any(binding.supports_done for binding in bindings)
    status = (
        ShellExitCheckpointStatus.DONE
        if required_ok and validation_ok and binding_ok
        else ShellExitCheckpointStatus.PARTIAL
    )
    gaps = (
        "P2.9-C not implemented",
        "P2.9-D not implemented",
        "P2.10+ not started",
        "Shell LIVE not claimed",
        "Command execution not implemented",
        "SAFE_VERIFIED sandbox unavailable without proof",
    )
    payload = {
        "checkpoint_id": checkpoint_id,
        "working_label": P2_9_B_WORKING_LABELS[checkpoint_id],
        "status": status,
        "truth_label": ShellExitTruthLabel.PREFLIGHT_ONLY
        if checkpoint_id == "P2.9.8"
        else ShellExitTruthLabel.CONTRACT_ONLY,
        "readiness_dimensions": contract.dimensions,
        "validation_checks": matrix.checks,
        "evidence_bindings": bindings,
        "remaining_gaps": gaps,
        "next_action": "P2.9-C" if checkpoint_id == "P2.9.10" else "covered by true P2.9-B",
    }
    return ShellExitCheckpointSeal(**payload, seal_hash=_hash_payload(payload))


def build_shell_exit_integration_tail(
    checkpoint_seals: tuple[ShellExitCheckpointSeal, ...],
) -> ShellExitIntegrationTail:
    all_done = all(seal.status is ShellExitCheckpointStatus.DONE for seal in checkpoint_seals)
    refs = build_p2_9_b_evidence_refs()
    payload = {
        "completed_range": P2_9_B_COVERED_RANGE,
        "next_pack": P2_9_B_NEXT_PACK,
        "next_range": P2_9_B_NEXT_RANGE,
        "p29c_handoff_ready": all_done,
        "p29d_handoff_ready": False,
        "p210_allowed": False,
        "p210_block_reason": "P2.9-C and P2.9-D are not done; P2.10+ remains NOT STARTED.",
        "inherited_evidence_refs": refs,
        "remaining_gaps": (
            "P2.9.11-P2.9.15 remain for P2.9-C",
            "P2.9.16-P2.9.20 remain for P2.9-D",
            "No Shell LIVE, product UI, command execution, full runtime, or safe sandbox seal.",
        ),
    }
    return ShellExitIntegrationTail(**payload, tail_hash=_hash_payload(payload))


def build_shell_exit_p29b_handoff(
    integration_tail: ShellExitIntegrationTail,
) -> ShellExitP29BHandoff:
    payload = {
        "handoff_id": "p2_9_b_to_p2_9_c_handoff",
        "completed_pack": P2_9_B_PACK_ID,
        "completed_range": P2_9_B_COVERED_RANGE,
        "next_pack": integration_tail.next_pack,
        "next_range": integration_tail.next_range,
        "p29c_status": ShellExitCheckpointStatus.NOT_DONE,
        "p29d_status": ShellExitCheckpointStatus.NOT_DONE,
        "p210_status": ShellExitCheckpointStatus.NOT_DONE,
        "p210_allowed": False,
        "no_p2_10_start_claim": True,
    }
    return ShellExitP29BHandoff(**payload, handoff_hash=_hash_payload(payload))


def build_p2_9_b_shell_exit_readiness_result() -> P29BResult:
    seals = tuple(build_shell_exit_checkpoint_seal(checkpoint_id) for checkpoint_id in P2_9_B_CHECKPOINT_IDS)
    done = tuple(seal.checkpoint_id for seal in seals if seal.status is ShellExitCheckpointStatus.DONE)
    partial = tuple(seal.checkpoint_id for seal in seals if seal.status is ShellExitCheckpointStatus.PARTIAL)
    not_done = tuple(seal.checkpoint_id for seal in seals if seal.status is ShellExitCheckpointStatus.NOT_DONE)
    blocked = tuple(seal.checkpoint_id for seal in seals if seal.status is ShellExitCheckpointStatus.BLOCKED)
    unavailable = tuple(seal.checkpoint_id for seal in seals if seal.status is ShellExitCheckpointStatus.UNAVAILABLE)
    tail = build_shell_exit_integration_tail(seals)
    handoff = build_shell_exit_p29b_handoff(tail)
    side_effect_proof = P29BSideEffectProof()
    payload = {
        "covered_range": P2_9_B_COVERED_RANGE,
        "checkpoint_seals": seals,
        "done_checkpoints": done,
        "partial_checkpoints": partial,
        "not_done_checkpoints": not_done,
        "blocked_checkpoints": blocked,
        "unavailable_checkpoints": unavailable,
        "integration_tail": tail,
        "handoff": handoff,
        "side_effect_proof": side_effect_proof,
        "old_p2_9_b_retained_as_overlay": True,
        "p2_vslice_a_truth_label": ShellExitTruthLabel.PREFLIGHT_ONLY,
        "p29c_next": True,
        "p210_allowed": False,
    }
    return P29BResult(**payload, result_hash=_hash_payload(payload))


def serialize_p2_9_b_result(result: P29BResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def render_p2_9_b_coverage_rows(result: P29BResult) -> tuple[str, ...]:
    rows: list[str] = []
    for seal in result.checkpoint_seals:
        rows.append(
            "| {checkpoint} | {label} | {status} | {truth} | {evidence} | {gap} | {next_action} |".format(
                checkpoint=seal.checkpoint_id,
                label=seal.working_label,
                status=seal.status.value,
                truth=seal.truth_label.value,
                evidence=", ".join(binding.source_report for binding in seal.evidence_bindings),
                gap="; ".join(seal.remaining_gaps),
                next_action=seal.next_action,
            )
        )
    return tuple(rows)


def assert_readiness_contract_required_dimensions_gate_done(
    contract: ShellExitReadinessContract,
) -> None:
    required = tuple(d for d in contract.dimensions if d.required)
    if contract.status is ShellExitCheckpointStatus.DONE and not all(
        d.status is ShellExitCheckpointStatus.DONE for d in required
    ):
        _reject(
            "checkpoint cannot be DONE unless required readiness dimensions are DONE",
            field="status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_validation_matrix_does_not_promote_not_run_or_unavailable(
    matrix: ShellExitValidationMatrix,
) -> None:
    if any(
        check.status in {ShellExitValidationStatus.NOT_RUN, ShellExitValidationStatus.UNAVAILABLE}
        and check.check_id in matrix.pass_check_ids
        for check in matrix.checks
    ):
        _reject(
            "NOT_RUN and UNAVAILABLE validation checks must not be promoted to PASS",
            field="pass_check_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_vslice_a_binding_is_preflight_only(binding: ShellExitEvidenceBinding) -> None:
    if binding.truth_label is not ShellExitTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A binding must remain PREFLIGHT_ONLY",
            field="truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )
    forbidden = " ".join(binding.notes).lower()
    if "shell live" not in forbidden or "command execution" not in forbidden:
        _reject(
            "P2.VSLICE-A binding must explicitly deny Shell LIVE and command execution claims",
            field="notes",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_9_b_no_scope_expansion(result: P29BResult) -> None:
    proof = result.side_effect_proof
    if any(proof.to_canonical_dict().values()):
        _reject(
            "P2.9-B readiness matrix must not create runtime, UI, execution, or future-pack side effects",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_9_b_handoff_points_to_p2_9_c(result: P29BResult) -> None:
    if result.integration_tail.next_pack != "P2.9-C" or result.integration_tail.p210_allowed:
        _reject(
            "P2.9-B must hand off to P2.9-C and keep P2.10 blocked",
            field="integration_tail",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_old_p2_9_b_remains_overlay(result: P29BResult) -> None:
    if not result.old_p2_9_b_retained_as_overlay:
        _reject(
            "old P2.9-B must remain retained as evidence overlay",
            field="old_p2_9_b_retained_as_overlay",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
