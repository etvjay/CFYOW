# Source Registry

CFYOW prefers primary protocol documentation and original research papers for load-bearing claims.

## GenLayer — primary technical sources

- **Equivalence Principle** — https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle
  - Leader/validator model
  - independent verification requirement
  - strict equality vs comparative/custom validation
  - `run_nondet_unsafe`

- **Non-determinism** — https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism
  - what belongs inside nondeterministic blocks
  - side effects only after agreed nondeterministic output
  - LLM/web operations and validation patterns

- **Messages** — https://docs.genlayer.com/developers/intelligent-contracts/features/messages
  - Intelligent Contract calls/messages
  - transaction-triggered execution
  - accepted vs finalized timing semantics

- **Official project boilerplate** — https://github.com/genlayerlabs/genlayer-project-boilerplate
  - current Python/tooling pattern used by this repository
  - direct-mode tests
  - `genvm-lint`
  - CI structure

## Coordination prior art

- Carriero, N.; Gelernter, D. **Linda in Context.** Communications of the ACM 32(4), 1989.
  - shared tuple-space coordination demonstrates that independent computation coordinating through a common environment long predates blockchains and LLM agents.

- Paredes García, F. **Ledger-State Stigmergy: A Formal Framework for Indirect Coordination Grounded in Distributed Ledger State.** arXiv:2604.03997, 2026.
  - https://arxiv.org/abs/2604.03997
  - explicitly models autonomous blockchain agents coordinating indirectly by observing replicated ledger state.

## Research consequence

CFYOW does **not** claim novelty for shared-state agent coordination. Its narrower research target is whether GenLayer-style **adjudicated judgment-bearing state transitions** materially change what independently governed agents can coordinate over without appointing one central semantic authority.
