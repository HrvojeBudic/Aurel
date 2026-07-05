"""P5-TRACE-G exit seal — evidence-backed closure of the P5 AurelTrace spine.

Seals P5 as a **v1 trace/evidence contract layer** by reading the six P5-A→F
reports as evidence and building structured seal artifacts: a checklist, a
capability coverage matrix, a truth-label overclaim audit, an unavailable-surface
registry, and an exit-seal report that also carries the P6/P8/P9 handoff contracts.

Doctrine anchors enforced structurally here:

* ``SEALED`` is a *derived* verdict (never a self-assigned boolean) — it requires
  the checklist not BLOCKED, the truth audit passed, all three handoffs present,
  and no blocked matrix rows. A missing P5-A→F report or a blocking overclaim
  yields BLOCKED.
* The seal is evidence-backed closure, **not** production certification. The exit
  report's ``claims_production_readiness`` / ``claims_legal_compliance`` /
  ``claims_replay_live`` / ``claims_p6/p8/p9_implemented`` are unconstructible True.
* Unavailable surfaces stay explicit; nothing here executes, mutates, or
  implements a downstream domain.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .p5_handoff import (
    P5ToP6Handoff,
    P5ToP8Handoff,
    P5ToP9Handoff,
    build_all_p5_handoff_contracts,
)
from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)


# --------------------------------------------------------------------------- #
#  Enums
# --------------------------------------------------------------------------- #
class P5TraceSealStatus(str, Enum):
    SEALED = "SEALED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class P5ItemStatus(str, Enum):
    PASSED = "PASSED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class P5DownstreamOwner(str, Enum):
    P6_DATA_OBJECT_PLANE = "P6_DATA_OBJECT_PLANE"
    P8_ATLAS_MODEL_ROUTER = "P8_ATLAS_MODEL_ROUTER"
    P9_CUSTOS_POLICY_RUNTIME = "P9_CUSTOS_POLICY_RUNTIME"
    P13_REPLAY_FUTURE = "P13_REPLAY_FUTURE"
    P2_SHELL_FUTURE = "P2_SHELL_FUTURE"
    P25_HARDENING_FUTURE = "P25_HARDENING_FUTURE"
    NONE = "NONE"


class P5TruthFindingKind(str, Enum):
    FAKE_TRACE_VERIFIED = "FAKE_TRACE_VERIFIED"
    FAKE_REPLAY = "FAKE_REPLAY"
    FAKE_EXPORT_COMPLIANCE = "FAKE_EXPORT_COMPLIANCE"
    FAKE_PRODUCTION_DURABILITY = "FAKE_PRODUCTION_DURABILITY"
    FAKE_SHELL_API_AVAILABILITY = "FAKE_SHELL_API_AVAILABILITY"
    FAKE_P6_IMPLEMENTATION = "FAKE_P6_IMPLEMENTATION"
    FAKE_P8_IMPLEMENTATION = "FAKE_P8_IMPLEMENTATION"
    FAKE_P9_IMPLEMENTATION = "FAKE_P9_IMPLEMENTATION"
    FAKE_POLICY_AUTHORITY = "FAKE_POLICY_AUTHORITY"
    FAKE_OBJECT_PLANE_OWNERSHIP = "FAKE_OBJECT_PLANE_OWNERSHIP"
    UNKNOWN_TRUTH_LABEL = "UNKNOWN_TRUTH_LABEL"
    MISSING_UNAVAILABLE_REASON = "MISSING_UNAVAILABLE_REASON"


class P5FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"
    ERROR = "ERROR"


# --------------------------------------------------------------------------- #
#  Report evidence constants
# --------------------------------------------------------------------------- #
P5_PACKS: tuple[str, ...] = ("P5-A", "P5-B", "P5-C", "P5-D", "P5-E", "P5-F")

_PACK_REPORTS: dict[str, str] = {
    "P5-A": "P5_TRACE_A_INVENTORY_DOCTRINE_ENVELOPE_REF_HASH.md",
    "P5-B": "P5_TRACE_B_RECEIPTS_SCHEMA_SUBMIT_COVERAGE.md",
    "P5-C": "P5_TRACE_C_RUNTIME_SUBMIT_P3_P4_EVIDENCE_BINDING.md",
    "P5-D": "P5_TRACE_D_TRACE_VERIFIED_RESOLVER_QUERY_CLI.md",
    "P5-E": "P5_TRACE_E_PROJECTION_FEED_GOLDEN_THREAD_REPLAY_READINESS.md",
    "P5-F": "P5_TRACE_F_PRIVACY_EXPORT_PERSISTENT_INTEGRITY.md",
}

# (pack, roadmap, capability, source_modules, required_tests)
_CHECKLIST_SPEC: tuple[tuple[str, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "P5-A",
        "P5.0-P5.4",
        "canonical trace envelope / refs / hash verification",
        ("trace_inventory.py", "trace_envelope.py", "trace_refs.py", "trace_hash.py", "trace_verify.py"),
        ("test_trace_hash_verification.py", "test_canonical_trace_envelope.py", "test_trace_refs.py"),
    ),
    (
        "P5-B",
        "P5.5-P5.7",
        "verification receipts / schema registry / submit coverage audit",
        ("trace_receipts.py", "trace_schema.py", "submit_coverage.py"),
        ("test_trace_receipts.py", "test_trace_schema_registry.py", "test_submit_trace_coverage_audit.py"),
    ),
    (
        "P5-C",
        "P5.8-P5.10",
        "EvidenceRefs / runtime submit binding / P3-P4 bindings",
        ("evidence_ref.py", "runtime_submit_bridge.py", "p3_binding.py", "p4_binding.py"),
        ("test_evidence_refs.py", "test_runtime_submit_trace_bridge.py", "test_p3_trace_binding.py", "test_p4_trace_binding.py"),
    ),
    (
        "P5-D",
        "P5.11-P5.13",
        "TRACE_VERIFIED resolver / query read model / CLI",
        ("trace_resolver.py", "trace_query.py"),
        ("test_trace_verified_resolver.py", "test_trace_verified_overclaim_guard.py", "test_trace_query_read_model.py", "test_trace_cli_commands.py"),
    ),
    (
        "P5-E",
        "P5.14-P5.16",
        "projection feed / Golden Thread / replay-readiness",
        ("trace_projection_feed.py", "golden_thread.py", "replay_readiness.py"),
        ("test_trace_projection_feed.py", "test_golden_thread.py", "test_causal_graph_read_only.py", "test_replay_readiness.py"),
    ),
    (
        "P5-F",
        "P5.17-P5.19",
        "privacy/redaction labels / export manifest+bundle / persistent integrity posture",
        ("privacy_labels.py", "trace_export.py", "persistent_integrity.py"),
        ("test_privacy_labels.py", "test_trace_export_manifest.py", "test_trace_audit_bundle.py", "test_persistent_integrity_profile.py"),
    ),
)


# --------------------------------------------------------------------------- #
#  Checklist
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class P5SealChecklistItem:
    item_id: str
    pack_id: str
    roadmap_item: str
    capability: str
    required_report: str
    source_modules: tuple[str, ...]
    required_tests: tuple[str, ...]
    status: P5ItemStatus
    evidence: str
    missing_evidence: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "item_id", "pack_id", "capability", "required_report", "evidence")

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "pack_id": self.pack_id,
            "roadmap_item": self.roadmap_item,
            "capability": self.capability,
            "required_report": self.required_report,
            "source_modules": list(self.source_modules),
            "required_tests": list(self.required_tests),
            "status": self.status.value,
            "evidence": self.evidence,
            "missing_evidence": list(self.missing_evidence),
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class P5TraceSealChecklist:
    checklist_id: str
    items: tuple[P5SealChecklistItem, ...]
    status: P5TraceSealStatus
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "checklist_id")
        if not self.items:
            raise AurelTraceError("a seal checklist must have at least one item")

    def _count(self, status: P5ItemStatus) -> int:
        return sum(1 for i in self.items if i.status is status)

    @property
    def passed_count(self) -> int:
        return self._count(P5ItemStatus.PASSED)

    @property
    def blocked_count(self) -> int:
        return self._count(P5ItemStatus.BLOCKED)

    @property
    def partial_count(self) -> int:
        return self._count(P5ItemStatus.PARTIAL)

    @property
    def unavailable_count(self) -> int:
        return self._count(P5ItemStatus.UNAVAILABLE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checklist_id": self.checklist_id,
            "items": [i.to_dict() for i in self.items],
            "passed_count": self.passed_count,
            "partial_count": self.partial_count,
            "blocked_count": self.blocked_count,
            "unavailable_count": self.unavailable_count,
            "status": self.status.value,
            "truth_label": self.truth_label.value,
        }


def build_p5_trace_seal_checklist(
    *,
    available_reports: Sequence[str],
    checklist_id: str = "p5-trace-seal-checklist.p5-trace-g.v1",
) -> P5TraceSealChecklist:
    """Build the P5-A→F checklist; a missing required report blocks the item and seal."""

    available = set(available_reports)
    items: list[P5SealChecklistItem] = []
    for pack, roadmap, capability, modules, tests in _CHECKLIST_SPEC:
        report = _PACK_REPORTS[pack]
        present = report in available
        status = P5ItemStatus.PASSED if present else P5ItemStatus.BLOCKED
        missing = () if present else (f"required report {report} not present",)
        evidence = (
            f"{pack} report + {len(modules)} modules + {len(tests)} focused test files"
            if present
            else f"{pack} report {report} MISSING — seal evidence incomplete"
        )
        items.append(
            P5SealChecklistItem(
                item_id="p5cli-" + trace_sha(canonical_trace_json({"pack": pack}))[:32],
                pack_id=pack,
                roadmap_item=roadmap,
                capability=capability,
                required_report=report,
                source_modules=modules,
                required_tests=tests,
                status=status,
                evidence=evidence,
                missing_evidence=missing,
            )
        )
    checklist_status = (
        P5TraceSealStatus.BLOCKED
        if any(i.status is P5ItemStatus.BLOCKED for i in items)
        else P5TraceSealStatus.SEALED
    )
    return P5TraceSealChecklist(
        checklist_id=checklist_id, items=tuple(items), status=checklist_status
    )


# --------------------------------------------------------------------------- #
#  Capability coverage matrix
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class P5CapabilityCoverageRow:
    capability_id: str
    roadmap_item: str
    pack_id: str
    module: str
    tests: str
    report: str
    status: P5ItemStatus
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE
    unavailable_reason: str | None = None
    downstream_owner: P5DownstreamOwner = P5DownstreamOwner.NONE

    def __post_init__(self) -> None:
        require_nonempty(self, "capability_id", "pack_id", "module", "report")
        if (
            self.status is P5ItemStatus.UNAVAILABLE
            and not (self.unavailable_reason or "").strip()
        ):
            raise AurelTraceError("an UNAVAILABLE coverage row must carry a reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "roadmap_item": self.roadmap_item,
            "pack_id": self.pack_id,
            "module": self.module,
            "tests": self.tests,
            "report": self.report,
            "status": self.status.value,
            "unavailable_reason": self.unavailable_reason,
            "downstream_owner": self.downstream_owner.value,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class P5CapabilityCoverageMatrix:
    matrix_id: str
    rows: tuple[P5CapabilityCoverageRow, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "matrix_id")
        if not self.rows:
            raise AurelTraceError("a coverage matrix must have at least one row")

    def _count(self, status: P5ItemStatus) -> int:
        return sum(1 for r in self.rows if r.status is status)

    @property
    def covered_count(self) -> int:
        return self._count(P5ItemStatus.PASSED)

    @property
    def partial_count(self) -> int:
        return self._count(P5ItemStatus.PARTIAL)

    @property
    def blocked_count(self) -> int:
        return self._count(P5ItemStatus.BLOCKED)

    @property
    def unavailable_count(self) -> int:
        return self._count(P5ItemStatus.UNAVAILABLE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "rows": [r.to_dict() for r in self.rows],
            "covered_count": self.covered_count,
            "partial_count": self.partial_count,
            "blocked_count": self.blocked_count,
            "unavailable_count": self.unavailable_count,
            "truth_label": self.truth_label.value,
        }


# (capability_id, roadmap, pack, module, tests, report_pack)
_MATRIX_SPEC: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("canonical_trace_envelope", "P5.2", "P5-A", "trace_envelope.py", "test_canonical_trace_envelope.py", "P5-A"),
    ("trace_refs", "P5.3", "P5-A", "trace_refs.py", "test_trace_refs.py", "P5-A"),
    ("hash_verification", "P5.4", "P5-A", "trace_verify.py", "test_trace_hash_verification.py", "P5-A"),
    ("verification_receipts", "P5.5", "P5-B", "trace_receipts.py", "test_trace_receipts.py", "P5-B"),
    ("schema_registry", "P5.6", "P5-B", "trace_schema.py", "test_trace_schema_registry.py", "P5-B"),
    ("submit_coverage_audit", "P5.7", "P5-B", "submit_coverage.py", "test_submit_trace_coverage_audit.py", "P5-B"),
    ("evidence_refs", "P5.10", "P5-C", "evidence_ref.py", "test_evidence_refs.py", "P5-C"),
    ("runtime_submit_binding", "P5.8", "P5-C", "runtime_submit_bridge.py", "test_runtime_submit_trace_bridge.py", "P5-C"),
    ("p3_binding", "P5.9", "P5-C", "p3_binding.py", "test_p3_trace_binding.py", "P5-C"),
    ("p4_binding", "P5.9", "P5-C", "p4_binding.py", "test_p4_trace_binding.py", "P5-C"),
    ("trace_verified_resolver", "P5.11", "P5-D", "trace_resolver.py", "test_trace_verified_resolver.py", "P5-D"),
    ("trace_query_read_model", "P5.12", "P5-D", "trace_query.py", "test_trace_query_read_model.py", "P5-D"),
    ("trace_cli", "P5.13", "P5-D", "cli_modules/trace_commands.py", "test_trace_cli_commands.py", "P5-D"),
    ("projection_feed", "P5.14", "P5-E", "trace_projection_feed.py", "test_trace_projection_feed.py", "P5-E"),
    ("golden_thread", "P5.15", "P5-E", "golden_thread.py", "test_golden_thread.py", "P5-E"),
    ("causal_graph", "P5.15", "P5-E", "golden_thread.py", "test_causal_graph_read_only.py", "P5-E"),
    ("time_slice_refs", "P5.16", "P5-E", "replay_readiness.py", "test_replay_readiness.py", "P5-E"),
    ("replay_readiness_assessment", "P5.16", "P5-E", "replay_readiness.py", "test_replay_readiness.py", "P5-E"),
    ("privacy_locality_labels", "P5.17", "P5-F", "privacy_labels.py", "test_privacy_labels.py", "P5-F"),
    ("redacted_trace_view", "P5.17", "P5-F", "privacy_labels.py", "test_redacted_trace_view.py", "P5-F"),
    ("export_manifest", "P5.18", "P5-F", "trace_export.py", "test_trace_export_manifest.py", "P5-F"),
    ("audit_bundle", "P5.18", "P5-F", "trace_export.py", "test_trace_audit_bundle.py", "P5-F"),
    ("persistent_backend_profile", "P5.19", "P5-F", "persistent_integrity.py", "test_persistent_integrity_profile.py", "P5-F"),
    ("persistent_integrity_assessment", "P5.19", "P5-F", "persistent_integrity.py", "test_persistent_integrity_profile.py", "P5-F"),
    ("p5_seal_checklist", "P5.20", "P5-G", "p5_seal.py", "test_p5_trace_seal.py", "P5-G"),
    ("p5_truth_label_audit", "P5.20", "P5-G", "p5_seal.py", "test_p5_truth_label_audit.py", "P5-G"),
    ("p5_unavailable_registry", "P5.20", "P5-G", "p5_seal.py", "test_p5_trace_seal.py", "P5-G"),
    ("p5_to_p6_handoff", "P5.20", "P5-G", "p5_handoff.py", "test_p5_handoff_contracts.py", "P5-G"),
    ("p5_to_p8_handoff", "P5.20", "P5-G", "p5_handoff.py", "test_p5_handoff_contracts.py", "P5-G"),
    ("p5_to_p9_handoff", "P5.20", "P5-G", "p5_handoff.py", "test_p5_handoff_contracts.py", "P5-G"),
)

_MATRIX_DOWNSTREAM: dict[str, P5DownstreamOwner] = {
    "p5_to_p6_handoff": P5DownstreamOwner.P6_DATA_OBJECT_PLANE,
    "p5_to_p8_handoff": P5DownstreamOwner.P8_ATLAS_MODEL_ROUTER,
    "p5_to_p9_handoff": P5DownstreamOwner.P9_CUSTOS_POLICY_RUNTIME,
    "replay_readiness_assessment": P5DownstreamOwner.P13_REPLAY_FUTURE,
    "time_slice_refs": P5DownstreamOwner.P13_REPLAY_FUTURE,
}


def build_p5_capability_coverage_matrix(
    *,
    available_reports: Sequence[str],
    matrix_id: str = "p5-capability-coverage-matrix.p5-trace-g.v1",
) -> P5CapabilityCoverageMatrix:
    available = set(available_reports)
    rows: list[P5CapabilityCoverageRow] = []
    for cap_id, roadmap, pack, module, tests, report_pack in _MATRIX_SPEC:
        report = _PACK_REPORTS.get(report_pack, "P5_TRACE_G_EXIT_SEAL_P6_P8_P9_HANDOFF.md")
        # P5-G rows report against this pack's own (about-to-be-created) report.
        present = report_pack == "P5-G" or report in available
        status = P5ItemStatus.PASSED if present else P5ItemStatus.BLOCKED
        rows.append(
            P5CapabilityCoverageRow(
                capability_id=cap_id,
                roadmap_item=roadmap,
                pack_id=pack,
                module=module,
                tests=tests,
                report=report,
                status=status,
                downstream_owner=_MATRIX_DOWNSTREAM.get(cap_id, P5DownstreamOwner.NONE),
                unavailable_reason=None,
            )
        )
    return P5CapabilityCoverageMatrix(matrix_id=matrix_id, rows=tuple(rows))


# --------------------------------------------------------------------------- #
#  Truth-label audit
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class P5TruthLabelFinding:
    finding_id: str
    finding_kind: P5TruthFindingKind
    target: str
    severity: P5FindingSeverity
    message: str
    recommended_fix: str
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "finding_id", "target", "message")

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_kind": self.finding_kind.value,
            "target": self.target,
            "severity": self.severity.value,
            "message": self.message,
            "recommended_fix": self.recommended_fix,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class P5TruthLabelAudit:
    audit_id: str
    findings: tuple[P5TruthLabelFinding, ...]
    passed: bool
    checked_surfaces: tuple[str, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "audit_id")
        has_blocking = any(
            f.severity in (P5FindingSeverity.BLOCKING, P5FindingSeverity.ERROR)
            for f in self.findings
        )
        if self.passed and has_blocking:
            raise AurelTraceError(
                "a passed audit cannot contain BLOCKING/ERROR findings"
            )

    @property
    def overclaims(self) -> tuple[P5TruthLabelFinding, ...]:
        return tuple(
            f
            for f in self.findings
            if f.severity in (P5FindingSeverity.BLOCKING, P5FindingSeverity.ERROR)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "findings": [f.to_dict() for f in self.findings],
            "overclaims": [f.to_dict() for f in self.overclaims],
            "passed": self.passed,
            "checked_surfaces": list(self.checked_surfaces),
            "truth_label": self.truth_label.value,
        }


# surface -> (finding kind, fix). Each MUST be unavailable/not-live for a clean audit.
_FORBIDDEN_LIVE_SURFACES: dict[str, tuple[P5TruthFindingKind, str]] = {
    "trace_verified_label": (
        P5TruthFindingKind.FAKE_TRACE_VERIFIED,
        "TRACE_VERIFIED is only a P5-D resolver decision, never a truth label",
    ),
    "replay": (P5TruthFindingKind.FAKE_REPLAY, "actual replay is UNAVAILABLE in P5"),
    "external_export": (
        P5TruthFindingKind.FAKE_EXPORT_COMPLIANCE,
        "external export / legal compliance is UNAVAILABLE in P5",
    ),
    "production_durability": (
        P5TruthFindingKind.FAKE_PRODUCTION_DURABILITY,
        "production distributed ledger / durable storage is UNAVAILABLE in P5",
    ),
    "shell_api": (
        P5TruthFindingKind.FAKE_SHELL_API_AVAILABILITY,
        "Shell UI / API / event bus is UNAVAILABLE in P5",
    ),
    "p6_implementation": (
        P5TruthFindingKind.FAKE_P6_IMPLEMENTATION,
        "P6 object/data plane is not implemented by P5",
    ),
    "p8_implementation": (
        P5TruthFindingKind.FAKE_P8_IMPLEMENTATION,
        "P8 model router is not implemented by P5",
    ),
    "p9_implementation": (
        P5TruthFindingKind.FAKE_P9_IMPLEMENTATION,
        "P9 policy enforcement is not implemented by P5",
    ),
    "policy_authority": (
        P5TruthFindingKind.FAKE_POLICY_AUTHORITY,
        "P5 grants no authority and enforces no policy",
    ),
    "object_plane_ownership": (
        P5TruthFindingKind.FAKE_OBJECT_PLANE_OWNERSHIP,
        "P5 does not own ObjectRef/DataRef/ArtifactRef storage",
    ),
}


def build_p5_truth_label_audit(
    *,
    live_surface_claims: dict[str, bool] | None = None,
    audit_id: str = "p5-truth-label-audit.p5-trace-g.v1",
) -> P5TruthLabelAudit:
    """Audit P5 truth posture. Any forbidden surface claimed live → BLOCKING finding.

    ``live_surface_claims`` maps a surface key to whether it is (dishonestly)
    claimed live. The honest default claims none live and passes.
    """

    claims = live_surface_claims or {}
    findings: list[P5TruthLabelFinding] = []
    for surface, (kind, fix) in _FORBIDDEN_LIVE_SURFACES.items():
        if claims.get(surface, False):
            findings.append(
                P5TruthLabelFinding(
                    finding_id="p5tf-"
                    + trace_sha(canonical_trace_json({"surface": surface}))[:32],
                    finding_kind=kind,
                    target=surface,
                    severity=P5FindingSeverity.BLOCKING,
                    message=f"surface {surface!r} is claimed LIVE but must be unavailable",
                    recommended_fix=fix,
                )
            )
    passed = not findings
    return P5TruthLabelAudit(
        audit_id=audit_id,
        findings=tuple(findings),
        passed=passed,
        checked_surfaces=tuple(_FORBIDDEN_LIVE_SURFACES.keys()),
    )


# --------------------------------------------------------------------------- #
#  Unavailable surface registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class P5UnavailableSurface:
    surface_id: str
    name: str
    reason: str
    future_owner: str
    truth_label: TraceTruthLabel = TraceTruthLabel.UNAVAILABLE

    def __post_init__(self) -> None:
        require_nonempty(self, "surface_id", "name", "reason", "future_owner")
        if self.truth_label is not TraceTruthLabel.UNAVAILABLE:
            raise AurelTraceError("an unavailable surface must carry the UNAVAILABLE label")

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "name": self.name,
            "reason": self.reason,
            "future_owner": self.future_owner,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class P5UnavailableSurfaceRegistry:
    registry_id: str
    surfaces: tuple[P5UnavailableSurface, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "registry_id")
        if not self.surfaces:
            raise AurelTraceError("the unavailable registry must list at least one surface")

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "surfaces": [s.to_dict() for s in self.surfaces],
            "truth_label": self.truth_label.value,
        }


_UNAVAILABLE_SPEC: tuple[tuple[str, str, str], ...] = (
    ("actual replay", "no deterministic replay engine exists in P5", "P13_REPLAY_FUTURE"),
    ("fork / exact-copy / state restore", "not implemented; readiness only", "P13_REPLAY_FUTURE"),
    ("production distributed ledger", "trace.py is a local ledger; no distributed store", "P25_HARDENING_FUTURE"),
    ("external export service", "no upload/network/export path exists", "P25_HARDENING_FUTURE"),
    ("legal compliance certification", "manifests/bundles are not certification", "P9_CUSTOS_POLICY_RUNTIME"),
    ("encryption / KMS", "no encryption or key management implemented", "P25_HARDENING_FUTURE"),
    ("PII / secret detector", "redaction is policy-based, not detection-based", "P25_HARDENING_FUTURE"),
    ("production retention", "no retention engine implemented", "P25_HARDENING_FUTURE"),
    ("Shell trace UI", "no Shell UI surface for trace", "P2_SHELL_FUTURE"),
    ("API / event bus", "no HTTP API or event bus for trace", "P2_SHELL_FUTURE"),
    ("P6 object/data storage", "ObjectRef/DataRef/ArtifactRef owned by P6", "P6_DATA_OBJECT_PLANE"),
    ("P8 model routing", "model routing/scoring owned by P8", "P8_ATLAS_MODEL_ROUTER"),
    ("P9 policy enforcement", "policy enforcement/authority owned by P9", "P9_CUSTOS_POLICY_RUNTIME"),
    ("Rust/WASM durable substrate", "no Rust/WASM substrate; Python v1 reference layer", "P25_HARDENING_FUTURE"),
)


def build_p5_unavailable_surface_registry(
    *, registry_id: str = "p5-unavailable-surface-registry.p5-trace-g.v1"
) -> P5UnavailableSurfaceRegistry:
    surfaces = tuple(
        P5UnavailableSurface(
            surface_id="p5us-" + trace_sha(canonical_trace_json({"name": name}))[:32],
            name=name,
            reason=reason,
            future_owner=owner,
        )
        for name, reason, owner in _UNAVAILABLE_SPEC
    )
    return P5UnavailableSurfaceRegistry(registry_id=registry_id, surfaces=surfaces)


# --------------------------------------------------------------------------- #
#  Exit seal report
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class P5ExitSealReport:
    report_id: str
    seal_status: P5TraceSealStatus
    checklist: P5TraceSealChecklist
    coverage_matrix: P5CapabilityCoverageMatrix
    truth_label_audit: P5TruthLabelAudit
    unavailable_registry: P5UnavailableSurfaceRegistry
    handoff_p6: P5ToP6Handoff
    handoff_p8: P5ToP8Handoff
    handoff_p9: P5ToP9Handoff
    remaining_risks: tuple[str, ...]
    next_domain: str = "P6 — AurelData / Object Plane"
    validation_summary: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: the seal never claims production readiness / compliance / replay / P6-P8-P9 impl.
    claims_production_readiness: bool = False
    claims_legal_compliance: bool = False
    claims_replay_live: bool = False
    claims_p6_implemented: bool = False
    claims_p8_implemented: bool = False
    claims_p9_implemented: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "report_id", "next_domain")
        for field_name in (
            "claims_production_readiness",
            "claims_legal_compliance",
            "claims_replay_live",
            "claims_p6_implemented",
            "claims_p8_implemented",
            "claims_p9_implemented",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — the P5 seal is evidence-backed "
                    "closure, not production/compliance/replay/downstream implementation"
                )
        if self.seal_status is P5TraceSealStatus.SEALED and self.checklist.status is (
            P5TraceSealStatus.BLOCKED
        ):
            raise AurelTraceError("cannot be SEALED while the checklist is BLOCKED")
        if self.seal_status is P5TraceSealStatus.SEALED and not self.truth_label_audit.passed:
            raise AurelTraceError("cannot be SEALED while the truth audit has overclaims")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "seal_status": self.seal_status.value,
            "checklist": self.checklist.to_dict(),
            "coverage_matrix": self.coverage_matrix.to_dict(),
            "truth_label_audit": self.truth_label_audit.to_dict(),
            "unavailable_registry": self.unavailable_registry.to_dict(),
            "handoff_p6": self.handoff_p6.to_dict(),
            "handoff_p8": self.handoff_p8.to_dict(),
            "handoff_p9": self.handoff_p9.to_dict(),
            "remaining_risks": list(self.remaining_risks),
            "next_domain": self.next_domain,
            "validation_summary": self.validation_summary,
            "claims_production_readiness": self.claims_production_readiness,
            "claims_legal_compliance": self.claims_legal_compliance,
            "claims_replay_live": self.claims_replay_live,
            "claims_p6_implemented": self.claims_p6_implemented,
            "claims_p8_implemented": self.claims_p8_implemented,
            "claims_p9_implemented": self.claims_p9_implemented,
            "truth_label": self.truth_label.value,
        }


def _derive_seal_status(
    checklist: P5TraceSealChecklist,
    matrix: P5CapabilityCoverageMatrix,
    audit: P5TruthLabelAudit,
    handoffs_present: bool,
) -> P5TraceSealStatus:
    if (
        checklist.status is P5TraceSealStatus.BLOCKED
        or not audit.passed
        or not handoffs_present
    ):
        return P5TraceSealStatus.BLOCKED
    if matrix.blocked_count > 0:
        return P5TraceSealStatus.BLOCKED
    if matrix.partial_count > 0 or checklist.partial_count > 0:
        return P5TraceSealStatus.PARTIAL
    return P5TraceSealStatus.SEALED


def build_p5_exit_seal_report(
    *,
    checklist: P5TraceSealChecklist,
    coverage_matrix: P5CapabilityCoverageMatrix,
    truth_label_audit: P5TruthLabelAudit,
    unavailable_registry: P5UnavailableSurfaceRegistry,
    handoffs: tuple[P5ToP6Handoff, P5ToP8Handoff, P5ToP9Handoff],
    remaining_risks: Sequence[str] = (),
    validation_summary: str | None = None,
    report_id: str = "p5-exit-seal-report.p5-trace-g.v1",
) -> P5ExitSealReport:
    handoff_p6, handoff_p8, handoff_p9 = handoffs
    status = _derive_seal_status(
        checklist, coverage_matrix, truth_label_audit, handoffs_present=True
    )
    return P5ExitSealReport(
        report_id=report_id,
        seal_status=status,
        checklist=checklist,
        coverage_matrix=coverage_matrix,
        truth_label_audit=truth_label_audit,
        unavailable_registry=unavailable_registry,
        handoff_p6=handoff_p6,
        handoff_p8=handoff_p8,
        handoff_p9=handoff_p9,
        remaining_risks=tuple(remaining_risks),
        validation_summary=validation_summary,
    )


def discover_available_p5_reports(reports_dir: Path) -> tuple[str, ...]:
    """Read-only presence check of the six P5-A→F report files (no file reads)."""

    return tuple(
        report
        for report in _PACK_REPORTS.values()
        if (reports_dir / report).exists()
    )


def build_p5_exit_seal_from_reports_dir(
    reports_dir: Path,
    *,
    remaining_risks: Sequence[str] = (),
    validation_summary: str | None = None,
) -> P5ExitSealReport:
    """Convenience: discover reports read-only and build the full exit seal report."""

    available = discover_available_p5_reports(reports_dir)
    checklist = build_p5_trace_seal_checklist(available_reports=available)
    matrix = build_p5_capability_coverage_matrix(available_reports=available)
    audit = build_p5_truth_label_audit()
    registry = build_p5_unavailable_surface_registry()
    handoffs = build_all_p5_handoff_contracts()
    return build_p5_exit_seal_report(
        checklist=checklist,
        coverage_matrix=matrix,
        truth_label_audit=audit,
        unavailable_registry=registry,
        handoffs=handoffs,
        remaining_risks=remaining_risks,
        validation_summary=validation_summary,
    )
