# CFYOW Documentation Audit

**Project:** Can't Fake Your Own World
**Audit scope:** `article/cantfake-your-own-world.md` and supporting research notes
**Method:** Docs Foundry + Research Foundry + Experiment Foundry review
**Status:** audit before rewrite

## What is strong

- The article has a concrete research question.
- It distinguishes deterministic, centralized-judgment, and decentralized-judgment arms.
- It reports sample sizes and measured results.
- It preserves limitations and replication needs.
- It names falsifiers rather than presenting the thesis as settled.
- It separates coordination from verification, which is the paper's strongest conceptual distinction.

## AI-slop and readability findings

| Location/pattern | Problem | Treatment |
|---|---|---|
| Opening builds several short thesis slogans | Delays the concrete question | Keep one thesis, then state the experiment |
| “It works.” | Overstates simulator evidence before qualification | Replace with exact evidence state: mechanism executed in simulator |
| “The thesis-deciding arm” | Dramatic and imprecise | Use decentralized-judgment arm |
| “The title is the finding.” | Rhetorical flourish, no evidentiary content | Remove |
| “The interesting engineering lives between those two facts.” | Generalized closing without a decision | Replace with the next falsifiable experiment |
| “The only thing that survived every attempt to fake it…” | Overclaims from the tested scenario set | Narrow to the observed scenario classes |
| Repeated “not X, but Y” contrasts | AI-like rhetorical cadence | Keep only where the distinction changes the conclusion |
| “This is the experimental version of…” | Introduces coined language before fully defining it | Define the term once, then use it sparingly |

## Claim corrections required

1. State the simulator boundary before discussing decentralized judgment results.
2. Keep the 30-case result tied to the tested scenarios and judge protocol.
3. Separate direct-perception claims from testimony-based evidence claims.
4. Keep “independent replication is pending” adjacent to the result it limits.
5. Replace broad statements about GenLayer with the exact environment and run status.
6. Make the next experiment concrete: direct-perception decentralized judgment versus centralized direct-perception judgment, with the same scenarios and acceptance criteria.

## Comprehension order for rewrite

1. Research question
2. Why deterministic state is insufficient for verification claims
3. Experimental arms
4. What was actually measured
5. Findings, one at a time
6. What the findings do not establish
7. Theory update
8. Next experiment

## Rewrite constraint

Do not add new concepts, account taxonomies, or product claims. CFYOW is an experiment paper. Its job is to report what was tested, what was observed, what remains uncertain, and what should be tested next.

## Evidence classification

- **Observed:** run outputs, case counts, accuracy results, transition depths, incident counts.
- **Interpretation:** testimony has weaker sensitivity than direct perception; judgment is required for some verification claims.
- **Open question:** whether decentralized judgment improves outcomes over a centralized judge at realistic scale.
- **Not established:** universal superiority of decentralized judgment, production reliability, or general market value.
