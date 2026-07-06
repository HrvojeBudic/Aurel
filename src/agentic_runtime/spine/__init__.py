"""SPINE-LIVE — the living vertical thread (P3→P4→P5→P2).

See ``agent/reports/SPINE_LIVE_IMPLEMENTATION_PLAN.md``. This package holds the
cross-phase primitives that flip contract-only phases to real execution using
the honest ``LIVE-with-evidence`` rule.
"""

from __future__ import annotations

from .live_evidence import (
    MODEL_CALL_EVIDENCE_VERSION,
    LiveEvidenceLabel,
    ModelCallEvidenceRef,
    capture_model_call_evidence,
    live_available,
)
from .flow_dispatch import (
    FlowDispatchCheckpoint,
    FlowDispatcher,
    FlowDispatchResult,
    FlowDispatchStepResult,
    build_patch_test_graph,
    create_workflow_run,
)
from .harness import SpineSliceResult, build_deepseek_client, run_spine_slice
from .plan_flow import (
    DEFAULT_PLAN_TOOL_ALLOWLIST,
    PlanRealizationError,
    plan_to_flow,
)
from .shell_run_view import (
    ShellRunView,
    build_shell_run_view,
    format_shell_run_view_text,
)
from .trace_verify import (
    TraceVerifiedEvidenceRef,
    TraceVerifiedLabel,
    replay_persisted_trace,
    verify_persisted_trace,
)
from .tool_exec import (
    MUTATING_SPINE_TOOLS,
    HardIsolationEvidenceRef,
    SpineExecutionBlocked,
    SpineToolExecRun,
    SpineToolExecSession,
    ToolExecEvidenceRef,
    ToolExecLease,
    args_hash,
    capture_hard_isolation_evidence,
)

__all__ = [
    "FlowDispatchCheckpoint",
    "FlowDispatcher",
    "FlowDispatchResult",
    "FlowDispatchStepResult",
    "build_patch_test_graph",
    "create_workflow_run",
    "TraceVerifiedEvidenceRef",
    "TraceVerifiedLabel",
    "replay_persisted_trace",
    "verify_persisted_trace",
    "ShellRunView",
    "build_shell_run_view",
    "format_shell_run_view_text",
    "MODEL_CALL_EVIDENCE_VERSION",
    "LiveEvidenceLabel",
    "ModelCallEvidenceRef",
    "capture_model_call_evidence",
    "live_available",
    "MUTATING_SPINE_TOOLS",
    "HardIsolationEvidenceRef",
    "SpineExecutionBlocked",
    "SpineToolExecRun",
    "SpineToolExecSession",
    "ToolExecEvidenceRef",
    "ToolExecLease",
    "args_hash",
    "capture_hard_isolation_evidence",
    "SpineSliceResult",
    "run_spine_slice",
    "build_deepseek_client",
    "DEFAULT_PLAN_TOOL_ALLOWLIST",
    "PlanRealizationError",
    "plan_to_flow",
]
