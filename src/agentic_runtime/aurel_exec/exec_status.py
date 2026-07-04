"""P4-EXEC-G ExecStatusReadModel / projection aggregator / CLI-Shell binding.

The single operator-facing read model for AurelExec execution state,
aggregated read-only from the P4-A…F objects. Missing categories become
honest UNAVAILABLE-with-reason entries, never fake LIVE. The aggregator
never calls the bridge or the kernel, never retries/recovers/rolls back,
never writes trace, and never enforces policy — projection is not control.

The CLI/Shell surface here is a **binding contract**: a closed-world
read-only command vocabulary plus a deterministic renderer over the status
read model (mirroring the proven P3 flow-CLI shape). The ``exec status`` CLI
command is wired read-only via ``cli_modules/exec_commands.py``. Shell UI
remains UNAVAILABLE (P2 owns it).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exec_errors import AurelExecErrorCode, AurelExecValidationError
from .exec_types import (
    ExecTruthLabel,
    ExecutionMode,
    _ExecCanonicalMixin,
    forbid_false,
    forbid_true,
    require_nonempty,
    stable_hash,
)

EXEC_STATUS_READ_MODEL_VERSION = "exec_status_read_model.v1"
SHELL_BINDING_CONTRACT_VERSION = "exec_shell_binding_contract.v1"
EXEC_CLI_STATUS_BINDING_VERSION = "exec_cli_status_binding.v1"

CLI_WIRING_UNAVAILABLE_REASON = (
    "the read-only CLI/status binding contract is implemented and tested, "
    "but live wiring into the agentic_runtime CLI is deliberately not "
    "performed in the seal pack — surface registration follows the proven "
    "flow-CLI pattern as a follow-up or lands with the P2 Shell binding"
)
CLI_WIRING_AVAILABLE_REASON = (
    "read-only exec status wired via agentic_runtime.cli exec status; "
    "projection is not control"
)
SHELL_UI_UNAVAILABLE_REASON = (
    "no Shell UI, React frontend, or API server exists for AurelExec; "
    "operator UI projection belongs to P2 AurelShell"
)
STATUS_CATEGORY_UNAVAILABLE_REASON = (
    "no object of this category was provided to the aggregator; the state "
    "is honestly UNAVAILABLE, never fabricated"
)

# The P4-A…F state categories every status read model must carry.
STATUS_CATEGORIES: tuple[str, ...] = (
    "admission_state",
    "lease_state",
    "job_state",
    "attempt_state",
    "session_state",
    "queue_state",
    "worker_state",
    "checkpoint_state",
    "rollback_ref_state",
    "local_message_state",
    "mode_state",
    "tool_profile_state",
    "model_profile_state",
    "terminal_profile_state",
    "code_profile_state",
    "runtime_submit_state",
    "outcome_state",
    "trace_binding_state",
    "verification_state",
    "failure_state",
    "recovery_state",
    "algedonic_state",
    "topology_state",
    "pressure_state",
    "backpressure_state",
    "telemetry_state",
)

_UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ExecStatusReadModel(_ExecCanonicalMixin):
    """One read-only operator view over the full P4 stack.

    Every category in ``STATUS_CATEGORIES`` is a string state value;
    missing inputs yield ``UNAVAILABLE`` with a reason recorded in
    ``unavailable_reasons``. Mutation/verification/enforcement claims are
    structurally unconstructible.
    """

    status_read_model_id: str
    projection_version: str
    categories: tuple[tuple[str, str], ...]
    truth_labels: tuple[ExecTruthLabel, ...]
    unavailable_reasons: tuple[tuple[str, str], ...]
    contract_version: str = EXEC_STATUS_READ_MODEL_VERSION
    exec_job_id: str | None = None
    attempt_id: str | None = None
    session_id: str | None = None
    created_at_tick: int | None = None
    mutates_runtime: bool = False
    executes: bool = False
    verifies_trace: bool = False
    enforces_policy: bool = False
    grants_authority: bool = False
    shell_ui_available: bool = False
    read_only: bool = True

    def __post_init__(self) -> None:
        require_nonempty(
            self, "status_read_model_id", code=AurelExecErrorCode.EMPTY_FIELD
        )
        forbid_true(
            self,
            "mutates_runtime",
            "executes",
            "verifies_trace",
            "enforces_policy",
            "grants_authority",
            "shell_ui_available",
        )
        forbid_false(self, "read_only")
        covered = [name for name, _ in self.categories]
        if covered != list(STATUS_CATEGORIES):
            raise AurelExecValidationError(
                "status read model must cover every P4-A..F category exactly "
                "once, in canonical order",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="categories",
            )
        for name, value in self.categories:
            if not value.strip():
                raise AurelExecValidationError(
                    f"category {name} must carry a state value",
                    code=AurelExecErrorCode.EMPTY_FIELD,
                    field="categories",
                )
        unavailable_names = {name for name, _ in self.unavailable_reasons}
        for name, value in self.categories:
            if value == _UNAVAILABLE and name not in unavailable_names:
                raise AurelExecValidationError(
                    f"UNAVAILABLE category {name} must carry a reason",
                    code=AurelExecErrorCode.EMPTY_FIELD,
                    field="unavailable_reasons",
                )
        if "TRACE_VERIFIED" in {value for _, value in self.categories}:
            raise AurelExecValidationError(
                "no status category may claim TRACE_VERIFIED before P5",
                code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                field="categories",
            )

    @property
    def status_hash(self) -> str:
        return stable_hash(self)

    def category(self, name: str) -> str:
        for category_name, value in self.categories:
            if category_name == name:
                return value
        raise AurelExecValidationError(
            f"unknown status category {name!r}",
            code=AurelExecErrorCode.ERROR,
            field="categories",
        )


def _enum_value(obj: Any, attribute: str) -> str | None:
    value = getattr(obj, attribute, None)
    if value is None:
        return None
    return getattr(value, "value", str(value))


def build_exec_status_read_model(
    *,
    admission_decision: Any = None,
    lease: Any = None,
    lease_validation: Any = None,
    job: Any = None,
    attempt: Any = None,
    session: Any = None,
    queue_entry: Any = None,
    worker_slot: Any = None,
    claim: Any = None,
    checkpoint_refs: tuple[Any, ...] = (),
    rollback_refs: tuple[Any, ...] = (),
    message_log: Any = None,
    mode_decision: Any = None,
    mode_registry: Any = None,
    outcome: Any = None,
    trace_binding: Any = None,
    verification_decision: Any = None,
    failure_classification: Any = None,
    recovery_plan: Any = None,
    algedonic_signal: Any = None,
    topology: Any = None,
    pressure_snapshot: Any = None,
    backpressure_decision: Any = None,
    telemetry_snapshot: Any = None,
    created_at_tick: int | None = None,
) -> ExecStatusReadModel:
    """The ExecProjectionAggregator: aggregate P4-A…F objects read-only.

    Pure function over the provided objects. Every missing optional input
    becomes an honest UNAVAILABLE category with a reason. Nothing here
    calls the bridge, the kernel, or any mutating helper.
    """
    unavailable: list[tuple[str, str]] = []
    labels: list[ExecTruthLabel] = []

    def _label(obj: Any) -> None:
        obj_label = getattr(obj, "truth_label", None)
        if obj_label is not None and obj_label not in labels:
            labels.append(obj_label)

    def _state(name: str, obj: Any, value: str | None) -> tuple[str, str]:
        if obj is None or value is None:
            unavailable.append((name, STATUS_CATEGORY_UNAVAILABLE_REASON))
            return (name, _UNAVAILABLE)
        _label(obj)
        return (name, value)

    lease_state = None
    if lease is not None:
        if lease_validation is not None:
            lease_state = (
                "LEASE_REVOKED"
                if lease_validation.revoked
                else "LEASE_EXPIRED"
                if lease_validation.expired
                else "LEASE_VALID"
            )
        else:
            lease_state = "LEASE_REVOKED" if lease.revoked else "LEASE_PRESENT"

    submit_state = None
    if attempt is not None:
        submit_state = (
            "SUBMITTED_ONCE" if attempt.runtime_submit_called else "NOT_SUBMITTED"
        )

    trace_state = None
    if trace_binding is not None:
        trace_state = "TRACE_BOUND" if trace_binding.trace_bound else "TRACE_UNBOUND"

    checkpoint_state = None
    if checkpoint_refs:
        checkpoint_state = f"CHECKPOINT_REFS_{len(checkpoint_refs)}"
    rollback_state = None
    if rollback_refs:
        rollback_state = "ROLLBACK_REF_NOT_EXECUTED"
    message_state = None
    if message_log is not None:
        message_state = f"LOCAL_MESSAGES_{len(message_log.messages)}"

    categories = (
        _state("admission_state", admission_decision, _enum_value(admission_decision, "state")),
        _state("lease_state", lease, lease_state),
        _state("job_state", job, _enum_value(job, "lifecycle_state")),
        _state("attempt_state", attempt, _enum_value(attempt, "lifecycle_state")),
        _state("session_state", session, _enum_value(session, "status")),
        _state("queue_state", queue_entry, _enum_value(queue_entry, "queue_state")),
        _state("worker_state", worker_slot, _enum_value(worker_slot, "status")),
        _state("checkpoint_state", checkpoint_refs or None, checkpoint_state),
        _state("rollback_ref_state", rollback_refs or None, rollback_state),
        _state("local_message_state", message_log, message_state),
        _state(
            "mode_state",
            mode_decision,
            None
            if mode_decision is None
            else ("MODE_ALLOWED" if mode_decision.allowed else "MODE_BLOCKED"),
        ),
        _state(
            "tool_profile_state",
            mode_registry,
            None
            if mode_registry is None
            else mode_registry.profile_for(ExecutionMode.TOOL).availability_status.value,
        ),
        _state(
            "model_profile_state",
            mode_registry,
            None
            if mode_registry is None
            else mode_registry.profile_for(ExecutionMode.MODEL).availability_status.value,
        ),
        _state(
            "terminal_profile_state",
            mode_registry,
            None
            if mode_registry is None
            else mode_registry.profile_for(ExecutionMode.TERMINAL).availability_status.value,
        ),
        _state(
            "code_profile_state",
            mode_registry,
            None
            if mode_registry is None
            else mode_registry.profile_for(ExecutionMode.CODE).availability_status.value,
        ),
        _state("runtime_submit_state", attempt, submit_state),
        _state("outcome_state", outcome, _enum_value(outcome, "runtime_status")),
        _state("trace_binding_state", trace_binding, trace_state),
        _state(
            "verification_state",
            verification_decision,
            _enum_value(verification_decision, "verification_status"),
        ),
        _state(
            "failure_state",
            failure_classification,
            _enum_value(failure_classification, "failure_class"),
        ),
        _state(
            "recovery_state",
            recovery_plan,
            _enum_value(recovery_plan, "recommended_action"),
        ),
        _state(
            "algedonic_state", algedonic_signal, _enum_value(algedonic_signal, "severity")
        ),
        _state("topology_state", topology, _enum_value(topology, "topology_kind")),
        _state(
            "pressure_state",
            pressure_snapshot,
            _enum_value(pressure_snapshot, "pressure_level"),
        ),
        _state(
            "backpressure_state",
            backpressure_decision,
            _enum_value(backpressure_decision, "decision"),
        ),
        _state(
            "telemetry_state",
            telemetry_snapshot,
            None if telemetry_snapshot is None else "TELEMETRY_BOUND",
        ),
    )
    return ExecStatusReadModel(
        status_read_model_id="exec-status-"
        + stable_hash(tuple(value for _, value in categories))[:16],
        projection_version=EXEC_STATUS_READ_MODEL_VERSION,
        categories=categories,
        truth_labels=tuple(labels) or (ExecTruthLabel.UNAVAILABLE,),
        unavailable_reasons=tuple(unavailable),
        exec_job_id=getattr(job, "exec_job_id", None),
        attempt_id=getattr(attempt, "attempt_id", None),
        session_id=getattr(session, "session_id", None),
        created_at_tick=created_at_tick,
    )


class ExecCliCommandKind(str, Enum):
    """Closed-world read-only CLI vocabulary. There is no SUBMIT/RUN/RETRY/
    RECOVER/ROLLBACK/APPROVE/MUTATE/VERIFY/ENFORCE member — mutating
    commands are unconstructible."""

    STATUS = "STATUS"
    COVERAGE = "COVERAGE"
    HANDOFF = "HANDOFF"
    SEAL = "SEAL"


@dataclass(frozen=True)
class ShellBindingContract(_ExecCanonicalMixin):
    """What a future Shell/CLI surface may bind. A contract, not a UI."""

    contract_id: str
    supported_commands: tuple[str, ...]
    truth_label: ExecTruthLabel
    contract_version: str = SHELL_BINDING_CONTRACT_VERSION
    read_only: bool = True
    cli_wiring_available: bool = False
    cli_wiring_unavailable_reason: str = CLI_WIRING_UNAVAILABLE_REASON
    shell_ui_available: bool = False
    shell_ui_unavailable_reason: str = SHELL_UI_UNAVAILABLE_REASON
    mutates_runtime: bool = False
    api_server_available: bool = False
    react_frontend_available: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "contract_id", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_false(self, "read_only")
        forbid_true(
            self,
            "shell_ui_available",
            "mutates_runtime",
            "api_server_available",
            "react_frontend_available",
        )
        if self.cli_wiring_available:
            if self.cli_wiring_unavailable_reason.strip():
                raise AurelExecValidationError(
                    "wired CLI binding must not carry an unavailable reason",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="cli_wiring_unavailable_reason",
                )
        else:
            require_nonempty(
                self,
                "cli_wiring_unavailable_reason",
                code=AurelExecErrorCode.EMPTY_FIELD,
            )
        allowed = {kind.value for kind in ExecCliCommandKind}
        for command in self.supported_commands:
            if command not in allowed:
                raise AurelExecValidationError(
                    f"command {command!r} is outside the closed-world "
                    "read-only vocabulary",
                    code=AurelExecErrorCode.FORBIDDEN_BOUNDARY_CLAIM,
                    field="supported_commands",
                )


def build_shell_binding_contract(
    *,
    cli_wiring_available: bool = True,
) -> ShellBindingContract:
    return ShellBindingContract(
        contract_id="exec-shell-binding-"
        + stable_hash(tuple(kind.value for kind in ExecCliCommandKind))[:16],
        supported_commands=tuple(kind.value for kind in ExecCliCommandKind),
        truth_label=ExecTruthLabel.LIVE,
        cli_wiring_available=cli_wiring_available,
        cli_wiring_unavailable_reason=(
            "" if cli_wiring_available else CLI_WIRING_UNAVAILABLE_REASON
        ),
    )


@dataclass(frozen=True)
class ExecCliStatusResponse(_ExecCanonicalMixin):
    """One deterministic read-only CLI response. Rendering mutates nothing."""

    command_kind: ExecCliCommandKind
    rendered_output: str
    truth_label: ExecTruthLabel
    contract_version: str = EXEC_CLI_STATUS_BINDING_VERSION
    runtime_mutated: bool = False
    executed: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self, "rendered_output", code=AurelExecErrorCode.EMPTY_FIELD)
        forbid_true(self, "runtime_mutated", "executed")


def handle_exec_cli_status(
    status: ExecStatusReadModel,
    *,
    command_kind: ExecCliCommandKind = ExecCliCommandKind.STATUS,
) -> ExecCliStatusResponse:
    """Render the status read model as deterministic JSON. Read-only."""
    if command_kind is not ExecCliCommandKind.STATUS:
        raise AurelExecValidationError(
            f"{command_kind.value} rendering is served by the seal module; "
            "this handler renders STATUS only",
            code=AurelExecErrorCode.ERROR,
            field="command_kind",
        )
    payload = {
        "status_read_model_id": status.status_read_model_id,
        "categories": dict(status.categories),
        "truth_labels": [label.value for label in status.truth_labels],
        "unavailable_reasons": dict(status.unavailable_reasons),
        "read_only": status.read_only,
        "shell_ui_available": status.shell_ui_available,
    }
    return ExecCliStatusResponse(
        command_kind=command_kind,
        rendered_output=json.dumps(payload, sort_keys=True, indent=2),
        truth_label=ExecTruthLabel.LIVE,
    )
