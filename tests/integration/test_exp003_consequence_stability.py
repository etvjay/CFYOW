"""Studio/network smoke test for EXP-003.

This validates that the parent can emit the positive consequence to both timing
variants and that both sinks eventually converge after finalization. It does NOT
prove accepted/finalized divergence; appeal/re-execution runs are captured
separately through Experiment Ledger network evidence.
"""

from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import MockedLLMResponse


def test_positive_case_reaches_both_sinks_after_finalization():
    sink_factory = get_contract_factory("ConsequenceSink")
    provisional_sink = sink_factory.deploy()
    settled_sink = sink_factory.deploy()

    parent_factory = get_contract_factory("ConsequenceParent")
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
            "case-positive",
            "Deliver a working JSON health endpoint.",
            "The deployed service returns HTTP 200 and JSON {status: ok} at /health.",
        ]
    ).transact(transaction_context=context)
    assert tx_execution_succeeded(receipt)

    provisional = provisional_sink.get_record(args=["case-positive"]).call()
    settled = settled_sink.get_record(args=["case-positive"]).call()

    assert provisional["applied"] is True
    assert settled["applied"] is True
    assert provisional["payload"] == "satisfied"
    assert settled["payload"] == "satisfied"
