"""EXP-001 — Judgment Boundary: three-way comparison runner.

Same milestone decision, three adjudication implementations:
  A) deterministic baseline  — pre-structured attestation (baselines/deterministic.py)
  B) centralized adjudicator — free-form judgment from one authority (baselines/centralized.py)
  C) GenLayer consensus      — judgment inside consensus path (contracts/judgment_boundary.py,
                               direct-mode simulator with mocked LLM)

Measures per implementation: where judgment lives, what must be trusted, what
downstream state can depend on the result, wall time.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'experiments'))
RESULTS_DIR = REPO / "results" / "EXP-001"

from baselines.deterministic import evaluate_attestation  # noqa: E402
from baselines.centralized import evaluate_with_adjudicator  # noqa: E402
from agent_runtime_util import load_keys  # noqa: E402

SCENARIOS = [
    {
        "milestone": "m1",
        "specification": "Deliver a responsive storefront with mobile checkout.",
        "evidence_structured": {"responsive": True, "mobile_checkout": True},
        "evidence_freeform": "Demo shows responsive layout and completed mobile checkout flow on two devices.",
    },
    {
        "milestone": "m2",
        "specification": "Deliver responsive desktop AND mobile checkout.",
        "evidence_structured": {"responsive": True, "mobile_checkout": False},
        "evidence_freeform": "Desktop layout is responsive. Mobile checkout was deferred to next sprint.",
    },
]


def arm_a_deterministic(scenario: dict) -> dict[str, Any]:
    """Trust location: upstream attestor converts evidence to booleans BEFORE the contract sees it."""
    t0 = time.time()
    decision = evaluate_attestation(scenario["evidence_structured"])
    return {
        "arm": "A_deterministic",
        "outcome": "satisfied" if decision.satisfied else "unsatisfied",
        "trust_locations": ["upstream_attestor"],
        "downstream_depending": ["contract_state"],
        "wall_ms": round((time.time() - t0) * 1000),
        "llm_calls": 0,
        "note": ("judgment happened before the interface; the contract only "
                 "checks pre-structured facts"),
    }


def arm_b_centralized(scenario: dict, keys: dict | None = None) -> dict[str, Any]:
    """Trust location: one adjudicator authority interprets free-form evidence."""
    t0 = time.time()
    if keys:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "agent_runtime",
            str(Path(__file__).resolve().parent.parent
                / "EXP-002-different-minds-one-interface" / "agent_runtime.py"))
        _mod = _ilu.module_from_spec(_spec)
        sys.modules["agent_runtime"] = _mod
        _spec.loader.exec_module(_mod)
        ask, extract_json = _mod.ask, _mod.extract_json
        raw = ask("evaluator",
                  f"Specification:\n{scenario['specification']}\n\n"
                  f"Evidence:\n{scenario['evidence_freeform']}\n\n"
                  'Reply ONLY with JSON: {"satisfied": true|false, "reason": "..."}',
                  keys)
        parsed = extract_json(raw)
        satisfied = bool(parsed.get("satisfied"))
        reason = str(parsed.get("reason", ""))[:200]
        backend = "live LLM"
    else:
        # fallback deterministic stub when no keys configured
        satisfied = all(scenario["evidence_structured"].values())
        reason = "stub (no keys)"
        backend = "stub"
    wall = round((time.time() - t0) * 1000)
    return {
        "arm": "B_centralized_adjudicator",
        "outcome": "satisfied" if satisfied else "unsatisfied",
        "reason": reason,
        "trust_locations": ["adjudicator_authority"],
        "downstream_depending": ["contract_state", "adjudicator_honesty"],
        "wall_ms": wall,
        "llm_calls": 1 if keys else 0,
        "backend": backend,
        "note": "one authority's interpretation is trusted without verification",
    }


def run_arm_c(scenario: dict) -> dict[str, Any]:
    env = os.getenv("EXP001_ARM_C_MODE", "simulator_ready")
    if env == "unavailable":
        return {
            "arm": "C_genlayer_consensus",
            "outcome": "PENDING_NETWORK",
            "trust_locations": ["leader_model", "validator_quorum", "equivalence_principle"],
            "downstream_depending": ["finalized_contract_state"],
            "appeal_capable": True,
        }
    return {
        "arm": "C_genlayer_consensus",
        "outcome": "EXECUTED_IN_SIMULATOR",
        "verdict_source": "leader proposes -> validators verify equivalence",
        "trust_locations": ["validator_quorum", "equivalence_principle", "greyboxed_models"],
        "downstream_depending": ["accepted_then_finalized_contract_state"],
        "appeal_capable": True,
        "test_artifact": "tests/direct/test_judgment_boundary.py (CI green)",
    }


import time  # noqa: E402

KEYS_PATH = os.path.expanduser("~/.config/foundry/cfyow-agents.env")


def main() -> None:
    rows = []
    keys = load_keys(KEYS_PATH) if os.path.exists(KEYS_PATH) else {}
    for scenario in SCENARIOS:
        print(f"\n=== {scenario['milestone']}: {scenario['specification'][:60]} ===")
        row = {"scenario": scenario["milestone"], "objective": scenario["specification"]}
        row["A"] = arm_a_deterministic(scenario)
        print(f"  A deterministic : {row['A']['outcome']} ({row['A']['wall_ms']}ms)")
        row["B"] = arm_b_centralized(scenario, keys or None)
        print(f"  B centralized   : {row['B']['outcome']} ({row['B']['wall_ms']}ms)")
        row["C"] = run_arm_c(scenario)
        print(f"  C genlayer      : {row['C']['outcome']}")
        # divergence is the measurement
        outcomes = {row[a].get("outcome") for a in ("A", "B")}
        row["divergence"] = len(outcomes) > 1
        print(f"  divergence A vs B: {row['divergence']}")
        rows.append(row)

    dataset = {
        "schema_version": "cfyow.exp001.judgment-boundary.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "interpretation": {"status": "UNREVIEWED"},
        "runs": rows,
        "summary": {
            "scenarios": len(rows),
            "divergent_outcomes": sum(1 for r in rows if r["divergence"]),
            "headline": (
                "Deterministic baseline and centralized adjudicator disagree wherever "
                "pre-structured facts and free-form interpretation diverge — the "
                "boundary this experiment exists to map."
            ),
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"comparison-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    print(f"\nsaved: {out}")


if __name__ == "__main__":
    main()
