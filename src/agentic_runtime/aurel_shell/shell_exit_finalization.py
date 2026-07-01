"""P2.9-C Shell Exit Seal finalization contracts.

Contract-only finalization layer for P2.9.11-P2.9.15. It consumes P2.9-A and
true P2.9-B evidence, models no-release blockers, bundles evidence for P2.9-D,
and keeps P2.10 blocked.

This module does not execute commands, create Shell product UI, mutate
sandbox/identity/policy behavior, complete P2.9-D, claim final P2 exit, or
allow P2.10.
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
    P29BResult,
    ShellExitEvidenceKind,
    ShellExitEvidenceRef,
    ShellExitTruthLabel,
    build_p2_9_b_shell_exit_readiness_result,
)

P2_9_C_PACK_ID = "P2.9-C"
P2_9_C_SECTION_ID = "P2.9"
P2_9_C_COVERED_RANGE = "P2.9.11-P2.9.15"
P2_9_C_NEXT_PACK = "P2.9-D"
P2_9_C_NEXT_RANGE = "P2.9.16-P2.9.20"
P2_9_C_REPORT_FILENAME = "P2_9_C_SHELL_EXIT_SEAL_FINALIZATION.md"
P2_9_C_REPORT_PATH = f"agent/reports/{P2_9_C_REPORT_FILENAME}"
P2_9_C_TEST_FINALIZATION_REF = "tests/test_shell_exit_finalization.py"
P2_9_C_TEST_BOUNDARIES_REF = "tests/test_p29c_release_boundaries.py"
P2_9_C_TEST_BUNDLE_REF = "tests/test_p29c_finalization_evidence_bundle.py"
P2_9_C_RESULT_VERSION = "p2_9_c_shell_exit_finalization_result.v1"

P2_9_B_IMPLEMENTATION_COMMIT_REF = "161fb8b"
P2_9_B_REPORT_HASH_COMMIT_REF = "e2ded25"

P2_9_C_CHECKPOINT_IDS: tuple[str, ...] = (
    "P2.9.11",
    "P2.9.12",
    "P2.9.13",
    "P2.9.14",
    "P2.9.15",
)

P2_9_C_WORKING_LABELS: dict[str, str] = {
    "P2.9.11": "Shell Exit Finalization Intake",
    "P2.9.12": "Seal Decision Aggregation Contract",
    "P2.9.13": "Release Blocker / No-Release Boundary Matrix",
    "P2.9.14": "Finalization Evidence Bundle Contract",
    "P2.9.15": "P2.9-D Final Tail Handoff Contract",
}

P2_9_C_REQUIRED_REPORTS: tuple[str, ...] = (
    P2_9_A_REPORT_PATH,
    P2_9_A_R1_REPORT_PATH,
    P2_9_B_R1_REPORT_PATH,
    P2_9_B_REPORT_PATH,
    OLD_P2_9_B_OVERLAY_REPORT_PATH,
    P2_REVIEW_A_REPORT_PATH,
    P2_VSLICE_A_REPORT_PATH,
    P1_ENF_A_REPORT_PATH,
    P1_ENF_D1_REPORT_PATH,
    P1_ENF_E_REPORT_PATH,
)

P2_9_C_REQUIRED_P29D_DECISIONS: tuple[str, ...] = (
    "Finalize P2.9.16-P2.9.20 without claiming P2_COMPLETE prematurely.",
    "Decide whether remaining release blockers can be cleared or must stay active.",
    "Preserve P2.VSLICE-A as PREFLIGHT_ONLY unless later evidence proves otherwise.",
    "Keep P2.10 blocked until P2.9-D explicitly seals the final tail.",
)

P2_9_C_VALIDATION_COMMANDS: tuple[str, ...] = (
    ".venv/bin/python -m compileall src tests",
    ".venv/bin/python -m pytest tests/test_shell_exit_finalization.py -q",
    ".venv/bin/python -m pytest tests/test_p29c_release_boundaries.py -q",
    ".venv/bin/python -m pytest tests/test_p29c_finalization_evidence_bundle.py -q",
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


class ShellExitDecisionStatus(str, Enum):
    SEALED = "SEALED"
    PARTIAL = "PARTIAL"
    NOT_SEALED = "NOT_SEALED"
    BLOCKED = "BLOCKED"
    DEFERRED_TO_P29D = "DEFERRED_TO_P29D"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ShellExitFinalizationStatus(str, Enum):
    C_READY_FOR_D = "C_READY_FOR_D"
    C_BLOCKED = "C_BLOCKED"
    C_PARTIAL = "C_PARTIAL"
    C_ERROR = "C_ERROR"


class ShellExitBlockerSeverity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    BLOCKS_P2_10 = "BLOCKS_P2_10"
    BLOCKS_LIVE = "BLOCKS_LIVE"
    BLOCKS_COMMAND_EXECUTION = "BLOCKS_COMMAND_EXECUTION"
    BLOCKS_PRODUCT_RELEASE = "BLOCKS_PRODUCT_RELEASE"


class ShellExitBoundaryType(str, Enum):
    NO_SHELL_LIVE = "NO_SHELL_LIVE"
    NO_PRODUCT_UI_RELEASE = "NO_PRODUCT_UI_RELEASE"
    NO_COMMAND_EXECUTION = "NO_COMMAND_EXECUTION"
    NO_SAFE_SANDBOX_CLAIM = "NO_SAFE_SANDBOX_CLAIM"
    NO_P2_10_START = "NO_P2_10_START"
    NO_FULL_API_EVENT_BRIDGE_CLAIM = "NO_FULL_API_EVENT_BRIDGE_CLAIM"
    NO_FULL_SUITE_CLAIM = "NO_FULL_SUITE_CLAIM"
    NO_COVERAGE_CLAIM = "NO_COVERAGE_CLAIM"


@dataclass(frozen=True)
class ShellExitReleaseBlocker(_CanonicalMixin):
    blocker_id: str
    severity: ShellExitBlockerSeverity
    description: str
    blocks: tuple[str, ...]
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    cleared: bool
    clearance_requirement: str
    blocker_hash: str


@dataclass(frozen=True)
class ShellExitNoReleaseBoundary(_CanonicalMixin):
    boundary_id: str
    boundary_type: ShellExitBoundaryType
    description: str
    active: bool
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    forbidden_claim: str
    boundary_hash: str


@dataclass(frozen=True)
class ShellExitFinalizationIntake(_CanonicalMixin):
    source_reports: tuple[str, ...]
    source_commits: tuple[str, ...]
    completed_ranges: tuple[str, ...]
    partial_ranges: tuple[str, ...]
    not_done_ranges: tuple[str, ...]
    prior_checkpoint_seals: tuple[str, ...]
    p29b_result_ref: str
    p2_vslice_ref: str
    old_overlay_ref: str
    intake_status: ShellExitFinalizationStatus
    failure_reason: str
    intake_hash: str


@dataclass(frozen=True)
class ShellExitSealDecision(_CanonicalMixin):
    checkpoint_id: str
    working_label: str
    decision_status: ShellExitDecisionStatus
    truth_label: ShellExitTruthLabel
    evidence_refs: tuple[ShellExitEvidenceRef, ...]
    blockers: tuple[ShellExitReleaseBlocker, ...]
    boundaries: tuple[ShellExitNoReleaseBoundary, ...]
    deferred_to: str
    notes: tuple[str, ...]
    decision_hash: str


@dataclass(frozen=True)
class ShellExitSealDecisionAggregate(_CanonicalMixin):
    covered_range: str
    decisions: tuple[ShellExitSealDecision, ...]
    sealed_checkpoints: tuple[str, ...]
    partial_checkpoints: tuple[str, ...]
    blocked_checkpoints: tuple[str, ...]
    deferred_checkpoints: tuple[str, ...]
    not_sealed_checkpoints: tuple[str, ...]
    aggregate_status: ShellExitFinalizationStatus
    can_claim_p2_complete: bool
    can_start_p210: bool
    notes: tuple[str, ...]
    aggregate_hash: str


@dataclass(frozen=True)
class ShellExitFinalizationEvidenceBundle(_CanonicalMixin):
    bundle_id: str
    covered_range: str
    required_reports: tuple[str, ...]
    present_reports: tuple[str, ...]
    missing_reports: tuple[str, ...]
    commit_refs: tuple[str, ...]
    test_refs: tuple[str, ...]
    state_refs: tuple[str, ...]
    trace_or_evidence_refs: tuple[ShellExitEvidenceRef, ...]
    bundle_status: ShellExitFinalizationStatus
    notes: tuple[str, ...]
    bundle_hash: str


@dataclass(frozen=True)
class ShellExitP29DHandoff(_CanonicalMixin):
    next_pack: str
    next_range: str
    p29d_handoff_ready: bool
    p210_allowed: bool
    p210_block_reason: str
    inherited_evidence_bundle: str
    required_p29d_decisions: tuple[str, ...]
    remaining_blockers: tuple[ShellExitReleaseBlocker, ...]
    notes: tuple[str, ...]
    handoff_hash: str


@dataclass(frozen=True)
class P29CSideEffectProof(_CanonicalMixin):
    shell_live_claimed: bool = False
    shell_product_ui_created: bool = False
    command_execution_implemented: bool = False
    full_command_runtime_implemented: bool = False
    api_event_bridge_runtime_implemented: bool = False
    safe_sandbox_claimed: bool = False
    p2_vslice_a_behavior_changed: bool = False
    command_preflight_behavior_changed: bool = False
    p2_9_d_implemented: bool = False
    p2_10_started: bool = False
    final_p2_exit_claimed: bool = False
    old_p2_9_b_deleted: bool = False
    old_p2_9_b_reverted: bool = False
    roadmap_checkpoint_ids_renamed: bool = False
    roadmap_numbering_changed: bool = False


@dataclass(frozen=True)
class P29CResult(_CanonicalMixin):
    covered_range: str
    finalization_intake: ShellExitFinalizationIntake
    decision_aggregate: ShellExitSealDecisionAggregate
    release_blockers: tuple[ShellExitReleaseBlocker, ...]
    no_release_boundaries: tuple[ShellExitNoReleaseBoundary, ...]
    evidence_bundle: ShellExitFinalizationEvidenceBundle
    p29d_handoff: ShellExitP29DHandoff
    side_effect_proof: P29CSideEffectProof
    p29d_next: bool
    p210_allowed: bool
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


def build_p2_9_c_evidence_refs() -> tuple[ShellExitEvidenceRef, ...]:
    return (
        _evidence_ref(
            ref_id="p2_9_a_foundation",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_A_REPORT_PATH,
            symbol="P2.9.0-P2.9.5",
            commit=P2_9_A_COMMIT_REF,
            description="P2.9-A Shell Exit Seal foundation evidence",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
        _evidence_ref(
            ref_id="p2_9_a_r1_repair",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_A_R1_REPORT_PATH,
            symbol="P2.9-A-R1",
            commit=P2_9_A_R1_COMMIT_REF,
            description="P2.9-A evidence ref repair",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="p2_9_b_r1_coverage_matrix",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_B_R1_REPORT_PATH,
            symbol="P2.9.x coverage matrix",
            commit=P2_9_B_R1_COMMIT_REF,
            description="Roadmap granularity reconciliation input",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="true_p2_9_b_readiness_matrix",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_9_B_REPORT_PATH,
            symbol="P2.9.6-P2.9.10 DONE",
            commit=P2_9_B_IMPLEMENTATION_COMMIT_REF,
            description="True P2.9-B readiness / validation / evidence matrix",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
        _evidence_ref(
            ref_id="old_p2_9_b_overlay",
            kind=ShellExitEvidenceKind.REPORT,
            path=OLD_P2_9_B_OVERLAY_REPORT_PATH,
            symbol="retained evidence overlay",
            commit=OLD_P2_9_B_OVERLAY_COMMIT_REF,
            description="Old P2.9-B evidence overlay retained, not deleted or reverted",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
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
            ref_id="p2_vslice_a_preflight",
            kind=ShellExitEvidenceKind.REPORT,
            path=P2_VSLICE_A_REPORT_PATH,
            symbol="P2.VSLICE-A",
            commit=P2_VSLICE_A_COMMIT_REF,
            description="Governed command palette preflight vertical slice",
            truth_label=ShellExitTruthLabel.PREFLIGHT_ONLY,
        ),
        _evidence_ref(
            ref_id="p1_enf_a_enforcement_bridge",
            kind=ShellExitEvidenceKind.REPORT,
            path=P1_ENF_A_REPORT_PATH,
            symbol="P1.ENF-A",
            commit=P1_ENF_A_COMMIT_REF,
            description="Policy and identity runtime submit enforcement bridge evidence",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="p1_enf_d1_identity_invariants",
            kind=ShellExitEvidenceKind.REPORT,
            path=P1_ENF_D1_REPORT_PATH,
            symbol="P1.ENF-D1",
            commit=P1_ENF_D1_COMMIT_REF,
            description="Identity invariant enforcement evidence",
            truth_label=ShellExitTruthLabel.EVIDENCE_SEALED,
        ),
        _evidence_ref(
            ref_id="p1_enf_e_sandbox_gate",
            kind=ShellExitEvidenceKind.REPORT,
            path=P1_ENF_E_REPORT_PATH,
            symbol="SAFE_VERIFIED unavailable",
            commit=P1_ENF_E_COMMIT_REF,
            description="Sandbox backend truth gate evidence",
            truth_label=ShellExitTruthLabel.UNAVAILABLE,
        ),
        _evidence_ref(
            ref_id="p2_9_c_tests",
            kind=ShellExitEvidenceKind.TEST,
            path=P2_9_C_TEST_BUNDLE_REF,
            symbol="P2.9-C focused tests",
            commit="pending-current-pack",
            description="Focused tests for P2.9-C finalization contracts",
            truth_label=ShellExitTruthLabel.CONTRACT_ONLY,
        ),
    )


def _refs_by_id(refs: tuple[ShellExitEvidenceRef, ...]) -> dict[str, ShellExitEvidenceRef]:
    return {ref.ref_id: ref for ref in refs}


def _p2_9_b_is_complete(p29b_result: P29BResult) -> bool:
    return (
        p29b_result.done_checkpoints == P2_9_B_CHECKPOINT_IDS
        and not p29b_result.partial_checkpoints
        and not p29b_result.not_done_checkpoints
        and not p29b_result.blocked_checkpoints
        and not p29b_result.unavailable_checkpoints
        and p29b_result.p29c_next
        and not p29b_result.p210_allowed
    )


def build_shell_exit_finalization_intake(
    p29b_result: P29BResult | None = None,
) -> ShellExitFinalizationIntake:
    p29b_result = p29b_result or build_p2_9_b_shell_exit_readiness_result()
    p29b_complete = _p2_9_b_is_complete(p29b_result)
    payload = {
        "source_reports": P2_9_C_REQUIRED_REPORTS,
        "source_commits": (
            P2_9_A_COMMIT_REF,
            P2_9_A_R1_COMMIT_REF,
            P2_9_B_R1_COMMIT_REF,
            P2_9_B_IMPLEMENTATION_COMMIT_REF,
            P2_9_B_REPORT_HASH_COMMIT_REF,
            OLD_P2_9_B_OVERLAY_COMMIT_REF,
            P2_REVIEW_A_COMMIT_REF,
            P2_VSLICE_A_COMMIT_REF,
            P1_ENF_A_COMMIT_REF,
            P1_ENF_D1_COMMIT_REF,
            P1_ENF_E_COMMIT_REF,
        ),
        "completed_ranges": ("P2.9.0-P2.9.5", "P2.9.6-P2.9.10"),
        "partial_ranges": () if p29b_complete else ("P2.9.6-P2.9.10",),
        "not_done_ranges": ("P2.9.16-P2.9.20", "P2.10+"),
        "prior_checkpoint_seals": p29b_result.done_checkpoints,
        "p29b_result_ref": P2_9_B_REPORT_PATH,
        "p2_vslice_ref": P2_VSLICE_A_REPORT_PATH,
        "old_overlay_ref": OLD_P2_9_B_OVERLAY_REPORT_PATH,
        "intake_status": ShellExitFinalizationStatus.C_READY_FOR_D
        if p29b_complete
        else ShellExitFinalizationStatus.C_BLOCKED,
        "failure_reason": "" if p29b_complete else "true P2.9-B did not prove P2.9.6-P2.9.10 DONE",
    }
    return ShellExitFinalizationIntake(**payload, intake_hash=_hash_payload(payload))


def _release_blocker(
    *,
    blocker_id: str,
    severity: ShellExitBlockerSeverity,
    description: str,
    blocks: tuple[str, ...],
    evidence_refs: tuple[ShellExitEvidenceRef, ...],
    cleared: bool,
    clearance_requirement: str,
) -> ShellExitReleaseBlocker:
    payload = {
        "blocker_id": blocker_id,
        "severity": severity,
        "description": description,
        "blocks": blocks,
        "evidence_refs": evidence_refs,
        "cleared": cleared,
        "clearance_requirement": clearance_requirement,
    }
    return ShellExitReleaseBlocker(**payload, blocker_hash=_hash_payload(payload))


def build_shell_exit_release_blockers() -> tuple[ShellExitReleaseBlocker, ...]:
    refs = _refs_by_id(build_p2_9_c_evidence_refs())
    p29b_ref = refs["true_p2_9_b_readiness_matrix"]
    p2_vslice_ref = refs["p2_vslice_a_preflight"]
    sandbox_ref = refs["p1_enf_e_sandbox_gate"]
    return (
        _release_blocker(
            blocker_id="p2_9_d_not_done",
            severity=ShellExitBlockerSeverity.BLOCKS_P2_10,
            description="P2.9-D / P2.9.16-P2.9.20 remains required before P2.10.",
            blocks=("P2.10 start", "P2_COMPLETE claim"),
            evidence_refs=(p29b_ref,),
            cleared=False,
            clearance_requirement="Complete or explicitly seal P2.9-D.",
        ),
        _release_blocker(
            blocker_id="p2_10_not_started",
            severity=ShellExitBlockerSeverity.INFO,
            description="P2.10+ remains NOT STARTED and cannot be unlocked by P2.9-C.",
            blocks=("P2.10 readiness claim",),
            evidence_refs=(p29b_ref,),
            cleared=False,
            clearance_requirement="P2.9-D final tail seal must authorize any future P2.10 gate.",
        ),
        _release_blocker(
            blocker_id="command_execution_unavailable",
            severity=ShellExitBlockerSeverity.BLOCKS_COMMAND_EXECUTION,
            description="P2.VSLICE-A is command preflight only; arbitrary command execution is unavailable.",
            blocks=("command execution claim", "full command runtime claim"),
            evidence_refs=(p2_vslice_ref,),
            cleared=False,
            clearance_requirement="Future authorized runtime work must implement and validate command execution.",
        ),
        _release_blocker(
            blocker_id="shell_ui_unavailable",
            severity=ShellExitBlockerSeverity.BLOCKS_PRODUCT_RELEASE,
            description="No broad Shell product UI exists in this pack.",
            blocks=("Shell product UI release", "Shell LIVE claim"),
            evidence_refs=(p29b_ref,),
            cleared=False,
            clearance_requirement="Future P2.10+ product UI work must provide implementation evidence.",
        ),
        _release_blocker(
            blocker_id="safe_sandbox_unavailable",
            severity=ShellExitBlockerSeverity.BLOCKS_LIVE,
            description="SAFE_VERIFIED sandbox remains unavailable without proof.",
            blocks=("safe sandbox claim", "Shell LIVE claim"),
            evidence_refs=(sandbox_ref,),
            cleared=False,
            clearance_requirement="Provide SAFE_VERIFIED sandbox backend proof.",
        ),
        _release_blocker(
            blocker_id="cli_tui_unavailable",
            severity=ShellExitBlockerSeverity.WARN,
            description="P2.VSLICE-A operator path is pytest read-model; CLI/TUI binding remains a gap.",
            blocks=("CLI/TUI live claim",),
            evidence_refs=(p2_vslice_ref,),
            cleared=False,
            clearance_requirement="Future binding pack must add explicit CLI/TUI evidence or keep unavailable.",
        ),
        _release_blocker(
            blocker_id="api_event_bridge_not_live",
            severity=ShellExitBlockerSeverity.BLOCKS_LIVE,
            description="Full API/event bridge runtime is not live.",
            blocks=("full API/event bridge claim", "Shell LIVE claim"),
            evidence_refs=(p29b_ref,),
            cleared=False,
            clearance_requirement="Future authorized bridge work must provide live runtime evidence.",
        ),
        _release_blocker(
            blocker_id="contract_only_shell_sections",
            severity=ShellExitBlockerSeverity.BLOCKS_PRODUCT_RELEASE,
            description="Shell sections remain contract/read-model scoped, not product release scoped.",
            blocks=("product release claim", "P2_COMPLETE claim"),
            evidence_refs=(p29b_ref,),
            cleared=False,
            clearance_requirement="P2.9-D and later product gates must distinguish contract scope from release scope.",
        ),
        _release_blocker(
            blocker_id="full_suite_not_run",
            severity=ShellExitBlockerSeverity.WARN,
            description="Full pytest suite was not run for this pack.",
            blocks=("full suite PASS claim",),
            evidence_refs=(refs["p2_9_c_tests"],),
            cleared=False,
            clearance_requirement="Run full suite before claiming full-suite PASS.",
        ),
        _release_blocker(
            blocker_id="coverage_not_run",
            severity=ShellExitBlockerSeverity.WARN,
            description="Coverage was not run for this pack.",
            blocks=("coverage PASS claim",),
            evidence_refs=(refs["p2_9_c_tests"],),
            cleared=False,
            clearance_requirement="Run coverage before claiming coverage PASS.",
        ),
    )


def _boundary(
    *,
    boundary_id: str,
    boundary_type: ShellExitBoundaryType,
    description: str,
    active: bool,
    evidence_refs: tuple[ShellExitEvidenceRef, ...],
    forbidden_claim: str,
) -> ShellExitNoReleaseBoundary:
    payload = {
        "boundary_id": boundary_id,
        "boundary_type": boundary_type,
        "description": description,
        "active": active,
        "evidence_refs": evidence_refs,
        "forbidden_claim": forbidden_claim,
    }
    return ShellExitNoReleaseBoundary(**payload, boundary_hash=_hash_payload(payload))


def build_shell_exit_no_release_boundaries() -> tuple[ShellExitNoReleaseBoundary, ...]:
    refs = _refs_by_id(build_p2_9_c_evidence_refs())
    p29b_ref = refs["true_p2_9_b_readiness_matrix"]
    p2_vslice_ref = refs["p2_vslice_a_preflight"]
    sandbox_ref = refs["p1_enf_e_sandbox_gate"]
    test_ref = refs["p2_9_c_tests"]
    return (
        _boundary(
            boundary_id="no_shell_live",
            boundary_type=ShellExitBoundaryType.NO_SHELL_LIVE,
            description="P2.9-C finalization is not Shell LIVE.",
            active=True,
            evidence_refs=(p29b_ref,),
            forbidden_claim="Shell LIVE",
        ),
        _boundary(
            boundary_id="no_product_ui_release",
            boundary_type=ShellExitBoundaryType.NO_PRODUCT_UI_RELEASE,
            description="P2.9-C creates no full Shell product UI release.",
            active=True,
            evidence_refs=(p29b_ref,),
            forbidden_claim="full Shell product UI",
        ),
        _boundary(
            boundary_id="no_command_execution",
            boundary_type=ShellExitBoundaryType.NO_COMMAND_EXECUTION,
            description="P2.VSLICE-A remains preflight-only and does not execute commands.",
            active=True,
            evidence_refs=(p2_vslice_ref,),
            forbidden_claim="arbitrary command execution",
        ),
        _boundary(
            boundary_id="no_safe_sandbox_claim",
            boundary_type=ShellExitBoundaryType.NO_SAFE_SANDBOX_CLAIM,
            description="SAFE_VERIFIED sandbox cannot be claimed without proof.",
            active=True,
            evidence_refs=(sandbox_ref,),
            forbidden_claim="safe sandbox",
        ),
        _boundary(
            boundary_id="no_p2_10_start",
            boundary_type=ShellExitBoundaryType.NO_P2_10_START,
            description="P2.10 remains blocked until P2.9-D completes or explicitly seals the gate.",
            active=True,
            evidence_refs=(p29b_ref,),
            forbidden_claim="P2.10+ start",
        ),
        _boundary(
            boundary_id="no_full_api_event_bridge_claim",
            boundary_type=ShellExitBoundaryType.NO_FULL_API_EVENT_BRIDGE_CLAIM,
            description="P2.9-C does not implement or seal a full API/event bridge runtime.",
            active=True,
            evidence_refs=(p29b_ref,),
            forbidden_claim="full API/event bridge",
        ),
        _boundary(
            boundary_id="no_full_suite_claim",
            boundary_type=ShellExitBoundaryType.NO_FULL_SUITE_CLAIM,
            description="Focused validation is recorded; full suite is not claimed.",
            active=True,
            evidence_refs=(test_ref,),
            forbidden_claim="full suite PASS",
        ),
        _boundary(
            boundary_id="no_coverage_claim",
            boundary_type=ShellExitBoundaryType.NO_COVERAGE_CLAIM,
            description="Coverage is not run and cannot be claimed.",
            active=True,
            evidence_refs=(test_ref,),
            forbidden_claim="coverage PASS",
        ),
    )


def build_shell_exit_seal_decisions(
    intake: ShellExitFinalizationIntake | None = None,
    release_blockers: tuple[ShellExitReleaseBlocker, ...] | None = None,
    boundaries: tuple[ShellExitNoReleaseBoundary, ...] | None = None,
) -> tuple[ShellExitSealDecision, ...]:
    intake = intake or build_shell_exit_finalization_intake()
    release_blockers = release_blockers or build_shell_exit_release_blockers()
    boundaries = boundaries or build_shell_exit_no_release_boundaries()
    refs = _refs_by_id(build_p2_9_c_evidence_refs())
    status = (
        ShellExitDecisionStatus.SEALED
        if intake.intake_status is ShellExitFinalizationStatus.C_READY_FOR_D
        else ShellExitDecisionStatus.BLOCKED
    )
    failure_note = () if status is ShellExitDecisionStatus.SEALED else (intake.failure_reason,)
    decisions: list[ShellExitSealDecision] = []
    for checkpoint_id in P2_9_C_CHECKPOINT_IDS:
        truth_label = (
            ShellExitTruthLabel.PREFLIGHT_ONLY
            if checkpoint_id == "P2.9.14"
            else ShellExitTruthLabel.CONTRACT_ONLY
        )
        checkpoint_refs = (
            refs["true_p2_9_b_readiness_matrix"],
            refs["p2_9_a_foundation"],
            refs["p2_vslice_a_preflight"],
            refs["p2_9_c_tests"],
        )
        payload = {
            "checkpoint_id": checkpoint_id,
            "working_label": P2_9_C_WORKING_LABELS[checkpoint_id],
            "decision_status": status,
            "truth_label": truth_label,
            "evidence_refs": checkpoint_refs,
            "blockers": release_blockers,
            "boundaries": boundaries,
            "deferred_to": "P2.9-D" if checkpoint_id == "P2.9.15" else "",
            "notes": (
                "Working label only; not a canonical ROADMAP title.",
                "P2.9-C can produce C_READY_FOR_D but not P2_COMPLETE.",
                "P2.10 remains blocked.",
                *failure_note,
            ),
        }
        decisions.append(ShellExitSealDecision(**payload, decision_hash=_hash_payload(payload)))
    return tuple(decisions)


def build_shell_exit_decision_aggregate(
    decisions: tuple[ShellExitSealDecision, ...] | None = None,
) -> ShellExitSealDecisionAggregate:
    decisions = decisions or build_shell_exit_seal_decisions()
    sealed = tuple(d.checkpoint_id for d in decisions if d.decision_status is ShellExitDecisionStatus.SEALED)
    partial = tuple(d.checkpoint_id for d in decisions if d.decision_status is ShellExitDecisionStatus.PARTIAL)
    blocked = tuple(d.checkpoint_id for d in decisions if d.decision_status is ShellExitDecisionStatus.BLOCKED)
    deferred = tuple(d.checkpoint_id for d in decisions if d.decision_status is ShellExitDecisionStatus.DEFERRED_TO_P29D)
    not_sealed = tuple(d.checkpoint_id for d in decisions if d.decision_status is ShellExitDecisionStatus.NOT_SEALED)
    aggregate_status = (
        ShellExitFinalizationStatus.C_READY_FOR_D
        if sealed == P2_9_C_CHECKPOINT_IDS and not (partial or blocked or deferred or not_sealed)
        else ShellExitFinalizationStatus.C_BLOCKED
        if blocked
        else ShellExitFinalizationStatus.C_PARTIAL
    )
    payload = {
        "covered_range": P2_9_C_COVERED_RANGE,
        "decisions": decisions,
        "sealed_checkpoints": sealed,
        "partial_checkpoints": partial,
        "blocked_checkpoints": blocked,
        "deferred_checkpoints": deferred,
        "not_sealed_checkpoints": not_sealed,
        "aggregate_status": aggregate_status,
        "can_claim_p2_complete": False,
        "can_start_p210": False,
        "notes": (
            "P2.9-C aggregate may only become C_READY_FOR_D.",
            "P2_COMPLETE and P2.10 start remain impossible in P2.9-C.",
        ),
    }
    return ShellExitSealDecisionAggregate(**payload, aggregate_hash=_hash_payload(payload))


def build_shell_exit_finalization_evidence_bundle(
    present_reports: tuple[str, ...] = P2_9_C_REQUIRED_REPORTS,
) -> ShellExitFinalizationEvidenceBundle:
    missing_reports = tuple(report for report in P2_9_C_REQUIRED_REPORTS if report not in present_reports)
    refs = build_p2_9_c_evidence_refs()
    payload = {
        "bundle_id": "p2_9_c_finalization_evidence_bundle",
        "covered_range": P2_9_C_COVERED_RANGE,
        "required_reports": P2_9_C_REQUIRED_REPORTS,
        "present_reports": present_reports,
        "missing_reports": missing_reports,
        "commit_refs": (
            P2_9_A_COMMIT_REF,
            P2_9_A_R1_COMMIT_REF,
            P2_9_B_R1_COMMIT_REF,
            P2_9_B_IMPLEMENTATION_COMMIT_REF,
            P2_9_B_REPORT_HASH_COMMIT_REF,
            OLD_P2_9_B_OVERLAY_COMMIT_REF,
            P2_REVIEW_A_COMMIT_REF,
            P2_VSLICE_A_COMMIT_REF,
            P1_ENF_A_COMMIT_REF,
            P1_ENF_D1_COMMIT_REF,
            P1_ENF_E_COMMIT_REF,
            "pending-current-pack",
        ),
        "test_refs": (
            P2_9_C_TEST_FINALIZATION_REF,
            P2_9_C_TEST_BOUNDARIES_REF,
            P2_9_C_TEST_BUNDLE_REF,
            "tests/test_shell_exit_readiness.py",
            "tests/test_shell_exit_validation_matrix.py",
            "tests/test_p29b_shell_exit_evidence_matrix.py",
            "tests/test_p2_command_palette_vslice.py",
            "tests/test_p2_command_preflight.py",
            "tests/test_p2_vertical_slice_review.py",
        ),
        "state_refs": ("agent/STATE.md", "agent/ACTIVE_TASK.md", "agent/REPORTS.md"),
        "trace_or_evidence_refs": refs,
        "bundle_status": ShellExitFinalizationStatus.C_READY_FOR_D
        if not missing_reports
        else ShellExitFinalizationStatus.C_BLOCKED,
        "notes": (
            "P2.9-D can consume this bundle instead of rediscovering prior P2.9 evidence.",
            "Evidence is bundled without escalating PREFLIGHT_ONLY or CONTRACT_ONLY truth labels.",
        ),
    }
    return ShellExitFinalizationEvidenceBundle(**payload, bundle_hash=_hash_payload(payload))


def build_shell_exit_p29d_handoff(
    aggregate: ShellExitSealDecisionAggregate,
    evidence_bundle: ShellExitFinalizationEvidenceBundle,
    release_blockers: tuple[ShellExitReleaseBlocker, ...],
) -> ShellExitP29DHandoff:
    p29d_ready = aggregate.aggregate_status is ShellExitFinalizationStatus.C_READY_FOR_D
    remaining = tuple(blocker for blocker in release_blockers if not blocker.cleared)
    payload = {
        "next_pack": P2_9_C_NEXT_PACK,
        "next_range": P2_9_C_NEXT_RANGE,
        "p29d_handoff_ready": p29d_ready,
        "p210_allowed": False,
        "p210_block_reason": "P2.9-D / P2.9.16-P2.9.20 is not done; P2.10+ remains NOT STARTED.",
        "inherited_evidence_bundle": evidence_bundle.bundle_id,
        "required_p29d_decisions": P2_9_C_REQUIRED_P29D_DECISIONS,
        "remaining_blockers": remaining,
        "notes": (
            "P2.9-C hands off to P2.9-D, not P2.10.",
            "P2.9-C does not claim final P2 exit.",
        ),
    }
    return ShellExitP29DHandoff(**payload, handoff_hash=_hash_payload(payload))


def build_p2_9_c_shell_exit_finalization_result(
    p29b_result: P29BResult | None = None,
) -> P29CResult:
    intake = build_shell_exit_finalization_intake(p29b_result)
    blockers = build_shell_exit_release_blockers()
    boundaries = build_shell_exit_no_release_boundaries()
    decisions = build_shell_exit_seal_decisions(intake, blockers, boundaries)
    aggregate = build_shell_exit_decision_aggregate(decisions)
    bundle = build_shell_exit_finalization_evidence_bundle()
    handoff = build_shell_exit_p29d_handoff(aggregate, bundle, blockers)
    side_effect_proof = P29CSideEffectProof()
    payload = {
        "covered_range": P2_9_C_COVERED_RANGE,
        "finalization_intake": intake,
        "decision_aggregate": aggregate,
        "release_blockers": blockers,
        "no_release_boundaries": boundaries,
        "evidence_bundle": bundle,
        "p29d_handoff": handoff,
        "side_effect_proof": side_effect_proof,
        "p29d_next": handoff.next_pack == "P2.9-D",
        "p210_allowed": False,
        "p2_vslice_a_truth_label": ShellExitTruthLabel.PREFLIGHT_ONLY,
    }
    return P29CResult(**payload, result_hash=_hash_payload(payload))


def serialize_p2_9_c_result(result: P29CResult) -> str:
    return to_canonical_json(result.to_canonical_dict())


def render_p2_9_c_coverage_rows(result: P29CResult) -> tuple[str, ...]:
    rows: list[str] = []
    for decision in result.decision_aggregate.decisions:
        gap = "P2.9-D not done; P2.10 blocked; Shell LIVE/product/command execution not claimed"
        next_action = "P2.9-D" if decision.checkpoint_id == "P2.9.15" else "covered by P2.9-C"
        rows.append(
            "| {checkpoint} | {label} | {status} | {truth} | {evidence} | {gap} | {next_action} |".format(
                checkpoint=decision.checkpoint_id,
                label=decision.working_label,
                status=decision.decision_status.value,
                truth=decision.truth_label.value,
                evidence=", ".join(ref.path for ref in decision.evidence_refs),
                gap=gap,
                next_action=next_action,
            )
        )
    return tuple(rows)


def assert_p2_9_c_prerequisite_gate_passed(intake: ShellExitFinalizationIntake) -> None:
    if intake.intake_status is not ShellExitFinalizationStatus.C_READY_FOR_D:
        _reject(
            "P2.9-C cannot proceed unless true P2.9-B proves P2.9.6-P2.9.10 DONE",
            field="intake_status",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_9_c_aggregate_does_not_claim_p2_complete(
    aggregate: ShellExitSealDecisionAggregate,
) -> None:
    if aggregate.can_claim_p2_complete or aggregate.can_start_p210:
        _reject(
            "P2.9-C aggregate cannot claim P2_COMPLETE or start P2.10",
            field="decision_aggregate",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_9_c_blocks_p2_10(result: P29CResult) -> None:
    has_blocker = any(
        blocker.severity is ShellExitBlockerSeverity.BLOCKS_P2_10 and not blocker.cleared
        for blocker in result.release_blockers
    )
    has_boundary = any(
        boundary.boundary_type is ShellExitBoundaryType.NO_P2_10_START and boundary.active
        for boundary in result.no_release_boundaries
    )
    if result.p210_allowed or result.p29d_handoff.p210_allowed or not (has_blocker and has_boundary):
        _reject(
            "P2.9-C must keep P2.10 blocked until P2.9-D completes",
            field="p210_allowed",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_p2_9_c_handoff_points_to_p2_9_d(result: P29CResult) -> None:
    if result.p29d_handoff.next_pack != "P2.9-D" or result.p29d_handoff.next_range != P2_9_C_NEXT_RANGE:
        _reject(
            "P2.9-C must hand off to P2.9-D / P2.9.16-P2.9.20",
            field="p29d_handoff",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_p2_vslice_a_remains_preflight_in_p29c(result: P29CResult) -> None:
    if result.p2_vslice_a_truth_label is not ShellExitTruthLabel.PREFLIGHT_ONLY:
        _reject(
            "P2.VSLICE-A must remain PREFLIGHT_ONLY in P2.9-C",
            field="p2_vslice_a_truth_label",
            code=AurelShellErrorCode.INVALID_TRUTH_LABEL,
        )


def assert_p2_9_c_no_scope_expansion(result: P29CResult) -> None:
    if any(result.side_effect_proof.to_canonical_dict().values()):
        _reject(
            "P2.9-C finalization must not create runtime, UI, execution, future-pack, or P2 exit side effects",
            field="side_effect_proof",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )
