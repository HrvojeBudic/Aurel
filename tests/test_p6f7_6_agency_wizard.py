"""F7.6 seal — the Agency wizard (environment templates + what-if impact report).

The wizard drafts a governed environment and previews what its mandate would
allow/deny through the REAL F6.2 gate (evidence, not authority). It creates
nothing directly — `to_proposal()` produces a one-door payload. An
`EnvironmentTemplate` is un-constructible without a scope.
"""
from __future__ import annotations

import pytest

from agentic_runtime.core_types import CommandEnvelope, RiskLevel
from agentic_runtime.corp import (
    EnvironmentTemplate,
    SampleAction,
    what_if,
)
from agentic_runtime.mandate import MandateScope
from agentic_runtime.mandate.enforcement import evaluate_mandate_scope_check


def _template():
    return EnvironmentTemplate(
        client_name="Acme",
        job_title="Repo Y work",
        scope=MandateScope(paths=("clients/acme/",), client_id="acme",
                           allowed_tools=("write_file", "run_tests"),
                           max_risk=RiskLevel.MEDIUM),
        persona_ref="advisor",
        repos=("repoY",),
    )


# --- no-overclaim -----------------------------------------------------------------

def test_template_requires_scope():
    with pytest.raises(TypeError):
        EnvironmentTemplate(client_name="c", job_title="j", scope=None)  # type: ignore[arg-type]


def test_template_requires_names():
    with pytest.raises(ValueError):
        EnvironmentTemplate(client_name="", job_title="j", scope=MandateScope())
    with pytest.raises(ValueError):
        EnvironmentTemplate(client_name="c", job_title="", scope=MandateScope())


# --- what-if predicts what the real gate would do ---------------------------------

def test_what_if_predicts_deny_and_allow():
    tmpl = _template()
    actions = [
        SampleAction("write_file", RiskLevel.LOW, {"path": "clients/acme/a.py"}),   # in scope
        SampleAction("write_file", RiskLevel.LOW, {"path": "clients/other/b.py"}),  # out of paths
        SampleAction("deploy", RiskLevel.LOW, {}),                                   # tool not allowed
        # risk > ceiling
        SampleAction("write_file", RiskLevel.HIGH, {"path": "clients/acme/c.py"}),
    ]
    report = what_if(tmpl, actions)
    verdicts = [r["would_block"] for r in report.results]
    assert verdicts == [False, True, True, True]
    assert report.allowed_count == 1 and report.blocked_count == 3


def test_what_if_matches_the_real_gate_on_a_real_command():
    # The wizard uses the same evaluate_mandate_scope_check the runtime uses, so a
    # SampleAction and an equivalent real CommandEnvelope must get the same verdict.
    tmpl = _template()
    mandate = tmpl.to_mandate()
    for path, tool, risk in (
        ("clients/acme/ok.py", "write_file", RiskLevel.LOW),
        ("clients/other/no.py", "write_file", RiskLevel.LOW),
    ):
        sample = SampleAction(tool, risk, {"path": path})
        cmd = CommandEnvelope.make(issuer_card_id="card-1", tool=tool,
                                   args={"path": path}, rationale="r",
                                   declared_risk=risk, expected_effect="e")
        wiz = what_if(tmpl, [sample]).results[0]["would_block"]
        real = evaluate_mandate_scope_check(cmd, None, mandate, now=0.0).should_block
        assert wiz == real


# --- evidence, not authority ------------------------------------------------------

def test_impact_report_is_advisory_not_authority():
    report = what_if(_template(), [SampleAction("write_file", RiskLevel.LOW,
                                                {"path": "clients/acme/a.py"})])
    d = report.to_dict()
    assert d["is_advisory"] is True and d["grants_authority"] is False


# --- creation goes through the one door -------------------------------------------

def test_to_proposal_is_one_door_payload_not_direct_creation():
    payload = _template().to_proposal()
    assert payload["kind"] == "act"                    # a proposal, not an executed creation
    assert payload["tool"] == "corp_create_environment"
    assert payload["args"]["client_name"] == "Acme"
    assert payload["args"]["scope"]["paths"] == ["clients/acme/"]
    assert "rationale" in payload and "expected_effect" in payload


def test_to_proposal_creates_nothing_by_itself():
    tmpl = _template()
    # Calling to_proposal twice yields an identical payload — pure, no side effects.
    assert tmpl.to_proposal() == tmpl.to_proposal()
