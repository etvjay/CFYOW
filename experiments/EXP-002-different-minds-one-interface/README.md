# EXP-002 — Different Minds, One Interface

## Research question
Can independently governed agents with different models, memory, policies, and owners coordinate through one shared adjudicated interface without a central orchestrator?

## Hypothesis
Cognitive convergence is not required for coordination if agents share a sufficiently explicit consequence interface.

## Agents
- requester — defines objective and accepts commitments;
- provider — proposes terms and submits work/evidence;
- evaluator/adversary — challenges unsupported claims and tests the interface boundary.

The implementations should deliberately differ. At least two agents must use materially different prompts/policies or model stacks. No hidden shared scratchpad is allowed.

## Shared protocol

```text
propose → accept → commit → submit_evidence → evaluate → settle
```

Only protocol-visible inputs may cross actor boundaries.

## Control
Run the same task with a centralized orchestrator that may inspect all agent messages/state.

## Metrics
- direct agent-to-agent assumptions;
- fields required in the shared schema;
- number of orchestrator-only interventions;
- conflicting claims produced;
- state convergence after adjudication;
- task completion rate;
- messages/transactions per completed workflow;
- context leaked/shared between otherwise independent agents.

## Falsifiers
- agents require hidden shared context to complete the workflow;
- the interface expands until it effectively becomes a centralized orchestrator API;
- disagreement cannot be resolved from protocol-visible evidence;
- GenLayer adjudication adds no coordination property beyond deterministic shared state for the selected task.

## Intended result
The experiment should tell us the **minimum shared semantic surface** needed for heterogeneous agents to coordinate. A negative result is useful: it defines where shared state stops being sufficient and richer communication/orchestration becomes necessary.
