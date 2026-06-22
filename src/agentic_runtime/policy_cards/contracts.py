"""Behavioral Contract models (P1.6.2).

First-class, typed, frozen, validated, deterministic, hash-ready behavioral
contract objects. Behavioral contracts define how a subject must behave while
operating inside the governed system — obligations, prohibitions,
preconditions, postconditions, evidence requirements, and escalation rules.

Architectural law:
  - Behavioral contracts do not grant authority.
  - Behavioral contracts do not bypass policy cards.
  - Behavioral contracts do not execute anything.
  - Behavioral contracts do not enforce runtime behavior yet.
  - PolicyCard = what rule exists.
  - BehavioralContract = how a subject must behave.
  - Runtime enforcement = later.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .errors import (
    BehavioralContractValidationError,
    BehavioralContractUnknownFieldError,
    BehavioralContractUnsafeFieldError,
)


# ---------------------------------------------------------------------------
# 24 enums
# ---------------------------------------------------------------------------


class BehavioralContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    TEST_ONLY = "test_only"


class BehavioralContractSubjectType(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"
    PROMPT = "prompt"
    MEMORY_WRITER = "memory_writer"
    WORKFLOW_NODE = "workflow_node"
    SANDBOX_EXECUTOR = "sandbox_executor"
    SPECIALIST = "specialist"
    BUSINESS_PROCESS = "business_process"
    RUNTIME = "runtime"
    GLOBAL = "global"


class BehavioralContractScopeType(str, Enum):
    GLOBAL = "global"
    RUNTIME = "runtime"
    TOOL = "tool"
    MODEL = "model"
    MEMORY = "memory"
    PROMPT = "prompt"
    SANDBOX = "sandbox"
    WORKFLOW = "workflow"
    AGENT = "agent"
    BUSINESS = "business"
    HUB = "hub"
    PROJECT = "project"
    REPOSITORY = "repository"


class BehavioralContractObligationType(str, Enum):
    MUST_FOLLOW_POLICY_CARDS = "must_follow_policy_cards"
    MUST_EMIT_TRACE = "must_emit_trace"
    MUST_PRODUCE_EVIDENCE = "must_produce_evidence"
    MUST_VALIDATE_INPUT = "must_validate_input"
    MUST_PRESERVE_SOURCE_PROVENANCE = "must_preserve_source_provenance"
    MUST_REQUEST_OPERATOR_APPROVAL = "must_request_operator_approval"
    MUST_RUN_TESTS_BEFORE_WRITE = "must_run_tests_before_write"
    MUST_USE_SAFE_SANDBOX = "must_use_safe_sandbox"
    MUST_DISCLOSE_UNCERTAINTY = "must_disclose_uncertainty"
    MUST_REPORT_FAILURE = "must_report_failure"
    MUST_ATTACH_OUTPUT_PASSPORT = "must_attach_output_passport"
    MUST_RESPECT_DATA_RESIDENCY = "must_respect_data_residency"
    MUST_CHECK_AUTHORITY = "must_check_authority"


class BehavioralContractProhibitionType(str, Enum):
    MUST_NOT_WRITE_WITHOUT_AUTHORITY = "must_not_write_without_authority"
    MUST_NOT_SKIP_TRACE = "must_not_skip_trace"
    MUST_NOT_HIDE_TOOL_FAILURE = "must_not_hide_tool_failure"
    MUST_NOT_STORE_UNVERIFIED_MEMORY = "must_not_store_unverified_memory"
    MUST_NOT_EXECUTE_UNTRUSTED_CONTENT = "must_not_execute_untrusted_content"
    MUST_NOT_CALL_EXTERNAL_MODEL_IN_LOCAL_ONLY_MODE = "must_not_call_external_model_in_local_only_mode"
    MUST_NOT_MODIFY_PROTECTED_TESTS = "must_not_modify_protected_tests"
    MUST_NOT_CLAIM_UNVERIFIED_CAPABILITY = "must_not_claim_unverified_capability"
    MUST_NOT_BYPASS_POLICY = "must_not_bypass_policy"
    MUST_NOT_IGNORE_DATA_RESIDENCY = "must_not_ignore_data_residency"
    MUST_NOT_ESCALATE_PRIVILEGES = "must_not_escalate_privileges"
    MUST_NOT_SILENTLY_DROP_EVIDENCE = "must_not_silently_drop_evidence"


class BehavioralContractPreconditionType(str, Enum):
    POLICY_RESOLVED = "policy_resolved"
    AUTHORITY_CONFIRMED = "authority_confirmed"
    INPUT_VALIDATED = "input_validated"
    PATH_ALLOWED = "path_allowed"
    SANDBOX_SELECTED = "sandbox_selected"
    OPERATOR_APPROVAL_PRESENT = "operator_approval_present"
    RISK_TIER_KNOWN = "risk_tier_known"
    DATA_RESIDENCY_CHECKED = "data_residency_checked"
    TOOL_CONTRACT_VALIDATED = "tool_contract_validated"
    MODEL_ROUTE_APPROVED = "model_route_approved"
    MEMORY_SCOPE_CHECKED = "memory_scope_checked"


class BehavioralContractPostconditionType(str, Enum):
    TRACE_WRITTEN = "trace_written"
    EVIDENCE_ATTACHED = "evidence_attached"
    OUTPUT_PASSPORT_READY = "output_passport_ready"
    STATE_DIFF_RECORDED = "state_diff_recorded"
    ERRORS_REPORTED = "errors_reported"
    MEMORY_WRITE_REVIEWED = "memory_write_reviewed"
    ROLLBACK_OR_COMPENSATION_RECORDED = "rollback_or_compensation_recorded"
    POLICY_DECISION_RECORDED = "policy_decision_recorded"
    MODEL_CALL_SUMMARIZED = "model_call_summarized"
    TOOL_RESULT_RECORDED = "tool_result_recorded"


class BehavioralContractEvidenceType(str, Enum):
    TRACE_EVENT = "trace_event"
    STATE_DIFF = "state_diff"
    TEST_RESULT = "test_result"
    OPERATOR_APPROVAL = "operator_approval"
    POLICY_DECISION = "policy_decision"
    TOOL_OUTPUT = "tool_output"
    MODEL_CALL_SUMMARY = "model_call_summary"
    SOURCE_REFERENCE = "source_reference"
    SANDBOX_REPORT = "sandbox_report"
    OUTPUT_PASSPORT = "output_passport"
    MEMORY_WRITE_RECORD = "memory_write_record"
    ERROR_REPORT = "error_report"


class BehavioralContractEscalationTrigger(str, Enum):
    RISK_TIER_ABOVE_THRESHOLD = "risk_tier_above_threshold"
    MISSING_EVIDENCE = "missing_evidence"
    POLICY_CONFLICT = "policy_conflict"
    UNCERTAIN_AUTHORITY = "uncertain_authority"
    EXTERNAL_EGRESS = "external_egress"
    IRREVERSIBLE_ACTION = "irreversible_action"
    MEMORY_WRITE_HIGH_IMPACT = "memory_write_high_impact"
    PROTECTED_PATH_WRITE = "protected_path_write"
    SANDBOX_UNCERTAIN = "sandbox_uncertain"
    MODEL_ROUTE_UNCERTAIN = "model_route_uncertain"
    SOURCE_TRUST_LOW = "source_trust_low"


class BehavioralContractEscalationAction(str, Enum):
    REQUEST_OPERATOR_APPROVAL = "request_operator_approval"
    PAUSE_WORKFLOW = "pause_workflow"
    DENY_ACTION = "deny_action"
    REQUIRE_ADDITIONAL_EVIDENCE = "require_additional_evidence"
    REQUIRE_POLICY_RESOLUTION = "require_policy_resolution"
    REQUIRE_HUMAN_REVIEW = "require_human_review"


# ---------------------------------------------------------------------------
# 15 frozen dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BehavioralContractIdentity:
    contract_id: str
    slug: str
    name: str
    version: str
    namespace: str


@dataclass(frozen=True)
class BehavioralContractSubject:
    subject_type: BehavioralContractSubjectType
    subject_id: str | None = None
    applies_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class BehavioralContractScope:
    scope_type: BehavioralContractScopeType
    scope_id: str | None = None
    applies_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class BehavioralContractObligation:
    obligation_type: BehavioralContractObligationType
    description: str
    required: bool = True


@dataclass(frozen=True)
class BehavioralContractProhibition:
    prohibition_type: BehavioralContractProhibitionType
    description: str
    strict: bool = True


@dataclass(frozen=True)
class BehavioralContractPrecondition:
    precondition_type: BehavioralContractPreconditionType
    description: str
    required: bool = True


@dataclass(frozen=True)
class BehavioralContractPostcondition:
    postcondition_type: BehavioralContractPostconditionType
    description: str
    required: bool = True


@dataclass(frozen=True)
class BehavioralContractEvidenceRequirement:
    evidence_type: BehavioralContractEvidenceType
    required: bool = True
    description: str = ""


@dataclass(frozen=True)
class BehavioralContractEscalationRule:
    trigger: BehavioralContractEscalationTrigger
    action: BehavioralContractEscalationAction
    description: str = ""


@dataclass(frozen=True)
class BehavioralContractSource:
    source_type: str
    source_path: str | None = None
    raw_source_hash: str | None = None
    canonical_hash: str | None = None
    loaded_at: str | None = None


@dataclass(frozen=True)
class BehavioralContractValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"


@dataclass(frozen=True)
class BehavioralContractValidationResult:
    valid: bool
    errors: tuple[BehavioralContractValidationIssue, ...]
    warnings: tuple[BehavioralContractValidationIssue, ...]
    contract_id: str | None = None
    canonical_hash: str | None = None


@dataclass(frozen=True)
class BehavioralContract:
    schema_version: str
    identity: BehavioralContractIdentity
    status: BehavioralContractStatus
    subject: BehavioralContractSubject
    scope: BehavioralContractScope
    policy_card_refs: tuple[str, ...]
    obligations: tuple[BehavioralContractObligation, ...]
    prohibitions: tuple[BehavioralContractProhibition, ...]
    preconditions: tuple[BehavioralContractPrecondition, ...]
    postconditions: tuple[BehavioralContractPostcondition, ...]
    evidence_requirements: tuple[BehavioralContractEvidenceRequirement, ...]
    escalation_rules: tuple[BehavioralContractEscalationRule, ...]
    source: BehavioralContractSource | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_issue(code: str, message: str, field: str | None = None,
                severity: str = "error") -> BehavioralContractValidationIssue:
    return BehavioralContractValidationIssue(
        code=code, message=message, field=field, severity=severity,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_VALID_STATUSES = frozenset(s.value for s in BehavioralContractStatus)
_VALID_SUBJECT_TYPES = frozenset(t.value for t in BehavioralContractSubjectType)
_VALID_SCOPE_TYPES = frozenset(t.value for t in BehavioralContractScopeType)
_VALID_OBLIGATION_TYPES = frozenset(t.value for t in BehavioralContractObligationType)
_VALID_PROHIBITION_TYPES = frozenset(t.value for t in BehavioralContractProhibitionType)
_VALID_PRECONDITION_TYPES = frozenset(t.value for t in BehavioralContractPreconditionType)
_VALID_POSTCONDITION_TYPES = frozenset(t.value for t in BehavioralContractPostconditionType)
_VALID_EVIDENCE_TYPES = frozenset(t.value for t in BehavioralContractEvidenceType)
_VALID_ESCALATION_TRIGGERS = frozenset(t.value for t in BehavioralContractEscalationTrigger)
_VALID_ESCALATION_ACTIONS = frozenset(t.value for t in BehavioralContractEscalationAction)

SUPPORTED_CONTRACT_SCHEMA_VERSIONS = frozenset({"1.0"})

# Known top-level fields (closed-world)
_KNOWN_TOP_FIELDS = frozenset({
    "schema_version", "identity", "status", "subject", "scope",
    "policy_card_refs", "obligations", "prohibitions", "preconditions",
    "postconditions", "evidence_requirements", "escalation_rules",
    "source", "metadata",
})

_DANGEROUS_TOP_FIELDS = frozenset({
    "authority_grant", "grant_authority", "permission_grant",
    "permissions_granted", "bypass_policy", "policy_bypass",
    "disable_policy", "skip_policy", "skip_trace", "skip_evidence",
    "ignore_evidence", "allow_untrusted_write", "allow_secret_access",
    "disable_oversight", "operator_not_required", "silent_egress_allowed",
    "memory_write_allowed", "tool_write_allowed", "sandbox_override",
    "model_override", "risk_override", "operator_override",
    "unrestricted", "execute_anyway", "ignore_contract", "disable_contract",
})

_DANGEROUS_META_KEYS = frozenset({
    "authority", "authority_grant", "grant_authority", "permissions",
    "permission_grant", "risk_override", "risk override", "egress",
    "memory_write", "memory write", "tool_write", "tool write",
    "sandbox_override", "sandbox override", "model_override",
    "model override", "operator_override", "operator override",
    "policy_bypass", "policy bypass", "bypass_policy", "trace_bypass",
    "trace bypass", "evidence_bypass", "delegation_grant", "secret_access",
    "network_access", "contract_bypass", "runtime enforcement",
    "operator_not_required", "unrestricted",
})


def validate_behavioral_contract(
    contract: BehavioralContract,
) -> BehavioralContractValidationResult:
    errors: list[BehavioralContractValidationIssue] = []
    warnings: list[BehavioralContractValidationIssue] = []

    # Schema version
    if not contract.schema_version or contract.schema_version not in SUPPORTED_CONTRACT_SCHEMA_VERSIONS:
        errors.append(_make_issue(
            "UNSUPPORTED_SCHEMA_VERSION",
            f"schema_version '{contract.schema_version}' not supported",
            field="schema_version"))

    # Identity
    ident = contract.identity
    for field_name in ("contract_id", "slug", "name", "version", "namespace"):
        if not getattr(ident, field_name, "").strip():
            errors.append(_make_issue("MISSING_REQUIRED",
                                       f"identity.{field_name} is required",
                                       field=f"identity.{field_name}"))

    # Status
    if contract.status.value not in _VALID_STATUSES:
        errors.append(_make_issue("INVALID_ENUM",
                                   f"status '{contract.status.value}' invalid",
                                   field="status"))

    # Subject
    if contract.subject.subject_type.value not in _VALID_SUBJECT_TYPES:
        errors.append(_make_issue("INVALID_ENUM",
                                   f"subject.subject_type invalid",
                                   field="subject.subject_type"))

    # Scope
    if contract.scope.scope_type.value not in _VALID_SCOPE_TYPES:
        errors.append(_make_issue("INVALID_ENUM",
                                   f"scope.scope_type invalid",
                                   field="scope.scope_type"))

    # Policy card refs
    if not isinstance(contract.policy_card_refs, tuple):
        errors.append(_make_issue("INVALID_TYPE",
                                   "policy_card_refs must be a tuple", field="policy_card_refs"))
    else:
        for i, ref in enumerate(contract.policy_card_refs):
            if not isinstance(ref, str):
                errors.append(_make_issue("INVALID_TYPE",
                                           f"policy_card_refs[{i}] must be a string",
                                           field=f"policy_card_refs[{i}]"))

    # Obligations
    for i, obl in enumerate(contract.obligations):
        if obl.obligation_type.value not in _VALID_OBLIGATION_TYPES:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"obligations[{i}].obligation_type invalid",
                                       field=f"obligations[{i}]"))
        if not obl.description.strip():
            errors.append(_make_issue("MISSING_REQUIRED",
                                       f"obligations[{i}].description required",
                                       field=f"obligations[{i}]"))

    # Prohibitions
    for i, proh in enumerate(contract.prohibitions):
        if proh.prohibition_type.value not in _VALID_PROHIBITION_TYPES:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"prohibitions[{i}].prohibition_type invalid",
                                       field=f"prohibitions[{i}]"))
        if not proh.description.strip():
            errors.append(_make_issue("MISSING_REQUIRED",
                                       f"prohibitions[{i}].description required",
                                       field=f"prohibitions[{i}]"))

    # Preconditions
    for i, pre in enumerate(contract.preconditions):
        if pre.precondition_type.value not in _VALID_PRECONDITION_TYPES:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"preconditions[{i}].precondition_type invalid",
                                       field=f"preconditions[{i}]"))
        if not pre.description.strip():
            errors.append(_make_issue("MISSING_REQUIRED",
                                       f"preconditions[{i}].description required",
                                       field=f"preconditions[{i}]"))

    # Postconditions
    for i, post in enumerate(contract.postconditions):
        if post.postcondition_type.value not in _VALID_POSTCONDITION_TYPES:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"postconditions[{i}].postcondition_type invalid",
                                       field=f"postconditions[{i}]"))
        if not post.description.strip():
            errors.append(_make_issue("MISSING_REQUIRED",
                                       f"postconditions[{i}].description required",
                                       field=f"postconditions[{i}]"))

    # Evidence requirements
    for i, ev in enumerate(contract.evidence_requirements):
        if ev.evidence_type.value not in _VALID_EVIDENCE_TYPES:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"evidence_requirements[{i}].evidence_type invalid",
                                       field=f"evidence_requirements[{i}]"))

    # Escalation rules
    for i, esc in enumerate(contract.escalation_rules):
        if esc.trigger.value not in _VALID_ESCALATION_TRIGGERS:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"escalation_rules[{i}].trigger invalid",
                                       field=f"escalation_rules[{i}]"))
        if esc.action.value not in _VALID_ESCALATION_ACTIONS:
            errors.append(_make_issue("INVALID_ENUM",
                                       f"escalation_rules[{i}].action invalid",
                                       field=f"escalation_rules[{i}]"))

    # Metadata safety
    for key in contract.metadata:
        if key in _DANGEROUS_META_KEYS:
            errors.append(_make_issue("UNSAFE_METADATA_KEY",
                                       f"metadata: dangerous key '{key}' rejected",
                                       field=f"metadata.{key}"))

    # Source
    if contract.source is not None:
        if not contract.source.source_type.strip():
            errors.append(_make_issue("MISSING_REQUIRED",
                                       "source.source_type is required",
                                       field="source.source_type"))

    valid = len(errors) == 0
    contract_id = contract.identity.contract_id if contract.identity else None

    try:
        ch = compute_behavioral_contract_hash(contract)
    except Exception:
        ch = None

    return BehavioralContractValidationResult(
        valid=valid, errors=tuple(errors), warnings=tuple(warnings),
        contract_id=contract_id, canonical_hash=ch,
    )


def load_behavioral_contract_from_dict(data: Mapping[str, Any]) -> BehavioralContract:
    if not isinstance(data, dict):
        raise BehavioralContractValidationError("data must be a mapping")

    present = set(data.keys())

    # Dangerous fields first
    dangerous = present & _DANGEROUS_TOP_FIELDS
    if dangerous:
        raise BehavioralContractUnsafeFieldError(
            f"dangerous field(s): {', '.join(sorted(dangerous))}")

    # Unknown fields
    unknown = present - _KNOWN_TOP_FIELDS
    if unknown:
        raise BehavioralContractUnknownFieldError(
            f"unknown field(s): {', '.join(sorted(unknown))} — closed-world")

    # Schema version
    sv = data.get("schema_version")
    if not isinstance(sv, str) or sv not in SUPPORTED_CONTRACT_SCHEMA_VERSIONS:
        raise BehavioralContractValidationError(
            f"schema_version must be one of: "
            f"{', '.join(sorted(SUPPORTED_CONTRACT_SCHEMA_VERSIONS))}")

    # Identity
    id_raw = data.get("identity", {})
    if not isinstance(id_raw, dict):
        raise BehavioralContractValidationError("identity must be a mapping")
    identity = BehavioralContractIdentity(
        contract_id=str(id_raw.get("contract_id", "")),
        slug=str(id_raw.get("slug", "")),
        name=str(id_raw.get("name", "")),
        version=str(id_raw.get("version", "")),
        namespace=str(id_raw.get("namespace", "")),
    )

    # Status
    status_raw = data.get("status")
    if not isinstance(status_raw, str) or status_raw not in _VALID_STATUSES:
        raise BehavioralContractValidationError(f"invalid status: {status_raw!r}")
    status = BehavioralContractStatus(status_raw)

    # Subject
    subj_raw = data.get("subject", {})
    if not isinstance(subj_raw, dict):
        raise BehavioralContractValidationError("subject must be a mapping")
    st_raw = subj_raw.get("subject_type", "")
    if not isinstance(st_raw, str) or st_raw not in _VALID_SUBJECT_TYPES:
        raise BehavioralContractValidationError(f"invalid subject_type: {st_raw}")
    subject = BehavioralContractSubject(
        subject_type=BehavioralContractSubjectType(st_raw),
        subject_id=subj_raw.get("subject_id"),
        applies_to=tuple(subj_raw.get("applies_to", ())),
    )

    # Scope
    scope_raw = data.get("scope", {})
    if not isinstance(scope_raw, dict):
        raise BehavioralContractValidationError("scope must be a mapping")
    sc_raw = scope_raw.get("scope_type", "")
    if not isinstance(sc_raw, str) or sc_raw not in _VALID_SCOPE_TYPES:
        raise BehavioralContractValidationError(f"invalid scope_type: {sc_raw}")
    scope = BehavioralContractScope(
        scope_type=BehavioralContractScopeType(sc_raw),
        scope_id=scope_raw.get("scope_id"),
        applies_to=tuple(scope_raw.get("applies_to", ())),
    )

    # Policy card refs
    refs_raw = data.get("policy_card_refs", ())
    if not isinstance(refs_raw, (list, tuple)):
        raise BehavioralContractValidationError("policy_card_refs must be a list/tuple")
    for i, ref in enumerate(refs_raw):
        if not isinstance(ref, str):
            raise BehavioralContractValidationError(
                f"policy_card_refs[{i}] must be a string")
    policy_card_refs = tuple(str(r) for r in refs_raw)

    # Obligations
    obligations: list[BehavioralContractObligation] = []
    for i, obl in enumerate(data.get("obligations", ())):
        if not isinstance(obl, dict):
            raise BehavioralContractValidationError(f"obligations[{i}] must be a mapping")
        ot = obl.get("obligation_type", "")
        if not isinstance(ot, str) or ot not in _VALID_OBLIGATION_TYPES:
            raise BehavioralContractValidationError(f"obligations[{i}]: invalid type: {ot}")
        obligations.append(BehavioralContractObligation(
            obligation_type=BehavioralContractObligationType(ot),
            description=str(obl.get("description", "")),
            required=bool(obl.get("required", True)),
        ))

    # Prohibitions
    prohibitions: list[BehavioralContractProhibition] = []
    for i, proh in enumerate(data.get("prohibitions", ())):
        if not isinstance(proh, dict):
            raise BehavioralContractValidationError(f"prohibitions[{i}] must be a mapping")
        pt = proh.get("prohibition_type", "")
        if not isinstance(pt, str) or pt not in _VALID_PROHIBITION_TYPES:
            raise BehavioralContractValidationError(f"prohibitions[{i}]: invalid type: {pt}")
        prohibitions.append(BehavioralContractProhibition(
            prohibition_type=BehavioralContractProhibitionType(pt),
            description=str(proh.get("description", "")),
            strict=bool(proh.get("strict", True)),
        ))

    # Preconditions
    preconditions: list[BehavioralContractPrecondition] = []
    for i, pre in enumerate(data.get("preconditions", ())):
        if not isinstance(pre, dict):
            raise BehavioralContractValidationError(f"preconditions[{i}] must be a mapping")
        pt = pre.get("precondition_type", "")
        if not isinstance(pt, str) or pt not in _VALID_PRECONDITION_TYPES:
            raise BehavioralContractValidationError(f"preconditions[{i}]: invalid type: {pt}")
        preconditions.append(BehavioralContractPrecondition(
            precondition_type=BehavioralContractPreconditionType(pt),
            description=str(pre.get("description", "")),
            required=bool(pre.get("required", True)),
        ))

    # Postconditions
    postconditions: list[BehavioralContractPostcondition] = []
    for i, post in enumerate(data.get("postconditions", ())):
        if not isinstance(post, dict):
            raise BehavioralContractValidationError(f"postconditions[{i}] must be a mapping")
        pt = post.get("postcondition_type", "")
        if not isinstance(pt, str) or pt not in _VALID_POSTCONDITION_TYPES:
            raise BehavioralContractValidationError(f"postconditions[{i}]: invalid type: {pt}")
        postconditions.append(BehavioralContractPostcondition(
            postcondition_type=BehavioralContractPostconditionType(pt),
            description=str(post.get("description", "")),
            required=bool(post.get("required", True)),
        ))

    # Evidence requirements
    evidence_reqs: list[BehavioralContractEvidenceRequirement] = []
    for i, ev in enumerate(data.get("evidence_requirements", ())):
        if not isinstance(ev, dict):
            raise BehavioralContractValidationError(f"evidence_requirements[{i}] must be a mapping")
        et = ev.get("evidence_type", "")
        if not isinstance(et, str) or et not in _VALID_EVIDENCE_TYPES:
            raise BehavioralContractValidationError(f"evidence_requirements[{i}]: invalid type: {et}")
        evidence_reqs.append(BehavioralContractEvidenceRequirement(
            evidence_type=BehavioralContractEvidenceType(et),
            required=bool(ev.get("required", True)),
            description=str(ev.get("description", "")),
        ))

    # Escalation rules
    escalation_rules: list[BehavioralContractEscalationRule] = []
    for i, esc in enumerate(data.get("escalation_rules", ())):
        if not isinstance(esc, dict):
            raise BehavioralContractValidationError(f"escalation_rules[{i}] must be a mapping")
        trig = esc.get("trigger", "")
        act = esc.get("action", "")
        if not isinstance(trig, str) or trig not in _VALID_ESCALATION_TRIGGERS:
            raise BehavioralContractValidationError(f"escalation_rules[{i}]: invalid trigger: {trig}")
        if not isinstance(act, str) or act not in _VALID_ESCALATION_ACTIONS:
            raise BehavioralContractValidationError(f"escalation_rules[{i}]: invalid action: {act}")
        escalation_rules.append(BehavioralContractEscalationRule(
            trigger=BehavioralContractEscalationTrigger(trig),
            action=BehavioralContractEscalationAction(act),
            description=str(esc.get("description", "")),
        ))

    # Source
    src_raw = data.get("source")
    source: BehavioralContractSource | None = None
    if src_raw is not None:
        if not isinstance(src_raw, dict):
            raise BehavioralContractValidationError("source must be a mapping")
        source = BehavioralContractSource(
            source_type=str(src_raw.get("source_type", "")),
            source_path=src_raw.get("source_path"),
            raw_source_hash=src_raw.get("raw_source_hash"),
            canonical_hash=src_raw.get("canonical_hash"),
            loaded_at=src_raw.get("loaded_at"),
        )

    # Metadata
    meta_raw = data.get("metadata")
    if meta_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(meta_raw, dict):
        dangerous_meta = set(meta_raw.keys()) & _DANGEROUS_META_KEYS
        if dangerous_meta:
            raise BehavioralContractUnsafeFieldError(
                f"dangerous metadata key(s): {', '.join(sorted(dangerous_meta))}")
        metadata = dict(meta_raw)
    else:
        raise BehavioralContractValidationError("metadata must be a mapping")

    contract = BehavioralContract(
        schema_version=sv,
        identity=identity,
        status=status,
        subject=subject,
        scope=scope,
        policy_card_refs=policy_card_refs,
        obligations=tuple(obligations),
        prohibitions=tuple(prohibitions),
        preconditions=tuple(preconditions),
        postconditions=tuple(postconditions),
        evidence_requirements=tuple(evidence_reqs),
        escalation_rules=tuple(escalation_rules),
        source=source,
        metadata=metadata,
    )

    result = validate_behavioral_contract(contract)
    if not result.valid:
        msgs = "; ".join(e.message for e in result.errors)
        raise BehavioralContractValidationError(f"validation failed: {msgs}")

    return contract


# ---------------------------------------------------------------------------
# Deterministic serialization
# ---------------------------------------------------------------------------

def _identity_to_dict(ident: BehavioralContractIdentity) -> dict[str, Any]:
    return {
        "contract_id": ident.contract_id,
        "name": ident.name,
        "namespace": ident.namespace,
        "slug": ident.slug,
        "version": ident.version,
    }


def _subject_to_dict(subj: BehavioralContractSubject) -> dict[str, Any]:
    result: dict[str, Any] = {"subject_type": subj.subject_type.value}
    if subj.subject_id is not None:
        result["subject_id"] = subj.subject_id
    if subj.applies_to:
        result["applies_to"] = list(subj.applies_to)
    return result


def _scope_to_dict(scope: BehavioralContractScope) -> dict[str, Any]:
    result: dict[str, Any] = {"scope_type": scope.scope_type.value}
    if scope.scope_id is not None:
        result["scope_id"] = scope.scope_id
    if scope.applies_to:
        result["applies_to"] = list(scope.applies_to)
    return result


def _obligation_to_dict(obl: BehavioralContractObligation) -> dict[str, Any]:
    return {
        "description": obl.description,
        "obligation_type": obl.obligation_type.value,
        "required": obl.required,
    }


def _prohibition_to_dict(proh: BehavioralContractProhibition) -> dict[str, Any]:
    return {
        "description": proh.description,
        "prohibition_type": proh.prohibition_type.value,
        "strict": proh.strict,
    }


def _precondition_to_dict(pre: BehavioralContractPrecondition) -> dict[str, Any]:
    return {
        "description": pre.description,
        "precondition_type": pre.precondition_type.value,
        "required": pre.required,
    }


def _postcondition_to_dict(post: BehavioralContractPostcondition) -> dict[str, Any]:
    return {
        "description": post.description,
        "postcondition_type": post.postcondition_type.value,
        "required": post.required,
    }


def _evidence_to_dict(ev: BehavioralContractEvidenceRequirement) -> dict[str, Any]:
    return {
        "description": ev.description,
        "evidence_type": ev.evidence_type.value,
        "required": ev.required,
    }


def _escalation_to_dict(esc: BehavioralContractEscalationRule) -> dict[str, Any]:
    return {
        "action": esc.action.value,
        "description": esc.description,
        "trigger": esc.trigger.value,
    }


def _source_to_dict(src: BehavioralContractSource) -> dict[str, Any]:
    result: dict[str, Any] = {"source_type": src.source_type}
    if src.source_path is not None:
        result["source_path"] = src.source_path
    if src.canonical_hash is not None:
        result["canonical_hash"] = src.canonical_hash
    if src.loaded_at is not None:
        result["loaded_at"] = src.loaded_at
    return result


def behavioral_contract_to_canonical_dict(
    contract: BehavioralContract,
) -> dict[str, Any]:
    obligations_sorted = sorted(
        (_obligation_to_dict(o) for o in contract.obligations),
        key=lambda x: x["obligation_type"],
    )
    prohibitions_sorted = sorted(
        (_prohibition_to_dict(p) for p in contract.prohibitions),
        key=lambda x: x["prohibition_type"],
    )
    preconditions_sorted = sorted(
        (_precondition_to_dict(p) for p in contract.preconditions),
        key=lambda x: x["precondition_type"],
    )
    postconditions_sorted = sorted(
        (_postcondition_to_dict(p) for p in contract.postconditions),
        key=lambda x: x["postcondition_type"],
    )
    evidence_sorted = sorted(
        (_evidence_to_dict(e) for e in contract.evidence_requirements),
        key=lambda x: x["evidence_type"],
    )
    escalation_sorted = sorted(
        (_escalation_to_dict(e) for e in contract.escalation_rules),
        key=lambda x: (x["trigger"], x["action"]),
    )

    canonical: dict[str, Any] = {
        "escalation_rules": escalation_sorted,
        "evidence_requirements": evidence_sorted,
        "identity": _identity_to_dict(contract.identity),
        "obligations": obligations_sorted,
        "policy_card_refs": sorted(contract.policy_card_refs),
        "postconditions": postconditions_sorted,
        "preconditions": preconditions_sorted,
        "prohibitions": prohibitions_sorted,
        "schema_version": contract.schema_version,
        "scope": _scope_to_dict(contract.scope),
        "status": contract.status.value,
        "subject": _subject_to_dict(contract.subject),
    }

    if contract.source is not None:
        canonical["source"] = _source_to_dict(contract.source)

    if contract.metadata:
        canonical["metadata"] = dict(sorted(
            contract.metadata.items(), key=lambda x: x[0]))

    return dict(sorted(canonical.items(), key=lambda x: x[0]))


def serialize_behavioral_contract_canonical(
    contract: BehavioralContract,
) -> str:
    canonical = behavioral_contract_to_canonical_dict(contract)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def compute_behavioral_contract_hash(contract: BehavioralContract) -> str:
    canonical = serialize_behavioral_contract_canonical(contract)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
