import pytest

from experiment_ledger.adapters.genlayer_appeal import resolve_appeal_bond


class FakeClient:
    def __init__(self, minimum=125, can_appeal=True):
        self.minimum = minimum
        self.allowed = can_appeal

    def can_appeal(self, transaction_id):
        assert transaction_id == "0xtx"
        return self.allowed

    def get_min_appeal_bond(self, transaction_id):
        assert transaction_id == "0xtx"
        return self.minimum


def test_uses_network_minimum_by_default():
    result = resolve_appeal_bond(FakeClient(), "0xtx")

    assert result.value == 125
    assert result.minimum_bond == 125
    assert result.source == "network_minimum"
    assert result.can_appeal is True


def test_positive_override_must_meet_network_minimum():
    result = resolve_appeal_bond(FakeClient(minimum=125), "0xtx", override="200")

    assert result.value == 200
    assert result.minimum_bond == 125
    assert result.source == "explicit_override"


@pytest.mark.parametrize("override", ["0", "-1"])
def test_nonpositive_override_is_rejected(override):
    with pytest.raises(ValueError, match="positive"):
        resolve_appeal_bond(FakeClient(), "0xtx", override=override)


def test_override_below_minimum_is_rejected():
    with pytest.raises(ValueError, match="below network minimum"):
        resolve_appeal_bond(FakeClient(minimum=125), "0xtx", override="100")


def test_missing_bond_api_is_invalid_instead_of_guessing_zero():
    class OldClient:
        pass

    with pytest.raises(RuntimeError, match="get_min_appeal_bond"):
        resolve_appeal_bond(OldClient(), "0xtx")
