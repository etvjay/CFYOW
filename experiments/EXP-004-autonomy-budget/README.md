# EXP-004 — Autonomy Budget

## Research question
How much consequential workflow progression can occur after one externally initiated transaction before a fresh offchain decision, signature, evidence publication, or trigger is required?

## Protocol boundary
All Intelligent Contract execution begins from a transaction. An executing IC can emit asynchronous child IC transactions that continue through consensus independently. This means "autonomous" should be measured rather than assumed.

## Workflow

```text
request
  → proposal selection
  → commitment
  → work claim
  → evidence evaluation
  → settlement intent
```

Each transition is classified as one of:
- `INTERNAL_CONTINUATION` — caused by an IC→IC child transaction;
- `EXTERNAL_TRIGGER` — requires a new EOA/EVM transaction;
- `NEW_INFORMATION` — waits for evidence that did not exist at the previous step;
- `NEW_AUTHORITY` — requires a fresh signature/decision from an independent actor;
- `FINALITY_WAIT` — no new decision, but cannot safely progress until state finalizes.

## Candidate metric

### Autonomy budget
The number and significance of consequential workflow transitions that can execute after a given external trigger before another fresh offchain intervention becomes necessary.

Report both:
- **transition budget** — count of internally continuable transitions;
- **semantic budget** — qualitative class of decisions/actions completed before intervention.

A raw count alone can be gamed by splitting one transition into many contracts.

## Metrics
- external triggers per completed workflow;
- child transactions per trigger;
- fresh human/agent signatures;
- new evidence boundaries;
- finality waits;
- wall-clock latency;
- failed/undetermined transitions;
- offchain keeper/orchestrator requirements.

## Falsifiers
- meaningful workflows require a fresh external trigger at nearly every stage;
- most continuation is syntactic contract chaining rather than meaningful autonomous progression;
- the metric is too implementation-dependent to compare systems honestly.

## Research goal
Use the experiment to replace binary language ("autonomous" / "not autonomous") with a measurable account of where workflow liveness and authority actually originate.
