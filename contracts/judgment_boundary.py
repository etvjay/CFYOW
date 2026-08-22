# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class Milestone:
    specification: str
    evidence: str
    evaluated: bool
    satisfied: bool
    score: u256
    rationale: str


class JudgmentBoundary(gl.Contract):
    milestones: TreeMap[str, Milestone]

    def __init__(self):
        pass

    def _evaluate(self, specification: str, evidence: str) -> dict:
        def leader_fn():
            prompt = f"""
You are evaluating whether submitted evidence substantially satisfies a written milestone specification.

Specification:
<specification>{specification}</specification>

Evidence:
<evidence>{evidence}</evidence>

Return JSON only with exactly these fields:
{{
  "satisfied": true or false,
  "score": integer from 0 to 100,
  "rationale": "brief evidence-grounded explanation"
}}

Rules:
- Judge only against the written specification and supplied evidence.
- Do not invent missing evidence.
- `satisfied` means the evidence substantially satisfies the specification as a whole.
- A score below 70 must be `satisfied: false`.
- A score of 70 or above may be `satisfied: true` only when no material requirement is missing.
"""
            response = gl.nondet.exec_prompt(prompt, response_format="json")
            return response

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False

            validator_result = leader_fn()
            leader_data = leader_result.calldata

            if not isinstance(leader_data, dict) or not isinstance(validator_result, dict):
                return False

            leader_satisfied = bool(leader_data.get("satisfied", False))
            validator_satisfied = bool(validator_result.get("satisfied", False))
            if leader_satisfied != validator_satisfied:
                return False

            leader_score = int(leader_data.get("score", -1))
            validator_score = int(validator_result.get("score", -1))
            if leader_score < 0 or leader_score > 100:
                return False
            if validator_score < 0 or validator_score > 100:
                return False

            # Compare coarse score buckets rather than demanding identical subjective scores.
            return (leader_score // 10) == (validator_score // 10)

        return gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

    @gl.public.write
    def register_milestone(self, milestone_id: str, specification: str, evidence: str) -> None:
        if milestone_id in self.milestones:
            raise gl.vm.UserError("Milestone already exists")
        if not milestone_id or not specification or not evidence:
            raise gl.vm.UserError("Milestone id, specification, and evidence are required")

        self.milestones[milestone_id] = Milestone(
            specification=specification,
            evidence=evidence,
            evaluated=False,
            satisfied=False,
            score=0,
            rationale="",
        )

    @gl.public.write
    def evaluate_milestone(self, milestone_id: str) -> None:
        if milestone_id not in self.milestones:
            raise gl.vm.UserError("Milestone not found")

        milestone = self.milestones[milestone_id]
        if milestone.evaluated:
            raise gl.vm.UserError("Milestone already evaluated")

        result = self._evaluate(milestone.specification, milestone.evidence)
        score = int(result["score"])
        satisfied = bool(result["satisfied"])

        if score < 0 or score > 100:
            raise gl.vm.UserError("Invalid score")
        if score < 70 and satisfied:
            raise gl.vm.UserError("Inconsistent judgment")

        milestone.evaluated = True
        milestone.satisfied = satisfied
        milestone.score = score
        milestone.rationale = str(result.get("rationale", ""))

    @gl.public.view
    def get_milestone(self, milestone_id: str) -> dict:
        milestone = self.milestones[milestone_id]
        return {
            "specification": milestone.specification,
            "evidence": milestone.evidence,
            "evaluated": milestone.evaluated,
            "satisfied": milestone.satisfied,
            "score": milestone.score,
            "rationale": milestone.rationale,
        }
