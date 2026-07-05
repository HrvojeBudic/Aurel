"""P5-TRACE-F export manifest / audit bundle over P5-E trace material.

A :class:`TraceExportManifest` describes exactly what is included, excluded,
redacted, hashed, or summary-only in an audit/export bundle, and a
:class:`TraceAuditBundle` packages that material with its redacted view. Neither
is an external export service, a legal-compliance certification, an upload, or an
encrypted package — those remain UNAVAILABLE and are listed explicitly. LOCAL_ONLY
/ EXPORT_RESTRICTED / SECRET / UNKNOWN material never enters ``included_refs`` raw.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .privacy_labels import (
    RedactedTraceView,
    TraceRedactionDecision,
    TraceRedactionMode,
)
from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)

# What this pack explicitly does NOT provide — always listed on a manifest.
UNAVAILABLE_COMPLIANCE_CLAIMS: tuple[str, ...] = (
    "legal/regulatory compliance certification: UNAVAILABLE",
    "external export service / cloud upload: UNAVAILABLE",
    "encryption / key management (KMS): UNAVAILABLE",
    "PII / secret detection engine: UNAVAILABLE",
    "production distributed ledger / durable retention: UNAVAILABLE",
)


@dataclass(frozen=True)
class TraceBundleInclusionDecision:
    """Whether one source item is included raw/redacted/hashed/summary/excluded."""

    inclusion_decision_id: str
    source_ref: str
    source_kind: str
    include_raw: bool
    include_redacted: bool
    include_hash: bool
    include_summary: bool
    exclude: bool
    reason: str
    redaction_decision_id: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "inclusion_decision_id", "source_ref", "reason")
        flags = (
            self.include_raw,
            self.include_redacted,
            self.include_hash,
            self.include_summary,
            self.exclude,
        )
        if sum(1 for f in flags if f) != 1:
            raise AurelTraceError(
                "exactly one inclusion flag must be true for a bundle inclusion decision"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a bundle inclusion decision is a LIVE contract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "inclusion_decision_id": self.inclusion_decision_id,
            "source_ref": self.source_ref,
            "source_kind": self.source_kind,
            "include_raw": self.include_raw,
            "include_redacted": self.include_redacted,
            "include_hash": self.include_hash,
            "include_summary": self.include_summary,
            "exclude": self.exclude,
            "reason": self.reason,
            "redaction_decision_id": self.redaction_decision_id,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceExportManifest:
    """Describes exactly what a trace export/audit bundle contains. Not an export."""

    manifest_id: str
    included_refs: tuple[str, ...] = ()
    excluded_refs: tuple[str, ...] = ()
    redacted_refs: tuple[str, ...] = ()
    hashed_refs: tuple[str, ...] = ()
    summary_only_refs: tuple[str, ...] = ()
    source_resolver_decisions: tuple[str, ...] = ()
    source_feed_entries: tuple[str, ...] = ()
    source_golden_thread_refs: tuple[str, ...] = ()
    source_replay_readiness_assessments: tuple[str, ...] = ()
    redaction_decisions: tuple[TraceRedactionDecision, ...] = ()
    inclusion_decisions: tuple[TraceBundleInclusionDecision, ...] = ()
    checksums: tuple[tuple[str, str], ...] = ()
    unavailable_compliance_claims: tuple[str, ...] = UNAVAILABLE_COMPLIANCE_CLAIMS
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a manifest describes; it never exports/uploads/encrypts/certifies.
    is_external_export: bool = False
    uploads: bool = False
    encrypts: bool = False
    certifies_compliance: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "manifest_id")
        for field_name in (
            "is_external_export",
            "uploads",
            "encrypts",
            "certifies_compliance",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a manifest is an audit/export "
                    "contract, not an external export/upload/encryption/certification"
                )
        if not self.unavailable_compliance_claims:
            raise AurelTraceError(
                "a manifest must list its unavailable compliance/export claims"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a manifest is a LIVE contract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "included_refs": list(self.included_refs),
            "excluded_refs": list(self.excluded_refs),
            "redacted_refs": list(self.redacted_refs),
            "hashed_refs": list(self.hashed_refs),
            "summary_only_refs": list(self.summary_only_refs),
            "source_resolver_decisions": list(self.source_resolver_decisions),
            "source_feed_entries": list(self.source_feed_entries),
            "source_golden_thread_refs": list(self.source_golden_thread_refs),
            "source_replay_readiness_assessments": list(
                self.source_replay_readiness_assessments
            ),
            "redaction_decisions": [d.to_dict() for d in self.redaction_decisions],
            "inclusion_decisions": [d.to_dict() for d in self.inclusion_decisions],
            "checksums": [list(pair) for pair in self.checksums],
            "unavailable_compliance_claims": list(self.unavailable_compliance_claims),
            "is_external_export": self.is_external_export,
            "uploads": self.uploads,
            "encrypts": self.encrypts,
            "certifies_compliance": self.certifies_compliance,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceAuditBundle:
    """In-memory audit bundle contract. Not certification, upload, or encryption."""

    bundle_id: str
    manifest: TraceExportManifest
    redacted_view: RedactedTraceView
    excluded_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    integrity_summary: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a bundle is a read-only package contract, nothing more.
    is_external_export: bool = False
    is_legal_certification: bool = False
    is_encrypted: bool = False
    uploads: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "bundle_id")
        for field_name in (
            "is_external_export",
            "is_legal_certification",
            "is_encrypted",
            "uploads",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — an audit bundle is a read-only "
                    "package contract, not certification/upload/encryption"
                )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("an audit bundle is a LIVE contract")

    @property
    def included_items(self) -> tuple[Any, ...]:
        return tuple(i for i in self.redacted_view.items if not i.excluded)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "manifest": self.manifest.to_dict(),
            "redacted_view": self.redacted_view.to_dict(),
            "excluded_refs": list(self.excluded_refs),
            "source_refs": list(self.source_refs),
            "integrity_summary": self.integrity_summary,
            "is_external_export": self.is_external_export,
            "is_legal_certification": self.is_legal_certification,
            "is_encrypted": self.is_encrypted,
            "uploads": self.uploads,
            "truth_label": self.truth_label.value,
        }


def decide_bundle_inclusion(
    decision: TraceRedactionDecision,
) -> TraceBundleInclusionDecision:
    """Map a redaction mode to a single bundle inclusion flag. Deterministic."""

    mode = decision.redaction_mode
    include_raw = mode is TraceRedactionMode.NONE
    include_redacted = mode is TraceRedactionMode.MASK
    include_hash = mode is TraceRedactionMode.HASH
    include_summary = mode is TraceRedactionMode.SUMMARY_ONLY
    exclude = mode in (TraceRedactionMode.EXCLUDE, TraceRedactionMode.ERROR)
    inclusion_decision_id = "tbincl-" + trace_sha(
        canonical_trace_json(
            {"decision_id": decision.decision_id, "mode": mode.value}
        )
    )[:40]
    return TraceBundleInclusionDecision(
        inclusion_decision_id=inclusion_decision_id,
        source_ref=decision.target_ref,
        source_kind=decision.target_kind,
        include_raw=include_raw,
        include_redacted=include_redacted,
        include_hash=include_hash,
        include_summary=include_summary,
        exclude=exclude,
        reason=decision.reason,
        redaction_decision_id=decision.decision_id,
    )


def checksum_refs(refs: Sequence[str]) -> str:
    """Deterministic checksum over a set of ref ids (audit integrity, not crypto)."""

    return "ck-" + trace_sha(canonical_trace_json(sorted(refs)))[:40]


def build_trace_export_manifest(
    *,
    redaction_decisions: Sequence[TraceRedactionDecision],
    feed: Any = None,
    golden_thread_graph: Any = None,
    replay_assessment: Any = None,
    resolver_decision_ids: Sequence[str] = (),
    manifest_id: str = "trace-export-manifest.p5-trace-f.v1",
) -> TraceExportManifest:
    """Build a manifest from redaction decisions over P5-E material.

    Only ``NONE``-mode material lands in ``included_refs`` (raw); everything else
    is routed to redacted/hashed/summary-only/excluded refs — so LOCAL_ONLY /
    SECRET / EXPORT_RESTRICTED / UNKNOWN never export raw.
    """

    included: list[str] = []
    excluded: list[str] = []
    redacted: list[str] = []
    hashed: list[str] = []
    summary_only: list[str] = []
    inclusion_decisions: list[TraceBundleInclusionDecision] = []

    for decision in redaction_decisions:
        inclusion = decide_bundle_inclusion(decision)
        inclusion_decisions.append(inclusion)
        ref = decision.target_ref
        if inclusion.include_raw:
            included.append(ref)
        elif inclusion.include_redacted:
            redacted.append(ref)
        elif inclusion.include_hash:
            hashed.append(ref)
        elif inclusion.include_summary:
            summary_only.append(ref)
        else:
            excluded.append(ref)

    feed_entry_ids = (
        tuple(e.feed_entry_id for e in feed.entries) if feed is not None else ()
    )
    golden_thread_ids = (
        (golden_thread_graph.golden_thread_ref.golden_thread_ref_id,)
        if golden_thread_graph is not None
        else ()
    )
    replay_ids = (
        (replay_assessment.assessment_id,) if replay_assessment is not None else ()
    )

    checksums = (
        ("included", checksum_refs(included)),
        ("redacted", checksum_refs(redacted)),
        ("hashed", checksum_refs(hashed)),
        ("summary_only", checksum_refs(summary_only)),
        ("excluded", checksum_refs(excluded)),
    )

    return TraceExportManifest(
        manifest_id=manifest_id,
        included_refs=tuple(included),
        excluded_refs=tuple(excluded),
        redacted_refs=tuple(redacted),
        hashed_refs=tuple(hashed),
        summary_only_refs=tuple(summary_only),
        source_resolver_decisions=tuple(resolver_decision_ids),
        source_feed_entries=feed_entry_ids,
        source_golden_thread_refs=golden_thread_ids,
        source_replay_readiness_assessments=replay_ids,
        redaction_decisions=tuple(redaction_decisions),
        inclusion_decisions=tuple(inclusion_decisions),
        checksums=checksums,
    )


def build_trace_audit_bundle(
    *,
    manifest: TraceExportManifest,
    redacted_view: RedactedTraceView,
    source_refs: Sequence[str] = (),
    integrity_summary: str | None = None,
    bundle_id: str = "trace-audit-bundle.p5-trace-f.v1",
) -> TraceAuditBundle:
    """Package a manifest + redacted view as a read-only audit bundle."""

    return TraceAuditBundle(
        bundle_id=bundle_id,
        manifest=manifest,
        redacted_view=redacted_view,
        excluded_refs=manifest.excluded_refs,
        source_refs=tuple(source_refs),
        integrity_summary=integrity_summary,
    )
