"""Roadmap mapping for P1.4.11 external doctrine."""
from __future__ import annotations

import re

from .external_doctrine import (
    DoctrineAssimilationStatus,
    ExternalDoctrineInput,
    RoadmapImpact,
    RoadmapImpactType,
)


_ROADMAP_REF_RE = re.compile(r"^P\d+(?:\.\d+)*(?:\s+.+)?$")

_IMPLEMENTED_STATUSES = {
    DoctrineAssimilationStatus.IMPLEMENTATION_ACTIVE: "implementation_active",
    DoctrineAssimilationStatus.IMPLEMENTED: "implemented_with_evidence",
}

_IMPACT_TYPE_BY_DOCTRINE: dict[str, RoadmapImpactType] = {
    "agentic_os_asymmetric_teardown": RoadmapImpactType.REFINES_EXISTING,
    "abos_design_principles_v1": RoadmapImpactType.ADDS_REQUIREMENT,
    "aether_v0_2": RoadmapImpactType.ADDS_REQUIREMENT,
}

_FUTURE_WORK_BY_DOCTRINE: dict[str, tuple[str, ...]] = {
    "agentic_os_asymmetric_teardown": (
        "Define evidence gates for runtime moat claims before P20 seal work.",
        "Add tests for trace replay, sandbox integrity, and evaluator isolation in future modules.",
        "Keep Agentic OS doctrine mapped into existing roadmap modules only.",
    ),
    "abos_design_principles_v1": (
        "Define ABOS deployment evidence requirements before P21.8.",
        "Add compliance, lifecycle ownership, and outcome measurement evidence before business claims.",
        "Keep business autonomy claims routed through P1.4.10 until verified.",
    ),
    "aether_v0_2": (
        "Define P19 research/intelligence evidence before claiming AETHER implementation.",
        "Add source trust, temporal memory, and human validation tests in future research layers.",
        "Keep multimodal and monitoring claims roadmap-only until implementation evidence exists.",
    ),
}


def roadmap_module_ref_is_existing_style(roadmap_module: str) -> bool:
    """Return True when a mapping references an existing P-numbered roadmap slot."""
    return bool(_ROADMAP_REF_RE.match(roadmap_module))


def map_doctrine_to_roadmap(
    doctrine: ExternalDoctrineInput,
) -> tuple[RoadmapImpact, ...]:
    """Map doctrine into existing roadmap modules.

    Rejected doctrine cannot create roadmap impact. Mapping records influence only;
    it is not implementation evidence.
    """
    if doctrine.assimilation_status == DoctrineAssimilationStatus.REJECTED:
        return ()

    impact_type = _IMPACT_TYPE_BY_DOCTRINE.get(
        doctrine.doctrine_id,
        RoadmapImpactType.REFINES_EXISTING,
    )
    implementation_status = _IMPLEMENTED_STATUSES.get(
        doctrine.assimilation_status,
        "not_implemented_by_doctrine",
    )
    required_future_work = _FUTURE_WORK_BY_DOCTRINE.get(
        doctrine.doctrine_id,
        (
            "Convert doctrine influence into explicit implementation requirements.",
            "Route any capability claim through P1.4.10 before publication.",
        ),
    )

    impacts: list[RoadmapImpact] = []
    for roadmap_module in doctrine.mapped_roadmap_modules:
        impacts.append(
            RoadmapImpact(
                doctrine_id=doctrine.doctrine_id,
                roadmap_module=roadmap_module,
                impact_type=impact_type,
                impact_summary=(
                    f"{doctrine.name} influences {roadmap_module}; "
                    "this mapping does not mark the module implemented."
                ),
                implementation_status=implementation_status,
                required_future_work=required_future_work,
            )
        )
    return tuple(impacts)
