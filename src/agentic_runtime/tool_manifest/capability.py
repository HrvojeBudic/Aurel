"""Runtime-normalized tool capabilities and registry entries (P1.3.0).

ToolCapability is the normalized view of a valid ToolManifest.
It does not execute tools — it describes what the runtime may later govern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from . import _serde as s
from .enums import (
    CapabilityStatus,
    CapabilityType,
    DataAccessType,
    RegistryEntryStatus,
    RiskClass,
    SideEffectType,
    ToolRole,
    TrustLevel,
)
from .manifest import ValidationIssue

if TYPE_CHECKING:
    from .research_metadata import (
        SimulationProfile,
        StateDeltaContract,
        ToolLearningProfile,
        ToolSafetySurface,
    )


@dataclass
class ToolCapability:
    tool_id: str
    plugin_id: str
    canonical_name: str
    version: str
    capability_types: list[CapabilityType]
    risk_class: RiskClass
    authority_required: str | None
    input_contract: dict[str, Any]
    output_contract: dict[str, Any]
    side_effect_profile: list[SideEffectType]
    data_access_profile: list[DataAccessType]
    dry_run_capable: bool
    simulation_capable: bool
    current_status: CapabilityStatus
    trust_score_seed: TrustLevel
    registry_source: str | None
    tool_roles: list[ToolRole] = field(default_factory=list)
    state_delta_contract: StateDeltaContract | None = None
    simulation_profile: SimulationProfile | None = None
    safety_surface: ToolSafetySurface | None = None
    learning_profile: ToolLearningProfile | None = None
    prediction_required: bool | None = None
    prediction_observable: bool | None = None
    predicted_effect_quality: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "plugin_id": self.plugin_id,
            "canonical_name": self.canonical_name,
            "version": self.version,
            "capability_types": s.enum_list_values(self.capability_types),
            "risk_class": s.enum_value(self.risk_class),
            "authority_required": self.authority_required,
            "input_contract": dict(self.input_contract),
            "output_contract": dict(self.output_contract),
            "side_effect_profile": s.enum_list_values(self.side_effect_profile),
            "data_access_profile": s.enum_list_values(self.data_access_profile),
            "dry_run_capable": self.dry_run_capable,
            "simulation_capable": self.simulation_capable,
            "current_status": s.enum_value(self.current_status),
            "trust_score_seed": s.enum_value(self.trust_score_seed),
            "registry_source": self.registry_source,
            "tool_roles": s.enum_list_values(self.tool_roles),
            "state_delta_contract": (
                self.state_delta_contract.to_dict() if self.state_delta_contract else None
            ),
            "simulation_profile": (
                self.simulation_profile.to_dict() if self.simulation_profile else None
            ),
            "safety_surface": (
                self.safety_surface.to_dict() if self.safety_surface else None
            ),
            "learning_profile": (
                self.learning_profile.to_dict() if self.learning_profile else None
            ),
            "prediction_required": self.prediction_required,
            "prediction_observable": self.prediction_observable,
            "predicted_effect_quality": self.predicted_effect_quality,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCapability":
        from .research_metadata import (
            SimulationProfile,
            StateDeltaContract,
            ToolLearningProfile,
            ToolSafetySurface,
        )

        sdc = data.get("state_delta_contract")
        sim = data.get("simulation_profile")
        safety = data.get("safety_surface")
        learning = data.get("learning_profile")
        return cls(
            tool_id=str(data["tool_id"]),
            plugin_id=str(data["plugin_id"]),
            canonical_name=str(data["canonical_name"]),
            version=str(data["version"]),
            capability_types=s.enum_list_from(
                CapabilityType, data.get("capability_types") or []
            ),
            risk_class=s.enum_from(RiskClass, data["risk_class"]),
            authority_required=data.get("authority_required"),
            input_contract=dict(data.get("input_contract") or {}),
            output_contract=dict(data.get("output_contract") or {}),
            side_effect_profile=s.enum_list_from(
                SideEffectType, data.get("side_effect_profile") or []
            ),
            data_access_profile=s.enum_list_from(
                DataAccessType, data.get("data_access_profile") or []
            ),
            dry_run_capable=bool(data["dry_run_capable"]),
            simulation_capable=bool(data["simulation_capable"]),
            current_status=s.enum_from(CapabilityStatus, data["current_status"]),
            trust_score_seed=s.enum_from(TrustLevel, data["trust_score_seed"]),
            registry_source=data.get("registry_source"),
            tool_roles=s.enum_list_from(ToolRole, data.get("tool_roles") or []),
            state_delta_contract=StateDeltaContract.from_dict(sdc) if sdc else None,
            simulation_profile=SimulationProfile.from_dict(sim) if sim else None,
            safety_surface=ToolSafetySurface.from_dict(safety) if safety else None,
            learning_profile=ToolLearningProfile.from_dict(learning) if learning else None,
            prediction_required=data.get("prediction_required"),
            prediction_observable=data.get("prediction_observable"),
            predicted_effect_quality=data.get("predicted_effect_quality"),
        )


@dataclass
class ToolRegistryEntry:
    tool_id: str
    plugin_id: str
    manifest_hash: str | None
    loaded_at: datetime | None
    validated_at: datetime | None
    status: RegistryEntryStatus
    validation_errors: list[ValidationIssue]
    capability: ToolCapability | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "plugin_id": self.plugin_id,
            "manifest_hash": self.manifest_hash,
            "loaded_at": s.datetime_to_iso(self.loaded_at),
            "validated_at": s.datetime_to_iso(self.validated_at),
            "status": s.enum_value(self.status),
            "validation_errors": [issue.to_dict() for issue in self.validation_errors],
            "capability": self.capability.to_dict() if self.capability else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolRegistryEntry":
        cap = data.get("capability")
        return cls(
            tool_id=str(data["tool_id"]),
            plugin_id=str(data["plugin_id"]),
            manifest_hash=data.get("manifest_hash"),
            loaded_at=s.datetime_from_iso(data.get("loaded_at")),
            validated_at=s.datetime_from_iso(data.get("validated_at")),
            status=s.enum_from(RegistryEntryStatus, data["status"]),
            validation_errors=[
                ValidationIssue.from_dict(item)
                for item in (data.get("validation_errors") or [])
            ],
            capability=ToolCapability.from_dict(cap) if cap else None,
        )
