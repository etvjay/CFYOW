
# M0 Falsifier Review — Research Frame Lock Review
date: 2026-08-23
scope: every spec'd falsifier vs evidence actually gathered in the Aug 22-23 build sprint.

## EXP-002 — Different Minds, One Interface

| # | Falsifier | Status | Evidence |
|---|---|---|---|
| 1 | agents require hidden shared context to complete the workflow | NOT TRIGGERED | all workflows completed via protocol-visible messages only; zero cross-talk (agents are isolated processes) |
| 2 | interface expands until it becomes a centralized orchestrator API | NOT TRIGGERED | schema fixed at 6 transitions; no expansion pressure observed in 7 scenarios |
| 3 | disagreement cannot be resolved from protocol-visible evidence | **PARTIALLY DEMONSTRATED** | evaluator resolved digest-vs-completion disagreement from visible evidence alone (reasoned about what the digest did NOT show) — resolution worked |
| 4 | GenLayer adds no coordination property beyond deterministic shared state | **OPEN — arm C decides** | deterministic arm settled vacuously 7/7 while judgment caught real gaps; whether *decentralized* judgment adds properties beyond centralized is precisely arm C's question |

## EXP-003 — Accepted vs Finalized
All falsifiers correctly remain OPEN — no live runs. Spec's own escape hatch
("chosen environment cannot reproduce appeal behavior -> no empirical claim")
is currently active by honesty: Bradbury unreproducible, watchdog armed.
Harness fixes landed; nothing claimed.

## EXP-004 — Autonomy Budget

| # | Falsifier | Status | Evidence |
|---|---|---|---|
| 1 | meaningful workflows require external trigger at nearly every stage | WEAKENED for monolithic (ratio 0.67), SUPPORTED for chained (0.33) — architecture-dependent, which is itself a finding |
| 2 | most continuation is syntactic chaining not meaningful progression | PARTIALLY CONFIRMED statically — deepest meaningful run bounded by NEW_INFORMATION + FINALITY_WAIT in both architectures |
| 3 | metric too implementation-dependent to compare honestly | MITIGATED BY DESIGN — both arms measured on identical workflow with same classifier |

## EXP-005 — DevX Under Judgment

| # | Falsifier | Status | Evidence |
|---|---|---|---|
| 1 | substantial tool/context switching but little expressive advantage | REJECTED by current data — expressive advantage demonstrated (EXP-002 arm B catches what A cannot); switching cost real (7/8 incidents) |
| 2 | realistic validation cannot be tested reproducibly before network execution | PARTIALLY CONFIRMED — direct-mode caught only 3/8; but direct-mode DID work where tooling allowed |
| 3 | developers cannot distinguish protocol disagreement from app bugs | NOT YET TESTED — needs multi-validator observation of a genuine disagreement (arm C live) |
| 4 | safest production pattern reduces to deterministic logic + conventional external adjudicator | **SERIOUSLY CONTESTED** — deterministic arm failed 5/5 non-verifiable scenarios; "conventional adjudicator" = arm B which works but is centralized. This falsifier is now the sharpest question in the program |

## Claim ledger impact
- C6 (shared consequence layer interpretation): unchanged, Medium confidence
- C7 (coordination without cognitive convergence): strengthened — heterogeneous
  agents coordinated through the interface alone in all runs; still Unproven
  until arm C tests whether GenLayer specifically adds value over arm B
- NEW claim candidate C8: deterministic consequence interfaces cannot verify
  judgment-dependent completion (EXP-002 arm A vs B divergence, 7/7)

## Verdict
Frame holds. No falsifier fired fatally. Two sharpened questions emerge:
1. Does decentralized adjudication beat centralized judgment (arm C)?
2. Is the safest pattern deterministic-plus-external-adjudicator (EXP-005 #4)?
Both are answerable with the built harness once the network path opens.
M0 gate condition met: frame locked with explicit open questions.
