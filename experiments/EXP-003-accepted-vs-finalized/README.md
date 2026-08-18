# EXP-003 — Accepted World vs Final World

## Research question
What application-level failures appear when downstream coordination acts on `accepted` state instead of waiting for `finalized` state?

## Protocol fact being tested
GenLayer internal IC messages may be emitted on `accepted` or `finalized`. Accepted messages can execute before the appeal window closes; re-execution can emit duplicates, and a later appeal can make an already executed child message inconsistent with the final parent outcome. External IC→EVM messages are finalized-only.

## Setup

Parent IC: adjudicates milestone completion.

Child IC: records completion/reward intent using an idempotency key.

### Variant A — provisional
```python
child.emit(on="accepted").record_completion(case_id)
```

### Variant B — settled
```python
child.emit(on="finalized").record_completion(case_id)
```

Where the environment permits, produce an appeal/re-execution path that changes or repeats the parent execution.

## Network evidence capture

Every live transaction used by this experiment must be captured with Experiment Ledger:

```bash
python -m experiment_ledger capture-genlayer \
  --rpc "$GENLAYER_RPC_URL" \
  --tx "$TX_HASH" \
  --contract "$PARENT_CONTRACT" \
  --output "results/EXP-003/runs/$RUN_ID-parent.json"
```

Capture the child transaction separately when a stable/documented child-transaction identifier is available. Do not infer child execution count from the parent receipt unless the protocol/API provides explicit lineage.

The parent capture records:

- the distinct status path actually observed;
- whether ACCEPTED was observed;
- whether FINALIZED was observed;
- appeal status/timestamp evidence;
- consensus round count;
- validator/vote/result-hash metadata exposed by the receipt;
- accepted and finalized contract-state snapshots.

A FINALIZED transaction does not retroactively count as an observed ACCEPTED state if the capture process started too late to see it.

## Metrics
- time from parent submission to child effect;
- accepted-to-finalized latency when both transitions are actually observed;
- consensus round count;
- appeal observed (boolean);
- additional-round/re-execution signal;
- duplicate child executions;
- stale/invalid child effects after appeal;
- idempotency state required;
- compensation actions required;
- number of protocol states the application must expose to users/agents;
- debugging steps needed to reconstruct parent/child lineage.

## Candidate concept
**Consequence stability** — how strongly an observed protocol state can be relied upon before taking an action that is expensive or impossible to reverse.

## Falsifiers
- accepted/finalized produces no meaningful application difference beyond latency;
- robust idempotency/compensation makes provisional execution effectively costless for the tested workflow;
- the chosen environment cannot reproduce the relevant appeal/re-execution behavior, in which case no empirical claim is made.

## Safety invariant
Never use a non-idempotent irreversible child effect merely to manufacture a dramatic result. The experiment should expose protocol semantics without creating avoidable real-world loss.
