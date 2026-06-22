"""Tool invocation drafts — proposals only, never execution (P1.3.0 / P1.3.5).

ToolInvocationDraft records intent to use a tool. Draft creation does not grant
authority, run tools, or mutate external state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from ..core_types import new_id
from . import _serde as s
from .enums import (
    CapabilityStatus,
    CapabilityType,
    DataAccessType,
    RegistryEntryStatus,
    Reversibility,
    RiskClass,
    SideEffectType,
    ValidationSeverity,
    is_high_risk_class,
)
from .capability import ToolCapability
from .manifest import PredictedEffect, ValidationIssue

if TYPE_CHECKING:
    from .registry import ToolRegistry

# --------------------------------------------------------------------------- #
#  Input validation codes
# --------------------------------------------------------------------------- #
TOOL_INPUT_NOT_OBJECT = "TOOL_INPUT_NOT_OBJECT"
TOOL_INPUT_SCHEMA_INVALID = "TOOL_INPUT_SCHEMA_INVALID"
TOOL_INPUT_REQUIRED_FIELD_MISSING = "TOOL_INPUT_REQUIRED_FIELD_MISSING"
TOOL_INPUT_UNEXPECTED_FIELD = "TOOL_INPUT_UNEXPECTED_FIELD"
TOOL_INPUT_TYPE_MISMATCH = "TOOL_INPUT_TYPE_MISMATCH"

_TYPE_CHECKERS: dict[str, Any] = {
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
}


class ToolInvocationDraftStatus(str, Enum):
    DRAFT = "draft"
    INVALID = "invalid"
    BLOCKED = "blocked"
    REQUIRES_APPROVAL = "requires_approval"
    READY_FOR_POLICY = "ready_for_policy"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ToolInvocationDraftResultStatus(str, Enum):
    CREATED = "created"
    INVALID_INPUT = "invalid_input"
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_NOT_ACTIVE = "tool_not_active"
    TOOL_QUARANTINED = "tool_quarantined"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"
    REJECTED = "rejected"


@dataclass
class ToolInvocationDraft:
    draft_id: str
    tool_id: str
    requested_by: str
    purpose: str
    input_payload: dict[str, Any]
    expected_output: str | None
    predicted_effect: PredictedEffect | None
    risk_class: RiskClass
    reversibility: Reversibility
    approval_required: bool
    evidence_plan: str | None
    created_at: datetime

    def requires_human_approval(self) -> bool:
        return self.approval_required or is_high_risk_class(self.risk_class)

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "tool_id": self.tool_id,
            "requested_by": self.requested_by,
            "purpose": self.purpose,
            "input_payload": dict(self.input_payload),
            "expected_output": self.expected_output,
            "predicted_effect": (
                self.predicted_effect.to_dict() if self.predicted_effect else None
            ),
            "risk_class": s.enum_value(self.risk_class),
            "reversibility": s.enum_value(self.reversibility),
            "approval_required": self.approval_required,
            "evidence_plan": self.evidence_plan,
            "created_at": s.datetime_to_iso(self.created_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolInvocationDraft":
        pe = data.get("predicted_effect")
        created = data.get("created_at")
        if created is None:
            raise KeyError("created_at")
        return cls(
            draft_id=str(data["draft_id"]),
            tool_id=str(data["tool_id"]),
            requested_by=str(data["requested_by"]),
            purpose=str(data["purpose"]),
            input_payload=dict(data.get("input_payload") or {}),
            expected_output=data.get("expected_output"),
            predicted_effect=PredictedEffect.from_dict(pe) if pe else None,
            risk_class=s.enum_from(RiskClass, data["risk_class"]),
            reversibility=s.enum_from(Reversibility, data["reversibility"]),
            approval_required=bool(data["approval_required"]),
            evidence_plan=data.get("evidence_plan"),
            created_at=s.datetime_from_iso(created),
        )


@dataclass
class ToolInvocationContext:
    requested_by: str
    purpose: str
    request_source: str | None = None
    runtime_mode: str | None = None
    operator_visible: bool = True
    correlation_id: str | None = None
    parent_command_id: str | None = None
    parent_trace_id: str | None = None


@dataclass
class ToolInputValidationResult:
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    unexpected_fields: list[str] = field(default_factory=list)
    schema_used: dict[str, Any] | None = None


@dataclass
class ToolInvocationDraftResult:
    status: ToolInvocationDraftResultStatus
    draft: ToolInvocationDraft | None = None
    draft_status: ToolInvocationDraftStatus | None = None
    tool_id: str | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    message: str | None = None
    approval_required: bool = False
    blocked_reason: str | None = None
    research_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "draft": self.draft.to_dict() if self.draft else None,
            "draft_status": self.draft_status.value if self.draft_status else None,
            "tool_id": self.tool_id,
            "issues": [issue.to_dict() for issue in self.issues],
            "message": self.message,
            "approval_required": self.approval_required,
            "blocked_reason": self.blocked_reason,
            "research_metadata": dict(self.research_metadata),
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _issue(code: str, message: str, field: str | None, severity: ValidationSeverity) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, field=field, severity=severity)


def validate_tool_input_payload(
    payload: dict[str, Any],
    input_schema: dict[str, Any],
) -> ToolInputValidationResult:
    if not isinstance(input_schema, dict):
        return ToolInputValidationResult(
            is_valid=False,
            issues=[_issue(
                TOOL_INPUT_SCHEMA_INVALID,
                "input schema must be a dict",
                "input_schema",
                ValidationSeverity.ERROR,
            )],
            schema_used=None,
        )

    if not isinstance(payload, dict):
        return ToolInputValidationResult(
            is_valid=False,
            issues=[_issue(
                TOOL_INPUT_NOT_OBJECT,
                "input payload must be an object",
                "input_payload",
                ValidationSeverity.ERROR,
            )],
            schema_used=dict(input_schema),
        )

    issues: list[ValidationIssue] = []
    missing_fields: list[str] = []
    unexpected_fields: list[str] = []

    required = input_schema.get("required") or []
    if not isinstance(required, list):
        issues.append(_issue(
            TOOL_INPUT_SCHEMA_INVALID,
            "input schema required must be a list",
            "required",
            ValidationSeverity.ERROR,
        ))
        required = []

    properties = input_schema.get("properties") or {}
    if properties and not isinstance(properties, dict):
        issues.append(_issue(
            TOOL_INPUT_SCHEMA_INVALID,
            "input schema properties must be an object",
            "properties",
            ValidationSeverity.ERROR,
        ))
        properties = {}

    allowed = set(properties.keys())
    for field_name in required:
        if field_name not in payload:
            missing_fields.append(field_name)
            issues.append(_issue(
                TOOL_INPUT_REQUIRED_FIELD_MISSING,
                f"missing required field '{field_name}'",
                field_name,
                ValidationSeverity.ERROR,
            ))

    if allowed:
        for key in payload:
            if key not in allowed and key not in required:
                unexpected_fields.append(key)
                issues.append(_issue(
                    TOOL_INPUT_UNEXPECTED_FIELD,
                    f"unexpected field '{key}'",
                    key,
                    ValidationSeverity.ERROR,
                ))

    for key, value in payload.items():
        if key not in properties:
            continue
        prop = properties[key]
        if not isinstance(prop, dict):
            continue
        expected_type = prop.get("type")
        if not expected_type:
            continue
        checker = _TYPE_CHECKERS.get(str(expected_type))
        if checker is not None and not checker(value):
            issues.append(_issue(
                TOOL_INPUT_TYPE_MISMATCH,
                f"field '{key}' must be {expected_type}",
                key,
                ValidationSeverity.ERROR,
            ))

    blocking = any(
        issue.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        for issue in issues
    )
    return ToolInputValidationResult(
        is_valid=not blocking,
        issues=issues,
        missing_fields=missing_fields,
        unexpected_fields=unexpected_fields,
        schema_used=dict(input_schema),
    )


def _risk_at_least(risk: RiskClass, minimum: RiskClass) -> bool:
    order = {RiskClass.R0: 0, RiskClass.R1: 1, RiskClass.R2: 2, RiskClass.R3: 3,
             RiskClass.R4: 4, RiskClass.R5: 5, RiskClass.R6: 6}
    return order[risk] >= order[minimum]


def derive_approval_requirement(
    capability: ToolCapability,
    *,
    reversibility: Reversibility | None = None,
) -> bool:
    if is_high_risk_class(capability.risk_class):
        return True

    effects = set(capability.side_effect_profile)
    data = set(capability.data_access_profile)

    if SideEffectType.EXTERNAL_WRITE in effects:
        return True
    if SideEffectType.SECRET_ACCESS in effects:
        return True
    if SideEffectType.PROCESS_EXECUTION in effects and _risk_at_least(capability.risk_class, RiskClass.R3):
        return True
    if SideEffectType.STATE_CHANGE in effects and _risk_at_least(capability.risk_class, RiskClass.R4):
        return True
    if DataAccessType.SECRETS in data:
        return True
    if DataAccessType.OPERATOR_PRIVATE in data and _risk_at_least(capability.risk_class, RiskClass.R3):
        return True
    if capability.authority_required == "approval_required":
        return True
    if reversibility in {Reversibility.IRREVERSIBLE, Reversibility.UNKNOWN}:
        if _risk_at_least(capability.risk_class, RiskClass.R3):
            return True

    return False


def derive_evidence_plan(
    capability: ToolCapability,
    input_payload: dict[str, Any],
) -> str | None:
    effects = set(capability.side_effect_profile)
    caps = set(capability.capability_types)

    if SideEffectType.SECRET_ACCESS in effects or DataAccessType.SECRETS in capability.data_access_profile:
        return "Capture policy decision and trace reference without storing secret values."
    if SideEffectType.EXTERNAL_WRITE in effects:
        return "Capture approval, payload preview, response metadata, and trace reference."
    if SideEffectType.PROCESS_EXECUTION in effects:
        return "Capture command envelope, sandbox/process metadata, exit code, and output summary."
    if caps & {CapabilityType.VERIFY, CapabilityType.EVALUATE} or SideEffectType.NONE in effects:
        if capability.risk_class in {RiskClass.R0, RiskClass.R1} and SideEffectType.LOCAL_READ in effects:
            return "Capture input, output summary, and trace reference."
        return "Capture command, exit code, test summary, and relevant logs."
    if SideEffectType.LOCAL_WRITE in effects or SideEffectType.STATE_CHANGE in effects:
        return "Capture proposed diff or draft preview before execution."
    if is_high_risk_class(capability.risk_class):
        return "Capture approval, input preview, expected effect, and trace reference."
    if SideEffectType.LOCAL_READ in effects or CapabilityType.READ in caps:
        return "Capture input, output summary, and trace reference."
    return "Capture input, output summary, and trace reference."


def derive_draft_status(
    capability: ToolCapability,
    input_validation: ToolInputValidationResult,
    approval_required: bool,
) -> ToolInvocationDraftStatus:
    if not input_validation.is_valid:
        return ToolInvocationDraftStatus.INVALID
    if approval_required:
        return ToolInvocationDraftStatus.REQUIRES_APPROVAL
    return ToolInvocationDraftStatus.READY_FOR_POLICY


def is_tool_entry_active_for_invocation(
    registry: ToolRegistry,
    tool_id: str,
) -> tuple[bool, str | None, list[ValidationIssue]]:
    entry = registry.get_tool(tool_id)
    if entry is None:
        return False, f"tool '{tool_id}' not found", []

    issues = list(entry.validation_errors)
    if registry.quarantine_store.has_quarantined_subject(tool_id):
        for record in registry.quarantine_store.list_by_tool(tool_id):
            issues.extend(record.validation_issues)

    if not registry.is_active(tool_id):
        if entry.status is RegistryEntryStatus.QUARANTINED or (
            entry.capability is not None
            and entry.capability.current_status is CapabilityStatus.QUARANTINED
        ):
            return False, f"tool '{tool_id}' is quarantined", issues
        if registry.quarantine_store.has_quarantined_subject(tool_id) and entry.status not in {
            RegistryEntryStatus.DEPRECATED,
        } and (
            entry.capability is None
            or entry.capability.current_status is not CapabilityStatus.DEPRECATED
        ):
            return False, f"tool '{tool_id}' is quarantined", issues
        if entry.capability is not None and entry.capability.risk_class is RiskClass.R6:
            return False, f"tool '{tool_id}' is blocked (R6)", issues
        return False, f"tool '{tool_id}' is not active", issues

    return True, None, issues


def is_tool_invocation_draft_policy_ready(draft: ToolInvocationDraft | None) -> bool:
    """Return True when a draft is structurally ready for a future policy gate.

    Policy-ready does **not** mean executable — it only means required draft
    fields are present and the draft was not blocked at creation time.
    """
    if draft is None:
        return False
    if not draft.tool_id.strip():
        return False
    if not draft.requested_by.strip():
        return False
    if not draft.purpose.strip():
        return False
    return True


def create_tool_invocation_draft(
    registry: ToolRegistry,
    tool_id: str,
    input_payload: dict[str, Any],
    context: ToolInvocationContext,
    predicted_effect_override: PredictedEffect | None = None,
) -> ToolInvocationDraftResult:
    entry = registry.get_tool(tool_id)
    if entry is None:
        return ToolInvocationDraftResult(
            status=ToolInvocationDraftResultStatus.TOOL_NOT_FOUND,
            tool_id=tool_id,
            message=f"tool '{tool_id}' not found in registry",
        )

    active, blocked_reason, entry_issues = is_tool_entry_active_for_invocation(registry, tool_id)
    if not active:
        status = ToolInvocationDraftResultStatus.TOOL_NOT_ACTIVE
        if entry.status is RegistryEntryStatus.QUARANTINED or (
            entry.capability is not None
            and entry.capability.current_status is CapabilityStatus.QUARANTINED
        ):
            status = ToolInvocationDraftResultStatus.TOOL_QUARANTINED
        elif registry.quarantine_store.has_quarantined_subject(tool_id) and entry.status not in {
            RegistryEntryStatus.DEPRECATED,
        } and (
            entry.capability is None
            or entry.capability.current_status is not CapabilityStatus.DEPRECATED
        ):
            status = ToolInvocationDraftResultStatus.TOOL_QUARANTINED
        elif blocked_reason and "R6" in blocked_reason:
            status = ToolInvocationDraftResultStatus.BLOCKED
        return ToolInvocationDraftResult(
            status=status,
            tool_id=tool_id,
            issues=entry_issues,
            message=blocked_reason,
            blocked_reason=blocked_reason,
        )

    capability = entry.capability
    if capability is None:
        return ToolInvocationDraftResult(
            status=ToolInvocationDraftResultStatus.BLOCKED,
            tool_id=tool_id,
            issues=entry_issues,
            message="tool capability metadata is missing",
            blocked_reason="missing capability",
        )

    input_validation = validate_tool_input_payload(input_payload, capability.input_contract)
    if not input_validation.is_valid:
        return ToolInvocationDraftResult(
            status=ToolInvocationDraftResultStatus.INVALID_INPUT,
            tool_id=tool_id,
            issues=list(input_validation.issues) + entry_issues,
            message="input payload failed validation",
            blocked_reason="invalid input",
        )

    meta = registry.get_invocation_meta(tool_id)
    reversibility = meta.reversibility if meta is not None else Reversibility.UNKNOWN

    approval_required = (
        derive_approval_requirement(capability, reversibility=reversibility)
        or registry.requires_approval(tool_id)
    )
    draft_status = derive_draft_status(capability, input_validation, approval_required)
    evidence_plan = derive_evidence_plan(capability, input_payload)

    predicted_effect = predicted_effect_override
    if predicted_effect is None and meta is not None:
        predicted_effect = meta.predicted_effect

    draft = ToolInvocationDraft(
        draft_id=new_id("draft"),
        tool_id=tool_id,
        requested_by=context.requested_by,
        purpose=context.purpose,
        input_payload=dict(input_payload),
        expected_output=None,
        predicted_effect=predicted_effect,
        risk_class=capability.risk_class,
        reversibility=reversibility,
        approval_required=approval_required,
        evidence_plan=evidence_plan,
        created_at=_utc_now(),
    )

    result_status = ToolInvocationDraftResultStatus.CREATED
    if approval_required:
        result_status = ToolInvocationDraftResultStatus.REQUIRES_APPROVAL

    from .research_metadata import research_metadata_from_capability

    return ToolInvocationDraftResult(
        status=result_status,
        draft=draft,
        draft_status=draft_status,
        tool_id=tool_id,
        issues=entry_issues,
        message="invocation draft created (proposal only)",
        approval_required=approval_required,
        research_metadata=research_metadata_from_capability(capability),
    )
