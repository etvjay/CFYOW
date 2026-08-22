"""Adapters that normalize CFYOW EXP-001 baselines into ledger results."""

from dataclasses import asdict

from baselines.centralized import evaluate_with_adjudicator
from baselines.deterministic import evaluate_attestation


def run_deterministic(scenario: dict) -> dict:
    decision = evaluate_attestation(scenario["structured_attestation"])
    return asdict(decision)


def run_centralized(scenario: dict) -> dict:
    adjudicated = scenario["centralized_decision"]

    def fixture_adjudicator(_specification: str, _evidence: str) -> dict:
        return adjudicated

    decision = evaluate_with_adjudicator(
        scenario["specification"],
        scenario["evidence"],
        fixture_adjudicator,
    )
    return asdict(decision)
