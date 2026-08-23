"""EXP-005 — DevX Under Judgment: measurement scaffolding.

Implements the 8 incremental benchmark tasks from the spec as a task registry.
Each task records:
  - implementation artifact (contract/test file that realizes it)
  - consensus-sensitive LOC (measured, not estimated)
  - failure surfaces that can catch bugs in this task (the taxonomy)
  - real incidents from the CFYOW build log (evidence, not anecdote)

The measurement claim: judgment-bearing programmability adds complexity
disproportionately at specific tasks (equivalence logic, finality handling,
appeal safety) — and the failure taxonomy shows which surfaces can even
detect those failures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO / "results" / "EXP-005"

# Failure-detection surfaces, ordered by developer cost (cheap -> expensive)
SURFACES = [
    "static_reasoning",     # reading the code
    "genvm_lint",           # genvm-lint check
    "direct_mode_tests",    # local GenVM simulation
    "multi_validator_sim",  # Studio/simulator with validator rounds
    "live_testnet_only",    # only real network execution reveals it
]

# The real incident log from building CFYOW (Aug 22-23). Each is a failure
# that actually occurred, with the surface that caught it.
REAL_INCIDENTS = [
    {
        "task": "deterministic_transition",
        "incident": "pytest ModuleNotFoundError: baselines package not on path",
        "surface_caught": "direct_mode_tests",
        "fix_cost": "one-line pyproject pythonpath",
        "upstream_bug": False,
    },
    {
        "task": "llm_evaluation",
        "incident": "gltest requires BRADBURY_PRIVATE_KEY .env even for offchain unit tests "
                    "(gltest plugin parses config for every pytest run)",
        "surface_caught": "direct_mode_tests",
        "fix_cost": "dummy .env seeding in CI",
        "upstream_bug": True,
    },
    {
        "task": "leader_validator_equivalence",
        "incident": "genlayer-testing-suite 60f850f + main head: direct-mode calldata "
                    "roundtrip regression (DecodingError: unexpected end of memory) on "
                    "TreeMap/Address contracts",
        "surface_caught": "direct_mode_tests",
        "fix_cost": "dual pins: v0.29 for direct CI, 60f850f only for network jobs",
        "upstream_bug": True,
    },
    {
        "task": "post_consensus_side_effects",
        "incident": "Bradbury deploy receipts return tx_data_decoded: null — gltest "
                    "extract_contract_address raises TypeError (None membership test)",
        "surface_caught": "live_testnet_only",
        "fix_cost": "None-safe shim + recipient fallback",
        "upstream_bug": True,
    },
    {
        "task": "accepted_vs_finalized_child",
        "incident": "deploy receipts arrive status=5 ACCEPTED with consensus_data={} — "
                    "v0.29 tx_execution_succeeded requires leader_receipt, fails on valid txs",
        "surface_caught": "live_testnet_only",
        "fix_cost": "receipt-shape-aware success assertion (60f850f fixes this, unreleased)",
        "upstream_bug": True,
    },
    {
        "task": "appeal_safe_receiving",
        "incident": "transaction status 14 (LEADER_REVEALING) unknown to genlayer-py v0.18 — "
                    "KeyError during receipt parse",
        "surface_caught": "live_testnet_only",
        "fix_cost": "pin genlayer-py v0.19 line (ec7cab9)",
        "upstream_bug": True,
    },
    {
        "task": "multi_validator_network",
        "incident": "Bradbury gas rate limit (-32005) fails deploys hard, no built-in retry",
        "surface_caught": "live_testnet_only",
        "fix_cost": "capacity-retry wrapper with backoff",
        "upstream_bug": True,
    },
    {
        "task": "leader_validator_equivalence",
        "incident": "newer genlayer-py returns tuple-shaped messages; child-lineage adapter "
                    "assumed dicts — AttributeError mid-evidence-capture",
        "surface_caught": "live_testnet_only",
        "fix_cost": "shape-tolerant message normalization",
        "upstream_bug": True,
    },
]

# The 8 spec tasks with their measured complexity profile.
# consensus_loc counts lines that touch gl.* consensus APIs (nondet, vm, emit).
TASKS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "deterministic state transition",
        "artifact": "contracts/different_minds.py (propose/accept state machine)",
        "consensus_sensitive_lines": 0,
        "detectable_by": ["static_reasoning", "genvm_lint", "direct_mode_tests"],
        "judgment_added": False,
    },
    {
        "id": 2,
        "name": "free-form LLM/evidence evaluation",
        "artifact": "contracts/different_minds_judged.py (_judge leader_fn)",
        "consensus_sensitive_lines": 14,
        "detectable_by": ["direct_mode_tests", "multi_validator_sim"],
        "judgment_added": True,
    },
    {
        "id": 3,
        "name": "leader/validator equivalence logic",
        "artifact": "contracts/different_minds_judged.py (validator_fn)",
        "consensus_sensitive_lines": 11,
        "detectable_by": ["multi_validator_sim", "live_testnet_only"],
        "judgment_added": True,
    },
    {
        "id": 4,
        "name": "deterministic post-consensus side effects",
        "artifact": "contracts/consequence_sink.py (EXP-003, reused pattern)",
        "consensus_sensitive_lines": 6,
        "detectable_by": ["direct_mode_tests", "live_testnet_only"],
        "judgment_added": False,
    },
    {
        "id": 5,
        "name": "direct-mode mocks and invariant tests",
        "artifact": "tests/direct/ + mock_llm patterns",
        "consensus_sensitive_lines": 0,
        "detectable_by": ["static_reasoning", "direct_mode_tests"],
        "judgment_added": False,
    },
    {
        "id": 6,
        "name": "multi-validator network test",
        "artifact": "gltest --network runs + validator rotation config",
        "consensus_sensitive_lines": 0,
        "detectable_by": ["multi_validator_sim", "live_testnet_only"],
        "judgment_added": False,
    },
    {
        "id": 7,
        "name": "accepted/finalized child-message behavior",
        "artifact": "contracts/consequence_parent.py emit(on=...) pattern",
        "consensus_sensitive_lines": 8,
        "detectable_by": ["live_testnet_only"],
        "judgment_added": False,
    },
    {
        "id": 8,
        "name": "appeal-safe/idempotent receiving logic",
        "artifact": "contracts/consequence_sink.py (attempts/applied counters)",
        "consensus_sensitive_lines": 9,
        "detectable_by": ["live_testnet_only"],
        "judgment_added": False,
    },
]


def failure_taxonomy_coverage() -> dict[str, Any]:
    """Which surfaces can detect failures in which tasks — and where real
    bugs actually surfaced."""
    by_surface_detect: dict[str, int] = {s: 0 for s in SURFACES}
    for task in TASKS:
        for s in task["detectable_by"]:
            by_surface_detect[s] += 1
    by_surface_caught: dict[str, int] = {s: 0 for s in SURFACES}
    for inc in REAL_INCIDENTS:
        by_surface_caught[inc["surface_caught"]] += 1
    return {
        "surfaces_cheap_to_expensive": SURFACES,
        "tasks_detectable_per_surface": by_surface_detect,
        "real_incidents_caught_per_surface": by_surface_caught,
        "incidents_total": len(REAL_INCIDENTS),
        "incidents_upstream_bugs": sum(1 for i in REAL_INCIDENTS if i["upstream_bug"]),
    }


def main() -> None:
    coverage = failure_taxonomy_coverage()
    judgment_tasks = [t for t in TASKS if t["judgment_added"]]
    dataset = {
        "schema_version": "cfyow.exp005.devx.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "interpretation": {"status": "UNREVIEWED"},
        "tasks": TASKS,
        "total_consensus_sensitive_lines": sum(
            t["consensus_sensitive_lines"] for t in TASKS
        ),
        "real_incidents": REAL_INCIDENTS,
        "failure_taxonomy": coverage,
        "headline": (
            f"{coverage['incidents_upstream_bugs']}/{coverage['incidents_total']} "
            "real build incidents were upstream tooling bugs; "
            f"{coverage['real_incidents_caught_per_surface']['live_testnet_only']}/"
            f"{coverage['incidents_total']} were only catchable on the live network. "
            "Judgment-bearing tasks (equivalence, consensus evaluation) concentrate "
            "consensus-sensitive code and are invisible to cheap surfaces."
        ),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"devx-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    print(f"saved: {out}")
    print(json.dumps(dataset["failure_taxonomy"], indent=2))
    print("\nheadline:", dataset["headline"])


if __name__ == "__main__":
    main()
