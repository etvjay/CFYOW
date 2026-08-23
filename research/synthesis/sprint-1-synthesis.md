# CFYOW Synthesis — Sprint 1 (Aug 22-23, 2026)

Status: DRAFT — interpretation fields in datasets remain UNREVIEWED pending
arm C live-network replication.

## What this sprint established

Three of five experiments moved from spec to executing machinery with real
data. The research frame survived a full falsifier review. One experiment
(EXP-005) reached REPRODUCED evidence grade; EXP-002 reached VALIDATED with
all three adjudication arms producing data.

## Finding 1 — Adjudication epistemics determine outcomes (EXP-002)

On identical workflows with identical evidence:

- A deterministic consequence interface settled 100% of scenarios "satisfied",
  including fabricated and unproven ones. It cannot discriminate because it
  cannot ask whether evidence demonstrates completion.
- A centralized LLM judge scored 7/7 against hidden ground truth across three
  scenario classes (verifiable / unproven / false-claim) — both sensitivity
  and specificity.
- GenLayer consensus evaluation was verified end-to-end in simulator: leader
  proposes over live-fetched web evidence, validators verify under the
  equivalence principle, quorum records the verdict.

**Claim shape:** deterministic shared state coordinates but cannot verify
judgment-dependent completion. Verification requires judgment. Whether that
judgment must be decentralized is precisely arm C's live question — the
simulator result proves the mechanism executes; the live comparison decides
whether decentralization adds properties beyond correctness of verdict.

## Finding 2 — Architecture is an autonomy/auditability trade (EXP-004)

The same workflow as one monolithic contract has autonomy ratio 0.67 with a
deepest autonomous run of 3 transitions; as chained ICs it drops to 0.33 with
deepest run 1 — but every authority boundary becomes an explicit, auditable
external trigger. NEW_INFORMATION and FINALITY_WAIT bound autonomy in both:
even maximal internal continuation must wait for evidence to exist and
consensus to finalize. Autonomy has epistemic limits independent of
architecture.

## Finding 3 — The DevX burden is real, concentrated, and mostly upstream (EXP-005)

Eight real incidents during the build: 7 were upstream tooling bugs, 5 were
only detectable on the live network, and zero were caught by static reading
or linting. Consensus-sensitive code concentrates entirely in judgment-bearing
tasks (equivalence logic, consensus evaluation). Practical implication:
review effort should weight those files disproportionately, and any team
adopting this stack should expect testnet-only failure classes that no local
surface can preempt. Full incident log + upstream draft in
docs/upstream-issue-draft.md (internal).

## Open questions (ranked)

1. Does decentralized multi-model adjudication produce better or more
   defensible outcomes than the best centralized judge? (arm C live)
2. Is the safest production pattern actually deterministic logic plus a
   conventional external adjudicator? (EXP-005 falsifier #4 — contested but
   not decided; arm B's accuracy keeps it alive)
3. What breaks when downstream actions rely on accepted rather than finalized
   state? (EXP-003 harness merged, execution gated)

## Blockers

Single root blocker: no released genlayer-test/genlayer-py pair both deploys
and parses receipts on Bradbury (docs/upstream-issue-draft.md). Watchdog
armed to fire EXP-003 the moment capacity allows. All harnesses are ready;
nothing further blocks on our side.

## Next

- Live arm C replication -> REPRODUCED grade -> thesis signal for EXP-002
- EXP-003 first VALID_RUN
- M4 cross-experiment synthesis once two experiments hold live-network evidence
