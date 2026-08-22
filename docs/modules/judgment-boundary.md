# Judgment Boundary Module

This document is the integration surface for `contracts/judgment_boundary.py`.

## Purpose

`JudgmentBoundary` stores a milestone specification and evidence, then resolves a judgment-dependent state transition through GenLayer nondeterministic execution and validator verification.

It is an **experiment contract**, not production escrow or a general-purpose adjudication protocol.

## Public interface

### `register_milestone(milestone_id, specification, evidence)`
Creates immutable input state for one experiment case.

Requirements:
- `milestone_id` must be unique;
- all three arguments must be non-empty;
- evidence is currently stored directly as text for experimental reproducibility.

### `evaluate_milestone(milestone_id)`
Runs the judgment once. The persisted result contains:
- `evaluated`;
- `satisfied`;
- `score` (0–100);
- `rationale`.

The current validator independently performs the evaluation and accepts the leader result only when:
- both nodes agree on `satisfied`;
- both scores are valid;
- both scores fall in the same 10-point bucket.

### `get_milestone(milestone_id)`
Returns the complete experiment record stored by the contract.

## Important boundaries

- Direct-mode LLM mocks test state transitions, not real validator diversity.
- The current score-bucket rule is an experimental equivalence criterion, not a claim that ±9 points is generally safe.
- The contract does not transfer funds.
- The contract does not fetch private evidence.
- The contract deliberately prevents repeat evaluation so EXP-001 measures one adjudication event per case. Appeal/re-execution behavior belongs to later network-level experiments.

## Frontend / agent consumption

Consumers should treat `satisfied` as **protocol-recognized experiment state**, not objective truth. Display or log the specification, evidence provenance, score, rationale, transaction/finality status, and experiment configuration together so the judgment is not detached from its evidence and validation context.
