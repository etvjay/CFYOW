# EXP-003 — Accepted World vs Final World

## Status
**Executable harness implemented; appeal/re-execution evidence still requires a live Studio/testnet run.**

## Research question
What application-level failures appear when downstream coordination acts on `accepted` state instead of waiting for `finalized` state?

## Protocol fact being tested
GenLayer internal IC messages may be emitted on `accepted` or `finalized`. Accepted messages can execute before the appeal window closes; re-execution can emit duplicates, and a later appeal can make an already executed child message inconsistent with the final parent outcome. External IC→EVM messages are finalized-only.

## Implemented topology

```text
ConsequenceParent.resolve_case(...)
        |
        | semantic judgment = satisfied
        |
        +---- on="accepted" ----> provisional ConsequenceSink
        |
        +---- on="finalized" ---> settled ConsequenceSink
```

The same positive semantic decision is emitted to two separate sinks. Each sink is idempotent and records total delivery attempts, unique consequences applied, per-case attempts, per-case duplicate count, first sender, and payload.

The parent emits **nothing** when the consensus result is `satisfied = false`. Therefore, if an accepted round emits a positive consequence and a later appeal changes the eventual result to negative, the provisional sink exposes a stale consequence while the settled sink should receive no corresponding finalized consequence.

## Contracts

- `contracts/consequence_parent.py` — semantic parent and timing split.
- `contracts/consequence_sink.py` — idempotent evidence sink.

## Network evidence capture

Every live parent transaction used by this experiment must be captured with Experiment Ledger:

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

Validates that a positive parent decision can eventually reach both sinks after finalization. This is wiring validation, not the appeal experiment itself.

### Appeal/re-execution run
The research run must create or observe a parent transaction that enters an appeal/additional consensus round where possible. No claim about stale provisional state is made unless such a lifecycle is actually captured.

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
- stale provisional effects after a changed final outcome;
- idempotency state required;
- compensation actions required;
- debugging steps needed to reconstruct parent/child lineage.

## Candidate metric: Consequence Stability

A first operational form:

```text
Consequence Stability(case) =
  1 - stale_or_duplicate_irreversible_effects / consequential_effect_attempts
```

This formula is provisional. It must not be promoted into a general metric until experiment results establish that its numerator and denominator are meaningful across workflows.

## Falsifiers
- accepted/finalized produces no meaningful application difference beyond latency;
- robust idempotency/compensation makes provisional execution effectively costless for the tested workflow;
- appeals/additional rounds do not create measurable stale or duplicate effects in the tested scenarios;
- the chosen environment cannot reproduce the relevant appeal/re-execution behavior, in which case no empirical claim is made.

## Safety invariant
Never use a non-idempotent irreversible child effect merely to manufacture a dramatic result. The experiment exposes protocol semantics through reversible/idempotent sinks before testing any economically consequential integration.
