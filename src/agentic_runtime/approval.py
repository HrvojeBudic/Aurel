"""P0.15 — structured approval contracts, policy resolver, and previews."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional

from .core_types import CommandEnvelope, PolicyVerdict, RiskLevel, new_id, now
from .policy import PolicyDecision
from .test_integrity import MUTATE_PROTECTED_TOOL
from .tools import ToolSideEffectType, ToolSpec

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|credential)"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
)


class ApprovalRiskClass(str, Enum):
    R0 = "R0"  # read-only / inspect
    R1 = "R1"  # safe local non-destructive
    R2 = "R2"  # reversible write
    R3 = "R3"  # external side effect
    R4 = "R4"  # sensitive / system / security-affecting
    R5 = "R5"  # irreversible / destructive / high-impact


class ApprovalMode(str, Enum):
    AUTO = "auto"
    CONSOLE = "console"
    DENY = "deny"
    PREVIEW_ONLY = "preview_only"


class ApprovalOutcome(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"
    AUTO_APPROVED = "auto_approved"
    AUTO_DENIED = "auto_denied"


@dataclass
class ApprovalPreview:
    action_type: str
    summary: str
    affected_paths: list[str] = field(default_factory=list)
    before_summary: str = ""
    after_summary: str = ""
    diff_summary: str = ""
    reversibility: str = "unknown"
    risk_explanation: str = ""
    command: list[str] = field(default_factory=list)
    timeout_seconds: Optional[float] = None
    working_directory: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApprovalRequest:
    request_id: str
    command: CommandEnvelope
    decision: PolicyDecision
    risk_class: ApprovalRiskClass
    action_summary: str
    side_effect_type: str
    preview: Optional[ApprovalPreview]
    affected_paths: list[str]
    required_capabilities: list[str]
    policy_verdict: PolicyVerdict
    created_at: float = field(default_factory=now)
    command_id: str = ""
    task_id: str = ""
    context: str = ""
    confirmation_level: int = 1
    strong_warning: bool = False

    @staticmethod
    def build(
        command: CommandEnvelope,
        decision: PolicyDecision,
        *,
        risk_class: ApprovalRiskClass,
        preview: Optional[ApprovalPreview],
        tool_spec: Optional[ToolSpec] = None,
        task_id: str = "",
        confirmation_level: int = 1,
        strong_warning: bool = False,
        context: str = "",
    ) -> "ApprovalRequest":
        affected = list(preview.affected_paths) if preview else _affected_paths(command)
        side_effect = (
            tool_spec.side_effect_type.value if tool_spec else "unknown"
        )
        capabilities = list(tool_spec.required_capabilities) if tool_spec else []
        summary = preview.summary if preview else _action_summary(command)
        return ApprovalRequest(
            request_id=new_id("approval"),
            command=command,
            decision=decision,
            risk_class=risk_class,
            action_summary=summary,
            side_effect_type=side_effect,
            preview=preview,
            affected_paths=affected,
            required_capabilities=capabilities,
            policy_verdict=decision.verdict,
            command_id=command.id,
            task_id=task_id,
            context=context or command.rationale,
            confirmation_level=confirmation_level,
            strong_warning=strong_warning,
        )


@dataclass
class ApprovalDecision:
    request_id: str
    outcome: ApprovalOutcome
    reason: str
    decided_by: str
    decided_at: float = field(default_factory=now)
    confirmation_level: int = 0
    constraints: dict[str, Any] = field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return self.outcome in {ApprovalOutcome.APPROVED, ApprovalOutcome.AUTO_APPROVED}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d


@dataclass
class ApprovalReceipt:
    receipt_id: str
    request_id: str
    decision: ApprovalOutcome
    risk_class: ApprovalRiskClass
    tool_name: str
    approved_scope: list[str] = field(default_factory=list)
    reason: str = ""
    decided_by: str = ""
    trace_id: str = ""
    expires_at: Optional[float] = None
    preview_summary: str = ""

    @staticmethod
    def from_decision(
        request: ApprovalRequest,
        decision: ApprovalDecision,
        *,
        trace_id: str = "",
    ) -> "ApprovalReceipt":
        preview_summary = request.preview.summary if request.preview else request.action_summary
        return ApprovalReceipt(
            receipt_id=new_id("approval_rcpt"),
            request_id=request.request_id,
            decision=decision.outcome,
            risk_class=request.risk_class,
            tool_name=request.command.tool,
            approved_scope=list(request.affected_paths),
            reason=decision.reason,
            decided_by=decision.decided_by,
            trace_id=trace_id,
            preview_summary=_sanitize_text(preview_summary, max_len=240),
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["decision"] = self.decision.value
        d["risk_class"] = self.risk_class.value
        return d


@dataclass
class ApprovalRequirement:
    risk_class: ApprovalRiskClass
    required: bool
    preview_required: bool
    auto_allow: bool
    auto_deny: bool
    confirmation_level: int
    strong_warning: bool
    reason: str


class ApprovalPolicy:
    """Resolve whether preview/approval/two-step confirmation is required."""

    def __init__(self, *, deny_r5_by_default: bool = True) -> None:
        self.deny_r5_by_default = deny_r5_by_default

    def resolve(
        self,
        cmd: CommandEnvelope,
        decision: PolicyDecision,
        tool_spec: Optional[ToolSpec] = None,
    ) -> ApprovalRequirement:
        risk_class = classify_risk(cmd, decision, tool_spec)
        if decision.verdict is PolicyVerdict.DENY:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=False,
                preview_required=False,
                auto_allow=False,
                auto_deny=True,
                confirmation_level=0,
                strong_warning=False,
                reason="policy denied",
            )

        if cmd.tool == MUTATE_PROTECTED_TOOL and cmd.args.get("approved") is True:
            return ApprovalRequirement(
                risk_class=ApprovalRiskClass.R4,
                required=True,
                preview_required=True,
                auto_allow=False,
                auto_deny=False,
                confirmation_level=2,
                strong_warning=True,
                reason="approved protected verification mutation requires confirmation",
            )

        if decision.verdict is PolicyVerdict.REQUIRE_APPROVAL and risk_class in {
            ApprovalRiskClass.R0, ApprovalRiskClass.R1,
        }:
            risk_class = ApprovalRiskClass.R3

        if risk_class is ApprovalRiskClass.R0:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=False,
                preview_required=False,
                auto_allow=True,
                auto_deny=False,
                confirmation_level=0,
                strong_warning=False,
                reason="R0 read-only action",
            )

        if risk_class is ApprovalRiskClass.R1:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=False,
                preview_required=False,
                auto_allow=True,
                auto_deny=False,
                confirmation_level=0,
                strong_warning=False,
                reason="R1 safe local action",
            )

        if risk_class is ApprovalRiskClass.R2:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=True,
                preview_required=True,
                auto_allow=False,
                auto_deny=False,
                confirmation_level=1,
                strong_warning=False,
                reason="R2 reversible write requires preview and approval",
            )

        if risk_class is ApprovalRiskClass.R3:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=True,
                preview_required=True,
                auto_allow=False,
                auto_deny=False,
                confirmation_level=1,
                strong_warning=False,
                reason="R3 external side effect requires explicit approval",
            )

        if risk_class is ApprovalRiskClass.R4:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=True,
                preview_required=True,
                auto_allow=False,
                auto_deny=False,
                confirmation_level=1,
                strong_warning=True,
                reason="R4 sensitive action requires explicit approval with warning",
            )

        # R5
        if self.deny_r5_by_default:
            return ApprovalRequirement(
                risk_class=risk_class,
                required=True,
                preview_required=True,
                auto_allow=False,
                auto_deny=True,
                confirmation_level=2,
                strong_warning=True,
                reason="R5 high-impact action denied by default",
            )
        return ApprovalRequirement(
            risk_class=risk_class,
            required=True,
            preview_required=True,
            auto_allow=False,
            auto_deny=False,
            confirmation_level=2,
            strong_warning=True,
            reason="R5 high-impact action requires two-step confirmation",
        )


def classify_risk(
    cmd: CommandEnvelope,
    decision: PolicyDecision,
    tool_spec: Optional[ToolSpec] = None,
) -> ApprovalRiskClass:
    tool = cmd.tool
    risk = decision.risk
    side_effect = tool_spec.side_effect_type if tool_spec else None

    if tool in {"read_file", "list_dir", "search_text", "git_status", "git_diff"}:
        return ApprovalRiskClass.R0
    if risk is RiskLevel.TRIVIAL:
        return ApprovalRiskClass.R0
    if risk is RiskLevel.LOW:
        return ApprovalRiskClass.R1

    destructive = {"delete_file", "mutate_protected_verification"}
    shell_tools = {"run_shell", "run_python", "run_tests", "network_fetch"}
    write_tools = {"write_file", "edit_file", "patch_file"}

    if tool in destructive or cmd.args.get("irreversible"):
        return ApprovalRiskClass.R5
    if risk is RiskLevel.CRITICAL:
        return ApprovalRiskClass.R5
    if tool in shell_tools or side_effect is ToolSideEffectType.SHELL_EXECUTION:
        if tool in {"run_shell", "network_fetch"} or cmd.args.get("touches_secrets"):
            return ApprovalRiskClass.R4
        return ApprovalRiskClass.R3
    if tool in write_tools or side_effect is ToolSideEffectType.FILESYSTEM_WRITE:
        return ApprovalRiskClass.R2
    if risk is RiskLevel.HIGH:
        return ApprovalRiskClass.R4
    if risk is RiskLevel.MEDIUM:
        return ApprovalRiskClass.R2
    return ApprovalRiskClass.R1


def build_preview(cmd: CommandEnvelope, sandbox, tool_spec: Optional[ToolSpec] = None) -> ApprovalPreview:
    tool = cmd.tool
    args = _sanitize_args(cmd.args)
    affected = _affected_paths(cmd)
    write_tools = {"write_file", "edit_file", "patch_file"}
    shell_tools = {"run_shell", "run_python", "run_tests"}

    if tool in write_tools:
        path = str(args.get("path", ""))
        before = ""
        try:
            before = sandbox.read_file(path)
        except OSError:
            before = ""
        after = _predict_after(tool, args, before)
        diff = _diff_summary(before, after)
        return ApprovalPreview(
            action_type=tool,
            summary=f"{tool} on {path}",
            affected_paths=[path] if path else affected,
            before_summary=_truncate(before, 240),
            after_summary=_truncate(after, 240),
            diff_summary=diff,
            reversibility="reversible with rollback" if before else "new file write",
            risk_explanation="filesystem write inside workspace",
            warnings=_write_warnings(tool, args),
        )

    if tool in shell_tools:
        command = _execution_command(tool, args)
        timeout = args.get("timeout_seconds", args.get("timeout", 10))
        warnings = ["shell execution may modify workspace state"]
        if tool == "run_shell":
            warnings.append("arbitrary shell command")
        if args.get("touches_secrets"):
            warnings.append("may access secrets")
        if tool == "network_fetch" or "curl" in " ".join(command):
            warnings.append("may perform network access")
        return ApprovalPreview(
            action_type=tool,
            summary=f"execute {tool}",
            affected_paths=affected,
            command=command,
            timeout_seconds=float(timeout) if timeout is not None else None,
            working_directory=getattr(sandbox, "root", "."),
            reversibility="may be irreversible",
            risk_explanation="execution side effects",
            warnings=warnings,
        )

    return ApprovalPreview(
        action_type=tool,
        summary=_action_summary(cmd),
        affected_paths=affected,
        risk_explanation=f"tool {tool}",
    )


def _execution_command(tool: str, args: dict) -> list[str]:
    if tool == "run_tests":
        command = args.get("command")
        if command is None:
            return ["python3", str(args.get("test_file", "test.py"))]
        return [str(x) for x in command]
    if tool == "run_python":
        return ["python3", *[str(x) for x in args.get("args", [])]]
    command = args.get("command", args.get("cmd"))
    if isinstance(command, str):
        return ["sh", "-c", command]
    if isinstance(command, list):
        return [str(x) for x in command]
    return []


def _predict_after(tool: str, args: dict, before: str) -> str:
    if tool == "write_file":
        return str(args.get("content", ""))
    if tool == "edit_file":
        find = str(args.get("find", ""))
        replace = str(args.get("replace", ""))
        if find and find in before:
            return before.replace(find, replace, 1)
        return before
    if tool == "patch_file":
        patch = str(args.get("patch") or args.get("unified_diff") or "")
        if not patch:
            return before
        lines = patch.splitlines()
        removed = [ln[1:] for ln in lines if ln.startswith("-") and not ln.startswith("---")]
        added = [ln[1:] for ln in lines if ln.startswith("+") and not ln.startswith("+++")]
        out = before
        for old, new in zip(removed, added):
            if old in out:
                out = out.replace(old, new, 1)
        return out
    return before


def _diff_summary(before: str, after: str) -> str:
    if before == after:
        return "no content change predicted"
    b_lines = before.splitlines()
    a_lines = after.splitlines()
    changes = []
    for idx, (b, a) in enumerate(zip(b_lines, a_lines), start=1):
        if b != a:
            changes.append(f"L{idx}: {_truncate(b, 60)} -> {_truncate(a, 60)}")
    if len(a_lines) > len(b_lines):
        changes.append(f"+{len(a_lines) - len(b_lines)} line(s)")
    elif len(b_lines) > len(a_lines):
        changes.append(f"-{len(b_lines) - len(a_lines)} line(s)")
    return "; ".join(changes[:5]) or "content changed"


def _affected_paths(cmd: CommandEnvelope) -> list[str]:
    path = cmd.args.get("path") or cmd.args.get("file") or cmd.args.get("root")
    if isinstance(path, str) and path:
        return [path]
    return []


def _action_summary(cmd: CommandEnvelope) -> str:
    args = _sanitize_args(cmd.args)
    bits = ", ".join(f"{k}={_truncate(str(v), 40)}" for k, v in list(args.items())[:4])
    return f"{cmd.tool}({bits})"


def _write_warnings(tool: str, args: dict) -> list[str]:
    warnings = []
    if tool == "patch_file":
        warnings.append("patch will modify file contents")
    if args.get("create_dirs"):
        warnings.append("may create parent directories")
    return warnings


def _sanitize_args(args: dict) -> dict:
    out = {}
    for key, value in args.items():
        text = str(value)
        if _SECRET_PATTERNS[0].search(key) or any(p.search(text) for p in _SECRET_PATTERNS):
            out[key] = "[REDACTED]"
        else:
            out[key] = _truncate(text, 200)
    return out


def _sanitize_text(text: str, *, max_len: int = 240) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return _truncate(out, max_len)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
