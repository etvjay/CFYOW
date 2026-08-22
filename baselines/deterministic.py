from dataclasses import dataclass


@dataclass(frozen=True)
class DeterministicDecision:
    satisfied: bool
    passed_requirements: int
    total_requirements: int
    judgment_location: str = "upstream_attestor"


def evaluate_attestation(requirements: dict[str, bool]) -> DeterministicDecision:
    """Resolve a milestone from already-structured trusted facts.

    This baseline intentionally does *not* interpret free-form evidence. Someone or
    something upstream must first convert ambiguous evidence into booleans. The
    function shows where deterministic logic begins and where judgment was moved.
    """
    if not requirements:
        raise ValueError("at least one requirement is required")
    if any(type(value) is not bool for value in requirements.values()):
        raise TypeError("all requirement attestations must be booleans")

    passed = sum(1 for value in requirements.values() if value)
    return DeterministicDecision(
        satisfied=passed == len(requirements),
        passed_requirements=passed,
        total_requirements=len(requirements),
    )
