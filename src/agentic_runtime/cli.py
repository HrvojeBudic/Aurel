"""
cli.py — Minimal CLI entrypoint (P0.11).

  python -m agentic_runtime.cli status
  python -m agentic_runtime.cli demo
  python -m agentic_runtime.cli verify
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess  # nosec B404 - CLI verify intentionally spawns local pytest as a direct argv command
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_status(args: argparse.Namespace) -> int:
    from . import build_runtime
    from .governance.enforcement_profiles import profile_spec
    from .governance.profile import profile_for
    from .status import format_status, runtime_status

    try:
        spec = profile_spec()
        gprofile = profile_for(spec.level)
        active_profile = {
            "name": spec.name,
            "level": spec.level.value,
            "enforcement_mode": gprofile.enforcement_mode.value,
        }
    except Exception as exc:  # never let a config issue hide the rest of status
        active_profile = {"name": "unavailable", "error": str(exc)}

    kernel = build_runtime()
    status = runtime_status(kernel)
    status["active_profile"] = active_profile
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        ap = active_profile
        if "error" in ap:
            print(f"active profile: unavailable ({ap['error']})")
        else:
            print(f"active profile: {ap['name']}  level={ap['level']}  "
                  f"enforcement={ap['enforcement_mode']}")
        print(format_status(status))
    return 0


def cmd_demo(_args: argparse.Namespace) -> int:
    from .demo import main
    main()
    return 0

_NESTED_VERIFY_DRIFT_TESTS = (
    "tests/test_prompt_system_p12.py",
    "tests/test_model_config_p11.py",
    "tests/test_repo_planner_p021.py",
    "tests/test_demo_harness_p19.py",
    "tests/test_policy_exit_seal_p1620.py",
    "tests/test_policy_exit_seal_projection_p1620.py",
    "tests/test_policy_exit_seal_cli_p1620.py",
)


def cmd_verify(args: argparse.Namespace) -> int:
    root = _repo_root()
    env = {**os.environ, "PYTHONPATH": f"src{os.pathsep}."}
    # -p no:cacheprovider makes the run cache-independent: it neither reads a
    # warm .pytest_cache (which can mask cold-cache-only failures) nor writes a
    # stale one. Cold and warm invocations therefore always agree.
    verbosity = "-v" if args.verbose else "-q"
    nested_smoke = env.get("AGENTIC_SKIP_RECURSIVE_SMOKE") == "1"
    cmd = [sys.executable, "-m", "pytest", verbosity]
    if nested_smoke:
        # Smoke tests invoke `cli verify` from inside pytest. In that nested path
        # we favor a fast drift check over a second cold-cache full-tree run.
        cmd.extend(_NESTED_VERIFY_DRIFT_TESTS)
    else:
        cmd.extend(["-p", "no:cacheprovider"])
    print(f"running: {' '.join(cmd)}  (cwd={root})")
    proc = subprocess.run(cmd, cwd=root, env=env)  # nosec B603 - direct argv pytest invocation, no shell expansion
    return proc.returncode


_SANDBOX_CHOICES = [
    "no_exec_readonly", "restricted_local", "unsafe_local_demo",
    "bubblewrap", "docker",
]


def _resolve_cli_sandbox(args: argparse.Namespace, *, apply: bool) -> tuple[str, list[str]]:
    from .sandbox_policy import resolve_apply_sandbox_profile

    if args.sandbox is not None:
        return args.sandbox, []
    if apply:
        return resolve_apply_sandbox_profile()
    return "restricted_local", []


def cmd_repo_task(args: argparse.Namespace) -> int:
    from .repo_agent import RepositoryAgentLoop, RepoTaskRequest

    test_command = shlex.split(args.test_command) if args.test_command else ["python3", "-m", "pytest", "-q"]
    apply = args.apply and not args.dry_run
    sandbox_profile, sandbox_warnings = _resolve_cli_sandbox(args, apply=apply)
    request = RepoTaskRequest.make(
        args.objective,
        repo_path=args.repo,
        allowed_paths=args.allowed_path or ["*"],
        disallowed_paths=args.disallowed_path or [],
        max_files_changed=args.max_files_changed,
        max_repair_iterations=args.max_repair_iterations,
        test_command=test_command,
        require_approval_before_write=not args.apply,
        approval_mode=args.approval_mode,
        sandbox_profile=sandbox_profile,
        planner_mode=args.planner,
        model_provider=args.provider,
    )
    report = RepositoryAgentLoop().run(request, apply=apply, dry_run=args.dry_run)
    payload = report.to_dict()
    if sandbox_warnings:
        payload["sandbox_warnings"] = sandbox_warnings
    print(json.dumps(payload, indent=2))
    return 0 if report.final_status in {"planned", "dry_run", "succeeded"} else 1


def cmd_approve_demo(args: argparse.Namespace) -> int:
    from . import AgentCard, AgentClass, AuthorityScope, build_runtime
    from .approval import ApprovalRiskClass
    from .core_types import CommandEnvelope, RiskLevel
    from .hitl import AutoApprover, DenyAllApprover
    from .sandbox import UnsafeLocalSandbox

    kernel = build_runtime(
        sandbox=UnsafeLocalSandbox(root=args.repo),
        approval_gate=DenyAllApprover() if args.mode == "deny" else AutoApprover(
            lambda r: r.risk_class in {ApprovalRiskClass.R0, ApprovalRiskClass.R1},
            allow_r2=args.allow_writes,
        ),
    )
    card = AgentCard.make(
        name="Approval Demo",
        agent_class=AgentClass.EXECUTION,
        mission="approval demo",
        authority=AuthorityScope(write_paths=["*"], read_paths=["*"], max_risk=RiskLevel.HIGH),
        allowed_tools=["read_file", "write_file", "run_shell"],
    )
    scenarios = [
        ("read_file", {"path": "demo.txt"}, "R0 read"),
        ("write_file", {"path": "demo.txt", "content": "hello"}, "R2 write"),
        ("run_shell", {"cmd": ["echo", "hi"]}, "R4 shell"),
    ]
    kernel.sandbox.write_file("demo.txt", "seed\n")
    rows = []
    for tool, tool_args, label in scenarios:
        res = kernel.runtime.submit(
            CommandEnvelope.make(
                issuer_card_id=card.id,
                tool=tool,
                args=tool_args,
                rationale=label,
                declared_risk=RiskLevel.LOW,
                expected_effect=label,
            ),
            card,
        )
        rows.append({
            "scenario": label,
            "tool": tool,
            "executed": res.ok,
            "approval": res.approval_receipt.to_dict() if res.approval_receipt else None,
            "verifier": res.verifier.code,
        })
    print(json.dumps(rows, indent=2))
    return 0


def cmd_sandbox_status(args: argparse.Namespace) -> int:
    from . import build_runtime
    from .status import runtime_status

    kernel = build_runtime(
        sandbox_profile=args.profile,
        workspace_root=args.root,
    )
    status = runtime_status(kernel)
    if args.json:
        print(json.dumps(status.get("sandbox", {}), indent=2))
    else:
        sb = status["sandbox"]
        print(f"profile: {sb.get('profile', '')}")
        print(f"backend: {sb.get('backend', '')} ({sb.get('mode', '')})")
        print(f"unsafe: {sb.get('unsafe', False)}")
        print(f"policy_restricted: {sb.get('policy_restricted', False)}")
        print(f"hard_isolated: {sb.get('hard_isolated', False)}")
        print(f"security_boundary: {sb.get('security_boundary', False)}")
        print(f"read={sb.get('read_allowed')} write={sb.get('write_allowed')} exec={sb.get('exec_allowed')}")
        print(f"network_allowed={sb.get('network_allowed')} secrets_allowed={sb.get('secrets_allowed')}")
        for lim in sb.get("limitations", []):
            print(f"  limitation: {lim}")
    return 0


_PRAXIS_CLI: object | None = None


def _praxis_metabolism():
    global _PRAXIS_CLI
    if _PRAXIS_CLI is None:
        from .praxis import PraxisMetabolism
        _PRAXIS_CLI = PraxisMetabolism()
    return _PRAXIS_CLI


def cmd_praxis_demo(_args: argparse.Namespace) -> int:
    from . import build_runtime
    from .core_types import AgentCard, AgentClass, AuthorityScope, CommandEnvelope, RiskLevel
    from .hitl import AutoApprover
    from .praxis import PraxisExperienceBuilder
    from .sandbox import UnsafeLocalSandbox

    kernel = build_runtime(sandbox=UnsafeLocalSandbox(root="."), approval_gate=AutoApprover())
    card = AgentCard.make(
        name="Praxis Demo",
        agent_class=AgentClass.EXECUTION,
        mission="praxis demo",
        authority=AuthorityScope(write_paths=["demo_praxis.txt"], read_paths=["*"], max_risk=RiskLevel.MEDIUM),
        allowed_tools=["write_file", "read_file"],
    )
    kernel.sandbox.write_file("demo_praxis.txt", "seed\n")
    cmd = CommandEnvelope.make(
        issuer_card_id=card.id,
        tool="write_file",
        args={"path": "demo_praxis.txt", "content": "praxis demo\n"},
        rationale="praxis demo write",
        declared_risk=RiskLevel.LOW,
        expected_effect="demo file update",
    )
    result = kernel.runtime.submit(cmd, card)
    exp = PraxisExperienceBuilder.from_command_result(
        trace_id=kernel.trace.run_id,
        run_id=kernel.trace.run_id,
        objective="praxis demo",
        action_summary="write_file demo_praxis.txt",
        result=result,
        tools_used=["write_file"],
        command_id=cmd.id,
    )
    metabolism = _praxis_metabolism()
    report = metabolism.process_experience(exp, trace=kernel.trace, run_id=kernel.trace.run_id)
    print(json.dumps({
        "experience": exp.outcome_status.value,
        "memory_candidates": report.memory_candidates_created,
        "limitations": report.limitations,
    }, indent=2))
    return 0


def cmd_memory_candidates(_args: argparse.Namespace) -> int:
    metabolism = _praxis_metabolism()
    rows = [
        {
            "candidate_id": c.candidate_id,
            "type": c.candidate_type.value,
            "trust": c.trust_level.value,
            "summary": c.content_summary[:120],
        }
        for c in metabolism.memory_candidates
    ]
    print(json.dumps(rows, indent=2))
    return 0


def cmd_praxis_report(_args: argparse.Namespace) -> int:
    metabolism = _praxis_metabolism()
    if not metabolism.reports:
        print(json.dumps({"message": "no praxis reports yet; run praxis-demo or repo-task"}, indent=2))
        return 0
    last = metabolism.reports[-1]
    print(json.dumps({
        "experience_id": last.experience_id,
        "memory_candidates_created": last.memory_candidates_created,
        "procedure_candidates_created": last.procedure_candidates_created,
        "skill_candidates_created": last.skill_candidates_created,
        "promotion_decisions": last.promotion_decisions,
        "reflex_eligibility_checks": last.reflex_eligibility_checks,
        "limitations": last.limitations,
    }, indent=2))
    return 0


def cmd_demo_harness(args: argparse.Namespace) -> int:
    from .demo_harness import (
        DemoHarness, DemoHarnessRequest, get_scenario, list_scenarios, write_evidence,
    )

    if args.scenario == "list":
        rows = [
            {"scenario_id": s.scenario_id, "name": s.name, "description": s.description}
            for s in list_scenarios()
        ]
        print(json.dumps(rows, indent=2))
        return 0

    scenario = get_scenario(args.scenario)
    apply = args.apply and not args.dry_run
    sandbox_profile, sandbox_warnings = _resolve_cli_sandbox(args, apply=apply)
    report = DemoHarness().run(DemoHarnessRequest(
        scenario_id=scenario.scenario_id,
        repo_parent=args.repo_parent,
        apply=args.apply,
        dry_run=args.dry_run,
        approval_mode=args.approval_mode,
        sandbox_profile=sandbox_profile,
        planner_mode=args.planner,
        model_provider=args.provider or None,
    ))
    evidence_written: list[str] = []
    if args.evidence_dir:
        evidence_written = write_evidence(args.evidence_dir, report, scenario)
    payload = {
        "scenario": report.scenario_id,
        "repo_path": report.repo_path,
        "initial_test": {
            "passed": report.initial_test_result.passed,
            "exit_code": report.initial_test_result.exit_code,
        },
        "plan_summary": report.agent_plan_summary,
        "files_inspected": report.files_inspected,
        "files_changed": report.files_changed,
        "final_test": None if report.final_test_result is None else {
            "passed": report.final_test_result.passed,
            "exit_code": report.final_test_result.exit_code,
        },
        "approval_summary": report.approval_summary,
        "sandbox_profile": report.sandbox_profile,
        "planner_mode": report.planner_mode,
        "model_provider": report.model_provider,
        "fallback_reason": report.fallback_reason,
        "sandbox_violations": report.sandbox_violations,
        "praxis_summary": report.praxis_summary,
        "trace_summary": report.trace_summary,
        "plan_verification": report.plan_verification,
        "final_status": report.final_status,
        "limitations": report.limitations,
    }
    if args.evidence_dir:
        payload["evidence_dir"] = args.evidence_dir
        payload["evidence_files"] = evidence_written
    if sandbox_warnings:
        payload["sandbox_warnings"] = sandbox_warnings
    print(json.dumps(payload, indent=2))
    return 0 if report.final_status in {"succeeded", "planned", "dry_run"} else 1


def cmd_alpha_seal(args: argparse.Namespace) -> int:
    from .alpha_seal import format_alpha_seal, run_alpha_seal

    report = run_alpha_seal(
        run_tests=not args.skip_tests,
        skip_coverage=args.skip_coverage,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_alpha_seal(report))
    return 0 if report.passed else 1


from .cli_modules.common import config_dir as _config_dir
from .cli_modules.identity_commands import (
    cmd_identity_card_attest,
    cmd_identity_card_hash,
    cmd_identity_card_show,
    cmd_identity_card_taxonomy,
    cmd_identity_card_validate,
    cmd_identity_context_attest,
    cmd_identity_context_compile,
    cmd_identity_context_hash,
    cmd_identity_context_render,
    cmd_identity_context_validate,
    cmd_identity_kernel_attest,
    cmd_identity_kernel_hash,
    cmd_identity_kernel_show,
    cmd_identity_kernel_validate,
    cmd_identity_modes_attest,
    cmd_identity_modes_hash,
    cmd_identity_modes_list,
    cmd_identity_modes_show,
    cmd_identity_modes_summary,
    cmd_identity_modes_validate,
    cmd_identity_operator_contract_attest,
    cmd_identity_operator_contract_hash,
    cmd_identity_operator_contract_show,
    cmd_identity_operator_contract_summary,
    cmd_identity_operator_contract_validate,
    cmd_identity_persona_attest,
    cmd_identity_persona_hash,
    cmd_identity_persona_show,
    cmd_identity_persona_summary,
    cmd_identity_persona_validate,
    cmd_identity_self_attest,
    cmd_identity_self_capabilities,
    cmd_identity_self_hash,
    cmd_identity_self_limitations,
    cmd_identity_self_show,
    cmd_identity_self_validate,
    cmd_identity_autonomy_evaluate,
    cmd_identity_autonomy_measure,
    cmd_identity_claims_evaluate,
    cmd_identity_claims_list,
    cmd_identity_claims_show,
    cmd_identity_claims_validate,
    cmd_identity_claims_rewrite,
    cmd_identity_doctrine_claims,
    cmd_identity_doctrine_impact,
    cmd_identity_doctrine_list,
    cmd_identity_doctrine_show,
    cmd_identity_doctrine_validate,
    cmd_identity_attestation_compare,
    cmd_identity_attestation_list,
    cmd_identity_attestation_show,
    cmd_identity_attestation_validate,
    cmd_identity_attestation_verify_bundle,
    cmd_identity_authority_delta_compare,
    cmd_identity_consent_request,
    cmd_identity_consent_grant,
    cmd_identity_consent_deny,
    cmd_identity_consent_revoke,
    cmd_identity_consent_show,
    cmd_identity_consent_validate,
    cmd_identity_status,
    cmd_identity_verify,
    cmd_identity_test_battery_run,
    cmd_identity_test_battery_list,
    cmd_identity_test_battery_run_case,
    cmd_identity_lifecycle_show,
    cmd_identity_lifecycle_profile,
    cmd_identity_lifecycle_validate_transition,
    cmd_identity_lifecycle_transitions,
    cmd_identity_lifecycle_recommend,
    cmd_identity_trust_evidence_requirements,
    cmd_identity_trust_evidence_build,
    cmd_identity_trust_evidence_validate,
    cmd_identity_trust_evidence_explain,
    cmd_identity_seal_readiness,
    cmd_identity_p14_seal_run,
    cmd_identity_p14_seal_list_checks,
    cmd_identity_p14_seal_run_check,
)
from .cli_modules.exec_commands import (
    cmd_exec_status,
)
from .cli_modules.trace_commands import (
    cmd_trace_anchor_verify,
    cmd_trace_audit,
    cmd_trace_inspect,
    cmd_trace_status,
    cmd_trace_verify,
)
from .cli_modules.evaluation_commands import (
    cmd_evaluation_foundation_scope,
    cmd_evaluation_foundation_status,
    cmd_evaluation_objects_examples,
    cmd_evaluation_objects_status,
    cmd_evaluation_capability_evidence_examples,
    cmd_evaluation_capability_evidence_status,
    cmd_evaluation_subjects_examples,
    cmd_evaluation_subjects_status,
    cmd_evaluation_criteria_examples,
    cmd_evaluation_criteria_status,
    cmd_evaluation_runs_examples,
    cmd_evaluation_runs_status,
    cmd_evaluation_classify_examples,
    cmd_evaluation_classify_status,
    cmd_evaluation_binding_examples,
    cmd_evaluation_binding_status,
    cmd_evaluation_hygiene_examples,
    cmd_evaluation_hygiene_status,
    cmd_evaluation_adversarial_examples,
    cmd_evaluation_adversarial_status,
    cmd_evaluation_baseline_examples,
    cmd_evaluation_baseline_status,
)
from .cli_modules.policy_commands import (
    cmd_policy_harness_list,
    cmd_policy_harness_run,
    cmd_policy_projection,
    cmd_policy_status,
    cmd_policy_unavailable,
)
from .cli_modules.shell_commands import (
    cmd_shell_clients,
    cmd_shell_evidence,
    cmd_shell_export_json,
    cmd_shell_parity,
    cmd_shell_read_model,
    cmd_shell_run_modes,
    cmd_shell_run_view,
    cmd_shell_status,
    cmd_shell_surfaces,
)
from .cli_modules.spine_commands import cmd_spine_replay, cmd_spine_run, cmd_spine_serve
from .cli_modules.doctor import cmd_doctor
from .cli_modules.governance_commands import (cmd_governance_audit, cmd_governance_levels,
                                              cmd_profile_audit, cmd_profile_show)
from .cli_modules.drill_commands import cmd_drill_model_swap
from .cli_modules.secrets_commands import cmd_secrets_set, cmd_secrets_status
from .cli_modules.gate_commands import cmd_gate_check
from .cli_modules.f3_commands import cmd_f3_seal, cmd_f3_surface
from .cli_modules.f4_commands import cmd_f4_loom, cmd_f4_seal
from .cli_modules.f5_commands import cmd_front_serve
from .cli_modules.mcp_client_commands import (cmd_mcp_client_demo,
                                              cmd_mcp_client_list_servers,
                                              cmd_mcp_client_seal)
from .cli_modules.dual_kernel_commands import (
    cmd_dual_kernel_bindings,
    cmd_dual_kernel_show,
    cmd_dual_kernel_status,
    cmd_dual_kernel_verify_ledger,
)
from .cli_modules.memory_commands import (
    cmd_memory_explore,
    cmd_memory_graph,
    cmd_memory_history,
    cmd_memory_rejected,
)
from .cli_modules.reasoning_commands import (
    cmd_reasoning_status,
    cmd_reasoning_workload,
)
from .cli_modules.shell_permission_commands import (
    cmd_shell_permissions_actions,
    cmd_shell_permissions_clients,
    cmd_shell_permissions_evidence,
    cmd_shell_permissions_export,
    cmd_shell_permissions_sensitive,
    cmd_shell_permissions_show,
    cmd_shell_permissions_summary,
    cmd_shell_permissions_surfaces,
)
from .cli_modules.path_governance import (
    cmd_path_governance_api_envelope,
    cmd_path_governance_capabilities,
    cmd_path_governance_events,
    cmd_path_governance_harness_summary,
    cmd_path_governance_policy_context_summary,
    cmd_path_governance_read_model,
    cmd_path_governance_status,
    cmd_path_governance_trace_hook_summary,
    cmd_path_governance_unavailable,
    cmd_path_governance_violation_drift_summary,
)
from .cli_modules.output_passport import (
    cmd_output_passport_inspect,
    cmd_output_passport_projection,
    cmd_output_passport_unavailable,
)

def cmd_config_validate(args: argparse.Namespace) -> int:
    from .model_config import ModelConfigError, ProviderConfigLoader

    try:
        bundle = ProviderConfigLoader(_config_dir(args)).load()
        payload = {
            "valid": True,
            "config_dir": str(_config_dir(args)),
            "providers": sorted(bundle.providers.keys()),
            "profiles": sorted(bundle.profiles.keys()),
            "local_only": bundle.runtime.local_only,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("config: valid")
            print(f"  dir: {payload['config_dir']}")
            print(f"  providers: {', '.join(payload['providers'])}")
            print(f"  profiles: {', '.join(payload['profiles'])}")
            print(f"  local_only: {payload['local_only']}")
        return 0
    except (ModelConfigError, Exception) as e:
        payload = {"valid": False, "error": str(e), "config_dir": str(_config_dir(args))}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"config: invalid — {e}")
        return 1


def cmd_models_list(args: argparse.Namespace) -> int:
    from .model_config import ProviderConfigLoader

    bundle = ProviderConfigLoader(_config_dir(args)).load()
    rows = []
    for name in sorted(bundle.profiles.keys()):
        profile = bundle.profiles[name]
        provider = bundle.providers.get(profile.provider)
        residency = "local"
        if provider is not None:
            residency = "remote" if provider.is_remote else "local"
        rows.append({
            "name": name,
            "provider": profile.provider,
            "model": profile.model,
            "purpose": profile.purpose,
            "residency": residency,
            "allowed_tasks": profile.allowed_tasks,
        })
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(
                f"{row['name']}: provider={row['provider']} model={row['model']} "
                f"purpose={row['purpose']} residency={row['residency']}"
            )
    return 0


def cmd_providers_status(args: argparse.Namespace) -> int:
    from .model_config import ProviderConfigLoader
    from .model_router import ModelRouter
    from .secrets import SecretRedactor

    bundle = ProviderConfigLoader(_config_dir(args)).load()
    router = ModelRouter(config=bundle)
    rows = router.provider_status()
    redactor = SecretRedactor()
    for row in rows:
        for key in ("message", "secret_status"):
            if key in row and isinstance(row[key], str):
                row[key] = redactor.redact(row[key])
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(
                f"{row['provider']}: type={row.get('type', '')} "
                f"residency={row.get('residency', '')} "
                f"enabled={row.get('enabled', '')} "
                f"secret={row.get('secret_status', '')} "
                f"status={row.get('status', '')}"
            )
            if row.get("message"):
                print(f"  message: {row['message']}")
    return 0


def _prompts_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "prompts_dir", None):
        return Path(args.prompts_dir)
    return _repo_root() / "prompts"


def _prompt_registry(args: argparse.Namespace, *, validate_profiles: bool = True):
    from .model_config import ProviderConfigLoader
    from .prompt_system import PromptRegistry

    bundle = ProviderConfigLoader(_config_dir(args)).load() if validate_profiles else None
    return PromptRegistry(
        _prompts_dir(args),
        model_config=bundle,
        validate_model_profiles=validate_profiles,
    ).load()


def _parse_prompt_vars(items: list[str] | None) -> dict[str, str]:
    variables: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"--var must be key=value: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("--var key must not be empty")
        variables[key] = value
    return variables



def cmd_prompts_validate(args: argparse.Namespace) -> int:
    from .prompt_system import PromptSystemError

    try:
        registry = _prompt_registry(args, validate_profiles=not args.skip_model_config)
        rows = registry.list_prompts()
        payload = {
            "valid": True,
            "prompts_dir": str(_prompts_dir(args)),
            "count": len(rows),
            "prompts": [p.id for p in rows],
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("prompts: valid")
            print(f"  dir: {payload['prompts_dir']}")
            print(f"  count: {payload['count']}")
        return 0
    except PromptSystemError as e:
        payload = {"valid": False, "error": str(e), "prompts_dir": str(_prompts_dir(args))}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"prompts: invalid — {e}")
        return 1


def cmd_prompts_list(args: argparse.Namespace) -> int:
    registry = _prompt_registry(args, validate_profiles=not args.skip_model_config)
    rows = [
        {
            "id": p.id,
            "version": p.version,
            "owner": p.owner,
            "purpose": p.purpose,
            "allowed_model_profiles": p.allowed_model_profiles,
            "status": p.status,
        }
        for p in registry.list_prompts()
    ]
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            profiles = ",".join(row["allowed_model_profiles"])
            print(
                f"{row['id']}@{row['version']}: owner={row['owner']} "
                f"status={row['status']} profiles={profiles} purpose={row['purpose']}"
            )
    return 0


def cmd_prompts_show(args: argparse.Namespace) -> int:
    from .prompt_system import prompt_metadata_to_safe_dict, safe_json

    registry = _prompt_registry(args, validate_profiles=not args.skip_model_config)
    metadata = registry.get(args.prompt_id).metadata
    payload = prompt_metadata_to_safe_dict(metadata)
    payload.pop("source_path", None)
    if args.json:
        print(safe_json(payload))
    else:
        print(f"id: {payload['id']}")
        print(f"version: {payload['version']}")
        print(f"owner: {payload['owner']}")
        print(f"status: {payload['status']}")
        print(f"purpose: {payload['purpose']}")
        print(f"allowed_model_profiles: {', '.join(payload['allowed_model_profiles'])}")
        print(f"allowed_tasks: {', '.join(payload['allowed_tasks'])}")
        print(f"risk_tier: {payload['risk_tier']}")
        print("policy:")
        for key, value in payload["policy"].items():
            print(f"  {key}: {value}")
        print(f"forbidden: {', '.join(payload['forbidden'])}")
    return 0


def cmd_prompts_render(args: argparse.Namespace) -> int:
    from .prompt_system import PromptSystemError

    try:
        registry = _prompt_registry(args, validate_profiles=not args.skip_model_config)
        prompt = registry.get(args.prompt_id)
        variables = _parse_prompt_vars(args.var)
        # CLI dry-run is operator-oriented, so omitted variables are explicit blanks.
        # The PromptTemplate API still fails safely when called with missing variables.
        for name in prompt.variables:
            variables.setdefault(name, "")
        result = registry.render(args.prompt_id, variables, include_raw_prompt=False)
        payload = result.trace_summary.to_dict()
        payload.pop("rendered_preview_redacted", None)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except (PromptSystemError, ValueError) as e:
        payload = {"rendered": False, "error": str(e), "prompt_id": args.prompt_id}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"prompt render failed: {e}")
        return 1


def cmd_flow(args: argparse.Namespace) -> int:
    # P3.7 read-only AurelFlow binding: every subcommand renders a projection
    # built from the DEV_FIXTURE demo substrate. Nothing executes, mutates,
    # approves, resumes, retries, recovers, or rolls back.
    from .aurel_flow.flow_cli import (
        FlowCliCommandKind,
        FlowCliOutputFormat,
        FlowCliRequest,
        handle_flow_cli_request,
        render_flow_cli_response,
    )

    request = FlowCliRequest(
        command_kind=FlowCliCommandKind(args.flow_command.upper()),
        output_format=(
            FlowCliOutputFormat.JSON
            if getattr(args, "json", False)
            else FlowCliOutputFormat.TEXT
        ),
        base_p3=getattr(args, "base_p3", True),
    )
    response = handle_flow_cli_request(request)
    print(render_flow_cli_response(response))
    return response.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentic-runtime",
        description="Governed agentic runtime — minimal CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show runtime wiring and sandbox mode")
    p_status.add_argument("--json", action="store_true", help="emit JSON")
    p_status.set_defaults(func=cmd_status)

    p_demo = sub.add_parser("demo", help="run the end-to-end governed demo")
    p_demo.set_defaults(func=cmd_demo)

    p_doctor = sub.add_parser(
        "doctor", help="host capability diagnostics (functional sandbox probes)")
    p_doctor.add_argument("--json", action="store_true", help="emit JSON")
    p_doctor.add_argument("--no-cache", action="store_true",
                          help="re-run probes, ignoring the cached results")
    p_doctor.set_defaults(func=cmd_doctor)

    p_gov = sub.add_parser("governance", help="governance scale G0–G5 (M6)")
    gov_sub = p_gov.add_subparsers(dest="governance_command", required=True)
    p_gov_levels = gov_sub.add_parser("levels", help="show the G0–G5 spectrum")
    p_gov_levels.add_argument("--json", action="store_true", help="emit JSON")
    p_gov_levels.set_defaults(func=cmd_governance_levels)
    p_gov_audit = gov_sub.add_parser(
        "audit", help="detect drift above a run's declared governance level")
    p_gov_audit.add_argument("run_id", help="run id under the trace dir")
    p_gov_audit.add_argument("--declared", default="G1",
                             help="declared level (G0..G5); default G1")
    p_gov_audit.add_argument("--trace-dir", default=".traces", help="trace base dir")
    p_gov_audit.add_argument("--checkpoint-every", type=int, default=5)
    p_gov_audit.set_defaults(func=cmd_governance_audit)

    p_profile = sub.add_parser("profile", help="enforcement profiles (F1): dev/standard/hardened")
    profile_sub = p_profile.add_subparsers(dest="profile_command", required=True)
    p_profile_show = profile_sub.add_parser("show", help="list profiles; mark the active one")
    p_profile_show.add_argument("--profile", default=None,
                                help="profile to treat as active (else AUREL_PROFILE / default)")
    p_profile_show.add_argument("--json", action="store_true", help="emit JSON")
    p_profile_show.set_defaults(func=cmd_profile_show)
    p_profile_audit = profile_sub.add_parser(
        "audit", help="audit the active profile for shadow drift (declared vs actually wired)")
    p_profile_audit.add_argument("--profile", default=None,
                                 help="profile to audit (else AUREL_PROFILE / default)")
    p_profile_audit.add_argument("--fail-on-drift", action="store_true",
                                 help="exit non-zero on config/wiring drift (a code regression)")
    p_profile_audit.add_argument("--strict", action="store_true",
                                 help="also fail on host capability gaps (e.g. no hard sandbox)")
    p_profile_audit.set_defaults(func=cmd_profile_audit)

    # F2: per-provider API-key management (SecretStore: env → keyring → file-0600).
    p_secrets = sub.add_parser("secrets", help="provider API keys (F2 SecretStore)")
    secrets_sub = p_secrets.add_subparsers(dest="secrets_command", required=True)
    p_secrets_set = secrets_sub.add_parser(
        "set", help="store a provider key (input hidden, never echoed)")
    p_secrets_set.add_argument(
        "provider", help="provider name (anthropic/deepseek/qwen/kimi/openai)")
    p_secrets_set.set_defaults(func=cmd_secrets_set)
    p_secrets_status = secrets_sub.add_parser(
        "status", help="per-provider presence + backend + masked fingerprint")
    p_secrets_status.add_argument("--json", action="store_true", help="emit JSON")
    p_secrets_status.set_defaults(func=cmd_secrets_status)

    # F2: model-swap drill — behavioral diff of a candidate provider over a corpus.
    p_drill = sub.add_parser("drill", help="operational drills (F2)")
    drill_sub = p_drill.add_subparsers(dest="drill_command", required=True)
    p_drill_swap = drill_sub.add_parser(
        "model-swap", help="replay a drill corpus against a candidate model profile")
    p_drill_swap.add_argument("--corpus", required=True,
                              help="path to a DrillCorpus JSONL file")
    p_drill_swap.add_argument("--candidate", required=True,
                              help="candidate model profile (e.g. coding, challenger)")
    p_drill_swap.add_argument("--config-dir", default="config/live",
                              help="model/provider config dir (default config/live)")
    p_drill_swap.add_argument("--limit", type=int, default=None,
                              help="bound the number of replayed entries")
    p_drill_swap.add_argument("--json", action="store_true", help="emit JSON")
    p_drill_swap.set_defaults(func=cmd_drill_model_swap)

    # F3.1: governance preflight for external executors (read-only; no execution).
    p_gate = sub.add_parser("gate", help="external-executor governance gate (F3)")
    gate_sub = p_gate.add_subparsers(dest="gate_command", required=True)
    p_gate_check = gate_sub.add_parser(
        "check", help="preflight a proposed (tool, args) through contract + policy")
    p_gate_check.add_argument("--proposal", help='inline proposal JSON, e.g. '
                              '\'{"tool": "read_file", "args": {"path": "a.py"}}\'')
    p_gate_check.add_argument("--proposal-file", help="path to a proposal JSON file")
    p_gate_check.add_argument("--card", help="inline external-executor AgentCard JSON")
    p_gate_check.add_argument("--card-file", help="path to an AgentCard JSON file")
    p_gate_check.add_argument("--executor", default="external-executor",
                              help="external executor id (provenance origin_ref)")
    p_gate_check.add_argument("--json", action="store_true", help="emit JSON")
    p_gate_check.set_defaults(func=cmd_gate_check)

    # F3.5: read-only F3 exit seal + external-executor surface projection.
    p_f3 = sub.add_parser("f3", help="external-executor phase (F3) inspection")
    f3_sub = p_f3.add_subparsers(dest="f3_command", required=True)
    p_f3_seal = f3_sub.add_parser("seal", help="print the derived F3 exit seal")
    p_f3_seal.add_argument("--reports-dir", default="agent/reports",
                           help="reports dir the seal reads (default agent/reports)")
    p_f3_seal.add_argument("--json", action="store_true", help="emit JSON")
    p_f3_seal.set_defaults(func=cmd_f3_seal)
    p_f3_surface = f3_sub.add_parser(
        "surface", help="project a demo external executor's reachable tool surface")
    p_f3_surface.add_argument("--executor", default="demo-executor",
                              help="executor id for the projection")
    p_f3_surface.add_argument("--trusted", action="store_true",
                              help="seed a trusted track record for the demo")
    p_f3_surface.set_defaults(func=cmd_f3_surface)

    # F4.4: read-only F4 exit seal + ContextLoom assembly projection.
    p_f4 = sub.add_parser("f4", help="cognition / ContextLoom (F4) inspection")
    f4_sub = p_f4.add_subparsers(dest="f4_command", required=True)
    p_f4_seal = f4_sub.add_parser("seal", help="print the derived F4 exit seal")
    p_f4_seal.add_argument("--reports-dir", default="agent/reports",
                           help="reports dir the seal reads (default agent/reports)")
    p_f4_seal.add_argument("--json", action="store_true", help="emit JSON")
    p_f4_seal.set_defaults(func=cmd_f4_seal)
    p_f4_loom = f4_sub.add_parser(
        "loom", help="project a demo ContextLoom assembly (provenance + budget)")
    p_f4_loom.add_argument("--max-tokens", type=int, default=60,
                           help="assembly token budget for the demo")
    p_f4_loom.set_defaults(func=cmd_f4_loom)

    # F4B: MCP client bridge — Aurel calls OUT to external MCP servers (read-only).
    p_mc = sub.add_parser("mcp-client", help="external MCP servers Aurel calls OUT to (F4B)")
    mc_sub = p_mc.add_subparsers(dest="mcp_client_command", required=True)
    p_mc_ls = mc_sub.add_parser("list-servers", help="list configured MCP servers")
    p_mc_ls.add_argument("--config", default="config/live/mcp_servers.yaml")
    p_mc_ls.add_argument("--json", action="store_true")
    p_mc_ls.set_defaults(func=cmd_mcp_client_list_servers)
    p_mc_seal = mc_sub.add_parser("seal", help="print the derived F4B exit seal")
    p_mc_seal.add_argument("--reports-dir", default="agent/reports")
    p_mc_seal.add_argument("--json", action="store_true")
    p_mc_seal.set_defaults(func=cmd_mcp_client_seal)
    p_mc_demo = mc_sub.add_parser(
        "demo", help="connect→list→call→sink against an in-process fake server")
    p_mc_demo.set_defaults(func=cmd_mcp_client_demo)

    # F5: Front server — the one door between UI and kernel (flag AUREL_FRONT_SERVER).
    p_front = sub.add_parser("front", help="Aurel Front v1 server (F5)")
    front_sub = p_front.add_subparsers(dest="front_command", required=True)
    p_front_serve = front_sub.add_parser("serve", help="run the Front HTTP server")
    p_front_serve.add_argument("--host", default="127.0.0.1")
    p_front_serve.add_argument("--port", type=int, default=8765)
    p_front_serve.set_defaults(func=cmd_front_serve)

    p_dk = sub.add_parser("dual-kernel", help="inspect the dual-kernel surface")
    dk_sub = p_dk.add_subparsers(dest="dual_kernel_command", required=True)
    p_dk_status = dk_sub.add_parser("status", help="flag state + canon coverage")
    p_dk_status.add_argument("--json", action="store_true", help="emit JSON")
    p_dk_status.set_defaults(func=cmd_dual_kernel_status)
    p_dk_bind = dk_sub.add_parser(
        "bindings", help="canon firewall: gate → no-collapse law")
    p_dk_bind.add_argument("--json", action="store_true", help="emit JSON")
    p_dk_bind.set_defaults(func=cmd_dual_kernel_bindings)
    p_dk_verify = dk_sub.add_parser(
        "verify-ledger", help="verify a decision ledger hash-chain")
    p_dk_verify.add_argument("path", help="path to a dual-kernel events JSONL")
    p_dk_verify.set_defaults(func=cmd_dual_kernel_verify_ledger)
    p_dk_show = dk_sub.add_parser(
        "show", help="print the 01I projection of a decision ledger")
    p_dk_show.add_argument("path", help="path to a dual-kernel events JSONL")
    p_dk_show.add_argument("--json", action="store_true", help="emit JSON")
    p_dk_show.set_defaults(func=cmd_dual_kernel_show)

    p_rz = sub.add_parser("reasoning", help="reasoning scheduler surface (read-only)")
    rz_sub = p_rz.add_subparsers(dest="reasoning_command", required=True)
    p_rz_status = rz_sub.add_parser("status", help="scheduler flag + vocabularies")
    p_rz_status.add_argument("--json", action="store_true", help="emit JSON")
    p_rz_status.set_defaults(func=cmd_reasoning_status)
    p_rz_work = rz_sub.add_parser(
        "workload", help="project a run's reasoning workload from its trace")
    p_rz_work.add_argument("run_id", help="run id under the trace dir")
    p_rz_work.add_argument("--trace-dir", default=".traces", help="trace base dir")
    p_rz_work.add_argument("--json", action="store_true", help="emit JSON")
    p_rz_work.set_defaults(func=cmd_reasoning_workload)

    # A7: read-only Memory Explorer — projections over a run's persisted trace.
    p_mem = sub.add_parser("memory", help="memory explorer surface (read-only)")
    mem_sub = p_mem.add_subparsers(dest="memory_command", required=True)

    def _mem_common(p: "argparse.ArgumentParser") -> None:
        p.add_argument("run_id", help="run id under the trace dir")
        p.add_argument("--trace-dir", default=".traces", help="trace base dir")
        p.add_argument("--durable", default=None,
                       help="optional A3 durable JSONL path (adds record content)")
        p.add_argument("--json", action="store_true", help="emit JSON")

    p_mem_explore = mem_sub.add_parser(
        "explore", help="current records + graph/rejected counts from the trace")
    _mem_common(p_mem_explore)
    p_mem_explore.set_defaults(func=cmd_memory_explore)

    p_mem_history = mem_sub.add_parser(
        "history", help="belief history (supersession chain) for a memory id")
    p_mem_history.add_argument("memory_id", help="the memory id to trace")
    _mem_common(p_mem_history)
    p_mem_history.set_defaults(func=cmd_memory_history)

    p_mem_graph = mem_sub.add_parser(
        "graph", help="typed memory edges reconstructed from the trace")
    _mem_common(p_mem_graph)
    p_mem_graph.set_defaults(func=cmd_memory_graph)

    p_mem_rejected = mem_sub.add_parser(
        "rejected", help="governance deny rows kept for audit")
    _mem_common(p_mem_rejected)
    p_mem_rejected.set_defaults(func=cmd_memory_rejected)

    p_verify = sub.add_parser("verify", help="run the pytest suite")
    p_verify.add_argument("-v", "--verbose", action="store_true")
    p_verify.set_defaults(func=cmd_verify)

    p_seal = sub.add_parser("alpha-seal", help="run P1.0 alpha readiness checks")
    p_seal.add_argument("--json", action="store_true")
    p_seal.add_argument("--skip-tests", action="store_true",
                        help="check docs/compile only; skip pytest")
    p_seal.add_argument("--skip-coverage", action="store_true",
                        help="run pytest without coverage threshold")
    p_seal.set_defaults(func=cmd_alpha_seal)

    p_repo = sub.add_parser("repo-task", help="plan/apply a bounded repository task")
    p_repo.add_argument("objective")
    p_repo.add_argument("--repo", default=".")
    p_repo.add_argument("--apply", action="store_true",
                        help="apply the generated patch; default is plan-only")
    p_repo.add_argument("--allowed-path", action="append")
    p_repo.add_argument("--disallowed-path", action="append")
    p_repo.add_argument("--max-files-changed", type=int, default=2)
    p_repo.add_argument("--max-repair-iterations", type=int, default=2)
    p_repo.add_argument("--test-command", default="")
    p_repo.add_argument("--approval-mode", default="auto",
                        choices=["auto", "console", "deny", "preview_only"])
    p_repo.add_argument("--dry-run", action="store_true",
                        help="show plan and approval requirements without applying")
    p_repo.add_argument("--sandbox", default=None,
                        choices=_SANDBOX_CHOICES,
                        help="sandbox profile; default auto (hard isolation) for --apply")
    p_repo.add_argument("--planner", default="deterministic",
                        choices=["deterministic", "demo-heuristic", "llm", "hybrid", "dry_run"],
                        help="'deterministic' is a demo heuristic (alias: demo-heuristic); "
                             "it refuses objectives it has no patch strategy for")
    p_repo.add_argument("--provider", default="",
                        choices=["", "mock", "openai", "anthropic", "ollama", "deepseek"])
    p_repo.set_defaults(func=cmd_repo_task)

    p_sandbox = sub.add_parser("sandbox-status", help="show active sandbox profile diagnostics")
    p_sandbox.add_argument("--profile", default="restricted_local")
    p_sandbox.add_argument("--root", default=".")
    p_sandbox.add_argument("--json", action="store_true")
    p_sandbox.set_defaults(func=cmd_sandbox_status)

    p_approve = sub.add_parser("approve-demo", help="demonstrate approval outcomes")
    p_approve.add_argument("--repo", default=".")
    p_approve.add_argument("--mode", default="deny", choices=["deny", "auto"])
    p_approve.add_argument("--allow-writes", action="store_true")
    p_approve.set_defaults(func=cmd_approve_demo)

    p_praxis = sub.add_parser("praxis-demo", help="demonstrate praxis experience capture")
    p_praxis.set_defaults(func=cmd_praxis_demo)

    p_mem = sub.add_parser("memory-candidates", help="list praxis memory candidates")
    p_mem.set_defaults(func=cmd_memory_candidates)

    p_pr = sub.add_parser("praxis-report", help="show latest praxis report")
    p_pr.set_defaults(func=cmd_praxis_report)

    p_harness = sub.add_parser(
        "demo-harness",
        help="run P0.19 demo harness scenario (controlled repo for P0.20)",
    )
    p_harness.add_argument(
        "scenario",
        nargs="?",
        default="buggy_calculator",
        help="scenario id or 'list' to show available scenarios",
    )
    p_harness.add_argument("--repo-parent", default=".",
                           help="parent directory for temporary demo repo")
    p_harness.add_argument("--apply", action="store_true",
                           help="apply patch via RepositoryAgentLoop (default: plan-only)")
    p_harness.add_argument("--dry-run", action="store_true",
                           help="record approval requirements without applying")
    p_harness.add_argument("--approval-mode", default="auto",
                           choices=["auto", "console", "deny", "preview_only"])
    p_harness.add_argument("--sandbox", default=None,
                           choices=_SANDBOX_CHOICES,
                           help="sandbox profile; default auto (hard isolation) for --apply")
    p_harness.add_argument("--planner", default="deterministic",
                           choices=["deterministic", "llm", "hybrid", "dry_run"])
    p_harness.add_argument("--provider", default="",
                           choices=["", "mock", "openai", "anthropic", "ollama"])
    p_harness.add_argument("--evidence-dir", default="",
                           help="write P0.20 evidence artifacts to this directory")
    p_harness.set_defaults(func=cmd_demo_harness)

    p_config = sub.add_parser("config", help="model configuration commands")
    config_sub = p_config.add_subparsers(dest="config_command", required=True)
    p_config_validate = config_sub.add_parser("validate", help="validate agent/config YAML")
    p_config_validate.add_argument("--config-dir", default="")
    p_config_validate.add_argument("--json", action="store_true")
    p_config_validate.set_defaults(func=cmd_config_validate)

    p_models = sub.add_parser("models", help="model profile commands")
    models_sub = p_models.add_subparsers(dest="models_command", required=True)
    p_models_list = models_sub.add_parser("list", help="list configured model profiles")
    p_models_list.add_argument("--config-dir", default="")
    p_models_list.add_argument("--json", action="store_true")
    p_models_list.set_defaults(func=cmd_models_list)

    p_providers = sub.add_parser("providers", help="provider status commands")
    providers_sub = p_providers.add_subparsers(dest="providers_command", required=True)
    p_providers_status = providers_sub.add_parser("status", help="show provider status")
    p_providers_status.add_argument("--config-dir", default="")
    p_providers_status.add_argument("--json", action="store_true")
    p_providers_status.set_defaults(func=cmd_providers_status)

    p_prompts = sub.add_parser("prompts", help="prompt manifest commands")
    prompts_sub = p_prompts.add_subparsers(dest="prompts_command", required=True)

    p_prompts_validate = prompts_sub.add_parser("validate", help="validate prompt manifests")
    p_prompts_validate.add_argument("--prompts-dir", default="")
    p_prompts_validate.add_argument("--config-dir", default="")
    p_prompts_validate.add_argument("--skip-model-config", action="store_true")
    p_prompts_validate.add_argument("--json", action="store_true")
    p_prompts_validate.set_defaults(func=cmd_prompts_validate)

    p_prompts_list = prompts_sub.add_parser("list", help="list prompt manifests")
    p_prompts_list.add_argument("--prompts-dir", default="")
    p_prompts_list.add_argument("--config-dir", default="")
    p_prompts_list.add_argument("--skip-model-config", action="store_true")
    p_prompts_list.add_argument("--json", action="store_true")
    p_prompts_list.set_defaults(func=cmd_prompts_list)

    p_prompts_show = prompts_sub.add_parser("show", help="show prompt metadata and policy")
    p_prompts_show.add_argument("prompt_id")
    p_prompts_show.add_argument("--prompts-dir", default="")
    p_prompts_show.add_argument("--config-dir", default="")
    p_prompts_show.add_argument("--skip-model-config", action="store_true")
    p_prompts_show.add_argument("--json", action="store_true")
    p_prompts_show.set_defaults(func=cmd_prompts_show)

    p_prompts_render = prompts_sub.add_parser("render", help="render prompt and print trace-safe summary")
    p_prompts_render.add_argument("prompt_id")
    p_prompts_render.add_argument("--var", action="append", default=[])
    p_prompts_render.add_argument("--dry-run", action="store_true")
    p_prompts_render.add_argument("--prompts-dir", default="")
    p_prompts_render.add_argument("--config-dir", default="")
    p_prompts_render.add_argument("--skip-model-config", action="store_true")
    p_prompts_render.add_argument("--json", action="store_true")
    p_prompts_render.set_defaults(func=cmd_prompts_render)

    # P1.5.0 — evaluation foundation
    p_evaluation = sub.add_parser("evaluation", help="evaluation mirror foundation (P1.5)")
    evaluation_sub = p_evaluation.add_subparsers(dest="evaluation_command", required=True)
    p_eval_foundation = evaluation_sub.add_parser("foundation", help="P1.5.0 foundation gate")
    eval_foundation_sub = p_eval_foundation.add_subparsers(dest="foundation_command", required=True)

    p_eval_status = eval_foundation_sub.add_parser("status", help="show P1.5.0 foundation status")
    p_eval_status.add_argument("--json", action="store_true")
    p_eval_status.set_defaults(func=cmd_evaluation_foundation_status)

    p_eval_scope = eval_foundation_sub.add_parser("scope", help="show default scope for domain")
    p_eval_scope.add_argument("--domain", required=True, help="EvaluationDomain value")
    p_eval_scope.add_argument("--json", action="store_true")
    p_eval_scope.set_defaults(func=cmd_evaluation_foundation_scope)

    # P1.5.1 — evaluation object model
    p_eval_objects = evaluation_sub.add_parser("objects", help="P1.5.1 evaluation object model")
    eval_objects_sub = p_eval_objects.add_subparsers(dest="objects_command", required=True)

    p_obj_status = eval_objects_sub.add_parser("status", help="show P1.5.1 object model status")
    p_obj_status.add_argument("--json", action="store_true")
    p_obj_status.set_defaults(func=cmd_evaluation_objects_status)

    p_obj_examples = eval_objects_sub.add_parser("examples", help="show example evaluation results")
    p_obj_examples.add_argument("--json", action="store_true")
    p_obj_examples.set_defaults(func=cmd_evaluation_objects_examples)

    # P1.5.2 — capability evidence
    p_eval_cap_ev = evaluation_sub.add_parser("capability-evidence", help="P1.5.2 capability evidence record")
    cap_ev_sub = p_eval_cap_ev.add_subparsers(dest="cap_evidence_command", required=True)

    p_cap_status = cap_ev_sub.add_parser("status", help="show P1.5.2 capability evidence status")
    p_cap_status.add_argument("--json", action="store_true")
    p_cap_status.set_defaults(func=cmd_evaluation_capability_evidence_status)

    p_cap_examples = cap_ev_sub.add_parser("examples", help="show example capability evidence records")
    p_cap_examples.add_argument("--json", action="store_true")
    p_cap_examples.set_defaults(func=cmd_evaluation_capability_evidence_examples)

    # P1.5.3 — evaluation subject registry
    p_eval_subjects = evaluation_sub.add_parser("subjects", help="P1.5.3 evaluation subject registry")
    subjects_sub = p_eval_subjects.add_subparsers(dest="subjects_command", required=True)

    p_subj_status = subjects_sub.add_parser("status", help="show P1.5.3 subject registry status")
    p_subj_status.add_argument("--json", action="store_true")
    p_subj_status.set_defaults(func=cmd_evaluation_subjects_status)

    p_subj_examples = subjects_sub.add_parser("examples", help="show example registry entries and subjects")
    p_subj_examples.add_argument("--json", action="store_true")
    p_subj_examples.set_defaults(func=cmd_evaluation_subjects_examples)

    # P1.5.4 — evaluation criteria schema
    p_eval_criteria = evaluation_sub.add_parser("criteria", help="P1.5.4 evaluation criteria schema")
    criteria_sub = p_eval_criteria.add_subparsers(dest="criteria_command", required=True)

    p_crit_status = criteria_sub.add_parser("status", help="show P1.5.4 criteria schema status")
    p_crit_status.add_argument("--json", action="store_true")
    p_crit_status.set_defaults(func=cmd_evaluation_criteria_status)

    p_crit_examples = criteria_sub.add_parser("examples", help="show example criteria schemas")
    p_crit_examples.add_argument("--json", action="store_true")
    p_crit_examples.set_defaults(func=cmd_evaluation_criteria_examples)

    # P1.5.5 — evaluation run envelope
    p_eval_runs = evaluation_sub.add_parser("runs", help="P1.5.5 evaluation run envelope")
    runs_sub = p_eval_runs.add_subparsers(dest="runs_command", required=True)

    p_runs_status = runs_sub.add_parser("status", help="show P1.5.5 run envelope status")
    p_runs_status.add_argument("--json", action="store_true")
    p_runs_status.set_defaults(func=cmd_evaluation_runs_status)

    p_runs_examples = runs_sub.add_parser("examples", help="show example run envelopes")
    p_runs_examples.add_argument("--json", action="store_true")
    p_runs_examples.set_defaults(func=cmd_evaluation_runs_examples)

    # P1.5.6 — result classification engine
    p_eval_classify = evaluation_sub.add_parser("classify", help="P1.5.6 result classification engine")
    classify_sub = p_eval_classify.add_subparsers(dest="classify_command", required=True)

    p_classify_status = classify_sub.add_parser("status", help="show P1.5.6 classification engine status")
    p_classify_status.add_argument("--json", action="store_true")
    p_classify_status.set_defaults(func=cmd_evaluation_classify_status)

    p_classify_examples = classify_sub.add_parser("examples", help="show example classification objects")
    p_classify_examples.add_argument("--json", action="store_true")
    p_classify_examples.set_defaults(func=cmd_evaluation_classify_examples)

    # P1.5.7 — evidence-to-claim binding
    p_eval_binding = evaluation_sub.add_parser("binding", help="P1.5.7 evidence-to-claim binding")
    binding_sub = p_eval_binding.add_subparsers(dest="binding_command", required=True)

    p_binding_status = binding_sub.add_parser("status", help="show P1.5.7 binding status")
    p_binding_status.add_argument("--json", action="store_true")
    p_binding_status.set_defaults(func=cmd_evaluation_binding_status)

    p_binding_examples = binding_sub.add_parser("examples", help="show example bindings")
    p_binding_examples.add_argument("--json", action="store_true")
    p_binding_examples.set_defaults(func=cmd_evaluation_binding_examples)

    # P1.5.8 — benchmark hygiene guard
    p_eval_hygiene = evaluation_sub.add_parser("hygiene", help="P1.5.8 benchmark hygiene guard")
    hygiene_sub = p_eval_hygiene.add_subparsers(dest="hygiene_command", required=True)

    p_hygiene_status = hygiene_sub.add_parser("status", help="show P1.5.8 hygiene status")
    p_hygiene_status.add_argument("--json", action="store_true")
    p_hygiene_status.set_defaults(func=cmd_evaluation_hygiene_status)

    p_hygiene_examples = hygiene_sub.add_parser("examples", help="show example hygiene decisions")
    p_hygiene_examples.add_argument("--json", action="store_true")
    p_hygiene_examples.set_defaults(func=cmd_evaluation_hygiene_examples)

    # P1.5.9 — adversarial evaluation cases
    p_eval_adversarial = evaluation_sub.add_parser("adversarial", help="P1.5.9 adversarial evaluation cases")
    adversarial_sub = p_eval_adversarial.add_subparsers(dest="adversarial_command", required=True)

    p_adversarial_status = adversarial_sub.add_parser("status", help="show P1.5.9 adversarial case status")
    p_adversarial_status.add_argument("--json", action="store_true")
    p_adversarial_status.set_defaults(func=cmd_evaluation_adversarial_status)

    p_adversarial_examples = adversarial_sub.add_parser("examples", help="show example adversarial cases")
    p_adversarial_examples.add_argument("--json", action="store_true")
    p_adversarial_examples.set_defaults(func=cmd_evaluation_adversarial_examples)

    # P1.5.10 — baseline comparison model
    p_eval_baseline = evaluation_sub.add_parser("baseline", help="P1.5.10 baseline comparison model")
    baseline_sub = p_eval_baseline.add_subparsers(dest="baseline_command", required=True)

    p_baseline_status = baseline_sub.add_parser("status", help="show P1.5.10 baseline comparison status")
    p_baseline_status.add_argument("--json", action="store_true")
    p_baseline_status.set_defaults(func=cmd_evaluation_baseline_status)

    p_baseline_examples = baseline_sub.add_parser("examples", help="show example baseline comparisons")
    p_baseline_examples.add_argument("--json", action="store_true")
    p_baseline_examples.set_defaults(func=cmd_evaluation_baseline_examples)

    # P1.6.18 — policy projection CLI binding
    p_policy = sub.add_parser("policy", help="P1.6 policy projection (read-only)")
    policy_sub = p_policy.add_subparsers(dest="policy_command", required=True)

    p_policy_status = policy_sub.add_parser("status", help="show policy subsystem status")
    p_policy_status.add_argument("--json", action="store_true")
    p_policy_status.set_defaults(func=cmd_policy_status)

    p_policy_projection = policy_sub.add_parser(
        "projection", help="show policy projection contract",
    )
    p_policy_projection.add_argument("--json", action="store_true")
    p_policy_projection.set_defaults(func=cmd_policy_projection)

    p_policy_unavailable = policy_sub.add_parser(
        "unavailable", help="list unavailable policy projection sections",
    )
    p_policy_unavailable.add_argument("--json", action="store_true")
    p_policy_unavailable.set_defaults(func=cmd_policy_unavailable)

    p_policy_harness = policy_sub.add_parser("harness", help="policy test harness commands")
    harness_sub = p_policy_harness.add_subparsers(dest="harness_command", required=True)

    p_harness_list = harness_sub.add_parser("list", help="list policy harness cases")
    p_harness_list.add_argument("--json", action="store_true")
    p_harness_list.set_defaults(func=cmd_policy_harness_list)

    p_harness_run = harness_sub.add_parser("run", help="run policy harness suite or case")
    p_harness_run.add_argument("--case", default="", help="run a single case by id")
    p_harness_run.add_argument("--json", action="store_true")
    p_harness_run.set_defaults(func=cmd_policy_harness_run)

    # P4-EXEC-G — AurelExec read-only status binding
    p_exec = sub.add_parser(
        "exec",
        help="P4 AurelExec read model (read-only)",
    )
    exec_sub = p_exec.add_subparsers(dest="exec_command", required=True)
    p_exec_status = exec_sub.add_parser(
        "status",
        help="show AurelExec status read model (read-only JSON)",
    )
    p_exec_status.set_defaults(func=cmd_exec_status)

    # P5-TRACE-D — AurelTrace TRACE_VERIFIED resolver / query / CLI (read-only)
    p_trace = sub.add_parser(
        "trace",
        help="P5 AurelTrace verification status (read-only)",
    )
    trace_sub = p_trace.add_subparsers(dest="trace_command", required=True)
    p_trace_status = trace_sub.add_parser(
        "status",
        help="show TRACE_VERIFIED resolver decisions over the demo substrate",
    )
    p_trace_status.add_argument("--json", action="store_true", help="emit JSON")
    p_trace_status.set_defaults(func=cmd_trace_status)
    p_trace_verify = trace_sub.add_parser(
        "verify",
        help="show per-target trace verification summaries (read-only)",
    )
    p_trace_verify.add_argument("--json", action="store_true", help="emit JSON")
    p_trace_verify.set_defaults(func=cmd_trace_verify)
    p_trace_inspect = trace_sub.add_parser(
        "inspect",
        help="inspect one resolver decision by target id (read-only)",
    )
    p_trace_inspect.add_argument("--target", help="target id to inspect")
    p_trace_inspect.set_defaults(func=cmd_trace_inspect)
    p_trace_audit = trace_sub.add_parser(
        "audit",
        help="show the trace verification audit summary (read-only)",
    )
    p_trace_audit.add_argument("--json", action="store_true", help="emit JSON")
    p_trace_audit.set_defaults(func=cmd_trace_audit)
    p_trace_anchor = trace_sub.add_parser(
        "anchor-verify",
        help="verify a persisted run against its external anchor (catches re-forge)",
    )
    p_trace_anchor.add_argument("run_id", help="run id under the trace dir")
    p_trace_anchor.add_argument("--trace-dir", default=".traces", help="trace base dir")
    p_trace_anchor.add_argument("--checkpoint-every", type=int, default=5)
    p_trace_anchor.add_argument("--json", action="store_true", help="emit JSON")
    p_trace_anchor.set_defaults(func=cmd_trace_anchor_verify)

    # SPINE-LIVE-5 — end-to-end living thread (model->flow->exec->trace->shell)
    p_spine = sub.add_parser(
        "spine",
        help="SPINE-LIVE end-to-end slice (governed live execution)",
    )
    spine_sub = p_spine.add_subparsers(dest="spine_command", required=True)
    p_spine_run = spine_sub.add_parser(
        "run", help="run the end-to-end spine slice and print evidence JSON"
    )
    p_spine_run.add_argument("--trace-dir", default=None, help="trace base dir")
    p_spine_run.add_argument("--run-id", default=None, help="explicit run id")
    p_spine_run.add_argument(
        "--live", action="store_true",
        help="use DeepSeek for the cognition leg (needs DEEPSEEK_API_KEY)",
    )
    p_spine_run.add_argument(
        "--model", default="pro",
        help="live model: pro (deepseek-v4-pro) | flash (deepseek-v4-flash)",
    )
    p_spine_run.add_argument(
        "--plan-driven", action="store_true",
        help="realize the model's own plan as the flow (entity proposes steps)",
    )
    p_spine_run.add_argument("--goal", default=None, help="task goal for the planner")
    p_spine_run.add_argument("--json", action="store_true", help="compact JSON")
    p_spine_run.set_defaults(func=cmd_spine_run)

    p_spine_replay = spine_sub.add_parser(
        "replay", help="record then replay a run from a model cassette (no network)"
    )
    p_spine_replay.add_argument("--trace-dir", default=None, help="trace base dir")
    p_spine_replay.add_argument("--goal", default=None, help="task goal for the planner")
    p_spine_replay.add_argument("--plan-driven", action="store_true")
    p_spine_replay.add_argument(
        "--allow-unsafe", action="store_true",
        help="dev-only: run replay on the UNSAFE local backend when no hard "
        "sandbox exists (labelled UNSAFE — not a security boundary)",
    )
    p_spine_replay.set_defaults(func=cmd_spine_replay)

    p_spine_serve = spine_sub.add_parser(
        "serve", help="launch the local SPINE-LIVE web console (browser UI)"
    )
    p_spine_serve.add_argument("--host", default="127.0.0.1")
    p_spine_serve.add_argument("--port", type=int, default=8765)
    p_spine_serve.set_defaults(func=cmd_spine_serve)

    # P2.10-D — Shell terminal client parity binding
    p_shell = sub.add_parser(
        "shell",
        help="P2.10 Shell terminal read model (read-only)",
    )
    shell_sub = p_shell.add_subparsers(dest="shell_command", required=True)

    p_shell_status = shell_sub.add_parser("status", help="show Shell terminal status")
    p_shell_status.add_argument("--json", action="store_true")
    p_shell_status.set_defaults(func=cmd_shell_status)

    p_shell_clients = shell_sub.add_parser("clients", help="list Shell clients")
    p_shell_clients.add_argument("--json", action="store_true")
    p_shell_clients.set_defaults(func=cmd_shell_clients)

    p_shell_surfaces = shell_sub.add_parser("surfaces", help="list Shell surfaces")
    p_shell_surfaces.add_argument("--json", action="store_true")
    p_shell_surfaces.set_defaults(func=cmd_shell_surfaces)

    p_shell_parity = shell_sub.add_parser("parity", help="show CLI/TUI parity matrix")
    p_shell_parity.add_argument("--json", action="store_true")
    p_shell_parity.set_defaults(func=cmd_shell_parity)

    p_shell_evidence = shell_sub.add_parser("evidence", help="list Shell evidence refs")
    p_shell_evidence.add_argument("--json", action="store_true")
    p_shell_evidence.set_defaults(func=cmd_shell_evidence)

    p_shell_run_modes = shell_sub.add_parser("run-modes", help="list terminal run modes")
    p_shell_run_modes.add_argument("--json", action="store_true")
    p_shell_run_modes.set_defaults(func=cmd_shell_run_modes)

    p_shell_run_view = shell_sub.add_parser(
        "run-view",
        help="SPINE-LIVE-4 live view of a persisted spine run (read-only)",
    )
    p_shell_run_view.add_argument("run_id", help="persisted trace run id")
    p_shell_run_view.add_argument(
        "--trace-dir", default=".traces", help="trace base dir (default .traces)"
    )
    p_shell_run_view.add_argument("--json", action="store_true")
    p_shell_run_view.set_defaults(func=cmd_shell_run_view)

    p_shell_export = shell_sub.add_parser(
        "export-json",
        help="export deterministic Shell terminal read model JSON",
    )
    p_shell_export.set_defaults(func=cmd_shell_export_json)

    p_shell_read_model = shell_sub.add_parser(
        "read-model",
        help="show Shell terminal read model",
    )
    p_shell_read_model.add_argument("--json", action="store_true")
    p_shell_read_model.set_defaults(func=cmd_shell_read_model)

    # P2.11-C — Shell permission inspection binding
    p_shell_permissions = shell_sub.add_parser(
        "permissions",
        help="P2.11-C surface permission inspection (read-only)",
    )
    permissions_sub = p_shell_permissions.add_subparsers(
        dest="permissions_command",
        required=True,
    )

    p_perm_summary = permissions_sub.add_parser(
        "summary",
        help="summarize permission inspection read model",
    )
    p_perm_summary.add_argument("--json", action="store_true")
    p_perm_summary.set_defaults(func=cmd_shell_permissions_summary)

    p_perm_clients = permissions_sub.add_parser(
        "clients",
        help="list client permission views",
    )
    p_perm_clients.add_argument("--json", action="store_true")
    p_perm_clients.set_defaults(func=cmd_shell_permissions_clients)

    p_perm_surfaces = permissions_sub.add_parser(
        "surfaces",
        help="list surface permission views",
    )
    p_perm_surfaces.add_argument("--json", action="store_true")
    p_perm_surfaces.set_defaults(func=cmd_shell_permissions_surfaces)

    p_perm_actions = permissions_sub.add_parser(
        "actions",
        help="list action permission views",
    )
    p_perm_actions.add_argument("--json", action="store_true")
    p_perm_actions.set_defaults(func=cmd_shell_permissions_actions)

    p_perm_show = permissions_sub.add_parser(
        "show",
        help="show filtered permission entries",
    )
    p_perm_show.add_argument("--client", default=None)
    p_perm_show.add_argument("--surface", default=None)
    p_perm_show.add_argument("--action", default=None)
    p_perm_show.add_argument("--level", default=None)
    p_perm_show.add_argument("--reason", default=None)
    p_perm_show.add_argument("--no-evidence", action="store_true")
    p_perm_show.add_argument("--sensitive", action="store_true")
    p_perm_show.add_argument("--denied", action="store_true")
    p_perm_show.add_argument("--future-gated", action="store_true")
    p_perm_show.add_argument("--contract-only", action="store_true")
    p_perm_show.add_argument("--unavailable", action="store_true")
    p_perm_show.add_argument("--preflight-only", action="store_true")
    p_perm_show.add_argument("--json", action="store_true")
    p_perm_show.set_defaults(func=cmd_shell_permissions_show)

    p_perm_evidence = permissions_sub.add_parser(
        "evidence",
        help="inspect evidence refs and NO_EVIDENCE entries",
    )
    p_perm_evidence.add_argument("--no-evidence", action="store_true")
    p_perm_evidence.add_argument("--json", action="store_true")
    p_perm_evidence.set_defaults(func=cmd_shell_permissions_evidence)

    p_perm_sensitive = permissions_sub.add_parser(
        "sensitive",
        help="inspect sensitive surface limitations",
    )
    p_perm_sensitive.add_argument("--json", action="store_true")
    p_perm_sensitive.set_defaults(func=cmd_shell_permissions_sensitive)

    p_perm_export = permissions_sub.add_parser(
        "export",
        help="export read-only permission inspection JSON",
    )
    p_perm_export.add_argument("--client", default=None)
    p_perm_export.add_argument("--surface", default=None)
    p_perm_export.add_argument("--action", default=None)
    p_perm_export.add_argument("--level", default=None)
    p_perm_export.add_argument("--no-evidence", action="store_true")
    p_perm_export.add_argument("--sensitive", action="store_true")
    p_perm_export.add_argument("--denied", action="store_true")
    p_perm_export.add_argument("--json", action="store_true")
    p_perm_export.set_defaults(func=cmd_shell_permissions_export)

    # P1.7.18 — path governance projection CLI binding
    p_pg = sub.add_parser(
        "path-governance",
        help="P1.7 path governance projection (read-only)",
    )
    pg_sub = p_pg.add_subparsers(dest="path_governance_command", required=True)

    p_pg_status = pg_sub.add_parser("status", help="show path governance projection status")
    p_pg_status.add_argument("--json", action="store_true")
    p_pg_status.add_argument("--table", action="store_true")
    p_pg_status.add_argument("--tui", action="store_true")
    p_pg_status.set_defaults(func=cmd_path_governance_status)

    p_pg_capabilities = pg_sub.add_parser(
        "capabilities", help="show path governance capability records",
    )
    p_pg_capabilities.add_argument("--json", action="store_true")
    p_pg_capabilities.add_argument("--table", action="store_true")
    p_pg_capabilities.add_argument("--tui", action="store_true")
    p_pg_capabilities.set_defaults(func=cmd_path_governance_capabilities)

    p_pg_read_model = pg_sub.add_parser(
        "read-model", help="show path governance read model (JSON)",
    )
    p_pg_read_model.add_argument("--json", action="store_true")
    p_pg_read_model.set_defaults(func=cmd_path_governance_read_model)

    p_pg_api_envelope = pg_sub.add_parser(
        "api-envelope", help="show path governance API envelope (JSON)",
    )
    p_pg_api_envelope.add_argument("--json", action="store_true")
    p_pg_api_envelope.set_defaults(func=cmd_path_governance_api_envelope)

    p_pg_events = pg_sub.add_parser("events", help="show projection event contracts")
    p_pg_events.add_argument("--json", action="store_true")
    p_pg_events.set_defaults(func=cmd_path_governance_events)

    p_pg_unavailable = pg_sub.add_parser(
        "unavailable", help="list unavailable path governance bindings",
    )
    p_pg_unavailable.add_argument("--json", action="store_true")
    p_pg_unavailable.set_defaults(func=cmd_path_governance_unavailable)

    p_pg_harness = pg_sub.add_parser(
        "harness-summary", help="show path governance harness projection summary",
    )
    p_pg_harness.add_argument("--json", action="store_true")
    p_pg_harness.set_defaults(func=cmd_path_governance_harness_summary)

    p_pg_policy = pg_sub.add_parser(
        "policy-context-summary",
        help="show policy context bridge projection summary",
    )
    p_pg_policy.add_argument("--json", action="store_true")
    p_pg_policy.set_defaults(func=cmd_path_governance_policy_context_summary)

    p_pg_trace = pg_sub.add_parser(
        "trace-hook-summary",
        help="show path resolution trace hook projection summary",
    )
    p_pg_trace.add_argument("--json", action="store_true")
    p_pg_trace.set_defaults(func=cmd_path_governance_trace_hook_summary)

    p_pg_violation = pg_sub.add_parser(
        "violation-drift-summary",
        help="show violation/drift trace hook projection summary",
    )
    p_pg_violation.add_argument("--json", action="store_true")
    p_pg_violation.set_defaults(func=cmd_path_governance_violation_drift_summary)

    # P1.9.28 — output passport read-only inspect CLI binding
    p_op = sub.add_parser(
        "output-passport",
        help="P1.9 output passport projection inspect (read-only)",
    )
    op_sub = p_op.add_subparsers(dest="output_passport_command", required=True)

    p_op_inspect = op_sub.add_parser(
        "inspect",
        help="inspect DEV_FIXTURE output passport projection (read-only)",
    )
    p_op_inspect.add_argument(
        "--dev-fixture",
        action="store_true",
        default=True,
        help="use DEV_FIXTURE projection payload",
    )
    p_op_inspect.add_argument("--json", action="store_true")
    p_op_inspect.add_argument("--text", action="store_true")
    p_op_inspect.set_defaults(func=cmd_output_passport_inspect)

    p_op_projection = op_sub.add_parser(
        "projection",
        help="show output passport projection/API/event contract",
    )
    p_op_projection.add_argument("--json", action="store_true")
    p_op_projection.add_argument("--text", action="store_true")
    p_op_projection.set_defaults(func=cmd_output_passport_projection)

    p_op_unavailable = op_sub.add_parser(
        "unavailable",
        help="list unavailable output passport bindings",
    )
    p_op_unavailable.add_argument("--json", action="store_true")
    p_op_unavailable.add_argument("--text", action="store_true")
    p_op_unavailable.set_defaults(func=cmd_output_passport_unavailable)

    # P3.7 — AurelFlow read-only projection binding (P3-FLOW-C)
    p_flow = sub.add_parser(
        "flow",
        help="P3.7 AurelFlow projection inspect (read-only; executes nothing)",
    )
    flow_sub = p_flow.add_subparsers(dest="flow_command", required=True)
    for flow_name, flow_help in (
        ("demo", "show DEV_FIXTURE flow demo state (demo state is not execution)"),
        ("inspect", "show flow state projection (read-only)"),
        ("timeline", "show local runtime behavior timeline (not Trace)"),
        ("wiring", "show hot/cold wiring truth matrix"),
        ("protocol", "show protocol / hybrid-ready boundary"),
        ("seal", "show the base P3.9 flow exit seal"),
    ):
        p_flow_cmd = flow_sub.add_parser(flow_name, help=flow_help)
        p_flow_cmd.add_argument("--json", action="store_true")
        if flow_name == "seal":
            p_flow_cmd.add_argument(
                "--base-p3", dest="base_p3", action="store_true", default=True,
                help="seal scope: base P3.0-P3.9 Flow (the only scope in this pack)",
            )
        p_flow_cmd.set_defaults(func=cmd_flow)

    p_identity = sub.add_parser("identity", help="identity kernel commands")
    identity_sub = p_identity.add_subparsers(dest="identity_command", required=True)

    # P1.4.15 — top-level identity status and verify
    p_identity_status = identity_sub.add_parser("status", help="show overall identity governance status (P1.4.15)")
    p_identity_status.add_argument("--json", action="store_true")
    p_identity_status.set_defaults(func=cmd_identity_status)

    p_identity_verify = identity_sub.add_parser("verify", help="run non-destructive identity governance checks (P1.4.15)")
    p_identity_verify.add_argument("--json", action="store_true")
    p_identity_verify.set_defaults(func=cmd_identity_verify)

    p_identity_kernel = identity_sub.add_parser("kernel", help="identity kernel operations")
    kernel_sub = p_identity_kernel.add_subparsers(dest="kernel_command", required=True)

    for name, func in (
        ("show", cmd_identity_kernel_show),
        ("validate", cmd_identity_kernel_validate),
        ("hash", cmd_identity_kernel_hash),
        ("attest", cmd_identity_kernel_attest),
    ):
        p_cmd = kernel_sub.add_parser(name)
        p_cmd.add_argument("--kernel-path", default="", help="path to identity_kernel.yaml")
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    p_identity_persona = identity_sub.add_parser("persona", help="persona manifest operations")
    persona_sub = p_identity_persona.add_subparsers(dest="persona_command", required=True)

    for name, func in (
        ("show", cmd_identity_persona_show),
        ("validate", cmd_identity_persona_validate),
        ("hash", cmd_identity_persona_hash),
        ("attest", cmd_identity_persona_attest),
        ("summary", cmd_identity_persona_summary),
    ):
        p_cmd = persona_sub.add_parser(name)
        p_cmd.add_argument("--persona-path", default="", help="path to persona_manifest.yaml")
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    p_identity_operator_contract = identity_sub.add_parser(
        "operator-contract",
        help="operator relationship contract operations",
    )
    operator_contract_sub = p_identity_operator_contract.add_subparsers(
        dest="operator_contract_command",
        required=True,
    )

    for name, func in (
        ("show", cmd_identity_operator_contract_show),
        ("validate", cmd_identity_operator_contract_validate),
        ("hash", cmd_identity_operator_contract_hash),
        ("attest", cmd_identity_operator_contract_attest),
        ("summary", cmd_identity_operator_contract_summary),
    ):
        p_cmd = operator_contract_sub.add_parser(name)
        p_cmd.add_argument(
            "--contract-path",
            default="",
            help="path to operator_contract.yaml",
        )
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    p_identity_modes = identity_sub.add_parser(
        "modes",
        help="communication modes registry operations",
    )
    modes_sub = p_identity_modes.add_subparsers(dest="modes_command", required=True)

    for name, func in (
        ("show", cmd_identity_modes_show),
        ("validate", cmd_identity_modes_validate),
        ("hash", cmd_identity_modes_hash),
        ("attest", cmd_identity_modes_attest),
        ("list", cmd_identity_modes_list),
    ):
        p_cmd = modes_sub.add_parser(name)
        p_cmd.add_argument(
            "--modes-path",
            default="",
            help="path to communication_modes.yaml",
        )
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    p_modes_summary = modes_sub.add_parser("summary", help="safe summary for one mode")
    p_modes_summary.add_argument("mode", help="mode name (e.g. FOCUS, HERETIC)")
    p_modes_summary.add_argument(
        "--modes-path",
        default="",
        help="path to communication_modes.yaml",
    )
    p_modes_summary.add_argument("--json", action="store_true")
    p_modes_summary.set_defaults(func=cmd_identity_modes_summary)

    p_identity_context = identity_sub.add_parser(
        "context",
        help="identity prompt context compiler operations",
    )
    context_sub = p_identity_context.add_subparsers(dest="context_command", required=True)

    for name, func in (
        ("compile", cmd_identity_context_compile),
        ("validate", cmd_identity_context_validate),
        ("hash", cmd_identity_context_hash),
        ("render", cmd_identity_context_render),
        ("attest", cmd_identity_context_attest),
    ):
        p_cmd = context_sub.add_parser(name)
        p_cmd.add_argument("--mode", required=True, help="communication mode (e.g. DEPLOY, HERETIC)")
        p_cmd.add_argument(
            "--kernel-path",
            default="",
            help="path to identity_kernel.yaml",
        )
        p_cmd.add_argument(
            "--persona-path",
            default="",
            help="path to persona_manifest.yaml",
        )
        p_cmd.add_argument(
            "--operator-path",
            default="",
            help="path to operator_contract.yaml",
        )
        p_cmd.add_argument(
            "--modes-path",
            default="",
            help="path to communication_modes.yaml",
        )
        p_cmd.add_argument(
            "--compiler-path",
            default="",
            help="path to identity_prompt_compiler.yaml",
        )
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    p_identity_card = identity_sub.add_parser("card", help="agent identity card operations")
    card_sub = p_identity_card.add_subparsers(dest="card_command", required=True)

    for name, func in (
        ("show", cmd_identity_card_show),
        ("validate", cmd_identity_card_validate),
        ("hash", cmd_identity_card_hash),
        ("attest", cmd_identity_card_attest),
        ("taxonomy", cmd_identity_card_taxonomy),
    ):
        p_cmd = card_sub.add_parser(name)
        p_cmd.add_argument("--kernel-path", default="", help="path to identity_kernel.yaml")
        p_cmd.add_argument("--persona-path", default="", help="path to persona_manifest.yaml")
        p_cmd.add_argument("--operator-path", default="", help="path to operator_contract.yaml")
        p_cmd.add_argument("--modes-path", default="", help="path to communication_modes.yaml")
        p_cmd.add_argument(
            "--compiler-path",
            default="",
            help="path to identity_prompt_compiler.yaml",
        )
        p_cmd.add_argument(
            "--self-model-policy-path",
            default="",
            help="path to self_model_policy.yaml",
        )
        p_cmd.add_argument(
            "--card-config-path",
            default="",
            help="path to agent_identity_card.yaml",
        )
        p_cmd.add_argument(
            "--prompt-mode",
            default="FOCUS",
            help="communication mode for prompt context binding",
        )
        p_cmd.add_argument(
            "--runtime-instance-id",
            default="",
            help="override runtime instance id (tests/determinism)",
        )
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    p_identity_self = identity_sub.add_parser("self", help="self-model operations")
    self_sub = p_identity_self.add_subparsers(dest="self_command", required=True)

    for name, func in (
        ("show", cmd_identity_self_show),
        ("validate", cmd_identity_self_validate),
        ("hash", cmd_identity_self_hash),
        ("attest", cmd_identity_self_attest),
        ("capabilities", cmd_identity_self_capabilities),
        ("limitations", cmd_identity_self_limitations),
    ):
        p_cmd = self_sub.add_parser(name)
        p_cmd.add_argument("--kernel-path", default="", help="path to identity_kernel.yaml")
        p_cmd.add_argument("--persona-path", default="", help="path to persona_manifest.yaml")
        p_cmd.add_argument("--operator-path", default="", help="path to operator_contract.yaml")
        p_cmd.add_argument("--modes-path", default="", help="path to communication_modes.yaml")
        p_cmd.add_argument(
            "--compiler-path",
            default="",
            help="path to identity_prompt_compiler.yaml",
        )
        p_cmd.add_argument(
            "--self-model-policy-path",
            default="",
            help="path to self_model_policy.yaml",
        )
        p_cmd.add_argument(
            "--prompt-mode",
            default="FOCUS",
            help="communication mode for optional prompt context binding",
        )
        p_cmd.add_argument("--json", action="store_true")
        if name == "attest":
            p_cmd.add_argument(
                "--write",
                default="",
                help="write attestation JSON to path (explicit only)",
            )
        p_cmd.set_defaults(func=func)

    # P1.4.8 Autonomy Scale Engine
    p_identity_autonomy = identity_sub.add_parser("autonomy", help="autonomy scale engine (P1.4.8)")
    autonomy_sub = p_identity_autonomy.add_subparsers(dest="autonomy_command", required=True)
    p_autonomy_eval = autonomy_sub.add_parser("evaluate", help="evaluate autonomy for a single action")
    p_autonomy_eval.add_argument("--action-category", required=True, help="Action category (answer, suggest, draft, etc.)")
    p_autonomy_eval.add_argument("--action-name", required=True, help="Human-readable action name")
    p_autonomy_eval.add_argument("--action-id", default="cli_evaluate", help="Unique action identifier")
    p_autonomy_eval.add_argument("--requested-by", default="operator", help="Who requested the action")
    p_autonomy_eval.add_argument("--risk-tier", default="", help="Risk tier (R0_NONE, R1_LOW, etc.)")
    p_autonomy_eval.add_argument("--reversibility-tier", default="", help="Reversibility tier (R1_FULLY_REVERSIBLE, etc.)")
    p_autonomy_eval.add_argument("--target", default=None, help="Target of the action")
    p_autonomy_eval.add_argument("--tool-name", default=None, help="Tool name if action uses a tool")
    p_autonomy_eval.add_argument("--path", default=None, help="Filesystem path if action affects a file")
    p_autonomy_eval.add_argument("--required-capability", default=None, help="Required capability ID")
    p_autonomy_eval.add_argument("--json", action="store_true")
    # Identity source paths (same as card commands)
    p_autonomy_eval.add_argument("--kernel-path", default="", help="path to identity_kernel.yaml")
    p_autonomy_eval.add_argument("--persona-path", default="", help="path to persona_manifest.yaml")
    p_autonomy_eval.add_argument("--operator-path", default="", help="path to operator_contract.yaml")
    p_autonomy_eval.add_argument("--modes-path", default="", help="path to communication_modes.yaml")
    p_autonomy_eval.add_argument("--compiler-path", default="", help="path to identity_prompt_compiler.yaml")
    p_autonomy_eval.add_argument("--self-model-policy-path", default="", help="path to self_model_policy.yaml")
    p_autonomy_eval.add_argument("--card-config-path", default="", help="path to agent_identity_card.yaml")
    p_autonomy_eval.add_argument("--prompt-mode", default="FOCUS", help="communication mode for prompt context binding")
    p_autonomy_eval.add_argument("--runtime-instance-id", default="", help="override runtime instance id")
    p_autonomy_eval.set_defaults(func=cmd_identity_autonomy_evaluate)

    # P1.4.9 Measured Autonomy Score
    p_autonomy_measure = autonomy_sub.add_parser("measure", help="measure autonomy from decision records (P1.4.9)")
    p_autonomy_measure.add_argument("--agent-id", default=None, help="Agent ID to measure (default: from identity card)")
    p_autonomy_measure.add_argument("--records-path", default=None, help="Path to JSONL records file")
    p_autonomy_measure.add_argument("--max-decisions", type=int, default=100, help="Max decisions to evaluate")
    p_autonomy_measure.add_argument("--minimum-decisions", type=int, default=5, help="Minimum decisions required")
    p_autonomy_measure.add_argument("--since", default=None, help="ISO timestamp to filter from")
    p_autonomy_measure.add_argument("--until", default=None, help="ISO timestamp to filter until")
    p_autonomy_measure.add_argument("--exclude-denied", action="store_true", help="Exclude denied decisions")
    p_autonomy_measure.add_argument("--evaluate-and-record", action="store_true", help="Evaluate a new decision and record it before measuring")
    p_autonomy_measure.add_argument("--action-category", default="answer", help="For --evaluate-and-record: action category")
    p_autonomy_measure.add_argument("--action-name", default="measure_record", help="For --evaluate-and-record: action name")
    p_autonomy_measure.add_argument("--requested-by", default="operator", help="Who requested")
    p_autonomy_measure.add_argument("--risk-tier", default="", help="Risk tier for evaluate-and-record")
    p_autonomy_measure.add_argument("--reversibility-tier", default="", help="Reversibility tier for evaluate-and-record")
    p_autonomy_measure.add_argument("--required-capability", default=None, help="Required capability")
    p_autonomy_measure.add_argument("--json", action="store_true")
    # Identity source paths
    for arg_name in ("kernel-path", "persona-path", "operator-path", "modes-path",
                     "compiler-path", "self-model-policy-path", "card-config-path",
                     "prompt-mode", "runtime-instance-id"):
        p_autonomy_measure.add_argument(f"--{arg_name}", default="", help=f"path to {arg_name.replace('-','_')}")
    p_autonomy_measure.set_defaults(func=cmd_identity_autonomy_measure)

    # P1.4.10 Capability Claim Boundary Engine
    p_identity_claims = identity_sub.add_parser("claims", help="capability claim boundary engine (P1.4.10)")
    claims_sub = p_identity_claims.add_subparsers(dest="claims_command", required=True)
    p_claims_evaluate = claims_sub.add_parser("evaluate", help="evaluate a capability claim")
    p_claims_evaluate.add_argument("--claim", default="", help="claim text to evaluate")
    p_claims_evaluate.add_argument("--claim-id", default="", help="registered claim ID to evaluate")
    p_claims_evaluate.add_argument("--claim-type", default="", help="claim type for ad-hoc evaluation")
    p_claims_evaluate.add_argument("--json", action="store_true")
    p_claims_evaluate.set_defaults(func=cmd_identity_claims_evaluate)
    p_claims_list = claims_sub.add_parser("list", help="list all registered claims")
    p_claims_list.add_argument("--json", action="store_true")
    p_claims_list.set_defaults(func=cmd_identity_claims_list)
    p_claims_show = claims_sub.add_parser("show", help="show a specific registered claim")
    p_claims_show.add_argument("claim_id", help="claim ID to show")
    p_claims_show.add_argument("--json", action="store_true")
    p_claims_show.set_defaults(func=cmd_identity_claims_show)
    p_claims_validate = claims_sub.add_parser("validate", help="validate the claim registry")
    p_claims_validate.add_argument("--json", action="store_true")
    p_claims_validate.set_defaults(func=cmd_identity_claims_validate)
    p_claims_rewrite = claims_sub.add_parser("rewrite", help="produce a safe truthful rewrite")
    p_claims_rewrite.add_argument("--claim", default="", help="claim text to rewrite")
    p_claims_rewrite.add_argument("--claim-id", default="", help="registered claim ID to rewrite")
    p_claims_rewrite.add_argument("--claim-type", default="", help="claim type for ad-hoc rewrite")
    p_claims_rewrite.add_argument("--json", action="store_true")
    p_claims_rewrite.set_defaults(func=cmd_identity_claims_rewrite)

    # P1.4.11 External Doctrine Assimilation Registry
    p_identity_doctrine = identity_sub.add_parser(
        "doctrine", help="external doctrine assimilation registry (P1.4.11)"
    )
    doctrine_sub = p_identity_doctrine.add_subparsers(dest="doctrine_command", required=True)
    p_doctrine_list = doctrine_sub.add_parser("list", help="list registered doctrine inputs")
    p_doctrine_list.add_argument("--json", action="store_true")
    p_doctrine_list.set_defaults(func=cmd_identity_doctrine_list)
    p_doctrine_show = doctrine_sub.add_parser("show", help="show a doctrine input")
    p_doctrine_show.add_argument("doctrine_id", help="doctrine ID to show")
    p_doctrine_show.add_argument("--json", action="store_true")
    p_doctrine_show.set_defaults(func=cmd_identity_doctrine_show)
    p_doctrine_validate = doctrine_sub.add_parser("validate", help="validate doctrine registry")
    p_doctrine_validate.add_argument("--json", action="store_true")
    p_doctrine_validate.set_defaults(func=cmd_identity_doctrine_validate)
    p_doctrine_impact = doctrine_sub.add_parser("impact", help="show roadmap impact mapping")
    p_doctrine_impact.add_argument("doctrine_id", help="doctrine ID to map")
    p_doctrine_impact.add_argument("--json", action="store_true")
    p_doctrine_impact.set_defaults(func=cmd_identity_doctrine_impact)
    p_doctrine_claims = doctrine_sub.add_parser("claims", help="show claim boundaries")
    p_doctrine_claims.add_argument("doctrine_id", help="doctrine ID to inspect")
    p_doctrine_claims.add_argument("--json", action="store_true")
    p_doctrine_claims.set_defaults(func=cmd_identity_doctrine_claims)

    # P1.4.12 Raw Source + Canonical Hash Attestation
    p_identity_attestation = identity_sub.add_parser(
        "attestation", help="raw source + canonical hash attestation (P1.4.12)"
    )
    attestation_sub = p_identity_attestation.add_subparsers(
        dest="attestation_command", required=True
    )
    p_attestation_list = attestation_sub.add_parser("list", help="list source attestations")
    p_attestation_list.add_argument("--json", action="store_true")
    p_attestation_list.set_defaults(func=cmd_identity_attestation_list)
    p_attestation_show = attestation_sub.add_parser("show", help="show a source attestation")
    p_attestation_show.add_argument("source_id", help="source kind or record key to show")
    p_attestation_show.add_argument("--json", action="store_true")
    p_attestation_show.set_defaults(func=cmd_identity_attestation_show)
    p_attestation_validate = attestation_sub.add_parser("validate", help="validate source attestations")
    p_attestation_validate.add_argument("--json", action="store_true")
    p_attestation_validate.set_defaults(func=cmd_identity_attestation_validate)
    p_attestation_verify = attestation_sub.add_parser(
        "verify-bundle", help="verify identity source bundle attestations"
    )
    p_attestation_verify.add_argument("--json", action="store_true")
    p_attestation_verify.set_defaults(func=cmd_identity_attestation_verify_bundle)
    p_attestation_compare = attestation_sub.add_parser(
        "compare", help="compare raw file hash against canonical source attestation"
    )
    p_attestation_compare.add_argument("--raw-path", required=True, help="raw file path")
    p_attestation_compare.add_argument(
        "--canonical-kind", required=True, help="SourceKind value such as operator_contract"
    )
    p_attestation_compare.add_argument("--json", action="store_true")
    p_attestation_compare.set_defaults(func=cmd_identity_attestation_compare)

    # P1.4.13 Authority Delta Detector
    p_identity_authority_delta = identity_sub.add_parser(
        "authority-delta", help="detect authority-relevant deltas (P1.4.13)"
    )
    authority_delta_sub = p_identity_authority_delta.add_subparsers(
        dest="authority_delta_command", required=True
    )
    p_ad_compare = authority_delta_sub.add_parser(
        "compare", help="compare two canonical sources for authority deltas"
    )
    p_ad_compare.add_argument("--old", required=True, help="path to old canonical source (YAML/JSON)")
    p_ad_compare.add_argument("--new", required=True, help="path to new canonical source (YAML/JSON)")
    p_ad_compare.add_argument(
        "--source-kind", required=True,
        help="source kind (e.g. operator_contract, agent_identity_card_config, external_doctrine)"
    )
    p_ad_compare.add_argument("--json", action="store_true")
    p_ad_compare.set_defaults(func=cmd_identity_authority_delta_compare)

    # P1.4.14 Operator Consent Binding
    p_identity_consent = identity_sub.add_parser(
        "consent", help="operator consent binding (P1.4.14)"
    )
    consent_sub = p_identity_consent.add_subparsers(dest="consent_command", required=True)

    p_c_request = consent_sub.add_parser("request", help="build consent request from delta report")
    p_c_request.add_argument("--delta-report", required=True, help="path to authority delta report JSON")
    p_c_request.add_argument("--scope", default="DELTA_REPORT", help="consent scope")
    p_c_request.add_argument("--json", action="store_true")
    p_c_request.set_defaults(func=cmd_identity_consent_request)

    p_c_grant = consent_sub.add_parser("grant", help="grant operator consent")
    p_c_grant.add_argument("--request", required=True, help="path to consent request JSON")
    p_c_grant.add_argument("--operator-id", default="operator.local", help="operator identifier")
    p_c_grant.add_argument("--ack-risk", action="store_true", help="explicitly acknowledge risk for HIGH/CRITICAL deltas")
    p_c_grant.add_argument("--reason", default=None, help="reason for granting consent")
    p_c_grant.add_argument("--json", action="store_true")
    p_c_grant.set_defaults(func=cmd_identity_consent_grant)

    p_c_deny = consent_sub.add_parser("deny", help="deny a consent request")
    p_c_deny.add_argument("--request", required=True, help="path to consent request JSON")
    p_c_deny.add_argument("--operator-id", default="operator.local", help="operator identifier")
    p_c_deny.add_argument("--reason", default=None, help="reason for denial")
    p_c_deny.add_argument("--json", action="store_true")
    p_c_deny.set_defaults(func=cmd_identity_consent_deny)

    p_c_revoke = consent_sub.add_parser("revoke", help="revoke a granted consent record")
    p_c_revoke.add_argument("--record", required=True, help="path to consent record JSON")
    p_c_revoke.add_argument("--operator-id", default="operator.local", help="operator identifier")
    p_c_revoke.add_argument("--reason", default=None, help="reason for revocation")
    p_c_revoke.add_argument("--json", action="store_true")
    p_c_revoke.set_defaults(func=cmd_identity_consent_revoke)

    p_c_show = consent_sub.add_parser("show", help="show a consent record")
    p_c_show.add_argument("--record", required=True, help="path to consent record JSON")
    p_c_show.add_argument("--json", action="store_true")
    p_c_show.set_defaults(func=cmd_identity_consent_show)

    p_c_validate = consent_sub.add_parser("validate", help="validate consent binding against delta report")
    p_c_validate.add_argument("--record", required=True, help="path to consent record JSON")
    p_c_validate.add_argument("--delta-report", required=True, help="path to authority delta report JSON")
    p_c_validate.add_argument("--json", action="store_true")
    p_c_validate.set_defaults(func=cmd_identity_consent_validate)

    # P1.4.16 Identity Test Battery
    p_identity_test_battery = identity_sub.add_parser(
        "test-battery", help="identity test battery (P1.4.16)"
    )
    battery_sub = p_identity_test_battery.add_subparsers(dest="battery_command", required=True)

    p_b_run = battery_sub.add_parser("run", help="run the full identity test battery")
    p_b_run.add_argument("--include-adversarial", action="store_true", default=True)
    p_b_run.add_argument("--include-cli", action="store_true", default=True)
    p_b_run.add_argument("--json", action="store_true")
    p_b_run.set_defaults(func=cmd_identity_test_battery_run)

    p_b_list = battery_sub.add_parser("list", help="list all registered test cases")
    p_b_list.add_argument("--json", action="store_true")
    p_b_list.set_defaults(func=cmd_identity_test_battery_list)

    p_b_run_case = battery_sub.add_parser("run-case", help="run a single test case by ID")
    p_b_run_case.add_argument("--case-id", required=True, help="test case ID")
    p_b_run_case.add_argument("--json", action="store_true")
    p_b_run_case.set_defaults(func=cmd_identity_test_battery_run_case)

    # P1.4.17 Identity Lifecycle
    p_identity_lifecycle = identity_sub.add_parser(
        "lifecycle", help="identity lifecycle state machine (P1.4.17)"
    )
    lifecycle_sub = p_identity_lifecycle.add_subparsers(dest="lifecycle_command", required=True)

    p_l_show = lifecycle_sub.add_parser("show", help="show lifecycle state")
    p_l_show.add_argument("--agent-id", required=True, help="agent identifier")
    p_l_show.add_argument("--state", required=True, help="lifecycle state (e.g. CANDIDATE, ACTIVE)")
    p_l_show.add_argument("--json", action="store_true")
    p_l_show.set_defaults(func=cmd_identity_lifecycle_show)

    p_l_profile = lifecycle_sub.add_parser("profile", help="build lifecycle eligibility profile")
    p_l_profile.add_argument("--agent-id", required=True, help="agent identifier")
    p_l_profile.add_argument("--state", required=True, help="lifecycle state")
    p_l_profile.add_argument("--reason", default="", help="comma-separated restriction reason codes")
    p_l_profile.add_argument("--json", action="store_true")
    p_l_profile.set_defaults(func=cmd_identity_lifecycle_profile)

    p_l_validate = lifecycle_sub.add_parser("validate-transition", help="validate lifecycle transition")
    p_l_validate.add_argument("--agent-id", required=True)
    p_l_validate.add_argument("--old-state", required=True, help="current lifecycle state")
    p_l_validate.add_argument("--new-state", required=True, help="requested lifecycle state")
    p_l_validate.add_argument("--reason-code", required=True, help="reason code (e.g. EVALUATION_PASSED)")
    p_l_validate.add_argument("--reason", required=True, help="human-readable reason")
    p_l_validate.add_argument("--requested-by", default=None, help="who requested the transition")
    p_l_validate.add_argument("--evidence-ref", action="append", default=[], help="evidence reference (repeatable)")
    p_l_validate.add_argument("--test-battery-ref", action="append", default=[], help="test battery reference (repeatable)")
    p_l_validate.add_argument("--json", action="store_true")
    p_l_validate.set_defaults(func=cmd_identity_lifecycle_validate_transition)

    p_l_transitions = lifecycle_sub.add_parser("transitions", help="show transition policy")
    p_l_transitions.add_argument("--json", action="store_true")
    p_l_transitions.set_defaults(func=cmd_identity_lifecycle_transitions)

    p_l_recommend = lifecycle_sub.add_parser("recommend", help="recommend lifecycle state change")
    p_l_recommend.add_argument("--agent-id", required=True)
    p_l_recommend.add_argument("--current-state", required=True, help="current lifecycle state")
    p_l_recommend.add_argument("--battery-status", help="battery status (PASSED/FAILED/DEGRADED)")
    p_l_recommend.add_argument("--highest-failed-severity", help="highest failed severity")
    p_l_recommend.add_argument("--json", action="store_true")
    p_l_recommend.set_defaults(func=cmd_identity_lifecycle_recommend)

    # P1.4.18 Trust Evidence Linkage
    p_trust_evidence = identity_sub.add_parser(
        "trust-evidence", help="trust evidence linkage (P1.4.18)"
    )
    te_sub = p_trust_evidence.add_subparsers(dest="te_command", required=True)

    p_te_req = te_sub.add_parser("requirements", help="show evidence requirements for lifecycle state")
    p_te_req.add_argument("--lifecycle-state", required=True, help="e.g. ACTIVE, CANDIDATE")
    p_te_req.add_argument("--json", action="store_true")
    p_te_req.set_defaults(func=cmd_identity_trust_evidence_requirements)

    p_te_build = te_sub.add_parser("build", help="build trust evidence bundle")
    p_te_build.add_argument("--agent-id", required=True)
    p_te_build.add_argument("--lifecycle-state", required=True)
    p_te_build.add_argument("--evidence-ref", action="append", default=[], help="evidence reference (repeatable)")
    p_te_build.add_argument("--json", action="store_true")
    p_te_build.set_defaults(func=cmd_identity_trust_evidence_build)

    p_te_val = te_sub.add_parser("validate", help="validate a trust evidence bundle JSON")
    p_te_val.add_argument("--bundle", required=True, help="path to bundle JSON")
    p_te_val.add_argument("--json", action="store_true")
    p_te_val.set_defaults(func=cmd_identity_trust_evidence_validate)

    p_te_explain = te_sub.add_parser("explain", help="explain trust posture from bundle JSON")
    p_te_explain.add_argument("--bundle", required=True, help="path to bundle JSON")
    p_te_explain.add_argument("--json", action="store_true")
    p_te_explain.set_defaults(func=cmd_identity_trust_evidence_explain)

    # P1.4.19 seal-readiness
    p_seal = identity_sub.add_parser(
        "seal-readiness", help="P1.4 seal readiness summary (P1.4.19)"
    )
    p_seal.add_argument("--json", action="store_true")
    p_seal.set_defaults(func=cmd_identity_seal_readiness)

    # P1.4.20 p14-seal
    p_p14_seal = identity_sub.add_parser(
        "p14-seal", help="P1.4 exit seal (P1.4.20)"
    )
    p14_seal_sub = p_p14_seal.add_subparsers(dest="p14_seal_command", required=True)

    p_seal_run = p14_seal_sub.add_parser("run", help="run full P1.4 exit seal")
    p_seal_run.add_argument("--json", action="store_true")
    p_seal_run.set_defaults(func=cmd_identity_p14_seal_run)

    p_seal_list = p14_seal_sub.add_parser("list-checks", help="list all seal checks")
    p_seal_list.add_argument("--json", action="store_true")
    p_seal_list.set_defaults(func=cmd_identity_p14_seal_list_checks)

    p_seal_check = p14_seal_sub.add_parser("run-check", help="run a single seal check")
    p_seal_check.add_argument("--check-id", required=True, help="seal check ID")
    p_seal_check.add_argument("--json", action="store_true")
    p_seal_check.set_defaults(func=cmd_identity_p14_seal_run_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
