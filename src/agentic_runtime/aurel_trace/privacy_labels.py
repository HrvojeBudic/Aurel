"""P5-TRACE-F privacy / locality labels and deterministic redaction.

Labels P5-E trace material (projection feed entries, Golden Thread refs, replay
readiness) with a privacy/locality posture and produces deterministic redaction
decisions plus a **safe read-only view** that never mutates the source material.

Doctrine anchors enforced structurally here:

* A privacy/locality label is not redaction, and neither certifies compliance.
* Redaction is a *decision that produces a safe view*, never a mutation of the
  source trace/feed/golden-thread objects (which are frozen).
* ``UNKNOWN``, ``LOCAL_ONLY``, ``SECRET``, and ``EXPORT_RESTRICTED`` fail closed —
  they never become ``NONE`` (raw) and never leak raw payload.
* No PII/secret *detector* is implemented; redaction is policy-based only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .trace_hash import (
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    require_nonempty,
    trace_sha,
)


class TracePrivacyLabel(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    PERSONAL_DATA = "PERSONAL_DATA"
    SENSITIVE_PERSONAL_DATA = "SENSITIVE_PERSONAL_DATA"
    LOCAL_ONLY = "LOCAL_ONLY"
    UNKNOWN = "UNKNOWN"


class TraceLocalityLabel(str, Enum):
    LOCAL_ONLY = "LOCAL_ONLY"
    EU_ONLY = "EU_ONLY"
    TENANT_LOCAL = "TENANT_LOCAL"
    EXPORT_ALLOWED = "EXPORT_ALLOWED"
    EXPORT_RESTRICTED = "EXPORT_RESTRICTED"
    UNKNOWN = "UNKNOWN"


class TraceRedactionMode(str, Enum):
    NONE = "NONE"
    MASK = "MASK"
    HASH = "HASH"
    SUMMARY_ONLY = "SUMMARY_ONLY"
    EXCLUDE = "EXCLUDE"
    ERROR = "ERROR"


# Severity order — combining two derived modes takes the strictest (highest).
_MODE_SEVERITY: dict[TraceRedactionMode, int] = {
    TraceRedactionMode.NONE: 0,
    TraceRedactionMode.SUMMARY_ONLY: 1,
    TraceRedactionMode.MASK: 2,
    TraceRedactionMode.HASH: 3,
    TraceRedactionMode.EXCLUDE: 4,
    TraceRedactionMode.ERROR: 5,
}

_DEFAULT_PRIVACY_MODE: dict[TracePrivacyLabel, TraceRedactionMode] = {
    TracePrivacyLabel.PUBLIC: TraceRedactionMode.NONE,
    TracePrivacyLabel.INTERNAL: TraceRedactionMode.NONE,
    TracePrivacyLabel.CONFIDENTIAL: TraceRedactionMode.MASK,
    TracePrivacyLabel.PERSONAL_DATA: TraceRedactionMode.MASK,
    TracePrivacyLabel.SECRET: TraceRedactionMode.EXCLUDE,
    TracePrivacyLabel.SENSITIVE_PERSONAL_DATA: TraceRedactionMode.EXCLUDE,
    TracePrivacyLabel.LOCAL_ONLY: TraceRedactionMode.EXCLUDE,
    TracePrivacyLabel.UNKNOWN: TraceRedactionMode.SUMMARY_ONLY,
}

_DEFAULT_LOCALITY_MODE: dict[TraceLocalityLabel, TraceRedactionMode] = {
    TraceLocalityLabel.EXPORT_ALLOWED: TraceRedactionMode.NONE,
    TraceLocalityLabel.EU_ONLY: TraceRedactionMode.SUMMARY_ONLY,
    TraceLocalityLabel.TENANT_LOCAL: TraceRedactionMode.SUMMARY_ONLY,
    TraceLocalityLabel.EXPORT_RESTRICTED: TraceRedactionMode.EXCLUDE,
    TraceLocalityLabel.LOCAL_ONLY: TraceRedactionMode.EXCLUDE,
    TraceLocalityLabel.UNKNOWN: TraceRedactionMode.SUMMARY_ONLY,
}


def _strictest(a: TraceRedactionMode, b: TraceRedactionMode) -> TraceRedactionMode:
    return a if _MODE_SEVERITY[a] >= _MODE_SEVERITY[b] else b


@dataclass(frozen=True)
class TraceRedactionPolicy:
    """How material should appear in redacted views/bundles. Deterministic."""

    policy_id: str
    default_mode: TraceRedactionMode = TraceRedactionMode.SUMMARY_ONLY
    privacy_overrides: tuple[tuple[TracePrivacyLabel, TraceRedactionMode], ...] = ()
    locality_overrides: tuple[tuple[TraceLocalityLabel, TraceRedactionMode], ...] = ()
    include_hashes: bool = True
    include_summaries: bool = True
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "policy_id")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a redaction policy is a LIVE contract")

    def _privacy_mode(self, label: TracePrivacyLabel) -> TraceRedactionMode:
        for override_label, mode in self.privacy_overrides:
            if override_label is label:
                return mode
        return _DEFAULT_PRIVACY_MODE.get(label, self.default_mode)

    def _locality_mode(self, label: TraceLocalityLabel) -> TraceRedactionMode:
        for override_label, mode in self.locality_overrides:
            if override_label is label:
                return mode
        return _DEFAULT_LOCALITY_MODE.get(label, self.default_mode)

    def resolve_mode(
        self, privacy_label: TracePrivacyLabel, locality_label: TraceLocalityLabel
    ) -> TraceRedactionMode:
        """Strictest of the privacy-derived and locality-derived modes."""

        return _strictest(
            self._privacy_mode(privacy_label), self._locality_mode(locality_label)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "default_mode": self.default_mode.value,
            "privacy_overrides": [
                [label.value, mode.value] for label, mode in self.privacy_overrides
            ],
            "locality_overrides": [
                [label.value, mode.value] for label, mode in self.locality_overrides
            ],
            "include_hashes": self.include_hashes,
            "include_summaries": self.include_summaries,
            "truth_label": self.truth_label.value,
        }


def build_default_trace_redaction_policy() -> TraceRedactionPolicy:
    return TraceRedactionPolicy(policy_id="trace-redaction-policy.p5-trace-f.v1")


@dataclass(frozen=True)
class TraceRedactionDecision:
    """How one P5-E item appears in a safe view/bundle. Deterministic, explicit."""

    decision_id: str
    target_ref: str
    target_kind: str
    privacy_label: TracePrivacyLabel
    locality_label: TraceLocalityLabel
    redaction_mode: TraceRedactionMode
    reason: str
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "decision_id", "target_ref", "target_kind", "reason")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a redaction decision is a LIVE contract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "target_ref": self.target_ref,
            "target_kind": self.target_kind,
            "privacy_label": self.privacy_label.value,
            "locality_label": self.locality_label.value,
            "redaction_mode": self.redaction_mode.value,
            "reason": self.reason,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class RedactedTraceItem:
    """One item in a RedactedTraceView. Never carries raw restricted payload."""

    item_id: str
    source_ref: str
    target_kind: str
    redaction_decision_id: str
    redaction_mode: TraceRedactionMode
    excluded: bool = False
    safe_value: str | None = None
    safe_summary: str | None = None
    content_hash: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "item_id", "source_ref", "redaction_decision_id")
        # A non-NONE mode may not carry a raw safe_value (only masked/summary/hash).
        if (
            self.redaction_mode is not TraceRedactionMode.NONE
            and self.safe_value is not None
        ):
            raise AurelTraceError(
                "redacted items may not carry a raw safe_value unless mode is NONE"
            )
        if self.excluded and (
            self.safe_value or self.safe_summary or self.content_hash
        ):
            raise AurelTraceError("an EXCLUDE item must carry no payload at all")

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "source_ref": self.source_ref,
            "target_kind": self.target_kind,
            "redaction_decision_id": self.redaction_decision_id,
            "redaction_mode": self.redaction_mode.value,
            "excluded": self.excluded,
            "safe_value": self.safe_value,
            "safe_summary": self.safe_summary,
            "content_hash": self.content_hash,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class RedactedTraceView:
    """Safe read model over P5-E feed / Golden Thread / replay-readiness material."""

    view_id: str
    items: tuple[RedactedTraceItem, ...]
    redaction_decisions: tuple[TraceRedactionDecision, ...]
    source_feed_id: str | None = None
    source_golden_thread_ref_id: str | None = None
    source_replay_assessment_id: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a redacted view is a safe read model; it mutates no source object.
    mutates: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "view_id")
        if self.mutates is True:
            raise AurelTraceError(
                "mutates must be False — a redacted view never mutates source material"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a redacted view is a LIVE read model")

    @property
    def included_count(self) -> int:
        return sum(
            1
            for i in self.items
            if not i.excluded and i.redaction_mode is TraceRedactionMode.NONE
        )

    @property
    def redacted_count(self) -> int:
        return sum(
            1
            for i in self.items
            if not i.excluded and i.redaction_mode is not TraceRedactionMode.NONE
        )

    @property
    def excluded_count(self) -> int:
        return sum(1 for i in self.items if i.excluded)

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "source_feed_id": self.source_feed_id,
            "source_golden_thread_ref_id": self.source_golden_thread_ref_id,
            "source_replay_assessment_id": self.source_replay_assessment_id,
            "items": [i.to_dict() for i in self.items],
            "redaction_decisions": [d.to_dict() for d in self.redaction_decisions],
            "included_count": self.included_count,
            "redacted_count": self.redacted_count,
            "excluded_count": self.excluded_count,
            "mutates": self.mutates,
            "truth_label": self.truth_label.value,
        }


def make_trace_redaction_decision(
    *,
    target_ref: str,
    target_kind: str,
    privacy_label: TracePrivacyLabel,
    locality_label: TraceLocalityLabel,
    policy: TraceRedactionPolicy | None = None,
) -> TraceRedactionDecision:
    """Deterministic redaction decision — strictest of privacy and locality mode."""

    if not isinstance(privacy_label, TracePrivacyLabel):
        raise AurelTraceError("privacy_label must be a TracePrivacyLabel (closed-world)")
    if not isinstance(locality_label, TraceLocalityLabel):
        raise AurelTraceError("locality_label must be a TraceLocalityLabel (closed-world)")
    the_policy = policy or build_default_trace_redaction_policy()
    mode = the_policy.resolve_mode(privacy_label, locality_label)
    reason = (
        f"privacy={privacy_label.value} locality={locality_label.value} "
        f"-> redaction={mode.value} (strictest of policy-derived modes)"
    )
    decision_id = "tredec-" + trace_sha(
        canonical_trace_json(
            {
                "target_ref": target_ref,
                "target_kind": target_kind,
                "privacy": privacy_label.value,
                "locality": locality_label.value,
                "policy_id": the_policy.policy_id,
                "mode": mode.value,
            }
        )
    )[:40]
    return TraceRedactionDecision(
        decision_id=decision_id,
        target_ref=target_ref,
        target_kind=target_kind,
        privacy_label=privacy_label,
        locality_label=locality_label,
        redaction_mode=mode,
        reason=reason,
    )


def _safe_item_for(
    decision: TraceRedactionDecision, *, summary: str | None
) -> RedactedTraceItem:
    mode = decision.redaction_mode
    item_id = "tredit-" + trace_sha(
        canonical_trace_json(
            {"decision_id": decision.decision_id, "target_ref": decision.target_ref}
        )
    )[:32]
    if mode is TraceRedactionMode.EXCLUDE or mode is TraceRedactionMode.ERROR:
        return RedactedTraceItem(
            item_id=item_id,
            source_ref=decision.target_ref,
            target_kind=decision.target_kind,
            redaction_decision_id=decision.decision_id,
            redaction_mode=mode,
            excluded=True,
        )
    if mode is TraceRedactionMode.NONE:
        # "raw" here is only the non-sensitive source ref id itself.
        return RedactedTraceItem(
            item_id=item_id,
            source_ref=decision.target_ref,
            target_kind=decision.target_kind,
            redaction_decision_id=decision.decision_id,
            redaction_mode=mode,
            safe_value=decision.target_ref,
        )
    if mode is TraceRedactionMode.HASH:
        return RedactedTraceItem(
            item_id=item_id,
            source_ref=decision.target_ref,
            target_kind=decision.target_kind,
            redaction_decision_id=decision.decision_id,
            redaction_mode=mode,
            content_hash="rh-" + trace_sha(decision.target_ref)[:40],
        )
    if mode is TraceRedactionMode.MASK:
        return RedactedTraceItem(
            item_id=item_id,
            source_ref=decision.target_ref,
            target_kind=decision.target_kind,
            redaction_decision_id=decision.decision_id,
            redaction_mode=mode,
            safe_summary="[REDACTED]",
        )
    # SUMMARY_ONLY
    return RedactedTraceItem(
        item_id=item_id,
        source_ref=decision.target_ref,
        target_kind=decision.target_kind,
        redaction_decision_id=decision.decision_id,
        redaction_mode=mode,
        safe_summary=summary or f"{decision.target_kind} (summary only)",
    )


def build_redacted_trace_view(
    *,
    label_map: dict[str, tuple[TracePrivacyLabel, TraceLocalityLabel]],
    feed: Any = None,
    golden_thread_graph: Any = None,
    replay_assessment: Any = None,
    policy: TraceRedactionPolicy | None = None,
    view_id: str = "redacted-trace-view.p5-trace-f.v1",
) -> RedactedTraceView:
    """Build a safe read model over P5-E material without mutating any source.

    ``label_map`` maps a source ref id to its ``(privacy, locality)`` labels. Refs
    not present in the map are treated as ``UNKNOWN``/``UNKNOWN`` and fail closed to
    a non-raw mode.
    """

    the_policy = policy or build_default_trace_redaction_policy()
    refs: list[tuple[str, str, str | None]] = []  # (ref, kind, summary)

    if feed is not None:
        for entry in feed.entries:
            refs.append((entry.target_id, "PROJECTION_FEED_ENTRY", entry.summary))
    if golden_thread_graph is not None:
        for node in golden_thread_graph.nodes:
            refs.append((node.source_ref, node.node_kind.value, None))
    if replay_assessment is not None:
        refs.append(
            (
                replay_assessment.time_slice_ref.time_slice_ref_id,
                "TIME_SLICE",
                f"replay readiness {replay_assessment.status.value}",
            )
        )

    decisions: list[TraceRedactionDecision] = []
    items: list[RedactedTraceItem] = []
    for ref, kind, summary in refs:
        privacy, locality = label_map.get(
            ref, (TracePrivacyLabel.UNKNOWN, TraceLocalityLabel.UNKNOWN)
        )
        decision = make_trace_redaction_decision(
            target_ref=ref,
            target_kind=kind,
            privacy_label=privacy,
            locality_label=locality,
            policy=the_policy,
        )
        decisions.append(decision)
        items.append(_safe_item_for(decision, summary=summary))

    return RedactedTraceView(
        view_id=view_id,
        items=tuple(items),
        redaction_decisions=tuple(decisions),
        source_feed_id=getattr(feed, "feed_id", None) if feed is not None else None,
        source_golden_thread_ref_id=(
            golden_thread_graph.golden_thread_ref.golden_thread_ref_id
            if golden_thread_graph is not None
            else None
        ),
        source_replay_assessment_id=(
            replay_assessment.assessment_id if replay_assessment is not None else None
        ),
    )
