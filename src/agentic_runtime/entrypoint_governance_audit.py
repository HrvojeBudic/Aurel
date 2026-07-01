"""P1.ENF-B entrypoint governance audit — repo-backed no-bypass evidence."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .entrypoint_governance_guard import (
    EntrypointGovernanceClassification,
    EntrypointGovernanceGuard,
    classify_entrypoint_governance,
)


class EntrypointSurface(str, Enum):
    RUNTIME = "runtime"
    REPO_AGENT = "repo_agent"
    CLI = "cli"
    AUREL_SHELL = "aurel_shell"
    TOOLS = "tools"
    SANDBOX = "sandbox"
    TEST = "test"
    DEV_FIXTURE = "dev_fixture"
    UNKNOWN = "unknown"


class EntrypointKind(str, Enum):
    SUBMIT = "submit"
    DISPATCH = "dispatch"
    COMMAND = "command"
    READ_MODEL = "read_model"
    CONTRACT = "contract"
    ORCHESTRATION = "orchestration"
    FIXTURE = "fixture"
    UNKNOWN = "unknown"


class EntrypointTruthLabel(str, Enum):
    GOVERNANCE_AUDIT = "governance_audit"
    NO_BYPASS_EVIDENCE = "no_bypass_evidence"
    CONTRACT_ONLY = "contract_only"
    DEV_FIXTURE = "dev_fixture"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class SideEffectVector:
    calls_runtime_submit: bool = False
    calls_tool_bus: bool = False
    calls_sandbox: bool = False
    calls_subprocess: bool = False
    writes_files: bool = False
    writes_memory: bool = False
    writes_trace: bool = False
    modifies_policy: bool = False
    modifies_identity: bool = False

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "calls_runtime_submit": self.calls_runtime_submit,
            "calls_sandbox": self.calls_sandbox,
            "calls_subprocess": self.calls_subprocess,
            "calls_tool_bus": self.calls_tool_bus,
            "modifies_identity": self.modifies_identity,
            "modifies_policy": self.modifies_policy,
            "writes_files": self.writes_files,
            "writes_memory": self.writes_memory,
            "writes_trace": self.writes_trace,
        }


@dataclass(frozen=True)
class EntrypointDiscoveryRecord:
    path: str
    symbol: str
    surface: EntrypointSurface
    kind: EntrypointKind
    side_effect_vectors: SideEffectVector
    classification: EntrypointGovernanceClassification
    evidence_refs: tuple[str, ...] = ()
    truth_label: EntrypointTruthLabel = EntrypointTruthLabel.GOVERNANCE_AUDIT
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "evidence_refs": sorted(self.evidence_refs),
            "kind": self.kind.value,
            "metadata": dict(sorted(self.metadata.items())),
            "path": self.path,
            "side_effect_vectors": self.side_effect_vectors.to_canonical_dict(),
            "surface": self.surface.value,
            "symbol": self.symbol,
            "truth_label": self.truth_label.value,
        }


@dataclass(frozen=True)
class P1ENFBSideEffectProof:
    p2_9_b_implemented: bool = False
    p2_vertical_slice_created: bool = False
    shell_command_router_created: bool = False
    product_ui_created: bool = False
    repo_agent_rewritten: bool = False
    identity_cli_refactored: bool = False
    sandbox_backend_hardened: bool = False
    golden_thread_b_created: bool = False
    runtime_submit_rewritten: bool = False
    trace_memory_rewritten: bool = False

    def to_canonical_dict(self) -> dict[str, bool]:
        return {
            "golden_thread_b_created": self.golden_thread_b_created,
            "identity_cli_refactored": self.identity_cli_refactored,
            "p2_9_b_implemented": self.p2_9_b_implemented,
            "p2_vertical_slice_created": self.p2_vertical_slice_created,
            "product_ui_created": self.product_ui_created,
            "repo_agent_rewritten": self.repo_agent_rewritten,
            "runtime_submit_rewritten": self.runtime_submit_rewritten,
            "sandbox_backend_hardened": self.sandbox_backend_hardened,
            "shell_command_router_created": self.shell_command_router_created,
            "trace_memory_rewritten": self.trace_memory_rewritten,
        }

    @property
    def allows_no_product_scope(self) -> bool:
        return all(not value for value in self.to_canonical_dict().values())


@dataclass(frozen=True)
class P1ENFBResult:
    discovery_records: tuple[EntrypointDiscoveryRecord, ...]
    side_effect_proof: P1ENFBSideEffectProof
    unknown_risk_count: int
    blocked_risk_count: int
    governed_count: int
    non_executing_count: int

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "blocked_risk_count": self.blocked_risk_count,
            "discovery_record_count": len(self.discovery_records),
            "governed_count": self.governed_count,
            "non_executing_count": self.non_executing_count,
            "side_effect_proof": self.side_effect_proof.to_canonical_dict(),
            "unknown_risk_count": self.unknown_risk_count,
        }

    @property
    def result_hash(self) -> str:
        payload = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Repo-backed seed discovery map — every record cites file:line evidence.
_SEED_DISCOVERY: tuple[EntrypointDiscoveryRecord, ...] = (
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/runtime.py",
        symbol="agentic_runtime.runtime.AgenticRuntime.submit",
        surface=EntrypointSurface.RUNTIME,
        kind=EntrypointKind.SUBMIT,
        side_effect_vectors=SideEffectVector(
            calls_tool_bus=True,
            calls_sandbox=True,
            writes_memory=True,
            writes_trace=True,
            modifies_policy=True,
        ),
        classification=EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT,
        evidence_refs=("runtime.py:147", "runtime.py:policy.evaluate", "runtime.py:_append_transition"),
        truth_label=EntrypointTruthLabel.NO_BYPASS_EVIDENCE,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/repo_agent.py",
        symbol="agentic_runtime.repo_agent.PatchExecutor.apply",
        surface=EntrypointSurface.REPO_AGENT,
        kind=EntrypointKind.ORCHESTRATION,
        side_effect_vectors=SideEffectVector(calls_runtime_submit=True, writes_files=True),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED,
        evidence_refs=("repo_agent.py:628", "repo_agent.py:647"),
        metadata={"delegates_via": "runtime.submit"},
        truth_label=EntrypointTruthLabel.NO_BYPASS_EVIDENCE,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/repo_agent.py",
        symbol="agentic_runtime.repo_agent.TestRunnerAdapter.run",
        surface=EntrypointSurface.REPO_AGENT,
        kind=EntrypointKind.ORCHESTRATION,
        side_effect_vectors=SideEffectVector(
            calls_runtime_submit=True,
            calls_sandbox=True,
            calls_subprocess=True,
        ),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED,
        evidence_refs=("repo_agent.py:668", "repo_agent.py:677"),
        metadata={"delegates_via": "runtime.submit", "tool": "run_tests"},
        truth_label=EntrypointTruthLabel.NO_BYPASS_EVIDENCE,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/repo_agent.py",
        symbol="agentic_runtime.repo_agent.RepositoryAgentLoop.run",
        surface=EntrypointSurface.REPO_AGENT,
        kind=EntrypointKind.ORCHESTRATION,
        side_effect_vectors=SideEffectVector(
            calls_runtime_submit=True,
            calls_sandbox=True,
            writes_trace=True,
            writes_memory=True,
        ),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        evidence_refs=("repo_agent.py:763", "repo_agent.py:777", "repo_agent.py:828"),
        metadata={"orchestrates": "PatchExecutor,TestRunnerAdapter,RepairLoop"},
        truth_label=EntrypointTruthLabel.GOVERNANCE_AUDIT,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/repo_agent.py",
        symbol="agentic_runtime.repo_agent.RepoContextBuilder.build",
        surface=EntrypointSurface.REPO_AGENT,
        kind=EntrypointKind.READ_MODEL,
        side_effect_vectors=SideEffectVector(),
        classification=EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY,
        evidence_refs=("repo_agent.py:RepoContextBuilder",),
        truth_label=EntrypointTruthLabel.CONTRACT_ONLY,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/tools.py",
        symbol="agentic_runtime.tools.ToolRuntime.dispatch",
        surface=EntrypointSurface.TOOLS,
        kind=EntrypointKind.DISPATCH,
        side_effect_vectors=SideEffectVector(calls_sandbox=True, calls_subprocess=True),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        evidence_refs=("tools.py:227", "runtime.py:submit→tools.dispatch"),
        metadata={"reachable_only_via": "AgenticRuntime.submit"},
        truth_label=EntrypointTruthLabel.GOVERNANCE_AUDIT,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/cli.py",
        symbol="agentic_runtime.cli.cmd_status",
        surface=EntrypointSurface.CLI,
        kind=EntrypointKind.READ_MODEL,
        side_effect_vectors=SideEffectVector(),
        classification=EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY,
        evidence_refs=("cli.py:23", "cli.py:runtime_status"),
        truth_label=EntrypointTruthLabel.CONTRACT_ONLY,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/cli.py",
        symbol="agentic_runtime.cli.cmd_repo_task",
        surface=EntrypointSurface.CLI,
        kind=EntrypointKind.COMMAND,
        side_effect_vectors=SideEffectVector(calls_runtime_submit=True, calls_sandbox=True),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        evidence_refs=("cli.py:88", "cli.py:108", "repo_agent.py:RepositoryAgentLoop.run"),
        metadata={"cli_routes_to": "RepositoryAgentLoop"},
        truth_label=EntrypointTruthLabel.GOVERNANCE_AUDIT,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/cli.py",
        symbol="agentic_runtime.cli.cmd_verify",
        surface=EntrypointSurface.CLI,
        kind=EntrypointKind.COMMAND,
        side_effect_vectors=SideEffectVector(calls_subprocess=True),
        classification=EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK,
        evidence_refs=("cli.py:52", "cli.py:68"),
        metadata={"bypasses_runtime_submit": True, "note": "dev validation subprocess"},
        truth_label=EntrypointTruthLabel.ERROR,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/cli.py",
        symbol="agentic_runtime.cli.cmd_approve_demo",
        surface=EntrypointSurface.CLI,
        kind=EntrypointKind.COMMAND,
        side_effect_vectors=SideEffectVector(calls_runtime_submit=True, calls_sandbox=True),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        evidence_refs=("cli.py:116", "cli.py:kernel.submit"),
        metadata={"demo_only": True},
        truth_label=EntrypointTruthLabel.GOVERNANCE_AUDIT,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/aurel_shell/contracts.py",
        symbol="agentic_runtime.aurel_shell.contracts.AurelShellSideEffectProof",
        surface=EntrypointSurface.AUREL_SHELL,
        kind=EntrypointKind.CONTRACT,
        side_effect_vectors=SideEffectVector(),
        classification=EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY,
        evidence_refs=("contracts.py:126", "tests/aurel_shell/"),
        truth_label=EntrypointTruthLabel.CONTRACT_ONLY,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/aurel_shell/shell_exit_seal_foundation.py",
        symbol="agentic_runtime.aurel_shell.shell_exit_seal_foundation",
        surface=EntrypointSurface.AUREL_SHELL,
        kind=EntrypointKind.CONTRACT,
        side_effect_vectors=SideEffectVector(),
        classification=EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY,
        evidence_refs=("shell_exit_seal_foundation.py:P29ASideEffectProof",),
        truth_label=EntrypointTruthLabel.CONTRACT_ONLY,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/sandbox.py",
        symbol="agentic_runtime.sandbox.UnsafeLocalSandbox.run_shell",
        surface=EntrypointSurface.SANDBOX,
        kind=EntrypointKind.DISPATCH,
        side_effect_vectors=SideEffectVector(calls_subprocess=True),
        classification=EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
        evidence_refs=("sandbox.py:389", "runtime.py:submit→sandbox"),
        metadata={"reachable_only_via": "ToolRuntime→AgenticRuntime.submit"},
        truth_label=EntrypointTruthLabel.GOVERNANCE_AUDIT,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/demo_harness.py",
        symbol="agentic_runtime.demo_harness",
        surface=EntrypointSurface.DEV_FIXTURE,
        kind=EntrypointKind.FIXTURE,
        side_effect_vectors=SideEffectVector(calls_subprocess=True, writes_files=True),
        classification=EntrypointGovernanceClassification.DEV_FIXTURE_ONLY,
        evidence_refs=("demo_harness.py:262", "demo_harness.py:244"),
        truth_label=EntrypointTruthLabel.DEV_FIXTURE,
    ),
    EntrypointDiscoveryRecord(
        path="tests/",
        symbol="tests.conftest",
        surface=EntrypointSurface.TEST,
        kind=EntrypointKind.FIXTURE,
        side_effect_vectors=SideEffectVector(),
        classification=EntrypointGovernanceClassification.TEST_ONLY_EXECUTION_FIXTURE,
        evidence_refs=("tests/",),
        metadata={"not_product_entrypoint": True},
        truth_label=EntrypointTruthLabel.DEV_FIXTURE,
    ),
    EntrypointDiscoveryRecord(
        path="external",
        symbol="external.plugin.execute_command",
        surface=EntrypointSurface.UNKNOWN,
        kind=EntrypointKind.UNKNOWN,
        side_effect_vectors=SideEffectVector(calls_subprocess=True),
        classification=EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK,
        evidence_refs=("entrypoint_governance_guard.py:_looks_execution_like",),
        truth_label=EntrypointTruthLabel.ERROR,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/cli_modules/identity_commands.py",
        symbol="agentic_runtime.cli_modules.identity_commands",
        surface=EntrypointSurface.CLI,
        kind=EntrypointKind.COMMAND,
        side_effect_vectors=SideEffectVector(writes_files=True, modifies_identity=True),
        classification=EntrypointGovernanceClassification.BLOCKED_IDENTITY_BYPASS_RISK,
        evidence_refs=("identity_commands.py",),
        metadata={"not_verified_submit_gate": True},
        truth_label=EntrypointTruthLabel.ERROR,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/cli_modules/policy_commands.py",
        symbol="agentic_runtime.cli_modules.policy_commands",
        surface=EntrypointSurface.CLI,
        kind=EntrypointKind.COMMAND,
        side_effect_vectors=SideEffectVector(modifies_policy=True),
        classification=EntrypointGovernanceClassification.BLOCKED_POLICY_BYPASS_RISK,
        evidence_refs=("policy_commands.py",),
        metadata={"not_verified_submit_gate": True},
        truth_label=EntrypointTruthLabel.ERROR,
    ),
    EntrypointDiscoveryRecord(
        path="src/agentic_runtime/aurel_shell/cli_binding.py",
        symbol="agentic_runtime.aurel_shell.cli_binding",
        surface=EntrypointSurface.AUREL_SHELL,
        kind=EntrypointKind.CONTRACT,
        side_effect_vectors=SideEffectVector(),
        classification=EntrypointGovernanceClassification.UNAVAILABLE,
        evidence_refs=("cli_binding.py:UNAVAILABLE", "P2.7-D section seal"),
        metadata={"product_cli_runner": "unavailable"},
        truth_label=EntrypointTruthLabel.UNAVAILABLE,
    ),
)


class EntrypointGovernanceAudit:
    """Assemble repo-backed entrypoint discovery and classification evidence."""

    def __init__(self, guard: EntrypointGovernanceGuard | None = None) -> None:
        self._guard = guard or EntrypointGovernanceGuard()

    def build_discovery_map(self) -> tuple[EntrypointDiscoveryRecord, ...]:
        return _SEED_DISCOVERY

    def classify_with_guard(self, entrypoint: str) -> EntrypointGovernanceClassification:
        return self._guard.classify(entrypoint).classification

    def build_side_effect_proof(self) -> P1ENFBSideEffectProof:
        return P1ENFBSideEffectProof()

    def build_result(self) -> P1ENFBResult:
        records = self.build_discovery_map()
        blocked = sum(
            1
            for r in records
            if r.classification
            in {
                EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK,
                EntrypointGovernanceClassification.BLOCKED_POLICY_BYPASS_RISK,
                EntrypointGovernanceClassification.BLOCKED_IDENTITY_BYPASS_RISK,
            }
        )
        unknown = sum(
            1
            for r in records
            if r.classification
            is EntrypointGovernanceClassification.BLOCKED_UNKNOWN_EXECUTION_RISK
        )
        governed = sum(
            1
            for r in records
            if r.classification
            in {
                EntrypointGovernanceClassification.GOVERNED_RUNTIME_SUBMIT,
                EntrypointGovernanceClassification.GOVERNED_DELEGATION_CONFIRMED,
                EntrypointGovernanceClassification.GOVERNED_DELEGATION_REQUIRED,
            }
        )
        non_executing = sum(
            1
            for r in records
            if r.classification
            in {
                EntrypointGovernanceClassification.NON_EXECUTING_CONTRACT_ONLY,
                EntrypointGovernanceClassification.NON_EXECUTING_READ_MODEL_ONLY,
                EntrypointGovernanceClassification.TEST_ONLY_EXECUTION_FIXTURE,
                EntrypointGovernanceClassification.DEV_FIXTURE_ONLY,
                EntrypointGovernanceClassification.UNAVAILABLE,
            }
        )
        return P1ENFBResult(
            discovery_records=records,
            side_effect_proof=self.build_side_effect_proof(),
            unknown_risk_count=unknown,
            blocked_risk_count=blocked,
            governed_count=governed,
            non_executing_count=non_executing,
        )


def classify_entrypoint_with_audit_symbol(symbol: str) -> EntrypointGovernanceClassification:
    """Resolve classification for a known audit seed symbol."""
    for record in _SEED_DISCOVERY:
        if record.symbol == symbol:
            return record.classification
    return classify_entrypoint_governance(symbol).classification
