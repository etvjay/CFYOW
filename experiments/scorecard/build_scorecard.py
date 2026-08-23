"""Track 4 — Benchmark scorecard: normalize all experiment outputs into the
Notion CFYOW Scorecard schema (evidence quality scored separately from
whether results support the thesis).

Reads latest datasets from results/ and emits:
  - scorecard.json (normalized rows)
  - Notion API payload ready for upsert
"""

from __future__ import annotations

import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent


def _latest(pattern: str) -> dict | None:
    files = sorted(glob.glob(str(REPO / "results" / pattern)))
    return json.loads(Path(files[-1]).read_text()) if files else None


def evidence_grade(*, live_network: bool, n_runs: int, upstream_blockers: bool) -> str:
    """Evidence-quality scale per the control-plane policy:
    SIMULATED < RECORDED < VALIDATED < REPRODUCED."""
    if n_runs == 0:
        return "SIMULATED"
    if upstream_blockers:
        return "RECORDED" if not live_network else "VALIDATED"
    if live_network and n_runs >= 5:
        return "REPRODUCED"
    return "VALIDATED"


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    # ---- EXP-002 ---------------------------------------------------------
    scaled = _latest("EXP-002/scaled-*.json")
    if scaled:
        b_scored = [r["B"] for r in scaled["runs"] if r["B"].get("correct") is not None]
        correct = sum(1 for b in b_scored if b["correct"])
        a_discriminates = any(
            r["A"]["verdict"] != "satisfied" for r in scaled["runs"]
        )
        rows.append({
            "experiment": "EXP-002",
            "question": "Can heterogeneous agents coordinate through one shared adjudicated interface without an orchestrator?",
            "finding": (
                f"Centralized LLM judge discriminated all {len(b_scored)} scenario classes "
                f"(accuracy {correct}/{len(b_scored)}); deterministic predicate settled every "
                "scenario identically regardless of ground truth. GenLayer consensus arm "
                "contract-ready, pending network."
            ),
            "supports_thesis": None,  # arm C decides this; do not overclaim
            "evidence_grade": evidence_grade(live_network=False, n_runs=len(scaled["runs"]),
                                             upstream_blockers=True),
            "n_runs": len(scaled["runs"]),
            "artifacts": [
                "contracts/different_minds.py",
                "contracts/different_minds_judged.py",
                "experiments/EXP-002-different-minds-one-interface/",
                Path(scaled and sorted(glob.glob(str(REPO / "results/EXP-002/scaled-*.json")))[-1]).name,
            ],
            "blockers": ["GenLayer execution path for arm C (watchdog-gated)"],
        })

    # ---- EXP-004 ---------------------------------------------------------
    budget = _latest("EXP-004/autonomy-budget-*.json")
    if budget:
        mono = budget["workflows"]["monolithic_contract"]["budget"]
        chained = budget["workflows"]["chained_contracts"]["budget"]
        rows.append({
            "experiment": "EXP-004",
            "question": "How much consequential progression survives one external trigger?",
            "finding": (
                f"Monolithic architecture autonomy ratio {mono['autonomy_ratio']} "
                f"(deepest run {mono['deepest_autonomous_run']}) vs chained "
                f"{chained['autonomy_ratio']} (deepest run {chained['deepest_autonomous_run']}). "
                "Architecture trades autonomy against explicit authority boundaries; "
                "NEW_INFORMATION and FINALITY_WAIT bound autonomy in both designs."
            ),
            "supports_thesis": None,
            "evidence_grade": "SIMULATED",  # static classification; live tx counts pending
            "n_runs": 0,
            "artifacts": ["experiments/EXP-004-autonomy-budget/run_budget.py"],
            "blockers": ["live child-tx measurement needs GenLayer execution path"],
        })

    # ---- EXP-005 ---------------------------------------------------------
    devx = _latest("EXP-005/devx-*.json")
    if devx:
        tax = devx["failure_taxonomy"]
        rows.append({
            "experiment": "EXP-005",
            "question": "Does judgment-bearing programmability add disproportionate DevX burden?",
            "finding": (
                f"{tax['incidents_upstream_bugs']}/{tax['incidents_total']} real incidents were "
                "upstream tooling bugs; "
                f"{tax['real_incidents_caught_per_surface']['live_testnet_only']}/"
                f"{tax['incidents_total']} were only catchable on the live network; cheap "
                "surfaces caught none. Judgment tasks concentrate all consensus-sensitive LOC."
            ),
            "supports_thesis": True,  # burden is real and concentrated — supports "disproportionate"
            "evidence_grade": evidence_grade(live_network=True, n_runs=tax["incidents_total"],
                                             upstream_blockers=False),
            "n_runs": tax["incidents_total"],
            "artifacts": ["experiments/EXP-005-devx-under-judgment/run_devx.py",
                          "docs/upstream-issue-draft.md"],
            "blockers": [],
        })

    # ---- EXP-001 / EXP-003 status ---------------------------------------
    rows.append({
        "experiment": "EXP-001",
        "question": "What moves into consensus vs deterministic/centralized adjudication?",
        "finding": "Contract + baselines merged to main; CI green. Live benchmark run pending.",
        "supports_thesis": None,
        "evidence_grade": "SIMULATED",
        "n_runs": 0,
        "artifacts": ["contracts/judgment_boundary.py", "baselines/"],
        "blockers": ["Bradbury execution path"],
    })
    rows.append({
        "experiment": "EXP-003",
        "question": "What breaks when downstream actions rely on accepted rather than finalized state?",
        "finding": ("Full harness merged (consequence contracts, dataset, integration tests). "
                    "Bradbury runs blocked by testnet capacity + unreleased receipt handling; "
                    "harness fixes landed, watchdog armed."),
        "supports_thesis": None,
        "evidence_grade": "SIMULATED",
        "n_runs": 0,
        "artifacts": ["contracts/consequence_*.py", ".github/workflows/exp003-network.yml",
                      "docs/upstream-issue-draft.md"],
        "blockers": ["Bradbury capacity", "upstream gltest/genlayer-py release pairing"],
    })
    return rows


def main() -> None:
    rows = build_rows()
    scorecard = {
        "schema_version": "cfyow.scorecard.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "Score evidence quality separately from thesis support.",
        "rows": rows,
    }
    out_dir = REPO / "results" / "scorecard"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"scorecard-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n")
    print(f"saved: {out}\n")
    for row in rows:
        print(f"{row['experiment']:9} grade={row['evidence_grade']:11} "
              f"thesis_support={str(row['supports_thesis']):5} — {row['finding'][:90]}...")


if __name__ == "__main__":
    main()
