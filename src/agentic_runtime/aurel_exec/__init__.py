"""AurelExec execution kernel foundation (P4-EXEC-A).

Deterministic admission and lease foundation:
P3-like candidate -> ExecAdmissionRequest -> ExecAdmissionDecision
-> ExecutionLease -> ExecJob -> ExecutionAttempt guard -> ExecProjection.

Hard boundary: P4-EXEC-A creates the execution gate and the execution key —
it does not turn the key. Nothing in this package calls AgenticRuntime.submit,
dispatches a tool, invokes a model or verifier, executes terminal/code/sandbox
actions, opens network or subprocess side effects, writes Trace/Ledger, or
mutates memory, policy, or identity. P3 proposes; P4-EXEC-A admits and leases;
P4-EXEC-B performs the first governed runtime.submit bridge; P5 proves;
P9 authorizes; Shell projects; Operator decides.

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
    create_exec_job,
    create_execution_attempt,
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
    AUREL_EXEC_CONTRACT_VERSION,
    AUREL_EXEC_PACK_ID,
    AUREL_EXEC_PACK_TITLE,
    AUREL_EXEC_REPORT_PATH,
    CUSTOS_ENFORCEMENT_UNAVAILABLE_REASON,
    FORBIDDEN_EXEC_TRUTH_LABELS,
    P3_READY_MARKER,
    PERSISTENCE_UNAVAILABLE_REASON,
    POLICY_SHADOW_ONLY_REASON,
    RAW_EXECUTION_UNAVAILABLE_REASON,
    RUNTIME_SUBMIT_UNAVAILABLE_REASON,
    SANDBOX_REQUIRED_MODES,
    SHELL_PROJECTION_UNAVAILABLE_REASON,
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
