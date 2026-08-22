from experiment_ledger.adapters.genlayer_children import (
    capture_child_lineage,
    count_recipient_deliveries,
)


class FakeClient:
    def __init__(self):
        self.transactions = {
            "0xparent": {
                "messages": [
                    {
                        "messageType": 1,
                        "recipient": "0xAAA",
                        "value": 0,
                        "data": "0x01",
                        "onAcceptance": True,
                        "saltNonce": 0,
                    },
                    {
                        "messageType": 1,
                        "recipient": "0xBBB",
                        "value": 0,
                        "data": "0x02",
                        "onAcceptance": False,
                        "saltNonce": 0,
                    },
                ]
            },
            "0xchild1": {"status": "FINALIZED"},
            "0xchild2": {"status": "FINALIZED"},
        }

    def get_transaction(self, transaction_hash):
        return self.transactions[transaction_hash]

    def get_triggered_transaction_ids(self, transaction_hash):
        assert transaction_hash == "0xparent"
        return ["0xchild1", "0xchild2"]


def test_capture_child_lineage_records_messages_and_children():
    lineage = capture_child_lineage(FakeClient(), "0xparent")

    assert lineage["message_count"] == 2
    assert lineage["accepted_message_count"] == 1
    assert lineage["finalized_message_count"] == 1
    assert lineage["triggered_transaction_ids"] == ["0xchild1", "0xchild2"]
    assert lineage["triggered_transaction_count"] == 2
    assert [c["transaction_hash"] for c in lineage["children"]] == [
        "0xchild1",
        "0xchild2",
    ]


def test_recipient_delivery_count_is_timing_aware():
    lineage = capture_child_lineage(FakeClient(), "0xparent")

    assert count_recipient_deliveries(lineage, "0xaaa") == {
        "emitted_to_recipient": 1,
        "accepted_timing": 1,
        "finalized_timing": 0,
    }
    assert count_recipient_deliveries(lineage, "0xbbb") == {
        "emitted_to_recipient": 1,
        "accepted_timing": 0,
        "finalized_timing": 1,
    }
