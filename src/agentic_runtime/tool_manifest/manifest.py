"""Plugin and tool manifest declarations (P1.3.0).

ToolManifest is a *declaration* — metadata about what a tool claims to be.
It does not grant authority, register execution rights, or invoke anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from . import _serde as s
from .enums import (
    CapabilityType,
    ConfidenceSeed,
    DataAccessType,
    DataResidency,
    ExecutionEnvironment,
    FilesystemPolicy,
    NetworkPolicy,
    PluginOrigin,
    PluginStatus,
    Reversibility,
    RiskClass,
    SecretPolicy,
    SideEffectType,
    ToolCategory,
    ToolRole,
    TraceLevel,
    TrustLevel,
    ValidationSeverity,
    is_high_risk_class,
)

if TYPE_CHECKING:
    from .research_metadata import (
        SimulationProfile,
        StateDeltaContract,
        ToolLearningProfile,
        ToolSafetySurface,
    )


@dataclass
class PredictedEffect:
    state_target: str | None
    expected_delta: str | None
    affected_objects: list[str]
    reversible: bool
    confidence_seed: ConfidenceSeed

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_target": self.state_target,
            "expected_delta": self.expected_delta,
            "affected_objects": list(self.affected_objects),
            "reversible": self.reversible,
            "confidence_seed": s.enum_value(self.confidence_seed),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PredictedEffect":
        return cls(
            state_target=data.get("state_target"),
            expected_delta=data.get("expected_delta"),
            affected_objects=list(data.get("affected_objects") or []),
            reversible=bool(data["reversible"]),
            confidence_seed=s.enum_from(ConfidenceSeed, data["confidence_seed"]),
        )


@dataclass
class ValidationIssue:
    code: str
    message: str
    field: str | None
    severity: ValidationSeverity

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "severity": s.enum_value(self.severity),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationIssue":
        return cls(
            code=str(data["code"]),
            message=str(data["message"]),
            field=data.get("field"),
            severity=s.enum_from(ValidationSeverity, data["severity"]),
        )


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str
    owner: str | None
    origin: PluginOrigin
    trust_level: TrustLevel
    status: PluginStatus
    created_at: datetime | None
    updated_at: datetime | None
    tools: list[str]
    required_permissions: list[str]
    data_residency: DataResidency | None
    network_policy: NetworkPolicy | None
    filesystem_policy: FilesystemPolicy | None
    secret_policy: SecretPolicy | None
    runtime_surfaces: list[str]
    compatibility: dict[str, Any]
    integrity_hash: str | None

    def is_external(self) -> bool:
        """True when the plugin did not ship with the runtime (non-builtin origin)."""
        return self.origin != PluginOrigin.BUILTIN

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "owner": self.owner,
            "origin": s.enum_value(self.origin),
            "trust_level": s.enum_value(self.trust_level),
            "status": s.enum_value(self.status),
            "created_at": s.datetime_to_iso(self.created_at),
            "updated_at": s.datetime_to_iso(self.updated_at),
            "tools": list(self.tools),
            "required_permissions": list(self.required_permissions),
            "data_residency": s.enum_value(self.data_residency),
            "network_policy": s.enum_value(self.network_policy),
            "filesystem_policy": s.enum_value(self.filesystem_policy),
            "secret_policy": s.enum_value(self.secret_policy),
            "runtime_surfaces": list(self.runtime_surfaces),
            "compatibility": dict(self.compatibility),
            "integrity_hash": self.integrity_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        return cls(
            plugin_id=str(data["plugin_id"]),
            name=str(data["name"]),
            version=str(data["version"]),
            description=str(data["description"]),
            owner=data.get("owner"),
            origin=s.enum_from(PluginOrigin, data["origin"]),
            trust_level=s.enum_from(TrustLevel, data["trust_level"]),
            status=s.enum_from(PluginStatus, data["status"]),
            created_at=s.datetime_from_iso(data.get("created_at")),
            updated_at=s.datetime_from_iso(data.get("updated_at")),
            tools=list(data.get("tools") or []),
            required_permissions=list(data.get("required_permissions") or []),
            data_residency=s.enum_from(DataResidency, data.get("data_residency")),
            network_policy=s.enum_from(NetworkPolicy, data.get("network_policy")),
            filesystem_policy=s.enum_from(FilesystemPolicy, data.get("filesystem_policy")),
            secret_policy=s.enum_from(SecretPolicy, data.get("secret_policy")),
            runtime_surfaces=list(data.get("runtime_surfaces") or []),
            compatibility=dict(data.get("compatibility") or {}),
            integrity_hash=data.get("integrity_hash"),
        )


@dataclass
class ToolManifest:
    tool_id: str
    plugin_id: str
    name: str
    description: str
    category: ToolCategory
    capability_types: list[CapabilityType]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    side_effects: list[SideEffectType]
    risk_class: RiskClass
    reversibility: Reversibility
    requires_approval: bool
    permissions_required: list[str]
    data_access: list[DataAccessType]
    execution_environment: ExecutionEnvironment
    dry_run_supported: bool
    simulation_supported: bool
    predicted_effect: PredictedEffect | None
    failure_modes: list[str]
    evidence_required: bool
    trace_level: TraceLevel
    timeout_policy: dict[str, Any] | None
    rate_limit_policy: dict[str, Any] | None
    enabled: bool
    tool_roles: list[ToolRole] = field(default_factory=list)
    state_delta_contract: StateDeltaContract | None = None
    simulation_profile: SimulationProfile | None = None
    safety_surface: ToolSafetySurface | None = None
    learning_profile: ToolLearningProfile | None = None
    prediction_required: bool | None = None
    prediction_observable: bool | None = None
    predicted_effect_quality: str | None = None

    def is_high_risk(self) -> bool:
        return is_high_risk_class(self.risk_class)

    def requires_human_approval(self) -> bool:
        return self.requires_approval or self.is_high_risk()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "category": s.enum_value(self.category),
            "capability_types": s.enum_list_values(self.capability_types),
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "side_effects": s.enum_list_values(self.side_effects),
            "risk_class": s.enum_value(self.risk_class),
            "reversibility": s.enum_value(self.reversibility),
            "requires_approval": self.requires_approval,
            "permissions_required": list(self.permissions_required),
            "data_access": s.enum_list_values(self.data_access),
            "execution_environment": s.enum_value(self.execution_environment),
            "dry_run_supported": self.dry_run_supported,
            "simulation_supported": self.simulation_supported,
            "predicted_effect": (
                self.predicted_effect.to_dict() if self.predicted_effect else None
            ),
            "failure_modes": list(self.failure_modes),
            "evidence_required": self.evidence_required,
            "trace_level": s.enum_value(self.trace_level),
            "timeout_policy": dict(self.timeout_policy) if self.timeout_policy else None,
            "rate_limit_policy": (
                dict(self.rate_limit_policy) if self.rate_limit_policy else None
            ),
            "enabled": self.enabled,
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
    def from_dict(cls, data: dict[str, Any]) -> "ToolManifest":
        from .research_metadata import (
            SimulationProfile,
            StateDeltaContract,
            ToolLearningProfile,
            ToolSafetySurface,
        )

        pe = data.get("predicted_effect")
        sdc = data.get("state_delta_contract")
        sim = data.get("simulation_profile")
        safety = data.get("safety_surface")
        learning = data.get("learning_profile")
        return cls(
            tool_id=str(data["tool_id"]),
            plugin_id=str(data["plugin_id"]),
            name=str(data["name"]),
            description=str(data["description"]),
            category=s.enum_from(ToolCategory, data["category"]),
            capability_types=s.enum_list_from(CapabilityType, data.get("capability_types") or []),
            input_schema=dict(data.get("input_schema") or {}),
            output_schema=dict(data.get("output_schema") or {}),
            side_effects=s.enum_list_from(SideEffectType, data.get("side_effects") or []),
            risk_class=s.enum_from(RiskClass, data["risk_class"]),
            reversibility=s.enum_from(Reversibility, data["reversibility"]),
            requires_approval=bool(data["requires_approval"]),
            permissions_required=list(data.get("permissions_required") or []),
            data_access=s.enum_list_from(DataAccessType, data.get("data_access") or []),
            execution_environment=s.enum_from(ExecutionEnvironment, data["execution_environment"]),
            dry_run_supported=bool(data["dry_run_supported"]),
            simulation_supported=bool(data["simulation_supported"]),
            predicted_effect=PredictedEffect.from_dict(pe) if pe else None,
            failure_modes=list(data.get("failure_modes") or []),
            evidence_required=bool(data["evidence_required"]),
            trace_level=s.enum_from(TraceLevel, data["trace_level"]),
            timeout_policy=dict(data["timeout_policy"]) if data.get("timeout_policy") else None,
            rate_limit_policy=(
                dict(data["rate_limit_policy"]) if data.get("rate_limit_policy") else None
            ),
            enabled=bool(data["enabled"]),
            tool_roles=s.enum_list_from(ToolRole, data.get("tool_roles") or []),
            state_delta_contract=StateDeltaContract.from_dict(sdc) if sdc else None,
            simulation_profile=SimulationProfile.from_dict(sim) if sim else None,
            safety_surface=ToolSafetySurface.from_dict(safety) if safety else None,
            learning_profile=ToolLearningProfile.from_dict(learning) if learning else None,
            prediction_required=data.get("prediction_required"),
            prediction_observable=data.get("prediction_observable"),
            predicted_effect_quality=data.get("predicted_effect_quality"),
        )
