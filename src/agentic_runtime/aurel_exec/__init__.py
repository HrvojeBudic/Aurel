"""AurelExec execution kernel (P4-EXEC-A admission/lease + P4-EXEC-B bridge).

Deterministic admission and lease foundation with the first governed
runtime submit bridge:
P3-like candidate -> ExecAdmissionRequest -> ExecAdmissionDecision
-> ExecutionLease -> ExecJob -> ExecutionSession -> ExecutionAttempt
-> ExecRuntimeBridge -> CommandEnvelope -> AgenticRuntime.submit()
-> ExecutionOutcome -> ExecTraceBinding -> ExecProjection.

Hard boundary: P4-EXEC-A created the execution gate and key; P4-EXEC-B
turns the key once, only through the existing ``AgenticRuntime.submit()``
kernel, only for the safe read-only TOOL path (``read_file``), only under a
valid lease and active session. AurelExec supervises the kernel and is
never a second executor: no direct tool dispatch, subprocess, network, raw
filesystem, sandbox, model, or verifier invocation, no manual Trace/Ledger
write, no manual policy/Custos enforcement, no worker/queue/bus/checkpoint/
recovery system. Runtime submit success is not semantic success;
trace-bound is not trace-verified. P3 proposes; P4 admits, leases, and
submits; P5 proves; P9 authorizes; Shell projects; Operator decides.

Like ``aurel_flow``, this package is not re-exported from the
``agentic_runtime`` top level; import it explicitly as
``agentic_runtime.aurel_exec``.
"""

from .exec_admission import (
    EXEC_ADMISSION_DECISION_VERSION,
    EXEC_ADMISSION_GATE_RESULT_VERSION,
    EXEC_ADMISSION_REQUEST_VERSION,
    STANDARD_UNAVAILABLE_REASONS,
    ExecAdmissionDecision,
    ExecAdmissionGateResult,
    ExecAdmissionRequest,
    ExecMissingRequirement,
    ExecUnavailableReason,
    build_dev_fixture_admission_request,
    decide_admission,
)
from .exec_errors import (
    AurelExecError,
    AurelExecErrorCode,
    AurelExecValidationError,
    reject,
)
from .exec_job import (
    EXEC_JOB_VERSION,
    EXECUTION_ATTEMPT_VERSION,
    ExecJob,
    ExecutionAttempt,
    bind_lease_to_job,
    create_exec_job,
    create_execution_attempt,
    transition_exec_job,
    transition_execution_attempt,
)
from .exec_outcome import (
    EXECUTION_OUTCOME_VERSION,
    ExecutionOutcome,
    ExecutionOutcomeStatus,
    normalize_runtime_result,
)
from .exec_runtime_bridge import (
    DIRECT_DISPATCH_FORBIDDEN_REASON,
    NO_DIRECT_DISPATCH_PROOF_VERSION,
    RUNTIME_BRIDGE_SUBMIT_REQUEST_VERSION,
    RUNTIME_BRIDGE_SUBMIT_RESULT_VERSION,
    RUNTIME_SUBMIT_PROOF_VERSION,
    SUPPORTED_BRIDGE_EXECUTION_MODES,
    SUPPORTED_BRIDGE_TOOLS,
    UNSUPPORTED_EXECUTION_MODE_PROOF_VERSION,
    ExecRuntimeBridge,
    NoDirectDispatchProof,
    RuntimeBridgeExecution,
    RuntimeBridgeSubmitRequest,
    RuntimeBridgeSubmitResult,
    RuntimeBridgeUnavailableReason,
    RuntimeSubmitProof,
    RuntimeSubmitStatus,
    UnsupportedExecutionModeProof,
    build_no_direct_dispatch_proof,
    build_runtime_bridge_submit_request,
    build_runtime_submit_proof,
    build_unsupported_execution_mode_proofs,
    describe_unavailable_mode,
)
from .exec_session import (
    ACTIVE_SESSION_STATUSES,
    EXECUTION_SESSION_VERSION,
    SESSION_STATUS_TRANSITIONS,
    ExecutionSession,
    ExecutionSessionStatus,
    bind_session_to_job,
    close_execution_session,
    mark_session_failed,
    mark_session_running,
    open_execution_session,
)
from .exec_trace_binding import (
    EXEC_TRACE_BINDING_VERSION,
    ExecTraceBinding,
    build_exec_trace_binding,
)
from .exec_lease import (
    EXECUTION_LEASE_VERSION,
    LEASE_SCOPE_VERSION,
    LEASE_VALIDATION_RESULT_VERSION,
    ExecLeaseDenied,
    ExecutionLease,
    LeaseDenialReason,
    LeaseRevocationState,
    LeaseScope,
    LeaseValidationResult,
    issue_execution_lease,
    revoke_execution_lease,
    validate_execution_lease,
)
from .exec_projection import (
    EXEC_PROJECTION_VERSION,
    FUTURE_RUNTIME_BRIDGE_STEPS,
    NO_CUSTOS_ENFORCEMENT_PROOF_VERSION,
    NO_RAW_EXECUTION_PROOF_VERSION,
    NO_RUNTIME_SUBMIT_PROOF_VERSION,
    NO_TRACE_VERIFIED_PROOF_VERSION,
    P4_EXEC_A_HANDOFF_FRAME_VERSION,
    STANDARD_BRIDGE_REQUIREMENTS,
    ExecAttemptGuardState,
    ExecLeaseProjectionState,
    ExecProjection,
    FutureRuntimeBridgeRequirement,
    NoCustosEnforcementProof,
    NoRawExecutionProof,
    NoRuntimeSubmitProof,
    NoTraceVerifiedProof,
    P4ExecAHandoffFrame,
    RuntimeSubmitUnavailableReason,
    build_exec_projection,
    build_no_custos_enforcement_proof,
    build_no_raw_execution_proof,
    build_no_runtime_submit_proof,
    build_no_trace_verified_proof,
    build_p4_exec_a_handoff_frame,
)
from .exec_types import (
    ADMISSION_GATE_ORDER,
    ATTEMPT_LIFECYCLE_TRANSITIONS,
    AUREL_EXEC_CONTRACT_VERSION,
    AUREL_EXEC_PACK_ID,
    AUREL_EXEC_PACK_TITLE,
    AUREL_EXEC_REPORT_PATH,
    CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
    FORBIDDEN_EXEC_TRUTH_LABELS,
    JOB_LIFECYCLE_TRANSITIONS,
    P3_READY_MARKER,
    PERSISTENCE_UNAVAILABLE_REASON,
    POLICY_SHADOW_ONLY_REASON,
    RAW_EXECUTION_UNAVAILABLE_REASON,
    RUNTIME_SUBMIT_UNAVAILABLE_REASON,
    SANDBOX_REQUIRED_MODES,
    SHELL_PROJECTION_UNAVAILABLE_REASON,
    SUBMIT_AWARE_ATTEMPT_STATES,
    TRACE_VERIFICATION_UNAVAILABLE_REASON,
    VERIFIER_REQUIRED_MODES,
    AlgedonicSignalKind,
    ExecAdmissionGateKind,
    ExecAdmissionState,
    ExecCustosStatus,
    ExecLifecycleState,
    ExecMissingRequirementKind,
    ExecPolicyStatus,
    ExecTraceStatus,
    ExecTruthLabel,
    ExecUnavailableSystem,
    ExecutionFailureClass,
    ExecutionMode,
    ExecutionPlasticityLevel,
    ExecutionTopologyKind,
    RecoveryActionKind,
    TraceBindingStatus,
)
