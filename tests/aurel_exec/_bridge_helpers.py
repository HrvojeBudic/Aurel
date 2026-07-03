"""Shared P4-EXEC-B test helpers: bound-object builders and a recording
fake kernel whose submit surface matches AgenticRuntime.submit exactly."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentic_runtime.aurel_exec import (
    ExecRuntimeBridge,
    ExecutionMode,
    RuntimeBridgeSubmitRequest,
    bind_lease_to_job,
    bind_session_to_job,
    build_dev_fixture_admission_request,
    build_runtime_bridge_submit_request,
    create_exec_job,
    create_execution_attempt,
    decide_admission,
    issue_execution_lease,
    open_execution_session,
)
from agentic_runtime.aurel_flow.types import stable_hash
from agentic_runtime.core_types import (
    ObservationEnvelope,
    PolicyVerdict,
    VerifierResult,
)
from agentic_runtime.policy import PolicyDecision
from agentic_runtime.core_types import RiskLevel

DEMO_PATH = "notes/hello.txt"
DEMO_ARGS = {"path": DEMO_PATH}
ISSUER_CARD_ID = "card_bridge_test"


@dataclass
class _FakeCard:
    id: str = ISSUER_CARD_ID


@dataclass
class _FakeTransition:
    id: str = "txn_fake_0001"
    entry_hash: str = "deadbeef" * 8


@dataclass
class _FakeCommandResult:
    observation: ObservationEnvelope
    verifier: VerifierResult
    decision: PolicyDecision
    transition: _FakeTransition | None
    rolled_back: bool = False


@dataclass
class RecordingFakeRuntime:
    """Same submit(cmd, card) surface as AgenticRuntime; records calls."""

    succeed: bool = True
    with_transition: bool = True
    submit_calls: list[Any] = field(default_factory=list)

    def submit(self, cmd: Any, card: Any) -> _FakeCommandResult:
        self.submit_calls.append((cmd, card))
        obs = ObservationEnvelope.make(
            cmd.id,
            success=self.succeed,
            stdout="fake file content" if self.succeed else "",
            stderr="" if self.succeed else "tool_exception: FileNotFoundError",
        )
        verifier = VerifierResult(self.succeed, "none")
        decision = PolicyDecision(PolicyVerdict.ALLOW, RiskLevel.LOW, [])
        transition = _FakeTransition() if self.with_transition else None
        return _FakeCommandResult(obs, verifier, decision, transition)


def build_bound_slice(*, expires_at_tick: int | None = 100):
    """DEV_FIXTURE candidate -> ADMIT -> lease -> job -> session -> attempt,
    fully bound and ready for the bridge."""
    request = build_dev_fixture_admission_request(
        requested_tool_name="read_file",
        requested_args_hash=stable_hash(DEMO_ARGS),
    )
    decision = decide_admission(request)
    job = create_exec_job(
        decision,
        source_p3_candidate_ref=request.source_p3_candidate_ref,
        requested_execution_mode=ExecutionMode.TOOL,
        requested_tool_name="read_file",
    )
    lease = issue_execution_lease(
        decision,
        request,
        exec_job_id=job.exec_job_id,
        issued_at_tick=1,
        expires_at_tick=expires_at_tick,
    )
    job = bind_lease_to_job(job, lease)
    session = open_execution_session(job, opened_at_tick=2)
    job = bind_session_to_job(job, session)
    attempt, _ = create_execution_attempt(
        job, lease, current_tick=3, session_id=session.session_id
    )
    return request, decision, job, lease, session, attempt


def build_bridge_request(
    job, lease, session, attempt, **overrides
) -> RuntimeBridgeSubmitRequest:
    values: dict[str, Any] = {
        "issuer_card_id": ISSUER_CARD_ID,
        "requested_tool_name": "read_file",
        "requested_execution_mode": ExecutionMode.TOOL,
        "command_args": (("path", DEMO_PATH),),
    }
    values.update(overrides)
    return build_runtime_bridge_submit_request(
        job=job, lease=lease, session=session, attempt=attempt, **values
    )


def bridge_with_fake(**fake_kwargs):
    fake = RecordingFakeRuntime(**fake_kwargs)
    return ExecRuntimeBridge(fake), fake, _FakeCard()
