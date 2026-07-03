"""P3-FLOW-L extended AurelFlow domain seal (P3.20).

The P3 domain seal closes AurelFlow as an honest, deterministic,
non-executing control-plane grammar. The seal is a control-plane statement
only: it is not production readiness, not release approval, not Trace proof,
not Custos authority, and not P4 implementation. The A-L coverage summary is
evidence bookkeeping, never proof. The K evaluation summary consumes the
P3-FLOW-K seal input frame as-is: an evaluation is not proof and a quality
score approves no release.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import AurelFlowErrorCode, AurelFlowValidationError
from .flow_harness_projection import P3SealInputFrame
from .types import FlowTruthLabel, _CanonicalMixin, stable_hash

P3_PACK_COVERAGE_ITEM_VERSION = "p3_pack_coverage_item.v1"
P3_COVERAGE_SUMMARY_VERSION = "p3_coverage_summary.v1"
K_EVALUATION_SUMMARY_VERSION = "k_evaluation_summary.v1"
P3_DOMAIN_SEAL_VERSION = "p3_domain_seal.v1"

DOMAIN_SEAL_UNAVAILABLE_REASON = (
    "the P3 domain seal closes AurelFlow as a non-executing control-plane "
    "grammar only: nothing becomes production-ready, release-approved, "
    "trace-verified, or authorized — P4 executes, P5 proves, P9 authorizes"
)
COVERAGE_SUMMARY_UNAVAILABLE_REASON = (
    "the A-L coverage summary reports pack status and evidence pointers "
    "only; a coverage summary is not proof and not production readiness"
)
K_EVALUATION_SUMMARY_UNAVAILABLE_REASON = (
    "the K evaluation summary consumes the P3-FLOW-K seal input frame "
    "as-is; an evaluation is not proof, a quality score approves no "
    "release, and K performed no final seal"
)


def _forbid_true(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain False",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


def _forbid_false(obj: object, *boundary_fields: str) -> None:
    for boundary_field in boundary_fields:
        if not getattr(obj, boundary_field):
            raise AurelFlowValidationError(
                f"{type(obj).__name__}.{boundary_field} must remain True",
                code=AurelFlowErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field=boundary_field,
            )


class P3FlowPack(str, Enum):
    """Closed-world P3 AurelFlow pack chain sealed by P3-FLOW-L."""

    P3_FLOW_A = "P3-FLOW-A"
    P3_FLOW_B = "P3-FLOW-B"
    P3_FLOW_C = "P3-FLOW-C"
    P3_FLOW_D = "P3-FLOW-D"
    P3_FLOW_E = "P3-FLOW-E"
    P3_FLOW_F = "P3-FLOW-F"
    P3_FLOW_G = "P3-FLOW-G"
    P3_FLOW_H = "P3-FLOW-H"
    P3_FLOW_I = "P3-FLOW-I"
    P3_FLOW_J = "P3-FLOW-J"
    P3_FLOW_K = "P3-FLOW-K"
    P3_FLOW_L = "P3-FLOW-L"


class P3PackCoverageStatus(str, Enum):
    """Closed-world pack coverage vocabulary. There is no PROVEN member."""

    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


_SEAL_BLOCKING_COVERAGE_STATUSES: frozenset[P3PackCoverageStatus] = frozenset(
    (
        P3PackCoverageStatus.MISSING,
        P3PackCoverageStatus.BLOCKED,
        P3PackCoverageStatus.ERROR,
    )
)


@dataclass(frozen=True)
class P3PackCoverageItem(_CanonicalMixin):
    """One pack's coverage status with an evidence pointer. Not proof."""

    coverage_item_id: str
    contract_version: str
    pack: P3FlowPack
    status: P3PackCoverageStatus
    evidence_note: str
    truth_label: FlowTruthLabel
    unavailable_reason: str = COVERAGE_SUMMARY_UNAVAILABLE_REASON
    proof_available: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_true(self, "proof_available", "production_ready")
        if not self.evidence_note.strip():
            raise AurelFlowValidationError(
                f"pack {self.pack.value} coverage must explain itself with "
                "a non-empty evidence note",
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="evidence_note",
            )


def create_p3_pack_coverage_item(
    *,
    pack: P3FlowPack,
    status: P3PackCoverageStatus,
    evidence_note: str,
) -> P3PackCoverageItem:
    payload = {
        "contract_version": P3_PACK_COVERAGE_ITEM_VERSION,
        "pack": pack.value,
        "status": status.value,
        "evidence_note": evidence_note,
    }
    return P3PackCoverageItem(
        coverage_item_id="fllci-" + stable_hash(payload)[:16],
        contract_version=P3_PACK_COVERAGE_ITEM_VERSION,
        pack=pack,
        status=status,
        evidence_note=evidence_note,
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


_DEFAULT_PACK_EVIDENCE: tuple[tuple[P3FlowPack, str], ...] = (
    (
        P3FlowPack.P3_FLOW_A,
        "agent/reports/P3_FLOW_A_AURELFLOW_RUNTIME_FOUNDATION_SUPERPACK.md; "
        "tests/test_p3_flow_a_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_B,
        "agent/reports/P3_FLOW_B_RUNTIME_BEHAVIOR_LOOP_PACK.md; "
        "tests/test_p3_flow_b_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_C,
        "agent/reports/P3_FLOW_C_FLOW_STATE_PROJECTION_CLI_DOCS_BASE_SEAL.md; "
        "tests/test_p3_flow_c_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_D,
        "agent/reports/P3_FLOW_D_AUTHORITY_CONTROL_BOUNDARY_PACK.md; "
        "tests/test_p3_flow_d_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_E,
        "agent/reports/P3_FLOW_E_DYNAMIC_RUNTIME_GRAPH_PACK.md; "
        "tests/test_p3_flow_e_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_F,
        "agent/reports/P3_FLOW_F_REVERSIBLE_RUNTIME_STATE_PACK.md; "
        "tests/test_p3_flow_f_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_G,
        "agent/reports/P3_FLOW_G_SELF_HEALING_RELIABILITY_CONTROL_PACK.md; "
        "tests/test_p3_flow_g_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_H,
        "agent/reports/P3_FLOW_H_GOVERNED_AUTONOMY_SCOPE_PACK.md; "
        "tests/test_p3_flow_h_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_I,
        "agent/reports/P3_FLOW_I_SCHEDULING_INTENT_RESOURCE_PREDICTION_PACK.md; "
        "tests/test_p3_flow_i_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_J,
        "agent/reports/P3_FLOW_J_COMPOUND_RUNTIME_TOPOLOGY_PACK.md; "
        "tests/test_p3_flow_j_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_K,
        "agent/reports/P3_FLOW_K_RUNTIME_HARNESS_EVALUATION_PACK.md; "
        "tests/test_p3_flow_k_*.py",
    ),
    (
        P3FlowPack.P3_FLOW_L,
        "agent/reports/P3_FLOW_L_EXTENDED_AURELFLOW_DOMAIN_SEAL_P4_HANDOFF.md; "
        "tests/test_p3_flow_l_*.py",
    ),
)


def build_default_p3_pack_coverage_items() -> tuple[P3PackCoverageItem, ...]:
    """The canonical A-L coverage claim: report + test evidence per pack."""

    return tuple(
        create_p3_pack_coverage_item(
            pack=pack,
            status=P3PackCoverageStatus.COVERED,
            evidence_note=evidence_note,
        )
        for pack, evidence_note in _DEFAULT_PACK_EVIDENCE
    )


@dataclass(frozen=True)
class P3CoverageSummary(_CanonicalMixin):
    """Total A-L coverage summary. A coverage summary is not proof."""

    coverage_summary_id: str
    contract_version: str
    items: tuple[P3PackCoverageItem, ...]
    covered_count: int
    partial_count: int
    missing_count: int
    unavailable_count: int
    blocked_count: int
    error_count: int
    fully_covered: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = COVERAGE_SUMMARY_UNAVAILABLE_REASON
    proof_available: bool = False
    trace_verified: bool = False
    production_ready: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self, "proof_available", "trace_verified", "production_ready"
        )


def build_p3_coverage_summary(
    items: tuple[P3PackCoverageItem, ...],
) -> P3CoverageSummary:
    """Deterministic totality check: every pack A-L exactly once."""

    seen: dict[P3FlowPack, P3PackCoverageItem] = {}
    for item in items:
        if item.pack in seen:
            raise AurelFlowValidationError(
                f"pack {item.pack.value} appears more than once in the "
                "coverage summary",
                code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
                field="items",
            )
        seen[item.pack] = item
    absent = tuple(pack for pack in P3FlowPack if pack not in seen)
    if absent:
        raise AurelFlowValidationError(
            "the coverage summary must be total over P3-FLOW-A..L; absent: "
            + ", ".join(pack.value for pack in absent),
            code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
            field="items",
        )

    def _count(status: P3PackCoverageStatus) -> int:
        return sum(1 for item in items if item.status is status)

    covered_count = _count(P3PackCoverageStatus.COVERED)
    payload = {
        "contract_version": P3_COVERAGE_SUMMARY_VERSION,
        "coverage_item_ids": tuple(
            sorted(item.coverage_item_id for item in items)
        ),
    }
    return P3CoverageSummary(
        coverage_summary_id="fllcs-" + stable_hash(payload)[:16],
        contract_version=P3_COVERAGE_SUMMARY_VERSION,
        items=tuple(items),
        covered_count=covered_count,
        partial_count=_count(P3PackCoverageStatus.PARTIAL),
        missing_count=_count(P3PackCoverageStatus.MISSING),
        unavailable_count=_count(P3PackCoverageStatus.UNAVAILABLE),
        blocked_count=_count(P3PackCoverageStatus.BLOCKED),
        error_count=_count(P3PackCoverageStatus.ERROR),
        fully_covered=covered_count == len(tuple(P3FlowPack)),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )


@dataclass(frozen=True)
class KEvaluationSummary(_CanonicalMixin):
    """P3-FLOW-K seal input, consumed as-is. Evaluation is not proof."""

    k_evaluation_summary_id: str
    contract_version: str
    seal_input_id: str
    evaluation_run_id: str
    readiness_finding_count: int
    blocking_risk_count: int
    seal_ready_candidate: bool
    truth_label: FlowTruthLabel
    unavailable_reason: str = K_EVALUATION_SUMMARY_UNAVAILABLE_REASON
    evaluation_is_proof: bool = False
    quality_score_approved_release: bool = False
    p4_implemented: bool = False
    final_seal_performed_by_k: bool = False

    def __post_init__(self) -> None:
        _forbid_true(
            self,
            "evaluation_is_proof",
            "quality_score_approved_release",
            "p4_implemented",
            "final_seal_performed_by_k",
        )


def summarize_k_evaluation(frame: P3SealInputFrame) -> KEvaluationSummary:
    payload = {
        "contract_version": K_EVALUATION_SUMMARY_VERSION,
        "seal_input_id": frame.seal_input_id,
    }
    return KEvaluationSummary(
        k_evaluation_summary_id="fllke-" + stable_hash(payload)[:16],
        contract_version=K_EVALUATION_SUMMARY_VERSION,
        seal_input_id=frame.seal_input_id,
        evaluation_run_id=frame.evaluation_run_id,
        readiness_finding_count=len(frame.readiness_findings),
        blocking_risk_count=len(frame.blocking_risks),
        seal_ready_candidate=frame.seal_ready_candidate,
        truth_label=FlowTruthLabel.READ_MODEL_ONLY,
    )


@dataclass(frozen=True)
class P3DomainSeal(_CanonicalMixin):
    """The final P3 control-plane seal. Sealed is not production-ready."""

    seal_id: str
    contract_version: str
    coverage_summary_id: str
    k_evaluation_summary_id: str
    sealed_pack_values: tuple[str, ...]
    truth_label: FlowTruthLabel
    unavailable_reason: str = DOMAIN_SEAL_UNAVAILABLE_REASON
    p3_control_plane_sealed: bool = True
    production_ready: bool = False
    release_approved: bool = False
    live_path_available: bool = False
    trace_verified: bool = False
    proof_available: bool = False
    authority_granted: bool = False
    permission_granted: bool = False
    p4_implemented: bool = False
    p5_implemented: bool = False
    p9_implemented: bool = False
    runtime_submit_wired: bool = False
    execution_available: bool = False
    workflow_executed: bool = False
    dispatch_available: bool = False
    persistence_implemented: bool = False

    def __post_init__(self) -> None:
        _forbid_false(self, "p3_control_plane_sealed")
        _forbid_true(
            self,
            "production_ready",
            "release_approved",
            "live_path_available",
            "trace_verified",
            "proof_available",
            "authority_granted",
            "permission_granted",
            "p4_implemented",
            "p5_implemented",
            "p9_implemented",
            "runtime_submit_wired",
            "execution_available",
            "workflow_executed",
            "dispatch_available",
            "persistence_implemented",
        )


def seal_p3_domain(
    *,
    coverage_summary: P3CoverageSummary,
    k_evaluation_summary: KEvaluationSummary,
) -> P3DomainSeal:
    """Fail-closed seal: gaps and blocking risks make sealing impossible.

    MISSING/BLOCKED/ERROR coverage or K blocking risks reject the seal
    outright — an honest partial state can never be dressed up as sealed.
    Sealing changes no runtime state and grants nothing.
    """

    blocking_items = tuple(
        item
        for item in coverage_summary.items
        if item.status in _SEAL_BLOCKING_COVERAGE_STATUSES
    )
    if blocking_items:
        raise AurelFlowValidationError(
            "cannot seal P3 with blocking coverage statuses: "
            + ", ".join(
                f"{item.pack.value}={item.status.value}"
                for item in blocking_items
            ),
            code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
            field="coverage_summary",
        )
    if k_evaluation_summary.blocking_risk_count:
        raise AurelFlowValidationError(
            f"cannot seal P3 with {k_evaluation_summary.blocking_risk_count} "
            "K blocking risks outstanding",
            code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
            field="k_evaluation_summary",
        )
    if not k_evaluation_summary.seal_ready_candidate:
        raise AurelFlowValidationError(
            "cannot seal P3 without a seal-ready K candidate",
            code=AurelFlowErrorCode.INVALID_SEAL_CHECK,
            field="k_evaluation_summary",
        )
    payload = {
        "contract_version": P3_DOMAIN_SEAL_VERSION,
        "coverage_summary_id": coverage_summary.coverage_summary_id,
        "k_evaluation_summary_id": (
            k_evaluation_summary.k_evaluation_summary_id
        ),
    }
    return P3DomainSeal(
        seal_id="fllds-" + stable_hash(payload)[:16],
        contract_version=P3_DOMAIN_SEAL_VERSION,
        coverage_summary_id=coverage_summary.coverage_summary_id,
        k_evaluation_summary_id=(
            k_evaluation_summary.k_evaluation_summary_id
        ),
        sealed_pack_values=tuple(pack.value for pack in P3FlowPack),
        truth_label=FlowTruthLabel.LOCAL_RUNTIME_SUBSTRATE,
    )
