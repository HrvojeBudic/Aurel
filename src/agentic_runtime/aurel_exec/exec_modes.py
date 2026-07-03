"""P4-EXEC-D execution mode registry / compatibility decision.

A closed-world registry of execution modes and a deterministic compatibility
decision: every ``ExecutionMode`` member must be classified, unknown modes
are BLOCKED, and no silent fallback exists — an unsupported requested mode
never degrades into tool mode or any other mode.

A registry is not execution and grants no authority. A profile is not
permission. A compatibility decision is not runtime success: ALLOWED means
only that the requested mode may proceed toward the existing managed
queue/claim/bridge path, where every P4-EXEC-A/B/C guard still applies.
Only TOOL mode can be available, and only for the existing safe read-only
``ExecRuntimeBridge`` path — direct tool dispatch remains forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_queue import ExecQueueEntry, block_queue_entry
from .exec_runtime_bridge import SUPPORTED_BRIDGE_EXECUTION_MODES
from .exec_types import (
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

if TYPE_CHECKING:
    from .exec_lease import ExecutionLease
    from .exec_mode_profiles import ToolExecutionProfile

EXECUTION_MODE_REGISTRY_VERSION = "execution_mode_registry.v1"
EXECUTION_MODE_PROFILE_VERSION = "execution_mode_profile.v1"
MODE_COMPATIBILITY_DECISION_VERSION = "mode_compatibility_decision.v1"
NO_SILENT_FALLBACK_PROOF_VERSION = "no_silent_fallback_proof.v1"

UNKNOWN_MODE_BLOCKED_REASON = (
    "the execution mode registry is closed-world; an unknown requested mode "
    "is BLOCKED — there is no silent fallback to tool or any other mode"
)
SILENT_FALLBACK_FORBIDDEN_REASON = (
    "an unsupported or unavailable execution mode never silently falls back "
    "to another mode; the request is blocked with an explicit reason"
)


class ExecutionModeAvailability(str, Enum):
    """Closed-world mode availability. AVAILABLE_FOR_EXISTING_BRIDGE is the
    only executable status and only TOOL mode may carry it."""

    AVAILABLE_FOR_EXISTING_BRIDGE = "AVAILABLE_FOR_EXISTING_BRIDGE"
    PROFILE_ONLY = "PROFILE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


_NON_EXECUTABLE_AVAILABILITY = (
    ExecutionModeAvailability.PROFILE_ONLY,
    ExecutionModeAvailability.UNAVAILABLE,
    ExecutionModeAvailability.BLOCKED,
    ExecutionModeAvailability.ERROR,
)


@dataclass(frozen=True)
class ExecutionModeProfile(_ExecCanonicalMixin):
    """Declared availability + requirements for one mode. Not permission."""

    profile_id: str
    execution_mode: ExecutionMode
    profile_name: str
    availability_status: ExecutionModeAvailability
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_MODE_PROFILE_VERSION
    requires_lease: bool = True
    requires_session: bool = True
    requires_worker_claim: bool = True
    requires_sandbox_profile: bool = True
    requires_policy_context: bool = True
    requires_verifier: bool = False
    requires_p5_proof: bool = False
    requires_p9_authority: bool = False
    unavailable_reason: str | None = None
    grants_permission: bool = False
    executes: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "profile_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "profile_name", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "grants_permission", "executes")
        if self.availability_status in _NON_EXECUTABLE_AVAILABILITY and (
            self.availability_status is not ExecutionModeAvailability.PROFILE_ONLY
            and not self.unavailable_reason
        ):
            raise AurelExecValidationError(
                f"{self.availability_status.value} profile must explain itself",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="unavailable_reason",
            )
        if (
            self.availability_status
            is ExecutionModeAvailability.AVAILABLE_FOR_EXISTING_BRIDGE
            and self.execution_mode not in SUPPORTED_BRIDGE_EXECUTION_MODES
        ):
            raise AurelExecValidationError(
                f"mode {self.execution_mode.value} cannot be available: only "
                "the existing safe bridge modes may carry "
                "AVAILABLE_FOR_EXISTING_BRIDGE",
                code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
                field="availability_status",
            )

    @property
    def profile_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class ExecutionModeRegistry(_ExecCanonicalMixin):
    """Closed-world execution mode registry. Total over ExecutionMode:
    an unclassified mode makes the registry unconstructible."""

    registry_id: str
    registry_version: str
    default_mode: ExecutionMode
    profiles: tuple[ExecutionModeProfile, ...]
    truth_label: ExecTruthLabel
    contract_version: str = EXECUTION_MODE_REGISTRY_VERSION
    registry_is_closed_world: bool = True
    unknown_mode_blocked: bool = True
    silent_fallback_allowed: bool = False
    grants_authority: bool = False
    executes: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "registry_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(self, "registry_version", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_false(self, "registry_is_closed_world", "unknown_mode_blocked")
        forbid_true(self, "silent_fallback_allowed", "grants_authority", "executes")
        covered = [profile.execution_mode for profile in self.profiles]
        if len(covered) != len(set(covered)):
            raise AurelExecValidationError(
                "a mode may carry exactly one profile in the registry",
                code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
                field="profiles",
            )
        missing = [mode for mode in ExecutionMode if mode not in covered]
        if missing:
            raise AurelExecValidationError(
                "registry must be total over ExecutionMode; missing: "
                + ", ".join(mode.value for mode in missing),
                code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
                field="profiles",
            )
        default_profile = self.profile_for(self.default_mode)
        if (
            default_profile.availability_status
            is not ExecutionModeAvailability.AVAILABLE_FOR_EXISTING_BRIDGE
        ):
            raise AurelExecValidationError(
                "default_mode must be an available mode",
                code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
                field="default_mode",
            )

    def profile_for(self, mode: ExecutionMode) -> ExecutionModeProfile:
        for profile in self.profiles:
            if profile.execution_mode is mode:
                return profile
        raise AurelExecValidationError(  # unreachable for a constructed registry
            f"no profile for mode {mode.value}",
            code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
            field="execution_mode",
        )

    def _modes_with(self, status: ExecutionModeAvailability) -> tuple[str, ...]:
        return tuple(
            profile.execution_mode.value
            for profile in self.profiles
            if profile.availability_status is status
        )

    @property
    def supported_modes(self) -> tuple[str, ...]:
        return self._modes_with(ExecutionModeAvailability.AVAILABLE_FOR_EXISTING_BRIDGE)

    @property
    def profile_only_modes(self) -> tuple[str, ...]:
        return self._modes_with(ExecutionModeAvailability.PROFILE_ONLY)

    @property
    def unavailable_modes(self) -> tuple[str, ...]:
        return self._modes_with(ExecutionModeAvailability.UNAVAILABLE)

    @property
    def blocked_modes(self) -> tuple[str, ...]:
        return self._modes_with(ExecutionModeAvailability.BLOCKED)

    @property
    def mode_profile_ids(self) -> tuple[str, ...]:
        return tuple(profile.profile_id for profile in self.profiles)

    @property
    def registry_hash(self) -> str:
        return stable_hash(self)


@dataclass(frozen=True)
class ModeCompatibilityDecision(_ExecCanonicalMixin):
    """Deterministic mode verdict. Not runtime success, not permission.

    ``allowed`` and ``blocked`` are structurally exclusive and exhaustive,
    and a decision claiming a silent fallback is unconstructible.
    """

    decision_id: str
    requested_execution_mode: str
    allowed: bool
    blocked: bool
    reason: str
    truth_label: ExecTruthLabel
    contract_version: str = MODE_COMPATIBILITY_DECISION_VERSION
    exec_job_id: str | None = None
    profile_id: str | None = None
    missing_requirements: tuple[str, ...] = ()
    unavailable_reason: str | None = None
    fallback_mode: str | None = None
    silent_fallback_used: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "decision_id", code=AurelExecErrorCode.EMPTY_FIELD)
        require_nonempty(
            self, "requested_execution_mode", code=AurelExecErrorCode.EMPTY_FIELD
        )
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "silent_fallback_used")
        if self.fallback_mode is not None:
            raise AurelExecValidationError(
                "a compatibility decision may not carry a fallback mode; "
                "unsupported modes are blocked, never redirected",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="fallback_mode",
            )
        if self.allowed == self.blocked:
            raise AurelExecValidationError(
                "a decision is exactly one of allowed or blocked",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="allowed",
            )
        if self.blocked and not (self.missing_requirements or self.reason.strip()):
            raise AurelExecValidationError(
                "a blocked decision must explain itself",
                code=AurelExecErrorCode.EMPTY_FIELD,
                field="reason",
            )

    @property
    def decision_hash(self) -> str:
        return stable_hash(self)


def _blocked(
    requested: str,
    reason: str,
    *,
    exec_job_id: str | None,
    profile_id: str | None = None,
    missing: tuple[str, ...] = (),
    unavailable_reason: str | None = None,
) -> ModeCompatibilityDecision:
    return ModeCompatibilityDecision(
        decision_id="exec-mode-dec-" + stable_hash((requested, reason, exec_job_id))[:16],
        requested_execution_mode=requested,
        allowed=False,
        blocked=True,
        reason=reason,
        truth_label=ExecTruthLabel.LIVE,
        exec_job_id=exec_job_id,
        profile_id=profile_id,
        missing_requirements=missing,
        unavailable_reason=unavailable_reason,
    )


def decide_mode_compatibility(
    registry: ExecutionModeRegistry,
    requested_mode: ExecutionMode | str,
    *,
    exec_job_id: str | None = None,
    tool_profile: "ToolExecutionProfile | None" = None,
    requested_tool_name: str | None = None,
    lease: "ExecutionLease | None" = None,
) -> ModeCompatibilityDecision:
    """Deterministically decide whether a requested mode may proceed.

    Pure function, no side effects. Unknown modes are blocked; PROFILE_ONLY,
    UNAVAILABLE, and BLOCKED modes are blocked with explicit reasons; TOOL
    mode is allowed only when the tool profile and lease scope context
    match. There is no fallback path of any kind.
    """
    if isinstance(requested_mode, str) and not isinstance(requested_mode, ExecutionMode):
        try:
            requested_mode = ExecutionMode(requested_mode)
        except ValueError:
            return _blocked(
                str(requested_mode), UNKNOWN_MODE_BLOCKED_REASON, exec_job_id=exec_job_id
            )
    profile = registry.profile_for(requested_mode)
    requested = requested_mode.value

    if profile.availability_status is ExecutionModeAvailability.BLOCKED:
        return _blocked(
            requested,
            f"mode {requested} is BLOCKED: {profile.unavailable_reason}",
            exec_job_id=exec_job_id,
            profile_id=profile.profile_id,
            unavailable_reason=profile.unavailable_reason,
        )
    if profile.availability_status is ExecutionModeAvailability.UNAVAILABLE:
        return _blocked(
            requested,
            f"mode {requested} is UNAVAILABLE: {profile.unavailable_reason}",
            exec_job_id=exec_job_id,
            profile_id=profile.profile_id,
            unavailable_reason=profile.unavailable_reason,
        )
    if profile.availability_status is ExecutionModeAvailability.PROFILE_ONLY:
        return _blocked(
            requested,
            f"mode {requested} is PROFILE_ONLY: modeled for future packs but "
            "not executable — no silent fallback to another mode",
            exec_job_id=exec_job_id,
            profile_id=profile.profile_id,
            unavailable_reason=profile.unavailable_reason,
        )
    if profile.availability_status is ExecutionModeAvailability.ERROR:
        return _blocked(
            requested,
            f"mode {requested} profile is in ERROR state",
            exec_job_id=exec_job_id,
            profile_id=profile.profile_id,
        )

    # AVAILABLE_FOR_EXISTING_BRIDGE (structurally TOOL-only): context checks
    missing: list[str] = []
    if tool_profile is None:
        missing.append("tool_profile")
    else:
        if requested_tool_name is None:
            missing.append("requested_tool_name")
        elif requested_tool_name not in tool_profile.allowed_tool_names:
            missing.append(
                f"tool {requested_tool_name!r} not in allowed read-only tools "
                f"{tool_profile.allowed_tool_names}"
            )
    if lease is not None:
        if lease.scope.allowed_execution_mode is not requested_mode:
            missing.append(
                f"lease scope binds mode {lease.scope.allowed_execution_mode.value}"
            )
        if (
            requested_tool_name is not None
            and lease.scope.allowed_tool_name is not None
            and lease.scope.allowed_tool_name != requested_tool_name
        ):
            missing.append(
                f"lease scope binds tool {lease.scope.allowed_tool_name!r}"
            )
    if missing:
        return _blocked(
            requested,
            f"mode {requested} is available only for the existing safe "
            "bridge path and the request context does not match",
            exec_job_id=exec_job_id,
            profile_id=profile.profile_id,
            missing=tuple(missing),
        )
    return ModeCompatibilityDecision(
        decision_id="exec-mode-dec-"
        + stable_hash((requested, requested_tool_name, exec_job_id))[:16],
        requested_execution_mode=requested,
        allowed=True,
        blocked=False,
        reason=(
            f"mode {requested} allowed for the existing safe read-only "
            "ExecRuntimeBridge path only; every lease/session/claim/bridge "
            "guard still applies — allowed is not runtime success"
        ),
        truth_label=ExecTruthLabel.LIVE,
        exec_job_id=exec_job_id,
        profile_id=profile.profile_id,
    )


def enforce_mode_compatibility_before_claim(
    decision: ModeCompatibilityDecision, entry: ExecQueueEntry
) -> ExecQueueEntry:
    """Narrow queue hook: block the queue entry when the mode is blocked.

    Uses the existing P4-EXEC-C ``block_queue_entry`` helper unchanged;
    an allowed decision returns the entry untouched. No fallback occurs.
    """
    if decision.blocked:
        return block_queue_entry(entry)
    return entry


def require_mode_compatibility(decision: ModeCompatibilityDecision) -> None:
    """Raise fail-closed when a blocked mode tries to proceed."""
    if decision.blocked:
        raise AurelExecValidationError(
            f"execution blocked by mode compatibility: {decision.reason}",
            code=AurelExecErrorCode.UNSUPPORTED_EXECUTION_MODE,
            field="requested_execution_mode",
        )


@dataclass(frozen=True)
class NoSilentFallbackProof(_ExecCanonicalMixin):
    """Evidence that unsupported modes block instead of falling back."""

    reason: str
    contract_version: str = NO_SILENT_FALLBACK_PROOF_VERSION
    silent_fallback_allowed: bool = False
    unknown_mode_blocked: bool = True
    registry_is_closed_world: bool = True

    def __post_init__(self) -> None:
        forbid_true(self, "silent_fallback_allowed")
        forbid_false(self, "unknown_mode_blocked", "registry_is_closed_world")
        require_nonempty(self, "reason", code=AurelExecErrorCode.EMPTY_FIELD)


def build_no_silent_fallback_proof() -> NoSilentFallbackProof:
    return NoSilentFallbackProof(reason=SILENT_FALLBACK_FORBIDDEN_REASON)
