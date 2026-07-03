"""P4-EXEC-D tool / model / terminal / code execution profiles.

Capability profiles, not permission grants. The tool profile is the only
one with an executable posture, and only for the existing safe read-only
``ExecRuntimeBridge`` path — direct tool dispatch and mutating tools remain
structurally forbidden. The model, terminal, and code profiles model future
execution requirements while their execution stays structurally unavailable:
a profile that claims model calls, shell/subprocess, eval/script execution,
filesystem mutation, or network execution is unconstructible in this pack.
"""

from __future__ import annotations

from dataclasses import dataclass

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_modes import (
    EXECUTION_MODE_PROFILE_VERSION,
    ExecutionModeAvailability,
    ExecutionModeProfile,
    ExecutionModeRegistry,
)
from .exec_runtime_bridge import SUPPORTED_BRIDGE_TOOLS
from .exec_types import (
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

TOOL_EXECUTION_PROFILE_VERSION = "tool_execution_profile.v1"
MODEL_EXECUTION_PROFILE_VERSION = "model_execution_profile.v1"
TERMINAL_EXECUTION_PROFILE_VERSION = "terminal_execution_profile.v1"
CODE_EXECUTION_PROFILE_VERSION = "code_execution_profile.v1"
NO_MODEL_CALL_PROOF_VERSION = "no_model_call_proof.v1"
NO_TERMINAL_EXECUTION_PROOF_VERSION = "no_terminal_execution_proof.v1"
NO_CODE_EXECUTION_PROOF_VERSION = "no_code_execution_proof.v1"

MUTATING_TOOLS_UNAVAILABLE_REASON = (
    "mutating tools are unavailable through the bridge; only the safe "
    "read-only path exists — widening requires a future pack with P9 "
    "authority and verifier evidence"
)
MODEL_EXECUTION_UNAVAILABLE_REASON = (
    "model execution is modeled PROFILE_ONLY; no model API is called in "
    "P4-EXEC-D — live model execution requires router/budget/prompt/output "
    "contracts, a verifier, and a future pack"
)
TERMINAL_EXECUTION_UNAVAILABLE_REASON = (
    "terminal execution is UNAVAILABLE; no shell, subprocess, or network "
    "action exists in P4-EXEC-D — it requires sandbox profile, operator "
    "approval, and P9 authority in a future pack"
)
CODE_EXECUTION_UNAVAILABLE_REASON = (
    "code execution is UNAVAILABLE; no eval, script execution, filesystem "
    "mutation, or network action exists in P4-EXEC-D — it requires sandbox "
    "profile, verifier, and P9 authority in a future pack"
)
CONVERSATION_MODE_UNAVAILABLE_REASON = (
    "conversation mode has no execution profile pack yet; it remains "
    "UNAVAILABLE until a future mode pack models it"
)
COMPOSITE_MODE_UNAVAILABLE_REASON = (
    "composite mode has no execution profile pack yet; it remains "
    "UNAVAILABLE until topology/concurrency canon exists (P4.17+)"
)
NON_MODE_BLOCKED_REASON = (
    "UNAVAILABLE/ERROR are posture markers, never executable modes; "
    "requesting them is always blocked"
)


@dataclass(frozen=True)
class ToolExecutionProfile(_ExecCanonicalMixin):
    """The only executable profile: existing safe read-only bridge path."""

    tool_profile_id: str
    allowed_tool_names: tuple[str, ...]
    read_only_tools: tuple[str, ...]
    truth_label: ExecTruthLabel
    contract_version: str = TOOL_EXECUTION_PROFILE_VERSION
    mutating_tools_unavailable: bool = True
    mutating_tools_unavailable_reason: str = MUTATING_TOOLS_UNAVAILABLE_REASON
    requires_sandbox_profile: bool = True
    requires_policy_context: bool = True
    requires_lease_scope_match: bool = True
    direct_dispatch_allowed: bool = False
    runtime_bridge_required: bool = True
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        require_nonempty(self, "tool_profile_id", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "direct_dispatch_allowed")
        forbid_false(
            self,
            "runtime_bridge_required",
            "mutating_tools_unavailable",
            "requires_lease_scope_match",
        )
        if not self.allowed_tool_names:
            raise AurelExecValidationError(
                "tool profile must name its allowed tools explicitly",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="allowed_tool_names",
            )
        for tool in self.allowed_tool_names:
            if tool not in self.read_only_tools:
                raise AurelExecValidationError(
                    f"allowed tool {tool!r} is not declared read-only; "
                    "mutating tools cannot be silently allowed",
                    code=AurelExecErrorCode.UNSUPPORTED_TOOL,
                    field="allowed_tool_names",
                )
            if tool not in SUPPORTED_BRIDGE_TOOLS:
                raise AurelExecValidationError(
                    f"allowed tool {tool!r} exceeds the existing safe bridge "
                    f"path {SUPPORTED_BRIDGE_TOOLS}; tool expansion belongs "
                    "to a future pack",
                    code=AurelExecErrorCode.UNSUPPORTED_TOOL,
                    field="allowed_tool_names",
                )

    @property
    def profile_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class ModelExecutionProfile(_ExecCanonicalMixin):
    """Model requirements model. Not a model call: execution structurally off."""

    model_profile_id: str
    truth_label: ExecTruthLabel
    contract_version: str = MODEL_EXECUTION_PROFILE_VERSION
    allowed_model_refs: tuple[str, ...] = ()
    model_execution_available: bool = False
    model_call_allowed: bool = False
    requires_router_ref: bool = True
    requires_budget_ref: bool = True
    requires_policy_context: bool = True
    requires_prompt_contract: bool = True
    requires_output_contract: bool = True
    requires_verifier: bool = True
    unavailable_reason: str = MODEL_EXECUTION_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        require_nonempty(self, "model_profile_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "unavailable_reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "model_execution_available", "model_call_allowed")
        forbid_false(
            self,
            "requires_router_ref",
            "requires_budget_ref",
            "requires_policy_context",
            "requires_prompt_contract",
            "requires_output_contract",
            "requires_verifier",
        )


@dataclass(frozen=True)
class TerminalExecutionProfile(_ExecCanonicalMixin):
    """Terminal requirements model. Not shell/subprocess execution."""

    terminal_profile_id: str
    truth_label: ExecTruthLabel
    contract_version: str = TERMINAL_EXECUTION_PROFILE_VERSION
    terminal_execution_available: bool = False
    subprocess_allowed: bool = False
    shell_allowed: bool = False
    network_allowed: bool = False
    requires_sandbox_profile: bool = True
    requires_operator_approval: bool = True
    requires_p9_authority: bool = True
    unavailable_reason: str = TERMINAL_EXECUTION_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        require_nonempty(self, "terminal_profile_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "unavailable_reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(
            self,
            "terminal_execution_available",
            "subprocess_allowed",
            "shell_allowed",
            "network_allowed",
        )
        forbid_false(
            self,
            "requires_sandbox_profile",
            "requires_operator_approval",
            "requires_p9_authority",
        )


@dataclass(frozen=True)
class CodeExecutionProfile(_ExecCanonicalMixin):
    """Code-execution requirements model. Not eval/script execution."""

    code_profile_id: str
    truth_label: ExecTruthLabel
    contract_version: str = CODE_EXECUTION_PROFILE_VERSION
    code_execution_available: bool = False
    eval_allowed: bool = False
    script_execution_allowed: bool = False
    filesystem_mutation_allowed: bool = False
    network_allowed: bool = False
    requires_sandbox_profile: bool = True
    requires_verifier: bool = True
    requires_p9_authority: bool = True
    unavailable_reason: str = CODE_EXECUTION_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        require_nonempty(self, "code_profile_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "unavailable_reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(
            self,
            "code_execution_available",
            "eval_allowed",
            "script_execution_allowed",
            "filesystem_mutation_allowed",
            "network_allowed",
        )
        forbid_false(
            self,
            "requires_sandbox_profile",
            "requires_verifier",
            "requires_p9_authority",
        )


def build_default_tool_execution_profile() -> ToolExecutionProfile:
    """The existing safe read-only bridge path, and nothing more."""
    return ToolExecutionProfile(
        tool_profile_id="exec-tool-profile-"
        + stable_hash(SUPPORTED_BRIDGE_TOOLS)[:16],
        allowed_tool_names=SUPPORTED_BRIDGE_TOOLS,
        read_only_tools=SUPPORTED_BRIDGE_TOOLS,
        truth_label=ExecTruthLabel.LIVE,
    )


def build_default_model_execution_profile() -> ModelExecutionProfile:
    return ModelExecutionProfile(
        model_profile_id="exec-model-profile-default",
        truth_label=ExecTruthLabel.UNAVAILABLE,
    )


def build_default_terminal_execution_profile() -> TerminalExecutionProfile:
    return TerminalExecutionProfile(
        terminal_profile_id="exec-terminal-profile-default",
        truth_label=ExecTruthLabel.UNAVAILABLE,
    )


def build_default_code_execution_profile() -> CodeExecutionProfile:
    return CodeExecutionProfile(
        code_profile_id="exec-code-profile-default",
        truth_label=ExecTruthLabel.UNAVAILABLE,
    )


def _mode_profile(
    mode: ExecutionMode,
    name: str,
    availability: ExecutionModeAvailability,
    *,
    unavailable_reason: str | None = None,
    requires_verifier: bool = False,
    requires_p9_authority: bool = False,
    truth_label: ExecTruthLabel = ExecTruthLabel.UNAVAILABLE,
) -> ExecutionModeProfile:
    return ExecutionModeProfile(
        profile_id="exec-mode-profile-" + stable_hash((mode.value, name))[:16],
        execution_mode=mode,
        profile_name=name,
        availability_status=availability,
        truth_label=truth_label,
        unavailable_reason=unavailable_reason,
        requires_verifier=requires_verifier,
        requires_p9_authority=requires_p9_authority,
    )


def build_default_execution_mode_registry() -> ExecutionModeRegistry:
    """The closed-world default registry: tool available for the existing
    bridge path only; model PROFILE_ONLY; terminal/code/conversation/
    composite UNAVAILABLE; UNAVAILABLE/ERROR markers BLOCKED."""
    profiles = (
        _mode_profile(
            ExecutionMode.TOOL,
            "safe read-only tool execution via existing ExecRuntimeBridge",
            ExecutionModeAvailability.AVAILABLE_FOR_EXISTING_BRIDGE,
            truth_label=ExecTruthLabel.LIVE,
        ),
        _mode_profile(
            ExecutionMode.MODEL,
            "model execution requirements (profile only)",
            ExecutionModeAvailability.PROFILE_ONLY,
            unavailable_reason=MODEL_EXECUTION_UNAVAILABLE_REASON,
            requires_verifier=True,
        ),
        _mode_profile(
            ExecutionMode.TERMINAL,
            "terminal execution requirements (unavailable)",
            ExecutionModeAvailability.UNAVAILABLE,
            unavailable_reason=TERMINAL_EXECUTION_UNAVAILABLE_REASON,
            requires_verifier=True,
            requires_p9_authority=True,
        ),
        _mode_profile(
            ExecutionMode.CODE,
            "code execution requirements (unavailable)",
            ExecutionModeAvailability.UNAVAILABLE,
            unavailable_reason=CODE_EXECUTION_UNAVAILABLE_REASON,
            requires_verifier=True,
            requires_p9_authority=True,
        ),
        _mode_profile(
            ExecutionMode.CONVERSATION,
            "conversation mode (no profile pack yet)",
            ExecutionModeAvailability.UNAVAILABLE,
            unavailable_reason=CONVERSATION_MODE_UNAVAILABLE_REASON,
        ),
        _mode_profile(
            ExecutionMode.COMPOSITE,
            "composite mode (no profile pack yet)",
            ExecutionModeAvailability.UNAVAILABLE,
            unavailable_reason=COMPOSITE_MODE_UNAVAILABLE_REASON,
        ),
        _mode_profile(
            ExecutionMode.UNAVAILABLE,
            "UNAVAILABLE posture marker",
            ExecutionModeAvailability.BLOCKED,
            unavailable_reason=NON_MODE_BLOCKED_REASON,
        ),
        _mode_profile(
            ExecutionMode.ERROR,
            "ERROR posture marker",
            ExecutionModeAvailability.BLOCKED,
            unavailable_reason=NON_MODE_BLOCKED_REASON,
        ),
    )
    return ExecutionModeRegistry(
        registry_id="exec-mode-registry-default",
        registry_version="v1",
        default_mode=ExecutionMode.TOOL,
        profiles=profiles,
        truth_label=ExecTruthLabel.LIVE,
    )


@dataclass(frozen=True)
class NoModelCallProof(_ExecCanonicalMixin):
    """Evidence that no model API was or can be called in this pack."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_MODEL_CALL_PROOF_VERSION
    model_execution_available: bool = False
    model_call_allowed: bool = False

    def __post_init__(self) -> None:
        forbid_true(self, "model_execution_available", "model_call_allowed")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_model_call_proof() -> NoModelCallProof:
    return NoModelCallProof(
        reason=MODEL_EXECUTION_UNAVAILABLE_REASON,
        future_pack_owner="future model execution pack under router/budget/verifier canon",
    )


@dataclass(frozen=True)
class NoTerminalExecutionProof(_ExecCanonicalMixin):
    """Evidence that no shell/subprocess/network execution exists."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_TERMINAL_EXECUTION_PROOF_VERSION
    terminal_execution_available: bool = False
    subprocess_allowed: bool = False
    shell_allowed: bool = False
    network_execution_available: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "terminal_execution_available",
            "subprocess_allowed",
            "shell_allowed",
            "network_execution_available",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_terminal_execution_proof() -> NoTerminalExecutionProof:
    return NoTerminalExecutionProof(
        reason=TERMINAL_EXECUTION_UNAVAILABLE_REASON,
        future_pack_owner="future terminal pack under sandbox/operator/P9 authority",
    )


@dataclass(frozen=True)
class NoCodeExecutionProof(_ExecCanonicalMixin):
    """Evidence that no eval/script/filesystem-mutating execution exists."""

    reason: str
    future_pack_owner: str
    contract_version: str = NO_CODE_EXECUTION_PROOF_VERSION
    code_execution_available: bool = False
    eval_allowed: bool = False
    script_execution_allowed: bool = False
    filesystem_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        forbid_true(
            self,
            "code_execution_available",
            "eval_allowed",
            "script_execution_allowed",
            "filesystem_mutation_allowed",
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "future_pack_owner", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_code_execution_proof() -> NoCodeExecutionProof:
    return NoCodeExecutionProof(
        reason=CODE_EXECUTION_UNAVAILABLE_REASON,
        future_pack_owner="future code execution pack under sandbox/verifier/P9 authority",
    )
