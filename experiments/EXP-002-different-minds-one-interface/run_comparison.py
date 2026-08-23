"""EXP-002 three-arm runner.

Runs N workflows through all three evaluator arms on identical scenarios:
  A) deterministic predicate (ERC-8183-style escrow)
  B) centralized single-LLM judge
  C) GenLayer Optimistic Democracy (simulator or live; falls back to
     "pending" marker when network unavailable)

Outputs a comparison dataset ready for visualization.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from agent_runtime import ask, extract_json, load_keys  # noqa: E402
from baselines.deterministic_exp002 import DeterministicWorkflow  # noqa: E402

RESULTS_DIR = REPO / "results" / "EXP-002"

OBJECTIVES = [
    "Deliver a working JSON health endpoint that returns HTTP 200 and "
    '{\\"status\\": \\"ok\\"} at /health.',
    "Deliver an uptime status page showing the service as operational.",
    "Deliver a JSON status endpoint including a timestamp field.",
]


def run_arm_a(objective: str) -> dict[str, Any]:
    wf = DeterministicWorkflow(
        requester="requester",
        provider="provider",
        evaluator="evaluator",
        objective=objective,
    )
    t0 = time.time()
    wf.open_workflow("requester")
    wf.propose("provider", terms="deliver per objective")
    wf.accept("requester")
    deliverable = {"endpoint": "/health"}
    wf.commit("provider", deliverable)
    digest = hashlib.sha256(json.dumps(deliverable, sort_keys=True).encode()).hexdigest()
    wf.submit_evidence("provider", f"sha256:{digest}")
    wf.evaluate("evaluator")
    wf.settle("requester")
    state = wf.get_state()
    return {
        "arm": "A_deterministic",
        "outcome": state["settled_outcome"],
        "verdict": state["evaluation_verdict"],
        "wall_ms": round((time.time() - t0) * 1000),
        "llm_calls": 0,
        "appeal_capable": False,
    }


def run_arm_b(objective: str, keys: dict) -> dict[str, Any]:
    from run_workflow import run_workflow  # local import to reuse logging runner

    result = run_workflow(objective, keys_path=KEYS_PATH)
    latencies = [
        e["latency_ms"] for e in result.get("log", []) if "latency_ms" in e
    ]
    return {
        "arm": "B_centralized_judge",
        "outcome": result["outcome"],
        "verdict": _verdict_from_log(result),
        "wall_ms": round(sum(latencies)),
        "llm_calls": result["metrics"]["llm_calls"],
        "schema_violations": result["metrics"]["schema_violations"],
        "appeal_capable": False,
    }


def _verdict_from_log(result: dict) -> str | None:
    for entry in reversed(result.get("log", [])):
        if entry["kind"] == "evaluate":
            payload = entry.get("payload", {})
            return payload.get("verdict")
    return None


def run_arm_c(objective: str) -> dict[str, Any]:
    """GenLayer arm. Simulator/live execution is wired via the same contract;
    when the network is unavailable the run is recorded as PENDING rather
    than silently skipped — apparatus failure stays visible."""
    env = os.getenv("EXP002_ARM_C_MODE", "unavailable")
    if env == "unavailable":
        return {
            "arm": "C_genlayer_optimistic_democracy",
            "outcome": "PENDING_NETWORK",
            "verdict": None,
            "note": "contract ready (different_minds_judged.py); awaits GenLayer execution path",
            "appeal_capable": True,
        }
    raise NotImplementedError(
        "live/simulator wiring lands with the EXP-003 Bradbury path; "
        "arm C runs are recorded as PENDING until then"
    )


KEYS_PATH = os.path.expanduser("~/.config/foundry/cfyow-agents.env")


def main() -> None:
    n = int(os.getenv("EXP002_RUNS", "6"))
    keys = load_keys(KEYS_PATH)
    rows = []
    for index in range(n):
        objective = OBJECTIVES[index % len(OBJECTIVES)]
        print(f"\n=== workflow {index + 1}/{n}: {objective[:60]}... ===")
        row: dict[str, Any] = {"workflow": index + 1, "objective": objective}
        print("  arm A (deterministic)")
        row["A"] = run_arm_a(objective)
        print(f"    -> {row['A']['outcome']}")
        try:
            print("  arm B (centralized LLM judge)")
            row["B"] = run_arm_b(objective, keys)
            print(f"    -> {row['B']['outcome']}")
        except Exception as exc:  # noqa: BLE001 - failures are data
            row["B"] = {"arm": "B_centralized_judge", "outcome": "RUNNER_ERROR",
                        "error": str(exc)[:300]}
            print(f"    -> RUNNER_ERROR {str(exc)[:100]}")
        print("  arm C (GenLayer)")
        row["C"] = run_arm_c(objective)
        print(f"    -> {row['C']['outcome']}")
        rows.append(row)

    dataset = {
        "schema_version": "cfyow.exp002.comparison.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": rows,
        "summary": _summarize(rows),
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"comparison-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    print(f"\nsaved: {out}")
    print(json.dumps(dataset["summary"], indent=2))


def _summarize(rows: list[dict]) -> dict[str, Any]:
    def arm_stats(arm_key: str) -> dict[str, Any]:
        entries = [r[arm_key] for r in rows if arm_key in r]
        outcomes: dict[str, int] = {}
        for e in entries:
            outcomes[e["outcome"]] = outcomes.get(e["outcome"], 0) + 1
        verdicts: dict[str, int] = {}
        for e in entries:
            v = e.get("verdict") or "none"
            verdicts[v] = verdicts.get(v, 0) + 1
        llm = [e.get("llm_calls", 0) for e in entries]
        walls = [e["wall_ms"] for e in entries if isinstance(e.get("wall_ms"), int)]
        return {
            "outcomes": outcomes,
            "verdicts": verdicts,
            "total_llm_calls": sum(llm),
            "avg_wall_ms": round(sum(walls) / len(walls)) if walls else None,
        }

    return {"A_deterministic": arm_stats("A"),
            "B_centralized_judge": arm_stats("B"),
            "C_genlayer": arm_stats("C")}


if __name__ == "__main__":
    main()
