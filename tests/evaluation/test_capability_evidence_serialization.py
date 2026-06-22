"""P1.5.2 capability evidence serialization tests."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.capability_evidence import (
    CapabilityEvidenceKind,
    CapabilityEvidenceRequirement,
    CapabilityEvidenceStrength,
    aggregate_capability_evidence_records,
    build_capability_evidence_link,
    build_p152_capability_evidence_report,
    capability_evidence_link_to_dict,
    capability_evidence_record_report_to_dict,
    capability_evidence_record_set_to_dict,
    capability_evidence_record_to_dict,
    capability_evidence_requirement_to_dict,
    example_usable_evidence_from_result,
)


def test_capability_evidence_record_json_serializable():
    rec = example_usable_evidence_from_result()
    d = capability_evidence_record_to_dict(rec)
    p = json.loads(json.dumps(d))
    assert p["evidence_id"] == rec.evidence_id
    assert p["status"] == "USABLE"
    assert p["status"] != "VERIFIED"


def test_capability_evidence_requirement_json_serializable():
    req = CapabilityEvidenceRequirement(
        requirement_id="req1", required_kinds=(CapabilityEvidenceKind.EVALUATION_RESULT,),
        minimum_strength=CapabilityEvidenceStrength.ADEQUATE, reason="test",
    )
    d = capability_evidence_requirement_to_dict(req)
    assert json.loads(json.dumps(d))["requirement_id"] == "req1"


def test_capability_evidence_link_json_serializable():
    link = build_capability_evidence_link(
        link_id="lnk1", evidence_id="ev1", subject_id="sub1",
        subject_type="CAPABILITY_CLAIM", relationship="supports_capability_claim",
        supports_claim_id="claim1",
    )
    d = capability_evidence_link_to_dict(link)
    assert json.loads(json.dumps(d))["link_id"] == "lnk1"


def test_capability_evidence_record_set_json_serializable():
    rec = example_usable_evidence_from_result()
    rs = aggregate_capability_evidence_records(record_set_id="rs1", records=(rec,))
    d = capability_evidence_record_set_to_dict(rs)
    assert json.loads(json.dumps(d))["record_set_id"] == "rs1"


def test_capability_evidence_report_json_serializable():
    report = build_p152_capability_evidence_report()
    d = capability_evidence_record_report_to_dict(report)
    p = json.loads(json.dumps(d))
    assert p["status"] == "READY"
    assert "P1.5.3" in p["next_module"]


def test_build_capability_evidence_link():
    link = build_capability_evidence_link(
        link_id="lnk1", evidence_id="ev1", subject_id="sub1",
        subject_type="CAPABILITY_CLAIM", relationship="supports_capability_claim",
    )
    assert link.link_id == "lnk1"


def test_link_rejects_empty_link_id():
    import pytest
    from agentic_runtime.evaluation.capability_evidence import build_capability_evidence_link
    with pytest.raises(ValueError, match="link_id"):
        build_capability_evidence_link(
            link_id="", evidence_id="ev1", subject_id="s1",
            subject_type="T", relationship="r",
        )


def test_link_rejects_empty_evidence_id():
    import pytest
    with pytest.raises(ValueError, match="evidence_id"):
        build_capability_evidence_link(
            link_id="l1", evidence_id="", subject_id="s1",
            subject_type="T", relationship="r",
        )


def test_link_rejects_empty_subject_id():
    import pytest
    with pytest.raises(ValueError, match="subject_id"):
        build_capability_evidence_link(
            link_id="l1", evidence_id="ev1", subject_id="",
            subject_type="T", relationship="r",
        )


def test_link_supports_claim_and_capability_ids():
    link = build_capability_evidence_link(
        link_id="l1", evidence_id="ev1", subject_id="s1",
        subject_type="CAPABILITY_CLAIM", relationship="supports_capability_claim",
        supports_claim_id="claim1", supports_capability_id="cap1",
    )
    assert link.supports_claim_id == "claim1"
    assert link.supports_capability_id == "cap1"
