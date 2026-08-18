from experiment_ledger.adapters.exp003_consequence import normalize_consequence_stability


def test_normalizer_reports_duplicate_delta_without_interpreting_it():
    before = {
        "provisional": {"attempts": 1, "duplicate_count": 0, "applied": True},
        "settled": {"attempts": 0, "duplicate_count": 0, "applied": False},
        "parent_lineage": {"triggered_transaction_count": 1},
    }
    after = {
        "provisional": {"attempts": 2, "duplicate_count": 1, "applied": True},
        "settled": {"attempts": 1, "duplicate_count": 0, "applied": True},
        "parent_lineage": {"triggered_transaction_count": 3},
    }

    result = normalize_consequence_stability(
        before, after, final_judgment_satisfied=True
    )

    metrics = result["metrics"]
    assert metrics["provisional_attempt_delta"] == 1
    assert metrics["provisional_duplicate_delta"] == 1
    assert metrics["settled_attempt_delta"] == 1
    assert metrics["triggered_child_count_delta"] == 2
    assert metrics["provisional_duplicate_observed"] is True
    assert metrics["stale_provisional_consequence_observed"] is False
    assert result["interpretation"]["status"] == "UNREVIEWED"


def test_stale_consequence_requires_explicit_negative_final_judgment():
    evidence = {
        "provisional": {"attempts": 1, "duplicate_count": 0, "applied": True},
        "settled": {"attempts": 0, "duplicate_count": 0, "applied": False},
        "parent_lineage": {"triggered_transaction_count": 1},
    }

    unknown = normalize_consequence_stability(evidence, evidence)
    overturned = normalize_consequence_stability(
        evidence, evidence, final_judgment_satisfied=False
    )

    assert unknown["metrics"]["stale_provisional_consequence_observed"] is None
    assert overturned["metrics"]["stale_provisional_consequence_observed"] is True
