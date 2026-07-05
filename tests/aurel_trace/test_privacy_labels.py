"""P5.17 — Privacy / locality labels and deterministic redaction."""

from __future__ import annotations

import pytest

from agentic_runtime.aurel_trace import (
    AurelTraceError,
    TraceLocalityLabel,
    TracePrivacyLabel,
    TraceRedactionMode,
    make_trace_redaction_decision,
)


def _mode(privacy, locality):
    return make_trace_redaction_decision(
        target_ref="r", target_kind="X", privacy_label=privacy, locality_label=locality
    ).redaction_mode


def test_public_export_allowed_is_none():
    assert (
        _mode(TracePrivacyLabel.PUBLIC, TraceLocalityLabel.EXPORT_ALLOWED)
        is TraceRedactionMode.NONE
    )


def test_local_only_privacy_excludes():
    assert (
        _mode(TracePrivacyLabel.LOCAL_ONLY, TraceLocalityLabel.EXPORT_ALLOWED)
        is TraceRedactionMode.EXCLUDE
    )


def test_local_only_locality_excludes():
    assert (
        _mode(TracePrivacyLabel.PUBLIC, TraceLocalityLabel.LOCAL_ONLY)
        is TraceRedactionMode.EXCLUDE
    )


def test_export_restricted_excludes():
    assert (
        _mode(TracePrivacyLabel.INTERNAL, TraceLocalityLabel.EXPORT_RESTRICTED)
        is TraceRedactionMode.EXCLUDE
    )


def test_unknown_fails_closed_not_none():
    mode = _mode(TracePrivacyLabel.UNKNOWN, TraceLocalityLabel.UNKNOWN)
    assert mode is not TraceRedactionMode.NONE
    assert mode is TraceRedactionMode.SUMMARY_ONLY


def test_strictest_of_two_modes_wins():
    # PERSONAL_DATA(MASK) vs EXPORT_RESTRICTED(EXCLUDE) -> EXCLUDE
    assert (
        _mode(TracePrivacyLabel.PERSONAL_DATA, TraceLocalityLabel.EXPORT_RESTRICTED)
        is TraceRedactionMode.EXCLUDE
    )
    # PERSONAL_DATA(MASK) vs EU_ONLY(SUMMARY_ONLY) -> MASK (MASK is stricter)
    assert (
        _mode(TracePrivacyLabel.PERSONAL_DATA, TraceLocalityLabel.EU_ONLY)
        is TraceRedactionMode.MASK
    )


def test_decision_is_deterministic_and_has_reason():
    a = make_trace_redaction_decision(
        target_ref="r1",
        target_kind="FEED",
        privacy_label=TracePrivacyLabel.SECRET,
        locality_label=TraceLocalityLabel.LOCAL_ONLY,
    )
    b = make_trace_redaction_decision(
        target_ref="r1",
        target_kind="FEED",
        privacy_label=TracePrivacyLabel.SECRET,
        locality_label=TraceLocalityLabel.LOCAL_ONLY,
    )
    assert a.decision_id == b.decision_id
    assert a.reason


def test_non_enum_label_fails_closed():
    with pytest.raises(AurelTraceError):
        make_trace_redaction_decision(
            target_ref="r",
            target_kind="X",
            privacy_label="SECRET",  # type: ignore[arg-type]
            locality_label=TraceLocalityLabel.LOCAL_ONLY,
        )
