"""EXP-004 — Autonomy Budget: transition classifier + budget meter.

Classifies each workflow transition per the EXP-004 spec:
  INTERNAL_CONTINUATION  IC->IC child transaction continues the workflow
  EXTERNAL_TRIGGER       requires a fresh EOA/EVM transaction
  NEW_INFORMATION        waits for evidence that did not previously exist
  NEW_AUTHORITY          requires a fresh signature/decision from an actor
  FINALITY_WAIT          no new decision, but unsafe before finalization

Two arms measured:
  A) monolithic contract — every step inside one IC call (single tx)
  B) chained contracts   — each step its own IC, parent emits children
The budget metric: consequential transitions after ONE external trigger
before the next offchain intervention is required.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO / "results" / "EXP-004"

# Transition classes with their cost semantics (spec-defined)
TRANSITION_CLASSES = {
    "INTERNAL_CONTINUATION": {"external_trigger": False, "weight": 1.0},
    "EXTERNAL_TRIGGER": {"external_trigger": True, "weight": 0.0},
    "NEW_INFORMATION": {"external_trigger": False, "weight": 0.8},
    "NEW_AUTHORITY": {"external_trigger": True, "weight": 0.0},
    "FINALITY_WAIT": {"external_trigger": False, "weight": 0.3},
}


@dataclass
class Transition:
    name: str
    cls: str
    note: str = ""


def classify_monolithic_workflow() -> list[Transition]:
    """EXP-002 workflow implemented as ONE contract: all steps are internal."""
    return [
        Transition("propose", "INTERNAL_CONTINUATION",
                   "same contract, same tx"),
        Transition("accept", "INTERNAL_CONTINUATION", "same contract"),
        Transition("commit", "INTERNAL_CONTINUATION", "same contract"),
        Transition("submit_evidence", "NEW_INFORMATION",
                   "evidence must exist before submission is meaningful"),
        Transition("evaluate_consensus", "FINALITY_WAIT",
                   "judgment must finalize before settle"),
        Transition("settle", "INTERNAL_CONTINUATION", "same contract"),
    ]


def classify_chained_workflow() -> list[Transition]:
    """EXP-002 workflow as a chain of separate ICs, parent triggers children.

    Each hop is still an IC->IC continuation, BUT the initial deployment and
    any role change require external signatures; evaluation waits on consensus.
    """
    return [
        Transition("deploy_parent", "EXTERNAL_TRIGGER",
                   "initial deployment needs an EOA tx"),
        Transition("open_workflow", "EXTERNAL_TRIGGER",
                   "requester signature defines participants"),
        Transition("propose", "INTERNAL_CONTINUATION",
                   "provider IC reacts to open state via child tx"),
        Transition("accept", "NEW_AUTHORITY",
                   "requester decision is a distinct governance act"),
        Transition("commit", "INTERNAL_CONTINUATION",
                   "provider IC reacts to accepted state"),
        Transition("submit_evidence", "NEW_INFORMATION",
                   "waits for real-world evidence to exist"),
        Transition("evaluate_consensus", "FINALITY_WAIT",
                   "leader/validator rounds must complete"),
        Transition("appeal_window", "FINALITY_WAIT",
                   "unsafe to settle until appeal window closes"),
        Transition("settle", "INTERNAL_CONTINUATION",
                   "emitted child from finalized evaluate"),
    ]


def compute_budget(transitions: list[Transition]) -> dict[str, Any]:
    total = len(transitions)
    internal = sum(1 for t in transitions if t.cls == "INTERNAL_CONTINUATION")
    external = sum(1 for t in transitions if TRANSITION_CLASSES[t.cls]["external_trigger"])
    weighted = sum(
        TRANSITION_CLASSES[t.cls]["weight"]
        for t in transitions if t.cls != "EXTERNAL_TRIGGER"
    )
    # semantic budget: the deepest consecutive internal run
    best_run, current = 0, 0
    for t in transitions:
        if t.cls == "INTERNAL_CONTINUATION":
            current += 1
            best_run = max(best_run, current)
        else:
            current = 0
    return {
        "transitions_total": total,
        "internal_continuations": internal,
        "external_interventions": external,
        "weighted_budget": round(weighted, 2),
        "deepest_autonomous_run": best_run,
        "autonomy_ratio": round(internal / total, 2) if total else 0,
    }


def main() -> None:
    workflows = {
        "monolithic_contract": classify_monolithic_workflow(),
        "chained_contracts": classify_chained_workflow(),
    }
    results: dict[str, Any] = {}
    for name, transitions in workflows.items():
        print(f"\n=== {name} ===")
        for t in transitions:
            print(f"  {t.name:22} {t.cls:22} {t.note}")
        budget = compute_budget(transitions)
        print(f"  -> budget: {json.dumps(budget)}")
        results[name] = {
            "transitions": [t.__dict__ for t in transitions],
            "budget": budget,
        }

    dataset = {
        "schema_version": "cfyow.exp004.autonomy-budget.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "interpretation": {"status": "UNREVIEWED"},
        "workflows": results,
        "note": (
            "Static classification of the EXP-002 workflow under two contract "
            "architectures. Live measurement of child-tx counts lands with the "
            "GenLayer execution path (watchdog-gated)."
        ),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"autonomy-budget-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    print(f"\nsaved: {out}")


if __name__ == "__main__":
    main()
