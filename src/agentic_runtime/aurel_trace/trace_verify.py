"""P5-TRACE-A structured hash-chain verification kernel v1.

Verification is *structured*: it returns findings, counts, a status, and the
chain head — not merely a bool. It proves the integrity of the trace's hash
chain over supported canonical envelopes. It never repairs a broken chain, and
a valid hash chain is explicitly **not** a claim of semantic/business
correctness — the strongest label mintable here is ``TRACE_INTEGRITY_VERIFIED``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .trace_envelope import (
    CanonicalTraceEventEnvelope,
    try_canonical_envelope,
)
from .trace_hash import (
    GENESIS_ENTRY_HASH,
    AurelTraceError,
    TraceTruthLabel,
    canonical_trace_json,
    recompute_entry_hash,
    trace_sha,
)
from .trace_refs import TraceEntryRef, TraceRunRef


class TraceVerificationScope(str, Enum):
    FULL_CHAIN = "FULL_CHAIN"
    SEGMENT = "SEGMENT"
    SINGLE_ENTRY = "SINGLE_ENTRY"
    CHAIN_HEAD = "CHAIN_HEAD"


class TraceVerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class TraceHashFindingKind(str, Enum):
    BROKEN_PREVIOUS_HASH = "BROKEN_PREVIOUS_HASH"
    MISSING_ENTRY = "MISSING_ENTRY"
    DUPLICATE_ENTRY_ID = "DUPLICATE_ENTRY_ID"
    ENTRY_HASH_MISMATCH = "ENTRY_HASH_MISMATCH"
    PAYLOAD_HASH_MISMATCH = "PAYLOAD_HASH_MISMATCH"
    UNSUPPORTED_RECORD_TYPE = "UNSUPPORTED_RECORD_TYPE"
    SCHEMA_UNKNOWN = "SCHEMA_UNKNOWN"
    CHAIN_HEAD_MISMATCH = "CHAIN_HEAD_MISMATCH"
    CAUSAL_REF_BROKEN = "CAUSAL_REF_BROKEN"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class TraceFindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class TraceHashFinding:
    """One trace-integrity finding. Evidence, never authority, never repair."""

    finding_id: str
    finding_kind: TraceHashFindingKind
    severity: TraceFindingSeverity
    message: str
    entry_ref: TraceEntryRef | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise AurelTraceError("finding_id must not be empty")
        if not self.message.strip():
            raise AurelTraceError("finding message must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_kind": self.finding_kind.value,
            "severity": self.severity.value,
            "message": self.message,
            "entry_ref": self.entry_ref.to_dict() if self.entry_ref else None,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceHashVerificationRequest:
    """A request for structured verification over trace entries/envelopes."""

    verification_request_id: str
    trace_run_ref: TraceRunRef
    scope: TraceVerificationScope
    start_index: int | None = None
    end_index: int | None = None
    expected_chain_head: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        if not self.verification_request_id.strip():
            raise AurelTraceError("verification_request_id must not be empty")
        if self.scope is TraceVerificationScope.SEGMENT:
            if self.start_index is None or self.end_index is None:
                raise AurelTraceError("SEGMENT scope requires start_index and end_index")
            if self.start_index < 0 or self.end_index < self.start_index:
                raise AurelTraceError("SEGMENT scope requires 0 <= start_index <= end_index")
        if self.scope is TraceVerificationScope.SINGLE_ENTRY and self.start_index is None:
            raise AurelTraceError("SINGLE_ENTRY scope requires start_index")
        if self.scope is TraceVerificationScope.CHAIN_HEAD and not self.expected_chain_head:
            raise AurelTraceError("CHAIN_HEAD scope requires expected_chain_head")

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_request_id": self.verification_request_id,
            "trace_run_ref": self.trace_run_ref.to_dict(),
            "scope": self.scope.value,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "expected_chain_head": self.expected_chain_head,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class TraceHashVerificationResult:
    """Structured verification output. PASS is unconstructible when broken."""

    verification_result_id: str
    request_id: str
    status: TraceVerificationStatus
    verified: bool
    checked_count: int
    valid_count: int
    invalid_count: int
    findings: tuple[TraceHashFinding, ...] = ()
    first_invalid_index: int | None = None
    chain_head_hash: str | None = None
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        if not self.verification_result_id.strip():
            raise AurelTraceError("verification_result_id must not be empty")
        pass_status = self.status is TraceVerificationStatus.PASS
        if pass_status:
            if not self.verified:
                raise AurelTraceError("PASS requires verified=True")
            if self.invalid_count != 0:
                raise AurelTraceError("PASS requires zero invalid entries")
            if self.truth_label is not TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
                raise AurelTraceError(
                    "a PASS result must carry TRACE_INTEGRITY_VERIFIED"
                )
        else:
            if self.verified:
                raise AurelTraceError("only a PASS result may be verified=True")
            if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
                raise AurelTraceError(
                    "only a PASS result may carry TRACE_INTEGRITY_VERIFIED"
                )
        if self.status is TraceVerificationStatus.FAIL and self.invalid_count == 0:
            raise AurelTraceError("FAIL requires at least one invalid entry")

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_result_id": self.verification_result_id,
            "request_id": self.request_id,
            "status": self.status.value,
            "verified": self.verified,
            "checked_count": self.checked_count,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "first_invalid_index": self.first_invalid_index,
            "chain_head_hash": self.chain_head_hash,
            "findings": [f.to_dict() for f in self.findings],
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class HashChainVerificationSummary:
    """Aggregate over one or more verification results."""

    summary_id: str
    results: tuple[TraceHashVerificationResult, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.TRACE_BOUND

    def __post_init__(self) -> None:
        if not self.summary_id.strip():
            raise AurelTraceError("summary_id must not be empty")

    @property
    def total_results(self) -> int:
        return len(self.results)

    @property
    def pass_count(self) -> int:
        return sum(
            1 for r in self.results if r.status is TraceVerificationStatus.PASS
        )

    @property
    def fail_count(self) -> int:
        return sum(
            1 for r in self.results if r.status is TraceVerificationStatus.FAIL
        )

    @property
    def all_passed(self) -> bool:
        return bool(self.results) and self.pass_count == len(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "total_results": self.total_results,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "all_passed": self.all_passed,
            "results": [r.to_dict() for r in self.results],
            "truth_label": self.truth_label.value,
        }


def _finding(
    kind: TraceHashFindingKind,
    severity: TraceFindingSeverity,
    message: str,
    *,
    request_id: str,
    index: int,
    entry_ref: TraceEntryRef | None,
) -> TraceHashFinding:
    finding_id = "tfind-" + trace_sha(
        canonical_trace_json(
            {
                "request_id": request_id,
                "kind": kind.value,
                "index": index,
                "message": message,
            }
        )
    )[:32]
    return TraceHashFinding(
        finding_id=finding_id,
        finding_kind=kind,
        severity=severity,
        message=message,
        entry_ref=entry_ref,
    )


def _result_id(request_id: str, status: TraceVerificationStatus, checked: int) -> str:
    return "tres-" + trace_sha(
        canonical_trace_json(
            {"request_id": request_id, "status": status.value, "checked": checked}
        )
    )[:32]


def _slice_for_scope(
    request: TraceHashVerificationRequest,
    envelopes: Sequence[CanonicalTraceEventEnvelope],
) -> tuple[int, int]:
    """Return the [start, end) half-open range of indices to check."""

    n = len(envelopes)
    if request.scope is TraceVerificationScope.SINGLE_ENTRY:
        start = request.start_index or 0
        return start, start + 1
    if request.scope is TraceVerificationScope.SEGMENT:
        start = request.start_index or 0
        end = (request.end_index if request.end_index is not None else n - 1) + 1
        return start, end
    return 0, n


def verify_canonical_trace_hash_chain(
    request: TraceHashVerificationRequest,
    envelopes: Sequence[CanonicalTraceEventEnvelope],
    *,
    extra_findings: Sequence[TraceHashFinding] = (),
) -> TraceHashVerificationResult:
    """Verify a canonical envelope chain and return a structured result.

    * Valid supported chain -> PASS (TRACE_INTEGRITY_VERIFIED).
    * Broken supported chain -> FAIL with findings.
    * No/insufficient data -> UNAVAILABLE (or PARTIAL when partly checked).
    * ``extra_findings`` (e.g. unsupported-record findings) fold in and, when
      present, prevent PASS — an unsupported record never silently passes.
    """

    request_id = request.verification_request_id
    findings: list[TraceHashFinding] = list(extra_findings)
    has_unsupported = any(
        f.finding_kind
        in (
            TraceHashFindingKind.UNSUPPORTED_RECORD_TYPE,
            TraceHashFindingKind.SCHEMA_UNKNOWN,
        )
        for f in extra_findings
    )

    n = len(envelopes)
    if n == 0:
        findings.append(
            _finding(
                TraceHashFindingKind.INSUFFICIENT_DATA,
                TraceFindingSeverity.WARNING,
                "no canonical envelopes were provided to verify",
                request_id=request_id,
                index=-1,
                entry_ref=None,
            )
        )
        return _build_result(
            request_id,
            TraceVerificationStatus.UNAVAILABLE,
            checked=0,
            valid=0,
            invalid=0,
            findings=findings,
            first_invalid_index=None,
            chain_head_hash=None,
        )

    start, end = _slice_for_scope(request, envelopes)
    if start < 0 or start >= n or end > n or end <= start:
        findings.append(
            _finding(
                TraceHashFindingKind.INSUFFICIENT_DATA,
                TraceFindingSeverity.WARNING,
                f"requested scope range [{start}, {end}) is out of bounds for {n} envelopes",
                request_id=request_id,
                index=start,
                entry_ref=None,
            )
        )
        return _build_result(
            request_id,
            TraceVerificationStatus.UNAVAILABLE,
            checked=0,
            valid=0,
            invalid=0,
            findings=findings,
            first_invalid_index=None,
            chain_head_hash=None,
        )

    seen_ids: dict[str, int] = {}
    checked = 0
    valid = 0
    invalid = 0
    first_invalid_index: int | None = None
    full_from_genesis = request.scope in (
        TraceVerificationScope.FULL_CHAIN,
        TraceVerificationScope.CHAIN_HEAD,
    )

    for index in range(start, end):
        env = envelopes[index]
        checked += 1
        entry_ref = env.trace_entry_ref
        entry_invalid = False

        # duplicate canonical event id detection
        if env.canonical_event_id in seen_ids:
            entry_invalid = True
            findings.append(
                _finding(
                    TraceHashFindingKind.DUPLICATE_ENTRY_ID,
                    TraceFindingSeverity.ERROR,
                    f"duplicate canonical_event_id at index {index}",
                    request_id=request_id,
                    index=index,
                    entry_ref=entry_ref,
                )
            )
        else:
            seen_ids[env.canonical_event_id] = index

        # previous-hash linkage
        if index == start and full_from_genesis and start == 0:
            expected_prev = GENESIS_ENTRY_HASH
        elif index > start:
            expected_prev = envelopes[index - 1].entry_hash
        else:
            expected_prev = None  # segment/single: no upstream neighbor checked

        if expected_prev is not None and env.previous_entry_hash != expected_prev:
            entry_invalid = True
            findings.append(
                _finding(
                    TraceHashFindingKind.BROKEN_PREVIOUS_HASH,
                    TraceFindingSeverity.CRITICAL,
                    (
                        f"previous_entry_hash at index {index} does not match the "
                        f"prior chain hash"
                    ),
                    request_id=request_id,
                    index=index,
                    entry_ref=entry_ref,
                )
            )

        # entry-hash recomputation (detects payload/entry tampering)
        expected_entry_hash = recompute_entry_hash(
            env.previous_entry_hash, env.payload_hash
        )
        if env.entry_hash != expected_entry_hash:
            entry_invalid = True
            findings.append(
                _finding(
                    TraceHashFindingKind.ENTRY_HASH_MISMATCH,
                    TraceFindingSeverity.CRITICAL,
                    (
                        f"entry_hash at index {index} does not equal "
                        f"sha(previous_entry_hash, payload_hash)"
                    ),
                    request_id=request_id,
                    index=index,
                    entry_ref=entry_ref,
                )
            )

        if entry_invalid:
            invalid += 1
            if first_invalid_index is None:
                first_invalid_index = index
        else:
            valid += 1

    chain_head_hash = envelopes[end - 1].entry_hash

    # chain-head scope check
    if request.scope is TraceVerificationScope.CHAIN_HEAD:
        if request.expected_chain_head != chain_head_hash:
            invalid += 1
            findings.append(
                _finding(
                    TraceHashFindingKind.CHAIN_HEAD_MISMATCH,
                    TraceFindingSeverity.CRITICAL,
                    "actual chain head does not match expected_chain_head",
                    request_id=request_id,
                    index=end - 1,
                    entry_ref=envelopes[end - 1].trace_entry_ref,
                )
            )
            if first_invalid_index is None:
                first_invalid_index = end - 1

    # decide status
    if invalid > 0:
        status = TraceVerificationStatus.FAIL
    elif has_unsupported:
        status = TraceVerificationStatus.PARTIAL
    else:
        status = TraceVerificationStatus.PASS

    return _build_result(
        request_id,
        status,
        checked=checked,
        valid=valid,
        invalid=invalid,
        findings=findings,
        first_invalid_index=first_invalid_index,
        chain_head_hash=chain_head_hash,
    )


def _build_result(
    request_id: str,
    status: TraceVerificationStatus,
    *,
    checked: int,
    valid: int,
    invalid: int,
    findings: Sequence[TraceHashFinding],
    first_invalid_index: int | None,
    chain_head_hash: str | None,
) -> TraceHashVerificationResult:
    verified = status is TraceVerificationStatus.PASS
    truth_label = (
        TraceTruthLabel.TRACE_INTEGRITY_VERIFIED
        if verified
        else TraceTruthLabel.TRACE_BOUND
    )
    return TraceHashVerificationResult(
        verification_result_id=_result_id(request_id, status, checked),
        request_id=request_id,
        status=status,
        verified=verified,
        checked_count=checked,
        valid_count=valid,
        invalid_count=invalid,
        findings=tuple(findings),
        first_invalid_index=first_invalid_index,
        chain_head_hash=chain_head_hash,
        truth_label=truth_label,
    )


def verify_trace_records(
    request: TraceHashVerificationRequest,
    records: Sequence[Any],
) -> TraceHashVerificationResult:
    """Adapt raw ledger records then verify, folding unsupported findings.

    Unsupported records produce an explicit UNSUPPORTED_RECORD_TYPE finding and
    prevent a PASS — they are never silently accepted.
    """

    envelopes: list[CanonicalTraceEventEnvelope] = []
    extra_findings: list[TraceHashFinding] = []
    for index, record in enumerate(records):
        adaptation = try_canonical_envelope(
            record,
            trace_run_ref=request.trace_run_ref,
            sequence_index=index,
        )
        if adaptation.supported and adaptation.envelope is not None:
            envelopes.append(adaptation.envelope)
        else:
            extra_findings.append(
                _finding(
                    TraceHashFindingKind.UNSUPPORTED_RECORD_TYPE,
                    TraceFindingSeverity.ERROR,
                    adaptation.reason
                    or f"unsupported record at index {index}",
                    request_id=request.verification_request_id,
                    index=index,
                    entry_ref=None,
                )
            )
    return verify_canonical_trace_hash_chain(
        request, envelopes, extra_findings=extra_findings
    )
