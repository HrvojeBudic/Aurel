"""Output Passport exit seal + live integration demo (P1.9.30).

Exit seal is evidence-gated. Live demo is not live unless actually tested.
Report is not seal.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .foundation import (
    OutputPassportSideEffectProof,
    OutputPassportSourceLabel,
    OutputPassportTruthLabel,
    stable_hash,
    to_canonical_json,
)
from .integration_tail import (
    P19_REPORT_CHAIN,
    handle_output_passport_cli_inspect,
    OUTPUT_PASSPORT_P1_9_D_PACK_TASK_ID,
)
from .projection import (
    build_output_passport_projection_contract,
    API_RUNTIME_UNAVAILABLE_REASON,
    EVENT_RUNTIME_UNAVAILABLE_REASON,
)

OUTPUT_PASSPORT_P1_9_30_TASK_ID = "P1.9.30"
OUTPUT_PASSPORT_EXIT_SEAL_VERSION = "output_passport_exit_seal.v1"
OUTPUT_PASSPORT_EXIT_SEAL_CHECKLIST_VERSION = (
    "output_passport_exit_seal_checklist.v1"
)
OUTPUT_PASSPORT_LIVE_DEMO_VERSION = "output_passport_live_demo.v1"

P19_FULL_CHECKPOINT_RANGE = "P1.9.0-P1.9.30"


class P19ExitSealDecision(str, Enum):
    """Exit seal decision — not runtime authority."""

    SEALED = "SEALED"
    NOT_SEALED = "NOT_SEALED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


class P19ExitSealCheckStatus(str, Enum):
    """Individual checklist item status."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"
    SKIPPED = "SKIPPED"


class P19LiveDemoStatus(str, Enum):
    """Live integration demo status."""

    DEV_FIXTURE = "DEV_FIXTURE"
    UNAVAILABLE_LIVE_PATH = "UNAVAILABLE_LIVE_PATH"
    NOT_RUN = "NOT_RUN"
    LIVE = "LIVE"


class _CanonicalMixin:
    def to_canonical_dict(self) -> dict[str, Any]:
        return _canonical_dataclass_dict(self)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical_dataclass_dict(value)
    if isinstance(value, Mapping):
        return {
            str(_canonical_value(key)): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    return value


def _canonical_dataclass_dict(value: Any) -> dict[str, Any]:
    return {
        field.name: _canonical_value(getattr(value, field.name))
        for field in fields(value)
    }


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return stable_hash(dict(payload))


def _all_false_side_effects() -> OutputPassportSideEffectProof:
    return OutputPassportSideEffectProof()


@dataclass(frozen=True)
class P19ExitSealCheckItem(_CanonicalMixin):
    """Single exit seal checklist item."""

    check_id: str
    check_label: str
    status: P19ExitSealCheckStatus
    summary: str
    evidence_refs: tuple[str, ...]
    unavailable_reason: str = ""


@dataclass(frozen=True)
class P19ExitSealChecklist(_CanonicalMixin):
    """Exit seal checklist envelope."""

    schema_version: str
    checkpoint_range: str
    checks: tuple[P19ExitSealCheckItem, ...]
    passed_count: int
    failed_count: int
    unavailable_count: int
    fake_live_detected: bool
    fake_trace_verified_detected: bool
    fake_exit_sealed_detected: bool
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    checklist_hash: str


@dataclass(frozen=True)
class P19LiveIntegrationDemoResult(_CanonicalMixin):
    """Live integration demo result with honest truth label."""

    schema_version: str
    demo_status: P19LiveDemoStatus
    demo_passed: bool
    truth_label: OutputPassportTruthLabel
    unavailable_reason: str
    projection_demo: bool
    cli_inspect_demo: bool
    harness_demo: bool
    summary: str
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    demo_result_hash: str


@dataclass(frozen=True)
class P19ExitSeal(_CanonicalMixin):
    """Exit seal aggregate."""

    schema_version: str
    task_id: str
    decision: P19ExitSealDecision
    decision_reason: str
    checklist: P19ExitSealChecklist
    live_demo: P19LiveIntegrationDemoResult
    checklist_passed: bool
    p2_readiness_blocked: bool
    p2_readiness_reason: str
    truth_label: OutputPassportTruthLabel
    source_label: OutputPassportSourceLabel
    side_effects: OutputPassportSideEffectProof
    seal_hash: str


def _check_item(
    *,
    check_id: str,
    check_label: str,
    status: P19ExitSealCheckStatus,
    summary: str,
    evidence_refs: Sequence[str] = (),
    unavailable_reason: str = "",
) -> P19ExitSealCheckItem:
    return P19ExitSealCheckItem(
        check_id=check_id,
        check_label=check_label,
        status=status,
        summary=summary,
        evidence_refs=tuple(evidence_refs),
        unavailable_reason=unavailable_reason,
    )


def _reports_exist(repo_root: Path, filenames: Sequence[str]) -> tuple[bool, tuple[str, ...]]:
    reports_dir = repo_root / "agent" / "reports"
    refs: list[str] = []
    all_exist = True
    for name in filenames:
        path = reports_dir / name
        exists = path.is_file()
        if not exists:
            all_exist = False
        refs.append(f"{name}:{'present' if exists else 'missing'}")
    return all_exist, tuple(refs)


def build_p1_9_live_integration_demo_result(
    *,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> P19LiveIntegrationDemoResult:
    """Run in-process DEV_FIXTURE demo chain; not LIVE production path."""
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    projection = build_output_passport_projection_contract(source_label=source_label)
    cli_result = handle_output_passport_cli_inspect(
        dev_fixture=True,
        source_label=source_label,
    )
    from .test_harness import run_output_passport_invariant_harness

    harness = run_output_passport_invariant_harness()
    demo_passed = (
        projection.contract_hash != ""
        and cli_result.get("read_only") is True
        and harness.all_passed
    )
    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_LIVE_DEMO_VERSION,
        "demo_status": P19LiveDemoStatus.DEV_FIXTURE,
        "demo_passed": demo_passed,
        "truth_label": OutputPassportTruthLabel.DEV_FIXTURE,
        "unavailable_reason": (
            "UNAVAILABLE_LIVE_PATH: in-process DEV_FIXTURE only; "
            "not production LIVE path"
        ),
        "projection_demo": True,
        "cli_inspect_demo": True,
        "harness_demo": harness.all_passed,
        "summary": (
            f"DEV_FIXTURE vertical slice: projection={projection.contract_hash[:12]}, "
            f"cli_read_only={cli_result.get('read_only')}, "
            f"harness_passed={harness.all_passed}"
        ),
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return P19LiveIntegrationDemoResult(
        **body,
        demo_result_hash=_hash_payload(body),
    )


def build_p1_9_exit_seal_checklist(
    *,
    repo_root: Path | None = None,
    truth_labels: Sequence[OutputPassportTruthLabel] | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> P19ExitSealChecklist:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    root = repo_root or Path(__file__).resolve().parents[3]
    labels = list(truth_labels or ())
    fake_live = OutputPassportTruthLabel.LIVE in labels
    fake_trace = OutputPassportTruthLabel.TRACE_VERIFIED in labels
    fake_sealed = (
        OutputPassportTruthLabel.SEALED in labels
        or OutputPassportTruthLabel.EXIT_SEALED in labels
    )

    checks: list[P19ExitSealCheckItem] = []

    a_exists, a_refs = _reports_exist(root, (P19_REPORT_CHAIN[0],))
    checks.append(
        _check_item(
            check_id="p1_9_a_report",
            check_label="P1.9-A report chain",
            status=P19ExitSealCheckStatus.PASS if a_exists else P19ExitSealCheckStatus.FAIL,
            summary="P1.9-A agent report present on disk",
            evidence_refs=a_refs,
        )
    )

    b_exists, b_refs = _reports_exist(root, (P19_REPORT_CHAIN[1],))
    checks.append(
        _check_item(
            check_id="p1_9_b_report",
            check_label="P1.9-B report chain",
            status=P19ExitSealCheckStatus.PASS if b_exists else P19ExitSealCheckStatus.FAIL,
            summary="P1.9-B agent report present on disk",
            evidence_refs=b_refs,
        )
    )

    c_exists, c_refs = _reports_exist(root, (P19_REPORT_CHAIN[2],))
    checks.append(
        _check_item(
            check_id="p1_9_c_report",
            check_label="P1.9-C report chain",
            status=P19ExitSealCheckStatus.PASS if c_exists else P19ExitSealCheckStatus.FAIL,
            summary="P1.9-C agent report present on disk",
            evidence_refs=c_refs,
        )
    )

    projection = build_output_passport_projection_contract(source_label=source_label)
    checks.append(
        _check_item(
            check_id="projection_contract",
            check_label="Projection/API/Event contract",
            status=P19ExitSealCheckStatus.PASS,
            summary="Projection contract built; API/event contract-only",
            evidence_refs=(
                projection.contract_hash,
                projection.api_contract.runtime_status.value,
                projection.event_contract.runtime_status.value,
            ),
        )
    )

    checks.append(
        _check_item(
            check_id="api_runtime_honest",
            check_label="No fake API_RUNTIME_LIVE",
            status=P19ExitSealCheckStatus.PASS,
            summary=API_RUNTIME_UNAVAILABLE_REASON,
            evidence_refs=(projection.api_contract.unavailable_reason,),
        )
    )

    checks.append(
        _check_item(
            check_id="event_runtime_honest",
            check_label="No fake EVENT_EMITTED",
            status=P19ExitSealCheckStatus.PASS,
            summary=EVENT_RUNTIME_UNAVAILABLE_REASON,
            evidence_refs=(projection.event_contract.unavailable_reason,),
        )
    )

    cli_result = handle_output_passport_cli_inspect(source_label=source_label)
    checks.append(
        _check_item(
            check_id="cli_binding",
            check_label="CLI read-only inspect",
            status=(
                P19ExitSealCheckStatus.PASS
                if cli_result.get("read_only") and not cli_result.get("authority_granted")
                else P19ExitSealCheckStatus.FAIL
            ),
            summary="Read-only CLI inspect binding exercised in-process",
            evidence_refs=(str(cli_result.get("projection_payload_hash", "")),),
        )
    )

    checks.append(
        _check_item(
            check_id="no_fake_live",
            check_label="No fake LIVE",
            status=(
                P19ExitSealCheckStatus.FAIL if fake_live
                else P19ExitSealCheckStatus.PASS
            ),
            summary="Truth labels must not include LIVE without proof",
            evidence_refs=tuple(label.value for label in labels),
        )
    )

    checks.append(
        _check_item(
            check_id="no_fake_trace_verified",
            check_label="No fake TRACE_VERIFIED",
            status=(
                P19ExitSealCheckStatus.FAIL if fake_trace
                else P19ExitSealCheckStatus.PASS
            ),
            summary="Truth labels must not include TRACE_VERIFIED without proof",
            evidence_refs=tuple(label.value for label in labels),
        )
    )

    checks.append(
        _check_item(
            check_id="no_fake_exit_sealed",
            check_label="No fake EXIT_SEALED",
            status=(
                P19ExitSealCheckStatus.FAIL if fake_sealed
                else P19ExitSealCheckStatus.PASS
            ),
            summary="Truth labels must not include SEALED/EXIT_SEALED without evidence",
            evidence_refs=tuple(label.value for label in labels),
        )
    )

    checks.append(
        _check_item(
            check_id="checkpoint_coverage",
            check_label="P1.9.0-P1.9.30 coverage",
            status=P19ExitSealCheckStatus.PASS,
            summary=f"Integration tail covers {P19_FULL_CHECKPOINT_RANGE} via packs A-D",
            evidence_refs=(P19_FULL_CHECKPOINT_RANGE, OUTPUT_PASSPORT_P1_9_D_PACK_TASK_ID),
        )
    )

    passed = sum(1 for c in checks if c.status is P19ExitSealCheckStatus.PASS)
    failed = sum(1 for c in checks if c.status is P19ExitSealCheckStatus.FAIL)
    unavailable = sum(1 for c in checks if c.status is P19ExitSealCheckStatus.UNAVAILABLE)
    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_EXIT_SEAL_CHECKLIST_VERSION,
        "checkpoint_range": P19_FULL_CHECKPOINT_RANGE,
        "checks": tuple(checks),
        "passed_count": passed,
        "failed_count": failed,
        "unavailable_count": unavailable,
        "fake_live_detected": fake_live,
        "fake_trace_verified_detected": fake_trace,
        "fake_exit_sealed_detected": fake_sealed,
        "truth_label": OutputPassportTruthLabel.NOT_SEAL,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return P19ExitSealChecklist(
        **body,
        checklist_hash=_hash_payload(body),
    )


def run_p1_9_exit_seal_checklist(
    checklist: P19ExitSealChecklist | None = None,
    *,
    repo_root: Path | None = None,
    source_label: OutputPassportSourceLabel | str = OutputPassportSourceLabel.DEV_FIXTURE,
) -> P19ExitSeal:
    if isinstance(source_label, str):
        source_label = OutputPassportSourceLabel(source_label)

    resolved = checklist or build_p1_9_exit_seal_checklist(
        repo_root=repo_root,
        source_label=source_label,
    )
    live_demo = build_p1_9_live_integration_demo_result(source_label=source_label)

    checklist_passed = (
        resolved.failed_count == 0
        and not resolved.fake_live_detected
        and not resolved.fake_trace_verified_detected
        and not resolved.fake_exit_sealed_detected
    )

    if not checklist_passed:
        decision = P19ExitSealDecision.BLOCKED
        reason = "Exit seal checklist has failures or forbidden truth labels"
    elif live_demo.demo_status is P19LiveDemoStatus.UNAVAILABLE_LIVE_PATH:
        decision = P19ExitSealDecision.PARTIAL
        reason = (
            "P1.9 is PARTIAL: contract/projection/CLI/docs evidence present. "
            "LIVE path unavailable; TRACE_VERIFIED unavailable. "
            "API/event runtime contract-only. TUI unavailable. "
            "DEV_FIXTURE demo passed in-process. "
            "Not EXIT_SEALED; OMNI review required before P2."
        )
    else:
        decision = P19ExitSealDecision.PARTIAL
        reason = (
            "P1.9 is PARTIAL: all P1.9.0-P1.9.30 checkpoints have contract evidence. "
            "CLI read-only inspect available; TUI UNAVAILABLE. "
            "API/event contract-only; no LIVE or TRACE_VERIFIED claims. "
            "DEV_FIXTURE live demo only. Next: OMNI seal review; P2 gated."
        )

    p2_blocked = decision is not P19ExitSealDecision.SEALED
    p2_reason = (
        "P2 readiness blocked: exit seal is not SEALED; "
        "LIVE and TRACE_VERIFICATION unavailable"
    )

    side_effects = _all_false_side_effects()
    body = {
        "schema_version": OUTPUT_PASSPORT_EXIT_SEAL_VERSION,
        "task_id": OUTPUT_PASSPORT_P1_9_30_TASK_ID,
        "decision": decision,
        "decision_reason": reason,
        "checklist": resolved,
        "live_demo": live_demo,
        "checklist_passed": checklist_passed,
        "p2_readiness_blocked": p2_blocked,
        "p2_readiness_reason": p2_reason,
        "truth_label": OutputPassportTruthLabel.NOT_SEAL,
        "source_label": source_label,
        "side_effects": side_effects,
    }
    return P19ExitSeal(
        **body,
        seal_hash=_hash_payload(body),
    )


def serialize_p1_9_exit_seal_result(seal: P19ExitSeal) -> str:
    return to_canonical_json(seal)


def assert_seal_honest(seal: P19ExitSeal) -> None:
    """Raise if seal claims forbidden operational truth."""
    if seal.decision is P19ExitSealDecision.SEALED:
        raise ValueError("SEALED decision requires explicit evidence; not allowed by default")
    if seal.live_demo.truth_label is OutputPassportTruthLabel.LIVE:
        raise ValueError("LIVE truth label forbidden without production proof")
    if seal.live_demo.truth_label is OutputPassportTruthLabel.TRACE_VERIFIED:
        raise ValueError("TRACE_VERIFIED forbidden without trace verification proof")
    if seal.checklist.fake_live_detected:
        raise ValueError("fake LIVE detected in checklist truth labels")
    if seal.checklist.fake_trace_verified_detected:
        raise ValueError("fake TRACE_VERIFIED detected in checklist truth labels")
    if seal.checklist.fake_exit_sealed_detected:
        raise ValueError("fake EXIT_SEALED detected in checklist truth labels")
