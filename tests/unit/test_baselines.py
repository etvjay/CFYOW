import pytest

from baselines.centralized import evaluate_with_adjudicator
from baselines.deterministic import evaluate_attestation


def test_deterministic_baseline_requires_structured_facts():
    result = evaluate_attestation({"responsive": True, "mobile": True, "checkout": False})
    assert result.satisfied is False
    assert result.passed_requirements == 2
    assert result.total_requirements == 3
    assert result.judgment_location == "upstream_attestor"


def test_deterministic_baseline_rejects_free_form_values():
    with pytest.raises(TypeError):
        evaluate_attestation({"responsive": "looks good"})


def test_centralized_baseline_accepts_free_form_judgment_from_one_authority():
    def adjudicator(specification, evidence):
        assert "responsive" in specification.lower()
        assert "mobile" in evidence.lower()
        return {
            "satisfied": True,
            "score": 84,
            "rationale": "Evidence covers the material requirements.",
        }

    result = evaluate_with_adjudicator(
        "Deliver a responsive storefront with mobile checkout.",
        "Demo shows responsive layouts and a completed mobile checkout flow.",
        adjudicator,
    )

    assert result.satisfied is True
    assert result.score == 84
    assert result.judgment_location == "central_adjudicator"


def test_centralized_baseline_enforces_decision_invariants():
    def inconsistent(_specification, _evidence):
        return {"satisfied": True, "score": 40, "rationale": "bad output"}

    with pytest.raises(ValueError, match="inconsistent judgment"):
        evaluate_with_adjudicator("spec", "evidence", inconsistent)
