# Adversarial Review

## The strongest skeptical reading

CFYOW may be describing an old coordination pattern with new vocabulary.

A replicated ledger already gives independently controlled actors a common state machine. Shared tuple spaces, blackboard systems, workflow engines, multisigs, oracle networks, courts, and committee-based protocols already let participants coordinate around state they did not individually author. Adding LLMs and validator voting does not automatically create a new primitive.

The research therefore fails if its core claim collapses to:

> Agents can coordinate by reading shared blockchain state.

That claim is neither new nor GenLayer-specific.

## Attack 1 — Judgment is merely relocated

A GenLayer Intelligent Contract may appear to eliminate a central adjudicator while actually relocating authority into:
- validator selection;
- common model/provider behavior;
- prompt construction;
- shared external sources;
- equivalence criteria;
- protocol governance.

**Required test:** EXP-001 must enumerate every trust dependency rather than counting only obvious backend operators.

## Attack 2 — Consensus does not repair bad evidence

If all validators read misleading, incomplete, poisoned, or adversarial evidence, agreement can still produce a bad external-world conclusion.

**Boundary:** protocol agreement is not objective truth.

## Attack 3 — Model diversity may be cosmetic

Multiple validators do not necessarily imply independent semantic judgment if they use the same underlying model family, provider, system prompt assumptions, or correlated web sources.

**Required measurement:** record observable validator/model configuration wherever the network exposes it and avoid equating validator count with epistemic independence.

## Attack 4 — Determinism may still be preferable

Many workflows that sound semantic can be redesigned around attestations, typed schemas, cryptographic proofs, objective APIs, threshold signatures, or explicit human approval. Those approaches may be cheaper and easier to verify.

**Required test:** always include the strongest deterministic reduction, not a deliberately weak strawman.

## Attack 5 — The central backend may be operationally superior

A centralized adjudicator can be faster, cheaper, observable, retryable, and easier to upgrade. For low-stakes or single-operator applications, decentralizing judgment may be economically irrational.

**Required result:** CFYOW should identify the coordination conditions under which shared adjudication is worth its cost, not argue that it is universally superior.

## Attack 6 — "Autonomous workflow" may be overstated

If every meaningful stage requires a new external transaction, signature, data publication, or operator action, then the protocol is a coordination state machine, not an autonomous runtime.

**Required test:** EXP-004 counts fresh external triggers and introduces the tentative metric `autonomy budget` only if it proves analytically useful.

## Attack 7 — Appeals complicate consequence semantics

Provisional acceptance can cause downstream effects that later conflict with a successful appeal. This can force idempotency, compensation, or delayed action.

**Required test:** EXP-003 must observe the actual application-level consequences of accepted-vs-finalized messaging rather than discussing finality abstractly.

## Publication rule

A negative result is publishable. If GenLayer adds substantial developer/latency complexity without materially changing the tested coordination boundary, CFYOW should say so directly.
