"""Governed prompt manifests, rendering, and trace-safe summaries (P1.2)."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from .model_config import ModelConfigBundle
from .secrets import SecretRedactor
from .yaml_minimal import YamlParseError, load_yaml


class PromptSystemError(ValueError):
    pass


class PromptValidationError(PromptSystemError):
    pass


class PromptRenderError(PromptSystemError):
    pass


KNOWN_RISK_TIERS = {
    "trivial", "low", "medium", "high", "critical",
    "r0", "r1", "r2", "r3", "r4", "r5",
}
SERIOUS_RISK_TIERS = {"medium", "high", "critical", "r2", "r3", "r4", "r5"}
DEFAULT_FORBIDDEN = {
    "execute_tools",
    "modify_files",
    "reveal_secrets",
    "override_policy",
    "ignore_custos",
    "change_tests_without_permission",
}
SECRET_MARKER = "[REDACTED]"
PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")
SECRET_LIKE_RE = re.compile(
    r"(?i)(\bsk-[A-Za-z0-9_-]{8,}\b|Bearer\s+[A-Za-z0-9._~+/=-]{8,}|"
    r"\b(?:OPENAI|ANTHROPIC|AUREL|AWS|AZURE|GITHUB|GITLAB|HF)_?"
    r"(?:API_KEY|SECRET|TOKEN|PASSWORD)\s*[=:]\s*\S+)"
)


@dataclass(frozen=True)
class PromptPolicy:
    may_execute_tools: bool = False
    may_modify_files: bool = False
    may_request_secrets: bool = False
    may_expand_authority: bool = False
    raw_prompt_trace_allowed: bool = False
    trace_summary_required: bool = True

    @classmethod
    def from_mapping(cls, data: Any) -> "PromptPolicy":
        if not isinstance(data, dict):
            raise PromptValidationError("policy must be a mapping")
        return cls(
            may_execute_tools=bool(data.get("may_execute_tools", False)),
            may_modify_files=bool(data.get("may_modify_files", False)),
            may_request_secrets=bool(data.get("may_request_secrets", False)),
            may_expand_authority=bool(data.get("may_expand_authority", False)),
            raw_prompt_trace_allowed=bool(data.get("raw_prompt_trace_allowed", False)),
            trace_summary_required=bool(data.get("trace_summary_required", True)),
        )


@dataclass(frozen=True)
class PromptEvalSpec:
    name: str
    description: str = ""

    @classmethod
    def from_item(cls, item: Any) -> "PromptEvalSpec":
        if isinstance(item, str):
            return cls(name=item)
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            if not name:
                raise PromptValidationError("eval entry missing name")
            return cls(name=name, description=str(item.get("description", "")))
        raise PromptValidationError("evals entries must be strings or mappings")


@dataclass(frozen=True)
class PromptMetadata:
    id: str
    version: str
    owner: str
    status: str
    purpose: str
    description: str
    allowed_model_profiles: list[str]
    allowed_tasks: list[str]
    risk_tier: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    policy: PromptPolicy
    forbidden: list[str]
    evals: list[PromptEvalSpec] = field(default_factory=list)
    source_path: str = ""


@dataclass(frozen=True)
class PromptTemplate:
    metadata: PromptMetadata
    template: str

    @property
    def template_hash(self) -> str:
        return _sha256(self.template)

    @property
    def variables(self) -> list[str]:
        return sorted(set(PLACEHOLDER_RE.findall(self.template)))

    def render(
        self,
        context: "PromptRenderContext",
        *,
        redactor: SecretRedactor | None = None,
        preview_chars: int = 240,
    ) -> "PromptRenderResult":
        redactor = redactor or SecretRedactor()
        variables = {str(k): str(v) for k, v in context.variables.items()}
        missing = [name for name in self.variables if name not in variables]
        if missing:
            raise PromptRenderError(
                f"missing template variables for {self.metadata.id}: {', '.join(missing)}"
            )

        def replace(match: re.Match[str]) -> str:
            return variables[match.group(1)]

        rendered = PLACEHOLDER_RE.sub(replace, self.template)
        if _contains_raw_secret(rendered):
            # Rendering may include user/context material, so fail before trace output.
            raise PromptRenderError(
                f"rendered prompt contains raw secret-like value: {self.metadata.id}"
            )
        redacted_preview = _bounded(redactor.redact(rendered), preview_chars)
        if _contains_raw_secret(redacted_preview):
            redacted_preview = SECRET_MARKER
        summary = PromptTraceSummary(
            prompt_id=self.metadata.id,
            version=self.metadata.version,
            owner=self.metadata.owner,
            purpose=self.metadata.purpose,
            allowed_model_profiles=list(self.metadata.allowed_model_profiles),
            allowed_tasks=list(self.metadata.allowed_tasks),
            risk_tier=self.metadata.risk_tier,
            template_hash=self.template_hash,
            rendered_hash=_sha256(rendered),
            variables_used=sorted(self.variables),
            raw_prompt_stored=False,
            rendered_preview_redacted=redacted_preview,
        )
        raw_prompt_allowed = (
            context.include_raw_prompt
            and self.metadata.policy.raw_prompt_trace_allowed
        )
        return PromptRenderResult(
            prompt_id=self.metadata.id,
            rendered_prompt=rendered if raw_prompt_allowed else "",
            trace_summary=summary,
        )


@dataclass(frozen=True)
class PromptRenderContext:
    variables: dict[str, Any] = field(default_factory=dict)
    include_raw_prompt: bool = False


@dataclass(frozen=True)
class PromptTraceSummary:
    prompt_id: str
    version: str
    owner: str
    purpose: str
    allowed_model_profiles: list[str]
    allowed_tasks: list[str]
    risk_tier: str
    template_hash: str
    rendered_hash: str
    variables_used: list[str]
    raw_prompt_stored: bool = False
    rendered_preview_redacted: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rendered_preview_redacted"] = SecretRedactor().redact(
            str(data.get("rendered_preview_redacted", ""))
        )
        return data


@dataclass(frozen=True)
class PromptRenderResult:
    prompt_id: str
    rendered_prompt: str
    trace_summary: PromptTraceSummary


class PromptRegistry:
    def __init__(
        self,
        prompts_dir: str | Path | None = None,
        *,
        model_config: ModelConfigBundle | None = None,
        validate_model_profiles: bool = False,
        redactor: SecretRedactor | None = None,
    ) -> None:
        self.prompts_dir = Path(prompts_dir) if prompts_dir else _default_prompts_dir()
        self.model_config = model_config
        self.validate_model_profiles = validate_model_profiles
        self.redactor = redactor or SecretRedactor()
        self._prompts: dict[str, PromptTemplate] = {}

    def load(self) -> "PromptRegistry":
        if not self.prompts_dir.is_dir():
            raise PromptValidationError(f"prompts directory not found: {self.prompts_dir}")
        prompts: dict[str, PromptTemplate] = {}
        for path in sorted(self.prompts_dir.rglob("*.yaml")):
            prompt = self._load_file(path)
            if prompt.metadata.id in prompts:
                raise PromptValidationError(f"duplicate prompt id: {prompt.metadata.id}")
            prompts[prompt.metadata.id] = prompt
        if not prompts:
            raise PromptValidationError(f"no prompt manifests found in {self.prompts_dir}")
        self._prompts = prompts
        return self

    @classmethod
    def load_default(
        cls,
        *,
        model_config: ModelConfigBundle | None = None,
        validate_model_profiles: bool = False,
    ) -> "PromptRegistry":
        return cls(
            model_config=model_config,
            validate_model_profiles=validate_model_profiles,
        ).load()

    def list_prompts(self) -> list[PromptMetadata]:
        return [self._prompts[key].metadata for key in sorted(self._prompts)]

    def get(self, prompt_id: str) -> PromptTemplate:
        prompt = self._prompts.get(prompt_id)
        if prompt is None:
            raise PromptValidationError(f"unknown prompt id: {prompt_id}")
        return prompt

    def render(
        self,
        prompt_id: str,
        variables: dict[str, Any],
        *,
        include_raw_prompt: bool = False,
    ) -> PromptRenderResult:
        return self.get(prompt_id).render(
            PromptRenderContext(variables=variables, include_raw_prompt=include_raw_prompt),
            redactor=self.redactor,
        )

    def validate_all(self) -> list[PromptMetadata]:
        if not self._prompts:
            self.load()
        return self.list_prompts()

    def _load_file(self, path: Path) -> PromptTemplate:
        try:
            text = path.read_text(encoding="utf-8")
            data = load_yaml(text)
        except (OSError, YamlParseError) as e:
            raise PromptValidationError(f"invalid prompt manifest {path}: {e}") from e
        if _contains_raw_secret(text):
            raise PromptValidationError(f"prompt manifest contains raw secret-like value: {path}")
        return self._parse_manifest(data, path)

    def _parse_manifest(self, data: dict[str, Any], path: Path) -> PromptTemplate:
        required = ("id", "version", "owner", "status", "purpose", "template")
        for key in required:
            if not str(data.get(key, "")).strip():
                raise PromptValidationError(f"{path}: {key} is required")

        allowed_model_profiles = data.get("allowed_model_profiles")
        if not isinstance(allowed_model_profiles, list):
            raise PromptValidationError(f"{path}: allowed_model_profiles must be a list")
        allowed_tasks = data.get("allowed_tasks")
        if not isinstance(allowed_tasks, list):
            raise PromptValidationError(f"{path}: allowed_tasks must be a list")
        risk_tier = str(data.get("risk_tier", "")).strip().lower()
        if not risk_tier:
            raise PromptValidationError(f"{path}: risk_tier is required")
        if risk_tier not in KNOWN_RISK_TIERS:
            allowed = ", ".join(sorted(KNOWN_RISK_TIERS))
            raise PromptValidationError(
                f"{path}: invalid risk_tier {risk_tier!r}; allowed: {allowed}"
            )

        input_schema = data.get("input_schema")
        if not isinstance(input_schema, dict):
            raise PromptValidationError(f"{path}: input_schema must be a mapping")
        output_schema = data.get("output_schema")
        if risk_tier in SERIOUS_RISK_TIERS and not isinstance(output_schema, dict):
            raise PromptValidationError(f"{path}: serious prompts require output_schema")
        if output_schema is None:
            output_schema = {}
        if not isinstance(output_schema, dict):
            raise PromptValidationError(f"{path}: output_schema must be a mapping")

        policy = PromptPolicy.from_mapping(data.get("policy"))
        _validate_policy(policy, [str(t) for t in allowed_tasks], path)

        forbidden = data.get("forbidden") or []
        if not isinstance(forbidden, list):
            raise PromptValidationError(f"{path}: forbidden must be a list")
        forbidden_str = [str(item) for item in forbidden]
        if _is_core_prompt(path, str(data["id"])) and not _has_override_forbidden(forbidden_str):
            raise PromptValidationError(f"{path}: core prompts must forbid override_policy")

        evals_raw = data.get("evals") or []
        if not isinstance(evals_raw, list):
            raise PromptValidationError(f"{path}: evals must be a list")
        evals = [PromptEvalSpec.from_item(item) for item in evals_raw]

        template = _template_text(data.get("template"))
        if not template.strip():
            raise PromptValidationError(f"{path}: template is required")
        if _contains_raw_secret(template):
            raise PromptValidationError(f"{path}: template contains raw secret-like value")

        profiles = [str(p) for p in allowed_model_profiles]
        if self.model_config is not None and self.validate_model_profiles:
            known = set(self.model_config.profiles)
            missing = [p for p in profiles if p not in known]
            if missing:
                raise PromptValidationError(
                    f"{path}: unknown model profile(s): {', '.join(missing)}"
                )

        meta = PromptMetadata(
            id=str(data["id"]),
            version=str(data["version"]),
            owner=str(data["owner"]),
            status=str(data["status"]),
            purpose=str(data["purpose"]),
            description=str(data.get("description", "")),
            allowed_model_profiles=profiles,
            allowed_tasks=[str(t) for t in allowed_tasks],
            risk_tier=risk_tier,
            input_schema=input_schema,
            output_schema=output_schema,
            policy=policy,
            forbidden=forbidden_str,
            evals=evals,
            source_path=str(path),
        )
        return PromptTemplate(metadata=meta, template=template)


def prompt_metadata_to_safe_dict(metadata: PromptMetadata) -> dict[str, Any]:
    data = asdict(metadata)
    data["policy"] = asdict(metadata.policy)
    data["evals"] = [asdict(e) for e in metadata.evals]
    return _redact_object(data)


def _validate_policy(policy: PromptPolicy, tasks: list[str], path: Path) -> None:
    if policy.may_expand_authority:
        raise PromptValidationError(f"{path}: policy may not allow may_expand_authority")
    if policy.may_request_secrets:
        raise PromptValidationError(f"{path}: policy may not allow may_request_secrets")
    is_planning = any("planning" in task or "plan" in task for task in tasks)
    if is_planning and policy.may_execute_tools:
        raise PromptValidationError(f"{path}: planning prompts may not execute tools")
    if is_planning and policy.may_modify_files:
        raise PromptValidationError(f"{path}: planning prompts may not modify files")


def _template_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value or "")


def _default_prompts_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "prompts"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bounded(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 14)] + "...[truncated]"


def _contains_raw_secret(text: str) -> bool:
    if not text:
        return False
    redacted = SecretRedactor().redact(text)
    return redacted != text or SECRET_LIKE_RE.search(text) is not None


def _has_override_forbidden(items: list[str]) -> bool:
    normalized = {item.lower().replace("-", "_") for item in items}
    return bool({"override_policy", "ignore_custos"} & normalized)


def _is_core_prompt(path: Path, prompt_id: str) -> bool:
    return "system" in path.parts or prompt_id in {
        "repo_planner", "patch_synthesizer", "reviewer", "summarizer",
    }


def _redact_object(value: Any) -> Any:
    redactor = SecretRedactor()
    if isinstance(value, str):
        return redactor.redact(value)
    if isinstance(value, list):
        return [_redact_object(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _redact_object(v) for k, v in value.items()}
    return value


def safe_json(data: Any) -> str:
    return SecretRedactor().redact(json.dumps(_redact_object(data), indent=2, sort_keys=True))
