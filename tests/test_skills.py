"""Skill reflex drift tests."""

from agentic_runtime.core_types import CapabilityState, CommandEnvelope, RiskLevel
from agentic_runtime.skills import SkillLibrary, environment_signature


def _cmd(tool, args):
    return CommandEnvelope.make("card_x", tool, args, "r", RiskLevel.LOW, "fx")


def test_reflex_demotes_on_environment_drift():
    lib = SkillLibrary()
    cmds = [_cmd("read_file", {"path": "a.py"})]
    sig_a = environment_signature({"fs_diff": {"a.py": ""}})
    sig_b = environment_signature({"fs_diff": {"b.py": ""}})
    sk = lib.observe_success("fix bug", "fix bug in a.py", cmds, sig_a, {})
    sk.state = CapabilityState.REFLEX
    sk.success_count = 10
    hit = lib.find_reflex("fix bug", sig_a)
    assert hit is not None
    assert hit.state is CapabilityState.REFLEX
    miss = lib.find_reflex("fix bug", sig_b)
    assert miss is None
    assert sk.state is CapabilityState.ACTIVE
    assert any("drift" in f for f in sk.known_failures)
