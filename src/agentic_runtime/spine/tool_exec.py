"""SPINE-LIVE-1 — governed mutating execution path (write + test).

The sealed P4-EXEC-D ``ToolExecutionProfile`` deliberately keeps mutating tools
*unconstructible* through the read-only bridge, and 285 tests guard that
invariant. We do **not** weaken it. Instead this module opens a new, honest
wormhole in the spine layer: a lease-scoped, hard-isolation-gated mutating path
that reuses the proven ``AgenticRuntime.submit`` kernel (the same syscall
``entity.py`` already drives for ``write_file`` / ``run_tests``) and produces a
``LIVE-with-evidence`` ref per submit.

The security-critical rule: a mutating spine tool may submit **only** when the
sandbox is hard-isolated. No hard isolation → fail-closed ``SpineExecutionBlocked``.
Nothing here grants authority or permission; the runtime still disposes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from ..core_types import (
    CommandEnvelope,
    RiskLevel,
    canonical_json,
    new_id,
    now,
    sha,
)
from .live_evidence import LiveEvidenceLabel

MUTATING_SPINE_TOOLS: tuple[str, ...] = ("write_file", "run_tests")

TOOL_EXEC_LEASE_VERSION = "spine_tool_exec_lease.v1"
HARD_ISOLATION_EVIDENCE_VERSION = "hard_isolation_evidence.v1"
TOOL_EXEC_EVIDENCE_VERSION = "spine_tool_exec_evidence.v1"
TOOL_EXEC_RUN_VERSION = "spine_tool_exec_run.v1"

HARD_ISOLATION_REQUIRED_REASON = (
    "a mutating spine tool requires a hard-isolated sandbox "
    "(is_hard_isolated and is_security_boundary); UnsafeLocalSandbox is never "
    "the write path"
)


class SpineExecutionBlocked(RuntimeError):
    """Fail-closed block before any kernel call. A block performs nothing."""


def args_hash(tool: str, args: Mapping[str, Any]) -> str:
    """Stable hash binding a tool to its exact arguments."""
    return sha(tool, canonical_json(dict(args)))


# --------------------------------------------------------------------------- #
#  Hard-isolation evidence — the security gate for mutating tools
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class HardIsolationEvidenceRef:
    """Proof the sandbox is a real isolation boundary. Never authority."""

    evidence_id: str
    contract_version: str
    sandbox_mode: str
    is_hard_isolated: bool
    is_security_boundary: bool
    produced_at: float

    @property
    def available(self) -> bool:
        return self.is_hard_isolated and self.is_security_boundary

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "contract_version": self.contract_version,
            "sandbox_mode": self.sandbox_mode,
            "is_hard_isolated": self.is_hard_isolated,
            "is_security_boundary": self.is_security_boundary,
            "produced_at": self.produced_at,
            "available": self.available,
        }


def capture_hard_isolation_evidence(sandbox: Any) -> HardIsolationEvidenceRef:
    mode = getattr(sandbox, "mode", None)
    return HardIsolationEvidenceRef(
        evidence_id=new_id("hiso"),
        contract_version=HARD_ISOLATION_EVIDENCE_VERSION,
        sandbox_mode=getattr(mode, "value", str(mode)),
        is_hard_isolated=bool(getattr(sandbox, "is_hard_isolated", False)),
        is_security_boundary=bool(getattr(sandbox, "is_security_boundary", False)),
        produced_at=now(),
    )


# --------------------------------------------------------------------------- #
#  Lease — binds a declared, ordered (tool, args) sequence
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ToolExecLease:
    """One lease authorizing a declared ordered (tool, args-hash) sequence.

    A lease is scope, not authority. It binds *which* tool with *which* exact
    args may submit, requires hard isolation for the mutating path, and expires.
    """

    lease_id: str
    session_id: str
    contract_version: str
    bound_steps: tuple[tuple[str, str], ...]
    issued_at_tick: int
    expires_at_tick: int
    requires_hard_isolation: bool = True
    authority_granted: bool = False
    permission_granted: bool = False

    def permits(self, tool: str, tool_args_hash: str, current_tick: int) -> bool:
        if current_tick > self.expires_at_tick:
            return False
        return (tool, tool_args_hash) in self.bound_steps

    def to_dict(self) -> dict:
        return {
            "lease_id": self.lease_id,
            "session_id": self.session_id,
            "contract_version": self.contract_version,
            "bound_steps": [list(s) for s in self.bound_steps],
            "issued_at_tick": self.issued_at_tick,
            "expires_at_tick": self.expires_at_tick,
            "requires_hard_isolation": self.requires_hard_isolation,
            "authority_granted": self.authority_granted,
            "permission_granted": self.permission_granted,
        }


# --------------------------------------------------------------------------- #
#  Per-submit evidence — LIVE only when a real kernel submit happened
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ToolExecEvidenceRef:
    """Proof one governed mutating submit happened. LIVE-with-evidence."""

    exec_id: str
    contract_version: str
    tool: str
    tool_args_hash: str
    command_id: str
    before_state_hash: str
    after_state_hash: str
    success: bool
    runtime_submit_called: bool
    verifier_passed: bool
    rolled_back: bool
    label: LiveEvidenceLabel
    blocked_reason: str = ""
    authority_granted: bool = False
    permission_granted: bool = False

    @property
    def available(self) -> bool:
        return (
            self.label is LiveEvidenceLabel.LIVE
            and self.runtime_submit_called
            and bool(self.command_id)
        )

    def to_dict(self) -> dict:
        return {
            "exec_id": self.exec_id,
            "contract_version": self.contract_version,
            "tool": self.tool,
            "tool_args_hash": self.tool_args_hash,
            "command_id": self.command_id,
            "before_state_hash": self.before_state_hash,
            "after_state_hash": self.after_state_hash,
            "success": self.success,
            "runtime_submit_called": self.runtime_submit_called,
            "verifier_passed": self.verifier_passed,
            "rolled_back": self.rolled_back,
            "label": self.label.value,
            "blocked_reason": self.blocked_reason,
            "available": self.available,
        }


@dataclass(frozen=True)
class SpineToolExecRun:
    """Outcome of a multi-step run under one lease."""

    run_id: str
    contract_version: str
    session_id: str
    lease_id: str
    step_evidence: tuple[ToolExecEvidenceRef, ...]
    hard_isolation: HardIsolationEvidenceRef
    success: bool
    reverted: bool

    @property
    def execution_available(self) -> bool:
        """True only if every recorded step is a real, available submit."""
        return bool(self.step_evidence) and all(
            e.available for e in self.step_evidence
        )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "contract_version": self.contract_version,
            "session_id": self.session_id,
            "lease_id": self.lease_id,
            "step_evidence": [e.to_dict() for e in self.step_evidence],
            "hard_isolation": self.hard_isolation.to_dict(),
            "success": self.success,
            "reverted": self.reverted,
            "execution_available": self.execution_available,
        }


@dataclass
class SpineToolExecSession:
    """A governed multi-step mutating session over the real runtime kernel."""

    runtime: Any
    card: Any
    sandbox: Any = None
    _session_id: str = field(default_factory=lambda: new_id("stex"))

    def __post_init__(self) -> None:
        if self.sandbox is None:
            self.sandbox = self.runtime.tools.sandbox

    @property
    def session_id(self) -> str:
        return self._session_id

    def issue_lease(
        self,
        steps: Sequence[tuple[str, Mapping[str, Any]]],
        *,
        issued_at_tick: int = 0,
        ttl_ticks: int = 1_000_000,
    ) -> ToolExecLease:
        bound = tuple((tool, args_hash(tool, args)) for tool, args in steps)
        return ToolExecLease(
            lease_id=new_id("stlease"),
            session_id=self._session_id,
            contract_version=TOOL_EXEC_LEASE_VERSION,
            bound_steps=bound,
            issued_at_tick=issued_at_tick,
            expires_at_tick=issued_at_tick + ttl_ticks,
        )

    def _gate(self, tool: str, tool_args_hash: str, lease: ToolExecLease,
              current_tick: int) -> None:
        if not lease.permits(tool, tool_args_hash, current_tick):
            raise SpineExecutionBlocked(
                f"lease {lease.lease_id} does not permit {tool!r} with the "
                "given args at this tick"
            )
        if tool in MUTATING_SPINE_TOOLS:
            iso = capture_hard_isolation_evidence(self.sandbox)
            if not iso.available:
                raise SpineExecutionBlocked(HARD_ISOLATION_REQUIRED_REASON)

    def submit_step(
        self,
        tool: str,
        args: Mapping[str, Any],
        lease: ToolExecLease,
        *,
        current_tick: int = 0,
        risk: RiskLevel = RiskLevel.MEDIUM,
    ) -> ToolExecEvidenceRef:
        """Gate, then call ``AgenticRuntime.submit`` once. Fail-closed on gate."""
        a_hash = args_hash(tool, args)
        self._gate(tool, a_hash, lease, current_tick)

        cmd = CommandEnvelope.make(
            issuer_card_id=self.card.id,
            tool=tool,
            args=dict(args),
            rationale="SPINE-LIVE-1 governed mutating submit",
            declared_risk=risk,
            expected_effect=f"governed {tool} through the runtime kernel",
        )
        res = self.runtime.submit(cmd, self.card)
        transition = res.transition
        return ToolExecEvidenceRef(
            exec_id=new_id("stev"),
            contract_version=TOOL_EXEC_EVIDENCE_VERSION,
            tool=tool,
            tool_args_hash=a_hash,
            command_id=cmd.id,
            before_state_hash=transition.before_state_hash if transition else "",
            after_state_hash=transition.after_state_hash if transition else "",
            success=res.ok,
            runtime_submit_called=True,
            verifier_passed=bool(res.verifier and res.verifier.passed),
            rolled_back=bool(res.rolled_back),
            label=LiveEvidenceLabel.LIVE,
        )

    def run(
        self,
        lease: ToolExecLease,
        steps: Sequence[tuple[str, Mapping[str, Any]]],
        *,
        current_tick: int = 0,
        revert_on_failure: bool = True,
    ) -> SpineToolExecRun:
        """Run declared steps in order; stop on first failure and optionally
        revert prior writes with compensating governed writes."""
        iso = capture_hard_isolation_evidence(self.sandbox)
        evidence: list[ToolExecEvidenceRef] = []
        # (path, original_content_or_None) captured before each write for revert
        revert_stack: list[tuple[str, str | None]] = []
        success = True
        reverted = False

        for tool, args in steps:
            if revert_on_failure and tool == "write_file":
                path = str(args.get("path", ""))
                revert_stack.append((path, self._read_original(path)))
            ev = self.submit_step(tool, args, lease, current_tick=current_tick)
            evidence.append(ev)
            if not ev.success:
                success = False
                if revert_on_failure and revert_stack:
                    reverted = self._revert(revert_stack)
                break

        return SpineToolExecRun(
            run_id=new_id("strun"),
            contract_version=TOOL_EXEC_RUN_VERSION,
            session_id=self._session_id,
            lease_id=lease.lease_id,
            step_evidence=tuple(evidence),
            hard_isolation=iso,
            success=success,
            reverted=reverted,
        )

    def _read_original(self, path: str) -> str | None:
        if not path:
            return None
        try:
            return self.sandbox.read_file(path)
        except (OSError, PermissionError, KeyError, AttributeError):
            return None

    def _revert(self, revert_stack: Iterable[tuple[str, str | None]]) -> bool:
        """Restore original file contents via governed compensating writes.

        A file that did not exist before (original is None) cannot be un-created
        without a delete tool; such entries make the revert honest-partial and
        the run reports ``reverted=False``.
        """
        all_restored = True
        for path, original in reversed(list(revert_stack)):
            if original is None:
                all_restored = False
                continue
            cmd = CommandEnvelope.make(
                issuer_card_id=self.card.id,
                tool="write_file",
                args={"path": path, "content": original},
                rationale="SPINE-LIVE-1 compensating revert",
                declared_risk=RiskLevel.MEDIUM,
                expected_effect=f"restore original content of {path}",
            )
            res = self.runtime.submit(cmd, self.card)
            if not res.ok:
                all_restored = False
        return all_restored
