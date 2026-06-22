"""P1.4 seal readiness helper — read-only consolidation.

Summarizes P1.4 module/report/test/CLI readiness before P1.4.20 exit seal.
Does NOT grant authority, mutate state, execute tools, or create artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class P14ModuleStatus:
    module_id: str
    name: str
    status: str  # IMPLEMENTED, VERIFIED, PARTIAL, MISSING
    report_path: str | None
    test_paths: tuple[str, ...]
    cli_groups: tuple[str, ...]
    known_limitations: tuple[str, ...]


@dataclass(frozen=True)
class P14SealReadinessReport:
    status: str  # READY, BLOCKED, UNKNOWN
    modules: tuple[P14ModuleStatus, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    next_module: str  # P1.4.20
    summary: str


# ---------------------------------------------------------------------------
# Known P1.4 module inventory (P1.4.8 – P1.4.20)
# ---------------------------------------------------------------------------

_P14_MODULES: tuple[P14ModuleStatus, ...] = (
    P14ModuleStatus(
        module_id="P1.4.8",
        name="Autonomy Scale Engine",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.8_AUTONOMY_SCALE_ENGINE.md",
        test_paths=("tests/identity/test_autonomy_scale_engine.py",),
        cli_groups=("identity autonomy",),
        known_limitations=(
            "Autonomy is action-scoped, not global",
            "A7 denial is not counted as high autonomy",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.9",
        name="Measured Autonomy Score",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.9_MEASURED_AUTONOMY_SCORE.md",
        test_paths=("tests/identity/test_autonomy_measurement.py",),
        cli_groups=("identity autonomy",),
        known_limitations=(
            "Measured autonomy is evidence-backed, not a hype score",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.10",
        name="Capability Claim Boundary Engine",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.10_CAPABILITY_CLAIM_BOUNDARY_ENGINE.md",
        test_paths=("tests/test_capability_claim_boundary.py",),
        cli_groups=("identity claims",),
        known_limitations=(
            "Capability claims require evidence",
            "Does not implement full capability enforcement",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.11",
        name="External Doctrine Assimilation Registry",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.11_EXTERNAL_DOCTRINE_ASSIMILATION_REGISTRY.md",
        test_paths=(
            "tests/identity/test_doctrine_attestation.py",
            "tests/identity/test_p1411_doctrine_smoke.py",
            "tests/test_external_doctrine_registry.py",
        ),
        cli_groups=("identity doctrine",),
        known_limitations=(
            "External doctrine cannot grant capability",
            "Doctrine boundary enforcement is claim-time, not runtime",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.12",
        name="Raw Source + Canonical Hash Attestation",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.12_RAW_SOURCE_CANONICAL_HASH_ATTESTATION.md",
        test_paths=(
            "tests/identity/test_source_attestation.py",
            "tests/identity/test_source_attestation_cli.py",
            "tests/identity/test_source_attestation_seal.py",
            "tests/identity/test_source_hashing.py",
        ),
        cli_groups=("identity attestation",),
        known_limitations=(
            "Raw source hash and canonical typed hash are distinct",
            "Valid source does not imply safe authority change",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.13",
        name="Authority Delta Detector",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.13_AUTHORITY_DELTA_DETECTOR.md",
        test_paths=(
            "tests/identity/test_authority_delta.py",
            "tests/identity/test_authority_delta_cli.py",
            "tests/identity/test_authority_delta_seal.py",
        ),
        cli_groups=("identity authority-delta",),
        known_limitations=(
            "Valid source can still require consent",
            "Detects deltas, does not enforce or block them",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.14",
        name="Operator Consent Binding",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.14_OPERATOR_CONSENT_BINDING.md",
        test_paths=(
            "tests/identity/test_operator_consent.py",
            "tests/identity/test_operator_consent_cli.py",
            "tests/identity/test_operator_consent_seal.py",
        ),
        cli_groups=("identity consent",),
        known_limitations=(
            "Consent is delta-bound, not global",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.15",
        name="Identity Governance Command Surface",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.15_IDENTITY_GOVERNANCE_COMMAND_SURFACE.md",
        test_paths=(
            "tests/identity/test_identity_cli_surface.py",
            "tests/identity/test_identity_cli_routing.py",
            "tests/identity/test_identity_cli_seal.py",
        ),
        cli_groups=("identity status", "identity verify"),
        known_limitations=(
            "Command surface does not create authority",
            "Command surface is not interactive agent terminal",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.16",
        name="Identity Test Battery",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.16_IDENTITY_TEST_BATTERY.md",
        test_paths=(
            "tests/identity/test_identity_test_battery.py",
            "tests/identity/test_identity_test_battery_seal.py",
        ),
        cli_groups=("identity test-battery",),
        known_limitations=(
            "Test battery tests integrated chain, not only isolated modules",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.17",
        name="Agent Lifecycle Eligibility State Machine",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.17_AGENT_LIFECYCLE_ELIGIBILITY_STATE_MACHINE.md",
        test_paths=(
            "tests/identity/test_agent_lifecycle.py",
            "tests/identity/test_agent_lifecycle_seal.py",
        ),
        cli_groups=("identity lifecycle",),
        known_limitations=(
            "Lifecycle is eligibility layer, not permission engine",
            "Lifecycle state does not grant authority",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.18",
        name="Trust Evidence Linkage",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.18_TRUST_EVIDENCE_LINKAGE.md",
        test_paths=(
            "tests/identity/test_trust_evidence.py",
            "tests/identity/test_trust_evidence_seal.py",
        ),
        cli_groups=("identity trust-evidence",),
        known_limitations=(
            "Trust posture is categorical, not numeric score",
            "Evidence refs are not truth by themselves",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.19",
        name="Identity Docs / Reports / State Update",
        status="IMPLEMENTED",
        report_path="agent/reports/P1.4.19_IDENTITY_DOCS_REPORTS_STATE_UPDATE.md",
        test_paths=("tests/identity/test_p1419_anti_overclaim.py",),
        cli_groups=("identity seal-readiness",),
        known_limitations=(
            "P1.4.19 is consolidation, not new governance semantics",
            "Docs must not overclaim capability",
        ),
    ),
    P14ModuleStatus(
        module_id="P1.4.20",
        name="P1.4 Identity & Autonomy Exit Seal",
        status="PENDING",
        report_path=None,
        test_paths=(),
        cli_groups=(),
        known_limitations=("Not yet implemented",),
    ),
)


# ---------------------------------------------------------------------------
# P1.4 invariant index
# ---------------------------------------------------------------------------

P14_INVARIANTS: tuple[str, ...] = (
    "P1.4-INV-01: Identity config must fail closed on authority uncertainty.",
    "P1.4-INV-02: Autonomy is action-scoped, not global.",
    "P1.4-INV-03: A7 denial is not high autonomy.",
    "P1.4-INV-04: Measured autonomy is evidence-backed, not a hype score.",
    "P1.4-INV-05: Capability claims require evidence.",
    "P1.4-INV-06: External doctrine cannot grant capability.",
    "P1.4-INV-07: Raw source hash and canonical typed hash are distinct.",
    "P1.4-INV-08: Valid source does not imply safe authority change.",
    "P1.4-INV-09: Consent is delta-bound, not global.",
    "P1.4-INV-10: Command surface does not create authority.",
    "P1.4-INV-11: Test battery must include adversarial governance cases.",
    "P1.4-INV-12: Lifecycle state does not grant authority.",
    "P1.4-INV-13: Lifecycle is eligibility, not permission.",
    "P1.4-INV-14: Trust evidence refs are not truth by themselves.",
    "P1.4-INV-15: Trust posture is categorical, not numeric score.",
)

# P1.4.19-specific invariants
P1419_INVARIANTS: tuple[str, ...] = (
    "INV-P1419-01: P1.4.19 is consolidation, not new governance semantics.",
    "INV-P1419-02: Docs must not overclaim capability.",
    "INV-P1419-03: Known limitations must be explicit.",
    "INV-P1419-04: P1.4 module index must include P1.4.8–P1.4.20.",
    "INV-P1419-05: P1.4.20 seal checklist must exist.",
    "INV-P1419-06: Roadmap numbering constitution must be preserved.",
    "INV-P1419-07: Command surface vs interactive CLI distinction must be documented.",
    "INV-P1419-08: Lifecycle eligibility vs runtime permission distinction must be documented.",
    "INV-P1419-09: Trust evidence linkage vs truth distinction must be documented.",
    "INV-P1419-10: P1.4.19 prepares P1.4.20 and does not replace it.",
)


# ---------------------------------------------------------------------------
# P1.4 CLI command index
# ---------------------------------------------------------------------------

P14_CLI_GROUPS: tuple[dict[str, str], ...] = (
    {"group": "identity status", "purpose": "Show overall identity governance status", "read_only": "true", "module": "P1.4.15"},
    {"group": "identity verify", "purpose": "Run non-destructive identity governance checks", "read_only": "true", "module": "P1.4.15"},
    {"group": "identity kernel", "purpose": "Identity kernel operations", "read_only": "true", "module": "P1.4.1"},
    {"group": "identity persona", "purpose": "Persona manifest operations", "read_only": "true", "module": "P1.4.2"},
    {"group": "identity operator-contract", "purpose": "Operator relationship contract operations", "read_only": "true", "module": "P1.4.3"},
    {"group": "identity modes", "purpose": "Communication modes registry operations", "read_only": "true", "module": "P1.4.4"},
    {"group": "identity context", "purpose": "Identity prompt context compiler operations", "read_only": "true", "module": "P1.4.5"},
    {"group": "identity card", "purpose": "Agent identity card operations", "read_only": "true", "module": "P1.4.7"},
    {"group": "identity self", "purpose": "Self-model operations", "read_only": "true", "module": "P1.4.6"},
    {"group": "identity autonomy", "purpose": "Autonomy scale engine (P1.4.8)", "read_only": "true", "module": "P1.4.8"},
    {"group": "identity claims", "purpose": "Capability claim boundary engine (P1.4.10)", "read_only": "true", "module": "P1.4.10"},
    {"group": "identity doctrine", "purpose": "External doctrine assimilation registry (P1.4.11)", "read_only": "true", "module": "P1.4.11"},
    {"group": "identity attestation", "purpose": "Raw source + canonical hash attestation (P1.4.12)", "read_only": "true", "module": "P1.4.12"},
    {"group": "identity authority-delta", "purpose": "Detect authority-relevant deltas (P1.4.13)", "read_only": "true", "module": "P1.4.13"},
    {"group": "identity consent", "purpose": "Operator consent binding (P1.4.14)", "read_only": "false", "module": "P1.4.14"},
    {"group": "identity test-battery", "purpose": "Identity test battery (P1.4.16)", "read_only": "true", "module": "P1.4.16"},
    {"group": "identity lifecycle", "purpose": "Identity lifecycle state machine (P1.4.17)", "read_only": "true", "module": "P1.4.17"},
    {"group": "identity trust-evidence", "purpose": "Trust evidence linkage (P1.4.18)", "read_only": "true", "module": "P1.4.18"},
    {"group": "identity seal-readiness", "purpose": "P1.4 exit seal readiness summary (P1.4.19)", "read_only": "true", "module": "P1.4.19"},
)


# ---------------------------------------------------------------------------
# P1.4 known limitations
# ---------------------------------------------------------------------------

P14_KNOWN_LIMITATIONS: tuple[str, ...] = (
    "1. P1.4 is not full runtime policy enforcement.",
    "2. P1.4 does not implement P1.5 Evaluation Mirror.",
    "3. P1.4 does not implement P1.6 Policy Cards.",
    "4. P1.4 does not implement P1.8 Delegation Mesh.",
    "5. P1.4 does not implement P3 Mneme Memory Graph.",
    "6. P1.4 does not implement P6 Custos v2 runtime enforcement.",
    "7. P1.4 does not implement P7 Forge tool runtime binding.",
    "8. P1.4 does not implement full cryptographic signing / key management.",
    "9. P1.4 does not make Aurel production-ready.",
    "10. P1.4 does not prove full autonomy.",
    "11. P1.4 does not train or fine-tune models.",
    "12. P1.4 does not implement ABOS as a runtime system unless specific code exists.",
    "13. P1.4 does not implement AETHER as a runtime system unless specific code exists.",
    "14. P1.4 command surface is not a full interactive terminal agent.",
    "15. P1.4 lifecycle is not runtime execution status.",
)


# ---------------------------------------------------------------------------
# P1.4.20 seal readiness checklist
# ---------------------------------------------------------------------------

P1420_SEAL_CHECKLIST: tuple[str, ...] = (
    "all P1.4 modules import",
    "all P1.4 reports exist or missing reports are explicitly flagged",
    "all P1.4 CLI groups respond or unavailable groups are explicitly flagged",
    "identity verify passes or reports clear blockers",
    "identity test-battery runs",
    "lifecycle cannot grant authority",
    "trust evidence cannot grant authority",
    "trust posture is categorical, not numeric",
    "claim overreach is blocked",
    "doctrine cannot grant capability",
    "authority delta requires consent",
    "consent is delta-bound",
    "valid source can still require consent",
    "raw/canonical hash distinction is preserved",
    "A7 denial is not counted as high autonomy",
    "unknown authority fields fail closed",
    "docs do not claim full autonomy",
    "docs do not claim production readiness",
    "docs do not claim self-improvement",
    "docs do not claim ABOS/AETHER implementation without code evidence",
    "roadmap numbering constitution is preserved",
    "STATE/ROADMAP/TESTS/REPORTS/ARCHITECTURE/DECISIONS are current",
)


# ---------------------------------------------------------------------------
# Engine functions
# ---------------------------------------------------------------------------


def build_p14_seal_readiness_report() -> P14SealReadinessReport:
    """Build a read-only seal readiness summary. Does NOT mutate anything."""
    blockers: list[str] = []
    warnings: list[str] = []

    for mod in _P14_MODULES:
        if mod.status == "MISSING":
            blockers.append(f"Module {mod.module_id} ({mod.name}) is MISSING")
        elif mod.status == "PARTIAL":
            warnings.append(f"Module {mod.module_id} ({mod.name}) is PARTIAL")
        if mod.report_path is None and mod.status != "PENDING":
            warnings.append(f"Module {mod.module_id} has no report path")

    if not blockers:
        status = "READY"
    else:
        status = "BLOCKED"

    return P14SealReadinessReport(
        status=status,
        modules=_P14_MODULES,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        next_module="P1.4.20",
        summary=f"P1.4 seal readiness: {status}. "
                f"{len(_P14_MODULES)} modules tracked. "
                f"Next: P1.4.20.",
    )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def p14_module_status_to_dict(status: P14ModuleStatus) -> dict[str, object]:
    return {
        "module_id": status.module_id,
        "name": status.name,
        "status": status.status,
        "report_path": status.report_path,
        "test_paths": list(status.test_paths),
        "cli_groups": list(status.cli_groups),
        "known_limitations": list(status.known_limitations),
    }


def p14_seal_readiness_report_to_dict(report: P14SealReadinessReport) -> dict[str, object]:
    return {
        "status": report.status,
        "modules": [p14_module_status_to_dict(m) for m in report.modules],
        "blockers": list(report.blockers),
        "warnings": list(report.warnings),
        "next_module": report.next_module,
        "summary": report.summary,
    }


def format_p14_seal_readiness_human(report: P14SealReadinessReport) -> str:
    lines = [
        f"P1.4 Seal Readiness: {report.status}",
        f"  Modules: {len(report.modules)}",
        f"  Blockers: {len(report.blockers)}",
        f"  Warnings: {len(report.warnings)}",
        f"  Next: {report.next_module}",
    ]
    if report.blockers:
        lines.append("")
        lines.append("Blockers:")
        for b in report.blockers:
            lines.append(f"  - {b}")
    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f"  - {w}")
    lines.append("")
    for mod in report.modules:
        lines.append(f"  {mod.module_id} {mod.status:12s} {mod.name}")
    lines.append("")
    lines.append(report.summary)
    return "\n".join(lines)


__all__ = [
    "P14ModuleStatus",
    "P14SealReadinessReport",
    "P14_CLI_GROUPS",
    "P14_INVARIANTS",
    "P1419_INVARIANTS",
    "P14_KNOWN_LIMITATIONS",
    "P1420_SEAL_CHECKLIST",
    "build_p14_seal_readiness_report",
    "p14_module_status_to_dict",
    "p14_seal_readiness_report_to_dict",
    "format_p14_seal_readiness_human",
]
