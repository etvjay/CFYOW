# Claim Ledger

| ID | Claim | Type | Current support | Confidence | Caveat / falsifier |
|---|---|---|---|---|---|
| C1 | Intelligent Contracts can use LLM and web-dependent non-deterministic operations inside explicit nondeterministic blocks. | Fact | GenLayer docs: Non-determinism | High | External data/model quality remains a dependency. |
| C2 | The Equivalence Principle lets validators verify a leader's non-deterministic result under an application-defined validation strategy. | Fact | GenLayer docs: Equivalence Principle | High | Consensus on acceptability is not proof of external truth. |
| C3 | Custom validators should independently verify substantive decisions rather than only checking leader-output format. | Fact | GenLayer docs: Equivalence Principle | High | Poor validator design can collapse back into trusting the leader. |
| C4 | Intelligent Contract execution is transaction-triggered, though executing ICs can continue work through child IC transactions. | Fact | GenLayer docs: Messages | High | External liveness can still bound practical autonomy. |
| C5 | Accepted and finalized timing expose different downstream safety properties. | Fact | GenLayer docs: Messages / finality | High | Application-level impact must be measured in EXP-003. |
| C6 | GenLayer can be modeled as a shared consequence layer for agents. | Interpretation | C1-C5 + experiments | Medium | Could be reducible to replicated state + adjudication. |
| C7 | Heterogeneous agents can coordinate without cognitive convergence if they share an adjudicated interface. | Hypothesis | EXP-002 | Unproven | Existing shared-state protocols may already satisfy the requirement. |
| C8 | GenLayer expands practical programmability by moving some judgment-dependent transitions into the consensus-critical program. | Hypothesis | EXP-001/005 | Medium | Similar systems can be composed from oracles, multisigs, committees, courts, or centralized AI. |
| C9 | Finality is part of agent autonomy semantics, not merely settlement semantics. | Proposed concept | EXP-003/004 | Unproven | Compensation may make provisional state safe enough for some workflows. |
| C10 | Networks of Intelligent Contracts can serve as programmable shared environments for independently governed agents. | Speculation | EXP-002/004 | Unproven | Cost, latency, trigger dependence, and evidence availability may make this narrow in practice. |

## Claim discipline

No claim moves from **hypothesis** to **result** without an experiment artifact under `results/` that records configuration, inputs, observed outputs, and limitations.

No protocol result is described as "truth" unless the claim is explicitly about protocol truth (for example, what state the chain finalized). External-world claims remain evidence-dependent judgments.
