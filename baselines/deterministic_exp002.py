"""EXP-002 deterministic baseline: same protocol, no judgment.

ERC-8183-style escrow semantics: every transition is a plain state check.
This is the control arm — coordination with zero judgment-bearing state.
Used to measure what GenLayer adjudication adds beyond deterministic shared state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

PHASES = ("uninitialized", "open", "accepted", "committed", "evidence_submitted", "settled")


class ProtocolViolation(Exception):
    pass


@dataclass
class DeterministicWorkflow:
    """Control baseline. Identical state machine to DifferentMinds IC,
    but evaluation is a fixed predicate, not judgment."""

    requester: str
    provider: str
    evaluator: str
    objective: str
    acceptance_predicate: str = "evidence_uri_nonempty"

    phase: str = "uninitialized"
    proposal_terms: str = ""
    commitment_digest: str = ""
    evidence_uri: str = ""
    evaluation_verdict: str = ""
    settled_outcome: str = ""
    transition_count: int = 0
    conflict_count: int = 0

    def _expect(self, *, sender: str, phase: str) -> None:
        if sender != self._expected_actor():
            raise ProtocolViolation(f"wrong actor {sender}")
        if self.phase != phase:
            raise ProtocolViolation(f"invalid phase {self.phase}, expected {phase}")

    def _expected_actor(self) -> str:
        return {
            "uninitialized": self.requester,
            "open": self.provider,       # propose
            "accepted": self.provider,   # commit
            "committed": self.provider,  # submit_evidence
            "evidence_submitted": self.evaluator,  # evaluate
        }.get(self.phase, "")

    # -- transitions -------------------------------------------------------
    def open_workflow(self, sender: str) -> None:
        if sender != self.requester or self.phase != "uninitialized":
            raise ProtocolViolation("open invalid")
        self.phase = "open"
        self.transition_count += 1

    def propose(self, sender: str, terms: str) -> None:
        self._expect(sender=sender, phase="open")
        self.proposal_terms = terms
        self.transition_count += 1

    def accept(self, sender: str) -> None:
        if sender != self.requester or self.phase != "open" or not self.proposal_terms:
            raise ProtocolViolation("accept invalid")
        self.phase = "accepted"
        self.transition_count += 1

    def commit(self, sender: str, deliverable: dict[str, Any]) -> None:
        self._expect(sender=sender, phase="accepted")
        digest = hashlib.sha256(
            json.dumps(deliverable, sort_keys=True).encode()
        ).hexdigest()
        self.commitment_digest = digest
        self.phase = "committed"
        self.transition_count += 1

    def submit_evidence(self, sender: str, evidence_uri: str) -> None:
        self._expect(sender=sender, phase="committed")
        self.evidence_uri = evidence_uri
        self.phase = "evidence_submitted"
        self.transition_count += 1

    def evaluate(self, sender: str) -> None:
        """Deterministic predicate replaces judgment."""
        self._expect(sender=sender, phase="evidence_submitted")
        if self.acceptance_predicate == "evidence_uri_nonempty":
            verdict = "satisfied" if self.evidence_uri else "unsatisfied"
        else:
            raise ProtocolViolation(f"unknown predicate {self.acceptance_predicate}")
        self.evaluation_verdict = verdict
        if verdict == "unsatisfied":
            self.conflict_count += 1
        self.transition_count += 1

    def settle(self, sender: str) -> None:
        if sender != self.requester or self.phase != "evidence_submitted":
            raise ProtocolViolation("settle invalid")
        self.settled_outcome = (
            "completed" if self.evaluation_verdict == "satisfied" else "rejected"
        )
        self.phase = "settled"
        self.transition_count += 1

    def get_state(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "objective": self.objective,
            "proposal_terms": self.proposal_terms,
            "commitment_digest": self.commitment_digest,
            "evidence_uri": self.evidence_uri,
            "evaluation_verdict": self.evaluation_verdict,
            "settled_outcome": self.settled_outcome,
            "transition_count": self.transition_count,
            "conflict_count": self.conflict_count,
        }
