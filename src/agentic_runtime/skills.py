"""
skills.py — The Procedural Skill Library (L4) + Capability lifecycle.

This is the Voyager primitive (Wang et al., arXiv:2305.16291) and the heart of
the Agent Maturation Loop (Hrvoje §10): successful trajectories are compiled
into reusable, vector-indexed skills so the entity gets cheaper/faster/more
reliable over time WITHOUT retraining the model.

Capability lifecycle state machine (Hrvoje §11):
    OBSERVED -> REPEATED -> CANDIDATE -> TESTED -> APPROVED -> ACTIVE
             -> OPTIMIZED -> REFLEX

REFLEX — corrected from the doc. A reflex is NOT "act without thinking." It is a
CACHED VERIFIED PLAN that skips the *planning LLM call only*. It STILL goes
through policy + sandbox + verify on every use. And it carries an
`environment_signature`; if the current environment's signature has drifted from
the one under which the skill was verified, the reflex is DEMOTED back to ACTIVE
and the entity must re-plan. This kills the "silently broken reflex" failure.
"""
from __future__ import annotations

import json
from typing import Optional

from .core_types import (CapabilityState, CommandEnvelope, SkillCandidate,
                         new_id, now, sha)
from .memory import Embedder, HashingEmbedder, cosine


# thresholds for promotion
REPEAT_FOR_CANDIDATE = 2     # successes before it becomes a candidate
SUCCESS_RATE_FOR_REFLEX = 0.95
USES_FOR_REFLEX = 5


def environment_signature(observation_artifacts: dict) -> str:
    """A coarse fingerprint of the environment a skill ran against (e.g. the set
    of files touched + their roles). Drift here invalidates a reflex."""
    keys = sorted(observation_artifacts.get("fs_diff", {}).keys())
    return sha(json.dumps(keys))


class SkillLibrary:
    def __init__(self, embedder: Optional[Embedder] = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self._skills: dict[str, SkillCandidate] = {}
        self._index: dict[str, list[float]] = {}  # skill_id -> embedding

    # ---- compilation from a successful trajectory --------------------- #
    def observe_success(self, name: str, description: str,
                        commands: list[CommandEnvelope],
                        env_sig: str, cost: dict) -> SkillCandidate:
        """Either create a new OBSERVED candidate or reinforce an existing one.
        Matching is by semantic similarity of the description (Voyager: key =
        embedding of the program description)."""
        emb = self.embedder.embed(description)
        match = self._nearest(emb, threshold=0.92)
        action_sequence = [{"tool": c.tool, "args_template": c.args,
                            "expected_effect": c.expected_effect}
                           for c in commands]
        if match:
            sk = self._skills[match]
            sk.success_count += 1
            sk.last_verified = now()
            sk.environment_signature = env_sig
            self._maybe_promote(sk)
            return sk

        sk = SkillCandidate(
            id=new_id("skill"), name=name, description=description,
            action_sequence=action_sequence,
            required_tools=sorted({c.tool for c in commands}),
            required_permissions=sorted({c.tool for c in commands}),
            input_schema={}, output_schema={}, environment_signature=env_sig,
            cost_profile=cost, state=CapabilityState.OBSERVED)
        self._skills[sk.id] = sk
        self._index[sk.id] = emb
        return sk

    def observe_failure(self, skill_id: str, reason: str) -> None:
        sk = self._skills.get(skill_id)
        if sk:
            sk.failure_count += 1
            sk.known_failures.append(reason)
            # a reflex that fails is demoted immediately
            if sk.state is CapabilityState.REFLEX:
                sk.state = CapabilityState.ACTIVE

    # ---- promotion state machine -------------------------------------- #
    def _maybe_promote(self, sk: SkillCandidate) -> None:
        s = sk.state
        if s is CapabilityState.OBSERVED and sk.success_count >= REPEAT_FOR_CANDIDATE:
            sk.state = CapabilityState.REPEATED
        if s is CapabilityState.REPEATED:
            sk.state = CapabilityState.CANDIDATE
        # CANDIDATE -> TESTED -> APPROVED -> ACTIVE handled by promote_tested()
        if (sk.state is CapabilityState.ACTIVE
                and sk.success_count >= USES_FOR_REFLEX
                and sk.success_rate >= SUCCESS_RATE_FOR_REFLEX):
            sk.state = CapabilityState.REFLEX

    def promote_tested(self, skill_id: str, passed: bool) -> None:
        """Called after a candidate's test_suite runs in the sandbox."""
        sk = self._skills[skill_id]
        if sk.state is CapabilityState.CANDIDATE and passed:
            sk.state = CapabilityState.APPROVED
        if sk.state is CapabilityState.APPROVED:
            sk.state = CapabilityState.ACTIVE

    # ---- retrieval (Voyager top-k by description similarity) ---------- #
    def _nearest(self, emb: list[float], threshold: float) -> Optional[str]:
        best, best_score = None, threshold
        for sid, e in self._index.items():
            sc = cosine(emb, e)
            if sc > best_score:
                best, best_score = sid, sc
        return best

    def retrieve(self, task_description: str, k: int = 5) -> list[SkillCandidate]:
        emb = self.embedder.embed(task_description)
        scored = [(cosine(emb, e), self._skills[sid])
                  for sid, e in self._index.items()]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for sc, s in scored[:k] if sc > 0.3]

    # ---- reflex retrieval with DRIFT-CHECK (the corrected reflex) ------ #
    def find_reflex(self, task_description: str,
                    current_env_sig: str) -> Optional[SkillCandidate]:
        for sk in self.retrieve(task_description, k=3):
            if sk.state is CapabilityState.REFLEX:
                if sk.environment_signature == current_env_sig:
                    return sk
                # DRIFT: environment changed since verification -> demote, re-plan
                sk.state = CapabilityState.ACTIVE
                sk.known_failures.append("reflex demoted: environment drift")
        return None

    def all(self) -> list[SkillCandidate]:
        return list(self._skills.values())

    def stats(self) -> dict:
        by_state: dict[str, int] = {}
        for sk in self._skills.values():
            by_state[sk.state.value] = by_state.get(sk.state.value, 0) + 1
        return {"count": len(self._skills), "by_state": by_state}
