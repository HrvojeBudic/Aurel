"""
agentic_runtime — a full reference implementation of an Agent 3.0 / Agentic OS
governed runtime. The entity proposes; the runtime disposes.

``build_runtime(...)`` wires the whole kernel together so callers only deal with
intents and entities.
"""
from __future__ import annotations

__version__ = "0.2.0"

from typing import Optional, cast

from .budget import BudgetLedger, BudgetPolicy
from .canonical_path import CanonicalPathResolver
from .entrypoint_governance_guard import (
    EntrypointBypassGuardResult,
    EntrypointBypassRisk,
    EntrypointGovernanceClassification,
    EntrypointGovernanceGuard,
    GovernedDelegationRequirement,
    NonExecutingEntrypointProof,
    classify_entrypoint_governance,
)
from .entrypoint_governance_audit import (
    EntrypointDiscoveryRecord,
    EntrypointGovernanceAudit,
    EntrypointKind,
    EntrypointSurface,
    EntrypointTruthLabel,
    P1ENFBResult,
    P1ENFBSideEffectProof,
    SideEffectVector,
    classify_entrypoint_with_audit_symbol,
)
from .governance_enforcement import (
    GovernanceEnforcementBoundary,
    GovernanceEnforcementConfig,
    GovernanceEnforcementMode,
    GovernanceEnforcementModeStatus,
    GovernanceEnforcementResult,
    P1ENFASideEffectProof,
    P1ENFAResult,
)
from .identity_invariant_enforcement import (
    IdentityInvariantCheckInput,
    IdentityInvariantDecision,
    IdentityInvariantEnforcementResult,
    IdentitySubmitWithInvariantResult,
    discover_identity_kernel_invariants,
    evaluate_identity_invariant_enforcement,
    evaluate_identity_submit_with_invariants,
    identity_invariant_enforcement_to_artifact,
)
from .identity_kernel_invariants import (
    IdentityKernelDiscoveryResult,
    IdentityKernelInvariantRecord,
    IdentityKernelSource,
    SELECTED_INVARIANT_IDS,
)
from .identity_submit_context import (
    IdentityMissingContextBehavior,
    IdentitySubmitArtifact,
    IdentitySubmitContext,
    IdentitySubmitContextHash,
    IdentitySubmitContextLoader,
    IdentitySubmitPreflightResult,
    build_identity_submit_context,
    evaluate_identity_submit_preflight,
    load_default_identity_submit_context,
)
from .policy_submit_influence import (
    PolicyResolverShadowCompatibilityProof,
    PolicyResolverSubmitArtifact,
    PolicyResolverSubmitGateResult,
    PolicyResolverSubmitInfluence,
    PolicyResolverSubmitInfluenceStatus,
    evaluate_policy_resolver_submit_influence,
)
from .core_types import (
    AgentCard,
    AgentClass,
    AuthorityScope,
    ExecutionOutcome,
    ExecutionStatus,
    Intent,
    RiskLevel,
)
from .core_types import MemoryGovernanceRecord, MemoryTruthState, PraxisEventRecord, SandboxViolationRecord
from .approval import (
    ApprovalDecision,
    ApprovalMode,
    ApprovalOutcome,
    ApprovalPolicy,
    ApprovalPreview,
    ApprovalReceipt,
    ApprovalRequest,
    ApprovalRequirement,
    ApprovalRiskClass,
    build_preview,
    classify_risk,
)
from .core_types import ApprovalReceiptRecord
from .entity import AgenticEntity
from .hitl import (
    ApprovalGate,
    AutoApprover,
    ConsoleApprover,
    DenyAllApprover,
    PreviewOnlyApprover,
    make_approval_gate,
)
from .memory import MemoryFabric
from .memory_governance import (
    MemoryWriteDecision,
    MemoryWritePolicy,
    MemoryWriteRequest,
)
from .model_providers import (
    ModelProvider,
    ModelProviderConfig,
    ModelRequest,
    ModelResponse,
    MockProvider,
    ProviderHealth,
    ProviderStatus,
    STRUCTURED_PLAN_SCHEMA,
    StructuredPlanResult,
    TokenUsage,
    validate_structured_plan_payload,
)
from .model_router import ModelRouter, MockModelClient, ProviderModelClient
from .plan_validator import PlanStatus, PlanValidationResult, PlanValidator
from .policy import PolicyEngine
from .policy_cards.registry import PolicyCardRegistry
from .runtime import AgenticRuntime
from .repo_agent import (
    CodeTaskPlanner,
    CodeTaskReport,
    LLMRepoPlanner,
    PatchExecutor,
    PatchPlan,
    PatchResult,
    RepairAttempt,
    RepairLoop,
    RepoContext,
    RepoContextBuilder,
    RepoFileSummary,
    RepoPlanValidator,
    RepoTaskPlan,
    RepoTaskRequest,
    RepoTaskStep,
    REPO_PLAN_SCHEMA,
    RepositoryAgentLoop,
    TestFailureAnalyzer,
    TestRunResult,
    TestRunnerAdapter,
)
from .skills import SkillLibrary
from .sandbox import (
    BubblewrapSandbox,
    DockerSandbox,
    ExecResult,
    LocalSubprocessSandbox,
    SafeSandbox,
    Sandbox,
    SandboxBackend,
    SandboxMode,
    SandboxUnavailableError,
    UnsafeLocalSandbox,
    create_sandbox,
)
from .sandbox_policy import (
    ProfiledSandbox,
    SandboxDiagnostics,
    SandboxExecutionContext,
    SandboxExecutionLimits,
    SandboxPolicy,
    SandboxProfile,
    SandboxProfileName,
    SandboxViolation,
    SandboxDecision,
    backend_availability,
    create_profiled_sandbox,
    enforce_path_policy,
    get_sandbox_profile,
    is_path_allowed,
    is_secret_like_path,
    materialize_sandbox_backend,
    resolve_apply_sandbox_profile,
    resolve_workspace_path,
)
from .state_machine import RuntimeStateMachine
from .tool_contracts import (
    ArgSpec,
    ContractValidationResult,
    OutputContract,
    SideEffect,
    ToolContract,
    ToolContractRegistry,
    ToolInputValidator,
    ToolOutputValidator,
    default_contract_registry,
)
from .tools import (
    ToolBus,
    ToolError,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolMetadata,
    ToolRegistry,
    ToolRiskLevel,
    ToolRuntime,
    ToolSandboxRequirement,
    ToolSideEffectType,
    ToolSpec,
    ToolVerifierRequirement,
)
from .trace import (
    InMemoryTraceLedger,
    PersistentTraceLedger,
    TraceLedger,
    TraceLedgerBackend,
)
from .test_integrity import (
    FileIntegritySnapshot,
    MUTATE_PROTECTED_TOOL,
    PROTECTED_FILE_MUTATION,
    ProtectedPathPolicy,
    TestIntegrityVerifier,
)
from .praxis import (
    MemoryCandidate as PraxisMemoryCandidate,
    PraxisEvidence,
    PraxisExperience,
    PraxisExperienceBuilder,
    PraxisMetabolism,
    PraxisOutcomeStatus,
    PraxisReport,
    ProcedureCandidate as PraxisProcedureCandidate,
    PromotionDecision as PraxisPromotionDecision,
    PromotionEvaluator,
    PromotionGate,
    PraxisCandidateGenerator,
    ReflexEligibilityCheck,
    SkillCandidate as PraxisSkillCandidate,
    bridge_skill_candidate_to_library,
    submit_memory_candidate_to_governance,
)
from .status import format_status, runtime_status
from .verifier import StateVerifier

__all__ = [
    "__version__",
    "AgentCard", "AgentClass", "AuthorityScope", "Intent", "RiskLevel",
    "ExecutionStatus", "ExecutionOutcome", "RuntimeStateMachine",
    "GovernanceEnforcementMode", "GovernanceEnforcementModeStatus",
    "GovernanceEnforcementConfig", "GovernanceEnforcementResult",
    "GovernanceEnforcementBoundary", "P1ENFASideEffectProof", "P1ENFAResult",
    "PolicyResolverSubmitInfluence", "PolicyResolverSubmitInfluenceStatus",
    "PolicyResolverSubmitGateResult", "PolicyResolverSubmitArtifact",
    "PolicyResolverShadowCompatibilityProof", "evaluate_policy_resolver_submit_influence",
    "IdentitySubmitContext", "IdentitySubmitContextHash", "IdentitySubmitPreflightResult",
    "IdentitySubmitArtifact", "IdentityMissingContextBehavior", "IdentitySubmitContextLoader",
    "build_identity_submit_context", "evaluate_identity_submit_preflight",
    "load_default_identity_submit_context",
    "IdentityKernelSource", "IdentityKernelInvariantRecord", "IdentityKernelDiscoveryResult",
    "SELECTED_INVARIANT_IDS", "discover_identity_kernel_invariants",
    "IdentityInvariantDecision", "IdentityInvariantCheckInput",
    "IdentityInvariantEnforcementResult", "IdentitySubmitWithInvariantResult",
    "evaluate_identity_invariant_enforcement", "evaluate_identity_submit_with_invariants",
    "identity_invariant_enforcement_to_artifact",
    "EntrypointGovernanceClassification", "EntrypointGovernanceGuard",
    "EntrypointBypassRisk", "EntrypointBypassGuardResult",
    "GovernedDelegationRequirement", "NonExecutingEntrypointProof",
    "classify_entrypoint_governance",
    "EntrypointGovernanceAudit", "EntrypointDiscoveryRecord",
    "EntrypointSurface", "EntrypointKind", "EntrypointTruthLabel",
    "SideEffectVector", "P1ENFBResult", "P1ENFBSideEffectProof",
    "classify_entrypoint_with_audit_symbol",
    "AgenticEntity", "AgenticRuntime", "build_runtime", "Kernel",
    "UnsafeLocalSandbox", "LocalSubprocessSandbox", "SafeSandbox",
    "DockerSandbox", "BubblewrapSandbox", "Sandbox", "SandboxBackend",
    "SandboxMode", "SandboxUnavailableError", "create_sandbox", "ExecResult",
    "SandboxProfile", "SandboxProfileName", "SandboxPolicy", "SandboxDiagnostics",
    "SandboxViolation", "SandboxDecision", "SandboxExecutionContext",
    "SandboxExecutionLimits", "ProfiledSandbox", "get_sandbox_profile",
    "create_profiled_sandbox", "backend_availability", "resolve_apply_sandbox_profile",
    "is_secret_like_path", "is_path_allowed", "enforce_path_policy", "resolve_workspace_path",
    "CanonicalPathResolver", "TestIntegrityVerifier", "StateVerifier",
    "ProtectedPathPolicy", "FileIntegritySnapshot", "MUTATE_PROTECTED_TOOL",
    "PROTECTED_FILE_MUTATION",
    "PlanValidator", "PlanValidationResult", "PlanStatus",
    "TraceLedger", "TraceLedgerBackend", "InMemoryTraceLedger", "PersistentTraceLedger",
    "BudgetLedger", "BudgetPolicy",
    "MemoryFabric", "MemoryTruthState", "MemoryWriteRequest",
    "MemoryWriteDecision", "MemoryWritePolicy", "MemoryGovernanceRecord",
    "ToolContract", "ToolContractRegistry", "ToolInputValidator",
    "ToolOutputValidator", "ArgSpec", "OutputContract", "SideEffect",
    "ContractValidationResult", "default_contract_registry",
    "runtime_status", "format_status",
    "ModelProvider", "ModelProviderConfig", "ModelRequest", "ModelResponse",
    "ProviderHealth", "ProviderStatus", "TokenUsage", "StructuredPlanResult",
    "MockProvider", "ProviderModelClient", "STRUCTURED_PLAN_SCHEMA",
    "validate_structured_plan_payload",
    "ToolBus", "ToolRegistry", "ToolSpec", "ToolMetadata",
    "ToolExecutionContext", "ToolExecutionResult", "ToolError",
    "ToolSideEffectType", "ToolRiskLevel", "ToolSandboxRequirement",
    "ToolVerifierRequirement",
    "RepositoryAgentLoop", "RepoTaskRequest", "RepoTaskPlan", "RepoTaskStep",
    "LLMRepoPlanner", "RepoPlanValidator", "REPO_PLAN_SCHEMA",
    "RepoContext", "RepoFileSummary", "PatchPlan", "PatchResult",
    "TestRunResult", "RepairAttempt", "CodeTaskReport",
    "RepoContextBuilder", "CodeTaskPlanner", "PatchExecutor",
    "TestRunnerAdapter", "TestFailureAnalyzer", "RepairLoop",
    "ApprovalRequest", "ApprovalDecision", "ApprovalReceipt",
    "ApprovalPolicy", "ApprovalRequirement", "ApprovalRiskClass",
    "ApprovalMode", "ApprovalOutcome", "ApprovalPreview",
    "ApprovalReceiptRecord", "PraxisEventRecord", "SandboxViolationRecord", "build_preview", "classify_risk",
    "ConsoleApprover", "DenyAllApprover", "PreviewOnlyApprover",
    "make_approval_gate",
    "PraxisExperience", "PraxisEvidence", "PraxisReport", "PraxisMetabolism",
    "PraxisExperienceBuilder", "PraxisCandidateGenerator",
    "PraxisMemoryCandidate", "PraxisProcedureCandidate", "PraxisSkillCandidate",
    "PraxisPromotionDecision", "PromotionEvaluator", "PromotionGate",
    "ReflexEligibilityCheck", "PraxisOutcomeStatus",
    "submit_memory_candidate_to_governance", "bridge_skill_candidate_to_library",
]


class Kernel:
    """Bundle of wired subsystems shared by all entities in one workspace."""

    def __init__(self, sandbox, tools, policy, verifier, trace, memory,
                 budget, router, skills, runtime, sandbox_policy=None):
        self.sandbox = sandbox
        self.sandbox_policy = sandbox_policy
        self.tools = tools
        self.policy = policy
        self.verifier = verifier
        self.trace = trace
        self.memory = memory
        self.budget = budget
        self.router = router
        self.skills = skills
        self.runtime = runtime

    def spawn(self, card: AgentCard) -> AgenticEntity:
        validator = PlanValidator(
            registered_tools=self.runtime.tools.registered,
            allowed_tools=card.allowed_tools or None,
        )
        return AgenticEntity(card, self.runtime, self.router, self.skills, validator)


def build_runtime(
    sandbox: SandboxBackend | ProfiledSandbox | None = None,
    sandbox_mode: Optional[SandboxMode] = None,
    sandbox_profile: Optional[str] = None,
    workspace_root: Optional[str] = None,
    allow_unsafe: bool = False,
    approval_gate: Optional[ApprovalGate] = None,
    approval_policy: Optional[ApprovalPolicy] = None,
    model_clients: Optional[dict] = None,
    budget: Optional[BudgetLedger] = None,
    trace_backend: str = "memory",
    trace_dir: str = ".traces",
    trace_run_id: Optional[str] = None,
    trace_checkpoint_every: int = 5,
    policy_card_registry: PolicyCardRegistry | None = None,
    enable_policy_shadow_projection: bool = False,
    governance_enforcement_config: GovernanceEnforcementConfig | None = None,
    identity_context_loader: IdentitySubmitContextLoader | None = None,
) -> Kernel:
    sandbox_policy: Optional[SandboxPolicy] = None
    if sandbox is None:
        if sandbox_profile:
            sandbox, sandbox_policy = create_profiled_sandbox(
                sandbox_profile,
                workspace_root or ".",
            )
        elif sandbox_mode is not None:
            sandbox = create_sandbox(
                sandbox_mode,
                root=workspace_root,
                allow_unsafe=allow_unsafe or sandbox_mode is SandboxMode.UNSAFE_LOCAL,
            )
            prof_name = (
                SandboxProfileName.UNSAFE_LOCAL_DEMO.value
                if sandbox_mode is SandboxMode.UNSAFE_LOCAL
                else sandbox_mode.value
            )
            profile = get_sandbox_profile(prof_name, sandbox.root)
            sandbox_policy = SandboxPolicy(profile)
            if not isinstance(sandbox, ProfiledSandbox):
                sandbox = ProfiledSandbox(sandbox, sandbox_policy)
        else:
            profile_name = (
                SandboxProfileName.UNSAFE_LOCAL_DEMO.value
                if allow_unsafe
                else SandboxProfileName.RESTRICTED_LOCAL.value
            )
            sandbox, sandbox_policy = create_profiled_sandbox(
                profile_name,
                workspace_root or ".",
            )
    else:
        if isinstance(sandbox, ProfiledSandbox):
            sandbox_policy = sandbox.policy
        elif sandbox_profile:
            profile = get_sandbox_profile(
                sandbox_profile, workspace_root or sandbox.root)
            sandbox_policy = SandboxPolicy(profile)
            sandbox = ProfiledSandbox(sandbox, sandbox_policy)
        else:
            profile = get_sandbox_profile(
                SandboxProfileName.UNSAFE_LOCAL_DEMO.value, sandbox.root)
            sandbox_policy = SandboxPolicy(profile)
    assert sandbox is not None  # all resolution branches above assign a backend
    sandbox_backend = cast(SandboxBackend, sandbox)
    tools = ToolRuntime(sandbox_backend, sandbox_policy=sandbox_policy)
    contracts = default_contract_registry()
    tools.bind_contracts(contracts)
    policy = PolicyEngine(registered_tools=tools.registered, sandbox=sandbox_backend,
                          contract_registry=contracts)
    test_integrity = TestIntegrityVerifier(sandbox_backend)
    verifier = StateVerifier(sandbox_backend, test_integrity=test_integrity)
    if trace_backend == "persistent":
        trace: TraceLedgerBackend = PersistentTraceLedger(
            base_dir=trace_dir,
            run_id=trace_run_id,
            checkpoint_every=trace_checkpoint_every,
        )
    else:
        trace = InMemoryTraceLedger(run_id=trace_run_id)
    memory = MemoryFabric()
    memory.bind_trace(trace)
    budget = budget or BudgetLedger()
    budget.bind_trace(trace)
    skills = SkillLibrary()

    router = ModelRouter()
    if model_clients:
        for profile, clients in model_clients.items():
            router.register(profile, clients)
    else:
        router.configure_default()

    approval_gate = approval_gate or AutoApprover()
    runtime = AgenticRuntime(
        tools, policy, verifier, trace, memory,
        approval_gate, budget,
        contracts=contracts,
        approval_policy=approval_policy or ApprovalPolicy(),
        sandbox_policy=sandbox_policy,
        policy_card_registry=policy_card_registry,
        enable_policy_shadow_projection=enable_policy_shadow_projection,
        governance_enforcement_config=governance_enforcement_config,
        identity_context_loader=identity_context_loader,
    )
    return Kernel(sandbox, tools, policy, verifier, trace, memory, budget,
                  router, skills, runtime, sandbox_policy=sandbox_policy)
