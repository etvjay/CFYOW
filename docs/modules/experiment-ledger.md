# Experiment Ledger v1

## What it is

A project-agnostic experiment capture layer. It discovers declared baselines from a registry, executes every declared implementation, fingerprints source and scenario inputs, records failures instead of hiding them, and writes a normalized JSON run envelope.

It does **not** decide whether the hypothesis is true. Interpretation remains a separate review step.

## Files

- `skills/experiment-ledger/SKILL.md` — experiment methodology and invariants
- `experiment_ledger/core.py` — capture primitives
- `experiment_ledger/manifest.py` — manifest/registry discovery
- `experiment_ledger/__main__.py` — CLI
- `experiment_ledger/registry/baselines.json` — reusable baseline registry
- `experiment_ledger/schema/*.json` — versioned schemas
- `experiment_ledger/adapters/` — project-specific adapters into the common result envelope

## Run the CFYOW baseline calibration

```bash
python -m experiment_ledger run \
  experiments/EXP-001-judgment-boundary/baseline-manifest.json \
  --run-id local-baseline-calibration
```

Default output:

```text
results/EXP-001-baseline-calibration/runs/local-baseline-calibration.json
```

Validate it:

```bash
python -m experiment_ledger validate \
  results/EXP-001-baseline-calibration/runs/local-baseline-calibration.json
```

## Register a baseline

Add one entry to `experiment_ledger/registry/baselines.json`:

```json
{
  "baseline_id": "my-baseline-v1",
  "type": "deterministic",
  "implementation": "baselines/my_baseline.py",
  "entrypoint": "my_package.adapters:run_my_baseline",
  "version": "repository-source",
  "configuration_hash": "computed-at-run",
  "dependency_fingerprint": "computed-at-run",
  "trust_model": ["trusted component A"]
}
```

The entrypoint receives the complete scenario input and returns a JSON-serializable result.

## Declare an experiment

The manifest names baseline IDs rather than manually wiring implementations:

```json
{
  "schema_version": "experiment-ledger.manifest.v1",
  "experiment_id": "EXP-XXX",
  "hypothesis": {
    "statement": "...",
    "falsifier": "..."
  },
  "scenario": {
    "id": "scenario-001",
    "input": {}
  },
  "baselines": ["my-baseline-v1"],
  "targets": []
}
```

## Evidence rules

1. A declared baseline must never be silently omitted.
2. Implementation exceptions are captured as structured failures.
3. Scenario inputs are SHA-256 fingerprinted using canonical JSON.
4. Baseline source files are SHA-256 fingerprinted at run assembly.
5. Writes are atomic (`.tmp` then `os.replace`).
6. Raw results and errors live under `implementations`.
7. `interpretation.status` begins as `UNREVIEWED` and is never inferred from the measurements.

## What still needs adapters

Network-specific systems such as GenLayer consensus require adapters that capture transaction hashes, validator observations, accepted/finalized transitions, appeals, re-executions, and child transactions. Those fields already have a place in the run envelope, but v1 does not invent observations it cannot retrieve.
