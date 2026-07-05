"""P5-TRACE-F persistent trace backend integrity posture (assessment only).

Describes and assesses a trace persistence backend's integrity posture. It does
**not** migrate storage, write to a database, replace the trace backend, or make
any production-grade durability / distributed-ledger claim. ``LOCAL_DURABLE`` is
a local persistence posture only — never a production distributed ledger.
``IN_MEMORY`` is never durable. Missing guarantees are listed explicitly.
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

LOCAL_DURABLE_LIMITATION = (
    "LOCAL_DURABLE is a local persistence posture only; it is NOT a production-grade "
    "distributed ledger and does not certify production durability"
)


class PersistentTraceBackendKind(str, Enum):
    IN_MEMORY = "IN_MEMORY"
    JSONL = "JSONL"
    FILE_SYSTEM = "FILE_SYSTEM"
    SQLITE = "SQLITE"
    EXTERNAL_DB = "EXTERNAL_DB"
    UNKNOWN = "UNKNOWN"


class PersistentTraceBackendStatus(str, Enum):
    DEV_ONLY = "DEV_ONLY"
    LOCAL_DURABLE = "LOCAL_DURABLE"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class PersistentIntegrityRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class PersistentTraceBackendProfile:
    """Describes a trace persistence backend's integrity posture. Posture only."""

    profile_id: str
    backend_kind: PersistentTraceBackendKind
    backend_status: PersistentTraceBackendStatus
    append_only_claim: bool = False
    hash_chain_supported: bool = False
    receipt_supported: bool = False
    fsync_claim: bool = False
    tamper_detection_supported: bool = False
    schema_compatibility_supported: bool = False
    privacy_label_supported: bool = False
    export_manifest_supported: bool = False
    limitations: tuple[str, ...] = ()
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a profile describes; it never migrates/replaces/certifies storage.
    migrates_storage: bool = False
    replaces_backend: bool = False
    is_distributed_ledger: bool = False
    certifies_durability: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "profile_id")
        for field_name in (
            "migrates_storage",
            "replaces_backend",
            "is_distributed_ledger",
            "certifies_durability",
        ):
            if getattr(self, field_name) is True:
                raise AurelTraceError(
                    f"{field_name} must be False — a backend profile is a posture, "
                    "not storage migration/replacement/ledger/certification"
                )
        if (
            self.backend_status is PersistentTraceBackendStatus.LOCAL_DURABLE
            and LOCAL_DURABLE_LIMITATION not in self.limitations
        ):
            raise AurelTraceError(
                "a LOCAL_DURABLE profile must record the not-a-production-ledger limitation"
            )
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a backend profile is a LIVE contract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "backend_kind": self.backend_kind.value,
            "backend_status": self.backend_status.value,
            "append_only_claim": self.append_only_claim,
            "hash_chain_supported": self.hash_chain_supported,
            "receipt_supported": self.receipt_supported,
            "fsync_claim": self.fsync_claim,
            "tamper_detection_supported": self.tamper_detection_supported,
            "schema_compatibility_supported": self.schema_compatibility_supported,
            "privacy_label_supported": self.privacy_label_supported,
            "export_manifest_supported": self.export_manifest_supported,
            "limitations": list(self.limitations),
            "migrates_storage": self.migrates_storage,
            "replaces_backend": self.replaces_backend,
            "is_distributed_ledger": self.is_distributed_ledger,
            "certifies_durability": self.certifies_durability,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class PersistentTraceIntegrityAssessment:
    """Assesses whether a backend has enough integrity guarantees. Honest, not certified."""

    assessment_id: str
    backend_profile: PersistentTraceBackendProfile
    status: PersistentTraceBackendStatus
    checks_passed: tuple[str, ...]
    checks_missing: tuple[str, ...]
    checks_unsupported: tuple[str, ...]
    risk_level: PersistentIntegrityRisk
    limitations: tuple[str, ...]
    recommendations: tuple[str, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    def __post_init__(self) -> None:
        require_nonempty(self, "assessment_id")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a backend integrity assessment is a LIVE contract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "backend_profile": self.backend_profile.to_dict(),
            "status": self.status.value,
            "checks_passed": list(self.checks_passed),
            "checks_missing": list(self.checks_missing),
            "checks_unsupported": list(self.checks_unsupported),
            "risk_level": self.risk_level.value,
            "limitations": list(self.limitations),
            "recommendations": list(self.recommendations),
            "truth_label": self.truth_label.value,
        }


def profile_persistent_trace_backend(
    *,
    backend_kind: PersistentTraceBackendKind,
    append_only_claim: bool = False,
    hash_chain_supported: bool = False,
    receipt_supported: bool = False,
    fsync_claim: bool = False,
    tamper_detection_supported: bool = False,
    schema_compatibility_supported: bool = False,
    privacy_label_supported: bool = False,
    export_manifest_supported: bool = False,
    profile_id: str = "persistent-trace-backend-profile.p5-trace-f.v1",
) -> PersistentTraceBackendProfile:
    """Derive a backend integrity posture from declared capability flags.

    IN_MEMORY is DEV_ONLY (never durable). JSONL/FILE_SYSTEM/SQLITE reach
    LOCAL_DURABLE only when append-only + hash-chain + fsync are all claimed, else
    PARTIAL. EXTERNAL_DB is UNKNOWN/UNAVAILABLE unless durability flags are given.
    UNKNOWN is UNSUPPORTED.
    """

    durable_local = append_only_claim and hash_chain_supported and fsync_claim
    limitations: list[str] = []

    if backend_kind is PersistentTraceBackendKind.IN_MEMORY:
        status = PersistentTraceBackendStatus.DEV_ONLY
        limitations.append("IN_MEMORY is volatile — durability is UNAVAILABLE")
    elif backend_kind in (
        PersistentTraceBackendKind.JSONL,
        PersistentTraceBackendKind.FILE_SYSTEM,
        PersistentTraceBackendKind.SQLITE,
    ):
        if durable_local:
            status = PersistentTraceBackendStatus.LOCAL_DURABLE
            limitations.append(LOCAL_DURABLE_LIMITATION)
        else:
            status = PersistentTraceBackendStatus.PARTIAL
            limitations.append(
                "missing append-only/hash-chain/fsync claims — durability is PARTIAL"
            )
    elif backend_kind is PersistentTraceBackendKind.EXTERNAL_DB:
        if durable_local:
            status = PersistentTraceBackendStatus.PARTIAL
            limitations.append(
                "external DB durability claimed but not independently verified here"
            )
        else:
            status = PersistentTraceBackendStatus.UNAVAILABLE
            limitations.append(
                "external DB integrity not profiled — UNAVAILABLE without explicit claims"
            )
    else:  # UNKNOWN
        status = PersistentTraceBackendStatus.UNSUPPORTED
        limitations.append("unknown backend kind — UNSUPPORTED, fails closed")

    return PersistentTraceBackendProfile(
        profile_id=profile_id,
        backend_kind=backend_kind,
        backend_status=status,
        append_only_claim=append_only_claim,
        hash_chain_supported=hash_chain_supported,
        receipt_supported=receipt_supported,
        fsync_claim=fsync_claim,
        tamper_detection_supported=tamper_detection_supported,
        schema_compatibility_supported=schema_compatibility_supported,
        privacy_label_supported=privacy_label_supported,
        export_manifest_supported=export_manifest_supported,
        limitations=tuple(limitations),
    )


_CHECKS: tuple[tuple[str, str], ...] = (
    ("append_only", "append_only_claim"),
    ("hash_chain", "hash_chain_supported"),
    ("receipt", "receipt_supported"),
    ("fsync_durability", "fsync_claim"),
    ("tamper_detection", "tamper_detection_supported"),
    ("schema_compatibility", "schema_compatibility_supported"),
    ("privacy_labels", "privacy_label_supported"),
    ("export_compatibility", "export_manifest_supported"),
)


def _risk_from(profile: PersistentTraceBackendProfile, missing: int) -> PersistentIntegrityRisk:
    if profile.backend_status in (
        PersistentTraceBackendStatus.UNSUPPORTED,
        PersistentTraceBackendStatus.UNAVAILABLE,
        PersistentTraceBackendStatus.ERROR,
    ):
        return PersistentIntegrityRisk.CRITICAL
    if profile.backend_status is PersistentTraceBackendStatus.DEV_ONLY:
        return PersistentIntegrityRisk.HIGH
    if missing == 0:
        return PersistentIntegrityRisk.LOW
    if missing <= 2:
        return PersistentIntegrityRisk.MEDIUM
    return PersistentIntegrityRisk.HIGH


def assess_persistent_trace_backend(
    profile: PersistentTraceBackendProfile,
    *,
    assessment_id: str = "persistent-trace-integrity-assessment.p5-trace-f.v1",
) -> PersistentTraceIntegrityAssessment:
    """Assess a backend profile against the eight integrity checks. Honest only."""

    passed: list[str] = []
    missing: list[str] = []
    unsupported: list[str] = []

    for check_name, attr in _CHECKS:
        # Durability checks are structurally unsupported for a volatile backend.
        if (
            profile.backend_kind is PersistentTraceBackendKind.IN_MEMORY
            and check_name in ("append_only", "fsync_durability")
        ):
            unsupported.append(check_name)
            continue
        if getattr(profile, attr) is True:
            passed.append(check_name)
        else:
            missing.append(check_name)

    risk = _risk_from(profile, len(missing))
    recommendations: list[str] = []
    if "hash_chain" in missing:
        recommendations.append("enable hash-chain verification for tamper evidence")
    if "fsync_durability" in missing and profile.backend_kind is not (
        PersistentTraceBackendKind.IN_MEMORY
    ):
        recommendations.append("declare/verify fsync durability before LOCAL_DURABLE")
    if profile.backend_status is PersistentTraceBackendStatus.DEV_ONLY:
        recommendations.append("move off IN_MEMORY for any durability guarantee")

    limitations = tuple(profile.limitations) + (
        "this assessment describes integrity posture only; it does not certify "
        "production durability and implements no storage migration",
    )

    return PersistentTraceIntegrityAssessment(
        assessment_id=assessment_id,
        backend_profile=profile,
        status=profile.backend_status,
        checks_passed=tuple(passed),
        checks_missing=tuple(missing),
        checks_unsupported=tuple(unsupported),
        risk_level=risk,
        limitations=limitations,
        recommendations=tuple(recommendations),
    )
