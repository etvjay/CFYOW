# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class DifferentMindsJudged(gl.Contract):
    """EXP-002 arm C: evaluation runs through GenLayer Optimistic Democracy.

    The evaluate step is judgment-bearing: a leader model proposes the verdict,
    validator models verify equivalence, and disputes can escalate via appeal.
    This is the treatment arm compared against deterministic (A) and
    single-LLM (B) evaluators on identical workflows.
    """

    requester: Address
    provider: Address

    objective: str
    phase: str
    proposal_terms: str
    commitment_digest: str
    evidence_uri: str
    evaluation_verdict: str
    settled_outcome: str
    appeal_count: u256
    transition_count: u256

    def __init__(self, requester: str):
        self.requester = Address(requester)
        self.phase = "uninitialized"
        self.appeal_count = 0
        self.transition_count = 0

    @gl.public.write
    def open_workflow(self, provider: str, objective: str) -> None:
        if self.phase != "uninitialized":
            raise gl.vm.UserError("already initialized")
        self.provider = Address(provider)
        self.objective = objective
        self.phase = "open"
        self.transition_count += 1

    @gl.public.write
    def propose(self, terms: str) -> None:
        if gl.message.sender_address != self.provider:
            raise gl.vm.UserError("only provider proposes")
        if self.phase != "open":
            raise gl.vm.UserError(f"propose invalid in {self.phase}")
        self.proposal_terms = terms
        self.transition_count += 1

    @gl.public.write
    def accept(self) -> None:
        if gl.message.sender_address != self.requester:
            raise gl.vm.UserError("only requester accepts")
        if self.phase != "open":
            raise gl.vm.UserError(f"accept invalid in {self.phase}")
        self.phase = "accepted"
        self.transition_count += 1

    @gl.public.write
    def commit(self, digest: str) -> None:
        if gl.message.sender_address != self.provider:
            raise gl.vm.UserError("only provider commits")
        if self.phase != "accepted":
            raise gl.vm.UserError(f"commit invalid in {self.phase}")
        self.commitment_digest = digest
        self.phase = "committed"
        self.transition_count += 1

    @gl.public.write
    def submit_evidence(self, evidence_uri: str) -> None:
        if gl.message.sender_address != self.provider:
            raise gl.vm.UserError("only provider submits")
        if self.phase != "committed":
            raise gl.vm.UserError(f"submit invalid in {self.phase}")
        self.evidence_uri = evidence_uri
        self.phase = "evidence_submitted"
        self.transition_count += 1

    def _judge(self) -> str:
        """Judgment-bearing evaluation through GenLayer consensus.

        The leader fetches the live evidence URL and decides; validators run the
        same prompt and must land within the equivalence principle (same verdict).
        """
        def leader_fn():
            response = gl.nondet.web.get(self.evidence_uri)
            body = response.body.decode("utf-8", errors="replace")[:2000]
            prompt = f"""
Decide whether the evidence satisfies the workflow objective.

Objective:
{self.objective}

Evidence fetched from {self.evidence_uri}:
{body}

Return only JSON:
{{"verdict": "satisfied" or "unsatisfied", "reason": "..."}}

Rules:
- Judge only what the evidence demonstrates.
- Commitment digests prove integrity, not completion.
- Explicit missing demonstration means unsatisfied.
"""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            leader_data = leader_result.calldata
            validator_data = leader_fn()
            if not isinstance(leader_data, dict) or not isinstance(validator_data, dict):
                return False
            # Equivalence principle: same verdict string.
            return str(leader_data.get("verdict", "")).strip().lower() == str(
                validator_data.get("verdict", "")
            ).strip().lower()

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        verdict = str(result.get("verdict", "")).strip().lower()
        if verdict not in ("satisfied", "unsatisfied"):
            raise gl.vm.UserError("consensus produced invalid verdict")
        return verdict

    @gl.public.write
    def evaluate_consensus(self) -> None:
        """Arm C evaluation: leader/validator consensus over live evidence."""
        if self.phase != "evidence_submitted":
            raise gl.vm.UserError(f"evaluate invalid in {self.phase}")
        verdict = self._judge()
        self.evaluation_verdict = verdict
        self.transition_count += 1

    @gl.public.write
    def record_appeal(self) -> None:
        """Called by the harness after an on-chain appeal re-executes evaluate."""
        self.appeal_count += 1

    @gl.public.write
    def settle(self) -> None:
        if gl.message.sender_address != self.requester:
            raise gl.vm.UserError("only requester settles")
        if self.phase != "evidence_submitted":
            raise gl.vm.UserError(f"settle invalid in {self.phase}")
        if not self.evaluation_verdict:
            raise gl.vm.UserError("no consensus verdict")
        self.settled_outcome = (
            "completed" if self.evaluation_verdict == "satisfied" else "rejected"
        )
        self.phase = "settled"
        self.transition_count += 1

    @gl.public.view
    def get_state(self) -> dict:
        return {
            "phase": self.phase,
            "objective": self.objective,
            "proposal_terms": self.proposal_terms,
            "commitment_digest": self.commitment_digest,
            "evidence_uri": self.evidence_uri,
            "evaluation_verdict": self.evaluation_verdict,
            "settled_outcome": self.settled_outcome,
            "appeal_count": int(self.appeal_count),
            "transition_count": int(self.transition_count),
        }
