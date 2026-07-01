"""P1.ENF-D1 Identity Kernel invariant enforcement for runtime submit/preflight."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .governance_enforcement import GovernanceEnforcementMode
from .identity_kernel_invariants import (
    SELECTED_INVARIANT_IDS,
    discover_identity_kernel_invariants,
)
from .identity_submit_context import (
    IdentitySubmitContext,
    IdentitySubmitContextLoader,
    IdentitySubmitContextStatus,
    IdentitySubmitPreflightResult,
    evaluate_identity_submit_preflight,
)

IDENTITY_INVARIANT_SIGNALS_KEY = "_identity_invariant_signals"


class IdentityInvariantDecision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class IdentityInvariantSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class IdentityInvariantUnavailableReason(str, Enum):
    DISABLED_MODE = "disabled_mode"
    DISCOVERY_MISSING = "discovery_missing"
    NOT_SELECTED = "not_selected"


@dataclass(frozen=True)
class IdentityInvariantViolation:
    invariant_id: str
    key: str
    truth_label: str
    message: str
    severity: IdentityInvariantSeverity
    evidence_refs: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_refs": sorted(self.evidence_refs),
            "invariant_id": self.invariant_id,
            "key": self.key,
            "message": self.message,
            "severity": self.severity.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class IdentityInvariantCheckInput:
    identity_context_present: bool = False
    operator_authority_present: bool = False
    canon_authority_present: bool = False
    require_identity_context: bool = False
    claims_operator_authority: bool = False
    claims_canon_override: bool = False
    silent_identity_mutation: bool = False
    self_authority_escalation: bool = False
    policy_bypass_self_grant: bool = False
    untrusted_identity_modification: bool = False

    @classmethod
    def from_submit_metadata(
        cls,
        metadata: Mapping[str, Any] | None,
        *,
        identity_context: IdentitySubmitContext | None,
        require_identity_context: bool,
    ) -> IdentityInvariantCheckInput:
        signals = _extract_signals(metadata)
        context_present = identity_context is not None
        return cls(
            identity_context_present=context_present,
            operator_authority_present=context_present
            and bool(getattr(identity_context, "operator_contract_hash", "")),
            canon_authority_present=context_present
            and bool(getattr(identity_context, "identity_kernel_hash", "")),
            require_identity_context=require_identity_context,
            claims_operator_authority=bool(signals.get("claims_operator_authority")),
            claims_canon_override=bool(signals.get("claims_canon_override")),
            silent_identity_mutation=bool(signals.get("silent_identity_mutation")),
            self_authority_escalation=bool(signals.get("self_authority_escalation")),
            policy_bypass_self_grant=bool(signals.get("policy_bypass_self_grant")),
            untrusted_identity_modification=bool(
                signals.get("untrusted_identity_modification")
            ),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "canon_authority_present": self.canon_authority_present,
            "claims_canon_override": self.claims_canon_override,
            "claims_operator_authority": self.claims_operator_authority,
            "identity_context_present": self.identity_context_present,
            "operator_authority_present": self.operator_authority_present,
            "policy_bypass_self_grant": self.policy_bypass_self_grant,
            "require_identity_context": self.require_identity_context,
            "self_authority_escalation": self.self_authority_escalation,
            "silent_identity_mutation": self.silent_identity_mutation,
            "untrusted_identity_modification": self.untrusted_identity_modification,
        }


@dataclass(frozen=True)
class IdentityInvariantEnforcementArtifact:
    mode: GovernanceEnforcementMode
    decision: IdentityInvariantDecision
    enforced: bool
    submit_blocked: bool
    truth_label: str
    identity_context_present: bool
    operator_authority_present: bool
    canon_authority_present: bool
    violations: tuple[IdentityInvariantViolation, ...] = ()
    warnings: tuple[IdentityInvariantViolation, ...] = ()
    unavailable_reasons: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    selected_invariant_ids: tuple[str, ...] = SELECTED_INVARIANT_IDS

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "canon_authority_present": self.canon_authority_present,
            "decision": self.decision.value,
            "enforced": self.enforced,
            "evidence_refs": sorted(self.evidence_refs),
            "identity_context_present": self.identity_context_present,
            "mode": self.mode.value,
            "operator_authority_present": self.operator_authority_present,
            "reason_codes": sorted(self.reason_codes),
            "selected_invariant_ids": list(self.selected_invariant_ids),
            "submit_blocked": self.submit_blocked,
            "truth_label": self.truth_label,
            "unavailable_reasons": sorted(self.unavailable_reasons),
            "violations": [item.to_canonical_dict() for item in self.violations],
            "warnings": [item.to_canonical_dict() for item in self.warnings],
        }

    @property
    def artifact_hash(self) -> str:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IdentityInvariantEnforcementResult:
    decision: IdentityInvariantDecision
    should_block: bool
    artifact: IdentityInvariantEnforcementArtifact

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact.to_canonical_dict(),
            "artifact_hash": self.artifact.artifact_hash,
            "decision": self.decision.value,
            "should_block": self.should_block,
        }


@dataclass(frozen=True)
class IdentitySubmitWithInvariantResult:
    preflight: IdentitySubmitPreflightResult
    invariant_enforcement: IdentityInvariantEnforcementResult
    should_block: bool

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "invariant_enforcement": self.invariant_enforcement.to_canonical_dict(),
            "preflight": self.preflight.to_canonical_dict(),
            "should_block": self.should_block,
        }


def evaluate_identity_invariant_enforcement(
    *,
    mode: GovernanceEnforcementMode,
    check_input: IdentityInvariantCheckInput,
) -> IdentityInvariantEnforcementResult:
    if mode is GovernanceEnforcementMode.DISABLED_UNAVAILABLE:
        artifact = _artifact(
            mode=mode,
            decision=IdentityInvariantDecision.UNAVAILABLE,
            enforced=False,
            submit_blocked=False,
            truth_label="IDENTITY_INVARIANT_UNAVAILABLE",
            check_input=check_input,
            unavailable_reasons=(IdentityInvariantUnavailableReason.DISABLED_MODE.value,),
            reason_codes=("IDENTITY_INVARIANT_ENFORCEMENT_DISABLED",),
            evidence_refs=("config/aurel/identity_kernel.yaml",),
        )
        return IdentityInvariantEnforcementResult(
            decision=IdentityInvariantDecision.UNAVAILABLE,
            should_block=False,
            artifact=artifact,
        )

    violations, warnings = _evaluate_selected_invariants(check_input)
    if (
        check_input.require_identity_context
        and not check_input.identity_context_present
    ):
        violations = violations + (
            IdentityInvariantViolation(
                invariant_id="IK-CONTEXT",
                key="identity_context_required",
                truth_label="IDENTITY_CONTEXT_REQUIRED",
                message="Required identity submit context is missing.",
                severity=IdentityInvariantSeverity.CRITICAL,
                evidence_refs=("identity_submit_context.py",),
            ),
        )

    if mode is GovernanceEnforcementMode.SHADOW_ONLY:
        return _finalize(
            mode=mode,
            violations=violations,
            warnings=warnings,
            check_input=check_input,
            block_on_critical=False,
            warn_only=False,
            record_only=True,
            truth_label="IDENTITY_INVARIANT_ENFORCED",
        )

    if mode is GovernanceEnforcementMode.ADVISORY:
        advisory_warnings = warnings + violations
        return _finalize(
            mode=mode,
            violations=(),
            warnings=advisory_warnings,
            check_input=check_input,
            block_on_critical=False,
            warn_only=True,
            truth_label=(
                "IDENTITY_INVARIANT_WARNED"
                if advisory_warnings
                else "IDENTITY_INVARIANT_ENFORCED"
            ),
        )

    return _finalize(
        mode=mode,
        violations=violations,
        warnings=warnings,
        check_input=check_input,
        block_on_critical=True,
        warn_only=False,
        truth_label=(
            "IDENTITY_INVARIANT_ENFORCED"
            if not violations
            else "BLOCKED_IDENTITY_BYPASS_RISK"
        ),
    )


def evaluate_identity_submit_with_invariants(
    *,
    mode: GovernanceEnforcementMode,
    require_identity_context: bool,
    loader: IdentitySubmitContextLoader | None,
    submit_metadata: Mapping[str, Any] | None = None,
) -> IdentitySubmitWithInvariantResult:
    preflight = evaluate_identity_submit_preflight(
        mode=mode,
        require_identity_context=require_identity_context,
        loader=loader,
    )
    check_input = IdentityInvariantCheckInput.from_submit_metadata(
        submit_metadata,
        identity_context=preflight.context,
        require_identity_context=require_identity_context,
    )
    invariant_result = evaluate_identity_invariant_enforcement(
        mode=mode,
        check_input=check_input,
    )
    should_block = preflight.should_block or invariant_result.should_block
    return IdentitySubmitWithInvariantResult(
        preflight=preflight,
        invariant_enforcement=invariant_result,
        should_block=should_block,
    )


def identity_invariant_enforcement_to_artifact(
    result: IdentityInvariantEnforcementResult,
) -> dict[str, Any]:
    return result.to_canonical_dict()


def identity_submit_with_invariants_to_artifact(
    result: IdentitySubmitWithInvariantResult,
) -> dict[str, Any]:
    return result.to_canonical_dict()


def _evaluate_selected_invariants(
    check_input: IdentityInvariantCheckInput,
) -> tuple[tuple[IdentityInvariantViolation, ...], tuple[IdentityInvariantViolation, ...]]:
    violations: list[IdentityInvariantViolation] = []
    warnings: list[IdentityInvariantViolation] = []

    if check_input.self_authority_escalation:
        violations.append(
            _violation(
                "IK-002",
                "self_escalation_allowed",
                "OPERATOR_AUTHORITY_REQUIRED",
                "Submit attempted self-authority escalation.",
            )
        )
    if check_input.policy_bypass_self_grant:
        violations.append(
            _violation(
                "IK-005",
                "policy_bypass_self_grant_allowed",
                "CANON_AUTHORITY_REQUIRED",
                "Submit attempted self-granted policy bypass.",
            )
        )
    if check_input.untrusted_identity_modification or check_input.silent_identity_mutation:
        violations.append(
            _violation(
                "IK-006",
                "untrusted_input_can_modify_identity",
                "BLOCKED_IDENTITY_BYPASS_RISK",
                "Submit attempted untrusted or silent identity/canon mutation.",
            )
        )
    if check_input.claims_operator_authority and not check_input.operator_authority_present:
        violations.append(
            _violation(
                "IK-007",
                "operator_replacement",
                "OPERATOR_AUTHORITY_REQUIRED",
                "Submit claimed operator authority without bound operator context.",
            )
        )
    if check_input.claims_canon_override and not check_input.canon_authority_present:
        violations.append(
            _violation(
                "IK-007",
                "operator_replacement",
                "CANON_AUTHORITY_REQUIRED",
                "Submit attempted canon override without bound identity kernel context.",
            )
        )

    return tuple(violations), tuple(warnings)


def _violation(
    invariant_id: str,
    key: str,
    truth_label: str,
    message: str,
) -> IdentityInvariantViolation:
    return IdentityInvariantViolation(
        invariant_id=invariant_id,
        key=key,
        truth_label=truth_label,
        message=message,
        severity=IdentityInvariantSeverity.CRITICAL,
        evidence_refs=(
            "config/aurel/identity_kernel.yaml",
            f"identity_kernel.invariants.{invariant_id}",
        ),
    )


def _finalize(
    *,
    mode: GovernanceEnforcementMode,
    violations: tuple[IdentityInvariantViolation, ...],
    warnings: tuple[IdentityInvariantViolation, ...],
    check_input: IdentityInvariantCheckInput,
    block_on_critical: bool,
    warn_only: bool,
    truth_label: str,
    record_only: bool = False,
) -> IdentityInvariantEnforcementResult:
    has_critical = bool(violations)
    should_block = block_on_critical and has_critical
    if record_only:
        artifact = _artifact(
            mode=mode,
            decision=IdentityInvariantDecision.ALLOW,
            enforced=False,
            submit_blocked=False,
            truth_label=truth_label,
            check_input=check_input,
            violations=violations,
            warnings=warnings,
            reason_codes=("IDENTITY_INVARIANT_SHADOW_RECORDED",),
        )
        return IdentityInvariantEnforcementResult(
            decision=IdentityInvariantDecision.ALLOW,
            should_block=False,
            artifact=artifact,
        )
    if warn_only and (violations or warnings):
        decision = IdentityInvariantDecision.WARN
        enforced = False
        all_warnings = violations + warnings
        reason_codes = tuple(
            sorted({item.truth_label for item in all_warnings})
        ) or ("IDENTITY_INVARIANT_ADVISORY",)
        artifact = _artifact(
            mode=mode,
            decision=decision,
            enforced=False,
            submit_blocked=False,
            truth_label=truth_label,
            check_input=check_input,
            violations=(),
            warnings=all_warnings,
            reason_codes=reason_codes,
        )
        return IdentityInvariantEnforcementResult(
            decision=decision,
            should_block=False,
            artifact=artifact,
        )

    if has_critical and should_block:
        decision = IdentityInvariantDecision.DENY
        enforced = True
    elif has_critical:
        decision = IdentityInvariantDecision.WARN if warn_only else IdentityInvariantDecision.DENY
        enforced = should_block
    else:
        decision = IdentityInvariantDecision.ALLOW
        enforced = False

    if decision is IdentityInvariantDecision.ALLOW:
        final_reason_codes: tuple[str, ...] = ("IDENTITY_INVARIANT_CHECKS_PASSED",)
    elif decision is IdentityInvariantDecision.DENY:
        final_reason_codes = tuple(sorted({item.truth_label for item in violations}))
    else:
        final_reason_codes = tuple(sorted({item.truth_label for item in warnings}))

    artifact = _artifact(
        mode=mode,
        decision=decision,
        enforced=enforced,
        submit_blocked=should_block,
        truth_label=truth_label,
        check_input=check_input,
        violations=violations,
        warnings=warnings,
        reason_codes=final_reason_codes,
    )
    return IdentityInvariantEnforcementResult(
        decision=decision,
        should_block=should_block,
        artifact=artifact,
    )


def _artifact(
    *,
    mode: GovernanceEnforcementMode,
    decision: IdentityInvariantDecision,
    enforced: bool,
    submit_blocked: bool,
    truth_label: str,
    check_input: IdentityInvariantCheckInput,
    violations: tuple[IdentityInvariantViolation, ...] = (),
    warnings: tuple[IdentityInvariantViolation, ...] = (),
    unavailable_reasons: tuple[str, ...] = (),
    reason_codes: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
) -> IdentityInvariantEnforcementArtifact:
    refs = evidence_refs or (
        "config/aurel/identity_kernel.yaml",
        "identity_kernel_invariants.py",
        "identity_invariant_enforcement.py",
    )
    return IdentityInvariantEnforcementArtifact(
        mode=mode,
        decision=decision,
        enforced=enforced,
        submit_blocked=submit_blocked,
        truth_label=truth_label,
        identity_context_present=check_input.identity_context_present,
        operator_authority_present=check_input.operator_authority_present,
        canon_authority_present=check_input.canon_authority_present,
        violations=violations,
        warnings=warnings,
        unavailable_reasons=unavailable_reasons,
        reason_codes=reason_codes,
        evidence_refs=refs,
    )


def _extract_signals(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if metadata is None:
        return {}
    signals = metadata.get(IDENTITY_INVARIANT_SIGNALS_KEY)
    if isinstance(signals, dict):
        return signals
    args = metadata.get("args")
    if isinstance(args, dict):
        nested = args.get(IDENTITY_INVARIANT_SIGNALS_KEY)
        if isinstance(nested, dict):
            return nested
    return {}
