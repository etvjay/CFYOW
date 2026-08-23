# Consequence Stability Harness

Reusable EXP-003 module for comparing provisional (`accepted`) and settled (`finalized`) internal-message consequences.

## Contracts

### `ConsequenceSink`
Deploy twice: one instance for provisional consequences and one for settled consequences.

Public methods:

- `record_consequence(case_id, payload)` — idempotent write. Every call increments attempt counters; only the first call for a case applies the consequence.
- `get_record(case_id)` — returns existence, attempts, duplicate count, applied flag, payload, and first sender.
- `get_totals()` — aggregate attempts, unique applications, and duplicate attempts.

### `ConsequenceParent`
Constructor arguments:

```text
provisional_sink: Address
settled_sink: Address
```

Public method:

```text
resolve_case(case_id, specification, evidence)
```

A positive semantic judgment emits the same payload twice:

```python
provisional.emit(on="accepted").record_consequence(case_id, "satisfied")
settled.emit(on="finalized").record_consequence(case_id, "satisfied")
```

A negative judgment emits no child consequence.

## Why separate sinks?

Using distinct sinks makes the timing policy an explicit experimental variable. It avoids relying on event ordering or decoding one mixed state surface to determine which delivery path produced a consequence.

## Evidence collection

1. Start network capture before submitting the parent transaction when accepted-to-finalized timing matters.
2. Submit `resolve_case`.
3. Persist the parent lifecycle JSON through `experiment_ledger capture-genlayer`.
4. Use `capture_child_lineage(client, parent_tx_hash)` to record emitted messages and triggered child transaction IDs.
5. Read both sinks after the relevant lifecycle completes.
6. Record per-sink `attempts` and `duplicate_count` into the experiment result.

## Interpretation boundary

- An emitted message is not automatically a successful child execution.
- A triggered child transaction is not automatically a successful consequence application.
- A duplicate child transaction is not automatically harmful because the sink is intentionally idempotent.
- A stale provisional consequence requires evidence that the final parent outcome would not emit that consequence.

## Frontend / observer consumption

A UI can expose:

```text
case_id
provisional.attempts
provisional.duplicate_count
provisional.applied
settled.attempts
settled.duplicate_count
settled.applied
parent.accepted_observed
parent.finalized_observed
parent.appeal_observed
parent.round_count
```

Do not label the accepted state as final or settled.
