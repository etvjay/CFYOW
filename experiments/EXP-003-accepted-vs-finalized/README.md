# EXP-003 — Accepted World vs Final World

## Benchmark family

**CFYOW Shared Consequence Benchmark**

EXP-003 is the finality module of the benchmark: **when is a shared adjudicated world stable enough for downstream consequences?**

Dataset specification: [`DATASET.md`](./DATASET.md)  
Visualization map: [`VISUALIZATIONS.md`](./VISUALIZATIONS.md)

## Status
**Executable Bradbury testnet harness implemented. No stale-world claim is promoted until a structurally valid live artifact reproduces it and passes the strict evidence gate.**

## Research question
What application-level failures appear when downstream coordination acts on `accepted` state instead of waiting for `finalized` state?

## Why this experiment exists

CFYOW studies what changes when independently governed agents coordinate through shared consequence-bearing state rather than a shared private cognition or central orchestrator. That raises a second-order problem: shared state can become recognized before it becomes settled.

EXP-003 isolates that boundary. It asks whether an action can be valid relative to the best shared world at T1, yet become inconsistent with the finalized shared world at T2 without any actor privately rewriting the shared state.

This is why the experiment is named **Accepted World vs Final World**:
- **Accepted World** = recognized, shared, actionable state during the finality/appeal window;
- **Final World** = the adjudicated state after the relevant finality process;
- **vs** = the measured difference in downstream consequences, not a claim that one world is false and the other objectively true.

The name therefore encodes the experiment's independent variable: **when downstream consequences are allowed to attach to shared state**.

## Protocol fact being tested
GenLayer internal IC messages may be emitted on `accepted` or `finalized`. Accepted messages can execute before the appeal window closes; re-execution can emit duplicates, and a later appeal can make an already executed child message inconsistent with the final parent outcome. External IC→EVM messages are finalized-only.

## Experiment family

EXP-003 is intentionally split into two sub-experiments because duplicate delivery and stale semantic consequence are different phenomena.

### EXP-003A — Appeal-induced duplicate delivery

```text
semantic judgment remains true
        |
     ACCEPTED
        |
provisional consequence
        |
      appeal
        |
re-execution remains true
        |
     FINALIZED
```

Question: does the accepted-timing consequence get delivered more than once during appeal/re-execution?

Implementation:
- `contracts/consequence_parent.py`
- `tests/integration/test_exp003_appeal_reexecution.py`

The test does **not** require a duplicate to occur. It captures the duplicate delta the network actually produces.

### EXP-003B — Semantic overturn under changed external evidence

```text
public evidence = SATISFIED
        |
same transaction reaches ACCEPTED
        |
provisional consequence applies
        |
external evidence changes to REVOKED
        |
      appeal
        |
same transaction re-executes
        |
final semantic judgment may become false
        |
FINALIZED consequence absent if false
```

Question: can a consequence legitimately applied in the provisional world become inconsistent with the final shared world when external evidence changes during the appeal window?

Implementation:
- `contracts/consequence_evidence_parent.py`
- mutable public evidence fixture: repository issue #3
- `tests/integration/test_exp003_semantic_overturn.py`

The same transaction calldata, contract code, and criterion are preserved across rounds. The experiment changes only the public external evidence before the appeal re-execution. Validator mocks are deliberately not swapped between rounds.

A stale consequence is counted only when the strict evidence gate in `DATASET.md` is satisfied. A semantic transition alone is insufficient.

## Shared topology

```text
Parent.resolve_case(...)
        |
        | semantic judgment = satisfied
        |
        +---- on="accepted" ----> provisional ConsequenceSink
        |
        +---- on="finalized" ---> settled ConsequenceSink
```

Each sink is idempotent and records total delivery attempts, unique consequences applied, per-case attempts, duplicate count, first sender, and payload.

## Contracts

- `contracts/consequence_parent.py` — constant-evidence semantic parent for EXP-003A.
- `contracts/consequence_evidence_parent.py` — re-fetches current public evidence on every execution for EXP-003B.
- `contracts/consequence_sink.py` — idempotent application-level evidence sink.

## Network evidence capture

Every live parent transaction used by this experiment should also be capturable through Experiment Ledger:

```bash
python -m experiment_ledger capture-genlayer \
  --rpc "$GENLAYER_RPC_URL" \
  --tx "$PARENT_TX_HASH" \
  --contract "$PARENT_ADDRESS" \
  --output "results/EXP-003-accepted-vs-finalized/runs/$RUN_ID-network.json"
```

Message/child lineage is captured through the documented GenLayerPY methods `get_transaction()` and `get_triggered_transaction_ids()` via `experiment_ledger.adapters.genlayer_children.capture_child_lineage`.

The lineage adapter records emitted messages and triggered transaction IDs but does not infer whether duplicate child executions were harmful. Sink state supplies that application-level evidence.

A FINALIZED transaction does not retroactively count as an observed ACCEPTED state if capture started too late to observe it.

## Test layers

### Direct mode
`tests/direct/test_consequence_sink.py`

Verifies idempotency and duplicate accounting. Direct mode is not evidence about accepted/finalized activation timing.

### Studio/network smoke test
`tests/integration/test_exp003_consequence_stability.py`

Validates that a positive parent decision can eventually reach both sinks after finalization. This is wiring validation, not an appeal result.

### Bradbury testnet evidence workflow
`.github/workflows/exp003-network.yml`

Runs EXP-003A and EXP-003B against `testnet_bradbury`, uses a dedicated testnet signer supplied only through GitHub Actions secrets, restores the mutable evidence fixture in an `always()` cleanup step, persists normalized benchmark dataset rows, and uploads evidence regardless of whether the experiment reaches a valid result.

## Dataset

The workflow exports one append-only case row per `(run_id, run_attempt, experiment_id)` into:

```text
results/EXP-003/dataset/run-cases.jsonl
results/EXP-003/dataset/run-cases.csv
results/EXP-003/dataset/overview.json
```

The dataset separates:
1. apparatus validity;
2. world-transition evidence;
3. consequence-effect evidence.

A failed harness is therefore not treated as a falsified protocol hypothesis.

## Metrics
- time from parent submission to first observed `ACCEPTED`;
- time from `ACCEPTED` to `FINALIZED`;
- appeal occurrence;
- consensus round count;
- accepted-timing message count;
- finalized-timing message count;
- triggered child transaction count;
- provisional sink delivery attempts;
- settled sink delivery attempts;
- duplicate attempts by sink;
- provisional duplicate delta after appeal;
- settled duplicate delta after appeal;
- stale provisional consequence observed (boolean, evidence-gated);
- idempotency state required;
- compensation actions required;
- debugging steps needed to reconstruct parent/child lineage.

## Candidate metric: Consequence Stability

A first operational form:

```text
Consequence Stability(case) =
  1 - stale_or_duplicate_irreversible_effects / consequential_effect_attempts
```

This formula is provisional. It must not be promoted into a general metric until experiment results establish that its numerator and denominator are meaningful across workflows. A vector representation may prove more rigorous:

```text
CS = {
  finality_latency,
  stale_effect_rate,
  duplicate_rate,
  compensation_cost,
  reversibility
}
```

## Falsifiers
- accepted/finalized produces no meaningful application difference beyond latency;
- robust idempotency/compensation makes provisional execution effectively costless for the tested workflow;
- appeals/additional rounds do not create measurable stale or duplicate effects in the tested scenarios;
- changing external evidence does not produce a reproducible semantic overturn under the tested criterion;
- the chosen environment cannot reproduce the relevant appeal/re-execution behavior, in which case no empirical claim is made.

## Safety invariant
Never use a non-idempotent irreversible child effect merely to manufacture a dramatic result. The experiment exposes protocol semantics through reversible/idempotent sinks before testing any economically consequential integration.
