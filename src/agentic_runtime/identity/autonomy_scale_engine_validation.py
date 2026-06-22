"""P1.4.8 — Autonomy Scale Engine validation layer.

Fail-closed validation: unknown/ambiguous values must not allow actions.
Malformed request shape -> validation exception.
Semantically disallowed -> A7_DENIED decision with blockers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agentic_runtime.identity.autonomy_scale_engine import (
    ActionCategory,
    AutonomyDecision,
    AutonomyEvaluationContext,
    AutonomyLevel,
    AutonomyRequest,
    ReversibilityTier,
    RiskTier,
    _denied,
    is_denied,
)

if TYPE_CHECKING:
    pass


# ── Validation exception ────────────────────────────────────────────────


class AutonomyValidationError(ValueError):
    """Raised when the autonomy request shape is invalid (malformed).

    Semantically disallowed requests produce A7_DENIED decisions,
    not exceptions. This exception is only for structural problems.
    """

    def __init__(self, message: str, *, field: str | None = None):
        super().__init__(message)
        self.field = field


# ── Validation result ────────────────────────────────────────────────────


@dataclass(frozen=True)
class AutonomyValidationResult:
    """Structured result from autonomy validation."""

    is_valid: bool
    decision: AutonomyDecision | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


# ── Public validators ───────────────────────────────────────────────────


def validate_autonomy_request(request: AutonomyRequest) -> AutonomyValidationResult:
    """Validate request shape. Returns validation result, not A7 decision."""
    errors: list[str] = []
    warnings: list[str] = []

    if not request.action_id or not request.action_id.strip():
        errors.append("missing_action_id")
    if not request.action_name or not request.action_name.strip():
        errors.append("missing_action_name")
    if not request.requested_by or not request.requested_by.strip():
        errors.append("missing_requested_by")
    if not request.agent_id or not request.agent_id.strip():
        errors.append("missing_agent_id")

    # Validate closed-world enums (must be known values)
    try:
        ActionCategory(request.action_category.value)
    except ValueError:
        errors.append("invalid_action_category")

    if request.risk_tier is not None:
        try:
            RiskTier(request.risk_tier.value)
        except ValueError:
            errors.append("invalid_risk_tier")

    if request.reversibility_tier is not None:
        try:
            ReversibilityTier(request.reversibility_tier.value)
        except ValueError:
            errors.append("invalid_reversibility_tier")

    return AutonomyValidationResult(
        is_valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_autonomy_context(context: AutonomyEvaluationContext) -> AutonomyValidationResult:
    """Validate that the evaluation context has minimum required fields."""
    errors: list[str] = []

    if context.agent_identity_card is None:
        errors.append("missing_agent_identity_card")
    if context.operator_contract is None:
        errors.append("missing_operator_contract")

    return AutonomyValidationResult(
        is_valid=len(errors) == 0,
        errors=tuple(errors),
    )


def validate_and_resolve_autonomy(
    request: AutonomyRequest,
    context: AutonomyEvaluationContext,
) -> AutonomyDecision:
    """Validate request and context, then resolve. Fails closed on ambiguity.

    Malformed structural problems raise AutonomyValidationError.
    Semantically invalid requests return A7_DENIED decisions.
    """
    # 1. Validate request shape
    req_validation = validate_autonomy_request(request)
    if not req_validation.is_valid:
        raise AutonomyValidationError(
            f"Invalid autonomy request: {', '.join(req_validation.errors)}",
            field="request",
        )

    # 2. Validate context shape
    ctx_validation = validate_autonomy_context(context)
    if not ctx_validation.is_valid:
        raise AutonomyValidationError(
            f"Invalid evaluation context: {', '.join(ctx_validation.errors)}",
            field="context",
        )

    # 3. Delegate to resolver (which handles semantic denial)
    from agentic_runtime.identity.autonomy_scale_engine import resolve_autonomy_decision

    return resolve_autonomy_decision(request, context)


# ── Invariant enforcement ────────────────────────────────────────────────


def enforce_autonomy_invariants(decision: AutonomyDecision) -> AutonomyValidationResult:
    """Enforce P1.4.8 invariants on a decision. Returns validation result."""
    errors: list[str] = []
    warnings: list[str] = []

    # INV-P148-02: A7 means denied, not elevated autonomy
    if decision.autonomy_level == AutonomyLevel.A7_DENIED and decision.allowed:
        errors.append("INV-P148-02: A7_DENIED but allowed=True")

    if decision.autonomy_level != AutonomyLevel.A7_DENIED and not decision.allowed:
        errors.append("INV-P148-02: allowed=False but autonomy level is not A7_DENIED")

    # INV-P148-07: Decision must be explainable
    if not decision.reason or not decision.reason.strip():
        errors.append("INV-P148-07: decision missing reason")

    # INV-P148-08: Denied decisions must expose blockers
    if not decision.allowed and len(decision.blockers) == 0:
        errors.append("INV-P148-08: denied decision has no blockers")

    # INV-P148-04: Authority scope required beyond suggestion
    if not decision.allowed:
        requires_scope = decision.action_category not in (
            ActionCategory.ANSWER,
            ActionCategory.SUGGEST,
        )
        # If beyond suggestion and denied, one blocker should mention authority
        if requires_scope:
            has_authority_blocker = any(
                "authority" in b.lower() or "scope" in b.lower()
                for b in decision.blockers
            )
            if not has_authority_blocker and "outside" not in " ".join(decision.blockers).lower():
                warnings.append("INV-P148-04: denied action beyond suggestion lacks authority blocker")

    return AutonomyValidationResult(
        is_valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
