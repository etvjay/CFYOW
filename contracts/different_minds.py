# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class DifferentMinds(gl.Contract):
    """EXP-002: coordination through a shared adjudicated interface.

    Protocol: propose -> accept -> commit -> submit_evidence -> evaluate -> settle
    Only protocol-visible inputs cross actor boundaries. No hidden scratchpad.
    """

    PHASES = ("open", "accepted", "committed", "evidence_submitted", "settled")

    requester: Address
    provider: Address
    evaluator: Address

    objective: str
    phase: str

    proposal_terms: str
    commitment_digest: str
    evidence_uri: str
    evaluation_verdict: str
    settled_outcome: str

    # metrics: every transition is recorded protocol-visibly
    transition_count: u256
    conflict_count: u256

    def __init__(self, requester: str):
        self.requester = Address(requester)
        self.phase = "uninitialized"
        self.transition_count = 0
        self.conflict_count = 0

    def _register_participants(self, provider: str, evaluator: str) -> None:
        if self.phase != "uninitialized":
            raise gl.vm.UserError("participants already registered")
        self.provider = Address(provider)
        self.evaluator = Address(evaluator)
        self.phase = "open"
        self.transition_count += 1

    @gl.public.write
    def open_workflow(self, provider: str, evaluator: str, objective: str) -> None:
        """Requester opens the workflow. Anyone can call init; only once."""
        if not objective:
            raise gl.vm.UserError("objective required")
        self._register_participants(provider, evaluator)
        self.objective = objective

    @gl.public.write
    def propose(self, terms: str) -> None:
        """Provider proposes terms while open."""
        if gl.message.sender_address != self.provider:
            raise gl.vm.UserError("only provider may propose")
        if self.phase != "open":
            raise gl.vm.UserError(f"propose invalid in phase {self.phase}")
        if not terms:
            raise gl.vm.UserError("terms required")
        self.proposal_terms = terms
        self.transition_count += 1

    @gl.public.write
    def accept(self) -> None:
        """Requester accepts the proposal -> accepted."""
        if gl.message.sender_address != self.requester:
            raise gl.vm.UserError("only requester may accept")
        if self.phase != "open":
            raise gl.vm.UserError(f"accept invalid in phase {self.phase}")
        if not self.proposal_terms:
            raise gl.vm.UserError("nothing proposed")
        self.phase = "accepted"
        self.transition_count += 1

    @gl.public.write
    def commit(self, digest: str) -> None:
        """Provider commits to delivery with an evidence digest commitment."""
        if gl.message.sender_address != self.provider:
            raise gl.vm.UserError("only provider may commit")
        if self.phase != "accepted":
            raise gl.vm.UserError(f"commit invalid in phase {self.phase}")
        if not digest:
            raise gl.vm.UserError("digest required")
        self.commitment_digest = digest
        self.phase = "committed"
        self.transition_count += 1

    @gl.public.write
    def submit_evidence(self, evidence_uri: str) -> None:
        """Provider submits evidence reference."""
        if gl.message.sender_address != self.provider:
            raise gl.vm.UserError("only provider may submit evidence")
        if self.phase != "committed":
            raise gl.vm.UserError(f"submit invalid in phase {self.phase}")
        if not evidence_uri:
            raise gl.vm.UserError("evidence uri required")
        self.evidence_uri = evidence_uri
        self.phase = "evidence_submitted"
        self.transition_count += 1

    @gl.public.write
    def evaluate(self, verdict: str) -> None:
        """Evaluator judges the evidence. Judgment-bearing: verdict recorded as-is,
        disputes increment conflict_count and are resolvable via re-evaluation."""
        if gl.message.sender_address != self.evaluator:
            raise gl.vm.UserError("only evaluator may evaluate")
        if self.phase != "evidence_submitted":
            raise gl.vm.UserError(f"evaluate invalid in phase {self.phase}")
        v = verdict.strip().lower()
        if v not in ("satisfied", "unsatisfied"):
            raise gl.vm.UserError("verdict must be satisfied|unsatisfied")
        self.evaluation_verdict = v
        if v == "unsatisfied":
            self.conflict_count += 1
        self.transition_count += 1

    @gl.public.write
    def settle(self) -> None:
        """Settle after evaluation. Outcome derives from the recorded verdict."""
        if gl.message.sender_address != self.requester:
            raise gl.vm.UserError("only requester may settle")
        if self.phase != "evidence_submitted":
            raise gl.vm.UserError(f"settle invalid in phase {self.phase}")
        if not self.evaluation_verdict:
            raise gl.vm.UserError("no verdict recorded")
        self.settled_outcome = "completed" if self.evaluation_verdict == "satisfied" else "rejected"
        self.phase = "settled"
        self.transition_count += 1

    @gl.public.view
    def get_state(self) -> dict:
        return {
            "phase": self.phase,
            "requester": str(self.requester.as_hex),
            "provider": str(self.provider.as_hex),
            "evaluator": str(self.evaluator.as_hex),
            "objective": self.objective,
            "proposal_terms": self.proposal_terms,
            "commitment_digest": self.commitment_digest,
            "evidence_uri": self.evidence_uri,
            "evaluation_verdict": self.evaluation_verdict,
            "settled_outcome": self.settled_outcome,
            "transition_count": int(self.transition_count),
            "conflict_count": int(self.conflict_count),
        }
