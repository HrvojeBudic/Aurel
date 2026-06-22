"""P1.4.11 external doctrine domain model.

External doctrine may influence roadmap mapping. It does not grant capability,
override canon, renumber roadmap modules, or authorize claims beyond evidence.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


class DoctrineSourceType(str, Enum):
    INTERNAL_CANON = "internal_canon"
    EXTERNAL_ARCHITECTURE = "external_architecture"
    RESEARCH_PAPER = "research_paper"
    BUSINESS_DOCTRINE = "business_doctrine"
    BENCHMARK_REPORT = "benchmark_report"
    COMPLIANCE_INPUT = "compliance_input"
    MARKET_ANALYSIS = "market_analysis"
    OPERATOR_NOTE = "operator_note"


class DoctrineAssimilationStatus(str, Enum):
    REFERENCE_ONLY = "REFERENCE_ONLY"
    ROADMAP_INFLUENCING = "ROADMAP_INFLUENCING"
    CANON_COMPATIBLE = "CANON_COMPATIBLE"
    IMPLEMENTATION_PLANNED = "IMPLEMENTATION_PLANNED"
    IMPLEMENTATION_ACTIVE = "IMPLEMENTATION_ACTIVE"
    IMPLEMENTED = "IMPLEMENTED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"


class RoadmapImpactType(str, Enum):
    CONFIRMS_EXISTING = "CONFIRMS_EXISTING"
    REFINES_EXISTING = "REFINES_EXISTING"
    ADDS_REQUIREMENT = "ADDS_REQUIREMENT"
    ADDS_RISK = "ADDS_RISK"
    ADDS_TEST = "ADDS_TEST"
    ADDS_NON_GOAL = "ADDS_NON_GOAL"
    REJECTED_CONFLICT = "REJECTED_CONFLICT"


@dataclass(frozen=True)
class ExternalDoctrineInput:
    doctrine_id: str
    name: str
    version: str | None
    source_type: DoctrineSourceType

    source_path: str | None
    source_hash: str
    ingested_at: str

    summary: str
    key_principles: tuple[str, ...]

    assimilation_status: DoctrineAssimilationStatus
    mapped_roadmap_modules: tuple[str, ...]

    claim_boundaries: tuple[str, ...]
    risk_notes: tuple[str, ...]
    operator_accepted: bool
    capability_evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoadmapImpact:
    doctrine_id: str
    roadmap_module: str
    impact_type: RoadmapImpactType
    impact_summary: str
    implementation_status: str
    required_future_work: tuple[str, ...]


@dataclass(frozen=True)
class DoctrineAssimilationDecision:
    doctrine_id: str
    accepted: bool
    assimilation_status: DoctrineAssimilationStatus

    roadmap_impacts: tuple[RoadmapImpact, ...]
    blocked_claims: tuple[str, ...]
    safe_claim_notes: tuple[str, ...]
    risk_notes: tuple[str, ...]

    reason: str


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple | list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _canonicalize(v) for k, v in sorted(value.items())}
    return value


def compute_doctrine_source_hash(*parts: object) -> str:
    """Compute a stable SHA-256 source identity hash for doctrine intake."""
    payload = json.dumps(
        [_canonicalize(part) for part in parts],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def external_doctrine_input_to_dict(doctrine: ExternalDoctrineInput) -> dict[str, object]:
    return {
        "doctrine_id": doctrine.doctrine_id,
        "name": doctrine.name,
        "version": doctrine.version,
        "source_type": _canonicalize(doctrine.source_type),
        "source_path": doctrine.source_path,
        "source_hash": doctrine.source_hash,
        "ingested_at": doctrine.ingested_at,
        "summary": doctrine.summary,
        "key_principles": list(doctrine.key_principles),
        "assimilation_status": _canonicalize(doctrine.assimilation_status),
        "mapped_roadmap_modules": list(doctrine.mapped_roadmap_modules),
        "claim_boundaries": list(doctrine.claim_boundaries),
        "risk_notes": list(doctrine.risk_notes),
        "operator_accepted": doctrine.operator_accepted,
        "capability_evidence_refs": list(doctrine.capability_evidence_refs),
    }


def roadmap_impact_to_dict(impact: RoadmapImpact) -> dict[str, object]:
    return {
        "doctrine_id": impact.doctrine_id,
        "roadmap_module": impact.roadmap_module,
        "impact_type": _canonicalize(impact.impact_type),
        "impact_summary": impact.impact_summary,
        "implementation_status": impact.implementation_status,
        "required_future_work": list(impact.required_future_work),
    }


def doctrine_assimilation_decision_to_dict(
    decision: DoctrineAssimilationDecision,
) -> dict[str, object]:
    return {
        "doctrine_id": decision.doctrine_id,
        "accepted": decision.accepted,
        "assimilation_status": _canonicalize(decision.assimilation_status),
        "roadmap_impacts": [roadmap_impact_to_dict(i) for i in decision.roadmap_impacts],
        "blocked_claims": list(decision.blocked_claims),
        "safe_claim_notes": list(decision.safe_claim_notes),
        "risk_notes": list(decision.risk_notes),
        "reason": decision.reason,
    }


def doctrine_grants_capability(_doctrine: ExternalDoctrineInput) -> bool:
    """Invariant helper: doctrine registration never grants runtime capability."""
    return False
