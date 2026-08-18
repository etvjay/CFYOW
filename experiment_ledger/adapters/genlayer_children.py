"""Child-transaction lineage capture through the documented GenLayerPY SDK.

This module deliberately accepts an already-created SDK client. Network selection,
accounts, and credentials remain caller concerns. The adapter only records the
public transaction/message lineage exposed by GenLayerPY.
"""

from __future__ import annotations

from typing import Any


def capture_child_lineage(client: Any, transaction_hash: str) -> dict[str, Any]:
    """Capture messages and triggered child transaction IDs for one parent tx."""
    transaction = client.get_transaction(transaction_hash=transaction_hash)
    child_ids = client.get_triggered_transaction_ids(transaction_hash=transaction_hash)

    messages = []
    if isinstance(transaction, dict):
        messages = list(transaction.get("messages", []) or [])

    children = []
    for child_id in child_ids or []:
        child_tx = client.get_transaction(transaction_hash=child_id)
        children.append({
            "transaction_hash": child_id,
            "transaction": child_tx,
        })

    accepted_messages = [
        message for message in messages if bool(message.get("onAcceptance", False))
    ]
    finalized_messages = [
        message for message in messages if not bool(message.get("onAcceptance", False))
    ]

    return {
        "parent_transaction_hash": transaction_hash,
        "messages": messages,
        "message_count": len(messages),
        "accepted_message_count": len(accepted_messages),
        "finalized_message_count": len(finalized_messages),
        "triggered_transaction_ids": list(child_ids or []),
        "triggered_transaction_count": len(child_ids or []),
        "children": children,
        "observation_boundary": {
            "source": "GenLayerPY public client methods",
            "does_not_infer": [
                "semantic equivalence between two different child transactions",
                "whether a repeated child is harmful",
                "why a parent was re-executed",
            ],
        },
    }


def count_recipient_deliveries(lineage: dict[str, Any], recipient: str) -> dict[str, int]:
    """Count emitted messages directed at a recipient; does not infer execution success."""
    normalized = recipient.lower()
    messages = lineage.get("messages", []) or []
    matching = [
        message
        for message in messages
        if str(message.get("recipient", "")).lower() == normalized
    ]
    return {
        "emitted_to_recipient": len(matching),
        "accepted_timing": sum(1 for message in matching if message.get("onAcceptance")),
        "finalized_timing": sum(1 for message in matching if not message.get("onAcceptance")),
    }
