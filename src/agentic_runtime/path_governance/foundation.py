"""Path governance foundation status (P1.7.0)."""
from __future__ import annotations

from .labels import ProjectionSourceLabel
from .types import (
    PATH_GOVERNANCE_MODULE_NAME,
    PATH_GOVERNANCE_MODULE_VERSION,
    PATH_GOVERNANCE_TASK_ID,
    FoundationPosture,
    PathGovernanceCapabilityStatus,
)

PATH_GOVERNANCE_UNAVAILABLE_REASONS: dict[str, str] = {
    "Projection/API/Event Contract": (
        "Projection/API/Event Contract scheduled for P1.7.17"
    ),
    "CLI/TUI Binding": "CLI/TUI Binding scheduled for P1.7.18",
    "Resolver": "Path/source resolvers scheduled for P1.7.10 and P1.7.11",
    "Trace hooks": (
        "P1.7.13 path resolution trace and P1.7.14 violation/drift trace payload "
        "models exist; global AurelTrace spine write remains unavailable until "
        "later P1.7 tasks"
    ),
    "Policy bridge": "Policy context bridge scheduled for P1.7.16",
}


def get_path_governance_foundation_status() -> PathGovernanceCapabilityStatus:
    """Return honest P1.7.0 foundation capability status (non-enforcing)."""
    return PathGovernanceCapabilityStatus(
        module_name=PATH_GOVERNANCE_MODULE_NAME,
        module_version=PATH_GOVERNANCE_MODULE_VERSION,
        task_id=PATH_GOVERNANCE_TASK_ID,
        posture=FoundationPosture.FOUNDATION_ONLY,
        enforcement_enabled=False,
        resolver_available=False,
        projection_available=False,
        cli_available=False,
        trace_hook_available=False,
        policy_bridge_available=False,
        source_label=ProjectionSourceLabel.UNAVAILABLE,
        unavailable_reasons=PATH_GOVERNANCE_UNAVAILABLE_REASONS,
        notes=(
            "P1.7.0 foundation only — vocabulary, labels, serialization, "
            "and honest capability reporting.",
            "Enforcement, resolver, projection, CLI, trace hooks, and policy "
            "bridge are deferred to later P1.7 tasks.",
        ),
    )
