"""P0.14 — bounded repository coding loop.

This is intentionally not a fully autonomous software engineer. It is a small
loop that builds bounded context, creates an explicit plan, applies at most a
small set of patches through the Runtime/Tool Bus path, runs tests, and returns
a structured report.
"""
from __future__ import annotations

import json
import re
import time
import fnmatch
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING

from .approval import ApprovalMode, ApprovalPolicy, build_preview
from .core_types import (AgentCard, AgentClass, AuthorityScope, CommandEnvelope,
                         RiskLevel, new_id)
from .hitl import AutoApprover, DenyAllApprover, make_approval_gate
from .sandbox_policy import SandboxProfileName, create_profiled_sandbox


MAX_CONTEXT_FILE_BYTES = 16_384
SECRET_NAMES = {".env", ".env.local", ".envrc", "credentials.json", "secrets.json"}

if TYPE_CHECKING:
    from .praxis import PraxisMetabolism, PraxisReport


@dataclass
class RepoTaskRequest:
    task_id: str
    objective: str
    repo_path: str = "."
    constraints: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=lambda: ["*"])
    disallowed_paths: list[str] = field(default_factory=list)
    max_files_changed: int = 2
    max_repair_iterations: int = 2
    test_command: list[str] = field(default_factory=lambda: ["python3", "-m", "pytest", "-q"])
    require_approval_before_write: bool = True
    approval_mode: str = "auto"
    sandbox_profile: str = "restricted_local"
    planner_mode: str = "deterministic"
    model_provider: Optional[str] = None
    planning_temperature: Optional[float] = None
    max_planning_tokens: Optional[int] = None
    allow_test_modifications: bool = False

    @staticmethod
    def make(objective: str, **kw) -> "RepoTaskRequest":
        return RepoTaskRequest(task_id=new_id("repo_task"), objective=objective, **kw)


@dataclass
class RepoFileSummary:
    path: str
    size_bytes: int
    content_preview: str = ""
    truncated: bool = False
    skipped_reason: str = ""


@dataclass
class RepoContext:
    repo_root: str
    metadata: dict[str, str] = field(default_factory=dict)
    top_level_entries: list[str] = field(default_factory=list)
    source_dirs: list[str] = field(default_factory=list)
    test_dirs: list[str] = field(default_factory=list)
    agent_docs: dict[str, str] = field(default_factory=dict)
    file_summaries: list[RepoFileSummary] = field(default_factory=list)
    symbol_matches: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class RepoTaskStep:
    step_id: str
    action: str
    target: str = ""
    rationale: str = ""
    tool_name: str = ""
    expected_output: str = ""
    risk_class: str = "low"


@dataclass
class PatchPlan:
    path: str
    patch: str = ""
    content: Optional[str] = None
    summary: str = ""


@dataclass
class RepoTaskPlan:
    objective_summary: str
    files_to_inspect: list[str]
    files_to_modify: list[str]
    proposed_steps: list[RepoTaskStep]
    risk_level: str
    expected_tests: list[str]
    requires_approval: bool
    patch_plans: list[PatchPlan] = field(default_factory=list)
    valid: bool = True
    refusal_reason: str = ""
    assumptions: list[str] = field(default_factory=list)
    planning_error: str = ""
    provider_name: str = ""


@dataclass
class PatchResult:
    applied: bool
    files_changed: list[str] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    command_ids: list[str] = field(default_factory=list)
    approval_summaries: list[dict] = field(default_factory=list)


@dataclass
class TestRunResult:
    __test__ = False  # not a pytest test class

    command: list[str]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


@dataclass
class RepairAttempt:
    iteration: int
    failure_summary: str
    proposed_repair: str
    files_touched: list[str] = field(default_factory=list)
    test_result: Optional[TestRunResult] = None


@dataclass
class CodeTaskReport:
    task_id: str
    objective: str
    plan_summary: str
    planner_mode: str = "deterministic"
    model_provider: str = ""
    planning_errors: list[str] = field(default_factory=list)
    fallback_reason: str = ""
    plan_assumptions: list[str] = field(default_factory=list)
    files_inspected: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    tests_run: list[list[str]] = field(default_factory=list)
    test_result: Optional[TestRunResult] = None
    repair_attempts: list[RepairAttempt] = field(default_factory=list)
    approval_summaries: list[dict] = field(default_factory=list)
    final_status: str = "not_started"
    limitations: list[str] = field(default_factory=list)
    next_recommendation: str = ""
    praxis_report: Optional["PraxisReport"] = None
    sandbox_profile: str = ""
    sandbox_violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class RepoContextBuilder:
    def __init__(self, max_file_bytes: int = MAX_CONTEXT_FILE_BYTES) -> None:
        self.max_file_bytes = max_file_bytes

    def build(self, request: RepoTaskRequest) -> RepoContext:
        root = self.detect_repo_root(request.repo_path)
        ctx = RepoContext(repo_root=str(root))
        ctx.metadata = self._metadata(root)
        ctx.top_level_entries = sorted(p.name for p in root.iterdir()
                                       if not p.name.startswith(".venv"))
        ctx.source_dirs = [d for d in ("src", "lib", "app") if (root / d).is_dir()]
        ctx.test_dirs = [d for d in ("tests", "test") if (root / d).is_dir()]
        ctx.agent_docs = self._agent_docs(root)

        candidates = self._candidate_files(root, request)
        for rel in candidates:
            ctx.file_summaries.append(self._summarize_file(root, rel, request))
        query = _keywords(request.objective)
        if query:
            ctx.symbol_matches = self._search(root, query, request)
        return ctx

    def detect_repo_root(self, repo_path: str) -> Path:
        start = Path(repo_path).resolve()
        if not start.exists():
            raise ValueError(f"repo_path does not exist: {repo_path}")
        cur = start if start.is_dir() else start.parent
        for p in (cur, *cur.parents):
            if (p / "pyproject.toml").exists() or (p / ".git").exists() or (p / "agent").is_dir():
                return p
        return cur

    def _metadata(self, root: Path) -> dict[str, str]:
        meta: dict[str, str] = {}
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            name = re.search(r'^name\s*=\s*"([^"]+)"', text, re.M)
            version = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
            if name:
                meta["name"] = name.group(1)
            if version:
                meta["version"] = version.group(1)
        return meta

    def _agent_docs(self, root: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        for name in ("AGENT.md", "ACTIVE_TASK.md", "STATE.md", "ARCHITECTURE.md", "TESTS.md"):
            path = root / "agent" / name
            if path.exists() and path.stat().st_size <= self.max_file_bytes:
                out[f"agent/{name}"] = path.read_text(encoding="utf-8", errors="replace")
        return out

    def _candidate_files(self, root: Path, request: RepoTaskRequest) -> list[str]:
        names: list[str] = []
        for name in ("pyproject.toml", "README.md"):
            if (root / name).exists():
                names.append(name)
        for rel in _objective_file_mentions(request.objective):
            try:
                mentioned = _resolve_under(root, rel)
            except ValueError:
                continue
            if self._allowed(rel, request) and mentioned.exists():
                names.append(rel)
        for d in ("src", "tests", "agent"):
            base = root / d
            if base.is_dir():
                for p in sorted(base.rglob("*")):
                    if p.is_file():
                        rel = _rel(root, p)
                        if self._allowed(rel, request):
                            names.append(rel)
                    if len(names) >= 40:
                        break
        return [n for n in dict.fromkeys(names) if self._allowed(n, request)]

    def _summarize_file(self, root: Path, rel: str, request: RepoTaskRequest) -> RepoFileSummary:
        path = _resolve_under(root, rel)
        if not path.exists():
            return RepoFileSummary(rel, 0, skipped_reason="missing file")
        size = path.stat().st_size
        if _is_secret(path):
            return RepoFileSummary(rel, size, skipped_reason="secret-like file skipped")
        if size > self.max_file_bytes:
            return RepoFileSummary(rel, size, content_preview="", truncated=True,
                                   skipped_reason="file too large for full context")
        return RepoFileSummary(
            rel,
            size,
            content_preview=path.read_text(encoding="utf-8", errors="replace"),
            truncated=False,
        )

    def _search(self, root: Path, query: str, request: RepoTaskRequest) -> list[dict]:
        matches: list[dict] = []
        for p in root.rglob("*"):
            if len(matches) >= 50:
                break
            if _skip_path(p) or not p.is_file() or _is_secret(p):
                continue
            try:
                rel = _rel(root, p)
            except ValueError:
                continue
            if not self._allowed(rel, request) or p.stat().st_size > self.max_file_bytes:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if query.lower() in line.lower():
                    matches.append({"path": rel, "line": line_no, "snippet": line[:200]})
                    break
        return matches

    def _allowed(self, rel: str, request: RepoTaskRequest) -> bool:
        return _is_allowed(rel, request.allowed_paths, request.disallowed_paths)


REPO_PLAN_ACTIONS = {"inspect", "patch", "test", "analyze", "report"}
REPO_PLAN_RISKS = {"trivial", "low", "medium", "high", "critical", "r0", "r1", "r2", "r3", "r4", "r5"}
REPO_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "objective_summary",
        "files_to_inspect",
        "files_to_modify",
        "proposed_steps",
        "risk_level",
        "expected_tests",
        "requires_approval",
        "assumptions",
        "refusal_reason",
    ],
    "properties": {
        "objective_summary": {"type": "string"},
        "files_to_inspect": {"type": "array", "items": {"type": "string"}},
        "files_to_modify": {"type": "array", "items": {"type": "string"}},
        "proposed_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "step_id", "action_type", "reason", "expected_output", "risk_class",
                ],
                "properties": {
                    "step_id": {"type": "string"},
                    "action_type": {"type": "string", "enum": sorted(REPO_PLAN_ACTIONS)},
                    "target_path": {"type": ["string", "null"]},
                    "tool_name": {"type": ["string", "null"]},
                    "reason": {"type": "string"},
                    "expected_output": {"type": "string"},
                    "risk_class": {"type": "string"},
                },
            },
        },
        "risk_level": {"type": "string"},
        "expected_tests": {"type": "array", "items": {"type": "string"}},
        "requires_approval": {"type": "boolean"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "refusal_reason": {"type": ["string", "null"]},
    },
}


@dataclass
class RepoPlanValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    data: Optional[dict[str, Any]] = None
    refusal_reason: str = ""


class RepoPlanValidator:
    def validate_payload(self, data: Any, request: RepoTaskRequest) -> RepoPlanValidationResult:
        errors: list[str] = []
        if not isinstance(data, dict):
            return RepoPlanValidationResult(False, ["top-level value must be object"])
        required = set(REPO_PLAN_SCHEMA["required"])
        missing = required - set(data)
        extra = set(data) - required
        if missing:
            errors.append(f"missing required fields: {sorted(missing)}")
        if extra:
            errors.append(f"unexpected fields: {sorted(extra)}")

        refusal = data.get("refusal_reason")
        if refusal is not None and not isinstance(refusal, str):
            errors.append("refusal_reason must be string or null")

        for key in ("objective_summary", "risk_level"):
            if key in data and not isinstance(data[key], str):
                errors.append(f"{key} must be string")
        if isinstance(data.get("risk_level"), str) and data["risk_level"].lower() not in REPO_PLAN_RISKS:
            errors.append(f"risk_level invalid: {data['risk_level']!r}")
        if "requires_approval" in data and not isinstance(data["requires_approval"], bool):
            errors.append("requires_approval must be boolean")

        for key in ("files_to_inspect", "files_to_modify", "expected_tests", "assumptions"):
            value = data.get(key)
            if key in data:
                if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                    errors.append(f"{key} must be array of strings")

        files_to_modify_raw = data.get("files_to_modify")
        files_to_modify: list[str] = (
            files_to_modify_raw if isinstance(files_to_modify_raw, list) else []
        )
        if len(set(files_to_modify)) > request.max_files_changed:
            errors.append("files_to_modify exceeds max_files_changed")
        for rel in files_to_modify:
            if not _is_allowed(rel, request.allowed_paths, request.disallowed_paths):
                errors.append(f"files_to_modify path not allowed: {rel}")
            if _looks_like_test_path(rel) and not request.allow_test_modifications:
                errors.append(f"test file modification not allowed: {rel}")
        for rel in data.get("files_to_inspect", []) if isinstance(data.get("files_to_inspect"), list) else []:
            if not _is_allowed(rel, request.allowed_paths, request.disallowed_paths):
                errors.append(f"files_to_inspect path not allowed: {rel}")

        steps = data.get("proposed_steps")
        if "proposed_steps" in data and not isinstance(steps, list):
            errors.append("proposed_steps must be array")
        elif isinstance(steps, list):
            if not steps and not refusal:
                errors.append("plan may be empty only when refusal_reason is non-null")
            for idx, step in enumerate(steps):
                errors.extend(self._validate_step(idx, step, request))

        expected_tests = data.get("expected_tests")
        if not refusal and (not isinstance(expected_tests, list) or not expected_tests):
            errors.append("expected_tests must be present")
        if refusal and files_to_modify:
            errors.append("refusal plans must not include files_to_modify")
        if refusal and steps:
            executable = [s for s in steps if isinstance(s, dict) and s.get("action_type") in {"patch", "test"}]
            if executable:
                errors.append("refusal plans must not include executable patch/test steps")

        return RepoPlanValidationResult(
            ok=not errors,
            errors=errors,
            data=data if not errors else None,
            refusal_reason=refusal if isinstance(refusal, str) else "",
        )

    def validate_json(self, raw: str, request: RepoTaskRequest) -> RepoPlanValidationResult:
        try:
            data = json.loads(_strip_json_fence(raw))
        except json.JSONDecodeError as e:
            return RepoPlanValidationResult(False, [f"invalid_json: {e.msg}"])
        return self.validate_payload(data, request)

    def validate_plan(self, plan: RepoTaskPlan, request: RepoTaskRequest) -> tuple[bool, str]:
        payload = _repo_plan_to_payload(plan)
        result = self.validate_payload(payload, request)
        if not result.ok:
            return False, "; ".join(result.errors)
        if not plan.valid:
            return False, plan.refusal_reason or plan.planning_error or "plan invalid"
        return True, ""

    def _validate_step(self, idx: int, step: Any, request: RepoTaskRequest) -> list[str]:
        errors: list[str] = []
        if not isinstance(step, dict):
            return [f"proposed_steps[{idx}] must be object"]
        allowed = {"step_id", "action_type", "target_path", "tool_name", "reason", "expected_output", "risk_class"}
        required = {"step_id", "action_type", "reason", "expected_output", "risk_class"}
        extra = set(step) - allowed
        missing = required - set(step)
        if extra:
            errors.append(f"proposed_steps[{idx}] unexpected fields: {sorted(extra)}")
        if missing:
            errors.append(f"proposed_steps[{idx}] missing fields: {sorted(missing)}")
        for key in required:
            if key in step and (not isinstance(step[key], str) or not step[key].strip()):
                errors.append(f"proposed_steps[{idx}].{key} must be non-empty string")
        action = step.get("action_type")
        if isinstance(action, str) and action not in REPO_PLAN_ACTIONS:
            errors.append(f"proposed_steps[{idx}].action_type invalid: {action!r}")
        risk = step.get("risk_class")
        if isinstance(risk, str) and risk.lower() not in REPO_PLAN_RISKS:
            errors.append(f"proposed_steps[{idx}].risk_class invalid: {risk!r}")
        target = step.get("target_path")
        if target is not None:
            if not isinstance(target, str):
                errors.append(f"proposed_steps[{idx}].target_path must be string or null")
            elif target:
                if not _is_allowed(target, request.allowed_paths, request.disallowed_paths):
                    errors.append(f"proposed_steps[{idx}].target_path not allowed: {target}")
                if action == "patch" and _looks_like_test_path(target) and not request.allow_test_modifications:
                    errors.append(f"test file patch step not allowed: {target}")
        tool = step.get("tool_name")
        if tool is not None and not isinstance(tool, str):
            errors.append(f"proposed_steps[{idx}].tool_name must be string or null")
        return errors


class LLMRepoPlanner:
    def __init__(
        self,
        router=None,
        validator: Optional[RepoPlanValidator] = None,
        prompt_registry=None,
    ) -> None:
        self.router = router
        self.validator = validator or RepoPlanValidator()
        self.prompt_registry = prompt_registry
        self.last_prompt_trace_summary = None

    def create_plan(self, request: RepoTaskRequest, context: RepoContext) -> RepoTaskPlan:
        try:
            router = self.router
            if router is None or request.model_provider:
                from .model_router import ModelRouter
                router = ModelRouter(default_provider=request.model_provider or None)
            system, user = self._build_prompt(request, context)
            raw, provider_name = router.complete_structured(
                "balanced",
                system,
                user,
                REPO_PLAN_SCHEMA,
                temperature=request.planning_temperature if request.planning_temperature is not None else 0.0,
                max_tokens=request.max_planning_tokens if request.max_planning_tokens is not None else 2048,
            )
            result = self.validator.validate_json(raw, request)
            if not result.ok:
                return _planning_failure(request, "llm plan invalid: " + "; ".join(result.errors), provider_name)
            if result.refusal_reason:
                return RepoTaskPlan(
                    objective_summary=request.objective[:240],
                    files_to_inspect=[],
                    files_to_modify=[],
                    proposed_steps=[],
                    risk_level="low",
                    expected_tests=[],
                    requires_approval=False,
                    valid=False,
                    refusal_reason=result.refusal_reason,
                    planning_error=result.refusal_reason,
                    provider_name=provider_name,
                )
            plan = _repo_plan_from_payload(result.data or {}, request, context)
            plan.provider_name = provider_name
            return plan
        except Exception as e:
            return _planning_failure(request, f"llm planner unavailable: {type(e).__name__}: {e}", "")

    def validate_plan(self, plan: RepoTaskPlan, request: RepoTaskRequest) -> tuple[bool, str]:
        return self.validator.validate_plan(plan, request)

    def _build_prompt(self, request: RepoTaskRequest, context: RepoContext) -> tuple[str, str]:
        repo_summary = {
            "metadata": context.metadata,
            "top_level_entries": context.top_level_entries[:40],
            "source_dirs": context.source_dirs,
            "test_dirs": context.test_dirs,
            "files": [
                {
                    "path": f.path,
                    "size_bytes": f.size_bytes,
                    "truncated": f.truncated,
                    "skipped_reason": f.skipped_reason,
                    "preview": _safe_prompt_text(f.content_preview, 1200),
                }
                for f in context.file_summaries[:12]
                if not f.skipped_reason or f.truncated
            ],
            "symbol_matches": context.symbol_matches[:10],
        }
        governance_rules = [
            "Entity proposes. Runtime disposes.",
            "LLM plan must not execute tools or include patches.",
            "No browser, network, git commit, or git push tools.",
            "Do not modify tests unless explicitly allowed.",
            "Return JSON only.",
        ]
        payload = {
            "objective": _safe_prompt_text(request.objective, 1000),
            "repo_context_summary": repo_summary,
            "allowed_paths": request.allowed_paths,
            "disallowed_paths": request.disallowed_paths,
            "max_files_changed": request.max_files_changed,
            "test_command": request.test_command,
            "governance_rules": governance_rules,
        }
        user = json.dumps(payload, indent=2)
        system = (
            "You produce bounded repository task plans only. You never execute tools. "
            "All writes/tests must later go through Runtime, Tool Bus, Approval, Sandbox, Verifier, Trace, and Praxis. "
            "Return JSON only for the supplied schema. Do not weaken tests. Do not include secrets."
        )
        if self.prompt_registry is not None:
            rendered = self.prompt_registry.render(
                "repo_planner",
                {
                    "objective": payload["objective"],
                    "repo_context": json.dumps(repo_summary, indent=2),
                    "governance_rules": "; ".join(governance_rules),
                },
            )
            self.last_prompt_trace_summary = rendered.trace_summary
            system = rendered.rendered_prompt
        return system, user


class CodeTaskPlanner:
    def create_plan(self, request: RepoTaskRequest, context: RepoContext) -> RepoTaskPlan:
        target_files = _mentioned_files(request.objective, context)
        if not target_files and context.symbol_matches:
            target_files = [context.symbol_matches[0]["path"]]

        patch_plans = _patches_for_request(request, context, target_files)
        files_to_modify = [p.path for p in patch_plans] or target_files[:1]
        steps = [
            RepoTaskStep("inspect", "inspect", ",".join(target_files), "build bounded context", "read_file", "bounded source context", "low"),
            RepoTaskStep("patch", "patch", ",".join(files_to_modify), "apply small governed patch", "patch_file", "narrow implementation patch", "medium"),
            RepoTaskStep("test", "test", " ".join(request.test_command), "run requested tests", "run_tests", "test command passes", "medium"),
        ]
        valid = bool(context.repo_root and request.objective.strip())
        if valid and not patch_plans:
            # A plan whose patch step has no patch content cannot achieve any
            # objective; refusing here is honest, silently "succeeding" is not.
            # Refusal plans must carry no executable steps (validator contract).
            return RepoTaskPlan(
                objective_summary=request.objective[:240],
                files_to_inspect=target_files,
                files_to_modify=[],
                proposed_steps=[],
                risk_level="low",
                expected_tests=[],
                requires_approval=request.require_approval_before_write,
                patch_plans=[],
                valid=False,
                refusal_reason=(
                    "heuristic planner has no patch strategy for this objective; "
                    "use --planner llm or hybrid"
                ),
            )
        return RepoTaskPlan(
            objective_summary=request.objective[:240],
            files_to_inspect=target_files,
            files_to_modify=files_to_modify,
            proposed_steps=steps,
            risk_level="medium" if files_to_modify else "low",
            expected_tests=[" ".join(request.test_command)],
            requires_approval=request.require_approval_before_write,
            patch_plans=patch_plans,
            valid=valid,
            refusal_reason="" if valid else "insufficient objective or context",
        )

    def validate_plan(self, plan: RepoTaskPlan, request: Optional[RepoTaskRequest] = None) -> tuple[bool, str]:
        if not plan.valid:
            return False, plan.refusal_reason or plan.planning_error or "plan invalid"
        if not plan.proposed_steps:
            return False, "plan has no steps"
        if plan.files_to_modify and not plan.expected_tests:
            return False, "plan with modifications must include test strategy"
        if request is not None:
            return RepoPlanValidator().validate_plan(plan, request)
        return True, ""


class PatchExecutor:
    def __init__(self, runtime, card: AgentCard, repo_root: str) -> None:
        self.runtime = runtime
        self.card = card
        self.repo_root = Path(repo_root).resolve()

    def apply(self, request: RepoTaskRequest, patch_plans: list[PatchPlan]) -> PatchResult:
        if len({p.path for p in patch_plans}) > request.max_files_changed:
            return PatchResult(False, errors=["max_files_changed exceeded"])
        result = PatchResult(applied=True)
        for plan in patch_plans:
            if not _is_allowed(plan.path, request.allowed_paths, request.disallowed_paths):
                result.applied = False
                result.errors.append(f"path not allowed: {plan.path}")
                continue
            try:
                _resolve_under(self.repo_root, plan.path)
            except ValueError as e:
                result.applied = False
                result.errors.append(str(e))
                continue
            if plan.content is not None:
                cmd = _cmd(self.card, "write_file", {"path": plan.path, "content": plan.content})
            else:
                cmd = _cmd(self.card, "patch_file", {"path": plan.path, "patch": plan.patch})
            res = self.runtime.submit(cmd, self.card)
            result.command_ids.append(cmd.id)
            if res.approval_receipt is not None:
                result.approval_summaries.append(res.approval_receipt.to_dict())
            if res.ok:
                result.files_changed.append(plan.path)
                result.summaries.append(plan.summary or res.observation.artifacts.get("summary", "patched"))
            else:
                result.applied = False
                result.errors.append(res.verifier.reason or res.observation.stderr or "patch failed")
        return result


class TestRunnerAdapter:
    __test__ = False  # not a pytest test class

    def __init__(self, runtime, card: AgentCard, default_timeout: int = 30) -> None:
        self.runtime = runtime
        self.card = card
        self.default_timeout = default_timeout

    def run(self, request: RepoTaskRequest) -> TestRunResult:
        command = request.test_command or ["python3", "-m", "pytest", "-q"]
        timeout = self.default_timeout
        if len(command) == 2 and command[0].startswith("python") and command[1].endswith(".py"):
            args = {"test_file": command[1], "timeout_seconds": timeout}
        else:
            args = {"command": command, "timeout_seconds": timeout}
        tool = "run_tests"
        t0 = time.perf_counter()
        res = self.runtime.submit(_cmd(self.card, tool, args, risk=RiskLevel.MEDIUM), self.card)
        obs = res.observation
        duration = int((time.perf_counter() - t0) * 1000)
        return TestRunResult(
            command=command,
            exit_code=obs.exit_code if obs.exit_code is not None else (0 if res.ok else 1),
            stdout=obs.stdout,
            stderr=obs.stderr,
            duration_ms=int(obs.artifacts.get("duration_ms", duration)),
            timed_out=bool(obs.artifacts.get("timed_out", False)),
        )


class TestFailureAnalyzer:
    __test__ = False  # not a pytest test class

    def analyze(self, result: TestRunResult) -> dict[str, str | list[str]]:
        output = f"{result.stdout}\n{result.stderr}"
        failures = re.findall(r"FAILED\s+([^\s]+)", output)
        if not failures:
            failures = re.findall(r"([A-Za-z0-9_./-]+\.py)::([A-Za-z0-9_]+)", output)
            failures = [f"{a}::{b}" for a, b in failures]
        likely = "unknown"
        if "AssertionError" in output:
            likely = "assertion failure"
        elif "SyntaxError" in output:
            likely = "syntax error"
        elif result.timed_out:
            likely = "test timeout"
        return {
            "summary": "tests passed" if result.passed else f"tests failed: {likely}",
            "failing_tests": failures[:10],
            "likely_cause": likely,
            "suggested_action": "inspect failing test output and apply a narrow repair",
        }


class RepairLoop:
    def __init__(
        self,
        patch_executor: PatchExecutor,
        test_runner: TestRunnerAdapter,
        analyzer: Optional[TestFailureAnalyzer] = None,
        repair_provider: Optional[Callable[[RepairAttempt], list[PatchPlan]]] = None,
    ) -> None:
        self.patch_executor = patch_executor
        self.test_runner = test_runner
        self.analyzer = analyzer or TestFailureAnalyzer()
        self.repair_provider = repair_provider

    def run(self, request: RepoTaskRequest, initial_patches: list[PatchPlan]) -> tuple[PatchResult, TestRunResult, list[RepairAttempt]]:
        attempts: list[RepairAttempt] = []
        patches = initial_patches
        patch_result = PatchResult(applied=True)
        test_result = TestRunResult(request.test_command, 1)
        max_iter = max(1, request.max_repair_iterations)
        for iteration in range(1, max_iter + 1):
            if patches:
                patch_result = self.patch_executor.apply(request, patches)
            test_result = self.test_runner.run(request)
            analysis = self.analyzer.analyze(test_result)
            attempt = RepairAttempt(
                iteration=iteration,
                failure_summary=str(analysis["summary"]),
                proposed_repair="; ".join(p.summary for p in patches) if patches else "run tests without repair",
                files_touched=list(patch_result.files_changed),
                test_result=test_result,
            )
            attempts.append(attempt)
            if test_result.passed:
                return patch_result, test_result, attempts
            if self.repair_provider is None:
                break
            patches = self.repair_provider(attempt)
            if not patches:
                break
        return patch_result, test_result, attempts


class RepositoryAgentLoop:
    def __init__(self, kernel=None) -> None:
        self.kernel = kernel
        self.context_builder = RepoContextBuilder()
        self.planner = CodeTaskPlanner()
        self.analyzer = TestFailureAnalyzer()

    def run(self, task_request: RepoTaskRequest, *, apply: bool = True,
            dry_run: bool = False) -> CodeTaskReport:
        context = self.context_builder.build(task_request)
        from . import build_runtime
        from .sandbox import SandboxUnavailableError

        effective_dry_run = dry_run or task_request.planner_mode == "dry_run"
        profile_name = (
            SandboxProfileName.NO_EXEC_READONLY.value
            if (not apply or effective_dry_run)
            else task_request.sandbox_profile
        )
        if self.kernel is None:
            try:
                sandbox, _policy = create_profiled_sandbox(
                    profile_name,
                    context.repo_root,
                    allowed_paths=task_request.allowed_paths,
                    disallowed_paths=task_request.disallowed_paths,
                )
            except SandboxUnavailableError as e:
                return CodeTaskReport(
                    task_id=task_request.task_id,
                    objective=task_request.objective,
                    plan_summary="",
                    final_status="sandbox_unavailable",
                    sandbox_profile=profile_name,
                    limitations=[str(e)],
                )
            kernel = build_runtime(
                sandbox=sandbox,
                approval_gate=_approval_gate_for(task_request),
            )
        else:
            kernel = self.kernel
        self.kernel = kernel
        card = _repo_card(task_request)
        plan, planner_mode, planning_errors, fallback_reason = _create_plan_for_request(
            self.planner, kernel.router, task_request, context)
        ok, reason = RepoPlanValidator().validate_plan(plan, task_request)
        report = CodeTaskReport(
            task_id=task_request.task_id,
            objective=task_request.objective,
            plan_summary=plan.objective_summary,
            planner_mode=planner_mode,
            model_provider=plan.provider_name or (task_request.model_provider or ""),
            planning_errors=planning_errors,
            fallback_reason=fallback_reason,
            plan_assumptions=list(plan.assumptions),
            files_inspected=plan.files_to_inspect,
            limitations=list(context.limitations),
            next_recommendation="Run with --apply after reviewing the plan." if not apply else "",
            sandbox_profile=profile_name,
        )
        report.approval_summaries = _approval_requirements(kernel, plan, card)
        if not ok:
            report.final_status = "planning_failed"
            report.limitations.append(reason)
            report.planning_errors.append(reason)
            return _finalize_report(kernel, report)
        if not apply or effective_dry_run:
            report.final_status = "dry_run" if effective_dry_run else "planned"
            if effective_dry_run:
                report.next_recommendation = "Dry-run complete; approval requirements recorded."
            return _finalize_report(kernel, report)
        executor = PatchExecutor(kernel.runtime, card, context.repo_root)
        runner = TestRunnerAdapter(kernel.runtime, card)
        repair_loop = RepairLoop(executor, runner, self.analyzer)
        patch_result, test_result, attempts = repair_loop.run(task_request, plan.patch_plans)
        report.files_changed = patch_result.files_changed
        report.tests_run = [task_request.test_command]
        report.test_result = test_result
        report.repair_attempts = attempts
        report.approval_summaries.extend(patch_result.approval_summaries)
        if not patch_result.applied:
            report.final_status = "patch_failed"
            report.limitations.extend(patch_result.errors)
        elif test_result.passed:
            report.final_status = "succeeded"
            report.next_recommendation = "Review the patch and continue with normal code review."
        else:
            report.final_status = "failed"
            report.next_recommendation = "Inspect the recorded failure summary before expanding scope."
        return _finalize_report(kernel, report)


_PRAXIS_METABOLISM: Optional["PraxisMetabolism"] = None


def _finalize_report(kernel, report: CodeTaskReport) -> CodeTaskReport:
    report.praxis_report = _process_praxis(kernel, report)
    report.sandbox_violations = [
        r.get("reason", "") for r in kernel.trace.replay()
        if r.get("kind") == "sandbox_violation"
    ]
    return report


def _process_praxis(kernel, report: CodeTaskReport) -> "PraxisReport":
    global _PRAXIS_METABOLISM
    from .praxis import PraxisMetabolism

    if _PRAXIS_METABOLISM is None:
        _PRAXIS_METABOLISM = PraxisMetabolism()
    return _PRAXIS_METABOLISM.process_repo_report(
        report,
        trace=kernel.trace,
        run_id=kernel.trace.run_id,
        memory_fabric=kernel.memory,
    )


def _create_plan_for_request(
    deterministic_planner: CodeTaskPlanner,
    router,
    request: RepoTaskRequest,
    context: RepoContext,
) -> tuple[RepoTaskPlan, str, list[str], str]:
    mode = (request.planner_mode or "deterministic").lower()
    if mode == "demo-heuristic":
        mode = "deterministic"
    if mode not in {"deterministic", "llm", "hybrid", "dry_run"}:
        return _planning_failure(request, f"unknown planner_mode: {request.planner_mode}", ""), mode, [f"unknown planner_mode: {request.planner_mode}"], ""
    if mode in {"deterministic", "dry_run"}:
        plan = deterministic_planner.create_plan(request, context)
        return plan, mode, [], ""

    llm = LLMRepoPlanner(router=router)
    plan = llm.create_plan(request, context)
    ok, reason = llm.validate_plan(plan, request)
    if mode == "llm":
        return plan, "llm", ([] if ok else [reason]), ""
    if ok:
        return plan, "hybrid", [], ""

    fallback = deterministic_planner.create_plan(request, context)
    fallback_reason = reason or plan.planning_error or plan.refusal_reason or "llm planning failed"
    fallback.assumptions.append(f"hybrid fallback used: {fallback_reason}")
    return fallback, "hybrid", [fallback_reason], fallback_reason


def _planning_failure(request: RepoTaskRequest, reason: str, provider_name: str) -> RepoTaskPlan:
    return RepoTaskPlan(
        objective_summary=request.objective[:240],
        files_to_inspect=[],
        files_to_modify=[],
        proposed_steps=[],
        risk_level="low",
        expected_tests=[],
        requires_approval=False,
        valid=False,
        refusal_reason=reason,
        planning_error=reason,
        provider_name=provider_name,
    )


def _repo_plan_from_payload(data: dict[str, Any], request: RepoTaskRequest, context: RepoContext) -> RepoTaskPlan:
    steps = [
        RepoTaskStep(
            step_id=str(step.get("step_id", "")),
            action=str(step.get("action_type", "")),
            target=str(step.get("target_path") or ""),
            rationale=str(step.get("reason", "")),
            tool_name=str(step.get("tool_name") or ""),
            expected_output=str(step.get("expected_output", "")),
            risk_class=str(step.get("risk_class", "low")),
        )
        for step in data.get("proposed_steps", [])
    ]
    files_to_modify = list(dict.fromkeys(data.get("files_to_modify", [])))
    files_to_inspect = list(dict.fromkeys(data.get("files_to_inspect", [])))
    patch_plans = _patches_for_request(request, context, files_to_modify or files_to_inspect)
    return RepoTaskPlan(
        objective_summary=str(data.get("objective_summary", request.objective[:240]))[:240],
        files_to_inspect=files_to_inspect,
        files_to_modify=files_to_modify or [p.path for p in patch_plans],
        proposed_steps=steps,
        risk_level=str(data.get("risk_level", "medium")),
        expected_tests=list(data.get("expected_tests", [])),
        requires_approval=bool(data.get("requires_approval", request.require_approval_before_write)),
        patch_plans=patch_plans,
        assumptions=list(data.get("assumptions", [])),
    )


def _repo_plan_to_payload(plan: RepoTaskPlan) -> dict[str, Any]:
    return {
        "objective_summary": plan.objective_summary,
        "files_to_inspect": list(plan.files_to_inspect),
        "files_to_modify": list(plan.files_to_modify),
        "proposed_steps": [
            {
                "step_id": s.step_id,
                "action_type": s.action,
                "target_path": s.target if s.action != "test" and s.target and "," not in s.target else None,
                "tool_name": s.tool_name or None,
                "reason": s.rationale,
                "expected_output": s.expected_output or "planned step output",
                "risk_class": s.risk_class or plan.risk_level,
            }
            for s in plan.proposed_steps
        ],
        "risk_level": plan.risk_level,
        "expected_tests": list(plan.expected_tests),
        "requires_approval": plan.requires_approval,
        "assumptions": list(plan.assumptions),
        "refusal_reason": plan.refusal_reason or None,
    }


def _patches_for_request(request: RepoTaskRequest, context: RepoContext, target_files: list[str]) -> list[PatchPlan]:
    patch_plans: list[PatchPlan] = []
    replacement = _parse_replacement(request.objective)
    if replacement and target_files:
        old, new = replacement
        summary = f"replace {old!r} with {new!r}"
        rel = target_files[0]
        source = _read_context_content(context, rel)
        if source and old in source:
            patch_plans.append(PatchPlan(rel, _unified_replace_patch(source, old, new), summary=summary))
            return patch_plans

    zero_division = (
        "divide" in request.objective.lower()
        and ("zero" in request.objective.lower() or "validation" in request.objective.lower())
    )
    for rel in target_files:
        source = _read_context_content(context, rel)
        if zero_division and source and "def divide" in source and "return a / b" in source and "raise ValueError" not in source:
            old = "def divide(a, b):\n    return a / b"
            new = "def divide(a, b):\n    if b == 0:\n        raise ValueError(\"division by zero\")\n    return a / b"
            if old in source:
                patch_plans.append(PatchPlan(rel, content=source.replace(old, new, 1), summary="add zero-division validation"))
                return patch_plans
    return patch_plans


def _strip_json_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        brace = text.find("{")
        if brace >= 0:
            text = text[brace:]
    return text


def _safe_prompt_text(text: str, limit: int) -> str:
    redacted = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text or "")
    if len(redacted) <= limit:
        return redacted
    return redacted[:limit] + f"\n... [truncated {len(redacted) - limit} chars]"


def _looks_like_test_path(rel: str) -> bool:
    path = rel.replace("\\", "/")
    name = path.rsplit("/", 1)[-1]
    return path.startswith("tests/") or path.startswith("test/") or name.startswith("test_") or name.endswith("_test.py")


def _approval_gate_for(request: RepoTaskRequest):
    mode = ApprovalMode(request.approval_mode)
    if mode is ApprovalMode.AUTO:
        # Repo auto mode: R0–R3 only; predicate may narrow, never widen to R4/R5.
        return AutoApprover(
            lambda r: True,
            allow_r2=True,
            allow_r3=True,
            allow_r4=False,
            allow_r5=False,
        )
    if mode is ApprovalMode.DENY:
        return DenyAllApprover()
    return make_approval_gate(mode)


def _approval_requirements(kernel, plan: RepoTaskPlan, card: AgentCard) -> list[dict]:
    policy = ApprovalPolicy()
    summaries: list[dict] = []
    for patch in plan.patch_plans:
        if patch.content is not None:
            cmd = _cmd(card, "write_file", {"path": patch.path, "content": patch.content})
        else:
            cmd = _cmd(card, "patch_file", {"path": patch.path, "patch": patch.patch})
        tool_spec = kernel.tools.get(cmd.tool)
        decision = kernel.policy.evaluate(cmd, card)
        requirement = policy.resolve(cmd, decision, tool_spec)
        preview = build_preview(cmd, kernel.sandbox, tool_spec) if requirement.preview_required else None
        summaries.append({
            "tool": cmd.tool,
            "path": patch.path,
            "risk_class": requirement.risk_class.value,
            "required": requirement.required,
            "preview_required": requirement.preview_required,
            "confirmation_level": requirement.confirmation_level,
            "reason": requirement.reason,
            "preview": preview.to_dict() if preview else None,
        })
    return summaries


def _repo_card(request: RepoTaskRequest) -> AgentCard:
    allowed_tools = ["read_file", "list_dir", "search_text", "write_file",
                     "patch_file", "run_tests", "run_shell"]
    return AgentCard.make(
        name="Repository Agent Loop",
        agent_class=AgentClass.EXECUTION,
        mission="bounded repository coding task",
        authority=AuthorityScope(
            write_paths=request.allowed_paths,
            read_paths=request.allowed_paths,
            max_risk=RiskLevel.HIGH,
        ),
        allowed_tools=allowed_tools,
        denied_tools=[],
    )


def _cmd(card: AgentCard, tool: str, args: dict, risk: RiskLevel = RiskLevel.MEDIUM) -> CommandEnvelope:
    return CommandEnvelope.make(
        issuer_card_id=card.id,
        tool=tool,
        args=args,
        rationale="repository agent loop",
        declared_risk=risk,
        expected_effect="bounded repository task step",
    )


def _resolve_under(root: Path, rel: str) -> Path:
    candidate = (root / rel).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path escapes repo root: {rel}")
    return candidate


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_secret(path: Path) -> bool:
    return path.name in SECRET_NAMES or "secret" in path.name.lower()


def _skip_path(path: Path) -> bool:
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    return any(part in ignored or (part.startswith(".") and part not in {".", ".."})
               for part in path.parts)


def _is_allowed(rel: str, allowed: list[str], disallowed: list[str]) -> bool:
    norm = rel.replace("\\", "/").lstrip("./")
    if any(_match_path(norm, pat) for pat in disallowed):
        return False
    return any(pat == "*" or _match_path(norm, pat) for pat in (allowed or ["*"]))


def _match_path(path: str, pattern: str) -> bool:
    pat = pattern.replace("\\", "/").rstrip("/")
    return path == pat or path.startswith(pat + "/") or fnmatch.fnmatch(path, pat)


def _keywords(objective: str) -> str:
    quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", objective)
    values = [a or b for a, b in quoted]
    if values:
        return values[0]
    words = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", objective)
             if len(w) > 3]
    return words[0] if words else ""


def _mentioned_files(objective: str, context: RepoContext) -> list[str]:
    candidates = _objective_file_mentions(objective)
    known = {f.path for f in context.file_summaries}
    out = [c for c in candidates if c in known or any(f.path == c for f in context.file_summaries)]
    return list(dict.fromkeys(out))


def _objective_file_mentions(objective: str) -> list[str]:
    return [m.group(0).lstrip("./") for m in re.finditer(
        r"[\w./-]+\.(?:py|md|txt|toml|json)", objective)]


def _parse_replacement(objective: str) -> Optional[tuple[str, str]]:
    patterns = [
        r"replace\s+['\"](.+?)['\"]\s+with\s+['\"](.+?)['\"]",
        r"change\s+['\"](.+?)['\"]\s+to\s+['\"](.+?)['\"]",
    ]
    for pat in patterns:
        m = re.search(pat, objective, flags=re.I)
        if m:
            return m.group(1), m.group(2)
    return None


def _read_context_content(context: RepoContext, rel: str) -> str:
    for f in context.file_summaries:
        if f.path == rel:
            return f.content_preview
    return ""


def _unified_replace_patch(content: str, old: str, new: str) -> str:
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if old in line:
            replaced = line.replace(old, new, 1)
            before = lines[idx - 1] if idx > 0 else None
            after = lines[idx + 1] if idx + 1 < len(lines) else None
            body = ["--- a/file\n", "+++ b/file\n", "@@\n"]
            if before is not None:
                body.append(f" {before}\n")
            body.append(f"-{line}\n")
            body.append(f"+{replaced}\n")
            if after is not None:
                body.append(f" {after}\n")
            return "".join(body)
    return ""
