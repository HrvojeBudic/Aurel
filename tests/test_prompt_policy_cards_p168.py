"""Unit tests for Prompt Policy Card model (P1.6.8).

Covers the 26 P1.6.8 test categories:
  1.  Default prompt policy card valid
  2.  Default decision is strict
  3.  Unknown source cannot be trusted
  4.  External web content cannot be instruction
  5.  Email content cannot be instruction
  6.  Tool output cannot command
  7.  Retrieved memory cannot command
  8.  Untrusted prompt cannot request tools
  9.  Untrusted prompt cannot write memory
  10. Untrusted prompt cannot modify policy
  11. Untrusted prompt cannot modify identity
  12. High injection risk cannot be instruction authority
  13. Trusted system/developer/operator classes validate
  14. Invalid source type rejected
  15. Invalid trust level rejected
  16. Invalid prompt role rejected
  17. Invalid decision rejected
  18. Dangerous metadata rejected
  19. Safe metadata accepted
  20. PolicyCard compatibility
  21. Closed-world unknown field rejected
  22. Deterministic serialization
  23. Hash stability
  24. Schema export deterministic
  25. Existing P1.6.0-P1.6.7 tests still pass (separate suites)
  26. No runtime enforcement
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.agentic_runtime.policy_cards.prompt_policy import (
    PromptBoundaryRequirement,
    PromptBoundaryRequirementType,
    PromptHandlingRule,
    PromptInjectionPattern,
    PromptInjectionRisk,
    PromptInjectionSignal,
    PromptPolicyCard,
    PromptPolicyDecision,
    PromptPolicyValidationIssue,
    PromptPolicyValidationResult,
    PromptRole,
    PromptSourceType,
    PromptTrustLevel,
    compute_prompt_policy_card_hash,
    create_default_prompt_policy_card,
    load_prompt_policy_card_from_dict,
    prompt_policy_card_to_canonical_dict,
    serialize_prompt_policy_card_canonical,
    validate_prompt_policy_card,
    validate_prompt_policy_card_dict,
)
from src.agentic_runtime.policy_cards.prompt_policy_schema import (
    DEFAULT_PROMPT_HANDLING_RULES,
    EXTERNAL_PROMPT_SOURCES,
    PROMPT_POLICY_CARD_SCHEMA_VERSION,
    PROTECTED_PROMPT_SOURCES,
    TRUSTED_PROMPT_SOURCES,
    UNTRUSTED_PROMPT_SOURCES,
    export_prompt_policy_schema,
    get_prompt_policy_schema,
    is_supported_prompt_policy_schema_version,
    validate_prompt_policy_schema_version,
)
from src.agentic_runtime.policy_cards.errors import (
    PolicyCardError,
    PromptPolicyCardError,
    PromptPolicyCardUnknownFieldError,
    PromptPolicyCardUnsafeFieldError,
    PromptPolicyCardValidationError,
)
from src.agentic_runtime.policy_cards.models import PolicyCardKind


# ───────────────────────── Helpers ─────────────────────────


def _make_default_card() -> PromptPolicyCard:
    return create_default_prompt_policy_card()


def _rule_dict(
    source_type: str,
    trust_level: str,
    prompt_role: str,
    decision: str,
    **overrides,
) -> dict:
    base = {
        "source_type": source_type,
        "trust_level": trust_level,
        "prompt_role": prompt_role,
        "decision": decision,
        "allowed_as_instruction": False,
        "allowed_as_context": True,
        "allowed_to_request_tools": False,
        "allowed_to_write_memory": False,
        "allowed_to_modify_policy": False,
        "allowed_to_modify_identity": False,
        "requires_provenance": True,
        "requires_redaction": False,
        "requires_review": False,
        "requires_sandbox": False,
        "local_only": False,
        "injection_risk": "none",
        "injection_signals": [],
        "requirements": [],
        "description": "test rule",
    }
    base.update(overrides)
    return base


def _to_dict(card: PromptPolicyCard) -> dict:
    from src.agentic_runtime.policy_cards.serialization import (
        policy_card_to_canonical_dict,
    )

    return {
        "policy_card": policy_card_to_canonical_dict(card.policy_card),
        "schema_version": card.schema_version,
        "prompt_rules": [
            {
                "source_type": r.source_type.value,
                "trust_level": r.trust_level.value,
                "prompt_role": r.prompt_role.value,
                "decision": r.decision.value,
                "allowed_as_instruction": r.allowed_as_instruction,
                "allowed_as_context": r.allowed_as_context,
                "allowed_to_request_tools": r.allowed_to_request_tools,
                "allowed_to_write_memory": r.allowed_to_write_memory,
                "allowed_to_modify_policy": r.allowed_to_modify_policy,
                "allowed_to_modify_identity": r.allowed_to_modify_identity,
                "requires_provenance": r.requires_provenance,
                "requires_redaction": r.requires_redaction,
                "requires_review": r.requires_review,
                "requires_sandbox": r.requires_sandbox,
                "local_only": r.local_only,
                "injection_risk": r.injection_risk.value,
                "injection_signals": [
                    {
                        "pattern": s.pattern.value,
                        "risk": s.risk.value,
                        "description": s.description,
                    }
                    for s in r.injection_signals
                ],
                "requirements": [
                    {
                        "requirement_type": req.requirement_type.value,
                        "required": req.required,
                        "description": req.description,
                    }
                    for req in r.requirements
                ],
                "risk_ceiling": r.risk_ceiling,
                "required_oversight": r.required_oversight,
                "description": r.description,
            }
            for r in card.prompt_rules
        ],
        "default_decision": card.default_decision.value,
        "metadata": dict(card.metadata),
    }


# ───────────────────────── 1. Default card validity ─────────────────────────


def test_default_card_is_valid():
    card = _make_default_card()
    result = validate_prompt_policy_card(card)
    assert result.valid, f"unexpected errors: {result.errors}"
    assert card.schema_version == PROMPT_POLICY_CARD_SCHEMA_VERSION
    assert card.policy_card.kind == PolicyCardKind.PROMPT
    assert len(card.prompt_rules) >= 15


def test_default_rules_are_schema_default():
    card = _make_default_card()
    assert card.prompt_rules == DEFAULT_PROMPT_HANDLING_RULES


# ───────────────────────── 2. Default decision is strict ─────────────────────


def test_default_decision_is_deny():
    card = _make_default_card()
    assert card.default_decision == PromptPolicyDecision.DENY


def test_allow_default_decision_rejected():
    data = _to_dict(_make_default_card())
    data["default_decision"] = "allow"
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


def test_context_only_default_decision_rejected():
    data = _to_dict(_make_default_card())
    data["default_decision"] = "context_only"
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 3. Unknown source cannot be trusted ───────────────


@pytest.mark.parametrize("trust", [
    "trusted_system", "trusted_developer", "operator_authorized",
    "repo_canonical", "verified_template",
])
def test_unknown_source_cannot_be_trusted(trust):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("unknown", trust, "context", "context_only")
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 4. External web content cannot be instruction ─────


def test_web_content_cannot_be_instruction():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("web_content", "external_untrusted", "instruction", "allow",
                   allowed_as_instruction=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 5. Email content cannot be instruction ────────────


def test_email_content_cannot_be_instruction():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("email_content", "external_untrusted", "instruction", "allow",
                   allowed_as_instruction=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 6. Tool output cannot command ─────────────────────


def test_tool_output_cannot_be_instruction():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("tool_output", "tool_output_untrusted", "instruction", "allow",
                   allowed_as_instruction=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid
    # Confirm specific safety code present via direct validation
    card = _make_default_card()
    bad = replace(
        card,
        prompt_rules=card.prompt_rules + (
            PromptHandlingRule(
                source_type=PromptSourceType.TOOL_OUTPUT,
                trust_level=PromptTrustLevel.TOOL_OUTPUT_UNTRUSTED,
                prompt_role=PromptRole.INSTRUCTION,
                decision=PromptPolicyDecision.ALLOW,
                allowed_as_instruction=True,
            ),
        ),
    )
    res = validate_prompt_policy_card(bad)
    assert not res.valid
    assert "TOOL_OUTPUT_AS_INSTRUCTION" in {e.code for e in res.errors}


# ───────────────────────── 7. Retrieved memory cannot command ────────────────


def test_retrieved_memory_cannot_be_instruction():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("retrieved_memory", "retrieved_context", "instruction", "allow",
                   allowed_as_instruction=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 8. Untrusted cannot request tools ─────────────────


@pytest.mark.parametrize("trust,source", [
    ("external_untrusted", "web_content"),
    ("tool_output_untrusted", "tool_output"),
    ("unknown_untrusted", "unknown"),
    ("retrieved_context", "retrieved_memory"),
])
def test_untrusted_cannot_request_tools(trust, source):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict(source, trust, "data", "context_only",
                   allowed_to_request_tools=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 9. Untrusted cannot write memory ──────────────────


@pytest.mark.parametrize("trust,source", [
    ("external_untrusted", "web_content"),
    ("tool_output_untrusted", "tool_output"),
    ("unknown_untrusted", "unknown"),
    ("retrieved_context", "retrieved_memory"),
])
def test_untrusted_cannot_write_memory(trust, source):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict(source, trust, "data", "context_only",
                   allowed_to_write_memory=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 10. Untrusted cannot modify policy ────────────────


@pytest.mark.parametrize("trust,source", [
    ("external_untrusted", "web_content"),
    ("tool_output_untrusted", "tool_output"),
    ("unknown_untrusted", "unknown"),
    ("retrieved_context", "retrieved_memory"),
])
def test_untrusted_cannot_modify_policy(trust, source):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict(source, trust, "data", "context_only",
                   allowed_to_modify_policy=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 11. Untrusted cannot modify identity ──────────────


@pytest.mark.parametrize("trust,source", [
    ("external_untrusted", "web_content"),
    ("tool_output_untrusted", "tool_output"),
    ("unknown_untrusted", "unknown"),
    ("retrieved_context", "retrieved_memory"),
])
def test_untrusted_cannot_modify_identity(trust, source):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict(source, trust, "data", "context_only",
                   allowed_to_modify_identity=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


# ───────────────────────── 12. High injection risk + instruction ─────────────


def test_high_injection_risk_instruction_rejected():
    # Use a trusted source so the only failing condition is injection risk
    card = _make_default_card()
    bad = replace(
        card,
        prompt_rules=card.prompt_rules + (
            PromptHandlingRule(
                source_type=PromptSourceType.DEVELOPER_PROMPT,
                trust_level=PromptTrustLevel.TRUSTED_DEVELOPER,
                prompt_role=PromptRole.INSTRUCTION,
                decision=PromptPolicyDecision.ALLOW,
                allowed_as_instruction=True,
                injection_risk=PromptInjectionRisk.CRITICAL,
            ),
        ),
    )
    res = validate_prompt_policy_card(bad)
    assert not res.valid
    assert "INJECTION_RISK_PERMISSIVE_INSTRUCTION" in {e.code for e in res.errors}


def test_high_injection_signal_instruction_rejected():
    card = _make_default_card()
    bad = replace(
        card,
        prompt_rules=card.prompt_rules + (
            PromptHandlingRule(
                source_type=PromptSourceType.DEVELOPER_PROMPT,
                trust_level=PromptTrustLevel.TRUSTED_DEVELOPER,
                prompt_role=PromptRole.INSTRUCTION,
                decision=PromptPolicyDecision.ALLOW,
                allowed_as_instruction=True,
                injection_risk=PromptInjectionRisk.NONE,
                injection_signals=(
                    PromptInjectionSignal(
                        pattern=PromptInjectionPattern.IGNORE_PREVIOUS_INSTRUCTIONS,
                        risk=PromptInjectionRisk.HIGH,
                    ),
                ),
            ),
        ),
    )
    res = validate_prompt_policy_card(bad)
    assert not res.valid


# ───────────────────────── 13. Trusted classes validate ──────────────────────


def test_trusted_system_developer_operator_validate():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("system_prompt", "trusted_system", "instruction", "allow",
                   allowed_as_instruction=True)
    )
    data["prompt_rules"].append(
        _rule_dict("operator_prompt", "operator_authorized", "instruction", "allow",
                   allowed_as_instruction=True, allowed_to_request_tools=True,
                   allowed_to_write_memory=True)
    )
    result = validate_prompt_policy_card_dict(data)
    assert result.valid, f"unexpected errors: {result.errors}"


# ───────────────────────── 14. Invalid source type rejected ──────────────────


@pytest.mark.parametrize("src", ["shadow_system", "fake_operator", "super_admin_prompt"])
def test_invalid_source_type_rejected(src):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict(src, "external_untrusted", "data", "context_only")
    )
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict(data)


# ───────────────────────── 15. Invalid trust level rejected ──────────────────


@pytest.mark.parametrize("trust", ["self_trusted", "external_admin", "auto_trusted"])
def test_invalid_trust_level_rejected(trust):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("web_content", trust, "data", "context_only")
    )
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict(data)


# ───────────────────────── 16. Invalid prompt role rejected ──────────────────


@pytest.mark.parametrize("role", ["authority_grant", "secret_exfiltration", "policy_override"])
def test_invalid_prompt_role_rejected(role):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("web_content", "external_untrusted", role, "context_only")
    )
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict(data)


# ───────────────────────── 17. Invalid decision rejected ─────────────────────


@pytest.mark.parametrize("dec", ["obey_always", "ignore_policy", "force_tool_call"])
def test_invalid_decision_rejected(dec):
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("web_content", "external_untrusted", "data", dec)
    )
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict(data)


def test_invalid_injection_risk_rejected():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict("web_content", "external_untrusted", "data", "context_only",
                   injection_risk="apocalyptic")
    )
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict(data)


# ───────────────────────── 18. Dangerous metadata rejected ───────────────────


@pytest.mark.parametrize("key", [
    "bypass_prompt_policy",
    "reveal_system_prompt",
    "grant_tool_access",
    "external_as_instruction",
    "trust_unknown_source",
])
def test_dangerous_metadata_rejected(key):
    data = _to_dict(_make_default_card())
    data["metadata"][key] = True
    with pytest.raises(PromptPolicyCardUnsafeFieldError):
        load_prompt_policy_card_from_dict(data)


# ───────────────────────── 19. Safe metadata accepted ────────────────────────


def test_safe_metadata_accepted():
    data = _to_dict(_make_default_card())
    data["metadata"]["owner_note"] = "strict default prompt policy"
    data["metadata"]["created_by"] = "test suite"
    card = load_prompt_policy_card_from_dict(data)
    assert "owner_note" in card.metadata
    assert "created_by" in card.metadata


# ───────────────────────── 20. PolicyCard compatibility ──────────────────────


def test_wrong_policy_card_kind_rejected():
    data = _to_dict(_make_default_card())
    data["policy_card"]["kind"] = "risk_tier"
    result = validate_prompt_policy_card_dict(data)
    assert not result.valid


def test_correct_policy_card_kind_accepted():
    card = _make_default_card()
    assert card.policy_card.kind == PolicyCardKind.PROMPT


# ───────────────────────── 21. Closed-world unknown field rejected ───────────


def test_unknown_top_level_field_rejected():
    data = _to_dict(_make_default_card())
    data["nonexistent_field"] = True
    with pytest.raises(PromptPolicyCardUnknownFieldError):
        load_prompt_policy_card_from_dict(data)


def test_forbidden_top_level_field_rejected():
    data = _to_dict(_make_default_card())
    data["prompt_override_backdoor"] = True
    with pytest.raises(PromptPolicyCardUnsafeFieldError):
        load_prompt_policy_card_from_dict(data)


def test_unknown_rule_field_rejected():
    data = _to_dict(_make_default_card())
    data["prompt_rules"][0]["mystery_field"] = True
    with pytest.raises(PromptPolicyCardUnknownFieldError):
        load_prompt_policy_card_from_dict(data)


# ───────────────────────── 22. Deterministic serialization ───────────────────


def test_serialization_deterministic():
    s1 = serialize_prompt_policy_card_canonical(_make_default_card())
    s2 = serialize_prompt_policy_card_canonical(_make_default_card())
    assert s1 == s2


def test_serialization_produces_valid_json():
    import json
    s = serialize_prompt_policy_card_canonical(_make_default_card())
    assert isinstance(json.loads(s), dict)


def test_canonical_dict_round_trips():
    card = _make_default_card()
    data = prompt_policy_card_to_canonical_dict(card)
    reloaded = load_prompt_policy_card_from_dict(data)
    assert compute_prompt_policy_card_hash(reloaded) == \
        compute_prompt_policy_card_hash(card)


# ───────────────────────── 23. Hash stability ────────────────────────────────


def test_hash_stable():
    h1 = compute_prompt_policy_card_hash(_make_default_card())
    h2 = compute_prompt_policy_card_hash(_make_default_card())
    assert h1 == h2
    assert len(h1) == 64


def test_hash_changes_with_metadata():
    data = _to_dict(_make_default_card())
    data["metadata"]["test_key"] = "value"
    card2 = load_prompt_policy_card_from_dict(data)
    assert compute_prompt_policy_card_hash(_make_default_card()) != \
        compute_prompt_policy_card_hash(card2)


# ───────────────────────── 24. Schema export deterministic ───────────────────


def test_schema_export_has_required_keys():
    schema = export_prompt_policy_schema()
    for key in (
        "schema_version",
        "supported_versions",
        "required_fields",
        "optional_fields",
        "forbidden_fields",
        "canonical_fields",
        "rule_required_fields",
        "rule_optional_fields",
        "requirement_required_fields",
        "injection_signal_required_fields",
        "dangerous_field_names",
        "dangerous_metadata_keys",
        "trusted_prompt_sources",
        "untrusted_prompt_sources",
        "external_prompt_sources",
        "protected_prompt_sources",
        "prompt_source_types",
        "prompt_trust_levels",
        "prompt_roles",
        "prompt_policy_decisions",
        "prompt_injection_risks",
    ):
        assert key in schema, f"missing key: {key}"


def test_schema_export_deterministic():
    assert export_prompt_policy_schema() == export_prompt_policy_schema()
    assert get_prompt_policy_schema() == export_prompt_policy_schema()


def test_is_supported_schema_version():
    assert is_supported_prompt_policy_schema_version("1.0")
    assert not is_supported_prompt_policy_schema_version("0.9")
    assert not is_supported_prompt_policy_schema_version("")
    assert not is_supported_prompt_policy_schema_version(None)  # type: ignore[arg-type]


def test_validate_schema_version():
    result = validate_prompt_policy_schema_version("1.0")
    assert result.valid
    result = validate_prompt_policy_schema_version("2.0")
    assert not result.valid
    assert any(e.code == "UNSUPPORTED_SCHEMA_VERSION" for e in result.errors)


def test_source_category_constants():
    assert "system_prompt" in TRUSTED_PROMPT_SOURCES
    assert "system_prompt" in PROTECTED_PROMPT_SOURCES
    assert "web_content" in EXTERNAL_PROMPT_SOURCES
    assert "tool_output" in UNTRUSTED_PROMPT_SOURCES
    assert "unknown" in UNTRUSTED_PROMPT_SOURCES


# ───────────────────────── 26. No runtime enforcement ────────────────────────


def test_no_runtime_methods_on_card():
    card = _make_default_card()
    forbidden_attrs = {
        "compile", "assemble", "enforce", "resolve", "detect",
        "block", "execute", "render", "inject", "scan",
    }
    for attr in forbidden_attrs:
        assert not hasattr(card, attr), f"card should not have {attr}"
        assert not callable(getattr(card, attr, None))


# ───────────────────────── Edge cases ────────────────────────────────────────


def test_load_empty_dict_raises():
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict({})


def test_load_schema_version_invalid():
    data = _to_dict(_make_default_card())
    data["schema_version"] = "99.99"
    with pytest.raises(PromptPolicyCardValidationError):
        load_prompt_policy_card_from_dict(data)


def test_empty_prompt_rules_rejected():
    card = _make_default_card()
    bad = replace(card, prompt_rules=())
    result = validate_prompt_policy_card(bad)
    assert not result.valid
    assert any(e.code == "EMPTY_PROMPT_RULES" for e in result.errors)


def test_boundary_requirement_loads():
    data = _to_dict(_make_default_card())
    data["prompt_rules"].append(
        _rule_dict(
            "web_content", "external_untrusted", "data", "context_only",
            requirements=[{
                "requirement_type": "requires_provenance",
                "required": True,
                "description": "needs provenance",
            }],
        )
    )
    card = load_prompt_policy_card_from_dict(data)
    last = card.prompt_rules[-1]
    assert last.requirements
    assert last.requirements[0].requirement_type == \
        PromptBoundaryRequirementType.REQUIRES_PROVENANCE


def test_error_hierarchy():
    assert issubclass(PromptPolicyCardValidationError, PromptPolicyCardError)
    assert issubclass(PromptPolicyCardError, PolicyCardError)
    assert issubclass(PromptPolicyCardError, ValueError)


def test_validation_result_types():
    result = validate_prompt_policy_card(_make_default_card())
    assert isinstance(result, PromptPolicyValidationResult)
    for issue in result.errors:
        assert isinstance(issue, PromptPolicyValidationIssue)
