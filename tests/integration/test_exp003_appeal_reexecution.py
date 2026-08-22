"""EXP-003 appeal/re-execution evidence test.

This test deliberately stops the parent transaction at ACCEPTED, submits an appeal,
waits through the next decision/finality path, then records parent/child/sink evidence.

The test targets duplicate provisional delivery first. It does not claim an overturned
semantic result unless the captured final state actually differs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from gltest import get_validator_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedLLMResponse, TransactionStatus

from experiment_ledger.adapters.exp003_consequence import normalize_consequence_stability
from experiment_ledger.adapters.genlayer_appeal import resolve_appeal_bond
from experiment_ledger.adapters.genlayer_children import capture_child_lineage
from tests.integration._contract_factory_compat import contract_factory_from_source

pytestmark = pytest.mark.integration

ARTIFACT_DIR = Path("artifacts/EXP-003")


def _tx_id(receipt: dict) -> str:
    for key in ("id", "transaction_hash", "transactionHash", "hash", "tx_id"):
        value = receipt.get(key)
        if value:
            return str(value)
    raise AssertionError(f"transaction id not found in receipt keys: {sorted(receipt.keys())}")


def _write_artifact(name: str, payload: dict) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / name).write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def test_appeal_reexecution_captures_provisional_duplicate_evidence(gl_client):
    sink_factory = contract_factory_from_source(
        "ConsequenceSink", "contracts/consequence_sink.py"
    )
    provisional_sink = sink_factory.deploy()
    settled_sink = sink_factory.deploy()

    parent_factory = contract_factory_from_source(
        "ConsequenceParent", "contracts/consequence_parent.py"
    )
    parent = parent_factory.deploy(args=[provisional_sink.address, settled_sink.address])

    mock_response: MockedLLMResponse = {
        "nondet_exec_prompt": {
            "Decide whether the evidence substantially satisfies": '{"satisfied": true}'
        }
    }
    validators = get_validator_factory().batch_create_mock_validators(
        count=5,
        mock_llm_response=mock_response,
    )
    context = {"validators": [validator.to_dict() for validator in validators]}

    receipt = parent.resolve_case(
        args=[
            "case-appeal-duplicate",
            "Deliver a working JSON health endpoint.",
            "The deployed service returns HTTP 200 and JSON {status: ok} at /health.",
        ]
    ).transact(
        transaction_context=context,
        wait_transaction_status=TransactionStatus.ACCEPTED,
        wait_triggered_transactions=True,
        wait_triggered_transactions_status=TransactionStatus.ACCEPTED,
    )
    assert tx_execution_succeeded(receipt)

    parent_tx = _tx_id(receipt)
    override = os.getenv("EXP003_APPEAL_VALUE") or None
    try:
        bond = resolve_appeal_bond(gl_client, parent_tx, override=override)
    except Exception as exc:
        _write_artifact(
            "appeal-duplicate-failure.json",
            {
                "status": "INVALID_RUN",
                "phase": "appeal_bond_resolution",
                "parent_transaction_hash": parent_tx,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "appeal_override": override,
            },
        )
        raise

    before_appeal = {
        "parent_receipt": receipt,
        "parent_lineage": capture_child_lineage(gl_client, parent_tx),
        "provisional": provisional_sink.get_record(args=["case-appeal-duplicate"]).call(),
        "settled": settled_sink.get_record(args=["case-appeal-duplicate"]).call(),
        "appeal_bond": bond.to_dict(),
    }
    _write_artifact("appeal-duplicate-before.json", before_appeal)

    try:
        appealed_receipt = parent.appeal(
            parent_tx,
            value=bond.value,
            wait_until="finalized",
            wait_retries=60,
        )
    except Exception as exc:
        _write_artifact(
            "appeal-duplicate-failure.json",
            {
                "status": "INVALID_RUN",
                "phase": "appeal",
                "parent_transaction_hash": parent_tx,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "appeal_bond": bond.to_dict(),
            },
        )
        if os.getenv("EXP003_REQUIRE_APPEAL", "0") == "1":
            raise
        pytest.skip(f"appeal unavailable in this environment: {exc}")

    after_appeal = {
        "status": "SUCCESS",
        "parent_transaction_hash": parent_tx,
        "appealed_receipt": appealed_receipt,
        "parent_lineage": capture_child_lineage(gl_client, parent_tx),
        "provisional": provisional_sink.get_record(args=["case-appeal-duplicate"]).call(),
        "settled": settled_sink.get_record(args=["case-appeal-duplicate"]).call(),
        "appeal_bond": bond.to_dict(),
    }
    _write_artifact("appeal-duplicate-after.json", after_appeal)

    metrics = normalize_consequence_stability(
        before_appeal,
        after_appeal,
        final_judgment_satisfied=True,
    )
    metrics["parent_transaction_hash"] = parent_tx
    metrics["appeal_bond"] = bond.to_dict()
    _write_artifact("appeal-duplicate-metrics.json", metrics)

    assert tx_execution_succeeded(appealed_receipt)
    assert after_appeal["provisional"]["applied"] is True
    assert after_appeal["settled"]["applied"] is True

    # The main measured variable. A duplicate is evidence only if the network actually
    # re-delivered the accepted child; we do not force the assertion to be > 0 here.
    assert metrics["metrics"]["provisional_duplicate_delta"] >= 0
    assert metrics["metrics"]["settled_duplicate_delta"] >= 0
    assert metrics["interpretation"]["status"] == "UNREVIEWED"
