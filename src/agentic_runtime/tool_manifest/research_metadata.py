"""Research-inspired tool metadata (P1.3.7).

Schema, derivation, and resolution helpers only — no world model, simulation,
learning, or execution behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from . import _serde as s
from .enums import (
    CapabilityType,
    DataAccessType,
    DriftRisk,
    ExternalityLevel,
    ExecutionEnvironment,
    Reversibility,
    RiskClass,
    SideEffectType,
    StateDeltaType,
    ToolCategory,
    ToolRole,
    is_high_risk_class,
)
from .manifest import PredictedEffect, ToolManifest

if TYPE_CHECKING:
    from .capability import ToolCapability

_PERCEPTION_CATEGORIES = frozenset({
    ToolCategory.FILESYSTEM,
    ToolCategory.CODE,
    ToolCategory.GIT,
    ToolCategory.WEB,
    ToolCategory.BROWSER,
    ToolCategory.DATABASE,
})
_PERCEPTION_CAPS = frozenset({
    CapabilityType.READ,
    CapabilityType.RETRIEVE,
    CapabilityType.SEARCH,
    CapabilityType.OBSERVE,
    CapabilityType.ANALYZE,
})
_ACTION_CAPS = frozenset({
    CapabilityType.WRITE,
    CapabilityType.SEND,
    CapabilityType.SCHEDULE,
    CapabilityType.EXECUTE,
})
_ACTION_EFFECTS = frozenset({
    SideEffectType.LOCAL_WRITE,
    SideEffectType.EXTERNAL_WRITE,
    SideEffectType.PROCESS_EXECUTION,
    SideEffectType.STATE_CHANGE,
})
_DRIFT_RANK = {
    DriftRisk.NONE: 0,
    DriftRisk.LOW: 1,
    DriftRisk.MEDIUM: 2,
    DriftRisk.HIGH: 3,
    DriftRisk.UNKNOWN: 4,
}


_STATE_CHANGING_EFFECTS = frozenset({
    SideEffectType.LOCAL_WRITE,
    SideEffectType.EXTERNAL_WRITE,
    SideEffectType.STATE_CHANGE,
    SideEffectType.PROCESS_EXECUTION,
})
_READ_ONLY_EFFECTS = frozenset({
    SideEffectType.NONE,
    SideEffectType.LOCAL_READ,
    SideEffectType.EXTERNAL_READ,
})


def _max_drift(current: DriftRisk, candidate: DriftRisk) -> DriftRisk:
    if _DRIFT_RANK[candidate] > _DRIFT_RANK[current]:
        return candidate
    return current


@dataclass
class StateDeltaContract:
    delta_type: StateDeltaType
    affected_objects: list[str] = field(default_factory=list)
    expected_delta: str | None = None
    static_context: str | None = None
    dynamic_delta: str | None = None
    observable_after_action: bool = True
    verification_hint: str | None = None
    drift_risk: DriftRisk = DriftRisk.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "delta_type": s.enum_value(self.delta_type),
            "affected_objects": list(self.affected_objects),
            "expected_delta": self.expected_delta,
            "static_context": self.static_context,
            "dynamic_delta": self.dynamic_delta,
            "observable_after_action": self.observable_after_action,
            "verification_hint": self.verification_hint,
            "drift_risk": s.enum_value(self.drift_risk),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateDeltaContract:
        return cls(
            delta_type=s.enum_from(StateDeltaType, data["delta_type"]),
            affected_objects=list(data.get("affected_objects") or []),
            expected_delta=data.get("expected_delta"),
            static_context=data.get("static_context"),
            dynamic_delta=data.get("dynamic_delta"),
            observable_after_action=bool(data.get("observable_after_action", True)),
            verification_hint=data.get("verification_hint"),
            drift_risk=s.enum_from(DriftRisk, data.get("drift_risk")) or DriftRisk.UNKNOWN,
        )


@dataclass
class SimulationProfile:
    dry_run_supported: bool = False
    dry_run_strategy: str | None = None
    simulation_supported: bool = False
    simulation_strategy: str | None = None
    resettable_environment_required: bool = False
    safe_preview_mode: str | None = None
    environment_requirement: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run_supported": self.dry_run_supported,
            "dry_run_strategy": self.dry_run_strategy,
            "simulation_supported": self.simulation_supported,
            "simulation_strategy": self.simulation_strategy,
            "resettable_environment_required": self.resettable_environment_required,
            "safe_preview_mode": self.safe_preview_mode,
            "environment_requirement": self.environment_requirement,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationProfile:
        return cls(
            dry_run_supported=bool(data.get("dry_run_supported", False)),
            dry_run_strategy=data.get("dry_run_strategy"),
            simulation_supported=bool(data.get("simulation_supported", False)),
            simulation_strategy=data.get("simulation_strategy"),
            resettable_environment_required=bool(
                data.get("resettable_environment_required", False)
            ),
            safe_preview_mode=data.get("safe_preview_mode"),
            environment_requirement=data.get("environment_requirement"),
        )


@dataclass
class ToolSafetySurface:
    threat_surfaces: list[str] = field(default_factory=list)
    sensitive_data_touchpoints: list[str] = field(default_factory=list)
    externality_level: ExternalityLevel = ExternalityLevel.UNKNOWN
    reversibility_confidence: str | None = None
    operator_attention_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "threat_surfaces": list(self.threat_surfaces),
            "sensitive_data_touchpoints": list(self.sensitive_data_touchpoints),
            "externality_level": s.enum_value(self.externality_level),
            "reversibility_confidence": self.reversibility_confidence,
            "operator_attention_required": self.operator_attention_required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolSafetySurface:
        return cls(
            threat_surfaces=list(data.get("threat_surfaces") or []),
            sensitive_data_touchpoints=list(data.get("sensitive_data_touchpoints") or []),
            externality_level=s.enum_from(ExternalityLevel, data.get("externality_level"))
            or ExternalityLevel.UNKNOWN,
            reversibility_confidence=data.get("reversibility_confidence"),
            operator_attention_required=bool(data.get("operator_attention_required", False)),
        )


@dataclass
class ToolLearningProfile:
    can_generate_skill_candidate: bool = False
    can_generate_procedure_candidate: bool = False
    useful_for_evaluation: bool = False
    useful_for_training_data: bool = False
    failure_should_be_remembered: bool = False
    success_should_be_remembered: bool = False
    operator_review_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "can_generate_skill_candidate": self.can_generate_skill_candidate,
            "can_generate_procedure_candidate": self.can_generate_procedure_candidate,
            "useful_for_evaluation": self.useful_for_evaluation,
            "useful_for_training_data": self.useful_for_training_data,
            "failure_should_be_remembered": self.failure_should_be_remembered,
            "success_should_be_remembered": self.success_should_be_remembered,
            "operator_review_hint": self.operator_review_hint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolLearningProfile:
        return cls(
            can_generate_skill_candidate=bool(data.get("can_generate_skill_candidate", False)),
            can_generate_procedure_candidate=bool(
                data.get("can_generate_procedure_candidate", False)
            ),
            useful_for_evaluation=bool(data.get("useful_for_evaluation", False)),
            useful_for_training_data=bool(data.get("useful_for_training_data", False)),
            failure_should_be_remembered=bool(data.get("failure_should_be_remembered", False)),
            success_should_be_remembered=bool(data.get("success_should_be_remembered", False)),
            operator_review_hint=data.get("operator_review_hint"),
        )


def _category(tool: ToolManifest | ToolCapability) -> ToolCategory | None:
    return getattr(tool, "category", None)


def _capability_types(tool: ToolManifest | ToolCapability) -> set[CapabilityType]:
    return set(tool.capability_types)


def _side_effects(tool: ToolManifest | ToolCapability) -> set[SideEffectType]:
    if hasattr(tool, "side_effects"):
        return set(tool.side_effects)
    return set(tool.side_effect_profile)


def _data_access(tool: ToolManifest | ToolCapability) -> set[DataAccessType]:
    if hasattr(tool, "data_access"):
        return set(tool.data_access)
    return set(tool.data_access_profile)


def _predicted_effect(tool: ToolManifest | ToolCapability) -> PredictedEffect | None:
    return getattr(tool, "predicted_effect", None)


def _reversibility(tool: ToolManifest | ToolCapability) -> Reversibility | None:
    return getattr(tool, "reversibility", None)


def _execution_environment(tool: ToolManifest | ToolCapability) -> ExecutionEnvironment | None:
    return getattr(tool, "execution_environment", None)


def _explicit_roles(tool: ToolManifest | ToolCapability) -> list[ToolRole]:
    roles = getattr(tool, "tool_roles", None) or []
    return list(roles)


def _is_action_tool(tool: ToolManifest | ToolCapability) -> bool:
    caps = _capability_types(tool)
    effects = _side_effects(tool)
    return bool(caps & _ACTION_CAPS) or bool(effects & _ACTION_EFFECTS)


def _is_read_only_tool(tool: ToolManifest | ToolCapability) -> bool:
    effects = _side_effects(tool)
    return not effects or effects <= _READ_ONLY_EFFECTS


def derive_tool_roles(tool: ToolManifest | ToolCapability) -> list[ToolRole]:
    explicit = _explicit_roles(tool)
    if explicit:
        return list(dict.fromkeys(explicit))

    roles: set[ToolRole] = set()
    category = _category(tool)
    caps = _capability_types(tool)
    effects = _side_effects(tool)

    if category in _PERCEPTION_CATEGORIES or caps & _PERCEPTION_CAPS:
        roles.add(ToolRole.PERCEPTION)
    if category is ToolCategory.MODEL or caps & {
        CapabilityType.ANALYZE,
        CapabilityType.TRANSFORM,
        CapabilityType.PROPOSE,
    }:
        roles.add(ToolRole.COGNITION)
    if _is_action_tool(tool):
        roles.add(ToolRole.ACTION)
    if category in {ToolCategory.TEST, ToolCategory.EVALUATION, ToolCategory.SECURITY} or caps & {
        CapabilityType.VERIFY,
        CapabilityType.EVALUATE,
    }:
        roles.add(ToolRole.VERIFICATION)
    if category is ToolCategory.MEMORY or caps & {
        CapabilityType.RETRIEVE,
        CapabilityType.PROPOSE,
    } or DataAccessType.MEMORY in _data_access(tool):
        roles.add(ToolRole.MEMORY)
    if category is ToolCategory.ENVIRONMENT or caps & {CapabilityType.SIMULATE}:
        roles.add(ToolRole.ENVIRONMENT)
    if category is ToolCategory.SECURITY or SideEffectType.STATE_CHANGE in effects:
        roles.add(ToolRole.GOVERNANCE)

    return sorted(roles, key=lambda role: role.value)


def derive_state_delta_type(tool: ToolManifest | ToolCapability) -> StateDeltaType:
    explicit = getattr(tool, "state_delta_contract", None)
    if explicit is not None:
        return explicit.delta_type

    category = _category(tool)
    caps = _capability_types(tool)
    effects = _side_effects(tool)

    if _is_read_only_tool(tool):
        return StateDeltaType.READ_ONLY_OBSERVATION
    if category is ToolCategory.MEMORY or DataAccessType.MEMORY in _data_access(tool):
        return StateDeltaType.MEMORY_STATE_CHANGE
    if category is ToolCategory.ENVIRONMENT or CapabilityType.SIMULATE in caps:
        return StateDeltaType.ENVIRONMENT_STATE_CHANGE
    if category is ToolCategory.SECURITY:
        return StateDeltaType.GOVERNANCE_STATE_CHANGE
    if SideEffectType.EXTERNAL_WRITE in effects or caps & {
        CapabilityType.SEND,
        CapabilityType.SCHEDULE,
    }:
        return StateDeltaType.EXTERNAL_STATE_CHANGE
    if effects & _STATE_CHANGING_EFFECTS:
        return StateDeltaType.LOCAL_STATE_CHANGE
    return StateDeltaType.UNKNOWN


def derive_default_state_delta_contract(tool: ToolManifest | ToolCapability) -> StateDeltaContract:
    explicit = getattr(tool, "state_delta_contract", None)
    if explicit is not None:
        return explicit

    delta_type = derive_state_delta_type(tool)
    predicted = _predicted_effect(tool)
    affected = list(predicted.affected_objects) if predicted else []
    expected_delta = predicted.expected_delta if predicted else None

    if delta_type is StateDeltaType.READ_ONLY_OBSERVATION:
        static_context = "Read-only observation of existing state."
        dynamic_delta = None
        drift = DriftRisk.NONE
        observable = True
        verification = "Compare observed output to input contract."
    elif delta_type is StateDeltaType.LOCAL_STATE_CHANGE:
        static_context = "Local workspace state before proposed change."
        dynamic_delta = expected_delta or "Local state mutation."
        drift = DriftRisk.LOW if _reversibility(tool) is Reversibility.REVERSIBLE else DriftRisk.MEDIUM
        observable = False
        verification = "Capture diff preview before execution."
    elif delta_type is StateDeltaType.EXTERNAL_STATE_CHANGE:
        static_context = "External system state before proposed action."
        dynamic_delta = expected_delta or "External state mutation."
        drift = DriftRisk.HIGH
        observable = False
        verification = "Capture approval and payload preview."
    else:
        static_context = "Context snapshot before action."
        dynamic_delta = expected_delta
        drift = DriftRisk.UNKNOWN
        observable = delta_type is StateDeltaType.READ_ONLY_OBSERVATION
        verification = None

    if SideEffectType.PROCESS_EXECUTION in _side_effects(tool):
        drift = _max_drift(drift, DriftRisk.MEDIUM)

    if is_high_risk_class(tool.risk_class):
        drift = _max_drift(drift, DriftRisk.HIGH)

    caps = _capability_types(tool)
    if caps & {CapabilityType.VERIFY, CapabilityType.EVALUATE} or _category(tool) in {
        ToolCategory.TEST,
        ToolCategory.EVALUATION,
    }:
        observable = True

    return StateDeltaContract(
        delta_type=delta_type,
        affected_objects=affected,
        expected_delta=expected_delta,
        static_context=static_context,
        dynamic_delta=dynamic_delta,
        observable_after_action=observable,
        verification_hint=verification,
        drift_risk=drift,
    )


def derive_default_simulation_profile(tool: ToolManifest | ToolCapability) -> SimulationProfile:
    explicit = getattr(tool, "simulation_profile", None)
    if explicit is not None:
        return explicit

    effects = _side_effects(tool)
    env = _execution_environment(tool)
    dry_run_supported = getattr(tool, "dry_run_supported", None)
    if dry_run_supported is None and hasattr(tool, "dry_run_capable"):
        dry_run_supported = tool.dry_run_capable
    simulation_supported = getattr(tool, "simulation_supported", None)
    if simulation_supported is None and hasattr(tool, "simulation_capable"):
        simulation_supported = tool.simulation_capable

    if _is_read_only_tool(tool):
        return SimulationProfile(
            dry_run_supported=False,
            simulation_supported=False,
            safe_preview_mode="read_only_probe",
        )

    if env is ExecutionEnvironment.MANUAL_ONLY:
        return SimulationProfile(
            dry_run_supported=True,
            dry_run_strategy="manual_review",
            safe_preview_mode="manual_review",
        )

    if SideEffectType.EXTERNAL_WRITE in effects:
        return SimulationProfile(
            dry_run_supported=True,
            dry_run_strategy="mock_external_call",
            simulation_supported=False,
            safe_preview_mode="manual_review",
            environment_requirement="external_service_stub",
        )

    if SideEffectType.PROCESS_EXECUTION in effects or _category(tool) in {
        ToolCategory.TEST,
        ToolCategory.TERMINAL,
    }:
        strategy = "sandbox_run" if env is ExecutionEnvironment.SANDBOX else "command_preview"
        return SimulationProfile(
            dry_run_supported=bool(dry_run_supported),
            dry_run_strategy="command_preview",
            simulation_supported=True,
            simulation_strategy=strategy,
            resettable_environment_required=env is ExecutionEnvironment.SANDBOX,
            safe_preview_mode="command_preview",
            environment_requirement=s.enum_value(env) if env else None,
        )

    if effects & {SideEffectType.LOCAL_WRITE, SideEffectType.STATE_CHANGE}:
        strategy = "draft_only" if _reversibility(tool) is Reversibility.DRAFT_ONLY else "diff_preview"
        return SimulationProfile(
            dry_run_supported=True,
            dry_run_strategy=strategy,
            simulation_supported=bool(simulation_supported),
            safe_preview_mode="diff_preview",
        )

    return SimulationProfile(
        dry_run_supported=bool(dry_run_supported),
        simulation_supported=bool(simulation_supported),
    )


def derive_safety_surface(tool: ToolManifest | ToolCapability) -> ToolSafetySurface:
    explicit = getattr(tool, "safety_surface", None)
    if explicit is not None:
        return explicit

    threats: set[str] = set()
    touchpoints: list[str] = []
    effects = _side_effects(tool)
    data = _data_access(tool)
    externality = ExternalityLevel.LOCAL_ONLY
    operator_attention = is_high_risk_class(tool.risk_class)

    if SideEffectType.SECRET_ACCESS in effects or DataAccessType.SECRETS in data:
        threats.add("secrets")
        touchpoints.append("secrets")
        operator_attention = True
        externality = ExternalityLevel.LOCAL_SENSITIVE

    if SideEffectType.EXTERNAL_WRITE in effects or SideEffectType.NETWORK in effects:
        threats.update({"external_io", "action"})
        externality = ExternalityLevel.EXTERNAL_WRITE
        operator_attention = True

    if SideEffectType.EXTERNAL_READ in effects:
        externality = ExternalityLevel.EXTERNAL_READ

    if DataAccessType.MEMORY in data:
        threats.add("memory")

    if SideEffectType.PROCESS_EXECUTION in effects:
        threats.update({"action", "environment"})

    if DataAccessType.OPERATOR_PRIVATE in data or DataAccessType.LOCAL_SENSITIVE in data:
        touchpoints.append("operator_private")
        externality = ExternalityLevel.LOCAL_SENSITIVE

    if _reversibility(tool) in {Reversibility.IRREVERSIBLE, Reversibility.UNKNOWN}:
        if externality is ExternalityLevel.EXTERNAL_WRITE:
            externality = ExternalityLevel.IRREVERSIBLE_EXTERNAL
        operator_attention = True

    if tool.risk_class in {RiskClass.R0, RiskClass.R1} and _is_read_only_tool(tool):
        operator_attention = bool(touchpoints)

    rev_confidence = s.enum_value(_reversibility(tool)) if _reversibility(tool) else None

    return ToolSafetySurface(
        threat_surfaces=sorted(threats),
        sensitive_data_touchpoints=touchpoints,
        externality_level=externality,
        reversibility_confidence=rev_confidence,
        operator_attention_required=operator_attention,
    )


def derive_learning_profile(tool: ToolManifest | ToolCapability) -> ToolLearningProfile:
    explicit = getattr(tool, "learning_profile", None)
    if explicit is not None:
        return explicit

    category = _category(tool)
    caps = _capability_types(tool)
    high_risk = is_high_risk_class(tool.risk_class)
    verification = category in {ToolCategory.TEST, ToolCategory.EVALUATION} or caps & {
        CapabilityType.VERIFY,
        CapabilityType.EVALUATE,
    }
    action = _is_action_tool(tool)

    return ToolLearningProfile(
        can_generate_procedure_candidate=action and not _is_read_only_tool(tool),
        useful_for_evaluation=verification,
        useful_for_training_data=verification or (action and not high_risk),
        failure_should_be_remembered=high_risk,
        success_should_be_remembered=high_risk,
        operator_review_hint=(
            "High-risk action requires operator review before reuse."
            if high_risk
            else None
        ),
    )


def resolve_research_metadata(tool: ToolManifest) -> dict[str, Any]:
    """Resolve explicit or derived research metadata for a manifest."""
    return {
        "tool_roles": [role.value for role in derive_tool_roles(tool)],
        "state_delta_contract": derive_default_state_delta_contract(tool).to_dict(),
        "simulation_profile": derive_default_simulation_profile(tool).to_dict(),
        "safety_surface": derive_safety_surface(tool).to_dict(),
        "learning_profile": derive_learning_profile(tool).to_dict(),
        "prediction_required": tool.prediction_required,
        "prediction_observable": tool.prediction_observable,
        "predicted_effect_quality": tool.predicted_effect_quality,
        "predicted_effect": (
            tool.predicted_effect.to_dict() if tool.predicted_effect else None
        ),
    }


def research_metadata_from_capability(capability: ToolCapability) -> dict[str, Any]:
    """Serialize research metadata carried on a ToolCapability."""
    return {
        "tool_roles": [role.value for role in capability.tool_roles],
        "state_delta_contract": (
            capability.state_delta_contract.to_dict()
            if capability.state_delta_contract
            else None
        ),
        "simulation_profile": (
            capability.simulation_profile.to_dict()
            if capability.simulation_profile
            else None
        ),
        "safety_surface": (
            capability.safety_surface.to_dict() if capability.safety_surface else None
        ),
        "learning_profile": (
            capability.learning_profile.to_dict() if capability.learning_profile else None
        ),
        "prediction_required": capability.prediction_required,
        "prediction_observable": capability.prediction_observable,
        "predicted_effect_quality": capability.predicted_effect_quality,
    }


def apply_research_metadata_to_capability(
    capability: ToolCapability,
    tool: ToolManifest,
) -> ToolCapability:
    """Populate capability research fields from manifest (explicit or derived)."""
    from .capability import ToolCapability as Capability

    roles = derive_tool_roles(tool)
    contract = derive_default_state_delta_contract(tool)
    simulation = derive_default_simulation_profile(tool)
    safety = derive_safety_surface(tool)
    learning = derive_learning_profile(tool)

    prediction_required = tool.prediction_required
    if prediction_required is None:
        prediction_required = contract.delta_type not in {
            StateDeltaType.NONE,
            StateDeltaType.READ_ONLY_OBSERVATION,
        }

    prediction_observable = tool.prediction_observable
    if prediction_observable is None:
        prediction_observable = contract.observable_after_action

    return Capability(
        tool_id=capability.tool_id,
        plugin_id=capability.plugin_id,
        canonical_name=capability.canonical_name,
        version=capability.version,
        capability_types=capability.capability_types,
        risk_class=capability.risk_class,
        authority_required=capability.authority_required,
        input_contract=capability.input_contract,
        output_contract=capability.output_contract,
        side_effect_profile=capability.side_effect_profile,
        data_access_profile=capability.data_access_profile,
        dry_run_capable=capability.dry_run_capable,
        simulation_capable=capability.simulation_capable,
        current_status=capability.current_status,
        trust_score_seed=capability.trust_score_seed,
        registry_source=capability.registry_source,
        tool_roles=roles,
        state_delta_contract=contract,
        simulation_profile=simulation,
        safety_surface=safety,
        learning_profile=learning,
        prediction_required=prediction_required,
        prediction_observable=prediction_observable,
        predicted_effect_quality=tool.predicted_effect_quality,
    )


def is_state_changing_capability(capability: ToolCapability) -> bool:
    contract = capability.state_delta_contract
    if contract is None:
        return False
    return contract.delta_type not in {
        StateDeltaType.NONE,
        StateDeltaType.READ_ONLY_OBSERVATION,
    }


def is_simulation_ready_capability(capability: ToolCapability) -> bool:
    profile = capability.simulation_profile
    if profile is None:
        return capability.dry_run_capable or capability.simulation_capable
    return profile.dry_run_supported or profile.simulation_supported
