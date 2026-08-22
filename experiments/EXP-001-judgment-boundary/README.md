# EXP-001 — Judgment Boundary Benchmark

## Research question
What coordination decision can GenLayer place inside shared consensus that a deterministic contract cannot evaluate without an external adjudicator?

## Scenario
A milestone says:

> Deliver a responsive storefront with working mobile checkout and no material regression in the agreed purchase flow.

A provider submits free-form evidence: text, screenshots, URLs, or a structured description of what was delivered.

The consequential decision is whether the milestone **substantially satisfies the written specification**.

## Three architectures

### A — Deterministic baseline
The deterministic implementation accepts only pre-structured boolean attestations such as:

```python
{
  "responsive": True,
  "mobile_checkout": True,
  "purchase_flow_regression_free": False,
}
```

The contract/code can resolve those facts deterministically. The experiment records that the semantic judgment needed to produce those booleans happened upstream.

### B — Centralized adjudicator
One trusted human/LLM/backend reads the specification and evidence and returns:

```json
{
  "satisfied": true,
  "score": 84,
  "rationale": "..."
}
```

The application can now consume free-form evidence, but downstream state inherits the adjudicator's authority.

### C — GenLayer Intelligent Contract
The Intelligent Contract performs the same free-form evaluation inside a nondeterministic block. A leader proposes the judgment; validators independently run the same task. The validator requires:

- the same `satisfied` decision;
- valid scores from 0–100;
- scores in the same 10-point bucket.

Only the accepted result is persisted into milestone state.

## Variables

| Variable | A: Deterministic | B: Centralized | C: GenLayer |
|---|---|---|---|
| Free-form evidence interpreted in decision path | No | Yes | Yes |
| Judgment authority | Upstream attestor | One adjudicator | Validator process |
| Deterministic downstream state | Yes | Yes | Yes after returned decision |
| Disagreement handling | Before input | Operator-defined | Validator agreement / protocol path |
| Appeal semantics | Application-defined | Application-defined | Protocol + application semantics |
| New trust assumption | Attestor | Adjudicator | Validator/equivalence mechanism + evidence/model dependencies |

## Metrics

1. **Judgment location** — where ambiguous evidence becomes a decision.
2. **Trusted decision authorities** — actors/services whose unilateral output becomes consequential.
3. **Evidence transformation count** — number of transformations before consensus-critical code can use the evidence.
4. **Decision reproducibility** — agreement rate over repeated/multi-validator runs.
5. **Outcome stability** — variance in `satisfied` and score bucket.
6. **Latency** — submission to accepted/finalized result.
7. **Developer burden** — implementation, mocks, validator design, integration steps, and debugging.
8. **Failure surface** — malformed evidence, divergent LLM output, validator disagreement, undetermined transactions, appeals.

## Falsifiers

The working thesis is weakened if any of these dominate:

- robust GenLayer validation requires an authority equivalent to the centralized adjudicator;
- validator disagreement is too high for the semantic criterion to be operationally useful;
- the deterministic baseline can represent the same evidence/decision without merely relocating judgment upstream;
- GenLayer's latency/complexity exceeds its reduction in centralized decision authority for the tested workflow;
- the observed result depends primarily on one shared model/provider rather than independent validation.

## Test layers

### Unit/direct mode
Purpose: contract invariants and deterministic plumbing.

These tests **do not prove distributed consensus quality** because mocked LLM outputs remove actual model disagreement.

### Multi-validator / network run
Purpose: measure real validator agreement, nondeterministic variation, latency, and finality behavior.

Every run must record:

```text
network / simulator version
contract commit SHA
validator configuration
model/provider configuration if observable
exact specification
exact evidence
leader result
validator/protocol outcome
accepted timestamp
finalized timestamp
appeal/re-execution events
```

## Current state
Implementation scaffold complete. Direct-mode validation is next; multi-validator measurements remain unclaimed until run artifacts are committed under `results/EXP-001/`.
