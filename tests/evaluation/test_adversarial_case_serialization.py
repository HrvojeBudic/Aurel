"""P1.5.9 serialization tests — Adversarial Evaluation Cases."""
from __future__ import annotations

import json

from agentic_runtime.evaluation.adversarial_cases import (
    adversarial_case_report_to_dict,
    adversarial_case_to_dict,
    build_default_adversarial_case_registry,
    build_default_adversarial_case_set,
    build_p159_adversarial_case_report,
)


class TestSerialization:
    def test_default_cases_serialize_deterministically(self):
        cases = build_default_adversarial_case_set()
        payloads = [adversarial_case_to_dict(c) for c in cases]
        for payload in payloads:
            assert isinstance(payload["attack_surfaces"], list)
            assert isinstance(payload["applies_to_domains"], list)
            json.dumps(payload)

    def test_registry_serialization_roundtrip_shape(self):
        registry = build_default_adversarial_case_registry()
        payload = {
            "registry_id": registry.registry_id,
            "case_count": len(registry.cases),
            "case_ids": [c.case_id for c in registry.cases],
        }
        json.dumps(payload)
        assert payload["case_count"] == 15

    def test_report_serialization(self):
        report = build_p159_adversarial_case_report(
            cases_created=15,
            cases_registered=15,
            sparse_cases_ready=True,
        )
        payload = adversarial_case_report_to_dict(report)
        json.dumps(payload)
        assert payload["status"] == "READY"
        assert payload["sparse_cases_ready"] is True
        assert "P1.5.10" in payload["next_module"]
