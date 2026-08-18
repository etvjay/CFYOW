import json


def _mock_judgment(vm, satisfied: bool, score: int, rationale: str = "grounded"):
    vm.mock_llm(
        r".*substantially satisfies a written milestone specification.*",
        json.dumps({
            "satisfied": satisfied,
            "score": score,
            "rationale": rationale,
        }),
    )


def test_register_and_read_milestone(direct_deploy):
    contract = direct_deploy("contracts/judgment_boundary.py")
    contract.register_milestone(
        "m1",
        "Deliver a responsive storefront with mobile checkout.",
        "Demo shows responsive layout and mobile checkout.",
    )

    milestone = contract.get_milestone("m1")
    assert milestone["evaluated"] is False
    assert milestone["satisfied"] is False
    assert milestone["score"] == 0


def test_consensus_judgment_updates_shared_state(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/judgment_boundary.py")
    contract.register_milestone(
        "m1",
        "Deliver a responsive storefront with mobile checkout.",
        "Demo shows responsive layouts and a completed mobile checkout flow.",
    )
    _mock_judgment(direct_vm, True, 84, "Material requirements are evidenced.")

    contract.evaluate_milestone("m1")

    milestone = contract.get_milestone("m1")
    assert milestone["evaluated"] is True
    assert milestone["satisfied"] is True
    assert milestone["score"] == 84


def test_rejected_judgment_is_persisted_as_consequence(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/judgment_boundary.py")
    contract.register_milestone(
        "m2",
        "Deliver responsive desktop and mobile checkout.",
        "Evidence contains a desktop screenshot only.",
    )
    _mock_judgment(direct_vm, False, 48, "Mobile checkout is not evidenced.")

    contract.evaluate_milestone("m2")

    milestone = contract.get_milestone("m2")
    assert milestone["evaluated"] is True
    assert milestone["satisfied"] is False
    assert milestone["score"] == 48


def test_milestone_cannot_be_judged_twice(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/judgment_boundary.py")
    contract.register_milestone("m3", "spec", "evidence")
    _mock_judgment(direct_vm, True, 90)
    contract.evaluate_milestone("m3")

    with direct_vm.expect_revert("Milestone already evaluated"):
        contract.evaluate_milestone("m3")
