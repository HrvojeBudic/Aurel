"""
agentic_runtime — a full reference implementation of an Agent 3.0 / Agentic OS
governed runtime. The entity proposes; the runtime disposes.

``build_runtime(...)`` wires the whole kernel together so callers only deal with
intents and entities.
"""
from __future__ import annotations

__version__ = "0.2.0"

from typing import Any, Optional, cast

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
from .core_types import (
    MemoryGovernanceRecord,
    MemoryTruthState,
    PraxisEventRecord,
    SandboxAttestationRecord,
    SandboxViolationRecord,
)
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
from .memory import HashingEmbedder, MemoryFabric
from .memory_governance import (
    MemoryLinkDecision,
    MemoryLinkRequest,
    MemoryRevisionDecision,
    MemoryRevisionRequest,
    MemoryWriteDecision,
    MemoryWritePolicy,
    MemoryWriteRequest,
)
# Track A memory stack (A0–A8) — public surface. All additive and, where it
# persists or promotes, gated on AUREL_DURABLE_MEMORY (byte-identical when OFF).
from .core_types import DurableMemoryGovernanceRecord
from .memory_bitemporal import BiTemporalStamp
from .memory_asof import AsOfView
from .memory_tools import MEMORY_TOOL_NAMES, MemoryToolSession
from .memory_graph import (
    MemoryEdge,
    MemoryGraphIndex,
    MemoryRelation,
    detect_supersession_chain,
)
from .memory_persistence import (
    ExternalMemoryBackend,
    FileMemoryBackend,
    MemoryBackend,
    MemoryBackendUnavailable,
)
from .durable_memory import DurableMemoryFabric
from .memory_revision import apply_update as memory_apply_update
from .memory_revision import forget as memory_forget
from .memory_revision import retract as memory_retract
from .memory_consolidation import consolidate as memory_consolidate
from .memory_retrieval import hybrid_retrieve
from .memory_projection import MemoryProjection
from .memory_embedder import NeuralEmbedderSeam
from .evaluation.memory_promotion_bridge import MemoryCandidateBridge
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
from .state_store import StateStore
from .worldline import (
    CheckoutError,
    ForkError,
    ForkRef,
    ForkResult,
    MergeConflict,
    MergeError,
    MergeRef,
    MergeResult,
    WorldLineForest,
    verify_fork,
    verify_merge,
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
from .sandbox_backend_gate import (
    SandboxBackendDecision,
    SandboxBackendGateMode,
    SandboxBackendGateResult,
    SandboxBackendRequirement,
    SANDBOX_BACKEND_SIGNALS_KEY,
    evaluate_sandbox_backend_gate,
    sandbox_backend_gate_to_artifact,
    sandbox_backend_requirement_from_config,
)
from .sandbox_safety import (
    SandboxBackendCapability,
    SandboxBackendKind,
    SandboxBackendRecord,
    SandboxSafetyClass,
    classify_sandbox_backend,
    discover_sandbox_backend_records,
    resolve_wrapped_sandbox_backend,
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
    "DockerSandbox", "BubblewrapSandbox", "Sandbox", "SandboxBackend", "StateStore",
    "WorldLineForest", "CheckoutError", "ForkError", "ForkRef", "ForkResult", "verify_fork",
    "MergeError", "MergeConflict", "MergeRef", "MergeResult", "verify_merge",
    "SandboxMode", "SandboxUnavailableError", "create_sandbox", "ExecResult",
    "SandboxProfile", "SandboxProfileName", "SandboxPolicy", "SandboxDiagnostics",
    "SandboxViolation", "SandboxDecision", "SandboxExecutionContext",
    "SandboxExecutionLimits", "ProfiledSandbox", "get_sandbox_profile",
    "create_profiled_sandbox", "backend_availability", "resolve_apply_sandbox_profile",
    "is_secret_like_path", "is_path_allowed", "enforce_path_policy", "resolve_workspace_path",
    "SandboxSafetyClass", "SandboxBackendKind", "SandboxBackendCapability",
    "SandboxBackendRecord", "classify_sandbox_backend", "discover_sandbox_backend_records",
    "resolve_wrapped_sandbox_backend",
    "SandboxBackendGateMode", "SandboxBackendDecision", "SandboxBackendRequirement",
    "SandboxBackendGateResult", "SANDBOX_BACKEND_SIGNALS_KEY",
    "evaluate_sandbox_backend_gate", "sandbox_backend_gate_to_artifact",
    "sandbox_backend_requirement_from_config",
    "CanonicalPathResolver", "TestIntegrityVerifier", "StateVerifier",
    "ProtectedPathPolicy", "FileIntegritySnapshot", "MUTATE_PROTECTED_TOOL",
    "PROTECTED_FILE_MUTATION",
    "PlanValidator", "PlanValidationResult", "PlanStatus",
    "TraceLedger", "TraceLedgerBackend", "InMemoryTraceLedger", "PersistentTraceLedger",
    "BudgetLedger", "BudgetPolicy",
    "MemoryFabric", "MemoryTruthState", "MemoryWriteRequest",
    "MemoryWriteDecision", "MemoryWritePolicy", "MemoryGovernanceRecord",
    # Track A memory stack (A0–A8) public surface.
    "HashingEmbedder", "BiTemporalStamp", "AsOfView",
    "MemoryToolSession", "MEMORY_TOOL_NAMES",
    "MemoryLinkRequest", "MemoryLinkDecision",
    "MemoryRevisionRequest", "MemoryRevisionDecision",
    "MemoryEdge", "MemoryGraphIndex", "MemoryRelation", "detect_supersession_chain",
    "MemoryBackend", "MemoryBackendUnavailable", "FileMemoryBackend", "ExternalMemoryBackend",
    "DurableMemoryFabric", "DurableMemoryGovernanceRecord",
    "memory_apply_update", "memory_retract", "memory_forget",
    "memory_consolidate", "hybrid_retrieve", "MemoryProjection",
    "NeuralEmbedderSeam", "MemoryCandidateBridge",
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
    "ApprovalReceiptRecord", "PraxisEventRecord", "SandboxViolationRecord",
    "SandboxAttestationRecord", "build_preview", "classify_risk",
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


# P0-S.3 — entity classes for which content-addressed state retention defaults
# ON (writers that produce forkable/rollbackable state). Every other class stays
# byte-identical to the pre-P0-S.3 default (retention OFF, no state store).
RETAIN_STATES_GATED_CLASSES: frozenset = frozenset({
    AgentClass.CORE, AgentClass.EXECUTION,
})


def _resolve_retain_states(retain_states: Optional[bool],
                           entity_class: Optional[AgentClass]) -> bool:
    """Explicit ``retain_states`` always wins; otherwise gate on the entity
    class. Unset + ungated (or no class) ⇒ False (byte-identical to today)."""
    if retain_states is not None:
        return retain_states
    return entity_class in RETAIN_STATES_GATED_CLASSES


def _build_memory_fabric(trace: Any, trace_dir: str, memory_backend: Any) -> MemoryFabric:
    """A8a — durable memory factory with a fail-closed fallback to in-RAM.

    Flag OFF (default) ⇒ a plain in-RAM ``MemoryFabric`` (byte-identical to today).
    Flag ON ⇒ a ``DurableMemoryFabric`` over a durable backend; if the backend is
    unavailable (or anything goes wrong building it) we FAIL CLOSED to the in-RAM
    fabric — never a silent claim of durability we don't have."""
    from .memory_bitemporal import _flag_enabled

    if not _flag_enabled():
        memory: MemoryFabric = MemoryFabric()
        memory.bind_trace(trace)
        return memory

    try:
        import os

        from .durable_memory import DurableMemoryFabric
        from .memory_persistence import FileMemoryBackend
        backend = memory_backend
        if backend is None:
            path = os.path.join(trace_dir, "memory", f"{trace.run_id}.jsonl")
            backend = FileMemoryBackend(path)
        if not getattr(backend, "available", False):
            raise RuntimeError("durable memory backend unavailable")
        memory = DurableMemoryFabric(backend)
    except Exception:  # noqa: BLE001 - fail closed to in-RAM, honestly non-durable
        memory = MemoryFabric()
    memory.bind_trace(trace)
    return memory


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
    trace_anchor: bool = False,
    policy_card_registry: PolicyCardRegistry | None = None,
    enable_policy_shadow_projection: bool = False,
    governance_enforcement_config: GovernanceEnforcementConfig | None = None,
    identity_context_loader: IdentitySubmitContextLoader | None = None,
    retain_states: Optional[bool] = None,
    state_store: StateStore | None = None,
    entity_class: Optional[AgentClass] = None,
    memory_backend: Any = None,
    profile: Optional[str] = None,
    mandate_registry: Any = None,
) -> Kernel:
    # F1 — enforcement profiles. Opt-in: profile=None keeps today's behavior
    # byte-identical (embedding + the test suite are unaffected). When set, the
    # profile supplies coherent defaults for the submit-path enforcement bundle;
    # any argument the caller passed explicitly always wins over the profile.
    if profile is not None:
        from .governance.enforcement_profiles import profile_build_kwargs, profile_spec

        spec = profile_spec(profile)
        no_sandbox_hint = (
            sandbox is None and sandbox_mode is None and sandbox_profile is None
        )
        p_kwargs, _p_limits = profile_build_kwargs(
            spec, workspace_root=workspace_root or ".")
        if approval_gate is None:
            approval_gate = p_kwargs["approval_gate"]
        if governance_enforcement_config is None:
            governance_enforcement_config = p_kwargs["governance_enforcement_config"]
        if identity_context_loader is None:
            identity_context_loader = p_kwargs["identity_context_loader"]
        if policy_card_registry is None:
            policy_card_registry = p_kwargs["policy_card_registry"]
        if workspace_root is None:
            workspace_root = p_kwargs["workspace_root"]
        if no_sandbox_hint:
            if "sandbox_profile" in p_kwargs:
                sandbox_profile = p_kwargs["sandbox_profile"]
            if p_kwargs.get("allow_unsafe"):
                allow_unsafe = True

    retain_states = _resolve_retain_states(retain_states, entity_class)
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
            sbx_profile = get_sandbox_profile(prof_name, sandbox.root)
            sandbox_policy = SandboxPolicy(sbx_profile)
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
            sbx_profile = get_sandbox_profile(
                sandbox_profile, workspace_root or sandbox.root)
            sandbox_policy = SandboxPolicy(sbx_profile)
            sandbox = ProfiledSandbox(sandbox, sandbox_policy)
        else:
            sbx_profile = get_sandbox_profile(
                SandboxProfileName.UNSAFE_LOCAL_DEMO.value, sandbox.root)
            sandbox_policy = SandboxPolicy(sbx_profile)
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
        anchor_sink = None
        if trace_anchor:
            from .trace_anchor import default_anchor_sink
            anchor_sink = default_anchor_sink()
        trace: TraceLedgerBackend = PersistentTraceLedger(
            base_dir=trace_dir,
            run_id=trace_run_id,
            checkpoint_every=trace_checkpoint_every,
            anchor_sink=anchor_sink,
        )
    else:
        trace = InMemoryTraceLedger(run_id=trace_run_id)
    # M0 — attest the isolation the host can actually provide for hard backends.
    # Functional-probe result (cached) is hash-chained into the run so the trace
    # records the true isolation posture, not a version/info check.
    if sandbox_backend.mode in (SandboxMode.BUBBLEWRAP, SandboxMode.DOCKER):
        from .sandbox import probe_backend
        attestation = probe_backend(sandbox_backend.mode)
        trace.append_sandbox_attestation(
            SandboxAttestationRecord.make(trace.run_id, attestation)
        )
    memory = _build_memory_fabric(trace, trace_dir, memory_backend)
    budget = budget or BudgetLedger()
    budget.bind_trace(trace)
    skills = SkillLibrary()

    router = ModelRouter()
    if model_clients:
        for client_profile, clients in model_clients.items():
            router.register(client_profile, clients)
    else:
        router.configure_default()

    approval_gate = approval_gate or AutoApprover()
    # M1 — content-addressed state retention (opt-in). When on and no store is
    # provided, default one under the trace base so states (base_dir/states) sit
    # beside runs (base_dir/runs) in the eventual world-line forest layout.
    if retain_states and state_store is None:
        state_store = StateStore(trace_dir)
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
        retain_states=retain_states,
        state_store=state_store,
        mandate_registry=mandate_registry,
    )
    return Kernel(sandbox, tools, policy, verifier, trace, memory, budget,
                  router, skills, runtime, sandbox_policy=sandbox_policy)
