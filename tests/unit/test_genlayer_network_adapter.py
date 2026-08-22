from experiment_ledger.adapters.genlayer_network import (
    capture_transaction_lifecycle,
    derive_consensus_observations,
    summarize_rounds,
)


class FakeClient:
    def __init__(self):
        self.statuses = iter(
            [
                {"status": "PENDING", "statusCode": 1},
                {"status": "PROPOSING", "statusCode": 2},
                {"status": "ACCEPTED", "statusCode": 5},
                {"status": "APPEAL_COMMITTING", "statusCode": 10},
                {"status": "FINALIZED", "statusCode": 7},
            ]
        )

    def transaction_status(self, tx_hash):
        return next(self.statuses)

    def transaction_receipt(self, tx_hash):
        return {
            "numOfInitialValidators": 5,
            "txExecutionHash": "0xexec",
            "result": 0,
            "timestamps": {"AppealSubmitted": 123},
            "roundData": [
                {
                    "round": 0,
                    "leaderIndex": 1,
                    "votesCommitted": 5,
                    "votesRevealed": 5,
                    "appealBond": 0,
                    "rotationsLeft": 1,
                    "result": 1,
                    "roundValidators": ["a", "b", "c", "d", "e"],
                    "validatorVotesHash": ["v1", "v2", "v3", "v4", "v5"],
                    "validatorResultHash": ["r1", "r2", "r3", "r4", "r5"],
                },
                {
                    "round": 1,
                    "leaderIndex": 2,
                    "votesCommitted": 5,
                    "votesRevealed": 5,
                    "appealBond": 10,
                    "rotationsLeft": 0,
                    "result": 1,
                    "roundValidators": ["f", "g", "h", "i", "j"],
                    "validatorVotesHash": ["v6", "v7", "v8", "v9", "v10"],
                    "validatorResultHash": ["r6", "r7", "r8", "r9", "r10"],
                },
            ],
        }

    def contract_state(self, address, status):
        return f"0x{status}"


def test_summarize_rounds_preserves_public_consensus_metadata():
    receipt = FakeClient().transaction_receipt("0x1")
    rounds = summarize_rounds(receipt)
    assert len(rounds) == 2
    assert rounds[0]["validator_count"] == 5
    assert rounds[1]["appeal_bond"] == 10


def test_derive_consensus_observations_does_not_invent_private_reasoning():
    receipt = FakeClient().transaction_receipt("0x1")
    history = [
        {"status": "ACCEPTED"},
        {"status": "APPEAL_COMMITTING"},
        {"status": "FINALIZED"},
    ]
    result = derive_consensus_observations(history, receipt)
    assert result["appeal_observed"] is True
    assert result["reexecution_or_additional_round_observed"] is True
    assert "validator_private_reasoning" in result["unavailable"]


def test_capture_transaction_lifecycle_records_status_path_and_state(monkeypatch):
    monkeypatch.setattr("experiment_ledger.adapters.genlayer_network.time.sleep", lambda _: None)
    result = capture_transaction_lifecycle(
        "http://unused",
        "0xtx",
        contract_address="0xcontract",
        poll_interval_s=0,
        max_polls=10,
        client=FakeClient(),
    )
    assert result["status"] == "SUCCESS"
    assert result["consensus"]["status_path"] == [
        "PENDING",
        "PROPOSING",
        "ACCEPTED",
        "APPEAL_COMMITTING",
        "FINALIZED",
    ]
    assert result["state_snapshots"]["accepted"] == "0xaccepted"
    assert result["state_snapshots"]["finalized"] == "0xfinalized"
