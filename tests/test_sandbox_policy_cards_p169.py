"""Tests for P1.6.9 Sandbox Policy Card Model.

Covers construction, closed-world validation, backend policy, filesystem policy,
egress policy, command class policy, decision input/output, export, and
cross-family consistency.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from agentic_runtime.policy_cards.errors import (
    SandboxPolicyCardUnknownFieldError,
    SandboxPolicyCardUnsafeFieldError,
    SandboxPolicyCardValidationError,
)
from agentic_runtime.policy_cards.models import (
    PolicyCard,
    PolicyCardIdentity,
    PolicyCardKind,
    PolicyCardScope,
    PolicyCardScopeType,
    PolicyCardStatus,
)
from agentic_runtime.policy_cards.risk_tiers import RiskTier
from agentic_runtime.policy_cards.sandbox import (
    ApprovalRequirement,
    CommandClass,
    DEFAULT_COMMAND_RULES,
    DEFAULT_EGRESS_RULES,
    DEFAULT_FILESYSTEM_RULES,
    EgressPolicy,
    FilesystemScope,
    RiskTierSandboxMapping,
    SandboxBackend,
    SandboxBackendRule,
    SandboxCommandClassRule,
    SandboxCommandDecision,
    SandboxEgressRule,
    SandboxFilesystemScopeRule,
    SandboxPolicyCard,
    SandboxPolicyDecision,
    SandboxPolicyDecisionInput,
    SandboxPolicyViolation,
    SandboxPolicyWarning,
    SandboxValidationIssue,
    SandboxValidationResult,
    compute_sandbox_policy_card_hash,
    create_default_sandbox_policy_card,
    evaluate_sandbox_policy_decision,
    load_sandbox_policy_card_from_dict,
    sandbox_policy_card_to_canonical_dict,
    serialize_sandbox_policy_card_canonical,
    validate_sandbox_policy_card,
    validate_sandbox_policy_card_dict,
)
from agentic_runtime.policy_cards.sandbox_schema import (
    SANDBOX_POLICY_CARD_SCHEMA_VERSION,
    export_sandbox_policy_schema,
    get_sandbox_policy_schema,
    is_supported_sandbox_policy_schema_version,
    validate_sandbox_policy_schema_version,
)
from agentic_runtime.policy_cards.serialization import policy_card_to_canonical_dict


def _make_policy_card(card_id: str = "test-sandbox-policy-v1") -> PolicyCard:
    return PolicyCard(
        schema_version="1.0",
        identity=PolicyCardIdentity(
            card_id=card_id,
            slug="test-sandbox-policy",
            name="Test Sandbox Policy",
            version="1.0",
            namespace="test",
        ),
        kind=PolicyCardKind.SANDBOX,
        status=PolicyCardStatus.ACTIVE,
        scope=PolicyCardScope(scope_type=PolicyCardScopeType.SANDBOX),
        description="Test sandbox policy card.",
    )


def _make_policy_card_dict(card_id: str = "test-sandbox-policy-v1") -> dict[str, Any]:
    return policy_card_to_canonical_dict(_make_policy_card(card_id))


# ===========================================================================
# 1. Construction tests
# ===========================================================================


class TestConstruction:
    def test_valid_minimal_sandbox_policy_card(self):
        """A minimal sandbox policy card with only required fields is valid."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card(),
            schema_version="1.0",
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is True, result.errors

    def test_valid_full_sandbox_policy_card(self):
        """A fully populated sandbox policy card is valid."""
        card = create_default_sandbox_policy_card()
        result = validate_sandbox_policy_card(card)
        assert result.valid is True, result.errors

    def test_identity_fields(self):
        """Card identity fields are accessible."""
        card = create_default_sandbox_policy_card()
        assert card.policy_card.identity.card_id == "aurel-core-sandbox-policy-v1"
        assert card.policy_card.identity.slug == "aurel-core-sandbox-policy"
        assert card.policy_card.identity.namespace == "aurel_core"
        assert card.policy_card.kind == PolicyCardKind.SANDBOX
        assert card.policy_card.status == PolicyCardStatus.ACTIVE

    def test_version_fields(self):
        """Schema version matches the declared constant."""
        card = create_default_sandbox_policy_card()
        assert card.schema_version == SANDBOX_POLICY_CARD_SCHEMA_VERSION

    def test_canonical_hash_determinism(self):
        """Two construction paths producing the same card yield the same hash."""
        card1 = create_default_sandbox_policy_card()
        card2 = create_default_sandbox_policy_card()
        assert compute_sandbox_policy_card_hash(card1) == compute_sandbox_policy_card_hash(card2)

    def test_canonical_hash_stable(self):
        """Canonical hash is non-empty and deterministic across runs."""
        card = create_default_sandbox_policy_card()
        h = compute_sandbox_policy_card_hash(card)
        assert isinstance(h, str)
        assert len(h) == 64
        assert h == compute_sandbox_policy_card_hash(card)


# ===========================================================================
# 2. Closed-world validation tests
# ===========================================================================


class TestClosedWorldValidation:
    def test_unknown_top_level_field_rejected(self):
        """Unknown top-level keys are rejected (closed-world)."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
            "unknown_field": "nope",
        }
        with pytest.raises(SandboxPolicyCardUnknownFieldError, match="unknown_field"):
            load_sandbox_policy_card_from_dict(data)

    def test_unknown_backend_rejected(self):
        """Unknown backend enum value is rejected via dict loading."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
            "backend_rules": [
                {
                    "rule_id": "test",
                    "allowed_backends": ["invalid_backend"],
                }
            ],
        }
        with pytest.raises(SandboxPolicyCardValidationError, match="invalid_backend"):
            load_sandbox_policy_card_from_dict(data)

    def test_unknown_filesystem_scope_rejected(self):
        """Unknown filesystem scope enum value is rejected."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
            "filesystem_rules": [
                {
                    "rule_id": "test",
                    "scope": "invalid_scope",
                }
            ],
        }
        with pytest.raises(SandboxPolicyCardValidationError, match="invalid_scope"):
            load_sandbox_policy_card_from_dict(data)

    def test_unknown_egress_mode_rejected(self):
        """Unknown egress policy enum value is rejected."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
            "egress_rules": [
                {
                    "rule_id": "test",
                    "egress_policy": "invalid_egress",
                }
            ],
        }
        with pytest.raises(SandboxPolicyCardValidationError, match="invalid_egress"):
            load_sandbox_policy_card_from_dict(data)

    def test_unknown_command_class_rejected(self):
        """Unknown command class enum value is rejected."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
            "command_rules": [
                {
                    "rule_id": "test",
                    "command_class": "invalid_command",
                }
            ],
        }
        with pytest.raises(SandboxPolicyCardValidationError, match="invalid_command"):
            load_sandbox_policy_card_from_dict(data)

    def test_duplicate_rule_ids_rejected(self):
        """Duplicate rule IDs across rules are rejected."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card(),
            schema_version="1.0",
            backend_rules=(
                SandboxBackendRule(rule_id="dup"),
                SandboxBackendRule(rule_id="dup"),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is False
        assert any("dup" in e.message and "DUPLICATE" in e.code for e in result.errors)

    def test_dangerous_metadata_rejected(self):
        """Dangerous metadata keys are rejected."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card(),
            schema_version="1.0",
            metadata={"auto_approve": True},
        )
        result = validate_sandbox_policy_card(card)
        assert not result.valid
        assert any("auto_approve" in e.message for e in result.errors)

    def test_empty_card_valid(self):
        """An empty card with no rules is valid (risk tier mappings optional)."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card(),
            schema_version="1.0",
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is True

    def test_wrong_policy_card_kind_rejected(self):
        """A SandboxPolicyCard with wrong PolicyCard kind is rejected."""
        pc = _make_policy_card()
        wrong_pc = PolicyCard(
            schema_version=pc.schema_version,
            identity=pc.identity,
            kind=PolicyCardKind.RISK_TIER,
            status=pc.status,
            scope=pc.scope,
            description="Wrong kind",
        )
        card = SandboxPolicyCard(
            policy_card=wrong_pc,
            schema_version="1.0",
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is False
        assert any("kind" in e.message for e in result.errors)

    def test_forbidden_top_level_field_rejected(self):
        """Dangerous/forbidden top-level fields are rejected."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
            "unsafe_override": True,
        }
        with pytest.raises(SandboxPolicyCardUnsafeFieldError, match="unsafe_override"):
            load_sandbox_policy_card_from_dict(data)

    def test_contradictory_allow_deny_backend_warns(self):
        """A backend both allowed and denied generates a warning."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card(),
            schema_version="1.0",
            backend_rules=(
                SandboxBackendRule(
                    rule_id="contradiction",
                    allowed_backends=(SandboxBackend.UNSAFE_LOCAL,),
                    denied_backends=(SandboxBackend.UNSAFE_LOCAL,),
                ),
            ),
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R0,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is True
        assert any("CONTRADICTORY" in w.code for w in result.warnings), result.warnings


# ===========================================================================
# 3. Backend policy tests
# ===========================================================================


class TestBackendPolicy:
    def test_unsafe_local_flagged_for_high_risk(self):
        """UNSAFE_LOCAL backend is rejected at risk tier R4."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_backend=SandboxBackend.UNSAFE_LOCAL,
            risk_tier=RiskTier.R4,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.allowed is False
        assert any("UNSAFE_LOCAL" in v.code for v in dec.violations)

    def test_unsafe_local_flagged_for_r5(self):
        """UNSAFE_LOCAL backend is rejected at risk tier R5."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_backend=SandboxBackend.UNSAFE_LOCAL,
            risk_tier=RiskTier.R5,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.allowed is False
        assert any("UNSAFE_LOCAL" in v.code for v in dec.violations)

    def test_unsafe_local_flagged_for_r6(self):
        """UNSAFE_LOCAL backend is rejected at risk tier R6."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_backend=SandboxBackend.UNSAFE_LOCAL,
            risk_tier=RiskTier.R6,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.allowed is False

    def test_docker_accepted_as_isolated_backend(self):
        """DOCKER backend is accepted for R4 (isolated required tier)."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_backend=SandboxBackend.DOCKER,
            risk_tier=RiskTier.R4,
            command_class=CommandClass.READ_ONLY_COMMAND,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.required_backend_minimum is not None

    def test_deny_execution_as_backend(self):
        """DENY_EXECUTION is a valid explicit sandbox posture."""
        assert SandboxBackend.DENY_EXECUTION.value == "deny_execution"
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(risk_tier=RiskTier.R6)
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.required_backend_minimum == SandboxBackend.DENY_EXECUTION
        assert dec.allowed is False

    def test_restricted_local_allowed_for_low_risk(self):
        """RESTRICTED_LOCAL is allowed for R1."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_backend=SandboxBackend.RESTRICTED_LOCAL,
            risk_tier=RiskTier.R1,
            command_class=CommandClass.READ_ONLY_COMMAND,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.allowed is True

    def test_requested_backend_not_in_allowlist_creates_violation(self):
        """A backend not in any allowlist rule generates a violation."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card("strict-backend-test"),
            schema_version="1.0",
            backend_rules=(
                SandboxBackendRule(
                    rule_id="strict",
                    allowed_backends=(SandboxBackend.RESTRICTED_LOCAL,),
                ),
            ),
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R1,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        inp = SandboxPolicyDecisionInput(
            requested_backend=SandboxBackend.DOCKER,
            risk_tier=RiskTier.R1,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert any("NOT_ALLOWLISTED" in v.code for v in dec.violations)


# ===========================================================================
# 4. Filesystem policy tests
# ===========================================================================


class TestFilesystemPolicy:
    def test_no_filesystem_default(self):
        """Default filesystem scope is NO_FILESYSTEM."""
        default_rule = next(
            (r for r in DEFAULT_FILESYSTEM_RULES if r.rule_id == "filesystem-default-deny"),
            None,
        )
        assert default_rule is not None
        assert default_rule.scope == FilesystemScope.NO_FILESYSTEM

    def test_temp_only_is_valid(self):
        """TEMP_ONLY filesystem scope is representable."""
        assert FilesystemScope.TEMP_ONLY.value == "temp_only"

    def test_read_only_project_allowed(self):
        """READ_ONLY_PROJECT scope is allowed and has secrets paths denied."""
        rule = next(
            (r for r in DEFAULT_FILESYSTEM_RULES if r.rule_id == "filesystem-readonly-project"),
            None,
        )
        assert rule is not None
        assert rule.scope == FilesystemScope.READ_ONLY_PROJECT
        assert any(".env" in p for p in rule.denied_paths)

    def test_write_scope_has_denied_paths(self):
        """Write scopes still have secrets paths denied."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card("write-fs-test"),
            schema_version="1.0",
            filesystem_rules=(
                SandboxFilesystemScopeRule(
                    rule_id="write-test",
                    scope=FilesystemScope.READ_WRITE_PROJECT,
                    denied_paths=("/etc/passwd", "secrets/"),
                ),
            ),
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R0,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is True

    def test_secrets_path_denied(self):
        """Paths containing secrets patterns are denied by default."""
        default_deny = next(
            (r for r in DEFAULT_FILESYSTEM_RULES if r.rule_id == "filesystem-default-deny"),
            None,
        )
        assert default_deny is not None
        denied = set(default_deny.denied_paths)
        assert ".env" in denied
        assert "secrets/" in denied
        assert "credentials/" in denied

    def test_suspicious_path_validation(self):
        """A card with suspicious allowed paths generates warnings."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card("suspicious-fs"),
            schema_version="1.0",
            filesystem_rules=(
                SandboxFilesystemScopeRule(
                    rule_id="suspicious",
                    scope=FilesystemScope.READ_WRITE_PROJECT,
                    allowed_paths=("/etc/passwd",),
                ),
            ),
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R0,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is True
        assert any("SUSPICIOUS" in w.code for w in result.warnings)

    def test_absolute_host_path_governed(self):
        """Absolute host paths like /root are denied by default."""
        default_deny = next(
            (r for r in DEFAULT_FILESYSTEM_RULES if r.rule_id == "filesystem-default-deny"),
            None,
        )
        assert default_deny is not None
        assert "/root" in default_deny.denied_paths
        assert "/etc/passwd" in default_deny.denied_paths

    def test_allowlist_scope_works(self):
        """READ_ONLY_ALLOWLIST scope with explicit paths is valid."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card("allowlist-fs"),
            schema_version="1.0",
            filesystem_rules=(
                SandboxFilesystemScopeRule(
                    rule_id="allowlist-test",
                    scope=FilesystemScope.READ_ONLY_ALLOWLIST,
                    allowlist_paths=("/tmp/safe/", "./data/"),
                ),
            ),
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R0,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is True

    def test_deny_host_fs_available(self):
        """DENY_HOST_FS scope is available."""
        assert FilesystemScope.DENY_HOST_FS.value == "deny_host_fs"


# ===========================================================================
# 5. Egress policy tests
# ===========================================================================


class TestEgressPolicy:
    def test_no_egress_default(self):
        """Default egress policy is NO_EGRESS."""
        default_rule = next(
            (r for r in DEFAULT_EGRESS_RULES if r.rule_id == "egress-default-deny"),
            None,
        )
        assert default_rule is not None
        assert default_rule.egress_policy == EgressPolicy.NO_EGRESS

    def test_localhost_only_allowed(self):
        """LOCALHOST_ONLY egress is a valid posture."""
        rule = next(
            (r for r in DEFAULT_EGRESS_RULES if r.rule_id == "egress-localhost-only"),
            None,
        )
        assert rule is not None
        assert rule.egress_policy == EgressPolicy.LOCALHOST_ONLY
        assert "127.0.0.0/8" in rule.allowed_targets

    def test_allowlist_only_valid(self):
        """ALLOWLIST_ONLY egress policy is valid."""
        assert EgressPolicy.ALLOWLIST_ONLY.value == "allowlist_only"

    def test_any_egress_requires_authority_warning(self):
        """ANY_EGRESS generates a warning."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_egress=EgressPolicy.ANY_EGRESS,
            risk_tier=RiskTier.R1,
            command_class=CommandClass.READ_ONLY_COMMAND,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert any("ANY_EGRESS" in w.code for w in dec.warnings)

    def test_network_command_without_egress_creates_violation(self):
        """NETWORK_COMMAND without compatible egress posture creates a violation."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.NETWORK_COMMAND,
            risk_tier=RiskTier.R1,
            requested_egress=EgressPolicy.NO_EGRESS,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.allowed is False
        assert any("NETWORK_COMMAND" in v.code for v in dec.violations)


# ===========================================================================
# 6. Command class policy tests
# ===========================================================================


class TestCommandClassPolicy:
    def test_shell_command_requires_approval(self):
        """SHELL_COMMAND requires approval."""
        shell_rule = next(
            (r for r in DEFAULT_COMMAND_RULES if r.command_class == CommandClass.SHELL_COMMAND),
            None,
        )
        assert shell_rule is not None
        assert shell_rule.decision == SandboxCommandDecision.APPROVAL_REQUIRED

    def test_package_install_requires_approval(self):
        """PACKAGE_INSTALL requires approval."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.PACKAGE_INSTALL),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.APPROVAL_REQUIRED
        assert rule.required_backend == SandboxBackend.DOCKER

    def test_destructive_command_denied(self):
        """DESTRUCTIVE_COMMAND is denied."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.DESTRUCTIVE_COMMAND),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.DENY

    def test_destructive_command_evaluation_denied(self):
        """DESTRUCTIVE_COMMAND evaluation returns allowed=False."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.DESTRUCTIVE_COMMAND,
            risk_tier=RiskTier.R3,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.allowed is False
        assert any("COMMAND_CLASS_DENIED" in v.code for v in dec.violations)

    def test_unknown_command_denied(self):
        """UNKNOWN_COMMAND is denied by default."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.UNKNOWN_COMMAND),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.DENY

    def test_secret_touching_command_denied(self):
        """SECRET_TOUCHING_COMMAND is denied."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.SECRET_TOUCHING_COMMAND),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.DENY

    def test_read_only_command_allowed(self):
        """READ_ONLY_COMMAND is allowed."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.READ_ONLY_COMMAND),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.ALLOW

    def test_write_command_approval_required(self):
        """WRITE_COMMAND requires approval."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.WRITE_COMMAND),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.APPROVAL_REQUIRED

    def test_process_control_requires_sandbox(self):
        """PROCESS_CONTROL requires sandbox (isolated backend)."""
        rule = next(
            (r for r in DEFAULT_COMMAND_RULES
             if r.command_class == CommandClass.PROCESS_CONTROL),
            None,
        )
        assert rule is not None
        assert rule.decision == SandboxCommandDecision.SANDBOX_REQUIRED
        assert rule.required_backend == SandboxBackend.DOCKER


# ===========================================================================
# 7. Decision input/output tests
# ===========================================================================


class TestDecisionInputOutput:
    def test_decision_input_serializes_deterministically(self):
        """Same SandboxPolicyDecisionInput serializes to same JSON twice."""
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.READ_ONLY_COMMAND,
            risk_tier=RiskTier.R1,
            requested_backend=SandboxBackend.RESTRICTED_LOCAL,
            touches_secrets=True,
            runs_shell=True,
        )
        from agentic_runtime.policy_cards.sandbox import _decision_input_to_canonical_dict
        d1 = _decision_input_to_canonical_dict(inp)
        d2 = _decision_input_to_canonical_dict(inp)
        assert d1 == d2
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_same_input_same_violations_order(self):
        """Same decision input on same card produces same violations in same order."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.DESTRUCTIVE_COMMAND,
            risk_tier=RiskTier.R5,
        )
        dec1 = evaluate_sandbox_policy_decision(card, inp)
        dec2 = evaluate_sandbox_policy_decision(card, inp)
        assert len(dec1.violations) == len(dec2.violations)
        for v1, v2 in zip(dec1.violations, dec2.violations):
            assert v1.code == v2.code

    def test_warnings_are_deterministic(self):
        """Same input produces same warnings."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            requested_egress=EgressPolicy.ANY_EGRESS,
            risk_tier=RiskTier.R1,
            command_class=CommandClass.READ_ONLY_COMMAND,
        )
        dec1 = evaluate_sandbox_policy_decision(card, inp)
        dec2 = evaluate_sandbox_policy_decision(card, inp)
        assert [w.code for w in dec1.warnings] == [w.code for w in dec2.warnings]

    def test_allowed_field_is_stable(self):
        """Same input on same card yields same allowed value."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.READ_ONLY_COMMAND,
            risk_tier=RiskTier.R1,
        )
        assert evaluate_sandbox_policy_decision(card, inp).allowed is True
        assert evaluate_sandbox_policy_decision(card, inp).allowed is True

    def test_approval_required_field_is_stable(self):
        """Approval_required field is stable for same input."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.READ_ONLY_COMMAND,
            risk_tier=RiskTier.R1,
        )
        d1 = evaluate_sandbox_policy_decision(card, inp)
        d2 = evaluate_sandbox_policy_decision(card, inp)
        assert d1.approval_required == d2.approval_required

    def test_decision_serialization_deterministic(self):
        """SandboxPolicyDecision serializes deterministically."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(risk_tier=RiskTier.R6)
        dec = evaluate_sandbox_policy_decision(card, inp)
        from agentic_runtime.policy_cards.sandbox import serialize_sandbox_policy_decision_canonical
        s1 = serialize_sandbox_policy_decision_canonical(dec)
        s2 = serialize_sandbox_policy_decision_canonical(dec)
        assert s1 == s2

    def test_sandbox_policy_card_hash_present_in_decision(self):
        """Decision carries the canonical hash of the source card."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(risk_tier=RiskTier.R1)
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert dec.source_card_id == "aurel-core-sandbox-policy-v1"
        assert dec.canonical_hash is not None


# ===========================================================================
# 8. Export tests
# ===========================================================================


class TestExports:
    def test_public_imports_work(self):
        """All major types are importable from the policy_cards package."""
        from agentic_runtime.policy_cards import (
            SandboxPolicyCard,
            SandboxPolicyDecision,
            SandboxPolicyDecisionInput,
            SandboxCommandDecision,
            SandboxBackend,
            SandboxBackendRule,
            SandboxCommandClassRule,
            SandboxEgressRule,
            SandboxFilesystemScopeRule,
            RiskTierSandboxMapping,
            SandboxPolicyViolation,
            SandboxPolicyWarning,
            evaluate_sandbox_policy_decision,
            create_default_sandbox_policy_card,
            validate_sandbox_policy_card,
            load_sandbox_policy_card_from_dict,
            compute_sandbox_policy_card_hash,
            serialize_sandbox_policy_card_canonical,
        )
        assert True

    def test_schema_imports_work(self):
        """Schema module exports are importable."""
        schema = get_sandbox_policy_schema()
        assert isinstance(schema, dict)
        assert "schema_version" in schema
        assert "required_fields" in schema

    def test_error_imports_work(self):
        """Sandbox error classes are importable."""
        from agentic_runtime.policy_cards.errors import (
            SandboxPolicyCardError,
            SandboxPolicyCardValidationError,
            SandboxPolicyCardSerializationError,
            SandboxPolicyCardHashError,
            SandboxPolicyCardUnknownFieldError,
            SandboxPolicyCardUnsafeFieldError,
            SandboxPolicyCardDecisionError,
            SandboxPolicyCardSchemaError,
        )
        assert issubclass(SandboxPolicyCardValidationError, SandboxPolicyCardError)
        assert issubclass(SandboxPolicyCardDecisionError, SandboxPolicyCardError)
        assert issubclass(SandboxPolicyCardSchemaError, SandboxPolicyCardError)

    def test_enum_values_exported(self):
        """All enum values are accessible."""
        assert len(CommandClass) == 9
        assert len(SandboxBackend) == 5
        assert len(FilesystemScope) == 7
        assert len(EgressPolicy) == 6
        assert len(ApprovalRequirement) == 7
        assert len(SandboxCommandDecision) == 7


# ===========================================================================
# 9. Cross-family consistency tests
# ===========================================================================


class TestCrossFamilyConsistency:
    def test_sandbox_card_follows_same_identity_conventions(self):
        """SandboxPolicyCard uses the same embedded PolicyCard pattern."""
        card = create_default_sandbox_policy_card()
        assert card.policy_card.schema_version == "1.0"
        assert isinstance(card.policy_card.identity, PolicyCardIdentity)
        assert card.policy_card.kind == PolicyCardKind.SANDBOX

    def test_sandbox_card_hash_follows_sha256_pattern(self):
        """Hash is 64-char hex (SHA-256)."""
        card = create_default_sandbox_policy_card()
        h = compute_sandbox_policy_card_hash(card)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_sandbox_schema_follows_export_pattern(self):
        """Schema export follows the established pattern."""
        schema = export_sandbox_policy_schema()
        assert "schema_version" in schema
        assert "supported_versions" in schema
        assert "required_fields" in schema
        assert "dangerous_field_names" in schema
        assert "dangerous_metadata_keys" in schema
        assert "canonical_fields" in schema
        assert "default_backend_rules" in schema
        assert "default_command_rules" in schema

    def test_no_runtime_enforcement(self):
        """evaluate_sandbox_policy_decision returns a decision, does NOT block."""
        card = create_default_sandbox_policy_card()
        inp = SandboxPolicyDecisionInput(
            command_class=CommandClass.SHELL_COMMAND,
            risk_tier=RiskTier.R1,
        )
        dec = evaluate_sandbox_policy_decision(card, inp)
        assert isinstance(dec, SandboxPolicyDecision)
        assert isinstance(dec.allowed, bool)

    def test_canonical_serialization_roundtrip(self):
        """Card -> canonical dict -> JSON -> re-hash is stable."""
        card = create_default_sandbox_policy_card()
        canonical_dict = sandbox_policy_card_to_canonical_dict(card)
        serialized = serialize_sandbox_policy_card_canonical(card)
        parsed = json.loads(serialized)
        assert json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")) == serialized
        assert canonical_dict == parsed

    def test_schema_version_validation(self):
        """Schema version validation works correctly."""
        result = validate_sandbox_policy_schema_version("1.0")
        assert result.valid is True
        result2 = validate_sandbox_policy_schema_version("2.0")
        assert result2.valid is False
        result3 = validate_sandbox_policy_schema_version("")
        assert result3.valid is False
        assert is_supported_sandbox_policy_schema_version("1.0") is True
        assert is_supported_sandbox_policy_schema_version("2.0") is False

    def test_dict_validation_returns_structured_result(self):
        """validate_sandbox_policy_card_dict returns a structured result."""
        data = {
            "policy_card": _make_policy_card_dict(),
            "schema_version": "1.0",
        }
        result = validate_sandbox_policy_card_dict(data)
        assert isinstance(result, SandboxValidationResult)
        assert result.valid is True
        assert result.card_id == "test-sandbox-policy-v1"

    def test_invalid_dict_returns_failure_result(self):
        """Invalid dict data returns a non-throwing validation result."""
        result = validate_sandbox_policy_card_dict({"bad": "data"})
        assert isinstance(result, SandboxValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_approval_policy_requirements_all_defined(self):
        """All approval requirement flags are defined in the default card."""
        card = create_default_sandbox_policy_card()
        assert len(card.approval_policy) == 7
        required = {a.value for a in ApprovalRequirement}
        present = {a.value for a in card.approval_policy}
        assert required == present


# ===========================================================================
# 10. Risk tier mapping tests
# ===========================================================================


class TestRiskTierMappings:
    def test_all_r0_to_r6_mapped(self):
        """All required risk tiers R0-R6 have sandbox mappings."""
        card = create_default_sandbox_policy_card()
        mapped_tiers = {m.risk_tier for m in card.risk_tier_mappings}
        assert RiskTier.R0 in mapped_tiers
        assert RiskTier.R1 in mapped_tiers
        assert RiskTier.R2 in mapped_tiers
        assert RiskTier.R3 in mapped_tiers
        assert RiskTier.R4 in mapped_tiers
        assert RiskTier.R5 in mapped_tiers
        assert RiskTier.R6 in mapped_tiers

    def test_r4_requires_isolated_and_approval(self):
        """R4 mapping requires approval and isolated backend."""
        card = create_default_sandbox_policy_card()
        mapping = next(m for m in card.risk_tier_mappings if m.risk_tier == RiskTier.R4)
        assert mapping.requires_approval is True
        assert mapping.requires_isolated_backend is True
        assert mapping.minimum_backend == SandboxBackend.DOCKER

    def test_r5_requires_approval_and_isolated(self):
        """R5 mapping requires approval and isolated backend."""
        card = create_default_sandbox_policy_card()
        mapping = next(m for m in card.risk_tier_mappings if m.risk_tier == RiskTier.R5)
        assert mapping.requires_approval is True
        assert mapping.requires_isolated_backend is True

    def test_r6_denies_execution(self):
        """R6 mapping sets backend to DENY_EXECUTION."""
        card = create_default_sandbox_policy_card()
        mapping = next(m for m in card.risk_tier_mappings if m.risk_tier == RiskTier.R6)
        assert mapping.minimum_backend == SandboxBackend.DENY_EXECUTION
        assert mapping.minimum_filesystem_scope == FilesystemScope.NO_FILESYSTEM
        assert mapping.minimum_egress_policy == EgressPolicy.DENY_NETWORK

    def test_r0_r1_r2_dont_require_approval(self):
        """R0, R1, R2 do not require approval by default."""
        card = create_default_sandbox_policy_card()
        for tier in (RiskTier.R0, RiskTier.R1, RiskTier.R2):
            mapping = next(m for m in card.risk_tier_mappings if m.risk_tier == tier)
            assert mapping.requires_approval is False, f"{tier} should not require approval"

    def test_missing_risk_tier_mapping_errors(self):
        """A card with incomplete risk tier mappings fails validation."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card("missing-mappings"),
            schema_version="1.0",
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R0,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R2,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert result.valid is False
        assert any("MISSING_REQUIRED_TIER" in e.code for e in result.errors)

    def test_duplicate_tier_mapping_errors(self):
        """Duplicate risk tier mappings fail validation."""
        card = SandboxPolicyCard(
            policy_card=_make_policy_card("dup-tiers"),
            schema_version="1.0",
            risk_tier_mappings=(
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R1,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
                RiskTierSandboxMapping(
                    risk_tier=RiskTier.R1,
                    minimum_backend=SandboxBackend.RESTRICTED_LOCAL,
                ),
            ),
        )
        result = validate_sandbox_policy_card(card)
        assert "DUPLICATE" in str([e.code for e in result.errors])
