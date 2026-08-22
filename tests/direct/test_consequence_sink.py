def test_first_consequence_applies_once(direct_deploy):
    sink = direct_deploy("contracts/consequence_sink.py")

    sink.record_consequence("case-1", "satisfied")

    record = sink.get_record("case-1")
    assert record["exists"] is True
    assert record["attempts"] == 1
    assert record["duplicate_count"] == 0
    assert record["applied"] is True
    assert record["payload"] == "satisfied"

    totals = sink.get_totals()
    assert totals["total_attempts"] == 1
    assert totals["unique_applied"] == 1
    assert totals["duplicate_attempts"] == 0


def test_duplicate_delivery_is_observed_but_not_reapplied(direct_deploy):
    sink = direct_deploy("contracts/consequence_sink.py")

    sink.record_consequence("case-1", "satisfied")
    sink.record_consequence("case-1", "satisfied")
    sink.record_consequence("case-1", "satisfied")

    record = sink.get_record("case-1")
    assert record["attempts"] == 3
    assert record["duplicate_count"] == 2
    assert record["applied"] is True

    totals = sink.get_totals()
    assert totals["total_attempts"] == 3
    assert totals["unique_applied"] == 1
    assert totals["duplicate_attempts"] == 2


def test_distinct_case_ids_apply_independently(direct_deploy):
    sink = direct_deploy("contracts/consequence_sink.py")

    sink.record_consequence("case-1", "satisfied")
    sink.record_consequence("case-2", "satisfied")

    totals = sink.get_totals()
    assert totals["total_attempts"] == 2
    assert totals["unique_applied"] == 2
    assert totals["duplicate_attempts"] == 0


def test_missing_case_returns_zero_record(direct_deploy):
    sink = direct_deploy("contracts/consequence_sink.py")

    assert sink.get_record("missing") == {
        "exists": False,
        "attempts": 0,
        "duplicate_count": 0,
        "applied": False,
        "payload": "",
        "first_sender": "",
    }
