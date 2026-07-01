"""P2.REVIEW-A first true P2 vertical slice decision harness.

Review/decision gate only: classifies P2.1–P2.9 truth state, compares vertical
slice candidates, selects the first operator-testable slice path, and documents
evidence gaps. Does not implement Shell product behavior, command execution, or
P2.9-B.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence


class P2TruthLabel(str, Enum):
    LIVE = "LIVE"
    TRACE_VERIFIED = "TRACE_VERIFIED"
    SIMULATED = "SIMULATED"
    DEV_FIXTURE = "DEV_FIXTURE"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    NOT_DONE = "NOT_DONE"


class P2VerticalSliceId(str, Enum):
    VSLICE_A = "P2.VSLICE-A"
    VSLICE_A_FALLBACK = "P2.VSLICE-A-FALLBACK"
    PROJECTION_BRIDGE = "P2.VSLICE-C-PROJECTION"
    HANDOFF = "P2.VSLICE-D-HANDOFF"
    SHELL_STATE = "P2.VSLICE-E-SHELL-STATE"


P2_6_OFFICIAL_TITLE = "Surface Projection / API / Event Bridge"
P2_6_DISCARDED_TITLE = "Shell Attention / Notification / Inbox"

P2_VSLICE_A_TITLE = (
    "Governed Command Palette / Global Command Preflight Slice"
)
P2_VSLICE_A_FALLBACK_TITLE = (
    "Global Topbar / Surface Registry Truth Slice"
)

P2_REVIEW_A_REPORT = (
    "agent/reports/P2_REVIEW_A_FIRST_TRUE_P2_VERTICAL_SLICE_DECISION.md"
)


@dataclass(frozen=True)
class P2ReviewSectionRecord:
    section_id: str
    section_title: str
    current_status: str
    truth_label: P2TruthLabel
    backend_capability_present: bool
    contract_schema_present: bool
    projection_read_model_present: bool
    cli_tui_binding_present: bool
    trace_evidence_present: bool
    operator_testable_path_present: bool
    evidence_refs: tuple[str, ...]
    gap_summary: str
    recommended_next_use: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "backend_capability_present": self.backend_capability_present,
            "cli_tui_binding_present": self.cli_tui_binding_present,
            "contract_schema_present": self.contract_schema_present,
            "current_status": self.current_status,
            "evidence_refs": list(self.evidence_refs),
            "gap_summary": self.gap_summary,
            "operator_testable_path_present": self.operator_testable_path_present,
            "projection_read_model_present": self.projection_read_model_present,
            "recommended_next_use": self.recommended_next_use,
            "section_id": self.section_id,
            "section_title": self.section_title,
            "trace_evidence_present": self.trace_evidence_present,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class P2VerticalSliceCandidate:
    candidate_id: str
    title: str
    backend_capability: bool
    contract_schema: bool
    projection_read_model: bool
    cli_tui_binding: bool
    trace_evidence: bool
    operator_testable: bool
    fake_live_risk: str
    sandbox_dependency_risk: str
    broad_rewrite_risk: str
    p29b_value: str
    score_summary: str
    evidence_refs: tuple[str, ...]

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "backend_capability": self.backend_capability,
            "broad_rewrite_risk": self.broad_rewrite_risk,
            "candidate_id": self.candidate_id,
            "cli_tui_binding": self.cli_tui_binding,
            "contract_schema": self.contract_schema,
            "evidence_refs": list(self.evidence_refs),
            "fake_live_risk": self.fake_live_risk,
            "operator_testable": self.operator_testable,
            "p29b_value": self.p29b_value,
            "projection_read_model": self.projection_read_model,
            "sandbox_dependency_risk": self.sandbox_dependency_risk,
            "score_summary": self.score_summary,
            "title": self.title,
            "trace_evidence": self.trace_evidence,
        }


@dataclass(frozen=True)
class P2VerticalSliceEvidenceGap:
    category: str
    gap: str
    blocking: bool

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "blocking": self.blocking,
            "category": self.category,
            "gap": self.gap,
        }


@dataclass(frozen=True)
class P2VerticalSliceDecision:
    chosen_slice_id: P2VerticalSliceId
    chosen_slice_title: str
    fallback_slice_id: P2VerticalSliceId
    fallback_slice_title: str
    rationale: str
    command_listing_support: bool
    command_inspection_support: bool
    command_preflight_support: bool
    truth_label_support: bool
    policy_gate_relationship: str
    identity_gate_relationship: str
    sandbox_gate_relationship: str
    trace_evidence_relationship: str
    operator_testable_path: bool
    claims_execution: bool
    claims_live: bool
    claims_shell_live: bool

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "chosen_slice_id": self.chosen_slice_id.value,
            "chosen_slice_title": self.chosen_slice_title,
            "claims_execution": self.claims_execution,
            "claims_live": self.claims_live,
            "claims_shell_live": self.claims_shell_live,
            "command_inspection_support": self.command_inspection_support,
            "command_listing_support": self.command_listing_support,
            "command_preflight_support": self.command_preflight_support,
            "fallback_slice_id": self.fallback_slice_id.value,
            "fallback_slice_title": self.fallback_slice_title,
            "identity_gate_relationship": self.identity_gate_relationship,
            "operator_testable_path": self.operator_testable_path,
            "policy_gate_relationship": self.policy_gate_relationship,
            "rationale": self.rationale,
            "sandbox_gate_relationship": self.sandbox_gate_relationship,
            "trace_evidence_relationship": self.trace_evidence_relationship,
            "truth_label_support": self.truth_label_support,
        }


@dataclass(frozen=True)
class P2SealReadinessDecision:
    p29b_status: str
    p29b_executed: bool
    rerun_criteria: tuple[str, ...]
    must_consume: tuple[str, ...]
    must_not_claim: tuple[str, ...]

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "must_consume": list(self.must_consume),
            "must_not_claim": list(self.must_not_claim),
            "p29b_executed": self.p29b_executed,
            "p29b_status": self.p29b_status,
            "rerun_criteria": list(self.rerun_criteria),
        }


@dataclass(frozen=True)
class P2ReviewSideEffectProof:
    shell_live_claimed: bool = False
    p2_live_claimed: bool = False
    p29b_marked_done: bool = False
    command_execution_claimed: bool = False
    full_vertical_slice_implemented: bool = False
    p26_attention_inbox_canon: bool = False

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "command_execution_claimed": self.command_execution_claimed,
            "full_vertical_slice_implemented": self.full_vertical_slice_implemented,
            "p26_attention_inbox_canon": self.p26_attention_inbox_canon,
            "p29b_marked_done": self.p29b_marked_done,
            "p2_live_claimed": self.p2_live_claimed,
            "shell_live_claimed": self.shell_live_claimed,
        }


@dataclass(frozen=True)
class P2ReviewResult:
    pack_id: str
    sections: tuple[P2ReviewSectionRecord, ...]
    candidates: tuple[P2VerticalSliceCandidate, ...]
    decision: P2VerticalSliceDecision
    evidence_gaps: tuple[P2VerticalSliceEvidenceGap, ...]
    seal_readiness: P2SealReadinessDecision
    p26_correction_preserved: bool
    p26_official_title: str
    side_effect_proof: P2ReviewSideEffectProof
    p1_enf_a_consumed: bool
    p1_enf_d1_consumed: bool
    p1_enf_e_consumed: bool
    report_path: str

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "candidates": [c.to_canonical_dict() for c in self.candidates],
            "decision": self.decision.to_canonical_dict(),
            "evidence_gaps": [g.to_canonical_dict() for g in self.evidence_gaps],
            "p1_enf_a_consumed": self.p1_enf_a_consumed,
            "p1_enf_d1_consumed": self.p1_enf_d1_consumed,
            "p1_enf_e_consumed": self.p1_enf_e_consumed,
            "p26_correction_preserved": self.p26_correction_preserved,
            "p26_official_title": self.p26_official_title,
            "pack_id": self.pack_id,
            "report_path": self.report_path,
            "seal_readiness": self.seal_readiness.to_canonical_dict(),
            "sections": [s.to_canonical_dict() for s in self.sections],
            "side_effect_proof": self.side_effect_proof.to_canonical_dict(),
        }


def _exists(repo_root: Path, rel_path: str) -> bool:
    return (repo_root / rel_path).is_file()


def _section_specs() -> tuple[Mapping[str, object], ...]:
    return (
        {
            "section_id": "P2.1",
            "section_title": "Global Topbar / Surface Registry",
            "current_status": "SEALED_FOR_P2_1_CONTRACT_SCOPE",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": True,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_1_A_GLOBAL_TOPBAR_SURFACE_REGISTRY.md",
                "agent/reports/P2_1_D_TOPBAR_INTEGRATION_TAIL.md",
                "src/agentic_runtime/aurel_shell/topbar_surface_registry.py",
                "tests/aurel_shell/test_shell_topbar_surface_registry.py",
            ),
            "gap_summary": (
                "Topbar/registry is contract/read-model only; CLI inspect "
                "contract exists but no live surface switcher or product UI."
            ),
            "recommended_next_use": "Fallback vertical slice (P2.VSLICE-A-FALLBACK).",
        },
        {
            "section_id": "P2.2",
            "section_title": "Per-Surface Local Navigation",
            "current_status": "SEALED_FOR_P2_2_CONTRACT_SCOPE",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": True,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_2_A_LOCAL_NAVIGATION_FOUNDATION.md",
                "agent/reports/P2_2_D_LOCAL_NAVIGATION_INTEGRATION_TAIL.md",
                "src/agentic_runtime/aurel_shell/local_navigation.py",
            ),
            "gap_summary": "Local nav contracts only; no sidebar UI or route runtime.",
            "recommended_next_use": "Support layer for multi-surface slice later.",
        },
        {
            "section_id": "P2.3",
            "section_title": "Floating Windows / Workspace State",
            "current_status": "SEALED_FOR_CONTRACT_SCOPE",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_3_A_WORKSPACE_STATE_FOUNDATION.md",
                "agent/reports/P2_3_D_WORKSPACE_WINDOW_SECTION_SEAL.md",
                "src/agentic_runtime/aurel_shell/workspace_window_section_projection.py",
            ),
            "gap_summary": "Window/workspace semantics are read-model only; no UI/docking runtime.",
            "recommended_next_use": "Later handoff/window slice dependency.",
        },
        {
            "section_id": "P2.4",
            "section_title": "Command Palette / Global Commands",
            "current_status": "SEALED_CONTRACT_SCOPE",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_4_A_COMMAND_PALETTE_GLOBAL_COMMANDS_FOUNDATION.md",
                "agent/reports/P2_4_D_COMMAND_PALETTE_SECTION_SEAL.md",
                "src/agentic_runtime/aurel_shell/global_command_registry.py",
                "src/agentic_runtime/aurel_shell/global_command_discovery.py",
                "src/agentic_runtime/aurel_shell/global_command_proposal.py",
                "tests/aurel_shell/test_shell_global_command_registry.py",
                "tests/aurel_shell/test_shell_global_command_discovery.py",
                "tests/aurel_shell/test_shell_global_command_proposal.py",
            ),
            "gap_summary": (
                "Registry, discovery, proposal, and no-execution boundary exist; "
                "no command palette UI, no runtime command execution, no governed "
                "preflight bridge to runtime.submit yet."
            ),
            "recommended_next_use": "Primary spine for P2.VSLICE-A.",
        },
        {
            "section_id": "P2.5",
            "section_title": "Cross-Surface Handoff",
            "current_status": "SEALED_CONTRACT_SCOPE",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_5_A_CROSS_SURFACE_HANDOFF_FOUNDATION.md",
                "agent/reports/P2_5_D_HANDOFF_SECTION_SEAL.md",
                "src/agentic_runtime/aurel_shell/cross_surface_handoff.py",
            ),
            "gap_summary": "Handoff intent/contracts only; requires window/UI state for true E2E.",
            "recommended_next_use": "Later candidate, not first slice.",
        },
        {
            "section_id": "P2.6",
            "section_title": P2_6_OFFICIAL_TITLE,
            "current_status": "SEALED_CONTRACT_ONLY",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_6_A_SURFACE_PROJECTION_API_EVENT_FOUNDATION.md",
                "agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md",
                "src/agentic_runtime/aurel_shell/surface_projection_foundation.py",
                "tests/aurel_shell/test_shell_surface_projection_foundation.py",
            ),
            "gap_summary": (
                "Projection/API/event bridge contracts only; no API server, event bus, "
                "or live bridge consumption."
            ),
            "recommended_next_use": "Projection spine for command availability read model.",
        },
        {
            "section_id": "P2.7",
            "section_title": "Shell / CLI / TUI Binding",
            "current_status": "SEALED_CONTRACT_ONLY",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_7_A_SHELL_CLI_TUI_BINDING_FOUNDATION.md",
                "agent/reports/P2_7_D_SHELL_CLI_TUI_BINDING_SECTION_SEAL.md",
                "src/agentic_runtime/aurel_shell/shell_binding_foundation.py",
            ),
            "gap_summary": (
                "Binding descriptors and read models only; TUI UNAVAILABLE; "
                "no CLI runner or Shell execution runtime."
            ),
            "recommended_next_use": "Operator inspect binding target for P2.VSLICE-A.",
        },
        {
            "section_id": "P2.8",
            "section_title": "Shell State / Reports / Docs",
            "current_status": "SEALED_CONTRACT_ONLY",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": True,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_8_A_SHELL_STATE_REPORTS_DOCS_FOUNDATION.md",
                "agent/reports/P2_8_D_SHELL_STATE_REPORTS_DOCS_SECTION_SEAL.md",
                "src/agentic_runtime/aurel_shell/shell_state_foundation.py",
            ),
            "gap_summary": "Shell state read models and report index contracts; not live Shell state.",
            "recommended_next_use": "Evidence/report sync support for slice and P2.9-B.",
        },
        {
            "section_id": "P2.9-A",
            "section_title": "Shell Exit Seal Foundation",
            "current_status": "DONE",
            "truth_label": P2TruthLabel.CONTRACT_ONLY,
            "backend": False,
            "contract": True,
            "projection": False,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md",
                "src/agentic_runtime/aurel_shell/shell_exit_seal_foundation.py",
            ),
            "gap_summary": "Foundation gate and handoff contract only; not validation execution.",
            "recommended_next_use": "P2.9-B consumes vertical-slice decision before rerun.",
        },
        {
            "section_id": "P2.9-A-R1",
            "section_title": "Shell Exit Seal Foundation Evidence Ref Repair",
            "current_status": "DONE",
            "truth_label": P2TruthLabel.TRACE_VERIFIED,
            "backend": False,
            "contract": True,
            "projection": False,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_9_A_R1_SHELL_EXIT_SEAL_FOUNDATION_EVIDENCE_REF_REPAIR.md",
                "tests/aurel_shell/test_shell_exit_seal_foundation_evidence_refs.py",
            ),
            "gap_summary": "Evidence-ref integrity repair only; scoped to ref/test truth not runtime LIVE.",
            "recommended_next_use": "Preflight hygiene for P2.9-B rerun.",
        },
        {
            "section_id": "P2.9-B",
            "section_title": "Shell Exit Seal Readiness / Validation / Evidence Matrix",
            "current_status": "NOT DONE",
            "truth_label": P2TruthLabel.NOT_DONE,
            "backend": False,
            "contract": False,
            "projection": False,
            "cli_tui": False,
            "trace": False,
            "operator": False,
            "evidence_refs": (
                "agent/reports/P2_9_A_SHELL_EXIT_SEAL_FOUNDATION.md",
                "src/agentic_runtime/aurel_shell/shell_exit_seal_foundation.py",
            ),
            "gap_summary": (
                "Blocked until first true vertical slice is selected and evidence "
                "gaps documented; must not claim P2 LIVE or Shell product complete."
            ),
            "recommended_next_use": "Rerun after P2.VSLICE-A implementation evidence exists.",
        },
    )


def build_p2_section_records(
    repo_root: Path | None = None,
) -> tuple[P2ReviewSectionRecord, ...]:
    root = repo_root or Path.cwd()
    records: list[P2ReviewSectionRecord] = []
    for spec in _section_specs():
        raw_refs = spec["evidence_refs"]
        assert isinstance(raw_refs, tuple)
        refs = tuple(str(r) for r in raw_refs)
        present_refs = tuple(r for r in refs if _exists(root, r))
        truth_label = spec["truth_label"]
        assert isinstance(truth_label, P2TruthLabel)
        records.append(
            P2ReviewSectionRecord(
                section_id=str(spec["section_id"]),
                section_title=str(spec["section_title"]),
                current_status=str(spec["current_status"]),
                truth_label=truth_label,
                backend_capability_present=bool(spec["backend"]),
                contract_schema_present=bool(spec["contract"])
                and len(present_refs) > 0,
                projection_read_model_present=bool(spec["projection"]),
                cli_tui_binding_present=bool(spec["cli_tui"]),
                trace_evidence_present=bool(spec["trace"]),
                operator_testable_path_present=bool(spec["operator"]),
                evidence_refs=present_refs if present_refs else refs,
                gap_summary=str(spec["gap_summary"]),
                recommended_next_use=str(spec["recommended_next_use"]),
            )
        )
    return tuple(records)


def build_p2_vertical_slice_candidates() -> tuple[P2VerticalSliceCandidate, ...]:
    return (
        P2VerticalSliceCandidate(
            candidate_id="A",
            title=P2_VSLICE_A_FALLBACK_TITLE,
            backend_capability=False,
            contract_schema=True,
            projection_read_model=True,
            cli_tui_binding=True,
            trace_evidence=False,
            operator_testable=False,
            fake_live_risk="LOW",
            sandbox_dependency_risk="LOW",
            broad_rewrite_risk="LOW",
            p29b_value="MEDIUM — truth labels only, passive",
            score_summary=(
                "Strong contract base (P2.1), read-only CLI inspect contract, "
                "low fake-LIVE risk; too passive for first command-path proof."
            ),
            evidence_refs=(
                "src/agentic_runtime/aurel_shell/topbar_surface_registry.py",
                "agent/reports/P2_1_D_TOPBAR_INTEGRATION_TAIL.md",
            ),
        ),
        P2VerticalSliceCandidate(
            candidate_id="B",
            title=P2_VSLICE_A_TITLE,
            backend_capability=True,
            contract_schema=True,
            projection_read_model=True,
            cli_tui_binding=False,
            trace_evidence=False,
            operator_testable=False,
            fake_live_risk="MEDIUM — must not claim execution",
            sandbox_dependency_risk="MEDIUM — preflight must show sandbox gate",
            broad_rewrite_risk="LOW — builds on P2.4 + P1.ENF chain",
            p29b_value="HIGH — binds governance, identity, sandbox, command path",
            score_summary=(
                "Best operator value: P2.4 registry/discovery/proposal + "
                "P1.ENF-A/D1/E runtime gates can support governed preflight "
                "without product UI or command execution."
            ),
            evidence_refs=(
                "src/agentic_runtime/aurel_shell/global_command_registry.py",
                "src/agentic_runtime/governance_enforcement.py",
                "src/agentic_runtime/identity_invariant_enforcement.py",
                "src/agentic_runtime/sandbox_backend_gate.py",
            ),
        ),
        P2VerticalSliceCandidate(
            candidate_id="C",
            title="Surface Projection / API / Event Bridge Slice",
            backend_capability=False,
            contract_schema=True,
            projection_read_model=True,
            cli_tui_binding=False,
            trace_evidence=False,
            operator_testable=False,
            fake_live_risk="LOW",
            sandbox_dependency_risk="LOW",
            broad_rewrite_risk="MEDIUM",
            p29b_value="MEDIUM — projection spine, read-only",
            score_summary=(
                "Aligns with P2.6 correction but read-only; does not prove "
                "operator command lifecycle."
            ),
            evidence_refs=(
                "src/agentic_runtime/aurel_shell/surface_projection_foundation.py",
                "agent/reports/P2_6_D_SURFACE_PROJECTION_API_EVENT_SECTION_SEAL.md",
            ),
        ),
        P2VerticalSliceCandidate(
            candidate_id="D",
            title="Cross-Surface Handoff Slice",
            backend_capability=False,
            contract_schema=True,
            projection_read_model=True,
            cli_tui_binding=False,
            trace_evidence=False,
            operator_testable=False,
            fake_live_risk="HIGH — multi-surface UI temptation",
            sandbox_dependency_risk="LOW",
            broad_rewrite_risk="HIGH",
            p29b_value="LOW for first slice",
            score_summary="Requires too much window/UI state too early.",
            evidence_refs=(
                "src/agentic_runtime/aurel_shell/cross_surface_handoff.py",
            ),
        ),
        P2VerticalSliceCandidate(
            candidate_id="E",
            title="Shell State / Reports / Docs Slice",
            backend_capability=False,
            contract_schema=True,
            projection_read_model=True,
            cli_tui_binding=False,
            trace_evidence=False,
            operator_testable=False,
            fake_live_risk="LOW",
            sandbox_dependency_risk="LOW",
            broad_rewrite_risk="LOW",
            p29b_value="LOW — docs/reporting adjacent",
            score_summary="Safe evidence layer but not enough as first true slice.",
            evidence_refs=(
                "src/agentic_runtime/aurel_shell/shell_state_foundation.py",
            ),
        ),
    )


def build_p2_vertical_slice_evidence_gaps() -> tuple[P2VerticalSliceEvidenceGap, ...]:
    return (
        P2VerticalSliceEvidenceGap(
            category="backend_capability",
            gap=(
                "No Shell command router or runtime command handler; "
                "runtime.submit exists for tool dispatch only."
            ),
            blocking=False,
        ),
        P2VerticalSliceEvidenceGap(
            category="contract_schema",
            gap=(
                "P2.4 command registry/discovery/proposal contracts exist; "
                "governed preflight envelope not yet wired to runtime.submit."
            ),
            blocking=True,
        ),
        P2VerticalSliceEvidenceGap(
            category="projection_read_model",
            gap=(
                "Command availability projection must compose P2.4 read models "
                "with P2.6 projection descriptors and P1.ENF gate summaries."
            ),
            blocking=True,
        ),
        P2VerticalSliceEvidenceGap(
            category="cli_tui_binding",
            gap=(
                "P2.7 binding section is CONTRACT_ONLY; need read-only CLI "
                "inspect for command list/preflight without TUI or product UI."
            ),
            blocking=True,
        ),
        P2VerticalSliceEvidenceGap(
            category="trace_evidence",
            gap="No TRACE_VERIFIED operator path for Shell commands.",
            blocking=False,
        ),
        P2VerticalSliceEvidenceGap(
            category="policy_identity_sandbox_gates",
            gap=(
                "P1.ENF-A/D1/E runtime gates exist but are not yet exposed through "
                "a Shell command preflight read model."
            ),
            blocking=True,
        ),
        P2VerticalSliceEvidenceGap(
            category="operator_testability",
            gap=(
                "First slice must be operator-testable via CLI inspect + pytest "
                "without claiming LIVE or command execution."
            ),
            blocking=True,
        ),
        P2VerticalSliceEvidenceGap(
            category="truth_labels",
            gap=(
                "P2.0-D truth label contracts exist; slice must attach labels "
                "per command/preflight outcome."
            ),
            blocking=False,
        ),
        P2VerticalSliceEvidenceGap(
            category="p29b_seal",
            gap=(
                "P2.9-B remains NOT DONE until vertical slice evidence satisfies "
                "rerun criteria."
            ),
            blocking=True,
        ),
    )


def build_p2_vertical_slice_decision() -> P2VerticalSliceDecision:
    return P2VerticalSliceDecision(
        chosen_slice_id=P2VerticalSliceId.VSLICE_A,
        chosen_slice_title=P2_VSLICE_A_TITLE,
        fallback_slice_id=P2VerticalSliceId.VSLICE_A_FALLBACK,
        fallback_slice_title=P2_VSLICE_A_FALLBACK_TITLE,
        rationale=(
            "Repo evidence supports P2.4 command listing, discovery, proposal, "
            "and explicit no-execution boundaries plus P1.ENF-A/D1/E runtime "
            "submit gates without broad Shell rewrite or fake LIVE claims. "
            "Command preflight is the honest first operator-testable path."
        ),
        command_listing_support=True,
        command_inspection_support=True,
        command_preflight_support=True,
        truth_label_support=True,
        policy_gate_relationship=(
            "Consume P1.ENF-A policy resolver submit influence in preflight artifact; "
            "do not bypass ENFORCE_FAIL_CLOSED."
        ),
        identity_gate_relationship=(
            "Consume P1.ENF-D1 identity invariant decisions in preflight artifact; "
            "surface IK-002/005/006/007 outcomes."
        ),
        sandbox_gate_relationship=(
            "Consume P1.ENF-E sandbox backend gate; SAFE_VERIFIED remains UNAVAILABLE; "
            "show UNSAFE_LOCAL/DEV_FIXTURE truth honestly."
        ),
        trace_evidence_relationship=(
            "Artifact refs only; do not claim TRACE_VERIFIED without trace proof."
        ),
        operator_testable_path=False,
        claims_execution=False,
        claims_live=False,
        claims_shell_live=False,
    )


def build_p2_seal_readiness_decision() -> P2SealReadinessDecision:
    return P2SealReadinessDecision(
        p29b_status="NOT DONE",
        p29b_executed=False,
        rerun_criteria=(
            "P2.REVIEW-A report exists and is indexed",
            "First true vertical slice selected with fallback documented",
            "P2 section truth matrix and evidence gap matrix present",
            "P1.ENF-A/D1/E chain referenced in slice criteria",
            "P2.6 Surface Projection correction preserved",
            "P2.VSLICE-A implementation evidence or honest fallback criteria met",
        ),
        must_consume=(
            P2_REVIEW_A_REPORT,
            "P2.VSLICE-A decision and evidence gaps",
            "P2.9-B NOT DONE status",
            "agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md",
            "agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md",
            "agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md",
        ),
        must_not_claim=(
            "P2 LIVE",
            "Shell product complete",
            "command execution if only preflight exists",
            "safe sandbox if SAFE_VERIFIED unavailable",
            "TRACE_VERIFIED without trace evidence",
        ),
    )


def evaluate_p2_vertical_slice_review(
    repo_root: Path | None = None,
) -> P2ReviewResult:
    root = repo_root or Path.cwd()
    sections = build_p2_section_records(root)
    candidates = build_p2_vertical_slice_candidates()
    decision = build_p2_vertical_slice_decision()
    gaps = build_p2_vertical_slice_evidence_gaps()
    seal = build_p2_seal_readiness_decision()

    p26_section = next(s for s in sections if s.section_id == "P2.6")
    p26_preserved = p26_section.section_title == P2_6_OFFICIAL_TITLE

    enf_a = _exists(
        root,
        "agent/reports/P1_ENF_A_POLICY_IDENTITY_ENTRYPOINT_ENFORCEMENT_VERTICAL.md",
    )
    enf_d1 = _exists(
        root,
        "agent/reports/P1_ENF_D1_IDENTITY_KERNEL_INVARIANT_ENFORCEMENT_DEEPENING.md",
    )
    enf_e = _exists(
        root,
        "agent/reports/P1_ENF_E_SANDBOX_SAFE_BACKEND_GATING_UNSAFE_LOCAL_HARDENING.md",
    )

    return P2ReviewResult(
        pack_id="P2.REVIEW-A",
        sections=sections,
        candidates=candidates,
        decision=decision,
        evidence_gaps=gaps,
        seal_readiness=seal,
        p26_correction_preserved=p26_preserved,
        p26_official_title=P2_6_OFFICIAL_TITLE,
        side_effect_proof=P2ReviewSideEffectProof(),
        p1_enf_a_consumed=enf_a,
        p1_enf_d1_consumed=enf_d1,
        p1_enf_e_consumed=enf_e,
        report_path=P2_REVIEW_A_REPORT,
    )
