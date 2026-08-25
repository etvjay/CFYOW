# Can't Fake Your Own World (CFYOW)

**A GenLayer research program on coordination between independently governed agents.**

The program asks two questions:

1. Can agents with different models, owners, and policies coordinate through a shared interface whose consequential state cannot be unilaterally rewritten?
2. Does decentralized judgment add something beyond deterministic state and a centralized LLM judge?

The repository is organized to test these questions, not assume their answers. Each experiment names its falsifiers and records its evidence level.

## Status

| Experiment | Question | Machinery | Evidence grade |
|---|---|---|---|
| EXP-001 Judgment Boundary | What moves into consensus vs deterministic/centralized adjudication? | ✅ three-way runner | SIMULATED |
| EXP-002 Different Minds | Can heterogeneous agents coordinate via one interface alone? | ✅ three-arm harness + real LLM agents | REAL AGENT RUNS; decentralized comparison pending |
| EXP-003 Accepted vs Finalized | What breaks when downstream relies on accepted state? | ✅ full harness + dataset | SIMULATED |
| EXP-004 Autonomy Budget | How far can a workflow progress on one trigger? | ✅ transition classifier + budget meter | SIMULATED |
| EXP-005 DevX Under Judgment | What does judgment-bearing programmability cost developers? | ✅ taxonomy + real incident log | REPRODUCED |

**M0 research frame: locked. M1 ledger reproducibility: complete.**

## Findings so far

### 1. Deterministic state coordinates but cannot verify

Across seven ground-truthed scenarios, the deterministic consequence interface settled every scenario as "satisfied," including fabricated claims. A centralized LLM judge scored 7/7 against hidden ground truth. The result is narrow: verification of judgment-dependent completion requires judgment. The open question is whether that judgment needs to be decentralized.

### 2. Architecture trades autonomy against auditability

The same workflow ran 67% of transitions autonomously as one contract and 33% as chained contracts. Chaining added explicit authority boundaries, but also required more external triggers. `NEW_INFORMATION` and `FINALITY_WAIT` limited both designs.

### 3. Judgment-bearing code increases development cost

The build recorded eight incidents. Seven were upstream tooling bugs, and five appeared only on the live network. Static reading and linting did not catch those five cases. In this program, the consensus-sensitive work was concentrated in judgment-bearing tasks.

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
