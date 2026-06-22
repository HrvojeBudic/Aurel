"""
tool_contracts.py — Tool Contract & Schema Enforcement (P0.10).

ToolSpec carried schemas, but they were advisory. A tool could be invoked with
missing args, wrong types, unsafe extra args, oversized payloads, or invalid
enum values, and its *output* was trusted structurally. That is an injection and
reward-hacking surface.

This module makes the contract canonical and enforced:

  - ``ToolContract``          — the canonical contract for one tool.
  - ``ToolInputValidator``    — validates ``CommandEnvelope.args`` BEFORE policy,
                                budget, or execution.
  - ``ToolOutputValidator``   — validates the ``ObservationEnvelope`` AFTER
                                execution and BEFORE it can be a verified success.
  - ``ToolContractRegistry``  — the set of registered contracts. No contract ->
                                no execution.

Each contract also declares a ``side_effect_profile`` so the policy/risk engine
can reason about what a tool actually does (filesystem write, shell execution,
network, irreversible action, ...) instead of trusting a name.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .core_types import ObservationEnvelope, RiskLevel


# --------------------------------------------------------------------------- #
#  Side effects — what a tool actually does to the world.
# --------------------------------------------------------------------------- #
class SideEffect(str, Enum):
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    SHELL_EXECUTION = "shell_execution"
    NETWORK_REQUEST = "network_request"
    MEMORY_WRITE = "memory_write"
    EXTERNAL_API_CALL = "external_api_call"
    IRREVERSIBLE_ACTION = "irreversible_action"


# Side effect -> intrinsic risk floor. The policy engine maxes these together
# with its own per-tool floor; it only ever escalates, never lowers.
SIDE_EFFECT_RISK: dict[SideEffect, RiskLevel] = {
    SideEffect.FILESYSTEM_READ: RiskLevel.TRIVIAL,
    SideEffect.MEMORY_WRITE: RiskLevel.LOW,
    SideEffect.FILESYSTEM_WRITE: RiskLevel.MEDIUM,
    SideEffect.SHELL_EXECUTION: RiskLevel.HIGH,
    SideEffect.NETWORK_REQUEST: RiskLevel.HIGH,
    SideEffect.EXTERNAL_API_CALL: RiskLevel.HIGH,
    SideEffect.IRREVERSIBLE_ACTION: RiskLevel.HIGH,
}


# --------------------------------------------------------------------------- #
#  Validation codes & result.
# --------------------------------------------------------------------------- #
class ContractCode(str, Enum):
    OK = "ok"
    UNKNOWN_TOOL = "unknown_tool"
    NO_CONTRACT = "no_contract"
    MISSING_REQUIRED_ARG = "missing_required_arg"
    WRONG_ARG_TYPE = "wrong_arg_type"
    UNEXPECTED_ARG = "unexpected_arg"
    OVERSIZED_ARG = "oversized_arg"
    INVALID_ENUM_VALUE = "invalid_enum_value"
    NULL_NOT_ALLOWED = "null_not_allowed"
    OUTPUT_NOT_ENVELOPE = "output_not_envelope"
    OUTPUT_WRONG_TYPE = "output_wrong_type"
    MISSING_OUTPUT_ARTIFACT = "missing_output_artifact"
    OUTPUT_ARTIFACT_WRONG_TYPE = "output_artifact_wrong_type"


@dataclass
class ContractValidationResult:
    ok: bool
    code: str = ContractCode.OK.value
    message: str = ""
    arg: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def good() -> "ContractValidationResult":
        return ContractValidationResult(True)

    @staticmethod
    def bad(code: ContractCode, message: str, arg: str = "",
            details: Optional[dict] = None) -> "ContractValidationResult":
        return ContractValidationResult(False, code.value, message, arg,
                                        details or {})


# --------------------------------------------------------------------------- #
#  Arg & output specs.
# --------------------------------------------------------------------------- #
# Supported scalar/collection type tokens.
_SCALAR = {"str", "int", "float", "number", "bool", "list", "dict", "list[str]"}

DEFAULT_MAX_STR_LEN = 100_000
DEFAULT_MAX_ITEMS = 10_000
DEFAULT_MAX_KEYS = 2_000


@dataclass
class ArgSpec:
    type: str
    required: bool = True
    nullable: bool = False
    enum: Optional[list[Any]] = None
    max_length: Optional[int] = None     # str length
    max_items: Optional[int] = None      # list length
    max_keys: Optional[int] = None       # dict keys

    def __post_init__(self) -> None:
        if self.type not in _SCALAR:
            raise ValueError(f"unsupported arg type '{self.type}'")


@dataclass
class OutputContract:
    # artifact key -> required type token; only enforced when obs.success is True.
    required_artifacts: dict[str, str] = field(default_factory=dict)


@dataclass
class ToolContract:
    name: str
    description: str
    input_schema: dict[str, ArgSpec]
    side_effect_profile: frozenset[SideEffect]
    output_schema: OutputContract = field(default_factory=OutputContract)

    def risk_floor(self) -> RiskLevel:
        floor = RiskLevel.TRIVIAL
        order = {RiskLevel.TRIVIAL: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2,
                 RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        for se in self.side_effect_profile:
            r = SIDE_EFFECT_RISK.get(se, RiskLevel.TRIVIAL)
            if order[r] > order[floor]:
                floor = r
        return floor


def _type_ok(value: Any, type_token: str) -> bool:
    if type_token == "str":
        return isinstance(value, str)
    if type_token == "bool":
        return isinstance(value, bool)
    if type_token == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_token in ("float", "number"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_token == "list":
        return isinstance(value, list)
    if type_token == "dict":
        return isinstance(value, dict)
    if type_token == "list[str]":
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    return False


# --------------------------------------------------------------------------- #
#  Validators.
# --------------------------------------------------------------------------- #
class ToolInputValidator:
    """Validate command args against a contract before anything executes."""

    def __init__(self, universal_optional: Optional[dict[str, ArgSpec]] = None,
                 max_str_len: int = DEFAULT_MAX_STR_LEN,
                 max_items: int = DEFAULT_MAX_ITEMS,
                 max_keys: int = DEFAULT_MAX_KEYS) -> None:
        # Governance control args the policy engine reads on any command.
        self.universal_optional = universal_optional or {
            "touches_secrets": ArgSpec("bool", required=False),
            "irreversible": ArgSpec("bool", required=False),
        }
        self.max_str_len = max_str_len
        self.max_items = max_items
        self.max_keys = max_keys

    def validate(self, contract: ToolContract,
                 args: dict[str, Any]) -> ContractValidationResult:
        if not isinstance(args, dict):
            return ContractValidationResult.bad(
                ContractCode.WRONG_ARG_TYPE,
                "args must be an object", arg="<args>",
                details={"got_type": type(args).__name__})

        schema = dict(contract.input_schema)
        allowed = set(schema) | set(self.universal_optional)

        # Unexpected extra args.
        for key in args:
            if key not in allowed:
                return ContractValidationResult.bad(
                    ContractCode.UNEXPECTED_ARG,
                    f"unexpected argument '{key}' for tool '{contract.name}'",
                    arg=key, details={"allowed": sorted(allowed)})

        # Missing required + per-arg checks.
        for name, spec in schema.items():
            present = name in args
            if not present:
                if spec.required:
                    return ContractValidationResult.bad(
                        ContractCode.MISSING_REQUIRED_ARG,
                        f"missing required argument '{name}'", arg=name)
                continue
            value = args[name]
            res = self._check_value(contract.name, name, spec, value)
            if not res.ok:
                return res

        # Universal optional args are type-checked when present.
        for name, spec in self.universal_optional.items():
            if name in args:
                res = self._check_value(contract.name, name, spec, args[name])
                if not res.ok:
                    return res

        return ContractValidationResult.good()

    def _check_value(self, tool: str, name: str, spec: ArgSpec,
                     value: Any) -> ContractValidationResult:
        if value is None:
            if spec.nullable:
                return ContractValidationResult.good()
            return ContractValidationResult.bad(
                ContractCode.NULL_NOT_ALLOWED,
                f"argument '{name}' may not be null", arg=name)

        if not _type_ok(value, spec.type):
            return ContractValidationResult.bad(
                ContractCode.WRONG_ARG_TYPE,
                f"argument '{name}' must be {spec.type}", arg=name,
                details={"expected": spec.type, "got_type": type(value).__name__})

        if spec.enum is not None and value not in spec.enum:
            return ContractValidationResult.bad(
                ContractCode.INVALID_ENUM_VALUE,
                f"argument '{name}' must be one of {spec.enum}", arg=name,
                details={"allowed": spec.enum, "got": value})

        # Size limits.
        if isinstance(value, str):
            limit = spec.max_length or self.max_str_len
            if len(value) > limit:
                return ContractValidationResult.bad(
                    ContractCode.OVERSIZED_ARG,
                    f"argument '{name}' string length {len(value)} exceeds {limit}",
                    arg=name, details={"len": len(value), "limit": limit})
        elif isinstance(value, list):
            limit = spec.max_items or self.max_items
            if len(value) > limit:
                return ContractValidationResult.bad(
                    ContractCode.OVERSIZED_ARG,
                    f"argument '{name}' list length {len(value)} exceeds {limit}",
                    arg=name, details={"len": len(value), "limit": limit})
            # Each string element is also bounded.
            for el in value:
                if isinstance(el, str) and len(el) > self.max_str_len:
                    return ContractValidationResult.bad(
                        ContractCode.OVERSIZED_ARG,
                        f"argument '{name}' has an oversized element", arg=name,
                        details={"limit": self.max_str_len})
        elif isinstance(value, dict):
            limit = spec.max_keys or self.max_keys
            if len(value) > limit:
                return ContractValidationResult.bad(
                    ContractCode.OVERSIZED_ARG,
                    f"argument '{name}' dict has {len(value)} keys, exceeds {limit}",
                    arg=name, details={"keys": len(value), "limit": limit})

        return ContractValidationResult.good()


class ToolOutputValidator:
    """Validate a tool's observation after execution, before verifier success."""

    def validate(self, contract: ToolContract,
                 obs: ObservationEnvelope) -> ContractValidationResult:
        if not isinstance(obs, ObservationEnvelope):
            return ContractValidationResult.bad(
                ContractCode.OUTPUT_NOT_ENVELOPE,
                "tool did not return an ObservationEnvelope")

        if not isinstance(obs.success, bool):
            return ContractValidationResult.bad(
                ContractCode.OUTPUT_WRONG_TYPE,
                "observation.success must be a bool", arg="success")
        if not isinstance(obs.stdout, str):
            return ContractValidationResult.bad(
                ContractCode.OUTPUT_WRONG_TYPE,
                "observation.stdout must be a str", arg="stdout")
        if not isinstance(obs.stderr, str):
            return ContractValidationResult.bad(
                ContractCode.OUTPUT_WRONG_TYPE,
                "observation.stderr must be a str", arg="stderr")
        if not isinstance(obs.artifacts, dict):
            return ContractValidationResult.bad(
                ContractCode.OUTPUT_WRONG_TYPE,
                "observation.artifacts must be a dict", arg="artifacts")

        # Success-path artifacts are only required when the tool claims success.
        if obs.success:
            for key, type_token in contract.output_schema.required_artifacts.items():
                if key not in obs.artifacts:
                    return ContractValidationResult.bad(
                        ContractCode.MISSING_OUTPUT_ARTIFACT,
                        f"successful '{contract.name}' must produce artifact '{key}'",
                        arg=key)
                if not _type_ok(obs.artifacts[key], type_token):
                    return ContractValidationResult.bad(
                        ContractCode.OUTPUT_ARTIFACT_WRONG_TYPE,
                        f"artifact '{key}' must be {type_token}", arg=key,
                        details={"expected": type_token,
                                 "got_type": type(obs.artifacts[key]).__name__})

        return ContractValidationResult.good()


# --------------------------------------------------------------------------- #
#  Registry.
# --------------------------------------------------------------------------- #
class ToolContractRegistry:
    def __init__(self) -> None:
        self._contracts: dict[str, ToolContract] = {}

    def register(self, contract: ToolContract) -> None:
        self._contracts[contract.name] = contract

    def get(self, name: str) -> Optional[ToolContract]:
        return self._contracts.get(name)

    def has(self, name: str) -> bool:
        return name in self._contracts

    @property
    def names(self) -> set[str]:
        return set(self._contracts)

    def side_effects(self, name: str) -> frozenset[SideEffect]:
        c = self._contracts.get(name)
        return c.side_effect_profile if c else frozenset()

    def resolve_for_execution(
        self, name: str, registered_tools: set[str]
    ) -> tuple[Optional[ToolContract], ContractValidationResult]:
        """Gate 0: a tool may only execute with a registered, contracted name."""
        if name not in registered_tools:
            return None, ContractValidationResult.bad(
                ContractCode.UNKNOWN_TOOL,
                f"tool '{name}' is not a registered tool")
        contract = self._contracts.get(name)
        if contract is None:
            return None, ContractValidationResult.bad(
                ContractCode.NO_CONTRACT,
                f"tool '{name}' has no registered contract; execution denied")
        return contract, ContractValidationResult.good()


def default_contract_registry() -> ToolContractRegistry:
    """Contracts for the builtin tools (mirror of tools.ToolRuntime builtins)."""
    reg = ToolContractRegistry()

    reg.register(ToolContract(
        name="read_file",
        description="Read a file in the workspace",
        input_schema={"path": ArgSpec("str"),
                      "max_bytes": ArgSpec("int", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_READ}),
        output_schema=OutputContract(required_artifacts={
            "path": "str", "content": "str", "truncated": "bool"}),
    ))
    reg.register(ToolContract(
        name="write_file",
        description="Write/overwrite a file",
        input_schema={"path": ArgSpec("str"), "content": ArgSpec("str"),
                      "create_dirs": ArgSpec("bool", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_WRITE}),
        output_schema=OutputContract(required_artifacts={
            "path": "str", "bytes_written": "int", "changed": "bool"}),
    ))
    reg.register(ToolContract(
        name="edit_file",
        description="Find/replace a single occurrence",
        input_schema={"path": ArgSpec("str"), "find": ArgSpec("str"),
                      "replace": ArgSpec("str")},
        side_effect_profile=frozenset(
            {SideEffect.FILESYSTEM_READ, SideEffect.FILESYSTEM_WRITE}),
        output_schema=OutputContract(required_artifacts={"path": "str"}),
    ))
    reg.register(ToolContract(
        name="list_dir",
        description="List a directory",
        input_schema={"path": ArgSpec("str", required=False),
                      "recursive": ArgSpec("bool", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_READ}),
        output_schema=OutputContract(required_artifacts={
            "entries": "list", "root": "str"}),
    ))
    reg.register(ToolContract(
        name="search_text",
        description="Search text under a workspace root",
        input_schema={"root": ArgSpec("str"), "query": ArgSpec("str"),
                      "glob": ArgSpec("str", required=False),
                      "max_results": ArgSpec("int", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_READ}),
        output_schema=OutputContract(required_artifacts={"matches": "list"}),
    ))
    reg.register(ToolContract(
        name="git_status",
        description="Read git status",
        input_schema={"repo_path": ArgSpec("str", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_READ}),
        output_schema=OutputContract(required_artifacts={
            "status_text": "str", "clean": "bool"}),
    ))
    reg.register(ToolContract(
        name="git_diff",
        description="Read git diff",
        input_schema={"repo_path": ArgSpec("str", required=False),
                      "staged": ArgSpec("bool", required=False)},
        side_effect_profile=frozenset({SideEffect.FILESYSTEM_READ}),
        output_schema=OutputContract(required_artifacts={
            "diff_text": "str", "truncated": "bool"}),
    ))
    reg.register(ToolContract(
        name="run_tests",
        description="Run a python test file",
        input_schema={"test_file": ArgSpec("str", required=False),
                      "command": ArgSpec("list[str]", required=False),
                      "timeout": ArgSpec("number", required=False),
                      "timeout_seconds": ArgSpec("int", required=False),
                      "allowed_app_paths": ArgSpec("list[str]", required=False)},
        side_effect_profile=frozenset(
            {SideEffect.FILESYSTEM_READ, SideEffect.FILESYSTEM_WRITE}),
        output_schema=OutputContract(required_artifacts={
            "exit_code": "int", "duration_ms": "int"}),
    ))
    reg.register(ToolContract(
        name="run_python",
        description="Run python inside the sandbox",
        input_schema={"args": ArgSpec("list[str]"),
                      "timeout_seconds": ArgSpec("int", required=False)},
        side_effect_profile=frozenset(
            {SideEffect.SHELL_EXECUTION, SideEffect.FILESYSTEM_READ,
             SideEffect.FILESYSTEM_WRITE}),
        output_schema=OutputContract(required_artifacts={
            "exit_code": "int", "duration_ms": "int"}),
    ))
    reg.register(ToolContract(
        name="run_shell",
        description="Run an arbitrary command (HIGH risk)",
        input_schema={"cmd": ArgSpec("list[str]", required=False),
                      "command": ArgSpec("str", required=False),
                      "timeout": ArgSpec("number", required=False),
                      "timeout_seconds": ArgSpec("int", required=False)},
        side_effect_profile=frozenset(
            {SideEffect.SHELL_EXECUTION, SideEffect.FILESYSTEM_READ,
             SideEffect.FILESYSTEM_WRITE}),
        output_schema=OutputContract(required_artifacts={
            "exit_code": "int", "duration_ms": "int"}),
    ))
    reg.register(ToolContract(
        name="patch_file",
        description="Apply a small unified diff to a file",
        input_schema={"path": ArgSpec("str"),
                      "patch": ArgSpec("str", required=False),
                      "unified_diff": ArgSpec("str", required=False)},
        side_effect_profile=frozenset(
            {SideEffect.FILESYSTEM_READ, SideEffect.FILESYSTEM_WRITE}),
        output_schema=OutputContract(required_artifacts={
            "path": "str", "applied": "bool", "summary": "str"}),
    ))
    reg.register(ToolContract(
        name="delete_file",
        description="Delete a file in the workspace",
        input_schema={"path": ArgSpec("str")},
        side_effect_profile=frozenset(
            {SideEffect.FILESYSTEM_WRITE, SideEffect.IRREVERSIBLE_ACTION}),
        output_schema=OutputContract(required_artifacts={
            "path": "str", "deleted": "bool"}),
    ))
    reg.register(ToolContract(
        name="network_fetch",
        description="Fetch a URL over HTTP(S)",
        input_schema={"url": ArgSpec("str"),
                      "timeout": ArgSpec("number", required=False),
                      "timeout_seconds": ArgSpec("int", required=False),
                      "max_bytes": ArgSpec("int", required=False)},
        side_effect_profile=frozenset({SideEffect.NETWORK_REQUEST}),
        output_schema=OutputContract(required_artifacts={
            "url": "str", "status": "int", "bytes": "int", "content_hash": "str"}),
    ))
    reg.register(ToolContract(
        name="mutate_protected_verification",
        description="Approved mutation of a protected verification file (HIGH risk)",
        input_schema={"path": ArgSpec("str"), "content": ArgSpec("str"),
                      "approved": ArgSpec("bool")},
        side_effect_profile=frozenset(
            {SideEffect.FILESYSTEM_WRITE, SideEffect.IRREVERSIBLE_ACTION}),
        output_schema=OutputContract(required_artifacts={"path": "str"}),
    ))
    return reg
