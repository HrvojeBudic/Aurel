"""AurelShell seven-surface registry (P2.0-A / P2.0.2–P2.0.8).

Canonical v5.5 surface contracts for Aurel CRO, HQ, CORP, HUB, IDE, SYSTEM,
and Settings. Registry is contract foundation only — not product UI or routes.

Architectural law:
  - Surfaces are projections; surfaces are not source-of-truth systems.
  - SYSTEM is operator-only root; Settings is non-root configuration.
  - HUB is not tool execution authority; IDE is not runtime execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contracts import (
    AurelShellErrorCode,
    AurelShellValidationError,
    AurelShellSideEffectProof,
    _CanonicalMixin,
    _all_false_side_effects,
    _hash_payload,
    _reject,
    to_canonical_json,
)

AUREL_SURFACE_CONTRACT_VERSION = "aurel_surface_contract.v1"
AUREL_SURFACE_REGISTRY_VERSION = "aurel_surface_registry.v1"

CANONICAL_SURFACE_ORDER: tuple[str, ...] = (
    "aurel_cro",
    "hq",
    "corp",
    "hub",
    "ide",
    "system",
    "settings",
)

OLD_SURFACE_TAXONOMY: frozenset[str] = frozenset(
    {
        "Forum",
        "Archivium",
        "A-Hub",
        "S-Hub",
        "L-Hub",
        "Workspace",
        "Strategy",
        "Society Hub",
    }
)


class AurelSurfaceKind(str, Enum):
    """Closed-world v5.5 P2.0 surface kinds."""

    AUREL_CRO = "AUREL_CRO"
    HQ = "HQ"
    CORP = "CORP"
    HUB = "HUB"
    IDE = "IDE"
    SYSTEM = "SYSTEM"
    SETTINGS = "SETTINGS"


SURFACE_KIND_DISPLAY_NAMES: dict[AurelSurfaceKind, str] = {
    AurelSurfaceKind.AUREL_CRO: "Aurel CRO",
    AurelSurfaceKind.HQ: "HQ",
    AurelSurfaceKind.CORP: "CORP",
    AurelSurfaceKind.HUB: "HUB",
    AurelSurfaceKind.IDE: "IDE",
    AurelSurfaceKind.SYSTEM: "SYSTEM",
    AurelSurfaceKind.SETTINGS: "Settings",
}

SURFACE_KIND_IDS: dict[AurelSurfaceKind, str] = {
    AurelSurfaceKind.AUREL_CRO: "aurel_cro",
    AurelSurfaceKind.HQ: "hq",
    AurelSurfaceKind.CORP: "corp",
    AurelSurfaceKind.HUB: "hub",
    AurelSurfaceKind.IDE: "ide",
    AurelSurfaceKind.SYSTEM: "system",
    AurelSurfaceKind.SETTINGS: "settings",
}

CANONICAL_SURFACE_KINDS: tuple[AurelSurfaceKind, ...] = (
    AurelSurfaceKind.AUREL_CRO,
    AurelSurfaceKind.HQ,
    AurelSurfaceKind.CORP,
    AurelSurfaceKind.HUB,
    AurelSurfaceKind.IDE,
    AurelSurfaceKind.SYSTEM,
    AurelSurfaceKind.SETTINGS,
)


class AurelSurfaceTruthLabel(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_MODEL_ONLY = "READ_MODEL_ONLY"
    SURFACE_CONTRACT_ONLY = "SURFACE_CONTRACT_ONLY"
    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"
    OPERATOR_ONLY_CONTRACT = "OPERATOR_ONLY_CONTRACT"
    NON_ROOT_CONFIG_CONTRACT = "NON_ROOT_CONFIG_CONTRACT"
    NOT_LIVE = "NOT_LIVE"


class AurelSurfaceAvailability(str, Enum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


class AurelSurfaceAgentAccess(str, Enum):
    GOVERNED = "governed"
    FORBIDDEN = "forbidden"
    NON_ROOT_ONLY = "non_root_only"


@dataclass(frozen=True)
class AurelSurfaceSourceOfTruth(_CanonicalMixin):
    """Source-of-truth relation for a surface — projection only in P2.0-A."""

    owns_truth: bool
    projection_only: bool
    read_model_only: bool
    description: str


@dataclass(frozen=True)
class AurelSurfaceAuthorityBoundary(_CanonicalMixin):
    """Authority boundary — what a surface must not claim."""

    autonomous_execution: bool
    business_execution: bool
    tool_execution: bool
    runtime_execution: bool
    permission_grant: bool
    root_authority_grant: bool
    bypass_validation_discipline: bool
    description: str


@dataclass(frozen=True)
class AurelSurfaceCapabilityBoundary(_CanonicalMixin):
    """Capability boundary seed — contract labels only."""

    agent_access: AurelSurfaceAgentAccess
    configuration_scope: str
    runtime_scope: str
    description: str


@dataclass(frozen=True)
class AurelSurfaceContract(_CanonicalMixin):
    """Single canonical surface contract."""

    schema_version: str
    surface_id: str
    display_name: str
    surface_kind: AurelSurfaceKind
    purpose: str
    operator_value: str
    source_of_truth_relation: AurelSurfaceSourceOfTruth
    authority_boundary: AurelSurfaceAuthorityBoundary
    agent_access_boundary: AurelSurfaceAgentAccess
    runtime_boundary: str
    configuration_boundary: str
    default_availability: AurelSurfaceAvailability
    truth_label: AurelSurfaceTruthLabel
    secondary_truth_labels: tuple[AurelSurfaceTruthLabel, ...]
    unavailable_reason: str
    non_goals: tuple[str, ...]
    side_effects: AurelShellSideEffectProof
    surface_contract_hash: str


@dataclass(frozen=True)
class AurelSurfaceRegistry(_CanonicalMixin):
    """Registry of exactly seven v5.5 canonical surfaces."""

    schema_version: str
    surfaces: tuple[AurelSurfaceContract, ...]
    surface_count: int
    canonical_surface_ids: tuple[str, ...]
    side_effects: AurelShellSideEffectProof
    registry_hash: str


_SURFACE_DEFINITIONS: dict[AurelSurfaceKind, dict[str, Any]] = {
    AurelSurfaceKind.AUREL_CRO: {
        "purpose": "Operator-facing command/self-command surface",
        "operator_value": (
            "Exposes operator command intent and self-command contract state "
            "without autonomous execution authority"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Projection/read model only; not autonomous authority",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Not autonomous execution authority; does not bypass Custos/Trace laws",
        ),
        "agent_access": AurelSurfaceAgentAccess.GOVERNED,
        "runtime_boundary": "no_runtime_execution",
        "configuration_boundary": "non_root_command_configuration_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (),
        "unavailable_reason": "surface_contract_only_no_autonomous_cro_runtime",
        "non_goals": (
            "no_autonomous_cro_runtime",
            "no_self_command_execution",
            "no_p18_product_layer",
        ),
    },
    AurelSurfaceKind.HQ: {
        "purpose": "Sovereign operations command view",
        "operator_value": (
            "Projects sovereign operations command state without owning "
            "runtime source of truth"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Projection/read model only; HQ is not runtime source of truth",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Operations view only; does not mutate runtime",
        ),
        "agent_access": AurelSurfaceAgentAccess.GOVERNED,
        "runtime_boundary": "no_runtime_mutation",
        "configuration_boundary": "operations_view_configuration_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (),
        "unavailable_reason": "surface_contract_only_no_hq_ui_or_operations_runtime",
        "non_goals": ("no_hq_ui", "no_operations_runtime", "no_live_command_board"),
    },
    AurelSurfaceKind.CORP: {
        "purpose": "BusinessEnvironment operating view",
        "operator_value": (
            "Projects BusinessEnvironment operating state without business "
            "execution authority or business truth ownership"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Shell projection only; does not own business truth",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Not business execution authority",
        ),
        "agent_access": AurelSurfaceAgentAccess.GOVERNED,
        "runtime_boundary": "no_business_execution",
        "configuration_boundary": "business_environment_view_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (),
        "unavailable_reason": "surface_contract_only_no_business_environment_mutation",
        "non_goals": (
            "no_business_execution",
            "no_agy_runtime",
            "no_business_environment_mutation",
        ),
    },
    AurelSurfaceKind.HUB: {
        "purpose": "Tool constellation / tool entry view",
        "operator_value": (
            "Exposes tool constellation entry state without tool execution "
            "authority or permission grants"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Tool entry projection only; not tool execution authority",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Not tool execution authority; does not grant tool permission",
        ),
        "agent_access": AurelSurfaceAgentAccess.GOVERNED,
        "runtime_boundary": "no_tool_execution",
        "configuration_boundary": "tool_constellation_view_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (),
        "unavailable_reason": "surface_contract_only_no_tool_execution_or_permission",
        "non_goals": (
            "no_tool_execution",
            "no_tool_permission_grants",
            "no_hub_product_ui",
        ),
    },
    AurelSurfaceKind.IDE: {
        "purpose": "CodeOps engineering surface",
        "operator_value": (
            "Exposes CodeOps engineering work state without runtime execution "
            "authority or validation/git/report discipline bypass"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Engineering projection only; not runtime execution authority",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Does not bypass git/validation/report discipline",
        ),
        "agent_access": AurelSurfaceAgentAccess.GOVERNED,
        "runtime_boundary": "no_runtime_execution_authority",
        "configuration_boundary": "codeops_engineering_view_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (),
        "unavailable_reason": "surface_contract_only_no_ide_implementation",
        "non_goals": (
            "no_ide_implementation",
            "no_coding_agent_harness",
            "no_runtime_execution",
        ),
    },
    AurelSurfaceKind.SYSTEM: {
        "purpose": "Operator-only root control surface",
        "operator_value": (
            "Declares operator-only root control contract boundary without "
            "granting root authority to agents in this pack"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Root control contract only; not runtime enforcement",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Operator-only; does not grant root authority in P2.0-A",
        ),
        "agent_access": AurelSurfaceAgentAccess.FORBIDDEN,
        "runtime_boundary": "operator_only_no_agent_access",
        "configuration_boundary": "root_system_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (AurelSurfaceTruthLabel.OPERATOR_ONLY_CONTRACT,),
        "unavailable_reason": "surface_contract_only_no_system_ui_or_enforcement_runtime",
        "non_goals": (
            "no_system_ui",
            "no_enforcement_runtime",
            "no_agent_access",
            "no_settings_overlap",
        ),
    },
    AurelSurfaceKind.SETTINGS: {
        "purpose": "Non-root configuration surface",
        "operator_value": (
            "Declares non-root configuration contract boundary without SYSTEM "
            "actions or root authority grants"
        ),
        "source_of_truth": AurelSurfaceSourceOfTruth(
            owns_truth=False,
            projection_only=True,
            read_model_only=True,
            description="Non-root configuration contract only",
        ),
        "authority_boundary": AurelSurfaceAuthorityBoundary(
            autonomous_execution=False,
            business_execution=False,
            tool_execution=False,
            runtime_execution=False,
            permission_grant=False,
            root_authority_grant=False,
            bypass_validation_discipline=False,
            description="Cannot grant root authority or perform SYSTEM actions",
        ),
        "agent_access": AurelSurfaceAgentAccess.NON_ROOT_ONLY,
        "runtime_boundary": "non_root_configuration_only",
        "configuration_boundary": "non_root_config_only",
        "truth_label": AurelSurfaceTruthLabel.SURFACE_CONTRACT_ONLY,
        "secondary_truth_labels": (AurelSurfaceTruthLabel.NON_ROOT_CONFIG_CONTRACT,),
        "unavailable_reason": "surface_contract_only_no_settings_ui_or_root_control",
        "non_goals": (
            "no_settings_ui",
            "no_root_control",
            "no_system_authority",
        ),
    },
}


def build_surface_contract(
    kind: AurelSurfaceKind | str,
) -> AurelSurfaceContract:
    if isinstance(kind, str):
        kind = AurelSurfaceKind(kind)
    definition = _SURFACE_DEFINITIONS[kind]
    side_effects = _all_false_side_effects()
    payload = {
        "schema_version": AUREL_SURFACE_CONTRACT_VERSION,
        "surface_id": SURFACE_KIND_IDS[kind],
        "display_name": SURFACE_KIND_DISPLAY_NAMES[kind],
        "surface_kind": kind,
        "purpose": definition["purpose"],
        "operator_value": definition["operator_value"],
        "source_of_truth_relation": definition["source_of_truth"],
        "authority_boundary": definition["authority_boundary"],
        "agent_access_boundary": definition["agent_access"],
        "runtime_boundary": definition["runtime_boundary"],
        "configuration_boundary": definition["configuration_boundary"],
        "default_availability": AurelSurfaceAvailability.CONTRACT_ONLY,
        "truth_label": definition["truth_label"],
        "secondary_truth_labels": definition["secondary_truth_labels"],
        "unavailable_reason": definition["unavailable_reason"],
        "non_goals": definition["non_goals"],
        "side_effects": side_effects,
    }
    return AurelSurfaceContract(
        **payload,
        surface_contract_hash=_hash_payload(payload),
    )


def build_default_surface_registry() -> AurelSurfaceRegistry:
    surfaces = tuple(
        build_surface_contract(kind)
        for kind in (
            AurelSurfaceKind.AUREL_CRO,
            AurelSurfaceKind.HQ,
            AurelSurfaceKind.CORP,
            AurelSurfaceKind.HUB,
            AurelSurfaceKind.IDE,
            AurelSurfaceKind.SYSTEM,
            AurelSurfaceKind.SETTINGS,
        )
    )
    canonical_ids = tuple(surface.surface_id for surface in surfaces)
    side_effects = _all_false_side_effects()
    payload = {
        "schema_version": AUREL_SURFACE_REGISTRY_VERSION,
        "surfaces": surfaces,
        "surface_count": len(surfaces),
        "canonical_surface_ids": canonical_ids,
        "side_effects": side_effects,
    }
    return AurelSurfaceRegistry(**payload, registry_hash=_hash_payload(payload))


def assert_surface_registry_has_exactly_v5_5_surfaces(
    registry: AurelSurfaceRegistry,
) -> None:
    if registry.surface_count != 7:
        _reject(
            f"expected exactly 7 surfaces, got {registry.surface_count}",
            field="surface_count",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    ids = [surface.surface_id for surface in registry.surfaces]
    if ids != list(CANONICAL_SURFACE_ORDER):
        _reject(
            f"unexpected surface order or ids: {ids!r}",
            field="canonical_surface_ids",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )
    kinds = {surface.surface_kind for surface in registry.surfaces}
    if kinds != set(AurelSurfaceKind):
        _reject(
            "registry must contain exactly the seven v5.5 surface kinds",
            field="surfaces",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_no_old_surface_taxonomy_active(registry: AurelSurfaceRegistry) -> None:
    active_names = {surface.display_name for surface in registry.surfaces}
    active_ids = {surface.surface_id for surface in registry.surfaces}
    for old_name in OLD_SURFACE_TAXONOMY:
        normalized = old_name.lower().replace("-", "_").replace(" ", "_")
        if old_name in active_names or normalized in active_ids:
            _reject(
                f"old surface taxonomy entry active: {old_name!r}",
                field="surfaces",
                code=AurelShellErrorCode.VALIDATION_ERROR,
            )


def assert_system_is_operator_only(contract: AurelSurfaceContract) -> None:
    if contract.surface_kind != AurelSurfaceKind.SYSTEM:
        _reject("expected SYSTEM surface", field="surface_kind", code=AurelShellErrorCode.VALIDATION_ERROR)
    if contract.agent_access_boundary != AurelSurfaceAgentAccess.FORBIDDEN:
        _reject(
            "SYSTEM must forbid agent access",
            field="agent_access_boundary",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_settings_is_non_root(contract: AurelSurfaceContract) -> None:
    if contract.surface_kind != AurelSurfaceKind.SETTINGS:
        _reject("expected Settings surface", field="surface_kind", code=AurelShellErrorCode.VALIDATION_ERROR)
    if contract.configuration_boundary != "non_root_config_only":
        _reject(
            "Settings must be non-root configuration only",
            field="configuration_boundary",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_settings_is_not_system(
    system: AurelSurfaceContract,
    settings: AurelSurfaceContract,
) -> None:
    if system.surface_id == settings.surface_id:
        _reject(
            "SYSTEM and Settings must be distinct surfaces",
            field="surface_id",
            code=AurelShellErrorCode.VALIDATION_ERROR,
        )


def assert_hub_is_not_execution_authority(contract: AurelSurfaceContract) -> None:
    if contract.surface_kind != AurelSurfaceKind.HUB:
        _reject("expected HUB surface", field="surface_kind", code=AurelShellErrorCode.VALIDATION_ERROR)
    boundary = contract.authority_boundary
    if boundary.tool_execution or boundary.permission_grant:
        _reject(
            "HUB must not claim tool execution authority or permission grant",
            field="authority_boundary",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def assert_ide_is_not_runtime_authority(contract: AurelSurfaceContract) -> None:
    if contract.surface_kind != AurelSurfaceKind.IDE:
        _reject("expected IDE surface", field="surface_kind", code=AurelShellErrorCode.VALIDATION_ERROR)
    boundary = contract.authority_boundary
    if boundary.runtime_execution or boundary.bypass_validation_discipline:
        _reject(
            "IDE must not claim runtime execution authority or bypass discipline",
            field="authority_boundary",
            code=AurelShellErrorCode.EXECUTION_AUTHORITY_VIOLATION,
        )


def serialize_surface_contract(contract: AurelSurfaceContract) -> str:
    return to_canonical_json(contract.to_canonical_dict())


def serialize_surface_registry(registry: AurelSurfaceRegistry) -> str:
    return to_canonical_json(registry.to_canonical_dict())
