# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class ConsequenceParent(gl.Contract):
    """EXP-003 parent: same semantic decision, two consequence timings."""

    provisional_sink: Address
    settled_sink: Address

    def __init__(self, provisional_sink: Address, settled_sink: Address):
        self.provisional_sink = provisional_sink
        self.settled_sink = settled_sink

    def _judge(self, specification: str, evidence: str) -> bool:
        def leader_fn():
            prompt = f"""
Decide whether the evidence substantially satisfies the specification.

Specification:
{specification}

Evidence:
{evidence}

Return only JSON:
{{"satisfied": true or false}}

Do not invent missing evidence.
"""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            leader_data = leader_result.calldata
            validator_data = leader_fn()
            if not isinstance(leader_data, dict) or not isinstance(validator_data, dict):
                return False
            return bool(leader_data.get("satisfied", False)) == bool(
                validator_data.get("satisfied", False)
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        return bool(result["satisfied"])

    @gl.public.write
    def resolve_case(self, case_id: str, specification: str, evidence: str) -> None:
        if not case_id or not specification or not evidence:
            raise gl.vm.UserError("case id, specification, and evidence are required")

        if not self._judge(specification, evidence):
            return

        payload = "satisfied"

        provisional = gl.get_contract_at(self.provisional_sink)
        settled = gl.get_contract_at(self.settled_sink)

        provisional.emit(on="accepted").record_consequence(case_id, payload)
        settled.emit(on="finalized").record_consequence(case_id, payload)
