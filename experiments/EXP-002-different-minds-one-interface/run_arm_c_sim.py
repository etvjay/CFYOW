"""EXP-002 arm C — GenLayer direct-mode (simulator) execution.

Runs different_minds_judged.py under gltest direct mode with mocked LLM
validators. This exercises the REAL consensus path (leader proposes,
validator verifies under the equivalence principle) without needing
Bradbury. Evidence is served by the local evidence server; the contract's
nondet web fetch is mocked to return its body.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> dict:
    from gltest import get_contract_factory, get_validator_factory
    from gltest.types import MockedLLMResponse, TransactionStatus

    evidence_body = json.dumps({
        "case": "arm-c-sim",
        "endpoint": "/health",
        "http_status": 200,
        "response_body": '{"status":"ok"}',
        "demonstrates": "live endpoint responded 200 with expected JSON body",
    })

    validators = get_validator_factory().batch_create_mock_validators(
        count=5,
        mock_llm_response=MockedLLMResponse({
            "nondet_exec_prompt": {
                "Decide whether the evidence satisfies": json.dumps({
                    "verdict": "satisfied",
                    "reason": "evidence shows live endpoint returned expected body",
                }),
            },
            "nondet_web_get": {
                "http://localhost:8765/evidence/arm-c-sim": evidence_body,
            },
        }),
    )
    context = {"validators": [v.to_dict() for v in validators]}

    factory = get_contract_factory("DifferentMindsJudged")
    contract = factory.deploy(args=["requester-address"])

    contract.open_workflow(
        args=["provider-address", "Deliver a JSON health endpoint returning HTTP 200"],
    ).transact(transaction_context=context)
    contract.propose(args=["deliver per objective, /health JSON"]).transact(
        transaction_context=context)
    contract.accept(args=[]).transact(transaction_context=context)
    contract.commit(args=["deadbeef"]).transact(transaction_context=context)
    contract.submit_evidence(
        args=["http://localhost:8765/evidence/arm-c-sim"]
    ).transact(transaction_context=context)

    # THE consensus step — leader/validator rounds run here
    receipt = contract.evaluate_consensus(args=[]).transact(
        transaction_context=context)

    state = contract.get_state(args=[]).call()
    return {
        "arm": "C_genlayer_optimistic_democracy",
        "mode": "direct_simulator",
        "outcome": state.get("settled_outcome") or "pre_settle",
        "verdict": state.get("evaluation_verdict"),
        "phase": state.get("phase"),
        "tx_status": getattr(receipt, "status", None),
        "state": state,
    }


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, default=str))
