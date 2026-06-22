"""P1.4.11 doctrine registry and assimilation evaluation."""
from __future__ import annotations

from .doctrine_claim_boundaries import blocked_doctrine_claims, safe_doctrine_claim_notes
from .doctrine_mapping import map_doctrine_to_roadmap, roadmap_module_ref_is_existing_style
from .external_doctrine import (
    DoctrineAssimilationDecision,
    DoctrineAssimilationStatus,
    DoctrineSourceType,
    ExternalDoctrineInput,
    compute_doctrine_source_hash,
)


P1411_INGESTED_AT = "2026-06-21T00:00:00Z"

_DOCTRINE_REGISTRY: dict[str, ExternalDoctrineInput] = {}

_ROADMAP_MAPPING_STATUSES = {
    DoctrineAssimilationStatus.ROADMAP_INFLUENCING,
    DoctrineAssimilationStatus.IMPLEMENTATION_PLANNED,
    DoctrineAssimilationStatus.IMPLEMENTATION_ACTIVE,
    DoctrineAssimilationStatus.IMPLEMENTED,
}


def _seed_hash(
    doctrine_id: str,
    name: str,
    version: str | None,
    source_type: DoctrineSourceType,
    source_path: str | None,
    summary: str,
    key_principles: tuple[str, ...],
) -> str:
    return compute_doctrine_source_hash(
        "P1.4.11",
        doctrine_id,
        name,
        version,
        source_type,
        source_path,
        summary,
        key_principles,
    )


def _doctrine(
    *,
    doctrine_id: str,
    name: str,
    version: str | None,
    source_type: DoctrineSourceType,
    source_path: str | None,
    summary: str,
    key_principles: tuple[str, ...],
    assimilation_status: DoctrineAssimilationStatus,
    mapped_roadmap_modules: tuple[str, ...],
    claim_boundaries: tuple[str, ...],
    risk_notes: tuple[str, ...],
    operator_accepted: bool,
) -> ExternalDoctrineInput:
    return ExternalDoctrineInput(
        doctrine_id=doctrine_id,
        name=name,
        version=version,
        source_type=source_type,
        source_path=source_path,
        source_hash=_seed_hash(
            doctrine_id,
            name,
            version,
            source_type,
            source_path,
            summary,
            key_principles,
        ),
        ingested_at=P1411_INGESTED_AT,
        summary=summary,
        key_principles=key_principles,
        assimilation_status=assimilation_status,
        mapped_roadmap_modules=mapped_roadmap_modules,
        claim_boundaries=claim_boundaries,
        risk_notes=risk_notes,
        operator_accepted=operator_accepted,
    )


def _build_seed_registry() -> dict[str, ExternalDoctrineInput]:
    seeds = (
        _doctrine(
            doctrine_id="agentic_os_asymmetric_teardown",
            name="The Agentic OS - Asymmetric Architectural Teardown",
            version=None,
            source_type=DoctrineSourceType.EXTERNAL_ARCHITECTURE,
            source_path="external://agentic-os/asymmetric-architectural-teardown",
            summary=(
                "Architecture doctrine for runtime moat, trace integrity, evaluation, "
                "memory, skill, orchestration, and sandbox principles."
            ),
            key_principles=(
                "runtime moat",
                "hash-chained trace",
                "adversarial evaluation",
                "state-transition validation",
                "four-tier memory",
                "procedural skill library",
                "single-write / parallel-read orchestration",
                "sandbox integrity",
            ),
            assimilation_status=DoctrineAssimilationStatus.ROADMAP_INFLUENCING,
            mapped_roadmap_modules=(
                "P1.5 Evaluation Mirror",
                "P3 Mneme Memory Graph",
                "P4 Evaluation Mirror",
                "P8 Coding Agent Harness",
                "P9 Secure Backend Arena",
                "P13 Skill Arena",
                "P20 Sovereign Agentic OS Seal",
            ),
            claim_boundaries=(
                "Does not mean Aurel has production sandboxing.",
                "Does not mean Aurel has deterministic replay yet.",
                "Does not mean Aurel has procedural skill library yet.",
                "Does not mean Aurel has passed Agentic OS Seal.",
            ),
            risk_notes=(
                "Runtime doctrine can create production-readiness overclaim risk.",
                "Sandbox and replay language must remain roadmap-only until verified.",
                "Memory and skill-library principles require future implementation evidence.",
            ),
            operator_accepted=True,
        ),
        _doctrine(
            doctrine_id="abos_design_principles_v1",
            name="ABOS Design Principles Specification v1.0",
            version="1.0",
            source_type=DoctrineSourceType.BUSINESS_DOCTRINE,
            source_path="external://abos/design-principles/v1",
            summary=(
                "Business governance doctrine for runtime governance, compliance, "
                "risk-based autonomy, lifecycle ownership, drift, outcomes, and human-agent operations."
            ),
            key_principles=(
                "runtime governance",
                "compliance-by-design",
                "risk-based autonomy",
                "lifecycle ownership",
                "drift detection",
                "outcome measurement",
                "human-agent operating model",
                "safe gradual evolution",
            ),
            assimilation_status=DoctrineAssimilationStatus.ROADMAP_INFLUENCING,
            mapped_roadmap_modules=(
                "P1.6 Policy Cards",
                "P1.8 Delegation / Agent Identity Mesh",
                "P6 Custos v2",
                "P14 TRiSM Plane",
                "P18 Business Cockpit",
                "P21.8 ABOS Deployment Layer",
            ),
            claim_boundaries=(
                "Does not mean Aurel has ABOS deployment.",
                "Does not mean Aurel can run businesses autonomously.",
                "Does not mean ROI/TCO engine exists yet.",
                "Does not mean Compliance Health Dashboard exists yet.",
            ),
            risk_notes=(
                "Business doctrine can create autonomy and deployment overclaim risk.",
                "Compliance and ROI claims require future evidence before publication.",
                "Human-agent operating model does not change Operator authority.",
            ),
            operator_accepted=True,
        ),
        _doctrine(
            doctrine_id="aether_v0_2",
            name="AETHER v0.2",
            version="0.2",
            source_type=DoctrineSourceType.EXTERNAL_ARCHITECTURE,
            source_path="external://aether/v0.2",
            summary=(
                "Research/intelligence architecture doctrine for goal-driven extraction, "
                "multi-source ingestion, temporal memory, change intelligence, trust, validation, and monitoring."
            ),
            key_principles=(
                "goal-driven extraction",
                "multi-source ingestion",
                "cross-modal reasoning",
                "temporal entity memory",
                "change intelligence",
                "source trust",
                "human validation",
                "predictive monitoring",
            ),
            assimilation_status=DoctrineAssimilationStatus.ROADMAP_INFLUENCING,
            mapped_roadmap_modules=(
                "P3 Mneme temporal memory",
                "P10 Noesis change significance",
                "P18 Workspace / Artifact Studio",
                "P19 Aurel Researcher",
                "P21.5 Scientific / Strategic Research Lab",
            ),
            claim_boundaries=(
                "Does not mean Aurel has multimodal intelligence extraction.",
                "Does not mean Aurel has live monitoring.",
                "Does not mean Aurel has predictive monitoring yet.",
                "Does not mean Aurel has AETHER implemented.",
            ),
            risk_notes=(
                "Research doctrine can create multimodal and monitoring overclaim risk.",
                "Source trust and human validation require future implementation evidence.",
                "Predictive monitoring remains roadmap-only until verified.",
            ),
            operator_accepted=True,
        ),
    )
    return {doctrine.doctrine_id: doctrine for doctrine in seeds}


def get_doctrine_registry() -> dict[str, ExternalDoctrineInput]:
    if not _DOCTRINE_REGISTRY:
        _DOCTRINE_REGISTRY.update(_build_seed_registry())
    return _DOCTRINE_REGISTRY


def list_external_doctrine_inputs() -> tuple[ExternalDoctrineInput, ...]:
    return tuple(get_doctrine_registry().values())


def get_external_doctrine_input(doctrine_id: str) -> ExternalDoctrineInput | None:
    return get_doctrine_registry().get(doctrine_id)


def register_external_doctrine_input(
    doctrine: ExternalDoctrineInput,
) -> ExternalDoctrineInput:
    registry = get_doctrine_registry()
    candidate = tuple(registry.values()) + (doctrine,)
    errors = validate_doctrine_registry(candidate)
    if errors:
        raise ValueError("; ".join(errors))
    registry[doctrine.doctrine_id] = doctrine
    return doctrine


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())


def _validate_doctrine(doctrine: ExternalDoctrineInput) -> tuple[str, ...]:
    errors: list[str] = []
    prefix = doctrine.doctrine_id or "<missing_doctrine_id>"

    if not doctrine.doctrine_id:
        errors.append("missing doctrine_id")
    if not doctrine.name:
        errors.append(f"{prefix}: missing name")
    if not isinstance(doctrine.source_type, DoctrineSourceType):
        errors.append(f"{prefix}: unknown source_type {doctrine.source_type!r}")
    if not doctrine.source_hash:
        errors.append(f"{prefix}: missing source_hash")
    elif not _is_sha256_hex(doctrine.source_hash):
        errors.append(f"{prefix}: source_hash must be a SHA-256 hex digest")
    if doctrine.assimilation_status is None:
        errors.append(f"{prefix}: missing assimilation_status")
        return tuple(errors)
    if not isinstance(doctrine.assimilation_status, DoctrineAssimilationStatus):
        errors.append(f"{prefix}: unknown assimilation_status {doctrine.assimilation_status!r}")
        return tuple(errors)

    status = doctrine.assimilation_status
    if status in _ROADMAP_MAPPING_STATUSES and not doctrine.mapped_roadmap_modules:
        errors.append(f"{prefix}: roadmap-influencing doctrine requires roadmap mapping")
    if status == DoctrineAssimilationStatus.REJECTED and doctrine.mapped_roadmap_modules:
        errors.append(f"{prefix}: rejected doctrine cannot create roadmap impact")
    if status == DoctrineAssimilationStatus.IMPLEMENTED and not doctrine.capability_evidence_refs:
        errors.append(f"{prefix}: implemented status requires capability evidence")
    if status == DoctrineAssimilationStatus.CANON_COMPATIBLE and not doctrine.operator_accepted:
        errors.append(f"{prefix}: operator acceptance is required before canon compatibility")
    if status in _ROADMAP_MAPPING_STATUSES and not doctrine.claim_boundaries:
        errors.append(f"{prefix}: roadmap-influencing doctrine requires claim boundaries")
    if not isinstance(doctrine.operator_accepted, bool):
        errors.append(f"{prefix}: operator_accepted must be boolean")

    for module in doctrine.mapped_roadmap_modules:
        if not roadmap_module_ref_is_existing_style(module):
            errors.append(f"{prefix}: doctrine cannot renumber roadmap module {module!r}")

    return tuple(errors)


def validate_doctrine_registry(
    doctrines: tuple[ExternalDoctrineInput, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for doctrine in doctrines:
        errors.extend(_validate_doctrine(doctrine))
        if doctrine.doctrine_id in seen:
            errors.append(f"duplicate doctrine_id {doctrine.doctrine_id!r}")
        seen.add(doctrine.doctrine_id)
    return tuple(errors)


def evaluate_doctrine_assimilation(
    doctrine: ExternalDoctrineInput,
) -> DoctrineAssimilationDecision:
    validation_errors = validate_doctrine_registry((doctrine,))
    if validation_errors:
        return DoctrineAssimilationDecision(
            doctrine_id=doctrine.doctrine_id,
            accepted=False,
            assimilation_status=doctrine.assimilation_status,
            roadmap_impacts=(),
            blocked_claims=blocked_doctrine_claims(doctrine),
            safe_claim_notes=safe_doctrine_claim_notes(doctrine),
            risk_notes=tuple(doctrine.risk_notes),
            reason="invalid doctrine: " + "; ".join(validation_errors),
        )

    accepted = (
        doctrine.operator_accepted
        and doctrine.assimilation_status
        not in (DoctrineAssimilationStatus.REJECTED, DoctrineAssimilationStatus.DEPRECATED)
    )
    impacts = map_doctrine_to_roadmap(doctrine)
    if doctrine.assimilation_status == DoctrineAssimilationStatus.REJECTED:
        reason = "Doctrine rejected; no roadmap impact is created."
    elif accepted:
        reason = (
            "Doctrine accepted for mapping. It may influence roadmap, but it does not "
            "grant capability or override P1.4.10 claim boundaries."
        )
    else:
        reason = "Doctrine recorded but not operator-accepted for assimilation."

    return DoctrineAssimilationDecision(
        doctrine_id=doctrine.doctrine_id,
        accepted=accepted,
        assimilation_status=doctrine.assimilation_status,
        roadmap_impacts=impacts,
        blocked_claims=blocked_doctrine_claims(doctrine),
        safe_claim_notes=safe_doctrine_claim_notes(doctrine),
        risk_notes=tuple(doctrine.risk_notes),
        reason=reason,
    )
