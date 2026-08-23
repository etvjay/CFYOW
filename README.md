# Can't Fake Your Own World (CFYOW)

**A GenLayer research program on agentic coordination through adjudicated shared state.**

Can independently governed AI agents — different models, owners, and policies — coordinate through a shared interface whose consequential state no single participant can rewrite? And does **decentralized judgment** (GenLayer's Optimistic Democracy) add coordination properties that deterministic escrow and centralized LLM judges don't already provide?

This repo is organized to falsify, not confirm. Every claim carries evidence; every experiment has named falsifiers.

## Status

| Experiment | Question | Machinery | Evidence grade |
|---|---|---|---|
| EXP-001 Judgment Boundary | What moves into consensus vs deterministic/centralized adjudication? | ✅ three-way runner | SIMULATED |
| EXP-002 Different Minds | Can heterogeneous agents coordinate via one interface alone? | ✅ three-arm harness + real LLM agents | VALIDATED |
| EXP-003 Accepted vs Finalized | What breaks when downstream relies on accepted state? | ✅ full harness + dataset | SIMULATED |
| EXP-004 Autonomy Budget | How far can a workflow progress on one trigger? | ✅ transition classifier + budget meter | SIMULATED |
| EXP-005 DevX Under Judgment | What does judgment-bearing programmability cost developers? | ✅ taxonomy + real incident log | REPRODUCED |

**M0 research frame: locked. M1 ledger reproducibility: complete.**

## Findings so far

### 1. Deterministic state coordinates but cannot verify

Across 7 ground-truthed scenarios, a deterministic consequence interface settled every one "satisfied" — including fabricated claims. A centralized LLM judge scored 7/7 against hidden ground truth. Verification of judgment-dependent completion *requires judgment*; the open question is whether that judgment must be decentralized.

### 2. Architecture trades autonomy against auditability

The same workflow as a monolithic contract runs 67% of transitions autonomously after one trigger; as chained contracts only 33% — but every authority boundary becomes an explicit external trigger. `NEW_INFORMATION` and `FINALITY_WAIT` bound autonomy in both designs.

### 3. The DevX burden is real and concentrated

Eight build incidents: 7 upstream tooling bugs, 5 only detectable on the live network, zero caught by static reading or linting. Consensus-sensitive code concentrates entirely in judgment-bearing tasks.

Full analysis: [`research/synthesis/sprint-1-synthesis.md`](research/synthesis/sprint-1-synthesis.md)

## The experiment stack

```
EXP-001  judgment_boundary contract     ← what moves into consensus?
EXP-002  different_minds(_judged)       ← heterogeneous agent coordination
EXP-003  consequence_parent/sink        ← accepted vs finalized downstream effects
EXP-004  transition classifier          ← autonomy budget measurement
EXP-005  task registry + incident log   ← DevX measurement scaffolding
experiment_ledger/                      ← run capture + content-addressed lineage
```

Each experiment measures the same workflows through multiple adjudication arms:

| Arm | Evaluator | Tests |
|---|---|---|
| A | deterministic predicate | pure shared-state coordination |
| B | centralized LLM judge | best-case centralized judgment |
| C | GenLayer Optimistic Democracy | decentralized multi-model adjudication |

Arm C is verified end-to-end in direct-mode simulator; live-network replication is the current gate for REPRODUCED grades.

## Running it

```bash
# unit + lineage tests
pytest tests/unit -v

# direct-mode consensus tests (simulator)
pytest tests/direct -v

# EXP-002 comparison (needs free-tier API keys in ~/.config/foundry/cfyow-agents.env)
python experiments/EXP-002-different-minds-one-interface/run_comparison.py

# lineage chains
python -m pytest tests/unit/test_lineage.py -v
```

Requirements follow the GenLayer project boilerplate (Python 3.12+).

## Repository map

```text
research/                 Thesis, claim ledger, adversarial review, synthesis
experiments/              Falsifiable experiment specs + runners + results
contracts/                GenLayer Intelligent Contracts
baselines/                Deterministic and centralized comparisons
tests/direct/             GenLayer direct-mode tests
tests/unit/               Offchain tests
results/                  Raw datasets, visualizations, scorecards
docs/decisions/           Research/architecture decision records
.github/workflows/        Reproducible CI
```

## Research invariants

1. **Consensus is not truth.** An accepted/finalized outcome is a protocol outcome, not proof of reality.
2. **Shared state is not novel by itself.** The question is what adjudication adds beyond replicated ledgers and tuple spaces.
3. **Autonomy must be measured, not assumed.**
4. **Accepted and finalized are different programming surfaces.**
5. **DevX is part of the result.**

## Related

- Filed upstream: [genlayer-testing-suite#107](https://github.com/genlayerlabs/genlayer-testing-suite/issues/107), [genlayer-py#107](https://github.com/genlayerlabs/genlayer-py/issues/107)
- Built by [Jaydearcadian](https://github.com/Jaydearcadian)
