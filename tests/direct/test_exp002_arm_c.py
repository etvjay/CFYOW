"""EXP-002 arm C: GenLayer consensus evaluation in direct mode (simulator)."""

import json

import pytest
from gltest import get_validator_factory

pytestmark = pytest.mark.integration


def test_arm_c_consensus_evaluates_evidence(direct_vm, direct_deploy):
    evidence_body = """{"case":"arm-c-sim","endpoint":"/health","http_status":200,
"response_body":\"{\\\"status\\\":\\\"ok\\\"}\",
"demonstrates":"live endpoint responded 200 with expected JSON body"}"""

    direct_vm.mock_web(
        r".*localhost:8765/evidence/arm-c-sim.*",
        {"status": 200, "body": json.dumps({
            "case": "arm-c-sim",
            "endpoint": "/health",
            "http_status": 200,
            "response_body": '{"status":"ok"}',
            "demonstrates": "live endpoint responded 200 with expected JSON body",
        })},
    )
    direct_vm.mock_llm(
        r".*Decide whether the evidence satisfies.*",
        '{\"verdict\": \"satisfied\", \"reason\": \"evidence shows live endpoint returned expected body\"}',
    )

    from gltest.direct.loader import create_address

    requester_addr = create_address("requester")
    provider_addr = create_address("provider")

    contract = direct_deploy(
        "contracts/different_minds_judged.py",
        requester_addr,
    )

    # requester opens
    direct_vm.sender = requester_addr
    contract.open_workflow(provider_addr, "Deliver a JSON health endpoint")
    # provider proposes
    direct_vm.sender = provider_addr
    contract.propose("deliver per objective")
    # requester accepts
    direct_vm.sender = requester_addr
    contract.accept()
    # provider commits + submits evidence
    direct_vm.sender = provider_addr
    contract.commit("deadbeef")
    contract.submit_evidence("http://localhost:8765/evidence/arm-c-sim")
    receipt = contract.evaluate_consensus()

    state = contract.get_state()
    print("\nDEBUG STATE:", state)
    assert state.get("evaluation_verdict") == "satisfied"
    assert state.get("phase") == "evidence_submitted"
