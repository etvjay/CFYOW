# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class ConsequenceEvidenceParent(gl.Contract):
    """EXP-003 semantic-overturn parent driven by mutable public evidence.

    The same transaction may be re-executed during appeal. Each execution fetches
    the current evidence URL before the semantic judgment, allowing the experiment
    to measure what happens when external evidence changes between ACCEPTED and
    FINALIZED without changing contract code or transaction calldata.
    """

    provisional_sink: Address
    settled_sink: Address

    def __init__(self, provisional_sink: str, settled_sink: str):
        self.provisional_sink = Address(provisional_sink)
        self.settled_sink = Address(settled_sink)

    def _judge_current_evidence(self, specification: str, evidence_url: str) -> bool:
        def leader_fn():
            response = gl.nondet.web.get(evidence_url)
            evidence = response.body.decode("utf-8", errors="replace")
            prompt = f"""
Decide whether the CURRENT public evidence substantially satisfies the specification.

Specification:
{specification}

Current evidence fetched from:
{evidence_url}

Evidence body:
{evidence}

Return only JSON:
{{"satisfied": true or false}}

Rules:
- Judge the evidence as it exists during this execution.
- Do not rely on earlier versions of the evidence.
- Do not invent missing facts.
- Explicit revocation, failure, or contradiction of a material requirement means false.
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
    def resolve_case(self, case_id: str, specification: str, evidence_url: str) -> None:
        if not case_id or not specification or not evidence_url:
            raise gl.vm.UserError("case id, specification, and evidence url are required")

        if not self._judge_current_evidence(specification, evidence_url):
            return

        provisional = gl.get_contract_at(self.provisional_sink)
        settled = gl.get_contract_at(self.settled_sink)
        provisional.emit(on="accepted").record_consequence(case_id, "satisfied")
        settled.emit(on="finalized").record_consequence(case_id, "satisfied")
