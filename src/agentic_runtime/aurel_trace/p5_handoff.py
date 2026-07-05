"""P5-TRACE-G handoff contracts from P5 to P6 / P8 / P9.

Each contract tells a downstream domain what trace/evidence material P5 provides,
what invariants must be honored, how it may be consumed, what remains
UNAVAILABLE, and what risks apply. A handoff contract is **not** an implementation
of the downstream domain: `implements_target_domain` is unconstructible, and the
provided artifacts are named by string so this module instantiates nothing from
P6/P8/P9 and never executes/mutates.
"""

from __future__ import annotations

from collections.abc import Sequence
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


class P5HandoffTarget(str, Enum):
    """Closed-world downstream domains P5 hands off to."""

    P6_DATA_OBJECT_PLANE = "P6_DATA_OBJECT_PLANE"
    P8_ATLAS_MODEL_ROUTER = "P8_ATLAS_MODEL_ROUTER"
    P9_CUSTOS_POLICY_RUNTIME = "P9_CUSTOS_POLICY_RUNTIME"


@dataclass(frozen=True)
class P5HandoffContract:
    """Generic handoff contract from P5 to a downstream domain. Not implementation."""

    handoff_id: str
    target_domain: P5HandoffTarget
    provided_artifacts: tuple[str, ...]
    downstream_owned: tuple[str, ...]
    required_invariants: tuple[str, ...]
    consumption_rules: tuple[str, ...]
    unavailable_claims: tuple[str, ...]
    risks: tuple[str, ...]
    truth_label: TraceTruthLabel = TraceTruthLabel.LIVE

    # Locked: a handoff describes a boundary; it never implements the target domain.
    implements_target_domain: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "handoff_id")
        if not isinstance(self.target_domain, P5HandoffTarget):
            raise AurelTraceError("target_domain must be a closed-world P5HandoffTarget")
        if self.implements_target_domain is True:
            raise AurelTraceError(
                "implements_target_domain must be False — a handoff is a contract, "
                "not an implementation of P6/P8/P9"
            )
        if not self.provided_artifacts:
            raise AurelTraceError("a handoff contract must list provided artifacts")
        if not self.unavailable_claims:
            raise AurelTraceError("a handoff contract must list its unavailable claims")
        if self.truth_label is TraceTruthLabel.TRACE_INTEGRITY_VERIFIED:
            raise AurelTraceError("a handoff contract is a LIVE contract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "target_domain": self.target_domain.value,
            "provided_artifacts": list(self.provided_artifacts),
            "downstream_owned": list(self.downstream_owned),
            "required_invariants": list(self.required_invariants),
            "consumption_rules": list(self.consumption_rules),
            "unavailable_claims": list(self.unavailable_claims),
            "risks": list(self.risks),
            "implements_target_domain": self.implements_target_domain,
            "truth_label": self.truth_label.value,
        }


def _handoff_id(target: P5HandoffTarget, provided: Sequence[str]) -> str:
    return "p5ho-" + trace_sha(
        canonical_trace_json({"target": target.value, "provided": list(provided)})
    )[:40]


# Shared invariant/consumption/unavailable language (deterministic constants).
_COMMON_INVARIANTS: tuple[str, ...] = (
    "TRACE_VERIFIED is only a P5-D resolver decision; downstream may reflect it but "
    "must never self-assign it",
    "trace/evidence refs are references, not raw payload; redaction decisions must be "
    "honored for restricted material",
    "P5 objects are frozen read models; consumers must not mutate them",
)
_COMMON_CONSUMPTION: tuple[str, ...] = (
    "consume by reference id (stable, deterministic); do not fabricate P5 objects",
    "preserve missing-evidence / unavailable reasons when re-presenting P5 material",
)


@dataclass(frozen=True)
class P5ToP6Handoff:
    """P5 → P6 (AurelData / Object Plane) handoff. P5 does not own storage."""

    contract: P5HandoffContract

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "P5ToP6Handoff", "contract": self.contract.to_dict()}


@dataclass(frozen=True)
class P5ToP8Handoff:
    """P5 → P8 (Atlas Model Router) handoff. P5 does not route models."""

    contract: P5HandoffContract

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "P5ToP8Handoff", "contract": self.contract.to_dict()}


@dataclass(frozen=True)
class P5ToP9Handoff:
    """P5 → P9 (Custos Policy Runtime) handoff. P5 does not enforce policy."""

    contract: P5HandoffContract

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "P5ToP9Handoff", "contract": self.contract.to_dict()}


def build_p5_to_p6_handoff() -> P5ToP6Handoff:
    provided = (
        "TraceRunRef",
        "TraceEventRef",
        "TraceBindingRef",
        "EvidenceRef",
        "TraceExportManifest",
        "TraceAuditBundle",
        "RedactedTraceView",
        "GoldenThreadGraph",
        "TraceTimeSliceRef",
        "ReplayReadinessAssessment",
        "PersistentTraceBackendProfile",
    )
    contract = P5HandoffContract(
        handoff_id=_handoff_id(P5HandoffTarget.P6_DATA_OBJECT_PLANE, provided),
        target_domain=P5HandoffTarget.P6_DATA_OBJECT_PLANE,
        provided_artifacts=provided,
        downstream_owned=(
            "ObjectRef",
            "DataRef",
            "ArtifactRef",
            "storage locality",
            "zero-copy path",
            "artifact lifecycle",
            "object persistence",
            "data indexing",
            "object/data read models",
        ),
        required_invariants=_COMMON_INVARIANTS
        + (
            "PersistentTraceBackendProfile is a posture, not durable storage; P6 owns "
            "actual object/data persistence",
        ),
        consumption_rules=_COMMON_CONSUMPTION,
        unavailable_claims=(
            "P5 does not implement the P6 object/data plane",
            "P5 does not own ObjectRef/DataRef/ArtifactRef storage",
            "P5 does not implement data indexing, object lifecycle, or zero-copy paths",
        ),
        risks=(
            "P6 must not treat a PersistentTraceBackendProfile LOCAL_DURABLE posture as "
            "production durable storage",
        ),
    )
    return P5ToP6Handoff(contract=contract)


def build_p5_to_p8_handoff() -> P5ToP8Handoff:
    provided = (
        "model/tool execution EvidenceRefs",
        "RuntimeSubmitTraceBinding refs",
        "verifier EvidenceRefs",
        "failure/evidence history (bindings + findings)",
        "TraceVerificationDecision (TRACE_VERIFIED) results",
        "TraceProjectionFeed summaries",
        "GoldenThreadGraph causal history",
        "TraceAuditBundle refs",
    )
    contract = P5HandoffContract(
        handoff_id=_handoff_id(P5HandoffTarget.P8_ATLAS_MODEL_ROUTER, provided),
        target_domain=P5HandoffTarget.P8_ATLAS_MODEL_ROUTER,
        provided_artifacts=provided,
        downstream_owned=(
            "model routing",
            "model selection",
            "model scoring",
            "model budget optimization",
            "routing policy",
            "evaluation-driven routing",
            "router state",
            "model-router enforcement/integration",
        ),
        required_invariants=_COMMON_INVARIANTS
        + (
            "evidence refs describe what was recorded, not model quality; P8 owns "
            "scoring/selection",
        ),
        consumption_rules=_COMMON_CONSUMPTION,
        unavailable_claims=(
            "P5 does not implement the P8 model router",
            "P5 does not select, score, or route models",
        ),
        risks=(
            "P8 must not infer model correctness from TRACE_VERIFIED — it proves "
            "trace/evidence integrity, not semantic/model correctness",
        ),
    )
    return P5ToP8Handoff(contract=contract)


def build_p5_to_p9_handoff() -> P5ToP9Handoff:
    provided = (
        "policy EvidenceRefs",
        "approval EvidenceRefs",
        "privacy/locality labels",
        "redaction decisions",
        "TraceExportManifest / TraceAuditBundle manifests",
        "TraceVerificationDecision (TRACE_VERIFIED) results",
        "P5 truth-label audit",
        "P5 unavailable-surface registry",
        "PersistentTraceIntegrityAssessment",
    )
    contract = P5HandoffContract(
        handoff_id=_handoff_id(P5HandoffTarget.P9_CUSTOS_POLICY_RUNTIME, provided),
        target_domain=P5HandoffTarget.P9_CUSTOS_POLICY_RUNTIME,
        provided_artifacts=provided,
        downstream_owned=(
            "policy enforcement",
            "authority decisions",
            "runtime permission checks",
            "risk gates",
            "compliance runtime rules",
            "operator authority enforcement",
            "Custos enforcement",
            "policy resolver/enforcement integration",
        ),
        required_invariants=_COMMON_INVARIANTS
        + (
            "P5 evidence records what happened; it grants no authority and enforces "
            "nothing — P9 owns enforcement",
        ),
        consumption_rules=_COMMON_CONSUMPTION,
        unavailable_claims=(
            "P5 does not enforce policy or grant authority",
            "P5 does not approve, deny, or allow execution",
            "P5 provides no legal/regulatory compliance certification",
        ),
        risks=(
            "P9 must not treat a P5 audit bundle or export manifest as compliance "
            "certification — those are UNAVAILABLE in P5",
        ),
    )
    return P5ToP9Handoff(contract=contract)


def build_all_p5_handoff_contracts() -> tuple[P5ToP6Handoff, P5ToP8Handoff, P5ToP9Handoff]:
    return (
        build_p5_to_p6_handoff(),
        build_p5_to_p8_handoff(),
        build_p5_to_p9_handoff(),
    )
