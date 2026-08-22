# EXP-005 — DevX Under Judgment

## Research question
Does judgment-bearing programmability create disproportionate developer reasoning, testing, and operational complexity relative to the expressive benefit it adds?

## Benchmark tasks
Implement the same workflow incrementally:

1. deterministic state transition;
2. free-form LLM/evidence evaluation;
3. leader/validator equivalence logic;
4. deterministic post-consensus side effects;
5. direct-mode mocks and invariant tests;
6. multi-validator network test;
7. accepted/finalized child-message behavior;
8. appeal-safe/idempotent receiving logic.

## Measurements

### Build effort
- files/modules touched;
- consensus-sensitive lines of code;
- prompt/criteria revisions;
- test cases required;
- time/steps from change to validated result.

### Failure taxonomy
Record whether each failure is detectable by:
- ordinary Python/static reasoning;
- `genvm-lint`;
- direct-mode tests;
- multi-validator Studio/simulator tests;
- live/testnet execution only.

### Debug burden
- number of artifacts/log surfaces inspected;
- ability to reproduce validator disagreement;
- visibility into leader result and validation outcome;
- parent/child transaction tracing;
- distinction between application error, VM error, disagreement, appeal, and finality wait.

## Programmability gain
For every new DevX burden, identify the exact capability it purchased. Examples:
- interpreting free-form evidence;
- tolerating semantic variation;
- moving a decision out of one centralized adjudicator;
- acting provisionally before finality;
- composing multiple Intelligent Contracts.

If a burden has no demonstrated capability gain, count it as pure complexity.

## Falsifiers
- judgment support adds substantial tool/context switching but little expressive advantage over a simpler architecture;
- realistic validation cannot be tested reproducibly before network execution;
- developers cannot distinguish protocol disagreement from application bugs with reasonable observability;
- the safest production pattern reduces back to deterministic logic plus a conventional external adjudicator.

## Intended output
A **judgment programmability cost map**, not a subjective "good/bad DevX" score. The final research should state which classes of GenLayer application justify the additional semantic and operational burden.
