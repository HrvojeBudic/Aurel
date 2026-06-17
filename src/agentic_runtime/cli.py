"""
cli.py — Minimal CLI entrypoint (P0.11).

  python -m agentic_runtime.cli status
  python -m agentic_runtime.cli demo
  python -m agentic_runtime.cli verify
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_status(args: argparse.Namespace) -> int:
    from . import build_runtime
    from .status import format_status, runtime_status

    kernel = build_runtime()
    status = runtime_status(kernel)
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(format_status(status))
    return 0


def cmd_demo(_args: argparse.Namespace) -> int:
    from .demo import main
    main()
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    root = _repo_root()
    env = {**dict(__import__("os").environ), "PYTHONPATH": f"src{__import__('os').pathsep}."}
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if args.verbose:
        cmd = [sys.executable, "-m", "pytest", "-v"]
    print(f"running: {' '.join(cmd)}  (cwd={root})")
    proc = subprocess.run(cmd, cwd=root, env=env)
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
                        choices=["deterministic", "llm", "hybrid", "dry_run"])
    p_repo.add_argument("--provider", default="",
                        choices=["", "mock", "openai", "anthropic", "ollama"])
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
