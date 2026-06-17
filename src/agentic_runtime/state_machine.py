"""Runtime execution state machine with legal transitions (P0.7)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core_types import (
    ExecutionStatus,
    RuntimeStatusTransitionRecord,
)
from .trace import TraceLedgerBackend


_FINAL = {
    ExecutionStatus.REJECTED,
    ExecutionStatus.NEEDS_HUMAN,
    ExecutionStatus.INVALID_PLAN,
    ExecutionStatus.HALTED,
    ExecutionStatus.FAILED,
    ExecutionStatus.VERIFICATION_FAILED,
    ExecutionStatus.PARTIALLY_COMPLETED,
    ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION,
    ExecutionStatus.COMPLETED,
}

_LEGAL: dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.CREATED: {
        ExecutionStatus.PLANNING,
        ExecutionStatus.HALTED,
    },
    ExecutionStatus.PLANNING: {
        ExecutionStatus.PLANNED,
        ExecutionStatus.INVALID_PLAN,
        ExecutionStatus.HALTED,
    },
    ExecutionStatus.PLANNED: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.HALTED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.REJECTED,
        ExecutionStatus.NEEDS_HUMAN,
        ExecutionStatus.HALTED,
        ExecutionStatus.FAILED,
        ExecutionStatus.VERIFICATION_FAILED,
        ExecutionStatus.PARTIALLY_COMPLETED,
        ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION,
        ExecutionStatus.COMPLETED,
    },
    ExecutionStatus.PARTIALLY_COMPLETED: {
        ExecutionStatus.NEEDS_HUMAN,
        ExecutionStatus.FAILED_WITH_PARTIAL_EXECUTION,
        ExecutionStatus.HALTED,
    },
}


@dataclass
class RuntimeStateMachine:
    trace: TraceLedgerBackend
    run_id: str
    intent_id: str
    agent_id: str
    status: ExecutionStatus = ExecutionStatus.CREATED
    last_transition_id: str = ""

    def __post_init__(self) -> None:
        rec = RuntimeStatusTransitionRecord.make(
            run_id=self.run_id,
            intent_id=self.intent_id,
            issuer_card_id=self.agent_id,
            from_status=self.status.value,
            to_status=self.status.value,
            reason_code="run_created",
            message="execution created",
        )
        self.trace.append_status_transition(rec)
        self.last_transition_id = rec.id

    def transition(
        self,
        to_status: ExecutionStatus,
        reason_code: str,
        message: str,
        *,
        evidence_refs: Optional[list[str]] = None,
        details: Optional[dict] = None,
        command_hash: Optional[str] = None,
        observation_hash: Optional[str] = None,
        verifier_hash: Optional[str] = None,
    ) -> RuntimeStatusTransitionRecord:
        self._ensure_legal(to_status)
        rec = RuntimeStatusTransitionRecord.make(
            run_id=self.run_id,
            intent_id=self.intent_id,
            issuer_card_id=self.agent_id,
            from_status=self.status.value,
            to_status=to_status.value,
            reason_code=reason_code,
            message=message,
            evidence_refs=evidence_refs or [],
            details=details or {},
            command_hash=command_hash,
            observation_hash=observation_hash,
            verifier_hash=verifier_hash,
        )
        self.trace.append_status_transition(rec)
        self.status = to_status
        self.last_transition_id = rec.id
        return rec

    @property
    def is_final(self) -> bool:
        return self.status in _FINAL

    def _ensure_legal(self, to_status: ExecutionStatus) -> None:
        if self.status in _FINAL:
            raise ValueError(
                f"illegal runtime state transition: final '{self.status.value}' -> '{to_status.value}'"
            )
        allowed = _LEGAL.get(self.status, set())
        if to_status not in allowed:
            raise ValueError(
                f"illegal runtime state transition: '{self.status.value}' -> '{to_status.value}'"
            )
