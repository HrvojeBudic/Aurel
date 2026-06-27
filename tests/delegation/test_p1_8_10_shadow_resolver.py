"""Focused P1.8.10 shadow resolver / consistency model tests (DEV_FIXTURE).

All shadow resolver objects are diagnostic only; no policy decision,
Custos call, approval creation, authority grant/deny, runtime allow/block,
enforcement, delegation execution, trace write, Ledger write, or runtime
mutation is implemented or claimed.
"""
from __future__ import annotations

import json

import pytest

from agentic_runtime.delegation import (
    DelegationConsistencyFamily,
    DelegationConsistencyFinding,
    DelegationConsistencyFindingKind,
    DelegationConsistencyMatrix,
    DelegationConsistencyMatrixEntry,
    DelegationConsistencySeverity,
    DelegationConsistencySnapshot,
    DelegationShadowResolverInputEnvelope,
    DelegationShadowResolverMode,
    DelegationShadowResolverReadinessProfile,
    DelegationShadowResolverResult,
    DelegationShadowResolverSideEffects,
    DelegationShadowResolverStatus,
    DelegationShadowResolverStatusReport,
    DelegationError,
    DelegationLifecycleBindingSet,
    DelegationSourceLabel,
    DelegationUnknownFieldError,
    DelegationValidationError,
    DELEGATION_SHADOW_RESOLVER_UNAVAILABLE_BINDINGS,
    build_delegation_consistency_finding,
    build_delegation_consistency_matrix,
    build_delegation_consistency_matrix_entry,
    build_delegation_consistency_snapshot,
    build_delegation_shadow_resolver_input_envelope,
    build_delegation_shadow_resolver_readiness_profile,
    build_delegation_shadow_resolver_result,
    build_delegation_shadow_resolver_status_report,
    hash_delegation_consistency_finding,
    hash_delegation_consistency_matrix,
    hash_delegation_consistency_matrix_entry,
    hash_delegation_consistency_snapshot,
    hash_delegation_shadow_resolver_input_envelope,
    hash_delegation_shadow_resolver_readiness_profile,
    hash_delegation_shadow_resolver_result,
    hash_delegation_shadow_resolver_status_report,
    serialize_delegation_consistency_matrix,
    serialize_delegation_shadow_resolver_input_envelope,
    serialize_delegation_shadow_resolver_result,
)
from agentic_runtime.delegation.foundation import (
    DelegationSourceLabel as DSL,
    validate_known_fields,
)
from agentic_runtime.delegation.shadow_resolver import (
    INPUT_ENVELOPE_KNOWN_FIELDS,
    FINDING_KNOWN_FIELDS,
    MATRIX_ENTRY_KNOWN_FIELDS,
    CONSISTENCY_MATRIX_KNOWN_FIELDS,
    READINESS_PROFILE_KNOWN_FIELDS,
    SNAPSHOT_KNOWN_FIELDS,
    SHADOW_RESULT_KNOWN_FIELDS,
    STATUS_REPORT_KNOWN_FIELDS,
    DelegationShadowResolverSideEffects as SRSE,
)

# ---------------------------------------------------------------------------
# Reusable DEV_FIXTURE helpers
# ---------------------------------------------------------------------------

_DELEGATION_REF_ID = "P1.8.10-test-delegation-ref"
_DUMMY_HASH = "a" * 64


def _build_dev_fixture_input_envelope(**overrides) -> DelegationShadowResolverInputEnvelope:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "delegation_identity_hash": _DUMMY_HASH,
        "role_binding_hash": "b" * 64,
        "constraint_set_hash": "c" * 64,
        "authority_binding_set_hash": "d" * 64,
        "non_repudiation_binding_set_hash": "e" * 64,
        "identity_mesh_binding_set_hash": "f" * 64,
        "scope_binding_set_hash": "g" * 64,
        "lifecycle_binding_set_hash": "h" * 64,
        "chain_binding_set_hash": "i" * 64,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_shadow_resolver_input_envelope(**kwargs)


def _build_dev_fixture_finding(family, finding_kind, **overrides) -> DelegationConsistencyFinding:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "family": family,
        "finding_kind": finding_kind,
        "severity": DelegationConsistencySeverity.INFO,
        "finding_detail": f"DEV_FIXTURE {family.value} {finding_kind.value}",
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_consistency_finding(**kwargs)


def _build_dev_fixture_matrix_entry(family, **overrides) -> DelegationConsistencyMatrixEntry:
    kwargs = {
        "delegation_ref_id": _DELEGATION_REF_ID,
        "family": family,
        "present": True,
        "hash_present": True,
        "delegation_ref_aligned": True,
        "source_label_present": True,
        "finding_count": 1,
        "source_label": DelegationSourceLabel.DEV_FIXTURE,
    }
    kwargs.update(overrides)
    return build_delegation_consistency_matrix_entry(**kwargs)


# ---------------------------------------------------------------------------
# 1. Import checks
# ---------------------------------------------------------------------------

def test_imports_work():
    """All P1.8.10 symbols importable from agentic_runtime.delegation."""
    assert DelegationShadowResolverMode is not None
    assert DelegationConsistencyFamily is not None
    assert DelegationConsistencyFindingKind is not None
    assert DelegationConsistencySeverity is not None
    assert DelegationShadowResolverStatus is not None
    assert DelegationShadowResolverInputEnvelope is not None
    assert DelegationConsistencyFinding is not None
    assert DelegationConsistencyMatrixEntry is not None
    assert DelegationConsistencyMatrix is not None
    assert DelegationShadowResolverReadinessProfile is not None
    assert DelegationConsistencySnapshot is not None
    assert DelegationShadowResolverResult is not None
    assert DelegationShadowResolverStatusReport is not None
    assert DelegationShadowResolverSideEffects is not None


def test_existing_p1_8_0_exports_remain():
    """P1.8.0 exports remain importable."""
    from agentic_runtime.delegation import (
        DelegationRecord,
        DelegationSideEffects,
        DelegationSourceLabel,
    )
    assert DelegationRecord is not None
    assert DelegationSideEffects is not None
    assert DelegationSourceLabel is not None


def test_existing_p1_8_9_exports_remain():
    """P1.8.9 exports remain importable."""
    from agentic_runtime.delegation import (
        DelegationChainBindingSet,
        DelegationChainEnvelope,
        build_delegation_chain_binding_set,
    )
    assert DelegationChainBindingSet is not None
    assert DelegationChainEnvelope is not None
    assert build_delegation_chain_binding_set is not None


# ---------------------------------------------------------------------------
# 2. InputEnvelope tests
# ---------------------------------------------------------------------------

def test_input_envelope_builds_deterministically():
    env1 = _build_dev_fixture_input_envelope()
    env2 = _build_dev_fixture_input_envelope()
    assert env1.input_envelope_hash == env2.input_envelope_hash
    assert env1.input_envelope_hash == hash_delegation_shadow_resolver_input_envelope(env1)


def test_input_envelope_hash_changes_on_different_hash():
    env1 = _build_dev_fixture_input_envelope()
    env2 = _build_dev_fixture_input_envelope(delegation_identity_hash="z" * 64)
    assert env1.input_envelope_hash != env2.input_envelope_hash


def test_input_envelope_hash_changes_on_different_ref_id():
    env1 = _build_dev_fixture_input_envelope()
    env2 = _build_dev_fixture_input_envelope(delegation_ref_id="different-ref")
    assert env1.input_envelope_hash != env2.input_envelope_hash


def test_input_envelope_serialization_is_json_safe():
    env = _build_dev_fixture_input_envelope()
    serialized = serialize_delegation_shadow_resolver_input_envelope(env)
    parsed = json.loads(serialized)
    assert parsed["schema_version"] == "delegation_shadow_resolver_input_envelope.v1"
    assert parsed["delegation_ref_id"] == _DELEGATION_REF_ID


def test_input_envelope_serialization_deterministic():
    env1 = _build_dev_fixture_input_envelope()
    env2 = _build_dev_fixture_input_envelope()
    assert serialize_delegation_shadow_resolver_input_envelope(env1) == \
           serialize_delegation_shadow_resolver_input_envelope(env2)


def test_input_envelope_enforces_required_fields():
    with pytest.raises(DelegationError):
        build_delegation_shadow_resolver_input_envelope(
            delegation_ref_id="",
            delegation_identity_hash=_DUMMY_HASH,
            role_binding_hash="b" * 64,
            constraint_set_hash="c" * 64,
            authority_binding_set_hash="d" * 64,
            non_repudiation_binding_set_hash="e" * 64,
            identity_mesh_binding_set_hash="f" * 64,
            scope_binding_set_hash="g" * 64,
            lifecycle_binding_set_hash="h" * 64,
            chain_binding_set_hash="i" * 64,
        )


def test_input_envelope_closed_world():
    validate_known_fields(
        _build_dev_fixture_input_envelope().to_canonical_dict(),
        INPUT_ENVELOPE_KNOWN_FIELDS,
        label="input_envelope",
    )


# ---------------------------------------------------------------------------
# 3. ConsistencyFinding tests
# ---------------------------------------------------------------------------

def test_finding_builds_deterministically():
    f1 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )
    f2 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )
    assert f1.finding_hash == f2.finding_hash
    assert f1.finding_hash == hash_delegation_consistency_finding(f1)


def test_finding_hash_changes_on_different_kind():
    f1 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )
    f2 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.MISSING,
    )
    assert f1.finding_hash != f2.finding_hash


def test_finding_hash_changes_on_different_family():
    f1 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )
    f2 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.FOUNDATION,
        DelegationConsistencyFindingKind.PRESENT,
    )
    assert f1.finding_hash != f2.finding_hash


def test_finding_hash_changes_on_different_detail():
    f1 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
        finding_detail="detail-a",
    )
    f2 = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
        finding_detail="detail-b",
    )
    assert f1.finding_hash != f2.finding_hash


def test_finding_kinds_exist():
    assert DelegationConsistencyFindingKind.PRESENT
    assert DelegationConsistencyFindingKind.MISSING
    assert DelegationConsistencyFindingKind.MISMATCH
    assert DelegationConsistencyFindingKind.CONFLICT_REFERENCED
    assert DelegationConsistencyFindingKind.UNAVAILABLE
    assert DelegationConsistencyFindingKind.REFERENCE_ONLY
    assert DelegationConsistencyFindingKind.UNKNOWN


def test_finding_present_is_not_verified():
    """PRESENT does not mean verified."""
    f = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )
    assert f.finding_kind == DelegationConsistencyFindingKind.PRESENT
    # Finding is diagnostic only; PRESENT makes no verification claim


def test_finding_missing_is_not_failed():
    """MISSING does not mean failed."""
    f = _build_dev_fixture_finding(
        DelegationConsistencyFamily.CHAIN,
        DelegationConsistencyFindingKind.MISSING,
    )
    assert f.finding_kind == DelegationConsistencyFindingKind.MISSING
    # Finding is diagnostic only; MISSING makes no failure claim


def test_finding_mismatch_is_not_denied():
    """MISMATCH does not mean denied."""
    f = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.MISMATCH,
    )
    assert f.finding_kind == DelegationConsistencyFindingKind.MISMATCH
    # Finding is diagnostic only; MISMATCH makes no denial claim


def test_finding_conflict_referenced_is_not_runtime_denial():
    """CONFLICT_REFERENCED does not mean runtime denial."""
    f = _build_dev_fixture_finding(
        DelegationConsistencyFamily.AUTHORITY,
        DelegationConsistencyFindingKind.CONFLICT_REFERENCED,
    )
    assert f.finding_kind == DelegationConsistencyFindingKind.CONFLICT_REFERENCED
    # Diagnostic only, not runtime denial


def test_finding_error_severity_is_not_enforcement():
    """ERROR severity does not mean enforcement."""
    f = _build_dev_fixture_finding(
        DelegationConsistencyFamily.FOUNDATION,
        DelegationConsistencyFindingKind.MISSING,
        severity=DelegationConsistencySeverity.ERROR,
    )
    assert f.severity == DelegationConsistencySeverity.ERROR
    # ERROR severity is diagnostic, not enforcement


def test_finding_closed_world():
    validate_known_fields(
        _build_dev_fixture_finding(
            DelegationConsistencyFamily.IDENTITY,
            DelegationConsistencyFindingKind.PRESENT,
        ).to_canonical_dict(),
        FINDING_KNOWN_FIELDS,
        label="finding",
    )


# ---------------------------------------------------------------------------
# 4. ConsistencyMatrixEntry tests
# ---------------------------------------------------------------------------

def test_matrix_entry_builds_deterministically():
    e1 = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)
    e2 = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)
    assert e1.entry_hash == e2.entry_hash
    assert e1.entry_hash == hash_delegation_consistency_matrix_entry(e1)


def test_matrix_entry_hash_changes_on_different_family():
    e1 = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)
    e2 = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.FOUNDATION)
    assert e1.entry_hash != e2.entry_hash


def test_matrix_entry_hash_changes_on_different_present():
    e1 = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY, present=True)
    e2 = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY, present=False)
    assert e1.entry_hash != e2.entry_hash


def test_matrix_entry_closed_world():
    validate_known_fields(
        _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY).to_canonical_dict(),
        MATRIX_ENTRY_KNOWN_FIELDS,
        label="matrix_entry",
    )


# ---------------------------------------------------------------------------
# 5. ConsistencyMatrix tests
# ---------------------------------------------------------------------------

def test_consistency_matrix_builds_deterministically():
    entries = [
        _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY),
        _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.FOUNDATION),
    ]
    m1 = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=entries,
    )
    m2 = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=list(reversed(entries)),  # order should not matter
    )
    assert m1.matrix_hash == m2.matrix_hash
    assert m1.matrix_hash == hash_delegation_consistency_matrix(m1)


def test_consistency_matrix_hash_changes_on_different_entries():
    m1 = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    m2 = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[
            _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY),
            _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.FOUNDATION),
        ],
    )
    assert m1.matrix_hash != m2.matrix_hash


def test_consistency_matrix_entries_sorted_deterministically():
    entries = [
        _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.CHAIN),
        _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.FOUNDATION),
        _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY),
    ]
    m = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=entries,
    )
    ordered = [e.family.value for e in m.entries]
    assert ordered == sorted(ordered)


def test_consistency_matrix_is_not_approval_matrix():
    """ConsistencyMatrix is diagnostic, not an approval matrix."""
    m = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    # Matrix exists as diagnostic artifact; does not approve/deny/enforce
    assert m.matrix_hash
    assert m.consistency_matrix_id


def test_consistency_matrix_serialization_json_safe():
    m = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    serialized = serialize_delegation_consistency_matrix(m)
    parsed = json.loads(serialized)
    assert "entry_hashes" in parsed
    assert "matrix_hash" in parsed


def test_consistency_matrix_closed_world():
    m = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    validate_known_fields(m.to_canonical_dict(), CONSISTENCY_MATRIX_KNOWN_FIELDS, label="matrix")


# ---------------------------------------------------------------------------
# 6. ShadowResolverReadinessProfile tests
# ---------------------------------------------------------------------------

def test_readiness_profile_builds_with_all_true():
    r = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
        has_identity=True,
        has_roles=True,
        has_constraints=True,
        has_authority=True,
        has_non_repudiation=True,
        has_identity_mesh=True,
        has_scope=True,
        has_lifecycle=True,
        has_chain=True,
    )
    assert r.has_foundation
    assert r.has_identity
    assert len(r.missing_families) == 0


def test_readiness_profile_reports_missing_families():
    r = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
        has_identity=False,
        has_roles=True,
        has_constraints=False,
    )
    missing = set(f.value for f in r.missing_families)
    assert "IDENTITY" in missing
    assert "CONSTRAINTS" in missing
    assert "FOUNDATION" not in missing


def test_readiness_profile_deterministic():
    r1 = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
        has_identity=True,
    )
    r2 = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
        has_identity=True,
    )
    assert r1.readiness_hash == r2.readiness_hash
    assert r1.readiness_hash == hash_delegation_shadow_resolver_readiness_profile(r1)


def test_readiness_profile_hash_changes_on_different_presence():
    r1 = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
    )
    r2 = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=False,
    )
    assert r1.readiness_hash != r2.readiness_hash


def test_readiness_profile_is_not_approval_readiness():
    """ReadinessProfile is presence/absence, not approval readiness."""
    r = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
        has_identity=True,
        has_roles=True,
        has_constraints=True,
        has_authority=True,
        has_non_repudiation=True,
        has_identity_mesh=True,
        has_scope=True,
        has_lifecycle=True,
        has_chain=True,
    )
    assert r.readiness_hash
    assert "not available" in r.policy_unavailable_reason.lower()
    assert "not available" in r.custos_unavailable_reason.lower()
    assert "not available" in r.approval_unavailable_reason.lower()


def test_readiness_profile_is_not_execution_readiness():
    """Readiness profile does not claim execution readiness."""
    r = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
    )
    assert "not available" in r.runtime_unavailable_reason.lower()


def test_readiness_profile_closed_world():
    r = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
    )
    validate_known_fields(r.to_canonical_dict(), READINESS_PROFILE_KNOWN_FIELDS, label="readiness")


# ---------------------------------------------------------------------------
# 7. ConsistencySnapshot tests
# ---------------------------------------------------------------------------

def test_snapshot_builds_deterministically():
    env = _build_dev_fixture_input_envelope()
    findings = [
        _build_dev_fixture_finding(
            DelegationConsistencyFamily.IDENTITY,
            DelegationConsistencyFindingKind.PRESENT,
        ),
    ]
    matrix = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    profile = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_identity=True,
    )
    s1 = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=findings,
        matrix=matrix,
        readiness_profile=profile,
    )
    s2 = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=findings,
        matrix=matrix,
        readiness_profile=profile,
    )
    assert s1.snapshot_hash == s2.snapshot_hash
    assert s1.snapshot_hash == hash_delegation_consistency_snapshot(s1)


def test_snapshot_hash_changes_on_different_findings():
    env = _build_dev_fixture_input_envelope()
    f1 = [_build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )]
    f2 = [_build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.MISSING,
    )]
    matrix = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    profile = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_identity=True,
    )
    s1 = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=f1,
        matrix=matrix,
        readiness_profile=profile,
    )
    s2 = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=f2,
        matrix=matrix,
        readiness_profile=profile,
    )
    assert s1.snapshot_hash != s2.snapshot_hash


def test_snapshot_closed_world():
    env = _build_dev_fixture_input_envelope()
    matrix = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    profile = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
    )
    s = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=[],
        matrix=matrix,
        readiness_profile=profile,
    )
    validate_known_fields(s.to_canonical_dict(), SNAPSHOT_KNOWN_FIELDS, label="snapshot")


# ---------------------------------------------------------------------------
# 8. ShadowResolverResult tests
# ---------------------------------------------------------------------------

def _build_full_result() -> DelegationShadowResolverResult:
    env = _build_dev_fixture_input_envelope()
    findings = [
        _build_dev_fixture_finding(
            DelegationConsistencyFamily.IDENTITY,
            DelegationConsistencyFindingKind.PRESENT,
        ),
    ]
    matrix = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    profile = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_identity=True,
    )
    snapshot = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=findings,
        matrix=matrix,
        readiness_profile=profile,
    )
    return build_delegation_shadow_resolver_result(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope=env,
        snapshot=snapshot,
        matrix=matrix,
        readiness_profile=profile,
        findings=findings,
        resolver_mode=DelegationShadowResolverMode.DIAGNOSTIC_ONLY,
    )


def test_result_builds_deterministically():
    r1 = _build_full_result()
    r2 = _build_full_result()
    assert r1.result_hash == r2.result_hash
    assert r1.result_hash == hash_delegation_shadow_resolver_result(r1)


def test_result_is_diagnostic_only():
    """ShadowResolverResult is diagnostic only, not policy decision."""
    r = _build_full_result()
    assert r.resolver_mode == DelegationShadowResolverMode.DIAGNOSTIC_ONLY
    assert r.resolver_status == DelegationShadowResolverStatus.SHADOW_EVALUATED
    # SHADOW_EVALUATED does not mean policy decision


def test_result_is_not_policy_decision():
    """ShadowResolverResult contains no allow/deny/approve fields."""
    r = _build_full_result()
    d = r.to_canonical_dict()
    assert "allow" not in d
    assert "deny" not in d
    assert "approved" not in d
    assert "blocked" not in d
    assert "enforce" not in d


def test_result_hash_changes_on_different_input():
    r1 = _build_full_result()
    # Different env
    env2 = _build_dev_fixture_input_envelope(delegation_identity_hash="z" * 64)
    findings = [
        _build_dev_fixture_finding(
            DelegationConsistencyFamily.IDENTITY,
            DelegationConsistencyFindingKind.PRESENT,
        ),
    ]
    matrix = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=[_build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)],
    )
    profile = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_identity=True,
    )
    snapshot2 = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env2.input_envelope_hash,
        findings=findings,
        matrix=matrix,
        readiness_profile=profile,
    )
    r2 = build_delegation_shadow_resolver_result(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope=env2,
        snapshot=snapshot2,
        matrix=matrix,
        readiness_profile=profile,
        findings=findings,
    )
    assert r1.result_hash != r2.result_hash


def test_result_serialization_json_safe():
    r = _build_full_result()
    serialized = serialize_delegation_shadow_resolver_result(r)
    parsed = json.loads(serialized)
    assert parsed["resolver_mode"] == "DIAGNOSTIC_ONLY"
    assert parsed["resolver_status"] == "SHADOW_EVALUATED"
    assert "side_effects" in parsed


def test_result_unavailable_bindings_are_deterministic():
    r1 = _build_full_result()
    r2 = _build_full_result()
    assert tuple(sorted(r1.unavailable_bindings)) == tuple(sorted(r2.unavailable_bindings))


def test_result_closed_world():
    r = _build_full_result()
    validate_known_fields(r.to_canonical_dict(), SHADOW_RESULT_KNOWN_FIELDS, label="result")


# ---------------------------------------------------------------------------
# 9. SideEffects tests
# ---------------------------------------------------------------------------

def test_side_effects_all_default_false():
    se = DelegationShadowResolverSideEffects()
    assert se.policy_decision_made is False
    assert se.custos_called is False
    assert se.approval_created is False
    assert se.authority_granted is False
    assert se.authority_denied is False
    assert se.runtime_allowed is False
    assert se.runtime_blocked is False
    assert se.enforcement_performed is False
    assert se.delegation_executed is False
    assert se.trace_written is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


def test_result_side_effects_all_false():
    r = _build_full_result()
    se = r.side_effects
    fields = [
        "policy_decision_made", "custos_called", "approval_created",
        "authority_granted", "authority_denied", "runtime_allowed",
        "runtime_blocked", "enforcement_performed", "delegation_executed",
        "trace_written", "ledger_written", "global_trace_written",
        "runtime_mutated",
    ]
    for fname in fields:
        assert getattr(se, fname) is False, f"side effect {fname} must be False"


def test_no_policy_decision():
    """P1.8.10 explicitly does not make policy decisions."""
    r = _build_full_result()
    assert r.side_effects.policy_decision_made is False


def test_no_custos_call():
    """P1.8.10 does not call Custos."""
    r = _build_full_result()
    assert r.side_effects.custos_called is False


def test_no_approval_creation():
    """P1.8.10 does not create approvals."""
    r = _build_full_result()
    assert r.side_effects.approval_created is False


def test_no_authority_grant():
    """P1.8.10 does not grant authority."""
    r = _build_full_result()
    assert r.side_effects.authority_granted is False


def test_no_authority_deny():
    """P1.8.10 does not deny authority."""
    r = _build_full_result()
    assert r.side_effects.authority_denied is False


def test_no_runtime_allow():
    """P1.8.10 does not allow runtime."""
    r = _build_full_result()
    assert r.side_effects.runtime_allowed is False


def test_no_runtime_block():
    """P1.8.10 does not block runtime."""
    r = _build_full_result()
    assert r.side_effects.runtime_blocked is False


def test_no_enforcement():
    """P1.8.10 does not enforce."""
    r = _build_full_result()
    assert r.side_effects.enforcement_performed is False


def test_no_delegation_execution():
    """P1.8.10 does not execute delegations."""
    r = _build_full_result()
    assert r.side_effects.delegation_executed is False


def test_no_trace_write():
    """P1.8.10 does not write trace."""
    r = _build_full_result()
    assert r.side_effects.trace_written is False


def test_no_ledger_write():
    """P1.8.10 does not write Ledger."""
    r = _build_full_result()
    assert r.side_effects.ledger_written is False


def test_no_global_trace_write():
    """P1.8.10 does not write global trace."""
    r = _build_full_result()
    assert r.side_effects.global_trace_written is False


def test_no_runtime_mutation():
    """P1.8.10 does not mutate runtime."""
    r = _build_full_result()
    assert r.side_effects.runtime_mutated is False


# ---------------------------------------------------------------------------
# 10. StatusReport tests
# ---------------------------------------------------------------------------

def test_status_report_builds():
    report = build_delegation_shadow_resolver_status_report()
    assert report.schema_version == "delegation_shadow_resolver_status_report.v1"
    assert "Diagnostic Only" in report.status_label


def test_status_report_deterministic():
    r1 = build_delegation_shadow_resolver_status_report()
    r2 = build_delegation_shadow_resolver_status_report()
    assert r1.status_hash == r2.status_hash
    assert r1.status_hash == hash_delegation_shadow_resolver_status_report(r1)


def test_status_report_has_unavailable_surfaces():
    report = build_delegation_shadow_resolver_status_report()
    unavailable = report.unavailable_bindings
    assert "Policy Decision Engine" in unavailable
    assert "Custos Resolver" in unavailable
    assert "Approval System" in unavailable
    assert "Authority Grant/Deny" in unavailable
    assert "Runtime Allow/Block" in unavailable
    assert "Enforcement Engine" in unavailable
    assert "Delegation Executor" in unavailable
    assert "Trace Writer" in unavailable
    assert "Ledger Write" in unavailable
    assert "P1.8.11 Operator Approval Intent Model" in unavailable
    assert "Output Passport / P1.9" in unavailable


def test_status_report_side_effects_all_false():
    report = build_delegation_shadow_resolver_status_report()
    se = report.side_effects
    assert se.policy_decision_made is False
    assert se.custos_called is False
    assert se.approval_created is False
    assert se.authority_granted is False
    assert se.authority_denied is False
    assert se.runtime_allowed is False
    assert se.runtime_blocked is False
    assert se.enforcement_performed is False
    assert se.delegation_executed is False
    assert se.trace_written is False
    assert se.ledger_written is False
    assert se.global_trace_written is False
    assert se.runtime_mutated is False


def test_status_report_closed_world():
    report = build_delegation_shadow_resolver_status_report()
    validate_known_fields(report.to_canonical_dict(), STATUS_REPORT_KNOWN_FIELDS, label="status")


# ---------------------------------------------------------------------------
# 11. Full DEV_FIXTURE vertical path
# ---------------------------------------------------------------------------

def test_dev_fixture_vertical_chain():
    """Full P1.8.10 operator-testable path: InputEnvelope → Findings → Matrix →
    Readiness → Snapshot → Result → StatusReport."""
    # 1. Build input envelope
    env = _build_dev_fixture_input_envelope()
    assert env.input_envelope_hash
    assert env.source_label == DSL.DEV_FIXTURE

    # 2. Build findings for each family
    families = [
        DelegationConsistencyFamily.FOUNDATION,
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFamily.ROLES,
        DelegationConsistencyFamily.CONSTRAINTS,
        DelegationConsistencyFamily.AUTHORITY,
        DelegationConsistencyFamily.NON_REPUDIATION,
        DelegationConsistencyFamily.IDENTITY_MESH,
        DelegationConsistencyFamily.SCOPE,
        DelegationConsistencyFamily.LIFECYCLE,
        DelegationConsistencyFamily.CHAIN,
    ]
    findings = [
        _build_dev_fixture_finding(f, DelegationConsistencyFindingKind.PRESENT)
        for f in families
    ]
    assert len(findings) == 10

    # 3. Build matrix entries
    entries = [
        _build_dev_fixture_matrix_entry(f, finding_count=1)
        for f in families
    ]
    matrix = build_delegation_consistency_matrix(
        delegation_ref_id=_DELEGATION_REF_ID,
        entries=entries,
    )
    assert matrix.matrix_hash

    # 4. Build readiness profile
    profile = build_delegation_shadow_resolver_readiness_profile(
        delegation_ref_id=_DELEGATION_REF_ID,
        has_foundation=True,
        has_identity=True,
        has_roles=True,
        has_constraints=True,
        has_authority=True,
        has_non_repudiation=True,
        has_identity_mesh=True,
        has_scope=True,
        has_lifecycle=True,
        has_chain=True,
    )
    assert len(profile.missing_families) == 0

    # 5. Build snapshot
    snapshot = build_delegation_consistency_snapshot(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope_hash=env.input_envelope_hash,
        findings=findings,
        matrix=matrix,
        readiness_profile=profile,
    )
    assert snapshot.snapshot_hash

    # 6. Build result
    result = build_delegation_shadow_resolver_result(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope=env,
        snapshot=snapshot,
        matrix=matrix,
        readiness_profile=profile,
        findings=findings,
        resolver_mode=DelegationShadowResolverMode.DIAGNOSTIC_ONLY,
    )
    assert result.result_hash
    assert result.resolver_status == DelegationShadowResolverStatus.SHADOW_EVALUATED
    assert result.finding_count == 10

    # 7. Build status report
    report = build_delegation_shadow_resolver_status_report()
    assert report.status_hash
    assert "Diagnostic Only" in report.status_label

    # 8. All side effects are false
    se = result.side_effects
    assert se.policy_decision_made is False
    assert se.delegation_executed is False
    assert se.ledger_written is False
    assert se.trace_written is False

    # 9. Deterministic re-check
    result2 = build_delegation_shadow_resolver_result(
        delegation_ref_id=_DELEGATION_REF_ID,
        input_envelope=env,
        snapshot=snapshot,
        matrix=matrix,
        readiness_profile=profile,
        findings=findings,
        resolver_mode=DelegationShadowResolverMode.DIAGNOSTIC_ONLY,
    )
    assert result.result_hash == result2.result_hash


# ---------------------------------------------------------------------------
# 12. DEV_FIXTURE source label visibility
# ---------------------------------------------------------------------------

def test_all_dev_fixture_objects_show_dev_fixture_label():
    """All generated test objects should show DEV_FIXTURE source label."""
    env = _build_dev_fixture_input_envelope()
    assert env.source_label == DelegationSourceLabel.DEV_FIXTURE

    finding = _build_dev_fixture_finding(
        DelegationConsistencyFamily.IDENTITY,
        DelegationConsistencyFindingKind.PRESENT,
    )
    assert finding.source_label == DelegationSourceLabel.DEV_FIXTURE

    entry = _build_dev_fixture_matrix_entry(DelegationConsistencyFamily.IDENTITY)
    assert entry.source_label == DelegationSourceLabel.DEV_FIXTURE
