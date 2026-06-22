"""CLI commands for P1.5 Evaluation Mirror foundation."""
from __future__ import annotations

import argparse
import json


def cmd_evaluation_foundation_status(args: argparse.Namespace) -> int:
    """Show P1.5.0 evaluation foundation status. Read-only."""
    from ..evaluation.evaluation_foundation import (
        P150_INVARIANTS,
        P150_NON_GOALS,
        build_p150_foundation_report,
        evaluation_foundation_report_to_dict,
    )

    docs_updated = (
        "agent/ROADMAP.md",
        "agent/STATE.md",
        "agent/ARCHITECTURE.md",
        "agent/DECISIONS.md",
        "agent/TESTS.md",
        "agent/REPORTS.md",
        "agent/ACTIVE_TASK.md",
    )
    docs_missing = (
        "AUREL_Roadmap_v3_2_FULL_0_20.md",
        "AUREL_ROADMAP.md",
        "docs/ROADMAP.md",
        "reports/ROADMAP_INDEX.md",
    )

    report = build_p150_foundation_report(
        docs_updated=docs_updated,
        docs_missing=docs_missing,
    )

    if args.json:
        payload = evaluation_foundation_report_to_dict(report)
        payload["invariants"] = list(P150_INVARIANTS)
        payload["non_goals"] = list(P150_NON_GOALS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.0 Evaluation Mirror Foundation: {report.status}")
        print(f"Roadmap alignment: {report.roadmap_alignment_status}")
        print(f"Next: {report.next_module}")
        print(f"\nInvariants: {len(P150_INVARIANTS)}")
        print(f"Non-goals: {len(P150_NON_GOALS)}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_foundation_scope(args: argparse.Namespace) -> int:
    """Show default evaluation scope for a domain. Read-only."""
    from ..evaluation.evaluation_foundation import (
        EvaluationDomain,
        default_criteria_for_domain,
        default_evaluation_scope_for_domain,
        evaluation_criterion_to_dict,
        evaluation_scope_to_dict,
    )

    try:
        domain = EvaluationDomain(args.domain)
    except ValueError:
        print(json.dumps({"error": f"Unknown domain: {args.domain}"}))
        return 1

    scope = default_evaluation_scope_for_domain(domain)
    criteria = default_criteria_for_domain(domain)

    if args.json:
        print(json.dumps({
            "scope": evaluation_scope_to_dict(scope),
            "criteria": [evaluation_criterion_to_dict(c) for c in criteria],
        }, indent=2))
    else:
        print(f"Domain: {domain.value}")
        print(f"Scope: {scope.scope_id}")
        print(f"Purpose: {scope.purpose}")
        print(f"Subject types: {', '.join(st.value for st in scope.subject_types)}")
        print("Non-goals:")
        for ng in scope.non_goals:
            print(f"  - {ng}")
    return 0


def cmd_evaluation_objects_status(args: argparse.Namespace) -> int:
    """Show P1.5.1 evaluation object model status. Read-only."""
    from ..evaluation.evaluation_objects import (
        P151_INVARIANTS,
        build_p151_object_model_report,
        evaluation_object_model_report_to_dict,
    )

    report = build_p151_object_model_report()
    if args.json:
        payload = evaluation_object_model_report_to_dict(report)
        payload["invariants"] = list(P151_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.1 Evaluation Object Model: {report.status}")
        print(f"Objects: {len(report.objects_added)}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_objects_examples(args: argparse.Namespace) -> int:
    """Show example evaluation result objects. Read-only."""
    from ..evaluation.evaluation_objects import (
        evaluation_criterion_result_to_dict,
        evaluation_result_to_dict,
        example_supported_criterion_result,
        example_supported_evaluation_result,
    )

    criterion = example_supported_criterion_result()
    result = example_supported_evaluation_result()
    if args.json:
        print(json.dumps({
            "criterion_result": evaluation_criterion_result_to_dict(criterion),
            "evaluation_result": evaluation_result_to_dict(result),
            "note": "PASS/SUPPORTED does not mean VERIFIED — evidence candidate only",
        }, indent=2))
    else:
        print(f"Criterion: {criterion.criterion_id} → {criterion.outcome.value}/{criterion.verdict.value}")
        print(f"Result: {result.result_id} → {result.outcome.value}/{result.verdict.value}")
        print("Note: PASS/SUPPORTED does not mean VERIFIED")
    return 0


def cmd_evaluation_capability_evidence_status(args: argparse.Namespace) -> int:
    """Show P1.5.2 capability evidence status. Read-only."""
    from ..evaluation.capability_evidence import (
        P152_INVARIANTS,
        build_p152_capability_evidence_report,
        capability_evidence_record_report_to_dict,
    )

    report = build_p152_capability_evidence_report()
    if args.json:
        payload = capability_evidence_record_report_to_dict(report)
        payload["invariants"] = list(P152_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.2 Capability Evidence Record: {report.status}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_capability_evidence_examples(args: argparse.Namespace) -> int:
    """Show example capability evidence records. Read-only."""
    from ..evaluation.capability_evidence import (
        capability_evidence_record_to_dict,
        example_usable_evidence_from_result,
    )

    record = example_usable_evidence_from_result()
    if args.json:
        print(json.dumps({
            "capability_evidence_record": capability_evidence_record_to_dict(record),
            "note": "USABLE is not VERIFIED — evidence for later claim binding only",
        }, indent=2))
    else:
        print(f"Evidence: {record.evidence_id} → {record.status.value}/{record.strength.value}")
        print("Note: USABLE is not VERIFIED")
    return 0


def cmd_evaluation_subjects_status(args: argparse.Namespace) -> int:
    """Show P1.5.3 evaluation subject registry status. Read-only."""
    from ..evaluation.evaluation_subject_registry import (
        P153_INVARIANTS,
        build_p153_subject_registry_report,
        evaluation_subject_registry_report_to_dict,
    )

    report = build_p153_subject_registry_report()
    if args.json:
        payload = evaluation_subject_registry_report_to_dict(report)
        payload["invariants"] = list(P153_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.3 Evaluation Subject Registry: {report.status}")
        print(f"Sparse cognition readiness: {report.sparse_cognition_readiness}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_subjects_examples(args: argparse.Namespace) -> int:
    """Show example evaluation subject registry entries. Read-only."""
    from ..evaluation.evaluation_subject_registry import (
        evaluation_subject_registry_entry_to_dict,
        evaluation_subject_registry_to_dict,
        example_registered_core_subject,
        example_registered_sparse_context_subject,
        example_subject_registry,
    )

    core_entry = example_registered_core_subject()
    sc_entry = example_registered_sparse_context_subject()
    registry = example_subject_registry()

    if args.json:
        print(json.dumps({
            "core_subject": evaluation_subject_registry_entry_to_dict(core_entry),
            "sparse_context_subject": evaluation_subject_registry_entry_to_dict(sc_entry),
            "example_registry": evaluation_subject_registry_to_dict(registry),
            "note": (
                "Subject registration does not verify capability. "
                "Sparse context subjects are future-ready — Sparse Context Compiler not implemented."
            ),
        }, indent=2))
    else:
        print(f"Core subject: {core_entry.entry_id} → {core_entry.status.value} ({core_entry.origin.value})")
        print(f"Sparse context subject: {sc_entry.entry_id} → {sc_entry.status.value} ({sc_entry.origin.value})")
        print(f"Registry: {registry.registry_id} ({len(registry.entries)} entries)")
        print("Note: Registration does not verify capability. Sparse Context Compiler not implemented.")
    return 0


def cmd_evaluation_criteria_status(args: argparse.Namespace) -> int:
    """Show P1.5.4 evaluation criteria schema status. Read-only."""
    from ..evaluation.evaluation_criteria_schema import (
        P154_INVARIANTS,
        build_p154_criteria_schema_report,
        criteria_schema_report_to_dict,
    )

    report = build_p154_criteria_schema_report(sparse_criteria_ready=True)
    if args.json:
        payload = criteria_schema_report_to_dict(report)
        payload["invariants"] = list(P154_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.4 Evaluation Criteria Schema: {report.status}")
        print(f"Sparse criteria ready: {report.sparse_criteria_ready}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_criteria_examples(args: argparse.Namespace) -> int:
    """Show example criteria schemas. Read-only."""
    from ..evaluation.evaluation_criteria_schema import (
        criteria_schema_to_dict,
        example_criteria_schema,
        example_sparse_criteria_schema,
    )

    core_schema = example_criteria_schema()
    sparse_schema = example_sparse_criteria_schema()

    if args.json:
        print(json.dumps({
            "core_criteria_schema": criteria_schema_to_dict(core_schema),
            "sparse_criteria_schema": criteria_schema_to_dict(sparse_schema),
            "note": (
                "Criteria schemas do not run evaluation, verify capability, or implement "
                "Sparse Context Compiler. SSA/subquadratic model attention NOT implemented."
            ),
        }, indent=2))
    else:
        print(f"Core schema: {core_schema.schema_id} ({len(core_schema.criteria)} criteria)")
        print(f"Sparse schema: {sparse_schema.schema_id} ({len(sparse_schema.criteria)} criteria)")
        print("Note: Criteria schemas do not run evaluation. Sparse Context Compiler not implemented.")
    return 0


def cmd_evaluation_runs_status(args: argparse.Namespace) -> int:
    """Show P1.5.5 evaluation run envelope status. Read-only."""
    from ..evaluation.evaluation_run_envelope import (
        P155_INVARIANTS,
        build_p155_run_envelope_report,
        run_envelope_report_to_dict,
    )

    report = build_p155_run_envelope_report()
    if args.json:
        payload = run_envelope_report_to_dict(report)
        payload["invariants"] = list(P155_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.5 Evaluation Run Envelope: {report.status}")
        print(f"Sparse run readiness: {report.sparse_run_readiness}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_runs_examples(args: argparse.Namespace) -> int:
    """Show example evaluation run envelopes. Read-only."""
    from ..evaluation.evaluation_run_envelope import (
        example_ready_run_envelope,
        example_sparse_ready_run_envelope,
        governed_evaluation_run_envelope_to_dict,
    )

    ready = example_ready_run_envelope()
    sparse = example_sparse_ready_run_envelope()

    if args.json:
        print(json.dumps({
            "ready_envelope": governed_evaluation_run_envelope_to_dict(ready),
            "sparse_ready_envelope": governed_evaluation_run_envelope_to_dict(sparse),
            "note": (
                "Run envelopes do not execute evaluation, verify capability, "
                "create EvaluationResult, call LLMs/tools, or implement "
                "Sparse Context Compiler. SSA/subquadratic model attention NOT implemented."
            ),
        }, indent=2))
    else:
        print(f"Ready envelope: {ready.run_id} → {ready.status.value}")
        print(f"Sparse ready envelope: {sparse.run_id} → {sparse.status.value}")
        print("Note: Run envelopes do not execute evaluation. Sparse Context Compiler not implemented.")
    return 0


def cmd_evaluation_classify_status(args: argparse.Namespace) -> int:
    """Show P1.5.6 result classification engine status. Read-only."""
    from ..evaluation.result_classification import (
        P156_INVARIANTS,
        build_p156_result_classification_report,
        result_classification_report_to_dict,
    )

    report = build_p156_result_classification_report(
        sparse_classification_ready=True,
    )
    if args.json:
        payload = result_classification_report_to_dict(report)
        payload["invariants"] = list(P156_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.6 Result Classification Engine: {report.status}")
        print(f"Sparse classification readiness: {report.sparse_classification_ready}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_classify_examples(args: argparse.Namespace) -> int:
    """Show example classification objects. Read-only."""
    from ..evaluation.result_classification import (
        build_default_result_classification_policy,
        classify_criterion_observation,
        criterion_classification_decision_to_dict,
        criterion_decision_to_result,
        evaluation_criterion_result_to_dict,
        evaluation_observation_to_dict,
        example_observation,
        example_sparse_observation,
        result_classification_policy_to_dict,
    )
    from ..evaluation.evaluation_criteria_schema import (
        example_criteria_schema,
    )

    policy = build_default_result_classification_policy()
    obs = example_observation()
    sparse_obs = example_sparse_observation()

    schema = example_criteria_schema()
    criterion = schema.criteria[0] if schema.criteria else None

    from ..evaluation.result_classification import CriterionClassificationInput

    if criterion is not None:
        cin = CriterionClassificationInput(
            run_id="example_run",
            criterion=criterion,
            observation=obs,
            required=True,
            blocking=False,
        )
        decision = classify_criterion_observation(classification_input=cin, policy=policy)
        crit_result = criterion_decision_to_result(decision)
    else:
        decision = None
        crit_result = None

    if args.json:
        result = {
            "policy": result_classification_policy_to_dict(policy),
            "observation": evaluation_observation_to_dict(obs),
            "sparse_observation": evaluation_observation_to_dict(sparse_obs),
        }
        if decision is not None:
            result["criterion_decision"] = criterion_classification_decision_to_dict(decision)
        if crit_result is not None:
            result["criterion_result"] = evaluation_criterion_result_to_dict(crit_result)
        result["note"] = (
            "Classification translates supplied observations into evaluation semantics. "
            "It does NOT execute evaluation, call LLMs/tools, verify capability, "
            "bind evidence to claims, or implement Sparse Context Compiler."
        )
        print(json.dumps(result, indent=2))
    else:
        print(f"Policy: {policy.policy_id}")
        print(f"  require_evidence: {policy.require_evidence_for_supported}")
        print(f"  block_on_conflicted: {policy.block_on_conflicted_evidence}")
        print(f"  allow_unknown_pass: {policy.allow_unknown_observation_to_pass}")
        if decision is not None:
            print(f"Criterion decision: {decision.criterion_id} → {decision.outcome.value}/{decision.verdict.value}")
        print("Note: Classification is not verification. Sparse Context Compiler NOT implemented.")
    return 0


def cmd_evaluation_binding_status(args: argparse.Namespace) -> int:
    """Show P1.5.7 evidence-to-claim binding status. Read-only."""
    from ..evaluation.evidence_claim_binding import (
        P157_INVARIANTS,
        build_p157_evidence_claim_binding_report,
        evidence_claim_binding_report_to_dict,
    )

    report = build_p157_evidence_claim_binding_report(
        sparse_binding_ready=True,
    )
    if args.json:
        payload = evidence_claim_binding_report_to_dict(report)
        payload["invariants"] = list(P157_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.7 Evidence-to-Claim Binding: {report.status}")
        print(f"Sparse binding readiness: {report.sparse_binding_ready}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_binding_examples(args: argparse.Namespace) -> int:
    """Show example evidence-to-claim bindings. Read-only."""
    from ..evaluation.evidence_claim_binding import (
        bind_evidence_to_claim,
        build_default_evidence_claim_binding_policy,
        evidence_claim_binding_policy_to_dict,
        evidence_claim_binding_to_dict,
        example_sparse_evidence_record,
        example_usable_evidence_record,
    )

    policy = build_default_evidence_claim_binding_policy()
    evidence = example_usable_evidence_record()
    sparse_evidence = example_sparse_evidence_record()

    binding = bind_evidence_to_claim(
        binding_id="binding_example_001",
        claim_id="claim_example_001",
        evidence=evidence,
        policy=policy,
    )
    sparse_binding = bind_evidence_to_claim(
        binding_id="binding_sparse_example",
        claim_id="claim_sparse_context_001",
        evidence=sparse_evidence,
        policy=policy,
    )

    if args.json:
        print(json.dumps({
            "policy": evidence_claim_binding_policy_to_dict(policy),
            "binding": evidence_claim_binding_to_dict(binding),
            "sparse_binding": evidence_claim_binding_to_dict(sparse_binding),
            "note": (
                "Binding models claim impact, does NOT verify capability. "
                "No VERIFIED status. No Sparse Context Compiler implemented."
            ),
        }, indent=2))
    else:
        print(f"Policy: {policy.policy_id}")
        print(f"  require_usable: {policy.require_usable_evidence_for_support}")
        print(f"  block_conflicted: {policy.block_conflicted_evidence}")
        print(f"  block_revoked_invalid: {policy.block_revoked_or_invalid_evidence}")
        print(f"  allow_stale_support: {policy.allow_stale_evidence_to_support}")
        print(f"Binding: {binding.binding_id} → {binding.relationship.value}")
        print(f"  support={binding.support_level.value}, conflict={binding.conflict_level.value}")
        print(f"Sparse binding: {sparse_binding.binding_id} → {sparse_binding.relationship.value}")
        print("Note: Binding is not verification. No VERIFIED status. No Sparse Context Compiler.")
    return 0



def cmd_evaluation_hygiene_status(args: argparse.Namespace) -> int:
    """Show P1.5.8 benchmark hygiene status. Read-only."""
    from ..evaluation.benchmark_hygiene import (
        P158_INVARIANTS,
        build_p158_benchmark_hygiene_report,
        benchmark_hygiene_report_to_dict,
    )

    report = build_p158_benchmark_hygiene_report(
        assessments_created=1,
        decisions_created=1,
        sparse_hygiene_ready=True,
    )
    if args.json:
        payload = benchmark_hygiene_report_to_dict(report)
        payload["invariants"] = list(P158_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.8 Benchmark Hygiene Guard: {report.status}")
        print(f"Sparse hygiene readiness: {report.sparse_hygiene_ready}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_hygiene_examples(args: argparse.Namespace) -> int:
    """Show example benchmark hygiene objects. Read-only."""
    from ..evaluation.benchmark_hygiene import (
        BenchmarkRepresentativeness,
        assess_benchmark_hygiene,
        benchmark_fixture_boundary_to_dict,
        benchmark_hygiene_assessment_to_dict,
        benchmark_hygiene_decision_to_dict,
        benchmark_hygiene_policy_to_dict,
        build_default_benchmark_hygiene_policy,
        example_clean_benchmark_fixture_boundary,
        example_leaky_benchmark_fixture_boundary,
        resolve_hygiene_decision,
    )

    policy = build_default_benchmark_hygiene_policy()
    clean_boundary = example_clean_benchmark_fixture_boundary()
    leaky_boundary = example_leaky_benchmark_fixture_boundary()
    clean_assessment = assess_benchmark_hygiene(
        assessment_id="hygiene_clean_example",
        boundary=clean_boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        policy=policy,
    )
    leaky_assessment = assess_benchmark_hygiene(
        assessment_id="hygiene_leaky_example",
        boundary=leaky_boundary,
        representativeness=BenchmarkRepresentativeness.REPRESENTATIVE,
        policy=policy,
    )
    clean_decision = resolve_hygiene_decision(
        decision_id="hygiene_decision_clean_example",
        assessment=clean_assessment,
        policy=policy,
    )
    leaky_decision = resolve_hygiene_decision(
        decision_id="hygiene_decision_leaky_example",
        assessment=leaky_assessment,
        policy=policy,
    )

    if args.json:
        print(json.dumps({
            "policy": benchmark_hygiene_policy_to_dict(policy),
            "clean_boundary": benchmark_fixture_boundary_to_dict(clean_boundary),
            "clean_assessment": benchmark_hygiene_assessment_to_dict(clean_assessment),
            "clean_decision": benchmark_hygiene_decision_to_dict(clean_decision),
            "leaky_boundary": benchmark_fixture_boundary_to_dict(leaky_boundary),
            "leaky_assessment": benchmark_hygiene_assessment_to_dict(leaky_assessment),
            "leaky_decision": benchmark_hygiene_decision_to_dict(leaky_decision),
            "note": (
                "Hygiene assesses benchmark/context trustworthiness and may downgrade evidence impact. "
                "It does NOT run benchmarks, execute evaluations, verify capability, mutate claims, "
                "call LLMs/tools, or implement Sparse Context Compiler."
            ),
        }, indent=2))
    else:
        print(f"Policy: {policy.policy_id}")
        print(f"Clean fixture: {clean_assessment.hygiene_status.value} → max {clean_decision.max_allowed_support_level.value}")
        print(f"Leaky fixture: {leaky_assessment.hygiene_status.value} → {leaky_decision.recommended_binding_relationship.value}")
        print("Note: Hygiene is not verification. No benchmark execution. No Sparse Context Compiler.")
    return 0


def cmd_evaluation_adversarial_status(args: argparse.Namespace) -> int:
    """Show P1.5.9 adversarial evaluation case status. Read-only."""
    from ..evaluation.adversarial_cases import (
        P159_INVARIANTS,
        adversarial_case_report_to_dict,
        build_default_adversarial_case_set,
        build_p159_adversarial_case_report,
    )

    cases = build_default_adversarial_case_set()
    sparse_ready = any(c.sparse_context_required for c in cases)
    report = build_p159_adversarial_case_report(
        cases_created=len(cases),
        cases_registered=len(cases),
        sparse_cases_ready=sparse_ready,
    )
    if args.json:
        payload = adversarial_case_report_to_dict(report)
        payload["invariants"] = list(P159_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.9 Adversarial Evaluation Cases: {report.status}")
        print(f"Sparse cases ready: {report.sparse_cases_ready}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_adversarial_examples(args: argparse.Namespace) -> int:
    """Show example adversarial evaluation cases. Read-only."""
    from ..evaluation.adversarial_cases import (
        AdversarialCaseRegistry,
        AdversarialCaseType,
        adversarial_case_registry_to_dict,
        build_default_adversarial_case_registry,
        list_adversarial_cases,
    )

    registry = build_default_adversarial_case_registry()
    sparse_cases = list_adversarial_cases(
        registry,
        case_type=AdversarialCaseType.SPARSE_CONTEXT_OMISSION_TRAP,
    )
    contradiction_cases = list_adversarial_cases(
        registry,
        case_type=AdversarialCaseType.CONTRADICTION_TRAP,
    )

    if args.json:
        print(json.dumps({
            "registry": adversarial_case_registry_to_dict(registry),
            "sparse_example": adversarial_case_registry_to_dict(
                AdversarialCaseRegistry(
                    registry_id="adv_sparse_examples",
                    cases=sparse_cases,
                    warnings=registry.warnings,
                    blockers=registry.blockers,
                    summary="Sparse trap examples",
                )
            ),
            "contradiction_example": adversarial_case_registry_to_dict(
                AdversarialCaseRegistry(
                    registry_id="adv_contradiction_examples",
                    cases=contradiction_cases,
                    warnings=registry.warnings,
                    blockers=registry.blockers,
                    summary="Contradiction trap examples",
                )
            ),
            "note": (
                "Adversarial cases are schema-only evaluation fixtures. "
                "They do NOT execute cases, run benchmarks, create EvaluationResult, "
                "verify capability, mutate claims, call LLMs/tools, or implement Sparse Context Compiler."
            ),
        }, indent=2))
    else:
        print(f"Registry: {registry.registry_id} ({len(registry.cases)} cases)")
        print(f"Sparse omission traps: {len(sparse_cases)}")
        print(f"Contradiction traps: {len(contradiction_cases)}")
        print("Note: Adversarial cases are definitions only. No execution. No verification.")
    return 0


def cmd_evaluation_baseline_status(args: argparse.Namespace) -> int:
    """Show P1.5.10 baseline comparison status. Read-only."""
    from ..evaluation.baseline_comparison import (
        P1510_INVARIANTS,
        baseline_comparison_report_to_dict,
        build_p1510_baseline_comparison_report,
    )

    report = build_p1510_baseline_comparison_report(
        comparisons_created=1,
        baseline_refs_created=2,
        sparse_comparison_ready=True,
    )
    if args.json:
        payload = baseline_comparison_report_to_dict(report)
        payload["invariants"] = list(P1510_INVARIANTS)
        print(json.dumps(payload, indent=2))
    else:
        print(f"P1.5.10 Baseline Comparison Model: {report.status}")
        print(f"Sparse comparison ready: {report.sparse_comparison_ready}")
        print(f"Next: {report.next_module}")
    return 0 if report.status != "BLOCKED" else 1


def cmd_evaluation_baseline_examples(args: argparse.Namespace) -> int:
    """Show example baseline comparison objects. Read-only."""
    from ..evaluation.baseline_comparison import (
        ComparisonDimension,
        baseline_comparison_decision_to_dict,
        baseline_comparison_policy_to_dict,
        baseline_reference_to_dict,
        build_default_baseline_comparison_policy,
        compare_adversarial_coverage,
        compare_evaluation_results,
        example_active_baseline_reference,
        example_current_baseline_reference,
    )
    from ..evaluation.evaluation_objects import example_supported_evaluation_result

    policy = build_default_baseline_comparison_policy()
    baseline = example_active_baseline_reference()
    current = example_current_baseline_reference()
    baseline_result = example_supported_evaluation_result()
    current_result = example_supported_evaluation_result()

    result_decision = compare_evaluation_results(
        comparison_id="baseline_example_result_cmp",
        baseline=baseline,
        current=current,
        baseline_result=baseline_result,
        current_result=current_result,
        dimensions=(
            ComparisonDimension.OUTCOME,
            ComparisonDimension.VERDICT,
            ComparisonDimension.EVIDENCE_QUALITY,
        ),
        policy=policy,
    )
    adversarial_decision = compare_adversarial_coverage(
        comparison_id="baseline_example_adv_cmp",
        baseline=baseline,
        current=current,
        baseline_case_refs=baseline.adversarial_case_refs,
        current_case_refs=current.adversarial_case_refs,
        policy=policy,
    )

    if args.json:
        print(json.dumps({
            "policy": baseline_comparison_policy_to_dict(policy),
            "baseline": baseline_reference_to_dict(baseline),
            "current": baseline_reference_to_dict(current),
            "result_comparison": baseline_comparison_decision_to_dict(result_decision),
            "adversarial_coverage_comparison": baseline_comparison_decision_to_dict(adversarial_decision),
            "note": (
                "Baseline comparison is categorical metadata comparison only. "
                "It does NOT run evaluations, benchmarks, or adversarial cases, "
                "create EvaluationResult or CapabilityEvidenceRecord, verify capability, "
                "mutate claims, use numeric scoring, call LLMs/tools, or implement Sparse Context Compiler."
            ),
        }, indent=2))
    else:
        print(f"Policy: {policy.policy_id}")
        print(f"Result comparison: {result_decision.signal.value} ({result_decision.confidence.value})")
        print(f"Adversarial coverage: {adversarial_decision.signal.value}")
        print("Note: Comparison is not verification. No numeric scoring.")
    return 0
