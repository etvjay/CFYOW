from dataclasses import dataclass
from typing import Callable, Mapping, Any


@dataclass(frozen=True)
class CentralizedDecision:
    satisfied: bool
    score: int
    rationale: str
    judgment_location: str = "central_adjudicator"


def evaluate_with_adjudicator(
    specification: str,
    evidence: str,
    adjudicator: Callable[[str, str], Mapping[str, Any]],
) -> CentralizedDecision:
    """Resolve free-form evidence through one trusted adjudicator.

    The adjudicator can be an LLM, human, service, or committee API. The important
    property for EXP-001 is architectural: one authority returns the decision that
    downstream state accepts.
    """
    if not specification or not evidence:
        raise ValueError("specification and evidence are required")

    raw = adjudicator(specification, evidence)
    satisfied = bool(raw["satisfied"])
    score = int(raw["score"])
    rationale = str(raw.get("rationale", ""))

    if score < 0 or score > 100:
        raise ValueError("score must be between 0 and 100")
    if score < 70 and satisfied:
        raise ValueError("inconsistent judgment: satisfied requires score >= 70")

    return CentralizedDecision(
        satisfied=satisfied,
        score=score,
        rationale=rationale,
    )
