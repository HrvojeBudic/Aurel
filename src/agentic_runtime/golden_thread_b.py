"""P1.ENF-C Golden Thread B governance continuity harness.

Continuity spine linking P1.8 through P2.9-A, P1.ENF repair/audit/gate chain,
and P2.9-B NOT_DONE handoff. Evidence nodes are not enforcement; missing
evidence is surfaced as GAP/WARNING/ERROR rather than hidden.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence


class GoldenThreadBTruthLabel(str, Enum):
    DONE_EVIDENCED = "done_evidenced"
    CONTRACT_ONLY = "contract_only"
    ENFORCEMENT_BRIDGE = "enforcement_bridge"
    VALIDATION_TRUTH_REPAIR = "validation_truth_repair"
    NO_BYPASS_EVIDENCE = "no_bypass_evidence"
    DRIFT_GATED = "drift_gated"
    UNAVAILABLE = "unavailable"
    NOT_DONE = "not_done"
    GAP = "gap"
    WARNING = "warning"
    ERROR = "error"


class GoldenThreadBNodeType(str, Enum):
    ROADMAP_CHECKPOINT = "roadmap_checkpoint"
    AGENT_REPORT = "agent_report"
    VALIDATION_EVIDENCE = "validation_evidence"
    COMMIT_EVIDENCE = "commit_evidence"
    RUNTIME_ENFORCEMENT = "runtime_enforcement"
    ENTRYPOINT_AUDIT = "entrypoint_audit"
    DRIFT_GATE = "drift_gate"
    SHELL_CONTRACT = "shell_contract"
    UNAVAILABLE_BINDING = "unavailable_binding"
    NEXT_TASK_HANDOFF = "next_task_handoff"


@dataclass(frozen=True)
class GoldenThreadBEvidenceRef:
    ref_kind: str
    ref_value: str
    present: bool

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "present": self.present,
            "ref_kind": self.ref_kind,
            "ref_value": self.ref_value,
        }


@dataclass(frozen=True)
class GoldenThreadBNode:
    node_id: str
    title: str
    roadmap_ref: str
    node_type: GoldenThreadBNodeType
    report_path: str | None
    report_exists: bool
    report_indexed: bool
    validation_evidence: bool
    commit_evidence: bool
    truth_label: GoldenThreadBTruthLabel
    required: bool
    gap_reason: str | None = None
    next_handoff: str | None = None
    evidence_refs: tuple[GoldenThreadBEvidenceRef, ...] = ()
    commit_hash: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "commit_evidence": self.commit_evidence,
            "commit_hash": self.commit_hash,
            "gap_reason": self.gap_reason,
            "next_handoff": self.next_handoff,
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "report_exists": self.report_exists,
            "report_indexed": self.report_indexed,
            "report_path": self.report_path,
            "required": self.required,
            "roadmap_ref": self.roadmap_ref,
            "title": self.title,
            "truth_label": self.truth_label.value,
            "validation_evidence": self.validation_evidence,
        }


@dataclass(frozen=True)
class GoldenThreadBGap:
    node_id: str
    severity: GoldenThreadBTruthLabel
    reason: str

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "node_id": self.node_id,
            "reason": self.reason,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class GoldenThreadBSideEffectProof:
    golden_thread_a_rewritten: bool = False
    p2_9_b_implemented: bool = False
    p2_9_c_started: bool = False
    p2_9_d_started: bool = False
    p2_10_started: bool = False
    shell_command_router_created: bool = False
    product_ui_created: bool = False
    p2_vertical_slice_created: bool = False
    roadmap_rewritten: bool = False
    identity_cli_refactored: bool = False
    sandbox_backend_hardened: bool = False
    repo_agent_rewritten: bool = False

    def blocks_product_scope(self) -> bool:
        return not any(
            (
                self.golden_thread_a_rewritten,
                self.p2_9_b_implemented,
                self.p2_9_c_started,
                self.p2_9_d_started,
                self.p2_10_started,
                self.shell_command_router_created,
                self.product_ui_created,
                self.p2_vertical_slice_created,
                self.roadmap_rewritten,
                self.identity_cli_refactored,
                self.sandbox_backend_hardened,
                self.repo_agent_rewritten,
            )
        )

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "golden_thread_a_rewritten": self.golden_thread_a_rewritten,
            "identity_cli_refactored": self.identity_cli_refactored,
            "p2_10_started": self.p2_10_started,
            "p2_9_b_implemented": self.p2_9_b_implemented,
            "p2_9_c_started": self.p2_9_c_started,
            "p2_9_d_started": self.p2_9_d_started,
            "p2_vertical_slice_created": self.p2_vertical_slice_created,
            "product_ui_created": self.product_ui_created,
            "repo_agent_rewritten": self.repo_agent_rewritten,
            "roadmap_rewritten": self.roadmap_rewritten,
            "sandbox_backend_hardened": self.sandbox_backend_hardened,
            "shell_command_router_created": self.shell_command_router_created,
        }


@dataclass(frozen=True)
class GoldenThreadBContinuityCheck:
    check_id: str
    passed: bool
    detail: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "detail": self.detail,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class NodeSpec:
    node_id: str
    title: str
    roadmap_ref: str
    node_type: GoldenThreadBNodeType
    report_path: str | None
    truth_label: GoldenThreadBTruthLabel
    required: bool = True
    index_token: str | None = None
    git_fallback_commit: str | None = None
    next_handoff: str | None = None
    binding_unavailable: bool = False


@dataclass(frozen=True)
class GoldenThreadBResult:
    nodes: tuple[GoldenThreadBNode, ...]
    continuity_passed: bool
    has_errors: bool
    has_gaps: bool
    has_warnings: bool
    p2_9_b_status: str
    live_claimed: bool
    trace_verified_claimed: bool
    side_effect_proof: GoldenThreadBSideEffectProof
    next_recommended_step: str
    gaps: tuple[GoldenThreadBGap, ...] = ()
    continuity_checks: tuple[GoldenThreadBContinuityCheck, ...] = ()
    golden_thread_a_preserved: bool = True

    def node_by_id(self, node_id: str) -> GoldenThreadBNode | None:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "continuity_passed": self.continuity_passed,
            "gaps": [gap.to_canonical_dict() for gap in self.gaps],
            "golden_thread_a_preserved": self.golden_thread_a_preserved,
            "has_errors": self.has_errors,
            "has_gaps": self.has_gaps,
            "has_warnings": self.has_warnings,
            "live_claimed": self.live_claimed,
            "next_recommended_step": self.next_recommended_step,
            "node_count": len(self.nodes),
            "p2_9_b_status": self.p2_9_b_status,
            "side_effect_proof": self.side_effect_proof.to_canonical_dict(),
            "trace_verified_claimed": self.trace_verified_claimed,
        }


_COMMIT_HASH_RE = re.compile(
    r"(?:Commit Hash|commit hash)[^\n`]*`([0-9a-f]{7,40})`",
    re.IGNORECASE,
)
_VALIDATION_MARKERS = (
    "compileall",
    "pytest",
    "passed",
    "validation",
    "ruff",
    "mypy",
)
_LIVE_CLAIM_RE = re.compile(r"\b(?:claims_live|LIVE\b(?!\s*demo))", re.IGNORECASE)
_TRACE_VERIFIED_CLAIM_RE = re.compile(
    r"\b(?:claims_trace_verified|TRACE_VERIFIED\b(?!\s*(?:without|not|unavailable)))",
    re.IGNORECASE,
)

GOLDEN_THREAD_B_NODE_SPECS: tuple[NodeSpec, ...] = (
    NodeSpec(
        node_id="p1_8",
        title="P1.8 Delegation / Accountability / Non-repudiation",
        roadmap_ref="P1.8",
        node_type=GoldenThreadBNodeType.ROADMAP_CHECKPOINT,
        report_path="agent/reports/P1_8_C_DELEGATION_INTEGRATION_TAIL_PACK.md",
        truth_label=GoldenThreadBTruthLabel.DONE_EVIDENCED,
        index_token="P1.8-C",
    ),
    NodeSpec(
        node_id="p1_9",
        title="P1.9 Output Passport / Evidence Continuity",
        roadmap_ref="P1.9",
        node_type=GoldenThreadBNodeType.ROADMAP_CHECKPOINT,
        report_path="agent/reports/P1_9_D_INTEGRATION_TAIL_PACK.md",
        truth_label=GoldenThreadBTruthLabel.DONE_EVIDENCED,
        index_token="P1.9-D",
    ),
    NodeSpec(
        node_id="p2_1",
        title="P2.1 Global Topbar / Surface Registry",
        roadmap_ref="P2.1",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_1_D_TOPBAR_INTEGRATION_TAIL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.1-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_2",
        title="P2.2 Per-Surface Local Navigation",
        roadmap_ref="P2.2",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_2_D_LOCAL_NAVIGATION_INTEGRATION_TAIL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.2-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_3",
        title="P2.3 Floating Windows / Workspace State",
        roadmap_ref="P2.3",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_3_D_WORKSPACE_WINDOW_SECTION_SEAL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.3-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_4",
        title="P2.4 Command Palette / Global Commands",
        roadmap_ref="P2.4",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_4_D_COMMAND_PALETTE_SECTION_SEAL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.4-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_5",
        title="P2.5 Cross-Surface Handoff",
        roadmap_ref="P2.5",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_5_D_HANDOFF_SECTION_SEAL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.5-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_6",
        title="P2.6 Surface Projection / API / Event Bridge",
        roadmap_ref="P2.6",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.6-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_7",
        title="P2.7 Shell / CLI / TUI Binding",
        roadmap_ref="P2.7",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_7_D_SHELL_CLI_TUI_BINDING_SECTION_SEAL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.7-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_8",
        title="P2.8 Shell State / Reports / Docs",
        roadmap_ref="P2.8",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_8_D_SHELL_STATE_REPORTS_DOCS_SECTION_SEAL.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.8-D",
        binding_unavailable=True,
    ),
    NodeSpec(
        node_id="p2_9_a",
        title="P2.9-A Shell Exit Seal Foundation",
        roadmap_ref="P2.9-A",
        node_type=GoldenThreadBNodeType.SHELL_CONTRACT,
        report_path="agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md",
        truth_label=GoldenThreadBTruthLabel.CONTRACT_ONLY,
        index_token="P2.9-A",
        git_fallback_commit="0e8a7b4",
    ),
    NodeSpec(
        node_id="p2_9_a_r1",
        title="P2.9-A-R1 Shell Exit Seal Foundation Evidence Ref Repair",
        roadmap_ref="P2.9-A-R1",
        node_type=GoldenThreadBNodeType.AGENT_REPORT,
        report_path="agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md",
        truth_label=GoldenThreadBTruthLabel.VALIDATION_TRUTH_REPAIR,
        index_token="P2.9-A-R1",
        git_fallback_commit="ab1b2ba",
    ),
    NodeSpec(
        node_id="p1_enf_a",
        title="P1.ENF-A Runtime Submit Enforcement Bridge",
        roadmap_ref="P1.ENF-A",
        node_type=GoldenThreadBNodeType.RUNTIME_ENFORCEMENT,
        report_path="agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md",
        truth_label=GoldenThreadBTruthLabel.ENFORCEMENT_BRIDGE,
        index_token="P1.ENF-A",
        git_fallback_commit="07c65b5",
    ),
    NodeSpec(
        node_id="p1_enf_a_omni_r1",
        title="P1.ENF-A-OMNI-R1 Validation Truth / Core Integrity Repair",
        roadmap_ref="P1.ENF-A-OMNI-R1",
        node_type=GoldenThreadBNodeType.VALIDATION_EVIDENCE,
        report_path="agent/reports/P1_ENF_A_OMNI_R1_VALIDATION_TRUTH_CORE_INTEGRITY_REPAIR.md",
        truth_label=GoldenThreadBTruthLabel.VALIDATION_TRUTH_REPAIR,
        index_token="P1.ENF-A-OMNI-R1",
        git_fallback_commit="8bf05de",
    ),
    NodeSpec(
        node_id="p1_enf_b",
        title="P1.ENF-B Entrypoint Bypass Guard / Repo Agent Audit",
        roadmap_ref="P1.ENF-B",
        node_type=GoldenThreadBNodeType.ENTRYPOINT_AUDIT,
        report_path="agent/reports/P1_ENF_B_ENTRYPOINT_BYPASS_GUARD_REPO_AGENT_ENFORCEMENT_AUDIT.md",
        truth_label=GoldenThreadBTruthLabel.NO_BYPASS_EVIDENCE,
        index_token="P1.ENF-B",
        git_fallback_commit="47ea128",
    ),
    NodeSpec(
        node_id="p1_enf_f_a",
        title="P1.ENF-F-A Tooling / Determinism / Shadow Drift Gates",
        roadmap_ref="P1.ENF-F-A",
        node_type=GoldenThreadBNodeType.DRIFT_GATE,
        report_path="agent/reports/P1_ENF_F_A_TOOLING_DETERMINISM_SHADOW_DRIFT_GATES.md",
        truth_label=GoldenThreadBTruthLabel.DRIFT_GATED,
        index_token="P1.ENF-F-A",
        git_fallback_commit="d91d2e2",
    ),
    NodeSpec(
        node_id="p2_9_b",
        title="P2.9-B Shell Exit Seal Readiness / Validation / Evidence Matrix",
        roadmap_ref="P2.9-B",
        node_type=GoldenThreadBNodeType.NEXT_TASK_HANDOFF,
        report_path=None,
        truth_label=GoldenThreadBTruthLabel.NOT_DONE,
        required=True,
        next_handoff="P2.9-B remains NOT DONE; blocked until operator reruns readiness pack",
    ),
)


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_commit_hash(report_text: str) -> str | None:
    match = _COMMIT_HASH_RE.search(report_text)
    if match is None:
        return None
    value = match.group(1)
    if value.lower() in {"pending", "tbd", "unknown"}:
        return None
    return value


def _has_validation_evidence(report_text: str) -> bool:
    lowered = report_text.lower()
    return any(marker in lowered for marker in _VALIDATION_MARKERS)


def _is_indexed(index_text: str, spec: NodeSpec) -> bool:
    if spec.index_token is None or spec.report_path is None:
        return False
    report_name = Path(spec.report_path).name
    return spec.index_token in index_text or report_name in index_text


def _build_node(
    spec: NodeSpec,
    *,
    repo_root: Path,
    index_text: str,
) -> tuple[GoldenThreadBNode, list[GoldenThreadBGap]]:
    gaps: list[GoldenThreadBGap] = []
    report_exists = False
    report_indexed = False
    validation_evidence = False
    commit_evidence = False
    commit_hash: str | None = None
    gap_reason: str | None = None
    truth_label = spec.truth_label
    evidence_refs: list[GoldenThreadBEvidenceRef] = []

    if spec.node_id == "p2_9_b":
        node = GoldenThreadBNode(
            node_id=spec.node_id,
            title=spec.title,
            roadmap_ref=spec.roadmap_ref,
            node_type=spec.node_type,
            report_path=None,
            report_exists=False,
            report_indexed=False,
            validation_evidence=False,
            commit_evidence=False,
            truth_label=GoldenThreadBTruthLabel.NOT_DONE,
            required=True,
            gap_reason=None,
            next_handoff=spec.next_handoff,
        )
        return node, gaps

    report_path = spec.report_path
    assert report_path is not None
    full_path = repo_root / report_path
    report_text = ""
    if full_path.is_file():
        report_exists = True
        report_text = _read_text(full_path)
    else:
        gaps.append(
            GoldenThreadBGap(
                node_id=spec.node_id,
                severity=GoldenThreadBTruthLabel.GAP,
                reason=f"report missing: {report_path}",
            )
        )
        truth_label = GoldenThreadBTruthLabel.GAP

    report_indexed = _is_indexed(index_text, spec)
    if report_exists and not report_indexed:
        gaps.append(
            GoldenThreadBGap(
                node_id=spec.node_id,
                severity=GoldenThreadBTruthLabel.WARNING,
                reason=f"report not indexed in agent/REPORTS.md: {report_path}",
            )
        )
        if truth_label not in {
            GoldenThreadBTruthLabel.GAP,
            GoldenThreadBTruthLabel.ERROR,
        }:
            truth_label = GoldenThreadBTruthLabel.WARNING

    if report_exists:
        validation_evidence = _has_validation_evidence(report_text)
        if not validation_evidence:
            gaps.append(
                GoldenThreadBGap(
                    node_id=spec.node_id,
                    severity=GoldenThreadBTruthLabel.WARNING,
                    reason="validation evidence markers not found in report",
                )
            )
            if truth_label == GoldenThreadBTruthLabel.DONE_EVIDENCED:
                truth_label = GoldenThreadBTruthLabel.WARNING

        commit_hash = _extract_commit_hash(report_text)
        if commit_hash is not None:
            commit_evidence = True
            evidence_refs.append(
                GoldenThreadBEvidenceRef(
                    ref_kind="commit_hash_report",
                    ref_value=commit_hash,
                    present=True,
                )
            )
        elif spec.git_fallback_commit is not None:
            gaps.append(
                GoldenThreadBGap(
                    node_id=spec.node_id,
                    severity=GoldenThreadBTruthLabel.WARNING,
                    reason=(
                        "commit hash not recorded in report; "
                        f"git fallback {spec.git_fallback_commit} identifiable"
                    ),
                )
            )
            commit_hash = spec.git_fallback_commit
            evidence_refs.append(
                GoldenThreadBEvidenceRef(
                    ref_kind="commit_hash_git_fallback",
                    ref_value=spec.git_fallback_commit,
                    present=True,
                )
            )
        else:
            gaps.append(
                GoldenThreadBGap(
                    node_id=spec.node_id,
                    severity=GoldenThreadBTruthLabel.GAP,
                    reason="commit evidence not recorded in report",
                )
            )
            if truth_label not in {
                GoldenThreadBTruthLabel.GAP,
                GoldenThreadBTruthLabel.ERROR,
            }:
                truth_label = GoldenThreadBTruthLabel.GAP

    if spec.binding_unavailable and report_exists:
        truth_label = GoldenThreadBTruthLabel.CONTRACT_ONLY
        evidence_refs.append(
            GoldenThreadBEvidenceRef(
                ref_kind="binding",
                ref_value="UNAVAILABLE",
                present=True,
            )
        )

    if not report_exists:
        gap_reason = f"report missing: {report_path}"

    node = GoldenThreadBNode(
        node_id=spec.node_id,
        title=spec.title,
        roadmap_ref=spec.roadmap_ref,
        node_type=spec.node_type,
        report_path=report_path,
        report_exists=report_exists,
        report_indexed=report_indexed,
        validation_evidence=validation_evidence,
        commit_evidence=commit_evidence,
        truth_label=truth_label,
        required=spec.required,
        gap_reason=gap_reason,
        next_handoff=spec.next_handoff,
        evidence_refs=tuple(evidence_refs),
        commit_hash=commit_hash,
    )
    return node, gaps


def _verify_golden_thread_a_preserved() -> bool:
    try:
        from agentic_runtime.golden_threads.thread_a import (
            GoldenThreadAHarness,
            GoldenThreadAResult,
        )
    except ImportError:
        return False
    return GoldenThreadAHarness is not None and GoldenThreadAResult is not None


class GoldenThreadBHarness:
    """Assemble governance continuity chain from repo evidence."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        node_specs: Sequence[NodeSpec] = GOLDEN_THREAD_B_NODE_SPECS,
    ) -> None:
        self.repo_root = repo_root or _default_repo_root()
        self.node_specs = tuple(node_specs)

    def assemble(self) -> GoldenThreadBResult:
        index_text = _read_text(self.repo_root / "agent" / "REPORTS.md")
        nodes: list[GoldenThreadBNode] = []
        gaps: list[GoldenThreadBGap] = []

        for spec in self.node_specs:
            node, node_gaps = _build_node(
                spec,
                repo_root=self.repo_root,
                index_text=index_text,
            )
            nodes.append(node)
            gaps.extend(node_gaps)

        golden_thread_a_preserved = _verify_golden_thread_a_preserved()
        if not golden_thread_a_preserved:
            gaps.append(
                GoldenThreadBGap(
                    node_id="golden_thread_a",
                    severity=GoldenThreadBTruthLabel.ERROR,
                    reason="Golden Thread A import surface unavailable",
                )
            )

        side_effect_proof = GoldenThreadBSideEffectProof()
        live_claimed = False
        trace_verified_claimed = False

        p2_9_b_node = next((n for n in nodes if n.node_id == "p2_9_b"), None)
        if p2_9_b_node is not None:
            p2_9_b_status = "NOT_DONE"
            assert p2_9_b_node.truth_label is GoldenThreadBTruthLabel.NOT_DONE
        else:
            p2_9_b_status = "UNKNOWN"

        shell_contract_nodes = [
            n
            for n in nodes
            if n.node_type is GoldenThreadBNodeType.SHELL_CONTRACT
        ]
        shell_contract_only = all(
            n.truth_label
            in {
                GoldenThreadBTruthLabel.CONTRACT_ONLY,
                GoldenThreadBTruthLabel.UNAVAILABLE,
                GoldenThreadBTruthLabel.WARNING,
                GoldenThreadBTruthLabel.GAP,
            }
            for n in shell_contract_nodes
        )

        enf_nodes_present = all(
            n.report_exists
            for n in nodes
            if n.node_id
            in {
                "p1_enf_a",
                "p1_enf_a_omni_r1",
                "p1_enf_b",
                "p1_enf_f_a",
            }
        )

        has_errors = any(g.severity is GoldenThreadBTruthLabel.ERROR for g in gaps)
        has_gaps = any(g.severity is GoldenThreadBTruthLabel.GAP for g in gaps)
        has_warnings = any(g.severity is GoldenThreadBTruthLabel.WARNING for g in gaps)

        continuity_checks = (
            GoldenThreadBContinuityCheck(
                check_id="golden_thread_a_preserved",
                passed=golden_thread_a_preserved,
                detail="Golden Thread A import surface remains available",
            ),
            GoldenThreadBContinuityCheck(
                check_id="p2_shell_contract_only",
                passed=shell_contract_only,
                detail="P2 Shell section nodes remain contract-only",
            ),
            GoldenThreadBContinuityCheck(
                check_id="p2_9_b_not_done",
                passed=p2_9_b_node is not None and p2_9_b_status == "NOT_DONE",
                detail="P2.9-B handoff remains NOT DONE",
            ),
            GoldenThreadBContinuityCheck(
                check_id="no_live_claim",
                passed=not live_claimed,
                detail="Golden Thread B does not claim LIVE",
            ),
            GoldenThreadBContinuityCheck(
                check_id="no_trace_verified_claim",
                passed=not trace_verified_claimed,
                detail="Golden Thread B does not claim TRACE_VERIFIED",
            ),
            GoldenThreadBContinuityCheck(
                check_id="enf_evidence_present",
                passed=enf_nodes_present,
                detail="P1.ENF-A/OMNI-R1/B/F-A report evidence nodes exist",
            ),
            GoldenThreadBContinuityCheck(
                check_id="side_effect_proof",
                passed=side_effect_proof.blocks_product_scope(),
                detail="Side-effect proof blocks product scope expansion",
            ),
        )

        continuity_passed = all(check.passed for check in continuity_checks) and not has_errors

        return GoldenThreadBResult(
            nodes=tuple(nodes),
            continuity_passed=continuity_passed,
            has_errors=has_errors,
            has_gaps=has_gaps,
            has_warnings=has_warnings,
            p2_9_b_status=p2_9_b_status,
            live_claimed=live_claimed,
            trace_verified_claimed=trace_verified_claimed,
            side_effect_proof=side_effect_proof,
            next_recommended_step="P1.ENF-F-B — Roadmap v5.5 Canon Sync / Historical Docs Archive",
            gaps=tuple(gaps),
            continuity_checks=continuity_checks,
            golden_thread_a_preserved=golden_thread_a_preserved,
        )


def evaluate_golden_thread_b(
    *,
    repo_root: Path | None = None,
    node_specs: Sequence[NodeSpec] | None = None,
) -> GoldenThreadBResult:
    harness = GoldenThreadBHarness(
        repo_root=repo_root,
        node_specs=node_specs or GOLDEN_THREAD_B_NODE_SPECS,
    )
    return harness.assemble()


def simulate_missing_report_gap(
    *,
    repo_root: Path,
    missing_report_path: str,
) -> GoldenThreadBGap | None:
    """Test helper: return a GAP if a required report path is absent."""
    if (repo_root / missing_report_path).is_file():
        return None
    return GoldenThreadBGap(
        node_id="simulated",
        severity=GoldenThreadBTruthLabel.GAP,
        reason=f"report missing: {missing_report_path}",
    )


def simulate_missing_commit_gap(*, commit_recorded: bool) -> GoldenThreadBGap | None:
    """Test helper: surface missing commit evidence as GAP."""
    if commit_recorded:
        return None
    return GoldenThreadBGap(
        node_id="simulated",
        severity=GoldenThreadBTruthLabel.GAP,
        reason="commit evidence not recorded in report",
    )
