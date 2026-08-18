# Can't Fake Your Own World (CFYOW)

**A GenLayer research program on agentic coordination, autonomous workflows, shared interfaces, developer experience, and judgment-bearing programmability.**

CFYOW is not starting from the claim that GenLayer gives agents truth. The research asks a narrower systems question:

> Can independently governed agents coordinate through a shared adjudicated interface whose consequential state cannot be unilaterally rewritten by one participant?

## Working thesis

GenLayer may be useful for agent coordination not merely because it can place AI-dependent computation inside a contract, but because Intelligent Contracts can turn some judgment-dependent claims into shared, consequence-bearing state through validator adjudication.

This is a hypothesis, not a conclusion. The repository is organized to try to falsify it.

## Research invariants

1. **Consensus is not truth.** An accepted/finalized GenLayer outcome is a protocol outcome, not proof of objective reality.
2. **Shared state is not novel by itself.** Replicated ledgers, tuple spaces, blackboards, commitment protocols, and stigmergic systems already coordinate independent actors through shared environments.
3. **Autonomy must be measured.** Intelligent Contract execution begins with a transaction; downstream IC messages can continue a workflow, but external triggers and evidence may still be required.
4. **Accepted and finalized are different programming surfaces.** Provisional actions can create duplicate, stale, or compensation-sensitive downstream effects.
5. **DevX is part of the result.** Greater expressiveness is not automatically an improvement if validation, testing, latency, appeals, or observability make the system impractical.

## Experiment program

| Experiment | Question | Status |
|---|---|---|
| EXP-001 — Judgment Boundary | What actually moves into consensus compared with deterministic and centralized adjudication? | Building |
| EXP-002 — Different Minds, One Interface | Can heterogeneous agents coordinate without shared cognition or a central orchestrator? | Designed |
| EXP-003 — Accepted vs Finalized | What breaks when downstream actions rely on accepted rather than finalized state? | Designed |
| EXP-004 — Autonomy Budget | How far can a workflow progress after one initiating transaction? | Designed |
| EXP-005 — DevX Under Judgment | What developer burden is introduced by judgment-bearing state transitions? | Designed |

## Repository map

```text
research/                 Thesis, claim ledger, related work, adversarial review
experiments/              Falsifiable experiment specifications and results
contracts/                GenLayer Intelligent Contracts used by experiments
baselines/                Deterministic and centralized comparison implementations
tests/direct/             GenLayer direct-mode tests
tests/unit/               Offchain baseline tests
results/                  Raw and normalized experiment outputs
docs/decisions/           Research/architecture decision records
docs/modules/             Usage notes for reusable modules
.github/workflows/         Reproducible CI
```

## Current executable target: EXP-001

The first scenario asks whether a free-form milestone submission **substantially satisfies a written specification**. The same decision is represented three ways:

1. a deterministic baseline that requires a pre-structured trusted attestation;
2. a centralized adjudicator that decides from the free-form specification and evidence;
3. a GenLayer Intelligent Contract that places the judgment and its validation inside the consensus-critical path.

The benchmark records where judgment lives, which components must be trusted, and what downstream state can depend on the result.

## Local development

Requirements follow the current GenLayer project boilerplate and require Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

genvm-lint check contracts/judgment_boundary.py
pytest tests/unit tests/direct -v
```

Direct tests use mocked LLM output. They test contract logic, **not distributed consensus quality**. Consensus-sensitive claims remain blocked until Studio/GLSim/testnet runs are recorded under `results/`.

## Research rule

**Do not upgrade an interpretation into a fact because it sounds good.** Every load-bearing claim is classified, sourced, and tied to an experiment or explicit boundary.
