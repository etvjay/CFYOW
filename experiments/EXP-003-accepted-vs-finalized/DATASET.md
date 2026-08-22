# EXP-003 Dataset — Accepted World vs Final World

## Benchmark family

**CFYOW Shared Consequence Benchmark**

EXP-003 is the finality module of the benchmark. It measures whether downstream consequences differ depending on whether an autonomous workflow acts on GenLayer `accepted` state or waits for `finalized` state.

The benchmark is not a truth benchmark. It does not score whether validators found objective truth. It scores the observable relationship between a shared adjudicated state transition and the consequences applications attach to that transition.

## Why this dataset exists

The CFYOW thesis is that autonomous actors can keep private cognition while coordinating through shared consequence-bearing state. EXP-003 tests a necessary boundary inside that thesis: a shared state can be recognized before it is settled.

The dataset therefore asks:

> What changes downstream when an application treats a provisional shared world as actionable, and what survives if that world is later re-executed or overturned?

## Dataset units

### 1. Run/case row

One row per `(github_run_id, run_attempt, experiment_id)`.

Purpose:
- distinguish apparatus validity from hypothesis outcome;
- preserve network/toolchain provenance;
- provide one chartable row per experimental case;
- retain raw normalized metrics without overwriting evidence.

Canonical file:

`results/EXP-003/dataset/run-cases.jsonl`

### 2. World-transition event

Planned long-form event rows:
- `submitted`
- `accepted`
- `accepted_child_triggered`
- `appeal_submitted`
- `consensus_round_observed`
- `finalized`
- `finalized_child_triggered`

These events should be derived only from transaction/status/round/child evidence. A later FINALIZED observation must never be backfilled as an ACCEPTED observation if ACCEPTED was not actually observed.

### 3. Consequence-effect event

Planned long-form effect rows:
- provisional delivery attempt;
- provisional application;
- provisional duplicate attempt;
- settled delivery attempt;
- settled application;
- settled duplicate attempt;
- compensation action, if any.

The idempotent `ConsequenceSink` is the authoritative application-level source for attempts/applied state. Emitted messages alone are not counted as successful child execution.

## Run/case schema v1

Each JSONL row contains:

| Field | Meaning |
|---|---|
| `schema_version` | `cfyow.exp003.dataset.case.v1` |
| `benchmark` | `CFYOW Shared Consequence Benchmark` |
| `module` | `EXP-003` |
| `experiment_id` | `EXP-003A` or `EXP-003B` |
| `case_name` | Stable case identifier |
| `run_id` / `run_attempt` | GitHub Actions provenance |
| `github_sha` | Exact source revision |
| `network` | Network under test |
| `generated_at` | Summary generation time |
| `status` | `VALID_RUN`, `INVALID_RUN`, or `NO_RESULT` |
| `step_outcome` | CI step outcome; not a research conclusion |
| `parent_transaction_hash` | Parent transaction when available |
| `artifact_files` | Evidence files captured for the case |
| `failure_phase` / `failure_error` | Apparatus failure provenance |
| `appeal_occurred` | Observed appeal flag when available |
| `round_count` | Observed consensus round count when available |
| `accepted_message_count` | Accepted-timing emitted message count |
| `finalized_message_count` | Finalized-timing emitted message count |
| `triggered_child_count` | Triggered child transaction count |
| `provisional_attempts` | Provisional sink delivery attempts |
| `settled_attempts` | Settled sink delivery attempts |
| `provisional_duplicate_delta` | Duplicate change attributable to the measured interval |
| `settled_duplicate_delta` | Settled duplicate change |
| `stale_provisional` | Evidence-gated stale provisional consequence |
| `finality_latency_ms` | Accepted-to-finalized latency when observed |
| `metrics` | Full normalized metrics object, preserved losslessly |

Missing evidence is represented as `null`, never as zero or false.

## Case definitions

### EXP-003A — Appeal-induced duplicate delivery

Control variable: semantic outcome remains positive across re-execution.

Primary observations:
- whether an appeal occurred;
- whether additional consensus round(s) occurred;
- provisional delivery attempts before/after appeal;
- settled delivery attempts;
- duplicate deltas;
- child transaction receipts.

This case does **not** assume duplicates must occur. A measured duplicate delta of zero is a valid result.

### EXP-003B — Semantic overturn under changed evidence

Controlled change: public evidence changes from `SATISFIED` to `REVOKED` after ACCEPTED and before appeal re-execution.

Strict stale-world gate:
1. initial semantic positive independently evidenced;
2. accepted consequence applied;
3. public evidence mutation independently evidenced;
4. appeal/additional round observed;
5. final semantic negative independently evidenced;
6. finalized positive consequence absent;
7. provisional positive consequence remains.

Only when all seven are observed may `stale_provisional=true`.

## Benchmark outputs

The first benchmark report should expose a vector rather than collapse everything into one score:

```text
{
  finality_latency,
  provisional_effect_rate,
  duplicate_rate,
  stale_effect_rate,
  compensation_cost,
  reversibility
}
```

The candidate scalar `Consequence Stability` remains experimental:

```text
1 - stale_or_duplicate_irreversible_effects / consequential_effect_attempts
```

It must not be promoted as a general score until multiple scenarios show that its numerator and denominator are stable and meaningful.

## Dataset integrity rules

- append-only case history;
- unique key = `(run_id, run_attempt, experiment_id)`;
- raw artifacts remain separate from normalized dataset rows;
- no hypothesis conclusion is written into evidence fields;
- apparatus failure is data about the harness, not evidence for or against the protocol hypothesis;
- secrets, private keys, raw chain-of-thought, and private model traces are forbidden;
- every chart must be reproducible from committed dataset rows or linked raw artifacts.
