# GenLayer Network Capture Adapter

Module: `experiment_ledger.adapters.genlayer_network`

## Purpose

Capture node-observable GenLayer transaction lifecycle evidence for Experiment Ledger without inventing hidden validator reasoning.

## CLI

```bash
python -m experiment_ledger capture-genlayer \
  --rpc http://localhost:9151 \
  --tx 0xTRANSACTION_HASH \
  --contract 0xCONTRACT_ADDRESS \
  --output results/EXP-003/runs/network-001.json
```

`--contract` is optional. When supplied, the adapter snapshots both accepted and finalized contract state through `gen_getContractState`.

## Captured evidence

- distinct transaction statuses observed while polling;
- status codes;
- observation timestamps;
- full `gen_getTransactionReceipt` payload;
- number of consensus rounds;
- per-round leader index;
- vote committed/revealed counts;
- validator addresses exposed by the receipt;
- validator vote hashes and result hashes;
- appeal bond and appeal timestamp signals;
- transaction execution hash;
- accepted/finalized contract-state snapshots when a contract address is supplied.

## Derived fields

The adapter derives only facts mechanically supported by captured data:

- `accepted_observed` — ACCEPTED was actually seen by the poller;
- `finalized_observed` — FINALIZED was actually seen;
- `appeal_observed` — an appeal status was seen or `AppealSubmitted` is non-zero;
- `round_count` — number of public receipt rounds;
- `reexecution_or_additional_round_observed` — more than one consensus round is present.

These are observations, not semantic conclusions.

## Explicitly unavailable

The adapter marks the following unavailable rather than inferring them:

- validator private reasoning;
- validator prompt/model context;
- semantic meaning of a validator result hash without separate trace/equivalence-output evidence.

## Important timing property

If capture starts after ACCEPTED has already transitioned away, `accepted_observed` remains `false`. FINALIZED does not cause the adapter to retroactively fabricate an observed ACCEPTED transition.

## Failure semantics

A polling timeout returns:

```json
{
  "status": "INVALID_RUN",
  "failure": {
    "type": "POLL_TIMEOUT"
  }
}
```

Network/infrastructure failure is therefore distinguishable from a protocol or hypothesis failure.

## Next integration

EXP-003 should use this adapter to compare accepted-triggered and finalized-triggered workflow effects. Child-transaction discovery must be added only against a documented/stable node or SDK endpoint; do not infer child calls from parent logs alone.
