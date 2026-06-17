"""
budget.py — Budget, resource, and cost governance (P0.8).

Enforces hard caps on command/tool/sandbox usage, retries, runtime duration,
stdout/stderr volume, write churn, memory writes, and estimated token/cost.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .core_types import BudgetDecisionRecord, ObservationEnvelope, now


@dataclass
class BudgetPolicy:
    max_commands_per_run: int = 200
    max_tool_calls_per_run: int = 120
    max_retries_per_step: int = 3
    max_sandbox_executions: int = 120
    max_runtime_seconds: float = 600.0
    max_stdout_bytes: int = 256 * 1024
    max_stderr_bytes: int = 256 * 1024
    max_file_writes: int = 200
    max_changed_files: int = 500
    max_memory_writes: int = 500
    max_estimated_tokens: int = 200_000
    max_estimated_cost_cents: int = 500
    max_llm_calls: int = 40


class BudgetExceeded(Exception):
    def __init__(self, kind: str, used: float, limit: float, reason: str = ""):
        super().__init__(f"budget '{kind}' exceeded: {used:.1f}/{limit:.1f}")
        self.kind = kind
        self.used = used
        self.limit = limit
        self.reason = reason or kind
        self.reason_code = "budget_exceeded"


@dataclass
class BudgetLedger:
    policy: BudgetPolicy = field(default_factory=BudgetPolicy)
    # Legacy-compatible global counters
    llm_calls: int = 0
    tool_calls: int = 0
    usd: float = 0.0
    wall_s: float = 0.0
    warnings: list[str] = field(default_factory=list)
    # Resource aggregates
    sandbox_executions: int = 0
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    file_writes: int = 0
    changed_files: int = 0
    memory_writes: int = 0
    estimated_tokens: int = 0
    estimated_cost_cents: float = 0.0
    # scoped usage
    per_run: dict[str, dict[str, Any]] = field(default_factory=dict)
    per_command: dict[str, dict[str, Any]] = field(default_factory=dict)
    per_step: dict[str, int] = field(default_factory=dict)
    per_agent: dict[str, dict[str, Any]] = field(default_factory=dict)
    # runtime context
    current_run_id: str = ""
    current_agent_id: str = ""
    current_intent_id: str = ""
    run_started_at: float = 0.0
    _trace: Any = None

    def bind_trace(self, trace: Any) -> None:
        self._trace = trace

    def begin_run(self, run_id: str, agent_id: str, intent_id: str) -> None:
        self.current_run_id = run_id
        self.current_agent_id = agent_id
        self.current_intent_id = intent_id
        self.per_run[run_id] = {
            "commands": 0,
            "tool_calls": 0,
            "sandbox_executions": 0,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
            "file_writes": 0,
            "changed_files": 0,
            "memory_writes": 0,
            "retries": {},
            "estimated_tokens": 0,
            "estimated_cost_cents": 0.0,
            "started_at": now(),
        }
        self.run_started_at = self.per_run[run_id]["started_at"]
        self.per_agent.setdefault(agent_id, {"commands": 0, "tool_calls": 0, "runs": set()})
        self.per_agent[agent_id]["runs"].add(run_id)

    def ensure_context(self, run_id: str, agent_id: str, intent_id: str) -> None:
        if not self.current_run_id:
            self.begin_run(run_id, agent_id, intent_id)

    def charge_llm(self, usd: float = 0.01, estimated_tokens: int = 1200) -> None:
        run = self._run_usage()
        self.llm_calls += 1
        self.usd += usd
        self.estimated_tokens += estimated_tokens
        cents = usd * 100.0
        self.estimated_cost_cents += cents
        run["estimated_tokens"] += estimated_tokens
        run["estimated_cost_cents"] += cents

        self._check("max_llm_calls", self.llm_calls, self.policy.max_llm_calls)
        self._check("max_estimated_tokens", run["estimated_tokens"], self.policy.max_estimated_tokens)
        self._check(
            "max_estimated_cost_cents",
            run["estimated_cost_cents"],
            self.policy.max_estimated_cost_cents,
        )

    def precheck_command(self, command_id: str, tool: str, agent_id: str) -> None:
        run = self._run_usage()
        run["commands"] += 1
        self.per_command.setdefault(command_id, {"tool": tool, "run_id": self.current_run_id})
        self.per_agent.setdefault(agent_id, {"commands": 0, "tool_calls": 0, "runs": set()})
        self.per_agent[agent_id]["commands"] += 1
        self._check("max_commands_per_run", run["commands"], self.policy.max_commands_per_run)
        elapsed = max(0.0, now() - run["started_at"])
        self._check("max_runtime_seconds", elapsed, self.policy.max_runtime_seconds)

    def charge_tool(self, agent_id: str) -> None:
        run = self._run_usage()
        self.tool_calls += 1
        run["tool_calls"] += 1
        self.per_agent.setdefault(agent_id, {"commands": 0, "tool_calls": 0, "runs": set()})
        self.per_agent[agent_id]["tool_calls"] += 1
        self._check("max_tool_calls_per_run", run["tool_calls"], self.policy.max_tool_calls_per_run)

    def charge_sandbox_execution(self) -> None:
        run = self._run_usage()
        self.sandbox_executions += 1
        run["sandbox_executions"] += 1
        self._check(
            "max_sandbox_executions",
            run["sandbox_executions"],
            self.policy.max_sandbox_executions,
        )

    def charge_retry(self, step_key: str) -> None:
        run = self._run_usage()
        retries = run["retries"]
        retries[step_key] = retries.get(step_key, 0) + 1
        self.per_step[step_key] = retries[step_key]
        self._check("max_retries_per_step", retries[step_key], self.policy.max_retries_per_step)

    def charge_time(self, seconds: float) -> None:
        run = self._run_usage()
        self.wall_s += seconds
        elapsed = max(0.0, now() - run["started_at"])
        self._check("max_runtime_seconds", elapsed, self.policy.max_runtime_seconds)

    def charge_memory_write(self) -> None:
        run = self._run_usage()
        self.memory_writes += 1
        run["memory_writes"] += 1
        self._check("max_memory_writes", run["memory_writes"], self.policy.max_memory_writes)

    def apply_output_caps(self, obs: ObservationEnvelope) -> ObservationEnvelope:
        run = self._run_usage()
        out = obs.stdout.encode("utf-8", "replace")
        err = obs.stderr.encode("utf-8", "replace")
        if len(out) > self.policy.max_stdout_bytes:
            trimmed = out[: self.policy.max_stdout_bytes]
            obs.stdout = trimmed.decode("utf-8", "replace")
            obs.artifacts["stdout_truncated"] = True
            obs.artifacts["stdout_original_bytes"] = len(out)
        if len(err) > self.policy.max_stderr_bytes:
            trimmed = err[: self.policy.max_stderr_bytes]
            obs.stderr = trimmed.decode("utf-8", "replace")
            obs.artifacts["stderr_truncated"] = True
            obs.artifacts["stderr_original_bytes"] = len(err)
        out_b = len(obs.stdout.encode("utf-8", "replace"))
        err_b = len(obs.stderr.encode("utf-8", "replace"))
        self.stdout_bytes += out_b
        self.stderr_bytes += err_b
        run["stdout_bytes"] += out_b
        run["stderr_bytes"] += err_b
        return obs

    def account_post_execution(self, tool: str, args: dict, obs: ObservationEnvelope) -> None:
        run = self._run_usage()
        changed = set()
        fs_diff = (obs.artifacts or {}).get("fs_diff") or {}
        if isinstance(fs_diff, dict):
            changed.update(fs_diff.keys())
        path = args.get("path")
        if tool in {"write_file", "edit_file", "patch_file", "delete_file",
                    "mutate_protected_verification"} and path:
            self.file_writes += 1
            run["file_writes"] += 1
            changed.add(path)
        run["changed_files"] += len(changed)
        self.changed_files += len(changed)
        self._check("max_file_writes", run["file_writes"], self.policy.max_file_writes)
        self._check("max_changed_files", run["changed_files"], self.policy.max_changed_files)

    def snapshot(self) -> dict:
        run = self.per_run.get(self.current_run_id, {})
        usage = {
            "run_id": self.current_run_id,
            "commands": run.get("commands", 0),
            "tool_calls": run.get("tool_calls", 0),
            "sandbox_executions": run.get("sandbox_executions", 0),
            "stdout_bytes": run.get("stdout_bytes", 0),
            "stderr_bytes": run.get("stderr_bytes", 0),
            "file_writes": run.get("file_writes", 0),
            "changed_files": run.get("changed_files", 0),
            "memory_writes": run.get("memory_writes", 0),
            "estimated_tokens": run.get("estimated_tokens", 0),
            "estimated_cost_cents": round(run.get("estimated_cost_cents", 0.0), 3),
        }
        return {
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "usd": round(self.usd, 4),
            "wall_s": round(self.wall_s, 2),
            "warnings": list(self.warnings),
            "usage": usage,
            "policy": {
                "max_commands_per_run": self.policy.max_commands_per_run,
                "max_tool_calls_per_run": self.policy.max_tool_calls_per_run,
                "max_retries_per_step": self.policy.max_retries_per_step,
                "max_sandbox_executions": self.policy.max_sandbox_executions,
                "max_runtime_seconds": self.policy.max_runtime_seconds,
                "max_stdout_bytes": self.policy.max_stdout_bytes,
                "max_stderr_bytes": self.policy.max_stderr_bytes,
                "max_file_writes": self.policy.max_file_writes,
                "max_changed_files": self.policy.max_changed_files,
                "max_memory_writes": self.policy.max_memory_writes,
                "max_estimated_tokens": self.policy.max_estimated_tokens,
                "max_estimated_cost_cents": self.policy.max_estimated_cost_cents,
            },
        }

    def _run_usage(self) -> dict[str, Any]:
        if not self.current_run_id:
            # Commands submitted directly to runtime without entity.run context.
            self.begin_run("run_unbound", "agent_unbound", "intent_unbound")
        return self.per_run[self.current_run_id]

    def _check(self, kind: str, used: float, limit: float) -> None:
        if used > 0.8 * limit:
            self.warnings.append(f"{kind} at {used:.1f}/{limit:.1f} (>80%)")
        if used > limit:
            self._trace_budget(kind, "deny", used, limit, "limit exceeded")
            raise BudgetExceeded(kind, used, limit)
        self._trace_budget(kind, "allow", used, limit)

    def _trace_budget(
        self,
        metric: str,
        verdict: str,
        used: float,
        limit: float,
        reason: str = "",
    ) -> None:
        if not self._trace:
            return
        if not hasattr(self._trace, "append_budget_decision"):
            return
        rec = BudgetDecisionRecord.make(
            run_id=self.current_run_id or "run_unbound",
            intent_id=self.current_intent_id or "intent_unbound",
            issuer_card_id=self.current_agent_id or "agent_unbound",
            metric=metric,
            verdict=verdict,
            used=float(used),
            limit=float(limit),
            reason=reason,
        )
        self._trace.append_budget_decision(rec)
