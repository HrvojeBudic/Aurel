"""P1.ENF-E sandbox backend requirement gate for runtime submit/preflight."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .governance_enforcement import GovernanceEnforcementMode
from .sandbox import SandboxBackend
from .sandbox_safety import (
    SAFE_VERIFIED_PROOF_REFS,
    SandboxBackendCapability,
    SandboxSafetyClass,
    classify_sandbox_backend,
    safety_class_allows_live_claim,
)

SANDBOX_BACKEND_SIGNALS_KEY = "_sandbox_backend_signals"


class SandboxBackendGateMode(str, Enum):
    DEV_ALLOW_UNSAFE = "dev_allow_unsafe"
    REQUIRE_RESTRICTED_OR_SAFE = "require_restricted_or_safe"
    REQUIRE_SAFE_VERIFIED = "require_safe_verified"
    DISABLED_UNAVAILABLE = "disabled_unavailable"


class SandboxBackendDecision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class SandboxBackendUnavailableReason(str, Enum):
    DISABLED_MODE = "disabled_mode"
    SAFE_VERIFIED_NOT_PROVEN = "safe_verified_not_proven"
    SAFE_BACKEND_REQUIRED = "safe_backend_required"
    RESTRICTED_BACKEND_REQUIRED = "restricted_backend_required"
    LIVE_CLAIM_WITH_UNSAFE_BACKEND = "live_claim_with_unsafe_backend"
    TRACE_VERIFIED_CLAIM_WITH_UNSAFE_BACKEND = "trace_verified_claim_with_unsafe_backend"


@dataclass(frozen=True)
class SandboxBackendRequirement:
    gate_mode: SandboxBackendGateMode
    require_safe_verified: bool = False
    require_restricted_or_safe: bool = False
    allow_unsafe_dev: bool = True
    claims_live_execution: bool = False
    claims_trace_verified: bool = False
    claims_safe_sandbox: bool = False
    dev_fixture_backend: bool = False

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "allow_unsafe_dev": self.allow_unsafe_dev,
            "claims_live_execution": self.claims_live_execution,
            "claims_safe_sandbox": self.claims_safe_sandbox,
            "claims_trace_verified": self.claims_trace_verified,
            "dev_fixture_backend": self.dev_fixture_backend,
            "gate_mode": self.gate_mode.value,
            "require_restricted_or_safe": self.require_restricted_or_safe,
            "require_safe_verified": self.require_safe_verified,
        }


@dataclass(frozen=True)
class SandboxBackendViolation:
    key: str
    truth_label: str
    message: str
    safety_class: SandboxSafetyClass
    evidence_refs: tuple[str, ...] = ()

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_refs": sorted(self.evidence_refs),
            "key": self.key,
            "message": self.message,
            "safety_class": self.safety_class.value,
            "truth_label": self.truth_label,
        }


@dataclass(frozen=True)
class SandboxBackendGateArtifact:
    mode: GovernanceEnforcementMode
    requirement: SandboxBackendRequirement
    capability: SandboxBackendCapability
    decision: SandboxBackendDecision
    enforced: bool
    submit_blocked: bool
    truth_label: str
    sandbox_backend_kind: str
    sandbox_safety_class: str
    sandbox_gate_decision: str
    sandbox_unavailable_reason: str = ""
    unsafe_backend_allowed_reason: str = ""
    safe_backend_proof_ref: str = ""
    violations: tuple[SandboxBackendViolation, ...] = ()
    warnings: tuple[SandboxBackendViolation, ...] = ()
    unavailable_reasons: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = field(
        default_factory=lambda: ("src/agentic_runtime/sandbox.py",)
    )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability.to_canonical_dict(),
            "decision": self.decision.value,
            "enforced": self.enforced,
            "evidence_refs": sorted(self.evidence_refs),
            "mode": self.mode.value,
            "reason_codes": sorted(self.reason_codes),
            "requirement": self.requirement.to_canonical_dict(),
            "safe_backend_proof_ref": self.safe_backend_proof_ref,
            "sandbox_backend_kind": self.sandbox_backend_kind,
            "sandbox_gate_decision": self.sandbox_gate_decision,
            "sandbox_safety_class": self.sandbox_safety_class,
            "sandbox_unavailable_reason": self.sandbox_unavailable_reason,
            "submit_blocked": self.submit_blocked,
            "truth_label": self.truth_label,
            "unavailable_reasons": sorted(self.unavailable_reasons),
            "unsafe_backend_allowed_reason": self.unsafe_backend_allowed_reason,
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
class SandboxBackendGateResult:
    decision: SandboxBackendDecision
    should_block: bool
    artifact: SandboxBackendGateArtifact

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact.to_canonical_dict(),
            "artifact_hash": self.artifact.artifact_hash,
            "decision": self.decision.value,
            "should_block": self.should_block,
        }


@dataclass(frozen=True)
class P1ENFESideEffectProof:
    full_sandbox_platform_created: bool = False
    container_runtime_created: bool = False
    firecracker_created: bool = False
    fake_safe_verified_claimed: bool = False
    fake_live_sandbox_claimed: bool = False
    p2_9_b_implemented: bool = False
    shell_command_router_created: bool = False

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "container_runtime_created": self.container_runtime_created,
            "fake_live_sandbox_claimed": self.fake_live_sandbox_claimed,
            "fake_safe_verified_claimed": self.fake_safe_verified_claimed,
            "firecracker_created": self.firecracker_created,
            "full_sandbox_platform_created": self.full_sandbox_platform_created,
            "p2_9_b_implemented": self.p2_9_b_implemented,
            "shell_command_router_created": self.shell_command_router_created,
        }


def sandbox_backend_requirement_from_config(
    *,
    mode: GovernanceEnforcementMode,
    require_safe_sandbox_backend: bool,
    gate_mode: SandboxBackendGateMode | None,
    submit_metadata: Mapping[str, Any] | None,
) -> SandboxBackendRequirement:
    signals = _extract_signals(submit_metadata)
    explicit_gate = gate_mode
    if explicit_gate is None:
        if require_safe_sandbox_backend:
            explicit_gate = SandboxBackendGateMode.REQUIRE_RESTRICTED_OR_SAFE
        elif mode is GovernanceEnforcementMode.DISABLED_UNAVAILABLE:
            explicit_gate = SandboxBackendGateMode.DISABLED_UNAVAILABLE
        else:
            explicit_gate = SandboxBackendGateMode.DEV_ALLOW_UNSAFE

    if bool(signals.get("require_safe_verified")):
        explicit_gate = SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED
    elif bool(signals.get("require_restricted_or_safe")):
        explicit_gate = SandboxBackendGateMode.REQUIRE_RESTRICTED_OR_SAFE

    return SandboxBackendRequirement(
        gate_mode=explicit_gate,
        require_safe_verified=(
            explicit_gate is SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED
        ),
        require_restricted_or_safe=(
            explicit_gate is SandboxBackendGateMode.REQUIRE_RESTRICTED_OR_SAFE
        ),
        allow_unsafe_dev=explicit_gate is SandboxBackendGateMode.DEV_ALLOW_UNSAFE,
        claims_live_execution=bool(signals.get("claims_live_execution")),
        claims_trace_verified=bool(signals.get("claims_trace_verified")),
        claims_safe_sandbox=bool(signals.get("claims_safe_sandbox")),
        dev_fixture_backend=bool(signals.get("dev_fixture_backend")),
    )


def evaluate_sandbox_backend_gate(
    *,
    mode: GovernanceEnforcementMode,
    backend: SandboxBackend,
    requirement: SandboxBackendRequirement,
) -> SandboxBackendGateResult:
    capability = classify_sandbox_backend(
        backend,
        dev_fixture=requirement.dev_fixture_backend,
    )
    safety = capability.safety_class

    if requirement.gate_mode is SandboxBackendGateMode.DISABLED_UNAVAILABLE:
        return _result(
            mode=mode,
            requirement=requirement,
            capability=capability,
            decision=SandboxBackendDecision.UNAVAILABLE,
            should_block=False,
            truth_label="SANDBOX_BACKEND_UNAVAILABLE",
            unavailable_reasons=(SandboxBackendUnavailableReason.DISABLED_MODE.value,),
            reason_codes=("SANDBOX_BACKEND_GATE_DISABLED",),
        )

    violations: list[SandboxBackendViolation] = []
    warnings: list[SandboxBackendViolation] = []

    if requirement.claims_live_execution and not safety_class_allows_live_claim(
        safety
    ):
        violations.append(
            _violation(
                key="live_claim_denied",
                truth_label="BLOCKED_UNSAFE_SANDBOX_PROMOTION",
                message="LIVE execution claim denied for non-SAFE_VERIFIED sandbox backend.",
                safety_class=safety,
            )
        )

    if requirement.claims_trace_verified and safety is not SandboxSafetyClass.SAFE_VERIFIED:
        violations.append(
            _violation(
                key="trace_verified_claim_denied",
                truth_label="BLOCKED_UNSAFE_SANDBOX_PROMOTION",
                message="TRACE_VERIFIED claim denied for sandbox backend without proof.",
                safety_class=safety,
            )
        )

    if requirement.claims_safe_sandbox and safety is not SandboxSafetyClass.SAFE_VERIFIED:
        violations.append(
            _violation(
                key="safe_sandbox_claim_denied",
                truth_label="BLOCKED_UNSAFE_SANDBOX_PROMOTION",
                message="Safe sandbox claim denied without SAFE_VERIFIED proof.",
                safety_class=safety,
            )
        )

    if requirement.gate_mode is SandboxBackendGateMode.REQUIRE_SAFE_VERIFIED:
        if not SAFE_VERIFIED_PROOF_REFS:
            return _result(
                mode=mode,
                requirement=requirement,
                capability=capability,
                decision=SandboxBackendDecision.UNAVAILABLE,
                should_block=mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
                truth_label="SANDBOX_BACKEND_UNAVAILABLE",
                unavailable_reasons=(
                    SandboxBackendUnavailableReason.SAFE_VERIFIED_NOT_PROVEN.value,
                ),
                reason_codes=("SAFE_VERIFIED_UNAVAILABLE",),
                violations=tuple(violations),
            )
        if safety is not SandboxSafetyClass.SAFE_VERIFIED:
            violations.append(
                _violation(
                    key="safe_verified_required",
                    truth_label="BLOCKED_UNSAFE_SANDBOX_PROMOTION",
                    message="SAFE_VERIFIED backend required but backend is not verified.",
                    safety_class=safety,
                )
            )

    if requirement.gate_mode is SandboxBackendGateMode.REQUIRE_RESTRICTED_OR_SAFE:
        if safety in {
            SandboxSafetyClass.UNSAFE_LOCAL,
            SandboxSafetyClass.DEV_FIXTURE,
        }:
            violations.append(
                _violation(
                    key="restricted_or_safe_required",
                    truth_label="BLOCKED_UNSAFE_SANDBOX_PROMOTION",
                    message=(
                        "Restricted or safe sandbox backend required; "
                        f"got {safety.value}."
                    ),
                    safety_class=safety,
                    evidence_refs=("src/agentic_runtime/sandbox.py",),
                )
            )

    if safety is SandboxSafetyClass.UNSAFE_LOCAL:
        from .sandbox import UnsafeLocalSandbox

        warnings.append(
            _violation(
                key="unsafe_local_truth",
                truth_label="SANDBOX_BACKEND_GATED",
                message=UnsafeLocalSandbox.UNSAFE_WARNING,
                safety_class=safety,
            )
        )

    if safety is SandboxSafetyClass.DEV_FIXTURE:
        warnings.append(
            _violation(
                key="dev_fixture_truth",
                truth_label="SANDBOX_BACKEND_GATED",
                message="DEV_FIXTURE sandbox backend is not LIVE.",
                safety_class=safety,
            )
        )

    if violations:
        return _finalize_with_violations(
            mode=mode,
            requirement=requirement,
            capability=capability,
            violations=tuple(violations),
            warnings=tuple(warnings),
        )

    unsafe_reason = ""
    if safety in {SandboxSafetyClass.UNSAFE_LOCAL, SandboxSafetyClass.DEV_FIXTURE}:
        unsafe_reason = "explicit_dev_allow_unsafe_gate"

    if mode is GovernanceEnforcementMode.SHADOW_ONLY:
        return _result(
            mode=mode,
            requirement=requirement,
            capability=capability,
            decision=SandboxBackendDecision.ALLOW,
            should_block=False,
            truth_label="SANDBOX_BACKEND_GATED",
            warnings=tuple(warnings),
            unsafe_backend_allowed_reason=unsafe_reason,
        )

    if mode is GovernanceEnforcementMode.ADVISORY:
        decision = SandboxBackendDecision.WARN if warnings else SandboxBackendDecision.ALLOW
        return _result(
            mode=mode,
            requirement=requirement,
            capability=capability,
            decision=decision,
            should_block=False,
            truth_label="SANDBOX_BACKEND_GATED",
            warnings=tuple(warnings),
            unsafe_backend_allowed_reason=unsafe_reason,
        )

    decision = SandboxBackendDecision.WARN if warnings else SandboxBackendDecision.ALLOW
    return _result(
        mode=mode,
        requirement=requirement,
        capability=capability,
        decision=decision,
        should_block=False,
        truth_label="SANDBOX_BACKEND_GATED",
        warnings=tuple(warnings),
        unsafe_backend_allowed_reason=unsafe_reason,
    )


def sandbox_backend_gate_to_artifact(result: SandboxBackendGateResult) -> dict[str, Any]:
    return result.to_canonical_dict()


def _extract_signals(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    args = metadata.get("args")
    if isinstance(args, Mapping):
        raw = args.get(SANDBOX_BACKEND_SIGNALS_KEY)
        if isinstance(raw, Mapping):
            return dict(raw)
    raw = metadata.get(SANDBOX_BACKEND_SIGNALS_KEY)
    if isinstance(raw, Mapping):
        return dict(raw)
    return {}


def _violation(
    *,
    key: str,
    truth_label: str,
    message: str,
    safety_class: SandboxSafetyClass,
    evidence_refs: tuple[str, ...] = (),
) -> SandboxBackendViolation:
    refs = evidence_refs or ("src/agentic_runtime/sandbox.py",)
    return SandboxBackendViolation(
        key=key,
        truth_label=truth_label,
        message=message,
        safety_class=safety_class,
        evidence_refs=refs,
    )


def _finalize_with_violations(
    *,
    mode: GovernanceEnforcementMode,
    requirement: SandboxBackendRequirement,
    capability: SandboxBackendCapability,
    violations: tuple[SandboxBackendViolation, ...],
    warnings: tuple[SandboxBackendViolation, ...],
) -> SandboxBackendGateResult:
    if mode is GovernanceEnforcementMode.SHADOW_ONLY:
        return _result(
            mode=mode,
            requirement=requirement,
            capability=capability,
            decision=SandboxBackendDecision.ALLOW,
            should_block=False,
            truth_label="SANDBOX_BACKEND_GATED",
            violations=violations,
            warnings=warnings,
            reason_codes=("SANDBOX_BACKEND_VIOLATION_RECORDED",),
        )

    if mode is GovernanceEnforcementMode.ADVISORY:
        return _result(
            mode=mode,
            requirement=requirement,
            capability=capability,
            decision=SandboxBackendDecision.WARN,
            should_block=False,
            truth_label="SANDBOX_BACKEND_GATED",
            violations=violations,
            warnings=warnings,
            reason_codes=("SANDBOX_BACKEND_ADVISORY",),
        )

    return _result(
        mode=mode,
        requirement=requirement,
        capability=capability,
        decision=SandboxBackendDecision.DENY,
        should_block=True,
        truth_label="BLOCKED_UNSAFE_SANDBOX_PROMOTION",
        violations=violations,
        warnings=warnings,
        reason_codes=("SANDBOX_BACKEND_DENIED",),
    )


def _result(
    *,
    mode: GovernanceEnforcementMode,
    requirement: SandboxBackendRequirement,
    capability: SandboxBackendCapability,
    decision: SandboxBackendDecision,
    should_block: bool,
    truth_label: str,
    violations: tuple[SandboxBackendViolation, ...] = (),
    warnings: tuple[SandboxBackendViolation, ...] = (),
    unavailable_reasons: tuple[str, ...] = (),
    reason_codes: tuple[str, ...] = (),
    unsafe_backend_allowed_reason: str = "",
) -> SandboxBackendGateResult:
    unavailable = unavailable_reasons[0] if unavailable_reasons else ""
    proof_ref = capability.safe_verified_proof_refs[0] if capability.safe_verified_proof_refs else ""
    artifact = SandboxBackendGateArtifact(
        mode=mode,
        requirement=requirement,
        capability=capability,
        decision=decision,
        enforced=mode is GovernanceEnforcementMode.ENFORCE_FAIL_CLOSED,
        submit_blocked=should_block,
        truth_label=truth_label,
        sandbox_backend_kind=capability.backend_kind.value,
        sandbox_safety_class=capability.safety_class.value,
        sandbox_gate_decision=decision.value,
        sandbox_unavailable_reason=unavailable,
        unsafe_backend_allowed_reason=unsafe_backend_allowed_reason,
        safe_backend_proof_ref=proof_ref,
        violations=violations,
        warnings=warnings,
        unavailable_reasons=unavailable_reasons,
        reason_codes=reason_codes,
    )
    return SandboxBackendGateResult(
        decision=decision,
        should_block=should_block,
        artifact=artifact,
    )
