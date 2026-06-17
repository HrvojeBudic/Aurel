"""
hitl.py — Human-in-the-Loop approval gates (P0.15 upgrade).

Approval gates consume structured ``ApprovalRequest`` objects and return
``ApprovalDecision`` receipts. Runtime remains the execution authority; gates
only decide whether a governed command may proceed.
"""
from __future__ import annotations

from typing import Callable, Optional, Protocol

from .approval import (
    ApprovalDecision,
    ApprovalMode,
    ApprovalOutcome,
    ApprovalRequest,
    ApprovalRiskClass,
)


class ApprovalGate(Protocol):
    def request(self, req: ApprovalRequest) -> ApprovalDecision: ...


class ConsoleApprover:
    """Text-based approver for CLI/manual operation."""

    def __init__(self, input_fn: Callable[[str], str] = input, *, operator: str = "console") -> None:
        self.input_fn = input_fn
        self.operator = operator

    def request(self, req: ApprovalRequest) -> ApprovalDecision:
        print("\n*** HUMAN APPROVAL REQUIRED ***")
        print(f"  request_id: {req.request_id}")
        print(f"  tool: {req.command.tool}")
        print(f"  risk_class: {req.risk_class.value}")
        print(f"  action: {req.action_summary}")
        if req.affected_paths:
            print(f"  affected_paths: {', '.join(req.affected_paths)}")
        if req.preview is not None:
            print(f"  preview: {req.preview.summary}")
            if req.preview.diff_summary:
                print(f"  diff: {req.preview.diff_summary}")
            if req.preview.command:
                print(f"  command: {' '.join(req.preview.command)}")
            for warning in req.preview.warnings:
                print(f"  warning: {warning}")
        if req.strong_warning:
            print("  STRONG WARNING: sensitive or high-impact action")
        if req.confirmation_level >= 2:
            confirm = self.input_fn("  type YES to acknowledge high-impact risk: ").strip()
            if confirm != "YES":
                return ApprovalDecision(
                    req.request_id,
                    ApprovalOutcome.DENIED,
                    "two-step confirmation not acknowledged",
                    self.operator,
                    confirmation_level=2,
                )
        ans = self.input_fn("  approve? [y/N] ").strip().lower()
        if ans == "y":
            return ApprovalDecision(
                req.request_id,
                ApprovalOutcome.APPROVED,
                "approved by console operator",
                self.operator,
                confirmation_level=req.confirmation_level,
            )
        return ApprovalDecision(
            req.request_id,
            ApprovalOutcome.DENIED,
            "denied by console operator",
            self.operator,
            confirmation_level=req.confirmation_level,
        )


class AutoApprover:
    """Unattended approver bounded by risk class and optional predicate."""

    def __init__(
        self,
        predicate: Optional[Callable[[ApprovalRequest], bool]] = None,
        *,
        allow_r0: bool = True,
        allow_r1: bool = True,
        allow_r2: bool = False,
        allow_r3: bool = False,
        allow_r4: bool = False,
        allow_r5: bool = False,
        decided_by: str = "auto_approver",
    ) -> None:
        self.predicate = predicate
        self.allow_r0 = allow_r0
        self.allow_r1 = allow_r1
        self.allow_r2 = allow_r2
        self.allow_r3 = allow_r3
        self.allow_r4 = allow_r4
        self.allow_r5 = allow_r5
        self.decided_by = decided_by
        self.log: list[dict] = []

    def request(self, req: ApprovalRequest) -> ApprovalDecision:
        allowed = self._class_allowed(req.risk_class)
        if self.predicate is not None:
            allowed = allowed and bool(self.predicate(req))
        outcome = ApprovalOutcome.AUTO_APPROVED if allowed else ApprovalOutcome.AUTO_DENIED
        reason = "auto-approved within configured envelope" if allowed else "auto-denied by approver policy"
        decision = ApprovalDecision(
            req.request_id,
            outcome,
            reason,
            self.decided_by,
            confirmation_level=req.confirmation_level,
        )
        self.log.append({
            "tool": req.command.tool,
            "risk_class": req.risk_class.value,
            "outcome": outcome.value,
            "allowed": allowed,
        })
        return decision

    def _class_allowed(self, risk_class: ApprovalRiskClass) -> bool:
        return {
            ApprovalRiskClass.R0: self.allow_r0,
            ApprovalRiskClass.R1: self.allow_r1,
            ApprovalRiskClass.R2: self.allow_r2,
            ApprovalRiskClass.R3: self.allow_r3,
            ApprovalRiskClass.R4: self.allow_r4,
            ApprovalRiskClass.R5: self.allow_r5,
        }[risk_class]


class DenyAllApprover:
    """Safety mode: deny every approval request."""

    def request(self, req: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(
            req.request_id,
            ApprovalOutcome.DENIED,
            "deny-all approval mode",
            "deny_all",
            confirmation_level=req.confirmation_level,
        )


class PreviewOnlyApprover:
    """Show preview metadata but never approve execution."""

    def request(self, req: ApprovalRequest) -> ApprovalDecision:
        return ApprovalDecision(
            req.request_id,
            ApprovalOutcome.DEFERRED,
            "preview-only mode; execution deferred",
            "preview_only",
            confirmation_level=req.confirmation_level,
        )


def make_approval_gate(mode: ApprovalMode, **kwargs) -> ApprovalGate:
    if mode is ApprovalMode.CONSOLE:
        return ConsoleApprover(**kwargs)
    if mode is ApprovalMode.DENY:
        return DenyAllApprover()
    if mode is ApprovalMode.PREVIEW_ONLY:
        return PreviewOnlyApprover()
    return AutoApprover(**kwargs)
