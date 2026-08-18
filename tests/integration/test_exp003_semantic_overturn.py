"""EXP-003 semantic-overturn evidence test.

This test uses a mutable public GitHub issue as the external evidence source.
It resets the fixture to SATISFIED, submits one transaction and waits until
ACCEPTED, mutates the same evidence source to REVOKED, then appeals the same
transaction and records whether the provisional consequence survives while the
finalized consequence is absent.

The test does not change transaction calldata, contract code, or validator mocks
between rounds. Only the external evidence changes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import requests
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus

from experiment_ledger.adapters.exp003_consequence import normalize_exp003_run
from experiment_ledger.adapters.genlayer_appeal import resolve_appeal_bond
from experiment_ledger.adapters.genlayer_children import capture_child_lineage

pytestmark = pytest.mark.integration

ARTIFACT_DIR = Path("artifacts/EXP-003")
ISSUE_API = "https://api.github.com/repos/etvjay/CFYOW/issues/3"
CASE_ID = "case-semantic-overturn"

SATISFIED_BODY = """CFYOW controlled external-evidence fixture.

EVIDENCE_STATUS: SATISFIED

The deployed service returns HTTP 200 and JSON `{ \"status\": \"ok\" }` at `/health`.

This issue is mutated by the EXP-003 semantic-overturn workflow between initial ACCEPTED state and appeal re-execution. It is an experimental fixture, not a product issue.
"""

REVOKED_BODY = """CFYOW controlled external-evidence fixture.

EVIDENCE_STATUS: REVOKED

The previously reported `/health` endpoint is no longer available and the milestone should not be treated as satisfied under the current evidence.

This issue is mutated by the EXP-003 semantic-overturn workflow between initial ACCEPTED state and appeal re-execution. It is an experimental fixture, not a product issue.
"""


def _tx_id(receipt: dict) -> str:
    for key in ("id", "transaction_hash", "transactionHash", "hash"):
        value = receipt.get(key)
        if value:
            return str(value)
    raise AssertionError(f"transaction id not found in receipt keys: {sorted(receipt.keys())}")


def _write(name: str, payload: dict) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / name).write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _set_fixture(body: str) -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        pytest.skip("GH_TOKEN/GITHUB_TOKEN required to mutate EXP-003 evidence fixture")

    response = requests.patch(
        ISSUE_API,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "CFYOW-EXP003",
        },
        json={"body": body},
        timeout=20,
    )
    response.raise_for_status()


def test_semantic_overturn_can_leave_provisional_consequence(gl_client):
    _set_fixture(SATISFIED_BODY)

    sink_factory = get_contract_factory("ConsequenceSink")
    provisional_sink = sink_factory.deploy()
    settled_sink = sink_factory.deploy()

    parent_factory = get_contract_factory("ConsequenceEvidenceParent")
    parent = parent_factory.deploy(args=[provisional_sink.address, settled_sink.address])

    receipt = parent.resolve_case(
        args=[
            CASE_ID,
            "The service must currently expose a working JSON health endpoint at /health.",
            ISSUE_API,
        ]
    ).transact(
        wait_transaction_status=TransactionStatus.ACCEPTED,
        wait_triggered_transactions=True,
        wait_triggered_transactions_status=TransactionStatus.ACCEPTED,
        wait_retries=60,
    )
    assert tx_execution_succeeded(receipt)

    parent_tx = _tx_id(receipt)
    override = os.getenv("EXP003_APPEAL_VALUE") or None
    try:
        bond = resolve_appeal_bond(gl_client, parent_tx, override=override)
    except Exception as exc:
        _write(
            "semantic-overturn-failure.json",
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

    before = {
        "status": "ACCEPTED_CAPTURED",
        "parent_transaction_hash": parent_tx,
        "parent_receipt": receipt,
        "parent_lineage": capture_child_lineage(gl_client, parent_tx),
        "provisional": provisional_sink.get_record(args=[CASE_ID]).call(),
        "settled": settled_sink.get_record(args=[CASE_ID]).call(),
        "evidence_fixture": {"url": ISSUE_API, "body": SATISFIED_BODY},
        "appeal_bond": bond.to_dict(),
    }
    _write("semantic-overturn-before.json", before)

    # External reality changes after ACCEPTED but before appeal re-execution.
    _set_fixture(REVOKED_BODY)

    try:
        appealed_receipt = parent.appeal(
            parent_tx,
            value=bond.value,
            wait_until="finalized",
            wait_retries=60,
        )
    except Exception as exc:
        failure = {
            "status": "INVALID_RUN",
            "phase": "semantic_overturn_appeal",
            "parent_transaction_hash": parent_tx,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "appeal_bond": bond.to_dict(),
            "evidence_fixture_after": {"url": ISSUE_API, "body": REVOKED_BODY},
        }
        _write("semantic-overturn-failure.json", failure)
        if os.getenv("EXP003_REQUIRE_APPEAL", "0") == "1":
            raise
        pytest.skip(f"semantic-overturn appeal unavailable: {exc}")

    settled_record = settled_sink.get_record(args=[CASE_ID]).call()
    after = {
        "status": "SUCCESS",
        "parent_transaction_hash": parent_tx,
        "appealed_receipt": appealed_receipt,
        "parent_lineage": capture_child_lineage(gl_client, parent_tx),
        "provisional": provisional_sink.get_record(args=[CASE_ID]).call(),
        "settled": settled_record,
        "evidence_fixture_after": {"url": ISSUE_API, "body": REVOKED_BODY},
        "appeal_bond": bond.to_dict(),
        # A finalized positive child is emitted only when the final re-execution
        # remains satisfied. Absence of settled application is the app-level signal.
        "final_judgment_satisfied": bool(settled_record.get("applied", False)),
    }
    _write("semantic-overturn-after.json", after)
    metrics = normalize_exp003_run(before, after)
    metrics["appeal_bond"] = bond.to_dict()
    _write("semantic-overturn-metrics.json", metrics)

    assert tx_execution_succeeded(appealed_receipt)
    assert before["provisional"]["applied"] is True

    # The experiment result remains evidence-driven. If settled still applies,
    # the semantic overturn did not reproduce and the metrics must say so.
    assert after["provisional"]["applied"] is True
