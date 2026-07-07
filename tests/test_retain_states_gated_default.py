"""P0-S.3 — retain_states defaults ON only for declared gated entity classes.

Writers (CORE / EXECUTION) get content-addressed state retention by default so
forking / rollback / materialize-to-live work out of the box; every other class
stays byte-identical to the pre-P0-S.3 default (retention OFF, no state store).
Explicit retain_states always wins.
"""
from __future__ import annotations

from agentic_runtime import (
    RETAIN_STATES_GATED_CLASSES,
    AgentClass,
    UnsafeLocalSandbox,
    build_runtime,
)


def _kernel(tmp_path, **kw):
    return build_runtime(
        sandbox=UnsafeLocalSandbox(root=str(tmp_path / "ws")),
        trace_backend="memory", trace_dir=str(tmp_path / "traces"), **kw)


def test_ungated_default_is_byte_identical(tmp_path):
    k = _kernel(tmp_path)  # no entity_class, no retain_states
    assert k.runtime._retain_states is False
    assert k.runtime._state_store is None


def test_research_class_is_not_gated(tmp_path):
    k = _kernel(tmp_path, entity_class=AgentClass.RESEARCH)
    assert k.runtime._retain_states is False
    assert k.runtime._state_store is None


def test_execution_class_retains_and_provisions_store(tmp_path):
    k = _kernel(tmp_path, entity_class=AgentClass.EXECUTION)
    assert k.runtime._retain_states is True
    assert k.runtime._state_store is not None  # factory provisioned it


def test_core_class_retains_by_default(tmp_path):
    k = _kernel(tmp_path, entity_class=AgentClass.CORE)
    assert k.runtime._retain_states is True


def test_explicit_off_overrides_gate(tmp_path):
    k = _kernel(tmp_path, entity_class=AgentClass.EXECUTION, retain_states=False)
    assert k.runtime._retain_states is False
    assert k.runtime._state_store is None


def test_explicit_on_overrides_ungated(tmp_path):
    k = _kernel(tmp_path, entity_class=AgentClass.RESEARCH, retain_states=True)
    assert k.runtime._retain_states is True
    assert k.runtime._state_store is not None


def test_gated_set_is_exactly_the_writers():
    assert AgentClass.EXECUTION in RETAIN_STATES_GATED_CLASSES
    assert AgentClass.CORE in RETAIN_STATES_GATED_CLASSES
    for c in (AgentClass.RESEARCH, AgentClass.CRITIC,
              AgentClass.MEMORY, AgentClass.POLICY):
        assert c not in RETAIN_STATES_GATED_CLASSES
